# Ex-US factor products: the shelf where the premium actually is

**Question.** [Experiment 002](factor-product-audit.md) audited the US factor shelf.
[Experiments 005](factor-persistence.md#experiment-005--the-regional-replication) and
[007](long-only-capture.md) then located essentially all of the value premium's
measurable weight **outside** the United States. So this repository had audited
products where the premium is weakest and audited none where it is strongest. Do
ex-US factor products deliver the exposure they advertise, against **their own
region's** factor panel, at a cost that leaves the exposure worth buying?

**Decision it informs.** Whether an ex-US or emerging factor sleeve has an
implementation at all, and what the recommendation page may say about one. Out of
scope: whether any factor premium is real — that is
[factor persistence](factor-persistence.md) — and alpha, which windows beginning in
2019 cannot identify and which nothing here claims.

**Status: `exploratory`, by decision and not by outcome.**
[Decision 0002](../decisions/0002-no-research-grade-free-price-source.md) caps all
fund-level work there, and the window caps it again. This may not promote a sleeve and
may not appear in the application as a finding.

## Conclusion

**The exposure is delivered, and the shelf is the constraint.**

Of 537 region-and-factor matching series screened from the union of the 2019Q4 and
2025Q4 N-PORT censuses, **26 passed the predeclared screen and 25 had at least 36
filed monthly returns**. Of those 25: **12 reached `exploratory`, 8 were `rejected` on
the frozen falsifier, and 5 are `unresolved`**. Median usable history is **76 months**,
against Experiment 002's uniform 72 — so the ex-US window is not the shorter one, which
was the expected objection and it does not hold.

Three findings, in descending order of how much they change other pages.

1. **The regional panel is not a refinement; it decides the verdict.** Grading these
   funds on the **US** factor panel instead of their own region's would put **16 of 25
   below the 0.15 loading bar rather than 5**. Against the *other* ex-US region's panel
   the intended loading moves by a median of **0.151** and by as much as **0.480**:
   three of the five clause-(a) rejections would vanish and two funds that clear the
   bar would fail instead. A published ex-US loading without its panel named is not a
   number.
2. **Cost, not exposure, is what rejects a fund here — exactly as in the US audit.**
   Clause (c) fired on 5 of the 8 rejections: the fund lost more to an in-sample fitted
   combination of cheap ex-US funds than its fee premium over that combination
   explains, by more than 0.50 pp/yr. The other three failed clause (a) on a loading
   below 0.15, and two funds failed both.
3. **The withholding drag could not be bounded, and the honest reading is that the
   method failed rather than that the drag is small.** VEA beat its own region's French
   market portfolio by 0.517 pp/yr beyond its fee while VTI *trailed* the US one by
   0.349, a difference of **+0.866 pp/yr in the wrong direction**. A negative difference
   would have been an upper bound on the ex-US structural drag; a positive one means
   index-construction differences swamp whatever withholding costs and **the method
   cannot bound the tax at all**. Withholding is certainly being paid, is inside every
   ex-US return here, and is simply not separable from the benchmark mismatch by this
   construction.

All figures `as of 2026-08-12`.

## What was run

| Field | Value |
| --- | --- |
| Specification | [`research/experiments/exp_009_exus_factor_products.yaml`](../../research/experiments/exp_009_exus_factor_products.yaml), hash `e99e2a6e27…` |
| Run kind | **exploratory**; does not consume the final holdout |
| Ledger `run_id` | `f6ce1701…` (quoted here); `e7c4b0d6…` and `46d51d99…` are earlier executions of the same specification, and `9ec0f164…` is ledgered `failed` on a `NaN` that is not JSON-compliant |
| Frame | The **union** of the 2019Q4 and 2025Q4 N-PORT censuses, as in Experiment 008 and unlike Experiment 002 |
| Sample | 2019-07 to 2025-12, each fund evaluated on the intersection with its own filed coverage; nothing after 2025-12 is downloaded |
| Panels | Ken French Developed ex-US and Emerging FF5 + momentum, in USD, per region; the US panel is used for the VTI pedestal alone |
| Comparators | VEA (developed ex-US), VWO (emerging), VTI (US pedestal), and a constrained-least-squares combination of VEA, VWO, VSS, EFV and EFG excluding the fund itself |
| Inference | Stationary block bootstrap, mean block **6 months frozen not tuned** (3 and 12 as predeclared neighbours), 10,000 resamples, HAC standard errors at 6 lags |
| Seed | 20260812 |

**Experiment 002's screen was not modified; it was complemented.** The two regexes in
`exp_002_fund_exposure.yaml` are asserted byte-for-byte before this experiment runs and
it aborts if either has moved, so *"no previously published US result changed"* is a
checked claim rather than an assurance. The two screens are complements over the same
census: a fund can appear in at most one of them.

**The frame is a union for a reason that would otherwise select the answer.**
Experiment 002 could take its frame at the start of its window because every fund it
audited already existed in 2019. Here that is false for exactly the products the
question is about — AVDV launched 2019-09; AVIV, AVES and DISV in 2021-09; DFIV in
2021-11; DFEV in 2022. A 2019Q4-only frame would have excluded them by construction.

### The screen, in the order it was applied

Criteria are applied in the frozen order below and each series is recorded against the
**first** one it failed, because the multiple-testing denominator is the whole screen.

| First criterion failed | Series |
| --- | ---: |
| Exclusion pattern (sector, hedged, dividend, leveraged, single-country, …) | 68 |
| US overlap | 99 |
| Not exchange-traded | 289 |
| Below the $500m asset floor | 46 |
| Mandate not in the frozen map (mostly minimum-volatility) | 4 |
| Region not in the frozen map (`world_ex_us`) | 1 |
| Above the 0.60% expense cap | 1 |
| Mandate not stable across the two censuses | 3 |
| **Passed** | **26** |

The asset floor is **half of Experiment 002's**, chosen from the *count* of qualifying
series visible in the census before any return was downloaded and never from
performance: at Experiment 002's $1bn floor the ex-US screen returns 23 series and at
$500m it returns 39. One of the questions is whether the shelf is deep enough to
matter, and using the US floor would have answered it by assumption.

The frozen falsifier rejects a fund when any of: **(a)** its intended loading in its
own region's FF5+UMD panel is below **0.15**; **(b)** that loading's sign flips between
the two fixed calendar halves, where both are covered; **(c)** its tracking difference
against the fitted cheap combination is worse than its fee premium over that
combination by more than **0.50 pp/yr**; or **(d)** its total cost of ownership exceeds
**1.0 pp/yr** above the regional comparator without a corresponding exposure. A fund is
`unresolved` when no clause fires but the 95% interval on its intended loading contains
0.15. **A t-statistic on residual alpha is not a falsifier in either direction**, and
**short history is a finding**: a fund whose filed history cannot detect its own
intended loading is reported with its sample length and its minimum detectable effect,
never rejected for the shortness of a window it did not choose.

## The 25 funds

Loading is on the intended factor in the fund's **own** region's panel, over its own
filed window. `alpha*` is the shrunk annual alpha, and it decides nothing.

### `exploratory` — the exposure is delivered

| Ticker | Region | Factor | Loading | 95% interval | Months | `alpha*` |
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

Every one is developed ex-US. **No emerging-market product reached `exploratory`.**

### `unresolved` — the interval contains the bar

| Ticker | Region | Factor | Loading | 95% interval | Months |
| --- | --- | --- | ---: | --- | ---: |
| IDHQ | developed ex-US | RMW | 0.321 | `[0.10, 0.52]` | 77 |
| DFEV | emerging | HML | 0.267 | `[0.08, 0.44]` | 44 |
| AVES | emerging | HML | 0.237 | `[0.12, 0.37]` | 51 |
| TLTD | developed ex-US | HML | 0.205 | `[0.13, 0.27]` | 77 |
| IQLT | developed ex-US | RMW | 0.184 | `[−0.04, 0.39]` | 77 |

**Both emerging value products are here**, and neither is `unresolved` because it
failed: their point estimates are positive and their windows are 44 and 51 months. This
is the status the specification predicted a short window would produce.

### `rejected` — and what actually rejected them

| Ticker | Loading | Clauses fired |
| --- | ---: | --- |
| EFG | 0.435 | **(c)** lost 2.76 pp/yr to its cheap replication |
| GWX | 0.856 | **(c)** lost 1.61 pp/yr |
| DIHP | 0.347 | **(c)** lost 1.23 pp/yr |
| RODM | 0.055 | **(a)**, **(c)** lost 1.47 pp/yr, **(d)** total cost 1.76 pp/yr |
| IMFL | −0.258 | **(a)**, **(c)** lost 1.14 pp/yr, **(d)** total cost 1.48 pp/yr |
| JHMD | 0.089 | **(a)**, **(b)** sign flips between halves (−0.013 then +0.13) |
| JHEM | 0.054 | **(a)** |
| MFEM | 0.117 | **(a)** |

**Read every clause-(c) rejection as "a look-ahead combination of five cheap ex-US
funds beat this product over these months", never as "this product is badly run."** The
replicating weights are fitted **in sample**, so the comparison is a best case for the
replication and a deliberately hard test for the product. The basis includes the two
cheapest broad ex-US *style* funds — EFV at 33 bp rather than VTV at 3 bp — because a
tilt is only worth what it beats, and on this shelf the thing to beat is a style fund.

Note that **GWX carries the largest intended loading in the whole audit, 0.856, and is
still rejected.** Exposure delivery and implementation value are different questions,
and this shelf separates them cleanly.

## The finding that decides how any of this may be quoted: the panel

Each fund's intended loading, estimated three ways on the same months.

| Panel used | Funds below the 0.15 bar | Median move from the correct panel |
| --- | ---: | ---: |
| **Its own region's** (as frozen) | **5 of 25** | — |
| The *other* ex-US region's | 4 of 25 | **0.151** |
| The **US** panel | **16 of 25** | — |

The individual moves are large enough to reverse verdicts rather than shade them.
`IMFL` reads **−0.258** on its own panel and **+0.221** on the other one; `IMTM` reads
0.505 against 0.112; `IDMO` 0.540 against 0.210; `GWX` 0.856 against 0.516. Regressing
an EAFE value fund on the US panel prices it against the wrong market, the wrong size
spread and the wrong value spread, and manufactures a loading or destroys one depending
only on how the two regions happened to co-move.

This is why the specification froze the regional panel as primary, and it is the single
most transferable result on this page: **any ex-US factor loading quoted anywhere in
this repository must name the panel it was estimated on.**

## The pedestals, and the drag that could not be measured

A cap-weighted market fund *is* its region's market portfolio, so its alpha under a
correctly specified model should be about minus its expense ratio. The distance from
that is model misfit shared by every fund in the region. **Read each fund's alpha as a
distance from its pedestal, never from zero.**

| Region | Comparator | Fee | FF5+UMD pedestal alpha | Market beta | R² |
| --- | --- | ---: | ---: | ---: | ---: |
| Developed ex-US | VEA | 0.03% | **−0.31 pp/yr** | 1.048 | 0.990 |
| Emerging | VWO | 0.06% | **+1.50 pp/yr** | 0.935 | 0.970 |
| US (Experiment 002's pedestal, re-estimated on these months) | VTI | 0.03% | −0.49 pp/yr | 0.996 | 0.998 |

The emerging pedestal is the more useful of the two, and it is uncomfortable: the model
misprices a cap-weighted emerging index fund by +1.50 pp/yr, so every emerging alpha in
this experiment carries at least that much misfit. That is one more reason no emerging
product could reach `exploratory` on anything alpha-shaped, and the falsifier
deliberately does not use alpha in either direction.

Three regional validation gates were frozen and all three passed: VEA against the
developed-ex-US market at beta 1.048 and R² 0.988 against a 0.93 floor; VWO at beta
0.973 and R² 0.963; VTI at beta 0.996 and R² 0.998. **The regional gates are looser than
the US one on purpose** — the French international files are built from a different
vintage than the US file, their second moments were never gated against any printed
table, and their dividend-tax treatment is undocumented. Every ex-US loading here
inherits that.

## What the shelf actually contains

The 26 products that passed the screen, by exposure and region (JIVE passed but filed
fewer than 36 usable months, so 25 reached the audit):

| Exposure | Developed ex-US | Emerging |
| --- | ---: | ---: |
| Value | 5 | 2 |
| Small cap | 5 | — |
| Small-cap value | 2 | — |
| Multifactor | 4 | 2 |
| Quality | 3 | — |
| Momentum | 2 | — |
| Growth | 1 | — |

**Emerging markets — where Experiment 005 measured the largest value premium — has
four products in total, two of which are rejected and two of which are unresolved.**
That is the concentration risk the specification's mechanism section predicted:
an exposure may exist in only one product at any price, which is not a choice.

Attrition over the window, on the decomposition that separates a death from a rename:
**88 of 322 qualifying ex-US series in the 2019Q4 frame were absent from the 2025Q4
census — 27.3%, holding $19.5bn** — against a naive rate of 32.3% that counts renames as
deaths. Both are **lower bounds**: public N-PORT filings begin in 2019, so a fund that
closed earlier is invisible to both censuses.

**This experiment also corrects a published Experiment 002 diagnostic.** Applying the
same death-versus-rename decomposition to Experiment 002's own patterns gives **312 of
1,513 series absent, 20.6%, holding $138.7bn**, against that artifact's headline of
358 series and $333.5bn, which counted renames as deaths. The corrected figure is the
one the [framework](portfolio-edge-research-framework.md) already carries. **No US
result changed**; only that diagnostic did.

## Verified, assumed, open

**Verified in this experiment.** That the intended loading is delivered by 12 ex-US
products against their own regional panels, with intervals excluding 0.15 from below.
That the panel choice moves a loading by a median 0.151 and up to 0.480, and moves the
count below the bar from 5 to 16 when the US panel is substituted. That Experiment
002's screening regexes are unchanged, asserted byte-for-byte at run time.

**Assumptions and known limits.**

- **Windows are unequal**, 27 to 78 months, so a cross-fund comparison of alphas is a
  comparison of differently powered estimates. The **median minimum detectable alpha at
  80% power is 3.23 pp/yr**, larger than any plausible true alpha. That is the whole
  reason alpha is not a falsifier here.
- **Every return is net of foreign dividend withholding**, deducted before net asset
  value is struck and not recoverable inside the fund. N-PORT carries no
  foreign-tax-paid figure. A taxable US shareholder may recover part of it through the
  foreign tax credit; a retirement-account shareholder may not. **Neither case is
  modelled**, which matters for [where an international sleeve belongs](portfolio-recommendation.md#3-account-placement-worked-through).
- **The tracking difference is against a constructed benchmark**, never against a
  fund's own stated index, because index levels are licensed and no free source with a
  documented contract carries them.
- **Item B.5 returns are fund-reported and unaudited**, and General Instruction G lets
  each filer use its own methodology. The intended cross-check against a free price
  endpoint returned an HTTP error for **all 25 tickers**, so no independent
  corroboration of any return exists here. No result depends on it, and that is by
  design rather than by luck.
- **Portfolio turnover, realised taxable distributions and the split between income
  and capital gain are all unavailable** from this source and are recorded as gaps. No
  constant tax haircut is applied to any return under any circumstances.

**Open.**

1. **Whether any of these funds is worth holding**, which needs the whole of
   `premium × delivered loading × capture − cost` and a licensed total-return source
   this repository does not have.
2. **What a fund's delivered *capture* is**, as opposed to its loading. Every capture
   figure in this repository is from research portfolios
   ([Exp 007](long-only-capture.md)); measuring a fund's own needs holdings rather than
   returns.
3. **Whether the emerging shelf is investable at all.** Four products, two rejected,
   two unresolved on 44- and 51-month windows.

**Reproducibility.**
`cd research && uv run python -m portfolio_edge.experiments.exp_009_exus_products --view-results`.
Source vintages are pinned by sha256 in the specification and a mismatch aborts;
manifests are committed under `research/data-manifests/`. Retrieval date for every
Ken French file: **2026-08-12**. Seed 20260812.

## Consequence for this repository

1. **The largest evidence gap [the recommendation page](portfolio-recommendation.md)
   named is now closed as a gap and re-opened as a cost problem.** The premium's weight
   is ex-US; ex-US products *do* deliver the exposure; and the ones that fail, fail on
   what a cheap combination of broad funds would have delivered instead.
2. **Any ex-US factor loading must name its panel.** A loading estimated on the US
   panel is a different quantity, and on this evidence it is wrong by enough to reverse
   eleven verdicts.
3. **Nothing is promoted, and nothing here can be.**
   [Decision 0002](../decisions/0002-no-research-grade-free-price-source.md) caps
   fund-level work at `exploratory` and
   [decision 0004](../decisions/0004-no-sleeve-promoted.md) stands in full. The twelve
   `exploratory` products may be used as implementation proxies in a later experiment
   and for nothing else.
4. **The ex-US structural drag remains unmeasured**, and the pedestal method is now
   known not to be able to measure it. Anything that needs it needs Form N-CSR or a
   1099-DIV, not N-PORT.
