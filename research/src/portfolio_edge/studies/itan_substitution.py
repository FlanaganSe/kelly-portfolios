"""Scoring one substitution inside the published vector: VTV 15 becomes VTV 10 + ITAN 5.

Why this module exists
----------------------
``docs/research/discovery-sweep-2026-09.md`` proposes intangible-adjusted value (Sparkline
ITAN) as the one equity idea that might raise the effective number of bets rather than add
another correlated value fund, and asks two things of the data: whether ITAN's value
exposure is positive at all, and how its active return correlates with the value and
momentum legs already held. :mod:`portfolio_edge.studies.untested_tilts` already owns the
arithmetic for pricing a tilt on delivered exposure, cost and overlap; this module adds the
three pieces a *substitution* needs that a sleeve-beside-the-portfolio does not, and keeps
them pure so the table script can be the only file that touches filings.

**A substitution is a weighted difference, not a new sleeve.** Moving five points of
capital from VTV to ITAN changes the portfolio by ``0.05 * (ITAN - VTV)``, so the delivered
exposure is fitted on the ``ITAN - VTV`` difference series and the whole effect is
:func:`substitution_return_change`, which is ``weight * sleeve_edge``. Nothing here may
multiply a loading by a capture fraction; :func:`untested_tilts.sleeve_edge` refuses it.

**The tracking error it adds depends on what is already held.** ``0.05 * TE(ITAN - VTV)``
is the substitution's own tracking error, and it is the wrong number to quote as the
portfolio's change unless the substitution is uncorrelated with the existing active
position. :func:`tracking_error_after_substitution` carries the correlation.

**A net cost needs the same estimator every other fund on the shelf got.** The repository
reads securities lending as the *median over fiscal years* of Form N-CEN Item C.6.g over
Item C.2 (``docs/research/final-construction-test.md`` §2). :func:`lending_median_bp`
is that definition, so ITAN's net cost is comparable to VTV's rather than to a different
statistic wearing the same units.

Everything is `exploratory`: no specification was frozen before the numbers were seen, and
ITAN's longest gapless filed run is 54 months, shorter than one value cycle.
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from portfolio_edge.studies.untested_tilts import portfolio_return_change, sleeve_edge

__all__ = [
    "PUBLISHED_VECTOR",
    "SUBSTITUTION_WEIGHT",
    "NcenLendingYear",
    "lending_median_bp",
    "substitution_return_change",
    "tracking_error_after_substitution",
    "vector_after_substitution",
]

#: The published recommendation, weights of capital, from
#: ``docs/research/portfolio-recommendation.md``. ``VTI`` and ``VXUS`` are the cheap
#: incumbents the active positions are measured against.
PUBLISHED_VECTOR: Final[Mapping[str, float]] = {
    "RSST": 0.30,
    "VTI": 0.19,
    "VTV": 0.15,
    "VXUS": 0.16,
    "AVDV": 0.10,
    "IDMO": 0.05,
    "AVES": 0.05,
}

#: Five points of capital, the size the discovery sweep proposed.
SUBSTITUTION_WEIGHT: Final = 0.05

_BASIS_POINTS: Final = 10_000.0


@dataclass(frozen=True, slots=True, kw_only=True)
class NcenLendingYear:
    """One fiscal year of Form N-CEN for one series: Item C.6.g over Item C.2, in dollars.

    ``net_income`` is *net income from securities lending activities* and
    ``average_net_assets`` is *monthly average net assets*, both as the fund filed them.
    The ratio is basis points a year of the fund's own assets, which is why it subtracts
    from an expense ratio.
    """

    fiscal_year_end: str
    net_income: float
    average_net_assets: float

    def __post_init__(self) -> None:
        if self.average_net_assets <= 0.0:
            raise ValueError(
                f"{self.fiscal_year_end}: average net assets must be positive, "
                f"got {self.average_net_assets}"
            )

    @property
    def basis_points(self) -> float:
        return self.net_income / self.average_net_assets * _BASIS_POINTS


def lending_median_bp(years: Sequence[NcenLendingYear]) -> float:
    """The median across fiscal years of lending income over average net assets, bp/yr.

    A median rather than the latest year, for the reason the final construction test
    gives: one year's figure can be eight times any other, and a single filed, unaudited
    outlier should not set a fund's cost. Raises on an empty sequence rather than
    returning zero, because "not read" and "earns nothing" are different statements.
    """
    if not years:
        raise ValueError("no fiscal years supplied; a net cost cannot be read from nothing")
    return statistics.median(year.basis_points for year in years)


def substitution_return_change(
    *,
    weight: float,
    delivered: Mapping[str, float],
    premia: Mapping[str, float],
    incremental_cost: float,
) -> float:
    """``weight * (sum_k (h_fund,k - h_incumbent,k) * premium_k - cost)``, pp/yr of portfolio.

    ``delivered`` is the *difference* regression's loadings, candidate less the fund it
    displaces, on one panel and one window. ``incremental_cost`` is the candidate's
    holding cost over the incumbent's, percent a year per dollar moved. The product is the
    change in the whole portfolio's expected return from moving ``weight`` of capital.
    """
    edge = sleeve_edge(delivered=delivered, premia=premia, incremental_cost=incremental_cost)
    return portfolio_return_change(weight=weight, edge=edge)


def tracking_error_after_substitution(
    *,
    held_tracking_error: float,
    weight: float,
    candidate_tracking_error: float,
    correlation: float,
) -> float:
    """Tracking error of ``held + weight * candidate``, in the units of the inputs.

    ``sqrt(s_h^2 + w^2 s_c^2 + 2 w rho s_h s_c)`` with ``s`` a tracking error.
    ``candidate_tracking_error`` is per dollar of the substitution leg and
    ``held_tracking_error`` is that of the whole existing active position at its actual
    weights; ``correlation`` is between the two. Subtract
    ``held_tracking_error`` from the result for the tracking error the substitution *adds*,
    which can be negative when the leg hedges what is held.
    """
    if held_tracking_error < 0.0 or candidate_tracking_error < 0.0:
        raise ValueError("a tracking error cannot be negative")
    if not -1.0 <= correlation <= 1.0:
        raise ValueError(f"correlation must lie in [-1, 1], got {correlation}")
    if not 0.0 <= weight <= 1.0:
        raise ValueError(f"weight must lie in [0, 1], got {weight}")
    scaled = weight * candidate_tracking_error
    variance = (
        held_tracking_error**2
        + scaled**2
        + 2.0 * correlation * held_tracking_error * scaled
    )
    return math.sqrt(max(variance, 0.0))


def vector_after_substitution(
    vector: Mapping[str, float], *, sell: str, buy: str, weight: float
) -> dict[str, float]:
    """``vector`` with ``weight`` of capital moved from ``sell`` to ``buy``.

    Refuses to sell more than is held, and refuses a zero move, because either would make
    the arithmetic downstream describe a portfolio nobody proposed. Weights sum to what
    they summed to before; a substitution funds itself.
    """
    if weight <= 0.0:
        raise ValueError(f"a substitution must move a positive weight, got {weight}")
    held = vector.get(sell, 0.0)
    if weight > held + 1e-12:
        raise ValueError(f"cannot move {weight} out of {sell}, which holds {held}")
    result = dict(vector)
    result[sell] = held - weight
    result[buy] = result.get(buy, 0.0) + weight
    return result


if __name__ == "__main__":  # pragma: no cover - regenerates the published tables
    from portfolio_edge.studies._itan_substitution_tables import main

    main()
