# 0004 — No sleeve is promoted; the portfolio is the control alone

Date: 2026-08-12. Status: accepted.

## Context

Five frozen experiments have run, across fifteen ledgered executions of six distinct
specifications, with 1,037 tests passing `as of 2026-08-12`, 18 of them
network-marked. The outcomes, in the closed status vocabulary:

| Hypothesis | Status | The number that decides it |
| --- | --- | --- |
| Phase 1 ingestion gate | `unresolved` | HML and RMW standard deviations do not reproduce; variance ratios 0.940 and 1.104 |
| HML, UMD, RMW premia persist post-publication | `unresolved` | 16 of 20 cells hold a premium smaller than their window can detect at 80% power |
| CMA premium persists post-publication | **`rejected`** | −1.39 pp/yr post-publication against +3.91 in-sample |
| Retail factor products deliver exposure worth buying | `exploratory` | 24 of 44 `rejected`; clause (c) fired on 22, a shortfall above 0.50 pp/yr to a fitted four-fund combination |
| Rebalancing is a source of return | **`rejected`** | Every policy lost on all three cost bases; drift gap ran ~35× `gamma_star` |
| A trend sleeve adds marginal value a simpler exposure cannot | **`rejected`** | A static + volatility-exposure replica delivers 44% of the benefit |

Three of those are `rejected` against a falsifier frozen before any result was seen.
Three are `unresolved`, and in every case the reason is that the available window
cannot detect the effect it is looking for — not that the effect is absent. Nothing
reached `walk-forward-tested`, `shadow-live` or `production-eligible`, and nothing
could have: the fund-level data contract caps that work at `exploratory`
([decision 0002](0002-no-research-grade-free-price-source.md)).

Recording this is not bookkeeping. The failure mode of a research programme with this
much apparatus is that a reader assumes the apparatus produced a portfolio.

## Decision

**No candidate sleeve is promoted. The research portfolio is the cheap broad-market
control alone** ([decision 0003](0003-cheap-broad-market-control.md)), plus the
deterministic cost, tax-location and do-not-trade discipline that the
[edge decomposition](../research/expected-edge-decomposition.md) prices at about
89 bp/yr against the investor's own counterfactual.

Consequently:

- **Leverage stays at zero.** It was conditioned on an unlevered edge surviving the
  protocol. None has, so there is nothing to lever.
- **Rebalancing is retained as risk control and forbidden as return.** It held
  exposure within 0.6 to 3.1 percentage points of target against buy-and-hold's 14.8,
  for 0.3 to 1.2 bp/yr. Anyone who wants their declared allocation to remain their
  actual allocation should rebalance. No rebalancing-bonus feature may be built.
- **The fifteen `exploratory` products may be used as implementation proxies in a
  later experiment and for nothing else.**
- **No number from `research/` may appear in the shipped application as a finding.**

## The conditions that would change this

Each is a measurable target, not a hope. A sleeve is promoted only when its own row's
condition is met *and* it beats the control on the terms in decision 0003.

The chain matters as much as the rows. What a shareholder receives is
`premium × delivered loading − cost`. Experiment 002 measured the second and third and
found the loading delivered and the cost measurable; Experiment 001 could not sign the
first for any factor. **No product can be promoted while its underlying factor is
unsigned**, which is why every product row below points back at a factor row.

| Candidate | Condition for promotion |
| --- | --- |
| Value, profitability | A post-publication window with more than the current 12–26% power against the 2.0 pp/yr materiality threshold; a **measured** long-only capture fraction; and a product meeting Experiment 002's frozen promotion protocol — loading ≥ 0.15 with a 95% interval excluding 0.15 from below, the same on both fixed halves, shortfall ≤ 0 pp/yr against a replication fitted on a **prior** window, and total cost of ownership including realised distributions and turnover ≤ 1.0 pp/yr |
| Momentum | A net premium computed from **observed** turnover rather than assumed tiers, with one-sided monthly turnover below 50%; and more than one investable product, since the entire retail shelf clearing a $1bn / 0.60% screen is one fund — MTUM, which delivers its exposure and was still `rejected` on cost |
| Investment (CMA) | Re-entry requires a new frozen specification on a genuinely post-2026 window. The current rejection stands |
| Size | A premium test that has never been run, plus the same product protocol |
| Trend | A multi-asset attribution leaving a residual after non-US-equity exposures; a fund-level audit on a licensed total-return source with real fees; and a contract-level test of the volatility scaling, which no public aggregate can support |
| Rebalancing as return | A real, investable, low-correlation pair whose drift gap is genuinely below its `gamma_star`. None was found; every pair tested correlated 0.72–0.79 in logs |
| Anything fund-level | A licensed, survivorship-free, point-in-time total-return source covering the listed shelf from at least 2003, so the window is 240 months rather than 72. Required contents are specified in the research framework under "The next experiment" |

**The immediate next step is not a promotion attempt, and it is not the purchase.** It
is Experiment 005, the regional replication of the post-publication premia across US,
developed-ex-US and emerging equity on files this repository has already downloaded and
hash-pinned. It attacks the only unsigned term in the chain, costs nothing, and is
decisive in both directions: either a factor advances, or public factor data is shown
to be permanently unable to sign these premia — at which point the licensed purchase
should **not** be made for factor products, because it buys the two terms that already
work.

## Alternatives considered

**Promote the trend sleeve as `exploratory` and build it.** Rejected. Its own
specification caps a vendor-series evaluation at `exploratory`, its falsifier fired,
and the vendor states no cost basis anywhere in the archived workbook, so every
figure is gross of the vendor's own trading costs by omission.

**Promote RMW on the grounds that it is the only factor that did not decay (96%
retained).** Rejected. That is a prioritisation for future work, not a finding: its
post-publication interval includes zero, 59% of its premium is the single year 2021,
and its volatility carries an unresolved ±5.09% systematic band from Phase 1.

**Report the 2000–2019 era, in which annual rebalancing was worth +0.575 pp/yr and
cleared the materiality threshold twice over.** Rejected, and the rejection rule was
frozen in advance precisely so this could not be reported as a finding: it is one
twenty-year window inside a thirty-five-year sample, bracketed by two windows of the
opposite sign.

**Say nothing and leave the absence implicit.** Rejected. An unrecorded non-promotion
decays into an assumed promotion.

## Consequences

The deliverable of this research programme is a design map and a control, not an
allocation. An allocation becomes appropriate only after the investor policy is
defined — benchmark, horizon, tax status, liabilities, cash flows, drawdown
tolerance, liquidity reserve, permitted instruments and objective — which remains
open decision 1 in the research framework.

Steps 6 and 7 of the framework's build order — portfolio combination, then
fractional/risk-constrained Kelly and leverage — are blocked, and not on effort.
Step 6 combines sleeves and there are none; step 7 sizes an edge and there is none.

This record should be superseded, not amended, when the first sleeve is promoted.
