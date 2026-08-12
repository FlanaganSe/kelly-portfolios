# Documentation

An index, not a source of facts. Start at the root [`README.md`](../README.md) for
setup and current status.

## Protocol

- [Documentation and research protocol](AGENTS.md) — where a document belongs, the
  required shape of a research synthesis, and how pages are retired. Read it before
  adding, moving, or deleting anything here.

## Research

- [Portfolio edge research framework](research/portfolio-edge-research-framework.md)
  — **the canonical synthesis, and the place to start.** Answers the commissioning
  question directly, holds the provisional portfolio-design map, accounts for what
  advanced, failed and remains unresolved across all six experiments, and names the
  single next experiment. Also carries the evidence, falsifiable hypotheses and
  validation protocol for leverage, rebalancing, crisis protection, factors and
  manager alpha. Answers whether a return source is real.
- [Agent configuration](research/2026-08-11-agent-configuration.md) — the evidence
  behind the instruction files, permissions, hook, and skills in this repository.
- [Fama-French factor reproduction](research/fama-french-reproduction.md) — the
  Phase 1 ingestion gate: which published table was reproduced from which data
  vintage, the two cells that do not reproduce, and what a downstream experiment
  may and may not assume about the data path as a result.
- [Where outperformance can come from](research/expected-edge-decomposition.md) —
  the size and certainty class of every return source the repository will model,
  and the benchmark each is measured against. Proves when constant-weight
  rebalancing beats buy-and-hold, gives the closed-form probability of doing so,
  and separates what is beatable (your own counterfactual) from what is not (a
  cheap index).
- [Structural and tax-aware edges](research/structural-and-tax-edges.md) — what else
  belongs in the contractual class the edge decomposition prices at 89 bp/yr, how large
  each lever is, and which of them double-count. Sizes fund-structure capital gains,
  foreign tax credit forfeiture, deferral and the step-up, harvesting decay net of its
  fee, §1256 and capital efficiency, against one stated reference investor,
  `as of 2026-08-12`.
- [Factor persistence and decay](research/factor-persistence.md) — Experiments 001,
  005 and 006: what HML, UMD, RMW and CMA did before and after publication across
  frozen eras in the US, and what adding developed-ex-US and emerging equity over the
  same eras did to that. Holds the measured effective sample size that pooling
  correlated regions actually buys, why value and momentum reached `exploratory`, why
  profitability and investment are closed on public data, whether the three regional
  momentum series crash together, and the cost-versus-turnover schedule that must not
  be applied to a long-only fund.
- [The long-only capture fraction](research/long-only-capture.md) — Experiment 007:
  what fraction of a long-short factor premium a long-only tilt actually delivers,
  measured from the portfolios the factor is assembled from rather than assumed.
  Finds that five defensible benchmarks disagree by 0.846, names the size-neutral
  reading of `0.520 [0.434, 0.722]` as the only one entitled to be called a value
  capture, tests size as a premium for the first time, and prices the small-value
  corner against the share of market capitalisation it actually holds.
- [Investable factor products](research/factor-product-audit.md) — Experiment 002:
  which of 44 screened ETFs deliver the exposure they advertise, what they cost
  against a cheap replication, why a 72-month N-PORT window decides nothing about
  alpha, and why nothing is promoted. Also measures how much of the 2019 factor
  shelf no longer exists.
- [Rebalancing policy on real regional equity](research/rebalancing-policy.md) —
  Experiment 003, the first confirmatory run: five policies on US, developed-ex-US
  and emerging equity over 35 years. The excess-growth closed form reproduces to a
  tenth of a basis point, its 68.27% win-probability floor does not survive real
  drift gaps, and every policy loses to buy-and-hold.
- [Trend: the index, the products, and a clause that was ambiguously specified](research/trend-marginal-value.md)
  — Experiment 004, a vendor-series evaluation of AQR's time-series-momentum factor
  against a risk-matched cash comparator: what a 15% sleeve adds to a portfolio that
  already exists, why the standalone Sharpe collapsed after publication while the
  marginal benefit did not, and why a static-plus-volatility exposure replica fires
  the falsifier. Then Experiment 008, the audit of the five US-listed managed-futures
  ETFs that clear a mechanical screen: only DBMF delivers the index's exposure, tax
  drag is two to three times the expense ratio, and Experiment 004's clause (d) is
  re-decided under both its readings.
- [The recommended portfolio](research/portfolio-recommendation.md) — the named funds,
  weights and account placement the evidence supports, with the certainty class and
  confidence horizon behind every line, the foreign-tax-credit arithmetic that decides
  where an international sleeve belongs, and a sleeve-by-sleeve verdict on the
  portfolio the project owner proposed. Answers what to hold; promotes nothing.
- [Numerical engine specification](research/portfolio-engine-specification.md) —
  the algorithms, closed-form test fixtures, and conditioning requirements
  underneath any allocation feature, and where the optimiser should run. Answers
  how to compute it, and defers to the edge framework on whether to.

## Decisions

- [0001 — Contained Python research workspace](decisions/0001-contained-python-research-workspace.md)
  — why portfolio research runs in `research/` under `uv` rather than in the
  client, and what that costs.
- [0002 — No research-grade free price source](decisions/0002-no-research-grade-free-price-source.md)
  — every free price feed was tested and none carries a total-return contract, so
  fund-level work is exploratory until a source is licensed.
- [0003 — The cheap broad-market portfolio is the control](decisions/0003-cheap-broad-market-control.md)
  — what every candidate is measured against, and the four comparators a result must
  report: benchmark and certainty class, a cheap combination, a risk match, and the
  model-misfit pedestal.
- [0004 — No sleeve is promoted](decisions/0004-no-sleeve-promoted.md) — the outcome
  of all six experiments in the closed status vocabulary, why leverage stays at
  zero, and the per-candidate conditions that would change it.
- [0005 — Profitability and investment premia are closed on public data](decisions/0005-factor-premia-closed-on-public-data.md)
  — the measured floor on what public factor data can detect, why RMW and CMA are
  `rejected` rather than `unresolved` again, and the four conditions that would
  reopen either.
- [0006 — A named-fund reference portfolio without promotion](decisions/0006-reference-portfolio-without-promotion.md)
  — why a concrete construction may now be published, what "recommended" is allowed to
  mean, and the four constraints that keep it from becoming a promotion.
