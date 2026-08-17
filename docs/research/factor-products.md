# Investable factor products: the exposure is delivered, the value is not

**Question.** Do exchange-traded factor products deliver the exposure they advertise,
stably, at a cost that leaves the exposure worth buying — and can a residual return be
separated from that exposure on the data available?

**Decision it informs.** Whether any retail factor product may be used as an
implementation proxy in a later experiment. Out of scope: allocation, sizing, after-tax
outcomes, and whether any factor premium exists — that is
[factor persistence](factor-persistence.md).

**Two experiments, one shelf split by region.** [Experiment 002](#the-us-shelf) audited
the US shelf; [Experiment 009](#the-ex-us-shelf) audited the ex-US and emerging shelf,
where [Experiments 005](factor-persistence.md#experiment-005--the-regional-replication)
and [007](long-only-capture.md) had located essentially all of the value premium's
measurable weight. Their screens are **complements over the same censuses** — a fund can
appear in at most one — and Experiment 009 asserts Experiment 002's two regexes
byte-for-byte before it runs.

**Status: `exploratory`, and nothing is promoted.**
[Decision 0002](../decisions/0002-no-research-grade-free-price-source.md) fixes the
ceiling until a source with a documented total-return and corporate-action contract is
licensed. All figures `as of 2026-08-12`.

---

## Conclusion

**Exposure delivery is answerable on these windows. Alpha is not.** Those are different
findings and merging them is the error this page exists to prevent.

| Shelf | Screened | Audited | `exploratory` | `rejected` | `unresolved` |
| --- | ---: | ---: | ---: | ---: | ---: |
| US (Exp 002) | 2,105 matched a mandate; 44 passed | 44 | **15** | 24 | 5 |
| Ex-US and emerging (Exp 009) | 537 matched; 26 passed | 25 | **12** | 8 | 5 |

1. **Exposure is largely delivered.** On the US shelf, **38 of 44 reject a zero intended
   loading in the mandate's own direction under Benjamini–Hochberg** — the only family
   here where a correction leaves most of its members standing. Twelve ex-US products
   clear the 0.15 bar with intervals excluding it from below.
2. **Alpha is negative almost everywhere and measurable almost nowhere.** 38 of 44 US
   shrunk alphas are negative, median −1.33 pp/yr. Only **8 of 44** raw alphas exceed the
   alpha their own window could detect at 80% power, and **all eight are negative**. The
   median minimum detectable alpha across the 132 US fund-by-specification tests is
   **4.52 pp/yr**, against a true cross-sectional dispersion of about 1.25 — the window is
   blunter than the effect by a factor of 3.6. Ex-US: median 3.23 pp/yr.
3. **The six positive US shrunk alphas are one trade.** VUG, IWF, IWY, IVW, IUSG and
   SPYG — every one a large-cap growth product, over a window in which large-cap growth
   beat the market. **Nothing here is alpha in the sense of skill.**
4. **The model itself has a measurable offset.** VTI *is* the market portfolio, so its
   alpha should be about minus its 3 bp fee; under FF5+UMD over these 72 months it is
   **−0.55 pp/yr (HAC *t* = −3.41)**. **Every alpha here is a distance from its pedestal,
   never from zero.** Subtracting it moves the median raw alpha from −2.92 to −2.38 —
   still negative — and cuts the funds whose distance from the pedestal exceeds their own
   detection threshold from 8 to 4. **The pedestal makes the alpha column less
   informative, not more real.**
5. **The regional panel is not a refinement; it decides the verdict.** Grading ex-US funds
   on the **US** panel instead of their own region's would put **16 of 25 below the 0.15
   bar rather than 5**, moving individual loadings by up to 0.480 — `IMFL` reads −0.258 on
   its own panel and +0.221 on the other. **An ex-US loading without its panel named is
   not a number.**
6. **Cost, not exposure, is what rejects a fund** — and the cost comparator is fitted in
   sample. See [§the comparator](#the-comparator-shrinkage-and-two-traps).

### What decided the rejections

| Clause | What it tests | US | Ex-US |
| --- | --- | ---: | ---: |
| (a) intended loading below 0.15 | the exposure is absent | 10 | 5 |
| (b) the loading flips sign across the fixed halves | the exposure is not an exposure | 1 | 1 |
| (c) shortfall to the cheap replication above 0.50 pp/yr | implementation value | **22** | **5** |
| (d) total cost above 1.0 pp/yr with no corresponding exposure | cost without exposure | 8 | 2 |

Clauses overlap. **Clause (c) did most of the work on both shelves — 27 of the 32
rejections — and it is decided against a comparator fitted in sample.** Read every (c)
rejection as *"a look-ahead combination of cheap funds beat this product over these
months"*, **never** as *"this product is badly run"*. The clearest demonstration is
`GWX`, which carries **the largest intended loading in the entire ex-US audit at +0.856**
and is rejected anyway.

---

## The US shelf

### What was run

| Field | Value |
| --- | --- |
| Specification | [`exp_002_fund_exposure.yaml`](../../research/experiments/exp_002_fund_exposure.yaml), hash `b4c9a134e106…` |
| Run kind | **exploratory**; does not consume the final holdout |
| Ledger `run_id` | `fbe139abd9114abeb69e39fad8839f8e`. Every outcome, exposure, replication, correction and universe figure is **byte-identical** to the two earlier successful runs of the same hash; the differences are two added diagnostics |
| Frame | SEC N-PORT **2019Q4**, 8,563 series. Follow-up 2025Q4, 12,552 series, used **only** to measure attrition |
| Returns | N-PORT Item B.5 monthly total return per share class; 1,205 filings across 44 funds, already net of expenses and reinvested distributions |
| Window | 2020-01…2025-12, **72 months**; nothing after 2025-12 was read |
| Model | FF5 + UMD, French vintage pinned by raw sha256; cash from the **same French file as the factors**, so the intercept is interpretable as alpha |
| Inference | Newey–West HAC at 6 lags; stationary block bootstrap, mean block **6 months frozen not tuned**, 10,000 resamples, resampling the return and the whole design jointly |
| Seed | 20260812 |

**The data path was gated before anything was believed.** Item B.5 reports `rtn1` as the
*first* month of the reporting period; reading it backwards would shift every history by
two months and leave every number looking plausible. So VTI, reconstructed from its own
filings, had to correlate at least 0.99 with the French market total return and show its
worst month in 2020-03. It correlates **0.99926**, betas 0.9968 with R² 0.99852, worst
month **2020-03 at −13.80%**.

### The screen: 2,105 to 44

Frozen before any return was read, mechanical, with no "and peers" clause. Criteria apply
in a fixed order and only the **first** failure is recorded, which is what makes the
funnel add up.

| Stage | Removed | Remaining | What went |
| --- | ---: | ---: | --- |
| 2019Q4 census | — | 8,563 | every series filing NPORT-P |
| mandate regex | 6,458 | **2,105** | everything naming no factor mandate |
| exclusion regex | 592 | 1,513 | international, global, income, allocation, emerging, dividend, bond, ESG, sector, leveraged, inverse |
| **exchange-traded** | **1,374** | **139** | open-end mutual funds with no listed share class — including the three largest series in the frame |
| minimum net assets ($1bn) | 92 | 47 | sub-billion ETFs |
| maximum expense ratio (0.60%) | 1 | 46 | PDP at 0.62% |
| inception cutoff (2016-12-31) | 1 | 45 | USMC |
| mandate in the frozen map | 1 | **44** | ILCG, which changed objective inside the window |
| complete return coverage | 0 | **44** | nothing; all 44 had all 72 months |

**The exchange-traded criterion is by far the largest filter, and it is a decision about
investability rather than quality.** Whatever this page concludes, it concludes about the
*listed* shelf.

Two structural facts about what survived. **The 44 are not 44 independent products** —
IVW/SPYG, IVE/SPYV, IJK/MDYG, IJJ/MDYV, IJS/SLYV, IJT/SLYG each track one index under two
sponsors, and IJH/SPMD and IJR/SPSM likewise: **sixteen funds are eight indices**, whose
loadings agree to about 0.001 and which received the same status. **And the shelf is thin
outside value and size**: 8 growth, 7 value, 5 mid-cap, 4 each small value, small growth,
mid value and mid growth, 3 small-cap, 2 quality, 2 multifactor, and **1 momentum**. MTUM
is the entire momentum shelf clearing a billion dollars and a 0.60% fee.

**One universe change is recorded rather than hidden.** The universe was rebuilt
**before any return was examined** to add nine growth ETFs that had been failing the
expense criterion only because nobody had looked their fees up — a gathering gap, not a
screen result, and leaving it would have stripped growth mandates out systematically, a
selection effect in exactly the direction that makes a value tilt look better. Six of the
nine are in the final 44 and three of the six positive alphas are among them.

### The exposure table

OLS of the fund's monthly excess return on `Mkt-RF, SMB, HML, RMW, CMA, UMD`, HAC at 6
lags, 72 observations. **Loading is sign-adjusted for the mandate** — a growth mandate is
graded on a *negative* HML loading, marked `HML (−)`, because growth is the short leg of
value and not an independent factor. **Shrunk** is the posterior mean under a fixed prior
using each fund's own standard error. **Shortfall** is positive when the product lost more
to its cheap replication than its fee premium explains.

| Ticker | Mandate | ER % | Intended | Loading | 95% interval | Raw α | Shrunk | MDE₈₀ | Shortfall | Status |
| --- | --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| VUG | growth | 0.03 | HML (−) | +0.284 | `[+0.207, +0.384]` | +2.25 | +1.23 | 3.19 | −4.19 | `exploratory` |
| IWF | growth | 0.18 | HML (−) | +0.278 | `[+0.200, +0.378]` | +2.27 | +1.36 | 2.86 | −0.58 | `exploratory` |
| IWY | growth | 0.20 | HML (−) | +0.302 | `[+0.207, +0.414]` | +3.09 | +1.45 | 3.74 | −1.39 | `exploratory` |
| IJH | mid cap | 0.05 | SMB | +0.480 | `[+0.390, +0.582]` | −3.47 | −1.48 | 4.06 | −0.28 | `exploratory` |
| SPMD | mid cap | 0.03 | SMB | +0.481 | `[+0.391, +0.582]` | −3.47 | −1.49 | 4.04 | −0.24 | `exploratory` |
| VBR | small value | 0.05 | HML | +0.410 | `[+0.322, +0.480]` | −2.78 | −1.50 | 3.22 | −0.62 | `exploratory` |
| IWN | small value | 0.24 | HML | +0.392 | `[+0.330, +0.464]` | −2.55 | −1.79 | 2.28 | +0.49 | `exploratory` |
| IVE | value | 0.18 | HML | +0.302 | `[+0.175, +0.429]` | −2.27 | −0.95 | 4.13 | +0.19 | `exploratory` |
| IUSV | value | 0.04 | HML | +0.310 | `[+0.184, +0.433]` | −2.18 | −0.93 | 4.07 | +0.06 | `exploratory` |
| SPYV | value | 0.04 | HML | +0.303 | `[+0.175, +0.429]` | −2.14 | −0.89 | 4.14 | +0.23 | `exploratory` |
| VLUE | value | 0.15 | HML | +0.393 | `[+0.269, +0.539]` | −2.40 | −0.66 | 5.71 | −0.32 | `exploratory` |
| FTA | value | 0.58 | HML | +0.452 | `[+0.354, +0.553]` | −3.85 | −1.49 | 4.40 | −0.33 | `exploratory` |
| IJJ / MDYV | mid value | 0.18 / 0.15 | HML | +0.411 | `[+0.287, +0.505]` | −2.96 / −2.90 | −0.91 / −0.89 | 5.26 | −0.56 / −0.57 | `exploratory` |
| EZM | mid cap | 0.38 | SMB | +0.554 | `[+0.456, +0.677]` | −3.43 | −1.31 | 4.45 | −1.06 | `exploratory` |
| IVW, IUSG, SPYG | growth | 0.18–0.04 | HML (−) | +0.207…+0.224 | contains 0.15 | +0.72…+1.06 | +0.34…+0.45 | ~4.0 | ≈0 | `unresolved` |
| SPHQ | quality | 0.15 | RMW | +0.176 | `[+0.079, +0.296]` | −0.56 | −0.26 | 3.75 | −0.13 | `unresolved` |
| JHMM | multifactor | 0.41 | HML | +0.212 | `[+0.127, +0.303]` | −3.60 | −1.66 | 3.78 | −0.11 | `unresolved` |
| VB | small cap | 0.03 | SMB | +0.599 | `[+0.516, +0.684]` | −2.97 | −1.63 | 3.16 | **+2.89** | `rejected` (c) |
| VTV | value | 0.03 | HML | +0.337 | `[+0.225, +0.471]` | −2.60 | −1.39 | 3.28 | **+2.57** | `rejected` (c) |
| IJR / SPSM | small cap | 0.06 / 0.03 | SMB | +0.889 | `[+0.796, +0.953]` | −2.99 | −2.26 | 2.00 | +0.95 | `rejected` (c) |
| IWD | value | 0.18 | HML | +0.350 | `[+0.228, +0.472]` | −3.63 | −2.10 | 2.99 | +0.63 | `rejected` (c) |
| MTUM | momentum | 0.15 | UMD | +0.444 | `[+0.277, +0.562]` | −2.95 | −0.55 | 7.34 | +1.10 | `rejected` (c) |
| QUAL | quality | 0.15 | RMW | +0.186 | `[+0.101, +0.247]` | −2.15 | −1.19 | 3.13 | +1.14 | `rejected` (c) |
| TILT | multifactor | 0.25 | HML | +0.148 | `[+0.113, +0.171]` | −0.95 | −0.86 | **1.08** | −1.21 | `rejected` (a) |
| IJK / MDYG / IJT / SLYG | mid & small growth | 0.16–0.18 | HML (−) | **−0.067** | contains 0 | −3.7…−4.3 | −1.7…−1.9 | ~4 | +1.4…+1.6 | `rejected` (a, c, d) |
| VO, VOE, VOT, IWR, IWS, IWP, IWO, VBK, RPG, SLYV, FTC | various | | | | | | | | | `rejected` |

**Four "growth" products delivered a positive HML loading.** IJK, IJT, SLYG and MDYG have
sign-adjusted loadings of −0.067, meaning a raw HML loading of **+0.067**: graded against
the short leg of value and tilted, weakly, towards value. That is an exposure-delivery
failure and it is what clause (a) exists to catch.

**Rolling loadings are stable almost everywhere.** Thirty-seven 36-month windows per fund;
only RPG (twelve sign changes), VOT (two) and FTC (one) change sign at all. TILT's rolling
loading moves over a range of 0.058 across six years, the tightest on the shelf.

### Statistical alpha versus implementation value

The specification forbids collapsing these. **A fund can be worth owning with zero alpha
if it delivers a wanted exposure cheaply; a positive alpha over a short history is not
evidence of skill.** Four cases make it concrete.

- **VUG.** Shrunk alpha +1.23 and it beat its cheap replication by 4.19 pp/yr. Both
  numbers are the same fact and neither is skill: because a fund is never part of the
  basis that replicates it, **VUG's replication degenerates to VTI at weight 1.000**, so
  its "shortfall" is the realised excess return of large-cap growth from 2020 to 2025.
  *Statistical conclusion: none. Implementation conclusion: VUG delivered a −0.284 HML
  loading stably at 3 bp.*
- **TILT.** The only genuinely powered alpha here — HAC standard error **0.38 pp/yr**
  against a median of 1.44, MDE₈₀ **1.08** against a median of 4.02, shrinkage factor
  0.913 because it barely needs shrinking. Raw alpha −0.95 on a 0.25% fee, and it beat its
  replication by 1.21. **`rejected` anyway on clause (a): HML loading +0.148 against a
  0.15 threshold, a miss of 0.002**, on an interval that contains the threshold.
- **IJH and SPMD.** Same index, loadings +0.480 and +0.481, alphas −3.47 both, fees 0.05%
  and 0.03%. *Statistical conclusion: none — a −3.47 alpha against a 4.05 detection
  threshold is an unmeasured quantity. Implementation conclusion: mid-cap exposure is
  available at 3 bp with no measurable shortfall.*
- **EZM, FTA, JHMM.** Fees of 0.38%, 0.58% and 0.41% — the three dearest funds not
  rejected — with **negative** shortfalls. **A fee comparison is not a cost comparison**,
  and this is the direction usually forgotten.

The reverse case is the common one. **27 of 44 products have a positive shortfall and 22
exceed the 0.50 pp/yr clause, while the largest fee premium any product carries over its
own replicating basis is 0.55 pp/yr and the median is 0.12.** The biggest shortfalls — VB
+2.89, VBK +2.84, VOT +2.60, VTV +2.57 — are five to a hundred times any fee difference.
**Whatever separates these products from cheap broad funds over this window, it is not the
expense ratio.**

### The falsifier, and why a *t*-statistic is not part of it

Verbatim, frozen before any return was read: a fund is rejected when **any** of (a) its
intended loading is below 0.15; (b) that loading's sign flips between the fixed halves;
(c) its tracking difference against a cheap broad fund plus a combination approximating
its exposures is worse than its expense-ratio advantage by more than 0.50 pp/yr; or (d)
its total realised cost of ownership exceeds 1.0 pp/yr above the broad-market comparator
without a corresponding exposure. **"A t-statistic on residual alpha below 2 is NOT a
falsifier: it usually means the sample cannot identify a small residual return, not that
the fund is useless."**

**A *t*-rule would not even be conservative here, which is what is usually missed: 26 of
the 44 primary alphas already have |*t*| ≥ 2, and 24 of those 26 are negative.** Reading
*t* as the verdict would not kill the shelf for being unmeasurable; it would convict most
of it of a large negative residual that 72 months cannot separate from model misfit.

Three boundary cases decide how the statuses read. **`unresolved` is a statement about the
interval, `rejected` about the point estimate** — TILT at +0.148 `[+0.113, +0.171]` is
`rejected` while IVW at +0.224 `[+0.141, +0.328]` is `unresolved`, both intervals
containing the threshold and the point estimate breaking the tie in opposite directions.
**Clause (b) fired once**, on FTC, whose loading is indistinguishable from zero anyway.
**Clause (d) never fired alone** — all eight firings are on funds that had already fired
(a) and (c), because (d) requires a missing exposure by construction.

### The multiple-testing family

**The family is 44 funds × 3 specifications = 132 alpha tests**, not the specification
anyone chose to report: CAPM, FF3 and FF5+UMD are all estimated and all 132 *p*-values
enter the correction, because a residual appearing in one specification and not the others
is not a finding.

| Correction | Rejections of 132 |
| --- | ---: |
| Uncorrected at 0.05 | 56 |
| **Benjamini–Hochberg at 0.10** | **54** |
| **Holm–Bonferroni** | **5** |
| BH, family padded to every mandate-matching series × 3 = 6,315 | 2 |
| Holm, padded family | **0** |

**BH assumes independence and this family has almost none** — three nested specifications
per fund, the same six factors, the same 72 months, eight pairs of funds on an identical
index — so the artifact itself calls the BH count "an OPTIMISTIC bound and Holm the
defensible one". **Holm leaves five tests, all negative, and IJR and SPSM are the same
index, so five tests are three products.** Padding with *p* = 1 for the 6,183 never
regressed cannot create a rejection and strictly tightens both corrections; it leaves 2
and 0.

**Exposure is the family that survives.** The intended-loading tests are a separate
44-member family: 37 reject uncorrected and **38 under BH**. **That asymmetry — 38 of 44
loadings against 5 of 132 alphas under a defensible correction — is the whole result in
two numbers.** It is also a weaker claim than the falsifier's, which asks for a loading of
0.15 rather than merely one distinguishable from zero.

---

## The ex-US shelf

**The frame is the union of the 2019Q4 and 2025Q4 censuses**, unlike Experiment 002's,
and for a reason that would otherwise select the answer: AVDV launched 2019-09; AVIV, AVES
and DISV in 2021-09; DFIV in 2021-11; DFEV in 2022. **A 2019Q4-only frame would have
excluded exactly the products the question is about.** The asset floor is **half** of
Experiment 002's, chosen from the *count* of qualifying series visible before any return
was downloaded and never from performance — at $1bn the ex-US screen returns 23 series and
at $500m it returns 39, and one of the questions is whether the shelf is deep enough to
matter.

Of 537 matching series, 26 passed the screen and 25 had at least 36 filed monthly returns.
**Median usable history is 76 months against Experiment 002's uniform 72** — so the ex-US
window is not the shorter one, which was the expected objection and does not hold.

### The twelve that deliver

Loading is on the intended factor in the fund's **own** region's panel. `α*` is shrunk and
decides nothing.

| Ticker | Region | Factor | Loading | 95% interval | Months | α* |
| --- | --- | --- | ---: | --- | ---: | ---: |
| **DFIV** | developed ex-US | HML | **0.662** | `[0.52, 0.85]` | 51 | −1.93 |
| **FNDC** | developed ex-US | SMB | **0.671** | `[0.55, 0.82]` | 76 | +0.18 |
| **SCHC** | developed ex-US | SMB | **0.629** | `[0.46, 0.77]` | 76 | −0.65 |
| **DFIS** | developed ex-US | SMB | **0.591** | `[0.46, 0.72]` | 45 | +0.65 |
| **SCZ** | developed ex-US | SMB | **0.551** | `[0.43, 0.64]` | 77 | −0.39 |
| **IDMO** | developed ex-US | UMD | **0.540** | `[0.39, 0.71]` | 77 | +0.03 |
| **AVDV** | developed ex-US | HML | **0.510** | `[0.32, 0.77]` | 75 | +0.24 |
| **IMTM** | developed ex-US | UMD | **0.505** | `[0.44, 0.59]` | 77 | −1.46 |
| **DISV** | developed ex-US | HML | **0.495** | `[0.36, 0.64]` | 45 | −0.09 |
| **AVIV** | developed ex-US | HML | **0.489** | `[0.36, 0.64]` | 51 | −2.27 |
| **IVLU** | developed ex-US | HML | **0.475** | `[0.31, 0.60]` | 77 | −0.67 |
| **EFV** | developed ex-US | HML | **0.368** | `[0.25, 0.49]` | 77 | −1.58 |

**Every one is developed ex-US. No emerging-market product reached `exploratory`.**

`unresolved`, the interval containing the bar: IDHQ (RMW 0.321), **DFEV (emerging HML
0.267, 44 months)**, **AVES (emerging HML 0.237, 51 months)**, TLTD (HML 0.205), IQLT
(RMW 0.184). **Both emerging value products are here**, and neither because it failed —
their point estimates are positive and their windows are short. This is the status the
specification predicted a short window would produce.

`rejected`: EFG, GWX and DIHP on clause (c) alone, losing 2.76, 1.61 and 1.23 pp/yr to
their replications; RODM and IMFL on (a), (c) and (d); JHMD on (a) and (b); JHEM and MFEM
on (a).

### What the ex-US shelf actually contains

| Exposure | Developed ex-US | Emerging |
| --- | ---: | ---: |
| Value | 5 | 2 |
| Small cap | 5 | — |
| Small-cap value | 2 | — |
| Multifactor | 4 | 2 |
| Quality | 3 | — |
| Momentum | 2 | — |
| Growth | 1 | — |

**Emerging markets — where the largest value premium was measured — has four products in
total, two rejected and two unresolved.** That is concentration risk the specification's
mechanism section predicted: an exposure may exist in only one product at any price, which
is not a choice.

### The drag that could not be measured

The intended method was to bound the ex-US withholding drag by comparing each region's
market fund against its own French market portfolio. **It failed, and the honest reading is
that the method failed rather than that the drag is small.** VEA beat its region's French
market portfolio by 0.517 pp/yr beyond its fee while VTI *trailed* the US one by 0.349 — a
difference of **+0.866 pp/yr in the wrong direction**. A negative difference would have
been an upper bound; a positive one means index-construction differences swamp whatever
withholding costs. **Withholding is certainly being paid, is inside every ex-US return
here, and is not separable from the benchmark mismatch by this construction.** Anything
that needs it needs Form N-CSR or a 1099-DIV.

---

## The comparator, shrinkage, and two traps

**Every alpha is shrunk before it means anything.** Taking true gross alpha as normal with
mean zero and cross-sectional standard deviation `sigma_true = 1.25%/yr`
([Fama and French 2010](https://doi.org/10.1111/j.1540-6261.2010.01598.x)), the posterior
mean is `observed × sigma_true**2 / (sigma_true**2 + SE**2)`, computed with **each fund's
own HAC standard error** and never a reference factor. Realised factors on the US shelf run
**0.162 to 0.913, median 0.431**.

**Trap one: an annual alpha is twelve times a monthly intercept, so its standard error
annualises by ×12 and never by ×√12.** Using √12 would divide every standard error by 3.46
and shrink far too little — on RPG it would move the posterior from −0.81 to −3.49, a
factor of four. **The shrunk alpha carries no interval by construction**, a posterior mean
under a fixed prior not being a sampling estimate, so the raw alpha, its HAC standard error
and MDE₈₀ are printed beside it and it must never be quoted alone.

**Trap two: the cheap replication is fitted in sample.** The comparator is a combination of
**VTI, VUG, VTV and VB** (US) or **VEA, VWO, VSS, EFV and EFG** (ex-US) with non-negative
weights summing to one, fitted by constrained least squares on the **same months** as the
exposure regression. An investor could not have known those weights in advance, so **the
comparison is a best case for the replication and therefore a hard test for the product**,
and a sampling interval around a look-ahead quantity would imply a precision the
construction does not have. The general rule that this comparator, not the market, is the
control is [decision 0003](../decisions/0003-cheap-broad-market-control.md).

Two structural facts a reader needs before using clause (c). **Three of the four US
building blocks are themselves audited products, and a fund is never in its own basis**, so
the replication degenerates for exactly those three: VUG is replicated by VTI at weight
1.000, VB by 0.733 VTI + 0.267 VTV, VTV by 0.784 VTI + 0.216 VB. **For these three the
"implementation shortfall" is the realised style return of 2020–2025 rather than an
implementation cost**, and VB's and VTV's rejections should be read as "small-cap and value
underperformed the market over these 72 months" — a return finding this page is not
entitled to make. And **tracking error against the combination ranges 1.38 to 8.65 pp/yr,
median about 5**, against a clause-(c) threshold of 0.50. **Clause (c) is a decision rule
applied as frozen, not a measurement.**

---

## Attrition, survivorship, and a defect that was corrected

The frame is taken at the **start** of the window so attrition is measurable rather than
invisible: screening the 2025Q4 census would select on survival.

| Quantity | Artifact's figure | Recomputed, separating a death from a rename |
| --- | ---: | ---: |
| US series present in frame, absent at follow-up | **358 (23.66%)**, $333.5bn | **312 (20.62%)**, **$138.7bn** |
| Ex-US, same decomposition | 32.3% naive | **88 of 322 (27.3%)**, $19.5bn |

**The artifact's US figure counts renames as deaths.** The "disappeared" set is a
difference of two sets each built by running the patterns over that census's *own* series
names, so a series that renamed out of the pattern is counted as gone even though it is
still filing. The committed file contradicts itself: **four of its own fifteen largest
"disappeared" series are recorded elsewhere in the same file as still filing at the
follow-up quarter**, holding 136.3, 17.3, 4.4 and 2.6 bn USD. The 46-series difference
carries $194.8bn, 58% of the headline, and one fund is most of it. Experiment 009
recomputed the decomposition on Experiment 002's own patterns, as a diagnostic and without
touching that experiment, and reached the same 312 and $138.7bn. **The defect is in the
artifact; the corrected number is quoted everywhere else.**

**The direction is unchanged and the caveat holds.** Even at 20.6%, a fifth of the 2019
listed factor shelf is gone in six years, and this is a **lower bound**: N-PORT begins in
2019, so a fund that closed earlier is invisible to both censuses. **None of the audited
funds is absent at follow-up, which is true by construction** — 72 months of filed returns
were required to enter the panel.

---

## Hostile tests: what ran, and what was wrong on the way

| Declared test | Status |
| --- | --- |
| Re-estimate under CAPM, FF3 and FF5+UMD and report all three | **Run.** 132 fits; the correction consumes all of them |
| Fixed calendar halves and rolling 36-month windows | **Run.** 37 windows per fund |
| Substitute DGS3MO and DFF for TB3MS | **Run.** Wrong in the first two successful runs; fixed |
| Every screened fund and specification in the denominator | **Run.** 6,315-member padded family |
| **Cross-check every N-PORT return against an independent source** | **Did not run at all** |
| Report MDE₈₀ beside every alpha | **Run** |
| Measure attrition between the censuses | **Run**, with the defect above |

**The cross-source check produced nothing.** All 44 US and all 25 ex-US tickers are in the
`unavailable` list with `HTTPError` and the `compared` list is empty. **Form N-PORT Item
B.5 is therefore the sole measurement of every return here, with no independent
corroboration of any kind**, and the specification's stated reason for having a secondary
source — "two independent measurements make a silent adjustment error visible" — is unmet.

**The cash-rate diagnostic was wrong in two earlier runs, and the error is worth recording
because it was large and pointed the wrong way.** Both printed the French one-month bill in
*percent* beside FRED series in *decimals*, producing an "alpha shift" of about 2.637 pp/yr
that would have been the largest single quantity in the audit. Corrected, with a unit guard
that now refuses a series whose declared units are wrong, the shifts are −0.09, −0.20 and
−0.09 pp/yr. **No conclusion ever depended on it**: a constant shift in the dependent
variable moves only the intercept, so every loading is invariant by construction.

**The model-misfit pedestal was added between runs and is the one addition that changes how
the page reads.** Without it the audit reports that a three-basis-point index fund carries a
−3 pp/yr alpha and leaves the reader to guess how much is the model. It is a control, not a
result.

---

## Verified, assumed, open

**Verified.** The screen was frozen, mechanical and applied before any return was
downloaded; returns were never fetched for a fund that failed it, so **no screen decision
could be revised after seeing performance**, and all 2,105 mandate-matching series are
committed with their outcome and first failing criterion. The Item B.5 month alignment is
checked, not assumed. All 44 US funds have 72 of 72 months with no gap and no
interpolation. The expense ratio is **not** subtracted twice — Item B.5 is already net.
Every excess return is taken over the rate `Mkt-RF` is defined against. Both French files
are pinned by raw sha256 and a new vintage aborts the run. The HML/RMW volatility band does
**not** propagate here: every figure is a loading, a mean or a difference of means, and
nothing divides by those volatilities. Experiment 002's two regexes were asserted
byte-for-byte before Experiment 009 ran.

**Assumptions.** `sigma_true = 1.25%/yr` is *transferred, not measured* — it comes from a
bootstrap of US active mutual funds over 1984–2006 and is applied to index-tracking ETFs
over 2020–2025, and it decides every shrunk number here. The intended-factor map is a
declaration written before any regression, so no fund could be graded against whichever
loading turned out largest. The thresholds are a priori and none is tuned. Benjamini–
Hochberg treats the tests as independent and they are not. **Every figure is PRETAX**, and
bid-ask spreads, brokerage, realised distributions and portfolio turnover are absent
entirely.

**Open.**

1. **How much of the remaining −2.38 pp/yr median is still model misfit?** The pedestal
   measures the misfit a fund with *market* exposure carries. A small-cap value fund is not
   the market, and **a pedestal per style does not exist**.
2. **Does any N-PORT return agree with an independent measurement?** Unanswered for all 69
   funds.
3. **What do realised distributions and turnover do to the cost ranking?** Neither is in
   N-PORT; both are in N-CSR as unstructured HTML. **Clause (d) is evaluated without the
   distribution term the falsifier names.**
4. **Would an out-of-sample replication change clause (c)?** Weights fitted on a prior
   window would remove the look-ahead. Not runnable on 72 months without shortening the
   estimation window further.
5. **What is a fund's delivered *capture*, as opposed to its loading?** Every capture
   figure here is from research portfolios. Measuring a fund's own needs **holdings rather
   than returns** — which N-PORT carries and no experiment has read.

## What this does not establish

- **Not skill, in any direction.** Six positive US shrunk alphas, all large-cap growth,
  none exceeding its own detection threshold, all measured against a model that charges the
  market portfolio itself −0.55 pp/yr.
- **Not investable cost.** Nothing here is a net-of-everything return.
- **Not a survivorship-free universe.** The measured attrition is a lower bound.
- **Not audited data.** Item B.5 returns are fund-reported and unaudited, and General
  Instruction G lets each filer use its own methodology, so two funds' returns are not
  guaranteed to be computed identically. With the cross-source check dead, that assumption
  is untested.
- **Not the whole shelf.** Exchange-traded only, above an asset floor, below an expense
  cap, inception before a cutoff.
- **Not a return finding.** Where a product's shortfall is really the realised style return
  of 2020–2025, this page is measuring the window, not the product.

**The binding constraint is the data contract and the length of the window, not the
evidence.** Form N-PORT is a materially stronger contract than any price feed decision 0002
tested, and it is still not enough to promote anything.

---

## Consequence for this repository

1. **Nothing is promoted, and decision 0002 is not the only reason.** Even with a licensed
   source, no product here would qualify: the alpha column is unmeasurable, and the cost
   comparison that rejected 27 of 32 is decided by a look-ahead comparator.
2. **Exactly what would change that.** A licensed, point-in-time, survivorship-free
   total-return source covering the listed shelf **from at least 2003, so the window is 240
   months rather than 72** ([evidence base](evidence-base.md) §4). Re-freeze and run
   **confirmatory**. Promotion then requires **all** of: intended loading ≥ 0.15 with a 95%
   interval excluding 0.15 from below; the same on both fixed halves; shortfall ≤ **0**
   pp/yr against a replication fitted on a **prior** window; total cost of ownership
   including realised distributions and turnover ≤ 1.0 pp/yr; and the underlying factor at
   `exploratory` or better. **A residual alpha of any sign or size remains inadmissible as a
   promotion criterion.**
3. **Any page that prints a fund alpha prints its pedestal beside it.** The control costs
   one extra regression and it is the difference between "this index fund destroyed
   3 pp/yr" and "this model does not span 2020–2025 to better than half a point".
4. **Any ex-US factor loading names its panel.** On this evidence the US panel is wrong by
   enough to reverse eleven verdicts.
5. **The edge budget's fund-cost line survives, with an addition.** It books 49 bp against
   an investor's own counterfactual, untouched here. What this page adds is the quantity
   that line does not carry: **for most of this shelf the gap to a cheap replication is
   larger than the fee** — 22 of 44 lost more than 0.50 pp/yr against a fee premium of at
   most 0.32 and typically 0.12. **A fee comparison is not a cost comparison.**
6. **The listed factor shelf is thinner than it looks.** Forty-four US products of which
   sixteen are eight indices sold twice, one is the entire momentum shelf, and two each are
   quality and multifactor. On the ex-US side, four emerging products in total. Any later
   work needing a momentum, quality or emerging-value proxy has one candidate or none.

## Reproduce it

```sh
cd research
uv run python -m portfolio_edge.experiments.exp_002_fund_exposure --build-universe
uv run python -m portfolio_edge.experiments.exp_002_fund_exposure --view-results
uv run python -m portfolio_edge.experiments.exp_009_exus_products --view-results
uv run pytest tests/unit/test_experiments_exp_002_fund_exposure.py
uv run pytest tests/unit/test_exp_002_universe_committed.py
```

| | Experiment 002 | Experiment 009 |
| --- | --- | --- |
| Specification | `exp_002_fund_exposure.yaml`, `b4c9a134e106…` | `exp_009_exus_factor_products.yaml`, `e99e2a6e27…` |
| Run reported | `fbe139abd9114abeb69e39fad8839f8e` | `f6ce1701324546b28c03598c935b7819` |
| Other ledgered runs | 1 `failed`, 3 `abandoned`, 2 superseded `succeeded` | 2 earlier `succeeded`, 1 `failed` on a non-JSON-compliant `NaN` |
| Seed | 20260812 | 20260812 |

The superseded successful runs are kept rather than deleted, because the difference between
them is the record of the two diagnostics above. Committed universe and product-facts
manifests were written **before any return was downloaded**, each fee, index and inception
with its own URL and date. Every run's git commit, working-tree diff hash,
dataset-manifest hashes, artifact hashes and `results_viewed` event is in
[`research/ledger.jsonl`](../../research/ledger.jsonl).
</content>
