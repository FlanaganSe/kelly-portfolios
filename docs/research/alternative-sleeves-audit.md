# The alternative sleeves: which ones a retail investor can actually own

**Question.** Which of the strategy universe's families can a retail investor actually
own, at what cost, and does the net result clear admission? Two halves. The exotic half
is [the event-driven and structural universe](#the-universe-this-page-was-given) — a
dozen families this repository had never examined. The
**ordinary** half is the four categories a retail investor is most often pointed at and
which this programme, having audited 69 factor ETFs, 15 managed-futures ETFs, 8
capital-efficient overlays, catastrophe bonds, merger arbitrage, closed-end funds,
option-income funds, commodities and gold, had **never once touched**: dividend and
dividend-growth funds, REITs, buffer / defined-outcome funds, spot bitcoin, and — added
2026-08-17 — **fixed income**, which had no investable total-return history here at all.

**Decision it informs.** Whether the "one engine" finding in
[capital efficiency and breadth](capital-efficiency-and-breadth.md) is a fact about
markets or about the fund shelf — and, for the four ordinary families, whether the most
recommended products in retail investing survive the bar everything else here faced.

**Out of scope.** Private markets (§G) and the exploratory families (§H). Nothing here
is promoted; [decision 0002](../decisions/0002-no-research-grade-free-price-source.md)
caps product work at `exploratory`.

`as of 2026-08-17`. Every figure is from an SEC filing, an issuer document with its
retrieval date, or a computation performed here. **Where a source could not be reached
it says "not found" rather than an estimate.** The computations for §§4–7 are in
[`studies/retail_shelf.py`](../../research/src/portfolio_edge/studies/retail_shelf.py)
and [`_retail_shelf_tables.py`](../../research/src/portfolio_edge/studies/_retail_shelf_tables.py);
the fund facts, with a source URL and a read date on every one, are in
[`data-manifests/retail_shelf/product_facts.json`](../../research/data-manifests/retail_shelf/product_facts.json).

---

## The universe this page was given

The event-driven and structural families the working plan named, transcribed here so the
denominator of conclusion 12 lives in the repository rather than in an untracked working
file:

> merger arbitrage · convertible arbitrage · equity market neutral · closed-end fund
> discounts · spin-offs · index reconstitution · reinsurance and catastrophe bonds ·
> securities-lending revenue · volatility selling · put writing · covered calls ·
> defensive option overlays · dispersion, if realistically accessible · tax-loss
> harvesting and direct indexing

Its instruction for this class was to model payoff asymmetry and expected shortfall
explicitly wherever a strategy wins often and loses rarely and largely — which is the
test §2 and §6 below actually apply. Private markets and the exploratory families were
declared out of scope and are not transcribed.


## Conclusion

**Of twelve families now audited, one passes and it is constrained by its vehicle. None
of the five ordinary ones does — and they fail by five different mechanisms, which is
the part worth reading.**

| Family | Best retail vehicle | All-in cost | Sharpe | ρ to equity | Instrument | MDE₈₀ | Verdict |
| --- | --- | ---: | ---: | ---: | --- | ---: | --- |
| **Catastrophe bonds** | Brookmont ILS ETF | 1.58% cap / **2.00% actual** | not measurable | ~0.10 | (4) | — | **passes — IRA only** |
| Merger arbitrage | MERFX I / ARB | 1.26% / 0.76% | not measurable | low, rises in crashes | (4) | — | **borderline** |
| Volatility risk premium | JEPI / XYLD / QYLD | 0.35–0.60% | 0.47–0.72 | **0.86–0.95** | **(5)** | — | **rejected**, alpha −0.09 to −0.88 |
| Closed-end fund discounts | FCEF | **3.69%** | not measurable | high | **(5)** | — | **rejected**, under-evidenced |
| Securities lending | embedded in any fund | — | — | 1.0 | — | — | **not a sleeve** |
| Direct indexing | Frec 0.09% / $20k | 0.09–0.40% | — | **≈1.0 by design** | — | — | **category error** |
| **Dividend / dividend growth** | **SCHD** | **0.06%** + **0.51 pp/yr tax** | **0.643** | **+0.820** | **(5)** | **10.93** | **dominated**, not rejected — §4 |
| *same family, worst case* | NOBL | 0.35% | 0.440 | +0.875 | (5) | 8.19 | **rejected** — a resolved −4.94 pp/yr against the pedestal |
| *same family, the interesting one* | DIVO | 0.56% + **1.05 pp/yr tax** | 0.725 | +0.907 | (5) | 7.09 | **unresolved**, and its tax cost exceeds two-thirds of its measured edge |
| **REITs** | **VNQ** | **0.13%** + **0.61 pp/yr tax** | **0.157** | **+0.839** | **(5)** | **9.82** | **dominated** — and the payoff shape is put-writing's — §5 |
| **Buffer / defined outcome** | **BUFR** | **0.95%** | 0.722 | **+0.966** | **(5)** | 3.73 | **rejected on the option arithmetic** — §6 |
| *same family, priceable* | PJUL / POCT | 0.79% | 0.747 / 0.806 | +0.940 / +0.936 | (5) | 6.64 / 6.01 | **rejected**: −5.9 to −7.5 pp/yr structural cost |
| **Spot bitcoin** | **IBIT / FBTC** | **0.25%** | **0.995** | **+0.342** | **(4)** | **15.58** | **`unresolved`** — it clears the bar and the bar decides nothing — §7 |
| **Nominal Treasuries** | **GOVT / VGIT** | **0.03–0.05%** | −0.45 / −0.36 | **+0.277 / +0.274** | **(4)** | 20.56 | **`unresolved`** — the only leg that clears any bar, and only financed and below its floor — §8 |
| **TIPS** | **SCHP** | **0.03%**, net **2.99 bp** | −0.025 | **+0.623** | **(5)** | **14.89** | **`rejected`** — ρ +0.85 to the aggregate leg it would sit beside, and **more** equity-correlated and **less** stable than nominal — §8 |
| **Standalone credit** | LQD / VCIT / HYG | 0.14 / 0.03 / **0.49%** | −0.13 / −0.05 / +0.20 | **+0.702 / +0.693 / +0.844** | **(5)** | 12.23 / 11.87 / **6.74** | **`rejected`** — ρ +0.57 to equity on 275 months and resolved negative gaps on all three funds — §8 |

**Instrument (4)** is the admission condition `S_d > L rho sigma_p`. **Instrument (5)**
is the matched-volatility control, where the variance terms cancel and the higher Sharpe
ratio wins outright. Which one applies is decided by the correlation and not by hand:
[`overlay_growth.py`](../../research/src/portfolio_edge/studies/overlay_growth.py)'s
first misuse warning puts the boundary at `|rho| = 0.5`, and `choose_instrument` in
`retail_shelf.py` enforces it. **Dividend funds, REITs and buffer funds all sit between
+0.82 and +0.97 and are therefore scored by (5) and by (5) only** — equation (4) is not
reported for them at all, because at that correlation it is a small difference of large
numbers and it is exactly what made put-writing read as a pass while its alpha was
−0.09%/yr. **Bitcoin sits at +0.34 and is scored by (4)**, with (5) beside it.

---

## 1. Catastrophe bonds — the one that passes, and the access wall

**Only one genuinely self-directed vehicle exists.** Stone Ridge's website states SRRIX
has "no individual investor minimums or accreditation requirements". **The prospectuses
say otherwise**: SRRIX requires **$15,000,000** and SHRIX Class I **$25,000,000**, both
available only through a registered investment adviser that has "completed an
educational program provided by the Adviser". A $400k self-directed investor cannot buy
either.

What is left is the **Brookmont Catastrophic Bond ETF**: inception **2025-04-01**, net
assets **$85.8m at 2026-08-13**, holding 200+ 144A cat bonds directly. Gross expense
**2.65%**, contractual cap **1.58% through 2027-04-30 with three-year recoupment**, and
an **audited 2.00% actual** in its first period.

**The premium has halved and it is measured, not asserted.** Artemis deal-directory
primary-market averages:

| | 2023 | 2024 | 2025 | **2026 YTD** |
| --- | ---: | ---: | ---: | ---: |
| Multiple (spread ÷ expected loss) | **4.54×** | 3.71× | 3.00× | **2.40×** |
| Spread above expected loss | 6.94 pp | 6.44 | 4.73 | **3.98 pp** |

Quarterly the swing is starker — Q3 2023 **6.87×** to Q3 2026 **2.27×**. **The 2026
multiple sits below the 2014–2016 soft-market range.** Net of the ETF's fee the forward
excess over cash is **+2.0% to +2.4%/yr**, against roughly +5.4% on 2023 vintages.

**Two findings matter more than the premium, and both are about behaviour and tax.**

**The record everyone quotes is the hard market, and nobody earned it.** SRRIX's
time-weighted ten-year figure is **7.92%/yr**. Its net assets ran $5.98bn (FY2018) →
$1.01bn (FY2022) → $1.52bn (2026-04-30), so the money arrived before the losses and left
before the recovery. Approximating annual profit as beginning-of-year assets times the
year's return, the **aggregate dollar earned roughly 1.8%/yr against T-bills at
2.1%/yr** — about cash, for a decade, net of a 2.35% fee. Excluding the post-Ian hard
market, SHRIX's FY2016–FY2022 Sharpe was **0.18** and SRRIX's was **−0.45**.

**Tax decides the account.** Distributions are essentially 100% ordinary income (SRRIX
FY2025: $236.2m, no long-term gain). SHRIX's own SEC-standardised table, ten years to
2025-12-31: **6.44% before tax, 3.27% after taxes on distributions** — roughly half the
edge, and the pre-tax excess over cash of +4.26%/yr falls to about **+1.98%/yr** after
tax. **This sleeve goes in a shelter or it does not go anywhere.**

**Status: `exploratory`, monitor rather than allocate.** It clears the admission bar at a
correlation near 0.10, and its only accessible vehicle is sixteen months old, holds
$86m, charges a fee consuming 40–50% of the gross premium, and carries a waiver expiring
2027-04-30 with recoupment. The premium halved while the vehicle was being launched.

---

## 2. The volatility risk premium — rejected, and the usual claim is backfilled

**The folk claim that put-writing beat the S&P with two-thirds the volatility "since
1986" rests on a hypothetical backtest for its first two decades.** From Cboe's own
methodology documents: PUT has a base date of 1988-06-01 and a **launch date of
2007-06-20**; BXM's base is 1986-06-30 and its launch **2002-04**. Cboe's disclaimer:
values before launch "are calculated using a theoretical approach involving back-testing
historical data."

Regressions on the **live-only** history, monthly against Ken French `Mkt-RF`:

| Index | Live window | Sharpe | **Market Sharpe** | Beta | **Alpha %/yr** | *t* | ρ |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **PUT** | 2007-02…2026-06 | 0.548 | **0.646** | 0.584 | **−0.09** | −0.07 | **0.863** |
| **BXM** | 2002-05…2026-06 | 0.470 | **0.633** | 0.610 | **−0.88** | −0.82 | **0.874** |
| BXMD | 2015-09…2026-06 | 0.722 | 0.826 | 0.727 | −0.72 | −0.59 | 0.946 |

**Its standalone Sharpe is below the market's over the same window**, so substituting it
for equity lowers portfolio Sharpe. And the payoff shape is the mechanism, measured
directly: **up-market beta 0.45, down-market beta 0.86.** You get 45% of the upside and
86% of the downside.

**The genuine premium is real, small, and bundled.** Israelov and Nielsen (*FAJ* 71(6),
2015) decompose an ATM overwrite into 3.5% passive equity, **1.9% short volatility at a
Sharpe near 1.0**, and 0.5% of uncompensated equity timing they call "material,
uncompensated, and unnecessary". **The 1.9% is on full notional, and every retail
product charges its fee on full notional** — a 0.60% fee takes a third of it. Global X's
own filings show the overlay P&L was **−$302m for XYLD and −$1.54bn for QYLD** in FY2025.

**This family is where equation (4) breaks**, and the module now says so: applied
mechanically, PUT's 0.548 Sharpe clears a 0.20 bar and reads as a pass. At ρ = 0.86 the
marginal contribution is essentially the alpha, which is **−0.09%/yr with *t* = −0.07**.
See [`overlay_growth.py`](../../research/src/portfolio_edge/studies/overlay_growth.py).

---

## 3. Merger arbitrage, closed-end funds, securities lending, direct indexing

**Merger arbitrage is borderline and the passive vehicle is not.** MERFX Class I earned
**+2.06%/yr over cash across ten years** at roughly 3% volatility, but only
**+0.30%/yr over the last five**. **MNA, the passive ETF, earned nothing over T-bills in
a decade** — 2.17%/yr against a 2.18% bill — while turning over **317%** a year, and lost
**8.62% in Q1 2020**, the quarter equities fell about 20%. The hedged vehicles earn less
and hedge harder; the cheap one carries the crisis beta.

**Closed-end fund discounts fail on fees.** The one vehicle that could be priced, FCEF,
charges **3.69% all in** — 0.85% management plus **2.84% of acquired fund fees** — and
beat its own CEF benchmark by **+0.29 pp/yr** since 2016 while trailing the Russell 3000
by 7.23 pp/yr. A 3.69% fee needs about 4%/yr of gross discount alpha to break even
against cash. Recorded as **under-evidenced**: PCEF, CEFS and the academic magnitudes
could not be reached this session.

**Securities lending is a fund-selection detail, and a measurable one.** From N-CEN
filings, net revenue accruing to shareholders as basis points of net assets: **VOO 0.07,
VTI 1.02, VBR 2.53, VB 3.10, VXF 10.43**, and iShares' ICLN 8.81. It is a rounding error
on a broad-market holding and **worth ~3–10 bp on a small-cap or completion tilt** —
which is one fund-selection decision, not a sleeve.

**Direct indexing is a category error in this ledger.** It tracks the index by
construction, so ρ ≈ 1.0 and the only independent risk it adds is tracking error. Its
"alpha" is a reduction in the tax drag on equity already held — **a cost line, not a
return stream**, and it belongs beside the expense ratio. The independent decay estimates
were **not sourced**; Frec's "up to 40% of the initial investment harvested" is the
issuer's own hypothetical simulation and its disclaimer says so.

---

## 4. Dividend and dividend growth — a value-and-quality tilt with a small tax bill

**The measurement.** Form N-PORT Item B.5, each fund's own filed monthly total return,
net of its own fees, against **VTI's Item B.5 return** rather than a gross factor —
comparing a net fund against a gross academic series would flatter every sleeve by the
control's fee. Roughly 80 months, 2019-08…2026-05, which is every month public N-PORT
reporting exists.

| Fund | fee | excess %/yr | vol | Sharpe | ρ to VTI | **unlevered growth gap** | **matched gap (5)** | 95% CI | **MDE₈₀** |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| **SCHD** | 0.06% | 10.71 | 16.67 | **0.643** | +0.820 | **−1.39** | **−1.02** | [−9.64, +7.59] | **10.93** |
| VYM | 0.04% | 9.49 | 15.55 | 0.610 | +0.879 | −2.04 | −1.14 | [−8.28, +5.99] | 9.05 |
| DGRO | 0.08% | 9.89 | 15.37 | 0.643 | +0.932 | −1.57 | −0.58 | [−5.31, +4.15] | 6.00 |
| VIG | 0.04% | 9.36 | 14.59 | 0.642 | +0.943 | −2.03 | −0.61 | [−4.34, +3.12] | 4.73 |
| **NOBL** | 0.35% | 7.35 | 16.71 | **0.440** | +0.875 | **−5.11** | −4.51 | [−10.96, +1.95] | 8.19 |
| **DIVO** | 0.56% | 10.02 | 13.82 | **0.725** | +0.907 | −0.74 | **+1.52** | [−4.07, +7.11] | 7.09 |
| *VTI, the base* | 0.03% | 11.62 | 17.00 | **0.684** | 1.000 | — | — | — | — |

**Not one gap is resolved.** Every point estimate sits inside its own 80%-power floor,
and for SCHD the floor is **10.93 pp/yr against a −1.02 pp/yr estimate** — a factor of
eleven. **This window cannot tell SCHD apart from VTI and it never could have.** Every
sentence below is about mechanism, not about a measured difference.

**SCHD's record is its loadings.** FF5 plus momentum, HAC standard errors, 81 months.
Every alpha is a distance from **VTI's own alpha in the identical regression**, because
a cheap total-market fund does not score zero against a gross six-factor model — it pays
a fee and the model misfits. That pedestal is **−0.43 pp/yr** here and **−0.55 pp/yr**
on the window [the evidence base](evidence-base.md) records.

| Fund | alpha %/yr | **vs VTI** | *t* | MDE₈₀ | Mkt | SMB | HML | RMW | CMA | Mom | R² |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **SCHD** | −0.80 | **−0.36** | −0.32 | 6.15 | +0.769 | +0.203 | **+0.246** | **+0.301** | **+0.312** | −0.011 | **0.874** |
| VYM | −1.64 | −1.20 | −1.36 | 2.99 | +0.806 | +0.031 | +0.302 | +0.136 | +0.258 | +0.007 | 0.949 |
| VIG | −2.20 | −1.77 | −1.63 | 3.36 | +0.825 | −0.029 | +0.053 | +0.269 | +0.139 | +0.057 | 0.928 |
| **NOBL** | **−5.38** | **−4.94** | **−2.62** | **5.10** | +0.810 | +0.154 | +0.128 | **+0.424** | +0.267 | −0.025 | 0.876 |
| DIVO | −0.24 | +0.19 | −0.16 | 3.72 | +0.746 | −0.032 | +0.094 | +0.173 | +0.242 | +0.050 | 0.898 |
| *VTI* | −0.43 | 0.00 | −2.29 | 0.47 | +0.996 | −0.004 | +0.022 | +0.030 | +0.001 | +0.000 | 0.999 |

**SCHD is 0.77 of the market plus a value, profitability and conservative-investment
tilt, and after that there is −0.36 pp/yr left over that the window cannot sign.** The
three tilts are the ones [decision 0005](../decisions/0005-factor-premia-closed-on-public-data.md)
already says public data cannot sign a premium for, and the ones the
[product audit](factor-products.md) already prices more cheaply. **NOBL is the one
resolved result in the family and it is negative**: −4.94 pp/yr against the pedestal
with a floor of 5.10, on the largest RMW loading in the table and the highest fee.

**The tax penalty is real, it is a fifth of what the framing suggests, and it is
qualified rather than ordinary.** From each fund's own SEC-standardised table — highest
federal individual rates, no state tax — five-year `before tax` minus
`after taxes on distributions`, with the control taken at the **same period end** so
nothing is compared across the 2024/2025 line:

| Fund | period end | drag | VTI, same period | **incremental** | qualified share of distributions |
| --- | --- | ---: | ---: | ---: | --- |
| **SCHD** | 2024-12-31 | 0.93 | 0.42 | **+0.51** | **100%**, DRD 98.60% |
| VYM | 2025-12-31 | 0.78 | 0.39 | +0.39 | 97.9% |
| DGRO | 2024-12-31 | 0.63 | 0.42 | +0.21 | effectively 100% |
| VIG | 2025-12-31 | 0.49 | 0.39 | +0.10 | 100% |
| NOBL | 2024-12-31 | 0.55 | 0.42 | +0.13 | **not found** |
| **DIVO** | 2025-12-31 | **1.44** | 0.39 | **+1.05** | **41.04%** |

**Over ten years, period-matched, SCHD trailed the broad market by 1.47 pp/yr before
tax and 1.85 pp/yr after taxes on distributions** — 11.03% against VTI's 12.50%, and
10.17% against 12.02%, both tables ending 2024-12-31. **Those are annualised returns and
they carry no second moment**, so they cannot be turned into a ten-year Sharpe
comparison; no monthly history exists before public N-PORT begins in 2019, and the
difference in the funds' volatilities is exactly what would decide it.

**The brief this audit was written against expected "forced income realisation in a
taxable account" to be a cost with no matching return, and it is — but the number is
+0.51 pp/yr for SCHD, not a percent or two, and the reason is that SCHD's distribution
is 100% qualified dividend income.** Its own annual report shows $2,469,946,295 of
ordinary income for the year to 2025-08-31, all of it designated qualified, on
$72,622m of net assets — a **3.40% distribution yield taxed at the qualified rate**.
At the stated investor's own rates (24%/15% federal plus California's 9.3%) that is a
shelter priority of **82.6 bp/yr against VTI's 25.0**, +57.6 bp incremental, which would
place it fourth in [the recommendation's queue](portfolio-recommendation.md) — above
developed ex-US equity and above RSST. **And that queue's own warning is the operative
one: priority ranks what a sheltered dollar saves and says nothing about whether the
asset should be held.** SCHD's marginal contribution is unmeasurable, so it is a sleeve
that would consume shelter it has not earned, which is exactly the ordering error the
queue was written to catch.

**DIVO is the one that nearly survives, and it is the covered-call family in a dividend
wrapper.** Its matched-volatility gap is **+1.52 pp/yr**, the only positive one here —
and its incremental tax drag is **+1.05 pp/yr**, because only **41.04%** of its
distributions are qualified. Amplify's own figures say the same thing from the other
side: a **1.51% SEC yield against a 4.82% distribution rate**, with the issuer's footnote
stating that the SEC yield "reflects the income earned from dividends – excluding option
income". The gap is option premium and it is not qualified. **After tax, +1.52 becomes
about +0.47, against an MDE₈₀ of 7.09.** Verdict `unresolved`, and the reason it is not
`rejected` alongside the other option-income funds in §2 is that its up/down betas are
**0.745 and 0.669** — mild genuine protection, the opposite ordering to PUT's 0.45/0.86.

**Nothing in this family protects on the downside.** Up-market and down-market beta from
one regression, so the difference carries a standard error: SCHD **0.786 up, 0.807
down**; VYM 0.753/0.850; NOBL 0.842/0.861. Dividend funds are lower-beta in both
directions and no more defensive in one than the other.

**Verdict: `dominated`, not `rejected`.** SCHD costs six basis points, delivers exactly
the exposures it says it does, and over its measurable history trailed VTI by an amount
this window cannot distinguish from zero. What is not in doubt is that its record is
explained by HML, RMW and CMA at an R² of 0.874, and that the same exposures are
available more cheaply — so it is a packaging decision rather than a return source. NOBL
is `rejected`. DIVO is `unresolved`.

---

## 5. REITs — partly a distinct asset class, and the distinct part has put-writing's shape

**The prior this was written to test was that REITs are not a distinct asset class once
you control for small-cap value and duration. Half of that is falsified.**

| Fund | fee | excess %/yr | vol | Sharpe | ρ to VTI | **unlevered gap** | **matched gap (5)** | 95% CI | MDE₈₀ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| **VNQ** | 0.13% | 3.05 | 19.46 | **0.157** | +0.839 | **−9.69** | **−8.90** | **[−16.64, −1.16]** | 9.82 |
| SCHH | 0.07% | 1.20 | 19.90 | 0.060 | +0.828 | −12.23 | −11.03 | **[−19.91, −2.14]** | 11.27 |
| USRT | 0.08% | 4.25 | 19.80 | 0.215 | +0.838 | −8.53 | −7.91 | [−16.01, +0.19] | 10.27 |

**Two of the three intervals exclude zero** — the only such intervals anywhere in this
audit — and both point estimates still sit just below their own 80%-power floor, so
these are detections at less than 80% power and must be described as that. **A REIT fund
carried a fifth of the market's Sharpe ratio at higher volatility over the only window
that can be measured.**

**The spanning test, run rather than asserted.** The duration leg is **TLT's own Item
B.5 return** — an investable, net-of-fee long-Treasury total return on exactly the same
months, which is the first time this repository has used anything but a modelled `GS10`
proxy for duration.

| Fund | model | alpha %/yr | *t* | MDE₈₀ | residual vol %/yr | R² | duration loading |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| VNQ | CAPM | −9.21 | −2.11 | 10.84 | 10.75 | 0.701 | — |
| VNQ | FF3 | −9.37 | −2.65 | 8.81 | 10.07 | 0.737 | — |
| **VNQ** | **FF3 + duration** | **−5.55** | −1.64 | 8.41 | **8.60** | **0.809** | **+0.406** |
| SCHH | FF3 + duration | −7.60 | −1.71 | 11.08 | 9.52 | 0.772 | +0.391 |
| USRT | FF3 + duration | −5.01 | −1.28 | 9.71 | 9.03 | 0.797 | +0.361 |

**Duration is a real and material part of a REIT fund** — a loading of +0.36 to +0.41 on
a long-Treasury ETF, worth 7 points of R² — and once it is in the model the REIT "alpha"
stops being distinguishable from zero. **But the residual is not small.** VNQ keeps
8.60 pp/yr of volatility that market, size, value and duration together do not explain,
out of 19.46 total. **REITs are about four-fifths spanned and one-fifth not**, and
calling them "not a distinct asset class" overstates what the regression says.

**The long window, and why it does not settle it either.** The only free documented
long real-estate equity return this search found is Ken French's `RlEst` industry
portfolio, monthly from 1926-07. It is **not a REIT index** — it is SIC-coded
real-estate operating companies, two firms in 1926 and 28 in 2025 — and the first thing
to do with a proxy is measure it: **correlation +0.797 with VNQ over the 81 months both
exist, at a tracking difference of 7.61 pp/yr.** That is far too loose to carry a
verdict about REITs, and this paragraph is context rather than evidence.

| Window | months | RlEst excess %/yr | vol | Sharpe | market Sharpe | FF3 alpha | *t* | MDE₈₀ | + duration loading |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1926-07…2025-12 | 1194 | 7.08 | 33.39 | 0.212 | 0.451 | −5.12 | −2.78 | 4.57 | +0.074 |
| **1963-07…2025-12** | 750 | 5.43 | 26.27 | **0.207** | 0.462 | **−6.66** | **−3.31** | **5.00** | +0.070 |
| 1990-01…2025-12 | 432 | 6.21 | 25.95 | 0.239 | 0.583 | −5.61 | −2.16 | 6.45 | −0.004 |

**On this proxy the alpha is resolved and negative on every window** — the only resolved
negative alpha this study produced with more than a hundred months behind it — and
**adding duration changes nothing at all** over sixty years, which contradicts what the
N-PORT window shows and is a warning that the +0.406 loading is a 2019–2026 fact about a
rate cycle rather than a structural property.

**What is genuinely new is the payoff shape, and it is the one §2 rejected.**

| Fund | up beta | **down beta** | asymmetry | *t* |
| --- | ---: | ---: | ---: | ---: |
| **VNQ** | **0.800** | **1.123** | **+0.322** | +1.19 |
| SCHH | 0.754 | 1.182 | +0.429 | +1.31 |
| USRT | 0.766 | 1.192 | +0.426 | +1.34 |
| *PUT index, from §2* | *0.45* | *0.86* | *+0.41* | — |

**A REIT fund gave 80% of the market's upside and 112% of its downside.** That is the
same asymmetry §2 measured on a put-writing index and rejected the whole
volatility-risk-premium family for — with the difference that put-writing is *sold* as
buying that shape in exchange for a premium, and a REIT fund is sold as
diversification. The *t* statistics are 1.2 to 1.3, so the asymmetry is not resolved
either; but the sign is the same in all three funds and it is the opposite of what a
diversifier is supposed to do.

**Tax makes it worse and by a measured amount.** VNQ's five-year distribution drag is
**1.00 pp/yr against VTI's 0.39** at the same period end, +0.61 incremental, because
REIT distributions are ordinary income: 75.5% ordinary and 24.5% return of capital in
the year to 2026-01-31, no long-term gain at all. **Section 199A is not in that figure
and it runs in the REITs' favour** — a REIT dividend eligible for the 20% deduction is
taxed below the ordinary rate, the split was searched for in all three funds' annual
reports and is **not found**, so +0.61 is an upper bound.

**Verdict: `dominated`.** Cheap, liquid, genuinely only four-fifths spanned, and it
bought a fifth of the market's Sharpe ratio while delivering a payoff shape this
repository has already rejected once under a different name.

---

## 6. Buffer and defined outcome — the cap is the product, and it is priced here

**This is the largest and most heavily marketed of the four families and it is the one
that can be settled without any fund data at all**, because its payoff is a contract and
the terms are filed.

**What is actually bought.** A defined-outcome fund holds FLEX options on the reference
asset's **price**. From Innovator's own 497K for PJUL, quoted rather than paraphrased:
*"the Cap and Buffer will be provided on a price return basis … and the Fund will not
receive the benefit of any dividends."* The buffer applies only over a **full** outcome
period held start to finish. And across periods, from the same document: *"over multiple
Outcome Periods, the Fund may have losses that exceed those of the Underlying ETF."*

**The terms these funds have actually offered**, each figure from that outcome period's
own filed summary prospectus:

| Fund | outcome periods | buffer | **mean cap** | median | min | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **PJUL** | 9, 2018–2026 | 15.0% | **11.98%** | 12.09% | 7.80% | 17.42% |
| **POCT** | 7, 2019–2025 | 15.0% | **12.83%** | 11.81% | 9.16% | 20.72% |

**Neither fund has ever offered a cap as wide as its buffer.** Pricing that against the
realised distribution of twelve-month S&P **price** returns — Goyal–Welch's `CRSP_SPvwx`,
the CRSP value-weighted return excluding dividends, which is the correct input and the
one a comparison against a total-return index silently gets wrong:

| Terms | window | protection received | upside sold | net option value | forgone dividend | fee | **total vs holding the index** |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| PJUL: buffer 15%, cap 11.98% | 1926-07…2025-12 | 3.01 | 5.76 | **−2.74** | 3.99 | 0.79 | **−7.53** |
| PJUL | 1990-01…2025-12 | 1.97 | 4.84 | **−2.87** | 2.26 | 0.79 | **−5.92** |
| PJUL | 2010-01…2025-12 | 0.88 | 4.96 | **−4.09** | 2.17 | 0.79 | **−7.04** |
| POCT: buffer 15%, cap 12.83% | 1926-07…2025-12 | 3.01 | 5.39 | **−2.37** | 3.99 | 0.79 | **−7.16** |
| POCT | 1990-01…2025-12 | 1.97 | 4.44 | **−2.47** | 2.26 | 0.79 | **−5.52** |
| POCT | 2010-01…2025-12 | 0.88 | 4.48 | **−3.61** | 2.17 | 0.79 | **−6.56** |

**The option package alone loses money before any fee is charged**, by 2.4 to 4.1 pp/yr:
the upside sold is worth roughly twice the protection received, on every window. Add the
dividend the wrapper cannot pass through and the fee, and the structure costs **5.5 to
7.5 pp/yr against simply holding the thing it references.** Over 1183 overlapping
twelve-month windows since 1926-07, **44.9% of price returns exceeded PJUL's mean cap**,
30.6% were negative at all, and only 11.1% fell through the 15% buffer entirely. **The
cap binds four times as often as the buffer pays out.**

**Now the funds' own filed returns, which are a disjoint measurement.**

| Fund | all-in cost | months | Sharpe | ρ | **unlevered growth gap** | **matched gap (5)** | MDE₈₀ | up beta | down beta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **BUFR** | **0.95%** | 68 | 0.722 | +0.966 | **−4.41** | −0.09 | 3.73 | 0.554 | 0.590 |
| BUFD | 0.95% | 63 | 0.528 | +0.952 | −5.05 | −1.00 | 4.38 | 0.404 | 0.406 |
| **PJUL** | **0.79%** | 74 | 0.747 | +0.940 | **−4.06** | **+1.91** | 6.64 | **0.482** | **0.431** |
| **POCT** | 0.79% | 74 | 0.806 | +0.936 | **−4.15** | **+2.95** | 6.01 | **0.443** | **0.380** |

**The realised growth shortfall of −4.06 to −4.41 pp/yr lands inside the −5.5 to −7.5
pp/yr the option arithmetic predicts, and the two share no data.** One is a century of
index price returns and a filed cap schedule; the other is six years of fund-reported
total returns. That agreement is the finding, and the funds' six years were, if
anything, favourable ones: two of PJUL's outcome periods carried caps well above its own
historical mean and two equity drawdowns arrived inside the window.

**Three things run the other way and are recorded rather than buried.**

*The asymmetry is the right way round.* PJUL's up beta is 0.482 and its down beta 0.431;
POCT's are 0.443 and 0.380. That is the **opposite** ordering to put-writing's 0.45/0.86
— these funds really do give up less on the downside than the upside. The asymmetry is
not resolved (*t* of −0.82 and −0.78), but the sign is right in both funds and it is a
genuine structural difference from §2's family.

*The tax treatment is unusually good.* PJUL's and POCT's own prospectus tables report a
five-year `after taxes on distributions` return **equal to their before-tax return** — a
distribution drag of exactly **0.00** against VTI's 0.42, because a FLEX-option fund
distributes almost nothing. They need no shelter at any weight, which in
[the recommendation's queue](portfolio-recommendation.md) is the position a bullion
trust occupies.

*Equation (5) says PJUL and POCT beat VTI.* Their matched-volatility gaps are **+1.91
and +2.95 pp/yr**. This is where the two comparisons in §4's table earn their place:
matched volatility means levering an 8% instrument to 17%, and what is being levered is
a **capped** payoff, so a 2× position sells the upside at half the index move. At the
weight anyone actually holds — one for one — the same funds lost **4.06 and 4.15
pp/yr of growth**, and growth is what
[decision 0008](../decisions/0008-growth-decides-crra-reports.md) makes deciding. Both
matched gaps are also well inside their own floors of 6.64 and 6.01.

**Verdict: `rejected`, on the option arithmetic rather than on the record.** The record
is unresolved in both directions; the arithmetic is not, and it is confirmed by the
record to within the record's resolution. Two of the four cost terms — the forgone
dividend of 2.2 to 4.0 pp/yr and the fee of 0.79 to 0.95 — are certain, recurring, and
independent of what markets do.

---

## 7. Spot bitcoin — it clears the bar, and the bar establishes nothing

**Start with what does not exist.** IBIT and FBTC are Delaware statutory trusts
registered under the Securities Act. From IBIT's own 10-K: *"The Trust is not registered
as an investment company for purposes of U.S. federal securities laws … Consequently,
the owners of Shares do not have the regulatory protections provided to investors in
registered investment companies."* Their complete EDGAR filing histories contain
**no N-PORT, N-CSR or N-CEN of any kind**. **There is therefore no fund-reported monthly
total return for spot bitcoin anywhere**, which is the source every other verdict in this
audit rests on, and the audit has to reach for a price series instead.

The one it reaches for is FRED's `CBBTCUSD`, and what it is matters:

- **Source Coinbase, one venue**, daily including weekends, and the series' only
  documentation of its observation convention is the sentence *"All data is as of 5 PM
  PST."*
- **It is not the index either trust prices its net asset value against**, and the two
  trusts do not even use the same one: IBIT uses the **CME CF Bitcoin Reference Rate –
  New York Variant** (CF Benchmarks Ltd., FCA-regulated, a 3–4 p.m. ET volume-weighted
  median across eight venues); FBTC uses the **Fidelity Bitcoin Reference Rate**, whose
  methodology is written by an affiliate of its own sponsor. Neither is published free.
- **Coinbase prohibits redistribution**, so its bytes stay in the uncommitted cache and
  only the hash is manifested — the same posture as the ICE BofA and LBMA series.
- [Decision 0002](../decisions/0002-no-research-grade-free-price-source.md) does not
  forbid it, and the reason is the one the gold acquisition established: that decision
  bans free price feeds because they drop distributions and mishandle corporate actions,
  and **bitcoin pays no distribution and has no corporate action.** Both trusts' 10-Ks
  confirm the first directly. Everything else about it is exploratory.

**The measurement**, 137 months, 2015-02…2026-06, month-end, excess of the French cash
rate:

| Base | months | window | BTC excess %/yr | vol %/yr | BTC Sharpe | **ρ** | base Sharpe |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| **French `Mkt-RF`** | **137** | 2015-02…2026-06 | **71.14** | **71.48** | **0.995** | **+0.342** | 0.799 |
| VTI, net | 81 | 2019-07…2026-03 | 43.87 | 63.60 | 0.690 | +0.531 | 0.684 |

**At `|rho| = 0.342` equation (4) is the right instrument and it passes decisively.**

| Exposure `L` | threshold `L rho sigma_p` | BTC Sharpe | margin | clears | usable |
| ---: | ---: | ---: | ---: | --- | --- |
| 1.00 | +0.0534 | 0.995 | **+0.942** | yes | **yes** |
| 1.50 | +0.0800 | 0.995 | **+0.915** | yes | **yes** |

**That is a pass, it is stated as one, and it is the least informative number on this
page.** Four things it does not establish, in order of how much they matter.

**First, and decisively: the admission rule takes an expected excess return as an input,
and for bitcoin that input has no defensible estimate.** Every figure above substitutes
the realised mean of the last eleven years for a forecast. The threshold inverted is the
only forward-looking statement available: equation (4) clears whenever the forward
excess return exceeds `L rho sigma_p sigma_d`, which at this correlation and volatility
is **3.81%/yr at `L = 1` and 5.72%/yr at `L = 1.5`** — below the equity premium, and low
*because* the correlation is low. **Whether bitcoin's forward excess return exceeds
5.72%/yr is the entire question and nothing in this repository can answer it.** A sleeve
whose expected return cannot be estimated is not the same thing as a sleeve whose
expected return is zero, and the honest verdict is `unresolved` rather than either.

**Second, the correlation is not stable and it moved the wrong way.** +0.342 over 137
months against the market factor; **+0.531 over the 81 months a net fund control
exists** — across the boundary at which equation (4) stops being usable at all. The
longer window is the one that can resolve a correlation and is the one quoted; the
shorter one is a warning that the input the pass depends on is drifting toward the
region where the pass would be inadmissible.

**Third, equation (5) says nothing at all.** Over the 81 months both series exist, the
matched-volatility gap against VTI is **+0.10 pp/yr, 95% interval [−12.18, +12.38], with
an MDE₈₀ of 15.58.** **Bitcoin's risk-adjusted return over that window is
indistinguishable from the S&P's, and the window could not have detected a fifteen-point
annual difference.** Its Sharpe of 0.690 against VTI's 0.684 is a coincidence of two
noisy estimates, not a result.

**Fourth, holdability.** Over the same 137 months bitcoin's worst month-end drawdown was
**−75.4%** against US equity's −24.8%. Equation (4) is a first-order condition on a
twice-differentiable objective and **contains no drawdown term at all**. The
[levered-equity result](capital-efficiency-and-breadth.md) is the same lesson from the
other direction: the growth optimum on a century of US equity is 2.2×, and it is refused
because it drew down 99.3% and spent 24.7 years under water. Here the plug-in
growth-optimal overlay notional is **1.318 units, 1.199 after shrinking for eleven years
of estimation error** — and the shrinkage barely moves it, because
`f* = S²T / (S²T + 1)` does almost nothing when the plug-in Sharpe is near 1.0, which is
precisely when it ought to do most.

**The vehicles, from their own filings.** IBIT: 0.25% sponsor fee, initial 0.12% waiver
on the first $5bn **expired 2025-01-10**, 734,261 BTC and $43.4bn of net assets at
2026-06-30, custody at Coinbase Custody with Anchorage as an additional custodian.
FBTC: 0.25% charged on bitcoin holdings rather than dollar net assets, waiver expired
2024-07-31, 174,383 BTC and $10.3bn at the same date, custody at Fidelity Digital
Assets — **an affiliate of its own sponsor**, and a different concentration risk rather
than a smaller one. Neither trust distributes anything; both pay the sponsor's fee by
selling or delivering bitcoin, which is a taxable event for holders that no distribution
statement reports. **Whether the 28% collectibles rate applies is `not found`** — the
words "collectible" and "28%" appear nowhere in either trust's tax discussion, and
EDGAR full-text search over IBIT's entire filing history returns zero hits. The filings
say only that bitcoin is property that may be held as a capital asset and that the
treatment "is uncertain" and may change with retroactive effect. **Do not attribute a
collectibles position to these filings, in either direction.**

**Verdict: `unresolved`.** It clears the admission threshold by a wide margin on the
only window able to score it; the threshold's input is unestimable; the correlation that
produces the low bar is drifting upward; the matched-volatility control resolves
nothing; and the asset drew down three-quarters of its value inside the measured
window. **Refusing to run the test would have been an omission. Reporting the pass
without the four paragraphs above would be worse.**

---

## 8. Fixed income — the shelf is cheap, the exposure is one engine, and TIPS are not a second one

**This section closes the last open row of "any asset outside equity and cash"**
([search coverage](search-coverage.md)). It was the same kind of failure as gold and
REITs: the long measured bond leg was **already in this repository's cache and
manifests** and no experiment had read it, and the investable leg was one N-PORT query
away. Computations are in
[`studies/fixed_income_shelf.py`](../../research/src/portfolio_edge/studies/fixed_income_shelf.py)
and
[`_fixed_income_tables.py`](../../research/src/portfolio_edge/studies/_fixed_income_tables.py);
fee facts with an accession on every figure are in
[`data-manifests/fixed_income_shelf/product_facts.json`](../../research/data-manifests/fixed_income_shelf/product_facts.json)
and the N-CEN provenance beside it.

### 8.1 The shelf on total cost, and SCHP specifically

Eighteen bond and TIPS funds, on the same basis the core-beta audit used: the 497K fee
table, Form N-CEN Item C.6 securities-lending income accruing to shareholders, and Item
C.8 waiver and recoupment flags. Sixteen fee tables were read here; BND's and AGG's are
already in the core-beta audit. **No fund on this shelf has a waiver, an expense
limitation or an acquired-fund-fees line**, so net equals gross everywhere and there is
no recoupment overhang — checked by searching all sixteen documents for `waiv`,
`recoup`, `recaptur`, `restat`, `contractually agreed`, `expense limitation` and
`until at least`, with every hit boilerplate in the performance section.

| ticker | exposure | fee bp | lending bp (median) | **net cost bp** | prospectus |
| --- | --- | ---: | ---: | ---: | --- |
| **SCHP** | broad US TIPS, WAM 7.1y, duration 6.3y | **3** | 0.01 | **2.99** | 2026-04-28 |
| STIP | 0–5y US TIPS | 3 | 0.06 | 2.94 | 2026-02-27 |
| VTIP | 0–5y US TIPS | 3 | does not lend | 3.00 | 2026-01-28 |
| SPIP | broad US TIPS | 12 | 0.61 | 11.39 | 2025-10-31 |
| **TIP** | broad US TIPS | **18** | 0.08 | **17.92** | 2026-02-27 |
| LTPZ | 15+y US TIPS | 20 | does not lend | 20.00 | 2025-10-31 |
| SCHO / VGSH | 1–3y Treasury | 3 | 0.00 / does not lend | 3.00 | 2026-04-28 / 2025-12-19 |
| SCHR / VGIT | 3–10y Treasury | 3 | 0.05 / does not lend | 2.95 / 3.00 | 2026-04-28 / 2025-12-19 |
| VGLT | 10–25y Treasury | 3 | does not lend | 3.00 | 2025-12-19 |
| GOVT | 1–30y Treasury | 5 | 0.05 | 4.95 | 2026-02-27 |
| TLT | 20+y Treasury | 15 | 0.00 | 15.00 | 2026-06-29 |
| BND / AGG | US aggregate | *not read here* | does not lend / 0.26 | — | — |
| VCIT | 5–10y IG corporate | 3 | does not lend | 3.00 | 2025-12-19 |
| LQD | IG corporate | 14 | 1.94 | 12.06 | 2026-06-29 |
| **HYG** | US high yield | **49** | **9.19** | **39.81** | 2026-06-29 |

**The answer on SCHP is that it is the right vehicle and the wrong question.** At a net
2.99 bp it is the cheapest broad TIPS fund on the shelf and **TIP charges six times as
much for the same asset** — 17.92 bp against 2.99, on exposures whose monthly returns
correlate **+1.000 to three decimal places** over the seventy-nine months the shelf
shares. A 15 bp difference on identical risk is the largest certain quantity anywhere in
this section, and it is also the only one: everything below concerns whether the exposure belongs in the portfolio at
all, and none of it depends on which of these two wrappers is used.

BND and AGG carry no fee here because they are already in the **core-beta shelf**'s
cost audit ([portfolio recommendation](portfolio-recommendation.md)) and re-reading their
fee tables would put the same fact in two places. Their N-CEN lending is reported above
because the fixed-income manifest holds it: **BND answers Item C.6.a "No" in every year
on file**, AGG earns a median 0.26 bp.

**Securities lending is negligible for governments and material for credit.** SCHP earns
0.01 bp a year from lending; HYG earns a median 9.19 bp, which is a fifth of its fee.
The pattern is the one the core-beta audit found and it runs the same way: the cheaper
the collateral is to borrow, the less the fund makes lending it.

**Not found, and recorded rather than estimated.** No fund on this shelf publishes a
portfolio **real yield**, in its 497K or its annual report. Only SCHP publishes an
effective duration for its own portfolio; for VTIP, TIP, STIP, SPIP and LTPZ the only
maturity figure published is the **target index's**, which is not the fund's, and it is
labelled as the index's wherever it appears. Section 8.5 therefore prices the exposure
from the Treasury's own real curve rather than from a fund's portfolio yield.

### 8.2 The bond leg, and how far back it now reaches

Two series, never spliced, and neither is a substitute for the other.

| leg | source | coverage | months | investable? | fee |
| --- | --- | --- | ---: | --- | --- |
| **long Treasury `ltr`** | Goyal–Welch, measured total return | 1926-01…2025-12 | **1,200** | no | gross |
| **long IG corporate `corpr`** | Goyal–Welch, measured total return | 1926-01…2025-12 | **1,200** | no | gross |
| **standalone credit `corpr − ltr`** | derived from the two above | 1926-01…2025-12 | 1,200 | no | gross |
| the eighteen funds above | Form N-PORT Item B.5 | 2019-07…2026-05 | **79 common** | **yes** | net of the fund's own |
| the `GS10` proxy everything used before | **modelled** from a yield | 1963-07…2026-06 in excess of French `RF` | 756 | no | none |

**`ltr` and `corpr` were in this repository the whole time.** They are columns of the
Goyal–Welch predictor file, which was landed on 2026-08-16 and manifested, and which
[capital efficiency §3](capital-efficiency-and-breadth.md) already reads for its
multi-asset panel. No experiment had used them as a bond leg, and every diversification
result in the programme was computed against a modelled `GS10` proxy instead. **That is
the sixth source recorded here as absent that turned out to be published, and the first
that had already been downloaded.**

**The proxy and the measured series are not interchangeable, and the size of the gap is
measurable.** On the 750 months both cover, 1963-07…2025-12, they correlate **+0.663**;
the proxy runs at **6.73%/yr** of volatility against `ltr`'s **10.11%**, and **1.63%/yr**
of excess return against **2.47%**. `GS10` is a ten-year point and `ltr` is a roughly
twenty-year index, so most of that is an exposure difference rather than an error in
either — but a page that says "bonds" and means one of them has not said which.

**What the investable window can and cannot resolve.** Seventy-nine months, 2019-09 to
2026-03, is the whole of it, and it is a bond bear market: **fifteen of the eighteen funds
have a negative excess return over it**, the exceptions being the two 0–5 year TIPS funds
and high yield, and the minimum detectable effect on a matched-volatility gap runs
**6.7 to 21.0 pp/yr**. It resolves nothing about returns. It
resolves correlations to two decimal places, which is the same asymmetry
[the evidence base](evidence-base.md) records everywhere else.

### 8.3 One engine, and TIPS are inside it

| pair | ρ, 79 investable months | reading |
| --- | ---: | --- |
| SCHP / BND | **+0.851** | one engine |
| SCHP / VGIT | +0.776 | one engine |
| SCHP / GOVT | +0.761 | one engine |
| SCHP / TLT | +0.705 | mostly one engine |
| LTPZ / VGLT | +0.846 | one engine |
| VTIP / SCHO | +0.585 | partly distinct, and both are near-cash |
| LQD / VGIT | +0.743 | mostly one engine |
| modelled 10y TIPS / modelled 10y nominal, 275 months 2003-02…2025-12 | **+0.798** | one engine |

**Counting a TIPS sleeve beside a nominal bond sleeve is the same fake breadth that
counting credit beside Treasuries was.** [Capital efficiency §3](capital-efficiency-and-breadth.md)
already rejects the second at ρ = +0.83; the first is +0.76 to +0.85 on investable funds
and +0.80 on a modelled series with three and a half times the history.

### 8.4 The question that decides: is TIPS' correlation to equity stable where nominal bonds' is not?

The rationale for a TIPS sleeve is that it responds to a different state variable, so its
correlation to equity should be stable where the nominal bond's is famously not.
**Measured, that is false in this window, and false in the direction opposite to the
one the rationale predicts.**

Correlation to the US market excess return, non-overlapping 60-month blocks, block length
fixed before the series were seen.

| series | window | months | full ρ | blocks | span | sd |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| long Treasury `ltr` | 1963-07…2025-12 | 750 | +0.097 | +0.18 +0.36 +0.35 +0.42 +0.28 +0.49 +0.42 **−0.30 −0.32 −0.27 −0.30 −0.09** | **0.802** | 0.330 |
| 10y nominal, modelled | 1963-07…2026-06 | 756 | +0.136 | +0.34 +0.51 +0.34 +0.34 +0.24 +0.37 +0.31 **−0.17 −0.14 −0.22 −0.18 +0.03** | 0.734 | 0.264 |
| standalone credit | 1963-07…2025-12 | 750 | +0.307 | +0.23 +0.04 +0.40 −0.03 −0.21 −0.28 −0.17 **+0.52 +0.67 +0.49 +0.63 +0.69** | 0.974 | 0.364 |
| **10y TIPS, modelled** | **2003-02…2026-06** | **279** | +0.131 | −0.14 +0.09 +0.02 +0.34 | 0.481 | 0.200 |

**The nominal bond's sign flip is measured and it is large.** Seven consecutive positive
blocks then five consecutive negative ones, a span of **0.802**; put compactly, ρ =
**+0.352** over 1963-07…1998-06 and **−0.206** over 1998-07…2025-12 on `ltr`, and +0.322
and −0.106 on the modelled ten-year. **That break date was chosen by eye from the block
table and is reported as descriptive** — the blocks are the pre-specified statistic and
the split only restates them. The pattern is the same shape as the trend/Treasury result a
concurrent audit found: **the bond has breadth in the era it has no return and return in
the era it has no breadth.** It is the strongest single argument against a fixed-income
sleeve in this repository.

**TIPS cannot be tested against it, and where they can be tested they are worse.** The
security did not exist before 1997 and the Treasury's real curve begins 2003-01, so
there is **no observation of a TIPS return in the era when nominal bonds' correlation to
equity was positive**. That is a hard limit, not a gap in the search. On the only window
where both exist:

| series, identical months and identical block edges, 275 months 2003-02…2025-12 | ρ to equity | SE | blocks | span | sd |
| --- | ---: | ---: | --- | ---: | ---: |
| long Treasury `ltr` | **−0.176** | 0.059 | −0.19 −0.29 −0.32 −0.09 | **0.229** | **0.103** |
| 10y nominal, modelled | **−0.076** | 0.060 | −0.12 −0.21 −0.18 +0.04 | 0.254 | 0.114 |
| **10y TIPS, modelled** | **+0.131** | 0.060 | −0.14 +0.09 +0.02 +0.34 | **0.481** | **0.200** |
| long IG corporate `corpr` | +0.190 | 0.058 | −0.01 +0.10 −0.03 +0.38 | 0.411 | 0.190 |
| standalone credit | +0.569 | 0.041 | +0.57 +0.51 +0.62 +0.69 | 0.183 | 0.078 |

**TIPS are more equity-correlated than nominal Treasuries and their correlation is less
stable, on the same months, by a factor of two on both counts.** The gap in the
full-sample correlation, +0.131 against −0.076, is **3.5 standard errors** wide. The
investable funds say the same thing at a wider duration range and with volatility held
roughly equal: **SCHP +0.623 at 5.71%/yr of volatility against GOVT +0.277 at 5.34% and
VGIT +0.274 at 4.94%**, and at the short end **STIP +0.571 and VTIP +0.566 against SCHO
+0.144 and VGSH +0.166**. It is not a duration artefact; it appears at both ends of the
curve at matched volatility.

Three qualifications, none of which rescues the hypothesis. The TIPS series is
**modelled** from FRED `FII10` and carries the Treasury's own documented **2008-12-01
methodology break**, when the real curve moved to most-recently-auctioned issues as knot
points. Its one modelling choice, the reference-CPI lag, is immaterial: moving it from
the statutory three months to zero moves the correlation to equity from +0.131 to
+0.138. And the real yield was **negative in 45 of 283 months**, which the repository's
existing par-bond helper refuses to price — that guard is correct for a nominal Treasury
and had to be replaced by a documented limit for an indexed one.

### 8.5 The exposure, not the wrapper: what a TIPS buyer is actually buying

| quantity | value | as of | source |
| --- | ---: | --- | --- |
| 10-year **real** constant-maturity yield | **2.35%/yr** | 2026-07 | FRED `FII10`, the monthly average of Treasury's daily par real curve |
| 10-year **nominal** constant-maturity yield | 4.60%/yr | 2026-07 | FRED `GS10` |
| 10-year **breakeven** inflation | **2.28%/yr** | 2026-08-17 | FRED `T10YIE` |
| the same breakeven from the two monthly averages | 2.25%/yr | 2026-07 | derived |

**A TIPS buyer is buying a real 2.35%/yr and selling the inflation forecast.** Holding
the ten-year TIPS instead of the ten-year note wins if and only if realised inflation
exceeds **2.28%/yr** over ten years. It is a swap of one risk for another at a
market-set price, **not a higher expected return** — and the breakeven is not a forecast
either, because it contains an inflation risk premium and a TIPS liquidity premium of
unknown and time-varying sign. Nothing here predicts with it.

Treasury's own definition, read from
[the daily real yield curve page](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_real_yield_curve)
on 2026-08-17: *"Par real yields on Treasury Inflation Protected Securities (TIPS) at
'constant maturity' are interpolated by the U.S. Treasury from Treasury's daily par real
yield curve."* The reference index is set by
[31 CFR 356](https://www.ecfr.gov/current/title-31/part-356) — *"the monthly
non-seasonally adjusted U.S. City Average All Items Consumer Price Index for All Urban
Consumers"*, applied with a three-month lag (*"Ref CPI April 1, 1996 = 154.40, the
non-seasonally adjusted CPI-U for January 1996"*), read from eCFR on 2026-08-17.

### 8.6 Does any fixed-income sleeve clear its bar? No

Scored against `global_equity_core` on Experiment 010's own 420-month sample, first-order
at the 10% reference weight. The pipeline reproduces that experiment's credit ceiling —
`sigma_p**2` = **2.171 pp/yr** per unit weight — which is what licenses the comparison.

| bond leg | β to core | credit @10% | **pro rata @10%** | overlay @10%, unfinanced | overlay @10%, financed | MDE₈₀ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **modelled** `GS10` — Experiment 010's own leg | −0.018 | +0.221 | **−0.328** | +0.258 | +0.183 | 0.795 |
| **measured** long Treasury `ltr` | −0.092 | +0.237 | **−0.136** | **+0.450** | +0.375 | 0.868 |
| **measured** long IG corporate `corpr` | +0.117 | +0.192 | −0.147 | +0.439 | +0.364 | 0.727 |
| **measured** standalone credit | +0.209 | +0.172 | −0.597 | −0.011 | −0.086 | 0.538 |

**Under the funding rule the zero-leverage constraint actually permits — pro rata — no
bond leg comes close.** The best is −0.136 pp/yr against a +0.30 bar.

**Under financed overlay funding two legs clear the bar and neither is resolved.** The
measured Treasury leg reads **+0.450 pp/yr unfinanced and +0.375 after a 60 bp borrow
spread and a 15 bp fee**, against its own 80%-power floor of **0.868**. An estimate half
its detection floor is a statement about the window. The same is true of corporates at
+0.364 against 0.727. **`unresolved`, not a pass** — and the honest control does not
rescue it either. Equation (5) at that weight puts the overlay portfolio's Sharpe ratio
at **0.578 against the base's 0.545** — a gap of 0.033 which, multiplied by the portfolio's
own volatility, is the same +0.450 pp/yr already shown to sit at half its detection floor.
The control agrees with the marginal; neither resolves anything.

**The measured leg does move Experiment 010's cell, materially, and in the sleeve's
favour.** Pro rata, from −0.328 to −0.136; overlay, from +0.258 to +0.450. That is a
finding about the proxy, not about bonds: the modelled series understates both the excess
return (+2.54 against +4.30) and the volatility (6.19 against 9.73) of the exposure it
stands in for, and its credit ceiling is lower because its beta to the core is closer to
zero from the wrong side.

On the investable window every fund fails equation (5) against VTI and only six of
eighteen gaps are resolved — LTPZ −16.88, BND −17.29, AGG −17.26, LQD −14.32, VCIT
−12.86 and HYG −8.70, all against floors of 6.7 to 16.2 pp/yr. **SCHP reads −12.48 pp/yr
with a 95% interval of `[−24.22, −0.74]` against a floor of 14.89** — an interval that
excludes zero at less than 80% power, the same shape as VNQ and SCHH in §5, and it must
be described as that rather than as a detection.

**Verdict: `unresolved` for a Treasury or aggregate sleeve, `rejected` for a separate
TIPS sleeve.** The TIPS rejection does not rest on the return window at all, which
cannot resolve anything; it rests on two things the window *can* resolve. TIPS are +0.76
to +0.85 correlated with the nominal bond funds they would sit beside, so they are not a
second engine. And their correlation to equity is **higher** and **less stable** than
nominal Treasuries' on identical months, which is the opposite of the property the sleeve
is held for.

---

## Verified, assumed, open

**Verified.** Every fee, minimum, return, cap, buffer and distribution figure above is
from a named SEC filing or index file. The PUT/BXM regressions, every §§4–7 moment,
regression, piecewise beta, matched-volatility gap and cap valuation were computed here
rather than quoted. The cat bond multiples are from the Artemis deal directory.

**Assumed, and both assumptions are load-bearing.** That modelled expected loss — a
vendor cat-model output, and the optimistic input — is the right subtrahend for a cat
bond's gross excess return. And that a **fund-reported** Item B.5 return is comparable
across filers: Form N-PORT General Instruction G lets each filer use its own
methodology, so two funds' returns are not guaranteed to be computed alike. That
assumption underlies every number in §§4–6.

**Open, and each is a real gap.**

- Mitchell and Pulvino's piecewise betas, the CEF discount literature's alpha
  magnitudes, and the direct-indexing decay estimates were all **searched for and not
  reached** (403s and rate limits), so three verdicts rest on vehicle economics alone.
  Section 1256 character breakdowns for the option-income funds were not sourced.
  Whether a US person may hold a UCITS cat bond fund was not established and the PFIC
  treatment is reasoning rather than a citation.
- **The qualified-dividend, Section 199A and dividends-received split for VNQ, SCHH and
  USRT is not found** in any of the three funds' annual reports; it lives in each
  issuer's year-end tax-character statement, which was not retrieved. **This runs in the
  REITs' favour**, so §5's tax figures are upper bounds.
- **NOBL's qualified share is not found.** ProShares' N-CSR states only that the fund
  "designated up to the maximum amount".
- **SCHD's published 30-day SEC yield and trailing distribution yield are not found**:
  Schwab's fund pages returned HTTP 403 to an automated client and bot protection was
  not circumvented. The 3.40% used in §4 is **computed here** from the fund's own filed
  distribution total and net assets, and is labelled as computed everywhere it appears.
- **FT Vest's starting caps for the twelve funds inside BUFR and BUFD are not
  retrieved**, so no cap-pricing figure in §6 is attributed to BUFR; its buffer level
  (10%, not 15%) and its 0.95% all-in cost are.
- **There is no ten-year monthly return history for any fund here.** Public N-PORT
  begins with periods ending 2019-09-30. A ten-year realised volatility for SCHD, and
  therefore a ten-year Sharpe comparison against VTI, cannot be built from any primary
  source this repository holds. The ten-year figures in §4 are annualised returns from
  the funds' own prospectus tables and carry no second moment.
- **No TIPS return exists for the era that would decide the question in §8.4.** The
  security dates from 1997 and the Treasury's real curve from 2003-01, so there is no
  observation of a TIPS return in the era when nominal bonds' correlation to equity was
  positive. **This is a hard limit and no search can close it**, which is why §8's TIPS
  verdict rests on the correlation to the nominal leg and on the same-window comparison
  rather than on an era test that cannot be run.
- **No fund on the fixed-income shelf publishes a portfolio real yield**, and only SCHP
  publishes its own effective duration; the other five TIPS funds publish only their
  target index's maturity. §8.5 therefore prices the exposure from Treasury's own curve.
- **The TIPS series in §8.4 is modelled** from a constant-maturity real yield, not a
  measured index return, and it carries the Treasury's documented 2008-12-01 curve
  methodology break. The measured legs `ltr` and `corpr` are index returns gross of any
  fee and are **not investable**; the funds are investable and six years long. Nothing in
  §8 splices the two.
- **The measured window is one in which large-cap growth beat the market substantially**
  — the same window that produced six positive shrunk alphas in the
  [product audit](factor-products.md), all large-cap growth, none clearing its own
  threshold. A value-tilted dividend fund trailing over it is partly a statement about
  the decade, which is why the MDE₈₀ column exists and why not one gap in §4 is
  resolved.

---

## Consequence for this repository

1. **"Breadth is one engine" was a statement about the fund shelf, not about markets.**
   Cat bonds clear the admission bar at ρ ≈ 0.10 and have no financed wrapper; trend
   clears it and has one. That is the binding constraint.
2. **Catastrophe bonds enter the registry as `exploratory`, monitor rather than
   allocate**, with a stated review trigger: the new-issue multiple recovering above
   3.0× and the Brookmont vehicle reaching three years and $250m.
3. **The volatility risk premium is `rejected`** on live-only alpha of −0.09 to
   −0.88%/yr at ρ 0.86–0.95, and any future page quoting put-writing performance must
   state that history before 2007 is a backtest.
4. **A dollar-weighted return belongs beside every time-weighted one** for an
   interval-fund sleeve. SRRIX's 7.92% and its investors' ~1.8% are the same decade.
5. **Prefer a completion or small-cap fund whose securities-lending revenue accrues to
   shareholders**: 10.43 bp on VXF against 0.07 on VOO is small, certain, and free.
6. **The five ordinary families fail by five different mechanisms and none of the five
   is "the premium is small".** Dividend funds are a value-and-quality tilt whose record
   is 87% explained by its loadings, with a **+0.51 pp/yr** tax wedge that is *qualified*
   rather than ordinary — a fifth of what the usual framing implies. REITs are
   four-fifths spanned by market, size, value and duration and the remaining fifth
   delivers **112% of the market's downside against 80% of its upside**. Buffer funds
   sell more upside than they buy downside, by a factor of two, on every window since
   1926. Bitcoin passes on arithmetic and fails on the absence of an input. Fixed income fails
   on breadth: it is one engine with equity's correlation drifting through it.
7. **The correlation decides the instrument, and that is now enforced in code.**
   `choose_instrument` in
   [`retail_shelf.py`](../../research/src/portfolio_edge/studies/retail_shelf.py) refuses
   to describe equation (4)'s margin as a verdict above `|rho| = 0.5`. Every long-only
   equity sleeve a retail investor is offered sits above that boundary, so **equation (4)
   is the wrong instrument for most of the retail shelf** and the audit that used it
   would have passed all three families.
8. **A matched-volatility win is not a growth win, and for a capped payoff it is not
   even a portfolio.** PJUL and POCT beat VTI by +1.91 and +2.95 pp/yr under equation (5)
   and lost 4.06 and 4.15 pp/yr of growth at the weight anyone holds. Any future page
   quoting a matched-volatility gap must quote the unlevered one beside it.
9. **A TIPS sleeve is rejected, and not on its return.** SCHP is the cheapest broad TIPS
   fund on the shelf at a net 2.99 bp and TIP charges six times that for a +0.9997
   correlated exposure — but the vehicle question is the small one. TIPS correlate +0.76
   to +0.85 with the nominal bond funds they would sit beside, so they are not a second
   engine; and on identical months their correlation to equity is **+0.131 against the
   nominal ten-year's −0.076** and their five-year-block dispersion is **twice** as
   large. **The one property the sleeve is held for is the one it does not have here.**
10. **`ltr` and `corpr` replace the `GS10` proxy as the repository's bond measurement,
   and the substitution is material.** Experiment 010's bond cell moves from −0.328 to
   −0.136 pp/yr pro rata and from +0.258 to +0.450 financed-overlay at the 10% reference
   weight. The proxy understates the exposure's excess return by 1.76 pp/yr and its
   volatility by 3.5 pp/yr. **Any page still quoting a `GS10`-derived bond figure should
   say so in the same sentence**; [setting the equity share](setting-the-equity-share.md)
   is the largest remaining one.
11. **Two sources were recorded as absent here and were not.** French's 49-industry file
   carries a documented real-estate equity total return from 1926-07, free, and FRED
   carries a bitcoin price from 2014-12. Both are now held and manifested. **That is the
   fourth and fifth time this has happened**, after Goyal–Welch, Shiller and gold; see
   [search coverage](search-coverage.md) §5 item 4. **The sixth is worse than any of
   them**: Goyal–Welch `ltr` and `corpr` are a hundred years of measured bond total
   returns that were already in this repository's cache and manifest, and every bond
   figure the programme has published was computed against a modelled proxy instead.
12. **The given universe is not the retail universe.** Every family
    [it names](#the-universe-this-page-was-given) is exotic; the four families a retail
    investor is actually pointed at were absent from it and from this repository entirely
    until 2026-08-17. **A universe assembled from what is interesting is not a
    universe.**
