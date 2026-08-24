# 0009 — The blocked steps are unblocked, and a closure must carry its instrument

**Status:** superseded as live research governance by
[decision 0010](0010-bars-carry-a-reopening-condition.md). Retained as the historical record
of the specification and interpretation corrections it documents.

Date: 2026-08-22. Status: accepted. Amends
[0004](0004-no-sleeve-promoted.md) (the step 6 and step 7 blocks) and
[0005](0005-factor-premia-closed-on-public-data.md) (the scope of its closure).
The non-promotion in 0004 and the measured floors in 0005 are unchanged.
**Items 1 and 7 are carried out by [decision 0010](0010-bars-carry-a-reopening-condition.md)**,
which restates the affected verdicts, demotes the two constants, and sets the rule that a bar
without a reopening condition is a finding.

## Context

This programme has produced a wall of nulls. Some of that is the world. A measurable
share of it is the verdict rules, and the repository had already written down most of the
evidence without acting on it.

**Four rules were doing the work.**

1. **A bar finer than the instrument.** Experiment 010's falsifier rejects a sleeve whose
   marginal gain is below **0.30 pp/yr**. The same page measures that instrument's
   detection floor at **MDE₈₀ 1.039 pp/yr** and says so plainly: *"A null here is a
   statement about resolution before it is a statement about gold."* The falsifier has an
   `unresolved` branch for exactly this case — "the effect is smaller than its own MDE" —
   but clause (a) is evaluated first and short-circuits it. Seven sleeves carry a
   `rejected` produced by an instrument that could not have seen the effect.

2. **Family-wise control on a screening pass.** The same falsifier requires survival of
   Holm at 0.05 across ten sleeves on a first exploratory search of 420 months. Seven of
   twelve candidates carry *p* = 1.0000. A screening stage under FWER at 0.05 cannot
   promote anything in principle, and the page concedes the family of ten is itself
   *"a lower bound on the correction the whole search requires."*

3. **The zero-leverage rule, which sets the bar it is judged against.** Three pages agree
   and none acts. [Capital efficiency](../research/capital-efficiency-and-breadth.md)
   conclusion 1: *"The zero-leverage rule is not a free conservatism; it is the reason
   the marginal-sleeve programme returned nulls."* Decision 0004 derives why — under
   pro-rata funding the first sleeve dollar must clear `a_p − sigma_p**2 (1 − beta)`,
   under a financed overlay only `rho sigma_p sigma_d`, and the difference is
   `sigma_p**2 (L_p* − 1)` = **+2.44 pp/yr**, in which every term involving the sleeve
   cancels. That is larger than any premium the programme has attempted to measure. 0004
   then states: *"Neither block is lifted by this record."*
   [Setting the equity share](../research/setting-the-equity-share.md) closes with
   *"Nothing here reopens the zero-leverage rule."* The cost is measured, agreed, and
   left in place by every page that measures it.

4. **Closures stated more strongly than their evidence.** 0005 reads *"closed, not
   paused"* and *"provably will not"*, while one of its own reopening conditions is the
   passage of about a decade — which [search coverage](../research/search-coverage.md)
   already flags: *"Its framing … is stronger than the evidence."* The client hardened it
   further, shipping the word *"permanently"*, which the decision never used.

**The same failure has a documented history on the data side.** Six sources were recorded
as unavailable and were published throughout, the last already sitting in
`data-manifests/`. `research/README.md` drew the right lesson and it never reached the
always-on file: *"Check the **reasoning** of any decision that appears to forbid a source
… decision 0002 bans free price feeds because they drop distributions and mishandle
corporate actions, and neither failure mode exists for an asset that pays nothing."*

**Two undefended constants sit underneath all of it.** The 2.0 pp/yr materiality
threshold and the 0.30 pp/yr sleeve bar are derived nowhere, justified nowhere and
sensitivity-tested nowhere. "Floor above bar" is the mechanism behind every null in the
programme.

## Decision

**1. A verdict may not be stronger than the instrument that produced it.** When a
falsifier's bar sits below the design's own minimum detectable effect, the terminal
status is `unresolved`, not `rejected`, and the MDE is reported in the same sentence.
A specification whose bar is finer than its floor is a specification defect, and the
defect is recorded rather than the verdict.

**2. A screening pass is corrected for false discovery, not family-wise error.** Holm at
0.05 belongs to a confirmatory stage with a promotion at the end of it. An exploratory
search reports Benjamini–Hochberg, states the family it corrected over, and states what
that family omits.

**3. The funding rule is a research question and is unblocked.** Step 7's block is
lifted for *measurement*. Whether a sleeve has positive marginal value depends on how it
is funded, so an experiment may run overlay funding as its primary arm with pro rata as
robustness, provided every arm is reported against a leverage-matched control.
**This does not authorise leverage in a recommended portfolio.** The zero-leverage
default for what this repository recommends is unchanged and 0004's non-promotion stands.
What changes is that the programme may now measure the rule instead of assuming it.

**4. Step 6 is unblocked and the construction tournament may run.** It compares weighting
methods — market weight, equal weight, inverse volatility, constrained minimum variance,
linear-shrinkage minimum variance, equal risk contribution — on assets that already
exist. It needs no promoted sleeve. It is the only designed experiment that treats a
portfolio as a joint object, it costs nothing, and three pages have said it should run.

**5. A closure carries its instrument, its window and its design, in the same sentence.**
"Closed", "cannot" and "permanently" without those three are not permitted. The honest
form of 0005 is: *no re-pooling, re-weighting, re-windowing or re-blocking of the French
files can sign a premium below about 2.6 pp/yr at 80% power.* That is a statement about
an instrument. It does not forbid a different **estimand**, a conditional or panel
design, a non-French construction, or a lower-variance estimator — and the framework's
own literature ledger records that switching the estimand moved one published replication
rate by **21.1 points with no new data**.

**6. A rule written against a failure mode does not reach a case that cannot exhibit it.**
Check the reasoning of any rule that appears to forbid a source, a method or a
comparison, before treating it as a bar.

**7. The two constants are now open questions, not settings.** The 2.0 pp/yr materiality
threshold and the 0.30 pp/yr sleeve bar must be derived or replaced. Until they are, they are
reporting reference points and may not be the operative clause of a new falsifier
([decision 0010](0010-bars-carry-a-reopening-condition.md), clause 4). Search coverage §5
already proposes deriving the sleeve bar from `sigma_p**2 w`, which is the arithmetic
ceiling on a diversification credit rather than a round number.

## Alternatives considered

**Leave the blocks and loosen nothing.** This is what 0004 chose twice, and the cost is
now measured rather than argued: every marginal-sleeve verdict in the repository was
taken against a hurdle inflated by ~2.44 pp/yr by a rule adopted for prudence.

**Lift the blocks and permit levered recommendations.** Rejected. The measurement
question and the allocation question are separable, and only the first is unblocked here.
The drawdown ceiling — a resampled `P(deeper)` that doubles between w=0.58 and w=0.60 —
is an argument about holdability that no funding-rule result touches.

**Re-run every rejected sleeve under the new rules and republish the verdicts.**
Rejected for now. Statuses are set by frozen specifications, and rewriting a verdict
after seeing its result is the failure the ledger exists to prevent. The correct route is
a new specification, frozen, with the corrected clauses — which is search coverage §5
item 1.

## Consequences

- **Sleeve verdicts stronger than their instrument are restated rather than annotated.**
  Every one of Experiment 010b's ten sleeves has a point estimate inside the design's own
  ±0.58 pp/yr floor, so none of them was resolvable.
  [Decision 0010](0010-bars-carry-a-reopening-condition.md) clause 3 moves the six whose only
  firing clauses were the sub-floor bar or Holm to `unresolved`, and leaves the four that
  fired a sign or boundary clause as `rejected`. Each is reported with its floor beside it,
  and no page may quote one as evidence of absence.
- **The re-specified marginal-sleeve experiment is round two's first item**, with the
  whole weight grid to the cap, a bar derived from `sigma_p**2 w`, overlay funding
  primary, and a leverage-matched control on every arm.
- **The construction tournament is unblocked and unowned.** It is free.
- **`unresolved` will become more common and `rejected` less common.** That is the
  intended direction: this repository's failure mode was never excessive optimism.
- **0005's reopening conditions stand**, and the fourth — a lower-variance estimator on
  the same files — is now explicitly permitted rather than implicitly forbidden.
- The client must stop shipping the word "permanently" for 0005's closure.
