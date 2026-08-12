# Numerical engine specification

**Question.** What should this repository's portfolio mathematics actually compute,
with which algorithms, and where should that computation run?

**Decision informed.** This page fixes the numerical contract for the primitives,
estimators, and inference procedures underneath any allocation feature, and settles
where the optimiser executes. It is the *how*; the companion page on
[portfolio edge](portfolio-edge-research-framework.md) is the *whether*, and it
governs — nothing here licenses a claim that page does not support.

**Conclusion.** Build the engine in three layers: exact primitives with closed-form
fixtures; conditioning and inference that make overfitting visible; and only then
optimisation. Two findings decide the architecture. First, **no maintained,
browser-ready convex QP solver exists in the JavaScript or WebAssembly ecosystem as
of 2026-08-11** — no OSQP or Clarabel WASM build is published to npm at all — so the
optimisation core belongs server-side in Python, with the client doing display
arithmetic. Second, **conditioning is a prerequisite, not a refinement**: the
practical browser QP requires a positive-definite quadratic term, and a
user-entered correlation matrix routinely is not one.

Every fixture in this document was recomputed independently of the source that
states it, in pure Python with no numerical libraries, and reproduced exactly.

## Layer 1 — primitives

### Geometric versus arithmetic mean

\(g \approx \mu - \sigma^2/2\) is a second-order expansion, exact only in continuous
time or for log returns. Under a lognormal simple-return model the exact growth rate
is \(g=e^m-1\) with \(m=\ln\!\big((1+\mu)^2/\sqrt{(1+\mu)^2+\sigma^2}\big)\).

| \(\mu\) | \(\sigma\) | \(\mu-\sigma^2/2\) | Exact | Error |
| --- | --- | --- | --- | --- |
| 0.08 | 0.15 | 0.068750 | 0.069732 | −0.00098 |
| 0.08 | 0.40 | 0.000000 | 0.012769 | −0.01277 |
| 0.10 | 0.60 | −0.080000 | −0.034315 | −0.04569 |

The approximation overstates volatility drag as \(\sigma\) grows and can wrongly
predict negative growth. Kelly sizing runs directly on \(g\), so this error
propagates straight into leverage — use the exact form.

### Drawdown

Maximum drawdown and time under water are one O(n) pass over the **equity curve**,
never over returns:

```
peak = equity[0]; mdd = 0; run = 0; tuw = 0
for v in equity:
    if v >= peak: peak = v; tuw = max(tuw, run); run = 0
    else:         run += 1; mdd = min(mdd, v/peak - 1)
tuw = max(tuw, run)          // a drawdown still open at the end must count
```

Fixture: `[100,110,105,95,120,90,130]` → MDD = −0.25, max time under water = 2.
Maximum drawdown is not scale-free in sample length — it deepens mechanically with
\(T\), so it must never be compared across unequal sample lengths.

### Tail risk

Historical VaR needs an explicit, documented quantile-interpolation rule; expected
shortfall with fewer than about ten observations in the tail is unestimable, so
surface the effective tail count rather than printing a number. Gaussian forms are
\(\mathrm{VaR}_\alpha=-(\mu+\sigma z_\alpha)\) and
\(\mathrm{ES}_\alpha=-(\mu-\sigma\varphi(z_\alpha)/\alpha)\).

The Cornish–Fisher expansion (S = skewness, K = *excess* kurtosis) is

\[
z_{cf}=z+\frac{(z^2-1)S}{6}+\frac{(z^3-3z)K}{24}-\frac{(2z^3-5z)S^2}{36}.
\]

It has a failure mode that returns a plausible number rather than an error: the
expansion is a valid quantile transform only where it is **monotone** in \(z\), that
is where

\[
\frac{dz_{cf}}{dz}=1+\frac{zS}{3}+\frac{(3z^2-3)K}{24}-\frac{(6z^2-5)S^2}{36}>0 .
\]

Scanning \(z\in[-4,4]\) gives the admissible skew by kurtosis: |S| < 0.418 at K = 0,
0.834 at K = 1, 1.376 at K = 3, 1.921 at K = 6. At \(\alpha=0.05,\ S=-2.0,\ K=1\) the
formula returns −2.118056 and is **non-monotone** — the value is meaningless.
Evaluate the derivative across the range actually queried and refuse to return a
Cornish–Fisher VaR when it changes sign. The published validity domain
(Maillard, SSRN 1997178) was not retrievable; the bounds above were derived here.

## Layer 2 — conditioning and inference

### Sharpe ratio inference

Under i.i.d. normality \(\mathrm{SE}(\widehat{SR})=\sqrt{(1+SR^2/2)/T}\): 0.1369306394
at SR = 0.5, T = 60; 0.1118033989 at SR = 1.0, T = 120.

Annualising by \(\sqrt{q}\) is wrong under autocorrelation. The correction is
\(SR(q)=\eta(q)\,SR\) with

\[
\eta(q)=\frac{q}{\sqrt{q+2\sum_{k=1}^{q-1}(q-k)\rho_k}}
\]

([Lo 2002](https://doi.org/10.2469/faj.v58.n4.2453), verified via its verbatim
restatement in
[Getmansky, Lo, and Makarov 2004](https://doi.org/10.1016/j.jfineco.2004.04.001),
eqs. 79–81, because the original is paywalled with no open-access copy). For AR(1)
returns:

| \(\rho\) | \(\eta(12)\) | \(\sqrt{12}/\eta-1\) |
| --- | --- | --- |
| 0.0 | 3.464102 | 0.00% |
| 0.1 | 3.160111 | +9.62% |
| 0.2 | 2.878849 | +20.33% |
| 0.3 | 2.614806 | +32.48% |
| 0.5 | 2.121288 | **+63.30%** |
| −0.2 | 4.170848 | −16.94% |

Non-AR(1) \(\rho=[0.3,0.2,0.1,0,\dots]\) gives \(\eta(12)=2.429329\); \(q=3\) with
\(\rho=[0.5,0.25]\) gives 1.279204. Three traps: \(\sqrt{q}\) is an upper bound only
under *positive* autocorrelation, since negative \(\rho\) makes \(\eta>\sqrt q\) and
the naive figure understates; the sum reaches \(\rho_{q-1}\), which is estimated from
very few pairs in short samples, so taper or truncate and disclose it; and never
apply \(\eta\) to a Sharpe already built from overlapping \(q\)-period returns.

### Deflated Sharpe ratio

The expected maximum of \(N\) independent zero-skill trials is

\[
E[\max Z]=(1-\gamma)\Phi^{-1}\!\left(1-\tfrac1N\right)+\gamma\,\Phi^{-1}\!\left(1-\tfrac1{Ne}\right),
\qquad \gamma=0.5772156649,
\]

giving 0.519755 (N = 2), 1.574598 (10), 2.276303 (50), 2.530603 (100), 3.255122
(1000), 3.860665 (10000)
([Bailey and López de Prado 2014](https://ssrn.com/abstract=2460551)). Under the
null the threshold is \(\widehat{SR}^*=\sqrt{V[\{SR_n\}]}\cdot E[\max Z]\), where
\(V[\{SR_n\}]\) is the variance of Sharpe ratios **across trials**, not the sampling
variance of one Sharpe ratio. That substitution is the most common implementation
error in this formula.

The effect is not cosmetic. With trial dispersion 0.5, \(\widehat{SR}=1.0\),
\(T=120\), skew −0.5 and kurtosis 6, the deflated significance falls from 0.919122 at
N = 10 to 0.040474 at N = 100 and 0.000018 at N = 1000. A strategy that is
"99.999% significant" against zero fails outright once a hundred trials are counted.

Correlated trials are where this is usually got wrong. With \(M\) trials of which
only \(N\) are independent, compute the average off-diagonal correlation \(\bar\rho\)
of the trial matrix and interpolate between \(\hat N=M\) at \(\bar\rho\to0\) and
\(\hat N=1\) at \(\bar\rho\to1\). The paper's own guardrails matter more than the
interpolation: correlation captures linear dependence only; the trial correlation
matrix is **singular whenever \(T<M\)**, so an average correlation computed from it
is itself overfit and the dimension must be reduced first; and \(\bar\rho\) is bounded
below by \(-1/(M-1)\) by positive semi-definiteness. Report the \(N\) used — the
deflated Sharpe ratio is a monotone function of an assumption, not a measurement.
The exact interpolation expression sits in a glyph our extraction dropped and is
**unverified**; the linear reading \(\hat N=M(1-\bar\rho)+\bar\rho\) reproduces both
endpoints but should be confirmed against the typeset paper before it is relied on.

### Covariance conditioning

The sample covariance matrix has rank at most \(\min(T-1,N)\), so it is exactly
singular for \(T\le N\) and merely disastrous just above: the smallest eigenvalues
are noise, and an inverse-covariance optimiser loads maximally on precisely those
directions. Marchenko–Pastur bounds the noise spectrum,
\(\lambda_\pm=\sigma^2(1\pm\sqrt{N/T})^2\) — giving (2.914214, 0.085786) at N = 50,
T = 100; (1.732456, 0.467544) at N = 100, T = 1000; and (4.0, 0.0) at N = T = 500
([Laloux et al. 1999](https://arxiv.org/pdf/cond-mat/9810255)). It applies to the
**correlation** matrix, and \(\sigma^2\) must be refitted on the bulk rather than
assumed to be 1, because the market mode absorbs variance — the original calibration
used \(\sigma^2=0.85\).

A user-entered correlation matrix is frequently not a correlation matrix at all,
because hand-specified pairwise values need not be jointly consistent. The fix is
Higham's alternating projections **with Dykstra's correction**
([Higham 2002](https://eprints.maths.manchester.ac.uk/232/1/paper.pdf), Alg. 3.3):

```
ΔS = 0; Y = A
repeat
    R  = Y − ΔS            // Dykstra correction — not optional
    X  = P_S(R)            // clip eigenvalues at zero
    ΔS = X − R
    Y  = P_U(X)            // set unit diagonal
```

Two verified fixtures. The inconsistent triple \(\rho_{12}=\rho_{13}=0.9,\
\rho_{23}=-0.9\) has eigenvalues (−0.8, 1.9, 1.9) and projects to
\(\rho_{12}=\rho_{13}=0.5,\ \rho_{23}=-0.5\), eigenvalues (0, 1.5, 1.5), in 28
iterations. Higham's own example \([[1,1,0],[1,1,1],[0,1,1]]\), eigenvalues
\((1-\sqrt2,1,1+\sqrt2)\), converges in 35 iterations to off-diagonals 0.760690 and
0.157298 with eigenvalues (0, 0.84270189, 2.15729811), matching the paper's published
0.7607 and 0.1573.

Dropping Dykstra's correction is not a harmless simplification: the naive iteration
`Y ← P_U(P_S(Y))` converges to a **measurably suboptimal** point — Frobenius distance
0.52791114 against 0.52779046 on the second fixture. Note also that the result is
positive *semi*-definite, so add a small ridge and renormalise the diagonal before
any Cholesky factorisation.

### Resampling

An i.i.d. bootstrap destroys serial dependence and biases the sampling distribution
of every statistic that depends on it — long-horizon variance, drawdown,
autocorrelation-adjusted Sharpe — generally too narrow. Use the circular block
bootstrap (wrap the series, draw fixed-length blocks, so every observation is equally
likely) or the stationary bootstrap (geometric block lengths, strictly stationary
resample, at the cost of extra variance from the randomised length).

Choose the block length by the Politis–White rule **with the Patton–Politis–White
2009 correction**: Nordman found an error in the underlying stationary-bootstrap
variance, so \(D_{SB}=2g^2(0)\) and the asymptotic relative efficiency is
\((2/3)^{2/3}\approx0.7631428\)
([Patton, Politis, and White 2009](https://www.math.ucsd.edu/~politis/PAPER/SBblockCORRECTION.pdf);
[reference implementation](http://www.math.ucsd.edu/~politis/SOFT/ppwR.txt)). The
pre-2009 constant is still circulating in older ports, so verify any library you
compare against. Note that \(\hat R(k)\) in the block-length formula is the
auto*covariance* while \(\hat\rho(k)\) in the lag-selection step is the
autocorrelation.

For model evaluation with overlapping labels, purge from the training set every
observation whose label interval intersects a test label interval, and embargo a
further span after the test set to stop serial correlation leaking backwards. Never
shuffle. The primary text for this was not retrievable in session and the mechanics
above are **unverified against it**.

## Layer 3 — optimisation, and where it runs

Prefer formulations that avoid estimating expected returns, because that is where
the error concentrates — see the estimation section of the
[edge framework](portfolio-edge-research-framework.md). Long-only constrained
minimum variance and equal risk contribution are the defaults; both are convex, and
the no-short constraint doubles as implicit covariance shrinkage.

The engineering finding is blunt. Package metadata observed on **2026-08-11**:

| Package | Latest | Published | Status |
| --- | --- | --- | --- |
| `ml-matrix` | 6.15.0 | 2026-08-05 | Maintained. Symmetric eigendecomposition, Cholesky, LU, QR, SVD, pseudo-inverse. **Best default for dense linear algebra.** |
| `quadprog` | 2.0.0 | 2026-06-25 | Maintained Goldfarb–Idnani dual active set. Dense, small \(N\), **requires a positive-definite quadratic term**. |
| `mathjs` | 15.2.0 | 2026-04-07 | Maintained, but its own documentation calls `eigs` "not a modern, high-precision eigenvalue computation". Do not use it on ill-conditioned covariance matrices. |
| `numeric` | 1.2.6 | 2012-12-20 | Abandoned — nearly fourteen years stale. |
| `osqp` | 0.0.2 | 2021-12-28 | Effectively abandoned, pre-alpha version number. |
| Clarabel WASM | — | — | **Does not exist on npm.** |
| `eigen-js` | 0.2.2 | 2023-04-13 | Unmaintained. |
| `glpk.js` | 5.0.0 | 2025-12-23 | Maintained, but LP/MIP only — no QP. |
| `highs-addon` | 0.10.3 | 2025-08-07 | Maintained but a native Node binding, **not browser-usable**. |
| `pyodide` | 314.0.3 | 2026-07-24 | Maintained; real NumPy and SciPy in the browser at the cost of a large download. |

So: use `ml-matrix` for dense linear algebra, and run the optimisation core
server-side in Python once any of \(N>200\), conic or cardinality constraints,
auditable numerics, or a genuine convergence certificate is required. LAPACK's
symmetric eigensolvers and OSQP/Clarabel/ECOS are decades ahead of anything
available in JavaScript, and for a research tool the reproducibility of the numerics
*is* the product. Pyodide is the middle path if client-side computation later becomes
a requirement. This repository already deploys handlers from `functions/`, so a
Python optimisation endpoint with `ml-matrix` doing display arithmetic in the client
is the natural split.

## Consequence for this repository

Build in the order of the layers above; each is independently testable and the
fixtures on this page need no market data, so **all of Layer 1 and most of Layer 2
can be tested before any data contract exists**. Installing a test runner is the
first step, per the root `AGENTS.md` rule on optimisation math.

Two defects in the current code are worth naming because they are exactly what this
specification is meant to prevent.

`src/utils/calculateOptimizedPortfolio.ts` normalises weights inside its
finite-difference gradient (`normalize(wPlus)` at line 67) while the objective it
minimises is evaluated on unnormalised weights, so it differentiates a different
function from the one it optimises; convergence to the stated optimum is not
guaranteed. Separately, nothing validates that the user-supplied correlation matrix
is positive semi-definite, so an inconsistent matrix yields a negative variance and a
`NaN` risk — the Higham projection above is the fix, and the inconsistent-triple
fixture is the test. The file is also named for Kelly while maximising a
mean-variance utility with \(\gamma=5\); since Merton's solution is the
mean-variance one divided by \(\gamma\), presenting that output as Kelly overstates
leverage by a factor of \(\gamma\).

## Open questions

1. The exact trial-count interpolation for correlated trials in the deflated Sharpe
   ratio, and whether clustering or the linear form is the intended estimator.
2. The published Cornish–Fisher validity domain, against the bounds derived here.
3. Whether the purged/embargoed cross-validation mechanics above match the primary
   text.
4. Whether a Python optimisation endpoint or Pyodide better fits the intended
   deployment, which depends on the product decision about offline use.
