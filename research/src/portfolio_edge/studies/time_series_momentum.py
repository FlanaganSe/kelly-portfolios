"""Time-series momentum, constructed here rather than bought from a vendor.

[Experiment 011](../../../experiments/exp_011_overlay_stack.yaml) returned
``unresolved`` for one reason, and it was not the arithmetic. Its trend leg is AQR's
``Time-Series-Momentum-Factors-Monthly.xlsx``, a vendor series that **states no fee,
transaction-cost, slippage or financing basis anywhere**, is reconstructed on every
update, and whose measured pre- to post-publication decay (12.11 pp/yr) exceeds the
9.57 pp/yr haircut at which the overlay it supports stops paying. No further analysis
of that file can settle the question, because the file is the question.

This module builds the strategy instead. It reads no market data — the caller supplies
a matrix of instrument excess returns — so the same construction runs on Ken French
market factors, Goyal-Welch bond returns, Jorda-Schularick-Taylor country panels, or
anything else with a documented provenance.

**The construction, which is the standard one and is frozen here rather than tuned.**
For each instrument ``i`` at time ``t``, using only information available at ``t``:

- **Signal** — the sign of the compounded excess return over the previous ``lookback``
  periods, ``sign(prod(1 + r[t-lookback : t]) - 1)``. This is Moskowitz, Ooi and
  Pedersen's 12-month time-series momentum signal.
- **Sizing** — ``target_volatility / trailing_volatility``, capped at ``cap``, where
  the trailing volatility uses ``volatility_window`` observations ending at ``t-1``.
  Inverse-volatility sizing is what makes the legs comparable; the cap stops one quiet
  instrument dominating the book.
- **Portfolio** — the equal-weighted average across instruments with both a signal and
  a volatility estimate.

Every window ends at ``t`` exclusive. Nothing here can see ``r[t]``, which is the
return the position earns.

**What the construction deliberately omits, and which way each omission cuts.** There
are no transaction costs on the strategy's own trading, which flatters it — though a
12-month signal at monthly rebalancing on broad indices turns over far less than a
58-instrument futures programme. There is no financing cost, which is defensible for a
long/short book whose signed basis is approximately zero
(``docs/research/structural-and-tax-edges.md`` §3). And the instrument count is small,
which cuts **against** it: by the breadth identity in
:mod:`portfolio_edge.studies.overlay_growth`, a book of ``k`` instruments earns
``k / (1 + (k-1) rho_dd)`` times one instrument's peak, so three or four instruments
must earn materially less than fifty-eight. **This is a lower bound on a good
programme and an upper bound on a bad one**, and it should be read as a bracket rather
than as an estimate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from portfolio_edge.core._types import FloatArray, FloatMatrix

__all__ = [
    "TimeSeriesMomentumSpec",
    "position_sizes",
    "time_series_momentum",
    "volatility_targeted",
]


def _as_panel(returns: FloatMatrix) -> FloatArray:
    """A 2-D float panel that **may contain ``nan``**, unlike ``as_float_matrix``.

    The shared helper rejects non-finite entries, which is right for a portfolio
    weight vector and wrong here: every real multi-instrument panel has gaps, and the
    whole point of this construction is that an instrument drops out of the book on
    the periods it is missing rather than being bridged. Jorda-Schularick-Taylor has
    wartime holes; Ken French's regional files start in different decades.
    """
    matrix = np.asarray(returns, dtype=np.float64)
    if matrix.ndim != 2:
        raise ValueError(f"returns must be two-dimensional, got shape {matrix.shape}")
    if matrix.size == 0:
        raise ValueError("returns is empty")
    return matrix


@dataclass(frozen=True)
class TimeSeriesMomentumSpec:
    """The construction's parameters, frozen so a caller cannot tune them silently.

    The defaults are the literature's: a 12-month lookback, a 36-month volatility
    window, a 10% per-position volatility target and a 2x position cap. They are
    **declared, not optimised** — no search over these values has been run, and any
    result that depends on the exact choice should be reported as depending on it.
    """

    lookback: int = 12
    volatility_window: int = 36
    target_volatility: float = 0.10
    cap: float = 2.0
    periods_per_year: int = 12

    def __post_init__(self) -> None:
        if self.lookback < 1:
            raise ValueError(f"lookback must be at least 1, got {self.lookback}")
        if self.volatility_window < 2:
            raise ValueError(
                f"volatility_window must be at least 2, got {self.volatility_window}"
            )
        if self.target_volatility <= 0.0:
            raise ValueError(
                f"target_volatility must be positive, got {self.target_volatility}"
            )
        if self.cap <= 0.0:
            raise ValueError(f"cap must be positive, got {self.cap}")
        if self.periods_per_year <= 0:
            raise ValueError(
                f"periods_per_year must be positive, got {self.periods_per_year}"
            )

    @property
    def burn_in(self) -> int:
        """First index at which a position can be formed without look-ahead."""
        return max(self.lookback, self.volatility_window)


def position_sizes(
    returns: FloatMatrix, *, index: int, spec: TimeSeriesMomentumSpec
) -> FloatArray:
    """Signed position in each instrument at ``index``, from data before ``index``.

    ``returns`` is ``(periods, instruments)`` of **excess** returns. The result is
    ``nan`` for any instrument whose signal or volatility cannot be formed, so a
    caller can see which legs were live rather than having them silently dropped.
    """
    matrix = _as_panel(returns)
    if index < spec.burn_in:
        raise ValueError(
            f"index {index} is inside the {spec.burn_in}-period burn-in; a position "
            "there would need data that did not exist yet"
        )
    if index >= matrix.shape[0]:
        raise ValueError(f"index {index} is past the end of a {matrix.shape[0]}-row panel")

    out = np.full(matrix.shape[1], np.nan, dtype=np.float64)
    for column in range(matrix.shape[1]):
        window = matrix[index - spec.lookback : index, column]
        history = matrix[index - spec.volatility_window : index, column]
        if not np.isfinite(window).all() or not np.isfinite(history).all():
            continue
        signal = float(np.prod(1.0 + window) - 1.0)
        volatility = float(np.std(history, ddof=1)) * math.sqrt(spec.periods_per_year)
        if volatility <= 0.0:
            continue
        size = min(spec.target_volatility / volatility, spec.cap)
        out[column] = math.copysign(size, signal) if signal != 0.0 else 0.0
    return out


def time_series_momentum(
    returns: FloatMatrix,
    *,
    spec: TimeSeriesMomentumSpec | None = None,
    minimum_instruments: int = 1,
) -> FloatArray:
    """The strategy's excess return per period, ``nan`` inside the burn-in.

    Equal-weighted across whichever instruments carry a position that period. A period
    with fewer than ``minimum_instruments`` live legs returns ``nan`` rather than a
    thin average, because a one-leg book is a different strategy from a four-leg one
    and averaging them would hide the change.
    """
    settings = spec or TimeSeriesMomentumSpec()
    matrix = _as_panel(returns)
    if minimum_instruments < 1:
        raise ValueError(
            f"minimum_instruments must be at least 1, got {minimum_instruments}"
        )
    out = np.full(matrix.shape[0], np.nan, dtype=np.float64)
    for index in range(settings.burn_in, matrix.shape[0]):
        sizes = position_sizes(matrix, index=index, spec=settings)
        live = np.isfinite(sizes) & np.isfinite(matrix[index])
        if int(live.sum()) < minimum_instruments:
            continue
        out[index] = float(np.mean(sizes[live] * matrix[index][live]))
    return out


def volatility_targeted(
    strategy: FloatArray, *, window: int, target: float, cap: float = 3.0
) -> FloatArray:
    """Rescale a strategy to ``target`` volatility using a **trailing** estimate.

    Scaling by the full-sample volatility is the easy look-ahead in this kind of work:
    it uses the strategy's realised volatility to size a position taken before that
    volatility was known. It does not change a Sharpe ratio, but it does change the
    magnitude of any overlay gap computed from the scaled series, which is the number
    a reader would quote. This uses the ``window`` periods ending at ``t-1`` instead,
    and returns ``nan`` until that window exists.
    """
    series = np.asarray(strategy, dtype=np.float64)
    if series.ndim != 1:
        raise ValueError(f"strategy must be one-dimensional, got shape {series.shape}")
    if window < 2:
        raise ValueError(f"window must be at least 2, got {window}")
    if target <= 0.0:
        raise ValueError(f"target must be positive, got {target}")
    out = np.full(series.size, np.nan, dtype=np.float64)
    periods = 12
    for index in range(window, series.size):
        history = series[index - window : index]
        if not np.isfinite(history).all() or not np.isfinite(series[index]):
            continue
        volatility = float(np.std(history, ddof=1)) * math.sqrt(periods)
        if volatility <= 0.0:
            continue
        out[index] = series[index] * min(target / volatility, cap)
    return out
