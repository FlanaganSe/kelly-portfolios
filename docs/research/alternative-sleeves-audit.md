# Alternative sleeves: which engines are distinct, and which are an expensive cash

**Question.** The candidate portfolio holds equity beta, equity factor tilts and one
managed-futures overlay — two or three distinct return engines. The investor is explicit
that they want more: *"creative funds, assets that don't correlate, assets that perform
better in black swan events without excessive long-term drawdowns, crypto, anything."*
Which further mechanisms are economically distinct, accessible to a US retail investor at
a cost that leaves something over, and worth a weight?

**Current answer.** Two genuinely new engines, and one free improvement that is worth more
than either. **Duration-hedged credit** is the largest change: this repository rejected
credit on a +0.835 correlation to Treasuries measured with twenty years of duration
attached, and once the duration is hedged out the correlation is **+0.016** over 1,068
months, at the same return as long Treasuries for half the volatility and a third of the
drawdown. **Catastrophe risk** is the only mechanism screened whose payer is not a financial
market and whose trigger is a hurricane; its access problem has been solved and a pricing
problem has replaced it. And **a larger cash and short-Treasury allocation is the cheapest
tail hedge on this panel** — it beats almost everything sold as one. Everything else is
already owned, an expensive form of cash, or an equity beta with a different name.

Two answers the investor asked for directly. **Crypto: at most 1–2%, and only as a
declared speculation, never as a diversifier** — in the worst decile of equity months
since 2015 bitcoin's mean return was **−7.51%** and it was positive in **1 of 13** of them.
**Explicit tail hedges: no.** The bleed is measured at roughly 12 percentage points a year
against the index, and the convexity it buys is not statistically resolvable in any asset
on this panel.

**Decision it informs.** What to add to the construction, at what weight, in which
account, and what evidence would move each weight.

**Out of scope.** The equity share ([setting the equity share](setting-the-equity-share.md)),
the trend overlay's own sizing ([trend](trend-marginal-value.md),
[live funds](live-managed-futures.md)), and the current construction as a whole
([recommendation](portfolio-recommendation.md)).

`as of 2026-08-22` for product facts; each carries its own source and read date. The
measured tables regenerate from
[`studies/_stress_dependence_tables.py`](../../research/src/portfolio_edge/studies/_stress_dependence_tables.py)
and the arithmetic is pinned in
`research/tests/unit/test_studies_stress_dependence.py`. **Everything measured here is
`exploratory`**: no specification was frozen before the numbers were seen, the stress
windows were chosen by eye from [the standing episode list](evidence-base.md), and four
of the legs are AQR vendor series their author reconstructs on every release. The stress
windows and the tail quantile are hypothesis-bearing analytical choices and **owe a
ledger entry**; the module and its tests are committed so the choice is inspectable.

---

## 1. What the data says before any product is named

### 1.1 The panel

Eight candidate engines against US equity, each on its own longest window, every leg an
**excess return over cash** so the rows are comparable. The base is Ken French `Mkt-RF`
and cash is the same file's `RF`; over 1926-07…2026-06 that base returned **+6.86%/yr**
excess at 18.38% volatility, Sharpe 0.45, with a maximum drawdown of **−84.6%** relative
to cash.

| Engine | Window | Months | Geo/yr | Vol/yr | Sharpe | Max DD vs cash | ρ to equity |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Long Treasury | 1926-07…2025-12 | 1194 | +1.91% | 8.42% | +0.27 | −59.1% | +0.076 |
| Corporate, unhedged | 1926-07…2025-12 | 1194 | +2.47% | 7.63% | +0.36 | −52.1% | +0.214 |
| **Credit, duration-hedged** | 1926-07…2014-12 | 1062 | +2.13% | **4.12%** | **+0.53** | **−20.7%** | +0.234 |
| Commodities, long-only | 1926-07…2025-05 | 1187 | +3.73% | 15.89% | +0.31 | −82.0% | +0.297 |
| Trend (AQR TSMOM) | 1985-01…2026-05 | 497 | +12.10% | 12.49% | +0.98 | −27.9% | −0.079 |
| Gold | 1975-02…2026-06 | 617 | +1.75% | 16.24% | +0.18 | **−91.2%** | −0.019 |
| Betting-against-beta | 1930-12…2026-05 | 1146 | +7.37% | 11.15% | +0.70 | −54.6% | −0.139 |
| Bitcoin | 2015-02…2026-06 | 137 | +60.03% | 71.48% | +1.00 | −75.9% | +0.342 |

Sources and their traps: long Treasury and unhedged corporate are Goyal–Welch `ltr` and
`corpr` less `Rfree`; **duration-hedged credit is AQR `CORP_XS`**, defined as the corporate
total return less a *duration-matched* government return and therefore the only true
credit-spread series held — it may never be summed with the Treasury leg and it ends in
2014-12; commodities are AQR's equal-weight long-run excess series; trend is AQR `TSMOM`,
**a vendor series that states no fee, transaction cost, slippage or financing basis
anywhere**; gold is the World Bank Pink Sheet less cash and an assumed 25 bp carry, from
1975-01 because private US bullion ownership was illegal before 1974-12-31; bitcoin is
FRED `CBBTCUSD`, one venue's daily print rather than the CME CF rate an ETP prices
against. Provenance and licence for each is in [the evidence base](evidence-base.md).

Two rows deserve a second look. **Duration-hedged credit has the best Sharpe and by far the
shallowest drawdown of any long-only engine here** — 0.53 at 4.12% volatility, against
equity's 0.42 over identical months. And **trend's headline Sharpe of 0.98 is gross of
everything**; this repository's own live-fund panel measures what the funds actually paid
([live managed futures](live-managed-futures.md)), and the last 78 months of the same
vendor series returned +1.95%/yr, not +12%.

### 1.2 There are two kinds of shock, and no single asset covers both

Cumulative excess return inside each of the standing named episodes. `—` means the panel
does not reach the window; `*` marks partial coverage, so the number beside it is not the
episode.

| Episode | Equity | Treasury | Corp. unhedged | Credit hedged | Commodity | Trend | Gold | BAB | Bitcoin |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1929-32 crash | −84.6% | +7.8% | +2.6% | +5.7% | −72.3% | — | — | −30.6%* | — |
| 1937-38 | −49.6% | −0.0% | +2.3% | +2.4% | −24.3% | — | — | −6.7% | — |
| 1973-74 | −53.1% | −17.3% | −21.1% | −6.9% | **+143.9%** | — | — | −13.5% | — |
| Late-1970s inflation | +5.0% | **−40.5%** | −41.4% | −3.2% | +6.9% | — | **+90.0%** | +74.4% | — |
| 1987 crash | −31.0% | +1.3% | +0.5% | −0.4% | +4.8% | −2.7% | +0.0% | −8.8% | — |
| 1998 LTCM | −13.0% | +7.0% | +3.1% | −1.8% | −7.3% | +11.6% | −2.4% | −4.9% | — |
| 2000-02 dot-com | −50.0% | +23.3% | +26.4% | +10.8% | +5.5% | +64.8% | +0.8% | +179.6% | — |
| 2008-09 GFC | −51.4% | +13.4% | −5.7% | **−13.1%** | −38.7% | +29.6% | +21.8% | **−31.6%** | — |
| 2020 Q1 covid | −20.5% | +19.2% | +4.0% | — | −24.4% | +12.3% | +7.2% | −9.4% | −10.5% |
| 2022 rate shock | −25.3% | −13.6% | −19.2% | — | +10.5% | **+34.2%** | −6.8% | −2.5% | **−58.3%** |

Read down the columns and the shocks separate cleanly:

- **Growth and deflation shocks** — 1929-32, 1987, 1998, 2000-02, 2008-09, 2020 Q1.
  Treasuries pay in every one. Commodities lose in four of six.
- **Inflation and rate shocks** — 1973-74, the late 1970s, 2022. Treasuries lose in all
  three, by up to 40%. Commodities and gold pay.
- **Trend is the only engine positive in both kinds**, and it has no data before 1985, so
  it has never been observed through an inflation shock larger than 2022.
- **Credit's hedged spread is the mildest loser in the growth shocks and nearly immune to
  the inflation ones** — −3.2% through five years of the late 1970s against the Treasury
  leg's −40.5%. That is the whole point of hedging the duration out.
- **BAB is a trap.** Its full-sample correlation to equity is −0.139, which reads as a
  diversifier. It lost 30.6% through 1929-32 and **31.6% through the GFC**, because its
  mechanism is selling leverage to people who cannot borrow, and a crisis is exactly when
  leverage is withdrawn. This matters here because the investor already holds equity factor
  tilts that lean the same way.

### 1.3 In the lower tail, almost every candidate is a worse cash

The black-swan question stated as an estimand. Split months by the base's own return, take
the worst decile, and ask what the engine did. `offset at 10%` is what swapping a tenth of
the equity base into the engine adds back in the average worst-decile month; `same for
cash` is the identical swap into T-bills, on the identical months.

| Engine | Months | n low | Equity mean | Engine mean | Hit rate | Worst | Offset at 10% | **Same for cash** | ρ low | ρ high | ρ full |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Long Treasury | 1194 | 119 | −9.23% | +0.16% | 53% | −11.2% | +0.94% | **+0.92%** | +0.023 | +0.098 | +0.076 |
| Corporate, unhedged | 1194 | 119 | −9.23% | −0.44% | 48% | −9.8% | +0.88% | **+0.92%** | +0.019 | +0.163 | +0.214 |
| Credit, duration-hedged | 1062 | 106 | −9.38% | −0.24% | 54% | −9.5% | +0.91% | **+0.94%** | +0.027 | +0.196 | +0.234 |
| Commodities | 1187 | 118 | −9.26% | −1.84% | 36% | −20.9% | +0.74% | **+0.93%** | +0.326 | +0.343 | +0.297 |
| **Trend** | 497 | 49 | −8.24% | **+2.59%** | **69%** | −10.5% | **+1.08%** | +0.82% | +0.024 | −0.190 | −0.079 |
| Gold | 617 | 61 | −8.03% | +1.21% | 56% | −17.9% | +0.92% | +0.80% | +0.190 | −0.150 | −0.019 |
| BAB | 1146 | 114 | −9.00% | +0.62% | 56% | −12.7% | +0.96% | +0.90% | **+0.324** | −0.264 | −0.139 |
| **Bitcoin** | 137 | 13 | −7.96% | **−7.51%** | **8%** | −37.7% | **+0.05%** | +0.80% | +0.251 | +0.263 | +0.342 |

Four readings, and the third is the one that should change a portfolio:

1. **Trend is the only engine that materially beats cash in the lower tail** — +1.08%
   against +0.82%, 26 bp a month of genuine protection, delivered in 69% of those months
   rather than by one enormous outlier.
2. **Long Treasuries buy two basis points a month over T-bills.** +0.94% against +0.92%.
   The entire crisis-hedging case for twenty-year duration, on a century of data,
   is 2 bp per worst-decile month — bought with 8.42% of annual volatility, a −59.1%
   drawdown, and a −40.5% loss through the late 1970s that cash did not have.
3. **Gold buys twelve basis points a month over T-bills**, at 16.24% volatility and a
   −91.2% peak-to-trough. This is the same conclusion as
   [marginal sleeve value](marginal-sleeve-value.md) reached by a different route, and it
   is why gold keeps failing: it is not that gold does not diversify, it is that cash
   diversifies nearly as well for nothing. Financed inside the leveraged construction it
   reads the same way: `unresolved` (Experiment 018, §8).
4. **Commodities and bitcoin are worse than cash in the lower tail**, and bitcoin is worse
   by 75 bp a month. Two assets frequently sold as diversifiers are, on this measurement,
   negative-value tail hedges.

Conditioning on the base's own magnitude truncates its variance, so ρ low and ρ high are
biased toward zero and are comparable with each other, never with ρ full.

### 1.4 Nothing on this panel is convex, and the only measured convexity has the wrong sign

Fit `engine = α + β·equity + κ·min(equity, 0)` with Newey-West standard errors. **κ is the
convexity**: negative κ means the engine's slope against equity falls when equity falls,
which is what "performs better in a crash than a linear exposure would" means as an
estimand. α is the per-month price of the shape.

| Engine | Months | α/month | *t* | Up beta | Down beta | κ | *t* |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Long Treasury | 1194 | +0.069% | +0.71 | +0.058 | +0.009 | −0.049 | −1.24 |
| Corporate, unhedged | 1194 | +0.060% | +0.60 | +0.115 | +0.060 | −0.056 | −1.37 |
| Credit, duration-hedged | 1062 | +0.084% | +1.54 | +0.068 | +0.034 | −0.034 | −1.36 |
| Commodities | 1187 | +0.365% | +1.69 | +0.223 | +0.291 | +0.068 | +0.62 |
| Trend | 497 | **+0.914%** | **+3.09** | −0.018 | −0.105 | −0.088 | −0.49 |
| Gold | 617 | +0.299% | +0.95 | −0.030 | −0.011 | +0.020 | +0.16 |
| **BAB** | 1146 | +1.427% | +6.83 | **−0.264** | **+0.118** | **+0.381** | **+3.49** |
| Bitcoin | 137 | +4.460% | +1.44 | **+1.526** | **+1.616** | +0.091 | +0.08 |

- **Not one engine has statistically resolvable convexity.** The largest |*t*| on κ among
  the seven non-BAB rows is 1.37. What looks like crisis protection in §1.3 is a low beta
  plus a positive mean, not a payoff that accelerates.
- **Trend's crisis case is an alpha, not a shape.** α = +0.91%/month at *t* = 3.09 on a
  vendor series with no costs in it; κ is indistinguishable from zero. That is consistent
  with [the evidence base](evidence-base.md), where the crisis-conditional trend benefit
  has ≈4.4 effective observations and cannot be resolved at all.
- **BAB is measurably concave at *t* = 3.49**: β = −0.264 when equity rises and **+0.118
  when it falls**. This is the sharpest available demonstration of the charter's rule that
  low average correlation is only an admission signal.
- **Bitcoin is a levered equity beta.** 1.53 up, 1.62 down, no convexity, and an α of
  +4.46%/month whose *t* is 1.44 — economically enormous and statistically nothing.

### 1.5 What a sleeve is worth, at the weight anyone would actually hold

Realised marginal growth of a pro-rata-funded sleeve (sell the equity base), which is
[Experiment 010](marginal-sleeve-value.md)'s rule and the least favourable one for a
diversifier. No trading cost is charged; the gold leg carries its 25 bp.

| Engine | Months | 1% | 2% | 5% | 10% | Base max DD | Blend max DD at 10% |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Trend | 497 | +0.060 | +0.120 | +0.296 | **+0.580** | −50.3% | −44.7% |
| Gold | 617 | −0.038 | −0.076 | −0.195 | −0.404 | −50.3% | −45.1% |
| Credit, duration-hedged | 1062 | −0.026 | −0.051 | −0.131 | −0.272 | −83.7% | −79.7% |
| Commodities | 1187 | −0.009 | −0.018 | −0.048 | −0.107 | −83.7% | −83.5% |
| Bitcoin | 137 | +0.647 | +1.292 | +3.215 | **+6.383** | −24.8% | **−29.2%** |

Units are pp/yr of realised geometric growth. Read this against the design's own floor:
[the evidence base](evidence-base.md) measures the marginal-sleeve instrument's MDE₈₀ at
**≈0.58 pp/yr**, so every row except bitcoin's lies inside the noise, and bitcoin's row is
137 months containing the largest bull market in the asset's history against a
matched-volatility floor of 15.58 pp/yr. **The one thing in that table that is not noise is
the last column**: a bitcoin sleeve is the only candidate here that made the portfolio's
drawdown *deeper* at every weight tested.

---

## 2. Candidate map

Every mechanism screened, with who pays and why they keep paying, what the payoff looks
like, and the verdict. **Access is separated from evidence throughout: a missing retail
vehicle is an implementation finding, not proof that the return source is absent.**

| Family | Who pays, and why they keep paying | Payoff shape | Distinct from what is held? | Verdict |
| --- | --- | --- | --- | --- |
| **Catastrophe bonds / ILS** | Insurers and reinsurers buy capital-markets capacity for peak perils they cannot retain. The payer is a balance sheet with a regulatory capital constraint, not a market participant with a view | Bond-like carry with a rare, severe, event-triggered loss; a short put on a hurricane | **Yes.** The only mechanism screened whose loss trigger is meteorological | **Admit, small.** §5 |
| **Duration-hedged credit** | Investors who must hold rated paper and cannot bear mark-to-market or default risk pay a spread above a duration-matched Treasury | Carry with a left tail concentrated in the same default state as equity | **Partly.** ρ full +0.234, but 4.12% volatility and −20.7% drawdown against equity's −84.6% | **Admit.** §6 |
| **Trend / managed futures** | Slow-moving capital, hedgers rolling risk, and behavioural under-reaction | Positive mean with near-zero beta; not measurably convex | Already held | **Held. Do not add a second.** §7 |
| **Gold** | Nobody. It has no cash flow and no counterparty obligation; its return is a change in what others will pay | Fat-tailed real asset; hedges currency and inflation regimes, not equity crashes | Yes, but buys 12 bp/month over cash | **Optional, ≤5%, and only in place of cash.** §8 |
| **Commodities, long-only** | Hedgers who want price certainty, when the curve is in backwardation and not otherwise | Inflation-shock payoff; loses in growth shocks | Yes, but negative in the equity lower tail | **Reject as a diversifier; consider only as an inflation hedge.** §8 |
| **Long/short commodities (carry, momentum)** | Same hedgers, but the long-only version pays the roll instead of collecting it | Closer to trend than to spot commodities | Substantially overlaps the trend sleeve | **Reject on overlap.** §8 |
| **Spot bitcoin** | Nobody. No cash-flow claim exists; expected return is entirely a claim about future adoption | Levered equity beta with an idiosyncratic regulatory and custody tail | **No.** β 1.53/1.62, ρ 0.342, worse than cash in the lower tail | **≤2%, as declared speculation.** §3 |
| **Explicit tail hedges (long puts)** | The buyer pays the variance risk premium to the seller, every month, forever | Convex when it works, and it must be sized and monetised to work | It is the *opposite* side of a premium, so it is negative expected return by construction | **Reject.** §4 |
| **Long volatility (VIX futures)** | Same, plus a roll paid into a persistently contangoed curve | Spike payoff destroyed by roll | Same | **Reject.** §4 |
| **Volatility selling / put writing** | The investor is paid the premium above, and takes the crash | Negative skew; the crash *is* the product | Duplicates equity's own left tail | **Reject on overlap.** §9 |
| **Buffered / defined-outcome** | The investor sells upside to buy a bounded downside, and pays a fee on top | Bounded both ways over a reset period | Replicable from a bond and two options | **Reject on price.** §4 |
| **Merger arbitrage** | Sellers of deal risk want certainty before a deal closes | Small carry with a deal-break left tail that clusters with equity | Weakly | **Unresolved; too small to matter.** §9 |
| **Alternative risk premia funds** | Various | Various | Various | **Reject on cost stack.** §9 |
| **Nominal bonds / TIPS** | Investors buying certainty of nominal cash flows | Duration, with the sign of its equity correlation flipping by era | TIPS and nominals are **one engine**, ρ +0.76 to +0.85 | **Hold for liability and withdrawal reasons, not for breadth.** §6 |
| **REITs, dividend funds, closed-end discounts, securities lending, direct indexing** | — | — | — | Screened in earlier rounds; see §9 |

---

## 3. Crypto: the investor asked, so here is the arithmetic

**Verdict. At most 1–2% of the portfolio, funded from the speculation budget rather than
from the defensive sleeve, held in a taxable account, and labelled a speculation rather
than a diversifier. Zero is also defensible. Anything above about 5% is a leveraged equity
position that the investor could obtain more cheaply and with a shallower drawdown by
holding more equity.**

**The mechanism, stated honestly.** There is no cash-flow claim. A bond pays a coupon
because a borrower is contractually obliged; an equity pays because a firm earns; a cat
bond pays because an insurer needs capacity. Bitcoin's expected return is entirely a claim
that the future marginal buyer will pay more than today's. That is not a risk premium and
it must not be written as one. What can be defended is narrower and worth stating: a fixed
supply schedule, a settlement network with no counterparty, and a payoff that is not a
claim on any government's solvency. Those are properties, not premia.

**What is measured, on 137 months of FRED `CBBTCUSD`:**

- **Equity beta 1.526 up and 1.616 down**, κ indistinguishable from zero. A 2% bitcoin
  sleeve is, to first order, 3% more equity plus a large idiosyncratic risk.
- **ρ to equity +0.342 over 137 months**, and the 81-month sub-window reads **+0.531**,
  which is *outside* the 0.5 boundary at which the repository's own admission arithmetic
  stops being usable ([evidence base](evidence-base.md)). Correlation has risen as the
  asset has been financialised — the direction that removes the case.
- **In the worst decile of equity months, mean −7.51%, positive in 1 of 13.** It has never
  been observed doing anything else in an equity crisis. −10.5% through 2020 Q1 and
  **−58.3% through 2022**, when equity fell 25.3%.
- **Maximum drawdown −75.9%** on monthly data over a window in which equity's was −25.3%.
- **Its measured α of +4.46%/month carries *t* = 1.44.** Against equity at matched
  volatility the measured gap is **+0.10 pp/yr against a floor of 15.58 pp/yr**: 137 months
  of the best returns in the asset's history cannot distinguish it from the S&P 500.
- **And the most recent evidence is the same evidence again.** In the first half of 2026
  bitcoin fell **−33.2%** while US equity returned **+9.9%** — measured on the same panel,
  and independently corroborated by the CME CF BRRNY rate falling from $87,549 to $58,605
  over the same six months (CF Benchmarks, read 2026-08-22). A 33% fall against a rising
  equity market in the sample's final six months is not a diversifier failing to help; it is
  an asset behaving as the beta measurement says it does, with the idiosyncratic risk on top.
- **The two 2025–26 drawdowns, on daily data** (Coinbase closes against the S&P 500,
  computed 2026-09-01). In the tariff episode bitcoin fell **−28.2%** and ether **−60.1%**
  peak to trough against the S&P 500's −18.9%, and all three troughed on 2025-04-08. From
  the 2025-10-06 cycle high to end-June 2026 bitcoin fell **−53.1%** and ether **−66.6%**
  while the S&P 500's own drawdown was −9.1% (2026-01-27 to 03-30); crypto kept falling for
  three months after equities bottomed. Trailing to 2026-08-31: bitcoin −27.4% over one
  year and +10.8%/yr over five against the S&P 500 price index's +19.0% and +11.2%; ether
  −43.8% and −6.4%/yr. The 30-day correlation to the S&P 500 in 2026 ran from 0.08 to 0.68
  with a mean of 0.46 (90-day 0.33–0.62), and one-year realised volatility was 44.2%, about
  3.5× the index's. IBIT's own standardised one-year return at NAV to 2026-06-30 was
  −45.62%, and it held $60.2bn on 2026-09-01.
- **What the managers who sell it say.** BlackRock's June 2026 note puts a reasonable
  allocation at **1–2%**, sized by risk budget so that it contributes about what a single
  "Magnificent 7" stock does to a 60/40, with a 2% cap because "allocations beyond 2%
  elevate portfolio risk disproportionately, given bitcoin's volatility and unstable
  correlations", and names 70–80% peak-to-trough selloffs as the risk. Fidelity's midyear
  outlook says "you can have 75% drawdowns in a long-term uptrend". Vanguard opened its
  platform to third-party crypto funds on 2025-12-02 and recommends no allocation.

**Why not zero, then.** Because the loss from a 1–2% position that goes to zero is 1–2%,
the position is not correlated with the investor's human capital, and the investor has
explicitly asked for it. A holding an investor wants and understands is easier to keep
than a holding they resent, and holdability is in the objective. That is a
behavioural-and-preference argument, not an evidence argument, and it should be written
down as one.

**Vehicle and account.** Spot ETPs are **1933-Act grantor trusts, not 1940-Act funds**: no
K-1, gain and loss flow through as if the holder owned the coin, brokers report on 1099-B,
and each sale of coin to pay the sponsor fee is a taxable disposition for the holder. **The
28% collectibles rate that applies to a physically-backed gold trust is not asserted here** —
IBIT's own prospectus tax section contains no collectibles discussion at all, and the IRS
treats bitcoin as property that can be held as a capital asset. Fees and sizes from each
trust's Q2-2026 Form 10-Q, net assets as of 2026-06-30, read 2026-08-22:

| Ticker | Sponsor | Fee | Net assets 2026-06-30 | Prices against |
| --- | --- | ---: | ---: | --- |
| **BTC** (Grayscale Mini) | Grayscale | **0.15%** | $3.19bn | CoinDesk Bitcoin Benchmark Rate |
| EZBC | Franklin Templeton | 0.19% | $335M | CME CF BRRNY |
| BITB | Bitwise | 0.20% | $2.13bn | CME CF BRRNY |
| HODL | VanEck | 0.20% — **full waiver expired 2026-07-31** | $959M | MarketVector |
| ARKB | ARK 21Shares | 0.21% | $1.89bn | CME CF BRRNY |
| **IBIT** | BlackRock | 0.25% | **$43.4bn** | CME CF BRRNY |
| FBTC | Fidelity | 0.25% | $10.3bn | Fidelity Bitcoin Reference Rate |
| GBTC | Grayscale | **1.50%** | $8.14bn | CoinDesk Bitcoin Benchmark Rate |

**Two rows have been re-read since, and both hold.** HODL's waiver expiry has now passed, and
the same Form 10-Q (filed 2026-08-13, read 2026-08-24) states the rate on the far side of it:
the Sponsor Fee is 0.20% of average daily net assets, the waiver of it on the first $2.5bn ran
"from November 25, 2024 through July 31, 2026", and "[a]fter July 31, 2026, the Sponsor Fee will
be 0.20%". EZBC's Q2-2026 10-Q (filed 2026-08-14, read 2026-08-24) accrues its sponsor fee "at
an annualized rate equal to 0.19%". **Data aggregators showed 0.25% and 0.29% for these two on
2026-08-22 and both readings are wrong**; the fee of a 1933-Act grantor trust is in its own
quarterly filing, and a fee under waiver is where an aggregator is most likely to be stale.
Sizes move faster than fees: **IBIT was $58.78bn at 2026-08-22** against the $43.4bn above,
which is a later date and mostly mark-to-market rather than flow, and every other net-asset
figure in the table is still as of 2026-06-30.

**Only six of eleven US spot bitcoin ETPs price against the CME CF rate**, and the
methodologies genuinely differ: at 4:00 p.m. ET on 2026-06-30 the same bitcoin was marked at
$58,605 (BRRNY, an hour-long volume-weighted median across seven venues), $58,717 (Lukka
Prime), $58,732 (CoinDesk) and $58,745 (Grayscale's single principal market) — **23.8 bp of
dispersion at a single instant**, from audited filings. That is small, it is the benchmark
working rather than failing, and it is the reason this repository's own FRED `CBBTCUSD` leg
is labelled one venue's print rather than the asset.

Hold it in **taxable**: it pays no income, so a tax-deferred account wastes shelter a bond
would use, and a taxable holding preserves the loss-harvesting option that a 75% drawdown
makes unusually valuable. **Avoid the crypto covered-call and "income" funds entirely** —
their headline distribution rates run 27% to 73% against 30-day SEC yields of 0.3% to 3.8%,
and at least one fund's most recent 19a-1 notice estimates the distribution as **100%
return of capital**. That is your own money handed back with a tax form attached.

**What would change this — and one condition has moved.** The three triggers were a
correlation to equity back below +0.2 on a window containing a recession; **a cash-flow
claim with a contractual payer**; or a realised equity bear market in which the asset does
not fall harder than equity.

The second has partially arrived, and not for bitcoin. **Rev. Proc. 2025-31** created a
safe harbour letting a grantor trust stake proof-of-stake assets without losing trust
classification, and staking ETPs are now live and material: Grayscale's ETHE and ETH stake
about 82% and 83% of their ether and **recognised $18.8M and $16.9M of staking income in
H1 2026 against $0 in 2025**, and BlackRock launched a separate staked trust (ETHB, 86.9%
staked) rather than turning staking on inside ETHA. That is a genuine contractual payer —
the protocol pays for validation — and it is the first thing in this family that is a yield
rather than a price expectation. **The economics, from the Q2-2026 Forms 10-Q, are small.**
The gross reward runs about 1.9% annualised on average net assets; ETHE's 2.5% sponsor fee
exceeds its staking income, so its net investment result is a loss and its carry is
negative; ETH (mini, 0.15%) keeps most of it; ETHB nets about 1.9% after a 0.12% waived fee
and the sponsor's share of rewards, paid monthly in cash. The holder recognises the reward
as ordinary income as earned, whether or not cash is distributed (Rev. Rul. 2023-14), and
the sponsor fee is a non-deductible miscellaneous itemised expense. **It is also not
bitcoin**, it carries slashing and validator risk, and a 1.9% gross yield on an asset that
fell 67% from its 2025 high is a coupon on a price bet. It is a reason to reopen the *ether*
question with a real estimand, not a reason to raise a bitcoin weight.

---

## 4. Tail hedging: the bleed is measured, and the cheaper substitutes win

**Verdict. Reject explicit tail hedges. The investor's stated requirement — "assets that
perform better in black swan events without excessive long-term drawdowns" — is best met
on this evidence by (a) a larger short-Treasury and cash allocation, (b) the trend overlay
already held, and (c) not holding the levered and concave things in §1.4. An option-based
hedge converts a diffuse long-term drawdown into a certain annual bleed, which is a
different risk, not less of it.**

**The mechanism, stated honestly.** A long put is the short side of the variance risk
premium. Index options have been persistently rich relative to subsequent realised
volatility because someone is being paid to bear crash risk — and a tail-hedge fund's
investor is the one paying. The strategy is therefore **negative expected return by
construction**, and the case for it can only ever be that a convex payoff at the right
moment is worth more than the premium. That is a claim about the *path*, and it requires
the holder to monetise the hedge at the bottom, which is the moment they are least likely
to.

**The bleed, from issuer-published standardised returns.**

| Fund | Structure | Fee | Window | Annualised NAV return | Same-issuer benchmark |
| --- | --- | ---: | --- | ---: | --- |
| **TAIL** (Cambria Tail Risk) | 1940-Act ETF; ~91% 10-year Treasuries, ~5% long OTM SPX puts | 0.59% | since inception 2017-04-06, as of 2026-06-30 | **−7.15%/yr, −49.59% cumulative** | SPY 10-yr 15.35%/yr (SSGA factsheet, same date; the windows differ by 0.77 yr) |
| **CAOS** (Alpha Architect Tail Risk) | 1940-Act ETF; protective SPX/SPY puts, put spreads, box-spread collateral | 0.63% gross = net | 10 years to 2026-07-31 | **+3.00%/yr** | SPY +14.93%/yr, identical window, both issuer-published |

Read 2026-08-22 from the [TAIL factsheet PDF](https://cambriafunds.com/assets/docs/TAIL-FactSheet.pdf),
the [Alpha Architect CAOS page](https://funds.alphaarchitect.com/caos/) and the
[SSGA SPY page](https://www.ssga.com/us/en/intermediary/etfs/spdr-sp-500-etf-trust-spy).
Two cautions that belong with the numbers: **do not use the figures rendered on
`cambriafunds.com/tail`** — that page is JavaScript-hydrated and returns numbers
irreconcilable with the issuer's own PDF; and **CAOS's ten-year record is inherited** from
the Arin Large Cap Theta mutual fund, a differently-mandated, higher-turnover predecessor,
with only about 3.4 years of it as the current ETF
([497K](https://www.sec.gov/Archives/edgar/data/1592900/000182912623001899/easeries-caos_497k.htm)).

**The bleed is roughly 12 pp/yr against the index on the honest comparison (CAOS, identical
window, both figures issuer-published) and worse on the pure hedge.** To first order a 10%
TAIL sleeve funded pro rata would have cost about **2.2 pp/yr** of portfolio growth over its
life — `0.10 × (−7.15 − 15.35)` — which is roughly four times the entire measured marginal
value of the trend overlay at the same weight in §1.5. That is arithmetic on two annualised
returns over slightly different windows, not a backtest.

**The calendar years say something the annualised figure cannot, and it is the decisive
thing.** From TAIL's own prospectus bar chart and the issuer's return feed, read 2026-08-23:

| 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2026 YTD |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| +2.33 | −13.99 | **+6.98** | −12.81 | **−13.15** | −12.98 | −9.98 | −8.33 |

**TAIL made 6.98% in 2020, the year of a 33.9% peak-to-trough fall in the S&P 500. And it
lost 13.15% in 2022, a year the S&P 500 returned −18.11%.** A put-buying programme
collateralised with Treasuries loses on both legs when a bear market is a slow grind with
rising rates rather than a volatility spike, and 2022 was the second kind.
**A crash hedge that loses money in a bear market is a bet on the shape of the decline
rather than a hedge.** On the same feed the fund's since-inception return to 2026-07-31 is
**−7.30%/yr, −50.64% cumulative**, its trailing five years **−9.06%/yr**, and its assets
**$147.6M** at 2026-08-21. *(TAIL's 2025 calendar return is deliberately absent: no primary
source publishes it yet — the issuer shows trailing periods only and the next prospectus
bar chart has not been filed. Cambria's own two sources also disagree by one day on the
inception date, 2017-04-05 in the SEC 485BPOS against 2017-04-06 on the fund page.)*

**And the distribution has the other tail too.** Simplify's **CYA**, launched
**2021-09-14**, reported **−99.16% since inception** on the issuer's own site at
2023-12-31, took a **1-for-20 reverse split effective after the close on 2024-02-09**
([SEC 497](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=CYA&type=497),
filed 2024-01-23) and was liquidated **"on or about March 14, 2024"** (SEC 497 filed
2024-02-20). Its last filed net assets, in the Form N-PORT for 2023-12-29, were about
**$2.16M**; no filing covers the final quarter, so the frequently repeated "$1.7M at
liquidation" is unconfirmed and is not used here. **A total loss on a product sold as crash
protection, over a period that contained a bear market.** CYA is also the seventh ticker in
Simplify's run of alternative-strategy closures — SCY, SPQ, FIG, NXTV, EQLS and WUSA all
last traded 2025-05-23, about fourteen and a half months after CYA — which is the
survivorship point: **a shelf screened today shows the products that lived.**

One point in TAIL's favour, because it changes what the number means without changing the
verdict: **TAIL is about 91% ten-year Treasuries and only about 5% options**, so its
−7.15%/yr is not all option bleed — a large part of it is the worst bond market in forty
years, and §1.2 already shows that Treasuries lost 13.6% through 2022. The option leg's own
cost is nearer the adviser's stated spend of roughly 1% of assets a month on puts. That
makes TAIL a *worse* proposition rather than a better one for this investor: the Treasury
part they can buy for 3 bp, and the part they are paying 59 bp to obtain is the part with
negative expected return.

**Long volatility is worse, and the reason is arithmetic.** VIX futures were in steep
contango across the whole visible curve on the last settlement before this page was
written: spot VIX 15.13 against 17.50 for September and 19.15 for October
([Cboe VIX futures](https://www.cboe.com/tradable_products/vix/vix_futures/), read
2026-08-22; the page carries no timestamp, so these are most likely the 2026-08-21
settlements). A constant-one-month index rolling M1→M2 pays roughly that spread every
cycle. The consequence is in the issuer-published returns: **VIXY −46.56%/yr over ten
years and UVXY −71.37%/yr**, NAV as of 2026-07-31
([ProShares](https://www.proshares.com/our-etfs/strategic/vixy)). These are also
**commodity pools, not 1940-Act funds, and they issue K-1s**; VXX is an **unsecured
Barclays note** maturing 2048, callable by the issuer at its sole discretion, and subject
to UK bail-in powers, with a tax treatment its own prospectus calls uncertain
([424B2](https://www.sec.gov/Archives/edgar/data/312070/000095010324010593/dp215108_424b2-vxxvxzps.htm),
read 2026-08-22). None of this belongs in a long-horizon portfolio.

**Buffered and defined-outcome funds are the same trade at a worse price.** This repository
has already priced the cap-and-buffer package from 1,183 overlapping twelve-month price
returns and found it worth **−2.4 to −4.1 pp/yr**, with the funds' realised −4.1 landing
inside that range from disjoint data ([evidence base](evidence-base.md)). Current shelf
facts are consistent: the July buffer series carries a **0.79% fee** for a 9% buffer
against an 18.14% cap, and the 100%-protection two-year funds cap at 13.61% and 18.32%
([Innovator factsheets](https://www.innovatoretfs.com/pdf/BJUL_Factsheet.pdf), read
2026-08-22). Two structural notes worth keeping: **Innovator's benchmark on its own
factsheets is the S&P 500 price-return index**, which omits dividends and flatters the
comparison; and because the FLEX options are written on **SPY and VOO rather than on a
broad-based index**, they are generally *not* §1256 contracts and get no 60/40 treatment —
unlike TAIL's and XTR's listed SPX options. Innovator has been an indirect wholly-owned
Goldman Sachs subsidiary since 2026-04-01
([497](https://www.sec.gov/Archives/edgar/data/1415726/000121390026038588/ea0284508-01_497.htm)),
which is a counterparty-and-continuity fact rather than a pricing one.

**What the investor should hold instead, and why it is not a compromise.** §1.3 measures
it: in the worst decile of equity months, swapping 10% of equity into T-bills adds back
**+0.92%** in the average month, at zero fee, zero drawdown and zero path risk. Long
Treasuries add +0.94% — two basis points more — and charge 8.42% of volatility and a −59%
drawdown for the privilege. Trend adds +1.08%. No option structure on the current shelf
offers a lower-tail offset larger than those *net of its bleed*, and the two that come
closest do it by holding Treasuries and spending 1% of assets a month on options.

**One structural defensive worth naming so it is not re-screened.** BTAL (AGF U.S. Market
Neutral Anti-Beta) is the non-option version of the same idea, and it is BAB's short side.
Its **gross expense ratio is 1.65% and its net is 1.40%** — the 0.45% "adjusted" figure
excludes dividend and brokerage expense on short positions, which is where the cost
actually is — and its since-inception NAV return is **−3.63%/yr against the S&P 500's
+15.41%** ([AGF factsheet](https://www.agf.com/agf-files/us/regulatory-documents/fact-sheets/agf-btal-ann-en.pdf),
as of 2026-07-31, read 2026-08-22). It also changed from index-tracking to active in
2022-02. §1.4 explains the shape: the anti-beta leg is BAB's mirror, and BAB's measured
concavity is *t* = 3.49. Reject.

---

## 5. Catastrophe bonds: the vehicle problem is solved and a price problem has replaced it

**Verdict. Admit the mechanism; hold at 0–3% or wait. This is the only candidate on the
page whose loss trigger is meteorological rather than financial, and the access finding
has genuinely changed — a 1940-Act ETF now exists with daily liquidity at 1.58% net. But
the risk spread has compressed by roughly half since 2023, and the net-of-fee record of
actual retail vehicles over nine years is about one percentage point a year over cash.
The reopening condition is a number, and it is stated below.**

**The mechanism, and why it is the best one on this page.** An insurer or reinsurer with a
concentrated peak-peril exposure — Florida wind, California quake — cannot retain it under
its own regulatory capital rules and cannot always cede it to the traditional reinsurance
market at an acceptable price. It sells the risk to capital markets through a special-purpose
vehicle: the investor's principal sits in Treasury money-market collateral, the investor
receives that collateral yield **plus** an insurance risk spread, and loses principal if a
defined event occurs. **The payer is a balance sheet with a statutory capital constraint, and
the loss trigger is a hurricane.** Nothing else screened here has a return whose driver is
outside financial markets entirely.

**What it has actually paid, and the two indices are not interchangeable.**

| Year | Swiss Re Global Cat Bond TR (cat bonds only, gross) | Eurekahedge ILS Advisers (fund NAVs, net of fees) |
| --- | ---: | ---: |
| 2017 | unverified | **−5.57%** |
| 2018 | unverified | −3.92% |
| 2019 | unverified | +0.92% |
| 2020 | unverified | +3.51% |
| 2021 | unverified | +0.85% |
| 2022 | **−2.16%** — first negative year in the index's history | −2.16% |
| 2023 | **+19.69%** (record) | +13.89% |
| 2024 | +17.29% | +13.10% |
| 2025 | +11.40% | +11.32% |
| 2026 to date | +4.12% (H1) | +5.02% (through July) |

Swiss Re figures as reported by [Artemis](https://www.artemis.bm/) and, for 2022, from
Swiss Re's *ILS Market Insights* March 2023; ILS Advisers from Artemis. Read 2026-08-22.
Swiss Re's pages return HTTP 403 and were not fetched directly.

**Compound the second column and the case gets much quieter. The ILS Advisers fund index
returned +3.31%/yr geometric over 2017–2025** — nine years that include the three best in
the market's history — against a US T-bill rate that averaged something close to 2.3% over
the same span. **That is roughly one percentage point a year over cash, net of fees, from
the actual vehicles.** The gap between the two columns is the cost-and-implementation gap
that this entire page keeps rediscovering: Swiss Re ran 17.29% in 2024 against 12–15% for
most managed funds.

**The 2022 week is the shape of the risk.** The Swiss Re index was −0.35% at the half-year
and then fell **−9.65% in the single week to 2022-09-30** on Hurricane Ian. SHRIX's worst
quarter is Q3 2022 at −10.29%. This is not a smooth carry.

**Cascading loss is the failure mode that a correlation cannot see.** Roughly **36% of the
outstanding market is annual-aggregate structure** ($22.78bn against $40.23bn occurrence),
where each qualifying event erodes the retention beneath the attachment point, so a season
of moderate events leaves a bond exposed to a later event it would have survived standalone.
The 2024–25 sequence is the clean illustration: Helene and Milton eroded aggregate retentions
in autumn 2024, and the January 2025 Palisades and Eaton wildfires landed **inside the same
annual risk period** for Allstate's Sanders Re programme — two tranches were marked down
about 50% **purely on the increased probability of attaching over the remaining risk period,
with no payout having occurred**. Peak-peril concentration compounds it: explicitly
named-storm buckets are 24.2% of outstanding and every bucket containing any US wind
totals 56.1%, so "diversified across perils" is a weaker claim than it sounds.

**The price. This is the part that decides the weight.**

| | 2023 peak | Mid-2026 | Change |
| --- | ---: | ---: | ---: |
| Secondary risk spread | **11.31%** (2023-01-13) | **5.53%** (2026-07-31) | −51% |
| Secondary spread ÷ expected loss | 4.90× | **2.21×** | **−55%** |
| New-issue spread above expected loss | 6.94% FY2023 | 3.98% YTD, **3.74% in Q2 2026** | −43% |
| New-issue multiple | 4.54× FY2023 | **2.40×** YTD | −47% |

Artemis market data, read 2026-08-22. Q2 2026 was the first quarter below 4% spread-above-EL
in twenty. The arithmetic that follows is simple and should be done before buying: a 5.53%
risk spread against a 2.50% market-average expected loss leaves about **3.0 percentage
points of gross expected compensation**, from which a retail vehicle takes **1.58% to
2.36%**. What is left is roughly one point a year of expected excess over the collateral
yield — which is exactly what the fund index has delivered — for an asset that can lose 10%
in a week.

**Access, which is the part that has changed.**

| Vehicle | Structure | Fee | Minimum | Liquidity | Net assets |
| --- | --- | ---: | ---: | --- | ---: |
| **ILS** (Brookmont Catastrophic Bond ETF) | 1940-Act **ETF**, active, non-diversified; inception 2025-04-01 | **2.65% gross / 1.58% net**, capped to 2027-04-30 | none | daily | $88.2M (2026-08-20) |
| SHRIX / SHRMX (Stone Ridge High Yield Reinsurance) | **open-end mutual fund**, daily redemption | 1.73% (I) / 1.88% (M) | $25M (I) / **$250k (M)** | daily | $4.44bn (2026-04-30) |
| XILSX (Victory Pioneer ILS) | interval fund, Rule 23c-3 | 1.94% | $1M | quarterly, 10% offered | ~$822M |
| SRRIX (Stone Ridge Reinsurance Risk Premium) | interval fund | 2.36% | **$15M** | quarterly, 5% + 2% discretionary | $1.52bn (2026-04-30) |
| CNRLX (City National Rochdale Select Strategies) | interval fund | 1.00% gross / **0.99% net** | $1M | quarterly, 5% | $234.5M (2026-01-31) |

Read 2026-08-22 from SEC filings and issuer pages. **Four corrections to the usual account
of this shelf, each of which changes a conclusion.** SHRIX is *not* an interval fund — it is
an open-end mutual fund with daily redemption, which removes the liquidity objection
entirely for an investor who can meet the $250k Class M minimum. **SRRIX is not a cat bond
fund**: at 2026-04-30 it held **19.4% event-linked bonds and 65.2% private quota-share
paper**, so comparing its 2.36% with an ETF's fee is not like for like. **CNRLX's 0.99% is
materially understated** — its own prospectus says the Neuberger Berman segregated accounts
have fees "not reflected in the fee table," and they never appear as acquired-fund expense.
And none of these funds imposes an accredited-investor or qualified-purchaser test; the
gate is minimum size, not investor status.

**On the ETF specifically**, which is the vehicle that makes this reachable at all: it holds
144A cat bonds inside a 1940-Act wrapper because **Rule 144A securities are not automatically
illiquid** — a board-approved liquidity risk management program classifies each holding
against the 15%-of-net-assets illiquid cap, and at 2025-12-31 144A paper was **85.4% of net
assets with 100% of holdings at Level 2 and no Level 3 at any point in 2025**. That is a
defensible answer to the obvious objection. Two cautions remain: it **trailed its own stated
benchmark by 430 bp** over its first nine months (+5.87% against the Swiss Re index's
+10.17%), and its **tailored shareholder report shows costs actually paid of 2.00%
annualised**, not the 1.58% cap.

**Where it belongs and what would change the verdict.** Tax-deferred, without exception:
the return is almost entirely ordinary income and short-term gain. **The reopening condition
is the spread-to-expected-loss multiple.** At 2.21× secondary and 2.40× new issue this is
the least attractive entry the market has recorded in the period observed here. At **3.5× or
above**, with the retail fee unchanged, the arithmetic gives roughly two and a half points a
year over collateral for genuinely non-financial risk, and the weight should rise. That is
a monitoring boundary, it is publicly observable weekly, and it is the reason to keep this
family open rather than screen it again from scratch.

---

## 6. Duration-hedged credit: the rejection was about the instrument, not the mechanism

**Verdict. Admit. This is the largest single change this page makes. The earlier finding
that "credit is not a second engine, its correlation to Treasuries is +0.835" is
reproduced here at +0.826 — and it is a property of the *unhedged* corporate leg. The
duration-hedged credit spread correlates +0.016 with long Treasuries over 1,068 months.
It is a separate engine, and it was rejected because the instrument that measured it had
twenty years of duration bolted to the front.**

**The mechanism.** Insurers, pension funds, banks and rating-constrained mandates must hold
investment-grade paper and cannot bear either default loss or mark-to-market volatility in
it. They pay a spread above a duration-matched Treasury for that. The payer is a balance
sheet with a regulatory or actuarial constraint, which is why the premium has survived a
century of publication: the buyer is not choosing to bear the risk cheaply, they are
required not to bear it at all.

**What is measured.** AQR's `CORP_XS`, defined as the corporate bond total return less a
duration-matched government return estimated by rolling empirical-duration regressions,
1926-01…2014-12. On the 1,062 months it shares with the equity and Treasury legs:

| | Geo/yr | Vol/yr | Sharpe | Max DD | ρ to equity | ρ to Treasury |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Long Treasury | +2.10% | 8.37% | +0.29 | −59.1% | +0.094 | 1 |
| **Duration-hedged credit** | **+2.13%** | **4.12%** | **+0.53** | **−20.7%** | +0.234 | **+0.016** |
| Equity | +6.28% | 18.71% | +0.42 | −84.6% | 1 | — |

**Identical return to long Treasuries, at half the volatility and a third of the
drawdown.** It is also nearly distinct from everything else on the panel: ρ −0.082 to
trend, +0.064 to commodities, −0.050 to gold.

**The honest counterweight, because this is a `risk-premium` and not a hedge.** Its mean in
the worst decile of equity months is **−0.24%**, its lower-tail offset at 10% weight is
+0.91% against cash's +0.94%, and it lost **13.1% through the GFC** while Treasuries gained
13.4%. Credit's left tail is the same corporate-default state that kills equity. Add it for
*return breadth*, never for crisis protection.

**Which is why the recommendation is a substitution, not an addition.** Holding half the
defensive sleeve in each is better than holding it all in long Treasuries on almost every
axis measured:

| Defensive sleeve, 1926-07…2014-12 | Geo/yr | Vol/yr | Sharpe | Max DD | 1929-32 | 1973-74 | Late 1970s | 2000-02 | **2008-09** |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| All long Treasury | +2.10% | 8.37% | +0.29 | −59.1% | +7.8% | −17.3% | **−40.5%** | +23.3% | +13.4% |
| All duration-hedged credit | +2.13% | 4.12% | +0.53 | −20.7% | +5.7% | −6.9% | −3.2% | +10.8% | **−13.1%** |
| **Half each** | **+2.23%** | **4.70%** | **+0.49** | **−27.1%** | +7.1% | −12.1% | −23.3% | +17.2% | **−0.0%** |

The blend is flat through the GFC and loses 23% rather than 41% through the late 1970s,
because the two legs fail in different states and correlate +0.016. That is what breadth
is supposed to look like, and it is available inside the allocation the investor already
intends to make.

**The scale problem, stated plainly.** At 4.12% volatility a 10% sleeve contributes about
21 bp/yr of gross excess return, which is inside this repository's 0.58 pp/yr detection
floor. **This engine cannot be made to matter at a satellite weight.** It matters as a
*replacement* for defensive assets already held, or not at all. Levering it to Treasury
volatility (2.03×) doubles the return to +4.20%/yr at the same Sharpe — and takes the
drawdown to −39.2% and the GFC loss to −26.6%, which is the whole point of not doing that.

**What would change this.** The series ends in 2014-12, so **it has never been measured
through 2020 or 2022** — the two episodes in which a hedged-credit sleeve's behaviour would
be most informative, since March 2020 was a liquidity event in exactly this instrument.
Acquiring a duration-hedged credit series that reaches 2026 is the single most decision-
relevant acquisition this page identifies. It also has no net-of-cost version: `CORP_XS` is
a vendor construction, gross of fee, spread and financing, and the retail wrapper's real
cost is what decides whether +2.13% survives.

### 6b. Retail access, and the conditions the sleeve would be bought into

**The vehicle exists, it is cheap, and it does exactly what the series describes.** The
iShares rate-hedged funds are fund-of-funds: they hold the underlying credit ETF and
overlay centrally-cleared interest-rate swaps at the 1, 2, 3, 5, 7, 10, 15, 20 and 30-year
points, weighted to the underlying's composition and **rebalanced daily**
([iShares product brief](https://www.ishares.com/us/literature/product-brief/ishares-interest-rate-hedged-etf-hygh-lqdh-embh-igbh-product-brief-en-us.pdf),
read 2026-08-22). ProShares does the same job with short Treasury futures and states an
explicit **target duration of zero**
([ProShares HYHG](https://www.proshares.com/our-etfs/strategic/hyhg)).

| Ticker | What it hedges | Gross ER | **Net ER** | Effective duration | OAS | 30-day SEC yield | Net assets |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **IGBH** | Long-term IG corporate (IGLB) | 0.39% | **0.14%** | **0.02 yr** | 91.8 bp | 5.21% | $237.3M |
| **LQDH** | IG corporate (LQD) | 0.44% | **0.24%** | **0.10 yr** | 81.4 bp | 4.65% | $545.7M |
| HYGH | High yield (HYG) | 1.12% | 0.52% | **−1.14 yr** | 236.3 bp | 5.97% | $618.8M |
| IGHG | IG, ProShares, bonds held directly | 0.30% | 0.30% | 0.42 yr | — | 5.29% | $341.9M |
| HYHG | High yield, ProShares, bonds directly | 0.50% | 0.50% | −0.09 yr | — | 6.97% | $200.2M |

Fees and durations as of 2026-08-20/21 from the iShares and ProShares product pages, read
2026-08-22. **The net figures depend on contractual waivers that expire 2027-02-28**; the
waiver sets total expenses equal to the underlying ETF's acquired-fund fee plus 10 bp
(LQDH, IGBH) or 5 bp (HYGH). If a waiver lapses the cost roughly doubles, and at a 2.13%/yr
gross premium that is not a rounding error.

**The category is shrinking, which is an implementation finding and should be recorded as
one.** iShares **liquidated AGRH**, the rate-hedged aggregate fund, effective 2026-08-17
(board approval 2026-06-12, trading halted 2026-08-13;
[prospectus supplement](https://www.ishares.com/us/literature/prospectus/p-ishares-us-etf-trust-hedged-index-10-31.pdf)),
and EMBH is no longer on the iShares screener. No new entrant was found in 2024–2026.
**A category that is losing funds while its mechanism is intact is a liquidity and
continuity risk, not a verdict on the premium.**

**A second, cleaner instrument for the same idea: AAA CLO tranches.** These reach near-zero
duration *natively* — they float over SOFR — rather than by overlaying a derivative on a
fixed-rate bond, so there is no swap carry, no daily rebalance, and no waiver to lapse.

| Ticker | What it holds | ER | Effective duration | 30-day SEC yield | AUM |
| --- | --- | ---: | ---: | ---: | ---: |
| **JAAA** | AAA CLO tranches (99.2% AAA) | **0.20%** | **0.06 yr** | 4.77% | **$28.4bn** |
| JBBB | BBB+ to B− CLO tranches | 0.47% | 0.09 yr | — | $1.3bn |
| CLOI | IG CLO tranches, VanEck/PineBridge | 0.36% | unverified | 5.03% | $1.53bn |
| CLOZ | BBB+ to B− CLO, Eldridge | 0.50% | unverified | — | $802M |

[Janus Henderson factsheets](https://cdn.janushenderson.com/webdocs/FactSheet_JAAA_ETF_2026_06_exp_2026_10.pdf),
data as of 2026-06-30; VanEck and Eldridge pages read 2026-08-22.
**The failure mode is different from corporate credit and must not be assumed away.** A
AAA CLO tranche is structured credit over leveraged loans; its risk is the correlation of
loan defaults and the behaviour of the structure's tests, not a single issuer's balance
sheet. JAAA launched in 2020-10, **so no CLO ETF here has a March 2020 record**, and March
2020 is precisely the liquidity event that would test it. Treat this as a candidate with an
excellent instrument and a short history — the mirror image of the corporate series, which
has a long history and a stale instrument.

**And the conditions it would be bought into are the least favourable part of the case.**
As of 2026-08-20/21, read from FRED and Treasury.gov on 2026-08-22:

| | Level |
| --- | ---: |
| 3-month CMT | 3.88% |
| 10-year nominal CMT | 4.74% |
| 30-year nominal CMT | 5.27% |
| **10-year TIPS real yield** | **2.40%** |
| **30-year TIPS real yield** | **3.00%** |
| 10-year breakeven | 2.34% |
| **ICE BofA US IG corporate OAS** | **82 bp** |
| **ICE BofA US high-yield OAS** | **275 bp** |

Two consequences, and they point in opposite directions.

**Against the credit sleeve: 82 bp is a tight spread.** The +2.13%/yr measured over 1,062
months was earned across the full range of spread regimes including 1932 and 2008. Buying
the engine at 82 bp of gross spread, before expected default loss and before a 14–24 bp
wrapper, is buying it near the bottom of its own distribution. This does not refute the
engine; it says the entry point is poor and the position should be small, or built over
time, or sized to the spread.

**For the defensive allocation generally: a 2.40% ten-year real yield and a 3.00% thirty-year
real yield are the strongest contractual terms available to this investor anywhere on this
page.** A TIPS held to maturity at 3.00% real is a *contractual* line — the certainty class
the repository reserves for statutes and accounting identities — against gold's measured
+1.75%/yr with a −91% drawdown and no coupon at all. When the risk-free real yield is 3%,
the hurdle every sleeve on this page has to clear rises with it, and the honest consequence
is that **more of the answer to "what should I add" is now "a better-constructed defensive
allocation" than it was when real yields were negative.**

### 6c. TIPS and nominal bonds are one engine, and that is not an argument against holding TIPS

Two facts that are frequently confused. **TIPS and nominal Treasury funds are not two
engines**: they correlate **+0.761 to +0.851** across eighteen bond and TIPS ETFs' filed
monthly returns and +0.798 on the modelled long series, against the 0.75 threshold
[capital efficiency](capital-efficiency-and-breadth.md) uses, so counting both toward
breadth is double counting. **But their equity relationship genuinely differs in sign** —
TIPS **+0.131** against nominals' **−0.076** on identical months, a gap of 3.5 standard
errors — and nominal bonds' correlation to equity is decisively era-dependent, spanning
**0.802 across twelve 60-month blocks**, positive in seven and negative in five. Full
working and provenance in [the evidence base](evidence-base.md).

The consequence is a **liability** argument rather than a breadth argument, and it is
stronger at today's real yields than it has been in twenty years: an investor whose future
spending is in real terms is matched by a real bond, and the era-dependence above is exactly
the risk that a nominal bond leaves on the table. Hold TIPS because they match the
liability, size the defensive sleeve as one engine, and take the diversification from §6's
credit leg instead — which is where it actually is.

---

## 7. Trend beyond the one already held: the mechanism is unchanged, the price is not

**Verdict. Do not add a second trend engine — it would be the same engine twice. But the
delivery cost of the one already held has fallen by roughly an order of magnitude, and
that is a live implementation finding worth acting on.** The evidence on trend itself is
owned by [trend](trend-marginal-value.md) and [live managed futures](live-managed-futures.md)
and is not restated here; §1.3 and §1.4 above add only that its crisis case is an alpha of
+0.91%/month (*t* = 3.09) with **no statistically resolvable convexity**, and that it is
the single engine on this panel that materially beats cash in the lower tail.

**What has appeared on the shelf since the last audit** (all read 2026-08-22 from issuer
pages; verify fee, waiver expiry and AUM before transacting):

| Ticker | What it is | Fee | AUM | Inception | Note |
| --- | --- | ---: | ---: | --- | --- |
| **CTAP** | Simplify US Equity PLUS Managed Futures — 100% notional US large-cap **plus** 100% notional systematic managed futures | **0.28% gross / 0.10% net**, waiver through 2026-12-04 | $157.9M | 2025-12-08 | A financed trend overlay at ten basis points |
| **SDMF** | Simplify DBi CTA Managed Futures Index ETF | **0.35%** | $39.2M | 2026-02-17 | Cheapest standalone managed-futures ETF found |
| **JPFP** | JPMorgan Managed Futures Plus | 0.59% | unverified | 2026-05-28 | New entrant; AUM and structure unverified |
| **RSIT** | Return Stacked International Stocks & Managed Futures | 0.98% | $68.5M | 2026-05-06 | The ex-US twin of RSST |
| RSST | Return Stacked US Stocks & Managed Futures | 0.99% | $505.0M | 2023-09-05 | The incumbent comparison |
| DBMF | iMGP DBi Managed Futures Strategy | 0.85% | $4.00bn | 2019-05-07 | The replication fund [Experiment 008](trend-marginal-value.md) found delivers the index's exposure |
| KMLM | KraneShares Mount Lucas Managed Futures | 0.90% | $392.7M | 2020-12-01 | |
| CTA | Simplify Managed Futures Strategy | 0.75% | $1.63bn | 2022-03-07 | |

Sources: [Simplify fund pages](https://www.simplify.us/etfs),
[Return Stacked prospectus 2026-04-27](https://www.returnstackedetfs.com/wp-content/uploads/pdf/return-PRO.pdf),
[iMGP](https://www.imgp.com/us/fund/US53700T8273-imgp-dbi-managed-futures-strategy-etf/),
[KraneShares](https://kraneshares.com/kmlm).

**Why the fee matters more than it looks.** The trend sleeve's measured marginal value at
10% weight is **+0.580 pp/yr gross**, which is exactly the design's own detection floor.
A 99 bp wrapper consumes 10 bp of that at a 10% weight; a 10 bp wrapper consumes 1 bp.
That does not make the sleeve resolvable — it is still inside the floor — but it removes
the one term in the arithmetic that was **known** to be working against it. The
financed-overlay funds ask a more favourable portfolio question than a pro-rata sale
of the core, which is the point [capital efficiency](capital-efficiency-and-breadth.md)
makes about funding rules.

**Three cautions that travel with the whole category.** These wrappers hold futures through
a **Cayman controlled foreign corporation** to keep the income RIC-qualifying, which is
what lets them issue a 1099 rather than a K-1 — CTA, KMLM, SDMF and CTAP all state "K-1:
No" on their own pages, and the Return Stacked funds are 1940-Act RICs (their 1099 status
is an inference from that, not an issuer statement). **No issuer in this set discloses a
numeric financing cost**; the only hard figure available is the Return Stacked funds'
interest-expense ratio of under 0.005% of average net assets for the year ended 2026-01-31,
which reflects derivative-embedded rather than borrowed financing. And CTAP's 10 bp is a
**waiver expiring 2026-12-04**, not a fee.

**Where the sleeve belongs.** Tax-deferred. Managed-futures funds distribute
short-term gains and interest income, and a financed stack distributes both legs.

---

## 8. Gold and commodities: right about the state, wrong about the state that hurts

**Verdict on gold. Optional, at most 5%, and only as a replacement for cash or bonds —
never funded by selling equity. A financed wrapper changes the funding question and does
not change the expected return. The finance-free version of the argument is in §1.3: gold
buys twelve basis points a month of lower-tail protection over T-bills, at 16.24%
volatility and a −91.2% peak-to-trough.**

**Verdict on long-only commodities. Reject as a diversifier; consider only if the investor
has a specific inflation liability.** Their mean in the worst decile of equity months is
**−1.84%**, positive in only 36% of them, with ρ low **+0.326** — they fall *with* equity
in equity crises and pay only in the inflation shocks (1973-74 **+143.9%**, 2022 +10.5%).
That is a real and valuable property, but it is a hedge against a different state, and the
investor should not buy it believing it is a crash hedge.

**Does a financed wrapper change the gold answer?** No, and it is worth being precise about
why. GDE (WisdomTree Efficient Gold Plus Equity Strategy Fund) holds US large-cap equity
plus US-listed gold futures, at **0.20%** with **$496.0M** of net assets, inception
2022-03-17
([factsheet](https://www.wisdomtree.com/-/media/us-media-files/documents/resource-library/fund-fact-sheets/asset-allocation/en-us_capital-efficient-etfs_gde.pdf),
data as of 2026-06-30, read 2026-08-22). Its own
[summary prospectus](https://www.sec.gov/Archives/edgar/data/1350487/000121465925018663/gde497k1225.htm)
dated 2026-01-01 says "approximately equal exposure" to the two legs, rebalanced quarterly,
with the gold leg run through a **Cayman subsidiary capped at 25% of total assets at each
fiscal quarter-end** to preserve RIC source-of-income qualification — so the "90/90"
marketing shorthand is not the prospectus language, and **whether §1256 60/40 treatment
reaches the shareholder is unverified**: gains realised inside a wholly-owned controlled
foreign corporation are generally not passed through with that character, and the
prospectus is silent. What the wrapper changes is the **funding rule**, and
[the marginal-sleeve work](marginal-sleeve-value.md) has already measured that the funding
rule flips gold's sign: −0.404 pp/yr at 10% funded pro rata against +0.18 to +0.22 financed.
What it does not change is that both estimates sit inside the design's 0.63–1.04 pp/yr
detection floor, or that gold's excess return over half a century has been **+1.75%/yr at
a Sharpe of 0.18**. **A cheaper wrapper for an uncertain expected return is a cheaper
wrapper, not a better expected return.** GDE also converts a grantor-trust holding taxed at
the 28% collectibles rate into a 1940-Act fund that is not — which is a genuine tax
improvement and should be scored as one, in the tax work rather than here.

**One thing the financed form does buy, and it is the honest case for it.** Because GDE's
gold leg is notional, holding it does not require selling equity. §1.5 measures that a
pro-rata gold sleeve costs −0.40 pp/yr at 10%; a notional one costs its financing rate and
its fee instead. For an investor who wants gold's inflation-state payoff and does not want
to reduce equity to get it, that is the correct instrument. The reason this page still caps
it at 5% is §1.3: gold's crisis contribution over cash is 12 bp a month, and financing does
not make that number larger.

**Inside the leveraged construction the financed form reads `unresolved`, and the verdict
holds.** Experiment 018 ([run `311048fb…`](../../research/artifacts/311048fbc6b44072a3715ff24d1507a4/summary.md),
`exploratory`) stacked ten points of GDE-like gold on the 70% equity core plus 30% trend
wrapper. On 1968–2025 it reads **+0.35 pp/yr [−0.20, +0.94] against a 0.64 floor** against
the reference construction; drawdown −44.4% against −45.9%; +6.8 pp across the 1970s
inflation episodes, which is the state it is bought for. On the AQR 1985–2025 panel it is
+0.27 [−0.22, +0.75] against 0.61, and on the 2003–2025 check +0.80 [+0.21, +1.39] against
0.88. Gold financing at 30 bp is an assumption. With the real gold price at the 98.5th
percentile since 1975 ([current regime](current-regime-and-pricing.md) §1.7), the sleeve is
not added; the reopening condition is a measured gap that clears its own floor on a window
that does not begin in 1971.

**Commodity vehicles carry a structural tax split worth naming once.** The broad commodity
products divide into 1940-Act funds that hold futures through a Cayman subsidiary and issue
a **1099**, and commodity pools that issue a **K-1**. That difference is larger than the
fee difference between them for most investors, and it decides which account can hold the
position at all. Confirm the current form on the issuer's page before transacting; the
category has changed structure repeatedly.

**The long/short version is not a separate idea.** A carry- and momentum-aware long/short
commodity strategy is, mechanically, the commodity leg of a diversified trend programme —
which the investor already owns inside the managed-futures overlay. **Reject on overlap,
not on the premium.** The measured evidence agrees: the AQR long-only commodity series
correlates −0.064 with TSMOM, which is exactly what you would expect if the trend programme
is trading the same markets from both sides.

---

## 9. Screened and set aside, with the reason attached

Each of these arrived with a mechanism. Each is set aside for a stated reason, and the
reason is what a future round should attack.

**Ideas the repository had not previously considered.** These are the ones worth arguing
about.

| Idea | Who pays, and why | Why it is set aside | What would reopen it |
| --- | --- | --- | --- |
| **Prepaying a mortgage, treated as a negative bond** | Nobody — it is the removal of a liability. The return is the after-tax mortgage rate, risk-free, with **negative duration** and zero market risk | Not set aside on evidence: it is very likely the **highest-Sharpe action available to a household carrying debt above the after-tax Treasury yield**, and it is invisible to every experiment here because the repository models an asset portfolio rather than a balance sheet. It is illiquid and it forecloses cheap fixed-rate leverage if the rate is low | The investor's actual mortgage rate, balance, and whether they itemise. This is an **investor input**, not a market question, and it belongs in the parameterisation work |
| **Currency diversification of the cash sleeve** | Nobody. It is not a premium; it is the removal of a single-currency concentration in the one asset assumed to be safe | A US investor's liabilities are in dollars, so foreign-currency cash is a mismatch rather than a hedge, and unhedged FX adds volatility with no expected return. Defensible only against a *dollar-specific* purchasing-power shock, which is a scenario, not an estimand | A liability stream that is not dollar-denominated, or a study that prices a dollar-specific regime rather than assuming one |
| **Life settlements and longevity risk** | Insurers and policyholders. The premium is compensation for mortality timing, which has no financial-market driver at all | Genuinely uncorrelated in mechanism, but the retail vehicles are interval funds with 2–3% cost stacks, and — the decisive objection — **their reported NAVs are appraisals, not prices**. An appraised NAV manufactures a low measured correlation whether or not the economics are uncorrelated | A vehicle marking to observable transactions, or an independent index of realised settlement returns |
| **Litigation finance** | Claimants who cannot fund a case and want certainty. The return is legal-outcome risk plus an illiquidity premium | Same mechanism-good / measurement-bad shape as life settlements, plus duration uncertainty that makes an IRR unquotable | The same: an observable-price vehicle |
| **Trade finance and receivables** | Corporates outside bank credit appetite | It is credit, and it correlates with credit in exactly the state that matters. Greensill is the worked example | Nothing likely. It duplicates §6 with worse liquidity |
| **Farmland and timberland** | Tenants and mills, via rent and stumpage | The public vehicles are leveraged real-asset equities and trade with equity beta; the private ones are appraisal-marked | A holdings-based decomposition showing exposure that beta, value and duration cannot span |
| **Local-currency EM sovereign debt** | Investors unwilling to hold the currency. Real rate plus a currency risk premium | It is the funding-currency crash trade with a sovereign wrapper; it sells the same crash insurance §4 says not to buy, so it belongs on the concave side of §1.4 | A crisis-conditional measurement on this panel. The repository holds no local-currency EM series |
| **Municipal bonds** | The US Treasury, through §103. A statutory exemption, not a premium | Not a return engine at all. It is a **placement** decision whose answer is the muni/Treasury ratio against the investor's bracket | Belongs in [structural and tax edges](structural-and-tax-edges.md), not here |
| **Series I savings bonds** | The Treasury, contractually | A liability match with a statutory purchase cap, so it cannot be sized to matter | A change in the cap |

**Families screened in earlier rounds and left where they were.** The reasons below are
scoped conclusions about instruments and vehicles, not statements that the mechanism is
absent.

- **Volatility selling and put writing.** The premium is real — it is the same premium §4
  says not to pay. Rejected on **overlap**, not on the premium: it duplicates equity's own
  left tail, and its measured live-only alpha ran −0.09 to −0.88%/yr at correlations of
  0.86–0.95 to equity, with an up-beta of 0.45 against a down-beta of 0.86.
- **Merger arbitrage.** The mechanism is genuine — sellers of deal risk pay for certainty
  before a deal closes — and the vehicles are real, cheap enough, and liquid. They are also
  too small to move a portfolio. Ten-year annualised NAV returns to 2026-06-30, all
  issuer-published and all read 2026-08-22: **MNA +2.92%/yr at a 0.77% fee**
  ([NYLI factsheet](https://www.nylim.com/assets/documents/index-nyli/mna-nyli-merger-arbitrage-etf-fs.pdf)),
  **MERIX +4.29% and MERFX +3.98% at a 1.26%/1.55% net fee**
  ([Virtus factsheet](https://www.virtus.com/assets/files/4yo/the-merger-fund-enhanced-fact-sheet-1412.pdf)),
  and **ARB +4.25% since 2020-05** at 0.76%
  ([AltShares factsheet](https://altshares.s3.amazonaws.com/arb/Fact_Sheet-ARB.pdf)).
  Those are total returns over a decade whose average T-bill yield was itself a large part
  of them, so the excess is a low single digit at best, and the left tail is a break-risk
  loss that clusters with equity. **At any weight a retail investor would hold, the
  contribution is well inside the 0.58 pp/yr detection floor: unresolved, and too small to
  be worth resolving.** Two housekeeping facts: ARB and EVNT reorganise from AltShares
  Trust into identically-named series of The Arbitrage Funds on or about 2026-09-25 at
  identical fees
  ([497](https://www.sec.gov/Archives/edgar/data/0001105076/000110465926087563/tm2618099d2_497.htm)),
  and First Trust's MARB **stopped being a merger-arb fund on 2026-06-24**, becoming the
  Equity Market Neutral ETF (NTRL) at a 0.95% fee
  ([First Trust](https://www.ftportfolios.com/retail/etf/etfsummary.aspx?Ticker=NTRL)) —
  a reminder that a strategy shelf is not a market ontology.
  A stacked version exists, **RSBA** (100% US Treasuries + 100% merger arbitrage, 1.01%,
  $52.3M, inception 2024-12-17), which is the only form in which this premium could
  plausibly matter, because it does not compete with equity for capital.
- **Alternative-risk-premia and multi-strategy funds.** The examined shelf earned 0.3–1.0%/yr
  gross post-2019 at 2–5% volatility against a retail wrapper costing about 1.5%. **The cost
  stack, not the premia, is the finding.** The survivor worth naming is QAI (NYLI Hedge
  Multi-Strategy Tracker, 1.10% gross / **0.88% net**, $1.02bn, inception 2009-03-25), whose
  ten-year NAV return to 2026-06-30 is **+3.93%/yr**
  ([factsheet](https://www.nylim.com/assets/documents/index-nyli/qai-nyli-hedge-multi-strategy-tracker-etf-fs.pdf),
  read 2026-08-22) — a decade of hedge-fund replication that did not beat its own cash leg
  by much. Its index has held digital-asset ETPs at up to ±2.5% since 2026-05-01
  ([497](https://www.sec.gov/Archives/edgar/data/1415995/000199937126009637/qai-497_042226.htm)),
  which is a mandate change a holder should notice.
- **REITs and dividend funds.** Dominated on Sharpe at correlations of +0.82 and +0.84;
  REITs gave 112% of the downside for 80% of the upside. Not distinct engines by label.
- **Closed-end fund discounts, securities lending, direct indexing.** Retained as
  candidates with the same next questions as before: a point-in-time discount panel, better
  N-CEN/N-PORT lending measures by fund and year, and after-fee modelling under the
  investor's actual lots. None is a market-return engine; the last two are implementation
  lines and belong with [the structural work](structural-and-tax-edges.md).
- **Short-term reversal, accruals, net issuance, and other published anomalies.** Their
  post-publication premia sit inside the public library's own detection floor, and no
  adequate registered implementation exists on the audited shelf. **An implementation
  finding on the second clause, an underpowered null on the first.**

---

## 10. Consequence for the portfolio

### The ranked shortlist

Weights are **scenario sizings for the reference investor**, not an optimiser output, and
they are stated as ranges because the investor inputs that would narrow them — contribution
and withdrawal path, embedded gains, account capacity, tolerable drawdown — are still
missing. **Nothing here is promoted** — [decision 0004](../decisions/0004-no-sleeve-promoted.md)
stands, nothing on this page is `production-eligible`, and no measurement here was frozen
before its numbers were seen. What has changed is which candidates deserve a frozen
specification next, and one of them changed because the instrument that rejected it was
wrong.

| # | What to add | Weight | Mechanism, in one line | The marginal case | Account |
| ---: | --- | ---: | --- | --- | --- |
| 1 | **Restructure the defensive sleeve: half duration-hedged credit or AAA CLO, half short-to-intermediate Treasuries or TIPS** | within the existing defensive allocation | Rating-constrained holders pay a spread; short duration removes the era-dependent rate bet | Same return as long Treasuries at half the volatility and a third of the drawdown; the two legs correlate **+0.016** and the blend is flat through 2008-09 and loses 23% rather than 41% through the late 1970s | Tax-deferred |
| 2 | **Buy the trend exposure you already hold, more cheaply** | unchanged sizing | Unchanged | The sleeve's gross marginal value is +0.58 pp/yr at 10%; moving from a 99 bp wrapper to a 10–35 bp one returns roughly 6–9 bp of it, and removes the one term known to work against it | Tax-deferred |
| 3 | **Raise the cash and short-Treasury allocation instead of buying a tail hedge** | +0 to +10% | Not a premium — an absence of exposure, plus a 3.88% bill yield and a 2.40% ten-year real yield | Measured: swapping 10% of equity into T-bills adds **+0.92%** in the average worst-decile equity month, at no fee and no drawdown. Long Treasuries add +0.94%. Nothing on the option shelf beats it net of bleed | Either; taxable if muni-equivalent yields favour it |
| 4 | **Catastrophe bonds** | 0–3%, or wait | Insurers with statutory capital constraints buy peak-peril capacity; the trigger is a hurricane | The only non-financial risk driver screened. **But the spread-to-expected-loss multiple is 2.21× against 4.90× in 2023**, and the retail record is ≈1 pp/yr over cash across nine years net of fees. Size to the spread; reopen at **3.5×** | Tax-deferred, without exception |
| 5 | **Spot bitcoin** | 0–2% | None. There is no cash-flow claim | A declared speculation the investor wants to own, at a size where total loss is survivable. **Not a diversifier**: β 1.53/1.62, −7.51% mean in the worst equity decile, and the only sleeve measured that deepened portfolio drawdown at every weight | Taxable, to keep the harvesting option |
| 6 | **Gold, only if funded from cash rather than equity** | 0–5% | No payer; a monetary-regime and inflation-state payoff | Buys 12 bp a month of lower-tail protection over T-bills, at 16.24% volatility and a −91.2% drawdown. A financed wrapper changes the funding rule, not the expected return | Taxable if via a 1940-Act fund; a grantor trust carries the 28% collectibles rate |

**Nothing above is a new return engine except items 1 and 4.** Items 2, 3, 5 and 6 are a
cheaper wrapper, an absence of exposure, a declared speculation and an optional
inflation-state hedge. Counting them as engines would be the error the charter names.

### What was rejected, and on what grounds

Grounds matter more than verdicts, because a rejection on cost reopens when the cost
changes and a rejection on overlap never reopens at all.

| Rejected | Grounds | Reopens when |
| --- | --- | --- |
| Explicit tail hedges, long volatility, buffered products | **Measured cost against measured benefit.** ~12 pp/yr of bleed; no engine on the panel shows resolvable convexity; VIX roll cost is arithmetic | Never on this design. Only a structural change in the variance risk premium's sign |
| Volatility selling and put writing | **Overlap.** It duplicates equity's own left tail | Never |
| Long/short commodities | **Overlap** with the commodity leg of the trend programme already held | If the trend sleeve is removed |
| Long-only commodities as a diversifier | **Measured tail behaviour.** −1.84% mean and 36% hit rate in the worst equity decile, ρ low +0.326 | Never as a crash hedge. It remains a valid *inflation* hedge and is admitted as one |
| BAB, low-volatility and anti-beta tilts as defensives | **Measured concavity**, *t* = +3.49: β −0.264 up, **+0.118 down** | Never. This is a property of the mechanism |
| Merger arbitrage, alternative-risk-premia funds | **Scale and cost stack.** 2.9–4.3%/yr total over ten years, inside the detection floor at any holdable weight | If a stacked wrapper makes the premium additive rather than competitive with equity |
| REITs, dividend funds, TIPS-as-a-second-engine | **Overlap and dominance**, measured in earlier rounds | On a holdings-based decomposition showing exposure the controls cannot span |
| Life settlements, litigation finance, farmland | **Measurement, not mechanism.** Appraised NAVs manufacture a low correlation whether or not the economics are uncorrelated | A vehicle marking to observable transactions |

### The three findings a reader should leave with

1. **A rejection is only as good as the series that produced it.** Credit was rejected here
   on a +0.835 correlation to Treasuries measured on an index carrying twenty years of
   duration. Hedge the duration out and the correlation is **+0.016** over 1,068 months.
   Same asset class, different instrument, opposite conclusion. Every other rejection on
   this page should be read with that possibility in mind.
2. **Shocks come in two kinds and no asset covers both.** Treasuries paid in every growth
   and deflation shock and lost up to 40% in the inflation ones; commodities and gold did
   the reverse; trend was positive in both but has no data before 1985. Breadth means
   holding across *shock types*, not across ticker counts.
3. **In the lower tail, cash is the benchmark almost nothing beats.** A 10% swap from equity
   into T-bills adds +0.92% in the average worst-decile month. Long Treasuries add +0.94%,
   gold +0.92%, BAB +0.96%, commodities +0.74% and bitcoin +0.05%. **Only trend, at +1.08%,
   materially beats it** — and its case is a positive mean, not a convex shape.

### What would change this page

- **A duration-hedged credit series reaching 2026.** The one held ends 2014-12 and has
  never seen March 2020 or 2022. This is the highest-value acquisition identified here.
- **A cat bond spread-to-expected-loss multiple at or above 3.5×.** Publicly observable
  weekly. It is a monitoring boundary, not a forecast.
- **A CLO ETF with a liquidity-crisis record**, which none has, because the oldest launched
  in 2020-10.
- **Bitcoin's correlation to equity falling below +0.2 on a window containing a recession**,
  or a realised equity bear market in which it does not fall harder than equity. 2020 and
  2022 both went the other way.
- **The investor's own inputs** — contribution and withdrawal path, embedded gains, account
  capacity, tolerable drawdown and tracking error, and whether they carry a mortgage above
  the after-tax Treasury yield. Every weight above is a range because those are missing, and
  several would narrow more from one of those answers than from another experiment.
- **A waiver lapse.** CTAP's 10 bp expires 2026-12-04; the iShares rate-hedged waivers expire
  2027-02-28; the cat bond ETF's cap expires 2027-04-30. Three of the six recommendations
  above rest on a fee that is contractually temporary.
