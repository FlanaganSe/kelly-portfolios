# Stacking: does a pile of 55% bets beat the market?

**Question.** The proposition under the whole proposed portfolio, in the investor's words:
*"if you stack a ton of strategies that are 55% likely to beat the market then you will
beat the market."* Under what conditions is that true, and does the candidate portfolio
meet them?

**Decision it informs.** Whether breadth is worth buying at the price the candidate pays
for it, and which of its eight holdings earn their place. Out of scope: whether any
premium is real ([factor persistence](factor-persistence.md)), what a wrapper's structure
is worth ([capital efficiency](capital-efficiency-and-breadth.md)), and what to hold
([the recommendation](portfolio-recommendation.md)).

**Status: `exploratory`.** For sections 1 to 4 and 6, no specification was frozen before
the numbers were seen and no experiment was registered. [Section 5](#5-how-many-candidates-a-long-only-optimiser-actually-holds)
is the exception: its weight-space search runs under
[Experiment 017](../../research/experiments/exp_017_longonly_ladder.yaml) with a frozen
grid and a ledger entry, and it reads no market data at all. Throughout, the arithmetic is
closed-form and tested; the correlations are measured on 422 months of committed data;
every expected return is an **input** carried across four scenarios, because this
repository cannot sign most of the premia involved.

---

## Conclusion

**The thesis is arithmetically correct and its premise is false on this portfolio.** More
55% bets do raise the odds — but by an amount governed by the sleeves' *effective* breadth,
which converges to `1/rho`, so the whole gain is bounded before the second sleeve is
bought. Stacking an unlimited number of 55% sleeves at the correlation this repository
measures between the candidate's own value tilts, **0.435**, reaches **0.576** and stops.
Not 0.9, not 1.

Six results, in the order they bind.

1. **`P = Phi(z_1 sqrt(k / (1 + (k-1) rho)))`, and the ceiling is `Phi(z_1 / sqrt(rho))`.**
   Correlation of *excess* returns, not sleeve count, is the whole quantity being bought.
2. **The candidate's eight tickers are five active positions worth `1'R^-1 1 = 3.71`
   effective bets.** Its own weights realise an information ratio of **0.230**, against
   **0.564** for DFIV held alone — so on the no-alpha reading the stack is *less* likely to
   beat the benchmark than one of its own components, which is dilution rather than
   diversification. **Charge DFIV's alpha and that comparison inverts**: DFIV alone becomes
   a losing bet at 0.398 and the stack's spread is what saves it. Both readings are in
   [§4](#4-the-candidates-true-breadth-and-the-joint-probability); neither is quotable
   without the other.
3. **Joint P(ahead of a same-split cheap-core benchmark) is 0.75–0.77 at 10 years,
   0.81–0.85 at 20, and 0.84–0.90 at 30** on the premium set most favourable to the
   candidate with no fund alpha charged. **That is not the primary reading.** Charging the
   one fitted alpha on this shelf that clears its own detection floor — DFIV's, at
   −3.80 pp/yr — takes the 30-year figure to **0.72**. Across every premium scenario the
   range is **0.40 to 0.91**, and the spread is larger than any construction change
   available.
4. **The construction change that survives the alpha charge is not the one this page first
   proposed.** Moving AVLV's 15% into **DFIV** raises the odds only if DFIV's measured
   alpha is ignored; charge it and the same move *lowers* them, 0.722 → 0.666. **That
   recommendation is withdrawn.** What survives all three alpha settings is moving the
   AVLV weight into **IDMO**, and the version this page recommends is the partial one —
   see [the recommendation](#the-construction-change-that-survives-its-own-worst-case).
5. **On a stated shelf of twelve candidates at that correlation, the best equal-weighted
   portfolio holds two and the exact long-only optimum holds three — and it does not
   improve past three however many further candidates are offered**
   ([§5](#5-how-many-candidates-a-long-only-optimiser-actually-holds), Experiment 017).
   The unconstrained optimum keeps rising, to 0.727 against long-only 0.463, and the whole
   difference is a short leg of seven positions. **Every edge in that ladder is an
   assumption, and the count depends on their dispersion**: give all eight candidates the
   same edge and the optimiser holds all eight.
6. **Geography is nearly free breadth; style is real breadth.** One factor spread across
   three regions is worth **1.35 to 1.55 of 3**; five factors inside one region are worth
   **5.52 of 5**. The candidate's 35% international allocation may be right for currency,
   valuation, home-bias or regret reasons — **it should not be defended as
   diversification**, because the measurement says a regional split of the same tilt buys
   about half a bet.

---

## 1. The arithmetic of stacking

Write `e` for the vector of sleeve edges over the benchmark, `w` for weights, `Sigma` for
the covariance of the sleeves' **excess** returns. Then

```text
IR = w'e / sqrt(w' Sigma w)          P(ahead after T years) = Phi(IR sqrt(T))
```

which is [the horizon module](expected-edge-decomposition.md#3-what-probability-is-actually-attainable)
with `e/s` renamed. For `k` sleeves of identical edge, identical tracking error and mutual
correlation `rho`,

```text
IR_k = IR_1 sqrt(k / (1 + (k-1) rho))        P_k = Phi(z_1 sqrt(k / (1 + (k-1) rho)))
```

and the breadth factor is the same `k / (1 + (k-1) rho)` that
[`overlay_growth.effective_breadth`](../../research/src/portfolio_edge/studies/overlay_growth.py)
already defines. **`z_1` is the only place the single-sleeve probability enters, and the
horizon cancels**, so the table below holds at every horizon at once.

| `rho` | k=1 | 2 | 3 | 5 | 10 | 25 | 100 | k → ∞ |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.0 | 0.550 | 0.571 | 0.586 | 0.611 | 0.654 | 0.735 | 0.896 | 1.000 |
| 0.1 | 0.550 | 0.567 | 0.579 | 0.594 | 0.613 | 0.633 | 0.648 | **0.654** |
| 0.2 | 0.550 | 0.564 | 0.573 | 0.583 | 0.594 | 0.603 | 0.609 | **0.611** |
| 0.3 | 0.550 | 0.562 | 0.568 | 0.575 | 0.582 | 0.587 | 0.590 | **0.591** |
| 0.4 | 0.550 | 0.560 | 0.564 | 0.569 | 0.573 | 0.577 | 0.578 | **0.579** |
| 0.5 | 0.550 | 0.558 | 0.561 | 0.564 | 0.567 | 0.569 | 0.570 | **0.571** |
| 0.6 | 0.550 | 0.556 | 0.558 | 0.561 | 0.562 | 0.564 | 0.564 | **0.564** |
| 0.7 | 0.550 | 0.554 | 0.556 | 0.557 | 0.558 | 0.559 | 0.560 | **0.560** |

**Where the intuition holds.** The `rho = 0` row is the investor's mental model and it is
right: with genuinely independent bets, breadth is linear in `k` and a hundred 55% sleeves
are 89.6% likely to be ahead. **Where it collapses:** at any positive correlation, breadth
converges to `1/rho` and so does the probability. At `rho = 0.4`, **five sleeves capture
two thirds of everything an infinite number of them could ever deliver, and ten capture
four fifths.** The twenty-fifth sleeve is worth a thousandth of a probability and the
hundredth is worth nothing at all.

Two further limits sit underneath the table and neither is a correlation.

**Independence is not enough either.** Even at `rho = 0` exactly, a hundred 55% sleeves
reach 0.896, not certainty. Inverting the `rho = 0` row gives the count directly: at
`rho = 0` the probability is `Phi(z_1 sqrt(k))`, so reaching a target `P` needs
`k = (z_P / z_1)**2` genuinely independent bets, with `z_1 = Phi^-1(0.55) = 0.12566`.

| Target probability of being ahead | `(z_P / z_1)**2` | Whole bets that clear it |
| ---: | ---: | ---: |
| 60% | 4.06 | 5 |
| 70% | 17.41 | 18 |
| 80% | 44.86 | 45 |
| 90% | **104.01** | **105** |
| 95% | **171.34** | **172** |
| 99% | **342.73** | **343** |

The 90% row is worth reading twice: **104 independent 55% bets reach 0.89997** and the
hundred-and-fifth is what clears the target, so "about a hundred" is the right size and the
exact integer depends on which side of the threshold is being asked for.

"Stack a ton and you will beat the market" is arithmetically true at roughly **170 to 340
truly uncorrelated bets**, which is a description of a market maker, not a portfolio of
eight ETFs — and the table above says those bets have to be uncorrelated, which the next
section says these are not.

**The edge is estimated, and that error never averages away.** Path noise accumulates as
`s**2 T` and washes out; an error in the *mean* accumulates as `tau**2 T**2` and does not.
Writing the cumulative relative log return as `N(eT, tau**2 T**2 + s**2 T)`,

```text
P(T) = Phi( e sqrt(T) / sqrt(tau**2 T + s**2) )     ->    Phi(e / tau)   as T -> inf
```

**`Phi(e/tau)` is a hard ceiling on any horizon**: the probability of being ahead cannot
exceed the probability that the edge is positive at all. Thirty years does not convert an
unsignable premium into a likely outcome; it converts it into a longer wait for the same
coin flip.

### Correlation, measured

The candidate's four long-only tilts are modelled month by month as their **measured
delivered loading vector** applied to their own region's French factors — the same
three-term chain [delivered loading](long-only-capture.md#what-this-does-to-premium--delivered-loading--cost)
prices, evaluated on the series instead of on the mean, with **no capture fraction anywhere
in it**. Trend is AQR's TSMOM, a vendor reconstruction standing in for RSST's trend leg.
RSST's own loading on that index has since been measured from its filings at +0.681
[+0.406, +0.955] over 31 months to 2026-04
([comparability](loading-comparability-and-wrapper-exposure.md)), so the substitution runs
the trend leg roughly a third hot — an approximation with a measured size, on an interval
too wide to correct for precisely.

Correlation of those modelled excess returns, 422 months, 1990-11…2025-12. The standard
error on a single correlation near zero is 0.049, so these are resolved to roughly two
decimal places even though the premia behind them are not signable at all — the asymmetry
[the evidence base](evidence-base.md) §1 records.

| | AVLV | DFIV | IDMO | AVES | trend |
| --- | ---: | ---: | ---: | ---: | ---: |
| **AVLV** US large value | 1.000 | 0.572 | −0.232 | 0.320 | −0.121 |
| **DFIV** dev ex-US value | 0.572 | 1.000 | −0.228 | 0.414 | −0.055 |
| **IDMO** dev ex-US momentum | −0.232 | −0.228 | 1.000 | −0.102 | 0.445 |
| **AVES** emerging value | 0.320 | 0.414 | −0.102 | 1.000 | 0.019 |
| **trend** | −0.121 | −0.055 | 0.445 | 0.019 | 1.000 |

| Set | `1'R^-1 1` | of |
| --- | ---: | ---: |
| three value tilts, US + developed ex-US + emerging | **1.62** | 3 |
| four long-only tilts | **3.40** | 4 |
| four tilts plus the trend overlay | **3.71** | 5 |
| every French factor in every region plus trend | **10.23** | 16 |
| HML across three regions | 1.55 | 3 |
| UMD across three regions | 1.35 | 3 |
| five factors within one region (US) | 5.52 | 5 |

**The candidate's three value tilts are worth 1.62 independent tilts**, and HML itself
across three regions reads 1.55 here beside the 1.49
[Experiment 005](factor-persistence.md) measured on a different era of the same file.
finding a ticker count cannot reach: *geography is nearly free breadth* — spreading one
factor over three regions buys about half a bet — while *style is real breadth*, because
five factors inside one region are worth 5.5, more than their own count, since value and
momentum are negatively correlated.

**`1'R^-1 1` above `N` is not an error.** It is what a negative correlation does, and
[`factor_breadth.exact_effective_breadth`](../../research/src/portfolio_edge/studies/factor_breadth.py)
computes it without a cap. It is also an **upper bound on anything realisable**: it prices
the sleeves at optimal weights and equal edges, which the candidate does not have.

### Funding: the thesis is a statement about overlays

Under **substitution** — a fixed capital base, weights summing to at most one — portfolio
edge is a weighted **average** of sleeve edges, so it is bounded above by the single best
sleeve. Adding a sleeve raises effective breadth and lowers mean edge in the same motion.
Under a **financed overlay** — notional weights, unconstrained — portfolio edge is a
**sum**, and "stack a ton" is exactly the right instruction.

On the candidate's own tilts, at the premia most favourable to it and 35% of capital
available to tilt:

| | Portfolio edge |
| --- | ---: |
| substitution, all 35% in the single best tilt | **117.3 bp** |
| a financed overlay, 35% of notional in each of the four | **297.4 bp** |
| the candidate's four tilts as actually weighted | **62.4 bp** |

**The candidate is about 93% substitution.** Only the RSST line is financed. So the
investor is applying overlay intuition to a portfolio whose arithmetic is an average.
[Capital efficiency](capital-efficiency-and-breadth.md#funding-algebra) owns the funding
identity itself and measures the gap at `a_p − sigma_p**2 = 2.44 pp/yr`; this page adds
only that the gap changes the *shape* of the stacking arithmetic and not merely its size.

**Dilution does not change the odds, only the prize.** Scaling every weight by a constant
moves edge and tracking error together, so `IR` and every probability are unchanged. A
5% tilt and a 20% tilt are equally likely to be ahead; one is four times as large. That is
why the candidate's low probability is not caused by small weights — it is caused by
*relative* weights, which is a different failure.

---

## 2. Is `p` even 55%?

Per dollar of sleeve, `edge = sum_k (h_fund,k − h_incumbent,k) * premium_k − cost`, with
loadings from the typed shelf and costs from the funds' own filings. **AVES's fee is now
measured** — 36 bp gross-equal-to-net with no waiver, against IEMG's 9 bp contractually
capped to 2030-12-31, so the fee delta is 27 bp; the turnover half is still assumed, at
AVLV's 7%/yr against an implicit zero for IEMG, which is unfavourable to AVES on both
sides. The change costs AVES 9 bp of sleeve edge and moves no verdict. Four premium
scenarios, none of them a forecast: **own-panel** is each region's own post-publication
figure, **pooled** applies the three-region pooled HML and UMD everywhere, **half** halves
the own-panel figures, **null** sets every premium to zero.

| Sleeve | own-panel | pooled | half | null | cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| AVLV, delivered HML +0.297 | +0.32 | +1.26 | +0.07 | −0.19 | 0.188 |
| DFIV, delivered HML +0.723 | **+3.35** | +3.16 | +1.54 | −0.27 | 0.274 |
| IDMO, delivered UMD +0.534 | +3.33 | +2.91 | +0.70 | −1.94 | **1.937** |
| AVES, delivered HML +0.237 | +1.41 | +0.74 | +0.51 | −0.39 | 0.389 |

Tracking error per dollar of sleeve, and the sleeve's own probability of being ahead:

| Sleeve | model TE | measured TE | factor share | `IR` alone | P(30y), edge known | P(edge > 0) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AVLV | 3.61 | **6.77** | 0.285 | 0.047 | 0.602 | **0.671** |
| DFIV | 5.40 | **5.95** | 0.824 | 0.564 | 0.999 | 0.994 |
| IDMO | 6.21 | assumed 8.34 | assumed | 0.399 | 0.985 | 0.947 |
| AVES | 1.94 | assumed 2.60 | assumed | 0.541 | 0.999 | 1.000 |
| trend | 12.41 | — | — | 0.081 | 0.673 | 0.937 |

**The answer to "is p 55%?" is that it is not one number and 55 is not the interesting
part of it.** Read the two rightmost columns together.

- **AVLV is the sleeve the question was really about.** Its 30-year probability is 0.60
  with the edge treated as known and its edge is positive with probability **0.671** — so
  the honest reading is nearer *p = 0.60 conditional on a premium that is itself a
  two-in-three proposition*. [The recommendation's](portfolio-recommendation.md) existing
  finding — that a modest tilt's expected benefit "can remain indistinguishable from noise
  over an investing lifetime" — survives this page intact.
  On the US-only premium its edge after cost is **+32 bp per dollar of sleeve**, from
  +51 bp gross less 19 bp of fee and turnover.
- **DFIV and AVES read far above 0.55**, because their delivered loadings are large and
  their regions' premia are the two this repository can sign. Those readings are entirely
  hostage to premia measured on 384 months, and to alphas discussed below.
- **The 0.285 factor share is a warning about all of them.** AVLV's delivered exposure
  explains **28.5%** of its measured tracking variance against VTI. The other seven
  tenths is fund residual: real risk, no priced expectation. DFIV's explains 0.824.
  The two disagree by a factor of three, so the tracking errors of IDMO and AVES — which
  this repository has never measured — are carried at the low, mean and high reading. That
  substitution is an assumption, and it is the weakest input on this page.

**The tracking error the investor is accepting is about 400 bp a year** against a
same-split cheap-core benchmark, of which **372 bp is the trend overlay** and 102 bp
the AVLV line. For scale, the thirty-year detection floor at 400 bp of tracking error is
**93 bp/yr at 90% confidence**, against a central edge of 92 bp. **The portfolio is
designed so that thirty years of holding it cannot establish whether it worked.**

---

## 3. What makes a sleeve worth adding

Not standalone `p`. The criterion is the candidate's edge net of what the sleeves already
held supply, over the part of its tracking error they do not already carry:

```text
beta_k  = rho_kp s_k / s_p      alpha_k = e_k − beta_k e_p     omega_k = s_k sqrt(1 − rho_kp**2)
IR_new**2 = IR_old**2 + (alpha_k / omega_k)**2
```

The appraisal ratio `alpha_k / omega_k` is exactly what an optimiser would have found —
[the test suite](../../research/tests/unit/test_studies_stacking.py) checks it against
`sqrt(e' Sigma^-1 e)` computed by an independent matrix solve. Two consequences, and both
are the investor's own objection made exact:

- **A sleeve with `p < 0.5` standalone raises portfolio `p`** whenever `beta_k` is negative
  enough that `alpha_k > 0`.
- **A sleeve with `p = 0.55` standalone adds nothing** when `alpha_k = 0`, however good it
  looks alone.

Each sleeve against the rest of the candidate, own-panel premia, trend at +1.0 pp/yr:

| Sleeve | weight | edge | `IR` alone | `beta` | `alpha` | residual TE | appraisal | conditioning |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AVLV | 0.15 | +0.32 | 0.047 | −0.043 | +0.36 | 6.77 | **0.053** | +0.006 |
| DFIV | 0.10 | +3.35 | 0.564 | +0.026 | +3.34 | 5.95 | **0.561** | −0.002 |
| IDMO | 0.05 | +3.33 | 0.399 | +0.580 | +2.89 | 8.03 | **0.360** | −0.039 |
| AVES | 0.05 | +1.41 | 0.541 | +0.053 | +1.36 | 2.59 | **0.526** | −0.016 |
| trend | 0.30 | +1.00 | 0.081 | +0.305 | +0.81 | 12.41 | **0.065** | −0.015 |

**Read the `conditioning` column first, because it overturns the framing.** It is
`appraisal − standalone IR`, and it is **exactly zero when a sleeve is uncorrelated with
everything else held**. In this portfolio it is +0.006, −0.002, −0.039, −0.016 and −0.015 —
small, and negative for four sleeves of five. **The candidate's sleeves are close enough to
mutually independent that the marginal verdict and the standalone verdict nearly coincide,
and no holding here is either rescued or condemned by the company it keeps.**

That matters because it is the investor's own question answered in the negative *for this
portfolio*. "Works in isolation, fails in a portfolio" is real arithmetic — the two worked
examples below show it — but **it is not what is happening in this construction**. What is
happening is simpler and worse: the standalone edges are small and premium-dependent, and
stacking them does not fix that.

| Sleeve | standalone `IR` | appraisal | conditioning | reading |
| --- | ---: | ---: | ---: | --- |
| AVLV | 0.047 | 0.053 | **+0.006** | the portfolio helps it, by nothing |
| DFIV | 0.564 | 0.561 | −0.002 | no effect either way |
| IDMO | 0.399 | 0.360 | **−0.039** | the largest effect here, and it is a *penalty* |
| AVES | 0.541 | 0.526 | −0.016 | slight penalty |
| trend | 0.081 | 0.065 | −0.015 | slight penalty |

**The correction this makes to an earlier reading of IDMO.** IDMO *does* earn its place —
its appraisal ratio is 0.360, third-largest — **but not on breadth grounds**, and this page
said otherwise before the column above was computed. Its conditioning term is the most
negative in the portfolio, because it is **+0.331 correlated with the trend overlay** that
occupies 30% of capital, and that overlap costs it more than its −0.092 and −0.154 against
the two value tilts earn back. **IDMO earns its place on its edge**: +3.33 pp/yr per dollar
of sleeve *after* charging the 1.94 pp/yr its 105%/yr turnover costs at `k = 1.7`, on the
one momentum premium the repository can sign on its own panel (developed ex-US UMD +8.35
against a 5.21 floor, Holm 0.003). Dropping it takes the 30-year probability from 0.722 to
0.672 under the primary reading. Decompose that: the stack's information ratio falls by
0.039, of which the negative correlation gives back only **0.003** — holding the tracking
error fixed at 400 bp instead of letting it fall to 387 changes the result by that much.
**Roughly nine tenths of what IDMO contributes is edge, not breadth.**

**The worked example in the other direction: AVLV, and the reconciliation it forces.**
Its appraisal ratio is **0.053** — fifteen percent of the portfolio, 102 bp of tracking
error, and six thousandths of an information ratio. But [the recommendation](portfolio-recommendation.md)
prices US large value at 20% as **+24.4 bp against 135 bp of tracking error**, and the
client suggests *raising* AVLV to that weight. Both figures are correct and they are not
in conflict; the reconciliation names which instrument measures what.

| Reading | AVLV standalone edge | standalone `IR` | appraisal inside the candidate |
| --- | ---: | ---: | ---: |
| pooled three-region HML, +4.74 | +1.26 pp/yr | 0.186 | **0.191** |
| US-only post-publication HML, +1.57 | +0.32 pp/yr | 0.047 | **0.053** |

This page reproduces the published line exactly — 24.4 bp of portfolio edge against 135 bp
of tracking error at a 20% weight, standalone `IR` **0.180** — from the same three-term
chain. **The gap is the premium, not the portfolio.** The conditioning channel is
`+0.006` on *either* premium; the premium channel is a factor of **4.0**. So:

- **the published line is a standalone instrument evaluated on the pooled premium**, which
  is the reading [the recommendation](portfolio-recommendation.md) adopts because the
  US-only premium is not signable;
- **this page's 0.053 is the same instrument evaluated on the US-only premium**, and
  conditions on the rest of the portfolio to almost no effect.

**Which should govern?** Neither is a portfolio effect, so the choice is the premium
choice and nothing else — exactly what the client's own caveat on this line already says:
*"that single choice, and not the fund, decides the sign."* What this page adds is that
**no amount of portfolio context rescues or damns the AVLV line**; anyone who wants to
argue for or against it must argue about the US value premium.

**The trend overlay is the third case, and it is the one this framework mis-scores.** Its
appraisal ratio against an equity benchmark is 0.065, near AVLV's, because a probability
calculation charges its entire 12.4 pp/yr volatility as tracking error and credits it with
one assumed pp/yr of edge. **That is the wrong comparator and the charter says so**:
market-neutral candidates compare with cash plus a stated premium, not with equity. What
trend scores against the comparator it is actually held for is already frozen elsewhere in
this repository and is not re-derived here:

| Result | Construction | Comparator | Growth |
| --- | --- | --- | ---: |
| [Experiment 004](trend-marginal-value.md) | 15% sleeve, 60/40 base, 432 mo | **risk-matched cash** | **+1.312 pp/yr**, 95% `[+0.759, +1.916]` |
| the same, post-publication | 168 mo | risk-matched cash | +0.883, `[−0.175, +2.165]`, fails Holm |
| [Experiment 010b](marginal-sleeve-value.md) | 10% sleeve, global equity core | pro-rata funding | +0.258 against a 0.30 threshold |

**Neither is a figure at 30% of notional and this study does not supply one.**

### The sizing result that needs no benchmark at all

An overlay's case is geometric, not probabilistic, and the geometric term is measured here.
Over 426 months, 1990-07…2025-12, the 65/25/10 equity blend runs **14.84 pp/yr** of
volatility at a **−0.183** correlation to AQR's TSMOM at **12.41 pp/yr**. A financed
overlay changes portfolio variance by **−5.2, −7.3, −6.2 and +5.4 pp²/yr at 10%, 20%, 30%
and 50% of notional**, worth **+0.026, +0.036, +0.031 and −0.027 pp/yr** of growth. Hence:

> **`w* = −rho × sigma_equity / sigma_trend = 21.6%`. Portfolio variance is minimised at
> 21.6% of trend notional, and the candidate holds 30%.** Three measured numbers, no
> premium, no forecast, no benchmark.

**Its sensitivity, stated because the point estimate alone would overclaim.** The standard
error on `rho` is `1/sqrt(426) = 0.048`, so the 95% interval on `rho` is
`[−0.277, −0.088]` and `w*` moves with it:

| `rho` | `w*` | |
| ---: | ---: | --- |
| −0.277 (−1.96 SE) | **32.8%** | **the candidate's 30% sits inside this bound** |
| −0.183 (point) | **21.6%** | |
| −0.170 ([Experiment 004](trend-marginal-value.md), 60/40 base, 432 mo) | 20.1% | an independent instrument agreeing |
| −0.088 (+1.96 SE) | 10.3% | |
| −0.590 (inside equity drawdowns) | 69.7% | 53 months, ~4.4 effective observations |
| 0.000 | 0.0% | any notional adds variance |

**Read it honestly.** 30% is *not* outside what this instrument can support: it sits inside
the upper end of `rho`'s own interval. What the instrument does say is that **30% is past
the centre of the admissible range rather than inside it**, and that under the central
estimate the marginal unit of trend at 30% is adding variance rather than removing it. The
crisis-conditional row points the other way entirely and is the weakest evidence on the
page.

Note how much smaller the whole credit is than [the pro-rata credit](marginal-sleeve-value.md#identity)
of `w sigma_p**2 (1−beta)`, about +0.22 pp/yr at a 10% weight: a substitution sells the
base and removes its variance, an overlay keeps the variance *and* the return. **That
difference is the funding-rule gap seen from the variance side.**

---

## 4. The candidate's true breadth, and the joint probability

**Eight tickers. Three of them — VTI, VEA, IEMG — carry no active position at all. Five
active sleeves. `1'R^-1 1 = 3.71` effective independent bets.**

Adding the funds' idiosyncratic residual back as an uncorrelated diagonal term raises the
figure to 4.06, and **that rise is not breadth**: residual carries no edge, so it lowers
every off-diagonal correlation while adding nothing to the numerator. Effective breadth
must always be read beside a realised information ratio.

**And the realised information ratio is where the weighting shows.** On the no-alpha
reading the stack achieves `IR = 0.230` against **0.564 for DFIV held alone** — the stack
is beaten by one of its own components, which is dilution. **Charge DFIV's alpha and that
inverts**: DFIV alone becomes `IR = −0.075`, a losing bet with a 30-year probability of
**0.398**, and the stack's spread is the only thing keeping it above water. The two
readings disagree about everything except this: **the candidate's weights are not the
weights its own evidence implies, in either direction.**

### The primary reading charges DFIV's alpha

The rule is stated before the numbers: **charge a fitted alpha when its own point estimate
exceeds its own detection floor; leave it at zero otherwise.** Exactly one qualifies.

| Fund | alpha net of pedestal | detection floor | charged under `resolved` |
| --- | ---: | ---: | --- |
| AVLV | −0.37 | 5.28 | no |
| **DFIV** | **−3.80** | **3.52** | **yes** |
| IDMO | +0.42 | 5.34 | no |
| AVES | −1.66 | 4.48 | no |

**Name the rule's bias: it charges the fund we can measure and forgives the ones we
cannot.** A short history and a wide floor buy a free pass. So every construction below is
scored under all three settings — `none`, `resolved` (primary) and `all` — and **a change
is called robust only if it beats the candidate under all three.**

Sleeve edge, pp/yr per dollar of sleeve, own-panel premia:

| Sleeve | `none` | `resolved` | `all` |
| --- | ---: | ---: | ---: |
| AVLV | +0.318 | +0.318 | −0.052 |
| DFIV | +3.352 | **−0.448** | **−0.448** |
| IDMO | +3.329 | +3.329 | +3.749 |
| AVES | +1.408 | +1.408 | −0.252 |
| trend | +1.000 | +1.000 | +1.000 |

### One change at a time

Own-panel premia, trend net excess +1.0 pp/yr, 30-year probability with the premia
estimated rather than known. `edge`, `TE`, `IR` and `bets` are the primary (`resolved`)
reading.

| Construction | edge bp | TE bp | `IR` | bets | `none` | **`resolved`** | `all` | robust |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| **the candidate** | 54.0 | 400 | 0.135 | 4.06 | 0.842 | **0.722** | 0.677 | — |
| AVLV 15 → DFIV | 42.5 | 408 | 0.104 | 3.42 | 0.918 | **0.666** | 0.643 | **no** |
| AVLV 15 → AVES | 70.3 | 395 | 0.178 | 3.42 | 0.893 | 0.790 | 0.674 | no |
| **AVLV 15 → IDMO** | 99.1 | 454 | 0.218 | 3.42 | 0.889 | **0.811** | 0.811 | **yes** |
| **AVLV 15 → IDMO 10, core 5** | 82.5 | 430 | 0.192 | 3.42 | 0.881 | **0.790** | 0.785 | **yes** |
| AVLV 15 split IDMO/AVES | 84.7 | 420 | 0.202 | 3.42 | 0.893 | 0.804 | 0.758 | yes |
| **trend 30 → 22, AVLV 15 → IDMO 10** | 74.5 | **336** | **0.222** | 3.42 | 0.905 | **0.807** | 0.800 | **yes** |
| AVLV 15 split DFIV/AVES | 56.4 | 399 | 0.141 | 3.42 | 0.908 | 0.729 | 0.658 | no |
| AVLV 15 → cheap core | 49.2 | 390 | 0.126 | 3.42 | 0.850 | 0.721 | 0.695 | no |
| drop DFIV, hold VEA | 58.5 | 395 | 0.148 | 3.58 | 0.758 | 0.758 | 0.712 | no |
| drop IDMO | 37.3 | 387 | 0.096 | 3.22 | 0.815 | 0.672 | 0.610 | no |
| drop AVES | 46.9 | 399 | 0.118 | 3.57 | 0.825 | 0.697 | 0.684 | no |
| trend 30 → 22 alone | 46.0 | 309 | 0.149 | 4.06 | 0.867 | 0.728 | 0.675 | no |
| trend 30 → 22 and AVLV 15 → core | 41.2 | 293 | 0.141 | 3.42 | 0.883 | 0.732 | 0.701 | yes |
| **drop the trend overlay** | 24.0 | **135** | 0.177 | 3.55 | *0.922* | 0.709 | 0.610 | no |
| priced weights (AVLV 20, DFIV 8) | 56.5 | 407 | 0.139 | 4.06 | 0.824 | 0.727 | 0.677 | no |
| tilts only: DFIV 20, AVLV 10, AVES 10 | 8.3 | 161 | 0.052 | 2.07 | *0.963* | 0.570 | 0.400 | no |
| DFIV alone at 10%, nothing else | −4.5 | 59 | −0.075 | 1.00 | *0.974* | **0.398** | 0.398 | no |

**The retraction, in one row.** `AVLV 15 → DFIV` was this page's first recommendation. It
wins under `none` (0.918) and **loses under the primary reading (0.666 against the
candidate's 0.722)**. Concentrating capital into the one fund on the shelf whose negative
alpha is statistically resolved is the opposite of robust. **Withdrawn.**

**Do not quote the italicised `none` figures.** The three largest — 0.922, 0.963, 0.974 —
all belong to constructions that shed tracking error rather than gain edge, and all three
collapse the moment DFIV's alpha is charged. `drop the trend overlay` is the worst offender
and it is a benchmark artefact: see [the sizing result](#the-sizing-result-that-needs-no-benchmark-at-all)
for what trend is actually scored against.

**The honest joint probability, with its interval.** Across the four premium scenarios,
both ends of the premium-error bracket, and all three alpha settings:

| | 10 years | 20 years | 30 years |
| --- | ---: | ---: | ---: |
| own-panel premia, trend +1.0, no alpha, edge known | 0.766 | 0.848 | 0.896 |
| the same with premium error carried | 0.747–0.761 | 0.809–0.836 | 0.842–0.880 |
| **own-panel, DFIV's alpha charged (primary)** | — | — | **0.722** |
| own-panel, every alpha charged | — | — | 0.677 |
| pooled premia, trend +1.0, no alpha | 0.782 | 0.865 | 0.912 |
| half the own-panel premia, trend +1.0, no alpha | 0.661 | 0.721 | 0.763 |
| every premium zero, trend still earning +1.0 | 0.540 | 0.557 | 0.570 |
| every premium zero, trend +0.0 | 0.446 | 0.424 | 0.407 |

**Quote the range, never the point.** The 30-year figure runs from **0.41** to **0.91**,
with **0.72** as the primary reading. The spread is not sampling noise: it is four beliefs
about premia this repository cannot choose between plus one alpha it can measure, and it
is larger than every construction change in the table above.

**The alpha is the largest single risk and it is now the primary case, not a sensitivity.**
DFIV's −3.80 pp/yr net of the developed-ex-US pedestal against a 3.52 pp/yr floor is the
only fund alpha on this shelf that clears its own floor, and it is one of four ex-US
large-value funds reading −2.2 to −4.1 for a reason nobody here understands. **Under it,
the strongest-looking sleeve in the portfolio is a losing bet held alone.**

### Which sleeves earn their place

Under the primary reading — own-panel premia, DFIV's alpha charged, trend at +1.0 pp/yr:

| Sleeve | Verdict | Why |
| --- | --- | --- |
| **IDMO** 5% | **earns it, on edge** | Appraisal 0.360 on the one momentum premium signable on its own panel (+8.35 against a 5.21 floor, Holm 0.003), *after* charging the 1.94 pp/yr its 105%/yr turnover costs. Its breadth contribution is **negative** (−0.039), because it is +0.331 correlated with the trend overlay |
| **AVES** 5% | **earns it, unresolved on evidence** | Appraisal 0.526 even after the newly measured 27 bp fee delta. But its loading is 51 months old, reads −0.074 on the US panel, its turnover is unread, and its status is `unresolved` |
| **DFIV** 10% | **does not earn it under the primary reading** | Appraisal 0.561 with no alpha charged and an edge of **−0.45 pp/yr** with it charged. This is the one holding whose verdict the alpha decides outright |
| **AVLV** 15% | **decided by the premium, not the portfolio** | Appraisal 0.053 on the US-only premium, 0.191 on the pooled. Conditioning moves it by 0.006 either way |
| **trend via RSST** 30% | **not scorable here; past its variance minimum** | 372 of the portfolio's 400 bp of tracking error against an equity benchmark it was never meant to beat. Its own comparators are [Experiments 004 and 010b](#3-what-makes-a-sleeve-worth-adding). Variance minimum 21.6% of notional against 30% held |
| **VTI, VEA, IEMG** 35% | **the benchmark** | No active position. They are what the tilts are measured against |

### The construction change that survives its own worst case

**Move the AVLV weight to IDMO, and move only part of it: `AVLV 15 → IDMO 10, cheap core
5`.** It is robust — 0.881 / **0.790** / 0.785 against the candidate's 0.842 / 0.722 /
0.677 — and it is the version of the winning change that does not concentrate. **Paired
with taking the trend overlay to its variance minimum it is better still and carries less
risk than the candidate on every axis measured here**: `trend 30 → 22, AVLV 15 → IDMO 10`
scores 0.905 / **0.807** / 0.800 at `IR` **0.222** and **336 bp** of tracking error against
the candidate's 400.

Three things that change must carry with it, none of them optional.

1. **It contradicts the repository's own product audit, which excludes IDMO by name.** That
   exclusion is a *promotion* verdict resting on the pooled momentum detection floor of
   4.98 pp/yr, the 105%/yr turnover, and a −0.394 CMA loading on a closed factor. All three
   are charged in the arithmetic above and the sleeve still clears, on the **developed
   ex-US own-panel** premium rather than the pooled one. **Marginal contribution and
   promotion status are different questions**; this page answers the first and does not
   overturn the second.
2. **The tax charge is not made anywhere above, and it points the other way.** Deferral
   plus the §1014 step-up is worth a horizon-free **1.62 pp/yr** in a taxable account
   ([edge decomposition](expected-edge-decomposition.md) §1) and is a hurdle any
   turnover-bearing sleeve must clear. As an upper bound — assuming the sleeve forfeits the
   whole benefit, which a fund with in-kind creation and redemption does not — that is
   **8, 16, 24 and 32 bp of portfolio return at 5%, 10%, 15% and 20% of capital in IDMO.**
   At a 15% or 20% weight it is the same order as the edge the swap buys. **This is the
   reason the recommendation is the partial move and not the whole one, and in a fully
   taxable account it may cancel even that.**
3. **The 15% does not go to DFIV, and it should not go to AVES either.** DFIV fails the
   primary reading outright. AVES is *nearly* as good on appraisal — 0.526 against DFIV's
   0.561 before any alpha — but it fails robustness by a hair under `all` (0.674 against
   0.677), its 36 bp fee against IEMG's 9 bp capped to 2030-12-31 is the more durable of
   the two commitments and it runs against AVES, and its status is `unresolved` on window
   length. **`AVLV 15 split IDMO/AVES` is robust** (0.893 / 0.804 / 0.758) and is the
   defensible compromise for a reader who wants the emerging weight.
4. **It raises the portfolio's exposure to a crash that is known to be correlated.** All
   three regions of momentum [lost their worst calendar year in 2009 together](factor-persistence.md#do-the-regions-crash-together-yes-and-it-is-the-finding),
   and IDMO is +0.331 correlated with the trend overlay, which is itself a momentum
   strategy in another asset class. In the worst decile of US equity months that pairing
   reads +0.64 and the five-sleeve count falls to 2.87
   ([§6](#6-crisis-conditional-breadth-measured)).

### What the international allocation is and is not

`1'R^-1 1` says one factor across three regions is worth **1.35 to 1.55 of 3**, while five
factors inside one region are worth **5.52 of 5**. **Geography is nearly free breadth;
style is real breadth.** The candidate's 35% international weight may be right on currency
exposure, relative valuation, home-bias correction or plain regret — none of which this
page measures, and all of which are legitimate. **It should not be defended as
diversification.** Splitting one value tilt across the US, developed ex-US and emerging
buys about half an extra independent bet; adding a second *style* to one region buys more
than a whole one.


## 5. How many candidates a long-only optimiser actually holds

[Experiment 017](../../research/experiments/exp_017_longonly_ladder.yaml), `exploratory`,
run artifact
[`946844e6`](../../research/artifacts/946844e68ba4455a9975c89baeaba8e9/summary.md).

Sections 1 to 4 price a stack whose weights are given. This section asks what an optimiser
does with a *shelf*, because that is the form the thesis is usually argued in — offer me
more candidates and I will be better off. **Every number in this section is computed on a
stated ladder of assumed edges. It reads no market data and estimates no premium**, so what
it establishes is a property of that ladder, not of markets. The ladder is frozen in the
specification and reproduced here in full: twelve candidates at **3.0, 2.4, 1.9, 1.5, 1.2,
0.9, 0.7, 0.5, 0.35, 0.2, 0.1 and 0.0 pp/yr gross**, each charged **40 bp**, each with
**6% tracking error**, all pairwise correlated at the **0.435 measured in §1** — which is
this portfolio's number and not a market constant.

Three weighting rules, one shelf.

| Candidates offered | Mean net edge | Available bets | Equal-weight IR | Long-only IR | Unconstrained IR | Transfer coefficient | Held long-only |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2.60 | 1.00 | **0.433** | 0.433 | 0.433 | 1.000 | 1 |
| 2 | 2.30 | 1.39 | **0.453** | 0.462 | 0.462 | 1.000 | 2 |
| 3 | 2.03 | 1.60 | 0.429 | **0.463** | 0.463 | 1.000 | **3** |
| 5 | 1.60 | 1.82 | 0.360 | **0.463** | 0.481 | 0.963 | **3** |
| 8 | 1.11 | 1.98 | 0.261 | **0.463** | 0.574 | 0.807 | **3** |
| 12 | 0.66 | 2.07 | 0.159 | **0.463** | 0.727 | 0.636 | **3** |

**The equal-weighted optimum is two, and it is not a cost result.** Setting every cost to
zero and re-running leaves the optimum at two: dilution alone produces the shape, because
the benefit factor is bounded by `1/sqrt(rho)` while the mean edge falls linearly. Raising
the charge to 100 bp also leaves it at two. Holding all twelve equally is about **a third**
of the information ratio of holding the best one alone.

**The long-only optimum holds three and does not improve past three.** It is 0.463 at three
candidates and 0.463 at twelve; the nine additional candidates receive zero weight. The
unconstrained optimum meanwhile rises from 0.463 to 0.727, and the whole difference is the
short leg: the unconstrained weights at twelve candidates are
`+0.217, +0.152, +0.098, +0.054, +0.022, −0.011, −0.032, −0.054, −0.070, −0.086, −0.097,
−0.108` normalised on gross — **seven of twelve short, and net long exposure is 8.4% of
gross**. That is the technical statement behind the whole section: **when candidates are
positively correlated, most of the incremental benefit of breadth lives in the short leg,
and a long-only investor cannot reach it.**

The optimum is exact rather than iterative. It is found by enumerating all `2^k - 1 = 4,095`
supports and keeping those whose `Sigma_S^-1 e_S` is non-negative, so it carries no
convergence tolerance and no starting point. A dense Dirichlet search over the simplex,
40,000 draws, reaches 0.400 — **below** it, as it must be.

### It is monotone in correlation, and that is not a knife-edge

| `rho` | Unconstrained IR | Long-only IR | Transfer coefficient | Held |
| ---: | ---: | ---: | ---: | ---: |
| 0.10 | 0.621 | 0.564 | 0.908 | 5 |
| 0.20 | 0.633 | 0.518 | 0.819 | 4 |
| 0.30 | 0.663 | 0.489 | 0.737 | 3 |
| **0.435** | **0.727** | **0.463** | **0.636** | **3** |
| 0.50 | 0.769 | 0.454 | 0.590 | 2 |
| 0.70 | 0.982 | 0.435 | 0.443 | 2 |

The two columns move in **opposite** directions, and that is the mechanism rather than a
curiosity: shorting correlated candidates against each other becomes *more* valuable as
correlation rises, while a long-only investor's reachable set shrinks. They diverge exactly
where the thesis needs them to converge.

### The scope limit that must travel with the count

The held count is set by **edge dispersion** at least as much as by correlation. Same
correlation, same cost, eight candidates, three dispersion settings:

| Candidate edges | Long-only IR | Unconstrained IR | Transfer coefficient | Held |
| --- | ---: | ---: | ---: | ---: |
| Identical, all 2.0 | 0.375 | 0.375 | **1.000** | **8** |
| Mild, 2.4 down to 1.7 | 0.412 | 0.413 | 0.997 | 6 |
| Realistic, 3.0 down to 0.5 | 0.463 | 0.574 | 0.807 | **3** |

**Give every candidate the same edge and equal weighting is optimal, the transfer
coefficient is 1.000, and the optimiser holds all eight.** The investor's own phrasing —
*"a ton of strategies that are 55% likely"* — assumes exactly that. Real shelves do not have
it, and this repository's own sleeve edges span +0.32 to +3.35 pp/yr. **The count is a
statement about dispersed shelves; it is not a law.** Note also that the identical-edge
case escapes nothing: the `Phi(z_1/sqrt(rho))` ceiling of §1 is unchanged at 0.576. There
are two routes to the same wall.

The ladder omits skew, fat tails, time-varying correlation and estimation error in the
edges. **Each omission favours the thesis**, so this is the generous case.

---

## 6. Crisis-conditional breadth, measured

`as of 2026-09-01`. Every correlation in §1–§4 is unconditional, and the question this
page left open was whether the five active sleeves stay five bets when equity falls. The
same 422-month panel (1990-11…2025-12), same modelled sleeve excess returns, conditioned
four ways: the worst decile of US equity months, the worst decile of the 65/25/10 blend,
the union of [Experiment 004](trend-marginal-value.md)'s frozen crisis windows, and months
whose trailing twelve-month US return is negative. The condition is a regime label formed
on the same month's return, not a signal; nothing here could be acted on. **No
specification was frozen and nothing is ledgered.**

| Condition | Months | `1'R^-1 1` of 5 | 95% i.i.d. bootstrap |
| --- | ---: | ---: | :---: |
| all months (reproduces §1) | 422 | **3.71** | [3.27, 4.33] |
| worst decile, US equity | 42 | **2.87** | [2.21, 4.44] |
| worst decile, 65/25/10 blend | 42 | 2.91 | [2.24, 4.51] |
| Experiment 004 crisis windows, union | 53 | 2.80 | [2.22, 4.11] |
| trailing 12-month US return negative | 75 | 2.68 | [2.17, 3.59] |

The intervals overlap 3.71 in three of four conditions; the one that excludes it is the
trailing-return condition, on an i.i.d. interval the study itself calls optimistic for a
clustered tail. The worst-decile matrix, US equity:

| | AVLV | DFIV | IDMO | AVES | trend |
| --- | ---: | ---: | ---: | ---: | ---: |
| **AVLV** | 1.000 | **0.809** | −0.218 | **0.637** | −0.107 |
| **DFIV** | 0.809 | 1.000 | −0.198 | 0.612 | −0.079 |
| **IDMO** | −0.218 | −0.198 | 1.000 | 0.005 | **0.636** |
| **AVES** | 0.637 | 0.612 | 0.005 | 1.000 | 0.098 |
| **trend** | −0.107 | −0.079 | 0.636 | 0.098 | 1.000 |

**The three value tilts merge** (AVLV–DFIV 0.57 → 0.81, AVLV–AVES 0.32 → 0.64, DFIV–AVES
0.41 → 0.61), **and IDMO's correlation with trend rises** from +0.445 to +0.64, the
pairing §4 flagged. The value-to-momentum and value-to-trend correlations stay near zero
or negative.

Conditional means in the worst decile of US equity, pp/month, with the Newey–West interval
the study prints and, for trend, the interval that prices the selection:

| Sleeve | Mean | Interval | All-months mean |
| --- | ---: | :---: | ---: |
| AVLV | +0.12 | [−0.63, +0.87] | +0.06 |
| DFIV | +0.88 | [−0.10, +1.87] | +0.28 |
| IDMO | +0.68 | [−0.07, +1.42] | +0.37 |
| AVES | +0.30 | [+0.04, +0.55] | +0.16 |
| trend (AQR TSMOM) | **+2.84** | NW [+1.65, +4.04]; **joint block bootstrap [+0.70, +4.37]** | +0.89 |

**No active sleeve has a negative conditional mean in any of the four conditions**, and
only AVES's and trend's intervals exclude zero. The plain reading: **they merge, they do
not fail together.** Inside the frozen windows, compounded, the four tilts ran −4.9% to
+1.8% through the GFC while trend ran +29.6%; through the dotcom bust all five were
positive; through 2022 all five were positive.

Four corrections to the trend figure, each from the red-team re-run. The Newey–West
interval is computed on the time-ordered subsequence of tail months, which treats 2008-10
and 2009-01 as adjacent and ignores that the tail was selected; a stationary block
bootstrap over the joint panel that re-selects the worst decile in every replicate gives
**[+0.70, +4.37]**. The +2.84 largely restates the unconditional relation: a linear fit on
TSMOM's −0.159 correlation with US equity predicts +2.04 at the tail's mean equity return
of −7.75%, and five months (2012-05, 2002-12, 2020-03, 2008-10, 2001-09) carry 47 of the
tail's 119 pp. On the repository's own 4-asset book, scaled as
[Experiment 018](defensive-engines-in-the-construction.md) uses it, the same conditional
mean is **+1.94 [+0.23, +3.65]** on 1990-11…2025-05 and +1.43 [+0.35, +2.52] on 1929–2025.
And the figure is per dollar of the vendor index: at RSST's fitted 0.681 loading it is
+1.94, and at 30% of capital **+0.58 pp/month against an equity leg at −7.9**, so the
overlay offsets about 7% of the equity loss in the tail; lagged one month the tail mean
halves to +1.44. Whether trend covered a stacked bond leg's 2022 loss depends on which
trend series is read, and on the own book it did not
([defensive engines](defensive-engines-in-the-construction.md) §3).

Reproduce it:

```sh
cd research
uv run python -m portfolio_edge.studies._conditional_breadth_tables
```

---

## Verified, assumed, open

**Verified.** The closed forms, against an independent covariance solve, at every `k` from
1 to 40 and every `rho` from 0 to 0.9; the ceiling `Phi(z_1/sqrt(rho))` as the limit of the
stack; the appraisal identity `IR_new**2 = IR_old**2 + (alpha/omega)**2` against
`sqrt(e' Sigma^-1 e)` computed by matrix solve; the substitution ceiling against 2,000
random simplex weights. All correlations are Pearson on 422 aligned months from committed
French and AQR files, last month read **2025-12**. The measured equity-to-trend correlation
of −0.183 independently reproduces [Experiment 004's](trend-marginal-value.md) −0.17 on a
different blend and window; the 1.55 effective regions measured here for HML sit beside
Experiment 005's 1.49 for the same factor over a different era.

**Assumptions, each one load-bearing.**

- **Every premium is an input**, carried across four scenarios. Nothing here estimates one.
- **Sleeve excess returns are the delivered loading vector applied to regional factors**,
  with no market-beta difference and no alpha. Fund residual is added back as an
  uncorrelated diagonal calibrated on the two sleeves whose tracking error was measured.
- **IDMO's and AVES's tracking errors are assumed**, from a factor share that the two
  measured sleeves disagree about by a factor of three. All three settings are reported and
  none moves a headline, because trend dominates the tracking error.
- **AVES's delivered HML is its own +0.237 with an implicit zero for IEMG**, which has no
  measured loading of any kind. That is the most optimistic reading available. Its **fee**
  is measured — 36 bp against IEMG's 9 bp capped to 2030-12-31 — but its turnover is not,
  and is charged at AVLV's 7%/yr against an implicit zero for IEMG.
- **Fund alphas are charged by a rule frozen before the numbers were read**: an alpha is
  charged when its own point estimate exceeds its own detection floor. The rule's bias —
  it charges the fund with the better instrument — is why all three settings are reported.
- **No tax charge is made anywhere.** The 1.62 pp/yr deferral-plus-step-up hurdle is
  quoted as an upper bound on what a high-turnover sleeve forfeits and is not netted into
  any probability.
- **AQR's TSMOM stands in for RSST's trend leg.** It is a vendor reconstruction by a firm
  that sells the strategy, with no vintage archive and no stated cost basis. RSST's own
  loading on it is +0.681 [+0.406, +0.955] over 31 filed months
  ([comparability](loading-comparability-and-wrapper-exposure.md)), so the stand-in is
  about a third hotter than the fund and every figure resting on it is optimistic by an
  amount this window cannot pin down.
- **The premium standard errors are backed out of published MDE80 figures** by dividing by
  `z_0.95 + z_0.80 = 2.486`. They are in-sample sampling errors and contain no structural or
  model uncertainty, so `Phi(e/tau)` is itself an upper bound.
- **Annual relative returns are treated as independent with constant mean.** Both
  assumptions flatter every probability on this page.

**Open.**

1. **The benchmark for the trend leg.** This page scores it against equity, which is the
   right comparator for *"will this portfolio beat the market"* and the wrong one for
   *"should I hold trend"*. A drawdown- or growth-objective scoring at 30% of notional does
   not exist; the repository's figures are at 10% and 15% weights in different base
   portfolios, and the client's own note on this construction records that the trend
   closure turns on the reference weight rather than on evidence.
2. **Crisis-conditional breadth is measured ([§6](#6-crisis-conditional-breadth-measured))
   and what remains is narrower.** The tail count is 2.7–2.9 of 5 on intervals that mostly
   still contain 3.71, so the measurement cannot yet separate "the tilts merge" from
   sampling noise on 42 months. Two things would: a bond-regime-conditioned version, since
   the one financed leg tested beside trend behaves differently in each correlation regime
   ([defensive engines](defensive-engines-in-the-construction.md) §3); and RSST's own tail
   behaviour from its filings at its delivered loading, in place of the vendor series that
   runs the trend leg about a third hot.
3. **Whether a loading estimated on 45 to 77 fund months forecasts the next thirty years.**
   Every delivered loading on this page comes from a window shorter than one value cycle.
4. **The ex-US large-value alpha.** Four funds read −2.2 to −4.1 pp/yr and it decides this
   portfolio's central case outright — DFIV's line is +3.35 pp/yr without it and
   −0.45 pp/yr with it. **It is the highest-value open question the candidate raises**, and
   until it is explained no weight in DFIV is defensible on this evidence.
5. **IDMO's after-tax edge.** The recommendation above moves capital into the
   highest-turnover fund in the portfolio, and the tax charge is bounded rather than
   measured. In a fully taxable account it could cancel the gain. Nothing here computes an
   after-tax return for any fund.

## What this does not establish

- **Not** that trend should be dropped. It establishes that trend is not scorable on a
  probability-of-beating-equity metric, and that its variance credit peaks at 21.6% of
  notional under the central `rho` while 30% remains inside that correlation's own 95%
  interval.
- **Not** that IDMO is promoted, or that the product audit excluding it is wrong. Marginal
  contribution inside one portfolio and promotion status are different questions.
- **Not** that any premium here is real, or that the candidate beats anything. Every
  probability is conditional on a premium scenario the repository cannot choose between.
- **Not** a verdict on the funds. Loadings, fees and turnovers are quoted from
  [products](factor-products.md) and the typed shelf, not re-estimated.
- **Not** a point-in-time result. Ken French rebuilds the whole history on every release,
  and the fund loadings come from a union census unsuitable for historical selection.
- **Not** a portfolio-level tournament. That is [the agenda's](search-coverage.md) item,
  runs under a frozen specification, and is not this.

## Reproduce it

```sh
cd research
uv run python -m portfolio_edge.studies._stacking_tables
uv run pytest tests/unit/test_studies_stacking.py
uv run python -m portfolio_edge.experiments.exp_017_longonly_ladder --view-results
uv run pytest tests/unit/test_studies_longonly_ladder.py
uv run python -m portfolio_edge.studies._conditional_breadth_tables
```

The arithmetic for sections 1 to 4 is
[`studies/stacking.py`](../../research/src/portfolio_edge/studies/stacking.py), pure and
dependency-light; the measured tables are
[`studies/_stacking_tables.py`](../../research/src/portfolio_edge/studies/_stacking_tables.py),
which is the only half that touches the cache. **Neither is an experiment**: no
specification was frozen and nothing is ledgered. Section 5 is
[`studies/longonly_ladder.py`](../../research/src/portfolio_edge/studies/longonly_ladder.py)
run through [Experiment 017](../../research/experiments/exp_017_longonly_ladder.yaml),
which *is* ledgered, and which reads no market data. **Nothing on this page may promote a
sleeve.**
Input file hashes and coverage are in [the evidence base](evidence-base.md) §2.
