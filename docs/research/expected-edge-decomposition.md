# Where outperformance can come from, how large it is, and how certain it is

**Question.** Where can a real retail investor's net return actually exceed a stated
benchmark, how large is each source, and how certain is each one?

**Decision it informs.** The *size and certainty class* of every return source this
repository is willing to model, and the benchmark each is measured against. Choosing
products, giving advice, and forecasting any market are out of scope.

Everything numerical here regenerates from
[`research/src/portfolio_edge/studies/`](../../research/src/portfolio_edge/studies/) and
is pinned in `research/tests/unit/test_studies_*.py`. Seeded, deterministic, no market
data. Retrieval date for every source: **2026-08-12**.

---

## Conclusion

1. **Three benchmarks, and they never aggregate.** Against a **cheap index** the whole
   honest budget is about **5.4 bp/yr against 313 bp of tracking error** — a 0.54
   thirty-year probability of being ahead, which is a coin flip. Against the **investor's own plausible
   alternative** it is about **89 bp against ~41 bp** here, revised to **≈110 bp** by
   [structural and tax-aware edges](structural-and-tax-edges.md). Against the **average
   investor** it is 15 bp. Conflating them is the standard way this argument is inflated,
   and `aggregate()` raises rather than summing across them.
2. **Certainty is a property of the pairing, not of the edge.** `P = Phi(e sqrt(T)/s)`
   and `T = (z s/e)**2`, so the horizon scales with the **square** of `s/e`. The same
   50 bp edge reaches 90% confidence in **24 days** against 10 bp of tracking error and
   in **105 years** against 400 bp.
3. **The own-counterfactual budget is conditional, and only one line is not.** The 49 bp
   fee reduction needs only that the reader currently holds an expensive fund. Every
   other line needs a taxable account, or more than one account type, or continuing
   contributions, or direct security ownership. For a reader already holding cheap index
   funds in one tax-deferred account the honest budget is close to zero. **Do not read
   ≈110 bp as a number available to everyone.**
4. **The largest quantity found in this work is a hurdle, not a saving.** Deferral of
   unrealised gain plus the §1014 step-up is worth a horizon-free **162 bp/yr** in a
   taxable account. It is deliberately not booked, and it is what any turnover-bearing
   sleeve must clear.

---

## 1. The budget

| Source | Benchmark | Class | Low | **Central** | High | TE | Falsifier |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| Fund cost reduction | own counterfactual | **contractual** | 40 | **49 bp** | 59 | ~0 | the asset-weighted fee gap closes |
| Tax-loss harvesting | own counterfactual | contractual, **conditional** | 0 | **30 bp** | 90 | 40 bp | no offsetting gains; no new money; a flat capital-gains rate |
| Asset location | own counterfactual | contractual, **conditional** | 0 | **10 bp** | 21 | 10 bp | one account type, or one rate across asset classes |
| Timing / behaviour gap avoided | **average investor** | probabilistic | 5 | **15 bp** | 60 | 150 bp | a decomposition attributing most of the gap to timing |
| Rebalancing, net of diversification | stated index | probabilistic | −62.9 | **−38.7 bp** | 2.4 | 27 bp | **FIRED.** A drift gap above `gamma_star`, measured at ~35× on the deciding pair |
| Securities-lending pass-through | stated index | contractual | 0.1 | **1 bp** | 3 | 2 bp | the fund report shows less, or the manager keeps the split |
| Factor tilt | stated index | probabilistic | −29 | **43 bp** | 78 | 312 bp | the premium's sign; on the US-only post-publication figure the growth contribution is negative at every weight |
| **Total vs the stated index** | | | **−92** | **5.4 bp** | **83** | **313 bp** | P(ahead at 30 yr) = **0.54** |
| **Total vs own counterfactual** | | | **40** | **89 bp** | **170** | **41 bp** | revised to ≈110 bp by [structural edges](structural-and-tax-edges.md) |
| **Total vs the average investor** | | | **5** | **15 bp** | **60** | **150 bp** | P(ahead at 30 yr) = **0.71** |

**Against a cheap index this budget is a coin flip, and that is the finding.** Two
probabilistic lines carry it — a value tilt at +43.1 bp and a rebalancing line measured at
**−38.7 bp/yr** over 420 months ([Experiment 003](rebalancing-policy.md)) — and they very
nearly cancel. The range runs from −92 to +83, so the sign is not robust, and the factor
line's own sign turns on a premium the budget does not choose.

The rebalancing line carried the equal-drift closed form of **+2.4 bp** until 2026-08-22,
which made the total read 46 bp. That line's falsifier had already fired. The stated
reason for keeping it was that the figures were pinned by tests — which inverts the rule
this workspace runs on, that a fixture disagreeing with a measurement is a finding rather
than a number to preserve. Almost the whole of the old total was one falsified line.

The practical consequence is not that the programme found less. It is that **the
index-relative budget was never the deliverable**: the counterfactual row below is, it is
contractual rather than statistical, and it is settled inside a year.

**The 41 bp tracking error on the own-counterfactual total is an assumption**, built by
combining the component tracking errors in quadrature. Those components sit inside the
same portfolio and are not independent, so the true dispersion is wider and every
probability derived from it is an upper bound.

### 1.1 What survives, with its evidence

**Cost reduction — the only large unconditional line.**
[Sharpe (1991)](https://web.stanford.edu/~wfsharpe/art/active/active.htm) is the
backbone: *"after costs, the return on the average actively managed dollar will be less
than the return on the average passively managed dollar… they depend only on the laws of
addition, subtraction, multiplication and division."* Morningstar's 2026 US Fund Fee
Study gives an asset-weighted 0.09% for broad index funds against 0.57% for active; ICI
gives 0.05% against 0.64%. The gap is 48–59 bp. **Use the asset-weighted figures** — the
equal-weighted active-equity average is 1.00–1.12% and overstates what investors pay by
roughly 45 bp.

Two limits usually dropped. The saving is measured against *the fund the investor would
otherwise have held*, never against the index. And switching from one randomly chosen
active fund carries that fund's idiosyncratic risk: at 350 bp of tracking error a 50 bp
fee edge is only 78% likely to be ahead after 30 years. Against the *average* active
dollar the tracking error collapses and the saving is near-certain.

**Sharpe's identity is not exact.** [Pedersen (2018)](https://research-api.cbs.dk/ws/portalfiles/portal/60084093/lasse_heje_pedersen_sharpening_the_arithmetic_of_active_management_publishersversion.pdf)
shows it assumes a static market portfolio; US equity turnover averaged 7.6%/yr over
1926–2015, so *"even 'passive' investors must regularly trade"*. The measured index-
inclusion cost was 21–28 bp/yr for S&P 500 index funds over 1990–2005
([Petajisto 2011](https://www.petajisto.net/papers/petajisto%202011%20jef%20-%20hidden%20cost%20for%20index%20funds.pdf)).
**This line is deliberately not booked, because the effect has since disappeared.**
Greenwood and Sammon report the S&P 500 addition abnormal return falling from 7.4% in the
1990s to *"an average return of only 0.1% between 2010 and 2020"*, and Bennett, Stulz and
Wang find the same independently. Anyone citing Petajisto's headline as a current cost is
off by roughly an order of magnitude.

**Tax-loss harvesting: 30 bp central, and every commonly quoted version is overstated.**
Chaudhuri, Burnham and Lo report a 1.08%/yr tax alpha, wash-sale-constrained to 0.82%,
**after liquidation taxes** — so the "it is only deferral" objection is already answered
inside their number. Four conditions in their own paper cut it hard: the base case
assumes **12.7%/yr of new money** (the static full-sample figure is 0.73% and 1995–2018
is 0.39%); roughly half the alpha is **rate arbitrage** that vanishes at a flat rate;
transaction costs take 16 bp; and it is **unavailable through funds** — *"mutual funds are
barred from passing through security-level tax losses"* — so it requires direct security
ownership. The decisive counterweight is decay: the active tax benefit runs *"from
155.3 bps in year 1 to 50.8 bps in year 2 to −4.3 bps in years 10 and later"* for an
investor with no new money, because harvesting sells the loss lots and retains the gain
lots until the option is out of the money.
[Structural edges §5](structural-and-tax-edges.md) nets the direct-indexing fee this line
does not subtract, moving it to about **26 bp** for a contributing investor.

**Asset location: 10 bp central, and no peer-reviewed source states a per-year figure at
all.** That absence is itself the finding. Shoven and Sialm's *"Optimal asset location
adds an additional 6.6 percent to certainty equivalent wealth"* annualises to about
21 bp/yr over their 30-year horizon — but the annualisation is **our** inference and a
certainty-equivalent wealth ratio is not a return. Vanguard's practitioner range is
*"5 to 30 basis points"*, typical cells 5–13. Two miscitations to avoid: Dammon et al.'s
"65.4 basis points per year" is a break-even hurdle for active management from a
different model, and Poterba, Shoven and Sialm's empirical test actually **reverses** the
conventional rule for index funds.

**Securities lending: 1 bp central, computed from filings.** Net lending income over
average net assets from N-CSR Statements of Operations: **VOO 0.07 bp, IVV 0.25, VTI
1.01, ITOT 1.03, IEFA 1.11**. The near-identical VTI and ITOT figures from two sponsors
cross-validate the method. The decomposition that makes it predictable is D'Avolio's
`17 bp value-weighted fee × 7% utilisation × 80% keep ≈ 1 bp/yr`, which is what the
filings show. **Blocher and Whaley's much-quoted 23–28 bp is modelled *gross* revenue and
is 25–100× the realised net figure for a broad large-cap fund.** Two structural notes:
the income is ordinary income in a taxable account, and SPY, QQQ, MDY and DIA are unit
investment trusts that **cannot lend at all**.
[Structural edges §6](structural-and-tax-edges.md#6-the-core-beta-shelf-audited-on-cost-rather-than-on-fee)
now measures it across 25 funds and 110 N-CEN filings and puts it at **1.83 bp** for the
recommended holdings, moving between 0.45 and 2.60 by fund choice alone. It corrects the
reason too: the premium is an international lending-demand effect, not a size effect — VB,
US small-cap, earns 3.0 bp, the same as large-cap developed international.

**Implementation and financing efficiency is not a line, and the 2026 numbers show why.**
As of 2026-08-10 Vanguard's published 30-day median bid/ask spreads are **0.55 bp (VTI),
0.58 (VOO), 1.18 (VXUS), 2.72 (VB)**; expense ratios are 3 bp on VTI, VOO and VB and
**5 bp on VXUS** from its 497K fee table dated 2026-02-27; commissions are $0 at all
six major US retail brokers checked. Total round-trip friction on a broad US index ETF is
about **1.3 bp**. There is nothing left to harvest, and claiming one would double-count
the cost line. The decision-relevant fact is that a small-cap or international round trip
approaches a full year of expense ratio — **and is larger than the 2.4 bp/yr the
rebalancing line earns.**

**Factor tilt: 43 bp central, sign decided by the premium alone.** The chain that
produced the original 21 bp was
`6.6%/yr gross long-short × 0.42 post-publication retention × 0.40 long-only capture ×
0.30 portfolio exposure − 12 bp incremental fee`, and **two of its five terms have been
deleted rather than measured.**

- **The capture term is gone.** A capture fraction *is* an HML loading — 94% of the
  size-neutral 0.520 is the loading 0.4891, and the identity is exact
  ([Experiment 007](long-only-capture.md#the-correction-a-capture-fraction-is-a-loading-so-it-may-not-multiply-one)).
  Multiplying a fund's loading by it discounted one exposure twice. **This closed open
  question 1 below**, which asked which benchmark the capture might be booked against: the
  answer is none, because a loading is taken against a factor.
- **The retention term is gone too.** It multiplied a gross premium by a decay factor;
  the premium used here is now already the post-publication one, so applying 0.42 to it
  would decay it twice.

The line is now `weight × (h_fund − h_incumbent) × premium − weight × incremental cost`,
with every term measured:

| Term | Value | Source |
| --- | --- | --- |
| weight | 20% of portfolio | the reference construction |
| `h_fund` | AVUV +0.537 `[+0.43, +0.64]` | [Experiment 013](factor-products.md#what-the-corrected-frame-finds) |
| `h_incumbent` | VTI +0.0247 | computed on the same 72 months |
| premium | pooled post-publication HML +4.74 `[+1.46, +8.10]` | [Experiment 005](factor-persistence.md) |
| incremental cost | 0.271 pp/yr — 22 bp of fee, 5 bp of turnover at `k = 1.7` | the funds' own 497K and 485BPOS |
| tracking error | 312 bp, **measured** against VTI, not assumed | AVUV against VTI, 2020-01…2025-12 |

**+43 bp central, `[+9, +78]` across the premium's own interval.** The low end of the range
in the table above is the US-only post-publication premium's lower bound, −2.28 pp/yr,
which gives −29 bp. **Two qualifications this budget cannot express and the recommendation
does.** Only 21 bp of the 43 survives into *geometric growth*, because a substitution into
a more volatile fund pays for its arithmetic edge out of `V/2`. And on the US-only
post-publication premium of +1.57 the growth contribution is negative at every weight —
that premium's own interval is `[−2.28, +5.54]`, and it survives no multiple-testing
correction ([Experiment 001](factor-persistence.md)). See
[the recommendation §5](portfolio-recommendation.md#5-what-each-tilt-costs-in-confidence-terms).

### 1.2 What is rejected, and why

- **"Diversification return" as an edge.** Measured against `sum_i w_i g_i`, which nobody
  can hold.
- **The 1.2 pp behaviour gap at its headline magnitude.** See §2.
- **"Not trading" as a line in the contractual budget.** Rejected structurally, not
  empirically. §2.
- **The index-inclusion cost as a current saving.** Real at 21–28 bp for 1990–2005,
  approximately zero by the 2010s on two independent measurements.
- **Barber–Odean's 6.5 pp turnover penalty as a current number.** Its 3 pp commission
  component no longer exists. Retained as a mechanism.
- **Implementation and financing efficiency.** Avoiding a bad spread is a cost reduction
  already counted; counting it again is a double count.
- **Distinct risk premia — term, credit, insurance, illiquidity.** Real compensation for
  real risk, but a *different benchmark*. Booking a term premium as an "edge" over an
  equity index is a benchmark switch, not a return source.

### 1.3 The double counts this budget avoids

- **Fees and timing do not overlap** — investor return is already net of fund expenses.
- **The behaviour gap and the contractual budget cannot be added at all.** §2.
- **Trading-cost avoidance and the behaviour gap would overlap**; only the smaller is
  booked.
- **Implementation efficiency and the cost line would overlap** — the most common
  inflation in a budget of this kind.
- **Harvesting and location are separable mechanisms with correlated conditions**: a
  single tax-deferred account with no taxable holdings zeroes both at once.
- **Rebalancing and the factor tilt sit inside the same equity portfolio**, so combining
  their tracking errors in quadrature assumes an independence that is optimistic. The
  313 bp is a **lower bound** on its own dispersion.

---

## 2. The behaviour gap is a different benchmark, not a missing line

**May the application present *not trading* as a quantified edge, and may the 15 bp join
the ≈110 bp?** No, and no — for a reason that is structural rather than empirical.

**A dollar-weighted gap is undefined for the investor this repository describes.** The
gap is the difference between a fund's time-weighted return and the internal rate of
return on its investors' dated cash flows. With no cash flows there is no difference: for
a lump sum held throughout the IRR **is** the geometric return, so the gap is exactly
zero. **"Not trading" cannot be a line in a budget whose own arithmetic sets it to zero.**

**And for a saver who does have cash flows, the sign is set by the market.** An investor
making level contributions with no timing intent whatsoever posts a **−9.54 pp/yr** gap
on a `+50%, −20%` path and **+12.21 pp/yr** on the same two returns reversed. Across all
24 orderings of a four-year path with a fixed time-weighted return the gap spans −8.66 to
+9.86 pp and is negative 45.8% of the time. Under 20,000 simulated ten-year paths with
level monthly contributions the gap has **mean +0.15 pp and standard deviation 2.60 pp**.
So the mechanical component is mean-zero and enormous, a persistently negative population
gap needs a cause the mechanics do not supply, and **a single measured gap cannot
identify an individual.**

**The measured cause is not restraint.** Fulkerson, Jordan, Riley and Yan (*FAJ* 82(3),
2026, open access, read in full) apply Hayley's decomposition to Morningstar's own
2015–2024 sample and split a **−0.17 pp** gap into **−0.10 pp of timing and −0.07 pp of
hindsight**. Their Appendix A carries the genuinely mechanical finding: weighting by
end-of-month rather than beginning-of-month assets overstates total return, and
correcting it moves the measured gap from **−2.14% to −0.93%/yr** across Morningstar's
2023–2025 methods. **A large share of the historical behaviour-gap literature is measuring
a weighting convention.** Hayley later attacks his own method too, putting roughly a third
of the remaining gap down to a spurious in-sample correlation, and Keswani and Stolin find
Dichev's result confined to pre-war data and reversing afterwards.

**DALBAR must not be cited, and the defect is a specific step.** Its published method
forms a "cost basis" by **adding up undiscounted contributions** and divides dollar gain
by that sum. There is no discounting of dated cash flows anywhere. It is not a
mis-specified IRR; it is not an IRR. Three independent critics reach the same place and
none is peer-reviewed; DALBAR's own rebuttal concedes the mechanism — *"IRR is neither
necessary nor relevant"*. Morningstar, by contrast, uses a proper IRR, so that objection
does not transfer to it.

**Morningstar disclaims the individual-level reading itself**: *"this estimate is not a
proxy for the average investor's dollar-weighted return"*, and *"for the theoretical
'total market' there can be no 'gap', as for every buyer there is a seller"*. The gap is
zero-sum, so it cannot be a population-wide edge — which is exactly why it belongs to
`AVERAGE_INVESTOR` and nowhere else.

**The actionable finding is product selection, and it is measured.** The gap runs from
**−0.4 pp** on the least-volatile quintile to **−2.1 pp** on the most volatile and
**−13.2 pp** on the most-volatile alternative funds; large blend is **0.0 pp** and US
equity index funds **−0.1 pp**. Morningstar's own reading is that the driver is neither
cost nor management style but **volatility**. So the controllable quantity is choosing
broad, low-volatility, low-tracking-error funds — which is *already* the 49 bp cost line,
and booking it again would be the same decision counted twice.

**But "index fund" is not what closes the gap, and this is where the claim breaks.**
Index funds in aggregate ran a **−1.1 pp** gap, and **international equity index funds
ran −1.6 — twice the gap of *active* international.** The near-zero figure belongs to US
equity index specifically. This matters here because the recommended construction holds
40% of its equity outside the US. Two readings — an ex-US sleeve is genuinely harder to
hold through, or the figure is the mechanical artefact this section opens with — and
**neither is tested here**. What it does establish is that *"hold index funds and the gap
goes away"* is false as stated.

**Status: `exploratory`, and the ceiling is low by construction.** This is a literature
and benchmark-consistency synthesis, not an experiment. The arithmetic above bounds what
the statistic *can* mean; it cannot measure what any real population of investors did.
**It is also the one block on this page not yet pinned by a test** — it wants a small
`studies/investor_return_gap.py` before any feature leans on it.

---

## 3. What probability is actually attainable

| Edge, against 400 bp tracking error | 10 yr | 20 yr | 30 yr | 50 yr | 90% at | 95% at |
| --- | --- | --- | --- | --- | --- | --- |
| 10 bp | 0.532 | 0.545 | 0.554 | 0.570 | 2,628 yr | 4,329 yr |
| 25 bp | 0.578 | 0.610 | 0.634 | 0.671 | 420 yr | 693 yr |
| **50 bp** | **0.654** | **0.712** | **0.753** | **0.812** | **105 yr** | **173 yr** |
| 100 bp | 0.785 | 0.868 | 0.915 | 0.961 | 26 yr | 43 yr |
| 200 bp | 0.943 | 0.987 | 0.997 | 1.000 | 7 yr | 11 yr |

The same 50 bp edge against different tracking errors, reaching 90%: **24 days** at
10 bp, 1.6 years at 50, 6.6 years at 100, 26 years at 200, **105 years** at 400.

| Benchmark | Central edge | TE | 10 yr | 30 yr | 90% at |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stated index | 5.4 bp | 313 bp | 0.522 | **0.538** | beyond any useful horizon |
| Average investor | 15 bp | 150 bp | 0.624 | **0.708** | ~164 yr |
| Own counterfactual | 89 bp | 41 bp | ~1.00 | **~1.00** | ~4 months |

**Read the last row with its conditions.** It is a reference investor with an expensive
active-fund counterfactual, a taxable account, more than one account type and continuing
contributions, against an assumed tracking error. Change any of those and the row moves
towards the first.

Read the table the other way and it stops being about markets: against the 313 bp of
tracking error the index-relative budget carries, thirty years can only *demonstrate* an
edge of about 73 bp/yr at 90% confidence and fifty years 57 bp — against a central estimate
of 5.4 bp. **No probabilistic line in this budget is demonstrable from an
investor's own experience**, and the gap is now more than an order of magnitude. Evidence has to come from somewhere other than a track
record.

---

## 4. Assumptions, open questions, provenance

**Assumptions.** Budget components' relative returns are mutually independent — plainly
false for a factor tilt and a rebalancing policy on the same portfolio, and false in the
direction that widens dispersion. The edge in §3 is treated as *known* rather than
estimated, which removes the dominant source of uncertainty and makes every probability
an upper bound. Every tax figure is US federal and jurisdiction-specific.

**Open questions.**

1. **The factor line has no capture term, so it needs no benchmark for one.** A capture
   fraction is an HML loading measured a second way
   ([Experiment 007](long-only-capture.md#the-correction-a-capture-fraction-is-a-loading-so-it-may-not-multiply-one)),
   and a loading is taken against a factor rather than against a portfolio. What replaces
   it is open in a smaller way: **whether a loading estimated on 36 to 72 months of a
   fund's history forecasts the next 36 to 72**, which nothing here tests.
2. **Tax outside the US, and the step-up interaction.** The harvesting alpha sits between
   the after-liquidation 1.10% and the before-liquidation 1.47% depending on whether the
   low-basis position is ever sold, which turns on §1014 and on charitable donation —
   both outside every model cited.
3. **Tracking difference and after-tax return of actual funds.** No all-in figure was
   retrievable, so the 3 bp expense ratio is a floor on holding cost rather than the whole
   of it.
4. **Whether equal weighting inside equities is a size tilt or a harvest.** The harvest is
   worth about 4 bp/yr at 30 years, so essentially all of any observed equal-weight
   advantage must be a factor tilt.
5. **Whether the 15 bp behaviour line should be split.** The measured gap for the products
   this repository recommends is 0.0 to −0.4 pp and for the products it rejects runs to
   −13.2 pp. The line is probably two different quantities, and separating them requires
   deciding how much of the volatility effect the 49 bp cost line has already been paid
   for.

**Reproducibility.** All figures regenerate with
`uv run pytest tests/unit/test_studies_*.py`; simulations use `numpy.random.default_rng`
with the committed seed `20260812`, closed forms use no randomness. Sources that could not
be retrieved are named on the pages that wanted them; the register is in
[the evidence base](evidence-base.md) §3.

---

## Consequence for this repository

1. **Declare the objective**: net geometric growth, equivalently expected log wealth, with
   a stated drawdown constraint, recorded as a **preference** justified by Breiman's
   asymptotic theorem — not as a proof that expected-terminal-wealth investors are wrong.
2. **Every result carries a benchmark and a certainty class.** A number without both is
   not reportable.
3. **Report probability of outperformance by horizon, never a point estimate of edge.**
   "5.4 bp with a 0.54 thirty-year probability" is honest output; "+5.4 bp/yr" is not.
4. **Rank features by their effect on the budget.** Cost, tax and account selection is
   worth roughly 89 conditional basis points. Rebalancing policy is worth about 2.4
   probabilistic ones — less than the round-trip spread on a small-cap ETF. **The
   optimiser is the least valuable part of the application.**
5. **Do not build a rebalancing-bonus feature.** A tool showing an expected rebalancing
   gain would have to show 2.4 bp/yr against a 5th percentile of −80 bp/yr — and
   [Experiment 003](rebalancing-policy.md) has since measured the real figure negative.
6. **Do not build a behaviour-gap feature, and never let "not trading" into the
   contractual budget.** The 15 bp line may be displayed, labelled `AVERAGE_INVESTOR` and
   `probabilistic`, and never summed with it. The application must not compute a personal
   behaviour gap: the source disclaims that reading, the statistic carries ~2.6 pp of
   mechanical noise, and no study has measured it for an identifiable individual.
</content>
