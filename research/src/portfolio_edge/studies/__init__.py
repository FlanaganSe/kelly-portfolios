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
"""
