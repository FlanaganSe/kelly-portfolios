### A bond-regime-conditioned Treasury stack: does switching a 20-point RSSB-like leg on when the trailing bond-equity correlation is negative resolve, against the 70% equity + 30% RSST-like reference and against the unconditional stack, what the unconditional stack could not, on 1929-2025 and on the months outside the 1981-2020 bond bull market?

- **Status:** `unresolved` — the available evidence cannot answer the question; this is not a negative result
- **Run:** `88e58977f62e444b8a3df3162d683db1`
- **Experiment family:** `exp_020_conditional_treasury_stack`
- **Specification hash:** `acbe4f8798d22aa5cb442a678a99f9af9732e0131683f59107c287cb05fd9c1f`
- **Run kind:** `exploratory`
- **Evidence class:** `policy-simulation`
- **Falsifier:** There is no fixed pp/yr bar; the operative bar is each comparison's own resolution (decisions 0009 clause 1 and 0010 clause 4). For each arm, against the reference and against the unconditional stack separately, on the full window and on the complement separately, on the primary metric: (a) `rejected` if the arithmetic mean gap point estimate is at or below zero; (b) `unresolved` if the gap is positive but smaller than the minimum detectable effect at 80% power computed from that comparison's own paired difference series, reported in the same row; (c) `unresolved` if the gap exceeds its floor but its Benjamini-Hochberg adjusted Newey-West p-value within the declared family (the four arms, one family per control per window) exceeds 0.10; (d) `unresolved` if the gap survives (b) and (c) but changes sign anywhere on the declared switching-cost band or the declared Treasury-financing band; (e) `exploratory` otherwise. Under no outcome may this specification produce a status above `exploratory`. Comparisons against the cheap, leverage-matched and volatility-matched controls, the era gaps, the episode table, the drawdown table and the regret table are reported and receive NO status. The whole-experiment status is `exploratory` when any scored comparison reaches (e) and `unresolved` otherwise.

16 scored comparisons: four conditioned arms against the reference and the unconditional stack on the full window and its complement. 0 separate from their control by more than the design can resolve. The primary arm (cond36_below0) reads +0.16 [-0.06, +0.38] pp/yr against the reference on 1151 months against a 0.32 floor and -0.15 [-0.33, +0.04] against a 0.23 floor on the 685 months outside the bond bull market, on 39% of months with 18 switches; the unconditional stack reads +0.34 on the same panel. Regret table: minimax action across the term-premium grid is `conditioned`.

Gross, net-optimistic and net-pessimistic are separate columns and are never collapsed; the spread between them is the cost-model uncertainty.

| Statistic | Units | Gross | Net-optimistic | Net-pessimistic | Interval method |
| --- | --- | --- | --- | --- | --- |
| arithmetic_gap[cond36_below0 vs reference on full] | percentage points per year | not reported | not reported | 0.1611 [-0.06216, 0.3844] | Newey-West HAC, 6 lags, 95% normal interval; block bootstrap interval in the diagnostics |
| arithmetic_gap[cond36_below0 vs reference on complement_of_bond_bull] | percentage points per year | not reported | not reported | -0.1456 [-0.3283, 0.03709] | Newey-West HAC, 6 lags, 95% normal interval; block bootstrap interval in the diagnostics |
| arithmetic_gap[cond36_below0 vs unconditional_stack on full] | percentage points per year | not reported | not reported | -0.1872 [-0.4565, 0.08218] | Newey-West HAC, 6 lags, 95% normal interval; block bootstrap interval in the diagnostics |
| arithmetic_gap[cond36_below0 vs unconditional_stack on complement_of_bond_bull] | percentage points per year | not reported | not reported | 0.08692 [-0.2202, 0.394] | Newey-West HAC, 6 lags, 95% normal interval; block bootstrap interval in the diagnostics |
| arithmetic_gap[cond60_below0 vs reference on full] | percentage points per year | not reported | not reported | 0.1524 [-0.0752, 0.38] | Newey-West HAC, 6 lags, 95% normal interval; block bootstrap interval in the diagnostics |
| arithmetic_gap[cond60_below0 vs reference on complement_of_bond_bull] | percentage points per year | not reported | not reported | -0.164 [-0.3593, 0.0313] | Newey-West HAC, 6 lags, 95% normal interval; block bootstrap interval in the diagnostics |
| arithmetic_gap[cond60_below0 vs unconditional_stack on full] | percentage points per year | not reported | not reported | -0.1896 [-0.4651, 0.08585] | Newey-West HAC, 6 lags, 95% normal interval; block bootstrap interval in the diagnostics |
| arithmetic_gap[cond60_below0 vs unconditional_stack on complement_of_bond_bull] | percentage points per year | not reported | not reported | 0.1003 [-0.2126, 0.4132] | Newey-West HAC, 6 lags, 95% normal interval; block bootstrap interval in the diagnostics |
| arithmetic_gap[cond36_below_minus02 vs reference on full] | percentage points per year | not reported | not reported | 0.04262 [-0.1295, 0.2148] | Newey-West HAC, 6 lags, 95% normal interval; block bootstrap interval in the diagnostics |
| arithmetic_gap[cond36_below_minus02 vs reference on complement_of_bond_bull] | percentage points per year | not reported | not reported | -0.1669 [-0.3142, -0.01957] | Newey-West HAC, 6 lags, 95% normal interval; block bootstrap interval in the diagnostics |
| arithmetic_gap[cond36_below_minus02 vs unconditional_stack on full] | percentage points per year | not reported | not reported | -0.3057 [-0.6061, -0.00518] | Newey-West HAC, 6 lags, 95% normal interval; block bootstrap interval in the diagnostics |
| arithmetic_gap[cond36_below_minus02 vs unconditional_stack on complement_of_bond_bull] | percentage points per year | not reported | not reported | 0.06564 [-0.2522, 0.3835] | Newey-West HAC, 6 lags, 95% normal interval; block bootstrap interval in the diagnostics |
| arithmetic_gap[cond36_below_median120 vs reference on full] | percentage points per year | not reported | not reported | 0.09777 [-0.1394, 0.335] | Newey-West HAC, 6 lags, 95% normal interval; block bootstrap interval in the diagnostics |
| arithmetic_gap[cond36_below_median120 vs reference on complement_of_bond_bull] | percentage points per year | not reported | not reported | -0.2225 [-0.4892, 0.04412] | Newey-West HAC, 5 lags, 95% normal interval; block bootstrap interval in the diagnostics |
| arithmetic_gap[cond36_below_median120 vs unconditional_stack on full] | percentage points per year | not reported | not reported | -0.1972 [-0.4742, 0.07988] | Newey-West HAC, 6 lags, 95% normal interval; block bootstrap interval in the diagnostics |
| arithmetic_gap[cond36_below_median120 vs unconditional_stack on complement_of_bond_bull] | percentage points per year | not reported | not reported | 0.2294 [-0.0668, 0.5255] | Newey-West HAC, 5 lags, 95% normal interval; block bootstrap interval in the diagnostics |

Statistics with no cost basis:

| Statistic | Units | Value | Interval method | Observations |
| --- | --- | --- | --- | --- |
| minimum_detectable_effect[cond36_below0 vs reference on full] | percentage points per year | 0.3193 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 1151 |
| minimum_detectable_effect[cond36_below0 vs reference on complement_of_bond_bull] | percentage points per year | 0.2276 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 685 |
| minimum_detectable_effect[cond36_below0 vs unconditional_stack on full] | percentage points per year | 0.3714 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 1151 |
| minimum_detectable_effect[cond36_below0 vs unconditional_stack on complement_of_bond_bull] | percentage points per year | 0.4301 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 685 |
| minimum_detectable_effect[cond60_below0 vs reference on full] | percentage points per year | 0.323 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 1127 |
| minimum_detectable_effect[cond60_below0 vs reference on complement_of_bond_bull] | percentage points per year | 0.2475 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 661 |
| minimum_detectable_effect[cond60_below0 vs unconditional_stack on full] | percentage points per year | 0.3807 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 1127 |
| minimum_detectable_effect[cond60_below0 vs unconditional_stack on complement_of_bond_bull] | percentage points per year | 0.436 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 661 |
| minimum_detectable_effect[cond36_below_minus02 vs reference on full] | percentage points per year | 0.2451 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 1151 |
| minimum_detectable_effect[cond36_below_minus02 vs reference on complement_of_bond_bull] | percentage points per year | 0.1775 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 685 |
| minimum_detectable_effect[cond36_below_minus02 vs unconditional_stack on full] | percentage points per year | 0.4239 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 1151 |
| minimum_detectable_effect[cond36_below_minus02 vs unconditional_stack on complement_of_bond_bull] | percentage points per year | 0.4529 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 685 |
| minimum_detectable_effect[cond36_below_median120 vs reference on full] | percentage points per year | 0.3531 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 1032 |
| minimum_detectable_effect[cond36_below_median120 vs reference on complement_of_bond_bull] | percentage points per year | 0.3175 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 566 |
| minimum_detectable_effect[cond36_below_median120 vs unconditional_stack on full] | percentage points per year | 0.4055 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 1032 |
| minimum_detectable_effect[cond36_below_median120 vs unconditional_stack on complement_of_bond_bull] | percentage points per year | 0.4625 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 566 |

**Caveats.**
- Wrappers are assumed exposure vectors. This ranks constructions and cannot rank funds.
- The bond leg (Goyal-Welch ltr) is a ~20-year bond and its window contains the 1981-2020 bull market; read every gap beside the era and on/off tables.
- Four rules on one signal; the effective trial count is reported and marked unverified.
- The complement window joins two disjoint eras; the HAC and bootstrap treat the join as adjacent months.
- The regret table is arithmetic on stated inputs and carries no interval.
- No pre-2003 TIPS series exists in the panel and none was built.
- No sleeve, fund or portfolio is promoted.
