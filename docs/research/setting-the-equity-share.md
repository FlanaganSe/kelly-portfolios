# Setting the equity share: what is arithmetic, what is preference, and what neither can reach

**Question.** The repository has declared net geometric growth as its objective and has
refused to set the equity/bond split. Given both, what can actually be said about setting
it?

**Decision it informs.** What a disciplined answer to the largest decision in the portfolio
looks like, and which parts an application may compute rather than ask. **It does not set
the split**, and the refusal in [the recommendation](portfolio-recommendation.md) §1.1
stands.

**Out of scope.** A forecast of any market. A recommended number. Glide paths as products.
Annuities, which change the problem rather than the parameter.

`as of 2026-08-17`. Every measured figure in §§1–7 regenerates from
[`studies/equity_share.py`](../../research/src/portfolio_edge/studies/equity_share.py) and
is pinned in `research/tests/unit/test_studies_equity_share.py`; conclusion 8's figures come
from [`studies/fixed_income_shelf.py`](../../research/src/portfolio_edge/studies/fixed_income_shelf.py)
and are set out in [alternative sleeves audit §8](alternative-sleeves-audit.md).

---

## Conclusion

1. **The objective does not choose the split. The constraint does.** Growth-optimal sizing
   contains no risk-aversion parameter at all, and under the zero-leverage rule the growth
   objective alone returns a **corner solution — 100% equity**, for any equity premium over
   bonds above about **2.2%/yr arithmetic**. Every bond in variants B and C is there because
   of the constraint, and **the constraint is a single number nobody has supplied.**
2. **Because the constraint binds, the only available error is underbetting, and
   underbetting is cheap.** Growth at exposure `f` times the growth-optimal exposure retains
   **`1 − (1 − f)**2`** of the peak excess growth — a parameter-free expression. Half the
   growth-optimal exposure keeps **75%**. Twice it keeps **0%**. With leverage at zero and
   the unconstrained optimum above 1.0, **every admissible portfolio sits on the gentle left
   branch of that parabola.**
3. **The equity share is worth about as much per year as the entire measured edge budget,
   and takes about twenty-five years to prove rather than twelve months.** Moving 60/40 to
   90/10 was worth **+127 bp/yr against 485 bp/yr of tracking error** on 1963-07…2025-12 —
   a 0.924 chance of being ahead after thirty years, 90% confidence at **24 years**. The
   contractual budget is ~109 bp against an assumed 46 bp. **Same order of magnitude,
   wholly different certainty class, and they may never be added.**
4. **The case for fractional Kelly is variance, not bias, and it is weaker than usually
   made.** The expected annual growth given up by using an *estimated* optimum is exactly
   **`1/(2T)`** — 0.80%/yr on a 62-year sample, free of every other parameter. The
   growth-maximising shrinkage is **`f* = S**2 T / (S**2 T + 1)`**, which on this
   repository's own US equity sample is **0.931, not 0.5**. **Half Kelly on this asset is
   the claim that 62 years of record are worth 4.7 years of stationary information.** That
   may be a good claim — but it is a claim about non-stationarity and should be argued as
   one.
5. **Sequence risk has a sign.** Across 20,000 reorderings of one fixed 360-month record, a
   lump sum's terminal wealth was **identical to floating-point precision**. A contributor's
   spanned **2.18×** and a withdrawer's **1.77×**, with correlations to first-decade returns
   of **−0.775 and +0.775** — the same number with opposite signs.
6. **Variant C bundles two situations with opposite answers.** In real terms over a 30-year
   retirement, a 20% equity portfolio drawing 4%/yr real failed in **6.82%** of reorderings
   against **2.43%** at 60% equity; at a 5% draw, failure fell *monotonically* to 90%
   equity.
7. **The bond side is a risk brake whose braking is regime-dependent.** On this repository's
   own data the equity/bond beta ran **+0.129 (1974–1999), −0.055 (2000–2022Q3), +0.116
   (2022Q4–2024Q2) and −0.109 since**. The all-bond portfolio drew down **−25.1%**, deeper
   than the 30/70 mix's −17.9%. **Bonds are not a floor.**
8. **Added 2026-08-17: TIPS do not fix that, and they are not a second asset.** The obvious
   answer to point 7 is an inflation-indexed bond, on the argument that it responds to a
   different state variable and so should hold its correlation where the nominal bond does
   not. **Measured, it is the reverse.** On the 275 months where both exist, TIPS'
   correlation to US equity is **+0.131 against the nominal ten-year's −0.076** — a gap of
   3.5 standard errors — and their five-year-block dispersion is **0.200 against 0.114**.
   TIPS correlate **+0.76 to +0.85** with the nominal bond funds they would sit beside, so
   holding both is the same fake breadth as holding credit beside Treasuries. And the era
   that would settle it cannot be reached: **no TIPS return exists before 2003**, which is
   entirely inside the period when the nominal bond's correlation had already flipped
   negative. Full working in
   [alternative sleeves audit §8.4](alternative-sleeves-audit.md); the practical reading is
   that **point 7's regime dependence has no fixed-income remedy on any evidence held here.**
9. **Status.** §§1–3 are **arithmetic** — closed forms, exact given their inputs, and not
   evidence about any market. §§5–7 are **`exploratory` at best**: one sample, one country,
   one modelled bond series, and in the retirement case a permutation null that deliberately
   destroys serial dependence. Point 8's TIPS figures are `exploratory` too and rest on a
   modelled real-yield series over 275 months. Nothing here is promoted.

---

## 1. The part that is arithmetic

### 1.1 The growth parabola, and why being wrong is cheap on one side

Written about its vertex, `g(L) = r + 0.5 sigma**2 [(L*)**2 − (L − L*)**2]` with
`L* = (mu − r)/sigma**2`. Divide the excess of `g` over cash by its peak and **every
parameter cancels**. At exposure `L = f L*`, growth retained is `1 − (1 − f)**2`:

| `f` | Peak excess growth retained |
| ---: | ---: |
| 0.25 | 0.438 |
| **0.50** | **0.750** |
| 0.75 | 0.938 |
| **1.00** | **1.000** |
| 1.50 | 0.750 |
| **2.00** | **0.000** — growth falls back to cash |
| 3.00 | **−3.000** |

The parabola is symmetric in `L`, so **the asymmetry people mean is *multiplicative***.
Half the growth-optimal exposure and twice it are both a factor of two away; one costs a
quarter of the peak, the other costs all of it **and carries four times the variance while
doing so.** That is why
[MacLean, Thorp and Ziemba (2010)](https://www.stat.berkeley.edu/~aldous/157/Papers/Good_Bad_Kelly.pdf)
write that *"it never pays to bet more than the Kelly strategy."*

The consequence here is specific. Leverage is zero and §1.2 shows the unconstrained optimum
sits well above 1.0, so **the whole feasible range is on the left branch. With leverage at
zero you cannot overbet the equity/bond decision.**

### 1.2 Where the optimum is, and why the constraint binds

For a fully invested long-only two-asset mix rebalanced continuously,

```
w* = ( mu_e − mu_b + sigma_b**2 − rho sigma_e sigma_b )
     / ( sigma_e**2 + sigma_b**2 − 2 rho sigma_e sigma_b )
```

**Both `mu` terms are forecasts. So are all three second moments. This step cannot be run
without a forecast, and the repository does not make one.**

**The honest direction to read it in is backwards.** Invert it, and a chosen equity share
becomes the forecast it always was. At the sample second moments of this repository's own
US series (`sigma_e` 15.40%, `sigma_b` 6.73% for the modelled ten-year bond), the arithmetic
equity-over-bond premium at which each share is growth-optimal:

| `rho` | w = 0.4 | w = 0.6 | w = 0.8 | **w = 1.0** |
| ---: | ---: | ---: | ---: | ---: |
| −0.30 | 0.61% | 1.30% | 1.99% | **2.68%** |
| 0.00 | 0.68% | 1.24% | 1.81% | **2.37%** |
| +0.133 (sample) | 0.70% | 1.21% | 1.72% | **2.23%** |
| +0.30 | 0.74% | 1.18% | 1.62% | **2.06%** |

Read the last column: **a 100% equity portfolio is growth-optimal for any expected
equity-over-bond premium above about 2.1 to 2.7%/yr.** Read the middle: **choosing 60/40
asserts that equities will beat bonds by about 1.2%/yr, and no more.** Anyone who would not
write that forecast down should notice that holding 60/40 writes it down for them.

For scale, and as an illustration rather than a forecast: over 1963-07…2025-12 the realised
arithmetic premium of US equity over the modelled bond was **5.51%/yr**, at which the
unconstrained `w*` is **2.28**.

**This is the finding that most needs stating plainly.** Growth-optimal sizing, under the
zero-leverage rule, does not produce a balanced portfolio. **It produces a corner.** Every
bond in variants B and C is bought by something the objective does not contain.

### 1.3 What one step up the ladder is worth

Same window, constant mix rebalanced monthly, log tracking error against the lower rung:

| Move | Edge | Tracking error | P(ahead, 30 yr) | 90% confident at |
| --- | ---: | ---: | ---: | ---: |
| 60/40 → 70/30 | +45.1 bp/yr | 161 bp/yr | 0.937 | 21 yr |
| 60/40 → 80/20 | +87.5 bp/yr | 323 bp/yr | 0.931 | 22 yr |
| **60/40 → 90/10** | **+127.1 bp/yr** | **485 bp/yr** | **0.924** | **24 yr** |
| 60/40 → 100/0 | +163.9 bp/yr | 648 bp/yr | 0.917 | 26 yr |
| 40/60 → 100/0 | +261.9 bp/yr | 968 bp/yr | 0.931 | 22 yr |

**The information ratio is nearly constant up the ladder**, because edge and tracking error
both scale with the weight difference — so the *size* of the step barely changes how long
the decision takes to prove. About twenty-five years either way.

**The comparison with the rest of the repository.** The contractual budget is ~109 bp
against an assumed 46 bp, 99% settled in about twelve months; the 60/40 → 90/10 move is
+127 bp against 485. Those are the same order of magnitude in expected return and **more
than twenty times apart in how fast you find out.** The often-repeated claim that the
equity share dwarfs everything else is **right about the risk** — 15 points of maximum
drawdown against an edge budget with no drawdown term at all — **and roughly wrong about the
return.** Both are historical, and **the second must never be added to the first**: they
carry different benchmarks and the study code raises on the attempt.

---

## 2. Why full Kelly is not the answer even on its own terms

Breiman's theorem is asymptotic, and its own statement says so. **Asymptotically is not a
horizon**, and Samuelson's objection at finite horizons stands.

Three arguments get made for cutting the fraction. They are not equally good.

### 2.1 The estimation-error argument, done exactly

With `sigma` known and `muhat ~ N(mu, sigma**2/T)` over `T` years:

```
SE(Lhat*) = 1 / (sigma sqrt(T))
E[g(Lhat*)] = g(L*) − 0.5 sigma**2 Var(Lhat*) = g(L*) − 1/(2T)
```

The second line is exact and is the sharpest thing here. **The expected annual growth given
up by estimating the growth-optimal exposure is `1/(2T)`, free of `mu`, `sigma` and `r`** —
a pure consequence of the objective being quadratic in the exposure error. Verified against
a 400,000-draw seeded simulation.

Shrink the plug-in by `f` and minimise the same expected shortfall, and the optimum is
`f* = S**2 T / (S**2 T + 1)`, depending on the data only through `S**2 T`, which is the
sample's whole information content about the mean. On this repository's US market series,
`S = 0.4631`:

| Sample length | `SE(Lhat*)` | Growth cost `1/(2T)` | `f*` |
| ---: | ---: | ---: | ---: |
| 10 yr | 2.05 | **5.00%/yr** | 0.682 |
| 20 yr | 1.45 | **2.50%/yr** | 0.811 |
| 30 yr | 1.19 | 1.67%/yr | 0.866 |
| **62.5 yr** (the whole sample) | 0.82 | **0.80%/yr** | **0.931** |

**The cost of not knowing the mean is large** — 0.80%/yr over the longest sample anyone has
is about three-quarters of the whole contractual budget, and at twenty years it is 2.50%/yr,
more than twice it. This is the quantitative form of
[Merton (1980)](https://doi.org/10.1016/0304-405X(80)90007-0): **the precision of a mean
estimate improves with the *calendar span* of the sample and not with sampling more finely
inside it**, so it improves slowly and there is no way to buy your way out. It is also why
Chopra and Ziemba find errors in means about **eleven times** as damaging as errors in
variances and **twenty-two times** as damaging as errors in covariances — the widely quoted
20:2:1 ratio, **and worse still as risk aversion falls**, a log investor's being about as
low as it gets. *(Their table is reproduced in MacLean, Thorp and Ziemba; the original is
paywalled and was not read here.)*

**And the honest shrinkage is 0.93, not 0.5.** This is where the usual telling goes wrong.
With `sigma` known the plug-in optimum is *not* biased upward — **it is unbiased and noisy,
and what the noise damages is the achieved growth, not the estimate.** Estimating `sigma`
too *does* bias it upward, by `(n−1)/(n−3)`, which on 750 monthly observations is
**1.00268** — a rounding error. Selection across many candidate assets biases the winner's
estimate properly, **but there is no selection in an equity/bond split**: there are two
assets and both are held.

So the estimation-error argument, run correctly, supports a fraction around 0.9. Inverting
the formula makes the folk rule legible: `T = f / ((1 − f) S**2)`, so **half Kelly on a
0.4631-Sharpe asset is the assertion that the entire 62-year record is worth 4.66 years of
stationary information.** That is defensible — regimes change, and §6's bond-stock sign flip
is direct evidence for it — **but it is a claim about non-stationarity and should be
defended as one rather than smuggled in as a statistical correction.**

### 2.2 The other two arguments

**Variance of the growth rate.** Full Kelly's wealth path is violent: *"the Kelly criterion
can be very risky in the short term."* MacLean, Thorp and Ziemba read Buffett as behaving
*"similar to a fully Kelly bettor (subject to the constraint of no borrowing)"* and Keynes
as an 80% Kelly bettor. **Note the parenthesis: it is the same constraint imposed here, and
under it full Kelly on equities is simply 100% equity.**

**Risk-constrained Kelly.** Framework open decision 8 notes a ~34% growth advantage at
matched drawdown risk on a finite-outcome case, and that the advantage vanished on that
paper's own fat-tailed mixture. Untested here and correctly deferred: **it sizes an edge,
and there is no edge.**

**What the argument actually supports** is a fraction between about 0.5 and 0.9, the low end
justified by non-stationarity and the high end by the arithmetic. On §1.2's numbers that maps
to an equity share of roughly **1.1 to 2.1 times a fully invested portfolio** — so **the
no-leverage constraint still binds across the whole of it. Fractional Kelly does not produce
a bond allocation either.**

---

## 3. Sequence risk, verified and given a sign

Terminal wealth without flows is `W0 · prod(1 + r_t)`, a product, and multiplication
commutes. With flows it is `sum_t C_t · prod_{s>t}(1 + r_s)`, which does not.

Measured rather than asserted: 20,000 random reorderings of one fixed 360-month record (the
US market, 1996-01…2025-12), seed 20260812, 100% equity throughout, so the multiset of
returns is identical in every draw and **ordering is the only thing that varies.**

| Investor | 5th pct | Median | 95th pct | p95/p5 | Correlation with first-decade return |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lump sum, no flows | 19.5839 | 19.5839 | 19.5839 | **1.0000** | **0.000** |
| Contributing 1/month | 1,588.76 | 2,303.87 | 3,459.91 | **2.178** | **−0.775** |
| Withdrawing 4%/yr of initial | 8.0508 | 11.9043 | 14.2880 | **1.775** | **+0.775** |

The lump-sum row is the identity, confirmed to about 1 part in 10¹⁵. The other two are the
finding, and **the correlations are the same magnitude with opposite sign, because level
contributions and level withdrawals are algebraically dual.** A bad first decade is *good*
for someone buying through it and bad for someone selling through it.

**The consequence is that horizon is the wrong input.** A 30-year accumulator and a 30-year
retiree have the same horizon and mirror-image problems. **The input that matters is the
schedule of cash flows: sign, size relative to the portfolio, and when they start.**

**One limitation, stated because it cuts against the result.** Permuting imposes an iid
null. It holds the multiset fixed, which is what makes it the right test of the identity,
but it **destroys serial dependence**, so it neither confirms nor denies mean reversion. If
real returns mean-revert, real sequence risk for a withdrawer is smaller than this; if
volatility clusters, it is larger.

---

## 4. Human capital, honestly

The standard argument: a young investor's future earnings are a large, bond-like asset, so
to hold a given fraction of *total* wealth in equities the *financial* portfolio must be
equity-heavy and should de-risk as human capital is spent down. That is the intellectual
basis of every target-date glide path on the market. It is a real result with a real
derivation, and four objections are usually left out.

1. **Labour income is not bond-like for everyone.**
   [Benzoni, Collin-Dufresne and Goldstein (2007)](https://doi.org/10.1111/j.1540-6261.2007.01271.x)
   model labour income and dividends as *cointegrated* — a long-run tie that a short-run
   correlation of roughly zero hides completely. **Under cointegration the young agent's
   human capital is stock-like**, because there is time for the tie to bind, and only the
   older agent's is bond-like. Their model implies young investors should **short** equities
   and produces **hump-shaped** lifetime holdings. **The mechanism the standard argument uses
   can run the other way, and in that paper it does.**
2. **Occupation and employer stock decide it, not age.** A tenured public employee and a
   commission-paid salesperson at a cyclical firm do not hold the same asset, and anyone
   holding employer stock in a qualified plan holds a position correlated with their own
   income at the moment they most need the money.
3. **Human capital is illiquid and cannot be pledged.** Treating it as a bond holding in a
   mix that is then rebalanced quarterly treats an unsellable asset as a tradeable one.
4. **The argument as usually deployed implies leverage this repository forbids.** If human
   capital is 80% of a 25-year-old's total wealth and the target total-wealth equity share
   is 60%, the implied financial portfolio is **300% equity**. The literature knows this and
   says so; retail practice quietly caps it at 100% and keeps the conclusion. **And the
   capped version is just "hold 100% equity while young", which §1.2 already gets from the
   growth objective without any human-capital argument at all.**

**The one piece that survives all four cleanly** is
[Bodie, Merton and Samuelson (1992)](https://www.sciencedirect.com/science/article/pii/016518899290044F):
the ability to vary work effort ex post — to work longer, save more, or retire later —
induces more risk-taking ex ante. **That is a statement about *flexibility*, not about age,
and it is the version an application can actually ask about.** "How old are you" is a proxy
for it, and a poor one.

Nothing in this section is measured here. It is published theory with published objections,
and it is `not tested`. **It should inform the *questions* an application asks and must not
be turned into a formula that outputs a weight.**

---

## 5. The drawdown anchor, which is the operational form of the answer

Constant mix, rebalanced monthly, 1963-07…2025-12, 750 months. Equity is Ken French's US
market total return — the same series that produced the 10.80% / 15.40% / −50.3% / 72-month
line in [Experiment 007](long-only-capture.md#the-small-value-corner), reproduced here
through a different code path as a check. Two safe assets, because the difference between
them is itself a finding: cash is French's `RF`, measured; **the ten-year bond is modelled**
from FRED `GS10`.

| Equity share | Cash: return | vol | **max drawdown** | under water | 10y bond: return | vol | **max drawdown** | under water |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0% | 4.45% | 0.9% | 0.0% | 0 mo | 5.92% | 6.7% | **−25.1%** | 65 mo |
| 20% | 5.89% | 3.2% | −10.9% | 37 mo | 7.10% | 6.6% | −18.4% | 48 mo |
| 30% | 6.58% | 4.7% | −16.9% | 40 mo | 7.65% | 7.0% | **−17.9%** | 41 mo |
| 40% | 7.26% | 6.2% | −22.6% | 50 mo | 8.18% | 7.8% | −21.3% | 36 mo |
| 50% | 7.90% | 7.7% | −27.9% | 57 mo | 8.68% | 8.8% | −26.1% | 37 mo |
| **60%** | 8.53% | 9.2% | **−33.0%** | 58 mo | 9.16% | 10.0% | **−30.6%** | 40 mo |
| 70% | 9.13% | 10.8% | −37.7% | 63 mo | 9.61% | 11.2% | −34.9% | 51 mo |
| 80% | 9.71% | 12.3% | −42.2% | 64 mo | 10.03% | 12.6% | −40.2% | 58 mo |
| **90%** | 10.27% | 13.9% | **−46.4%** | 66 mo | 10.43% | 14.0% | **−45.5%** | 64 mo |
| **100%** | **10.80%** | **15.4%** | **−50.3%** | **72 mo** | 10.80% | 15.4% | −50.3% | 72 mo |

**This table is the answer in the only form that can be handed to a person.** Pick the row
whose drawdown you would have held through — not the one you would tolerate in the abstract,
the one you would have held through *for the months under water in the same row* — and read
the equity share off the left.

Three warnings that belong beside it and not in a footnote. **Drawdown deepens mechanically
with sample length**, so no number here may be compared against a drawdown from a different
window. And **bonds shortened the drawdown but did not remove it**: the 90/10 rung is
−45.5%, 4.8 points better than all-equity.

**The third limitation is measured, and it is worse than a warning about one country
would suggest.** [Jordà–Schularick–Taylor R6](evidence-base.md) supplies annual **real**
total returns for sixteen countries, 1870–2020:

| | worst | median | best | **where the US ranks** |
| --- | --- | --- | --- | --- |
| Full sample 1871–2020 | −98.4% PRT | ≈ −78% | −49.8% DNK | **15th of 16** at −51.9% |
| 1963 onward, the window above | −98.4% PRT | — | −47.2% **USA** | **16th of 16** |

**In the same 1963-onward window this ladder is built from, every one of the other fifteen
countries did worse, and fourteen of fifteen did worse than −50%.** France fell **−97.7%**
from its 1942 peak and had **not regained it 78 years later**; Japan's −93.0% (1937→1945) is
a floor rather than a measurement, because 1946–47 are missing from the source and inflation
in those years ran +91% and +125%.

Three qualifications travel with that table and none of them rescue the anchor. Portugal's
−98.4% leans on **source-flagged interpolations for 1975–77**; dropping them leaves −80.1%,
and the cleanest fully-measured near-total loss is France's. Germany's −97.9% is contaminated
by hyperinflation arithmetic and the 1948 currency reform. And these are **annual and real**
against this page's **monthly and nominal** −50.3%, so the like-for-like US comparator is
**−47.2%** — which is the number that ranks last of sixteen.

**Read the ladder accordingly.** −50.3% is not a bound and not a typical case. It is close to
the most fortunate outcome the developed world produced, and an equity share chosen against
it is chosen against the best draw rather than the median one.

### 5.1 Withdrawals invert part of the table

The drawdown ladder is monotone; the *failure* ladder is not. In real terms — CPI deflated,
level real withdrawal, 30-year horizon, 20,000 reorderings, 748 months (real equity
6.66%/yr, real bond 1.98%/yr) — the probability of running out:

| Real withdrawal | 20% eq | 30% | 40% | 50% | **60%** | 70% | 80% | 90% | 100% |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3%/yr | 0.07% | 0.03% | **0.03%** | 0.04% | 0.07% | 0.15% | 0.27% | 0.41% | 0.64% |
| 4%/yr | **6.82%** | 3.78% | 2.88% | 2.50% | **2.43%** | 2.71% | 3.17% | 3.60% | 4.24% |
| 5%/yr | 47.34% | 32.41% | 22.74% | 17.51% | 14.87% | 13.56% | 13.06% | **12.86%** | 13.16% |
| 6%/yr | 86.77% | 74.97% | 60.77% | 49.05% | 40.96% | 35.16% | 31.31% | **28.74%** | 27.27% |

**The minimum walks right as the withdrawal rate rises.** At 3% real the safest portfolio is
genuinely the safe one; at 4% the minimum is at 60% equity and a 20% equity portfolio is
nearly three times as likely to fail; at 5% and 6% failure falls almost all the way to 100%
equity. **Above about a 4% real draw, holding too few equities is the larger risk.** The
mechanism is not subtle: the withdrawal outruns the return, and no ordering of a 1.98%/yr
real bond return supports a 5% real draw for thirty years.

**This is `exploratory`** — one country, one modelled bond, an iid permutation null, and a
real bond return no reader should assume forward. **It is enough to show that variant C
conflates two cases.**

---

## 6. What the bond side is actually for

[The recommendation](portfolio-recommendation.md) books bonds as *"a different benchmark,
not an edge"*, sized by risk capacity, citing
[Campbell, Pflueger and Viceira (2025)](https://www.nber.org/papers/w34323) for the sign
flip. Two corrections to how they have been quoted here, and one measurement.

**The era boundaries usually quoted are not the ones the authors state.** In their own
February 2026 summary the negative era runs to **2022Q3**, not 2022, and the positive era
that follows runs **2022Q3 to 2024Q2**. They also name three earlier sub-periods: negative
1964Q1–1967Q3, positive 1967Q4–1971Q3, and no significant beta 1971Q4–1974Q2. **The picture
is not two eras. It is at least six.**

**The "US, UK and Eurozone" attribution could not be verified.** The NBER landing page, the
abstract and the authors' summary are US-only in what they state; the working paper PDF
returned HTTP 403 from two hosts. **The multi-country claim may well be in the paper. It is
not supported by anything read here.**

**Measured on this repository's own data**, with the modelled bond and their sub-period
boundaries translated to months:

| Era | Months | Correlation | Beta of bond on equity |
| --- | ---: | ---: | ---: |
| 1964-01…1967-09 | 45 | +0.400 | +0.120 |
| 1967-10…1971-09 | 48 | +0.540 | +0.226 |
| 1971-10…1974-06 | 33 | +0.071 | +0.021 |
| **1974-07…1999-12** | 306 | +0.266 | **+0.129** |
| **2000-01…2022-09** | 273 | −0.138 | **−0.055** |
| **2022-10…2024-06** | 21 | +0.258 | **+0.116** |
| **2024-07…2025-12** | 18 | −0.239 | **−0.109** |

**The three long eras reproduce the published sign pattern independently.** The three short
ones do not and should not be expected to — 18 to 45 observations carry no power, and the
two earliest disagree with the published sign outright. **The final row is the one worth
sitting with: on the eighteen months since the published sample ends, this repository's own
data says the sign has flipped back to negative again.**

**What follows for the split**: bonds are held as a risk brake **whose diversification
benefit is regime-dependent — the sign changed three times in the published record and, on
this data, a fourth time since it ended.** That is weaker than "bonds diversify equities".
It is strong enough to keep them, since §5 shows the brake working at every rung, **but not
strong enough to size them from a covariance estimate**, and it is direct evidence for the
non-stationarity §2.1 says is the real argument for a fractional exposure.

And the row that should end any conversation about bonds as a floor: **the all-bond
portfolio drew down −25.1% and spent 65 months under water**, deeper and longer than the
30/70 mix's −17.9% over 41 months. Its worst stretch was 2020-08 to 2023-10, inside the era
when the beta had turned positive again.

---

## 7. The decision structure

This is the part an application renders. **It is a structure, not a number, and it fails
loudly at the step where a forecast is required rather than substituting one.**

**Step 1 — inputs the reader must supply. None can be inferred.**

| Input | Why it is needed | Used in |
| --- | --- | --- |
| **The drawdown you would hold through** — depth *and* months under water | The objective is growth *subject to* this. Without it the objective returns a corner | §5 |
| **Cash flows**: sign, size relative to the portfolio, start date, real or nominal | Sequence risk is a cash-flow interaction and its sign flips with the direction of the flow | §3, §5.1 |
| **Withdrawal rate**, if drawing | Decides whether more equity raises or lowers failure risk | §5.1 |
| **Flexibility**: can you work longer, save more, or spend less after a bad decade | The one part of the human-capital argument that survives its objections | §4 |
| **Occupation and employer-stock exposure** | Decides whether human capital is bond-like or stock-like at all | §4 |
| Optionally, an **equity-over-bond premium forecast** | Only needed to run §1.2 forwards. Not needed to run it backwards | §1.2 |

**Step 2 — arithmetic that runs on them, with no forecast.**

| Computation | Closed form | Forecast needed? |
| --- | --- | --- |
| Growth retained at a fraction of the optimum | `1 − (1 − f)**2` | **No** |
| Growth cost of estimating the optimum | `1/(2T)` | **No** |
| Growth-maximising shrinkage | `S**2 T / (S**2 T + 1)` | Needs `S` and a *believed* `T` |
| Premium your chosen weight implies | inverse of `w*` | **No** — this is the honest direction |
| Drawdown and time under water at each weight | one pass over a wealth path | **No**, but one historical sample |
| Ruin probability at a withdrawal rate | permutation over a return record | **No**, same caveat |
| Growth-optimal weight `w*` | `Σ⁻¹(μ − μ_b)` form | **Yes. Stop here and say so** |

**Step 3 — the range where being wrong is cheap.** Under zero leverage the whole admissible
range sits on the left branch, so the only available error is underbetting. Against a
growth-optimal exposure of 2.28 (§1.2, at the sample premium, **an illustration and not a
forecast**): 40% equity retains 0.32 of peak excess growth, 60% retains 0.45, 80% 0.58, 100%
0.68. **Read that as a warning about the premise, not a recommendation** — at a forecast
premium of 1.2%/yr instead, `w*` is 0.6 and the table inverts. **The gradient is entirely a
function of the forecast you are unwilling to make**, which is the whole reason the split is
not set here.

**Step 4 — the drawdown you are signing up for.** §5's table, filtered to the chosen rung,
with its `as of` date, its window, its one-country limitation, and the note that the bond
column is modelled.

**What the application must not do.** Present §1.2's `w*` without the premium forecast that
produced it. Add the §1.3 ladder edge to the contractual budget — different benchmarks, and
the study code raises. **Output an equity share from age**; §4 is the reason. Describe any
of §§5–7 as anything but one historical sample.

---

## Verified, assumed, open

**Verified here.** The `1 − (1 − f)**2` identity, cross-checked against an independently
written `growth_rate_vertex` to 1e-15. The two-asset `w*` and its inverse, against a
20,001-point grid search at twelve parameter combinations. `1/(2T)` and `f*`, against a
400,000-draw seeded simulation. `(n−1)/(n−3)` likewise. Permutation invariance of terminal
wealth without flows, to floating-point precision. The 1963-07…2025-12 market line
reproduced from Experiment 007 through a different code path. The
Campbell–Pflueger–Viceira sign pattern in its three long eras.

**Assumed on this page, and nowhere else.**

1. **The ten-year bond total return on this page is modelled from `GS10`, not measured**,
   and **as of 2026-08-17 that is a choice rather than a necessity.** Goyal–Welch `ltr`
   carries 1,200 months of measured long-Treasury total return from 1926-01 and eighteen
   bond and TIPS ETFs carry investable Item B.5 returns from 2019-09
   ([evidence base](evidence-base.md)). **This page has not been re-run on either**, and the
   two are not interchangeable with the proxy: `ltr` is a roughly twenty-year exposure
   against `GS10`'s ten-year point, they correlate **+0.663** over the 750 months both
   cover, and the proxy is 3.4 pp/yr less volatile and 0.8 pp/yr lower in excess return.
   Rebuilding §5's ladder on `ltr` would make the bond column a *different question*, not a
   better answer to the same one — so it is left as it is, labelled, and the substitution is
   named as open below. The proxy still carries no on-the-run premium, no bid/ask, no tax
   and no index roll rules. **Every bond figure on this page inherits it.**
2. **Monthly rebalancing** in every constant mix. Experiment 003 priced the policy difference
   at 0.3–1.2 bp/yr in cost and nothing in return, so this is small — but it is one.
3. **`sigma` known and returns Gaussian and independent** in §2.1. Both fail in practice, and
   **both failures push `f*` down**, which is the direction §2.1 already argues.
4. **An iid permutation null** in §3 and §5.1 — deliberate, and it destroys serial dependence.
5. **A 30-year horizon** in §5.1, CPI-U as the deflator.
6. **Nominal, US, pre-tax throughout §§1, 3, 5 and 6.** §5.1 alone is real.

**Open.** What drawdown constraint the objective is subject to — **the binding input, and
nothing here can supply it.** Which estimation window and regime-conditioning scheme the
covariance matrix should use, on which §6 is now direct evidence that the question is live.
Whether risk-constrained Kelly beats fractional Kelly on real returns. Whether the
multi-country bond-stock claim holds. How labour income actually covaries with equities for
a given reader.

**One item left this list on 2026-08-16.** "What a non-US drawdown ladder looks like" is
answered in §5 above: sixteen countries are now loaded, and the US ranks 15th of 16 on the
full sample and 16th of 16 from 1963. What remains open is the *constant-mix ladder* on those
countries — this page's rungs are still computed on US data alone, and rebuilding them
per country is a study nobody has run.

**One item joined it on 2026-08-17.** §5's ladder should be rebuilt on the **measured**
`ltr` bond leg beside the modelled `GS10` one, so that the drawdown a reader is asked to
choose from is a drawdown someone could have taken. It is a study, not an acquisition: the
series is held. **What it will not change is the corner solution**, which is set by the
equity premium over the safe leg and the zero-leverage rule — and `ltr`'s realised excess
return over 1991-2025 is *higher* than the proxy's by 1.76 pp/yr at a *higher* volatility,
so the bonds still come from the constraint.

**Reproducibility.** `cd research && uv run python -m portfolio_edge.studies.equity_share`.
Equity: Ken French `Mkt-RF + RF`, 1963-07…2025-12, 750 observations. Cash: the `RF` column.
Bond: FRED `GS10`, **modelled** by pricing a semiannual par bond struck at last month's
yield and repricing at this month's. Inflation: `CPIAUCSL`, ending two months before the
equity series, so §5.1 runs on 748 months. Seed 20260812, 20,000 permutation draws per cell.
**No experiment was run and no ledger entry was written: this is a study, not an experiment,
and it decides nothing a frozen specification would have to adjudicate.**

---

## Consequence for this repository

1. **§1.1 of the recommendation keeps its refusal and gains the reason.** Not "risk
   capacity" as an undefined faculty, but **a drawdown constraint the objective is explicitly
   subject to and that nobody has supplied.**
2. **Variant C should be split.** "Under 10 years" and "withdrawals have begun" have opposite
   answers above a 4% real draw.
3. **The bond–stock citation needs tightening.** The era boundaries and the
   three-currency-area attribution are not supported by anything reachable; §6 states what is.
   **What §6 asserts is now also measured here**: on Goyal–Welch `ltr` against Ken French's
   market, the correlation to equity spans **0.802** across twelve non-overlapping five-year
   blocks, seven positive then five negative — compactly, **+0.352 to 1998-06 and −0.206
   after**, on a break date chosen by eye and reported as descriptive. The sign change is
   real and it is not a citation problem.
4. **An application may render §7 and must render it whole.** Every input in step 1, the
   stop-here marker at step 2's last row, and the drawdown table with its limitations. **A
   calculator that outputs an equity share from an age or a risk questionnaire is the thing
   this page exists to prevent.**
5. **Nothing here reopens the zero-leverage rule.** The observation that the growth objective
   would like more than 100% equity is an observation about the objective, not a case for
   borrowing.
6. **`studies/equity_share.py` is the executable record.** Any change to a number here
   changes a test, by construction.
</content>
