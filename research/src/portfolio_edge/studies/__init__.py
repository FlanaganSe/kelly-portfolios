"""Self-contained studies that regenerate the numbers in a research synthesis.

Each module here answers one question in ``docs/research/`` and is the executable
record of how its numbers were produced. Nothing in this package reads market data,
so every result is reproducible from its stated inputs alone. Where a study uses
randomness the generator seed is an explicit argument with a committed default.

* :mod:`volatility_harvesting` — the exact growth algebra of constant-weight versus
  buy-and-hold portfolios, and the finite-horizon probabilities that follow from it.
* :mod:`rebalancing_monte_carlo` — seeded simulation used only to confirm the closed
  forms above, never to establish a result the algebra does not already give.
* :mod:`chambers_zdanowicz` — the worked binomial example behind the dispute over
  whether expected log wealth is "an arbitrary nonlinear transformation of wealth".
* :mod:`outperformance_horizon` — how long an edge of a given size takes to become
  statistically visible against a given tracking error, and the edge budget itself.
* :mod:`overlay_growth` — what a diversifying sleeve is worth under a financed
  overlay rather than pro-rata funding, and the exact size of the gap between them:
  ``a_e - sigma_e**2``, which involves no property of the diversifier at all.
* :mod:`time_series_momentum` — the trend strategy built here rather than bought from
  a vendor, so Experiment 011's `unresolved` verdict can be tested against a series
  whose provenance this repository controls. Reads no market data.
* :mod:`overlay_stress` — the same overlay attacked rather than priced: a joint stress
  surface over four correlated axes, a resampled test of the flat-drawdown result the
  recommendation rests on, and the failure modes the charter names. Reads no
  market data; ``_overlay_stress_tables`` is the companion that touches the cache.
* :mod:`gold_sleeve` — the arithmetic for the one candidate asset outside equity and
  cash this repository can reach: total return from a price level plus a stated carry,
  moments, the admission threshold, the correlation *inside* equity drawdowns, and
  Experiment 010's credit decomposition. Reads no market data; ``_gold_sleeve_tables``
  is the companion that touches the cache.
* :mod:`tax_structure` — the contractual, tax-code half of that budget: foreign tax
  credit forfeiture, fund-structure capital gains, §1256, the value of deferral, the
  decay of loss harvesting, and the arithmetic of capital efficiency. Rates are a dated,
  jurisdiction-stamped argument rather than a constant.
"""
