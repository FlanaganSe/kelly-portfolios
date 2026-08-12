# What a sleeve is worth inside a portfolio, rather than on its own

**Question.** Every sleeve this repository has judged except trend was judged by a
*standalone* chain — `premium × loading × capture − cost` — which asks whether an
asset beats the market on its own and **sets the covariance term to zero by
construction**. The portfolio question is different: does adding weight `w` to a
portfolio that already exists raise its growth rate? To first order, funding weight
`w` in sleeve `i` out of funding leg `f` inside portfolio `p`,

```
dg/dw|_(w=0) = (mu_i − mu_f) − (sigma_ip − sigma_fp)
```

The first term is the standalone alpha the existing chain already measures. The
second is a **diversification credit** the standalone chain omits. With `f = p` it
collapses to `(mu_i − mu_p) + sigma_p^2 (1 − beta_ip)`, the same form this repository
already uses for volatility harvesting. The credit can be positive **or negative** —
`beta_ip > 1` makes it negative — so the portfolio view can be *harsher* than the
standalone view rather than kinder. Which way it goes was the question, and it was not
assumed.

**Decision it informs.** Whether the standalone dismissals in
[factor persistence](factor-persistence.md), [long-only capture](long-only-capture.md)
and [the recommended portfolio](portfolio-recommendation.md) omit something that would
change them. Out of scope: any investable claim. Every input here is a paper
portfolio, a vendor series or a model.

**Two specifications, one search.**

| | Deciding metric | Status | What it is |
| --- | --- | --- | --- |
| `exp_010_marginal_sleeve_value` | CRRA certainty equivalent, `gamma = 3` | **`unresolved`** | Frozen first. Kept, hash and runs intact, because it was written before the result |
| `exp_010b_growth_basis` | geometric growth, `gamma = 1` | **`rejected`** | Identical inputs, vintages, portfolios, sleeves, costs, window, eras and **seed**. One parameter differs: `decision_gamma`. It **supersedes exp_010 on what the repository should believe** |

They add **zero trials between them**. exp_010b re-judges data exp_010 had already
spent, so any later deflated-Sharpe or family-wise count must treat the two as **one
search of ten sleeves**. [Decision 0008](../decisions/0008-growth-decides-crra-reports.md)
is why the metric changed and why it was done this way rather than by editing a frozen
file. All figures `as of 2026-08-12`.

## Conclusion

**No sleeve survives, and the reason is arithmetic rather than empirical: the
diversification credit has a ceiling, and the ceiling is below the bar.**

Under pro-rata funding the credit is `sigma_p^2 (1 − beta_ip)` per unit of sleeve
weight, so it is largest at `beta = 0` and equals **exactly `sigma_p^2`** there. That
is a fact about the base portfolio's variance and not about any sleeve:

| Base portfolio | Annualised volatility | Maximum credit at `beta = 0`, 10% weight | Materiality threshold |
| --- | ---: | ---: | ---: |
| `global_equity_core` 60/30/10 | 14.73% | **+0.217 pp/yr** | 0.30 |
| `balanced_60_40` (60% of that core, 40% cash) | 8.85% | **+0.078 pp/yr** | 0.30 |

**Both are below the frozen 0.30 pp/yr threshold, and no sleeve can beat a bound it
cannot reach.** A perfect zero-beta asset added at the reference weight would still
fail on the credit alone; the credit can only ever be a contribution to a case that
the standalone alpha term has to carry. That settles the question the experiment was
built to ask: *the portfolio-level view does not rescue anything the standalone chain
dismissed.*

Three further findings, in descending order of how much they change other pages.

1. **Judged marginally, equity tilts against a bond-containing portfolio do
   strictly worse, not better.** Against `balanced_60_40` **every one of the six
   long-only equity sleeves carries `beta > 1` and therefore a negative credit** —
   from `dev_ex_us_small_value` at 1.345 to `emerging_equity` at 1.871. The portfolio
   view *strengthens* those dismissals. Against the pure equity core the picture is
   milder and one prediction failed (below), but the credits there are at most +0.041
   pp/yr at the reference weight and the ceiling still binds.
2. **The certainty equivalent pays for de-risking, and this experiment measured the
   payment.** Its `cash_control` — cash added to a 100% equity core, funded pro rata
   from it — supplies **zero alpha and zero credit by construction**. It scores
   **+0.166 pp/yr** of certainty equivalent while **losing 0.643 pp/yr of growth**: a
   de-risking reward of **+0.809 pp/yr, 2.7× the materiality threshold**, for a sleeve
   that supplies nothing. This is the calibration that produced decision 0008, and it
   is the reason the whole family's status moved from `unresolved` to `rejected`.
3. **The modelled long-duration Treasury proxy was exp_010's only non-rejected sleeve,
   and growth rejects it.** On the certainty equivalent it read **+0.492** and reached
   `unresolved` only because no rejection clause fired. On growth it reads **−0.385**,
   clause (a) fires and clause (c) with it. With nothing left unresolved the family is
   `rejected`. It is a *proxy* either way, and whatever status it carries is a
   statement about the model, never about a real Treasury sleeve.

## What was run

| Field | Value |
| --- | --- |
| Specifications | [`exp_010_marginal_sleeve_value.yaml`](../../research/experiments/exp_010_marginal_sleeve_value.yaml), hash `d46d0f9524…`; [`exp_010b_growth_basis.yaml`](../../research/experiments/exp_010b_growth_basis.yaml), hash `228c6f97f1…` |
| Run kind | **exploratory** both; neither consumes the final holdout |
| Ledger `run_id` | exp_010: `b27643d6…`, `7e5016a3…`, `11d76e90…`. exp_010b: `eb2279fa…`, `cb564f2a…` (the page quotes `cb564f2a`) |
| Sample | 1991-01 to 2025-12, **420 months = 35 whole calendar years**, one lead month (1990-12) read and never reported |
| Base portfolios | `global_equity_core` 60% US / 30% developed ex-US / 10% emerging, monthly rebalanced — a **frozen round approximation of global market capitalisation, not an optimum**; `balanced_60_40`, 60% of that core plus 40% cash (FRED TB3MS). Cash rather than bonds, because [decision 0002](../decisions/0002-no-research-grade-free-price-source.md) leaves no investable bond total-return history available |
| Sleeves | 10 in the Holm family, plus one **modelled proxy** and one **calibration control** = 12 tested |
| Funding legs | `pro_rata` (primary), `named_leg`, `cash` |
| Weights | reference **10%**, cap 20%, grid step 0.005 |
| Costs | 2 bp (optimistic) and 8 bp (pessimistic) one-way on portfolio trades, plus fee tiers per sleeve kind; charged inside the realised path, never as a haircut. **Net-pessimistic decides** |
| Inference | Paired stationary block bootstrap on the joint monthly panel, mean block **12 months frozen not tuned**, 10,000 resamples |
| Seed | 20260909, identical in both specifications |

The frozen falsifier, identical in both files except that every reading of "certainty
equivalent" becomes "geometric growth rate at `gamma = 1`" in exp_010b. A sleeve is
**`rejected`** when any of:

- **(a)** its marginal gain at the reference weight, funded pro rata, net-pessimistic,
  is below **0.30 pp/yr**;
- **(b)** its diversification credit `12(sigma_fp − sigma_ip)` at the declared funding
  leg is zero or negative, so the portfolio view supplies no credit the standalone
  chain omitted and **the existing standalone dismissal stands unaltered**;
- **(c)** the constrained optimal weight on the growth surface is zero at the
  long-only boundary; or
- **(d)** it does not survive Holm at 0.05 across the declared family of ten.

It is **`unresolved`**, not rejected, when no clause fires but any of: (u1) the 95%
interval contains zero; (u2) the effect is smaller than its own minimum detectable
effect at 80% power; (u3) its sign differs between the two frozen funding legs; (u4)
the credit spans zero at the ends of the correlation's own interval; or (u5) it is a
declared proxy, since **a modelled series may never resolve anything**.

Clause (b) already read the `gamma = 1` credit in exp_010 while the rest of that
falsifier read `gamma = 3`. That internal inconsistency is one of the things exp_010b
resolves.

## The sleeve table, both bases

`global_equity_core`, pro-rata funding, net-pessimistic costs, reference weight 10%,
full period. **Growth decides; the certainty equivalent is reported beside it and the
third column is the difference between them** — what the CRRA metric was paying, or
charging, for a change in risk. Interval and *p* are on the growth figure.

| Sleeve | **Growth, γ=1** | CE, γ=3 | De-risking | 95% interval on growth | Holm *p* | Status |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| `emerging_small_value` | **+0.543** | +0.248 | −0.295 | `[−0.166, +1.269]` | 0.6075 | `rejected` (d) |
| `us_small_value` | **+0.392** | +0.590 | +0.198 | `[−0.125, +0.924]` | 0.6075 | `rejected` (b, d) |
| `us_momentum_long_only` | **+0.269** | +0.321 | +0.052 | `[+0.014, +0.524]` | 0.1890 | `rejected` (a, d) |
| `trend_aqr` | **+0.258** | +1.172 | +0.913 | `[−0.545, +1.069]` | 1.0000 | `rejected` (a, d) |
| `emerging_momentum_overlay` | **+0.202** | +0.924 | +0.723 | `[−0.396, +0.782]` | 1.0000 | `rejected` (a, d) |
| `dev_ex_us_small_value` | **+0.029** | +0.127 | +0.098 | `[−0.416, +0.502]` | 1.0000 | `rejected` (a, d) |
| `dev_ex_us_momentum_overlay` | **+0.007** | +0.886 | +0.879 | `[−0.747, +0.741]` | 1.0000 | `rejected` (a, d) |
| `emerging_equity` | **−0.104** | −0.357 | −0.253 | `[−0.706, +0.486]` | 1.0000 | `rejected` (a, b, c, d) |
| `us_momentum_overlay` | **−0.299** | +0.734 | +1.033 | `[−1.175, +0.570]` | 1.0000 | `rejected` (a, c, d) |
| `dev_ex_us_equity` | **−0.348** | −0.345 | +0.003 | `[−0.573, −0.116]` | 1.0000 | `rejected` (a, c, d) |
| **PROXY** `long_duration_treasury_proxy` | **−0.385** | +0.492 | +0.877 | `[−1.064, +0.330]` | — | `rejected` (a, c) |
| **CONTROL** `cash_control` | **−0.643** | +0.166 | +0.809 | `[−1.231, −0.036]` | — | `rejected` (a, c) |

**Seven sleeves cleared the 0.30 bar on the certainty equivalent. Six fail it on
growth**, and the sixth column is why: trend 1.172 → 0.258, the US momentum overlay
0.734 → −0.299, the developed-ex-US overlay 0.886 → 0.007, the emerging overlay
0.924 → 0.202, long-only US momentum 0.321 → 0.269, and the modelled proxy
0.492 → −0.385.

**One sleeve moves the other way, and it is recorded because it contradicts the claim
that the metric change is uniformly hostile.** `emerging_small_value` goes 0.248 →
0.543 and **clears the bar on growth having failed it on the certainty equivalent**,
because its de-risking component is **negative**: it adds risk, and the CRRA metric
was charging it for that. It remains `rejected`, on the Holm clause alone, at an
adjusted *p* of 0.6075. The change is hostile at the experiment level, not at every
clause.

Two of the twelve are outside the Holm family by design. The **proxy** would only
harden the correction, and no sleeve survives Holm at ten either way, so excluding it
cannot flatter anything. The **control** is a machine check, not a hypothesis.

## The decomposition: where the credit comes from and where it goes

Per unit of sleeve weight, pro-rata funding, net-pessimistic, `global_equity_core`.
`alpha` is the standalone term the existing chain already measures; `credit` is what
that chain omits. The credit column is ordered exactly as `beta` is, because under
pro-rata funding it *is* `sigma_p^2 (1 − beta_ip)`.

| Sleeve | Kind | `beta` to core | Credit, pp/yr per unit weight | Credit at 10% |
| --- | --- | ---: | ---: | ---: |
| `us_momentum_overlay` | funded long-short | −0.329 | +2.883 | +0.288 |
| `dev_ex_us_momentum_overlay` | funded long-short | −0.221 | +2.648 | +0.265 |
| `emerging_momentum_overlay` | funded long-short | −0.158 | +2.512 | +0.251 |
| `trend_aqr` | funded long-short, vendor | −0.132 | +2.457 | +0.246 |
| `long_duration_treasury_proxy` | **modelled proxy** | −0.018 | +2.208 | +0.221 |
| `cash_control` | **control** | +0.001 | +2.168 | **+0.217 = the ceiling** |
| `dev_ex_us_small_value` | long-only | 0.809 | +0.413 | +0.041 |
| `us_momentum_long_only` | long-only | 0.932 | +0.147 | +0.015 |
| `dev_ex_us_equity` | long-only | 0.981 | +0.041 | +0.004 |
| `emerging_small_value` | long-only | 0.994 | +0.013 | +0.001 |
| `us_small_value` | long-only | 1.083 | −0.181 | −0.018 |
| `emerging_equity` | long-only | 1.125 | −0.271 | −0.027 |

**Read the `cash_control` row as the ruler.** It sits at `beta ≈ 0` and therefore at
the ceiling, +0.217 pp/yr at the reference weight, and it supplies no alpha at all. Any
sleeve with a larger credit than that is one whose beta is *negative* — the four
funded long-short overlays and the proxy — and every one of those pays for it in the
alpha term instead.

**A predeclared prediction was falsified, and it is reported as prominently as a
confirmation would have been.** The specification predicted, before any result, that
*every* long-only equity sleeve would carry `beta ≥ 1` and therefore a non-positive
credit. Against the equity core **four of the six did not**: `dev_ex_us_small_value`
(0.809), `us_momentum_long_only` (0.932), `dev_ex_us_equity` (0.981) and
`emerging_small_value` (0.994) all carry positive credits. Seven of the eleven scored
sleeves matched the prediction; four contradicted it.

That failure is real and it is also small. **The largest credit any long-only equity
sleeve earns is `dev_ex_us_small_value`'s +0.413 pp/yr per unit weight — +0.041 at the
reference weight, against a 0.30 bar.** It is the only equity sleeve with a materially
positive credit, and it still cannot be signed: its own marginal growth is +0.029 pp/yr
with an interval of `[−0.416, +0.502]`, which contains zero and is smaller than its own
minimum detectable effect of 0.580.

**Against `balanced_60_40` the prediction holds without exception.** Every long-only
equity sleeve carries `beta > 1` there — 1.345, 1.554, 1.632, 1.653, 1.803, 1.871 —
and every credit is negative. Adding equity to a portfolio that is 40% cash raises its
risk, and the credit term charges for that correctly. The marginal *growth* figures
against that base are larger, because the sleeves are being funded partly out of cash;
that is a statement about the base portfolio's equity share, not about the sleeves, and
it is the reason a base portfolio is declared rather than chosen.

## Why the certainty equivalent could not be left deciding

The control was frozen with an answer known in advance: *cash added to an equity core
and funded from US equity must show a materially negative marginal figure. If it does
not, the machinery is wrong and no other figure may be read.*

| `cash_control`, by funding leg | CE, γ=3 | Growth, γ=1 | De-risking |
| --- | ---: | ---: | ---: |
| `pro_rata` | **+0.166** | **−0.643** | **+0.809** |
| `named_leg` (US equity) | −0.026 | **−0.803** | +0.777 |
| `cash` | −0.007 | **−0.007** | **−0.0005** |

The growth reading passes the machine check on every leg. The certainty equivalent
passes it only under `cash` funding — the degenerate case where the sleeve *is* the
funding leg, and the control on the control. **The reward appears exactly when the
sleeve removes equity and nowhere else.**

The second-moment model predicts part of this and not all of it. Raising `gamma` from
1 to 3 triples the credit term and moves the control's *predicted* marginal from −0.582
to −0.148 pp/yr, a de-risking allowance of +0.434. The realised allowance is +0.809, so
**+0.376 pp/yr is a left-tail reward the variance never sees**: exact CRRA utility over
only 35 calendar-year observations weights the realised worst years far more heavily
than a variance does, and cash is what was not in equities during them. Note that even
at `gamma = 3` the *model* says the cash sleeve costs 0.148 pp/yr. Only the exact
utility over 35 points makes it look profitable.

A reader who prefers the certainty-equivalent reading concludes that this experiment is
void and no figure may be read. **That reader reaches the same decision about every
sleeve**, because every sleeve is rejected on the frozen falsifier either way. The
choice of reading cannot promote anything.

## Hostile tests

Marginal growth, `global_equity_core`, pro-rata, net-pessimistic, pp/yr. The two eras
are diagnostics and never independent observations.

| Sleeve | Baseline | Double costs | Delay 1 month | Best year removed | 1991–2008 | 2009–2025 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `emerging_small_value` | +0.543 | +0.496 | +0.731 | +0.314 (1993) | +0.950 | +0.092 |
| `us_small_value` | +0.392 | +0.347 | +0.641 | +0.269 (2000) | +0.742 | +0.006 |
| `us_momentum_long_only` | +0.269 | +0.226 | +0.471 | +0.216 (1998) | +0.407 | +0.117 |
| `trend_aqr` | +0.258 | −0.009 | +0.231 | +0.021 (2008) | +1.243 | −0.823 |
| `emerging_momentum_overlay` | +0.202 | −0.051 | +0.160 | +0.027 (2008) | +0.648 | −0.292 |
| `dev_ex_us_momentum_overlay` | +0.007 | −0.220 | −0.030 | −0.216 (2008) | +0.586 | −0.632 |
| `long_duration_treasury_proxy` | −0.385 | −0.404 | −0.383 | −0.616 (2008) | +0.182 | −1.010 |

**Every sleeve with a negative beta collapses in the second era and every one of them
loses its best year to 2008.** Trend goes +1.243 to −0.823; the developed-ex-US
momentum overlay +0.586 to −0.632; the modelled proxy +0.182 to −1.010. Doubling costs
alone takes trend and both momentum overlays that were positive at baseline below zero.
The sleeves whose value is a *credit* are the sleeves whose credit was earned in one
crisis.

## The optimal weight is a selected maximum, and its interval says so

The constrained optimum is chosen from the same sample it is evaluated on, so its naive
gain is positive by construction on a noisy surface. Only an interval that re-selects
the weight inside every bootstrap replicate carries that selection effect, and the gap
between the two is reported rather than resolved.

| Sleeve | In-sample optimum | Re-selected gain, median | Re-selected 95% | Replicates choosing zero weight |
| --- | ---: | ---: | --- | ---: |
| `us_small_value` | 0.20 | +0.753 | `[0.000, 1.838]` | 6.7% |
| `emerging_small_value` | 0.20 | +1.054 | `[0.000, 2.485]` | 6.6% |
| `dev_ex_us_small_value` | 0.20 | +0.040 | `[0.000, 0.999]` | **45.0%** |

Every one of those intervals has a lower bound of exactly zero, which is what the
long-only boundary produces when the surface is flat and noisy. Read the median as *the
gain a searcher who optimises in sample would report*, not as a gain available to
anyone.

## Verified, assumed, open

**Verified in this experiment.** The credit ceiling `sigma_p^2` at `beta = 0`, which is
algebra confirmed numerically by the control landing on it. That the metric change
moves exactly one thing — the two runs share inputs, vintages, portfolios, sleeves,
costs, window, eras and seed, and a unit test compares the two committed
specifications field by field so neither can drift. That the machinery reports a
correctly negative growth marginal for a sleeve that supplies nothing, on all three
funding legs.

**Assumptions, stated so they can be attacked.** The base portfolio weights are frozen
and round, not optimised. The fee tiers are **this repository's assumptions** about an
accessible implementation and not any provider's disclosure — the underlying Ken French
series carry no cost at all, and AQR states none. The reference weight of 10% and the
20% cap were chosen before any result and neither is optimised. Long-short sleeves are
made funded by adding cash to a self-financing factor return, which is the only way to
compare them with a long-only holding and which **understates their cost**, since the
French factor files contain no shorting cost, no borrow and no capacity limit.

**What this is not.** Not an investable backtest, and no figure here is an achievable
investor outcome. Ken French's files are paper portfolios rebuilt from the current
vintage on every release; the trend series is maintained by a firm that sells the
strategy; the long-duration sleeve is modelled from a yield and is not a total-return
history at all.

**Open questions this page does not settle.**

1. **Gold was not tested, and its absence biases the experiment toward finding no
   credit anywhere.** It is one of only two candidate assets with a plausibly low equity
   beta and no research-grade series is reachable
   ([decision 0002](../decisions/0002-no-research-grade-free-price-source.md)). That
   direction is stated rather than left for a reader to notice.
2. **An investable bond sleeve was not tested either.** The GS10 duration proxy stands
   in its place and clause (u5) is what keeps it from resolving anything.
3. **The credit is a difference of two covariances from 420 months.** Its sensitivity
   is reported beside it: a credit that moves by more than itself when the correlation
   moves by 0.10 is not a finding, and several of these do.
4. **The Holm family of ten is a lower bound on the correction the whole search
   requires.** It counts neither the three funding legs, the two base portfolios, the
   three cost columns, the two eras, nor the twelve specifications frozen before it.
   Any later trial count starts from the ledger, not from this family.

**Reproducibility.**
`cd research && uv run python -m portfolio_edge.experiments.exp_010_marginal_sleeve_value --view-results`.
Source vintages are pinned by sha256 in each specification and a mismatch aborts;
manifests are committed under `research/data-manifests/`. Retrieval date for every
source: **2026-08-12**. Seed 20260909.

## Consequence for this repository

1. **The portfolio-level view is now closed as a route to rescuing a dismissed
   sleeve, and the reason is a bound rather than a result.** At this base portfolio's
   volatility the credit cannot reach the materiality threshold even at `beta = 0`. A
   future experiment that wants a material credit needs a *lower-volatility* base
   portfolio to be irrelevant — the ceiling falls with `sigma_p^2`, so a bond-containing
   base makes it worse, not better — or a genuinely large standalone alpha, which is the
   term the standalone chain was already measuring.
2. **The standalone dismissals stand, and two of them are strengthened.** Clause (b)
   fired for `us_small_value` and `emerging_equity` against the equity core, and every
   long-only equity sleeve's credit is negative against `balanced_60_40`. Judged
   marginally, an equity tilt inside an equity portfolio is worth *less* than the
   standalone chain said, not more.
3. **Every future specification names `decision_gamma`.** Omitting it silently inherits
   the pre-0008 meaning ([decision 0008](../decisions/0008-growth-decides-crra-reports.md)
   constraint 1).
4. **A control with no value by construction is now the pattern**, not an optional
   extra. It cost one cell of compute, it cannot promote anything because it is outside
   the Holm family, and it is the only reason this error was found rather than
   published.
5. **Nothing is promoted.** [Decision 0004](../decisions/0004-no-sleeve-promoted.md)
   stands in full, and this experiment makes the case for promotion strictly harder.
