# Part A — the portfolio for one investor, derived

`as of 2026-08-23`. Working analysis behind `/portfolio`. Not personalised advice; every
figure is a function of stated inputs.

**The investor.** Roughly equal nominal thirds in a Roth, a traditional tax-deferred
account and a taxable brokerage account. Multi-decade horizon. Contributing 5–15%/yr.
Wants ETFs simple to hold. Willing to run a rule-based strategy only with real
understanding of it. US federal taxes; state tax excluded and additive.

Sources: `.claude/scratch/claims-ledger.md`, `docs/research/portfolio-recommendation.md`,
`docs/research/final-construction-test.md`, `docs/research/trend-weight-under-uncertainty.md`,
`docs/research/structural-and-tax-edges.md` §8, `src/content/shelf.ts`,
`src/content/placement.ts`, `src/lib/placement.ts`, `.claude/scratch/market-scan-2026.md`,
`.claude/scratch/stacking-thesis-verdict.md`.

---

## 1. The construction

Taken from the repository's recommended construction, which is what Experiment 016e scored
(`docs/research/final-construction-test.md`, spec `3a86ef6f…`, run `cd2fb4b9…`). Not a new
invention.

### Capital weights — the only vector anyone types

| Ticker | Fund | Capital weight | Engine | Gross fee | Net cost after lending |
| --- | --- | ---: | --- | ---: | ---: |
| RSST | Return Stacked U.S. Stocks & Managed Futures | 25% | US equity + trend | 99 bp | 99 bp (lending unread) |
| VTI | Vanguard Total Stock Market | 24% | US equity | 3 bp | 1.16 bp |
| VXUS | Vanguard Total International Stock | 16% | International equity | 5 bp | 1.43 bp |
| VTV | Vanguard Value | 15% | US value | 3 bp | 2.70 bp |
| AVDV | Avantis International Small Cap Value | 10% | Developed ex-US small value | 36 bp | 30.03 bp |
| IDMO | Invesco S&P International Developed Momentum | 5% | International momentum | 25 bp | 22.59 bp |
| AVES | Avantis Emerging Markets Value | 5% | Emerging value | 36 bp | 29.21 bp |
| | **Total** | **100%** | | **33.4 bp** | **31.3 bp** |

Weighted gross fee computed here is 33.4 bp; 016e's frozen run reports **33.9 bp** for the
same arm (small fee-grid differences). Net-of-lending weighted cost of **31.3 bp/yr** is
derived here from the eight funds' Form N-CEN medians in
`final-construction-test.md` §2 plus VTI 1.16 and VXUS 1.43 from
`structural-and-tax-edges.md` §6.1.

### Notional exposure — a derived audit quantity, never typed

RSST delivers 1.072 of US equity and 1.00 of managed-futures notional per dollar of
capital (Form N-PORT 2026-04-30; `src/content/shelf.ts`).

| Exposure | Notional, % of capital | Where it comes from |
| --- | ---: | --- |
| US equity | 65.8 | VTI 24 + VTV 15 + RSST 25 × 1.072 |
| International equity | 36.0 | VXUS 16 + AVDV 10 + IDMO 5 + AVES 5 |
| Managed futures (trend) | 25.0 | RSST 25 × 1.00 |
| **Gross** | **126.8** | 1.268× |

Equity notional is 101.8%. Bonds: zero. That is a position, not an oversight, and the
equity-versus-bond split is a larger decision than everything else on this page —
60/40 to 90/10 was worth **+127.1 bp/yr against 485 bp of tracking error** (B3).

### What the evidence can and cannot separate

The construction tournament scored four candidate constructions against a leverage-matched
control: recommended +2.20, AVUV-instead-of-VTV +2.35, previous recommendation +1.92,
investor's original eight +2.49 pp/yr — **a spread of 0.57 inside detection floors of
2.75–3.33**. Ranking them is reporting noise, and the repository says so.

So the fund choices below are made on cost, spread, turnover and holdability, and are
stated as such:

- **VTV over AVUV.** Unresolved on both admissible windows (−0.15 pp/yr [−0.68, +0.34]
  against a 0.68 floor). Picked on cost: 2.70 bp net against 24.54, and 8%/yr turnover
  against AVUV's higher figure. AVUV's extra exposure over VTV is 87% size, on a premium of
  +0.33 pp/yr against a 2.47 floor.
- **RPV rejected**, not on exposure. It buys HML +0.369 over VTV while selling RMW −0.204
  and UMD −0.173, at 42%/yr turnover against VTV's 8%. Negative under all four premium
  scenarios.
- **SPMO not added.** Better than MTUM on every knowable dimension (13 bp, 44% turnover)
  and +0.02% a year at a 5% weight against a −0.14% to +0.18% range, with an active leg
  +0.626 correlated with IDMO's, which the portfolio already owns.
- **AVDV kept.** +0.28 pp/yr [+0.05, +0.56] against a 0.29 floor — short of resolution by
  0.01, positive in the full window and all seven declared sub-periods, reproduced
  independently at +0.29 on the unlevered pair. Its net cost is 30.03 bp, not the 36 bp
  headline.
- **RSST over CTAP, MATE and JPFP.** Not on return, which cannot separate them, and no
  longer on the funding rule (RSST δ −0.07, CTAP −0.027, MATE −0.159 all keep the whole
  gap). On age, size, counterparty and spread. See §4.

### Two arithmetic facts that carry the construction

1. **The funding rule is worth more than any sleeve, and it contains no sleeve property.**
   `a_p − σ_p²` ≈ **+2.44 pp/yr** for a 100%-equity base. RSST's δ of −0.07 keeps
   essentially all of it; a standalone managed-futures fund keeps none. This is why the
   trend leg is bought through a stacked wrapper rather than by selling equity.
2. **Stacking has a hard ceiling.** At the ρ = 0.435 measured among this portfolio's own
   active sleeves, an unlimited stack of 55%-likely bets reaches **0.576** and stops. Eight
   tickers were worth 3.71 effective independent bets. This portfolio is about **93%
   substitution**, so its edge is a weighted *average* bounded by its best single sleeve,
   not a sum. Only the RSST line is financed.

---

## 2. The 25% versus 30% trend decision

### The trade, stated

| | 25% wrapper | 30% wrapper |
| --- | --- | --- |
| Capital weights | RSST 25, VTI 24, VTV 15, VXUS 16, AVDV 10, IDMO 5, AVES 5 | RSST 30, VTI 19, VTV 15, VXUS 16, AVDV 10, IDMO 5, AVES 5 |
| Gross notional | 1.268× | 1.322× |
| US equity notional | 65.8% | 66.2% |
| Trend notional | 25% | 30% |
| Weighted gross fee | 33.4 bp | 38.2 bp |
| Weighted net cost | 31.3 bp | 36.2 bp |

The five points come out of VTI. Because RSST carries 1.072 of US equity per dollar, US
equity notional barely moves (65.8 → 66.2) and the whole change is +5 points of trend.

**Growth.** 30% beats 25% by **0.50 pp/yr [0.23, 0.77] against a 0.39 floor** — the only
whole-portfolio comparison in either tournament that clears its own resolution, negative for
the 25% arm in all seven declared sub-periods (−0.19 to −0.94). The tournament is explicit
that this is a *leverage* result, not a construction one: at the panel's realised 9.83% US
equity premium, more notional wins.

**Holdability.** Abandonment probability over thirty years at a −20% relative-drawdown
trigger runs about **17% at 30% against 11% at 25%** at the premium prior's median, and
**66.7% at 30% if the premium is gone entirely**. Holdability and return are a bet on the
same parameter — the same risk twice, not a diversification of it.

**Price of the step.** The 0.25 → 0.30 step buys +15 bp/yr of expected growth for +8.2
points of abandonment probability, about **1.81 bp per point** with capitulation priced
inside the path. Every step from 0.15 to 0.40 still buys more than 1 bp per point; the elbow
that used to sit at 0.20 was an artifact of a units error and no longer exists.

**Four routes bracket the weight** and 25% is the only one all four admit: variance
minimisation 21.6% [10.3, 32.8]; growth subject to holdability 15–25%; minimax regret 25%
(robust 20–30%); construction tournament no interior optimum.

### Recommendation: 30%

For *this* investor. Three reasons, in order of weight.

1. **The comparison that favours 30% is the only one in the programme that clears its own
   floor.** Nearly everything else here is unresolved. Discarding the one resolved
   measurement in favour of four routes that disagree with each other is choosing the
   weaker evidence.
2. **A contribution stream is what carries a position through a drought.** The abandonment
   model's trigger is a relative drawdown, and the mechanism that defeats it is new money
   arriving at a low price. This investor contributes 5–15%/yr, which is 2.5 to 7.5 times
   the largest rebalancing rotation the portfolio needs.
3. **Zero is the worse extreme.** Over the panel's one flat-to-negative equity decade
   (1999-03…2009-02, equity −2.55%/yr) a 30% overlay contributed about **+9.5 pp/yr above
   its own complement** and turned that decade from −2.55%/yr to about +0.05%/yr, against
   +0.21 pp/yr in ordinary decades.

**Choose 25% instead if you would sell it.** A portfolio held beats a better one abandoned,
and the honest test is whether a decade of the sleeve contributing nothing while equities
rise would end with you selling. If the answer is maybe, take 25% — every route admits it,
and the growth you give up is half a point a year against a 6.0% tracking error you would
never be able to attribute anyway.

**One caveat that cuts against 30%.** The resampled probability that the overlay is the
deeper drawdown is 6.9% at 30% of notional and doubles from 10.8% to 18.9% between 58% and
60%. That is a cliff, not a ramp, and it is why the weight cannot simply be raised further.

---

## 3. The placement problem

This is the new work. Method is `src/lib/placement.ts` (`taxableCostBp` −
`shelteredCostBp`), applied at fund level exactly as
`research/src/portfolio_edge/studies/investor_placement.py` does. Arithmetic reproduced in
`scratchpad/placement.mjs`.

```
priority = Box1a yield × [q × cgFraction + ordinary × (1 − cgFraction)]
           − creditable foreign tax yield
```

The second term is the whole of the correction, and it is zero for everything except a
foreign holding. §408(e)(1) exempts an IRA from tax, so there is no US tax for §901 to
credit against and a §904 numerator of zero: **foreign withholding is paid and permanently
lost inside a traditional IRA and a Roth alike.**

### 3.1 Inputs

| Fund | Box 1a yield | At capital-gain rates | Creditable foreign tax | Provenance |
| --- | ---: | ---: | ---: | --- |
| RSST *(recognised)* | 9.273% | 10.5% | 0 | Tidal Trust II N-CSR, FYE 2026-01-31 |
| RSST *(distributed)* | 1.285% | 85.7% | 0 | the same filing |
| VTI | 1.067% | 100% *(assumed)* | 0 | Vanguard fund-yield endpoint, 2026-07-31 |
| VTV | 1.810% | 100% *(assumed)* | 0 | **derived**: trailing 12-month yield 1.81%, StockAnalysis, read 2026-08-23 |
| VXUS | 2.678% | 58.4% *(derived)* | 0.1777% | **derived**: cash yield 2.50% grossed by Vanguard's filed 7.11% of ordinary dividends; qualified fraction a 75/25 blend of VEA's filed 66.27% and VWO's 34.63% |
| AVDV | 2.789% | 66.3% *(derived)* | 0.1693% | **derived**: cash yield 2.62% grossed at the developed ex-US rate of 6.068% of Box 1a; qualified fraction from VEA |
| IDMO | 4.403% | 25.6% *(filed)* | 0.1229% | Invesco ETF Trust II N-CSR, FYE 2025-10-31 |
| AVES | 3.910% | 44.5% *(filed)* | 0.4598% | Avantis 2025 tax centre and ICI file |

Three of eight yields are filed for this exact construction; three are derived and flagged.
Every derived assumption pushes its fund toward the taxable account, so the plan is
conservative in the direction it is uncertain. Yields mix windows, which is the input a
placement ranking is most sensitive to and none of these is point-in-time.

### 3.2 The ranking, at three brackets

Basis points per dollar of shelter capacity. Wrapper on the recognised basis.

| Fund | 23.8% | 18.8% | 15% |
| --- | ---: | ---: | ---: |
| **RSST** | **361.78** | **315.41** | **213.79** |
| **IDMO** | **148.22** | **126.20** | **83.25** |
| AVES | 83.98 | 64.43 | 32.21 |
| AVDV | 65.45 | 51.51 | 33.38 |
| VXUS | 64.91 | 51.52 | 32.43 |
| VTV | 43.08 | 34.03 | 27.15 |
| **VTI** | **25.39** | **20.06** | **16.01** |
| *RSST (distributed)* | *33.72* | *27.29* | *20.93* |

**Every international fund outranks every US equity fund at every rate, and VTI is last at
every rate.** This is the opposite of "hold international in taxable for the foreign tax
credit," and the reason is that the credit is small and the yield gap is not.

Sheltering all four international funds destroys **7.45 bp/yr** of foreign tax credit
permanently (repository figure for the eight-fund original: 8.81 bp/yr). Sheltering them
buys back far more: VXUS alone is worth 64.91 bp per dollar sheltered at 23.8%, against
VTI's 25.39. The credit is not close to deciding it.

The break-even is exact. `q* = u·w·y_i/(y_i − y_d)` puts the developed break-even at
**10.52%**, below every positive US qualified rate. The US schedule offers 0%, 15%, 18.8%
and 23.8%, so developed ex-US always belongs in shelter ahead of US equity. That is a fact
about the bracket schedule, not about the funds. The 0% bracket is a trap: §904 limits the
credit to US tax on foreign-source income, and there is none, so a 0%-rate investor forfeits
the withholding in both locations and the credit argues for neither.

**A high-turnover momentum fund at a 5% weight outranks almost everything else.** IDMO
designates 25% qualified dividend income against **105% portfolio turnover**, and its
December distribution of $0.68417 of short-term and $0.27579 of long-term gain per share
takes its taxable distribution to 4.40% of net assets with only 25.6% at capital-gain rates.
The ETF in-kind shield does not survive 105% turnover. Nothing about its 5% size or its
"momentum" label suggests it should be a placement priority, and it is second in the queue
at every bracket.

**The order is stable across the bracket range.** Only AVDV and VXUS change places, and at
18.8% they are 0.01 bp apart. Treat them as tied and order them by whatever is
operationally simpler.

### 3.3 The wrapper, and why its unresolved input does not stall the decision

RSST routes its trend leg through a wholly-owned Cayman controlled foreign corporation whose
net income is included in the fund's taxable income each year. Its undistributed ordinary
income went from 1.40% to **8.56% of net assets in one year** while the fund distributed
0.33%. Two readings:

- **Distributed** — count only what shareholders were taxed on: 33.72 bp/yr at 23.8%.
  Corroborated independently by the fund's own prospectus, 17.17%/yr before tax against
  16.85% after taxes on distributions, a 32 bp gap.
- **Recognised** — count the 9.27% of net assets the fund recognised: 361.78 bp/yr.

Computed here for this construction at 23.8% and f = 1, at the recommended 30% wrapper
(25% figures in brackets):

| | if the audited (distributed) basis is right | if the accrual is distributed |
| --- | ---: | ---: |
| Shelter the wrapper anyway | **−1.34 bp/yr** *(−0.87)* | 0 |
| Follow the audited-basis ranking | 0 | **−45.58 bp/yr** *(−29.64)* |

**34 to 1 at both weights.** The repository's figures for the eight-fund original are 1.12–8.54 bp/yr
against 42.62–89.88 bp/yr — ten to one at every bracket and every open-menu fraction. Both
readings agree: shelter the wrapper, and leave the measurement open. The review trigger is
the fund's next December distribution.

### 3.4 The plan — account by account, at equal nominal thirds

Shelter capacity is 66.7% of the portfolio. Assume `f = 1`, the whole tax-deferred third in
a rollover IRA with an open menu. Stated at the **recommended 30% wrapper**; the 25%
variant is beside it and moves nothing except how much VTV spills into taxable.

| Account | Holdings | Weight (30%) | Weight (25%) | Why |
| --- | --- | ---: | ---: | --- |
| **Traditional** *(33.3%)* | RSST | 30.0 | 25.0 | First in the queue by a factor of 2.4 over anything else. It goes in the *traditional* rather than the Roth for three reasons that are not the drag: the trend leg is the least-established expected return in the portfolio and the Roth's premium is proportional to expected return; RMDs force the traditional and never the Roth, and a trend overlay after a strong trend year is exactly the sleeve you would be trimming; and the traditional makes the government a `t`-share partner in the dispersion as well as the mean, which is where the most uncertain sleeve belongs. |
| | IDMO | 3.3 | 5.0 | Second in the queue at every bracket. 105% turnover and 25.6% at capital-gain rates. Also the weakest premium held — momentum's pooled detection floor of 4.98 pp/yr is the worst measured here — so it belongs on the government's side of the partnership too. |
| | AVES | — | 3.3 | Third in the queue. Any split between two shelters is an artifact of exact thirds and has no tax consequence, because both sides of it are sheltered. |
| **Roth** *(33.4%)* | IDMO | 1.7 | — | |
| | AVES | 5.0 | 1.7 | Emerging value carries the largest measured HML premium anywhere here, +7.58 pp/yr, and is `unresolved`. |
| | AVDV | 10.0 | 10.0 | Fourth in the queue, and the highest-conviction tilt in the construction: +0.28 pp/yr [+0.05, +0.56] against a 0.29 floor. Highest expected return that fits, so the Roth's never-taxed growth is spent on it. |
| | VXUS | 16.0 | 16.0 | Fifth in the queue, 0.01 bp from AVDV at two of three brackets. Forfeits 2.84 bp/yr of credit and saves 64.91 bp per dollar sheltered. |
| | VTV | 0.7 | 5.6 | The shelter runs out here. |
| **Taxable** *(33.3%)* | VTV | 14.3 | 9.4 | 1.81% yield, fully qualified, 8%/yr turnover, no capital-gain distribution. |
| | VTI | 19.0 | 24.0 | Last in the queue at every rate. The cheapest, broadest, lowest-turnover fund in the portfolio is the one that belongs in the taxable account, because its 1.07% fully qualified yield is the smallest tax bill per dollar of shelter it would consume. |

**At a 30% wrapper the traditional third is 90% one fund.** That is the arithmetic warning
already on record: a 30% wrapper consumes nine tenths of a one-third pre-tax account. The
2026 mandatory-Roth catch-up rule makes it worse over time — SECURE 2.0 §603 is effective
for 2026, and a participant whose 2025 FICA wages from the sponsoring employer exceeded
$150,000 must make every catch-up dollar as designated Roth, removing $8,000 to $11,250/yr
of pre-tax capacity. The pre-tax account this wrapper lives in grows more slowly every year,
for exactly this investor.

**Roth and traditional are not interchangeable.** The recurring drag is identical in both —
zero for everything except the forfeited foreign credit, which is also identical. What
separates them is that Roth growth is never taxed, so the Roth's advantage is proportional
to expected return, while a traditional balance is shared with the government at the
withdrawal rate. Exactly: swapping growth factor `A` in a Roth of size `R` for factor `B` in
a traditional of size `T` at withdrawal rate `t` changes terminal wealth by `(R − T(1−t))(A −
B)`. At equal nominal thirds, a 24% withdrawal rate, 30 years, a 30% sleeve swapped and a
1 pp/yr expected-return gap, that is **1.96 bp/yr**. It is a forecast, and it is not free:
holding the same after-tax allocation, moving a sleeve to the Roth raises your share of its
dispersion by the same factor it raises the mean.

Which is why the wrapper goes in the traditional and the tilts go in the Roth. The naive
rule — shelter the highest drag — points the other way and puts the wrapper in the Roth.
The drag is the wrong instrument for that question, because it is the same number in both
accounts.

**A tax-deferred balance is not the investor's money.** At a 24% withdrawal rate, $100,000
of traditional IRA is $76,000 of investor wealth. Equal nominal thirds are Roth 37.84% /
traditional 28.76% / taxable **33.41%** after tax — the taxable account is the *larger*
constraint after tax, not the smaller. The ranking above is stated per dollar of shelter
capacity precisely to sidestep that.

### 3.5 What the plan is worth

Three benchmarks, and their answers do not add.

Computed at the recommended 30% wrapper. The 25% figures are 121.44 / 39.43 / 33.75 / 6.41.

| Control | Value, 23.8%, recognised | Value, 23.8%, distributed |
| --- | ---: | ---: |
| Everything held taxable | +137.38 bp/yr | +38.96 bp/yr |
| Pro-rata: every fund one third in each account | +38.47 bp/yr | +5.66 bp/yr |
| **A default-choosing investor with the same accounts** | **+2 to +7 bp/yr** *(repository, booked)* | same |

The first is not a saving anyone can capture, because nobody holds everything taxable. The
second is the value of getting the *order* right, and the repository's own scope note says a
pro-rata control is **infeasible** for an investor whose shelter is partly a captive
employer plan, so measuring against it overstates the result. The booked figure against a
feasible control is **−2.04 / +6.66 / +5.41 bp/yr** at `f` = 0 / 0.5 / 1 at the top bracket,
falling to −0.40 / +2.56 / +2.04 at 15%.

**So the honest total value of placement is +2 to +7 bp/yr against the investor's own
counterfactual, and it is negative if the tax-deferred third is wholly captive.** Not the
121 bp headline. Four lines were withdrawn to get there: a rebalancing hurdle avoided is not
a saving; lot selection is mutually exclusive with never selling; the wrapper's undistributed
accrual is conditional on a distribution decision the fund has not made; and fee and
fund-structure lines are measured against a cheap index and belong to a different benchmark.

The one line that is larger than the whole ordering decision: **never having to sell in the
taxable account is worth about 14 bp/yr.** Realising 10% of standing gain a year costs
41.5 bp of the 84.1 bp deferral at a 30-year horizon.

### 3.6 Where a captive employer menu breaks it

A typical employer 401(k) menu holds a broad US index fund, a developed ex-US one and an
emerging one, and nothing else this portfolio owns. Of the seven lines here, **only VTI and
VXUS can go in it.** No employer plan offers a return-stacked ETF, an Avantis systematic
fund or a single-factor momentum ETF.

Write `f` for the share of the tax-deferred third sitting in a rollover IRA. The
unconstrained plan shelters VXUS at 16% of the portfolio, so the employer plan is free while
it is no larger than that:

```
1 − 0.16/0.3333 = 0.52
```

**The menu binds below f = 0.52** for this construction. The repository derives 0.55 the
same way for the eight-fund original, which shelters VEA 10 + IEMG 5 = 15%.

At `f = 0`, computed here at the recommended 30% wrapper:

| Account | Holdings |
| --- | --- |
| Employer plan *(33.3%)* | VXUS 16.0, **VTI 17.3** |
| Roth *(33.3%)* | RSST 30.0, IDMO 3.3 |
| Taxable *(33.4%)* | **AVDV 10.0**, **AVES 5.0**, VTV 15.0, IDMO 1.7, VTI 1.7 |

**VTI, last in the queue at every rate, is forced into shelter at 17.3% while AVDV and AVES
are evicted to taxable.** That is the exact inverse of the ranking, imposed by a fund lineup
rather than by any tax fact. Cost, computed here at 23.8%: **9.12 bp/yr** at a 30% wrapper
and 6.00 bp at 25% — larger than the whole booked placement edge either way. The
repository's figure for the eight-fund original is 9.09 bp, which this reproduces.

Two consequences.

- **Consolidating an old employer balance into a rollover IRA buys the whole f = 0 to
  f = 0.5 improvement for the cost of a form.** It is the cheapest lever available.
- **At f = 0 the wrapper has no choice but to take the Roth**, because the traditional third
  cannot hold it. That is a second and separate cost of a captive plan, and it is the one
  place the plan above cannot be executed as written. The Roth is 33.3% against the wrapper's
  25%, so it fits — but at a 30% wrapper the margin falls to 3.3 points, and above 33.3% the
  wrapper spills into taxable and the weight itself becomes the thing to reconsider.

### 3.7 Rebalancing feasibility

Restoring the target without a taxable sale is reachable **iff every fund's taxable holding
is at or below its portfolio target weight** (exact, not a heuristic). At a 30% wrapper: VTV
14.3 against a 15 target, VTI 19.0 against 19.0. VTI sits exactly at target, so it has zero
headroom, and the constrained direction is selling US equity to buy international. That rotation needs
roughly two points of the portfolio a year; contributions of 5–15%/yr cover it 2.5 to 7.5
times over.

The clean fix is to leave one or two points of headroom on VTI — hold 18 in taxable and 1 in
the Roth at a 30% wrapper, or 23 and 1 at 25%. The repository's joint solution costs **0.28 bp/yr** for a 1 pp headroom band. A
forced taxable sale costs hundreds of times a spread.

---

## 4. The two new findings, checked against the recommendation

### CTAP's 33 bp bid-ask spread

`capital-efficiency-and-breadth.md` concluded that neither the funding rule nor the fee
table separates RSST, CTAP and MATE. The market scan found **CTAP's 30-day median bid-ask
spread is 0.33% against RSST's 0.09%** (Rule 6c-11(c)(1)(v) disclosures, read 2026-08-22).
A round trip in CTAP costs about 66 bp; a one-way purchase adds 33 bp to a first-year all-in
cost of about 0.81%.

**Does it change the recommendation? No — it confirms it, and it retires a caveat.** The
recommendation already names RSST. The spread finding removes the last reason to reopen the
comparison: the three wrappers were tied on δ and tied on all-in fee, and the tie is now
broken by 24 bp/yr on a one-year hold, on a shelf whose entire fee dispersion is 18 bp. For
an investor who rebalances annually, CTAP is the dearest of the three, not the cheapest.

What it does change is a *review trigger*. CTAP's waiver lapses on 2026-12-04, taking it to
about 0.99% all-in. If the waiver is renewed, its spread tightens with age and size, and its
82.48%-of-net-assets bilateral swap exposure to one bank falls, the comparison is worth
reopening. Not before.

### Fidelity's $100 per ETF purchase

Fidelity began charging **$100 per trade** on ETFs from issuers refusing platform fees on
2026-06-01; Schwab has confirmed a comparable programme for year-end 2026. On a $10,000
purchase that is **100 bp on day one** — larger than the entire annual expense ratio of
every fund here except the wrapper, and about three times AVDV's whole annual net cost.

**Does it change the recommendation? It changes how you execute it, not what you hold — and
it is the one open item that could change what you hold.**

The exposure is structurally asymmetric. Vanguard, iShares, Invesco and American Century
(Avantis) are not plausibly at risk. **Tidal, which issues RSST, is exactly the profile that
is** — a boutique with little fee revenue to hand over. No shelf issuer appears on any
published list, but **Fidelity's live service-fee list returns HTTP 403 to automated fetches
and could not be read**, so this is unverified rather than cleared.

Three concrete consequences for a contributing investor:

1. **Check your broker's service-fee list before the first purchase**, for RSST above all.
2. **A per-trade fee is fatal to monthly contributions and survivable annually.** $100 twelve
   times a year on a $200,000 portfolio is 60 bp/yr. Once a year on the same portfolio is
   5 bp. If RSST carries the fee at your broker, either move that line to a broker that does
   not charge it, or buy it once or twice a year and direct monthly contributions at the
   index funds.
3. **This is a reason to prefer the wrapper over a standalone managed-futures fund a second
   time.** One line rather than two means one exposed purchase rather than two.

One more thing the scan turned up that is *not* a change yet. **RSIT** — Return Stacked
International Stocks & Managed Futures, inception 2026-05-06, 0.98%, $68.53m, spread 0.15% —
is the international twin of RSST, with a base leg near 1.00 and δ ≈ 0.00. It lands exactly
where this construction is thin. It is three and a half months old with no N-PORT and no
measurable loading, so nothing can be promoted from it. Revisit when it has 24 filed months.

---

## 5. The failure modes

### What losing looks like

The failure mode is not a crash. It is a decade of quiet monthly underperformance against
the most familiar comparator.

| Sleeve | Worst run behind | Duration | Recovered? |
| --- | ---: | ---: | --- |
| US value tilt | −54.3% | 17.7 years | No |
| International sleeve | −69.0% | 18.2 years | No |
| Financed trend, net of the equity it displaces | −59.9% | 11.2 years | No |

Every one of those is inside the history this construction is built from. None of them is a
tail scenario.

Add the portfolio-level picture: maximum drawdown **−50.3%** against the levered control's
−64.6%, longest run under water **42 months**, and a worst decade against its own control of
**−1.15 pp/yr for seventeen years** post-2009, against +8.15 pp/yr through the 1999–2009 flat
equity decade. The asymmetry is the wrapper's.

### The reframing fact

**At this portfolio's tracking error, thirty years of holding it cannot establish whether it
worked.**

- Against a leverage-matched cheap index: **+2.20 pp/yr [+0.05, +4.57] against a 2.83 floor
  — 59 years to separate**, at 6.0% tracking error.
- Against a same-split cheap core: tracking error about **400 bp/yr**, of which 372 bp is
  the trend overlay. The thirty-year detection floor at 400 bp is **93 bp/yr**, against a
  central edge of **92 bp**. The portfolio is designed so that thirty years of holding it
  cannot settle the question.
- The arithmetic is exact and horizon-free: `T = (z·s/e)²`. The same 50 bp edge reaches 90%
  confidence in 24 days at 10 bp of tracking error and 105 years at 400 bp. And every
  probability computed that way is an **upper bound**, because it assumes the edge is known.
- An estimated edge imposes a second ceiling no horizon removes: `P(T) → Φ(e/τ)`. Path noise
  washes out; error in the mean does not. Thirty years converts an unsignable premium into a
  longer wait for the same coin flip.

The load-bearing precommitment: **the comparator must be leverage-matched.** Comparing a
levered portfolio with an unlevered index credits the leverage to the strategy on the way up
and blames the strategy for it on the way down.

And a monitoring rule that follows from it: **do not set a performance review for a
diversifying sleeve.** At a 30% weight such a sleeve underperforms in 43.8% of resampled
ten-year histories even when its premium is positive, so a performance trigger removes it for
doing what it was bought to do. Require three consecutive readings. A bar must be coarser
than the instrument that reads it — the trend-weight page proposed removing the sleeve below
a 0.70 loading, and the first measurement returned 0.681 on an interval of [0.406, 0.955]
that spans the bar twice over. The defensible bar is the wrapper's break-even against a
standalone fund, **0.19 to 0.27** at a 25% weight, and the measurement clears it comfortably.

### The one thing on this page nobody has measured

Three of seven lines have no measured factor exposure of any kind. The wrapper's trend
loading rests on **31 filed months**, roughly one market regime, on an interval that cannot
tell one dollar of delivered trend from four fifths of one. Its financing spread is disclosed
by no issuer, because futures financing lives in the basis, and it decides the *sign* of the
overlay's contribution. **52% of the managed-futures ETFs listed in 2019 had stopped filing
by the end of 2025.** RSST is under three years old.

---

## 6. What would change this

Ordered by how much it moves the answer.

1. **Your own numbers.** The rollover share `f` of the tax-deferred third — it moves the
   booked placement line from −2.0 to +6.7 bp/yr and decides whether AVDV can be sheltered
   at all. Your maximum tolerable drawdown and months underwater, which is the single most
   valuable missing input in this repository and is not a research task. Your bracket.
2. **The equity-versus-bond split**, which this construction sets at 100% equity by omission
   and which is worth more than every tilt combined.
3. **RSST's trend loading refreshed at 48 filed months, around 2027-09.**
4. **The fund-level financing spread**, which decides the sign of the overlay's contribution.
5. **RSST's next December distribution**, which resolves the recognised-versus-distributed
   reading behind the placement's conditional line.
6. **Whether your broker charges $100 per purchase on the wrapper.** Unverified; HTTP 403.
7. **CTAP's waiver on 2026-12-04**, and its spread and counterparty concentration after it.
8. **RSIT at 24 filed months**, if the international sleeve is ever to be financed too.

---

## Verified, derived, assumed

**Verified from the repository.** Every tournament figure, interval, detection floor and
sub-period in §1, §2 and §5, from `final-construction-test.md` and run `cd2fb4b9…`. Every
filed tax characteristic for RSST, VTI, IDMO and AVES, and the 23.8/18.8/15 priorities for
those four, from `structural-and-tax-edges.md` §8 and `src/content/placement.ts`. Net costs
from 50 fiscal years of Form N-CEN. Wrapper structure and δ from Form N-PORT 2026-04-30.
Spreads and the broker programme from `.claude/scratch/market-scan-2026.md`.

**Derived here, and reproducible from `scratchpad/placement.mjs`.** VTV, VXUS and AVDV
priorities at all three brackets. The f = 1 and f = 0 fill orders for the seven-fund
construction at both wrapper weights. The 34-to-1 wrapper regret ratio. The 0.52
menu-binding fraction. The 9.12 bp menu cost at 30% and 6.00 at 25%. The 7.45 bp of forfeited credit. Weighted net cost of 31.3 bp at a 25% wrapper
and 36.2 bp at 30%. The notional decomposition and the 126.8 gross.

**Assumed.** VTV, VXUS and AVDV yields are trailing-twelve-month figures from an aggregator
read 2026-08-23, not sponsor filings. VXUS's and AVDV's qualified fractions are blends of
VEA's and VWO's filed figures, not their own. AVDV's withholding rate is VEA's. VTI's, VTV's
and the wrapper's qualified fractions are assumed at 1.00. State income tax is excluded and
additive; it compresses every gap without reordering them. Equal *nominal* thirds are
assumed; after tax they are 37.84 / 28.76 / 33.41.
