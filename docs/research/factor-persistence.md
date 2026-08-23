# Factor persistence and decay: what survives publication in the French series

**Question.** Do HML, UMD, RMW and CMA retain a positive, economically meaningful premium
after publication — and when the United States window turns out to be too short to
answer that, do independent regions supply the sample size it lacks? And, added later
because a product decision turned on it: **can SMB be signed on any of the same panels?**

**Decision it informs.** Whether any of the four factors earns a place in the
[product audit](factor-products.md), and whether more public factor data is worth reading
at all. Out of scope: investability, cost, whether publication *caused* any change, and
any allocation.

**Three experiments and one study.** [Experiment 001](#experiment-001--the-united-states-grid)
measured four factors across frozen pre- and post-publication eras in the US and left three
`unresolved` on power grounds.
[Experiment 005](#experiment-005--the-regional-replication) added developed-ex-US and
emerging equity over the *same* eras, pooled under a cross-region joint block bootstrap,
and **measured** how much effective sample size that bought.
[Experiment 006](#experiment-006--regional-momentum) ran the identical design on UMD,
using three regional momentum files nobody had downloaded.
[The size study](#size-on-the-three-panels--a-study-not-an-experiment) adds a fifth factor
to the same machinery, on the same files and eras, because a product decision downstream
turned on whether the **ex-US** size premium could be signed and only the US one had ever
been tested. **It froze no specification and is `exploratory`.**

---

## Conclusion

| Factor | Status | Why |
| --- | --- | --- |
| **HML** | **`exploratory`** | Pooled **+4.74 pp/yr** post-publication across three regions, joint 90% `[+1.46, +8.10]`, positive in all three, surviving its own best calendar year (+3.96) and Holm at 0.036. **No post-publication cell in Experiment 001 survived any correction** |
| **UMD** | **`exploratory`** | Pooled **+7.33 pp/yr**, `[+3.92, +10.31]`, positive in all three, surviving its best year (+6.65) and Holm at 0.0016. **But its detection threshold is 4.98 pp/yr, the worst here**, its regions are the least independent measured anywhere (1.33 effective, ρ̄ = 0.66), and **they crash together** — all three lost their worst calendar year in 2009 |
| **RMW** | **`unresolved` by this design** | Pooled **+2.53 pp/yr** against its window's own minimum detectable effect of **2.62** — the premium is below the smallest one this window could resolve. Adding two regions did not fix it |
| **CMA** | **`unresolved` by this design** | −1.39 pp/yr in the US, +0.20 pooled, against a 3.41 detection threshold |
| **SMB** | **not signable, on any panel** | Pooled **+0.33 pp/yr**, joint 90% `[−1.32, +2.06]`, against a **2.47** detection floor — the sharpest size instrument here. Developed ex-US **+0.49** `[−1.44, +2.44]` against 2.83; emerging −0.05; US +0.29 post-Banz. **Measured rather than transferred**, because HML is three times larger abroad and nothing said SMB would not be ([§Size](#size-on-the-three-panels--a-study-not-an-experiment)) |

The frozen ledger records which preregistered branch fired; the current claim-level
interpretation is **unresolved by this design**, not “the premium is zero.” The public
regional files did not supply enough effective information at the stated materiality point.
Different data, estimands, conditional models, longer windows, or lower-variance designs
remain open ([decision 0010](../decisions/0010-bars-carry-a-reopening-condition.md)).

**Neither advance is a discovery of a premium.** Each is a measurement that the premium
is larger than the threshold its pooled window can see: HML's window could detect only
3.35 pp/yr at 80% power and UMD's only 4.98, both above 2.0. They cleared because their
premia are 4.74 and 7.33, **not because the windows became powerful**. A premium between
2.0 and 4.98 pp/yr remains invisible to the momentum grid however it is pooled.

**Both premia are carried by the two non-US regions.** For HML the US contributes +1.57,
developed-ex-US +5.07, emerging +7.58. For UMD, +4.19 / +8.35 / +9.44 — and the US
momentum premium in the most recent decade is **+0.37 pp/yr** against +5.75 and +10.33
abroad.

**No factor may be described as working on this evidence.** These are academic
zero-investment long-short research portfolios, gross of transaction costs, shorting
costs, borrow, fees and taxes, which a retail investor cannot implement. The pooled
figures are a *looser* upper bound than the US ones, because emerging-market shorting is
hardest and dearest and the largest premium sits there.

---

## Era boundaries, and the publication record

Shared by all three experiments: **005 and 006 copy every era name and both boundaries
verbatim from 001's frozen specification, and a committed test compares the files
directly** so none can drift. Each boundary is **the first January strictly after the
journal issue date**, so no month of a "post-publication" era can precede the printed
result. Every citation and sample period was checked against Crossref DOI metadata and
the articles' own text on 2026-08-11; all eleven verified with no correction.

| Factor | Publication | Issue | Boundary | Original sample | Alternative date tested |
| --- | --- | --- | --- | --- | --- |
| HML | [Fama and French (1993)](https://doi.org/10.1016/0304-405X%2893%2990023-5) | Feb 1993 | 1994-01 | 1963-07…1991-12 | 1986-01 |
| UMD | [Jegadeesh and Titman (1993)](https://doi.org/10.1111/j.1540-6261.1993.tb04702.x) | Mar 1993 | 1994-01 | 1965-01…1989-12 | 1998-01, after Carhart |
| RMW | [Fama and French (2015)](https://doi.org/10.1016/j.jfineco.2014.10.010) | Apr 2015 | 2014-01 | 1963-07…2013-12 | 2016-01 |
| CMA | as above | Apr 2015 | 2014-01 | 1963-07…2013-12 | 2016-01 |

Three choices need defending. **1993 is dropped, not assigned** — HML's and UMD's papers
appeared in February and March, so the year belongs to neither era. **RMW and CMA's
2014-01 precedes their journal issue**: it is the first month outside the authors' own
estimation sample and follows the working paper, which is why 2016-01 is reported as
well. **CMA's discovery date is the most disputed of the four** — asset growth was
published in 2008, six years earlier — and a 2009-01 boundary is deliberately **not**
tested, because it would place the post-publication window inside the authors' estimation
sample. CMA's rejection therefore rests on the most generous available date, which makes
it stronger rather than weaker.

**The ambiguity changes nothing.** HML from 1986-01 gives +1.89 `[−1.48, +5.32]` against
+1.57; UMD from 1998-01 gives +3.65 `[−1.52, +8.56]` against +4.19.

---

## Experiment 001 — the United States grid

Two results dominate.

**Every cell that survives multiple-testing correction is a pre-publication cell.** Of
20 predeclared factor × era cells, five have a one-sided HAC *p* at or below 0.05
uncorrected; Benjamini–Hochberg at 0.10 leaves four, and all four are the factors' own
*original paper samples*. Not one post-publication cell survives, in any factor, under
either correction.

**Sixteen of the 20 cells hold a premium smaller than their own window could detect at
80% power, and the four exceptions are those same original samples.** A reader who takes
"the interval contains zero" as evidence of absence has misread every one of the sixteen.

The calibration check makes it concrete. A **zero-mean Gaussian series** with HML's length
and volatility, put through the identical procedure, produced +1.98 pp/yr, a 90% interval
of `[−1.70, +5.65]`, a −53.2% maximum drawdown and 247 months under water. HML's real
post-publication figures are +1.57, `[−2.28, +5.54]`, −57.8% and 228 months. **On these
statistics HML's post-publication record is not distinguishable from noise** — which is
not a claim that HML is noise, but a measurement of how little this window can say.

### The grid

Percentage points per year, gross. `90% interval` is a stationary block bootstrap at the
frozen 12-month mean block, 10,000 resamples. **MDE₈₀** is the smallest true premium the
window could reject a zero mean for at 80% power. **BH** is Benjamini–Hochberg across the
whole 20-cell family at α = 0.10.

| Factor | Era | Window | n | Premium | Vol | Sharpe | 90% interval | MDE₈₀ | BH |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| HML | original | 1963-07…1991-12 | 342 | **+4.56** | 8.79 | 0.518 | `[+1.31, +7.66]` | 4.10 | **0.040** |
| HML | first post-pub | 1994-01…2003-12 | 120 | +5.85 | 12.53 | 0.467 | `[−1.84, +13.98]` | 9.86 | 0.210 |
| HML | full post-pub | 1994-01…2025-12 | 384 | +1.57 | 11.43 | 0.137 | `[−2.28, +5.54]` | 5.03 | 0.402 |
| HML | recent | 2016-01…2025-12 | 120 | −0.44 | 13.32 | −0.033 | `[−8.28, +7.27]` | 10.47 | 0.714 |
| UMD | original | 1965-01…1989-12 | 300 | **+9.85** | 12.27 | 0.803 | `[+6.40, +13.32]` | 6.10 | **0.0002** |
| UMD | first post-pub | 1994-01…2003-12 | 120 | +10.53 | 19.70 | 0.534 | `[+2.78, +18.47]` | 15.49 | 0.101 |
| UMD | full post-pub | 1994-01…2025-12 | 384 | +4.19 | 16.55 | 0.253 | `[−0.34, +8.50]` | 7.27 | 0.172 |
| UMD | recent | 2016-01…2025-12 | 120 | +0.37 | 13.30 | 0.028 | `[−4.69, +5.41]` | 10.46 | 0.656 |
| RMW | original | 1963-07…2013-12 | 606 | **+3.17** | 7.79 | 0.407 | `[+1.14, +5.23]` | 2.73 | **0.035** |
| RMW | first post-pub | 2014-01…2019-12 | 72 | +1.64 | 5.08 | 0.322 | `[−0.05, +3.36]` | 5.16 | 0.301 |
| RMW | full post-pub | 2014-01…2025-12 | 144 | +3.04 | 7.35 | 0.414 | `[−0.32, +6.76]` | 5.27 | 0.168 |
| RMW | recent | 2016-01…2025-12 | 120 | +3.51 | 7.66 | 0.458 | `[−0.23, +7.56]` | 6.02 | 0.168 |
| CMA | original | 1963-07…2013-12 | 606 | **+3.91** | 6.93 | 0.564 | `[+2.06, +5.85]` | 2.42 | **0.002** |
| CMA | first post-pub | 2014-01…2019-12 | 72 | −2.46 | 5.29 | −0.465 | `[−4.96, +0.13]` | 5.37 | 0.889 |
| CMA | full post-pub | 2014-01…2025-12 | 144 | −1.39 | 7.91 | −0.176 | `[−5.00, +3.02]` | 5.68 | 0.748 |
| CMA | recent | 2016-01…2025-12 | 120 | −0.60 | 8.49 | −0.071 | `[−4.86, +4.35]` | 6.68 | 0.726 |

The common-period rows (2014-01…2025-12, the only window in which all four are
simultaneously post-publication) are omitted here and are in the artifact; they change
nothing. Bold marks the four BH survivors, which are also the only four cells whose
premium exceeds their own MDE₈₀.

### Risk, which the premium table hides

Geometric contribution is a diagnostic for a hypothetical fully collateralised overlay,
not an achievable return: a long-short spread financed at an unstated rate is not a
wealth path. Drawdown deepens mechanically with sample length and must never be compared
across unequal windows.

| Factor / era | Geometric %/yr | Max drawdown | Months under water | Worst 1y | Worst 10y |
| --- | ---: | ---: | ---: | ---: | ---: |
| **HML full post-pub** | **+0.92** | **−57.8%** | **228 of 384** | −35.2% | **−47.4%** |
| **UMD full post-pub** | **+2.78** | **−57.8%** | **205 of 384** | **−56.6%** | −41.7% |
| RMW full post-pub | +2.81 | −14.8% | 26 of 144 | −12.8% | +32.0% |
| CMA full post-pub | −1.69 | −27.2% | 95 of 144 | −15.9% | −14.3% |

HML spent **59% of its entire post-publication history below its prior peak**. UMD's
worst year was the 2008-12…2009-11 momentum crash.

### Decay, and the hostile tests

| Factor | Original | Full post-pub | Retained | Recent decade | Drop best calendar year |
| --- | ---: | ---: | ---: | ---: | ---: |
| HML | +4.56 | +1.57 | 34% | −0.44 | **+0.33** (2000) |
| UMD | +9.85 | +4.19 | 43% | +0.37 | +3.46 (1999) |
| RMW | +3.17 | +3.04 | **96%** | +3.51 | **+1.25** (2021) |
| CMA | +3.91 | −1.39 | sign flip | −0.60 | −3.96 (2022) |

**79% of HML's entire post-publication premium is the year 2000**, and 59% of RMW's is
2021. A premium that lives in one calendar year is a description of that year. The
decay pattern is consistent with
[McLean and Pontiff (2016)](https://doi.org/10.1111/jofi.12365) *and* equally consistent
with the original estimates having been inflated by selection; **this experiment cannot
separate those two mechanisms**, and neither can a before/after comparison in general.

**Era boundaries shifted ±24 months.** The one that matters: **CMA's full
post-publication premium goes from −1.39 to +0.40 at −24 months**, so the *sign* of the
rejection is not robust to the boundary. Two things keep the rejection standing — the
shifted window pulls in 2012–2013, inside the authors' estimation sample, and +0.40 is
still far below materiality, so clause (b) fires instead of (a). **This is the least
robust conclusion on the page and is reported as such.** No other shift changes a status.

**Bootstrap block length.** The corrected Politis–White automatic length lands between
1.00 and 4.79 months for 19 of 20 cells, far shorter than the frozen 12; intervals barely
move and no status changes. Two cells cross zero on a length choice — RMW and CMA's
first post-publication eras, both on 72 months, where six years of data cannot support
the distinction.

**Not run.** The equal-weighted robustness test **was not performed**: the library
distributes no equal-weighted variant. Since the value-weighted/equal-weighted choice
moves published replication rates from 35% to 58.6%, this is a **material untested
sensitivity**, not an omission of convenience.

---

## Experiment 005 — the regional replication

Experiment 001 ended by asserting that a regional check "would add breadth, not power",
because the regional files start 1990-07 and 1989-07 and are shorter than the
post-publication windows. **That reason was wrong, and correcting it is what made this
experiment possible.** It is true only of the *original-sample* eras. HML's
post-publication era begins 1994-01 and RMW's and CMA's 2014-01, so both regional files
begin before both boundaries with 42 and 54 months of head room. The experiment checks
that against the loaded series at run time and aborts on a silently truncated window.

Three regions × three factors × three post-publication era roles: a predeclared
**27-cell family**, plus nine pooled cells corrected as their own separate family,
because a pooled cell is a function of the same observations as the three beneath it.
`Developed_ex_US_5_Factors` is used and `Developed_5_Factors` is not, because the latter
**includes the United States** at roughly half its weight.

### Pooling, and the effective sample size actually achieved

Pooling is the equal-weighted composite of three monthly long-short series, weights
declared before the run: one vote per region, because the object is to count independent
looks, not to build a portfolio. **The interval is a cross-region *joint* stationary
block bootstrap** — one set of time indices drawn and applied to all three regions at
once, so contemporaneous cross-region dependence survives the resample.

| Factor | Era | Months | Pooled | Joint 90% | MDE₈₀ | ρ̄ | Eff. regions | Eff. N | Naive N |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| **HML** | **full post-pub** | **384** | **+4.74** | **`[+1.46, +8.10]`** | **3.35** | 0.52 | **1.49** | **573** | **1152** |
| HML | first post-pub | 120 | +8.31 | `[+1.65, +15.33]` | 6.92 | 0.51 | 1.49 | 178 | 360 |
| HML | recent | 120 | +4.15 | `[−2.36, +10.16]` | 6.89 | 0.56 | 1.45 | 174 | 360 |
| **RMW** | **full post-pub** | **144** | **+2.53** | **`[+1.07, +3.96]`** | **2.62** | 0.18 | **2.26** | **326** | **432** |
| RMW | first post-pub | 72 | +3.07 | `[+1.75, +4.42]` | 2.98 | 0.23 | 2.12 | 153 | 216 |
| RMW | recent | 120 | +2.25 | `[+0.60, +3.92]` | 2.94 | 0.16 | 2.31 | 277 | 360 |
| **CMA** | **full post-pub** | **144** | **+0.20** | **`[−2.57, +3.44]`** | **3.41** | 0.38 | **1.76** | **253** | **432** |
| CMA | first post-pub | 72 | −0.92 | `[−2.45, +0.68]` | 3.47 | 0.49 | 1.57 | 113 | 216 |
| CMA | recent | 120 | +0.73 | `[−2.62, +4.42]` | 4.03 | 0.39 | 1.74 | 209 | 360 |

**Eff. regions** is `mean_i var(r_i) / var(composite)` — the number of independent regions
three correlated ones actually amount to, measured from the realised sample rather than
assumed, and carrying its own joint-bootstrap interval because it is a sample statistic.
**Eff. N** is that times the month count. **Naive N** is what treating the regions as
independent would have claimed.

**HML: 1152 naive region-months bought 573 effective ones — an effective 1.49 regions out
of three, worth about one extra region.** RMW's regions are the least correlated (0.18)
so it got the most out of pooling, 2.26 regions — **and it still could not resolve its own
+2.53 premium.** For RMW and CMA the *entire* 90% sampling interval of the pooled MDE₈₀
sits above the 2.0 pp/yr threshold, and so does the whole Phase 1 systematic band, so
branch (b) is not a point-estimate artefact.

**Six of the nine pooled cells survive both corrections, including RMW's — which is
precisely why the correction is not the falsifier.** RMW's pooled premium is
statistically distinguishable from zero *and* below the smallest premium its window can
resolve at 80% power. A *p*-value answers "could this be zero?"; the minimum detectable
effect answers "could this window have found something worth having?". **Only the second
decides anything here.**

### What fired, clause by clause

| Clause | HML | RMW | CMA |
| --- | --- | --- | --- |
| (a1) pooled premium positive | ✓ +4.74 | ✓ +2.53 | ✓ +0.20 |
| (a2) at or above 2.0 pp/yr | ✓ | ✓ | ✗ |
| (a3) joint one-sided 95% lower bound above zero | ✓ +1.46 | ✓ +1.07 | ✗ −2.57 |
| (a4) sign shared by ≥ 2 of 3 regions | ✓ 3 of 3 | ✓ 3 of 3 | ✓ 2 of 3 |
| (a5) survives dropping its own best calendar year | ✓ +3.96 | ✗ +1.79 | ✗ −1.48 |
| (b) measured pooled MDE₈₀ above 2.0 | not reached | **fired, 2.62** | **fired, 3.41** |
| **Verdict** | **`exploratory`** | **`rejected`** | **`rejected`** |

Branch (b) is evaluated only after (a) fails, so it means "we found nothing material
*and* could not have found it". **HML never reaches it — but it remains blind to any
premium between 2.0 and 3.35 pp/yr**, which is most of the range this repository would
care about. RMW came within one clause of advancing, and the arithmetic agrees with the
verdict: its premium (2.53) is below its own MDE₈₀ (2.62), which is what clause (a5) says
in a different currency.

### Do the regions share the same episodes?

| Factor | Best year by region | Same? | Share of that region's premium |
| --- | --- | --- | --- |
| HML | US 2000, dev ex-US 2000, emerging **1997** | **no** | 2000: US **79.6%**, dev ex-US 22.5%, emerging **4.3%**; pooled 19.1% |
| RMW | US 2021, dev ex-US 2020, emerging 2014 | **no** | 2021: US **62.4%**, dev ex-US 19.1%, emerging 16.2%; pooled 35.3% |
| CMA | **2022 in all three** | **yes** | dropping it takes the pooled premium to −1.48 |

**HML's US episode concentration does not replicate** — the year carrying four fifths of
the US premium carries 4.3% of the emerging one. That is why clause (a5) passed. RMW's
does not replicate either but pooling did not save it. **CMA is the one factor whose
regions share an episode**, consistent with their 0.38 correlation, and they are the
least independent looks in the grid.

### Hostile tests

- **Resampling the regions independently — the error this experiment exists to avoid — is
  measurably wrong, and in one cell it manufactures a result.** It narrows HML's pooled
  interval by about 1.5× in every era, and for **HML's recent decade the invalid procedure
  returns `[+0.06, +8.09]`, excluding zero, where the valid joint procedure returns
  `[−2.36, +10.16]`.** RMW, whose regions are barely correlated, shows almost no gap —
  exactly what the mechanism predicts.
- **A pool excluding the US entirely** is the genuinely independent look, sharing no
  security with the US file. HML: **+6.33 `[+3.19, +9.58]`, stronger without the US.**
  RMW +2.28, still below its own threshold. CMA +1.00 — **the US sign flip is not
  replicated abroad**, so CMA's rejection rests on materiality rather than on the flip.
- **Inverse-variance weights** move HML +4.74 → +5.47, RMW +2.53 → +2.39, CMA +0.20 →
  +0.51. No verdict changes. They put 0.20 on the US, because the US series is the most
  volatile of the three in every factor.
- **A zero-mean Gaussian panel** with HML's length and measured cross-region covariance
  gives −0.89 pp/yr, `[−2.54, +0.76]`, MDE₈₀ 3.10 and 1.59 effective regions. The
  machinery recovers roughly the right effective sample from correlated noise and produces
  no premium from it.

---

## Experiment 006 — regional momentum

Experiment 005 recorded that UMD "could not be tested because no regional momentum file
exists in this repository". **That was true of the repository and false of the data.**
Ken French publishes `Developed_ex_US_Mom_Factor_CSV.zip` and `Emerging_MOM_Factor_CSV.zip`;
neither had ever been downloaded. Both begin before UMD's 1994-01 boundary with 38 and 48
months of head room. Their small zipped size is what one column of monthly data costs,
not evidence they are annual.

The design is Experiment 005's, **imported unchanged** rather than rewritten: same
regions, same frozen eras, same equal weights, same joint bootstrap, same falsifier.

| Era role | Region | n | Premium | Vol | MDE₈₀ | Holm |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| first post-pub | US | 120 | +10.53 | 19.70 | 15.49 | 0.101 |
| first post-pub | developed ex-US | 120 | +10.63 | 14.71 | 11.57 | 0.101 |
| first post-pub | emerging | 120 | +9.82 | 11.20 | 8.81 | **0.031** |
| full post-pub | US | 384 | +4.19 | 16.55 | 7.27 | 0.154 |
| full post-pub | developed ex-US | 384 | +8.35 | 11.86 | 5.21 | **0.003** |
| full post-pub | emerging | 384 | **+9.44** | 9.93 | 4.37 | **0.0000** |
| recent | US | 120 | **+0.37** | 13.30 | 10.46 | 0.459 |
| recent | developed ex-US | 120 | +5.75 | 8.90 | 7.00 | **0.065** |
| recent | emerging | 120 | +10.33 | 8.73 | 6.86 | **0.0005** |

Five cells survive Holm and **every one is non-US**. **The US recent decade is the row to
sit with**: +0.37 against +5.75 and +10.33 abroad, over the same months on disjoint
universes.

| Era | Months | Pooled | Joint 90% | MDE₈₀ | ρ̄ | Eff. regions | Eff. N | Naive N |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| first post-pub | 120 | +10.33 | `[+5.05, +15.51]` | 10.27 | 0.58 | 1.43 | 171 | 360 |
| **full post-pub** | **384** | **+7.33** | **`[+3.92, +10.31]`** | **4.98** | **0.66** | **1.33** | **512** | **1152** |
| recent | 120 | +5.48 | `[+2.14, +8.74]` | 7.11 | 0.64 | 1.36 | 163 | 360 |

**1152 naive region-months bought 512 — an effective 1.33 regions, the lowest figure
measured anywhere in this repository.** Momentum's regions are the most correlated of the
four factors, so pooling bought it the least, and the pooled MDE₈₀ of 4.98 pp/yr is
correspondingly the worst detection threshold here. All five branch (a) clauses passed;
branch (b) was never reached but **would have fired**.

### Do the regions crash together? Yes, and it is the finding

Momentum crashes are state-dependent, occurring in rebounds after bear markets
([Daniel and Moskowitz 2016](https://doi.org/10.1016/j.jfineco.2015.12.002)). Bear markets
are global, so the crash test was predeclared with the year **2009 named in advance**.

- **All three regions lost their worst calendar year in 2009.** US −52.9%, developed
  ex-US −36.8%, emerging −28.9%, pooled −39.9%.
- **Every one of the ten worst pooled months has all three regions negative.**
- All three are negative in the same month **17.5% of months against 4.3% under
  independence** — a factor of 4.1.
- All three are simultaneously in **their own worst decile 3.65% of months against 0.1%
  under independence** — a factor of 36. This measure conditions on nothing and is the
  cleanest of the four.

**The consequence is precise.** The 1.33 effective regions are measured over *all* months;
in the tail they are worse. **The pooled MDE₈₀ of 4.98 is therefore an upper bound on what
this window learned**, and a portfolio holding regional momentum tilts gets no
diversification from the regional split in exactly the episode that would matter.

Dropping 2009 *raises* the pooled premium to +9.05. The crash is a drawdown, not a premium
driver, so clause (a5) — which drops the *best* year — is the wrong question for momentum.
Both are reported.

Hostile tests match Experiment 005's: independent resampling narrows the interval by 1.34
to 1.51×; a US-excluded pool gives **+8.90 `[+5.84, +11.62]`, stronger without the US**;
inverse-variance weights give +8.15; the Gaussian null gives +0.64 with 1.35 effective
regions; and the Carhart alternative date gives +6.71, changing no status.

---

## Size, on the three panels — a study, not an experiment

**The question this answers.** A developed-ex-US small-value fund carries an SMB loading
near +0.5 to +0.7 beside its HML loading
([factor products](factor-products.md#what-is-decision-relevant)). Whether that leg is
an exposure worth paying for depends on whether the **ex-US** size premium can be signed,
and this repository has only ever tested the **US** one — as a quintile and decile spread
over `Portfolios_Formed_on_ME`, not as SMB
([Experiment 007](long-only-capture.md#momentum-and-size)). The US answer does not
transfer either way: HML is three times larger outside the United States, so nothing says
SMB behaves the same.

**No specification was frozen before these numbers were seen, so this is `exploratory`
and is a study rather than an experiment.** It reads the same three five-factor files
Experiment 005 pins, over the same eras, with the same 12-month block bootstrap, the same
10,000 resamples and the same conventional MDE₈₀. **It reproduces every published
Experiment 005 and 006 developed-ex-US and emerging cell exactly** — HML +5.071 and
+7.584, RMW +1.681 and CMA +0.533 on their own 2014-01 boundary, UMD +8.351 — which is
what licenses reading a new row beside them.

**SMB's own boundary is 1982-01**, the first January strictly after
[Banz (1981)](https://doi.org/10.1016/0304-405X%2881%2990018-0), *Journal of Financial
Economics* 9(1), March 1981 — the same rule the four factors above use, applied to a fifth.
**Outside the United States it makes no difference and cannot**: the international files
begin 1990-07 and 1989-07 and are entirely post-Banz, so **ex-US SMB has no
pre-publication era and no decay across a size boundary is measurable there at all.** The
figures below therefore report SMB on HML's 1994-01 window as well, which is the window
every product figure downstream uses.

Percentage points per year. `90% interval` is the joint stationary block bootstrap;
**MDE₈₀** is the smallest true premium the window could reject a zero mean for at 80%
power, on the conventional standard error, as everywhere else on this page.

| Panel | Era | Window | n | Premium | 90% interval | MDE₈₀ | HAC *t* |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: |
| US | full sample | 1963-07…2025-12 | 750 | +2.15 | `[−0.41, +4.78]` | 3.30 | 1.52 |
| US | post-Banz | 1982-01…2025-12 | 528 | **+0.29** | `[−2.22, +2.86]` | 3.80 | 0.19 |
| US | on HML's window | 1994-01…2025-12 | 384 | +0.57 | `[−2.44, +3.73]` | 4.74 | 0.31 |
| **Developed ex-US** | **full sample = post-Banz** | **1990-07…2025-12** | **426** | **+0.49** | **`[−1.44, +2.44]`** | **2.83** | **0.44** |
| **Developed ex-US** | **on HML's window** | **1994-01…2025-12** | **384** | **+0.49** | **`[−1.55, +2.56]`** | **2.85** | **0.43** |
| Emerging | full sample = post-Banz | 1989-07…2025-12 | 438 | +1.83 | `[−0.33, +4.16]` | 3.29 | 1.28 |
| Emerging | on HML's window | 1994-01…2025-12 | 384 | −0.05 | `[−1.72, +1.59]` | 3.07 | −0.04 |
| Both regions | recent decade | 2016-01…2025-12 | 120 | −1.31 / −2.19 | `[−4.28, +1.53]` / `[−5.19, +0.93]` | 3.66 / 4.15 | −0.86 / −1.30 |
| **Pooled, three regions** | **1994-01…2025-12** | equal weights, joint | **384** | **+0.33** | **`[−1.32, +2.06]`** | **2.47** | **0.33** |

**The ex-US size premium is not signable either, and the pooling that rescued HML does not
rescue it.** Every interval on every panel contains zero, every point estimate sits below
its own detection floor, and the pooled reading — **+0.33 against a 2.47 pp/yr floor** — is
the sharpest instrument this repository owns for size and still cannot sign it. For
comparison the same pooling gives HML **+4.74 against 3.35**, which is why one is
`exploratory` and the other is not.

**Three things this is not.**

- **Not evidence that the size premium is zero.** The pooled floor of 2.47 sits *above* the
  2.0 pp/yr materiality threshold, so this is branch (b): nothing was found *and* nothing
  material could have been. Read it beside
  [the resolution table](evidence-base.md#1-resolution-of-the-instruments-already-tested).
- **Not a formal rejection.** No falsifier was frozen for SMB, no multiple-testing family
  contains it, and no clause fired. It is a measurement, and its consequence is a
  restriction on how a *loading* may be priced, not a status for a factor.
- **Not decay.** Outside the United States there is no pre-publication era to decay from.
  Inside it, the post-Banz reading of +0.29 against a full-sample +2.15 is the same
  before/after comparison this page refuses to read causally everywhere else.

**The consequence is downstream and specific.** A fund's SMB loading is exposure to a
premium nobody here can sign, on any panel, so it contributes variance and no priced
expectation — pure drag on the geometric term. That is the argument that put a large-value
fund ahead of a small-value one on the US shelf, and **it now survives the only test that
could have overturned it abroad.**

---

## The systematic volatility band, and what carries none

The [Phase 1 gate](fama-french-reproduction.md) is **`unresolved`**: means, *t*-statistics
and all ten cross-factor correlations reproduce, but **the standard deviations of HML and
RMW do not**, by −3.03% and +5.09%, against two independently typeset vintages. That is a
vintage disagreement, not sampling error, so it is carried as a **separate band** and
never combined with a sampling interval.

**Where it changes a conclusion: nowhere, and that is structural rather than lucky.** The
primary metric, the falsifier and every rejection clause are functions of the *mean*,
which reproduced for all five factors. The band moves only volatility, Sharpe and the
minimum detectable effect. Propagated into the one place it could matter — the pooled
MDE₈₀ that decides branch (b) — it is roughly ±1.5%, because two of three legs are
unaffected, and **every branch (b) verdict holds at both ends of the band and across the
whole 90% sampling interval of the MDE.**

**Five series carry no measured band at all, which is weaker than a band of zero**: the
two regional five-factor files, and **all three momentum files, which were never gated
against any printed table in any region.** Their second moments are *unmeasured*. The
practical consequence is sharpest for Experiment 006: its branch (b) would have read a
pooled MDE built entirely on ungated volatilities, so unlike 005 it could not have bounded
that uncertainty at all.

---

## Cost, as a function of turnover

Never a haircut, and never subtracted from a premium above. The French series have no
turnover, no holdings and no tradable form, so no net figure for them exists. **Cost is a
function whose input is turnover, and turnover cannot be recovered from a return series**,
so every figure below is the consequence of a *stated* assumption. Using
`cost bp/month ≈ k × one-sided turnover %`, `k` in [1.0, 1.7]:

| One-sided turnover %/month | Cost at k = 1.0 | Cost at k = 1.7 | Inside the 50%/month retail limit? |
| ---: | ---: | ---: | --- |
| 1.0 | 0.12 pp/yr | 0.20 pp/yr | yes |
| 5.0 | 0.60 | 1.02 | yes |
| **27.5** | **3.30** | 5.61 | yes |
| 50.0 | 6.00 | 10.20 | at the limit |
| **91.5** | 10.98 | **18.67** | **no** |

**Which turnover belongs to what — getting this wrong is an order-of-magnitude error and
it has been made here before.** HML, RMW and CMA rebalance annually at end-June, giving a
declared 1.2–7.2%/month and **0.14–1.47 pp/yr**. UMD re-forms its portfolios **every
month in every region**, giving a declared 27.5–91.5% and **3.30–18.67 pp/yr** — against a
pooled gross premium of 7.33, so the pessimistic end is more than twice it and outside the
retail limit entirely, while the optimistic end consumes 45% of it. HML fares no better
in relative terms: 1.47 pp/yr against a US gross premium of 1.57.

**That range belongs to the academic long-short series and to nothing else.** A long-only
fund rebalancing semi-annually at *x*% one-sided has a monthly-equivalent turnover of
`x/6`, and *x* is not measured anywhere in this repository. Applying the academic row to
such a fund overstates its cost by roughly an order of magnitude, **and an earlier
analysis here did exactly that.** Read the schedule at whatever turnover the product
discloses.

---

## Verified, assumed, open

**Verified.** All three grids, era boundaries, falsifiers and the materiality threshold
were frozen before any number was computed, with hashes in the ledger — Experiment 005's
specification 15 minutes before its run, Experiment 006's before its module existed, when
all that had been seen of the momentum files was their hash, size, row count, date range
and column name. All seven source files are pinned by the SHA-256 of raw bytes *and*
derived table; a mismatch aborts. **Experiment 005's nine US cells and 006's three
reproduce Experiment 001's published figures exactly**, asserted in the output rather than
assumed. The regional files begin before every boundary, checked at run time per region.
The sample ends 2025-12 in all three; **six further months exist and were not read**.
`RF` is not subtracted from anything — all five FF5 series and UMD are already excess or
long-short, and subtracting it again would move every factor mean by −4.98 pp/yr and flip
every long-short sign.

**Assumptions.** Equal pooling weights, declared before the run, with inverse-variance as
a hostile test; no regional market-capitalisation series exists here to weight by. Every
cost figure rests on an **assumed** turnover. The frozen 12-month block, chosen a priori,
with the data-driven alternative reported for every cell. Normal-approximation power —
branch (b) reads the **conventional** pooled MDE, the more generous of the two for RMW, so
firing on it is a fortiori. **Both Benjamini–Hochberg corrections treat their tests as
independent and they are not** — eras nest, RMW and CMA share every era, all factors are
spreads over overlapping holdings — so **the corrected *p*-values are a lower bound on the
true correction**, which is why Holm is reported beside them throughout.

**Open.**

- **What the equal-weighted constructions do.** Untestable from the distributed files.
- **What the long-only capture fraction is.** Measured since, found to be a range rather
  than a number, and then found to be an HML loading rather than a multiplier
  ([Experiment 007](long-only-capture.md#the-correction-a-capture-fraction-is-a-loading-so-it-may-not-multiply-one)).
  The chain a shareholder receives is
  `premium × (fund loading − incumbent loading) − cost`, and these experiments moved only
  the first term, in gross long-short form.
- **What premium would be worth detecting.** Harvey, Liu and Zhu's structural estimate for
  a genuinely true factor is 6.6 pp/yr gross. Against the 2.0 pp/yr threshold used here,
  **no US post-publication window in Experiment 001's grid exceeds 26% power**, and
  pooling leaves the best threshold at 2.62 and momentum's at 4.98.

## What this does not establish

- **Not a publication effect.** A before/after comparison is descriptive and confounds
  publication with changing composition, valuation regimes, crowding and chance. Adding
  regions adds sample, not identification.
- **Not the authors' original series.** The distributed files apply the current vintage and
  construction to the whole history *including the pre-publication eras*, so the
  original-sample figures are not what the papers printed.
- **Not a currency-neutral result.** All files are USD unhedged. For a within-region
  long-short spread the exchange rate is multiplicative, so currency moves the second
  moment first-order and the mean only through the covariance `E[f × spread_local]` —
  **which is not zero a priori and is not measured here.**
- **Not independent of Experiment 001.** The US leg *is* Experiment 001, so a third of the
  pooled evidence is the data that produced the question.
- **Not "RMW does not work".** Under branch (b) it means the publicly available data
  cannot resolve the premium at the materiality threshold, so it cannot be signed either
  way.
- **Not a claim that HML or UMD works.** `exploratory` permits an investable implementation
  to be *tested* and permits nothing else.

---

## Consequence for this repository

1. **HML and UMD are `exploratory`, and both are promoted to nothing.**
2. **RMW and CMA are closed on the public files.** The earlier prioritisation of RMW as
   "the one worth looking at first" because it retained 96% of its premium is
   **superseded**: it retained its premium, and its premium is still smaller than the
   smallest one three regions of public data can resolve.
3. **Momentum's problem has moved from power to implementation.** Its construction
   rebalances monthly with an assumed cost that straddles its own gross premium, its
   post-publication path includes a −56.6% US year, and its three regions crash together.
   **The next momentum question is a measured turnover and a measured capture, not another
   premium experiment.**
4. **HML and CMA are never two independent bets** — 0.63 correlated. **Nor are regional
   sleeves**: three regions of HML are worth an effective 1.49 and of UMD 1.33, and for
   momentum a construction must additionally assume **no regional diversification at all
   in a crash**.
5. **The volatility band propagates and five series carry none.** Any downstream
   calculation dividing by one of those volatilities carries ±3.03% and ±5.09% as a
   separate systematic band, records that the other second moments are *unmeasured*, or
   says that it did not.
6. **The 2026-01-onward window is the natural confirmatory test** and has not been read in
   any region. Six to eight months against a 2.6 pp/yr floor is not yet worth spending it.
7. **SMB may not be priced into any chain, on any panel.** A fund's size loading is
   exposure to a premium that three regions and 384 joint months cannot sign, so it enters
   a growth calculation as variance and nothing else. This is what makes a large-value fund
   beat a small-value one on both shelves
   ([portfolio recommendation](portfolio-recommendation.md#optional-factor-tilts)),
   and it is a restriction on how a loading is used rather than a status for a factor.

## Reproduce it

```sh
cd research
uv run python -m portfolio_edge.experiments.exp_001_factor_decay --view-results
uv run python -m portfolio_edge.experiments.exp_005_regional_replication --view-results
uv run python -m portfolio_edge.experiments.exp_006_regional_momentum --view-results
uv run python -m portfolio_edge.studies._exus_value_tilt_tables   # the size study
uv run pytest tests/unit/test_experiments_exp_00{1,5,6}_*.py
uv run pytest tests/unit/test_studies_exus_value_tilt.py
```

The size study has **no run id, no spec hash and no ledger entry**, because it froze no
specification and is not an experiment. It reads the pinned files above, prints its own
reproduction of Experiment 005's and 006's developed-ex-US cells beside its new rows, and
is `exploratory` for exactly that reason.

| | Experiment 001 | Experiment 005 | Experiment 006 |
| --- | --- | --- | --- |
| Run | `37b77882963b45d09af9be418784ebda` | `aae878bfc1e649038966408ac9a29ba2` | `f52fd449df6540e5a0711697c8174140` |
| Spec hash | `f9184dfe2661…` | `6fd843b790b7…` | `3f13053c38d0…` |
| Seed | 20260811 | 20260812 | 20260812 |
| Grid | 4 × 5 = 20 cells | 3 × 3 × 3 = 27, plus 9 pooled | 1 × 3 × 3 = 9, plus 3 pooled |

Bootstrap: stationary block (Politis–Romano), 10,000 resamples, frozen 12-month mean
block; drawn **jointly across regions** for every pooled statistic. Source file hashes and
coverage are in [the evidence base](evidence-base.md) §2. Units are source percent →
parsed decimal → reported percent, on Python 3.12. **Each specification refuses to run
against a file whose SHA-256 is not the pinned one**: when Ken French publishes a new
vintage these experiments abort rather than report numbers.
</content>
