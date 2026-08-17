# Capital efficiency and breadth: what the funding rule is worth, and how many engines exist

**Question.** Every marginal-sleeve result in this repository was produced by *selling
something* to fund the sleeve. What changes if the sleeve is financed instead — and how
many genuinely distinct return engines are available to finance?

**Decision it informs.** Whether the zero-leverage rule in
[decision 0004](../decisions/0004-no-sleeve-promoted.md) is a conservative simplification
or a load-bearing constraint, and what a multi-engine portfolio could contain.

**Out of scope.** Which funds to buy and in what account — that is
[the recommendation](portfolio-recommendation.md). Nothing here promotes a sleeve.

`as of 2026-08-16`.

---

## Conclusion

1. **The funding rule moves the hurdle by `a_p − sigma_p**2`, and that expression contains
   nothing about the sleeve.** It is **+2.44 pp/yr** for a 100%-equity base — larger than
   any premium this repository has attempted to measure. The zero-leverage rule is not a
   free conservatism; it is the reason the marginal-sleeve programme returned nulls.
2. **Leverage on equity alone is not the answer.** The realised growth optimum on 100 years
   of US data is about **2.2×, at a −99.3% maximum drawdown and 296 months under water.**
   The drawdown constraint sets exposure; the growth objective never does.
3. **Breadth is limited by the vehicle shelf, not by markets — and the gap is now
   measured.** Effective breadth of **4.06** is available on paper from trend, BAB,
   short-term reversal and accruals, worth about four times trend alone. **Exactly one of
   those four can be bought**, and three of the seven newly tested families have no
   registered vehicle of any kind. This page previously said "breadth is one engine";
   a red team falsified that framing. At least four engines
   clear the *overlay* bar and fail the *pro-rata* bar — trend, duration-hedged credit,
   long/short commodities and catastrophe bonds — **and gold, added 2026-08-17, makes
   five.** **This page previously said only trend has a financed retail wrapper; that is
   now false.** WisdomTree's GDE stacks roughly a dollar of gold-futures notional on a
   dollar of US equity for **0.20%/yr**, a seventh of trend's assumed fee, on $595m of
   assets since 2022. **Gold is the one candidate whose vehicle shelf does not bind — and
   it fails on return instead, which is a cleaner refusal than any this page has made.**
   §3a. The binding constraint is which strategies happen to have a futures market
   deep enough to build a return-stacked fund on, which is a fact about the fund industry
   rather than about return premia. Separately, the alternative risk premia do fail on
   cost: 0.3–1.0%/yr gross post-2019 at 2–5% volatility against a ~1.5% retail wrapper.
4. **Trend survives on three independent instruments, and no single one of them resolves
   it.** The sign is robust; the magnitude is bracketed; the power is not there.

   | Instrument | Window | Trend Sharpe | ρ to equity | Overlay gap vs leverage-matched |
   | --- | --- | ---: | ---: | ---: |
   | **Built here**, 4 series, none a trend product | 1,091 mo | **+0.52** | −0.07 | **+1.44 pp/yr** |
   | **Live funds**, 46 of them, net of fees, SEC Item B.5 | 78 mo | **+0.33** | −0.11 | **+1.27 pp/yr** |
   | AQR vendor series, gross | 485 mo | +0.96 | −0.08 | +1.14 pp/yr |

   **The vendor series was the reason Experiment 011 said `unresolved`, and it is no
   longer load-bearing.** An independent construction reproduces the correlation to
   within 0.01 and earns roughly half the Sharpe; live funds net of every real fee earn a
   third of it. **All three agree on the sign of every quantity that matters.**
   Its left-tail contribution is positive at every haircut tested, including one that
   turns its median contribution negative — so it is a risk-reduction claim before it is
   a return claim.
5. **Global versus US is unresolved, and the two datasets disagree in opposite
   directions.** In local currency over 150 years, global 60/40 beat US-only on drawdown
   and on return per unit of risk. **In USD over 1990–2025 it lost 1.57 pp/yr and drew down
   deeper.** The case for global equity is not that it raises expected return — on the only
   USD evidence here it does not — but that the US is the survivor and its record cannot be
   bought in advance. **An earlier draft of this page claimed global was the largest certain
   improvement available; building the frontier falsified that and the claim is withdrawn.**
6. **The flat drawdown is real at the recommended weight, and three things about it were
   never stated.** Resampled 4,000 times, the overlay's drawdown is the deeper one in
   **6.9%** of histories at 30% notional — and in **78.7%** at 200%, so §7's `w = 2.00`
   row is a lucky path. The result is measured on a window **starting 1934-07**, from
   which 1929-32 is excluded by the trend leg's burn-in; rebuilt to cover it, the baseline
   drawdown is **−83.65%**, not −50.3%, and the overlay still shallows it monotonically.
   And it is **not** flat inside every crisis: the overlay makes 1987, 2022 and the
   late-1970s **worse**, by 1.4 to 7.7 pp at 1.0× notional. **§9.**
7. **The recommendation breaks on one condition and it is precisely monitorable.** Forcing
   trend's correlation to equity to **+0.30 inside equity drawdowns only** — a full-sample
   correlation of just +0.29 — turns the flat drawdown into a **3.6 pp deeper** one at 30%
   notional and an **11 pp deeper** one at 100%, while barely touching growth. **§5a stresses
   the unconditional correlation and finds the overlay survives to +0.50; the conditional
   correlation is the one that matters and it was never varied.** §5b's boundary adds the
   return condition: at a forward trend excess return of 2.0% the overlay dies at a
   correlation of +0.20 or above, and at 0.0% it is behind at any correlation.
8. **Fund closure is the modal outcome, not a tail.** Thirteen of the twenty-five
   managed-futures funds filing at 2019-07 had stopped by 2025-12 — a **10.7%/yr** hazard,
   giving **43%** over five years and **90%** over twenty. Methodology change cannot be
   estimated at all and the page says so rather than guessing. **§9.4.**
9. **A five-year review cannot see this edge.** Its minimum detectable effect at five
   years is **3.84 pp/yr** against a measured gap of **+1.50**, and a bad five-year review
   is followed by a *positive* next five years. The investor's stated intent to reassess at
   five years is, on this evidence, a plan to sell after bad luck.

---

## 1. The funding rule, derived

From [`studies/overlay_growth.py`](../../research/src/portfolio_edge/studies/overlay_growth.py),
closed-form and pinned by tests that read no market data. Write `a_p`, `sigma_p` for the
base portfolio's arithmetic excess return over cash and its volatility, `a_net` for what a
unit of sleeve notional earns after financing and fee, and `rho` for their correlation.

| Funding rule | What the first sleeve dollar must clear |
| --- | --- |
| **Pro rata** — sell the base. Every experiment here | `a_p − sigma_p**2 (1 − beta)` |
| **Overlay** — sell nothing, finance the notional | `rho sigma_p sigma_d` |
| **Difference** | **`a_p − sigma_p**2 = sigma_p**2 (L_p* − 1)`** |

Every term involving the sleeve cancels. The penalty the zero-leverage rule imposes on
*every* candidate is a property of the base position alone, it is positive exactly when the
base's own growth-optimal leverage exceeds 1, and the two rules agree exactly when the
constraint does not bind.

At `a_p = 5.0%` and `sigma_p = 16%` the gap is **2.44 pp/yr**; for the 60/40 equity/cash
base [Experiment 004](trend-marginal-value.md) used it is **2.08**.

**What this does not explain.** It does not account for the difference between Experiment
004's +1.312 pp/yr and Experiment 010b's +0.258. Checked rather than assumed: the
funding-rule term is **+0.25 pp/yr of a +2.15 pp/yr per-unit-weight difference, about 12%**.
The rest is period, base composition, comparator and realised returns.

**The honest control.** At matched volatility the variance terms cancel and the higher
Sharpe ratio wins outright. An overlay that raises growth over the *unlevered* base while
lowering the portfolio's Sharpe ratio has bought its gain with beta, and must be labelled
that way. Every figure below is reported against a **leverage-matched** control.

---

## 2. Levering equity alone: the growth optimum is unholdable

`levered_ladder` in [`studies/equity_share.py`](../../research/src/portfolio_edge/studies/equity_share.py),
on the Ken French US market series, 1200 months 1926-07…2026-06, financed at the T-bill
with a 60 bp/yr borrow spread. The pipeline reproduces this repository's published figures
at `L = 1.0` on the 1963 window — 10.87% geometric, 15.42% volatility, −50.3%, 72 months —
which is what licenses reading the rest.

| Leverage | geometric | volatility | max drawdown | under water |
| ---: | ---: | ---: | ---: | ---: |
| 1.0 | 10.37% | 18.34% | −83.7% | 184 mo |
| 1.4 | 11.97% | 25.69% | −93.4% | 196 mo |
| 2.0 | 13.15% | 36.71% | −98.6% | 273 mo |
| **2.2** | **13.16%** | 40.39% | **−99.3%** | **296 mo** |
| 3.0 | 10.83% | 55.09% | −100.0% | 416 mo |

**Two readings, and the second matters more.** The growth objective does want leverage, and
the amount is large — worth +2.8 pp/yr over unlevered. And it is unholdable: the optimum
drew down 99.3% and spent **24.7 years** under water. Even 1.2× drew down −89.5%.

Incidental and material: **unlevered US equity's worst drawdown over its full 100-year
record is −83.7%**, not the −50.3% the [equity-share page](setting-the-equity-share.md)
anchors on. That page states its 1963 window; the figure is not even a bound within the
United States.

---

## 3. How many engines are there? One

A multi-asset monthly panel, the first this repository has held: US equity (French), long
Treasury and corporate (Goyal–Welch `ltr`/`corpr`), commodities (AQR CLR), trend (AQR
TSMOM), cash (`Rfree`). Excess of cash, 1985-01…2025-05, n = 485.

| Asset | excess | volatility | Sharpe | corr to equity |
| --- | ---: | ---: | ---: | ---: |
| equity | 9.11% | 15.59% | 0.58 | 1.00 |
| treasury | 4.73% | 10.07% | 0.47 | −0.04 |
| credit | 4.89% | 8.87% | 0.55 | +0.19 |
| commodity | 3.46% | 13.01% | 0.27 | +0.29 |
| **gold** | **3.28%** | **12.22%** | **0.27** | **−0.09** |
| trend | 12.07% | 12.58% | 0.96 | −0.08 |

**Credit and treasury correlate +0.83 — they are one engine, not two.** Counting them
separately is the fake breadth `docs/the-plan.md` forbids.

**The gold row was added on 2026-08-17 and is measured on this section's exact window**,
1985-01…2025-05, 485 months, net of GLDM's published 0.10% fee, from the World Bank Pink
Sheet — with the LBMA month-end fix as a cross-check giving 3.76% / 15.27% / **0.25** /
**−0.04**. **Where the two disagree the less favourable is quoted**, because the Pink Sheet
is a monthly *average* and averaging biases a Sharpe ratio upward. Read it beside
commodities and not beside trend: **the same Sharpe ratio as commodities, at a correlation
of −0.09 instead of +0.29.** Full construction, provenance, licence position and the 1971
handling are in [marginal sleeve value § Gold, tested](marginal-sleeve-value.md#gold-tested);
the two numbers that decide anything are repeated in §3a below.

### The window flatters, and by how much is measurable

| | full 1926-2025 | pre-1985 | 1985-2025 |
| --- | ---: | ---: | ---: |
| Treasury Sharpe | 0.27 | **0.08** | 0.47 |
| equity/treasury correlation | +0.08 | **+0.17** | −0.04 |
| Commodity Sharpe | 0.31 | 0.34 | 0.27 |
| equity/commodity correlation | +0.30 | +0.30 | +0.29 |
| **Gold Sharpe** | *no market price* | **0.39** | **0.27** |
| **equity/gold correlation** | *no market price* | **+0.04** | **−0.09** |

**The bond overlay's entire case is the post-1985 disinflation**, in both its return and its
correlation. Commodities are the stable one, in Sharpe and in correlation alike.

**Gold's two cells are not comparable with the others' and the table says so rather than
lining them up.** There is no market price for gold before 1971-08-15 — the dollar price
was an administered peg and the two devaluations that ended it were acts of Congress — so
its "pre-1985" column is **1971-09…1984-12, 160 months**, not sixty years. It is also the
column that flatters gold most: **the first forty of those months, when private US gold
ownership was still illegal, carry a Sharpe of 1.56 and the remaining 120 carry 0.007.**
The 1985-2025 cell is the one to read, and there gold looks like commodities on return and
much better on correlation. LBMA cross-check: 0.39 / +0.10 and 0.25 / −0.04.

**Correction, 2026-08-16.** An earlier version of this page said commodities' stable +0.30
correlation "disqualifies them once cost is charged". **That was wrong, and the error was
comparing their Sharpe ratio against the correlation instead of against the threshold.**
Equation (4)'s bar is `L rho sigma_p`, which at `L = 1.5` is `1.5 × 0.286 × 0.1559 =
0.067`, not 0.286. Commodities' net Sharpe is **0.174 even at a 1.2% fee**, so they clear
it by +0.107 and **pass at every exposure and fee tested**. What is true is weaker and
different: their margin is roughly **five times smaller than trend's**, and the AQR series
is excess-of-cash with **unpriced roll costs**, which is what would actually sink them.
They are not rejected here; they are dominated.

### 3a. Gold: it passes admission, it is dominated on return, and its shelf does not bind

Two facts belong here rather than only on the marginal-sleeve page, because this section's
argument is about *engines* and *vehicles* and gold changes both.

**It passes equation (4) at every exposure, and the margin is not carried by the cost
assumption.** On the longest defensible window, 1971-09…2026-06, 658 months:

| | net Sharpe | `rho` | threshold at `L = 1` | margin |
| --- | ---: | ---: | ---: | ---: |
| gold, 1971-09…end | 0.313 / 0.298 | −0.031 / +0.019 | −0.0050 / +0.0030 | +0.318 / **+0.295** |
| **gold, 1975-01…end** — the only window a US person could legally hold it | 0.187 / **0.181** | −0.024 / +0.034 | −0.0038 / +0.0052 | +0.191 / **+0.176** |

**Forty months in which private US gold ownership was illegal carry about 40% of the
full-sample Sharpe ratio** — gold earned 54.5%/yr over 1971-09…1974-12 while equity lost
9.8%/yr. **Use the second row.** Equation (4)'s documented misuse does not apply here:
`|rho|` is under 0.04, far inside the `|rho| <= 0.5` range where the first-order condition
is a usable test.

**Its crisis-conditional correlation is the one number that clears §7's own falsifier.**
Conclusion 7 above makes the recommendation conditional on trend's correlation to equity
*inside equity drawdowns* staying below **+0.20**, and §9.3 shows what +0.30 costs.
Measured on the identical definition — equity at least 10% below its running peak, 294 of
658 months — **gold's crisis correlation is −0.011 / +0.072, and +0.084 on the holdable
window.** Its mean return inside those months is **+0.85 to +0.95%/month** against equity's
−0.26%. **On the axis this page identifies as the top-ranked threat to its own
recommendation, gold is measurably safer than the sleeve the recommendation names.**

**And gold is the counter-example to this section's structural claim.** §3 concludes that
"the fund shelf binds before the evidence does": three of the seven factor families have no
vehicle of any kind and the one BAB fund is $362m. **For gold it does not bind, in either
direction.**

| Route | Vehicle | Fee | Size / inception | Funding rule |
| --- | --- | ---: | --- | --- |
| Physical | GLD / IAU / GLDM / SGOL | 0.40 / 0.25 / **0.10** / 0.17% | decades old, tens of $bn | **pro rata** — GLD's 10-K: *"The Trust does not hold or employ any derivative securities"* |
| **Stacked on equity** | **WisdomTree GDE** | **0.20%** | **$595.1m**, inception 2022-03-17 | **overlay** — *"approximately equal exposure to U.S.-listed gold futures contracts and U.S. equity securities"*; its 2026-05-31 N-PORT measures 85.7% equity + 88.1% gold notional |
| Stacked on stocks and bonds | First Trust ESBG | 0.95% | **$2.2m**, inception 2025-11-18 | overlay, ~210% notional in three sleeves. A sub-$3m fund; treat closure as likely |
| Stacked, gold + bitcoin | Return Stacked RSSX | 0.67% | $66.3m, inception 2025-05-29 | overlay, but the stacked dollar is a **risk-parity blend of gold and bitcoin** and cannot be dialled to pure gold |

All figures retrieved 2026-08-17 from the funds' own SEC filings. **GDE is the second
financed retail wrapper this repository has found for any candidate engine, after trend —
and at 0.20% it is a seventh of trend's assumed 1.45% fee.** With this page's own ≤40 bp
gold-futures financing bound from [structural and tax-aware
edges](structural-and-tax-edges.md), the all-in overlay cost is about **0.60%/yr against
trend's 2.05%.**

**None of that promotes gold, and the reason is on the return side, not the vehicle side.**
Under pro-rata funding — the rule a physical gold ETF actually imposes — gold's marginal
growth at a 10% weight is **+0.007 to +0.043 pp/yr** on the headline window and **−0.41 to
−0.42** on the holdable one, against a 0.30 pp/yr bar and an MDE₈₀ of about 1.0. It is
**dominated exactly as commodities are** — same Sharpe, better correlation, no measurable
edge — and it joins trend, duration-hedged credit, long/short commodities and catastrophe
bonds in the set that clears the overlay bar and fails the pro-rata one.

**One thing gold changes that commodities do not.** The AQR commodity series is
excess-of-cash with **unpriced roll costs**, which is what §3 says would actually sink it.
Gold has no roll cost in the physical wrapper, its carry is a published fee, and its total
return is *exactly* price return minus that fee because bullion pays no distribution and
has no corporate action. **It is the one candidate here whose cost side is measured rather
than assumed** — and it still does not clear the bar that matters.

**The tax side is worse than equity's and decides placement.** A bullion ETF is taxed as a
collectible: **28% plus 3.8% NIIT** against 20% plus 3.8% for equity, verified from IRS
Pub. 550 and from GLD's, IAU's, GLDM's and SGOL's own 10-Ks, each of which states it
directly. Inside an IRA the collectibles rate does not apply — both GLD and IAU hold IRS
private letter rulings to that effect — but traditional-IRA distributions are ordinary
income, so the shelter helps and does not make gold tax-favoured. **The physical route
competes with trend for the same scarce shelter that §7 already identifies as the binding
constraint on the overlay weight.**

### The seven families this repository had never opened

`docs/the-plan.md` §A lists about eighteen equity factor families. Five had been tested
(HML, RMW, CMA, UMD, SMB), and [decision 0005](../decisions/0005-factor-premia-closed-on-public-data.md)
closed factor work "on public data" on the strength of those five. **That was
over-general, and the remaining families are now measured on the same free library.**

**Premia, gross, pp/yr, with each window's own measured detection floor beside it:**

| Family | Full sample | 95% CI | MDE₈₀ | **Post-publication** | 95% CI | **MDE₈₀** |
| --- | ---: | --- | ---: | ---: | --- | ---: |
| **BAB** | **+7.77** | [5.05, 10.48] | 3.45 | +3.70 | [−0.92, 8.31] | **5.86** |
| Short-term reversal | **+7.46** | [4.93, 9.98] | 3.20 | +1.71 | [−1.75, 5.17] | **4.39** |
| Buybacks | **+6.63** | [3.53, 9.73] | 3.93 | +3.88 | [−2.02, 9.79] | **7.49** |
| Net issuance | +4.50 | [1.14, 7.85] | 4.26 | +3.37 | [−3.73, 10.5] | **9.00** |
| QMJ | +3.75 | [1.62, 5.89] | 2.71 | **−1.78** | [−11.6, 8.1] | **12.50** |
| Accruals | +3.53 | [1.02, 6.05] | 3.19 | +1.94 | [−2.29, 6.16] | **5.36** |
| Long-term reversal | +3.44 | [0.65, 6.23] | 3.54 | +1.62 | [−1.76, 5.00] | **4.29** |
| Low-beta decile, unlevered | −2.18 | [−8.45, 4.09] | 7.96 | −1.74 | [−8.57, 5.09] | 8.66 |

**Six of seven survive Holm and Benjamini–Hochberg across the family on the full sample.
Zero of seven survive either post-publication** — and **every post-publication estimate
sits below its own detection floor**, by 1.6× (BAB) to 7× (QMJ). These are unresolved
nulls, not measured zeros, and the distinction is decision 0005's whole lesson.

**And here is the part that matters, because it is the one thing this data can resolve.**
Breadth. Correlations over 497 months: **nothing correlates above +0.18 with trend.**

| Set | k | **Effective breadth `1' R⁻¹ 1`** |
| --- | ---: | ---: |
| trend alone | 1 | **1.00** |
| trend + BAB | 2 | **1.69** |
| trend + BAB + short-term reversal | 3 | **3.18** |
| **trend + BAB + STR + accruals** | 4 | **4.06** |
| trend + all seven | 8 | 6.67 |

**Effective breadth of four is genuinely available**, and by the multiplier in §1 that
would be worth roughly four times the peak gain of trend alone — more than any single
tilt this repository has ever priced.

**It is not available to anyone.** From the SEC N-PORT 2025Q4 census:

| Engine | Registered long/short vehicle |
| --- | --- |
| BAB / low beta | **one** — AGF U.S. Market Neutral Anti-Beta, $362m |
| QMJ, net issuance, buybacks | **none** |
| Short-term reversal, long-term reversal, accruals | **none** |
| Trend | 33 managed-futures and return-stacked series |

A long-only minimum-volatility fund is not BAB: no short leg, no leverage, and a
correlation to equity near one. **Three of the seven have no vehicle of any kind.**

**So the answer to "combine several strategies" is now precise, and it is not a hedge.**
*In principle* the breadth is real — four effectively independent engines, worth about
4× one. *In practice* it is unreachable, because six of the seven cannot be bought and
the seventh is a $362m fund whose post-publication premium sits 1.6× below its own
detection floor, built by a firm that sells the strategy and states no financing cost —
**on a strategy whose entire mechanism is borrowing.**

**This is the third independent confirmation of the same structural fact**, after the
alternative risk premia below and the [§F families](alternative-sleeves-audit.md): **the
fund shelf binds before the evidence does.**

Two side findings that must travel. **QMJ correlates 0.72 with RMW and may never be
counted as a separate engine.** **PEAD is published by neither French nor AQR in any
form** and is recorded as unobtainable rather than tested.

### Alternative risk premia: they pass the correlation test and fail the cost test

Scoped from AQR's *Century of Factor Premia*, four styles × four asset classes, long-short,
gross, 1926-07…2026-02. **Downloaded 2026-08-16 and not yet adaptered or manifested, so
this row is exploratory and may not support a decision.**

| Engine | Sharpe pre-2019 | **Sharpe 2019+** | volatility |
| --- | ---: | ---: | ---: |
| All asset classes Multi-style | 1.48 | **0.33** | 2.3% |
| All Macro Multi-style | 0.90 | **−0.08** | 2.4% |
| All Stock Selection Multi-style | 1.38 | 1.00 | 4.7% |
| Value / Momentum / Carry / Defensive | 0.53–0.69 | −0.12 to 0.19 | 3.7–5.4% |

Post-publication decay is 78% on the headline portfolio and total for macro and carry. More
decisive than the decay: these are **gross academic long-shorts at 2–5% volatility** with no
fee, financing, shorting cost or capacity limit, earning **0.3–1.0%/yr** post-2019. A retail
multi-strategy wrapper charges on the order of 1.5%. To contribute like a 12.6%-volatility
trend sleeve they would need roughly **5× the notional**, multiplying every cost.

**Consequence.** The breadth multiplier `k / (1 + (k−1) rho_dd)` needs several
*implementable* engines to pay. There is one.

---

## 4. Trend's mechanism, measured here rather than cited

Same panel, 497 months 1985-01…2026-05. Trend's mean monthly excess return by equity-return
decile, worst first:

| Equity decile | 1 | 2 | 3 | 5 | 8 | 10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| equity, %/mo | −8.17 | −3.39 | −1.78 | +0.90 | +3.64 | +7.88 |
| **trend, %/mo** | **+2.56** | +0.40 | +0.49 | +1.06 | +1.57 | +0.58 |
| trend win rate | 70% | 50% | 64% | 68% | 69% | 51% |

Compounded across four structurally different equity drawdowns: dotcom equity −48.9% /
trend **+50.9%**; GFC −51.4% / **+29.6%**; covid −20.4% / **+10.5%**; 2022 inflation −19.4%
/ **+31.9%**. **Four different crisis types, positive in all four** — not one lucky episode.

**Trend pays in sustained selloffs and much less in sharp ones.** Covid, two months, gave
+10.5%; dotcom, twenty-five months, gave +50.9%. A 1987-style single-month crash would not
be hedged much, because the strategy needs time to establish positions.

**A discrepancy that must not be smoothed over.** [Experiment 004](trend-marginal-value.md)
reports a downside beta of **−0.67** and a crisis correlation of **−0.59**. On this panel
the comparable figures are **−0.18** and **−0.15**. The conditioning sets differ —
Experiment 004 uses 53 months inside frozen peak-to-trough windows, this uses the worst
equity quintile — and the gap is itself the mechanism: drawdown *windows* contain the
sustained declines trend profits from, while a worst-quintile screen is dominated by sharp
single-month falls it cannot react to. **Neither number is wrong and neither should be
quoted without its conditioning set.**

---

## 5. What the overlay is worth at a weight anyone can hold

25% trend notional, held sheltered so the measured 2.09 pp/yr distribution drag is zero,
net of 1.45%/yr on notional. Haircuts are applied to trend's mean.

| Window | no haircut | −4 pp | **−7.7 pp** (the repository's CTA bias bound) |
| --- | ---: | ---: | ---: |
| 1985–2025 | +2.60 | +1.60 | **+0.68** |
| post-publication 2012–2025 | +1.20 | +0.20 | **−0.73** |

pp/yr of growth at matched volatility. **The return case spans zero.** But in every cell
the drawdown improves — −50.3% to −48.0% on the full window even at the worst haircut, and
time under water falls from 72 months to 58.

**The haircut moves the mean and leaves the correlation alone.** That is why the risk
reduction survives assumptions that destroy the return gain, and it is
[Experiment 004](trend-marginal-value.md)'s "almost all of what survives is the correlation,
not the mean", reproduced at portfolio level against a leverage-matched control.

**These figures are now superseded by a frozen experiment, and it corrects them.**
[Experiment 011](../../research/experiments/exp_011_overlay_stack.yaml) reproduces the panel
exactly and reports, on the full window, a matched-volatility gap for a 50% trend overlay of
**+4.79 pp/yr against levered equity** `[+2.72, +6.73]` and **+4.58 against unlevered**
`[+2.53, +6.48]`, at an **MDE₈₀ of 2.82 pp/yr**. Two of the scoping numbers on this page are
wrong and are corrected here rather than quietly edited:

- **The break-even haircut is 9.57 pp/yr against the levered control and 9.16 against the
  unlevered, not the 9.9 quoted above.** The sweep is exactly linear at −0.5 pp of gap per
  pp of haircut, so the interpolation is exact.
- **The scoping script charged the borrow spread in its geometric returns but not in its
  Sharpe ratios**, so every matched-volatility gap in §§5–5a is overstated by the financing
  cost of the overlay notional — 0.295 pp/yr at a 50% overlay. The post-2012 gap is
  **+1.25 against unlevered equity, not +1.55.**

**The 7.7 pp/yr haircut used in the table above has now been measured against live funds,
and it is the wrong size and possibly the wrong sign.** [Experiment
012](live-managed-futures.md) rebuilds the trend leg from 46 real managed-futures funds'
Form N-PORT Item B.5 returns — net of their own fees, backfill-free, retaining the funds
that died. Over the 78 months both series exist, the **vendor series earned −2.62 pp/yr
*less* than the funds at matched volatility**, 95% interval `[−10.91, +5.68]`. **+7.7 sits
above that interval.** Two qualifications carry equal weight: the measurable window is
2019–2025, and the haircut is applied to a mean that lives in 1985–2011 where no fund return
exists; and the 7.7 figure bounds *hedge-fund CTA databases*, not this vendor's index
against registered funds. Every row on this page haircut by 7.7 pp/yr is therefore a
**scenario, not a bias estimate**, and must be read as one.

**And the experiment's own status is `unresolved`, on a clause frozen before it ran.**
Trend's measured pre- to post-publication decay is **12.11 pp/yr**, which **exceeds the
9.57 pp/yr haircut at which the overlay stops paying.** The full-window figure describes
1985–2025; it does not forecast. Post-2012, on a trend Sharpe of 0.296, the gap is still
+1.44 against levered equity and +1.25 against unlevered — **both true, and the tension
between them is the finding.**

### Against the control that decides

At **identical 1.5× gross notional**, 1985-2025, net of the same costs:

| Portfolio | geometric | volatility | Sharpe | max DD | under water |
| --- | ---: | ---: | ---: | ---: | ---: |
| equity only, 1.0× | 11.59% | 15.60% | 0.584 | −50.3% | 72 mo |
| **equity + 50% trend** | **17.13%** | 16.36% | **0.881** | **−43.0%** | **38 mo** |
| equity levered 1.50× | 14.59% | 23.39% | 0.584 | −66.7% | 85 mo |

Breadth beat leverage at the same notional by +2.5 pp/yr of growth, 7 pp less volatility
and 24 pp less drawdown. **This row is the case for capital efficiency and it is also the
most flattered number on this page** — see the limits below.

---

## 5a. Stress: the risk everyone names is not the risk that binds

Analytic, from `overlay_growth.py`. Base a global equity portfolio at `a_p = 5.0%`,
`sigma_p = 15.5%`; overlay 25% of trend notional at a **gross excess return of 4.0%** —
already a two-thirds haircut to the measured 12.07% — 12.6% volatility, 59 bp financing and
86 bp fee. Growth in pp/yr, reported against **both** the unlevered base and the
leverage-matched control.

| Scenario | `a_net` | vs unlevered | **vs leverage-matched** |
| --- | ---: | ---: | ---: |
| central case | +2.55% | +0.63 | **+0.62** |
| correlation rises to 0.00 | +2.55% | +0.59 | +0.54 |
| correlation rises to +0.20 | +2.55% | +0.49 | +0.34 |
| **correlation rises to +0.50** (crowded unwind) | +2.55% | +0.34 | **+0.06** |
| fee doubles to 1.72% | +1.69% | +0.41 | +0.40 |
| trend vol doubles to 25% | +2.55% | +0.52 | +0.40 |
| **held taxable** (2.09 pp drag) | +0.46% | +0.10 | +0.09 |
| trend excess halved to 2.0% | +0.55% | +0.13 | +0.12 |
| **financing +300 bp** | −0.45% | **−0.12** | **−0.13** |
| **trend excess to zero** (a five-year drought) | −1.45% | **−0.37** | **−0.38** |
| financing +500 bp | −2.45% | −0.62 | −0.63 |
| trend excess −2% *and* correlation +0.30 | −3.45% | −1.06 | −1.26 |

**Read the ordering, because it is not the intuitive one.** The overlay survives its
correlation turning from −0.08 all the way to **+0.50** — the crowded-unwind scenario people
name first — and still contributes. What breaks it is arithmetic on the *mean*: a financing
spike of 300 bp, or a five-year stretch with no trend return at all. **The second of those
is not a tail scenario; it is roughly what happened between 2012 and 2019.**

Two further readings. The leverage-matched column tracks the unlevered column almost exactly
except at `rho = +0.50`, which is the evidence that this construction is **not disguised
leveraged beta** — at 25% notional and near-zero correlation it adds little volatility to
match. And the taxable row confirms the placement constraint: +0.63 becomes +0.10.

**This table is univariate and that is a defect, not a simplification.** §5b replaces it as
the thing to quote. Its one modestly-joint cell is already the worst row here, and the joint
object shows why: moving one axis at a time understates the *tail* by about a factor of
two while barely moving the failure rate.

The break-even the sleeve must clear, by correlation, shows the same thing from the other
side — and shows how much the funding rule is carrying:

| `rho` | overlay bar | pro-rata bar |
| ---: | ---: | ---: |
| −0.20 | −0.39% | +2.21% |
| −0.08 | −0.16% | +2.44% |
| 0.00 | 0.00% | +2.60% |
| +0.50 | +0.98% | +3.57% |

**Even at a correlation of +0.50 the overlay bar is below 1%, while the pro-rata bar is
above 3.5%.** The analytic central case of +0.63 pp/yr also agrees with the empirical
+0.68 pp/yr measured at the 7.7 pp haircut in §5, by two routes that share no arithmetic.

---

## 5b. The joint surface: dependence moves the tail, not the failure rate

§5a moves one parameter at a time, which assumes without saying so that the adverse moves
are independent. They are not: a return drought arrives with a correlation that has risen
and financing that has widened. `stress_surface` in
[`studies/overlay_stress.py`](../../research/src/portfolio_edge/studies/overlay_stress.py)
varies all four axes together under a stated copula, at the recommended **30% overlay**,
40,000 draws, seed 20260816.

**The prior, stated because every number in it was chosen rather than measured.** The
centres are the page's own figures — `a_d ~ N(4.0%, 4.0%)`, `rho ~ N(−0.08, 0.20)`,
`sigma_d ~ 12.6% · exp(0.25 z)`, `s ~ 59 bp · exp(0.80 z)` — and the scales are wider than
estimation error alone would justify, because the forward uncertainty that matters is
regime rather than sampling. The 4.0 pp scale on the mean puts about 16% of mass below
zero, which is roughly what the post-2012 drought looks like on all three instruments.
The `ADVERSE_COPULA` sets `corr(a_d, rho) = −0.50`, `corr(a_d, s) = −0.40`,
`corr(rho, sigma_d) = +0.40` and `corr(s, sigma_d) = +0.30` on the latent normals.

| Copula | `P(gap < 0)` vs **leverage-matched** | `P(gap < 0)` vs unlevered | mean gap | p05 gap | mean gap when negative |
| --- | ---: | ---: | ---: | ---: | ---: |
| **independent** — what §5a assumes | **30.3%** | 29.1% | +0.65 | −1.41 | −0.80 |
| half adverse | 31.7% | 30.0% | +0.63 | −1.61 | −0.90 |
| **adverse** | **32.6%** | 30.7% | +0.62 | **−1.83** | **−1.01** |

**The finding is the shape of that change, and it is not what the red team predicted.**
Dependence moves the failure *rate* by 2.3 pp — a rounding error. It moves the fifth
percentile by **0.42 pp/yr, a 30% widening of the loss**, and the expected loss given a
loss by 0.21. **Correlated adversity does not make failure more likely; it makes failure
worse.** A univariate table cannot show that at all, because the quantity it understates
is a joint tail rather than a marginal probability.

**How badly the univariate table understates it, in its own units.** The worst cell
obtainable by moving one axis to its own 1st percentile is **−2.08 pp/yr**, and
**3.6% of the joint prior sits below it** under the adverse copula against 1.5% under
independence. §5a's own worst printed cell is **−1.26 pp/yr**, and **10.0%** of the joint
prior sits below *that*, against 6.4% under independence.

**The mean is what fails.** Among the failing draws, 99.2% have a below-median trend
excess return; 80.1% have an above-median correlation, 74.5% an above-median financing
spread, 68.4% an above-median volatility. **The overlay does not break on correlation. It
breaks on the mean, and correlation decides how much it hurts** — which is §5a's ordering
confirmed on a joint object rather than a list.

**Failure probability barely moves with weight, and the tail moves a great deal**, which
is the same statement again and is the reason weight is not a risk control here:

| overlay `w` | `P(gap < 0)` | mean gap | p05 gap |
| ---: | ---: | ---: | ---: |
| 0.15 | 30.6% | +0.35 | −0.86 |
| **0.30** | **32.6%** | **+0.62** | **−1.83** |
| 0.50 | 35.1% | +0.87 | −3.25 |
| 1.00 | 40.7% | +1.03 | −7.26 |

### The boundary, without any prior at all

`tolerable_financing_spread` gives the region's edge in closed form: the financing spread a
30% overlay can absorb before it loses to the leverage-matched control, in pp/yr. **Negative
means the overlay is already behind at zero financing cost, so no funding market rescues
it.**

| gross `a_d` \ `rho` | −0.20 | −0.08 | 0.00 | +0.20 | +0.30 | +0.50 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **0.0%** | −0.54 | −1.03 | −1.35 | −2.12 | −2.49 | −3.22 |
| **2.0%** | +1.46 | +0.97 | +0.65 | −0.12 | −0.49 | −1.22 |
| **4.0%** | +3.46 | +2.97 | +2.65 | +1.88 | +1.51 | +0.78 |
| 8.0% | +7.46 | +6.97 | +6.65 | +5.88 | +5.51 | +4.78 |

**Two cells are the whole monitoring rule.** At a zero forward trend excess return the
overlay is behind at any correlation and any financing cost. At 2.0% — half §5a's
already-haircut central case — it survives at trend's measured correlation with 97 bp of
financing headroom, and **dies at a correlation of +0.20 or above**. That pair, `a_d ≥ 2%`
and `rho ≤ +0.20`, is the condition to monitor.

**And the bar that decides is not the one §5a leads with.** The overlay bar
`rho sigma_p sigma_d` is *negative* at negative correlation. The **leverage-matched** bar
is `a_p (sigma_total / sigma_p − 1) / w`, which is **positive at every correlation**,
because a portfolio held at higher volatility must earn more merely to keep the base's
Sharpe ratio. At the recommended weight it is about **+0.16%/yr**, not zero.

---

## 6. Global versus US: the two datasets disagree, and the disagreement is the finding

**This section previously claimed global diversification was the largest certain
improvement available. Building the candidate frontier falsified that, and the claim is
withdrawn.** What follows is what the evidence actually supports.

### What the century of local-currency data says

[JST R6](evidence-base.md), annual **real, local currency**, US against an equal-weight
ex-US basket held 60/40:

| | geometric | volatility | geo/vol | max DD | under water |
| --- | ---: | ---: | ---: | ---: | ---: |
| USA alone, 1871–2020 | 6.82% | 18.23% | 0.37 | −51.9% | 13 yr |
| 60/40 global, 1871–2020 | 6.68% | 14.68% | **0.46** | **−46.0%** | **10 yr** |
| USA alone, 1963–2020 | 6.28% | 15.64% | 0.40 | −47.2% | 13 yr |
| 60/40 global, 1963–2020 | **6.44%** | 15.20% | **0.42** | **−42.6%** | **10 yr** |

### What the USD data says, and it says the opposite

Ken French regional market factors, **monthly nominal USD**, 426 months 1990-07…2025-12 —
the only multi-region series here that a US investor could actually have earned:

| | geometric | volatility | Sharpe | max DD | under water |
| --- | ---: | ---: | ---: | ---: | ---: |
| 100% US | **10.98%** | 15.16% | **0.594** | **−50.3%** | 72 mo |
| global 60/30/10 | 9.41% | 14.84% | 0.507 | **−53.1%** | 63 mo |

**Global lost 1.57 pp/yr *and* drew down deeper.** Both halves contradict the table above.

### Why they disagree, and which one to believe

Two differences, both material and neither dismissible.

- **Currency.** JST returns are **local currency**; the French regional factors are
  **USD**, so they carry the exchange-rate exposure a US investor actually bears. The JST
  result is what a local investor in each market earned, not what an American earned.
- **Window.** 1990–2025 is precisely the period in which the US ran away — the drift gap
  measured in [Experiment 003](rebalancing-policy.md) is **4.34 pp/yr against a
  `gamma_star` of 12.5 bp**. The JST windows are 150 and 58 years.

**Neither is the answer, and the honest conclusion is narrower than either.** The case for
holding global equity is **not** that it has historically outperformed — in the only USD
series available it did not, by a wide margin. The case is that **the United States is the
survivor, and its record cannot be bought in advance.** Sixteen countries produced a median
real drawdown near −74%; the US produced −51.9% and ranks 15th of 16 on the full sample and
**16th of 16 from 1963** ([the ladder](setting-the-equity-share.md)). Concentrating in the
market that happened to win is a bet on that outcome repeating, and nothing here supports
that bet.

That is a **statement about the distribution of outcomes, not a prediction of returns**, and
it should never be quoted as evidence that global diversification raises expected return. On
the evidence available it does not.

### The vehicle decides the sign, and this repository has been naming the wrong one

**This is the practical payoff of §1 and it took a red team to notice it.** The funding
rule is not a modelling choice a reader makes; it is a property of the *fund they buy*.
A standalone managed-futures ETF is a pro-rata vehicle: holding DBMF beside equity means
selling equity to buy it, expression (2), a bar of about **+2.44 pp/yr**. A return-stacked
ETF is an overlay vehicle: nothing is sold, expression (1), a bar near zero and **negative**
at trend's measured correlation. **Same strategy, same evidence, opposite verdict, decided
entirely by the ticker** — and [the recommendation](portfolio-recommendation.md) named the
vehicle that gets the worse bar. §6a audits the shelf that follows from this.

---

## 6a. The wrapper shelf, audited from the filings

**The question §6 raises and does not answer.** The entire recommendation now rests on a
financed retail wrapper existing, and exactly one product had ever been examined for the
role. This section enumerates the shelf, prices it, and asks the only two questions that
decide: **is the wrapper an overlay or a pro-rata vehicle, and what happens when it
closes.** `as of 2026-08-17`, from SEC filings and each issuer's own documents.

### 6a.1 A dichotomy was the wrong shape, and one number replaces it

§1 states the funding rule as two rules. **Real wrappers are a continuum, and reading them
as a dichotomy gets NTSX wrong.** A 90/60 efficient-core fund sells ten cents of equity to
buy sixty cents of Treasury notional: neither rule describes it. From
[`studies/wrapper_economics.py`](../../research/src/portfolio_edge/studies/wrapper_economics.py),
for a wrapper delivering `b` of base and `d` of diversifier notional per dollar of capital,

    dg/dw at w=0  =  (a_net - rho sigma_p sigma_d)  -  delta (a_p - sigma_p**2),
    delta = (1 - b) / d,                                                          (7)

so **the wrapper's structure enters exactly once, as a multiplier on §1's gap.** `delta` is
the base sold per unit of diversifier notional obtained; `1 - delta` is the share of the
funding-rule benefit the wrapper keeps. Equation (7) reduces to (1) at `delta = 0` and to (2)
at `delta = 1`, and both reductions are pinned by tests that differentiate an independently
written growth function rather than asserting the module's own output.

**Two consequences that are not obvious and both bite on the real shelf.**

- **Gross notional per dollar decides nothing.** A 50/50 equity-and-trend fund and a
  standalone trend fund both show 1.0× and both pay §1's gap in full; a 90/60 fund shows
  1.5× and pays a seventh of it. **A wrapper at 40% equity and 30% trend has `delta = 2.0`
  and is worse than selling equity outright** — a category with no name in the marketing
  vocabulary and which the gross-notional figure cannot distinguish from the good case.
- **An expense ratio is quoted in the wrong units.** The hurdle is stated per unit of
  *notional*; a fee is charged on *capital*. The conversion is `fee / d`. NTSX's 0.20% buys
  0.635 of Treasury notional and is therefore **0.315% per unit of notional**, and a wrapper
  charging 20 bp for 0.10 of notional is dearer than one charging 100 bp for 1.00.

### 6a.2 Structure, from the holdings rather than the fact sheet

Every figure below is computed from the fund's own **Form N-PORT** holdings and derivative
notionals in the SEC's 2026Q2 structured data set, not from marketing copy. Provenance,
hashes and retrieval dates are in
[`data-manifests/wrapper_shelf/shelf_census.json`](../../research/data-manifests/wrapper_shelf/shelf_census.json).

| Wrapper | Report date | Base leg, % NAV | Overlay leg, % NAV | Gross | `delta` | **Funding capture** |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| **RSSB** global stocks & bonds | 2026-04-30 | 100.07 equity | 100.33 Treasury futures | 2.004 | **−0.00** | **100%** |
| **RSST** US stocks & managed futures | 2026-04-30 | ≥100 equity (see below) | ~100 trend, per prospectus | ~2.0 | **≤0.00** | **100%** |
| **NTSX** US efficient core | 2026-03-31 | 90.83 equity | 63.50 Treasury futures | 1.543 | 0.144 | 85.6% |
| **NTSE** emerging efficient core | 2026-03-31 | 90.33 equity | 63.71 Treasury futures | 1.540 | 0.152 | 84.8% |
| **NTSI** developed ex-US efficient core | 2026-03-31 | 89.89 equity | 61.03 Treasury futures | 1.509 | 0.166 | 83.4% |
| **GDE** efficient gold plus equity | 2026-02-28 | 84.80 equity | 83.63 gold futures | 1.684 | 0.182 | 81.8% |
| **GDMN** efficient gold plus miners | 2026-02-28 | 86.70 **gold miners** | 80.70 gold futures | 1.674 | 0.165 | *base not substitutable* |
| **DBMF, CTA, KMLM, FMF, WTMF** | 2026-02…04 | **0 equity** | 100 trend | 1.000 | **1.000** | **0%** |
| a hypothetical 50/50 blend | — | 50 equity | 50 trend | 1.000 | 1.000 | 0% |

At `a_p = 5.0%` and `sigma_p = 16%`, `delta` converts to a hurdle: **0.00 pp/yr for RSSB and
RSST, 0.35 for NTSX, 0.40 for NTSI, and the full 2.44 for every standalone managed-futures
fund.** The last row is the one to keep: **a 50/50 blend is marketed as capital efficient and
is, at the margin, arithmetically identical to selling equity to buy a standalone product.**

**RSSB is the clean read and it verifies the marketing exactly.** Two equity ETFs at 90.53%
of net assets plus one long equity-index future at 9.54% is **100.07% equity**; four long
Treasury-note and bond futures total **100.33% of net assets**. The two legs use different
N-PORT asset categories, so nothing is commingled and `delta = −0.0007`.

**RSST cannot be read the same way, and the limitation is stated rather than filled in.**
It holds the SPDR Portfolio S&P 500 ETF at **74.09%** of net assets, a government money fund
at **16.04%** as futures collateral, and a diversified futures book at **2.96× net assets of
gross futures notional**. Its equity-index futures serve *both* the base top-up and the trend
book's own equity positions, and **N-PORT does not label which is which**, so the 100/100
split cannot be verified from the filing. What can be established bounds the answer usefully:
equity-index futures are **70.21% of net assets and every one of them is long**, so total
equity exposure is 144.30% and `b ≥ 1.0` is not in doubt. The prospectus states the target
directly — *"The Fund will target a 100% exposure to each of its U.S. Equity strategy and its
Managed Futures strategy"* ([497K, 2026-04-27](https://www.sec.gov/Archives/edgar/data/1924868/000199937126009152/rsst-497k_042726.htm),
retrieved 2026-08-17). **RSST forfeits none of the funding-rule benefit; the exact split is
`not found` from the holdings.**

**A consequence nobody markets.** RSST's realised equity exposure is 100% *by contract* plus
whatever the trend book is doing in equity indices, which on 2026-04-30 was a further 44
points long. The wrapper's equity beta is therefore **time-varying around 1.0**, and a reader
who models it as a constant dollar of equity is modelling a tracking error away.

**RSBT, RSBA, RSBY stack on a bond base, not an equity one**, and equation (7) does not apply
to them for an equity-based investor: they change the base composition *and* add an overlay,
and no single `delta` separates those two decisions. `base_substitution_note` refuses to score
them rather than returning a number, which is the correct behaviour and is pinned by a test.

### 6a.3 Cost, in the units the hurdle is stated in

From each fund's own SEC-filed fee table, retrieved 2026-08-17. **Not one Return Stacked or
WisdomTree fund carries a fee waiver**, so there is no cap to expire and no recoupment clause
— a materially better structure than the contractual-cap-plus-recoupment funds
[the alternative-sleeves audit](alternative-sleeves-audit.md) found elsewhere.

| Wrapper | Mgmt | AFFE | **Total ER** | Waiver | `d` | **Cost per unit of overlay notional** |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| **NTSX** | 0.20 | — | **0.20%** | none | 0.635 | **0.315%** |
| **GDE** | 0.20 | — | 0.20% | none | 0.836 | **0.239%** |
| **RSSB** | 0.35 | 0.04 | **0.39%** | none | 1.003 | **0.39%** |
| **NTSI** | 0.26 | — | 0.26% | none | 0.610 | 0.426% |
| **NTSE** | 0.32 | — | 0.32% | none | 0.637 | 0.502% |
| **RSSX** stocks & gold/bitcoin | 0.65 | 0.02 | 0.67% | none | ~1.0 | ~0.67% |
| **RSST** | 0.95 | 0.04 | **0.99%** | none | ~1.0 | **~0.99%** |
| **RSSY** stocks & futures yield | 0.95 | 0.04 | 0.99% | none | ~1.0 | ~0.99% |
| RSBT / RSBY / RSBA | 0.95 | 0.05–0.06 | 1.01% | none | ~1.0 | ~1.01% |
| *DBMF, for comparison* | — | — | *0.85%* | *none* | *1.000* | *0.85%* |

**The fee is not the whole cost, and the prospectus says so.** Tidal's unitary fee explicitly
excludes *"interest charges on any borrowings made for investment purposes"*, and the strategy
description states that the managed-futures return is stacked *"minus the cost of
financing"*. **So the embedded financing cost sits outside the 0.99% and is borne by the
shareholder, undisclosed in size.** That is the input §5b's boundary table prices, and the
boundary is not tight: at a 2.0% forward trend excess return and trend's measured
correlation, a 30% overlay tolerates **97 bp** of financing spread.

**Where that spread lands is a structural question this repository has already answered from
the other side.** [Structural and tax-aware edges §3](structural-and-tax-edges.md#3-section-1256-and-capital-efficiency-handled-honestly)
measures Treasury-futures financing at **12–18 bp against OIS**, equity-index futures at
**+62 bp against three-month Term SOFR** post-2022, and a **diversified long/short trend book
at a signed mean of about zero** because it takes both sides by construction. Applied to the
structures above, and labelled as inference from those measurements rather than as a
measurement of these funds:

- **NTSX pays its financing on the leg the evidence prices best.** 63.5% of Treasury futures
  at 12–18 bp is **8–11 bp/yr on capital**, against a break-even the same page puts at
  **48.3 bp/yr of Treasury excess return over cash**.
- **RSST's overlay leg is close to unfinanced in the signed sense**, and the +62 bp
  equity-futures basis falls on the roughly 26% of the *base* leg delivered by futures rather
  than on the trend notional — about **16 bp/yr on capital**, which is a cost of holding the
  equity through this wrapper rather than a cost of the overlay.
- **No fund discloses its realised financing cost anywhere.** Every figure in this bullet
  list is a transfer from published research on the contracts, not a reading of a filing, and
  it is `not found` as a fund-specific fact.

### 6a.4 The tax finding, which changes the account rule

Each fund computes an SEC-standardised after-tax return at the **highest individual federal
rates**, and this repository already uses that instrument. The method reproduces the three
figures [the trend audit](trend-marginal-value.md#cost-and-tax) published — DBMF 2.09, KMLM
1.81, FMF 0.76 — which is what licenses reading the new rows the same way.

| Fund | Period | Before tax | After tax on distributions | **Drag pp/yr** |
| --- | --- | ---: | ---: | ---: |
| **RSST** | since 2023-09-05 | 17.17% | 16.85% | **0.32** |
| **NTSX** | since 2018-08-02 | 11.58% | 11.25% | **0.33** |
| NTSI | since 2021-05-20 | −0.77% | −1.24% | 0.47 |
| RSSY | since 2024-05-28 | −0.88% | −1.38% | 0.50 |
| NTSE | since 2021-05-20 | −5.90% | −6.52% | 0.62 |
| RSBT | since 2023-02-07 | −1.81% | −2.55% | 0.74 |
| RSSB | since 2023-12-04 | 20.71% | 19.92% | 0.79 |
| RSBY | since 2024-08-20 | −14.65% | −15.73% | 1.08 |
| RSBA | since 2024-12-17 | 7.68% | 6.38% | 1.30 |
| **GDE** | since 2022-03-17 | 18.63% | 17.10% | **1.53** |
| *KMLM* | *since 2020-12-01* | *5.77%* | *3.96%* | *1.81* |
| **DBMF** | since 2019-05-07 | 8.28% | 6.19% | **2.09** |

**The low drag is a property of the overlay's asset, not of the wrapper.** NTSX and GDE are
the same issuer, the same structure and the same 0.20% fee, and their drags differ by a factor
of 4.6. Treasury futures throw off compensation a bond holder would have been taxed on anyway;
**gold futures are §1256 contracts marked to market every 31 December with nothing to defer**,
so GDE converts an asset a long-only holder could have held untaxed for decades into an annual
realisation. Any reader tempted to read "efficient core is tax-efficient" as a structural fact
should read these two rows instead.

**A dollar of managed-futures notional costs 0.32 pp/yr of distribution tax through RSST and
2.09 through DBMF.** [The recommendation](portfolio-recommendation.md) calls managed futures
*"the one sleeve whose account decides its sign"* on the strength of the 2.09. **That is true
of the pro-rata vehicle and is not true of the overlay one**, and §7's shelter constraint —
the thing that sets the weight — is correspondingly weaker.

**Three reasons not to bank the whole 1.77 pp difference.** RSST's window is **28 months**
against DBMF's 80, and every one of those months is a rising market in which a growing ETF
can defer realisation; DBMF's window contains 2022, a year of very large realised trend
gains, so the two are not like-for-like. And a fund's after-tax table is a **backward-looking
disclosure, not a contract**: RSST runs the same Cayman-subsidiary structure that makes
DBMF's income ordinary, and nothing prevents its drag rising. **The direction is solid; the
magnitude is one short window.**

### 6a.5 Survival, and the shelf-age claim this page had wrong

**The claim that "the entire shelf is younger than six years" is false and is withdrawn.** It
came from a name screen that missed both long-lived families. From the 2019Q4 census:
**NTSX filed at $39.0m in 2019Q4** — inception **2018-08-02**, now eight years old and
$1,203.6m — and the **entire PIMCO StocksPLUS family was already there**, five of its funds
above $1bn, on a strategy PIMCO has run since the 1980s. Capital efficiency is not a
post-2020 fashion; the *retail ETF* expression of it is.

Filed net assets, 2025Q4 → 2026Q2, from the same two censuses:

| Wrapper | 2025Q4 | 2026Q2 | Change | In 2019Q4? |
| --- | ---: | ---: | ---: | --- |
| **NTSX** | $1,262.6m | $1,203.6m | **−4.7%** | **yes, at $39.0m** |
| **RSSB** | $381.8m | $476.6m | +24.8% | no |
| NTSI | $433.8m | $456.6m | +5.3% | no |
| **RSST** | $292.8m | **$415.0m** | **+41.7%** | no |
| RSBT | $86.9m | $127.0m | +46.1% | no |
| RSSY | $116.2m | $107.2m | −7.7% | no |
| RSBY | $96.9m | $77.9m | **−19.6%** | no |
| RSSX | $37.3m | $65.1m | +74.5% | no |
| RSBA | $24.2m | $52.6m | +117.6% | no |
| NTSE | $34.4m | $45.9m | +33.4% | no |
| *PIMCO StocksPLUS, eight funds* | *$9.40bn* | *$8.93bn* | *−5.0%* | ***yes, all eight*** |

**RSST is the fastest-growing wrapper on the shelf and reached $508.7m by 2026-08-14**
(issuer's own page, retrieved 2026-08-17). **Not one of the 23 capital-efficient series in
either census is marked as a final filing and none is absent from the later one**, so the
measured closure count over these two quarters is **zero**. Two quarters is far too short to
update §9.4's 10.7%/yr hazard and it is not used to: it is reported as the observation it is.

**The Return Stacked family is now seven ETFs, not five**, and this page had listed five. The
two it missed are **RSBY** (bonds and futures yield, −14.65%/yr since inception and shrinking
19.6% in two quarters — the one fund here whose numbers point at closure) and **RSSX** (stocks
and gold/bitcoin, the fastest-growing after RSBA).

### 6a.6 What this does to §3's breadth finding

§3 concludes that four effectively independent engines exist on paper and **only trend has a
financed retail wrapper**. That is no longer the whole picture, and the correction runs in the
repository's favour on count and against it on quality:

| Engine | Financed overlay wrapper | Base it stacks on |
| --- | --- | --- |
| Trend | **RSST** | US equity — substitutable |
| Term premium | **NTSX / NTSI / NTSE, RSSB** | equity — substitutable |
| Merger arbitrage | **RSBA** | **bonds — not substitutable for an equity base** |
| Carry / "futures yield" | RSSY | US equity — substitutable |
| Gold and bitcoin | RSSX | US equity — substitutable |
| BAB, QMJ, reversals, accruals, issuance, buybacks | **none** | — |

**So the count of financed wrappers rose from one to five and the count of *engines §3 found
worth having* rose from one to one.** BAB, short-term reversal and accruals — the three that
produce the effective breadth of 4.06 — still have no vehicle of any kind, and merger
arbitrage arrives only stacked on a base an equity investor does not hold. **§3's conclusion
that the fund shelf binds before the evidence does survives this audit intact**; what changed
is that the binding is now demonstrably about *which* strategies have a deep enough futures
market, since the industry has proved willing to wrap five different ones in two years.

---

### Can valuation settle it? No — measured, not assumed

Valuation conditioning has never been tested in this repository, and the Shiller and
Goyal–Welch data landed in the same round as everything else here, so it can be. If CAPE
predicted subsequent returns well enough, it would resolve US versus global directly.

Regressing subsequent **10-year annualised real total return** on `log(CAPE)`, built from
Shiller's real total-return index rather than taken from his forward-return column,
1881-01…2016-08:

| Test | Result |
| --- | --- |
| In-sample slope, full period | **−0.0658**, R² **0.258** |
| In-sample, post-1950 | −0.0724, R² 0.286 |
| In-sample, post-1985 | **−0.1292**, R² **0.680** |
| Out-of-sample R² vs prevailing mean, **no embargo** | +0.232 — **contaminated** |
| Out-of-sample R², **120-month embargo** | **+0.174** |

**The embargo matters and is easy to omit.** An expanding-window forecast that trains on
10-year forward returns which have not yet finished is using data from after the forecast
date. Purging the training set to labels fully realised beforehand cuts the out-of-sample
R² from +0.232 to +0.174 — the difference is look-ahead, and it is the reason
`docs/the-plan.md` requires purging and embargo where labels overlap.

**And +0.174 still cannot size a decision, because of what n is.** There are 1,040
overlapping monthly observations and about **eight independent ten-year windows**. The
post-1985 R² of 0.680 is one long swing of rising valuations and falling subsequent
returns, not 380 observations. A relationship measured on eight effective points cannot
distinguish +0.17 from zero.

At the current CAPE of 41.2 the in-sample line forecasts roughly **+0.3%/yr real over ten
years, against a residual standard deviation of 4.43 pp — a 95% band of about ±8.7 pp
before any correction for overlap.** The point estimate is unusually low and the band
swamps it.

**Consequence: valuation conditioning is `unresolved` and cannot arbitrate US versus
global.** The relationship is real and the instrument's resolution sits far below the
decision's requirement — which is precisely the check
[the evidence base](evidence-base.md) exists to force before an experiment is commissioned.
This closes round-two item 5 with a measured reason rather than leaving it open.

---

### The candidate frontier, with the two decisions separated

The frontier above conflated two independent choices. Separating them is the whole point,
because **one of them is resolved and the other is not.**

Same 426-month USD window. `+25% trend` is haircut by the repository's full **7.7 pp/yr**
CTA bias bound — the pessimistic row. `B2` levers the *same base* to the candidate's own
volatility, which is the control the plan makes mandatory.

| Base | Candidate | geometric | volatility | Sharpe | max DD | **ΔSharpe** |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| **US** | no overlay (**B0**) | 10.98% | 15.16% | 0.594 | −50.3% | — |
| US | + 25% trend, no haircut | 13.71% | 14.93% | 0.765 | −46.6% | +0.171 |
| US | **+ 25% trend, 7.7 pp haircut** | **11.56%** | 14.93% | **0.636** | **−48.0%** | **+0.042** |
| US | leverage-matched 0.985× control | 10.88% | 14.93% | 0.595 | −49.7% | **+0.001** |
| **Global** | no overlay (**B1/C1**) | 9.41% | 14.84% | 0.507 | −53.1% | — |
| Global | + 25% trend, no haircut | 12.10% | 14.60% | 0.681 | −49.6% | +0.174 |
| Global | **+ 25% trend, 7.7 pp haircut** | 9.98% | 14.60% | 0.549 | −51.0% | **+0.042** |
| Global | leverage-matched 0.984× control | 9.32% | 14.60% | 0.508 | −52.4% | **+0.001** |

**The overlay's contribution is identical on both bases to three decimals** — ΔSharpe
**+0.042** at the full bias haircut, **+0.171** without it — while the leverage-matched
control contributes **+0.001**. Two things follow, and they are the most useful pair of
numbers on this page.

1. **The overlay decision is independent of the base decision.** Whatever a reader
   concludes about US versus global, the overlay answers the same way.
2. **It is breadth and not beta.** A control levered to the identical volatility from the
   identical base buys 0.001 of Sharpe. The overlay buys 0.042 at the pessimistic haircut.

**And the US base with an overlay beats B0 outright** — 11.56% against 10.98%, at a 2.3 pp
shallower drawdown, on the window the US won. That is the one candidate here that clears
100% US equity on its own favoured sample.

**The base choice remains unresolved and must not be settled by this table.** Preferring the
US base because it won 1990–2025 is the ex-post selection error this repository exists to
catch. The overlay result is what survives; the base result is a window.

---

## 7. The weight is a corner solution, and the constraint is the account

The recommended 15–25% was chosen by judgement. A red team asked what the model itself
says, and the answer is that **the sizing question has no interior solution.**

**The shrunk growth-optimal overlay notional**, from
[`overlay_growth.py`](../../research/src/portfolio_edge/studies/overlay_growth.py), at
`a_p = 5.0%`, `sigma_p = 15.5%`, `sigma_d = 12%`, `rho = −0.10`, shrunk by
`f* = S**2 T / (S**2 T + 1)` on `T` years of *stationary* information:

| Evidence | net `a_d` | unshrunk `w*` | T=10 | **T=20** | T=40 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Live funds, net (S=0.33) | 3.96% | 2.88 | 1.57 | **2.03** | 2.38 |
| Built here (S=0.52) | 6.24% | 4.46 | 3.31 | **3.80** | 4.10 |
| **Pessimistic (S=0.20)** | 2.40% | 1.80 | 0.57 | **0.86** | 1.17 |
| Post-2012 drought (S=0.00) | 0.00% | 0.13 | 0.00 | **0.00** | 0.00 |

**Even the pessimistic row puts the optimum at 86% of notional**, four times the
recommended weight. Only a forward Sharpe of exactly zero brings it to zero.

**And the drawdown constraint — the one that made leveraged equity unholdable — does not
bind here.** Measured on the independent series over 1,091 months:

| overlay `w` | geometric | volatility | Sharpe | **max drawdown** | under water | gross |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.00 | 11.13% | 15.81% | 0.540 | **−50.3%** | 74 mo | 1.00 |
| 0.25 | 12.86% | 16.15% | 0.629 | −49.3% | 74 | 1.25 |
| 0.50 | 14.50% | 17.06% | 0.690 | −49.3% | 72 | 1.50 |
| **1.00** | 17.51% | 20.23% | **0.741** | −49.4% | 72 | 2.00 |
| 2.00 | 22.31% | 29.65% | 0.723 | **−52.0%** | 72 | 3.00 |

**Maximum drawdown is close to flat in `w` on this path** — −49% to −52% from 1.0× to
3.0× gross notional, against **−99.3% for equity levered to 2.2×** in §2. That contrast
is the argument for breadth over leverage: uncorrelated notional barely deepens the
drawdown, correlated notional ruins it.

**Read "flat" as scoped to this path and to modest weights, because resampling breaks it
at the top of the range.** An earlier draft of this section said maximum drawdown is flat
"across the entire range". Under a paired block bootstrap the overlay draws down deeper
than equity in **6.9%** of histories at `w = 0.30`, **26.9%** at `w = 1.00` and **78.7%**
at `w = 2.00` — **so the `w = 2.00` row above is a lucky draw from a distribution centred
on −7.7%**, and the property is a property of small weights rather than of the whole
ladder. The full attack is in §5b.

**That table was produced by an uncommitted scoping script. It is now reproduced from the
pinned sources by [`_overlay_stress_tables.py`](../../research/src/portfolio_edge/studies/_overlay_stress_tables.py),
and it survives — with three corrections that must travel with it.**

- **Every geometric return, maximum drawdown and time under water above reproduces
  exactly.** The volatilities and Sharpe ratios do not: each volatility here is about
  0.3% *relative* higher (15.86% against 15.81% at `w = 0`, at the same ratio on every
  rung), moving each Sharpe by roughly 0.002. The quantities the argument rests on agree;
  the residual is recorded rather than reconciled because the script that produced the
  published figures no longer exists.
- **The ladder charges no borrow spread.** It finances 2.00× gross notional free. At this
  repository's own 60 bp the `w = 1.00` rung is 16.82% rather than 17.51% and the `w = 2.00`
  rung is 20.87% rather than 22.31%. Drawdown is almost unmoved.
- **The window starts 1934-07, and 1929-32 is excluded by construction.** The trend leg's
  36-month signal burn-in plus its 60-month volatility-target window consume the first 96
  months of a panel that begins 1926-07. So the **−50.3%** this table anchors on is not US
  equity's worst drawdown — §2 of this page puts that at **−83.7%** on the same series —
  and the flat-drawdown claim was never tested against the deepest episode in the record.

**The flat-drawdown property survives all three attacks at the recommended weight and
fails at high weight.** §9 has the numbers; the short version is that it is a real
property of a diversifying overlay and not an artefact of one path, that it is *not*
flat in every crisis, and that it depends entirely on an assumption the stress table
never varied.

**So the weight is set by the account, not by the estimate or the risk.** The binding
constraints, in order:

1. **Tax shelter capacity.** Managed-futures distributions are ordinary income at
   2.09 pp/yr in a taxable account and zero in a shelter, and a 100/100 return-stacked
   fund delivers one dollar of overlay notional per dollar held. **The overlay cannot
   exceed the shelter that will hold it.**
2. **Fund closure and methodology change**, on a shelf where no fund is six years old.
3. **Model risk the shrinkage does not cover** — `sigma_d` and `rho` are treated as
   known, and the post-2012 drought is real on all three instruments.

**What the constraint costs is exact**, from the parameter-free retention curve
`1 − (1 − f)**2` with `f = w / w*`:

| `w` | share of the optimum | growth retained | gain |
| ---: | ---: | ---: | ---: |
| 15% | 0.07 | **14.2%** | +0.61 pp/yr |
| 25% | 0.12 | 23.1% | +0.99 pp/yr |
| **30%** | 0.15 | **27.4%** | **+1.18 pp/yr** |
| 100% | 0.49 | 74.3% | +3.43 pp/yr |

**Consequence: hold as much as the shelter allows, and stop there.** There is no
interior optimum to search for, the drawdown that would justify holding less does not
appear, and every weight under discussion sits on the gentle left branch of the growth
parabola where being wrong is cheap.

---

## 8. Concentration: the variance argument is weak and the skewness argument is the real one

[Search coverage](search-coverage.md) §2 records that "the objective wants concentration
and the programme has only tested dilution", on the grounds that growth-optimal sizing
returns a corner solution. **That conflates two different corners**, and the concentration
one is now measured rather than asserted.

For `N` equicorrelated names at single-stock volatility `sigma` and pairwise correlation
`rho`, equal-weighted, the excess growth rate is exactly

    gamma_star = 0.5 sigma**2 (1 - rho) (1 - 1/N)

so the growth **given up** by holding `N` names instead of the whole market is
`0.5 sigma**2 (1 - rho) / N`. At `sigma = 35%` and `rho = 0.25`:

| Names held | 1 | 5 | 10 | 25 | 50 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Growth given up vs the market | **4.58 pp/yr** | 0.91 | 0.45 | **0.17** | 0.08 |
| Extra alpha needed to break even | 4.58 pp/yr | 0.91 | 0.45 | **0.17** | 0.08 |

**Two readings, and the second is the one that matters.**

**Concentrating into a single stock costs 3.4–8.6 pp/yr of growth** across plausible
parameters — an enormous, and entirely mechanical, penalty. But **the penalty collapses
as `1/N`**: at twenty-five names it is **0.17 pp/yr**, smaller than the fee difference
between two ordinary funds. **So the variance channel gives almost no reason to hold five
hundred stocks rather than twenty-five**, and any argument against a
twenty-five-name portfolio that rests on the diversification return is arguing about
seventeen basis points.

**The real argument against concentration is skewness, and this model does not contain
it.** The expression above assumes every name has the same expected return. Individual
stock returns are severely right-skewed — the median stock underperforms Treasury bills
over its life and the market's entire return comes from a small minority — so a
concentrated book has a high probability of badly trailing the market even when its
*expected* return matches. That is a statement about the cross-sectional distribution of
outcomes, not about variance drag, and **it cannot be read off `gamma_star`.**

**Consequence.** The objective is close to indifferent to concentration above roughly
twenty-five names, so "the objective wants concentration" is not supported by the
variance arithmetic that was cited for it. Whether to concentrate turns on whether the
holder has genuine selection skill, which is a different question this repository has
never tested and which its detection floors could not resolve if it tried.

---

## 9. The flat drawdown attacked, and the failure modes priced

All of this is `exploratory`. The panel is Experiment 011's, minus its vendor trend leg,
with the leg rebuilt by [`time_series_momentum`](../../research/src/portfolio_edge/studies/time_series_momentum.py);
the specification was written after §7's numbers were known, and no re-run converts that.
Regenerate with `uv run python -m portfolio_edge.studies.overlay_stress`.

### 9.1 The drawdown, resampled

Circular block bootstrap, 24-month blocks, 4,000 **paired** resamples, seed 20260816,
60 bp financing charged. The statistic is `mdd(w) − mdd(0)`: **positive means the overlay
drew down less** than unlevered equity on the same resampled history.

| `w` | observed | mean | 95% interval | **`P`(overlay deeper)** |
| ---: | ---: | ---: | --- | ---: |
| 0.25 | +0.91% | +3.62% | `[−0.98%, +9.95%]` | **6.5%** |
| **0.30** | **+0.92%** | +4.18% | `[−1.18%, +11.60%]` | **6.9%** |
| 0.50 | +0.88% | +5.83% | `[−2.37%, +17.80%]` | 9.6% |
| 1.00 | +0.56% | +5.69% | `[−7.65%, +22.98%]` | 26.9% |
| 2.00 | **−2.05%** | −7.69% | `[−28.01%, +12.55%]` | **78.7%** |

**The flat-drawdown property is not an artefact of one path at the recommended weight, and
it is at 3.0× gross.** At `w = 0.30` there is a 6.9% chance the overlay's drawdown is the
deeper one, and the interval barely crosses zero. At `w = 2.00` it is 78.7% and the
observed −2.05% is the *good* end of a distribution centred on −7.69%. §7's `w = 2.00` row
is therefore a lucky path, and the one place the published ladder should not be quoted.

**No minimum detectable effect is quoted here and none exists.** Maximum drawdown is an
order statistic of a path, not a mean, so the MDE machinery does not apply; the interval
width is the resolution statement and it is enormous — ±10 pp at the recommended weight.
**Anyone reading the −49.3% and −50.3% cells as a 1.0 pp difference is reading noise.**

### 9.2 The crisis windows, which are not flat

Peak-to-trough inside each episode `docs/the-plan.md` names, 60 bp financing charged.

| Window | n | `w = 0.00` | `w = 0.30` | `w = 1.00` |
| --- | ---: | ---: | ---: | ---: |
| 1937-38 | 13 | −49.33% | −48.69% | −47.64% |
| **1973-74** | 24 | −44.95% | **−33.49%** | **−16.49%** |
| **late-1970s inflation** | 39 | −11.99% | **−13.19%** | **−16.69%** |
| **1987** | 5 | −29.85% | **−31.84%** | **−37.57%** |
| 1998 | 4 | −15.62% | −15.77% | −16.10% |
| 2000-02 dotcom | 30 | −44.99% | −40.15% | −33.05% |
| 2008-09 GFC | 16 | −47.99% | −41.91% | −26.43% |
| 2020 Q1 covid | 3 | −20.22% | −18.36% | −13.95% |
| **2022 inflation** | 12 | −20.49% | **−20.70%** | **−22.17%** |
| **1929-32 great crash** | 34 | *not in the panel* | | |

**The overlay makes the drawdown worse in four of nine episodes**, and the pattern is the
mechanism §4 describes rather than noise: it loses in the *sharp* ones (1987, five months)
and in the ones where its own positions were caught wrong-footed by a reversal (2022,
late-1970s), and wins by large margins in the sustained ones (1973-74, dotcom, GFC).
**"Maximum drawdown is flat in `w`" is a statement about the full path's single worst
episode and is false conditional on the episode.** An investor who meets 1987 first sees
the overlay add two points of loss.

**The 1929-32 arm required rebuilding the trend leg.** Dropping the outer volatility target
moves its start to 1929-07 and gives 1,151 months; the raw leg carries 6.27% volatility
against the published leg's 12.46%, so weights are multiplied by 1.99 to match the risk
contribution. That factor is a single full-sample constant, look-ahead **in level only** —
it changes no sign and no date and cannot manufacture a drawdown result, but the growth
figures below are not out-of-sample.

| `w` | geometric | max drawdown | under water | 1929-32 peak-to-trough |
| ---: | ---: | ---: | ---: | ---: |
| 0.00 | 9.62% | **−83.65%** | 184 mo | −82.77% |
| 0.30 | 11.46% | −82.01% | 164 mo | −80.87% |
| 1.00 | 15.22% | −78.08% | 77 mo | −76.17% |
| 2.00 | 19.20% | −72.70% | 74 mo | −69.37% |

**The flat-drawdown claim survives its hardest test and the baseline does not.** Over the
window that contains 1929-32, adding overlay notional *monotonically reduces* maximum
drawdown, from −83.65% to −72.70% at 3.0× gross. **But the level is −83.65%, not −50.3%**,
so the recommendation's own drawdown budget is set by a number this page states in §2 and
§7 does not use.

### 9.3 The assumption §5a never varied

`stress_crisis_correlation` forces trend's correlation to equity to a target **inside equity
drawdowns only** — months where equity sits ≥10% below its running peak, 469 of 1,091 — by
a rotation that preserves the crisis-window mean and volatility of the trend leg exactly.
So only co-movement changes.

| crisis `rho` | full-sample `rho` | `w = 0.30` max DD | `w = 1.00` max DD | `w = 0.30` geometric |
| ---: | ---: | ---: | ---: | ---: |
| −0.20 (measured region) | +0.018 | −49.48% | −50.02% | 12.99% |
| 0.00 | +0.127 | −50.87% | −54.39% | 12.91% |
| **+0.30** | +0.292 | **−52.86%** | **−60.31%** | 12.80% |
| +0.60 | +0.457 | −54.76% | −65.54% | 12.69% |
| +0.90 | +0.621 | −56.53% | −70.12% | 12.58% |

And with the trend leg additionally earning **zero** inside those months — the plan's
"simultaneous loss in both sides of a return stack", against an unlevered base at 11.13%:

| crisis `rho` | `w = 0.30` max DD | `w = 1.00` max DD | `w = 0.30` geometric |
| ---: | ---: | ---: | ---: |
| 0.00 | −51.55% | −57.51% | 11.97% |
| **+0.30** | **−53.53%** | −62.37% | 11.86% |
| +0.90 | −57.15% | −71.58% | 11.64% |

**This is the condition under which the recommendation is wrong, and it is the only one
that breaks the drawdown argument cleanly.** A crisis-conditional correlation of +0.30 —
which is a *full-sample* correlation of only +0.29, well inside what §5a treats as
survivable — turns the flat drawdown into a 3.6 pp deeper one at the recommended weight
and an 11 pp deeper one at 1.0×. **At +0.30 crisis correlation and a zero crisis return
the overlay still adds 0.73 pp/yr of growth and costs 3.2 pp of drawdown.** That is a
different trade from the one §7 describes, and a reader who accepted §7 because the
drawdown was flat has not agreed to it.

**Note what did not break it.** Correlation stress alone never turns the growth gap
negative at 30% notional — the geometric return falls only from 12.99% to 12.58% across
the entire range. §5a's ordering holds: correlation is a drawdown risk, not a return risk.

### 9.4 The named failure modes, with a probability or a reason there is none

**Forced deleveraging inside the stacked fund.** A drawdown-control mandate that cuts the
overlay to zero when the fund's own NAV falls `trigger` below its peak and restores it only
at a new high. The state variable is the stacked fund's own path, so the constraint is
endogenous.

| trigger | restore at | months cut | geometric | max DD | growth cost | drawdown change |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| −15% | prior peak | 350 of 1,091 | 12.46% | −52.26% | **−0.53 pp/yr** | **−2.86 pp** |
| −20% | prior peak | 282 | 12.59% | −52.26% | −0.41 | −2.86 |
| −20% | 90% of peak | 225 | 12.70% | −52.26% | −0.29 | −2.86 |
| −30% | prior peak | 174 | 12.80% | −51.33% | −0.19 | −1.93 |

**Risk control applied to the stack makes both the return and the drawdown worse.** It cuts
the diversifier after the loss and restores it after the recovery, which is exactly
backwards, and it costs 0.19–0.53 pp/yr *and* 1.9–2.9 pp of drawdown. **Probability: this
is a property of the fund's stated mandate, not a random event.** It is a due-diligence
question — does the wrapper carry a drawdown-triggered de-risking rule — with a yes/no
answer, and it should be asked before the fund is bought.

**Simultaneous loss in both legs**, measured over 1,091 months:

| | |
| --- | ---: |
| `P`(equity loses) | 0.389 |
| `P`(trend loses) | 0.405 |
| **`P`(both lose in the same month)** | **0.192** |
| independence benchmark | 0.157 |
| Gaussian-copula benchmark at the measured correlation | 0.159 |
| **lift over independence** | **1.22×** |
| `P`(trend loses \| equity in its worst decile) | 0.427 |
| worst single month, both legs summed | −34.66% |

**Both legs lose together in one month in five, 22% more often than independence and 21%
more often than a Gaussian copula at the measured correlation predicts.** That excess is
tail dependence the correlation does not carry, and it is the number to hold in mind rather
than the −0.07: **a correlation of −0.07 does not mean the legs rarely lose together.**

**Fund closure.** The only cohort this repository has measured is
[Experiment 012](live-managed-futures.md)'s: **13 of the 25 managed-futures funds filing at
2019-07 had stopped filing by 2025-12.** Under a constant hazard with a Clopper-Pearson
interval on the cohort proportion:

| | |
| --- | ---: |
| annual hazard | **10.7%** `[5.6%, 17.9%]` |
| `P`(the fund held closes within 5 years) | **43.1%** `[25.1%, 62.6%]` |
| `P`(within 10 years) | 67.7% `[43.9%, 86.0%]` |
| `P`(within 20 years) | **89.5%** `[68.5%, 98.1%]` |

Two things weaken it in opposite directions and both are stated rather than netted. Fund
mortality is front-loaded, so a constant rate **understates** the first years and overstates
the later ones. And Experiment 012's own attrition figure is a **lower bound** twice over,
because a fund that both launched and died inside the window appears in neither census.
**Consequence: closure is not a tail risk. It is the modal outcome over a twenty-year
hold**, and the recommendation must name a successor or accept a forced transition.

**Methodology change: not estimated, and here is why.** N-PORT records returns and net
assets, not prospectus amendments, so a fund that stays open and changes its leverage
target, its trend model or its sub-adviser produces **no observable event in any census
this repository holds**. The thirteen capital-efficient series are all younger than six
years, so there is no cohort to measure a rate on at all. The probability is not small and
it is not estimable here. **That is a reason to prefer a monitorable rule to a point
estimate**, and §5b's boundary table is that rule.

**Five-year manager underperformance, against the investor's stated five-year review.**
Circular block bootstrap of paired 60-month windows.

| horizon | vs **leverage-matched** | vs unlevered |
| --- | ---: | ---: |
| 3 years | `P`(gap < 0) **32.8%**, worst −7.63 | 19.9%, worst −4.88 |
| **5 years** | `P`(gap < 0) **23.8%**, worst −4.48 | 12.9%, worst −2.89 |
| 10 years | 13.2%, worst −2.64 | 5.1%, worst −1.65 |

**The MDE at five years is 3.84 pp/yr against a full-sample gap of +1.50.** So a five-year
review cannot distinguish this overlay from nothing even when it is working: the instrument
the investor plans to use has a resolution floor two and a half times the effect it is
looking for. **The two columns are two claims and are never added.** The leverage-matched
gap is invariant to rescaling the benchmark, so "versus equity" and "versus equity levered
1.30×" are the *same number*, not two observations — a defect this work found in its own
first draft and pinned with a test.

**And the review does not predict.** Over 972 overlapping windows, 25.8% of five-year
reviews show the overlay behind; the next five years after a bad review average **+0.44
pp/yr** and after a good review **+1.24 pp/yr**, both against an MDE of 1.11 on the full
monthly difference. The windows overlap heavily so the difference has no interval, but the
sign is the wrong way for the reviewer: **a bad five-year review is followed by a positive
gap, so acting on it is selling after bad luck.**

### 9.5 Removing the strongest episodes

The plan's "test removing" clause, on the leverage-matched gap. Full sample **+1.50 pp/yr**.

| removed | n | gap | change |
| --- | ---: | ---: | ---: |
| the 1970s | 120 | +1.21 | **−0.29** |
| the 2000s | 120 | +1.27 | −0.23 |
| 1973-74 | 24 | +1.29 | −0.21 |
| 2008-09 GFC | 16 | +1.34 | −0.16 |
| 2000-02 dotcom | 30 | +1.38 | −0.12 |
| the 2010s | 120 | +1.73 | +0.23 |

**No single episode carries the result.** The most damaging removal is the entire 1970s and
it costs 0.29 pp/yr; the strongest single crisis costs 0.21. The gap stays above +1.2 pp/yr
under every removal tested, which is the one attack in this section the overlay passes
outright.

---

## Verified, assumed, open

**Verified.** The funding-rule identity and its 12% share of the two trend results, both
derived and tested. The levered ladder against this repository's own published figures at
`L = 1.0`. Credit and treasury as one engine at +0.83. Treasury's Sharpe of 0.08 before
1985. Trend's positive contribution in four structurally different drawdowns. **§7's
ladder, reproduced from the pinned sources** on geometric return, maximum drawdown and time
under water at every rung; its volatilities and Sharpe ratios reproduce only to 0.3%
relative and 0.002 respectively, and the residual is unexplained because the script that
produced them is not in Git.

**Assumed.** A 1.45%/yr all-in cost on trend notional and a 60 bp borrow spread, neither
verified against a filing on this page. The 25% and 50% overlay weights, and the 1985 start,
were chosen **after** the data was seen — this page is `exploratory` throughout and no
specification was frozen before its numbers were examined. **§5b's prior**: every centre is
one of this page's own figures but every *scale* and every copula entry was chosen, which
is why every number computed from it is reported beside the same number under an
independence copula. **§9's constant closure hazard**, on a cohort of 25 whose attrition is
a lower bound twice over. **§9.2's 1929 arm**, whose trend leg is rescaled by a single
full-sample constant.

**Open, and each of these could reverse a conclusion.**

1. **The trend evidence rests on an AQR vendor series that states no fee,
   transaction-cost, slippage or financing basis anywhere** and is reconstructed on every
   update. **Partly closed, and in the unexpected direction.**
   [Experiment 012](live-managed-futures.md) rebuilds the leg from 46 live funds' net
   N-PORT returns and finds the vendor series **−2.62 pp/yr behind them** at matched
   volatility over 2019–2025, `[−10.91, +5.68]`. What remains open is the period that
   matters: the vendor series earned +16.09%/yr over 1985–2011, and no fund return exists
   before 2019 to price that.
2. **JST returns are local currency.** A USD investor holding ex-US equity also bears FX,
   which is not modelled here, and equal-weight ex-US is not directly investable.
3. **1985–2025 is the most favourable forty years available** for both equities and bonds.
4. **No experiment here holds a tax lot**, so no figure prices a realisation.
5. **The crisis-conditional correlation is unmeasured going forward and is the one input
   that decides §7.** §9.3 shows what a +0.30 crisis correlation costs; nothing here
   estimates how likely it is, and the mechanism that would produce it — crowding into the
   same trend positions through the same wrappers — is precisely the mechanism a
   1,091-month backtest of an independently constructed series cannot observe.
6. **Methodology change inside a live fund is not estimable from anything held here**, and
   §9.4 says so rather than substituting the closure hazard for it.

**Reproducibility.** Every source is cached, sha256-pinned and manifested under
`research/data-manifests/`. The closed forms regenerate from
`portfolio_edge.studies.overlay_growth`, `portfolio_edge.studies.overlay_stress` and
`portfolio_edge.studies.equity_share` and are pinned by tests needing no market data.
§§5b and 9 regenerate with `uv run python -m portfolio_edge.studies.overlay_stress`, seed
20260816 throughout: 40,000 prior draws, 4,000 block-bootstrap resamples at 24-month
blocks. **The panel computations in §§3–6 and §9 were run as scoping scripts and are not
yet an experiment** — that is the gap a frozen specification must close before any of it
informs a decision.

---

## Consequence for this repository

0. **The 7.7 pp/yr survivorship-and-backfill haircut this page applies to the vendor
   series is not supported over the only window where it can be measured — and the sign
   is the other way.** Regressing the vendor series on 46 live funds over the same 78
   months gives the vendor an alpha of **−1.36 pp/yr** (*t* = −0.39) and a
   volatility-matched difference of **−2.62 pp/yr, 95% CI [−10.91, +5.68]**. **+7.7 sits
   above that interval.** Three things this does not license, and they are the reason the
   haircut is retained rather than dropped: the measurable window is 2019–2025 while the
   haircut is applied to a mean living in 1985–2011, where no fund return exists; the
   7.7 bound was measured on hedge-fund CTA *databases*, not on registered funds; and the
   vendor's 12.11 pp/yr post-publication decay is untouched by any of it.
1. **The zero-leverage rule's cost is now a number, not an assumption**, and
   [decision 0004](../decisions/0004-no-sleeve-promoted.md) records that its block on step 7
   is circular for that reason. **Neither block is lifted here.**
2. **Any future marginal-sleeve experiment must state its funding rule**, because the rule
   is worth more than the sleeve.
3. **Global diversification is a distributional argument, not a return argument**, and any
   page that states it must carry the USD counter-evidence in the same breath.
4. **A trend sleeve is a risk-reduction claim, not a return claim**, and must be judged on
   mechanism rather than on relative performance.
5. **Credit is rejected as a separate engine** (it correlates +0.835 with treasuries and is
   the same engine), and **the alternative risk premia are rejected on cost**.
   **Commodities are not rejected — they pass admission and are dominated**, at roughly a
   fifth of trend's margin and with unpriced roll costs in the only series held.
   **Gold is in the same position and for a better-measured reason**: identical Sharpe to
   commodities on the 1985-2025 window at a correlation of −0.09 rather than +0.29, a
   crisis-conditional correlation of at worst **+0.084** against the **+0.20** that breaks
   conclusion 7, a cost side that is a published fee rather than an unpriced roll, a
   **0.20%** overlay wrapper — and a marginal growth under pro-rata funding of **+0.04 to
   −0.42 pp/yr** against a 0.30 bar. **It passes admission, it is dominated, and it is not
   promoted.** §3a.
6. **A univariate stress table may not be quoted as a worst case again.** §5b measures what
   it costs: the failure rate is almost unchanged and the fifth percentile is 30% worse.
   Any future stress must vary its axes jointly and state the copula.
7. **Maximum drawdown must be reported with a resampled interval or not at all.** The
   ±10 pp interval in §9.1 is wider than every difference §7's ladder invites a reader to
   compare. The same rule the resolution table already imposes on means now applies to the
   one order statistic this repository's recommendation rests on.
8. **The recommendation stands, with three monitorable falsifiers rather than one.** Hold
   it while **(a)** the forward trend excess return stays above ~2%/yr gross, **(b)** the
   correlation to equity *inside equity drawdowns* stays below about +0.20, and **(c)** the
   wrapper carries no drawdown-triggered de-risking rule. **The review interval must not be
   five years**: §9.4 shows five years cannot resolve the effect and that a bad five-year
   review predicts a good next five. Review on (a)–(c), not on realised performance.
