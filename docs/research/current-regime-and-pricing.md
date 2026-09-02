# Current regime and pricing: which engines are cheap today, and which are expensive

**Question.** Every other page in this repository asks whether an engine works *on average*.
This one asks a different question: of the return engines this portfolio can reach — US
beta, international beta, emerging beta, a value tilt, momentum, trend, credit, duration,
cash and gold — **which are cheaply priced right now and which are expensive**, and does
"cheap" predict anything at all?

**Decision it informs.** Whether any weight in the current construction should move because
of the *level* of a market variable in August 2026, rather than because of its long-run
average. It does not set the equity share, does not forecast a market, and does not
supersede any page below.

**Out of scope.** The US CAPE level itself and the US/international split, which
[valuation and the allocation](valuation-and-the-allocation.md) owns; sleeve selection,
which [alternative sleeves](alternative-sleeves-audit.md) owns; and any moving-average or
trend timing rule, which [timing rules](timing-rules-on-the-equity-sleeve.md) owns.

`as of 2026-08-23`, with the priced inputs in §1 refreshed to `2026-08-31` (H.15 and FRED,
refetched 2026-09-02). Every measured figure regenerates from
[`studies/_current_pricing_tables.py`](../../research/src/portfolio_edge/studies/_current_pricing_tables.py),
run with `uv run python -m portfolio_edge.studies._current_pricing_tables`; the arithmetic
is pinned in `research/tests/unit/test_studies_current_pricing.py`. **Everything measured
here is `exploratory`**: no specification was frozen before the numbers were seen, no
experiment is registered, and nothing below may support a promoted claim.

---

## Conclusion

1. **The two things this portfolio does not own are the two things that are cheap, and the
   two things it does own are the two that are dear.** Long real yields sit at the top of
   their record — the thirty-year TIPS real yield of **2.99%** is above **99.8%** of its
   own history since 2010 — while US equity and corporate credit are both near the
   expensive extreme of theirs. That is an uncomfortable arrangement and it is *not* on its
   own a reason to trade, for the reason in point 4.
2. **Credit is the clearest extreme on the longest record available.** The Moody's Baa−Aaa
   quality spread — what an investor is paid for holding weaker corporate credit rather
   than the strongest — is **0.44 pp**, wider in **97.8% of the 1,202 months since
   1926** and wider in all but one of the **440 months since 1990**. Investment-grade OAS is
   80 bp and high yield 263 bp. It has never been cheaper to be a borrower in this record.
3. **The predictable part of the opportunity set is the part this portfolio has excluded.**
   Of twenty-seven conditioning relations tested, the only ones that survive both a Hodrick
   1B statistic and a positive out-of-sample record predict **bond and credit** returns, not
   equity returns. Nothing tested here predicts the equity premium out of sample.
4. **Nothing tested here predicts equity returns, and one relation shows exactly how a
   predictor fools you.** The term spread's five-year equity regression reports a Hodrick
   `t` of **2.32** and an in-sample `R**2` of 0.122 — and an out-of-sample `R**2` of
   **−0.175**. That is the same signature the CAPE regression carries. A large `t` on an
   overlapping long-horizon regression is not evidence until it has beaten a rolling mean
   on data its coefficients never saw.
5. **The real cash rate has no conditioning record, and the premise that it does is wrong.**
   Across six responses and two horizons its best out-of-sample `R**2` is **+0.007**. Its
   *level* is also less remarkable than it feels: a **+0.19 pp** ex-post real bill sits at
   the **45th** percentile of a century, not the top. It is only unusual against the
   post-2008 window, where the real bill averaged **−1.06 pp** and was positive in 64 of
   211 months.
6. **The value spread is wide and has narrowed sharply.** Cheap US stocks trade at **7.5x**
   the book-to-market of expensive ones once the ratio is moved to current prices, against
   a hundred-year median of **4.95x** — the **81st** percentile. Eighteen months ago it was
   near the 91st. It is a real state variable and its predictive content is **unresolved**:
   the fitted effect is 2.6 pp/yr per standard deviation against a design that could only
   have detected 7.2.
7. **Gold is the most expensive thing on this page relative to its own history**, at the
   **98.5th** percentile of the real price since 1975 and above both the January 1980 and
   August 2011 real peaks.
8. **Momentum and trend are not priced at all.** Neither has a valuation state variable, no
   source in this repository publishes one, and inventing one would be a search over
   definitions. `unpriced` is the honest label.
9. **What to do: nothing to the allocation.** Two negative decisions get firmer — do not
   open a credit sleeve at this spread, and do not open a gold sleeve at this price — and
   one contingent statement is added: if a defensive allocation is ever opened, the
   inflation-linked leg is the part that is cheap. See §5.

---

## 1. Where every priced input sits

Percentile means the share of that series' own history strictly below today's reading. It
is arithmetic on a sample. **It is not a forecast**, and §2 is where the forecasting claims
live.

### 1.1 US equity

Owned by [valuation and the allocation](valuation-and-the-allocation.md), which holds the
derivation, the four disagreeing CAPE readings and the buyback and concentration
adjustments. Repeated here only so the comparison in §3 has a row.

| Measure | Value | Percentile | Window |
| --- | ---: | ---: | --- |
| CAPE | 41.18 (`as of 2026-08-01`) | 0.989 | 1881–2026 |
| CAPE earnings yield | 2.43%/yr | 0.010 | 1881–2026 |
| Shiller excess CAPE yield | +0.97 pp | 0.187 | 1881–2026 |
| **TIPS excess CAPE yield** | **−0.01 pp** (`as of 2026-08-31`; +0.03 pp on the August average) | **0.000** | 2003–2026, fifth month at the floor |
| Forward earnings yield (FactSet fwd P/E 19.6, `as of 2026-08-28`) | ≈5.1%/yr | not computed | — |

The two excess-yield rows are the same construction with a different real rate and they
disagree by nearly a percentage point. The forward multiple disagrees with both. That
tension is unresolved and this repository cannot settle it.

### 1.2 International

| Market | CAPE | Source `as of` |
| --- | ---: | --- |
| United States | 35.82 | 2026-06-30 |
| Global ex-US | 21.02 | 2026-06-30 |
| Emerging markets | 19.36 | 2026-06-30 |

Siblis Research, read 2026-08-22, all three inside one methodology: a **1.70x** US premium
over developed ex-US and **1.85x** over EM.

**No percentile is available for that spread and this page will not invent one.** The only
long cross-country valuation panel in the cache — Jordà–Schularick–Taylor R6 — carries a
*dividend yield*, not a CAPE, and **ends in 2020**; its US-minus-panel log dividend-yield
spread reads −0.259 in 2020, the 19th percentile of 150 years. That describes 2020. Siblis
publishes no history this code can read. The relative-valuation question is therefore
**measured in level and unmeasured in percentile**, and [valuation and the
allocation](valuation-and-the-allocation.md) already records that the cross-country
relation is undetectable after 1990.

### 1.3 Real rates, the nominal curve, and cash

FRED and the Federal Reserve H.15 release, refetched 2026-09-02 for the 2026-08-31 close;
each percentile is taken over that series' own record, which for the TIPS series is short.
The 2-year note was not refetched and keeps its 2026-08-20 reading.

| Measure | Value | `as of` | Percentile | Window (n) | Median |
| --- | ---: | --- | ---: | --- | ---: |
| **30y TIPS real yield** | **2.99%** | 2026-08-31 | **0.998** | 2010-02…2026-08 (4,135) | 1.01% |
| **10y TIPS real yield** | **2.44%** | 2026-08-31 | **0.967** | 2003-01…2026-08 (5,920) | 1.05% |
| 10y nominal | 4.75% | 2026-08-31 | 0.435 | 1962–2026 | 5.40% |
| 30y nominal | 5.25% | 2026-08-31 | ≈0.47 | 1977–2026 | 5.42% |
| 2y nominal | 4.19% | 2026-08-20 | 0.447 | 1976–2026 (12,552) | 4.62% |
| 3m bill | 3.78% | 2026-08-31 | 0.462 | 1954–2026 | 4.10% |
| Fed funds effective | 3.63% | 2026-08-31 | 0.427 | 1954–2026 | 4.27% |
| 10y breakeven inflation | 2.35% | 2026-09-01 | 0.713 | 2003–2026 | 2.22% |
| Slope, 10y − 3m | +0.84 pp | 2026-08-31 | 0.312 | 1981–2026 | +1.57 pp |
| Slope, 10y − 2y | +0.56 pp | 2026-08-31 / 08-20 | ≈0.40 | 1976–2026 | +0.78 pp |
| Slope, 30y − 10y | +0.50 pp | 2026-08-31 | 0.638 | 1977–2026 | +0.30 pp |
| Real slope, 30y − 10y | +0.55 pp | 2026-08-31 | 0.495 | 2010–2026 | +0.56 pp |
| **Term premium, 10y, Kim–Wright** | **+0.84 pp** | 2026-08-14 | — | FRED `THREEFYTP10`, 1990–2026 | — |
| Term premium, 10y, ACM | ≈ +0.80 pp | 2026-08-13 | — | NY Fed, read from aggregators | — |

**Three readings.**

**Nominal yields are ordinary; real yields are extreme.** A 4.75% ten-year is the 44th
percentile of sixty-four years — unremarkable. The same maturity's *real* yield is the 97th
percentile of everything the TIPS market has ever printed, and the thirty-year real yield of
2.99% is above **99.8% of the 4,135 daily readings since 2010**. The difference is that
inflation compensation is priced near normal (2.35% breakeven, 71st percentile) while the
real component is not. **The percentile is short-windowed and the level is not**: 2.99% real
is also the best contractual real yield the US Treasury has offered in this record, and the
July 2026 ten-year TIPS auction cleared at a real yield of 2.438%, the highest since
October 2008 ([tipswatch](https://tipswatch.com/2026/07/23/10-year-tips-auction-gets-real-yield-of-2-438-a-great-result-for-investors/),
`as of 2026-07-23`).

**The curve is positive but flat by its own standards** — the 10y−3m slope of +0.84 pp is
the 31st percentile. The long end is the exception: 30y−10y at +0.50 pp is the 64th
percentile, so the extra term compensation available today is concentrated beyond ten years.

**The term premium is measured, by two independent decompositions, at about +0.8 pp.**
Kim–Wright reads +0.84% (Federal Reserve Board series on FRED, 2026-08-14) and ACM about
+0.80% (NY Fed, 2026-08-13, read from aggregators rather than the primary CSV, so medium
confidence). The two agree, and they are materially positive for the first time in about
five years, which says the +0.84 pp 10y−3m slope is roughly all term premium and roughly no
expected rate change. That is the expected excess return of a financed Treasury leg before
its costs, and it is the number
[defensive engines in the construction](defensive-engines-in-the-construction.md) prices a
stacked Treasury leg against.

### 1.4 Cash in real terms

| Measure | Value | `as of` | Percentile | Window |
| --- | ---: | --- | ---: | --- |
| Nominal 3m bill (monthly average) | 3.73% | 2026-07 | 0.591 | 1926–2026 |
| Trailing 12-month CPI inflation | 3.54% | 2026-07 | 0.657 | 1927–2026 |
| **Real bill, ex-post** (bill − trailing CPI) | **+0.19 pp** | 2026-07 | **0.446** | 1927–2026 (1,190) |
| **Real bill, ex-ante** (bill − 10y breakeven) | **+1.47 pp** | 2026-08-31 | **0.784** | 2003–2026 |

The BLS's own July 2026 print (released 2026-08-12) is 3.4% headline and 2.5% core, not
seasonally adjusted; the 3.54% above is the module's computation from the FRED index and is
the figure the real bill uses. The two conventions disagree by 1.3 pp because realised
inflation over the last year is well above what the bond market prices for the next ten
(2.35%). Both are
reported because neither is definitive: the ex-post measure is the one with a century of
history, and the ex-ante measure is the one an investor actually chooses against.

**Against the post-2008 record cash is well paid; against the century it is ordinary.**
Since 2009 the ex-post real bill averaged **−1.06 pp** and was positive in **64 of 211
months**; today's +0.19 pp is the 74th percentile of that window and the 45th of the full
one. The sentence "a positive real cash rate changes the whole opportunity set" is true
about the last fifteen years and false about the last hundred.

### 1.5 Credit

| Measure | Value | `as of` | Percentile | Window (n) | Since 1990 | Since 2010 |
| --- | ---: | --- | ---: | --- | ---: | ---: |
| IG corporate OAS | 0.80 pp | 2026-08-31 | 0.236 | **2023-08…2026-08 only (784)** | — | — |
| High-yield OAS | 2.63 pp | 2026-08-31 | 0.015 | **2023-08…2026-08 only** | — | — |
| **Moody's Baa − Aaa (quality)** | **0.44 pp** | 2026-08 | **0.022** | 1926-07…2026-08 (1,202) | **0.002** | **0.005** |
| Moody's Baa − 10y (default) | 1.64 pp | 2026-08 | 0.478 | 1926-07…2026-08 (1,202) | — | 0.120 |
| Moody's Baa − 10y, daily | 1.64 pp | 2026-08-20 | 0.144 | 1986-01…2026-08 (10,159) | 0.143 | 0.081 |

**A data-contract finding first, because it decides what can be said.** ICE BofA's
option-adjusted spreads on FRED are **truncated to three years at source**, exactly as the
total-return siblings are: measured 2026-08-23, `BAMLC0A0CM` and `BAMLH0A0HYM2` return 786
and 787 daily rows beginning 2023-08-22. **No percentile of a current OAS against its own
history can be computed from FRED**, and the "35th percentile" in that row means only
"35th percentile of the last three years", which is not a useful statement. The Moody's
series, which begin in 1919, are the long-history substitute.

**The two long measures disagree, and the disagreement is the finding.** The *quality*
spread — Baa yield less Aaa yield, both long corporate — is at the **2.2nd percentile of a
century** and has been this narrow in one month since 1990. The *default* spread — Baa
less the ten-year Treasury — is at the 46th percentile of the same century. They differ
because Baa−10y is not a clean credit spread: Moody's Baa is a long-maturity corporate
yield, so subtracting a ten-year Treasury leaves a **term premium mixed into the credit
premium**, which is the same confound [alternative sleeves](alternative-sleeves-audit.md)
documents for the unhedged corporate leg. On the shorter windows where the two can be
compared the story converges: Baa−10y is at the **12th percentile since 2010** and the daily
series at the **14th since 1986**.

**Read together with the 80 bp OAS, all four measures say the same thing: an investor is
being paid unusually little for corporate credit risk right now.**

### 1.6 The value spread

The valuation gap between cheap and expensive stocks — how much more book value a dollar
buys in the cheap half of the market than in the expensive half. Ken French's own
value-weighted `BE/ME` averages for the six size × book-to-market portfolios, expressed as
a log ratio and averaged across the big-cap and small-cap pairs.

| Measure | Log spread | Cheap/expensive ratio | Percentile of 100 years |
| --- | ---: | ---: | ---: |
| Big caps | 2.286 | 9.83x | 0.97 |
| Small caps | 2.109 | 8.24x | 0.84 |
| Combined, at formation (ME dated 2024-12) | 2.198 | 9.00x | 0.91 |
| **Combined, marked to market (2026-06)** | **2.021** | **7.54x** | **0.81** |

Hundred-year median: **4.95x**.

**The stale-price problem is the reason two rows exist.** French's `BE/ME` is fixed at
formation: book from the prior fiscal year over market equity at the prior December. The
file is built from the 202606 CRSP database and its last row is 2026-06, but that row
belongs to the **June-2025** formation, whose market equity is dated **December 2024** — so
the raw spread is twenty months old on prices. Scaling each side by its own cumulative
return since then restores the price leg: big-cap value returned **+62.3%** against big-cap
growth's **+24.1%** over that stretch, which narrows the spread by 0.27 log units. Using
total rather than price returns biases this **downward**, because the cheap side pays the
larger dividend, so 7.54x is a floor rather than a point estimate.

**The reading: wide, and narrower than it was.** At the 81st percentile the cheap half of
the market is still priced at a larger discount than in four fifths of the last century.
But the spread has spent eighteen months closing while the tilt delivered, and it is no
longer near the 2022 extreme.

### 1.7 Gold

| Measure | Value | `as of` | Percentile | Window |
| --- | ---: | --- | ---: | --- |
| Real gold price, LBMA PM fix deflated by CPI | **$4,027/oz** in 2026-07 money | 2026-07 | **0.985** | 1975-01…2026-07 (618) |

For scale: the January 1980 peak was **$2,786** and the August 2011 peak **$2,669** in the
same money, against a period median of **$1,170**. Spot was $4,457 on 2026-08-31, about 20%
below the futures record of $5,542 set on 2026-01-29 and still higher than any real reading
in the module's monthly series. Gold has no cash flow and therefore no valuation ratio; the
real price is the only state variable available, and it is near the top of its record.

### 1.8 What is not priced

**Momentum and trend have no valuation state variable.** French publishes no `BE/ME` for
the momentum portfolios, AQR's TSMOM series carries no valuation measure, and there is no
accepted one in the literature this repository has read. Constructing one would be a search
over definitions with no pre-registration, which is how a spurious conditioning rule gets
made. They are `unpriced`, and that is a property of the engines, not a gap in the data.

One arithmetic note that is not a forecast: a fully collateralised futures programme earns
the bill rate on its collateral, so a 3.78% bill adds roughly 3.7 pp/yr to a managed-futures
sleeve's total return that a 0.05% bill did not. **For the stacked wrapper this nets to
approximately nothing**, because the same rate is what the wrapper pays to finance its
equity exposure. The level of rates is close to neutral for the construction actually held.

---

## 2. What each conditioning variable has actually predicted

Monthly, Goyal–Welch 1926-07…2025-12 (the workbook's return columns are not spliced
forward). Slopes are reported as **pp/yr of response per one standard deviation of the
predictor**, so predictors in different units compare. **`MDE` is the smallest slope this
design would have detected**, at 5% two-sided size and 80% power — an estimate below it is
one the study could not tell apart from zero, in either direction. `t` is Hodrick 1B, which
does not let the number of estimated quantities grow with the horizon; the Newey-West
statistic is kept beside it because the gap between them is the point.

| Predictor | Response | Horizon | Indep. obs | Slope /sd | **MDE** | `t` NW | **`t` Hod** | `R**2` | **OOS `R**2`** | Verdict |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| **Term spread** | long govt excess | 1 yr | 98.5 | **+3.18** | 2.84 | 4.98 | **3.14** | 0.142 | **+0.127** | **supported** |
| **Default spread** | long govt excess | 5 yr | 18.9 | **+1.48** | 1.34 | 3.27 | **3.09** | 0.143 | **+0.136** | **supported** |
| **Default spread** | credit excess | 1 yr | 98.5 | +1.30 | 1.98 | 2.89 | 1.85 | 0.108 | **+0.107** | suggestive |
| **Default spread** | credit excess | 5 yr | 18.9 | +0.62 | 1.02 | 3.92 | 1.69 | 0.256 | **+0.154** | suggestive |
| Quality spread | credit excess | 5 yr | 18.9 | +0.47 | 0.97 | 2.68 | 1.35 | 0.147 | +0.117 | suggestive |
| Quality spread | credit excess | 1 yr | 98.5 | +0.99 | 2.07 | 2.07 | 1.35 | 0.062 | +0.059 | suggestive |
| Quality spread | long govt excess | 5 yr | 18.9 | +1.33 | 1.37 | 2.98 | 2.72 | 0.115 | +0.100 | suggestive |
| Term spread | long govt excess | 5 yr | 18.9 | +1.26 | 1.70 | 2.67 | 2.07 | 0.103 | +0.057 | suggestive |
| Real bill | long govt excess | 5 yr | 18.7 | +0.80 | 1.29 | 1.93 | 1.75 | 0.042 | +0.007 | suggestive |
| **Term spread** | **equity excess** | 5 yr | 18.9 | +2.87 | 3.48 | 2.33 | **2.32** | 0.122 | **−0.175** | **unresolved** |
| Term spread | equity excess | 1 yr | 98.5 | +2.06 | 4.75 | 1.45 | 1.22 | 0.010 | −0.001 | unresolved |
| Quality spread | equity excess | 5 yr | 18.9 | +1.26 | 5.64 | 1.51 | 0.63 | 0.024 | −0.752 | unresolved |
| Default spread | equity excess | 5 yr | 18.9 | +0.58 | 5.64 | 0.58 | 0.29 | 0.005 | −0.820 | unresolved |
| Real bill | equity excess | 5 yr | 18.7 | −1.84 | 5.12 | −1.79 | −1.01 | 0.052 | −0.047 | unresolved |
| Real bill | credit excess | 5 yr | 18.7 | +0.20 | 0.84 | 1.01 | 0.68 | 0.028 | −0.142 | unresolved |

Twenty-four macro rows were run; the fifteen above are the ones that carry a reading. The
full table prints from the module.

And the value spread, on annual data where a one-year horizon needs no overlap correction
at all. Predictor: the spread at the June formation date. Response: the subsequent Fama–French
`HML` return, July to June.

| Predictor | Response | Horizon | Indep. obs | Slope /sd | **MDE** | `t` NW | **`t` Hod** | `R**2` | **OOS `R**2`** | Verdict |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| US value spread | HML | 1 yr | 98.0 | +2.60 | 7.18 | 1.33 | 1.01 | 0.031 | **+0.033** | unresolved |
| US value spread | HML | 5 yr | 18.8 | +1.42 | 5.56 | 1.49 | 0.71 | 0.075 | **+0.080** | unresolved |
| US value spread | HML | 10 yr | 8.9 | +1.19 | 3.59 | 2.67 | 0.93 | 0.132 | +0.008 | unresolved |

**Five readings, and they are the substance of this page.**

**Credit spreads predict credit returns and nothing else.** The default spread's
relationship to subsequent corporate-over-government excess return is the most reliable
thing in either table: positive out-of-sample at both horizons, `R**2` of 0.256 in sample
at five years. Against equity returns the same predictor is inert — `t` of 0.29, an
out-of-sample `R**2` of **−0.82**. A credit spread is a signal about credit, not about
risk appetite generally.

**The term spread predicts bond returns, with the highest statistic on the page.** Hodrick
`t` of 3.14 and an out-of-sample `R**2` of +0.127 at one year. It is also the row that
demonstrates the failure mode: the *same* predictor against *equity* at five years reports
`t` = 2.32 in sample and loses to a rolling mean out of sample by 17.5%. **A statistic and a
record are different claims and this table shows them disagreeing inside one predictor.**

**The real cash rate is noise.** Three responses at two horizons, best out-of-sample `R**2`
**+0.007**, best Hodrick `t` 1.75, and against equity the sign is negative and unresolved.
It collects a `suggestive` grade on one cell only because the grader's out-of-sample gate
is "positive", and +0.007 is a rounding error against a rolling mean rather than a result.
The hypothesis that a real cash rate is a well-evidenced conditioning variable is not
supported on this panel. It is a fact about the price of cash, not a signal about anything
else.

**The value spread is the most interesting `unresolved` here.** Its Hodrick statistics are
weak — 1.01, 0.71, 0.93 — and every point estimate is far below its own MDE. But its
out-of-sample `R**2` is **positive at every horizon and every start**, which is exactly what
CAPE fails to do. Directionally right, economically plausible, and **not resolvable on a
hundred years of annual data**. Anyone sizing a tilt on it is sizing on faith.

**Nothing here should be read as a promotion, and the multiple-testing arithmetic says so.**
Twenty-seven relations were tested. At a 5% two-sided size about 1.4 spurious rejections are
expected by chance, and two rows reach `|t| ≥ 3.0` — the
Harvey–Liu–Zhu hurdle this repository uses elsewhere. Both are bond-return relations, they
share a response, and their predictors are related. **Two survivors out of twenty-seven,
concentrated in one response, is weak-to-moderate evidence and not a discovery.**

---

## 3. The ranking, with the two claims kept apart

**Column one is a measurement. Column two is not a claim this page makes.** "Cheap by
percentile" says where a price sits inside its own history. "Expected to deliver" is a
forecast, and §2 shows that the forecasting record behind almost all of these is poor. The
right-hand column therefore records only whether a *conditioning relation with an
out-of-sample record* exists for that engine — not what it forecasts.

| Rank | Engine | Priced by | Reading | Does conditioning on it have an OOS record? |
| ---: | --- | --- | --- | --- |
| 1 | **Long inflation-linked duration** | 30y TIPS real yield 2.99% | **cheapest** — 99.8th pct since 2010 | Partly: term and default spreads predict *nominal* long-bond excess (OOS +0.127, +0.136). Not tested on TIPS. |
| 2 | 10y inflation-linked duration | 10y TIPS real yield 2.44% | cheap — 97th pct since 2003 | as above |
| 3 | **US value tilt** | value spread 7.54x | wide — 81st pct of 100 yr, narrowing | Yes, but **unresolved**: OOS +0.033/+0.080, estimate one third of MDE |
| 4 | Cash | ex-ante real bill +1.47 pp | well paid vs 2003–2026 (78th pct); ordinary vs 1927–2026 (45th) | **No.** Best OOS +0.007 across six cells |
| 5 | Emerging beta | CAPE 19.4 vs US 35.8 | cheap in level; percentile **unavailable**; AQR reads EM's own CAPE at the 98th pct since 2001 | Not detectable after 1990 ([valuation](valuation-and-the-allocation.md)) |
| 6 | International developed beta | CAPE 21.0 vs US 35.8 | cheap in level; percentile **unavailable** | as above |
| 7 | Nominal duration | 10y 4.75%, 30y 5.25%; term premium ≈ +0.8 pp | ordinary — 44th and 47th pct | **Yes**, the best on the page (term spread, OOS +0.127) |
| = | **Momentum** | — | **unpriced** | no state variable exists |
| = | **Trend** | — | **unpriced** | no state variable exists |
| 8 | US equity beta | CAPE 41.18; TIPS excess CAPE yield −0.01 pp | expensive — 98.9th pct on CAPE, 0th pct on the TIPS-based excess yield since 2003 | **No.** OOS `R**2` −0.44 at ten years ([valuation](valuation-and-the-allocation.md)) |
| 9 | **Gold** | real price $4,027 | **expensive** — 98.5th pct since 1975, above the 1980 and 2011 real peaks | none tested |
| 10 | **Credit** | IG OAS 80 bp; Baa−Aaa 0.44 pp | **most expensive on the longest record** — 2.2nd pct of a century, 0.2nd since 1990 | **Yes**, the second-best on the page (OOS +0.107/+0.154) |

**Credit is last and it is the only entry where "expensive" and "has a conditioning record"
coincide.** For every other engine, either the price is not extreme or the conditioning
evidence is absent. That coincidence is what makes §5's one firm conclusion possible.

---

## 4. Three ways this ranking could mislead

**A short window makes an extreme look more extreme.** The TIPS real yield's 99.8th
percentile is taken over sixteen years, all of them inside the era of quantitative easing.
Before 2003 there is no TIPS market to measure. The *level* — a 2.99% contractual real
yield — carries more information than the percentile does, and the percentile should not be
read as "once in two hundred years."

**A percentile is not a probability.** Nineteen of 1,748 months have equalled today's CAPE
and eighteen of them are one episode; about 2% of the 1,202 months since 1926 have
carried a narrower quality spread, and they are not spread evenly across the century.
A count of past occurrences drawn from two or three episodes is a description, not a
frequency, and [valuation and the allocation](valuation-and-the-allocation.md) makes the same
point about the CAPE drawdown evidence.

**Revised history flatters every backward-looking rule here.** FRED, Goyal–Welch and Ken
French all rebuild their full history on each release and publish no vintage archive. Every
percentile and every out-of-sample `R**2` above uses a revised series that no historical
investor held. That biases the conditional results **in their own favour**, and most of them
still fail.

---

## 5. What should change because of the level

The bar is high, and it should be. This session already established that conditioning the
equity share on CAPE loses before costs, that the one valuation rule with a real gross edge
is eaten by tax, and that timing rules on the equity sleeve fail deflation. So the default
answer to "should this level move a weight" is no.

**The equity allocation: no change.** Nothing in §2 predicts equity returns out of sample.
The six-line construction — stacked equity + managed futures ~25%, US total market ~25%, US
value ~15%, international core ~25%, international momentum 5%, emerging value 5% — is
unaffected by anything measured here. The existing advice in
[valuation and the allocation](valuation-and-the-allocation.md) stands unchanged: widen the
drawdown assumption, direct new contributions rather than realised gains toward the
international side, and do not run a valuation-conditional weighting rule in a taxable
account.

**Credit: do not open the sleeve at this spread.** This is the one place where the level
changes a decision, and it strengthens a caution
[alternative sleeves](alternative-sleeves-audit.md) already raised. Three things now line up:

- duration-hedged credit is the largest *candidate* addition on that page, at a measured
  **+2.13%/yr** over 1,062 months at 4.12% volatility;
- that premium was earned across the full range of spread regimes, and the current gross
  spread is **80 bp** with the century-long quality spread at its **2.2nd percentile** and
  the tightest reading but one in 440 months;
- **credit is the one engine here whose conditioning variable has a positive out-of-sample
  record** — a wider default spread has bought more subsequent credit excess return, OOS
  `R**2` +0.107 at one year and +0.154 at five.

The consequence is not that the engine is refuted. It is that **the one place the evidence
says entry price matters is also the place the entry price is worst**, and a 14–24 bp
wrapper plus expected default loss is being charged against 80 bp of gross spread. Defer,
size to the spread, or build in over time. A specific, falsifiable reopening condition:
**revisit when the Moody's Baa−Aaa quality spread returns to its century median of 0.90 pp**,
which is a level, not a forecast, and can be checked from the same series in one command.

**Gold: do not open the sleeve at this price.** [Alternative sleeves](alternative-sleeves-audit.md)
already found gold return-dominated at examined weights on a +1.75%/yr measured excess return
with a −91% drawdown. The real price at the 98.5th percentile of fifty-one years, above both
prior real peaks, does not make that case better.

**The value tilt: keep it, do not enlarge it.** The spread is genuinely wide and the
direction of the evidence is favourable. It is also `unresolved` at a factor of nearly three
below its own detection floor, and it has already closed by 0.27 log units in eighteen
months. The 15% US value and 5% emerging value weights need no adjustment from this page.

**If a defensive allocation is ever opened, the inflation-linked leg is the cheap part.**
The portfolio holds no bonds, and [the recommendation](portfolio-recommendation.md) is
explicit that the defensive allocation should be decided by the withdrawal path and the
ability to persist, not by a return forecast. That does not change. What changes is the
price of the instrument *if* that decision is ever made: a 30-year TIPS at 2.99% real is a
contractual line in the certainty class this repository reserves for statutes, and it is
the best such line in the record. Long-horizon, contributions of 5–15%/yr, no near-term
withdrawal need — this investor has no current use for it unless a stated drawdown
tolerance binds, which is the conditional rule [valuation and the
allocation](valuation-and-the-allocation.md) §6.2 states. The note lapses when the 30-year
real yield falls below about 2.0%.

**Cash: no change, and the framing was wrong.** A +0.19 pp ex-post real bill is the 45th
percentile of a century. It is unusual only against the post-2008 window. And it predicts
nothing.

---

## 6. Provenance, and what could not be measured

Every FRED series is refetched on each run and its `sha256` and retrieval timestamp print
at the top of the module's output. The Goyal–Welch workbook is `sha256:1e4b6527…`, retrieved
2026-08-17, data through 2025-12. Ken French's `6_Portfolios_2x3` is `sha256:06108313…`,
refetched 2026-08-23 and byte-identical, built from the 202606 CRSP database. The LBMA PM
fix was refetched 2026-08-23.

**A hash identifies the bytes used. It does not make a revised series point-in-time**, and
none of these sources publishes a vintage archive this code can read.

Four things could not be measured and are recorded as gaps, not as excuses.

- **A percentile for any current OAS.** ICE BofA's spread series on FRED are capped at three
  years at source, the same cap the total-return siblings carry. The Moody's quality and
  default spreads are the long-history substitutes and they are not the same instrument.
- **A percentile for the US-versus-international valuation gap.** The only long panel in the
  cache ends in 2020 and measures a dividend yield, not a CAPE.
- **A term-premium decomposition from the cache.** The Kim–Wright series (`THREEFYTP10`)
  and the ACM series are published and are quoted in §1.3 from outside the cache; neither is
  yet fetched and hashed by the module, and the ACM figure is an aggregator read.
- **A value spread outside the US.** French's developed-ex-US and emerging portfolio files
  carry returns, firm counts and market caps but **no `BE/ME` block**, so the same
  construction cannot be run for the international core or the emerging value sleeve. That
  is the single most useful missing input on this page, because it is where two of the
  portfolio's six lines live.

The most informative next test, if this page is ever revisited: obtain a `BE/ME` or
book-to-price series for developed ex-US and emerging markets and repeat §1.6 and §2 on
them. Everything else here is either measured or shown to be unmeasurable from committed
sources.
