"""Shared array typing and validation helpers for the deterministic numerical core.

Every public function in ``portfolio_edge.core`` works in float64. Inputs are
accepted as any 1-D or 2-D sequence and converted here so that a caller can pass a
Python list, a pandas Series, or a NumPy array without changing the result.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
FloatVector = Sequence[float] | FloatArray
FloatMatrix = Sequence[Sequence[float]] | FloatArray


def as_float_array(values: FloatVector, *, name: str = "values") -> FloatArray:
    """Return ``values`` as a finite 1-D float64 array.

    Raises ``ValueError`` on the wrong dimensionality or on any non-finite entry.
    Silent ``NaN`` propagation is the failure mode this whole package exists to
    prevent, so it is rejected at the boundary rather than checked downstream.
    """
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional, got shape {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} contains non-finite entries")
    return array


def as_float_matrix(values: FloatMatrix, *, name: str = "matrix") -> FloatArray:
    """Return ``values`` as a finite 2-D float64 array."""
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 2:
        raise ValueError(f"{name} must be two-dimensional, got shape {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} contains non-finite entries")
    return array


def as_square_matrix(values: FloatMatrix, *, name: str = "matrix") -> FloatArray:
    """Return ``values`` as a finite square float64 array."""
    array = as_float_matrix(values, name=name)
    rows, columns = array.shape
    if rows != columns:
        raise ValueError(f"{name} must be square, got shape {array.shape}")
    return array


def require_non_empty(array: FloatArray, *, name: str = "values") -> FloatArray:
    """Return ``array`` unchanged, raising if it holds no observations."""
    if array.size == 0:
        raise ValueError(f"{name} must contain at least one observation")
    return array
