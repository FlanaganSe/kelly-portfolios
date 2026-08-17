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

`as of 2026-08-17` for the wrapper and managed-futures product facts and for **every
core-fund cost fact in §1.2**, `2026-08-12` for everything else. US federal individual
investor, state tax excluded and additive **except in §3.1, which is worked for one named
California investor and says so.**

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
   shelter**. The break-even is 21.51%, between two live US rates — and on eleven funds'
   filed withholding it is more likely **24.4% to 27.5%**, above every US rate, which would
   widen the inversion rather than close it.
6. **The four funds holding the whole portfolio were chosen on expense ratio and have now
   been audited on cost. They survive, by 0.60 bp/yr.** Twenty-five funds and 110 Form
   N-CEN filings: `fee − securities lending` puts **IEMG below VWO on a 50% higher fee**
   and makes **BND the dearest bond fund on the shelf** because it is the only one that
   does not lend. Capital-gain distributions are **zero everywhere**, so no fund choice
   here buys any of the +23 bp line. **VXUS costs 5 bp, not the 3 this repository had
   recorded, so splitting the international sleeve is cheaper before any placement
   argument.** And **VTI against VOO is 1.78 bp/yr of lending and nothing else** — a
   0.52 probability of being ahead after thirty years.
7. **"Managed futures is the one sleeve whose account decides its sign" is withdrawn. It
   was a fact about DBMF, not about the exposure, and it is smaller than it looked even
   there.** 2.09 pp/yr of distribution tax drag against an 0.85% fee, and zero in a shelter
   — **but a dollar of the same trend notional obtained through the return-stacked wrapper
   RSST carries 0.32 pp/yr**, on each fund's own SEC-standardised after-tax table
   ([capital efficiency §6a.4](capital-efficiency-and-breadth.md)). **And 0.32 is still the
   wrong comparison**: RSST is bought *instead of* the plain equity fund it contains, which
   pays 26.7 bp of its own, so **the incremental cost of holding the overlay in a taxable
   account is 4.5 bp per dollar — 1.3 bp of portfolio return at a 30% overlay**
   ([§7.2](capital-efficiency-and-breadth.md)). **The account decides DBMF's sign. It does
   not decide RSST's, and no weight or placement on this page may be justified by that
   claim again.**
8. **The overlay weight was a corner solution against that constraint, and it survives its
   removal for a different reason.** Re-derived without it, the growth optimum is **3.04
   units of notional, 2.14 after twenty years of shrinkage** — and is refused, on the same
   grounds as this repository's 2.2× levered-equity optimum. What binds is the **resampled
   drawdown, which doubles between `w = 0.58` and `w = 0.60`**, giving a ceiling near
   **0.55**; and, for an investor whose taxable account carries unrealised gain they will
   not realise, the capital that can be moved at all. **The recommended weight does not
   move. Every reason previously given for it does.**
9. **The wrapper was a single point of failure and is no longer one.** The equity-plus-trend
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

| Sleeve | Fund | ER | Lending | **Net cost** | % of equity | Status of what it buys |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| US total market | **VTI** (or ITOT) | 0.03% | 1.84 bp | **1.16 bp** | 60 | the control |
| Developed ex-US | **VEA** (or SPDW) | 0.03% | 3.30 bp | **−0.30 bp** | 30 | the control |
| Emerging markets | **VWO** (or IEMG) | 0.06% | 4.33 bp | **1.67 bp** | 10 | the control |
| Investment-grade bonds | **BND** (or SPAB, or a Treasury fund) | 0.03% | **none** | **3.00 bp** | — | risk control, sized by variant |

**These four have now been audited on cost rather than on fee, and they survive by
0.60 bp/yr.** Twenty-five funds, 110 Form N-CEN filings, eight fiscal years, in
[structural and tax-aware edges §6](structural-and-tax-edges.md#6-the-core-beta-shelf-audited-on-cost-rather-than-on-fee).
`Net cost` is `expense ratio − net securities-lending income`, both measured against the
fund's own net assets; the fee is contractual and filed, the lending is a **median over
every fiscal year on file** and is a measurement rather than a promise. At the reference
60/14/6/20 allocation the recommended four cost **1.36 bp/yr**, the cheapest combination
available anywhere on the shelf — ITOT, SPDW, IEMG, SPAB — costs **0.76**, and the dearest
plausible one costs **3.12**. **The entire fund-selection decision is 0.60 bp/yr against a
84 bp/yr turnover hurdle and a 49 bp fee line**, which settles the order in which the
decisions matter.

Three things the old fee table could not say.

- **IEMG charges 9 bp against VWO's 6 and costs less to own**, because its lending income
  covers the fee and 0.87 bp besides. Same at State Street: SPDW's 3 bp fee is covered
  twice over, making it the cheapest developed ex-US fund on the shelf. **VWO and VEA are
  kept because the gap is 0.15 and 0.19 bp of the portfolio, not because they win.**
- **BND is the only fund of the four that is beaten by more than a basis point.** It does
  not lend at all — Vanguard answers Item C.6.a "No" in all eight fiscal years — so at an
  identical 3 bp fee it is the dearest aggregate-bond fund audited. SPAB costs 2.09.
- **`(0.00)%` waiver lines were the wrong worry.** This page previously called IEMG's the
  least stable figure on it. Its footnote is an expense **cap** — BFA "has contractually
  agreed to waive a portion of its management fee such that the Fund's total annual fund
  operating expenses after the fee waiver will not exceed 0.09% **through December 31,
  2030**" — with no recoupment, which makes it the most durable fee commitment here. **The
  only recoupable waiver on the shelf is Schwab's SCHF and SCHE**, filed in N-CEN Item C.8
  every year since fiscal 2022 and absent from every document a shareholder reads.

Fees are 497K fee tables read on **2026-08-17**, from prospectuses dated: VTI, VOO, VEA,
BND 2026-04-28; VWO, VXUS, VEU, SCHB, SCHF 2026-02-27; SPTM, SPLG 2026-02-03; SPDW, SPEM
2026-01-30; ITOT, IVV 2026-07-31; AGG 2026-06-29; SCHE 2026-06-11; SCHZ 2026-04-28; IEFA,
IDEV, IXUS 2025-11-28; IEMG, EEM 2025-12-30; AVEM 2025-12-31; SPY 2026-01-26. **Vanguard's
seven fee tables carry no waiver, no expense-limitation and no acquired-fund-fee line at
all**; every iShares table states that what BFA pays "exclude[s] acquired fund fees and
expenses, if any".

**Three names on this page changed under it, and one alternate was in the wrong category.**
Morningstar acquired CRSP, so from **2026-07-29** Vanguard renamed the fund and its index:
VTI is now the **Vanguard Morningstar Total Stock Market ETF** tracking the **Morningstar US
Total Market Index**, and VBR is the **Vanguard Morningstar Small-Cap Value ETF** — "*Each
Fund's investment objective, strategies, and polices remain unchanged*", so this is a rename
and not a methodology change (Form 497, accession `0000036405-26-000386`). **SPLG now trades
as `SPYM`** after State Street's 2025-10-21 rebrand. And **SPTM is not a total-market fund**
— it tracks the S&P Composite 1500, so State Street has no counterpart to VTI at all.

**Six qualifying funds were not audited**, from a sweep of the SEC's 2026Q2 N-PORT data set:
IUSB, VONE, BBUS at **0.02%**, BBIN, VTHR, and **BKLC and BKAG at 0.00%** — BKAG tracking the
*same* Bloomberg US Aggregate as AGG, SCHZ and SPAB at no fee, which is the one that could
move the bond row. Their lending income and waiver terms were not read
([§6.7](structural-and-tax-edges.md#67-what-the-shelf-is-missing-and-one-fund-that-is-in-the-wrong-category)).
**Bid-ask spreads are published and deliberately not in the ranking**: VTI 0.55 bp, VOO
0.56, VXUS 1.18, VEA 1.41, VWO 1.70, BND 1.38, at 2026-08-14, with Schwab's four returning
HTTP 403. A spread is paid once and a fee for thirty years — and **SPY has the tightest
spread on the shelf, at zero, and the highest cost of ownership on it.**

### Use VEA + VWO rather than VXUS, and not only for the reason this page used to give

**The split is cheaper before any placement argument.** VXUS costs **0.05%** — not the
0.03% this repository had recorded — against a 75/25 blend of VEA and VWO at 0.0375%, so
splitting saves **1.25 bp/yr on the international sleeve, 0.50 bp of equity**, and lending
is a wash (VXUS 3.57 bp against the blend's 3.56). On net cost the split is **0.19 bp
against VXUS's 1.43**. The placement gain is separate and smaller than the framing implied:
**1.33 bp/yr of equity at 23.8%, 0.958 at 15%, and exactly zero** if the shelter holds the
whole equity sleeve or the qualified rate is 0%
([computed, not asserted](structural-and-tax-edges.md#1-foreign-tax-credit-forfeiture--the-result-that-changes-an-allocation)).

**So the conditional runs the other way.** A reader holding everything in one account gains
nothing from placement and still saves 0.50 bp/yr of equity by splitting. VXUS's case is
one fewer holding, one fewer spread crossing at purchase, and — the part that is not a
cost — **market weights this repository cannot otherwise supply**, since 75/25 is a
declared research weight and no global market-capitalisation series exists here. VXUS is
nonetheless the cheapest total-international fund on the shelf, at 1.43 bp against VEU's
1.61 and IXUS's 3.99.

### VTI against VOO is not a decision this evidence can make

`as of 2026-08-17`. Same sponsor, **same 0.03% fee**, zero capital-gain distributions in
every year filed, and each tracking its own index to within 4 bp over ten years. Their
tracking differences are **not comparable** — CRSP US Total Market against the S&P 500 —
and the only group on the shelf that shares an index is VOO, IVV and SPLG, which are
indistinguishable once compared.

**One contractual difference survives and it is securities lending: VTI 1.84 bp/yr against
VOO 0.06, a gap of 1.78 bp.** It replicates at both other sponsors that run the pair —
ITOT 1.96 against IVV 0.25, SCHB 1.04 against SPLG 0.18 — so it is a property of the
completion tail's borrow demand rather than of one manager. **And it is undetectable.** At
1.78 bp against any plausible tracking error between the two indices, the probability of
being ahead after thirty years is **0.52 to 0.54**, and 90% confidence arrives in about
five thousand years at 100 bp of tracking error. **Take the total-market fund on the
lending margin and stop arguing.** Whether the completion index earns more is a return
claim, and this repository has no instrument that can sign it — the same reason
[VB's and VTV's rejections](factor-products.md#the-comparator-shrinkage-and-two-traps) are
not return findings.

**And avoid SPY, which is the one large cost difference in this category.** 0.0945% against
0.02–0.03%, and its unit-investment-trust structure forbids the offset: it "is not
authorized to … lend its portfolio securities or other assets", credits dividends to "a
non-interest-bearing account" whose earnings accrue to the Trustee, pays them a month after
a quarterly ex-date, and provides **no dividend reinvestment service**. Net cost **9.45 bp
against SPLG's 1.82**.

### 1.3 The two optional sleeves, and nothing else

Both are second decisions, taken after the split, and both held **inside** the equity or
total allocation rather than added to it.

| Sleeve | Fund | ER | Size | Where | Verdict |
| --- | --- | ---: | --- | --- | --- |
| Small-cap value | **VBR** | 0.05% | 0–20% of US equity | treat as US equity in §3 | `exploratory` product, `exploratory` premium, **chain negative on the defensible reading**, and its marginal credit against an equity core is **−0.181 pp/yr per unit weight** |
| Managed futures | **DBMF** pro rata | 0.85% | **0–10% of total capital** | **tax-deferred only.** 2.09 pp/yr of drag, 143.9 bp of it incremental over the equity it is sold to buy | `exploratory` product, index `unresolved`. **DBMF is the pro-rata vehicle and gets the +2.44 pp/yr bar** |
| Managed futures | **RSST** as the overlay | 0.99% | **0–30% of *notional*, which is 0–30% of capital at `d ≈ 1.0`** | **either account.** 4.5 bp per dollar incremental in taxable ([§7.2](capital-efficiency-and-breadth.md)); place it wherever it does not force a realisation | Same status. **RSST is the overlay and gets a bar near zero.** Single-product risk has eased: the overlay shelf is four live funds and the listed managed-futures shelf is fifteen |

**The two rows are two different weights and must never be added or compared directly.**
DBMF's 10% is a share of *capital*, sold out of equity; RSST's 30% is a share of *notional*,
financed and selling nothing. Ten per cent of capital in DBMF buys 10% of trend notional at
the cost of 10% of the equity position; thirty per cent of capital in RSST buys 30% of trend
notional and **more** base equity than it displaced, because the wrapper delivers 107.2%
([capital efficiency §6a.2](capital-efficiency-and-breadth.md)).

Three sizing notes, because these weights are judgements before they are measurements.
**VBR's yield is higher than the market's, which raises its shelter priority above plain US
equity — by how much is not measured here.** **Experiment 004 priced a 15% trend sleeve, not
a 10% one**: the pro-rata cap is set below the tested weight because one product's loading
has been measured and there is no fallback, not because 10% was measured to be better. And
**the 30% overlay is not a growth optimum**: the growth optimum is 3.04 units of notional
and is refused, the drawdown ceiling that replaces it is about 0.55, and 30% is where an
investor holding appreciated taxable lots can get to without realising gain
([§7](capital-efficiency-and-breadth.md)). **A reader with no embedded gain may hold 0.50.
Nobody should hold the optimum.**

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
- **The tax gap between the two vehicles is 1.77 pp/yr gross and 1.39 pp/yr net of the
  equity each displaces, and it runs the other way from this page's framing.** RSST 0.32 pp/yr
  of distribution tax drag, DBMF 2.09, each from its own SEC-standardised after-tax table;
  subtract the 26.7 bp the plain equity fund pays anyway and the figures are **4.5 bp and
  143.9 bp per dollar held** ([§7.2](capital-efficiency-and-breadth.md)). The mechanism is
  that a tax-favoured equity sleeve shares RSST's capital, **not** that its trend sleeve is
  taxed better — RSBT and RSBY, whose base leg is bonds, distribute 100% ordinary income like
  DBMF.
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
| **VTI** (or ITOT) | equity risk premium at a **1.16 bp net cost** — 3 bp of fee less 1.84 bp of lending — and ~1.3 bp of round trip | **contractual** on the *cost*; risk premium on the *return* | It is the control. Every candidate was measured against it and none beat it. **VOO is the same fee and 1.78 bp less lending**, which is the whole measurable difference between them |
| **VEA** (or SPDW, IEFA) | developed ex-US equity at a **−0.30 bp net cost**: lending of 3.30 bp more than covers the 3 bp fee | same | Diversification of the equity claim, not an edge. Its foreign tax credit is worth 15.78 bp/yr **only in taxable**. SPDW is cheaper still at −1.63; IEFA is 4.65 |
| **VWO** (or IEMG) | emerging equity at a **1.67 bp net cost**; IEMG's is **−0.87** on a *higher* 9 bp fee | same | Same. Its credit is worth 20.00 bp/yr in taxable, and it is the sleeve §3's arithmetic moves |
| **BND** or Treasuries | term and credit compensation, and a risk brake, at a **3.00 bp net cost — the dearest bond fund audited**, because it is the only one that does not lend | **a different benchmark, not an edge** | Sized by risk capacity. **The brake works; its diversification does not, in every era** — the bond–stock beta was positive to 1999, negative to 2022Q3, positive again to 2024Q2, and negative on the 18 months since, on this repository's own data |
| **VBR** (optional) | HML loading **+0.410 `[+0.322, +0.480]`**, delivered and stable, at 5 bp, with a **negative** shortfall against a fitted four-fund combination | **risk premium**, `exploratory` on both terms | **Low confidence.** The chain is +0.09 to −0.39 pp/yr on the US premium and +0.28 to +0.76 on the pooled one. It is here because it is the only US value product that both delivers its exposure and does not lose to a cheap combination — **not because the chain is positive** |
| **DBMF** (optional) | loading **+0.671 `[+0.513, +0.829]`** on the AQR index, stable across the split and all 19 rolling windows, trailing a cost-free index by 0.48 pp/yr against an 0.85% fee | **risk premium**, `exploratory`; the index itself `unresolved` | **Nothing better has been measured**, which is not the same as nothing better existing: four of the five tested funds fail the 0.50 bar and **ten more listed funds have never been tested**. Crisis correlation −0.59 and payoff spread across four crises — but the post-publication interval includes zero and fails Holm |
| **RSST** (optional, in place of DBMF) | the same trend exposure as an **overlay** rather than pro rata, so the sleeve's hurdle falls by about 2.44 pp/yr; 0.99% all-in, no waiver, no recoupment; 0.32 pp/yr of distribution tax drag, **4.5 bp of it incremental over the equity fund inside it** | **risk premium**, `exploratory` on the product and `unresolved` on the index — **the wrapper changes the hurdle, not the evidence** | **Its loading on the benchmark has never been measured.** It is named because its structure is verified from N-PORT and its costs from filings, not because anything here says its trend leg delivers |
| **RSSB** | **rejected as a second overlay and as a replacement.** Global equity plus 100% Treasury notional at 0.39%, `delta` −0.0007 — the best-built wrapper on the shelf | — | **A bond overlay does not inherit trend's flat drawdown**: resampled, it is the deeper drawdown in **49.7%** of histories at 30% notional and **70.0%** at 100%, against trend's 6.9%. At matched 1.6× gross, **60% trend beats 30% trend plus 30% bonds by +1.40 pp/yr** and on Sharpe. Its base leg is *global* equity where the incumbent is US, so no single `delta` scores it ([§7a](capital-efficiency-and-breadth.md)) |
| **Cash reserve** | optionality and the ability not to sell | contractual | The framework requires it and **no experiment here sizes it** |

### What is deliberately absent

| Excluded | Reason |
| --- | --- |
| **MTUM**, and any momentum sleeve | Delivers its exposure (UMD +0.444) and is still `rejected`: a 1.22 pp/yr shortfall to a three-fund combination whose fee premium over it was 0.12. **It is no longer the entire retail momentum shelf** — that was a property of Experiment 002's census frame, and [Experiment 013](factor-products.md#the-us-shelf-on-the-corrected-frame) finds six, four of them `exploratory`. The sleeve stays excluded on the premium and turnover grounds, which are untouched |
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
| **Traditional 401(k)/IRA** | bonds first, then developed ex-US, then per the table. **DBMF here or not at all** | Bonds dominate by four to one. DBMF's 2.09 pp/yr distribution tax drag is zero here, and 143.9 bp of it is incremental over the equity it displaces. **A trend overlay held through RSST does not need this shelter at all** — 4.5 bp per dollar in taxable, so a 30% overlay forfeits **1.3 bp of portfolio return** by sitting outside a shelter, against the **43 bp** a 30% DBMF sleeve forfeits ([§7.2](capital-efficiency-and-breadth.md)) |
| **Roth** | the highest-expected-growth sleeve that fits after bonds | Identical to traditional on foreign withholding — both forfeit it. **The traditional-vs-Roth choice itself is a rate forecast, not a structure** |
| **Taxable** | US total market; emerging-market equity at 15% or 18.8%; **a trend overlay through RSST, if buying it in a sheltered account would mean realising gain to make room**; whatever does not fit above | ETFs, specific-ID lots as a standing instruction, no turnover. **The 1.3 bp the overlay costs here is 60 times smaller than the 84 bp/yr deferral hurdle that realising gain to relocate it would trigger** |
| **Physical gold, if held at all** | **taxable, and nowhere else** | A bullion trust distributes nothing, so it consumes no shelter and defers indefinitely; the capital-efficient wrapper GDE distributes **100% ordinary income at a measured 1.53 pp/yr** and cannot defer. **This page holds neither** ([§3a](capital-efficiency-and-breadth.md)) |

Three conditions that decide more than the ranking. **A tax-deferred balance is not the
investor's money** — at a 24% withdrawal rate $100,000 of traditional IRA is $76,000 of
investor wealth, so an allocation stated on nominal balances misstates true equity exposure.
**Below $300 of creditable foreign tax ($600 joint)** the credit is claimed without Form
1116 and without the §904 limitation, a threshold reached at about $190,153 of holdings and
never indexed. And **wash-sale scanning must be household-wide**: Rev. Rul. 2008-5 disallows
a loss where the replacement is bought in the taxpayer's IRA **and does not increase the
IRA's basis**, destroying the deduction rather than deferring it — 119 bp outright on a
5%-of-portfolio disallowance.

**One of the two omissions that cut against the emerging inversion is now measured at
zero.** A shelter also shelters capital-gain distributions — and **every emerging ETF on
the audited shelf distributed 0.00 of realised gain in each of five fiscal years**, as did
every other fund on it
([structural and tax-aware edges §6.3](structural-and-tax-edges.md#63-capital-gain-distributions-zero-everywhere-including-the-unit-trust)).
What remains unquantified is that a taxable international position is a better
loss-harvesting candidate, which could still close a 6 bp gap.

**And the input the whole table rests on is probably understated, in the direction that
widens the inversion.** Eleven funds from five sponsors file foreign taxes paid over
foreign source income at **9.12–14.23% for emerging** against the **9.853%** used here;
at VWO's own filed 12.59% the break-even rises from 21.51% to **27.48%**, and on the
conservative reading of the filings' denominator to 24.40% — **above 23.8% either way**,
so the "treat it as a tie" row above would become a third inversion. The input is not
changed until the denominator is reconciled to Form 1099-DIV Box 1a
([§1](structural-and-tax-edges.md#the-withholding-rate-is-the-input-this-whole-section-rests-on-and-five-funds-disagree-with-it));
**no holding on this page moves on either reading.**

### 3.1 The queue, with the sleeves in it, at one worked bracket

The table above is federal-only and covers the plain sleeves. The wrappers belong in the
same queue, and putting them there is what shows that **sorting the shelter by tax drag
alone fills it with the sleeve that contributes least.** Worked for a California investor at
**24%/15% federal with no §1411 surtax and 9.3% state on every line** — 33.3% ordinary and
24.3% qualified/long-term, the machinery and the restatement in
[capital efficiency §7.2](capital-efficiency-and-breadth.md):

| Rank | Asset | Priority per sheltered dollar | Its measured marginal contribution |
| ---: | --- | ---: | --- |
| 1 | **DBMF**, pro-rata trend | **170.6 bp** | +2.44 pp/yr of hurdle it must clear first, and it does not |
| 2 | **Taxable IG bonds** | **154.8 bp** | risk control, not a return claim |
| 3 | **GDE**, equity + gold | 130.9 bp | **+0.09 pp/yr against an MDE₈₀ of 1.68 — unmeasurable** |
| 4 | **RSSB**, global equity + bonds | ~70 bp | rejected; a bond overlay deepens the drawdown in 70% of resampled histories at its own notional |
| 5 | Developed ex-US equity | 47.4 bp | the control |
| 6 | **RSST**, equity + trend | **31.2 bp**, of which **4.5 bp is incremental** over the equity fund inside it | **+1.50 pp/yr** at 30% notional, leverage-matched, MDE₈₀ 1.11 |
| 7 | Emerging-market equity | 29.3 bp | the control |
| 8 | US equity (VTI) | 26.7 bp | the control |
| 9 | **GLDM**, physical gold | **~0 bp** — a bullion trust distributes nothing | needs no shelter at any weight |

**Read rows 1, 3 and 6 together.** The naive rule — shelter the highest drag — puts DBMF and
GDE at the front and RSST near the back, and it is exactly backwards: **RSST is the only one
of the three with a marginal contribution that clears its own detection floor, and it is the
one that needs the shelter least.** Priority ranks what a sheltered dollar *saves*; it says
nothing about whether the asset should be held at all, and **a queue is only ever run over
sleeves already decided on other grounds.**

**The operative constraint for the stated investor is not capacity but fungibility.** A
menu-constrained 401(k) can hold the top of this queue (bonds, broad index) and none of the
wrappers; a taxable account carrying unrealised gain can hold anything but cannot be
*converted* into anything; so the IRA and Roth are the only accounts that can take an
arbitrary ETF at zero cost. **That is what caps an overlay, and it caps it in units of
capital rather than of tax.**

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
| **Managed futures** | **Keep. The account rule applies to DBMF and does not apply to RSST** | **Only DBMF's loading has been measured against the benchmark**, on three independent measurements, and the other fourteen listed funds are untested rather than rejected. DBMF's tax drag is 2.09 pp/yr — 2.5× its own fee, zero in a shelter, and 143.9 bp of it incremental over the equity it is sold to buy; **RSST's incremental drag is 4.5 bp and its account does not decide its sign.** RSST is also the vehicle that keeps the funding-rule benefit. **25% of capital is far too large for DBMF and is inside the range for RSST notional**, which is the distinction §1.3 insists on |

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
| Post-publication, **taxable through DBMF** (less `0.15 × 1.439`) | **+37 bp** | 251 bp | 0.790 | 76 yr |
| Post-publication, **taxable through RSST** (less `0.15 × 0.045`) | **+58 bp** | 251 bp | **0.897** | **31 yr** |
| Full-period, tax-deferred | +88 bp | 251 bp | 0.973 | 13 yr |

**The two taxable rows are charged on the *incremental* drag over the equity each sleeve
displaces, and they used to be charged on the gross drag.** `0.15 × 2.09` and `0.15 × 0.32`
gave +28 and +54 bp; both overstated the cost, because a sleeve sold out of a taxable equity
position removes 26.7 bp of that position's own distribution tax as it goes
([capital efficiency §7.2](capital-efficiency-and-breadth.md)).

**The account was the largest controllable term, the wrapper has displaced it, and on the
corrected arithmetic the account is barely a term at all.** Choosing the shelter over taxable
is worth **21.6 bp/yr** through DBMF and **0.7 bp/yr** through RSST — the second number is
the whole finding, and it is 60 times smaller than the deferral hurdle a reader would trigger
by selling appreciated lots to make shelter room. Choosing RSST over DBMF is worth **21 bp/yr
in taxable and nothing at all in a shelter**, and it also removes the 2.44 pp/yr funding-rule
hurdle that no account does anything about. **The wrapper decision comes first because it
changes which bar the sleeve is judged against; the account decision now comes last.**

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
| **A taxable account with no embedded gain, or contributions large enough to build one** | Lifts the constraint that caps the overlay at 30% of notional. The next constraint is the resampled drawdown at about **0.55**, not the growth optimum at 3.04 ([capital efficiency §7](capital-efficiency-and-breadth.md)) |
| **RSST's next after-tax table, covering a flat-equity year** | Its 0.32 pp/yr drag comes from a 28-month window in which a growing ETF deferred realisation and a tax-favoured equity sleeve shared the capital. **A year in which the equity leg makes no long-term gain while the Cayman subsidiary makes ordinary income is the one that would move it** — and that is the year the sleeve exists for |

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
- **Not net of everything, though the core four are now closer.** Their fee, securities
  lending, realised capital-gain distributions and waiver terms are all read from filings
  ([structural and tax-aware edges §6](structural-and-tax-edges.md#6-the-core-beta-shelf-audited-on-cost-rather-than-on-fee)).
  **Bid-ask and brokerage are still absent**, and deliberately weighted as one-time costs at
  purchase rather than recurring ones: a spread is paid once and a 3 bp fee is paid for
  thirty years. For the *factor and wrapper* audits, realised distributions and turnover
  remain absent entirely.
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

**Three of those have been promoted from "would refine the answer" to "set it".** The
annual contribution rate, the embedded gain in each taxable lot, and **whether the 401(k)
menu can hold anything but a broad index** now jointly decide the overlay weight, because
the constraint that used to decide it — tax-shelter capacity — is withdrawn
([capital efficiency §7.3](capital-efficiency-and-breadth.md)). None of the three was ever
asked for by any page here, and without them **an overlay weight is a guess about an account
rather than a judgement about a strategy.**

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
holdings, 497K fee tables, N-CSR tax-character tables and N-CEN recoupment flags. **Every
core-fund cost figure in §1.2 and §2** traces to
[structural and tax-aware edges §6](structural-and-tax-edges.md#6-the-core-beta-shelf-audited-on-cost-rather-than-on-fee),
regenerated by `studies/core_beta_shelf.py` from 110 hashed N-CEN filings and pinned in
`tests/unit/test_studies_core_beta_shelf.py`.

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
7. **§3.1's worked bracket is one investor and its 401(k) menu is assumed, not verified.**
   California at 24%/15% federal with no §1411 surtax and 9.3% state; a menu-constrained
   401(k) able to hold a broad index and nothing exotic; a taxable account whose embedded
   gain will not be realised. **A reader in a state with a preferential capital-gains rate,
   or with a brokerage-window 401(k), gets a different queue and possibly a different
   weight.** DBMF's distribution composition is `not found` and is bounded as 100%
   non-qualified ordinary, which makes its restated 170.6 bp an upper bound.

**Open.** Which benchmark a factor line may book its capture against — the answer moves the
line by a factor of two and a half. What a real fund's delivered capture is; every figure
here is from research portfolios, and measuring a fund's own **needs holdings rather than
returns**. Whether the emerging inversion survives harvesting value — **it survives
capital-gain distributions, which are now measured at zero for every fund on the shelf.**
**What the true effective foreign withholding rate is**: eleven funds file 9.12–14.23% for
emerging against the 9.853% §3 uses, and reconciling the filings' "foreign source income"
to Form 1099-DIV Box 1a would settle whether the inversion covers 23.8% too. **Whether BKAG,
a zero-fee tracker of the same Bloomberg US Aggregate as three audited funds, beats BND** —
its lending income and waiver terms were not read. **And Schwab's four funds' spreads**,
behind a site-wide HTTP 403. What a liquidity reserve should be, unsized. **What any of the ten untested listed
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
4. **Five review triggers**: the fund-structure line (94 SEC orders, and 89 Form 497K
   documents now naming an "ETF Class" against 2 before the first order, but only nine funds
   actually listed — **and Schwab, BlackRock, JPMorgan and Fidelity's index range hold
   orders and have filed nothing**); every fund-specific
   fact in §1.2, whose fee tables and lending figures are dated 2026-08-17 and whose waiver
   expiries run **2026-10-31 (State Street), 2027-01-31 (State Street ex-US), 2026-11-30
   (IXUS), 2027-02-01 (SPY), 2027-06-30 (AGG) and 2030-12-31 (IEMG)**; **fund and index
   renamings** — SPLG now trades as `SPYM`, and Morningstar's acquisition of CRSP renamed
   VTI and VBR and their target indices on 2026-07-29; **JPFP's commencement**, which would reorder the
   wrapper cost ranking at 0.59% against RSST's 0.99%; and **KMLM's shareholder vote around
   2026-11-20**, the fund having operated under interim advisory agreements since a change of
   control on 2026-06-23.
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
8. **A tax drag is compared with the fund it displaces, at the holder's own rates, or it is
   not quoted.** Both halves cost this page a wrong conclusion: the wrapper's 0.32 pp/yr is
   4.5 bp once the equity fund inside it is subtracted, and California's flat treatment of
   capital gain almost exactly cancels a lower federal bracket rather than compounding it
   ([capital efficiency §7.2](capital-efficiency-and-breadth.md)).
9. **A weight is stated in its own units and never compared across funding rules.** DBMF's
   0–10% is capital; RSST's 0–30% is notional; adding or comparing them is the error §1.3
   exists to prevent. **And an account cap is not a risk limit**: this page capped the
   overlay at what a shelter could carry and called it sizing, when the quantity that
   actually limits it is the resampled drawdown.
10. **A fund's cost is `fee − securities lending`, and the two rankings are different
    rankings.** [Experiment 009](factor-products.md) proved that on the funds holding
    little of the money and it was never applied to the four holding all of it; it is now,
    and it moves IEMG below VWO on a 50% higher fee and BND to the bottom of the bond
    shelf. **A page naming a fund states both terms, marks the first contractual and the
    second measured, and never ranks two funds on a tracking difference taken against two
    different indices** — only VOO, IVV and SPLG share one.
11. **The recommendation survived its own doctrine, and the margin is the result.**
    0.60 bp/yr between the recommended four and the cheapest combination on the shelf,
    against an 84 bp turnover hurdle. **Fund selection is the smallest decision on this
    page**, and any future effort spent on it should be spent on §1.1 instead.
