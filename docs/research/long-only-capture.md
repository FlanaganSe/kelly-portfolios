# The long-only capture fraction: what a tilt delivers of a long-short premium

**Question.** Every factor premium measured here is an academic long-short spread — long
the high-scoring portfolio, short the low, zero net investment, gross of every cost. A
retail investor cannot hold one. What fraction does a long-only tilt actually deliver?

**Decision it informs.** The [edge decomposition](expected-edge-decomposition.md) budgets
21 bp/yr for its factor line by *assuming* a 0.40 capture, and the framework recorded four
separate times that no source read there establishes the number. This page replaces the
assumption with a measurement. Out of scope: whether any tilt is worth holding, which
needs the whole of `premium × delivered loading − cost`.

**Status: `rejected`, and the rejection is the finding.** What is rejected is not the
capture fraction. It is the premise that there *is* one — and, since 2026-08-17, the
premise that it may multiply anything.

---

## The correction: a capture fraction is a loading, so it may not multiply one

**This page was read as supplying a multiplier and it does not supply one.** Every chain
of the form `loading × capture × premium` in this repository discounted the same
long-only exposure twice. The error is now settled by computation rather than by
argument, and it is worth about a factor of two.

**The algebra.** Regress the very spread this page measures, `L − B`, on the very factors
this repository uses:

```
L − B  =  a  +  h · HML  +  Σ_{k ≠ HML} b_k · f_k  +  e,     mean(e) = 0 by construction
```

Take means and divide by `mean(HML)`:

```
capture  =  h  +  ( a + Σ_{k ≠ HML} b_k · mean(f_k) ) / mean(HML)                     (C)
```

**A capture fraction is an HML loading plus a residue.** It is not a haircut applied to a
loading; it is a second, noisier measurement of the same exposure, with the spread's alpha
and every other factor's contribution folded into its numerator.

**The measurement, on this page's own primary definition, own file and own 750 months:**

| Quantity | Value |
| --- | ---: |
| capture, the direct ratio `mean(L − B)/mean(HML)` | **0.5204** |
| capture, rebuilt from identity (C) | **0.5204** |
| identity error | 4.4 × 10⁻¹⁶ |
| **HML loading `h` of the same spread**, FF5+UMD, HAC 6 | **0.4891** (*t* = 53.9) |
| residue | +0.0313 |
| of which the spread's own alpha | +0.0489 |
| of which the other five factors | −0.0177 |
| **share of the ratio that is the exposure** | **0.940** |

**94% of the 0.520 is the HML loading.** So multiplying a fund's own HML loading by 0.520
does not convert a gross exposure into a delivered one. It multiplies a delivered exposure
by another delivered exposure and produces a number with no interpretation — in the case
this repository actually shipped, 0.410 × 0.520 = 0.213, which is *below the loading of
any audited value product on the shelf.*

**The loading form also dissolves the benchmark problem this page opened.** The 0.846
spread across five benchmarks is a property of the ratio, not of the exposure. Regress the
same long-only value halves against the **market** instead of against the size-neutral
six and the single ratio `0.959` splits into an **HML loading of +0.699 and an SMB loading
of +0.452**. The "size premium wearing a value label" identified below in prose is that
SMB coefficient, and a regression separates it automatically where a ratio cannot. A
loading is taken against a *factor*; the only benchmark choice that survives is which fund
is sold to buy the tilt, and that enters as one small measured number — VTI's own HML
loading is **+0.0247** over 2020-01…2025-12.

**What the capture fraction is still for.** It remains the honest summary of *the whole
return difference* between a long-only portfolio and a named benchmark, all-in, including
alpha and every other exposure. Quoted that way, with its benchmark, it is a measurement.
Used as a multiplier it is a double count. `studies/value_tilt.py` raises
`CaptureDoubleCountError` rather than accepting one.

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

**The result that precedes all four below: it is a loading, and it may not multiply one.**
Identity (C) above, exact to 4.4 × 10⁻¹⁶ on this page's own numbers. **94% of the 0.520 is
the HML regression coefficient of the same spread**, 0.4891. Every `loading × capture`
chain in this repository was discounting one exposure twice and has been corrected.

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
4. **The `0.40` in the edge budget was not obviously wrong, and that was the problem.** It
   sits inside the size-neutral interval post-publication and just below it in the full
   sample, so it looked defensible or indefensible depending on a benchmark choice the
   budget never stated. **The correction above retires the question rather than answering
   it**: a budget that prices its factor line from a delivered loading needs no capture
   term at any benchmark, and the edge decomposition's open question 1 is closed.

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

**It is not signable as Fama–French SMB either, and not on any panel.** This table is a
plain quintile and decile spread in the United States alone, which was the objection to
reading it as a verdict on size. That objection is now answered: SMB itself, on all three
regional five-factor panels over the same eras Experiment 005 froze, reads **+0.33 pp/yr
pooled `[−1.32, +2.06]` against a 2.47 detection floor**, developed ex-US **+0.49** against
2.83 and emerging −0.05
([factor persistence, §Size](factor-persistence.md#size-on-the-three-panels--a-study-not-an-experiment)).
**The ex-US legs were measured rather than carried over from this table**, because HML is
three times larger abroad and nothing said size would behave the same. It does.

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

**The 20–40% assumption has since been checked against the funds and is four to eight
times too high.** Every US systematic value and small-value product Experiment 013
admitted files an Item 3 portfolio turnover rate in its own summary prospectus, and eight
of the nine report **5% to 9% a year**, `as of 2026-08-17`:

| Fund | Turnover %/yr | Fund | Turnover %/yr |
| --- | ---: | --- | ---: |
| AVSC, DFUV, DFLV | 5 | DFAT, DFSV | 9 |
| AVUV, DFAS | 6 | VBR | 25 |
| AVLV | 7 | RPV | 42 |
| | | **VTI** (the incumbent) | **3** |

At `k = 1.7` that is **0.09–0.15 pp/yr for a systematic fund, and 0.05 pp/yr incremental
over VTI**, against the 0.20–0.68 assumed here. Two qualifications, both real: the SEC
turnover rate is `min(purchases, sales) / average net assets` and **excludes an ETF's
in-kind creations and redemptions**, so it understates rotation while correctly excluding
the part that costs the fund nothing; and the two funds whose sort is an *index*
reconstitution rather than a manager's, VBR and RPV, are the two that look like the
assumption. **The assumption was right about index reconstitution and wrong about the
funds an investor would actually buy.**

---

## What this does to `premium × delivered loading − cost`

**The chain has no missing middle term, and this page's earlier answer that it did is
withdrawn.** The version published here on 2026-08-12 read

> | Product | Delivered HML loading | Capture used | On the pooled +4.74 | On the US-only +1.57 |
> | VBR small value | 0.410 | 0.520 size-neutral | 1.01 pp/yr | 0.34 pp/yr |

and concluded that the choice of capture definition moved the gross factor line by a
factor of two and a half. Identity (C) says that table multiplied a delivered exposure by
a delivered exposure. **The correct chain has three terms and not four**, and it is
`weight × (h_fund − h_incumbent) × premium − cost`.

Restated with the incumbent named — VTI, HML loading **+0.0247** over 2020-01…2025-12 —
and against Experiment 005's pooled post-publication +4.74 and the US-only +1.57:

| Product | HML loading | Delivered over VTI | On the pooled +4.74 | On the US-only +1.57 |
| --- | ---: | ---: | ---: | ---: |
| **AVUV** small-cap value | +0.537 | 0.512 | **2.43 pp/yr** | **0.80 pp/yr** |
| VBR small value | +0.410 | 0.386 | 1.83 | 0.61 |
| VTV large value | +0.337 | 0.312 | 1.48 | 0.49 |
| *the same on the superseded chain* | | | *1.01 (VBR)* | *0.34 (VBR)* |

Cost is deliberately not subtracted here: the net figures, at three weights and with
growth and the certainty equivalent beside them, belong in
[the recommendation](portfolio-recommendation.md#5-what-each-tilt-costs-in-confidence-terms)
where the weight is set.

Two things follow, and neither is the pair this page originally drew. **The gross factor
line roughly doubles**, because the discount was applied twice. And it remains **small
relative to what decides it**: the same product's line is 2.43 pp/yr on the pooled premium
and 0.80 on the US-only one, a factor of three, and the US-only premium's own 90% interval
is `[−2.28, +5.54]`. **The premium, not the capture, is now the whole of the uncertainty**
— which is the honest place for it to sit.

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

**Verified.** Identity (C) to 4.4 × 10⁻¹⁶, on this page's own primary definition and
months, with VTI's own alpha over 2020-01…2025-12 reproducing Experiment 013's published
pedestal of −0.5470 pp/yr exactly — which is what licenses reading a comparator loading
computed here beside that experiment's fund loadings. All four reconstruction identities
to their derived tolerance, and the five-factor SMB's failure to reconstruct. Long and
short leg shares summing to 1 to machine precision. The US HML reconstructed here over 1994-01…2025-12 is +1.5703 pp/yr, matching
Experiment 001's published +1.57. ME1 × BM5 held 21.24% of listed firms and 0.236% of
market capitalisation at 2025-12.

**Assumptions.** Value-weighted returns throughout — equal-weighted tables were excluded in
advance, because an equal-weighted portfolio of the smallest quintile is the least
implementable object in the library and using it would flatter everything here. The market
comparator is `Mkt-RF + RF` from the same file and vintage, and for the regional files `RF`
is the US bill with the regional markets USD unhedged. Internal sort turnover of
20–40%/yr for value and 300–900% for momentum, and expense ratios of 0.15–0.25%/yr: **all
four are assumptions, none is measured** — and the first has since been contradicted by
the funds' own filings, above. The pooled premium and the fund loadings in the chain table
are **quoted** from Experiments 005 and 013, not recomputed here; only VTI's loading and
identity (C) are computed on this page.

**Closed since 2026-08-12.** Two of the three open questions this page carried are
answered by identity (C) rather than by a new measurement.

- **An edge budget's factor line needs no benchmark.** A delivered loading is taken
  against a factor, so a budget that prices its factor line
  from one needs no capture term and makes no benchmark choice. The only benchmark left is
  the fund being sold, and it enters as `h_incumbent`.
- **The ratio is not the right object for a budget.** The loading is, and it is estimated
  on the same months from the same series with a standard error the
  ratio cannot offer. The long-only excess in pp/yr remains the better *descriptive*
  summary, and it still needs no denominator.

**Open.**

- **What a real fund's capture looks like.** Every capture figure here is a research
  portfolio. This matters less than it did — the loading is what a budget needs and
  Experiments 002 and 013 measure it directly — but a *holdings*-based delivered exposure
  would still be the first thing here that did not come from a return regression. N-PORT
  data is already held and no experiment has read it.
- **Whether a loading estimated on 36 to 72 months forecasts anything.** Identity (C)
  settles what the loading *is*; it says nothing about stability. Every fund loading in the
  chain table above comes from a window shorter than one value cycle.

## What this does not establish

- **Not** that a long-only value tilt is worth holding. This measures one term of three.
- **Not** that 0.520 is a *forecast*. It is an in-sample ratio whose stability is partly
  structural.
- **Not** that the small-value corner's premium is real — its excess over the market
  carries an MDE₈₀ of 3.22–4.47 pp/yr.
- **Not** a point-in-time result. Ken French rebuilds the whole history on every release.

---

## Consequence for this repository

1. **A capture fraction may never multiply a regression loading.** They are the same
   quantity measured two ways — identity (C) — and their product discounts one exposure
   twice. `studies/value_tilt.sleeve_edge` raises rather than accepting a capture
   argument, so this is enforced in code and not only in prose.
2. **No page may quote a long-only capture fraction without its benchmark**, in the one
   use that survives: as a description of a whole return difference against a named
   portfolio.
3. **The edge decomposition's 0.40 is not replaced by 0.520; it is deleted.** A factor
   line is `weight × (h_fund − h_incumbent) × premium − cost`, and every term in it is
   measured.
4. **Size has now been tested as a premium and is not signable.** The design map's
   `not tested as a premium` is retired. This now bears directly on product choice: a
   small-value fund carries an SMB loading near +0.85 whose premium this repository cannot
   sign, so that exposure is variance without a priced expectation.
5. **The small-value corner is a real result about a portfolio nobody can hold at scale.**
6. **The turnover assumption is superseded by filings** for every fund on the US
   systematic shelf, and it was too high by a factor of four to eight.

## Reproduce it

```sh
cd research
uv run python -m portfolio_edge.experiments.exp_007_longonly_capture --view-results
uv run python -m portfolio_edge.studies.value_tilt   # identity (C), the funds, the corners
```

The second command is **not** part of Experiment 007 and is not ledgered as one. It is a
study, `exploratory` throughout, and it froze no specification before its numbers were
seen. It reads Experiment 013's committed exposures rather than re-estimating them, and
computes only VTI's own loadings, identity (C), and the arithmetic over both.

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
