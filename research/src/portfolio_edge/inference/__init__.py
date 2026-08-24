"""Statistical inference for portfolio research.

Layer 2 of ``docs/research/portfolio-engine-specification.md``: the machinery that makes
overfitting visible before any optimisation runs.

* :mod:`~portfolio_edge.inference.bootstrap` — circular block and stationary bootstraps,
  with corrected Politis-White automatic block-length selection.
* :mod:`~portfolio_edge.inference.hac` — Newey-West standard errors for means and OLS.
* :mod:`~portfolio_edge.inference.deflated_sharpe` — probabilistic and deflated Sharpe
  ratios, and effective trial counts.
* :mod:`~portfolio_edge.inference.multiple_testing` — Holm, Benjamini-Hochberg, White's
  Reality Check and Hansen's SPA.
* :mod:`~portfolio_edge.inference.conditioning` — nearest correlation matrix,
  Marchenko-Pastur noise bounds, Ledoit-Wolf shrinkage.
* :mod:`~portfolio_edge.inference.walk_forward` — purged and embargoed chronological
  cross-validation.

Every resampling entry point takes an explicit :class:`numpy.random.Generator`. There is no
module-level generator, no global state, and no printing from library code.
"""

from __future__ import annotations

from portfolio_edge.inference import (
    bootstrap,
    conditioning,
    deflated_sharpe,
    hac,
    multiple_testing,
    walk_forward,
)

__all__ = [
    "bootstrap",
    "conditioning",
    "deflated_sharpe",
    "hac",
    "multiple_testing",
    "walk_forward",
]
