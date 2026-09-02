# Experiment 019: carry as a second financed engine

Run `fd023828337641fa8cfdbc44e1c5ffe3`; specification hash `692359e34f0c082a11931ed470d6ab36ccf5c32ac95d8d8e022f422cb5947a11`.

WRAPPERS ARE ASSUMED EXPOSURE VECTORS, NOT FUND RETURNS. The carry leg is AQR's 'All Macro Carry' from the century-of-factor-premia workbook, a vendor reconstruction gross of trading costs and fees, three asset classes before 1974-02 and four after, scaled to 12.38% volatility by one full-window constant. The long-panel trend leg is this repository's own 4-asset book scaled the same way; the secondary panel's is AQR's TSMOM. The prediction was a bracket: `exploratory` at the gross series and full loading, `unresolved` under a 2 pp/yr haircut and a 0.681 loading. The whole-experiment status is inherited from the trend reference and says nothing about carry.

Trend-book volatility scalar 1.9771 (realised 6.26% on 1929-01..2025-05, target 12.38%). Carry-leg volatility scalar 2.7575 (realised 4.49% on the same window, target 12.38%).

Gap cells read: point estimate [95% block-bootstrap interval] MDE at 80% power, years to distinguish, falsifier status. A control column marked `identical` is the arm itself. Descriptive tables carry no status by design.

## Panel `primary` (primary): 1929-01..2025-05, 1157 months, trend `own_4_asset_book`, carry `published`

The longest window on which equity, T-bills, the own trend book and the carry composite all exist. Expected 1929-01..2025-05, 1157 months; the composite holds three asset classes before 1974-02.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 12.9362 | 11.0753 | 18.9893 | 0.51 | -82.78 | 164 | 1.0 | 5.1688 |
| `base_no_trend` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 10.9532 | 9.21 | 18.4972 | 0.4165 | -83.67 | 184 | 0.1935 | 1.0 |
| `carry30_no_trend` | 1.300 | 1.000 | 0.000 | 0.300 | 0.000 | 12.6851 | 10.7802 | 19.3067 | 0.4889 | -80.84 | 188 | 0.8265 | 4.2719 |
| `trend30_carrystack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 13.5136 | 11.6098 | 19.1944 | 0.5347 | -81.82 | 88 | 1.6362 | 8.4569 |
| `trend30_carrystack20` | 1.522 | 1.022 | 0.300 | 0.200 | 0.000 | 14.091 | 12.1291 | 19.4763 | 0.5567 | -80.83 | 86 | 2.646 | 13.6763 |
| `trend15_carry15` | 1.311 | 1.011 | 0.150 | 0.150 | 0.000 | 12.8107 | 10.9594 | 18.9819 | 0.5037 | -81.81 | 177 | 0.9295 | 4.8043 |
| `trend30_carry30` | 1.622 | 1.022 | 0.300 | 0.300 | 0.000 | 14.6684 | 12.633 | 19.8315 | 0.5759 | -79.8 | 94 | 4.229 | 21.8585 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.98 [+1.26, +2.71] MDE 1.06 27y `exploratory` | -0.30 [-1.63, +1.16] MDE 1.97 4181y `rejected` | +1.79 [+1.07, +2.53] MDE 1.06 34y `exploratory` | +1.59 [+0.81, +2.38] MDE 1.11 45y `exploratory` | -- |
| `base_no_trend` | identical | identical | identical | -0.00 [-0.00, +0.00] MDE 0.00 424y `rejected` | -1.98 [-2.71, -1.26] MDE 1.06 27y `rejected` |
| `carry30_no_trend` | +1.73 [+0.85, +2.58] MDE 1.06 36y `exploratory` | -0.40 [-1.85, +1.15] MDE 1.80 1980y `rejected` | +1.42 [+0.51, +2.33] MDE 1.06 53y `exploratory` | +1.09 [+0.15, +1.99] MDE 1.07 90y `exploratory` | -0.25 [-1.38, +0.87] MDE 1.44 3165y `rejected` |
| `trend30_carrystack10` | +2.56 [+1.78, +3.35] MDE 1.14 19y `exploratory` | -0.43 [-2.13, +1.42] MDE 2.43 3064y `rejected` | +2.29 [+1.50, +3.11] MDE 1.14 24y `exploratory` | +2.00 [+1.15, +2.86] MDE 1.18 33y `exploratory` | +0.58 [+0.28, +0.86] MDE 0.35 36y `exploratory` |
| `trend30_carrystack20` | +3.14 [+2.20, +4.09] MDE 1.32 17y `exploratory` | -0.56 [-2.67, +1.73] MDE 2.95 2630y `rejected` | +2.76 [+1.80, +3.75] MDE 1.32 22y `exploratory` | +2.36 [+1.36, +3.37] MDE 1.36 31y `exploratory` | +1.15 [+0.57, +1.72] MDE 0.71 36y `exploratory` |
| `trend15_carry15` | +1.86 [+1.29, +2.43] MDE 0.78 17y `exploratory` | -0.35 [-1.61, +1.03] MDE 1.74 2414y `rejected` | +1.67 [+1.09, +2.27] MDE 0.77 21y `exploratory` | +1.44 [+0.84, +2.04] MDE 0.79 28y `exploratory` | -0.13 [-0.69, +0.44] MDE 0.72 3166y `rejected` |
| `trend30_carry30` | +3.72 [+2.59, +4.87] MDE 1.55 17y `exploratory` | -0.70 [-3.23, +2.07] MDE 3.49 2418y `rejected` | +3.20 [+2.04, +4.41] MDE 1.56 23y `exploratory` | +2.68 [+1.44, +3.89] MDE 1.60 33y `exploratory` | +1.73 [+0.85, +2.58] MDE 1.06 36y `exploratory` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | first_half | second_half | flat_equity_decade | three_class_carry | four_class_carry | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +1.98 | +1.99 | +1.98 | +1.99 | +2.84 | +1.97 | +2.00 | +0.37 | +0.04 |
| `base_no_trend` | -1.98 | -1.99 | -1.98 | -1.99 | -2.84 | -1.97 | -2.00 | -0.37 | -0.04 |
| `carry30_no_trend` | +0.14 | -0.64 | +0.15 | -0.65 | -0.54 | -0.17 | -0.32 | -0.47 | -1.26 |
| `trend30_carrystack10` | +0.71 | +0.45 | +0.71 | +0.44 | +0.77 | +0.60 | +0.56 | -0.03 | -0.41 |
| `trend30_carrystack20` | +1.41 | +0.90 | +1.42 | +0.89 | +1.53 | +1.20 | +1.12 | -0.07 | -0.82 |
| `trend15_carry15` | +0.07 | -0.32 | +0.07 | -0.33 | -0.27 | -0.09 | -0.16 | -0.24 | -0.63 |
| `trend30_carry30` | +2.12 | +1.35 | +2.13 | +1.33 | +2.30 | +1.79 | +1.68 | -0.10 | -1.22 |

### Leg correlations: 1157 months, worst decile = 115 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.074 | 0.072 |
| equity_carry | 0.119 | 0.219 |
| trend_carry | 0.063 | 0.066 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 7.75 | 18.53 | -9.359 | 0.0 |
| trend | 7.22 | 12.38 | 1.569 | 0.626 |
| carry | 6.89 | 12.38 | 0.168 | 0.574 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1929-01..1977-02 | 578 | 0.036 | 0.13 | -0.127 | 0.139 | 0.281 | 8.18 | 7.25 | 7.12 |
| panel_second_half | 1977-03..2025-05 | 579 | 0.102 | 0.098 | -0.011 | -0.006 | 0.194 | 5.6 | 7.19 | 8.38 |
| first_half | 1929-01..1977-03 | 579 | 0.036 | 0.13 | -0.127 | 0.139 | 0.281 | 8.21 | 7.26 | 7.08 |
| second_half | 1977-04..2025-05 | 578 | 0.102 | 0.099 | -0.011 | -0.006 | 0.194 | 5.56 | 7.18 | 8.42 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.13 | 0.152 | -0.331 | -0.281 | 0.507 | 8.78 | 10.93 | -4.32 |
| three_class_carry | 1929-01..1974-01 | 541 | 0.062 | 0.136 | -0.103 | 0.165 | 0.284 | 7.09 | 7.18 | 7.48 |
| four_class_carry | 1974-02..2025-05 | 616 | 0.069 | 0.09 | -0.047 | -0.02 | 0.156 | 6.71 | 7.25 | 7.99 |
| post_2009 | 2009-01..2025-05 | 197 | -0.01 | 0.253 | -0.049 | -0.255 | 0.292 | 0.77 | 1.41 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | -0.026 | 0.17 | -0.067 | -0.399 | 0.609 | -2.96 | 0.43 | 12.12 |

Sum rule against the cheap control: both 3.7152 = trend 1.9831 + carry 1.7319 + residual 0.0002 pp/yr.

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (5 ep.) | 0.0 (3 ep.) |
| `base_no_trend` | -0.239 (0.426) | -0.038 (-1.29) | -2.09 (5 ep.) | -14.98 (3 ep.) |
| `carry30_no_trend` | -0.217 (0.487) | -0.0551 (-1.44) | -2.27 (5 ep.) | -11.06 (3 ep.) |
| `trend30_carrystack10` | 0.008 (0.557) | -0.0057 (-0.84) | -0.06 (5 ep.) | 1.56 (3 ep.) |
| `trend30_carrystack20` | 0.015 (0.557) | -0.0114 (-0.84) | -0.09 (5 ep.) | 3.13 (3 ep.) |
| `trend15_carry15` | -0.108 (0.487) | -0.0276 (-1.44) | -1.15 (5 ep.) | -5.6 (3 ep.) |
| `trend30_carry30` | 0.023 (0.557) | -0.0171 (-0.84) | -0.1 (5 ep.) | 4.7 (3 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | -82.78 (+0.00) | -50.34 (+0.00) | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -34.29 (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `base_no_trend` | -83.67 (-0.89) | -49.47 (+0.87) | -45.03 (-4.35) | -50.33 (-4.47) | -20.22 (-1.59) | -46.54 (-12.24) | 54.6 (-31.41) | -24.86 (-1.29) |
| `carry30_no_trend` | -80.84 (+1.94) | -53.14 (-2.79) | -39.49 (+1.18) | -52.78 (-6.92) | -23.4 (-4.77) | -40.38 (-6.09) | 61.05 (-24.96) | -25.71 (-2.14) |
| `trend30_carrystack10` | -81.82 (+0.96) | -51.56 (-1.22) | -38.76 (+1.92) | -46.73 (-0.87) | -19.71 (-1.08) | -31.88 (+2.41) | 88.56 (+2.56) | -23.85 (-0.28) |
| `trend30_carrystack20` | -80.83 (+1.95) | -52.76 (-2.41) | -36.79 (+3.89) | -47.6 (-1.74) | -20.78 (-2.15) | -29.4 (+4.90) | 91.06 (+5.05) | -24.13 (-0.56) |
| `trend15_carry15` | -81.81 (+0.97) | -51.74 (-1.39) | -40.06 (+0.62) | -49.38 (-3.52) | -21.03 (-2.40) | -37.37 (-3.08) | 73.34 (-12.66) | -24.63 (-1.06) |
| `trend30_carry30` | -79.8 (+2.98) | -53.93 (-3.59) | -34.76 (+5.92) | -48.46 (-2.60) | -21.85 (-3.22) | -26.84 (+7.45) | 93.49 (+7.49) | -24.42 (-0.85) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 98, 130, 165, 200, 231
ordering against reference stable across the band: `True`

| arm | 62 | 98 | 130 | 165 | 200 | 231 | vs cheap at each point |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `base_trend30` | -- | -- | -- | -- | -- | -- | +1.98, +1.95, +1.92, +1.88, +1.85, +1.82 |
| `base_no_trend` | -1.98 | -1.95 | -1.92 | -1.88 | -1.85 | -1.82 | +0.00, +0.00, +0.00, +0.00, +0.00, +0.00 |
| `carry30_no_trend` | -0.25 | -0.24 | -0.23 | -0.23 | -0.22 | -0.21 | +1.73, +1.70, +1.68, +1.65, +1.63, +1.61 |
| `trend30_carrystack10` | +0.58 | +0.57 | +0.56 | +0.55 | +0.54 | +0.54 | +2.56, +2.52, +2.48, +2.43, +2.39, +2.35 |
| `trend30_carrystack20` | +1.15 | +1.14 | +1.12 | +1.10 | +1.09 | +1.07 | +3.14, +3.08, +3.04, +2.98, +2.93, +2.89 |
| `trend15_carry15` | -0.13 | -0.12 | -0.12 | -0.11 | -0.11 | -0.10 | +1.86, +1.83, +1.80, +1.77, +1.74, +1.71 |
| `trend30_carry30` | +1.73 | +1.71 | +1.68 | +1.65 | +1.63 | +1.61 | +3.72, +3.65, +3.60, +3.54, +3.47, +3.42 |

## Panel `four_class_subwindow` (primary_subwindow): 1974-02..2025-05, 616 months, trend `own_4_asset_book`, carry `published`

The primary panel from the first month the currency carry leg exists. Expected 616 months.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 14.2251 | 12.7823 | 16.5129 | 0.6015 | -45.86 | 51 | 1.0 | 2.3856 |
| `base_no_trend` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 12.2268 | 10.9072 | 15.8741 | 0.4999 | -50.33 | 73 | 0.4192 | 1.0 |
| `carry30_no_trend` | 1.300 | 1.000 | 0.000 | 0.300 | 0.000 | 13.9047 | 12.4778 | 16.4408 | 0.585 | -52.78 | 51 | 0.8316 | 1.9838 |
| `trend30_carrystack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 14.7845 | 13.3127 | 16.6535 | 0.6301 | -46.73 | 50 | 1.2664 | 3.021 |
| `trend30_carrystack20` | 1.522 | 1.022 | 0.300 | 0.200 | 0.000 | 15.3438 | 13.8329 | 16.854 | 0.6559 | -47.6 | 40 | 1.5999 | 3.8167 |
| `trend15_carry15` | 1.311 | 1.011 | 0.150 | 0.150 | 0.000 | 14.0649 | 12.6589 | 16.3014 | 0.5996 | -49.38 | 51 | 0.924 | 2.2044 |
| `trend30_carry30` | 1.622 | 1.022 | 0.300 | 0.300 | 0.000 | 15.9032 | 14.3427 | 17.1123 | 0.6788 | -48.46 | 39 | 2.0159 | 4.8092 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +2.00 [+1.01, +3.01] MDE 1.54 31y `exploratory` | -0.36 [-1.92, +1.29] MDE 2.48 2428y `rejected` | +1.70 [+0.71, +2.71] MDE 1.55 43y `exploratory` | +1.50 [+0.48, +2.55] MDE 1.61 55y `unresolved` | -- |
| `base_no_trend` | identical | identical | identical | +0.00 [-0.00, +0.00] MDE 0.00 9690y `unresolved` | -2.00 [-3.01, -1.01] MDE 1.54 31y `rejected` |
| `carry30_no_trend` | +1.68 [+0.72, +2.61] MDE 1.19 26y `exploratory` | -0.52 [-2.14, +1.12] MDE 2.12 846y `rejected` | +1.42 [+0.42, +2.37] MDE 1.19 36y `exploratory` | +0.93 [-0.08, +1.93] MDE 1.21 81y `unresolved` | -0.32 [-1.70, +1.02] MDE 1.88 1759y `rejected` |
| `trend30_carrystack10` | +2.56 [+1.50, +3.61] MDE 1.62 21y `exploratory` | -0.53 [-2.48, +1.55] MDE 3.00 1619y `rejected` | +2.20 [+1.12, +3.26] MDE 1.63 28y `exploratory` | +1.83 [+0.70, +2.99] MDE 1.69 41y `exploratory` | +0.56 [+0.24, +0.87] MDE 0.40 26y `exploratory` |
| `trend30_carrystack20` | +3.12 [+1.92, +4.31] MDE 1.79 17y `exploratory` | -0.71 [-3.09, +1.85] MDE 3.59 1317y `rejected` | +2.66 [+1.43, +3.88] MDE 1.80 23y `exploratory` | +2.13 [+0.79, +3.45] MDE 1.87 37y `exploratory` | +1.12 [+0.48, +1.74] MDE 0.79 26y `exploratory` |
| `trend15_carry15` | +1.84 [+1.14, +2.53] MDE 1.01 16y `exploratory` | -0.44 [-1.87, +1.09] MDE 2.11 1169y `rejected` | +1.64 [+0.93, +2.34] MDE 1.01 19y `exploratory` | +1.31 [+0.53, +2.09] MDE 1.05 31y `exploratory` | -0.16 [-0.85, +0.51] MDE 0.94 1759y `rejected` |
| `trend30_carry30` | +3.68 [+2.28, +5.05] MDE 2.02 16y `exploratory` | -0.88 [-3.75, +2.18] MDE 4.21 1170y `rejected` | +3.10 [+1.65, +4.53] MDE 2.04 22y `exploratory` | +2.39 [+0.82, +3.96] MDE 2.11 38y `exploratory` | +1.68 [+0.72, +2.61] MDE 1.19 26y `exploratory` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | first_half | second_half | flat_equity_decade | four_class_carry | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +2.59 | +1.41 | +2.19 | +1.99 | +2.84 | +2.00 | +0.37 | +0.04 |
| `base_no_trend` | -2.59 | -1.41 | -2.19 | -1.99 | -2.84 | -2.00 | -0.37 | -0.04 |
| `carry30_no_trend` | -0.05 | -0.59 | +4.73 | -0.65 | -0.54 | -0.32 | -0.47 | -1.26 |
| `trend30_carrystack10` | +0.84 | +0.27 | +2.30 | +0.44 | +0.77 | +0.56 | -0.03 | -0.41 |
| `trend30_carrystack20` | +1.69 | +0.55 | +4.61 | +0.89 | +1.53 | +1.12 | -0.07 | -0.82 |
| `trend15_carry15` | -0.03 | -0.29 | +2.36 | -0.33 | -0.27 | -0.16 | -0.24 | -0.63 |
| `trend30_carry30` | +2.53 | +0.82 | +6.91 | +1.33 | +2.30 | +1.68 | -0.10 | -1.22 |

### Leg correlations: 616 months, worst decile = 61 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.047 | 0.089 |
| equity_carry | 0.09 | 0.156 |
| trend_carry | 0.069 | -0.02 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 7.99 | 15.91 | -8.27 | 0.0 |
| trend | 7.25 | 13.17 | 2.004 | 0.656 |
| carry | 6.71 | 10.14 | -0.219 | 0.492 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1974-02..1999-09 | 308 | 0.078 | -0.005 | 0.076 | 0.133 | -0.042 | 9.55 | 9.18 | 8.38 |
| panel_second_half | 1999-10..2025-05 | 308 | 0.05 | 0.196 | -0.195 | -0.163 | 0.331 | 3.86 | 5.32 | 7.59 |
| first_half | 1974-02..1977-03 | 38 | -0.317 | 0.05 | -0.39 | -0.913 | -0.662 | 24.16 | 8.35 | 1.38 |
| second_half | 1977-04..2025-05 | 578 | 0.102 | 0.099 | -0.011 | -0.006 | 0.194 | 5.56 | 7.18 | 8.42 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.13 | 0.152 | -0.331 | -0.281 | 0.507 | 8.78 | 10.93 | -4.32 |
| four_class_carry | 1974-02..2025-05 | 616 | 0.069 | 0.09 | -0.047 | -0.02 | 0.156 | 6.71 | 7.25 | 7.99 |
| post_2009 | 2009-01..2025-05 | 197 | -0.01 | 0.253 | -0.049 | -0.255 | 0.292 | 0.77 | 1.41 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | -0.026 | 0.17 | -0.067 | -0.399 | 0.609 | -2.96 | 0.43 | 12.12 |

Sum rule against the cheap control: both 3.6764 = trend 1.9983 + carry 1.6779 + residual 0.0002 pp/yr.

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (3 ep.) |
| `base_no_trend` | -0.394 (0.344) | 0.0057 (0.1) | -3.47 (3 ep.) | -13.46 (3 ep.) |
| `carry30_no_trend` | -0.487 (0.426) | 0.0247 (0.33) | -3.5 (3 ep.) | -10.86 (3 ep.) |
| `trend30_carrystack10` | -0.031 (0.475) | 0.0063 (0.62) | -0.01 (3 ep.) | 1.03 (3 ep.) |
| `trend30_carrystack20` | -0.062 (0.475) | 0.0126 (0.62) | -0.0 (3 ep.) | 2.04 (3 ep.) |
| `trend15_carry15` | -0.244 (0.426) | 0.0123 (0.33) | -1.77 (3 ep.) | -5.5 (3 ep.) |
| `trend30_carry30` | -0.094 (0.475) | 0.019 (0.62) | 0.03 (3 ep.) | 3.03 (3 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -26.34* (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `base_no_trend` | n/c | n/c | -45.03 (-4.35) | -50.33 (-4.47) | -20.22 (-1.59) | -34.03* (-7.69) | 54.6 (-31.41) | -24.86 (-1.29) |
| `carry30_no_trend` | n/c | n/c | -39.49 (+1.18) | -52.78 (-6.92) | -23.4 (-4.77) | -31.81* (-5.47) | 61.05 (-24.96) | -25.71 (-2.14) |
| `trend30_carrystack10` | n/c | n/c | -38.76 (+1.92) | -46.73 (-0.87) | -19.71 (-1.08) | -25.53* (+0.81) | 88.56 (+2.56) | -23.85 (-0.28) |
| `trend30_carrystack20` | n/c | n/c | -36.79 (+3.89) | -47.6 (-1.74) | -20.78 (-2.15) | -24.71* (+1.63) | 91.06 (+5.05) | -24.13 (-0.56) |
| `trend15_carry15` | n/c | n/c | -40.06 (+0.62) | -49.38 (-3.52) | -21.03 (-2.40) | -29.11* (-2.77) | 73.34 (-12.66) | -24.63 (-1.06) |
| `trend30_carry30` | n/c | n/c | -34.76 (+5.92) | -48.46 (-2.60) | -21.85 (-3.22) | -23.89* (+2.45) | 93.49 (+7.49) | -24.42 (-0.85) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 98, 130, 165, 200, 231
ordering against reference stable across the band: `True`

| arm | 62 | 98 | 130 | 165 | 200 | 231 | vs cheap at each point |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `base_trend30` | -- | -- | -- | -- | -- | -- | +2.00, +1.96, +1.93, +1.90, +1.86, +1.83 |
| `base_no_trend` | -2.00 | -1.96 | -1.93 | -1.90 | -1.86 | -1.83 | +0.00, +0.00, +0.00, +0.00, +0.00, +0.00 |
| `carry30_no_trend` | -0.32 | -0.31 | -0.30 | -0.30 | -0.29 | -0.28 | +1.68, +1.65, +1.63, +1.60, +1.57, +1.55 |
| `trend30_carrystack10` | +0.56 | +0.55 | +0.54 | +0.53 | +0.52 | +0.52 | +2.56, +2.51, +2.47, +2.43, +2.39, +2.35 |
| `trend30_carrystack20` | +1.12 | +1.10 | +1.08 | +1.07 | +1.05 | +1.03 | +3.12, +3.06, +3.02, +2.96, +2.91, +2.86 |
| `trend15_carry15` | -0.16 | -0.16 | -0.15 | -0.15 | -0.14 | -0.14 | +1.84, +1.81, +1.78, +1.75, +1.72, +1.69 |
| `trend30_carry30` | +1.68 | +1.65 | +1.63 | +1.60 | +1.57 | +1.55 | +3.68, +3.61, +3.56, +3.50, +3.44, +3.38 |

## Panel `secondary` (secondary): 1985-01..2026-02, 494 months, trend `aqr_tsmom`, carry `published`

AQR TSMOM replaces the own book; 1985-01..2026-02, the carry file's end. Expected 494 months.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.8948 | 14.5159 | 15.9621 | 0.7986 | -46.71 | 41 | 1.0 | 3.4501 |
| `base_no_trend` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 12.3995 | 11.1312 | 15.4819 | 0.5969 | -50.33 | 73 | 0.2899 | 1.0 |
| `carry30_no_trend` | 1.300 | 1.000 | 0.000 | 0.300 | 0.000 | 13.722 | 12.3207 | 16.2254 | 0.6513 | -52.78 | 51 | 0.4424 | 1.5262 |
| `trend30_carrystack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 16.3357 | 14.9177 | 16.1703 | 0.8157 | -47.58 | 39 | 1.1644 | 4.0173 |
| `trend30_carrystack20` | 1.522 | 1.022 | 0.300 | 0.200 | 0.000 | 16.7766 | 15.3095 | 16.4379 | 0.8294 | -48.45 | 39 | 1.3521 | 4.6647 |
| `trend15_carry15` | 1.311 | 1.011 | 0.150 | 0.150 | 0.000 | 14.8084 | 13.4449 | 15.9341 | 0.7316 | -49.8 | 50 | 0.6699 | 2.3112 |
| `trend30_carry30` | 1.622 | 1.022 | 0.300 | 0.300 | 0.000 | 17.2175 | 15.6911 | 16.7618 | 0.8397 | -49.32 | 39 | 1.5653 | 5.4003 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +3.50 [+2.28, +4.65] MDE 1.63 9y `exploratory` | +0.72 [-1.26, +2.72] MDE 2.71 577y `unresolved` | +3.23 [+1.97, +4.40] MDE 1.64 11y `exploratory` | +3.15 [+1.98, +4.30] MDE 1.74 12y `exploratory` | -- |
| `base_no_trend` | identical | identical | identical | -0.00 [-0.00, +0.00] MDE 0.00 166y `rejected` | -3.50 [-4.65, -2.28] MDE 1.63 9y `rejected` |
| `carry30_no_trend` | +1.32 [+0.35, +2.28] MDE 1.32 41y `exploratory` | -1.26 [-2.99, +0.49] MDE 2.24 130y `rejected` | +0.91 [-0.11, +1.92] MDE 1.31 86y `unresolved` | +0.81 [-0.35, +1.93] MDE 1.35 107y `unresolved` | -2.17 [-3.44, -0.96] MDE 1.98 34y `rejected` |
| `trend30_carrystack10` | +3.94 [+2.58, +5.23] MDE 1.74 8y `exploratory` | +0.30 [-2.15, +2.78] MDE 3.27 4790y `unresolved` | +3.55 [+2.14, +4.88] MDE 1.75 10y `exploratory` | +3.47 [+2.11, +4.84] MDE 1.86 11y `exploratory` | +0.44 [+0.12, +0.76] MDE 0.44 41y `exploratory` |
| `trend30_carrystack20` | +4.38 [+2.83, +5.87] MDE 1.94 8y `exploratory` | -0.12 [-3.05, +2.90] MDE 3.90 45335y `rejected` | +3.85 [+2.21, +5.39] MDE 1.96 11y `exploratory` | +3.74 [+2.15, +5.37] MDE 2.07 12y `exploratory` | +0.88 [+0.23, +1.52] MDE 0.88 41y `exploratory` |
| `trend15_carry15` | +2.41 [+1.52, +3.27] MDE 1.11 9y `exploratory` | -0.27 [-2.00, +1.51] MDE 2.28 2950y `rejected` | +2.16 [+1.23, +3.05] MDE 1.11 11y `exploratory` | +2.10 [+1.16, +3.03] MDE 1.17 12y `exploratory` | -1.09 [-1.72, -0.48] MDE 0.99 34y `rejected` |
| `trend30_carry30` | +4.82 [+3.03, +6.53] MDE 2.21 9y `exploratory` | -0.54 [-4.00, +3.02] MDE 4.56 2955y `rejected` | +4.11 [+2.21, +5.93] MDE 2.23 12y `exploratory` | +3.97 [+2.07, +5.89] MDE 2.36 13y `exploratory` | +1.32 [+0.35, +2.28] MDE 1.32 41y `exploratory` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | second_half | flat_equity_decade | four_class_carry | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +5.29 | +1.70 | +3.47 | +4.52 | +3.47 | +0.98 | +0.98 |
| `base_no_trend` | -5.29 | -1.70 | -3.47 | -4.52 | -3.47 | -0.98 | -0.98 |
| `carry30_no_trend` | -2.90 | -1.45 | -2.21 | -2.22 | -2.21 | -1.09 | -2.20 |
| `trend30_carrystack10` | +0.80 | +0.08 | +0.42 | +0.77 | +0.42 | -0.03 | -0.41 |
| `trend30_carrystack20` | +1.60 | +0.17 | +0.84 | +1.53 | +0.84 | -0.07 | -0.82 |
| `trend15_carry15` | -1.45 | -0.73 | -1.11 | -1.11 | -1.11 | -0.54 | -1.10 |
| `trend30_carry30` | +2.39 | +0.25 | +1.26 | +2.30 | +1.26 | -0.10 | -1.22 |

### Leg correlations: 494 months, worst decile = 49 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.083 | 0.021 |
| equity_carry | 0.152 | 0.227 |
| trend_carry | 0.101 | -0.036 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 9.27 | 15.48 | -8.231 | 0.0 |
| trend | 12.15 | 12.5 | 2.575 | 0.694 |
| carry | 5.52 | 10.08 | -0.699 | 0.449 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1985-01..2005-07 | 247 | 0.176 | 0.036 | 0.057 | 0.064 | 0.046 | 9.09 | 18.17 | 8.65 |
| panel_second_half | 2005-08..2026-02 | 247 | 0.008 | 0.276 | -0.209 | -0.091 | 0.444 | 1.96 | 6.13 | 9.89 |
| second_half | 1985-01..2025-05 | 485 | 0.096 | 0.155 | -0.081 | -0.033 | 0.218 | 5.3 | 12.07 | 9.11 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.281 | 0.152 | -0.268 | 0.25 | 0.507 | 8.78 | 16.56 | -4.32 |
| four_class_carry | 1985-01..2025-05 | 485 | 0.096 | 0.155 | -0.081 | -0.033 | 0.218 | 5.3 | 12.07 | 9.11 |
| post_2009 | 2009-01..2025-05 | 197 | -0.026 | 0.253 | -0.202 | -0.114 | 0.292 | 0.77 | 3.47 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | 0.029 | 0.17 | -0.26 | -0.466 | 0.609 | -2.96 | 3.55 | 12.12 |

Sum rule against the cheap control: both 4.8181 = trend 3.4953 + carry 1.3225 + residual 0.0002 pp/yr.

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (1 ep.) |
| `base_no_trend` | -0.565 (0.327) | 0.0219 (0.41) | -4.36 (3 ep.) | -6.83 (1 ep.) |
| `carry30_no_trend` | -0.803 (0.347) | 0.0658 (0.94) | -4.39 (3 ep.) | -7.68 (1 ep.) |
| `trend30_carrystack10` | -0.079 (0.429) | 0.0146 (1.43) | 0.02 (3 ep.) | -0.31 (1 ep.) |
| `trend30_carrystack20` | -0.158 (0.429) | 0.0293 (1.43) | 0.06 (3 ep.) | -0.63 (1 ep.) |
| `trend15_carry15` | -0.402 (0.347) | 0.0329 (0.94) | -2.21 (3 ep.) | -3.92 (1 ep.) |
| `trend30_carry30` | -0.238 (0.429) | 0.0439 (1.43) | 0.12 (3 ep.) | -0.94 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -37.96 (+0.00) | -46.71 (+0.00) | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `base_no_trend` | n/c | n/c | -45.03 (-7.07) | -50.33 (-3.63) | -20.22 (-2.38) | n/c | n/c | -24.86 (-6.83) |
| `carry30_no_trend` | n/c | n/c | -39.49 (-1.53) | -52.78 (-6.08) | -23.4 (-5.56) | n/c | n/c | -25.71 (-7.68) |
| `trend30_carrystack10` | n/c | n/c | -35.95 (+2.01) | -47.58 (-0.88) | -18.92 (-1.08) | n/c | n/c | -18.34 (-0.31) |
| `trend30_carrystack20` | n/c | n/c | -33.89 (+4.07) | -48.45 (-1.75) | -19.99 (-2.15) | n/c | n/c | -18.65 (-0.63) |
| `trend15_carry15` | n/c | n/c | -38.71 (-0.75) | -49.8 (-3.09) | -20.64 (-2.80) | n/c | n/c | -21.94 (-3.92) |
| `trend30_carry30` | n/c | n/c | -31.77 (+6.19) | -49.32 (-2.61) | -21.05 (-3.21) | n/c | n/c | -18.97 (-0.94) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 98, 130, 165, 200, 231
ordering against reference stable across the band: `True`

| arm | 62 | 98 | 130 | 165 | 200 | 231 | vs cheap at each point |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `base_trend30` | -- | -- | -- | -- | -- | -- | +3.50, +3.46, +3.43, +3.39, +3.36, +3.33 |
| `base_no_trend` | -3.50 | -3.46 | -3.43 | -3.39 | -3.36 | -3.33 | +0.00, +0.00, +0.00, +0.00, +0.00, +0.00 |
| `carry30_no_trend` | -2.17 | -2.16 | -2.16 | -2.15 | -2.14 | -2.13 | +1.32, +1.30, +1.27, +1.25, +1.22, +1.20 |
| `trend30_carrystack10` | +0.44 | +0.43 | +0.42 | +0.42 | +0.41 | +0.40 | +3.94, +3.89, +3.85, +3.81, +3.76, +3.73 |
| `trend30_carrystack20` | +0.88 | +0.86 | +0.85 | +0.83 | +0.81 | +0.80 | +4.38, +4.32, +4.28, +4.22, +4.17, +4.12 |
| `trend15_carry15` | -1.09 | -1.08 | -1.08 | -1.07 | -1.07 | -1.07 | +2.41, +2.38, +2.35, +2.32, +2.29, +2.26 |
| `trend30_carry30` | +1.32 | +1.30 | +1.27 | +1.25 | +1.22 | +1.20 | +4.82, +4.76, +4.70, +4.64, +4.58, +4.52 |

## Panel `post_publication_check` (check): 2013-09..2026-02, 150 months, trend `aqr_tsmom`, carry `published`

A CHECK, NOT A TEST: 150 months after the carry paper circulated, on which no floor under about 1 pp/yr exists for any carry arm.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.3702 | 14.2228 | 14.6254 | 0.9331 | -18.48 | 20 | 1.0 | 1.1244 |
| `base_no_trend` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 14.15 | 12.9825 | 14.845 | 0.8377 | -24.86 | 23 | 0.8894 | 1.0 |
| `carry30_no_trend` | 1.300 | 1.000 | 0.000 | 0.300 | 0.000 | 13.293 | 12.025 | 15.533 | 0.7458 | -25.71 | 23 | 0.8133 | 0.9145 |
| `trend30_carrystack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 15.0846 | 13.9107 | 14.8212 | 0.9017 | -18.92 | 14 | 0.9705 | 1.0912 |
| `trend30_carrystack20` | 1.522 | 1.022 | 0.300 | 0.200 | 0.000 | 14.7989 | 13.5902 | 15.0708 | 0.868 | -19.99 | 14 | 0.9411 | 1.0582 |
| `trend15_carry15` | 1.311 | 1.011 | 0.150 | 0.150 | 0.000 | 14.3316 | 13.1515 | 14.9063 | 0.8464 | -21.94 | 18 | 0.9034 | 1.0158 |
| `trend30_carry30` | 1.622 | 1.022 | 0.300 | 0.300 | 0.000 | 14.5133 | 13.2612 | 15.3718 | 0.8326 | -21.12 | 15 | 0.912 | 1.0255 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.22 [-0.67, +3.35] MDE 3.11 81y `unresolved` | -2.58 [-5.70, +0.67] MDE 5.32 53y `rejected` | +1.40 [-0.45, +3.50] MDE 3.08 60y `unresolved` | +0.64 [-0.90, +2.35] MDE 3.42 273y `unresolved` | -- |
| `base_no_trend` | identical | identical | identical | -0.00 [-0.00, +0.00] MDE 0.00 32y `rejected` | -1.22 [-3.35, +0.67] MDE 3.11 81y `rejected` |
| `carry30_no_trend` | -0.86 [-2.10, +0.36] MDE 2.19 82y `rejected` | -4.40 [-6.59, -2.25] MDE 3.85 10y `rejected` | -1.40 [-2.68, -0.15] MDE 2.17 30y `rejected` | -1.30 [-3.19, +0.46] MDE 2.72 42y `rejected` | -2.08 [-4.54, +0.06] MDE 3.68 39y `rejected` |
| `trend30_carrystack10` | +0.93 [-1.05, +3.11] MDE 3.24 151y `unresolved` | -4.04 [-7.75, -0.28] MDE 6.30 30y `rejected` | +0.95 [-1.03, +3.12] MDE 3.24 144y `unresolved` | +0.23 [-1.54, +2.19] MDE 3.65 2421y `unresolved` | -0.29 [-0.70, +0.12] MDE 0.73 82y `rejected` |
| `trend30_carrystack20` | +0.65 [-1.52, +2.90] MDE 3.53 369y `unresolved` | -5.51 [-9.88, -1.19] MDE 7.37 22y `rejected` | +0.47 [-1.74, +2.74] MDE 3.55 714y `unresolved` | -0.21 [-2.40, +2.11] MDE 4.08 3545y `rejected` | -0.57 [-1.40, +0.24] MDE 1.46 82y `rejected` |
| `trend15_carry15` | +0.18 [-1.01, +1.39] MDE 1.96 1460y `unresolved` | -3.49 [-6.00, -1.04] MDE 4.25 19y `rejected` | +0.13 [-1.07, +1.35] MDE 1.97 2739y `unresolved` | -0.20 [-1.53, +1.18] MDE 2.31 1316y `rejected` | -1.04 [-2.27, +0.03] MDE 1.84 39y `rejected` |
| `trend30_carry30` | +0.36 [-2.02, +2.78] MDE 3.93 1459y `unresolved` | -6.98 [-12.01, -2.07] MDE 8.50 19y `rejected` | -0.06 [-2.54, +2.43] MDE 3.97 63559y `rejected` | -0.68 [-3.37, +2.10] MDE 4.66 447y `rejected` | -0.86 [-2.10, +0.36] MDE 2.19 82y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | second_half | four_class_carry | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +1.69 | +0.75 | +0.98 | +0.98 | +0.98 | +0.98 |
| `base_no_trend` | -1.69 | -0.75 | -0.98 | -0.98 | -0.98 | -0.98 |
| `carry30_no_trend` | -2.78 | -1.38 | -2.20 | -2.20 | -2.20 | -2.20 |
| `trend30_carrystack10` | -0.36 | -0.21 | -0.41 | -0.41 | -0.41 | -0.41 |
| `trend30_carrystack20` | -0.72 | -0.42 | -0.82 | -0.82 | -0.82 | -0.82 |
| `trend15_carry15` | -1.39 | -0.69 | -1.10 | -1.10 | -1.10 | -1.10 |
| `trend30_carry30` | -1.08 | -0.63 | -1.22 | -1.22 | -1.22 | -1.22 |

### Leg correlations: 150 months, worst decile = 15 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.262 | -0.519 |
| equity_carry | 0.158 | 0.615 |
| trend_carry | 0.055 | -0.468 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 12.46 | 14.84 | -7.557 | 0.0 |
| trend | 4.34 | 13.32 | 2.203 | 0.6 |
| carry | -1.74 | 9.22 | -1.501 | 0.4 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 2013-09..2019-11 | 75 | -0.038 | 0.321 | -0.164 | -0.488 | 0.387 | -2.5 | 5.92 | 12.22 |
| panel_second_half | 2019-12..2026-02 | 75 | 0.114 | 0.094 | -0.337 | -0.544 | 0.59 | -0.98 | 2.75 | 12.71 |
| second_half | 2013-09..2025-05 | 141 | 0.029 | 0.17 | -0.26 | -0.466 | 0.609 | -2.96 | 3.55 | 12.12 |
| four_class_carry | 2013-09..2025-05 | 141 | 0.029 | 0.17 | -0.26 | -0.466 | 0.609 | -2.96 | 3.55 | 12.12 |
| post_2009 | 2013-09..2025-05 | 141 | 0.029 | 0.17 | -0.26 | -0.466 | 0.609 | -2.96 | 3.55 | 12.12 |
| post_publication | 2013-09..2025-05 | 141 | 0.029 | 0.17 | -0.26 | -0.466 | 0.609 | -2.96 | 3.55 | 12.12 |

Sum rule against the cheap control: both 0.3633 = trend 1.2202 + carry -0.857 + residual 0.0002 pp/yr.

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (1 ep.) | 0.0 (1 ep.) |
| `base_no_trend` | -0.469 (0.4) | -0.0188 (-0.3) | -2.38 (1 ep.) | -6.83 (1 ep.) |
| `carry30_no_trend` | -0.947 (0.133) | 0.0825 (0.93) | -5.56 (1 ep.) | -7.68 (1 ep.) |
| `trend30_carrystack10` | -0.159 (0.333) | 0.0338 (2.27) | -1.08 (1 ep.) | -0.31 (1 ep.) |
| `trend30_carrystack20` | -0.319 (0.333) | 0.0676 (2.27) | -2.15 (1 ep.) | -0.63 (1 ep.) |
| `trend15_carry15` | -0.473 (0.133) | 0.0413 (0.93) | -2.8 (1 ep.) | -3.92 (1 ep.) |
| `trend30_carry30` | -0.478 (0.333) | 0.1013 (2.27) | -3.21 (1 ep.) | -0.94 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | n/c | n/c | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `base_no_trend` | n/c | n/c | n/c | n/c | -20.22 (-2.38) | n/c | n/c | -24.86 (-6.83) |
| `carry30_no_trend` | n/c | n/c | n/c | n/c | -23.4 (-5.56) | n/c | n/c | -25.71 (-7.68) |
| `trend30_carrystack10` | n/c | n/c | n/c | n/c | -18.92 (-1.08) | n/c | n/c | -18.34 (-0.31) |
| `trend30_carrystack20` | n/c | n/c | n/c | n/c | -19.99 (-2.15) | n/c | n/c | -18.65 (-0.63) |
| `trend15_carry15` | n/c | n/c | n/c | n/c | -20.64 (-2.80) | n/c | n/c | -21.94 (-3.92) |
| `trend30_carry30` | n/c | n/c | n/c | n/c | -21.05 (-3.21) | n/c | n/c | -18.97 (-0.94) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 98, 130, 165, 200, 231
ordering against reference stable across the band: `True`

| arm | 62 | 98 | 130 | 165 | 200 | 231 | vs cheap at each point |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `base_trend30` | -- | -- | -- | -- | -- | -- | +1.22, +1.18, +1.15, +1.12, +1.08, +1.05 |
| `base_no_trend` | -1.22 | -1.18 | -1.15 | -1.12 | -1.08 | -1.05 | +0.00, +0.00, +0.00, +0.00, +0.00, +0.00 |
| `carry30_no_trend` | -2.08 | -2.07 | -2.06 | -2.05 | -2.04 | -2.04 | -0.86, -0.88, -0.91, -0.93, -0.96, -0.98 |
| `trend30_carrystack10` | -0.29 | -0.29 | -0.30 | -0.31 | -0.32 | -0.33 | +0.93, +0.89, +0.85, +0.81, +0.76, +0.72 |
| `trend30_carrystack20` | -0.57 | -0.59 | -0.61 | -0.62 | -0.64 | -0.66 | +0.65, +0.60, +0.55, +0.50, +0.44, +0.40 |
| `trend15_carry15` | -1.04 | -1.03 | -1.03 | -1.03 | -1.02 | -1.02 | +0.18, +0.15, +0.12, +0.09, +0.06, +0.03 |
| `trend30_carry30` | -0.86 | -0.88 | -0.91 | -0.93 | -0.96 | -0.98 | +0.36, +0.30, +0.24, +0.18, +0.12, +0.07 |

## Panel `carry_cost_1pp` (sensitivity): 1929-01..2025-05, 1157 months, trend `own_4_asset_book`, carry `cost_1pp`

The primary panel with 1.0 pp/yr charged on every unit of carry notional.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 12.9362 | 11.0753 | 18.9893 | 0.51 | -82.78 | 164 | 1.0 | 5.1688 |
| `base_no_trend` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 10.9532 | 9.21 | 18.4972 | 0.4165 | -83.67 | 184 | 0.1935 | 1.0 |
| `carry30_no_trend` | 1.300 | 1.000 | 0.000 | 0.300 | 0.000 | 12.3851 | 10.4823 | 19.3067 | 0.4734 | -81.02 | 191 | 0.6361 | 3.288 |
| `trend30_carrystack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 13.4136 | 11.5106 | 19.1944 | 0.5295 | -81.88 | 88 | 1.4974 | 7.7399 |
| `trend30_carrystack20` | 1.522 | 1.022 | 0.300 | 0.200 | 0.000 | 13.891 | 11.9307 | 19.4763 | 0.5464 | -80.95 | 87 | 2.2165 | 11.4564 |
| `trend15_carry15` | 1.311 | 1.011 | 0.150 | 0.150 | 0.000 | 12.6607 | 10.8106 | 18.9819 | 0.4958 | -81.89 | 182 | 0.8145 | 4.2102 |
| `trend30_carry30` | 1.622 | 1.022 | 0.300 | 0.300 | 0.000 | 14.3684 | 12.3356 | 19.8315 | 0.5608 | -79.98 | 94 | 3.2429 | 16.762 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.98 [+1.10, +2.73] MDE 1.06 27y `exploratory` | -0.30 [-1.66, +1.16] MDE 1.97 4181y `rejected` | +1.79 [+0.94, +2.58] MDE 1.06 34y `exploratory` | +1.59 [+0.86, +2.34] MDE 1.11 45y `exploratory` | -- |
| `base_no_trend` | identical | identical | identical | -0.00 [-0.00, +0.00] MDE 0.00 424y `rejected` | -1.98 [-2.73, -1.10] MDE 1.06 27y `rejected` |
| `carry30_no_trend` | +1.43 [+0.44, +2.26] MDE 1.06 53y `exploratory` | -0.70 [-2.07, +0.79] MDE 1.80 643y `rejected` | +1.12 [+0.15, +1.98] MDE 1.06 86y `exploratory` | +0.79 [-0.03, +1.67] MDE 1.07 172y `unresolved` | -0.55 [-1.70, +0.52] MDE 1.44 657y `rejected` |
| `trend30_carrystack10` | +2.46 [+1.61, +3.25] MDE 1.14 21y `exploratory` | -0.53 [-2.18, +1.35] MDE 2.43 2020y `rejected` | +2.19 [+1.39, +2.99] MDE 1.14 26y `exploratory` | +1.90 [+1.18, +2.75] MDE 1.18 36y `exploratory` | +0.48 [+0.15, +0.75] MDE 0.35 53y `exploratory` |
| `trend30_carrystack20` | +2.94 [+1.96, +3.80] MDE 1.32 19y `exploratory` | -0.76 [-2.85, +1.46] MDE 2.95 1433y `rejected` | +2.56 [+1.65, +3.49] MDE 1.32 26y `exploratory` | +2.16 [+1.33, +3.20] MDE 1.36 37y `exploratory` | +0.95 [+0.30, +1.51] MDE 0.71 53y `exploratory` |
| `trend15_carry15` | +1.71 [+1.07, +2.18] MDE 0.78 20y `exploratory` | -0.50 [-1.73, +0.71] MDE 1.74 1180y `rejected` | +1.52 [+0.93, +2.02] MDE 0.77 25y `exploratory` | +1.29 [+0.83, +1.86] MDE 0.79 35y `exploratory` | -0.28 [-0.85, +0.26] MDE 0.72 657y `rejected` |
| `trend30_carry30` | +3.42 [+2.14, +4.37] MDE 1.55 20y `exploratory` | -1.00 [-3.47, +1.42] MDE 3.49 1181y `rejected` | +2.90 [+1.75, +3.94] MDE 1.56 28y `exploratory` | +2.38 [+1.42, +3.59] MDE 1.60 42y `exploratory` | +1.43 [+0.44, +2.26] MDE 1.06 53y `exploratory` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | first_half | second_half | flat_equity_decade | three_class_carry | four_class_carry | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +1.98 | +1.99 | +1.98 | +1.99 | +2.84 | +1.97 | +2.00 | +0.37 | +0.04 |
| `base_no_trend` | -1.98 | -1.99 | -1.98 | -1.99 | -2.84 | -1.97 | -2.00 | -0.37 | -0.04 |
| `carry30_no_trend` | -0.16 | -0.94 | -0.15 | -0.95 | -0.84 | -0.47 | -0.62 | -0.77 | -1.56 |
| `trend30_carrystack10` | +0.61 | +0.35 | +0.61 | +0.34 | +0.67 | +0.50 | +0.46 | -0.13 | -0.51 |
| `trend30_carrystack20` | +1.21 | +0.70 | +1.22 | +0.69 | +1.33 | +1.00 | +0.92 | -0.27 | -1.02 |
| `trend15_carry15` | -0.08 | -0.47 | -0.08 | -0.48 | -0.42 | -0.24 | -0.31 | -0.39 | -0.78 |
| `trend30_carry30` | +1.82 | +1.05 | +1.83 | +1.03 | +2.00 | +1.49 | +1.38 | -0.40 | -1.52 |

### Leg correlations: 1157 months, worst decile = 115 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.074 | 0.072 |
| equity_carry | 0.119 | 0.219 |
| trend_carry | 0.063 | 0.066 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 7.75 | 18.53 | -9.359 | 0.0 |
| trend | 7.22 | 12.38 | 1.569 | 0.626 |
| carry | 5.89 | 12.38 | 0.085 | 0.557 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1929-01..1977-02 | 578 | 0.036 | 0.13 | -0.127 | 0.139 | 0.281 | 7.18 | 7.25 | 7.12 |
| panel_second_half | 1977-03..2025-05 | 579 | 0.102 | 0.098 | -0.011 | -0.006 | 0.194 | 4.6 | 7.19 | 8.38 |
| first_half | 1929-01..1977-03 | 579 | 0.036 | 0.13 | -0.127 | 0.139 | 0.281 | 7.21 | 7.26 | 7.08 |
| second_half | 1977-04..2025-05 | 578 | 0.102 | 0.099 | -0.011 | -0.006 | 0.194 | 4.56 | 7.18 | 8.42 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.13 | 0.152 | -0.331 | -0.281 | 0.507 | 7.78 | 10.93 | -4.32 |
| three_class_carry | 1929-01..1974-01 | 541 | 0.062 | 0.136 | -0.103 | 0.165 | 0.284 | 6.09 | 7.18 | 7.48 |
| four_class_carry | 1974-02..2025-05 | 616 | 0.069 | 0.09 | -0.047 | -0.02 | 0.156 | 5.71 | 7.25 | 7.99 |
| post_2009 | 2009-01..2025-05 | 197 | -0.01 | 0.253 | -0.049 | -0.255 | 0.292 | -0.23 | 1.41 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | -0.026 | 0.17 | -0.067 | -0.399 | 0.609 | -3.96 | 0.43 | 12.12 |

Sum rule against the cheap control: both 3.4152 = trend 1.9831 + carry 1.4319 + residual 0.0002 pp/yr.

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (5 ep.) | 0.0 (3 ep.) |
| `base_no_trend` | -0.239 (0.426) | -0.038 (-1.29) | -2.09 (5 ep.) | -14.98 (3 ep.) |
| `carry30_no_trend` | -0.242 (0.487) | -0.0551 (-1.44) | -2.47 (5 ep.) | -11.98 (3 ep.) |
| `trend30_carrystack10` | -0.001 (0.557) | -0.0057 (-0.84) | -0.12 (5 ep.) | 1.21 (3 ep.) |
| `trend30_carrystack20` | -0.002 (0.557) | -0.0114 (-0.84) | -0.23 (5 ep.) | 2.41 (3 ep.) |
| `trend15_carry15` | -0.121 (0.487) | -0.0276 (-1.44) | -1.24 (5 ep.) | -6.09 (3 ep.) |
| `trend30_carry30` | -0.002 (0.557) | -0.0171 (-0.84) | -0.3 (5 ep.) | 3.6 (3 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | -82.78 (+0.00) | -50.34 (+0.00) | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -34.29 (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `base_no_trend` | -83.67 (-0.89) | -49.47 (+0.87) | -45.03 (-4.35) | -50.33 (-4.47) | -20.22 (-1.59) | -46.54 (-12.24) | 54.6 (-31.41) | -24.86 (-1.29) |
| `carry30_no_trend` | -81.02 (+1.77) | -53.3 (-2.95) | -39.88 (+0.80) | -52.98 (-7.12) | -23.45 (-4.82) | -40.7 (-6.41) | 58.78 (-27.22) | -25.88 (-2.32) |
| `trend30_carrystack10` | -81.88 (+0.90) | -51.62 (-1.27) | -38.89 (+1.79) | -46.81 (-0.95) | -19.72 (-1.09) | -32.0 (+2.29) | 87.68 (+1.67) | -23.91 (-0.34) |
| `trend30_carrystack20` | -80.95 (+1.84) | -52.86 (-2.52) | -37.06 (+3.62) | -47.74 (-1.88) | -20.81 (-2.18) | -29.65 (+4.65) | 89.27 (+3.27) | -24.25 (-0.68) |
| `trend15_carry15` | -81.89 (+0.89) | -51.82 (-1.48) | -40.25 (+0.43) | -49.49 (-3.63) | -21.06 (-2.43) | -37.54 (-3.25) | 72.12 (-13.88) | -24.72 (-1.15) |
| `trend30_carry30` | -79.98 (+2.80) | -54.09 (-3.74) | -35.18 (+5.50) | -48.67 (-2.81) | -21.89 (-3.26) | -27.23 (+7.06) | 90.78 (+4.78) | -24.59 (-1.02) |

## Panel `carry_cost_2pp` (sensitivity): 1929-01..2025-05, 1157 months, trend `own_4_asset_book`, carry `cost_2pp`

The primary panel with 2.0 pp/yr charged on every unit of carry notional, the pessimistic bound.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 12.9362 | 11.0753 | 18.9893 | 0.51 | -82.78 | 164 | 1.0 | 5.1688 |
| `base_no_trend` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 10.9532 | 9.21 | 18.4972 | 0.4165 | -83.67 | 184 | 0.1935 | 1.0 |
| `carry30_no_trend` | 1.300 | 1.000 | 0.000 | 0.300 | 0.000 | 12.0851 | 10.1844 | 19.3067 | 0.4579 | -81.19 | 191 | 0.4899 | 2.5322 |
| `trend30_carrystack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 13.3136 | 11.4114 | 19.1944 | 0.5243 | -81.93 | 88 | 1.3705 | 7.084 |
| `trend30_carrystack20` | 1.522 | 1.022 | 0.300 | 0.200 | 0.000 | 13.691 | 11.7324 | 19.4763 | 0.5361 | -81.06 | 88 | 1.8571 | 9.5987 |
| `trend15_carry15` | 1.311 | 1.011 | 0.150 | 0.150 | 0.000 | 12.5107 | 10.6617 | 18.9819 | 0.4879 | -81.97 | 183 | 0.7139 | 3.69 |
| `trend30_carry30` | 1.622 | 1.022 | 0.300 | 0.300 | 0.000 | 14.0684 | 12.0382 | 19.8315 | 0.5457 | -80.16 | 95 | 2.488 | 12.8596 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.98 [+1.29, +2.64] MDE 1.06 27y `exploratory` | -0.30 [-1.76, +1.14] MDE 1.97 4181y `rejected` | +1.79 [+1.04, +2.47] MDE 1.06 34y `exploratory` | +1.59 [+0.83, +2.40] MDE 1.11 45y `exploratory` | -- |
| `base_no_trend` | identical | identical | identical | -0.00 [-0.00, +0.00] MDE 0.00 424y `rejected` | -1.98 [-2.64, -1.29] MDE 1.06 27y `rejected` |
| `carry30_no_trend` | +1.13 [+0.30, +1.89] MDE 1.06 84y `exploratory` | -1.00 [-2.50, +0.87] MDE 1.80 314y `rejected` | +0.82 [-0.00, +1.71] MDE 1.06 160y `unresolved` | +0.49 [-0.46, +1.50] MDE 1.07 445y `unresolved` | -0.85 [-2.14, +0.26] MDE 1.44 276y `rejected` |
| `trend30_carrystack10` | +2.36 [+1.60, +3.09] MDE 1.14 22y `exploratory` | -0.63 [-2.40, +1.27] MDE 2.43 1431y `rejected` | +2.09 [+1.22, +2.91] MDE 1.14 29y `exploratory` | +1.80 [+0.99, +2.66] MDE 1.18 40y `exploratory` | +0.38 [+0.10, +0.63] MDE 0.35 84y `exploratory` |
| `trend30_carrystack20` | +2.74 [+1.82, +3.67] MDE 1.32 22y `exploratory` | -0.96 [-3.19, +1.51] MDE 2.95 900y `rejected` | +2.36 [+1.36, +3.28] MDE 1.32 30y `exploratory` | +1.96 [+0.94, +2.93] MDE 1.36 45y `exploratory` | +0.75 [+0.20, +1.26] MDE 0.71 84y `exploratory` |
| `trend15_carry15` | +1.56 [+1.03, +2.10] MDE 0.78 24y `exploratory` | -0.65 [-2.04, +0.88] MDE 1.74 697y `rejected` | +1.37 [+0.75, +1.90] MDE 0.77 31y `exploratory` | +1.14 [+0.53, +1.73] MDE 0.79 44y `exploratory` | -0.43 [-1.07, +0.13] MDE 0.72 276y `rejected` |
| `trend30_carry30` | +3.12 [+2.05, +4.20] MDE 1.55 24y `exploratory` | -1.30 [-4.08, +1.75] MDE 3.49 697y `rejected` | +2.60 [+1.33, +3.67] MDE 1.56 35y `exploratory` | +2.08 [+0.93, +3.25] MDE 1.60 55y `exploratory` | +1.13 [+0.30, +1.89] MDE 1.06 84y `exploratory` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | first_half | second_half | flat_equity_decade | three_class_carry | four_class_carry | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +1.98 | +1.99 | +1.98 | +1.99 | +2.84 | +1.97 | +2.00 | +0.37 | +0.04 |
| `base_no_trend` | -1.98 | -1.99 | -1.98 | -1.99 | -2.84 | -1.97 | -2.00 | -0.37 | -0.04 |
| `carry30_no_trend` | -0.46 | -1.24 | -0.45 | -1.25 | -1.14 | -0.77 | -0.92 | -1.07 | -1.86 |
| `trend30_carrystack10` | +0.51 | +0.25 | +0.51 | +0.24 | +0.57 | +0.40 | +0.36 | -0.23 | -0.61 |
| `trend30_carrystack20` | +1.01 | +0.50 | +1.02 | +0.49 | +1.13 | +0.80 | +0.72 | -0.47 | -1.22 |
| `trend15_carry15` | -0.23 | -0.62 | -0.23 | -0.63 | -0.57 | -0.39 | -0.46 | -0.54 | -0.93 |
| `trend30_carry30` | +1.52 | +0.75 | +1.53 | +0.73 | +1.70 | +1.19 | +1.08 | -0.70 | -1.82 |

### Leg correlations: 1157 months, worst decile = 115 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.074 | 0.072 |
| equity_carry | 0.119 | 0.219 |
| trend_carry | 0.063 | 0.066 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 7.75 | 18.53 | -9.359 | 0.0 |
| trend | 7.22 | 12.38 | 1.569 | 0.626 |
| carry | 4.89 | 12.38 | 0.002 | 0.557 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1929-01..1977-02 | 578 | 0.036 | 0.13 | -0.127 | 0.139 | 0.281 | 6.18 | 7.25 | 7.12 |
| panel_second_half | 1977-03..2025-05 | 579 | 0.102 | 0.098 | -0.011 | -0.006 | 0.194 | 3.6 | 7.19 | 8.38 |
| first_half | 1929-01..1977-03 | 579 | 0.036 | 0.13 | -0.127 | 0.139 | 0.281 | 6.21 | 7.26 | 7.08 |
| second_half | 1977-04..2025-05 | 578 | 0.102 | 0.099 | -0.011 | -0.006 | 0.194 | 3.56 | 7.18 | 8.42 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.13 | 0.152 | -0.331 | -0.281 | 0.507 | 6.78 | 10.93 | -4.32 |
| three_class_carry | 1929-01..1974-01 | 541 | 0.062 | 0.136 | -0.103 | 0.165 | 0.284 | 5.09 | 7.18 | 7.48 |
| four_class_carry | 1974-02..2025-05 | 616 | 0.069 | 0.09 | -0.047 | -0.02 | 0.156 | 4.71 | 7.25 | 7.99 |
| post_2009 | 2009-01..2025-05 | 197 | -0.01 | 0.253 | -0.049 | -0.255 | 0.292 | -1.23 | 1.41 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | -0.026 | 0.17 | -0.067 | -0.399 | 0.609 | -4.96 | 0.43 | 12.12 |

Sum rule against the cheap control: both 3.1152 = trend 1.9831 + carry 1.1319 + residual 0.0002 pp/yr.

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (5 ep.) | 0.0 (3 ep.) |
| `base_no_trend` | -0.239 (0.426) | -0.038 (-1.29) | -2.09 (5 ep.) | -14.98 (3 ep.) |
| `carry30_no_trend` | -0.267 (0.47) | -0.0551 (-1.44) | -2.66 (5 ep.) | -12.89 (3 ep.) |
| `trend30_carrystack10` | -0.009 (0.53) | -0.0057 (-0.84) | -0.19 (5 ep.) | 0.85 (3 ep.) |
| `trend30_carrystack20` | -0.018 (0.53) | -0.0114 (-0.84) | -0.36 (5 ep.) | 1.7 (3 ep.) |
| `trend15_carry15` | -0.133 (0.47) | -0.0276 (-1.44) | -1.34 (5 ep.) | -6.58 (3 ep.) |
| `trend30_carry30` | -0.027 (0.53) | -0.0171 (-0.84) | -0.51 (5 ep.) | 2.53 (3 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | -82.78 (+0.00) | -50.34 (+0.00) | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -34.29 (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `base_no_trend` | -83.67 (-0.89) | -49.47 (+0.87) | -45.03 (-4.35) | -50.33 (-4.47) | -20.22 (-1.59) | -46.54 (-12.24) | 54.6 (-31.41) | -24.86 (-1.29) |
| `carry30_no_trend` | -81.19 (+1.60) | -53.46 (-3.12) | -40.26 (+0.42) | -53.18 (-7.32) | -23.49 (-4.86) | -41.02 (-6.73) | 56.55 (-29.45) | -26.06 (-2.49) |
| `trend30_carrystack10` | -81.93 (+0.85) | -51.67 (-1.33) | -39.02 (+1.66) | -46.88 (-1.02) | -19.74 (-1.11) | -32.12 (+2.17) | 86.8 (+0.79) | -23.97 (-0.40) |
| `trend30_carrystack20` | -81.06 (+1.72) | -52.97 (-2.63) | -37.32 (+3.35) | -47.89 (-2.03) | -20.84 (-2.21) | -29.9 (+4.40) | 87.5 (+1.49) | -24.37 (-0.80) |
| `trend15_carry15` | -81.97 (+0.81) | -51.9 (-1.56) | -40.44 (+0.24) | -49.59 (-3.73) | -21.08 (-2.45) | -37.71 (-3.42) | 70.91 (-15.10) | -24.81 (-1.24) |
| `trend30_carry30` | -80.16 (+2.62) | -54.25 (-3.90) | -35.59 (+5.09) | -48.89 (-3.03) | -21.93 (-3.31) | -27.62 (+6.68) | 88.11 (+2.10) | -24.77 (-1.20) |

## Panel `carry_loading_0681` (sensitivity): 1929-01..2025-05, 1157 months, trend `own_4_asset_book`, carry `loading_0681`

The primary panel with the carry leg delivered at 0.681 of a unit, the loading RSST's filings show for its trend leg, applied here to the sister wrapper as an assumption; the fee is unchanged.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 12.9362 | 11.0753 | 18.9893 | 0.51 | -82.78 | 164 | 1.0 | 5.1688 |
| `base_no_trend` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 10.9532 | 9.21 | 18.4972 | 0.4165 | -83.67 | 184 | 0.1935 | 1.0 |
| `carry30_no_trend` | 1.300 | 1.000 | 0.000 | 0.300 | 0.000 | 12.0259 | 10.1883 | 18.9734 | 0.4627 | -81.84 | 188 | 0.4789 | 2.4754 |
| `trend30_carrystack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 13.2939 | 11.4057 | 19.1205 | 0.5252 | -82.15 | 89 | 1.3567 | 7.0123 |
| `trend30_carrystack20` | 1.522 | 1.022 | 0.300 | 0.200 | 0.000 | 13.6515 | 11.729 | 19.2878 | 0.5393 | -81.51 | 88 | 1.8307 | 9.4624 |
| `trend15_carry15` | 1.311 | 1.011 | 0.150 | 0.150 | 0.000 | 12.4811 | 10.6553 | 18.8578 | 0.4895 | -82.29 | 177 | 0.7031 | 3.6341 |
| `trend30_carry30` | 1.622 | 1.022 | 0.300 | 0.300 | 0.000 | 14.0091 | 12.0453 | 19.4901 | 0.5521 | -80.85 | 87 | 2.457 | 12.6997 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.98 [+1.35, +2.64] MDE 1.06 27y `exploratory` | -0.30 [-1.59, +0.90] MDE 1.97 4181y `rejected` | +1.79 [+1.14, +2.47] MDE 1.06 34y `exploratory` | +1.59 [+0.86, +2.27] MDE 1.11 45y `exploratory` | -- |
| `base_no_trend` | identical | identical | identical | -0.00 [-0.00, +0.00] MDE 0.00 424y `rejected` | -1.98 [-2.64, -1.35] MDE 1.06 27y `rejected` |
| `carry30_no_trend` | +1.07 [+0.47, +1.64] MDE 0.72 44y `exploratory` | -1.06 [-2.24, +0.17] MDE 1.66 239y `rejected` | +0.89 [+0.27, +1.50] MDE 0.72 63y `exploratory` | +0.69 [+0.17, +1.18] MDE 0.73 105y `unresolved` | -0.91 [-1.76, -0.12] MDE 1.23 177y `rejected` |
| `trend30_carrystack10` | +2.34 [+1.60, +3.07] MDE 1.10 21y `exploratory` | -0.65 [-2.23, +0.90] MDE 2.43 1340y `rejected` | +2.10 [+1.40, +2.81] MDE 1.11 27y `exploratory` | +1.84 [+1.16, +2.56] MDE 1.15 36y `exploratory` | +0.36 [+0.16, +0.55] MDE 0.24 44y `exploratory` |
| `trend30_carrystack20` | +2.70 [+1.85, +3.52] MDE 1.19 19y `exploratory` | -1.00 [-2.92, +0.95] MDE 2.92 816y `rejected` | +2.40 [+1.59, +3.17] MDE 1.20 24y `exploratory` | +2.06 [+1.29, +2.86] MDE 1.24 34y `exploratory` | +0.72 [+0.32, +1.10] MDE 0.48 44y `exploratory` |
| `trend15_carry15` | +1.53 [+1.03, +2.01] MDE 0.66 18y `exploratory` | -0.68 [-1.83, +0.47] MDE 1.71 617y `rejected` | +1.39 [+0.91, +1.85] MDE 0.66 22y `exploratory` | +1.21 [+0.77, +1.65] MDE 0.68 29y `exploratory` | -0.46 [-0.88, -0.06] MDE 0.62 177y `rejected` |
| `trend30_carry30` | +3.06 [+2.06, +4.01] MDE 1.32 18y `exploratory` | -1.36 [-3.66, +0.94] MDE 3.43 617y `rejected` | +2.68 [+1.73, +3.58] MDE 1.33 24y `exploratory` | +2.27 [+1.40, +3.12] MDE 1.37 34y `exploratory` | +1.07 [+0.47, +1.64] MDE 0.72 44y `exploratory` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | first_half | second_half | flat_equity_decade | three_class_carry | four_class_carry | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +1.98 | +1.99 | +1.98 | +1.99 | +2.84 | +1.97 | +2.00 | +0.37 | +0.04 |
| `base_no_trend` | -1.98 | -1.99 | -1.98 | -1.99 | -2.84 | -1.97 | -2.00 | -0.37 | -0.04 |
| `carry30_no_trend` | -0.64 | -1.18 | -0.64 | -1.18 | -1.38 | -0.85 | -0.96 | -0.54 | -0.98 |
| `trend30_carrystack10` | +0.45 | +0.27 | +0.45 | +0.27 | +0.49 | +0.37 | +0.35 | -0.06 | -0.31 |
| `trend30_carrystack20` | +0.89 | +0.54 | +0.90 | +0.53 | +0.97 | +0.74 | +0.69 | -0.12 | -0.63 |
| `trend15_carry15` | -0.32 | -0.59 | -0.32 | -0.59 | -0.69 | -0.43 | -0.48 | -0.27 | -0.49 |
| `trend30_carry30` | +1.34 | +0.81 | +1.34 | +0.80 | +1.46 | +1.11 | +1.04 | -0.18 | -0.94 |

### Leg correlations: 1157 months, worst decile = 115 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.074 | 0.072 |
| equity_carry | 0.119 | 0.219 |
| trend_carry | 0.063 | 0.066 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 7.75 | 18.53 | -9.359 | 0.0 |
| trend | 7.22 | 12.38 | 1.569 | 0.626 |
| carry | 4.69 | 8.43 | 0.115 | 0.574 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1929-01..1977-02 | 578 | 0.036 | 0.13 | -0.127 | 0.139 | 0.281 | 5.57 | 7.25 | 7.12 |
| panel_second_half | 1977-03..2025-05 | 579 | 0.102 | 0.098 | -0.011 | -0.006 | 0.194 | 3.82 | 7.19 | 8.38 |
| first_half | 1929-01..1977-03 | 579 | 0.036 | 0.13 | -0.127 | 0.139 | 0.281 | 5.59 | 7.26 | 7.08 |
| second_half | 1977-04..2025-05 | 578 | 0.102 | 0.099 | -0.011 | -0.006 | 0.194 | 3.79 | 7.18 | 8.42 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.13 | 0.152 | -0.331 | -0.281 | 0.507 | 5.98 | 10.93 | -4.32 |
| three_class_carry | 1929-01..1974-01 | 541 | 0.062 | 0.136 | -0.103 | 0.165 | 0.284 | 4.83 | 7.18 | 7.48 |
| four_class_carry | 1974-02..2025-05 | 616 | 0.069 | 0.09 | -0.047 | -0.02 | 0.156 | 4.57 | 7.25 | 7.99 |
| post_2009 | 2009-01..2025-05 | 197 | -0.01 | 0.253 | -0.049 | -0.255 | 0.292 | 0.52 | 1.41 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | -0.026 | 0.17 | -0.067 | -0.399 | 0.609 | -2.02 | 0.43 | 12.12 |

Sum rule against the cheap control: both 3.056 = trend 1.9831 + carry 1.0728 + residual 0.0002 pp/yr.

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (5 ep.) | 0.0 (3 ep.) |
| `base_no_trend` | -0.239 (0.426) | -0.038 (-1.29) | -2.09 (5 ep.) | -14.98 (3 ep.) |
| `carry30_no_trend` | -0.233 (0.443) | -0.0497 (-1.44) | -2.31 (5 ep.) | -12.64 (3 ep.) |
| `trend30_carrystack10` | 0.002 (0.557) | -0.0039 (-0.84) | -0.07 (5 ep.) | 0.94 (3 ep.) |
| `trend30_carrystack20` | 0.004 (0.557) | -0.0078 (-0.84) | -0.12 (5 ep.) | 1.88 (3 ep.) |
| `trend15_carry15` | -0.116 (0.443) | -0.0248 (-1.44) | -1.15 (5 ep.) | -6.46 (3 ep.) |
| `trend30_carry30` | 0.006 (0.557) | -0.0117 (-0.84) | -0.16 (5 ep.) | 2.81 (3 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | -82.78 (+0.00) | -50.34 (+0.00) | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -34.29 (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `base_no_trend` | -83.67 (-0.89) | -49.47 (+0.87) | -45.03 (-4.35) | -50.33 (-4.47) | -20.22 (-1.59) | -46.54 (-12.24) | 54.6 (-31.41) | -24.86 (-1.29) |
| `carry30_no_trend` | -81.84 (+0.94) | -52.05 (-1.71) | -41.44 (-0.77) | -52.08 (-6.22) | -22.41 (-3.78) | -42.51 (-8.22) | 58.24 (-27.77) | -25.5 (-1.93) |
| `trend30_carrystack10` | -82.15 (+0.63) | -51.19 (-0.85) | -39.42 (+1.25) | -46.48 (-0.62) | -19.37 (-0.74) | -32.7 (+1.59) | 87.44 (+1.43) | -23.78 (-0.21) |
| `trend30_carrystack20` | -81.51 (+1.27) | -52.03 (-1.69) | -38.15 (+2.53) | -47.1 (-1.24) | -20.11 (-1.48) | -31.08 (+3.22) | 88.84 (+2.84) | -23.99 (-0.43) |
| `trend15_carry15` | -82.29 (+0.49) | -51.19 (-0.84) | -41.03 (-0.36) | -49.01 (-3.16) | -20.53 (-1.90) | -38.51 (-4.21) | 71.79 (-14.21) | -24.53 (-0.96) |
| `trend30_carry30` | -80.85 (+1.93) | -52.86 (-2.52) | -36.85 (+3.83) | -47.71 (-1.85) | -20.84 (-2.21) | -29.42 (+4.87) | 90.21 (+4.20) | -24.21 (-0.64) |

## Panel `carry_shifted_one_month` (sensitivity): 1929-01..2025-05, 1157 months, trend `own_4_asset_book`, carry `shifted_one_month`

The primary panel with the carry series moved one month later. A vendor return series cannot be positionally lagged, so this is an ALIGNMENT test: it leaves the carry mean unchanged and destroys its same-month co-movement with equity and trend, so it bounds how much of each result is diversification rather than mean.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 12.9362 | 11.0753 | 18.9893 | 0.51 | -82.78 | 164 | 1.0 | 5.1688 |
| `base_no_trend` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 10.9532 | 9.21 | 18.4972 | 0.4165 | -83.67 | 184 | 0.1935 | 1.0 |
| `carry30_no_trend` | 1.300 | 1.000 | 0.000 | 0.300 | 0.000 | 12.7386 | 10.9068 | 18.9087 | 0.5021 | -80.39 | 187 | 0.9134 | 4.7211 |
| `trend30_carrystack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 13.5314 | 11.658 | 19.0311 | 0.5402 | -81.68 | 88 | 1.7018 | 8.796 |
| `trend30_carrystack20` | 1.522 | 1.022 | 0.300 | 0.200 | 0.000 | 14.1267 | 12.2254 | 19.1513 | 0.568 | -80.53 | 86 | 2.8631 | 14.7985 |
| `trend15_carry15` | 1.311 | 1.011 | 0.150 | 0.150 | 0.000 | 12.8374 | 11.0272 | 18.7578 | 0.5112 | -81.59 | 177 | 0.9814 | 5.0729 |
| `trend30_carry30` | 1.622 | 1.022 | 0.300 | 0.300 | 0.000 | 14.7219 | 12.7776 | 19.3482 | 0.5931 | -79.32 | 93 | 4.7615 | 24.6109 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.98 [+1.37, +2.68] MDE 1.06 27y `exploratory` | -0.30 [-1.57, +1.14] MDE 1.97 4181y `rejected` | +1.79 [+1.14, +2.53] MDE 1.06 34y `exploratory` | +1.59 [+0.94, +2.34] MDE 1.11 45y `exploratory` | -- |
| `base_no_trend` | identical | identical | identical | -0.00 [-0.00, +0.00] MDE 0.00 424y `rejected` | -1.98 [-2.68, -1.37] MDE 1.06 27y `rejected` |
| `carry30_no_trend` | +1.79 [+0.92, +2.56] MDE 1.05 33y `exploratory` | -0.34 [-1.74, +1.28] MDE 1.89 2923y `rejected` | +1.63 [+0.82, +2.42] MDE 1.05 40y `exploratory` | +1.49 [+0.65, +2.39] MDE 1.09 50y `exploratory` | -0.20 [-1.28, +0.86] MDE 1.53 5798y `rejected` |
| `trend30_carrystack10` | +2.58 [+1.82, +3.29] MDE 1.09 17y `exploratory` | -0.41 [-1.97, +1.43] MDE 2.45 3372y `rejected` | +2.37 [+1.64, +3.10] MDE 1.10 21y `exploratory` | +2.16 [+1.44, +2.92] MDE 1.14 26y `exploratory` | +0.60 [+0.31, +0.85] MDE 0.35 33y `exploratory` |
| `trend30_carrystack20` | +3.17 [+2.23, +4.01] MDE 1.23 15y `exploratory` | -0.53 [-2.54, +1.82] MDE 2.98 3071y `rejected` | +2.92 [+2.01, +3.81] MDE 1.24 17y `exploratory` | +2.67 [+1.82, +3.70] MDE 1.29 22y `exploratory` | +1.19 [+0.61, +1.70] MDE 0.70 33y `exploratory` |
| `trend15_carry15` | +1.88 [+1.28, +2.39] MDE 0.72 14y `exploratory` | -0.32 [-1.52, +1.08] MDE 1.77 2933y `rejected` | +1.78 [+1.21, +2.30] MDE 0.72 16y `exploratory` | +1.67 [+1.17, +2.30] MDE 0.75 19y `exploratory` | -0.10 [-0.64, +0.43] MDE 0.77 5799y `rejected` |
| `trend30_carry30` | +3.77 [+2.56, +4.79] MDE 1.44 14y `exploratory` | -0.64 [-3.03, +2.15] MDE 3.55 2937y `rejected` | +3.44 [+2.32, +4.52] MDE 1.46 17y `exploratory` | +3.13 [+2.07, +4.45] MDE 1.51 22y `exploratory` | +1.79 [+0.92, +2.56] MDE 1.05 33y `exploratory` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | first_half | second_half | flat_equity_decade | three_class_carry | four_class_carry | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +1.98 | +1.99 | +1.98 | +1.99 | +2.84 | +1.97 | +2.00 | +0.37 | +0.04 |
| `base_no_trend` | -1.98 | -1.99 | -1.98 | -1.99 | -2.84 | -1.97 | -2.00 | -0.37 | -0.04 |
| `carry30_no_trend` | +0.13 | -0.52 | +0.13 | -0.53 | -0.51 | -0.21 | -0.19 | -0.15 | -0.76 |
| `trend30_carrystack10` | +0.70 | +0.49 | +0.70 | +0.49 | +0.77 | +0.59 | +0.60 | +0.07 | -0.24 |
| `trend30_carrystack20` | +1.40 | +0.98 | +1.41 | +0.97 | +1.55 | +1.17 | +1.21 | +0.14 | -0.48 |
| `trend15_carry15` | +0.06 | -0.26 | +0.07 | -0.26 | -0.26 | -0.10 | -0.09 | -0.08 | -0.38 |
| `trend30_carry30` | +2.10 | +1.47 | +2.11 | +1.46 | +2.32 | +1.76 | +1.81 | +0.21 | -0.72 |

### Leg correlations: 1157 months, worst decile = 115 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.074 | 0.072 |
| equity_carry | 0.01 | 0.007 |
| trend_carry | -0.061 | -0.088 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 7.75 | 18.53 | -9.359 | 0.0 |
| trend | 7.22 | 12.38 | 1.569 | 0.626 |
| carry | 7.07 | 12.24 | 0.106 | 0.53 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1929-01..1977-02 | 578 | -0.034 | 0.032 | -0.127 | 0.051 | -0.031 | 8.13 | 7.25 | 7.12 |
| panel_second_half | 1977-03..2025-05 | 579 | -0.101 | -0.033 | -0.011 | -0.279 | 0.094 | 6.01 | 7.19 | 8.38 |
| first_half | 1929-01..1977-03 | 579 | -0.034 | 0.032 | -0.127 | 0.051 | -0.031 | 8.15 | 7.26 | 7.08 |
| second_half | 1977-04..2025-05 | 578 | -0.102 | -0.033 | -0.011 | -0.279 | 0.094 | 5.98 | 7.18 | 8.42 |
| flat_equity_decade | 1999-03..2009-02 | 120 | -0.201 | 0.116 | -0.331 | -0.366 | 0.371 | 8.85 | 10.93 | -4.32 |
| three_class_carry | 1929-01..1974-01 | 541 | -0.038 | 0.029 | -0.103 | 0.032 | -0.038 | 6.98 | 7.18 | 7.48 |
| four_class_carry | 1974-02..2025-05 | 616 | -0.091 | -0.023 | -0.047 | -0.203 | 0.083 | 7.15 | 7.25 | 7.99 |
| post_2009 | 2009-01..2025-05 | 197 | -0.058 | -0.012 | -0.049 | -0.155 | 0.185 | 1.82 | 1.41 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | -0.0 | -0.105 | -0.067 | 0.036 | 0.515 | -1.27 | 0.43 | 12.12 |

Sum rule against the cheap control: both 3.7687 = trend 1.9831 + carry 1.7855 + residual 0.0002 pp/yr.

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (5 ep.) | 0.0 (3 ep.) |
| `base_no_trend` | -0.239 (0.426) | -0.038 (-1.29) | -2.09 (5 ep.) | -14.98 (3 ep.) |
| `carry30_no_trend` | -0.235 (0.443) | -0.0269 (-0.68) | -1.71 (5 ep.) | -11.9 (3 ep.) |
| `trend30_carrystack10` | 0.001 (0.504) | 0.0037 (0.54) | 0.14 (5 ep.) | 1.25 (3 ep.) |
| `trend30_carrystack20` | 0.003 (0.504) | 0.0074 (0.54) | 0.3 (5 ep.) | 2.49 (3 ep.) |
| `trend15_carry15` | -0.118 (0.443) | -0.0134 (-0.68) | -0.86 (5 ep.) | -6.05 (3 ep.) |
| `trend30_carry30` | 0.004 (0.504) | 0.0111 (0.54) | 0.48 (5 ep.) | 3.72 (3 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | -82.78 (+0.00) | -50.34 (+0.00) | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -34.29 (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `base_no_trend` | -83.67 (-0.89) | -49.47 (+0.87) | -45.03 (-4.35) | -50.33 (-4.47) | -20.22 (-1.59) | -46.54 (-12.24) | 54.6 (-31.41) | -24.86 (-1.29) |
| `carry30_no_trend` | -80.39 (+2.39) | -52.14 (-1.80) | -40.13 (+0.55) | -52.49 (-6.63) | -21.68 (-3.05) | -40.92 (-6.63) | 56.91 (-29.10) | -23.54 (+0.02) |
| `trend30_carrystack10` | -81.68 (+1.10) | -51.22 (-0.88) | -38.96 (+1.71) | -46.61 (-0.75) | -19.12 (-0.49) | -32.09 (+2.21) | 87.1 (+1.09) | -23.12 (+0.45) |
| `trend30_carrystack20` | -80.53 (+2.25) | -52.1 (-1.75) | -37.21 (+3.47) | -47.36 (-1.51) | -19.61 (-0.99) | -29.83 (+4.47) | 88.1 (+2.10) | -22.67 (+0.90) |
| `trend15_carry15` | -81.59 (+1.19) | -51.23 (-0.89) | -40.37 (+0.31) | -49.22 (-3.36) | -20.16 (-1.53) | -37.66 (-3.37) | 71.21 (-14.80) | -23.54 (+0.03) |
| `trend30_carry30` | -79.32 (+3.46) | -52.96 (-2.61) | -35.41 (+5.27) | -48.11 (-2.26) | -20.11 (-1.48) | -27.51 (+6.79) | 89.03 (+3.02) | -22.22 (+1.35) |

## Carry components on the primary panel: each per-asset-class carry column, unscaled, against the own trend book and equity (descriptive)

| component | window | months | corr with trend | corr with equity | corr with trend (worst decile) | corr with equity (worst decile) | mean pp/yr | vol % |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Equity indices Carry | 1929-01..2025-05 | 1157 | -0.024 | 0.231 | 0.01 | 0.33 | 1.86 | 12.6 |
| Fixed income Carry | 1929-01..2025-05 | 1157 | 0.1 | -0.045 | -0.006 | -0.039 | 2.56 | 4.78 |
| Currencies Carry | 1974-02..2025-05 | 616 | -0.005 | 0.337 | 0.011 | 0.367 | 2.61 | 6.4 |
| Commodities Carry | 1929-01..2025-05 | 1084 | 0.04 | -0.067 | 0.013 | -0.0 | 5.82 | 16.94 |
