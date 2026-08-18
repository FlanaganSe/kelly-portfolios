# What a sleeve is worth inside a portfolio, rather than on its own

**Question.** Every sleeve judged here except trend was judged by a *standalone* chain —
`premium × loading × capture − cost` — which asks whether an asset beats the market on its
own and **sets the covariance term to zero by construction**. The portfolio question is
different. Funding weight `w` in sleeve `i` out of leg `f` inside portfolio `p`, to first
order,

```
dg/dw|_(w=0) = (mu_i − mu_f) − (sigma_ip − sigma_fp)
```

The first term is the standalone alpha. The second is a **diversification credit** the
standalone chain omits. With `f = p` it collapses to
`(mu_i − mu_p) + sigma_p**2 (1 − beta_ip)`. The credit can be positive **or negative** —
`beta_ip > 1` makes it negative — so the portfolio view can be *harsher* than the
standalone view rather than kinder. Which way it goes was the question, and it was not
assumed.

**Decision it informs.** Whether the standalone dismissals elsewhere omit something that
would change them. Out of scope: any investable claim. **Every input here is a paper
portfolio, a vendor series or a model.**

**Two specifications, one search.**

| | Deciding metric | Status | What it is |
| --- | --- | --- | --- |
| `exp_010_marginal_sleeve_value` | CRRA certainty equivalent, `gamma = 3` | **`unresolved`** | Frozen first. Kept, hash and runs intact, because it was written before the result |
| `exp_010b_growth_basis` | geometric growth, `gamma = 1` | **`rejected`** | Identical inputs, vintages, portfolios, sleeves, costs, window, eras and **seed**. One parameter differs: `decision_gamma`. It **supersedes exp_010 on what to believe** |

They add **zero trials between them** — exp_010b re-judges data exp_010 had already spent,
so any later trial count must treat the two as **one search of ten sleeves**.
[Decision 0008](../decisions/0008-growth-decides-crra-reports.md) is why the metric changed
and why it was done this way rather than by editing a frozen file. `as of 2026-08-12`.

---

## Conclusion

**No sleeve survives.** Two findings do the work, and they are not equally strong.

### What is established

**Judged marginally, equity tilts against a bond-containing portfolio do strictly worse,
not better.** Against `balanced_60_40` **every one of the six long-only equity sleeves
carries `beta > 1` and therefore a negative credit** — 1.345 to 1.871. Adding equity to a
portfolio that is 40% cash raises its risk, and the credit term charges for that correctly.
**The portfolio view *strengthens* those dismissals.**

**The certainty equivalent pays for de-risking, and this experiment measured the payment.**
The `cash_control` — cash added to a 100% equity core, funded pro rata from it — supplies
**zero alpha and zero credit by construction**. It scores **+0.166 pp/yr** of certainty
equivalent while **losing 0.643 pp/yr of growth**: a de-risking reward of **+0.809 pp/yr,
2.7× the materiality threshold, for a sleeve that supplies nothing.** This is the
calibration that produced decision 0008, and it is the reason the family's status moved
from `unresolved` to `rejected`.

**Gold has now been tested under both funding rules, the "no credit anywhere" phrasing is
falsified, and the conclusion survives anyway.** Gold earns a credit of **+0.217 pp/yr at the 10% reference
weight against `global_equity_core` — exactly the ceiling**, because its beta to that
portfolio measures **+0.000**. It is the only asset this repository has found that
reaches the ceiling while being a real holdable asset rather than the cash control. **And
its marginal growth is −0.100 pp/yr**, because the credit was never the binding term: per
unit of weight the credit is **+2.171 pp/yr** and gold's standalone shortfall against the
equity core is **−2.95**, so **the maximum credit the construction can pay covers 74% of
the shortfall and no more, at any weight.** **[§ Gold, tested](#gold-tested) is the section; the short version
is that the ceiling is reachable, is reached, and is not enough.**

**And the pro-rata rule this experiment froze is the wrong test for that conclusion, which
a red team caught after the first version of this section was written.** Re-run under
*financed overlay* funding — the rule the one gold overlay wrapper actually imposes — gold's
marginal contribution **changes sign, from −0.395 to +0.182 pp/yr** against the
leverage-matched control at the reference weight. **The correction is material and the
verdict is unchanged**, because +0.182 sits below the 0.30 bar and below its own 0.73
detection floor, because the matched-volatility control rejects the sleeve outright at the
weight the wrapper actually runs, and because that wrapper's measured 1.53 pp/yr tax drag
exceeds every positive cell. **The funding-rule table is the one to quote from now, not the
pro-rata one.**

**The modelled long-duration Treasury proxy was exp_010's only non-rejected sleeve, and
growth rejects it.** On the certainty equivalent it read +0.492 and reached `unresolved`
only because no clause fired; on growth it reads **−0.385** and clause (a) fires. It is a
*proxy* either way, and whatever status it carries is a statement about the model, never
about a real Treasury sleeve.

**And on 2026-08-17 a measured series replaced it, which moves the cell and does not move
the verdict.** Goyal–Welch `ltr` — 1,200 months of long-term US government total return
from 1926-01, [in this repository's cache and manifests the whole time](evidence-base.md) —
was run through the same construction on this experiment's own 420-month sample. The
first-order marginal at the 10% reference weight moves from **−0.328 to −0.136 pp/yr**
pro rata, and from **+0.258 to +0.450** under financed overlay funding before costs, or
**+0.375** after a 60 bp borrow spread and a 15 bp fee. **The proxy was understating the
exposure**, by 1.76 pp/yr of excess return and 3.5 pp/yr of volatility. It still does not
clear anything: the pro-rata figure is far below the 0.30 bar, and the overlay figure sits
at less than half its own 80%-power floor of **0.868 pp/yr**. The working is in
[alternative sleeves audit §8.6](alternative-sleeves-audit.md); the two figures that matter
are repeated here because this is the page whose cell they change.

### What is NOT established, and the page previously overstated

Under pro-rata funding the credit is `sigma_p**2 (1 − beta)` per unit weight, so at
`beta = 0` it equals **exactly `sigma_p**2`**:

| Base portfolio | Volatility | Maximum credit at `beta = 0`, **10% weight** | Same at the **20% cap** | Bar |
| --- | ---: | ---: | ---: | ---: |
| `global_equity_core` | 14.73% | **+0.217 pp/yr** | **+0.434 pp/yr** | 0.30 |
| `balanced_60_40` | 8.85% | **+0.078 pp/yr** | +0.157 pp/yr | 0.30 |

**At the frozen 10% reference weight the ceiling sits below the bar, so a perfect zero-beta
asset would fail on the credit alone. At the specification's own 20% cap it does not.**

This page previously concluded from the first column that *"the portfolio-level view is
closed as a route to rescuing anything the standalone chain dismissed"*. **That closure is
weight-dependent and does not survive this experiment's own cap**, and it is withdrawn as
stated. Three limits on how much this design can settle, set out in
[search coverage](search-coverage.md) §1.1:

- **The reference weight was frozen at 10% and the ceiling scales linearly in it.** The
  weight question is not hypothetical inside this experiment either: the optimal-weight
  table below puts all three small-value sleeves' in-sample optima **at the 0.20 cap**.
  Those optima are selected in sample and their re-selected intervals all reach exactly
  zero, so they establish nothing — **but the closure sentence does not engage them.**
- **A sleeve bolted onto a fixed base is not "the portfolio-level view."** Two declared,
  equity-dominated base portfolios with one sleeve varied at a time. The portfolio question
  is the joint weighting of everything at once, which is the construction tournament —
  designed in the framework and never run.
- **Pro-rata funding is the least favourable rule for a diversifier.** Funding out of the
  highest-beta leg is the realistic alternative; `named_leg` results exist and the headline
  uses pro rata.

**Be precise about what the ceiling applies to.** The deciding clause (a) reads a **finite
difference at the 10% weight**, not a derivative at zero, and the frozen specification
explicitly rejects the derivative-at-zero because it "favours any low-beta asset by
construction". `sigma_p**2 (1 − beta)` is the **first-order credit term**, so it is clause
(b) and the closure sentence that inherit the weight dependence — not clause (a), and not
clause (c), which does read the whole growth surface.

**A re-specification is the correct response, and it is round two's first item.** Nothing
here promotes anything either way: every sleeve is rejected on the frozen falsifier on both
metrics.

---

## What was run

| Field | Value |
| --- | --- |
| Specifications | `exp_010_marginal_sleeve_value.yaml` `d46d0f9524…`; `exp_010b_growth_basis.yaml` `228c6f97f1…` |
| Run kind | **exploratory** both; neither consumes the final holdout |
| Ledger `run_id` | exp_010: `b27643d6…`, `7e5016a3…`, `11d76e90…`. exp_010b: `eb2279fa…`, `cb564f2a…` (quoted here) |
| Sample | 1991-01…2025-12, **420 months**, one lead month read and never reported |
| Base portfolios | `global_equity_core` 60/30/10 US / developed ex-US / emerging, monthly rebalanced — a **frozen round approximation of global market capitalisation, not an optimum**; `balanced_60_40`, 60% of that plus 40% cash. **Cash rather than bonds**, because no bond total-return history was thought to be available. **That reason expired on 2026-08-17** and the specification stays as frozen; a successor may use a bond leg for the base and this one may not |
| Sleeves | 10 in the Holm family, plus one **modelled proxy** and one **calibration control** = 12 |
| Funding legs | `pro_rata` (primary), `named_leg`, `cash` |
| Weights | reference **10%**, cap 20%, grid step 0.005 |
| Costs | 2 bp and 8 bp one-way plus fee tiers per sleeve kind, charged inside the realised path. **Net-pessimistic decides** |
| Inference | Paired stationary block bootstrap on the joint monthly panel, mean block **12 months frozen not tuned**, 10,000 resamples |
| Seed | 20260909, identical in both |

The frozen falsifier, identical in both files except that "certainty equivalent" becomes
"geometric growth rate at `gamma = 1`" in exp_010b. A sleeve is **`rejected`** when any of:
**(a)** its marginal gain at the reference weight, funded pro rata, net-pessimistic, is
below **0.30 pp/yr**; **(b)** its diversification credit at the declared funding leg is
zero or negative; **(c)** the constrained optimal weight on the growth surface is zero at
the long-only boundary; or **(d)** it does not survive Holm at 0.05 across the family of
ten. It is **`unresolved`** when no clause fires but the interval contains zero, the effect
is smaller than its own MDE, its sign differs between funding legs, the credit spans zero,
or **it is a declared proxy — since a modelled series may never resolve anything.**

Clause (b) already read the `gamma = 1` credit in exp_010 while the rest of that falsifier
read `gamma = 3`. That internal inconsistency is one of the things exp_010b resolves.

---

## The sleeve table

`global_equity_core`, pro-rata funding, net-pessimistic, reference weight 10%, full period.
**Growth decides; the certainty equivalent reports beside it and the third column is the
difference** — what the CRRA metric was paying, or charging, for a change in risk.

| Sleeve | **Growth, γ=1** | CE, γ=3 | De-risking | 95% interval on growth | Holm *p* | Status |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| `emerging_small_value` | **+0.543** | +0.248 | **−0.295** | `[−0.166, +1.269]` | 0.6075 | `rejected` (d) |
| `us_small_value` | **+0.392** | +0.590 | +0.198 | `[−0.125, +0.924]` | 0.6075 | `rejected` (b, d) |
| `us_momentum_long_only` | **+0.269** | +0.321 | +0.052 | `[+0.014, +0.524]` | 0.1890 | `rejected` (a, d) |
| `trend_aqr` | **+0.258** | +1.172 | **+0.913** | `[−0.545, +1.069]` | 1.0000 | `rejected` (a, d) |
| `emerging_momentum_overlay` | **+0.202** | +0.924 | +0.723 | `[−0.396, +0.782]` | 1.0000 | `rejected` (a, d) |
| `dev_ex_us_small_value` | **+0.029** | +0.127 | +0.098 | `[−0.416, +0.502]` | 1.0000 | `rejected` (a, d) |
| `dev_ex_us_momentum_overlay` | **+0.007** | +0.886 | +0.879 | `[−0.747, +0.741]` | 1.0000 | `rejected` (a, d) |
| `emerging_equity` | **−0.104** | −0.357 | −0.253 | `[−0.706, +0.486]` | 1.0000 | `rejected` (a, b, c, d) |
| `us_momentum_overlay` | **−0.299** | +0.734 | **+1.033** | `[−1.175, +0.570]` | 1.0000 | `rejected` (a, c, d) |
| `dev_ex_us_equity` | **−0.348** | −0.345 | +0.003 | `[−0.573, −0.116]` | 1.0000 | `rejected` (a, c, d) |
| **PROXY** `long_duration_treasury_proxy` | **−0.385** | +0.492 | +0.877 | `[−1.064, +0.330]` | — | `rejected` (a, c) |
| *the same leg, **measured** `ltr` instead of the proxy, recomputed 2026-08-17 outside the frozen run* | **−0.136** *(first order, pro rata, gross)* | — | — | — | — | still below the 0.30 bar and inside its 0.868 floor |
| **CONTROL** `cash_control` | **−0.643** | +0.166 | **+0.809** | `[−1.231, −0.036]` | — | `rejected` (a, c) |

**Seven sleeves cleared the 0.30 bar on the certainty equivalent. Six fail it on growth**,
and the de-risking column is why: trend 1.172 → 0.258, the US momentum overlay 0.734 →
−0.299, the developed-ex-US overlay 0.886 → 0.007, the emerging overlay 0.924 → 0.202,
long-only US momentum 0.321 → 0.269, and the proxy 0.492 → −0.385.

**One sleeve moves the other way, and it is recorded because it contradicts the claim that
the metric change is uniformly hostile.** `emerging_small_value` goes 0.248 → 0.543 and
**clears the bar on growth having failed it on the certainty equivalent**, because its
de-risking component is **negative**: it adds risk, and the CRRA metric was charging it for
that. It remains `rejected` on Holm alone. **The change is hostile at the experiment level,
not at every clause.**

Two of the twelve are outside the Holm family by design. The **proxy** would only harden
the correction. The **control** is a machine check, not a hypothesis.

---

## The decomposition: where the credit comes from

Per unit of sleeve weight, pro-rata funding, `global_equity_core`. The credit column is
ordered exactly as `beta` is, because under pro-rata funding it *is* `sigma_p**2 (1 − beta)`.

| Sleeve | Kind | `beta` to core | Credit per unit weight | Credit at 10% |
| --- | --- | ---: | ---: | ---: |
| `us_momentum_overlay` | funded long-short | −0.329 | +2.883 | +0.288 |
| `dev_ex_us_momentum_overlay` | funded long-short | −0.221 | +2.648 | +0.265 |
| `emerging_momentum_overlay` | funded long-short | −0.158 | +2.512 | +0.251 |
| `trend_aqr` | funded long-short, vendor | −0.132 | +2.457 | +0.246 |
| `long_duration_treasury_proxy` | **modelled proxy** | −0.018 | +2.208 | +0.221 |
| *`ltr`, the **measured** long Treasury that replaced it* | Goyal–Welch index, gross | **−0.092** | **+2.370** | **+0.237** |
| **`cash_control`** | **control** | **+0.001** | **+2.168** | **+0.217 = the ceiling** |
| **`gold`** — added later, **exploratory** | benchmark price + assumed carry | **+0.000** | **+2.171** | **+0.217 = the ceiling** |
| `dev_ex_us_small_value` | long-only | 0.809 | **+0.413** | +0.041 |
| `us_momentum_long_only` | long-only | 0.932 | +0.147 | +0.015 |
| `dev_ex_us_equity` | long-only | 0.981 | +0.041 | +0.004 |
| `emerging_small_value` | long-only | 0.994 | +0.013 | +0.001 |
| `us_small_value` | long-only | **1.083** | **−0.181** | −0.018 |
| `emerging_equity` | long-only | **1.125** | **−0.271** | −0.027 |

**Read the `cash_control` row as the ruler.** It sits at `beta ≈ 0` and therefore at the
ceiling, supplying no alpha at all. **The `gold` row is the same place occupied by a real
asset** — added after the fact and outside the Holm family, so it scores nothing, but it is
the evidence that the ceiling is reachable rather than merely bounding
([§ Gold, tested](#gold-tested)). Any sleeve with a larger credit has a *negative* beta —
the four funded long-short overlays and the proxy — **and every one of those pays for it in
the alpha term instead.**

**A predeclared prediction was falsified, and it is reported as prominently as a
confirmation would have been.** The specification predicted, before any result, that *every*
long-only equity sleeve would carry `beta >= 1` and therefore a non-positive credit.
Against the equity core **four of the six did not**. Seven of the eleven scored sleeves
matched the prediction; four contradicted it.

That failure is real and it is also small. **The largest credit any long-only equity sleeve
earns is `dev_ex_us_small_value`'s +0.413 pp/yr per unit weight — +0.041 at the reference
weight.** It is the only equity sleeve with a materially positive credit, and it still
cannot be signed: its own marginal growth is +0.029 pp/yr with an interval of
`[−0.416, +0.502]`, inside its own minimum detectable effect of 0.580. **It is a reason to
look at a developed ex-US small-value product before a US one. It is not a reason to hold
one.**

**Against `balanced_60_40` the prediction holds without exception.** Every long-only equity
sleeve carries `beta > 1` there and every credit is negative. The marginal *growth* figures
against that base are larger because the sleeves are funded partly out of cash; that is a
statement about the base portfolio's equity share, not about the sleeves.

---

## Gold, tested

This page previously recorded gold as untested and said its absence "biases the experiment
toward finding no credit anywhere". **The bias was real, the direction was right, and the
sentence it was defending is now falsified in its literal form and confirmed in its
substance.** `as of 2026-08-17`, and **`exploratory` throughout** — no specification was
frozen before these numbers were seen, so nothing here may be read as a twelfth entry in
the Holm family.

### Why gold escapes decision 0002, stated before any number

[Decision 0002](../decisions/0002-no-research-grade-free-price-source.md) bans free price
feeds from confirmatory work. Its *reasoning* names two failure modes: **a silently
dropped distribution** and **a mishandled corporate action**. Bullion has neither. It pays
no dividend, no coupon and no distribution of any kind; it splits nothing, merges with
nothing, and is issued by no entity that can restate or delist. So for an unlevered holder

```
total return  =  price return  −  carry cost
```

is exact, with no unobserved cash flow anywhere in it. The carry cost is the *only* free
parameter, and it is an assumption a caller has to state rather than a number a parser can
lose. **That is a different situation from an ETF price whose adjusted close is recomputed
on every request, and decision 0002 does not reach it.**

Three weaker objections do reach it, and they are why the ceiling is `exploratory` rather
than higher: there is **no vintage archive**, so a corrected fix overwrites in place
exactly as a revised FRED series does; **a wholesale auction price is not a retail
execution**; and **the carry cost is assumed, not measured**. None of the three is
decision 0002's objection, and the distinction is the point — 0002 says a free price feed
*cannot become* a total return, while these three say a gold series *can*, subject to a
stated assumption and without point-in-time resolution.

### The instruments, and why there are two

| | Primary | Cross-check |
| --- | --- | --- |
| Series | **World Bank Pink Sheet**, `Gold`, `($/troy oz)` | **LBMA Gold Price PM**, USD month-end fix |
| Coverage | monthly, **1960-01…2026-07**, 799 rows | daily, **1968-04-01…2026-08-14**, 14,662 rows |
| Sampling | **monthly average of daily rates** | **month-end**, the last published fix |
| Licence | **CC BY 4.0**, redistributable with attribution | **licence required from IBA to obtain, use or redistribute** |
| sha256 (raw) | `7902a775…` | `fa986c0a…` |

Both are the same benchmark. The Pink Sheet's own definition says so: *"Gold, spot average
of daily rates, from June 2025; previously (UK), 99.5% fine, **London afternoon fixing,
average of daily rates**"* — so before June 2025 it **is** the LBMA PM auction, averaged.
The auction itself is administered by ICE Benchmark Administration, which its methodology
states is *"authorised and regulated by the U.K. Financial Conduct Authority… for the
regulated activity of administering a benchmark under the U.K. Benchmarks Regulation"*;
LBMA gives 2015-03-20 as the date the London Gold Fix ceased. **This is a regulated
benchmark, not a scraped quote**, which is the whole reason the decision-0002 question was
worth asking rather than assumed.

**The licence is the constraint, and it is why the Pink Sheet is primary.** LBMA states
*"a licence from IBA is required in order to obtain, use or redistribute real-time or
historical benchmark data"*; IBA's own disclaimer says *"none of IBA's benchmark and other
information may be used without a written licence from IBA"*; and in March 2025 IBA had the
World Gold Council remove its historical LBMA series. No research exemption was found. The
raw bytes therefore stay in the uncommitted cache and only hashes are manifested — the
treatment this repository already gives the ICE BofA indices, for the same administrator.

**Two samplings of one benchmark is not redundancy, it is the measurement.** Differencing
monthly *averages* is the Working problem: it induces positive first-order autocorrelation
and understates volatility, so **the Pink Sheet's Sharpe ratio is biased upward**. Measured
here: AC(1) is **+0.274** on the average and **+0.053** on the month-end fix, and the two
monthly return series correlate only **+0.673**. **Where they disagree, the less favourable
figure is the one quoted below.**

### The 1971 break, handled explicitly

Before 1971-08-15 the US dollar gold price was an administered peg. A "return" across it
records a policy decision: the par value was reset to $38 by PL 92-268 (1972-03-31, 86
Stat. 116) and to $42.22 by PL 93-110 (1973-09-21, 87 Stat. 352), and **regulations on
private US gold ownership were not eliminated until 1974-12-31** (PL 93-373, 88 Stat. 445).
The pegged window is reported and excluded, and **1975-01 — the first month the asset was
legal for the investor this repository models — is the window every verdict below is
quoted on.** 1971-09 is reported beside it as context and is never the number to take away.

**The distinction between those two starts is the largest single fact on this page, and
this section previously led with the wrong one.**

| Window, net of GLDM's 0.10% | n | gold geometric | gold Sharpe | equity Sharpe |
| --- | ---: | ---: | ---: | ---: |
| **1975-01…end — THE WINDOW TO QUOTE** | **618** | **6.17% / 6.04%** | **0.187 / 0.181** | 0.586 |
| 1975-01…1984-12 | 120 | 5.58% / 5.05% | **0.007 / 0.007** | 0.501 |
| 1985-01…2025-05, §3's window | 485 | 5.84% / 5.92% | 0.268 / 0.247 | 0.584 |
| *1971-09…end, context only* | *658* | *8.62% / 8.63%* | *0.313 / 0.298* | *0.485* |
| *1971-09…1974-12, the repricing* | *40* | *54.5% / 57.8%* | *1.559 / 1.440* | *−0.816* |
| *pegged, excluded* | *139 / 40* | *1.69% / 1.07%* | *−0.368 / −0.388* | — |

Pink Sheet first, LBMA second, in every cell. **Forty months in which a US person could
not legally own the asset carry roughly 40% of the full-sample Sharpe ratio**: gold earned
54.5%/yr while equity lost 9.8%/yr, and dropping those forty months takes the Sharpe from
0.31 to **0.18**. The artefact is the same *kind* as the pre-1971 peg — a window whose
returns record something an investor could not participate in — and it is handled the same
way. **Every headline figure below is the 1975-01 one, with 1971-09 in italics beside it.**

### Admission: gold clears the overlay bar comfortably, at every exposure

Equation (4) of [`overlay_growth.py`](../../research/src/portfolio_edge/studies/overlay_growth.py),
`S_d > L·rho·sigma_p`. **Its documented misuse — that it mis-scores any sleeve above
roughly `|rho| = 0.5` — does not apply**: gold's correlation is 0.019 to 0.034 in absolute
value, an order of magnitude inside the valid range, and the code reports that check rather
than leaving it to a reader.

| Window | `S_d` net | `rho` | `sigma_p` | threshold at `L = 1` | margin | verdict |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| **1975-01…end** | 0.187 / **0.181** | −0.024 / +0.034 | 15.56% | −0.0038 / **+0.0052** | +0.191 / **+0.176** | **admitted** |
| *1971-09…end* | *0.313 / 0.298* | *−0.031 / +0.019* | *15.79%* | *−0.0050 / +0.0030* | *+0.318 / +0.295* | *admitted* |

It clears at `L = 1`, at `L = 1.5`, and at the base's own growth-optimal `L_p*` of 3.08 and
3.76. **The bar is essentially zero because the correlation is essentially zero, and gold's
net Sharpe is not zero.** On the pessimistic reading it clears by **+0.176**.

**The carry assumption is not what decides this.** Across every tier verified from a
sponsor's own SEC filing — GLDM 0.10%, SGOL 0.17%, IAU 0.25%, GLD 0.40% — the Sharpe moves
from 0.313 to 0.295 on the primary instrument. Even the 1.19% all-in of a geared futures
wrapper leaves 0.249. **A cost assumption that moves the answer by 0.06 of Sharpe cannot be
the thing carrying a verdict of +0.18.**

### Crisis-conditional correlation: the axis that breaks trend does not break gold

[Capital efficiency §9.3](capital-efficiency-and-breadth.md) shows that a diversifier's
correlation **inside equity drawdowns** is what sets the portfolio's drawdown, and that
the recommendation there fails at a crisis correlation of **+0.20**. Measured for gold on
the identical definition — months where equity sits at least the stated depth below its
running peak:

| Depth | months in / out | `rho` inside | `rho` outside | gap | gold %/mo inside | equity %/mo inside |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5% | 372 / 286 | +0.005 / +0.056 | −0.055 / −0.031 | +0.061 / +0.086 | +0.86 / +0.83 | −0.31 |
| **10%** | **294 / 364** | **−0.011 / +0.072** | −0.034 / −0.035 | +0.023 / **+0.107** | **+0.85 / +0.95** | **−0.26** |
| 20% | 181 / 477 | +0.011 / +0.071 | −0.045 / −0.007 | +0.057 / +0.078 | +0.83 / +0.76 | −0.62 |

On the holdable 1975-01 window the same figures at 10% depth are **−0.042 / +0.084**.

**Three readings, and the third is the one that matters.**

- **The repository's existing claim is confirmed, not overturned.** [The
  framework](portfolio-edge-research-framework.md) says gold "has been an average hedge…
  not a universally negative-correlation asset" and [the
  recommendation](portfolio-recommendation.md) repeats it. **Correct.** Gold's correlation
  to equity is **zero, not negative** — −0.031 to +0.034 unconditionally, −0.042 to +0.084
  inside drawdowns. Anyone holding it as a negative-beta hedge is holding something else.
- **A zero-correlation asset is not a hedge, and it is exactly what the credit term
  rewards.** `sigma_p**2 (1 − beta)` is maximised at `beta = 0`, not at `beta < 0`. Gold is
  the first candidate here to sit on that point.
- **The crisis correlation does not rise to anything like the level that breaks the trend
  recommendation.** The worst reading is **+0.084 at 10% depth on the holdable window**,
  against the **+0.20** at which §5b's boundary kills the trend overlay. And gold's mean
  return *inside* equity drawdowns is **+0.85 to +0.95%/month** while equity averages
  −0.26%/month. **This is the one axis on which gold is unambiguously stronger than the
  sleeve this repository currently recommends.**

Compounded inside each episode `docs/the-plan.md` names, Pink Sheet then LBMA:

| Episode | n | equity | gold | within-window `rho` |
| --- | ---: | ---: | ---: | ---: |
| 1973-74 | 24 | −41.7% | **+186.9% / +186.8%** | +0.164 / +0.112 |
| late-1970s inflation | 39 | +21.1% | +312.1% / +266.5% | +0.146 / +0.171 |
| 1987 | 5 | −21.8% | +7.7% / +4.6% | +0.567 / −0.604 |
| 1998 | 4 | −5.4% | +1.3% / **−1.4%** | +0.993 / +0.761 |
| 2000-02 dotcom | 30 | −44.9% | +11.3% / +16.7% | −0.157 / −0.017 |
| 2008-09 GFC | 16 | −50.3% | +24.7% / +20.4% | −0.172 / +0.021 |
| 2020 Q1 covid | 3 | −20.2% | +7.6% / +6.2% | +0.998 / +0.999 |
| 2022 inflation | 12 | −19.9% | +0.3% / +0.3% | −0.076 / +0.056 |

**Positive in seven of eight, and the eighth is −1.4% on one instrument and +1.3% on the
other.** Two qualifications that must travel: the 1973-74 and late-1970s figures are the
repricing decade and are not repeatable, and the three shortest windows carry three to
five observations, where a within-window correlation of +0.998 is arithmetic rather than
evidence.

### Marginal value under PRO-RATA funding: gold reaches the credit ceiling and still fails

**This subsection uses Experiment 010's frozen funding rule, which is the rule a physical
gold ETF imposes and the wrong rule for a financed wrapper.** Read it with the funding-rule
subsection that follows, never alone.

Experiment 010's construction, pro-rata funding, at its frozen 10% reference weight and
20% cap.

**On this experiment's own bases and its own 420-month sample, 1991-01…2025-12:**

| Base | `w` | marginal growth | `beta` | standalone alpha | credit at `w` | **ceiling at `w`** |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `global_equity_core` | 0.10 | **−0.100 / −0.084** | **+0.000 / +0.102** | **−2.95 / −2.55** | +0.217 / +0.195 | **+0.217** |
| `global_equity_core` | **0.20** | **−0.241 / −0.214** | +0.000 / +0.102 | −2.95 / −2.55 | **+0.434 / +0.390** | **+0.434** |
| `balanced_60_40` | 0.10 | +0.100 / +0.125 | +0.000 / +0.171 | +0.26 / +0.66 | +0.078 / +0.065 | +0.078 |
| `balanced_60_40` | 0.20 | +0.175 / +0.219 | +0.000 / +0.171 | +0.26 / +0.66 | +0.156 / +0.130 | +0.156 |

**The `balanced_60_40` rows are positive and they are not a finding about gold.** That base
is 40% cash, so a sleeve funded pro rata out of it is partly funded out of cash, and gold's
standalone alpha against it is *positive* (+0.26 / +0.66) purely because cash returned less
than gold. This page already records the same effect for the equity sleeves: it is a
statement about the base portfolio's equity share, not about the sleeve. **Both cells are
also below the 0.30 bar.**

**Read the first row against [the credit-ceiling table](#what-is-not-established-and-the-page-previously-overstated).**
The ceiling at `beta = 0` is `sigma_p**2 · w`, and on the primary instrument gold's credit
**is the ceiling, to three decimals**. This page's `cash_control` sat there too — but the
control supplies nothing by construction, and gold is an asset someone can buy. **The
ceiling is not a theoretical bound that no real asset approaches. A real asset sits on
it.**

**And that settles the open question [search coverage](search-coverage.md) §1.1 raised.**
That page records that the portfolio-level closure "does not survive its own experiment's
weight cap", because at 20% the ceiling of **+0.434** exceeds the frozen **0.30** bar. It
does exceed it — and **the sleeve that reaches the ceiling still fails, by −0.241 pp/yr.**

**The credit was never the binding term, and the arithmetic is weight-free.** Per unit of
weight the credit is `sigma_p**2 (1 − beta)` = **+2.171 pp/yr** at `beta = 0`, and gold's
standalone shortfall against the equity core is **−2.95 pp/yr** (LBMA: +1.949 against
−2.55). **The credit covers 74% of the shortfall and the ratio does not depend on the
weight at all** — both terms are linear in it, so the net first-order marginal is −0.078 at
10% and −0.156 at 20%, and raising the weight makes the loss larger rather than smaller.
**The closure sentence was wrong about *why*, and right about *what*.**

**Against a 100% US equity base over the longer window**, which is where the two starting
dates matter most:

| Window | `w` | marginal growth | standalone alpha | credit at `w` | ceiling |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1971-09…end | 0.10 | +0.007 / +0.043 | −2.27 / −1.77 | +0.258 / +0.243 | 0.249 |
| 1971-09…end | 0.20 | −0.049 / +0.015 | −2.27 / −1.77 | +0.516 / +0.487 | 0.498 |
| **1975-01…end** | 0.10 | **−0.423 / −0.407** | **−6.07 / −5.73** | +0.248 / +0.232 | 0.242 |
| **1975-01…end** | 0.20 | **−0.902 / −0.877** | −6.07 / −5.73 | +0.497 / +0.465 | 0.484 |

**Every reading fails clause (a)'s 0.30 pp/yr bar, and the holdable window fails it by more
than a percentage point.** The realised growth surface is flat then falling — 11.26% at
zero weight, 11.27–11.30% at 10%, 11.21–11.28% at 20%, 10.68–10.78% at 50% — while
volatility falls monotonically from 15.74% to 11.43%. **Gold buys risk reduction and pays
for it in growth**, which is the same shape as everything else in this experiment.

**And the effect is far below the instrument's floor.** The bootstrapped interval on the
arithmetic marginal at 10% weight is `[−1.035, +0.598]` against an **MDE₈₀ of 1.039 pp/yr**
over 658 months, and `[−1.314, +0.145]` against **0.939** over the holdable 618. Stationary
block bootstrap, mean block 12 months, 10,000 resamples, seed 20260817. **A null here is a
statement about resolution before it is a statement about gold** — which is the check
[the evidence base](evidence-base.md) exists to force.

### The funding rule reverses the sign, and it does not reverse the verdict

**The section above tests gold under pro-rata funding, which is Experiment 010's rule and
the wrong test for the conclusion a reader will draw from it.**
[Capital efficiency §1](capital-efficiency-and-breadth.md) is this repository's own result
that pro rata costs `a_p − sigma_p**2` — **+6.69 pp/yr on this window**, an amount
containing nothing about the sleeve — and §6a is its own result that the funding rule is a
property of the *ticker*. A verdict quoted from the pro-rata table alone is a verdict about
GLDM. **This subsection was added after a red team pointed that out, and it changes the
sign of the answer.**

Three bars, per unit of gold notional, 1975-01…2026-06, 618 months. Gross gold excess of
cash is 3.14% / 3.48%; charge **40 bp** of gold-futures financing
([structural and tax-aware edges](structural-and-tax-edges.md), an upper bound transferred
from published research on the contracts and **not** read from any fund filing) and
**23.9 bp** of fee — GDE's 0.20% on capital converted to notional at its measured
`d = 0.8363` — to give `a_net` of **2.50% / 2.84%**.

| Funding rule | per unit notional | at `w = 0.10` | at GDE's own `w = 0.8363` |
| --- | ---: | ---: | ---: |
| **pure overlay**, equation (1) | +2.563 / **+2.740** | +0.256 / +0.274 | +2.144 / +2.292 |
| **GDE as measured**, equation (7) | +1.347 / **+1.525** | +0.135 / +0.152 | +1.127 / +1.275 |
| **pro rata**, equation (2) | −4.126 / **−3.949** | −0.413 / −0.395 | −3.450 / −3.302 |

**GDE is not a pure overlay and equation (7) is why.** §6a.2 measures its legs from its own
Form N-PORT at 2026-02-28: **84.80% equity and 83.63% gold-futures notional**, so
`delta = (1 − b)/d = 0.182` and **it forfeits 18.2% of the funding-rule gap** — it sells
fifteen cents of equity to buy eighty-four cents of gold. That costs 1.22 pp/yr per unit of
notional, which is larger than gold's entire net excess return over cash.

**So the sign reverses: −0.41 pp/yr becomes +0.14 to +0.27 at the reference weight.** That
is the finding, and it is stated plainly because this repository has made the opposite
error — leaving a sleeve condemned by a hurdle it should never have faced.

**And now the realised path, because a first-order bar at `w = 0` is not a result.**
Equation (5) decides: at matched volatility the variance terms cancel and the higher Sharpe
ratio wins outright, so every row is reported against the base levered to the same
volatility as well as against the unlevered base.

| Portfolio, 1975-01…2026-06 | geometric | volatility | Sharpe | **vs leverage-matched** | MDE₈₀ |
| --- | ---: | ---: | ---: | ---: | ---: |
| equity only, 1.00× | 12.78% | 15.56% | **0.586** | — | — |
| **pure overlay, `w = 0.10`** | 13.06 / 13.07% | 15.60 / 15.73% | 0.600 / 0.597 | **+0.224 / +0.182** | **0.63 / 0.73** |
| pure overlay, `w = 0.8363` | 14.22 / 14.00% | 20.40 / 22.38% | 0.549 / 0.513 | **−0.743 / −1.620** | 5.67 / 6.55 |
| **GDE as measured** | 13.04 / 12.85% | 18.70 / 20.75% | **0.525 / 0.487** | **−1.133 / −2.048** | 5.77 / 6.67 |

**Three readings, and the second and third are why the verdict survives its own
correction.**

- **At a small weight the sign is positive and the magnitude is not resolvable.** +0.224 /
  +0.182 pp/yr against the leverage-matched control, below the frozen **0.30** bar and
  below its own **0.63–0.73** minimum detectable effect. It is a positive number that this
  instrument cannot distinguish from zero.
- **At the weight the only gold overlay wrapper actually runs, the matched-volatility
  control rejects it outright.** GDE's implied portfolio carries a Sharpe ratio of
  **0.525 / 0.487 against equity's 0.586** — it is *worse* on the quantity equation (5)
  says is the only one that matters. Gold's own Sharpe of 0.13–0.19 is roughly a third of
  equity's, so past a small weight the overlay buys growth with volatility rather than with
  diversification, and the control catches exactly that. **The closed-form bar is a
  derivative at `w = 0` and says nothing about `w = 0.84`**; the difference is the
  `w**2 sigma_d**2 / 2` term, worth about 0.9 pp/yr at GDE's weight.
- **In a taxable account the measured tax number exceeds every positive cell.** §6a.4
  computes GDE's SEC-standardised after-tax drag at **1.53 pp/yr on capital** since its
  2022-03-17 inception — 18.63% before tax against 17.10% after. Gold futures are §1256
  contracts marked to market every 31 December, so there is nothing to defer. **1.53
  exceeds +0.22, and it exceeds the +1.13 to +1.28 the closed form gives at GDE's own
  weight.** Held in a shelter the drag is zero and the sleeve competes with the trend
  overlay for the same scarce capacity.

**The pro-rata framing was the wrong test and the correction is material. The conclusion is
unchanged and is now much better supported.**

### Does gold add to trend, or substitute for it?

The standing question is whether *several* diversifying engines can be combined, and
[capital efficiency §3](capital-efficiency-and-breadth.md) answers it pessimistically:
effective breadth of 4.06 exists on paper across trend, BAB, short-term reversal and
accruals, and **six of those seven engines cannot be bought.** Gold is the first candidate
to arrive with both a measurable series and a cheap financed wrapper, so the pairing is
worth measuring rather than assuming.

The trend leg is the one **this repository builds itself** — no vendor series — from
[`time_series_momentum`](../../research/src/portfolio_edge/studies/time_series_momentum.py)
on four instruments, imported from the module that produces §7's published ladder so the
two cannot diverge. 605 joint months, 1975-01…2025-05, gold charged the same 40 bp
financing and 23.9 bp fee, trend charged 95 bp.

| Leg | excess | volatility | Sharpe | `rho` to equity | **`rho` to equity in drawdowns** |
| --- | ---: | ---: | ---: | ---: | ---: |
| equity | 8.87% | 15.62% | 0.568 | 1.000 | — |
| trend | 5.35% | 12.18% | **0.440** | −0.006 | **−0.239** |
| gold | 2.12% / 2.52% | 16.15 / 18.46% | **0.131 / 0.136** | −0.026 / +0.027 | **−0.042 / +0.084** |

**The correlation between trend and gold is +0.141 / +0.072.** They are not the same
engine, and that is the whole question:

| Set | k | **effective breadth `k / (1 + (k−1) rho_dd)`** |
| --- | ---: | ---: |
| trend alone | 1 | 1.00 |
| **trend + gold** | 2 | **1.75 / 1.87** |
| trend + BAB + STR + accruals (§3) | 4 | 4.06 — **and three of the four cannot be bought** |

**Gold is the first addition to trend that raises effective breadth using an engine anyone
can actually hold.** 1.75 is not 4.06, and it is the only one of the two that exists.

Realised, against the leverage-matched control, same 605 months, 60 bp borrow charged on
gross notional above 1.0:

| Portfolio | geometric | volatility | Sharpe | **vs leverage-matched** | MDE₈₀ | max drawdown |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| equity only | 12.51% | 15.62% | 0.568 | — | — | −50.3% |
| **+ 30% trend** (the recommendation) | 14.04% | 16.02% | 0.643 | **+1.198** | 1.45 | −44.8% |
| + 10% gold alone | 12.68 / 12.70% | 15.66 / 15.77% | 0.576 / 0.574 | +0.129 / +0.102 | 0.64 / 0.73 | −49.2 / −49.3% |
| **+ 30% trend + 10% gold** | 14.20 / 14.23% | 16.11 / 16.20% | **0.649 / 0.647** | **+1.298 / +1.285** | 1.67 / 1.68 | **−43.5 / −43.7%** |
| + 30% trend + 30% gold | 14.43 / 14.48% | 16.76 / 17.17% | 0.641 / 0.633 | +1.230 / +1.118 | 2.60 / 2.76 | **−41.0 / −41.6%** |

**Gold adds rather than substitutes, and the increment is smaller than the instrument can
see.** Adding 10% gold notional to the recommended 30% trend overlay moves the
matched-volatility gap from **+1.198 to +1.298 / +1.285** — an increment of **+0.09 to
+0.10 pp/yr against an MDE₈₀ of 1.67.** The unshrunk growth-optimal vector puts trend at
3.53 and gold at 0.47 / 0.55, which is a plug-in optimum from forecasts and a statement
about the covariance estimate rather than a recommendation.

**The drawdown moves further than the return does, and that is the same pattern trend
shows.** −44.8% to −43.5% at a 10% gold overlay and to **−41.0%** at 30% — a 3.8 pp
improvement on the deepest episode in the window, while the growth gap *falls* from +1.298
to +1.230. **The best return weight and the best drawdown weight are different weights**,
and neither difference clears its own resolution floor.

**The one comparison that is not marginal.** [Capital efficiency §5b](capital-efficiency-and-breadth.md)
makes the whole recommendation conditional on the overlay's correlation to equity *inside
equity drawdowns* staying below **+0.20**, and §9.3 shows a +0.30 crisis correlation costs
3.6 pp of drawdown at the recommended weight. **Gold's crisis-conditional correlation is
−0.042 / +0.084 and trend's is −0.239 on the same 217 crisis months.** A second overlay
whose crisis correlation is also near zero *and* which is near-uncorrelated with the first
is worth more than its standalone Sharpe ratio suggests — which is the breadth identity's
entire content. **Gold's standalone Sharpe of 0.13 is what disqualifies it, not its
correlation, and it is the one input that a longer window could change.**

### The vehicle, and the one place gold beats the recommended sleeve

**A physical-gold ETF is a pro-rata vehicle**, so the bar it faces is the one gold fails.
SPDR Gold Trust's own 10-K (FY ended 2025-09-30, filed 2025-11-25): *"The Trust does not
hold or employ any derivative securities… Each Share represents a proportional interest…
in the gold and any cash held by the Trust."* A dollar of GLD is a dollar not invested
elsewhere.

**An overlay vehicle for gold exists, is cheap, and is not a fund the funding-rule
argument had to assume.** WisdomTree Efficient Gold Plus Equity Strategy Fund (**GDE**),
inception 2022-03-17, **0.20% expense ratio**, $595.1m net assets at 2026-05-31: *"Under
normal circumstances, the Fund will have approximately equal exposure to U.S.-listed gold
futures contracts and U.S. equity securities."* Its own N-PORT for 2026-05-31 measures
85.7% of NAV in equity and 88.1% in gold-futures notional — **~174% total notional per
dollar held.** Two others exist and are worse fits: First Trust **ESBG** (0.95%, $2.2m,
inception 2025-11-18 — a sub-$3m fund with real liquidation risk) and Return Stacked
**RSSX** (0.67%, $66.3m), whose stacked dollar is a *risk-parity blend of gold and
bitcoin* that cannot be dialled to pure gold.

**This matters for [capital efficiency §3](capital-efficiency-and-breadth.md)'s central
structural claim.** That page's finding is that "the fund shelf binds before the evidence
does" — three of seven factor families have no vehicle of any kind, and the one BAB fund is
$362m. **For gold the shelf does not bind.** The overlay wrapper costs 0.20% against
trend's assumed 1.45%, and this repository has already measured gold-futures financing at
**≤40 bp** ([structural and tax-aware edges](structural-and-tax-edges.md)), so the all-in
overlay cost is on the order of **0.60%/yr against trend's 2.05%.**

**The tax answer is worse than equity's and it decides placement.** For the bullion trusts,
verified from the statute and from four sponsors' own filings:

| | Rate | Source |
| --- | ---: | --- |
| Gold ETF long-term gain, US individual | **28% + 3.8% NIIT** | IRS Pub. 550: *"collectibles gain… metal (such as gold, silver, and platinum bullion)"*, Table 4-4 rate 28%. 26 U.S.C. §1(h)(5) cross-references §408(m) **without §408(m)(3)**, so the bullion carve-out does not rescue it |
| The funds say so themselves | 28% | GLD, IAU, GLDM and SGOL 10-Ks each carry *"gains recognized by individuals from the sale of 'collectibles,' including gold bullion, held for more than one year are taxed at a maximum rate of 28%, rather than the 20% rate"* |
| Equity long-term gain, for comparison | 20% + 3.8% | same table |
| Inside an IRA | **not the 28% rate** | GLD and IAU both hold IRS private letter rulings that purchase by an IRA "will not be treated as the acquisition of a collectible". Distributions are then **ordinary income** (Pub. 590-B), which at the top bracket is worse than 28%; in a Roth, untaxed. **The PLR numbers are not disclosed in any fund document read, and a PLR binds only its requester** |

**The overlay wrapper is a structurally different after-tax asset, and it is not the better
one.** A reader would expect a RIC holding §1256 gold futures to deliver 60/40 treatment.
**It does not.** GDE holds its gold through a **Cayman Islands subsidiary** capped at 25% of
total assets — the §851(b)(2) qualifying-income structure — and WisdomTree's own SAI states
that *"Subpart F income and GILTI are treated as **ordinary income, regardless of the
character of the CFC's underlying income**"*, with subsidiary losses neither flowing through
nor carrying forward. **Every dollar GDE has distributed in all three fiscal years since its
2022 inception was ordinary income**, only **28.9%** of it at qualified-dividend rates, and
its measured drag is **1.53 pp/yr**. The collectibles rate does *not* reach it: "collectibles"
appears **zero times in every filing WisdomTree Trust has ever made**, against 76 hits for
SPDR Gold Trust.

| | Annual drag | Rate on the distribution | Rate on selling the shares | Deferrable? |
| --- | ---: | --- | --- | --- |
| **GLDM** and the other bullion trusts | ~0 | n/a — they distribute nothing | **28% + 3.8%** | **yes, indefinitely** |
| **GDE** | **1.53 pp/yr** | **ordinary**, 28.9% at QDI rates | 20% + 3.8% | **no** |

**Neither route dominates and the physical one is the tax-favoured one for a long holder.**
The bullion trust pays a higher rate on a gain it can defer for decades; the overlay pays an
ordinary rate every year on income it cannot defer. Against
[structural and tax-aware edges](structural-and-tax-edges.md) §4, where deferral is the
largest single number, that ordering is the reverse of what the fee comparison suggests.

**And there is still no plain futures vehicle.** **Invesco DB Gold (DGL) liquidated in March
2023** (Form 8-K 2023-01-23; the shares "cease trading… after market close on March 3,
2023"), and the surviving geared fund UGL is 2× leveraged, costs 1.19% all-in, issues
**K-1s**, and its own prospectus warns that "swap agreements and non-currency forward
contracts are **generally not** Section 1256 Contracts".

### The verdict

**Gold is dominated, and the reason is its standalone Sharpe ratio rather than its
correlation, its cost, its data or its vehicle.** All four of those are better than any
candidate this repository has tested. On the 1975-01 window it earns **0.18** of Sharpe
against equity's **0.59**, and everything else follows from that one number.

Stated against each of the four tests, on the holdable window and the pessimistic
instrument:

| Test | Result |
| --- | --- |
| **Admission**, equation (4) | **passes**, by +0.176 at every exposure, at a correlation an order of magnitude inside the equation's own validity range |
| **Marginal value, pro rata** — the rule GLDM imposes | **fails**, −0.395 pp/yr at the reference weight against a 0.30 bar |
| **Marginal value, overlay** — the rule GDE imposes | **sign reverses to positive**, +0.182 pp/yr against the leverage-matched control at the reference weight — **and that is below the 0.30 bar and below its own 0.73 detection floor**. At GDE's own 0.84 notional the matched-volatility control rejects it outright, because the portfolio's Sharpe falls to 0.487 against equity's 0.586 |
| **Breadth beside trend** | **adds rather than substitutes** — correlation +0.072, effective breadth 1.00 → 1.87, matched gap +1.198 → +1.285, drawdown −44.8% → −43.7%. The increment is +0.09 pp/yr against an MDE₈₀ of 1.68 |
| **After tax** | **the physical route defers and the overlay route cannot.** GLDM pays 28% + 3.8% on a gain it can hold for decades; GDE distributes 100% ordinary income annually, 28.9% of it at QDI rates, measured at **1.53 pp/yr** — larger than every positive cell above |

**What survives is a risk statement, not a return statement**, which is the same shape as
every trend result on
[capital efficiency](capital-efficiency-and-breadth.md): the drawdown improvements are
monotone and consistent across weights while the return gap is not resolvable anywhere.

**Three things would have to be true for this verdict to be wrong**, and they are worth
naming because none of them is a data problem:

1. gold's forward Sharpe ratio is materially above the 0.18 measured over 618 months —
   the estimate whose interval is widest here;
2. the overlay is held in a shelter, so GDE's measured **1.53 pp/yr** distribution drag is
   zero — the drag is **ordinary Subpart F income from its Cayman blocker**, not §1256
   60/40, and the shelter it needs is the same one the trend overlay already competes for;
3. it is held at a weight small enough for the matched-volatility control to accept, which
   is far below the weight the only gold overlay wrapper actually runs at.

**Nothing is promoted.** [Decision 0004](../decisions/0004-no-sleeve-promoted.md) stands.
This is exploratory work on a licence-restricted benchmark with an assumed carry cost and
an assumed financing spread, no specification was frozen before the numbers were seen, its
effect sits below its own detection floor under every funding rule, and its most favourable
window is forty months in which the asset was illegal to own.

**Reproduce with**
`cd research && uv run python -m portfolio_edge.studies.gold_sleeve`. Manifests:
`research/data-manifests/worldbank_pinksheet_gold_monthly.json`, `lbma_gold_pm.json`,
`lbma_gold_am.json`. Retrieval date **2026-08-17**.

---

## Why the certainty equivalent could not be left deciding

The control was frozen with an answer known in advance: *cash added to an equity core and
funded from US equity must show a materially negative marginal figure. If it does not, the
machinery is wrong and no other figure may be read.*

| `cash_control`, by funding leg | CE, γ=3 | Growth, γ=1 | De-risking |
| --- | ---: | ---: | ---: |
| `pro_rata` | **+0.166** | **−0.643** | **+0.809** |
| `named_leg` (US equity) | −0.026 | **−0.803** | +0.777 |
| `cash` | −0.007 | −0.007 | **−0.0005** |

**The growth reading passes the machine check on every leg. The certainty equivalent passes
it only under `cash` funding** — the degenerate case where the sleeve *is* the funding leg.
**The reward appears exactly when the sleeve removes equity and nowhere else.**

The second-moment model predicts part of this and not all of it. Raising `gamma` from 1 to
3 triples the credit term and moves the control's *predicted* marginal from −0.582 to
−0.148 pp/yr, an allowance of +0.434. The realised allowance is +0.809, so **+0.376 pp/yr
is a left-tail reward the variance never sees**: exact CRRA utility over only 35 calendar
observations weights the realised worst years far more heavily than a variance does, and
cash is what was not in equities during them. **Note that even at `gamma = 3` the *model*
says the cash sleeve costs 0.148 pp/yr. Only the exact utility over 35 points makes it look
profitable.**

A reader who prefers the certainty-equivalent reading concludes that this experiment is
void and no figure may be read. **That reader reaches the same decision about every
sleeve**, because every sleeve is rejected on the frozen falsifier either way. **The choice
of reading cannot promote anything.**

---

## Hostile tests

Marginal growth, `global_equity_core`, pro-rata, net-pessimistic, pp/yr. The two eras are
diagnostics and never independent observations.

| Sleeve | Baseline | Double costs | Delay 1 month | Best year removed | 1991–2008 | 2009–2025 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `emerging_small_value` | +0.543 | +0.496 | +0.731 | +0.314 (1993) | +0.950 | +0.092 |
| `us_small_value` | +0.392 | +0.347 | +0.641 | +0.269 (2000) | +0.742 | +0.006 |
| `us_momentum_long_only` | +0.269 | +0.226 | +0.471 | +0.216 (1998) | +0.407 | +0.117 |
| `trend_aqr` | +0.258 | **−0.009** | +0.231 | +0.021 (2008) | **+1.243** | **−0.823** |
| `emerging_momentum_overlay` | +0.202 | −0.051 | +0.160 | +0.027 (2008) | +0.648 | −0.292 |
| `dev_ex_us_momentum_overlay` | +0.007 | −0.220 | −0.030 | −0.216 (2008) | +0.586 | −0.632 |
| `long_duration_treasury_proxy` | −0.385 | −0.404 | −0.383 | −0.616 (2008) | +0.182 | −1.010 |

**Every sleeve with a negative beta collapses in the second era and every one of them loses
its best year to 2008.** Doubling costs alone takes trend and both positive momentum
overlays below zero. **The sleeves whose value is a *credit* are the sleeves whose credit
was earned in one crisis.**

**The optimal weight is a selected maximum, and its interval says so.** The constrained
optimum is chosen from the same sample it is evaluated on, so its naive gain is positive by
construction on a noisy surface. Only an interval that re-selects the weight inside every
bootstrap replicate carries that selection effect:

| Sleeve | In-sample optimum | Re-selected gain, median | Re-selected 95% | Replicates choosing zero weight |
| --- | ---: | ---: | --- | ---: |
| `us_small_value` | 0.20 | +0.753 | `[0.000, 1.838]` | 6.7% |
| `emerging_small_value` | 0.20 | +1.054 | `[0.000, 2.485]` | 6.6% |
| `dev_ex_us_small_value` | 0.20 | +0.040 | `[0.000, 0.999]` | **45.0%** |

Every lower bound is exactly zero, which is what the long-only boundary produces on a flat
noisy surface. **Read the median as the gain a searcher who optimises in sample would
report, not as a gain available to anyone.**

---

## Verified, assumed, open

**Verified.** The credit ceiling `sigma_p**2` at `beta = 0`, algebra confirmed numerically
by the control landing on it. That the metric change moves exactly one thing — the two runs
share inputs, vintages, portfolios, sleeves, costs, window, eras and seed, and a unit test
compares the two committed specifications field by field. That the machinery reports a
correctly negative growth marginal for a sleeve supplying nothing, on all three funding
legs.

**Assumptions.** Base portfolio weights are frozen and round, not optimised. The fee tiers
are **this repository's assumptions** about an accessible implementation and not any
provider's disclosure — the underlying Ken French series carry no cost at all. The 10%
reference weight and 20% cap were chosen before any result, neither optimised, **and the
first is now known to be load-bearing.** Long-short sleeves are made funded by adding cash
to a self-financing factor return, which **understates their cost**, since the French files
contain no shorting cost, no borrow and no capacity limit.

**Not an investable backtest.** No figure here is an achievable investor outcome. Ken
French's files are paper portfolios; the trend series is maintained by a firm that sells
the strategy; the long-duration sleeve is modelled from a yield and is not a total-return
history at all.

**Open.**

1. **The reference weight and funding rule are load-bearing and were not varied in the
   headline.** The credit ceiling at the 20% cap exceeds the bar. This is round two's first
   item.
2. **Gold is no longer the open question and is now [a section](#gold-tested).** What
   remains open from it is narrower: whether a *joint* weighting of gold, trend and equity
   does anything the one-sleeve-at-a-time design cannot see, and whether the overlay
   funding rule — which gold clears and pro rata does not — should be the primary arm of
   the successor specification rather than its robustness arm.
3. **A measured bond sleeve is now tested and an investable one is now possible.** As of
   2026-08-17 the `GS10` proxy is superseded by Goyal–Welch `ltr` and `corpr` as a
   measurement and by eighteen funds' Item B.5 returns as an investable series
   ([alternative sleeves audit §8](alternative-sleeves-audit.md)). Clause (u5) still binds
   this frozen run, because its leg is still the proxy. **What is open is whether the
   successor specification should carry a bond leg in the *base* rather than as a sleeve**,
   which is the question [setting the equity share](setting-the-equity-share.md) asks.
4. **The credit is a difference of two covariances from 420 months.** A credit that moves
   by more than itself when the correlation moves by 0.10 is not a finding, **and several
   of these do.**
5. **The Holm family of ten is a lower bound on the correction the whole search requires.**
   It counts neither the three funding legs, the two base portfolios, the three cost
   columns, the two eras, nor the twelve specifications frozen before it.

**Reproducibility.**
`cd research && uv run python -m portfolio_edge.experiments.exp_010_marginal_sleeve_value --view-results`.
Source vintages are pinned by sha256 and a mismatch aborts. Retrieval date **2026-08-12**,
seed 20260909.

---

## Consequence for this repository

1. **The standalone dismissals stand, and two are strengthened.** Clause (b) fired for
   `us_small_value` and `emerging_equity` against the equity core, and every long-only
   equity sleeve's credit is negative against `balanced_60_40`. **Judged marginally, an
   equity tilt inside an equity portfolio is worth *less* than the standalone chain said,
   not more.**
2. **The portfolio-level closure is withdrawn as previously stated and replaced by a
   re-specification.** The ceiling at the 20% cap exceeds the bar; a first-order derivative
   is not the portfolio view; and pro-rata funding is the least favourable rule for a
   diversifier. [Search coverage](search-coverage.md) §5 sets out what the successor must
   freeze.
3. **The ceiling is reachable and reaching it is not enough, and that is now measured
   rather than argued.** Gold sits at `beta = +0.000` against the equity core and takes the
   whole `sigma_p**2 w` credit — **+0.434 pp/yr at the 20% cap, above the 0.30 bar** — and
   its marginal growth there is **−0.241 pp/yr**. **Per unit weight the credit is +2.171
   and the standalone shortfall is −2.95, so the credit covers 74% of it and the ratio is
   weight-free**: raising the weight scales both terms and makes the loss larger. **The successor specification must therefore stop treating the credit ceiling
   as the binding constraint.** Setting the bar from the ceiling, as search coverage §5
   proposes, makes the bar reachable; it does not make the alpha term go away.
4. **The funding rule, not the weight, is the choice worth re-specifying.** Gold clears
   the overlay bar by +0.18 of Sharpe on the worst reading and fails the pro-rata bar on
   every reading. The gap between them is 5.17–6.69 pp/yr and contains nothing about gold.
   **The successor should make overlay funding the primary arm.**
5. **Every future specification names `decision_gamma`.** Omitting it silently inherits the
   pre-0008 meaning.
6. **A control with no value by construction is now the pattern**, not an optional extra.
   It cost one cell of compute, it cannot promote anything because it is outside the Holm
   family, and **it is the only reason this error was found rather than published.**
7. **Nothing is promoted.** [Decision 0004](../decisions/0004-no-sleeve-promoted.md) stands
   in full.
