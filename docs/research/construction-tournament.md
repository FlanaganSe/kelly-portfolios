# The construction tournament

**Question.** Compared as whole portfolios rather than sleeve by sleeve, does the proposed
stacked, tilted construction beat a cheap cap-weighted control — and can this data tell?

**Current answer.** The tilts can be resolved and the stack cannot. Charging every cost
inside the rule, the proposal's factor tilts beat the cheap cap-weighted control by
**+0.79 pp/yr [+0.30, +1.32]** against a **0.47 pp/yr** detection floor, and they are
positive in all five predeclared sub-periods. The 30% stacked trend wrapper adds
**+2.49 pp/yr** against a leverage-matched control — but against a **3.33 pp/yr** floor,
which makes it `unresolved`, and **an investor would have to hold it for 64 years** before
this design could tell it apart from simply levering the index. The three stacked wrappers
span **0.15 pp/yr**, which is 5% of their own floor: RSST, MATE and JPFP are not
distinguishable here and the tournament should not be read as ranking them. Nothing is
promoted; [decision 0004](../decisions/0004-no-sleeve-promoted.md)'s non-promotion stands.

Evidence: [Experiment 016](../../research/experiments/exp_016_construction_tournament.yaml)
(spec `17e2cef1…`, run
[`492e28df…`](../../research/artifacts/492e28dfcb1d413b8c33a98ab0a6e034/summary.md), 20 arms)
and its follow-on
[016b](../../research/experiments/exp_016b_alternative_constructions.yaml)
(spec `705445e2…`, run
[`c49f8587…`](../../research/artifacts/c49f8587590d46cc9bf5ba8e389cbd0b/summary.md), 25 arms),
which adds four arms proposed **after** 016's results were seen and reproduces every shared
arm's point estimate exactly. Both are `exploratory`; this is a screening pass and cannot
promote anything.

## The one thing to read first

**Funds here are basis-mapped, not simulated from fund returns.** No research-grade fund
return series is committed ([decision 0002](../decisions/0002-no-research-grade-free-price-source.md)),
so every ticker is a linear combination of Ken French factor series and AQR's TSMOM, using
this repository's own measured loadings, less its own fee. The mapping is an assumption. It
is stated fund by fund in the specification, every gap carries the range it moves over a
27-point perturbation grid, and **a growth figure here is a property of a construction and
never of a fund.**

The trend leg is AQR's TSMOM: a vendor series, rebuilt in full on every update, stating no
cost basis anywhere, and therefore gross of the vendor's own trading costs by omission.

## Verified findings

All figures are after-cost annualised log growth gaps against the named benchmark, over
427 months (1990-11..2026-05). The three benchmarks are three families and their results are
never combined. `MDE` is this design's own minimum detectable effect at 80% power;
`years` is how long the arm would have to be held before that floor falls to the estimate.

| Arm | Benchmark | Gap | 95% interval | MDE | Years | Status |
| --- | --- | ---: | --- | ---: | ---: | --- |
| `stacked_heavy_50` (50% wrapper) | levered | +4.47 | [+1.26, +7.95] | 4.17 | 31 | unresolved |
| `proposal_ten_bp_wrapper` | levered | +2.77 | [+0.23, +5.67] | 3.33 | 52 | unresolved |
| `proposal_mate` | levered | +2.64 | [+0.20, +5.41] | 3.18 | 52 | unresolved |
| `proposal_jpfp` | levered | +2.61 | [+0.08, +5.52] | 3.33 | 58 | unresolved |
| `proposal_rsst` (the proposal) | levered | +2.49 | [−0.05, +5.39] | 3.33 | 64 | unresolved |
| `alt_idmo_swap_trend30` | levered | +2.38 | [−0.15, +5.26] | 3.49 | 76 | unresolved |
| `proposal_mate_prospectus_floor` | levered | +2.29 | [−0.34, +5.29] | 3.46 | 81 | unresolved |
| `proposal_rsst_216` (21.6% trend) | levered | +1.63 | [−0.67, +4.29] | 3.03 | 124 | unresolved |
| `fund_overlay_328` | levered | +1.61 | [−1.01, +4.55] | 3.69 | 186 | unresolved |
| `alt_idmo_swap_trend22` | levered | +1.56 | [−0.73, +4.23] | 3.20 | 150 | unresolved |
| `fund_overlay_30` (trend only) | levered | +1.36 | [−1.16, +4.23] | 3.56 | 244 | unresolved |
| `fund_overlay_216` | levered | +0.59 | [−1.65, +3.23] | 3.20 | 1033 | unresolved |
| `fund_overlay_103` | levered | −0.46 | [−2.40, +1.86] | 2.78 | 1280 | rejected |
| `fund_cash_30` | 70/30 cash holder | **+2.97** | [+1.67, +4.32] | 1.82 | 13 | exploratory |
| `fund_prorata_30` (same portfolio) | cheap index | +1.09 | [−1.18, +3.59] | 3.17 | 302 | unresolved |
| `proposal_no_trend` (tilts only) | cheap index | **+0.79** | [+0.30, +1.32] | 0.47 | 13 | exploratory |
| `repo_evidence_led` | cheap index | +0.23 | [−0.32, +0.83] | 0.57 | 216 | unresolved |
| `wm_min_variance` (walk-forward) | cheap index | **+1.61** | [+0.37, +2.90] | 1.29 | 16 | exploratory |
| `control_global_603010` | cheap index | −0.14 | [−0.36, +0.08] | 0.24 | 100 | rejected |

**Three of twenty-five arms separate from their benchmark by more than this design can
resolve.** Every stacked arm is `unresolved`. The full table, all five eras, the
perturbation grid, the haircut sweeps and the hostile arms are in the run artifact.

**1. The tilts are the only part of the proposal this data resolves.** Replacing the
wrapper with plain US beta at the same capital leaves +0.79 pp/yr at 1.0% tracking error,
which clears its floor, survives Benjamini–Hochberg at q = 0.10 (adjusted p = 0.010) and
never changes sign on the perturbation grid. It is positive in every era: **+1.24** first
half, **+0.32** second half, **+0.41** post-GFC, **+1.71** through the lost decade.

**2. The wrapper's whole contribution is pre-2008.** `proposal_rsst`'s gap by era:
**+4.80** first half, **−0.30** second half, **−1.20** in the post-GFC sub-period declared
in advance as the least favourable, **+7.76** through the lost decade. `stacked_heavy_50`
runs +7.81 / +0.67 / **−0.41** / +10.28 on the same splits. Every trend-bearing arm is
negative post-2009. A full-window figure for these arms describes 1990–2008 more than it
describes the future.

**3. The three stacked wrappers cannot be told apart.** RSST +2.49, MATE +2.64, JPFP +2.61.
The spread is 0.15 pp/yr against floors of 3.18–3.33. MATE's filed 2026-05-31 base leg
(1.1587, `delta` −0.159) versus its prospectus contractual floor (1.000, `delta` 0.00) moves
its own gap by 0.35 pp/yr — also inside the floor. JPFP has filed no Form N-PORT, so its arm
carries RSST's structure by assumption and differs from the RSST arm by its 40 bp fee and
nothing else, worth **12 bp/yr** on the portfolio by construction.

**4. The funding rule changes the answer without changing a holding.** `fund_prorata_30` and
`fund_cash_30` are the *same portfolio*: 70% of the cheap control plus 30% trend notional,
11.09 pp/yr of growth, −31.7% maximum drawdown, identical month by month. Against a
100%-equity counterfactual it is +1.09 and `unresolved`; against the counterfactual of an
investor who was holding 30% cash it is +2.97 and clears its floor. Separately, financing the
sleeve instead of selling the base is worth **+1.72 pp/yr** of growth at the same 30% trend
notional — 5.74 pp per unit of base not sold. The funding rule is a statement about a
counterfactual, and neither frame is the correct one.

**5. Among the six weighting methods, only long-only minimum variance clears its floor, and
the reason is not risk.** On the common walk-forward window (2000-11..2026-05, 307 months,
expanding estimation from a 120-month minimum, applied forward twelve months at a time),
against the cheap control: minimum variance **+1.61** (MDE 1.29), equal weight +1.38 (2.32),
equal risk contribution +1.29 (2.00), inverse volatility +1.25 (2.01), shrunk minimum
variance +1.06 (1.34), market weight +0.05 (0.03). **The minimum-variance arm has a *worse*
drawdown than the control (−54.5% against −52.7%), higher volatility (15.6% against 14.7%)
and triple the turnover (8.1%/yr against 2.6%).** Its weights swing from 70% US large value
at the first rebalance to 58% US market plus 28% international momentum at the last, and it
holds zero emerging market throughout. It won by avoiding developed ex-US, the worst
sleeve on the window, not by reducing risk.

**6. Growth wants more trend than variance does, and the two arguments disagree because
one of them needs the mean.** Four overlay arms on the same benchmark span the
variance-minimising notional's supported interval. Growth is **monotone increasing across
all of it and past it**: 10.99 pp/yr at a 10.3% trend notional, 12.04 at 21.6%, 12.81 at
30.0%, 13.06 at 32.8%, and 15.92 for the 50% stacked arm. There is no interior optimum in
the tested range, which means the growth argument returns a corner and therefore returns no
optimum at all. The variance argument's 21.6% uses only the equity–trend correlation; the
growth argument is a bet on TSMOM's gross mean. **They disagree because they are answering
different questions, and the disagreement should not be averaged away.** Note that the
leverage-matched control is exactly matched only to `proposal_rsst` at 1.3216× — the
low-trend overlay arms are compared with a benchmark carrying more leverage than they do, so
their *levels* are not fair leverage matches even though the *differences between them* are.

**7. The sleeve substitution another instrument prefers ranks below the proposal here, and
almost all of the difference is the trend cut rather than the swap.** Substituting US large
value for developed ex-US momentum plus cheap core, with trend cut to 22%, gives **+1.56**
(MDE 3.20) against the proposal's +2.49. Holding trend at 30% and making only the sleeve
substitution gives **+2.38** — so the swap itself costs **0.11 pp/yr** and the trend cut
costs **0.82**. Every one of those numbers is far inside every floor involved, so this is not
a disagreement the data resolves; it is a disagreement about the trend weight, which returns
to finding 6.

**8. A 10 bp wrapper instead of a 99 bp one is worth +0.28 pp/yr, and it is the only figure
here that is knowable in advance.** `proposal_ten_bp_wrapper` returns +2.77 against the
proposal's +2.49, matching the `0.30 × 0.89 = 26.7 bp` arithmetic. It is 8% of the arm's own
detection floor. No product on the audited shelf has been verified to charge it.

**9. Enlarging the family removed the only resolvable stacked result.** In 016,
`stacked_heavy_50` cleared its floor at Benjamini–Hochberg adjusted p = 0.081. In 016b, with
four more arms in the same family, the same point estimate and the same interval carry
adjusted p = 0.131 and the arm is `unresolved`. Nothing about the portfolio changed. **The
one stacked arm that looked resolvable was resolvable only at a particular family size**,
which is what a screening pass on twenty-odd correlated constructions should be expected to
produce.

**10. Linear shrinkage went all the way to its target at every rebalance.** The Ledoit–Wolf
intensity is 1.000 at all 26 estimations: over 120 or more months, the sample covariance of
seven near-collinear equity sleeves carries so little independent information that the
constant-correlation target wins outright. Relatedly, minimum variance fitted **in sample on
the whole window** returns +1.08 pp/yr — *less* than the walk-forward arm's +1.61. An
optimiser that knew the answer would not have done better, because it minimises variance and
the gap is a return outcome.

## Interpretation, and what it rests on

**Costs are inside the rule and are the smallest thing here.** Fees, the 62 bp equity-index
futures basis charged on futures notional (and charged to the leverage-matched control on
identical terms), and bid/ask spread on rebalancing turnover. The proposal's weighted cost is
39.7 bp/yr against the control's 3.7. Fee differences are exactly linear in the simulation —
the AVES sweep moves the proposal's gap by 0.73 bp for a 15 bp fee change at a 5% weight
against 0.75 bp predicted — so a wrapper at 10 bp rather than 99 bp would add
`0.30 × 0.89 = 26.7 bp/yr` **with certainty**, which is 8% of the arm's own 3.33 pp/yr floor.
That is the shape of the whole result: **the differences that are knowable in advance are
the cost differences, and they are the smallest ones on the table.**

**The tilt result is fragile to one number.** Charging every tilt fund its measured
`alpha − pedestal` — a hostile arm, since each figure sits inside its own detection floor —
takes `proposal_no_trend` from +0.79 to **+0.30**, below its 0.47 floor, and
`repo_evidence_led` from +0.23 to **−0.14**. DFIV's −3.80 pp/yr does most of that. The tilt
finding survives only on the assumption that those measured alphas are noise, which is what
their floors say and not what their point estimates say.

**The trend result rests on a vendor series' gross mean.** The proposal stops beating its
leverage-matched control once the trend leg loses **8.02 pp/yr** of arithmetic mean
(`stacked_heavy_50` 8.78, `fund_overlay_30` 4.60, `fund_prorata_30` 3.64). AQR's TSMOM
returned 10.98 pp/yr of arithmetic excess over this window, computed directly from the pinned
file (`sha256 33470930…3eeb`), so the break-even sits at **73% of the series' own mean** —
comfortable against a fee, and not obviously comfortable against unpriced vendor trading
costs on a book running several hundred percent of gross notional.

**Taxes are almost entirely not measured.** RSST is the only fund in the tournament with an
SEC-standardised after-tax table. Its incremental distribution drag of 4.5 bp at a 30% weight
moves the proposal's gap from +2.49 to +2.47. Every other after-tax cell reads `not measured`
and no default was substituted. Section 1256 marking, Cayman subpart F conversion and cash
creations are documented in
[capital efficiency](capital-efficiency-and-breadth.md) and are not priced here.

**Risk, for the charter's common core.** `proposal_rsst`: 15.0% volatility, −49.6% maximum
drawdown against the levered control's −66.8% and the cheap control's −52.7%, 39 months as
the longest run under water, `P(underperform over ten years) = 0.164` with a median shortfall
of −0.93 pp/yr when it does. `proposal_no_trend`: 14.7% volatility, −53.1% drawdown,
`P = 0.041`, median shortfall −0.14 pp/yr. Eight funds against two, 3.9% annual turnover
against 2.6%.

## Scope and limitations

- **Instrument:** basis-mapped constructions, not funds. Loadings from
  `src/content/shelf.ts` as of 2026-08-17, measured over 44–77 month fund windows and applied
  to 427 months. Market betas of 1.000 are assumed and were never measured.
- **Window:** 1990-11..2026-05, 427 months, set by Ken French's Developed ex-US momentum
  factor (starts 1990-11) and AQR's TSMOM (ends 2026-05). Neither boundary was chosen. The
  weighting-method arms are scored on 2000-11..2026-05 and their benchmark is re-measured on
  the same months; a 307-month gap and a 427-month gap are never put in one column.
- **Benchmarks:** a cheap 65/35 cap-weighted control, the same control levered to 1.3216×
  and charged the same financing, and a 70/30 equity-cash holder. Three families, never
  pooled, corrected within each by Benjamini–Hochberg at q = 0.10 — the correction a
  screening pass takes ([decision 0009](../decisions/0009-blocks-lifted-and-closures-rescoped.md)
  clause 2), not Holm.
- **Costs:** fees, equity-futures financing basis, rebalancing spread. Not charged:
  the vendor's internal trend trading costs, capital-gains tax on realisation, foreign
  withholding, market impact, and fund alphas outside the hostile arm.
- **Post-hoc arms:** 016b's four new arms were chosen after 016's results were inspected.
  That is recorded in its freeze note, in the ledger and here, and it is why 016 was not
  amended ([decision 0010](../decisions/0010-bars-carry-a-reopening-condition.md) clause 4).
- **Leverage matching is exact for one arm only.** The levered control is set to
  `proposal_rsst`'s 1.3216× gross notional. Arms at 1.10× to 1.55× are compared against it
  anyway; their levels carry that mismatch and only their differences from each other do not.
- **Not measured:** any defensive sleeve. This tournament holds no bonds, no
  duration-hedged credit, no gold and no cash beyond the one funding arm, so it cannot
  adjudicate substitutions inside a defensive allocation.
- **Inference:** stationary block bootstrap over the joint panel, whole rows, mean block 12
  months, 10,000 resamples. Intervals at mean blocks of 6 and 24 months move the headline
  figures by under 0.2 pp/yr.
- **The look-ahead no design here removes:** the candidate weights, the fund list and the
  loadings were chosen by people who had already read fifteen experiments on this same data.
  `run_kind: exploratory` records that, and no re-run converts it.

## Consequence for the decision

The tournament reframes the question. It does not say the proposal is wrong; it says that
**the proposal's central claim is unobservable over a human investing horizon** — 64 years to
distinguish the stacked construction from levering a cheap index, 244 years for a pure trend
overlay at 30%, 1,033 years at 21.6%. When the ranking is a ranking of expected values whose
differences cannot be observed by the person holding them, the decision is not "which is
best" but **which is best-supported and cheapest to be wrong about**. On that question the
tournament is clear:

- the tilt component is supported, cheap (10.0 bp), low-tracking-error (1.0%), positive in
  every era, and costs 0.49 pp/yr if its measured alphas turn out to be real;
- the stacked-wrapper component is unsupported *by this instrument*, costs 30 bp/yr more,
  contributes 6.1 percentage points of the 7.1 points of tracking error, is negative in the
  post-2009 sub-period, and is indifferent between the three products on offer;
- the choice among RSST, MATE and JPFP should be made on the things that are actually
  known — filed structure, fee, age, size, survival and tax placement — because the return
  evidence cannot separate them and will not in this investor's lifetime; the largest
  knowable difference available is the fee, and an 89 bp saving is worth 27 bp/yr with
  certainty against a 333 bp/yr floor of uncertainty.

The trend *weight* is the live question and this tournament does not settle it. A variance
argument puts it near 21.6%; this growth argument runs monotonically to the top of the tested
range and therefore names no optimum. The investor's 30% sits between them. Neither instrument
can distinguish 22% from 30% from 33%, and the era table says the last seventeen years would
have preferred none of them.

The one arm that came closest to clearing its floor at a large weight, `stacked_heavy_50`,
is also the one whose post-GFC gap is negative and whose whole margin comes from a vendor
series' gross mean — and it lost even that standing when four more arms joined its family.
It is a reason to test the trend leg harder, not a reason to hold more of it.

## Next informative tests

1. **The trend weight, framed as regret rather than as an optimum.** The growth argument
   returns a corner and the variance argument returns an interior point; the useful next
   design is neither, but a regret surface over the trend weight against a stated prior on
   TSMOM's mean, since that prior is the entire disagreement.
2. **A defensive arm.** Substitute duration-hedged credit, short Treasuries and T-bills
   *within* a defensive allocation and let the tournament adjudicate, which a sleeve-by-sleeve
   test cannot. This needs a new frozen specification: Experiment 016's spec must not be
   amended after its results were inspected
   ([decision 0010](../decisions/0010-bars-carry-a-reopening-condition.md) clause 4).
3. **An independent trend construction.** Every trend figure here inherits AQR's gross mean
   and its 8.02 pp/yr break-even. Contract-level futures data with point-in-time rolls would
   replace the largest unpriced item in the result.
4. **A market-beta measurement for the mapped funds.** Every mapping assumes β = 1.000 and
   none was measured. It is the cheapest way to shrink the mapping error that clause (e) of
   the falsifier exists to police.
5. **Loading stability.** The tilt finding applies 44–77 month loadings to 427 months. If
   loadings drift, +0.79 pp/yr is an upper bound on a quantity nobody has estimated.
