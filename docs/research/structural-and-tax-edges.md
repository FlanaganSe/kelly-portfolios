# Structural and tax-aware edges: what else is contractual, and how big is it

**Question.** The [edge decomposition](expected-edge-decomposition.md) prices a
contractual edge of about 89 bp/yr against the investor's own plausible alternative.
What else belongs in that class, how large is it, and does it double-count what is
already booked?

**Decision it informs.** Whether the contractual budget should be revised, and which
account a real investor's international sleeve belongs in.

**Scope.** US federal individual investor, `as of 2026-08-12`. State income tax is
excluded and additive wherever it exists. **This is not personalised advice** — it is a
sizing exercise for a class of edge, and every figure is a function of stated inputs a
different investor should restate. Non-US investors differ on every line.

Everything numerical regenerates from
[`studies/tax_structure.py`](../../research/src/portfolio_edge/studies/tax_structure.py)
and is pinned in `research/tests/unit/test_studies_tax_structure.py`. No market data, no
randomness, no forecast.

---

## Conclusion

1. **The contractual class is bigger than the budget records, by about 20 bp.** One
   genuinely additive line dominates — the capital-gain distributions an active mutual
   fund makes and an ETF does not, **+23 bp**. Lot-selection discipline adds **+5 bp**.
   Two corrections run the other way: the foreign tax credit forfeited inside a shelter
   (**−3.4 bp**) and the direct-indexing fee the harvesting line never subtracted
   (**−4.4 bp**). Net, the own-counterfactual budget moves from **89 to about 109 bp/yr**.
   The shape does not change; the magnitude improves by roughly a fifth.
2. **The largest number here is not a saving — it is a hurdle.** Deferral of unrealised
   gain is worth **84 bp/yr** at thirty years and the §1014 step-up a further 78,
   summing to a **horizon-free 162 bp/yr**. It is deliberately **not booked**, because
   crediting yourself for not doing something nobody proposed is how these budgets get
   inflated. It is the price of turnover in a taxable account.
3. **The foreign tax credit inverts standard asset-location advice for exactly one
   sleeve, at exactly two brackets.** The break-even qualified-dividend rate is 10.5% for
   developed markets — below every positive US rate — but **21.5% for emerging markets**,
   which falls *between* the 18.8% and 23.8% brackets. **A US investor at 15% or 18.8%
   should hold emerging-market equity in the taxable account and US equity in the
   shelter.**
4. **Capital efficiency is the most substantive structural candidate and the only one
   whose sign this repository cannot check.** A 90/60 return-stacked fund needs
   **92 bp/yr** of Treasury excess return over cash before its overlay contributes
   anything, against a futures funding basis this page **previously mis-benchmarked at
   58.70 bp/yr and now puts at 12–33 bp**, which roughly halves the hurdle. Both inputs are
   forecasts, so it is probabilistic by construction.
5. **The largest additive line is decaying while being measured.** 94 SEC orders let
   mutual funds add ETF share classes. **Recheck before any decision leans on the 23 bp.**

**One caution on the whole page.** Every figure is sized for **one stated reference
investor** — US top bracket, 30-year horizon, liquidation at the end; 60% US equity, 14%
developed ex-US, 6% emerging, 20% taxable bonds; 40% of the portfolio in tax-advantaged
capacity. Quoting a per-sleeve number as a portfolio number is the commonest way a tax
figure is inflated, and every lever here has a different base.

---

## 1. Foreign tax credit forfeiture — the result that changes an allocation

**Mechanism, a statutory chain rather than a published rule.** A foreign government
withholds at source; a US fund pays it and under
[§853](https://www.law.cornell.edu/uscode/text/26/853) may elect to pass it through, so
the shareholder *"include[s] in gross income"* their share and credits it under
[§901(a)](https://www.law.cornell.edu/uscode/text/26/901), subject to the
[§904(a)](https://www.law.cornell.edu/uscode/text/26/904) limitation. An IRA is *"exempt
from taxation under this subtitle"*
([§408(e)(1)](https://www.law.cornell.edu/uscode/text/26/408)): no tax to credit against,
no gross income to include the pass-through in, a §904 numerator of zero. **The
withholding is paid and permanently lost, identically in a traditional account and a
Roth.** No IRS publication states this — Publication 514 and the Form 1116 instructions
do not mention IRAs — so assert it from the statute, not from commentary.

The treaty route does not rescue it. Both the US–Japan and US–UK conventions exempt a
resident *pension fund*, then disapply the exemption for *"a pooled investment vehicle"*
and for RIC dividends. The beneficial owner of the shares in VEA is the fund, not the
IRA.

**Size, from fund filings.** Vanguard's 2025 foreign tax credit worksheet gives foreign
tax as a percentage of ordinary dividends — VEA 6.46%, VXUS 7.11%, VWO 10.93% — which on
the grossed-up Box 1a basis is 6.068% and 9.853%. Against MSCI index dividend yields at
2026-07-31:

| Sleeve | Gross yield | Effective withholding | **Forfeited inside any shelter** |
| --- | ---: | ---: | ---: |
| Developed ex-US equity | 2.60% | 6.07% | **15.78 bp/yr** |
| Emerging-market equity | 2.03% | 9.85% | **20.00 bp/yr** |
| Same, at 30% of a total-equity portfolio | | | **5.11 bp/yr** |

Emerging markets forfeits *more* while yielding *less*, because its withholding rate is
62% higher. **The two sleeves cannot be treated as one "international" line.** iShares'
2025 tax supplement cross-validates the method from a different sponsor on a per-share
basis.

**The decision this settles is not the one usually stated.** The conventional advice —
"hold international in taxable to capture the credit" — compares the wrong pair. The
right metric for scarce shelter capacity is what a sheltered dollar *saves*:

```
priority = (recurring tax if held in taxable) − (irrecoverable withholding if sheltered)
```

For every asset except a foreign one the second term is zero and this collapses to the
familiar rule. At the top bracket, with BND's SEC 30-day yield of 4.65% and a US equity
yield of 1.10%:

| Asset | Taxable cost | Sheltered cost | **23.8%** | **18.8%** | **15%** |
| --- | --- | ---: | ---: | ---: | ---: |
| Taxable investment-grade bonds | yield × 40.8% | 0 | **189.7** | 189.7 | 189.7 |
| Developed ex-US equity | 2.60% × q | 15.78 | **46.1** | **33.1** | **23.2** |
| Emerging-market equity | 2.03% × q | 20.00 | **28.3** | 18.2 | 10.45 |
| US equity | 1.10% × q | 0 | 26.2 | **20.7** | **16.50** |

The break-even is closed form, `q* = u w y_i / (y_i − y_d)`: **10.52% developed, 21.51%
emerging**. The US schedule offers 0%, 15%, 18.8% and 23.8%, so the developed break-even
falls below every positive rate and the emerging one falls *between* two live rates.
**That is a fact about the bracket schedule, not about the funds.**

- **At 23.8% the ranking survives but the margin does not** — emerging's advantage over
  US equity falls from 22.1 bp to **2.1 bp**. Treat it as a tie.
- **At 15% or 18.8% the ranking inverts.** Emerging drops to 10.45 bp of priority against
  US equity's 16.50.
- **Bonds dominate by a factor of four at every rate**, so the uncontested half of the
  conventional rule is uncontested here too. Note the 189.7 uses the top ordinary rate
  and must be restated with the investor's own — at 22% it is about 102 bp, and still
  dominates.
- **The 0% bracket is the trap.** §904 limits the credit to US tax on foreign-source
  income, and there is none. Such an investor forfeits the withholding in *both*
  locations.

**Two limits.** Below **$300 of creditable foreign tax ($600 joint)** the credit is
claimed without Form 1116 and without the §904 limitation — a threshold reached at about
$190,153 of developed-market holdings, and neither figure is indexed. And two omissions
cut against the emerging inversion, neither quantified: a shelter also shelters
capital-gain distributions and rebalancing turnover, which emerging funds generate more
of; and a taxable international position is a better loss-harvesting candidate.

**Double count: not additive.** This is a **correction** to the 10 bp location line,
whose sources do not model foreign withholding at all. Booking it as a new positive line
would be the same dollars with the sign reversed.

---

## 2. Fund structure — the one large additive line

**Mechanism, one sentence of statute.**
[§852(b)(6)](https://www.law.cornell.edu/uscode/text/26/852) disapplies §311(b) for a
redemption in kind, so an ETF hands appreciated shares to an authorised participant and
recognises nothing, while an equivalent mutual fund sells, recognises, and must
distribute. [SEC Rule 6c-11](https://www.sec.gov/rules/final/2019/33-10695.pdf) turned
that shield into a tool by permitting **custom baskets** under written policies — its own
footnote 281 is explicit: *"In-kind redemptions allow ETFs to avoid taxable events."*

**Size, from N-CSR Financial Highlights**, capital-gain distributions as a percentage of
beginning NAV over ten years: **VOO, VFIAX, VTI, VTSAX all 0.00%** in all 44 fund-years;
**AGTHX 6.62%** (distributed in FY2022 while returning −23.78%); **FCNTX 7.01%**.
Frequency, from Morningstar's annual survey: *"Only 7% of ETFs paid a capital gain in
2025, compared with 52% of mutual funds"*.

**The tax cost of a distribution is far below its headline tax**, because the distribution
raises basis. At the top rate, 7% growth, 30 years, liquidating at the end: a 3%-of-NAV
distribution costs **38.3 bp/yr**, not its 71.4 bp headline. Quoting the headline
overstates it roughly twofold.

**Booked at 23 bp**: 38.3 bp on the taxable equity sleeve at a 3% counterfactual
distribution, times the 60% that sleeve occupies. Range 0 to 49 bp.

**The correction that must not be dropped.** Poterba and Shoven (2002) found the SPDR
trust and a low-turnover index mutual fund *"very similar"* before and after tax over
1994–2000, and the peer-reviewed measurement isolates the wrapper at **ETFs 0.39%,
Vanguard index funds 0.41%, non-Vanguard index funds 1.07%**. **The ETF advantage is
against *active* funds and *non-Vanguard index* funds, not against a low-turnover index
mutual fund** — which matters most here, since the control is a cheap broad index fund
either way.

**Double count: ADDITIVE.** The 49 bp fee line is an expense-ratio gap containing no tax,
and this is the *fund* realising gains rather than the *investor* realising losses.

**Falsifier, already firing.** The SEC granted its first ETF-share-class order on
2025-11-17 and its listing shows **94 granted orders as of 2026-08-11**, covering roughly
ninety fund families, with only two applications still noticed and unordered. Vanguard is
the proof of concept: VFIAX and VTSAX show zero capital gains for a decade precisely
because they share a portfolio with VOO and VTI. **So the 23 bp is a decaying quantity
with a visible mechanism of decay.** The opposite risk also exists — a 2021 Senate Finance
discussion draft proposed to repeal the RIC exception outright; never enacted, no
successor found.

---

## 3. Section 1256, and capital efficiency handled honestly

**§1256** marks a regulated futures contract to market at year end and splits the gain
60/40 long/short-term regardless of holding period, blending to 30.6% at 2026 top rates.
Against ordinary annual treatment it saves **51 bp/yr on a 5% return**; against a deferred
long-only equity holding it is **−31 bp/yr**, because the rate is higher *and*
mark-to-market destroys the deferral §4 prices. Which is the counterfactual decides the
sign, and nothing about the statute settles it.

**And the 60/40 split did not reach shareholders of any fund checked.** From N-CSR
tax-character tables: **DBMF distributed 100% ordinary income in 2024 and 2025; KMLM 100%
in FY2026; CTA 100% in FY2025; NTSX reports a single "Ordinary Income" column.** Three
mechanisms stack: a Cayman subsidiary converts commodity gains to ordinary income
**asymmetrically** (DBMF's prospectus: *"any annual net loss of the Subsidiary will not be
recognized and will not carry forward"*), forced by §851(b)(2); capital-loss
carryforwards absorb the long-term half; and §1256(f)(2) cannot rescue income that is
ordinary by another route. **NTSX is the structural exception** — Treasury futures
generate qualifying income directly, so it needs no blocker.

**Capital efficiency: the mechanism, the cost, and why it is not booked.** A
"return-stacked" fund at 90% equity plus 60% Treasury-futures notional obtains 150% of
exposure per dollar. WisdomTree's NTSX is the reference case at 0.20% total expenses. The
arithmetic of whether it helps is entirely in one expression:

```
net contribution = bond notional × (bond excess return over cash − implied financing spread) − fee
```

**The financing spread was measured here against the wrong benchmark, and the correction
roughly halves the hurdle.** `as of 2026-08-16`.

This page previously read: *Fleckenstein and Longstaff, on 6,943 daily observations of CME
5-year Treasury note futures 1991–2018, "the average funding basis is 58.70 basis points"
— positive in all 28 years, so a 90/60 fund needs 92.0 bp/yr of Treasury excess return
before the overlay contributes.* **The 58.70 bp is real and it is not the number a fund
pays.** Fleckenstein and Longstaff define the funding basis against the **term bilateral
*special-collateral* repo rate on on-the-run 5-year notes**, and say why at p. 5062:
*"5-year Treasury notes often can be financed at special repo rates that are substantially
below general collateral repo rates."* That is a dealer's spread over its own cheapest
specific funding. **A fund posting T-bill collateral never faces that rate.** Their own
NBER working-paper draft published **81 bp** for the same quantity, so the figure moved
22 bp between drafts and should never have carried two decimal places here.

Against the benchmarks a fund actually finances at:

| Overlay | Benchmark | Spread |
| --- | --- | ---: |
| US Treasury futures | maturity-matched OIS | **12–18 bp** (Siriwardane, Sunderam and Wallen; 2y/5y/10y/20y/30y = 13/12/18/17/11, Jan 2010–Feb 2020) |
| US Treasury futures | T-bills | 21–33 bp (Barth and Kahn, OFR WP 21-01, 2015–20) |
| Gold futures | Treasury curve | ≤40 bp, and an **upper bound** — the identical 40 bp appears in SPX option boxes over the same window, so it is the Treasury convenience yield rather than anything gold-specific |
| Equity index futures | 3-month Term SOFR | **+62 bp**, ten rolls Dec-2022→Mar-2025. A genuine post-2022 regime change |
| **Diversified long/short trend book** | local interbank | **signed mean ≈ 0** |

**The NTSX hurdle, re-based:**

| Financing input | 90/60 break-even |
| --- | ---: |
| 58.70 bp, as this page previously stated | 92.0 bp/yr |
| **15 bp (OIS, the right benchmark)** | **48.3 bp/yr** |
| 33 bp (against bills) | 66.3 bp/yr |

**The last row of the spread table is the one that matters for a trend overlay, and it is
a sign question rather than a size question.** Hazelkorn, Moskowitz and Vasudevan
(*Journal of Finance* 78(1), 2023) measure the *signed* basis across 18 equity index
futures at **−0.83 bp on average, 2000–2017** — −8.15 before 2007, +3.52 after — against a
mean *absolute* basis of 52–64 bp. Their mechanism is that *"the basis tends to be positive
when dealers face long futures demand… and negative when dealers face short futures
demand"*, and Russell 2000 runs **−76 bp**, meaning a long position is *paid*. **A trend
book takes both sides by construction, so a systematic per-contract financing drag is not
supported.** The trap to pin: Siriwardane et al.'s widely quoted 42 bp for SPX is a **mean
absolute deviation** — they say *"we work with absolute values of spreads since the sign…
depends on whether arbitrageurs are net long or short"* — and it must never be applied as
a drag.

**Both inputs are forecasts**, which is why nothing here enters a contractual budget.
And the evidence that the whole advantage lives in the financing assumption is
quantitative, from both sides. The pro-risk-parity study's **own Appendix B** shows the
advantage over the market falling from 4.15% (t = 2.95) financing at T-bills to 1.81%
(t = 1.29) at LIBOR's 62.3 bp spread; its one-sentence defence is *"leverage can be
achieved by using futures contracts at an implicit cost that is lower than LIBOR"*.
**This page used to answer that the measured 58.70 bp is almost exactly the LIBOR spread.
That answer was wrong in kind** — Fleckenstein and Longstaff measure against special repo,
not LIBOR — **and at the 12–18 bp OIS benchmark the defence is largely correct.** What
survives of the critique is that the advantage is still sensitive to the financing
assumption, not that a 60 bp spread is the right one. The independent critique
reaches the same place: levered risk parity beats 60/40 by *"210 basis points… (P = 0.03)"*
at the risk-free rate and by *"only 29 basis points… (P = 0.40)"* once borrowing costs are
priced. **A ~60 bp financing spread removes 86% of the claimed edge over eighty-five
years of data.**

**NTSX's own record does not settle it either way.** Since inception it returned
11.38%/yr against 8.81% for 60/40 and 13.35% for the S&P 500 alone. The 60/40 comparison
is **not risk-matched**, and outperforming a lower-risk portfolio in an equity bull market
is precisely the trap
[decision 0003](../decisions/0003-cheap-broad-market-control.md) exists to catch. It had
no capital-gains distributions in any year 2022–2026, which is a real and separate point
in the structure's favour.

**What [decision 0004](../decisions/0004-no-sleeve-promoted.md) forbids, precisely.** It
forbids **levering an edge**. Capital efficiency is not that — it is obtaining a
*diversifying exposure* per dollar. But the edge decomposition closes the gap from the
other side: the term premium is excluded *"by construction"* because booking it as an
edge over an equity index is a benchmark switch. **So the 60% Treasury overlay is not an
edge under this repository's own rules even if the term premium is positive.**

**Four measurable conditions would justify revisiting:** a measured implied financing
spread on the specific contracts a candidate rolls, from contract-level data; a term
premium signed under the framework's protocol; a defined investor policy; and a modelled
margin and forced-liquidation path. Until all four exist, capital efficiency is reported
and not booked.

---

## 4. Deferred unrealised gain — the largest number here

An unrealised gain is an interest-free loan from the government whose principal compounds
with the position. [§1014](https://www.law.cornell.edu/uscode/text/26/1014) resets basis
at death, forgiving it outright.

At 7% pre-tax log growth and top rates, in bp/yr of annualised log growth:

| Horizon | Deferral | Step-up | Total |
| --- | ---: | ---: | ---: |
| 10 yr | 34.6 | 127.6 | **162.2** |
| **30 yr** | **84.1** | 78.1 | **162.2** |
| 40 yr | 99.0 | 63.3 | **162.2** |

**The total is horizon-free at 162.21 bp/yr**, because it is exactly
`g − log(e**g (1 − q) + q)`, which contains no `H`. The horizon only decides the split.

**At thirty years the deferral component alone is 84 bp/yr — 95% of the entire 89 bp
budget.** A strategy that fully turns over a taxable portfolio must out-earn that before
its fee and its spread.

Two limits. It is an upper bound, but the function is **sharply concave, not
proportional**: realising 10% of standing gain a year already costs 41.5 bp of the 84.1,
so **"low turnover" is not a defence**. And it vanishes entirely in the 0% long-term
bracket and in every sheltered account.

**Double count: not additive.** It is a **hurdle**, not a saving.

---

## 5. Direct indexing against the 30 bp already booked

The 30 bp harvesting line **already assumes direct security ownership** — the paper it
comes from states that funds cannot pass through security-level losses. Direct indexing
is not an addition to it; it is the *precondition*. So the question is whether the 30 bp
survives the fee charged to obtain it, and the budget states it gross of that fee.

The decay profile, from AQR's Sosner, Gromis and Krasner — whose conflict of interest runs
the useful way, since AQR sells strategies that *compete* with direct indexing. Annual
active tax benefit in bp, wash-sale rule **not modelled** so every figure is an upper
bound:

| Year | No flow, LT gains only | 1%/month contributions |
| ---: | ---: | ---: |
| 1 | 155.3 | 164.3 |
| 2 | 50.8 | 64.7 |
| 10+ | **−4.3** | 27.4 |

The mechanism is ossification, and it is self-inflicted: *"tax lots that are at a loss are
being systematically sold while tax lots that are at a gain are being systematically
retained."* Averaged over a holding period — which is what "bp/yr" means:

| Horizon | No flow, LT only | With contributions |
| ---: | ---: | ---: |
| **30 yr** | **5.6** | **34.6** |
| 30 yr, net of a 9 bp fee | **−3.4** | **25.6** |
| 30 yr, net of a 40 bp fee | −34.4 | **−5.4** |

**Three readings.** The 30 bp is well calibrated to the *contributing* investor. For a
**static** investor with only long-term gains the honest figure is **5.6 bp**, negative at
any fee. And **at a 40 bp fee no scenario measured is positive over thirty years.**
Published fees as of mid-2026: Wealthfront 9 bp, Frec 9, Altruist 12, Vanguard 20
(sub-advisory, $250k), Schwab 40, Fidelity 40. **The 40 bp tier is negative expected value
in steady state.** Vendor headlines quote year one, the largest number any profile takes.

**Two conditions decide the whole line and both are usually assumed.**
[§1211(b)](https://www.law.cornell.edu/uscode/text/26/1211) caps the deduction of net
capital loss against ordinary income at **$3,000 a year**, unchanged since 1978 and never
indexed: on a $1m portfolio harvesting 5%, the benefit is **119 bp with offsetting
realised gains and 12.2 bp without them**, and the cap's basis-point value falls with
portfolio size — 122 bp of $100,000 and **1.2 bp of $10m**. Every vendor figure assumes
offsetting gains; Vanguard's own research puts loss-offsetting income at 2–9% of taxable
equity. And harvesting is a *deferral*: the sheltered gain reappears in the replacement
lot's lower basis.

**One avoidance whose cost is permanent rather than timing.** An ordinary wash sale under
§1091 merely defers the loss, because §1091(d) adds it to the replacement shares' basis.
**Revenue Ruling 2008-5 removes that repair when the replacement is bought inside the
taxpayer's IRA** — the loss is disallowed and the IRA's basis is *not* increased, so the
deduction is destroyed. 119 bp outright on a 5%-of-portfolio disallowance at the top rate.
**Wash-sale scanning must be household-wide**, because a same-account check converts a
deferred loss into a destroyed one.

**Double count: a small downward revision.** Netting a 9 bp fee at a 30-year horizon moves
the line to **25.6 bp** for a contributing investor, **−4.4 bp**.

---

## 6. Securities lending, verified by asset class

Net lending income over average net assets, from N-CSR Statements of Operations for
fiscal years ending 2025. Dollar figures are read directly; the denominator is inferred
two ways, which is why several are ranges.

| Fund | bp/yr | | Fund | bp/yr |
| --- | ---: | --- | --- | ---: |
| IEFA | 1.08–1.11 | | IEMG | ~9.2–9.7 |
| VEA | ~2.97 | | VSS | ~13.0–13.4 |
| VB (US small-cap) | ~3.0–3.1 | | VWO | ~4.9–5.2 |
| VXUS | ~3.4–3.6 | | | |

Three findings, none of which changes the budget materially. **The 1 bp booked is right
for a US total-market fund and low for an international one** — a portfolio 20%
international earns about 1.5 bp, a +0.5 bp correction. **It is not a size effect**: VB,
pure US small-cap, earns the same as VEA, large-cap developed international. The premium
is in *international and emerging* lending demand, which corrects the edge decomposition's
framing of the VOO/VTI gap as "the small- and mid-cap tail". And **the sponsor matters
more than the asset class** — IEFA at ~1.1 bp and VEA at ~3.0 bp hold nearly the same
universe.

---

## 7. Smaller levers, sized so they can be dismissed with a number

**Account type is mostly a forecast, not a structure.** Traditional and Roth are
algebraically identical whenever the contribution and withdrawal rates are equal, so the
entire difference is the rate change — a saver falling from 32% to 22% gains exactly
14.71% of terminal wealth. **Predicting your own marginal rate thirty years out is a
forecast**, so this is probabilistic and does not belong in a contractual budget. What *is*
structural, from the same algebra: **a tax-deferred balance is not the investor's money**
— at a 24% withdrawal rate, $100,000 of traditional IRA is $76,000 of investor wealth, so
an allocation stated on nominal balances misstates true equity exposure. §1's ranking is
per dollar of *capacity* precisely to sidestep that.

**The HSA is the one genuine structural exception** — the only US account untaxed at all
three points, with payroll contributions escaping FICA. Not booked, because its value is a
**dollar amount bounded by a contribution limit** ($4,400 self-only / $8,750 family for
2026, plus a $1,000 age-55 catch-up never indexed) rather than a rate on a portfolio. Two
conditions are routinely dropped: it requires a high-deductible plan, and **California
breaks all three legs** — no deduction, *"Interest or earnings in an HSA are taxable in
the year earned"*, and internal sales are realisation events. New Jersey is widely
reported to do the same and **no New Jersey primary source was found at all**, so treat
that as inference from omission.

**Municipal bonds are material, maturity-dependent, and inactive here.** The break-even
marginal rate falls from **39.81% at two years to 15.58% at thirty**, so a top-bracket
investor gains 7 bp at two years and 222 bp at thirty. **Any rule of the form "municipals
for taxable accounts" is wrong at the short end.** Booked at zero for the reference
investor, because §1 puts bonds into the shelter first by a factor of four; municipals
activate only once the bond allocation exceeds shelter capacity.

**Specific identification of tax lots — cheap, legally clear, under-measured.** Treas.
Reg. §1.1012-1(c)(8) accepts *"a standing order or instruction"* and §1.1012-1(c)(10) says
the choice *"is not a method of accounting"*, so switching is free. The default without it
is FIFO, which realises the most gain. The only measurement found is a 1984–98 simulation
giving HIFO over average cost at *"73 basis points per year"*; a worked lot model confirms
the scale — twenty annual $10,000 purchases at 7%, selling a quarter, realises **$83,159
under FIFO against $31,944 under HIFO**. **Booked at 5 bp**, heavily shrunk, because a
buy-and-hold investor who never sells realises nothing. **This is the weakest additive
line on the page** — a judgement, not a measurement.

**Not booked, each for a stated reason.** *Charitable gift of appreciated shares* — real,
and worse in 2026 (a new 0.5%-of-AGI floor absorbs capital-gain property first, and a
rewritten §68 caps the marginal subsidy at 35%) — but a cheaper way to do something the
investor was already doing is not a return. *Net unrealised appreciation on employer
stock*, worth 13.6 bp/yr in a stated case, but narrow, and it is the one appreciated asset
that does **not** get a step-up. *Tax-gain harvesting in the 0% bracket*, worth 47.6 bp/yr
over ten years, but it needs a low-income year, competes with Roth conversions for the
same bracket space, and **reduces future harvesting capacity** by raising basis. And two
*errors avoided* — the IRA wash sale above, and a fund only 70% qualified on a 2% yield
losing 10.2 bp/yr — because an avoided mistake is not a return source.

---

## The ledger

| Lever | bp/yr, portfolio | Range | Additive to the 89 bp? |
| --- | ---: | --- | --- |
| **Fund structure: capital-gain distributions avoided** | **+23.0** | 0 to +50 | **ADDITIVE**, and **decaying** |
| **Specific identification of tax lots** | **+5.0** | 0 to +44 | **ADDITIVE** (residual only) |
| Foreign tax credit forfeited inside a shelter | **−3.4** | −6 to 0 | **correction** to the 10 bp location line |
| Direct-indexing fee, netted against harvesting | **−4.4** | −30 to +6 | **correction** to the 30 bp harvesting line |
| Securities lending, verified by asset class | +0.5 | 0 to +2 | same 1 bp line, revised |
| Deferred unrealised gain | 84.1 | 0 to 162 | **No — a hurdle, not a saving** |
| Municipal bonds | 0.0 | 0 to +222 | inactive; the shelter covers the bonds |
| §1256 60/40 treatment | 0.0 | 0 to +51 | no futures sleeve; leverage is zero |
| Traditional vs Roth, and the HSA | 0.0 | — | **probabilistic**, or a dollar limit |
| Charitable gift, NUA, tax-gain harvesting | 0.0 | 0 to +48 | each needs a circumstance, not a decision |
| Wash sale into an IRA; non-qualified dividends | 0.0 | 0 to +119 | errors avoided are not returns |
| **Additive total** | **+28.0** | 0 to +94 | |
| **Corrections** | **−7.8** | | |
| **Revised own-counterfactual budget** | **≈109 bp** | **4 to 270** | was 89 bp, range 40–170 |

**Read the 4-to-270 as an outer bound, not a distribution.** It assumes every condition
fails together at the bottom (a sheltered account, an index-fund counterfactual, a static
investor at a 40 bp fee) and succeeds together at the top, and those conditions are
correlated rather than independent. The central 109 bp belongs to the reference investor
at the head of this page and to nobody else automatically.

At ≈109 bp against roughly 46 bp of **assumed** combined tracking error, 90% confidence
arrives in about 3.5 months and 99% in about twelve — against 4.2 and 13.8 months for the
89 bp budget. **A fifth more edge buys about two months.** Certainty is a property of the
pairing of edge and benchmark, not of the edge's size.

---

## Assumptions, open questions, provenance

**Assumptions.** Pre-tax log growth of 7%/yr with constant parameters, no volatility and
no cash flows; tax paid from the account; distributions reinvested; rates constant over
thirty years, which no thirty-year period in US history has satisfied; the reference
allocation and account split fixed. All fail in directions that mostly *reduce* the
measured advantage, except constant rates, which cuts both ways.

**Open questions.**

1. **The implied financing spread a retail investor actually pays** through a
   capital-efficient fund. No 2019–2026 measurement was retrieved, and none at all of what
   a specific fund's roll costs. **The binding gap on §3.**
2. **The asset-weighted capital-gain distribution rate of the active funds a real investor
   would otherwise hold.** The 3% central is bracketed by frequency data and two named
   funds at 6.6–7.0%, but no asset-weighted average was found. **The largest additive line
   rests on it.**
3. **Whether ETF share classes actually eliminate the distributions.** Ninety-four orders
   exist; no SEC document quantifies the benefit, and the operative conditions live in each
   applicant's 40-APP application, which was not read.
4. **The value of lot-selection discipline for a retail buy-and-hold investor.** The only
   measurement is a simulation on a turning-over separate account.
5. **Non-US tax.** A jurisdiction with no foreign tax credit turns §1 into a pure cost; one
   taxing gains on accrual removes §4 entirely; one with no step-up removes half of it.
6. **State tax.** Excluded and additive.

**Reproducibility.** Rates, yields and profiles are arguments rather than constants, all
committed in `tax_structure.py` with the source beside each. Retrieval date **2026-08-12**
except: municipal and Treasury curves 2026-07-29, Treasury par cross-check 2026-08-11, BND
yield 2026-08-10, MSCI yields 2026-07-31, SEC order count 2026-08-11. Sources that
resisted retrieval are registered in [the evidence base](evidence-base.md) §3.

---

## Consequence for this repository

1. **Revise the own-counterfactual budget to about 109 bp/yr**, record that its largest
   component is decaying, and **never quote it without its conditions**.
2. **Add the deferral hurdle to the promotion protocol.** Any sleeve that turns over a
   taxable portfolio must clear 84 bp/yr at thirty years *before* its fee and its spread.
   It is larger than every premium any experiment here has measured.
3. **The tax boundary must be a dated, versioned input.** `TaxRegime` in
   `tax_structure.py` is the shape — a labelled, jurisdiction-stamped, dated set of rates
   that refuses to construct without them. Nothing hardcodes a rate again.
4. **Asset location must be computed, not asserted.** The rule "shelter the higher-yielding
   asset" is right for bonds by a factor of four and wrong for emerging-market equity at
   two of the four US dividend rates. Any location feature runs the ranking and states the
   bracket it assumed.
5. **Do not build a capital-efficiency feature, and do not close the question either.**
   §3's four conditions are what would reopen it.
6. **Recheck the fund-structure line before it is used.** A page whose largest new line has
   a visible mechanism of decay carries a review trigger, and this is it.
</content>
