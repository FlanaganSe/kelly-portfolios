# 0003 — The cheap broad-market portfolio is the control every candidate must beat

Date: 2026-08-12. Status: accepted.

## Context

Five frozen experiments have now run. Across them, the comparator kept changing
shape, and in three separate places the comparator turned out to decide the answer:

- [Experiment 004](../research/trend-marginal-value.md) measured a trend sleeve at
  **+1.34 pp/yr** against the fully invested passive portfolio and at a much smaller
  margin against a **risk-matched cash** comparator, because part of the apparent
  gain was simply de-risking. Israelov's put-protection result is the same trap in
  the literature: 2.5%/yr of protected excess return looks like protection until a
  36.5% equity / 63.5% cash portfolio earns the same 2.5%.
- [Experiment 002](../research/factor-products.md) compared 44 factor ETFs
  against the market *and* against a fitted long-only combination of VTI, VUG, VTV
  and VB. That comparison is clause (c) of its falsifier, it **fired on 22 of 44** and
  is the single largest cause of the 24 rejections. MTUM is the decisive case: it
  delivers genuine, stable momentum exposure and was still `rejected`, because its
  shortfall to a three-fund combination was 1.22 pp/yr against a fee premium of 0.12.
  The comparator is fitted in sample, so it is a look-ahead best case for the
  combination — which is why the rejection reads as "four cheap funds beat this over
  these 72 months", not "this product is badly run".
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
implementation value, which is exactly where 22 of 44 products failed.

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
useful with zero alpha. That is the stated basis on which fifteen products reached
`exploratory` as implementation proxies, and this decision does not change it — it
only forbids describing such a product as an edge.

This decision is about the comparator, not about promotion. Nothing is promoted; see
[0004](0004-no-sleeve-promoted.md).
