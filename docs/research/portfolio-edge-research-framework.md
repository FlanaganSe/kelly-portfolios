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
backtested signals. It is a simple passive benchmark plus a few predeclared,
economically distinct factor *themes*, with each proposed sleeve measured
separately. Value, momentum, profitability and diversified time-series trend are
candidates under dispute, not approved edges. Volatility targeting is initially a
risk-control experiment, not alpha, and leverage remains disabled until unlevered
results survive hostile out-of-sample replication. Rebalancing is a
portfolio-maintenance policy, not assumed alpha. Tail options are insurance whose
crisis payoff must justify their normal-time drag. Active funds and
betting-against-beta begin with a more sceptical prior because net persistence and
implementability evidence are weak.

Adversarial verification narrows the claims substantially. The rebalancing bonus
is an accounting identity against a benchmark nobody can hold; a particular
two-period rebalance is short relative-performance continuation, but that is not a
theorem about every policy. Protective puts look much less attractive when matched
to reduced equity, though their value depends on an ex-ante objective and exact
contract. Factor replication varies sharply by construction and statistical model,
and replication is not implementability. Historical active-fund gross alpha is
near zero in a central study and net alpha negative by roughly the fee, while
manager skill may be captured through fees and scale rather than by investors.

A second verification round sharpened four of these and left each *weaker* than
before. The apparent resolution of the factor-replication dispute is an artefact of
changing the estimand: the celebrated 82.4% figure owes +21.1pp to switching from
raw returns to CAPM alpha and exactly **zero** to the Bayesian machinery that gives
the paper its name. Risk parity's entire measured advantage lives inside its
financing assumption, collapsing from 210 bp/yr to an insignificant 29 bp/yr on the
same 85 years of data once borrowing is priced realistically. Time-series momentum —
previously the one survivor of the crisis-protection review — fails its own
bootstrap hurdle, and stripping its volatility scaling collapses the statistic below
even the conventional threshold, leaving a profitable strategy without the
predictability that was supposed to justify it. And of five capacity-constrained
"alpha" strategies, four are refuted outright, with only catastrophe risk left
unproven rather than disproven.

**No positive, independently replicated, net-of-cost edge was established.** A
low-cost diversified-beta baseline is therefore the control every proposed edge
must beat, not a claim that the final answer has already been found.

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

Adding an exposure-proportional cost \(c\) to the *entire* risky exposure, expected
log growth is approximately

\[
g(L) \approx r + L(\mu-r-c) - \tfrac12L^2\sigma^2.
\]

This is a stylised identity, not an executable financing model. With lending rate
\(r_l\), borrowing spread \(s_b\), and instrument costs \(C(L)\), a more realistic
one-asset approximation is kinked at one-times exposure:

\[
g(L) \approx r_l+L(\mu-r_l)-s_b(L-1)^+-C(L)-\tfrac12L^2\sigma^2.
\]

The optimum and the boundaries below do not survive unchanged when financing is
kinked, costs are nonlinear, or margin forces liquidation. In the stylised smooth
model, leverage improves modeled geometric growth only below the true optimum;
beyond it, leverage reduces growth. Two boundaries follow from the same quadratic
and are true by construction: growth falls back to exactly the risk-free rate at
\(2L^*\), and turns negative above
\(L^*+\sqrt{(L^*)^2+2r/\sigma^2}\)
([Peters 2011](https://arxiv.org/pdf/0902.2965)). For an investor whose objective
is this model's asymptotic log-growth rate, the cash-relative model boundary is
\(2L^*\), not the zero-growth root: above \(2L^*\) the model loses to holding
cash. It is not a universal leverage ceiling, a ruin boundary, or a margin limit.
Continuous GBM never reaches zero in finite time; real ruin comes from jumps,
discrete trading, liabilities, margin, and forced liquidation that this equation
omits.

The cleanest form to hold in code is the vertex form, which was re-derived here
from Itô's lemma rather than copied from the paper:

\[
g(L) = r + \tfrac12\sigma^2\left[(L^*)^2-(L-L^*)^2\right],
\qquad g(L^*) = r + \frac{(\mu-r)^2}{2\sigma^2}.
\]

Growth is a downward parabola symmetric about \(L^*\), so \(g(0)=g(2L^*)=r\)
follows from symmetry alone and needs no separate derivation, and the zero-growth
root is the positive solution of \(L^2-2L^*L-2r/\sigma^2=0\). Attribute this
algebra to Itô, Kelly, Latané and Merton rather than to ergodicity economics.
Peters describes his own contribution as framing the already-known result "as a
question of ergodicity"
([Peters 2019](https://www.nature.com/articles/s41567-019-0732-0), p. 1218), and
the surrounding framework is disputed by economists
([Doctor, Wakker and Wang 2020](https://www.nature.com/articles/s41567-020-01106-x))
in a way the algebra is not. Nothing in that dispute changes a leverage number:
because \(E[\ln W_T]=\ln W_0+T\,g(L)\), maximising time-average growth and
maximising expected log utility are the same optimisation, and both are the
\(\gamma=1\) case of Merton's \(L^*=(\mu-r)/(\gamma\sigma^2)\). Cite Peters for
the leverage-boundary framing and for his overestimate caveat; do not let the
repository depend on the claim that this supersedes utility theory.

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
the true excess drift is half the estimate, betting \(0.5\hat{f}^*\) attains
maximum growth while \(\hat{f}^*\) gives zero excess log growth over cash and
\(1.5\hat{f}^*\) gives negative excess log growth
(Thorp 2006, "The Kelly Criterion in Blackjack, Sports Betting and the Stock
Market", sec. 7.3). Real portfolios also have jumps, changing margin, unequal
borrowing and lending rates, taxes, and forced liquidations, none of which the
diffusion expression captures.
For discrete multiasset returns the actual problem is
\(\max_w E[\log(1+w^\top R_{net})]\), subject to
\(1+w^\top R_{net}>0\) almost surely plus leverage, position, and margin constraints
and an integrability condition that makes expected log wealth finite.
A Gaussian model of simple returns has unbounded losses, so it makes expected log
wealth undefined for every nonzero unconstrained exposure. A script must instead
use bounded scenarios or an explicit jump-support model, or remain consistently in
continuous-time diffusion mathematics. Under the idealized multiasset diffusion,
\(w^*=\Sigma^{-1}(\mu-r\mathbf1)\); this makes mean error especially dangerous
because the inverse covariance amplifies it.

Kelly is optimal for log utility, not for every investor, horizon, liability, or
drawdown preference ([Samuelson 1979](https://doi.org/10.1016/0378-4266%2879%2990023-2));
\(1/\gamma\) times Kelly only in the constant-opportunity continuous-time Merton
diffusion ([Merton 1969](https://doi.org/10.2307/1926560)). That scaling is not
generally exact with discrete returns, jumps, costs, constraints, or changing
opportunities; solve the declared utility directly in those cases.

The normative choice remains open. Peters and Gell-Mann map logarithms to
multiplicative wealth dynamics and advocate time-average growth
([Peters and Gell-Mann 2016](https://doi.org/10.1063/1.4940236)), while Samuelson
shows that geometric-mean maximization is not a universal terminal-wealth criterion
([Samuelson 1971](https://pmc.ncbi.nlm.nih.gov/articles/PMC389451/)). At finite
horizons, growth-optimal leverage need not maximize the probability of beating cash
or the market, expected consumption, or drawdown utility. The repository may choose
log growth, CRRA utility, or liability/consumption shortfall, but physics does not
uniquely choose one.

Parameter uncertainty is large enough to swamp a plug-in Kelly estimate. If
volatility were known and annual excess returns were independent with
\(\sigma=18\%\), then after 20 years
\(SE(\hat L^*)=1/(\sigma\sqrt{T})\approx1.24\) exposure units, before accounting
for volatility error, nonstationarity, tails, costs, or dependence. This is a
diagnostic calculation, not a confidence interval for real markets; it explains
why the app must show a sensitivity surface and feasibility cap rather than one
number labelled "optimal leverage."

Lifecycle leverage is a proposal to redistribute market exposure across time, not
to create alpha. Young investors usually have little financial capital, so an
unlevered equity allocation concentrates most lifetime dollar exposure late in
life. Ayres and Nalebuff report that an initially leveraged glidepath matched the
mean accumulation of constant 75% equity with 21% lower standard deviation in a US
historical simulation beginning in 1871
([Ayres and Nalebuff 2010](https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID1702364_code462513.pdf?abstractid=1687272&mirid=1)).
That result is conditional on its sample, glidepath, contributions and financing;
an earlier version reported much larger benefits, illustrating specification
sensitivity. It does not imply that a leveraged ETF implements the theoretical
trade or that leverage is suitable without stable contributions and labor income.

Three points decide how much weight this can carry. First, the mechanism must not
be confused with the refuted claim that stocks are safer over long horizons: the
authors assume returns are i.i.d., so no mean reversion does any work, and the claim
is that the *base* against which exposure is measured is mismeasured — present value
of lifetime savings rather than current savings. Second, the 2:1 figure is not an
optimum but Federal Reserve Regulation T's cap; their own target rule
\(\lambda=(\mu-r)/(\sigma^2\gamma)\) contains no age term at all, and their
robustness table inverts the prescription in favour of a conventional target-date
fund once volatility is raised to 29.29%. Third, the one independent out-of-sample
test finds the risk reduction real but "relatively insignificant", and the strategy
inferior to conventional and dynamic lifecycle glidepaths (Wang, Li, and Liu 2017,
*Financial Planning Research Journal* 3(2), 12–30).

Reconciling this with growth-optimal sizing exposes the error most likely to matter
here. At \(\mu-r=5\%,\ \sigma=18\%\), full Kelly is \(L^*=1.5432\), so 2:1 on the
tradable account exceeds it by 29.6%, sits past the growth peak, and buys the same
log growth as \(L=1.086\) with double the variance. But the prescription is not sized
on liquid wealth: \(2S/(S+W)\) stays below 1.5432 unless \(S>3.38W\), so for a
25-year-old with \(W/S\approx10\) effective exposure is about 0.18 of total wealth —
far *below* Kelly, not above it. An age-dependent leverage schedule therefore follows
from growth-optimal reasoning if and only if human capital is a riskless bond that
cannot be sold. That premise is exactly what cointegration between labour income and
dividends breaks: it makes human capital stock-like when young and bond-like when
old, implying a hump-shaped path and, under plausible calibrations, short equity
positions for the young
([Benzoni, Collin-Dufresne, and Goldstein 2007](https://doi.org/10.1111/j.1540-6261.2007.01271.x)).
Note also that Samuelson personally rejected the prescription on ruin grounds,
though he wrote to the authors that he had read only the abstract; and that Shiller
is not available as a citation against leverage, since he found the standard
glidepath *insufficiently* aggressive.

The operational trap is the \(\gamma\): Merton's \(\lambda\) is the mean-variance
solution divided by risk aversion, so treating a mean-variance output as Kelly
overstates leverage by a factor of \(\gamma\) — a 4× error for a CRRA-4 investor.
This is not hypothetical here; see the consequence section on
`src/utils/calculateOptimizedPortfolio.ts`.

Human capital can reverse the age-only prescription. Positive wage/stock
correlation can push an employed investor's equity allocation below a retiree's,
and greater idiosyncratic income risk lowers equity demand
([Viceira 2001](https://www.nber.org/system/files/working_papers/w7409/w7409.pdf)).
The app must therefore model conservative after-tax human-capital value, its market
beta, job-loss risk, labor flexibility, liabilities and contributions. A lifecycle
leverage test must combine an equity crash, job loss, stopped contributions,
financing-spread jump and margin tightening. Its comparator is the same lifetime
market exposure without leverage, and its output must include forced-liquidation
risk.

Sequence risk is a cash-flow interaction, not a separate premium. Without external
cash flows, permuting returns leaves terminal wealth unchanged; contributions and
withdrawals break that identity. A decumulation engine must simulate the full
inflation-adjusted liability path, longevity, pensions and flexible spending and
report consumption shortfall and funded ratio, not only a historical success rate.
Rising-equity retirement glidepaths can reduce failure severity in adverse
sequences while sacrificing average terminal wealth, but the preferred path is
model-dependent ([Pfau and Kitces 2014](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2324930)).

Taxes can dominate a small forecast edge and require joint asset-allocation and
asset-location optimization. The familiar US rule placing taxable bonds in
tax-deferred accounts follows from their higher current tax burden
([Dammon, Spatt, and Zhang 2004](https://doi.org/10.1111/j.1540-6261.2004.00655.x)),
but is not universal: actual-return studies find cases where tax-inefficient equity
funds belong there instead. Turnover, distributions, municipal yields, loss
harvesting, basis, withdrawal tax, account type and capacity all matter
([Poterba, Shoven, and Sialm 2001](https://www.nber.org/papers/w7991)). Tax law must
be a dated jurisdiction-specific input, never a hardcoded financial truth.

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

**A two-period rebalance is a short straddle on relative performance.** Under the
source's two-asset, two-period setup, the exact identity is
\(R_{\text{REBAL}}-R_{\text{HOLD}}=-w_Sw_B\kappa_1\kappa_2\),
where \(\kappa_t\) is the difference in simple returns between the two assets
([Rattray et al. 2020](https://people.duke.edu/~charvey/Research/Published_Papers/P145_Strategic_rebalancing.pdf)). Rebalancing
therefore *loses* when relative performance trends and gains only on reversal, and
the loss concentrates in crises: the monthly-rebalanced 60/40 had a maximum
drawdown 5 percentage points worse than buy-and-hold in 2007–2009.

**There is no unconditional expected profit in one important model.** Under the
source's Markov-price assumptions and comparison trade, the long-rebalanced /
short-buy-and-hold position has exactly zero expected profit
([Chambers and Zdanowicz 2014](https://www.hec.ca/finance/Fichier/Chambers2014.pdf)).
This does not prove that every calendar, threshold, or multiperiod policy has zero
conditional profit or utility value. It does prove that a positive variance
decomposition is insufficient evidence of alpha.

One live objection to this repository's premise sat here and is now **settled** in
the [expected-edge decomposition](expected-edge-decomposition.md), which supersedes
this paragraph's framing.

Chambers and Zdanowicz's zero-expected-profit result concerns expected terminal
*wealth*, and it is correct — it even generalises, since with unequal means
buy-and-hold is strictly ahead on \(E[W_T]\). Two corrections to what this page
previously said. Their 1.874% and 1.867% are **not** expected log wealth; they are
\(E[W^{1/T}]-1\), the expected annualised rate. The corresponding expected log
growth rates are 1.2346% and 1.2201%. And their "arbitrary nonlinear transformation"
sentence is aimed at that annualised rate, not at log wealth, which they never
analyse — so it is not the direct attack on log utility this page reported.

Against \(E[\log W]\) the dismissal fails on its own terms, because
\((1/T)\log W_T\) is a pathwise property containing no preferences, and Breiman's
almost-sure dominance applies. Their own Exhibit 5 also stops where the effect is
smallest: extended, the rebalanced portfolio's expected log growth stays constant
while buy-and-hold's decays to zero, so their 12-period 12 bp gap grows without
bound. What a log investor actually gains is a mean-preserving contraction —
identical \(E[V_T]\), variance lower by 29%, median higher.

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

Diversified time-series momentum is a leading but disputed candidate for a dynamic
crisis sleeve. Evidence spans many futures markets
([Moskowitz, Ooi, and Pedersen 2012](https://doi.org/10.1016/j.jfineco.2011.11.003))
and a reconstructed history back to 1880
([Hurst, Ooi, and Pedersen 2017](https://ssrn.com/abstract=2993026)); the latter is
a vendor-authored historical reconstruction, not independent live evidence.
Huang et al. reuse the original 55-asset data and find weak asset-level and
out-of-sample predictability: 47 of 55 individual statistics are below 1.65, mean
in-sample \(R^2\) is 0.39%, and mean out-of-sample \(R^2\) is **negative** at
−0.67%, negative for 45 of 55 assets. Their test is a bootstrap of the pooled
\(t\)-statistic — parametric wild and nonparametric pairs — not a Wald test. The
decisive number is that the original pooled \(t=4.34\) sits **below** its own
bootstrap 5% critical values of 12.53 (wild) and 4.83 (pairs), and still fails when
restricted to the original 1985–2009 window. They cannot distinguish the portfolio
return from a static history rule that buys assets with positive historical sample
means and requires no return predictability at all: the gap is 0.14%/month at
\(p=0.19\), and −0.02% against Asness–Moskowitz–Pedersen factors at \(p=0.84\)
([Huang et al. 2020](https://doi.org/10.1016/j.jfineco.2019.08.004)).

Two further results explain where the performance actually comes from. Volatility
scaling is not an implementation detail but the effect itself: removing it collapses
the pooled statistic from 4.34 to 1.68, below even the conventional hurdle
([Kim, Tse, and Wald 2016](https://doi.org/10.1016/j.finmar.2016.05.003), *Journal of
Financial Markets* 30, 103–124). And the strategy carries a large embedded net-long
market position — on average \$3.28 long against \$1.73 short, a \$5 active position
against cross-sectional momentum's \$2 — so the original comparison set a 2.5×-levered
factor against an unlevered one. Adding a time-varying market position to a
cross-sectional strategy reproduces the time-series result
([Goyal and Jegadeesh 2018](https://doi.org/10.1093/rfs/hhy131), *Review of Financial
Studies* 31(5), 1784–1824).

The defensible reading is that the strategy is *profitable* while returns are not
*predictable* — these are different claims, and only the first survives. What is
being harvested is cross-sectional mean-return dispersion plus a time-varying market
tilt, not an asset's own past forecasting its future. This disputes the forecasting
mechanism without proving the historical crisis payoff is useless. Trend is also not
an instant hedge: slow signals miss gaps and sharp reversals cause whipsaw, early
data are reconstructed, and authors have industry affiliations. No rebuttal to Huang
et al. was found; the usual defence predates it and does not address the bootstrap
argument.

Inverse-volatility exposure has improved factor Sharpe ratios in historical tests
because volatility persistence was not matched by proportional changes in expected
return ([Moreira and Muir 2017](https://doi.org/10.1111/jofi.12513)). It reacts
after volatility rises, can miss jumps, and may re-enter too slowly after a sharp
rebound. It must be compared with the same volatility scaler applied to the passive
benchmark, not only with an unscaled benchmark. Later evidence finds turnover and
costs erase most improvements outside the market factor, and a broader factor test
finds no statistically significant surviving Sharpe improvement after estimation
error and costs ([Barroso and Detzel 2021](https://doi.org/10.1016/j.jfineco.2021.02.009),
[DeMiguel et al. 2024](https://doi.org/10.1111/jofi.13395)).

Price protection and funding liquidity are different. In March 2020, even the US
Treasury market suffered impaired depth and forced sales: Federal Reserve staff
estimate hedge-fund Treasury holdings fell $141 billion and valuation-adjusted net
sales were $173 billion
([Federal Reserve 2021](https://www.federalreserve.gov/econres/notes/feds-notes/sizing-hedge-funds-treasury-market-activities-and-holdings-20211006.html)).
The FSB attributes the turmoil to interacting dealer constraints, leveraged
nonbank sales, redemptions, and margin, and judges that central-bank intervention
prevented worse conditions
([FSB 2020](https://www.fsb.org/2020/11/holistic-review-of-the-march-market-turmoil/)).
A diversifier that rises on a monthly chart may still fail as same-day collateral.

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

The apparent contradiction with
[Jensen, Kelly, and Pedersen 2023](https://doi.org/10.1111/jofi.13249) is now
resolved methodologically, not empirically. They study 153 factors in 93 countries
using country terciles, non-micro breakpoints, capped value weights, publication
lags, and volatility-scaled long-short returns. The gap decomposes additively, and the decomposition is the finding:

| Step | Rate | Δ |
| --- | --- | --- |
| Hou–Xue–Zhang baseline | 35.0% | — |
| US, raw returns, JKP construction | 55.6% | +20.6pp |
| Drop 34 factors the *original* papers found insignificant | 61.3% | +5.7pp |
| Raw return → **CAPM alpha** | 82.4% | **+21.1pp** |
| Hierarchical empirical-Bayes multiple testing | 82.4% | **+0.0pp** |
| Global, 93 countries | 82.4% | +0.0pp |

The marquee Bayesian machinery moves the headline by nothing; JKP concede the
Bayesian rate is "coincidentally, the same as the OLS replication rate", and the
global evidence adds nothing either — conditioning the US posterior on global data
in fact lowers it to 81.5%. The single largest driver is the switch of estimand from
raw return to CAPM alpha, justified with a betting-against-beta example whose raw
return is near zero by construction. The headline is 98/119, not 98/153: the
denominator silently shifts once 34 factors are dropped. Hou–Xue–Zhang and
Jensen–Kelly–Pedersen therefore answer different questions with different hurdles,
estimands, and models.

JKP do overturn one substantive empirical claim rather than merely reframing it.
Hou–Xue–Zhang's stated mechanism is microcaps — "anomalies in microcaps are more
apparent than real". JKP report replication rates by size of mega 77.3%, large
79.8%, small 85.7%, micro 85.7%, and nano 68.1%, against 82.4% overall, so the
result is not concentrated in small stocks. Their capped value weighting does shift
weight down-cap relative to pure value weighting, which is the choice Hou–Xue–Zhang
argue against, and the internal appendix that would decompose the +20.6pp
construction step is not publicly reachable. Neither is
a net-return test: the latter has no transaction-cost, borrow, financing, tax, or
fund-fee model and tests mostly academic zero-investment long-short portfolios.
The defensible conclusion is that economic themes deserve a positive but heavily
shrunk prior; no replication percentage establishes an investable edge.

This repository has since measured HML, UMD, RMW and CMA over frozen
pre- and post-publication eras. None of the four was promoted; see
[factor persistence and decay](factor-persistence.md) for the era boundaries, the
power calculation that makes three of them `unresolved` rather than negative, and
the one that was `rejected`.

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

Costs must alter the trading rule, not appear as a constant haircut after the
backtest. Novy-Marx and Velikov's value-weighted decile long/short results,
1963–2012, give the haircut by turnover tier
([Novy-Marx and Velikov 2016](https://www.nber.org/papers/w20721)):

| Tier | One-sided monthly turnover | Gross | Net | Haircut | Survive net \(t>2\) |
| --- | --- | --- | --- | --- | --- |
| Low | 1.2–7.2% | 42.8 bp/mo | 35.4 | **17%** | 4 of 8 |
| Mid | 14–35% | 89.8 | 42.8 | **52%** | 5 of 9 |
| High | 90–94% | 99.7 | −44.0 | **144%** | 0 of 6 |

Nine of 23 anomalies retain net \(t>2\); four of the six high-turnover strategies
have strictly negative net returns. Dispersion within a tier exceeds the gap between
the low and mid tiers, so turnover is the better continuous predictor. Fitting cost
to turnover across the tier means gives a usable first-order rule,
\(\text{cost bp/month}\approx k\times\text{one-sided turnover }\%\), with \(k\)
between 1.57 and 1.71 across all three tiers and a conservative floor of 1.0. A
buy/hold spread or no-trade band is their most effective simple mitigation, cutting
turnover 41% and costs 42%.

Two conventions have to be pinned down before that rule computes anything, because
both are silent factor-of-two or factor-of-ten traps. **One-sided turnover means
\(\tfrac12\sum_i|\Delta w_i|\)**, the Novy-Marx–Velikov convention; reading it as
\(\sum_i|\Delta w_i|\) doubles every cost figure. And \(k\) is **not independently
re-derivable from the published tier ranges**: the range midpoints give 1.762 (low),
1.918 (mid), 1.562 (high), so only the high tier reproduces. The paper fits to tier
*means*, which it does not print. Running the derivation backwards is the available
check — each published \(k\) implies a mean one-sided turnover of 4.35%, 27.5% and
91.5% respectively, and each of those does fall inside its published range. Treat the
low and mid \(k\) as reported rather than verified.

The apparent conflict with live institutional evidence is narrower than usually
reported. Frazzini, Israel, and Moskowitz measure a 21.33 bp mean quoted spread at
order arrival on \$1.7tn of executions and state it matches the academic estimates;
there is no dispute about the input. They pay roughly 10 bp of market impact instead
because they execute patiently over about 2.7 days with only 15% aggressive orders.
The gap is **execution style, not data**, and the genuine order-of-magnitude fight is
against *linear* impact models: at 10% of daily volume a linear model gives 223 bp
against their 32 bp, whereas Almgren's independent broker-data estimate — no industry
interest, published 13 years earlier — lands at 32–43 bp, siding with them on
functional form ([Almgren et al. 2005](https://www.cis.upenn.edu/~mkearns/finread/costestim.pdf)).
Impact follows a square-root-like law, \(\text{bp}\approx c\,\sqrt{|Q/V|}\) with
\(c\approx11\) for US stocks, though Almgren rejects the 1/2 exponent in favour of
3/5, so treat it as \(0.5\pm0.1\). **\(|Q/V|\) is in percent, not as a fraction**, and
the two readings differ by an order of magnitude: at 10% of daily volume the percent
convention gives \(11\sqrt{10}=34.8\) bp, which sits inside Almgren's 32–43 bp
bracket and beside the 32 bp figure above, while the fraction convention gives
\(11\sqrt{0.1}=3.5\) bp and is wrong. The bracket is the fixture that pins it.

Which regime applies here is decided by size, and the answer is counter-intuitive:
at retail scale trade/ADV is far below 0.1%, so the impact term vanishes and the
institutional advantage is irrelevant because there is no impact to avoid. What
binds is the spread — and Novy-Marx and Velikov explicitly describe their measure as
"the costs faced by a small liquidity demander" assuming market orders, which *is*
the retail case. The low-cost institutional evidence additionally depends on trading
large liquid names and does not transfer to the microcaps where much of the academic
premium lives. Report gross, net-optimistic (\(k=1.0\), patient limit orders, liquid
large caps) and net-pessimistic (\(k=1.7\), market orders, full universe) from one
turnover input, so the spread between columns *is* the visible model uncertainty;
default to net-pessimistic. Treat anything above 50% monthly one-sided turnover as
not retail-implementable regardless of gross Sharpe. Optimize net holdings and trades
under investor-specific capacity, borrow, fee, and tax assumptions; never choose
whichever published cost estimate preserves the result
([Frazzini, Israel, and Moskowitz](https://people.stern.nyu.edu/afrazzin/pdf/Trading%20Cost%20of%20Asset%20Pricing%20Anomalies%20-%20Frazzini%2C%20Israel%20and%20Moskowitz.pdf),
[Patton and Weller 2020](https://doi.org/10.1016/j.jfineco.2020.02.012)).

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
Manager skill can also be captured by the manager rather than the investor. Berk
and van Binsbergen estimate persistent dollar value added by funds, consistent
with skilled managers expanding until fees and scale diseconomies absorb their
advantage ([Berk and van Binsbergen 2015](https://doi.org/10.1016/j.jfineco.2015.05.002)).
That reconciles manager skill with little scalable investor net alpha; it is not a
fund-selection rule.

### Portfolio construction is an estimation problem

Mean–variance optimization is most fragile where this project most wants precision:
expected returns. Across seven datasets, none of 14 optimized models consistently
beat equal weight on Sharpe, certainty-equivalent return, and turnover; under one
US calibration the estimated samples required for dominance were about 3,000
months for 25 assets and 6,000 for 50
([DeMiguel, Garlappi, and Uppal 2009](https://doi.org/10.1093/rfs/hhm075)). This is
not a theorem that equal weight is optimal. It makes market weight, equal weight,
drifting buy-and-hold, constrained minimum variance, and regularized covariance
mandatory baselines.

Linear covariance shrinkage has the explicit form
\(\hat\Sigma_\delta=(1-\delta)S+\delta F\), with \(\delta\) learned inside each
training window ([Ledoit and Wolf 2004](https://ledoit.net/honey.pdf)). Risk parity
is likewise a construction, not an edge: it equalizes declared risk contributions
\(RC_i=w_i(\Sigma w)_i/\sqrt{w^\top\Sigma w}\), but still depends on covariance,
asset definitions, and often leverage. Hierarchical risk parity, Black–Litterman,
nonlinear shrinkage, and regime models are candidates only after frozen comparisons
against these simple baselines. No method earns the label “optimal” merely by
solving its own estimated objective.

The initial construction stack should use long-only constrained minimum variance
or explicit risk budgets, a shrunk covariance matrix, group and position caps, and
turnover/cost penalties. No-short constraints can improve realized performance by
acting as regularization even when the economic constraint is artificial
([Jagannathan and Ma 2003](https://doi.org/10.1111/1540-6261.00580)). Nonlinear
eigenvalue shrinkage is a credible challenger to linear shrinkage when the number
of assets is not small relative to observations, but better covariance loss does
not guarantee better net portfolio utility
([Ledoit and Wolf 2017](https://ssrn.com/abstract=2383361)).

Equal risk contribution equalizes modeled risk contributions, not opportunities,
and may require leverage after loading heavily on low-volatility assets
([Maillard, Roncalli, and Teiletche 2010](https://ssrn.com/abstract=1271972)).
Three properties of ERC are proved rather than empirical and belong in tests: the
solution is unique for positive-definite \(\Sigma\); it reduces *exactly* to
inverse-volatility weighting for two assets — independent of correlation — and for
\(n>2\) only under constant correlation; and it is ordered
\(\sigma_{\text{MV}}\le\sigma_{\text{ERC}}\le\sigma_{1/n}\). The load-bearing
optimality condition is narrow and stated by the authors themselves: ERC is the
maximum-Sharpe portfolio only if correlations are equal **and** all assets share the
same Sharpe ratio. Risk parity is therefore an implicit expected-return forecast,
not a return-agnostic construction, and a tool should surface that implied
assumption rather than present the output as optimal.

Its empirical case rests almost entirely on an assumption about financing. The
strongest pro-risk-parity study reports a levered Sharpe of 0.53 against 0.25 for
the market over 1926–2010, and states that it applies no adjustment for the cost of
leverage; its authors' firm sells risk parity funds and the journal appended an
editor's note saying so
([Asness, Frazzini, and Pedersen 2012](https://www.aqr.com/-/media/AQR/Documents/Insights/Journal-Article/Leverage-Aversion-and-Risk-Parity.pdf)).
On the same CRSP data, substituting a realistic borrowing rate for the Treasury-bill
rate collapses the advantage over 60/40 from 210 bp/yr (\(p=0.03\)) to 29 bp/yr
(\(p=0.40\)), and adding trading costs reverses it; levered risk parity also
underperformed both 60/40 and the market throughout 1946–1982
([Anderson, Bianchi, and Goldberg 2012](https://eml.berkeley.edu/~anderson/risk%20parity111111.pdf)).
Eighty-five years of data therefore yield no significant result once financing is
priced. The arithmetic of why is direct: reaching 16% volatility from a 6.17%
-volatility parity portfolio needs 2.59× leverage, so every 100 bp of borrowing
spread costs about 159 bp per year. Any levered risk-parity figure must take the
financing spread as a required input rather than defaulting it to zero. The 2022
drawdown is the matching out-of-sample evidence and failed in the predicted way — a
simultaneous stock and bond selloff rather than an equity crash, with the RPAR Risk
Parity ETF returning −22.81% on net asset value against roughly −18% for the S&P 500.
Black–Litterman is a governance and shrinkage interface for genuine forecasts, not
a signal: its market prior, views and confidence must all have provenance
([Black and Litterman 1992](https://doi.org/10.2469/faj.v48.n5.28)). Robust
optimization is likewise only as sound as its externally calibrated uncertainty
set ([Goldfarb and Iyengar 2003](https://doi.org/10.1287/moor.28.1.1.14260)). HRP,
resampling and regime switching remain challenger models; clustering and latent
states add unstable choices, and smoothed regime probabilities introduce
look-ahead. Use regimes first as stress scenarios, and filtered probabilities only
in any later dynamic allocation test.

The frozen construction tournament should therefore compare the same point-in-time
returns, constraints, execution lag, costs, and rebalance dates across: drifting
buy-and-hold, the declared market or strategic benchmark, equal weight, inverse
volatility, sample-covariance constrained minimum variance, linear-shrinkage
minimum variance, and equal risk contribution using that same shrunk covariance.
Nonlinear shrinkage is the first advanced challenger; HRP and resampling follow only
as fully specified challengers. Black–Litterman belongs in a separate forecast
experiment with a no-view prior and the identical forecast passed to regularized
mean–variance optimization. Regime models must use recursively estimated parameters
and filtered probabilities available on the decision date, never full-sample
smoothed labels.

Choose the tournament's primary criterion before running it—net
certainty-equivalent return for a declared utility, or net realized volatility for
an explicitly minimum-risk product. All window, shrinkage, clustering, uncertainty,
turnover, and regime choices occur inside chronological nested training folds. An
advanced method replaces linear-shrinkage constrained minimum variance only if its
net improvement clears a predeclared economic threshold or uncertainty interval,
appears across multiple outer eras rather than one crisis, survives neighboring
windows and stressed costs without retuning, and does not come from hidden leverage
or relaxed constraints. Otherwise complexity has not earned promotion.

### Capacity-constrained and alternative returns

Most alternative “alpha” is compensation for scarce liquidity, insurance, access,
complexity or leverage. Limited capacity can slow arbitrage, but it also prevents a
historical return from scaling; it is not evidence that the return is mispricing.

- Managed-futures trend is the strongest liquid alternative-diversifier candidate,
  but its slow signals miss gaps and whipsaw on reversals, and investors have not
  historically captured its gross edge. Over 1994–2012 CTA excess returns net of fees
  were insignificantly different from zero while gross excess returns were 6.1%, with
  no alpha relative to public-domain futures rules; fee income runs about 4% of assets
  ([Bhardwaj, Gorton, and Rouwenhorst 2014](https://doi.org/10.1093/rfs/hhu040)). On
  the same universe, survivorship and backfill move measured returns from 12.6%
  (Sharpe 0.73) to 4.9% (Sharpe 0.09) — a 7.7pp distortion that is larger than the
  strategy's entire gross premium. Use transparent futures rules and treat the long
  history as a replication target, not a forecast.
- Merger arbitrage resembles selling uncovered index puts: ordinary beta is low,
  while deal breaks and downside beta cluster in market and funding stress. The
  piecewise regression makes this concrete — beta is 0.0167 and insignificant in
  normal markets but 0.4920 when the market falls more than 4% below the risk-free
  rate, and the 10.3% excess return computed ignoring transaction costs falls to
  about 4% once costs and practical limits are imposed
  ([Mitchell and Pulvino 2001](https://andreisimonov.com/N4106/pdf/MitchellPulvinoJFDec2001.pdf)).
  Capacity did not protect it: spreads compressed by more than 400 bp after 2002 and
  merger-arbitrage fund alpha fell about 41 bp/month
  ([Jetley and Ji 2010](https://doi.org/10.2469/faj.v66.n2.6)).
- Catastrophe bonds transfer physical-event tail risk. Their low financial-market
  correlation is economically distinct, but principal loss, model, trigger basis,
  climate, peril and vintage concentration replace financial tail risk; this is
  insurance beta, not alpha
  ([IMF 2006](https://www.elibrary.imf.org/view/journals/001/2006/199/article-A001-en.xml),
  [BIS 2024](https://www.bis.org/fsi/publ/insights62.pdf)).
- Private credit's reported premium reflects credit, leverage, origination,
  illiquidity and sometimes skill; model marks suppress observed volatility. The
  Federal Reserve reports historical direct-lending returns roughly 2–4 percentage
  points above syndicated leveraged loans while documenting weak price discovery,
  highly leveraged borrowers and deteriorating coverage
  ([Federal Reserve 2024](https://www.federalreserve.gov/econres/notes/feds-notes/private-credit-characteristics-and-risks-20240223.html)).
- Short volatility earns an insurance premium for jump and disaster exposure and
  is a return sleeve, never crisis protection. Statistical arbitrage is a research
  program whose borrow, latency, turnover, impact and decay must be demonstrated
  live, not an assumed allocation. Its decay is directly measured rather than
  inferred: the standard contrarian strategy's average daily return fell almost
  monotonically from 1.38% in 1995 to 0.13% in 2007, so that roughly 9:1 leverage
  was needed by 2007 to match 1998 returns, and the August 2007 unwind produced a
  cumulative three-day loss of 6.85% — twelve daily standard deviations — followed
  by a 5.92% rebound, leaving the week nearly flat and marking it as a crowded
  liquidity event rather than a signal failure
  ([Khandani and Lo 2007](http://web.mit.edu/Alo/www/Papers/august07.pdf)).

Trend and catastrophe risk may diversify different crises. Merger arbitrage,
private credit and short volatility can all fail together in a funding/equity
shock and must not be counted as three independent edges. Capacity inputs belong
in the contract: futures volume/open interest, deal notional, peril concentration,
fund gates/lockups, equity participation and borrow limits.

Hedge-fund databases are unsuitable optimizer inputs without a point-in-time
reconstruction. Liang's comparison found survivorship bias of 0.60% per year in
HFR and 2.24% in TASS, showing that vendor construction changes the answer
([Liang 2000](https://papers.ssrn.com/sol3/Delivery.cfm/000219403.pdf?abstractid=213012)).
Fung and Hsieh estimated a 343-day average backfill period and roughly 1.4% per
year return bias for hedge funds in an older TASS sample
([Fung and Hsieh 2000](https://doi.org/10.1017/S0022109000000421)); later work
warns that dropping a fixed number of initial months does not solve vendor
migration and database-entry artifacts
([Fung and Hsieh 2009](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1414464)).
These historical estimates are sensitivities, not additive corrections or stable
constants.

Voluntary reporting can select both winners and losers, so even the direction of a
generic self-selection adjustment is not identified. Funds found through registered
funds of funds but absent from commercial databases had insignificant measured
alpha in one study, while reporting funds had 72–120 bps per quarter depending on
the model; delisted funds with later observations underperformed continuing
reporters by 184 bps per quarter
([Aiken, Clifford, and Ellis 2013](https://doi.org/10.1093/rfs/hhs057)). Yet a
study of mega firms found reporting and nonreporting firms similar after accounting
for credit exposure
([Edelman, Fung, and Hsieh 2013](https://doi.org/10.1016/j.jfineco.2013.04.003)).
"Dead" also does not mean liquidated: a fund may stop reporting because it closed
to capital, merged, migrated vendors, or chose silence. The data model must retain
the last report and exit reason rather than impute either zero loss or no loss.

Illiquid or managed marks create a second failure that a mean-return haircut cannot
repair. Getmansky, Lo, and Makarov model reported returns as moving averages of
latent economic returns. In their 908-fund TASS sample, mean annual Sharpe fell
from 1.32 naively to 1.19 after their smoothing adjustment, with category-level
overstatement around 16–20% for several illiquid strategies
([Getmansky, Lo, and Makarov 2004](https://web.mit.edu/Alo/www/Papers/JFE2004Pub.pdf)).
Serial correlation is a diagnostic, not proof of manipulation, and any
"unsmoothing" is model-dependent. Preserve raw returns and show adjusted
sensitivities; report long-run volatility, lagged beta, redemption-window loss, and
crisis dependence. A self-reported or non-investable index may be a descriptive
benchmark, never a tradable portfolio merely because it has monthly returns.

### Why an edge can exist without being easy to capture

Perfect informational efficiency is internally inconsistent when information is
costly: informed investors need compensation for acquiring it
([Grossman and Stiglitz 1980](https://www.aeaweb.org/aer/top20/70.3.393-408.pdf)).
That leaves room for edge, but does not identify a signal. Limits to arbitrage also
make apparent mispricing risky: specialized managers using outside capital can
lose funding after prices move further away from fundamentals, exactly when a
trade's long-run thesis looks strongest
([Shleifer and Vishny 1997](https://doi.org/10.1111/j.1540-6261.1997.tb03807.x)).
Competition, capital flows, regulation, technology, and participant ecology can
therefore create and destroy opportunities; the adaptive-markets framing is useful
as a hypothesis generator, not a forecasting model
([Lo 2004](https://doi.org/10.3905/jpm.2004.442611)).

The practical implication is sociological as well as statistical. A published
strategy changes the population trading it; assets under management, common
financing, benchmark pressure, redemptions, and crowded exits can turn historically
separate returns into one liquidity trade. The research ledger must therefore
record publication date, live assets/capacity, ownership concentration when
available, and performance before and after publication. Mechanism decay is not an
unexpected nuisance; it is a core falsifier.

## Numerical fixtures

These are closed-form, need no market data, and were each recomputed independently
of the paper that states them. They satisfy the root `AGENTS.md` requirement for
"at least one fixture computed independently of the implementation under test".

The test runner now exists, and every fixture below has been reproduced in
`research/tests/unit/`, re-derived in the test from its stated inputs rather than
hardcoded. This table is therefore scheduled for deletion: it survives only until
the last row is confirmed pinned by a named test, at which point the durable
outcome lives in the tests and this section becomes a pointer to them. Adding a
new fixture here rather than to a test is a regression.

| Fixture | Inputs | Expected result |
| --- | --- | --- |
| Diversification return, exact | Two assets, equal weights, returns +25%/−10% and +50%/−20%, \(\rho=1\) | \(g_A=6.0660\%\), \(g_B=9.5445\%\), \(\sum w_ig_i=7.8053\%\), \(g_p=8.1087\%\), DR = **+0.3035%** |
| Erb–Harvey form is wrong | Same, and \(\sigma=[5,10,20,35,50]\%\) equal-weighted | \(\tfrac12(1-1/N)\bar\sigma^2(1-\bar\rho)\) does not vanish correctly at \(\bar\rho=1\); overstates by 10.6% on the dispersed-vol case |
| Rebalance identity | \(w_S=0.6\), \(w_B=0.4\), \(\kappa_1=\kappa_2=-40\%\) | \(R_{\text{REBAL}}-R_{\text{HOLD}}=-3.84\) pp exactly; coefficient \(-w_Sw_B=-0.24\) |
| Zero-expected-profit test | Two assets, i.i.d. ±25%/−20% at \(p=0.5\), equal weights, two periods, 16 paths | \(E[W_T]=1.050625\) for **both** strategies; long/short trade \(E[\text{profit}]=0\), s.d. \$0.02531 |
| Kelly boundaries | \(\mu-r=5\%\), \(\sigma=18\%\), \(r=5\%\) | \(L^*=1.5432098765\); growth = \(r\) at \(3.0864\); growth = 0 at \(3.8815675216\) |
| Kelly vertex form | Same | \(g(L^*)=0.0885802469=r+(\mu-r)^2/2\sigma^2\); \(g(L)=r+\tfrac12\sigma^2[(L^*)^2-(L-L^*)^2]\) agrees with the quadratic to machine precision at \(L=0,0.5,1,1.5432,2,3,3.88\) |
| Equal risk contribution, two assets | \(\sigma_e=16\%\), \(\sigma_b=6\%\), \(\rho=0\) | \(w=(3/11,\ 8/11)\) exactly — equals inverse-volatility, and is *independent of \(\rho\)*; \(\sigma_p^2=288/75625\), \(\sigma_p=0.06171113727\); \(RC_e=RC_b=0.030855568634\), summing to \(\sigma_p\) (Euler) at 50/50 |
| ERC financing sensitivity | Same, levered to 16% volatility | \(L=2.5927249\) → 70.7107% equity, 188.5618% bonds, borrowing 159.2725% of NAV, so each 100 bp of spread costs 159.27 bp/yr |
| Cost-by-turnover rule | Novy-Marx–Velikov tier means | \(k=\text{cost}/\text{turnover}\) = 1.70 (low), 1.71 (mid), 1.57 (high) — stable across tiers, floor 1.0 |
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

Nor does combining twenty strategies that each win 55% of trades imply a durable
portfolio edge. A hit rate omits win and loss sizes: a strategy that wins $1 with
55% probability and loses $2 otherwise has negative expectancy. Even for equal
payoffs and a correctly known independent 55% probability, twenty simultaneous
bets produce a strict majority only about 59.1% of the time
(the exact binomial probability \(P[X\ge11]\)); they do not make outperformance
certain. In markets, independence and the 55% parameter are both
estimated from the same finite, selected history. Signals are commonly signed and
selected because they worked in sample, which makes multi-signal combinations
especially vulnerable to overfitting ([Novy-Marx 2015](https://www.nber.org/papers/w21329)).
Among 215 commercially promoted alternative-beta strategies, the median live
Sharpe deterioration from the backtest was 73%, and greater complexity predicted
larger deterioration
([Suhonen, Lennkh, and Perez 2017](https://ssrn.com/abstract=2757113)). That sample
is vendor-selected and not a census of all strategies, but it is direct evidence
against treating several reported edges as independent known probabilities.

The app must therefore combine *return distributions*, not success rates. It must
estimate joint downside and conditional crisis dependence, attribute shared factor
and funding exposures, shrink expected returns, and cap the effective number of
independent bets. A new sleeve whose residual return is not distinct after these
tests is a repackaging of an existing exposure, not another vote for leverage.

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

### Unknown unknowns and graceful failure

An unseen shock cannot be assigned a trustworthy probability from the historical
sample. Fatter fitted tails are useful sensitivity analyses, not an exhaustive
model of surprise. The engineering response is redundancy: hard exposure and
concentration limits, independent liquidity reserves, multiple execution paths,
counterparty limits, reverse stress tests, operational checks, and a safe failure
state. The FSB specifically recommends extreme-but-plausible collateral stresses,
contingency funding, diversified reliable liquidity, and operational resilience
([FSB 2024](https://www.fsb.org/2024/12/liquidity-preparedness-for-margin-and-collateral-calls-final-report/)).

The stress engine must solve the inverse question: what is the smallest joint move
in prices, spreads, margin, haircuts, correlations, and funding availability that
forces liquidation? It must also inject stale prices, missing settlements, contract
roll errors, wrong multipliers, halted markets, and revised regime labels. A
portfolio that silently carries stale weights fails; the application must stop,
identify the violated assumption, and fall back to the last explicitly safe state.

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
   return? The Chambers–Zdanowicz half of this question is now answered in the
   [expected-edge decomposition](expected-edge-decomposition.md): their dismissal
   targets an annualised rate rather than log wealth, and does not survive against
   \(E[\log W]\). What remains open is the genuine product choice — terminal
   wealth, log growth, or a liability/consumption objective — which evidence
   cannot settle and the investor policy must.
3. Which point-in-time datasets are licensed, reproducible, and rich enough to
   model delistings, publications, spreads, borrow, futures, and options?
4. What capital scale, tax model, leverage source, margin rules, and liquidity
   reserve define implementability?
5. How will the experiment ledger prevent undisclosed researcher degrees of
   freedom across code revisions and researchers? Note that the effective number of
   independent trials is unrecoverable retroactively, so the ledger must start
   before the first backtest, not after.
6. Which factor themes, definitions, and benchmarks survive both the strict
   frequentist Hou–Xue–Zhang construction and the hierarchical Bayesian
   Jensen–Kelly–Pedersen construction, then remain positive after executable costs?
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
10. How many days of autonomous cash liquidity are required, and which assets may
    genuinely be assumed monetizable during a systemic stress?

## Product and data contract

The web app should be a reproducible research instrument, not an answer vending
machine. Every result needs a stable experiment identifier and five linked views:

1. **Investor contract:** objective, benchmark, horizon, account and jurisdiction,
   cash flows, liabilities, currency, capital, instruments, drawdown/shortfall and
   ruin limits; tax lots and account capacities; occupation and employer exposure;
   stochastic labor income, pension and housing/debt; dependants; essential versus
   discretionary consumption; liquidity reserve and ability to change work,
   retirement, saving or spending after a loss.
2. **Evidence card:** mechanism, primary source, publication cutoff, frozen
   specification, known counter-evidence, falsifier, and status from proposed
   through live. “Replicated premium” must never be rendered as “alpha.”
3. **Portfolio comparison:** market weight, equal weight, drifting buy-and-hold,
   constrained minimum variance, and shrinkage baseline beside every candidate;
   uncertainty intervals and exposure attribution beside point estimates.
4. **Implementation ledger:** holdings and trades, point-in-time inputs, spreads,
   nonlinear impact, fees, borrow, financing, margin, taxes, capacity, turnover,
   and every attempted variation. Gross, executable net, stressed net, and
   after-tax results remain separate.
5. **Failure map:** shock type × horizon × currency × instrument × liquidity/funding
   state, including what the portfolio does *not* protect against. Show margin draw,
   worst gap, expected shortfall, maximum drawdown, recovery, time under water, and
   liquidity shortfall; do not collapse these into an unexplained protection score.

The minimum data schema must preserve source, retrieval/vintage and availability
timestamp; asset and share-class identity through delisting or merger; adjusted and
unadjusted prices; distributions and corporate actions; bid/ask and volume; cash,
borrow, financing and margin histories; futures chain, multiplier, roll and
collateral; option strike, expiry, settlement and executable quote; fund fee and
holdings history; and the exact transform that produced each feature. Derived data
must retain lineage back to raw observations. A current-symbol price table is not
adequate research data.

For funds and alternative indexes, also preserve `series_kind` (fund NAV,
non-investable peer index, investable index, rules backtest, or live product), a
stable economic-fund identity distinct from share class and vendor identifiers,
inception and first-trade date, vendor first-seen date, whether observations were
backfilled, live/graveyard status, last report and exit reason, reopening or
closure, valuation policy, AUM/capacity, and subscription, redemption, gate,
lockup, and notice terms. Raw reported returns remain immutable. Any exclusion of
backfill, duplicate resolution, long-run-volatility adjustment, or unsmoothing must
be a separately versioned transform with its assumptions exposed.

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

The algorithms, conditioning requirements, and closed-form fixtures for all of this
are specified separately in the
[numerical engine specification](portfolio-engine-specification.md), which also
settles where the optimiser should run. That page is subordinate to this one: it
says how to compute, never whether a return source is real.

Two existing files are inconsistent with this page and should be resolved rather
than extended. `src/utils/calculateOptimizedPortfolio.ts` is named for Kelly but
maximises a mean-variance utility with \(\gamma=5\), which silently answers open
question 2 in a way this page does not support — and because Merton's solution is
the mean-variance one divided by \(\gamma\), presenting that output as Kelly
overstates leverage by a factor of \(\gamma\). It has two further defects noted in
the engine specification: its finite-difference gradient normalises weights while
its objective does not, so it differentiates a different function from the one it
minimises, and it never checks that the user-supplied correlation matrix is positive
semi-definite, so an inconsistent matrix yields a negative variance and a `NaN`
risk. `scripts/seed-database.ts` emits an unseeded random walk, so it cannot
regenerate any fixture above; seeding it and exposing \(\mu\), \(\sigma\), and
correlation as explicit inputs would make it useful for exactly that.

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

Counter-source search now covers the central disputes in factor replication,
time-series momentum, volatility targeting, manager skill, and portfolio
estimation. It changed the conclusions rather than merely decorating them: factor
replication is model-dependent, trend's forecasting mechanism is disputed,
volatility targeting is risk control rather than established alpha, and manager
skill need not accrue to fund investors. It is still not a systematic review, and
absence from this page is not evidence against a strategy.

Coverage remains uneven. The gaps below are the highest-value next research
questions because each could change a construction decision rather than add a
minor caveat.

- **Lifecycle implementation.** The theoretical claim and human-capital
  counterexample are now documented, but taxes, realized margin paths, investor
  labor-income data and modern financing instruments still require an executable
  audit before any glidepath can be recommended.
- **Alternative-return implementation.** The risk mechanisms for trend, merger
  arbitrage, catastrophe risk, private credit, volatility selling and statistical
  arbitrage are now classified. None has yet passed a common point-in-time,
  net-cost, capacity-aware replication, and investable cat-risk data may be
  especially difficult to license. Catastrophe risk is the only one of the five
  whose capacity constraint is physical rather than competitive — the supply of
  insured catastrophe risk is bounded by exposed property, not by how many funds
  want the trade — so it is the one worth settling first. The test is explicit:
  assemble the annual spread-to-expected-loss multiple alongside realized losses,
  regress realized return on modelled expected loss, and ask whether the intercept
  is significantly positive *and stable across the 2017–18 and 2022 loss years*. If
  the load appears only in soft markets and is repaid in hard ones, it is tail
  compensation rather than alpha. Two controls are mandatory: repeat on net-of-fee
  fund returns rather than the index, since managed cat-bond strategies returned
  roughly 12–15% in 2024 against the index's 17.29%; and verify that vendor
  revisions to modelled expected loss have not re-baselined the denominator
  downward, which would manufacture an attractive multiple by construction.
- **Construction tournament.** Risk parity, shrinkage, Black–Litterman, robust
  optimization, HRP, resampling, and regime conditioning now have roles, a frozen
  comparison design, and falsifiers, but no common point-in-time walk-forward
  result. That experiment is still required before choosing a default beyond the
  simple constrained linear-shrinkage baseline.
- **Hedge-fund investability.** Historical survivorship, backfill, self-reporting,
  and smoothing magnitudes are now bounded well enough to reject naive index use.
  A current point-in-time fund population with post-delisting observations,
  subscription terms, capacity, fees, and executable proxies has not been acquired.
  The old studies cannot supply a universal bias correction.
- **The ergodicity-economics critique.** The specific Itô/Kelly equations and the
  mainstream normative objection have now been checked. What remains unsettled is
  the product decision: which finite-horizon investor objective and liability model
  this repository will implement. Ergodicity cannot settle that choice.
- **Taxes beyond the US and household data.** Asset location can reverse portfolio
  rankings, but tax lots, wash-sale networks, withdrawal sequencing, estate rules,
  currency/home bias and account types remain jurisdiction-specific data and legal
  questions. The app needs a versioned tax-policy boundary, not scattered formulas.

Four specific sources resisted retrieval and are named so nobody re-spends the
budget discovering that. The Jensen–Kelly–Pedersen internet appendix is not
publicly reachable, so the +20.6pp construction step in the decomposition above
cannot be attributed between capped value weighting, terciles, and the longer
sample; nor can the pure uncapped value-weighted rate, which is the number that
would settle the weighting dispute. No Hou–Xue–Zhang reply to that paper was found,
and no rebuttal to Huang et al. on time-series momentum was found — in both cases
searched for and absent, not merely uncited. Post-publication trend returns are no
longer an open gap: [Experiment 004](trend-marginal-value.md) measured them on the
AQR series, and the standalone decay is severe — Sharpe 1.34 pre-publication
against 0.18 recently, geometric 19.4% against 3.1%. The decay is in the
*standalone* series; the sleeve's *marginal* contribution to a portfolio falls far
less (2.00 to 1.01 pp/yr), though its post-publication interval now includes zero.
Note also that the statistical failure Huang et al. identify occurs inside the
original 1985–2009 sample, so it is an inferential problem as well as a decay
story, and the two are separate objections.
Current retail borrow rates, box-spread financing, futures roll costs and ETF
bid-ask spreads are unverified, and the fraction of a long-short premium that a
long-only tilt captures was not established by any source — which matters, because
a retail investor cannot implement most academic long-short factors at all.

No positive candidate on this page has passed this repository's full net-cost,
point-in-time, independently reproduced, frozen out-of-sample protocol. Published
gross returns are hypothesis inputs, not portfolio return forecasts.
