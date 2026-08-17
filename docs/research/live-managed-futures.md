# Live managed futures: what the funds actually paid, and what the vendor index overstated

**Question.** Every trend figure in this repository comes from AQR's published TSMOM series,
which states no fee, transaction-cost, slippage or financing basis anywhere. What did real
managed-futures funds pay their investors over the same months, and how big is the gap?

**Decision it informs.** Whether [Experiment 011](capital-efficiency-and-breadth.md)'s
`unresolved` verdict can be lifted by changing the instrument, and whether the **7.7 pp/yr**
survivorship-plus-backfill-plus-cost haircut this repository applies to the vendor series is
the right size.

**Out of scope.** Whether to hold a trend sleeve — that is
[decision 0004](../decisions/0004-no-sleeve-promoted.md), and nothing here changes it. Which
fund to buy — that is [the recommendation](portfolio-recommendation.md).

`as of 2026-08-16`. [Experiment 012](../../research/experiments/exp_012_live_trend.yaml),
`exploratory`, result `unresolved`.

---

## Conclusion

1. **The vendor series did not overstate what fund investors earned. It understated it.**
   Over the 78 months both series exist, AQR's TSMOM index returned **+1.95%/yr** excess of
   cash at a Sharpe of **0.141**; an equal-weight index of **46 live managed-futures funds,
   net of their own fees**, returned **+2.84%/yr** at a Sharpe of **0.329**. Regressing the
   vendor series on the live one gives an alpha of **−1.36 pp/yr** (HAC *t* = −0.39).
2. **The 7.7 pp/yr haircut is outside the interval on the only window that can measure it.**
   At matched volatility the vendor series earned **−2.62 pp/yr** relative to the funds,
   95% interval **[−10.91, +5.68]**. A +7.7 gap sits above that interval. **This does not
   refute the bound where it matters** — the bound is applied to 1985–2011, where no fund
   return exists — but on the only live evidence available it points the other way.
3. **The overlay result is still `unresolved`, and the reason has moved.** The
   matched-volatility gap for a 50% live-trend overlay against the leverage-matched control
   is **+1.27 pp/yr** `[−2.62, +4.95]` against an **MDE₈₀ of 4.76 pp/yr**. Experiment 011
   was unresolved because of its *series*; Experiment 012 is unresolved because of its
   *window*. **Replacing the instrument did not settle it and cannot, at 78 months.**
4. **The break-even haircut collapses from 9.57 pp/yr to 2.54.** That is a fact about
   2019–2025, in which trend earned a quarter of its long-run mean, not about the leg's
   construction.
5. **Attrition is severe and every figure is a lower bound.** Of 25 funds filing at the
   window's open, **13 (52%) stopped filing inside 6.5 years**, including a $1.78bn fund.

---

## 1. The census: what is in it, and what can never be

Screened over the **union** of the 2019Q4 and 2025Q4 SEC N-PORT structured data sets —
14,742 fund series — on **series names only**, with no return read while screening. The
mandate and exclusion patterns are [Experiment 008](trend-marginal-value.md)'s, reused
verbatim because they were frozen before any fund return was downloaded.

| Step | Series |
| --- | ---: |
| Union of both censuses | 14,742 |
| Series name matches the managed-futures mandate pattern | 60 |
| less rejected by the frozen exclusion pattern | −9 |
| less rejected as not a diversified futures programme, each named with its reason | −5 |
| **Admitted** | **46** |
| of which at least one filed Item B.5 month exists | 46 |

Unlike Experiment 008 there is **no exchange-listing test, no asset floor, no expense-ratio
cap and no inception cutoff**. Experiment 008 audited a shelf you could buy; this measures
what the mandate delivered, so screening down to the survivors of a size test would
reintroduce the selection the exercise exists to remove. Mutual funds, tiny funds and dead
funds are all in.

### Two survivorship holes, and the second is worse

- **Public N-PORT filings begin in 2019.** A managed-futures fund that closed before 2019Q4
  is invisible to both censuses.
- **A fund that both launched after 2019Q4 and closed before 2025Q4 is in *neither*
  census**, so it is missing from the index entirely. Unlike the first hole this one deletes
  funds from *inside* the window. Closing it needs the intermediate quarterly censuses,
  which this experiment does not read; that is the cheapest single improvement available.

Both holes remove funds that failed, so **both flatter every return below**. A live index
that is too high makes the vendor-less-live difference too *low* — the direction that would
hide the gap this experiment went looking for.

Two further limits on the count itself. A diversified futures programme whose name carries
none of the mandate tokens is not in the census at all. And the frozen exclusion pattern has
one known defect, recorded rather than fixed: it removes the **Credit Suisse Managed Futures
Strategy Fund** ($343m) because the *sponsor's* name contains "credit". Editing the pattern
after seeing what it caught would destroy the provenance that makes reusing it worthwhile.

### Attrition, 2019-07 to 2025-12 — a lower bound, twice over

| | |
| --- | ---: |
| Funds filing at the window's open | 25 |
| Of those, funds that stopped filing before the window closed | **13 (52%)** |
| Funds whose first filed month is after 2020-01 | 21 |

The five largest to stop: **ASG Managed Futures Strategy Fund** ($1.78bn, last filed
2023-03), Equinox IPM Systematic Macro ($316m, 2019-12), CTIVP–AQR Managed Futures ($266m,
2020-03), JNL/AQR Managed Futures ($134m, 2021-03), 361 Managed Futures ($131m, 2021-01).
Only three of the thirteen carry an `isFinalFiling` flag, so "stopped filing" is the
observable and "liquidated" is an inference.

---

## 2. The live index

Equal weight across the funds that filed a return **for that month**. A fund that died
contributes until it died; a fund that launched contributes from launch; nothing is
backfilled. That is the property a CTA peer-group index does not have. Between **18 and 33
funds** report in any month of the window.

Annualised, excess of the Ken French one-month bill, 78 months 2019-07…2025-12:

| Series | excess | volatility | Sharpe | corr. to equity | corr. to AQR |
| --- | ---: | ---: | ---: | ---: | ---: |
| **Live managed futures, net of fees** | **+2.84%** | 8.64% | **0.329** | **−0.109** | +0.724 |
| AQR TSMOM, vendor, gross of its own costs | +1.95% | 13.86% | 0.141 | −0.340 | 1.00 |
| US equity `Mkt-RF` | +13.17% | 17.20% | 0.766 | 1.00 | — |

**The index is not a diversification artefact.** The **median individual fund** with at
least 36 months returned **+2.82%/yr** at a Sharpe of **0.280** — essentially the index's
mean, at a higher volatility. The index's advantage is lower volatility, not a higher
return.

The equity correlation of −0.109 is the mechanism the sleeve is supposed to supply, and it
held: over the 2022 equity drawdown, 2022-01…2022-09, US equity compounded **−25.3%** while
the live net index compounded **+26.4%** (the vendor series, +34.2%).

### Robustness, on subsets defined by the census and never by a return

| Arm | funds | excess | vol | Sharpe | vendor − live, vol-matched |
| --- | ---: | ---: | ---: | ---: | ---: |
| **Every admitted fund (headline)** | 46 | +2.84% | 8.64% | 0.329 | **−2.62 pp/yr** |
| Excluding the five funds run by the vendor itself | 41 | +1.99% | 8.68% | 0.230 | −1.23 |
| Balanced panel: funds filing every month | 11 | +2.89% | 9.64% | 0.300 | −2.21 |
| Funds reaching $250m of net assets | 16 | +2.97% | 10.41% | 0.285 | −2.00 |
| Dropping two funds with implausible cross-class dispersion | 44 | +3.43% | 8.62% | 0.398 | −3.57 |

The second arm matters most: **AQR authors the comparator series and also runs five of the
funds in the index**, so the headline comparison is not fully independent. Removing them
cuts the live Sharpe from 0.329 to 0.230 — still above the vendor's 0.141 — and shrinks the
matched-volatility difference from −2.62 to −1.23 pp/yr. It does not change the sign.

The last arm is a caution rather than a result: two funds (Virtus Rampart Multi-Asset Trend,
Virtus AlphaSimplex Managed Futures Strategy) show cross-share-class return dispersion of
**69 and 41 pp/yr**, against a median of **1.10** across the 28 multi-class funds. That is
almost certainly a filing artefact rather than 40 percentage points of fee. **They are kept
in**, because dropping them makes the live index better and the conservative choice is the
one that does not.

---

## 3. The decisive comparison: AQR TSMOM regressed on the live funds

`AQR_t = alpha + beta · live_t + e_t`, 78 monthly observations, Newey–West with 3 lags.

| | estimate | std. error | |
| --- | ---: | ---: | --- |
| **alpha** | **−1.36 pp/yr** | 3.51 | *t* = −0.39, *p* = 0.70 |
| **beta** | **+1.161** | 0.156 | *t* = +1.04 against 1 |
| R² | 0.524 | | residual volatility 9.56%/yr |

| Difference, vendor less live | estimate | 95% interval |
| --- | ---: | --- |
| Raw | −0.90 pp/yr | [−7.87, +6.08] |
| **At matched volatility** | **−2.62 pp/yr** | **[−10.91, +5.68]** |

**Read the interval, not the point estimate.** The instrument cannot distinguish −2.6 from
zero. What it *can* do is exclude +7.7: the repository's standing CTA bias bound sits above
the upper end of both intervals. On these 78 months, a 7.7 pp/yr haircut to the vendor
series is not a conservatism, it is a misstatement.

**Three things this does not license.**

- **It is not a measurement of the pre-2019 period, which is where the haircut does its
  work.** The vendor series earned **+16.09%/yr at a Sharpe of 1.343 over 1985–2011**,
  **+4.17% at 0.315 over 2012–2025**, and **+1.95% at 0.141 over this window**. The 7.7
  pp/yr bound is applied to the long-window mean, and no fund return exists to test it
  there. This experiment measures the gap only where the gap is smallest.
- **The 7.7 pp/yr figure was never a claim about AQR's index against funds.** It bounds
  survivorship and backfill in *hedge-fund CTA databases*, whose fee load and reporting
  regime are different. Transferring it to a registered fund is the error Experiment 008
  was written to correct, and this result is consistent with that correction rather than a
  surprise against it.
- **It does not clear the vendor series.** AQR still states no cost basis, still
  reconstructs its full history on every update, and still shows a **12.11 pp/yr** pre- to
  post-publication decay. What has been ruled out is one specific explanation — that the
  series flatters relative to what funds delivered — on one specific window.

---

## 4. The overlay, re-run with the live leg

Same base portfolios, same weights, same leverage-matched control and same
matched-volatility statistic as Experiment 011. The trend leg carries a **zero modelled
fee**, and that is arithmetic rather than optimism: Item B.5 has already deducted the fund's
fee, its trading costs, its slippage and its roll. Experiment 011 charged 1.45%/yr to a
series that had never paid one. The borrow spread of 0.59% is charged to the levered
controls on exactly the same terms as to the overlay.

78 months, 2019-07…2025-12, net:

| Portfolio | geometric | volatility | Sharpe | max DD | under water |
| --- | ---: | ---: | ---: | ---: | ---: |
| equity only, 1.00× | 15.28% | 17.20% | 0.766 | −24.8% | 23 mo |
| **equity + 50% live trend** | **16.58%** | 17.27% | **0.828** | **−20.8%** | **14 mo** |
| equity levered 1.35× | 18.97% | 23.21% | 0.757 | −32.9% | 25 mo |
| equity levered 1.50× | 20.45% | 25.79% | 0.754 | −36.2% | 25 mo |

| Matched-volatility gap | estimate | 95% bootstrap interval | MDE₈₀ | |
| --- | ---: | --- | ---: | --- |
| vs `equity_levered_150` (primary) | +1.27 pp/yr | [−2.62, +4.95] | **4.76** | **below the resolution** |
| vs `equity_only` (secondary) | +1.07 pp/yr | [−2.86, +4.77] | **4.76** | **below the resolution** |

**The two benchmarks answer different questions and are never combined.**

**This is `unresolved`, and it could not have been anything else.** The gap is a quarter of
the smallest effect 78 months can detect at 80% power. Experiment 011 had 485 months and an
MDE₈₀ of 2.82 pp/yr; six years of N-PORT gives 4.76. Trading a contaminated instrument for a
clean but blunt one is the whole trade this experiment made, and the trade did not produce
an answer.

The break-even haircut on the live leg is **2.54 pp/yr** against the levered control and
**2.14** against the unlevered, against Experiment 011's 9.57 and 9.16. That is not a
statement about the leg: the sweep is linear in the sleeve's mean, and the live window's
mean is 2.84% where the 1985–2025 vendor mean is 12.07%.

---

## Verified, assumed, open

**Verified.** The census counts, the attrition of the opening cohort, the index's moments,
the regression and both differences, all from
[Experiment 012](../../research/experiments/exp_012_live_trend.yaml) against hash-pinned
French and AQR files and the two committed N-PORT censuses. The overlay arithmetic is
Experiment 011's code, imported rather than reimplemented, so the two results are produced
by the same functions.

**Assumed.** That Item B.5 means the same thing across 46 filers. It is **unaudited**, and
Form N-PORT General Instruction G lets each filer use its own internal methodology. The
repository's cross-source check returned an HTTP error for **all 44 US, all 25 ex-US and
all 109 corrected-frame tickers**, so **Item B.5 is the sole measurement of every fund return here** and no
independent corroboration exists ([evidence base](evidence-base.md)). Also assumed: that the
equal-weight mean across a fund's share classes is the right representative, and that
EDGAR's series-filtered filing feed reaches back to a fund's first N-PORT filing — it does
not always, and DBMF is the case in hand: it launched 2019-05 and its feed begins 2021-07.

**Open.**

1. **The pre-2019 gap is unmeasured and unmeasurable from this source.** It is where the
   7.7 pp/yr haircut is actually applied, and nothing here reaches it.
2. **The within-window survivorship hole is closable** by reading the intermediate quarterly
   N-PORT censuses. That is the cheapest improvement available and it would tighten every
   attrition figure on this page.
3. **The index is equal-weight across funds, not across dollars.** It is what the average
   managed-futures *fund* delivered, not what the average managed-futures *dollar* earned.
   N-PORT gives net assets at two dates only.
4. **Pretax everywhere**, and managed futures are the worst case for that omission.

---

## Consequence for this repository

1. **The 7.7 pp/yr CTA bias haircut may no longer be quoted as though it applied to the AQR
   TSMOM series against live funds.** Where it appears in
   [capital efficiency and breadth](capital-efficiency-and-breadth.md) it must carry this
   measurement beside it: on the only window where the comparison is possible, the
   vendor-less-live difference is **−2.62 pp/yr with a 95% interval of [−10.91, +5.68]**.
2. **Experiment 011's `unresolved` verdict stands, but its stated reason is superseded.**
   The verdict was attributed to the vendor series being unmeasurable. It is measurable, and
   over the measurable window it is not the problem. The binding constraint is the length of
   any window on which live fund data exists.
3. **A trend sleeve remains a risk-reduction claim, not a return claim.** The live evidence
   supports the correlation (−0.109, and +26.4% through a −25.3% equity drawdown) and cannot
   resolve the mean.
4. **No sleeve is promoted and [decision 0004](../decisions/0004-no-sleeve-promoted.md)
   stands.** Nothing here is confirmatory: the specification was written after Experiment
   011's result was known, and that cannot be undone by re-running it.
