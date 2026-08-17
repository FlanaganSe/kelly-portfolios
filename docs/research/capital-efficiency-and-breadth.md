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
3. **Breadth is one engine, not four.** Every alternative risk premium tested passes the
   *correlation* test and almost all fail the *cost* test. Post-publication gross returns
   of 0.3–1.0%/yr at 2–5% volatility do not survive a retail fee.
4. **Trend is the one engine that survives, and it survives as risk reduction rather than
   as return.** Its left-tail contribution is positive at every haircut tested, including
   one that turns its median contribution negative.
5. **Global versus US is unresolved, and the two datasets disagree in opposite
   directions.** In local currency over 150 years, global 60/40 beat US-only on drawdown
   and on return per unit of risk. **In USD over 1990–2025 it lost 1.57 pp/yr and drew down
   deeper.** The case for global equity is not that it raises expected return — on the only
   USD evidence here it does not — but that the US is the survivor and its record cannot be
   bought in advance. **An earlier draft of this page claimed global was the largest certain
   improvement available; building the frontier falsified that and the claim is withdrawn.**

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
| trend | 12.07% | 12.58% | 0.96 | −0.08 |

**Credit and treasury correlate +0.83 — they are one engine, not two.** Counting them
separately is the fake breadth `docs/the-plan.md` forbids.

### The window flatters, and by how much is measurable

| | full 1926-2025 | pre-1985 | 1985-2025 |
| --- | ---: | ---: | ---: |
| Treasury Sharpe | 0.27 | **0.08** | 0.47 |
| equity/treasury correlation | +0.08 | **+0.17** | −0.04 |
| Commodity Sharpe | 0.31 | 0.34 | 0.27 |
| equity/commodity correlation | +0.30 | +0.30 | +0.29 |

**The bond overlay's entire case is the post-1985 disinflation**, in both its return and its
correlation. Commodities are the stable one — and stably *correlated* at +0.30, which is
what disqualifies them once cost is charged.

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

### The candidate frontier

Same 426-month USD window. Trend is haircut by the repository's full **7.7 pp/yr** CTA bias
bound, so these are the pessimistic rows. `B2` levers the *global* base to each candidate's
volatility — the control the plan makes mandatory.

| | Candidate | geometric | volatility | Sharpe | max DD | under water | notional |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **B0** | 100% US | 10.98% | 15.16% | 0.594 | −50.3% | 72 mo | 1.00 |
| **B1/C1** | global 60/30/10 | 9.41% | 14.84% | 0.507 | −53.1% | 63 mo | 1.00 |
| **C2** | global + 15% trend | 9.76% | 14.61% | 0.535 | −51.8% | 62 mo | 1.15 |
| **C3** | global + 25% trend | 9.98% | 14.60% | **0.549** | −51.0% | 64 mo | 1.25 |
| **C4** | global + 50% trend | 10.44% | 15.02% | 0.566 | **−48.9%** | 65 mo | 1.50 |
| **B2** | global levered to C3's volatility | 9.32% | 14.60% | 0.508 | −52.4% | 63 mo | 0.98 |

**C3 beats its leverage-matched control on Sharpe by 0.041 at identical volatility**, which
is the test that separates breadth from beta, and it passes. The overlay contributes
**+0.57 pp/yr and 2.1 pp of drawdown** at the full bias haircut.

**And every candidate trails B0 on this window.** A reader who takes B0 as the benchmark
should conclude that nothing here beat 100% US equity over 1990–2025. That is true, it is
the window in which the US won, and it is exactly why B0 is not the only benchmark the plan
requires.

---

## Verified, assumed, open

**Verified.** The funding-rule identity and its 12% share of the two trend results, both
derived and tested. The levered ladder against this repository's own published figures at
`L = 1.0`. Credit and treasury as one engine at +0.83. Treasury's Sharpe of 0.08 before
1985. Trend's positive contribution in four structurally different drawdowns.

**Assumed.** A 1.45%/yr all-in cost on trend notional and a 60 bp borrow spread, neither
verified against a filing on this page. The 25% and 50% overlay weights, and the 1985 start,
were chosen **after** the data was seen — this page is `exploratory` throughout and no
specification was frozen before its numbers were examined.

**Open, and each of these could reverse a conclusion.**

1. **The trend evidence rests on an AQR vendor series that states no fee,
   transaction-cost, slippage or financing basis anywhere** and is reconstructed on every
   update. This repository bounds survivorship and backfill distortion on comparable CTA
   data at **7.7 pp/yr**, against a measured break-even near 9.9. That single uncertainty
   spans the entire result.
2. **JST returns are local currency.** A USD investor holding ex-US equity also bears FX,
   which is not modelled here, and equal-weight ex-US is not directly investable.
3. **1985–2025 is the most favourable forty years available** for both equities and bonds.
4. **No experiment here holds a tax lot**, so no figure prices a realisation.

**Reproducibility.** Every source is cached, sha256-pinned and manifested under
`research/data-manifests/`. The closed forms regenerate from
`portfolio_edge.studies.overlay_growth` and `portfolio_edge.studies.equity_share` and are
pinned by tests needing no market data. **The panel computations in §§3–6 were run as
scoping scripts and are not yet an experiment** — that is the gap a frozen specification
must close before any of it informs a decision.

---

## Consequence for this repository

1. **The zero-leverage rule's cost is now a number, not an assumption**, and
   [decision 0004](../decisions/0004-no-sleeve-promoted.md) records that its block on step 7
   is circular for that reason. **Neither block is lifted here.**
2. **Any future marginal-sleeve experiment must state its funding rule**, because the rule
   is worth more than the sleeve.
3. **Global diversification is a distributional argument, not a return argument**, and any
   page that states it must carry the USD counter-evidence in the same breath.
4. **A trend sleeve is a risk-reduction claim, not a return claim**, and must be judged on
   mechanism rather than on relative performance.
5. **Commodities, credit as a separate engine, and the alternative risk premia are
   rejected** — on stable +0.30 correlation, on duplication, and on cost respectively.
