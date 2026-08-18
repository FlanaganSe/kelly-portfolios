# Researching portfolio edge without fooling ourselves

**Question.** Can leverage, rebalancing, drawdown controls, diversifiers, active funds
and systematic factors be combined to improve an investable portfolio, and how should
this repository test that claim?

**Decision it informs.** Which hypotheses deserve implementation, what evidence would
reject them, and the minimum standard before any result is shown as financially
meaningful. Selecting products for a reader, giving personalised advice, and claiming
that a strategy will beat the market are out of scope.

**This page is the canonical synthesis and the place to start.** It answers *whether a
return source is real*. Three pages carry what it deliberately does not:
[the evidence base](evidence-base.md) holds what the data can and cannot measure;
[search coverage](search-coverage.md) audits where the search has looked and what round
two should test; [the recommendation](portfolio-recommendation.md) answers what to hold.

`as of 2026-08-12`.

---

## Conclusion

No reviewed method mathematically guarantees market outperformance. The defensible
objective is narrower: test whether a small number of economically distinct return
sources can improve **net geometric return** against a cheap investable benchmark, while
keeping estimation error, ruin, drawdown, liquidity and implementation costs inside
explicit limits.

**No positive, independently replicated, net-of-cost edge has been established here.** A
low-cost diversified-beta baseline is therefore the control every proposed edge must
beat ([decision 0003](../decisions/0003-cheap-broad-market-control.md)) — not a claim
that the final answer has been found.

Read that with its scope attached. What has been shown is that a narrow set of gross
academic factor spreads, a 72-month unaudited fund window, and ten marginal 10% sleeve
additions to two fixed base portfolios cannot support a promotion. Several of those
instruments have measured detection floors above the effect size that would matter, so a
null result from them carries little information. [Search coverage](search-coverage.md)
sets out which conclusions that qualifies and which it does not.

---

## Can you near-definitively beat the market? The direct answer

The commissioning premise was: *"The goal is to have information and strategies and
research to near definitively beat the market. Beating the market is not hypothetical;
it's definitely possible (ie, capture rebalancing bonus against two assets that both
return the market). But that's not enough."*

The honest answer has two halves and both are load-bearing.

### Against your own counterfactual: yes, and most of it is arithmetic

Against **the portfolio you would otherwise have owned**, the
[edge decomposition](expected-edge-decomposition.md) and
[structural and tax-aware edges](structural-and-tax-edges.md) price a budget of roughly
**110 basis points a year for one stated reference investor**, at an assumed ~46 bp of
tracking error. Its lines, and the conditions each depends on:

| Line | Central | Conditional on |
| --- | ---: | --- |
| Fund cost reduction | **49 bp** | holding an expensive fund now. **This is the only line with no other condition** |
| Fund structure: capital-gain distributions an ETF does not make | **+23 bp** | a taxable account and an active-mutual-fund counterfactual. **Decaying** — 94 SEC orders let mutual funds add ETF share classes |
| Tax-loss harvesting, net of its fee | **+26 bp** | a taxable account, direct security ownership, offsetting gains, continuing contributions, and a 9–12 bp provider |
| Asset location, net of forfeited foreign tax credit | **+7 bp** | more than one account type and more than one asset class |
| Specific identification of tax lots | **+5 bp** | ever selling anything |
| **Total** | **≈110 bp** | outer range **4 to 270 bp** |

**Three cautions the headline usually drops.** The 4-to-270 range is not a distribution:
it assumes every condition fails together at the bottom and succeeds together at the
top. Only the fee line is unconditional, so for a reader who already holds cheap index
funds in one tax-deferred account the honest budget is close to zero. And the 46 bp
tracking error is an assumption, not a measurement, which makes the *"99% confident in
twelve months"* figure an upper bound on certainty rather than a result.

What survives all three is the shape, and it is the most useful thing here.
[Sharpe (1991)](https://web.stanford.edu/~wfsharpe/art/active/active.htm) makes the fee
half an accounting identity — *"they depend only on the laws of addition, subtraction,
multiplication and division."* A fee not paid and a tax not realised are contractual in a
way no premium is, and they require a view on no market. It is also an edge that is
*spent once taken*: an index fund cannot beat its own index by cutting its fee again.

**Not trading is deliberately not on that list.** The behaviour gap is booked separately
at 15 bp against the *average investor*, and the two benchmarks may never be added
([§2](expected-edge-decomposition.md#2-the-behaviour-gap-is-a-different-benchmark-not-a-missing-line)).

### Against a cheap index: no, at any horizon a human has

Against **a stated cheap index**, the whole honest budget is about **24 bp/yr against
401 bp of tracking error** — a thirty-year probability of being ahead of **0.63**, and
roughly 443 years to 90% confidence. Read 24 bp as an **upper bound**, because its
rebalancing line has since been measured negative on real data and its factor line's
sign turns on a benchmark choice the budget never states.

The arithmetic underneath is what matters, and it is not about markets. Because
`P(outperform) = Phi(e sqrt(T) / s)` and `T(confidence) = (z s / e)**2`, the horizon
scales with the **square** of `s/e`. The same 50 bp edge reaches 90% confidence in
**24 days** against 10 bp of tracking error and in **105 years** against 400 bp. Thirty
years against 400 bp can demonstrate an edge of only about 94 bp/yr.

**Tracking error, not edge size, decides whether a lifetime is enough.** Every feasible
improvement to the index-relative answer is on the `s` side, and combining sleeves moves
`s` the wrong way.

### The rebalancing example, in three parts

The premise named one mechanism and it deserves a specific answer.

**Mathematically true.** For constant long-only weights, portfolio log growth carries a
non-negative excess term `gamma_star = 0.5 (sum_i w_i sigma_i**2 − sigma_p**2)`. A
buy-and-hold portfolio converges almost surely on its single best component and
asymptotically throws all of it away. With *equal* drifts, constant weights win
eventually, always.

**Provably conditional, and the condition is exact.** Constant weights beat buy-and-hold
in almost-sure growth rate **iff `g_p > max_i g_i`**. The break-even is horizon-free: at
a drift gap equal to `gamma_star` the probability is exactly 0.5 at *every* horizon.
Even in the ideal equal-drift case the win probability floors at `2 Phi(1) − 1 = 68.27%`
and reaches 90% only at about **390 years**. "Near definitively" is refuted
quantitatively.

**Empirically absent on the canonical real pair.**
[Experiment 003](rebalancing-policy.md) tested it on 420 months of US, developed-ex-US
and emerging equity. The closed form for `gamma_star` reproduced to **0.09 bp/yr** — the
mathematics is not the problem. What failed is the premise that two broad equity markets
"both return the market": US against developed-ex-US ran a realised drift gap of
**4.34 pp/yr against a `gamma_star` of 12.5 bp**, a factor of 35. The realised advantage
was **−62.9 bp/yr** against **−70.5 bp** predicted once the closed form is extended to
that drift gap. The theory predicted the loss.

Costs are not the explanation and must not be offered as one: the most expensive policy
paid 1.2 bp/yr. What rebalancing *did* buy is real and is not return — it held exposure
within 0.6 to 3.1 percentage points of target against buy-and-hold's 14.8. That is
keeping a promise, and it is the only claim the evidence supports.

---

## The design map

**This is not an allocation and not a recommendation.** It records, per candidate, what
would have to become true before it could be held. Statuses are the closed vocabulary —
`exploratory`, `source-reproduced`, `independently-reproduced`, `walk-forward-tested`,
`shadow-live`, `production-eligible`, `rejected`, `unresolved` — and are never collapsed
into "works".

| Candidate | Status | The number that decides it | Condition for promotion |
| --- | --- | --- | --- |
| **Cheap broad market** | **the control** | Sharpe's identity; ~1.3 bp round-trip friction at retail. But FF5+UMD prices VTI itself at −0.55 pp/yr, so the standard model does not span the control | none — it is the control |
| **Value (HML)** | **`exploratory`** | Pooled +4.7 pp/yr `[+1.5, +8.1]` post-publication across three regions, positive in all three, surviving Holm and its own best year. **US leg alone is +1.6 and survives no correction** | A delivered capture measured from a fund's holdings, and a product clearing the frozen promotion protocol on a prior-window comparator |
| **Momentum (UMD)** | **`exploratory`** | Pooled +7.3 pp/yr `[+3.9, +10.3]`, the largest gross premium here — against the worst detection threshold (4.98), the fewest effective regions (1.33), and three regions that **crash together** in 2009 | A net premium from **observed** turnover below 50%/month one-sided, and a second product: the retail shelf is MTUM alone |
| **Profitability (RMW)** | **`rejected`** | Pooled +2.5 pp/yr against its own 2.62 pp/yr detection threshold. **Closed on the public files** ([decision 0005](../decisions/0005-factor-premia-closed-on-public-data.md)) | A further decade of out-of-sample months (~2035), or a non-French construction |
| **Investment (CMA)** | **`rejected`** | −1.4 pp/yr post-publication in the US, +0.2 pooled, against a 3.41 threshold. Outside the US the premium is ~0 rather than negative, so the sign flip is a US phenomenon and the rejection rests on materiality | As above. **Never count HML and CMA as two bets** — 0.63 correlated |
| **Size (SMB)** | **not signable** | +1.9 pp/yr `[−1.9, +6.0]` over 750 months against a 4.73 threshold; +0.4 post-publication | A premium visible in some window this repository can reach |
| **Diversified trend** | index **`unresolved`**; **DBMF `exploratory`** | Marginal growth +1.31 pp/yr against a risk match, falling to +0.88 post-publication with an interval containing zero. A static-plus-volatility replica delivers 44%. Only DBMF of five listed ETFs clears the 0.50 loading bar. Distribution tax drag 0.76–2.53 pp/yr, **2.5× DBMF's fee, and zero in a shelter** | A multi-asset attribution leaving a residual; a contract-level test of the volatility scaling; a second delivering product |
| **Rebalancing** | **`rejected`** as return, retained as risk control | −38.7 bp/yr on the portfolio over 35 years; drift gap 35× `gamma_star`; `kappa` trends rather than reverts | An investable low-correlation pair whose drift gap is genuinely below its `gamma_star`. None was found |
| **Cost / tax / structure** | **contractual, conditional** | ≈110 bp/yr for one stated reference investor, 4–270 outer range; only the 49 bp fee line is unconditional | Already available. What remains is a **review trigger** on the decaying fund-structure line |

### What the sleeves share

Strategies are not additive because their backtests have low correlation. Concretely,
the rows above share: **leverage** (trend is a levered futures book), **funding
liquidity** (March 2020 impaired even the Treasury market), **volatility estimation**
(trend, any volatility target and any risk-parity weight divide by the same estimated
covariance, which for HML and RMW carries a 3–5% systematic band), **short borrow**
(every academic long-short premium above; retail cannot implement them at all),
**equity rebounds** (momentum crashes exactly there), and **crowded exits** (the August
2007 quant unwind was a three-day −6.85%, twelve daily standard deviations, followed by
a +5.92% rebound — a liquidity event, not a signal failure).

Regional splits are not independent bets either: three regions of HML are worth an
effective **1.49** looks and of UMD **1.33**, and momentum's three regions share their
worst calendar year.

Nor does combining twenty strategies that each win 55% imply a durable edge. Even for
equal payoffs and a correctly known independent 55% probability, twenty simultaneous
bets produce a strict majority only **59.1%** of the time. In markets, independence and
the 55% are both estimated from the same finite selected history — and among 215
commercially promoted alternative-beta strategies the median live Sharpe deterioration
from backtest was **73%**
([Suhonen, Lennkh and Perez 2017](https://ssrn.com/abstract=2757113); vendor-selected,
not a census).

---

## What the prior literature establishes, and what it does not

Compressed to the claim, the primary source, and the single number that decides how much
weight it can carry. Each was checked against the primary source and put through
three-vote adversarial verification. **Verification killed framing far more often than
arithmetic**: of seven claims rejected, six reproduced their numbers exactly and failed
on dropped scope — a hurdle omitted, a weight fitted ex post, a benchmark that was not
the stated one.

**Portfolio theory and leverage.**
[Markowitz (1952)](https://doi.org/10.1111/j.1540-6261.1952.tb01525.x) finds
minimum-variance portfolios given known inputs; it does not show that estimated
efficient portfolios outperform out of sample. With a risk-free asset and identical
borrowing and lending rates, leverage only changes exposure to the tangency portfolio
([Tobin 1958](https://doi.org/10.2307/2296205)). [Kelly (1956)](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x)
maximises expected log wealth; in a one-risky-asset diffusion `L* = (mu − r)/sigma**2`,
and the vertex form `g(L) = r + 0.5 sigma**2 [(L*)**2 − (L − L*)**2]` makes the two
boundaries follow from symmetry alone. Two traps: `mu` must be the arithmetic Itô drift,
not a CAGR; and the widely repeated `L* ≈ 1.54` is **not** a measured S&P quantity but
an illustration at `mu − r = 5%`, `sigma = 18%`, whose author states his own framework
overestimates optimal leverage and conjectures the real figure for a broad index is near
1. Attribute the algebra to Itô, Kelly, Latané and Merton rather than to ergodicity
economics; nothing in that dispute changes a leverage number, because
`E[ln W_T] = ln W_0 + T g(L)` makes time-average growth and expected log utility the same
optimisation. Kelly is optimal for log utility, not for every investor
([Samuelson 1979](https://doi.org/10.1016/0378-4266%2879%2990023-2)), and `1/gamma`
times Kelly holds only in the constant-opportunity Merton diffusion.

**The operational trap is `gamma`.** Merton's solution is the mean-variance one divided
by risk aversion, so presenting a mean-variance output as Kelly overstates leverage by a
factor of `gamma` — a 4× error for a CRRA-4 investor. This is why no optimiser ships.

**Lifecycle leverage** redistributes market exposure across time; it does not create
alpha. Ayres and Nalebuff's initially leveraged glidepath matched constant 75% equity's
mean accumulation with 21% lower standard deviation in one US historical simulation, but
their 2:1 is Regulation T's cap rather than an optimum, their own robustness table
inverts the prescription at 29.29% volatility, and the one independent out-of-sample
test finds the risk reduction "relatively insignificant". The premise it needs — human
capital as an unsellable riskless bond — is exactly what cointegration between labour
income and dividends breaks, implying hump-shaped holdings and, under plausible
calibrations, short equity positions for the young
([Benzoni, Collin-Dufresne and Goldstein 2007](https://doi.org/10.1111/j.1540-6261.2007.01271.x)).

**Rebalancing.** Diversification return is *defined* against `sum_i w_i g_i`, which is
not the return of any portfolio one can hold, so a random walk produces a positive
measured diversification return with no skill involved. A two-period rebalance is
exactly a short straddle on relative performance,
`R_REBAL − R_HOLD = −w_S w_B kappa_1 kappa_2`
([Rattray et al. 2020](https://people.duke.edu/~charvey/Research/Published_Papers/P145_Strategic_rebalancing.pdf)),
so it loses when relative performance trends. Under Markov prices the
long-rebalanced/short-buy-and-hold trade has exactly zero expected profit
([Chambers and Zdanowicz 2014](https://www.hec.ca/finance/Fichier/Chambers2014.pdf)) —
correct, and it generalises. Their dismissal of log wealth as "an arbitrary nonlinear
transformation" does **not** reach `E[log W]`: read in context it targets the expected
*annualised rate*, which they say is arbitrary because "the magnitude of the effect is
driven by the time it takes the planet to orbit the sun". `(1/T) log W_T` is a pathwise
property containing no annualisation and no preferences, and Breiman's Theorem 2 gives
the log-optimal strategy almost-sure dominance. What survives on the other side is
Samuelson's actual objection — a finite-horizon CRRA maximiser has no reason to adopt an
asymptotic criterion — and it stands. **The correct diagnostic for whether rebalancing
adds value is the serial dependence of `kappa_t`, never the diversification-return
statistic.**

**Crisis diversification and tail protection.** International correlations rise in bear
markets ([Longin and Solnik 2001](https://doi.org/10.1111/0022-1082.00340)), so
unconditional covariance understates joint left-tail risk. Gold has been an average
hedge and a short-lived safe haven in some countries and samples, not a universally
negative-correlation asset. **Measured here on 2026-08-17 and confirmed**: over 658 months
from 1971-09, gold's correlation to US equity is **−0.031 / +0.019** unconditionally and
**−0.011 / +0.072** inside equity drawdowns of 10% or more (World Bank Pink Sheet / LBMA
month-end fix). **Zero, not negative, on both.** What the claim understated is the other
half: gold's crisis correlation does *not* rise the way this paragraph's opening sentence
warns international correlations do — the conditional-minus-unconditional gap is +0.02 to
+0.11 — and its mean return inside those months is **+0.85 to +0.95%/month** against
equity's −0.26%. **A zero-correlation asset that pays inside drawdowns is not a hedge and
is exactly what the diversification credit rewards**; it still fails the marginal test on
return ([marginal sleeve value § Gold, tested](marginal-sleeve-value.md#gold-tested)). The nominal bond–stock beta was positive circa 1970–2000,
negative circa 2000–2022Q3, and positive again to 2024Q2
([Campbell et al. 2025](https://www.nber.org/papers/w34323), NBER working paper) — so a
covariance matrix estimated over a long full sample averages opposite regimes and
describes neither. Price protection and funding liquidity are different: in March 2020
even the Treasury market suffered impaired depth and forced sales. Repeatedly buying
puts pays option premium, skew, spread and decay, and the benchmark decides the answer —
over 1986–2016 the Cboe 5% Put Protection Index earned 2.5%/yr excess of cash against
5.8% for the index, and a **constant-weight 36.5% equity / 63.5% cash portfolio earned
the same 2.5%**. Two limits usually dropped: that 36.5% weight is fitted **ex post**, and
under the same paper's implementable rule the protected portfolio has better
fifth-percentile drawdowns.

**Time-series momentum is profitable while returns are not predictable, and only the
first survives.** Huang et al. reuse the original 55-asset data: mean out-of-sample R² is
**negative** at −0.67%, and the original pooled `t = 4.34` sits **below** its own
bootstrap 5% critical values of 12.53 (wild) and 4.83 (pairs)
([Huang et al. 2020](https://doi.org/10.1016/j.jfineco.2019.08.004)). Removing the
volatility scaling collapses the statistic from 4.34 to 1.68
([Kim, Tse and Wald 2016](https://doi.org/10.1016/j.finmar.2016.05.003)), and the
strategy carries a large embedded net-long market position, so adding a time-varying
market position to a cross-sectional strategy reproduces the result
([Goyal and Jegadeesh 2018](https://doi.org/10.1093/rfs/hhy131)). No rebuttal to Huang
et al. was found — searched for and absent. This repository's own Experiment 004
reproduces the mechanism: a large negative static market beta against a large positive
volatility-scaled beta.

**Factor replication is model-dependent, and the dispute is about estimands.** With NYSE
breakpoints and value weighting, 65.0% of 452 published anomalies fail `|t| >= 1.96` and
82.1% fail `|t| >= 2.78`
([Hou, Xue and Zhang 2020](https://doi.org/10.1093/rfs/hhy131); gross of costs). The
apparently contradictory 82.4% of
[Jensen, Kelly and Pedersen (2023)](https://doi.org/10.1111/jofi.13249) decomposes
additively, and the decomposition is the finding: +20.6pp from construction, +5.7pp from
dropping 34 factors the original papers found insignificant, **+21.1pp from switching the
estimand from raw return to CAPM alpha**, and **exactly zero** from the Bayesian
machinery that gives the paper its name or from the global evidence. Per-category
replication rates must never be quoted without their hurdle: "classic value and
profitability survive" is true at `|t| >= 1.96` and false at 2.78. **Never quote a
replication percentage as evidence of an investable edge.**

**Published effects decay**, more so in liquid large-capitalisation stocks where
implementation is cheapest ([McLean and Pontiff 2016](https://doi.org/10.1111/jofi.12365)),
and hundreds of attempted factors make `t > 2` far too permissive — a new factor needs
`|t| > 3.0` and the family-wise hurdle rises over time
([Harvey, Liu and Zhu 2016](https://doi.org/10.1093/rfs/hhv059)). Their structural model
puts a genuinely true factor's mean return at 0.55%/month, **6.6%/yr at an imposed 15%
volatility** — in-sample, gross, before decay, so an upper bound on what any factor
sleeve should be expected to deliver.

**Costs must alter the trading rule, never appear as a haircut.** By turnover tier the
measured haircut is 17% (low), 52% (mid) and **144%** (high), with four of six
high-turnover strategies strictly negative net
([Novy-Marx and Velikov 2016](https://www.nber.org/papers/w20721)). The usable rule is
`cost bp/month ≈ k × one-sided turnover %` with `k` in [1.0, 1.7]. Two silent
factor-of-two traps: **one-sided turnover means `0.5 sum_i |dw_i|`**, and `|Q/V|` in the
square-root impact law `bp ≈ 11 sqrt(|Q/V|)` is **in percent, not as a fraction** — the
two readings differ by an order of magnitude. At retail scale trade/ADV is far below
0.1%, so impact vanishes and what binds is the spread; treat anything above 50% monthly
one-sided turnover as not retail-implementable regardless of gross Sharpe.

**Manager skill exists, is small, and need not accrue to investors.** Over 1984–2006
value-weighted *gross* alpha was statistically zero and *net* alpha negative by roughly
the expense ratio ([Fama and French 2010](https://doi.org/10.1111/j.1540-6261.2010.01598.x)). The
usable number is not the point estimate but the ratio: true gross alpha's
cross-sectional standard deviation is about **1.25%/yr** against an average standard
error on a single fund's alpha of **3.36%/yr** — **noise is 2.7 times signal**, so any
observed alpha must be shrunk hard, using *that estimate's own* standard error. Berk and
van Binsbergen reconcile persistent dollar value added with little scalable investor net
alpha: skilled managers expand until fees and scale absorb the advantage.

**Portfolio construction is an estimation problem.** Across seven datasets none of 14
optimised models consistently beat equal weight on Sharpe, certainty-equivalent return
and turnover; under one calibration the samples required for dominance were about 3,000
months for 25 assets ([DeMiguel, Garlappi and Uppal 2009](https://doi.org/10.1093/rfs/hhm075)).
That is not a theorem that equal weight is optimal — it makes market weight, equal
weight, drifting buy-and-hold, constrained minimum variance and regularised covariance
**mandatory baselines**. No-short constraints act as implicit shrinkage
([Jagannathan and Ma 2003](https://doi.org/10.1111/1540-6261.00580)). **Risk parity is an
implicit expected-return forecast, not a return-agnostic construction**: ERC is the
maximum-Sharpe portfolio only if correlations are equal *and* all assets share the same
Sharpe. Its empirical case rests almost entirely on financing — on the same 85 years of
CRSP data, substituting a realistic borrowing rate collapses the advantage over 60/40
from **210 bp/yr (p = 0.03) to 29 bp/yr (p = 0.40)**, and the pro-risk-parity study's own
appendix shows the same collapse at a LIBOR spread. Any levered risk-parity figure must
take the financing spread as a required input.

**Capacity-constrained alternatives are mostly compensation for scarce liquidity,
insurance, access, complexity or leverage.** Merger arbitrage resembles selling uncovered
index puts — beta 0.0167 in normal markets and 0.4920 when the market falls more than 4%
below the risk-free rate, with a 10.3% excess return falling to about 4% once costs are
imposed. Catastrophe bonds are insurance beta, not alpha, and are the one candidate whose
capacity constraint is **physical rather than competitive**. Private credit's premium
reflects credit, leverage, origination and illiquidity, with model marks suppressing
observed volatility. Statistical arbitrage's decay is directly measured: the standard
contrarian strategy's daily return fell from 1.38% in 1995 to 0.13% in 2007. Managed-futures
CTAs earned 6.1% gross and insignificantly-different-from-zero net over 1994–2012 on a
~4%-of-assets fee load — **which does not transfer to an exchange-traded fund** charging
0.66–0.98%, and this repository made that error once and records it. Hedge-fund databases
are unsuitable optimiser inputs without point-in-time reconstruction: survivorship bias
0.60%/yr in HFR and 2.24% in TASS, backfill roughly 1.4%/yr, and voluntary reporting
selects both winners and losers so even the *direction* of a generic correction is
unidentified.

**Why an edge can exist without being easy to capture.** Perfect informational efficiency
is internally inconsistent when information is costly
([Grossman and Stiglitz 1980](https://www.aeaweb.org/aer/top20/70.3.393-408.pdf)), and
limits to arbitrage make apparent mispricing risky exactly when the thesis looks
strongest ([Shleifer and Vishny 1997](https://doi.org/10.1111/j.1540-6261.1997.tb03807.x)).
The practical implication is sociological: a published strategy changes the population
trading it, so **mechanism decay is a core falsifier, not a nuisance**, and the ledger
records publication date and performance either side of it.

---

## Where the programme has got to

### The ledger, counted rather than described

Verified directly from [`research/ledger.jsonl`](../../research/ledger.jsonl):
**116 entries, 41 runs, 21 distinct specification hashes, 17 experiment families.**
Recount rather than quoting; the ledger is append-only:

```sh
python3 -c "import json; r=[json.loads(l) for l in open('research/ledger.jsonl') if l.strip()]; print(len(r),'entries',len({x['run_id'] for x in r}),'runs',len({x['spec_hash'] for x in r}),'specs')"
```

| Terminal outcome | Runs | Which |
| --- | ---: | --- |
| `unresolved` | 9 | Phase 1; Exp 001; Exp 007's superseded specification; Exp 010 (3 executions of one specification); Exp 011 (1); Exp 012 (2 executions of one question) |
| `rejected` | 9 | Exp 003 (1); Exp 004 (5 executions of one specification); Exp 007 (1); Exp 010b (2) |
| `exploratory` | 15 | Exp 002 (3); Exp 005 (1); Exp 006 (1); Exp 008 (3); Exp 009 (3); Exp 013 (2); Exp 014 (1); Exp 015 (1) |
| no terminal status | 8 | 3 `failed`, 5 `abandoned` |

**Twenty-one, not forty-one, is the number a deflated-Sharpe trial count starts from —
and it is an upper bound**, because `exp_010b` re-judges data `exp_010` had already spent
and the two are one search, because `exp_012` re-asks `exp_011`'s question with a
different instrument on a shorter window, and because `exp_013`, `exp_014` and `exp_015`
all re-run an earlier falsifier on data it had already spent — `exp_013` on a corrected
census frame, `exp_014` on the US shelf under six comparator bases and `exp_015` on the
ex-US shelf under seven — rather than asking a new question. `exp_014`
additionally declares, in its own frozen file, one uncommitted scratch look that preceded
it, which the ledger cannot see. No run consumed the final holdout. The ledger also contains a
correction to itself: one `abandoned` entry was appended prematurely and for the wrong
run's reason, and a superseding entry says so rather than repairing it in place.

### Advanced

Nothing was promoted. One factor advanced a rung; the rest of what advanced is machinery
and results that are now measurements rather than citations.

- **Value reached `exploratory`** on a pooled +4.7 pp/yr across three regions, and
  **momentum** on +7.3 — both carried by the two non-US regions
  ([Exps 005 and 006](factor-persistence.md)).
- **The cost of naive pooling was measured, not asserted.** Resampling three regions
  independently rather than jointly narrows HML's interval by about 1.5×, and in one cell
  converts `[−2.4, +10.2]` into `[+0.1, +8.1]` — a significant result manufactured
  entirely by treating correlated regions as independent.
- **The excess-growth closed form is confirmed on real data** to 0.09 bp/yr, and the
  exact condition `g_p > max_i g_i` was proved rather than cited.
- **The long-only capture fraction was measured** and found to be a range, not a number:
  0.52 `[0.43, 0.72]` size-neutral against 0.96 market-relative, spanning 0.846 across
  five defensible benchmarks ([Exp 007](long-only-capture.md)).
- **The ex-US product gap is closed as a gap** — twelve products reach `exploratory` on
  delivered exposure against their own region's panel, and substituting the US panel
  would put 16 of 25 below the bar rather than 5 ([Exp 009](factor-products.md)).
- **The deciding metric was corrected by a control rather than by an argument.** A cash
  sleeve supplying nothing scored +0.166 pp/yr of certainty equivalent while losing 0.643
  of growth — a de-risking reward of **+0.809**, 2.7× the materiality threshold, for
  supplying nothing ([decision 0008](../decisions/0008-growth-decides-crra-reports.md)).
  The change is strictly hostile: it removes a reward and moves a family to a worse status.
- **The research loop exists end to end** — frozen specification, hashed input,
  deterministic calculation, adversarial validation, append-only ledger, synthesis — under
  a runner that refuses a confirmatory experiment lacking a benchmark, primary metric,
  cost model, sample policy and rejection rule.

### Failed against a predeclared falsifier

- **Rebalancing as return.** Four clauses fired at once over 35 years
  ([Exp 003](rebalancing-policy.md)).
- **RMW and CMA**, closed on the public files: their pooled premia sit below the smallest
  premium their own pooled windows can resolve. **Neither rejection says the premium is
  zero**; both say the publicly available data cannot sign it
  ([decision 0005](../decisions/0005-factor-premia-closed-on-public-data.md)).
- **The AQR trend series as a marginal sleeve**, on clause (d) under its *absolute*
  reading; `unresolved` under the *relative* reading, which
  [Experiment 008 judges better justified](trend-marginal-value.md#clause-d-re-read-under-both-readings)
  because the absolute reading's bar gets *easier* to clear as the sleeve gets better. A
  second experiment then rejected the same sleeve on a different clause against a
  different comparator.
- **Forty-eight of 109 US and eight of 25 ex-US factor products** — with clause (c),
  decided against an **in-sample fitted** comparator, firing on 40 of those 56. And read
  the count with its frame: Experiment 002 reported 24 of 44 because the 2019Q4 census
  carries no fund with an August fiscal year, and on the corrected frame the funds it
  could not see have a *negative* median shortfall.
- **Four of five listed managed-futures ETFs.** Read those as "this fund does not deliver
  *this benchmark's* exposure" — KMLM's index holds no equity futures while AQR's holds
  nine — never as "this fund is badly run".
- **All ten sleeves in Experiment 010's marginal family.** With the caveat that its
  headline closure is weight-dependent; see [search coverage](search-coverage.md) §1.1.

### Unresolved, which is not the same as negative

- **The Phase 1 ingestion gate.** Thirteen of fifteen cells reproduce; HML's and RMW's
  standard deviations do not, against two independently typeset vintages. Exact
  reproduction is unavailable at any tolerance because no vintage archive exists.
  **Consequence: a systematic 3–5% denominator uncertainty on anything that divides by
  those volatilities.**
- **Momentum's tail**, now that its premium is signed: three regions that crash together
  make the pooled evidence thinnest in exactly the episode a holder would care about.
- **Whether any of it is investable.** Fund-level work is `exploratory` by decision, on a
  72-month unaudited self-reported window with no independent corroboration of any kind.

### Never started

The **deferred financing experiment** and the **frozen construction tournament** have
designs, comparators and falsifiers here and no ledgered run. Leverage remains at zero,
which is correct — it was conditioned on an unlevered edge surviving the protocol. The
construction tournament's block is **not** correct and should be lifted; see
[search coverage](search-coverage.md) §5.

---

## Research protocol

Every experiment has a machine-readable specification committed before its result is
examined.

1. **State the mechanism and falsifier**, naming the deciding quantity **as an
   expression, not as prose, and in units that do not move with the size of the effect.**
   [Experiment 004's clause (d)](trend-marginal-value.md#clause-d-re-read-under-both-readings)
   is the worked example of what happens otherwise: an ambiguously specified clause
   produced a defensible verdict and a defensible opposite verdict from the same two
   numbers.
2. **Check the instrument before freezing.** If the question's minimum detectable effect
   exceeds the effect size that would matter, the experiment cannot answer it.
   [The resolution table](evidence-base.md#1-the-resolution-table--read-this-before-proposing-an-experiment)
   is where to look.
3. **Keep the ledger.** Count every universe, lag, filter, parameter, rebalance rule, cost
   model, objective and abandoned variation. A result is evaluated against the whole
   search.
4. **Use point-in-time data**, and never use an observation before its availability
   timestamp.
5. **Separate discovery and evaluation in time.** Nested walk-forward, embargoed
   overlapping outcomes, an untouched final holdout. Looking once converts a holdout into
   training data.
6. **Correct for search** — family-wise or false-discovery, White's Reality Check, and a
   deflated Sharpe whose trial count is stated as the assumption it is.
7. **Model an executable strategy.** Next-tradable prices; spread, commission, impact,
   fees, borrow, financing, margin, rolls, taxes, partial fills, delisting. Report gross,
   net and stressed-net. **Costs alter the trading rule; they are never a haircut.**
8. **Estimate uncertainty honestly.** Block bootstrap or suitable time-series inference,
   never iid Gaussian Monte Carlo alone.
9. **Report the whole outcome**: geometric and arithmetic return, volatility, downside
   beta, Sharpe with uncertainty, maximum drawdown, time under water, expected shortfall,
   turnover, capacity, worst periods, exposure attribution. No single metric decides.
10. **Carry a control with no value by construction** wherever the metric could reward
    something the sleeve did not supply. Experiment 010's cash control is the model: one
    cell of compute, excluded from the multiple-testing family, and the only reason
    decision 0008's error was found rather than published.
11. **Promote in stages**: paper replication, independent reproduction, frozen shadow
    portfolio, small-capital live test, capacity scaling. A backtest is never permission
    to skip a stage.

**Mandatory hostile tests.** Attempt to kill every successful result with twice the
estimated costs; an execution delay; removal of its best month, year and crisis;
alternate cash rate, benchmark, currency hedge and inflation convention; overnight gaps;
correlation convergence; funding and margin shocks; forced liquidation; fund closure and
backfill; and independent reproduction from the written specification.

For leverage, additionally draw `mu`, covariance and financing cost from an uncertainty
model. Do not approve leverage because a point estimate of `L*` exceeds one.

**Numerical fixtures live in tests, not on this page.** Adding a fixture here rather than
to a test is a regression. They are pinned in `research/tests/unit/test_core_*.py`,
`test_inference_*.py` and `test_studies_*.py`, re-derived in each test from stated inputs.
Three things a test cannot carry: the Erb–Harvey approximation is wrong and deliberately
unimplemented (it wrongly vanishes at `rho = 1` where the exact diversification return is
+1.37%, and it *understates* for every `rho > 0`, which is the opposite of what was
originally recorded here); three constants must be re-derived per parameterisation, never
hardcoded; and **a fixture that disagrees with our own computation is a finding, not a
tolerance to loosen** — the Phase 1 gate is the standing example.

---

## Assumptions and open questions

**Working assumptions**, to be challenged rather than silently embedded: the investable
baseline is a low-cost diversified passive portfolio and is the formal control; the
objective is net geometric growth subject to a drawdown or expected-shortfall constraint,
**declared as a preference justified by Breiman rather than derived**; strategies must be
implementable by the intended investor at realistic scale; no expected alpha is accepted
because a historical mean is positive; and leverage begins at zero until an unlevered edge
survives the protocol. **None has.**

**Open decisions**, in the order they bind.

1. **Who is the modelled investor** — taxable or tax-advantaged, horizon, currency,
   liabilities, cash flows, drawdown tolerance, accessible instruments? **Open, and the
   binding constraint on producing an allocation rather than a design map.** Individual
   experiments declared CRRA `gamma = 3` for their own comparisons; that is a
   per-experiment preference, not a product decision.
2. **Which point-in-time datasets are licensed and rich enough?** Open, and the binding
   constraint on every investable conclusion
   ([decision 0002](../decisions/0002-no-research-grade-free-price-source.md)). Required
   contents in [evidence base](evidence-base.md) §4.
3. **Which benchmark may an edge budget's factor line book its capture against?** The
   fraction is measured — 0.52 size-neutral, 0.96 market-relative — but the gap between
   them is a size premium, and booking it under value counts it twice.
4. **What capital scale, tax model, leverage source, margin rules and liquidity reserve
   define implementability?**
5. **What estimation window and regime-conditioning scheme should the covariance matrix
   use**, given the documented bond–stock beta sign flip?
6. **What is the net-of-cost equivalent of each gross figure here?** Partly answered.
   Every academic long-short figure remains an upper bound of unknown tightness.
7. **Which factor themes survive both the strict Hou–Xue–Zhang construction and the
   Jensen–Kelly–Pedersen one, then remain positive after executable costs?** Narrowed, not
   closed. The equal-weighted variant was **not run** — the library distributes none —
   which matters because that single choice moves published replication rates from 35% to
   58.6%.
8. **Does risk-constrained Kelly beat fractional Kelly on real returns?** Untested and
   correctly deferred: it sizes an edge and there is no edge to size.
9. **How many days of autonomous cash liquidity are required?** Unsized.

**Two questions are closed and recorded as closed** rather than deleted, because a reader
needs to know they were asked. *What objective defines "beat the market"* — closed on the
objective (net geometric growth, as a preference), open on horizon and liability model,
with the answer on benchmarks being that there is no single one and the three never
aggregate. *How the ledger prevents undisclosed researcher degrees of freedom* — closed by
implementation, except that the ledger does **not** solve dependence between trials, and
no procedure recovers that automatically.

---

## Consequence for this repository

1. **No optimiser ships.** Anything that searches a weight space belongs in `research/`
   with a frozen specification and a ledger entry. The client-side optimiser this section
   used to argue against has been deleted; its defects are kept in the
   [engine specification](portfolio-engine-specification.md) as reasons, not as a
   description of code that still exists.
2. **Steps 1–5 of the original build order are done.** What remains is portfolio
   combination and stress testing, then fractional/risk-constrained Kelly with live
   financing. **Step 7 is correctly blocked** — it sizes an edge and there is none.
   **Step 6's block should be lifted**: a construction tournament compares weighting
   methods on assets that already exist and does not need a promoted sleeve
   ([search coverage](search-coverage.md) §5).
3. **Any estimated alpha passes through shrinkage before it reaches a sizing function**,
   using *that estimate's own* standard error. Realised factors here run 0.016 to 0.913;
   hardcoding a reference would be wrong for nearly every fund in both directions.
   Omitting shrinkage entirely is the most likely catastrophic sizing error in a Kelly
   system.
4. **The client may render a research finding**, but only from `src/content/`, only with
   its status, `as of` date, interval and source attached, and never aggregated across
   benchmarks ([decision 0007](../decisions/0007-application-may-render-research.md)). A
   number hardcoded in a route is a defect, and no "rebalancing bonus" language is
   permitted anywhere.
5. **Nothing was promoted** ([decision 0004](../decisions/0004-no-sleeve-promoted.md)), and
   the conditions that would change that are in the design map above. Published gross
   returns are hypothesis inputs, not portfolio return forecasts.
</content>
