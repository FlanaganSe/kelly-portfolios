# Trend: the index, the products, and a clause that was ambiguously specified

**Two questions, two experiments, one page.**

1. **[Experiment 004](#experiment-004--the-index).** What does adding a diversified
   time-series-momentum sleeve do to a passive portfolio that already exists, measured
   against the honest control — a risk-matched increase in cash — rather than against
   the fully invested portfolio?
2. **[Experiment 008](#experiment-008--the-products).** Do the US-listed
   managed-futures ETFs an investor can actually buy *deliver* that exposure, at a
   cost their fee can account for?

**Decision they inform.** Whether a trend sleeve is worth building an investable
implementation for, which product could serve as that implementation, and what
evidence would be needed to promote one. Neither informs an allocation.

**Statuses.**

| | Status | What the word means here |
| --- | --- | --- |
| Experiment 004, the AQR TSMOM **index** | **`rejected`** under its frozen clause (d), **`unresolved`** under the reading [Experiment 008 judges better justified](#clause-d-re-read-under-both-readings) | The hypothesis that *this vendor series* adds material marginal value a simpler exposure cannot reproduce. Trend as a strategy is not rejected. |
| Experiment 008, **DBMF** | **`exploratory`** | It delivers the index's exposure at a loading of **+0.671** and trails it by less than its own fee. It may be used as an implementation proxy in a later experiment and for nothing else. |
| Experiment 008, **CTA, FMF, KMLM, WTMF** | **`rejected`** | They do not deliver *this benchmark's* exposure at the frozen 0.50 bar. That is a statement about a measured loading, not about whether they are well run. |

> **Experiment 004 evaluated an INDEX. It said nothing about any product, and its
> verdict was for a time repeated to the project owner as though it applied to KMLM,
> DBMF and CTA.** It did not. Those products were never tested, they are differently
> constructed, and DBMF is an explicit *replication* strategy — which is the most
> interesting thing on the shelf given Experiment 004's own finding that a static
> replica captured 44% of the index's benefit. Experiment 008 is what testing them
> looks like, and it reaches a different answer for one of them.

> **Experiment 004 is a vendor-series evaluation, NOT an independent replication.**
> The series is authored and maintained by AQR, a firm that sells the strategy, and
> the workbook states that AQR reconstructs the full history each time the returns are
> updated. An independent reimplementation would require contract-level futures
> histories, roll conventions, collateral returns, execution assumptions and
> point-in-time market availability. None of those are inputs here. `evidence_class:
> vendor-series-evaluation` is frozen in the specification so this cannot be
> renegotiated at write-up time. Experiment 008 is a `fund-implementation-audit` and
> is capped at `exploratory` by
> [decision 0002](../decisions/0002-no-research-grade-free-price-source.md).

---

## Experiment 004 — the index

## Conclusion

Adding a 15% trend sleeve to a 60/40 US equity / cash portfolio raised the CRRA
(γ=3) certainty-equivalent return by **+1.34 percentage points a year** over a
risk-matched cash comparator, net-pessimistic, 95% interval **[+0.76, +1.92]** on
432 months. That survived every hostile test: removing the best month costs 6%,
removing the best crisis costs 9%, doubling all costs costs 27%, delaying execution
a full month *improves* it, and the benefit is spread across all four predeclared
crises rather than concentrated in one.

It nonetheless fires the frozen falsifier, on clause (d). A replica built only from
a static US-equity position, a volatility-scaled US-equity position, a convexity
term and a lagged market term — **with the regression intercept removed** —
delivers **+0.59 pp/yr**, 44% of the sleeve's own benefit and well above the 0.30
pp/yr materiality threshold. A simpler exposure reproduces a material part of the
result, which is what Goyal and Jegadeesh (2018) predict and what clause (d) was
frozen to catch.

Two further findings matter more than the verdict.

**The standalone series decayed enormously after publication and the marginal
benefit barely moved.** Trend's own Sharpe ratio fell 1.34 → 0.83 → 0.18 across the
reconstructed, pre-publication and post-publication eras, and its geometric return
fell 19.4% → 12.3% → 3.1% a year. The marginal portfolio benefit fell only +2.00 →
+1.18 → +1.01 pp/yr. Almost all of what survives is the correlation, not the mean.
That is a materially different claim from "trend still works", and it is the reason
a standalone Sharpe ratio is not an answer to this question.

**The vendor's cost basis cannot be established at all.** The archived workbook
states no fee, transaction-cost, slippage or financing assumption anywhere. Its
Definitions, Data Sources and Disclosures tabs carry their entire content as
embedded EMF pictures rather than cells (see [Provenance](#provenance)), and the
text recovered from those pictures documents the volatility model, the 40%
per-position volatility target and the 58-instrument universe while saying nothing
about costs. Every figure below is therefore gross of the vendor's own trading costs
by omission, on top of the survivorship and backfill distortion that
[the framework](portfolio-edge-research-framework.md) bounds at 7.7 percentage
points a year on comparable CTA data — larger than the strategy's entire gross
premium.

## What was compared

Five portfolios, monthly, 1990-01 to 2025-12 (432 months = 36 whole calendar years),
with the same lagged volatility estimator and the same exposure cap applied wherever
logically possible. Net-pessimistic column: 8 bp one-way on portfolio trades, 1.50%
a year management fee and 10% of gains over a high-water mark on the sleeve.

| Portfolio | CE %/yr | Geo %/yr | Vol % | Sharpe | Max DD % | Corr to passive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `passive_benchmark` 60/40 equity/cash | 6.61 | 7.85 | 9.12 | 0.58 | −33.1 | 1.00 |
| `volatility_scaled_passive` same estimator and cap | 6.69 | 8.20 | 10.23 | 0.56 | −32.4 | 0.96 |
| `trend_alone` vendor series + cash | 9.18 | 10.70 | 12.17 | 0.68 | −30.1 | −0.17 |
| `passive_plus_trend` 15% sleeve, funded pro rata | **7.62** | 8.45 | 7.65 | 0.75 | −25.9 | 0.97 |
| `passive_plus_cash` **matched ex-ante risk budget** | **6.28** | 7.14 | 7.88 | 0.57 | −28.4 | 0.99 |

The last two rows are the experiment. Comparing `passive_plus_trend` against
`passive_benchmark` would credit trend with +1.34 pp/yr of certainty equivalent that
is partly just de-risking — the benchmark carries 9.12% volatility against the
sleeve portfolio's 7.65%. The risk-matched comparator removes that, and it is the
comparator the specification froze as primary for exactly the reason Israelov (2019)
gives about protection strategies: the benchmark choice decides the answer.

### Marginal certainty equivalent, against the risk-matched comparator

| Comparison | n | pp/yr | 95% interval | one-sided p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: |
| `passive_plus_trend`, full period | 432 | **+1.342** | [+0.759, +1.916] | 0.0001 | 0.0006 ✓ |
| `passive_plus_trend`, reconstructed 1990–2000 | 132 | +1.998 | [+1.361, +2.746] | 0.0000 | 0.0000 ✓ |
| `passive_plus_trend`, pre-publication 2001–2011 | 132 | +1.179 | [+0.356, +1.953] | 0.0014 | 0.0072 ✓ |
| `passive_plus_trend`, post-publication 2012–2025 | 168 | +1.011 | [−0.175, +2.165] | 0.0498 | 0.1992 ✗ |
| `trend_alone` | 432 | +2.892 | [−2.950, +8.487] | 0.1754 | 0.4930 ✗ |
| `volatility_scaled_passive` | 432 | +0.408 | [−0.827, +2.066] | 0.2178 | 0.4930 ✗ |
| `passive_benchmark` | 432 | +0.330 | [−0.454, +1.191] | 0.1643 | 0.4930 ✗ |

Paired stationary block bootstrap, mean block 12 months, 20 000 resamples,
resampling the joint monthly panel so the pairing is preserved. The predeclared 6-
and 24-month neighbour blocks move the full-period interval to [+0.73, +1.96] and
[+0.83, +1.86]; the conclusion does not depend on the block length. Holm at 0.05
across the seven-member family; these comparisons share a benchmark, a sleeve and
overlapping windows, so the correction is a lower bound.

Note that `trend_alone` — the standalone series everyone quotes — does **not**
survive its own interval. Standalone significance and marginal utility are different
questions and they give different answers here.

### Crisis-conditional

Crisis windows frozen from peak-to-trough equity drawdown dates before any result
was examined. Figures are compounded over the window, not annualised, because
annualising a two-month window manufactures precision.

| Crisis | Months | Passive | Risk-matched cash | Passive + trend | Trend alone | Marginal | DD reduction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Dotcom 2000-09 – 2002-09 | 25 | −27.5% | −20.6% | −18.5% | +49.6% | +2.11 pp | +2.18 pp |
| GFC 2007-11 – 2009-02 | 16 | −33.1% | −28.4% | −25.9% | +26.3% | +2.44 pp | +1.84 pp |
| Covid 2020-02 – 2020-03 | 2 | −12.3% | −9.4% | −9.0% | +10.4% | +0.40 pp | +0.90 pp |
| Inflation 2022-01 – 2022-10 | 10 | −10.7% | −10.7% | −5.0% | +32.0% | +5.69 pp | +1.74 pp |
| **Union** | **53** | — | — | — | — | **+6.17 pp** | — |

Over the 53 crisis months the sleeve's correlation to the passive portfolio falls
from −0.17 to **−0.59**, and its downside beta over the full period is **−0.67**.
That is the crisis-diversification mechanism behaving as advertised. It is also
where the evidence is weakest: 53 months at a 12-month mean block is about **4.4
effective independent observations**, so no crisis-conditional interval here can
distinguish much of anything, and the specification requires that to be reported as
`unresolved` rather than narrowed by changing the estimator.

## Every hostile test

| Test | Result | Share of the +1.342 baseline lost |
| --- | --- | ---: |
| Remove the best trend month (2015-01, +12.96%) | +1.255 | 6% |
| Remove the best crisis (dotcom, the largest summed sleeve return) | +1.217 | 9% |
| Delay execution by one full month | +1.377 | −3% (improves) |
| Double every cost: 16 bp, 3.0% fee, 20% performance | +0.975 | 27% |
| Cap leverage at 1.5 | +1.342 | 0% — the cap never binds |
| Cap leverage at 0.75 | +1.652 | **invalid, see below** |
| Volatility lookback 20 days instead of 60 | +1.395 | −4% |
| Volatility lookback 120 days instead of 60 | +1.400 | −4% |
| Bond-leg robustness arm (modelled GS10 total return) | +1.255 | 6% |
| Static long at matched ex-ante risk | −0.219 | destroys it |
| Volatility-scaled long at matched ex-ante risk | −0.121 | destroys it |
| **Static + volatility exposure replica, intercept removed** | **+0.586** | **56% — clause (d) fires** |

**The 0.75 leverage cap row is not a valid marginal comparison and is reported only
because it was frozen.** `passive_plus_trend` is unlevered by construction — the
sleeve is funded pro rata from the two existing legs, so gross exposure stays at
1.0 and no leverage cap can ever bind on it. The cap binds on the *risk-matched cash
comparator*, whose mean exposure is 0.888, in 364 of the 432 months. Forcing the
control below its matched exposure de-risks the control and inflates the measured
benefit. The number is evidence about where the cap bites, not a stressed estimate.

**Removing the best crisis costs almost nothing, and that is the strongest positive
finding here.** The sleeve's summed excess return by crisis is dotcom +43.3%, 2022
inflation +29.0%, GFC +27.9%, Covid +10.4%. The payoff is spread across four
structurally different episodes — an equity-valuation unwind, a credit crisis, a
two-month liquidity shock, and a joint stock-bond inflation repricing — not
concentrated in the one crisis a backtest happened to catch.

**Delaying execution by a month improves the result**, which is consistent with a
slow signal whose value is not in the immediate month. The frozen one- and
five-trading-day delays are not expressible in a monthly series, so this substitutes
a strictly more hostile test.

### Gaps and reversals

A monthly series cannot show an overnight gap at all, so this is a proxy and it
understates the problem.

| Regime | Months | Mean equity excess | Mean sleeve excess |
| --- | ---: | ---: | ---: |
| Abrupt onset: a large equity loss straight after a rising month | 23 | −6.84%/mo | **+1.95%/mo** |
| Developed drawdown: a large loss after two losing months | 13 | −8.25%/mo | **+4.01%/mo** |
| Sharp reversal: a large move against a large move | 20 | +4.24%/mo | **−0.53%/mo** |

The predicted pattern is present and it is the mechanism, not a coincidence: the
sleeve pays roughly twice as much in a *developed* drawdown as in one that opens
abruptly, and it loses money in sharp reversals. A slow signal cannot be short
before a fall it has not seen.

## The decisive test: static and volatility exposures

Goyal and Jegadeesh (2018) show time-series momentum carries a large embedded
net-long market position and that adding a time-varying market position to a
cross-sectional strategy reproduces the time-series result. So the attribution is
the test, not a footnote.

Regressing the sleeve's monthly excess return on a constant, the market excess
return, a volatility-scaled market position, the absolute market return (a convexity
proxy) and the lagged market return, with Newey-West standard errors at 5 lags over
431 months:

| Regressor | Coefficient | HAC t |
| --- | ---: | ---: |
| Constant (annualised **+6.42%/yr**) | +0.00535 | **+2.04** |
| Market excess return | **−1.043** | **−7.24** |
| Volatility-scaled market excess return | **+0.834** | **+5.94** |
| Absolute market excess return (convexity) | +0.133 | +2.01 |
| Lagged market excess return | +0.006 | +0.16 |

R² = **12.6%**.

Three readings, all of which belong in the record.

1. **The convexity is real but small.** A positive, marginally significant loading
   on |market| is the crisis-convexity claim showing up where it should.
2. **The market exposure is dynamic, not static.** A large negative static beta
   against a large positive volatility-scaled beta is a *time-varying* market
   position, which is precisely Goyal and Jegadeesh's mechanism rather than the
   forecasting mechanism the strategy is sold on.
3. **The exposure replica reproduces 44% of the benefit and fires clause (d).**
   Stripping the intercept and holding only the fitted exposures at the same 15%
   sleeve weight yields +0.586 pp/yr against the sleeve's +1.342.

A reader can reasonably disagree with the verdict, and the number they need is here:
the sleeve's margin over its own replica is **+0.756 pp/yr**, which itself clears
the 0.30 pp/yr threshold. Clause (d) was frozen in *absolute* form — "leaves a
marginal benefit below the materiality threshold" — and is applied as frozen. Had it
been written as a relative share, the verdict would be `unresolved`. The clause is
also ambiguous between "the replica clears the threshold" and "the residual falls
below it"; both readings fire here (the residual delivers −0.443 pp/yr), and the
second is degenerate anyway because an OLS residual is mean-zero by construction.
That ambiguity is [re-decided below](#clause-d-re-read-under-both-readings) rather
than left as a footnote.

Two guards worth naming, because both were bugs found while reading the first run's
output and fixed before the reported run:

- The replica initially **included the regression intercept**. That builds a
  near-riskless asset paying the sleeve's whole +6.42%/yr alpha at roughly a third
  of its volatility; it delivered +1.510 pp/yr, beat the sleeve itself, and fired
  clause (d) on an artefact of the arithmetic. An intercept is by construction the
  part the exposures do *not* explain, so including it in a test of whether
  exposures explain the result is a category error.
- The crisis drawdown-reduction column had its **sign inverted**, reporting every
  improvement as a deterioration.

Both now carry regression tests.

## What this experiment could not do

| Test | Why not |
| --- | --- |
| **Kim, Tse and Wald (2016): remove the volatility scaling** | Not runnable. Removing per-instrument volatility scaling collapses the published pooled *t* from 4.34 to 1.68, which makes it the single most informative test of this strategy. The published series is an aggregate of 58 already-scaled instrument positions and cannot be unwound. |
| **Huang et al. (2020) bootstrap** | An asset-level predictive-regression test on the underlying instruments, not on a portfolio return series. Their finding — that the original pooled *t*=4.34 sits *below* its own 5% bootstrap critical values of 12.53 (wild) and 4.83 (pairs) — stands as prior evidence and is neither confirmed nor rebutted here. |
| **Re-cost the vendor series from its own trades** | The trades are not observable and the workbook states no cost basis. |
| **Correct for survivorship and backfill** | Not estimable from one series. The published magnitude on comparable CTA data is 7.7 pp/yr, Sharpe 0.73 → 0.09. |

The lookback sensitivity above must be read narrowly for the same reason: changing
the lookback moves *this experiment's* estimator, which sizes the risk match and the
scaled comparator. It cannot touch the sleeve's own scaling, which is the vendor's
and is baked into the published aggregate.

## Provenance

Reproducibility details, `as of 2026-08-12`.

| Input | Identity |
| --- | --- |
| AQR time-series momentum, monthly | `Time-Series-Momentum-Factors-Monthly.xlsx`, sheet **`TSMOM Factors`**, column `TSMOM`, sha256 `33470930e2269c0d97be4732ec2d9c27ddbc69ac8133b059a263e27400263eeb`, 139 830 bytes, `Last-Modified: Fri, 26 Jun 2026 15:54:00 GMT`, 497 monthly rows, 1985-01 to 2026-05. Manifest `research/data-manifests/aqr_tsmom_factors_monthly.json`. |
| US equity total return | Ken French `F-F_Research_Data_5_Factors_2x3`, monthly, `Mkt-RF + RF`, sha256 `cbc3724…6ad3b`. French defines the market factor against the US one-month bill, so `Mkt-RF + RF` is an identity, not an approximation. |
| Cash | FRED `TB3MS`, monthly average three-month bill, discount basis, divided by 12. `DGS3MO` and `DFF` are registered and were **not** used: different maturity, frequency, construction and basis. |
| Bond proxy (robustness arm only) | FRED `GS10` through a par-bond duration-and-convexity approximation. **Modelled, `research_grade = False`.** |

The AQR sheet name is pinned as a first-class `SHEET PINNED:` warning on the
manifest: AQR changes URLs, workbook names, sheet names and revisions, and a
manifest that records a hash but not a sheet is not reproducible. A raw-hash
mismatch on AQR or Ken French **aborts** the experiment, because both rebuild their
whole history from the current vintage and a premium computed from an unrecognised
file looks exactly like a good one. FRED appends rather than rewrites, so its hashes
are recorded and reported without aborting.

**The vendor ships its methodology as pictures.** The Definitions, Data Sources and
Disclosures sheets hold 2, 1 and 0 substantive text cells respectively; their content
is four embedded EMF drawings. `data/aqr.py` recovers the text from the EMF record
stream on a best-effort basis and writes it into the manifest, because the
alternative — recording that the vendor documented nothing — is false. What it
recovers, and what it does not:

- The ex-ante volatility model is an exponentially weighted variance of lagged daily
  squared returns with a **60-day centre of mass** and an annualisation factor of
  261, using the estimate at *t−1* on the returns at *t*. This experiment applies the
  identical form at monthly frequency at the same calendar centre of mass (60/21
  months), which is an approximation of the vendor's estimator and not that
  estimator.
- Each position is sized to a **40% ex-ante annualised volatility**, equal-weighted
  across the instruments available at each date; the aggregate runs about 12%/yr.
- The universe is 58 instruments: 9 equity index futures, 13 bond futures, 12 FX
  cross pairs from 10 rates, and 24 commodities.
- **MSCI country index returns and JP Morgan country bond index returns stand in for
  futures returns before futures were available.** Part of the early history is
  therefore not a futures strategy at all, which is why the reconstructed era is
  reported separately and never pooled — and it is the era with by far the largest
  measured marginal benefit (+2.00 pp/yr).
- **No fee, transaction-cost, slippage or financing basis appears anywhere**, in
  cells or in pictures. The Disclosures drawing is generic legal language.

Run: `uv run python -m portfolio_edge.experiments.exp_004_trend_marginal_value
--view-results`. Specification hash
`e9e564f39ebd335808482db79558ddd9fd7f955e1ae3ce4267e9184f8d4a7473`, seed 20260814,
ledger `run_id` `21a1517f295a44fd9ac213b502c1752a`, `results_viewed` recorded.

Four executions of this identical specification hash are in the ledger, each with
its own `results_viewed` entry, plus one earlier development execution against a
scratch ledger whose printed *status line* was seen before any deliberate view. They
are repeated executions of one specification, not four hypotheses, and no parameter
was changed after any of them: the three code changes between the first ledgered run
and the reported one are the intercept, drawdown-sign and cap-reporting corrections
described above, each of which fixes a stated defect rather than moving a threshold.
The intercept fix is the one that matters, and it is reported here precisely because
it *lowered* the number that fires the falsifier, from +1.510 to +0.586, without
changing the verdict.

The specification was frozen before any result was examined; its
`parameters.concretisation_log` records the three substantive fields that were made
executable, each with the reason and a `made_before_any_result: true` flag.

### Departures from the frozen draft, all made before any result

- **The benchmark's bond leg was replaced by cash.**
  [Decision 0002](../decisions/0002-no-research-grade-free-price-source.md)
  establishes that no free price source is research-grade, so no investable bond
  total-return history is available. The equity/bond form survives as a declared
  robustness arm built from a modelled GS10 duration approximation, which moves the
  headline from +1.342 to +1.255 pp/yr. No conclusion rests on it.
- **The volatility lookback stayed at 60 days and moved to monthly frequency.** The
  recovered methodology text confirms 60 days is the vendor's own centre of mass, so
  the frozen number was right and only its frequency had to change.
- **The execution delay became one month** rather than one and five trading days,
  which a monthly series cannot express. One month is strictly more hostile.

---

## Experiment 008 — the products

**Question.** Do the US-listed managed-futures ETFs an investor can actually buy
deliver the exposure the AQR index carries, at a tracking difference their own fee
can account for?

**Exposure delivery is answerable on this window. Alpha is not.** That distinction
governs every number below and is not a disclaimer. Exposure delivery is a loading on
a named benchmark and a difference of means against it, and 46 to 78 months can
measure both. Alpha is a small residual mean, and the **median minimum detectable
alpha at 80% power across the 15 fund-by-specification tests is 12.75 pp/yr** —
larger than any plausible true value. Not one of the 15 intercepts survives an
uncorrected test at 0.05, let alone Benjamini–Hochberg or Holm at 0.10. No falsifier
clause in Experiment 008 reads a *p*-value, by design.

### The screen, and what it excluded

Frozen before any return was downloaded, mechanical, applied in a fixed order, with
only the **first** failure recorded so the funnel adds up.

The frame is the **union of the 2019Q4 and 2025Q4 N-PORT censuses**, 14 742 series.
Experiment 002 could take its frame at the *start* of its window; this one cannot,
because DBMF launched 2019-05, KMLM 2020-12 and CTA 2022-03, and a 2019Q4-only frame
would have excluded the products the question is about by construction. The union
frame retains the funds that died inside the window as well as the ones that
launched, which is the least survivorship-selecting frame this source supports. The
asset floor is applied to the **larger** of a series' two observed net-asset figures,
so a fund that reached the floor and then shrank is not selected out.

| Stage | Removed | Remaining | What was removed |
| --- | ---: | ---: | --- |
| union census | — | 14 742 | every series filing NPORT-P in either quarter |
| `mandate_regex` | 14 682 | **60** | everything whose name names no managed-futures, trend, CTA or systematic-macro mandate |
| `exclusion_regex` | 9 | 51 | single-asset-class and sector trend products: Credit Suisse (name matched "credit"), Virtus Rampart **Equity** Trend, Virtus Rampart **Sector** Trend, Counterpoint High **Yield** Trend, Cambria **Fixed Income** Trend, Return Stacked U.S. **Stocks** & Managed Futures, Return Stacked **Bonds** & Managed Futures, and two more |
| `exchange_traded` | 35 | 16 | the entire mutual-fund shelf, including the three largest managed-futures series in either census — **AQR Managed Futures Strategy Fund at 4.88 bn**, Campbell Systematic Macro 1.97 bn, American Beacon AHL 1.91 bn — and **Fidelity Trend Fund**, a 1958 large-cap growth fund the name pattern catches and the exchange flag removes |
| `minimum_net_assets` (100 m) | 7 | 9 | LFEQ 65.9 m, AHLT 50.3 m, ASMF 28.6 m, MFUT 22.1 m, BTRN 5.4 m, STRN 4.9 m, HFMF 2.1 m |
| `maximum_expense_ratio` (1.50%) | 1 | 8 | **TFPN**, Blueprint Chesapeake Multi-Asset Trend, at **1.96%** |
| `inception_cutoff` (2022-12-31) | 3 | **5** | **FCTE** (2024-07), **IMF** (2025-03), **FFUT** (2025-06) — the 2023–2025 launches, excluded so that three complete calendar years exist |
| `mandate_in_map` | 0 | 5 | nothing; the three funds whose mandate is not a diversified futures programme had already failed earlier |
| `minimum_return_coverage` (36 months) | 0 | **5** | nothing; all five had enough filed months |

**The screen is a rule, not a description of the request.** All three tickers the
project owner named pass, and so do two he did not: **FMF** and **WTMF**. Had the
passing set been exactly the requested set, nothing here would be a screen, and a
test asserts it is not.

**The exchange-traded criterion removes 35 of 51 and it is a decision about
investability, not quality.** Whatever this section concludes, it concludes about the
*listed* shelf. The largest managed-futures programme in either census, AQR's own
mutual fund at 4.88 bn, is not audited here at all.

**Attrition is severe and it is a lower bound.** Of 24 mandate-qualifying series in
the 2019Q4 census, **13 (54.2%, 2.99 bn USD)** are absent from the 2025Q4 census
altogether, and 27 series present in 2025Q4 were absent in 2019Q4. Public N-PORT
filings begin in 2019, so any managed-futures fund that closed before 2019Q4 is
invisible to both censuses.

### The five products

| Ticker | Fund | Fee % | Inception | Filed months | Window |
| --- | --- | ---: | --- | ---: | --- |
| DBMF | iMGP DBi Managed Futures Strategy ETF | 0.85 | 2019-05-07 | 54 | 2021-07…2025-12 |
| CTA | Simplify Managed Futures Strategy ETF | 0.75 | 2022-03-07 | 46 | 2022-03…2025-12 |
| FMF | First Trust Managed Futures Strategy Fund | 0.98 | 2013-08-01 | 78 | 2019-07…2025-12 |
| KMLM | KraneShares Mount Lucas Managed Futures Index Strategy ETF | 0.90 | 2020-12-01 | 60 | 2021-01…2025-12 |
| WTMF | WisdomTree Managed Futures Strategy Fund | 0.66 | 2011-01 | 76 | 2019-09…2025-12 |

Every fee is read from the fund's own **SEC-filed summary prospectus fee table**, with
the accession number and the date read committed in
[`product_facts.json`](../../research/data-manifests/exp_008/product_facts.json). None
is 2-and-20, and the point of saying so is in [the fee error](#two-errors-this-page-corrects).

**DBMF's filed history begins 2021-07, twenty-six months after its prospectus
inception.** EDGAR's series feed lists 20 NPORT-P filings for its current series
identifier and the earliest covers the quarter ending 2021-09-30. Whatever explains
that — a series reorganisation, or earlier filings not associated with this
identifier — the effect on this audit is that **DBMF's effective sample is 54 months,
not 80**, and it is reported as 54 everywhere. FMF's 78 months are the longest history
on the shelf and the only one that spans a pre-COVID month.

### Exposure delivery against the AQR TSMOM index

OLS of the fund's monthly excess return on a constant and the AQR index, Newey–West at
6 lags. The interval is a stationary block bootstrap at the frozen 6-month mean block,
resampling the return and the whole design jointly. `TD` is the raw annualised
difference of means; `MDE₈₀` is the smallest intercept the window could detect at 80%
power.

| Ticker | n | Loading | HAC SE | 95% interval | H1 | H2 | Corr | R² | TD pp/yr | TE pp/yr | MDE₈₀ | Status |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| **DBMF** | 54 | **+0.671** | 0.075 | `[+0.513, +0.829]` | +0.59 | +0.73 | +0.72 | 0.524 | −0.48 | 9.66 | 10.93 | **`exploratory`** |
| CTA | 46 | +0.475 | 0.249 | `[+0.058, +0.991]` | −0.31 | +0.81 | +0.37 | 0.137 | +1.90 | 15.68 | 13.14 | `rejected` |
| FMF | 78 | +0.303 | 0.057 | `[+0.183, +0.420]` | +0.25 | +0.43 | +0.61 | 0.368 | −0.53 | 11.12 | 6.64 | `rejected` |
| KMLM | 60 | +0.245 | 0.137 | `[−0.148, +0.446]` | +0.14 | +0.24 | +0.26 | 0.066 | −1.41 | 15.79 | 16.49 | `rejected` |
| WTMF | 76 | +0.099 | 0.045 | `[+0.003, +0.201]` | +0.10 | +0.11 | +0.20 | 0.042 | +2.31 | 13.66 | 8.94 | `rejected` |

**One product delivers the index's exposure and it is the replication strategy.**
DBMF loads **+0.671** on the AQR series with a 95% interval well clear of the 0.50 bar,
correlates 0.72, explains 52% of its own monthly variance with a single regressor, and
holds the loading across the fixed calendar split (+0.59 then +0.73) and across all 19
rolling 36-month windows (range 0.658 to 0.816, no sign change). Its raw tracking
difference is **−0.48 pp/yr against an 0.85% fee**, so it trailed a *cost-free vendor
index* by less than it charges. That is the exposure result, and it is exactly what a
product that sells replication should look like.

**The other four do not deliver this benchmark's exposure**, and the reasons are not
the same reason.

- **KMLM's shortfall is partly definitional and this must not be read as a defect.**
  The KFA MLM Index holds 22 futures — 11 commodities, 6 currencies, 5 global bond
  markets — and **no equity index futures at all**, while AQR's TSMOM universe holds
  nine. A loading of +0.245 on a benchmark a quarter of whose instruments KMLM does
  not trade is a statement about the *benchmark's* equity content as much as about
  KMLM. Clause (a) fires as frozen; the reader should treat that firing as "KMLM is
  not this index" rather than "KMLM is not trend".
- **CTA has 46 months and an interval from +0.058 to +0.991.** Its point estimate
  misses the bar by 0.025 and its halves are −0.31 then +0.81. Neither number is
  resolvable. Under the frozen rule the point estimate decides, and it is the least
  robust classification on this page.
- **FMF and WTMF are the long histories and the low loadings.** FMF's +0.303 over 78
  months has a tight interval `[+0.183, +0.420]` and 43 rolling windows ranging 0.235
  to 0.483: it stably delivers about a third of the index. WTMF's +0.099 over 76
  months, range 0.033 to 0.115, delivers almost none of it, and its raw tracking
  difference of **+2.31 pp/yr** means it *beat* the index — which is a return finding
  this page is not entitled to make on 76 months and a 13.66 pp/yr tracking error.

**Read every tracking difference against its tracking error.** They run 9.66 to 15.79
pp/yr. A difference of means with that much dispersion over 46 to 78 months is not
resolvable at a percentage point. Clause (c) is a decision rule applied as frozen, not
a measurement — and it fired on nobody.

### The static exposure set: are these products anything more than a market position?

Experiment 004's decisive design, unchanged, run on each product and on the index
itself over the same months.

| Series | Market | Vol-scaled market | \|Market\| | Lagged market | Raw α pp/yr | Shrunk α | MDE₈₀ | R² |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **AQR TSMOM index** (2019-07…2025-12) | **−1.769** | **+1.282** | +0.102 | −0.060 | +0.43 | — | — | 0.266 |
| DBMF | −1.174 | +0.785 | +0.237 | −0.067 | −5.14 | −0.08 | 27.37 | 0.158 |
| KMLM | −0.628 | +0.426 | −0.068 | −0.038 | +6.87 | +0.27 | 17.26 | 0.031 |
| WTMF | −0.373 | +0.446 | −0.015 | −0.035 | +1.80 | +0.13 | 12.75 | 0.241 |
| FMF | −0.363 | +0.315 | +0.065 | +0.035 | −2.59 | −0.22 | 11.62 | 0.041 |
| CTA | −0.053 | −0.214 | +0.296 | +0.110 | −5.52 | −0.29 | 14.93 | 0.158 |
| *VTI, the model-misfit pedestal* | *+1.002* | *−0.005* | *−0.016* | *−0.000* | *+0.42* | — | *1.18* | *0.999* |

**The index row is the control that makes this table readable.** Over these same 78
months a definitionally-trend series shows a large negative static market beta against
a large positive volatility-scaled beta — a *time-varying* market position, which is
Goyal and Jegadeesh's (2018) mechanism showing up again on a six-year window rather
than a thirty-six-year one. Each product's loadings should be read as a distance from
that row, not from zero.

Read that way, **DBMF is the index scaled down by about two thirds on both legs**
(−1.174 / −1.769 = 0.66; +0.785 / +1.282 = 0.61), which is the same 0.67 its direct
loading on the index reports. Three independent measurements agree. **CTA is the
outlier in the other direction**: a static market beta of −0.053 and a *negative*
volatility-scaled loading, which is not the trend exposure profile at all over its 46
months, whatever it is.

**The market-model pedestal is small here and it still matters.** VTI is a
cap-weighted total-market fund, so under a correctly specified model its alpha should
be about minus its three-basis-point fee. Measured over the same window it is −0.32
(CAPM), −0.45 (FF3), −0.49 (FF5+UMD) and +0.42 under the static set, with a detection
threshold of 1.18 pp/yr. Every alpha in the table above carries that offset. It does
not rescue the column and it is not meant to: with MDE₈₀ running 11.6 to 27.4 pp/yr,
the alpha column is unmeasured, not measured and small.

**Shrinkage is measured, not assumed, and it is far more severe here than on index
funds.** Each fund's factor is computed from its own annualised HAC standard error
against a prior standard deviation of 1.25%/yr. The realised factors run **0.016 to
0.218, median 0.070** — against Experiment 002's **0.431** on index funds and the
framework's **0.121** reference. A raw alpha on this shelf is worth about a
fourteenth of itself once shrunk, and quoting one unshrunk would overstate it by more
than an order of magnitude.

### FF5+UMD, and the multiple-testing family

The family is **5 funds × 3 specifications = 15 intercept tests**, not the
specification anyone chose to report. **Zero survive at an uncorrected 0.05, zero
under Benjamini–Hochberg at 0.10 and zero under Holm at 0.10.** Padding the
denominator to every screened series × three specifications (180) leaves zero as well,
which it must: padding with *p* = 1 cannot create a rejection.

The FF5+UMD fits are reported because the family requires them, not because they
inform anything: R² runs 0.075 (KMLM) to 0.321 (WTMF), the largest single loading on
the whole shelf is CMA −0.500 on CTA, and every MDE₈₀ is between 6.94 and 22.38 pp/yr.
A six-factor equity model does not span a futures programme and the table is here to
show that it does not.

### Marginal contribution — declared, run, and NOT a valid comparison

Experiment 004's five-way structure was re-run on each product: a 15% sleeve funded pro
rata from a 60/40 equity/cash benchmark against the same benchmark at a **matched
ex-ante risk budget**.

| Ticker | Whole years | Marginal CE pp/yr | Months with an unwarmed estimator | Risk match holds |
| --- | ---: | ---: | ---: | --- |
| DBMF | 4 | +2.093 | 6 of 48 | **no** |
| CTA | 3 | +1.431 | 2 of 36 | **no** |
| KMLM | 5 | +0.426 | 12 of 60 | **no** |
| FMF | 6 | +0.307 | 6 of 72 | **no** |
| WTMF | 6 | −0.053 | 8 of 72 | **no** |

**Not one of these is a valid marginal comparison, and the column that says so is the
only one worth reading.** The risk-matched comparator is sized from a lagged
exponentially weighted volatility estimator. Experiment 004 had sixty months of
burn-in before its reported window; a fund whose entire filed history is the window has
none, so in the first months the comparator runs at full exposure while the treatment
is de-risked, and the arm credits the sleeve with de-risking — the exact error the
risk-matched comparator exists to remove. The estimator is warmed on each fund's whole
filed history and the certainty equivalent computed only on the whole calendar years
inside it, which is the most that can be done; it is not enough for any fund. These
numbers are reported because they were declared, and they are evidence about the
window, not about the funds. The parallel is Experiment 004's own 0.75-leverage-cap
row, which is reported and labelled invalid for the same structural reason.

A null-case regression test pins this: with a warm-up prefix a zero-excess sleeve
gives a marginal benefit of zero to 1e-6, and without one the same input gives a
spurious positive.

### Cost and tax

**The distribution observable in Form N-PORT turned out to be empty for this whole
shelf, and that is a finding rather than a gap to fill quietly.** Item B.6 reports the
dollar value of distributions *reinvested in shares*. Across **321 fund-months** it is
**identically zero for all five funds** — ETF distributions are paid in cash through
the depository and never appear as fund-level reinvestment. The reader in
`data/nport.py` and its tests are kept, because the refusal is the record: this field
cannot measure distributions for an exchange-traded product.

What can measure tax is each fund's **own SEC-standardised after-tax return table**,
computed by the fund at the highest individual federal marginal rates with no state or
local tax, for a taxable account.

| Ticker | Table as of | Longest period | Before tax %/yr | After tax on distributions %/yr | **Tax drag pp/yr** |
| --- | --- | --- | ---: | ---: | ---: |
| CTA | 2024-12-31 | since inception (3/2022) | 10.93 | 8.40 | **+2.53** |
| DBMF | 2025-12-31 | since inception (5/2019) | 8.28 | 6.19 | **+2.09** |
| KMLM | 2025-12-31 | since inception (12/2020) | 5.77 | 3.96 | **+1.81** |
| WTMF | 2024-12-31 | 10 years | 1.04 | −0.26 | **+1.30** |
| FMF | 2025-12-31 | since inception (8/2013) | 1.32 | 0.56 | **+0.76** |

**The tax drag is two to three times the expense ratio on the two funds that made
money.** For DBMF, 0.85% of fee against 2.09 pp/yr of distribution tax: the fee is the
smaller number by a factor of 2.5. Every one of these funds runs its commodity book
through a Cayman subsidiary whose income is ordinary, and the tables show what that
costs a taxable holder. **In an IRA or a 401(k) this entire column is zero and
irrelevant.** If the owner is deciding where to hold such a fund, this is the number
that decides it, and it is larger than anything else on this page that a product
controls.

**No falsifier clause reads these figures, deliberately.** They were read from the
prospectuses while the product facts were assembled — before any N-PORT return was
downloaded, but visible to the author. A threshold placed on a quantity after seeing
it is not a falsifier. They are measured, reported, and decide nothing, and that
limitation is recorded in the frozen specification rather than repaired by inventing a
bar. A later experiment that wants to grade cost of ownership must freeze its
threshold against a shelf it has not yet priced.

---

## Clause (d), re-read under both readings

Experiment 004's falsifier clause (d), verbatim:

> (d) an attribution on static asset exposures plus a volatility-scaled market
> position **leaves a marginal benefit below the materiality threshold**, i.e. a
> simpler static exposure explains it

**The sentence does not say whose marginal benefit.** Experiment 008 re-runs the
*decision*, not the data: the three deciding quantities are quoted in its frozen
specification from Experiment 004's ledgered artifact and verified against that
artifact at run time, to a tolerance of 1e-6.

| Reading | Deciding quantity | Value | Threshold | Clause fires? | Experiment 004's verdict |
| --- | --- | ---: | ---: | --- | --- |
| **Absolute** — the replica's own marginal benefit clears the threshold | replica marginal CE | **+0.586** | 0.30 | **yes** | **`rejected`** |
| **Relative** — what the attribution *leaves*, the sleeve less the replica | sleeve's margin over its replica | **+0.756** | 0.30 | **no** | **`unresolved`** |

Sleeve +1.342, replica +0.586 (**43.7% of the sleeve**), margin +0.756. Experiment 004
applied the absolute reading, as frozen.

A third reading — that the *residual* must clear the threshold — was considered and is
degenerate: the residual delivers −0.443 pp/yr and an OLS residual is mean-zero by
construction, so it fires whatever the data say.

### Which reading is better justified

**The relative reading, and the argument is about what the clause was for rather than
which answer it gives.**

Clause (d) was frozen to catch one specific failure mode: Goyal and Jegadeesh's (2018)
finding that time-series momentum carries a large embedded time-varying market
position, so that the strategy could be a market position wearing a forecasting
costume. The claim that failure mode makes is that **the exposures *explain* the
result** — and "explains" is inherently a share, not a level.

The absolute reading has a property no falsifier should have: **its bar gets easier to
clear as the sleeve gets better.** A larger sleeve benefit mechanically enlarges the
fitted replica that reproduces part of it, so a stronger result is *more* likely to be
rejected at a fixed explained share. Hold the share the replica explains fixed at
Experiment 004's own 43.7% and scale the effect:

| Sleeve pp/yr | Replica pp/yr | Share explained | Absolute fires? | Relative fires? |
| ---: | ---: | ---: | --- | --- |
| 0.50 | 0.219 | 43.7% | no | **yes** |
| 1.00 | 0.437 | 43.7% | **yes** | no |
| **1.342** | **0.586** | **43.7%** | **yes** | no |
| 5.00 | 2.185 | 43.7% | **yes** | no |
| 50.0 | 21.85 | 43.7% | **yes** | no |

Nothing about the explanation changed down that column. The absolute reading changed
its mind anyway, and in the wrong direction: a sleeve delivering 50 pp/yr of which
56% is unexplained would be rejected for being "explained". The relative reading moves
in the right direction — a large unexplained residue is harder to reject — and that
monotonicity is asserted as a regression test, not only as prose.

**Neither reading is scale-free, and that is the deeper defect.** Both compare a level
in percentage points against an absolute bar. A clause about *explanation* should have
named a **share** — "the replica reproduces more than 60% of the benefit" — and then
neither the level nor the direction of the effect could have moved it.

### The honest answer, and the lesson

**Both readings are defensible on the text as written, and that is the finding.** The
clause named a threshold and a quantity the sentence does not uniquely identify.
Experiment 004 applied one reading as frozen, disclosed the ambiguity in its own
write-up, and reported the number the other reading needs — which is the correct
behaviour and the only reason this re-run was possible at all. The defect is one of
**specification quality, not of conduct**.

The rule that would have prevented it, stated so a later specification can follow it:

> **A falsifier must name its deciding quantity as an expression, not as a description
> in prose, and must state it in units that do not move with the size of the effect.**
> "leaves a marginal benefit below X" names neither. `replica_marginal >= 0.30` or
> `replica_marginal / sleeve_marginal >= 0.60` would each name both.

### What this changes, and what it does not

Under the relative reading Experiment 004's status becomes **`unresolved`** rather than
`rejected` — exactly what its own write-up said it would. **`unresolved` is not a
promotion.** The vendor's cost basis is still unestablished, the post-publication
interval still contains zero and still fails Holm, the standalone Sharpe still fell
1.34 → 0.18 and the geometric return 19.4% → 3.1%, the survivorship and backfill
distortion on comparable CTA data is still 7.7 pp/yr, and `evidence_class:
vendor-series-evaluation` still caps the result at `exploratory`. **Nothing about a
trend sleeve becomes investable because a clause was read the other way.**

Experiment 004's frozen specification, its ledger entries and its recorded status are
untouched. Its result stands as recorded. This is a second, differently-specified look
at the same decision, ledgered separately, and the two must never be described as one
run.

---

## Two errors this page corrects

Both were mine, both were transfers of a verdict to a population it was never measured
on, and both are recorded here rather than quietly fixed.

1. **Experiment 004's verdict was repeated to the project owner as though it applied
   to KMLM, DBMF and CTA.** It evaluated an index. Those products were never tested and
   are differently constructed. Experiment 008 tests them and reaches a *different*
   answer for DBMF — the one that is an explicit replication strategy, and therefore
   the one Experiment 004's own 44%-replica finding should have made most interesting
   rather than least.
2. **Hedge-fund CTA fee evidence was applied to exchange-traded funds.** Bhardwaj,
   Gorton and Rouwenhorst (2014) measure 1994–2012 CTAs whose **fee income was around
   4% of assets** and whose net excess returns were insignificantly different from zero
   against 6.1% gross. The funds here charge **0.66% to 0.98%**, read from their own
   SEC-filed prospectus fee tables. A four-percentage-point fee load does not transfer
   to an 0.85% one, and that study is used nowhere in Experiment 008. The finding it
   *does* support — that the gap between a gross strategy and a net product can exceed
   the entire premium — is exactly what the tax column above measures on the real
   products, and there the number is 0.76 to 2.53 pp/yr rather than 4.

---

## Open questions

- **Does DBMF's exposure delivery survive a longer window and a real cost model?**
  Fifty-four months, one benchmark, and no bid-ask or brokerage. The loading is stable
  across every split this window supports, which is the strongest statement 54 months
  can make and is not a strong statement.
- **Is the AQR index the right benchmark for a shelf that does not all trade the same
  markets?** KMLM's loading is depressed by a benchmark whose universe includes nine
  equity index futures that KMLM's index excludes by construction. A per-fund benchmark
  built from each fund's own stated universe would separate "does not deliver trend"
  from "does not deliver *this* trend", and does not exist here.
- **What is the after-tax ranking of this shelf?** Measured but not decided: the
  prospectus figures were seen before any threshold could be frozen against them, so
  Experiment 008 reports them and grades nothing on them. A later specification must
  freeze its cost-of-ownership bar before pricing the shelf.
- **Does the volatility-scaling result survive at contract level?** The single most
  informative published counter-test cannot be run on any public aggregate. It needs
  contract-level futures histories.
- **Is the residual after the exposure attribution a different exposure or a
  premium?** The attribution can only see the US equity market while the sleeve
  trades 58 instruments across four asset classes, so its 12.6% R² is a *lower*
  bound on how much simple exposures could explain. A multi-asset attribution would
  tighten clause (d) considerably and is the highest-value next step on this
  question.
- **Does any N-PORT return agree with an independent measurement?** Unanswered. No
  cross-source check was obtained for any of the five funds, so Item B.5 is the sole
  measurement of every product return on this page.

## Consequence for this repository

- The framework's open gap that "post-publication trend index returns (2013–2025,
  including 2022) were never verified" is now closed for this vendor series over
  2012–2025: the standalone Sharpe fell to **0.18** and the geometric return to
  **3.1%/yr**, while the marginal portfolio benefit fell only to +1.01 pp/yr with an
  interval that includes zero and does not survive the Holm correction. Decay is
  large in the *series* and small in the *marginal benefit*, and conflating the two
  is the error this experiment exists to prevent.
- Trend is **not promoted**. Under the frozen taxonomy this result cannot exceed
  `exploratory` in any case, because a vendor-series evaluation cannot support more.
- This result and [Experiment 003](rebalancing-policy.md) look at the same phenomenon
  from opposite sides and agree. Experiment 003 found that relative performance
  between equity sleeves *trends* rather than reverses — every variance ratio at every
  horizon exceeds one — which is why its rebalancing policies all lost to
  buy-and-hold. A market in which relative performance trends is one in which a
  trend-following sleeve should pay and a mean-reverting rebalancing rule should not.
  Neither experiment promotes anything, but the two failures point the same way.
- The AQR reader in `research/src/portfolio_edge/data/aqr.py` is reusable for the
  other public AQR datasets. Anything added to it must keep the sheet pin and the
  drawing-text recovery: without them a manifest of an AQR workbook is not
  reproducible and understates what the vendor disclosed.
- **The listed managed-futures shelf is five products, one of which delivers the
  benchmark's exposure.** After a mechanical screen of 14 742 series: 60 name a
  managed-futures mandate, 35 of the 51 survivors are mutual funds rather than ETFs,
  and five clear an asset floor a tenth of Experiment 002's, an expense ceiling two
  and a half times its, and a 2022 inception cutoff. **DBMF is the only one whose
  loading on the AQR index clears 0.50.** Any later work needing an investable trend
  proxy has one candidate and no fallback — a thinner shelf than momentum's, which at
  least had MTUM.
- **A product's fee is the smaller cost on this shelf.** Fees run 0.66% to 0.98%;
  distribution tax drag from the funds' own prospectus tables runs 0.76 to 2.53 pp/yr,
  and is 2.5× the fee for DBMF. In a tax-deferred account it is zero. If a trend
  sleeve is ever held, **where it is held matters more than which product is chosen**,
  and nothing on this page grades the choice because the figures were seen before a
  threshold could be frozen against them.
- **A falsifier must name its deciding quantity as an expression, not as prose, and
  in units that do not move with the size of the effect.** Clause (d) is the worked
  example: an ambiguously specified clause produced a defensible verdict and a
  defensible opposite verdict from the same two numbers. Every specification frozen
  after this one should be read against that rule before it is committed.
- **Form N-PORT cannot measure distributions for an exchange-traded fund.** Item B.6's
  reinvestment figure is identically zero across 321 fund-months on this shelf,
  because ETF distributions are paid in cash. The reader and its tests are kept as the
  record of the refusal; any later work wanting distributions needs Form N-CSR, which
  is unstructured HTML.

## Reproduce it

```sh
cd research
uv run python -m portfolio_edge.experiments.exp_008_managed_futures --build-universe
uv run python -m portfolio_edge.experiments.exp_008_managed_futures --view-results
uv run pytest tests/unit/test_experiments_exp_008_managed_futures.py
uv run pytest tests/integration/test_exp_008_universe_committed.py
```

Reproducibility details for Experiment 008, `as of 2026-08-12`.

| Field | Value |
| --- | --- |
| Specification | [`research/experiments/exp_008_managed_futures_products.yaml`](../../research/experiments/exp_008_managed_futures_products.yaml), hash `2392fbca35bcdbc5f2633dc8fd01911dbf82e92745effe332648eff078c2296d`, seed 20260812 |
| Run kind | **exploratory**, `evidence_class: fund-implementation-audit`; does not consume the final holdout |
| Ledger `run_id` | `3cf8c777d76e4d9094f7c431803b7a2e`, `succeeded` and `results_viewed`. `result.json` sha256 `ca6bfd3f97a2f3e9…` |
| Frame | SEC N-PORT data sets **2019Q4** (8 563 series) and **2025Q4** (12 552), union 14 742, both manifested |
| Returns | Form N-PORT Item B.5 monthly total return per share class; 46–78 months per fund; already net of ongoing expenses and of reinvested distributions |
| Benchmark | AQR TSMOM monthly, the same workbook, sheet and vintage Experiment 004 pinned, raw sha256 `33470930e2269c0d…`; a mismatch **aborts** |
| Factors | Ken French FF5 + momentum, pinned by raw sha256; cash from the same French file as the factors |
| Product facts | [`product_facts.json`](../../research/data-manifests/exp_008/product_facts.json) — every fee, inception and after-tax table read from the fund's own SEC-filed **497K summary prospectus**, with its accession and the date read |
| Universe | [`product_universe.json`](../../research/data-manifests/exp_008/product_universe.json) sha256 `461883abe99cdb58…`, written **before any return was downloaded** |
| Inference | Newey–West HAC at 6 lags; stationary block bootstrap, mean block **6 months frozen not tuned**, 10 000 resamples, 3 and 12 as reported neighbours; joint resampling of the return and the whole design |

### The run history, not only the run that worked

Three executions are in [`research/ledger.jsonl`](../../research/ledger.jsonl): one
`failed` and two `succeeded`.

| Run | Spec | Terminal event | Why |
| --- | --- | --- | --- |
| `b718e47b…` | `d5196929…` | `failed` | The clause (d) **verification guard refused the run**: the sleeve marginal frozen in the specification differed from Experiment 004's ledgered artifact by 0.00057 pp/yr, above the 1e-6 tolerance. The frozen value carried digits that had been supplied rather than read. Corrected from the artifact and recorded in the specification's `correction_log`. **No result had been examined** — the run aborted before any result object existed. |
| `8e225e72…` | `2392fbca…` | `succeeded` | First complete result, on an uncommitted working tree. |
| `3cf8c777…` | `2392fbca…` | `succeeded` | **The run reported here.** Its `result` block is byte-identical to `8e225e72…`; the difference is the git commit. |

One change was made **after** the first successful run and it is reported rather than
folded in silently. The marginal-contribution arm originally warmed its volatility
estimator on the reported window alone, so the risk-matched comparator was unmatched
for the first year of every fund. It now warms on each fund's whole filed history and
reports the count of unwarmed months. FMF moved +0.012 → +0.307 and WTMF −0.193 →
−0.053; the other three did not move, and no falsifier clause reads that arm. The
defect is not fully repairable on this data, which is why every row of that table is
labelled invalid.
