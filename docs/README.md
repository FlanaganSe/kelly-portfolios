# Documentation

An index, not a source of facts. Start at the root [`README.md`](../README.md) for setup
and current status.

## Protocol

- [Documentation and research protocol](AGENTS.md) — where a document belongs, the required
  shape of a research synthesis, and how pages are retired. **Read it before adding, moving
  or deleting anything here.**

## Start here

- **[Portfolio edge research framework](research/portfolio-edge-research-framework.md)** —
  the canonical synthesis. Answers *whether a return source is real*: the direct answer to
  "can you beat the market", the design map with every candidate's status and promotion
  condition, what the prior literature does and does not establish, the ledger accounting,
  and the research protocol.
- **[The evidence base](research/evidence-base.md)** — the sources of truth. Every dataset
  held, what it is pinned to, **what it can and cannot resolve at 80% power**, what was
  tried and failed, and what a next round would have to acquire. **Check the resolution
  table before proposing an experiment.**
- **[Search coverage](research/search-coverage.md)** — where the search has looked, the
  three design choices that make the null result partly self-inflicted, what has never been
  tested at all, and **round two, ranked**.
- **[The recommended portfolio](research/portfolio-recommendation.md)** — the named funds,
  weights and account placement the evidence supports, with the certainty class behind every
  line. Answers *what to hold*; promotes nothing.

## The evidence

### Where an edge can come from

- [Where outperformance can come from](research/expected-edge-decomposition.md) — the three
  benchmarks that never aggregate, the budget against each, and the horizon arithmetic that
  makes tracking error rather than edge size decide whether a lifetime is enough. Also why
  the behaviour gap may be displayed and never added.
- [Structural and tax-aware edges](research/structural-and-tax-edges.md) — what else is
  contractual for a US investor, sized against one stated reference portfolio: fund
  structure, the foreign tax credit that inverts standard placement advice, §1256 and
  capital efficiency, the deferral hurdle, direct indexing, securities lending.
- [Setting the equity share](research/setting-the-equity-share.md) — the largest decision in
  the portfolio, split into the part that is arithmetic and the part that is preference.
  Shows that the objective plus the zero-leverage rule returns a corner solution, so the
  bonds come from the constraint. **Sets no split.**

### The experiments

- [Fama–French factor reproduction](research/fama-french-reproduction.md) — the Phase 1
  ingestion gate, `unresolved`: which published table was reproduced from which vintage, the
  two cells that do not, and the systematic 3–5% volatility band that follows.
- [Factor persistence and decay](research/factor-persistence.md) — Experiments 001, 005 and
  006. What HML, UMD, RMW and CMA did before and after publication across frozen eras in
  three regions, **the measured effective sample size that pooling correlated regions
  actually buys**, and why profitability and investment are closed on the public files.
- [The long-only capture fraction](research/long-only-capture.md) — Experiment 007. What
  fraction of a long-short premium a long-only tilt delivers, measured from the portfolios
  the factor is assembled from. **Five defensible benchmarks disagree by 0.846**, so the
  rejection is of the premise that there is one number. Also the first test of size as a
  premium.
- [Investable factor products](research/factor-products.md) — Experiments 002 and 009. Which
  of 69 audited ETFs deliver the exposure they advertise, on both the US and the ex-US
  shelf, why a 72-month N-PORT window decides nothing about alpha, and why an ex-US loading
  without its panel named is not a number.
- [Rebalancing](research/rebalancing-policy.md) — the closed-form theory and Experiment 003,
  the first confirmatory run. The excess-growth identity reproduces to a tenth of a basis
  point, its 68.27% win-probability floor does not survive real drift gaps, and every policy
  lost to buy-and-hold.
- [Trend: the index, the products, and a clause that was ambiguously specified](research/trend-marginal-value.md)
  — Experiments 004 and 008. What a trend sleeve adds against a risk-matched comparator, why
  a static-plus-volatility replica fires the falsifier, and the audit of the five listed
  managed-futures ETFs of which one delivers the exposure.
- [Live managed futures](research/live-managed-futures.md) — Experiment 012. The trend leg
  rebuilt from 46 real funds' net Form N-PORT returns instead of a vendor index: what
  managed-futures investors actually earned, 52% attrition in the opening cohort, and the
  measurement that the vendor series **understated** rather than overstated the funds over
  the only window where both exist.
- [Marginal sleeve value](research/marginal-sleeve-value.md) — Experiments 010 and 010b.
  What a sleeve is worth *inside* a portfolio, split into a standalone term and a
  diversification credit whose ceiling is the base portfolio's own variance. Carries the
  cash control that produced decision 0008 — and the weight-dependence that reopens its own
  headline.
- [Capital efficiency and breadth](research/capital-efficiency-and-breadth.md) — what the
  funding rule is worth (`a_p - sigma_p**2`, containing nothing about the sleeve), why the
  realised growth optimum on levered equity is unholdable at a -99.3% drawdown, how many
  distinct return engines actually exist once cost is charged (one), the candidate frontier
  against a leverage-matched control, and why the global-versus-US question is unresolved:
  the century of local-currency data and the only USD series available disagree in opposite
  directions.
- [Numerical engine specification](research/portfolio-engine-specification.md) — the
  algorithms, closed-form fixtures and conditioning requirements underneath any allocation
  feature, and where the optimiser should run.

## Decisions

- [0001 — Contained Python research workspace](decisions/0001-contained-python-research-workspace.md)
  — why portfolio research runs in `research/` under `uv`, and what that costs.
- [0002 — No research-grade free price source](decisions/0002-no-research-grade-free-price-source.md)
  — every free price feed was tested and none carries a total-return contract, so fund-level
  work is exploratory until a source is licensed.
- [0003 — The cheap broad-market portfolio is the control](decisions/0003-cheap-broad-market-control.md)
  — what every candidate is measured against, and the four comparators a result must report.
- [0004 — No sleeve is promoted](decisions/0004-no-sleeve-promoted.md) — the outcome of each
  frozen hypothesis, why leverage stays at zero, and the per-candidate conditions that would
  change it. Its context block is a snapshot; the current ledger count is in the
  [framework](research/portfolio-edge-research-framework.md#the-ledger-counted-rather-than-described).
- [0005 — Profitability and investment premia are closed on public data](decisions/0005-factor-premia-closed-on-public-data.md)
  — the measured floor on what public factor data can detect, and the four conditions that
  would reopen either.
- [0006 — A named-fund reference portfolio without promotion](decisions/0006-reference-portfolio-without-promotion.md)
  — why a concrete construction may be published, and the four constraints that keep it from
  becoming a promotion.
- [0007 — The application may render research findings](decisions/0007-application-may-render-research.md)
  — why the ban was lifted, and the four constraints that replace it.
- [0008 — Geometric growth decides; the certainty equivalent reports beside it](decisions/0008-growth-decides-crra-reports.md)
  — the CRRA metric pays a sleeve for de-risking, measured at +0.809 pp/yr on a control that
  supplies nothing.
</content>
