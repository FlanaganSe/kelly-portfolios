# 0006 — A named-fund reference portfolio may be published without promoting a sleeve

Date: 2026-08-12. Status: accepted.

## Context

[Decision 0004](0004-no-sleeve-promoted.md) states that "the deliverable of this
research programme is a design map and a control, not an allocation", and that "an
allocation becomes appropriate only after the investor policy is defined". That
condition is not met: framework open decision 1 is still open, and no experiment has
declared a horizon, liability model or drawdown tolerance.

Read literally, that forbids the thing the project exists to produce. Read as
intended, it forbids something narrower — presenting an allocation as though the
research had *validated* it. The two readings need separating, because the cost of the
literal one is now visible:

- The design map records, per candidate, what would have to become true before it
  could be held. It does not say what to hold **now**, so a reader who wants an answer
  must assemble one themselves from nine research pages, and will assemble it wrong.
- The largest measured result in the repository — a contractual **~109 bp/yr** against
  the investor's own counterfactual, 99% confident in about twelve months
  ([structural and tax-aware edges](../research/structural-and-tax-edges.md)) — is
  bought entirely by decisions a design map cannot express: which fund, which wrapper,
  which account, which lot. **Withholding the construction withholds the only
  near-certain edge the repository has found.**
- The absence has already caused a specific error. Experiment 004's index verdict was
  repeated to the project owner as though it applied to KMLM, DBMF and CTA, which were
  never tested. That error is recorded on
  [its own page](../research/trend-marginal-value.md#two-transfers-a-reader-will-be-tempted-to-repeat). A
  page that names products and states exactly what was measured on each is the
  structural fix.

## Decision

**A reference portfolio naming concrete funds, weights and accounts may be published,
provided it makes no promotion claim.** It lives in
[`docs/research/portfolio-recommendation.md`](../research/portfolio-recommendation.md)
and nowhere else.

"Recommended" in that page means, and may only mean, **the best-supported construction
given the evidence**. It does not mean the construction is expected to beat an index,
and it does not advance any sleeve's status.

Four constraints make that separation enforceable rather than rhetorical.

1. **Every holding carries the status of what it buys**, in the closed vocabulary,
   with the experiment that set it. A holding whose status is `exploratory` must say
   so beside its weight.
2. **Every holding carries its evidence class** — contractual, risk premium, risk
   control, or "nothing better exists" — and the class governs how the line may be
   described. A risk premium may never be described as an edge.
3. **Every tilt is priced in confidence terms**, not in expected return alone: edge,
   tracking error, probability of being ahead at a stated horizon, and the horizon to
   90% confidence, from
   [`studies/outperformance_horizon.py`](../../research/src/portfolio_edge/studies/outperformance_horizon.py).
   A tilt quoted as "+X pp/yr" without its tracking error is not reportable.
4. **The investor-policy inputs that remain missing are stated on the page**, and the
   one parameter the evidence cannot set — the equity/bond split — is presented as the
   investor's choice with the others held fixed.

The page is subordinate to the [research framework](../research/portfolio-edge-research-framework.md):
it may not state a premium, a status or a cost that the framework or a linked
experiment page does not.

## What this does not change

- **No sleeve is promoted.** Decision 0004 stands in full, including zero leverage,
  rebalancing as risk control only, and the `exploratory` products being usable as
  implementation proxies and for nothing else — forty-eight on the US shelf and twelve
  ex-US, of which eight survive a fair comparator.
- ~~**No number from `research/` may appear in the shipped application as a finding**~~
  **Amended by [decision 0007](0007-application-may-render-research.md):** the
  application may render a finding provided its status, date, interval and source
  travel with it. The ban on shipping *price data* is separate and still stands
  ([decision 0002](0002-no-research-grade-free-price-source.md)).
- **The cheap broad-market portfolio remains the control**
  ([decision 0003](0003-cheap-broad-market-control.md)). The reference portfolio *is*
  that control plus placement discipline plus two optional `exploratory` sleeves; it
  is not a competitor to it.

## Alternatives considered

**Publish nothing until the investor policy is defined.** Rejected. The policy inputs
that are missing bear on one parameter — the equity/bond split — and on the size of the
optional sleeves. They do not bear on fund choice, account placement, lot discipline or
turnover, which is where the measured edge is. Withholding all four because one is
unsettled is a worse error than stating the fourth as a range.

**Publish a portfolio without naming funds.** Rejected. "Hold a cheap broad-market
fund" is unfalsifiable and unimplementable; naming VTI at 3 bp against a measured 0.55
bp spread, and stating the date, is both. The cost is that fund-specific facts decay,
which the page handles with dated facts and a stated review trigger rather than by
staying vague.

**Add the reference portfolio to the framework instead of a new page.** Rejected under
the one-canonical-place rule, and for the opposite reason to usual: the framework
answers whether a return source is *real*, and mixing "what to hold" into it would let
a construction choice inherit the framework's evidentiary authority. Two pages with
sharply different questions is the correct split; a third page on the same question
would not be.

**Let the page state a probability of beating the market.** Rejected. Against a cheap
index the honest budget is ~5.4 bp against 313 bp of tracking error and a 0.538
thirty-year probability, which is not a claim worth making and is trivially
misreadable as one that is.

## Consequences

- The repository now has two audiences and two entry points: the framework for whether
  a return source is real, and the recommendation page for what to hold. `docs/README.md`
  must keep both visible and must not let a reader mistake the second for a finding.
- Any status change in any experiment obliges a check of the recommendation page, since
  every holding on it cites a status. That coupling is deliberate and is the cost of
  naming funds.
- Fund-specific facts on that page decay on a timescale of months. It carries a review
  trigger — the SEC multi-class order count and the per-fund fee table — and a
  standing instruction to re-check rather than re-quote.
- Supersede this record, do not amend it, if a sleeve is ever promoted: the
  recommendation page's meaning of "recommended" would then have to change.
