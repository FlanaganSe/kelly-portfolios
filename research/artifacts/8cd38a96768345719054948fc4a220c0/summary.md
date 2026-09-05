### Rebuild Cautious's defensive half using actual fund NAV and observed inflation

- **Status:** `exploratory` — a search, not a finding; it may not be quoted as evidence that anything works
- **Run:** `8cd38a96768345719054948fc4a220c0`
- **Experiment family:** `exp_033_cautious_defensive_budget`
- **Specification hash:** `2b65872a857cba65fb25e2d48874bbca1a1d88603cea12450fe3a2f05edef026`
- **Run kind:** `exploratory`
- **Evidence class:** `policy-simulation`
- **Falsifier:** Report paired growth-gap intervals and nominal/real downside for all fixed arms. Reversals across the two differently constructed histories expose scope dependence. No selected historical winner, retirement claim or long-run shortfall probability.

Fixed defensive-half substitutions in actual Cautious and a separately labelled longer no-trend portfolio, with paid execution and purchasing-power outcomes. No defensive allocation selected and no withdrawal adequacy tested.

Gross, net-optimistic and net-pessimistic are separate columns and are never collapsed; the spread between them is the cost-model uncertainty.

| Statistic | Units | Gross | Net-optimistic | Net-pessimistic | Interval method |
| --- | --- | --- | --- | --- | --- |
| log_gap[actual_cautious\|5bp\|schp vs cheap] | percentage points per year | not reported | 0.03895 [-2.185, 2.808] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|5bp\|short_tips vs schp] | percentage points per year | not reported | 0.1315 [-0.8439, 1.159] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|5bp\|short_tips vs cheap] | percentage points per year | not reported | 0.1704 [-2.442, 3.005] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|5bp\|bills vs schp] | percentage points per year | not reported | -0.3245 [-1.79, 1.07] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|5bp\|bills vs cheap] | percentage points per year | not reported | -0.2856 [-3.236, 2.9] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|5bp\|intermediate_treasury vs schp] | percentage points per year | not reported | -0.04884 [-1.08, 0.9731] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|5bp\|intermediate_treasury vs cheap] | percentage points per year | not reported | -0.009887 [-2.504, 2.837] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|5bp\|short_tips_bills vs schp] | percentage points per year | not reported | -0.09596 [-1.299, 1.086] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|5bp\|short_tips_bills vs cheap] | percentage points per year | not reported | -0.05702 [-2.812, 2.931] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|5bp\|schp_bills vs schp] | percentage points per year | not reported | -0.1603 [-0.888, 0.5373] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|5bp\|schp_bills vs cheap] | percentage points per year | not reported | -0.1213 [-2.615, 2.789] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|5bp\|cheap vs schp] | percentage points per year | not reported | -0.03895 [-2.808, 2.185] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|25bp\|schp vs cheap] | percentage points per year | not reported | not reported | 0.03962 [-2.186, 2.805] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|25bp\|short_tips vs schp] | percentage points per year | not reported | not reported | 0.1313 [-0.8441, 1.159] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|25bp\|short_tips vs cheap] | percentage points per year | not reported | not reported | 0.1709 [-2.442, 3.001] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|25bp\|bills vs schp] | percentage points per year | not reported | not reported | -0.3253 [-1.79, 1.07] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|25bp\|bills vs cheap] | percentage points per year | not reported | not reported | -0.2856 [-3.238, 2.898] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|25bp\|intermediate_treasury vs schp] | percentage points per year | not reported | not reported | -0.04886 [-1.08, 0.9735] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|25bp\|intermediate_treasury vs cheap] | percentage points per year | not reported | not reported | -0.009237 [-2.506, 2.835] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|25bp\|short_tips_bills vs schp] | percentage points per year | not reported | not reported | -0.09643 [-1.3, 1.086] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|25bp\|short_tips_bills vs cheap] | percentage points per year | not reported | not reported | -0.05681 [-2.812, 2.929] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|25bp\|schp_bills vs schp] | percentage points per year | not reported | not reported | -0.1606 [-0.8888, 0.5369] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|25bp\|schp_bills vs cheap] | percentage points per year | not reported | not reported | -0.121 [-2.613, 2.788] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[actual_cautious\|25bp\|cheap vs schp] | percentage points per year | not reported | not reported | -0.03962 [-2.805, 2.186] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|5bp\|schp vs cheap] | percentage points per year | not reported | 0.5079 [-0.2031, 1.263] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|5bp\|short_tips vs schp] | percentage points per year | not reported | 1.391 [-0.03851, 2.997] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|5bp\|short_tips vs cheap] | percentage points per year | not reported | 1.899 [0.05217, 3.989] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|5bp\|bills vs schp] | percentage points per year | not reported | 1.716 [-0.4242, 4.077] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|5bp\|bills vs cheap] | percentage points per year | not reported | 2.224 [-0.2621, 4.939] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|5bp\|intermediate_treasury vs schp] | percentage points per year | not reported | -0.8803 [-2.139, 0.2389] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|5bp\|intermediate_treasury vs cheap] | percentage points per year | not reported | -0.3723 [-1.457, 0.7441] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|5bp\|short_tips_bills vs schp] | percentage points per year | not reported | 1.555 [-0.2037, 3.514] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|5bp\|short_tips_bills vs cheap] | percentage points per year | not reported | 2.063 [-0.08967, 4.455] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|5bp\|schp_bills vs schp] | percentage points per year | not reported | 0.8731 [-0.2087, 2.072] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|5bp\|schp_bills vs cheap] | percentage points per year | not reported | 1.381 [-0.1158, 2.985] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|5bp\|cheap vs schp] | percentage points per year | not reported | -0.5079 [-1.263, 0.2031] | not reported | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|25bp\|schp vs cheap] | percentage points per year | not reported | not reported | 0.5078 [-0.203, 1.263] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|25bp\|short_tips vs schp] | percentage points per year | not reported | not reported | 1.39 [-0.03857, 2.996] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|25bp\|short_tips vs cheap] | percentage points per year | not reported | not reported | 1.898 [0.05219, 3.987] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|25bp\|bills vs schp] | percentage points per year | not reported | not reported | 1.715 [-0.4246, 4.075] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|25bp\|bills vs cheap] | percentage points per year | not reported | not reported | 2.222 [-0.2624, 4.937] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|25bp\|intermediate_treasury vs schp] | percentage points per year | not reported | not reported | -0.8802 [-2.14, 0.239] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|25bp\|intermediate_treasury vs cheap] | percentage points per year | not reported | not reported | -0.3725 [-1.459, 0.7428] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|25bp\|short_tips_bills vs schp] | percentage points per year | not reported | not reported | 1.554 [-0.2037, 3.513] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|25bp\|short_tips_bills vs cheap] | percentage points per year | not reported | not reported | 2.062 [-0.09053, 4.454] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|25bp\|schp_bills vs schp] | percentage points per year | not reported | not reported | 0.8725 [-0.2092, 2.07] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|25bp\|schp_bills vs cheap] | percentage points per year | not reported | not reported | 1.38 [-0.1156, 2.985] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |
| log_gap[no_trend_diagnostic\|25bp\|cheap vs schp] | percentage points per year | not reported | not reported | -0.5078 [-1.263, 0.203] | paired joint fund-row stationary bootstrap; reexecuted paths; 6-month blocks, 2000 draws, percentile 95% |

**Caveats.**
- Actual Cautious: 30 months. The 54-month diagnostic replaces RSST with VTI.
- CPI 2025-10 missing: real downside only on observed dates, not complete-month risk.
- Endpoint real growth is measurable; CPI is monthly, not exact trading-date prices.
- No withdrawals, taxes, independent holdout or retirement-proof claim.
- Common realised inflation cancels from paired nominal/real growth gaps.
- Source hashes identify bytes, not point-in-time fund selection or availability.
