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
recommendation is **RSST 30 / VTI 19 / VTV 15 / VXUS 16 / AVDV 10 / IDMO 5 / AVES 5**,
1.322× gross, 38.2 bp of weighted fee and 36.2 bp of weighted net cost, derived in
[part A](portfolio-for-one-investor.md) §2 and rendered on `/portfolio`. The construction
Experiment 016e scored, and which everything in this section reports, is the **same seven
funds at RSST 25 / VTI 24**, 1.268× gross, 33.4 bp of fee and 31.3 bp of net cost — the
recommendation as it stood when the specification was frozen. The five points come out of VTI
and go into trend; no other line changes. Every "recommended" figure below belongs to the 25%
arm, and no experiment anywhere has run the seven funds at 30%.

Experiment 016e ran that construction through the frozen tournament machinery, with
`unresolved` predicted in the specification before the run.

Against a cheap index levered to the same 1.268× and charged the same financing, the
25% arm reads **+2.20 pp/yr [+0.05, +4.57] against a 2.83 floor** — unresolved,
and 59 years of holding before the design could see it. Tracking error 6.0%; probability of
trailing 15.6% / 7.1% / 3.4% at 10 / 20 / 30 years with median shortfalls of −0.79 / −0.46 /
−0.30; drawdown −50.3% against the levered control's −64.6%.

**The candidate constructions cannot be told apart.** Recommended +2.20, the AVUV variant
+2.35, the previous recommendation +1.92, the investor's original +2.49 — a spread of 0.57
inside floors of 2.75–3.33. Fund selection among reasonable tilts is below this design's
resolution, and a page that ranks them is reporting noise.

**Two comparisons do resolve, and they are the useful part.**

1. **The 25% arm minus the investor's original is −0.50 pp/yr [−0.77, −0.23] against a 0.39
   floor.** That difference is **5.4 points of leverage rather than construction** — the
   original holds the wrapper at 30% where the 25% arm holds 25%. On growth against a
   leverage-matched control, more trend earns more. It is also **not a clean reading of the
   trend weight**: the two arms differ in four holdings as well, which *Optional financed
   trend* below sets out. This is the number that subsequently moved the published weight to
   30%, against the holdability evidence rather than with it, and the trade should be stated
   to the investor as a choice rather than resolved on their behalf.
2. **The tilt complex alone beats the cheap index by +0.80 pp/yr [+0.36, +1.31] against a 0.47
   floor — resolvable, in 12 years.** This reproduces Experiment 016's +0.79 on a different
   fund list, which is independent confirmation rather than a restatement.

**AVDV's addition reads +0.28 pp/yr [+0.05, +0.56] against a 0.29 floor** — short of resolution
by 0.01, and positive in every sub-period. The unlevered tilt-only pair gives +0.29
independently.

**Net cost after securities lending is now read from 50 fiscal-year Form N-CEN filings, and no
fund on the tilt shelf has negative net cost**: VTV 2.70 bp, SPMO 12.93, AVLV 14.94, IDMO
22.59, AVUV 24.54, AVES 29.21, AVDV 30.03, RPV 33.87. The VTV-versus-AVUV gap is 21.8 bp on
cost against 22 bp on fee, so the fee-based conclusion stands. The one correction favours the
strongest recommendation: AVDV costs 30.03 bp, not its 36 bp headline.

**RPV and SPMO are both rejected on measurement rather than on principle.** RPV reads −0.10
pp/yr at a 15% weight [−0.63, +0.42], negative under all four premium scenarios: it delivers
HML +0.369 over VTV but also **RMW −0.204 and UMD −0.173 — it pays for value by selling
profitability and momentum** — at 42%/yr turnover. SPMO is the better momentum vehicle than
MTUM (13 bp, 44% turnover against 116%) and still reads +0.02 pp/yr at 5% [−0.14, +0.18], with
an active leg +0.626 correlated with IDMO's.

## Optional financed trend

Trend remains the leading diversifier candidate, and the case is stronger than this
repository stated for most of its history. Four independent routes now bracket the weight:

| Route | Weight | What it optimises |
|---|---|---|
| Variance minimisation, `w* = −ρ σₑ/σ_d` | 21.6%, interval [10.3, 32.8] | portfolio variance |
| Growth subject to holdability | 15–25%, centre 20% | after-cost log growth |
| Regret over an explicit premium prior | 25%, robust 20–30% | maximum regret, then capitulation |
| Construction tournament | no interior optimum | growth against a leverage-matched control |

**25% is the only weight all four routes admit, and 30% is the weight the one resolvable
measurement prefers.** Nothing in the corrected growth arithmetic argues below 0.28 on the
investor's own benchmark under any reweighting of the premium prior; what holds the four-route
consensus below the regret surface's own 0.36 is the premium-free holdability evidence — 15–25%
from tracking error, and 19.1% from the CAPE-conditioned drawdown.

Experiment 016e then measured the closest thing to a 25-against-30 comparison the programme
has: **0.50 pp/yr [0.23, 0.77] against a 0.39 floor** in favour of the higher weight, the only
whole-portfolio comparison anywhere here that clears its own resolution. **Read what it
compared.** The arm is `recommended_vs_original`, which scores the seven-fund construction at
RSST 25 against the investor's *original eight-fund* proposal at RSST 30, so **the pair differs
in four holdings as well as in five points of the wrapper**, and no experiment holds the
recommended seven funds at 30%. The reason to attribute the gap to the wrapper is that the two
tilt complexes, stripped of trend and of leverage, score +0.7996 and +0.79 pp/yr against the
same unlevered control on the same panel; that is an argument rather than a paired measurement,
and [016e's own open question 4](final-construction-test.md#verified-assumed-open) asks for the
matched pair that would settle it.

So the choice between them is not settled by measurement either. It is
whether the investor can hold a sleeve through a decade in which it contributes nothing while
equities rise — abandonment probability runs about 17% at the median at 30% against 11% at 25%,
and 66.7% at 30% if the premium is gone entirely.

**For an investor contributing 5–15%/yr with a multi-decade horizon, 30% is the better choice**,
because a contribution stream is what carries a position through a drought and the growth
comparison, imperfect as it is, is the only one in the programme that clears its own floor. For an investor who would sell it,
25% is better, and a portfolio held beats a better one abandoned. State the trade; do not
resolve it silently.

Three things to hold onto:

- **The forward premium this repository asserted at 1.80 pp/yr was never measured.** It is
  the 2012–2025 subsample's own geometric mean less a fee, restated onto a gross arithmetic
  axis as **4.17%**, and it had been double-counted as a separate scenario. A verdict built
  on it inherited a units error rather than a finding.
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
- **86% of the measured edge comes from the repository's shortest series** — developed
  ex-US and emerging panels starting 1990-11, with no out-of-sample period at all;
- charging fitted alphas moves the result from +0.79 to +0.60 under empirical-Bayes
  shrinkage and to +0.30 charged raw. The threshold rule used elsewhere in this repository
  is harsher than the defensible estimator, and it charges only the side whose alphas were
  measured.

**The developed-ex-US value result was a property of its window, and any decision resting on
it should be restated.** On the 55 months DFIV and AVIV impose, all four large-cap
developed-ex-US value funds read −2.3 to −2.9 pp/yr with intervals excluding zero. IVLU and
EFV are old enough to measure over 78 months, and there they read −1.0 and −1.7 with neither
interval excluding zero; the small-minus-large gap falls from +4.5 (resolvable) to +2.0 (not).
Over the months AVDV and DFIV both existed, their plain returns differed by **−0.30 ± 5.16
pp/yr** — the small-cap fund never out-returned the large-cap one, it out-returned the model's
prediction for it. So *"large-cap developed value delivers badly and small-cap escapes it"* is
not supported. A tilt should be chosen on delivered exposure, cost, turnover and overlap,
which the data resolves, rather than on a measured excess return it does not.

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
- Gold has diversified the tested samples but appeared return-dominated at examined
  weights; a cheap financed wrapper changes implementation, not the expected-return
  uncertainty.
- **Crypto is rejected as a diversifier**: up-beta 1.526 against down-beta 1.616, convexity
  indistinguishable from zero, positive in 1 of 13 worst-decile equity months, and the only
  sleeve tested that deepened portfolio drawdown at every weight.
- **Explicit tail hedges are rejected on measured cost against measured benefit.** Across
  eight candidate engines, none showed statistically resolvable convexity; the only
  significant kink was BAB's, and its sign is *concave*.
- Catastrophe risk is the one genuinely non-financial engine with a solved access problem
  and an unattractive current price.

See [alternative sleeves](alternative-sleeves-audit.md).

## Currency

Unhedged foreign equity is a long position in the developed-currency carry trade, and the
identity is exact: unhedged minus hedged is the currency excess return and nothing else.

- **The mean is unresolvable on every panel tested, including 150 years of annual data** —
  estimates from −1.12 to +0.62 pp/yr against floors of 1.79 to 4.21.
- **The variance reduction is large and precise**: roughly 20% of sleeve volatility,
  reproduced independently by MSCI's own index pair (EAFE hedged 10-year σ 11.82% against
  unhedged 14.99%, max drawdown −54.6% against −60.4%).
- The currency leg's correlation with its own local equity is **+0.26**, so it adds risk,
  and the minimum-variance hedge ratio exceeds 1.0.
- The "dollar strengthens in a crisis" pattern is younger and shakier than usually
  presented: in all four pre-2000 windows the data reach, the dollar weakened.

Make the case on variance and crisis dependence, never on the mean. Hedge in sheltered
accounts only: a cash-settled forward cannot be redeemed in kind, so hedge P&L is forced
out annually. See [currency](currency-and-the-international-sleeve.md).

## Timing rules on the equity sleeve

Not supported at any weight in any account. A 10-month/200-day rule beats a **beta-matched**
control by +0.74 pp/yr against a detection floor of 3.03 — `unresolved`, not rejected — and
fails deflation (DSR 0.33 at 14.8 effective trials; Hansen SPA p = 0.267). What survives is
drawdown reduction, not the mean.

The decision is settled by three cheaper substitutes rather than by the null: a lower equity
share buys exposure reduction free and tax-free, a financed trend overlay buys the same
signal better and across more markets, and the tax cost of the rule in a taxable account is
1.92 pp/yr — several times the entire pre-tax gap. See
[timing rules](timing-rules-on-the-equity-sleeve.md).

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

## Harvesting, and why the never-sell plan destroys its own best use

Tax-loss harvesting looks like the largest available implementation edge for an accumulating
investor with a large taxable account, and for this construction it is close to worthless.
The two good ideas cancel: **a plan whose taxable account never sells generates no realised
gains for harvested losses to offset**, so the losses hit the §1211(b) $3,000/yr deduction cap.

- The gross harvest yield is real and large — 18.8% of the account in year one, 4.0% in year
  thirty at a 10%/yr contribution rate. Contributions are what prevent ossification; with no
  new money the same series collapses to 0.9%. A year-one headline overstates the thirty-year
  average by 3.7× with contributions and 8.3× without.
- **Only about 0.2% of those losses ever produce a tax saving.** The cap is worth 11.1 bp on a
  $1m account and 3.7 bp on $3m, and it falls as the account compounds.
- Harvesting cuts basis by exactly the loss realised. On liquidation the carryforward absorbs
  the untouched part and only the rate difference survives; §1014 and §170 forgive it outright.
  So the same programme is worth **+13.9 bp held to death and 0.0 bp if the money is spent**.
- An unused carryforward **dies with the taxpayer** (IRS Pub 559), so the step-up that makes
  harvesting permanent also destroys the unused stock of it.

**Direct indexing is rejected.** Break-even needs 1.2%/yr of the account in realised gains from
elsewhere at the top bracket held to death, or 3.0% if ever liquidated. It doubles lock-in
(55.7% embedded gain against 26.7% from never selling; 142 bp/yr to abandon), its fee is
permanently non-deductible under §67(h), and measured tracking error on a proxy is 1.44%/yr
against a 46 bp edge budget — noise three times the signal.

**Fund-level harvesting between two similar but not substantially identical broad funds is the
route that survives.** It is free, reversible, and beats direct indexing at every rate tested
below 2.48% of offsetting gains. For an investor with no outside gains it captures the annual
deduction cap and little else, which is a small positive rather than a programme.

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

The failure mode is not a crash. It is a decade of quiet monthly underperformance against
the most familiar comparator: a US value tilt has run 54.3% behind for 17.7 years without
recovering; an international sleeve 69.0% behind over 18.2 years; a financed trend sleeve,
net of the equity it displaces, 59.9% behind over 11.2 years.

The load-bearing precommitment is that the comparator must be leverage-matched. Comparing a
levered portfolio with an unlevered index credits the leverage to the strategy on the way up
and blames the strategy for it on the way down.

## What would change the position

Investor inputs with the highest decision value: contribution and withdrawal paths, the
open-menu fraction of sheltered accounts, maximum tolerable drawdown and tracking error,
embedded gains and tax rates, liabilities, human capital, and liquidity needs.

Research capable of changing the position:

- **replication of the wrapper trend loading on a longer window.** This is no longer
  unmeasured: Form N-PORT Item B.5 carries a fund's own filed monthly total return, so no
  licensed price series is required, and RSST over 31 months (2023-10…2026-04) loads
  **+0.681 [+0.406, +0.955]** on the AQR TSMOM index and **+0.857 [+0.719, +0.995]** on DBMF
  itself (R² 0.88) — about 86 cents of DBMF per dollar. A negative control on RSSB, the same
  sponsor and wrapper with bonds instead of trend, reads −0.10 [−0.36, +0.16], so the design
  discriminates. Thirty-one months is short and the estimate should be refreshed annually;
- the fund-level financing spread, which decides the sign of an overlay's contribution and
  which no issuer discloses because futures financing lives in the basis;
- a survivorship-corrected, point-in-time live-product panel including dead funds;
- crisis-conditional dependence estimates for trend, bonds, gold and currency;
- holdings-based delivered factor exposure and cost;
- a derivation of the materiality and sleeve-bar constants, which remain asserted.

## Review policy

Review the construction when investor circumstances change, a chosen vehicle changes fee,
mandate, liquidity or tax treatment, a monitoring boundary is crossed, or new evidence can
materially reverse a decision.

Monitor on evidence and on a calendar, never on price. Do not set a performance review for a
diversifying sleeve: at a 30% weight such a sleeve underperforms in 43.8% of resampled
ten-year histories even when its premium is positive, so a performance trigger removes it
for doing what it was bought to do. Require three consecutive readings before acting, because
a decade of decay is inside this strategy's historical range of behaviour.

**A monitoring bar must be coarser than the instrument that reads it.** The trend-weight page
proposed removing the sleeve at a measured loading below 0.70. The first measurement returned
**0.681 on a 95% interval of [0.406, 0.955]** — 0.019 under a bar the interval spans twice
over, so the reading neither fires it nor clears it. That is a defective bar, not a marginal
sleeve, and it is the same defect [decision 0009](../decisions/0009-blocks-lifted-and-closures-rescoped.md)
clause 1 records for the 0.30 pp/yr sleeve hurdle: a threshold finer than the design's own
resolution manufactures verdicts the data cannot support. The bar is left in place, unfired
and recorded as unresolved, and should be re-derived — from the break-even delivery the
wrapper needs to beat a standalone fund, which is **0.19 to 0.27** at a 25% weight, not from a
round number. Against that bar the measurement clears comfortably. Review at 48 filed months,
around 2027-09.

The detailed numerical and product evidence remains in the linked topical syntheses, typed
client content, specifications, manifests, tests and run artifacts. This page owns the
current interpretation only.
