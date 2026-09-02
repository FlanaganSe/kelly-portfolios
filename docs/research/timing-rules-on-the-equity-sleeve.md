# Timing rules on the equity sleeve: the drawdown is real, the return is not, and it is a bet already held

**Question.** Should this investor apply a trend or timing rule — the 10-month/200-day
moving average, 12-month absolute momentum, or dual momentum — to **their own equity
holdings**? That is a different question from the one
[trend as a diversifying sleeve](trend-marginal-value.md) answers, and it has different
costs: a long/flat switch on the base portfolio realises the base portfolio's gains every
time it fires, which a financed long/short overlay never does.

**Decision it informs.** Whether to add an equity timing rule, at what weight, in which of
the investor's three account thirds — and whether doing so duplicates the ~30% stacked
managed-futures position already in the candidate portfolio.

**Out of scope.** Whether to hold a trend *sleeve* ([trend](trend-marginal-value.md),
[live funds](live-managed-futures.md)); which managed-futures product to buy
([the recommendation](portfolio-recommendation.md)); rebalancing policy
([rebalancing](rebalancing-policy.md)).

`as of 2026-08-22`. **`exploratory`** — a study module, not a registered experiment. No
specification was frozen before these numbers were seen, so nothing here may support a
promoted claim. Code:
[`studies/timing_rules.py`](../../research/src/portfolio_edge/studies/timing_rules.py) and
[`studies/_timing_rules_tables.py`](../../research/src/portfolio_edge/studies/_timing_rules_tables.py).
Regenerate every table below with:

```sh
cd research && uv run python -m portfolio_edge.studies.timing_rules
```

The same signal on daily-reset 2x and 3x funds (Gayed's *Leverage for the Long Run*) and the
static 55/45 UPRO/TMF mix are measured in [leveraged ETFs and timing rules](leveraged-etfs-and-timing-rules.md), Experiment 021.

---

## Conclusion

**Do not apply a timing rule to the equity sleeve. Confidence: moderate-to-high on the
recommendation, and the reason is not that the rule fails — it is that three of its four
components are already owned more cheaply.**

1. **The return claim is `unresolved` and fails deflation.** Over 1,190 months the
   10-month SMA beat a **beta-matched** control by **+0.74 pp/yr**, HAC *t* = 0.69,
   95% `[−1.38, +2.87]`, against an **MDE₈₀ of 3.03 pp/yr**. The effect is a quarter of
   the smallest one a century of monthly US data can detect. Deflated against the family
   it was selected from, the probability its true active Sharpe beats the best-of-N
   zero-skill threshold is **0.33 at 14.8 effective trials and 0.04 at 10,000**. Across
   all 46 rules, Hansen's SPA against the beta-matched control returns **p = 0.267** on
   the full sample and **p = 0.585** post-1990.
2. **The drawdown claim is large, robust and the only thing here that clears its own
   floor.** Maximum drawdown **−43.1% against the matched control's −71.6%** and
   buy-and-hold's −83.7%; worst twelve months **−28.9% against −52.8% and −65.7%**; months
   under water **82 against 164 and 184**. Repeated in developed ex-US, emerging and the
   1871–1926 sample. This is a mechanical property of truncating the left tail, not an
   estimated premium, which is why it survives when the mean does not.
3. **Most of the published edge is a data artefact.** On the *same* 1,124 months, the rule
   reads **+0.88 pp/yr (t = 0.78)** on Ken French's month-end total returns and
   **+2.71 pp/yr (t = 2.87)** on Shiller's, whose price is a **monthly average of daily
   closes**. Averaging triples the apparent edge, because it manufactures the
   autocorrelation the rule trades — AR(1) **0.103 against 0.274**. Any long-history
   moving-average result built on Shiller's file is measuring the sampling convention.
4. **After tax in the taxable third the rule is indefensible.** In a Roth it trails
   buy-and-hold by **1.04 pp/yr**; in a top-bracket taxable account with a basis step-up
   it trails by **2.96**. The **1.92 pp/yr difference is the tax cost of the rule itself**,
   two and a half times the entire pre-tax gap it was hired to produce. It realises
   **$16.04 of long-term and $2.44 of short-term gain per dollar invested** over 36 years
   and pays **$5.15 of tax against buy-and-hold's $1.53**.
5. **It is substantially the bet already held.** Regressed on AQR's TSMOM index, the
   12-month rule's active return loads **+0.232** with **R² = 0.145**; against the index's
   *equity* leg alone, **ρ = 0.566, R² = 0.321**. Its alpha over that index is **negative**
   (−1.38 to −2.16 pp/yr, not significant). The ~30% stacked managed-futures position
   supplies the same signal across roughly fifty markets, long and short, financed rather
   than funded by selling, and inside a wrapper whose distribution tax drag is 0.32 pp/yr.
6. **The behavioural cost is the decisive argument and no backtest shows it.**
   **58 of 73 exits (79.5%) lost money.** The worst run is **twelve consecutive losing
   exits, 1948-03 to 1960-11**; post-1990 it is **nine consecutive losing exits,
   2010-07 to 2020-05, costing 56.8% of a fully invested position**. And the rule's wealth
   relative to buy-and-hold **peaked in June 1932 and has been below that peak for every
   one of the 1,128 months since**. Post-1990 the relative peak is **February 2009** and
   the rule has been behind for **208 months**.

**What would change this.** A pre-registered design with resolution — the pooled
cross-country test below is the only one here that has any — or an investor who does not
already hold trend, has no taxable account, and states a drawdown constraint the equity
share cannot meet.

---

## 1. What the rule does

US, Ken French `Mkt-RF + RF`, 1926-07…2026-06, 1,200 months. One-way cost 10 bp, charged
inside the rule, so a whipsaw pays 20 bp. `+1m` delays execution by one month.

| rule | months | in mkt | switch/decade | geo total | vol | Sharpe | max DD | under water | worst 12m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **sma-10** | 1190 | 0.730 | 14.7 | **9.64** | 12.55 | **0.541** | **−43.1** | **82** | **−28.9** |
| — control at 0.730 beta | 1190 | 0.730 | 0.0 | 8.72 | 13.47 | 0.449 | −71.6 | 164 | −52.8 |
| **absolute_momentum-12** | 1187 | 0.706 | 8.7 | **9.78** | 12.62 | **0.549** | −44.5 | 95 | −31.8 |
| — control at 0.706 beta | 1187 | 0.706 | 0.0 | 8.51 | 13.02 | 0.445 | −70.2 | 164 | −51.5 |
| sma-10 `+1m` | 1189 | 0.730 | 14.7 | 9.31 | 12.97 | 0.504 | −50.5 | 87 | −31.8 |
| absolute_momentum-12 `+1m` | 1186 | 0.706 | 8.7 | 8.53 | 12.92 | 0.450 | −39.9 | 92 | −31.0 |
| buy and hold 100% | 1200 | 1.000 | 0.0 | 10.37 | 18.38 | 0.454 | −83.7 | 184 | −65.7 |

**The control is the whole argument.** A rule out of the market 27% of the time carries
27% less beta. Scored against a fully invested portfolio it is credited for risk it
declined to take; scored against a constant-weight portfolio at its own average exposure —
whose excess return is exactly `w × equity excess`, no rebalancing term — the credit
disappears. The rule *loses* 0.73 pp/yr to buy-and-hold and *gains* 0.92 against the
matched control. Both are true and only the second is a result.

### The gap, and the floor it has to clear

| rule | months | gap pp/yr | HAC *t* | 95% HAC | **MDE₈₀** | block | block 95% |
| --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| sma-10 | 1190 | **+0.74** | 0.69 | `[−1.38, +2.87]` | **3.03** | 2.3 | `[−1.49, +2.80]` |
| absolute_momentum-12 | 1187 | +1.13 | 1.11 | `[−0.87, +3.14]` | 2.86 | 3.1 | `[−0.94, +3.15]` |
| sma-10 `+1m` | 1189 | +0.53 | 0.47 | `[−1.65, +2.71]` | 3.12 | 1.4 | `[−1.63, +2.55]` |
| absolute_momentum-12 `+1m` | 1186 | **+0.04** | 0.04 | `[−2.07, +2.15]` | 3.01 | 3.6 | `[−2.09, +2.17]` |

**A one-month execution delay removes the entire measured edge of the momentum rule**
(+1.13 → +0.04) and a third of the SMA's. Monthly data cannot resolve anything finer, so
the true cost of trading after the signal sits somewhere inside that bracket and the
`+1m` row is the conservative bound rather than a scenario.

**Effective sample size is not 1,190.** The rule makes **73 round trips in 99 years** —
about one decision every sixteen months. That is the number of independent bets, and it is
why a century of data yields a 3 pp/yr floor.

**Costs are not the explanation and must not be offered as one.** Zero cost gives +0.89
and 50 bp one-way gives +0.16; the whole cost grid moves the answer by less than one
standard error. What kills it is the control, not the friction.

| one-way cost | 0 bp | 5 bp | 10 bp | 50 bp |
| --- | ---: | ---: | ---: | ---: |
| gap pp/yr | +0.89 | +0.82 | +0.74 | +0.16 |

**Pre-1975 this backtest is not implementable at any cost.** US commissions were fixed by
the exchange until May 1975 and no index fund existed to trade before 1971. Two-thirds of
the sample is a paper exercise.

### Where the effect lives

| window | months | in mkt | gap pp/yr | HAC *t* | MDE₈₀ | rule geo | control geo | rule maxDD | control maxDD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1927–1945 | 224 | 0.638 | +1.86 | 0.47 | 11.15 | 7.43 | 5.20 | −43.1 | −66.0 |
| 1946–1969 | 288 | 0.757 | +0.23 | 0.21 | 3.19 | 9.69 | 9.53 | −20.7 | −18.7 |
| 1970–1989 | 240 | 0.704 | +0.93 | 0.50 | 5.21 | 11.41 | 10.55 | −24.5 | −32.7 |
| 1990–2007 | 216 | 0.778 | +0.69 | 0.42 | 4.57 | 10.10 | 9.37 | −17.3 | −35.7 |
| **2008–2026** | 222 | 0.770 | **+0.04** | 0.02 | 6.70 | 9.50 | 9.25 | −18.1 | −37.1 |
| pre-1990 | 752 | 0.705 | +0.95 | 0.64 | 4.14 | 9.56 | 8.44 | −43.1 | −70.1 |
| post-1990 | 438 | 0.774 | +0.35 | 0.24 | 4.09 | 9.80 | 9.32 | −18.1 | −41.1 |
| **post-2007 (Faber)** | 230 | 0.778 | **−0.07** | −0.03 | 6.50 | 9.18 | 9.05 | −18.1 | −41.2 |

**The post-publication reading is −0.07 pp/yr against a 6.50 pp/yr floor.** That is not a
rejection; 230 months cannot reject anything. It is a *coincidence of two facts* — the
point estimate has gone to zero, and the design that would prove it cannot. Read the
drawdown columns instead: they are stable in every era, which the mean is not.

---

## 2. The deflation, which is where public versions of this backtest stop

The declared family is both signals at every lookback from 2 to 24 months — **46 rules**,
enumerated in [`rule_grid`](../../research/src/portfolio_edge/studies/timing_rules.py) so
that the *selection* can be priced rather than tuned. The true search over US equity
history is very much larger, so every trial count here is a **lower bound** and every
deflated significance an **upper bound on the evidence**.

**The mis-specified test first, because it is the one usually run.** On the rule's raw
Sharpe ratio the deflated Sharpe reads **1.0000 at the effective trial count and 0.9965 at
10,000 trials** — it passes handsomely. It is meaningless. Every one of the 46 trials is
long the equity index 60–80% of the time, so every trial contains the equity risk premium
and the "zero-skill" null is false by construction. Consistently, White's reality check on
`rule less bills` returns **p = 0.0005**, which establishes that equities beat bills.

**The test that answers the question** is the same arithmetic on the **beta-matched active
return**, the only series with the equity premium taken out of it. Full sample, 1,176
common months, trial dispersion 0.0185/month, mean off-diagonal ρ = 0.694 → **14.8
effective independent trials of 46**.

| candidate | active SR (ann.) | N trials | SR\* (ann.) | **DSR** |
| --- | ---: | ---: | ---: | ---: |
| **sma-10** | 0.067 | 14.8 | 0.113 | **0.325** |
| | | 100 | 0.162 | 0.176 |
| | | 1,000 | 0.209 | 0.083 |
| | | 10,000 | 0.248 | **0.039** |
| absolute_momentum-12 | 0.109 | 14.8 | 0.113 | 0.483 |
| | | 10,000 | 0.248 | 0.089 |
| best in grid (momentum-10) | 0.174 | 14.8 | 0.113 | 0.722 |
| | | 10,000 | 0.248 | 0.237 |

**The rule fails deflation at its own grid's effective trial count**, before any allowance
for the thousands of rules the literature has searched. Post-1990 it is the same picture:
active Sharpe 0.086, DSR **0.399** at 15.2 trials and **0.126** at 10,000.

Across all 46 rules jointly:

| test | full sample | post-1990 |
| --- | ---: | ---: |
| White reality check, rule less beta-matched control | **p = 0.248** | **p = 0.571** |
| Hansen SPA (consistent recentring), same | **p = 0.267** | **p = 0.585** |
| White / Hansen, rule less **bills** | p = 0.0005 | p = 0.0005 |

`N_trials` is an assumption, not a measurement, and
[`effective_number_of_trials`](../../research/src/portfolio_edge/inference/deflated_sharpe.py)
carries an **UNVERIFIED** marker on its interpolation. The conclusion does not turn on it:
the rule fails at the most generous count available.

### The averaged-price artefact

The same rule, the same 1,124 months, two US price series.

| panel | months | AR(1) of the monthly return | in mkt | gap pp/yr | HAC *t* |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ken French, month-end total returns | 1124 | **0.103** | 0.728 | **+0.88** | 0.78 |
| Shiller, monthly **average** of daily closes | 1124 | **0.274** | 0.723 | **+2.71** | **2.87** |

Shiller's own documentation states that `P` is the monthly average. Averaging suppresses
volatility and induces positive serial correlation — precisely the property a
moving-average rule monetises — and it turns a null into a *t* of 2.87. The 1871–1926
extension on that file reads a Sharpe of 0.600 against a matched control's 0.318 and a
max drawdown of −12.8% against −22.9%; **it is not evidence, and the number of published
"150 years of trend following" results that rest on it is the reason this section exists.**

---

## 3. What it costs in reality

### Taxes, by account third

Simulated on the realised 1990–2026 path with an average-cost basis, a §1222 holding-period
boundary at *more than* twelve months, loss carryforwards against later capital gains,
dividends reinvested and raising basis, and tax paid out of the account. A 1.75% dividend
yield; the 1.25% arm moves every figure by under 0.15 pp/yr.

Growth is annualised log growth of one dollar; the last column is the shortfall against
buy-and-hold **in the same account**.

| account | portfolio | terminal \$1 | tax paid | growth %/yr | vs buy-hold |
| --- | --- | ---: | ---: | ---: | ---: |
| Roth / traditional | timing rule | 36.70 | 0.00 | 10.10 | **−1.04** |
| | static blend, monthly rebalanced | 29.14 | 0.00 | 9.45 | −1.69 |
| | static blend, never rebalanced | 42.04 | 0.00 | 10.48 | −0.66 |
| | buy and hold 100% | 53.17 | 0.00 | 11.14 | 0.00 |
| taxable, top bracket, **step-up** | timing rule | 15.94 | **5.15** | 7.76 | **−2.96** |
| | static blend, monthly rebalanced | 19.38 | 2.57 | 8.31 | −2.42 |
| | static blend, never rebalanced | 36.19 | 1.30 | 10.06 | −0.67 |
| | buy and hold 100% | 45.89 | 1.53 | 10.73 | 0.00 |
| taxable, top bracket, liquidate | timing rule | 15.68 | 5.40 | 7.72 | −2.36 |
| | buy and hold 100% | 36.37 | 11.05 | 10.08 | 0.00 |
| taxable, upper-middle, step-up | timing rule | 22.00 | 3.97 | 8.67 | **−2.21** |
| | static blend, never rebalanced | 38.25 | 0.85 | 10.22 | −0.66 |
| | buy and hold 100% | 48.46 | 1.00 | 10.88 | 0.00 |
| taxable, upper-middle, liquidate | timing rule | 21.80 | 4.18 | 8.64 | −1.85 |
| | buy and hold 100% | 42.19 | 7.27 | 10.49 | 0.00 |

**Read the difference between the first and second blocks, not the levels.** The rule's
shortfall against buy-and-hold widens from **−1.04 pp/yr sheltered to −2.96 taxable at the
top bracket under a step-up**: the **tax cost of the rule is 1.92 pp/yr**, against a
pre-tax beta-matched gap of +0.74 whose interval includes zero. At the upper-middle bracket
the tax cost is 1.17. Over 36 years it realises **\$16.04 of long-term and \$2.44 of
short-term gain per dollar** and hands over **\$5.15 of tax where buy-and-hold hands over
\$1.53**.

Three modelling choices, each named with its direction. Losses carry forward against
capital gains only — the §1211(b) \$3,000 ordinary offset and §1222 character netting are
omitted, both of which would *improve* the rule's figure. Dividend tax is paid in the month
received rather than at year end, worth under a basis point a year. And the basis is
average cost, which is exact for a rule that sells all or nothing.

**The account allocation does not rescue it.** With a third of the portfolio taxable, the
rule's blended cost is roughly `⅔ × 1.04 + ⅓ × 2.96 ≈ 1.68 pp/yr` of shortfall against
buy-and-hold, of which about 0.64 is purely tax. Confining the rule to the two sheltered
thirds halves the tax but also halves the drawdown protection, which is the only thing
being bought.

### The behavioural cost

The rule's exits scored against **staying fully invested** — which is what the investor
actually experiences, and is a different accounting from the beta-matched gap.

| | full sample, 1926–2026 | post-1990 |
| --- | ---: | ---: |
| exits | 73 | 25 |
| of which lost money | **58 (79.5%)** | **21 (84.0%)** |
| median exit length | 2 months | 2 months |
| sum of exit gains | **−1.383** | −0.557 |
| from the best three exits | **+1.215** | +0.719 |
| from every other exit | **−2.599** | −1.277 |
| worst run of consecutive losing exits | **12**, 1948-03…1960-11 | **9**, 2010-07…2020-05 |
| cost of that run | −0.508 | **−0.568** |

The five exits that paid for the whole record: **1929-11…1932-08 (+0.626)**,
2008-01…2009-05 (+0.348), 1937-09…1938-06 (+0.242), 1973-12…1975-01 (+0.236),
2000-11…2001-12 (+0.226). The five worst: **1933-03…1933-04 (−0.433)**, 1940-06…1940-10
(−0.189), 1939-09 (−0.171), 1998-09…1998-10 (−0.138), 1987-01 (−0.127).

**Holdability, measured.** Drawdown of the rule's wealth divided by its control's:

| against | max shortfall | months behind | from | to |
| --- | ---: | ---: | --- | --- |
| beta-matched control, 1926–2026 | −67.3% | **1128** | 1932-06 | 1941-10 |
| buy and hold 100%, 1926–2026 | −89.3% | **1128** | 1932-06 | 2000-07 |
| beta-matched control, post-1990 | −38.8% | **208** | 2009-02 | 2026-04 |
| buy and hold 100%, post-1990 | −62.4% | **208** | 2009-02 | 2026-05 |

**The rule's entire lifetime advantage was banked by June 1932 and it has not made a new
relative high in the 94 years since.** Post-1990 the relative high is February 2009 and the
rule has trailed for seventeen straight years. That is the record an investor would have
to sit through while continuing to follow it, and no Sharpe ratio contains it.

---

## 4. Out of sample

| panel | rule | months | in mkt | gap pp/yr | HAC *t* | MDE₈₀ | rule maxDD | control maxDD |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Developed ex-US, 1990-07→ | sma-10 | 422 | 0.682 | +0.55 | 0.36 | 4.26 | −25.3 | −41.6 |
| Developed ex-US | momentum-12 | 420 | 0.607 | +0.77 | 0.49 | 4.46 | −27.4 | −37.7 |
| Emerging, 1989-07→ | sma-10 | 434 | 0.654 | **+3.16** | 1.66 | 5.34 | −31.0 | −44.4 |
| Emerging | momentum-12 | 432 | 0.653 | +0.66 | 0.32 | 5.72 | −34.3 | −44.3 |

Emerging is the strongest single cell in this page and it is **one cell of many, below its
own floor, and not adjusted for having been looked at**.

**Dual momentum (Antonacci's GEM)**, US and developed ex-US, 1990-07…2026-06: geometric
10.03%, volatility 12.42%, Sharpe 0.634, max drawdown −23.6%, 44 months under water,
against a beta-matched 50/50 control at 7.86%, 11.58%, 0.497, −44.3% and 62 months. The
gap is **+2.11 pp/yr, HAC *t* = 1.21, MDE₈₀ 4.87** — the largest point estimate here and
still less than half its detection floor. It also holds only US or only ex-US at any time,
so it concentrates rather than diversifies.

**The broadest evidence held: sixteen countries, Jorda-Schularick-Taylor annual,
1870–2020.** Annual data cannot carry a ten-month average, so the rule is one-year absolute
momentum against the country's own bill rate. German 1922–23 is dropped as hyperinflation
arithmetic, on the source's own documentation.

- mean gap **+1.01 pp/yr**, median +1.01, **positive in 12 of 16 countries**, cross-country
  SD 1.19 pp/yr. **The United States is one of the four negatives (−0.63).**
- Countries are not independent draws — 1929 and 2008 are in every column — so the pooled
  test is the honest one: the equal-weighted active return across live countries reads
  **+0.97 pp/yr over 148 years, HAC *t* = 2.74, MDE₈₀ 0.99 pp/yr**. **This is the only
  design on this page with meaningful resolution, and it does find an effect.** The
  estimate sits marginally below the 80%-power floor, so power against the effect actually
  found is roughly 70%.
- **At annual resolution the rule has a *deeper* maximum drawdown than its control in 9 of
  16 countries.** The drawdown benefit is a monthly-resolution phenomenon; sampled once a
  year the rule cannot get out in time and its lower average exposure does not compensate.
- JST is not investable: no fees, no spreads, no taxes, several series reconstructed from
  newspapers, exchange closures interpolated, and the index behind a country changes
  definition mid-sample.

**How to read the two halves.** The cross-country pooled test says the *signal* is not
nothing. Every US-specific, monthly, after-cost, after-tax test says the *implementation on
one equity book* does not clear its floor. Those are consistent, and the second is the one
the decision depends on.

---

## 5. Overlap with the managed-futures overlay already held

The candidate portfolio's ~30% stacked position supplies roughly 100% of trend notional per
dollar of capital ([capital efficiency](capital-efficiency-and-breadth.md)). Regressing the
timing rule's **beta-matched active return** on AQR's TSMOM index, 497 months 1985-01…2026-05:

| rule | trend series | ρ | β | HAC *t* on β | R² | α pp/yr | HAC *t* on α |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| sma-10 | TSMOM (all markets) | 0.315 | +0.208 | 4.48 | 0.099 | **−2.16** | −1.68 |
| sma-10 | TSMOM^EQ (equity leg only) | 0.362 | +0.108 | 4.68 | 0.131 | −1.24 | −1.06 |
| momentum-12 | TSMOM | 0.381 | +0.232 | 5.46 | 0.145 | **−1.87** | −1.48 |
| momentum-12 | **TSMOM^EQ** | **0.566** | +0.156 | 8.18 | **0.321** | −1.38 | −1.43 |

**Thirty-two per cent of the 12-month rule's active variance is the equity leg of the trend
index the investor already owns**, the loadings are significant at *t* = 4.5 to 8.2, and
**the residual alpha is negative in all four rows**. Once the overlay is held, the rule
adds nothing measurable and is priced as if it subtracts.

The concentration the investor may not see: the overlay applies the signal to ~50 markets,
long and short, at roughly 30% notional, financed rather than funded by selling. The equity
timing rule applies the *same family of signal* to one market, long-only, at a notional
swing of 0 to 100% of the equity book, funded by selling the book. It is a second and much
larger dose of the same bet, in the worse wrapper.

---

## 6. The honest alternative: four ways to buy the same drawdown

Common months 1985-01…2026-05, 497 months, pretax.

| construction | geo total | vol | Sharpe | max DD | under water | worst 12m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| equity 100% | 12.00 | 15.54 | 0.608 | −50.3 | 72 | −42.6 |
| **sma-10 timing rule** | 10.20 | 11.70 | 0.622 | **−24.5** | 42 | **−24.5** |
| static equity 0.73 + bills | 9.83 | 11.35 | 0.608 | −39.1 | 64 | −32.5 |
| equity 100% + 30% TSMOM, vendor gross | 16.12 | 15.69 | 0.836 | −45.5 | 40 | −38.4 |
| equity 0.73 + 30% TSMOM, vendor gross | 13.86 | 11.67 | **0.906** | −33.5 | **37** | −27.8 |
| equity 0.73 + 30% TSMOM less 7.7 pp/yr | 11.28 | 11.67 | 0.708 | −35.5 | 39 | −29.5 |
| equity 0.73 + 30% TSMOM at the live-fund mean | 10.72 | 11.67 | 0.664 | −36.0 | 41 | −29.9 |

**The two vendor-gross rows are not investable and are printed only so the haircut rows can
be read against them.** AQR's series states no fee, transaction-cost, slippage or financing
basis anywhere; the last two rows apply this repository's 7.7 pp/yr CTA bias scenario and,
separately, rescale the leg to the **+2.84%/yr the 46 live managed-futures funds actually
paid** over 2019–2025 ([live managed futures](live-managed-futures.md)).

Read the three comparable rows — the timing rule, the static blend, and the haircut overlay
— all at essentially the same volatility (11.35 to 11.70):

- **A lower equity share is the cheapest instrument and the weakest.** −39.1% for free, no
  tax, no signal, no discipline required.
- **The timing rule buys the deepest drawdown reduction of the three** (−24.5%) and the
  best worst-twelve-months (−24.5%), at +0.37 pp/yr over the static blend — before tax, and
  the tax is 1.2 to 1.9 pp/yr.
- **Even a heavily haircut trend overlay dominates it on return and Sharpe** (10.72 vs
  10.20; 0.664 vs 0.622) while giving up 11 points of drawdown depth.
- **Rebalancing is not a candidate.** It was tested and rejected on this repository's own
  data: every policy lost to buy-and-hold on growth and *every one had an equal or worse
  maximum drawdown* ([rebalancing](rebalancing-policy.md)). It does not buy drawdown
  reduction at any price.

---

## 7. The decision

**No timing rule on the equity sleeve, at any weight, in any account.**

| account third | verdict | why |
| --- | --- | --- |
| **taxable (~⅓)** | **no**, and this one is not close | 1.92 pp/yr of tax against a +0.74 pp/yr gap whose interval includes zero |
| **traditional (~⅓)** | **no** | tax-neutral, but the pre-tax gap fails deflation and duplicates the overlay |
| **Roth (~⅓)** | **no** | same, plus the Roth is the highest-value shelter and this is the lowest-value use of it |

The one place a timing rule would be defensible — a sheltered account, an investor with no
trend exposure, and a stated drawdown constraint that a lower equity share cannot meet —
does not describe this investor, who already holds ~30% of a product that runs the same
signal across fifty markets at a distribution tax drag of 0.32 pp/yr.

**If the underlying want is a shallower drawdown, buy it in this order.** (1) Lower the
equity share — free, tax-free, and it is what
[the equity share work](setting-the-equity-share.md) is for. (2) Keep the trend overlay
already held, sized on its own evidence and its own `unresolved` verdict. (3) Nothing else
on this page.

**And the investor's own condition is the one that settles it.** *"We have to have
confidence and understanding in them."* The understanding is available and it is the
problem: the rule's mechanism is truncating the left tail; its measured return advantage is
below the resolution of a century of data and fails deflation; its historical record is 58
losing exits out of 73 and 94 years without a new relative high. An investor who
understands that will not follow it through the ninth consecutive whipsaw, and a rule that
is abandoned at its worst moment is worse than never adopting it.

---

## Verified, assumed, open

**Verified.** Every figure above regenerates from
[`_timing_rules_tables.py`](../../research/src/portfolio_edge/studies/_timing_rules_tables.py)
against hash-pinned Ken French, Shiller, AQR and JST files under
`research/data-manifests/`. The construction, cost accounting, episode ledger, holding-period
boundary and loss carryforward are pinned by hand-computed fixtures in
`tests/unit/test_studies_timing_rules.py`, including a look-ahead test that perturbs every
future month and asserts the position does not move.

**Assumed.** A 10 bp one-way cost, a 1.75% dividend yield, US federal rates with no state
tax, and the trial counts fed to the deflated Sharpe ratio. Each is an argument with a
sensitivity, and none carries the conclusion. The 1985–2026 overlap and alternatives
sections inherit the AQR series' unstated cost basis.

**Open.**

1. **The one design with resolution is the cross-country pooled test, and it is annual,
   pretax and not investable.** A monthly multi-country panel with a real bill leg would be
   the informative next instrument. It does not exist here.
2. **Nothing is pre-registered.** The subperiod splits, the 46-rule grid and the emerging
   cell were all chosen after the full-sample result was known. Re-running does not fix it.
3. **The drawdown benefit is measured but never deflated.** No multiple-testing machinery
   here applies to a maximum drawdown, and the statistic has one observation per sample.
4. **The overlap in §5 is against a vendor index, not against the position actually
   held.** The stacked wrapper's own trend loading has since been measured from its filings
   — +0.681 [+0.406, +0.955] over 31 months
   ([comparability](loading-comparability-and-wrapper-exposure.md)) — so the substitution
   now has a known size of error rather than an unknown one: the index runs about a third
   hotter than the fund, on an interval too wide to pin that fraction down.

## Consequence for this repository

1. **A long/flat rule on the base portfolio and a financed long/short trend overlay are
   different constructions and must not share a verdict.** They share a signal and nothing
   else: funding rule, tax treatment, breadth and sign are all different.
   [`studies/timing_rules.py`](../../research/src/portfolio_edge/studies/timing_rules.py)
   is deliberately separate from
   [`studies/time_series_momentum.py`](../../research/src/portfolio_edge/studies/time_series_momentum.py).
2. **Shiller's `ie_data` may not be used for any rule that trades on serial correlation.**
   Measured here: it triples the apparent edge and moves *t* from 0.78 to 2.87. Recorded
   against the source in [the evidence base](evidence-base.md).
3. **A deflated Sharpe ratio computed on a long/flat rule's raw return is not a test.**
   The trials all contain the equity premium. Deflate the beta-matched active return or do
   not deflate.
4. **No decision record changes.** [Decision 0004](../decisions/0004-no-sleeve-promoted.md)
   stands and nothing here promotes anything; this is an `exploratory` study whose verdict
   on the return claim is **`unresolved`** by
   [decision 0010](../decisions/0010-bars-carry-a-reopening-condition.md)'s standard, and
   whose recommendation rests on the tax arithmetic, the overlap and the holdability
   record rather than on a rejected mean.
