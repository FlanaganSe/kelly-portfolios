### The trend leg rebuilt from live, net, fund-reported returns: what did managed-futures investors actually earn, and how much did the vendor index overstate it?

- **Status:** `unresolved` — the available evidence cannot answer the question; this is not a negative result
- **Run:** `d7e531ab2eea4677a37519c4055e73bb`
- **Experiment family:** `exp_012_live_trend`
- **Specification hash:** `49e604fc422f4851e5c076f87a81f7f78c205e4cc4a5c21178f3df91a2000a70`
- **Run kind:** `exploratory`
- **Evidence class:** `fund-implementation-audit`
- **Falsifier:** THE OVERLAY CLAIM is rejected when ANY of: (a) the matched-volatility gap `sigma_p (S_portfolio - S_benchmark)` for `equity_plus_trend_50` against the leverage-matched control is at or below zero on the live window, net of the declared costs charged inside the simulation; (b) a leverage-matched control attains a Sharpe ratio at or above the overlay portfolio's, in which case the gain is leveraged beta. It is `unresolved` when (i) the gap's bootstrap interval includes zero, or (ii) the gap is smaller than the minimum detectable effect reported beside it. On a window of roughly 78 months `unresolved` is the EXPECTED outcome and is not a failure of the experiment: it is the measurement that the window, and no longer the series, is the binding constraint. THE VENDOR CLAIM has no falsifier clause and deliberately produces no status of its own, because it is an estimate rather than a test. It is reported as a point estimate with a Newey-West interval, and the repository's 7.7 pp/yr bound is compared with that interval rather than with the point estimate. Under no outcome may this specification produce a status above `exploratory`.

the gap is +1.27 pp/yr but its bootstrap interval [-2.62, +4.95] includes zero, and the minimum detectable effect is 4.76 pp/yr over 78 months. The window, not the series, is now the binding constraint.

Gross, net-optimistic and net-pessimistic are separate columns and are never collapsed; the spread between them is the cost-model uncertainty.

| Statistic | Units | Gross | Net-optimistic | Net-pessimistic | Interval method |
| --- | --- | --- | --- | --- | --- |
| live_managed_futures_excess_return | percent per year | not reported | 2.844 (no interval: the interval that decides is on the difference from the vendor series and on the portfolio gap, and both are reported) | not reported | not reported |
| vendor_alpha_against_the_live_funds | percentage points per year | -1.355 [-8.234, 5.523] | not reported | not reported | Newey-West HAC, 3 lags, normal 95% interval |
| vendor_less_live_at_matched_volatility | percentage points per year | -2.615 [-10.91, 5.679] | not reported | not reported | Newey-West HAC on the paired difference, normal 95% interval |
| net_geometric_return[equity_only] | percent per year | not reported | 15.28 (no interval: a geometric return over one realised path has no sampling interval that is not a restatement of the arithmetic mean's; the interval that decides is on the matched-volatility gap, which is reported) | not reported | not reported |
| net_geometric_return[equity_plus_trend_50] | percent per year | not reported | 16.58 (no interval: a geometric return over one realised path has no sampling interval that is not a restatement of the arithmetic mean's; the interval that decides is on the matched-volatility gap, which is reported) | not reported | not reported |
| net_geometric_return[equity_levered_135] | percent per year | not reported | 18.97 (no interval: a geometric return over one realised path has no sampling interval that is not a restatement of the arithmetic mean's; the interval that decides is on the matched-volatility gap, which is reported) | not reported | not reported |
| net_geometric_return[equity_levered_150] | percent per year | not reported | 20.45 (no interval: a geometric return over one realised path has no sampling interval that is not a restatement of the arithmetic mean's; the interval that decides is on the matched-volatility gap, which is reported) | not reported | not reported |
| matched_volatility_gap[equity_plus_trend_50 vs equity_levered_150] | percentage points per year | not reported | 1.268 [-2.622, 4.953] | not reported | stationary block bootstrap, 95% percentile, mean block 12m, 10000 resamples, paired rows |
| matched_volatility_gap[equity_plus_trend_50 vs equity_only] | percentage points per year | not reported | 1.071 [-2.857, 4.772] | not reported | stationary block bootstrap, 95% percentile, mean block 12m, 10000 resamples, paired rows |
| break_even_haircut_on_live_trend[vs equity_levered_150] | percentage points per year | not reported | 2.537 (no interval: a deterministic function of the sample mean; its uncertainty is the gap's and is reported there) | not reported | not reported |
| break_even_haircut_on_live_trend[vs equity_only] | percentage points per year | not reported | 2.142 (no interval: a deterministic function of the sample mean; its uncertainty is the gap's and is reported there) | not reported | not reported |

**Caveats.**
- EXPLORATORY AND UNPROMOTABLE. This specification was written after Experiment 011's result was known and after its unresolved verdict was traced to the vendor series. The index construction, the fund-level screen and the window were chosen with that in view. No re-run converts that into a confirmatory result.
- ITEM B.5 IS UNAUDITED AND SELF-REPORTED. Form N-PORT General Instruction G lets each filer use its own internal methodology, so two funds' returns are not guaranteed to be computed identically. The repository's cross-source check returned an HTTP error for all 44 US and all 25 ex-US tickers, so Item B.5 is the SOLE measurement of every fund return here and no independent corroboration exists.
- SURVIVORSHIP IS BOUNDED, NOT REMOVED, AND EVERY ATTRITION FIGURE IS A LOWER BOUND. Public N-PORT filings begin in 2019, so a managed-futures fund that closed before 2019Q4 is invisible to both censuses. Worse for this design: a fund that both launched after 2019Q4 and closed before 2025Q4 is in NEITHER census and is missing from the index entirely. Both omissions delete funds that failed.
- THE WINDOW IS THE BINDING CONSTRAINT. Roughly 78 months cannot resolve a portfolio effect of the size at issue; the minimum detectable effect at 80% power is reported beside every gap and is several times the point estimate. A gap below that floor is not evidence of an effect and must not be read as one.
- THE TREND LEG CARRIES A ZERO MODELLED FEE, and that is not optimism. Item B.5 is already net of the fund's own ongoing fees, its trading costs, its slippage and its roll. Charging Experiment 011's 1.45% on top would deduct the fee twice.
- THE INDEX IS EQUAL-WEIGHT ACROSS FUNDS, NOT ACROSS DOLLARS. It is what the average managed-futures fund delivered, not what the average managed-futures dollar earned. N-PORT gives net assets at two dates only, which cannot support a monthly asset weighting.
- THE FUND POPULATION IS NOT CONSTANT. It ranges from about eighteen to about thirty-three funds a month, and the composition changes as funds launch and die. That is the design -- a fixed population would be a survivorship screen -- but it means no two months' index values rest on the same funds.
- THE TWO BENCHMARKS ARE NEVER COMBINED. The leverage-matched control answers whether this is alpha; the unlevered control answers what a non-borrowing investor gives up.
- PRETAX everywhere, and managed futures are the worst case for that omission. The simulation holds no tax lots, so it cannot know a basis, so it may not price a realisation.
- No sleeve is promoted by this result and decision 0004 stands.
