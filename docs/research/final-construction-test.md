# The final construction, tested as one object

**Question.** Three gaps, and they turn out to have one answer. First: every result behind
the recommended portfolio is component-level, and the construction tournament scored the
investor's *original* eight-fund proposal rather than this one — does the recommended
construction beat a leverage-matched cheap index, and does it beat the alternatives it was
chosen over? Second: the shelf quoted fees where net costs belong, and Form N-CEN carries
the missing term — does reading it change the VTV call? Third: two products were named as
the right way to revisit US value and US momentum and neither was ever priced — what are
RPV and SPMO worth?

**Decision it informs.** Whether to keep RSST 25% / VTI 24% / VTV 15% / VXUS 16% /
AVDV 10% / IDMO 5% / AVES 5% as it stands, and which of four named substitutions would
improve it.

**Out of scope.** The trend weight ([tournament](construction-tournament.md) finding 6 and
[trend weight](trend-weight-under-uncertainty.md)), whether any factor premium exists
([factor persistence](factor-persistence.md)), and the weights themselves
([the recommendation](portfolio-recommendation.md), which this page does not edit).

> **"Recommended" on this page means the 25% arm, and the published recommendation is
> now 30%.** Experiment 016e's specification was frozen while the recommendation stood at
> RSST 25% / VTI 24%, and every arm here named `recommended` carries those weights. §1's
> own resolved head-to-head is then what moved the weight: the published construction is
> **RSST 30% / VTI 19% / VTV 15% / VXUS 16% / AVDV 10% / IDMO 5% / AVES 5%**, derived in
> [part A](portfolio-for-one-investor.md) §2 and rendered on `/portfolio`. The five points
> come out of VTI and go into trend; nothing else changes. A frozen specification is not
> amended after its results were inspected
> ([decision 0010](../decisions/0010-bars-carry-a-reopening-condition.md) clause 4), so the
> labels stay and this note carries the correction. **No arm in this file, or in any other
> experiment in the programme, holds the recommended seven funds at a 30% trend weight.**

`as of 2026-08-23`. **`exploratory`.** The tournament arm is
[Experiment 016e](../../research/experiments/exp_016e_final_construction.yaml)
(spec `3a86ef6f…`, run
[`cd2fb4b9…`](../../research/artifacts/cd2fb4b964cf4f8b966432076906ad82/summary.md),
19 arms, 15 scored). The fund-level arithmetic reproduces with
`cd research && uv run python -m portfolio_edge.studies.untested_tilts`.

---

## Conclusion

1. **The recommended portfolio beats its leverage-matched control by +2.20% a year and
   the test cannot see it.** Against a cheap 65/35 cap-weighted index levered to the same
   1.268× gross notional and charged the same financing, over 427 months: **+2.20 pp/yr,
   95% interval [+0.05, +4.57], against a smallest-detectable effect of 2.83**. It would
   take **59 years of holding** before this design could tell the two apart. Tracking
   error 6.0%. Probability of trailing the control: **15.6% over ten years, 7.1% over
   twenty, 3.4% over thirty**, with a median shortfall of −0.79, −0.46 and −0.30 pp/yr
   when it does. The verdict is `unresolved`, and that was predicted in the specification
   before the run.
2. **The four constructions are indistinguishable from one another, which is the
   expected result and a legitimate one.** Recommended +2.20, AVUV-instead-of-VTV +2.35,
   previous recommendation +1.92, investor's original eight +2.49 — a spread of 0.57 pp/yr
   inside floors of 2.75 to 3.33.
3. **The one comparison this design *can* resolve says the recommended portfolio trails
   the investor's original proposal by −0.50 pp/yr [−0.77, −0.23], against a floor of
   0.39. Almost all of it is leverage, not construction.** The original holds RSST at 30%
   and therefore 1.322× gross against the recommendation's 1.268×; on a panel whose US
   equity leg returned 9.83%/yr, five points more notional is worth about what the gap is.
   This is the tournament's own load-bearing lesson pointed at the recommendation:
   **comparing two portfolios at different leverage credits the leverage to the winner.**
   **The pair also differs in four of its holdings**, so it is not a clean reading of the
   trend weight either; §1 gives the reason to attribute it to the wrapper anyway and the
   reason that reason is not a measurement. This page does not settle the trend weight, and
   the weight it moved to is 30%.
4. **Adding AVDV was worth about +0.28% a year and sits exactly on the edge of what the
   test can see.** Recommended against previous recommendation, same gross notional, one
   sleeve different: **+0.28 pp/yr [+0.05, +0.56] against a floor of 0.29**, positive in
   the full window and in all seven declared sub-periods, 39 years to separate. The sleeve-level arithmetic agrees
   independently at +0.16% a year for a 5% line and +0.32% for 10%.
5. **VTV against AVUV is unresolved and stays unresolved on both windows on which the
   comparison is legal.** Whole-portfolio: **−0.15 pp/yr [−0.68, +0.34] against a floor of
   0.68** — 717 years. On published loadings (both funds fitted on the same 72 months)
   AVUV is 0.15 ahead; on matched loadings (both refitted on the same 36 months, where
   VTV's value exposure is *higher* than AVUV's) AVUV is 0.07 ahead. **Neither window
   resolves it, and the window that flatters AVUV's exposure is not the window that
   flatters its portfolio result.**
6. **Net cost does not change the VTV call, and it changes no verdict on this shelf.**
   Form N-CEN was read for eight funds across 50 fiscal years. **No fund on this shelf has
   negative net cost.** The largest fee-to-cost gap is AVDV's — 36 bp of fee against
   **30.03 bp of net cost** — and it makes the strongest recommendation on the shelf
   slightly stronger. VTV's own lending is **0.30 bp**, so its net cost is **2.70 bp**
   against AVUV's **24.54**: the gap the VTV call rests on was 22 bp on fee and is 21.8 bp
   on cost.
7. **RPV is rejected, and not on its exposure.** It delivers the deepest US value exposure
   on the shelf, but over VTV it also delivers **RMW −0.204 and UMD −0.173** — it pays for
   value partly by selling momentum — and it trades **42%/yr against VTV's 8%**. At a 15%
   weight replacing VTV it changes portfolio return by about **−0.10% a year, plausibly
   −0.63% to +0.42%**, and it is **negative under all four of this repository's premium
   scenarios including the pooled one**. The +0.18%/yr it was hoped to be worth is not
   there.
8. **SPMO is the better US momentum product and still is not worth adding.** 13 bp against
   MTUM's 15, **44%/yr of turnover against MTUM's 116%**, 12.93 bp net cost, and a
   distribution tax drag *below* VTI's. Over VTI it delivers **UMD +0.395 [+0.281,
   +0.508]** on 78 months. At a 5% weight it is **+0.02% a year, plausibly −0.14% to
   +0.18%** — better than MTUM's −0.03% and still not distinguishable from zero. Two
   things sink it: the US momentum premium it buys is **+4.19 pp/yr against a 7.27 pp/yr
   floor**, and its active leg is **+0.626 correlated with IDMO's**, a tighter overlap
   than MTUM's +0.554.

---

## 1. The tournament, on the seven-fund construction at a 25% trend weight

Same frozen machinery as [the construction tournament](construction-tournament.md), same
427-month panel (1990-11…2026-05), same costs charged inside the rule, same stationary
block bootstrap. **Funds are basis-mapped, not simulated from fund returns** — every
ticker is a linear combination of Ken French factor series and AQR's TSMOM less a fee, and
that mapping is the largest single source of error in every figure below. A growth number
here is a property of a construction and never of a fund.

Two leverage-matched controls are carried rather than one, because the recommendation cut
the wrapper from 30% to 25% and therefore runs 1.268× gross where the original ran 1.322×.
016's own scope note records the single-control mismatch as a defect it could not avoid.

### Against the leverage-matched control

| Arm | Gross | Gap, pp/yr | 95% interval | Smallest the test could see | Years to separate | Tracking error | Verdict |
| --- | ---: | ---: | :---: | ---: | ---: | ---: | --- |
| investor's original eight | 1.33 | +2.49 | [−0.07, +5.31] | 3.33 | 64 | 7.1% | unresolved |
| AVUV instead of VTV | 1.28 | +2.35 | [+0.05, +4.93] | 2.80 | 51 | 6.0% | unresolved |
| AVUV, matched-window loadings | 1.28 | +2.32 | [+0.04, +4.88] | 2.79 | 52 | 5.9% | unresolved |
| **recommended**, matched-window loadings | 1.28 | +2.26 | [+0.07, +4.68] | 2.85 | 57 | 6.1% | unresolved |
| **recommended** | 1.28 | **+2.20** | [+0.05, +4.57] | 2.83 | **59** | 6.0% | unresolved |
| previous recommendation | 1.28 | +1.92 | [−0.15, +4.17] | 2.75 | 73 | 5.9% | unresolved |

The original eight is scored against the 1.322× control and the rest against the 1.268×
one; those are two families and their gaps are not pooled. Every arm's gap survives the
27-point mapping-perturbation grid without changing sign — the recommended arm ranges
+1.41 to +3.00 across it — so what makes them `unresolved` is the width of the sample, not
the fragility of the mapping.

### The three head-to-heads, which are what the recommendation actually claims

A paired difference between two whole portfolios has far less noise in it than either has
against a control, so these are the comparisons this design can nearly resolve.

| Comparison | Gap, pp/yr | 95% interval | Smallest the test could see | Years | Tracking error | Verdict |
| --- | ---: | :---: | ---: | ---: | ---: | --- |
| recommended − investor's original eight | **−0.50** | [−0.77, −0.23] | 0.39 | 22 | 0.8% | **resolved, and negative** |
| recommended − previous recommendation | +0.28 | [+0.05, +0.56] | 0.29 | 39 | 0.6% | unresolved, by 0.01 |
| recommended − AVUV variant | −0.15 | [−0.68, +0.34] | 0.68 | 717 | 1.4% | unresolved |

**Read the first row carefully, because it is quoted more than anything else here and it
is not the comparison it is usually described as.** It is the only whole-portfolio
comparison in either tournament that clears its own floor. **It is not a 25-against-30
comparison at a fixed construction.** `recommended_vs_original` scores RSST 25 / VTI 24 /
VTV 15 / VXUS 16 / AVDV 10 / IDMO 5 / AVES 5 against RSST 30 / VTI 20 / AVLV 15 / DFIV 10 /
VEA 10 / IDMO 5 / IEMG 5 / AVES 5, so **the pair differs in four of its holdings as well as
in five points of trend**, and no arm anywhere holds the recommended seven funds at 30%.

Two reasons to read the gap as the trend weight rather than the fund list, and one reason
not to over-read it. The tilt complexes are near enough identical: `recommended_no_trend`
scores **+0.7996** and 016's `proposal_no_trend` **+0.79** pp/yr, both against the same
unlevered cheap control on the same 427 months, so what is left to move the whole-portfolio
number is the wrapper. And the gap is negative in all seven declared sub-periods as well as
the full window, from −0.19 post-GFC to −0.94 before the flat decade. Against that: the two
tilt-only figures come from two tournaments and are not a paired difference, so they carry
no interval of their own and cannot bound the fund-list contribution. **The clean design is
in *Open* item 4 and has not been run.**

What survives is that this is a leverage result rather than a construction one: the two
portfolios differ by 5.4 points of gross notional, and
[the tournament](construction-tournament.md) finding 11 established that the sign of a
wrapper's contribution is set by the equity premium assumed. At the panel's realised 9.83%
US equity premium, more notional wins. **This number is what subsequently moved the
recommended trend weight from 25% to 30%** ([part A](portfolio-for-one-investor.md) §2),
against the holdability evidence rather than in agreement with it, and it should be quoted
with the caveat above attached.

The second row is the AVDV decision, and it is the most informative line on the page: two
portfolios at identical leverage differing in one sleeve, +0.28 pp/yr against a floor of
0.29. **It misses resolution by a hundredth of a percentage point.** It is positive in
every sub-period (+0.06 to +0.73), its Benjamini–Hochberg adjusted p is 0.033, and its
probability of trailing over thirty years is 1.3%. Calling that "unresolved" is correct and
is also the least interesting true thing about it.

### The tilt component on its own

Strip the wrapper out and replace it with plain US beta at the same capital, and score
against the *unlevered* cheap control:

| Arm | Gap, pp/yr | 95% interval | Smallest the test could see | Years | Tracking error | Verdict |
| --- | ---: | :---: | ---: | ---: | ---: | --- |
| recommended, tilts only | **+0.80** | [+0.36, +1.31] | 0.47 | 12 | 1.0% | **resolved** |
| previous recommendation, tilts only | **+0.51** | [+0.24, +0.79] | 0.32 | 14 | 0.7% | **resolved** |

This reproduces 016's `proposal_no_trend` at +0.79 on a different fund list, which is the
useful part: the tilt result is not a property of the particular funds the investor
proposed. It is positive in the full window and in all seven declared sub-periods, weakest
in the second half at +0.35 and post-GFC at +0.43, strongest through the lost decade at +1.71, and it costs 9.1 bp of weighted fee against the control's
3.7. **The difference between the two rows is AVDV again, at +0.29 pp/yr on the unlevered
pair against +0.28 on the levered one** — the same answer arrived at twice.

### Risk, and what it will feel like

| | recommended | previous | AVUV variant | original eight | levered control | cheap control |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Growth, pp/yr | 13.44 | 13.16 | 13.59 | 13.94 | 11.24 | 10.00 |
| Volatility | 14.7% | 14.9% | 15.0% | 15.0% | 18.9% | 14.7% |
| Maximum drawdown | −50.3% | −50.2% | −50.6% | −49.6% | −64.6% | −52.7% |
| Longest run under water | 42 months | 44 | 40 | 39 | 69 | 63 |
| Weighted fee | 33.9 bp | 30.9 | 37.2 | 39.7 | 4.6 | 3.7 |
| Annual turnover | 3.7% | 3.7% | 4.0% | 3.9% | 4.1% | 2.6% |
| Lines held | 7 | 6 | 7 | 8 | 2 | 2 |

The recommended construction's own worst decade against its control is post-2009: **−1.15
pp/yr for seventeen years**, against +8.15 pp/yr through the 1999–2009 flat equity decade.
That asymmetry is the wrapper's, it is documented in
[the tournament](construction-tournament.md) finding 11b, and this run reproduces it on a
different portfolio.

### After tax, and what is still missing from it

016 could compute an after-tax gap from one fund's filed table. This run has three — RSST,
AVUV and AVDV — and the recommended arm's after-tax gap is **+2.19 against +2.20 before
tax**, a difference of 1.0 bp. **VTV is the hole**: no after-tax table was in the
repository when the specification was frozen, so a 15% line contributes nothing to that
column. §2 fills the gap for future work — VTV's distribution drag is 0.67 pp/yr against
VTI's 0.42, so a 15% VTV line costs about 3.8 bp a year of extra distribution tax that this
arm does not charge. That is still an order of magnitude below the floor.

---

## 2. Net cost, from Form N-CEN

`net cost = expense ratio − net securities-lending income`, both measured against the
fund's own net assets, which is why they subtract. Lending is the **median** over every
fiscal year on file, from Item C.6.g over Item C.2 — the same definition
[structural and tax edges](structural-and-tax-edges.md) §6.1 uses for the core-beta shelf.
Read on 2026-08-23 from EDGAR: 50 fiscal-year filings across eight funds.

| Fund | Fee | Lending, median | Range across years | Fiscal years | **Net cost** |
| --- | ---: | ---: | :---: | ---: | ---: |
| VTV | 3 bp | 0.30 bp | 0.05 – 0.70 | 8 (2018–2025) | **2.70 bp** |
| AVLV | 15 bp | 0.06 bp | 0.01 – 0.13 | 4 (2022–2025) | **14.94 bp** |
| SPMO | 13 bp | 0.07 bp | 0.00 – 0.31 | 7 (2019–2025) | **12.93 bp** |
| AVUV | 25 bp | 0.46 bp | 0.21 – 1.51 | 6 (2020–2025) | **24.54 bp** |
| IDMO | 25 bp | 2.41 bp | 1.31 – 5.28 | 7 (2018–2025) | **22.59 bp** |
| RPV | 35 bp | 1.13 bp | 0.39 – 26.65 | 8 (2019–2026) | **33.87 bp** |
| AVES | 36 bp | 6.79 bp | 5.43 – 8.28 | 4 (2022–2025) | **29.21 bp** |
| AVDV | 36 bp | 5.97 bp | 2.99 – 10.28 | 6 (2020–2025) | **30.03 bp** |

Beside them, already held: VTI 1.16 bp net and VXUS 1.43 bp net.

**Four things this table says.**

- **Nothing here is free, and nothing here is negative.** The hypothesis that some funds on
  this shelf earn more from lending than they charge in fees is true on the *core-beta*
  shelf — SPDW at −1.63 bp and IEMG at −0.87 bp — and false on the tilt shelf. The tilt
  funds are US and developed large-cap value and momentum, which is not what short sellers
  borrow. The one fund with meaningful borrow demand is the emerging-markets one.
- **The fee ranking and the cost ranking differ in exactly one place, and it does not
  matter.** On fee, AVUV and IDMO are tied at 25 bp. On cost, IDMO is 2.0 bp cheaper. Every
  other pair keeps its order.
- **The largest correction is AVDV's, and it favours the recommendation.** 36 bp of fee
  against 30.03 bp of cost. [The tilt audit](untested-tilt-candidates.md) charged AVDV its
  gross fee and called that "unfavourable to it"; it was, by 6 bp a year on a 10% line, or
  0.6 bp on the portfolio.
- **RPV's fiscal-2026 filing is an outlier and the median deliberately does not follow
  it.** $3.97m of lending income on $1.49bn of net assets is 26.65 bp — eight times any
  prior year, in a year the fund shrank. The figure is filed and unaudited; a median over
  eight years is the right estimator precisely because one year can do that.

**Does this change the VTV call? No, and the reason is arithmetic.** The recommendation
holds VTV at 15% rather than AVUV because AVUV's extra exposure over VTV is 87% size, on a
premium of +0.33 pp/yr against a 2.47 pp/yr floor, and because it costs more. That cost
difference was 22 bp on fee. On net cost it is **21.8 bp**. The incremental cost bracket for
AVUV replacing VTV moves from a collapsed 0.22 pp/yr to a measured 0.215–0.223, and the
portfolio effect is unchanged at **+0.09% a year, range −0.42% to +0.60%**. Reading Form
N-CEN for every fund in the tilt audit moved no headline figure by as much as 0.01
percentage points, because the audit's centre already sat at the fee end of each bracket.

---

## 3. RPV: the deepest value exposure on the shelf, and a subtraction

Delivered exposure is fitted from the **difference series** — RPV's filed monthly total
return less VTV's, regressed on the US FF5+UMD panel — so the coefficients are what RPV
adds over the fund it would replace and the intervals mean something. 78 months,
2019-10…2026-03.

| | Delivered over VTV | 95% interval | Smallest the window could see |
| --- | ---: | :---: | ---: |
| HML | **+0.369** | [+0.249, +0.490] | 0.173 |
| SMB | **+0.199** | [+0.066, +0.332] | 0.191 |
| RMW | **−0.204** | [−0.361, −0.047] | 0.224 |
| CMA | −0.103 | [−0.266, +0.060] | 0.233 |
| UMD | **−0.173** | [−0.337, −0.008] | 0.235 |
| Extra return | −0.58 | [−4.56, +3.41] | 5.70 |

**The value exposure is real and so are the two legs nobody priced.** RPV's index weights
its constituents by value score rather than by capitalisation and excludes anything showing
growth characteristics, and one of the six factors that definition scores on is twelve-month
price momentum. The fund therefore buys value *by selling momentum*, and momentum is the one
US factor with a larger own-panel premium than value (+4.19 against +1.57). On the
repository's own-panel premia the gross exposure gain is:

`0.369 × 1.57 (HML) + 0.199 × 0.33 (SMB) − 0.173 × 4.19 (UMD) ≈ −0.07 pp/yr`

— a wash before a single basis point of cost. Then the costs arrive: **33.87 bp of net cost
against VTV's 2.70**, and **42%/yr of turnover against VTV's 8%**, which at the
repository's 1.0-to-1.7 trading-cost coefficient is 0.649 to 0.901 pp/yr of incremental
cost.

| Premium scenario | RPV replacing VTV, pp/yr per dollar of sleeve |
| --- | ---: |
| own-panel | −0.98 to −0.73 |
| pooled | −0.89 to −0.63 |
| half | −0.94 to −0.69 |
| null | −0.90 to −0.65 |

**Negative in all four.** That is a stronger statement than the confidence interval,
because it does not depend on the sample: there is no premium assumption in this
repository under which RPV replacing VTV pays.

Conditioned on what the portfolio already owns, RPV's active leg is **−0.086 correlated
with the held active position** and **−0.370 with IDMO's** — it is the anti-momentum
position, which is the same finding read from the other side. Its marginal edge is −0.69
pp/yr per dollar of sleeve, and its own tracking error is 7.9%.

| Weight | Expected change in portfolio return | Range | If every premium is zero |
| ---: | ---: | :---: | ---: |
| 5% | −0.03% a year | −0.21% to +0.14% | −0.05% |
| 10% | −0.07% a year | −0.42% to +0.28% | −0.09% |
| **15%** | **−0.10% a year** | **−0.63% to +0.42%** | −0.14% |

**Verdict: do not hold it, and the reason is momentum and turnover rather than fee.**
Two objections that were expected to decide it do not. Its tracking error is 7.9%, not
wild. And its tax drag is **0.62 pp/yr against VTV's 0.67 over the same five years** — RPV
is the *more* tax-efficient of the two on distributions, despite five times the turnover,
which is the ETF in-kind shield doing the same work
[the tilt audit](untested-tilt-candidates.md) found it doing for MTUM.

One thing this does not establish: RPV's *measured* extra return over VTV is −0.58 pp/yr
against a 5.70 pp/yr floor, and no verdict above uses it.

---

## 4. SPMO: right product, wrong sleeve

[The tilt audit](untested-tilt-candidates.md) rejected MTUM on 116%/yr of turnover and
named SPMO as the way to revisit US momentum properly, noting that the shelf carried a UMD
loading for it "and no fee, window, interval or turnover recorded for it at all." All four
are now read.

**The published loading could not be used and was not.** The shelf records SPMO at UMD
+0.414 with `window: null`. A loading with no window cannot be reproduced and cannot be
compared with any other fund's — that is the rule `src/lib/loadings.ts` enforces by
throwing, and [loading comparability](loading-comparability-and-wrapper-exposure.md)
explains why. SPMO is therefore fitted here from its own Form N-PORT Item B.5 filings on a
stated window, exactly as every other candidate is.

| | SPMO over VTI | MTUM over VTI |
| --- | ---: | ---: |
| Months | 78 (2019-10…2026-03) | 78 (2019-10…2026-03) |
| UMD delivered | **+0.395** [+0.281, +0.508] | +0.437 [+0.316, +0.559] |
| SMB delivered | −0.171 [−0.301, −0.040] | −0.042 [−0.212, +0.127] |
| Fee | **13 bp** | 15 bp |
| Net cost | **12.93 bp** | not read |
| Turnover | **44%/yr** | 116%/yr |
| Incremental cost over VTI | **0.51 to 0.82 pp/yr** | 1.25 to 2.06 pp/yr |
| Distribution tax drag vs VTI | **−0.05 pp/yr** | −0.11 pp/yr |
| Correlation of active leg with IDMO's | **+0.626** | +0.554 |
| Sleeve edge, own-panel | +0.70 to +1.01 | −0.28 to +0.53 |
| Marginal edge given what is held | +0.37 | −0.53 |
| **At a 5% weight** | **+0.02% a year, −0.14% to +0.18%** | −0.03% a year, −0.18% to +0.13% |

From its summary prospectus dated 2025-12-19: 0.13% management fee, no other expenses, 44%
portfolio turnover in the most recent fiscal year, approximately 100 S&P 500 constituents
weighted by capitalisation times momentum score, non-diversified. Its five-year return to
2024-12 was 19.23% before taxes and 18.86% after taxes on distributions.

**SPMO beats MTUM on every knowable dimension and the sleeve still does not earn its
place.** Turnover falls from 116% to 44%, which was the whole of MTUM's problem, and the
portfolio effect moves from −0.03% to +0.02% a year. It does not clear zero by anything the
data can see, and two facts explain why:

- **The premium it buys cannot be signed.** US UMD is +4.19 pp/yr against a 7.27 pp/yr
  detection floor on this repository's own panel. A gross exposure gain of `0.395 × 4.19 =
  +1.66 pp/yr` is computed from a number smaller than its own measurement error.
- **The overlap with IDMO is worse than MTUM's, not better.** SPMO's active leg correlates
  **+0.626** with the international momentum line already held, against MTUM's +0.554.
  Two momentum tickers at that correlation are worth about 1.23 independent bets out of 2.
  The portfolio already owns the momentum region whose premium *does* clear its floor.

**Verdict: SPMO replaces MTUM as the shelf's US momentum reference and is not added.** If
US momentum is ever wanted on non-evidential grounds, this is the fund and 5% is the size;
it is not an improvement this page can demonstrate.

---

## Verified, assumed, open

**Verified here.** Every gap, interval, smallest-detectable effect, era split, drawdown and
underperformance probability in §1, from
[run `cd2fb4b9…`](../../research/artifacts/cd2fb4b964cf4f8b966432076906ad82/summary.md)
against a specification frozen and hashed before the run. Every delivered exposure in §3 and
§4, from Form N-PORT Item B.5 and Ken French's factor files, with the published loadings
first reproduced on their own windows to within 0.002. Every lending figure in §2, from Form
N-CEN Items C.2 and C.6.g. Fee, turnover and standardised after-tax returns from each
fund's own Form 497K: RPV's dated 2025-08-28, SPMO's 2025-12-19, and VTV's and VTI's
2025-04-29, which is the vintage whose after-tax table ends 2024-12 and therefore the one
that subtracts against the others.

**Assumed.**

- **Funds are basis-mapped in §1.** Every ticker is Ken French factors plus AQR's TSMOM
  less a fee, with market beta assumed to be 1.000 everywhere and never measured. Loadings
  fitted on 36–78 month fund windows are applied to 427 months.
- **Premia are inputs, not estimates.** Four scenarios, carried from
  [stacking](stacking-and-effective-breadth.md) §2; nothing here estimates one.
- **Trading cost is `k × turnover` basis points at `k` from 1.0 to 1.7.** For RPV and SPMO,
  which turn over 42% and 44%, the choice between the two ends is 0.25 and 0.31 pp/yr —
  smaller than the whole verdict in RPV's case and comparable to it in SPMO's. Both ends are
  reported.
- **AQR's TSMOM is gross of the vendor's own trading costs by omission**, so every
  trend-bearing figure in §1 inherits that.
- **Securities lending is not credited inside the tournament.** The specification omits it
  on the grounds that it would credit the cheap control and charge the candidates nothing,
  which is the direction least favourable to the hypothesis under test. §2's figures are
  therefore not in §1's numbers.

**A correction, recorded here rather than by editing a frozen specification.** 016e's
`parameters.assumed_fee_grid` rationale says the file "charges 36 where 016 charged an
assumed 30" for AVES. **It does not**: `cost_model.fund_expense_ratio_basis_points` still
carries 30, and the 36 bp reading is the `AVES@0.36%` sensitivity arm, which moves the
recommended arm's gap from +2.200 to +2.197. The prose is wrong and the numbers are right,
and 0.3 bp is three orders of magnitude below the arm's own 2.83 pp/yr floor.
[Decision 0010](../decisions/0010-bars-carry-a-reopening-condition.md) clause 4 forbids
amending a specification after its results were inspected, so this is the route. Two smaller
slips in the same file, both prose and neither load-bearing: the note on the `recommended`
arm says "three of them (VTI, VXUS) carry no active position" where it is two, and several
blocks inherited verbatim from 016d — `hostile_tests`, `reporting_requirements` and
`notes` — still describe MATE, JPFP and the post-hoc arms of 016b, which this file does not
carry. The contestants, cost model and inference blocks are this file's own.

**Open.**

1. **VTV's after-tax table is now read (0.67 pp/yr, five years to 2024-12) but is not in
   the tournament's after-tax column**, because the specification was frozen before it was
   read. Worth about 3.8 bp/yr on a 15% line.
2. **MTUM's and QVAL's securities lending remain unread.** Both are already rejected on
   turnover and lending cannot move either verdict; this is recorded so the gap is not
   mistaken for a measurement.
3. **RPV's fiscal-2026 lending figure of 26.65 bp is unexplained.** If it is a regime
   rather than a filing artefact, RPV's net cost falls toward 8 bp. That would not move the
   centre of its verdict, which is quoted at the worse end of the cost bracket and therefore
   at the gross fee; it would move the *best* case from −0.73 to about −0.47 pp/yr per
   dollar of sleeve. Still negative, because turnover and the momentum leg rather than the
   fee are what decide it.
4. **The head-to-head against the investor's original proposal is a leverage comparison
   wearing a construction label**, and no arm here separates the two. The clean design is a
   pair matched at the same gross notional, which means choosing a trend weight first.
5. **Everything in §3 and §4 rests on 78 months**, which is shorter than one value cycle.

## What this does not establish

- **Not** that the recommended portfolio beats a cheap levered index. +2.20 pp/yr against a
  2.83 pp/yr floor is `unresolved` and 59 years is longer than the holding period.
- **Not** that the investor's original proposal is better. It is more levered, and on a
  panel with a 9.83% realised equity premium that is what the −0.50 measures.
- **Not** that VTV is the right US value fund. It is the cheapest one whose exposure is
  delivered, and the comparison against AVUV is unresolved on both admissible windows.
- **Not** that RPV or SPMO are bad funds. Each is scored against *this* portfolio at *this*
  moment; SPMO against a portfolio holding no momentum at all would read differently.
- **Not** a promotion. Nothing here is `production-eligible` and
  [decision 0004](../decisions/0004-no-sleeve-promoted.md)'s non-promotion stands.
