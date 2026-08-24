# Currency and the international sleeve: the position nobody chose

**Question.** The portfolio holds 35% international — VEA, DFIV, IDMO, IEMG, AVES — every one
unhedged. That is a long position in a basket of foreign currencies, funded in dollars, sized
at roughly a third of the equity book. Is it compensated, what does it cost in risk, and should
any of it be hedged?

**Decision it informs.** Whether to hedge the currency exposure of the international sleeve —
all, half, developed only, or none — and in which account. It does **not** change the size of
the international allocation; that is [the equity share](setting-the-equity-share.md) and
[the recommendation](portfolio-recommendation.md).

**Out of scope.** Currency as a return sleeve in its own right (carry, value, momentum as
factors). Hedging foreign *bonds*, where the literature is unanimous and this portfolio holds
none. Tactical or dynamic hedge ratios.

`as of 2026-08-22`. Measured figures regenerate from
[`studies/currency_hedging.py`](../../research/src/portfolio_edge/studies/currency_hedging.py)
and its cache companion
[`_currency_hedging_tables.py`](../../research/src/portfolio_edge/studies/_currency_hedging_tables.py),
run with `uv run python -m portfolio_edge.studies._currency_hedging_tables`; the arithmetic is
pinned in `research/tests/unit/test_studies_currency_hedging.py`. **Everything measured here is
`exploratory`**: no specification was frozen before the numbers were seen and no experiment is
registered, so nothing below may support a promoted claim
([decision 0010](../decisions/0010-bars-carry-a-reopening-condition.md)).

---

## Conclusion

1. **The mean is unresolvable and the variance reduction is large and certain. Make the case
   on the second, or do not make it.** Across six developed-market panels — 150 years of
   annual data and three overlapping monthly windows — the point estimate lands between
   **−0.30 and +0.93 pp/yr** against a **minimum detectable effect of 1.8 to 4.2 pp/yr**. Not
   one window can sign it. Over the same windows a full hedge removes **17% to 21%** of the
   sleeve's volatility, and that estimate is precise. Any argument for or against hedging that
   rests on a forecast of the currency's return is unsupported by this evidence, in either
   direction.

2. **For this investor the currency leg *adds* risk rather than diversifying it, and it is
   worst exactly when it matters.** The correlation between the currency basket and the
   sleeve's own local-currency equity return is **+0.26**, not negative. In the worst decile
   of months for the international sleeve's own equity, the currency leg lost a further
   **−2.11%** per month and was positive in only **14%** of them. The variance-minimising
   hedge ratio is **1.47** — above a full hedge. This is not a hedge that happens to be
   unnecessary; it is a position that compounds the loss it is supposed to soften.

3. **The dollar smile is real, recent, and not a law.** In the **four** stress windows before
   2000 that this repository's currency data reach, the dollar **weakened every time** —
   1973–74, the late-1970s inflation, the 1987 crash and 1998 LTCM. In the **six** since, it
   strengthened in five and weakened once, in **February–April 2025**, when US equity fell
   8.5% and the currency basket *gained* 7.5%. So the pattern the hedging case rests on is a
   post-1997 one with a fresh exception, not a regularity of markets. The month-by-month tail
   statistic is the stronger design and it is clearly adverse; the episode list is the
   honest reminder of how few independent crises there have been.

4. **Hedging currently pays about +1.5 pp/yr in carry, and that is the least durable part of
   the case.** US three-month interbank is 3.77% against a VEA-weighted foreign 2.25%. But the
   Fed has stopped cutting while the ECB, BoJ and RBA have started hiking, the differential has
   compressed by roughly 89 bp in twelve months, and **82% of what remains comes from JPY, EUR
   and CHF alone**. Underwrite the hedge on variance, not on this.

5. **Emerging markets are the opposite trade and the answer is no.** EM currency is more
   strongly pro-cyclical (correlation with its own local equity **+0.54**, variance-minimising
   ratio **2.67**, positive in only **5%** of the worst EM equity months), but hedging it costs
   the interest differential, which for ZAR and MXN is **−3.0 to −3.3 pp/yr against the dollar
   today**. The right response to EM currency risk is to size the sleeve, not to hedge it.

6. **Recommendation: hedge about half the developed sleeve, in tax-advantaged accounts only,
   and nothing in emerging markets.** Confidence **moderate** on "hedge some", **low** on the
   exact ratio. Two implementation facts do most of the work: a hedged fund's forward P&L
   cannot leave through in-kind redemption, so it belongs nowhere near the taxable account;
   and **no product hedges the universe this investor actually owns** — every large hedged
   fund tracks MSCI EAFE, which excludes Canada (10.9% of VEA) and Korea (8.0%), the two
   currencies whose behaviour most argues for hedging. §5 and §6 have the details.

---

## 1. The mechanism, and what it does and does not imply

Write `r_L` for a foreign asset's return in its own currency and `s` for the appreciation of
that currency against the dollar. A US investor holding it unhedged earns `(1+r_L)(1+s) − 1`.
Selling the beginning notional forward at the covered-interest-parity rate
`F = S(1+i_USD)/(1+i_foreign)` leaves

    hedged = unhedged − [(1+i_f)(1+s) − (1+i_d)] / (1+i_f)

and the bracket is the excess return on **foreign cash funded in dollars** — the spot move plus
the interest earned abroad, less the interest given up at home. So:

> **Unhedged minus hedged is the currency excess return, and nothing else.**

"Should I hedge?" is therefore exactly "do I want to be long the developed-currency carry
trade?", and that decomposes into three questions with wildly different resolution: a **mean**
(is it compensated?), a **variance** (what does it cost in risk?), and a **crisis dependence**
(what does it do when it matters?). The derivation is pinned against an independently written
forward payoff in `test_the_forward_hedge_matches_an_independently_derived_payoff`.

**The theory is genuinely two-sided.** A currency has no cash-flow claim, so the prior that it
earns nothing is reasonable and old — Perold and Schulman's "free lunch" argument (*Financial
Analysts Journal* 44(3), 1988; the text is behind a paywall and is reported here only through
[Schmittmann, IMF WP/10/151](https://www.imf.org/external/pubs/ft/wp/2010/wp10151.pdf) and
Campbell et al.). Its formal condition is *two* things: a nil risk premium **and** zero
correlation with the asset. Against it: hedging costs the interest differential, foreign
currency has sometimes diversified dollar-asset drawdowns, and the hedge has operational and
tax costs that the theory ignores entirely.

**Which argument dominates is an empirical question about the second condition, not the
first**, and §2 answers it for this investor.

**A caveat that runs through every hedged number below.** CIP is assumed, not measured. Since
2008 a cross-currency basis has separated the traded forward from the CIP forward — and its
sign **favours** a dollar-based investor, which is the thing most often stated backwards. The
basis sits on the non-dollar leg and is negative because dollars are scarce, so whoever
supplies dollars to the swap market is paid for it, and a US investor hedging foreign assets is
supplying dollars. The BIS puts the turnover-weighted three-month basis at about **−9 bp in
October 2025**, down from about −59 bp in October 2022, widening each autumn as three-month
contracts begin to span the year-end
([*BIS Quarterly Review*, December 2025](https://www.bis.org/publ/qtrpdf/r_qt2512.htm)). Every
hedged return here is understated by roughly that much.

---

## 2. What the repository's own data say

Five panels, because no single free source answers all three sub-questions. The long one is
Jordà–Schularick–Taylor: local-currency equity total returns, bill rates and the `xrusd`
exchange rate for 15 non-US countries, 1871–2020, annual. The monthly ones pair Ken French's
developed-ex-US market return — which he publishes **in dollars only**, so the local leg here
is a residual — with a currency basket built from H.10 month-end noon rates and the OECD
three-month interbank differential. See
[the evidence base](evidence-base.md) for source fitness, including why a month-end sample and
not a monthly average.

### 2.1 The decomposition

| panel | window | n | eff n | unhedged pp/yr | vol % | hedged pp/yr | vol % | currency pp/yr | MDE80 | resolved | vol cut % | min-var h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :-: | ---: | ---: |
| JST, all regimes | 1871–2020 | 150 | 118 | +10.12 | 16.22 | +10.43 | 13.49 | −0.30 | 1.79 | **no** | 16.8 | 1.15 |
| JST, post-war | 1951–2020 | 70 | 53 | +13.88 | 18.67 | +12.95 | 16.80 | +0.93 | 2.92 | **no** | 10.0 | 0.94 |
| JST, floating | 1974–2020 | 47 | 37 | +13.54 | 21.24 | +12.92 | 18.95 | +0.62 | 4.21 | **no** | 10.8 | 0.93 |
| VEA basket, spot+carry | 2002-04…2026-01 | 285 | 246 | +8.73 | 16.15 | +8.19 | 12.77 | +0.54 | 3.90 | **no** | 20.9 | 1.47 |
| VEA basket, spot only | 1999-02…2026-06 | 329 | 298 | +7.81 | 16.21 | +7.64 | 12.93 | +0.17 | 3.48 | **no** | 20.3 | 1.48 |
| EAFE basket, spot+carry | 2002-04…2026-01 | 285 | 239 | +8.73 | 16.15 | +8.29 | 13.37 | +0.44 | 4.09 | **no** | 17.2 | 1.26 |

Read the `resolved` column first. **The mean is unresolved in every window, including the one
with 150 annual observations.** Effective sample size — the number of independent draws the
serial correlation leaves — runs 0.84 to 0.91 of the raw count, so the shortfall is not a
statistical artefact that a longer window would fix soon. To resolve a 1 pp/yr currency premium
at this volatility would take several centuries of floating rates, and there have been fifty
years of them.

The volatility column is a different object. A variance ratio over the same months is estimated
an order of magnitude more precisely than a mean, and **the full hedge removes about a fifth of
the sleeve's volatility** in every modern window.

**Two internal contrasts carry information.** First, the JST windows: the deep history's
currency losses are dominated by wars, occupations and currency reforms, not by a floating
market — the 30 largest annual moves in that panel are almost entirely 1914–1950, and Germany
1914–1950 is excluded outright as redenomination arithmetic. Pre-1971 "currency volatility" is
a devaluation-jump process under a peg, which is why the 1974–2020 row is the only JST row that
describes the world this investor lives in. Second, the VEA and EAFE baskets differ only in
that VEA's includes **Canada and Korea**; adding them raises the volatility cut from 17.2% to
20.9% and the variance-minimising ratio from 1.26 to 1.47. Hold that thought for §5.

### 2.2 Volatility, and what the currency is correlated with

| panel | corr with US equity | corr with the sleeve's own USD equity | corr with the implied local-currency leg |
| --- | ---: | ---: | ---: |
| VEA basket, spot+carry | +0.39 | +0.65 | **+0.26** |
| EAFE basket, spot+carry | +0.31 | +0.57 | **+0.14** |
| EM basket, spot only | +0.50 | +0.72 | **+0.54** |

The third column decides the risk case. A currency leg *negatively* correlated with the local
equity leg would be a genuine diversifier and would belong in the portfolio on risk grounds
alone. It is positive for every sleeve this investor owns.

**This reproduces independently.** MSCI publishes both legs of the same index. As of
2026-07-31, MSCI EAFE 100% Hedged to USD had a ten-year annualised standard deviation of
**11.82%** against unhedged EAFE's **14.99%** — a 21% reduction, essentially identical to the
20.9% measured above on a differently constructed basket — and the hedged index sat within
0.03 pp of the pure local-currency index (11.85%), which is what a working hedge looks like
([hedged factsheet](https://www.msci.com/documents/10199/a8a3ef21-f61a-4a4e-82aa-81c24481b783),
read 2026-08-22). Campbell, Serfaty-de Medeiros and Viceira (*Journal of Finance* 65(1), 2010,
Table VII) put a US investor's global equity volatility at 15.05% unhedged against 13.86%
hedged over 1975–2005; AQR's *Risk Without Reward* (2015) puts 16.7% against 14.5% over
1975–2015.

### 2.3 Crisis-conditional behaviour, which is the decision-relevant measurement

Average correlation is incomplete evidence about crisis dependence
([charter](../charter.md)), so both the tail statistic and the named episodes are reported.

| panel | conditioning base | tail months | base mean %/mo | currency mean %/mo | hit rate | worst %/mo | corr full | corr in tail |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| VEA basket | US equity | 28 | −8.10 | **−1.35** | 29% | −5.89 | +0.39 | +0.48 |
| VEA basket | the sleeve's own equity | 28 | −8.54 | **−2.11** | **14%** | −5.89 | +0.65 | +0.41 |
| EM basket | US equity | 37 | −8.14 | −1.79 | 19% | −5.98 | +0.50 | +0.40 |
| EM basket | the sleeve's own equity | 37 | −10.70 | **−2.15** | **5%** | −5.98 | +0.72 | +0.40 |

**In 86% of the worst months for the international sleeve's own equity, the currency moved
against the holder too.** That is the answer to the question the charter asks: the currency leg
is not neutral in the tail, it is additive to the loss. Note that the in-tail correlation is
not comparable with the full-sample figure — conditioning on the base's magnitude truncates its
variance — and should be read against the same design's other rows only.

The named episodes are the honest complication.

| episode | window | US equity | developed currency | EM currency | DTWEXM | DTWEXAFEGS |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1973–74 | 1973-01…1974-09 | – | – | – | +4.05\* | – |
| 1987 crash | 1987-09…1987-11 | – | – | – | **+6.58** | – |
| 1998 LTCM | 1998-07…1998-09 | – | – | −0.59 | **+1.97** | – |
| 2000–02 dot-com | 2000-04…2002-09 | −44.89 | −4.36 | −11.90 | −5.31 | – |
| 2008–09 GFC | 2007-11…2009-02 | −50.31 | **−13.90** | **−17.33** | −14.59 | −15.80 |
| 2020 Q1 covid | 2020-01…2020-03 | −20.17 | −3.43 | −4.90 | – | −3.88 |
| 2022 rate shock | 2022-01…2022-09 | −24.83 | **−14.70** | −11.63 | – | −12.62 |
| 2025 Feb–Apr | 2025-02…2025-04 | −8.47 | **+7.48** | +1.83 | – | +7.65 |
| 2026 Feb–Mar | 2026-02…2026-03 | −5.75 | −3.43 | −2.10 | – | −3.18 |

`*` partial coverage. `–` means no currency series in this repository reaches the window; none
of them sees 1929, 1937 or 1973 in full, and that limit is itself the most important thing the
top rows say. The 2025 and 2026 windows are the peak-to-trough months of French's US market
return since 2024-06, read off the panel rather than chosen.

**Split the rows at 2000 and the pattern is unmistakable — and so is its age.** In all four
pre-2000 windows the panel reaches (1973–74, the late-1970s, 1987, 1998) the foreign-currency
leg was **positive**: the dollar weakened. In five of the six windows since (2000–02, 2008–09,
2020, 2022, 2026) it was **negative**: the dollar strengthened. The GFC and 2022 rows are large
— a 14 pp currency loss stacked on a 50 pp and a 25 pp equity loss — and they are the two
episodes that matter most to a long-horizon holder. But the dollar's crisis behaviour as this
data records it is a **quarter-century-old regularity with one fresh counter-example**, not a
law of markets, and a decision that leans hard on it is leaning on roughly five independent
observations.

**2025 is a published break, and its cause is disputed.** The BIS regresses daily S&P 500
returns on the DXY and reports a fitted slope of **−1.449 (R² 0.26) for 2020–24 flipping to
+0.792 (R² 0.09) in 2025** (*BIS Quarterly Review*, December 2025, Graph 4.A). Its own reading
of April 2025 is *not* a loss of confidence in dollar assets but **ex-post hedging flow** by
non-US investors whose hedge ratios had fallen to historic lows — Japanese life insurers from
about 60% in 2021 to 40% in 2024
([BIS Bulletin 105](https://www.bis.org/publ/bisbull105.pdf), June 2025). If that reading is
right, 2025 is a positioning unwind inside an unchanged relationship. One year is not a sample
either way, and the March 2026 review has the dollar rallying again on a genuine risk-off shock.

### 2.4 The hedge-ratio frontier

| hedge ratio | mean pp/yr | vol % | worst month % | max drawdown % |
| ---: | ---: | ---: | ---: | ---: |
| 0.00 | +8.73 | 16.15 | −21.03 | −55.94 |
| 0.25 | +8.60 | 15.06 | −19.56 | −54.06 |
| 0.50 | +8.46 | 14.12 | −18.08 | −52.15 |
| 0.75 | +8.32 | 13.35 | −16.61 | −50.22 |
| 1.00 | +8.19 | 12.77 | −15.14 | −48.27 |

VEA basket, spot and carry, 2002-04 to 2026-01. **The curve is close to linear: the first half
of the hedge buys about 60% of the volatility reduction and about half of the drawdown and
worst-month reduction.** Campbell et al. found the same shape more sharply — a half hedge captured 1.14 of
the 1.19 pp their full hedge bought — and it is why the choice between 50% and 100% matters
much less than the choice between 0% and 50%. MSCI's published maximum drawdowns say the same
thing in realised terms: **−54.60% hedged against −60.41% unhedged**, both troughing on
2009-03-09.

### 2.5 The carry today

| currency | basket weight | spot mean pp/yr | spot vol % | 3m interbank % | USD minus foreign pp |
| --- | ---: | ---: | ---: | ---: | ---: |
| EUR | 0.279 | +0.43 | 9.15 | 2.34 (2026-06) | **+1.43** |
| JPY | 0.224 | −0.78 | 9.49 | 1.27 (2026-05) | **+2.50** |
| GBP | 0.125 | −0.43 | 8.48 | 3.71 (2026-01) | +0.06 |
| CAD | 0.117 | +0.56 | 8.24 | 2.27 (2026-06) | +1.50 |
| KRW | 0.086 | −0.47 | 10.37 | 2.91 (2026-06) | +0.86 |
| CHF | 0.076 | +2.51 | 9.69 | −0.04 (2026-06) | **+3.82** |
| AUD | 0.062 | +1.03 | 11.65 | 4.46 (2026-06) | **−0.69** |
| SEK | 0.030 | −0.21 | 10.85 | 1.95 (2026-06) | +1.82 |
| USD | – | – | – | 3.77 (2026-06) | – |

Weighted, **+1.52 pp/yr** before the basis pickup and before any fee. The same calculation on
policy rates read on 2026-08-22 (Fed 3.50–3.75%, ECB deposit 2.25%, BoJ 1.00%, BoE 3.75%, SNB
0.00%, RBA 4.35%, BoC 2.25%, Riksbank 1.75%) gives **+1.40 pp/yr**, and shows the same twelve-
month compression of roughly **−89 bp**: the Fed cut three times in late 2025 and stopped,
while the ECB, BoJ and RBA have all raised since. **Hedging GBP and AUD now costs money.**

This is the least durable leg of the case. It is a positive number today, it is shrinking, and
82% of it comes from three currencies.

**The decade table is the reason not to lean on any recent window.**

| decade | VEA basket pp/yr | DTWEXM pp/yr | DTWEXAFEGS pp/yr |
| --- | ---: | ---: | ---: |
| 1970s | – | +1.92 | – |
| 1980s | – | +0.72 | – |
| 1990s | – | −0.19 | – |
| 2000s | +2.68 | +2.86 | +3.41 |
| 2010s | −1.30 | −1.82 | −1.85 |
| 2020s | −1.34 | – | −0.26 |

Cumulatively the developed basket lost **−25.83%** over 2010–2024 (the Fed's own AFE index says
−27.09%), then **gained +7.63% in 2025** and lost **−2.77% in 2026 H1**. A decade of drag
followed by one large year is what an unforecastable near-random-walk looks like; it is not
evidence of a trend in either direction.

---

## 3. Emerging markets are a different question with a different answer

| panel | window | n | unhedged pp/yr | vol % | spot-hedged pp/yr | vol % | currency pp/yr | MDE80 | resolved | vol cut % | min-var h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :-: | ---: | ---: |
| EM, spot only | 1995-02…2026-06 | 377 | +9.61 | 20.39 | +10.73 | 16.91 | −1.12 | 2.55 | **no** | 17.0 | **2.67** |
| EM, spot+carry (4 ccy) | 1997-06…2026-05 | 346 | +8.81 | 20.90 | +7.60 | 17.60 | +1.21 | 3.15 | **no** | 15.7 | 1.74 |

Three findings. The first argues for hedging EM harder than developed; the second and third
say the trade is not available at a price worth paying.

**The risk case for hedging EM is stronger than for developed.** Correlation with its own local
equity is **+0.54** against the developed sleeve's +0.26; the variance-minimising ratio is
**2.67**; and in the worst decile of EM equity months the currency was positive in **5%** of
them. Conover, Garcia-Feijoo, Silverstein and Szakmary (*Review of Financial Economics* 43,
2025, open access) find the local-equity/currency correlation significantly **positive in 12 of
13** emerging markets and the ex-post optimal hedge ratio equal to 1 in 11 of 13, against
significantly *negative* correlations in six developed markets. The mechanism is not mysterious:
EM currencies are commodity-linked, and dollar-denominated corporate debt gets harder to repay
exactly as the local currency falls.

**But the spot depreciation is roughly the interest differential, so hedging removes both.**
The spot-only row shows a −1.12 pp/yr currency drag; the carry-inclusive row on the four
currencies with a comparable interbank series shows **+1.21 pp/yr** — the sign reverses once
the interest earned abroad is counted. That is the carry trade, and it means the naïve reading
of the spot table ("EM currency loses 1.1 pp/yr, hedge it") is wrong.

| EM currency | spot mean pp/yr | spot vol % | 3m interbank % | USD minus foreign pp |
| --- | ---: | ---: | ---: | ---: |
| TWD | −0.45 | 5.61 | – | – |
| KRW | −1.29 | 12.75 | 2.91 (2026-06) | +0.86 |
| CNY | +0.75 | 3.05 | 1.51 (2026-05) | +2.26 |
| INR | −3.30 | 6.43 | – | – |
| BRL | −4.19 | 17.07 | – | – |
| ZAR | −3.76 | 14.78 | 7.11 (2026-06) | **−3.34** |
| MXN | −2.88 | 10.91 | 6.76 (2026-06) | **−2.99** |

**And the cost of hedging is prohibitive and worst when it is needed.** Selling a
high-yielding currency forward locks in the differential as a loss: ZAR and MXN cost 3.0–3.3
pp/yr *today*. The two rows with a blank rate column are the expensive ones — Brazil and India
have no comparable interbank series on this feed, and both currencies depreciated 3–4 pp/yr
against the dollar over three decades, which is what a large positive differential looks like
from the other side. Viceira and Shen (NBER WP 35498, July
2026) make the trade-off explicit: risk minimisation wants EM over-hedged at ratios of 2.7–2.9,
but their factor-implied expected currency excess returns are **+6.1% for BRL and +4.7% for
MXN**, which "offset, and in some cases reverse, portfolio-risk minimizing demands." On top of
that, much EM hedging runs through non-deliverable forwards, whose pricing separates from the
onshore market precisely in stress (McCauley, Shu and Ma, *BIS Quarterly Review*, March 2014).

**Verdict for EM: do not hedge.** The measurement says EM currency is a crisis amplifier; the
cost structure says the hedge is not worth buying; and the tools are worse. The correct control
for EM currency risk is the **size of the EM sleeve**, which is a different decision on a
different page. It also interacts with the foreign-tax-credit finding in
[structural and tax edges](structural-and-tax-edges.md) — an EM sleeve in a taxable account is
already carrying an account-placement argument, and adding a hedge does not help it.

---

## 4. What the literature says, and where it genuinely disagrees

**Converged, and worth stating plainly.**

- Developed-currency excess returns are close to zero and statistically indistinguishable from
  zero. Nobody disputes this. The whole argument is about correlation.
- The dollar was negatively correlated with global equity through 2023. Campbell et al. (2010)
  over 1975–2005 and Viceira and Shen (NBER WP 35498, 2026) over 1975–2023 agree, and the
  latter states the implication for this investor without hedging its words: *"the U.S. dollar
  is still negatively correlated with global equity markets… This means that US investors want
  to hedge and even overhedge their currency exposures."* Their implied optimal ratios using
  observed forwards are CAD 2.03, AUD 1.44, EUR 1.03, GBP 1.00, JPY 0.50.
- The correlation is unstable and regime-dependent — Schmittmann (2010) measures it swinging
  ±40 points decade to decade. Anyone quoting one number is quoting one sample.
- Foreign **bonds** should be hedged, unanimously. Not relevant here; noted so it is not
  mistaken for support of the equity case.

**Genuinely open.**

- **Vanguard and AQR give opposite advice to the same investor.** AQR (2015) reports hedged
  volatility of 14.5% against unhedged 16.7% over 1975–2015, Sharpe 0.37 against 0.33, a worst
  one-year drawdown of −60.4% against −78.7%, and a volatility-minimising currency allocation
  of about −10% — hedge fully, then a little more. Vanguard (May 2026) recommends leaving
  equities largely unhedged, at portfolio hedge ratios of 10–20% for an 80%-equity investor.
  They are measuring different things: AQR compares risk-adjusted outcomes, Vanguard compares
  a marginal volatility saving against a fixed cost of 0.25–0.50% a year. **And Vanguard
  carves out this exact investor:** its own Figure 4 reports that from a **US** perspective the
  ten-year rolling currency/equity correlation was positive — risk-adding — in **71% of
  1972–2025**, the highest of the seven domiciles it shows, and its text concedes that "the US
  dollar's 'safe haven' correlation channel… may justify higher overall hedging for USD-based
  investors."
- **Whether hedging helps at long horizons.** Froot (NBER WP 4355, 1993) is the standard
  citation for "no" — the minimum-variance ratio falls to about 35% at five to ten years. Two
  things are usually dropped: it uses **one currency pair**, GBP/USD, from a *British*
  investor's perspective; and its own text concedes that "the data provide little power against
  the hypothesis that β = 1 at very long investment horizons." Schmittmann (2010) reaches the
  opposite conclusion on four base currencies and says so explicitly. Neither settles it, and
  the burden of proof sits with the side whose data cannot reject a full hedge.
- **Whether 2025 broke the dollar's safe-haven property.** §2.3. Published, quantified, and
  interpreted by its own publisher as a flow event rather than a regime change.

**On the 50% rule, a correction worth carrying.** The usual attribution of "minimum regret =
50%" to Gardner and Wuilloud (*Journal of Portfolio Management* 21(3), 1995) could not be
verified — the citation is real, the paper is paywalled, and nothing found actually says they
recommend 50%. The properly sourced version is Michenaud and Solnik (*Journal of International
Money and Finance* 27(5), 2008), who derive it formally: **the regret-minimising hedge ratio is
always between 50% and 100%, and reaches 50% only in the limit of infinite regret aversion.**
The 50% choice is "always wrong, but the maximum regret is cut in half" — and, decisively for
this page, **it requires no forecast of the currency mean**, which is the one quantity none of
the evidence above can supply. Black's universal hedging ratio (77% on his baseline inputs) is
the other principled interior answer, and its own author's worked examples span 30% to 73%
across two four-year windows, which is the standard critique.

---

## 5. Implementation, honestly

### 5.1 The products, and the one that does not exist

| ticker | fund | expense | structure | unhedged comparator | difference | net assets |
| --- | --- | ---: | --- | --- | ---: | ---: |
| **DBEF** | Xtrackers MSCI EAFE Hedged Equity | **0.35%** | direct holdings, no waiver | EFA 0.32% / VEA 0.03% | +3 bp / **+32 bp** | $8.81bn (2026-05-31) |
| **HEFA** | iShares Currency Hedged MSCI EAFE | **0.35%** net (0.70% gross) | fund-of-funds holding **EFA** | EFA 0.32% / VEA 0.03% | +3 bp / **+32 bp** | $7.51bn (2026-08-21) |
| **HFXI** | NYLI FTSE International Equity Currency Neutral | **0.20%** | direct, **50% hedged** | VEA 0.03% | +17 bp | $0.96bn (2025-04-30) |
| HAWX | iShares Currency Hedged MSCI ACWI ex US | 0.35% net | fund-of-funds holding ACWX | ACWX 0.32% | +3 bp | $0.35bn |
| HEDJ | WisdomTree Europe Hedged Equity | 0.58% | direct | VGK 0.06% | +52 bp | $1.70bn |
| IHDG | WisdomTree Intl Hedged Quality Div Growth | 0.58% | direct | IQDG 0.42% | +16 bp | $2.14bn |

Read 2026-08-22 from issuer pages and SEC filings; HEFA's fee table and net assets were
confirmed independently against ishares.com, and VEA's 0.03% against Vanguard's own profile
endpoint (stated as of 2026-04-28).

**Prefer DBEF to HEFA on structure, not on price.** They cost the same and hedge the same
index, but HEFA's fee is a waiver with an expiry and its fund-of-funds form carries a tax
wrinkle its own prospectus discloses: *"the Fund's realized losses on sales of shares of the
Underlying Fund may be indefinitely or permanently deferred as 'wash sales'"*, and the
underlying fund's own loss carryforwards cannot offset the hedged fund's gains. DBEF holds the
securities directly, charges a flat unitary fee with no waiver to expire, and has no acquired-
fund layer at all.

**Fees are not the obstacle.** Against the VEA counterfactual a hedge costs about 32 bp, which
is real but small against a 3 pp/yr volatility reduction. HEFA's 0.35% is a contractual waiver
running to **2030-11-29** and structured as "EFA's fee plus 0.03%"; DBEF has no waiver at all,
which makes it the more robust choice on this axis. Realised tracking against the hedged index
is tight — HEFA within 3–28 bp over 1, 3, 5 and 10 years — so the hedge itself is not where
value leaks.

**The obstacle is that no product hedges what this investor owns.** Every broad hedged fund
tracks **MSCI EAFE**, which excludes **Canada (10.9% of VEA)** and **Korea (8.0%)** — 19% of
the sleeve, as of Vanguard's 2026-07-31 allocation. HFXI's index is FTSE Developed **ex North
America**, which also excludes Canada. And Canada and Korea are precisely the currencies whose
behaviour most argues for hedging: §2.1 measured the variance-minimising ratio rising from 1.26
to 1.47 and the local-equity correlation from +0.14 to +0.26 when they are added, and Conover
et al. measure CAD's equity correlation at **+0.18** where France's is −0.18. **The available
hedge removes the currency risk that needs removing least.**

This is not fatal — 81% of the exposure is hedgeable — but it means switching VEA for DBEF is
not a currency-only change. It is also a change of equity index, and the charter is explicit
that two decisions bundled into one trade should be separated. A partial position beside VEA
keeps them separate; a wholesale swap does not.

**Also relevant to the 50% question:** Xtrackers has an *MSCI EAFE 50% Hedged Equity ETF* in
registration on Form 485APOS, filed mid-2026. **Its ticker and its entire fee table are blank
in the filing** and it has not launched. Worth checking at the next review; do not plan around
it.

### 5.2 The mechanics leave a residual, and the issuers say so

The MSCI hedged indices sell each foreign currency forward at the one-month forward rate and
**reset the hedge monthly, without intra-month adjustment for equity price moves**. So the fund
is over-hedged when equities fall inside a month and under-hedged when they rise. This is the
same `r_L × s` cross term the arithmetic in §1 keeps rather than dropping, and it is why a
"100% hedged" fund is not fully hedged.

### 5.3 Tax, which is the part that actually decides the account

**The mechanism is §852(b)(6).** An ETF flushes appreciated *stock* out through in-kind
redemption with no gain recognised. **A cash-settled currency forward cannot be delivered in
kind.** The equity leg of a hedged ETF is therefore exactly as tax-efficient as its unhedged
twin, while the currency leg is forced through the income statement and out to shareholders in
cash. HEFA's FY2025 statement of operations shows the two legs side by side: a realised loss on
forward FX of **$(581.9)m** against in-kind redemptions of **+$705.4m**.

The consequence in a dollar-strength year is not subtle.

| calendar 2022 | distribution/share | % of year-end price | QDI share | long-term gains |
| --- | ---: | ---: | ---: | ---: |
| **HEFA** | $6.788 | **24.4%** | **22.67%** | $3.539 |
| DBEF | $5.110 | 15.4% | – | – |
| EFA | $1.766 | 2.6% | 100.00% | $0 |
| IEFA | $1.667 | 2.6% | 99.97% | $0 |
| VEA | $1.223 | 2.9% | – | – |

EFA and IEFA have distributed **zero** capital gains in every year 2016–2026. HEFA has done so
in 2014, 2015, 2016, 2018, 2019 and 2022. The realised after-tax drag, from iShares' own
standardised after-tax-pre-liquidation figures, is **204 bp over 5 years and 144 bp over 10 for
HEFA against 78 and 69 for EFA** — roughly 2.5 to 3 times.

**On character:** a foreign currency forward is a §1256 contract, so it is marked to market
annually whatever else happens. Its character is **ordinary** under §988(a)(1)(A) unless the
fund elects out under §988(a)(1)(B). HEFA's 2022 distribution split of **60.08 / 39.92** is the
§1256(a)(3) signature and implies the election was made, but no fund document states it; DBEF's
treatment is unverified. Even under 60/40 the short-term 40% is distributed as a non-qualified
ordinary dividend.

**On the foreign tax credit, the worry is half right.** §853(a)(1) requires more than 50% of
assets in stock of *foreign corporations*, and a fund-of-funds holding a US-listed ETF fails
that on its face — but **§852(g)(1)(B)**, added by the RIC Modernization Act of 2010, waives
the test for a qualified fund of funds. HEFA's own 1099s confirm the credit reaches
shareholders at the same rate as EFA's (5.28% of ordinary dividends in 2025 against EFA's
5.14%, on QDI shares of 76.00% and 76.15%). The election is annual rather than guaranteed —
**neither** HEFA nor EFA passed any foreign tax through in 2021 or 2022 — but that failure hit
both funds identically and is not a hedging problem. **The real problem is second-order and
specific to hedging:** §988(a)(3)(A) sources
ordinary §988 income by the taxpayer's residence, so hedge gains are **US-source income that
dilutes the foreign-source fraction** in the §904 limitation. HEFA's foreign-source income was
**22.61% in 2022 against EFA's 100%**. The credit survives; the ability to use it shrinks in
exactly the years the hedge pays.

**No Cayman subsidiary is involved and none is needed** — §851(b)(2)(A) already treats currency
forward gains as qualifying income when they are derived with respect to the business of
investing in the underlying securities. This is *not* analogous to the commodity-fund structure
[structural and tax edges](structural-and-tax-edges.md) covers. The analogy that does hold is
the ordinary-income one: like a §1256 commodity structure, a hedged equity fund converts return
into currently recognised income the holder cannot defer.

**Conclusion: a currency-hedged fund is disqualified from the taxable account.** Not marginal —
disqualified. The one exception in the data is a fund carrying a large disclosed loss
carryforward (HEDJ holds about $2.1bn against $1.7bn of net assets, a shield worth roughly 124%
of NAV), but that is depletable, fund-specific, and HEDJ is a Europe-only 0.58% product that
does not fit this sleeve.

---

## 6. The decision

**Hedge about half the developed portion of the international sleeve, hold the hedged position
only in the Roth or traditional accounts, and hedge nothing in emerging markets.**

Concretely: leave VEA, DFIV, IDMO, IEMG and AVES exactly as they are in the taxable account,
and in the sheltered accounts hold DBEF beside the developed exposure, sized so that roughly
half the developed sleeve's currency notional is hedged. The developed sleeve is **25% of
notional equity exposure** (DFIV 10, VEA 10, IDMO 5) against **10% emerging** (IEMG 5, AVES 5),
so a half hedge is a position of roughly **12% of the portfolio** — which fits comfortably in
two accounts holding about two-thirds of it between them, without displacing the higher
placement priorities in [structural and tax edges](structural-and-tax-edges.md).

**Confidence: moderate that some hedge is right; low on the ratio.**

Why moderate rather than high: the variance reduction is large, precisely estimated, reproduced
on six internal panels and on MSCI's own published index pair, and corroborated by three
independent literature strands including one 2026 paper by an author of the canonical one. The
crisis evidence points the same way and is the measurement the charter asks for. The carry
currently pays.

Against that, **the portfolio-level effect is modest, and this page has not measured it.** A
half hedge takes the sleeve from 16.15% to 14.12% annualised volatility, about 2.0 pp. At a 35%
weight that is an *upper bound* of roughly 0.7 pp on portfolio volatility, and the true figure
is lower because the sleeve is imperfectly correlated with the rest of the book — Vanguard's
independent estimate for a US investor is **0.3 to 0.7 pp**. Whether that is worth a certain
32 bp and a permanent account constraint is a judgement, not a measurement, and it is the
weakest link in the chain. The mean is unresolvable. And the product hedges the wrong universe.

Why 50% and not 100%: because the frontier is nearly linear and the first half buys about 60%
of the benefit; because the regret-minimising ratio requires no forecast of the quantity this
evidence cannot resolve; and because 2025 demonstrated in one year that the regret is real —
unhedged EAFE beat hedged EAFE by **8.1 percentage points** (31.22% against 23.10%). A 50%
hedge is not a compromise between two estimates. It is the correct answer to a question whose
central input is genuinely unknown.

Why not 0%: because the strongest argument for leaving it alone — that foreign currency
diversifies dollar-asset risk — is the one thing measured here that is clearly **false for this
portfolio**. The correlation with the sleeve's own local equity is +0.26, the
variance-minimising ratio is above one, and in 86% of the sleeve's worst months the currency
made it worse.

**What would change this.**

- **The carry turning negative.** It is +1.4 to +1.5 pp/yr today and has compressed 89 bp in
  twelve months, with the BoJ, ECB and RBA all hiking. If US-minus-foreign goes to zero, the
  variance argument has to carry a certain fee on its own, and the case for 50% weakens toward
  25%. Recheck at the next annual review.
- **The currency/local-equity correlation turning durably negative** — AQR puts the threshold
  at about −0.5, Vanguard's grid at about −0.3. It is +0.26 now. A sustained move below −0.3
  would flip the recommendation to 0%.
- **A second 2025-style episode.** One dollar decline inside an equity drawdown is a
  data point the BIS itself reads as a positioning unwind. A second one, especially with a
  different proximate cause, would be evidence of a regime change and should reopen this page.
- **A hedged product on a Canada-and-Korea-inclusive index** at a comparable fee, which would
  remove the largest implementation objection. Watch the Xtrackers 50%-hedged EAFE filing and
  any FTSE Developed ex-US hedged launch.
- **A frozen evaluation.** Everything here is exploratory. The whole-portfolio effect at the
  actual 35% weight has never been scored against the charter's outcome set — after-tax
  relative terminal wealth, drawdown, benchmark-relative risk, and holdability — and that is
  the natural next test.

---

## What could not be established

- **The sign of the currency premium.** Unresolved on all eight panels, developed and emerging,
  with detection floors of 1.8 to 4.2 pp/yr against point estimates inside ±1.3. This is not a small effect; it is an
  unmeasured one, and no free data this repository can reach will change that soon.
- **Whether 2025 was a break.** Published, quantified, and disputed by its own publisher.
- **A local-currency developed-ex-US equity series.** None is free. The local leg here is a
  residual after dividing out a constructed basket and inherits every error in the weights;
  it is not a measurement of a local-currency index and is not quoted as one.
- **Point-in-time currency weights.** The baskets apply constant 2026 fund weights to windows
  starting in 1995 and 1999. Vanguard's own endpoint shows Korea going 4.6% to 8.0% in twelve
  months, so the constancy assumption is known to be wrong; the Fed's trade-weighted indices are
  reported beside every basket result as a check that the answer survives a different scheme.
- **EM carry for BRL, INR and TWD.** No comparable interbank series exists on this feed, so the
  carry-inclusive EM panel covers four currencies of seven and is not the fund's basket.
- **The realised cross-currency basis inside a fund's own forward roll**, and whether DBEF has
  made the §988 election out.
- **The after-tax comparison for this investor.** It depends on his marginal rates, contribution
  path and account capacity, and the charter requires that dependency be shown rather than
  silently resolved. The direction is unambiguous and is enough for the account recommendation;
  the magnitude is not established.
