# Adversarial review of the August 2026 construction session

**Question.** Nine agents sharing one repository, one data cache and one house style
converged on a portfolio recommendation. Which parts of that position are wrong,
overconfident, or an artifact of shared method — measured, and ranked by how much the
finding moves the decision?

**Current answer.** Two of the session's five conclusions are unsafe as stated and one is
mis-sized by an order of magnitude. The case against the 30% stacked wrapper rests on a
**basis error**: a geometric, net-of-1.5%-fee forecast of 1.80 pp/yr is subtracted from a
gross arithmetic realised mean of 10.98 and the difference called a haircut. Put on one
basis, that same forecast is **4.07 pp/yr gross arithmetic**, a haircut of **6.91 against
a break-even of 8.02** — so at the premium this repository holds, the overlay **adds
+0.34 pp/yr**, not subtracts. Three independent trend constructions on data the session
did not use (141 years, 96 years) put the premium at **5.3–7.2 pp/yr**, all above the
break-even. Separately, **no era claim in the tournament is resolvable** — not one arm's
first-half-minus-second-half difference clears its own floor — and the tournament's own
block-bootstrap floor, computed and stored but not published, turns the tilt result's
"13 years" into **30 years**. The placement line, the largest new number in the
recommendation, is **+3 to +38 bp/yr, not +38 to +55, and is not contractual**.

**As of 2026-08-22.** This page attacks; it promotes nothing and reverses nothing. Its arithmetic is
[`portfolio_edge.studies.adversarial_review`](../../research/src/portfolio_edge/studies/adversarial_review.py)
with tests at
[`tests/unit/test_studies_adversarial_review.py`](../../research/tests/unit/test_studies_adversarial_review.py).
Its re-runs of Experiment 016 use the frozen specification unamended, monkeypatching
mappings in memory: **no experiment was registered and no ledger entry was made**, because
this is a review of finished work rather than a new hypothesis-bearing trial.

## Findings, ranked by decision impact

### 1. The forward-premium argument mixes three bases, and correcting it flips its sign

**Decision moved: 30% of the portfolio.** [Tournament](construction-tournament.md)
finding 11 is the single argument that turns an `unresolved` verdict into a
recommendation to cut the wrapper: *"the proposal stops beating its leverage-matched
control once the trend leg loses 8.02 pp/yr of arithmetic mean. AQR's TSMOM returned
10.98 pp/yr of arithmetic excess. The repository's own forward trend premium is 1.80
pp/yr, which is a haircut of 9.18 — past the 8.02 break-even."*

**Where 1.80 comes from.** [Decision 0004](../decisions/0004-no-sleeve-promoted.md) cites
"a post-publication trend excess return this repository measures at roughly 1.8 pp/yr",
with no experiment reference. Computing directly from the pinned AQR workbook:

| Window | n | Arithmetic | Geometric | Volatility |
| --- | ---: | ---: | ---: | ---: |
| 1985-01…2026-05 (whole file) | 497 | 12.25 | 12.10 | 12.49 |
| 1990-11…2026-05 (the tournament window) | 427 | **10.98** | 10.71 | 12.38 |
| 2012-01…2025-12 (Experiment 004's post-publication era) | 168 | 4.17 | **3.35** | 13.23 |

`3.35 − 1.50` (Experiment 004's stated management fee) `= 1.85`. **The 1.80 is the same
AQR TSMOM file's last 168 months, taken geometrically and net of a fee.** It is a
39%-subsample of the 427 months being judged, not an independent prior.

**Three basis errors, each measurable.** Comparing it with 10.98 subtracts a geometric
net figure from an arithmetic gross one and calls the residue a haircut:

- **variance drag** `0.5 × 12.38² / 100 = 0.77 pp/yr`;
- **a 1.50 pp/yr management fee** that the tournament's arms **already charge separately**
  — RSST's 99 bp expense ratio is inside the rule, so the fee is counted twice;
- and the point estimate is used with no error bar, when the 168-month subsample's own
  95% interval is **[−2.67, +11.00]** and therefore *contains* the 10.98 it is being used
  to overturn.

Restated on the basis the break-even was computed on, `1.80 + 1.50 + 0.77 = 4.07 pp/yr`.
The like-for-like haircut is **6.91**, not 9.18, against a break-even of **8.02**.

**Re-running the frozen tournament at each candidate premium** (`trend_haircut_pp_yr`
against the same specification, nothing else changed):

| Trend leg's arithmetic gross mean | source | `proposal_rsst` gap | `stacked_heavy_50` |
| ---: | --- | ---: | ---: |
| 10.98 | realised, tournament window (published) | **+2.49** | +4.47 |
| 7.18 `[4.61, 9.75]` | own 4-asset book 1929–2025, at 12.38% vol | **+1.30** | +2.52 |
| 5.32 | own 36-leg JST book 1880–2020, at 12.38% vol | **+0.72** | +1.57 |
| 5.06 | AQR TSMOM 2012-01…2026-05 | **+0.64** | +1.44 |
| 4.17 | AQR TSMOM 2012-01…2025-12 | **+0.37** | +0.99 |
| **4.07** | **the repository's 1.80, restated to one basis** | **+0.34** | **+0.94** |
| 2.96 | the break-even | 0.00 | +0.42 |
| 2.84 | live managed-futures funds 2019–2025, net of their own fees | −0.04 | +0.32 |
| 1.80 | the figure as published (geometric, net of a second fee) | **−0.35** | −0.20 |

**Only the published figure, on its uncorrected basis, puts the proposal below zero.**
Every estimate on the break-even's own basis leaves it positive. The correct statement is
not "at the premium this repository believes the overlay subtracts" but **"the overlay's
sign is decided in the fourth decimal of a premium nobody can estimate, and the
repository's own estimate leaves it positive by about a third of a point."**

That does not make 30% right. It removes the only argument the session had for a
particular direction of error.

**The error has already propagated.** The trend-weight regret study built this session
carries `gross_premium = 0.0180` as one scenario at a 15% prior weight, labelled "a
convention this page traces and does not inherit" — correctly sceptical of the number's
provenance, and still entering a geometric net-of-fee figure on a **gross** axis. On that
page's own basis the same scenario belongs at 4.07, and every regret surface computed with
it is shifted toward zero trend.

### 2. Not one era claim in the tournament clears its own resolution

**Decision moved: the second pillar of the case against the wrapper, and the standing of
the tilt result.** Tournament finding 2 says the wrapper's whole contribution is pre-2008
and *"a full-window figure for these arms describes 1990–2008 more than it describes the
future."* [`AGENTS.md`](../../AGENTS.md) requires that "before interpreting a null, compare
the effect of interest with the design's resolution." The era table was never so compared.

An era gap is a mean on a sub-sample, so its floor scales as `1/sqrt(n)`; the *difference*
between two halves has twice the full sample's standard error, so its floor is exactly
`2 ×` the full floor. Using the tournament's own stored block-bootstrap floors:

| Arm | 1st half | 2nd half | post-GFC | 2nd-half floor | post-GFC floor | 1H−2H | its floor | resolved? |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `proposal_rsst` | +4.80 | −0.30 | −1.20 | 5.51 | 5.61 | 5.10 | 7.79 | **no** |
| `stacked_heavy_50` | +7.81 | +0.67 | −0.41 | 6.77 | 6.88 | 7.14 | 9.56 | **no** |
| `fund_overlay_30` | +3.21 | −0.90 | −2.00 | 5.47 | 5.56 | 4.11 | 7.72 | **no** |
| `proposal_no_trend` | +1.24 | +0.32 | +0.41 | 1.02 | 1.04 | 0.92 | 1.45 | **no** |
| `repo_evidence_led` | +0.68 | −0.25 | −0.15 | 1.16 | 1.18 | 0.93 | 1.64 | **no** |

**Nineteen arms, nineteen unresolved era differences.** Every one of the twelve
trend-bearing arms' post-GFC gaps sits between 3.5 and 7.5 floors inside noise. The era
table is a table of nineteen numbers none of which this design can distinguish from its
own full-window estimate, and it was read as if it distinguished all of them.

**The asymmetry is the finding.** `proposal_no_trend`'s post-GFC gap is +0.41 against a
floor of 1.04 — the tilt arm is `unresolved` on the last seventeen years by exactly the
standard applied to trend, and its first-to-second-half decay (+1.24 → +0.32, a fall of
74%) is proportionally *larger* than the difference between the trend arm's halves as a
share of their own floors. The session read one era table as evidence of decay and the
other as evidence of persistence. Neither is either.

*Assumption stated:* the sub-period floors above scale the full-window floor by
`sqrt(n_full / n_sub)`, which assumes the gap's volatility is constant across eras. Where
it is not, the floor is larger in the volatile era and smaller in the quiet one; the
1990s–2000s were the volatile half for every trend-bearing arm, which cuts against the
session's reading rather than for it.

### 3. The published detection floors use a different inference basis from the intervals beside them

**Decision moved: whether the tilt result is resolvable in a human holding period.** The
tournament's intervals are stationary block bootstrap, mean block 12 months — the right
choice for autocorrelated monthly gaps. Its **MDE is the i.i.d. `sd/sqrt(T)`**. Both are
computed and both are stored in the run artifact
(`mde_80pc_power_pp_yr`, `mde_80pc_power_block_bootstrap_pp_yr`). **Only the i.i.d. one is
published**, including in the headline.

| Arm | gap | MDE published | MDE block bootstrap | years published | years, bootstrap | status changes? |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `proposal_no_trend` | +0.79 | 0.47 | **0.72** | **13** | **30** | clears by 10%, not 68% |
| `wm_min_variance` | +1.61 | 1.29 | **1.81** | 16 | **32** | **stops clearing** |
| `wm_min_variance_shrunk` | +1.06 | 1.34 | 1.44 | 41 | 47 | no (already below) |
| `fund_cash_30` | +2.97 | 1.82 | 1.91 | 13 | 15 | no |
| `proposal_rsst` | +2.49 | 3.33 | 3.89 | 64 | **87** | no |
| `stacked_heavy_50` | +4.47 | 4.17 | 4.78 | 31 | **41** | no |

**Two of the three arms the tournament reports as separating from their benchmark do so
only under the narrower inference.** The min-variance arm loses the property outright. The
tilt arm — the recommendation's load-bearing result — clears by 0.07 pp/yr rather than by
0.32, and needs **thirty years of holding**, not thirteen. Its implied *t* falls from 4.73
to **3.05**, which is exactly the hurdle Harvey, Liu and Zhu propose for anything drawn
from the published factor family. A result that arrives precisely at the deflation
threshold is not a result that supports "the tilts are the only resolvable edge" without
qualification.

### 4. The placement line is +3 to +38 bp/yr, not +38 to +55, and is not contractual

**Decision moved: the largest single line in the recommendation.** The arithmetic in
[structural and tax edges](structural-and-tax-edges.md) §8 reproduces exactly — every
priority, the §901 credit cap, the two-bucket yield split, all twelve cells. I could not
break the calculation. What does not survive is what is booked from it.

- **The range is truncated.** §8.6 states plainly that one input decides whether placement
  is worth **6.5 bp/yr or 38**, and the ledger's own range column prints `+2.8 to +38.2`.
  The headline, the conclusion list and the `+38 to +55` bucket all use `+21 to +38` —
  bracket uncertainty only, with the entire *distributed* reading dropped. **−18 bp on the
  floor.**
- **94.7% of the +38.21 is one holding.** Decomposed by fund: RSST **+36.18**, IDMO +2.47,
  DFIV +2.12, VEA +1.87, AVES +1.40, IEMG +1.07, AVLV −3.51, VTI −3.39. The 36.18 is
  40.8% charged on 8.3% of NAV of *undistributed* controlled-foreign-corporation income
  from a single fiscal year with a 19.94% total return. A RIC shareholder is not taxed on
  undistributed investment-company taxable income; the page's own independent check
  (prospectus 17.17% pre-tax against 16.85% after tax on distributions, a 32 bp gap) is
  evidence *for* the distributed reading. Scaling that yield by 0.75 / 0.5 / 0.25 gives
  **+29.75 / +21.28 / +12.82** bp.
- **The `+14` for rebalancing inside the shelter is not incremental.** Under the pro-rata
  control every fund is two-thirds sheltered, so any rotation smaller than two-thirds of a
  position is *also* executable with no realisation. It is a property of having 66.7%
  shelter, not of optimising location. §8.6 concedes the plan makes rebalancing *harder*
  in one direction. **−14 bp.** It is also booked against §4's explicit instruction that
  the figure is "a hurdle, not a saving. Double count: not additive."
- **`+14` and `≤+2.8` are mutually exclusive.** Lot selection pays only on realised gains;
  the +14 is the value of realising none. **−2.8 bp.**
- **Three benchmarks are summed in one line**, two paragraphs after the same section warns
  that lines measured against different benchmarks are not added — the error
  [`aggregate()`](../../AGENTS.md) raises on.
- **The optimum may not be reachable.** It requires 30% of total net worth in RSST *inside
  the traditional account*. Traditional balances are typically employer plans with closed
  fund menus, and RSST/MATE/JPFP appear on none. That single line is 36.18 of the 38.21 bp.
  The page checks the Roth contribution phase-out and never checks whether the traditional
  account can hold the wrapper at all.
- **What is right, and worth recording:** the nominal-versus-after-tax objection is *not*
  present. Rebuilding the whole thing in after-tax dollars (traditional discounted at 24%)
  gives **40.88 bp of after-tax wealth against the published 38.21** — the nominal
  treatment is mildly conservative, because the saving accrues in the taxable account.

**Defensible range: +3 to +38 bp/yr, sensitive to a tax-character reading and to whether
the traditional account can hold the fund.** The claim that placement is worth more than
the overlay survives only at the top of that range.

### 5. Eighty-six per cent of the tilt edge is measured on the repository's shortest series

**Decision moved: how much weight the one "resolvable" conclusion can carry.** Stripping
each fund's non-market loadings from `proposal_no_trend` one at a time and re-running the
frozen tournament:

| Fund | contribution to the +0.79 | share | factor series |
| --- | ---: | ---: | --- |
| DFIV | **+0.328** | 41.6% | French Developed ex-US, from 1990-11 |
| IDMO | **+0.237** | 30.1% | French Developed ex-US momentum, from 1990-11 |
| AVLV | +0.128 | 16.2% | French US, available from 1963/1926 |
| AVES | +0.096 | 12.2% | French Emerging, from 1990-11 |
| VEA | +0.012 | 1.6% | |
| VTI | −0.011 | −1.4% | |

**US tilts contribute +0.125 pp/yr; non-US tilts contribute +0.683.** The 1990-start
problem the session named for trend applies with far more force to the tilts: the whole
non-US factor evidence in this repository is 427 months with **zero out-of-sample**, and
it carries 86% of the only result the session calls resolvable. The US value premium — the
one with a century of history — was **+2.16 pp/yr over this window with `t = 0.95`**, and
contributes about 10 bp.

Trend, by contrast, *can* be tested outside 1990–2026 and was not. Two independent
constructions using this repository's own frozen
[`time_series_momentum`](../../research/src/portfolio_edge/studies/time_series_momentum.py):

| Construction | window | n | mean | 95% | vol | Sharpe | *t* |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| 4 assets monthly (US equity, long govt, corporate, commodities) | 1929-01…2025-05 | 1,157 | +3.64 | [+2.34, +4.94] | 6.28 | **0.58** | **5.48** |
| — the same book, restricted to 1990-11…2025-05 | | 415 | +3.68 | [+1.56, +5.79] | 6.37 | 0.58 | 3.41 |
| — the same book, 1929-01…1990-10 | | 742 | +3.62 | [+1.95, +5.28] | 6.23 | 0.58 | 4.26 |
| 36 legs annual (18 JST countries, equity and bonds) | 1880…2020 | 141 | +1.65 | [+1.16, +2.14] | 3.80 | **0.43** | **6.59** |

**The tournament's window is not the problem for trend.** The Sharpe ratio of an
independently built book is 0.58 before 1990, 0.58 after 1990 and 0.58 over the whole 96
years — the 427-month window is representative, and the trend premium *is* resolvable
once the instrument is long enough (`t = 5.5` and `t = 6.6`). What the window cannot
resolve is the *portfolio gap*, which is a different estimand. Restated at AQR's 12.38%
volatility these give **7.18 [4.61, 9.75]** and **5.32** pp/yr — both above the 2.96
break-even, and the monthly book's entire 95% interval is above it.

*Charged and unflattering:* the own book runs 262% annual one-way turnover; at 20 bp
one-way its mean falls from 3.64 to 3.12 and its Sharpe from 0.58 to 0.50. Four legs
against a vendor's fifty-eight understates by the breadth identity; annual data with a
one-year lookback is a coarser signal than monthly. Read the two as a bracket.

### 6. The alpha-charging rule is dominated by the estimator it should have used

**Decision moved: whether the tilt result survives a hostile arm.** Two agents charged a
fitted alpha when its estimate exceeded its own detection floor. Exactly one fund
qualifies. That rule charges whatever was measured precisely and forgives whatever was
not — it conditions on the estimator's variance, not on the truth, and it takes a single
extreme estimate at face value at the exact moment the winner's curse is largest.

The standard alternative shrinks the whole cross-section by its own precision:
`tau² / (tau² + s_i²)` with `tau²` from moments. On the five measured `alpha − pedestal`
figures and their HAC standard errors:

| Fund | alpha | HAC se | keeps | shrunk | weight |
| --- | ---: | ---: | ---: | ---: | ---: |
| AVLV | −0.37 | 1.883 | 0.250 | −0.092 | 15% |
| **DFIV** | **−3.80** | 1.257 | 0.427 | **−1.624** | 10% |
| IDMO | +0.42 | 1.907 | 0.245 | +0.103 | 5% |
| AVES | −1.66 | 1.600 | 0.315 | −0.524 | 5% |
| VEA | 0.00 | 0.538 | 0.803 | 0.000 | 10% |

| Treatment | tilt gap | vs 0.47 (published floor) | vs 0.72 (bootstrap floor) |
| --- | ---: | --- | --- |
| charge nothing (the headline) | **+0.79** | clears | clears |
| **empirical-Bayes shrinkage, all funds** | **+0.60** | clears | **fails** |
| charge DFIV only (the threshold rule) | +0.42 | fails | fails |
| charge every measured alpha at face value | +0.30 | fails | fails |

**The threshold rule is *harsher* than the statistically defensible treatment** — and it
is harsher for the wrong reason, because it takes −3.80 whole while zeroing −1.66. Under
shrinkage the tilt result survives the published floor and fails the bootstrap floor; the
honest summary is that the tilt finding is fragile to the alpha treatment under **every**
inference basis except the pair the session happened to publish.

Two asymmetries make even that generous. **DFIV's −3.80 pp/yr is not credible as a fund
property** for a 27 bp index fund; it is far more likely absorbing a loading error, which
means it is evidence about the mapping rather than about the fund. And **the wrappers'
alphas were never measured**, so charging measured alphas charges only the tilt side and
gives RSST, MATE and JPFP a zero implementation shortfall by absence of measurement.

### 7. The market betas were measured, then discarded, and the specification says otherwise

**Decision moved: levels, not the ranking.** Experiment 016's specification states that
*"a market beta of 1.000 is an assumption everywhere: no market beta was measured for any
of these funds."* **That is false.** Every tilt fund's market beta was fitted, with a HAC
standard error, in Experiments 009 and 013, on the same French files with the same
`sha256`: AVLV 1.0137 (0.0274), DFIV 1.0547 (0.0261), IDMO 0.9540 (0.0385), AVES 1.1766
(0.0346), VEA 1.0498, VTI 0.9966. The betas were not unmeasured; they were unrepresentable
— `src/content/shelf.ts`'s `FactorLoading` union has no `"MKT"` member — and the
perturbation grid then protects them by name (`_MARKET_LEGS`).

Re-running the frozen tournament with the fitted values substituted:

| Mapping | `proposal_rsst` | `proposal_no_trend` | trend contribution |
| --- | ---: | ---: | ---: |
| β = 1.000 (published) | +2.486 | +0.790 | 1.697 |
| fitted market betas | +2.609 | +0.903 | 1.706 |
| AVLV's dropped RMW/CMA restored | +2.567 | +0.876 | 1.691 |
| fitted betas + every fitted leg the panel can carry | +2.684 | **+0.984** | 1.701 |
| fitted betas, each pushed 2 HAC se toward the control | +2.494 | +0.787 | 1.707 |

**The trend contribution moves by 0.016 pp/yr across all of it — the ranking is
invariant.** The tilt level moves over **+0.787 to +0.984**, a range of 0.197 pp/yr, which
is 42% of the published floor and 27% of the bootstrap floor. The direction matters: the
tilted funds have *higher* betas than the control, so about **11 bp of the +0.79 that an
investor would actually realise is market beta rather than tilt** — the β = 1 assumption
manufactures a beta neutrality the real funds do not have, and is conservative for the
level while being exactly wrong for the attribution.

Two coefficient sets were also silently truncated. AVLV's fitted RMW +0.074 and CMA +0.118
were dropped though the panel carries both legs. AVES's fitted SMB +0.367, RMW +0.267,
CMA +0.303 and UMD −0.176 were dropped because the emerging panel has no such series — the
emerging leg is *structurally* unable to carry its own fitted vector, and AVES is 12% of
the tilt result.

### 8. Ninety-eight per cent of the portfolio's active risk sits in one boutique fund

**Decision moved: a concentration nobody counted.** `proposal_rsst` runs 7.087% tracking
error against the cheap control; `proposal_no_trend`, the same portfolio with the wrapper
replaced by plain US beta, runs 0.999%. The wrapper therefore carries
`1 − (0.999/7.087)² = ` **98.0% of the portfolio's active variance** at 30% of its capital.

Under the placement optimum that 30% of total net worth sits in a **single ~$313m fund
from a boutique issuer, inside the traditional account**, whose N-PORT structure JPFP has
never filed and whose own sister page records that **13 of 25 managed-futures funds (52%)
filing at the window's open stopped filing within 6.5 years**. Issuer shares of the
proposal: Return Stacked 30%, Vanguard 30%, Avantis 20%, Dimensional 10%, Pacer 5%,
iShares 5%. The five-year closure and merger risk on 98% of the active risk is a cost that
appears in no arm, no floor and no fee table.

### 9. The whole resolvable edge is worth about three points of savings rate

**Decision moved: what the investor should spend attention on.** Nobody asked what any of
this is worth against the contribution rate, which is the one lever with no tracking
error and no detection floor. Solving for the constant monthly contribution that buys the
same terminal wealth as extra growth, at 10.8%/yr:

| Edge | over 30 years | over 36 years |
| --- | ---: | ---: |
| the tilt gap, +0.79 pp/yr | 2.57%/yr of the starting balance | **3.08%/yr** |
| placement at the top of its range, +0.38 | 1.17%/yr | 1.39%/yr |
| placement on the distributed reading, +0.03 | 0.09%/yr | 0.10%/yr |
| the stacked gap, +2.49 (unresolved) | 10.2%/yr | 13.0%/yr |

**The only conclusion in this recommendation that the data resolves is worth, over a full
career, about the same as raising the savings rate by three points of the starting
balance** — one budgeting decision, available immediately, certain, and with no fund risk.
That is not an argument against the tilts. It is an argument that the marginal hour of
this project has been spent on the smaller lever, and it is the comparison the charter's
reference investor should see beside every sleeve number.

*Read with its own caveat:* the equivalence depends entirely on the ratio of contributions
to balance. Early in accumulation the flow dominates by an order of magnitude; near the
end it does not.

### 10. The timing-rule verdict rests on the underpowered half of its own evidence

**Decision moved: conclusion 5's scope, not its direction.**
[Timing rules](timing-rules-on-the-equity-sleeve.md) reaches "no timing rule at any weight,
in any account" from a US test that is `unresolved` (+0.74 pp/yr, MDE₈₀ **3.03**) — while
its **JST pooled test, the only design on the page with resolution, finds the effect**
(+0.97 pp/yr, HAC *t* = 2.74, MDE₈₀ 0.99, 148 years, 16 countries). Two further
window mismatches: the −2.96 pp/yr after-tax cost is measured on 1990–2026 and juxtaposed
with a +0.74 pre-tax gap measured on 1926–2026, where the matched post-1990 pre-tax gap is
**+0.35 (t = 0.24)**; and roughly 0.73 of the "1.92 pp/yr tax cost of the rule" is the cost
of holding 27% in ordinary-rate bills and rebalancing monthly, which a static blend at the
rule's own average weight incurs **with no timing signal at all**.

The recommendation is probably still right — the overlap with the wrapper (ρ = 0.566) and
the deflation result carry it in the sheltered accounts, and the tax arithmetic carries it
in the taxable one. But the *verdict's scope* is set by the instrument that could not see,
not by the one that could.

## What I tried hardest to break and could not

- **That trend decayed after 2008.** It did, and it is not a vendor artifact. My own
  4-asset book runs Sharpe **0.87 over 1990–2008 and 0.17 over 2009–2025**; the JST book
  runs 0.55 pre-1990 and 0.19 over 1990–2020. Three constructions, three sources, same
  shape. What the century of data adds is context, not a rescue: the **1960s Sharpe was
  0.07** on the same book, and the decade that followed was 0.80. A fifteen-year dry spell
  has happened before and did not end the effect — which is why the decay is not
  resolvable, not why it is not real.
- **The vendor-cost objection to AQR's TSMOM.** I expected the gross-of-trading-costs
  index to flatter badly. On the only window where it can be checked, **live managed-
  futures funds net of their own fees returned +2.84%/yr against the index's +1.95%** —
  the funds beat the index. The 7.7 pp/yr CTA-bias scenario is well outside the measured
  interval. [Live managed futures](live-managed-futures.md) already says this and is right.
- **The basis mapping.** I expected β = 1.000 to be load-bearing. It moves levels by up to
  0.20 pp/yr and the ranking by 0.016. Attack 7 above is what survived; the rest failed.
- **The symmetric-haircut argument.** I expected that haircutting the value premium the
  way the session haircut trend would sink the tilts. It does not: realised US HML over
  1990–2026 was **+2.16 pp/yr (t = 0.95)**, *below* the repository's own pooled
  post-publication estimate of +4.74, so the "haircut" is an increase and the tilt gap
  rises from +0.79 to +1.14. On the US-only post-publication figure of +1.57 it falls only
  to +0.71. The tilt result does not depend on the US value premium — which is finding 5,
  arrived at from the other side.
- **Sequence-of-returns risk for an accumulating investor.** Recomputing every arm's
  terminal wealth with constant monthly contributions rather than a lump sum, the
  money-weighted advantage over the cheap control moves from +0.876 to +0.825 pp/yr for
  the tilt arm and from +4.440 to +4.170 for the proposal at contributions up to 2% of the
  starting balance per month. **The ranking is invariant to the contribution rate.** The
  accumulator objection is real for the *size* of the prize (finding 9) and empty for the
  *choice*.
- **The placement arithmetic itself.** Every priority, the §901 credit cap, the two-bucket
  yield split and all twelve cells reproduce exactly by hand. The foreign-tax credit is
  not double-counted. The pro-rata control is the right control. Finding 4 is entirely
  about what is booked from a correct calculation.
- **65/35.** Global cap weight is ~64% US on a single 2026-06-30 read, and the same page's
  own arithmetic puts a 10 pp shift at 14 bp/yr against 80–144 bp of tracking error —
  55 to 178 years to resolve. 65/35 is unfalsifiable here, and so is 60/40 and 70/30.
  This is the safest of the five conclusions precisely because nothing is being claimed.

## Which conclusions are unsafe

| # | Conclusion | Verdict |
| --- | --- | --- |
| 1 | Cut the wrapper toward 15–22%, possibly zero | **Unsafe.** Its decisive argument is a basis error (finding 1) and its supporting era argument is unresolvable (finding 2). Nothing here says 30% is right; the case for *any* particular direction is gone |
| 2 | The tilts are the only resolvable edge | **Overstated.** 30 years not 13, clears by 10% not 68%, *t* = 3.05 at the deflation hurdle, 86% of it on 427 months with no out-of-sample, and it fails under any alpha treatment other than zero |
| 3 | Placement beats the overlay, +38 to +55 bp contractual | **Unsafe as sized.** +3 to +38, not contractual, 95% of the top end on one fund's one-year CFC accrual in an account that may not be able to hold it |
| 4 | Keep 65/35 | **Safe, and empty.** Unfalsifiable at this resolution in either direction |
| 5 | No timing rule, no crypto, no tail hedge | **Right, scoped wrongly.** The timing verdict's scope is set by the underpowered instrument while the powered one finds the effect; the crypto verdict rests on 13 tail months, an interval-free down-beta and a drawdown order statistic the sister page disqualifies when it is inconvenient |

## Scope and limitations

- **Instrument:** all tournament re-runs use Experiment 016's frozen specification, its
  pinned source bytes and its own code paths, with mappings replaced in memory. The
  published central case reproduces to four decimals in every re-run, which is the check
  that the substitutions are the only difference.
- **Not registered.** No experiment file, no ledger entry, no promotion. This reviews
  finished work; it does not open a hypothesis. `run_kind` would be `exploratory` if it
  had one, and the look-ahead is total — every number here was chosen after reading the
  session's results.
- **The long-window trend books are lower bounds on breadth and upper bounds on
  cleanliness.** Four and thirty-six legs against a vendor's fifty-eight; no financing, no
  market impact, no capacity; annual data for JST with a one-year lookback. Costs are
  charged only in the sensitivity row.
- **The sub-period floors are scalings, not measurements**, and assume constant gap
  volatility across eras. Where that assumption fails it fails against the session's
  reading, not for it.
- **Empirical-Bayes shrinkage uses the raw HAC standard errors** from Experiments 009 and
  013 as proxies for the standard errors of the *pedestal-adjusted* alphas the tournament
  charges. The two differ; the pedestal is itself estimated, so the true errors are larger
  and the shrinkage stronger than shown.
- **The placement findings** are an independent re-derivation of §8's arithmetic and of
  what is booked from it. They are not a new tax measurement, and the character question
  (recognised versus distributed) is unresolved here as it is there.
- **Not examined:** human capital and job correlation; the operational cost of holding nine
  lines across three brokerages with partial shares and settlement; what happens if the
  investor stops contributing; estate and §1014 interactions beyond noting that the
  placement optimiser scores annual distribution drag only and never asks which asset
  should receive the step-up — a term §4 puts at 78 bp/yr at thirty years, 40× the
  boundary §8.5 does price.

## What would change these findings

1. **A stated prior on the trend premium with an interval**, arrived at without touching
   the 1990–2026 AQR file. Finding 1 exists only because the repository's forward premium
   is that file's own tail, on a different basis. The two independent constructions here
   are a start and are not a forecast.
2. **Publishing the block-bootstrap MDE beside the block-bootstrap interval**, or stating
   in one place why the i.i.d. floor is the right companion to a bootstrap interval.
   Finding 3 is a reporting choice, not a modelling error, and it is one line to fix.
3. **A market-beta field on the shelf.** Finding 7 is downstream of a TypeScript union
   with no `"MKT"` member; the numbers already exist in two committed artifacts.
4. **A pre-1990 international value or momentum series.** Finding 5 is currently
   untestable in this repository: nothing here can put DFIV's and IDMO's factor legs
   outside the single window they were measured on.
5. **Resolving RSST's tax character**, and checking whether a traditional account can hold
   the wrapper at all. Those two facts move finding 4's range from a factor of thirteen to
   something a decision can use.
