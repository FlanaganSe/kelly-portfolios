# Numerical engine specification

**Question.** What should this repository's portfolio mathematics compute, with which
algorithms, and where should that computation run?

**Decision it informs.** The numerical contract for the primitives, estimators and
inference underneath any allocation feature, and where the optimiser executes. **This is
the *how*; the [edge framework](portfolio-edge-research-framework.md) is the *whether*, and
it governs — nothing here licenses a claim that page does not support.**

**Conclusion.** Build in three layers: exact primitives with closed-form fixtures;
conditioning and inference that make overfitting visible; and only then optimisation. Two
findings decide the architecture. **No maintained, browser-ready convex QP solver exists in
the JavaScript or WebAssembly ecosystem** as of 2026-08-11 — no OSQP or Clarabel WASM build
is published to npm at all — so the optimisation core belongs server-side in Python.
**And conditioning is a prerequisite, not a refinement**: the practical browser QP requires
a positive-definite quadratic term, and a user-entered correlation matrix routinely is not
one.

**Every fixture here was recomputed independently of the source that states it**, in pure
Python with no numerical libraries, and reproduced exactly.

---

## Layer 1 — primitives

**Geometric versus arithmetic mean.** `g ≈ mu − sigma**2/2` is a second-order expansion,
exact only in continuous time or for log returns. Under a lognormal simple-return model the
exact growth rate is `g = e**m − 1` with
`m = ln((1 + mu)**2 / sqrt((1 + mu)**2 + sigma**2))`.

| `mu` | `sigma` | Approximation | Exact | Error |
| ---: | ---: | ---: | ---: | ---: |
| 0.08 | 0.15 | 0.068750 | 0.069732 | −0.00098 |
| 0.08 | 0.40 | 0.000000 | 0.012769 | −0.01277 |
| 0.10 | 0.60 | −0.080000 | −0.034315 | −0.04569 |

**The approximation overstates volatility drag as `sigma` grows and can wrongly predict
negative growth.** Kelly sizing runs directly on `g`, so this error propagates straight into
leverage. Use the exact form.

**Drawdown.** Maximum drawdown and time under water are one O(n) pass over the **equity
curve**, never over returns, and **a drawdown still open at the end must count**. Fixture:
`[100,110,105,95,120,90,130]` → MDD = −0.25, max time under water = 2. **Maximum drawdown is
not scale-free in sample length** — it deepens mechanically with `T`, so it must never be
compared across unequal samples.

**Tail risk.** Historical VaR needs an explicit, documented quantile-interpolation rule, and
expected shortfall with fewer than about ten observations in the tail is unestimable — **so
surface the effective tail count rather than printing a number.**

The Cornish–Fisher expansion has a failure mode that returns a plausible number rather than
an error: **it is a valid quantile transform only where it is monotone in `z`**, that is
where

```
dz_cf/dz = 1 + zS/3 + (3z**2 − 3)K/24 − (6z**2 − 5)S**2/36 > 0
```

Scanning `z` in [−4, 4] gives the admissible skew by excess kurtosis: |S| < 0.418 at K = 0,
0.834 at K = 1, 1.376 at K = 3, 1.921 at K = 6. **At `alpha = 0.05, S = −2.0, K = 1` the
formula returns −2.118056 and is non-monotone — the value is meaningless.** Evaluate the
derivative across the range actually queried and **refuse to return a Cornish–Fisher VaR
when it changes sign.** The published validity domain was not retrievable; **the bounds above
were derived here.**

---

## Layer 2 — conditioning and inference

**Sharpe ratio inference.** Under iid normality `SE = sqrt((1 + SR**2/2)/T)`. **Annualising
by `sqrt(q)` is wrong under autocorrelation**; the correction is `SR(q) = eta(q) SR` with
`eta(q) = q / sqrt(q + 2 sum_k (q − k) rho_k)`
([Lo 2002](https://doi.org/10.2469/faj.v58.n4.2453), verified via its verbatim restatement
in Getmansky, Lo and Makarov, because the original is paywalled). For AR(1) returns,
`sqrt(12)/eta − 1` is +9.62% at `rho = 0.1`, +32.48% at 0.3, **+63.30% at 0.5**, and
**−16.94% at −0.2**.

Three traps. `sqrt(q)` is an upper bound only under *positive* autocorrelation — **negative
`rho` makes `eta > sqrt(q)` and the naive figure understates.** The sum reaches `rho_{q−1}`,
estimated from very few pairs in short samples, so taper or truncate and disclose it. And
**never apply `eta` to a Sharpe already built from overlapping `q`-period returns.**

**Deflated Sharpe ratio.** The expected maximum of `N` independent zero-skill trials is
`(1 − gamma) Phi_inv(1 − 1/N) + gamma Phi_inv(1 − 1/(Ne))` with `gamma = 0.5772156649`,
giving 0.519755 (N = 2), 1.574598 (10), 2.276303 (50), 2.530603 (100), 3.255122 (1000).
Under the null the threshold is `sqrt(V[{SR_n}]) × E[max Z]`, where `V[{SR_n}]` is the
variance of Sharpe ratios **across trials, not the sampling variance of one Sharpe ratio.**
**That substitution is the most common implementation error in this formula.**

The effect is not cosmetic: with trial dispersion 0.5, `SR = 1.0`, `T = 120`, skew −0.5 and
kurtosis 6, deflated significance falls from **0.919122 at N = 10 to 0.040474 at N = 100 and
0.000018 at N = 1000.** A strategy "99.999% significant" against zero fails outright once a
hundred trials are counted.

**Correlated trials are where this is usually got wrong.** With `M` trials of which only `N`
are independent, interpolate on the average off-diagonal correlation. The paper's own
guardrails matter more than the interpolation: correlation captures linear dependence only;
**the trial correlation matrix is singular whenever `T < M`**, so an average computed from it
is itself overfit; and `rho_bar` is bounded below by `−1/(M − 1)`. **Report the `N` used —
the deflated Sharpe ratio is a monotone function of an assumption, not a measurement.** The
exact interpolation expression sits in a glyph our extraction dropped and is **unverified**;
the linear reading `N_hat = M(1 − rho_bar) + rho_bar` reproduces both endpoints but should be
confirmed against the typeset paper before it is relied on.

**Covariance conditioning.** The sample covariance matrix has rank at most `min(T − 1, N)`,
so it is exactly singular for `T <= N` and merely disastrous just above: **the smallest
eigenvalues are noise, and an inverse-covariance optimiser loads maximally on precisely those
directions.** Marchenko–Pastur bounds the noise spectrum,
`lambda_pm = sigma**2 (1 ± sqrt(N/T))**2` — (2.914214, 0.085786) at N = 50, T = 100;
(4.0, 0.0) at N = T = 500. **It applies to the correlation matrix, and `sigma**2` must be
refitted on the bulk rather than assumed to be 1**, because the market mode absorbs variance
— the original calibration used 0.85.

**A user-entered correlation matrix is frequently not a correlation matrix at all**, because
hand-specified pairwise values need not be jointly consistent. The fix is Higham's
alternating projections **with Dykstra's correction**
([Higham 2002](https://eprints.maths.manchester.ac.uk/232/1/paper.pdf), Alg. 3.3):

```
ΔS = 0; Y = A
repeat
    R  = Y − ΔS            // Dykstra correction — not optional
    X  = P_S(R)            // clip eigenvalues at zero
    ΔS = X − R
    Y  = P_U(X)            // set unit diagonal
```

Two verified fixtures. The inconsistent triple `rho_12 = rho_13 = 0.9, rho_23 = −0.9` has
eigenvalues (−0.8, 1.9, 1.9) and projects to (0.5, 0.5, −0.5) in 28 iterations. Higham's own
example converges in 35 iterations to off-diagonals 0.760690 and 0.157298, matching his
published 0.7607 and 0.1573.

**Dropping Dykstra's correction is not a harmless simplification**: the naive iteration
converges to a measurably suboptimal point — Frobenius distance 0.52791114 against
0.52779046. Note also that the result is positive *semi*-definite, so **add a small ridge and
renormalise the diagonal before any Cholesky factorisation.**

**Resampling.** An iid bootstrap destroys serial dependence and biases the sampling
distribution of every statistic that depends on it — long-horizon variance, drawdown,
autocorrelation-adjusted Sharpe — **generally too narrow.** Use the circular block bootstrap
or the stationary bootstrap. Choose the block length by the Politis–White rule **with the
Patton–Politis–White 2009 correction** — Nordman found an error in the underlying variance,
so `D_SB = 2 g**2(0)` and the asymptotic relative efficiency is `(2/3)**(2/3) ≈ 0.7631428`.
**The pre-2009 constant is still circulating in older ports, so verify any library you
compare against.** Note that `R_hat(k)` in the block-length formula is the auto*covariance*
while `rho_hat(k)` in the lag-selection step is the autocorrelation.

For model evaluation with overlapping labels, **purge** from the training set every
observation whose label interval intersects a test label interval, and **embargo** a further
span after the test set. **Never shuffle.** The primary text for this was not retrievable and
the mechanics above are **unverified against it**.

---

## Layer 3 — optimisation, and where it runs

**Prefer formulations that avoid estimating expected returns**, because that is where the
error concentrates. Long-only constrained minimum variance and equal risk contribution are
the defaults; both are convex, and **the no-short constraint doubles as implicit covariance
shrinkage.**

The engineering finding is blunt. Package metadata observed **2026-08-11**:

| Package | Latest | Published | Status |
| --- | --- | --- | --- |
| `ml-matrix` | 6.15.0 | 2026-08-05 | Maintained. **Best default for dense linear algebra** |
| `quadprog` | 2.0.0 | 2026-06-25 | Maintained Goldfarb–Idnani dual active set. Dense, small `N`, **requires a positive-definite quadratic term** |
| `mathjs` | 15.2.0 | 2026-04-07 | Maintained, but its own docs call `eigs` "not a modern, high-precision eigenvalue computation". **Do not use on ill-conditioned covariance matrices** |
| `numeric` | 1.2.6 | 2012-12-20 | Abandoned |
| `osqp` | 0.0.2 | 2021-12-28 | Effectively abandoned, pre-alpha version number |
| **Clarabel WASM** | — | — | **Does not exist on npm** |
| `glpk.js` | 5.0.0 | 2025-12-23 | Maintained, but LP/MIP only — **no QP** |
| `highs-addon` | 0.10.3 | 2025-08-07 | Maintained but a native Node binding, **not browser-usable** |
| `pyodide` | 314.0.3 | 2026-07-24 | Real NumPy and SciPy in the browser at the cost of a large download |

**So: `ml-matrix` for dense linear algebra, and the optimisation core server-side in Python**
once any of `N > 200`, conic or cardinality constraints, auditable numerics, or a genuine
convergence certificate is required. **For a research tool the reproducibility of the
numerics *is* the product.** Pyodide is the middle path if client-side computation later
becomes a requirement.

---

## Consequence for this repository

**Build in the order of the layers.** Each is independently testable and the fixtures here
need no market data, so **all of Layer 1 and most of Layer 2 can be tested before any data
contract exists.**

**No optimiser ships**, and the client-side one this specification argued against has been
deleted. Its defects are kept here as the *reasons* rather than as a description of code
that still exists, because they are exactly what this specification is meant to prevent: it
**normalised weights inside its finite-difference gradient while evaluating the objective on
unnormalised weights, so it differentiated a different function from the one it minimised**;
nothing validated that the user-supplied correlation matrix was positive semi-definite, so an
inconsistent matrix yielded a negative variance and a `NaN` risk; and **it was named for
Kelly while maximising a mean-variance utility at `gamma = 5`, which overstates leverage by a
factor of `gamma`.**

**What the client may carry** is closed-form arithmetic the research workspace has already
run and tested, as a port in `src/lib/` checked against fixtures that workspace generates
([decision 0007](../decisions/0007-application-may-render-research.md)). **Anything that
searches a weight space belongs in `research/` with a frozen specification and a ledger
entry.**

## Open questions

1. The exact trial-count interpolation for correlated trials in the deflated Sharpe ratio,
   and whether clustering or the linear form is the intended estimator.
2. The published Cornish–Fisher validity domain, against the bounds derived here.
3. Whether the purged/embargoed cross-validation mechanics above match the primary text.
4. Whether a Python optimisation endpoint or Pyodide better fits the intended deployment,
   which depends on a product decision about offline use that has not been taken.
</content>
