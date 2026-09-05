# Current portfolio position

**Question.** Given the evidence now held, what is the best-supported implementable
portfolio for the reference US investor, and which inputs or new evidence would change it?

**Status.** Working decision, not proof of an optimum and not personalised advice. Fund
facts are volatile and the typed client content is the current source for tickers, fees,
dates, and citations. No sleeve is `production-eligible`, and no construction is claimed to
beat a cheap index with near certainty.

## Current answer

Use a low-cost diversified equity core, decide the defensive allocation from the
withdrawal path and the ability to persist rather than from a return forecast, place
holdings and tax lots deliberately, size any financed sleeve against holdability rather
than against a growth optimum, and keep the operating procedure simple enough to follow
for thirty years.

This is a decision tree, not one universal set of weights:

1. **Set the feasible equity exposure.** Expected growth alone generally pushes the
   reference scenario toward a corner. Withdrawals, liabilities, job risk, drawdown
   tolerance, and behavior decide what can actually be held. See
   [setting the equity share](setting-the-equity-share.md) and
   [leverage and the notional budget](leverage-and-the-notional-budget.md).
2. **Choose the cheapest adequate core.** Broad US and international equity plus the
   investor's chosen defensive assets are the control. The evidence does not identify a
   reliably superior US/global split; a cap-weighted split is already the market portfolio
   and needs no defence. See [valuation and the allocation](valuation-and-the-allocation.md).
3. **Take implementation gains that actually apply.** Fee savings, account placement,
   foreign-tax-credit treatment, lot selection and contribution-directed rebalancing can
   improve the investor's own counterfactual. Their total is smaller than the sum of their
   headline figures, because those figures are measured against different benchmarks and
   do not add. See [structural and tax edges](structural-and-tax-edges.md).
4. **Consider optional sleeves only after the core is specified.** Price their marginal
   contribution under the actual funding rule, costs, tax and tracking error. A financed
   overlay and a sleeve funded by selling the core answer different questions, and the
   difference is larger than any premium this programme has measured.
5. **Precommit maintenance.** Rebalance to control exposure using cash flows where
   practical. Do not book a stable rebalancing premium. Define review triggers on evidence
   and on a calendar, never on price. See [rebalancing policy](rebalancing-policy.md).

## The comparator decides the answer, and it decided several of them

Three recurring questions use different benchmarks and their answers do not add: whether a
construction beats a cheap index, whether it improves the investor's own counterfactual,
and whether it reduces mistakes relative to typical behavior.

This is not a methodological preamble. It is the single most common way a result in this
repository has turned out to be wrong.

- The construction tournament's verdict on a financed trend overlay **reverses on the
  assumed equity premium, not on the assumed trend premium**, because a leverage-matched
  benchmark holds 132% equity notional against the candidate's 67% and a lower equity
  premium charges the benchmark about twice as hard
  ([tournament](construction-tournament.md), exp_016d).
- The same overlay's minimax-regret weight is **0.36 against the investor's own portfolio
  and 0.12 against a leverage-matched control**. The disagreement is a choice of
  comparator, not a measurement ([trend weight](trend-weight-under-uncertainty.md)).
- An implementation budget assembled by summing lines measured against a cheap index, the
  investor's counterfactual and typical behavior overstates what any one investor can
  capture ([adversarial review](adversarial-review.md), finding 4).

## What is relatively dependable

The strongest claims are contractual or arithmetic:

- lower fees improve the investor's own counterfactual when the current holding is more
  expensive and exposures are comparable;
- taxes depend on account, wrapper, lot, holding period, and realization path;
- a factor tilt's expected line is `weight × (fund loading − incumbent loading) × premium
  − cost`;
- a loading and a long-only capture fraction are alternate measures of exposure and must
  not be multiplied;
- a wrapper's structure enters exactly once, through `delta = (1 − b)/d`, and the funding
  rule can dominate the apparent value of a diversifier;
- stacking sleeves that are correlated has a ceiling: `P(stack ahead) → Φ(z₁/√ρ)`, so at
  the ρ = 0.435 measured among this portfolio's own value tilts, an unlimited stack of
  55%-likely sleeves reaches 0.576 ([stacking](stacking-and-effective-breadth.md));
- under substitution funding, portfolio edge is a weighted *average* of sleeve edges and
  is therefore bounded by the best single sleeve; under a financed overlay it is a *sum*.

## The final construction, tested as one object

**Two weight vectors appear in this repository and only one of them is published.** The
recommendation is **RSST 30 / VTI 19 / VTV 15 / VXUS 16 / AVDV 10 / IDMO 5 / AVES 5**
(`as of 2026-09-01`, unchanged by the September review), 38.2 bp of weighted fee and 36.2 bp of
weighted net cost, derived in [part A](portfolio-for-one-investor.md) §2 and rendered on
`/portfolio`. Gross notional is 1.322× on the 1.072 RSST equity leg the shelf carries and
1.315× on the 1.050 its 2026-04-30 Form N-PORT supports (part A §1). The construction
Experiment 016e scored is the **same seven funds at RSST 25 / VTI 24**, 1.268× gross, 33.4 bp
of fee and 31.3 bp of net cost — the recommendation as it stood when that specification was
frozen. Experiment 016f has since scored the seven funds at 30% directly
([run `36f14b39…`](../../research/artifacts/36f14b395e53407f8fdfaee3b4e8e37a/summary.md)):
+2.50 pp/yr [−0.15, +5.26] against the levered cheap control and a 3.38 floor, `unresolved`
exactly as the 25% arm is. The 25%-arm figures below carry over to it.

Experiment 016e ran that construction through the frozen tournament machinery, with
`unresolved` predicted in the specification before the run.

Against a cheap index levered to the same 1.268× and charged the same financing, the
25% arm reads **+2.20 pp/yr [+0.05, +4.57] against a 2.83 floor** — unresolved,
and 59 years of holding before the design could see it. Tracking error 6.0%; drawdown −50.3%
against the levered control's −64.6% and the unlevered cheap index's −52.7%. The probability
of trailing depends on the comparator and the premium, and the three readings belong on one
line: 15.6 / 7.1 / 3.4% at 10 / 20 / 30 years against the cheap index at the realised premium
with the edge treated as known (median shortfalls −0.79 / −0.46 / −0.30); 25.3 / 16.7 / 11.5%
against the same index at the forward prior's median; and 69.5 / 76.5 / 80.2% against the
leverage-matched control, the comparator this page calls load-bearing
([trend weight](trend-weight-under-uncertainty.md) §6).

**The candidate constructions cannot be told apart.** Recommended +2.20, the AVUV variant
+2.35, the previous recommendation +1.92, the investor's original +2.49 — a spread of 0.57
inside floors of 2.75–3.33. Fund selection among reasonable tilts is below this design's
resolution, and a page that ranks them is reporting noise.

**Investor-supplied equivalents are equivalents, not errors** (016f, 427 months, basis-mapped
funds). VEA 11 + IEMG 5 in place of VXUS 16 reads +0.05 pp/yr [+0.00, +0.10] against a 0.07
floor, `unresolved`, at the same blended headline fee. AVLV in place of VTV reads −0.01 [−0.06,
+0.05] against 0.09, at 12 bp more net cost (14.94 against 2.70). DFIV in place of AVDV reads
−0.10 [−0.29, +0.10] against 0.26; DFIV's −3.8 fitted alpha is unexplained, and AVDV delivers
small and value at 4% turnover. One label is wrong: the investor's "AVLV (SCV US)" names a
large-cap value fund. AVUV is the small-cap value fund, and it reads +0.15 [−0.34, +0.67]
against VTV at a 0.67 floor. None of these separates from the published vector.

**Two comparisons do resolve, and they are the useful part.**

1. **The 30% arm minus the 25% arm is +0.51 pp/yr [+0.30, +0.72] against a 0.31 floor**
   (016f, the matched pair 016e's open question 4 asked for). 016e's −0.50 between the 25% arm
   and the investor's original eight funds was **all wrapper weight**: the two fund lists at
   the same 30% differ by +0.01 [−0.18, +0.19] against a 0.26 floor. It is a *leverage* result
   at the panel's realised premium — the pair's break-even trend haircut is 10.08 pp/yr, and at
   the 4.07 forward premium the same pair reads about +0.18 against its 0.30 floor. It is the
   number behind the published 30%. It resolves at the realised premium and not at the
   forward one, so the trade is stated to the investor as a choice, below, rather than
   resolved on their behalf.
2. **The tilt complex alone beats the cheap index by +0.80 pp/yr [+0.36, +1.31] against a 0.47
   floor on i.i.d. inference and a 0.72 floor on matched HAC inference, where the horizon is
   30 years rather than 12; shrinking the fitted alphas takes it to +0.60, which fails the
   matched floor.** This reproduces Experiment 016's +0.79 on a different fund list, which is
   independent confirmation rather than a restatement; the qualifications are in *Optional
   factor tilts* below and are not repeated. **It now has an out-of-sample window** (Experiment
   023, [final construction](final-construction-test.md) §1b): the same complex on AQR's
   Value and Momentum Everywhere basis over 1981-07…1990-10, a window disjoint from every
   series it was chosen on, reads **+0.89 pp/yr [+0.44, +1.34] against a 0.65 HAC floor**,
   both halves positive, developed value carrying +0.54 of it, with the developed small-cap
   half of AVDV unmapped and therefore biasing the figure down. On the same basis the
   1990–2026 window reads +0.40 against 0.62, so the sign reproduces and the size does not.

**AVDV's addition reads +0.28 pp/yr [+0.05, +0.56] against a 0.29 floor** — short of resolution
by 0.01, and positive in every sub-period. The unlevered tilt-only pair gives +0.29
independently.

**Net cost after securities lending is now read from 50 fiscal-year Form N-CEN filings, and no
fund on the tilt shelf has negative net cost**: VTV 2.70 bp, SPMO 12.93, AVLV 14.94, IDMO
22.59, AVUV 24.54, AVES 29.21, AVDV 30.03, RPV 33.87. The VTV-versus-AVUV gap is 21.8 bp on
cost against 22 bp on fee, so the fee-based conclusion stands. The one correction favours the
strongest recommendation: AVDV costs 30.03 bp, not its 36 bp headline.

**RPV remains unattractive under the declared factor-and-cost scenarios; SPMO's role is
unresolved.** The earlier return figures for these funds multiplied residual appraisal
alpha by purchase weight, which does not measure a funded change in portfolio return.
The corrected [tilt calculation](untested-tilt-candidates.md) separates those quantities.
RPV's deeper value loading comes with negative profitability and momentum loadings and
higher modelled trading costs. SPMO's lower filed fee and turnover than MTUM make it a
candidate for a whole-portfolio comparison; correlation with IDMO is a diversification
input, not a deduction from a fixed purchase's expected return.

**ITAN's factor-and-cost case also remains negative under the four declared scenarios.**
Its −0.10 pp/yr headline was a weighted residual appraisal diagnostic, not a funded
portfolio-return estimate. Its negative profitability and momentum exposures and its fee
remain relevant, but a growth claim requires the whole funded portfolio to be tested.

## Optional financed trend

Trend remains the leading diversifier candidate, and the case is stronger than this
repository stated for most of its history. Four independent routes now bracket the weight:

| Route | Weight | What it optimises |
|---|---|---|
| Variance minimisation, `w* = −ρ σₑ/σ_d` | 21.6%, interval [10.3, 32.8] | portfolio variance |
| Growth subject to holdability | 20–30%, centre 25% (corrected 2026-09-02; the earlier 15–25% read the retracted 1.80% row) | after-cost log growth |
| Regret over an explicit premium prior | 25%, robust 20–30% | maximum regret, then capitulation |
| Construction tournament | no interior optimum | growth against a leverage-matched control |

**Every route admits 25%, and after the correction every route admits 30% as well.** The
tracking-error route was described here as premium-free. It was not: its central row was the
retracted 1.80% figure, and at the corrected 4.07 it reads a worst relative run of −15.7% over
188 months and an 8.7% thirty-year probability of a −20% relative run at 30%, doubling to
18.2% at 35% ([leverage](leverage-and-the-notional-budget.md) §6a, §9). Nothing in the
corrected growth arithmetic argues below 0.28 on the investor's own benchmark under any
reweighting of the premium prior. The one route still arguing below 30% is the
CAPE-conditioned drawdown ladder, 19.1% at a −50% tolerance, and it terminates in a
tolerance the investor has not supplied.

Experiment 016f then ran the matched pair: **the 30% arm beats the 25% arm by +0.51 pp/yr
[+0.30, +0.72] against a 0.31 floor**, the only whole-portfolio comparison here that clears its
own resolution, and a leverage result at the realised premium. What it does not settle is
whether the investor can hold a sleeve through a decade in which it contributes nothing while
equities rise — abandonment probability runs about 17% at the median at 30% against 11% at
25%, and 66.7% at 30% if the premium is gone entirely. A contribution stream does not change
those figures: at 5, 10 or 15%/yr of starting capital the median reads 17.6 to 17.8% and the
no-premium case 63.3 to 64.9% ([trend weight](trend-weight-under-uncertainty.md) §4).

**On 96 years the overlay clears its floor at the top of a bracket and not at the bottom.**
Experiment 018 ([run `311048fb…`](../../research/artifacts/311048fbc6b44072a3715ff24d1507a4/summary.md),
`exploratory`) put a 70% US-equity core plus a 30% RSST-like wrapper on a 1929–2025 panel,
with the repository's own 4-asset trend book scaled to 12.38% volatility as the trend leg. It
beats the cheap 100%-equity control by **+1.98 pp/yr [+1.26, +2.73] against a 1.06 floor** and
a volatility-matched control by +1.79. The adversarial re-run brackets it: +1.67 with 20 bp
one-way trading cost on the book's 262% turnover, +1.31 with a one-month signal lag, +0.91
unscaled (floor 0.54); at RSST's filed 0.681 loading, +1.30 / +1.08 / +0.84 against the same
1.06 floor. Sub-windows from 1934, 1946, 1970 and 1990-11 read +2.04 / +1.86 / +2.17 / +1.84
against floors of 1.08–1.78; from 2009, +0.37 against 2.2. Against the leverage-matched
control the arithmetic mean is behind (−0.30) but that control draws down 92–97%; on log
growth the construction leads by +0.88 over the full window. This is the strongest
portfolio-level evidence for the overlay the repository holds; it is US-only, the trend leg
is a construction rather than a fund, and it promotes nothing. The defensive arms run beside
it are in [defensive engines in the construction](defensive-engines-in-the-construction.md).

**The choice between 25% and 30% is the investor's, and it turns on one input.** The
argument that a contribution stream carries the position through a drought was tested and is
withdrawn: contributions dilute the edge and the deficit alike and move abandonment by under a
point. What remains for 30% is that every route now admits it and the matched pair prefers it
at the realised premium. What remains for 25% is the same pair at the forward premium and the
drawdown ladder, which at any stated tolerance of −60% or tighter puts the wrapper at 23.7% or
below; an investor who supplies no tolerance is holding the ladder's loosest row, near −70%.
A portfolio held beats a better one abandoned. State the trade; do not resolve it silently.

Three things to hold onto:

- **The forward premium this repository asserted at 1.80 pp/yr was never measured.** It is
  the 2012–2025 subsample's own geometric mean less a fee, restated onto a gross arithmetic
  axis as 4.17%; a verdict built on it inherited a units error rather than a finding.
- **Zero is the worse extreme.** Over the panel's one flat-to-negative equity decade
  (1999-03…2009-02, equity −2.55%/yr) a 30% overlay contributed roughly **+9.5 pp/yr above
  its own complement** and turned that decade from −2.55%/yr to about +0.05%/yr. It removes
  the lost decade rather than softening it. Against +0.21 pp/yr in ordinary decades, this is
  the state that decides whether a plan survives.
- **Holdability and return are a bet on the same parameter.** Abandonment probability at a
  30% weight is 66.7% if the premium is gone and 17.2% at the median. That is the same risk
  twice, not a diversification of it.

The case remains suggestive, not promoted. Trend's post-2008 decay is real and
independently confirmed on constructions the vendor never touched; it is also not
resolvable, and the 1960s ran a Sharpe of 0.07 before an 0.80 decade.

## Optional factor tilts

Long-short research series show stronger post-publication evidence for value and momentum
than for size, profitability or investment on the tested panels. That is the first layer of
the evidence chain, not an investable return forecast.

The tilts are the part of a stacked construction that the tournament can resolve — **+0.79
pp/yr at 1.0% tracking error, positive in all five eras, no sign change across a 27-point
perturbation grid, at 10 bp of fee.** Three qualifications belong in the same breath:

- the published detection floor of 0.47 used i.i.d. inference while the interval beside it
  used HAC; on matched inference the floor is **0.72 and the horizon is 30 years, not 13**,
  and the implied *t* of 3.05 sits exactly on the Harvey–Liu–Zhu multiple-testing hurdle;
- **86% of the measured edge comes from the repository's shortest series**, developed
  ex-US and emerging panels starting 1990-11; the 1981–1990 out-of-sample window in
  Experiment 023 now carries the sign on a different basis, at a size the 112 months cannot
  pin down;
- charging fitted alphas moves the result from +0.79 to +0.60 under empirical-Bayes
  shrinkage and to +0.30 charged raw. The threshold rule used elsewhere in this repository
  is harsher than the defensible estimator, and it charges only the side whose alphas were
  measured.

**The developed-ex-US value result was a property of its window.** On the 55 months DFIV and
AVIV impose, the large-cap developed-ex-US value funds read −2.3 to −2.9 pp/yr; on IVLU's and
EFV's 78 months they read −1.0 and −1.7 with neither interval excluding zero, and AVDV's and
DFIV's plain returns differed by −0.30 ± 5.16 pp/yr. A tilt is chosen on delivered exposure,
cost, turnover and overlap, which the data resolves, rather than on a measured excess return
it does not.

Before using a tilt: measure delivered loading relative to the incumbent being sold,
subtract product costs, turnover, tax and implementation shortfall, use a comparator
capable of expressing the admitted exposure, and price the tracking error and the time the
edge needs to become observable.

## Breadth is not ticker count

Counting return engines rather than tickers is a charter principle; it is now also a
measurement.

- An eight-line portfolio of the kind considered here carries **3.71 effective independent
  active sleeves**, and three of its lines carry no active position at all.
- **Geography is nearly free breadth; style is real breadth.** One factor across three
  regions is worth 1.35–1.55 of 3; five factors inside one region is worth 5.52 of 5. An
  international allocation may be right on currency, valuation, home-bias or regret
  grounds. It should not be defended as diversification.
- Concentration of *active* risk is easy to miss: a single boutique sleeve can carry the
  overwhelming majority of a portfolio's active variance while looking like one line of
  eight, in a category where 52% of filers stopped filing within 6.5 years.
- **In a crisis the breadth shrinks and no sleeve turns against the book.** In the worst
  decile of US equity months (42 of 422, 1990-11…2025-12), no active sleeve has a negative
  mean; the three value tilts converge (AVLV–DFIV correlation 0.57 → 0.81, AVLV–AVES 0.32 →
  0.64) and IDMO–trend rises 0.45 → 0.64, so effective bets fall from 3.71 to 2.7–2.9, with
  intervals that overlap 3.71 in three of four conditions. Trend's conditional mean is +2.84
  pp/month on the vendor series, whose honest interval under a joint block bootstrap is
  [+0.70, +4.37]; +1.94 [+0.23, +3.65] on the repository's own book; and about +0.58 pp/month
  at RSST's delivered loading and a 30% weight, against equity's −7.9. In calendar 2022 on the
  own book, trend did not cover a stacked bond leg's loss (−21.3% against the reference's
  −18.8%); on the vendor series it did.
- **Stacking works only for financed, low-correlation engines.** Under substitution the
  portfolio edge is a weighted average bounded by the best sleeve; under a financed overlay it
  is a sum, and the tail correlation is higher than the average. This portfolio finances one
  engine and substitutes four tilts, which is why it has one financed leg and why more tilts,
  a second momentum fund, or a gold or bond stack do not add
  ([stacking](stacking-and-effective-breadth.md)).
- **Cross-asset carry is the one second engine that adds as a sum, and it is not added by
  default.** It correlates +0.06 with the trend book on a century and +0.07 in the worst
  decile of equity months. A 10-point RSSY-like stack reads +0.58 pp/yr [+0.28, +0.86] against
  a 0.35 floor on the gross vendor series at full loading, +0.22 against 0.35 once a 2 pp/yr
  trading-cost haircut and a 0.681 delivered loading are charged, −0.41 since 2013, and the
  substitution of carry for half the trend leg is negative on both panels. RSSY is 27 months
  old and behind. For an investor who wants it anyway: 10 points from VTI, in shelter, at
  about 6 bp/yr of placement cost ([carry](carry-as-a-second-engine.md)).

## Valuation, taken into account

`as of 2026-08-31`. US CAPE 41.7; 10-year TIPS real yield 2.44% (96.7th percentile since
2003), 30-year 2.99% (99.8th since 2010); TIPS-based excess CAPE yield −0.01 pp on the daily
read, the first sub-zero print in the 23-year record and the 0th percentile of 284 months for
a fifth month. Six managers' 2026 ten-year US large-cap expectations run 3.3% to 9.0% nominal;
four of six put the equity premium over TIPS between −2.2 and +1.5 pp/yr. Those are inputs,
displayed and never sized on
([decision 0012](../decisions/0012-valuation-enters-through-the-drawdown-assumption.md)).
What the repository's evidence licenses ([valuation](valuation-and-the-allocation.md),
[current regime](current-regime-and-pricing.md)):

1. **No timing rule on the CAPE level.** −9 bp/yr gross and −86 bp net over 1921–2026;
   out-of-sample R² negative at every horizon since 1990, too pessimistic by 4–8 pp/yr.
2. **A wider drawdown assumption.** Entries above CAPE 30 ran a median −51.8% real
   fifteen-year drawdown with 59.7% of months under water, on 0.32 independent observations.
   Routed through the notional budget, that supports a wrapper of 14.9% / 19.1% / 23.7% at a
   −40% / −50% / −60% stated tolerance; the current book implies a tolerance near −70%. The
   investor has not supplied the number; `/portfolio` asks for it and shows the ladder.
3. **The excess-CAPE-yield rule (k = 0.4)** is the one valuation rule with a positive record,
   and it is now registered (Experiment 022, `exploratory` because k was chosen on this data;
   [valuation](valuation-and-the-allocation.md) §3.3). Against a constant mix at the rule's
   own mean weight it reads **+0.63 pp/yr [+0.26, +0.99] against a 0.42 floor** on 1921–2026,
   ahead in 99.9% of rolling 30-year windows drawn from 2.5 independent blocks, wrong sign in
   1980–2000, and **+0.37 [−0.09, +0.83] against 0.49 since 1990-11, unresolved**. Against
   100% equity it is **−0.67 [−1.50, +0.16]**, a drawdown purchase priced at the premium:
   the position it takes today, about 85/15, gains 31 bp/yr in log growth if the forward
   equity premium over bonds is zero, 8 bp at 1.5, and costs 14 bp at 3 and 44 bp at 5, with
   break-even near 2 pp/yr. It is admissible in the traditional third and not adopted by
   default. Applied there, the only line that funds it is the wrapper: **RSST 30 → 24.8, a
   ten-year Treasury or TIPS 5.2**, no taxable line moved, gross 1.32 → 1.27, which is the
   25% arm every route admits plus a 5-point defensive line. That is the vector for an
   investor who wants the August 2026 valuation to move a point of the portfolio, and
   [part A](portfolio-for-one-investor.md) §7 takes it as the working default for the
   reference investor, who has stated that concern and no tolerance. The published
   construction stays the 30% vector, which is the same book at a tolerance of −70% or looser.
   The default is scored as one object (Experiment 024, part A §7): against the published
   vector it reads **−0.64 pp/yr [−0.87, −0.40] against a 0.33 floor on 96 years**, a leverage
   result at the panel's realised premia, and the wrapper cut is the whole difference; at
   the forward premia it costs 0 to 0.2 pp/yr of log growth and wins only if the equity
   premium over bonds is about 1.5 pp or less, which is where four of six managers put it.
   It buys 1.8 points of maximum drawdown and one point of volatility. That is the price of
   the valuation bet, stated; an investor who does not hold that belief holds the 30% vector. What the same evidence says about the 0th-percentile excess CAPE yield
   is that an unlevered 10–15 point TIPS
   line in the traditional IRA is the cheapest drawdown protection has been in expectation:
   the substitution's historical cost of 0.55–0.77 pp/yr was earned on a 6–7 pp realised
   premium, and at 0–1.5 pp over TIPS it is 0–0.2. It costs shelter space, since the
   traditional third is 90% RSST. **The conditional rule: at a tolerable drawdown of −50% or
   tighter, hold 10 points of long TIPS unlevered in the traditional account, funded from VTI
   and VXUS pro rata, and shrink the wrapper to 19.1%; at −60% or looser, hold none.** The 10
   points are Experiment 018's frozen substitution arm and the 19.1% is the ladder's trend
   column, not a derivation from the ladder: the rule leaves equity notional near 91% where the
   ladder's −50% row carries 65%, and the ladder-consistent version needs about 36 points of
   TIPS, which spills out of the traditional third at about 7.4 bp/yr
   ([part A](portfolio-for-one-investor.md) §7). The default for this contributing,
   leverage-accepting investor is none.
4. **US versus international: 65/35 to 60/40 by contributions only.** 81% of 35 years of US
   outperformance was re-rating; relative CAPE 1.70× developed and 1.85× EM; a 10 pp shift
   is worth about 14 bp/yr against 80–144 bp of tracking error and 55–178 years to
   demonstrate. New money reaches AVDV only through the Roth's annual cap, so the executable
   rule is every sheltered dollar to VXUS until 60/40, taxable dollars to VTI and VTV to
   target and then VXUS, and AVDV bought only to hold 10%, the weight at which it was measured:
   about a year with an employer plan receiving deferrals, two without
   ([part A](portfolio-for-one-investor.md) §3.8). Framed as regret across stated
   re-rating scenarios ([valuation](valuation-and-the-allocation.md) §5.7), 60/40 is the first
   stop rather than the destination: 50/50 is the minimax-regret split at 152 bp/yr of
   tracking error and 2.8 years of contributions at 10%/yr, 55/45 sits between at 98 bp, and
   40/60 is not supported because its worst cell flips under further US re-rating. Where to
   stop between 60 and 50 is a tracking-error tolerance the investor has not stated.
5. **Value tilts: hold, do not enlarge.** Spread 7.54×, 81st percentile, closed 0.27 log
   units in eighteen months, fitted slope a third of its detection floor, positive
   out-of-sample R².
6. **No change** to credit (Baa−Aaa 0.44 pp, 2nd percentile of a century), gold (98.5th
   percentile real), or cash (no conditioning record; best out-of-sample R² +0.007).

Review triggers, each a level checkable from the same series: Baa−Aaa back at 0.90 pp reopens
credit; the value spread below 4.95× re-examines tilt size; CAPE below 30 reverts the widened
drawdown assumption; the Shiller excess CAPE yield's expanding percentile at 0.50, or the
TIPS-based measure back at its 2.97 pp median, returns the ECY rule to its anchor; a 30-year
TIPS real yield below about 2.0% ends the "cheapest in the record" note; a term premium above
1.5 pp *and* a negative trailing 36-month bond–equity correlation, both required, reopen the
stacked Treasury leg, because the correlation alone sorted months only inside the 1981–2020
bull market (Experiment 020).

## Bonds, gold, and other alternatives

Defensive assets belong in the portfolio when they help meet withdrawals, drawdown or
holdability constraints; they need not beat equity standalone.

- **Duration-hedged credit is a distinct engine and the earlier rejection was scoped to the
  wrong object.** The +0.83 correlation to Treasuries that closed the question is a property
  of the *unhedged* corporate leg; the duration-hedged excess correlates **+0.016 with long
  Treasuries over 1,068 months**. It is a premium, not a hedge, and it matters as a
  substitution inside a defensive allocation or not at all.
- **Cash does the crash-hedging work usually credited to duration.** Swapping 10% of equity
  into T-bills adds +0.92% in the average worst-decile equity month; long Treasuries add
  +0.94%, for 8.4% volatility and a −59% drawdown.
- **Defensive engines were tested inside the leveraged construction for the first time, and
  none is added** (Experiment 018, `exploratory`;
  [defensive engines](defensive-engines-in-the-construction.md)). A stacked Treasury leg of
  20 or 40 points reads +0.34 [−0.01, +0.69] and +0.68 against the reference on 96 years,
  `unresolved`; it leaves maximum drawdown within 1 pp, halves months under water in 1929,
  helps the three modern deflationary episodes (2000, 2008, 2020) by 1–5 pp while 1929 and
  1937 read +0.25 / −0.07, and costs 22–42 pp across 1977–81 for the 20- and 40-point stacks
  (the 10-point substitution arms cost about 10 pp there) and 2–5 pp in 2022.
  Its whole contribution sits in 1981-10…2020-07: +1.20 there, −0.25 [−0.69, +0.16] on the
  691 months outside, −1.32 pp/yr since 2020-08, and 576 consecutive months behind the
  reference over 1933–1981; with a ten-year bond it is +0.17. Today's term premium of about
  0.8 pp less 15 bp of financing on 20 points is about +0.04 pp/yr of expected gap against
  1.71% of tracking error after an 11 bp certain cost, at a post-2020 bond–equity correlation
  of +0.37. **Not adopted.** An investor who wants it anyway: at most 10 points, rollover
  IRA only (§1256 mark-to-market; RSSB's 2025 distribution was 3.4% of NAV, 73% ordinary), as
  an explicit correlation-reversion bet; NTSX is the cheaper wrapper per Treasury dollar and
  RSSB the cleaner one.
- **A regime-conditioned stack does not rescue it** (Experiment 020, `unresolved`;
  [defensive engines](defensive-engines-in-the-construction.md) §3.1). Switched on only when
  the trailing 36-month bond–equity correlation is negative, the same 20-point leg reads +0.16
  pp/yr [−0.06, +0.38] against a 0.32 floor on 96 years and −0.15 [−0.33, +0.04] on the 685
  months outside the bull market, where the signal picked the losing months. Eighteen switches
  in 96 years, off since 2023-02: the rule would hold the published vector today.
- **Substitution arms are `rejected` on mean and are the only route that cuts drawdown.** Ten
  points of equity into cash, long Treasuries or a bonds-plus-trend wrapper read −0.55 to
  −0.77 pp/yr against the reference and cut 1929- and 2008-scale drawdown by about 4 pp.
  NTSX-only, with no trend, is rejected everywhere (−1.66). The TIPS line in *Valuation*
  above is this trade, taken only when the stated tolerance binds and priced at today's real
  yield rather than at the panel's.
- **Stacked gold is unresolved and not added.** Ten points GDE-like read +0.35 [−0.20, +0.94]
  against a 0.64 floor on 1968–2025, drawdown −44.4% against −45.9%, +6.8 pp across the 1970s
  inflation episodes, with the real gold price at the 98.5th percentile since 1975. A cheap
  financed wrapper changes implementation, not the expected-return uncertainty.
- **Crypto stays at 0–2%, taxable, labelled speculation, outside the vector.** Up-beta 1.526
  against down-beta 1.616, convexity indistinguishable from zero, and the only sleeve tested
  that deepened portfolio drawdown at every weight. The 2025–26 record is the same evidence
  again: Feb–Apr 2025 bitcoin −28% and ether −60% against the S&P 500's −19%, troughing on
  the same day; H1 2026 bitcoin −53% and ether −67% from their cycle highs against −9%, still
  falling three months after equities bottomed; 30-day correlation to the S&P 500 in 2026
  between 0.08 and 0.68, mean 0.46; one-year realised volatility 44%. Ether staking is a real
  contractual payer and a small one: ETHE's 2.5% sponsor fee exceeds its staking income, ETHB
  nets about 1.9% annualised, and the reward is ordinary income. BlackRock's own guidance is
  1–2%, risk-budgeted like a single mega-cap stock. Financing it does not change the verdict: a
  financed 3.5-point leg beats the same points sold from equity by +0.37 pp/yr, which is the
  equity premium on the capital not sold and contains no property of bitcoin. A 10-point
  RSSX-like stack's +3.15 [+1.53, +4.81] against a 2.25 floor is bitcoin's own +73 pp/yr over
  eleven years doing the work, and the stack needs bitcoin to earn +3.0 pp/yr arithmetic and
  +8.1 in log growth to break even ([audit](alternative-sleeves-audit.md) §3.1).
- **Explicit tail hedges are rejected on measured cost against measured benefit.** Across
  eight candidate engines, none showed statistically resolvable convexity; the only
  significant kink was BAB's, and its sign is *concave*.
- Catastrophe risk is the one genuinely non-financial engine with a solved access problem
  and an unattractive current price.

See [alternative sleeves](alternative-sleeves-audit.md).

## Currency

Unhedged foreign equity is a long position in the developed-currency carry trade: unhedged
minus hedged is the currency excess return and nothing else. **The mean is unresolvable on
every panel tested** (−1.12 to +0.62 pp/yr against floors of 1.79 to 4.21); **the variance
reduction is large and precise**, about 20% of sleeve volatility, reproduced by MSCI's own
hedged and unhedged EAFE pair. The currency leg correlates +0.26 with its own local equity,
and the "dollar strengthens in a crisis" pattern fails in all four pre-2000 windows. Make the
case on variance, never on the mean, and hedge in sheltered accounts only, since forward P&L
is forced out annually. See [currency](currency-and-the-international-sleeve.md).

## Timing rules on the equity sleeve

Not supported at any weight in any account. A 10-month/200-day rule beats a **beta-matched**
control by +0.74 pp/yr against a detection floor of 3.03 — `unresolved`, not rejected — and
fails deflation (DSR 0.33 at 14.8 effective trials; Hansen SPA p = 0.267). What survives is
drawdown reduction, not the mean.

The decision is settled by three cheaper substitutes rather than by the null: a lower equity
share buys exposure reduction free and tax-free, a financed trend overlay buys the same
signal on about fifty markets, financed rather than sold, at 0.32 pp/yr of distribution drag,
and the tax cost of the rule in a taxable account is 1.92 pp/yr — several times the entire
pre-tax gap. A pooled test on the JST annual panel finds +0.97 (t 2.74) on uninvestable data.
See [timing rules](timing-rules-on-the-equity-sleeve.md).

The leveraged versions are measured too (Experiment 021, daily data 1926–2026;
[leveraged ETFs](leveraged-etfs-and-timing-rules.md)). The 200-day rule on a 3× fund carries
no resolvable timing content against the same fund held at the rule's own average exposure:
+4.79 pp/yr against an 8.41 floor over 99 years and −0.44 since 1990. Everything else it earns
is beta on paths that draw down 85 to 99.9%. It cut the slow bear markets, did nothing in
October 1987, and its deepest drawdown is a run of whipsaws in 1933–35 at −84.6%. The UPRO/TMF
mix is the 1981–2020 bond bull market with equity leverage attached; it lost 52% across
1972–81 while the index gained 60%. In a taxable account the rule costs 1.8 to 3.2 pp/yr.
None belongs in any third.

## Account placement

Asset location is an investor-specific optimization over tax rate, yield type, turnover,
foreign tax credits, embedded gains, account capacity and expected holding period. Generic
rules reverse.

- **Every international fund outranks every US equity fund in the shelter queue, and a
  total-market US fund is last at every rate tested.** "Hold international in taxable for
  the credit" is wrong for an investor of this shape even though it forfeits the credit.
- The repository's earlier emerging-market inversion was an artifact of assuming fully
  qualified dividends. The filed qualified fractions reverse it.
- A high-turnover momentum fund at a 5% weight can outrank almost everything else, because
  the ETF in-kind shield does not survive its turnover.
- **Sheltering a stacked wrapper makes the largest open measurement in the placement
  problem stop mattering.** It costs 1.12 to 8.54 bp/yr if the audited basis is right,
  against 42.62 to 89.88 bp/yr for following the audited ranking if the wrapper's accrual is
  distributed. Ten to one at every bracket: the decision is right under either reading, so
  the measurement can stay unresolved.
- **Placement is worth far less than its headline, and the honest figure is +2 to +7 bp/yr
  against the investor's own counterfactual.** Lot selection is mutually exclusive with never
  selling and is withdrawn; a rebalancing hurdle avoided is not a saving and is withdrawn; a
  line resting on an undistributed accrual is conditional on a distribution decision the fund
  has not made, and is reported unbooked. Fee and fund-structure lines are measured against a
  cheap index and are reported separately, never added.
- **A captive employer menu can invert the entire ranking.** Where the tax-deferred third is
  partly an employer plan, five of eight funds cannot go in it; the menu binds below a
  rollover share of **0.55**, and at the extreme it forces the fund that ranks *last* in the
  shelter queue into shelter while evicting the two highest-yielding funds to taxable. That
  costs 3.3 to 9.1 bp/yr depending on bracket — **more than the whole placement edge** — which
  makes consolidating an old employer balance into a rollover IRA the cheapest lever
  available. It also means a pro-rata control is *infeasible* for such an investor, and
  measuring against one overstates the result.
- **The conditional TIPS leg has a placement cost of about the whole placement edge.** Ten
  points of TIPS in the traditional account displace 10 points of RSST into the Roth and push
  5–9 points of VXUS to taxable, depending on whether the leg is funded pro rata from VTI and
  VXUS or from VTI alone (part A §7). State it; do not hide it.

## Harvesting, and why the never-sell plan destroys its own best use

Tax-loss harvesting looks like the largest available implementation edge for an accumulating
investor with a large taxable account, and for this construction it is close to worthless:
**a plan whose taxable account never sells generates no realised gains for harvested losses
to offset**, so the losses hit the §1211(b) $3,000/yr cap. The gross harvest yield is real
(18.8% of the account in year one, 4.0% in year thirty at 10%/yr contributions) and about
0.2% of it ever produces a tax saving; the programme is worth +13.9 bp held to death and 0.0
bp if the money is spent, and an unused carryforward dies with the taxpayer.

**Direct indexing is rejected**: break-even needs 1.2%/yr of the account in outside realised
gains at the top bracket held to death, it doubles lock-in, its fee is non-deductible under
§67(h), and proxy tracking error of 1.44%/yr is three times the 46 bp edge budget.
**Fund-level harvesting between two similar broad funds is the route that survives**: free,
reversible, and worth the annual deduction cap and little else. See
[harvesting](harvesting-and-direct-indexing.md).

## Operating the portfolio

- **The rebalancing target is a vector of capital weights. Nothing else is ever typed.**
  Exposure figures are derived audit quantities, recomputed from the wrapper's latest
  filing; a target stated in notional changes every quarter on its own, and typing exposure
  figures into a capital-weight screen costs about a quarter of the intended sleeve.
- Across multiple accounts the portfolio is restorable without a taxable sale **iff every
  fund's taxable holding is at or below its target weight**. Headroom on a line is however
  much of it sits somewhere sellable. A few points of headroom cost well under a basis
  point a year; a forced taxable sale costs hundreds of times a spread.
- A contribution stream and a headroom buffer are substitutes.
- Annual review with a 25% relative band and sheltered trades only holds mean exposure error
  near 1 pp at roughly three trades a year and zero realization tax. The *return* benefit of
  any rebalancing policy is `unresolved`; exposure control is the defensible objective.

## What this construction will feel like

This portfolio has no crash protection worth the name; it has a lost-decade hedge. In a fast
crash it falls with the market, −50.3% against the unlevered cheap index's −52.7%, and the
overlay at RSST's delivered loading offsets about 7% of the equity loss in the tail. The only
route that cuts crash drawdown is the unlevered TIPS substitution the valuation rule defaults
to zero, and at today's real yields it costs 0 to 0.2 pp/yr in expectation.

The failure mode is not a crash. It is a decade of quiet monthly underperformance against
the most familiar comparator: a US value tilt has run 54.3% behind for 17.7 years without
recovering; an international sleeve 69.0% behind over 18.2 years; a financed trend sleeve,
net of the equity it displaces, 59.9% behind over 11.2 years.

The load-bearing precommitment is that the comparator must be leverage-matched. Comparing a
levered portfolio with an unlevered index credits the leverage to the strategy on the way up
and blames the strategy for it on the way down.

## What would change the position

Investor inputs with the highest decision value: the maximum tolerable drawdown, which now
decides both the wrapper's size under the widened assumption and whether the conditional
TIPS leg exists, and which nobody has supplied; then contribution and withdrawal paths, the
open-menu fraction of sheltered accounts, tracking-error tolerance, embedded gains and tax
rates, liabilities, human capital, and liquidity needs.

Research capable of changing the position:

- **the wrapper's trend loading, refreshed at each filing.** Form N-PORT Item B.5 carries a
  fund's own filed monthly total return, so no licensed price series is required. RSST over
  31 months (2023-10…2026-04) loads **+0.681 [+0.406, +0.955]** on the AQR TSMOM index and
  **+0.857 [+0.719, +0.995]** on DBMF itself (R² 0.88); a negative control on RSSB, the same
  sponsor and wrapper with bonds instead of trend, reads −0.10 [−0.36, +0.16], so the design
  discriminates. Twelve months to 2026-08-31 RSST returned +41.5% at NAV against SG Trend
  +22.8% and the S&P 500 about +19–22%, consistent with roughly one unit of each. RSST's
  2026-07-31 N-PORT is not yet filed and is due by 2026-09-29: refresh then. DBMF loads
  0.671, CTA 0.475, KMLM 0.245. **JPFP** (direct futures plus direct stocks, no ETF or swap,
  59 bp) has filed no N-PORT; review it at its first, due by 2026-09-29. **RSIT** is reviewed
  at 24 filed months and **MATE** has six. None replaces RSST yet;
- the numeric valuation triggers listed under *Valuation, taken into account*, and a term
  premium above 1.5 pp together with a negative trailing bond–equity correlation for the
  stacked Treasury leg;
- the fund-level financing spread, which decides the sign of an overlay's contribution and
  which no issuer discloses because futures financing lives in the basis;
- a survivorship-corrected, point-in-time live-product panel including dead funds;
- crisis-conditional dependence estimates for trend, bonds, gold and currency;
- holdings-based delivered factor exposure and cost;
- a derivation of the materiality and sleeve-bar constants, which remain asserted.

## Review policy

Review the construction when investor circumstances change, a chosen vehicle changes fee,
mandate, liquidity or tax treatment, a monitoring boundary is crossed, or new evidence can
materially reverse a decision. An issuer or trust liquidation notice is a review trigger.

**If RSST announces liquidation or a mandate change**, sell it before the last trading day and
buy VTI in the same account. The tax cost is zero under both placements because the wrapper is
sheltered; the exposure cost is the overlay's expected gap of about 0.84 pp/yr for each year
without a replacement; the resulting vector is RSST 0 / VTI 49 / VTV 15 / VXUS 16 / AVDV 10 /
IDMO 5 / AVES 5, the site's portfolio three. Candidate replacements are reviewed in the order
CTAP, MATE, JPFP, RSIT, and each currently fails a stated test
([part A](portfolio-for-one-investor.md) §5).

Monitor on evidence and on a calendar, never on price. Do not set a performance review for a
diversifying sleeve: at a 30% weight such a sleeve underperforms in 43.8% of resampled
ten-year histories even when its premium is positive, so a performance trigger removes it
for doing what it was bought to do. Require three consecutive readings before acting, because
a decade of decay is inside this strategy's historical range of behaviour.

**A monitoring bar must be coarser than the instrument that reads it.** The trend-weight page
proposed removing the sleeve at a measured loading below 0.70; the first measurement returned
**0.681 on a 95% interval of [0.406, 0.955]**, which neither fires the bar nor clears it. That
is a defective bar, not a marginal sleeve — the defect
[decision 0009](../decisions/0009-blocks-lifted-and-closures-rescoped.md) clause 1 records for
the 0.30 pp/yr sleeve hurdle. The bar stands unfired and should be re-derived from the
break-even delivery the wrapper needs to beat a standalone fund, **0.19 to 0.27** at a 25%
weight, which the measurement clears. Review at 48 filed months, around 2027-09.

**Execution facts, resolved `as of 2026-09-01`.** Fidelity's ETF service-fee list as of
2026-08-15 (84 tickers in the PDF) names none of Tidal/Return Stacked, Simplify, Pacer, J.P.
Morgan, Invesco, Avantis or Dimensional; Schwab's programme is announced for late 2026 to Q1
2027 with no list. RSSB's fee is 0.39% with no expiry, the waiver having been replaced by an
outright cut on 2026-04-27. No shelf fund was liquidated, merged or changed mandate in 2026.
KMLM's adviser changed control on 2026-06-23, CTAP's portfolio manager left on 2026-08-07 and
ReSolve became RSST's execution sub-adviser: vehicle facts on record, and none fires a trigger.

The detailed numerical and product evidence remains in the linked topical syntheses, typed
client content, specifications, manifests, tests and run artifacts. This page owns the
current interpretation only.
