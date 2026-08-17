# Rebalancing: the theory is exact, the premise is false

**Question.** Does any rebalancing policy — annual calendar, monthly calendar, a frozen
relative threshold, or cash-flow-directed — beat buy-and-hold from identical starting
weights and cash flows, on a declared objective and net of the costs it actually pays?

**Decision it informs.** Whether rebalancing belongs anywhere in this repository's product
as a source of return, and what a rebalancing feature would be allowed to claim. Out of
scope: leverage and financing, taxes, and any claim about an investable fund.

**This page holds both halves**: §1 is the closed-form theory, derived rather than cited
and pinned by tests that need no market data; §2 onward is
[Experiment 003](#2-the-experiment), the repository's first confirmatory run, which tested
it on 420 months of real regional equity.

---

## Conclusion

**`rejected`.** The falsifier fired on every clause at once.

Advantage over buy-and-hold, PRETAX, pp/yr, on the **net-pessimistic** basis the frozen
rejection rule names. Growth is the deciding figure and the certainty equivalent reports
beside it ([decision 0008](../decisions/0008-growth-decides-crra-reports.md)); the third
column is what a policy was paid for reducing risk.

| Policy | **Growth, γ=1** | CE, γ=3 | De-risking | 95% interval on CE | Holm *p* |
| --- | ---: | ---: | ---: | --- | ---: |
| Relative threshold, 25% | **−0.240** | −0.213 | +0.027 | `[−1.698, +0.444]` | 1.000 |
| Cash-flow-directed | **−0.262** | −0.373 | −0.111 | `[−0.871, +0.256]` | 0.822 |
| Annual calendar | **−0.265** | −0.199 | +0.066 | `[−1.829, +0.402]` | 1.000 |
| Monthly calendar | **−0.438** | −0.339 | +0.100 | `[−1.951, +0.313]` | 1.000 |

**Every policy lost on both bases, on all three cost bases, over 35 years.** None came
near the frozen materiality threshold of +0.25 pp/yr, none had an interval excluding zero,
none survived Holm, none appeared in two of the three diagnostic eras, and **every one had
an equal or worse maximum drawdown than the untouched portfolio.** Four independent
rejection clauses, all firing.

**This is not an underpowered null.** The effect is large, negative, and its mechanism is
measured — which distinguishes it from most of the other rejections in this repository.

**And the verdict is scoped to this window and this universe.** The mechanism §3 identifies
is the drift gap, which ran **35 to 1 against** rebalancing here. On 1963-2020 US against an
equal-weight ex-US basket the same ratio is **0.3 to 1 in favour**, and rebalancing wins by
12-18 bp/yr (**§6**, scoping only). The rule generalises; this verdict does not. Quoting
"rebalancing is rejected" without its window is the error
[docs/AGENTS.md](../AGENTS.md) names.

**Three findings that matter more than the verdict.**

1. **The closed form for `gamma_star` is confirmed to a tenth of a basis point.** Predicted
   `0.5 (sum w_i sigma_i**2 − sigma_p**2)` matched realised excess growth to within
   **0.2 bp/yr on every regional pair and 0.09 bp/yr on the portfolio**. The mathematics is
   not the problem.
2. **The closed form's *probability* is wrong on real data, and wrong in the dangerous
   direction.** The published result says the chance rebalancing beats buy-and-hold never
   falls below **68.27%**. Over rolling 30-year windows of US against developed-ex-US the
   realised frequency was **0.0% — zero of 61 windows.** The floor is a property of the
   *equal-drift assumption*, not of rebalancing.
3. **The mechanism that would make rebalancing pay is absent, and its opposite is present
   at conventional significance.** `kappa_t` is **positively** autocorrelated in every pair
   tested. Relative regional performance *trends*; rebalancing is short exactly that.

**Costs are not the explanation and must not be offered as one.** The most expensive policy
paid **1.2 bp/yr**. Quadrupling every cost moved the monthly policy's shortfall from −0.339
to −0.376 — about a tenth of it. **Rebalancing lost to the drift gap, not to friction.**

---

## 1. The theory, settled by derivation

Two assets follow correlated geometric Brownian motions with log-drifts `g_i`,
volatilities `sigma_i`, correlation `rho`. Write `D(T)` for the difference in log price
relatives and `tau**2 = sigma_a**2 + sigma_b**2 − 2 rho sigma_a sigma_b`. Everything below
regenerates from
[`studies/volatility_harvesting.py`](../../research/src/portfolio_edge/studies/volatility_harvesting.py)
and is pinned in `test_studies_volatility_harvesting.py`. No market data.

**The excess growth rate.** For constant long-only weights,
`g_p = sum_i w_i g_i + gamma_star` with
`gamma_star = 0.5 (sum_i w_i sigma_i**2 − sigma_p**2) >= 0`. At equal volatilities and
50/50 this is `tau**2 / 8`. **The subtrahend `sum_i w_i g_i` is not the return of any
investable portfolio**, so a random walk produces a positive measured "diversification
return" with no skill involved.

**Buy-and-hold's asymptotic growth is `max_i g_i`, almost surely.** For `n` assets with
fixed positive weights, `M(T) + log(min_i w_i) <= log sum_i w_i e**X_i(T) <= M(T)` where
`M(T) = max_i X_i(T)`, so both bounds are `M(T) + O(1)` and the strong law gives
`X_i(T)/T -> g_i`. **A buy-and-hold portfolio converges on its single best component and
asymptotically throws away the whole of `gamma_star`.**

**The exact condition.** Constant weights beat buy-and-hold asymptotically **iff
`g_p > max_i g_i`**. With equal drifts this reduces to `gamma_star > 0`, so with equal
drifts rebalancing *always* wins eventually.

**Why it is a short straddle.** For equal volatilities at 50/50,
`0.5(e**u + e**v) = e**((u+v)/2) cosh((u−v)/2)` gives, with no approximation,

```
log V_reb(T) − log V_hold(T) = gamma_star * T − log cosh(D(T)/2)
```

The common factor cancels **pathwise**. Since `log cosh(d/2) -> |d|/2 − log 2`, this is
literally the payoff of a short straddle on relative log performance struck at zero, with
premium `gamma_star * T`: **the upside is capped and the downside is not.** That derives
the qualitative
[Rattray et al. (2020)](https://people.duke.edu/~charvey/Research/Published_Papers/P145_Strategic_rebalancing.pdf)
two-period identity in continuous time.

**One function governs frequency, buy-and-hold and continuous rebalancing.** With
`B(v) = E[log cosh(Z/2)]`, `Z ~ N(0, v)`: rebalancing at interval `h` earns `B(tau**2 h)/h`
per year, buy-and-hold for `T` years earns `B(tau**2 T)/T`, and continuous rebalancing
earns `tau**2/8`. **Monthly rebalancing captures 99.917% of the continuous bonus and annual
99.026%, so frequency is a second-order question and horizon is a first-order one.**

**The probability has a closed form and depends on volatility, correlation and horizon
only through `c = gamma_star T`:**
`P = 2 Phi(2 arccosh(e**c) / sqrt(8c)) − 1`. **The break-even drift gap is horizon-free**:
against the ex-ante higher-drift asset, `P = Phi((gamma_star − delta) sqrt(T/(2 gamma_star)))`,
which at `delta = gamma_star` is exactly 0.5 at **every** horizon.

### The numbers these produce

Two 20%-volatility assets, identical log-drift, 50/50, 30 years, monthly rebalancing. All
closed form; a seeded 20,000-path Monte Carlo agrees within three of its own standard
errors.

| rho | `gamma_star` | Buy-and-hold captures | Rebalancing residual (mean) | Median | 5th pct | P(rebal wins) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.0 | 100.0 bp | 81.69 bp | **18.31 bp** | 56.44 bp | −190.6 bp | 0.7066 |
| 0.3 | 70.0 bp | 59.97 bp | 10.03 bp | 39.12 bp | −147.7 bp | 0.6995 |
| 0.6 | 40.0 bp | 36.26 bp | 3.74 bp | 22.12 bp | −94.6 bp | 0.6923 |
| 0.9 | 10.0 bp | 9.72 bp | 0.28 bp | 5.47 bp | −27.0 bp | 0.6851 |

Three readings matter more than the table.

- **The win probability is nearly inert**, moving from 0.685 to 0.707 across the whole
  correlation range, because its floor as `c -> 0` is `2 Phi(1) − 1 = 68.27%`. **A 70% win
  rate against buy-and-hold is the *null*, not evidence.**
- **The mean and median differ by a factor of three.** Reporting only the mean understates
  a typical path; reporting only the median hides a 5th percentile at −191 bp/yr over
  thirty years.
- **Realistic portfolios are far smaller.** A 60/40 at `sigma = 16%/6%`, `rho = 0.1` has
  `gamma_star = 32.74 bp`, of which buy-and-hold captures 30.29, leaving **2.45 bp/yr** in
  the mean.

**More assets makes buy-and-hold capture *more*, not less.** One hundred equicorrelated
stocks at `sigma = 30%`, `rho = 0.25` have `gamma_star = 334 bp/yr`, of which a 30-year
buy-and-hold captures more than 95%, leaving about **4 bp/yr**. **So an equal-weight sleeve
run against a cap-weighted index is not harvesting 334 bp of volatility; whatever it earns
is a size and value tilt.**

**Horizons to confidence, at the most favourable plausible `gamma_star` of 100 bp/yr:**
75% at 88 years, 80% at 163, **90% at 390**, 95% at 622. At a realistic 40 bp/yr, multiply
by 2.5. **"Near definitively" is refuted quantitatively, not rhetorically.**

### Chambers and Zdanowicz, and why log wealth survives them

Their Exhibit 4 fixture reproduces exactly: `E[W_T] = 1.050625` for both policies, and
their long-rebalanced/short-buy-and-hold trade has **exactly zero** expected profit. **The
result also generalises**, which strengthens their case: for returns independent across
time, `E[W_reb] = (1 + w'mu)**T` and `E[W_hold] = sum_i w_i (1 + mu_i)**T`, which coincide
when all `mu_i` are equal and, by strict convexity, leave buy-and-hold strictly *ahead*
whenever the means differ. **An investor who genuinely maximises expected terminal wealth
should never rebalance.**

Three corrections to how they are usually quoted here and elsewhere.

1. **Their 1.874% and 1.867% are not expected log wealth.** They are `E[W**(1/T)] − 1`, the
   expected annualised compound rate. The expected log growth rates are 1.2346% and
   1.2201%. Both rank the policies the same way, but the numbers belong to a different
   statistic.
2. **Their "arbitrary nonlinear transformation" sentence is about the annualised rate, not
   about log wealth**, which they never analyse. The decisive evidence is their own
   footnote 6: *"The magnitude of the effect is driven by the time it takes the planet to
   orbit the sun."* **`E[log W]` contains no annualisation, so the charge does not reach
   it.** They engage neither Breiman nor Algoet–Cover anywhere.
3. **Two arithmetic slips in their Exhibit 5**, neither changing a conclusion:
   recomputation reproduces 34 of 36 printed figures exactly.

**Where they stop is where the argument turns.** Their footnote says the horizon "was not
extended beyond 12 years because a four path tree with non-recombining nodes" becomes
unmanageable — but both policies are recombining and the whole exhibit computes in
`O(T**2)`. Extended, **the rebalanced portfolio's expected log growth is constant at
1.2346% at every horizon** (log wealth is additive) while buy-and-hold's falls
monotonically to `max_i g_i`, which is exactly 0% here. **Their 12-period gap of 12 bp is
not the size of the effect; it is the size of the effect at the horizon they stopped at.**

**Verdict: the dismissal is wrong as stated and right in what it defends.** Wrong, because
`(1/T) log W_T` is a pathwise property of the realised wealth path with no preferences in
it, and Breiman's Theorem 2 gives the log-optimal strategy almost-sure dominance — no other
utility has that property. Right, because expected terminal wealth is a legitimate
alternative objective under which rebalancing is worth nothing. Their own deciding example
prices the disagreement cleanly: **a log investor pays $268.12 per $10,000, 1.32%, to
decline a gamble whose expected value is 23% higher.** That is a preference, not an error,
and **Samuelson's objection at finite horizons stands untouched.**

**What a log investor actually gains is exactly a mean-preserving contraction.** At
`mu = 7%`, `sigma = 20%`, `rho = 0`, `T = 30`: expected terminal wealth 8.1662 for
**both**; variance 54.82 rebalanced against 77.36 held, a **29.1% reduction at an unchanged
mean**; median 6.0496 against 5.6610. **That is the whole economic content of the
diversification return** — worth having, priced in single-digit-to-tens of basis points of
growth, and not an arbitrage.

---

## 2. The experiment

| Field | Value |
| --- | --- |
| Specification | [`exp_003_rebalancing.yaml`](../../research/experiments/exp_003_rebalancing.yaml), hash `fe521d2fbc02…` |
| Run kind | **confirmatory**; does not consume the final holdout |
| Ledger `run_id` | `add1e77a184d45808bc062ac372f44ca`. A prior run of the identical specification is ledgered `abandoned` — stopped mid-flight to add a hostile test, results never viewed |
| Sample | 1991-01…2025-12, **420 months**; 2026-01 onward held out |
| Sleeves | US 60%, developed ex-US 30%, emerging 10%, USD total returns |
| Cash flows | Identical everywhere: 5%/yr of initial wealth, flat nominal, monthly, 1.75× initial wealth in total |
| Objective | **As frozen:** CRRA certainty equivalent, `gamma = 3`, on 35 non-overlapping calendar-year net returns — a declared preference. **As read now:** the specification predates decision 0008 and names no `decision_gamma`, so its frozen falsifier still decides on `gamma = 3`, with growth reported beside every verdict figure and reaching the same verdict on every clause |
| Costs | 2.0 bp and 8.0 bp one-way, charged on traded notional inside the simulation, never as a haircut |
| Inference | Stationary block bootstrap on the joint sleeve panel, mean block **24 months frozen not tuned**, 20,000 resamples, every policy re-simulated on every resample |
| Seed | 20260813 |

**The metric change costs this experiment nothing, and that was checked rather than
assumed.** The de-risking component never exceeds 0.111 pp/yr anywhere in the grid against
a gap to the threshold of at least 0.45. What *does* change is the identity of the
least-bad policy — annual calendar on the certainty equivalent, the 25% threshold on growth
— and neither is within 0.44 pp/yr of the bar. The one policy whose de-risking component is
**negative** is the cash-flow-directed one: it *adds* risk relative to buy-and-hold.

### Two data findings that changed the experiment

**The registered `french_developed_ff5` dataset was mislabelled, and using it would have
wrecked the comparison.** `Developed_5_Factors_CSV.zip` was described here as "developed
markets ex-US aggregate". It is not: it **includes** the United States. Regressing its
`Mkt-RF` on the US and Developed-ex-US series gives coefficients **0.460 and 0.549, summing
to 1.009** — used beside a US sleeve it would have double-counted roughly half the US
market.

**One risk-free rate is correct for all three regions, and it is the US bill.** Ken
French's international page states that *"the market factor is the return on a region's
value-weight market portfolio minus the U.S. one month T-bill rate"*, so `Mkt-RF + RF` is
an identity, not an approximation. The three files' `RF` columns agree to their printed
precision, and the experiment **raises** rather than proceeding if they ever disagree by
more. The residual reconstruction error is therefore the source's two-decimal printing —
**0.24 bp/yr** — which is small but the same order of magnitude as the effect the theory
predicts, and it cancels exactly in `kappa`.

### The full comparison, PRETAX

Gross, net-optimistic and net-pessimistic are separate columns and never collapsed.
Drawdown, volatility and geometric return are on the **time-weighted** wealth index, so
contributions cannot hide a drawdown. Net-pessimistic rows only; cost moves no figure by
more than 0.013 pp/yr.

| Policy | CE %/yr | **Geo %/yr** | Vol | Max DD | Under water | Turnover %/yr | Cost %/yr | Mean abs. deviation | Max deviation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Buy-and-hold** | **6.370** | **10.322** | 14.94 | **−53.0** | 67 mo | 0.00 | 0.0000 | **14.83 pp** | **26.36 pp** |
| Annual calendar | 6.171 | 10.057 | 14.73 | −53.0 | 63 mo | 2.97 | 0.0048 | 1.80 | 7.28 |
| Monthly calendar | 6.032 | 9.884 | 14.73 | −53.1 | 63 mo | 7.17 | 0.0115 | **0.60** | **2.62** |
| Threshold 25% | 6.157 | 10.083 | 14.75 | −53.3 | 63 mo | 1.94 | 0.0031 | 3.05 | 10.17 |
| Cash-flow-directed | 5.997 | 10.060 | 14.92 | **−53.9** | 65 mo | 0.00 | 0.0000 | 7.02 | 16.95 |

**Read the table for what rebalancing *did* buy, because it is not nothing and it is not
return.** The untouched portfolio's weights drifted a mean 14.83 percentage points from
target and reached 26.36 at their worst — a 60/30/10 policy that spent much of the period
as something closer to 75/17/8. Monthly rebalancing held that to 0.60 and 2.62.

**What it did not buy is drawdown protection.** Every rebalanced policy's maximum drawdown
was equal to or worse than buy-and-hold's. This is the theory's short-straddle result
appearing in the data: rebalancing buys the falling asset, and in a crisis every equity
region falls together, so the policy **adds exposure to the drawdown** rather than removing
it.

**Tax is not modelled and no haircut is applied.** The simulation holds no tax lots, so it
cannot know a basis and may not price a realisation. Qualitatively the missing test moves
the ranking *further against* rebalancing, because every rebalance realises gain that
buy-and-hold defers indefinitely. **The size of that move is not estimated and must not be
guessed.**

**The index-to-fund gap, in its own column.** These are index-like series, not funds:
weighted expense ratio plus non-recoverable withholding is about **13.3 bp/yr**. It cannot
change the ranking, because it is charged on assets held rather than on trades and cancels
in every paired difference. **It is decision-relevant because it is larger than the entire
predicted rebalancing bonus and about twelve times the largest transaction cost any policy
paid.** The withholding figures inside it are an **assumption with no retrieved source**.

---

## 3. The four questions the experiment asked

### Does `gamma_star` match the closed form? Yes, almost exactly

| Pair, 50/50 | Predicted, bp/yr | **Realised** | Error |
| --- | ---: | ---: | ---: |
| US \| developed ex-US | 12.5 | **12.7** | +0.2 |
| US \| emerging | 25.5 | **25.5** | +0.0 |
| Developed ex-US \| emerging | 21.2 | **21.1** | −0.1 |
| **Portfolio, 60/30/10** | **17.69** | **17.78** | **+0.09** |

Continuous and discrete-monthly predictions are indistinguishable at this frequency, which
is the closed form's own statement that frequency is second-order, confirmed. **The
diversification-return identity was not used as evidence anywhere**, and the code says so
in its own output.

### Does the realised advantage fall inside the predicted band? No

| Pair, 50/50 | Realised, bp/yr | Predicted, **equal drift** | Realised drift gap | Predicted **at that drift gap** | Inside? |
| --- | ---: | ---: | ---: | ---: | --- |
| **US \| developed ex-US** | **−62.9** | +0.5 | **+4.34 pp/yr** | **−70.5** | **No** |
| US \| emerging | −1.5 | +1.9 | +2.53 | −21.7 | Yes |
| Developed ex-US \| emerging | +6.9 | +1.3 | −1.82 | −11.3 | Yes |
| **Portfolio, 60/30/10** | **−38.7** | — | — | — | — |

**The gap is the drift gap, and it is diagnosable to a single number.** The closed form's
break-even is exactly `drift gap = gamma_star`, and it is horizon-free. For US against
developed ex-US the realised drift gap was **4.34 pp/yr against a `gamma_star` of 12.5 bp —
a factor of 35.** Extending the closed form to a non-zero drift gap predicts **−70.5 bp/yr**
against a realised **−62.9**. **The theory is not wrong. Its equal-drift special case is
what was being quoted, and that special case does not describe two real equity regions.**

### Is `kappa_t` serially dependent? Yes, positively — the crux

This, not the diversification-return statistic, is the diagnostic that decides whether
rebalancing can add value. Rebalancing is short relative-performance continuation, so
**positive** autocorrelation predicts that it loses.

| Pair | `rho_1` | Block-bootstrap 95% | iid null 95% | Ljung-Box(12) *p* | VR(12), *z*₂ | VR(60), *z*₂ |
| --- | --- | --- | --- | ---: | --- | --- |
| US \| developed ex-US | +0.081 | `[−0.021, +0.152]` | `[−0.096, +0.092]` | 0.054 | 1.130, +0.63 | 2.004, **+2.19** |
| US \| emerging | **+0.203** | `[+0.047, +0.297]` | `[−0.098, +0.094]` | **0.0000** | 2.014, **+4.90** | 3.763, **+6.08** |
| Developed ex-US \| emerging | +0.128 | `[−0.040, +0.218]` | `[−0.098, +0.093]` | **0.0000** | 1.236, +0.97 | 1.407, +0.79 |

Variance ratios are Lo–MacKinlay on log relative performance with the
heteroskedasticity-consistent statistic, the only one that should be read here given the
volatility clustering. **Every variance ratio at every horizon in every pair exceeds 1.**
For US against emerging it rises monotonically to 3.76 at five years.

**The mechanism that could make rebalancing profitable — mean reversion in relative
performance — is absent from this sample. Its opposite is present.** That is a structural
explanation for the verdict, not a description of one unlucky path.

Two honest qualifications. The block-bootstrap interval is attenuated at lags approaching
the frozen 24-month block, so those intervals are conservative. And the Politis–White
automatic lengths (2.0, 6.8, 10.5 months) are reported as a **diagnostic only** — the block
was frozen before the run and a data-chosen block would have been a tuned parameter.

### Where does the data contradict the theory?

**The 68.27% floor does not survive contact with real drifts.** Realised frequencies over
overlapping rolling windows:

| Pair | 5 yr | 10 yr | 20 yr | 30 yr |
| --- | ---: | ---: | ---: | ---: |
| US \| developed ex-US | 21.6% | 24.9% | 28.2% | **0.0%** |
| US \| emerging | 22.2% | 24.3% | 95.0% | 41.0% |
| Developed ex-US \| emerging | 59.0% | 69.8% | 61.3% | 95.1% |

Nine of twelve cells fall below the theoretical floor and six below half of it. **The
windows overlap and are not independent observations** — a 30-year window in a 35-year
sample has 61 distinct start months, and the 0.0% and 95.1% cells are each close to a
single realisation. But no amount of dependence turns 0 of 61 into evidence for a 68%
floor.

**Returns are not lognormal.** Monthly `kappa` carries excess kurtosis of 0.86 to 1.51, and
Ljung–Box on `kappa**2` gives *p* down to 7.8 × 10⁻³² — overwhelming volatility clustering
in all three pairs, which the GBM model behind the closed form has none of. **Notably
`gamma_star` survived both violations intact**, so what the non-normality damages is the
*distribution* of the outcome, not its centre.

**The 2000s–2010s era is the only one that supports rebalancing, and it supports it
loudly.** Diagnostics, never independent observations, certainty equivalent only:

| Era | Annual | Monthly | Threshold 25% | Cash-flow-directed |
| --- | ---: | ---: | ---: | ---: |
| 1991–1999 | −0.184 | −0.610 | −0.300 | −0.324 |
| **2000–2019** | **+0.575** | **+0.490** | **+0.564** | **+0.290** |
| 2020–2025 | −0.020 | −0.028 | −0.020 | −0.098 |
| **Full sample** | **−0.199** | **−0.339** | **−0.213** | **−0.373** |

A reader who saw only the middle row would conclude that annual rebalancing is worth
+0.575 pp/yr and clears the threshold twice over. **It is one twenty-year window inside a
thirty-five-year sample, bracketed by two windows of the opposite sign, and the rejection
rule requires two of three eras precisely so this cannot be reported as a finding.**

---

## 4. Hostile tests

Every declared test, net-pessimistic, pp/yr against buy-and-hold. **Nothing rescues any
policy**, and the smallest gap any test leaves to the +0.25 threshold is 0.355 pp/yr.

| Test | Annual | Monthly | Threshold 25% | Cash-flow-directed |
| --- | ---: | ---: | ---: | ---: |
| Baseline | −0.199 | −0.339 | −0.213 | −0.373 |
| Quadruple every cost | −0.215 | −0.376 | −0.221 | −0.373 |
| Remove 2008–2009 | −0.249 | −0.390 | −0.243 | −0.267 |
| Remove 2020 and 2022 | −0.227 | −0.388 | −0.242 | −0.409 |
| Remove the leading policy's best year | −0.275 | −0.416 | −0.289 | −0.407 |
| **Annual anchor moved to June** | **−0.388** | −0.403 | **−0.130** | −0.287 |
| **Annual anchor moved to March** | **−0.345** | −0.462 | −0.347 | −0.476 |
| US weight ±10 pp | −0.146 / −0.239 | −0.262 / −0.394 | −0.096 / −0.182 | −0.351 / −0.381 |
| Threshold band 20% / 30% | — | — | −0.165 / −0.105 | — |
| **Zero cash flow** | −0.199 | −0.339 | −0.213 | **0.000** |
| Contribution tracking current wealth | −0.199 | −0.339 | −0.213 | −0.459 |

Three are worth naming. **Zero cash flow makes the cash-flow-directed policy identical to
buy-and-hold to the last decimal**, which is the accounting check the specification
predicted in advance. **The two-period identity `R_rebal − R_hold = −w₁w₂κ₁κ₂` reproduces
to 1.0 × 10⁻¹⁶**, so the simulation's accounting does what the algebra says. And **the
annual policy's result moves by 0.19 pp/yr across a December, a June and a March anchor** —
as large as the effect being measured, **so a calendar rebalancing result of this size is
partly a month artefact and should never be quoted without its anchor.**

**One declared hostile test was not run.** A *further* one-month execution delay for the
threshold policy is not implementable through the frozen `core.rebalance` API, which
already executes every decision on the next period's return. It is recorded as an open item
rather than quietly omitted.

---

## 5. Verified, assumed, open

**Verified.** The `gamma_star` closed form on real data to 0.1 bp. The `kappa` sign and its
significance. The two-period identity to machine precision. The `Mkt-RF + RF`
reconstruction as an identity, with the shared US bill enforced by a hard check. That
`Developed_5_Factors` includes the US. That the cash-flow-directed policy degenerates to
buy-and-hold at zero cash flow. In §1, the exact condition, the pathwise straddle identity,
the closed-form probability, the horizon-free break-even, and the Chambers–Zdanowicz
fixture and its extension.

**Assumptions.** `gamma = 3` is a declared preference; a different `gamma` is a different
specification, which is why decision 0008 froze a *new* specification for Experiment 010
rather than editing the old one. Starting weights are pinned to approximate global market
capitalisation — an external anchor chosen because sample first moments had already been
seen while diagnosing the mislabelled dataset, and **that sequence is recorded in the
specification's freeze note.** The withholding figures are assumptions with no retrieved
source. Market impact is omitted by declared choice, at retail scale. In §1: returns are
lognormal with constant parameters and no jumps, with no taxes, costs or cash flows — **all
of which fail in the direction that reduces the measured advantage.**

**Open.**

1. **Would a daily source change the threshold policy?** The data is monthly, so intramonth
   breaches are invisible and the 25% band fired only 12 times in 35 years.
2. **Would an after-tax test change the ranking, or only the level?** The direction is
   clear and the magnitude is not.
3. **Does the positive `kappa` autocorrelation persist out of sample?** Measured on one
   35-year window; a cross-sectional-momentum reading would be a different experiment with
   its own multiple-testing family.
4. **What would the answer be for genuinely uncorrelated sleeves?** Every pair here
   correlates 0.72 to 0.79 in logs. **Whether a real, investable, low-correlation pair with
   *equal* drift exists is the only condition under which any of this could pay, and no
   such pair was tested.**

**Reproducibility.**
`cd research && uv run python -m portfolio_edge.experiments.exp_003_rebalancing --view-results`.
Source vintages are pinned by sha256 and a mismatch aborts. Retrieval date **2026-08-12**,
seed 20260813. Every figure is PRETAX.

---

## 6. The sign reverses on a longer window, exactly where the theory says it should

`as of 2026-08-16`. **Scoping only** — annual, real, local-currency, gross of cost and tax,
run after the experiment above and not under a frozen specification.

The [16-country long-horizon data](evidence-base.md) landed after this experiment and
permits the same question over 149 years instead of 35. Against **US versus an equal-weight
ex-US basket, held 60/40**, deflated by each country's own CPI:

| Window | US geo | ex-US geo | **drift gap** | corr | **`gamma_star`** | gap ÷ `gamma_star` | rebalanced − drifting |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1871–2020 | 6.82% | 5.80% | +1.02 pp | +0.59 | 25.7 bp | 4.0× | **+12.2 bp/yr** |
| **1963–2020** | 6.28% | 6.22% | **+0.05 pp** | +0.75 | **17.2 bp** | **0.3×** | **+17.9 bp/yr** |
| 1991–2020 | 7.67% | 7.25% | +0.42 pp | +0.82 | 15.5 bp | 2.7× | — |

**This is not a contradiction of §3; it is §3's own diagnostic, evaluated where it comes out
the other way.** The experiment above measured a drift gap of **4.34 pp/yr against a
`gamma_star` of 12.5 bp — 35 to 1** over 1991–2025 on US against developed ex-US, and
predicted the loss to within 8 bp. From 1963 the same comparison against an equal-weight
ex-US basket gives **0.3 to 1**, the break-even condition `drift gap < gamma_star` is
satisfied, and rebalancing wins. The rejection is a finding about **a 35-year window in
which one region ran away**, not a law.

The 1871 row wins while its ratio is 4.0×, which looks wrong and is not. The asymptotic
condition is `g_p > max_i g_i`, and here `g_p = 6.68%` against the US's 6.82%, so
buy-and-hold *should* win **eventually**. It has not won yet at 149 years, because
convergence is `M(T) + O(1)` and therefore slow — which is §1's "horizon is first-order"
statement showing up as a measurement.

**Three limits before anyone quotes this.** It is 58 annual observations in the decisive
row, against 420 monthly ones above. It is **gross** — the experiment above charges costs
inside the simulation and this does not, though at 0.3 to 1.2 bp/yr costs cannot flip a
12–18 bp result, and tax could if it were run in a taxable account. And the near-equal
drift from 1963 is **known only in retrospect**; nobody could have asserted it in 1963.

**What actually matters here is not the 12 to 18 basis points.** It is that the drifting
60/40 ended the century at **86.3% US**. Buy-and-hold does not hold a global portfolio; it
holds whichever market won, at the moment the [country ladder](setting-the-equity-share.md)
says concentration is the thing to avoid. Consequence 2 below was already the right
conclusion, and this strengthens it: **rebalance to keep the promise, and expect the return
contribution to be a rounding error of either sign.**

---

## Consequence for this repository

1. **Rebalancing is `rejected` as a source of return *for this experiment's window and
   universe*, and the rejection is stronger than the
   [edge budget](expected-edge-decomposition.md) assumed.** That page books +2.4 bp/yr
   against the stated index; the measured figure over 35 years is **−38.7 bp/yr** on the
   portfolio and **−62.9** on the US/developed-ex-US pair. **The budget line is an
   equal-drift upper bound that a real drift gap removes.** §6 finds **+12 to +18 bp/yr**
   over 1871-2020 and 1963-2020 on a different universe and basis, which is the same
   theory evaluated where the drift gap is small. **Neither sign is worth building on: the
   effect is a rounding error in both directions.**
2. **Rebalancing is retained as a risk-control policy, which is what it demonstrably is.**
   It held exposure within 0.6 to 3.1 percentage points of target against buy-and-hold's
   14.8, for 0.3 to 1.2 bp/yr. **That is a statement about keeping a promise, not about
   return, and it is the only claim this evidence supports.**
3. **Do not build a rebalancing-bonus feature.** §1 forbids it on theory; §2 forbids it on
   data and supplies the number a tool would have to show: **−0.2 to −0.4 pp/yr with a 95%
   interval reaching −1.9, and a worse maximum drawdown.**
4. **The drift gap, not the excess growth rate, is the quantity that decides.** Any future
   code reasoning about constant-weight portfolios must carry `drift gap versus
   gamma_star` as an explicit, reported comparison. **On this data it was 35 to 1 against;
   on 1963-2020 US against equal-weight ex-US it is 0.3 to 1 in favour** (§6). The rule
   travels, the verdict does not, and quoting the verdict without its window is the error
   this line exists to prevent.
5. **`gamma_star` is safe to compute and display; the probability attached to it is not.**
   Displaying the 68.27% floor without the drift gap beside it would be the most misleading
   thing this repository could ship on the subject.
</content>
