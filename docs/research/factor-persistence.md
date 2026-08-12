# Factor persistence and decay: what survives publication in the French series

**Question.** Do HML, UMD, RMW and CMA, as distributed in the Ken French data
library, retain a positive and economically meaningful premium after publication —
and when the United States window turns out to be too short to answer that, do
independent regions supply the sample size it lacks?

**Decision it informs.** Whether any of the four factors earns a place in
[Experiment 002](factor-product-audit.md), the exposure and implementation audit of
investable factor products, and whether more public factor data is worth reading at
all. Out of scope: whether any factor is investable, what it costs to hold, whether
publication *caused* any change, and any allocation.

**Three experiments answer it.** [Experiment 001](#experiment-001--the-united-states-grid)
measured the four factors across frozen pre- and post-publication eras in the US
and left three `unresolved` on power grounds.
[Experiment 005](#experiment-005--the-regional-replication) added developed-ex-US
and emerging equity over the *same* frozen eras, pooled them under a cross-region
block bootstrap, and **measured** how much effective sample size that actually
bought. It was designed so that both branches of its falsifier are decisive, and
both fired: one factor advanced and two were closed. It stated that momentum could
not be tested because no regional momentum file existed.
[Experiment 006](#experiment-006--regional-momentum) showed that reason was false,
downloaded the three files Ken French does publish, and ran the identical design on
UMD.

## Conclusion

**Value and momentum are `exploratory`. Profitability and investment are `rejected`
and closed on public data.**

| Factor | Status | Decided by | Why |
| --- | --- | --- | --- |
| **HML** | **`exploratory`** | Exp 005, branch (a) | Pooled across three regions, **+4.74 pp/yr** post-publication, cross-region joint 90% interval `[+1.46, +8.10]`, positive in all three regions, and it survives dropping its own best calendar year (+3.96). Its adjusted *p* is 0.014 under Benjamini–Hochberg and **0.036 under Holm–Bonferroni**, which is valid under arbitrary dependence — **no post-publication cell in Experiment 001 survived either correction**. |
| **UMD** | **`exploratory`** | Exp 006, branch (a) | Pooled **+7.33 pp/yr** post-publication, joint 90% `[+3.92, +10.31]`, positive in all three regions, surviving its own best calendar year (+6.65) and Holm at 0.0016. **But its pooled detection threshold is 4.98 pp/yr, the worst in this repository**, its three regions are the least independent measured anywhere here (**1.33 effective regions**, ρ̄ = 0.66), and **they crash together**: all three lost their worst calendar year in the same year, 2009. Its academic construction rebalances monthly. |
| **RMW** | **`rejected`** | Exp 005, branch (b) | Pooled **+2.53 pp/yr**, `[+1.07, +3.96]` — but the window's own minimum detectable effect is **2.62 pp/yr**, so the premium is *below the smallest one this window could resolve*. Adding two regions did not fix that. |
| **CMA** | **`rejected`** | Exp 001, confirmed by Exp 005 branch (b) | −1.39 pp/yr in the US, +0.20 pp/yr pooled, against a pooled detection threshold of 3.41 pp/yr. |

`rejected` under branch (b) has a precise and permanent meaning here, and it is not
"the premium is zero". It means: **every independent region the public data library
distributes was added, the effective sample size that bought was measured, and the
result still cannot resolve a premium at the 2.0 pp/yr materiality threshold this
repository uses.** No amount of currently available public data can sign RMW's or
CMA's premium. That is a bounded, final answer, not a request for more research —
see [decision 0005](../decisions/0005-factor-premia-closed-on-public-data.md).

**Neither advance is a discovery of a premium; each is a measurement that the
premium is larger than the threshold its pooled window can see.** HML's pooled
window could only detect **3.35 pp/yr** at 80% power and UMD's only **4.98**, both
above the 2.0 pp/yr materiality threshold. They cleared it because their pooled
premia are 4.74 and 7.33, not because the windows became powerful. **A premium
between 2.0 and 4.98 pp/yr is invisible to the momentum grid however it is
pooled**, and one between 2.0 and 3.35 is invisible to the value grid.

Both premia are carried by the two non-US regions. For HML the US contributes
**+1.57 pp/yr**, developed-ex-US **+5.07** and emerging **+7.58**. For UMD the US
contributes **+4.19**, developed-ex-US **+8.35** and emerging **+9.44** — and the
US momentum premium in the most recent decade is **+0.37 pp/yr**, against +5.75 and
+10.33 abroad. Both falsifiers only required the *signs* to agree.

**No factor may be described as working on this evidence.** These are academic
zero-investment long-short research portfolios, gross of transaction costs,
shorting costs, borrow, fees and taxes, and a retail investor cannot implement most
of them at all. The pooled figures are a *looser* upper bound than the US ones, not
a tighter one, because emerging-market shorting is harder and dearer than US
shorting and the largest measured premium sits in exactly that region.

## Experiment 001 — the United States grid

Two results dominate this experiment.

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

### The grid

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

These boundaries are shared. **Experiments 005 and 006 copy every era name and both
of its boundaries verbatim from Experiment 001's frozen specification, and a
committed test compares the files directly** so that none can drift without
breaking. The publication record below is the single canonical justification for all
three.

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

## Hostile tests on the United States grid

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

## Experiment 005 — the regional replication

Experiment 001 ended by asking whether the pattern holds outside the US and
answering that a regional check "would add breadth, not power", because the
regional files "start 1990-07 and 1989-07, so they are shorter than the
post-publication windows". **That reason was wrong, and correcting it is what made
this experiment possible.** It is true only of the *original-sample* eras, which
begin 1963-07. HML's post-publication era begins **1994-01** and RMW's and CMA's
**2014-01**; the developed-ex-US file begins **1990-07** and the emerging file
**1989-07**. Both regional files therefore begin before both boundaries, with 42
and 54 months of head room on HML's, so the regional post-publication windows are
*exactly as long as the US ones*. The experiment checks that against the loaded
series rather than restating it, and aborts on a silently truncated window.

Three regions, three factors, the three post-publication era roles: a predeclared
**27-cell family**, plus nine pooled cells corrected as their own separate family
because a pooled cell is a function of the same observations as the three regional
cells beneath it. `Developed_ex_US_5_Factors` is used and `Developed_5_Factors` is
not, because the latter includes the United States at roughly half its weight
([Experiment 003](rebalancing-policy.md) measured 0.460 US + 0.549 developed-ex-US);
pooling it beside a US file would have inflated the very effective sample size this
experiment exists to measure honestly.

**UMD is outside this experiment's frozen universe**, which names HML, RMW and CMA.
The reason recorded at the time — that no regional momentum file existed — was true
of this repository and **false of the data**.
[Experiment 006](#experiment-006--regional-momentum) corrected it. Nothing in
Experiment 005's HML, RMW or CMA results depends on that correction.

### The regional grid

Premium and MDE₈₀ in percentage points per year, gross. **BH** is the
Benjamini–Hochberg-adjusted one-sided HAC *p*-value across the whole 27-cell family
at α = 0.10; nine cells are at or below 0.05 uncorrected and **eight survive BH**.

| Factor | Era role | Region | n | Premium | Vol | Sharpe | MDE₈₀ | *p* | BH |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HML | first post-pub | US | 120 | +5.85 | 12.53 | 0.467 | 9.86 | 0.105 | 0.203 |
| HML | first post-pub | developed ex-US | 120 | +8.79 | 9.88 | 0.890 | 7.77 | 0.029 | **0.098** |
| HML | first post-pub | emerging | 120 | +10.30 | 9.55 | 1.079 | 7.51 | 0.003 | **0.040** |
| HML | full post-pub | US | 384 | +1.57 | 11.43 | 0.137 | 5.03 | 0.258 | 0.366 |
| HML | full post-pub | developed ex-US | 384 | +5.07 | 8.35 | 0.607 | 3.67 | 0.006 | **0.040** |
| HML | full post-pub | emerging | 384 | **+7.58** | 7.70 | 0.985 | 3.38 | 0.00001 | **0.0002** |
| HML | recent | US | 120 | −0.44 | 13.32 | −0.033 | 10.47 | 0.535 | 0.629 |
| HML | recent | developed ex-US | 120 | +5.17 | 9.57 | 0.540 | 7.52 | 0.079 | 0.177 |
| HML | recent | emerging | 120 | +7.71 | 8.03 | 0.960 | 6.31 | 0.007 | **0.040** |
| RMW | first post-pub | US | 72 | +1.64 | 5.08 | 0.322 | 5.16 | 0.166 | 0.298 |
| RMW | first post-pub | developed ex-US | 72 | +4.24 | 3.86 | 1.098 | 3.92 | 0.005 | **0.040** |
| RMW | first post-pub | emerging | 72 | +3.34 | 3.76 | 0.889 | 3.82 | 0.020 | **0.076** |
| RMW | full post-pub | US | 144 | +3.04 | 7.35 | 0.414 | 5.27 | 0.062 | 0.165 |
| RMW | full post-pub | developed ex-US | 144 | +1.68 | 4.29 | 0.392 | 3.08 | 0.099 | 0.203 |
| RMW | full post-pub | emerging | 144 | +2.88 | 4.28 | 0.672 | 3.07 | 0.010 | **0.044** |
| RMW | recent | US | 120 | +3.51 | 7.66 | 0.458 | 6.02 | 0.067 | 0.165 |
| RMW | recent | developed ex-US | 120 | +0.92 | 4.39 | 0.210 | 3.45 | 0.256 | 0.366 |
| RMW | recent | emerging | 120 | +2.33 | 4.34 | 0.536 | 3.41 | 0.044 | 0.132 |
| CMA | first post-pub | US | 72 | −2.46 | 5.29 | −0.465 | 5.37 | 0.889 | 0.889 |
| CMA | first post-pub | developed ex-US | 72 | −1.00 | 3.20 | −0.312 | 3.25 | 0.792 | 0.823 |
| CMA | first post-pub | emerging | 72 | +0.69 | 4.09 | 0.170 | 4.15 | 0.350 | 0.450 |
| CMA | full post-pub | US | 144 | −1.39 | 7.91 | −0.176 | 5.68 | 0.711 | 0.768 |
| CMA | full post-pub | developed ex-US | 144 | +0.53 | 4.92 | 0.108 | 3.53 | 0.381 | 0.467 |
| CMA | full post-pub | emerging | 144 | +1.46 | 5.66 | 0.258 | 4.06 | 0.227 | 0.366 |
| CMA | recent | US | 120 | −0.60 | 8.49 | −0.071 | 6.68 | 0.581 | 0.653 |
| CMA | recent | developed ex-US | 120 | +1.18 | 5.29 | 0.222 | 4.16 | 0.286 | 0.386 |
| CMA | recent | emerging | 120 | +1.60 | 6.12 | 0.262 | 4.81 | 0.245 | 0.366 |

**The nine US rows reproduce Experiment 001's published figures exactly** — premium,
volatility, Sharpe and MDE₈₀ — which they must, since they read the same column of
the same pinned file over the same windows. That agreement is asserted in the
output as a self-check, not assumed.

Three readings deserve naming.

- **Every one of the eight BH survivors is a non-US cell**, and every one is HML or
  RMW. **Not one US post-publication cell survives correction in either experiment.**
- **Under Holm–Bonferroni, which is valid under arbitrary dependence, exactly two
  survive: emerging HML's first decade (0.082) and emerging HML's full
  post-publication window (0.0002).** Nothing in Experiment 001's 20-cell grid
  survived Holm outside the original paper samples, so these are the first
  post-publication cells in this repository to do so.
- **HML's US decay is not a global phenomenon.** Its recent decade is −0.44 in the
  US, +5.17 in developed ex-US and +7.71 in emerging. Whatever happened to US value
  after publication, the same construction applied to two disjoint universes over
  the same months does not show it.

### Pooling, and the effective sample size actually achieved

Pooling is the equal-weighted cross-region composite of the three monthly
long-short series, with weights declared before the run. One vote per region: the
object is to count independent looks, not to build a portfolio, and any weighting
fitted to the data would answer a different question. **The interval is a
cross-region *joint* stationary block bootstrap** — one set of time indices drawn
and applied to all three regions at once, so contemporaneous cross-region
dependence survives the resample.

| Factor | Era role | Months | Pooled premium | Joint 90% interval | MDE₈₀ | MDE₈₀ 90% | MDE₈₀ HAC | Sharpe | ρ̄ | Eff. regions | Eff. N | Naive N |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HML | first post-pub | 120 | +8.31 | `[+1.65, +15.33]` | 6.92 | `[3.96, 9.17]` | 9.35 | 0.868 | 0.514 | 1.49 `[1.33, 2.13]` | 178 | 360 |
| **HML** | **full post-pub** | **384** | **+4.74** | **`[+1.46, +8.10]`** | **3.35** | `[2.65, 3.98]` | 4.51 | 0.623 | 0.519 | **1.49 `[1.39, 1.68]`** | **573** | **1152** |
| HML | recent | 120 | +4.15 | `[−2.36, +10.16]` | 6.89 | `[5.29, 8.20]` | 8.76 | 0.550 | 0.558 | 1.45 `[1.34, 1.66]` | 174 | 360 |
| RMW | first post-pub | 72 | +3.07 | `[+1.75, +4.42]` | 2.98 | `[2.52, 3.35]` | 2.93 | 1.010 | 0.228 | 2.12 `[1.89, 2.46]` | 153 | 216 |
| **RMW** | **full post-pub** | **144** | **+2.53** | **`[+1.07, +3.96]`** | **2.62** | `[2.15, 3.07]` | 2.35 | 0.693 | 0.184 | **2.26 `[2.01, 2.65]`** | **326** | **432** |
| RMW | recent | 120 | +2.25 | `[+0.60, +3.92]` | 2.94 | `[2.32, 3.50]` | 2.60 | 0.591 | 0.163 | 2.31 `[2.01, 2.81]` | 277 | 360 |
| CMA | first post-pub | 72 | −0.92 | `[−2.45, +0.68]` | 3.47 | `[2.71, 4.06]` | 3.35 | −0.224 | 0.490 | 1.57 `[1.42, 1.86]` | 113 | 216 |
| **CMA** | **full post-pub** | **144** | **+0.20** | **`[−2.57, +3.44]`** | **3.41** | `[2.60, 4.12]` | 4.22 | 0.042 | 0.380 | **1.76 `[1.60, 1.97]`** | **253** | **432** |
| CMA | recent | 120 | +0.73 | `[−2.62, +4.42]` | 4.03 | `[3.23, 4.76]` | 5.03 | 0.155 | 0.389 | 1.74 `[1.58, 1.94]` | 209 | 360 |

**Eff. regions** is `mean_i var(r_i) / var(composite)`: the number of independent
regions three correlated ones actually amount to. It is 3 under zero correlation
and 1 under perfect correlation, it is measured from the realised sample rather
than assumed, and it carries its own joint-bootstrap interval because it is a
sample statistic and not a constant. **Eff. N** is that figure times the month
count — the pooled evidence expressed in independent single-region months, directly
comparable to an Experiment 001 observation count. **Naive N** is `3 × months`,
which is what treating the three regions as independent samples would have claimed.
`ρ̄` is the mean pairwise cross-region correlation.

**The decisive numbers, stated plainly.**

- **HML: 384 months × 3 regions = 1152 naive region-months bought 573 effective
  ones, an effective 1.49 regions out of 3, leaving MDE₈₀ = 3.35 pp/yr.** Pooling
  three regions was worth about half of what independence would have promised, and
  roughly one extra region.
- **RMW: 432 naive → 326 effective, 2.26 regions, MDE₈₀ = 2.62 pp/yr `[2.15, 3.07]`.**
  RMW's regions are the least correlated of the three factors (ρ̄ = 0.18), so it got
  the most out of pooling — and it *still* could not resolve its own +2.53 premium.
- **CMA: 432 naive → 253 effective, 1.76 regions, MDE₈₀ = 3.41 pp/yr `[2.60, 4.12]`.**

For RMW and CMA the entire 90% sampling interval of the pooled MDE₈₀ sits above the
2.0 pp/yr materiality threshold, and so does the whole Phase 1 systematic band. The
branch (b) verdict is not a point-estimate artefact.

The nine pooled cells are corrected as their **own** family, separately from the 27
regional ones, because a pooled cell is a function of the same observations as the
three regional cells beneath it and counting it again would count one piece of
evidence twice.

| Pooled cell | one-sided HAC *p* | BH (α = 0.10) | Holm (α = 0.10) |
| --- | ---: | ---: | ---: |
| HML first post-pub | 0.0135 | **0.028** | **0.081** |
| **HML full post-pub** | **0.0045** | **0.014** | **0.036** |
| HML recent | 0.1198 | 0.180 | 0.479 |
| RMW first post-pub | 0.0045 | **0.014** | **0.036** |
| **RMW full post-pub** | **0.0037** | **0.014** | **0.034** |
| RMW recent | 0.0157 | **0.028** | **0.081** |
| CMA first post-pub | 0.7529 | 0.753 | 1.000 |
| CMA full post-pub | 0.4530 | 0.510 | 1.000 |
| CMA recent | 0.3598 | 0.463 | 1.000 |

**Six of the nine pooled cells survive both corrections, including RMW's — which is
precisely why the correction is not the falsifier.** RMW's pooled premium is
statistically distinguishable from zero and still below the smallest premium its own
window can resolve at 80% power. A *p*-value answers "could this be zero?"; the
minimum detectable effect answers "could this window have found something worth
having?". Only the second question decides anything here.

### What fired, clause by clause

The falsifier was frozen with five clauses on branch (a) and one on branch (b),
evaluated on the full post-publication era in a fixed order.

| Clause | HML | RMW | CMA |
| --- | --- | --- | --- |
| (a1) pooled premium positive | ✓ +4.74 | ✓ +2.53 | ✓ +0.20 |
| (a2) at or above 2.0 pp/yr | ✓ | ✓ | ✗ 0.20 |
| (a3) joint one-sided 95% lower bound above zero | ✓ +1.46 | ✓ +1.07 | ✗ −2.57 |
| (a4) sign shared by ≥ 2 of 3 regions | ✓ 3 of 3 | ✓ 3 of 3 | ✓ 2 of 3 |
| (a5) survives dropping its own best calendar year | ✓ +3.96 | ✗ +1.79 | ✗ −1.48 |
| (b) measured pooled MDE₈₀ above 2.0 pp/yr | not reached | **fired, 2.62** | **fired, 3.41** |
| **Verdict** | **`exploratory`** | **`rejected`** | **`rejected`** |

Two points about the order, because it decides the readings.

- **Branch (b) is evaluated only after branch (a) fails.** It means "we found
  nothing material *and* could not have found it". HML never reaches it: its
  premium of 4.74 exceeds its own 3.35 detection threshold, so this window did
  detect *this* premium. **It remains blind to any premium between 2.0 and 3.35
  pp/yr**, which is most of the range this repository would care about.
- **RMW came within one clause of advancing and the arithmetic agrees with the
  verdict.** Its pooled premium (2.53) is below its own MDE₈₀ (2.62): the window
  cannot distinguish it from zero at 80% power, which is the same statement clause
  (a5) makes in a different currency.

### Do the regions share the same episodes?

Experiment 001 found **79% of HML's US post-publication premium in the single year
2000** and 59% of RMW's in 2021. If the three regions ran through the same episodes
they would not be three independent looks, so the experiment tests both the
best-year-by-region question and the two US episodes *by name*, so the test cannot
be fitted after the fact.

| Factor | Best year by region | Same year? | 2000 / 2021 share of that region's premium |
| --- | --- | --- | --- |
| HML | US **2000**, developed ex-US **2000**, emerging **1997** | **no** | 2000: US **79.6%**, dev ex-US 22.5%, emerging **4.3%**; pooled 19.1% |
| RMW | US **2021**, developed ex-US **2020**, emerging **2014** | **no** | 2021: US **62.4%**, dev ex-US 19.1%, emerging 16.2%; pooled 35.3% |
| CMA | US **2022**, developed ex-US **2022**, emerging **2022** | **yes** | — |

**The answer differs by factor, and it matters.**

- **HML's US episode concentration does not replicate.** The year that carries four
  fifths of the US premium carries 4.3% of the emerging one, and emerging's own best
  year is three years earlier. Pooled, no single year carries more than 19.1%, and
  dropping the best one leaves +3.96 pp/yr. **On this test the pooled HML result is
  the least episode-driven of the three, and it is the reason clause (a5) passed.**
- **RMW's does not replicate either, but pooling did not save it**: the pooled
  premium still loses 30% of itself to one year and falls to +1.79.
- **CMA is the one factor whose regions do share an episode** — 2022 in all three —
  and dropping it takes the pooled premium to −1.48. Those three regions are the
  least independent looks in the grid on this measure, which is consistent with
  their 0.38 mean correlation.

### Hostile tests

**Resampling the regions independently — the error this experiment exists to
avoid — is measurably wrong, and in one cell it manufactures a result.** Drawing a
separate bootstrap index per region rather than one shared index narrows HML's
pooled 90% interval by a factor of about 1.5 in every era. For **HML's recent
decade the invalid procedure returns `[+0.06, +8.09]`, excluding zero, where the
valid joint procedure returns `[−2.36, +10.16]`, including it.** A naive pooling
would have reported a significant recent-decade value premium that the correct
procedure cannot support. RMW, whose regions are barely correlated, shows almost no
gap (ratio 0.96–1.17), which is exactly what the mechanism predicts.

**A pool that excludes the United States entirely** is the genuinely independent
look at the US finding, since it shares no security with the US file. HML:
**+6.33 pp/yr `[+3.19, +9.58]`**, MDE₈₀ 3.02 — stronger without the US, not weaker.
RMW: +2.28 `[+1.02, +3.48]`, MDE₈₀ 2.38, still below its own threshold. CMA:
+1.00 `[−1.97, +4.01]`. **The US sign flip that produced CMA's Experiment 001
rejection is not replicated abroad**; outside the US, CMA's post-publication premium
is approximately zero rather than negative. That refines the reason for CMA's
rejection without changing it, since +1.00 is far below materiality and far below
its own 3.15 pp/yr detection threshold.

**Inverse-variance weights instead of equal weights** move HML's pooled premium
from +4.74 to +5.47, RMW's from +2.53 to +2.39 and CMA's from +0.20 to +0.51. No
verdict changes. The inverse-variance weights put 0.20 on the US and 0.37–0.43 on
the two regional legs, because the US series is the most volatile of the three in
every factor — which is itself worth noticing.

**A zero-mean Gaussian panel with HML's length and its measured cross-region
covariance**, put through the identical pooled procedure, produced a premium of
−0.89 pp/yr, a joint 90% interval of `[−2.54, +0.76]`, an MDE₈₀ of 3.10 and an
effective 1.59 regions. The machinery recovers roughly the right effective sample
size from correlated noise and produces no premium from it. HML's real +4.74 sits
well outside what this procedure generates from nothing; Experiment 001's US-only
calibration, where HML's +1.57 was *inside* it, is the contrast that matters.

**Block length.** The frozen 12-month mean block is used throughout, with 6 and 24
months as predeclared neighbours and the corrected Politis–White automatic length
computed from every pooled composite. All four are reported for all nine pooled
cells; no verdict changes across them.

### What Experiment 005 does not establish

- **Not a publication effect.** Adding regions adds sample, not identification.
- **Not investability, and the direction is unfavourable.** The largest measured
  premium, emerging HML at +7.58 pp/yr, sits in the universe where shorting is
  hardest, dearest and often unavailable. The pooled figures are a *looser* gross
  upper bound than the US ones.
- **Not a currency-neutral result.** All three files are USD and unhedged. For a
  within-region long-short spread the exchange rate is multiplicative —
  `spread_usd = (1 + f) × spread_local` exactly, since both legs convert at the same
  rate — so currency moves the second moment first-order and the mean only through
  the covariance `E[f × spread_local]`. **That covariance is not zero a priori and
  is not measured here**, and emerging-market currency moves are large.
- **Not a second-moment agreement.** Neither regional file was ever gated against a
  printed table; see the next section.
- **Not independent of Experiment 001.** The US leg *is* Experiment 001, so a third
  of the pooled evidence is the same data that produced the question.
- **Not a long-only capture fraction.** The chain a shareholder receives is
  `premium × delivered loading − cost`. This experiment moved the first term for
  HML only, and only in a gross long-short form.

## Experiment 006 — regional momentum

Experiment 005 recorded that UMD "could not be tested because no regional momentum
file exists in this repository". **That was true of the repository and false of the
data.** Ken French publishes `Developed_Mom_Factor_CSV.zip`,
`Developed_ex_US_Mom_Factor_CSV.zip` and `Emerging_MOM_Factor_CSV.zip`. All three
are monthly. None had ever been downloaded. The gap was an acquisition nobody had
made, not a limit of the public data, and correcting it is what this experiment is.

The files are small — 2.2 to 2.3 kB zipped — which is what a single-column monthly
series of 428 rows costs, not evidence that they are annual. Each holds a monthly
table and an annual one, in the standard library layout. The developed-ex-US and
emerging files begin **1990-11** and **1990-01**, both later than the corresponding
five-factor files because a 2-12 month prior return cannot be formed until twelve
months of history exist, and both **before UMD's 1994-01 post-publication
boundary** — with 38 and 48 months of head room, checked against the loaded series
at run time rather than asserted.

The design is Experiment 005's, unchanged: the same three regions, the same frozen
era boundaries copied verbatim from Experiment 001, the same equal pooling weights,
the same cross-region **joint** block bootstrap, the same four effective-sample-size
definitions and the same two-branch falsifier — all imported from Experiment 005's
module rather than rewritten. The grid is **1 factor × 3 regions × 3 era roles = 9
cells**, plus 3 pooled cells corrected as their own family.
`Developed_ex_US_Mom_Factor` is used and `Developed_Mom_Factor` is not, for the
reason Experiment 005 gives: the Developed file includes the United States.

### The regional grid

Premium and MDE₈₀ in percentage points per year, gross. **BH** and **Holm** are
adjusted one-sided HAC *p*-values across the whole 9-cell family at α = 0.10.

| Era role | Region | n | Premium | Vol | Sharpe | MDE₈₀ | *p* | BH | Holm |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| first post-pub | US | 120 | +10.53 | 19.70 | 0.534 | 15.49 | 0.025 | **0.036** | 0.101 |
| first post-pub | developed ex-US | 120 | +10.63 | 14.71 | 0.723 | 11.57 | 0.028 | **0.036** | 0.101 |
| first post-pub | emerging | 120 | +9.82 | 11.20 | 0.877 | 8.81 | 0.005 | **0.012** | **0.031** |
| full post-pub | US | 384 | +4.19 | 16.55 | 0.253 | 7.27 | 0.077 | **0.087** | 0.154 |
| full post-pub | developed ex-US | 384 | +8.35 | 11.86 | 0.704 | 5.21 | 0.0004 | **0.001** | **0.003** |
| full post-pub | emerging | 384 | **+9.44** | 9.93 | 0.950 | 4.37 | <0.0001 | **0.0000** | **0.0000** |
| recent | US | 120 | +0.37 | 13.30 | 0.028 | 10.46 | 0.459 | 0.459 | 0.459 |
| recent | developed ex-US | 120 | +5.75 | 8.90 | 0.646 | 7.00 | 0.013 | **0.023** | **0.065** |
| recent | emerging | 120 | +10.33 | 8.73 | 1.183 | 6.86 | 0.0001 | **0.0003** | **0.0005** |

**The three US rows reproduce Experiment 001's published UMD figures exactly** —
+10.53 / +4.19 / +0.37, volatilities 19.70 / 16.55 / 13.30, MDE₈₀ 15.49 / 7.27 /
10.46. They read the same column of the same pinned file over the same windows, and
the agreement is asserted in the output rather than assumed.

Five cells survive Holm–Bonferroni, and **every one of them is non-US**. The US
cells are not new evidence in any case: they are already members of Experiment
001's 20-cell family, where UMD's first post-publication decade was precisely the
cell that looked significant uncorrected and did not survive correction.

**The US recent decade is the row to sit with.** +0.37 pp/yr against +5.75 in
developed ex-US and +10.33 in emerging. Whatever has happened to US momentum since
2016, the same construction on two disjoint universes over the same months does not
show it — the same pattern Experiment 005 found for HML, and in the same direction.

### Pooling, and the effective sample size actually achieved

| Era role | Months | Pooled premium | Joint 90% interval | MDE₈₀ | MDE₈₀ 90% | MDE₈₀ HAC | Sharpe | ρ̄ | Eff. regions | Eff. N | Naive N |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| first post-pub | 120 | +10.33 | `[+5.05, +15.51]` | 10.27 | `[7.03, 12.83]` | 10.40 | 0.791 | 0.576 | 1.43 | 171 | 360 |
| **full post-pub** | **384** | **+7.33** | **`[+3.92, +10.31]`** | **4.98** | `[3.87, 5.98]` | 5.55 | 0.647 | 0.659 | **1.33** | **512** | **1152** |
| recent | 120 | +5.48 | `[+2.14, +8.74]` | 7.11 | `[5.64, 8.50]` | 6.51 | 0.607 | 0.641 | 1.36 | 163 | 360 |

**384 months × 3 regions = 1152 naive region-months bought 512 effective ones — an
effective 1.33 regions out of 3, the lowest figure measured anywhere in this
repository.** HML got 1.49, CMA 1.76, RMW 2.26. Momentum's regions are the most
correlated of the four (ρ̄ = 0.66 against HML's 0.52 and RMW's 0.18), so pooling
bought it the least. The pooled MDE₈₀ of **4.98 pp/yr** is correspondingly the
worst pooled detection threshold in the repository, and its whole 90% sampling
interval `[3.87, 5.98]` sits above the 2.0 pp/yr materiality threshold.

The three pooled cells, corrected as their own family: *p* = 0.0068 / 0.0005 /
0.0182, BH 0.010 / 0.0016 / 0.018, Holm 0.014 / 0.0016 / 0.018. All three survive
both corrections. **That is not what advanced UMD.** A *p*-value answers "could this
be zero?"; the minimum detectable effect answers "could this window have found
something worth having?", and only the second decides anything here.

### What fired, clause by clause

| Clause | UMD |
| --- | --- |
| (a1) pooled premium positive | ✓ +7.33 |
| (a2) at or above 2.0 pp/yr | ✓ |
| (a3) joint one-sided 95% lower bound above zero | ✓ +3.92 |
| (a4) sign shared by ≥ 2 of 3 regions | ✓ 3 of 3 |
| (a5) survives dropping its own best calendar year | ✓ +6.65 (1999) |
| (b) measured pooled MDE₈₀ above 2.0 pp/yr | not reached |
| **Verdict** | **`exploratory`** |

Branch (b) is evaluated only after branch (a) fails, so it was never reached. **It
would have fired**: the measured pooled MDE₈₀ is 4.98 pp/yr, far above the
threshold. UMD advanced for the same reason HML did — its premium is larger than
its window's blind spot, not because the blind spot closed.

### Do the regions crash together? Yes, and it is the finding

Momentum crashes are state-dependent: they occur in market rebounds after bear
markets, when the short leg has become a portfolio of high-beta distressed stocks
([Daniel and Moskowitz 2016](https://doi.org/10.1016/j.jfineco.2015.12.002)). Bear
markets and their rebounds are global events, so the crash test was predeclared in
the frozen specification, with the year **2009** named in advance.

- **All three regions lost their worst calendar year in the same year: 2009.** US
  **−52.9%**, developed ex-US **−36.8%**, emerging **−28.9%**, pooled **−39.9%**.
  Experiment 005 found that only CMA's regions shared an episode; momentum's share
  the largest one there is.
- **Every one of the ten worst pooled months has all three regions negative.** The
  worst, 2009-04, is −34.4% in the US, −22.5% in developed ex-US and −14.4% in
  emerging.
- All three regions are negative in the same month **17.5% of months, against 4.3%
  if they were independent** — a factor of 4.1 on their own measured monthly
  negative rates.
- All three are simultaneously in **their own worst decile 3.65% of months, against
  0.1% under independence** — a factor of 36. This measure conditions on nothing
  and is the cleanest of the four.
- The cross-region correlation on the worst decile of pooled months is **0.50**,
  against a matched-covariance Gaussian null whose mean is **0.06** and whose 95th
  percentile is 0.28. (Selecting on the composite conditions on a *collider* and
  pushes a within-tail sample correlation **down**, not up — which is why the null
  is required, and why this statistic is reported only against it. The own-decile
  rate above is free of that problem.)

**The consequence is precise.** The 1.33 effective regions and 512 effective months
are measured over *all* months. In the tail they are worse. **The pooled MDE₈₀ of
4.98 pp/yr is therefore an upper bound on what this window learned, not a
measurement of it**, and a portfolio holding regional momentum tilts gets no
diversification from the regional split in exactly the episode that would matter.

Dropping 2009 *raises* the pooled premium, from +7.33 to **+9.05**. The crash is a
drawdown, not a premium driver, and clause (a5) — which drops the *best* year — is
the wrong question for momentum. Both are reported.

### Hostile tests

- **Independent resampling narrows the interval by 1.34× to 1.51×.** For the full
  post-publication cell the valid joint interval is `[+3.92, +10.31]` and the
  invalid independent one `[+5.17, +9.40]`. Experiment 005 measured about 1.5× on
  HML; momentum, being the most correlated across regions, sits at the top of that
  range. No cell changes its zero-crossing here, but the error is the same one.
- **A pool that excludes the United States entirely** — the genuinely independent
  look at the US result, since it shares no security with the US file — gives
  **+8.90 pp/yr `[+5.84, +11.62]`**, MDE₈₀ 4.31, *stronger* without the US. In the
  recent decade it is +8.04 against +5.48 including the US.
- **Inverse-variance weights** move the pooled premium from +7.33 to +8.15, putting
  0.18 on the US, 0.34 on developed ex-US and 0.49 on emerging, because the US
  series is by far the most volatile of the three. No verdict changes.
- **A zero-mean Gaussian panel with UMD's length and measured cross-region
  covariance** produced +0.64 pp/yr, `[−2.17, +3.45]`, MDE₈₀ 4.91 and an effective
  1.35 regions. The machinery recovers the right effective sample size from
  correlated noise and produces no premium from it; UMD's +7.33 sits far outside
  what it generates from nothing.
- **Experiment 001's alternative Carhart (1997) publication date**, 1998-01, gives a
  pooled +6.71 pp/yr `[+2.90, +9.96]` over 336 months, MDE₈₀ 5.60, effective 1.31
  regions, with the US at +3.65 against +7.80 and +8.69 abroad. The status does not
  depend on which of the two candidate dates is used.
- **Block length.** The frozen 12-month mean block throughout, with 6 and 24 months
  as predeclared neighbours and the corrected Politis–White automatic length
  computed from every pooled composite. No verdict changes across them.

### What Experiment 006 does not establish

- **Not a publication effect**, for the reasons that apply to all three experiments.
- **Not investability, and momentum is the worst case in this repository.** The
  construction re-forms its portfolios *every month* in every region. See
  [cost](#cost-as-a-function-of-turnover) below.
- **Not a second-moment agreement, and here there is not even a band.** No momentum
  file, in any region, has ever been gated against a printed table. Experiment 005
  could bound the effect of the Phase 1 band on the MDE that branch (b) reads
  because that band was measured; here it cannot be bounded at all. That is an
  unquantified sensitivity on every volatility, Sharpe ratio and MDE on this page's
  momentum rows.
- **Not independent of Experiment 001.** The US leg *is* Experiment 001's UMD rows.
- **Not a long-only capture fraction**, and for momentum the gap between the gross
  long-short series and anything holdable is the largest of the four factors.

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
MDE₈₀" holds at both ends of the band in all ten affected cells of Experiment 001,
so not one reading flips.

**Experiment 005 propagates it into the one place it could have mattered.** The
pooled MDE₈₀ decides branch (b), and the band moves it. The band is carried by
rescaling the US leg's deviations by `1 ± u` and recomputing — a relative error `u`
in a volatility is exactly a scale error of that size on the deviations, and the
mean is left untouched because Phase 1 reproduced it.

| Pooled cell | Sharpe | Sharpe band | MDE₈₀ | MDE₈₀ band | Branch (b) fires across the whole band? |
| --- | ---: | --- | ---: | --- | --- |
| HML full post-publication | 0.623 | `[0.614, 0.631]` | 3.35 | `[3.30, 3.39]` | not reached — branch (a) fired first |
| RMW full post-publication | 0.693 | `[0.674, 0.712]` | 2.62 | `[2.55, 2.70]` | **yes** |
| CMA full post-publication | 0.042 | no band (CMA reproduced) | 3.41 | — | **yes** |

The band is roughly ±1.5% on a pooled MDE, an order of magnitude smaller than the
same band on a US-only one, because two of the three legs are unaffected by it.
**Every branch (b) verdict holds at both ends of the systematic band and across the
whole 90% sampling interval of the MDE.**

**Five series carry no measured band at all, which is weaker than a band of zero.**
The developed-ex-US and emerging five-factor files come from a Bloomberg vintage,
and **all three momentum files — US, developed-ex-US and emerging — were never
gated against any printed table in any region**. Their second moments are
**unmeasured**, and every output says so rather than quoting agreement. The
practical consequence is sharpest for Experiment 006: its branch (b) would have
read a pooled MDE built entirely on ungated volatilities, so unlike Experiment 005
it could not have bounded the effect of that uncertainty at all.

The band would matter for anything that divides by these volatilities — a
volatility-scaled sleeve, a risk-parity weight, a covariance matrix, a Kelly
fraction. None of those is computed here. **Experiment 002 and anything that sizes
a position must carry it.**

## Cost, as a function of turnover

Not a haircut, and never subtracted from a premium above. The French series have
no turnover, no holdings and no tradable form, so no net figure for them exists.
This is the size of the gap between the gross numbers and anything an investor
could have earned, for a tradable strategy of the stated turnover, using this
repository's `core/costs.py` turnover rule
(`cost_bp/month ≈ k × one-sided turnover %`, *k* ∈ [1.0, 1.7]).

**Cost is a function, not a number, and the input is turnover.** Turnover cannot be
recovered from a return series, so every figure below is the arithmetic consequence
of a *stated* turnover, and the only honest way to read the table is to bring your
own.

| One-sided turnover, %/month | %/year | Cost at *k* = 1.0 | Cost at *k* = 1.7 | Inside the 50%/month retail limit? |
| ---: | ---: | ---: | ---: | --- |
| 0.5 | 6 | 0.06 pp/yr | 0.10 pp/yr | yes |
| 1.0 | 12 | 0.12 | 0.20 | yes |
| 2.0 | 24 | 0.24 | 0.41 | yes |
| 5.0 | 60 | 0.60 | 1.02 | yes |
| 10.0 | 120 | 1.20 | 2.04 | yes |
| 20.0 | 240 | 2.40 | 4.08 | yes |
| **27.5** | 330 | **3.30** | 5.61 | yes |
| 50.0 | 600 | 6.00 | 10.20 | at the limit |
| **91.5** | 1098 | 10.98 | **18.67** | **no** |

**Which turnover belongs to what, because getting this wrong is an order-of-
magnitude error and it has been made here before.**

- **The academic long-short factors are the only things on this page.** HML, RMW and
  CMA rebalance annually at the end of June; Experiment 001's declared assumption
  is 1.2–7.2% one-sided per month, giving **0.14–1.47 pp/yr**. UMD's construction
  re-forms its six size × prior-return portfolios **every month, in every region**;
  the declared assumption is 27.5–91.5%, giving **3.30–18.67 pp/yr**. Both are
  assumptions declared before the run, not measurements.
- **Against UMD's own gross figures**: 3.30–18.67 pp/yr against a US post-
  publication +4.19 and a pooled +7.33. The pessimistic end is more than twice the
  pooled gross premium and outside the retail limit entirely; the optimistic end
  consumes 45% of it. HML fares no better in relative terms: 1.47 pp/yr against a
  US gross premium of 1.57.
- **That range belongs to the academic long-short series and to nothing else.** A
  long-only momentum fund rebalancing semi-annually cannot carry the monthly
  turnover of a monthly-rebalanced long-short spread. If such a fund turns over *x*%
  one-sided at each of two rebalances a year, its one-sided monthly-equivalent
  turnover is `2x/12 = x/6`. **That is arithmetic, and *x* is not measured anywhere
  in this repository.** Applying 27.5–91.5%/month to such a fund overstates its cost
  by roughly an order of magnitude, and an earlier analysis here did exactly that.
  Read the schedule at whatever turnover the product actually discloses; do not
  import the academic row.

This is consistent with
[Novy-Marx and Velikov (2016)](https://www.nber.org/papers/w20721), whose measured
haircut is 17% in the low-turnover tier and **144%** in the high-turnover tier,
where four of six strategies had strictly negative net returns. **The ordering of
these factors by gross premium is not their ordering by net premium, and these
experiments cannot establish the latter.**

## Verified facts, assumptions, open questions

### Verified

- Experiment 001's 20-cell grid, Experiment 005's 27-cell grid and Experiment 006's
  9-cell grid, the era boundaries, all three falsifiers and the materiality
  threshold were frozen in their specifications before any number was computed, and
  all three specification hashes are recorded in the ledger. Experiment 005's
  specification was written, validated and hashed at **2026-08-12T09:54Z**, before
  its experiment module existed and 15 minutes before the run at 10:09Z.
  Experiment 006's was written and validated at **2026-08-12T13:16Z**, also before
  its module existed; what had been seen of the momentum files at that point was
  their sha256, byte size, row count, date range, column name and prose preamble,
  obtained by downloading them and writing the committed manifests, and no return,
  mean, volatility or correlation from any of them.
- **Experiments 005's and 006's era boundaries are Experiment 001's, verbatim.** A
  committed test loads the specifications and compares every era name and both
  boundaries, so no file can drift. The same test pins Experiment 006's Carhart
  alternative window to Experiment 001's `umd_post_carhart_alternative` era.
- All seven source files are pinned by the SHA-256 of their raw bytes *and* of the
  derived table; the three momentum files are pinned by row count and first
  observation as well. A mismatch aborts rather than reporting numbers.
- **The regional files begin before every post-publication boundary.** Checked at run
  time against the loaded series, per region and per factor: on HML's 1994-01
  boundary developed-ex-US has 42 months of head room and emerging 54; on UMD's
  1994-01 boundary the momentum files have 38 and 48. A region that started late
  would abort rather than truncate silently.
- **Experiment 005's nine US cells and Experiment 006's three reproduce Experiment
  001's published figures exactly**, on premium, volatility, Sharpe and MDE₈₀. They
  read the same column of the same pinned file over the same windows, and the
  agreement is asserted in the output rather than assumed.
- **The three regional momentum files are monthly, not annual.** 428 rows from
  1990-11 for Developed and Developed ex-US and 438 from 1990-01 for Emerging,
  through 2026-06, each with a second annual table in the same file. Their small
  zipped size is what one column of monthly data costs.
- The sample policy ends 2025-12 in all three experiments. Six further months exist
  in every file (through 2026-06) and were **not read**. They remain a genuinely
  post-specification window.
- `RF` is not subtracted from anything: all five FF5 series and UMD are already
  excess or long-short returns, in every region. Subtracting it again would move
  every factor mean by −4.98 pp/yr and flip every long-short sign.
- Every publication date and sample period in the boundary table above was checked
  against Crossref DOI metadata and the articles' own text on 2026-08-11.

### Assumptions

- **Equal pooling weights.** One vote per region, declared before the run and not
  tuned. Inverse-variance weights are reported as a hostile test and change no
  verdict. No regional market-capitalisation series exists here to weight by.
- **Turnover.** Every cost figure on this page rests on an assumed turnover,
  declared before the run. Turnover cannot be recovered from a return series; these
  are assumptions, not measurements. Experiment 005 does not recompute them because
  the tiers are US assumptions, and Experiment 006 replaces the single UMD figure
  with a schedule in stated turnover for the same reason.
- **The frozen 12-month block length.** Chosen a priori, not tuned, in all three
  experiments. The data-driven alternative is reported for every cell and disagrees
  materially in Experiment 001 (1–5 months), without changing a status.
- **Normal-approximation power.** The MDE and the power figures assume normality of
  the sample mean. At n ≥ 72 with monthly returns this is the standard
  approximation; the HAC-based MDE is reported beside it because these series are
  autocorrelated. Branch (b) reads the **conventional** pooled MDE, which is the more
  generous of the two for RMW, so firing on it is a fortiori. For UMD the HAC reading
  is the *larger* of the two (5.55 against 4.98), so the branch (b) it never reached
  would have fired on either.
- **The effective sample size is a sample statistic, not a constant.** `k` is its
  value under zero *population* correlation, and a finite sample whose regions
  happen to correlate negatively returns more than `k`. That is why every pooled
  cell reports a joint-bootstrap interval on it rather than a bare point estimate.
- **Both Benjamini–Hochberg corrections treat their tests as independent.** They are
  not: eras nest, RMW and CMA share every era, all factors are spreads over
  overlapping holdings, and three regions of one factor share global risk factors.
  **The corrected *p*-values are a lower bound on the true correction.**
  Holm–Bonferroni, valid under arbitrary dependence, leaves three cells in
  Experiment 001 (UMD, RMW and CMA original samples), two in Experiment 005 (both
  emerging HML) and five in Experiment 006 (all five non-US momentum cells).

### Open questions

- Can the 2013–2014 CRSP vintage be obtained? It is the one observation that would
  settle the HML/RMW second-moment disagreement and remove the band. It changes no
  conclusion on either page.
- What do the equal-weighted constructions do? Untestable from the distributed
  files; it needs the underlying sorted portfolios.
- **Does UMD hold outside the US?** **Answered by Experiment 006: yes, and more
  strongly than in the US.** +8.35 pp/yr in developed ex-US and +9.44 in emerging
  against +4.19 in the US over the same 384 months, and +5.75 and +10.33 against
  +0.37 in the most recent decade. What remains open is not the sign but the tail:
  the three regions crash together, so the pooled evidence is thinner in exactly the
  episode a holder would care about.
- **What is the long-only capture fraction of a long-short factor premium?** Still
  unmeasured, and it is now the binding unknown for **both** `exploratory` factors:
  the chain a shareholder receives is `premium × delivered loading − cost`, and this
  page has only moved the first term, in gross long-short form. For momentum the
  second and third terms are the harder ones, and the third needs a **measured**
  turnover for the product in question — never the academic long-short assumption.
- **What premium would be worth detecting?** Harvey, Liu and Zhu's structural
  estimate for a genuinely true factor is 0.55%/month gross, or 6.6 pp/yr
  ([Harvey, Liu and Zhu 2016](https://doi.org/10.1093/rfs/hhv059)). Against the
  2.0 pp/yr materiality threshold this repository actually uses, **no US
  post-publication window in Experiment 001's grid exceeds 26% power**, and pooling
  three regions leaves the best pooled detection threshold at 2.62 pp/yr and
  momentum's at 4.98 — all above 2.0. **On the currently available public data, a
  premium between 0 and about 2.6 pp/yr is invisible no matter how it is pooled, and
  for momentum the blind spot runs to 5.0 pp/yr.**

## What this does not establish

- **Not a publication effect.** A before/after comparison across a publication date
  is descriptive. It confounds publication with changing composition, valuation
  regimes, crowding and chance, and nothing here identifies which. Adding regions
  adds sample, not identification.
- **Not the authors' original series.** The distributed files apply the current
  vintage and the current construction to the whole history, *including the
  pre-publication eras*. The original-sample figures are not what the papers
  printed, and a difference is expected. All four international files are built from
  a Bloomberg vintage rather than CRSP.
- **Not investability, and for HML the direction is unfavourable.** These are
  zero-investment long-short research portfolios. HML's largest measured premium is
  in emerging markets, where shorting is hardest, dearest and often unavailable.
  Whether the exposure can be bought, at what cost, with what tracking difference,
  is [Experiment 002](factor-product-audit.md).
- **Not "RMW does not work" or "CMA does not work".** `rejected` means the
  predeclared falsifier fired on these series over these windows under this
  construction. For RMW and CMA under branch (b) it means something sharper and
  narrower: **the publicly available data cannot resolve the premium at the
  materiality threshold, so it cannot be signed either way.** It is not a claim that
  either premium is zero.
- **Not a claim that HML or UMD works.** `exploratory` is the lowest rung of the
  promotion ladder. It permits an investable implementation to be *tested* and
  permits nothing else.
- **Not a claim that momentum diversifies across regions.** Experiment 006 measured
  the opposite: 1.33 effective regions out of three, and all three sharing their
  worst calendar year.

## Consequence for this repository

1. **HML and UMD are `exploratory`, and both are promoted to nothing.** A product
   may be audited against either under
   [Experiment 002](factor-product-audit.md)'s frozen promotion protocol; that
   protocol is unchanged and every screened product still has to pass it on its own
   terms. MTUM, the entire retail momentum shelf that experiment screened, is
   already `rejected` there on its own evidence, and nothing here revisits that.
2. **RMW and CMA are closed on public data.** No further public-data experiment on
   either premium should be commissioned; the reopening conditions are in
   [decision 0005](../decisions/0005-factor-premia-closed-on-public-data.md).
   The earlier prioritisation of RMW as "the one worth looking at first", on the
   grounds that it retained 96% of its premium, is **superseded**: it retained its
   premium and its premium is still smaller than the smallest one three regions of
   public data can resolve.
3. **UMD's premium is signed and its problem has moved from power to
   implementation.** The blockers are now the ones cost and tail risk create, not
   sample size: the academic construction rebalances monthly and its assumed
   turnover reaches outside the retail limit; the illustrative cost range straddles
   the gross pooled premium; its post-publication path includes a −56.6% US year;
   and the three regions crash together, so splitting a momentum tilt across regions
   buys no protection in the episode that matters. **The next question for momentum
   is a measured long-only capture fraction and a measured turnover, not another
   premium experiment.**
4. **HML and CMA must never be counted as two independent bets** in any
   construction: 0.63 correlated over the common US period.
5. **Regional factor sleeves are not independent bets either.** US, developed-ex-US
   and emerging HML correlate 0.52 on average and amount to an effective **1.49**
   regions; the same three momentum series correlate **0.66** and amount to an
   effective **1.33**. Any construction holding regional value or momentum tilts must
   use those numbers, not three — and for momentum must additionally assume no
   regional diversification at all in a crash.
6. **The HML/RMW volatility band propagates**, and five series carry no measured
   band at all: the two regional five-factor files and **all three momentum files**.
   Any downstream calculation that divides by one of those volatilities must carry
   ±3.03% and ±5.09% as a separate systematic band, and must record that the other
   second moments are *unmeasured*, or say that it did not.
7. **The 2026-01 onward window is the natural confirmatory test** of anything these
   experiments propose. It has not been read, in any region.

## Reproduce it

```sh
cd research
uv run python -m portfolio_edge.experiments.exp_001_factor_decay --view-results
uv run python -m portfolio_edge.experiments.exp_005_regional_replication --view-results
uv run python -m portfolio_edge.experiments.exp_006_regional_momentum --view-results
uv run pytest tests/unit/test_experiments_exp_001_factor_decay.py
uv run pytest tests/unit/test_experiments_exp_005_regional_replication.py
uv run pytest tests/unit/test_experiments_exp_006_regional_momentum.py
uv run pytest tests/integration/test_exp_001_factor_decay.py           # offline
uv run pytest tests/integration/test_exp_005_regional_replication.py   # offline
uv run pytest tests/integration/test_exp_006_regional_momentum.py      # offline
```

| Field | Experiment 001 | Experiment 005 | Experiment 006 |
| --- | --- | --- | --- |
| Run | `37b77882963b45d09af9be418784ebda` | `aae878bfc1e649038966408ac9a29ba2` | `f52fd449df6540e5a0711697c8174140` |
| Specification hash | `f9184dfe26619e85b083fae3a08e283eea83daaea977d058fb707554e68f3d76` | `6fd843b790b799c4565cb7b8354b758ade70944d7c6ca91052c9e78fe562c13c` | `3f13053c38d0e21cee9e1fbbe6ab366fe74d3eb90f82164c102bed4b67dc2e91` |
| Specification | [`exp_001_factor_decay.yaml`](../../research/experiments/exp_001_factor_decay.yaml) | [`exp_005_regional_replication.yaml`](../../research/experiments/exp_005_regional_replication.yaml) | [`exp_006_regional_momentum.yaml`](../../research/experiments/exp_006_regional_momentum.yaml) |
| Code | [`exp_001_factor_decay.py`](../../research/src/portfolio_edge/experiments/exp_001_factor_decay.py) | [`exp_005_regional_replication.py`](../../research/src/portfolio_edge/experiments/exp_005_regional_replication.py) | [`exp_006_regional_momentum.py`](../../research/src/portfolio_edge/experiments/exp_006_regional_momentum.py) |
| Seed | 20260811 | 20260812 | 20260812 |
| Grid | 4 factors × 5 eras = 20 cells | 3 factors × 3 regions × 3 eras = 27 cells, plus 9 pooled | 1 factor × 3 regions × 3 eras = 9 cells, plus 3 pooled |
| Bootstrap | stationary block (Politis–Romano), 10 000 resamples, frozen mean block 12 months | the same, drawn **jointly across regions** for every pooled statistic | Experiment 005's implementation, imported unchanged |

All seven source files, pinned by the SHA-256 of their raw bytes. The three
momentum files are also pinned by row count and first observation.

| File | sha256 | Rows | Coverage |
| --- | --- | ---: | --- |
| `F-F_Research_Data_5_Factors_2x3_CSV.zip` | `cbc3724812132654fbbe8daae3c46e0f90e70008434f94a7986fe49f1db6ad3b` | 756 | 1963-07…2026-06 |
| `F-F_Momentum_Factor_CSV.zip` | `f405ee2d47a5c75ce05025f789733d0599879361e9836a553504240b89159871` | 1194 | 1927-01…2026-06 |
| `Developed_ex_US_5_Factors_CSV.zip` | `54ffd319a49811548eb4bdcaae6eaedfdd2cf13da2d3ae2e23fb5c43185f563d` | 432 | 1990-07…2026-06 |
| `Emerging_5_Factors_CSV.zip` | `ea71c1f51d1788c2eeea42ead56897175c5ca24ac4abe40a59346128b1ac51b8` | 444 | 1989-07…2026-06 |
| `Developed_ex_US_Mom_Factor_CSV.zip` | `ca8297c338b45cc2121b81ac23f0bba9cd8b8cf3c6afb523a413542fd1557bb6` | 428 | 1990-11…2026-06 |
| `Emerging_MOM_Factor_CSV.zip` | `5e684176192fb88e9103e6393e293f73d3aad265873224558f9532ccb0bb0f4e` | 438 | 1990-01…2026-06 |
| `Developed_Mom_Factor_CSV.zip` (registered, **not used**) | `2bee31ed74c88f01bc8c8b33327c2a8506901d1f95a3785b3237f84cfcd25109` | 428 | 1990-11…2026-06 |

`Developed_Mom_Factor` is registered and manifested but excluded from every pool,
because like `Developed_5_Factors` it includes the United States. Registering it
makes the exclusion a recorded choice rather than an absence. The `Mom` column of
the US file and the `WML` column of the two international files are the same 30/70
prior-return spread; both are called UMD throughout, and the source column of each
region is pinned so a silent column change cannot pass unnoticed.

Units are source percent → parsed decimal (`value / 100`) → reported percent
throughout, on Python 3.12 with NumPy 2.x and pandas 2.x.

All three runs, their git commits, specification hashes, dataset-manifest hashes,
artifact hashes and `results_viewed` events are in
[`research/ledger.jsonl`](../../research/ledger.jsonl). Each specification refuses
to run against a file whose SHA-256 is not the pinned one: when Ken French
publishes a new vintage these experiments will **abort rather than report numbers**,
and a new specification must be frozen against it.
