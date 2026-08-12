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
must beat, not a claim that the final answer has already been found
([decision 0003](../decisions/0003-cheap-broad-market-control.md)).

## Can you near-definitively beat the market? The direct answer

This section is written to be read on its own. Everything in it is derived on the
pages linked beside it; nothing here is new evidence. `as of 2026-08-12`, after
sixteen ledgered runs across six frozen experiments.

The commissioning premise was: *"The goal is to have information and strategies and
research to near definitively beat the market. Beating the market is not
hypothetical; it's definitely possible (ie, capture rebalancing bonus against two
assets that both return the market). But that's not enough."*

The honest answer has two halves and both are load-bearing.

### Yes — against your own counterfactual, and the arithmetic is deterministic

Against **the portfolio you would otherwise have owned**, roughly **89 basis points
a year** is available, at about **41 bp of tracking error**, reaching 90% confidence
in about **four months** and 99% in about **fourteen**. It decomposes into three
lines, none of which is a forecast
([edge decomposition](expected-edge-decomposition.md) §2):

| Line | Central | Range | Mechanism |
| --- | ---: | --- | --- |
| Fund cost reduction | **49 bp** | 40–59 | Asset-weighted 0.09% for broad index funds against 0.57% for active (Morningstar 2026); ICI gives 0.05% against 0.64% |
| Tax-loss harvesting | **30 bp** | 0–90 | Conditional on a taxable account, direct security ownership, offsetting gains and continuing contributions |
| Asset location | **10 bp** | 0–21 | Conditional on holding more than one account type and more than one asset class |
| **Total** | **89 bp** | 40–170 | TE ≈ 41 bp; `P(ahead at 30 yr) ≈ 1.00` |

The certainty comes from the *pairing*, not from the size. `P(outperform) =
Phi(e sqrt(T) / s)`, so at `e = 89 bp` and `s = 41 bp` a single year already gives
0.985 and fourteen months gives 0.99. The reason the tracking error is small is that
none of these lines is a bet: a fee not paid and a tax not realised are contractual,
and [Sharpe (1991)](https://web.stanford.edu/~wfsharpe/art/active/active.htm) makes
the fee half an accounting identity — *"they depend only on the laws of addition,
subtraction, multiplication and division."*

**Cost, tax location, and not trading. That is the whole of the near-definite part,**
and none of it requires a view on any market. It is also the part that is *already
spent* once taken: an index fund cannot beat its own index by cutting its fee again.

### No — against a cheap index, at any horizon a human has

Against **a stated cheap index**, the entire honest budget is about **24 bp/yr,
ranging −30 to +101 bp, against 401 bp of tracking error**. That gives a thirty-year
probability of being ahead of **0.631**, and 90% confidence would take roughly
**443 years**. The budget's three probabilistic lines are a factor tilt (21 bp
central, sign not robust), rebalancing (2.4 bp) and securities-lending pass-through
(1 bp). **Read 24 bp as an upper bound, not a central estimate** — for the reason in
the second bullet below.

Two things make this worse than it looks, not better.

- **The factor line is still a construction, and one term of it is now measured.**
  Its 21 bp is `6.6%/yr gross long-short × 0.42 post-publication retention × 0.40
  long-only capture × 0.30 portfolio exposure − 12 bp incremental fee`. The first two
  terms are now measurements for value rather than literature: pooling three regions
  gives HML **+4.74 pp/yr** post-publication against +4.56 in its US original sample,
  so the retention factor is closer to 1 than to 0.42 for that factor
  ([Exp 005](factor-persistence.md#experiment-005--the-regional-replication)) —
  though the pooled figure is gross and long-short in three regions, which is not the
  same object the 0.42 was measured on. **The long-only capture fraction is still not
  established by any source read here, and it is now the binding unknown.** Halve it
  and halve the exposure and the chain goes negative regardless of the premium.
- **The rebalancing line is now refuted downward by this repository's own data.**
  [Experiment 003](rebalancing-policy.md) measured **−38.7 bp/yr** on the portfolio
  and **−62.9 bp/yr** on the canonical regional pair over 35 years. The +2.4 bp in
  the budget is an equal-drift upper bound that a real drift gap removes.

Read the arithmetic the other way and it stops being about markets at all. Thirty
years against 400 bp of tracking error can *demonstrate* an edge of only about
94 bp/yr at 90% confidence, and fifty years only 72 bp. **No probabilistic line in this budget is demonstrable
from an investor's own experience.** The horizon scales with the square of `s/e`, so
tracking error, not edge size, decides whether a lifetime is enough: the same 50 bp
edge reaches 90% confidence in 24 days against 10 bp of tracking error and in
105 years against 400 bp.

### The rebalancing example: mathematically true, conditionally true, empirically dead

The premise named one specific mechanism, and it deserves a specific answer in three
parts.

**It is mathematically true.** For constant long-only weights, portfolio log growth
carries a non-negative excess term `gamma_star = 0.5 (sum_i w_i sigma_i^2 −
sigma_p^2)`. A buy-and-hold portfolio converges almost surely on its single best
component, so it asymptotically throws the whole of `gamma_star` away. With *equal*
drifts, a constant-weight portfolio beats buy-and-hold eventually, always
([edge decomposition](expected-edge-decomposition.md) §1.1).

**It is provably conditional, and the condition is exact.** Constant weights beat
buy-and-hold in almost-sure growth rate **iff `g_p > max_i g_i`**. The break-even is
horizon-free: at a drift gap equal to `gamma_star`, the probability is exactly 0.5 at
*every* horizon, and above it rebalancing loses with probability approaching one.
Waiting does not help. Even in the ideal equal-drift case the win probability has a
floor of `2 Phi(1) − 1 = 68.27%` and reaches 90% only at `gamma_star × T ≈ 3.90` —
**390 years** at the most favourable plausible `gamma_star` of 100 bp/yr. "Near
definitively" is refuted quantitatively, not rhetorically.

**It is empirically dead on the canonical real pair.** [Experiment 003](rebalancing-policy.md)
tested it on US, developed-ex-US and emerging equity over 420 months. The closed form
for `gamma_star` reproduced **to within 0.09 bp/yr on the portfolio** — the
mathematics is not the problem. What failed is the premise that two broad equity
markets "both return the market":

- US against developed-ex-US ran a realised drift gap of **4.34 pp/yr against a
  `gamma_star` of 12.5 bp/yr — a factor of about 35**.
- The realised advantage was **−62.9 bp/yr**, against **−70.5 bp/yr** predicted once
  the closed form is extended to that drift gap. The theory predicted the loss.
- The 68.27% floor did not survive: over rolling 30-year windows of that pair the
  realised frequency was **0.0%, zero of 61 windows**.
- `kappa_t`, the difference in simple returns between the two sleeves, is
  **positively** autocorrelated in every pair tested — every Lo–MacKinlay variance
  ratio at every horizon exceeds one. Relative regional performance *trends*.
  Rebalancing is short exactly that.
- Every rebalanced policy had an equal or **worse** maximum drawdown than the
  untouched portfolio.

Costs are not the explanation and must not be offered as one: the most expensive
policy paid 1.2 bp/yr, and quadrupling every cost moved the result by about a tenth
of the shortfall. **Rebalancing lost to the drift gap, not to friction.**

What rebalancing *did* buy is real and is not return: it held the portfolio within
0.6 to 3.1 percentage points of its declared weights against buy-and-hold's 14.8, for
0.3 to 1.2 bp/yr. That is keeping a promise, and it is the only claim the evidence
supports.

### What would have to be true for this answer to change

Five conditions, each of which is a measurable target rather than a hope.

1. **A licensed, survivorship-free, point-in-time total-return source.** This is the
   binding constraint on every investable conclusion
   ([decision 0002](../decisions/0002-no-research-grade-free-price-source.md)).
   [Experiment 002](factor-product-audit.md) can only see 72 months, where the median
   minimum detectable alpha across its 132 fund-by-specification tests is **4.52 pp/yr**
   against a true cross-sectional dispersion of gross alpha of about 1.25 pp/yr. The
   window cannot see the effect it is looking for by roughly a factor of three, and
   its returns have **no independent corroboration of any kind** — the cross-source
   check refused all 44 requests.
2. **An investable, low-correlation pair whose drift gap is genuinely below its
   `gamma_star`.** No such pair was tested. Every pair in Experiment 003 correlates
   0.72 to 0.79 in logs, and the drift gap dominated.
3. **A measured long-only capture fraction of a long-short factor premium.** The sign
   of the factor line depends on a number no source establishes.
4. **Tracking error reduction, not edge enlargement.** Because `T = (z s / e)**2`,
   halving tracking error quarters the horizon to any confidence level. Every
   feasible improvement to the index-relative answer is on the `s` side.
5. **Post-publication windows with power. This one is now settled, and negatively.**
   Against this repository's own 2.0 pp/yr materiality threshold, no post-publication
   window in Experiment 001's US grid exceeds 26% power.
   [Experiment 005](factor-persistence.md#experiment-005--the-regional-replication)
   added every independent region the public library distributes and **measured** what
   that bought: 1.49 effective regions out of three for HML and 2.26 for RMW, leaving
   the best pooled detection threshold at **2.62 pp/yr**, still above 2.0. **A premium
   between zero and about 2.6 pp/yr is invisible in public factor data no matter how
   it is pooled** ([decision 0005](../decisions/0005-factor-premia-closed-on-public-data.md)).
   One factor cleared it anyway, because its premium is larger than the threshold:
   pooled HML is +4.74 pp/yr `[+1.46, +8.10]` and is now `exploratory`.

Absent those, the defensible statement is the one this repository will make: *you can
near-definitively beat the portfolio you would otherwise have owned, by roughly 90
basis points a year, because most of that edge is contractual rather than
statistical. You cannot near-definitively beat a cheap index, at any horizon a human
has.* The asymmetry is not a fact about markets. It is a fact about which benchmark a
saving is measured against.

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

**That test has now been run and it is `rejected`.**
[Experiment 003](rebalancing-policy.md) applied exactly that design to US,
developed-ex-US and emerging equity over 420 months. The \(\kappa_t\) diagnostic
came back **positive** in every pair — relative performance trends rather than
reverts — and every policy lost to buy-and-hold on all three cost bases with a worse
maximum drawdown. Rebalancing is retained as a *risk-control* policy, which is what
the same experiment measured it to be: exposure held within 0.6 to 3.1 percentage
points of target against buy-and-hold's 14.8, for 0.3 to 1.2 bp/yr.

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

This repository has since measured HML, UMD, RMW and CMA over frozen pre- and
post-publication eras in the US, and then re-measured HML, RMW and CMA across the
US, developed-ex-US and emerging files over the *same* eras. See
[factor persistence and decay](factor-persistence.md) for the era boundaries, the
power calculation that made three of them `unresolved` in the US, and what adding
two regions did to that. The short version: **HML reached `exploratory` on a pooled
+4.74 pp/yr carried by the two non-US regions; RMW and CMA are `rejected` and closed
on public data, because the measured pooled window still cannot resolve a 2.0 pp/yr
premium; UMD could not be tested regionally at all.** No sleeve is promoted.

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

## Numerical fixtures live in the tests

The closed-form fixtures that used to be tabulated here are now pinned by named
tests, re-derived in each test from its stated inputs rather than hardcoded. They
need no market data, so they satisfy the root `AGENTS.md` requirement for "at least
one fixture computed independently of the implementation under test" without any
data contract. **Adding a new fixture to this page rather than to a test is a
regression.**

| Fixture family | Pinned by |
| --- | --- |
| Kelly optimum, the two leverage boundaries, the vertex form, ERC financing sensitivity | `research/tests/unit/test_core_kelly.py` |
| Exact diversification return, the two-period rebalance identity, the zero-expected-profit lattice, `kappa` as the diagnostic | `research/tests/unit/test_core_rebalance.py` |
| Two-asset ERC equals inverse volatility independent of `rho`, Euler risk contributions, the `sigma_MV <= sigma_ERC <= sigma_1/n` ordering | `research/tests/unit/test_core_portfolio.py` |
| One-sided turnover convention, the cost-by-turnover constants `k`, square-root impact, the retail implementability limit | `research/tests/unit/test_core_costs.py` |
| Expected maximum Sharpe, trial dispersion *across trials*, effective trial count under correlation | `research/tests/unit/test_inference_deflated_sharpe.py` |
| The `1.25**2 / (1.25**2 + 3.36**2) = 0.121` shrinkage factor and the ×12 (never ×√12) annualisation trap | `research/tests/unit/test_experiments_exp_002_fund_exposure.py` |
| The `gamma_star` closed form, the short-straddle identity, the 68.27% floor, the horizon-free break-even drift gap | `research/tests/unit/test_studies_volatility_harvesting.py` |
| Chambers–Zdanowicz Exhibit 5, the mean-preserving contraction, the annualised-rate mislabel | `research/tests/unit/test_studies_chambers_zdanowicz.py` |

Three things a test cannot carry survive here.

**The Erb–Harvey approximation is wrong and is deliberately not implemented, so no
test pins it.** For two assets at equal weights with returns +25%/−10% and
+50%/−20% and \(\sigma=[5,10,20,35,50]\%\) equal-weighted,
\(\tfrac12(1-1/N)\bar\sigma^2(1-\bar\rho)\) wrongly vanishes at \(\bar\rho=1\),
where the exact diversification return is **+1.37%** — dispersed volatilities leave
a Jensen gap even at perfect correlation. **The "overstates by 10.6%" half of the
original record did not reproduce** and is withdrawn: recomputed under both readings
of \(\bar\sigma^2\) (mean variance, and the square of mean volatility) the
approximation *understates* for every \(\bar\rho>0\), by ratios of 0.853 / 0.623 /
0.216 at \(\bar\rho=0.3/0.6/0.9\), and is exact at \(\bar\rho=0\) under the
mean-variance reading. The direction of the error, not only its size, was recorded
wrongly. Use `core/rebalance.py`'s exact form.

**Three constants must be re-derived per parameterisation, never hardcoded**: the
36.5% return-matched equity weight in the put-protection comparison, the \$0.050625
per-path gap, and the −3.84 pp two-period rebalance figure (its multiperiod analogue
in the same paper is −5.3 pp). The 0.44 prior Sharpe scales as
\(\sqrt{240/N_{\text{months}}}\).

**A fixture that disagrees with our own computation is a finding, not a tolerance to
loosen.** The Phase 1 gate is the standing example: it is
[`unresolved`](fama-french-reproduction.md) because two published standard deviations
did not reproduce and the declared tolerance was not touched.

## The provisional portfolio-design map

**This is not an allocation, and it is not a recommendation.** An allocation becomes
appropriate only after the investor policy is defined — benchmark, horizon, tax
status, liabilities, cash flows, drawdown tolerance, liquidity reserve, permitted
instruments and objective — and none of that is settled here. This map records, per
candidate, what would have to become true before it could be held. It supersedes the
earlier "candidate hypotheses and rejection rules" table, which carried the same
candidates without their evidence, their data quality, or their measured status.

Statuses are the closed vocabulary — `exploratory`, `source-reproduced`,
`independently-reproduced`, `walk-forward-tested`, `shadow-live`,
`production-eligible`, `rejected`, `unresolved` — and are never collapsed into
"works" or "does not work". `not tested` means no ledgered run exists.

### Map A — what each candidate is

| Candidate sleeve | Baseline portfolio | Investable proxy | Expected mechanism | Experiment status |
| --- | --- | --- | --- | --- |
| **Cheap broad market** | itself; it is the control | VTI / VOO / ITOT and a broad ex-US fund, 3 bp, ~1.3 bp round trip | Equity risk premium; the only line whose delivery is contractual | **the control**, [decision 0003](../decisions/0003-cheap-broad-market-control.md) |
| **Value (HML)** | cheap broad market | 33 of the 44 screened funds grade on HML; 15 reached `exploratory` as proxies only | Risk or behavioural premium on book-to-market | **`exploratory`** ([Exp 005](factor-persistence.md#experiment-005--the-regional-replication)), on a pooled +4.74 pp/yr carried by the two non-US regions; products `exploratory`/`rejected` ([Exp 002](factor-product-audit.md)) |
| **Momentum (UMD)** | cheap broad market | MTUM — **the entire retail shelf** at $1bn / 0.60% | Underreaction; possibly risk | `unresolved` (Exp 001) and **untestable regionally**: no regional momentum file is manifested here; MTUM `rejected` (Exp 002) |
| **Profitability (RMW)** | cheap broad market | QUAL (`rejected` on cost) and SPHQ (`unresolved`) — the entire shelf | Gross-profitability premium | **`rejected`** (Exp 005, branch b): pooled +2.53 pp/yr against its own 2.62 pp/yr detection threshold. **Closed on public data** |
| **Investment (CMA)** | cheap broad market | none on the screened shelf | Conservative-minus-aggressive asset growth | **`rejected`** (Exp 001, confirmed by Exp 005 branch b). **Closed on public data** |
| **Size (SMB)** | cheap broad market | IJH, IJR, VB, SPMD, SPSM, EZM | Compensation for illiquidity/distress, disputed | not tested as a premium; 3 of 8 products `rejected` on cost |
| **Diversified trend** | 60/40 equity/cash | none audited; CTA funds unpriced here | Slow behavioural adjustment; crisis convexity | **`rejected`** on its frozen falsifier ([Exp 004](trend-marginal-value.md)) |
| **Rebalancing as policy** | any multi-sleeve portfolio | the portfolio itself | `gamma_star` excess growth; short relative-performance continuation | **`rejected`** as return ([Exp 003](rebalancing-policy.md)); retained as risk control |
| **Cost / tax / behaviour** | your own counterfactual | fund selection, account type, direct indexing, not trading | Contractual, not statistical | **deterministic**, 89 bp ([edge decomposition](expected-edge-decomposition.md)) |

### Map B — the evidence on each side, and how good the data is

| Candidate sleeve | Evidence supporting | Counterevidence | Data quality |
| --- | --- | --- | --- |
| **Cheap broad market** | Sharpe's arithmetic identity; measured fee gap 48–59 bp; ~1.3 bp round-trip friction at retail scale | Passive investors still trade: 7.6%/yr US turnover, implicit IPO/SEO costs (Pedersen 2018). And **FF5+UMD prices VTI itself at −0.55 pp/yr (HAC *t* = −3.41)** over 2020–2025, so the standard model does not even span the control | Highest available here. Filed N-PORT returns, sponsor-published fees and spreads, all dated — but N-PORT figures are unaudited, per-filer methodology, and uncorroborated |
| **Value (HML)** | Pooled across three regions, **+4.74 pp/yr `[+1.46, +8.10]`** post-publication, positive in all three, surviving Holm and its own best calendar year. Ex-US only it is **+6.33 `[+3.19, +9.58]`**. Emerging HML's BH-adjusted *p* is **0.0002** | The **US** leg is +1.57 pp/yr and survives no correction; the result is a five-fold spread across regions (US +1.57, developed ex-US +5.07, emerging +7.58) and the largest leg sits where shorting is hardest. Pooled detection threshold is still 3.35 pp/yr, so 2.0–3.3 pp/yr remains invisible. Three regions are worth an effective **1.49**, not three | Phase 1 `unresolved`: US HML's standard deviation carries a **−3.03% systematic band**; the two regional files were **never gated at all**. Long-short, gross, USD unhedged, not investable |
| **Momentum (UMD)** | +9.85 pp/yr original; +4.19 pp/yr post-publication; MTUM's UMD loading +0.444 `[+0.277, +0.562]`, sign stable across the fixed calendar split and all 37 rolling windows | Only post-publication cell that looked significant is exactly what BH removes; −56.6% worst year (2008-12…2009-11); illustrative cost **3.30–18.67 pp/yr** against a +4.19 gross premium; MTUM `rejected` after a **1.22 pp/yr** shortfall against a combination whose fee premium over it was 0.12 | **Second moment never gated** — the momentum file was never reproduced against a printed table. Weaker than a band of zero |
| **Profitability (RMW)** | 96% of its US premium retained; mildest post-publication drawdown (−14.8%); low-turnover tier; pooled +2.53 pp/yr `[+1.07, +3.96]`, positive in all three regions; its regions are the least correlated of the three factors (ρ̄ = 0.18), so pooling helped it most | **Its pooled premium is below its own pooled detection threshold** — 2.53 against 2.62 pp/yr, whose entire 90% interval `[2.15, 3.07]` sits above materiality. 59% of the US premium is 2021, and the pooled premium falls to +1.79 when its best year is dropped | Phase 1 `unresolved`: US RMW's standard deviation carries a **+5.09% systematic band**; the regional files were never gated. The branch (b) verdict holds across the whole band |
| **Investment (CMA)** | +3.91 pp/yr in the original sample, the strongest of the four. Outside the US its post-publication premium is ~0 rather than negative (+0.53 developed ex-US, +1.46 emerging), so the US sign flip does **not** replicate | **−1.39 pp/yr post-publication in the US**; +0.20 pp/yr pooled against a 3.41 pp/yr pooled detection threshold. It is the one factor whose three regions share the same best calendar year (2022), so they are the least independent looks in the grid | Reproduced to 0.53% on the second moment, so it carries no Phase 1 band. Rejection tested against the most generous candidate discovery date, and now against two further regions |
| **Size (SMB)** | Exposure is delivered and stable: SPSM/IJR +0.889, VB +0.599 | Weak as a standalone premium (Hou–Xue–Zhang); **never tested as a premium here**; VB carries the largest shortfall on the shelf, **+2.89 pp/yr** against the fitted cheap combination | 72 months of filed returns; MDE₈₀ 1.97–3.16 pp/yr on these funds |
| **Diversified trend** | +1.342 pp/yr marginal CE `[+0.759, +1.916]`; survives every hostile test; payoff spread across four structurally different crises; crisis correlation −0.59, downside beta −0.67 | A static + volatility-exposure replica delivers **44%** of it; post-publication interval includes zero and fails Holm; standalone Sharpe 1.34 → 0.18; **vendor states no cost basis anywhere**; comparable CTA survivorship/backfill distortion is 7.7 pp/yr | Vendor-series evaluation, ceiling `exploratory` by construction. Early history substitutes index returns for futures |
| **Rebalancing as policy** | `gamma_star` closed form reproduces on real data to **0.09 bp/yr**; exposure held to 0.6–3.1 pp against 14.8 | Every policy lost on all three cost bases; realised drift gap **35× `gamma_star`**; `kappa` trends rather than reverts; drawdown equal or worse | French regional total returns, 420 months, pinned by sha256. Pretax only — no tax lots exist |
| **Cost / tax / behaviour** | Morningstar and ICI fee studies; Chaudhuri–Burnham–Lo harvesting alpha after liquidation taxes; N-CSR securities-lending filings | Harvesting decays to ~0 within five years without new money; behaviour gap refuted from 1.2 pp to ~0.10 pp (Fulkerson et al. 2026); DALBAR must not be cited | Vendor research and regulatory filings, dated. US-only and jurisdiction-specific |

### Map C — what they share, how they fail, and what would promote them

| Candidate sleeve | Shared exposures | Failure regimes | Conditions required for promotion |
| --- | --- | --- | --- |
| **Cheap broad market** | It *is* the shared exposure. Every other row inherits its beta and its crises | Any equity bear market, in full | None — it is the control, not a candidate |
| **Value (HML)** | **0.63 correlated with CMA** over the common US post-publication period; its three regions correlate 0.52 and are worth an effective **1.49** looks, not three; shares equity beta and the same crowded exits | Prolonged growth regimes; intangible-heavy composition; 2010–2020 in full in the US | The premium is now signed, so what remains is the rest of the chain: **a long-only capture fraction measured rather than assumed**, and a product whose tracking difference against a cheap mix is not negative under [Exp 002](factor-product-audit.md)'s frozen promotion protocol |
| **Momentum (UMD)** | −0.325 to HML; shares equity rebounds with every long-only tilt | Rebound after a bear market (Daniel–Moskowitz); any regime where turnover cost exceeds the premium | A net-of-cost premium measured from observed turnover, not assumed tiers; one-sided monthly turnover below 50%; a second product so the shelf is not a single point of failure |
| **Profitability (RMW)** | 0.219 to CMA, 0.152 to HML in the US; its three regions correlate only 0.18 and are worth an effective 2.26 looks | Junk rallies; the same 2000–2002 window where its variance is concentrated; 2021 alone carries 62% of the US premium | **Closed on public data** ([decision 0005](../decisions/0005-factor-premia-closed-on-public-data.md)). Reopening needs a materially longer or genuinely independent premium series — a further decade of out-of-sample months, or a licensed non-French construction — not another pass over these files |
| **Investment (CMA)** | 0.63 to HML in the US — **never count them as two bets**; its three regions share the same best year and correlate 0.38 | Already failed: US post-publication sign flip, ~zero abroad | **Closed on public data**. Re-entry requires a new frozen specification and a genuinely post-2026 window; the current rejection stands |
| **Size (SMB)** | Small-cap liquidity, borrow and spread; the same equity beta | Liquidity events; the cost tail (VB's round-trip spread is 2.72 bp, ~a year of expense ratio) | A premium test that was never run, plus a product whose tracking difference against a cheap mix is non-negative |
| **Diversified trend** | **Leverage, funding liquidity, volatility estimation, short borrow**; it is a levered futures position and shares margin with everything else levered | Sharp reversals (measured: −0.53%/mo against +4.24% equity months); gaps a monthly series cannot even show; funding shocks; crowded exits | A multi-asset attribution that leaves a residual after non-US-equity exposures; a fund-level audit on a licensed total-return source with real fees; and a contract-level test of the volatility scaling, which no public aggregate can support |
| **Rebalancing as policy** | Sits **inside** the same equity portfolio as any factor tilt, so their tracking errors are not independent | Trending relative performance — which is the measured regime; crises, where it adds exposure to the fall | Promotion as *return* requires a real investable pair with drift gap below `gamma_star`. As *risk control* it needs no promotion and is already the recommended default |
| **Cost / tax / behaviour** | Tax-loss harvesting and asset location share a *condition*: one tax-deferred account zeroes both at once | A single account type; no offsetting gains; no new money; a flat capital-gains rate; non-US tax law | Already deterministic. What is missing is a versioned, dated, jurisdiction-specific tax boundary rather than scattered constants |

**Strategies are not additive because their backtests have low correlation.** The
sleeves above share, concretely: **leverage** (trend is a levered futures book),
**funding liquidity** (March 2020 impaired even the Treasury market — Fed staff put
hedge-fund Treasury holdings down $141bn), **volatility estimation** (trend, any
volatility target and any risk-parity weight all divide by the same estimated
covariance, which for HML and RMW carries a 3–5% systematic band from Phase 1),
**short borrow** (every academic long-short premium above; retail cannot implement
them at all), **equity rebounds** (momentum crashes exactly there), and **crowded
exits** (the August 2007 quant unwind was a three-day −6.85%, twelve daily standard
deviations, followed by a +5.92% rebound — a liquidity event, not a signal failure).
Any combination must expose that shared dependence explicitly, not assume it away.

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

## What advanced, what failed, and what remains unresolved

The accounting below is against the hypotheses this repository actually froze, in
the closed status vocabulary. `as of 2026-08-12`.

### The ledger, counted rather than described

Verified directly from [`research/ledger.jsonl`](../../research/ledger.jsonl):
**44 entries, 16 runs, 7 distinct specification hashes, 6 experiment families.**

| Terminal outcome | Runs | Which |
| --- | ---: | --- |
| `unresolved` | 2 | Phase 1 gate; Experiment 001 |
| `rejected` | 5 | Experiment 003 (1); Experiment 004 (4 executions of one specification) |
| `exploratory` | 4 | Experiment 002 (3 executions of one specification); Experiment 005 (1) |
| no terminal status | 5 | 1 `failed` (a parser table-name error), 4 `abandoned` (one operator interrupt, three SIGTERMs) |

Eleven runs recorded a `results_viewed` event; **no run consumed the final holdout**.
Two facts about this count matter more than the count.

- **Repeated executions of one specification are not independent hypotheses, and the
  ledger keeps them distinguishable.** Four of the five `rejected` rows are one
  specification hash run four times, and all three `exploratory` rows are one
  specification hash run three times. The number of distinct specifications searched
  is **seven**, not sixteen, and that is the number any deflated-Sharpe trial count
  must start from.
- **The ledger contains a correction to itself.** One `abandoned` entry was appended
  prematurely and for the wrong run's reason; rather than repair it in place, a
  superseding entry was appended saying so. That is why there are five `abandoned`
  events across four abandoned runs.

### Advanced

Nothing was promoted to a sleeve. One *factor* advanced a rung, and the rest of what
advanced is machinery and specific results that are now measurements rather than
citations.

- **Value reached `exploratory`, and it is the first thing on this page to do so on
  the strength of a premium.** Pooled across the US, developed-ex-US and emerging
  files over Experiment 001's own frozen post-publication era, HML returned
  **+4.74 pp/yr** with a cross-region joint 90% interval of `[+1.46, +8.10]`, the
  same sign in all three regions, survival of Holm–Bonferroni at an adjusted *p* of
  0.036, and survival of dropping its own best calendar year. It is `exploratory`, which permits an
  investable implementation to be *tested* and permits nothing else
  ([Exp 005](factor-persistence.md#experiment-005--the-regional-replication)).
- **The cost of naive pooling was measured, not asserted.** Resampling the three
  regions independently rather than jointly narrows HML's pooled interval by about
  1.5×, and in the recent decade it converts `[−2.36, +10.16]` into `[+0.06, +8.09]`
  — a significant result manufactured entirely by treating correlated regions as
  independent samples.

- **The excess-growth closed form is `source-reproduced` and now confirmed on real
  data.** `0.5 (sum w_i sigma_i^2 − sigma_p^2)` matched realised excess growth to
  within 0.2 bp/yr on every regional pair and 0.09 bp/yr on the portfolio
  ([Exp 003](rebalancing-policy.md)). On synthetic paths the Monte Carlo agrees with
  the closed form within three of its own standard errors.
- **The exact condition for constant weights to beat buy-and-hold was proved, not
  cited**: `g_p > max_i g_i`, with the break-even drift gap shown to be horizon-free
  ([edge decomposition](expected-edge-decomposition.md) §1.1).
- **The objective is declared.** Net geometric growth, equivalently expected log
  wealth, recorded as a *preference* justified by Breiman's asymptotic theorem rather
  than as a proof. This closes the Chambers–Zdanowicz half of open question 2.
- **The binding constraint was identified and written down**: no free price source
  carries a total-return contract, so fund-level work cannot exceed `exploratory`
  ([decision 0002](../decisions/0002-no-research-grade-free-price-source.md)).
- **The research loop exists end to end** — frozen specification, hashed input,
  deterministic calculation, adversarial validation, append-only ledger, synthesis —
  with 1,082 tests passing and a runner that refuses a confirmatory
  experiment lacking a benchmark, primary metric, cost model, sample policy and
  rejection rule.

### Failed — `rejected` against a predeclared falsifier

- **Rebalancing as a source of return.** All four policies lost on all three cost
  bases over 35 years; four independent rejection clauses fired at once. The
  mechanism that would make it pay is absent and its opposite is present at
  conventional significance ([Exp 003](rebalancing-policy.md)).
- **Profitability (RMW) and conservative-minus-aggressive investment (CMA), both now
  closed on public data.** CMA first: −1.39 pp/yr post-publication in the US against
  +3.91 in-sample, clauses (a) and (c) firing ([Exp 001](factor-persistence.md)).
  Experiment 005 then added two regions to both and fired **branch (b)** on each —
  the measured pooled minimum detectable effect is 2.62 pp/yr for RMW and 3.41 for
  CMA, both above the 2.0 pp/yr materiality threshold, and both with their entire
  90% sampling interval and Phase 1 systematic band above it too. **RMW's pooled
  premium of +2.53 pp/yr is smaller than the smallest premium its own pooled window
  can resolve.** Neither rejection says the premium is zero; both say the publicly
  available data cannot sign it, permanently
  ([decision 0005](../decisions/0005-factor-premia-closed-on-public-data.md)).
  CMA's US rejection is also now better understood: outside the US its
  post-publication premium is approximately zero rather than negative, so the sign
  flip is a US phenomenon and the rejection rests on materiality, not on the flip.
- **The AQR time-series-momentum series as a marginal sleeve.** `rejected` on clause
  (d), narrowly and on an *absolute* reading of the clause: a static
  time-varying-market-exposure replica with the intercept removed delivers 44% of the
  benefit. Under a relative reading the verdict would be `unresolved`, and the page
  says so ([Exp 004](trend-marginal-value.md)).
- **Twenty-four of 44 screened factor products.** Clause (c) did most of the work,
  firing on 22: a shortfall above 0.50 pp/yr against a fitted combination of VTI, VUG,
  VTV and VB, whose fee premium over those products was at most 0.32 pp/yr and
  typically 0.12. The comparator is fitted **in sample**, so every (c) rejection reads
  as "a look-ahead combination of four cheap funds beat this product over these 72
  months", never as "this product is badly run" ([Exp 002](factor-product-audit.md)).

### Unresolved — and why, which is not the same as negative

- **The Phase 1 ingestion gate.** Thirteen of fifteen gating cells reproduce; the
  standard deviations of HML and RMW do not, by variance ratios of 0.940 and 1.104,
  against two independently typeset vintages. Exact reproduction is unavailable at
  any tolerance because Ken French publishes no vintage archive. **Consequence: a
  systematic 3–5% denominator uncertainty on anything that divides by those
  volatilities** — a Sharpe ratio, a volatility-scaled sleeve, a risk-parity weight, a
  covariance matrix, a Kelly fraction. It is not sampling error and will not shrink
  with more data.
- **UMD, and UMD alone among the four factors.** It is the one Experiment 005 could
  not touch: the Ken French momentum file registered and manifested here is US-only,
  so there is no regional momentum series to pool. Its US post-publication premium is
  +4.19 pp/yr against a detection threshold of 7.27, and resolving it needs a data
  acquisition rather than an analysis. HML and RMW were `unresolved` for the same
  power reason and are no longer: one advanced and one closed.
- **Five of the 44 screened products**, whose intended exposure sits at or just above
  the 0.15 threshold with intervals that reach it.
- **Whether any of this is investable.** Experiment 002 is `exploratory` by decision,
  not by outcome, and cannot promote anything on a 72-month unaudited self-reported
  window whose median minimum detectable alpha is 4.52 pp/yr and whose returns have no
  independent corroboration at all.

### Never started

The **deferred financing experiment** and the **frozen construction tournament** have
designs, comparators and falsifiers on this page and no ledgered run. Leverage
remains at zero, which is the correct state: it was conditioned on an unlevered edge
surviving the protocol, and none has.

## The premium is signed for one factor. What that changed, and what is next

**Experiment 005 has run.** Its design, its frozen falsifier, its 27-cell regional
grid, its pooled tables and every hostile test live in
[factor persistence and decay](factor-persistence.md#experiment-005--the-regional-replication),
which is their canonical home. This section records only what the result changes for
the programme.

What a shareholder actually receives from any factor product is

```
premium  ×  delivered loading  −  cost
```

[Experiment 002](factor-product-audit.md) §12 measured the second and third terms and
found the loading **delivered** and the cost **measurable**. Experiment 001 could not
sign the first for any factor, which is why a licensed price source was the wrong
purchase: it buys resolution on the two terms that already work.

**Experiment 005 signed the first term for exactly one factor, and closed it for two.**

| Factor | Outcome | The number |
| --- | --- | --- |
| **HML** | branch (a): **`exploratory`** | Pooled +4.74 pp/yr, joint 90% `[+1.46, +8.10]`, positive in all three regions, survives Holm and its own best year |
| **RMW** | branch (b): **`rejected`**, closed on public data | Pooled +2.53 pp/yr against a measured detection threshold of **2.62** |
| **CMA** | branch (b): **`rejected`**, closed on public data | Pooled +0.20 pp/yr against a measured detection threshold of **3.41** |
| **UMD** | not testable | No regional momentum file is manifested here |

Three consequences follow, and none of them is a promotion.

- **The effective sample size is now a measured quantity, and it is the number to
  quote.** Three regions of HML over 384 months are worth **573 independent
  single-region months, not 1152** — an effective 1.49 regions out of three, at a mean
  cross-region correlation of 0.52. RMW's regions are less correlated (0.18) and are
  worth 2.26. **Any future claim that pooling n series adds n× the evidence must
  measure it, and this repository now has the machinery to.**
- **Public factor data has a floor, and it has been measured.** The best pooled
  detection threshold across every factor and era is **2.62 pp/yr**, above the 2.0
  pp/yr materiality threshold this repository uses. A premium between zero and about
  2.6 pp/yr cannot be signed from these files however they are combined. That is what
  [decision 0005](../decisions/0005-factor-premia-closed-on-public-data.md) records,
  and it is why no further public-data premium experiment on RMW or CMA should be
  commissioned.
- **The blocking term for value has moved one link down the chain.** It is no longer
  the premium; it is the **long-only capture fraction** — how much of a gross
  long-short spread a long-only tilt actually delivers. The
  [edge decomposition](expected-edge-decomposition.md) budgets 21 bp/yr for the factor
  line using an *assumed* 0.40 capture, and states plainly that no source read here
  establishes it. Halving it and halving the exposure turns the line negative.

### The next experiment: measure the long-only capture fraction

Regress a **long-only** value-tilted portfolio's excess return on the market and on
HML, over the same frozen post-publication eras and the same three regions, and
report the fraction of the long-short premium that the long-only tilt delivers, with
its interval and its own minimum detectable effect. The falsifier should be frozen
against the 0.40 the edge budget currently assumes, in both directions: a measured
capture materially below it kills the factor line arithmetically, and a measured
capture at or above it makes a licensed fund-level source worth buying for value
specifically.

**Data it needs, stated honestly.** The Ken French sorted portfolio files —
`25_Portfolios_5x5` and its regional equivalents — are the natural source, and
`french_us_25_portfolios_5x5` is already **registered** in this repository's dataset
registry with parser coverage and a test fixture. It is **not yet manifested**, so
retrieving it and pinning its bytes is the first step rather than a formality. The
regional sorted-portfolio files are neither registered nor manifested.

**Its known limits, before it is designed.** A long-only tilt built from sorted
portfolios is still not a fund: it has no fee, no turnover cost, no tax and no
tracking error against a real index. Measuring the capture fraction removes the last
*unmeasured* term in the chain but leaves the whole of implementation to
[Experiment 002](factor-product-audit.md), which cannot exceed `exploratory` on the
data available ([decision 0002](../decisions/0002-no-research-grade-free-price-source.md)).

**Why it beats the alternatives now.**

| Alternative | Effort | Why it loses |
| --- | --- | --- |
| **Buy a licensed point-in-time source** | money | Still buys the loading and cost terms, which already work, plus one term — capture — that free sorted portfolios can measure first. Buy it *after* the capture fraction, not before |
| Acquire a regional momentum file and finish UMD | low–moderate | Genuinely fills the one gap Experiment 005 could not reach, and is worth doing. But UMD is already outside the retail turnover limit and its illustrative cost exceeds its gross premium, so signing its premium unblocks nothing |
| Another public-data premium experiment on RMW or CMA | low | **Forbidden by decision 0005.** The floor has been measured; a further pass over the same files cannot clear it |
| Exit census of the fund series that stopped filing | low | Sharpens a survivorship bound outside the blocking chain — though its known defect (renames counted as deaths) should be fixed regardless, as a repair rather than an experiment |
| Read Form N-CSR for realised distributions and turnover | moderate | Sharpens *cost*, which is measured and is not the blocker |
| The frozen construction tournament | high | Decides how to weight sleeves; there is one `exploratory` factor and no promoted sleeve to weight |
| Obtain the 2013–14 CRSP vintage to settle Phase 1 | unbounded, likely impossible | The band it would remove is checked cell by cell in both experiments and **changes no conclusion anywhere** |
| Read the 2026-01-onward holdout | low | Six to eight months against windows whose pooled detection threshold is 2.6 pp/yr. Spends a genuine holdout for nothing |

**If a licensed purchase is eventually made, this is what the dataset must contain.**
Stated now so the specification exists before the budget does: fund and share-class
total returns net of fees at monthly or finer frequency, covering the listed shelf
**from at least 2003 so the window is 240 months rather than 72**; a
**survivorship-free universe with post-delisting observations and a coded exit
reason**; stable economic fund identity across share class, ticker change, merger and
vendor migration; inception and first-trade dates and a vendor first-seen date so
backfill is detectable; point-in-time expense ratios, net assets and index-mandate
history; documented total-return, distribution and corporate-action treatment; and a
stated revision policy with retrievable vintages. A source that supplies returns but
not exit reasons or vintages does not lift Experiment 002 above `exploratory`, and
paying for one that does not would be the most expensive way to learn nothing.

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

- the investable baseline is a low-cost, diversified passive portfolio, and it is
  now the formal control ([decision 0003](../decisions/0003-cheap-broad-market-control.md));
- the objective is net geometric growth subject to a drawdown or expected-shortfall
  constraint, declared as a preference rather than derived, with the horizon and the
  liability model still unchosen;
- strategies must be implementable by the intended investor at realistic scale;
- no expected alpha is accepted solely because a historical mean is positive; and
- leverage begins at zero until an unlevered edge survives the research protocol.
  **None has**, so leverage stays at zero
  ([decision 0004](../decisions/0004-no-sleeve-promoted.md)).

Open decisions must be settled before performance code is authoritative. Two of the
original ten are closed and are recorded as closed rather than deleted, because a
reader needs to know they were asked.

1. Who is the modelled investor — taxable or tax-advantaged, horizon, currency,
   liabilities, cash flows, drawdown tolerance, and accessible instruments? **Still
   open, and it is now the binding constraint on producing an allocation rather than
   a design map.** Experiments 003 and 004 each declared CRRA `gamma = 3` for their
   own comparison; that is a per-experiment preference, not a product decision.
2. What exact benchmark and objective define "beat the market"? **Closed on the
   objective, open on the horizon and liability model.** The
   [edge decomposition](expected-edge-decomposition.md) settles the
   Chambers–Zdanowicz half — their dismissal targets an annualised rate rather than
   log wealth and does not survive against \(E[\log W]\) — and declares net geometric
   growth as a preference justified by Breiman rather than as a proof. On the
   benchmark, the answer is that there is no single one: cost savings are measured
   against the investor's own counterfactual, factor and rebalancing lines against a
   stated index, and the two must never be aggregated.
3. Which point-in-time datasets are licensed, reproducible, and rich enough to model
   delistings, publications, spreads, borrow, futures, and options? **Open, and now
   the single binding constraint on every investable conclusion**
   ([decision 0002](../decisions/0002-no-research-grade-free-price-source.md)). The
   required contents are specified above under "The next experiment".
4. What capital scale, tax model, leverage source, margin rules, and liquidity
   reserve define implementability?
5. ~~How will the experiment ledger prevent undisclosed researcher degrees of
   freedom?~~ **Closed by implementation.** `research/src/portfolio_edge/experiments/ledger.py`
   appends every attempted run including failures and abandonments, with
   specification hash, git commit, worktree diff hash, dataset-manifest hashes,
   seed, run kind, `results_viewed` and `consumes_final_holdout`; the runner refuses
   a confirmatory run whose specification lacks a benchmark, primary metric, cost
   model, sample policy or rejection rule. What the ledger does **not** solve is the
   dependence between trials: six distinct specifications across fifteen runs is a
   count, not an effective number of independent tests, and no procedure recovers
   that automatically.
6. Which factor themes survive both the strict frequentist Hou–Xue–Zhang
   construction and the hierarchical Bayesian Jensen–Kelly–Pedersen construction,
   then remain positive after executable costs? **Still open, and narrowed.**
   Experiment 001 measured four factors on the French value-weighted construction
   only; the equal-weighted variant is not distributed and the test was **not run**,
   which matters because that single choice moves published replication rates from
   35% to 58.6%.
7. What is the net-of-cost equivalent of each gross figure on this page? **Partly
   answered, still open in general.** Experiment 003 charged costs inside the
   simulation rather than as a haircut; Experiment 002 used returns already net of
   fund fees; Experiment 001 reports an illustrative cost column beside — never
   subtracted from — its gross premia. Every academic long-short figure above remains
   an upper bound of unknown tightness.
8. Does risk-constrained Kelly beat fractional Kelly on bootstrapped historical
   returns? It does so by about 34% in growth at matched drawdown risk on the
   finite-outcome case in
   [Busseti, Ryu, and Boyd](https://web.stanford.edu/~boyd/papers/pdf/kelly.pdf), but the
   advantage vanished on that paper's own fat-tailed mixture — the case it says
   resembles a real portfolio problem — and only two synthetic single draws were
   ever tested. Untested here, and correctly deferred: it sizes an edge, and there is
   no edge to size.
9. What estimation window and regime-conditioning scheme should the covariance
   matrix use, given the documented bond–stock beta sign flip? Note that for HML and
   RMW any such matrix inherits Phase 1's 3–5% systematic volatility band.
10. How many days of autonomous cash liquidity are required, and which assets may
    genuinely be assumed monetizable during a systemic stress?
11. **What fraction of a long-short factor premium does a long-only tilt capture?**
    Promoted from a buried caveat to an open question because the sign of the entire
    factor line in the edge budget depends on it and no source read here establishes
    it.

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

Do not extend the current optimizer or label its output Kelly-optimal.

Steps 1 through 5 of the original build order are **done**: the primitives, the
passive and rebalancing policies, volatility scaling applied identically to
benchmark and sleeve, the factor and trend replications with frozen specifications,
and walk-forward, block-bootstrap and multiple-testing diagnostics all exist in
`research/` under a test runner ([decision 0001](../decisions/0001-contained-python-research-workspace.md)),
with 1,082 tests passing `as of 2026-08-12`, 18 of them network-marked. What
remains, in order:

6. portfolio combination and stress testing; and only then
7. fractional/risk-constrained Kelly and leverage with live financing and margin
   rules.

Neither may begin yet, and the reason is not sequencing. **Step 6 combines sleeves
and there are no promoted sleeves; step 7 sizes an edge and there is no edge to
size** ([decision 0004](../decisions/0004-no-sleeve-promoted.md)). The next
substantive move is still evidence rather than code. Experiment 005 has now run and
signed exactly one premium; what it did **not** buy is a long-only capture fraction
or a fund-level data contract, and both remain prerequisites.

Three standing rules survive from that build order.

- **Closed-form fixtures come before any data contract.** The primitives were and
  remain testable without market data; they now live in `research/tests/unit/`.
- **The trial ledger must precede the first backtest**, because the effective number
  of independent trials cannot be reconstructed afterwards. It did, and the current
  count is seven distinct specifications across sixteen runs.
- **Any estimated alpha passes through shrinkage before it reaches a sizing
  function**, using *that estimate's own* standard error. The reference factor of
  0.121 comes from a 3.36%/yr standard error typical of an active fund; on index
  funds with tighter errors the median factor was 0.431, and hardcoding the
  reference would have over-shrunk every one of them. Omitting shrinkage entirely is
  the most likely catastrophic sizing error in a Kelly system.

The first useful script should make false confidence harder. It should reproduce a
benchmark, expose every assumption and cost, and fail loudly on look-ahead,
unavailable data, weight violations, insolvency, and unrecorded experiments before
it searches for an optimal portfolio. That is now what
[`research/`](../../research/README.md) is.

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

Coverage remains uneven. The gaps below are what is left after five experiments;
each could change a construction decision rather than add a minor caveat. **None of
them was the recommended next step** — that was Experiment 005, which has now run —
and all five remain blocked on a data contract that does not exist yet.

- **Lifecycle implementation.** The theoretical claim and human-capital
  counterexample are now documented, but taxes, realized margin paths, investor
  labor-income data and modern financing instruments still require an executable
  audit before any glidepath can be recommended.
- **Alternative-return implementation.** The risk mechanisms for trend, merger
  arbitrage, catastrophe risk, private credit, volatility selling and statistical
  arbitrage are now classified, and **trend is no longer among the untested**:
  [Experiment 004](trend-marginal-value.md) evaluated the AQR vendor series and
  `rejected` it on its frozen falsifier, without touching investability. None of the
  five has passed a common point-in-time, net-cost, capacity-aware replication, and
  investable cat-risk data may be especially difficult to license. Catastrophe risk
  is the only one of the five
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
- **Fund and hedge-fund investability.** Historical survivorship, backfill,
  self-reporting and smoothing magnitudes are now bounded well enough to reject naive
  index use, and [Experiment 002](factor-product-audit.md) put a floor under the
  problem in the retail ETF shelf: **312 of the 1,513 mandate-qualifying series in the
  2019Q4 frame — 20.6%, holding $138.7bn — were absent from the 2025Q4 census.** (The
  artifact's own headline of 358 / $333.5bn is defective: it counts a series that
  renamed out of the mandate pattern as a death, and four of its fifteen largest
  "disappeared" series are recorded in the same file as still filing. The defect is
  documented and open.) That figure is a **lower bound**, because public N-PORT filings
  begin in 2019 and a fund that closed earlier is invisible to both censuses; and the
  fact that all 44 audited funds survived is **true by construction**, since 72 months
  of filed returns were required to enter the panel. A point-in-time fund population
  with post-delisting
  observations, subscription terms, capacity, fees and executable proxies has still
  not been acquired
  ([decision 0002](../decisions/0002-no-research-grade-free-price-source.md)), and
  the old studies cannot supply a universal bias correction.
- **The ergodicity-economics critique.** Closed on the algebra and on the objective:
  the Itô/Kelly equations and the mainstream normative objection were checked, and
  net geometric growth is now declared as a *preference*. What remains is the
  finite-horizon liability model — consumption, drawdown, or terminal wealth — which
  no evidence can settle and the investor policy must.
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
**ETF bid-ask spreads are no longer unverified**: dated, sponsor-published 30-day
median spreads and expense ratios are in the
[edge decomposition](expected-edge-decomposition.md) §2.1 `as of 2026-08-10`, and
the finding there is that retail implementation friction is about 1.3 bp round trip,
with nothing left to harvest. Current retail borrow rates, box-spread financing and
futures roll costs remain unverified, and the fraction of a long-short premium that
a long-only tilt captures was not established by any source — which matters, because
a retail investor cannot implement most academic long-short factors at all.

No positive candidate on this page has passed this repository's full net-cost,
point-in-time, independently reproduced, frozen out-of-sample protocol. Published
gross returns are hypothesis inputs, not portfolio return forecasts. Five
experiments have now been run against frozen falsifiers and **nothing was promoted**
([decision 0004](../decisions/0004-no-sleeve-promoted.md)); the conditions that
would change that are in Map C above.
