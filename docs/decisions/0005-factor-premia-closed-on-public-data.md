# 0005 — Profitability and investment premia are closed on public data

Date: 2026-08-12. Status: accepted.

## Context

[Experiment 001](../research/factor-persistence.md) left HML, UMD and RMW
`unresolved`, not because their premia were shown to be absent but because **16 of
its 20 factor × era cells held a premium smaller than their own window could detect
at 80% power**. More United States history cannot fix that: the US post-publication
window is the length it is and it ends at the frozen sample boundary.

[Experiment 005](../research/factor-persistence.md#experiment-005--the-regional-replication)
was designed to settle it in one of two directions, with both branches of its
falsifier frozen before any number existed. It re-ran Experiment 001's
post-publication grid for HML, RMW and CMA across the US, developed-ex-US and
emerging Ken French files over the *same* frozen eras, pooled them under a
cross-region **joint** block bootstrap that preserves contemporaneous cross-region
correlation, and — this is the point — **measured** the effective sample size that
pooling actually bought rather than assuming it.

The measurement, on the full post-publication era of each factor:

| Factor | Months | Naive region-months | Effective region-months | Effective regions | ρ̄ | Pooled MDE₈₀ | Pooled premium |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HML | 384 | 1152 | **573** | 1.49 `[1.39, 1.68]` | 0.52 | 3.35 | **+4.74** `[+1.46, +8.10]` |
| RMW | 144 | 432 | **326** | 2.26 `[2.01, 2.65]` | 0.18 | **2.62** `[2.15, 3.07]` | +2.53 `[+1.07, +3.96]` |
| CMA | 144 | 432 | **253** | 1.76 `[1.60, 1.97]` | 0.38 | **3.41** `[2.60, 4.12]` | +0.20 `[−2.57, +3.44]` |

Branch (b) of the frozen falsifier fired for RMW and CMA: the measured pooled
minimum detectable effect at 80% power is above this repository's 2.0 pp/yr
materiality threshold. It fires at the point estimate, across the whole 90% sampling
interval of the MDE, and across the whole Phase 1 systematic volatility band. **RMW's
pooled premium of +2.53 pp/yr is smaller than the smallest premium its own pooled
window can resolve**, and RMW is the factor pooling helped *most*, because its three
regions are the least correlated in the grid.

Branch (a) fired for HML, which is now `exploratory`. UMD was not testable: the Ken
French momentum file registered and manifested in this repository is US-only.

## Decision

**No further experiment may be commissioned that attempts to sign the RMW or CMA
premium from publicly available factor data.** Both are `rejected` and the question
is closed, not paused.

This decision also fixes the general statement the measurement supports:

> On the Ken French public factor files, across every independent region the library
> distributes, **a post-publication premium between zero and about 2.6 percentage
> points a year cannot be signed at 80% power, however the regions are pooled.**

That floor — 2.62 pp/yr, RMW's pooled figure, the best across all nine pooled cells —
is above the 2.0 pp/yr materiality threshold this repository uses. It is a property
of the available data, not of the factors.

**What `rejected` means here, precisely.** It is the predeclared falsifier firing on
these series over these windows under this construction. It is **not** a claim that
the profitability or investment premium is zero, and it must never be reported as
one. The honest statement is that the publicly available evidence cannot sign the
premium either way, and that adding more of the same evidence provably will not.

**What it forbids.**

- No RMW or CMA sleeve, tilt, or product may be proposed on premium grounds.
- No re-pooling, re-weighting, re-windowing or re-blocking of these files may be
  offered as a new answer. The floor was measured under the frozen 12-month block
  with 6- and 24-month neighbours and the Politis–White automatic length reported
  for every cell, under equal and inverse-variance weights, and with and without the
  US leg. None of those changed a verdict.
- No product may be promoted because it *delivers* RMW or CMA exposure cheaply. The
  chain a shareholder receives is `premium × delivered loading − cost`, and an
  unsigned premium makes the product's own quality irrelevant to the decision
  ([decision 0004](0004-no-sleeve-promoted.md)).

## What would reopen it

Each is a measurable condition, not a hope. Any one of them reopens the specific
factor it names, under a **new** frozen specification.

| Condition | Why it would work |
| --- | --- |
| **A materially longer out-of-sample window.** RMW's and CMA's post-publication eras begin 2014-01 and are 144 months. The pooled MDE₈₀ scales as `1/sqrt(T)`, so reaching 2.0 pp/yr from 2.62 needs roughly **1.7× the months at the same effective region count — about 245 months, or a further decade** ending near 2035. | It is the same data, so nothing about the construction changes; only the sample grows. This is the honest waiting condition and the reason branch (b) is a closure rather than a defeat. |
| **A genuinely independent premium series, not another French region.** A licensed non-French construction of the same economic factor, on a different universe and a different vendor's accounting data, would add effective sample rather than correlated sample. | The measured constraint is *effective* sample size. Three French regions were worth 1.49 to 2.26 independent looks because they share construction, accounting definitions and global risk factors. A source that does not share them would be worth more. |
| **A regional sorted-portfolio source that supports a materially lower-variance estimator.** The pooled MDE₈₀ is proportional to the composite's volatility; a construction with the same premium and lower variance lowers the threshold directly. | This is the only route that does not require waiting for months to accumulate. It requires evidence that the alternative construction estimates the *same* premium, which is itself a research task. |
| **A change to the materiality threshold, argued and frozen first.** 2.0 pp/yr is this repository's own standard. | Stated for completeness and flagged as the dangerous one: lowering the threshold to clear a measured floor is fitting the standard to the result, and must be argued on investor-policy grounds before any premium figure is looked at, or not at all. |

**What does not reopen it:** a new Ken French vintage of the same files, a different
block length, a different pooling weight, a different era boundary inside the same
sample, the 2026-01-onward holdout (six to eight months against a 2.6 pp/yr floor),
or the 2013–14 CRSP vintage that would settle the Phase 1 band — that band is
checked cell by cell in both experiments and changes no conclusion anywhere.

## Alternatives considered

**Leave RMW and CMA `unresolved` again.** Rejected, and this is the decision's whole
point. `unresolved` absorbs effort indefinitely: it reads as "come back with more
data", and Experiment 005 was built specifically to determine whether more of the
available data exists. It does not. A measured statement that the question cannot be
answered from public data is more useful than a third invitation to try.

**Report RMW as `exploratory` on the grounds that its pooled interval `[+1.07,
+3.96]` excludes zero and its premium clears 2.0 pp/yr.** Rejected, and the
rejection rule was frozen in advance precisely so this could not be reported as a
finding. Its premium is below its own detection threshold, which means the interval
excluding zero is not evidence the window can carry; 62% of its US premium is the
single year 2021; and dropping the pooled composite's best calendar year takes it to
+1.79, below materiality. Clause (a5) failed on its own terms before branch (b) was
reached.

**Close HML too, for consistency.** Rejected. Branch (a) fired for HML on every one
of its five clauses, and the falsifier's whole design was that both branches be
decisive. Closing a factor whose premium exceeds its own measured detection
threshold would be applying the rule to the conclusion rather than the evidence.

**Extend the closure to UMD.** Rejected as unsupported. UMD was never tested
regionally, because no regional momentum file is registered or manifested here.
Closing it would claim a measurement that was not made. It stays `unresolved`, and
what would resolve it is a data acquisition.

## Consequences

- [Experiment 001](../research/factor-persistence.md)'s prioritisation of RMW as
  "the one worth looking at first", on the grounds that it retained 96% of its
  premium, is **superseded**. It retained its premium, and its premium is still
  smaller than the smallest one three regions of public data can resolve.
- The design map's Map C promotion conditions for profitability and investment are
  replaced by the reopening conditions above.
- The programme's remaining live question for factors is no longer the premium. For
  HML it is the **long-only capture fraction**, which no source read in this
  repository establishes and which the
  [edge decomposition](../research/expected-edge-decomposition.md) currently
  *assumes* at 0.40.
- [Decision 0004](0004-no-sleeve-promoted.md) stands: no sleeve is promoted. A
  factor reaching `exploratory` is not a sleeve, and every value product still has
  to pass [Experiment 002](../research/factor-product-audit.md)'s frozen promotion
  protocol on its own terms.
- All figures behind this record are gross of transaction costs, shorting costs,
  borrow, fees and taxes, on academic zero-investment long-short research portfolios
  a retail investor cannot implement. They are upper bounds of unknown tightness,
  and the pooled ones are looser than the US ones because emerging-market shorting
  is harder and dearer than US shorting.
