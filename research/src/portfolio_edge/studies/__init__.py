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
* :mod:`valuation_conditioning` — whether a valuation level should move an allocation,
  and the inference that decides it: Hodrick 1B standard errors for overlapping
  long-horizon regressions, the Stambaugh bias of a persistent valuation ratio, an
  out-of-sample score against a rolling-mean benchmark, and the cost arithmetic of a
  dynamic weight. Reads no market data; ``_valuation_conditioning_tables`` is the
  companion that touches the cache.
* :mod:`stacking` — what a pile of sleeves is jointly worth: the probability a stack of
  ``k`` sleeves each ``p`` likely to win beats its benchmark, the ceiling
  ``Phi(z_1/sqrt(rho))`` that no number of correlated sleeves gets past, the second
  ceiling ``Phi(e/tau)`` that an estimated edge imposes at every horizon, the marginal
  appraisal ratio that decides whether one more sleeve earns its place, and the
  arithmetic difference between funding a sleeve by substitution and by overlay. Reads no
  market data; ``_stacking_tables`` is the companion that touches the cache.
* :mod:`longonly_ladder` — the question :mod:`stacking` leaves open: given a shelf of
  candidates ranked best to worst, how many does an optimiser hold? Equal weights, the
  unconstrained ``Sigma^-1 e`` optimum, and the exact long-only optimum solved by
  enumerating every support rather than by an iterative solver, so the count carries no
  convergence tolerance. The ratio of the last two is the Clarke-de Silva-Thorley transfer
  coefficient. Every edge is an argument: the module estimates no premium and reads no
  market data, and the answer depends on edge dispersion as much as on correlation, which
  is why the held count and the dispersion setting are always reported together.
  Experiment 017 runs it under a frozen specification.
* :mod:`rebalancing_operations` — whether the stacked candidate can be *run*: the map
  between capital weights and notional exposure and the two ways an investor gets it
  wrong, the exact condition under which a portfolio target is restorable using only
  sheltered accounts (``taxable_i <= target_i`` for every fund), and the joint objective
  that decides the placement — recurring tax drag *plus* the forced realisation that zero
  headroom causes, minimised together rather than either alone. The per-fund tax profiles
  are rebuilt from the filed yields and qualified fractions and reproduce every published
  shelter priority at every bracket, so the ranking is shared with the placement page
  rather than copied from it. Includes an executable three-account rule that charges
  spreads and capital-gains tax inside itself. Reads no market data;
  ``_rebalancing_operations_tables`` is the companion that touches the cache.
* :mod:`trend_weight_regret` — how much trend notional to hold when the forward premium
  is not identified and no amount of resampling one window can identify it: a weighted
  prior assembled from this repository's own measurements with the vendor-authored ones
  labelled, a regret surface over weight and net premium against two benchmarks that are
  never added, the closed-form identity showing that a minimax rule is the average optimal
  weight under a uniform prior on the stated range, and the two arms of the asymmetry —
  the investor's own capitulation priced inside the path, and the overlay's contribution
  conditioned on the equity decade rather than averaged over it. Reads no market data;
  ``_trend_weight_regret_tables`` is the companion that touches the cache.
* :mod:`adversarial_review` — the arithmetic a red team needs: restating a geometric,
  net-of-fee forecast onto the arithmetic gross basis a break-even was computed on; a
  sub-period's own detection floor and the floor on a difference between two halves;
  empirical-Bayes shrinkage of a cross-section of fitted alphas, which is what a
  charge-if-it-clears-its-floor rule should have been; and what an edge is worth against
  a savings rate. Reads no market data and takes only numbers a caller measured elsewhere.
* :mod:`currency_hedging` — what a dollar investor is actually holding in an unhedged
  foreign equity fund. The identity ``unhedged - hedged = the currency excess return``,
  written exactly rather than to first order; the beginning-notional forward hedge under
  covered interest parity and the give-up it removes; cap-weighted currency baskets; the
  effective sample size of a near-random-walk; and a hedge-ratio frontier reported beside
  the mean's own detection floor, because the mean and the variance of a currency position
  are estimated with wildly different precision and a page that reports one without the
  other will make the wrong argument. Reads no market data;
  ``_currency_hedging_tables`` is the companion that touches the cache.
* :mod:`loading_windows` — what a factor loading may be compared with. Every published
  loading here was fitted on the fund's own filed history, so the windows differ and the
  numbers cannot be ranked against one another; ``rank`` refuses a mixed-window set rather
  than sorting it, as ``outperformance_horizon.aggregate`` refuses to add across
  benchmarks. Also the machinery that measures a *stacked wrapper's* delivered exposure
  from Form N-PORT Item B.5, which needs no price feed. Reads no market data;
  ``_loading_windows_tables`` is the companion that touches the cache.
* :mod:`tax_loss_harvesting` — what harvesting is worth once §1211(b)'s $3,000 cap
  decides how much of a realised loss can ever be deducted. Two functions with no shared
  state: a market model that says how much loss is harvestable and contains no tax law,
  and a tax model that says how much of it is usable and contains no market model. The
  identity that organises it is that harvesting reduces basis by exactly the loss it
  realises, so a liquidation reverses the benefit in full while §1014 and §170 forgive it
  — and both destroy the unused carryforward. Reads no market data;
  ``_tax_loss_harvesting_tables`` is the companion that touches the cache.
* :mod:`financed_gold_bitcoin` — whether financing a gold-and-bitcoin sleeve on top of
  the construction, as RSSX does, changes the crypto verdict that was measured on a
  pro-rata construction: the wrapper algebra Experiment 018 uses with a bitcoin leg
  admitted, one arm against the reference with the floor beside the gap, the closed-form
  break-even bitcoin premium and the variance term that turns it into a growth
  break-even, and a check of an assumed exposure vector against a fund's printed months.
  Reads no market data; ``_financed_gold_bitcoin_tables`` is the companion that touches
  the cache and, because its choices were made after the audit, ledgers its own run.
"""
