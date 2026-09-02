## Arms

| Arm | Window | Months | Basis | Gap, pp/yr | HAC 95% | Bootstrap 95% | Floor i.i.d. | Floor HAC | Floor boot | TE | Years | t | Status |
| --- | --- | ---: | --- | ---: | :---: | :---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| **tilts_oos** | 1981-07..1990-10 | 112 | vme, unscaled, AVES dropped | +0.89 | [+0.44, +1.34] | [+0.45, +1.29] | 0.60 | 0.65 | 0.60 | 0.66% | 4 | 3.86 | exploratory |
| tilts_oos_bridged | 1981-07..1990-10 | 112 | vme, bridged, AVES dropped | +0.53 | [+0.28, +0.78] | [+0.28, +0.76] | 0.34 | 0.36 | 0.34 | 0.37% | 4 | 4.15 | exploratory |
| tilts_oos_aves_dev | 1981-07..1990-10 | 112 | vme, unscaled, AVES developed_value | +0.98 | [+0.49, +1.47] | [+0.51, +1.42] | 0.65 | 0.70 | 0.66 | 0.71% | 4 | 3.92 | exploratory |
| tilts_overlap_vme | 1990-11..2026-05 | 427 | vme, unscaled, AVES developed_value | +0.40 | [-0.15, +0.96] | [-0.17, +1.02] | 0.62 | 0.80 | 0.85 | 1.32% | 83 | 1.42 | unresolved |
| tilts_overlap_vme_dropped | 1990-11..2026-05 | 427 | vme, unscaled, AVES dropped | +0.38 | [-0.13, +0.88] | [-0.14, +0.93] | 0.56 | 0.72 | 0.77 | 1.20% | 79 | 1.47 | unresolved |
| tilts_overlap_vme_bridged | 1990-11..2026-05 | 427 | vme, bridged, AVES developed_value | +0.25 | [-0.04, +0.55] | [-0.06, +0.59] | 0.32 | 0.42 | 0.46 | 0.68% | 57 | 1.70 | unresolved |
| tilts_overlap_french | 1990-11..2026-05 | 427 | french, unscaled, AVES emerging_value | +0.59 | [+0.20, +0.99] | [+0.16, +1.04] | 0.42 | 0.56 | 0.63 | 0.90% | 18 | 2.94 | exploratory |
| tilts_overlap_french_complete | 1990-11..2026-05 | 427 | french, unscaled, AVES emerging_value | +0.75 | [+0.36, +1.15] | [+0.33, +1.23] | 0.45 | 0.57 | 0.64 | 0.97% | 13 | 3.72 | exploratory |
| tilts_full_vme | 1981-07..2026-05 | 539 | vme, unscaled, AVES developed_value | +0.52 | [+0.07, +0.98] | [+0.04, +1.03] | 0.51 | 0.65 | 0.70 | 1.22% | 42 | 2.26 | exploratory |
| tilts_full_vme_dropped | 1981-07..2026-05 | 539 | vme, unscaled, AVES dropped | +0.48 | [+0.07, +0.89] | [+0.05, +0.94] | 0.46 | 0.59 | 0.63 | 1.11% | 41 | 2.30 | exploratory |
| tilts_full_vme_bridged | 1981-07..2026-05 | 539 | vme, bridged, AVES developed_value | +0.32 | [+0.08, +0.56] | [+0.06, +0.59] | 0.27 | 0.34 | 0.38 | 0.64% | 31 | 2.63 | exploratory |

## Attribution, pp/yr

| Arm | cost | dev_mom | dev_val | dxus_cma | dxus_hml | dxus_mkt | dxus_rmw | dxus_smb | dxus_umd | em_hml | em_mkt | us_hml | us_mkt | us_val | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| tilts_oos | -0.04 | +0.17 | +0.54 |  |  |  |  |  |  |  |  |  |  | +0.22 | +0.89 |
| tilts_oos_bridged | -0.04 | +0.15 | +0.30 |  |  |  |  |  |  |  |  |  |  | +0.12 | +0.53 |
| tilts_oos_aves_dev | -0.05 | +0.17 | +0.64 |  |  |  |  |  |  |  |  |  |  | +0.22 | +0.98 |
| tilts_overlap_vme | -0.05 | +0.16 | +0.25 |  |  |  |  |  |  |  |  |  |  | +0.04 | +0.40 |
| tilts_overlap_vme_dropped | -0.04 | +0.16 | +0.21 |  |  |  |  |  |  |  |  |  |  | +0.04 | +0.38 |
| tilts_overlap_vme_bridged | -0.05 | +0.14 | +0.14 |  |  |  |  |  |  |  |  |  |  | +0.02 | +0.25 |
| tilts_overlap_french | -0.05 |  |  |  | +0.32 |  |  |  | +0.23 |  |  | +0.10 |  |  | +0.59 |
| tilts_overlap_french_complete | -0.05 |  |  | -0.06 | +0.32 | +0.04 | +0.13 | +0.04 | +0.23 | +0.10 | +0.02 | +0.10 | -0.10 |  | +0.75 |
| tilts_full_vme | -0.05 | +0.16 | +0.34 |  |  |  |  |  |  |  |  |  |  | +0.08 | +0.52 |
| tilts_full_vme_dropped | -0.04 | +0.16 | +0.28 |  |  |  |  |  |  |  |  |  |  | +0.08 | +0.48 |
| tilts_full_vme_bridged | -0.05 | +0.14 | +0.19 |  |  |  |  |  |  |  |  |  |  | +0.04 | +0.32 |

## Sub-periods, hostile arms and trailing probabilities

| Arm | Sub-period gaps (months, floor) | Best month removed | Worst month removed | Perturbation range | Boot 6m | Boot 24m | P(trail) | Median shortfall |
| --- | --- | ---: | ---: | :---: | :---: | :---: | --- | --- |
| tilts_oos | oos_first_half +1.05 (56, 0.97); oos_second_half +0.73 (56, 0.73) | +0.82 | +0.94 | [+0.56, +1.22] | [+0.45, +1.33] | [+0.48, +1.27] | 5y 0.1% | 5y -0.04 |
| tilts_oos_bridged | oos_first_half +0.61 (56, 0.54); oos_second_half +0.45 (56, 0.42) | +0.49 | +0.56 | [+0.30, +0.76] | [+0.28, +0.77] | [+0.29, +0.75] | 5y 0.1% | 5y -0.02 |
| tilts_oos_aves_dev | oos_first_half +1.15 (56, 1.05); oos_second_half +0.82 (56, 0.77) | +0.91 | +1.04 | [+0.59, +1.37] | [+0.50, +1.45] | [+0.54, +1.40] | 5y 0.1% | 5y -0.07 |
| tilts_overlap_vme | flat_equity_decade +1.06 (120, 1.70); post_gfc +0.04 (206, 0.74) | +0.35 | +0.48 | [+0.17, +0.64] | [-0.15, +0.99] | [-0.17, +0.99] | 10y 22.4%, 20y 15.1%, 30y 10.1% | 10y -0.25, 20y -0.16, 30y -0.12 |
| tilts_overlap_vme_dropped | flat_equity_decade +0.98 (120, 1.54); post_gfc +0.05 (206, 0.66) | +0.33 | +0.45 | [+0.17, +0.58] | [-0.12, +0.91] | [-0.14, +0.91] | 10y 22.6%, 20y 14.1%, 30y 9.2% | 10y -0.22, 20y -0.14, 30y -0.10 |
| tilts_overlap_vme_bridged | flat_equity_decade +0.64 (120, 0.87); post_gfc +0.04 (206, 0.39) | +0.22 | +0.29 | [+0.08, +0.43] | [-0.04, +0.57] | [-0.06, +0.58] | 10y 18.9%, 20y 11.4%, 30y 7.5% | 10y -0.13, 20y -0.08, 30y -0.06 |
| tilts_overlap_french | flat_equity_decade +1.10 (120, 0.95); post_gfc +0.34 (206, 0.61) | +0.56 | +0.62 | [+0.30, +0.89] | [+0.19, +1.01] | [+0.16, +1.05] | 10y 7.6%, 20y 2.2%, 30y 0.6% | 10y -0.14, 20y -0.09, 30y -0.05 |
| tilts_overlap_french_complete | flat_equity_decade +1.46 (120, 1.04); post_gfc +0.44 (206, 0.57) | +0.71 | +0.78 | [+0.36, +1.14] | [+0.36, +1.17] | [+0.32, +1.26] | 10y 2.6%, 20y 0.3%, 30y 0.1% | 10y -0.09, 20y -0.07, 30y -0.03 |
| tilts_full_vme | primary_out_of_sample +0.98 (112, 0.65); overlap_with_016e +0.40 (427, 0.62); full_first_half +0.89 (270, 0.83); full_second_half +0.16 (269, 0.59); flat_equity_decade +1.06 (120, 1.70); post_gfc +0.04 (206, 0.74) | +0.48 | +0.59 | [+0.26, +0.79] | [+0.04, +1.00] | [+0.04, +1.01] | 10y 14.2%, 20y 7.7%, 30y 3.8% | 10y -0.21, 20y -0.12, 30y -0.09 |
| tilts_full_vme_dropped | primary_out_of_sample +0.89 (112, 0.60); overlap_with_016e +0.38 (427, 0.56); full_first_half +0.81 (270, 0.76); full_second_half +0.15 (269, 0.53); flat_equity_decade +0.98 (120, 1.54); post_gfc +0.05 (206, 0.66) | +0.44 | +0.54 | [+0.25, +0.71] | [+0.05, +0.91] | [+0.05, +0.92] | 10y 14.4%, 20y 7.3%, 30y 3.9% | 10y -0.18, 20y -0.12, 30y -0.08 |
| tilts_full_vme_bridged | primary_out_of_sample +0.58 (112, 0.36); overlap_with_016e +0.25 (427, 0.32); full_first_half +0.53 (270, 0.43); full_second_half +0.11 (269, 0.31); flat_equity_decade +0.64 (120, 0.87); post_gfc +0.04 (206, 0.39) | +0.30 | +0.35 | [+0.13, +0.51] | [+0.06, +0.58] | [+0.05, +0.59] | 10y 11.8%, 20y 5.0%, 30y 2.5% | 10y -0.12, 20y -0.06, 30y -0.05 |

## Each leg on its own longest pre-1990-11 window

| Leg | Window | Months | Exposure | Premium, pp/yr | HAC 95% | Floor | Contribution, pp/yr | HAC 95% | Floor |
| --- | --- | ---: | ---: | ---: | :---: | ---: | ---: | :---: | ---: |
| us_val | 1972-02..1990-10 | 225 | +0.0466 | +5.10 | [-0.79, +10.99] | 7.93 | +0.24 | [-0.04, +0.51] | 0.37 |
| dev_mom | 1974-02..1990-10 | 201 | +0.0278 | +6.62 | [+2.79, +10.45] | 5.51 | +0.18 | [+0.08, +0.29] | 0.15 |
| dev_val | 1981-07..1990-10 | 112 | +0.0619 | +8.72 | [+4.18, +13.26] | 5.84 | +0.54 | [+0.26, +0.82] | 0.36 |

## Basis check, 1990-11..2026-05

| Quantity | pp/yr |
| --- | ---: |
| reference_016e_growth_gap_pp_yr | +0.7996 |
| french_complete_arithmetic_gap_pp_yr | +0.7540 |
| variance_drag_arithmetic_minus_growth_pp_yr | +0.0314 |
| french_complete_less_reference_pp_yr | -0.0456 |
| french_mapped_legs_only_gap_pp_yr | +0.5923 |
| vme_unscaled_gap_pp_yr | +0.4050 |
| vme_bridged_gap_pp_yr | +0.2539 |
| regional_residual_pp_yr | -0.0391 |
| unmapped_legs_pp_yr | +0.2007 |

### Bridge slopes, French factor on VME leg

| VME leg | French leg | Pinned | Recomputed | Drift | Correlation | French mean | VME mean | French vol | VME vol |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| us_val | us_hml | 0.532 | 0.5319 | -0.0001 | 0.7627 | 2.1552 | 0.9226 | 11.2486 | 16.1294 |
| dev_val | dxus_hml | 0.564 | 0.5644 | 0.0004 | 0.7969 | 5.115 | 3.4527 | 8.0939 | 11.4276 |
| dev_mom | dxus_umd | 0.876 | 0.8756 | -0.0004 | 0.9361 | 8.2376 | 5.7943 | 11.7116 | 12.5208 |
