# Valuation and the allocation: what a CAPE of 41 does and does not license

**Question.** US CAPE is at the 99th percentile of 145 years. Should that change the equity
share, the US/international split, or the rebalancing rule?

**Decision it informs.** Whether any allocation number moves because of an August 2026
valuation reading, and if so which one and through which mechanism. It does **not** set the
equity share — [setting the equity share](setting-the-equity-share.md) owns that — and it
forecasts no market.

**Out of scope.** Trend and moving-average timing, which is a different signal and a
different page. Sector or single-stock valuation. Any claim that a level "must" mean revert.

`as of 2026-08-22`; the market readings in §1.1, §1.2 and §1.4 are `as of 2026-09-01`.
Measured figures regenerate from
[`studies/valuation_conditioning.py`](../../research/src/portfolio_edge/studies/valuation_conditioning.py)
and its cache companion
[`_valuation_conditioning_tables.py`](../../research/src/portfolio_edge/studies/_valuation_conditioning_tables.py),
run with `uv run python -m portfolio_edge.studies.valuation_conditioning`; the arithmetic is
pinned in `research/tests/unit/test_studies_valuation_conditioning.py`. **Everything measured
here is `exploratory`**: no specification was frozen before the numbers were seen and no
experiment is registered, so nothing below may support a promoted claim.

---

## Conclusion

1. **The concern is correct about the level and wrong about what follows from it.** US CAPE
   of **41.18** (`as of 2026-08-01`, Shiller) has been equalled or exceeded in **19 of 1,748
   months since 1881**, and **18 of those 19 are March 1999 to September 2000**. The 1929
   peak was 32.56. But a level is not a forecast, and the three claims bundled inside "we
   must consider valuations" — a return forecast, a risk statement, and a relative call —
   have very different evidence. Only two of them survive.
2. **The forecast claim is much weaker than its usual presentation, and the weakness is in
   the standard errors, not the slope.** At the ten-year horizon the CAPE-yield regression
   reports a Newey-West `t` of **4.84** and a Hodrick 1B `t` of **2.47** on the same
   coefficient. The sample holds **13.6 independent** ten-year observations, not 1,628.
   Separately, the predictor's monthly autoregressive root is **0.9966** and its innovation
   correlates **−0.9975** with the return innovation, so the Stambaugh bias is **73.4% of
   the fitted slope**: annualised, **0.0369 uncorrected against 0.0098 corrected**. Neither
   correction is exotic and both are omitted from almost every published version of this
   chart.
3. **Out of sample since 1990 the CAPE model has lost to a rolling mean at every horizon,
   and lost badly.** Out-of-sample `R**2` of **−0.21 (1yr), −0.42 (5yr), −0.44 (10yr),
   −1.88 (15yr)**, with the model too *pessimistic* by **+7.8, +6.3, +4.9 and +4.3 pp/yr**
   respectively. An investor who acted on it in 1990 would have been wrong for a third of a
   century. That is not proof it is wrong now, but it is the record.
4. **Conditioning the equity share on the CAPE *level* loses even before costs.** Over
   1921-01…2026-07 a rule that tilts 80/20 on the expanding CAPE percentile returned
   **−9.0 bp/yr** against a constant 80/20 gross, and **−86 bp/yr** net of 10 bp execution
   and a 15% effective capital-gains rate. "Halve above the CAPE median" lost **−55 bp
   gross and −202 bp net**. Both used a **revised, non-point-in-time** history, which
   flatters them.
5. **One valuation rule does have a real gross edge, and tax eats it.** Tilting on the
   **excess CAPE yield** rather than the level earned **+49.5 bp/yr** gross against a
   constant 80/20, of which **+47.7 bp is timing** rather than de-risking, and it was ahead
   in **98.5%** of rolling 30-year windows. Net of execution and a 15% effective
   capital-gains rate it turns **−15.6 bp**, ahead in **39.4%** of windows. The break-even
   effective capital-gains rate is **11.3%**. **The signal is real and the account decides
   whether it is worth having.**
6. **The risk claim survives, and it is the strongest thing valuation says.** Buyers at
   CAPE above 30 spent a median **59.7% of the following fifteen years below their own real
   entry level**, against **5.0%** for buyers below 20, with a median worst real drawdown of
   **−51.8%** against −36.7%. That is a statement about **holdability**, not about return —
   the same cohort's fifteen-year real return was still positive at a median +2.15%/yr and
   its twenty-year median was +4.31%/yr. **It is drawn from two episodes** (1929 and
   1997-2002, 0.32 independent observations) and cannot be read as a probability.
7. **The relative call is the best-posed of the three, and the strongest thing in it is not a
   CAPE reading.** It is that **81% of thirty-five years of US outperformance was re-rating
   rather than earnings growth** (+3.8 pp of 4.7 pp/yr, AQR, `as of 2024-12`). The US CAPE
   premium over developed ex-US is **1.70x** (Siblis, `as of 2026-06-30`), it is about fifteen
   years old, and in the late 1980s it was *inverted*. Cross-sectionally on 1870-2020 and 18
   countries a one-log-unit valuation gap bought **+6.05 pp/yr** of relative ten-year real
   return with `t = 3.65` on 14 independent observations — **and the relation is undetectable
   after 1990** (slope −0.0006, `t = −0.03`) on a design that could have found the historical
   0.07 at 80% power. AQR's own version of the same test reports a **+0.5 correlation on "4+
   independent observations."**
8. **The 65/35 split is not a US overweight.** Siblis's global index is **~64% US**
   (`as of 2026-06-30`), so 65/35 is a **+1.0 pp** active bet against global market-cap
   weight. The question is therefore not "should we cut an overweight" but "should we
   deliberately underweight the market portfolio", which needs a stronger claim than
   "expensive".
9. **Every US-versus-international measurement here has a confound the size of the effect.**
   Buybacks close about **half** the US-versus-Europe payout gap and explain about **a third**
   of the US's own CAPE elevation — and correcting for them does not forecast better. Sector
   mix explains about **half** of the US's relative richness. **Currency** contributed ≈−1.7
   pp/yr to unhedged non-US returns over 2010-2024, ≈**+7 pp in 2025 alone**, and ≈−1.6 pp in
   2026 H1. And Japan, Korea and Taiwan now carry CAPEs **at or above** the US's.
10. **What to do.** Do not run a valuation-conditional weighting rule in a taxable account.
    Do not cut the equity share on the return forecast. **Do** widen the drawdown and drought
    assumptions the equity share is sized against, and **do** direct new contributions rather
    than realised gains toward the international side. A 10 pp US-to-international shift is
    worth about **14 bp/yr** against **80-144 bp** of tracking error and needs **55-178
    years** to demonstrate. It is not worth a tax bill; it is nearly free with new money.
    **Hedging currency is worth ≈0.8 pp/yr of carry to a USD investor and has not been tested
    here — it is larger than the valuation edge and should be studied before the split moves.**

---

## 1. What valuations actually are

### 1.1 The US level, from this repository's own cache

Shiller's `ie_data` workbook, `sha256:71c3636d…`, `Last-Modified: Tue, 04 Aug 2026
15:29:32 GMT`, refetched 2026-08-23 and byte-identical. Its final row is 2026-08 and its own
footnote says *"Aug price is Aug 1st close … Aug GS10 is Jul 31st value"*, so **this is an
August 1st reading.**

| Measure | Value | Percentile, 1881-2026 | Note |
| --- | ---: | ---: | --- |
| **CAPE** | **41.18** | **0.989** | 19 of 1,748 months at or above; 18 are 1999-03…2000-09 |
| Total-return CAPE | 43.98 | 0.987 | max 48.11 (1999-12) |
| CAPE earnings yield | 2.43%/yr | 0.010 | not an expected return |
| **Shiller excess CAPE yield** | **+0.97 pp** | **0.187** | against a *trailing-inflation-adjusted* nominal 10y |
| **TIPS excess CAPE yield** | **−0.01 pp** | **0.000 since 2003** | against DFII10 2.44% on 2026-08-31; +0.03 pp on the August daily average (DFII10 2.40%) |

**The last two rows are the finding.** They are the same construction with a different real
rate, and they disagree by a percentage point, because the real yield implied by Shiller's
own column is **1.45%** where the market prices **2.44%** (2026-08-31, the 96.7th percentile
of the ten-year TIPS record since 2003; the thirty-year is 2.99%, the 99.8th since 2010). On
Shiller's measure today sits at the 19th percentile of 145 years and is unremarkable. On a
market-priced real yield the excess CAPE yield is **+0.03 pp on the August average and
−0.01 pp on the 2026-08-31 daily reading — the first sub-zero print in the 23-year TIPS
record**, and it has sat at the 0th percentile of 284 months for five consecutive months.

For scale on how far this has moved: the TIPS-based measure averaged **2.82 pp** over
2003-2026 with a standard deviation of 1.25, peaked at **5.80 pp** in 2009-03, and by annual
average has gone 2.83 (2022) → 1.72 (2023) → 0.94 (2024) → 0.74 (2025) → **0.46 (2026, to
August)**.

**The "low rates justify a high CAPE" defence has expired.** It was a good argument in 2021
and it is not one now.

Both prior CAPE peaks had a *negative* Shiller excess CAPE yield: **−1.09 pp** at 1999-12 and
**−0.61 pp** at 1929-09. On that measure today is less extreme than either. On the
market-priced measure the gap has closed to zero.

### 1.2 The same level from the web, and why the readings differ

| Measure | Value | Source as-of | Source, read 2026-08-22 |
| --- | ---: | --- | --- |
| Shiller CAPE | 41.74 (41.96 on 2026-08-21) | 2026-09-01 close | [multpl.com/shiller-pe](https://www.multpl.com/shiller-pe) |
| CAPE mean / median, from 1871 | 17.40 / 16.11 | full history | same |
| S&P 500 | 7,674.37 | 2026-08-21 | [TradingEconomics](https://tradingeconomics.com/united-states/stock-market) |
| 2026 YTD total return | +12.9% | 2026-08-21 | [ChartRow](https://chartrow.com/sp500/returns) |
| Forward 12-month P/E | 19.6 (20.0 on 2026-08-07; 5yr avg 19.9, 10yr avg 19.0) | 2026-08-28 | [FactSet Earnings Insight](https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/EarningsInsight_082826.pdf) |
| Forward P/E, forward EPS | 19.7, $393.28 | 2026-08-22 | [Yardeni](https://www.yardeniquicktakes.com/us-market-call-stocks-getting-cheaper-as-earnings-outpace-prices/) |
| Trailing P/E, earnings yield | 29.58, 3.38% | 2026-08-21 | [multpl](https://www.multpl.com/s-p-500-pe-ratio) |
| 10y nominal / 10y TIPS / 30y TIPS (CMT) | 4.75% / 2.44% / 2.99% | 2026-08-31 | [Federal Reserve H.15](https://www.federalreserve.gov/releases/h15/) |
| 10y nominal / 10y TIPS (CMT) | 4.69% / 2.35% | 2026-08-20 | H.15, the reading the §2–§4 tables were built on |
| 10y nominal / 10y TIPS | 4.74% / 2.39% | 2026-08-21 | [TradingEconomics](https://tradingeconomics.com/united-states/government-bond-yield) |
| 10y TIPS auction real yield | 2.438%, highest since Oct 2008 | 2026-07-23 | [tipswatch](https://tipswatch.com/2026/07/23/10-year-tips-auction-gets-real-yield-of-2-438-a-great-result-for-investors/) |

**Four "current" CAPE readings disagree: 41.18, 41.58, 41.96 and 40.4.** Scaling Shiller's
41.178 from its 7,600.50 August 1st close to 7,674.37 on August 21 gives **41.58**, which is
what GuruFocus published for August 2026 — so the staleness explains part of the gap and the
construction explains the rest. multpl's 41.96 is *not* reproduced by that scaling. The test
`test_rescale_cape_reconciles_the_workbook_with_an_independent_reading` pins this. **No page
may quote these interchangeably**, and the difference between 41.2 and 42.0 changes no
decision below.

**The tension that matters is between CAPE and the forward multiple.** CAPE is at the 99th
percentile and trailing P/E is 29.6x, yet forward P/E is 20.0 and *fell* over 2026, because
forward earnings rose 24.9% year-to-date against a 12.1% price gain (Yardeni, 2026-08-22).
FactSet reports Q2 2026 blended earnings growth of **50.4%** (32.0% excluding Alphabet and
Amazon) and an aggregate earnings surprise of **29.2%, the highest since it began tracking in
2008**, which it flags as *"heavily influenced by the two tech giants' gains related to
equity investments and valuations"* — mark-to-market on equity stakes, not operating income.
A ten-year smoothed denominator does not get that relief; a forward multiple gets all of it.
**Which of those two is right is the question, and this repository cannot answer it.**

### 1.3 International

| Market | CAPE | Source as-of |
| --- | ---: | --- |
| Global (3,000 largest, ~64% US) | 29.12 | 2026-06-30 |
| **United States** | **35.82** | 2026-06-30 |
| **Global ex-US** | **21.02** | 2026-06-30 |
| **Emerging markets** | **19.36** | 2026-06-30 |
| Japan / Korea / Taiwan | 38.59 / 40.76 / 46.44 | 2026-06-30 |
| Germany / France / UK / Australia | 23.28 / 20.91 / 20.07 / 20.44 | 2026-06-30 |
| China / Hong Kong | 18.18 / 9.49 | 2026-06-30 |

Source: [Siblis Research](https://siblisresearch.com/data/cape-ratios-by-country/) and its
[world CAPE page](https://siblisresearch.com/data/world-cape-ratio/), read 2026-08-22. **US
premium: 1.70x over developed ex-US, 1.85x over EM**, computed inside one methodology.
Siblis's own US CAPE is 35.82, not 41.96; dividing multpl's US figure by Siblis's ex-US
figure would give a spurious 2.00x.

Two qualifications that cut against the simple story. **Japan, Korea and Taiwan are at or
above US levels** — the developed-ex-US discount is concentrated in Europe, the UK, Australia
and Greater China. And AQR reports that while *"the U.S. CAPE ratio of nearly 40 is at the
96th percentile since 1980, [...] non-U.S. global developed CAPE is near the historical
median"*, the YE2025 **MSCI EM CAPE of 23 sits at the 98th percentile since 2001**
([AQR 2026 Capital Market Assumptions](https://www.aqr.com/-/media/AQR/Documents/Alternative-Thinking/AQR-Alternative-Thinking---2026-Capital-Market-Assumptions.pdf?sc_lang=en),
`as of` start of 2026). **EM is cheap against the US and expensive against itself.**

### 1.4 Published forecasts, labelled as forecasts

Not measurements. Each is a model output on that firm's assumptions, and AQR states there is
a 50% chance realised ten-year returns fall outside its own error bars.

| Source, as-of | US large | Developed ex-US | EM | Units |
| --- | ---: | ---: | ---: | --- |
| [GMO](https://www.gmo.com/globalassets/articles/gmo-7-year-asset-class-forecast/2026/gmo-7-year-asset-class-forecastjun26.pdf), 2026-06-30 | **−8.1%** | −1.7% | −1.8% | 7yr real, "normal rates" |
| AQR, 2025-12-31 | **3.9%** | 4.9% | 5.1% | 5-10yr local real |
| [Vanguard](https://corporate.vanguard.com/content/corporatesite/us/en/corp/vemo/vemo-return-forecasts.html), 2026-06-30 | **4.2-6.2%** | 4.5-6.5% | 2.0-4.0% | 10yr nominal |

**Every forecaster with a public number ranks US large-cap last.** They do not agree on
anything else: GMO's US large-cap forecast is 12 pp below AQR's, and GMO and Vanguard put EM
*below* the US while AQR puts it above. AQR's global 60/40 expected real return is **3.4%**,
about 1.5 pp above its 2021 low and still well below the long-run US average.

**Six managers' 2026 assumptions, reconciled to one basis** (ten-year nominal geometric USD,
collected 2026-09-01 from each firm's own document), span fourteen points on US large cap:
Syzygy/Research Affiliates **3.3%** (as of 2026-07-31, full reversion of the cyclically
adjusted earnings yield over twenty years), Vanguard 5.1%, AQR 6.3% (no reversion term),
J.P. Morgan 6.7%, BlackRock **9.0%** (an AI-earnings scenario weighting), and GMO −5.1% on a
seven-year real forecast converted at 2.3% inflation. Their implied equity premium over a
market TIPS runs from −9.9 pp (GMO) and −2.2 (RA) through +1.2 to +1.5 (J.P. Morgan,
Vanguard, AQR) to +3.8 (BlackRock): four of six sit between −2.2 and +1.5, the models that
revert the multiple at the bottom and the models that do not at the top. Every source except
BlackRock puts developed ex-US above US large cap; bonds and cash agree within half a point.
**These are external inputs, displayed for the reader and sized on by nothing here**
([decision 0012](../decisions/0012-valuation-enters-through-the-drawdown-assumption.md)).

### 1.5 Sources that could not be reached

Recorded as evidence about the data contract, not as an excuse.

- **FRED** returned HTTP 403 to the web-fetch tool and to `curl`, but answered the research
  workspace's own `requests` client normally on 2026-08-23. **The block is on the fetch path,
  not on the source**, and `DGS10`/`DFII10` remain usable from `research/`.
- **Research Affiliates Asset Allocation Interactive has moved**:
  `interactive.researchaffiliates.com/asset-allocation` now 301-redirects to
  `interactive.syzygyassetmanagement.com`, which renders nothing without JavaScript. It is
  not usable as a programmatic source.
- **403 or paywalled**: GuruFocus, Morningstar (both editions), Barclays `indices.cib.barclays`,
  MacroMicro, Slickcharts, CNBC, Schwab, MSCI factsheets, YCharts, FinanceCharts.
- **Timed out**: `home.treasury.gov` real yield curve, superseded by H.15.
- **Binary-only**: the GMO, AQR and J.P. Morgan PDFs needed local text or image extraction. If
  any becomes a recurring input, that step is part of the contract, and figures read off a
  chart rather than printed carry roughly ±0.5 pp of reading error — every such figure on this
  page is marked with ≈.
- **AQR's "Exceptional Expectations" is gated on aqr.com.** Every `-/media/` path returns HTML
  and `?aqrPDF=1` returns a cover stub. §5.1's decomposition was read from a third-party
  mirror whose authors, disclosures and exhibit sources are intact. **A primary-source copy
  should be obtained before this figure supports a decision record.**
- **Vanguard's currency-valuation page is three years stale**, dated 2023-09-30. It is the only
  free source found for a dollar over/undervaluation estimate with a stated method, and it
  cannot be used for a 2026 decision. This is the binding gap on the hedging question in §6.1.
- **BIS/FRED real effective exchange rate**: not reachable, so the dollar's real-effective
  percentile in §5.2 is a chart-read from a J.P. Morgan slide rather than a computed figure.
- **Shiller's own excess-CAPE-yield publication is not reachable.** Three secondary sources
  quote "current" ECY values spanning 3x (0.49%, 0.97%, 1.46%) on three different real-rate
  definitions. This repository uses the workbook's own `Excess_CAPE_Yield` column and its own
  TIPS-based recomputation, and reports both, because there is no single number to quote.

---

## 2. What valuation predicts, and with what resolution

### 2.1 The regression, and the standard error that changes the answer

Shiller real total return, 1881-01…2026-08, regressor `log(1/CAPE)`, response the annualised
subsequent real log total return.

| Horizon | Overlapping obs | **Independent obs** | Slope | `t` Newey-West | **`t` Hodrick 1B** | `t` non-overlapping | In-sample `R**2` |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 yr | 1,736 | 144.7 | 0.0771 | 2.53 | 2.57 | 2.17 | 0.032 |
| 5 yr | 1,688 | 28.1 | 0.0664 | 2.86 | 2.70 | **1.48** | 0.137 |
| **10 yr** | 1,628 | **13.6** | 0.0615 | **4.84** | **2.47** | 4.42 | 0.255 |
| **15 yr** | 1,568 | **8.7** | 0.0574 | **4.01** | **2.11** | 2.87 | 0.372 |

Three readings of the same data. **Newey-West with a lag equal to the horizon is asked for
120 autocovariances from 13.6 independent windows and answers confidently**; Hodrick's 1B
estimator sums the regressors backward instead of the residuals forward, so the number of
quantities estimated does not grow with the horizon, and it halves the statistic. At five
years the non-overlapping regression — which needs no HAC at all, and has 29 observations —
gives `t = 1.48`.

**The rising `R**2` is not rising information.** It rises because averaging returns over a
longer window removes variance from the denominator, and the independent-observation count
falls in exact step. An `R**2` of 0.372 computed on 8.7 independent observations is not
stronger evidence than an `R**2` of 0.032 on 144.7.

### 2.1a Robustness: the averaged price series, and what it is worth here

**Shiller's `P` is the average of the month's daily closes, not a month-end price**, and the
[evidence base](evidence-base.md) records the source-fitness finding that this disqualifies it
for rules that depend on serial correlation. An overlapping long-horizon regression is not a
moving-average rule, but it is in the same family — induced autocorrelation inflates HAC
standard errors' cousins — so the check is owed rather than assumed.

Same predictor, same 1926-07…2026-06 window, two responses: Shiller's monthly-averaged real
total return, and Ken French's month-end `Mkt-RF + RF` deflated by the same CPI.

| Response | AR(1) monthly | Ann. sd | h | Slope | `t` Newey-West | **`t` Hodrick 1B** |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **French, month-end** | **+0.087** | 18.39% | 10 yr | 0.0673 | 4.37 | **1.88** |
| **Shiller, monthly-average** | **+0.265** | 15.26% | 10 yr | 0.0707 | 4.31 | **2.37** |
| French, month-end | +0.087 | 18.39% | 15 yr | 0.0640 | 3.77 | **2.01** |
| Shiller, monthly-average | +0.265 | 15.26% | 15 yr | 0.0693 | 4.04 | **2.57** |

**Three readings.** The averaging **triples the first-order autocorrelation** (+0.087 to
+0.265) exactly as the trend work found on its own window. It inflates the Hodrick statistic
by about a quarter, and **on month-end data the ten-year `t` is 1.88 — below the conventional
threshold the averaged series clears.** And the Newey-West statistic barely moves (4.37 vs
4.31), which is its own indictment: the estimator is so oversized in this design that a
tripling of the response's autocorrelation is invisible inside it.

**Two things change at once and this design cannot separate them**: the dating, and the
universe, since French covers all of CRSP (18.4% annualised volatility) where Shiller covers
the S&P composite (15.3%). The AR(1) column isolates the dating, which is the part at issue.

**The direction of the effect is against the headline result, not for it.** Every conclusion
below is therefore quoted on the Shiller series, which is the more favourable of the two to
the case that valuation predicts.

### 2.2 Stambaugh bias, which is unusually large here

| Quantity | Value |
| --- | ---: |
| Monthly autoregressive root of `log(1/CAPE)` | **0.9966** |
| Correlation, return innovation with predictor innovation | **−0.9975** |
| Fitted monthly slope | 0.003076 |
| Stambaugh bias | 0.002259 |
| **Bias as a share of the slope** | **73.4%** |
| Annualised slope, uncorrected → corrected | **0.0369 → 0.0098** |

Both ingredients are at their theoretical maximum here **for a mechanical reason**: price sits
in the denominator of the valuation ratio and inside the return, so the predictor's innovation
is very nearly the negative of the return's. This is not a defect of CAPE specifically; it
applies to every price-scaled predictor. The consequence is that **the uncorrected slope
overstates by roughly a factor of four**, and almost no published version of this chart
corrects it.

### 2.3 The out-of-sample record

Expanding-window coefficients and an expanding-window benchmark mean, both using only outcomes
already *observed* at the forecast origin.

| Horizon | Origins from | Forecasts | Independent | **`R**2` out-of-sample** | Model mean error |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 yr | 1911 | 1,376 | 114.7 | −0.044 | +1.71 pp |
| 5 yr | 1911 | 1,328 | 22.1 | −0.156 | +2.12 pp |
| 10 yr | 1911 | 1,268 | 10.6 | +0.001 | +2.02 pp |
| 15 yr | 1911 | 1,208 | 6.7 | +0.189 | +1.07 pp |
| **1 yr** | **1990** | 428 | 35.7 | **−0.212** | **+7.77 pp** |
| **5 yr** | **1990** | 380 | 6.3 | **−0.423** | **+6.29 pp** |
| **10 yr** | **1990** | 320 | 2.7 | **−0.437** | **+4.86 pp** |
| **15 yr** | **1990** | 260 | 1.4 | **−1.878** | **+4.25 pp** |

Over the full sample the model is roughly a draw with a rolling mean at ten years and beats it
at fifteen. **Since 1990 it loses at every horizon, and the sign of the error is consistent:
it forecast too little return, by between four and eight percentage points a year.** The
model's mean error is positive in every row of the table, full sample included — **it has
been systematically pessimistic for a century**, which is what a persistently rising valuation
level does to a mean-reverting model.

The 1990-onward rows carry 1.4 to 6.3 independent observations. They are a record, not a test.

### 2.4 Is the level comparable across eras?

Two mechanical adjustments, in opposite directions, and neither is small.

**Payout has moved out of dividends.** Shiller's own `D/E` ratio is **0.307** (`as of
2026-03`) against a **0.646** average before 1980. More than half the historical dividend
payout now leaves as buybacks or retention, which raises earnings growth per share and means a
given CAPE supports a higher return than the same CAPE did in 1950. Shiller publishes a
total-return CAPE for exactly this reason; it stands at **43.98**, at the **98.7th**
percentile — so the adjustment moves the level up and the *percentile* barely at all.

**Real rates are the other adjustment, and it now points the other way.** §1.1 has the
arithmetic: the TIPS-based excess CAPE yield is at the bottom of its 23-year range.

**Two more are named and not quantified here.** Post-2001 goodwill impairment accounting
depresses reported `E` in recessions, raising CAPE mechanically. And index concentration is at
a record: the Magnificent Seven are **34.03% of S&P 500 market capitalisation** (`as of
2026-07`, [Voronoi](https://www.voronoiapp.com/markets/-Magnificent-Seven-Climb-to-Record-34-Share-of-SP-500-3175)),
against a historical top-ten average near 24% and a prior peak near 28% in 1970. Yardeni puts
the Mag-7 forward P/E at 23.7, its narrowest premium to the broad market since April 2025 —
concentration currently rising on delivered earnings rather than on multiple expansion. **This
page does not adjust the CAPE for any of these.** Their existence is the reason the level's
percentile should not be read as a probability.

---

## 3. Does conditioning the allocation on valuation beat not conditioning it?

The decision-relevant test. Shiller real equity total return against Shiller's modelled real
ten-year bond total return, 1921-01…2026-07 (1,267 months after a 40-year burn-in),
monthly rebalancing, all percentiles expanding-window with no look-ahead.

| Rule | Mean weight | Turnover | **Gross vs constant** | **Timing vs matched** | **Net vs constant** | Tracking error | MDE, 30 yr |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Constant 80/20 | 0.800 | 6.1% | — | — | — | — | — |
| CAPE level tilt, k=0.4 | 0.755 | 15.9% | **−9.0 bp** | +16.3 bp | **−86.0 bp** | 225 bp | 53 bp |
| **Excess CAPE yield tilt, k=0.4** | 0.803 | 14.7% | **+49.5 bp** | **+47.7 bp** | **−15.6 bp** | 146 bp | **34 bp** |
| CAPE level tilt, k=0.8 | 0.690 | 22.1% | −36.2 bp | +25.5 bp | −161.8 bp | 400 bp | 94 bp |
| Excess CAPE yield tilt, k=0.8 | 0.792 | 21.5% | +79.4 bp | +84.1 bp | −37.5 bp | 262 bp | 61 bp |
| *Control:* real yield only, k=0.4 | 0.760 | 10.4% | **−80.5 bp** | −58.2 bp | −115.5 bp | 154 bp | 36 bp |
| Halve above the CAPE median | 0.637 | 24.0% | −55.2 bp | +36.6 bp | −202.3 bp | 510 bp | 119 bp |

Net figures charge 10 bp of execution and a **15% effective** capital-gains rate on the equity
sold. "Timing vs matched" compares each rule with a constant mix held at **the rule's own
average weight**, which strips out the part of any answer that is really just "held less
equity."

**Three things follow.**

**The CAPE level is the wrong signal.** Every level rule loses gross. Its *timing* component
is mildly positive (+16 to +37 bp), so it is not that the level is uninformative — it is that
acting on it costs more exposure than the timing is worth, because a level that drifts upward
makes an expanding percentile rule sell continuously.

**The excess CAPE yield is a genuinely different object.** +49.5 bp gross, of which +47.7 bp
survives the matched-weight control, at an average weight of 0.803 — it barely de-risks at
all, it reallocates *when*. **The signal is joint, and neither leg works alone.** A rule
tilting on the implied **real yield alone**, with no valuation term at all, lost **−80.5 bp**
gross and was ahead in **0 of 908** rolling 30-year windows; the CAPE-yield-alone rule managed
only +16 bp of timing. So the excess-CAPE-yield rule is not a bond-cheapness bet wearing a
valuation label, and it is not the CAPE level with extra steps.

**Tax decides it.** Charging the rule only its turnover *in excess of* the constant-mix
control's own 6.1% — because a constant 80/20 also rebalances and also pays tax — the
break-even effective capital-gains rate is:

| Rule | Gross | Turnover over control | **Break-even effective CGT** | Net at 5% | Net at 15% |
| --- | ---: | ---: | ---: | ---: | ---: |
| Excess CAPE yield, k=0.4 | +49.5 bp | 8.6 pp | **11.3%** | +27.2 bp | −15.7 bp |
| Excess CAPE yield, k=0.8 | +79.4 bp | 15.4 pp | **10.1%** | +39.2 bp | −37.9 bp |

The **effective** rate is the statutory rate times the embedded unrealised gain fraction. A
long-held taxable position at a 15% federal long-term rate and 75% embedded gain sits at
about 11% — **exactly on the break-even**. Add state tax or the 3.8% net investment income
tax and it is comfortably below water. In a tax-advantaged account the effective rate is zero
and the rule nets **+48.6 bp**.

### 3.1 The distribution, which is what the investor actually faces

An investor gets one draw, so the mean is the wrong summary. Rolling 30-year windows,
annualised difference against the constant 80/20:

| Rule | Gross median | **Gross share ahead** | Net median | **Net share ahead** |
| --- | ---: | ---: | ---: | ---: |
| CAPE level tilt, k=0.4 | −6.1 bp | 40.0% | −77.2 bp | **3.7%** |
| **Excess CAPE yield tilt, k=0.4** | +29.1 bp | **98.5%** | −36.6 bp | **39.4%** |
| Halve above the CAPE median | −48.3 bp | 25.0% | −216.4 bp | 5.0% |

**908 windows from about 2.5 independent 30-year blocks.** The 98.5% is not a 98.5%
probability of anything; it is one century seen 908 times.

Neither is the edge stable across eras. Gross, against the constant 80/20:

| Rule | 1921-1950 | 1950-1980 | 1980-2000 | 2000- |
| --- | ---: | ---: | ---: | ---: |
| CAPE level tilt, k=0.4 | +89.4 bp | −7.6 bp | −77.2 bp | −66.4 bp |
| **Excess CAPE yield tilt, k=0.4** | +115.0 bp | +52.8 bp | **−27.8 bp** | +32.5 bp |
| Halve above the CAPE median | +174.1 bp | −99.2 bp | −169.2 bp | −169.8 bp |

**The CAPE-level rules earned their entire historical reputation in one era and have lost in
every era since 1950.** The excess-yield rule has the wrong sign in one of four. Each cell is
about 0.7 independent 30-year blocks, so the dispersion is not itself evidence of regime
change — but it is evidence that the full-sample mean is not a stable expectation.

### 3.2 Resolution

The instrument's limits, stated before any verdict is read from it.

- The excess-CAPE-yield rule's gross edge of **49.5 bp against 146 bp** of tracking error
  clears its own 30-year minimum detectable effect of **34 bp** and would take **14 years**
  to reach 90% confidence — on the 106-year sample. **Net, the edge is negative**, so no
  horizon demonstrates it.
- Every CAPE-level rule has an MDE between **53 and 119 bp/yr** and a measured edge of the
  wrong sign. Those rules are not merely unproven; they lost by more than the design's
  resolution in the taxable case.
- Every backtest above uses **revised, non-point-in-time** Shiller data. The whole workbook is
  rebuilt on each release, so the "expanding window" hands each historical decision a history
  that had not yet been written. **This biases the conditional rules in their own favour**,
  and the level rules still lose.

---

## 4. Valuation as a risk statement rather than a forecast

This is the part of the investor's concern that the evidence supports.

Subsequent annualised real total return by entry CAPE:

| Horizon | Bucket | Months | **Independent** | Distinct years | p10 | Median | **P(real < 0)** |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 yr | **CAPE > 30** | 57 | **0.48** | **7** | −4.37% | **−1.13%** | **59.6%** |
| 10 yr | CAPE 25-30 | 107 | 0.89 | 17 | +1.11% | +5.56% | 4.7% |
| 10 yr | CAPE < 25 | 1,464 | 12.20 | 129 | −0.21% | +7.08% | 10.5% |
| 15 yr | **CAPE > 30** | 57 | 0.32 | 7 | +1.81% | **+2.15%** | **3.5%** |
| 20 yr | **CAPE > 30** | 57 | 0.24 | 7 | +3.58% | **+4.31%** | **0.0%** |

And the holdability statistic, over fifteen years from entry:

| Bucket | **Median worst real drawdown** | Worst | **Median share of months below real entry** | p90 |
| --- | ---: | ---: | ---: | ---: |
| **CAPE > 30** | **−51.8%** | −76.8% | **59.7%** | 83.6% |
| CAPE < 20 | −36.7% | −76.8% | **5.0%** | 42.5% |

**Read the two tables together.** A buyer at CAPE above 30 did badly over ten years, recovered
by fifteen, and did fine by twenty. What was different the whole way through was the *path*:
the median such buyer spent **six of every ten months of the next fifteen years below their
own real entry level**, against one month in twenty for a buyer below CAPE 20, and watched a
median 52% real drawdown along the way.

**That is an argument about whether the portfolio gets held, not about what it returns.** It
is the mechanism by which a high entry valuation can legitimately lower an equity share — via
the drawdown constraint that [setting the equity share](setting-the-equity-share.md) §1.2
identifies as the thing that actually binds, rather than via a return forecast.

**The resolution caveat is severe and unavoidable.** The `CAPE > 30` bucket is 57 monthly
observations spanning **seven distinct calendar years and two episodes** — 1929, and
1997-2002 — which is **0.32 independent fifteen-year observations**. Current CAPE is above
every month in that bucket except the 1999-2000 window. **The conditioning set for the
question being asked is one episode.** No probability in the table above should be quoted as
one.

---

## 5. The relative call, which is a different and better-posed question

A cross-sectional comparison does not depend on any market's level drifting, which is the
defect that sinks §2. Jordà-Schularick-Taylor R6, 18 countries, 1870-2020, **local-currency
real** returns, valuation measured by **dividend yield**. US minus the panel median.

| Horizon | Years | **Independent** | Intercept | Slope | `t` | `R**2` | Residual sd |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 yr | 149 | 149.0 | +0.0175 | +0.0844 | 2.53 | 0.035 | 14.08 pp |
| 5 yr | 145 | 29.0 | +0.0178 | +0.0812 | 4.31 | 0.239 | 4.46 pp |
| **10 yr** | 140 | **14.0** | **+0.0184** | **+0.0605** | **3.65** | 0.270 | **2.95 pp** |
| 15 yr | 135 | 9.0 | +0.0182 | +0.0554 | 5.23 | 0.327 | 2.25 pp |

**This is the better-supported estimand.** It has more independent observations than the US
time series at the same horizon, and its identification is cross-sectional. Demeaning both
variables inside each year — so that every global shock is absorbed by a year fixed effect and
only within-year variation identifies the slope — leaves it intact, with Driscoll-Kraay
standard errors clustered by year and HAC-corrected over the overlap:

| Horizon | Country-years | Years | Slope | `t` (Driscoll-Kraay) | Within `R**2` |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 yr | 2,137 | 150 | +0.0518 | 3.01 | 0.016 |
| 5 yr | 2,073 | 146 | +0.0535 | 5.68 | 0.092 |
| 10 yr | 1,988 | 141 | +0.0380 | 5.21 | 0.101 |

The within-year slope at ten years, **+0.038**, is well below the US time-series slope of
+0.062 — a one-log-unit valuation gap between two countries buys less than a one-log-unit
change in one country's own level appears to. That is what you would expect if part of the
time-series slope is the drift §2.2 and §2.3 identify.

**And it does not survive the modern era either.**

| Era | Years | Independent | Slope | `t` | **MDE at 80% power** |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1870-1945 | 74 | 7.4 | +0.0707 | 3.37 | 0.052 |
| 1945-1990 | 45 | 4.5 | +0.0741 | 6.10 | 0.030 |
| **1990-2010** | 21 | **2.1** | **−0.0006** | **−0.03** | **0.043** |

The 1990-2010 design could have detected the historical slope of ~0.07 at 80% power and found
**zero**. That is a more informative null than §2.3's, and it is still built on 2.1
independent ten-year observations. **The honest statement is that the cross-sectional relation
held for 120 years and has not been detectable in the only era anyone is asking about** —
which is exactly the era in which the "US is expensive relative to the world" call has been
made and been wrong.

### 5.1 How old the US premium actually is, and what built it

**The US premium is about fifteen years old and its sign was inverted thirty-five years ago.**
AQR's Ilmanen and Maloney track MSCI USA CAPE against MSCI World ex-USA CAPE from 1980: in the
late 1980s **the US CAPE was less than half the non-US CAPE** (the Nikkei bubble), the two
converged through the 1990s and sat near parity until the financial crisis, and by end-2024
the US was **"nearly twice"** non-US — a relative re-rating of **4x since 1989 and 2x since
2009** (["Exceptional Expectations: U.S. vs. Non-U.S. Equities"](https://www.aqr.com/Insights/Research/White-Papers/Exceptional-Expectations-US-vs-Non-US-Equities),
May 2025, data to 2025-04, read 2026-08-22 from a
[third-party mirror](https://mebfaber.com/wp-content/uploads/2025/05/Exceptional-Expectations-US-vs-Non-US-Equities-Pt2.pdf)
because the paper is gated on aqr.com).

**And the premium is almost entirely a price change, not an earnings change.** Their
decomposition of 35 years of MSCI USA outperformance over MSCI World ex-USA to 2024-12,
currency-hedged and real, totalling **4.7 pp/yr**:

| Component | Contribution |
| --- | ---: |
| **Relative valuation change (re-rating)** | **+3.8 pp** |
| Real EPS growth edge | +1.1 pp |
| Dividend yield differential | −0.6 pp |
| Real interest rate differential | −0.3 pp |

**About 81% of it was re-rating.** For scale, AQR puts the US's long-run *growth* edge at
about 1 pp/yr over the past century and its long-run *return* edge near 2 pp/yr, with the
cumulative-to-date figure trough at 1.1 pp (end-1988) and peak at 2.2 pp (end-2024).

**This is the strongest available argument for a valuation tilt and it is not a CAPE
argument.** A premium built out of multiple expansion is a premium that a reversal of multiple
expansion takes away; a premium built out of earnings growth is not. AQR's own arithmetic for
what reversion would look like: **a 45% fall in US prices from December 2024 levels** returns
the two CAPEs to parity, or equivalently a positive-but-disappointing US growth edge of ~1
pp/yr with 5 pp/yr of relative repricing over a decade.

**It is also the argument with the most obvious counter, and AQR supplies that too:** *"about
half of US outperformance in the past 15 years and of its relative richness can be attributed
to its different sector composition than the rest of the world (mainly a larger tech
sector)."* **Half.** A sector-neutral version of the spread is roughly half the headline.

### 5.2 Three confounds, now measured rather than named

**Buybacks close about half the payout gap, and about a third of the US's own CAPE
elevation.** The US-minus-panel log *dividend*-yield spread by decade — **−0.093 (1990s),
−0.498 (2000s), −0.516 (2010s), −0.259 (2020s)** against a full-sample mean of −0.003 — moved
to a large discount exactly as buybacks became the majority of US payout, and exactly when the
cross-sectional relation stopped working. Total shareholder yield tells a different story
(J.P. Morgan *Guide to the Markets — UK* slide 49, `as of 2026-06-30`, chart-read):

| | Dividend yield | Net buyback yield | **Total shareholder yield** |
| --- | ---: | ---: | ---: |
| US (S&P 500) | ≈1.35% | ≈1.45% | **≈2.8%** |
| Europe ex-UK | ≈2.80% | ≈0.75% | **≈3.55%** |
| UK (FTSE 100) | ≈3.45% | ≈1.85% | **≈5.30%** |
| EM | ≈2.65% | **≈−0.50%** | **≈2.15%** |

The US-versus-Europe *dividend* gap is ≈1.45 pp; the *total shareholder yield* gap is ≈0.75 pp.
**Buybacks close roughly half of it.** And **EM's total shareholder yield is below the US's,
because EM dilutes** — Capital Group puts 2025 US buybacks at **147% of US dividends**, Europe
ex-UK at 44%, Japan at 72%, and **EM at under one-twelfth**
([Global Equity Study, March 2026](https://www.cfsrating.com/media/utgdxzan/cg-global-equity-study-2026-buybacks.pdf),
FY2025, read 2026-08-22).

**The adjustment does not improve prediction.** Keimling's payout-adjusted CAPE attributes
**about one-third** of the US's elevated recent valuation to the change in dividend policy —
and finds the adjusted measure shows *"no signs of superiority to ordinary CAPE either in
terms of `R**2` or correlation"*, with `R**2` deteriorating in **9 of 16 countries**
([StarCapital, 2016](https://mebfaber.com/wp-content/uploads/2016/02/Research_2016_01_Predicting_Stock_Market_Returns_Shiller_CAPE_Keimling_1_.pdf),
read 2026-08-22). **So the confound is real, it is roughly a third of the level, and
correcting for it buys no forecasting power.**

**Currency is the largest single term and this repository's panel does not price it.** JST
returns are local-currency real. J.P. Morgan's decomposition of USD total returns (*Guide to
the Markets — U.S.* slide 45, `as of 2026-06-30`, chart-read) puts the currency contribution
to unhedged non-US returns at **≈−1.7 pp/yr over 2010-2024**, then **≈+7.2 pp in 2025 alone**
(Eurozone **≈+14.7 pp**), then **≈−1.6 pp in 2026 H1** (Eurozone ≈−4.3 pp). **Currency, not
the multiple, drove 2025's international outperformance.** Across every dollar cycle since
1973 the currency contribution and the direction of US relative equity performance have agreed
in sign, and in the current cycle roughly three-quarters of the US's relative underperformance
is currency (*Guide to the Markets — UK* slide 13). For a USD investor, AQR's 2026 assumptions
put the carry from hedging Eurozone equity back to USD at **≈+0.8 pp/yr**.

**The unconditional US premium in the JST panel is large.** The intercept is **+1.84 pp/yr**
at ten years: at an *equal* valuation spread the US beat the panel median by nearly two points
a year over 150 years. Some of that is genuine and some is that the panel includes markets
that closed. Either way, **a relative-valuation model must overcome a large positive constant
before it recommends underweighting the US.**

### 5.3 What the published evidence says about this exact estimand

The most honest published statement found, from AQR on the relative US/non-US CAPE against
next-decade relative performance, 1979-12 to 2025-04:

> *"the relative US/Non-US CAPE has predicted quite well the next-decade relative performance.
> The predictive correlation is +0.5 over an admittedly short sample (only 4+ independent
> observations)."*

**A correlation of 0.5 is an `R**2` near 0.25 on four independent draws.** That is the same
shape as §5's result and the same shape as §2's: a real relationship with almost no
statistical resolution. AQR add, in the same paper, that *"this prediction has not panned out
well for the past decade"* and that consensus capital-market assumptions *"since 2011
consistently assumed lower future return for US equities than for Non-US"* — **the gap has
been forecasting US underperformance for fifteen years and been wrong throughout.**

The closest published analogue to §3's timing test reaches §3's conclusion independently. AQR's
[*Market Timing: Sin a Little*](https://www.aqr.com/-/media/AQR/Documents/Insights/White-Papers/Market-Timing-Sin-a-Little.pdf)
(2017) runs a realistic CAPE contrarian rule on US equity with no look-ahead:

| | 1900-2015 buy & hold | Value timing | 1958-2015 buy & hold | Value timing |
| --- | ---: | ---: | ---: | ---: |
| **Sharpe** | **0.38** | **0.37** | **0.37** | **0.37** |
| Max relative drawdown | — | **−32%** | — | −32% |

> *"The results are disappointing. Even before costs, the timing strategy cannot beat the
> Sharpe ratio of buy-and-hold over either the full 116-year sample or the latter half…
> Neither return differences… nor Sharpe ratio differences… are statistically significant."*

And on the pooled cross-country level relation, Keimling's 16-country panel gives `R**2` 0.49
and correlation −0.67 against subsequent 10-15 year real returns, with a median subsequent real
return of **+0.5%/yr from a starting CAPE above 30** — accompanied by his own caveats that the
sample *"comprises only two independent 10-15-year periods"*, that removing Japan cuts the
pooled `R**2` by 0.07, and that per-country `R**2` ranges from **0.01 (Canada) to 0.90 (Hong
Kong)**.

**Three independent literatures, three different designs, one answer: the relationship is
there and the resolution is not.**

### 5.4 Where the spread sits now, and whether it has already narrowed

**It has narrowed, and mostly for a reason that is not a US de-rating.** Siblis's own
three-year table (`as of 2026-06-30`):

| | 2023-06-30 | 2024-12-31 | 2025-12-31 | **2026-06-30** |
| --- | ---: | ---: | ---: | ---: |
| United States | 27.53 | 32.39 | 34.73 | **35.82** |
| Japan | 26.39 | 26.14 | 29.38 | **38.59** |
| South Korea | 13.47 | 12.60 | 21.22 | **40.76** |
| Taiwan | 21.00 | 25.81 | 30.50 | **46.44** |
| Germany | 19.24 | 21.08 | 24.08 | **23.28** |
| UK | 18.42 | 18.20 | 20.19 | **20.07** |

**The US did not de-rate — Asia re-rated violently.** Korea's CAPE roughly tripled in eighteen
months. "International is cheap" is not true of the Asian half of EAFE and EM at these levels,
and the narrowing of the aggregate ratio is largely arithmetic on that.

On forward multiples the picture is milder. J.P. Morgan's relative forward P/E of MSCI ACWI
ex-US against the S&P 500 stands at a **−31% discount against a 20-year average of −20%**
(*Guide to the Markets — U.S.* slide 46, `as of 2026-06-30`) — on the US/ex-US convention,
**1.45x now against 1.25x on average.** That is 11 pp wider than average and **marginally
narrower than the −32% at 2026-01-01**. The same slide shows ACWI ex-US at a wider-than-average
discount in *every* sector it lists, so sector mix is not the whole of it on JPM's own data,
even though AQR attributes about half.

And relative *performance* has already delivered part of the trade and then stopped. In 2025
EAFE returned **+31.9% in USD against the S&P 500's +17.9%** — a 14 pp gap, and 41.3% for the
Eurozone. **In 2026 H1, EAFE returned +9.8% against the S&P 500's +10.2%**: the developed
relative trade stopped working, and ex-US only beat the US in aggregate because of Korea
(+118.9% USD YTD) and Taiwan (+62.6%). JPM's rolling two-year EAFE-minus-USA series was
continuously negative from about 2009 through 2025, bottomed near **−10%/yr in late 2024**,
and has since climbed only to roughly **0 to +2%** — *"fifteen years of US outperformance"* has
been given back for about eighteen months and the two-year window has barely reached zero.

### 5.5 Sizing the decision

Taking the ten-year fit at face value and plugging in the current spread — **an assumption,
not a measurement**, because it applies a dividend-yield elasticity to a CAPE ratio, and §5.2
has just shown the two differ by roughly half the gap:

Siblis's US/ex-US CAPE ratio of 1.704 is a log yield spread of −0.533. The fit implies the US
underperforms by **−1.38 pp/yr** over ten years, with a residual standard deviation of 2.95 pp
— **a 95% band of −7.2 to +4.4 pp/yr.** The interval is four times the point estimate and
comfortably contains zero and US outperformance.

**Two independent estimates land close to it.** AQR's December 2025 capital market assumptions
give US large-cap **3.9% real** against global developed ex-US **4.9%** — a **1.0 pp** gap;
their December 2024 version gave 4.2% against 6.1% hedged, a **1.9 pp** gap. AQR reach that
number from the payout yield alone: they set the valuation-reversion term to **zero** and
assume expected spot FX equals the inflation differential, so **their ex-US edge contains no
currency alpha and no mean reversion.** Read the other way round, their framing says the US
needs a **2.2 pp/yr growth edge** merely to match non-US, *assuming the valuation gap
persists*.

**A JST-panel fit built on 150 years of cross-country data, and a practitioner model built on
payout yields with no valuation term, both land near 1 to 1.9 pp/yr.** That is meaningful
agreement on the point estimate and says nothing about the interval, which remains four times
as wide.

What a shift is worth, at the JST point estimate:

| Shift out of US | Edge | Tracking error | P(ahead, 30 yr) | Years to 90% confidence |
| ---: | ---: | ---: | ---: | ---: |
| 5 pp | 6.9 bp | 40-72 bp | 0.70-0.83 | 55-178 |
| **10 pp** | **13.8 bp** | **80-144 bp** | **0.70-0.83** | **55-178** |
| 15 pp | 20.7 bp | 120-216 bp | 0.70-0.83 | 55-178 |

Tracking errors bracket an 8%/yr US-versus-developed relative return volatility against the
14.4%/yr the JST panel actually shows for US-minus-panel-median. **The information ratio does
not change with the size of the shift**, which is the same structure
[setting the equity share](setting-the-equity-share.md) §1.3 found on the equity ladder: the
size of the step barely changes how long it takes to prove.

### 5.6 The reframing that matters most

**Siblis's global index is ~64% US** (`as of 2026-06-30`). So:

| Split | Active bet against global market-cap weight |
| --- | ---: |
| **65/35** | **+1.0 pp** |
| 60/40 | −4.0 pp |
| 55/45 | −9.0 pp |
| 50/50 | −14.0 pp |

**65/35 is not a US overweight. It is approximately the global market portfolio.** The
question in front of the investor is therefore not "should I unwind an overweight" — there
isn't one — but "should I deliberately underweight the market portfolio on a signal whose
cross-sectional relation has been undetectable for 35 years and whose implied edge has a
confidence interval four times its point estimate."

---

## 6. What to do

### 6.1 The US/international split

**Keep 65/35 as the default. If it moves, move it to 60/40 with new contributions and not by
selling.**

The reasoning, in order of weight:

1. **65/35 is already market-cap neutral**, so no correction is owed. A move below it is a new
   active bet, not the removal of an old one.
2. **The direction of the tilt has the best argument on this page, and it is not a CAPE
   argument.** It is §5.1's decomposition: **81% of 35 years of US outperformance was
   re-rating, 23% was earnings growth.** A premium built out of multiple expansion is the kind
   a reversal takes back. That argument is about the *composition* of a realised return, which
   is a measurement, rather than about a forecast.
3. **Its size is small and its interval swamps it.** The JST fit implies **−1.38 pp/yr** with
   a 95% band of **−7.2 to +4.4**; AQR's payout-yield model implies **1.0 pp** (2025-12) or
   **1.9 pp** (2024-12) with no valuation-reversion term at all. Two very different methods
   agreeing on ~1-2 pp is real corroboration of the point estimate and no help at all with the
   interval.
4. **It is far too small to justify realising a capital gain.** ≈14 bp/yr per 10 pp shifted
   against 80-144 bp of tracking error, needing 55-178 years to demonstrate. At a 15%
   effective rate, moving 10 pp of a portfolio with 75% embedded gain costs about **113 bp of
   one-off wealth against an edge of 14 bp/yr** — an eight-year payback on a signal whose sign
   is not established.
5. **It is nearly free with new contributions**, which pay no tax to direct. If the investor
   wants a valuation tilt, this is where it belongs, and it is where
   [structural and tax edges](structural-and-tax-edges.md) put every other tilt.
6. **Much of the trade has already happened, and part of it was currency.** EAFE beat the
   S&P 500 by 14 pp in USD in 2025 and by −0.4 pp in 2026 H1. Currency contributed **≈+7 pp**
   of the 2025 non-US result and has been **negative again in 2026**. An investor moving now
   is buying after the re-rating and after the dollar's fall from its early-2025 peak — the
   broad real dollar is roughly 7-8% off that peak and still in the upper quartile of its
   29-year range, so there is less currency tailwind left than there was.
7. **Do not go to EM on the valuation argument.** EM's CAPE of 19.36 is cheap against the US
   and, per AQR, at the **98th percentile of its own history since 2001**. EM's **total
   shareholder yield (≈2.15%) is below the US's (≈2.8%)** because EM dilutes — buybacks are
   under one-twelfth of dividends there. And the forecasters disagree on EM more than on
   anything else: AQR +5.1% real, GMO −1.8% real, Vanguard 2.0-4.0% nominal. **There is no
   consensus to follow.**
8. **"International is cheap" is not true of Asia.** Japan 38.59, Korea 40.76 and Taiwan 46.44
   are at or above the US's 35.82. The developed-ex-US discount is a Europe, UK, Australia and
   Greater China phenomenon, and a cap-weighted EAFE purchase buys a lot of the expensive half.

**Confidence: high on "do not sell to move"; moderate on the direction; low on the size.**
The moderate rating on direction comes from the re-rating decomposition and from two
independent models agreeing on the sign. The low rating on size comes from the 1990-2010 null,
from AQR's own +0.5 correlation on *four independent observations*, and from the fact that
consensus capital-market assumptions have made this exact call every year since 2011 and been
wrong every year. **If the investor wants a number, 60/40 funded by new money is defensible.
50/50 is not supported by anything measured here.**

**On hedging**, which the split raises and this page has not tested: AQR's 2026 assumptions
put the carry from hedging Eurozone equity into USD at **≈+0.8 pp/yr** for a USD investor —
larger than the entire valuation edge in point 4. That is a contractual, rate-differential
quantity rather than a forecast, and **it deserves its own study before the split moves at
all.**

### 6.2 The equity share

**Do not cut it on the return forecast. Do widen the assumptions it is sized against.**

The forecast route fails at every step: the corrected slope is a quarter of the raw one, the
Hodrick statistic is 2.47 at ten years on 13.6 independent observations, and the out-of-sample
record since 1990 is negative at every horizon with a consistent four-to-eight point
pessimistic bias. And the regret of being wrong is not small, because it is linear in the
weight cut and needs no forecast to state:

| If the realised equity-over-bond real premium is | A 15 pp cut costs | Over 10 years | **Over 30 years** |
| ---: | ---: | ---: | ---: |
| +5.0%/yr | +75 bp/yr | −7.2% of terminal wealth | **−20.1%** |
| +4.0%/yr | +60 bp/yr | −5.8% | −16.5% |
| +3.0%/yr | +45 bp/yr | −4.4% | −12.6% |
| +2.0%/yr | +30 bp/yr | −3.0% | −8.6% |
| 0.0%/yr | 0 bp/yr | 0% | 0% |
| −2.0%/yr | −30 bp/yr | +3.0% | +9.4% |

For scale, the realised figure on this repository's own Shiller sample is **+4.59 pp/yr**
(equity 6.50% real log, modelled ten-year bond 1.91%, 1881-2026). **The investor should choose
the row they actually believe, and notice that the cut only pays in the bottom two.**

**The route that does work goes through the constraint.** §4 establishes that entry above
CAPE 30 historically meant a median 52% real drawdown and six of every ten months below real
entry for fifteen years. [Setting the equity share](setting-the-equity-share.md) §1.1-1.2
establishes that under the zero-leverage rule the growth objective alone returns a corner
solution, and **every bond in the portfolio is there because of a drawdown constraint nobody
has supplied a number for**. If the tolerable-drawdown number is set against a −37% real
assumption and the conditional history says −52%, then the constraint binds harder and the
implied weight falls — **as a constraint decision, not a market call, and the difference
matters because it tells the investor what would reverse it.**

**Concretely:** this page recommends no change to the equity share and instead recommends
that the drawdown assumption used to set it be widened from the unconditional −37% to the
high-valuation-conditional −52%, and the "months underwater" assumption from ~5% to ~60%
of a fifteen-year window. **Whether that widening changes the share depends on a number the
investor has not yet supplied.** That number — the tolerable peak-to-trough real drawdown —
is the single most valuable missing input in this repository, and it is worth more than any
further valuation research.

**The one conditional rule this licenses**, priced inside the leveraged construction by
Experiment 018 ([defensive engines](defensive-engines-in-the-construction.md)): at a stated
tolerance of −50% or tighter, hold 10 points of long TIPS unlevered in the traditional
account, funded from VTI and VXUS pro rata, and shrink the wrapper to the notional ladder's
figure (19.1% at −50%); at −60% or looser, hold none. The substitution's historical cost of 0.55–0.77 pp/yr
was earned on a 6–7 pp realised premium; at today's 0–1.5 pp over TIPS it is 0–0.2. The
default for a contributing investor is none.

### 6.3 A dynamic, valuation-conditional rule

**No, in a taxable account. Defensible but unpromoted in a sheltered one.**

- Rules on the CAPE **level** lose gross and net, in every specification tested. There is no
  version of this worth running.
- The **excess CAPE yield** rule is the only one with a real gross edge (+49.5 bp, +47.7 bp of
  it timing), and its break-even effective capital-gains rate is **11.3%** — below where a
  long-held taxable position sits.
- In a tax-advantaged account it nets **+48.6 bp against 146 bp of tracking error**. That is a
  real but modest number, on a rule that had the wrong sign in one of four eras, was measured
  on revised data that flatters it, and rests on ~2.5 independent 30-year windows. **It is
  `exploratory` and no specification was frozen.** It should not be implemented on this
  evidence; it is a candidate for a registered experiment.
- The signal's current reading, for the record and not as a recommendation (`as of
  2026-09-01`): the excess CAPE yield sits at the **18.7th percentile** of its expanding
  history on Shiller's own measure and the **0th percentile** of the TIPS era. The k = 0.4
  rule would hold **0.675 against its 0.80 anchor** — a cheap-end reading, held in 6.9% of
  months since 1921 with a minimum of 0.603, not the extreme — and a CAPE-level rule 0.604.
  Scaled to this investor's all-equity base that is about **84–88% equity** with the balance
  in a ten-year Treasury or TIPS, in the sheltered account only. Every caveat above travels
  with it: `exploratory`, wrong sign in 1980–2000, ~2.5 independent windows, revised data, a
  73% Stambaugh bias on the underlying slope, and a regret of 30–60 bp/yr if the realised
  premium is 2–4% (§6.2).

### 6.4 The one-line answer to the investor

**The evidence does not support timing, it does support a modest tilt funded by new money
rather than by sales, and it strongly supports a wider expected-drawdown assumption.** The
return-forecast case has a corrected slope a quarter the size of the advertised one, a
Hodrick `t` of 2.47 on 13.6 independent observations — 1.88 on month-end data — and a 35-year
out-of-sample losing record. The risk case has a median 52% real drawdown and six of fifteen
years underwater, from two episodes. The relative case is the best of the three, rests on the
fact that four-fifths of the US premium is re-rating rather than earnings, and is worth 14
bp/yr per 10 pp shifted against 80-144 bp of tracking error — less than the ≈80 bp/yr of carry
available from hedging the currency, which nobody here has studied.

---

## 7. Open questions, and the next informative test

**Open.**

- **Is the current earnings surge durable?** FactSet flags a record 29.2% aggregate surprise
  as heavily driven by mark-to-market on equity stakes rather than operating income, and
  hyperscaler capital spending is reportedly running near 100% of operating cash flow while
  buyback activity at those firms is down 64% year on year. CAPE and the forward multiple
  disagree by a factor the answer to this question would resolve. **This repository has no
  instrument for it.**
- **What does the excess CAPE yield rule do on a point-in-time history?** Every result in §3
  used a revised workbook. No vintage archive is published, so this needs a different source.
- **Does the cross-sectional relation hold on cap-weighted regional indices with currency?**
  The JST panel is local-currency, equal-treatment, dividend-yield-based and ends in 2020. A
  test on MSCI USA against MSCI EAFE and EM in USD, with a CAPE or composite valuation
  measure, would answer the actual question. `research/` already holds regional French factor
  files used by Experiments 005 and 009.
- **What is currency hedging worth, and should the international sleeve be hedged?** AQR puts
  the carry at ≈+0.8 pp/yr for a USD investor — larger than the valuation edge in §6.1 — and
  §5.2 shows currency has been the largest single term in relative returns. **This page did
  not test it and it is now the most under-researched input to the split.**
- **How much of the US/ex-US gap survives sector neutralisation?** AQR says about half of the
  US's relative richness is sector composition; J.P. Morgan's slide shows ACWI ex-US at a
  wider-than-average discount in every sector. **Those two are not obviously compatible** and
  a sector-neutral relative CAPE computed here would settle it.
- **Two published readings could not be reconciled and are recorded as data-contract
  findings.** Four "current" US CAPE readings span 40.4 to 41.96 on three constructions
  (§1.2). And J.P. Morgan's *Guide to the Markets — UK* slide 59 prints an MSCI Europe ex-UK
  **CAPE of 41.3x** against Siblis's Germany 23.28 and France 20.91 for the same date. **It is
  irreconcilable and this page does not use it.**

**Not open.** Whether the CAPE *level* alone should drive an allocation rule. Every
specification tested lost, gross and net; the timing component that does exist is swamped by
the exposure it gives up; and AQR's independent 116-year test of a realistic contrarian CAPE
rule found a Sharpe of 0.37 against buy-and-hold's 0.38 with a −32% relative drawdown.
Reopening condition: a point-in-time history, or a measure that removes the upward drift that
makes an expanding percentile rule sell continuously.

**Next informative test.** The cap-weighted, USD, **currency-decomposed** version of §5 on
regional indices, reporting the hedged and unhedged legs separately. It targets the estimand
with the most decision leverage (the split), it is the one of the three claims with a
defensible identification strategy, the currency term turns out to be larger than the
valuation term, and the data is already partly in the cache. Second priority is the investor's
tolerable-drawdown number, which is not a research task at all and is worth more than the
first.

---

## Status

§1 is **read**, with sources and read dates; §§2-5 are **measured** and `exploratory`; §6 is
**interpretation**. Nothing here is promoted, no specification was frozen before the results
were seen, and no experiment is registered. Under
[decision 0010](../decisions/0010-bars-carry-a-reopening-condition.md) the nulls in §2.3,
§3 and §5 are scoped to their designs: "not detected here" is not "does not exist," and the
independent-observation counts beside every table are there so that no verdict outruns its
instrument.
