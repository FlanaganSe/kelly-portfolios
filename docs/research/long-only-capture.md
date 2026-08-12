# The long-only capture fraction: what a tilt delivers of a long-short premium

**Question.** Every factor premium this repository has measured is an academic
long-short spread — long the high-scoring portfolio, short the low, zero net
investment, gross of every cost. A retail investor cannot hold one. What fraction
of that spread does a long-only tilt actually deliver? Out of scope: whether any
tilt is worth holding, which needs the whole of
`premium × delivered loading × capture − cost` and not this term alone.

**Decision it informs.** The
[edge decomposition](portfolio-edge-research-framework.md) budgets 21 bp/yr for
its factor line by *assuming* a 0.40 long-only capture, and the framework records
four separate times that no source read there establishes the number. This page
replaces the assumption with a measurement.

**Status: `rejected`, and the rejection is the finding.** What is rejected is not
the capture fraction. It is the premise that there *is* one.

## Conclusion

**There is no benchmark-free long-only capture fraction.** Measured on the same
months, from the same file, with the same long-only portfolio, five defensible
benchmarks give capture fractions spanning **0.846** — more than twice the 0.40
the edge budget assumes, and nearly three times the 0.30 threshold frozen in
advance as the point at which a multiplier stops being a multiplier.

The number to use, and the only one entitled to be called a *value* capture:

> **The size-neutral long-only value capture of HML is `0.520`, two-sided 90%
> interval `[0.434, 0.722]`, over 1963-07…2025-12 (750 months).** Over the
> post-publication era 1994-01…2025-12 it is `0.574 [−0.295, 1.288]`, and over the
> longest available window 1926-07…2025-12 it is `0.543 [0.480, 0.644]`. Every one
> of these is **gross**, and the two shorter ones are marked **UNSTABLE**: the
> denominator is a premium that is not reliably signed, so the ratio has no finite
> variance. All figures `as of 2026-08-12`.

Four results follow, and the last is the one that changes what other pages mean.

1. **The reconstruction is exact.** `HML = 0.5(SH + BH) − 0.5(SL + BL)` reproduces
   the published HML column to a maximum absolute residual of **0.005 percentage
   points per month** over 1194 months — exactly half of the last printed digit,
   which is the best a two-decimal-place file admits. The long legs read here are
   the legs of the factor Experiments 001 and 005 measured, not a lookalike.
2. **Roughly half, and for a structural reason.** Against a size-neutral
   benchmark the capture lands at 0.46–0.54 in the United States, in developed
   ex-US, in emerging markets, and for momentum as well as value. That stability
   is arithmetic, not evidence: the long leg is one half of a symmetric
   three-bucket spread, so subtracting the equal-weighted six recovers close to
   half of it almost whatever the data do.
3. **Against the market it looks far better, and the difference is size, not
   value.** `0.958` full sample. Holding the small and big halves at 50/50 against
   a market that is overwhelmingly big is a size bet, and crediting the value line
   of a budget with it is crediting value with a size premium under another name.
   The small-value half alone reads `1.287` — more than the whole long-short
   spread, from one leg of it.
4. **The `0.40` in the edge budget is not obviously wrong, and that is the
   problem.** It sits inside the size-neutral interval in the post-publication era
   and just below it in the full sample. It is defensible or indefensible
   depending on a benchmark choice the budget never states.

## What was measured, and how

`6_Portfolios_2x3` publishes the six value-weighted size × book-to-market
portfolios HML is assembled from. So the long leg `L = 0.5(SH + BH)` is a
portfolio, `L − benchmark` is a long-only excess, and the capture fraction is
`mean(L − benchmark) / mean(HML)` over the same months. Nothing here needed data
this repository did not already have; what was missing was the observation that
the long leg of a published spread is itself a published series.

Five benchmark definitions were frozen before the run, and clause (1) of the
falsifier reads the spread of their point estimates against 0.30.

| Definition | Long-only | Benchmark | What it is |
| --- | --- | --- | --- |
| **`value_halves_vs_size_neutral`** | `0.5(SH + BH)` | `(SL+SM+SH+BL+BM+BH)/6` | **The primary.** Same 50/50 size weighting on both sides, so the difference is book-to-market and nothing else |
| `value_halves_vs_market` | `0.5(SH + BH)` | `Mkt-RF + RF` | What a retail investor gets instead of a total-market fund. Contains a large size tilt |
| `big_value_vs_market` | `BH` | `Mkt-RF + RF` | The closest public analogue of a large-cap value fund, and the most implementable |
| `big_value_vs_big_third` | `BH` | `(BL+BM+BH)/3` | The value tilt inside large caps alone |
| `small_value_vs_market` | `SH` | `Mkt-RF + RF` | The small-value corner in 2×3 form. The least implementable |

The benchmark is a **total** return, `Mkt-RF + RF`, never `Mkt-RF`. The six
portfolios are total returns; subtracting a market factor already net of the
one-month bill would understate the benchmark by the whole bill rate and flatter
every figure on this page.

## The grid

Gross. Percentage points per year unless the column says otherwise. `*` marks a
member of the predeclared five-definition family. Intervals are two-sided 90%
from a **joint** stationary block bootstrap: one set of time indices drawn with a
12-month mean block and applied to numerator and denominator at once, because a
long leg and the spread it is half of are not independent estimates.

| Definition | Era | n | Capture | 90% interval | Long-only excess | Long-only | Benchmark | HML | MDE₈₀ |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| \* **size-neutral** | 1963-07…2025-12 | 750 | **0.520** | `[0.434, 0.722]` | +1.80 | 14.80 | 13.01 | 3.45 | 1.54 |
| \* vs market | 1963-07…2025-12 | 750 | 0.958 | `[0.586, 1.662]` | +3.31 | 14.80 | 11.49 | 3.45 | 2.73 |
| \* big value vs market | 1963-07…2025-12 | 750 | 0.630 | `[0.242, 0.933]` | +2.17 | 13.67 | 11.49 | 3.45 | 2.76 |
| \* big value vs big third | 1963-07…2025-12 | 750 | 0.441 | `[0.183, 0.722]` | +1.52 | 13.67 | 12.14 | 3.45 | 1.86 |
| \* small value vs market | 1963-07…2025-12 | 750 | 1.287 | `[0.603, 2.788]` | +4.44 | 15.94 | 11.49 | 3.45 | 3.50 |
| half tilt vs market | 1963-07…2025-12 | 750 | 0.479 | `[0.294, 0.848]` | +1.65 | 13.15 | 11.49 | 3.45 | 1.36 |
| short leg vs size-neutral | 1963-07…2025-12 | 750 | 0.480 | `[0.271, 0.568]` | +1.66 | 13.01 | 11.35 | 3.45 | 1.80 |
| \* **size-neutral** | 1926-07…2025-12 | 1194 | **0.543** | `[0.480, 0.644]` | +2.27 | 15.77 | 13.50 | 4.18 | 1.59 |
| \* vs market | 1926-07…2025-12 | 1194 | 1.013 | `[0.752, 1.398]` | +4.23 | 15.77 | 11.54 | 4.18 | 3.03 |
| \* big value vs market | 1926-07…2025-12 | 1194 | 0.721 | `[0.493, 0.919]` | +3.01 | 14.55 | 11.54 | 4.18 | 2.80 |
| \* big value vs big third | 1926-07…2025-12 | 1194 | 0.486 | `[0.318, 0.644]` | +2.03 | 14.55 | 12.52 | 4.18 | 1.86 |
| \* small value vs market | 1926-07…2025-12 | 1194 | 1.305 | `[0.835, 2.004]` | +5.45 | 16.99 | 11.54 | 4.18 | 3.80 |
| \* **size-neutral** | 1963-07…1991-12 | 342 | 0.513 | `[0.447, 0.670]` | +2.34 | 16.29 | 13.95 | 4.56 | 1.93 |
| \* **size-neutral** | 1994-01…2003-12 | 120 | 0.420 | `[0.122, 0.754]` | +2.46 | 16.24 | 13.78 | 5.85 | 4.01 |
| \* **size-neutral** | 1994-01…2025-12 | 384 | **0.574** | `[−0.295, 1.288]` | +0.90 | 12.90 | 11.99 | 1.57 | 2.40 |
| \* vs market | 1994-01…2025-12 | 384 | 0.882 | `[−1.058, 2.536]` | +1.39 | 12.90 | 11.51 | 1.57 | 4.31 |
| \* big value vs market | 1994-01…2025-12 | 384 | 0.581 | `[−1.158, 2.408]` | +0.91 | 12.42 | 11.51 | 1.57 | 4.52 |
| \* big value vs big third | 1994-01…2025-12 | 384 | 0.338 | `[−1.041, 1.847]` | +0.53 | 12.42 | 11.89 | 1.57 | 2.91 |
| \* small value vs market | 1994-01…2025-12 | 384 | 1.184 | `[−2.524, 4.553]` | +1.86 | 13.37 | 11.51 | 1.57 | 5.28 |

Every cell above except the five on 1926-07…2025-12 is marked **UNSTABLE** by the
frozen rule: more than 1% of resamples produced a denominator near zero or of the
opposite sign. That is not a caveat about method, it is a fact about HML.

**The definitional spread is 0.846 in both falsifier eras.** Clause (1) fired.

**The full sample and the post-publication era do not disagree about the capture
fraction.** 0.520 against 0.574, with the second interval containing the first
several times over. They disagree about the *premium*: HML is +3.45 pp/yr over the
full sample and +1.57 post-publication, exactly reproducing Experiment 001's US
figure. Post-publication decay lives in the numerator and the denominator alike,
so it very nearly cancels in the ratio. **The capture fraction is stable; what
decayed is the thing it is a fraction of.**

### The reconstruction, which is the integration test

| Identity | n | max abs residual | rms | Tolerance | Passed |
| --- | ---: | ---: | ---: | ---: | --- |
| `HML = 0.5(SH+BH) − 0.5(SL+BL)` vs the three-factor file | 1194 | 0.00500 pp/month | 0.00289 | 0.01500 | yes |
| the same vs the five-factor file | 750 | 0.00500 | 0.00291 | 0.01500 | yes |
| `SMB = (SL+SM+SH)/3 − (BL+BM+BH)/3` vs the three-factor file | 1194 | 0.00500 | 0.00293 | 0.01500 | yes |
| `UMD = 0.5(SHi+BHi) − 0.5(SLo+BLo)` vs the momentum file | 1188 | 0.01000 | 0.00403 | 0.01500 | yes |
| the SMB identity vs the **five**-factor file | 750 | **3.51700** | 0.59769 | 0.01500 | **no, and expected** |

The tolerance is derived, not chosen: four terms weighted 0.5 whose absolute
weights sum to 2, each carrying at most 0.005 pp of two-decimal-place rounding,
against an independently rounded target, is `2 × 0.005 + 0.005 = 0.015` pp/month.

The last row is a finding, not a failure. **The three-factor and five-factor SMB
are different series.** The five-factor SMB averages the size legs of the
book-to-market, profitability and investment sorts; only the three-factor one is
rebuildable from these six portfolios. A reader who assumed they were the same
would draw a false conclusion from this page.

A second identity, checked because it must hold: the long leg's share and the
short leg's share against the size-neutral benchmark sum to **1.0 to within
2 × 10⁻¹⁶** in every era. The 0.520/0.480 split in the full sample is that
identity, not a coincidence.

## Why the size-neutral reading is the defensible one

`L − market` decomposes exactly into `(L − size-neutral) + (size-neutral − market)`.
The first term is book-to-market. The second is the return to equal-weighting six
size × value buckets against a capitalisation-weighted market — a size and
weighting effect with no book-to-market content at all. Over 1963-07…2025-12 the
size-neutral six returned **13.01%/yr** against the market's **11.49%**, so that
second term is 1.52 pp/yr, and it is the whole of the difference between a 0.520
capture and a 0.958 one.

A budget that has a size line and a value line must not book that 1.52 pp/yr
twice. A budget that has only a value line and books it there is claiming a value
premium it did not measure.

## The small-value corner

From `25_Portfolios_5x5`, over 1963-07…2025-12 (750 months), value-weighted.

| Portfolio | Geometric %/yr | Volatility %/yr | Max drawdown | Time under water | α %/yr | β Mkt | SMB | HML |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ME1 × BM5 (the corner cell) | 16.29 | 21.69 | −66.8% | 85 months | +2.35 | 0.938 | 1.082 | 0.522 |
| 0.5(ME1×BM5 + ME5×BM5) | 14.43 | 18.86 | −60.1% | 69 months | +0.21 | 1.029 | 0.500 | 0.684 |
| ME2 × BM5 | 14.64 | 21.58 | −64.9% | 69 months | −0.06 | 1.071 | 0.885 | 0.654 |
| total market | 10.80 | 15.40 | −50.3% | 72 months | — | — | — | — |

Loadings are HAC (Newey–West) on `Mkt-RF, SMB, HML`; α is the monthly intercept
times 12 and its standard error times 12, never √12.

| Corner capture | Capture | 90% interval | Excess | MDE₈₀ |
| --- | ---: | --- | ---: | ---: |
| corner halves vs market | 1.117 | `[0.617, 2.345]` | +3.85 | 3.22 |
| corner halves vs equal-weighted 25 | 0.595 | `[0.222, 1.323]` | +2.05 | 2.20 |
| ME1 × BM5 cell vs market | 1.748 | `[0.799, 4.309]` | +6.03 | 4.47 |
| corner halves **with ME1 dropped** vs market | 0.910 | `[0.477, 1.637]` | +3.14 | 3.15 |

The same benchmark spread reappears: 1.117 against the market, 0.595 against the
equal-weighted 25.

### Does it depend on the smallest quintile? No. Is it implementable? Also no.

Dropping the ME1 size quintile entirely and using ME2 as the small leg costs
**0.71 pp/yr** of a 3.85 pp/yr excess — 18%. **The small-value result does not
depend on microcaps.** Hou–Xue–Zhang's mechanism, that "anomalies in microcaps
are more apparent than real", is not what is driving this one.

The investability question has the opposite answer, and it is measured here from
the file's own firm-count and average-market-cap tables rather than asserted. A
share of `firms × average cap` is invariant to the scale the file never states,
so only shares are reported; no absolute capitalisation can be.

| Cell | Share of listed firms | Share of market capitalisation |
| --- | ---: | ---: |
| ME1 × BM5, mean over 1963-07…2025-12 | 17.81% | 0.633% |
| ME1 × BM5, at 2025-12 | 21.24% | 0.236% |
| whole ME1 quintile, mean | 54.26% | 2.583% |
| whole ME1 quintile, at 2025-12 | 48.28% | 0.679% |

For comparison,
[Hou, Xue and Zhang (2020)](https://doi.org/10.1093/rfs/hhy131) put microcaps at
3.2% of market capitalisation and 60.7% of the stock count. French's ME1 quintile
uses NYSE breakpoints applied to the whole NYSE/AMEX/NASDAQ universe, so it is
*more* extreme than that: **half the listed companies in the United States, and
under seven tenths of one percent of the money.**

**Stated plainly: the ME1 × BM5 cell is not implementable at retail in size.** A
cell holding a fifth of the listed companies and under a quarter of a percent of
market capitalisation cannot absorb meaningful assets at the prices its own return
series assumes. The result survives dropping the quintile, which is what makes it
interesting — the investable version of the corner is `ME2 × BM5` and the halves
that exclude ME1, and those deliver +3.14 pp/yr over the market rather than +3.85.

## The regional check, ex-US

The **ex-US** files, not the Developed ones: `Developed_6_Portfolios` and
`Developed_25_Portfolios` include the United States exactly as `Developed_5_Factors`
does, so neither can be an ex-US check. Over 1994-01…2025-12, 384 months.

| Region | Definition | Capture | 90% interval | Excess | HML |
| --- | --- | ---: | --- | ---: | ---: |
| developed ex-US | size-neutral | 0.463 | `[0.397, 0.546]` | +2.35 | 5.07 |
| developed ex-US | vs market | 0.481 | `[0.217, 0.712]` | +2.44 | 5.07 |
| developed ex-US | small value vs market | 0.601 | `[0.169, 1.240]` | +3.05 | 5.07 |
| emerging | size-neutral | 0.521 | `[0.486, 0.567]` | +3.95 | 7.58 |
| emerging | vs market | 0.492 | `[0.369, 0.626]` | +3.73 | 7.58 |
| emerging | small value vs market | 0.655 | `[0.456, 0.949]` | +4.97 | 7.58 |

Two things stand out. The size-neutral capture is **0.46 to 0.52 in every region**,
which is the structural one-half again. And outside the United States the market
and size-neutral readings nearly agree — the enormous US gap between 0.520 and
0.958 is a fact about how top-heavy the US market is, not about value.

`Emerging_25_Portfolios_ME_BE-ME_CSV.zip` returns HTTP 404. Probing the library
index gives the reason: emerging sorts are published under the prefix
`Emerging_Markets_`, not the `Emerging_` prefix the emerging *factor* files use,
and only 2×3 sixes and 2×2 fours exist. **There is no emerging small-value corner
in this data library to test.** The correct emerging filename is
`Emerging_Markets_6_Portfolios_ME_BE-ME_CSV.zip`, now registered.

## Momentum, and size

**Momentum**, from `6_Portfolios_ME_Prior_12_2`, whose sort is reconstituted
*monthly*:

| Definition | Era | n | Capture | 90% interval | Excess | UMD |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| winner halves, size-neutral | 1963-07…2025-12 | 750 | 0.501 | `[0.438, 0.565]` | +3.57 | 7.13 |
| winner halves vs market | 1963-07…2025-12 | 750 | 0.633 | `[0.426, 0.951]` | +4.51 | 7.13 |
| winner halves, size-neutral | 1994-01…2025-12 | 384 | 0.465 | `[0.168, 0.719]` | +1.95 | 4.20 |
| winner halves, size-neutral | 1965-01…1989-12 | 300 | 0.517 | `[0.455, 0.580]` | +5.10 | 9.85 |

The same one half. Value and momentum are nonetheless **not comparable**: an
annual June reconstitution and a monthly prior-return reconstitution differ by an
order of magnitude in turnover, and the cost column below shows what that does.

**Size**, from `Portfolios_Formed_on_ME`. The design map records that size "was
never tested as a premium" in this repository. This is that test.

| Sort | Era | n | Long-short premium | 90% interval | HAC t | one-sided p | MDE₈₀ |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| smallest minus largest quintile | 1963-07…2025-12 | 750 | +1.91 | `[−1.90, +6.00]` | 0.90 | 0.184 | 4.73 |
| smallest minus largest decile | 1963-07…2025-12 | 750 | +2.06 | `[−2.67, +6.74]` | 0.85 | 0.199 | 5.20 |
| smallest minus largest quintile | 1994-01…2025-12 | 384 | +0.41 | `[−4.27, +5.49]` | 0.15 | 0.441 | 6.81 |
| smallest minus largest decile | 1994-01…2025-12 | 384 | −0.01 | `[−5.81, +6.13]` | −0.00 | 0.501 | 7.26 |

**The size premium is not signable on this data.** Every interval contains zero,
every point estimate sits below its own window's detection threshold, and the
post-publication estimates are indistinguishable from nothing. The long-only
capture is nominally 0.836 `[0.555, 1.135]` over the full sample, but it is a
ratio of a small number to a smaller one and the post-publication decile reading
of −9.679 against an interval of `[0.287, 1.389]` shows exactly how little that
means. This is a spread from a plain quintile or decile sort and is **not** the
Fama–French SMB, which averages size legs across three sorts.

## Cost, as a separate column

Never a haircut. One component is measured; two are assumed, and the assumed ones
are the weakest numbers on this page because turnover cannot be recovered from a
return series.

**Measured.** The 50/50 rebalance between the small-value and big-value halves,
priced by `core/costs.py` and charged against the wealth path at the moment of
the trade, over 1963-07…2025-12:

| Rebalance | k | Rebalances | One-sided turnover %/yr | Gross geometric %/yr | Net | Cost pp/yr |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| monthly | 1.0 | 749 | 6.44 | 13.9709 | 13.8975 | 0.073 |
| monthly | 1.7 | 749 | 6.44 | 13.9709 | 13.8461 | 0.125 |
| annual | 1.0 | 62 | 1.99 | 14.0164 | 13.9936 | 0.023 |
| annual | 1.7 | 62 | 1.99 | 14.0164 | 13.9777 | 0.039 |

It is small, and saying so is the point: the cost that matters for a long-only
tilt is the fee and the internal reconstitution of the sort, not the investor's
own rebalancing. A never-rebalanced 50/50 returned 14.10%/yr against 13.97% for a
monthly rebalance, with the same −61% drawdown.

**Assumed**, at `cost_bp = k × one-sided turnover %`, k from `core/costs.py`:

| Sort | Turnover %/yr | k | Trading cost pp/yr | Retail-implementable |
| --- | ---: | ---: | ---: | --- |
| annual book-to-market reconstitution | 20 | 1.0 / 1.7 | 0.20 / 0.34 | yes |
| annual book-to-market reconstitution | 40 | 1.0 / 1.7 | 0.40 / 0.68 | yes |
| monthly prior-return reconstitution | 300 | 1.0 / 1.7 | 3.00 / 5.10 | yes, at 25%/month |
| monthly prior-return reconstitution | 900 | 1.0 / 1.7 | 9.00 / 15.30 | **no**, 75%/month against a 50% limit |

Add an expense ratio of 0.15%/yr (Experiment 002's shelf median) or 0.25%/yr for a
small-value product. Against a size-neutral long-only excess of **+1.80 pp/yr**
full sample and **+0.90 pp/yr** post-publication, a value tilt's 0.35–0.93 pp/yr
of total assumed cost consumes between a fifth and all of it. A momentum tilt's
does not survive at all.

## What this does to `premium × delivered loading − cost`

Experiment 002's chain gains its missing middle term:
`premium × delivered loading × capture − cost`. With Experiment 005's pooled
three-region post-publication HML of +4.74 pp/yr and, beside it, the US-only
figure this experiment measured from the same pinned file (**+1.57 pp/yr**, which
reproduces Experiment 001 exactly):

| Product | Delivered HML loading | Capture used | On the pooled +4.74 | On the US-only +1.57 |
| --- | ---: | ---: | ---: | ---: |
| VTV large value | 0.337 | 0.520 size-neutral | 0.83 pp/yr | 0.28 pp/yr |
| VBR small value | 0.410 | 0.520 size-neutral | 1.01 | 0.34 |
| VTV large value | 0.337 | 1.287 vs market | 2.06 | 0.68 |
| VBR small value | 0.410 | 1.287 vs market | 2.50 | 0.83 |

Cost is deliberately not subtracted in that table: folding it in would produce a
net figure from two quoted numbers and two assumed turnovers.

Two things follow. First, **the choice of capture definition moves the gross
factor line by a factor of two and a half** — from 0.83 pp/yr to 2.06 pp/yr for the
same product on the same premium. Second, on the size-neutral capture and the
US-only premium the line is **0.28 to 0.34 pp/yr gross**, against 0.35–0.93 pp/yr
of assumed cost. **The chain is negative on the defensible reading of both terms**,
and positive only if one takes the pooled premium (whose weight sits in the two
regions where shorting is hardest and no audited product operates) together with
the market-relative capture (which is largely a size premium).

## Hostile tests

- **Block length.** The frozen 12-month mean block, the predeclared 6 and 24, and
  the corrected Politis–White automatic length (4.94 months on the full sample,
  2.29 post-publication) give size-neutral intervals of `[0.434, 0.722]`,
  `[0.432, 0.715]`, `[0.434, 0.736]` and `[0.432, 0.725]`. Nothing turns on it.
- **The near-zero denominator, shown rather than described.** In `recent`
  (2016-01…2025-12) Experiment 001 measured US HML at −0.44 pp/yr. The size-neutral
  capture there is **−2.362 with a 90% interval of `[−1.569, 2.468]`** — a point
  estimate outside its own interval, from 4 675 sign-flipped denominators in
  10 000 resamples. The specification excluded this era from the falsifier in
  advance for exactly this reason, so the exclusion is not a response to the
  number.
- **Calibration on correlated noise.** A zero-mean Gaussian pair with the matched
  covariance of the real numerator and denominator (correlation 0.965) put through
  the identical machinery gives a point estimate of 0.13 with an interval of
  `[−0.263, 1.255]` and 4 444 sign flips. The machinery produces wide, unstable
  ratios from nothing — which is why the full-sample interval of `[0.434, 0.722]`
  is informative and the post-publication `[−0.295, 1.288]` barely is.
- **Not run.** No product was tested. No point-in-time universe was reconstructed.
  No capacity or liquidity model was built for the corner, so the
  implementability verdict rests on capitalisation shares alone.

## Verified facts, assumptions, open questions

### Verified

- `HML = 0.5(SH + BH) − 0.5(SL + BL)` reproduces the published column to
  0.005 pp/month over 1194 months; the momentum identity to 0.010 pp/month over
  1188 months; the three-factor SMB identity to 0.005 pp/month.
- The five-factor SMB is **not** rebuildable from these six portfolios: residual
  3.517 pp/month.
- Long and short leg shares against the size-neutral benchmark sum to 1 to
  machine precision.
- The US HML reconstructed here over 1994-01…2025-12 is +1.5703 pp/yr, matching
  Experiment 001's published +1.57.
- ME1 × BM5 held 21.24% of listed firms and 0.236% of market capitalisation at
  2025-12; the whole ME1 quintile, 48.28% and 0.679%.

### Assumptions

- Value-weighted returns throughout. Equal-weighted tables were excluded in
  advance: an equal-weighted portfolio of the smallest quintile is the least
  implementable object in the library and using it would flatter everything here.
- The market comparator is `Mkt-RF + RF` from the same file and vintage. For the
  regional files `RF` is the US one-month bill, as Ken French defines it, and the
  regional markets are USD and unhedged.
- Internal sort turnover of 20–40%/yr for value and 300–900%/yr for momentum, and
  expense ratios of 0.15–0.25%/yr. All four are assumptions; none is measured.
- The pooled +4.74 pp/yr premium and the delivered loadings in the chain table are
  **quoted** from Experiments 005 and 002, not recomputed here.

### Open questions

- **What benchmark should an edge budget's factor line actually use?** This page
  argues the size-neutral one and shows the arithmetic; it does not settle it, and
  the answer depends on whether the budget carries a separate size line.
- **What does a real fund's capture look like?** Every figure here is a research
  portfolio. Experiment 002 measured delivered loadings but not delivered capture,
  and the two are not the same quantity.
- **Is the ratio the right object at all?** A capture fraction is undefined when
  its denominator is undefined, and the post-publication HML nearly is. The
  long-only excess in pp/yr — +0.90 post-publication, +1.80 full sample — may be
  the more honest summary, and it needs no denominator.

## What this does not establish

- **Not** that a long-only value tilt is worth holding. This measures one term of
  a four-term chain.
- **Not** that the size-neutral 0.520 is a *forecast*. It is an in-sample ratio
  whose stability is partly structural.
- **Not** that the small-value corner's premium is real. Its excess over the
  market carries an MDE₈₀ of 3.22–4.47 pp/yr, and Experiment 005 left HML at
  `exploratory` on a pooled figure whose US leg survives no correction.
- **Not** a point-in-time result. Ken French rebuilds the whole history from the
  current vintage on every rebuild, so these numbers can move.

## Consequence for this repository

1. **No page may quote a long-only capture fraction without its benchmark.** The
   design map's value and size rows now carry the size-neutral figure and the
   range beside it.
2. **The edge decomposition's 0.40 assumption is superseded by a measurement with
   a stated benchmark.** On the size-neutral reading the factor line's capture term
   is 0.520 `[0.434, 0.722]`, marginally above 0.40; on the market-relative reading
   it is 0.958, and the difference between them is a size premium the budget does
   not separately carry.
3. **Size has now been tested as a premium and is not signable.** +1.91 pp/yr full
   sample and +0.41 post-publication, both far inside their own detection
   thresholds. The design map's `not tested as a premium` is retired.
4. **The small-value corner is a real result about a portfolio nobody can hold at
   scale.** The investable version excludes the smallest quintile and delivers
   +3.14 pp/yr over the market rather than +3.85, gross.
5. **A concrete next step exists and this page does not take it.** Measuring
   delivered capture for an actual fund needs holdings, not returns, and that is
   Experiment 002's data, not this one's.

## Reproduce it

```sh
cd research
uv run python -m portfolio_edge.experiments.exp_007_longonly_capture --view-results
```

| | |
| --- | --- |
| Specification | `research/experiments/exp_007_longonly_capture.yaml` |
| Specification hash | `be40d9010a9de68db9f14f0ecb5cc26c62534918675f8235e8a19eb4cfc1e759` |
| Run id | `ac65387415e04e84b1e6d50fd01f4846`, `succeeded`, result `rejected` |
| Seed | `20260812` |
| Superseded specification | `265ebd1232e45e765fb428f5a3b35b03cc57f3651ba9874293adeca15adcd5ba` |
| Superseded run | `0d37fe33c09a4d379fd9b8a2507a76de`, `succeeded`, result `unresolved` |
| Bootstrap | joint stationary block (Politis–Romano) on numerator and denominator together, 10 000 resamples, frozen mean block 12 months |
| Correction | Benjamini–Hochberg at α = 0.10 over five definitions × two eras, with Holm–Bonferroni beside it |

**The superseded run is on the ledger and stays there.** The first specification
declared its reconstruction tolerances by a hand-wave rather than by propagating
the rounding, at 0.005 and 0.0075 pp/month, and clause (0) fired on the momentum
identity's 0.010. The correction re-derives one uniform bound of 0.015 pp/month
from the files' printed precision and the number of terms, and from no observed
quantity. **The output of the first run, including every capture fraction, had
been seen when the correction was written**; that is recorded in the
specification's own correction record, and the falsifier, its two clauses, the
0.40, the 0.30 threshold, the definitions, the eras and the seed did not change.

Input files, all from
`https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/`, `202606` CRSP and
Bloomberg vintages, retrieved 2026-08-12:

| File | sha256 | Bytes | Coverage |
| --- | --- | ---: | --- |
| `6_Portfolios_2x3_CSV.zip` | `06108313811fe1fd230600f59da30eae279f043b4b1edeee658c18e3be0cd326` | 149 079 | 1926-07…2026-06 |
| `25_Portfolios_5x5_CSV.zip` | `43cfc360fca14e7d50766e8432fb8b6151c47078512efe74bd0f5d3804789a2a` | 548 060 | 1926-07…2026-06 |
| `6_Portfolios_ME_Prior_12_2_CSV.zip` | `8c3ae277bb2c598d01d94c3b4902e8370e833ff70a89851e30fb8f90d063d67b` | 121 761 | 1927-01…2026-06 |
| `Portfolios_Formed_on_ME_CSV.zip` | `d731dea95b67098490892788225d8b5ac38218a90d8442ac32c35407fc285364` | 200 434 | 1926-07…2026-06 |
| `F-F_Research_Data_Factors_CSV.zip` | `cd6d8e0d175b6f423862a6ad15a3073a6e4264b52b2ac9262396c79f707c6bcb` | 13 052 | 1926-07…2026-06 |
| `F-F_Research_Data_5_Factors_2x3_CSV.zip` | `cbc3724812132654fbbe8daae3c46e0f90e70008434f94a7986fe49f1db6ad3b` | 11 901 | 1963-07…2026-06 |
| `F-F_Momentum_Factor_CSV.zip` | `f405ee2d47a5c75ce05025f789733d0599879361e9836a553504240b89159871` | 5 610 | 1927-01…2026-06 |
| `Developed_ex_US_6_Portfolios_ME_BE-ME_CSV.zip` | `2b79a26326eb699bdd5946ffdd90f5674494b8cd684bd5977459325a91153faa` | 29 292 | 1990-07…2026-06 |
| `Developed_ex_US_5_Factors_CSV.zip` | `54ffd319a49811548eb4bdcaae6eaedfdd2cf13da2d3ae2e23fb5c43185f563d` | 6 746 | 1990-07…2026-06 |
| `Emerging_Markets_6_Portfolios_ME_BE-ME_CSV.zip` | `2b5fa424fd368430bec353a6fef35bd5a989551aac3004b781d814f12bc2aedb` | 28 602 | 1989-07…2026-06 |
| `Emerging_5_Factors_CSV.zip` | `ea71c1f51d1788c2eeea42ead56897175c5ca24ac4abe40a59346128b1ac51b8` | 6 949 | 1989-07…2026-06 |

Observations after 2025-12 were not read. Six months exist in every file, through
2026-06, and remain a genuinely post-specification window. Returns are decimal,
converted from the source's percent by an explicit recorded transform; premia and
excesses are `12 × monthly arithmetic mean`, volatilities `√12 × monthly standard
deviation`. Python 3.12; the committed manifests in `research/data-manifests/`
pin every derived table. The append-only ledger is `research/ledger.jsonl`.
