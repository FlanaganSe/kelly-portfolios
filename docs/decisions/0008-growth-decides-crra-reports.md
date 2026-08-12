# 0008 — Geometric growth decides; the certainty equivalent reports beside it

Date: 2026-08-12. Status: accepted.

## Context

Three experiments in this repository judge a candidate by a CRRA certainty equivalent
at `gamma = 3`, computed exactly over 35 non-overlapping calendar-year returns:
[Experiment 003](../research/rebalancing-policy.md),
[Experiment 004](../research/trend-marginal-value.md) and Experiment 010, the marginal
sleeve valuation. The choice looked conservative. It is not: **on that metric a
candidate is paid for reducing risk, and the payment can exceed the materiality
threshold on its own.**

Experiment 010 measures the payment, because it carries a control designed to have no
value at all. Its `cash_control` is cash added to a 100% equity core and funded pro
rata from it, so it supplies **zero alpha and zero diversification credit by
construction**. At the frozen 10% weight, on the net-pessimistic cost column, over
1991–2025:

| Cash control, pro-rata funding | pp/yr |
| --- | ---: |
| Marginal certainty equivalent, `gamma = 3` | **+0.166** |
| Marginal geometric growth rate, `gamma = 1` | **−0.643** |
| De-risking component (the difference) | **+0.809** |
| Frozen materiality threshold | 0.30 |

A sleeve that supplies nothing is handed **+0.809 pp/yr, 2.7 times the materiality
threshold**, purely for holding less equity — enough to carry a sleeve over the bar
from a real growth contribution of −0.5 pp/yr. That is not a defect in the machinery:
the growth reading comes out correctly negative, which is what the machine check was
for. It is a property of the metric.

**The mechanism, and how much of it no model predicted.** The second-moment
approximation the decomposition uses, `(mu_i − mu_f) − gamma (sigma_ip − sigma_fp)`,
does predict part of it: raising `gamma` from 1 to 3 triples the credit term and moves
the control's predicted marginal from −0.582 to −0.148 pp/yr at the reference weight, a
de-risking allowance of +0.434. The **realised** allowance is +0.809. The extra
**+0.376 pp/yr is a left-tail reward that the second-moment model never sees**: exact
CRRA utility over only 35 observations weights the realised worst years far more
heavily than a variance does, and cash is what was not in equities during them. Two
further facts settle that this is measurement error rather than value:

- Even at `gamma = 3`, the **model** says the cash sleeve **costs 0.148 pp/yr**. The
  only thing that makes it look profitable is the exact utility over 35 points.
- Under `cash` funding — where the sleeve *is* the funding leg — the de-risking
  component collapses to **−0.0005 pp/yr**. The reward appears exactly when the sleeve
  removes equity and nowhere else.

**The comparator decides how much this matters, and two experiments bracket it.**

| | Comparator | CE basis | Growth basis | Agreement |
| --- | --- | ---: | ---: | ---: |
| **Exp 004** headline, 15% trend sleeve | **risk-matched cash** | +1.342 | +1.312 | **97.8%** |
| **Exp 010** cash control, 10% weight | the portfolio it de-risks | +0.166 | −0.643 | **−387%** |

Experiment 004's two arms carry 7.65% and 7.88% annualised volatility, so the
de-risking is already removed from both sides before the difference is taken and only
**+0.030 pp/yr** of its headline is de-risking. Experiment 010's comparator is the
portfolio the sleeve de-risks, so the whole of the gap survives into the answer — the
gap is **487% of the certainty-equivalent figure itself**. The metric is not the
problem in isolation; the metric *without a risk-matched comparator* is.

The repository has, separately, already
[declared its objective to be net geometric growth](../research/portfolio-edge-research-framework.md),
and [decision 0003](0003-cheap-broad-market-control.md) already requires a risk-matched
comparator whenever a candidate changes portfolio risk. This record closes the gap
between those two commitments and the number the experiments actually read.

## Decision

**Geometric growth — the `gamma = 1` certainty equivalent, which is the geometric mean
of the calendar-year gross returns minus one — is the metric that decides every
materiality threshold and every falsifier clause. The CRRA certainty equivalent is
reported beside it, never alone and never as the deciding number.**

The rationale is one sentence: **the de-risking component is not an edge, because any
investor obtains it free by holding less equity.** A sleeve that clears a bar on it has
been paid for something it did not supply, and the investor could have had the same
thing for nothing.

Four constraints make this enforceable rather than rhetorical.

1. **Every deciding figure names its basis.** A marginal figure published without
   `deciding_basis` beside it is not reportable. Specifications carry
   `parameters.decision_gamma`; a specification frozen before this record and not naming
   one falls back to its `crra_gamma`, which is what it meant.
2. **The pair travels together.** Growth, the CRRA certainty equivalent, and the
   de-risking component that separates them are published as three numbers or as none.
   Publishing only the growth figure would hide how much risk a sleeve removes, which
   is the opposite error and equally bad. This is why the certainty equivalent is
   *retained* rather than deleted.
3. **A certainty equivalent may be a primary metric only against a risk-matched
   comparator**, in the sense [decision 0003](0003-cheap-broad-market-control.md)
   clause 3 already requires: matched on an ex-ante risk budget with the same lagged
   estimator and the same exposure cap. Experiment 004 is the worked example of what
   that buys — 97.8% agreement between the two bases. Without it, the two bases are
   answering different questions and only the growth one is answering the asked one.
4. **A control with no value by construction is the calibration**, and every experiment
   whose metric could reward de-risking carries one. Experiment 010's cash control is
   the model: it costs one cell of compute, it cannot promote anything because it is
   excluded from the multiple-testing family, and it is the only reason this error was
   found rather than published.

## What this changes, concretely

**Experiment 010's family is now `rejected`, not `unresolved`.** The metric change
rewrites a frozen falsifier, so it is not a bug fix and could not be handled as a
re-run of exp_010's specification the way the convexity defect in exp_004 was. A new
specification, `exp_010b_growth_basis`, was frozen: identical inputs, vintages,
portfolios, sleeves, costs, window, eras and **seed**, differing only in
`decision_gamma`. exp_010 keeps its own hash, its own runs and its recorded
`unresolved`; exp_010b supersedes it on what the repository should believe, and adds
**zero trials** to the search, because it re-judges data already spent.

Seven sleeves cleared the 0.30 bar on the certainty equivalent. **Six fail it on
growth**: trend 1.172 → 0.258, the US momentum overlay 0.734 → −0.299, the
developed-ex-US overlay 0.886 → 0.007, the emerging overlay 0.924 → 0.202, long-only US
momentum 0.321 → 0.269, and the modelled long-duration Treasury proxy 0.492 → −0.385.
Only US small value survives the bar, 0.590 → 0.392, and it is rejected anyway on the
negative-credit and Holm clauses. The proxy was exp_010's **sole** non-rejected sleeve,
reaching `unresolved` only because no rejection clause fired; on growth, clause (a)
fires and clause (c) with it, and nothing is left unresolved.

The change is not uniformly hostile clause by clause, and the exception is recorded
rather than suppressed: emerging small value goes **0.248 → 0.543** and clears the bar
on growth having failed it on the certainty equivalent, because its de-risking
component is **negative** — it adds risk, and the CRRA metric was charging it for that.
It stays `rejected` on Holm alone.

**Experiments 003 and 004 do not move**, which was checked from their own published
artifacts rather than assumed. Every exp_003 policy is negative against buy-and-hold on
**both** bases at every cost basis, and its largest de-risking component anywhere is
0.111 pp/yr; the best policy's identity changes (annual calendar → 25% relative
threshold) and both remain far below the 0.25 threshold, so the `rejected` status and
every clause are unmoved. exp_004's headline is 97.8% growth, as above.

## Alternatives considered

**Keep the certainty equivalent and raise the threshold to cover the de-risking.**
Rejected. The de-risking component is not a constant: it ranges from −0.295 to +1.033
pp/yr across exp_010's own sleeves and depends on the funding leg, so no single
threshold covers it. A threshold that absorbed the worst case would be 1.03 pp/yr and
would reject genuine value along with the artefact.

**Lower `gamma` to 2 rather than to 1.** Rejected. It shrinks the artefact without
removing it and buys an argument about the right value in exchange. `gamma = 1` is not
a milder preference — it is the *absence* of a preference term, and it is the objective
the repository already declared. Any `gamma > 1` reintroduces a term that pays for risk
reduction, and there is no principled stopping point between 1 and 3.

**Delete the certainty equivalent.** Rejected, and this is the constraint most likely
to be violated later by someone tidying up. Growth alone cannot say how much risk a
sleeve removes, which is a real thing an investor is entitled to know and to want. The
error was never computing it; it was letting it decide. Reporting it beside growth,
with the difference named, makes the de-risking visible instead of both hidden and
decisive.

**Edit exp_010's frozen specification in place.** Rejected, firmly. The committed YAML
is evidence precisely because it was written before the result was read; editing its
falsifier after reading the result destroys that, whatever the edit says. Git would
hold the history but no reader of the file would see a pre-registration. A superseding
specification costs one file and preserves the property.

**Treat the change as suspect because it was made after the results were seen.** Not
rejected — recorded, because it is the honest objection and it is right about the
direction of danger. Two things bound it. The change was calibrated on a **control that
carries no hypothesis** and whose correct answer was known before any data was seen.
And it is **strictly hostile**: it removes a reward, raises the effective bar for every
sleeve that was clearing it on de-risking, and moves a family's status to a worse one.
A metric changed after the fact that made everything look better would be worthless;
this one makes everything look worse, which is the only direction in which such a
change is cheap to trust.

## Consequences

- **Every future specification names `decision_gamma`.** Omitting it is not a neutral
  default; it silently inherits the pre-0008 meaning, which is why the fallback is
  documented at the point it applies rather than left implicit.
- **Any experiment reporting a certainty equivalent as a primary must build a
  risk-matched comparator first**, which costs a volatility estimator and an exposure
  cap. Experiment 004 already pays that cost. Nothing else in the repository does, so
  nothing else may quote a certainty equivalent as its deciding number.
- **A "de-risking component" field is now part of a reportable marginal figure**, on
  the same footing as an interval and a cost basis. A figure quoted without it is
  incomplete in the same way a tilt quoted without its tracking error is
  ([decision 0006](0006-reference-portfolio-without-promotion.md) constraint 3).
- **Downstream pages that quote a certainty equivalent as a verdict now carry a
  superseded framing**, and each has to be re-read against this record before it is
  cited again. That coupling is the cost of having let one metric decide three
  experiments.
- **Nothing is promoted or demoted by this record except exp_010's family.** No sleeve
  moves; [decision 0004](0004-no-sleeve-promoted.md) stands in full, and the change
  makes the case for promotion strictly harder rather than easier.
- Supersede this record, do not amend it, if a risk-matched comparator is ever built
  for the portfolio-marginal question: the third constraint would then permit a
  certainty-equivalent primary in a place it currently forbids one.
