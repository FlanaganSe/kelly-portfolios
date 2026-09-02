# Rebalancing: a maintenance policy, and how to run one

**Two questions, and they have different answers.**

**A. Is rebalancing a source of return?** Does any policy — annual calendar, monthly
calendar, a frozen relative threshold, or cash-flow-directed — beat buy-and-hold from
identical starting weights and cash flows, on a declared objective and net of the costs it
actually pays? **Part A** answers this: `rejected` on the window tested, with the
mechanism measured. Out of scope there: leverage, financing, taxes.

**B. Can the stacked candidate actually be operated?** In what units is its target stated,
what happens when a portfolio-level target has to be restored using only trades inside two
of three accounts, what policy should the investor run, and how many lines should they
hold? **Part B** answers this, and it is where the operating decisions are made. Its
scope, assumptions and evidence level are stated at its head.

**Decisions informed.** What a rebalancing feature would be allowed to claim (Part A); the
procedure the investor follows, the placement that makes it feasible, and the line count
(Part B).

---

## Conclusion, Part A: rebalancing as a source of return

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

## Conclusion, Part B: operating the stacked candidate

**The target is a vector of eight capital weights, and nothing else is ever typed.** The
portfolio's exposure table adds to 132.16% because it is levered; a brokerage screen adds
to 100%. Every attempt to reconcile those two numbers by scaling the exposure table
destroys about a quarter of the trend sleeve — **−7.30 pp of trend one way, −6.92 the
other**, on a 30 pp target ([B1](#b1-the-target-is-a-capital-weight-vector-the-exposure-table-is-not)).

**Rebalancing across accounts has an exact feasibility condition, and it is one number.**
The portfolio target is restorable without a taxable sale **if and only if the taxable
account holds no fund above its portfolio target weight**. The distance to that wall is
`min_i (target_i − taxable_i)`, the *headroom* — and at target it is simply how much of
that fund sits somewhere you are allowed to sell.

**The published placement plan has zero headroom, and that costs 0.28 bp/yr.** The plan in
`src/content/placement.ts` puts VTI entire in the taxable account, so
`taxable_VTI = target_VTI = 20.0` and the condition fails on that line. It failed in **127
of 427 months**. The plan is nonetheless close to right, because the failure is **shallow**:
forced-realisation tax measured inside an executable rule is **0.49 bp/yr**, against a plan
worth **+38.21 bp/yr** over pro-rata placement. **The correction is one part in a hundred
and forty of the thing being corrected** ([B2](#b2-rebalancing-across-three-accounts)).

**The joint optimum — recurring drag plus forced realisation, minimised together — is one
percentage point of headroom, and the whole frontier spans about a basis point a year.**

| Minimum headroom | Recurring drag | Forced tax | **Total** | Infeasible months | Worst of five stresses |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0.00 — the published plan | **19.51** | 0.49 | **20.00** | 127 | 21.92 |
| **1.00 — recommended** | 19.72 | **0.00** | **19.72** | 38 | 20.82 |
| 3.00 — the minimax choice | 20.61 | 0.00 | 20.61 | 12 | **20.61** |
| 5.42 — the ceiling | 22.04 | 0.00 | 22.04 | 0 | — |

**Neither corner solution is right, and the disagreement is nearly free.** Keep the
placement plan's logic — it is the same knapsack this page solves, at zero constraint —
and move **one percentage point each of VTI and AVLV out of the taxable account**, which
requires a third line there and lands on **taxable = VTI 19.00, AVLV 14.00, VEA 0.33**.
That buys back 89 of the 127 infeasible months for **0.21 bp/yr**. The obvious cheaper fix
— moving VTI alone — **does not work**: VTI and AVLV target 35 pp between them and must
hold 33.33, so two lines can never share more than 0.83 pp of slack, and at 0.67 pp the
constraint simply moves to AVLV.

**Policy: review once a year, act on a 25% relative band, trade only inside Roth and
traditional.** That is **0.4 rebalances a year, 2.9 trades a year, 0.10 bp/yr of spread,
zero tax, mean exposure error 0.94 pp**. Against buy-and-hold it is **−0.09 pp/yr of
growth with an MDE80 of 1.81** — `unresolved`, exactly as Part A predicts, and the
decision rests on exposure control, which is not close ([B3](#b3-what-policy-and-what-is-it-worth)).

**On line count, the operating axis barely votes.** Eight lines cost 0.4 rebalances and 2.9
trades a year to run; the burden is the positions and their placement constraints, not the
trading. Every small international line is sheltered under the corrected ranking, so **none
of them costs any headroom** — the constraint binds only on the two US lines that have to
absorb the whole taxable account. **The cut worth making is DFIV, on the breadth work's
finding that it does not earn its place once its own −3.80 pp/yr alpha is charged, which is
a change of intent rather than a simplification; and IDMO, the one line resting on a
premium that clears a multiple-testing threshold, should be kept.** Six tickets: RSST 30,
VTI 20, AVLV 15, a total-international fund at 25, IDMO 5, AVES 5
([B4](#b4-the-complexity-budget)).

**The moments this will be hardest to hold are measured and long.** The US value tilt has
been **54.3% behind the US market for 17.7 years and has not recovered**; international is
**69.0% behind over 18.2 years**; the stacked wrapper less the equity it displaces spent
**11.2 years and 59.9% behind** on the live-fund trend basis. **All three are longer than
most people's stated patience**, which is why the precommitment has to be written before
the stretch, not during it ([B5](#b5-the-moments-this-will-be-hardest-to-hold)).

---

# Part A. Is rebalancing a source of return?

`Experiment 003`, confirmatory, frozen specification. Everything under this heading is
PRETAX and scoped to 1991-2025 regional equity except where §6 says otherwise.

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

Reproduced and extended in
[`studies/chambers_zdanowicz.py`](../../research/src/portfolio_edge/studies/chambers_zdanowicz.py).
Their Exhibit 4 fixture reproduces exactly — `E[W_T] = 1.050625` for both policies, their
long-rebalanced/short-buy-and-hold trade earns **exactly zero** — and the result
*generalises*, which strengthens their case: for returns independent across time,
`E[W_reb] = (1 + w'mu)**T` and `E[W_hold] = sum_i w_i (1 + mu_i)**T` coincide at equal
`mu_i` and, by strict convexity, leave buy-and-hold strictly ahead otherwise. **An investor
who genuinely maximises expected terminal wealth should never rebalance.**

**But their dismissal does not reach log wealth.** Their 1.874% and 1.867% are
`E[W**(1/T)] − 1`, not expected log growth, which is 1.2346% and 1.2201%; their "arbitrary
nonlinear transformation" objection is aimed at that annualisation, and their own footnote
6 says so — *"the magnitude of the effect is driven by the time it takes the planet to
orbit the sun."* **`E[log W]` contains no annualisation.** Extending their tree — both
policies recombine and the exhibit is `O(T**2)`, so the stated obstacle is not real — the
rebalanced portfolio's expected log growth is **constant at 1.2346% at every horizon**
while buy-and-hold's falls to `max_i g_i`, here exactly 0%. **Their 12-period gap of 12 bp
is the size of the effect at the horizon they stopped at, not the size of the effect.**

**What a log investor gains is exactly a mean-preserving contraction.** At `mu = 7%`,
`sigma = 20%`, `rho = 0`, `T = 30`: expected terminal wealth 8.1662 for **both**; variance
54.82 rebalanced against 77.36 held, a **29.1% reduction at an unchanged mean**. That is
the whole economic content of the diversification return — worth having, priced in tens of
basis points, and not an arbitrage. Their deciding example prices the disagreement: a log
investor pays **$268.12 per $10,000, 1.32%**, to decline a gamble whose expected value is
23% higher. That is a preference, not an error.

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

**`Developed_5_Factors_CSV.zip` includes the United States**, despite having been
registered here as "developed markets ex-US aggregate". Regressing its `Mkt-RF` on the US
and Developed-ex-US series gives **0.460 and 0.549, summing to 1.009**; beside a US sleeve
it would have double-counted half the US market.

**One risk-free rate is correct for all three regions, and it is the US bill**, because
French's international page defines every region's market factor against the US one-month
bill. So `Mkt-RF + RF` is an identity, the experiment raises if the three `RF` columns ever
disagree beyond printed precision, and the residual reconstruction error is the source's
two-decimal printing at **0.24 bp/yr** — small, but the same order as the predicted effect,
and it cancels exactly in `kappa`.

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

**Tax is not modelled here and no haircut is applied.** This simulation holds no tax lots,
so it cannot know a basis and may not price a realisation. Qualitatively the missing test
moves the ranking *further against* rebalancing, because every rebalance realises gain that
buy-and-hold defers indefinitely. [Part B](#b2-rebalancing-across-three-accounts) prices
that realisation for the stacked candidate — **1,170 bp of the amount traded at a ten-year
holding period** — and then shows how to run a policy that never pays it.

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
2. **Would an after-tax test change the ranking, or only the level?**
   [Part B](#b3-what-policy-and-what-is-it-worth) settles the operating half — a policy
   confined to sheltered accounts pays **zero** realisation tax, so for that policy the
   question does not arise. It remains open for a policy that must sell in taxable.
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

# Part B. Can this portfolio be run?

`as of 2026-08-22`. **Evidence level: explore.** Not a registered experiment, no frozen
falsifier, no holdout consumed. Executable record:
[`studies/rebalancing_operations.py`](../../research/src/portfolio_edge/studies/rebalancing_operations.py),
pinned by `test_studies_rebalancing_operations.py`; tables regenerate with
`cd research && uv run python -m portfolio_edge.studies._rebalancing_operations_tables`.

**The portfolio.** The stacked candidate of `src/content/portfolios.ts`: RSST 30, VTI 20,
AVLV 15, DFIV 10, VEA 10, IDMO 5, IEMG 5, AVES 5, as **capital** weights. It is **eight
lines, not nine** — the count reaches nine only by listing the wrapper's trend leg
separately from its equity leg, which is the units error B1 exists to prevent.

**The investor.** Roughly a third of wealth in each of Roth, traditional and taxable, long
horizon, contributing.

**Assumptions, kept separate from what is measured.**

- Account thirds are *balances*. In after-tax dollars, at a 24% future ordinary rate and a
  ten-year taxable holding period, they are **Roth 37.84%, traditional 28.76%, taxable
  33.41%** — the taxable share, the one that constrains rebalancing, is **larger** after
  tax, not smaller.
- **Placement is another page's decision and this page defers to it.**
  `src/content/placement.ts` holds the fund-by-fund tax profiles and the shelter ranking;
  this page reconstructs that ranking from the same filed inputs — reproducing all eight
  funds' published priorities at all three brackets to within 0.01 bp — and then adds the
  one thing that page does not price, which is whether the resulting plan can be
  rebalanced. Every figure below is on the corrected ranking, in which the partly-qualified
  international dividends make those funds dearer to hold in taxable than fully-qualified
  US ones.
- Sheltered accounts are treated as able to hold any of the eight funds. A 401(k) menu that
  cannot is a real constraint and would reduce every feasibility figure below.
- Contributions are 5% of initial wealth a year, flat nominal — the convention frozen in
  `exp_003_rebalancing.yaml`, so the two halves of this page are comparable.
- Costs are 2.0 bp one-way on traded notional, charged inside the rule; 8.0 bp is reported
  as a sensitivity. Long-term capital gains are 23.8%.

**What the return series are.** Index proxies, not funds: French US / developed ex-US /
emerging markets and their large-value portfolios, French developed ex-US `WML` at an
assumed 0.35 loading for IDMO, and RSST built as `RF + 1.072 x (US Mkt-RF) + AQR TSMOM −
99 bp`. **1990-11 to 2026-05, 427 months.** AQR's `TSMOM` states no fee, transaction-cost
or financing basis anywhere in its workbook, so it is gross of all of them by omission;
every figure that depends on the trend leg's *level* is therefore reported on three bases —
vendor gross, the **+2.84%/yr** an equal-weight index of 46 live managed-futures funds
earned net of their own fees over the 78 months on which they can be compared
([live managed futures](live-managed-futures.md)), and zero excess over cash.
**No return claim is made on these proxies.** What is measured is exposure control, trade
counts, realised gain and tax, which are properties of the rule rather than of the proxy's
mean.

---

## B1. The target is a capital-weight vector. The exposure table is not.

Those eight capital weights deliver:

| Notional kind | pp of capital | where it comes from |
| --- | ---: | --- |
| US equity | **67.16** | 20 VTI + 15 AVLV + 30 × **1.072** from RSST's equity leg |
| Developed ex-US equity | 25.00 | DFIV 10 + VEA 10 + IDMO 5 |
| Emerging equity | 10.00 | IEMG 5 + AVES 5 |
| Managed futures | **30.00** | RSST's trend leg, 1.000 per dollar |
| **Gross notional** | **132.16** | equity notional alone is **102.16** |

**Two things follow, and both are actionable.**

**"US 65%" is a capital weight and it delivers 67.16 pp of US equity notional.** To deliver
exactly 65 the weights are RSST 30, VTI **18.77**, AVLV **14.07**, with **2.16 pp left in
cash**. That 2.16 pp is not rounding: it is the entire difference between believing you
hold 100% equity and holding 102.16%.

**The 1.072 is a dated filing fact, not a constant.** It is 74.09% of net assets in a
physical S&P 500 fund plus 33.1% in E-mini futures, read from the 2026-04-30 Form N-PORT.
Reread on 2026-09-01 from the same filing's own contract values, the E-mini line is 30.94%
and the leg 1.050 (delta −0.05, gross 2.05), which is what `src/content/shelf.ts` now
carries; the tables on this page keep the 1.072 they were built on
([part A](portfolio-for-one-investor.md) §1). It moves as the futures leg moves. **A target stated in notional therefore changes every
quarter without the investor touching anything; a target stated in capital does not.**

### What goes wrong when the target is stated in exposure

Both natural attempts to rebalance in exposure units fail the same way, and both cost about
a quarter of the trend sleeve. Each requests more than a dollar of capital — 132.2% and
130.0% respectively — so the brokerage forces a pro-rata scale-down, and the scale-down is
applied to exposures that are then read as capital.

| What the investor types | Trend delivered | US equity delivered | Worst error |
| --- | ---: | ---: | ---: |
| The exposure table, scaled to fit a 100% screen | **22.70** (−7.30) | 75.15 (**+7.99**) | +7.99 pp US equity |
| Trend counted beside a full 65/35 equity book | **23.08** (−6.92) | 63.20 (−3.96) | −6.92 pp trend |

The first double-counts the wrapper's equity leg, which is already inside the 67.16 line,
and so buys that equity twice. The second treats trend as an allocation *beside* the equity
book rather than inside it. **In both, the trend sleeve is the line that shrinks, because
it is the only one with no unlevered substitute to absorb the scaling.** Gross exposure
lands at 124.3% and 124.7% against an intended 132.2%.

**Why the trap is currently half-invisible.** RSST's *trend* leg is exactly 1.000 per
dollar, so 30% of capital happens to be 30 pp of trend notional and a capital sheet is
accidentally right on that line. Its *equity* leg is 1.072, so the same sheet is wrong on
that one by 2.16 pp. Replace the wrapper with one carrying a 1.5x trend leg — the shelf
already holds funds with different ratios — and the identical sheet delivers **45 pp** of
trend. The discipline has to be the rule, not the coincidence.

### The procedure, in the units to type

1. **Hold the target as eight capital weights summing to 100.** That vector, and only that
   vector, is what is entered anywhere.
2. **Once a year, read each fund's current leg ratios from its latest filing** and
   recompute the notional table. Compare it with the intended exposures. **If they
   disagree, change the capital weights.** Never rebalance towards a notional number.
3. **Never write a sheet that mixes the two.** A row reading "managed futures 30%" and a
   row reading "VTI 20%" are in different units and cannot be added, compared, or
   rebalanced against one another — which is the warning `src/content/portfolios.ts`
   already carries, stated here as arithmetic.

---

## B2. Rebalancing across three accounts

No single account holds a miniature of the portfolio, so restoring one account to its own
targets is not restoring the portfolio. The question is what the *portfolio* target costs
when only two of three accounts can be traded without realising gain.

### The feasibility condition, exactly

Let `v_i` be what the taxable account holds of fund `i` as a share of total wealth, and
`w*_i` the portfolio target. Sheltered accounts can be reallocated freely, so the set of
portfolios reachable without a taxable sale is `{v + s : s >= 0, sum(s) = 1 − sum(v)}`.
Therefore

> **`w*` is reachable if and only if `v_i <= w*_i` for every fund.**

That is exact, not a heuristic, and it collapses to a single number to watch:

> **Headroom = `min_i (w*_i − v_i)`.** Non-negative means the target is restorable with
> sheltered trades alone. Negative means it is not, whatever else the investor does.

**And at target it needs no arithmetic at all.** Since `w*_i = v_i + s_i`, the headroom on
a line *is* the sheltered holding of that line. **The headroom on a fund is however much of
it sits somewhere you are allowed to sell.** The whole condition reduces to: every fund
must be present in Roth or traditional, and the one with the smallest presence there is the
one that will break first.

`nearest_reachable()` projects the target onto the reachable set, so when headroom goes
negative the *size* of the miss is measured rather than asserted. The projection is checked
against a brute-force search over the reachable set in the tests.

**The consequence that decides the placement.** A placement that fills the taxable account
to exactly a fund's target weight has **zero headroom on that fund**, and the first month
that fund outperforms, the portfolio target stops being reachable. The published plan does
exactly that with VTI, at 20.00 pp of a 20.00 pp target.

**How thin that is, in market terms.** With one fund held at share `a` of wealth entirely
in taxable and everything else at `b`, its portfolio share reaches a limit `L` after a
cumulative relative outperformance of `L·b / (a(1−L)) − 1`. Two limits matter and they are
different questions: the **condition** breaks when the share passes its *target*, while the
**band** does not fire until it passes the target by 25%.

| Taxable VTI | Budget to the condition, at 20.0% | to 22.5% | Budget to the band edge, 25.0% |
| --- | ---: | ---: | ---: |
| **20.00 — the published plan** | **0.0%** | 16.1% | **33.3%** |
| 19.00 — recommended | **6.6%** | 23.8% | 42.1% |
| 17.00 — three points of headroom | 22.1% | 41.7% | 62.7% |

**This is why the plan survives its own zero headroom.** The condition fails the moment VTI
outperforms at all, but *nothing needs doing* until VTI is a quarter above target, and by
then the sheltered accounts have usually recovered the room through returns or new
contributions. **The band and the contribution stream are substitutes for headroom**, which
is why the joint cost below is so flat and why the no-contribution case is the one where
the argument for headroom disappears.

### What a forced taxable trade costs

Not the spread. The realised gain times the rate, charged inside the rule:

| Lot held | Unrealised gain, share of value | Tax, bp of the trade | Spread, bp | Ratio |
| --- | ---: | ---: | ---: | ---: |
| 5 yr at 7% | 28.70% | 683 | 2.0 | **342×** |
| 10 yr at 7% | 49.17% | **1,170** | 2.0 | **585×** |
| 20 yr at 7% | 74.16% | 1,765 | 2.0 | 882× |
| 30 yr at 7% | 86.86% | 2,067 | 2.0 | 1,034× |

**So the question is never "how expensive is this trade". It is "can this trade be
avoided" — and then "how often".** That second question is what decides this section, and
it is the one neither this page nor the placement page had answered.

### The published placement plan, tested against the condition

`src/content/placement.ts` was rewritten on 2026-08-22 and its conclusion is not the one
this study was asked to assume. **Every international line now outranks every US equity
line for the shelter, and VTI is last at all three brackets.** The reason is a single
corrected input: the old table took the qualified-dividend fraction as 1.00 for every fund,
and the filings say **VEA 66.27%, IEMG 34.82% and AVES 44.48%** of qualified dividend
income, with IDMO at 25% before its long-term gain distribution. The ordinary remainder is
17 percentage points of rate dearer at the top bracket, and that reverses the ranking.

This page reproduces that page's published `priorityBp` for **all eight funds at all three
brackets, to within 0.01 bp**, from the filed yields and qualified fractions rather than by
copying the table — which is what licenses reusing its ranking here. The bracket pairs
implied by that reconstruction are **23.8/40.8, 18.8/35.8 and 15.0/24.0**.

| Bracket | Shelter priority per dollar, bp/yr — lowest goes to taxable first |
| --- | --- |
| 23.8% qualified / 40.8% ordinary | VTI 25.4, AVLV 42.1, VEA 56.0, DFIV 63.7, IEMG 64.3, AVES 84.0, IDMO 148.2, **RSST 361.8** |
| 18.8 / 35.8 | VTI 20.1, AVLV 33.3, DFIV 43.6, VEA 44.1, IEMG 51.5, AVES 64.4, IDMO 126.2, RSST 315.4 |
| 15.0 / 24.0 | VTI 16.0, AVLV 26.6, DFIV 28.2, VEA 28.6, IEMG 28.6, AVES 32.2, IDMO 83.3, RSST 213.8 |

**The plan and this page are the same optimisation.** Total drag is
`sum_i target_i × sheltered_i + sum_i taxable_i × priority_i`, and the first term does not
depend on the placement — so minimising drag means filling the taxable account from the
lowest priority upward, which is a continuous knapsack whose greedy solution is exact. At a
minimum headroom of **zero** that returns **VTI 20.00 and AVLV 13.33 in taxable**, which is
the published plan to the decimal. **The two pages were never using different methods. They
were solving the same problem at different constraint levels**, and the test suite asserts
that correspondence rather than asserting it in prose.

**Applying the condition to it.** `taxable_VTI = 20.00 = target_VTI`, so **VTI has zero
headroom** and AVLV has 1.67; every other line is entirely sheltered and has its full
target. Over 427 months the plan was **infeasible in 127 of them — 30% of the sample —
with a worst headroom of −5.09 pp**, meaning VTI reached 25.09% of a portfolio targeting
20%. That is the same failure mode this page measured for the placement it was originally
given, and it fires more often, because the US market beat everything else over this window
and VTI is the line that had to sit in taxable.

**But the exposure consequence is small.** Under the recommended policy the disciplined arm
— which refuses to sell in taxable and simply lives with the miss — carries a mean exposure
error of **0.93 pp against 0.94 pp** at five points of headroom. A VTI overshoot of two or
three points, spread across eight lines, barely moves a portfolio-level average. **Frequent
is not the same as expensive, and the honest way to price this is to make the rule sell and
charge it.**

### The joint optimum: drag plus forced realisation

Both arms below hold the same portfolio-level target, so they are comparable. The
disciplined arm never sells in taxable and pays in exposure error; the restoring arm sells
whatever the sheltered accounts could not absorb and pays capital-gains tax on the realised
gain, charged inside the rule out of the portfolio. Annual review, 25% relative band,
wrapper barred from taxable, 23.8% qualified, average-cost basis.

| Minimum headroom | Recurring drag | Forced tax | **Total** | Infeasible months | Taxable account holds |
| ---: | ---: | ---: | ---: | ---: | --- |
| **0.00 — the published plan** | **19.51** | 0.49 | **20.00** | 127 | VTI 20.00, AVLV 13.33 |
| **1.00 — the optimum** | 19.72 | **0.00** | **19.72** | 38 | VTI 19.00, AVLV 14.00, VEA 0.33 |
| 2.00 | 20.17 | 0.00 | 20.17 | 16 | VTI 18.00, AVLV 13.00, VEA 2.33 |
| 3.00 | 20.61 | 0.00 | 20.61 | 12 | VTI 17.00, AVLV 12.00, VEA 4.33 |
| 4.00 | 21.08 | 0.00 | 21.08 | 0 | VTI 16, AVLV 11, VEA 6.00, DFIV 0.33 |
| 5.00 | 21.76 | 0.00 | 21.76 | 0 | VTI 15, AVLV 10, VEA 5, DFIV 3.33 |
| 5.42 — the ceiling | 22.04 | 0.00 | 22.04 | 0 | — |

**One percentage point of headroom is the optimum and it is worth 0.28 bp/yr.** Set against
a placement decision the placement page prices at **+38.21 bp/yr over pro-rata**, that is a
**0.7% refinement**. The plan is not broken; it is one line short of a third holding in the
taxable account.

**The obvious fix does not work, and that is worth knowing.** "Move a point of VTI into the
Roth" leaves AVLV to absorb the freed taxable capacity, so AVLV's headroom falls as VTI's
rises. The best two-line taxable account is **VTI 19.17 / AVLV 14.17 at 0.83 pp**, because
those two lines target 35 pp between them and must hold 33.33 — **1.67 pp of slack to share,
whatever you do.** Tested at 19.00 / 14.33 it delivers 0.67 pp and **126 infeasible months
against the plan's 127**: no improvement at all. **Reaching a full point on every line
requires a third fund in the taxable account**, and the cheapest one is VEA.

**Hostile tests. One point of headroom wins four of five; three points is the minimax
choice.** The embedded-gain rows matter most: an investor who already holds these funds
does not start with a fresh basis, and every realisation figure above assumes they do.

| Test | 0.00 pp | **1.00 pp** | 3.00 pp |
| --- | ---: | ---: | ---: |
| Baseline | 20.00 | **19.72** | 20.61 |
| 40% gain embedded on day one | 20.35 | **19.72** | 20.61 |
| 70% gain embedded on day one | 20.61 | **19.72** | 20.61 |
| A 10% relative band instead of 25% | 21.02 | **20.15** | 20.61 |
| Quarterly review instead of annual | 21.92 | 20.82 | **20.98** |
| No contributions at all | **20.26** | 20.40 | 20.61 |
| **Worst case** | 21.92 | 20.82 | **20.61** |

Two readings. **A wider band and a live contribution stream are substitutes for headroom** —
the plan survives its zero headroom largely because 5%/yr of new money keeps buying the
underweight lines, and the no-contribution row is the only one where zero headroom wins.
And **the entire question is worth 2.2 bp/yr at its widest**, from 19.72 to 21.92, which is
smaller than the uncertainty in almost every other input on this page.

**The wrapper's largest unknown is neutralised by sheltering it.** Its taxable cost is
**361.78 bp/yr per dollar on the recognised reading and 33.72 on the distributed one** — a
factor of eleven, on the same filing, unresolved until its next December distribution. Both
placements above hold it entirely in the shelter, where its cost is **zero on either
reading**, so the plan drag is 19.51 bp/yr under both. **Barring the wrapper from taxable is
not only worth 1.17 bp/yr of expected drag; it makes the biggest open measurement in the
placement problem stop mattering.** The price is that it also halves the headroom ceiling,
from 10.56 pp to **5.42**, because the wrapper is the largest line and removing it from the
taxable account removes the most capacity. At an optimum of 1 pp that ceiling does not bind.

### The recommended placement, line by line

| Fund | Target | Taxable | Sheltered — and therefore the headroom |
| --- | ---: | ---: | ---: |
| RSST | 30.00 | **0.00** | **30.00** |
| VTI | 20.00 | 19.00 | **1.00** |
| AVLV | 15.00 | 14.00 | **1.00** |
| DFIV | 10.00 | 0.00 | 10.00 |
| VEA | 10.00 | 0.33 | 9.67 |
| IDMO | 5.00 | 0.00 | 5.00 |
| IEMG | 5.00 | 0.00 | 5.00 |
| AVES | 5.00 | 0.00 | 5.00 |

Which sheltered account holds what does not affect feasibility, because both trade free.
The placement page decides that on other grounds — required minimum distributions and the
government's share of dispersion in a traditional balance — and this page defers to it.

**The 8.81 bp of foreign tax credit the plan deliberately forfeits is unaffected by this
change**, because the 0.33 pp of VEA that moves *into* taxable recovers a sliver of it
rather than costing more.

### The procedure, across accounts

1. **Compute the portfolio-level weights** across all three accounts. Nothing is ever
   rebalanced account by account.
2. **Send new money first.** Sheltered contributions go to whatever is most underweight.
   **Taxable contributions go to whichever eligible line has the most headroom, not to
   whichever is most underweight** — that split maximises the resulting minimum headroom
   and cannot create an infeasibility. On this sample the two rules were indistinguishable
   and the sign of the difference flips between placements; treat it as a safety property,
   not a measured gain. What *is* measured is that contributions matter more than the
   placement tweak: the no-contribution row above is the only case where zero headroom wins.
3. **Then reallocate the sheltered accounts** to the portfolio target. If headroom is
   non-negative this reaches it exactly; if not, it reaches the nearest point, and the miss
   is what to look at.
4. **Never sell in taxable to rebalance.** Redirect taxable dividends instead of
   reinvesting them, hold specific-identification as a standing instruction, and if VTI is
   stuck above target, let the band absorb it and point the next contribution at the
   shortfall rather than selling now. Over 427 months that discipline cost **0.01 pp of
   mean exposure error** against a rule that sells.

## B3. What policy, and what is it worth?

Three points of headroom, live-fund trend basis, 1990-11 to 2026-05, costs inside the rule.
Every row trades only inside the sheltered accounts and therefore realises **nothing**.
The policy ranking is the same at every headroom level tested, including the published
plan's zero: the placement decides what a policy *can* reach, not which policy to run.

| Policy | Mean exposure error | Max error | Trend notional error, mean/max | Reviews/yr | Trades/yr | Turnover %/yr | Cost bp/yr | Tax bp/yr |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Buy and hold | **6.39 pp** | 9.79 | 24.65 / 39.17 | 0.0 | 0.0 | 0.00 | 0.00 | 0.00 |
| Contribution-directed only | 4.38 | 7.41 | 16.62 / 29.64 | 0.0 | 0.0 | 0.00 | 0.00 | 0.00 |
| Annual calendar | 0.57 | 1.99 | 1.39 / 7.83 | 1.0 | 7.8 | 3.58 | 0.14 | 0.00 |
| Quarterly calendar | **0.21** | **0.92** | **0.54 / 3.12** | 4.0 | **31.1** | 7.17 | 0.29 | 0.00 |
| Relative band 25%, checked monthly | 0.72 | 1.56 | 1.65 / 6.04 | 0.6 | 4.5 | 2.92 | 0.12 | 0.00 |
| Absolute band 5 pp, checked monthly | 0.96 | 2.59 | 1.66 / 4.87 | 0.3 | 2.5 | 2.29 | 0.09 | 0.00 |
| **Annual review, act on a 25% relative band** | **0.94** | 2.19 | 1.96 / 8.75 | **0.4** | **2.9** | 2.37 | **0.09** | **0.00** |
| Annual review, act on a 5 pp absolute band | 1.13 | 2.17 | 2.29 / 7.87 | 0.2 | 1.8 | 1.66 | 0.07 | 0.00 |

**Exposure control is the axis that separates these policies, and it separates them by a
factor of seven.** An untouched portfolio drifted a mean **6.39 pp** per line and reached
**9.79**; its trend notional was a mean **24.65 pp** away from the 30 pp target and reached
**39.17** — the sleeve the whole construction is built around roughly doubles or halves if
nobody touches it. Any of the acting policies holds that to 1-2 pp.

**Contributions alone are not enough.** Directing every dollar of new money at the most
underweight line, and never trading, leaves a mean error of **4.38 pp** and a trend
notional error of **16.62**. Raising the contribution rate to 10%/yr only reaches 3.36 pp.
**Cash flow is a useful first lever and it is not a rebalancing policy for this portfolio.**

**Return is `unresolved`, exactly as Part A predicts.**

| Policy | Growth | vs buy-and-hold | MDE80 |
| --- | ---: | ---: | ---: |
| Buy and hold | 11.501 %/yr | — | — |
| Annual review, 25% relative band | 11.410 | **−0.091 pp/yr** | **1.813 pp/yr** |
| Annual calendar | 11.321 | −0.181 | 1.851 |
| Quarterly calendar | 11.317 | −0.184 | 1.885 |
| Contribution-directed only | 11.294 | −0.207 | 0.615 |

**Every difference is an order of magnitude inside what 427 months can resolve.** The
largest gap is 0.21 pp/yr against a minimum detectable effect of 0.61 to 1.89. Under
[decision 0010](../decisions/0010-bars-carry-a-reopening-condition.md) the verdict on
return is **`unresolved` and may not be stated more strongly**. The decision is made on
exposure control, where the ratio is seven to one and the cost of acting is a tenth of a
basis point a year.

**Costs and the trend basis, as sensitivities.** Quarterly rebalancing costs 0.29 bp/yr at
2 bp one-way and 1.16 at 8 bp — **the spread cannot decide anything here**. The trend
basis, by contrast, moves the drift substantially and never the ranking:

| Trend basis | Buy-and-hold mean error | Buy-and-hold trend notional error, max | Annual policy mean error | Infeasible months at 3 pp | at 5 pp |
| --- | ---: | ---: | ---: | ---: | ---: |
| Vendor gross | 12.12 pp | **65.32 pp** | 0.62 | 0 | 0 |
| Live-fund mean +2.84%/yr | 6.39 | 39.17 | 0.57 | 11 | 0 |
| Zero excess over cash | 4.35 | 23.98 | 0.58 | **53** | 1 |

The trend basis changes how much headroom is *enough*: a trend leg that earns nothing
lets the equity lines run away faster, and three points stops being sufficient. That is the
argument for the minimax choice rather than the expected-cost one, and it costs 0.89 bp/yr.

**On the vendor's own gross series a buy-and-hold trend sleeve ends more than twice its
target notional.** That number is not investable and is quoted only as the upper bound on
how much drift an unmanaged stack can accumulate.

### Does the trend sleeve create a "sell what held up" moment?

Yes, and it is the mechanism that makes rebalancing this portfolio different from
rebalancing a basket of equity regions. Part A's finding is that rebalancing loses when
relative performance *trends*, and every pair it tested correlated 0.72 to 0.79 in logs.
The trend leg does not: it is the one sleeve whose relative performance against the equity
book is not a persistent regional drift. **What the data here does not do is resolve
whether that is worth anything in return** — the wrapper's mean gap over the equity it
displaces is **+2.56 pp/yr against an MDE80 of 5.76** on the live-fund basis, and −0.28
against the same 5.76 at zero excess. **The rebalancing case for the sleeve is an exposure
argument, not a return argument, and this page will not make it into one.**

---

## B4. The complexity budget

**What the eight-line design actually costs to run**, under the recommended policy: **one
review a year, about 0.4 rebalances a year, 2.9 trades a year, 0.09 bp/yr of spread, no
tax.** That is a spreadsheet with eight rows, one annual sitting, and a trade in most but
not all years. **The burden is not the trading. It is the eight positions across three
accounts, the placement constraints each one carries, and the annual re-reading of the
wrapper's filing.**

**What a consolidation costs, measured against the eight-line design over the same 427
months.** Each row drops exactly one decision.

| Cumulative ladder | Tracking error vs the eight-line design | Decisions removed |
| --- | ---: | --- |
| 8: as designed | — | — |
| 7: IDMO into VEA | 0.20 %/yr | the ex-US momentum tilt |
| 6: also AVES into IEMG | 0.35 | the emerging value tilt |
| 5: also DFIV into VEA | 0.71 | the ex-US value tilt |
| 3: also AVLV into VTI | **1.96** | the US value tilt |

**Read that ladder for scale only.** Tracking errors do not add, so its increments are not
the cost of the lines they drop — dropping DFIV alone costs **0.58 %/yr**, not the 0.36 the
ladder's arithmetic suggests. Attribution needs single cuts.

### Tracking error is the wrong axis for this decision

The obvious reading of that table is to take the three cheapest cuts — IDMO, AVES and
DFIV — for 0.71 %/yr between them, and hold five sleeves as four tickers. **That reading is
wrong on both of the axes that decide it, and this section exists to say why.**

**Headroom does not argue for fewer lines here.** The tempting argument is that a 5% line
placed half in taxable has only 2.5 pp of headroom, so small lines die first. Under the
shelter ranking **no small international line goes into the taxable account at all** — they are the four
*highest* shelter priorities in the portfolio after the wrapper, at 148.2, 84.0, 64.3 and
63.7 bp per dollar against VTI's 25.4. A line that is never held in taxable costs exactly
zero headroom. **The constraint binds only on VTI and AVLV, the two lines that have to
absorb the whole taxable account, and nothing about the line count changes that.**
Consolidation does still raise the *ceiling* — 5.42 pp at eight lines, 9.17 at five, both
with the wrapper barred — but at an optimum of one point the ceiling is not close to
binding. **The operating case for fewer lines is real but worth well under a basis point a
year, which is not enough to decide anything.**

**The edge argument points the other way, and specifically at IDMO.** The
[construction tournament](construction-tournament.md) finds the **tilt basket** is the only
component of the whole proposal that clears its own detection floor: **+0.79 pp/yr against
a cheap 65/35 index, 95% interval [+0.30, +1.32], BH-adjusted p = 0.010, 13 years to
resolve, at 1.0% tracking error** — while every trend-bearing arm is `unresolved`, the
proposal's own at **64 years to resolve** and the weakest at 1,033. The
[breadth work](stacking-and-effective-breadth.md) then attributes per line, and **IDMO is
the single line resting on a premium that clears a multiple-testing threshold** —
developed ex-US momentum at +8.35 against a 5.21 floor, Holm 0.003, after charging the
1.94 pp/yr its 105%/yr turnover costs. Dropping it moves that page's 30-year probability
from 0.722 to **0.672**, and roughly nine tenths of that is edge rather than breadth,
because IDMO's breadth contribution is actually **negative** (−0.039, from being +0.331
correlated with the trend overlay).

**Cutting the resolvable half to simplify around the unresolvable half is backwards.** The
trend sleeve carries 372 bp of the portfolio's 400 bp of tracking error and cannot be
resolved in 64 years; the tilt basket carries about 100 bp and resolves in 13. A
simplification that removes tilt lines and keeps the wrapper spends the part of the
portfolio that can be evaluated to tidy the part that cannot.

### Simplifications and changes of intent are different cuts

The ladder above is cumulative, and tracking errors do not add, so each cut has to be
measured on its own. Measured singly against the eight-line design:

| Cut | Tracking error | What it is |
| --- | ---: | --- |
| VEA and IEMG bought as one total-international fund | **0.00 %/yr** | a **simplification**: a fund holding the two two-to-one *is* the two |
| IDMO into VEA | 0.20 | a simplification, and the dearest of them on evidence |
| AVES into IEMG | 0.32 | a simplification, on an `unresolved` line |
| **DFIV into VEA** | **0.58** | **not a simplification** — it removes the ex-US value tilt |

The merge is exactly free on holdings and carries one caveat: a real total-international
fund sets its own developed/emerging split and lets it float with capitalisation, where
VEA 10 plus IEMG 5 pins it at two to one. **The merge is free if the investor wants the
cap split and is a small active decision if they do not.**

**DFIV is a decision about what to hold, not about how many lines to hold, and it should be
argued on the evidence for the tilt.** That evidence says drop it: the breadth work finds
DFIV **does not earn its place** once its own measured alpha of **−3.80 pp/yr** is charged —
the only fund alpha on the shelf that clears its own detection floor — leaving an edge of
**−0.45 pp/yr**. Dropping it and holding VEA instead is the only single-line change on that
page that *raises* the 30-year probability, from 0.722 to **0.758**. Its 0.58 %/yr of
tracking error against the eight-line design is therefore the cost of an intended change,
not the price of tidiness, and it should not be netted against the simplifications.

**IDMO is the one line to keep.** It costs 0.20 %/yr to drop, it is the second-highest
shelter priority in the portfolio at 148.2 bp per dollar so it never touches the taxable
account, and it is the single line resting on a premium that clears a multiple-testing
threshold. Dropping it moves the same 30-year probability the wrong way, 0.722 → **0.672**.

**AVES is the genuine toss-up.** `unresolved` on the breadth page's own label, 0.32 %/yr to
drop, a loading 51 months old, and it fails that page's strictest robustness setting by
0.674 against 0.677. Either answer is defensible; neither is worth much.

### The recommendation

This is Part B's line-count recommendation for the eight-line candidate it studies. The
published capital-weight vector is RSST 30 / VTI 19 / VTV 15 / VXUS 16 / AVDV 10 / IDMO 5 /
AVES 5 ([the recommendation](portfolio-recommendation.md)).

**Six tickers: RSST 30, VTI 20, AVLV 15, a total-international fund at 25, IDMO 5,
AVES 5.** Five if AVES goes into the international line as well. That is DFIV dropped on
its own evidence, VEA and IEMG merged for free, and the two lines with the best and the
most uncertain per-line cases kept. Against the eight-line design it measures **0.86 %/yr**
of tracking error, and **0.58 of that is the intended removal of DFIV** rather than any
part of the simplification.

**On this page's own axis the choice barely registers.** Six lines raise the headroom
ceiling from 5.42 pp to **8.89**, against an optimum of 1 pp that neither construction
comes close to binding. The trade count is unchanged in any material way. **The operating
cost of the eight-line design is about 0.4 rebalances and 3 trades a year, and that is not
a reason to hold a different portfolio.**

**Three caveats, because none of the supporting evidence is promoted.** The construction
tournament is `exploratory` in its entirety and its fund series are basis-mapped from
factor data, so a growth figure there is a property of a construction and never of a
ticker. The tilt basket's +0.79 pp/yr falls to **+0.30 — below its own 0.47 floor** — once
every tilt fund is charged its measured alpha, and *DFIV does most of that*, which is the
same finding arriving twice. And the breadth page's own summary is that no holding is
rescued or condemned by the company it keeps: conditioning terms run +0.006 to −0.039.
**Consolidation here is a per-line question, and the operating cost this page contributes
is the smallest of the three inputs to it.**

## B5. The moments this will be hardest to hold

Depth is the worst drawdown of the wealth *ratio* to the comparator — how far behind the
investor actually fell, and for how long. These are the numbers to write into a
precommitment while nothing is wrong.

**Rows with no trend leg in them. No assumption about managed futures can move these.**

| Comparison | Depth | Length | Window |
| --- | ---: | ---: | --- |
| US value tilt vs US market | **−54.3%** | **17.7 yr** | 2008-09 → 2020-09 → **not recovered** |
| International vs US | **−69.0%** | **18.2 yr** | 2008-02 → 2024-11 → **not recovered** |
| Ex-US value vs ex-US market | −36.1% | 18.8 yr | 2007-01 → 2020-09 → 2025-11 |

**Rows that do contain the trend leg, on all three bases.**

| Trend basis | Comparison | Depth | Length | Window |
| --- | --- | ---: | ---: | --- |
| Vendor gross | whole portfolio vs US market | −24.4% | 15.1 yr | 2011-04 → 2021-11 → not recovered |
| Live-fund +2.84%/yr | whole portfolio vs US market | **−45.5%** | **18.2 yr** | 2008-02 → 2024-12 → not recovered |
| Zero excess | whole portfolio vs US market | −52.8% | 18.2 yr | 2008-02 → 2024-12 → not recovered |
| Vendor gross | wrapper vs the equity it displaces | −24.5% | 6.2 yr | 2016-02 → 2021-11 → 2022-05 |
| Live-fund +2.84%/yr | wrapper vs the equity it displaces | **−59.9%** | **11.2 yr** | 2015-03 → 2025-07 → not recovered |
| Zero excess | wrapper vs the equity it displaces | −74.6% | 17.4 yr | 2008-12 → 2025-07 → not recovered |

**Three specific moments, named.**

**A strong equity year with a flat trend leg.** The wrapper still carries 1.072x of equity
(reread 2026-09-01 as 1.050; see [part A](portfolio-for-one-investor.md) §1), so it does not
*fall* — it merely fails to add, while the 99 bp fee and the trend leg's own
drag subtract. On the live-fund basis this stretch ran **eleven years and ended 59.9%
behind a plain index fund**. **This is the failure mode, and it is not a crash. It is a
decade of quiet, visible, monthly underperformance against the most familiar comparator
there is.**

**A long value drought.** The US value tilt has been behind the US market since **September
2008** and has not caught up. Seventeen years is longer than most people's entire investing
memory, and the tilt is 15% of capital.

**International lagging.** 69.0% behind over eighteen years, still open. At 35% of capital
this is the single largest source of visible tracking error in the portfolio, and it is
also the one for which the tax placement is most constrained.

**A whipsaw stretch.** The rebalancing policy is what makes this hard, not the sleeve: a
band breach after a bad trend year requires *buying* the wrapper, which is the trade
nobody wants to place. Under placement C that trade is always available — the wrapper sits
entirely in sheltered accounts, so it can be bought by selling equity there at no tax cost.
**That is one of three reasons to bar the wrapper from taxable, and it is the one no tax
table contains: you must be able to buy it back in the year you least want to.** The other
two are that its taxable cost is the largest and least settled number in the placement
problem — **361.78 bp/yr per dollar on one reading of its filing and 33.72 on another** —
and that sheltering it makes that difference zero.

### The precommitment

Written once, before any of this happens, and re-read at the annual review rather than
during a drawdown.

1. **The comparator is a leverage-matched one, not the S&P 500.** At 132% of gross exposure
   the honest comparison is against the same equity risk taken directly. Any month in which
   the portfolio is compared with an unlevered index is a month in which the leverage is
   being credited to the strategy or charged to it, arbitrarily.
2. **The review happens once a year, on a fixed date, and nowhere else.** Part A's own
   evidence is that a calendar policy's measured result moves by 0.19 pp/yr across a
   December, a June and a March anchor — as large as the effect being measured. Pick the
   anchor once and never move it, because moving it is indistinguishable from acting on the
   drawdown.
3. **The declared tolerance is written as a number now.** The historical stretches above
   are the honest range: an eighteen-year, forty-five-percent shortfall against the US
   market is inside what this construction has done and is not evidence that anything is
   broken. An investor unwilling to write that number down should hold fewer tilts, not a
   shorter memory.
4. **Only two things reopen the construction**: a change in the *evidence* for a sleeve, or
   a change in the *investor*. Neither is a price path. A trend sleeve that trails for a
   decade is doing what a diversifier does; a trend sleeve whose measured loading has
   collapsed is a different fund.
5. **The band is the discipline.** A 25% relative band on an eight-line portfolio fires
   about once every two and a half years. Between firings there is nothing to do, and
   having nothing to do is the design working.

---

# Consequence for this repository

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
6. **A rebalancing target is stated in capital weights, and any code or content that
   states one in notional is a defect.** Notional is a derived, dated audit quantity; the
   conversion factor is a filing fact that moves. The two failure cases are priced in
   [B1](#b1-the-target-is-a-capital-weight-vector-the-exposure-table-is-not) and both cost
   about a quarter of the trend sleeve.
7. **A placement chosen on tax drag alone lands at zero headroom by construction**, because
   the drag-minimising fill runs each line to its cap. Any placement this repository
   publishes should therefore report `min_i (target_i − taxable_i)` beside its drag. The
   fix is cheap — one percentage point costs **+0.21 bp/yr** — and so is the problem: the
   published plan's zero headroom costs **0.49 bp/yr** of forced realisation against a plan
   worth **+38.21 bp/yr**. **Report the number; do not re-plan around it.**
8. **The joint objective is drag plus forced realisation, and it must be minimised
   together.** Minimising either alone gives a corner solution that the other rejects. The
   optimum here is **1 pp of headroom at 19.72 bp/yr**, the minimax choice is 3 pp at
   20.61, and the entire frontier spans **2.2 bp/yr** across five hostile tests. A band and
   a live contribution stream are substitutes for headroom, which is why the frontier is so
   flat and why the only test that prefers zero headroom is the one with no contributions.
9. **Barring a fund from the taxable account can be worth more than its drag.** The
   wrapper's taxable cost is **361.78 bp/yr per dollar on one reading of its filing and
   33.72 on another**, unresolved until its next December distribution. Sheltering it makes
   that difference **zero** under both. The price is that it halves the headroom ceiling,
   from 10.56 pp to 5.42, because it is the largest line.
10. **After-tax account shares, not balances, are what constrain rebalancing.** At a 24%
    ordinary rate and a ten-year taxable holding period, thirds by balance are **Roth 37.8%,
    traditional 28.8%, taxable 33.4%** — the constraining account is *larger* after tax.
11. **A qualified-dividend fraction is a filed number and assuming 1.00 reverses
    conclusions.** Taking it as 1.00 moves IEMG from second-cheapest to third in the
    taxable fill order and flips whether international or US equity belongs in the shelter.
    Any placement conclusion in this repository that predates the filed fractions should
    be re-derived rather than quoted.
</content>
