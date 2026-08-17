# The alternative sleeves: which ones a retail investor can actually own

**Question.** Beyond equity, bonds, commodities and trend, the strategy universe in
`docs/the-plan.md` §F lists a dozen families this repository had never examined. For
each: does a retail-accessible vehicle exist, what does it cost all in, and does the net
result clear the admission bar `S_d > L rho sigma_p`?

**Decision it informs.** Whether the "one engine" finding in
[capital efficiency and breadth](capital-efficiency-and-breadth.md) is a fact about
markets or about the fund shelf.

**Out of scope.** Private markets (§G) and the exploratory families (§H). Nothing here
is promoted.

`as of 2026-08-16`. Every figure is from an SEC filing, an issuer document with its
retrieval date, or a computation on Cboe's own index files. **Where a source could not
be reached it says "not found" rather than an estimate.**

---

## Conclusion

**One family passes and it is constrained by its vehicle, not by its premium.**

| Family | Best retail vehicle | All-in fee | Net excess over cash | ρ to equity | Verdict |
| --- | --- | ---: | ---: | ---: | --- |
| **Catastrophe bonds** | Brookmont ILS ETF | 1.58% cap / **2.00% actual** | **+2.0 to +2.4%/yr** | ~0.10 | **passes — IRA only** |
| Merger arbitrage | MERFX I / ARB | 1.26% / 0.76% | +0.30 to +0.71%/yr (5yr) | low, rises in crashes | **borderline** |
| Volatility risk premium | JEPI / XYLD / QYLD | 0.35–0.60% | **alpha −0.09 to −0.88%/yr** | **0.86–0.95** | **rejected** |
| Closed-end fund discounts | FCEF | **3.69%** | +0.29 pp/yr vs its own CEF benchmark | high | **rejected**, under-evidenced |
| Securities lending | embedded in any fund | — | **0.07–10.4 bp/yr** | 1.0 | **not a sleeve** |
| Direct indexing | Frec 0.09% / $20k | 0.09–0.40% | not sourced | **≈1.0 by design** | **category error** |

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

## Verified, assumed, open

**Verified.** Every fee, minimum and return above from a named SEC filing or index file.
The PUT/BXM regressions were computed here on Cboe's daily files and Ken French's
factors, not quoted. The cat bond multiples are from the Artemis deal directory.

**Assumed.** That modelled expected loss — a vendor cat-model output, and the optimistic
input — is the right subtrahend for a cat bond's gross excess return.

**Open, and each is a real gap.** Mitchell and Pulvino's piecewise betas, the CEF
discount literature's alpha magnitudes, and the direct-indexing decay estimates were all
**searched for and not reached** (403s and rate limits), so three verdicts rest on
vehicle economics alone. Section 1256 character breakdowns for the option-income funds
were not sourced. Whether a US person may hold a UCITS cat bond fund was not established
and the PFIC treatment is reasoning rather than a citation.

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
