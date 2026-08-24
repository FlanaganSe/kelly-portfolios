# Structural and tax-aware edges: what else is contractual, and how big is it

**Question.** The [edge decomposition](expected-edge-decomposition.md) prices a
contractual edge of about 89 bp/yr against the investor's own plausible alternative.
What else belongs in that class, how large is it, and does it double-count what is
already booked?

**Decision it informs.** Whether the contractual budget should be revised, which account a
real investor's international sleeve belongs in, and — in
[§8](#8-the-investors-plan-eight-funds-three-accounts-and-a-ranking-that-does-not-move) —
where one stated investor's eight named funds actually go.

**Scope.** US federal individual investor, `as of 2026-08-12` for §§1–7 and `2026-08-22`
for §8. State income tax is excluded and additive wherever it exists. **This is not personalised advice** — it is a
sizing exercise for a class of edge, and every figure is a function of stated inputs a
different investor should restate. Non-US investors differ on every line.

Everything numerical regenerates from
[`studies/tax_structure.py`](../../research/src/portfolio_edge/studies/tax_structure.py)
and [`studies/investor_placement.py`](../../research/src/portfolio_edge/studies/investor_placement.py),
pinned in `research/tests/unit/test_studies_tax_structure.py` and
`research/tests/unit/test_studies_investor_placement.py`. No market data, no randomness, no
forecast.

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
3. **The foreign tax credit does invert standard asset-location advice — and then the
   funds' own filings invert it back.** The credit is paid and permanently lost inside a
   traditional account and a Roth alike, which on an assumed 100%-qualified sleeve puts the
   emerging-market break-even at **21.5%**, between two live US brackets, so an investor at
   15% or 18.8% would hold emerging-market equity in taxable. **The sponsors file qualified
   fractions of 25% to 45%**, and the ordinary-rate remainder more than reverses it:
   [§8](#8-the-investors-plan-eight-funds-three-accounts-and-a-ranking-that-does-not-move)
   ranks named funds and puts **both emerging funds above US equity at every live US
   rate**. The related open input — two withholding figures that appeared to disagree —
   is closed: they were the same fact on two denominators and reconcile to four figures.
4. **Capital efficiency is the most substantive structural candidate and the only one
   whose sign this repository cannot check.** A 90/60 return-stacked fund needs
   **92 bp/yr** of Treasury excess return over cash before its overlay contributes
   anything, against a futures funding basis this page **previously mis-benchmarked at
   58.70 bp/yr and now puts at 12–33 bp**, which roughly halves the hurdle. Both inputs are
   forecasts, so it is probabilistic by construction.
5. **The largest additive line is decaying while being measured, and the decay is now
   counted rather than inferred.** 94 SEC orders let mutual funds add ETF share classes,
   and Form 497K filings naming an "ETF Class" went from **2 documents to 89 across the
   first order**, every one of the 14 registrants an *active* manager — which is the
   counterfactual the 23 bp is measured against. **Recheck before any decision leans on
   it.**
6. **The core beta shelf is now audited on cost, and the fee ranking is not the cost
   ranking** (§6). Across 25 funds and 110 N-CEN filings, `fee − securities lending` puts
   **IEMG at 9 bp of fee below VWO at 6**, makes **BND the dearest aggregate-bond fund on
   the shelf** because it is the only one that does not lend, and prices **SPY at five
   times any other S&P 500 tracker**. Capital-gain distributions are **zero for all 25
   funds in every year filed**, so no fund choice inside this shelf buys any of §2's line.
   **The whole decision is worth 0.60 bp/yr against the recommended four** — two orders of
   magnitude below §4's turnover hurdle.
7. **The waiver risk is real and it was pointed at the wrong fund.** IEMG's `(0.00)%`
   line is a **0.09% cap running to 2030-12-31 with no recoupment** — the most durable fee
   commitment on the shelf. The only recoupable waiver anywhere on it is **Schwab's SCHF
   and SCHE**, disclosed in Form N-CEN Item C.8 since fiscal 2022 and **in no document a
   shareholder reads**.
8. **Applied to one real investor with all three account types, the fill order is stable
   and the prize is small.** **VTI — the cheapest, broadest fund in the portfolio — is last
   in the shelter queue at every rate**, and every international fund outranks every US
   equity fund. But the honest value against a control the investor could actually have
   executed is **+2 to +7 bp/yr**, not the +38 to +55 an earlier draft published; that
   figure summed three benchmarks, booked a hurdle as a saving, and rested mostly on a
   wrapper accrual no shareholder was taxed on. **The binding constraint is not the tax
   code but the employer plan's fund menu**, which below a rollover share of 0.55 evicts
   the two highest-yielding funds from the shelter and forces the lowest-priority one in.

**One caution on the whole page.** §§1–7 are sized for **one stated reference investor** —
US top bracket, 30-year horizon, liquidation at the end; 60% US equity, 14% developed ex-US,
6% emerging, 20% taxable bonds; 40% of the portfolio in tax-advantaged capacity. **§8 is a
different investor** — equal thirds of Roth, traditional and taxable, no bonds, named funds
— and it is stated across a bracket range rather than at one rate. Quoting a per-sleeve
number as a portfolio number is the commonest way a tax figure is inflated, and every lever
here has a different base.

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
- **At 15% or 18.8% the ranking inverts** *on this table's assumption*: emerging drops to
  10.45 bp of priority against US equity's 16.50. **The assumption is that every equity
  sleeve is 100% qualified, and it is wrong for emerging markets by a factor of three.**
  See the two subsections below; the fund-level answer in
  [§8](#8-the-investors-plan-eight-funds-three-accounts-and-a-ranking-that-does-not-move)
  runs the other way at every rate.
- **Bonds dominate by a factor of four at every rate**, so the uncontested half of the
  conventional rule is uncontested here too. Note the 189.7 uses the top ordinary rate
  and must be restated with the investor's own — at 22% it is about 102 bp, and still
  dominates.
- **The 0% bracket is the trap.** §904 limits the credit to US tax on foreign-source
  income, and there is none. Such an investor forfeits the withholding in *both*
  locations.

**Two limits.** Below **$300 of creditable foreign tax ($600 joint)** the credit is
claimed without Form 1116 and without the §904 limitation — a threshold reached at about
$190,153 of developed-market holdings, and neither figure is indexed. And a shelter also
shelters **capital-gain distributions**, which this table omits: on the cheap shelf that
omission is worth zero, because [§6.3](#63-capital-gain-distributions-zero-everywhere-including-the-unit-trust)
finds every fund distributed **0.00** of realised gain in five fiscal years — but it is not
zero off that shelf. [§8.2](#82-the-inputs-from-the-funds-own-filings) measures a
105%-turnover international momentum fund distributing **2.14% of net assets** of capital
gain in one December, which nearly doubles its priority. What remains unquantified is that
a taxable international position is a better loss-harvesting candidate.

### The withholding rate: the open input is closed, and the two figures never disagreed

`as of 2026-08-22`. This section used to record eleven funds filing a `foreign taxes paid ÷
foreign source income` ratio of 5.99–7.61% developed and 9.12–14.23% emerging against the
6.068% and 9.853% used above, and to call the gap **the largest open input on the page**.
**It is not a disagreement. It is two denominators**, and they reconcile exactly.

A sponsor's shareholder worksheet states foreign tax as a share of the **dividend**; a
fund's N-CSR tax note states it as a share of **foreign source income**; and foreign source
income is 77% to 100% of the dividend, never all of it. Vanguard's own worksheet gives VEA
foreign source income of **79.6488% of Box 1a**, and

```
6.068% ÷ 79.6488% = 7.618%
```

which is the 7.61% VEA's own N-CSR files. Same fact, two bases.

**The gross-versus-net question the old text could not settle is settled, from three
sponsors, arithmetically rather than by reading.** Vanguard's worksheet footnote defines
Box 1a as *"ordinary cash dividends paid by the Fund, short-term capital gains paid by the
Fund, and foreign taxes paid"* — gross by construction. iShares' 2025 distribution summary
gives IEMG cash of **$1.848602** plus foreign tax of **$0.196929** equal to Box 1a of
**$2.045531** per share, to the cent. Avantis' 2025 ICI file gives AVES **$1.8479** plus
**$0.246250712** equal to **$2.094150712**, to the cent.

**Consequence: the inputs above do not move, and the trap is now named.** Multiplying a
fund's whole dividend yield by a filed foreign-source ratio overstates the withholding by
up to a quarter. Any later work quoting a withholding rate states which of the two bases it
is on.

### The qualified fraction is the input this section actually rests on, and it was assumed

`as of 2026-08-22`, and this is the correction that **reverses the finding above**.

The table's priority for a foreign sleeve collapses to `(q − w) y` only because the sleeve
is taken to be **100% qualified**. A qualified dividend is taxed at `q`; the rest is
ordinary income, taxed 17 pp higher at the top bracket. The sponsors file the fraction and
it is nowhere near one:

| Fund | Qualified dividend income, filed | Source |
| --- | ---: | --- |
| VEA | **66.27%** of Box 1a | Vanguard 2025 foreign tax credit worksheet |
| VWO | **34.63%** of Box 1a | the same worksheet |
| IEMG | **34.82%** | iShares 2025 QDI summary |
| AVES | **44.48%** | Avantis 2025 tax centre |
| IDMO | **25%** of ordinary income dividends | Invesco N-CSR, FY ended 2025-10-31 |
| DFIV | **100%** of ordinary income distributions | Dimensional N-CSR, FY ended 2025-10-31 |

Emerging markets is low for a statutory reason: [§1(h)(11)(C)](https://www.law.cornell.edu/uscode/text/26/1)
qualifies a foreign corporation only if it is eligible for a comprehensive US tax treaty or
its stock is readily tradable in the US, and several large emerging markets are neither.
IDMO's 25% is a **turnover** effect — [§1(h)(11)(B)(iii)](https://www.law.cornell.edu/uscode/text/26/1)
requires the fund to hold the stock more than 60 days in the 121-day window around the
ex-dividend date, and IDMO's portfolio turnover is 105%.

**Restoring the filed fraction destroys the emerging inversion.** At the 15% qualified rate
an emerging fund's US tax is no longer `0.15 y` but roughly `0.35 × 0.15 y + 0.65 × 0.24 y`,
which is 39% higher, and the sleeve moves back above US equity. [§8](#8-the-investors-plan-eight-funds-three-accounts-and-a-ranking-that-does-not-move)
runs it at fund level: **both emerging funds outrank US equity for shelter capacity at every
live US rate.** The inversion was an artifact of an assumed input, not a property of the
funds — which is the same lesson as the paragraph above, in the opposite direction.

**Splitting the international sleeve is worth 1.33 bp/yr of equity at most.** The
recommendation holds VEA + VWO rather than one total-international fund *because*
splitting is what makes this ranking available. That is a quantity, so
[`international_split_versus_single_fund`](../../research/src/portfolio_edge/studies/tax_structure.py)
computes it rather than asserting it: at the 60/30/10 equity composition the gain peaks at
**1.334 bp/yr of the equity sleeve at 23.8%** and **0.958 at 15%**, both at a shelter
holding 30% of equity after bonds, and it is **exactly zero** when the shelter holds
everything or when the qualified rate is 0%. A single fund's priority is the *weight
average* of the two it replaces, because taxable cost and forfeited withholding are both
linear in yield at these rates. **The fee difference is separate and larger than it looks;
[the recommendation](portfolio-recommendation.md#current-answer) prices the whole trade.**

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

**Falsifier, already firing, and now with adoption measured rather than inferred.** The SEC
granted its first ETF-share-class order on 2025-11-17 and its listing shows **94 granted
orders as of 2026-08-11**. An order is permission, not a share class, so the
decision-relevant quantity is adoption, and it has three tiers. **Filings**: Form 497K
documents containing `"ETF Class"` went from **2 in the ten and a half months before the
first order to 89 in the nine months after, from 14 registrants**, `as of 2026-08-17`.
**Launches**: nine funds from six managers, Dimensional first on 2026-03-20 and the first
S&P 500 one — **DLCU**, the ETF class of its $14.09bn U.S. Large Company Portfolio at 0.06%
net — on **2026-08-05**. **Silence**: Schwab, BlackRock, JPMorgan, T. Rowe Price, Goldman,
Morgan Stanley and Fidelity's index range all hold orders and have filed nothing.

**Every registrant that has filed is an active or systematic manager**, which is what makes
it bind: the cheap index sponsors already have ETFs, and the funds converting are precisely
the counterfactual the 23 bp is measured against. Vanguard remains the proof of concept —
VFIAX and VTSAX show zero capital gains for a decade because they share a portfolio with
VOO and VTI. **So the fuse is lit but slow, and if FXAIX or SWPPX sprouts a class the line
moves quickly.** The opposite risk also exists — a 2021 Senate Finance discussion draft
proposed to repeal the RIC exception outright; never enacted, no successor found.

---

## 3. Section 1256, and capital efficiency handled honestly

**§1256** marks a regulated futures contract to market at year end and splits the gain
60/40 long/short-term regardless of holding period, blending to 30.6% at 2026 top rates.
Against ordinary annual treatment it saves **51 bp/yr on a 5% return**; against a deferred
long-only equity holding it is **−31 bp/yr**, because the rate is higher *and*
mark-to-market destroys the deferral §4 prices. Which is the counterfactual decides the
sign, and nothing about the statute settles it.

**The claim that the 60/40 split reaches no shareholder does not hold, and two funds now
falsify it.** From N-CSR tax-character tables: **DBMF distributed 100% ordinary income in
2024 and 2025; KMLM 100% in FY2026; CTA 100% in FY2025**. But **CTA's FY2024 distribution
was 59.9% ordinary and 40.1% long-term capital gain**, and **RSST's fiscal year to
2026-01-31 was 74.3% long-term capital gain — $2,648,642 against $915,484 of ordinary
income** (`as of 2026-08-22`). So the split does reach shareholders, in some funds in some
years, and which ones cannot be predicted from the structure. Three mechanisms stack: a Cayman subsidiary converts commodity gains to ordinary income
**asymmetrically** (DBMF's prospectus: *"any annual net loss of the Subsidiary will not be
recognized and will not carry forward"*), forced by §851(b)(2); capital-loss
carryforwards absorb the long-term half; and §1256(f)(2) cannot rescue income that is
ordinary by another route. **NTSX needs no Cayman blocker** — Treasury futures generate
qualifying income directly.

**But calling NTSX "the structural exception" attributed its clean record to the wrong
mechanism, and the filings say otherwise. `as of 2026-08-17`.** Its zero-capital-gain record
is produced by the *same* loss-absorption machinery this paragraph attributes to DBMF and
KMLM, plus the ETF wrapper: **capital loss carryforwards of $170.7m at 2024-06-30 and $163.5m
at 2025-06-30 — about 13.6% of net assets** — and permanent book/tax reclassifications
*"primarily due to redemptions-in-kind"* of **$15.4m (FY2024) and $30.4m (FY2025)**. A fund
with a loss bank that size and in-kind redemption relief would show no capital gain whatever
its futures were.

**And "a single Ordinary Income column" understates NTSX in the other direction.** Ordinary
income is the RIC *distribution category*, not the rate. NTSX designates **100.0% of its
FY2023 distribution, 98.7% of FY2024 and 84.9% of FY2025 as qualified dividend income**, so
nearly all of it is taxed at long-term rates. Its filed after-tax return since inception to
2024-12-31 is **11.58% before tax against 11.25% after taxes on distributions — a 33 bp/yr
drag**. Two further corrections of record: the two-column presentation exists in the FY2023
N-CSR, so the single column is a FY2025 presentation change rather than a permanent feature;
and **FY2021 did carry a $0.02/share capital-gain distribution**, so the "no capital-gains
distributions" claim must keep its 2022 start date. Every figure here is from
WisdomTree Trust's own N-CSR filings; the wrapper audit is in
[capital efficiency §6a](capital-efficiency-and-breadth.md).

### Gold is the one asset class whose wrapper carries a *worse* rate than ordinary equity

`as of 2026-08-17`, and it decides account placement rather than whether to hold anything.

A physical-gold ETF is a grantor trust holding bullion, so the shareholder is treated as
owning the metal, and metal is a **collectible**. IRS Publication 550 defines collectibles
gain as gain from "a work of art, rug, antique, **metal (such as gold, silver, and platinum
bullion)**, gem, stamp, coin, or alcoholic beverage held more than 1 year", and its
Table 4-4 gives the maximum rate as **28%**. The statutory route is
[26 U.S.C. §1(h)(5)](https://www.law.cornell.edu/uscode/text/26/1), which cross-references
§408(m) **"without regard to paragraph (3) thereof"** — so the bullion carve-out that
exists for IRA *eligibility* does not rescue bullion from the rate.

**The funds say it themselves**, which is what makes this a verified fact rather than an
inference. All four bullion trusts checked on 2026-08-17 carry near-identical language;
GLD's Form 10-K for the year ended 2025-09-30: *"gains recognized by individuals from the
sale of 'collectibles,' including gold bullion, held for more than one year are taxed at a
maximum rate of 28%, rather than the 20% rate applicable to most other long-term capital
gains."* Its prospectus adds the look-through — a gain on shares in a trust holding
collectibles is itself collectibles gain — and confirms the **3.8% NIIT sits on top**:
*"This tax is in addition to any capital gains taxes due on such investment income."*

| | Top federal rate on a long-term gain |
| --- | ---: |
| Equity, for comparison | 20% + 3.8% = **23.8%** |
| **Bullion ETF (GLD, IAU, GLDM, SGOL)** | **28% + 3.8% = 31.8%** |
| §1256 futures blend, 60/40 | 30.6% — the rate §3 already books |

**Placement, and the qualification that matters.** Both GLD and IAU disclose **IRS private
letter rulings** that purchase by an IRA or a §401(a) participant-directed account "will
not be treated as the acquisition of a collectible", so the 28% rate does not apply inside
a shelter. Three limits travel with that: **neither fund discloses the ruling number, and a
PLR binds only its requester**; traditional-IRA distributions are **ordinary income**
(Publication 590-B, "you can't use… capital gain treatment"), which at the top bracket is
worse than 28%; and an in-kind redemption into bullion re-triggers §408(m). **So the
shelter removes a penalty rather than conferring an advantage, and the gold sleeve would
compete for the same scarce shelter as the managed-futures overlay** — which
[the recommendation](portfolio-recommendation.md) already identifies as the binding
constraint on that overlay's weight.

**The futures route does NOT get the 60/40 treatment, and this was checked rather than
reasoned.** A reader — and this repository's own first draft — would expect a RIC holding
§1256 gold futures to deliver 60% long-term / 40% short-term under
[§1256(a)(3)](https://www.law.cornell.edu/uscode/text/26/1256). **It does not**, and the
reason is the same §851(b)(2) qualifying-income mechanism §3 already documents for DBMF,
KMLM and CTA.

WisdomTree's GDE holds its gold exposure through a **Cayman Islands subsidiary** capped at
**25% of total assets at each fiscal quarter-end**, disclosed in its own summary prospectus
dated 2026-01-01: *"The Fund seeks to gain exposure to the commodity market for gold… through
investments in a subsidiary organized in the Cayman Islands… intended to provide the Fund
with exposure to the investment returns of gold while enabling the Fund to satisfy
source-of-income requirements that apply to RICs under the Code."* The audited FY2025
N-CSR names it **WisdomTree Efficient Gold Plus Equity Strategy Portfolio I**.

The trust's own SAI states what that does to the character, and states the asymmetry:

> "Subpart F income and GILTI are treated as **ordinary income, regardless of the character
> of the CFC's underlying income**. Net losses incurred by a CFC during a tax year **do not
> flow through** to a Fund… In addition, the net losses incurred during a taxable year by a
> WisdomTree Subsidiary **cannot be carried forward**."

And the audited distribution tables say what actually happened. **Every dollar GDE has
distributed in all three fiscal years since its March 2022 inception was ordinary income:
$29,464, $307,865 and $3,699,370, against zero long-term capital gain and zero return of
capital.** Only **28.9%** of the FY2025 figure was qualified dividend income; the
dividends-received deduction was **5.44%**. NTSX, which needs no blocker because Treasury
futures generate qualifying income directly, shows **84.9% QDI and an 84.19% DRD** on the
same trust's filings. **The SAI's own 60/40 discussion is confined to non-equity options the
funds write directly and says nothing about the Subsidiary's futures.**

| | Annual drag | Rate on the distribution | Rate on selling the shares | Deferrable? |
| --- | ---: | --- | --- | --- |
| **GLDM / GLD / IAU / SGOL** | ~0 | n/a — bullion trusts distribute nothing | **28% + 3.8% collectibles** | **yes, indefinitely** |
| **GDE** | **1.53 pp/yr**, measured | **ordinary**, only 28.9% at QDI rates | 20% + 3.8%, ordinary capital gain | **no** |

**So the two routes trade one tax against the other and neither dominates.** The physical
wrapper pays a *higher rate* on a gain it can defer for decades; the overlay wrapper pays
an *ordinary rate annually* on income it cannot defer, and its losses are trapped inside
the CFC. Against §4's finding that deferral is the largest number on this page, **the
physical route is the tax-favoured one for a long holder and the overlay route is not** —
which is the reverse of what the fee comparison alone suggests.

**One thing the collectibles rate does not do is reach GDE.** The word "collectibles"
appears **zero times in every filing WisdomTree Trust has ever made**, against 76 hits for
SPDR Gold Trust on the same full-text search. Its SAI treats a share sale as ordinary
capital gain with no carve-out. **GDE is a structurally different after-tax asset from a
bullion trust, and the 28% finding above does not transfer to it.**

**And there is still no plain futures vehicle.** **Invesco DB Gold (DGL) liquidated in March 2023**
(Form 8-K filed 2023-01-23; shares "cease trading on the NYSE Arca, Inc. after market close
on March 3, 2023"), and the surviving ProShares UGL is **2× geared**, costs **1.19%**
all-in, issues **K-1s**, and warns in its own prospectus that "swap agreements and
non-currency forward contracts are **generally not** Section 1256 Contracts". A 120 bp rate
saving is not worth 119 bp of fee, leverage and a K-1. 

**Consequence.** Gold's tax treatment is a reason to place it, never a reason to hold it.
It does not change the verdict, which is on return:
[marginal sleeve value § Gold, tested](marginal-sleeve-value.md#gold-tested).

---

**Capital efficiency: the mechanism, the cost, and why it is not booked.** A
"return-stacked" fund at 90% equity plus 60% Treasury-futures notional obtains 150% of
exposure per dollar. WisdomTree's NTSX is the reference case at 0.20% total expenses. The
arithmetic of whether it helps is entirely in one expression:

```
net contribution = bond notional × (bond excess return over cash − implied financing spread) − fee
```

**The financing spread was measured here against the wrong benchmark, and the correction
roughly halves the hurdle.** `as of 2026-08-16`.

**Do not benchmark a fund's financing on Fleckenstein and Longstaff's 58.70 bp.** That
figure — 6,943 daily observations of CME 5-year Treasury note futures, 1991–2018, positive
in all 28 years — is real, and it is not the number a fund pays. They define the funding
basis against the **term bilateral
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
| Gold futures | Treasury curve | ≤40 bp, and an **upper bound** — the identical 40 bp appears in SPX option boxes over the same window, so it is the Treasury convenience yield rather than anything gold-specific. **This is now a live number rather than a hypothetical**: WisdomTree's GDE stacks gold-futures notional on US equity for a 0.20% fee, so the all-in overlay cost is about 0.60%/yr ([capital efficiency §3a](capital-efficiency-and-breadth.md)) |
| Equity index futures | 3-month Term SOFR | **+62 bp**, ten rolls Dec-2022→Mar-2025. A genuine post-2022 regime change |
| **Diversified long/short trend book** | local interbank | **signed mean ≈ 0** |

**The NTSX hurdle, re-based:**

| Financing input | 90/60 break-even |
| --- | ---: |
| 58.70 bp (special-collateral repo — **not a rate a fund pays**) | 92.0 bp/yr |
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

**NTSX's own record does not settle it either way.** From its own filed prospectus, for
periods ending **2024-12-31**, since inception 2018-08-02: **11.58%/yr against 8.86% for the
60/40 composite and 13.99% for the S&P 500 alone**, `as of 2026-08-17`. The 60/40 comparison
is **not risk-matched**, and outperforming a lower-risk portfolio in an equity bull market
is precisely the trap
[decision 0003](../decisions/0003-cheap-broad-market-control.md) exists to catch. It made
no capital-gains distributions in any fiscal year 2022–2025 nor in the six months to
2025-12-31 — which spans the December date an ETF's annual capital gain would fall on —
and that is a real and separate point in the structure's favour. **January–June 2026 is not
yet reported.**

**The two sibling funds are the counter-evidence and they are not a footnote.** NTSI
returned **−0.77%/yr against MSCI EAFE's +2.26%** and NTSE **−5.90%/yr against MSCI EM's
−3.18%** since their common 2021-05-20 inception, on the same filed basis — **each losing to
its own equity leg's index by roughly 3 pp/yr** while the Treasury overlay ran through the
2022 rate rise. Neither is given a blended 90/60 benchmark in its own prospectus, so no
risk-matched comparison is published for either.

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

## 6. The core beta shelf, audited on cost rather than on fee

`as of 2026-08-17`. Twenty-five funds in six categories, every fiscal year Form N-CEN has
published — **110 filings, eight fiscal years for all but two funds**. Regenerate with
`cd research && uv run python -m portfolio_edge.studies.core_beta_shelf --build`; every
figure below is pinned in `tests/unit/test_studies_core_beta_shelf.py` and each filing's
URL and sha256 is in
[`data-manifests/core_beta_shelf/ncen_costs.json`](../../research/data-manifests/core_beta_shelf/ncen_costs.json).

**This section replaces a six-fund N-CSR lending table.** Its three findings survive
verbatim on eight times the data — the 1 bp booked is right for a US total-market fund
and low for an international one, the premium is *not* a size effect, and the sponsor
matters more than the asset class. What that table could not say is the thing that
decides a fund choice.

### 6.1 Net cost, and why it is not the fee ranking

`net cost = expense ratio − net securities-lending income`. Both terms are measured
against **the fund's own net assets** rather than against an index, so adding them is not
the benchmark switch [`aggregate()`](../../research/src/portfolio_edge/studies/outperformance_horizon.py)
refuses. The fee is the current 497K table
([dated per fund](portfolio-recommendation.md#current-answer)); lending is the **median**
over every fiscal year on file, from N-CEN Item C.6.g over Item C.2.

| Category | Cheapest to own → dearest, bp/yr net | | |
| --- | --- | --- | --- |
| **US total market** | ITOT **1.04** · VTI 1.16 · SCHB 1.96 · SPTM 2.63 — but **SPTM tracks the S&P Composite 1500, not a total-market index** ([§6.7](#67-what-the-shelf-is-missing-and-one-fund-that-is-in-the-wrong-category)) | | |
| **S&P 500** | SPLG **1.82** · IVV 2.75 · VOO 2.94 · **SPY 9.45** | | |
| **Developed ex-US** | SPDW **−1.63** · VEA −0.30 · SCHF 1.84 · IDEV 2.11 · IEFA 4.65 | | |
| **Emerging** | IEMG **−0.87** · VWO 1.67 · SPEM 2.01 · SCHE 4.84 · AVEM 25.99 · **EEM 67.34** | | |
| **Total international** | VXUS **1.43** · VEU 1.61 · IXUS 3.99 | | |
| **Aggregate bonds** | SPAB **2.09** · AGG 2.74 · SCHZ 2.93 · **BND 3.00** | | |

**A fee comparison is not a cost comparison, and here is the same finding on the funds
that hold the money.** [Experiment 013](factor-products.md#the-us-shelf-on-the-corrected-frame)
established it where 35 of 109 US factor products lost more than 0.50 pp/yr to a cheap
replication against a fee premium of at most 0.57. On the core shelf it shows up three
times:

- **IEMG charges 9 bp against VWO's 6 and is the cheaper fund to own.** Its lending income
  covers the whole fee and 0.87 bp besides. SPDW's 3 bp fee is covered twice over.
- **BND is the dearest aggregate-bond fund on this shelf at an identical 3 bp fee**,
  because it is the only one that does not lend at all: Vanguard answers Item C.6.a "No"
  for the Total Bond Market Index Fund in **all eight fiscal years**.
- **SPY costs five times any other S&P 500 fund** — 9.45 bp against 1.82 to 2.94 — and its
  own prospectus forbids the offset. It "is not authorized to … **lend its portfolio
  securities or other assets**", holds dividends in "a **non-interest-bearing account**"
  whose earnings credit accrues to the Trustee rather than to unitholders, pays them "on
  the last Business Day in the calendar month following each Ex-Dividend Date", and states
  that "**no dividend reinvestment service is provided by the Trust**". Four separate cash
  drags, all structural to the unit investment trust, none of them in the 0.0945% fee.

**Two things the lending column is not.** It is **not contractual**: the fee is a filed
commitment and borrow demand is not, so the sign is certain and the size is a measurement.
And **a high lending yield is partly compensation for holding what short sellers want** —
IEMG's 8.30–12.12 bp range over eight years is emerging-market borrow demand, which is a
property of the holdings and not of the manager. What makes the column usable anyway is
that its *rank* is stable: VOO has been the lowest-earning fund here in all eight years
and IEMG among the highest in all eight.

### 6.2 Tracking difference — filed, and mostly unusable across funds

Item C.3.b.ii files "the annualized difference between the Fund's total return … and the
index's return", before and after fund fees. It is the number a fee is usually mistaken
for, and this repository can use almost none of it, for three reasons that are worth more
than the number.

1. **Every fund's difference is against its own index, and the indices differ** —
   Morningstar US Total Market (**renamed from CRSP on 2026-07-29**), S&P Total Market,
   S&P Composite 1500, Dow Jones US Broad, FTSE, MSCI. Ranking funds across those is adding
   lines measured against different benchmarks. **The only group on this shelf that shares
   an index is VOO, IVV and SPLG**, and once compared they are indistinguishable: derived
   ETF-class differences of −1 to −4 bp, inside the 0.01 percentage point the filings round
   to.
2. **The item does not say which share class a multi-class fund answers for.** For every
   Vanguard series here the gap between the before- and after-expense figures is 9.5 to
   35.3 bp against an ETF-class fee of 3 to 6, so **the filed after-expense figure is not
   the ETF class's tracking difference.** For a single-class ETF the same gap recovers the
   expense ratio to the filed rounding, which is what identifies the defect.
3. **The figures are unaudited and the filings show it.** BlackRock filed the before- and
   after-expense differences as *the same number* for every iShares fund here in its
   fiscal-2025 and fiscal-2026 N-CENs, which cannot be true of a fund that charges a fee;
   IVV and AGG each lose three of eight years to that screen and IDEV two. Vanguard's
   filings lose none. **A page that ranked funds on the filed figure would be ranking
   filers.**

What survives is a null worth having. **Before fees, every fund on this shelf tracks its
own index to within a few basis points a year** — median differences of +0.03 (US),
+0.12 to +0.49 (developed ex-US), −0.24 to +0.23 (emerging), −0.04 to +0.00 (bonds). The
positive ex-US medians are **not skill**: a net-return index deducts withholding at the
maximum non-treaty rate, which the funds reclaim under treaty, and iShares says so in its
own prospectus footnote. Index-construction differences swamp everything else, which is
the same wall [Experiment 009's withholding bound](factor-products.md#scope-and-uncertainty)
hit from the other side.

The 497K "Average Annual Total Returns" tables agree, on the longest window filed. Fund
NAV return less its own target index, ten years to 2025-12-31: **VTI 0.00, VEA −0.01,
VXUS −0.01, VEU −0.02, VOO −0.04, BND −0.05, and VWO +0.04** pp/yr. Six funds at 3–6 bp of
fee, none trailing its index by more than its fee, and one ahead of it.

### 6.3 Capital-gain distributions: zero, everywhere, including the unit trust

From Financial Highlights, five fiscal years each, all twenty-five funds plus SPY:
**every ETF distributed 0.00 of realised capital gain in every year shown.** The only
non-zero figures anywhere on the shelf are BND's ETF class in FY2021 and FY2022, at
**20.8 bp and 7.0 bp of beginning NAV** — a bond fund, in the rate rise, and still an
order of magnitude below the 3%-of-NAV counterfactual §2 books against.

**So §2's 23 bp is intact and its comparator is confirmed as the right one.** The wrapper
advantage is against an *active* fund, never against another ETF, and no fund choice
inside this shelf buys any of it.

**And the decay §2's falsifier predicted has started, in exactly the direction that
consumes the 23 bp** — the converting sponsors are the *active* managers, which is the
counterfactual the line is measured against.

### 6.4 Waivers and recoupment — the risk is real and it is not where it was expected

A waiver line reading `(0.00)%` costs nothing today and can be withdrawn with no fee
increase announced; a **recoupable** one can be clawed back out of later years. Form N-CEN
Item C.8 asks all three questions and the answers are structured, so the whole shelf can be
screened rather than sampled.

| Sponsor | Expense limitation in place | Recoupable, per Item C.8 | What the fee table says |
| --- | --- | --- | --- |
| **Vanguard** (7 funds) | **never, in any of eight years** | never | no waiver line exists at all |
| **BlackRock** | IXUS, AGG, IEMG, IDEV(2018) | **never** | `(0.00)%` on IXUS, AGG, IEMG |
| **State Street** | SPTM, SPLG, SPAB, SPDW, SPEM | never | no line — the waiver is in the statutory prospectus |
| **Schwab** | **SCHF and SCHE since FY2022** | **SCHF and SCHE, every year since FY2022** | **no waiver line, and no recoupment language anywhere** |
| **Avantis** | never | never | no waiver line |

Three findings, and the first two run against what [the recommendation](portfolio-recommendation.md)
previously assumed.

- **IEMG's `(0.00)%` waiver is the most durable fee commitment on the shelf, not the least
  stable figure on it.** Its footnote is an expense *cap*: BFA "has contractually agreed to
  waive a portion of its management fee such that the Fund's total annual fund operating
  expenses after the fee waiver will not exceed 0.09% **through December 31, 2030**", with
  no recoupment. IXUS's and AGG's waivers are the ordinary acquired-fund-fee offset,
  expiring 2026-11-30 and 2027-06-30, also with no recoupment.
- **Schwab's two international funds are the only place on this shelf where a waiver is
  marked recoupable, and it appears in no document a shareholder reads.** SCHF and SCHE
  have answered Item C.8 "expense limitation: Yes / recoupable: Yes" in every N-CEN since
  fiscal 2022. The registrant's own 485BPOS returns **zero** hits for `recoup` or
  `recaptur`, its 28 MB fiscal-2025 N-CSR returns zero for `recoup`, `recaptur` and
  `expense limitation`, and the only `waiv` hits in the annual report are about the code of
  ethics. **Two of the same registrant's filings disagree, and the one carrying the
  recoupment flag is the one nobody reads.** Not resolved here: either Schwab is answering
  Item C.8 loosely, or an arrangement exists that its prospectus does not describe. Either
  way SCHF's audited expense ratio has been **0.05% (FY2025) and 0.06% (FY2024) against the
  0.03% in the fee table**, which is labelled "restated to reflect current fees".
- **State Street's waivers carry the strongest disclaimer and the shortest fuse.** Both
  trusts state the waiver "**does not provide for the recoupment by the Adviser of any
  amounts previously waived or reimbursed**" and both expire inside eighteen months —
  2026-10-31 for SPTM/SPLG/SPAB, 2027-01-31 for SPDW/SPEM. SPY's is weaker still: the
  Trustee's fee waiver is **voluntary rather than contractual**, runs to 2027-02-01, and
  the trust states plainly that "there is no guarantee that the Trust's ordinary operating
  expenses will not exceed 0.0945%".

### 6.5 What the lending line does to the budget

For the reference investor's 60/14/6/20 allocation held in the recommended four, the
measured lending pass-through is **1.83 bp/yr**, against the 1.0 bp originally booked and
the 1.5 bp the six-fund table corrected it to. Fund selection alone moves it between
**0.45 and 2.60 bp/yr** across the cheap shelf. The ledger line becomes **+0.83 bp**, and
it is still a rounding error on a 109 bp budget — which is the finding, not a
disappointment.

### 6.6 Spread and premium/discount, weighted as the one-time costs they are

`as of 2026-08-14`, from each issuer's own Rule 6c-11(c)(1) disclosure. **22 of 26 tickers
returned data; Schwab's site returns HTTP 403 to every path including `robots.txt`, so
SCHB, SCHF, SCHE and SCHZ are "not found" and were not worked around.**

| | 30-day median bid-ask spread |
| --- | --- |
| **US equity** | VTI 0.55 bp · VOO 0.56 bp · ITOT, IVV, SPLG, SPTM 1 bp · **SPY 0.00 bp** |
| **International equity** | VXUS 1.18 · VEU 1.21 · VEA 1.41 · VWO 1.70 · IEFA, IEMG, IXUS, IDEV 1 bp · EEM 2 · SPDW, SPEM 2 · AVEM 3 |
| **Bonds** | AGG 1 bp · BND 1.38 · SPAB 4 |

**A spread is paid once and a fee is paid for thirty years, so this table must not be
allowed to reorder §6.1.** VTI's 0.55 bp round trip is under half of one year's net cost;
over a thirty-year hold it is worth about 0.02 bp/yr. **SPY is the case that proves the
point**: it has the tightest spread on the shelf, at zero, and the highest cost of
ownership on it, at 9.45 bp/yr. A spread is what a *trader* pays. **Choosing SPY for its
spread is buying a one-time saving of under a basis point with a recurring cost of seven.**

Two dating properties of the source, which matter because they are easy to get wrong.
**iShares' premium/discount tables carry no as-of date at all** — the backing field is
`formattedAsOfDate: null` — while the spread and net-asset figures on the same page do
carry 2026-08-14. Do not borrow that date for them; each column carries its own period end,
identical across every fund checked, and the latest completed one is **2026-06-30**. And
**no published column and no sum of columns is a trailing twelve months**: Rule 6c-11
requires a calendar year plus year-to-date quarters, so 2025 + Q1 + Q2 spans twenty months
and the current quarter renders as "–" because it is not yet published. Any trailing-12m
figure is derived, not published.

One artifact worth stating so it is not read as a finding. **Both Vanguard and iShares
round the daily premium/discount to two decimals, so anything under 0.005% lands in
neither bucket** — 54 days for VTI, 46 for ITOT, 36 for VOO, 28 for IVV. Premium plus
discount does not sum to the trading year, and "days at discount" is not one minus days at
premium.

### 6.7 What the shelf is missing, and one fund that is in the wrong category

The 25 audited funds are not the whole shelf. Sweeping the SEC's own 2026Q2 N-PORT data set
— 12,945 ETF-like series — for plain-beta index funds in these six categories above $2bn
and at or below 0.10%, **six qualify and none was audited**:

| Fund | Category | Net assets | ER | Index |
| --- | --- | ---: | ---: | --- |
| **IUSB** | US broad bond | $36.5bn @2026-04-30 | 0.06% | Bloomberg US **Universal** — a superset of the Aggregate, so a different exposure rather than a cheaper tracker |
| **VONE** | US large blend | $11.3bn @2026-05-31 | 0.06% | Russell 1000 |
| **BBUS** | US large/mid | $7.8bn @2026-04-30 | **0.02%** | Morningstar US Target Market Exposure — the cheapest broad US equity ETF in the census |
| **BBIN** | Developed ex-US | $6.3bn @2026-04-30 | 0.07% | Morningstar Developed Markets ex-North America |
| **VTHR** | US total market | $6.1bn @2026-05-31 | 0.06% | Russell 3000 |
| **BKLC** / **BKAG** | US large blend / US aggregate | $5.3bn / $2.1bn @2026-04-30 | **0.00%** | Solactive GBS US 500 / **Bloomberg US Aggregate** — the same index as AGG, SCHZ and SPAB, at no fee |

**BKAG is the one that could move §6.1**, because it tracks the same index as three audited
bond funds at a zero expense ratio, and BND — the recommended holding — is the dearest of
those three at 3.00 bp. **Its lending income, its waiver terms and whether a 0.00% fee is
contractual or an absorbed cost were not read**, so it is recorded as a candidate and not
as a result. Both BNY Mellon funds sit at or near the $2bn floor and are five years old.

**Two facts about the audited shelf itself were wrong.** **SPTM is not a total-market
fund**: its SEC series name is "State Street SPDR Portfolio **S&P 1500 Composite** Stock
Market ETF" and has been since at least the 2021-06-30 N-PORT, so treating it as State
Street's answer to VTI is a category error — State Street has no total-market fund. And
**SPLG no longer trades under that ticker**: SPDR Series Trust's Form 497 of 2025-10-21
(accession `0001193125-25-245123`) states that "*Current Ticker Symbol SPLG / New Ticker
Symbol SPYM*", alongside a "State Street SPDR" rebrand of the whole line. The N-CEN series
identity is unchanged, so every figure above still applies; only the ticker moved.

**Excluded on their own terms, and worth naming so nobody re-tests them.** Dimensional's
and Avantis's broad funds — DFUS ($19.9bn, 0.09%), DFAI, DFAX, DFAE, AVUS, AVDE — clear
size and, for DFUS, fee, and are **not index funds**: DFUS's own prospectus says it "*is an
actively managed exchange-traded fund and does not seek to replicate the performance of a
specific index*". **VT** ($89.9bn, 0.06%) qualifies on every numeric test and sits in a
seventh category, total world, that this frame does not contain. Nothing at or below 0.10%
exists outside the audited funds in **emerging markets or total international** — the next
cheapest emerging fund is EMXC at 0.25%. **S&P 500 was complete until 2026-08-05**, when
DLCU began trading at 0.06% net — dearer than SPLG's 0.02% and VOO's and IVV's 0.03%, so it
changes the category's shape rather than its winner. Sweeping every Form 8-A12B filed by
the plausible low-cost issuers over 2024-01-01…2026-08-17 turns up **no new launch above
$2bn at or below 0.10%** in any of the six categories.

---

## 7. Smaller levers, sized so they can be dismissed with a number

**Account type is mostly a forecast, not a structure.** Traditional and Roth are
algebraically identical whenever the contribution and withdrawal rates are equal, so the
entire difference is the rate change — a saver falling from 32% to 22% gains exactly
14.71% of terminal wealth. What *is* structural, from the same algebra: **a tax-deferred
balance is not the investor's money** — at a 24% withdrawal rate, $100,000 of traditional
IRA is $76,000 of investor wealth, so an allocation stated on nominal balances misstates
true equity exposure. §1's ranking is per dollar of *capacity* precisely to sidestep that.
**[§8.5a](#85a-where-the-wrapper-goes-inside-the-shelter) prices the choice between the two shelters** — about 2 bp/yr at
stated inputs, against 21 to 38 for the taxable-versus-sheltered decision — and names the
one part of it that is not a forecast.

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

## 8. The investor's plan: eight funds, three accounts, and a ranking that does not move

**Scope.** One stated investor, `as of 2026-08-22`: roughly equal nominal thirds of Roth,
traditional and taxable; long horizon; no near-term withdrawal need; US-based. Holdings
**US 65%** — 30% in a stacked US-equity-plus-managed-futures ETF, 20% VTI, 15% AVLV — and
**international 35%** — 10% DFIV, 10% VEA, 5% IDMO, 5% IEMG, 5% AVES. **No bonds**, which
removes the one placement decision every source agrees on and makes the foreign-withholding
and wrapper lines binding. **The tax-deferred third is a mix of a rollover IRA and an employer plan**, and that menu
constraint turns out to bind harder than anything in the tax code — see
[§8.5](#85-the-plan-and-the-employer-plans-menu). Contributions run **5–15%/yr** of the
portfolio. Everything below regenerates from
[`studies/investor_placement.py`](../../research/src/portfolio_edge/studies/investor_placement.py)
and is pinned in `research/tests/unit/test_studies_investor_placement.py`. **Not
personalised advice**; every figure is a function of stated inputs a different investor
should restate.

### 8.1 The bracket is not selected, and one column is unreachable

Rev. Proc. 2025-32 §3.03 puts the 2026 20% long-term rate above **$613,700** of taxable
income filing jointly and **$545,500** filing single, while the §1411 threshold is an
unindexed **$250,000 / $200,000** of modified AGI. **A taxpayer at the 20% rate is
therefore always past the surtax**, so 20% without 3.8% is not a live combination and does
not appear below. The three columns that are live are **23.8% / 40.8%**, **18.8% / 35.8%**
and **15% / 24%** qualified/ordinary. State income tax is excluded and additive; it
compresses every gap below without reordering them.

### 8.2 The inputs, from the funds' own filings

Each yield is the fund's whole annual taxable distribution as a fraction of net assets —
Form 1099-DIV Box 1a **grossed up for the creditable foreign tax** the §853 election makes
the shareholder report, plus Box 2a where a fund distributes long-term gain. Only IDMO has a
non-zero Box 2a. Splitting each yield into what is taxed at the capital-gain rate and what
is taxed at the ordinary rate is the whole of the fund-level correction.

| Fund | Weight | Fee | Taxable distribution | At capital-gain rates | Creditable foreign tax | Filing |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| **RSST** *(recognised)* | 30% | 99 bp | **9.273%** | 10.5% | 0 | Tidal Trust II N-CSR, FYE 2026-01-31 |
| **RSST** *(distributed)* | 30% | 99 bp | 1.285% | 85.7% | 0 | the same filing |
| **VTI** | 20% | 3 bp | 1.067% | 100% *(assumed)* | 0 | Vanguard fund-yield endpoint, 2026-07-31 |
| **AVLV** | 15% | 15 bp | 1.770% | 100% *(assumed)* | 0 | American Century ETF Trust N-CSR, FYE 2025-08-31 |
| **DFIV** | 10% | 27 bp | 4.033% | **100%** *(filed)* | 0.323% | Dimensional ETF Trust N-CSR, FYE 2025-10-31 |
| **VEA** | 10% | 3 bp | 2.387% | **66.3%** *(filed)* | 0.145% | Vanguard 2025 FTC worksheet |
| **IDMO** | 5% | 25 bp | **4.403%** | **25.6%** | 0.123% | Invesco ETF Trust II N-CSR, FYE 2025-10-31 |
| **IEMG** | 5% | 9 bp | 2.545% | **34.8%** *(filed)* | 0.245% | iShares 2025 QDI and distribution summaries |
| **AVES** | 5% | 36 bp | 3.910% | **44.5%** *(filed)* | 0.460% | Avantis 2025 tax centre and ICI file |

Two rows need their own sentence.

**IDMO is not a 2.3%-yield momentum fund for tax purposes.** Its N-CSR designates **25%**
qualified dividend income against **105% portfolio turnover**; it carried **$32,959,121 of
undistributed ordinary income and $11,582,181 of undistributed long-term gain** on
$2,081,578,000 of net assets at 2025-10-31, and paid them out on **2025-12-22 as $0.68417
of short-term and $0.27579 of long-term gain per share**. Adding those to the dividend
takes its taxable distribution to **4.40% of net assets with only 25.6% at capital-gain
rates** — the heaviest tax bill per dollar of any long-only fund in the portfolio. **The in-kind
redemption shield in [§2](#2-fund-structure--the-one-large-additive-line) does not survive
105% turnover**, and the five zero-capital-gain fiscal years in its Financial Highlights
are a fiscal-calendar artifact: the December distribution falls in the next fiscal year.

**AVES and IEMG are the emerging pair, and their filed qualified fractions are what reverse
[§1](#1-foreign-tax-credit-forfeiture--the-result-that-changes-an-allocation).** 44.5% and
34.8%, against the 100% §1's sleeve table assumes.

### 8.3 The wrapper is the largest line, and its size turns on one unsettled fact

The stacked fund routes its managed-futures leg through a **wholly-owned Cayman subsidiary
capped at 25% of total assets at each quarter-end**. That is not a §1256 story and must not
be told as one: §1256 is statutory and reaches all three candidate wrappers identically —
**RSST's 2026-04-27 summary prospectus contains the string `1256` zero times** and MATE's
prospectus quotes the rule verbatim, so what distinguishes MATE is *disclosure*, not
treatment. The mechanism that bites is the controlled foreign corporation, and the trust
says so itself:

> "As wholly-owned controlled foreign corporations, the Subsidiaries' net income and
> capital gains, if any, **will be included each year in the Funds' investment company
> taxable income**."

J.P. Morgan's SAI states the two consequences: subpart F income *"is generally treated as
ordinary income, regardless of the character of the Subsidiary's underlying income"*, and a
subsidiary's loss *"cannot be carried forward"*. **So the wrapper converts return into
currently-recognised ordinary income, and the conversion is asymmetric** — gains are
recognised, losses are trapped inside the CFC.

**The audited numbers show that conversion accumulating.** RSST's undistributed ordinary
income on a tax basis went from **$3,964,528 at 2025-01-31 to $29,468,239 at 2026-01-31**,
against net assets of $282,674,000 and $344,251,000 — **from 1.40% to 8.56% of net assets in
one year**, while the fund distributed $915,484 of ordinary income. About **8.43% of mean
net assets was recognised and not paid out**. Per share, the fund has distributed $0.53
since its 2023-09-05 inception and is carrying roughly **$2.53 a share of queued ordinary
income**, nearly five times everything it has ever paid.

| Reading | What it counts | Drag at 23.8% / 40.8% |
| --- | --- | ---: |
| **Distributed** | the $0.32 a share shareholders were actually taxed on, 74.3% long-term | **33.7 bp/yr** |
| **Recognised** | the 9.27% of net assets the fund recognised, 89.5% ordinary | **361.8 bp/yr** |

The distributed reading is corroborated independently: the fund's own prospectus reports
**17.17% a year before tax against 16.85% after taxes on distributions** since inception —
a 32 bp/yr gap. **The recognised reading is ten times larger, and the difference is a queue
that has been audited but not yet distributed.** The same N-CSR reserves the right to
*"retain income or capital gains and pay excise tax"*, so whether and when it is paid out is
**not settled here**, and FY2026 was a 19.94% total-return year that will not repeat
annually. **The review trigger is the fund's next December distribution.**

**What is settled either way: the wrapper does not belong in the taxable account.** It is
first in the queue on the recognised reading by a factor of two and a half over anything
else, and still ahead of only VTI on the distributed one — but on the distributed reading
it is the *marginal* holding, so 13.3% of the portfolio spills into taxable. The two
readings therefore disagree about the *plan*, not about the direction.

### 8.4 The ranking, at three brackets

`priority = (recurring tax if held in taxable) − (irrecoverable withholding if sheltered)`,
in bp/yr per dollar of shelter capacity. Wrapper on the recognised basis.

| Fund | 23.8% | 18.8% | 15% |
| --- | ---: | ---: | ---: |
| **RSST** | **361.78** | **315.42** | **213.79** |
| **IDMO** | **148.22** | **126.20** | **83.25** |
| **AVES** | 83.98 | 64.43 | 32.21 |
| **IEMG** | 64.27 | 51.55 | 28.60 |
| **DFIV** | 63.73 | 43.56 | 28.23 |
| **VEA** | 56.01 | 44.07 | 28.56 |
| **AVLV** | 42.13 | 33.28 | 26.55 |
| **VTI** | **25.39** | **20.06** | **16.00** |

Four results, none of which is the maxim.

1. **VTI is last at every rate.** The cheapest, broadest, lowest-turnover fund in the
   portfolio is the one that belongs in the taxable account, because its 1.07% fully
   qualified yield is the smallest tax bill per dollar of shelter it would consume.
2. **Every international fund outranks every US equity fund at every rate.** "Hold
   international in taxable to capture the credit" is wrong here at all three brackets, and
   the credit is not close to deciding it: sheltering the whole 35% international sleeve
   destroys **8.81 bp/yr** of credit permanently and buys far more than that back.
3. **IDMO is second, and it is 5% of the portfolio.** A momentum fund at 25% qualified and
   105% turnover carries more tax per dollar than a 4.0%-yield emerging value fund. Nothing
   about its size or its label suggests it should be a placement priority.
4. **The order barely moves across the bracket range.** Only IEMG, DFIV and VEA change
   places with each other, and they are within 0.4 bp of one another at 15%.

### 8.5 The plan, and the employer plan's menu

Shelter capacity is **66.7%** of the portfolio — but not all of it is usable capacity. **The
tax-deferred third is a mix of a rollover IRA and an employer 401(k)/403(b)**, and an
employer plan has a fixed lineup: a broad US index fund, a developed ex-US one, an emerging
one, and nothing else this portfolio holds. **No employer plan offers a return-stacked ETF,
a Dimensional or Avantis systematic fund, or a single-factor momentum ETF.** Write `f` for
the share of the tax-deferred third that sits in the rollover IRA. `f` **has not been
measured**, so everything below is reported across its range.

Three claims on the same capacity, resolved in this order: the employer plan **must** be
filled and can only be filled from `{VTI, VEA, IEMG}`; the wrapper takes open-menu capacity
next ([§8.6](#86-what-the-plan-is-worth-under-four-rules-that-bound-it) shows why that
survives the wrapper's unresolved input); everything else fills the remainder by priority.

| | `f = 0` *(all employer plan)* | `f = 0.5` | `f = 1` *(all rollover)* |
| --- | --- | --- | --- |
| **Employer plan** | VTI 18.3, VEA 10, IEMG 5 | VEA 10, IEMG 5, VTI 1.7 | — |
| **Rollover IRA** | — | wrapper 16.7 | wrapper 30, IDMO 3.3 |
| **Roth** | **wrapper 30**, IDMO 3.3 | wrapper 13.3, IDMO 5, AVES 5, DFIV 10 | IDMO 1.7, AVES 5, IEMG 5, DFIV 10, VEA 10, AVLV 1.7 |
| **Taxable** | **AVLV 15, DFIV 10, AVES 5**, IDMO 1.7, VTI 1.7 | **AVLV 15, VTI 18.3** | **VTI 20, AVLV 13.3** |

**The menu binds below `f = 0.55`, and the threshold is derived rather than asserted.** The
unconstrained plan already shelters VEA and IEMG — 15% of the portfolio — so while the
employer plan is no larger than that it can be filled with exactly those two and costs
nothing. `1 − 0.15/0.333 = 0.55`. Above it the constraint is free; below it every extra point
of employer plan forces one more point of a low-priority index fund into the shelter and
evicts a high-priority fund from it.

**At `f = 0` the two highest-yielding funds in the portfolio are evicted.** DFIV (4.03%
yield, 100% qualified) and AVES (3.91%, 44.5% qualified) go to the taxable account while
**VTI — last in the queue at every rate — is forced into the shelter at 18.3%**. That is the
exact inverse of §8.4's ranking, imposed by a fund menu rather than by any tax fact. Against
the same plan at `f = 1` it costs **9.09 bp/yr at 23.8%, 6.56 at 18.8% and 3.33 at 15%** —
and **identically on both readings of the wrapper**, because the wrapper is sheltered either
way and what the menu reorders is the equity queue behind it.

**The wrapper never has to leave the shelter, at any `f`** — the Roth alone is 33.3% against
its 30%. But the margin is **3.3 points**, so this is a coincidence of the stated weights
rather than a structural fact: a wrapper allocation above 33.3% would spill into the taxable
account at `f = 0`, and at that point the wrapper weight itself is the thing to reconsider,
not the placement.

The split of IDMO and AVLV across two accounts is an artifact of exact thirds, not a
recommendation to hold one fund in two places; round it whichever way is operationally
simpler, because the funds either side of each boundary differ by a few basis points. A
joint solution with the rebalancing work puts taxable at **VTI 19.00, AVLV 14.00, VEA 0.33**
at `f = 1`, which costs **0.28 bp/yr** and buys a 1 pp headroom band; that is a better
rounding than this one and the two models reproduce each other's per-fund priorities to
within 0.01 bp.

### 8.5a Where the wrapper goes inside the shelter

**The wrapper goes in the tax-deferred account when `f` allows it and the Roth when it does
not, and the usual reason given for that is wrong.** The argument that "the traditional
converts everything to ordinary income anyway, so the wrapper's conversion costs nothing
there" is true and is **not a discriminator**: the recurring cost of a shelter is the
forfeited foreign credit and nothing else, and for the wrapper that is zero in a Roth too.
What decides it is three things that are not the drag:

- **The Roth's premium is proportional to expected return**, and the managed-futures leg is
  the least-established expected return in the portfolio — no measured loading, no measured
  alpha, not promoted ([decision 0004](../decisions/0004-no-sleeve-promoted.md)). Spending
  the best shelter on it is the wrong bet, and **at `f = 0` the investor has no choice but
  to make it**, which is a second and separate cost of a captive traditional account.
- **Required minimum distributions force the traditional and never the Roth.** The IRS
  states that *"withdrawals from Roth IRAs and Designated Roth accounts (401(k) or 403(b))
  are not required until after the death of the account owner"*, while a traditional balance
  must begin distributing at 73. The traditional is the right home for the sleeve the
  investor expects to be trimming; a trend overlay after a strong trend year is exactly that
  sleeve.
- **The traditional makes the government a partner in the outcome.** At a withdrawal rate
  `t` the investor bears `(1 − t)` of the sleeve's dispersion as well as its mean. Putting
  the most uncertain sleeve where that sharing happens is a risk decision and it points the
  same way.

**And the naive rule points the other way, which is why it has to be run rather than
recited.** "Shelter the highest drag" is a statement about *which shelter*, and it puts the
wrapper in the Roth. The drag is the wrong instrument for that question: it is identical in
both. The same confusion is available one level up —
[§3](#3-section-1256-and-capital-efficiency-handled-honestly) finds gold's overlay wrapper
carrying the heaviest distribution drag on the capital-efficient shelf while having the
weakest case for being held at all, so drag alone would buy it scarce shelter it has not
earned.

**Roth versus traditional is worth about 2 bp/yr, and it is a forecast.** Writing `R` and
`T` for the nominal balances, the difference between putting growth factor `A` in the Roth
and `B` in the traditional, and the reverse, is exactly `(R − T(1 − t))(A − B)`: the
after-tax size gap between the accounts times the growth gap between the sleeves. At equal
nominal thirds, a 24% withdrawal rate, 30 years, a 30% sleeve swapped and a 1 pp/yr
expected-return gap, that is **1.96 bp/yr** — an order of magnitude below the
taxable-versus-sheltered decision, and it needs two numbers nobody has. It is also not free:
holding the same after-tax allocation, the "gain" is more exposure, not more edge.

### 8.6 What the plan is worth, under four rules that bound it

A location number is easy to inflate and the four ways of doing it are all available here,
so the rules are stated before the figure rather than after it.

1. **The control has to be feasible.** Pro-rata placement of the same eight funds is *not*
   available to an investor whose shelter is partly a captive employer plan, because the
   wrapper and the systematic funds cannot go in there at all. Measuring against it compares
   the plan with something nobody could have done. The control used below is what a
   *default-choosing* investor with the same accounts would actually do: fill the employer
   plan with the biggest, most familiar index funds, then hold everything else pro rata.
2. **Income recognised inside a fund and not distributed is not a saving to anybody yet.**
   The wrapper's recognised basis rests on exactly that, so it is reported beside the booked
   figure and **never added to it**.
3. **A hurdle avoided is not a saving.**
   [§4](#4-deferred-unrealised-gain--the-largest-number-here) says in terms that deferral is
   *"a hurdle, not a saving"* and that crediting yourself for not doing something nobody
   proposed is how these budgets get inflated. Rebalancing inside the shelter is worth
   **zero** as a line, and is reported below as a hurdle not paid.
4. **Lot selection and never selling are mutually exclusive.** Lot-selection discipline pays
   only when you sell, and rule 3's whole content is that this investor does not sell in the
   taxable account. Booking both is booking one dollar twice, so **the lot-selection line is
   zero here**.

**Booked, against the feasible control, on the audited distributed basis**, in bp/yr of the
whole portfolio:

| Qualified rate | `f = 0` | `f = 0.5` | `f = 1` |
| --- | ---: | ---: | ---: |
| **23.8%** | **−2.04** | **+6.66** | **+5.41** |
| **18.8%** | −1.04 | +5.22 | +4.24 |
| **15%** | −0.40 | +2.56 | +2.04 |

**So the defensible booked figure is +2 to +7 bp/yr**, and at `f = 0` it is *negative*: with
a wholly captive tax-deferred third, forcing the wrapper into the Roth costs more on the
audited basis than the plan's fund ordering saves. The sign flips at **`f ≈ 0.02 to 0.05`**,
so any rollover balance worth more than a twentieth of the tax-deferred third is enough. The
`f = 0.5` column beats `f = 1` because the captive employer plan hurts the *naive* investor
more than it hurts a deliberate one — the gap widens before the constraint relaxes.

`location_edge()` **refuses to return a component when the value is negative**, and says so
in the exception. That guard is the finding made unpublishable-by-accident, in the same
spirit as `aggregate()`'s refusal to sum across benchmarks.

**Conditional and not booked**: if the wrapper's recognised income is distributed at the
rate it is being recognised, the plan gains a further **+19.3 to +49.2 bp/yr** depending on
`f` and bracket — largest at `f = 0`, because that is where the naive investor is worst
placed. **This page books none of it.** The review's charge was that the headline quoted it
without carrying its conditionality, and the charge is accepted.

**The unresolved accrual does not stall the decision, and this is why.** Ask not "how big is
it" but "does the decision need to know":

| At 23.8% | if the audited basis is right | if the accrual is distributed |
| --- | ---: | ---: |
| **Shelter the wrapper** | costs **1.12 bp/yr** (`f = 1`), **8.54** (`f = 0`) | — |
| **Follow the audited-basis ranking instead** | — | costs **42.62 bp/yr** (`f = 1`), **89.88** (`f = 0`) |

The asymmetry is **ten to one at every `f` and every bracket**, so **sheltering the wrapper
is right under either reading** and the measurement can stay unresolved without stalling the
plan. That is worth more than the drag it costs, and it is the reason the wrapper's queue is
an open question rather than a blocker.

**Rebalancing: a hurdle avoided, reported as a hurdle.** The entire international sleeve and
the entire trend overlay sit inside the shelter, so every trade on those two legs realises
nothing. **One direction is constrained** — selling US equity to buy international — because
at `f = 1` only 1.7% of AVLV sits in the shelter beside the wrapper. That needs roughly
**2 points of the portfolio a year**. **Contributions of 5–15%/yr cover it 2.5 to 7.5 times
over**, so the taxable account never has to sell and §4's deferral is never broken. That is
the hurdle not being paid; **it is not an edge and it is not booked**.

**Contributions: the dollar-limited accounts first, then taxable at whatever is furthest
below target.** 2026 limits, from IRS Notice 2025-67: §402(g) elective deferral **$24,500**,
age-50 catch-up **$8,000**, ages 60–63 **$11,250**, IRA **$7,500** with a **$1,100**
catch-up. **One constraint bites and it is easy to miss**: the Roth IRA contribution phases
out between **$242,000 and $252,000** of modified AGI filing jointly, and the §1411 surtax
starts at an unindexed **$250,000**. Any investor in the 18.8% or 23.8% column is at or past
the phase-out, so their Roth capacity comes from a designated Roth account in an employer
plan or from a conversion — **not from a direct contribution**, and a plan that assumes
otherwise will not execute. At 5–15%/yr of the portfolio the contribution stream is also
large enough to *migrate* the placement over a few years without realising anything, which
is the cheapest way to reach this plan from any starting point.

### 8.7 How much of the ~109 bp budget this investor can capture

**Every line below is against one named benchmark and lines against different benchmarks are
not added.** [`docs/charter.md`](../charter.md) forbids it outright and
[`aggregate()`](../../research/src/portfolio_edge/studies/outperformance_horizon.py) raises
on it; the earlier draft summed three.

**Benchmark: the investor's own counterfactual** — the same eight funds, placed the way a
default-choosing investor with the same accounts would place them.

| Line | bp/yr | Certainty class |
| --- | ---: | --- |
| **Asset location, eight funds, three accounts** | **+2.0 to +6.7** at `f ≥ 0.05`; **−0.4 to −2.0** at `f = 0` | **deterministic** — arithmetic on filed figures, given `f` |
| Roth versus traditional | +2.0 | **probabilistic** — needs a future marginal rate and a return gap |
| Lot selection | **0** | withdrawn: mutually exclusive with never selling |
| Rebalancing deferral | **0** | withdrawn: a hurdle avoided, not a saving (§4) |
| **Booked total, this benchmark** | **+2 to +7 deterministic, +2 probabilistic** | |
| *Conditional, not booked* | *+19 to +49 if the wrapper's accrual is distributed* | **unresolved** |

**Benchmark: a cheap index.** The fee gap and the fund-structure line live here. Neither is
sized for this investor — the fee gap depends on what these eight funds replaced, which was
not stated — and **neither may be added to the table above**. For the record on the second:
seven of the eight funds filed **zero** capital-gain distributions, so §2's +23 bp has
nothing to buy; **IDMO is the exception and it runs the wrong way**, at −3.9 bp/yr of the
portfolio if held in taxable and **zero under the plan**, which shelters it.

**Benchmark: typical investor behaviour.** Nothing here is measured against it.

**So the defensible answer is +2 to +7 bp/yr, not a third to a half of the ~109 bp budget.**
The budget's two largest lines are simply unavailable: the **23 bp fund-structure** line is
measured against an *active mutual fund* counterfactual this investor does not have, and the
**30 bp harvesting** line needs direct security ownership that funds do not give. **The good
news and the bad news are the same fact** — a portfolio already built from cheap ETFs has
little implementation edge left to collect, which is exactly what
[the recommendation](portfolio-recommendation.md#what-is-relatively-dependable) says about
an investor already holding cheap index funds. The conditional +19 to +49 is real and may
arrive; it is not a budget until the wrapper's next December distribution settles it.

### 8.8 What was assumed, and what would change the plan

**Assumed rather than filed**, each flagged in the module's own source field:

- **Qualified fractions of 1.00 for VTI and AVLV.** Both sponsors publish per-fund
  percentages and neither was retrieved. A *lower* fraction raises a fund's priority, so
  assuming 1.00 is the choice that most favours the taxable placement the plan gives them —
  conservative in the direction it is uncertain. The threshold is sharp and worth stating:
  **at 0.54, AVLV overtakes VEA** and the last international dollar leaves the shelter. Both
  are large, low-turnover, US-domiciled funds, so a fraction near 1.00 is likely; it is not
  verified.
- **The wrapper's queued ordinary income has no qualified designation.** Only the $404,096
  actually designated is credited at capital-gain rates. A larger designation would lower
  the 361.8 bp, not the ranking.
- **The wrapper is priced on RSST's filings.** MATE and JPFP are too new to have filed a
  tax-character table — MATE has one N-CSRS to 2026-02-28 and JPFP listed on 2026-05-27 —
  and all three run the same 25%-capped Cayman CFC. **The placement conclusion is identical
  for all three**, so the wrapper choice can be made on fee and structure without reopening
  this section.

- **The rollover share `f` of the tax-deferred third has not been measured**, and it is the
  input the plan is most sensitive to — it moves the booked line from −2.0 to +6.7 bp/yr and
  decides whether DFIV and AVES can be sheltered at all. **Ask for it before executing.** So
  has the employer plan's actual lineup: `{VTI, VEA, IEMG}` is a typical menu, not a filed
  one, and a plan offering a cheap international value or small-value fund would relax the
  constraint materially.
- **Contributions are 5–15%/yr of the portfolio.** The midpoint is used where a single value
  is needed; the range is what is reported. At every point in it, new money covers the one
  constrained rebalancing direction more than twice over, so no conclusion here turns on
  where in the range the investor sits.

**Yields mix windows**: two are sponsor forecasts effective 2026-07-31, three are audited
fiscal-year ratios ending in 2025, and none is point-in-time. A yield is the input a
location ranking is most sensitive to after `f`.

**Four review triggers.** The wrapper's next December distribution, which decides the
conditional +19-to-+49 line. IDMO's next fiscal year, which decides whether its capital-gain
flush is a feature of the mandate or one year. Any change in the investor's bracket that
crosses $250,000 of modified AGI, which moves two columns at once — the surtax and the Roth
IRA phase-out. And **any rollover into or out of the employer plan**, which moves `f` and is
the cheapest lever on this page: consolidating an old employer balance into the rollover IRA
buys the whole `f = 0` to `f = 0.5` improvement for the cost of a form.

---

## The ledger

| Lever | bp/yr, portfolio | Range | Additive to the 89 bp? |
| --- | ---: | --- | --- |
| **Fund structure: capital-gain distributions avoided** | **+23.0** | 0 to +50 | **ADDITIVE**, and **decaying** |
| **Specific identification of tax lots** | **+5.0** | 0 to +44 | **ADDITIVE** (residual only) |
| Foreign tax credit forfeited inside a shelter | **−3.4** | −6 to 0 | **correction** to the 10 bp location line |
| Direct-indexing fee, netted against harvesting | **−4.4** | −30 to +6 | **correction** to the 30 bp harvesting line |
| Securities lending, measured across 25 funds and 8 fiscal years (§6) | +0.83 | +0.45 to +2.60 | same 1 bp line, revised |
| Deferred unrealised gain | 84.1 | 0 to 162 | **No — a hurdle, not a saving** |
| Municipal bonds | 0.0 | 0 to +222 | inactive; the shelter covers the bonds |
| §1256 60/40 treatment | 0.0 | 0 to +51 | no futures sleeve; leverage is zero |
| Traditional vs Roth, and the HSA | 0.0 | — | **probabilistic**, or a dollar limit |
| Asset location at fund level, one stated investor (§8) | **+2 to +7** | −2.0 to +6.7 | **replaces** the 10 bp location line for that investor; measured against a *feasible* control |
| Same, conditional on the wrapper's accrual being distributed (§8.6) | *not booked* | +19 to +49 | **unresolved**; reported, never added |
| Rebalancing kept inside the shelter (§8.6) | **0.0** | — | **withdrawn** — a hurdle avoided is not a saving (§4) |
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
   exist and 89 Form 497K documents now name an "ETF Class", but no SEC document
   quantifies the benefit and the operative conditions live in each applicant's 40-APP
   application, which was not read.
4. **Whether a capital-efficient wrapper's queued ordinary income is distributed, and
   when.** RSST recognised about 8.4% of net assets of ordinary income in the year to
   2026-01-31 and paid out 0.3%, leaving 8.56% of net assets undistributed on a tax basis.
   That single input moves [§8](#8-the-investors-plan-eight-funds-three-accounts-and-a-ranking-that-does-not-move)'s
   placement value from 6.5 to 38 bp/yr. **The largest open input on this page**, and the
   one that replaced the withholding denominator, now closed in §1.
5. **The value of lot-selection discipline for a retail buy-and-hold investor.** The only
   measurement is a simulation on a turning-over separate account.
6. **Schwab's four funds' spreads and premium/discount**, and **BKAG's lending, waiver
   terms and whether its 0.00% fee is contractual** — the one unaudited candidate that
   could move §6.1's bond row (§6.6, §6.7). Schwab's site returns HTTP 403 site-wide,
   including `robots.txt`, and was not worked around.
7. **Non-US tax.** A jurisdiction with no foreign tax credit turns §1 into a pure cost; one
   taxing gains on accrual removes §4 entirely; one with no step-up removes half of it.
8. **State tax.** Excluded and additive.

**Reproducibility.** Rates, yields and profiles are arguments rather than constants, all
committed in `tax_structure.py` with the source beside each. Retrieval date **2026-08-12**
except: municipal and Treasury curves 2026-07-29, Treasury par cross-check 2026-08-11, BND
yield 2026-08-10, MSCI yields 2026-07-31, SEC order count 2026-08-11, and **everything in
§6 plus §1's withholding cross-check 2026-08-17**. §6 regenerates from
`portfolio_edge.studies.core_beta_shelf`; its 110 filings are hashed in
`data-manifests/core_beta_shelf/ncen_costs.json` and its figures pinned in
`tests/unit/test_studies_core_beta_shelf.py`. Sources that resisted retrieval are
registered in [the evidence base](evidence-base.md) §3.

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
4. **Asset location must be computed, not asserted, and at the fund rather than the
   sleeve.** The rule "shelter the higher-yielding asset" is right for bonds by a factor of
   four; on a generic sleeve it looked wrong for emerging-market equity at two US rates, and
   at fund level it is wrong in the other direction, because the sponsors file qualified
   fractions of 25% to 45%. **A location ranking that assumes a qualified fraction has
   assumed its own answer.** Any location feature runs the ranking, states the bracket, and
   states which withholding denominator it is on.
5. **Do not build a capital-efficiency feature, and do not close the question either.**
   §3's four conditions are what would reopen it.
6. **Recheck the fund-structure line before it is used.** A page whose largest new line has
   a visible mechanism of decay carries a review trigger, and this is it.
7. **A named fund's cost is `fee − lending`, never its fee**, and §6 is where that
   arithmetic lives for the core shelf. Any page naming a fund quotes both terms, states
   that the first is contractual and the second measured, and never ranks two funds on a
   tracking difference measured against two different indices.
8. **Form N-CEN is now a held source** and it is the only structured one for fund costs:
   `portfolio_edge.data.ncen` reads Items C.3.b, C.6 and C.8 per series per fiscal year.
   Item C.8 is the only place a *recoupable* waiver is disclosed in a machine-readable
   field, and on this shelf it disagrees with the prospectus for two funds.
