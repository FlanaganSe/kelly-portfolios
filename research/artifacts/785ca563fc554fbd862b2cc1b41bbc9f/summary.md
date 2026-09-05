### Actual filed fund returns for complete published portfolios and fixed VTV/SPMO substitutions

- **Status:** `exploratory` — a search, not a finding; it may not be quoted as evidence that anything works
- **Run:** `785ca563fc554fbd862b2cc1b41bbc9f`
- **Experiment family:** `exp_030_live_fund_portfolios`
- **Specification hash:** `86f7a21cb5d8a46e89c3f07621143de5c99903bee5c90be8f006fdc1a3ed4ac5`
- **Run kind:** `exploratory`
- **Evidence class:** `policy-simulation`
- **Falsifier:** Report signed paired growth gaps and intervals for each fixed comparison. A zero or negative realised gap contradicts improvement on that window; intervals spanning zero leave the historical estimate unresolved. No outcome promotes or permanently rejects a fund, forecasts outperformance odds, or identifies an optimal allocation.

Fixed fund substitutions evaluated inside three complete published portfolios using filed NAV total returns, drifting weights and paid annual execution. Short common histories and descriptive intervals cannot establish a future winner.

Gross, net-optimistic and net-pessimistic are separate columns and are never collapsed; the spread between them is the cost-model uncertainty.

| Statistic | Units | Gross | Net-optimistic | Net-pessimistic | Interval method |
| --- | --- | --- | --- | --- | --- |
| log_growth_gap[value-lean\|5bp\|unchanged vs cheap] | percentage points per year | not reported | 1.037 [-0.4004, 2.615] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[value-lean\|5bp\|avuv vs unchanged] | percentage points per year | not reported | -0.07654 [-1.041, 0.9631] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[value-lean\|5bp\|avuv vs cheap] | percentage points per year | not reported | 0.9607 [-0.749, 2.817] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[value-lean\|5bp\|spmo vs unchanged] | percentage points per year | not reported | 0.3034 [-0.1273, 0.7502] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[value-lean\|5bp\|spmo vs cheap] | percentage points per year | not reported | 1.341 [-0.2521, 2.894] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[value-lean\|5bp\|both vs unchanged] | percentage points per year | not reported | 0.2295 [-0.7138, 1.255] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[value-lean\|5bp\|both vs cheap] | percentage points per year | not reported | 1.267 [-0.4885, 3.037] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[value-lean\|25bp\|unchanged vs cheap] | percentage points per year | not reported | not reported | 1.036 [-0.4005, 2.613] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[value-lean\|25bp\|avuv vs unchanged] | percentage points per year | not reported | not reported | -0.07652 [-1.042, 0.9623] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[value-lean\|25bp\|avuv vs cheap] | percentage points per year | not reported | not reported | 0.9595 [-0.7498, 2.814] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[value-lean\|25bp\|spmo vs unchanged] | percentage points per year | not reported | not reported | 0.3029 [-0.1274, 0.7497] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[value-lean\|25bp\|spmo vs cheap] | percentage points per year | not reported | not reported | 1.339 [-0.2531, 2.892] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[value-lean\|25bp\|both vs unchanged] | percentage points per year | not reported | not reported | 0.2291 [-0.7134, 1.255] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[value-lean\|25bp\|both vs cheap] | percentage points per year | not reported | not reported | 1.265 [-0.4896, 3.035] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[with-trend\|5bp\|unchanged vs cheap] | percentage points per year | not reported | 0.2701 [-3.595, 4.805] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[with-trend\|5bp\|avuv vs unchanged] | percentage points per year | not reported | -0.102 [-1.598, 1.406] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[with-trend\|5bp\|avuv vs cheap] | percentage points per year | not reported | 0.168 [-4.411, 5.458] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[with-trend\|5bp\|spmo vs unchanged] | percentage points per year | not reported | 0.5713 [0.06914, 1.049] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[with-trend\|5bp\|spmo vs cheap] | percentage points per year | not reported | 0.8413 [-2.911, 5.108] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[with-trend\|5bp\|both vs unchanged] | percentage points per year | not reported | 0.4734 [-0.9874, 1.848] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[with-trend\|5bp\|both vs cheap] | percentage points per year | not reported | 0.7434 [-3.707, 5.795] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[with-trend\|25bp\|unchanged vs cheap] | percentage points per year | not reported | not reported | 0.2689 [-3.597, 4.803] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[with-trend\|25bp\|avuv vs unchanged] | percentage points per year | not reported | not reported | -0.1021 [-1.599, 1.404] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[with-trend\|25bp\|avuv vs cheap] | percentage points per year | not reported | not reported | 0.1667 [-4.414, 5.458] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[with-trend\|25bp\|spmo vs unchanged] | percentage points per year | not reported | not reported | 0.5706 [0.06914, 1.049] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[with-trend\|25bp\|spmo vs cheap] | percentage points per year | not reported | not reported | 0.8394 [-2.91, 5.106] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[with-trend\|25bp\|both vs unchanged] | percentage points per year | not reported | not reported | 0.4724 [-0.9889, 1.847] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[with-trend\|25bp\|both vs cheap] | percentage points per year | not reported | not reported | 0.7413 [-3.709, 5.791] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[cautious\|5bp\|unchanged vs cheap] | percentage points per year | not reported | 0.03895 [-2.246, 2.677] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[cautious\|5bp\|avuv vs unchanged] | percentage points per year | not reported | -0.05935 [-0.8179, 0.7739] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[cautious\|5bp\|avuv vs cheap] | percentage points per year | not reported | -0.0204 [-2.598, 2.997] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[cautious\|5bp\|spmo vs unchanged] | percentage points per year | not reported | 0.3061 [0.01416, 0.5572] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[cautious\|5bp\|spmo vs cheap] | percentage points per year | not reported | 0.345 [-1.881, 2.812] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[cautious\|5bp\|both vs unchanged] | percentage points per year | not reported | 0.2479 [-0.5155, 0.9686] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[cautious\|5bp\|both vs cheap] | percentage points per year | not reported | 0.2868 [-2.253, 3.121] | not reported | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[cautious\|25bp\|unchanged vs cheap] | percentage points per year | not reported | not reported | 0.03962 [-2.244, 2.674] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[cautious\|25bp\|avuv vs unchanged] | percentage points per year | not reported | not reported | -0.05931 [-0.819, 0.7729] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[cautious\|25bp\|avuv vs cheap] | percentage points per year | not reported | not reported | -0.01969 [-2.601, 2.994] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[cautious\|25bp\|spmo vs unchanged] | percentage points per year | not reported | not reported | 0.3057 [0.01411, 0.5566] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[cautious\|25bp\|spmo vs cheap] | percentage points per year | not reported | not reported | 0.3453 [-1.88, 2.81] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[cautious\|25bp\|both vs unchanged] | percentage points per year | not reported | not reported | 0.2475 [-0.5168, 0.9678] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |
| log_growth_gap[cautious\|25bp\|both vs cheap] | percentage points per year | not reported | not reported | 0.2871 [-2.252, 3.119] | paired stationary bootstrap, joint fund rows; reexecuted paths; mean block 6 months, 2000 draws, percentile 95% |

**Caveats.**
- Current surviving products selected after inspecting overlapping history; no holdout.
- Broad 65/35 controls preserve SCHP capital weights, not risk, beta or leverage.
- Returns include fund internal costs; investor execution is assumed, taxes omitted.
- Roundtrip 5/25 bp means 2.5/12.5 bp per dollar on each side; no exit sale.
- Initial purchase cost enters first return and first rolling twelve-month window.
- Month-end drawdown misses intramonth lows; only 30 or 54 months cover few regimes.
- Rolling underperformance describes overlapping realised windows, not forecast odds.
- Source hashes identify exact bytes, not historical availability of revised filings.
