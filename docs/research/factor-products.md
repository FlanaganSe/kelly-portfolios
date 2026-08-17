# Investable factor products: the exposure is delivered, and the frame decided the rest

**Question.** Do exchange-traded factor products deliver the exposure they advertise,
stably, at a cost that leaves the exposure worth buying — and can a residual return be
separated from that exposure on the data available?

**Decision it informs.** Whether any retail factor product may be used as an
implementation proxy in a later experiment. Out of scope: allocation, sizing, after-tax
outcomes, and whether any factor premium exists — that is
[factor persistence](factor-persistence.md).

**Three experiments over two shelves.**
[Experiment 002](#the-us-shelf-as-experiment-002-framed-it) audited the US shelf against
the **2019Q4 census alone**. [Experiment 009](#the-ex-us-shelf) audited the ex-US and
emerging shelf against the **union of the 2019Q4 and 2025Q4 censuses**, because a
2019Q4-only frame "would have excluded exactly the products the question is about".
[Experiment 013](#the-us-shelf-on-the-corrected-frame) applies that same correction to the
US shelf, which nobody had done, and re-runs Experiment 002 unchanged on the corrected
frame. All three assert Experiment 002's two screening regexes byte-for-byte before they
run.

**Status: `exploratory`, and nothing is promoted.**
[Decision 0002](../decisions/0002-no-research-grade-free-price-source.md) fixes the
ceiling until a source with a documented total-return and corporate-action contract is
licensed. Experiment 013's figures are `as of 2026-08-17`; Experiments 002 and 009 are
`as of 2026-08-12`.

---

## The correction, and whether the conclusion survives

**It does not, and the half of it that fails is the half this page was named after.**

> **Experiment 002's frame could see 44 US factor products. The corrected frame finds
> 109.** Of the 65 it adds, **13 fire clause (c) against 22 of the original 44**, their
> median shortfall to the cheap replication is **−0.48 pp/yr rather than +0.53**, and
> **33 of them reach `exploratory`**. Every systematic value and small-value product on
> the US shelf — AVUV, AVLV, AVSC, DFAT, DFSV, DFUV, DFLV, DFAS — is in the added set,
> every one delivers its intended loading, and **every one clears clause (c), most of
> them by beating a look-ahead replication outright**.

What survives unchanged, and is now measured on two and a half times as many funds:

- **Exposure delivery is answerable on these windows. Alpha is not.** Those are different
  findings and merging them is the error this page exists to prevent.
- **No positive alpha anywhere exceeds what its own window could detect.** Sixteen of 109
  raw alphas beat their own 80%-power threshold and **all sixteen are negative**.
- **Nothing is promoted.** `exploratory` permits a product to be *tested* as an
  implementation proxy and permits nothing else.

**What changed is a frame, not a method.** Experiment 013 estimates every one of
Experiment 002's 44 funds on the same 72 months with the same functions, and reproduces
its loadings, alphas, implementation shortfalls and statuses to **zero difference in
every figure**. Nothing Experiment 002 computed was wrong. It was computed on a census
that could not see two thirds of the shelf.

| Shelf | Screened | Audited | `exploratory` | `rejected` | `unresolved` |
| --- | ---: | ---: | ---: | ---: | ---: |
| **US, corrected frame (Exp 013)** | 3,169 matched a mandate; 116 passed | **109** | **48** | 48 | 13 |
| US, 2019Q4 frame (Exp 002) | 2,105 matched; 44 passed | 44 | 15 | 24 | 5 |
| Ex-US and emerging (Exp 009) | 537 matched; 26 passed | 25 | 12 | 8 | 5 |

---

## Conclusion

1. **Exposure is largely delivered.** On the corrected US shelf, **96 of 109 reject a zero
   intended loading in the mandate's own direction under Benjamini–Hochberg** — the only
   family here where a correction leaves most of its members standing. Twelve ex-US
   products clear the 0.15 bar with intervals excluding it from below.
2. **Alpha is negative almost everywhere and measurable almost nowhere.** 82 of 109 US
   shrunk alphas are negative, median −0.89 pp/yr. Only **16 of 109** raw alphas exceed the
   alpha their own window could detect at 80% power, and **all sixteen are negative**. The
   median minimum detectable alpha across the 327 US fund-by-specification tests is
   **5.01 pp/yr**, against a true cross-sectional dispersion of about 1.25 — the window is
   blunter than the effect by a factor of four. Ex-US: median 3.23 pp/yr.
3. **The positive US shrunk alphas are one trade.** Twenty-seven are positive and the six
   largest are IWY, VONG, SCHG, IWF, MGK and VUG — every one a large-cap growth product,
   over a window in which large-cap growth beat the market. **Nothing here is alpha in the
   sense of skill**, and Experiment 002 said the same thing about the six it could see.
4. **The model itself has a measurable offset.** VTI *is* the market portfolio, so its
   alpha should be about minus its 3 bp fee; under FF5+UMD over these 72 months it is
   **−0.55 pp/yr (HAC *t* = −3.41)**. **Every alpha here is a distance from its pedestal,
   never from zero**, and a fund estimated on a shorter window is a distance from *that
   window's* pedestal, which runs from −0.26 on 46 months to −0.65 on 36.
5. **The regional panel is not a refinement; it decides the verdict.** Grading ex-US funds
   on the **US** panel instead of their own region's would put **16 of 25 below the 0.15
   bar rather than 5**, moving individual loadings by up to 0.480 — `IMFL` reads −0.258 on
   its own panel and +0.221 on the other. **An ex-US loading without its panel named is
   not a number.**
6. **Cost is what rejects a fund, the cost comparator is fitted in sample, and which
   funds were in the comparison was decided by a filing calendar.** See
   [§the corrected frame](#the-us-shelf-on-the-corrected-frame) and
   [§the comparator](#the-comparator-shrinkage-and-two-traps).

### What decided the rejections

| Clause | What it tests | US corrected | US 2019Q4 frame | Ex-US |
| --- | --- | ---: | ---: | ---: |
| (a) intended loading below 0.15 | the exposure is absent | 23 | 10 | 5 |
| (b) the loading flips sign across the fixed halves | the exposure is not an exposure | 6 | 1 | 1 |
| (c) shortfall to the cheap replication above 0.50 pp/yr | implementation value | **35** | **22** | **5** |
| (d) total cost above 1.0 pp/yr with no corresponding exposure | cost without exposure | 11 | 8 | 2 |

Clauses overlap. **Clause (c) still does most of the work, and it is decided against a
comparator fitted in sample.** Read every (c) rejection as *"a look-ahead combination of
cheap funds beat this product over these months"*, **never** as *"this product is badly
run"*. The clearest demonstration is `GWX`, which carries **the largest intended loading
in the entire ex-US audit at +0.856** and is rejected anyway.

**The reverse reading is the stronger one and it is new.** A *positive* shortfall against
a hindsight comparator is weak evidence against a product. A *negative* one is hard
evidence for it: the combination had the whole window to fit itself and still lost.
**Fifty-eight of 109 US products have a negative shortfall**, and among the funds the
corrected frame admits the median is −0.48 pp/yr.

---

## The US shelf on the corrected frame

### Why the frame was wrong, measured rather than asserted

Experiment 002 screened the census of every fund that filed a Form NPORT-P in the SEC's
**2019Q4** data set, and took its frame at the start of the window on the correct general
principle that screening today's listings selects on survival. What nobody checked is
what that file contains.

**Form N-PORT is filed on each series' own fiscal calendar, and public reporting begins
with periods ending 2019-09-30.** So the 2019Q4 data set carries fiscal quarters ending
**2019-09-30 (5,599 series) and 2019-10-31 (2,963)** and one stray November. It contains
**zero series with an August fiscal quarter-end**, against **2,507 in the 2025Q4 file**.

**A fund with an August fiscal year was therefore invisible to Experiment 002 whatever its
age.** That is the whole of Schwab's equity range (SCHG, SCHV, SCHA, SCHM), Vanguard's
ETF-only trusts (VONG, VONV, VOOG, VOOV, VIOO, VIOV, IVOO, IVOG, IVOV, VTWG, MGV, VFMO),
three of Invesco's factor products (SPMO, OMFL, QVML) and Avantis (AVUV, AVLV, AVSC) — 25 of the
49 passing series the 2019Q4 census does not carry. **It is a fact about the filer's
accounting year, not about the fund.**

The second cause is the one Experiment 009 named: **products that did not yet exist.**
Dimensional converted DFAT and DFAS into ETFs on 2021-06-14 and launched DFSV, DFLV
and DUHP in 2022; DFUV converted in 2022; Avantis listed AVUV on 2019-09-24. **At least 32
of the 72 funds the corrected screen passes and Experiment 002 did not began trading as
ETFs after its 2016-12-31 inception cutoff** — 25 of the 65 that also have enough filed
history to be audited, and every one of the seven excluded for a short window. The cutoff
would have removed all of them even had the frame carried them. Inside Experiment 002's
own frame that cutoff removed exactly one fund; **its real effect was latent and only the
corrected frame makes it visible.** The figure is "at least" because 18 of the added funds
carry no recorded inception date: they filed in the 2019Q4 census, so the screen no longer
needs one and none was gathered.

The third is smaller and is a property of reading an asset floor at a single date.
Twenty-two funds were in the 2019Q4 census and below $1bn *then* — DYNF at $0.06bn, now
$29.0bn; JQUA at $0.11bn, now $7.5bn. One more, FLQL, renamed *into* the mandate pattern.
The corrected screen reads the floor on the **maximum** of the two observed figures.

### What changed in the screen, and what did not

Two criteria move and they are the same change twice, recorded in the frozen
specification's `screen_changes_from_exp_002` block:

| | Experiment 002 | Experiment 013 |
| --- | --- | --- |
| Frame | 2019Q4 census alone, asset floor read at that date | **union of 2019Q4 and 2025Q4**, floor on the **maximum** of the two |
| Inception | on or before 2016-12-31 | **deleted**; replaced by ≥ 36 filed monthly returns at estimation time |

Everything else is byte-identical and asserted as such: both regexes, the exchange-traded
criterion, the $1bn floor, the 0.60% expense cap, the intended-factor map and every sign
in it, the four falsifier clauses and their thresholds, the VTI comparator and the
VTI/VUG/VTV/VB basis, the 2020-01…2025-12 window and both fixed halves, HAC at 6 lags, a
6-month mean block, 10,000 resamples and the seed.

**The check that makes "only the frame moved" a claim rather than an assurance:** every one
of Experiment 002's 44 funds is estimated here on the same 72 months, and the largest
difference in any of the six loadings is **0.0**, in any annual alpha **0.0**, in any
implementation shortfall **0.0**, and no shared fund's status changed. The screen is also
a strict superset — the 44 are a subset of the 116 — which a test enforces.

### The funnel: 3,169 to 116 to 109

| Stage | Removed | Remaining | What went |
| --- | ---: | ---: | --- |
| union census | — | 14,742 | every series filing NPORT-P in either quarter |
| mandate regex | 11,573 | **3,169** | everything naming no factor mandate |
| exclusion regex | 908 | 2,261 | international, global, income, dividend, bond, ESG, sector, leveraged, inverse |
| **exchange-traded** | **1,843** | **418** | open-end mutual funds with no listed share class |
| minimum net assets ($1bn on the max) | 292 | 126 | sub-billion ETFs |
| maximum expense ratio (0.60%) | 2 | 124 | PDP at 0.62% and FNX at 0.62% |
| mandate in the frozen map | 8 | **116** | four minimum-volatility products (USMV, SPLV, LGLV, FDLO), two whose objective changed inside the window (USMC, ILCG) and two on the MSCI-to-STOXX transition Experiment 002 classified as a change in kind (LRGF, SMLF) |
| at least 36 filed monthly returns | 7 | **109** | FELG, FELV, FESM and FMDE at 24 months, BSVO at 33, QLTY at 25, COWG at 19 |

**The minimum-volatility products are recorded and not graded, on purpose.** The corrected
frame admits USMV ($36.5bn) and SPLV ($7.9bn) for the first time, and neither claims any of
the six factors as its objective. Adding a mandate to the map after seeing which funds the
frame admits would be exactly the discretionary edit this experiment exists to avoid.

**Seven funds are excluded for a short window and none is rejected for it.** Four of the
seven are the Fidelity Enhanced conversions of November 2023 and one is the GMO quality
ETF; their absence is a statement about their age.

### What the corrected frame finds

Loading is sign-adjusted for the mandate, on each fund's own window. `α*` is shrunk and
decides nothing. `short` is positive when the product lost more to its cheap replication
than its fee premium explains. **`+` marks a fund Experiment 002's frame could not audit.**

**The systematic value and small-value shelf, which was entirely absent before:**

| Ticker | Mandate | ER % | Months | Loading | 95% interval | Raw α | α* | MDE₈₀ | Shortfall | Status |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- |
| **+AVSC** | small cap | 0.25 | 47 | **+1.058** | `[+0.98, +1.11]` | +0.62 | +0.34 | 3.14 | **−0.72** | `exploratory` |
| **+DFAS** | small cap | 0.26 | 54 | **+0.816** | `[+0.74, +0.91]` | −1.40 | −0.81 | 2.97 | **−1.16** | `exploratory` |
| **+RPV** | value | 0.35 | 72 | **+0.710** | `[+0.53, +0.83]` | −2.80 | −0.63 | 6.50 | **−0.95** | `exploratory` |
| **+DFLV** | value | 0.21 | 36 | **+0.637** | `[+0.42, +0.82]` | −6.06 | −1.67 | 5.69 | **−0.42** | `exploratory` |
| **+AVUV** | small-cap value | 0.25 | 72 | **+0.537** | `[+0.43, +0.64]` | +0.39 | +0.19 | 3.64 | **−4.92** | `exploratory` |
| **+DFUV** | value | 0.21 | 43 | **+0.515** | `[+0.35, +0.71]` | −2.06 | −0.64 | 5.21 | +0.11 | `exploratory` |
| **+DFSV** | small-cap value | 0.30 | 46 | **+0.442** | `[+0.34, +0.64]` | +0.45 | +0.15 | 4.84 | **−1.83** | `exploratory` |
| **+DFAT** | small-cap value | 0.28 | 54 | **+0.433** | `[+0.37, +0.55]` | +0.33 | +0.15 | 3.79 | **−3.44** | `exploratory` |
| **+AVLV** | value | 0.15 | 51 | **+0.322** | `[+0.22, +0.46]` | −0.92 | −0.28 | 5.28 | **−2.93** | `exploratory` |
| **+DUHP** | quality | 0.20 | 46 | +0.179 | `[+0.03, +0.29]` | −1.43 | −0.55 | 4.46 | −0.11 | `unresolved` |

**All nine graded on HML or SMB reach `exploratory`, not one fires any clause, and eight
of the nine beat their look-ahead cheap replication outright.** AVUV, which
Experiment 002's frame could not see, has 72 months of filed history — the full window —
an HML loading of +0.537 whose interval excludes 0.15 from below by a wide margin, and a
shortfall of **−4.92 pp/yr**. The best in-sample combination of VTI, VUG, VTV and VB,
fitted with the whole window in hand, could not get within five points a year of it.

**The one caveat that cuts against this, stated plainly.** The comparator basis is
Experiment 002's and contains **no small-value fund**: VBR is an audited product, not a
building block. A small-value product is therefore scored against a basis that cannot
express small value, and part of every negative shortfall in the table above is that
limitation rather than the manager. The basis was frozen before any of these funds was
visible, so this is not a choice made to favour them — but it is a reason to read the
magnitudes as *"cheap broad funds could not do this"* rather than *"nothing could"*.

**What the corrected frame does to the two headline counts:**

| | Experiment 002's 44 | The 65 added | All 109 |
| --- | ---: | ---: | ---: |
| Median intended loading | +0.302 | +0.310 | +0.303 |
| Loadings ≥ 0.40 | 12 | **21** | 33 |
| Median implementation shortfall | **+0.53** | **−0.48** | −0.07 |
| Clause (c) fired | **22 (50%)** | **13 (20%)** | 35 (32%) |
| Reached `exploratory` | 15 (34%) | **33 (51%)** | 48 (44%) |

The loadings are not systematically larger in the added set; **the cost verdict is what
moves.** The funds Experiment 002 could see lost to their replications at the median and
the funds it could not see beat theirs.

### Alpha is exactly as unmeasurable as it was

The frame correction buys nothing here and was never going to.

- **Median MDE₈₀ across the 327 fund-by-specification alpha tests: 5.01 pp/yr**, against a
  cross-sectional dispersion of true gross alpha of about 1.25. On the primary
  specification alone the median is 4.04. **The instrument is blunter than the effect by a
  factor of four.**
- **Sixteen of 109 raw alphas exceed their own detection threshold. All sixteen are
  negative** — DFLV, IJR, IJT, IMCB, IWD, IWN, IWS, JHML, SCHA, SCHM, SCHV, SLYG, SPSM,
  VIOO, VOE, VONV. Not one positive alpha anywhere on the corrected shelf is large enough
  for its own window to have found it.
- **AVUV's alpha is +0.39 pp/yr against an MDE₈₀ of 3.64.** It is an unmeasured quantity
  and must be read as one. Its *loading* is measured; its *residual* is not.
- **The pedestal now travels with the window.** VTI's own alpha over the full 72 months is
  −0.547 pp/yr; over the shorter windows the added funds are estimated on it ranges from
  −0.258 (46 months) to −0.654 (36 months). Comparing a 46-month fund's alpha against the
  72-month pedestal would compare two different quantities, so each fund carries the
  pedestal for exactly its own months.

| Correction | Rejections of 327 |
| --- | ---: |
| Uncorrected at 0.05 | 96 |
| **Benjamini–Hochberg at 0.10** | **58** |
| **Holm–Bonferroni** | **5** |
| BH, family padded to every mandate-matching series × 3 = 9,507 | 3 |
| Holm, padded family | **0** |

**BH assumes independence and this family has less of it than Experiment 002's did.**
Eleven index families are tracked by two or three audited funds each, covering 29 funds:
IJR, SPSM and VIOO all track the S&P SmallCap 600 and their loadings agree to 0.001, as do
IJH/IVOO/SPMD, IVW/SPYG/VOOG, IVE/SPYV/VOOV, IJK/IVOG/MDYG, IJJ/IVOV/MDYV and
IJS/SLYV/VIOV. **The BH count is an optimistic bound and Holm is the defensible one.**

Holm still leaves five tests of the 327, against five of 132 before, and the composition
makes the dependence concrete: **IJR, SPSM and VIOO are one index sold three times**, and
IWS appears twice under two specifications. So the five surviving tests are three
products, one of which is a single index in triplicate — and the corrected frame added a
survivor (VIOO) that carries no information the frame already had.

**Exposure is the family that survives.** The intended-loading tests are a separate
109-member family: 94 reject uncorrected and **96 under Benjamini–Hochberg**. **That
asymmetry — 96 of 109 loadings against 5 of 327 alphas under a defensible correction — is
still the whole result in two numbers**, and the corrected frame makes it sharper rather
than weaker.

### What the corrected US shelf actually contains

Every audited product, by its declared mandate, with the funds Experiment 002's frame
could not see marked `+`.

| Mandate | Products | New | `exploratory` | `rejected` | `unresolved` |
| --- | ---: | ---: | ---: | ---: | ---: |
| value | 22 | 15 | **14** | 7 | 1 |
| growth | 19 | 11 | 9 | 5 | 5 |
| small cap | 11 | 8 | 7 | 4 | — |
| mid cap | 9 | 4 | 5 | 4 | — |
| small-cap value | 9 | 5 | 5 | 3 | 1 |
| **quality** | 9 | 7 | **0** | 5 | 4 |
| multifactor | 8 | 6 | 1 | 6 | 1 |
| **momentum** | 6 | 5 | **4** | 1 | 1 |
| mid-cap growth | 6 | 2 | **0** | 6 | — |
| small-cap growth | 5 | 1 | **0** | 5 | — |
| mid-cap value | 5 | 1 | 3 | 2 | — |

Three of these rows are findings in their own right.

- **Quality is nine products and none of them delivers.** Five fire clause (a) or (c) and
  four are `unresolved` with intervals straddling 0.15. The largest RMW loading on the
  whole US shelf is XMHQ's +0.228 on an interval of `[+0.03, +0.48]`. **A quality tilt is
  not purchasable on this shelf at this threshold**, and Experiment 002 saw two of these
  nine.
- **Every mid-cap-growth and small-cap-growth product is rejected, all eleven of them.**
  Their sign-adjusted loadings run from −0.068 to +0.168, meaning several carry a
  *positive* raw HML loading while being sold as growth. That is the exposure-delivery
  failure clause (a) exists to catch, it was visible in Experiment 002 on four funds, and
  the corrected frame finds it on eleven.
- **Momentum went from one product to six.** MTUM was the entire US momentum shelf
  clearing a $1bn, 0.60% screen and it was rejected on cost. SPMO, XSMO, XMMO and VFMO
  now reach `exploratory` with loadings of +0.414, +0.413, +0.462 and +0.372 and
  shortfalls of −4.53, −2.49, −3.85 and −3.44. **The claim that a momentum proxy does not
  exist was a claim about the frame.**

### Where clause (b) fires, and why it means nothing here

Clause (b) fired six times: FTC, IMCG, QGRO, DSTL, DYNF and OMFL. **Every one of the six
has an intended loading of +0.17 or less**, five of them under +0.09, so the sign that
flipped belongs to a quantity indistinguishable from zero. Clause (b) is catching the
absence of an exposure, which clause (a) has already caught in five of the six cases.

**Clause (b) was evaluated only where a fund covers both fixed halves in full**, which is
the situation Experiment 002 was always in because every fund it audited had all 72
months. A fund covering part of a half has clause (b) recorded as *not evaluable*, never
as passed and never as fired: a loading estimated on nine months can change sign on noise
alone, and the frozen falsifier says in terms that no fund is rejected for the shortness
of a window it did not choose.

---

## The US shelf as Experiment 002 framed it

**Everything below is Experiment 002 and it is reproduced here exactly by Experiment 013.**
It is kept because the comparator, the falsifier and the traps are stated here first and
because it is the record of what a 2019Q4 frame sees. Read every count in this section as
*"of the 44 products that census carried"*, not as *"of the US shelf"*.

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
is the entire momentum shelf clearing a billion dollars and a 0.60% fee **inside this
frame**; the corrected frame carries six momentum products.

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
2019, so a fund that closed earlier is invisible to both censuses. Experiment 013
recomputes the same decomposition from its own union frame and reaches the same 312 and
$138.7bn, with 699 mandate-qualifying series launched inside the window and 52 renamed
into the pattern. **None of the audited funds is absent at follow-up, which is true by
construction** — 36 months of filed returns are required to enter the panel, and a fund
that stopped filing before 2023 cannot have them.

**The union frame does not weaken this.** A frame taken at the *end* of the window would
have dropped the 312 dead series entirely; the union retains every one of them and
screens them, so the attrition remains measurable. That is the property Experiment 002's
start-of-window frame was protecting, and a test enforces that the union still carries
series present in 2019Q4 and absent in 2025Q4.

---

## Hostile tests: what ran, and what was wrong on the way

| Declared test | Experiment 002 | Experiment 013 |
| --- | --- | --- |
| Re-estimate under CAPM, FF3 and FF5+UMD and report all three | **Run.** 132 fits | **Run.** 327 fits |
| Fixed calendar halves and rolling 36-month windows | **Run.** 37 windows per fund | **Run**, and reported as not evaluable where a fund's window cannot support it |
| Substitute DGS3MO and DFF for TB3MS | **Run.** Wrong in the first two successful runs; fixed | Not repeated: a constant shift in the dependent variable moves only the intercept, and 002 measured it at ≤ 0.20 pp/yr with every loading invariant |
| Every screened fund and specification in the denominator | **Run.** 6,315-member padded family | **Run.** 9,507-member padded family; BH 3, Holm 0 |
| Assert Experiment 002's screen unchanged before running | n/a | **Run**, and enforced by a test that fails if either regex moves |
| Report the pedestal on each fund's own window | Not designed | **Run.** Fourteen distinct windows, −0.26 to −0.65 pp/yr |
| Decompose the added funds by *why* the old frame missed them | n/a | **Run.** 42 absent from the 2019Q4 census, 23 excluded by a criterion that moved |
| **Cross-check every N-PORT return against an independent source** | **Did not run at all** | **Did not run at all** |
| Report MDE₈₀ beside every alpha | **Run** | **Run**, with the minimum detectable *loading* beside every loading |
| Measure attrition between the censuses | **Run**, with the defect above | **Run**, with renames separated from deaths |

**The cross-source check produced nothing, three times.** All 44 US, all 25 ex-US and all
109 corrected-frame tickers are in the `unavailable` list with `HTTPError` and the
`compared` list is empty. **Form N-PORT Item
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

**Verified.** Each screen was frozen, mechanical and applied before any return was
downloaded; returns were never fetched for a fund that failed it, so **no screen decision
could be revised after seeing performance**, and all 2,105 mandate-matching series in
Experiment 002 and all 3,169 in Experiment 013 are committed with their outcome and first
failing criterion. The Item B.5 month alignment is checked, not assumed, on the same
comparator and the same months in both. All 44 of Experiment 002's funds have 72 of 72
months; Experiment 013's windows run from 36 to 72 and every estimate carries its own
count. The expense ratio is **not** subtracted twice — Item B.5 is already net. Every
excess return is taken over the rate `Mkt-RF` is defined against. Both French files are
pinned by raw sha256 and a new vintage aborts the run. The HML/RMW volatility band does
**not** propagate here: every figure is a loading, a mean or a difference of means, and
nothing divides by those volatilities. Experiment 002's two regexes were asserted
byte-for-byte before Experiments 009 and 013 ran, and Experiment 013 reproduces every one
of Experiment 002's 44 funds to zero difference.

**Assumptions.** `sigma_true = 1.25%/yr` is *transferred, not measured* — it comes from a
bootstrap of US active mutual funds over 1984–2006 and is applied to index-tracking ETFs
over 2020–2025, and it decides every shrunk number here. The intended-factor map is a
declaration written before any regression, so no fund could be graded against whichever
loading turned out largest. The thresholds are a priori and none is tuned. Benjamini–
Hochberg treats the tests as independent and they are not. **Every figure is PRETAX**, and
bid-ask spreads, brokerage, realised distributions and portfolio turnover are absent
entirely. **Experiment 013's mandate assignments are the one genuinely new judgement**: 79
funds needed a mandate from the frozen eleven-value vocabulary, taken from each fund's own
filed objective by an ordered rule committed with the facts, before any return was read.
Four funds name two of the map's factors and are graded on the one they name first, which
is the rule Experiment 002's own map note states in words. Two, LRGF and SMLF, are given
the reserved `mandate_changed` because Experiment 002 classified the identical MSCI-to-STOXX
transition that way for INTF and Experiment 009 carried it to three more funds.

**Open.**

1. **How much of the remaining median alpha is still model misfit?** The pedestal measures
   the misfit a fund with *market* exposure carries, and Experiment 013 now measures it on
   each fund's own window. A small-cap value fund is still not the market, and **a pedestal
   per style does not exist**.
2. **Does any N-PORT return agree with an independent measurement?** Unanswered for all
   134 funds across the three experiments. Experiment 013's cross-source check refused for
   **109 of 109** tickers, exactly as its two predecessors did.
3. **What do realised distributions and turnover do to the cost ranking?** Neither is in
   N-PORT; both are in N-CSR as unstructured HTML. **Clause (d) is evaluated without the
   distribution term the falsifier names.**
4. **Would an out-of-sample replication change clause (c)?** Weights fitted on a prior
   window would remove the look-ahead. Not runnable on 72 months without shortening the
   estimation window further, and **this is now the single most load-bearing open
   question on the page**: clause (c) is what separates the 48 `exploratory` products
   from the 48 rejected ones, and the funds with the largest negative shortfalls are
   scored against a basis with no small-value member.
5. **What is a fund's delivered *capture*, as opposed to its loading?** Every capture
   figure here is from research portfolios. Measuring a fund's own needs **holdings rather
   than returns** — which N-PORT carries and no experiment has read.

## What this does not establish

- **Not skill, in any direction.** Twenty-seven positive US shrunk alphas, the six
  largest all large-cap growth, **not one of them exceeding its own detection threshold**,
  all measured against a model that charges the market portfolio itself −0.55 pp/yr.
- **Not investable cost.** Nothing here is a net-of-everything return.
- **Not a survivorship-free universe.** The measured attrition is a lower bound.
- **Not audited data.** Item B.5 returns are fund-reported and unaudited, and General
  Instruction G lets each filer use its own methodology, so two funds' returns are not
  guaranteed to be computed identically. With the cross-source check dead, that assumption
  is untested.
- **Not the whole shelf.** Exchange-traded only, above an asset floor, below an expense
  cap. The inception cutoff is gone, but seven funds are still absent for having fewer
  than 36 filed months, and a fund that closed before 2019 is invisible to both censuses.
- **Not a vindication of the products, either.** A negative shortfall says a look-ahead
  combination of four cheap funds could not match a product over 72 months or fewer. It
  does not say the product will do it again, and the residual that would have to be real
  for that is exactly the quantity this window cannot measure.
- **Not a return finding.** Where a product's shortfall is really the realised style return
  of 2020–2025, this page is measuring the window, not the product.

**The binding constraint is the data contract and the length of the window, not the
evidence.** Form N-PORT is a materially stronger contract than any price feed decision 0002
tested, and it is still not enough to promote anything.

---

## Consequence for this repository

1. **Nothing is promoted, and decision 0002 is not the only reason.** Even with a licensed
   source, no product here would qualify: the alpha column is unmeasurable, and the cost
   comparison that decides most rejections is a look-ahead comparator.
   **What has changed is that the shortlist a promotion attempt would start from is no
   longer fifteen index trackers.** Forty-eight US products reach `exploratory`, and the
   ones with the largest delivered loadings are the systematic value and small-value
   products Experiment 002's frame could not see.
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
5. **The edge budget's fund-cost line survives, and its supporting statistic does not.**
   It books 49 bp against an investor's own counterfactual, untouched here. What this page
   used to add was *"for most of this shelf the gap to a cheap replication is larger than
   the fee"*, on 22 of 44. **On the corrected frame that is a minority: 35 of 109, and 13
   of the 65 funds the frame correction admits.** The general point stands — a fee
   comparison is not a cost comparison, and the largest shortfalls are five to a hundred
   times any fee difference — but it must not be quoted as a property of the shelf.
6. **The listed factor shelf is thicker than this page said, and more duplicated.** The US
   shelf carries 109 auditable products, not 44. Eleven index families are sold two or
   three times over, covering 29 of them, so the count of *products* still overstates the
   count of *choices*. **Momentum is no longer one fund**: it has six — MTUM, SPMO, XSMO,
   XMMO, VFMO and JMOM — five of them new to the audit and four reaching `exploratory`,
   where MTUM alone was rejected. **Quality went the other way**: nine products, and not
   one reaches `exploratory`. On the ex-US side, four emerging products in total, and
   that has not moved.
7. **A frame is a result.** Experiment 002's numbers were right and its conclusion was a
   property of which funds a filing calendar let it see. Any future screen against a
   quarterly regulatory census states which fiscal quarter-ends that census carries,
   before it reports a count.

## Reproduce it

```sh
cd research
uv run python -m portfolio_edge.experiments.exp_013_us_products_union_frame --build-universe
uv run python -m portfolio_edge.experiments.exp_013_us_products_union_frame --view-results
uv run python -m portfolio_edge.experiments.exp_002_fund_exposure --view-results
uv run python -m portfolio_edge.experiments.exp_009_exus_products --view-results
uv run pytest tests/unit/test_experiments_exp_013_us_products_union_frame.py
uv run pytest tests/integration/test_exp_013_universe_committed.py
```

| | Experiment 002 | Experiment 009 | Experiment 013 |
| --- | --- | --- | --- |
| Specification | `exp_002_fund_exposure.yaml`, `b4c9a134e106…` | `exp_009_exus_factor_products.yaml`, `e99e2a6e27…` | `exp_013_us_products_union_frame.yaml`, `79f4e7628a3a…` |
| Run reported | `fbe139abd9114abeb69e39fad8839f8e` | `f6ce1701324546b28c03598c935b7819` | `2b8cc7f73aef4d8abee68b7abcde9c1c` |
| Other ledgered runs | 1 `failed`, 3 `abandoned`, 2 superseded `succeeded` | 2 earlier `succeeded`, 1 `failed` on a non-JSON-compliant `NaN` | 1 `abandoned` before any return was read, 1 superseded `succeeded` |
| Seed | 20260812 | 20260812 | 20260812 |

**Experiment 013's two non-reported runs are both recorded and both are worth reading.**
The `abandoned` one was killed during its download phase, before any return existed,
because the committed product facts carried a tracked index for several funds that track
none — an artefact of the mechanical fee harvester, read by no criterion and by no
estimate, but committed and therefore quotable. It was corrected and the universe rebuilt
**before** any return was read. The superseded `succeeded` run is identical except that
two funds, DYNF and VONV, were dropped by an HTTP 503 from EDGAR; their filings were
fetched and the run repeated. **Every figure the two runs share is identical to zero
difference**, and the difference between them is two funds, one of which — VONV at
$15.0bn — is a `rejected` (c) product whose absence would have flattered the corrected
frame's counts.

The universe and the per-fund facts were committed **before any return was downloaded**,
each fee with the SEC filing it was read from, the form, the filing date and the date
read. **Every one of the 79 new fees was then re-fetched from its cited document and
checked against it**; all 79 verified. Every run's git commit, working-tree diff hash,
dataset-manifest hashes, artifact hashes and `results_viewed` event is in
[`research/ledger.jsonl`](../../research/ledger.jsonl).
