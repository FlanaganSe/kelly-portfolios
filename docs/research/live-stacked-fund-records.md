# Live stacked funds: what the second dollar has actually paid

**Question.** [Capital efficiency](capital-efficiency-and-breadth.md) prices the funding
rule and [loading comparability](loading-comparability-and-wrapper-exposure.md) measures
what a stacked wrapper delivers. Neither asks the plainest question a reader will ask:
**what have these funds actually returned to the people who own them, against the
benchmark their own issuer prints beside the number?**

**Decision it informs.** Whether the financed-overlay case — which this repository's own
algebra says is worth about 2.44 pp/yr before costs on a 100%-equity base — has shown up
in the retail products that sell it, and what an investor should expect to sit through
while waiting for it. Out of scope: whether to hold a trend sleeve
([decision 0004](../decisions/0004-no-sleeve-promoted.md)), what a wrapper's structure is
worth ([capital efficiency](capital-efficiency-and-breadth.md)), and what the funds are
made of ([loading comparability](loading-comparability-and-wrapper-exposure.md)).

**Status: `source-reproduced`.** Every figure here is read from an issuer's or an author's
own published table on a stated date; the only arithmetic performed is subtracting two
numbers the issuer printed side by side. **Nothing here is a repository measurement and
nothing here is a backtest.** `as of 2026-08-23`. The Return Stacked figures are the
issuer's 2026-07-31 month-end; the WisdomTree figures are that issuer's 2026-06-30 quarter
end. **The two tables are a month apart and are not as-of matched.** Standardised returns
update on the issuers' own schedules; re-read before quoting.

---

## Conclusion

1. **On the funds where the comparison is clean, the second dollar has not paid.** For five
   Return Stacked funds the benchmark the issuer itself prints *is the base leg of the
   stack*, so the difference is exactly the question. All five are negative since
   inception: **−1.71, −3.54, −6.98, −5.80 and −7.37 pp/yr**. The one clear win is the
   merger-arbitrage fund at **+1.24 pp/yr**, the least glamorous sleeve on the shelf.
2. **And then the trailing year reversed hard.** Over the twelve months to 2026-07-31 the
   stocks-plus-trend fund returned **+41.77% against the S&P 500's +19.56%**, and the
   bond version **+22.48% against +2.71%**. Both facts are one fact. The windows are 0.2
   to 3.5 years and none of them prices a strategy.
3. **The prize, from the idea's leading advocate, is about 70 basis points — and it is a
   forecast, not a record.** Cliff Asness's worked example puts 60/40 at 8.9% compound,
   the same portfolio with 25% alternatives sold-to-fund at **8.8%**, and the same
   alternatives financed at **9.6%**. That is +0.7 pp against the starting 60/40 and
   +0.8 pp against the sold-to-fund version. It is built on *assumed* capital-market
   expectations, not on a sample.
4. **The cheapest version of the idea is the one with a record.** NTSX has run nearly eight
   years at **20 basis points**, compounding at **+12.81%/yr** to 2026-06-30. It buys no
   alternative strategy and bets on no premium, and it is the only fund on this page whose
   case does not depend on somebody's estimate of a future mean. Its two younger siblings
   compound at roughly half that on the same mechanism, which is the reminder that the
   mechanism supplies cheaper exposure and not a premium.
5. **The methodological caveat decides how much of the above counts, so it is stated first.**
   A fund running two dollars of notional against a one-dollar index is being credited or
   blamed for leverage. Section
   [*What is a clean comparison here*](#what-is-a-clean-comparison-here) says which rows
   survive that objection and which do not.

---

## What is a clean comparison here

This repository has made the leverage-matched-comparator error three times and caught
itself three times, so the rule is stated before the tables rather than after them.

**A fund holding $1 of stocks and $1 of managed futures per dollar of capital is not
comparable with a $1 stock index.** Over a period when the base leg compounds at 20%/yr,
that fund is charged for the drag of a second leg while receiving no credit for having
kept the whole first one. Over a period when the base leg falls, the same comparison
flatters it. The comparison a repository experiment would run is against a
**leverage-matched control** — the same gross notional in the base asset alone — and none
of the issuer tables below is that.

What the issuer benchmark *does* answer is narrower, and worth having:

- **Clean, for the question asked.** For **RSST, RSBT, RSSY, RSBY and RSSX** the printed
  benchmark **is the base leg**: the S&P 500 for the three stock funds, the Bloomberg US
  Aggregate for the two bond funds. Since the fund holds approximately one dollar of that
  base per dollar of capital *plus* a second leg, the difference is a direct read on
  whether the second leg covered its own financing and fee. It is not a read on whether
  the fund was a good idea at a given risk level, which is a different question and needs
  the leverage-matched control.
- **Not clean.** **RSSB** shows a *global* equity base against a *US* index during a period
  of heavy US outperformance, so most of its shortfall is benchmark mismatch. It is
  reported and excluded from the count.
- **Not clean.** **NTSX's** since-inception figure below is quoted with no benchmark at
  all, deliberately, because a 90/60 fund against the S&P 500 is exactly the error above.
  What NTSX is quoted for is its fee, its age and its mechanism.
- **Too short to read.** **RSIT** has no since-inception annualised figure yet.

**And every window here is short.** The longest is 3.5 years and three are under two.
[The construction tournament](construction-tournament.md) puts the years needed to resolve
a 30% stacked trend wrapper against a leverage-matched control at **64**, and a pure trend
overlay at **244**. Nothing on this page can settle anything; it can only say what
happened.

---

## 1. Return Stacked: six of seven trail the benchmark their own issuer prints

Issuer-published standardised NAV returns **as of 2026-07-31**, net assets **as of
2026-08-20**, read from [returnstackedetfs.com](https://www.returnstackedetfs.com/) on
**2026-08-23** and independently re-read the same day.

| Fund | Stacks | Inception | Fee | Net assets | Since inception, ann. | The issuer's own benchmark | Difference |
| --- | --- | --- | ---: | ---: | ---: | --- | ---: |
| **RSST** | US stocks + managed futures | 2023-09-05 | 0.99% | $504.95M | +19.07% | S&P 500 TR +20.78% | **−1.71** |
| **RSBT** | Bonds + managed futures | 2023-02-07 | 1.01% | $147.27M | **−0.38%** | Bloomberg US Agg +3.16% | **−3.54** |
| **RSSY** | US stocks + futures yield | 2024-05-28 | 0.99% | $94.46M | +11.68% | S&P 500 TR +18.66% | **−6.98** |
| **RSBY** | Bonds + futures yield | 2024-08-20 | 1.01% | $55.63M | **−3.58%** | Bloomberg US Agg +2.22% | **−5.80** |
| **RSSX** | US stocks + gold/bitcoin | 2025-05-29 | 0.67% | $70.59M | +16.44% | S&P 500 TR +23.81% | **−7.37** |
| **RSBA** | Bonds + merger arbitrage | 2024-12-17 | 1.01% | $52.33M | +4.11% | Bloomberg US Treasury +2.87% | **+1.24** |
| RSSB | Global stocks + Treasuries | 2023-12-04 | 0.39% | $521.01M | +18.93% | S&P Composite 1500 TR +21.53% | −2.60, mismatch |
| RSIT | Int'l stocks + managed futures | 2026-05-06 | 0.98% | $68.53M | — | — | too new |

Units are percentage points a year. The difference column is our subtraction of two figures
the issuer prints beside each other and is not a fitted quantity.

**Five of five clean cases are negative, and the one clear win is the dullest sleeve on the
shelf.** Merger arbitrage — the strategy with the smallest advertised upside in the family —
is the only stacked leg that has covered its own cost since inception. That ordering is
worth more attention than it gets: the funds whose second leg is the most exciting story
(futures yield, gold and bitcoin) have the largest shortfalls.

### Then trend fired

Trailing twelve months to **2026-07-31**, issuer-published NAV:

| Fund | Trailing year | Its own benchmark |
| --- | ---: | ---: |
| **RSST** | **+41.77%** | S&P 500 TR **+19.56%** |
| **RSBT** | **+22.48%** | Bloomberg US Agg **+2.71%** |
| RSSY | +33.48% | — |

**A bond-plus-trend fund that had lost money over three and a half years while plain bonds
compounded at 3.2% then made 22.5% in twelve months.** Neither number is quotable without
the other, and the pair is the whole experience of owning a financed overlay: the
diversifier is dead weight until the year it is not, and no one can tell in advance which
year that is. Quoting only the since-inception column is the sceptic's version; quoting
only the trailing year is the marketing version.

### The exposure is delivered; the record cannot yet price the strategy

The engineering is not in doubt and is measured rather than asserted:
[loading comparability §2](loading-comparability-and-wrapper-exposure.md#2-the-wrappers-trend-loading)
fits RSST's trend loading at **+0.681 [+0.406, +0.955]** over 31 filed months, with RSSB as
a negative control at −0.10, from the funds' own Form N-PORT filed returns rather than from
a price feed. **The fund holds what it says it holds. Nothing about that signs a premium.**

**One issuer disclosure deserves more attention than it gets.** The Q3 2025 quarterly
commentary — [PDF](https://www.returnstackedetfs.com/wp-content/uploads/pdf/Return-Stacked-Q3-2025-Commentary.pdf),
header-dated October 2025, read 2026-08-23 — plots rolling 252-day tracking error of the
replication engine behind RSBT and RSST against the SG Trend Index at roughly **6.3% to
7.5%** through the period ending 2025-09-30. **The managed-futures leg is a single
manager's implementation, not index exposure.** An investor who believes they are buying
"managed futures" is buying one firm's version of it with six to seven points a year of
dispersion around the category, and
[live managed futures](live-managed-futures.md#1-the-census-what-is-in-it-and-what-can-never-be)
records the attrition rate in that category separately.

---

## 2. Asness's own arithmetic: about 70 basis points, and it is a forecast

Cliff Asness, **"Should Hedge Funds Hedge?: Why Some Alts Should Have a Beta of 1.0"**,
AQR, **2025-03-28**
([source](https://www.aqr.com/Insights/Perspectives/Should-Hedge-Funds-Hedge-Why-Some-Alts-Should-Have-a-Beta-of-1-0),
read 2026-08-23). The paper endorses return stacking by name, credits Corey Hoffstein for
the term, and announces AQR's own "Fusion" strategies doing the same thing.

| Portfolio | Excess return | Volatility | Sharpe | Compound return |
| --- | ---: | ---: | ---: | ---: |
| 60/40 | 4.4% | 10.2% | 0.44 | **8.9%** |
| + 25% alternatives, **funded by selling** stocks and bonds | 4.1% | 8.0% | **0.51** | **8.8%** |
| The same alternatives, **equitised** rather than sold-to-fund | 5.2% | 10.5% | 0.49 | **9.6%** |

**Read the middle row first.** Funding alternatives by selling produced *no compound-return
benefit at all* — 8.8% against 8.9% — while raising the Sharpe ratio from 0.44 to 0.51. It
bought smoothness, not growth. That is exactly the substitution-versus-overlay distinction
[capital efficiency](capital-efficiency-and-breadth.md#funding-algebra) derives from
`a_p − sigma_p²`, reached independently and with numbers attached, by an author with every
incentive to make the sold-to-fund case look better rather than worse.

**The financing is worth +0.7 pp against the 60/40 it started from and +0.8 pp against the
sold-to-fund version**, at approximately equal Sharpe, for 25% of notional in alternatives.
Quote whichever comparison you name; do not quote 70 bp against the middle row.

**Two scope limits, and the first is the one a reader will miss.**

- **This is not a backtest and there is no sample period.** The table is an explicitly
  hypothetical exercise built on stated capital-market assumptions — stocks at 6.0% excess
  return and 15% volatility, bonds at 2.1% and 7%, alternatives at 3.0% and 10% — and the
  paper introduces it with "under these assumptions". **It is a forecast of what financing
  is worth, not a record of what it paid.** Read beside section 1, which is a record and
  disagrees.
- **"Alternatives" is generic.** No index is named and no fund is named, so the row cannot
  be reproduced against a live product and carries no fee, no financing spread and no
  manager risk. Section 1's funds carry all three.

The same author's later work cuts the other way and is worth carrying for that reason.
Asness, Villalon and Ilmanen, **"A Positive Stock-Bond Correlation Is a Terrible Reason to
Add More Equity Risk to Your Portfolio"**, **2026-04-08**
([source](https://www.aqr.com/Insights/Perspectives/A-Positive-Stock-Bond-Correlation-Is-a-Terrible-Reason-to-Add-More-Equity-Risk-to-Your-Portfolio),
read 2026-08-23), five years ending **2026-02-28**:

| Sleeve | Equity beta | Return | Alpha |
| --- | ---: | ---: | ---: |
| Private credit, Cliffwater BDC Index | 0.70 | 7.3% | **−3.8%** |
| Buffer funds, Cboe S&P 500 Buffer Protect balanced series | 0.63 | 10.9% | — |
| Bitcoin | **2.09** | 25.5% | **−1.3%** |
| Equity market neutral, HFRI EH: Equity Market Neutral | 0.02 | 7.1% | **+3.6%** |
| Trend, SG Trend Index | −0.22 | 8.6% | **+7.8%** |

**Bitcoin at a beta of 2.09 with negative alpha independently corroborates this
repository's own 1.53-up / 1.62-down measurement and its verdict**
([alternative sleeves §3](alternative-sleeves-audit.md#3-crypto-the-investor-asked-so-here-is-the-arithmetic)),
and the buffer row matches this repository's independent −2.4 to −4.1 pp/yr pricing of the
cap-and-buffer package. Five years is a short window and the row definitions are index
proxies rather than investable products.

---

## 3. NTSX: the cheapest version of the idea is the one with a record

WisdomTree's US Efficient Core Fund stacks the one thing that is closest to free. It holds
equity through futures and puts the released capital into Treasuries — **90 of equity and
60 of Treasury notional per 100 of capital**, the "90/60" language its live SEC prospectus
uses verbatim. **It buys no alternative strategy and takes no bet on any premium.**

Issuer-published figures, **as of 2026-06-30**, which is the quarterly date WisdomTree
prints; read 2026-08-23.

| | Inception | Fee | Net assets | 1 year, NAV | Since inception, ann. |
| --- | --- | ---: | ---: | ---: | ---: |
| **NTSX** (US) | 2018-08-02 | **0.20%** | $1.36bn | +19.41% | **+12.81%** |
| NTSI (developed ex-US) | 2021-05-20 | 0.26% | $497M | +18.74% | +6.29% |
| NTSE (emerging) | 2021-05-20 | 0.32% | $57.1M | +48.84% | +6.70% |

**They are quoted here without a benchmark, deliberately.** A 150%-notional fund against a
100%-notional index is the comparison this page opened by refusing. The honest reading of
NTSX's record is not "it beat the market" — nothing here establishes that — but that
**capital efficiency without manager risk survived nearly eight years at twenty basis
points and did what its prospectus said.** It is the only fund on this page whose case does
not rest on somebody's estimate of a future average return, and the only one whose fee is
of the same order as the index fund it displaces. Its tax treatment is in
[structural and tax edges](structural-and-tax-edges.md), its notional arithmetic in
[the notional budget](leverage-and-the-notional-budget.md), and neither is repeated here.

**The two younger funds are the caution.** NTSI and NTSE compound at roughly half NTSX's
rate over five years, on the same mechanism at a slightly higher fee. The mechanism does
not supply a premium; it supplies exposure more cheaply, and what the exposure then earns
is a different question that this page does not answer.

---

## 4. The tail-hedge products, and where they live

The page copy that draws on this synthesis also cites Cambria's TAIL and Simplify's CYA.
Their canonical home is
[alternative sleeves §4](alternative-sleeves-audit.md#4-tail-hedging-the-bleed-is-measured-and-the-cheaper-substitutes-win),
which prices the whole tail-hedging mechanism rather than two products, and the verified
figures — TAIL's calendar years, its **+6.98% in 2020** against a 33.9% equity drawdown and
its **−13.15% in 2022** against an −18.11% equity year, and CYA's reverse split and
liquidation — were added there rather than duplicated here.

They belong to this page's argument in one respect, and it is the survivorship one.
**A shelf screened today shows the products that lived.** CYA did not, and it is the
seventh member of a run of Simplify alternative-strategy closures. Every performance table
on this page, including the one in section 1, is a table of survivors; the honest reading
of "six of seven trailed" is that seven is the number still filing.

---

## Verified, assumed, open

**Verified, against the primary source, read 2026-08-23.**

- Every NTSX, NTSI and NTSE row in section 3, against `wisdomtree.com`, and the 90/60
  mechanism against WisdomTree Trust's live SEC prospectus.

- Every cell of the Return Stacked table in section 1 — inception, fee, net assets,
  since-inception annualised NAV return and the issuer's own benchmark — against each
  fund's own page on `returnstackedetfs.com`, which carries "As of 07/31/2026" on the
  performance table and "As of 08/20/2026" on net assets. Re-read independently the same
  day.
- The three trailing-twelve-month rows, from the same tables.
- The 6.3%–7.5% rolling tracking error against the SG Trend Index, from Figure 4 of the
  issuer's own Q3 2025 commentary PDF.
- Every figure in both AQR tables, fetched from `aqr.com` rather than from a summary,
  including the authorship of the 2026 paper (Asness, Villalon and Ilmanen, not Asness
  alone) and the assumption set behind the 2025 one.

**Corrected during verification.**

- The financing gain in Asness's table is **+0.7 pp against the 60/40** and **+0.8 pp
  against the sold-to-fund portfolio**. An earlier draft quoted "roughly 70 bp" without
  saying which pair it referred to.
- The 2025 table is a **forward-looking illustration on assumed capital-market
  expectations**, not a historical result. An earlier draft read it as a track record.
- The 2026 paper has **three authors**, not one.
- **NTSX's since-inception return is +12.81%/yr as of 2026-06-30**, not the +12.87% an
  earlier draft carried, and its assets are $1.36bn rather than $1.39bn. WisdomTree prints
  performance quarterly, so this table is a month older than the Return Stacked one and the
  two are not as-of matched.
- **NTSE's trailing year is +48.84% NAV**, not the +41.45% an earlier draft carried — a
  material miss rather than a rounding one.

**Not verified, and therefore not used above.**

- **RSST's calendar-year returns.** The issuer publishes rolling periods only; its fund
  pages carry no calendar-year table. SEC EDGAR, which would supply the N-CSR bar chart,
  returned HTTP 403 to every automated request. Only the year-to-date figure could be
  confirmed: **+14.93% NAV against the S&P 500's +10.14%** at 2026-07-31. The 2024 and 2025
  calendar figures are dropped.
- **Family assets of about $1.97bn including partner funds.** The homepage figure is
  rendered by JavaScript and returns nothing to a fetch. **The eight SEC-registered Return
  Stacked ETFs' own stated net assets sum to about $1.52bn**, and that sum is the only
  figure used on this page. Whether partner vehicles bring the total to $1.97bn is
  unconfirmed.
- **The issuer's phrases "two years of bad performance" and "some of the worst drawdowns in
  its history".** The full Q3 2025 commentary was read and neither phrase appears in it.
  The substance is visible in the fund's own standardised figures, so the substance is
  stated above and the quotation is dropped.
- **That no Return Stacked fund has been liquidated.** Every fund appears in every
  quarterly commentary published between October 2025 and July 2026, with growing assets.
  That supports the claim without establishing it, and no issuer statement to that effect
  was found.
- **The 2025 industry fund-closure counts** (146 active ETFs closed, 962 launched, 357
  mutual funds liquidated or merged). These are Morningstar's, reached only through a
  secondary aggregator; Morningstar and ETF.com both refuse automated retrieval. **They are
  not used on this page.** This repository's own attrition count, on its own census, is in
  [live managed futures](live-managed-futures.md#attrition-2019-07-to-2025-12--a-lower-bound-twice-over).

**Assumed.**

- That each stacked fund holds approximately one dollar of its printed benchmark's asset
  per dollar of capital, which is what makes the difference column a read on the second
  leg. It is checked for RSST and MATE in
  [capital efficiency](capital-efficiency-and-breadth.md#read-the-base-leg-from-the-whole-filing-not-from-its-largest-line)
  from Form N-PORT and is *not* separately checked for RSSY, RSBY, RSSX or RSBA.
- That an issuer's standardised NAV return is computed as the SEC requires. No independent
  return series exists for any of these funds in this repository
  ([decision 0002](../decisions/0002-no-research-grade-free-price-source.md)).

**Open.**

1. **A leverage-matched comparison for any of these funds.** It cannot be built from
   issuer tables and needs a fund return series this repository is not licensed to hold.
   Until then, section 1 answers "did the second leg cover its own cost" and no more.
2. **Whether the trailing year is a regime or an episode.** Twelve months of trend is
   worth less than the 64-year resolution figure the tournament reports, and this page
   deliberately makes no claim either way.
3. **Partner-vehicle assets and the family's true size**, which bears on survival risk for
   the smaller funds — three of the eight hold under $75M.

## Reproduce it

Nothing here runs. Every number is read from a published table, and the only arithmetic is
the subtraction in the difference column, which a reader can repeat with the two figures
printed beside it. The URLs and read dates are in the section they support and in
*Verified, assumed, open* above. **Standardised returns update monthly: re-read before
quoting.**
