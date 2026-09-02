### Matched pairs on the fund list: does the published recommendation, RSST 30 / VTI 19 / VTV 15 / VXUS 16 / AVDV 10 / IDMO 5 / AVES 5, differ from the same portfolio at RSST 25, from the investor's original eight at the same leverage, or from itself with one holding swapped -- and can 427 months tell?

- **Status:** `exploratory` — a search, not a finding; it may not be quoted as evidence that anything works
- **Run:** `36f14b395e53407f8fdfaee3b4e8e37a`
- **Experiment family:** `exp_016f_matched_pairs`
- **Specification hash:** `68323191bca66ea857826bf29869a00fbed16028af2b104878b84c40c4497888`
- **Run kind:** `exploratory`
- **Evidence class:** `policy-simulation`
- **Falsifier:** There is deliberately NO fixed pp/yr bar in this falsifier. Decision 0010 clause 4 demotes the 2.0 pp/yr and 0.30 pp/yr constants to sensitivities, and decision 0009 clause 1 forbids a verdict stronger than the instrument, so the operative bar IS the instrument's own resolution and it is computed per arm. For each contestant, against each named benchmark separately: (a) `rejected` if the after-cost growth gap point estimate is at or below zero on the full joint window; (b) `rejected` if the arm's gross notional exceeds 1.0, its gap is positive against the unlevered control, and the leverage-matched control attains an equal or higher Sharpe ratio, because the gain is then leveraged beta rather than a construction effect. The clause is restricted to levered arms because an unlevered arm has no leverage to which a gain could be attributed; (c) `unresolved` if the gap is positive but smaller in absolute value than the minimum detectable effect at 80% power computed from that arm's own paired difference series, which must be reported in the same sentence; (d) `unresolved` if the gap exceeds its MDE but its Benjamini-Hochberg adjusted p-value over the declared family exceeds 0.10; (e) `unresolved` if the gap survives (c) and (d) but changes sign anywhere on the declared mapping-perturbation grid, because the mapping is an assumption and a result that lives inside the assumption is not a result about a portfolio; (f) `exploratory` otherwise. Under no outcome may this specification produce a status above `exploratory`; see the freeze note. The whole-experiment status is `exploratory` when at least one arm reaches (f) and `unresolved` when none does, because "no construction was separable from the control on this instrument" is a statement about the instrument.

17 constructions scored on 427 months (1990-11..2026-05), on BASIS-MAPPED funds rather than fund returns. The largest after-cost growth gap is fund_cash_30 at +2.97 pp/yr against control_seventy_thirty_cash, against its own 1.82 pp/yr detection floor at 80% power. 2 of 17 arms separate from their benchmark by more than this design can resolve. Every other arm is `unresolved`, which is a statement about a 427-month joint sample and not about the constructions.

Gross, net-optimistic and net-pessimistic are separate columns and are never collapsed; the spread between them is the cost-model uncertainty.

| Statistic | Units | Gross | Net-optimistic | Net-pessimistic | Interval method |
| --- | --- | --- | --- | --- | --- |
| growth_gap[fund_cash_30 vs control_seventy_thirty_cash] | percentage points per year | not reported | not reported | 2.973 [1.653, 4.285] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[fund_overlay_30 vs control_capweight_levered] | percentage points per year | not reported | not reported | 1.361 [-1.217, 4.155] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[fund_prorata_30 vs control_capweight] | percentage points per year | not reported | not reported | 1.09 [-1.217, 3.514] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[original30 vs control_capweight_levered] | percentage points per year | not reported | not reported | 2.486 [-0.1678, 5.265] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[rec25 vs control_capweight_levered_1268] | percentage points per year | not reported | not reported | 2.2 [-0.02911, 4.539] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[rec30 vs control_capweight_levered] | percentage points per year | not reported | not reported | 2.498 [-0.1547, 5.262] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[rec30_avlv vs control_capweight_levered] | percentage points per year | not reported | not reported | 2.492 [-0.1555, 5.279] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[rec30_avlv_vs_rec30 vs rec30] | percentage points per year | not reported | not reported | -0.005724 [-0.06057, 0.04956] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[rec30_avuv vs control_capweight_levered] | percentage points per year | not reported | not reported | 2.646 [-0.1183, 5.622] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[rec30_avuv_vs_rec30 vs rec30] | percentage points per year | not reported | not reported | 0.1481 [-0.336, 0.6672] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[rec30_dfiv vs control_capweight_levered] | percentage points per year | not reported | not reported | 2.399 [-0.2459, 5.166] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[rec30_dfiv_vs_rec30 vs rec30] | percentage points per year | not reported | not reported | -0.0988 [-0.2912, 0.101] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[rec30_vea_iemg vs control_capweight_levered] | percentage points per year | not reported | not reported | 2.547 [-0.09881, 5.322] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[rec30_vea_iemg_vs_rec30 vs rec30] | percentage points per year | not reported | not reported | 0.04898 [0.002167, 0.09892] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[rec30_vs_original30 vs original30] | percentage points per year | not reported | not reported | 0.01173 [-0.1768, 0.1923] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[rec30_vs_rec25 vs rec25] | percentage points per year | not reported | not reported | 0.5101 [0.2973, 0.7229] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[wm_min_variance vs control_capweight] | percentage points per year | not reported | not reported | 1.838 [-0.1137, 4.139] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |

Statistics with no cost basis:

| Statistic | Units | Value | Interval method | Observations |
| --- | --- | --- | --- | --- |
| minimum_detectable_effect[fund_cash_30 vs control_seventy_thirty_cash] | percentage points per year | 1.821 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[fund_overlay_30 vs control_capweight_levered] | percentage points per year | 3.563 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[fund_prorata_30 vs control_capweight] | percentage points per year | 3.174 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[original30 vs control_capweight_levered] | percentage points per year | 3.329 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[rec25 vs control_capweight_levered_1268] | percentage points per year | 2.832 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[rec30 vs control_capweight_levered] | percentage points per year | 3.383 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[rec30_avlv vs control_capweight_levered] | percentage points per year | 3.365 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[rec30_avlv_vs_rec30 vs rec30] | percentage points per year | 0.08597 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[rec30_avuv vs control_capweight_levered] | percentage points per year | 3.335 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[rec30_avuv_vs_rec30 vs rec30] | percentage points per year | 0.6742 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[rec30_dfiv vs control_capweight_levered] | percentage points per year | 3.353 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[rec30_dfiv_vs_rec30 vs rec30] | percentage points per year | 0.2564 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[rec30_vea_iemg vs control_capweight_levered] | percentage points per year | 3.38 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[rec30_vea_iemg_vs_rec30 vs rec30] | percentage points per year | 0.0682 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[rec30_vs_original30 vs original30] | percentage points per year | 0.257 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[rec30_vs_rec25 vs rec25] | percentage points per year | 0.2951 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[wm_min_variance vs control_capweight] | percentage points per year | 1.975 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 307 |

**Caveats.**
- Funds are basis-mapped. This experiment ranks CONSTRUCTIONS and cannot rank funds.
- AQR's TSMOM is a vendor series and is gross of its own trading costs by omission.
- JPFP has filed no N-PORT; its structure is RSST's, copied, and is an assumption.
- AVES's fee appears nowhere in this repository and is a declared assumption.
- Fund alphas are not charged in the headline arms; the hostile arm charges them.
- Only RSST publishes a distribution tax drag. Every other after-tax cell is not measured.
- The 427-month joint sample is the binding constraint on every conclusion here.
- No sleeve, fund or portfolio is promoted. Decision 0004's non-promotion stands.
