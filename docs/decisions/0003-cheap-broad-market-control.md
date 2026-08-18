# 0003 — The cheap broad-market portfolio is the control every candidate must beat

Date: 2026-08-12. Status: accepted. Amended 2026-08-17 after Experiments 014 and 015,
which measured how much the *composition* of a fitted comparator decides — on the US shelf
and then on the ex-US one, with opposite answers — and which added the placebo and coverage
obligations to clause 2. **The rule itself has not changed.**

## Context

Across the frozen experiments the comparator kept changing shape, and in five separate
places the comparator turned out to decide the answer:

- [Experiment 004](../research/trend-marginal-value.md) measured a trend sleeve at
  **+1.34 pp/yr** against the fully invested passive portfolio and at a much smaller
  margin against a **risk-matched cash** comparator, because part of the apparent
  gain was simply de-risking. Israelov's put-protection result is the same trap in
  the literature: 2.5%/yr of protected excess return looks like protection until a
  36.5% equity / 63.5% cash portfolio earns the same 2.5%.
- [Experiment 002](../research/factor-products.md) compared 44 factor ETFs
  against the market *and* against a fitted long-only combination of VTI, VUG, VTV
  and VB. That comparison is clause (c) of its falsifier, it **fired on 22 of the 44 its
  census frame could see and on 35 of the 109 the corrected frame finds**
  ([Experiment 013](../research/factor-products.md#the-us-shelf-on-the-corrected-frame)), and
  is the single largest cause of the 24 rejections. MTUM is the decisive case: it
  delivers genuine, stable momentum exposure and was still `rejected`, because its
  shortfall to a three-fund combination was 1.22 pp/yr against a fee premium of 0.12.
  The comparator is fitted in sample, so it is a look-ahead best case for the
  combination — which is why the rejection reads as "four cheap funds beat this over
  these 72 months", not "this product is badly run".
- **The composition of that combination is itself a choice, and how much it decides is
  measured — on both shelves, with opposite answers.**
  [Experiment 014](../research/factor-products.md#what-the-comparator-decided-measured)
  re-scored all 109 US products under six bases and changed nothing else. The clause (c)
  count moves from 35 to 26 and the `exploratory` count from 48 to 49 under a complete cheap
  style grid — but **two placebo bases, which add as many columns while adding no new
  size-by-style cell, move more verdicts than the expressive ones do**. So the rule this
  record establishes stands, and it acquires a second obligation: **a fitted comparator
  needs a placebo comparator beside it**, or a movement in the count cannot be attributed to
  what the added funds express.
- **That placebo result does not generalise, and the ex-US shelf is what proves it.**
  [Experiment 015](../research/factor-products.md#what-the-ex-us-comparator-decided-measured)
  re-scored all 25 ex-US products under seven bases, **pairing each expressive basis with a
  placebo matched on column count**, which is stronger than Experiment 014's single pairing.
  The placebos moved **0, 0 and 1** verdicts against their partners' **1, 0 and 4** — the
  reverse of the US shelf, where they moved 9 and 15 against 1, 5 and 5. So a placebo is
  **not** a correction factor that can be measured once and reused; **it has to be run
  beside every fitted comparator, on that comparator's own shelf**. Where clause (c) turns
  out to be informative, what it says need not be welcome: on the ex-US shelf a basis that
  can express developed small value, quality and momentum **rejects four of the twelve
  products that had reached `exploratory`**.
- **A comparator that is not there is a different defect from one that cannot express
  something.** Both audits drop a basis constituent that does not cover a fund's own months.
  On the US shelf every constituent covers all 72 months and the rule never binds. On the
  ex-US shelf it decides three of the five clause (c) figures: `GWX` and `RODM` file from
  2019-07 and are therefore replicated by **VEA at weight 1.000**, and `MFEM` gets no
  replication at all. Trimming GWX's window by the one month no comparator covers takes its
  shortfall from +1.24 to **+0.09** — below the threshold that rejected it — on the largest
  intended loading in the whole ex-US audit.
- [Experiment 002](../research/factor-products.md) also measured a **model-misfit
  pedestal**: VTI, which *is* the market portfolio, prices at −0.55 pp/yr alpha under
  FF5+UMD over 2020–2025. Every fund alpha in that window must be read as a distance
  from −0.55, never from zero.

The [edge decomposition](../research/expected-edge-decomposition.md) adds the reason
this cannot be left implicit: the three benchmarks it uses — a stated index, the
investor's own counterfactual, and the average investor — carry central edges of
24 bp, 89 bp and 15 bp with tracking errors of 401 bp, 41 bp and 150 bp. They never
aggregate, and conflating them is the standard way this argument is inflated.

## Decision

**The control is a cheap, broad, long-only, fully invested market portfolio**, and
every candidate sleeve is measured against it. Concretely, every future result must
report:

1. **Which benchmark** it is measured against — stated index, own counterfactual, or
   average investor — and **its certainty class**, deterministic or probabilistic. A
   number without both is not reportable.
2. **A cheap-combination comparator**, not the market alone, whenever the candidate
   is a product or a tilt. The combination is a long-only, fully invested mix of
   cheap broad funds fitted to the candidate's own exposures. Because it is fitted in
   sample it is a best case for the combination and a deliberately hard test for the
   candidate, and that look-ahead must be stated wherever the number appears.
   Two conditions on that comparator, both of which came from measurement rather than
   principle:
   - **A placebo comparator beside it**, matched on column count and adding no new cell,
     run on the same shelf as the comparator it bounds. Its movement is reported beside the
     expressive one, never after it. A result from another shelf does not substitute.
   - **Every constituent covers the whole window**, and the run aborts if one does not — or,
     where the shelf makes that impossible, **the number of columns each candidate's fit
     actually had is reported per candidate**. A comparator that was not there and a
     comparator that could not express something produce the same number and are not the
     same finding.
3. **A risk-matched comparator**, not the fully invested portfolio, whenever the
   candidate changes portfolio risk. Matching is on an ex-ante risk budget with the
   same lagged estimator and the same exposure cap applied wherever logically
   possible.
4. **The model-misfit pedestal**, whenever an alpha is quoted: the same model's alpha
   on a total-market fund over the identical window.

The control does not have to be beaten on a point estimate. It has to be beaten on
the candidate's own predeclared primary metric, net of the costs the candidate
actually pays, with an interval, after multiple-testing correction across the whole
search.

## Alternatives considered

**The market index alone.** Rejected. It cannot separate exposure delivery from
implementation value, which is exactly where a third of the products fail. **The count
that decides how damning that is depends on the census frame**: 22 of 44 on Experiment
002's, 35 of 109 on the corrected one, and 13 of the 65 funds the correction admits.

**Equal weight, or a minimum-variance baseline.** Rejected as *the* control, retained
as mandatory comparators in the construction tournament. Both are constructions with
their own estimation error; the cheap broad market is the only comparator whose
delivery is contractual rather than estimated.

**A per-experiment comparator chosen at write-up.** Rejected explicitly. The
benchmark decides the answer, so it must be frozen in the specification before any
result is examined — which is what Experiment 004's specification did, and why its
+1.34 pp/yr figure is reported against cash rather than against the benchmark that
would have flattered it.

## Consequences

The evidence card in the product contract gains two required fields, benchmark and
certainty class.

Any future product experiment must build the cheap replication before it estimates
an alpha, which costs a fitting step and removes the option of quoting a raw alpha.

A candidate that merely delivers a cheap, stable, desired *exposure* can still be
useful with zero alpha. That is the stated basis on which the `exploratory` products are
implementation proxies at all, and this decision does not change it — it only forbids
describing such a product as an edge. **What the two comparator experiments change is that
the count of such products must always name the basis it was computed on**: 48 US products
on the frozen comparator and 47 to 49 across comparators that can express what they
deliver, 12 ex-US products on the frozen comparator and **8 that survive one that can**.

This decision is about the comparator, not about promotion. Nothing is promoted; see
[0004](0004-no-sleeve-promoted.md).
