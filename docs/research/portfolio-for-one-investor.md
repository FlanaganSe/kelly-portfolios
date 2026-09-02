# Part A — the portfolio for one investor, derived

`as of 2026-09-01`. Working analysis behind `/portfolio`. Not personalised advice; every
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

Taken from the construction Experiment 016e scored
(`docs/research/final-construction-test.md`, spec `3a86ef6f…`, run `cd2fb4b9…`). Not a new
invention.

**The table below is the 25% arm, which is what was tested and is not what is recommended.**
§2 takes the wrapper to 30% and VTI to 19%, which is the vector `/portfolio` publishes and
the one every figure record on the site carries. Nothing else in the construction changes,
so §1's fund-by-fund reasoning applies to both.

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

RSST's 2026-04-30 Form N-PORT holds SPLG at 74.09% of net assets and S&P 500 e-mini futures
at 30.94%, so the fund delivers **1.050** of US equity per dollar of capital (1.117 counting
its 6.63% Nasdaq-100 future, which may belong to the trend sleeve) and 1.00 of
managed-futures notional. `src/content/shelf.ts` carries **1.072**, which adds 33.1% of
e-mini; that figure does not appear in the filing and the client content agent reconciles
it. Both are shown (`as of 2026-09-01`).

| Exposure | Notional at 1.050 | At the shelf's 1.072 | Where it comes from |
| --- | ---: | ---: | --- |
| US equity | 65.3 | 65.8 | VTI 24 + VTV 15 + RSST 25 × leg |
| International equity | 36.0 | 36.0 | VXUS 16 + AVDV 10 + IDMO 5 + AVES 5 |
| Managed futures (trend) | 25.0 | 25.0 | RSST 25 × 1.00 |
| **Gross** | **126.3** | **126.8** | 1.263× / 1.268× |

Equity notional is 101.3% (101.8% on the shelf's leg). Bonds: zero. That is a position, not an oversight, and the
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
| Gross notional | 1.263× (1.268× on the shelf's 1.072 leg) | 1.315× (1.322×) |
| US equity notional | 65.3% (65.8%) | 65.5% (66.2%) |
| Trend notional | 25% | 30% |
| Weighted gross fee | 33.4 bp | 38.2 bp |
| Weighted net cost | 31.3 bp | 36.2 bp |

The five points come out of VTI. Because RSST carries about one dollar of US equity per
dollar, US equity notional barely moves and the whole change is +5 points of trend.

**Growth.** Experiment 016f ran the matched pair
([run `36f14b39…`](../../research/artifacts/36f14b395e53407f8fdfaee3b4e8e37a/summary.md)):
the 30% arm beats the 25% arm by **+0.51 pp/yr [+0.30, +0.72] against a 0.31 floor**, the
only whole-portfolio comparison in the programme that clears its own resolution. It is a
*leverage* result at the panel's realised premium: the pair's break-even trend haircut is
10.08 pp/yr, and at the 4.07 forward premium the same pair reads about +0.18 against its 0.30
floor. The same run settles what 016e could not: its −0.50 between the 25% arm and the
investor's original eight funds was **all wrapper weight**, since the two fund lists at the
same 30% differ by +0.01 [−0.18, +0.19] against a 0.26 floor.

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
   floor**, and since 016f it isolates the weight. Nearly everything else here is
   unresolved. Discarding the one resolved measurement in favour of four routes that
   disagree with each other is choosing the weaker evidence — with the caveat that the
   measurement resolves only at the realised premium.
2. **A contribution stream is what carries a position through a drought.** The abandonment
   model's trigger is a relative drawdown, and the mechanism that defeats it is new money
   arriving at a low price. This investor contributes 5–15%/yr, and §3.8 shows how much of
   it reaches a shelter, which is the only place new money can buy the wrapper without a
   tax cost: all of it through an active employer plan and the Roth, by swap inside the
   shelter, and a quarter of it when the tax-deferred third receives nothing new.
3. **Zero is the worse extreme.** Over the panel's one flat-to-negative equity decade
   (1999-03…2009-02, equity −2.55%/yr) a 30% overlay contributed about **+9.5 pp/yr above
   its own complement** and turned that decade from −2.55%/yr to about +0.05%/yr, against
   +0.21 pp/yr in ordinary decades.

**Choose 25% instead if you would sell it.** A portfolio held beats a better one abandoned,
and the honest test is whether a decade of the sleeve contributing nothing while equities
rise would end with you selling. If the answer is maybe, take 25% — every route admits it,
and the growth you give up is half a point a year against a 6.0% tracking error you would
never be able to attribute anyway.

**The resampled drawdown cliff is not a reason.** The probability that the overlay is the
deeper drawdown is 6.9% at 30% of notional and steps from 10.8% to 18.8% between 0.58 and
0.59 of notional. [The notional budget](leverage-and-the-notional-budget.md#3a-the-resampled-drawdown-cliff-located-and-explained)
§3a shows the step vanishes without the 60 bp financing spread, is an episode switch between
2007-09 and 1937-38 inside one panel, and lists it under what does not bind. What caps the
weight is the holdability routes above, each of which lands below 30, not a cliff.

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

**The wrapper's weight depends on which shelter holds it, once the unit is after tax.**
After-tax wealth at equal nominal thirds and a 24% withdrawal rate is
`33.3 + 33.3 × 0.76 + 33.4` = 92.0 points. RSST 30 in the traditional is `30 × 0.76 / 92.0`
= **24.8%** of after-tax wealth; the same 30 in the Roth, where f = 0 forces it (§3.6), is
`30 / 92.0` = **32.6%**. That 7.8-point gap is wider than the five points §2 argues over.
Every decision on this page is made in nominal units: §2's weight, §3.7's headroom, §3.8's
flows and §7's rules. Nominal is the right unit for holdability, because the statement the
investor reads and the drawdown that would make them sell are nominal. After tax is the
right unit for growth, which is the unit the Roth-versus-traditional line above is priced
in, and in that unit moving the wrapper between shelters moves its weight more than the
25-versus-30 choice does.

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
headroom, and the constrained direction is selling US equity to buy international. That
rotation needs roughly two points of the portfolio a year. Contributions cover it only where
they land in a shelter: about 2.5 points a year through the Roth cap when the tax-deferred
third receives nothing new, 5 to 11 through an active employer plan at 5–15%/yr (§3.8).

The clean fix is to leave one or two points of headroom on VTI — hold 18 in taxable and 1 in
the Roth at a 30% wrapper, or 23 and 1 at 25%. The repository's joint solution costs **0.28 bp/yr** for a 1 pp headroom band. A
forced taxable sale costs hundreds of times a spread.

### 3.8 Where new money lands, and what the contribution rules can execute

The plan in §3.4 is a snapshot. Two rules on this page spend new money, §7's 60/40 move and
the rotation in §3.7, and neither said which account the money reaches, though the account
decides which funds it can buy. Stated at an illustrative **$300,000 in equal thirds** with
**10%/yr** of contributions, growth ignored; the formulas take any balance.

Write `B` for the balance, `c` for the contribution rate and `C = cB`. 2026 limits from the
tax page (`structural-and-tax-edges.md` §8.6): IRA **$7,500**, §402(g) deferral **$24,500**.

- Roth: `R = min(C, 7,500)`. At the 18.8% and 23.8% columns the direct contribution is phased
  out ($242,000 to $252,000 of modified AGI filing jointly), so the $7,500 arrives as a
  designated-Roth deferral or a conversion; beside a rollover IRA a backdoor contribution is
  mostly a taxable conversion under the pro-rata rule.
- Employer plan: `E = min(C − R, 24,500)` while a plan is receiving deferrals; **0** when the
  tax-deferred third is a rollover IRA and nothing else, because an IRA takes no more than
  the $7,500 already counted. A solo 401(k) or SEP is the one open-menu plan.
- Taxable: `X = C − R − E`.

| The year's $30,000 | Active employer plan | Rollover IRA only |
| --- | ---: | ---: |
| Roth, any of the seven funds | $7,500 (2.5 points) | $7,500 (2.5 points) |
| Employer plan, VTI or VXUS only (§3.6 menu) | $22,500 (7.5 points) | $0 |
| Taxable, VTV and VTI under §3.4, anything else at the §3.2 cost | $0 | $22,500 (7.5 points) |

At 5%/yr the plan takes $7,500 and taxable $0 or $7,500; at 15%/yr the plan takes its $24,500
cap and $13,000 spills to taxable either way.

**"Direct all new money to AVDV and VXUS until 60/40" is executable in one column and not the
other.** AVDV can be bought with new money only in the Roth, at $7,500 a year; no employer
menu carries it. VXUS can be bought in the Roth or the plan. With an active plan the whole
$30,000 can go ex-US inside shelter (Roth to VXUS, plan to its ex-US fund), the 7.7 points
§7 needs arrive in `7.7 / 10` = 0.77 years, and the placement cost is zero. Without a plan,
$22,500 of the $30,000 lands in taxable, where the rule means buying AVDV at **65.45 bp/yr
per dollar** or VXUS at **64.91** at 23.8% (§3.2), the whole shelter saving forgone; net of
the VTI dollar a taxable dollar otherwise holds, 40.06 and 39.52.

That cost is not the rule's, because at f = 1 the taxable account outgrows its US lines in
the first year. Taxable holds VTV 15 + VTI 19 = 34 points and receives 75% of new money:
after one year it is $122,500 against a 34-point allowance of `0.34 × 330,000` = $112,200,
so $10,300 (3.1 points) must hold something else, and the queue says VXUS, the cheapest
international line in taxable at 23.8% and tied with AVDV at 18.8%. In both columns the
wrapper's own top-up, `0.3 × C` = $9,000 a year, exceeds the Roth's $7,500, and the Roth is
the only account new wrapper money can reach: no employer menu carries it and a rollover
IRA receives nothing. Above `cB` = $25,000 a year the 30% target therefore evicts about half
a point of a sheltered tilt to taxable every year, VTV's 0.7 first and then VXUS, at about
0.3 bp/yr per year cumulatively. The §3.4 plan decays under contributions whatever the
rules say; an active plan slows the decay from 3.1 points a year to half a point.

**The executable rule.** Every new sheltered dollar goes to VXUS, in the plan's ex-US fund or
the Roth, until the equity notional reads 60/40; taxable dollars go to VTI and VTV up to
their targets and to VXUS after that; AVDV is bought only to hold it at 10. With an active
plan the split reads 60/40 in about a year at no placement cost. Without one it reads 37.6%
ex-US after a year and 39.9% after two, and the taxable VXUS it uses is the overflow the
account holds anyway, so the move costs nothing the account structure was not already
paying.

**Where AVDV ends up.** "AVDV first" with all 7.7 points into AVDV takes it to
`(10 + 7.7) / 107.7` = **16.4%** of the enlarged book; with only the Roth's $7,500 a year
into AVDV and the plan's money into VXUS, 11.1%. The +0.28 pp/yr [+0.05, +0.56] was measured
at 10 and nowhere else (§1), AVDV's 30.03 bp net cost is the highest of the tilts, and no
run has scored it at 16. The rule keeps it at 10: the Roth's first `0.10 × C` = $3,000 a year
tops AVDV up and the rest goes to VXUS. Under the VXUS-only move AVDV would drift to 9.3% by
dilution, which is what the top-up restores.

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

### Fidelity's $100 per ETF purchase — resolved

Fidelity charges **5% of trade value, capped at $100**, on purchases of ETFs from issuers
that do not pay it a platform fee, on cohorts dated 2025-11-03 and 2026-06-01. On a $10,000
purchase that is 100 bp on day one — larger than the annual expense ratio of every fund here
except the wrapper. The exposure is structurally asymmetric: a boutique such as Tidal, which
issues RSST, is exactly the profile at risk.

**Resolved `as of 2026-09-01`.** Fidelity's list "ETFs Subject to Service Fee, as of August
15, 2026" (84 tickers in the PDF; press counts run to about 108) names none of
Tidal/Return Stacked, Simplify, Pacer, J.P. Morgan, Invesco, Avantis or Dimensional, and no
ticker in this construction. The list is "subject to change without notice", so re-check
before a first purchase. **Schwab** has announced a comparable programme for late 2026 to Q1
2027 and published no list. Two operating rules survive: a per-trade fee is fatal to monthly
contributions and survivable annually ($100 twelve times a year on a $200,000 portfolio is
60 bp/yr; once a year is 5 bp), so if a line is ever listed, buy it once or twice a year and
direct monthly contributions at the index funds; and one wrapper line rather than a separate
managed-futures fund means one exposed purchase rather than two.

One more thing that is *not* a change yet. **RSIT** — Return Stacked International Stocks &
Managed Futures, inception 2026-05-06, 0.98%, $73.39m and a 0.14% spread at 2026-08-31 — is
the international twin of RSST, with a base leg near 1.00 and δ ≈ 0.00. It lands exactly
where this construction is thin. Its first N-PORT (period 2026-07-31) is not yet filed and it
has no measurable loading, so nothing can be promoted from it. Revisit at 24 filed months.

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

### The fallback, the week the wrapper is closed

RSST is $504.95m of net assets at 2026-08-20 and the issuer's shelf is eight funds, five of
five clean cases trailing their own benchmark since inception
(`live-stacked-fund-records.md` §1); the unit of closure risk is the issuer and trust, not
the fund. A liquidation or mandate-change notice is a review trigger, and this is what the
week looks like.

- **Sell** RSST 30 before the last trading day, or take the liquidation at NAV; the 9 bp
  spread is the whole execution cost. **Buy** VTI with the proceeds in the same account. Both
  placements hold the wrapper in a shelter, the traditional at f = 1 (§3.4) and the Roth at
  f = 0 (§3.6), so the **tax cost is zero** either way: nothing inside an IRA is a
  realisation event. That is an unstated benefit of sheltering the wrapper and a reason not
  to move it.
- **The fallback vector: RSST 0 / VTI 49 / VTV 15 / VXUS 16 / AVDV 10 / IDMO 5 / AVES 5**,
  the six holdings of the site's portfolio three. Equity notional falls from 101.5% to 100%
  and trend notional from 30 to zero.
- **Exposure cost.** The overlay's expected gap over the cheap index at 30% and the trend
  prior's median is **0.84 pp/yr** (`trend-weight-under-uncertainty.md` §3), so each year
  without a replacement costs about that in expectation; a permanent loss of the sleeve is
  the whole case for the wrapper in §1, and the closure base rate above is the probability
  that multiplies it.
- **Residual placement cost.** The traditional now holds VTI 30 + IDMO 3.3 while VTV 14.3
  sits in taxable, the inverse of the §3.2 order for those two: `(43.08 − 25.39) × 0.143` =
  **2.5 bp/yr** at 23.8%. Undo it with contributions, new taxable money to VTI and new
  sheltered money to VTV, or leave it; a taxable sale of VTV to fix it costs more than it
  saves.
- **Replacements, in review order, and the test each currently fails** (§1, §4): **CTAP**,
  fee waiver lapses 2026-12-04 to about 0.99% all-in, 82.48% of net assets in a bilateral
  swap with one bank, 33 bp spread, portfolio manager left 2026-08-07; **MATE**, δ −0.159
  keeps the funding gap but no measured loading, one N-CSRS to 2026-02-28 and no
  tax-character table; **JPFP**, $32.75m, no Form N-PORT filed with the first due
  2026-09-29, cash creations that forfeit the in-kind shield; **RSIT**, $73.39m at
  2026-08-31, inception 2026-05-06, no N-PORT, δ read from a marketing page, and an
  international base leg that would move the US/ex-US split by 30 points; **a standalone
  managed-futures fund such as DBMF bought by selling equity**, which fails the funding
  rule in §1, since δ = 1 keeps none of the +2.44 pp/yr and a substitution adds its edge as
  an average rather than a sum. The first of the four wrappers to clear its test is bought
  in the same account with the fallback's VTI, again at no tax cost.

---

## 6. What would change this

Ordered by how much it moves the answer.

1. **Your own numbers.** Your maximum tolerable drawdown, which is the single most valuable
   missing input in this repository and is not a research task: it sets the wrapper under
   the widened drawdown assumption and decides the conditional TIPS leg in §7. The rollover
   share `f` of the tax-deferred third, which moves the booked placement line from −2.0 to
   +6.7 bp/yr and decides whether AVDV can be sheltered at all. Your bracket.
2. **The equity-versus-bond split**, which this construction sets at 100% equity by omission
   and which is worth more than every tilt combined. §7 states the one conditional rule the
   evidence supports and its placement cost.
3. **RSST's 2026-07-31 Form N-PORT, due by 2026-09-29**, which refreshes the trend loading
   from 31 to 34 filed months; then 48 months around 2027-09.
4. **A liquidation or mandate-change notice from RSST's issuer or trust**, which fires the
   fallback in §5 the week it lands.
5. **JPFP's first N-PORT, due by 2026-09-29.** It has filed none; its structure (direct
   futures plus direct stocks, no ETF or swap, 59 bp) is an assumption until then.
6. **The fund-level financing spread**, which decides the sign of the overlay's contribution.
7. **RSST's next December distribution**, which resolves the recognised-versus-distributed
   reading behind the placement's conditional line.
8. **CTAP's waiver on 2026-12-04**, and its spread and counterparty concentration after it.
9. **RSIT at 24 filed months**, if the international sleeve is ever to be financed too.
10. **Your broker's service-fee list**, re-read before a first purchase; resolved clear at
    Fidelity as of 2026-08-15 (§4), unpublished at Schwab.

---

## 7. Valuation, September 2026

`as of 2026-08-31`: CAPE 41.7, 10-year TIPS real yield 2.44% (96.7th percentile since 2003),
30-year 2.99% (99.8th since 2010), TIPS-based excess CAPE yield −0.01 pp, the 0th percentile
of its record for a fifth month. The derivation is in
[valuation and the allocation](valuation-and-the-allocation.md) and the standing position in
[the recommendation](portfolio-recommendation.md); nothing here is a forecast, and no
external capital-market assumption is sized on
([decision 0012](../decisions/0012-valuation-enters-through-the-drawdown-assumption.md)).
Three things follow for this investor.

**The conditional TIPS rule, which is a 10-point Experiment 018 arm and not the ladder's
row.** At a stated tolerable drawdown of **−50% or tighter**, hold **10 points of long TIPS,
unlevered, in the traditional account**, funded from VTI and VXUS pro rata, and set the
wrapper to the notional ladder's figure (19.1% at −50%), with the 10.9 points that frees
going to VTI as in §2. At **−60% or looser, hold none.** The default for a contributing,
leverage-accepting investor is none. The rule is conditional because the drawdown
constraint is the only route through which a valuation reading enters the construction.
The 10-point size is what Experiment 018 froze and priced, at −0.55 to −0.77 pp/yr of mean
for about 4 pp of 1929- and 2008-scale drawdown, earned on a 6–7 pp realised premium, and
at today's 0–1.5 pp equity premium over TIPS the expected cost is 0–0.2 pp/yr; it does not
fall out of any tolerance. A 30-year TIPS at 2.99% real is the best contractual real line
in the record. Both versions worked through, at the 1.050 leg:

| | (a) the rule as written | (b) the ladder's −50% row |
| --- | --- | --- |
| Vector | RSST 19.1 / VTI 24.5 / VTV 15 / VXUS 11.4 / AVDV 10 / IDMO 5 / AVES 5 / TIPS 10 | RSST 19.1 / VTI 12.2 / VTV 9.7 / VXUS 10.3 / AVDV 6.4 / IDMO 3.2 / AVES 3.2 / TIPS 35.9 |
| Equity notional | `19.1 × 1.05 + 70.9` = **91.0%** | **65.1%** |
| Trend notional | 19.1 | 19.1 |
| Defensive | 10 | 35.9 |
| Gross | 1.20 | 1.20 |
| Placement, 23.8% | traditional TIPS 10 + RSST 19.1 + IDMO 4.2; Roth IDMO 0.8, AVES 5, AVDV 10, VXUS 11.4, VTV 6.2; taxable VTV 8.8, VTI 24.5. Nothing evicted; cost zero. | traditional RSST 19.1 + TIPS 14.2; Roth TIPS 21.7, IDMO 3.2, AVES 3.2, AVDV 5.3; taxable AVDV 1.1, VXUS 10.3, VTV 9.7, VTI 12.2. Cost about **7 bp/yr**. |

The ladder's −50% row (`leverage-and-the-notional-budget.md` §3.2) is base notional 0.651
with trend 0.191. The 19.1% wrapper figure is that row's trend column, and (a) keeps the
trend column while discarding the equity column: it delivers 0.91 of equity, not 0.651. (b)
is what the row supports, and its defensive size is arithmetic: the wrapper's `19.1 × 1.05`
= 20.1 points of equity leave 45.0 points of unlevered equity to reach 65.1, so
`100 − 19.1 − 45.0` = **35.9 points of TIPS**, and every unlevered line scales by
`45.0 / 70` = 0.643 because the ladder scales the equity book whole. TIPS in a taxable
account are ordinary income on the coupon and on the inflation accrual, which is taxed the
year it accrues and paid at maturity (phantom income): at the 30-year's 2.99% real that is
`2.99 × 0.408` = 122 bp/yr per dollar at zero inflation plus 40.8 bp per point of inflation,
218 bp at the 2.35% ten-year breakeven on the regime page, ahead of every international
line in the §3.2 queue at any inflation rate and ahead of IDMO above 0.6%. So (b)'s 35.9
points take shelter before the international lines: 14.2 fit beside the wrapper in the
traditional third and 21.7 spill into the Roth, which evicts VXUS 10.3 and AVDV 1.1 to
taxable at 64.91 and 65.45 bp per dollar, `10.3 × 64.91 + 1.1 × 65.45` = **7.4 bp/yr**,
about the whole booked placement edge of §3.5. Putting the 21.7 in taxable instead would
cost 13.9 bp/yr at zero inflation before the phantom income, so the eviction is the cheaper
route. Which version an investor takes is their tolerance, which nobody has supplied (§6);
what this page no longer says is that (a) is the ladder's consequence.

**The 60/40 move, by contributions only.** The book is 64.5% US / 35.5% ex-US in equity
notional (65.5 of 101.5 at the 1.050 leg). Reaching 60/40 without a sale needs
`(0.4 × 101.5 − 36) / 0.6` = **7.7 points** of new ex-US capital, all of it VXUS: the
developed-ex-US discount sits in the value half rather than in Japan, Korea or Taiwan, but
AVDV's evidence is at 10 and it stays there (§3.8). The expected value of the move is about
7 bp/yr against 40–72 bp of tracking error, which is why it is worth doing with sheltered
money and not with taxed money. §3.8 gives the executable version: about a year through an
active employer plan at 10%/yr at no placement cost, about two years without one, riding the
taxable VXUS the account has to hold anyway. 50/50 is unsupported.

**An investor who takes the 10-point leg and keeps the wrapper at 30%** pays for it: 10
points of RSST move from the traditional into the Roth, and 4.7 points of VXUS (pro rata
funding) or 9.3 (VTI-only funding) go to taxable at 64.91 bp per dollar at the 23.8%
bracket, plus VTV's last 0.7 points, about **3 to 6 bp/yr, roughly the whole booked
placement edge of +2 to +7 bp/yr** in §3.5. Moving the wrapper to the Roth also shifts its
dispersion onto the investor's side of the partnership, which §3.4 prices as a forecast, and
raises its after-tax weight from 24.8% to 32.6%. State the cost; do not hide it.

**The decision for this investor, made rather than deferred** (`as of 2026-09-02`). Two facts
are on record: the investor has said the August 2026 valuation must count, and has not stated
a tolerable drawdown. Under those two facts the working default is the vector the
excess-CAPE-yield rule produces when applied to the traditional third
([valuation](valuation-and-the-allocation.md) §3.3, Experiment 022):

| | Vector | Where the defensive line sits |
| --- | --- | --- |
| Working default | **RSST 25 / VTI 19 / VTV 15 / VXUS 16 / AVDV 10 / IDMO 5 / AVES 5 / ten-year TIPS 5** | traditional: RSST 25 + TIPS 5 + IDMO 3.3; Roth and taxable as in §3.4; no taxable line moves |
| Published construction | RSST 30 / VTI 19 / VTV 15 / VXUS 16 / AVDV 10 / IDMO 5 / AVES 5 | for a stated tolerance of −70% or looser |
| Rule (a) above | RSST 19.1 / TIPS 10, wrapper funds VTI | for a stated tolerance of −50% or tighter |

Why this one. It is the 25% arm every route admits after the §6a correction. It sits between
the ladder's −50% and −60% rows (19.1 and 23.7), which is where an investor who names the
valuation concern and accepts leverage plausibly sits. Against 100% equity it costs about 14
bp/yr of log growth if the forward equity premium over bonds is 3 pp and gains 31 if it is
zero, with break-even near 2 pp, and six managers' 2026 ten-year expectations put that premium
between −2.2 and +1.5 pp over TIPS. Against the 30% vector it gives up about 0.18 pp/yr at the
forward trend premium, inside a 0.30 floor. Gross notional falls from 1.32 to 1.27. The three
vectors are within resolution of each other on every measurement this repository holds; what
separates them is the drawdown the investor can hold, and this paragraph is the assumption
made in the absence of that number. A stated tolerance replaces it the day it is supplied.

### The working default, scored as one object

`as of 2026-09-02`. **`exploratory`.**
[Experiment 024](../../research/experiments/exp_024_working_default.yaml), spec
`d1ef4950…`, run
[`5f3c2db9…`](../../research/artifacts/5f3c2db962fe420881d3aaba3e44df55/summary.md), tables
in [`tables.md`](../../research/artifacts/5f3c2db962fe420881d3aaba3e44df55/tables.md). The
working default, a 25% RSST-like wrapper, 70 points of equity core and a 5-point unlevered
ten-year line, against the published 30% wrapper and 70 points of core, as one object on
[Experiment 018](defensive-engines-in-the-construction.md)'s 1929-01…2025-05 panel and
machinery, and the same pair on 016f's 427-month fund-list panel with the line added. The
TIPS line is a modelled nominal ten-year Treasury, because no TIPS series exists before 2003;
reading it as TIPS is wrong in 1977…81 in the direction that overstates the line's loss
there. Predicted `rejected` before the run at about −0.6 pp/yr against a floor near 0.35, a
leverage result at realised premia; every prediction held, 018's trend scalar 1.9771 and
016f's +0.5101 wrapper pair both reproduced exactly.

**Conclusion.** At the panel's realised premia the working default costs **0.64 pp/yr of
arithmetic mean and 0.44 of log growth** against the published vector, on every start date
from 1929, 1934, 1946, 1970 and 1990-11 and on both panels; it buys **1.8 pp of maximum
drawdown and one point of volatility**. The wrapper cut is the whole of it and the bond line
sits at its own floor. At forward premia the cost is inside a third of a point and its sign
depends on the equity premium over bonds. Nothing in the result argues against the working
default for the reason it was chosen, which is the drawdown; the paragraph above stands, with
a measured number in place of the interpolated 0.18.

| Pair, primary metric arithmetic gap | Panel | Gap, pp/yr | 95% bootstrap; HAC | Floor | Log gap | Status |
| --- | --- | ---: | :---: | ---: | ---: | --- |
| **working default − published** | 1929-01…2025-05, 1,157 months | **−0.64** | [−0.86, −0.41]; [−0.87, −0.40] | 0.33 | −0.44 | `rejected` |
| working default − published | 1990-11…2026-05, 427 months, 016f's funds | −0.87 | [−1.20, −0.52]; [−1.19, −0.54] | 0.46 | −0.74 | `rejected` |
| wrapper cut alone: 25 wrapper + 5 cash − published | 1929– | −0.72 | [−0.94, −0.49]; [−0.95, −0.49] | 0.32 | −0.52 | `rejected` |
| bond line alone: ten-year − cash, derived from the two arms above | 1929– | +0.08 | HAC [+0.01, +0.15] | 0.08 | +0.07 | check, not registered |
| long Treasury in the line − published | 1929– | −0.61 | [−0.83, −0.38]; [−0.84, −0.37] | 0.33 | −0.41 | `rejected` |
| 016f's pair on 96 years: 25 wrapper + 75 core − published | 1929– | −0.33 | [−0.45, −0.21]; [−0.46, −0.20] | 0.18 | −0.30 | `rejected` |

The pair reads −0.61 to −0.71 on every declared sub-window with every interval excluding
zero, −0.52 inside the 1981-10…2020-07 bond bull market and −0.70 outside it. The bond
line's +0.08 is +0.24 inside the bull market, 0.00 before it and −0.33 on the 58 months
since 2020-08, the same one-era shape 018 found for the stacked leg. Against the cheap 100%
equity index the working default is +1.34 [+0.71, +1.99] against a 0.91 floor where the
published vector is +1.98; against the 85/15 constant mix Experiment 022 uses, +2.27
[+1.56, +2.98] against 1.05.

**Drawdown and crises**, descriptive, one history. Maximum drawdown **−81.0% against
−82.78%**; months under water 163 against 164 (the long-Treasury variant, 89); volatility
17.97% against 18.99%; worst-decile-of-equity-months offset +0.44 pp/month at a 92% hit rate.
Cumulative offset against the published vector: 1929 +1.8 pp, 1937 +2.2, dotcom +2.0, GFC
+1.8, covid +1.1, 1973 −0.1, **1977…81 −9.2**, of which −5.0 is the wrapper cut and −4.2 the
nominal bond, 2022 +0.3. **Flat decade 1999-03…2009-02: −0.08 [−0.73, +0.56] against a 0.84
floor**; against the cheap index +2.75 where the published vector reads +2.84. The default
keeps the decade the wrapper exists for.

**Regret at forward premia.** Arithmetic on the paired difference, no simulation: five
points of wrapper forgo `1.072 × equity excess + trend − 1.195` and the line earns the bond's
excess over cash less 5 bp, at the 0.8 pp term premium the
[market scan](market-scan-2026.md) records; the log cell adds the realised variance-drag
constant, +0.19 pp/yr. Cells are working default minus published, pp/yr, arithmetic / log;
positive means the default wins.

| Gross trend premium, pp/yr ([trend weight](trend-weight-under-uncertainty.md) §1) | Equity over bonds 0 | 1.5 | 3 | 5 |
| --- | ---: | ---: | ---: | ---: |
| 0.00, premium gone | +0.05 / +0.24 | −0.03 / +0.16 | −0.11 / +0.08 | −0.21 / −0.03 |
| 1.74, vendor's last 78 months | −0.03 / +0.16 | −0.11 / +0.07 | −0.19 / −0.01 | −0.30 / −0.11 |
| 3.90, vendor post-publication | −0.14 / +0.05 | −0.22 / −0.03 | −0.30 / −0.11 | −0.41 / −0.22 |
| **4.07, the corrected central figure** | **−0.15 / +0.04** | **−0.23 / −0.04** | **−0.31 / −0.12** | **−0.42 / −0.23** |
| 5.32, JST book | −0.21 / −0.02 | −0.29 / −0.10 | −0.37 / −0.18 | −0.48 / −0.29 |
| 7.18, own 4-asset book | −0.30 / −0.12 | −0.39 / −0.20 | −0.47 / −0.28 | −0.57 / −0.38 |
| 10.98, 1990…2026 realised | −0.49 / −0.31 | −0.57 / −0.39 | −0.66 / −0.47 | −0.76 / −0.57 |

Break-even gross trend premium on log growth, below which the default wins: 4.86 at a zero
equity premium over bonds, 3.25 at 1.5, 1.64 at 3, none at 5. Across the six managers'
−2.2 to +1.5 pp over TIPS the central log cell runs +0.16 to −0.04: the two vectors are
within a tenth of a point of each other on the growth objective, and the choice between
them is the drawdown, as the paragraph above says. The 0.18 quoted there is the wrapper cut
priced on 016f's panel without the line; this is the object itself.

**Verified.** Every gap, interval, floor, sub-window, drawdown, episode and regret figure
above, from run `5f3c2db9…` against a specification hashed before the run and carrying its
predictions; the wrapper's fee charged on 25 rather than 30 points, which is 5.73 bp/yr of
the gap; 018's scalar and 016f's pair reproduced. **Interpretation.** The −0.64 is what five
points of a 7.75 pp/yr equity excess and a 7.22 trend excess cost when swapped for a 1.61
bond excess, and it says nothing about forward premia; the regret table is arithmetic on
assumed premia; the nominal ten-year stands in for TIPS; the bond line's +0.08 is the
1981…2020 era; the variance-drag constant uses realised variances; the derived bond-line row
was computed from two scored arms in a check and is not registered. **Open.** A TIPS series
before 2003, 018's open question 2, without which 1977…81 cannot be read for the line as
held; the default's placement cost, priced above and not inside the experiment; whether a
daily trend programme lands nearer the no-lag or the lagged row of 018 §2's bracket, which
moves both vectors together and the pair by about a tenth.

---

## Verified, derived, assumed

**Verified from the repository.** Every tournament figure, interval, detection floor and
sub-period in §1, §2 and §5, from `final-construction-test.md` and run `cd2fb4b9…`. Every
filed tax characteristic for RSST, VTI, IDMO and AVES, and the 23.8/18.8/15 priorities for
those four, from `structural-and-tax-edges.md` §8 and `src/content/placement.ts`. Net costs
from 50 fiscal years of Form N-CEN. Wrapper structure and δ from Form N-PORT 2026-04-30; the
1.050 equity leg is SPLG 74.09% + S&P 500 e-mini 30.94% from the same filing, and the shelf's
1.072 is recorded beside it until reconciled. Spreads from `.claude/scratch/market-scan-2026.md`;
the Fidelity service-fee list from the issuer PDF as of 2026-08-15; 016f figures from run
`36f14b39…`.

**Derived here, and reproducible from `scratchpad/placement.mjs`.** VTV, VXUS and AVDV
priorities at all three brackets. The f = 1 and f = 0 fill orders for the seven-fund
construction at both wrapper weights. The 34-to-1 wrapper regret ratio. The 0.52
menu-binding fraction. The 9.12 bp menu cost at 30% and 6.00 at 25%. The 7.45 bp of forfeited credit. Weighted net cost of 31.3 bp at a 25% wrapper
and 36.2 bp at 30%. The notional decomposition at both RSST legs (126.3 / 126.8 gross at 25%,
131.5 / 132.2 at 30%). The §7 arithmetic for both TIPS versions, the §3.8 contribution
flows and the years to 60/40, the §5 fallback's 2.5 bp residual, the after-tax wrapper
weights in §3.4, and the 7.7 points of capital the 60/40 move needs.

**Assumed.** VTV, VXUS and AVDV yields are trailing-twelve-month figures from an aggregator
read 2026-08-23, not sponsor filings. VXUS's and AVDV's qualified fractions are blends of
VEA's and VWO's filed figures, not their own. AVDV's withholding rate is VEA's. VTI's, VTV's
and the wrapper's qualified fractions are assumed at 1.00. State income tax is excluded and
additive; it compresses every gap without reordering them. Equal *nominal* thirds are
assumed; after tax they are 37.84 / 28.76 / 33.41.
