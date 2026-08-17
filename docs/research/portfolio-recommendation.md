# The recommended portfolio: what to hold, which account holds it, and what each line buys

**Question.** Given everything this repository has measured, what is the best-supported
portfolio a US investor can actually implement — named funds, weights, account placement —
and what is each decision buying, at what confidence?

**Decision it informs.** What construction the repository puts its name to, and what it
refuses to. [Decision 0006](../decisions/0006-reference-portfolio-without-promotion.md)
records why naming funds is permitted and what "recommended" is allowed to mean: **the
best-supported construction given the evidence**, and nothing more.

**Out of scope.** Personalised advice, a forecast of any market, and the promotion of any
sleeve. **Nothing here reached `production-eligible`, and nothing here is claimed to beat
an index.** Every fund-specific fact below is dated and must be re-checked before use.

`as of 2026-08-17` for the wrapper and managed-futures product facts, `2026-08-12` for
everything else. US federal individual investor, state tax excluded and additive.

---

## Conclusion

1. **The portfolio is the control plus placement.** A cheap, broad, long-only, fully
   invested global equity/bond portfolio
   ([decision 0003](../decisions/0003-cheap-broad-market-control.md)), held in the right
   accounts, with lot discipline, and not traded. Not a default chosen for want of anything
   better — **it is the only construction whose delivery is contractual rather than
   statistical.**
2. **The reliable edge is up to ~109 bp/yr against the portfolio you would otherwise have
   owned, and it is conditional.** Only the 49 bp fee line is unconditional; the rest needs
   a taxable account, or more than one account type, or continuing contributions
   ([structural and tax-aware edges](structural-and-tax-edges.md)). **For a reader already
   holding cheap index funds in one tax-deferred account, the honest figure is close to
   zero.** Its largest new component is decaying while being measured, and the ~46 bp
   tracking error behind the "99% in twelve months" claim is an assumption rather than a
   measurement.
3. **Every tilt is smaller, slower, and not signable within a lifetime.** The best case for
   a 20%-of-portfolio small-value tilt is **+15 bp/yr against 140 bp of tracking error** —
   a 0.72 probability of being ahead after thirty years and 139 years to 90% confidence. On
   the defensible reading of the two terms that decide it, **the same tilt is negative**.
4. **The equity/bond split is the investor's to set and nothing here can set it.** It is the
   largest single decision in the portfolio and the only one the evidence is silent on.
5. **One account-placement result is not the textbook one:** at a 15% or 18.8% qualified
   rate, **emerging-market equity belongs in the taxable account and US equity in the
   shelter**. The break-even is 21.51%, between two live US rates.
6. **Managed futures was called the one sleeve whose account decides its sign. That is a
   fact about DBMF, not about the exposure.** 2.09 pp/yr of distribution tax drag against an
   0.85% fee, and zero in a shelter — **but a dollar of the same trend notional obtained
   through the return-stacked wrapper RSST carries 0.32 pp/yr**, on each fund's own
   SEC-standardised after-tax table
   ([capital efficiency §6a.4](capital-efficiency-and-breadth.md)). The account still
   decides more than the product; it decides a great deal less than this page said.
7. **The wrapper was a single point of failure and is no longer one.** The equity-plus-trend
   overlay shelf is four live funds and a JPMorgan entrant at 0.59%, and the listed
   managed-futures shelf has gone from five products to fifteen with BlackRock, Fidelity,
   Invesco and Man Group among the entrants. **None of the newcomers has been tested against
   the benchmark**, so this removes a survival risk and adds no evidence.

---

## 1. The recommendation

### 1.1 The one parameter that changes the answer

Risk capacity — horizon, liabilities, cash flows, and the drawdown that would force a sale.
Four variants differing **only** in the equity share. No evidence here sets it: the declared
objective is net geometric growth as a *preference*, and the horizon and liability model
remain unchosen.

**[Setting the equity share](setting-the-equity-share.md) is the canonical page**, and it
works through why the objective alone returns a corner solution, what the estimation error
is worth, and the drawdown at every rung. It does not set the split either, and it explains
what would have to be supplied first.

**The anchor is a measured drawdown, not a risk questionnaire.** The US total market
returned **10.80%/yr geometric at 15.40% volatility with a −50.3% maximum drawdown and 72
months under water** over 1963-07…2025-12. Set the equity share at the level whose worst
case you would hold through, then stop.

**And set it against the right anchor, because that one is close to the best case.** Sixteen
countries of annual real total returns are now loaded
([JST R6](evidence-base.md)), and **in this same 1963-onward window every one of the other
fifteen did worse than the United States** — fourteen of fifteen worse than −50%. France fell
−97.7% from its 1942 peak and had not regained it 78 years later. The like-for-like US figure
on that annual real basis is **−47.2%, last of sixteen**. The full ladder, its interpolation
caveats and the basis mismatch are in
[setting the equity share](setting-the-equity-share.md#5-the-drawdown-anchor-which-is-the-operational-form-of-the-answer).

| Variant | Applies when | Equity | Bonds |
| --- | --- | ---: | ---: |
| **A — long horizon** | 20+ years, no liability inside it, contributions continuing, a −50% fall changes no plan | 90–100% | 0–10% |
| **B — mixed** | 10–20 years, or a known liability inside the horizon | 70–80% | 20–30% |
| **C — short horizon** | under 10 years, whatever the cash flows | 40–60% | 40–60% |
| **D — drawing down** | withdrawals begun over a long remaining horizon | **set by the withdrawal rate, not the horizon** | — |

Sequence risk is a cash-flow interaction, not a premium: without external cash flows,
permuting returns leaves terminal wealth unchanged, which is
[verified rather than asserted](setting-the-equity-share.md#3-sequence-risk-verified-and-given-a-sign)
across 20,000 reorderings.

**C and D point opposite ways, and were one row here until they were measured.** A short
horizon argues for fewer equities. A long retirement at a demanding withdrawal rate argues
for more: on CPI-deflated US returns over a 30-year draw, a 20%-equity portfolio taking 4%
real ran out in **6.82%** of reorderings against **2.43%** at 60% equity, and at a 5% real
draw the failure rate fell all the way to 90% equity. **Above roughly a 4% real draw,
holding too few equities is the larger risk.**

### 1.2 The holdings

Equity composition is identical in every variant. The weights are **the repository's own
declared research weights**, frozen in [Experiment 003](rebalancing-policy.md)'s
specification before any result was examined — **a stated choice, not a measured optimum.**
No global market-capitalisation series exists here, so no page can tell you the market
weight.

| Sleeve | Fund | ER | % of equity | Status of what it buys |
| --- | --- | ---: | ---: | --- |
| US total market | **VTI** (or ITOT, VOO) | 0.03% | 60 | the control |
| Developed ex-US | **VEA** (or IEFA at 0.07%) | 0.03% | 30 | the control |
| Emerging markets | **VWO** (or IEMG at 0.09%) | 0.06% | 10 | the control |
| Investment-grade bonds | **BND** (or a Treasury fund) | 0.03% | — | risk control, sized by variant |

**Use VXUS instead of VEA + VWO only if you will hold the whole international sleeve in one
account.** Splitting developed from emerging is what makes §3's placement result available,
and VXUS forecloses it.

Fees are dated lookups, not experiment results: VEA/BND 0.03% (Vanguard's published
endpoint, `expenseRatioAsOfDate` 2026-04-28), VWO 0.06% (2026-02-27), IEFA 0.07% and IEMG
0.09% (SEC-filed 497K fee tables, 2025-11-28 and 2025-12-30). Two qualifications: **IEMG's
fee table carries a waiver line currently at `(0.00)%`**, and a waiver sitting at zero can
be withdrawn, so IEMG's 0.09% is the least stable figure here; and both iShares tables
exclude acquired fund fees, so neither is all-in. **Where a figure is absent, look it up; do
not take a number from this page that this page does not have.**

### 1.3 The two optional sleeves, and nothing else

Both are second decisions, taken after the split, and both held **inside** the equity or
total allocation rather than added to it.

| Sleeve | Fund | ER | Size | Where | Verdict |
| --- | --- | ---: | --- | --- | --- |
| Small-cap value | **VBR** | 0.05% | 0–20% of US equity | treat as US equity in §3 | `exploratory` product, `exploratory` premium, **chain negative on the defensible reading**, and its marginal credit against an equity core is **−0.181 pp/yr per unit weight** |
| Managed futures | **DBMF** pro rata, or **RSST** as the overlay | 0.85% / 0.99% | 0–10% of total | DBMF **tax-deferred only**; RSST's drag is 0.32 pp/yr, so the shelter is no longer decisive for it | `exploratory` product, index `unresolved`. **DBMF is the pro-rata vehicle and gets the +2.44 pp/yr bar; RSST is the overlay and gets a bar near zero — see below.** Single-product risk has eased: the overlay shelf is four live funds and the listed managed-futures shelf is fifteen |

Two sizing notes, because both weights are judgements and neither is measured. **VBR's
yield is higher than the market's, which raises its shelter priority above plain US equity
— by how much is not measured here.** And **Experiment 004 priced a 15% trend sleeve, not a
10% one**: the cap is set below the tested weight because one product delivers the exposure
and there is no fallback, not because 10% was measured to be better.

Everything else tested is out: momentum (MTUM), quality (QUAL, SPHQ), large-cap value
(VTV), plain small-cap (VB), the other four managed-futures ETFs, rebalancing as a source
of return, and the small-value corner as the literature defines it.

**"Leverage and return-stacking" left that list on 2026-08-16, and has not joined the
table above.** [Capital efficiency and breadth](capital-efficiency-and-breadth.md) shows
that the funding rule alone moves a sleeve's hurdle by `a_p − sigma_p**2` — **2.44 pp/yr**
for a 100% equity base, containing nothing about the sleeve — and that this repository's
financing input was measured against a rate no fund pays
([above](structural-and-tax-edges.md#3-section-1256-and-capital-efficiency-handled-honestly)).
Measured on 426 months, a **25% trend overlay funded as notional rather than by selling
equity** contributes **ΔSharpe +0.050** at the repository's full 7.7 pp/yr CTA bias
haircut — **identical on a US and on a global base to three decimals** — while the same
base levered to the identical volatility contributes **+0.001**. That is the test that
separates breadth from beta, and it passes.

**The vehicle decides which bar applies, and this table names the wrong one.** Holding
DBMF beside equity means *selling equity to buy it* — the pro-rata rule, bar about
+2.44 pp/yr, which trend does not clear. A return-stacked ETF delivers a dollar of
equity *and* a dollar of managed futures per dollar held, so nothing is sold — the
overlay rule, bar near zero. **Same strategy, same evidence, opposite verdict, decided
by the ticker.**

**The shelf that follows has now been audited from the filings**
([capital efficiency §6a](capital-efficiency-and-breadth.md)), and four things it found
belong here because they move what a reader should hold.

- **RSST's overlay claim checks out and its cost is filed.** 107.2% equity plus a ~100%
  trend sleeve at 2026-04-30; **0.99% all-in including 0.04% of acquired fund fees, with no
  waiver and — from Form N-CEN — no recoupment clause**; $508.7m at 2026-08-14 and growing
  faster than any other wrapper on the shelf.
- **The tax gap between the two vehicles is 1.77 pp/yr and runs the other way from this
  page's framing.** RSST 0.32 pp/yr of distribution tax drag, DBMF 2.09, each from its own
  SEC-standardised after-tax table. The mechanism is that a tax-favoured equity sleeve shares
  RSST's capital, **not** that its trend sleeve is taxed better — RSBT and RSBY, whose base
  leg is bonds, distribute 100% ordinary income like DBMF.
- **The successor is named.** **CTAP** (Simplify U.S. Equity PLUS Managed Futures, $123.4m)
  is the only live alternative above $100m; it obtains its trend leg through a **total return
  swap** rather than futures, and its swap financing rate was not established. **JPFP**
  (JPMorgan Managed Futures Plus) offers the same structure at a **0.59% unitary fee** and
  has not commenced operations, so it has no assets, no holdings and no record.
- **What is worse than this page assumed is the financing.** No wrapper on the shelf
  quantifies its financing cost anywhere, and the accounting hides it: every Return Stacked
  fund reports **0.00% of interest expense** because futures financing is embedded in the
  contract price. The family's only disclosed rate is RSBA's merger-arbitrage swap at
  **OBFR + 6.64%**, up from OBFR + 3.00% one quarter earlier.

**And this page's claim that "none of it is six years old" was wrong and is withdrawn.**
NTSX appears in the 2019Q4 census — as "WisdomTree 90/60 U.S. Balanced Fund" — and is eight
years old; PIMCO has run StocksPLUS since the 1980s. What survives is narrower: **RSST itself
is under three years old.**

**It is still not promoted, for three reasons that are not about the arithmetic.** The
trend leg rests on a vendor series stating no cost basis anywhere, against a bias bound
of 7.7 pp/yr and a break-even near 9.9 — a bound that has since been measured against 46
real funds' net returns and found to point the *other* way over 2019–2025, at −2.62 pp/yr
`[−10.91, +5.68]` ([live managed futures](live-managed-futures.md)), which changes the size
of the uncertainty without removing it. The overlay's *return* contribution spans zero
across the haircut range while only its *risk* contribution is robust — so it is a
risk-reduction claim, and must be judged on mechanism rather than on relative performance.
And [decision 0004](../decisions/0004-no-sleeve-promoted.md) still holds leverage at zero;
what changed is that the cost of that rule is now a measured number rather than an
assumption, and its block on step 7 is recorded as circular.

### 1.4 The disciplines, which are worth more than the sleeves

| Discipline | Worth | Conditional on |
| --- | ---: | --- |
| Hold index funds rather than the average active dollar | **49 bp/yr** | **nothing — the only unconditional line** |
| Hold ETFs (or Vanguard's dual-share-class funds) rather than active mutual funds in taxable | +23 bp | a taxable account and an active counterfactual. **Decaying** |
| Tax-loss harvesting, only with contributions and only at a 9–12 bp fee | 30 bp gross, **25.6 net** | a taxable account, direct ownership, offsetting gains, new money |
| Asset location, computed rather than asserted (§3) | 10 bp less 3.4 of forfeited foreign tax credit | more than one account type |
| Specific identification of lots, as a standing instruction | +5 bp | ever selling |
| Do not turn the taxable account over | avoids an **84 bp/yr hurdle** at 30 years | a taxable account |
| Rebalance to hold the declared weights | 0.3–1.2 bp/yr in cost; **not a return** | — |
| **Total against your own counterfactual** | **up to ≈109 bp/yr** | **outer range 4 to 270** |

The 84 bp is a **hurdle, not a saving**. Deferral plus the §1014 step-up is a horizon-free
**162 bp/yr**, and the function is sharply concave, so **"low turnover" is not a defence**:
realising 10% of standing gain a year already costs 41.5 bp of the 84.1.

---

## 2. Line by line: what each holding buys, and at what confidence

`Contractual` means an accounting identity or statutory fact whose sign is known in advance.
`Risk premium` means a bet whose sign is not known at any horizon a human has. `Nothing
better exists` means the alternatives were tested and lost.

| Holding | What it buys | Class | Why it is here |
| --- | --- | --- | --- |
| **VTI / VOO / ITOT** | equity risk premium at 3 bp, ~1.3 bp round trip, plus 1.01 bp/yr of lending pass-through | **contractual** on the *cost*; risk premium on the *return* | It is the control. Every candidate was measured against it and none beat it |
| **VEA / IEFA** | developed ex-US equity; ~2.97 / ~1.08 bp/yr of lending income | same | Diversification of the equity claim, not an edge. Its foreign tax credit is worth 15.78 bp/yr **only in taxable** |
| **VWO / IEMG** | emerging equity; ~4.9 / ~9.2 bp/yr of lending income | same | Same. Its credit is worth 20.00 bp/yr in taxable, and it is the sleeve §3's arithmetic moves |
| **BND** or Treasuries | term and credit compensation, and a risk brake | **a different benchmark, not an edge** | Sized by risk capacity. **The brake works; its diversification does not, in every era** — the bond–stock beta was positive to 1999, negative to 2022Q3, positive again to 2024Q2, and negative on the 18 months since, on this repository's own data |
| **VBR** (optional) | HML loading **+0.410 `[+0.322, +0.480]`**, delivered and stable, at 5 bp, with a **negative** shortfall against a fitted four-fund combination | **risk premium**, `exploratory` on both terms | **Low confidence.** The chain is +0.09 to −0.39 pp/yr on the US premium and +0.28 to +0.76 on the pooled one. It is here because it is the only US value product that both delivers its exposure and does not lose to a cheap combination — **not because the chain is positive** |
| **DBMF** (optional) | loading **+0.671 `[+0.513, +0.829]`** on the AQR index, stable across the split and all 19 rolling windows, trailing a cost-free index by 0.48 pp/yr against an 0.85% fee | **risk premium**, `exploratory`; the index itself `unresolved` | **Nothing better has been measured**, which is not the same as nothing better existing: four of the five tested funds fail the 0.50 bar and **ten more listed funds have never been tested**. Crisis correlation −0.59 and payoff spread across four crises — but the post-publication interval includes zero and fails Holm |
| **RSST** (optional, in place of DBMF) | the same trend exposure as an **overlay** rather than pro rata, so the sleeve's hurdle falls by about 2.44 pp/yr; 0.99% all-in, no waiver, no recoupment; 0.32 pp/yr of distribution tax drag | **risk premium**, `exploratory` on the product and `unresolved` on the index — **the wrapper changes the hurdle, not the evidence** | **Its loading on the benchmark has never been measured.** It is named because its structure is verified from N-PORT and its costs from filings, not because anything here says its trend leg delivers |
| **Cash reserve** | optionality and the ability not to sell | contractual | The framework requires it and **no experiment here sizes it** |

### What is deliberately absent

| Excluded | Reason |
| --- | --- |
| **MTUM**, and any momentum sleeve | Delivers its exposure (UMD +0.444) and is still `rejected`: a 1.22 pp/yr shortfall to a three-fund combination whose fee premium over it was 0.12. It is the **entire** retail momentum shelf |
| **VTV**, large-cap value | HML +0.337, but a +2.57 pp/yr shortfall — and its replication is degenerate (VTI + VB), so read that as "value underperformed the market over these 72 months", not as a defect |
| **VB**, plain small-cap | Largest shortfall on the shelf, +2.89 pp/yr; and **the size premium is not signable**: +1.91 `[−1.90, +6.00]` over 750 months against a 4.73 threshold |
| **QUAL, SPHQ**, quality | RMW is `rejected` and closed on public data. **An unsigned premium makes the product's own quality irrelevant** |
| **CTA, FMF, KMLM, WTMF** | Loadings 0.475, 0.303, 0.245, 0.099 against a 0.50 bar. Read KMLM as "not *this* index" — its own index holds no equity futures while AQR's holds nine |
| **NTSX and any 90/60 return-stacked fund** | Needs **48.3 bp/yr** of Treasury excess return over cash before the overlay contributes, at the 15 bp OIS financing benchmark. **This row previously said 92.0 bp against a 58.70 bp basis; that basis was measured against special-collateral repo, which is not a rate a fund pays** ([structural and tax-aware edges](structural-and-tax-edges.md#3-section-1256-and-capital-efficiency-handled-honestly)). Both inputs remain forecasts |
| **Leverage of any kind** | Zero, and it stays zero. Conditioned on an unlevered edge surviving the protocol; none has |
| **Rebalancing as a source of return** | `rejected`: **−38.7 bp/yr** over 420 months, drift gap ~35× `gamma_star`, and relative regional performance **trends** rather than reverts |
| **The academic small-value corner** | ME1 × BM5 held 21.24% of listed firms and **0.236% of market capitalisation**. Not implementable at retail in size |
| **Gold** | **Tested 2026-08-17 under both funding rules and excluded on return, not on absence.** The claim that it is "not a universal negative-correlation asset" is **confirmed**: correlation to US equity of −0.02 to +0.03 unconditionally and −0.04 to +0.08 inside equity drawdowns — **zero, not negative**. On the only window a US person could legally own it, 1975-01 onward, its Sharpe ratio is **0.18 against equity's 0.59**, and everything follows from that. It passes admission; funded pro rata (what GLDM imposes) it loses 0.40 pp/yr; funded as an overlay (what GDE imposes) it **gains 0.18 pp/yr against the leverage-matched control — below the 0.30 bar and below its own 0.73 detection floor**, and at GDE's own notional the matched-volatility control rejects it. Beside a 30% trend overlay it **adds** rather than substitutes (correlation +0.07, breadth 1.00 → 1.87, drawdown −44.8% → −43.7%) by +0.09 pp/yr against an MDE₈₀ of 1.68. Tax decides placement and not the verdict: GLDM pays **28% + 3.8%** on a deferrable gain, GDE distributes 100% ordinary income at a measured **1.53 pp/yr** ([marginal sleeve value § Gold, tested](marginal-sleeve-value.md#gold-tested)) |
| **Tail hedges, private credit, cat bonds, merger arb** | **Untested here.** A protective put must be benchmarked against a **return-matched** equity/cash mix |

---

## 3. Account placement, worked through

**The rule.** The right metric for a scarce shelter is what a sheltered dollar **saves**:

```
priority = (recurring tax if held in taxable) − (irrecoverable withholding if sheltered)
```

For every asset except a foreign one the second term is zero and this collapses to the
familiar rule. Foreign withholding is **paid and permanently lost** inside a traditional IRA
and a Roth alike — an IRA has no tax to credit against and a §904 numerator of zero. **No
IRS publication states this; it is asserted from the statute.**

Priority per dollar of shelter capacity, bp/yr, with the inputs dated in
[structural and tax-aware edges](structural-and-tax-edges.md) §1:

| Asset | **23.8%** | **18.8%** | **15%** |
| --- | ---: | ---: | ---: |
| Taxable investment-grade bonds | **189.7** | 189.7 | 189.7 |
| Developed ex-US equity | **46.1** | **33.1** | **23.2** |
| Emerging-market equity | **28.3** | 18.2 | 10.45 |
| US equity | 26.2 | **20.7** | **16.50** |

**One caveat, or the table is internally inconsistent.** 189.7 uses the 40.8% top ordinary
rate, which belongs with the 23.8% column; a taxpayer whose qualified rate is 15% faces an
ordinary rate nearer 22%, so the bond line falls to roughly 102 bp. **It still dominates by
more than four to one**, which is why the ranking does not move.

| Rate | Fill order | The reversal |
| --- | --- | --- |
| **23.8%** | bonds → developed → emerging → US | Conventional order survives, but emerging's margin over US collapses to **2.1 bp**. Treat it as a tie |
| **18.8%** | bonds → developed → **US** → emerging | **Inverted** |
| **15%** | bonds → developed → **US** → emerging | **Inverted**, by 6.05 bp |
| **0%** | the credit is worth nothing either way | §904 limits the credit to US tax on foreign-source income, and there is none |

### By account

| Account | Holds, in this order | Why |
| --- | --- | --- |
| **HSA** (if a high-deductible plan applies) | equity, highest-growth sleeve | The only US account untaxed at all three points. **A dollar limit, not a rate**: $4,400 self-only / $8,750 family for 2026. **California breaks the deduction and taxes internal earnings annually**; New Jersey is widely reported to do the same and no primary source was found |
| **Traditional 401(k)/IRA** | bonds first, then developed ex-US, then per the table. **DBMF here if held at all** | Bonds dominate by four to one. DBMF's 2.09 pp/yr distribution tax drag is zero here. **A trend overlay held through RSST does not need this shelter nearly as much** — 0.32 pp/yr of drag, so a 15% sleeve forfeits about **5 bp of portfolio return** by sitting in taxable rather than the **31 bp** DBMF forfeits, and the shelter it would have consumed is better spent on bonds |
| **Roth** | the highest-expected-growth sleeve that fits after bonds | Identical to traditional on foreign withholding — both forfeit it. **The traditional-vs-Roth choice itself is a rate forecast, not a structure** |
| **Taxable** | US total market; emerging-market equity at 15% or 18.8%; whatever does not fit above | ETFs, specific-ID lots as a standing instruction, no turnover |

Three conditions that decide more than the ranking. **A tax-deferred balance is not the
investor's money** — at a 24% withdrawal rate $100,000 of traditional IRA is $76,000 of
investor wealth, so an allocation stated on nominal balances misstates true equity exposure.
**Below $300 of creditable foreign tax ($600 joint)** the credit is claimed without Form
1116 and without the §904 limitation, a threshold reached at about $190,153 of holdings and
never indexed. And **wash-sale scanning must be household-wide**: Rev. Rul. 2008-5 disallows
a loss where the replacement is bought in the taxpayer's IRA **and does not increase the
IRA's basis**, destroying the deduction rather than deferring it — 119 bp outright on a
5%-of-portfolio disallowance.

**Two omissions that cut against the emerging inversion**, neither quantified: a shelter
also shelters capital-gain distributions and rebalancing turnover, which emerging funds
generate more of; and a taxable international position is a better loss-harvesting
candidate. **Either could close a 6 bp gap.**

---

## 4. Verdict on the proposed portfolio

The proposal: **US 45% / international 35% / other 25%**, with small-cap value, momentum and
managed-futures sleeves. **It sums to 105%**, and that matters because it is ambiguous which
sleeve absorbs the five points.

| Sleeve | Verdict | Reason |
| --- | --- | --- |
| **US 45 / international 35** | **Supported, as an investor choice.** No change required | A 56:44 US:ex-US split against the repository's declared 60:40. **No page here can distinguish them** — there is no global market-capitalisation series here and no experiment signed a regional tilt. Choose either and stop |
| **"Other" 25%** | **Underspecified. Split it** | If bonds, they go in the shelter first by a factor of four. If managed futures at anything like 25%, far too large for a sleeve whose index is `unresolved` and whose only delivering product is one fund |
| **Small-cap value** | **Reduce, and know what you are buying.** 0–20% of US equity, via VBR | On the size-neutral capture (0.520) and the US-only premium (+1.57) the chain is **+0.09 to −0.39 pp/yr — negative on the defensible reading of both terms.** It is positive only on the pooled premium *and* the market-relative capture, and the gap between those captures is **a size premium wearing a value label** — which the size test then failed to sign. Judged marginally it gets worse: US small value's beta to an equity core is 1.083, so its credit is −0.181 pp/yr per unit weight |
| **Momentum** | **Drop** | **Not because the premium is weak** — it is the largest gross factor measured here, pooled **+7.33 pp/yr**. Because its detection threshold is 4.98 pp/yr, the worst here; its three regions are worth 1.33 effective regions and **crash together**; the academic construction rebalances **monthly** with an assumed cost of 3.30–18.67 pp/yr against that 7.33; and the entire retail shelf is MTUM, `rejected` on cost |
| **Managed futures** | **Keep, smaller. The account rule applies to DBMF and much less to RSST** | **Only DBMF's loading has been measured against the benchmark**, on three independent measurements, and the other fourteen listed funds are untested rather than rejected. DBMF's tax drag is 2.09 pp/yr — 2.5× its own fee, zero in a shelter; **RSST's is 0.32**, and RSST is also the vehicle that keeps the funding-rule benefit |

### What changed since the earlier answer to the owner

Six corrections, all running against what was said before.

1. **Momentum is the strongest gross factor, not the weakest.** The case against it is
   entirely turnover, product shelf and a shared crash — not the premium.
2. **Trend is `unresolved`, not `rejected`.** Experiment 004's clause (d) was ambiguously
   specified, and under the reading
   [Experiment 008 judges better justified](trend-marginal-value.md#which-reading-is-better-justified)
   the verdict is `unresolved`. **`unresolved` is not a promotion.**
3. **Experiment 004's verdict was repeated as though it applied to KMLM, DBMF and CTA. It
   evaluated an index.** Experiment 008 tested the products and reached a different answer
   for DBMF.
4. **The long-only capture fraction is measured, and it makes a US-only long-only value tilt
   negative after cost.** Five benchmarks span 0.846, which is why Experiment 007 is
   `rejected` on its own dispersion clause: **what was rejected is not the capture fraction
   but the premise that there is one.**
5. **The chain that judged every sleeve here except trend was the wrong shape.**
   `premium × loading × capture − cost` sets the covariance term to zero by construction.
   [Experiment 010](marginal-sleeve-value.md) added it. **No holding moves; the reasoning
   behind three of them does** — and the marginal view makes the equity tilts look *worse*,
   because a beta above one makes the credit negative.
6. **Zero ex-US factor products had been audited, and twelve now reach `exploratory`.** What
   [Experiment 009](factor-products.md) found is a **cost** problem rather than an exposure
   problem — with one exception that matters here: **no emerging product reached
   `exploratory` at all.**

---

## 5. What each tilt costs in confidence terms

`P = Phi(e sqrt(T)/s)` and `T = (z s/e)**2`. **The horizon scales with the square of `s/e`,
so tracking error and not edge size decides whether a lifetime is enough.** Every
probability below is an **upper bound**: the machinery treats `e` as known.

| Line | Edge | TE | P(30 yr) | 90% at | 99% at |
| --- | ---: | ---: | ---: | ---: | ---: |
| **Cost + tax + placement, vs your own counterfactual** | **109 bp** | 46 bp* | ~1.00 | **3.5 months** | **~12 months** |
| The whole honest budget **vs a cheap index** | 24 bp | 401 bp | **0.631** | ~443 yr | — |
| Best case for a 20% small-value tilt | 15.2 bp | 140 bp | 0.724 | 139 yr | ~460 yr |
| Worst case for the same tilt | **−7.8 bp** | 140 bp | **0.380** | never | never |
| Best case for a 15% trend sleeve in a shelter | 88 bp | 251 bp | 0.973 | 13 yr | ~44 yr |

\* **assumed**, not measured, and the components are not independent.

**A 20% small-value tilt, all four corners.** Gross contribution is
`weight × loading × capture × premium`; cost is Experiment 007's assumed sort turnover plus
VBR's 5 bp fee, giving about 0.25–0.73 pp/yr; tracking error is taken at **7 pp/yr**, inside
Experiment 002's measured 1.38–8.65 range — **an assumption, since VBR's own tracking error
is not published anywhere here.**

| Premium used | Sleeve cost | Net edge | **P(30 yr)** | 90% confidence at |
| --- | --- | ---: | ---: | ---: |
| Pooled +4.74 pp/yr | 0.25 | **+15.2 bp** | **0.724** | 139 yr |
| Pooled +4.74 | 0.73 | +5.6 bp | 0.587 | 1,026 yr |
| **US-only +1.57** | 0.25 | +1.8 bp | 0.528 | ~10,000 yr |
| **US-only +1.57** | 0.73 | **−7.8 bp** | **0.380** | never |

**That table is the whole case, for and against.** The best corner requires believing a
premium whose weight sits in the two regions where shorting is hardest and where no audited
product exists here; the worst corner is a persistent loss. **At no corner is the tilt
demonstrable from the investor's own experience.**

**A 15% managed-futures sleeve.** Experiment 004 measured the **index** at +1.312 pp/yr of
marginal growth against a risk-matched cash comparator, falling to **+0.883 post-publication
with an interval that includes zero and fails Holm**. DBMF delivers 0.671 of that exposure.
Tracking error is **derived**, not published: 2.52 pp/yr from Experiment 004's own
volatilities and correlation.

| Case | **Net edge, growth** | TE | **P(30 yr)** | 90% at |
| --- | ---: | ---: | ---: | ---: |
| Post-publication, **tax-deferred** | **+59 bp** | 251 bp | 0.902 | 30 yr |
| Post-publication, **taxable through DBMF** (less `0.15 × 2.09`) | **+28 bp** | 251 bp | 0.729 | 133 yr |
| Post-publication, **taxable through RSST** (less `0.15 × 0.32`) | **+54 bp** | 251 bp | **0.883** | **35 yr** |
| Full-period, tax-deferred | +88 bp | 251 bp | 0.973 | 13 yr |

**The account was the largest controllable term and the wrapper has displaced it.** Choosing
the shelter over taxable is worth **31 bp/yr** through DBMF; choosing RSST over DBMF is worth
**26 bp/yr in taxable and nothing at all in a shelter**, and it also removes the 2.44 pp/yr
funding-rule hurdle that the shelter does nothing about. **Both are larger than the whole
fee, and the wrapper decision comes first because it changes which bar the sleeve is judged
against.**

Against those probabilities: the index's standalone Sharpe fell 1.34 → 0.18, the vendor
states **no cost basis anywhere**, comparable CTA survivorship distortion is bounded at
7.7 pp/yr — a bound the only live measurement available contradicts in sign
([live managed futures](live-managed-futures.md)) — and **one product's loading has been
measured, on a shelf of fifteen.** These rows use DBMF's measured loading throughout; **no
loading has ever been measured for RSST**, so the RSST row prices a tax difference on
DBMF's evidence and must not be read as a claim about RSST's trend leg.

**The comparison that decides the page.** A conditional 109 bp settled in about twelve months
is worth more than any tilt's gross premium, and it is available first. **That is not a
rhetorical preference; it is what the pairing of edge and tracking error produces.**

---

## 6. What would change this

Each is measurable and dated. None is a hope.

| Condition | What it changes |
| --- | --- |
| **ETF share classes are adopted broadly.** 94 SEC orders granted `as of 2026-08-11`; only two applications remain unordered | The +23 bp line goes towards zero and the budget falls to about 86 bp. **Recheck the order count first** |
| **§852(b)(6) is repealed.** A 2021 Senate Finance draft proposed exactly that; never enacted | Removes the ETF wrapper advantage outright |
| **A qualified-dividend rate below 10.52%, or at or above 21.51%** | Below: developed ex-US belongs in taxable too. At or above: emerging returns to the shelter and §3's inversion disappears |
| **A licensed, survivorship-free, point-in-time total-return source from at least 2003** | Lifts the product audits above `exploratory` for the first time. Without it, VBR and DBMF cannot be promoted **or** properly rejected |
| **JPFP commences operations and files an N-PORT** | The same 100/100 structure as RSST at a **0.59%** unitary fee from a far larger sponsor. It would reorder the wrapper cost ranking outright. It has no assets, no holdings and no record today |
| **An audited emerging value product** | **Still the gap, and it is now a gap in the *shelf* rather than in coverage.** The value premium's weight is +7.58 pp/yr in emerging; the whole emerging shelf clearing the screen is four funds, two rejected and two unresolved on 44- and 51-month windows |
| **A second managed-futures ETF with a loading ≥ 0.50** on a per-fund benchmark from its own stated universe | Removes DBMF's single-product risk and separates "does not deliver trend" from "does not deliver *this* trend". **Half met: the shelf went from five funds to fifteen, so the candidates now exist — none has been tested** |
| **A measured one-sided monthly turnover below 50% for a long-only momentum fund** | Reopens momentum. **The 27.5–91.5%/month figure belongs to a monthly-rebalanced academic long-short spread and must never be applied to a fund** |
| **A measured implied financing spread, a signed term premium, a defined investor policy, and a modelled forced-liquidation path** — all four | Reopens capital efficiency and the zero-leverage rule |
| **A further decade of RMW/CMA data, or a non-French construction** | Nothing else reopens them. Pooled MDE₈₀ scales as `1/sqrt(T)`: reaching 2.0 from 2.62 needs ~245 months, about 2035 |
| **A re-specified portfolio-level test** at the weight cap, with named-leg funding and a ceiling-derived bar | Reopens whether a diversifying sleeve can pay inside a portfolio. **The current closure is weight-dependent** ([search coverage](search-coverage.md) §1.1) |

---

## 7. What this is not

- **Not personalised advice.** A construction derived from measurements, for a stated
  reference investor.
- **Not a forecast.** No expected return for any market appears here. The probabilities in
  §5 are conditional on edges being what the cited pages measured, and are upper bounds.
- **Not a promotion.** **No sleeve reached `production-eligible`, `walk-forward-tested`, or
  even `independently-reproduced`.**
- **Not a claim of outperformance against an index.** Against a cheap index the whole honest
  budget is ~24 bp against 401 bp of tracking error.
- **Not net of everything.** No page here has a full after-tax, after-spread, after-turnover
  return for any product. Bid-ask, brokerage, realised distributions and portfolio turnover
  are absent from the product audits entirely.
- **Not free of model risk.** FF5+UMD prices **VTI itself** at −0.55 pp/yr with a HAC *t* of
  −3.41. **The standard model does not span the control**, and every alpha here is a distance
  from that pedestal, not from zero.
- **Not vintage-stable.** Ken French rebuilds the whole history on every release, and the
  Phase 1 gate is `unresolved`, leaving a **systematic 3–5% band** on anything that divides
  by an HML or RMW volatility. **Five series carry no measured band at all**, including all
  three momentum files.

### The investor-policy inputs still missing

Without these, §1.1's variants are ranges rather than an answer, and no page here can narrow
them. [Setting the equity share](setting-the-equity-share.md) §7 sets out which an
application may compute on and which it must ask for:

horizon and liability model; drawdown and shortfall tolerance, and the loss that would force
a sale; cash flows in and out, and whether contributions continue; marginal federal **and
state** bracket, now and expected at withdrawal; balances by account type and remaining
contribution capacity; high-deductible-plan status; existing lots and their basis; employer
stock in a qualified plan; currency and home-country bias; capital scale; permitted
instruments; liquidity reserve in days; and the objective — **net geometric growth is
declared as a preference here, and a consumption or shortfall objective would change the
answer.**

---

## Verified, assumed, open

**Verified elsewhere and quoted here.** Every number traces to a page, an artifact or the
ledger: the ≈109 bp budget and its lines
([structural and tax-aware edges](structural-and-tax-edges.md), regenerated by
`studies/tax_structure.py`); the break-evens of 10.52% and 21.51%; the long-only capture and
its 0.846 spread ([Exp 007](long-only-capture.md)); pooled HML +4.74 and UMD +7.33 with
their thresholds and effective region counts ([Exps 005 and 006](factor-persistence.md));
every fund loading, fee and status ([Exps 002 and 009](factor-products.md),
[Exp 008](trend-marginal-value.md#experiment-008--the-products)); the trend marginal growth
of +1.312 falling to +0.883 ([Exp 004](trend-marginal-value.md)); every sleeve's beta to the
equity core ([Exp 010](marginal-sleeve-value.md)); and the −38.7 bp rebalancing result
([Exp 003](rebalancing-policy.md)). **Every wrapper structure, fee, waiver, tax-character
and net-asset figure** traces to
[capital efficiency §6a](capital-efficiency-and-breadth.md), which takes them from N-PORT
holdings, 497K fee tables, N-CSR tax-character tables and N-CEN recoupment flags.

**Assumed on this page, and nowhere else.**

1. **A 7 pp/yr tracking error for a value sleeve.** Inside Experiment 002's measured range
   for *other* funds, but **VBR's own is not published anywhere here.** §5 is proportionally
   sensitive to it in the horizon column and not in the sign.
2. **That a trend sleeve's marginal growth scales linearly in the product's loading.**
   `0.671 × 0.883` is an approximation; the experiment measured the index at a 15% weight,
   not DBMF at any weight, and Experiment 008's own marginal arm is **labelled invalid for
   every fund**. **A second reason to distrust the scaling exists**: Experiment 010b measured
   a 10% trend sleeve against a global equity core and got +0.258 pp/yr, which fails its
   0.30 bar. The two answer different questions and neither transfers, but a reader entitled
   to one of them should know the portfolio-level one is smaller.
3. **A derived 2.52 pp/yr portfolio tracking error for the trend sleeve**, computed against
   the *fully invested* benchmark rather than the risk-matched comparator the experiment
   used as primary.
4. **Experiment 003's US 60 / developed-ex-US 30 / emerging 10 as the equity composition.**
   A declared research weight, not a measured optimum and not a market weight.
5. **That VBR's 5 bp fee substitutes for the 15–25 bp assumed in Experiment 007's cost
   table.**
6. **That RSST's measured tax drag may be substituted into a chain built on DBMF's measured
   loading.** §5's RSST row changes one term of a four-term chain and leaves the other three
   at DBMF's values. **RSST's loading on the benchmark has never been measured**, its
   after-tax table covers 28 months, and nothing licenses assuming the two funds deliver the
   same exposure. The row prices a tax difference, not a product.

**Open.** Which benchmark a factor line may book its capture against — the answer moves the
line by a factor of two and a half. What a real fund's delivered capture is; every figure
here is from research portfolios, and measuring a fund's own **needs holdings rather than
returns**. Whether the emerging inversion survives capital-gain distributions and harvesting
value. What a liquidity reserve should be, unsized. **What any of the ten untested listed
managed-futures ETFs, or RSST's own trend leg, load on the benchmark** — the shelf tripled
and the evidence did not move. **What any wrapper actually pays to finance its overlay** —
no fund discloses it, and the only rate the shelf does disclose is OBFR + 6.64%.

---

## Consequence for this repository

1. **This page is where a named-fund construction lives, and the only place.** The framework
   answers *whether a return source is real*; this page answers *what to hold given that*.
   **It must never state a premium, a status or a cost that its source page does not.**
2. **The application may render this, under four constraints and not otherwise**
   ([decision 0007](../decisions/0007-application-may-render-research.md)): only from
   `src/content/`; only with status, `as of` date, interval and source attached; never
   aggregated across benchmarks; and with client arithmetic tested against fixtures the
   research workspace generates. `exploratory` is displayed as `exploratory`. **A number
   hardcoded in a route is a defect.**
3. **The asset-location ranking must be computed, not asserted**, and must state the bracket
   it assumed.
4. **Four review triggers**: the fund-structure line (94 SEC orders and rising); every
   fund-specific fact in §1.2; **JPFP's commencement**, which would reorder the wrapper cost
   ranking at 0.59% against RSST's 0.99%; and **KMLM's shareholder vote around 2026-11-20**,
   the fund having operated under interim advisory agreements since a change of control on
   2026-06-23.
5. **The largest evidence gap this page exposes is a product gap, not a premium gap.** The
   value premium was measured where no product here has been audited, and the momentum
   premium on a construction no product can implement. Both are fixable with the same
   purchase.
6. **The wrapper is a separate decision from the sleeve, and it is decided first.** Which
   fund delivers a diversifier changes the hurdle that fund must clear by up to 2.44 pp/yr
   and its tax drag by up to 1.77, before any question about whether the strategy works. **No
   sleeve on this page may be named without naming its funding rule**, and
   [capital efficiency §6a.1](capital-efficiency-and-breadth.md) gives the one number —
   `delta = (1 − b) / d` — that states it. A gross-notional figure from a fact sheet does
   not.
7. **Naming a wrapper is not evidence about the strategy inside it.** RSST is named here on
   verified *structure* and filed *costs*. **Its loading on the trend benchmark has never
   been measured**, and neither has that of the ten new listed managed-futures ETFs. The
   shelf tripled; the evidence did not move.
</content>
