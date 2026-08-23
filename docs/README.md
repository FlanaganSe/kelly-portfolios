# Documentation

This is a reading map, not a second source of research facts. Detailed experiment output
lives in committed run artifacts; each synthesis links its evidence.

## What should I believe now?

Start with the [research framework](research/portfolio-edge-research-framework.md) for the
short current position and evidence model, then read the
[portfolio recommendation](research/portfolio-recommendation.md) as a provisional decision
for the stated reference investor. The [edge decomposition](research/expected-edge-decomposition.md)
keeps three different benchmarks from being mixed.

For the major decisions:

- [Equity share](research/setting-the-equity-share.md): what arithmetic can say and which
  investor constraints decide the rest.
- [Valuation and the allocation](research/valuation-and-the-allocation.md): what an August
  2026 CAPE of 41 licenses — a wider drawdown assumption, not a timing rule — and why the
  US/international spread is a differently identified question from the US level.
- [Structural and tax edges](research/structural-and-tax-edges.md): implementation gains
  that are conditional on accounts, taxes, holdings, and behavior.
- [Factors](research/factor-persistence.md), [delivered loading](research/long-only-capture.md),
  and [products](research/factor-products.md): the evidence chain from research premium to
  investable exposure.
- [Trend and managed futures](research/trend-marginal-value.md) and
  [live-fund evidence](research/live-managed-futures.md): the strongest current diversifier
  candidate and its unresolved implementation risks.
- [Timing rules on the equity sleeve](research/timing-rules-on-the-equity-sleeve.md): the
  same signal applied to the base portfolio instead — a different funding rule, a different
  tax outcome, and largely the same bet as a trend overlay.
- [Rebalancing](research/rebalancing-policy.md): useful exposure control, with no stable
  return bonus established.
- [Other diversifiers](research/alternative-sleeves-audit.md) and
  [capital efficiency](research/capital-efficiency-and-breadth.md): candidate mechanisms,
  access, financing, and failure modes — including the cross-engine stress table, the
  verdicts on crypto and tail hedging, and why duration-hedged credit is a separate engine
  when unhedged credit is not.
- [Leverage and the notional budget](research/leverage-and-the-notional-budget.md): what
  gross and net exposure a 30% stacked-fund line actually carries, what the growth objective
  wants across the premium surface, what the embedded financing costs, and why the binding
  constraint is holdability rather than drawdown.
- [Stacking and effective breadth](research/stacking-and-effective-breadth.md): what a
  pile of sleeves is worth once their excess returns are correlated, and how many
  independent bets the proposed portfolio is actually making.
- [The construction tournament](research/construction-tournament.md): twenty-five whole
  portfolios scored against three benchmarks — which differences this data can resolve,
  which it cannot, and how many years an investor would have to hold each one before
  finding out.

## What should we research next?

Read [search coverage](research/search-coverage.md). It is the ranked agenda, not a
permission boundary. Check the [evidence base](research/evidence-base.md) before designing
the next test: it records source fitness, resolution, and limitations. A current instrument
that cannot resolve the effect is a reason to acquire or design a better one, not to stop
asking the question.

The highest-value open work is portfolio-level rather than another isolated sleeve screen:
compare feasible diversifiers under a common set of investor constraints and explicit
funding rules; measure crisis-conditional dependence; improve point-in-time live-fund
coverage including dead funds; and parameterize the recommendation by investor inputs.

## How do I reproduce a result?

Follow the synthesis link to its `research/artifacts/*/summary.md`, then to the frozen YAML
specification, manifests, and implementation. The [research workspace README](../research/README.md)
contains commands and integrity requirements. Experiment counts and statuses are generated:

```sh
cd research && uv run python -m portfolio_edge.reporting.programme_status
```

## Governance and method

- [Charter](charter.md): objective, reference scenario, benchmarks, and decision sufficiency.
- [Documentation protocol](AGENTS.md): canonical homes and tiered evidence standards.
- [Numerical engine](research/portfolio-engine-specification.md): mathematical architecture.
- [Decision records](decisions/README.md): current and historical choices, with
  supersession made explicit.

## Complete file map

Topical pages not already named above: [Fama–French reproduction](research/fama-french-reproduction.md),
[marginal sleeve value](research/marginal-sleeve-value.md),
[expected-edge decomposition](research/expected-edge-decomposition.md), and the
[numerical engine](research/portfolio-engine-specification.md).

Decision records: [0001](decisions/0001-contained-python-research-workspace.md),
[0002](decisions/0002-no-research-grade-free-price-source.md),
[0003](decisions/0003-cheap-broad-market-control.md),
[0004](decisions/0004-no-sleeve-promoted.md),
[0005](decisions/0005-factor-premia-closed-on-public-data.md),
[0006](decisions/0006-reference-portfolio-without-promotion.md),
[0007](decisions/0007-application-may-render-research.md),
[0008](decisions/0008-growth-decides-crra-reports.md),
[0009](decisions/0009-blocks-lifted-and-closures-rescoped.md), and
[0010](decisions/0010-bars-carry-a-reopening-condition.md).
