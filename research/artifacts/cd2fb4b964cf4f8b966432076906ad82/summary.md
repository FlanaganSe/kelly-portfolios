### The recommended portfolio as a single object: does RSST 25 / VTI 24 / VTV 15 / VXUS 16 / AVDV 10 / IDMO 5 / AVES 5 beat a leverage-matched cheap index, the investor's original eight-fund proposal, the previous recommendation, or a variant holding AVUV instead of VTV — and can 427 months tell?

- **Status:** `exploratory` — a search, not a finding; it may not be quoted as evidence that anything works
- **Run:** `cd2fb4b964cf4f8b966432076906ad82`
- **Experiment family:** `exp_016e_final_construction`
- **Specification hash:** `3a86ef6f04a37c13634304d0b4a6de32b4ea56c5fe302ce32ef6e6c0d8d7189e`
- **Run kind:** `exploratory`
- **Evidence class:** `policy-simulation`
- **Falsifier:** There is deliberately NO fixed pp/yr bar in this falsifier. Decision 0010 clause 4 demotes the 2.0 pp/yr and 0.30 pp/yr constants to sensitivities, and decision 0009 clause 1 forbids a verdict stronger than the instrument, so the operative bar IS the instrument's own resolution and it is computed per arm. For each contestant, against each named benchmark separately: (a) `rejected` if the after-cost growth gap point estimate is at or below zero on the full joint window; (b) `rejected` if the arm's gross notional exceeds 1.0, its gap is positive against the unlevered control, and the leverage-matched control attains an equal or higher Sharpe ratio, because the gain is then leveraged beta rather than a construction effect. The clause is restricted to levered arms because an unlevered arm has no leverage to which a gain could be attributed; (c) `unresolved` if the gap is positive but smaller in absolute value than the minimum detectable effect at 80% power computed from that arm's own paired difference series, which must be reported in the same sentence; (d) `unresolved` if the gap exceeds its MDE but its Benjamini-Hochberg adjusted p-value over the declared family exceeds 0.10; (e) `unresolved` if the gap survives (c) and (d) but changes sign anywhere on the declared mapping-perturbation grid, because the mapping is an assumption and a result that lives inside the assumption is not a result about a portfolio; (f) `exploratory` otherwise. Under no outcome may this specification produce a status above `exploratory`; see the freeze note. The whole-experiment status is `exploratory` when at least one arm reaches (f) and `unresolved` when none does, because "no construction was separable from the control on this instrument" is a statement about the instrument.

15 constructions scored on 427 months (1990-11..2026-05), on BASIS-MAPPED funds rather than fund returns. The largest after-cost growth gap is fund_cash_30 at +2.97 pp/yr against control_seventy_thirty_cash, against its own 1.82 pp/yr detection floor at 80% power. 3 of 15 arms separate from their benchmark by more than this design can resolve. Every other arm is `unresolved`, which is a statement about a 427-month joint sample and not about the constructions.

Gross, net-optimistic and net-pessimistic are separate columns and are never collapsed; the spread between them is the cost-model uncertainty.

| Statistic | Units | Gross | Net-optimistic | Net-pessimistic | Interval method |
| --- | --- | --- | --- | --- | --- |
| growth_gap[avuv_for_vtv vs control_capweight_levered_1268] | percentage points per year | not reported | not reported | 2.35 [0.04735, 4.93] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[avuv_for_vtv_matched_loadings vs control_capweight_levered_1268] | percentage points per year | not reported | not reported | 2.324 [0.04132, 4.878] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[fund_cash_30 vs control_seventy_thirty_cash] | percentage points per year | not reported | not reported | 2.973 [1.656, 4.305] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[fund_overlay_30 vs control_capweight_levered] | percentage points per year | not reported | not reported | 1.361 [-1.148, 4.163] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[fund_prorata_30 vs control_capweight] | percentage points per year | not reported | not reported | 1.09 [-1.193, 3.523] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[investor_original_eight vs control_capweight_levered] | percentage points per year | not reported | not reported | 2.486 [-0.06905, 5.308] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[previous_no_trend vs control_capweight] | percentage points per year | not reported | not reported | 0.5094 [0.2389, 0.786] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[previous_recommendation vs control_capweight_levered_1268] | percentage points per year | not reported | not reported | 1.921 [-0.1547, 4.171] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[recommended vs control_capweight_levered_1268] | percentage points per year | not reported | not reported | 2.2 [0.05084, 4.571] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[recommended_matched_loadings vs control_capweight_levered_1268] | percentage points per year | not reported | not reported | 2.258 [0.07142, 4.677] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[recommended_no_trend vs control_capweight] | percentage points per year | not reported | not reported | 0.7996 [0.3582, 1.31] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[recommended_vs_avuv vs avuv_for_vtv] | percentage points per year | not reported | not reported | -0.1506 [-0.6774, 0.3406] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[recommended_vs_original vs investor_original_eight] | percentage points per year | not reported | not reported | -0.4984 [-0.7742, -0.2274] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[recommended_vs_previous vs previous_recommendation] | percentage points per year | not reported | not reported | 0.2787 [0.04549, 0.5551] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |
| growth_gap[wm_min_variance vs control_capweight] | percentage points per year | not reported | not reported | 1.838 [-0.1365, 4.183] | stationary block bootstrap on the joint panel, whole rows, mean block 12 months, 10000 resamples, 95% percentile |

Statistics with no cost basis:

| Statistic | Units | Value | Interval method | Observations |
| --- | --- | --- | --- | --- |
| minimum_detectable_effect[avuv_for_vtv vs control_capweight_levered_1268] | percentage points per year | 2.804 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[avuv_for_vtv_matched_loadings vs control_capweight_levered_1268] | percentage points per year | 2.794 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[fund_cash_30 vs control_seventy_thirty_cash] | percentage points per year | 1.821 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[fund_overlay_30 vs control_capweight_levered] | percentage points per year | 3.563 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[fund_prorata_30 vs control_capweight] | percentage points per year | 3.174 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[investor_original_eight vs control_capweight_levered] | percentage points per year | 3.329 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[previous_no_trend vs control_capweight] | percentage points per year | 0.315 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[previous_recommendation vs control_capweight_levered_1268] | percentage points per year | 2.755 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[recommended vs control_capweight_levered_1268] | percentage points per year | 2.832 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[recommended_matched_loadings vs control_capweight_levered_1268] | percentage points per year | 2.851 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[recommended_no_trend vs control_capweight] | percentage points per year | 0.47 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[recommended_vs_avuv vs avuv_for_vtv] | percentage points per year | 0.6761 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[recommended_vs_original vs investor_original_eight] | percentage points per year | 0.3934 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect[recommended_vs_previous vs previous_recommendation] | percentage points per year | 0.2928 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
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
