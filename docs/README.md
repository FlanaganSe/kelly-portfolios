# Documentation

A map, not a source of facts. Every number lives on the page that measured it; this file
carries none, so that nothing here can go stale on its own. Start at the root
[`README.md`](../README.md) for setup and current status.

**[The documentation and research protocol](AGENTS.md)** — where a document belongs, the
required shape of a synthesis, and how pages are retired. Read it before adding, moving or
deleting anything here. **[The register](style.md)** is what the site may claim and how it
may sound.

## Start here

| Page | Answers |
| --- | --- |
| [Charter](charter.md) | What this programme is for, the reference investor it is sized against, the benchmarks, the objective, and the conditions under which it would be finished. |
| [Research framework](research/portfolio-edge-research-framework.md) | Can you beat the market? The design map, every candidate's status, and the research protocol. |
| [The evidence base](research/evidence-base.md) | What each instrument can and cannot resolve. **Check its resolution table before proposing an experiment.** |
| [Search coverage](research/search-coverage.md) | The strategy universe and how much of it has been searched, what has never been tested, and round two, ranked. |
| [The recommended portfolio](research/portfolio-recommendation.md) | What to hold, in which account, at what confidence. Promotes nothing. |

## Where an edge can come from

| Page | Answers |
| --- | --- |
| [Expected edge decomposition](research/expected-edge-decomposition.md) | The three benchmarks that never aggregate, the budget against each, and why tracking error rather than edge size decides whether a lifetime is enough. |
| [Structural and tax-aware edges](research/structural-and-tax-edges.md) | What else is contractual for a US investor: fund structure, the foreign tax credit, §1256, the deferral hurdle, direct indexing, and the core beta shelf audited on cost rather than on fee. |
| [Setting the equity share](research/setting-the-equity-share.md) | The largest decision in the portfolio, split into the part that is arithmetic and the part that is preference. Sets no split. |
| [Capital efficiency and breadth](research/capital-efficiency-and-breadth.md) | What the funding rule is worth, how many distinct return engines survive cost, the candidate frontier, and the stress surface underneath the overlay weight. |

## The experiments

| Page | Covers |
| --- | --- |
| [Fama–French reproduction](research/fama-french-reproduction.md) | The Phase 1 ingestion gate, and the systematic volatility band that follows from the cells it cannot reproduce. |
| [Factor persistence and decay](research/factor-persistence.md) | Experiments 001, 005 and 006. What HML, UMD, RMW and CMA did before and after publication across three regions, and why SMB cannot be signed on any panel. |
| [The long-only capture fraction](research/long-only-capture.md) | Experiment 007. Why the capture fraction turns out to be a loading rather than a multiplier, so it may never multiply one. |
| [Investable factor products](research/factor-products.md) | Experiments 002, 009, 013, 014 and 015. Which audited ETFs deliver the exposure they advertise, on both shelves, and why the census frame decided the rest. |
| [Rebalancing](research/rebalancing-policy.md) | Experiment 003. The excess-growth identity reproduces exactly; the premise behind it does not survive real drift gaps. |
| [Trend](research/trend-marginal-value.md) | Experiments 004 and 008. What a trend sleeve adds against a risk-matched comparator, and the audit of the listed managed-futures ETFs. |
| [Live managed futures](research/live-managed-futures.md) | Experiment 012. The trend leg rebuilt from real funds' filed net returns instead of a vendor index. |
| [Marginal sleeve value](research/marginal-sleeve-value.md) | Experiments 010 and 010b. What a sleeve is worth *inside* a portfolio, split into a standalone term and a diversification credit. |
| [The alternative sleeves audit](research/alternative-sleeves-audit.md) | Which families a retail investor can actually own, at what all-in cost, and whether the net result clears admission. |
| [Numerical engine specification](research/portfolio-engine-specification.md) | The algorithms, fixtures and conditioning requirements underneath any allocation feature, and where an optimiser would run. |

## Decisions

| Record | Decides |
| --- | --- |
| [0001](decisions/0001-contained-python-research-workspace.md) | Portfolio research runs in `research/` under `uv`, and what that costs. |
| [0002](decisions/0002-no-research-grade-free-price-source.md) | No free price feed carries a total-return contract, so fund-level work is exploratory until a source is licensed. |
| [0003](decisions/0003-cheap-broad-market-control.md) | The cheap broad-market portfolio is the control, and the comparators a result must report. |
| [0004](decisions/0004-no-sleeve-promoted.md) | No sleeve is promoted; leverage stays at zero; the per-candidate conditions that would change it. |
| [0005](decisions/0005-factor-premia-closed-on-public-data.md) | Profitability and investment premia are closed on public data, and the conditions that would reopen either. |
| [0006](decisions/0006-reference-portfolio-without-promotion.md) | A named-fund reference portfolio may be published, under four constraints that keep it from becoming a promotion. |
| [0007](decisions/0007-application-may-render-research.md) | The application may render a research finding, under four constraints. |
| [0008](decisions/0008-growth-decides-crra-reports.md) | Geometric growth decides; the certainty equivalent reports beside it. |
| [0009](decisions/0009-blocks-lifted-and-closures-rescoped.md) | The blocked steps are unblocked, a verdict may not outrun its instrument, and a closure carries its scope. |

## Counts and statuses

Do not transcribe them. The ledger is the only thing that knows what was run:

```sh
cd research && uv run python -m portfolio_edge.reporting.programme_status
```
