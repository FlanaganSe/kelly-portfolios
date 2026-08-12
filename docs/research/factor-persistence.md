# Factor persistence and decay: what survives publication in the French series

**Question.** Do HML, UMD, RMW and CMA, as distributed in the Ken French data
library, retain a positive and economically meaningful premium after publication,
and is the result stable enough to justify building and testing an investable
implementation?

**Decision it informs.** Whether any of the four factors earns a place in
[Experiment 002](factor-product-audit.md), the exposure and implementation audit of
investable factor products. Out of scope: whether any factor is investable, what
it costs to hold, whether publication *caused* any change, and any allocation.

## Conclusion

**No factor reaches even `exploratory` status. Three are `unresolved` and one is
`rejected`.** The reason is not that the premia are absent; it is that the
post-publication windows are too short, relative to how volatile these series
are, to tell a modest surviving premium from nothing.

| Factor | Status | Why |
| --- | --- | --- |
| **HML** | `unresolved` | +1.57 pp/yr post-publication, 90% interval `[−2.28, +5.54]`. The window could only detect 5.03 pp/yr at 80% power. |
| **UMD** | `unresolved` | +4.19 pp/yr, `[−0.34, +8.50]`, detection threshold 7.27 pp/yr. |
| **RMW** | `unresolved` | +3.04 pp/yr, `[−0.32, +6.76]`, detection threshold 5.27 pp/yr. Alone among the four it did not decay. |
| **CMA** | `rejected` | −1.39 pp/yr post-publication against +3.91 in-sample. Falsifier clauses (a) and (c) both fired. |

Two results dominate everything else in this page.

**First: every cell that survives multiple-testing correction is a
pre-publication cell.** Of the 20 predeclared factor × era cells, five have a
one-sided HAC *p*-value at or below 0.05 uncorrected. Benjamini–Hochberg at 0.10
leaves four — and all four are the factors' *original paper samples*. Not one
post-publication cell survives, in any factor, under either correction. The
single post-publication cell that looked significant uncorrected (UMD's first
decade, *p* = 0.0253) is exactly what the correction removes.

**Second: 16 of the 20 cells hold a premium smaller than their own window could
have detected at 80% power, and the four exceptions are the same four original
samples.** No post-publication window in this grid is powered to find the premium
it actually contains. That is the finding. A reader who takes "the interval
contains zero" as evidence of absence has misread every one of those 16 cells.

The calibration check makes the point concrete. A **zero-mean Gaussian series**
with HML's length (384 months) and volatility, put through the identical
procedure, produced a premium of **+1.98 pp/yr**, a 90% interval of
`[−1.70, +5.65]`, a maximum drawdown of **−53.2%**, **247 months** under water,
and a worst rolling ten-year return of **−46.8%**. HML's real post-publication
figures are +1.57 pp/yr, `[−2.28, +5.54]`, −57.8%, 228 months and −47.4%. **On
these statistics, HML's post-publication record is not distinguishable from
noise.** That is not a claim that HML is noise; it is a measurement of how little
this window can say.

**No factor may be described as working on this evidence.** These are academic
zero-investment long-short research portfolios, gross of transaction costs,
shorting costs, borrow, fees and taxes, and a retail investor cannot implement
most of them at all. Every number below is an upper bound of unknown tightness.

## The grid

Computed from the pinned vintages over the frozen eras. Premium and MDE in
percentage points per year, gross. `90% interval` is a stationary block bootstrap
at the frozen 12-month mean block, 10 000 resamples. **MDE₈₀** is the smallest
true premium the window could reject a zero mean for at 80% power, one-sided,
given that era's realised volatility and length. **BH** is the
Benjamini–Hochberg-adjusted one-sided HAC *p*-value across the whole 20-cell
family at α = 0.10.

| Factor | Era role | Window | n | Mean %/mo | Premium | Vol | Sharpe | 90% interval | MDE₈₀ | *p* | BH |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HML | original sample | 1963-07…1991-12 | 342 | 0.380 | **+4.56** | 8.79 | 0.518 | `[+1.31, +7.66]` | 4.10 | 0.008 | **0.040** |
| HML | first post-publication | 1994-01…2003-12 | 120 | 0.488 | +5.85 | 12.53 | 0.467 | `[−1.84, +13.98]` | 9.86 | 0.105 | 0.210 |
| HML | full post-publication | 1994-01…2025-12 | 384 | 0.131 | +1.57 | 11.43 | 0.137 | `[−2.28, +5.54]` | 5.03 | 0.258 | 0.402 |
| HML | recent | 2016-01…2025-12 | 120 | −0.036 | −0.44 | 13.32 | −0.033 | `[−8.28, +7.27]` | 10.47 | 0.535 | 0.714 |
| HML | common period | 2014-01…2025-12 | 144 | −0.113 | −1.35 | 12.49 | −0.108 | `[−7.75, +5.18]` | 8.97 | 0.628 | 0.739 |
| UMD | original sample | 1965-01…1989-12 | 300 | 0.821 | **+9.85** | 12.27 | 0.803 | `[+6.40, +13.32]` | 6.10 | <0.0001 | **0.0002** |
| UMD | first post-publication | 1994-01…2003-12 | 120 | 0.877 | +10.53 | 19.70 | 0.534 | `[+2.78, +18.47]` | 15.49 | 0.025 | 0.101 |
| UMD | full post-publication | 1994-01…2025-12 | 384 | 0.350 | +4.19 | 16.55 | 0.253 | `[−0.34, +8.50]` | 7.27 | 0.077 | 0.172 |
| UMD | recent | 2016-01…2025-12 | 120 | 0.031 | +0.37 | 13.30 | 0.028 | `[−4.69, +5.41]` | 10.46 | 0.459 | 0.656 |
| UMD | common period | 2014-01…2025-12 | 144 | 0.175 | +2.10 | 13.19 | 0.159 | `[−2.12, +6.25]` | 9.46 | 0.262 | 0.402 |
| RMW | original sample | 1963-07…2013-12 | 606 | 0.264 | **+3.17** | 7.79 | 0.407 | `[+1.14, +5.23]` | 2.73 | 0.005 | **0.035** |
| RMW | first post-publication | 2014-01…2019-12 | 72 | 0.136 | +1.64 | 5.08 | 0.322 | `[−0.05, +3.36]` | 5.16 | 0.166 | 0.301 |
| RMW | full post-publication | 2014-01…2025-12 | 144 | 0.253 | +3.04 | 7.35 | 0.414 | `[−0.32, +6.76]` | 5.27 | 0.062 | 0.168 |
| RMW | recent | 2016-01…2025-12 | 120 | 0.292 | +3.51 | 7.66 | 0.458 | `[−0.23, +7.56]` | 6.02 | 0.067 | 0.168 |
| RMW | common period | 2014-01…2025-12 | 144 | 0.253 | +3.04 | 7.35 | 0.414 | `[−0.31, +6.61]` | 5.27 | 0.062 | 0.168 |
| CMA | original sample | 1963-07…2013-12 | 606 | 0.326 | **+3.91** | 6.93 | 0.564 | `[+2.06, +5.85]` | 2.42 | 0.0002 | **0.002** |
| CMA | first post-publication | 2014-01…2019-12 | 72 | −0.205 | −2.46 | 5.29 | −0.465 | `[−4.96, +0.13]` | 5.37 | 0.889 | 0.889 |
| CMA | full post-publication | 2014-01…2025-12 | 144 | −0.116 | −1.39 | 7.91 | −0.176 | `[−5.00, +3.02]` | 5.68 | 0.711 | 0.748 |
| CMA | recent | 2016-01…2025-12 | 120 | −0.050 | −0.60 | 8.49 | −0.071 | `[−4.86, +4.35]` | 6.68 | 0.581 | 0.726 |
| CMA | common period | 2014-01…2025-12 | 144 | −0.116 | −1.39 | 7.91 | −0.176 | `[−5.00, +2.93]` | 5.68 | 0.711 | 0.748 |

Bold marks the four cells that survive Benjamini–Hochberg. Bold premia are also
the only four cells whose premium exceeds their own MDE₈₀.

### Risk, which the premium table hides

Geometric contribution is reported for a hypothetical fully collateralised
overlay earning nothing on collateral; a long-short spread financed at an
unstated rate is not a wealth path, so this is a diagnostic, not an achievable
return. Drawdown deepens mechanically with sample length and must not be compared
across unequal windows.

| Factor / era | Geometric %/yr | Max drawdown | Months under water | Worst 1y | Worst 3y | Worst 5y | Worst 10y |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HML original | +4.26 | −28.0% | 33 | −22.3% | −24.1% | −17.7% | +33.3% |
| **HML full post-pub** | **+0.92** | **−57.8%** | **228 of 384** | −35.2% | −45.4% | −43.3% | **−47.4%** |
| UMD original | +9.49 | −20.2% | 35 | −15.6% | −3.0% | +7.2% | +84.9% |
| **UMD full post-pub** | **+2.78** | **−57.8%** | **205 of 384** | **−56.6%** | −51.2% | −46.5% | −41.7% |
| RMW original | +2.90 | −41.8% | 142 | −37.8% | −36.2% | −26.0% | −16.6% |
| RMW full post-pub | +2.81 | −14.8% | 26 of 144 | −12.8% | −4.5% | −3.7% | +32.0% |
| CMA original | +3.73 | −17.5% | 103 | −15.5% | −17.2% | −11.2% | −0.8% |
| CMA full post-pub | −1.69 | −27.2% | 95 of 144 | −15.9% | −26.5% | −17.8% | −14.3% |

HML spent **59% of its entire post-publication history below its prior peak**, and
every one of its worst rolling windows ends in 2020 — the worst decade,
2010-06…2020-05, lost 47.4%. UMD's worst single year post-publication was −56.6%
over 2008-12…2009-11, the momentum crash
([Daniel and Moskowitz 2016](https://doi.org/10.1016/j.jfineco.2015.12.002)).
CMA's worst three-year window, −26.5%, is 2023-01…2025-12 — still open at the
sample end.

### Decay

| Factor | Original sample | Full post-publication | Retained | Recent decade |
| --- | ---: | ---: | ---: | ---: |
| HML | +4.56 | +1.57 | 34% | −0.44 |
| UMD | +9.85 | +4.19 | 43% | +0.37 |
| RMW | +3.17 | +3.04 | **96%** | +3.51 |
| CMA | +3.91 | −1.39 | sign flip | −0.60 |

The pattern is consistent with
[McLean and Pontiff (2016)](https://doi.org/10.1111/jofi.12365), who find returns
lower out of sample and lower again after publication across 97 predictors. It is
equally consistent with the original estimates having been inflated by selection.
**This experiment cannot separate those two mechanisms**, and neither can a
before/after comparison in general — see "What this does not establish".

### Cross-factor correlations, common period only

Computed over 2014-01…2025-12, the only window in which all four factors are
simultaneously post-publication. The frozen specification forbids computing them
anywhere else, because a longer window would mix pre- and post-publication
regimes for at least one factor.

|  | HML | UMD | RMW | CMA |
| --- | ---: | ---: | ---: | ---: |
| **HML** | 1.000 | −0.325 | 0.152 | **0.632** |
| **UMD** | −0.325 | 1.000 | −0.070 | −0.026 |
| **RMW** | 0.152 | −0.070 | 1.000 | 0.219 |
| **CMA** | **0.632** | −0.026 | 0.219 | 1.000 |

**HML and CMA are 0.63 correlated over this window and are not two independent
bets.** Over the same window the market factor `Mkt-RF` — the value-weight market
return *already net of the one-month bill* — returned **+11.85 pp/yr** arithmetic,
roughly four times the best of the four long-short factors, and it is investable at
a few basis points. That comparison is descriptive: the market factor is not a
portfolio this experiment claims to hold, and a long-short spread has no
investable benchmark.

## Era boundaries, and the publication record behind them

Boundaries were frozen from the publication record before any result was
computed, and each was set at **the first January strictly after the journal
issue date**, so that no month of a "post-publication" era can precede the printed
result. Every citation below — journal, volume, issue, page range and issue
month — was checked against publisher-deposited Crossref metadata for the DOI, and
every sample period against the article's own text, **as of 2026-08-11**, the date
the frozen specification records. All eleven verified with no correction.

| Factor | Publication used | Issue | Boundary | Original sample | Predecessor evidence | Alternative date tested |
| --- | --- | --- | --- | --- | --- | --- |
| HML | [Fama and French (1993)](https://doi.org/10.1016/0304-405X%2893%2990023-5), *JFE* 33(1) 3–56 | Feb 1993 | 1994-01 | 1963-07…1991-12 (342 months, the paper's own) | [Basu (1977)](https://doi.org/10.1111/j.1540-6261.1977.tb01979.x); [Rosenberg, Reid and Lanstein (1985)](https://doi.org/10.3905/jpm.1985.409007); [De Bondt and Thaler (1985)](https://doi.org/10.1111/j.1540-6261.1985.tb05004.x); [Fama and French (1992)](https://doi.org/10.1111/j.1540-6261.1992.tb04398.x) | 1986-01, after Rosenberg–Reid–Lanstein |
| UMD | [Jegadeesh and Titman (1993)](https://doi.org/10.1111/j.1540-6261.1993.tb04702.x), *JF* 48(1) 65–91 | Mar 1993 | 1994-01 | 1965-01…1989-12 (their main sample) | [Carhart (1997)](https://doi.org/10.1111/j.1540-6261.1997.tb03808.x) is a successor, not a predecessor: it is when momentum entered the standard model | 1998-01, after Carhart |
| RMW | [Fama and French (2015)](https://doi.org/10.1016/j.jfineco.2014.10.010), *JFE* 116(1) 1–22 | Apr 2015 | 2014-01 | 1963-07…2013-12 (606 months) | [Novy-Marx (2013)](https://doi.org/10.1016/j.jfineco.2013.01.003), *JFE* 108(1), Apr 2013 | 2016-01, after the journal issue |
| CMA | Fama and French (2015), as above | Apr 2015 | 2014-01 | 1963-07…2013-12 | [Titman, Wei and Xie (2004)](https://doi.org/10.1017/S0022109000003173); [Cooper, Gulen and Schill (2008)](https://doi.org/10.1111/j.1540-6261.2008.01370.x) | 2016-01, after the journal issue |

Three boundary choices need defending rather than asserting.

- **1993 is dropped, not assigned.** HML's and UMD's papers appeared in February
  and March 1993, so 1993 was ten to eleven months of "published" year. Assigning
  it to either side would be arbitrary; it belongs to neither era.
- **RMW and CMA's 2014-01 precedes their journal issue.** It is the first month
  outside the authors' own estimation sample and follows the working paper, whose
  title page reads *"First draft: June 2013"*. It is genuinely out-of-sample with
  respect to the discovery but not post-*publication* in the narrow sense, which
  is why 2016-01 is reported as well (it is the `recent` era). For RMW the two
  candidate discovery dates *coincide*: the first January after Novy-Marx (2013)
  is also 2014-01.
- **CMA's discovery date is the most disputed of the four.** Asset growth was
  published by Cooper, Gulen and Schill in 2008, six years before this era starts.
  A 2009-01 boundary is **not** tested, because it would place the
  "post-publication" window inside the authors' own estimation sample and confound
  decay with in-sample fit. CMA's rejection therefore rests on the most generous
  of the available candidate dates, which makes it a stronger rejection, not a
  weaker one.

**The ambiguity changes nothing.** Under the alternative dates: HML from 1986-01
gives +1.89 pp/yr `[−1.48, +5.32]` against +1.57 from 1994-01; UMD from 1998-01
gives +3.65 pp/yr `[−1.52, +8.56]` against +4.19 from 1994-01. Both remain
`unresolved` on either date.

## Hostile tests

### The premium lives in single years

| Cell | Premium | Drop best month | Drop best calendar year |
| --- | ---: | ---: | ---: |
| HML full post-pub | +1.57 | +1.17 (2022-01) | **+0.33** (2000) |
| HML recent | −0.44 | −1.74 | −3.76 (2022) |
| UMD full post-pub | +4.19 | +3.64 | +3.46 (1999) |
| UMD recent | +0.37 | −0.45 | −1.71 (2022) |
| RMW full post-pub | +3.04 | +2.46 | **+1.25** (2021) |
| CMA full post-pub | −1.39 | −2.05 | −3.96 (2022) |

**79% of HML's entire post-publication premium is the year 2000**, and 59% of
RMW's is 2021. UMD is the least concentrated of the four by this measure. A
premium that lives in one calendar year is a description of that year.

### Era boundaries shifted ±24 months

Shifts that would read past the frozen sample end are refused rather than
truncated. The shift that matters:

- **CMA's full post-publication premium goes from −1.39 to +0.40 when the window
  moves back 24 months** (2012-01…2023-12). The sign of the rejection is
  therefore *not* robust to the boundary. Two qualifications keep the rejection
  standing: the shifted window pulls in 2012–2013, which are inside the authors'
  own estimation sample, and +0.40 pp/yr is still far below the 2.0 pp/yr
  materiality threshold, so falsifier clause (b) would fire instead of clause (a).
  This is reported because it is the least robust conclusion on the page.
- HML's full post-publication premium moves +1.57 → +2.66 at −24 months; RMW's
  +3.04 → +2.91; UMD's +4.19 → +4.44. None changes a status.
- RMW's six-year first post-publication era is the most boundary-sensitive of all:
  +1.64 base, +0.09 at −24 months, +4.85 at +24 months. Six years decides nothing.

### Bootstrap block length

The frozen mean block is 12 months. The corrected Politis–White automatic length
(Politis and White 2004, *Econometric Reviews* 23, with the Patton, Politis and
White 2009 correction, *Econometric Reviews* 28(4) 372–375; both implemented and
cross-checked against the authors' reference code in
[`research/src/portfolio_edge/inference/bootstrap.py`](../../research/src/portfolio_edge/inference/bootstrap.py)),
computed from each cell's own series, lands between **1.00 and 4.79 months** for 19 of the 20 cells — far shorter than the frozen 12. Intervals barely
move: the largest shift in any 90% bound is about 2 pp/yr, and no status changes.

Two cells are worth naming because a length choice does move them across zero:

- **RMW first post-publication**: the automatic rule returns 24.00 (clipped at its
  own maximum, on a 72-month series where the rule is unreliable) and gives
  `[+0.32, +2.98]`, excluding zero, where the frozen 12 gives `[−0.05, +3.36]`,
  including it. Six years of data cannot support that distinction.
- **CMA first post-publication**: at a 24-month block the interval is
  `[−4.43, −0.47]`, excluding zero on the *negative* side, where the frozen 12
  gives `[−4.96, +0.13]`.

### Not run

The equal-weighted robustness test **was not performed**. The Ken French library
distributes no equal-weighted variant of the five-factor or momentum factor files.
[Hou, Xue and Zhang (2020)](https://doi.org/10.1093/rfs/hhy131) find the
value-weighted/equal-weighted choice moves anomaly replication rates from 35% to
58.6%, so this is a material untested sensitivity, not an omission of convenience.

## The systematic volatility band inherited from Phase 1

The [Phase 1 ingestion gate](fama-french-reproduction.md) is **UNRESOLVED, not
passed**. Means, *t*-statistics and all ten cross-factor correlations reproduce
Fama and French (2015) Table 4; the **standard deviations of HML and RMW do not**,
by −3.03% and +5.09%, against two independently typeset vintages. That is a
systematic disagreement between data vintages, not sampling error. It does not
shrink with more data and it is in no bootstrap interval, so it is carried here as
a **separate band** and never combined with a sampling interval.

| Cell | Sharpe | Systematic band |
| --- | ---: | --- |
| HML original sample | 0.518 | `[0.503, 0.535]` |
| HML full post-publication | 0.137 | `[0.133, 0.141]` |
| RMW original sample | 0.407 | `[0.387, 0.429]` |
| RMW full post-publication | 0.414 | `[0.394, 0.436]` |
| RMW recent | 0.458 | `[0.436, 0.483]` |

**Where it changes a conclusion: nowhere, and that is a structural fact rather
than luck.** The primary metric, the falsifier and every clause of the rejection
rule are functions of the *mean*, which Phase 1 reproduced for all five factors.
The band moves only the volatility, the Sharpe ratio and the minimum detectable
effect. Checked cell by cell, the statement "the premium exceeds this window's
MDE₈₀" holds at both ends of the band in all ten affected cells, so not one
reading flips.

The band would matter for anything that divides by these volatilities — a
volatility-scaled sleeve, a risk-parity weight, a covariance matrix, a Kelly
fraction. None of those is computed here. **Experiment 002 and anything that sizes
a position must carry it.**

**UMD is different and weaker.** It comes from the momentum file, which was never
gated against a printed table. Its second moment is **unmeasured**, which is a
weaker statement than a band of zero, and no band is quoted for it.

## Cost, as a separate column

Not a haircut, and never subtracted from a premium above. The French series have
no turnover, no holdings and no tradable form, so no net figure for them exists.
This is the size of the gap between the gross numbers and anything an investor
could have earned, for a tradable strategy of comparable turnover, using this
repository's `core/costs.py` turnover rule
(`cost_bp/month ≈ k × one-sided turnover %`, *k* ∈ [1.0, 1.7]) with turnover
assumptions declared before the run.

| Factor | Assumed one-sided monthly turnover | Illustrative cost | Gross post-pub premium | Retail-implementable? |
| --- | --- | ---: | ---: | --- |
| HML, RMW, CMA | 1.2–7.2% (low tier, annual June rebalance) | 0.14–1.47 pp/yr | +1.57 / +3.04 / −1.39 | yes at both ends |
| UMD | 27.5–91.5% (mid-to-high tier, monthly rebalance) | **3.30–18.67 pp/yr** | +4.19 | **no** at the pessimistic end |

**UMD's illustrative cost at the pessimistic end is more than four times its gross
post-publication premium**, and even the optimistic end consumes 79% of it. At
91.5% one-sided monthly turnover it is outside the repository's retail-
implementability limit of 50% entirely. HML fares no better in relative terms: a
1.47 pp/yr cost against a 1.57 pp/yr gross premium.

This is consistent with
[Novy-Marx and Velikov (2016)](https://www.nber.org/papers/w20721), whose measured
haircut is 17% in the low-turnover tier and **144%** in the high-turnover tier,
where four of six strategies had strictly negative net returns. **The ordering of
these factors by gross premium is not their ordering by net premium, and this
experiment cannot establish the latter.**

## Verified facts, assumptions, open questions

### Verified

- The 20-cell grid, the era boundaries, the falsifier and the materiality
  threshold were frozen in the specification before any number was computed, and
  the specification hash is recorded in the ledger.
- Both source files are pinned by the SHA-256 of their raw bytes *and* of the
  derived table. A mismatch aborts rather than reporting numbers.
- The sample policy ends 2025-12. Six further months exist in both files
  (through 2026-06) and were **not read**. They remain a genuinely
  post-specification window.
- `RF` is not subtracted from anything: all five FF5 series and UMD are already
  excess or long-short returns. Subtracting it again would move every factor mean
  by −4.98 pp/yr and flip every long-short sign.
- Every publication date and sample period in the table above was checked against
  Crossref DOI metadata and the articles' own text on 2026-08-11.

### Assumptions

- **Turnover.** The cost figures rest on assumed turnover tiers, declared before
  the run. Turnover cannot be recovered from a return series; these are
  assumptions, not measurements.
- **The frozen 12-month block length.** Chosen a priori, not tuned. The
  data-driven alternative is reported for every cell and disagrees materially
  (1–5 months), without changing a status.
- **Normal-approximation power.** The MDE and the power figures assume normality
  of the sample mean. At n ≥ 72 with monthly returns this is the standard
  approximation; the HAC-based MDE is reported beside it because these series are
  autocorrelated (RMW's original sample has an effective sample size of 446 against
  606 observations; HML's 234 against 342).
- **The Benjamini–Hochberg correction treats the 20 tests as independent.** They
  are not: eras nest, RMW and CMA share every era, and all four factors are spreads
  over overlapping holdings of one universe. **The corrected *p*-values are a lower
  bound on the true correction.** Holm–Bonferroni, valid under arbitrary
  dependence, leaves only three cells (UMD, RMW and CMA original samples; HML's
  falls to 0.138).

### Open questions

- Can the 2013–2014 CRSP vintage be obtained? It is the one observation that would
  settle the HML/RMW second-moment disagreement and remove the band.
- What do the equal-weighted constructions do? Untestable from the distributed
  files; it needs the underlying sorted portfolios.
- Does the pattern hold outside the US? Developed and emerging FF5 manifests exist
  in this repository but start 1990-07 and 1989-07, so they are shorter than the
  post-publication windows already shown to be underpowered. A regional check
  would add breadth, not power.
- **What premium would be worth detecting?** Harvey, Liu and Zhu's structural
  estimate for a genuinely true factor is 0.55%/month gross, or 6.6 pp/yr
  ([Harvey, Liu and Zhu 2016](https://doi.org/10.1093/rfs/hhv059)). Even against
  *that* generous target, HML's full post-publication window has 95% power but its
  recent decade only 47%, and RMW's post-publication window 93%. Against the 2.0
  pp/yr materiality threshold this repository actually uses, **no post-publication
  window in the grid exceeds 26% power**, and most sit between 12% and 24%. **The
  available public data cannot answer the question this experiment asks.**

## What this does not establish

- **Not a publication effect.** A before/after comparison across a publication
  date is descriptive. It confounds publication with changing composition,
  valuation regimes, crowding and chance, and nothing here identifies which.
- **Not the authors' original series.** The distributed files apply the current
  CRSP vintage and the current construction to the whole history, *including the
  pre-publication eras*. The original-sample figures are not what the papers
  printed, and a difference is expected.
- **Not investability.** These are zero-investment long-short research portfolios.
  Whether the exposure can be bought, at what cost, with what tracking difference,
  is Experiment 002.
- **Not "CMA does not work".** `rejected` here means the predeclared falsifier
  fired on this series over this window under this construction. It is not a
  statement about the investment premium on conservative-minus-aggressive
  exposure in general.

## Consequence for this repository

1. **No factor is promoted to Experiment 002 on the strength of a premium.** None
   reached `exploratory`. A product may still be worth auditing because it
   delivers a *desired exposure cheaply and reliably* — which is the stated basis
   for Experiment 002 — but not because this page found a premium.
2. **RMW is the one worth looking at first**, on the narrow grounds that it is the
   only factor that did not decay (96% retained), has the mildest post-publication
   drawdown (−14.8%) and sits in the low-turnover cost tier. That is a
   prioritisation, not a finding, and its window is still underpowered.
3. **UMD should not be pursued as a standalone sleeve.** Its illustrative cost
   exceeds its gross premium at the pessimistic end, its turnover is outside the
   retail limit, and its post-publication path includes a −56.6% year.
4. **HML and CMA must never be counted as two independent bets** in any
   construction: 0.63 correlated over the common period.
5. **The HML/RMW volatility band propagates.** Any downstream calculation that
   divides by one of those volatilities must carry ±3.03% and ±5.09% as a separate
   systematic band, or say that it did not.
6. **The 2026-01 onward window is now the natural confirmatory test** of anything
   this exploration proposes. It has not been read.

## Reproduce it

```sh
cd research
uv run python -m portfolio_edge.experiments.exp_001_factor_decay --view-results
uv run pytest tests/unit/test_experiments_exp_001_factor_decay.py
uv run pytest tests/integration/test_exp_001_factor_decay.py     # offline
```

| Field | Value |
| --- | --- |
| Run | `37b77882963b45d09af9be418784ebda` |
| Specification hash | `f9184dfe26619e85b083fae3a08e283eea83daaea977d058fb707554e68f3d76` |
| Specification | [`research/experiments/exp_001_factor_decay.yaml`](../../research/experiments/exp_001_factor_decay.yaml) |
| Code | [`research/src/portfolio_edge/experiments/exp_001_factor_decay.py`](../../research/src/portfolio_edge/experiments/exp_001_factor_decay.py) |
| FF5 file | `F-F_Research_Data_5_Factors_2x3_CSV.zip`, sha256 `cbc3724812132654fbbe8daae3c46e0f90e70008434f94a7986fe49f1db6ad3b`, retrieved 2026-08-12T06:19:22Z, 756 monthly rows 1963-07…2026-06 |
| Momentum file | `F-F_Momentum_Factor_CSV.zip`, sha256 `f405ee2d47a5c75ce05025f789733d0599879361e9836a553504240b89159871`, retrieved 2026-08-12T06:19:22Z, 1194 monthly rows 1927-01…2026-06 |
| Units | source percent → parsed decimal (`value / 100`) → reported percent |
| Seed | 20260811, declared in the specification |
| Bootstrap | stationary block (Politis–Romano), 10 000 resamples, frozen mean block 12 months |
| Environment | Python 3.12, NumPy 2.x, pandas 2.x |

The run, its git commit, specification hash, dataset-manifest hashes, artifact
hashes and the `results_viewed` event are in
[`research/ledger.jsonl`](../../research/ledger.jsonl). The specification refuses
to run against a file whose SHA-256 is not the pinned one: when Ken French
publishes a new vintage this experiment will **abort rather than report numbers**,
and a new specification must be frozen against it.
