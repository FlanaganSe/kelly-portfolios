### The tilt complex out of sample: does VTI 49 / VTV 15 / VXUS 16 / AVDV 10 / IDMO 5 / AVES 5 beat the cheap 65/35 index on AQR's Value and Momentum Everywhere stock-selection factors before 1990-11, where the French ex-US panels that carry 86% of its +0.80 pp/yr edge do not exist, and does the VME basis reproduce the French one where the two overlap?

- **Status:** `exploratory` — a search, not a finding; it may not be quoted as evidence that anything works
- **Run:** `6915b6746af046c5ba54beb2902bbab2`
- **Experiment family:** `exp_023_tilts_out_of_sample`
- **Specification hash:** `59181ce65b5bf79c95ca066acd6e61681628b24a295c43f7a8e70ffd0036899a`
- **Run kind:** `exploratory`
- **Evidence class:** `policy-simulation`
- **Falsifier:** For the PRIMARY arm, `tilts_oos` on 1981-07..1990-10, VME basis, unscaled loadings, AVES dropped: (a) `rejected` if the after-cost arithmetic-mean gap is at or below zero. This is the clause that would mean the in-sample tilt edge does not reproduce out of sample. (b) `unresolved` if the gap is positive but smaller than the minimum detectable effect at 80% power from the arm's own paired difference series, which must be reported in the same sentence, with the HAC and block-bootstrap floors beside it. (c) `unresolved` if the gap clears (b) but its 95% stationary-block-bootstrap interval or its 95% HAC interval includes zero. (d) `unresolved` if the gap clears (b) and (c) but changes sign anywhere on the +/-0.15 loading perturbation grid or in either declared half of the window. (e) `exploratory` otherwise. Under no outcome may this specification produce a status above `exploratory` (freeze note 8). The whole-experiment status is the primary arm's status. Every secondary arm is reported with the same clauses applied, for information, and none of them can change the whole-experiment status.

PRIMARY, 1981-07..1990-10 (112 months), VME basis, unscaled loadings, AVES dropped: the tilt complex's after-cost arithmetic gap over the cheap 65/35 index is +0.89 pp/yr, HAC 95% [+0.44, +1.34], block bootstrap [+0.45, +1.29], against floors of 0.60 (i.i.d.), 0.65 (HAC) and 0.60 (block bootstrap); tracking error 0.66%; implied HAC t 3.86 against a 3 hurdle. Status exploratory: (e) survived every clause. Basis check on 1990-11..2026-05: VME unscaled +0.40, VME bridged +0.25, French complete +0.75 against 016e's +0.80.

Gross, net-optimistic and net-pessimistic are separate columns and are never collapsed; the spread between them is the cost-model uncertainty.

| Statistic | Units | Gross | Net-optimistic | Net-pessimistic | Interval method |
| --- | --- | --- | --- | --- | --- |
| arithmetic_gap[tilts_oos] | percentage points per year | not reported | not reported | 0.8905 [0.455, 1.291] | stationary block bootstrap of the paired difference, mean block 12 months, 10000 resamples, 95% percentile |
| arithmetic_gap_hac[tilts_oos] | percentage points per year | not reported | not reported | 0.8905 [0.438, 1.343] | Newey-West HAC, 4 lags by the automatic rule, 95% normal |
| arithmetic_gap[tilts_oos_bridged] | percentage points per year | not reported | not reported | 0.5303 [0.2841, 0.7581] | stationary block bootstrap of the paired difference, mean block 12 months, 10000 resamples, 95% percentile |
| arithmetic_gap_hac[tilts_oos_bridged] | percentage points per year | not reported | not reported | 0.5303 [0.2798, 0.7808] | Newey-West HAC, 4 lags by the automatic rule, 95% normal |
| arithmetic_gap[tilts_oos_aves_dev] | percentage points per year | not reported | not reported | 0.9813 [0.5074, 1.421] | stationary block bootstrap of the paired difference, mean block 12 months, 10000 resamples, 95% percentile |
| arithmetic_gap_hac[tilts_oos_aves_dev] | percentage points per year | not reported | not reported | 0.9813 [0.4905, 1.472] | Newey-West HAC, 4 lags by the automatic rule, 95% normal |
| arithmetic_gap[tilts_overlap_vme] | percentage points per year | not reported | not reported | 0.405 [-0.169, 1.017] | stationary block bootstrap of the paired difference, mean block 12 months, 10000 resamples, 95% percentile |
| arithmetic_gap_hac[tilts_overlap_vme] | percentage points per year | not reported | not reported | 0.405 [-0.1523, 0.9623] | Newey-West HAC, 5 lags by the automatic rule, 95% normal |
| arithmetic_gap[tilts_overlap_vme_dropped] | percentage points per year | not reported | not reported | 0.3766 [-0.1393, 0.9289] | stationary block bootstrap of the paired difference, mean block 12 months, 10000 resamples, 95% percentile |
| arithmetic_gap_hac[tilts_overlap_vme_dropped] | percentage points per year | not reported | not reported | 0.3766 [-0.1264, 0.8795] | Newey-West HAC, 5 lags by the automatic rule, 95% normal |
| arithmetic_gap[tilts_overlap_vme_bridged] | percentage points per year | not reported | not reported | 0.2539 [-0.05569, 0.5881] | stationary block bootstrap of the paired difference, mean block 12 months, 10000 resamples, 95% percentile |
| arithmetic_gap_hac[tilts_overlap_vme_bridged] | percentage points per year | not reported | not reported | 0.2539 [-0.03809, 0.5458] | Newey-West HAC, 5 lags by the automatic rule, 95% normal |
| arithmetic_gap[tilts_overlap_french] | percentage points per year | not reported | not reported | 0.5923 [0.1641, 1.044] | stationary block bootstrap of the paired difference, mean block 12 months, 10000 resamples, 95% percentile |
| arithmetic_gap_hac[tilts_overlap_french] | percentage points per year | not reported | not reported | 0.5923 [0.1977, 0.9869] | Newey-West HAC, 5 lags by the automatic rule, 95% normal |
| arithmetic_gap[tilts_overlap_french_complete] | percentage points per year | not reported | not reported | 0.754 [0.3288, 1.228] | stationary block bootstrap of the paired difference, mean block 12 months, 10000 resamples, 95% percentile |
| arithmetic_gap_hac[tilts_overlap_french_complete] | percentage points per year | not reported | not reported | 0.754 [0.3567, 1.151] | Newey-West HAC, 5 lags by the automatic rule, 95% normal |
| arithmetic_gap[tilts_full_vme] | percentage points per year | not reported | not reported | 0.5247 [0.04304, 1.028] | stationary block bootstrap of the paired difference, mean block 12 months, 10000 resamples, 95% percentile |
| arithmetic_gap_hac[tilts_full_vme] | percentage points per year | not reported | not reported | 0.5247 [0.06924, 0.9802] | Newey-West HAC, 5 lags by the automatic rule, 95% normal |
| arithmetic_gap[tilts_full_vme_dropped] | percentage points per year | not reported | not reported | 0.4834 [0.04998, 0.9395] | stationary block bootstrap of the paired difference, mean block 12 months, 10000 resamples, 95% percentile |
| arithmetic_gap_hac[tilts_full_vme_dropped] | percentage points per year | not reported | not reported | 0.4834 [0.07194, 0.8948] | Newey-West HAC, 5 lags by the automatic rule, 95% normal |
| arithmetic_gap[tilts_full_vme_bridged] | percentage points per year | not reported | not reported | 0.3208 [0.05995, 0.5938] | stationary block bootstrap of the paired difference, mean block 12 months, 10000 resamples, 95% percentile |
| arithmetic_gap_hac[tilts_full_vme_bridged] | percentage points per year | not reported | not reported | 0.3208 [0.08143, 0.5602] | Newey-West HAC, 5 lags by the automatic rule, 95% normal |

Statistics with no cost basis:

| Statistic | Units | Value | Interval method | Observations |
| --- | --- | --- | --- | --- |
| minimum_detectable_effect_iid[tilts_oos] | percentage points per year | 0.6035 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 112 |
| minimum_detectable_effect_iid[tilts_oos_bridged] | percentage points per year | 0.342 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 112 |
| minimum_detectable_effect_iid[tilts_oos_aves_dev] | percentage points per year | 0.6496 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 112 |
| minimum_detectable_effect_iid[tilts_overlap_vme] | percentage points per year | 0.6192 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect_iid[tilts_overlap_vme_dropped] | percentage points per year | 0.5623 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect_iid[tilts_overlap_vme_bridged] | percentage points per year | 0.3209 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect_iid[tilts_overlap_french] | percentage points per year | 0.4224 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect_iid[tilts_overlap_french_complete] | percentage points per year | 0.4541 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 427 |
| minimum_detectable_effect_iid[tilts_full_vme] | percentage points per year | 0.5093 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 539 |
| minimum_detectable_effect_iid[tilts_full_vme_dropped] | percentage points per year | 0.4632 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 539 |
| minimum_detectable_effect_iid[tilts_full_vme_bridged] | percentage points per year | 0.2656 (no interval: a detection floor is a property of the design, not an estimate of a quantity in the world, so it carries no interval) | not reported | 539 |

**Caveats.**
- Every fund is 016e's basis expression; no fund return enters. On the VME basis the French loadings are applied UNSCALED to a rank-weighted long/short book they were not fitted on; the bridged arms carry the pinned overlap slopes and the pair brackets the translation.
- VME carries no size, profitability or investment factor. AVDV's small-cap half and IDMO's CMA leg are unmapped; their French-basis price on the overlap window is in `basis_check.unmapped_legs_pp_yr`.
- The primary window is 112 months, set by the first developed VME value observation. Its floor is about twice 016e's and the test is underpowered for a full-size replication; the specification says so before the run.
- The estimand is the arithmetic active-leg gap, not 016e's simulated log-growth gap; the regional residual and the variance-drag difference are priced on the overlap window in `basis_check`.
- Nothing was read from the VME asset-allocation legs. The stock-selection series are vendor-authored, reconstructed on every update, and gross of every implementation cost, as the French series are.
- The design was chosen after reading the 1990-2026 result. The window is out of sample for the data; nothing here is out of sample for the design.
