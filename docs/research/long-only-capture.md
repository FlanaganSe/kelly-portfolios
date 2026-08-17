# The long-only capture fraction: what a tilt delivers of a long-short premium

**Question.** Every factor premium measured here is an academic long-short spread — long
the high-scoring portfolio, short the low, zero net investment, gross of every cost. A
retail investor cannot hold one. What fraction does a long-only tilt actually deliver?

**Decision it informs.** The [edge decomposition](expected-edge-decomposition.md) budgets
21 bp/yr for its factor line by *assuming* a 0.40 capture, and the framework recorded four
separate times that no source read there establishes the number. This page replaces the
assumption with a measurement. Out of scope: whether any tilt is worth holding, which
needs the whole of `premium × loading × capture − cost`.

**Status: `rejected`, and the rejection is the finding.** What is rejected is not the
capture fraction. It is the premise that there *is* one.

---

## Conclusion

**There is no benchmark-free long-only capture fraction.** Measured on the same months,
from the same file, with the same long-only portfolio, five defensible benchmarks give
capture fractions spanning **0.846** — more than twice the 0.40 the edge budget assumes,
and nearly three times the 0.30 threshold frozen in advance as the point at which a
multiplier stops being a multiplier. Clause (1) fired.

The number to use, and the only one entitled to be called a *value* capture:

> **The size-neutral long-only value capture of HML is `0.520`, two-sided 90% interval
> `[0.434, 0.722]`, over 1963-07…2025-12 (750 months).** Over the post-publication era it
> is `0.574 [−0.295, 1.288]` and over the longest available window `0.543 [0.480, 0.644]`.
> Every one is **gross**, and the two shorter ones are marked **UNSTABLE**: the denominator
> is a premium that is not reliably signed, so the ratio has no finite variance.

Four results follow.

1. **The reconstruction is exact.** `HML = 0.5(SH + BH) − 0.5(SL + BL)` reproduces the
   published HML column to a maximum absolute residual of **0.005 pp/month** over 1,194
   months — exactly half the last printed digit, the best a two-decimal file admits. The
   long legs read here are the legs of the factor Experiments 001 and 005 measured, not a
   lookalike.
2. **Roughly half, and for a structural reason.** Against a size-neutral benchmark the
   capture lands at 0.46–0.54 in the US, in developed ex-US, in emerging markets, and for
   momentum as well as value. **That stability is arithmetic, not evidence**: a long leg is
   one half of a symmetric three-bucket spread, so subtracting the equal-weighted six
   recovers close to half of it almost whatever the data do.
3. **Against the market it looks far better, and the difference is size, not value.**
   `0.958` full sample. Holding the small and big halves at 50/50 against a market that is
   overwhelmingly big **is a size bet**, and crediting the value line of a budget with it
   is crediting value with a size premium under another name. The small-value half alone
   reads `1.287` — more than the whole long-short spread, from one leg of it.
4. **The `0.40` in the edge budget is not obviously wrong, and that is the problem.** It
   sits inside the size-neutral interval post-publication and just below it in the full
   sample. **It is defensible or indefensible depending on a benchmark choice the budget
   never states.**

---

## What was measured

`6_Portfolios_2x3` publishes the six value-weighted size × book-to-market portfolios HML
is assembled from. So the long leg `L = 0.5(SH + BH)` is a portfolio, `L − benchmark` is a
long-only excess, and the capture fraction is `mean(L − benchmark) / mean(HML)` over the
same months. **Nothing here needed data this repository did not already have**; what was
missing was the observation that the long leg of a published spread is itself a published
series.

Five benchmark definitions frozen before the run:

| Definition | Long-only | Benchmark | What it is |
| --- | --- | --- | --- |
| **`value_halves_vs_size_neutral`** | `0.5(SH + BH)` | the equal-weighted six | **The primary.** Same 50/50 size weighting on both sides, so the difference is book-to-market and nothing else |
| `value_halves_vs_market` | `0.5(SH + BH)` | `Mkt-RF + RF` | What a retail investor gets instead of a total-market fund. Contains a large size tilt |
| `big_value_vs_market` | `BH` | `Mkt-RF + RF` | The closest public analogue of a large-cap value fund, and the most implementable |
| `big_value_vs_big_third` | `BH` | the big third | The value tilt inside large caps alone |
| `small_value_vs_market` | `SH` | `Mkt-RF + RF` | The small-value corner. The least implementable |

The benchmark is a **total** return, `Mkt-RF + RF`, never `Mkt-RF`. The six portfolios are
total returns; subtracting a market factor already net of the bill would understate the
benchmark by the whole bill rate and flatter every figure here.

### The grid

Intervals are two-sided 90% from a **joint** stationary block bootstrap — one set of time
indices applied to numerator and denominator at once, because a long leg and the spread it
is half of are not independent estimates. `*` marks a member of the predeclared family.

| Definition | Era | n | Capture | 90% interval | Long-only excess | HML |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| \* **size-neutral** | 1963-07…2025-12 | 750 | **0.520** | `[0.434, 0.722]` | +1.80 | 3.45 |
| \* vs market | 1963-07…2025-12 | 750 | 0.958 | `[0.586, 1.662]` | +3.31 | 3.45 |
| \* big value vs market | 1963-07…2025-12 | 750 | 0.630 | `[0.242, 0.933]` | +2.17 | 3.45 |
| \* big value vs big third | 1963-07…2025-12 | 750 | 0.441 | `[0.183, 0.722]` | +1.52 | 3.45 |
| \* small value vs market | 1963-07…2025-12 | 750 | **1.287** | `[0.603, 2.788]` | +4.44 | 3.45 |
| \* **size-neutral** | 1926-07…2025-12 | 1194 | **0.543** | `[0.480, 0.644]` | +2.27 | 4.18 |
| \* **size-neutral** | 1994-01…2025-12 | 384 | **0.574** | `[−0.295, 1.288]` | +0.90 | 1.57 |
| \* vs market | 1994-01…2025-12 | 384 | 0.882 | `[−1.058, 2.536]` | +1.39 | 1.57 |
| short leg vs size-neutral | 1963-07…2025-12 | 750 | 0.480 | `[0.271, 0.568]` | +1.66 | 3.45 |

**Every cell except the five on 1926-07…2025-12 is marked UNSTABLE** by the frozen rule:
more than 1% of resamples produced a denominator near zero or of the opposite sign. That is
not a caveat about method; it is a fact about HML.

**The full sample and the post-publication era do not disagree about the capture
fraction** — 0.520 against 0.574, the second interval containing the first several times
over. They disagree about the *premium*: HML is +3.45 pp/yr full sample and +1.57
post-publication, exactly reproducing Experiment 001's US figure. Post-publication decay
lives in numerator and denominator alike, so it nearly cancels. **The capture fraction is
stable; what decayed is the thing it is a fraction of.**

### The reconstruction, which is the integration test

| Identity | n | max abs residual | Tolerance | Passed |
| --- | ---: | ---: | ---: | --- |
| `HML = 0.5(SH+BH) − 0.5(SL+BL)` vs the three-factor file | 1194 | 0.005 pp/mo | 0.015 | yes |
| the same vs the five-factor file | 750 | 0.005 | 0.015 | yes |
| `SMB` (three-factor) from the six | 1194 | 0.005 | 0.015 | yes |
| `UMD = 0.5(SHi+BHi) − 0.5(SLo+BLo)` | 1188 | 0.010 | 0.015 | yes |
| the SMB identity vs the **five**-factor file | 750 | **3.517** | 0.015 | **no, and expected** |

The tolerance is **derived, not chosen**: four terms weighted 0.5 whose absolute weights
sum to 2, each carrying at most 0.005 pp of rounding, against an independently rounded
target, is `2 × 0.005 + 0.005 = 0.015`.

**The last row is a finding, not a failure. The three-factor and five-factor SMB are
different series** — the five-factor one averages size legs across three sorts. A reader
who assumed they were the same would draw a false conclusion.

A second identity, checked because it must hold: the long and short leg shares against the
size-neutral benchmark sum to **1.0 to within 2 × 10⁻¹⁶** in every era. The 0.520/0.480
split *is* that identity, not a coincidence.

### Why the size-neutral reading is the defensible one

`L − market` decomposes exactly into `(L − size-neutral) + (size-neutral − market)`. The
first term is book-to-market. The second is the return to equal-weighting six size × value
buckets against a capitalisation-weighted market — a size and weighting effect with **no
book-to-market content at all**. Over 1963-07…2025-12 the size-neutral six returned
13.01%/yr against the market's 11.49%, so that second term is 1.52 pp/yr, and it is the
whole of the difference between a 0.520 capture and a 0.958 one.

**A budget with a size line and a value line must not book that 1.52 pp/yr twice. A budget
with only a value line and booking it there is claiming a value premium it did not
measure.**

---

## The small-value corner

From `25_Portfolios_5x5`, over 1963-07…2025-12, value-weighted. Loadings are HAC on
`Mkt-RF, SMB, HML`; α is the monthly intercept times 12 and its standard error times 12,
never √12.

| Portfolio | Geometric %/yr | Vol | Max drawdown | Under water | α %/yr | β Mkt | SMB | HML |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ME1 × BM5 (the corner) | 16.29 | 21.69 | −66.8% | 85 mo | +2.35 | 0.938 | 1.082 | 0.522 |
| 0.5(ME1×BM5 + ME5×BM5) | 14.43 | 18.86 | −60.1% | 69 mo | +0.21 | 1.029 | 0.500 | 0.684 |
| ME2 × BM5 | 14.64 | 21.58 | −64.9% | 69 mo | −0.06 | 1.071 | 0.885 | 0.654 |
| **total market** | **10.80** | **15.40** | **−50.3%** | **72 mo** | — | — | — | — |

| Corner capture | Capture | 90% interval | Excess | MDE₈₀ |
| --- | ---: | --- | ---: | ---: |
| corner halves vs market | 1.117 | `[0.617, 2.345]` | +3.85 | 3.22 |
| corner halves vs equal-weighted 25 | 0.595 | `[0.222, 1.323]` | +2.05 | 2.20 |
| corner halves **with ME1 dropped** vs market | 0.910 | `[0.477, 1.637]` | +3.14 | 3.15 |

**The same benchmark spread reappears**: 1.117 against the market, 0.595 against the
equal-weighted 25.

**It does not depend on microcaps, and it is not implementable.** Dropping the ME1 size
quintile entirely and using ME2 as the small leg costs **0.71 pp/yr of a 3.85 pp/yr
excess — 18%**. Hou–Xue–Zhang's mechanism, that "anomalies in microcaps are more apparent
than real", is not what drives this one. But measured from the file's own firm-count and
average-market-cap tables:

| Cell | Share of listed firms | Share of market capitalisation |
| --- | ---: | ---: |
| ME1 × BM5, at 2025-12 | 21.24% | **0.236%** |
| whole ME1 quintile, at 2025-12 | 48.28% | **0.679%** |

French's ME1 quintile uses NYSE breakpoints applied to the whole NYSE/AMEX/NASDAQ
universe, so it is *more* extreme than Hou–Xue–Zhang's microcaps: **half the listed
companies in the United States, and under seven tenths of one percent of the money.**
**Stated plainly: the ME1 × BM5 cell is not implementable at retail in size.** The
investable version excludes the quintile and delivers **+3.14 pp/yr** over the market
rather than +3.85, gross.

---

## The regional check, and momentum and size

Over 1994-01…2025-12, 384 months, using the **ex-US** files — `Developed_6_Portfolios`
includes the United States exactly as `Developed_5_Factors` does.

| Region | Definition | Capture | 90% interval | Excess | HML |
| --- | --- | ---: | --- | ---: | ---: |
| developed ex-US | size-neutral | 0.463 | `[0.397, 0.546]` | +2.35 | 5.07 |
| developed ex-US | vs market | 0.481 | `[0.217, 0.712]` | +2.44 | 5.07 |
| emerging | size-neutral | 0.521 | `[0.486, 0.567]` | +3.95 | 7.58 |
| emerging | vs market | 0.492 | `[0.369, 0.626]` | +3.73 | 7.58 |

**The size-neutral capture is 0.46 to 0.52 in every region** — the structural one-half
again. And **outside the United States the market and size-neutral readings nearly
agree**: the enormous US gap between 0.520 and 0.958 is a fact about how top-heavy the US
market is, not about value.

`Emerging_25_Portfolios_ME_BE-ME_CSV.zip` returns HTTP 404, and probing the library index
gives the reason: emerging sorts are published under the prefix `Emerging_Markets_`, and
only 2×3 sixes and 2×2 fours exist. **There is no emerging small-value corner in this
library to test.**

### Momentum and size

**Momentum**, from `6_Portfolios_ME_Prior_12_2`, whose sort is reconstituted *monthly*:

| Definition | Era | n | Capture | 90% interval | Excess | UMD |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| winner halves, size-neutral | 1963-07…2025-12 | 750 | **0.501** | `[0.438, 0.565]` | +3.57 | 7.13 |
| winner halves vs market | 1963-07…2025-12 | 750 | 0.633 | `[0.426, 0.951]` | +4.51 | 7.13 |
| winner halves, size-neutral | 1994-01…2025-12 | 384 | 0.465 | `[0.168, 0.719]` | +1.95 | 4.20 |

The same one half. **Value and momentum are nonetheless not comparable**: an annual June
reconstitution and a monthly prior-return reconstitution differ by an order of magnitude
in turnover.

**Size**, from `Portfolios_Formed_on_ME`. The design map recorded that size "was never
tested as a premium". This is that test.

| Sort | Era | n | Premium | 90% interval | HAC t | MDE₈₀ |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| smallest minus largest quintile | 1963-07…2025-12 | 750 | **+1.91** | `[−1.90, +6.00]` | 0.90 | 4.73 |
| smallest minus largest decile | 1963-07…2025-12 | 750 | +2.06 | `[−2.67, +6.74]` | 0.85 | 5.20 |
| smallest minus largest quintile | 1994-01…2025-12 | 384 | **+0.41** | `[−4.27, +5.49]` | 0.15 | 6.81 |
| smallest minus largest decile | 1994-01…2025-12 | 384 | −0.01 | `[−5.81, +6.13]` | −0.00 | 7.26 |

**The size premium is not signable on this data.** Every interval contains zero, every
point estimate sits below its own detection threshold, and the post-publication estimates
are indistinguishable from nothing. The long-only capture is nominally 0.836 over the full
sample, but it is a ratio of a small number to a smaller one — the post-publication decile
reading of **−9.679** against an interval of `[0.287, 1.389]` shows exactly how little
that means. This is a plain quintile or decile spread and is **not** the Fama–French SMB.

---

## Cost, as a separate column

Never a haircut. One component is measured; two are assumed, and the assumed ones are the
weakest numbers here because turnover cannot be recovered from a return series.

**Measured** — the 50/50 rebalance between the small-value and big-value halves, priced by
`core/costs.py` and charged against the wealth path at the moment of the trade:

| Rebalance | k | One-sided turnover %/yr | Gross geometric | Net | Cost pp/yr |
| --- | ---: | ---: | ---: | ---: | ---: |
| monthly | 1.0 | 6.44 | 13.9709 | 13.8975 | 0.073 |
| monthly | 1.7 | 6.44 | 13.9709 | 13.8461 | 0.125 |
| annual | 1.7 | 1.99 | 14.0164 | 13.9777 | 0.039 |

**It is small, and saying so is the point**: the cost that matters for a long-only tilt is
the fee and the internal reconstitution of the sort, not the investor's own rebalancing. A
never-rebalanced 50/50 returned 14.10%/yr against 13.97% for a monthly rebalance, with the
same −61% drawdown.

**Assumed**, at `cost_bp = k × one-sided turnover %`:

| Sort | Turnover %/yr | Trading cost pp/yr | Retail-implementable |
| --- | ---: | ---: | --- |
| annual book-to-market reconstitution | 20–40 | 0.20 / 0.68 | yes |
| monthly prior-return reconstitution | 300 | 3.00 / 5.10 | yes, at 25%/month |
| monthly prior-return reconstitution | 900 | 9.00 / 15.30 | **no**, against a 50% limit |

Add 0.15%/yr (the shelf median) or 0.25% for a small-value product. Against a size-neutral
long-only excess of **+1.80 pp/yr** full sample and **+0.90** post-publication, a value
tilt's 0.35–0.93 pp/yr of total assumed cost consumes between a fifth and all of it. **A
momentum tilt's does not survive at all.**

---

## What this does to `premium × delivered loading − cost`

The chain gains its missing middle term. With Experiment 005's pooled post-publication HML
of +4.74 pp/yr and, beside it, the US-only figure this experiment measured from the same
pinned file (+1.57, reproducing Experiment 001 exactly):

| Product | Delivered HML loading | Capture used | On the pooled +4.74 | On the US-only +1.57 |
| --- | ---: | ---: | ---: | ---: |
| VTV large value | 0.337 | 0.520 size-neutral | 0.83 pp/yr | **0.28 pp/yr** |
| VBR small value | 0.410 | 0.520 size-neutral | 1.01 | **0.34** |
| VTV large value | 0.337 | 1.287 vs market | 2.06 | 0.68 |
| VBR small value | 0.410 | 1.287 vs market | 2.50 | 0.83 |

Cost is deliberately not subtracted: folding it in would produce a net figure from two
quoted numbers and two assumed turnovers.

Two things follow. **The choice of capture definition moves the gross factor line by a
factor of two and a half** for the same product on the same premium. And on the
size-neutral capture and the US-only premium the line is **0.28 to 0.34 pp/yr gross against
0.35–0.93 pp/yr of assumed cost** — **negative on the defensible reading of both terms**,
and positive only if one takes the pooled premium (whose weight sits where shorting is
hardest and no audited product operates) together with the market-relative capture (which
is largely a size premium).

---

## Hostile tests

- **Block length.** The frozen 12-month mean block, the predeclared 6 and 24, and the
  corrected Politis–White automatic length give size-neutral intervals of `[0.434, 0.722]`,
  `[0.432, 0.715]`, `[0.434, 0.736]` and `[0.432, 0.725]`. Nothing turns on it.
- **The near-zero denominator, shown rather than described.** In the recent decade, where
  US HML is −0.44 pp/yr, the size-neutral capture is **−2.362 with a 90% interval of
  `[−1.569, 2.468]`** — a point estimate outside its own interval, from 4,675 sign-flipped
  denominators in 10,000 resamples. **The specification excluded that era from the
  falsifier in advance for exactly this reason**, so the exclusion is not a response to the
  number.
- **Calibration on correlated noise.** A zero-mean Gaussian pair with the matched
  covariance of the real numerator and denominator (correlation 0.965) gives 0.13 with an
  interval of `[−0.263, 1.255]` and 4,444 sign flips. **The machinery produces wide,
  unstable ratios from nothing** — which is why the full-sample interval is informative and
  the post-publication one barely is.
- **Not run.** No product was tested, no point-in-time universe was reconstructed, and no
  capacity or liquidity model was built, so the implementability verdict rests on
  capitalisation shares alone.

---

## Verified, assumed, open

**Verified.** All four reconstruction identities to their derived tolerance, and the
five-factor SMB's failure to reconstruct. Long and short leg shares summing to 1 to machine
precision. The US HML reconstructed here over 1994-01…2025-12 is +1.5703 pp/yr, matching
Experiment 001's published +1.57. ME1 × BM5 held 21.24% of listed firms and 0.236% of
market capitalisation at 2025-12.

**Assumptions.** Value-weighted returns throughout — equal-weighted tables were excluded in
advance, because an equal-weighted portfolio of the smallest quintile is the least
implementable object in the library and using it would flatter everything here. The market
comparator is `Mkt-RF + RF` from the same file and vintage, and for the regional files `RF`
is the US bill with the regional markets USD unhedged. Internal sort turnover of
20–40%/yr for value and 300–900% for momentum, and expense ratios of 0.15–0.25%/yr: **all
four are assumptions, none is measured.** The pooled premium and the delivered loadings in
the chain table are **quoted** from Experiments 005 and 002, not recomputed here.

**Open.**

- **What benchmark an edge budget's factor line should use.** This page argues the
  size-neutral one and shows the arithmetic; it does not settle it, and the answer depends
  on whether the budget carries a separate size line.
- **What a real fund's capture looks like.** Every figure here is a research portfolio.
  Experiment 002 measured delivered *loadings* but not delivered *capture*, and the two are
  not the same quantity. **Measuring a fund's own needs holdings rather than returns** —
  N-PORT data that is already held and that no experiment has read.
- **Whether the ratio is the right object at all.** A capture fraction is undefined when
  its denominator is, and the post-publication HML nearly is. **The long-only excess in
  pp/yr — +0.90 post-publication, +1.80 full sample — may be the more honest summary, and
  it needs no denominator.**

## What this does not establish

- **Not** that a long-only value tilt is worth holding. This measures one term of four.
- **Not** that 0.520 is a *forecast*. It is an in-sample ratio whose stability is partly
  structural.
- **Not** that the small-value corner's premium is real — its excess over the market
  carries an MDE₈₀ of 3.22–4.47 pp/yr.
- **Not** a point-in-time result. Ken French rebuilds the whole history on every release.

---

## Consequence for this repository

1. **No page may quote a long-only capture fraction without its benchmark.**
2. **The edge decomposition's 0.40 is superseded by a measurement with a stated
   benchmark**: 0.520 `[0.434, 0.722]` size-neutral, 0.958 market-relative, and **the
   difference between them is a size premium the budget does not separately carry.**
3. **Size has now been tested as a premium and is not signable.** The design map's
   `not tested as a premium` is retired.
4. **The small-value corner is a real result about a portfolio nobody can hold at scale.**
5. **A concrete next step exists and this page does not take it**: delivered capture from a
   fund's holdings.

## Reproduce it

```sh
cd research
uv run python -m portfolio_edge.experiments.exp_007_longonly_capture --view-results
```

| | |
| --- | --- |
| Specification | `exp_007_longonly_capture.yaml`, hash `be40d9010a9d…` |
| Run id | `ac65387415e04e84b1e6d50fd01f4846`, `succeeded`, result `rejected` |
| Seed | 20260812 |
| Superseded run | `0d37fe33c09a4d379fd9b8a2507a76de`, `unresolved`, spec `265ebd1232e4…` |
| Bootstrap | joint stationary block on numerator and denominator together, 10,000 resamples, frozen 12-month mean block |

**The superseded run is on the ledger and stays there.** The first specification declared
its reconstruction tolerances by a hand-wave rather than by propagating the rounding, and
clause (0) fired on the momentum identity. The correction re-derives one uniform bound from
the files' printed precision and the number of terms, **and from no observed quantity**.
The output of the first run, including every capture fraction, **had been seen** when the
correction was written; that is recorded in the specification's own correction record, and
the falsifier, its clauses, the 0.40, the 0.30 threshold, the definitions, the eras and the
seed did not change.

Input file hashes and coverage are in [the evidence base](evidence-base.md) §2. Returns are
decimal, converted by an explicit recorded transform; premia are `12 × monthly arithmetic
mean`, volatilities `√12 × monthly standard deviation`. **Observations after 2025-12 were
not read** — six months exist in every file and remain a genuinely post-specification
window.
</content>
