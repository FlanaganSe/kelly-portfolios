# Researching portfolio edge without fooling ourselves

**Question.** Can leverage, rebalancing, drawdown controls, diversifiers, active
funds, and systematic factors be combined to improve an investable portfolio, and
how should this repository test that claim?

**Decision informed.** This page defines which hypotheses deserve implementation,
what evidence would reject them, and the minimum validation standard before any
result is shown as financially meaningful. Selecting products, giving personalised
advice, and claiming that a strategy will beat the market are out of scope.

**Conclusion.** No reviewed method mathematically guarantees market
outperformance. The defensible objective is narrower: test whether a small number
of economically distinct return sources can improve **net geometric return or a
predeclared investor utility** relative to a cheap investable benchmark, while
keeping estimation error, ruin, drawdown, liquidity, and implementation costs
inside explicit limits.

The most credible first research portfolio is not an optimized collection of many
backtested signals. It is a simple passive benchmark plus separately measured
sleeves for value/profitability, momentum, and diversified time-series trend, with
conservative volatility targeting and no leverage until unlevered results survive
hostile out-of-sample replication. Rebalancing is a portfolio-maintenance policy,
not assumed alpha. Tail options are insurance whose crisis payoff must justify
their normal-time drag. Active funds and betting-against-beta begin with a more
sceptical prior because net persistence and implementability evidence are weak.

Adversarial verification of the strongest specific claims in this literature
sharpened that conclusion in one direction only. What survives is mostly either an
identity true by construction — which constrains how much of an assumed premium is
harvestable, and supplies none — or a negative result. The rebalancing bonus is an
accounting identity measured against a benchmark nobody can hold, and rebalancing
is structurally a short straddle on relative performance. Protective puts lose to
simply holding less equity once the benchmark is return-matched. Most published
anomalies do not replicate at the hurdle their own critics advocate. Active gross
alpha is zero and net alpha is negative by roughly the fee. **No positive,
replicated, net-of-cost edge was established.** The working hypothesis that the
honest answer is low-cost diversified beta at modest sub-Kelly leverage plus
behavioural discipline is consistent with everything verified here — and is not
itself tested by any of it.

## What is established, and what is not

### Portfolio theory and leverage

Markowitz shows how to find minimum-variance portfolios for a target expected
return when expected returns and covariance are known. It does not show that
variance captures every relevant risk or that estimated efficient portfolios
outperform out of sample ([Markowitz 1952](https://doi.org/10.1111/j.1540-6261.1952.tb01525.x)).
With a risk-free asset, identical borrowing and lending rates, frictionless
markets, and mean-variance preferences, leverage only changes exposure to the
tangency portfolio; linear scaling alone does not manufacture alpha or improve
Sharpe ([Tobin 1958](https://doi.org/10.2307/2296205)).

Kelly maximizes expected log wealth in a specified repeated-bet model
([Kelly 1956](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x)). In a
one-risky-asset diffusion, the idealized exposure is

\[
L^* = \frac{\mu-r}{\sigma^2}.
\]

Adding an exposure-proportional financing and implementation cost \(c\), expected
log growth is approximately

\[
g(L) \approx r + L(\mu-r-c) - \tfrac12L^2\sigma^2.
\]

Leverage therefore improves modeled geometric growth only below the true optimum;
beyond it, leverage reduces growth. Two boundaries follow from the same quadratic
and are true by construction: growth falls back to exactly the risk-free rate at
\(2L^*\), and turns negative above
\(L^*+\sqrt{(L^*)^2+2r/\sigma^2}\)
([Peters 2011](https://arxiv.org/pdf/0902.2965)). The decision-relevant
ceiling is \(2L^*\), not the zero-growth root; above \(2L^*\) leverage loses to
holding cash.

Two traps for any script computing \(L^*\). First, \(\mu\) must be the arithmetic
Itô drift and \(\sigma\) the instantaneous volatility; substituting a CAGR or a
coarsely sampled volatility gives the wrong answer. Second, the widely repeated
value \(L^*\approx1.54\) is **not** a measured S&P quantity — it comes from
stylised illustrative parameters (\(\mu-r=5\%\), \(\sigma=18\%\)). Peters states
that his own framework overestimates optimal leverage, listing continuous
rebalancing, zero costs, lognormality, certain knowledge of \(\mu\) and \(\sigma\),
and no borrowing spread as the reasons, and conjectures real optimal leverage for a
broad index is near 1.

The optimum is especially fragile because its numerator is an estimated expected
return. Relative to an *estimated* Kelly fraction, downscaling is close to free: if
the true mean is half the estimate, betting \(0.5\hat{f}^*\) attains maximum growth
while \(\hat{f}^*\) gives zero and \(1.5\hat{f}^*\) gives negative growth
(Thorp 2006, "The Kelly Criterion in Blackjack, Sports Betting and the Stock
Market", sec. 7.3). Real portfolios also have jumps, changing margin, unequal
borrowing and lending rates, taxes, and forced liquidations, none of which the
diffusion expression captures.
Kelly is optimal for log utility, not for every investor, horizon, liability, or
drawdown preference ([Samuelson 1979](https://doi.org/10.1016/0378-4266%2879%2990023-2));
full Kelly is relative risk aversion of exactly 1, and every CRRA optimum is
\(1/\gamma\) times Kelly against empirical \(\gamma\) estimates of 2–10.

Leverage aversion is a plausible equilibrium mechanism: constrained investors may
overpay for high-beta assets, leaving relatively better risk-adjusted returns in
low-beta assets that unconstrained investors lever. Cross-asset evidence supports
this betting-against-beta hypothesis
([Frazzini and Pedersen 2014](https://doi.org/10.1016/j.jfineco.2013.10.005)),
but a later replication finds that construction choices, costs, and other factor
exposures explain much of the result
([Novy-Marx and Velikov 2022](https://doi.org/10.1016/j.jfineco.2021.05.023)).
On US equities 1968–2017, BAB's headline Sharpe of 1.08 comes from a non-standard
rank weighting that is 99.6% monthly-correlated with equal weighting; value
weighted, Sharpe is 0.49 and the FF5 alpha is 24 bps/month (t = 1.63). After costs
the generalised alpha is 16 bps/month (t = 1.20), with the surviving return loading
on profitability and investment. Note what does *not* follow: the 56 bps/month
excess return survives and is significant — what vanishes is the alpha. This is a
hypothesis about a risky premium, not a free lunch.

Scope limits worth keeping. The critique is US-only, while the original spans 20
equity markets plus Treasuries, credit, FX and futures; the AQR-side defence
(Asness, Frazzini, Gormsen and Pedersen, "Betting against correlation", JFE 2020)
has not been read here. It does not generalise to "the low-volatility anomaly is
dead" — the standard-weighting low-volatility literature was not tested. Both
sides are financially interested.

### Rebalancing

For constant long-only weights and diffusion-like returns, portfolio log growth
has an excess-growth term:

\[
g_p \approx \sum_i w_i g_i +
\tfrac12\left(\sum_i w_i\sigma_i^2-\sigma_p^2\right).
\]

That nonnegative arithmetic term compares the portfolio with the weighted log
growth of its components. It does **not** prove that a periodically rebalanced
portfolio beats an untouched buy-and-hold portfolio, whose weights drift. The
terminology and decomposition are treated carefully by
[Hallerbach 2014](https://doi.org/10.1057/jam.2014.29).

Three results sharpen this from a caution into a constraint. All were verified by
independent re-derivation, not only by reading the source.

**The benchmark is not investable.** Diversification return is *defined* as
\(g_p-\sum_i w_i g_i\), and \(\sum_i w_i g_i\) is not the return of any portfolio
one can hold ([Willenbrock 2011](https://arxiv.org/abs/1109.1256)). The
investable comparison is buy-and-hold, whose geometric mean may be higher or lower.
A random walk produces a positive measured diversification return with no skill
involved.

**Rebalancing is a short straddle on relative performance.** Over two periods the
exact identity is
\(R_{\text{REBAL}}-R_{\text{HOLD}}=-w_Sw_B\kappa_1\kappa_2\),
where \(\kappa_t\) is the difference in simple returns between the two assets
([Rattray et al. 2020](https://people.duke.edu/~charvey/Research/Published_Papers/P145_Strategic_rebalancing.pdf)). Rebalancing
therefore *loses* when relative performance trends and gains only on reversal, and
the loss concentrates in crises: the monthly-rebalanced 60/40 had a maximum
drawdown 5 percentage points worse than buy-and-hold in 2007–2009.

**There is no expected profit to harvest.** Under Markov prices the long-rebalanced
/ short-buy-and-hold trade has exactly zero expected profit
([Chambers and Zdanowicz 2014](https://www.hec.ca/finance/Fichier/Chambers2014.pdf)).
Rebalancing raises expected terminal wealth only when relative returns mean-revert,
in which case the gain is a transfer from trend followers — a contrarian bet, not a
property of variance reduction.

One live objection to this repository's premise sits here and is *not* settled.
Chambers and Zdanowicz's zero-expected-profit result concerns expected terminal
*wealth*. In their own example the rebalanced portfolio does have higher expected
**log** wealth (1.874% vs 1.867% per year), which they dismiss as "an arbitrary
nonlinear transformation of wealth". That dismissal is a stance, not a theorem, and
it is precisely the premise a Kelly investor rejects. Settling it is open question 2
below.

Rebalancing should therefore be tested as an explicit rule—calendar, threshold,
or no rebalance—from identical starting weights and cash flows. A variance
identity must never be reported as realized alpha, and the correct diagnostic for
whether rebalancing adds value is the serial dependence of \(\kappa_t\), not the
diversification-return statistic.

### Drawdowns, crisis diversification, and tail protection

Ordinary-state correlation is not a crisis guarantee. International equity
correlations rise in bear markets, so unconditional covariance and iid Gaussian
simulation understate joint left-tail risk
([Longin and Solnik 2001](https://doi.org/10.1111/0022-1082.00340)). Gold has been
an average hedge and a short-lived safe haven in some countries and samples, not a
universal permanently negative-correlated asset
([Baur and Lucey 2010](https://doi.org/10.1111/j.1540-6288.2010.00244.x)).
Long-duration government bonds are not a regime-independent hedge, and this is now
documented rather than merely plausible. The sign of the nominal bond–stock beta was
positive circa 1970–2000, negative circa 2000–2022, and turned positive again in
2023 through 2025Q2, across the US, UK and Eurozone
([Campbell et al. 2025](https://www.nber.org/papers/w34323), as of 2026-08-11;
NBER working paper, not peer reviewed). High risk premia amplify the magnitude of
the beta in *both* regimes, so in a positive-beta regime stress makes bonds
co-crash harder. “Safe haven” must always specify shock, currency, duration, and
horizon.

The direct consequence for this repository is that a covariance matrix estimated
over a long full sample averages two opposite regimes and describes neither, while
one estimated over 2000–2020 is fitted to a regime that has already ended. Any
allocation engine must state which regime its inputs describe.

Diversified time-series momentum is the strongest researched candidate for a
dynamic crisis sleeve. Evidence spans many futures markets
([Moskowitz, Ooi, and Pedersen 2012](https://doi.org/10.1016/j.jfineco.2011.11.003))
and a reconstructed history back to 1880
([Hurst, Ooi, and Pedersen 2017](https://ssrn.com/abstract=2993026)). It is not an
instant hedge: slow signals miss gaps and sharp reversals cause whipsaw. Early data
are reconstructed, authors have industry affiliations, and volatility scaling
explains a material part of some published performance
([Kim, Tse, and Wald 2017](https://doi.org/10.1016/j.jempfin.2016.12.004)).

Inverse-volatility exposure has improved factor Sharpe ratios in historical tests
because volatility persistence was not matched by proportional changes in expected
return ([Moreira and Muir 2017](https://doi.org/10.1111/jofi.12513)). It reacts
after volatility rises, can miss jumps, and may re-enter too slowly after a sharp
rebound. It must be compared with the same volatility scaler applied to the passive
benchmark, not only with an unscaled benchmark.

Long out-of-the-money puts supply immediate convexity, unlike trend, but repeatedly
buying them pays option premium, skew, spread, and time decay. The historical
variance risk premium is evidence that this insurance is priced
([Bollerslev, Tauchen, and Zhou 2009](https://doi.org/10.1093/rfs/hhp008)). Tail
insurance can improve expected shortfall or utility while lowering long-run CAGR;
calling that failure or success requires declaring the objective first.

The benchmark choice decides the answer, so it must be fixed before the test. Over
1986-07-01 to 2016-05-19 the Cboe S&P 500 5% Put Protection Index earned 2.5% per
year compound excess of cash against 5.8% for the index, and a **constant-weight,
daily-rebalanced** 36.5% equity / 63.5% cash portfolio earned the same 2.5%
([Israelov 2019](https://images.aqr.com/-/media/AQR/Documents/Journal-Articles/Pathetic-Protection-JAI-Wint19.pdf); gross of costs, and the
author was an AQR principal whose firm is structurally short this trade). Comparing
a protected portfolio against the *fully invested* index therefore flatters it, and
the naive proportional match 2.5/5.8 = 43.1% is wrong.

Two limits on that result matter as much as the result. The much-quoted finding
that divesting beat protection on drawdowns 97–100% of the time depends on the
36.5% weight being fitted **ex post**; under the same paper's *ex ante*
implementable rule (averaging about 84% equity) the protected portfolio has better
fifth-percentile drawdowns. And in the paper's own simulation with no volatility
risk premium, protection wins the first-percentile tail. The defensible claim is
about the correct benchmark, not about protection being universally dominated.

### Factors and manager alpha

Momentum, value, profitability, and conservative investment have long-run evidence
and economic or behavioral rationales, but they are risky premia or anomalies—not
contractual alpha:

- Cross-sectional momentum is documented by
  [Jegadeesh and Titman 1993](https://doi.org/10.1111/j.1540-6261.1993.tb04702.x),
  but it has high turnover and state-dependent crashes during rebounds after bear
  markets ([Daniel and Moskowitz 2016](https://doi.org/10.1016/j.jfineco.2015.12.002)).
- Value and size enter the Fama–French three-factor model
  ([Fama and French 1993](https://doi.org/10.1016/0304-405X%2893%2990023-5)). Value can
  underperform for long periods, and book value is less comparable when intangible
  investment differs across firms and industries.
- Profitability and conservative investment have independent evidence
  ([Novy-Marx 2013](https://doi.org/10.1016/j.jfineco.2013.01.003),
  [Fama and French 2015](https://doi.org/10.1016/j.jfineco.2014.10.010)). “Quality”
  is not one factor; vendor mixtures of profitability, leverage, stability, and
  growth are separate specifications and must be counted as such.
- Size by itself is a weak implementation candidate. With NYSE breakpoints and
  value-weighted returns, 65.0% of 452 published anomalies fail \(|t|\ge1.96\) —
  only 158 replicate — and 82.1% fail the multiple-testing hurdle \(|t|\ge2.78\)
  ([Hou, Xue, and Zhang 2020](https://doi.org/10.1093/rfs/hhy131); Jan 1967 –
  Dec 2016, Newey–West, **gross of transaction and shorting costs**). Microcaps
  drive many apparent results: they are 3.2% of market capitalisation but 60.7% of
  the stock count, and the equal-weighted all-breakpoint specification that most
  original studies used raises the replication rate from 35% to 58.6% by itself.

Per-category replication rates must never be quoted without their hurdle, because
the ranking survives the change of hurdle but the conclusion does not. At
\(|t|\ge1.96\): investment 73.7%, momentum 63.2%, profitability 44.3%, value
42.0%, intangibles 25.2%, trading frictions 3.8%. At the authors' own preferred
\(|t|\ge2.78\): momentum 49.1%, investment 50.0%, profitability 17.7%, intangibles
10.7%, value 10.1%, trading frictions 1.9%. "Classic value and profitability
survive" is true at the lax hurdle and false at the strict one. Note also that the
authors own and market the q-factor model, whose own factors are investment and
profitability — the two categories their procedure ranks best.

**This is the largest unresolved dispute bearing on anything this repository would
build.** [Jensen, Kelly, and Pedersen 2023](https://doi.org/10.1111/jofi.13249)
report that the majority of factors *do* replicate across 93 countries under a
hierarchical Bayesian model. It has not been read here, and it directly contests
both the replication rates above and the discovery threshold below. Treat neither
as settled until it has been.

Published effects decay. Across 97 predictors, returns were lower out of sample
and lower again after publication, consistent with both statistical bias and
arbitrage/crowding ([McLean and Pontiff 2016](https://doi.org/10.1111/jofi.12365)).
Decay is largest in liquid, large-capitalisation, low-idiosyncratic-risk stocks, so
whatever premium survives publication is concentrated where implementation costs
are highest. Hundreds of attempted factors also make the traditional \(t>2\)
discovery rule too permissive
([Harvey, Liu, and Zhu 2016](https://doi.org/10.1093/rfs/hhv059)): a new factor
needs \(|t|>3.0\), the authors' own stated minimum is 3.18, and the family-wise
hurdle rises over time to 3.78 (2012) with a projected 4.00 (2032). Their
structural model puts the mean return of a genuinely true factor at 0.55% per month
— 6.6% per year at an *imposed* 15% volatility, an annual Sharpe of 0.44, with
about 70% of true factors below 0.5. That figure is in-sample, gross, and before
post-publication decay, so it is an upper bound on what any factor sleeve should be
expected to deliver. The authors explicitly do not endorse a blanket \(|t|<3.0\)
rejection for factors developed from first principles.

Past winning active funds are not a reliable shortcut. Survivor-controlled and
factor-adjusted studies find that expenses and common exposures explain most
mutual-fund persistence, with stronger persistence among bad funds than superior
ones ([Carhart 1997](https://doi.org/10.1111/j.1540-6261.1997.tb03808.x)); bootstrap
evidence finds few funds whose expected benchmark-adjusted return covers their
costs ([Fama and French 2010](https://doi.org/10.1111/j.1540-6261.2010.01598.x)).
Over Jan 1984 – Sep 2006, value-weighted *gross* alpha was statistically zero
(three-factor +0.13%/yr, t = 0.40; four-factor −0.05%/yr, t = −0.15; CAPM
−0.18%/yr, t = −0.49) while *net* alpha was negative by roughly the expense ratio
(CAPM −1.13%/yr, t = −3.03; three-factor −0.81%/yr, t = −2.50; four-factor
−1.00%/yr, t = −3.02). "Gross" there means before expense ratios only — it is
still net of trading costs, so zero gross alpha means managers earn back their
trading costs but not their fees.

This evidence does not prove that no manager has skill; genuine dispersion exists
and is small. Taking true gross alpha as normal with mean zero, its cross-sectional
standard deviation is about 1.25% per year, so 15.87% of funds exceed 1.25%/yr and
2.28% exceed 2.50%/yr — against an average standard error on a single fund's alpha
of 0.28% per month, or 3.36% per year. The noise is roughly 2.7 times the signal.
That ratio, not the point estimates, is the usable result: it makes point-in-time,
net-of-all-cost, forward persistence the required test, and it implies that any
observed alpha must be shrunk hard before it is believed.

## Numerical fixtures

These are closed-form, need no market data, and were each recomputed independently
of the paper that states them. They belong in tests, not in prose; they live here
only until a test runner exists, and this section should be cut down to a pointer
once they do. They satisfy the root `AGENTS.md` requirement for "at least one
fixture computed independently of the implementation under test".

| Fixture | Inputs | Expected result |
| --- | --- | --- |
| Diversification return, exact | Two assets, equal weights, returns +25%/−10% and +50%/−20%, \(\rho=1\) | \(g_A=6.0660\%\), \(g_B=9.5445\%\), \(\sum w_ig_i=7.8053\%\), \(g_p=8.1087\%\), DR = **+0.3035%** |
| Erb–Harvey form is wrong | Same, and \(\sigma=[5,10,20,35,50]\%\) equal-weighted | \(\tfrac12(1-1/N)\bar\sigma^2(1-\bar\rho)\) does not vanish correctly at \(\bar\rho=1\); overstates by 10.6% on the dispersed-vol case |
| Rebalance identity | \(w_S=0.6\), \(w_B=0.4\), \(\kappa_1=\kappa_2=-40\%\) | \(R_{\text{REBAL}}-R_{\text{HOLD}}=-3.84\) pp exactly; coefficient \(-w_Sw_B=-0.24\) |
| Zero-expected-profit test | Two assets, i.i.d. ±25%/−20% at \(p=0.5\), equal weights, two periods, 16 paths | \(E[W_T]=1.050625\) for **both** strategies; long/short trade \(E[\text{profit}]=0\), s.d. \$0.02531 |
| Kelly boundaries | \(\mu-r=5\%\), \(\sigma=18\%\), \(r=5\%\) | \(L^*=1.5432\); growth = \(r\) at \(3.0864\); growth = 0 at \(3.8816\) |
| Expected maximum Sharpe | \(N\) independent zero-skill trials | \(\text{maxZ}=(1-\gamma)\Phi^{-1}(1-1/N)+\gamma\Phi^{-1}(1-1/(Ne))\), \(\gamma=0.5772156649\); at \(N=100\) gives 2.5306 against an exact 2.5076 |

Three constants must be **re-derived per parameterisation, never hardcoded**: the
36.5% return-matched equity weight, the \$0.050625 per-path gap, and the −3.84 pp
two-period figure (its multiperiod analogue in the same paper is −5.3 pp). The
0.44 prior Sharpe scales as \(\sqrt{240/N_{\text{months}}}\).

Two implementation traps are worth recording because both are easy to get wrong
and neither is visible in the formula. In the deflated Sharpe ratio,
\(V[\{SR_n\}]\) is the variance of Sharpe ratios *across trials*, not the sampling
variance of one Sharpe ratio, and \(N\) must be the number of *independent* trials.
In the manager-skill shrinkage, an annual alpha is twelve times a monthly
intercept, so the standard error annualises as \(\times12\), never \(\times\sqrt{12}\).
The resulting shrinkage factor is
\(\sigma^2_{\text{true}}/(\sigma^2_{\text{true}}+SE^2)=1.25^2/(1.25^2+3.36^2)=0.121\):
an observed 5%/yr alpha implies a posterior of about 0.6%/yr.

## Candidate hypotheses and rejection rules

| Candidate | Plausible source | Required comparison | Reject or cap when |
| --- | --- | --- | --- |
| Value plus profitability | Risk or behavioral premium | Cheap broad index; matching factor exposures | Net result vanishes outside microcaps, one region, or one definition |
| Cross-sectional momentum | Underreaction/behavior; possibly risk | Same universe without the signal | Costs erase it or rebound crashes violate the risk budget |
| Diversified time-series trend | Slow behavioral adjustment; crisis convexity | Cash and buy-and-hold, each with identical volatility scaling | Unscaled signal has no value, or net crisis benefit depends on selected episodes |
| Volatility targeting | Volatility is more forecastable than return | Fixed exposure at equal realized risk | Benefit disappears with lagged inputs, gaps, caps, or financing |
| Threshold rebalancing | Maintains risk and may harvest relative oscillation | Untouched shares and calendar rebalance | Turnover/tax dominates or result requires tuned bands |
| Levered diversified portfolio | Access to a higher-Sharpe base portfolio | Same unlevered portfolio and benchmark | Robust growth optimum includes or falls below 1× |
| Betting against beta | Leverage constraints | Tradable value-weighted BAB with factor controls | Alpha disappears after microcap, financing, borrow, and factor adjustments |
| Tail puts | Purchased jump convexity | Cash, trend, put spreads, and collars at equal budget | Crisis utility gain does not justify long-run premium and spread |
| Active-fund selection | Persistent manager skill | Investable index plus matched factors | Frozen selection rule has no future net alpha or depends on surviving funds |

Strategies are not additive merely because their backtests have low full-sample
correlation. The combined portfolio must expose common dependence on leverage,
liquidity, volatility estimation, short borrow, equity rebounds, and crowded exits.

## Research protocol for scripts

Every experiment must have a short machine-readable specification committed
before its evaluation result is examined:

1. **State the mechanism and falsifier.** Record universe, signal, holding period,
   expected adverse regime, capacity, benchmark, and the result that rejects it.
2. **Keep an experiment ledger.** Count every universe, lag, filter, parameter,
   rebalance rule, cost model, objective, and abandoned variation. A successful
   result is evaluated against the entire search, not only the final script.
3. **Use point-in-time data.** Preserve delisted assets, original identifiers,
   corporate actions, dividends, fund closures, index membership, accounting
   release timestamps and revisions, borrow availability, and data-vendor vintage.
4. **Separate discovery and evaluation in time.** Use nested rolling or expanding
   walk-forward evaluation, embargo overlapping outcomes, and keep a final holdout
   untouched. Looking once converts a holdout into training data.
5. **Correct for search.** Use a family-wise or false-discovery procedure, White's
   bootstrap Reality Check
   ([White 2000](https://doi.org/10.1111/1468-0262.00152)), and a Deflated Sharpe
   Ratio that incorporates non-normal returns, sample length, and the effective
   number of trials
   ([Bailey and López de Prado 2014](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551)).
6. **Model an executable strategy.** Use next-tradable prices and include spread,
   commission, market impact, fund fees, borrow and recall, financing and margin,
   futures rolls and collateral, taxes when relevant, partial fills, and delisting
   losses. Report gross, net, and stressed-net results.
7. **Estimate uncertainty honestly.** Returns are autocorrelated, fat-tailed,
   heteroskedastic, and cross-dependent. Use block bootstrap or suitable
   time-series inference; never rely only on iid Gaussian Monte Carlo.
8. **Report the whole outcome.** At minimum: geometric and arithmetic return,
   volatility, downside beta, Sharpe with its uncertainty, maximum drawdown,
   time under water, expected shortfall, turnover, capacity, worst periods, and
   exposure attribution. No single metric decides promotion.
9. **Demand untuned robustness.** Test predeclared neighboring parameters,
   non-overlapping eras, post-publication data, major regions, alternate reputable
   data sources, value weighting, and exclusion of microcaps.
10. **Promote in stages.** Paper replication, independent code/data reproduction,
    frozen shadow portfolio, small-capital live test, then capacity scaling. A
    backtest is evidence for further testing, never permission to skip a stage.

### Mandatory hostile tests

Attempt to kill every successful result with twice the estimated costs; an
appropriate execution delay; removal of its best month, year, and crisis; alternate
cash rate, benchmark, currency hedge, and inflation convention; volatility-clustered
and cross-asset stress paths; overnight gaps; correlation convergence; funding and
margin shocks; missing prices and halted markets; forced liquidation; fund closure
and backfill; and independent reproduction from the written specification without
the original implementation.

For leverage, additionally draw plausible \(\mu\), covariance, and financing cost
from an uncertainty model. Do not approve leverage merely because a point estimate
of \(L^*\) exceeds one. Require the choice to remain solvent under the joint stress
and to remain above one across a predeclared high proportion of plausible inputs.
Fractional Kelly is a conservative sizing candidate, not a cure for a nonexistent
or poorly estimated edge.

## Assumptions and open questions

The working assumptions, to be challenged rather than silently embedded, are:

- the investable baseline is a low-cost, diversified passive portfolio;
- the objective is net geometric growth subject to a drawdown or expected-shortfall
  constraint, but the precise utility and horizon are not yet chosen;
- strategies must be implementable by the intended investor at realistic scale;
- no expected alpha is accepted solely because a historical mean is positive; and
- leverage begins at zero until an unlevered edge survives the research protocol.

Open decisions must be settled before performance code is authoritative:

1. Who is the modeled investor—taxable or tax-advantaged, horizon, currency,
   liabilities, cash flows, drawdown tolerance, and accessible instruments?
2. What exact benchmark and objective define “beat the market”: terminal wealth,
   log growth, inflation-adjusted return, expected utility, or downside-constrained
   return? This is not merely a preference to declare. Chambers and Zdanowicz
   attack log wealth directly as "an arbitrary nonlinear transformation", and a
   repository named for Kelly cannot leave that unanswered.
3. Which point-in-time datasets are licensed, reproducible, and rich enough to
   model delistings, publications, spreads, borrow, futures, and options?
4. What capital scale, tax model, leverage source, margin rules, and liquidity
   reserve define implementability?
5. How will the experiment ledger prevent undisclosed researcher degrees of
   freedom across code revisions and researchers? Note that the effective number of
   independent trials is unrecoverable retroactively, so the ledger must start
   before the first backtest, not after.
6. Does [Jensen, Kelly, and Pedersen 2023](https://doi.org/10.1111/jofi.13249)
   overturn the replication rates and discovery threshold above, or only reframe
   them? This determines whether any factor sleeve belongs here at all, and it is
   the single highest-value unread source.
7. What is the net-of-cost equivalent of each gross figure on this page? No source
   cited here deducts transaction costs, shorting costs, or capacity constraints.
   Every replication rate, premium, and Sharpe ratio above is an upper bound of
   unknown tightness.
8. Does risk-constrained Kelly beat fractional Kelly on bootstrapped historical
   returns? It does so by about 34% in growth at matched drawdown risk on the
   finite-outcome case in
   [Busseti, Ryu, and Boyd](https://web.stanford.edu/~boyd/papers/pdf/kelly.pdf), but the
   advantage vanished on that paper's own fat-tailed mixture — the case it says
   resembles a real portfolio problem — and only two synthetic single draws were
   ever tested.
9. What estimation window and regime-conditioning scheme should the covariance
   matrix use, given the documented bond–stock beta sign flip?

## Consequence for this repository

Do not extend the current optimizer or label its output Kelly-optimal. The next
implementation change to financial math must first install a test runner, define
the investor objective and benchmark, and establish a point-in-time data contract.
Then build small, independent research modules in this order:

1. return, wealth, cost, turnover, drawdown, expected-shortfall, and attribution
   primitives with independently calculated fixtures;
2. passive buy-and-hold plus calendar and threshold rebalancing;
3. volatility scaling applied identically to benchmark and candidate sleeves;
4. canonical factor and time-series-trend replications with frozen specifications;
5. walk-forward evaluation, block bootstrap, experiment ledger, and multiple-test
   diagnostics;
6. portfolio combination and stress testing; and only then
7. fractional/risk-constrained Kelly and leverage with live financing and margin
   rules.

Three of those steps have a specific first move that the evidence now fixes.

- Step 1's fixtures are already written: the table under "Numerical fixtures" is
  closed-form and needs no data, so the primitives can be tested before any market
  data contract exists.
- Step 5's trial ledger must begin before the first backtest. Every deflated-Sharpe
  threshold depends on the effective number of independent trials, and that number
  cannot be reconstructed after the fact.
- Any estimated alpha must pass through a shrinkage step before it reaches a sizing
  function. With signal 1.25%/yr against noise 3.36%/yr the factor is 0.121, and
  omitting it is the most likely catastrophic sizing error in a Kelly system.

The first useful script should make false confidence harder. It should reproduce a
benchmark, expose every assumption and cost, and fail loudly on look-ahead,
unavailable data, weight violations, insolvency, and unrecorded experiments before
it searches for an optimal portfolio.

Two existing files are inconsistent with this page and should be resolved rather
than extended. `src/utils/calculateOptimizedPortfolio.ts` is named for Kelly but
maximises a mean-variance utility, which silently answers open question 2 in a way
this page does not support. `scripts/seed-database.ts` emits an unseeded random
walk, so it cannot regenerate any fixture above; seeding it and exposing
\(\mu\), \(\sigma\), and correlation as explicit inputs would make it useful for
exactly that.

Separately, the shipped UI copy claims real-time data, optimality, and professional
validation. Nothing on this page supports those claims and the rebalancing findings
contradict any "rebalancing bonus" language. Per the root `AGENTS.md`, correcting
that copy is a product decision to raise, not an edit to make unasked.

## How this page was researched, and what that does not cover

Claims were gathered by fan-out web search, extracted from primary sources with
supporting quotes, then put through three-vote adversarial verification in which a
claim dies on two refutations. Verifiers were instructed to fetch the primary
source before searching, to re-derive any algebra and recompute any number from its
stated inputs, and to treat a claim whose arithmetic fails to reproduce as refuted
even when the source does state it. That check earned its place: it caught a
"157 years" figure that recomputes to about 19, a formula whose printed values were
twice what the equation yields, and an exhibit that is internally inconsistent in a
provably symmetric setup.

Four limits bound how much this page should be trusted, as of 2026-08-11.

Verification killed framing more often than arithmetic. Of seven claims rejected,
six reproduced their numbers exactly and failed on dropped scope — a hurdle
omitted, a weight fitted ex post, a benchmark that was not the stated one. The
numbers on this page are reliable; the generalisations they are attached to are
where error concentrates, which is why hurdles, weighting schemes, and sample
periods are stated inline throughout rather than in footnotes.

Counter-source search was not completed. Verifiers exhausted their web-search
budget before the adversarial literature step in both rounds, so several empirical
findings rest on primary-source reading and independent re-derivation with no
survey of the disputing literature. The mathematical identities are unaffected —
they are self-verifying — but the empirical findings are weaker than their vote
counts suggest. The unread [Jensen, Kelly, and Pedersen 2023](https://doi.org/10.1111/jofi.13249)
is the specific casualty.

Coverage is uneven. Leverage, rebalancing, tail protection, factor replication and
manager alpha were verified. The gaps below are not marginal thinness — each is a
topic named in the original research brief that no search angle across three
rounds ever surfaced, or a claim a verifier flagged directly and that was never
followed up. Each is a plausible place where a different search would change a
conclusion this page currently states, not just add detail to one.

- **Lifecycle leverage.** Ayres and Nalebuff's prescription — leverage early-career
  portfolios roughly 2x, deleverage with age — is a specific, testable claim that
  belongs directly against this page's leverage-boundary math. It never surfaced.
  Start with the book and its academic critiques (Blanchett's response is the
  usual starting point).
- **Capacity-constrained alpha.** Managed futures/trend, statistical arbitrage,
  catastrophe reinsurance, merger arbitrage, and private credit are where
  practitioners most often claim genuine, non-decaying alpha exists — precisely
  because size limits competition. Named as its own sub-question in the brief;
  never touched. It needs the same adversarial treatment as everything else here,
  not an exemption because the claim sounds structural.
- **Risk parity.** Named explicitly, zero coverage. Its construction (equal risk
  contribution, not equal dollar weight), its dependence on leverage to reach a
  target return, and the specific mechanism of its 2022 failure (simultaneous
  stock–bond selloff, not a normal equity crash) all need verification before it
  is treated as a candidate diversifier.
- **Portfolio construction beyond 1/N.** DeMiguel–Garlappi–Uppal was this page's
  only result on portfolio-theory failure modes, and verification reframed it as
  non-universal — so the sub-question is effectively unanswered. Shrinkage
  estimators (Ledoit–Wolf), Black–Litterman, and hierarchical risk parity are the
  standard responses to the estimation-error problem 1/N's dominance illustrates,
  and none has been checked.
- **Hedge fund index biases.** Survivorship, backfill, and self-reporting bias in
  commonly cited hedge fund indices. One data point (Eurekahedge Tail Risk Index
  survivorship) surfaced in round 2 and was explicitly dropped before round 3's
  verification pass; the general magnitude of these biases is still unestablished
  here.
- **Time-series momentum's own evidence base.** Moskowitz–Ooi–Pedersen and its
  replication critiques were named in the brief and never searched. This matters
  specifically because trend-following is the only positive result that survived
  this page's tail-risk section — its foundation hasn't been checked with the
  rigor applied to everything it is compared against.
- **The ergodicity-economics critique.** Peters' framework is now load-bearing for
  this page's leverage-boundary math, but the critique of that broader research
  program (Doctor, Wakker and Wang, and others) has only been cited in passing,
  never independently read or tested against the specific claims used here.
- **Jensen, Kelly, and Pedersen 2023** — see open question 6 above. It is the
  single item on this list most likely to overturn, rather than extend, a
  conclusion already stated on this page.

Sequence-of-returns risk, currency and home bias, and counterparty risk in levered
structures were also never surfaced, but with lower confidence that they would
change a conclusion rather than add a caveat to one; the claims about them
elsewhere on this page carry their original citations without a verification pass.

Nothing verified here is net of costs. Every replication rate, premium, Sharpe
ratio, and growth figure above is gross, and the haircut bites hardest on exactly
the highest-turnover candidates.
