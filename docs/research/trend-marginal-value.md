# Trend as marginal crisis diversification

**Question.** What does adding a diversified time-series-momentum sleeve do to a
passive portfolio that already exists, measured against the honest control — a
risk-matched increase in cash — rather than against the fully invested portfolio?

**Decision it informs.** Whether a trend sleeve is worth building an investable
implementation for, and what evidence would be needed to promote one. It does not
inform an allocation.

**Status: `rejected`, and the word is narrower than it looks.** What is rejected is
the hypothesis that *this vendor series* adds material marginal value that a simpler
exposure cannot reproduce. Trend as a strategy is not rejected, and nothing here
establishes that an investable trend product is or is not worth holding.

> **This is a vendor-series evaluation, NOT an independent replication.** The series
> is authored and maintained by AQR, a firm that sells the strategy, and the workbook
> states that AQR reconstructs the full history each time the returns are updated. An
> independent reimplementation would require contract-level futures histories, roll
> conventions, collateral returns, execution assumptions and point-in-time market
> availability. None of those are inputs here. `evidence_class:
> vendor-series-evaluation` is frozen in the specification so this cannot be
> renegotiated at write-up time.

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

## Open questions

- **Does an investable trend product deliver any of this?** Unanswerable here. CTA
  excess returns net of fees were insignificantly different from zero over 1994–2012
  while gross excess returns were 6.1%, with fee income around 4% of assets
  ([Bhardwaj, Gorton and Rouwenhorst 2014](https://doi.org/10.1093/rfs/hhu040)). The
  fee columns in this experiment are this repository's assumptions, not the vendor's
  disclosure. Answering it needs a fund-level audit with a licensed total-return
  source, which Decision 0002 says does not currently exist here.
- **Does the volatility-scaling result survive at contract level?** The single most
  informative published counter-test cannot be run on any public aggregate. It needs
  contract-level futures histories.
- **Is the residual after the exposure attribution a different exposure or a
  premium?** The attribution can only see the US equity market while the sleeve
  trades 58 instruments across four asset classes, so its 12.6% R² is a *lower*
  bound on how much simple exposures could explain. A multi-asset attribution would
  tighten clause (d) considerably and is the highest-value next step on this
  question.

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
