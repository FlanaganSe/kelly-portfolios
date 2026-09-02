# Five tilts the recommendation never priced

**Question.** The recommended portfolio was assembled by correcting the investor's own list
of eight tickers. It was never asked whether *better* tilts existed on the shelf. Four
candidates were never scored against it: **AVDV** (developed ex-US small value), **AVUV**
(US small value), **MTUM** (US momentum) and **QVAL** (Alpha Architect's concentrated US
value, which is not on the shelf at all). A fifth, **ITAN** (Sparkline's intangible-adjusted
US value), arrived from [the discovery sweep](discovery-sweep-2026-09.md) and is scored in
§7 against the vector as published. What does each add to the portfolio actually held,
after everything it actually costs?

**Decision it informs.** Whether to change the construction as it stood when this page was
written — RSST 25%, VTI 25%, VTV 15%, VXUS 25%, IDMO 5%, AVES 5% — and by how much. **AVDV
has since been adopted at 10%** and the resulting portfolio has been tested as one object in
[the final construction test](final-construction-test.md); every figure below is still
measured against the pre-AVDV portfolio, which is what makes it a marginal figure. It also settles the question that
decides whether international value re-enters the portfolio at all: two *large*-cap
international value funds were dropped for delivering measurably negative returns, and
AVDV is small-cap. Is that distinction real?

**Out of scope.** Whether any factor premium exists
([factor persistence](factor-persistence.md)), what the trend sleeve is worth
([trend](trend-marginal-value.md)), and the weights themselves
([the recommendation](portfolio-recommendation.md), which this page does not edit).

`as of 2026-08-23`. **`exploratory`.** No specification was frozen before these numbers were
seen and no experiment is registered for them. Reproduce with
`cd research && uv run python -m portfolio_edge.studies.untested_tilts`; the arithmetic is
in [`untested_tilts.py`](../../research/src/portfolio_edge/studies/untested_tilts.py) and
the filing reads in
[`_untested_tilts_tables.py`](../../research/src/portfolio_edge/studies/_untested_tilts_tables.py).

---

## Conclusion

1. **AVDV is worth adding, and it is the only one of the four that is.** Funded out of
   VXUS at 5% of capital it changes expected portfolio return by about **+0.16% a year,
   plausibly −0.06% to +0.38%**; at 10%, **+0.32% a year, −0.12% to +0.77%**. That rests on
   exposure, cost and overlap, none of which involves its measured extra return — which is
   not distinguishable from zero and is not used here.
2. **The small-versus-large distinction in international value is not established, and
   AVDV must not be recommended on it.** On the 55 months DFIV and AVIV impose, all four
   large-cap international value funds read −2.3 to −2.9 with intervals excluding zero
   while AVDV reads +1.8. On the 78 months the two *older* large-cap funds also cover, the
   same two funds read −1.0 and −1.7 and neither excludes zero. **The negative result is
   substantially a property of the window, not of the funds' capitalisation.** And over the
   months AVDV and DFIV both existed, their plain returns differed by **−0.30 ± 5.16
   pp/yr** — AVDV did not out-return DFIV at all; it out-returned the *model's prediction*
   for it.
3. **AVUV is not worth adding to this portfolio.** Against VTI it is worth about
   **−0.01% a year** once the US value line already held is accounted for: its active leg
   is +0.430 correlated with VTV's own and +0.455 with the whole active position, and the
   exposure it adds beyond VTV is 87% size, on a premium of +0.33 pp/yr against a floor of
   2.47. Replacing VTV with it outright is
   **+0.09% a year at 15%, range −0.42% to +0.60%** — a coin flip dressed as a decision.
4. **MTUM is not worth adding, and turnover rather than overlap is what kills it.** It
   delivers **UMD +0.437 [+0.316, +0.559]** over VTI, which is real. It also files
   **116%/yr of portfolio turnover** against VTI's 3%, costing 1.13 to 1.92 pp/yr — more
   than the entire gross exposure gain of +1.78 pp/yr on the US momentum premium, which is
   itself +4.19 against a detection floor of 7.27. Net: **−0.03% a year at a 5% weight,
   range −0.18% to +0.13%.** The overlap with IDMO is real but secondary: the two funds'
   active legs correlate **+0.554**, so two momentum tickers are worth **1.29 independent
   bets out of 2**.
5. **QVAL is the clearest verdict on the page and it is negative.** Its facts are
   established from its own filing: 28 bp, and **332%/yr of portfolio turnover**. That is
   3.29 to 5.59 pp/yr of trading cost against a gross factor gain of +1.1 pp/yr. At a 5%
   weight it is **−0.30% a year, range −0.50% to −0.10%** — the only one of the four whose
   portfolio effect the data can resolve, and it is resolved in the wrong direction.
6. **The tax objection to momentum is false on the filed evidence, and it is the surprise
   of this page.** MTUM's own SEC-standardised after-tax table shows a distribution drag of
   **0.31 pp/yr against VTI's 0.42** over the same five years — the momentum fund is
   **11 bp/yr more tax-efficient than the total-market fund** despite turning over its
   whole portfolio each year, because the ETF in-kind redemption shield does the work.
   AVDV against VXUS is **−0.01 pp/yr**: parity. Tax does not decide any of these four.
7. **ITAN in place of five points of VTV is not worth making, and the sign does not depend
   on the sample.** Over VTV it delivers **UMD −0.221 [−0.328, −0.114]** and **RMW −0.381
   [−0.521, −0.241]**, both resolved, and HML −0.154 against a floor of 0.338, unresolved;
   it costs 50 bp against VTV's 3 and turns over 31% against 8%. The move reads
   **−0.10% a year at 5%, range −0.28% to +0.07%**, and is negative in all four premium
   scenarios including the null. Its overlap with VTV's active leg is +0.009 over the full
   sample, which is what the sweep hoped for, and +0.80 in the five worst equity months,
   which is not. §7.

---

## 1. The method, proved before it was used

Every published loading this page touches was first refitted on **its own published
window** and checked against the shelf. This is what separates "a different answer" from
"a different method".

| Fund | Panel | Published window | Loadings checked |
| --- | --- | --- | ---: |
| AVDV, DISV, DFIV, AVIV, IVLU, IDMO | developed ex-US | 45 to 77 months | 13 |
| VTI, VTV, AVUV, MTUM, RPV | US | 72 months | 7 |

**Largest gap across all twenty: 0.0020**, and that one is RPV's SMB, which the shelf
publishes to one decimal place as +0.2 against a refit of +0.198. Every other loading
reproduces to within 0.0005. **SPMO is deliberately absent from this check**: the shelf
records its UMD loading with `window: null`, and a loading with no window cannot be
reproduced or compared, so it is fitted from its own filings on a stated window instead. The fund return series is Form N-PORT Item
B.5 — the fund's own filed monthly total return, net of its own fees, with distributions
reinvested — read by the same module Experiments 008, 009, 012 and 013 use. No price feed
is involved, which is why [decision 0002](../decisions/0002-no-research-grade-free-price-source.md)
does not reach it; see [loading comparability](loading-comparability-and-wrapper-exposure.md)
§1 for the argument in full.

**Two departures from the published numbers, both stated here rather than buried.**

- **A delivered exposure is fitted from the difference series.** Rather than fitting fund
  and incumbent separately and subtracting two coefficients whose standard errors do not
  combine, the *difference* of the two funds' filed returns is regressed on the panel
  directly. The coefficients are then the delivered exposures and the intercept is the
  extra return, each with an interval that means something.
- **The shelf's published alphas for DFIV and AVIV do not reproduce exactly.** Every
  loading does, to 0.0005, on the identical window with the identical estimator; the
  alphas come back **−3.88 and −2.88** against the published −4.11 and −3.13. The gap is
  0.23 and 0.25 pp/yr, well inside both funds' own detection floors, and nothing on this
  page turns on it — but it is unexplained and it is recorded.

**One gap in the source, and it moves a window.** QVAL has no Form N-PORT filing for the
quarter ending 2021-09-30, so its history has a three-month hole. A Newey-West covariance
laid across a hole treats two months a quarter apart as neighbours, so QVAL is fitted on
its longest gapless run, **54 months, 2021-10…2026-03**, and not on the 75-month span its
first and last filings suggest.

---

## 2. The crux: does large-cap international value's negative result reach small-cap?

This is the question that decides AVDV, and the answer is **no, but not for the reason it
first appears.**

### On the window the young funds impose

DFIV and AVIV began filing in 2021, so any comparison including them is a comparison over
2021-10 onwards. Every fund below is fitted on those 55 months, on the developed-ex-US
FF5+UMD panel, against the one-month bill.

| Fund | | Extra return, pp/yr | 95% interval | Smallest detectable |
| --- | --- | ---: | :---: | ---: |
| VXUS | international core | +0.30 | [−1.58, +2.18] | 2.69 |
| VEA | developed core | −0.27 | [−1.83, +1.28] | 2.22 |
| IVLU | **large** value | **−2.64** | [−4.63, −0.65] | 2.85 |
| EFV | **large** value | **−2.69** | [−4.42, −0.96] | 2.47 |
| DFIV | **large** value | **−2.85** | [−5.49, −0.21] | 3.78 |
| AVIV | **large** value | **−2.25** | [−3.98, −0.52] | 2.48 |
| **AVDV** | **small** value | **+1.84** | [−1.00, +4.67] | 4.05 |

Four large-cap funds from three different sponsors, all negative, all excluding zero. The
one small-cap fund is positive. The difference regressions confirm it with much more power,
because the common factor noise cancels:

| Difference | Extra return | 95% interval | Smallest detectable |
| --- | ---: | :---: | ---: |
| AVDV − DFIV | **+4.69** | [+2.26, +7.12] | 3.47 |
| AVDV − AVIV | **+4.09** | [+1.63, +6.55] | 3.52 |
| AVDV − IVLU | **+4.48** | [+2.00, +6.95] | 3.53 |
| AVDV − EFV | **+4.53** | [+1.94, +7.11] | 3.69 |

On this window the distinction is real as arithmetic and comfortably resolvable.

### On a longer window it evaporates

IVLU and EFV are old enough to be measured over 78 months. Refit them there and the
result changes:

| Fund | 55 months, 2021-10…2026-04 | 78 months, 2019-10…2026-03 |
| --- | ---: | ---: |
| IVLU | **−2.64** [−4.63, −0.65] | −0.99 [−2.65, +0.67] |
| EFV | **−2.69** [−4.42, −0.96] | −1.69 [−3.39, +0.02] |
| AVDV | +1.84 [−1.00, +4.67] | +0.68 [−1.88, +3.25] |
| AVDV − IVLU | **+4.48** [+2.00, +6.95] | +1.67 [−1.64, +4.99] |
| AVDV − EFV | **+4.53** [+1.94, +7.11] | +2.37 [−0.66, +5.41] |

**The two funds that can be measured on both windows lose their negative result on the
longer one, and so does the small-minus-large difference.** Add twenty-three months of
2019-10…2021-09 and nothing excludes zero any more. That is the same defect
[loading comparability](loading-comparability-and-wrapper-exposure.md) §4 records for the
US value shelf, appearing here in an *alpha* rather than a loading: the published verdict
was a statement about which months each fund happened to exist for.

### And even where it resolves, it is not a return difference

The most useful line on this page needs no factor model at all. Over the 55 months AVDV
and DFIV both filed:

> **AVDV − DFIV: −0.30 ± 5.16 pp/yr.** AVDV − AVIV: +1.70 ± 4.59 pp/yr.

**AVDV did not out-return the large-cap funds. It out-returned the model's prediction for
it**, because the model charges it for +0.56 of SMB and +0.38 of RMW that it holds and they
do not. That is a statement about how well a six-factor model fits a small-cap
international portfolio, not about money.

**So the crux resolves as follows.** Small-cap international value did not escape a fate
that befell large-cap international value, because there was no resolvable fate: on the
longest window available the large-cap funds' negative returns are not distinguishable from
zero, and on the shorter window the small-cap advantage is a model residual rather than a
return. **AVDV's case must rest on something else, and it does.**

---

## 3. What each candidate actually delivers, and what it costs

Every exposure below is `fund − incumbent`, fitted on the difference series, on one window,
with the interval and the smallest exposure the window could have detected.

| | AVDV over VXUS | AVUV over VTI | AVUV over VTV | MTUM over VTI | QVAL over VTI |
| --- | ---: | ---: | ---: | ---: | ---: |
| Months | 78 | 78 | 78 | 78 | 54 |
| Window | 2019-10…2026-03 | 2019-10…2026-03 | 2019-10…2026-03 | 2019-10…2026-03 | 2021-10…2026-03 |
| HML | **+0.464** [+0.302, +0.626] | **+0.513** [+0.420, +0.606] | +0.221 [+0.051, +0.390] | −0.028 [−0.149, +0.094] | **+0.503** [+0.262, +0.743] |
| SMB | **+0.639** [+0.505, +0.773] | **+0.899** [+0.777, +1.022] | **+0.874** [+0.685, +1.063] | −0.042 [−0.212, +0.127] | +0.409 [+0.152, +0.667] |
| RMW | **+0.703** [+0.429, +0.977] | +0.246 [+0.061, +0.432] | +0.137 [−0.078, +0.352] | −0.126 [−0.312, +0.059] | +0.396 [+0.120, +0.672] |
| CMA | +0.089 [−0.150, +0.328] | −0.060 [−0.222, +0.102] | −0.242 [−0.459, −0.025] | +0.043 [−0.156, +0.242] | −0.123 [−0.405, +0.159] |
| UMD | +0.006 [−0.067, +0.079] | +0.002 [−0.055, +0.058] | −0.005 [−0.127, +0.118] | **+0.437** [+0.316, +0.559] | −0.010 [−0.201, +0.180] |
| Extra return | +0.85 [−1.59, +3.29] | +1.30 [−1.27, +3.87] | +2.69 [−1.02, +6.39] | −2.86 [−7.71, +1.99] | −0.96 [−6.92, +5.00] |
| Smallest detectable | 3.49 | 3.67 | 5.29 | 6.93 | 8.52 |

**Not one of the five extra-return figures is distinguishable from zero.** Each smallest
detectable effect is two to nine times the estimate beside it. **No verdict on this page
uses any of them**, and that is deliberate: across dozens of funds the best-looking number
is luck, and AVDV's headline +2.47 on the shelf sits inside a ±3.96 band on a window chosen
by nobody.

### Cost, from each fund's own filing

| | Fee | Turnover | Incumbent's turnover | Incremental cost, pp/yr |
| --- | ---: | ---: | ---: | ---: |
| AVDV | 36 bp | **4%/yr** | VXUS 4% | **0.25 to 0.35** |
| AVUV over VTI | 25 bp | 6%/yr | VTI 3% | 0.25 to 0.29 |
| AVUV over VTV | 25 bp | 6%/yr | VTV 8% | 0.215 to 0.223 |
| MTUM | 15 bp | **116%/yr** | VTI 3% | **1.25 to 2.06** |
| QVAL | 28 bp | **332%/yr** | VTI 3% | **3.54 to 5.86** |

Fees and turnover are from each fund's own Form 497K: iShares 2025-11-28 for MTUM (fiscal
year to 2025-07-31), Avantis 2025-12-31 for AVDV and AVUV, Alpha Architect 2026-02-01 for
QVAL, Vanguard 2026-04-28 for VTI and VTV and 2026-02-27 for VXUS. The cost range carries
two widths at once: the trading-cost coefficient's own 1.0-to-1.7 calibration, and the fee
against the net cost.

> **Net cost has since been read, and it moved nothing.** Form N-CEN securities-lending
> income is now on the shelf for AVDV (5.97 bp, so 30.03 bp net), AVUV (0.46, so 24.54),
> VTV (0.30, so 2.70) and four other tilt funds, beside VTI's 1.84 and VXUS's 3.57. **No
> fund on this shelf has negative net cost** and no verdict on this page changes, because
> every centre figure below is quoted at the *worse* end of its cost bracket and that end is
> the gross fee. The gain shows up only in the better end — AVDV's incremental cost bracket
> widens downward from 0.31 to 0.25 — and the arithmetic is in
> [the final construction test](final-construction-test.md) §2. MTUM's and QVAL's lending
> remains unread; both are rejected on turnover, which lending cannot reach. The code
> ([`FundCost.net_cost_bp`](../../research/src/portfolio_edge/studies/untested_tilts.py))
> still raises rather than letting a fee be quoted where a net cost belongs.

### Tax, and the assumption it overturns

The investor's money will be spent in retirement, so there is no §1014 step-up to forgive a
turnover-heavy fund's realised gains, and roughly a third of the portfolio is taxable. The
natural worry is that MTUM's 116% turnover is a tax disaster.

**It is not.** From each fund's own Form N-1A standardised after-tax table, all over the
same five years to 2024-12, at the highest historical individual federal rates:

| Fund | Before tax | After taxes on distributions | Drag | Against its incumbent |
| --- | ---: | ---: | ---: | ---: |
| VTI | 13.80% | 13.38% | 0.42 | — |
| VXUS | 4.32% | 3.53% | 0.79 | — |
| **MTUM** | 11.77% | 11.46% | **0.31** | **−0.11 pp/yr vs VTI** |
| **AVUV** | 14.12% | 13.68% | **0.44** | **+0.02 pp/yr vs VTI** |
| **AVDV** | 6.35% | 5.57% | **0.78** | **−0.01 pp/yr vs VXUS** |

A momentum fund that rotates its whole portfolio each year distributes *less* taxable income
than a total-market index fund, because an ETF's in-kind redemption mechanism removes
appreciated lots without a sale and momentum names carry low dividend yields.
[Structural and tax edges](structural-and-tax-edges.md) already records that "the ETF
in-kind shield does not survive its turnover" for a high-turnover momentum fund at a 5%
weight; on the *distribution* measure, for this fund, the filed evidence says it does. The
two are compatible — that finding is about ranking the shelter queue, and this is about
what the fund distributes — but the tax objection to MTUM in a taxable account is not
supported by MTUM's own filing.

Three limits. The table measures distributions, not the tax on eventually selling. It
assumes the top federal bracket throughout. And no after-tax table was read for QVAL, whose
332% turnover decides it without one.

---

## 4. The sleeve edge, and what survives what is already owned

The line is the repository's: `sum_k (h_fund,k − h_incumbent,k) × premium_k − cost`, with
**no capture fraction anywhere in it** — the code refuses the argument. Four premium
scenarios, none of them a forecast, all carried from
[stacking](stacking-and-effective-breadth.md) §2.

Per dollar of sleeve, pp/yr, the range spanning the cost bracket:

| | own-panel | pooled | half | null |
| --- | ---: | ---: | ---: | ---: |
| **AVDV over VXUS** | **+3.60 to +3.64** | +3.91 to +3.94 | +1.63 to +1.66 | −0.35 to −0.31 |
| AVUV over VTI | +0.82 to +0.86 | +3.06 to +3.10 | +0.27 to +0.30 | −0.29 to −0.25 |
| AVUV over VTV | +0.40 | +1.38 | +0.09 | −0.22 |
| MTUM over VTI | **−0.28 to +0.53** | +0.69 to +1.50 | −1.17 to −0.36 | −2.06 to −1.25 |
| QVAL over VTI | **−4.98 to −2.66** | −2.44 to −0.12 | −5.42 to −3.10 | −5.86 to −3.54 |

**Which premia can be signed matters more than which fund is picked.** AVDV's edge is
mostly developed-ex-US HML, **+5.07 pp/yr against a 3.67 floor** — one of the two premia
this repository can sign on its own panel. MTUM's is entirely US UMD, **+4.19 against a
7.27 floor** — the premium is smaller than the smallest effect its own test could see.
AVUV's marginal exposure over VTV is 87% SMB, **+0.33 against a 2.47 floor**. Two of the
three candidates are buying an exposure to something the evidence cannot establish exists.

### Conditioning on what is already held

The held active position is `0.25(RSST − VTI) + 0.15(VTV − VTI) + 0.05(IDMO − VXUS) +
0.05(AVES − VXUS)`, built from the funds' own filed returns. Correlations are measured, not
modelled. `marginal edge = candidate edge − beta × held edge`, delegating to the same
`alpha_k / omega_k` [stacking](stacking-and-effective-breadth.md) §3 defines.

| Candidate | Own tracking error | ρ to held | Standalone edge | **Marginal edge** |
| --- | ---: | ---: | ---: | ---: |
| **AVDV over VXUS** | 5.59 | +0.396 | +3.60 | **+3.23** |
| AVUV over VTI | 13.38 | +0.455 | +0.82 | **−0.20** |
| AVUV replacing VTV | 11.85 | −0.041 | +0.40 | **+0.60** |
| MTUM over VTI | 8.98 | +0.164 | −0.28 | **−0.53** |
| QVAL over VTI | 11.93 | +0.505 | −4.98 | **−5.99** |

54 months, 2021-10…2026-03, own-panel premia at the worse end of each cost bracket. On the
30 months that include the trend wrapper the ordering is unchanged.

Pairwise, each candidate's active leg against each held one, on the longest run of months
each pair shares:

| | VTV | IDMO | AVES | RSST |
| --- | ---: | ---: | ---: | ---: |
| **AVDV** | +0.333 | **−0.124** | **−0.104** | +0.140 |
| AVUV | **+0.430** | −0.305 | −0.001 | −0.017 |
| MTUM | −0.094 | **+0.554** | −0.177 | −0.021 |
| QVAL | **+0.524** | +0.089 | −0.042 | +0.214 |

**AVDV keeps about nine tenths of its standalone case.** It is +0.333 correlated with the
US value line and **negatively** correlated with both international positions already held.
It is not the same bet as anything in the portfolio.

**AVUV loses its whole case to VTV.** Its active leg is +0.455 correlated with the held
position, most of that with VTV's own +0.430, and once that is netted off its marginal edge
is *negative*. This is the investor's own objection made exact: a sleeve that looks
acceptable alone can add nothing in a portfolio. **Replacing** VTV instead of sitting beside
it is a different and slightly better proposition, and it is still small.

**QVAL is worse conditioned than standalone**, because it is +0.505 correlated with what is
already owned and its standalone edge is already negative.

---

## 5. Momentum in two regions

[Factor persistence](factor-persistence.md) measures one factor across three regions as
worth 1.35 to 1.55 independent bets out of 3, from the research factors. The same question
can be asked of the two *funds*, from their filed returns:

> **MTUM over VTI against IDMO over VXUS: ρ = +0.554 ± 0.219 over 80 months** (2019-08…
> 2026-03). Two momentum tickers are worth **1.29 independent bets out of 2**.

Beside it, for scale: AVDV's active leg against IDMO's is **−0.124**, and AVUV's is
**−0.305**. Adding a second region of momentum buys about a quarter of a bet; adding a
different style buys more than a whole one. That is [stacking](stacking-and-effective-breadth.md)'s
"geography is nearly free breadth, style is real breadth" reproduced on live funds rather
than on research factors.

**But overlap is not what decides MTUM.** At a 5% weight the portfolio-level cost of the
+0.554 correlation is small — the marginal edge falls from −0.28 to −0.53 pp/yr per dollar
of sleeve. The turnover charge alone is 1.13 to 1.92 pp/yr. **MTUM would fail on cost even
if IDMO were not held.**

---

## 6. The recommendation, in plain percentages

Centre is the marginal edge on the own-panel premia at the worse end of the cost bracket.
The range carries the premia's own standard error at 95%. The null column is what the
candidate costs if every premium turns out to be zero.

| Candidate | Weight | Expected change in portfolio return | Range | If every premium is zero |
| --- | ---: | ---: | :---: | ---: |
| **AVDV** | **5%** | **+0.16% a year** | −0.06% to +0.38% | −0.02% |
| **AVDV** | 10% | +0.32% a year | −0.12% to +0.77% | −0.03% |
| AVUV over VTI | 5% | −0.01% a year | −0.23% to +0.21% | −0.01% |
| AVUV replacing VTV | 15% | +0.09% a year | −0.42% to +0.60% | −0.03% |
| MTUM | 5% | −0.03% a year | −0.18% to +0.13% | −0.10% |
| QVAL | 5% | **−0.30% a year** | −0.50% to −0.10% | −0.29% |

### AVDV: add it

**Take 5% of capital out of VXUS and put it in AVDV.** Ten percent is defensible and is not
what this page recommends, for two reasons stated below.

- **Why it earns its place.** It delivers **HML +0.464, SMB +0.639 and RMW +0.703** over
  VXUS, all three with intervals excluding zero on 78 months, and its HML sits on the
  developed-ex-US premium that clears its own floor. It files **4%/yr of turnover, the
  lowest of any factor product in either audit**, so essentially none of its cost is
  trading. Its distribution tax drag is a hair *below* VXUS's. And it is uncorrelated with
  — slightly negatively correlated with — both international positions already held.
- **Which account.** **A sheltered one: the Roth, or the rollover IRA.**
  [Structural and tax edges](structural-and-tax-edges.md) finds that every international
  fund outranks every US equity fund in the shelter queue for an investor of this shape,
  and AVDV's 0.78 pp/yr distribution drag is the highest of any candidate here. It is not
  disqualifying in taxable — it is at parity with the VXUS it replaces — but shelter is
  strictly better, and a 5% line fits inside a third of the portfolio easily. If the
  employer plan is part of the tax-deferred third, AVDV will not be on its menu; that is
  the captive-menu problem [the recommendation](portfolio-recommendation.md) records, and
  the answer is the Roth or the rollover.
- **Why not 10%.** Two reasons and neither is a measurement. Nearly half of AVDV's gross
  edge is the RMW and SMB legs, whose premia are **+1.68 against a 2.62 floor** and
  **+0.49 against a 2.83 floor** — unsignable. And its +0.703 RMW over VXUS is partly an
  artefact of VXUS's own −0.275 RMW on a developed-ex-US panel, which is emerging markets
  read through a developed lens; priced against VEA instead, the RMW delta is +0.416 and
  the sleeve edge falls from +3.60 to +2.99 pp/yr. Five percent is the size at which the
  unsignable half of the case does not matter.

### AVUV: do not add it

Not because it is a bad fund — its delivered exposure is the largest on the US shelf — but
because **this portfolio already holds VTV at 15% and 87% of what AVUV adds beyond VTV is
size**, on a premium of +0.33 pp/yr against a 2.47 floor. Its active leg is +0.455
correlated with what is held, and conditioning on that turns +0.82 into −0.20. Replacing
VTV outright is worth about +0.09% a year on a range from −0.42% to +0.60%, at 11.9 pp/yr of
tracking error against 7.6 for VTV. **That is more risk for a number the data cannot
resolve.** If the investor wants US small value on non-evidential grounds, replacing VTV is
the right way to buy it and 15% is the right size; it is not an improvement this page can
demonstrate.

### MTUM: do not add it

**116%/yr of turnover against VTI's 3% costs 1.13 to 1.92 pp/yr, and the exposure it buys
is worth +1.78 pp/yr gross on a premium of +4.19 against a 7.27 detection floor.** The
turnover charge alone can exceed the entire gain. Add the +0.554 correlation with IDMO and
the case is −0.03% a year at a 5% weight. The tax objection turns out to be wrong — MTUM is
the most tax-efficient fund on this page — and it does not rescue the trading cost.

**If US momentum is wanted anyway, SPMO is the fund and it is also not worth adding.** Its
facts have since been read: 13 bp, **44%/yr of turnover** against MTUM's 116%, 12.93 bp of
net cost, a distribution tax drag below VTI's, and UMD **+0.395 [+0.281, +0.508]** delivered
over VTI on 78 months — fitted on a stated window, because the shelf's published +0.414
carries none and therefore cannot be compared with anything. At a 5% weight it is **+0.02% a
year, plausibly −0.14% to +0.18%**. It beats MTUM on every knowable dimension and still
cannot be told from zero, because the premium it buys is +4.19 pp/yr against a 7.27 pp/yr
floor and its active leg is **+0.626 correlated with IDMO's** — a tighter overlap than
MTUM's. See [the final construction test](final-construction-test.md) §4.

### QVAL: do not add it, and the facts are established

QVAL is Alpha Architect's U.S. Quantitative Value ETF, CIK 1592900, series S000046016,
inception 2014-10-21, benchmarked to the Solactive GBS United States 1000 Index. From its
summary prospectus dated **2026-02-01**: total annual fund operating expenses **0.28%**
(management fee restated to current), and **portfolio turnover 332% of average portfolio
value** in the most recent fiscal year. On its longest gapless run of filings it delivers
**HML +0.503, SMB +0.409, RMW +0.396** over VTI — a genuinely deep value tilt — for a gross
factor gain of about +1.1 pp/yr on the own-panel premia against **3.29 to 5.59 pp/yr of
trading cost**. At a 5% weight that is −0.30% a year on the whole portfolio, and it is the
only figure on this page whose sign the data can resolve. It also duplicates what is held:
+0.505 correlated with the existing active position, +0.754 with AVUV's active leg.

**It should be added to the shelf as `rejected`, which is done.**

---

## 7. ITAN: intangible-adjusted value in place of five points of VTV

`as of 2026-09-02`. **`exploratory`.** No specification was frozen before these numbers
were seen. Each run is recorded in the ledger under `study_itan_substitution`; reproduce
with `cd research && uv run python -m portfolio_edge.studies.itan_substitution`. The
arithmetic is in
[`itan_substitution.py`](../../research/src/portfolio_edge/studies/itan_substitution.py)
and the filing reads in
[`_itan_substitution_tables.py`](../../research/src/portfolio_edge/studies/_itan_substitution_tables.py).

**The question.** [The discovery sweep](discovery-sweep-2026-09.md) proposes VTV 15
becoming VTV 10 + ITAN 5, on the hope that a value fund which counts intangibles is a
different bet from the value funds already held, and names the measurement: ITAN's
correlation with the held value and momentum legs, and a regression on the French five
factors plus momentum to see whether its value exposure is positive at all or whether the
label covers growth. Both are measured here, and the substitution is scored the way §3 to
§6 score the candidates above: on delivered exposure, cost and overlap, never on the
measured extra return, which at 54 months is not a number.

### Conclusion

**Do not make the substitution.** Moving five points of capital from VTV to ITAN changes
expected portfolio return by about **−0.10% a year, range −0.28% to +0.07%**, and the sign
holds under **every premium scenario the repository carries**: own-panel, pooled, half and
null. It holds because the exposures the move buys are *short* the two priced US factors
that decide it. Over VTV, ITAN delivers **UMD −0.221 [−0.328, −0.114]** against a floor of
0.153 and **RMW −0.381 [−0.521, −0.241]** against 0.200, both resolved. Its value
exposure over VTV is **−0.154 [−0.390, +0.083]** against a floor of 0.338, unresolved,
which is the polite way of saying the window cannot tell whether it has less value
exposure than VTV or the same. On its own ITAN is a mild value fund on the French
definition, **HML +0.133 [+0.050, +0.215]**, about a third of VTV's on the same months,
with a beta of 1.05, short profitability and short momentum: value in the label, growth
in the loadings. The sweep's hoped-for overlap is real and irrelevant. Its active leg is
**+0.009** correlated with VTV's over the full sample, and a negative edge does not
become positive by being uncorrelated with what is held. In the five worst VTI months of
the window the same correlation is **+0.80 [−0.29, +0.99]**.

**Sized implication for the published vector.** RSST 30 / VTI 19 / VTV 15 / VXUS 16 /
AVDV 10 / IDMO 5 / AVES 5 stands. The proposed RSST 30 / VTI 19 / VTV 10 / VXUS 16 /
AVDV 10 / IDMO 5 / AVES 5 / ITAN 5 would give up about 0.10% a year of expected return and
cut the active position's tracking error by 0.13 to 0.38 pp/yr, because it removes a
third of the value tilt and replaces it with a leg that is nearly uncorrelated with the
rest. That is a smaller tilt, not a broader one. At 10 and 15 points the loss scales:
−0.21% and −0.31% a year.

### What was filed

ITAN commenced 2021-06-28 and has filed **56 whole months, 2021-07 to 2026-05**, after the
launch stub. The trust (CIK 1592900, the same one QVAL files under) reports quarters
ending February, May, August and November, and no filing covers the quarter ending
2021-11-30, so **2021-09 to 2021-11 have no filed return**. The longest gapless run is
**54 months, 2021-12 to 2026-05**, and every fit below is on it. The sweep's "60 filed
months (2021-07 to 2026-06)" was the span between first and last filing, not the run.
VTV and VTI file through 2026-06; AVUV and AVDV through 2026-05; IDMO and VXUS through
2026-04, which is why the overlap table stops a month earlier.

### Loadings

Each column is a fund less a fund on the filed returns, regressed on the US FF5+UMD panel
with Newey-West errors at six lags. ITAN alone is its excess return over the one-month
bill. The market leg is VTI's own filed return, not the French market factor, so that a
fund is compared with the fund the investor would otherwise hold; the French factor is a
control.

| | ITAN alone | ITAN over VTV | ITAN over VTI | VTV over VTI, same months |
| --- | ---: | ---: | ---: | ---: |
| Months | 54 | 54 | 54 | 54 |
| Mkt-RF | **+1.048** [+1.000, +1.096] | **+0.217** [+0.140, +0.294] | +0.045 [−0.005, +0.095] | **−0.172** [−0.220, −0.123] |
| HML | **+0.133** [+0.050, +0.215] | −0.154 [−0.390, +0.083] | **+0.126** [+0.044, +0.208] | **+0.280** [+0.061, +0.499] |
| SMB | −0.061 [−0.157, +0.034] | −0.146 [−0.294, +0.002] | −0.066 [−0.162, +0.029] | +0.080 [−0.035, +0.194] |
| RMW | **−0.177** [−0.307, −0.047] | **−0.381** [−0.521, −0.241] | **−0.197** [−0.322, −0.073] | **+0.184** [+0.121, +0.247] |
| CMA | −0.011 [−0.130, +0.109] | **−0.246** [−0.480, −0.012] | −0.033 [−0.151, +0.084] | +0.213 [−0.016, +0.442] |
| UMD | **−0.192** [−0.269, −0.116] | **−0.221** [−0.328, −0.114] | **−0.195** [−0.268, −0.122] | +0.026 [−0.036, +0.089] |
| Extra return, pp/yr | +0.14 [−4.02, +4.30] | +0.70 [−3.76, +5.17] | +0.30 [−3.71, +4.31] | −0.40 [−3.20, +2.40] |
| Smallest detectable extra return | 5.95 | 6.38 | 5.73 | 4.00 |

The substitution's delivered exposure is the **ITAN over VTV** column, and each gap sits
beside the smallest gap the window could have found at 80% power:

| ITAN over VTV | Delivered | Floor | Reading |
| --- | ---: | ---: | --- |
| HML | −0.154 | 0.338 | unresolved; less value than VTV or the same |
| SMB | −0.146 | 0.211 | unresolved |
| RMW | **−0.381** | 0.200 | resolved; sells profitability |
| CMA | −0.246 | 0.335 | unresolved |
| UMD | **−0.221** | 0.153 | resolved; sells momentum |
| Extra return | +0.70 pp/yr | 6.38 pp/yr | unresolved by a factor of nine, and unused |

The fitted alpha of +0.70 pp/yr over VTV is reported because the investor asked that a
young fund not be dismissed for a short record. It is not dismissed for its record; its
record is not consulted. A window that could only have detected 6.38 pp/yr cannot say
anything about 0.70, in either direction.

### Overlap

ITAN's active leg (ITAN less VTI) against each held leg (VTV and AVUV less VTI; AVDV and
IDMO less VXUS), on the 53 months every pair shares, 2021-12 to 2026-04, and in the five
worst VTI months of that window (2022-01, 2022-04, 2022-06, 2022-09, 2025-03). Intervals
are Fisher-z at 95%.

| Against | Full sample | Worst decile |
| --- | ---: | ---: |
| VTV | **+0.009** [−0.26, +0.28] | **+0.797** [−0.29, +0.99] |
| AVUV | +0.324 [+0.06, +0.55] | +0.654 [−0.54, +0.97] |
| AVDV | −0.001 [−0.27, +0.27] | +0.401 [−0.74, +0.95] |
| IDMO | −0.300 [−0.53, −0.03] | −0.417 [−0.95, +0.74] |

The sweep's threshold was an excess-return correlation with VTV below 0.2, and the full
sample clears it. Two things stop that from mattering. The first is that the worst-decile
figure rests on five months and its interval spans almost the whole line, so the
diversification is established only in the months when it is not needed. The second is
the −0.300 against IDMO, which is the fund's short momentum leg read from the other side:
ITAN is anti-correlated with the momentum sleeve because it sells what that sleeve buys,
which is the same finding §3 of [the final construction test](final-construction-test.md)
records for RPV.

### Cost and facts

| | Value | Source |
| --- | ---: | --- |
| Fee | 50 bp | Form 497K dated 2025-09-30 |
| Securities lending, median of 5 fiscal years | 0.048 bp | Form N-CEN, fiscal years to 2022-05 through 2026-05 (0.023, 1.356, 0.087, 0.048, 0.001 bp) |
| Net cost | 49.95 bp | against VTV's 2.70 |
| Portfolio turnover | 31%/yr | 497K, fiscal year to 2025-05-31; VTV 8% |
| Incremental cost over VTV | 0.70 to 0.86 pp/yr | fee gap plus 23 points of excess turnover at k = 1.0 to 1.7 |
| Net assets | $117.45m | issuer page, 2026-09-01 |
| Holdings | 163 | issuer page, 2026-09-01; prospectus floor 50 |
| 30-day median bid-ask spread | 0.09% | issuer page, 2026-09-01 |
| Premium to NAV | −0.05% | issuer page, 2026-09-01 |
| Distributions | quarterly | issuer page |

**Is the value definition disclosed? In concept, not in formula.** The summary prospectus
says the sub-adviser buys stocks that appear cheap relative to a proprietary measure of
"intangible-augmented intrinsic value", which adds intangible value from intellectual
property, brand, human capital and network effects to tangible assets, scored with natural
language processing over patents, job postings and earnings calls. The weights, the
scoring and the rebalancing rule are not published, there is no index, and the prospectus
expects "significant exposure to companies in the information technology sector". The
fund is a discretionary quantitative strategy under a value name, which is consistent with
the loadings.

### The substitution across four premium scenarios

`weight × Σ_k (h_ITAN,k − h_VTV,k) × premium_k − weight × cost`, with no capture fraction
anywhere in it. Per dollar moved and for the whole portfolio at five points of capital,
the range spanning the cost bracket:

| Scenario | Per dollar moved, pp/yr | Portfolio at 5%, % a year |
| --- | ---: | ---: |
| own-panel | −2.08 to −1.92 | **−0.104 to −0.096** |
| pooled | −4.28 to −4.11 | −0.214 to −0.206 |
| half | −1.47 to −1.31 | −0.074 to −0.065 |
| null | −0.86 to −0.70 | −0.043 to −0.035 |

On the own-panel premia the gross exposure change is **−1.22 pp/yr per dollar**, of which
**−0.93 is momentum** (−0.221 × 4.19), −0.24 is value and −0.05 is size; profitability and
investment carry no own-panel premium and contribute nothing. The costs then add 0.70 to
0.86. Momentum decides it, and the momentum premium is the one this repository cannot
sign: +4.19 pp/yr against a 7.27 floor. That cuts both ways and does not rescue the
substitution, because if the premium is zero the move still costs 0.04% a year.

### Given what the vector already holds

The page's rule for a replacement is that the displaced position is dropped from the held
set first, so the five points of ITAN are scored against RSST 30 / VTV 10 / AVDV 10 /
IDMO 5 / AVES 5, from the funds' own filed returns. A position scored against a held set
that still contains it reads as pure overlap, which is an artefact and not a finding.

| Held set | Months | Held tracking error | ρ(ITAN over VTI, held) | Standalone edge | Marginal edge | Active tracking error, published to proposed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| with the trend wrapper | 31, 2023-10 to 2026-04 | 3.59 | +0.128 | −1.61 | **−1.74** | 3.76 to 3.63 |
| without it | 53, 2021-12 to 2026-04 | 1.29 | −0.088 | −1.61 | **−1.43** | 1.67 to 1.29 |

Conditioning changes nothing that matters: a sleeve whose standalone edge is negative in
every scenario stays negative once what is held is netted off. The tracking-error column is
the one number in ITAN's favour, and it is not a diversification gain. The active position
gets smaller because a third of the value tilt is removed, which is what selling VTV for a
fund with a third of its value loading does.

### The headline, in plain percentages

Centre is the own-panel premia at the worse end of the cost bracket, fitted on the ITAN
less VTV series directly. The range carries the premia's own standard error at 95%, summed
rather than added in quadrature as everywhere on this page; the loadings' own sampling error
is in the tables above and is not folded in.

| Capital moved from VTV to ITAN | Expected change in portfolio return | Range | If every premium is zero |
| ---: | ---: | :---: | ---: |
| **5%** | **−0.10% a year** | −0.28% to +0.07% | −0.04% |
| 10% | −0.21% a year | −0.55% to +0.14% | −0.09% |
| 15% | −0.31% a year | −0.83% to +0.21% | −0.13% |

### Verified, interpretation, open

**Verified here.** Every loading, interval and floor above, from Form N-PORT Item B.5 and
Ken French's US files on the 54-month gapless run. Every correlation, from the funds' own
filed returns. ITAN's series and class identifiers from the SEC's ticker map; its fee and
turnover from its own Form 497K; its lending income and average net assets from five
fiscal years of the trust's Form N-CEN; the three-month hole in its filings. The internal
check that the difference fitted directly on ITAN less VTV (−2.081 pp/yr per dollar) agrees
with the two funds' separate edges over VTI (−1.605 and +0.473, difference −2.078).

**Interpretation.** That ITAN is a growth fund with a value name rests on reading a beta
of 1.05 with negative RMW and UMD loadings through the French lens; the fund's own thesis
is that the French value definition is what is wrong. That the worst-decile correlation of
+0.80 means the diversification fails when needed rests on five months. That the momentum
premium is worth +4.19 pp/yr is an input carried from [stacking](stacking-and-effective-breadth.md)
§2, and the substitution's centre figure is mostly that input times −0.221.

**Open.**

1. **Whether an intangible-adjusted value factor is a premium in its own right.** This
   repository prices five French factors and momentum and does not price the Eisfeldt,
   Kim and Papanikolaou factor the fund is built on. If that factor were established as a
   premium distinct from HML, RMW and UMD, and ITAN loaded on it, the scoring here would
   be charging the fund for its exposures without crediting its thesis. Nothing here
   measures that; a long intangible-value factor series is the data it would take.
2. **54 months.** Shorter than one value cycle, and §2 of this page is a demonstration of
   what twenty-three extra months can do to a conclusion. The sign of the substitution
   does not rest on the sample, but the resolved RMW and UMD loadings do.
3. **The five worst months.** A worst-decile correlation on five observations is a
   direction, not a number; the next reading is at 80 filed months, when the decile holds
   eight.

---

## Verified, assumed, open

**Verified here.** Eighteen published loadings reproduced on their own windows to within
0.0005 across two panels. Every delivered exposure, extra return, interval and smallest
detectable effect above, from Form N-PORT Item B.5 and Ken French's factor files. Every
correlation, from the funds' own filed returns. Fee, turnover and standardised after-tax
returns for AVDV, AVUV, MTUM, QVAL, VTI, VTV and VXUS from their own Form 497K filings,
each dated above. QVAL's missing 2021-Q3 filing.

**Since closed.** A 10% AVDV line has been through the construction tournament, at
[the final construction test](final-construction-test.md) §1: two whole portfolios at
identical gross notional differing only in AVDV give **+0.28 pp/yr [+0.05, +0.56] against a
0.29 floor**, and the unlevered tilt-only pair gives +0.29. Two independent routes to the
same number as this page's +0.32% at a 10% weight.

**Assumed.**

- **Every premium is an input**, carried across four scenarios; nothing here estimates one.
- **Trading cost is `k × turnover` basis points at `k` from 1.0 to 1.7.** On MTUM and QVAL
  the choice between the two ends is larger than the whole edge, and both are reported.
  The coefficient is the repository's, calibrated in `portfolio_edge.core.costs`, and it
  has never been validated on a mega-cap US momentum universe where the real figure is
  probably nearer the low end.
- **Securities lending is now read for five of the seven funds** and each candidate is
  still charged its gross fee at the centre, which is unfavourable to every candidate. MTUM
  and QVAL remain unread.
- **The premium standard errors are backed out of published MDE80 figures** and summed
  rather than added in quadrature, which is the perfectly-correlated bound and the wider of
  the two defensible readings.
- **AVES's edge (+1.408) and the trend leg's (+1.0) are carried** from
  [stacking](stacking-and-effective-breadth.md) rather than refitted here.
- **The held position's tracking error is measured over 54 months without the trend
  wrapper and 30 with it.** Both are reported; neither changes an ordering.

**Open.**

1. **Why the shelf's DFIV and AVIV alphas differ from a refit by 0.23 and 0.25 pp/yr.**
2. **Whether AVDV's +0.703 RMW over VXUS is exposure or panel mismatch.** Against VEA it is
   +0.416. The gap is VXUS's emerging sleeve read through a developed-ex-US panel, and the
   clean fix is an emerging-inclusive panel that this repository does not have.
3. **Everything here rests on 54 to 78 months.** That is shorter than one value cycle, and
   the crux of §2 is precisely a demonstration of what twenty-three extra months can do to
   a conclusion.

## What this does not establish

- **Not** that AVDV's measured extra return is positive. It is +0.68 [−1.88, +3.25] on 78
  months and is not used anywhere in the recommendation.
- **Not** that international value "works". §2 establishes the opposite of a clean story:
  the negative result for large-cap international value is a window effect, and the
  small-cap advantage over it is a model residual.
- **Not** that AVUV, MTUM, QVAL or ITAN are bad funds. Each is scored against *this*
  portfolio at *this* moment; AVUV against a portfolio with no US value line would read
  differently, and ITAN against a portfolio with no momentum sleeve would lose the IDMO
  reading but not its sign.
- **Not** that intangible-adjusted value is not a premium. §7 prices ITAN on the factors
  this repository can price and finds it short two of them; it does not measure the factor
  the fund is built on.
- **Not** a promotion. Nothing here is `production-eligible`, no specification was frozen,
  and no experiment is registered; the ITAN runs are ledgered as a study.
