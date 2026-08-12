# Rebalancing policy on real regional equity: the theory holds, the premise does not

**Question.** On real, unlevered, multi-region equity sleeves, does any rebalancing
policy — annual calendar, monthly calendar, a frozen relative threshold, or
cash-flow-directed — beat buy-and-hold from identical starting weights and identical
cash flows, on a declared investor objective and net of the costs it actually pays?

**Decision it informs.** Whether rebalancing policy belongs anywhere in this
repository's product as a source of return, and what a rebalancing feature would be
allowed to claim. The closed-form theory that this experiment tests empirically is in
[where outperformance can come from](expected-edge-decomposition.md) §1; the rule that
`kappa_t`, not the diversification-return statistic, is the correct diagnostic is in
the [research framework](portfolio-edge-research-framework.md), "Rebalancing". Out of
scope: leverage and financing, taxes, and any claim about an investable fund.

## Conclusion

**`rejected`.** Experiment 003, the repository's first confirmatory experiment, was
run once against its frozen falsifier and the falsifier fired on every clause at once.

Advantage over buy-and-hold, PRETAX, in percentage points per year, on the
**net-pessimistic** basis the frozen rejection rule names as the decision basis.
Growth is the deciding figure and the certainty equivalent is reported beside it
([decision 0008](../decisions/0008-growth-decides-crra-reports.md)); the third column
is the difference between them, which is what a policy was paid for reducing risk. The
interval and the two *p*-values are on the certainty-equivalent difference, because
that is the statistic the frozen specification named.

| Policy | **Growth, γ=1** | CE, γ=3 | De-risking | 95% interval on CE | bootstrap *p* | Holm-adjusted *p* |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| Relative threshold, 25% | **−0.240** | −0.213 | +0.027 | `[−1.698, +0.444]` | 0.710 | 1.000 |
| Cash-flow-directed | **−0.262** | −0.373 | −0.111 | `[−0.871, +0.256]` | 0.206 | 0.822 |
| Annual calendar | **−0.265** | −0.199 | +0.066 | `[−1.829, +0.402]` | 0.738 | 1.000 |
| Monthly calendar | **−0.438** | −0.339 | +0.100 | `[−1.951, +0.313]` | 0.578 | 1.000 |

Growth is `geo(policy) − geo(buy-and-hold)` on the time-weighted wealth index in §2,
which is the `gamma = 1` certainty equivalent by construction. Gross and
net-optimistic are not shown because cost moves no figure in the table by more than
**0.013 pp/yr** on the certainty equivalent or **0.012** on growth — §2 carries all
three cost columns and the point of that paragraph is exactly how little they change.

Every policy lost on **both bases**, on all three cost bases, over 35 years. None came
near the frozen materiality threshold of +0.25 pp/yr, none had an interval excluding
zero, none survived Holm correction, none appeared in two of the three diagnostic
eras, and every one of them had a **worse** maximum drawdown than the untouched
portfolio. Four independent rejection clauses, all firing.

**The metric change costs this experiment nothing, and that was checked rather than
assumed.** The de-risking component never exceeds 0.111 pp/yr in magnitude anywhere in
the grid, against a gap to the threshold of at least 0.45 pp/yr, so no clause can turn
on it. What does change is the *identity of the least-bad policy*: annual calendar on
the certainty equivalent, the 25% relative threshold on growth. Neither is within
0.44 pp/yr of the bar, so the swap decides nothing and is recorded only because a
reader comparing the two bases would otherwise find it unexplained. The one policy
whose de-risking component is **negative** is the cash-flow-directed one — it *adds*
risk relative to buy-and-hold, and the certainty equivalent was charging it for that.

**The three findings that matter more than the verdict.**

1. **The closed form for `gamma_star` is confirmed to a tenth of a basis point.** On
   real data, predicted `0.5 (sum w_i sigma_i^2 − sigma_p^2)` matched realised excess
   growth to within **0.2 bp/yr on every regional pair and 0.09 bp/yr on the
   portfolio**. The mathematics is not the problem.
2. **The closed form's *probability* is wrong on real data, and wrong in the
   dangerous direction.** The published result says the chance that rebalancing beats
   buy-and-hold never falls below **68.27%**. Over rolling 30-year windows of US
   against developed-ex-US, the realised frequency was **0.0%** — zero of 61 windows.
   The 68.27% floor is a property of the *equal-drift assumption*, not of rebalancing,
   and real regional equity drifts are nowhere near equal.
3. **The mechanism that would make rebalancing pay is absent, and its opposite is
   present at conventional significance.** `kappa_t` is **positively** autocorrelated
   in every pair tested. Relative regional performance *trends*; rebalancing is short
   exactly that, so it is predicted to lose, and it did.

**Costs are not the explanation and must not be offered as one.** The most expensive
policy paid **1.2 bp/yr** on the pessimistic assumption. Quadrupling every cost moved
the monthly policy's shortfall from −0.339 to −0.376 pp/yr — about a tenth of it.
Rebalancing did not lose to friction. It lost to the drift gap.

---

## 1. What was run

| Field | Value |
| --- | --- |
| Specification | [`research/experiments/exp_003_rebalancing.yaml`](../../research/experiments/exp_003_rebalancing.yaml), hash `fe521d2fbc0258027294e3eaebc402fdf74ee2543715adebb4bb8ed6a9ea4a72` |
| Run kind | **confirmatory**; does not consume the final holdout |
| Ledger `run_id` | `add1e77a184d45808bc062ac372f44ca` (a prior run of the identical specification, `5d3fc60f10bb…`, is ledgered `abandoned`: it was stopped mid-flight to add a hostile test, and its results were never viewed) |
| Sample | 1991-01 to 2025-12, **420 months = 35 whole calendar years**; 2026-01 onward held out |
| Sleeves | US 60%, developed ex-US 30%, emerging 10%, USD total returns |
| Cash flows | Identical everywhere: 5%/yr of initial wealth, flat nominal, contributed monthly, 1.75× initial wealth in total |
| Objective | **As frozen:** CRRA certainty-equivalent return, `gamma = 3`, on 35 non-overlapping calendar-year net returns — a **declared preference**, not a derived truth. **As read now:** the specification predates [decision 0008](../decisions/0008-growth-decides-crra-reports.md) and names no `decision_gamma`, so it falls back to its `crra_gamma` and its frozen falsifier still decides on `gamma = 3`. Geometric growth at `gamma = 1` is reported beside every verdict figure and reaches the same verdict on every clause |
| Costs | 2.0 bp (optimistic) and 8.0 bp (pessimistic) one-way, charged on traded notional inside the simulation, never as a haircut |
| Inference | Stationary block bootstrap on the joint sleeve panel, mean block **24 months frozen not tuned**, 20,000 resamples, every policy re-simulated on every resample |
| Seed | 20260813 |

### Two data findings that changed the experiment

**The registered `french_developed_ff5` dataset was mislabelled, and using it would
have wrecked the comparison.** `Developed_5_Factors_CSV.zip` was described in this
repository as "developed markets ex-US aggregate". It is not: it **includes** the
United States. Regressing its `Mkt-RF` on the US and Developed-ex-US series over
1990-07…2026-06 gives coefficients **0.460 and 0.549, summing to 1.009**. Used beside
a US sleeve it would have double-counted roughly half the US market. The description
is corrected and `Developed_ex_US_5_Factors_CSV.zip` is now registered as
`french_developed_ex_us_ff5`, with committed manifests.

**One risk-free rate is correct for all three regions, and it is the US bill.** Each
sleeve's total return is reconstructed as `Mkt-RF + RF`. That is an identity, not an
approximation. Ken French's international page, retrieved 2026-08-12, states verbatim:
*"The market factor is the return on a region's value-weight market portfolio minus
the U.S. one month T-bill rate"* and *"All returns are in U.S. dollars, include
dividends and capital gains, and are not continuously compounded."* Adding back the
rate that was subtracted recovers each region's USD total return exactly. The three
files' `RF` columns were checked and agree to **0.01 percentage points**, which is
their printed precision; the experiment **raises** rather than proceeds if they ever
disagree by more.

The residual reconstruction error is therefore not a cash-rate mismatch but the
source's two-decimal printing: **0.24 bp/yr** of standard deviation on each sleeve's
annualised mean. That is small, but it is the same order of magnitude as the effect
the theory predicts, which is the only reason a rounding error is worth reporting. It
cancels exactly in `kappa`, because `RF` is the identical column in both files.

---

## 2. The full policy comparison, PRETAX

Gross, net-optimistic and net-pessimistic are separate columns and are never
collapsed. Drawdown, volatility and geometric return are computed on the
**time-weighted** wealth index, so contributions cannot hide a drawdown; terminal
wealth is the equity curve, which should include them. **The `Geo %/yr` column is the
deciding basis in level form** — the conclusion's growth figures are this column minus
buy-and-hold's, on the matching cost basis.

| Policy | Basis | CE %/yr | Geo %/yr | Vol %/yr | Max DD % | Under water, months | Turnover %/yr | Cost %/yr | Trades | Mean abs. deviation, pp | Max deviation, pp | Terminal wealth |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Buy-and-hold | gross | **6.370** | 10.322 | 14.94 | −53.0 | 67 | 0.00 | 0.0000 | 0 | 14.83 | 26.36 | 45.36 |
| Annual calendar | gross | 6.176 | 10.062 | 14.73 | −53.0 | 63 | 2.97 | 0.0000 | 35 | 1.80 | 7.28 | 41.70 |
| Monthly calendar | gross | 6.044 | 9.897 | 14.73 | −53.1 | 63 | 7.17 | 0.0000 | 420 | 0.60 | 2.62 | 39.88 |
| Threshold 25% | gross | 6.160 | 10.086 | 14.75 | −53.3 | 63 | 1.94 | 0.0000 | 12 | 3.05 | 10.17 | 42.13 |
| Cash-flow-directed | gross | 5.997 | 10.060 | 14.92 | −53.9 | 65 | 0.00 | 0.0000 | 0 | 7.02 | 16.95 | 41.86 |
| Buy-and-hold | net-opt | **6.370** | 10.322 | 14.94 | −53.0 | 67 | 0.00 | 0.0000 | 0 | 14.83 | 26.36 | 45.36 |
| Annual calendar | net-opt | 6.175 | 10.061 | 14.73 | −53.0 | 63 | 2.97 | 0.0012 | 35 | 1.80 | 7.28 | 41.68 |
| Monthly calendar | net-opt | 6.041 | 9.894 | 14.73 | −53.1 | 63 | 7.17 | 0.0029 | 420 | 0.60 | 2.62 | 39.84 |
| Threshold 25% | net-opt | 6.159 | 10.085 | 14.75 | −53.3 | 63 | 1.94 | 0.0008 | 12 | 3.05 | 10.17 | 42.12 |
| Cash-flow-directed | net-opt | 5.997 | 10.060 | 14.92 | −53.9 | 65 | 0.00 | 0.0000 | 0 | 7.02 | 16.95 | 41.86 |
| Buy-and-hold | net-pess | **6.370** | 10.322 | 14.94 | −53.0 | 67 | 0.00 | 0.0000 | 0 | 14.83 | 26.36 | 45.36 |
| Annual calendar | net-pess | 6.171 | 10.057 | 14.73 | −53.0 | 63 | 2.97 | 0.0048 | 35 | 1.80 | 7.28 | 41.63 |
| Monthly calendar | net-pess | 6.032 | 9.884 | 14.73 | −53.1 | 63 | 7.17 | 0.0115 | 420 | 0.60 | 2.62 | 39.73 |
| Threshold 25% | net-pess | 6.157 | 10.083 | 14.75 | −53.3 | 63 | 1.94 | 0.0031 | 12 | 3.05 | 10.17 | 42.09 |
| Cash-flow-directed | net-pess | 5.997 | 10.060 | 14.92 | −53.9 | 65 | 0.00 | 0.0000 | 0 | 7.02 | 16.95 | 41.86 |

Read the table for what rebalancing *did* buy, because it is not nothing and it is not
return. **It controlled exposure, exactly as advertised.** The untouched portfolio's
weights drifted a mean 14.83 percentage points from target and reached 26.36 at their
worst — a 60/30/10 policy that spent much of the period as something closer to
75/17/8. Monthly rebalancing held that to 0.60 and 2.62. Volatility fell from 14.94%
to 14.73%, and time under water from 67 months to 63.

**What it did not buy is drawdown protection.** Every rebalanced policy's maximum
drawdown was equal to or worse than buy-and-hold's −53.0%, reaching −53.9% for the
cash-flow-directed policy. This is the framework's Rattray result appearing in the
data: rebalancing buys the falling asset, and in a crisis every equity region falls
together, so the policy adds exposure to the drawdown rather than removing it.

**Tax is not modelled and no haircut is applied.** The simulation holds no tax lots,
so it cannot know a basis and therefore may not price a realisation. Qualitatively the
missing test moves the ranking *further against* the rebalancing policies, because
every rebalance sells an appreciated position and realises gain that buy-and-hold
defers indefinitely; the annual policy turned over 2.97%/yr and the monthly 7.17%/yr
against buy-and-hold's zero. The size of that move is not estimated here and must not
be guessed.

### The index-to-fund gap, in its own column

These are index-like series, not funds. The gap is reported separately and applied to
nothing:

| Sleeve | Weight | Expense ratio, bp | Non-recoverable withholding, bp | Weighted, bp |
| --- | --- | --- | --- | --- |
| US | 0.60 | 3.0 | 0.0 | 1.8 |
| Developed ex-US | 0.30 | 5.0 | 21.0 | 7.8 |
| Emerging | 0.10 | 7.0 | 30.0 | 3.7 |
| **Portfolio** | | | | **13.3 bp/yr** |

Expense ratios and the spread figures inside the cost model are the dated, sourced
numbers in [expected-edge-decomposition](expected-edge-decomposition.md) §2.1 (as of
2026-08-10: VTI 0.55 bp, VXUS 1.18 bp, VB 2.72 bp median 30-day spreads; 3 bp expense
ratios). **The withholding figures are an assumption, not a measurement**, and no
primary source for them was retrieved: 3.0% dividend yield × 7% non-recoverable for
developed ex-US, 2.7% × 11% for emerging. Their arithmetic is stated so a reader can
substitute their own. Recoverability depends on account type and the foreign tax
credit, neither of which is modelled.

This column **cannot change the ranking**, because expense ratio and withholding are
charged on assets held rather than on trades and so cancel in every paired difference.
It is decision-relevant for a different reason: at **13.3 bp/yr** it is larger than
the entire predicted rebalancing bonus on this portfolio, and about twelve times the
largest transaction cost any policy actually paid.

---

## 3. Question 1: does `gamma_star` match the closed form? Yes, almost exactly

| Pair, 50/50 | Predicted continuous, bp/yr | Predicted discrete monthly, bp/yr | **Realised**, bp/yr | Error |
| --- | --- | --- | --- | --- |
| US \| developed ex-US | 12.5 | 12.5 | **12.7** | +0.2 |
| US \| emerging | 25.5 | 25.5 | **25.5** | +0.0 |
| Developed ex-US \| emerging | 21.2 | 21.2 | **21.1** | −0.1 |
| **Portfolio, 60/30/10** | **17.69** | — | **17.78** | **+0.09** |

`0.5 (sum w_i sigma_i^2 − sigma_p^2)` is not an approximation on this data; it is a
measurement. The continuous and discrete-monthly predictions are indistinguishable at
this frequency, which is the closed form's own statement that rebalancing *frequency*
is a second-order question, confirmed.

**The diversification-return identity was not used as evidence anywhere in this
experiment**, and the code says so in its own output. It appears once, because
`gamma_star` is defined against `sum_i w_i g_i` — which on this portfolio is 9.259%/yr
and is the growth rate of no portfolio anyone can hold (Willenbrock 2011). The
investable comparison is the next line.

## 4. Question 3: does the realised advantage fall inside the predicted band? No

| Pair, 50/50 | Realised rebalanced − held, bp/yr | Predicted, **equal drift** | Equal-drift 5th–95th | Realised drift gap, pp/yr | Predicted with the realised drift gap | Inside the band? |
| --- | --- | --- | --- | --- | --- | --- |
| US \| developed ex-US | **−62.9** | +0.5 | `[−33.1, +12.5]` | **+4.34** | **−70.5** | **No** |
| US \| emerging | −1.5 | +1.9 | `[−63.0, +25.4]` | +2.53 | −21.7 | Yes |
| Developed ex-US \| emerging | +6.9 | +1.3 | `[−53.4, +21.1]` | −1.82 | −11.3 | Yes |
| **Portfolio, 60/30/10** | **−38.7** | — | — | — | — | — |

**The gap is the drift gap, and it is diagnosable to a single number.** The closed
form's break-even is exactly `drift gap = gamma_star`
([expected-edge-decomposition](expected-edge-decomposition.md) §1.1, and it is
horizon-free). For US against developed ex-US the realised drift gap was **4.34 pp/yr
against a `gamma_star` of 12.5 bp/yr — a factor of 35**. The estimation cliff that page
describes as theoretical is, on the canonical real-world pair, thirty-five times deep.

Extending the closed form to a non-zero drift gap — `E[log cosh(D/2)]` with
`D ~ N(delta·T, tau^2 T)`, implemented as `expected_log_cosh_half` and checked against
the repository's existing zero-mean solution — predicts **−70.5 bp/yr** against a
realised **−62.9**. The theory is not wrong. **Its equal-drift special case is what
was being quoted, and that special case does not describe two real equity regions.**

## 5. Question 2: is `kappa_t` serially dependent? Yes, positively — the crux

This, not the diversification-return statistic, is the diagnostic that decides whether
rebalancing can add value. Rebalancing is short relative-performance continuation, so
**positive** autocorrelation in `kappa` predicts that it loses.

| Pair | `rho_1` | Block-bootstrap 95% | i.i.d. null 95% | Lags outside the null | Ljung-Box(12) *p* | VR(12), *z*₂ | VR(60), *z*₂ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| US \| developed ex-US | +0.081 | `[−0.021, +0.152]` | `[−0.096, +0.092]` | {11} | 0.054 | 1.130, +0.63 | 2.004, **+2.19** |
| US \| emerging | **+0.203** | `[+0.047, +0.297]` | `[−0.098, +0.094]` | {1, 2, 3, 7} | **0.0000** | 2.014, **+4.90** | 3.763, **+6.08** |
| Developed ex-US \| emerging | +0.128 | `[−0.040, +0.218]` | `[−0.098, +0.093]` | {1, 2, 4, 6, 9, 11, 24, 36} | **0.0000** | 1.236, +0.97 | 1.407, +0.79 |

Variance ratios are Lo–MacKinlay on log relative performance with the
heteroskedasticity-consistent statistic, which is the only one that should be read
here because these series have severe volatility clustering. **Every variance ratio at
every horizon in every pair exceeds 1.** For US against emerging the ratio rises
monotonically to 3.76 at five years with *z*₂ = +6.08.

**Reading.** The mechanism that could make rebalancing profitable — mean reversion in
relative performance — is **absent from this sample**. Its opposite, multi-year
momentum in relative regional performance, is present, and in the US/emerging pair it
is significant at every horizon and by every test used. That is a sufficient
explanation for the verdict, and it is a structural explanation rather than a
description of one unlucky path.

Two honest qualifications. The block-bootstrap interval is attenuated at lags
approaching the frozen 24-month mean block length, because a resample breaks
dependence at every block join, so those intervals are conservative. And the
Politis–White automatic block lengths — 2.0, 6.8 and 10.5 months for the three pairs —
are reported as a **diagnostic only**; the block was frozen at 24 months before the
run and a data-chosen block would have been a tuned parameter.

## 6. Question 4: where the data contradicts the theory

Four places, in descending order of how much they matter.

**The 68.27% floor does not survive contact with real drifts.** The closed form proves
`P(rebalanced beats held) >= 2 Phi(1) − 1 = 68.27%` at every horizon and every
correlation. Realised frequencies over overlapping rolling windows:

| Pair | 5 years | 10 years | 20 years | 30 years |
| --- | --- | --- | --- | --- |
| US \| developed ex-US | 21.6% | 24.9% | 28.2% | **0.0%** |
| US \| emerging | 22.2% | 24.3% | 95.0% | 41.0% |
| Developed ex-US \| emerging | 59.0% | 69.8% | 61.3% | 95.1% |

Nine of the twelve cells fall below the theoretical floor and six fall below half of
it. The windows overlap and are **not** independent observations — a 30-year window in
a 35-year sample has 61 distinct start months, and the 0.0% and 95.1% cells are each
close to a single realisation. But no amount of dependence turns 0 of 61 into evidence
for a 68% floor. The floor is a theorem about a model whose equal-drift premise is
false here, not a property of rebalancing.

**Returns are not lognormal.** Monthly `kappa` carries excess kurtosis of 0.86 to 1.51
and skewness of −0.22 to +0.11. The Ljung–Box statistic on `kappa²` gives
*p* = 2.7 × 10⁻⁸, 2.6 × 10⁻⁴ and 7.8 × 10⁻³² — overwhelming volatility clustering in
all three pairs. The GBM model behind the closed form has neither. Notably, `gamma_star`
survived both violations intact, so what the non-normality damages is the *distribution*
of the outcome, not its centre.

**Rebalancing worsened the maximum drawdown rather than improving it.** The theory is
silent on drawdown; the sales pitch is not. Buy-and-hold −53.0%, threshold −53.3%,
cash-flow-directed −53.9%.

**The 2000s–2010s era is the only one that supports rebalancing, and it supports it
loudly.** Diagnostics, never independent observations. **Certainty equivalent only:
the artifact publishes no era-level geometric return, so no growth companion and no
de-risking component can be quoted here without inventing one.** Under
[decision 0008](../decisions/0008-growth-decides-crra-reports.md) that is exactly why
these rows may not decide anything — the specification already forbade it on
era-dependence grounds, and the missing companion is a second, independent reason.

| Era | Annual | Monthly | Threshold 25% | Cash-flow-directed |
| --- | --- | --- | --- | --- |
| 1991–1999 | −0.184 | −0.610 | −0.300 | −0.324 |
| 2000–2019 | **+0.575** | **+0.490** | **+0.564** | **+0.290** |
| 2020–2025 | −0.020 | −0.028 | −0.020 | −0.098 |
| **Full sample** | **−0.199** | **−0.339** | **−0.213** | **−0.373** |

A reader who saw only the middle row would conclude that annual rebalancing is worth
+0.575 pp/yr and clears the materiality threshold twice over. It is one twenty-year
window inside a thirty-five-year sample, it is bracketed by two windows of the opposite
sign, and the specification's rejection rule requires two of three eras precisely so
that this cannot be reported as a finding.

## 7. Hostile tests

Every declared test, on the net-pessimistic basis, in pp/yr against buy-and-hold.
Nothing rescues any policy. **Certainty equivalent only, for the same reason as the
era table**: the artifact carries no per-test geometric return, so the growth
companion decision 0008 requires cannot be sourced. The **smallest** gap any test
leaves to the +0.25 threshold is 0.355 pp/yr, at the 30% threshold band, and the
largest de-risking component measured anywhere in this experiment is 0.111 — so no
plausible companion changes a verdict. That is an argument, not a published number,
and it is stated as one.

| Test | Annual | Monthly | Threshold 25% | Cash-flow-directed |
| --- | --- | --- | --- | --- |
| Baseline | −0.199 | −0.339 | −0.213 | −0.373 |
| Double every cost | −0.205 | −0.351 | −0.216 | −0.373 |
| Quadruple every cost | −0.215 | −0.376 | −0.221 | −0.373 |
| Remove 2008–2009 | −0.249 | −0.390 | −0.243 | −0.267 |
| Remove 2020 and 2022 | −0.227 | −0.388 | −0.242 | −0.409 |
| Remove the leading policy's best year (2025, +2.89 pp of excess) | −0.275 | −0.416 | −0.289 | −0.407 |
| Annual anchor moved to June | −0.388 | −0.403 | −0.130 | −0.287 |
| Annual anchor moved to March | −0.345 | −0.462 | −0.347 | −0.476 |
| US weight +10 pp | −0.146 | −0.262 | −0.096 | −0.351 |
| US weight −10 pp | −0.239 | −0.394 | −0.182 | −0.381 |
| Threshold band 20% | — | — | −0.165 | — |
| Threshold band 30% | — | — | −0.105 | — |
| Zero cash flow | −0.199 | −0.339 | −0.213 | **0.000** |
| Contribution tracking current wealth | −0.199 | −0.339 | −0.213 | −0.459 |

Three of these are worth naming. **Zero cash flow makes the cash-flow-directed policy
identical to buy-and-hold to the last decimal**, which is the accounting check the
specification predicted in advance. **The two-period identity
`R_rebal − R_hold = −w₁w₂κ₁κ₂` reproduces to 1.0 × 10⁻¹⁶**, so the simulation's
accounting is doing what the algebra says. And **the annual policy's result moves by
0.19 pp/yr across a December, a June and a March anchor** — as large as the effect
being measured, which means a calendar rebalancing result of this size is partly a
month artefact and should never be quoted without its anchor.

The wider threshold bands look better than the frozen one (−0.165 at 20%, −0.105 at
30%). That is reported because it was predeclared, and it changes nothing: the frozen
25% remains the decision rule, all three are negative, and the pattern only says that
trading less was better — which is the same finding again.

**One declared hostile test was not run.** A *further* one-month execution delay for
the threshold policy is not implementable through the frozen `core.rebalance` API,
which already executes every decision on the next period's return; adding a second lag
needs a new policy type in `core/`, which this experiment was not permitted to add for
a diagnostic. It is recorded as an open item rather than quietly omitted. The two
annual-anchor shifts *are* execution shifts and were run.

---

## 8. Verified facts, assumptions, open questions

**Verified in this experiment.** The `gamma_star` closed form on real data, to 0.1 bp.
The `kappa` sign and its significance. The two-period identity, to machine precision.
The `Mkt-RF + RF` reconstruction as an identity, with the shared US bill confirmed to
its printing precision and enforced by a hard check. That `Developed_5_Factors`
includes the US. That the cash-flow-directed policy degenerates to buy-and-hold at zero
cash flow.

**Assumptions, stated so they can be attacked.** CRRA `gamma = 3` is a declared
preference; a different `gamma` is a different specification — which is precisely why
[decision 0008](../decisions/0008-growth-decides-crra-reports.md) froze a *new*
specification for Experiment 010 rather than editing the old one, and why this
experiment's frozen falsifier is still read at `gamma = 3`. Starting weights are
pinned to approximate global market capitalisation, an external anchor chosen because
sample first moments had already been seen while diagnosing the mislabelled dataset —
that sequence is recorded in the specification's freeze note. The withholding-tax
figures are assumptions with no retrieved source. Market impact is omitted by declared
choice; at retail scale trade/ADV is far below 0.1%. Deploying a contribution is
charged no transaction cost, identically for every policy, so it cancels in every
paired difference.

**Open questions this page does not settle.**

1. **Would a daily source change the threshold policy?** The data is monthly, so
   intramonth breaches are invisible and the 25% band fired only 12 times in 35 years.
   A daily band would trade more and cost more; whether it would also capture more is
   unmeasured.
2. **Would an after-tax test change the ranking, or only the level?** The direction is
   clear and the magnitude is not. It needs tax lots, holding periods, realised gains,
   distributions, loss-harvesting rules, rates and account type — none of which exist
   here.
3. **Does the positive `kappa` autocorrelation persist out of sample?** It is measured
   on one 35-year window, and a cross-sectional-momentum reading of it would be a
   different experiment with its own specification and its own multiple-testing family.
4. **What would the answer be for genuinely uncorrelated sleeves?** Every pair here
   correlates 0.72 to 0.79 in logs. The theory says `gamma_star` grows as correlation
   falls; whether a real, investable, low-correlation pair with *equal* drift exists is
   the only condition under which any of this could pay, and no such pair was tested.

**Reproducibility.** `cd research && uv run python -m portfolio_edge.experiments.exp_003_rebalancing --view-results`.
Source vintages are pinned by sha256 in the specification and a mismatch aborts;
manifests are committed under `research/data-manifests/`. Retrieval date for every
source: **2026-08-12**. Seed 20260813. Every figure on this page is PRETAX.

---

## Consequence for this repository

1. **Rebalancing is `rejected` as a source of return, and the rejection is stronger
   than the [edge budget](expected-edge-decomposition.md) assumed.** That page books
   rebalancing at +2.4 bp/yr central against the stated index. On the canonical
   real-world instance of its own premise, the measured figure over 35 years is
   **−38.7 bp/yr** on the portfolio and **−62.9 bp/yr** on the US/developed-ex-US pair.
   The budget line should be read as an upper bound that a real drift gap removes.
2. **Rebalancing is retained as a risk-control policy, which is what it demonstrably
   is.** It held exposure within 0.6 to 3.1 percentage points of target against
   buy-and-hold's 14.8, for 0.3 to 1.2 bp/yr. Anyone who wants their declared
   allocation to remain their actual allocation should rebalance. That is a statement
   about *keeping a promise*, not about return, and it is the only claim this evidence
   supports.
3. **Do not build a rebalancing-bonus feature.** The decomposition page already
   forbids it on theory. This page forbids it on data, and adds the specific number a
   tool would have to show: not a positive expectation, but **−0.2 to −0.4 pp/yr with a
   95% interval reaching −1.9**, and a worse maximum drawdown.
4. **The drift gap, not the excess growth rate, is the quantity that decides.** Any
   future sizing or allocation code that reasons about constant-weight portfolios must
   carry `drift gap versus gamma_star` as an explicit, reported comparison. On this
   data it was 35 to 1 against.
5. **`gamma_star` is safe to compute and safe to display; the probability attached to
   it is not.** The excess-growth closed form reproduced on real data to a tenth of a
   basis point. The 68.27% win-probability floor did not survive at all. Displaying the
   second without the drift gap beside it would be the most misleading thing this
   repository could ship on the subject.
