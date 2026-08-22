# Trend: the index, the products, and a clause that was ambiguously specified

**Two questions, two experiments.**

1. **[Experiment 004](#experiment-004--the-index).** What does adding a diversified
   time-series-momentum sleeve do to a passive portfolio that already exists, measured
   against the honest control — a risk-matched increase in cash — rather than against the
   fully invested portfolio?
2. **[Experiment 008](#experiment-008--the-products).** Do the US-listed managed-futures
   ETFs an investor can actually buy *deliver* that exposure, at a cost their fee can
   account for?

**Statuses.**

| | Status | What the word means here |
| --- | --- | --- |
| Exp 004, the AQR TSMOM **index** | **`rejected`** under its frozen clause (d), **`unresolved`** under the reading [Experiment 008 judges better justified](#clause-d-re-read-under-both-readings) | The hypothesis that *this vendor series* adds material marginal value a simpler exposure cannot reproduce. **Trend as a strategy is not rejected** |
| Exp 008, **DBMF** | **`exploratory`** | It delivers the index's exposure at +0.671 and trails it by less than its own fee. Usable as an implementation proxy and for nothing else |
| Exp 008, **CTA, FMF, KMLM, WTMF** | **`rejected`** | They do not deliver *this benchmark's* exposure at the frozen 0.50 bar. **A statement about a measured loading, not about whether they are well run** |

Three warnings that belong before any number.

> **Experiment 004 evaluated an INDEX, and its verdict was for a time repeated to the
> project owner as though it applied to KMLM, DBMF and CTA.** It did not. Those products
> were never tested, they are differently constructed, and DBMF is an explicit
> *replication* strategy — the most interesting thing on the shelf given Experiment 004's
> own finding that a static replica captured 44% of the index's benefit. Experiment 008 is
> what testing them looks like, and it reaches a different answer for one of them.

> **Experiment 004 is a vendor-series evaluation, NOT an independent replication.** The
> series is authored by a firm that sells the strategy and is reconstructed on every
> update. An independent reimplementation would need contract-level futures histories, roll
> conventions, collateral returns and point-in-time availability, none of which are inputs
> here. `evidence_class: vendor-series-evaluation` is frozen in the specification so it
> cannot be renegotiated at write-up time. Experiment 008 is a `fund-implementation-audit`
> and is capped at `exploratory` by
> [decision 0002](../decisions/0002-no-research-grade-free-price-source.md).

> **A third experiment has since judged the same sleeve against a different comparator and
> rejected it.** [Experiment 010b](marginal-sleeve-value.md) measures a **10%** trend sleeve
> added to a **global equity core** with no risk match: on the deciding growth basis it
> contributes **+0.258 pp/yr** against a 0.30 threshold. Its certainty-equivalent companion
> is +1.172, and the **+0.913 pp/yr between them is de-risking**. **Neither experiment
> supersedes the other** — they ask different questions of different portfolios at different
> weights — but a reader who wants one number for "what is trend worth" should know there
> are two, and that the portfolio-level one is smaller.

---

## Experiment 004 — the index

### Conclusion

Adding a 15% trend sleeve to a 60/40 US equity / cash portfolio raised **geometric growth
by +1.312 pp/yr** and the CRRA certainty equivalent by **+1.342**, over a risk-matched cash
comparator, net-pessimistic, on 432 months, with a 95% interval of **[+0.76, +1.92]**. That
survived every hostile test: removing the best month costs 6%, removing the best crisis 9%,
doubling all costs 27%, and delaying execution a full month *improves* it.

**The two bases agree to 97.8%, and this is the repository's worked example of why a
risk-matched comparator is worth paying for.**
[Decision 0008](../decisions/0008-growth-decides-crra-reports.md) makes growth the deciding
metric everywhere, because an exact CRRA utility over a few dozen years pays a candidate
for *reducing risk* — something any investor obtains free by holding less equity. Only
**+0.030 pp/yr** of this headline is that payment, because `passive_plus_trend` carries
7.65% volatility against `passive_plus_cash`'s 7.88%, so **the de-risking is removed from
both sides before the difference is taken.** Experiment 010, measuring a sleeve against the
portfolio it de-risks, sees the same metric hand a cash control **+0.809 pp/yr**. **This is
the only place in the repository that pays for a risk-matched comparator, and therefore the
only place a certainty equivalent may be quoted as a primary at all.**

**It nonetheless fires the frozen falsifier, on clause (d).** A replica built only from a
static US-equity position, a volatility-scaled US-equity position, a convexity term and a
lagged market term — **with the regression intercept removed** — delivers **+0.59 pp/yr**,
44% of the sleeve's own benefit and well above the 0.30 threshold.

**Two findings matter more than the verdict.**

**The standalone series decayed enormously after publication and the marginal benefit
barely moved.** Trend's own Sharpe fell **1.34 → 0.83 → 0.18** across the reconstructed,
pre-publication and post-publication eras, and its geometric return **19.4% → 12.3% →
3.1%**. The marginal portfolio benefit fell only **+2.05 → +1.15 → +0.88 pp/yr** of growth.
**Almost all of what survives is the correlation, not the mean** — a materially different
claim from "trend still works", and the reason a standalone Sharpe ratio is not an answer
to this question.

**The vendor's cost basis cannot be established at all.** The archived workbook states no
fee, transaction-cost, slippage or financing assumption anywhere; its Definitions, Data
Sources and Disclosures tabs carry their content as embedded pictures rather than cells,
and the text recovered from them documents the volatility model and the universe while
saying nothing about costs. **Every figure below is gross of the vendor's own trading costs
by omission**, on top of survivorship and backfill distortion bounded at 7.7 pp/yr on
comparable CTA data — larger than the strategy's entire gross premium.

### What was compared

Five portfolios, monthly, 1990-01…2025-12 (432 months), with the same lagged volatility
estimator and exposure cap applied wherever logically possible. Net-pessimistic: 8 bp
one-way on portfolio trades, 1.50%/yr management fee and 10% of gains over a high-water
mark on the sleeve.

| Portfolio | CE %/yr | Geo %/yr | Vol % | Sharpe | Max DD % | Corr to passive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `passive_benchmark` 60/40 equity/cash | 6.61 | 7.85 | 9.12 | 0.58 | −33.1 | 1.00 |
| `volatility_scaled_passive` | 6.69 | 8.20 | 10.23 | 0.56 | −32.4 | 0.96 |
| `trend_alone` vendor series + cash | 9.18 | 10.70 | 12.17 | 0.68 | −30.1 | **−0.17** |
| **`passive_plus_trend`** 15% sleeve, funded pro rata | **7.62** | 8.45 | 7.65 | 0.75 | −25.9 | 0.97 |
| **`passive_plus_cash`** matched ex-ante risk budget | **6.28** | 7.14 | 7.88 | 0.57 | −28.4 | 0.99 |

**The last two rows are the experiment.** Comparing `passive_plus_trend` against
`passive_benchmark` would credit trend with certainty equivalent that is partly just
de-risking. The size of what the risk match removes is measurable on this page's own
numbers: against `passive_benchmark` the two metrics disagree by 0.380 pp/yr; against the
risk match, by **0.030**.

| Comparison | n | **Growth, γ=1** | CE, γ=3 | De-risking | 95% interval on CE | Holm p |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| `passive_plus_trend`, full period | 432 | **+1.312** | +1.342 | +0.030 | [+0.759, +1.916] | 0.0006 ✓ |
| reconstructed 1990–2000 | 132 | **+2.045** | +1.998 | −0.047 | [+1.361, +2.746] | 0.0000 ✓ |
| pre-publication 2001–2011 | 132 | **+1.152** | +1.179 | +0.027 | [+0.356, +1.953] | 0.0072 ✓ |
| **post-publication 2012–2025** | 168 | **+0.883** | +1.011 | +0.128 | **[−0.175, +2.165]** | **0.1992 ✗** |
| `trend_alone` | 432 | +3.556 | +2.892 | −0.664 | [−2.950, +8.487] | 0.4930 ✗ |
| `volatility_scaled_passive` | 432 | +1.061 | +0.408 | −0.653 | [−0.827, +2.066] | 0.4930 ✗ |
| `passive_benchmark` | 432 | +0.709 | +0.330 | −0.380 | [−0.454, +1.191] | 0.4930 ✗ |

**Read the de-risking column downward, because it is decision 0008's argument in one
place.** For the four rows carrying the risk match it never exceeds 0.128 pp/yr and is
twice negative. For the three that do *not*, it reaches −0.664, and there the certainty
equivalent is *charging* for added risk rather than paying for removed risk. **The metric
is not biased in one direction; it answers a different question, and only the risk match
makes the two questions the same.** Among the matched rows the gap is widest
post-publication, where **13% of the headline is de-risking** — the era whose interval
already includes zero and already fails Holm.

Note that **`trend_alone` — the standalone series everyone quotes — does not survive its
own interval.** Standalone significance and marginal utility are different questions and
give different answers here.

### Crisis-conditional

Crisis windows frozen from peak-to-trough equity drawdown dates before any result was
examined. Compounded over the window, not annualised.

| Crisis | Months | Passive | Risk-matched cash | Passive + trend | Trend alone | Marginal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Dotcom 2000-09 – 2002-09 | 25 | −27.5% | −20.6% | −18.5% | +49.6% | +2.11 pp |
| GFC 2007-11 – 2009-02 | 16 | −33.1% | −28.4% | −25.9% | +26.3% | +2.44 pp |
| Covid 2020-02 – 2020-03 | 2 | −12.3% | −9.4% | −9.0% | +10.4% | +0.40 pp |
| Inflation 2022-01 – 2022-10 | 10 | −10.7% | −10.7% | −5.0% | +32.0% | +5.69 pp |

Over the 53 crisis months the sleeve's correlation to the passive portfolio falls from
−0.17 to **−0.59**, and its downside beta over the full period is **−0.67**. That is the
mechanism behaving as advertised. **It is also where the evidence is weakest: 53 months at
a 12-month mean block is about 4.4 effective independent observations**, so no
crisis-conditional interval here can distinguish much of anything.

### Every hostile test

Certainty equivalent, against the +1.342 baseline. **The artifact publishes no per-test
geometric return**, so no growth companion can be quoted without inventing one; every row
shares the risk-matched comparator where the de-risking component is 2.2% of the baseline,
so the ranking is not one the metric change can plausibly reorder. **That is an argument
from the headline's own agreement, not a published number, and it is stated as one.**

| Test | Result | Share of baseline lost |
| --- | --- | ---: |
| Remove the best trend month (2015-01, +12.96%) | +1.255 | 6% |
| **Remove the best crisis (dotcom)** | **+1.217** | **9%** |
| Delay execution by one full month | +1.377 | −3% (improves) |
| Double every cost | +0.975 | 27% |
| Cap leverage at 1.5 | +1.342 | 0% — the cap never binds |
| Cap leverage at 0.75 | +1.652 | **invalid, see below** |
| Volatility lookback 20 / 120 days instead of 60 | +1.395 / +1.400 | −4% |
| Bond-leg robustness arm (modelled GS10) | +1.254 | 6% |
| Static long at matched ex-ante risk | −0.219 | destroys it |
| **Static + volatility exposure replica, intercept removed** | **+0.586** | **56% — clause (d) fires** |

**The 0.75 leverage cap row is not a valid marginal comparison and is reported only because
it was frozen.** `passive_plus_trend` is unlevered by construction, so no leverage cap can
bind on it; the cap binds on the *risk-matched comparator* in 364 of 432 months, de-risking
the control and inflating the measured benefit.

**Removing the best crisis costs almost nothing, and that is the strongest positive finding
here.** The sleeve's summed excess by crisis is dotcom +43.3%, 2022 inflation +29.0%, GFC
+27.9%, Covid +10.4% — **spread across four structurally different episodes**, not
concentrated in the one a backtest happened to catch.

**Gaps and reversals.** A monthly series cannot show an overnight gap, so this is a proxy
that understates the problem. The predicted pattern is present and it is the mechanism:
the sleeve pays **+1.95%/mo** in an abrupt onset, **+4.01%/mo** in a developed drawdown —
roughly twice as much — and **loses 0.53%/mo in sharp reversals**. A slow signal cannot be
short before a fall it has not seen.

### The decisive test: static and volatility exposures

Goyal and Jegadeesh (2018) show time-series momentum carries a large embedded net-long
market position, so the attribution is the test, not a footnote. Regressing the sleeve's
monthly excess return on a constant, the market excess return, a volatility-scaled market
position, |market| and the lagged market, HAC at 5 lags over 431 months:

| Regressor | Coefficient | HAC t |
| --- | ---: | ---: |
| Constant (annualised **+6.42%/yr**) | +0.00535 | +2.04 |
| Market excess return | **−1.043** | **−7.24** |
| Volatility-scaled market excess return | **+0.834** | **+5.94** |
| Absolute market excess return (convexity) | +0.133 | +2.01 |
| Lagged market excess return | +0.006 | +0.16 |

R² = 12.6%. Three readings. **The convexity is real but small.** **The market exposure is
dynamic, not static** — a large negative static beta against a large positive
volatility-scaled beta is precisely Goyal and Jegadeesh's mechanism rather than the
forecasting mechanism the strategy is sold on. **And the exposure replica reproduces 44% of
the benefit.**

A reader can reasonably disagree with the verdict, and the number they need is here: **the
sleeve's margin over its own replica is +0.756 pp/yr, which itself clears the 0.30
threshold.** Clause (d) was frozen in *absolute* form and applied as frozen. Had it been
written as a relative share, the verdict would be `unresolved`.

**Two guards worth naming, both bugs found while reading the first run's output and fixed
before the reported run.** The replica initially **included the regression intercept**,
which builds a near-riskless asset paying the sleeve's whole +6.42%/yr alpha at a third of
its volatility; it delivered +1.510, beat the sleeve itself, and fired clause (d) on an
artefact. **An intercept is by construction the part the exposures do *not* explain, so
including it in a test of whether exposures explain the result is a category error.** And
the crisis drawdown-reduction column had its **sign inverted**. Both now carry regression
tests, and the intercept fix is reported precisely because it *lowered* the number that
fires the falsifier, from +1.510 to +0.586, without changing the verdict.

### What this experiment could not do

| Test | Why not |
| --- | --- |
| **Kim, Tse and Wald: remove the volatility scaling** | **Not runnable, and it is the single most informative test of this strategy** — removing it collapses the published pooled *t* from 4.34 to 1.68. The published series is an aggregate of 58 already-scaled instrument positions and cannot be unwound |
| **Huang et al.'s bootstrap** | An asset-level predictive-regression test on the underlying instruments, not on a portfolio return series. Their finding stands as prior evidence and is neither confirmed nor rebutted here |
| **Re-cost the vendor series from its own trades** | The trades are not observable and the workbook states no cost basis |
| **Correct for survivorship and backfill** | Not estimable from one series. The published magnitude on comparable CTA data is 7.7 pp/yr, Sharpe 0.73 → 0.09 |

The lookback sensitivity must be read narrowly for the same reason: it moves *this
experiment's* estimator, which sizes the risk match. **It cannot touch the sleeve's own
scaling, which is the vendor's and is baked into the published aggregate.**

### Provenance

The AQR workbook is pinned by sha256 **and by sheet name**, as a first-class warning on the
manifest: AQR changes URLs, workbook names, sheet names and revisions, and a manifest
recording a hash but not a sheet is not reproducible. A raw-hash mismatch on AQR or Ken
French **aborts** the experiment.

**The vendor ships its methodology as pictures.** `data/aqr.py` recovers text from the EMF
record stream, because the alternative — recording that the vendor documented nothing — is
false. What it recovers: an exponentially weighted volatility model with a **60-day centre
of mass**; each position sized to **40% ex-ante annualised volatility**; a **58-instrument**
universe of 9 equity index futures, 13 bond futures, 12 FX pairs and 24 commodities; and
that **MSCI country index returns stand in for futures returns before futures were
available**, so part of the early history is not a futures strategy at all — which is why
the reconstructed era is reported separately and never pooled, **and it is the era with by
far the largest measured marginal benefit.** What it does not recover, because it is not
there: **any fee, transaction-cost, slippage or financing basis.**

Run `exp_004_trend_marginal_value --view-results`. Spec hash `e9e564f39ebd…`, seed
20260814, `run_id` `21a1517f295a44fd9ac213b502c1752a`. Four executions of the identical
hash are ledgered — repeated executions of one specification, not four hypotheses; the
three code changes between the first and the reported run are the intercept, drawdown-sign
and cap-reporting corrections above, each fixing a stated defect rather than moving a
threshold.

**Departures from the frozen draft, all made before any result.** The benchmark's bond leg
was replaced by cash, because no investable bond total-return history exists; the
equity/bond form survives as a declared robustness arm on a modelled GS10 proxy, moving the
headline to +1.254, and no conclusion rests on it. The volatility lookback stayed at 60
days and moved to monthly frequency. The execution delay became one month rather than one
and five trading days, which a monthly series cannot express — **strictly more hostile**.

---

## Experiment 008 — the products

**Exposure delivery is answerable on this window. Alpha is not.** Exposure delivery is a
loading on a named benchmark and a difference of means against it, and 46 to 78 months can
measure both. **The median minimum detectable alpha at 80% power across the 15
fund-by-specification tests is 12.75 pp/yr** — larger than any plausible true value. **Not
one of the 15 intercepts survives an uncorrected test at 0.05**, and **no falsifier clause
in Experiment 008 reads a *p*-value, by design.**

### The screen

Frozen before any return was downloaded, applied in a fixed order, only the **first**
failure recorded. The frame is the **union of the 2019Q4 and 2025Q4 censuses**, 14,742
series: Experiment 002 could take its frame at the start of its window, but DBMF launched
2019-05, KMLM 2020-12 and CTA 2022-03, so a 2019Q4-only frame would have excluded the
products the question is about by construction. **The asset floor is applied to the *larger*
of a series' two observed net-asset figures**, so a fund that reached the floor and then
shrank is not selected out.

| Stage | Removed | Remaining | What went |
| --- | ---: | ---: | --- |
| union census | — | 14,742 | — |
| mandate regex | 14,682 | **60** | everything naming no managed-futures mandate |
| exclusion regex | 9 | 51 | single-asset-class and sector trend products |
| **exchange-traded** | **35** | **16** | the entire mutual-fund shelf, including **AQR's own Managed Futures Strategy Fund at $4.88bn**, the largest in either census |
| minimum net assets ($100m) | 7 | 9 | |
| maximum expense ratio (1.50%) | 1 | 8 | TFPN at 1.96% |
| inception cutoff (2022-12-31) | 3 | **5** | the 2023–2025 launches |

**The screen is a rule, not a description of the request.** All three tickers the project
owner named pass, and so do two he did not — FMF and WTMF. **A test asserts the passing set
is not the requested set.**

**Attrition is severe and it is a lower bound.** Of 24 mandate-qualifying series in 2019Q4,
**13 (54.2%, $2.99bn)** are absent from the 2025Q4 census altogether.

### Exposure delivery against the AQR TSMOM index

OLS on a constant and the index, HAC at 6 lags. `TD` is the raw annualised difference of
means; `MDE₈₀` is the smallest intercept the window could detect.

| Ticker | Fee % | n | Loading | 95% interval | H1 | H2 | R² | TD pp/yr | TE pp/yr | MDE₈₀ | Status |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| **DBMF** | 0.85 | 54 | **+0.671** | `[+0.513, +0.829]` | +0.59 | +0.73 | 0.524 | **−0.48** | 9.66 | 10.93 | **`exploratory`** |
| CTA | 0.75 | 46 | +0.475 | `[+0.058, +0.991]` | −0.31 | +0.81 | 0.137 | +1.90 | 15.68 | 13.14 | `rejected` |
| FMF | 0.98 | 78 | +0.303 | `[+0.183, +0.420]` | +0.25 | +0.43 | 0.368 | −0.53 | 11.12 | 6.64 | `rejected` |
| KMLM | 0.90 | 60 | +0.245 | `[−0.148, +0.446]` | +0.14 | +0.24 | 0.066 | −1.41 | 15.79 | 16.49 | `rejected` |
| WTMF | 0.66 | 76 | +0.099 | `[+0.003, +0.201]` | +0.10 | +0.11 | 0.042 | +2.31 | 13.66 | 8.94 | `rejected` |

**One product delivers the index's exposure and it is the replication strategy.** DBMF's
interval is well clear of the 0.50 bar, it explains 52% of its own monthly variance with a
single regressor, and it holds the loading across the fixed split and **all 19 rolling
36-month windows** with no sign change. Its raw tracking difference is **−0.48 pp/yr
against an 0.85% fee**, so it trailed a *cost-free vendor index* by less than it charges.

**The other four do not deliver this benchmark's exposure, and the reasons differ.**
**KMLM's shortfall is partly definitional and must not be read as a defect**: the KFA MLM
Index holds 22 futures and **no equity index futures at all**, while AQR's universe holds
nine, so a loading of +0.245 on a benchmark a quarter of whose instruments KMLM does not
trade is a statement about the *benchmark's* equity content as much as about KMLM. **CTA
has 46 months and an interval from +0.058 to +0.991**, missing the bar by 0.025 with halves
of −0.31 then +0.81 — the least robust classification here. **FMF stably delivers about a
third** of the index over 78 months; **WTMF almost none**, and its +2.31 pp/yr tracking
difference means it *beat* the index, which is a return finding this page is not entitled
to make on 76 months and a 13.66 pp/yr tracking error.

**Read every tracking difference against its tracking error** — they run 9.66 to 15.79
pp/yr. **Clause (c) is a decision rule applied as frozen, not a measurement, and it fired
on nobody.**

**DBMF's filed history begins 2021-07, twenty-six months after its prospectus inception.**
Whatever explains that, **DBMF's effective sample is 54 months, not 80**, and it is
reported as 54 everywhere.

### Is any of this more than a market position?

Experiment 004's decisive design, unchanged, run on each product **and on the index
itself** over the same months.

| Series | Market | Vol-scaled market | \|Market\| | Raw α pp/yr | Shrunk α | MDE₈₀ | R² |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **AQR TSMOM index** | **−1.769** | **+1.282** | +0.102 | +0.43 | — | — | 0.266 |
| DBMF | −1.174 | +0.785 | +0.237 | −5.14 | −0.08 | 27.37 | 0.158 |
| KMLM | −0.628 | +0.426 | −0.068 | +6.87 | +0.27 | 17.26 | 0.031 |
| WTMF | −0.373 | +0.446 | −0.015 | +1.80 | +0.13 | 12.75 | 0.241 |
| FMF | −0.363 | +0.315 | +0.065 | −2.59 | −0.22 | 11.62 | 0.041 |
| CTA | −0.053 | **−0.214** | +0.296 | −5.52 | −0.29 | 14.93 | 0.158 |
| *VTI, the pedestal* | *+1.002* | *−0.005* | *−0.016* | *+0.42* | — | *1.18* | *0.999* |

**The index row is the control that makes this table readable** — a definitionally-trend
series shows Goyal and Jegadeesh's time-varying market position on a six-year window as
well as a thirty-six-year one. Each product's loadings are a distance from that row, not
from zero.

Read that way, **DBMF is the index scaled down by about two thirds on both legs** (0.66 and
0.61), which is the same 0.67 its direct loading reports. **Three independent measurements
agree.** **CTA is the outlier in the other direction**: a static market beta of −0.053 and
a *negative* volatility-scaled loading is not the trend exposure profile at all.

**Shrinkage is measured, not assumed, and far more severe here than on index funds.** The
realised factors run **0.016 to 0.218, median 0.070** — against Experiment 002's 0.431 on
index funds. **A raw alpha on this shelf is worth about a fourteenth of itself once shrunk,
and quoting one unshrunk would overstate it by more than an order of magnitude.** With
MDE₈₀ running 11.6 to 27.4 pp/yr, **the alpha column is unmeasured, not measured and
small.**

**The multiple-testing family is 5 funds × 3 specifications = 15 intercept tests. Zero
survive at an uncorrected 0.05, zero under Benjamini–Hochberg and zero under Holm.**
Padding to every screened series × three leaves zero as well, which it must.

### The marginal-contribution arm is declared, run, and NOT valid

Experiment 004's five-way structure re-run on each product:

| Ticker | Whole years | Marginal CE pp/yr | Months with an unwarmed estimator | Risk match holds |
| --- | ---: | ---: | ---: | --- |
| DBMF | 4 | +2.093 | 6 of 48 | **no** |
| CTA | 3 | +1.431 | 2 of 36 | **no** |
| KMLM | 5 | +0.426 | 12 of 60 | **no** |
| FMF | 6 | +0.307 | 6 of 72 | **no** |
| WTMF | 6 | −0.053 | 8 of 72 | **no** |

**Not one of these is a valid marginal comparison, and the column that says so is the only
one worth reading.** The risk-matched comparator is sized from a lagged volatility
estimator; Experiment 004 had sixty months of burn-in, and a fund whose entire filed
history is the window has none, so in the first months the comparator runs at full exposure
while the treatment is de-risked — **the exact error the risk-matched comparator exists to
remove.** A null-case regression test pins this: with a warm-up prefix a zero-excess sleeve
gives a marginal benefit of zero to 1e-6, and without one the same input gives a spurious
positive. **These numbers are evidence about the window, not about the funds.**

### Cost and tax

**The distribution observable in Form N-PORT turned out to be empty for this whole shelf,
and that is a finding rather than a gap to fill quietly.** Item B.6 reports distributions
*reinvested in shares*; across **321 fund-months it is identically zero for all five
funds**, because ETF distributions are paid in cash through the depository. **This field
cannot measure distributions for an exchange-traded product**, and the reader and its tests
are kept because the refusal is the record.

What can measure tax is each fund's **own SEC-standardised after-tax return table**,
computed by the fund at the highest individual federal rates.

| Ticker | Longest period | Before tax %/yr | After tax on distributions | **Tax drag pp/yr** |
| --- | --- | ---: | ---: | ---: |
| CTA | since 3/2022 | 10.93 | 8.40 | **+2.53** |
| **DBMF** | since 5/2019 | 8.28 | 6.19 | **+2.09** |
| KMLM | since 12/2020 | 5.77 | 3.96 | **+1.81** |
| WTMF | 10 years | 1.04 | −0.26 | **+1.30** |
| FMF | since 8/2013 | 1.32 | 0.56 | **+0.76** |

**The tax drag is two to three times the expense ratio on the two funds that made money.**
For DBMF, 0.85% of fee against 2.09 pp/yr of distribution tax — the fee is smaller by a
factor of 2.5. Every one of these funds runs its commodity book through a Cayman subsidiary
whose income is ordinary. **In an IRA or a 401(k) this entire column is zero.**

**No falsifier clause reads these figures, deliberately.** They were read from the
prospectuses while the product facts were assembled — before any N-PORT return was
downloaded, but **visible to the author**. A threshold placed on a quantity after seeing it
is not a falsifier. They are measured, reported, and decide nothing, **and that limitation
is recorded in the frozen specification rather than repaired by inventing a bar.**

---

## The shelf two censuses later: five became fifteen, and the screen is why it did not

`as of 2026-08-17`, from the SEC's 2026Q2 N-PORT structured data set against the 2025Q4 one
Experiment 008 used, screened with the **same frozen mandate and exclusion patterns**.
Provenance in
[`data-manifests/wrapper_shelf/shelf_census.json`](../../research/data-manifests/wrapper_shelf/shelf_census.json).

**Experiment 008's sentence "the listed managed-futures shelf is five products" was true when
it was written and is no longer true.** Fifteen exchange-listed series now carry a diversified
managed-futures mandate. The frozen screen still admits exactly five — **and it is the
inception cutoff doing it, not quality.**

| Ticker | Fund | Net assets 2026Q2 | vs 2025Q4 | In Exp 008? |
| --- | --- | ---: | ---: | --- |
| **DBMF** | iMGP DBi Managed Futures Strategy | **$3,297.3m** | **+118%** | yes |
| **CTA** | Simplify Managed Futures Strategy | $1,491.5m | +27% | yes |
| **IMF** | Invesco Managed Futures Strategy | $301.1m | +3% | **no — inception 2025** |
| **KMLM** | KraneShares Mount Lucas MF Index | $272.5m | +50% | yes |
| **FFUT** | Fidelity Managed Futures | $255.9m | **+103%** | **no — inception 2025** |
| **FMF** | First Trust Managed Futures Strategy | $252.9m | +37% | yes |
| **WTMF** | WisdomTree Managed Futures Strategy | $213.5m | +29% | yes |
| **TFPN** | Blueprint Chesapeake Multi-Asset Trend | $140.0m | +13% | **no — fee was 1.96%, now 1.13%** |
| ISMF | iShares Managed Futures Active | $56.6m | +165% | no |
| AHLT | American Beacon AHL Trend | $49.6m | −1% | no |
| MATE | Man Active Trend Enhanced | $36.3m | new | no — and it is an **overlay** |
| ASMF | Virtus AlphaSimplex Managed Futures | $31.0m | +8% | no |
| MFUT | Cambria Chesapeake Pure Trend | $30.5m | +38% | no |
| HFMF | Unlimited HFMF Managed Futures | $19.4m | +837% | no |
| SDMF | Simplify DBi CTA Managed Futures Index | $4.4m | new | no |

**Three funds now fail the screen on nothing but a date.** IMF and FFUT clear the $100m floor
and the 1.50% fee cap and fail only the 2022-12-31 inception cutoff. **TFPN cut its expense
ratio from 1.96% to 1.13%** effective 2026-07-17 — it was the single fund Experiment 008
rejected on fee — and at $140m it too now fails on inception alone. **A screen re-frozen today
would admit eight.**

**That is a statement about the screen and not an invitation to re-run it.** The cutoff was
frozen before any return was seen; moving it now, with this table visible, would destroy the
provenance that makes Experiment 008 worth anything. The right response is a **new**
pre-registered specification, not an amendment to this one.

### What this changes about single-product risk

[The recommendation](portfolio-recommendation.md) records DBMF as carrying "single-product
risk" with "no fallback", and this page's consequence list says any later work needing an
investable trend proxy "has one candidate and no fallback". **Both are now overstated.**

- **BlackRock, Fidelity, Invesco and Man Group have all entered since Experiment 008 ran.**
  Four of the largest asset managers in the world now list a diversified managed-futures ETF.
  A shelf with those sponsors on it is a different survival proposition from a five-fund one.
- **DBMF is no longer the fragile case.** It grew from $1,511m to $3,297m across two
  censuses, monotonically — $2,046m at 2025-12-31 — and is now roughly twice the size of the
  next fund. The concern that attached to it in 2026 was a concern about a small fund.
- **What has *not* changed is exposure delivery.** None of the new funds has been tested
  against the AQR benchmark, and Experiment 008's finding was never that no fallback *exists*
  — it was that only DBMF's **measured loading** clears the frozen 0.50 bar. **Eleven
  untested funds are not eleven fallbacks.** They are the population a re-specified experiment
  would draw from.

### Fund-level facts, as of the latest census

- **KMLM is under interim advisory agreements.** Krane Funds Advisors underwent a **change of
  control on 2026-06-23** — KFA Two Holdings acquired 50.1% from CICC USA — which assigned and
  terminated the advisory and sub-advisory agreements. The fund operates under **interim**
  agreements expiring around **2026-11-20** pending a shareholder vote. This is the closest
  thing to an observable methodology-change precursor that
  [capital efficiency §9.4](capital-efficiency-and-breadth.md) says is not estimable, and it
  is live on a fund this page grades.
- **DBMF's trust was renamed to iM Global Partner Funds on 2026-07-24**, and its Cayman
  subsidiary is capped at **20% of assets**, not the 25% every other fund on the shelf uses.
- **FMF changed its fiscal year end from 31 December to 30 September**, effective around
  2026-07-31, and is the one fund of the five whose distributions include **return of
  capital**.
- **CTA's tax character was not 100% ordinary in every year.** This page's cost-and-tax
  section and [structural and tax-aware edges §3](structural-and-tax-edges.md#3-section-1256-and-capital-efficiency-handled-honestly)
  both read as though the §1256 60/40 split reached no shareholder. **CTA's FY2024
  distribution was about 59.9% ordinary income and 40.1% long-term capital gain.** The FY2025
  figure is right; the generalisation is not.
- **No fund on this shelf carries a drawdown-triggered de-risking rule.** Checked across all
  fifteen listed funds and nine managed-futures mutual funds. Several carry continuous
  **volatility targets** — DBMF 8–10%, American Beacon AHL 10% of NAV, Virtus AlphaSimplex
  ≤17%, AQR 5–20% — which are a different object and do not condition on drawdown.
- **Experiment 008's universe rejected the iShares fund for the wrong reason.** It was
  recorded as failing `exchange_traded` because no share class carried an `ETF=Y` flag; it is
  **ISMF, listed on Cboe BZX**. The screen's outcome is unaffected — at $56.6m it fails the
  asset floor either way — but the stated reason is wrong, and the same gap in the SEC's
  `company_tickers_mf.json` hides CTAP and MATE. **The `exchange_traded` test must not rest on
  that file alone.**

### Closures: zero measured, and the measurement is lagged

**No series present in the 2025Q4 census is absent from 2026Q2, and none is marked as a final
filing.** Two quarters is far too short to say anything about
[the 10.7%/yr hazard](live-managed-futures.md), and it is not used to.

**One reorganisation is under way that no census can see yet.** The Mast Managed Futures
Strategy Fund closes to purchases on 2026-08-27 and converts into an ETF after the close on
2026-08-31 (497 filed 2026-08-07). **It will appear in no N-PORT census until 2026Q3.** Every
closure figure this repository publishes is therefore lagged by at least a quarter *as well as*
being a lower bound, and the two errors run the same way.

---

## Clause (d), re-read under both readings

Experiment 004's clause (d), verbatim:

> (d) an attribution on static asset exposures plus a volatility-scaled market position
> **leaves a marginal benefit below the materiality threshold**, i.e. a simpler static
> exposure explains it

**The sentence does not say whose marginal benefit.** Experiment 008 re-runs the *decision*,
not the data: the three deciding quantities are quoted in its frozen specification from
Experiment 004's ledgered artifact and verified against it at run time to 1e-6. All three
are certainty equivalents, and they are entitled to be — every one is measured against the
same risk-matched comparator, which is the condition
[decision 0008](../decisions/0008-growth-decides-crra-reports.md) sets.

| Reading | Deciding quantity | Value | Threshold | Fires? | Verdict |
| --- | --- | ---: | ---: | --- | --- |
| **Absolute** — the replica's own marginal benefit clears the threshold | replica marginal CE | **+0.586** | 0.30 | **yes** | **`rejected`** |
| **Relative** — what the attribution *leaves* | sleeve less replica | **+0.756** | 0.30 | **no** | **`unresolved`** |

Sleeve +1.342, replica +0.586 (**43.7%**), margin +0.756. Experiment 004 applied the
absolute reading, as frozen. A third reading — that the *residual* must clear the threshold
— is degenerate, since an OLS residual is mean-zero by construction and would fire whatever
the data say.

### Which reading is better justified

**The relative reading, and the argument is about what the clause was for rather than which
answer it gives.**

Clause (d) was frozen to catch one failure mode: Goyal and Jegadeesh's finding that
time-series momentum could be a market position wearing a forecasting costume. **The claim
that failure mode makes is that the exposures *explain* the result — and "explains" is
inherently a share, not a level.**

The absolute reading has a property no falsifier should have: **its bar gets easier to
clear as the sleeve gets better.** A larger sleeve benefit mechanically enlarges the fitted
replica, so a stronger result is *more* likely to be rejected at a fixed explained share.
Holding the share fixed at 43.7% and scaling the effect:

| Sleeve pp/yr | Replica pp/yr | Share explained | Absolute fires? | Relative fires? |
| ---: | ---: | ---: | --- | --- |
| 0.50 | 0.219 | 43.7% | no | **yes** |
| **1.342** | **0.586** | **43.7%** | **yes** | no |
| 50.0 | 21.85 | 43.7% | **yes** | no |

**Nothing about the explanation changed down that column.** The absolute reading changed
its mind anyway, and in the wrong direction: a sleeve delivering 50 pp/yr of which 56% is
unexplained would be rejected for being "explained". The relative reading moves in the
right direction, and **that monotonicity is asserted as a regression test, not only as
prose.**

**Neither reading is scale-free, and that is the deeper defect.** Both compare a level in
percentage points against an absolute bar. A clause about *explanation* should have named a
**share**.

**The honest answer.** Both readings are defensible on the text as written, and that is the
finding. Experiment 004 applied one as frozen, **disclosed the ambiguity in its own
write-up, and reported the number the other reading needs** — which is the correct
behaviour and the only reason this re-run was possible. **The defect is one of
specification quality, not of conduct.** The rule that would have prevented it:

> **A falsifier must name its deciding quantity as an expression, not as a description in
> prose, and in units that do not move with the size of the effect.** `replica_marginal >=
> 0.30` or `replica_marginal / sleeve_marginal >= 0.60` would each name both.

**What this changes, and what it does not.** Under the relative reading Experiment 004's
status becomes **`unresolved`** — exactly what its own write-up said it would. **`unresolved`
is not a promotion.** The vendor's cost basis is still unestablished, the post-publication
interval still contains zero and still fails Holm, the standalone Sharpe still fell 1.34 →
0.18, the survivorship distortion on comparable CTA data is still 7.7 pp/yr, and
`vendor-series-evaluation` still caps the result at `exploratory`. **Nothing about a trend
sleeve becomes investable because a clause was read the other way.** Experiment 004's frozen
specification and recorded status are untouched; this is a second, differently-specified
look at the same decision, ledgered separately, **and the two must never be described as
one run.**

---

## Two errors this page corrects

Both were transfers of a verdict to a population it was never measured on.

1. **Experiment 004's verdict was repeated as though it applied to KMLM, DBMF and CTA.** It
   evaluated an index. Experiment 008 tests them and reaches a *different* answer for DBMF
   — the one that is an explicit replication strategy, and therefore the one Experiment
   004's own 44%-replica finding should have made most interesting rather than least.
2. **Hedge-fund CTA fee evidence was applied to exchange-traded funds.** Bhardwaj, Gorton
   and Rouwenhorst measure 1994–2012 CTAs whose **fee income was around 4% of assets**. The
   funds here charge **0.66% to 0.98%**, read from their own SEC-filed prospectus fee
   tables. A four-point fee load does not transfer to an 0.85% one, and that study is used
   nowhere in Experiment 008. **The finding it *does* support — that the gap between a
   gross strategy and a net product can exceed the entire premium — is exactly what the tax
   column measures, and there the number is 0.76 to 2.53 pp/yr, not 4.**

---

## Open questions

- **Does DBMF's exposure delivery survive a longer window and a real cost model?**
  Fifty-four months, one benchmark, no bid-ask or brokerage. The loading is stable across
  every split this window supports, **which is the strongest statement 54 months can make
  and is not a strong statement.**
- **Is the AQR index the right benchmark for a shelf that does not all trade the same
  markets?** A per-fund benchmark built from each fund's own stated universe would separate
  "does not deliver trend" from "does not deliver *this* trend", and does not exist here.
- **What is the after-tax ranking?** Measured but not decided: the figures were seen before
  a threshold could be frozen against them.
- **Does the volatility-scaling result survive at contract level?** The single most
  informative published counter-test cannot be run on any public aggregate.
- **Is the residual after the exposure attribution a different exposure or a premium?** The
  attribution can only see the US equity market while the sleeve trades 58 instruments
  across four asset classes, so its 12.6% R² is a **lower bound** on how much simple
  exposures could explain. **A multi-asset attribution is the highest-value next step on
  this question.**
- **Does any N-PORT return agree with an independent measurement?** Unanswered for all five.

## Consequence for this repository

- **The framework's gap that post-publication trend index returns were never verified is
  closed for this vendor series.** Decay is large in the *series* and small in the *marginal
  benefit*, **and conflating the two is the error this experiment exists to prevent.**
- **Trend is not promoted**, and under the frozen taxonomy a vendor-series evaluation cannot
  exceed `exploratory` in any case.
- **This result and [Experiment 003](rebalancing-policy.md) look at the same phenomenon from
  opposite sides and agree.** Experiment 003 found relative performance between equity
  sleeves *trends* rather than reverses — every variance ratio exceeds one — which is why
  its rebalancing policies all lost. **A market in which relative performance trends is one
  in which a trend-following sleeve should pay and a mean-reverting rebalancing rule should
  not.** Neither promotes anything, but the two failures point the same way.
- **The listed managed-futures shelf was five products when Experiment 008 ran and is
  fifteen now**, with BlackRock, Fidelity, Invesco and Man Group among the entrants, and
  DBMF has grown to $3.30bn. **One product still delivers the benchmark's exposure at the
  frozen bar, because the other fourteen have never been tested.** "One candidate and no
  fallback" was true of the *tested* set and was repeated as though it were true of the
  shelf; the correct statement is that a re-specified experiment now has a population to draw
  from and this one does not.
- **A screen that admits the same five funds two years later is reporting its own inception
  cutoff.** Three funds now fail on that date alone, one of them because it cut its fee below
  the cap that had rejected it. A frozen screen is worth its provenance and it is not worth a
  claim about the market.
- **A product's fee is the smaller cost on this shelf.** Fees run 0.66% to 0.98%;
  distribution tax drag runs 0.76 to 2.53 pp/yr and is 2.5× the fee for DBMF, **and zero in
  a tax-deferred account. Where a trend sleeve is held matters more than which product is
  chosen** — **and the wrapper decides how much that matters.** The same dollar of trend
  notional carries 2.09 pp/yr of drag through DBMF and **0.32 through RSST**, whose equity
  sleeve shares the capital and is taxed at long-term rates
  ([capital efficiency §6a.4](capital-efficiency-and-breadth.md)). The control case is
  RSBT and RSBY: bond-based stacks whose entire overlay sits in a Cayman subsidiary, **100%
  ordinary income and 0% qualified in every year of their existence.**
- **A falsifier must name its deciding quantity as an expression, not as prose, and in units
  that do not move with the size of the effect.** Clause (d) is the worked example.
- **Form N-PORT cannot measure distributions for an exchange-traded fund.** Any later work
  wanting distributions needs Form N-CSR, which is unstructured HTML.

## Reproduce it

```sh
cd research
uv run python -m portfolio_edge.experiments.exp_004_trend_marginal_value --view-results
uv run python -m portfolio_edge.experiments.exp_008_managed_futures --build-universe
uv run python -m portfolio_edge.experiments.exp_008_managed_futures --view-results
```

| | Experiment 004 | Experiment 008 |
| --- | --- | --- |
| Specification | `exp_004_trend_marginal_value.yaml`, `e9e564f39ebd…` | `exp_008_managed_futures_products.yaml`, `2392fbca35bc…` |
| Run reported | `21a1517f295a44fd9ac213b502c1752a` | `3cf8c777d76e4d9094f7c431803b7a2e` |
| Seed | 20260814 | 20260812 |
| Inference | Paired stationary block bootstrap, 12-month mean block, 20,000 resamples | HAC at 6 lags; block bootstrap, 6-month mean block, 10,000 resamples |

Experiment 008's other ledgered runs: one `failed` — **the clause (d) verification guard
refused the run**, because the sleeve marginal frozen in the specification differed from
Experiment 004's ledgered artifact by 0.00057 pp/yr, above the 1e-6 tolerance; the frozen
value carried digits that had been supplied rather than read, and **no result had been
examined** because the run aborted before any result object existed. And one earlier
`succeeded` whose `result` block is byte-identical to the reported run.

One change was made **after** the first successful run and is reported rather than folded
in: the marginal-contribution arm now warms its volatility estimator on each fund's whole
filed history and reports the count of unwarmed months. FMF moved +0.012 → +0.307 and WTMF
−0.193 → −0.053; **the defect is not fully repairable on this data, which is why every row
of that table is labelled invalid.**
</content>
