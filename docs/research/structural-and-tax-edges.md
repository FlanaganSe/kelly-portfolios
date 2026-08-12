# Structural and tax-aware edges: what else is contractual, and how big is it

**Question.** The [edge decomposition](expected-edge-decomposition.md) prices a
*contractual* edge of about 89 bp/yr against the investor's own plausible alternative —
49 bp of fund cost, 30 bp of tax-loss harvesting, 10 bp of asset location — and reaches
99% confidence in fourteen months precisely because none of it depends on a forecast.
What else belongs in that class, how large is it, and does it double-count what is
already booked?

**Decision informed.** Whether the contractual budget should be revised, and in which
direction. Also which account a real investor's international sleeve belongs in, because
the foreign tax credit bears directly on that and the standard advice is stated as a
universal rule when it is not.

**Scope.** US federal individual investor, `as of 2026-08-12`. State income tax is
excluded and additive wherever it exists. **This is not personalised advice**; it is a
sizing exercise for a class of edge, and every figure is a function of stated inputs that
a different investor should restate. Non-US investors differ on every line, most sharply
on §1 — a jurisdiction with no credit mechanism converts a location question into a pure
cost.

**Conclusion, stated directly.**

1. **The contractual class is bigger than the budget records, but by 20 bp rather than the
   30–50 bp that would change the project's conclusion.** One genuinely additive line
   dominates: the capital-gain distributions an active mutual fund makes and an ETF does
   not, worth **23 bp/yr** on the reference portfolio. A second, lot-selection discipline,
   is worth about **5 bp**. Two corrections run the other way — the foreign tax credit
   forfeited inside a shelter (**−3.4 bp**) and the direct-indexing fee the harvesting line
   never subtracted (**−4.4 bp**). Net, the own-counterfactual budget moves from
   **89 bp/yr to about 109 bp/yr**, and the time to 99% confidence falls from about
   fourteen months to about **twelve**. The shape of the finding does not change; its
   magnitude improves by roughly a fifth.
2. **The largest number found is not a saving at all — it is a hurdle.** Deferral of
   unrealised gain is worth **84 bp/yr** at a thirty-year horizon and the §1014 step-up a
   further **78 bp**, summing to a horizon-free **162 bp/yr**. That is the price of
   turnover in a taxable account, and it is nearly as large as the entire budget. It is
   deliberately **not booked**, because crediting yourself for not doing something nobody
   proposed is how these budgets get inflated. It belongs in the record as the hurdle every
   future turnover-bearing sleeve must clear.
3. **The foreign tax credit inverts standard asset-location advice for exactly one sleeve,
   at exactly two brackets.** Withholding is irrecoverable inside a traditional account and
   a Roth alike, costing **15.8 bp/yr** on a developed sleeve and **20.0 bp** on emerging.
   The break-even qualified-dividend rate is 10.5% for developed markets — below every
   positive US rate, so the conventional rule survives — but **21.5% for emerging markets**,
   which falls *between* the 18.8% and 23.8% brackets. **A US investor paying 15% or 18.8%
   should hold emerging-market equity in the taxable account and US equity in the shelter.**
   At 23.8% the conventional order returns, by 2.1 bp, which is a tie.
4. **Capital efficiency is the most substantive structural candidate on the page and the
   only one whose sign this repository cannot check.** A 90/60 return-stacked fund needs
   **92 bp/yr** of Treasury excess return over cash before its overlay contributes
   anything, against a measured futures funding basis of 58.70 bp/yr that has been positive
   in all 28 years measured. Both inputs are forecasts, so it is probabilistic by
   construction and cannot enter a contractual budget. Decision 0004's reasoning does not
   quite forbid it, but the edge decomposition's exclusion of the term premium as a
   benchmark switch does.
5. **The largest additive line is decaying while being measured.** As of 2026-08-11 the SEC
   has granted **94 orders** letting mutual funds add ETF share classes, covering roughly
   ninety fund families. If they are adopted broadly, the 23 bp in item 1 goes towards zero.
   This page should be rechecked before any decision leans on that line.

Everything numerical here regenerates from
[`research/src/portfolio_edge/studies/tax_structure.py`](../../research/src/portfolio_edge/studies/tax_structure.py)
and is pinned in `research/tests/unit/test_studies_tax_structure.py`. No market data, no
randomness, no forecast.

---

## 1. Foreign tax credit forfeiture — the answer that changes an allocation

**Mechanism, and it is a statutory chain rather than a published rule.** A foreign
government withholds tax at source on dividends paid by its companies. A US fund pays it,
and under [26 U.S.C. §853](https://www.law.cornell.edu/uscode/text/26/853) may elect to
pass it through: *"each shareholder of such investment company shall — (A) **include in
gross income** and treat as paid by him his proportionate share of such taxes"*. The
shareholder then credits it under
[§901(a)](https://www.law.cornell.edu/uscode/text/26/901), which credits it against *"the
tax imposed by this chapter"*, subject to the
[§904(a)](https://www.law.cornell.edu/uscode/text/26/904) limitation that the credit
*"shall not exceed the same proportion of the tax against which such credit is taken"* as
foreign-source income bears to total income.

An IRA is *"exempt from taxation under this subtitle"*
([§408(e)(1)](https://www.law.cornell.edu/uscode/text/26/408)). It has no tax to credit
against, no gross income to include the pass-through in, and a §904 numerator of zero.
**The withholding is therefore paid and permanently lost, identically in a traditional
account and a Roth.** No IRS publication states this in terms — Publication 514 and the
Form 1116 instructions do not mention IRAs at all — so the claim should be asserted from
the statute, not from commentary.

The treaty route does not rescue it. Both the
[US–Japan](https://home.treasury.gov/system/files/131/Treaty-Japan-11-6-2003.pdf) and
[US–UK](https://home.treasury.gov/system/files/131/Treaty-UK-7-24-2001.pdf) conventions
exempt a resident *pension fund* from dividend withholding — US–UK Art. 10(3): dividends
*"shall not be taxed"* where the beneficial owner is *"a pension scheme"* — but Art. 10(4)
of each then disapplies the exemption for *"a pooled investment vehicle"* and for
RIC/REIT dividends. The beneficial owner of the shares in VEA is the fund, not the IRA, so
the pension rate is unreachable through an index fund by construction.

**Size, computed from fund filings.** Vanguard's
[2025 foreign tax credit worksheet](https://investor.vanguard.com/content/dam/retail/us/en/pdfs/taxes/ftcws-012026.pdf)
(FTCWS 012026) states foreign tax paid as a percentage of ordinary cash dividends: **VEA
6.46%, VXUS 7.11%, VWO 10.93%**. Converting to the grossed-up Box 1a basis the shareholder
reports gives 6.068% and 9.853%. Applying MSCI's index dividend yields at 2026-07-31 —
[EAFE 2.60%](https://www.msci.com/documents/10199/822e3d18-16fb-4d23-9295-11bc9e07b8ba),
[Emerging Markets 2.03%](https://www.msci.com/documents/10199/255599/msci-emerging-markets-index-usd-net.pdf):

| Sleeve | Gross yield | Effective withholding | **Forfeited inside any shelter** |
| --- | ---: | ---: | ---: |
| Developed ex-US equity | 2.60% | 6.07% | **15.78 bp/yr** |
| Emerging-market equity | 2.03% | 9.85% | **20.00 bp/yr** |
| 70/30 blend | | | **17.04 bp/yr** on the sleeve |
| Same, at 30% of a total-equity portfolio | | | **5.11 bp/yr** |

Emerging markets forfeits *more* while yielding *less*, because its withholding rate is
62% higher. The two sleeves cannot be treated as one "international" line.
[iShares' 2025 tax supplement](https://www.ishares.com/us/literature/tax-information/2025-ishares-distribution-summary-stamped.pdf)
cross-validates the method from a different sponsor and a per-share basis: IEFA reports
$0.164816 of foreign tax against $3.341921 of Box 1a dividends, and
$3.341921 − $3.177092 = $0.164829 confirms that Box 1a is the §853 gross-up.

**The decision this actually settles, and it is not the one usually stated.** The
conventional advice — "hold international in taxable to capture the credit" — compares
the wrong pair. The right metric for shelter capacity is what a sheltered dollar *saves*:

```
priority = (recurring tax if held in taxable) − (irrecoverable withholding if sheltered)
```

For every asset except a foreign one the second term is zero and the rule collapses to
the familiar one. At the top bracket (23.8% qualified, 40.8% ordinary), with
[BND's SEC 30-day yield of 4.65% at 2026-08-10](https://investor.vanguard.com/investment-products/etfs/profile/api/0584/yields)
and a US equity yield of 1.10%:

| Asset | Taxable cost | Sheltered cost | **Priority for shelter** |
| --- | ---: | ---: | ---: |
| Taxable investment-grade bonds | 189.7 bp | 0 | **189.7 bp** |
| Developed ex-US equity | 61.9 bp | 15.8 bp | **46.1 bp** |
| Emerging-market equity | 48.3 bp | 20.0 bp | **28.3 bp** |
| US equity | 26.2 bp | 0 | **26.2 bp** |

Bonds dominate by a factor of four, so the uncontested half of the conventional rule is
uncontested here too. The contested half moves:

- **At 23.8%, the credit does not reverse the ranking but it erases the margin.**
  Emerging-market equity's advantage over US equity for shelter space falls from 22.1 bp
  to **2.1 bp** — well inside the uncertainty in either dividend yield. Treat it as a tie.
- **At 15% or 18.8%, the ranking inverts.** Emerging-market equity drops to 10.5 bp of
  priority against US equity's 16.5 bp. **A US investor in the 15% bracket should hold
  emerging-market equity in the taxable account and US equity in the shelter**, which is
  the opposite of the standard rule.
- **Developed markets never inverts.** Its break-even qualified-dividend rate is 10.52%,
  below every positive rate in the US schedule.

The break-even is closed form: `q* = u w y_i / (y_i − y_d)`, giving **10.52% for developed
markets and 21.51% for emerging markets**. The US schedule offers only 0%, 15%, 18.8% and
23.8%, so the developed break-even falls in the gap below every positive rate and the
emerging one falls *between* two live rates. That is why one sleeve inverts and the other
does not, and it is a fact about the bracket schedule rather than about the funds.

**The 0% bracket is the trap.** It looks like the strongest case for holding international
in taxable, and it is worth exactly nothing: §904 limits the credit to the US tax on
foreign-source income, and there is none. Such an investor forfeits the withholding in
*both* locations, so the credit is not an argument for either.

**Where the credit stops being fully usable.** Below **$300 of creditable foreign tax
($600 joint)** the credit is claimed on Schedule 3 without Form 1116 and without the §904
limitation — the
[Form 1116 (2025) instructions](https://www.irs.gov/instructions/i1116) condition it on
*"Your total creditable foreign taxes aren't more than $300 ($600 if married filing a
joint return)"*, all foreign income being passive and reported on a qualified payee
statement. At the developed-market sleeve's rate that threshold is reached at **$190,153
of holdings ($380,305 joint)**. Neither figure is indexed, so the fraction of investors
pushed onto Form 1116 rises mechanically every year. Two further conditions that are
usually dropped: unused credit carries back one year and forward ten under §904(c) and is
**not refundable**, and no carryover is available in any year the $300/$600 election is
used; and §901(k)(1)(A) disallows the credit entirely on a dividend where the stock was
*"held by the recipient of the dividend for 15 days or less during the 31-day period
beginning on the date which is 15 days before the date on which such share becomes
ex-dividend"*.

**Double count: this is not additive.** It is a **correction to the 10 bp asset-location
line already in the budget**, which is sourced to work
([Shoven–Sialm](https://doi.org/10.1016/S0047-2727(02)00138-X),
[Dammon–Spatt–Zhang](https://doi.org/10.1111/j.1540-6261.2004.00655.x)) that does not
model foreign withholding at all. Booking it as a new positive line would be a double
count in the most direct sense: it is the same dollars, with the sign reversed.

**Falsifier.** A fund's published foreign-tax-paid ratio falling to zero (widespread
relief at source rather than reclaim), or a treaty or domestic rule extending the pension
exemption to pooled vehicles, or a US rate schedule with a positive qualified-dividend
rate below 10.5%.

**Two things this comparison leaves out**, both cutting against the emerging-market
inversion: a sheltered account also shelters *capital-gain* distributions and any
rebalancing turnover, which emerging-market funds generate more of; and a taxable
international position is a better tax-loss-harvesting candidate because it is more
volatile. Neither is quantified here, and either could close a 6 bp gap.

---

## 2. Fund structure — the one large additive line

**Mechanism, one sentence of statute.**
[26 U.S.C. §852(b)(6)](https://www.law.cornell.edu/uscode/text/26/852): *"Section 311(b)
shall not apply to any distribution by a regulated investment company to which this part
applies, if such distribution is in redemption of its stock upon the demand of the
shareholder."* §311(b) is the general rule forcing a corporation to recognise gain when
it distributes appreciated property. An ETF hands appreciated shares to an authorised
participant and recognises nothing; an equivalent mutual fund sells, recognises, and —
under §852(a)(1)'s 90% distribution requirement and the 98%/98.2% thresholds of
[§4982](https://www.law.cornell.edu/uscode/text/26/4982) — must distribute the gain.

[SEC Rule 6c-11](https://www.sec.gov/rules/final/2019/33-10695.pdf) (Release 33-10695,
adopted 2019-09-25, effective 2019-12-23) is what turned that shield into a tool. It let
ETFs use **custom baskets** under written policies rather than bespoke exemptive orders,
subject to *"detailed parameters for the construction and acceptance of custom baskets
that are in the best interest of the ETF and its shareholders"*. Custom baskets are how a
manager selects the lowest-basis lots for an in-kind redemption. The release's own
footnote 281 is explicit: *"In-kind redemptions allow ETFs to avoid taxable events."*

**Size, from actual filings.** Read from N-CSR Financial Highlights, "Distributions from
Realized Capital Gains" as a percentage of beginning NAV:

| Fund | 10-year average distribution | Note |
| --- | ---: | --- |
| VOO, VFIAX, VTI, VTSAX | **0.00%** | Nil in all 44 fund-years, 2015–2025 |
| AGTHX (American Funds Growth Fund of America) | **6.62%** | Distributed in FY2022 while returning −23.78% |
| FCNTX (Fidelity Contrafund) | **7.01%** | Distributed 7.25% of NAV in 2022 while returning −28.26% |

Frequency, from Morningstar's annual survey via
[SSGA](https://www.ssga.com/us/en/individual/insights/tax-efficiency-is-structural-etfs-continue-to-issue-fewer-capital-gains-than-mutual-funds)
(data to 2025-12-31): *"Only 7% of ETFs paid a capital gain in 2025, compared with 52% of
mutual funds"*, with a since-2016 average of 9% against 53%.
[Morningstar's own 2025 survey](https://www.morningstar.com/funds/few-etfs-project-capital-gains-distributions-2025-key-takeaways-investors)
of ~1,600 ETFs: *"Only 6% of the ETFs surveyed estimated a capital gains distribution,
and only 2% estimated a distribution greater than 1% of their NAV."*

**The tax cost of a distribution is far below its headline tax**, because the distribution
raises the shareholder's basis. At the top rate, 7% growth, 30 years, liquidating at the
end:

| Distribution, % of NAV | Headline tax | **Actual annualised drag** | Drag if held to a step-up |
| ---: | ---: | ---: | ---: |
| 2% | 47.6 bp | **25.7 bp** | 47.7 bp |
| 3% | 71.4 bp | **38.3 bp** | 71.7 bp |
| 5% | 119.0 bp | **63.0 bp** | 119.7 bp |
| 6.6% | 157.1 bp | **82.2 bp** | 158.3 bp |

Quoting the headline overstates it roughly twofold for a liquidating investor; quoting the
step-up column as though it applied to one is the same error in reverse.

**Cross-check against the peer-reviewed measurement.** Moussawi, Shen and Velthuis, *"The
Role of Taxes in the Rise of ETFs"*, *Review of Financial Studies* 38(10) (2025) —
published text unreachable; figures from the
[Sept 2022 working paper](https://corpgov.law.harvard.edu/2025/05/22/the-role-of-taxes-in-the-rise-of-etfs/)
and the Harvard Law School Forum summary of the published version — measure the ETF
advantage over active mutual funds at **1.05%/yr since 2012** (0.92%/yr in the working
paper; cite the version you use). Their tax-burden table is the more useful number
because it isolates the wrapper: **ETFs 0.39%, Vanguard index funds 0.41%, non-Vanguard
index funds 1.07%**, and 0.43% for the *same* S&P 500 portfolio in two wrappers.
*"confirming that ETF tax efficiency is not an indexing phenomenon"*.

**The correction that must not be dropped.**
[Poterba and Shoven (2002)](https://www.nber.org/papers/w8781), *AER* 92(2), found *"the
before- and after-tax returns on the SPDR trust and this mutual fund were very
similar. Both the after-tax and the pre-tax returns on the fund were slightly greater than
those on the ETF"* over 1994–2000. **The ETF advantage is against *active* funds and
against *non-Vanguard index* funds, not against a low-turnover index mutual fund.** Anyone
stating "ETFs beat mutual funds on tax" without that qualifier is wrong on the case that
matters most to this repository, since the control is a cheap broad index fund either way.

**Booked at 23 bp**: 38.3 bp on the taxable equity sleeve at a 3%-of-NAV counterfactual
distribution, times the 60% of the reference portfolio that sleeve occupies. Range 0 to
49 bp, the top being the AGTHX/FCNTX rate. The 3% central sits below the two largest
active funds because they are the highest-turnover end of the shelf, and above zero
because 52% of mutual funds distributed something in 2025.

**Double count: ADDITIVE.** The 49 bp fund-cost line is an expense-ratio gap and contains
no tax at all. It does not overlap tax-loss harvesting either: that is the *investor*
realising losses, this is the *fund* realising gains.

**Falsifier, and it is already firing — this is the most time-sensitive claim on the
page.** The SEC granted its first order permitting a mutual fund to add an ETF share class
on **2025-11-17** ([Release IC-35786](https://www.sec.gov/files/rules/ic/2025/ic-35786.pdf),
Dimensional), *"effective immediately"*. It then cleared the backlog in four batches, and
its own
[Multi-Class ETF notices-and-orders listing](https://www.sec.gov/rules-regulations/investment-company-act-notices-orders?category=350341)
shows **94 granted orders as of 2026-08-11**, covering roughly ninety distinct fund
families — Fidelity, BlackRock, State Street, Schwab, T. Rowe Price, J.P. Morgan, PIMCO,
Franklin Templeton, Invesco and most of the rest of the shelf. Only two applications
remain noticed and unordered, and the run rate has fallen to single digits a month, so
this is now routine processing rather than an open policy question. All three exchanges
adopted generic listing standards for the new share class on 2025-11-28. Vanguard, whose
own relief predates all of it and was expressly preserved by the 6c-11 release, is the
proof of concept: **VFIAX and VTSAX show zero capital gains for a decade precisely because
they share a portfolio with VOO and VTI.**

**So the 23 bp booked below is a decaying quantity with a visible mechanism of decay**, and
it must be re-checked before any decision leans on it. The opposite risk also exists: the
2021 [Senate Finance discussion draft](https://www.finance.senate.gov/imo/media/doc/Wyden%20Pass-through%20Reform%20Section%20by%20Section.pdf)
proposed to *"repeal the exception for RICs"* outright, effective for years after 2022. It
was never enacted and no successor bill was found, but Treasury and IRS officials
discussed §852(b)(6) boundary cases publicly in July 2026. *(Retrieval note: no SEC
document quantifies the tax benefit of a multi-class structure, and none states how
in-kind ETF-class redemptions interact with the mutual-fund class's gains. The operative
conditions live in each applicant's own 40-APP application, which was not read.)*

---

## 3. Section 1256, and capital efficiency handled honestly

**Mechanism.** [§1256(a)](https://www.law.cornell.edu/uscode/text/26/1256) marks a
regulated futures contract to market at year end and splits the resulting gain 60%
long-term / 40% short-term *"without regard to the period for which the taxpayer has held
such contract"*. At 2026 top rates the blend is
`0.6 × 23.8% + 0.4 × 40.8% = 30.6%`.

**Both halves, priced.**

- **Against ordinary annual treatment** — the true counterfactual for a managed-futures
  programme whose positions turn over in weeks — §1256 saves
  `(40.8% − 30.6%) × return`, or **51 bp/yr on a 5% return**.
- **Against a deferred long-only equity holding**, §1256 is worse on both counts: the rate
  is higher *and* mark-to-market destroys the deferral §4 prices. Over 30 years at 5%
  growth the deferral loss is **82 bp/yr**, so the net is **−31 bp/yr**.

Which of those is the counterfactual decides the sign, and nothing about the statute
settles it. In the 0% long-term bracket the blend is a pure tax *increase*: `0.4 × 12% =
4.8%` against a 0% alternative.

**And in practice the 60/40 split did not reach shareholders of any fund checked.** Read
from N-CSR tax-character tables: **DBMF distributed 100% ordinary income in 2024 and
2025**; **KMLM 100% ordinary in FY2026** (of which 56.97% was US Government interest on
T-bill collateral, not trading profit); **CTA 100% ordinary in FY2025**; and **NTSX**
reports its distributions in a table with a single column headed "Distributions Paid from
Ordinary Income" for FY2024 and FY2025. Three mechanisms stack:

1. A Cayman subsidiary converts commodity gains to ordinary income **asymmetrically** —
   DBMF's own prospectus: *"Any annual net profit of the Subsidiary will be recognized as
   ordinary income by the Fund, but any annual net loss of the Subsidiary will not be
   recognized and will not carry forward."* This is forced by
   [§851(b)(2)](https://www.law.cornell.edu/uscode/text/26/851): Rev. Rul. 2006-31 holds
   *"A Derivative is not a security for purposes of section 851(b)(2)"*, and the blocker is
   capped at 25% of assets by §851(b)(3)(B). One fund checked ran at 24.7%.
2. Capital-loss carryforwards absorb the 60% long-term half — DBMF $165.6m, NTSX $163.5m,
   CTA $47.0m.
3. [§1256(f)(2)](https://www.law.cornell.edu/uscode/text/26/1256) says the 60/40 rule
   *"shall not apply to any gain or loss which, but for such paragraph, would be ordinary
   income or loss"*, so it cannot rescue income that is ordinary by another route.

**NTSX is the structural exception**, and the reason is worth stating: Treasury futures
generate qualifying income directly, so it needs no blocker and has none in the
registration statement's list. Its own filing also records the cost of mark-to-market —
DBMF's SAI states that it *"may cause the Fund to recognize income without receiving cash…
a Fund may be required to liquidate its investments at a time when the investment adviser
might not otherwise have chosen to do so."*

**Capital efficiency: the mechanism, the cost, and why it is not booked.** A
"return-stacked" fund at 90% equity plus 60% Treasury-futures notional obtains 150% of
exposure per dollar. WisdomTree's NTSX
([prospectus dated 2025-11-01](https://www.sec.gov/Archives/edgar/data/1350487/000121465925015435/pea965102025485bpos.htm))
is the reference case: *"approximately 90% of its net assets in U.S. equity securities"*,
Treasury futures at *"approximately 60% of the Fund's net assets"* targeting 3–8 years
duration, total expenses **0.20%**, inception 2018-08-02.

The arithmetic of whether that helps is entirely in one expression:

```
net contribution = bond notional × (bond excess return over cash − implied financing spread) − fee
```

so the break-even bond excess return is `financing spread + fee / bond notional`. **The
financing spread has been measured, and it is large.** Fleckenstein and Longstaff,
[*"Renting Balance Sheet Space"*](https://www.anderson.ucla.edu/sites/default/files/document/2021-12/Renting%20Balance%20Sheet%20Space%20Intermediary%20File70.pdf),
*RFS* 33(11) (2020), on 6,943 daily observations of CME 5-year Treasury note futures from
1991 to 2018: *"The average funding basis is **58.70 basis points**, but reached levels of
200 basis points or more"*. It is 58.79 bp before the crisis and 58.56 bp after, and
positive in **all 28 years** — a stable cost, not a crisis artefact. Equity futures are
similar and more variable: CME measures the E-mini S&P 500 roll at *"62bps rich"* over
3-month SOFR across ten rolls from December 2022 to March 2025, ranging 20 to 142 bp, and
at **−27 bp** against LIBOR in September 2011, so the sign is not even constant.

**At a 58.70 bp financing spread and NTSX's 20 bp fee, a 90/60 fund needs 92.0 bp/yr of
Treasury excess return over cash before the overlay contributes anything at all.**

**Both inputs are forecasts.** The bond excess return over cash *is* the term premium, and
the financing spread is a market price that moves by 120 bp across rolls. That is the
definition of probabilistic, and it is why nothing from this section enters a contractual
budget however attractive the mechanism looks.

**The evidence that the whole advantage lives in the financing assumption is now
quantitative, and both sides of it are on the record.** Asness, Frazzini and Pedersen,
[*"Leverage Aversion and Risk Parity"*](https://www.aqr.com/-/media/AQR/Documents/Insights/Journal-Article/Leverage-Aversion-and-Risk-Parity.pdf),
*FAJ* 68(1) (2012) — the editor's note records that *"The authors are affiliated with AQR
Capital Management, LLC, which offers risk parity funds"* — report risk parity beating the
market by 2.7%/yr over 1926–2010. Their **own Appendix B** shows what financing does to it:

| Financing rate | Spread over T-bills | RP − market | t-stat |
| --- | ---: | ---: | ---: |
| T-bills | 0 bp | 4.15% | **2.95** |
| Repo | 20 bp | 3.38% | 2.40 |
| OIS | 24.6 bp | 3.21% | 2.28 |
| Fed funds | 40.4 bp | 2.64% | 1.88 |
| **LIBOR** | **62.3 bp** | **1.81%** | **1.29** |

Their defence is one sentence: *"Note that leverage can be achieved by using futures
contracts at an implicit cost that is lower than LIBOR."* **Fleckenstein and Longstaff's
measured 58.70 bp is almost exactly that 62.3 bp LIBOR spread.** The one measurement of
the implicit cost retrieved for this page does not support the defence.

The independent critique reaches the same place from a different direction. Anderson,
Bianchi and Goldberg,
[*"Will My Risk Parity Strategy Outperform?"*](https://escholarship.org/content/qt21t3566t/qt21t3566t.pdf?t=mqe9e1)
(*FAJ* 68(6), 2012; quoted from the open working paper), verbatim: levered risk parity
beats 60/40 *"by 210 basis points, and the result is statistically significant (P = 0.03)"*
financing at the risk-free rate, but *"Once we take account of borrowing costs that exceed
the risk-free rate, the return of levered risk parity exceeds that of 60/40 by only **29
basis points**, and is nowhere close to being statistically significant (P = 0.40)."* A
~60 bp financing spread removes **86%** of the claimed edge, over eighty-five years of
data.

**NTSX's own record does not settle it either way, for the reason decision 0003 exists.**
Since inception to 2026-03-31 it returned 11.38%/yr against 8.81% for 60% S&P 500 / 40%
Bloomberg US Aggregate and 13.35% for the S&P 500 alone — **+2.57 pp/yr against 60/40 and
−1.97 pp/yr against equities**. WisdomTree publishes no 90/60 blended comparator; the
60/40 comparison is not risk-matched, and outperforming a lower-risk portfolio in an
equity bull market is precisely the trap
[decision 0003](../decisions/0003-cheap-broad-market-control.md) requires a risk-matched
comparator to catch. Note also there were **no capital-gains distributions in any year
2022–2026**, which is a real and separate point in the structure's favour.

**What decision 0004 actually forbids, and what it does not.**
[Decision 0004](../decisions/0004-no-sleeve-promoted.md) says leverage stays at zero
because *"It was conditioned on an unlevered edge surviving the protocol. None has, so
there is nothing to lever."* Read precisely, that forbids **levering an edge**. Capital
efficiency is not that: it is obtaining a *diversifying exposure* per dollar. But the
[edge decomposition](expected-edge-decomposition.md#22-what-is-rejected-and-why) closes
the gap from the other side — distinct risk premia including the term premium are excluded
*"by construction"*, because *"Booking a term premium as an 'edge' over an equity index is
a benchmark switch, not a return source"*. **So the 60% Treasury overlay is not an edge
under this repository's own rules even if the term premium is positive.** It is a
risk-budgeting choice, and the repository has no investor policy against which to make it
([framework open decision 1](portfolio-edge-research-framework.md)).

The [framework](portfolio-edge-research-framework.md) and
[Experiment 003](rebalancing-policy.md) both found levered risk parity's entire advantage
living inside its financing assumption, and the same is true here: the whole question is
whether the implied financing rate beats the investor's own alternative, and no
measurement of that rate was retrieved for this page.

**What would justify revisiting 0004**, stated as measurable conditions rather than a
hope:

1. **A measured implied financing spread** on the specific contracts a candidate fund
   rolls — implied repo against the investor's own cash alternative — over a predeclared
   window, from contract-level data rather than a fund's headline return.
2. **A signed term premium** under the framework's own protocol, which no experiment has
   attempted. Every factor that has been tested is `unresolved` or `rejected`.
3. **A defined investor policy** — the framework's open decision 1 — because leverage
   changes the drawdown distribution and there is currently no stated tolerance to test
   it against.
4. **A margin and forced-liquidation path**, since the framework already records that
   levered strategies' advantage disappears once borrowing rates, taxes and forced
   liquidations are modelled.

Until all four exist, the honest statement is: **capital efficiency is the most
substantive structural candidate on this page and the only one whose sign this repository
cannot check.** The one *contractual* piece inside it is the §1256 treatment above, and it
is inseparable from the leverage decision, so it is reported and not booked.

---

## 4. Deferred unrealised gain — the largest number on this page

**Mechanism.** An unrealised gain is an interest-free loan from the government whose
principal compounds with the position. Realising it converts the loan into a payment.
[26 U.S.C. §1014](https://www.law.cornell.edu/uscode/text/26/1014) resets basis to fair
market value at death, which forgives the loan outright; a gift of appreciated long-term
property to a public charity under §170 does the same thing while the donor is alive.

**Size.** With a 7% pre-tax log growth rate and the top rates, all figures annualised log
growth in bp/yr:

| Horizon | Deferral (never realise vs realise annually) | Step-up (never realise vs liquidate at the end) | Total |
| --- | ---: | ---: | ---: |
| 10 yr | 34.6 | 127.6 | **162.2** |
| 20 yr | 63.4 | 98.8 | **162.2** |
| 30 yr | **84.1** | 78.1 | **162.2** |
| 40 yr | 99.0 | 63.3 | **162.2** |

The total is **horizon-free at 162.21 bp/yr**, because both endpoints compound at
constant rates: it is exactly `g − log(e**g (1 − q) + q)`, which contains no `H`. The
horizon only decides how the 162 bp splits between deferral and forgiveness. That is a
closed form, checked against the simulator to machine precision.

**The consequence, and it is the strongest argument on the page.** At a thirty-year
horizon the deferral component alone is **84 bp/yr** — 95% of the entire 89 bp/yr
contractual budget the repository has already booked. **A strategy that fully turns over a
taxable portfolio every year must out-earn 84 bp/yr before it beats doing nothing**, on
top of its fee and its spread. Nothing in the existing budget states this hurdle, and it
is larger than every line in it except fund cost.

Two limits stated so the figure is not over-read. It is an upper bound — realising *all*
standing gain annually is what an unmanaged high-turnover strategy approximates, not what
a real one does — but the function is **sharply concave, not proportional**, which is the
part usually assumed away: at 30 years, realising 10% of standing gain a year already
costs 41.5 bp, 25% costs 63.9 bp and 50% costs 76.4 bp against the full-turnover 84.1 bp.
Half the penalty arrives in the first tenth of the turnover, so "low turnover" is not a
defence. And it vanishes entirely in the 0% long-term bracket and in every sheltered
account, where `q = 0` makes the whole expression zero.

**Double count: not additive as a positive line.** It is a **hurdle**, not a saving — the
cost of a policy the investor is not currently pursuing. Booking 84 bp as an edge would be
claiming credit for not doing something nobody proposed. It belongs in the budget as a
constraint on any future turnover-bearing sleeve, which is exactly where
[decision 0004](../decisions/0004-no-sleeve-promoted.md) leaves the question.

**Falsifier.** Repeal of §1014 in favour of carryover or deemed-realisation basis, which
would remove the second column entirely; or a flat rate structure in which realisation
timing carries no rate arbitrage.

---

## 5. Direct indexing against the 30 bp already booked

**Where the 30 bp comes from.** The [edge decomposition](expected-edge-decomposition.md#21-what-survives-with-its-evidence)
sources it to Chaudhuri, Burnham and Lo's 1.08%/yr headline, cut by four conditions the
paper itself states — the base case assumes 12.7%/yr of new money, roughly half the alpha
is rate arbitrage that disappears at a flat rate, transaction costs take 16 bp, and
security-level losses **cannot** be passed through a fund. That last condition means the
30 bp line **already assumes direct security ownership**. Direct indexing is not an
addition to it; it is the *precondition* for it.

**So the question is not whether direct indexing raises the 30 bp. It is whether the
30 bp survives the fee charged to obtain it.** The budget states the line gross of that
fee, and that is the omission this page corrects.

**The decay profile, and why the horizon average is the only honest statistic.** The
primary source is Sosner, Gromis and Krasner,
[*"The Tax Benefits of Direct Indexing: Not a One-Size-Fits-All Formula"*](https://www.aqr.com/-/media/AQR/Documents/Journal-Articles/AQR-The-Tax-Benefits-of-Direct-Indexing.pdf),
*Journal of Beta Investment Strategies* 13(2), Summer 2022. Its conflict of interest runs
the useful way: AQR sells tax-aware long/short strategies that *compete* with direct
indexing, so the paper's conclusion is adverse to the product it is not selling. Exhibit 1
is a year-dummy regression on 45 overlapping simulations, 1975–2019, S&P 500 universe,
2020 rates, HIFO lots — and the wash-sale rule **not modelled**, so every figure is an
upper bound. Annual active tax benefit, in bp:

| Year | No flow, long-term gains only | No flow, short-term gains available | 1%/month contributions, long-term only |
| ---: | ---: | ---: | ---: |
| 1 | 155.3 | 339.1 | 164.3 |
| 2 | 50.8 | 114.0 | 64.7 |
| 5 | 8.0 | 36.8 | 32.8 |
| 7 | **−0.5** | 24.1 | 28.7 |
| 10+ | **−4.3** | 18.2 | 27.4 |

The mechanism is ossification, and it is self-inflicted rather than merely a bull-market
effect. Verbatim: *"The loss-harvesting process itself further accelerates the accumulation
of built-in gains as tax lots that are at a loss are being systematically sold while tax
lots that are at a gain are being systematically retained in the portfolio."* Averaged
over a holding period — which is what "bp/yr" means — those profiles give:

| Horizon | No flow, LT only | No flow, ST available | With contributions |
| ---: | ---: | ---: | ---: |
| 1 yr | 155.3 | 339.1 | 164.3 |
| 5 yr | 51.7 | 121.7 | 69.7 |
| 10 yr | 25.3 | 72.3 | 49.0 |
| **30 yr** | **5.6** | **36.2** | **34.6** |
| 30 yr, net of a 9 bp fee | **−3.4** | 27.2 | **25.6** |
| 30 yr, net of a 40 bp fee | −34.4 | **−3.8** | **−5.4** |

**Three readings.** The 30 bp already in the budget is well calibrated to the *contributing*
investor — 34.6 bp gross over thirty years — and the budget's own condition text says so.
For a **static** investor with only long-term gains the honest figure is **5.6 bp**, and
negative at any fee. And **at a 40 bp fee no scenario measured is positive over thirty
years**, including the one requiring systematic short-term gains from hedge funds or
derivatives. Vendor headlines quote year one, which is the largest number any of these
profiles ever takes.

Fees, from published schedules as of July–August 2026: **Wealthfront S&P 500 Direct 9 bp
($5,000 minimum), Frec 9 bp ($20,000), Wealthfront Nasdaq-100 Direct 12 bp, Altruist 12 bp
(adviser channel), Vanguard Personalized Indexing 20 bp (sub-advisory tier, $250,000 —
there is no retail-direct product), Schwab Personalized Indexing 40 bp ($100,000), Fidelity
Managed FidFolios 40 bp**. Retail direct indexing has bifurcated into a 9–12 bp automated
tier and a 40 bp incumbent-brokerage tier, and against the profiles above **the 40 bp tier
is negative expected value in steady state**.

**Two conditions that decide the whole line, and both are usually assumed.** First,
[§1211(b)](https://www.law.cornell.edu/uscode/text/26/1211) caps the deduction of net
capital loss against ordinary income at **$3,000 a year** — a nominal figure unchanged
since 1978 and never indexed — with the excess carried forward under §1212(b). On a $1m
portfolio harvesting 5% of value, the benefit is **119 bp with offsetting realised gains
and 12.2 bp without them**, a factor of ten. Worse, the cap is nominal, so its
basis-point value falls with portfolio size: at 40.8% it is worth at most $1,224 a year,
which is 122 bp of $100,000 and **1.2 bp of $10m**. Every vendor figure assumes offsetting
gains are available; Vanguard's own research puts loss-offsetting income at only 2–9% of
taxable equity across net-worth profiles.
Second, harvesting is a *deferral*: the sheltered gain reappears in the replacement lot's
lower basis, so the permanent part is only the rate arbitrage plus whatever §1014
eventually forgives — which is §4's number, not this one.

**And one avoidance whose cost is permanent rather than timing.** An ordinary wash sale
under [§1091](https://www.law.cornell.edu/uscode/text/26/1091) merely defers the loss,
because §1091(d) adds it to the replacement shares' basis. **Revenue Ruling 2008-5 removes
that repair when the replacement is bought inside the taxpayer's IRA**: the loss is
disallowed and the IRA's basis is not increased, so the deduction is destroyed. At the top
rate a 5%-of-portfolio disallowance costs 119 bp outright. This is the only tax-loss
mechanic on the page whose damage is not recoverable, and it is a hazard of harvesting
rather than a benefit of it.

**Double count: not additive. This is a small downward revision.** The 30 bp line should be
read as **gross of a direct-indexing fee it does not subtract**. Netting a 9 bp fee and
using the 30-year horizon average moves it to **25.6 bp for a contributing investor**, a
−4.4 bp correction, with the range running from −34 bp (static investor at 40 bp) to
+27 bp (short-term gains available at 9 bp).

---

## 6. Securities lending — the 1 bp verified, by asset class

Net securities-lending income as a fraction of average net assets, read from N-CSR
Statements of Operations for fiscal years ending July to December 2025. Dollar figures are
read directly; the average-net-assets denominator is **inferred** two ways (net investment
income divided by the reported NII ratio, and the midpoint of beginning and ending net
assets), which is why several are ranges.

| Fund | Net lending income | **bp/yr** |
| --- | ---: | ---: |
| IEFA (iShares Core MSCI EAFE) | $14.13m | **1.08–1.11** |
| VEA (Vanguard Developed Markets) | $68.28m | **~2.97** |
| VB (Vanguard Small-Cap) | $48.21m | **~3.0–3.1** |
| VXUS (Vanguard Total International) | $171.17m | **~3.4–3.6** |
| VWO (Vanguard Emerging Markets) | $62.31m | **~4.9–5.2** |
| IEMG (iShares Core MSCI EM) | $83.34m | **~9.2–9.7** |
| VSS (Vanguard FTSE All-World ex-US Small-Cap) | $14.70m | **~13.0–13.4** |

Three findings, none of which changes the budget materially.

- **The 1 bp booked is right for a US total-market fund and low for an international one.**
  A portfolio 20% international earns about 1.5 bp rather than 1.0, so the correction is
  +0.5 bp. Immaterial, and recorded so nobody re-derives it.
- **It is not a size effect.** VB, US small-cap, earns 3.0 bp — the same as VEA, large-cap
  developed. The premium is in *international and emerging* lending demand, and largest in
  international small-cap. The edge decomposition's framing of the VOO/VTI gap as "the
  small- and mid-cap tail" does not extend to this evidence.
- **The sponsor matters more than the asset class.** IEFA at ~1.1 bp and VEA at ~3.0 bp
  hold nearly the same universe. That is a threefold difference in the same mandate.

Structurally, [§851(b)(2)(A)](https://www.law.cornell.edu/uscode/text/26/851) lists
*"payments with respect to securities loans"* as qualifying RIC income, so this revenue
never threatens fund status. **Double count: already counted**, at 1 bp, revised to about
1.5 bp for an internationally diversified portfolio.

---

## 7. Account-type sequencing — mostly not an edge, and the exception is not a rate

**Traditional against Roth is a forecast, not a structure.** Contribute `C` pre-tax
dollars: the traditional account ends at `C e**(gH) (1 − t_withdrawal)` and the Roth at
`C (1 − t_contribution) e**(gH)`. Multiplication commutes, so **they are identical
whenever the two rates are equal**, and the entire difference is the rate change: a saver
falling from 32% to 22% gains exactly `(1 − 0.22)/(1 − 0.32) − 1 = 14.71%` of terminal
wealth, and one whose rate rises loses the mirror image. Predicting one's own marginal
rate thirty years out is a forecast, so this line is **probabilistic and does not belong
in a contractual budget** however large it is.

What *is* structural, and follows from the same algebra, is that **a tax-deferred balance
is not the investor's money**. At a 24% withdrawal rate, $100,000 of traditional IRA is
$76,000 of investor wealth and $24,000 of government wealth. An allocation stated on
nominal balances therefore misstates true equity exposure, and — more sharply for this
page — an asset-location comparison run on nominal rather than after-tax dollars is
systematically wrong. §1's ranking is stated per dollar of shelter *capacity* precisely to
sidestep that.

**The HSA is the one genuine structural exception.** It is the only US account untaxed at
all three points — deductible in, untaxed inside, untaxed out for qualified medical
expense — and contributions made through payroll additionally escape FICA. That is not a
rate forecast; it is a strictly dominant wrapper. But its value is a **dollar amount
bounded by an annual contribution limit** — $4,400 self-only and $8,750 family for 2026
under [Rev. Proc. 2025-19](https://www.irs.gov/pub/irs-drop/rp-25-19.pdf), plus a $1,000
age-55 catch-up hardcoded in §223(b)(3) and never indexed — not a rate on a portfolio, so
it cannot be expressed as bp/yr on a portfolio of arbitrary size and is not booked here.

Two conditions are routinely dropped. It requires a high-deductible health plan. And
**California breaks all three legs**: its
[2025 Schedule CA (540) instructions](https://www.ftb.ca.gov/forms/2025/2025-540-ca-instructions.html)
state *"California law does not conform"* on the deduction, that *"Interest or earnings in
an HSA are taxable in the year earned"*, and that gains on internal sales are California
realisation events. For a Californian an HSA is federally dominant and a *worse* wrapper
than a taxable brokerage account on one axis — forced annual realisation of internal
gains. New Jersey is widely reported to do the same; **no New Jersey primary source
addressing HSAs was found at all**, so treat that as inference from omission.

**Double count: not additive.** Account *choice* is a rate forecast (probabilistic);
account *sequencing* of assets is the asset-location line already booked at 10 bp; the HSA
is a dollar lever outside the rate framework.


---

## 8. Smaller levers, sized so they can be dismissed with a number

**Municipal bonds — material, maturity-dependent, and inactive for this investor.**
[§103(a)](https://www.law.cornell.edu/uscode/text/26/103) excludes state and local bond
interest from gross income, and Treas. Reg. §1.1411-1(d)(4)(i) names it as excluded income
for the §1411 surtax too, so the tax-equivalent yield divides by the full 40.8%. At
2026-07-29, with MMD AAA general-obligation yields against the official Treasury par curve
on the same date:

| Term | Muni | Treasury | Break-even marginal rate | Tax-equivalent yield at 40.8% | Pick-up |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2 year | 2.54% | 4.22% | **39.81%** | 4.29% | **+7 bp** |
| 5 year | 2.84% | 4.37% | 35.01% | 4.80% | +43 bp |
| 10 year | 3.24% | 4.67% | 30.62% | 5.47% | +80 bp |
| 30 year | 4.39% | 5.20% | **15.58%** | 7.42% | **+222 bp** |

**Any rule of the form "municipals for taxable accounts" is wrong at the short end**: the
break-even marginal rate falls from 39.8% at two years to 15.6% at thirty, so a top-bracket
investor gains essentially nothing at two years and 222 bp at thirty. **Not booked for the
reference investor, at zero**, because §1's ranking puts bonds into the shelter first by a
factor of four over any equity sleeve — municipals only activate once the bond allocation
exceeds shelter capacity. The comparison also makes no adjustment for credit or call risk.

**Specific identification of tax lots — cheap, legally clear, and under-measured.** Treas.
Reg. §1.1012-1(c)(3) requires only that *"At the time of the sale or transfer, the taxpayer
specifies to such broker or other agent having custody of the stock the particular stock to
be sold"*, §1.1012-1(c)(8) accepts *"A standing order or instruction"*, and §1.1012-1(c)(10)
says the choice *"is not a method of accounting"* — so switching is free and needs no Form
3115. The default without it is first-in-first-out, which realises the most gain.

The only measurement found is Dickson, Shoven and Sialm,
[*"Tax Externalities of Equity Mutual Funds"*](https://www.nber.org/papers/w7669) (*NTJ*
53(3), 2000): in a no-cash-flow separate account over 1984–98, HIFO beat FIFO by
*"7.72 basis points per month"* and average cost by *"6.09 basis points per month or 73
basis points per year"*. A worked lot model confirms the scale: twenty annual $10,000
purchases compounding at 7%, selling a quarter of the position, realises **$83,159 of gain
under FIFO against $31,944 under highest-in-first-out** — $51,215 of gain deferred on
$112,978 of proceeds. **Booked at 5 bp**, heavily shrunk from 73, because the DSS figure is
a simulation over an unusually strong bull market on a portfolio with index turnover, and a
buy-and-hold retail investor who never sells realises nothing at all.

**Charitable gift of appreciated shares — real, and worse in 2026 than it was.**
[§170](https://www.law.cornell.edu/uscode/text/26/170) allows a deduction at fair market
value for long-term appreciated property held over a year, and §170(e)(1)(A) reduces only
gain *"which would not have been long-term capital gain"* — so the appreciation escapes tax
to everyone. Three 2026 changes make the arithmetic worse and are easy to miss: the 30%-of-AGI
limit under §170(b)(1)(C)(i); a **new 0.5%-of-AGI floor** under §170(b)(1)(I) whose ordering
rule absorbs capital-gain property **first**; and a rewritten
[§68](https://www.law.cornell.edu/uscode/text/26/68) reducing itemised deductions by
*"2/37"*, capping the marginal federal subsidy at `37% × (1 − 2/37) = 35%`. **Not booked**:
a cheaper way to do something the investor was already doing is a real saving and not a
return, and counting it would let any spending decision become alpha.

**Net unrealised appreciation on employer stock —
[§402(e)(4)(B)](https://www.law.cornell.edu/uscode/text/26/402).** Distribute employer
securities in kind in a lump sum; ordinary tax applies only to the plan's basis and the
appreciation is long-term on later sale. Worth `(40.8% − 23.8%) × (1 − basis fraction)`
once: **13.6 bp/yr** for a 10% position at 20% basis distributed in ten years. Requires
employer securities in a qualified plan and a triggering event, and it is the one
appreciated asset that does **not** get a §1014 step-up, being income in respect of a
decedent under §691 — though the specific authority for that classification, Rev. Rul.
75-125 (1975-1 C.B. 254), could not be retrieved and the point rests on §1014(c) plus
§691(a)(3). **Not booked**: narrow, and sizing a concentrated position is not recommending
one.

**Tax-gain harvesting in the 0% bracket.** The wash-sale rule is written for losses only,
so selling and repurchasing at a gain is legal and costs the spread. Worth the rate spread:
realising a fifth of the portfolio as gain at 0% against a later 23.8% is **47.6 bp/yr over
ten years**. The 2026 zero-rate ceiling is **$98,900 of taxable income joint and $49,450
single** (Rev. Proc. 2025-32 §4.03), which with the standard deduction is about $131,100
and $65,550 of gross income. **Not booked**: it needs a low-income year, it competes with
Roth conversions for the same bracket space, and it *reduces future harvesting capacity* by
raising basis — an engine running both must sequence them.

**Two errors avoided, not levers.** Revenue Ruling 2008-5 holds a loss disallowed under
§1091(a) where the replacement is bought in the taxpayer's IRA, and — verbatim — *"A's
basis in the individual retirement account or Roth IRA is **not** increased by virtue of
§ 1091(d)"*. IRS Publication 550 says the same in its own list, adding *"except in (4)
above"* to the sentence that normally rescues the loss. **This is the only tax-loss
mechanic on the page whose damage is permanent rather than timing**: 119 bp on a
5%-of-portfolio disallowance at the top rate. The engineering consequence is concrete —
wash-sale scanning must be household-wide across IRAs and a spouse's accounts, because a
same-account check converts a deferred loss into a destroyed one. Separately,
[§1(h)(11)(B)(iii)](https://www.law.cornell.edu/uscode/text/26/1) substitutes "60 days" and
a "121-day period" into §246(c), so a dividend is qualified only if the stock is held more
than 60 days in that window; a fund only 70% qualified on a 2% yield loses **10.2 bp/yr**.
Neither is booked, because an avoided mistake is not a return source.

---

## The ledger

Every lever examined, sized at **portfolio level for one stated reference investor**:
US top bracket, 30-year horizon, liquidation at the end; 60% US equity, 14% developed
ex-US, 6% emerging, 20% taxable bonds; 40% of the portfolio in tax-advantaged capacity and
60% taxable, located by §1's ranking — so the shelter holds the bonds and the whole
international sleeve and the taxable account holds US equity. Stating the reference is not
decoration: quoting a per-sleeve number as though it were a portfolio number is the single
commonest way a tax figure is inflated, and every lever here has a different base.

| Lever | Size (bp/yr, portfolio) | Range | Class | Benchmark | Additive to the 89 bp? |
| --- | ---: | --- | --- | --- | --- |
| **Fund structure: capital-gain distributions avoided** | **+23.0** | 0 to +50 | deterministic | own counterfactual | **ADDITIVE** |
| **Specific identification of tax lots** | **+5.0** | 0 to +44 | deterministic | own counterfactual | **ADDITIVE** (residual only) |
| Foreign tax credit forfeited inside a shelter | **−3.4** | −6 to 0 | deterministic | own counterfactual | No — **correction** to the 10 bp location line |
| Direct-indexing fee, netted against harvesting | **−4.4** | −30 to +6 | deterministic | own counterfactual | No — **correction** to the 30 bp harvesting line |
| Securities lending, verified by asset class | +0.5 | 0 to +2 | deterministic | stated index | No — same 1 bp line, revised |
| Deferred unrealised gain | 84.1 | 0 to 162 | deterministic | own counterfactual | **No — a hurdle, not a saving** |
| Municipal bonds for taxable bonds | 0.0 | 0 to +222 | deterministic | own counterfactual | No — inactive; shelter covers the bonds |
| Section 1256 60/40 treatment | 0.0 | 0 to +51 | deterministic | own counterfactual | No — no futures sleeve; leverage is zero |
| Traditional vs Roth, and the HSA | 0.0 | — | **probabilistic** | own counterfactual | No — a rate forecast, or a dollar limit |
| Charitable gift, NUA, tax-gain harvesting | 0.0 | 0 to +48 | deterministic | own counterfactual | No — each needs a circumstance, not a decision |
| Wash sale into an IRA; non-qualified dividends | 0.0 | 0 to +119 | deterministic | own counterfactual | No — errors avoided are not returns |
| **Additive total** | **+28.0** | **0 to +94** | | own counterfactual | |
| **Corrections** | **−7.8** | | | own counterfactual | |
| **Revised own-counterfactual budget** | **≈109 bp** | **4 to 270** | | own counterfactual | was 89 bp, range 40–170 |

The 4-to-270 interval is the arithmetic sum of the existing 40–170 range, the additive
lines' 0–94, and the corrections' −36 to +6. Read it as an outer bound and not as a
distribution: it assumes every condition fails together at the bottom (a sheltered
account, an index-fund counterfactual, a static investor at a 40 bp fee) and succeeds
together at the top, and those conditions are correlated rather than independent. The
central 109 bp is the number to use.

At about 109 bp of edge against roughly 46 bp of combined tracking error, 90% confidence
arrives in about **3.5 months** and 99% in about **twelve** — against 4.2 and 13.8 months
for the 89 bp budget. **A fifth more edge buys about two months.** That is the same lesson
the [edge decomposition](expected-edge-decomposition.md#3-what-probability-is-actually-attainable)
already draws: certainty is a property of the pairing of edge and benchmark, not of the
edge's size.

---

## Assumptions, open questions, and provenance

**Assumptions, stated so they can be attacked.** Pre-tax log growth of 7%/yr with constant
parameters, no volatility and no cash flows; tax paid out of the account rather than from
an external wallet; distributions reinvested; rates constant over thirty years, which no
thirty-year period in US history has satisfied; the reference investor's allocation and
account split held fixed. All of these fail in directions that mostly *reduce* the measured
advantage, except the constant-rate assumption, which cuts both ways.

**Open questions this page does not settle.**

1. **The implied financing spread a retail investor actually pays** through a capital-
   efficient fund. Fleckenstein and Longstaff measure 58.70 bp on 5-year Treasury note
   futures to 2018; no 2019–2026 measurement was retrieved, and no measurement at all of
   what a specific fund's roll costs. This is the binding gap on §3.
2. **The asset-weighted capital-gain distribution rate of the active funds a real investor
   would otherwise hold.** The 3%-of-NAV central estimate is bracketed by Morningstar's
   frequency data and by two named funds at 6.6–7.0%, but no asset-weighted average was
   found. The largest additive line rests on it.
3. **Whether ETF share classes actually eliminate the distributions.** Ninety-four orders
   exist; no SEC document quantifies the benefit, and none states how in-kind ETF-class
   redemptions interact with the mutual-fund class's gains. The operative conditions live
   in each applicant's 40-APP application, which was not read.
4. **The value of lot-selection discipline for a retail buy-and-hold investor.** The only
   measurement is a 1984–98 simulation on a turning-over separate account. The 5 bp booked
   is a judgement, not a measurement, and it is the weakest additive line on the page.
5. **Non-US tax.** Every figure here is US federal. A jurisdiction with no foreign tax
   credit turns §1 into a pure cost; one taxing gains on accrual removes §4 entirely; one
   with no step-up removes half of it.
6. **State tax.** Excluded throughout and additive where it exists. California is a
   documented special case that breaks two of the HSA's three legs; New Jersey is widely
   reported to do the same and **no New Jersey primary source addressing HSAs was found at
   all**, so treat that as inference from omission.

**Reproducibility.** Rates, yields and profiles are arguments rather than constants, all
committed in `tax_structure.py` with the source beside each. Retrieval date for every
source above: **2026-08-12**, except the municipal and Treasury curves (2026-07-29), the
Treasury par yield cross-check (2026-08-11), the BND yield (2026-08-10), MSCI index yields
(2026-07-31), and the SEC multi-class order count (2026-08-11).

**Sources that could not be retrieved**, named so nobody re-spends the budget.

- **Asness, "Why Not 100% Equities", *JPM* 22(2) (1996)** — paywalled at pm-research, no
  deposited abstract at Crossref or OpenAlex, and **AQR does not host it**. Its headline
  numbers circulate only through secondary sources and were not used here.
- **Asness, Frazzini and Pedersen's 2013 comment and Anderson, Bianchi and Goldberg's
  author response**, *FAJ* 69(2) — both paywalled, neither with a deposited abstract. The
  exchange that would settle §3's dispute is the part that is unreadable.
- **Moussawi, Shen and Velthuis, *RFS* 38(10) (2025)** — published text paywalled. Figures
  are from the September 2022 working paper and the Harvard Law School Forum summary, and
  **the headline moved from 0.92%/yr to 1.05%/yr between them**; cite the version you use.
  The paper is frequently miscited to the *Journal of Finance*.
- **Constantinides (1983), *Econometrica* 51(3)** — closed access everywhere, no working
  paper exists. The widely repeated claim that it shows capital gains tax "can be reduced
  to near zero" has **no verbatim support in any retrievable source**; do not attribute it.
- **Dammon, Spatt and Zhang (2001), *RFS* 14(3)** — closed access, no repository copy, no
  working paper. Its headline numbers are unobtainable and are quoted here only from the
  authors' own non-technical restatement, which is secondary.
- **Chaudhuri, Burnham and Lo (2020) and Khang, Paradise and Dickson (2021), both *FAJ***
  — paywalled; figures from CFA Institute summaries.
- **Rev. Rul. 75-125, 1975-1 C.B. 254** — the specific authority classifying NUA as income
  in respect of a decedent. The IRS online bulletin archive does not reach 1975.
- **Berkeley CDAR** (the tax-loss-harvesting life-cycle work) — the entire domain fails DNS.
  **Parametric's insights library** — 403 and 404. Neither vendor's primary research was
  obtained.
- **Alpha Architect's bond-futures-vs-ETF tax comparison** — Cloudflare 403 on every route;
  its conclusion is reported here only from search-index extracts and is not first-party
  verified.
- **CME Group's own site is IP-blocked**; the equity-financing figures above were recovered
  through the Internet Archive. A 2026 CME article reporting an 81 bp June roll has **no
  archive capture and could not be retrieved**, so that figure is not used.
- **Schwab Asset Management's foreign tax credit page** — Akamai 403 to every user agent.
  SCHE and SCHF withholding ratios were therefore not obtained. **Avantis publishes no
  foreign-tax-paid figure at all**, so AVDV and AVES could not be sized.
- **congress.gov and govtrack** — 403 to every route, so the legislative status of the STEP
  Act and of any §852(b)(6) repeal successor rests on the absence of an amendment in the
  current Code text.
- **MSRB EMMA and FRED** — JS-only and unreachable respectively; the municipal curve comes
  from a dealer republication of MMD data rather than from MSRB directly.

**Corrections this page makes to material already in the repository.**

1. The [edge decomposition](expected-edge-decomposition.md) books tax-loss harvesting at
   **30 bp gross of the direct-indexing fee that the line's own conditions require**. The
   fee is 9–40 bp and the honest figure is about 25.6 bp.
2. The same page's asset-location line does not model foreign withholding, which costs
   3.4 bp/yr on the reference portfolio and which none of its cited sources addresses.
3. Its securities-lending note attributes the VOO/VTI gap to *"the small- and mid-cap
   tail"*. VB, a pure US small-cap fund, earns 3.0 bp — the same as large-cap developed
   international. The premium is an international and emerging-market lending-demand
   effect, not a size effect.
4. It states the ETF/mutual-fund comparison nowhere, and the fee gap it does book
   understates the cost of an active-fund counterfactual in a taxable account by roughly as
   much again.

---

## Consequence for this repository

1. **Revise the own-counterfactual budget to about 109 bp/yr** with the two additive lines
   and the two corrections above, and record that its largest component is decaying.
2. **Add the deferral hurdle to the promotion protocol.** Any sleeve that turns over a
   taxable portfolio must clear 84 bp/yr at a thirty-year horizon *before* its fee and its
   spread. [Decision 0004](../decisions/0004-no-sleeve-promoted.md)'s per-candidate
   conditions should carry it, because it is larger than every premium any experiment here
   has measured.
3. **The tax boundary must be a dated, versioned input.** `TaxRegime` in
   `tax_structure.py` is the shape: a labelled, jurisdiction-stamped, dated set of rates
   that refuses to construct without them. The framework asks for exactly this and the
   repository now has one. Nothing should hardcode a rate again.
4. **Asset location must be computed, not asserted.** The rule "shelter the higher-yielding
   asset" is right for bonds by a factor of four and wrong for emerging-market equity at
   two of the four US dividend rates. Any location feature must run the ranking rather than
   restate the maxim, and must state the bracket it assumed.
5. **Do not build a capital-efficiency feature, and do not close the question either.**
   Decision 0004 keeps leverage at zero and this page supplies the four measurable
   conditions that would justify revisiting it: a measured implied financing spread on the
   specific contracts a candidate rolls; a term premium signed under the framework's own
   protocol; a defined investor policy, which is the framework's open decision 1; and a
   modelled margin and forced-liquidation path.
6. **Recheck the fund-structure line before it is used.** Ninety-four SEC orders are
   already granted. A page whose largest new line has a visible mechanism of decay should
   carry a review trigger, and this is it.
