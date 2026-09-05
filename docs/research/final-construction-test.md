# The final construction, tested as one object

## Current published portfolios: funded fund substitutions

`as of 2026-09-05`. **`exploratory`.** VTV versus AVUV remains unresolved;
SPMO remains a candidate. These comparisons use the current printed value-lean,
with-trend and cautious holdings. The older numbered sections below concern their own
frozen constructions, whose labels and weights must not be read as today's recommendation.
The decision is whether to replace the entire VTV holding with AVUV, move five percentage
points from VTI to SPMO (half that in cautious), or do both. Weight optimisation, personal
taxes and a permanent fund ranking are outside these experiments.

[Experiment 030](../../research/experiments/exp_030_live_fund_portfolios.yaml) uses the
funds' filed NAV total returns: October 2021–March 2026 for value-lean, October 2023–March
2026 for the two portfolios containing RSST. It buys initially, lets weights drift, and
rebalances annually. Fund fees and internal trading are already in NAV returns; only
investor execution is added, at assumed roundtrip costs of 5 and 25 basis points.
The [generated comparisons](../../research/artifacts/785ca563fc554fbd862b2cc1b41bbc9f/tables.md)
and [committed paths and source identities](../../research/artifacts/785ca563fc554fbd862b2cc1b41bbc9f/result.json)
contain the exact outcomes and intervals.

The value portfolio demonstrates why average return alone cannot choose the fund:
AVUV slightly raises arithmetic return but lowers compounded growth. In the two shorter
portfolios it lowers both growth and the worst drawdown. SPMO improves observed growth;
the value portfolio's interval spans zero, while the shorter portfolios' conditional
intervals do not. Combining both changes trails the SPMO-only arm in these samples.
Raising execution costs barely changes the relative ordering. These are short, overlapping,
previously observed histories; resampling them does not establish future performance.
Intervals use a joint stationary bootstrap with six-month blocks and rerun the trading
rule. Cheap-index controls are separate descriptive comparisons, not leverage-matched tests.

[Experiment 029](../../research/experiments/exp_029_funded_fund_substitutions.yaml)
asks how those same substitutions behave under different fitted exposures, premiums and
cost assumptions. Its [scenario table](../../research/artifacts/d75a07b3f92c436c9337a3a865e87846/tables.md)
projects matched three- and six-year US fund fits onto the historical factor panel.
AVUV's advantage shrinks when historical premiums are replaced by the declared assumptions;
its interval includes zero. SPMO's case weakens with halved premiums and can reverse under
null style premiums plus high assumed trading costs. The combination adds little beyond
the separate effects. Higher fitted market exposure explains part of the historical gains.

Experiment 029 uses the inherited anniversary-rebalance cost approximation and waives
initial purchase costs. Experiment 030 charges the initial purchase and solves the
self-financing execution equation exactly; the two cost conventions are not identical.

These projected paths omit fund residual return and risk, and their intervals omit loading
and assumed-premium uncertainty. They use nominal Treasuries as the SCHP proxy and a gross
trend series for RSST's trend leg. They cannot replace the actual fund-history test.
The [provenance record](../../research/artifacts/d75a07b3f92c436c9337a3a865e87846/provenance.json)
identifies the fitted source bytes and inherited panels. The ledger preserves the initial
failed attempt and subsequent specification correction before portfolio results existed.

**Consequence.** Neither experiment establishes VTV as the best value fund or licenses an
SPMO allocation from a favourable recent window. They replace the former overlap argument
with a funded comparison. Next compare AVUV funded from VTI, test smaller value allocations,
and evaluate momentum under weaker premiums and changing exposures, including its reversal
risk. The ETF trading-cost coefficient needs fund-specific validation; it is an assumption,
not an empirical lower bound. A decision to change holdings must state the investor's
objective and tradeoff between growth, drawdown and tracking error.

## Earlier construction tests

**Question.** Three gaps, and they turn out to have one answer. First: every result behind
the recommended portfolio is component-level, and the construction tournament scored the
investor's *original* eight-fund proposal rather than this one — does the recommended
construction beat a leverage-matched cheap index, and does it beat the alternatives it was
chosen over? Second: the shelf quoted fees where net costs belong, and Form N-CEN carries
the missing term — does reading it change the VTV call? Third: two products were named as
the right way to revisit US value and US momentum and neither was ever priced — what are
RPV and SPMO worth? A fourth was added on 2026-09-02: the one whole-portfolio result this
page can resolve, the tilt complex against the cheap index, rests on ex-US panels that begin
1990-11 and had never been tested before that date. Does it hold out of sample?

**Decision it informs.** Whether to keep RSST 25% / VTI 24% / VTV 15% / VXUS 16% /
AVDV 10% / IDMO 5% / AVES 5% as it stands, and which of four named substitutions would
improve it.

**Out of scope.** The trend weight ([tournament](construction-tournament.md) finding 6 and
[trend weight](trend-weight-under-uncertainty.md)), whether any factor premium exists
([factor persistence](factor-persistence.md)), and the weights themselves
([the recommendation](portfolio-recommendation.md), which this page does not edit).

> **"Recommended" in the older sections means the 25% arm; the subsequent revision used
> 30%.** Experiment 016e's specification was frozen while the recommendation stood at
> RSST 25% / VTI 24%, and every arm here named `recommended` carries those weights. §1's
> own resolved head-to-head is then what moved the weight: that historical revision is
> **RSST 30% / VTI 19% / VTV 15% / VXUS 16% / AVDV 10% / IDMO 5% / AVES 5%**, derived in
> [part A](portfolio-for-one-investor.md) §2 at that time. The five points
> come out of VTI and go into trend; nothing else changes. A frozen specification is not
> amended after its results were inspected
> ([decision 0010](../decisions/0010-bars-carry-a-reopening-condition.md) clause 4), so the
> labels stay and this note carries the correction. **No arm in this file holds the
> recommended seven funds at a 30% trend weight; Experiment 016f does, and
> [§1a](#1a-the-matched-pair-run-as-experiment-016f) records what it found.**

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
7. **RPV has a negative priced-factor contribution under all four declared premium
   scenarios.** Its deeper value loading also comes with negative profitability and
   momentum loadings and higher modelled trading costs than VTV. This is a conditional
   factor-and-cost finding, not a whole-portfolio growth comparison (§3).
8. **SPMO's portfolio role is unresolved.** Its filed fee and turnover are lower than
   MTUM's on the dated comparison. The earlier +0.02% portfolio-return headline was a
   residual appraisal statistic multiplied by weight, not the return from replacing VTI.
   The corrected [tilt calculation](untested-tilt-candidates.md) separates the two.
   Correlation with IDMO affects diversification; it does not subtract expected return
   from a funded purchase (§4).
9. **The tilt complex holds out of sample, and it is the first result on this page that
   does.** On AQR's Value and Momentum Everywhere stock-selection factors, 1981-07 to
   1990-10, before any French ex-US panel exists, the same complex at the same loadings and
   costs earns **+0.89 pp/yr, HAC 95% [+0.44, +1.34], block bootstrap [+0.45, +1.29],
   against floors of 0.60 (i.i.d.), 0.65 (HAC) and 0.60 (block bootstrap)**, positive in
   both halves, with an implied t of 3.86 against the 3.0 deflation hurdle. The same basis
   reads only **+0.40 against a 0.62 floor** on 1990-11 to 2026-05, so on a like-for-like
   basis the out-of-sample period was the better one. Developed value carries 0.54 of the
   0.89; US value 0.22 on a premium its own window cannot sign; developed momentum 0.17.
   Nothing here argues for moving VTV 15 / AVDV 10 / IDMO 5 / AVES 5
   ([§1b](#1b-out-of-sample-as-experiment-023)).

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
in five points of trend**. [§1a](#1a-the-matched-pair-run-as-experiment-016f) separates
the two.

Two reasons to read the gap as the trend weight rather than the fund list, and one reason
not to over-read it. The tilt complexes are near enough identical: `recommended_no_trend`
scores **+0.7996** and 016's `proposal_no_trend` **+0.79** pp/yr, both against the same
unlevered cheap control on the same 427 months, so what is left to move the whole-portfolio
number is the wrapper. And the gap is negative in all seven declared sub-periods as well as
the full window, from −0.19 post-GFC to −0.94 before the flat decade. Against that: the two
tilt-only figures come from two tournaments and are not a paired difference, so they carry
no interval of their own and cannot bound the fund-list contribution. **The clean design
was run afterwards as Experiment 016f ([§1a](#1a-the-matched-pair-run-as-experiment-016f)),
and it attributes the whole −0.50 to the wrapper weight.**

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

### 1a. The matched pair, run as Experiment 016f

`as of 2026-09-01`. **`exploratory`.**
[Experiment 016f](../../research/experiments/exp_016f_matched_pairs.yaml), run
[`36f14b39…`](../../research/artifacts/36f14b395e53407f8fdfaee3b4e8e37a/summary.md), 17
constructions on the same 427 months, same basis-mapped machinery, same block bootstrap.
It holds the recommended seven funds at 30% (`rec30`, 1.322× gross) and scores the pairs
this page could not.

| Pair, same fund list unless stated | Gap, pp/yr | 95% interval | Floor | Verdict |
| --- | ---: | :---: | ---: | --- |
| **rec30 − rec25** (five points of wrapper weight, nothing else) | **+0.51** | [+0.30, +0.72] | 0.30 (block 0.31) | **resolved** |
| rec30 − investor's original eight at 30% | +0.01 | [−0.18, +0.19] | 0.26 | unresolved |
| VEA 11 + IEMG 5 in place of VXUS 16 | +0.05 | [+0.00, +0.10] | 0.07 | unresolved (p 0.047, BH-adjusted 0.19) |
| AVLV in place of VTV | −0.01 | [−0.06, +0.05] | 0.09 | unresolved |
| DFIV in place of AVDV | −0.10 | [−0.29, +0.10] | 0.26 | unresolved |
| AVUV in place of VTV | +0.15 | [−0.34, +0.67] | 0.67 | unresolved |

**All of 016e's −0.50 was wrapper weight.** `(rec30 − original30) − (rec30 − rec25) =
+0.0117 − 0.5101 = −0.4984`, which is this page's `recommended_vs_original` to four
decimals; the four-holding fund-list change is worth +0.01 against a 0.26 floor. By hand,
`0.05 × 10.976` trend `+ 0.0036 × 9.83` equity `− 0.048` fee `− 0.010` financing `= +0.526`
arithmetic, less variance drag on the growth basis.

**It is a leverage result at the realised premium.** The pair's break-even trend haircut
is 10.08 pp/yr on the stored premium surface; at the like-for-like forward figure of 4.07
([trend weight](trend-weight-under-uncertainty.md) §1.1) it reads about +0.18 against its
0.30 floor, and at the 1.80 convention +0.07. "Resolvable" is a property of 1990–2026's
10.98 pp/yr, not of the construction. 30% stands for a contributing investor; 25% for one
who would sell it; the holdability figures on the trend-weight page are unchanged.

**Every fund-list pair is inside its floor**, which is what the specification declared
before the run: each is one or two points of capital moved between funds with near-identical
mappings. The VEA + IEMG pair is 5 bp/yr from one point of developed-to-emerging weight
under the 0.75/0.25 VXUS assumption, and the pair is 1–2 bp cheaper after lending; AVLV
costs 12 bp more than VTV for −0.01; DFIV's −0.10 carries its −3.8 fitted alpha, which
[stacking](stacking-and-effective-breadth.md) §4 leaves unexplained. The investor's label
"AVLV (SCV US)" is wrong: AVLV is large-cap value; AVUV is the small-cap value fund, and
it reads +0.15 against a 0.67 floor.

### 1b. Out of sample, as Experiment 023

`as of 2026-09-02`. **`exploratory`.**
[Experiment 023](../../research/experiments/exp_023_tilts_out_of_sample.yaml) (spec
`59181ce6…`), run
[`6915b674…`](../../research/artifacts/6915b6746af046c5ba54beb2902bbab2/summary.md), with
the full tables in
[`tables.md`](../../research/artifacts/6915b6746af046c5ba54beb2902bbab2/tables.md) and the
code in
[`exp_023_tilts_out_of_sample.py`](../../research/src/portfolio_edge/experiments/exp_023_tilts_out_of_sample.py).

**Conclusion.** The tilt complex's edge over the cheap index reproduces before 1990-11 with
the same sign and, on a like-for-like basis, a larger size. On AQR's Value and Momentum
Everywhere (VME) stock-selection factors, 1981-07 to 1990-10, 112 months: **+0.89 pp/yr,
HAC 95% [+0.44, +1.34], block bootstrap [+0.45, +1.29], against floors of 0.60 (i.i.d.),
0.65 (HAC) and 0.60 (block bootstrap)**; tracking error 0.66%; four years to distinguish at
80% power. Both halves are positive, +1.05 on 1981-07 to 1986-02 (floor 0.97) and +0.73 on
1986-03 to 1990-10 (floor 0.73). Removing the best month gives +0.82 and the worst +0.94; the
plus or minus 0.15 loading grid spans +0.56 to +1.22; block lengths of 6 and 24 months give
[+0.45, +1.33] and [+0.48, +1.27]. The implied t is 3.86 against the Harvey, Liu and Zhu
hurdle of 3 that [the adversarial review](adversarial-review.md) §3 applied to the
in-sample figure. The specification predicted +0.4 to +1.2 and `unresolved`; the size
landed inside the range and the status did not, because the tracking error came in at
0.66% rather than the 1.0% the floor was budgeted on.

**Why it is not a replication of +0.80.** The mapping carries the four tilt legs onto VME
the way 016e carries them onto French: VTV's +0.337 and VTI's +0.0247 onto VME US value;
AVDV's +0.510 and IDMO's +0.218 onto the equal-weighted UK, Europe and Japan value factor;
IDMO's +0.540 and AVDV's +0.008 onto the equal-weighted developed momentum factor. The
French loadings are applied unscaled to a rank-weighted long/short book they were not fitted
on, and the same complex on the same VME basis over 016e's own 427 months reads **+0.40
[HAC −0.15, +0.96] against a 0.62 floor, unresolved**. Three things separate that from
016e's +0.80, and the run prices each on the French basis over 1990-11 to 2026-05:

| Piece | pp/yr | Where it comes from |
| --- | ---: | --- |
| 016e `recommended_no_trend`, log-growth gap | +0.80 | [run `cd2fb4b9…`](../../research/artifacts/cd2fb4b964cf4f8b966432076906ad82/summary.md) |
| same complex, arithmetic active-leg gap, every French leg | +0.75 | this run; the −0.05 is annual rebalancing drift and constant costs, net of +0.03 variance drag |
| less the legs VME cannot carry | −0.20 | AVDV's and IDMO's SMB (+0.04), RMW (+0.13) and CMA (−0.06), and AVES's emerging value (+0.10) |
| less the regional residual | +0.04 | the complex holds 64/27/9 where the control holds 65/26.25/8.75; the residual is −0.04 and dropping it adds it back |
| French basis, mapped legs only | +0.59 | the estimand the VME arms measure, on French data |
| VME basis, same legs, same loadings | +0.40 | VME's value factors carry lower means: 0.92 against 2.16 pp/yr in the US and 3.45 against 5.12 developed |

**VME has no size, profitability or investment factor, so the small-cap half of AVDV is
unmapped, and the omission biases every VME figure downward**, by about 0.20 pp/yr on the
window where it can be measured. Out of sample the bias runs the same way: what VME cannot
carry is exactly the part of AVDV's exposure that 016e credits, so +0.89 is the complex
with its size leg removed. The bridged mapping, which multiplies each VME exposure by the
slope of the French factor on it over 1990-11 to 2026-05 (0.532, 0.564, 0.876, recomputed
by the run to within 0.0004 of the pins), reads **+0.53 [+0.28, +0.78] against a 0.34
floor** out of sample; the two mappings bracket the answer and both clear their floors.

**Which leg drove it.** Developed value +0.54 of the 0.89, US value +0.22, developed
momentum +0.17, cost −0.04. On each leg's own longest window before 1990-11: developed
value +8.72 pp/yr [+4.18, +13.26] on 112 months, contributing +0.54 [+0.26, +0.82] against
a 0.36 floor; developed momentum +6.62 [+2.79, +10.45] on 201 months from 1974-02,
contributing +0.18 [+0.08, +0.29] against 0.15; **US value +5.10 [−0.79, +10.99] on 225
months from 1972-02, against a 7.93 floor**, contributing +0.24 [−0.04, +0.51] against
0.37. The result is carried by the leg that carries it in sample, which is what the
specification predicted, and the one leg with a century of history is the one the window
cannot sign on its own.

**AVES is dropped before 1990-11**, its 5% scored as the VXUS it displaces, because no
emerging value series exists there. Carrying its +0.237 on the developed value factor
instead, as a stated approximation, adds +0.09 (+0.98 against a 0.65 floor).

**The full 539 months, 1981-07 to 2026-05, are the second basis**: **+0.52 [+0.07, +0.98]
against 0.51 (i.i.d.), 0.65 (HAC) and 0.70 (block bootstrap)**, clearing the first floor by
0.01 and neither of the other two; +0.89 before 1990-11 and +0.40 after; +0.89 in the first
half and +0.16 in the second; **+0.04 post-GFC against a 0.74 floor**, which is 016e's own
worst era read again on a different basis. Probability of trailing the control: 14.2% over
ten years, 7.7% over twenty, 3.8% over thirty, with median shortfalls of −0.21, −0.12 and
−0.09.

**Sized implication for the tilt weights.** Nothing here argues for moving VTV 15 /
AVDV 10 / IDMO 5 / AVES 5, and the result ranks the four lines by how much of the evidence
each one owns. Per point of capital, net of the fee difference against the line it
displaces: out of sample IDMO earned about 5.0 bp/yr, AVDV 4.2, VTV 1.5 and AVES (approximated)
1.8; in sample on the French basis with every leg, 4.6, 3.8, 0.7 and 1.7; bridged, about
0.55 of each out-of-sample figure. The developed lines earn their weights on both windows.
**VTV's 15 points are the least supported on the shelf**: 1.5 bp/yr per point out of sample
on a premium the window cannot sign, and 0.7 in sample. That is not a reason to cut it, since
it costs 3 bp and the complex needs a US value line, but it is a reason not to raise it and
the reason the AVUV question stays unresolved. Had the primary come back at or below zero,
clause (a), that would have been the evidence to cut AVDV and IDMO; it did not.

**Verified here.** Every gap, interval, floor, sub-period, leg contribution and trailing
probability above, from the run artifact against a specification frozen and hashed before
the run, with the raw and normalised hashes of the VME workbook and the four French files
pinned and a mismatch aborting. Nothing was read from the VME asset-allocation legs, which
[the evidence base](evidence-base.md) flags as changing construction after 2014.

**Assumed.** That 016e's loadings, fitted on 51 to 77 months of fund filings after 2019,
describe the same funds' exposure in the 1980s, and that a loading on a French 2x3 spread
transfers unscaled to a rank-weighted VME book; the bridged arm is the sensitivity. That
equal-weighting the UK, Europe and Japan factors is the right stand-in for a cap-weighted
developed ex-US composite. That the arithmetic active-leg gap stands in for the simulated
log-growth gap, which the basis check bounds at 0.05.

**Open.** The primary window is 112 months and its floor is 0.60. The VME series are
vendor-authored and reconstructed on every update. The design was chosen after reading the
1990-2026 result: the window is out of sample for the data and not for the design. AVES
has no out-of-sample test and cannot have one on any series in this repository.

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

Both rows are measured on 427 months whose developed ex-US and emerging factor series begin
1990-11, so until 2026-09-02 neither had an out-of-sample period.
[§1b](#1b-out-of-sample-as-experiment-023) supplies one.

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

**Negative in all four declared scenarios.** This depends on the sample-fitted loadings,
chosen premia and trading-cost model. It is not a claim about every plausible premium
assumption or the effect on the whole portfolio's compounded growth.

Conditioned on what the portfolio already owns, RPV's active leg is **−0.086 correlated
with the held active position** and **−0.370 with IDMO's** — it is the anti-momentum
position, which is the same finding read from the other side. Its residual appraisal alpha is −0.69
pp/yr per dollar of sleeve, and its own tracking error is 7.9%.

The former weight table multiplied this residual alpha by the purchase weight and
mislabelled it portfolio return. It is withdrawn. The corrected funded factor contribution
and its assumption range live in [the tilt calculation](untested-tilt-candidates.md).
Neither figure includes a forecast for the incremental market beta, unexplained return
or investor taxes, and neither measures the change in compounded portfolio growth.

**Working decision: do not add RPV on this factor-and-cost model.**
Two objections that were expected to decide it do not. Its tracking error is 7.9%, not
wild. And its tax drag is **0.62 pp/yr against VTV's 0.67 over the same five years** — RPV
is the *more* tax-efficient of the two on distributions, despite five times the turnover,
which is the ETF in-kind shield doing the same work
[the tilt audit](untested-tilt-candidates.md) found it doing for MTUM.

One thing this does not establish: RPV's *measured* extra return over VTV is −0.58 pp/yr
against a 5.70 pp/yr floor, and no verdict above uses it.

---

## 4. SPMO: portfolio role unresolved

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
| Assumed incremental cost over VTI | **0.51 to 0.82 pp/yr** | 1.25 to 2.06 pp/yr |
| Distribution tax drag vs VTI | **−0.05 pp/yr** | −0.11 pp/yr |
| Correlation of active leg with IDMO's | **+0.626** | +0.554 |
| Sleeve edge, own-panel | +0.70 to +1.01 | −0.28 to +0.53 |
| Residual appraisal alpha, not funded return | +0.37 | −0.53 |

From its summary prospectus dated 2025-12-19: 0.13% management fee, no other expenses, 44%
portfolio turnover in the most recent fiscal year, approximately 100 S&P 500 constituents
weighted by capitalisation times momentum score, non-diversified. Its five-year return to
2024-12 was 19.23% before taxes and 18.86% after taxes on distributions.

**The fee and turnover comparison favours SPMO; its portfolio role is still open.**
The earlier return claim subtracted exposure already held before multiplying by the
purchase weight. That is appropriate for asking whether a return can be explained by
other positions. It is not the arithmetic of selling VTI and buying SPMO. The corrected
[tilt calculation](untested-tilt-candidates.md) keeps the funded factor contribution
separate from this residual diagnostic.

Two uncertainties remain. The assumed US momentum premium has substantial estimation
error. SPMO's active leg also correlates +0.626 with IDMO's, so the two provide less
independent diversification than unrelated strategies would. Neither observation
establishes that adding SPMO lowers portfolio growth. That requires the full portfolio,
its funding asset, covariance, costs and drawdown outcomes in one test.

**Working decision: keep SPMO available for a whole-portfolio comparison.** This screen
provides no demonstrated reason to replace the current allocation, and its former
residual-return argument provides no demonstrated reason to reject SPMO either.

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
  reported. These are sensitivity assumptions, not validated ETF cost bounds; the
  [tilt audit](untested-tilt-candidates.md#fees-and-turnover-from-filings-trading-costs-assumed)
  compares the premise with SPMO's filed index-tracking figures.
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
4. **Run.** The head-to-head against the investor's original proposal was a leverage
   comparison wearing a construction label, and Experiment 016f separated the two
   ([§1a](#1a-the-matched-pair-run-as-experiment-016f)): rec30 − rec25 = +0.51 [+0.30,
   +0.72] against a 0.30 floor, and the fund-list change +0.01 against 0.26. What remains
   open is the forward premium at which the pair stays resolvable, which is the
   trend-weight page's question.
5. **Everything in §3 and §4 rests on 78 months**, which is shorter than one value cycle.

## What this does not establish

- **Not** that the recommended portfolio beats a cheap levered index. +2.20 pp/yr against a
  2.83 pp/yr floor is `unresolved` and 59 years is longer than the holding period.
- **Not** that the investor's original proposal is better. It is more levered, and on a
  panel with a 9.83% realised equity premium that is what the −0.50 measures.
- **Not** that VTV is the right US value fund. It is the cheapest one whose exposure is
  delivered, and the comparison against AVUV is unresolved on both admissible windows.
- **Not** that RPV or SPMO are bad funds. Their residual appraisal changes with the
  held portfolio; the mean contribution of a fixed funded purchase does not. Its effect
  on portfolio growth and risk still depends on the other holdings.
- **Not** that the tilt complex is worth +0.80 pp/yr going forward. Out of sample it is
  +0.89 on a basis that reads +0.40 in sample, with AVDV's size leg unmapped on both; the
  sign is established on two disjoint windows and the size is not.
- **Not** a promotion. Nothing here is `production-eligible` and
  [decision 0004](../decisions/0004-no-sleeve-promoted.md)'s non-promotion stands.
