# The recommended portfolio: what to hold, which account holds it, and what each line buys

**Question.** Given everything this repository has measured, what is the
best-supported portfolio a US investor can actually implement — named funds, weights,
and account placement — and what is each decision buying, at what confidence?

**Decision it informs.** What construction the repository puts its name to, and what
it refuses to. It is the first page here to name funds and weights.
[Decision 0006](../decisions/0006-reference-portfolio-without-promotion.md) records
why that is now permitted and what the word "recommended" is allowed to mean.

**Out of scope.** Personalised advice, a forecast of any market, and the promotion of
any sleeve. **Nothing here reached `production-eligible`, and nothing here is claimed
to beat an index.** Every fund-specific fact below (fee, spread, share class, tax
table) is dated and must be re-checked before it is used.

`as of 2026-08-12`, US federal individual investor, state tax excluded and additive.

---

## Conclusion, stated directly

1. **The portfolio is the control plus placement.** A cheap, broad, long-only, fully
   invested global equity/bond portfolio ([decision 0003](../decisions/0003-cheap-broad-market-control.md)),
   held in the right accounts, with lot discipline, and not traded. That is not a
   default chosen for want of anything better in the abstract — it is the only
   construction whose delivery is contractual rather than statistical.
2. **The reliable edge is ~109 bp/yr against the portfolio the investor would
   otherwise have owned, and it is bought by fund choice, account placement and not
   trading.** Against about 46 bp of combined tracking error it reaches 90%
   confidence in about **3.5 months** and 99% in about **twelve**
   ([structural and tax-aware edges](structural-and-tax-edges.md)). Its largest new
   component is decaying while being measured.
3. **Every tilt is smaller, slower, and not signable within a lifetime.** The best
   case for a 20%-of-portfolio small-value tilt is **+15 bp/yr against 140 bp of
   tracking error** — a 0.72 probability of being ahead after thirty years and 139
   years to 90% confidence. On the defensible reading of the two terms that decide
   it, the same tilt is **negative**. §5 shows all four corners.
4. **The equity/bond split is the investor's to set and nothing here can set it.**
   It is the largest single decision in the portfolio and the only one the evidence
   is silent on. Everything below it follows from evidence.
5. **The single account-placement result that is not the textbook one:** at a 15% or
   18.8% qualified-dividend rate, **emerging-market equity belongs in the taxable
   account and US equity in the shelter**. The break-even is 21.51%, which falls
   between two live US rates. §3 shows the arithmetic.
6. **Managed futures is the one sleeve whose account decides its sign.** Its
   distribution tax drag is 2.09 pp/yr on the only product that delivers the
   exposure, against an 0.85% fee — and **zero in a tax-deferred account**.

---

## 1. The recommendation, concretely

### 1.1 The one parameter that changes the answer

Risk capacity — horizon, liabilities, cash flows and the drawdown that would force a
sale. Four variants, differing **only** in the equity share. No evidence in this
repository sets it; the repository's declared objective is net geometric growth as a
*preference* justified by Breiman's theorem, not as a proof
([edge decomposition](expected-edge-decomposition.md) §1.3), and the horizon and
liability model remain unchosen (framework open decision 1).

**[Setting the equity share](setting-the-equity-share.md) is the canonical page for
everything below.** It works the arithmetic through: the growth-optimal weight and the
forecast it needs, the parameter-free curve showing that being at half the
growth-optimal exposure costs only a quarter of the peak excess growth, why the
zero-leverage rule means the objective alone returns a corner solution of 100% equity,
what the estimation error is worth, and the drawdown at every equity share. It does not
set the split either, and it explains what would have to be supplied before anything
could.

The anchor for the choice is a measured drawdown, not a risk questionnaire: the US
total market returned **10.80%/yr geometric at 15.40% volatility with a −50.3%
maximum drawdown and 72 months under water** over 1963-07…2025-12
([Exp 007](long-only-capture.md#the-small-value-corner)). Set the equity share at the
level whose worst case you would hold through, then stop. That page's
[drawdown ladder](setting-the-equity-share.md#5-the-drawdown-anchor-which-is-the-operational-form-of-the-answer)
gives the same figure at every rung between 0% and 100%.

| Variant | Applies when | Equity | Bonds |
| --- | --- | ---: | ---: |
| **A — long horizon** | 20+ years, no liability inside it, contributions continuing, a −50% equity fall changes no plan | 90–100% | 0–10% |
| **B — mixed** | 10–20 years, or a known liability inside the horizon | 70–80% | 20–30% |
| **C — short horizon** | under 10 years, whatever the cash flows | 40–60% | 40–60% |
| **D — drawing down** | withdrawals have begun over a long remaining horizon | **set by the withdrawal rate, not by the horizon** | — |

Sequence risk is a cash-flow interaction, not a premium: without external cash flows,
permuting returns leaves terminal wealth unchanged, which
[is verified rather than asserted](setting-the-equity-share.md#3-sequence-risk-verified-and-given-a-sign)
across 20,000 reorderings of one fixed return record. Variants C and D exist because
contributions and withdrawals break that identity, not because equities are riskier
over short horizons in some deeper sense.

**C and D point opposite ways, and were one row here until they were measured.** A
short horizon argues for fewer equities. A long retirement at a demanding withdrawal rate
argues for more: on CPI-deflated US returns over a 30-year draw, a 20%-equity portfolio
taking 4%/yr real ran out in 6.82% of reorderings against 2.43% at 60% equity, and at a
5% real draw the failure rate fell all the way to 90% equity
([setting the equity share](setting-the-equity-share.md#51-withdrawals-invert-part-of-the-table)).
Above roughly a 4% real draw, holding too few equities is the larger risk.

### 1.2 The holdings

Equity composition is identical in every variant. The weights are **the
repository's own declared research weights**, frozen in
[Experiment 003](rebalancing-policy.md)'s specification before any result was
examined — a stated choice, not a measured optimum. No global market-capitalisation
series exists in this repository, so no page here can tell you the market weight.

| Sleeve | Fund | ER | % of equity | Status of what it buys |
| --- | --- | ---: | ---: | --- |
| US total market | **VTI** (or ITOT, VOO) | **0.03%** | 60 | the control |
| Developed ex-US | **VEA** (or IEFA at **0.07%**) | **0.03%** | 30 | the control |
| Emerging markets | **VWO** (or IEMG at **0.09%**) | **0.06%** | 10 | the control |
| Investment-grade bonds | **BND** (or a Treasury fund) | **0.03%** | — | risk control, sized by variant |

**Use VXUS instead of VEA + VWO only if you will hold the whole international sleeve
in one account.** Splitting developed from emerging is what makes §3's placement
result available, and VXUS forecloses it. VXUS's expense ratio is 3 bp and its
30-day median bid/ask spread 1.18 bp `as of 2026-08-10`
([edge decomposition](expected-edge-decomposition.md) §2.1).

**Fees not read here are not omissions of convenience.** VTI, VOO, VXUS and VB are
confirmed at 3 bp `as of 2026-08-10`; VBR at 0.05% and every other factor fee below
comes from the sponsor's own prospectus or fund page with its URL and date recorded
([Exp 002](factor-product-audit.md)), and every managed-futures fee from the fund's
SEC-filed 497K summary prospectus fee table with its accession number
([Exp 008](trend-marginal-value.md#experiment-008--the-products)), both
`as of 2026-08-12`. The five fees this page previously refused to state are now read
from their sponsors. Each is a **dated lookup, not an experiment result**:

| Fund | ER | Primary source | Dated |
| --- | ---: | --- | --- |
| VEA | 0.03% | Vanguard's published fund-profile endpoint, `expenseRatioAsOfDate` | 2026-04-28 |
| VWO | 0.06% | same endpoint | 2026-02-27 |
| BND | 0.03% | same endpoint | 2026-04-28 |
| IEFA | 0.07% | SEC-filed 497K fee table, accession [0001193125-25-302120](https://www.sec.gov/Archives/edgar/data/1100663/000119312525302120/d35638d497k.htm) | 2025-11-28 |
| IEMG | 0.09% | SEC-filed 497K fee table, accession [0001193125-25-336670](https://www.sec.gov/Archives/edgar/data/930667/000119312525336670/d947325d497k.htm) | 2025-12-30 |

Two qualifications, because these are not like-for-like with the Vanguard numbers above.
**IEMG's fee table carries a waiver line, currently `(0.00)%`** — a waiver sitting at
zero is one that can be withdrawn, so IEMG's 0.09% is the least stable figure here. And
the footnote to both iShares tables excludes acquired fund fees and expenses, so neither
is an all-in number.

Where a figure is still absent, look it up; do not take a number from this page that
this page does not have.

### 1.3 The two optional sleeves, and nothing else

Both are second decisions, taken after the split above, and both are held **inside**
the equity or total allocation rather than added to it.

| Sleeve | Fund | ER | Size | Where | Verdict |
| --- | --- | ---: | --- | --- | --- |
| Small-cap value | **VBR** | 0.05% | 0–20% of US equity | treat as US equity in §3's ranking | `exploratory` product, `exploratory` premium, **chain negative on the defensible reading** |
| Managed futures | **DBMF** | 0.85% | 0–10% of total | **tax-deferred only** | `exploratory` product, index `unresolved`; single-product risk |

Two sizing notes, because both weights are judgements and neither is measured.
**VBR's yield is higher than the market's, which raises its shelter priority above the
26.2/20.7/16.5 bp of plain US equity in §3 — by how much is not measured here.** And
**Experiment 004 priced a 15% trend sleeve, not a 10% one**; the cap is set below the
tested weight because one product delivers the exposure and there is no fallback, not
because 10% was measured to be better.

Everything else that was tested is out, and each has a specific reason in §2:
momentum (MTUM), quality (QUAL, SPHQ), large-cap value (VTV), plain small-cap (VB),
the other four managed-futures ETFs (CTA, FMF, KMLM, WTMF), leverage and
return-stacking (NTSX and any 90/60), rebalancing as a source of return, and the
small-value corner as the academic literature defines it.

### 1.4 The disciplines, which are worth more than the sleeves

| Discipline | Worth | Class |
| --- | ---: | --- |
| Hold index funds rather than the average active dollar | **49 bp/yr** | deterministic |
| Hold ETFs (or Vanguard's dual-share-class funds) rather than active mutual funds in taxable | **+23 bp** | deterministic, **decaying** |
| Specific identification of lots, as a standing instruction | **+5 bp** | deterministic |
| Asset location, computed rather than asserted (§3) | 10 bp, less 3.4 bp of forfeited foreign tax credit | deterministic |
| Tax-loss harvesting, only with contributions and only at a 9–12 bp fee | 30 bp gross, **25.6 bp** net | deterministic |
| Do not turn the taxable account over | avoids an **84 bp/yr** hurdle at 30 years | deterministic |
| Rebalance to hold the declared weights, annually or on a band | 0.3–1.2 bp/yr in cost; **not a return** | risk control |
| **Total against your own counterfactual** | **≈109 bp/yr** | 99% confident in ~12 months |

The 84 bp figure is a **hurdle, not a saving**. Deferral of unrealised gain is worth
84.1 bp/yr at thirty years and the §1014 step-up a further 78.1, summing to a
horizon-free **162.21 bp/yr**. Any strategy that turns a taxable portfolio over must
out-earn that before its fee and its spread. The function is sharply concave, so
"low turnover" is not a defence: realising 10% of standing gain a year already costs
41.5 bp of the 84.1 ([structural and tax-aware edges](structural-and-tax-edges.md) §4).

---

## 2. Line by line: what each holding is buying, and at what confidence

`Contractual` means an accounting identity or a statutory fact whose sign is known in
advance. `Risk premium` means a bet whose sign is not known at any horizon a human
has. `Nothing better exists` means the line is there because the alternatives were
tested and lost, not because it was shown to be good.

| Holding | What it is buying | Evidence class | Confidence | Why it is here |
| --- | --- | --- | --- | --- |
| **VTI / VOO / ITOT** | equity risk premium at 3 bp, ~1.3 bp round trip, plus 1.01 bp/yr of securities-lending pass-through (VTI, FY2025 N-CSR) | **contractual** on the *cost*; risk premium on the *return* | The cost is certain. The return is not, and no page here forecasts it | It is the control ([decision 0003](../decisions/0003-cheap-broad-market-control.md)). Every candidate was measured against it and none beat it |
| **VEA / IEFA** | developed ex-US equity; ~2.97 bp/yr (VEA) or ~1.08–1.11 (IEFA) of lending income | same | same | Diversification of the equity claim, not an edge. Its foreign tax credit is worth 15.78 bp/yr **only in taxable** |
| **VWO / IEMG** | emerging equity; ~4.9–5.2 bp/yr (VWO) or ~9.2–9.7 (IEMG) of lending income | same | same | Same. Its credit is worth 20.00 bp/yr in taxable — and it is the sleeve §3's arithmetic moves |
| **BND** or Treasuries | term and credit compensation, and a risk brake | **a different benchmark, not an edge** | US bond–stock comovement was positive from 1974, negative 2000–2022Q3, and positive again 2022Q3–2024Q2 ([Campbell, Pflueger and Viceira 2025](https://www.nber.org/papers/w34323); dates from the [authors' own summary](https://econbrowser.com/archives/2026/02/guest-contribution-understanding-bond-stock-price-comovements), retrieved 2026-08-12, and reproduced on this repository's data in [setting the equity share](setting-the-equity-share.md#6-what-the-bond-side-is-actually-for)) | Sized by the investor's risk capacity. The brake works; its **diversification** does not, in every era. Booking a term premium as an edge over an equity index is a benchmark switch, not a return source |
| **VBR** (optional) | HML loading **+0.410 `[+0.322, +0.480]`**, delivered and stable, at 5 bp, with a **negative** shortfall (−0.62 pp/yr) against a fitted four-fund combination | **risk premium**, `exploratory` on both terms | **Low.** `premium × loading × capture − cost` is +0.09 to −0.39 pp/yr on the US premium and +0.28 to +0.76 on the pooled one. §5 | It is the only US value product that both delivers its exposure and does not lose to a cheap combination. It is *not* here because the chain is positive |
| **DBMF** (optional) | loading **+0.671 `[+0.513, +0.829]`** on the AQR TSMOM index, stable across the fixed split and all 19 rolling windows, trailing a cost-free vendor index by 0.48 pp/yr against an 0.85% fee | **risk premium**, `exploratory`; the index itself is `unresolved` | **Low, and lower in taxable.** Crisis correlation −0.59, downside beta −0.67, payoff spread across four structurally different crises — but the post-publication interval includes zero and fails Holm | **Nothing better exists.** Four of five listed managed-futures ETFs fail the 0.50 loading bar. One product, no fallback |
| **Cash / liquidity reserve** | optionality and the ability not to sell | contractual | — | The framework requires it and no experiment here sizes it. An investor-policy input, still missing |

### What is deliberately absent, and why

| Excluded | Reason | Source |
| --- | --- | --- |
| **MTUM**, and any momentum sleeve | Delivers its exposure (UMD +0.444 `[+0.277, +0.562]`) and is still `rejected`: a 1.22 pp/yr tracking shortfall to a three-fund combination whose fee premium over it was 0.12. It is the **entire** retail momentum shelf clearing $1bn and 0.60% | [Exp 002](factor-product-audit.md) |
| **VTV**, large-cap value | HML +0.337, but a +2.57 pp/yr shortfall; and its replication is degenerate (VTI + VB), so read that as "value underperformed the market over these 72 months", not as a defect | [Exp 002](factor-product-audit.md) §7 |
| **VB**, plain small-cap | Largest shortfall on the shelf, +2.89 pp/yr; and the size premium is **not signable**: +1.91 pp/yr `[−1.90, +6.00]` over 750 months against its own 4.73 detection threshold, +0.41 post-publication | [Exp 007](long-only-capture.md#momentum-and-size) |
| **QUAL, SPHQ**, quality | RMW is `rejected` and **closed on public data**. An unsigned premium makes the product's own quality irrelevant | [decision 0005](../decisions/0005-factor-premia-closed-on-public-data.md) |
| **CTA, FMF, KMLM, WTMF** | Loadings 0.475, 0.303, 0.245, 0.099 against a 0.50 bar. KMLM's interval `[−0.148, +0.446]` includes zero — but read that as "KMLM is not *this* index" (its own index holds no equity futures; AQR's holds nine), not as "KMLM is not trend" | [Exp 008](trend-marginal-value.md#experiment-008--the-products) |
| **NTSX and any 90/60 return-stacked fund** | Needs **92.0 bp/yr** of Treasury excess return over cash before the overlay contributes anything, against a measured futures funding basis of 58.70 bp/yr that was positive in all 28 years measured. Both inputs are forecasts | [structural edges](structural-and-tax-edges.md) §3 |
| **Leverage of any kind** | Zero, and it stays zero. It was conditioned on an unlevered edge surviving the protocol. None has | [decision 0004](../decisions/0004-no-sleeve-promoted.md) |
| **Rebalancing as a source of return** | `rejected`: **−38.7 bp/yr** on the portfolio and −62.9 on the US/developed-ex-US pair over 420 months. The realised drift gap ran ~35× `gamma_star`, and relative regional performance **trends** rather than reverts | [Exp 003](rebalancing-policy.md) |
| **The academic small-value corner** | ME1 × BM5 held **21.24% of listed firms and 0.236% of market capitalisation** at 2025-12. Not implementable at retail in size. The investable version excluding the smallest quintile delivers +3.14 pp/yr over the market rather than +3.85, gross | [Exp 007](long-only-capture.md) |
| **Gold, tail hedges, private credit, cat bonds, merger arb** | Untested here. Gold is an average hedge and a short-lived safe haven in some countries and samples, not a universal negative-correlation asset; a protective put must be benchmarked against a **return-matched** equity/cash mix, and comparing it to the fully invested index flatters it | [framework](portfolio-edge-research-framework.md) |

---

## 3. Account placement, worked through

### 3.1 The rule

The right metric for a scarce shelter is what a sheltered dollar **saves**, not which
asset is "tax-inefficient":

```
priority = (recurring tax if held in taxable) − (irrecoverable withholding if sheltered)
```

For every asset except a foreign one the second term is zero and this collapses to
the familiar rule. Foreign withholding is **paid and permanently lost** inside a
traditional IRA and a Roth alike: an IRA is *"exempt from taxation under this
subtitle"* ([§408(e)(1)](https://www.law.cornell.edu/uscode/text/26/408)), so it has
no tax to credit against under [§901(a)](https://www.law.cornell.edu/uscode/text/26/901)
and a [§904(a)](https://www.law.cornell.edu/uscode/text/26/904) numerator of zero.
No IRS publication states this; it is asserted from the statute.

### 3.2 The arithmetic

Inputs, each dated and sourced in [structural and tax-aware edges](structural-and-tax-edges.md) §1:
BND SEC 30-day yield **4.65%** (2026-08-10); MSCI EAFE dividend yield **2.60%** and
Emerging Markets **2.03%** (2026-07-31); US equity yield **1.10%** (stated input);
effective withholding on the grossed-up §853 basis **6.068%** developed and **9.853%**
emerging, from Vanguard's 2025 foreign tax credit worksheet (VEA 6.46%, VXUS 7.11%,
VWO 10.93% of ordinary dividends). Ordinary rate 40.8%.

```
withholding forfeited, developed  = 2.60% × 6.068%  = 15.78 bp/yr
withholding forfeited, emerging   = 2.03% × 9.853%  = 20.00 bp/yr
break-even qualified rate  q* = u·w·y_i / (y_i − y_d)
   developed:  0.0260 × 0.06068 / (0.0260 − 0.0110) = 10.52%
   emerging:   0.0203 × 0.09853 / (0.0203 − 0.0110) = 21.51%
```

The US schedule offers 0%, 15%, 18.8% and 23.8%. **The developed break-even falls
below every positive rate, so developed ex-US always belongs in the shelter ahead of
US equity. The emerging break-even falls *between* two live rates, which is why one
sleeve inverts and the other does not.** That is a fact about the bracket schedule,
not about the funds.

Priority per dollar of shelter capacity, in bp/yr:

| Asset | Taxable cost | Sheltered cost | **23.8%** | **18.8%** | **15%** |
| --- | --- | ---: | ---: | ---: | ---: |
| Taxable investment-grade bonds | yield × 40.8% | 0 | **189.7** | **189.7** | **189.7** |
| Developed ex-US equity | 2.60% × q | 15.78 | **46.1** | **33.1** | **23.2** |
| Emerging-market equity | 2.03% × q | 20.00 | **28.3** | 18.2 | 10.45 |
| US equity | 1.10% × q | 0 | 26.2 | **20.7** | **16.50** |

**One caveat on the bond row, because the table would otherwise be internally
inconsistent.** 189.7 bp uses the 40.8% top ordinary rate, which belongs with the
23.8% qualified rate and not with the other two columns: a taxpayer whose qualified
rate is 15% faces an ordinary rate nearer 12–24%, so the bond line falls to roughly
`4.65% × 22% = 102 bp`. **It still dominates the next line by more than four to one**,
which is why the ranking does not move — but the printed 189.7 is a top-bracket figure
and must be restated with the investor's own ordinary rate.

Read down each rate column and fill the shelter in that order.

| Rate | Fill order | The reversal |
| --- | --- | --- |
| **23.8%** | bonds → developed → emerging → US | Conventional order survives, but emerging's margin over US collapses from 22.1 bp to **2.1 bp**. Treat it as a tie |
| **18.8%** | bonds → developed → **US** → emerging | **Inverted.** Emerging goes to taxable |
| **15%** | bonds → developed → **US** → emerging | **Inverted**, by 6.05 bp |
| **0%** | the credit is worth nothing either way | §904 limits the credit to US tax on foreign-source income, and there is none. The 0% bracket forfeits the withholding in *both* locations |

### 3.3 The placement, by account

| Account | Holds, in this order | Why |
| --- | --- | --- |
| **HSA** (if a high-deductible plan applies) | equity, highest-growth sleeve | The only US account untaxed at all three points, and payroll contributions escape FICA. Not a rate, a **dollar limit**: $4,400 self-only / $8,750 family for 2026, plus a $1,000 age-55 catch-up hardcoded in §223(b)(3) and never indexed. **California breaks the deduction and taxes internal earnings annually**; New Jersey is widely reported to do the same and no primary source was found |
| **Traditional 401(k)/IRA** | bonds first, then developed ex-US, then per §3.2. **DBMF here if held at all** | Bonds dominate by a factor of four. DBMF's 2.09 pp/yr distribution tax drag is zero here |
| **Roth** | the highest-expected-growth sleeve that fits after bonds — US equity, or the small-value tilt | Identical to traditional on foreign withholding (both forfeit it). The traditional-vs-Roth choice itself is a **rate forecast**, not a structure, and does not belong in a contractual budget |
| **Taxable** | US total market; emerging-market equity at a 15% or 18.8% rate; whatever does not fit above | ETFs, specific-ID lots as a standing instruction, no turnover |

Three conditions that decide more than the ranking:

- **A tax-deferred balance is not the investor's money.** At a 24% withdrawal rate,
  $100,000 of traditional IRA is $76,000 of investor wealth. An allocation stated on
  nominal balances misstates true equity exposure; §3.2's ranking is per dollar of
  *capacity* precisely to sidestep that.
- **Below $300 of creditable foreign tax ($600 joint)** the credit is claimed on
  Schedule 3 with no Form 1116 and no §904 limitation. At the developed sleeve's rate
  that threshold arrives at **$190,153 of holdings ($380,305 joint)**. Neither figure
  is indexed.
- **Wash-sale scanning must be household-wide.** Rev. Rul. 2008-5 disallows a loss
  where the replacement is bought in the taxpayer's IRA **and does not increase the
  IRA's basis**, so the deduction is destroyed rather than deferred — 119 bp outright
  on a 5%-of-portfolio disallowance at the top rate. It is the only tax-loss mechanic
  on record here whose damage is permanent.

**Two omissions that cut against the emerging-market inversion**, neither quantified:
a shelter also shelters capital-gain distributions and rebalancing turnover, which
emerging funds generate more of; and a taxable international position is a better
loss-harvesting candidate because it is more volatile. Either could close a 6 bp gap.

---

## 4. Verdict on the proposed portfolio

The proposal: **US 45% / international 35% / other 25%**, with small-cap value,
momentum and managed-futures sleeves.

**It sums to 105%.** That is the first correction, and it matters because it is
ambiguous which sleeve absorbs the five points.

| Sleeve | Verdict | Reason |
| --- | --- | --- |
| **US 45 / international 35** | **Supported, as an investor choice.** No change required | That is a 56:44 US:ex-US equity split against the repository's own declared 60:40. No page here can distinguish them: there is no global market-capitalisation series in this repository, and no experiment signed a regional tilt. Choose either and stop |
| **"Other" 25%** | **Underspecified. Split it.** | If it is bonds, they go in the shelter first, by a factor of four over any equity sleeve. If it is managed futures at anything like 25%, that is far too large for a sleeve whose index is `unresolved` and whose only delivering product is one fund |
| **Small-cap value** | **Reduce, and know what you are buying.** 0–20% of US equity, via VBR | The chain is `premium × loading × capture − cost`. On the size-neutral capture (0.520) and the US-only premium (+1.57 pp/yr) it is **+0.09 to −0.39 pp/yr — negative on the defensible reading of both terms**. It is positive only on the pooled premium (+4.74) *and* the market-relative capture (0.958–1.287), and the gap between those captures is a **size premium wearing a value label** — which the size test then failed to sign |
| **Momentum** | **Drop.** | Not because the premium is weak — it is the **largest** gross factor measured here, pooled **+7.33 pp/yr `[+3.92, +10.31]`**. Because: its pooled detection threshold is **4.98 pp/yr, the worst in this repository**; its three regions are worth **1.33 effective regions** out of three and **crash together** (all three lost their worst calendar year in 2009); the academic construction rebalances **monthly**, with an assumed cost of 3.30–18.67 pp/yr against that 7.33 gross premium; and the entire retail shelf is MTUM, which delivers its exposure and is `rejected` on cost |
| **Managed futures** | **Keep, smaller, and only in a tax-deferred account.** DBMF only | **Only DBMF delivers the exposure** (+0.671, interval clear of the 0.50 bar, three independent measurements agreeing). KMLM's loading interval `[−0.148, +0.446]` includes zero. Tax drag is 0.76–2.53 pp/yr across the shelf and 2.09 for DBMF — **2.5× its own fee** — and **zero in a shelter** |

### What changed since the earlier answer to the owner

Four corrections, all of which run against what was said before.

1. **Momentum is the strongest gross factor, not the weakest.** Pooled UMD +7.33 pp/yr
   against HML's +4.74. The case against a momentum sleeve is now entirely about
   turnover, product shelf and a shared crash — not about the premium
   ([Exp 006](factor-persistence.md#experiment-006--regional-momentum)).
2. **Trend is `unresolved`, not `rejected`.** Experiment 004's clause (d) was
   ambiguously specified. Under the *relative* reading — which
   [Experiment 008 judges better justified](trend-marginal-value.md#which-reading-is-better-justified),
   because the absolute reading's bar gets *easier* to clear as the sleeve gets
   better — the verdict is `unresolved`. **`unresolved` is not a promotion.**
3. **Experiment 004's verdict was repeated as though it applied to KMLM, DBMF and
   CTA. It did not — it evaluated an index.** Experiment 008 tested the products and
   reached a *different* answer for DBMF, the one that is an explicit replication
   strategy. That error is recorded on its own page.
4. **The long-only capture fraction is measured, and it makes a US-only long-only
   value tilt negative after cost.** Five defensible benchmarks span **0.846**, which
   is why Experiment 007 is `rejected` on its own dispersion clause: what was
   rejected is not the capture fraction but the premise that there is one.

---

## 5. What each tilt costs in confidence terms

`P(outperform) = Phi(e sqrt(T) / s)` and `T(confidence) = (z s / e)**2`, from
[`studies/outperformance_horizon.py`](../../research/src/portfolio_edge/studies/outperformance_horizon.py).
**The horizon scales with the square of `s / e`, so tracking error and not edge size
decides whether a lifetime is enough.** Every probability below is an **upper bound**:
the machinery treats `e` as known, which removes the dominant source of uncertainty.

### 5.1 The contractual line

| Line | Edge | TE | P(10 yr) | P(30 yr) | 90% at | 99% at |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Cost + tax + placement, vs your own counterfactual** | **109 bp** | 46 bp | ~1.00 | ~1.00 | **3.5 months** | **~12 months** |
| The same budget before the 2026 revision | 89 bp | 41 bp | ~1.00 | ~1.00 | 4.2 months | 13.8 months |
| The whole honest budget **vs a cheap index** | 24.4 bp | 401 bp | 0.576 | **0.631** | ~443 yr | — |

Read the last row as an **upper bound**, not a central estimate: its rebalancing line
has since been measured negative on real data.

### 5.2 A 20%-of-portfolio small-value tilt (VBR)

Gross contribution is `weight × loading × capture × premium`. Cost is Experiment 007's
assumed sort turnover (0.20–0.68 pp/yr) plus a fee; VBR's actual 5 bp fee is below the
0.15–0.25% the cost table assumes, so the applicable sleeve cost is about
**0.25–0.73 pp/yr**. Tracking error is taken at **7 pp/yr for the sleeve**, inside the
1.38–8.65 pp/yr range Experiment 002 measured against a cheap combination (VTV 7.48,
VB 8.31) — **an assumption, since VBR's own tracking error was not published**.

| Premium used | Sleeve cost | Net edge | TE | **P(30 yr)** | 90% confidence at |
| --- | --- | ---: | ---: | ---: | ---: |
| Pooled +4.74 pp/yr | 0.25 pp/yr | **+15.2 bp** | 140 bp | **0.724** | 139 yr |
| Pooled +4.74 | 0.73 | +5.6 bp | 140 bp | 0.587 | 1,026 yr |
| **US-only +1.57** | 0.25 | +1.8 bp | 140 bp | 0.528 | ~10,000 yr |
| **US-only +1.57** | 0.73 | **−7.8 bp** | 140 bp | **0.380** | never |

**That table is the whole case, for and against.** The best corner requires believing
a premium whose weight sits in the two regions where shorting is hardest and where no
audited product exists here, and the worst corner is a persistent loss. At no corner
is the tilt demonstrable from the investor's own experience.

### 5.3 A 15%-of-portfolio managed-futures sleeve (DBMF)

Experiment 004 measured a 15% sleeve of the **index** at +1.342 pp/yr of marginal
certainty equivalent `[+0.759, +1.916]` over 432 months, falling to **+1.011 pp/yr
post-publication with an interval that includes zero and fails Holm**. DBMF delivers
0.671 of that exposure. Tracking error is **derived**, not published: from Experiment
004's own table, `passive_plus_trend` runs 7.65% volatility against the passive
benchmark's 9.12% at correlation 0.97, giving
`sqrt(7.65² + 9.12² − 2 × 0.97 × 7.65 × 9.12) = 2.52 pp/yr`.

| Case | Net edge | TE | P(30 yr) | 90% at |
| --- | ---: | ---: | ---: | ---: |
| Post-publication, **tax-deferred** (`0.671 × 1.011`) | +68 bp | 251 bp | 0.931 | 22 yr |
| Post-publication, **taxable** (less `0.15 × 2.09`) | +37 bp | 251 bp | 0.790 | 76 yr |
| Full-period, tax-deferred (`0.671 × 1.342`) | +90 bp | 251 bp | 0.975 | 13 yr |

**The account, not the product, is the largest controllable term** — 31 bp/yr of
portfolio return, larger than the whole fee. Set against those probabilities: the
index's own standalone Sharpe fell 1.34 → 0.18 and its geometric return 19.4% → 3.1%
after publication; the vendor states **no cost basis anywhere** in the archived
workbook; comparable CTA survivorship and backfill distortion is **7.7 pp/yr**, larger
than the strategy's entire gross premium; and one product delivers the exposure, with
no fallback.

### 5.4 The comparison that decides the page

| | Edge | TE | 99% confident in |
| --- | ---: | ---: | --- |
| Cost, placement, fund structure, lot discipline | **109 bp** | 46 bp | **~12 months** |
| Best case for a 20% small-value tilt | 15.2 bp | 140 bp | ~460 years |
| Best case for a 15% trend sleeve in a shelter | 90 bp | 251 bp | ~42 years |

**A certain 109 bp is worth more than any tilt's gross premium, and it is available
first.** That is the honest headline and it is not a rhetorical preference: it is what
the pairing of edge and tracking error produces.

---

## 6. What would change this

Each is measurable and dated. None is a hope.

| Condition | What it changes |
| --- | --- |
| **ETF share classes are adopted broadly.** 94 SEC orders granted `as of 2026-08-11`, covering ~90 fund families; only two applications remain noticed and unordered | The +23 bp fund-structure line goes towards zero and the budget falls to about 86 bp. **Recheck the order count before leaning on that line** |
| **§852(b)(6) is repealed.** A 2021 Senate Finance discussion draft proposed exactly that; never enacted, no successor found | Removes the ETF wrapper advantage outright |
| **A qualified-dividend rate below 10.52%, or at or above 21.51%** | Below 10.52%: developed ex-US belongs in taxable too. At or above 21.51%: emerging returns to the shelter and §3's inversion disappears |
| **A licensed, survivorship-free, point-in-time total-return source from at least 2003**, with coded exit reasons and retrievable vintages | Lifts Experiments 002 and 008 above `exploratory` for the first time. Without it, VBR and DBMF cannot be promoted **or** properly rejected |
| **An audited ex-US or emerging value product** | The value premium's weight is +5.07 pp/yr developed ex-US and +7.58 emerging against +1.57 in the US. Experiment 002's screen removed **185 international, 82 global and 51 emerging** series, so this repository has audited **zero** ex-US factor products. This is the single largest gap between where the premium was measured and where a product was tested |
| **A second managed-futures ETF with a loading ≥ 0.50** on a per-fund benchmark built from its own stated universe | Removes DBMF's single-product risk and separates "does not deliver trend" from "does not deliver *this* trend" |
| **A measured one-sided monthly turnover below 50% for a long-only momentum fund** | Reopens momentum. The 27.5–91.5%/month figure belongs to a monthly-rebalanced academic long-short spread and must never be applied to a fund |
| **A measured implied financing spread, a signed term premium, a defined investor policy, and a modelled forced-liquidation path** — all four | Reopens capital efficiency and [decision 0004](../decisions/0004-no-sleeve-promoted.md)'s zero-leverage rule |
| **A further decade of RMW/CMA data, or a non-French construction** | Nothing else reopens them. Pooled MDE₈₀ scales as `1/sqrt(T)`: reaching 2.0 pp/yr from 2.62 needs ~245 months, about 2035 ([decision 0005](../decisions/0005-factor-premia-closed-on-public-data.md)) |
| **The 2026-01-onward window**, unread in every file, under a **new** frozen specification | The natural confirmatory test. Six to eight months against a 2.6 pp/yr floor spends a genuine holdout for very little; wait |

---

## 7. What this is not

- **Not personalised advice.** It is a construction derived from measurements, for a
  stated reference investor: US federal, top or specified bracket, thirty-year
  horizon, contributions continuing, state tax excluded.
- **Not a forecast.** No expected return for any market appears on this page. The
  probabilities in §5 are conditional on edges being what the cited pages measured,
  and they are upper bounds because they treat those edges as known.
- **Not a promotion.** **No sleeve reached `production-eligible`, or
  `walk-forward-tested`, or even `independently-reproduced`.** VBR and DBMF are
  `exploratory` products, which permits them to be used as implementation proxies in
  a later experiment and permits nothing else
  ([decision 0004](../decisions/0004-no-sleeve-promoted.md)).
- **Not a claim of outperformance against an index.** Against a cheap index the whole
  honest budget is ~24 bp against 401 bp of tracking error — a 0.631 probability of
  being ahead after thirty years. "Recommended" here means *best-supported
  construction given the evidence*, not *this will win*.
- **Not net of everything.** No page here has a full after-tax, after-spread,
  after-turnover return for any product. Bid-ask, brokerage, realised distributions
  and portfolio turnover are absent from Experiment 002 entirely.
- **Not free of model risk.** FF5+UMD prices **VTI itself** at −0.55 pp/yr with a HAC
  *t* of −3.41 over 2020–2025. The standard model does not span the control, and every
  alpha in this repository is a distance from that pedestal, not from zero.
- **Not vintage-stable.** Ken French rebuilds the whole history from the current
  vintage on every rebuild, and the Phase 1 gate is `unresolved`: HML's and RMW's
  standard deviations do not reproduce, leaving a **systematic 3–5% band** on anything
  that divides by them. Five series carry no measured band at all, which is weaker
  than a band of zero — including **all three momentum files**.

### The investor-policy inputs still missing

Framework open decisions 1 and 4, unchanged. Without these, §1.1's variants are
ranges rather than an answer, and no page here can narrow them.
[Setting the equity share](setting-the-equity-share.md) §7 sets out which of them an
application can compute on and which it must ask for:

horizon and liability model; drawdown and shortfall tolerance and the loss that would
force a sale; cash flows in and out, and whether contributions continue; marginal
federal **and state** bracket, now and expected at withdrawal; balances by account
type and remaining contribution capacity; high-deductible-plan status; existing lots
and their basis; employer stock in a qualified plan (§402(e)(4)(B) NUA); currency and
home-country bias; capital scale; permitted instruments; liquidity reserve in days;
and the objective — net geometric growth is *declared as a preference* here, and a
consumption or shortfall objective would change the answer.

---

## Verified, assumed, open

### Verified elsewhere and quoted here

Every number in §§1–5 traces to a page, an artifact or the ledger. The load-bearing
ones: the ~109 bp budget and its component lines
([structural and tax-aware edges](structural-and-tax-edges.md), regenerated by
`studies/tax_structure.py`); the foreign-tax-credit break-evens of 10.52% and 21.51%
(same page, §1); the long-only capture of 0.520 `[0.434, 0.722]` size-neutral and the
0.846 definitional spread ([Exp 007](long-only-capture.md)); pooled HML +4.74 and UMD
+7.33 with their detection thresholds of 3.35 and 4.98 and effective region counts of
1.49 and 1.33 ([Exps 005 and 006](factor-persistence.md)); every fund loading, fee and
status ([Exp 002](factor-product-audit.md),
[Exp 008](trend-marginal-value.md#experiment-008--the-products)); the trend marginal
CE of +1.342 falling to +1.011 post-publication ([Exp 004](trend-marginal-value.md));
and the −38.7 bp rebalancing result ([Exp 003](rebalancing-policy.md)).

### Assumed on this page, and nowhere else

1. **A 7 pp/yr tracking error for a value sleeve against a cheap combination.** Inside
   Experiment 002's measured 1.38–8.65 pp/yr range (VTV 7.48, VB 8.31), but **VBR's
   own tracking error is not published anywhere in this repository**. §5.2 is
   proportionally sensitive to it in the horizon column and not in the sign.
2. **That a trend sleeve's marginal certainty equivalent scales linearly in the
   product's loading on the index.** `0.671 × 1.011` is an approximation; the
   experiment measured the index at a 15% weight, not DBMF at any weight. Experiment
   008's own marginal-contribution arm is labelled **invalid** for every fund on
   warm-up grounds, so no direct measurement exists.
3. **A derived 2.52 pp/yr portfolio tracking error for the trend sleeve**, computed
   from Experiment 004's published volatilities and correlation against the *fully
   invested* passive benchmark rather than the risk-matched comparator the experiment
   used as primary.
4. **Experiment 003's US 60 / developed-ex-US 30 / emerging 10 as the equity
   composition.** A declared research weight, frozen before results, not a measured
   optimum and not a market weight.
5. **That VBR's 5 bp fee substitutes for the 15–25 bp expense assumed in Experiment
   007's cost table**, giving a 0.25–0.73 pp/yr sleeve cost rather than 0.35–0.93.

### Open

- **Which benchmark a factor line may book its capture against.** Framework open
  question 11, unresolved. §5.2 reports both and the answer moves the line by a factor
  of two and a half.
- **What a real fund's delivered capture is.** Every capture figure here is from
  research portfolios. Measuring a fund's own capture requires holdings rather than
  returns — Experiment 002's data, and the next experiment nobody has run.
- **Whether the emerging-market inversion survives capital-gain distributions and
  harvesting value**, neither of which §3 quantifies.
- **What a fund's own tracking error against a cheap combination is.** §5.2 assumes 7
  pp/yr for VBR from Experiment 002's range for *other* funds. VBR's own is unpublished
  here, and it is the input the small-value horizon column is most sensitive to.
- **What a liquidity reserve should be.** Framework open decision 10, unsized.

---

## Consequence for this repository

1. **This page is where a named-fund construction lives, and the only place.** The
   framework holds the design map and answers *whether a return source is real*; this
   page answers *what to hold given that*. It must never state a premium, a status or
   a cost that its source page does not.
2. **The application may not render any of this as a finding.** No number from
   `research/` may appear in the shipped app, and the shipped UI copy still claims
   real-time data, optimality and professional validation that nothing here supports.
   Correcting that copy is a product decision to raise, not an edit to make unasked.
3. **The asset-location ranking must be computed, not asserted.** Any location feature
   must run §3.1's expression and state the bracket it assumed. "Shelter the
   higher-yielding asset" is right for bonds by a factor of four and wrong for
   emerging-market equity at two of the four US dividend rates.
4. **Two review triggers.** The fund-structure line (94 SEC orders and rising) and
   every fund-specific fact in §1.2. Re-check both before any decision leans on them.
5. **The largest evidence gap this page exposes is a product gap, not a premium gap.**
   The value premium was measured where no product here has been audited, and the
   momentum premium was measured on a construction no product can implement. Both are
   fixable with the same purchase.
