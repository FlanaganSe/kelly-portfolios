# Experiment 027: selective carry in whole portfolios

Run `516783a759174471b809a0f472ec26b2`; specification `54e9237a73dcb7cd71305ad31380e6be253aa8e3207e8647fadf64cbbb90061f`.

Vendor gross factors, hypothetical wrappers, pre-1974 carry risk calibration. Reference is 019's 70/30 proxy, not the current published portfolios. No retail delivery, independent replication, tax or promotion claim. Own trend retains 019's full-window scalar; internal trading costs are omitted. The 2013+ window is inside the 2021 vendor reconstruction, not untouched evidence. Frozen inherited source prose saying components enter no arm is superseded by explicit variant definitions. Haircuts are assumptions, not cost evidence. MDE measures resolution, not an allocation rule. Partial crisis coverage is flagged; it does not represent the complete event.

Carry calibration: `{'all_macro': {'coefficients': {'All Macro Carry': 3.223366593088996}, 'first': '1926-07', 'last': '2026-02'}, 'bond_commodity': {'coefficients': {'Fixed income Carry': 3.293423720652368, 'Commodities Carry': 0.41581960130539436}, 'first': '1926-07', 'last': '2026-02'}, 'commodity_only': {'coefficients': {'Commodities Carry': 0.5342393653897949}, 'first': '1926-07', 'last': '2026-02'}}`.

Gross omits INTERNAL carry costs; wrapper fees and financing are always charged. Costed assumes 2 pp/yr; costed_loading multiplies gross return AND internal costs by 0.681, with wrapper fees unchanged.

## Panel `all_macro_primary_gross` (primary): 1974-02..2025-05, 616 months, trend `own_4_asset_book`, carry `all_macro_gross`

all_macro; primary; gross. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 14.2251 | 12.7823 | 16.5129 | 0.6015 | -45.86 | 51 | 1.0 | 2.3856 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 14.8978 | 13.42 | 16.6832 | 0.6358 | -46.86 | 50 | 1.3296 | 3.1718 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 14.1286 | 12.9044 | 15.1523 | 0.6494 | -42.71 | 40 | 1.0216 | 2.4371 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.3136 | 12.8687 | 16.5223 | 0.6067 | -49.99 | 51 | 1.019 | 2.4308 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +2.00 [+1.00, +3.00] MDE 1.54 31y `exploratory` | -0.36 [-1.87, +1.26] MDE 2.48 2428y `rejected` | +1.70 [+0.70, +2.73] MDE 1.55 43y `exploratory` | +1.50 [+0.43, +2.62] MDE 1.61 55y `unresolved` | -- |
| `stack10` | +2.67 [+1.60, +3.75] MDE 1.65 19y `exploratory` | -0.42 [-2.29, +1.62] MDE 3.01 2621y `rejected` | +2.30 [+1.24, +3.38] MDE 1.66 27y `exploratory` | +1.90 [+0.73, +3.12] MDE 1.72 39y `exploratory` | +0.67 [+0.30, +1.04] MDE 0.46 24y `exploratory` |
| `sell_equity10` | +1.90 [+0.78, +3.01] MDE 1.72 42y `exploratory` | -0.46 [-2.32, +1.59] MDE 3.01 2226y `rejected` | +2.26 [+1.20, +3.34] MDE 1.66 28y `exploratory` | +1.86 [+0.68, +3.10] MDE 1.72 41y `exploratory` | -0.10 [-0.68, +0.50] MDE 0.74 3036y `rejected` |
| `replace_trend15` | +2.09 [+1.30, +2.81] MDE 1.09 14y `exploratory` | -0.27 [-1.63, +1.25] MDE 2.13 3154y `rejected` | +1.79 [+1.00, +2.51] MDE 1.08 19y `exploratory` | +1.42 [+0.59, +2.26] MDE 1.12 30y `exploratory` | +0.09 [-0.64, +0.81] MDE 1.00 6587y `unresolved` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | flat_equity_decade | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +2.59 | +1.41 | +2.84 | +0.37 | +0.04 |
| `stack10` | +1.01 | +0.34 | +0.91 | -0.02 | -0.46 |
| `sell_equity10` | +0.20 | -0.39 | +1.38 | -1.35 | -1.64 |
| `replace_trend15` | +0.30 | -0.12 | -0.10 | -0.08 | -0.58 |

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
| carry | 7.84 | 11.85 | -0.256 | 0.492 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1974-02..1999-09 | 308 | 0.078 | -0.005 | 0.076 | 0.133 | -0.042 | 11.17 | 9.18 | 8.38 |
| panel_second_half | 1999-10..2025-05 | 308 | 0.05 | 0.196 | -0.195 | -0.163 | 0.331 | 4.52 | 5.32 | 7.59 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.13 | 0.152 | -0.331 | -0.281 | 0.507 | 10.26 | 10.93 | -4.32 |
| post_2009 | 2009-01..2025-05 | 197 | -0.01 | 0.253 | -0.049 | -0.255 | 0.292 | 0.9 | 1.41 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | -0.026 | 0.17 | -0.067 | -0.399 | 0.609 | -3.46 | 0.43 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (3 ep.) |
| `stack10` | -0.035 (0.475) | 0.0074 (0.62) | 0.0 (3 ep.) | 1.26 (3 ep.) |
| `sell_equity10` | 0.795 (0.984) | 0.0074 (0.62) | 3.54 (3 ep.) | 3.67 (3 ep.) |
| `replace_trend15` | -0.339 (0.377) | 0.0139 (0.35) | -2.11 (3 ep.) | -5.44 (3 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -26.34* (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `stack10` | n/c | n/c | -38.41 (+2.27) | -46.86 (-1.01) | -19.89 (-1.26) | -25.38* (+0.96) | 89.16 (+3.15) | -23.89 (-0.32) |
| `sell_equity10` | n/c | n/c | -33.92 (+6.76) | -42.71 (+3.15) | -17.93 (+0.70) | -21.71* (+4.63) | 90.28 (+4.27) | -21.47 (+2.10) |
| `replace_trend15` | n/c | n/c | -40.01 (+0.67) | -49.99 (-4.13) | -21.51 (-2.88) | -29.27* (-2.93) | 74.0 (-12.00) | -24.94 (-1.38) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +2.00, +1.83 |
| `stack10` | +0.67 | +0.63 | +2.67, +2.46 |
| `sell_equity10` | -0.10 | -0.10 | +1.90, +1.73 |
| `replace_trend15` | +0.09 | +0.09 | +2.09, +1.92 |

## Panel `all_macro_primary_costed` (sensitivity): 1974-02..2025-05, 616 months, trend `own_4_asset_book`, carry `all_macro_costed`

all_macro; primary; costed. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 14.2251 | 12.7823 | 16.5129 | 0.6015 | -45.86 | 51 | 1.0 | 2.3856 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 14.6978 | 13.222 | 16.6832 | 0.6238 | -47.01 | 50 | 1.2079 | 2.8817 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 13.9286 | 12.7063 | 15.1523 | 0.6362 | -42.86 | 41 | 0.9283 | 2.2146 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.0136 | 12.5715 | 16.5223 | 0.5885 | -50.2 | 51 | 0.8829 | 2.1061 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +2.00 [+1.00, +3.03] MDE 1.54 31y `exploratory` | -0.36 [-1.90, +1.29] MDE 2.48 2428y `rejected` | +1.70 [+0.71, +2.75] MDE 1.55 43y `exploratory` | +1.50 [+0.48, +2.61] MDE 1.61 55y `unresolved` | -- |
| `stack10` | +2.47 [+1.40, +3.57] MDE 1.65 23y `exploratory` | -0.62 [-2.55, +1.44] MDE 3.01 1205y `rejected` | +2.10 [+1.03, +3.21] MDE 1.66 32y `exploratory` | +1.70 [+0.54, +2.88] MDE 1.72 49y `unresolved` | +0.47 [+0.10, +0.87] MDE 0.46 49y `exploratory` |
| `sell_equity10` | +1.70 [+0.59, +2.84] MDE 1.72 53y `unresolved` | -0.66 [-2.59, +1.41] MDE 3.01 1077y `rejected` | +2.06 [+1.00, +3.18] MDE 1.66 33y `exploratory` | +1.66 [+0.50, +2.85] MDE 1.72 52y `unresolved` | -0.30 [-0.86, +0.30] MDE 0.74 321y `rejected` |
| `replace_trend15` | +1.79 [+1.06, +2.57] MDE 1.09 19y `exploratory` | -0.57 [-2.00, +1.00] MDE 2.13 713y `rejected` | +1.49 [+0.76, +2.28] MDE 1.08 27y `exploratory` | +1.12 [+0.31, +1.92] MDE 1.12 48y `unresolved` | -0.21 [-0.94, +0.55] MDE 1.00 1155y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | flat_equity_decade | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +2.59 | +1.41 | +2.84 | +0.37 | +0.04 |
| `stack10` | +0.81 | +0.14 | +0.71 | -0.22 | -0.66 |
| `sell_equity10` | -0.00 | -0.59 | +1.18 | -1.55 | -1.84 |
| `replace_trend15` | -0.00 | -0.42 | -0.40 | -0.38 | -0.88 |

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
| carry | 5.84 | 11.85 | -0.423 | 0.475 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1974-02..1999-09 | 308 | 0.078 | -0.005 | 0.076 | 0.133 | -0.042 | 9.17 | 9.18 | 8.38 |
| panel_second_half | 1999-10..2025-05 | 308 | 0.05 | 0.196 | -0.195 | -0.163 | 0.331 | 2.52 | 5.32 | 7.59 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.13 | 0.152 | -0.331 | -0.281 | 0.507 | 8.26 | 10.93 | -4.32 |
| post_2009 | 2009-01..2025-05 | 197 | -0.01 | 0.253 | -0.049 | -0.255 | 0.292 | -1.1 | 1.41 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | -0.026 | 0.17 | -0.067 | -0.399 | 0.609 | -5.46 | 0.43 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (3 ep.) |
| `stack10` | -0.052 (0.459) | 0.0074 (0.62) | -0.14 (3 ep.) | 0.6 (3 ep.) |
| `sell_equity10` | 0.778 (0.967) | 0.0074 (0.62) | 3.38 (3 ep.) | 3.0 (3 ep.) |
| `replace_trend15` | -0.364 (0.377) | 0.0139 (0.35) | -2.33 (3 ep.) | -6.36 (3 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -26.34* (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `stack10` | n/c | n/c | -38.67 (+2.01) | -47.01 (-1.15) | -19.92 (-1.29) | -25.49* (+0.86) | 87.39 (+1.38) | -24.0 (-0.44) |
| `sell_equity10` | n/c | n/c | -34.19 (+6.48) | -42.86 (+2.99) | -17.96 (+0.67) | -21.82* (+4.53) | 88.5 (+2.49) | -21.59 (+1.98) |
| `replace_trend15` | n/c | n/c | -40.39 (+0.29) | -50.2 (-4.34) | -21.55 (-2.92) | -29.42* (-3.08) | 71.56 (-14.44) | -25.12 (-1.55) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +2.00, +1.83 |
| `stack10` | +0.47 | +0.43 | +2.47, +2.26 |
| `sell_equity10` | -0.30 | -0.30 | +1.70, +1.53 |
| `replace_trend15` | -0.21 | -0.21 | +1.79, +1.62 |

## Panel `all_macro_primary_costed_loading` (sensitivity): 1974-02..2025-05, 616 months, trend `own_4_asset_book`, carry `all_macro_costed_loading`

all_macro; primary; costed_loading. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 14.2251 | 12.7823 | 16.5129 | 0.6015 | -45.86 | 51 | 1.0 | 2.3856 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 14.5114 | 13.048 | 16.6199 | 0.615 | -46.67 | 50 | 1.1186 | 2.6685 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 13.7423 | 12.5317 | 15.0862 | 0.6266 | -42.5 | 41 | 0.8596 | 2.0506 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 13.7341 | 12.3126 | 16.4138 | 0.5753 | -49.71 | 57 | 0.7883 | 1.8806 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +2.00 [+1.03, +3.00] MDE 1.54 31y `exploratory` | -0.36 [-1.92, +1.23] MDE 2.48 2428y `rejected` | +1.70 [+0.72, +2.72] MDE 1.55 43y `exploratory` | +1.50 [+0.45, +2.57] MDE 1.61 55y `unresolved` | -- |
| `stack10` | +2.28 [+1.28, +3.35] MDE 1.60 25y `exploratory` | -0.81 [-2.74, +1.24] MDE 3.00 706y `rejected` | +1.94 [+0.89, +3.00] MDE 1.61 35y `exploratory` | +1.61 [+0.49, +2.75] MDE 1.67 52y `unresolved` | +0.29 [+0.04, +0.53] MDE 0.32 62y `unresolved` |
| `sell_equity10` | +1.52 [+0.43, +2.61] MDE 1.68 63y `unresolved` | -0.84 [-2.78, +1.20] MDE 3.00 648y `rejected` | +1.91 [+0.85, +2.97] MDE 1.61 37y `exploratory` | +1.57 [+0.44, +2.72] MDE 1.67 55y `unresolved` | -0.48 [-0.96, +0.04] MDE 0.67 99y `rejected` |
| `replace_trend15` | +1.51 [+0.88, +2.14] MDE 0.94 20y `exploratory` | -0.85 [-2.21, +0.64] MDE 2.08 307y `rejected` | +1.26 [+0.62, +1.89] MDE 0.94 28y `exploratory` | +0.98 [+0.25, +1.71] MDE 0.97 47y `exploratory` | -0.49 [-1.08, +0.10] MDE 0.88 164y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | flat_equity_decade | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +2.59 | +1.41 | +2.84 | +0.37 | +0.04 |
| `stack10` | +0.51 | +0.06 | +0.45 | -0.19 | -0.48 |
| `sell_equity10` | -0.30 | -0.67 | +0.91 | -1.51 | -1.67 |
| `replace_trend15` | -0.44 | -0.54 | -0.80 | -0.32 | -0.62 |

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
| carry | 3.98 | 8.07 | -0.288 | 0.475 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1974-02..1999-09 | 308 | 0.078 | -0.005 | 0.076 | 0.133 | -0.042 | 6.24 | 9.18 | 8.38 |
| panel_second_half | 1999-10..2025-05 | 308 | 0.05 | 0.196 | -0.195 | -0.163 | 0.331 | 1.71 | 5.32 | 7.59 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.13 | 0.152 | -0.331 | -0.281 | 0.507 | 5.63 | 10.93 | -4.32 |
| post_2009 | 2009-01..2025-05 | 197 | -0.01 | 0.253 | -0.049 | -0.255 | 0.292 | -0.75 | 1.41 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | -0.026 | 0.17 | -0.067 | -0.399 | 0.609 | -3.72 | 0.43 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (3 ep.) |
| `stack10` | -0.038 (0.459) | 0.005 (0.62) | -0.13 (3 ep.) | 0.3 (3 ep.) |
| `sell_equity10` | 0.791 (1.0) | 0.005 (0.62) | 3.39 (3 ep.) | 2.69 (3 ep.) |
| `replace_trend15` | -0.344 (0.328) | 0.0104 (0.29) | -2.3 (3 ep.) | -6.78 (3 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -26.34* (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `stack10` | n/c | n/c | -39.36 (+1.32) | -46.67 (-0.81) | -19.51 (-0.88) | -25.78* (+0.57) | 86.65 (+0.64) | -23.88 (-0.32) |
| `sell_equity10` | n/c | n/c | -34.94 (+5.74) | -42.5 (+3.36) | -17.55 (+1.08) | -22.12* (+4.22) | 87.77 (+1.76) | -21.47 (+2.10) |
| `replace_trend15` | n/c | n/c | -41.4 (-0.72) | -49.71 (-3.85) | -20.95 (-2.32) | -29.84* (-3.49) | 70.54 (-15.46) | -24.94 (-1.37) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +2.00, +1.83 |
| `stack10` | +0.29 | +0.24 | +2.28, +2.07 |
| `sell_equity10` | -0.48 | -0.48 | +1.52, +1.35 |
| `replace_trend15` | -0.49 | -0.49 | +1.51, +1.34 |

## Panel `all_macro_secondary_gross` (secondary): 1985-01..2026-02, 494 months, trend `aqr_tsmom`, carry `all_macro_gross`

all_macro; secondary; gross. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.8948 | 14.5159 | 15.9621 | 0.7986 | -46.71 | 41 | 1.0 | 3.4501 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 16.429 | 15.0033 | 16.2115 | 0.8194 | -47.72 | 39 | 1.2031 | 4.1509 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 15.5316 | 14.3504 | 14.7211 | 0.8416 | -43.58 | 39 | 0.9347 | 3.2246 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 15.041 | 13.6371 | 16.1664 | 0.7355 | -50.41 | 50 | 0.7202 | 2.4848 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +3.50 [+2.29, +4.68] MDE 1.63 9y `exploratory` | +0.72 [-1.19, +2.68] MDE 2.71 577y `unresolved` | +3.23 [+2.04, +4.41] MDE 1.64 11y `exploratory` | +3.15 [+2.01, +4.40] MDE 1.74 12y `exploratory` | -- |
| `stack10` | +4.03 [+2.66, +5.33] MDE 1.77 8y `exploratory` | +0.40 [-2.01, +2.84] MDE 3.28 2810y `unresolved` | +3.62 [+2.22, +4.96] MDE 1.78 10y `exploratory` | +3.53 [+2.13, +5.04] MDE 1.89 11y `exploratory` | +0.53 [+0.15, +0.90] MDE 0.51 38y `exploratory` |
| `sell_equity10` | +3.13 [+1.67, +4.56] MDE 1.86 15y `exploratory` | +0.36 [-2.04, +2.80] MDE 3.28 3394y `unresolved` | +3.59 [+2.17, +4.93] MDE 1.78 10y `exploratory` | +3.50 [+2.09, +5.02] MDE 1.89 11y `exploratory` | -0.36 [-0.98, +0.27] MDE 0.78 192y `rejected` |
| `replace_trend15` | +2.64 [+1.70, +3.55] MDE 1.20 8y `exploratory` | -0.13 [-1.81, +1.64] MDE 2.30 12969y `rejected` | +2.26 [+1.27, +3.19] MDE 1.18 11y `exploratory` | +2.19 [+1.18, +3.23] MDE 1.25 12y `exploratory` | -0.85 [-1.53, -0.21] MDE 1.07 64y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | flat_equity_decade | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +5.29 | +1.70 | +4.52 | +0.98 | +0.98 |
| `stack10` | +0.95 | +0.12 | +0.91 | -0.02 | -0.46 |
| `sell_equity10` | +0.12 | -0.84 | +1.38 | -1.35 | -1.64 |
| `replace_trend15` | -1.13 | -0.58 | -0.94 | -0.39 | -1.05 |

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
| carry | 6.46 | 11.78 | -0.817 | 0.449 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1985-01..2005-07 | 247 | 0.176 | 0.036 | 0.057 | 0.064 | 0.046 | 10.63 | 18.17 | 8.65 |
| panel_second_half | 2005-08..2026-02 | 247 | 0.008 | 0.276 | -0.209 | -0.091 | 0.444 | 2.29 | 6.13 | 9.89 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.281 | 0.152 | -0.268 | 0.25 | 0.507 | 10.26 | 16.56 | -4.32 |
| post_2009 | 2009-01..2025-05 | 197 | -0.026 | 0.253 | -0.202 | -0.114 | 0.292 | 0.9 | 3.47 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | 0.029 | 0.17 | -0.26 | -0.466 | 0.609 | -3.46 | 3.55 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (1 ep.) |
| `stack10` | -0.091 (0.429) | 0.0171 (1.43) | 0.04 (3 ep.) | -0.35 (1 ep.) |
| `sell_equity10` | 0.735 (0.98) | 0.0171 (1.43) | 3.63 (3 ep.) | 2.2 (1 ep.) |
| `replace_trend15` | -0.509 (0.327) | 0.0366 (0.99) | -2.56 (3 ep.) | -4.24 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -37.96 (+0.00) | -46.71 (+0.00) | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `stack10` | n/c | n/c | -35.58 (+2.38) | -47.72 (-1.01) | -19.1 (-1.26) | n/c | n/c | -18.38 (-0.35) |
| `sell_equity10` | n/c | n/c | -30.91 (+7.05) | -43.58 (+3.12) | -17.14 (+0.71) | n/c | n/c | -15.82 (+2.20) |
| `replace_trend15` | n/c | n/c | -38.65 (-0.69) | -50.41 (-3.71) | -21.11 (-3.27) | n/c | n/c | -22.27 (-4.24) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +3.50, +3.33 |
| `stack10` | +0.53 | +0.49 | +4.03, +3.82 |
| `sell_equity10` | -0.36 | -0.36 | +3.13, +2.96 |
| `replace_trend15` | -0.85 | -0.85 | +2.64, +2.47 |

## Panel `all_macro_secondary_costed` (sensitivity): 1985-01..2026-02, 494 months, trend `aqr_tsmom`, carry `all_macro_costed`

all_macro; secondary; costed. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.8948 | 14.5159 | 15.9621 | 0.7986 | -46.71 | 41 | 1.0 | 3.4501 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 16.229 | 14.8055 | 16.2115 | 0.8071 | -47.86 | 39 | 1.1138 | 3.8428 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 15.3316 | 14.1525 | 14.7211 | 0.828 | -43.74 | 39 | 0.8655 | 2.9861 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.741 | 13.3401 | 16.1664 | 0.7169 | -50.62 | 50 | 0.6425 | 2.2165 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +3.50 [+2.31, +4.68] MDE 1.63 9y `exploratory` | +0.72 [-1.23, +2.63] MDE 2.71 577y `unresolved` | +3.23 [+2.01, +4.42] MDE 1.64 11y `exploratory` | +3.15 [+2.02, +4.26] MDE 1.74 12y `exploratory` | -- |
| `stack10` | +3.83 [+2.43, +5.21] MDE 1.77 9y `exploratory` | +0.20 [-2.23, +2.57] MDE 3.28 11433y `unresolved` | +3.42 [+1.94, +4.78] MDE 1.78 11y `exploratory` | +3.33 [+2.03, +4.69] MDE 1.89 12y `exploratory` | +0.33 [-0.05, +0.70] MDE 0.51 97y `unresolved` |
| `sell_equity10` | +2.93 [+1.36, +4.32] MDE 1.86 17y `exploratory` | +0.16 [-2.27, +2.54] MDE 3.28 17080y `unresolved` | +3.39 [+1.89, +4.74] MDE 1.78 11y `exploratory` | +3.30 [+2.00, +4.66] MDE 1.89 13y `exploratory` | -0.56 [-1.18, +0.06] MDE 0.78 80y `rejected` |
| `replace_trend15` | +2.34 [+1.34, +3.28] MDE 1.20 11y `exploratory` | -0.43 [-2.15, +1.28] MDE 2.30 1182y `rejected` | +1.96 [+0.90, +2.88] MDE 1.18 15y `exploratory` | +1.89 [+0.92, +2.89] MDE 1.25 17y `exploratory` | -1.15 [-1.80, -0.49] MDE 1.07 35y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | flat_equity_decade | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +5.29 | +1.70 | +4.52 | +0.98 | +0.98 |
| `stack10` | +0.75 | -0.08 | +0.71 | -0.22 | -0.66 |
| `sell_equity10` | -0.08 | -1.04 | +1.18 | -1.55 | -1.84 |
| `replace_trend15` | -1.43 | -0.88 | -1.24 | -0.69 | -1.35 |

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
| carry | 4.46 | 11.78 | -0.984 | 0.429 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1985-01..2005-07 | 247 | 0.176 | 0.036 | 0.057 | 0.064 | 0.046 | 8.63 | 18.17 | 8.65 |
| panel_second_half | 2005-08..2026-02 | 247 | 0.008 | 0.276 | -0.209 | -0.091 | 0.444 | 0.29 | 6.13 | 9.89 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.281 | 0.152 | -0.268 | 0.25 | 0.507 | 8.26 | 16.56 | -4.32 |
| post_2009 | 2009-01..2025-05 | 197 | -0.026 | 0.253 | -0.202 | -0.114 | 0.292 | -1.1 | 3.47 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | 0.029 | 0.17 | -0.26 | -0.466 | 0.609 | -5.46 | 3.55 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (1 ep.) |
| `stack10` | -0.108 (0.408) | 0.0171 (1.43) | -0.11 (3 ep.) | -0.48 (1 ep.) |
| `sell_equity10` | 0.718 (0.959) | 0.0171 (1.43) | 3.47 (3 ep.) | 2.08 (1 ep.) |
| `replace_trend15` | -0.534 (0.286) | 0.0366 (0.99) | -2.77 (3 ep.) | -4.42 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -37.96 (+0.00) | -46.71 (+0.00) | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `stack10` | n/c | n/c | -35.86 (+2.10) | -47.86 (-1.16) | -19.13 (-1.29) | n/c | n/c | -18.51 (-0.48) |
| `sell_equity10` | n/c | n/c | -31.2 (+6.76) | -43.74 (+2.96) | -17.17 (+0.67) | n/c | n/c | -15.95 (+2.08) |
| `replace_trend15` | n/c | n/c | -39.05 (-1.08) | -50.62 (-3.91) | -21.16 (-3.32) | n/c | n/c | -22.45 (-4.42) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +3.50, +3.33 |
| `stack10` | +0.33 | +0.29 | +3.83, +3.62 |
| `sell_equity10` | -0.56 | -0.56 | +2.93, +2.76 |
| `replace_trend15` | -1.15 | -1.15 | +2.34, +2.17 |

## Panel `all_macro_secondary_costed_loading` (sensitivity): 1985-01..2026-02, 494 months, trend `aqr_tsmom`, carry `all_macro_costed_loading`

all_macro; secondary; costed_loading. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.8948 | 14.5159 | 15.9621 | 0.7986 | -46.71 | 41 | 1.0 | 3.4501 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 16.0869 | 14.6795 | 16.123 | 0.8026 | -47.52 | 40 | 1.0621 | 3.6641 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 15.1894 | 14.0254 | 14.6296 | 0.8234 | -43.38 | 39 | 0.8252 | 2.847 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.5277 | 13.1526 | 16.0224 | 0.71 | -50.13 | 51 | 0.5997 | 2.069 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +3.50 [+2.34, +4.63] MDE 1.63 9y `exploratory` | +0.72 [-1.28, +2.77] MDE 2.71 577y `unresolved` | +3.23 [+2.02, +4.39] MDE 1.64 11y `exploratory` | +3.15 [+2.01, +4.27] MDE 1.74 12y `exploratory` | -- |
| `stack10` | +3.69 [+2.39, +4.93] MDE 1.71 9y `exploratory` | +0.05 [-2.48, +2.52] MDE 3.27 148203y `unresolved` | +3.33 [+1.97, +4.65] MDE 1.72 11y `exploratory` | +3.24 [+1.96, +4.53] MDE 1.83 12y `exploratory` | +0.19 [-0.07, +0.44] MDE 0.35 137y `unresolved` |
| `sell_equity10` | +2.79 [+1.34, +4.21] MDE 1.81 17y `exploratory` | +0.02 [-2.52, +2.49] MDE 3.27 1258239y `unresolved` | +3.30 [+1.94, +4.63] MDE 1.72 11y `exploratory` | +3.21 [+1.92, +4.50] MDE 1.83 12y `exploratory` | -0.71 [-1.27, -0.14] MDE 0.71 42y `rejected` |
| `replace_trend15` | +2.13 [+1.30, +2.93] MDE 1.03 10y `exploratory` | -0.64 [-2.41, +1.13] MDE 2.26 507y `rejected` | +1.83 [+0.98, +2.64] MDE 1.02 13y `exploratory` | +1.77 [+0.94, +2.59] MDE 1.08 14y `exploratory` | -1.37 [-1.98, -0.84] MDE 0.93 19y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | flat_equity_decade | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +5.29 | +1.70 | +4.52 | +0.98 | +0.98 |
| `stack10` | +0.48 | -0.09 | +0.45 | -0.19 | -0.48 |
| `sell_equity10` | -0.36 | -1.05 | +0.91 | -1.51 | -1.67 |
| `replace_trend15` | -1.84 | -0.89 | -1.64 | -0.63 | -1.09 |

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
| carry | 3.04 | 8.02 | -0.67 | 0.429 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1985-01..2005-07 | 247 | 0.176 | 0.036 | 0.057 | 0.064 | 0.046 | 5.88 | 18.17 | 8.65 |
| panel_second_half | 2005-08..2026-02 | 247 | 0.008 | 0.276 | -0.209 | -0.091 | 0.444 | 0.2 | 6.13 | 9.89 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.281 | 0.152 | -0.268 | 0.25 | 0.507 | 5.63 | 16.56 | -4.32 |
| post_2009 | 2009-01..2025-05 | 197 | -0.026 | 0.253 | -0.202 | -0.114 | 0.292 | -0.75 | 3.47 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | 0.029 | 0.17 | -0.26 | -0.466 | 0.609 | -3.72 | 3.55 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (1 ep.) |
| `stack10` | -0.076 (0.408) | 0.0116 (1.43) | -0.11 (3 ep.) | -0.35 (1 ep.) |
| `sell_equity10` | 0.749 (1.0) | 0.0117 (1.43) | 3.47 (3 ep.) | 2.21 (1 ep.) |
| `replace_trend15` | -0.487 (0.245) | 0.0284 (0.86) | -2.75 (3 ep.) | -4.23 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -37.96 (+0.00) | -46.71 (+0.00) | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `stack10` | n/c | n/c | -36.58 (+1.38) | -47.52 (-0.81) | -18.72 (-0.88) | n/c | n/c | -18.38 (-0.35) |
| `sell_equity10` | n/c | n/c | -31.98 (+5.98) | -43.38 (+3.33) | -16.76 (+1.08) | n/c | n/c | -15.82 (+2.21) |
| `replace_trend15` | n/c | n/c | -40.08 (-2.12) | -50.13 (-3.42) | -20.56 (-2.72) | n/c | n/c | -22.26 (-4.23) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +3.50, +3.33 |
| `stack10` | +0.19 | +0.15 | +3.69, +3.48 |
| `sell_equity10` | -0.71 | -0.71 | +2.79, +2.62 |
| `replace_trend15` | -1.37 | -1.37 | +2.13, +1.96 |

## Panel `all_macro_recent_gross` (check): 2013-09..2026-02, 150 months, trend `aqr_tsmom`, carry `all_macro_gross`

all_macro; recent; gross. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.3702 | 14.2228 | 14.6254 | 0.9331 | -18.48 | 20 | 1.0 | 1.1244 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 15.0551 | 13.8758 | 14.8596 | 0.8975 | -19.1 | 14 | 0.9674 | 1.0877 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 13.8385 | 12.8709 | 13.4402 | 0.9018 | -17.14 | 14 | 0.8717 | 0.9801 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.4145 | 13.2003 | 15.127 | 0.8396 | -22.27 | 18 | 0.9087 | 1.0217 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.22 [-0.69, +3.26] MDE 3.11 81y `unresolved` | -2.58 [-5.81, +0.50] MDE 5.32 53y `rejected` | +1.40 [-0.47, +3.39] MDE 3.08 60y `unresolved` | +0.64 [-0.86, +2.32] MDE 3.42 273y `unresolved` | -- |
| `stack10` | +0.91 [-1.11, +3.00] MDE 3.28 164y `unresolved` | -4.07 [-7.92, -0.46] MDE 6.30 30y `rejected` | +0.89 [-1.13, +2.99] MDE 3.28 169y `unresolved` | +0.18 [-1.64, +2.24] MDE 3.71 4259y `unresolved` | -0.32 [-0.80, +0.17] MDE 0.85 92y `rejected` |
| `sell_equity10` | -0.31 [-2.69, +2.05] MDE 3.63 1699y `rejected` | -4.11 [-7.95, -0.49] MDE 6.30 29y `rejected` | +0.87 [-1.17, +2.97] MDE 3.29 181y `unresolved` | +0.14 [-1.70, +2.23] MDE 3.72 6783y `unresolved` | -1.53 [-2.34, -0.76] MDE 1.34 10y `rejected` |
| `replace_trend15` | +0.26 [-1.03, +1.48] MDE 2.08 773y `unresolved` | -3.53 [-6.11, -1.08] MDE 4.28 18y `rejected` | +0.04 [-1.30, +1.30] MDE 2.09 33822y `unresolved` | -0.28 [-1.76, +1.19] MDE 2.47 741y `rejected` | -0.96 [-2.23, +0.15] MDE 1.98 54y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | +1.69 | +0.75 | +0.98 | +0.98 |
| `stack10` | -0.40 | -0.23 | -0.46 | -0.46 |
| `sell_equity10` | -1.60 | -1.47 | -1.64 | -1.64 |
| `replace_trend15` | -1.33 | -0.58 | -1.05 | -1.05 |

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
| carry | -2.03 | 10.77 | -1.755 | 0.4 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 2013-09..2019-11 | 75 | -0.038 | 0.321 | -0.164 | -0.488 | 0.387 | -2.92 | 5.92 | 12.22 |
| panel_second_half | 2019-12..2026-02 | 75 | 0.114 | 0.094 | -0.337 | -0.544 | 0.59 | -1.15 | 2.75 | 12.71 |
| post_2009 | 2013-09..2025-05 | 141 | 0.029 | 0.17 | -0.26 | -0.466 | 0.609 | -3.46 | 3.55 | 12.12 |
| post_publication | 2013-09..2025-05 | 141 | 0.029 | 0.17 | -0.26 | -0.466 | 0.609 | -3.46 | 3.55 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (1 ep.) | 0.0 (1 ep.) |
| `stack10` | -0.185 (0.333) | 0.0395 (2.27) | -1.26 (1 ep.) | -0.35 (1 ep.) |
| `sell_equity10` | 0.573 (1.0) | 0.0395 (2.27) | 0.71 (1 ep.) | 2.2 (1 ep.) |
| `replace_trend15` | -0.594 (0.133) | 0.0498 (1.05) | -3.27 (1 ep.) | -4.24 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | n/c | n/c | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `stack10` | n/c | n/c | n/c | n/c | -19.1 (-1.26) | n/c | n/c | -18.38 (-0.35) |
| `sell_equity10` | n/c | n/c | n/c | n/c | -17.14 (+0.71) | n/c | n/c | -15.82 (+2.20) |
| `replace_trend15` | n/c | n/c | n/c | n/c | -21.11 (-3.27) | n/c | n/c | -22.27 (-4.24) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +1.22, +1.05 |
| `stack10` | -0.32 | -0.36 | +0.91, +0.70 |
| `sell_equity10` | -1.53 | -1.53 | -0.31, -0.48 |
| `replace_trend15` | -0.96 | -0.96 | +0.26, +0.10 |

## Panel `all_macro_recent_costed` (sensitivity): 2013-09..2026-02, 150 months, trend `aqr_tsmom`, carry `all_macro_costed`

all_macro; recent; costed. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.3702 | 14.2228 | 14.6254 | 0.9331 | -18.48 | 20 | 1.0 | 1.1244 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 14.8551 | 13.6779 | 14.8596 | 0.884 | -19.13 | 15 | 0.9474 | 1.0652 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 13.6385 | 12.6729 | 13.4402 | 0.8869 | -17.17 | 14 | 0.8539 | 0.96 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.1145 | 12.9033 | 15.127 | 0.8197 | -22.45 | 18 | 0.8809 | 0.9904 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.22 [-0.70, +3.19] MDE 3.11 81y `unresolved` | -2.58 [-5.71, +0.67] MDE 5.32 53y `rejected` | +1.40 [-0.48, +3.33] MDE 3.08 60y `unresolved` | +0.64 [-0.92, +2.29] MDE 3.42 273y `unresolved` | -- |
| `stack10` | +0.71 [-1.31, +2.79] MDE 3.28 271y `unresolved` | -4.27 [-7.85, -0.43] MDE 6.30 27y `rejected` | +0.69 [-1.32, +2.79] MDE 3.28 280y `unresolved` | -0.02 [-1.85, +1.91] MDE 3.71 215720y `rejected` | -0.52 [-0.98, -0.03] MDE 0.85 34y `rejected` |
| `sell_equity10` | -0.51 [-2.77, +1.84] MDE 3.63 630y `rejected` | -4.31 [-7.89, -0.47] MDE 6.30 27y `rejected` | +0.67 [-1.35, +2.79] MDE 3.29 306y `unresolved` | -0.06 [-1.91, +1.90] MDE 3.72 35592y `rejected` | -1.73 [-2.50, -0.97] MDE 1.34 7y `rejected` |
| `replace_trend15` | -0.04 [-1.27, +1.21] MDE 2.08 42884y `rejected` | -3.83 [-6.27, -1.34] MDE 4.28 16y `rejected` | -0.26 [-1.53, +1.03] MDE 2.09 806y `rejected` | -0.58 [-2.11, +0.88] MDE 2.47 173y `rejected` | -1.26 [-2.53, -0.12] MDE 1.98 31y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | +1.69 | +0.75 | +0.98 | +0.98 |
| `stack10` | -0.60 | -0.43 | -0.66 | -0.66 |
| `sell_equity10` | -1.80 | -1.67 | -1.84 | -1.84 |
| `replace_trend15` | -1.63 | -0.88 | -1.35 | -1.35 |

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
| carry | -4.03 | 10.77 | -1.922 | 0.333 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 2013-09..2019-11 | 75 | -0.038 | 0.321 | -0.164 | -0.488 | 0.387 | -4.92 | 5.92 | 12.22 |
| panel_second_half | 2019-12..2026-02 | 75 | 0.114 | 0.094 | -0.337 | -0.544 | 0.59 | -3.15 | 2.75 | 12.71 |
| post_2009 | 2013-09..2025-05 | 141 | 0.029 | 0.17 | -0.26 | -0.466 | 0.609 | -5.46 | 3.55 | 12.12 |
| post_publication | 2013-09..2025-05 | 141 | 0.029 | 0.17 | -0.26 | -0.466 | 0.609 | -5.46 | 3.55 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (1 ep.) | 0.0 (1 ep.) |
| `stack10` | -0.201 (0.2) | 0.0395 (2.27) | -1.29 (1 ep.) | -0.48 (1 ep.) |
| `sell_equity10` | 0.557 (1.0) | 0.0395 (2.27) | 0.67 (1 ep.) | 2.08 (1 ep.) |
| `replace_trend15` | -0.619 (0.133) | 0.0498 (1.05) | -3.32 (1 ep.) | -4.42 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | n/c | n/c | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `stack10` | n/c | n/c | n/c | n/c | -19.13 (-1.29) | n/c | n/c | -18.51 (-0.48) |
| `sell_equity10` | n/c | n/c | n/c | n/c | -17.17 (+0.67) | n/c | n/c | -15.95 (+2.08) |
| `replace_trend15` | n/c | n/c | n/c | n/c | -21.16 (-3.32) | n/c | n/c | -22.45 (-4.42) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +1.22, +1.05 |
| `stack10` | -0.52 | -0.56 | +0.71, +0.50 |
| `sell_equity10` | -1.73 | -1.73 | -0.51, -0.68 |
| `replace_trend15` | -1.26 | -1.26 | -0.04, -0.20 |

## Panel `all_macro_recent_costed_loading` (sensitivity): 2013-09..2026-02, 150 months, trend `aqr_tsmom`, carry `all_macro_costed_loading`

all_macro; recent; costed_loading. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.3702 | 14.2228 | 14.6254 | 0.9331 | -18.48 | 20 | 1.0 | 1.1244 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 14.9839 | 13.8178 | 14.7768 | 0.8976 | -18.72 | 20 | 0.9604 | 1.0798 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 13.7672 | 12.812 | 13.3546 | 0.9021 | -16.76 | 14 | 0.8653 | 0.9729 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.3076 | 13.1152 | 14.993 | 0.8399 | -22.26 | 18 | 0.899 | 1.0108 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.22 [-0.73, +3.31] MDE 3.11 81y `unresolved` | -2.58 [-5.87, +0.58] MDE 5.32 53y `rejected` | +1.40 [-0.52, +3.48] MDE 3.08 60y `unresolved` | +0.64 [-0.96, +2.24] MDE 3.42 273y `unresolved` | -- |
| `stack10` | +0.83 [-1.15, +2.92] MDE 3.20 184y `unresolved` | -4.14 [-8.04, -0.49] MDE 6.30 29y `rejected` | +0.89 [-1.08, +2.99] MDE 3.20 161y `unresolved` | +0.16 [-1.61, +1.96] MDE 3.59 5032y `unresolved` | -0.39 [-0.71, -0.07] MDE 0.58 28y `rejected` |
| `sell_equity10` | -0.38 [-2.66, +1.88] MDE 3.58 1090y `rejected` | -4.18 [-8.08, -0.52] MDE 6.30 28y `rejected` | +0.87 [-1.12, +2.96] MDE 3.20 171y `unresolved` | +0.12 [-1.65, +1.94] MDE 3.59 8238y `unresolved` | -1.60 [-2.34, -0.93] MDE 1.23 7y `rejected` |
| `replace_trend15` | +0.16 [-0.96, +1.29] MDE 1.83 1682y `unresolved` | -3.64 [-6.27, -1.30] MDE 4.22 17y `rejected` | +0.04 [-1.09, +1.18] MDE 1.83 26457y `unresolved` | -0.30 [-1.54, +0.89] MDE 2.13 469y `rejected` | -1.06 [-2.21, +0.02] MDE 1.77 35y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | +1.69 | +0.75 | +0.98 | +0.98 |
| `stack10` | -0.45 | -0.33 | -0.48 | -0.48 |
| `sell_equity10` | -1.64 | -1.57 | -1.67 | -1.67 |
| `replace_trend15` | -1.39 | -0.73 | -1.09 | -1.09 |

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
| carry | -2.75 | 7.34 | -1.309 | 0.333 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 2013-09..2019-11 | 75 | -0.038 | 0.321 | -0.164 | -0.488 | 0.387 | -3.35 | 5.92 | 12.22 |
| panel_second_half | 2019-12..2026-02 | 75 | 0.114 | 0.094 | -0.337 | -0.544 | 0.59 | -2.14 | 2.75 | 12.71 |
| post_2009 | 2013-09..2025-05 | 141 | 0.029 | 0.17 | -0.26 | -0.466 | 0.609 | -3.72 | 3.55 | 12.12 |
| post_publication | 2013-09..2025-05 | 141 | 0.029 | 0.17 | -0.26 | -0.466 | 0.609 | -3.72 | 3.55 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (1 ep.) | 0.0 (1 ep.) |
| `stack10` | -0.14 (0.2) | 0.0269 (2.27) | -0.88 (1 ep.) | -0.35 (1 ep.) |
| `sell_equity10` | 0.618 (1.0) | 0.0269 (2.27) | 1.08 (1 ep.) | 2.21 (1 ep.) |
| `replace_trend15` | -0.527 (0.133) | 0.0309 (0.75) | -2.72 (1 ep.) | -4.23 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | n/c | n/c | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `stack10` | n/c | n/c | n/c | n/c | -18.72 (-0.88) | n/c | n/c | -18.38 (-0.35) |
| `sell_equity10` | n/c | n/c | n/c | n/c | -16.76 (+1.08) | n/c | n/c | -15.82 (+2.21) |
| `replace_trend15` | n/c | n/c | n/c | n/c | -20.56 (-2.72) | n/c | n/c | -22.26 (-4.23) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +1.22, +1.05 |
| `stack10` | -0.39 | -0.43 | +0.83, +0.62 |
| `sell_equity10` | -1.60 | -1.60 | -0.38, -0.55 |
| `replace_trend15` | -1.06 | -1.06 | +0.16, -0.01 |

## Panel `bond_commodity_primary_gross` (primary): 1974-02..2025-05, 616 months, trend `own_4_asset_book`, carry `bond_commodity_gross`

bond_commodity; primary; gross. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 14.2251 | 12.7823 | 16.5129 | 0.6015 | -45.86 | 51 | 1.0 | 2.3856 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 15.0676 | 13.6076 | 16.5765 | 0.6501 | -45.87 | 50 | 1.4303 | 3.4122 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 14.2984 | 13.0885 | 15.0554 | 0.6648 | -41.65 | 41 | 1.097 | 2.6171 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.5682 | 13.1466 | 16.3801 | 0.6274 | -48.57 | 51 | 1.1339 | 2.705 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +2.00 [+0.99, +3.03] MDE 1.54 31y `exploratory` | -0.36 [-1.92, +1.36] MDE 2.48 2428y `rejected` | +1.70 [+0.68, +2.71] MDE 1.55 43y `exploratory` | +1.50 [+0.44, +2.58] MDE 1.61 55y `unresolved` | -- |
| `stack10` | +2.84 [+1.69, +3.99] MDE 1.76 20y `exploratory` | -0.25 [-2.27, +1.98] MDE 3.14 8005y `rejected` | +2.52 [+1.35, +3.69] MDE 1.78 26y `exploratory` | +2.01 [+0.79, +3.31] MDE 1.85 41y `exploratory` | +0.84 [+0.37, +1.31] MDE 0.70 36y `exploratory` |
| `sell_equity10` | +2.07 [+0.86, +3.29] MDE 1.86 41y `exploratory` | -0.29 [-2.31, +1.94] MDE 3.14 6135y `rejected` | +2.48 [+1.32, +3.65] MDE 1.78 27y `exploratory` | +1.96 [+0.73, +3.27] MDE 1.85 43y `exploratory` | +0.07 [-0.57, +0.77] MDE 0.96 8796y `unresolved` |
| `replace_trend15` | +2.34 [+1.43, +3.26] MDE 1.37 18y `exploratory` | -0.02 [-1.58, +1.67] MDE 2.39 980243y `rejected` | +2.11 [+1.18, +3.05] MDE 1.38 22y `exploratory` | +1.57 [+0.65, +2.55] MDE 1.43 40y `exploratory` | +0.34 [-0.47, +1.22] MDE 1.23 662y `unresolved` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | flat_equity_decade | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +2.59 | +1.41 | +2.84 | +0.37 | +0.04 |
| `stack10` | +1.21 | +0.48 | +0.94 | +0.13 | -0.16 |
| `sell_equity10` | +0.40 | -0.25 | +1.40 | -1.19 | -1.35 |
| `replace_trend15` | +0.60 | +0.09 | -0.07 | +0.15 | -0.14 |

### Leg correlations: 616 months, worst decile = 61 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.047 | 0.089 |
| equity_carry | -0.049 | -0.077 |
| trend_carry | 0.113 | -0.055 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 7.99 | 15.91 | -8.27 | 0.0 |
| trend | 7.25 | 13.17 | 2.004 | 0.656 |
| carry | 9.54 | 17.92 | 0.688 | 0.574 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1974-02..1999-09 | 308 | 0.161 | -0.147 | 0.076 | 0.093 | -0.364 | 13.18 | 9.18 | 8.38 |
| panel_second_half | 1999-10..2025-05 | 308 | 0.054 | 0.045 | -0.195 | -0.049 | 0.249 | 5.9 | 5.32 | 7.59 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.304 | -0.04 | -0.331 | 0.001 | 0.427 | 10.47 | 10.93 | -4.32 |
| post_2009 | 2009-01..2025-05 | 197 | -0.034 | 0.093 | -0.049 | -0.384 | 0.44 | 2.44 | 1.41 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | -0.032 | -0.008 | -0.067 | -0.459 | 0.687 | -0.53 | 0.43 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (3 ep.) |
| `stack10` | 0.06 (0.574) | 0.0116 (0.65) | -0.02 (3 ep.) | 6.9 (3 ep.) |
| `sell_equity10` | 0.889 (0.951) | 0.0116 (0.65) | 3.53 (3 ep.) | 9.34 (3 ep.) |
| `replace_trend15` | -0.197 (0.426) | 0.0202 (0.43) | -2.15 (3 ep.) | 2.52 (3 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -26.34* (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `stack10` | n/c | n/c | -38.93 (+1.75) | -45.87 (-0.01) | -20.41 (-1.78) | -24.07* (+2.28) | 104.81 (+18.81) | -23.95 (-0.38) |
| `sell_equity10` | n/c | n/c | -34.48 (+6.19) | -41.65 (+4.21) | -18.45 (+0.18) | -20.34* (+6.00) | 106.0 (+19.99) | -21.53 (+2.03) |
| `replace_trend15` | n/c | n/c | -40.78 (-0.10) | -48.57 (-2.71) | -22.29 (-3.66) | -27.38* (-1.04) | 96.09 (+10.09) | -25.04 (-1.47) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +2.00, +1.83 |
| `stack10` | +0.84 | +0.80 | +2.84, +2.63 |
| `sell_equity10` | +0.07 | +0.07 | +2.07, +1.90 |
| `replace_trend15` | +0.34 | +0.34 | +2.34, +2.17 |

## Panel `bond_commodity_primary_costed` (sensitivity): 1974-02..2025-05, 616 months, trend `own_4_asset_book`, carry `bond_commodity_costed`

bond_commodity; primary; costed. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 14.2251 | 12.7823 | 16.5129 | 0.6015 | -45.86 | 51 | 1.0 | 2.3856 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 14.8676 | 13.4096 | 16.5765 | 0.6381 | -46.02 | 50 | 1.2992 | 3.0992 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 14.0984 | 12.8905 | 15.0554 | 0.6516 | -41.81 | 41 | 0.9966 | 2.3774 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.2682 | 12.8495 | 16.3801 | 0.6092 | -48.78 | 51 | 0.9818 | 2.3422 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +2.00 [+1.02, +3.00] MDE 1.54 31y `exploratory` | -0.36 [-1.92, +1.17] MDE 2.48 2428y `rejected` | +1.70 [+0.71, +2.70] MDE 1.55 43y `exploratory` | +1.50 [+0.45, +2.54] MDE 1.61 55y `unresolved` | -- |
| `stack10` | +2.64 [+1.52, +3.78] MDE 1.76 23y `exploratory` | -0.45 [-2.50, +1.52] MDE 3.14 2483y `rejected` | +2.32 [+1.21, +3.44] MDE 1.78 30y `exploratory` | +1.81 [+0.57, +3.00] MDE 1.85 51y `unresolved` | +0.64 [+0.19, +1.11] MDE 0.70 61y `unresolved` |
| `sell_equity10` | +1.87 [+0.70, +3.04] MDE 1.86 51y `exploratory` | -0.49 [-2.54, +1.49] MDE 3.14 2131y `rejected` | +2.28 [+1.17, +3.41] MDE 1.78 31y `exploratory` | +1.76 [+0.52, +2.97] MDE 1.85 54y `unresolved` | -0.13 [-0.78, +0.54] MDE 0.96 2945y `rejected` |
| `replace_trend15` | +2.04 [+1.17, +2.92] MDE 1.37 23y `exploratory` | -0.32 [-1.88, +1.28] MDE 2.39 2906y `rejected` | +1.81 [+0.94, +2.70] MDE 1.38 30y `exploratory` | +1.27 [+0.29, +2.18] MDE 1.43 62y `unresolved` | +0.04 [-0.78, +0.91] MDE 1.23 41848y `unresolved` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | flat_equity_decade | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +2.59 | +1.41 | +2.84 | +0.37 | +0.04 |
| `stack10` | +1.01 | +0.28 | +0.74 | -0.07 | -0.36 |
| `sell_equity10` | +0.20 | -0.45 | +1.20 | -1.39 | -1.55 |
| `replace_trend15` | +0.30 | -0.21 | -0.37 | -0.15 | -0.44 |

### Leg correlations: 616 months, worst decile = 61 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.047 | 0.089 |
| equity_carry | -0.049 | -0.077 |
| trend_carry | 0.113 | -0.055 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 7.99 | 15.91 | -8.27 | 0.0 |
| trend | 7.25 | 13.17 | 2.004 | 0.656 |
| carry | 7.54 | 17.92 | 0.521 | 0.574 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1974-02..1999-09 | 308 | 0.161 | -0.147 | 0.076 | 0.093 | -0.364 | 11.18 | 9.18 | 8.38 |
| panel_second_half | 1999-10..2025-05 | 308 | 0.054 | 0.045 | -0.195 | -0.049 | 0.249 | 3.9 | 5.32 | 7.59 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.304 | -0.04 | -0.331 | 0.001 | 0.427 | 8.47 | 10.93 | -4.32 |
| post_2009 | 2009-01..2025-05 | 197 | -0.034 | 0.093 | -0.049 | -0.384 | 0.44 | 0.44 | 1.41 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | -0.032 | -0.008 | -0.067 | -0.459 | 0.687 | -2.53 | 0.43 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (3 ep.) |
| `stack10` | 0.043 (0.574) | 0.0116 (0.65) | -0.16 (3 ep.) | 6.19 (3 ep.) |
| `sell_equity10` | 0.872 (0.951) | 0.0116 (0.65) | 3.37 (3 ep.) | 8.62 (3 ep.) |
| `replace_trend15` | -0.222 (0.426) | 0.0202 (0.43) | -2.37 (3 ep.) | 1.5 (3 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -26.34* (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `stack10` | n/c | n/c | -39.19 (+1.49) | -46.02 (-0.16) | -20.44 (-1.81) | -24.17* (+2.17) | 102.9 (+16.89) | -24.06 (-0.50) |
| `sell_equity10` | n/c | n/c | -34.76 (+5.92) | -41.81 (+4.05) | -18.48 (+0.15) | -20.45* (+5.89) | 104.07 (+18.06) | -21.65 (+1.91) |
| `replace_trend15` | n/c | n/c | -41.15 (-0.48) | -48.78 (-2.92) | -22.33 (-3.70) | -27.53* (-1.19) | 93.35 (+7.34) | -25.22 (-1.65) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +2.00, +1.83 |
| `stack10` | +0.64 | +0.60 | +2.64, +2.43 |
| `sell_equity10` | -0.13 | -0.13 | +1.87, +1.70 |
| `replace_trend15` | +0.04 | +0.04 | +2.04, +1.87 |

## Panel `bond_commodity_primary_costed_loading` (sensitivity): 1974-02..2025-05, 616 months, trend `own_4_asset_book`, carry `bond_commodity_costed_loading`

bond_commodity; primary; costed_loading. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 14.2251 | 12.7823 | 16.5129 | 0.6015 | -45.86 | 51 | 1.0 | 2.3856 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 14.627 | 13.1777 | 16.5352 | 0.6251 | -46.0 | 50 | 1.176 | 2.8054 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 13.8579 | 12.6591 | 15.0068 | 0.6376 | -41.78 | 50 | 0.9025 | 2.1531 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 13.9075 | 12.5063 | 16.2893 | 0.5904 | -48.74 | 57 | 0.8483 | 2.0237 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +2.00 [+1.01, +3.06] MDE 1.54 31y `exploratory` | -0.36 [-1.95, +1.32] MDE 2.48 2428y `rejected` | +1.70 [+0.69, +2.78] MDE 1.55 43y `exploratory` | +1.50 [+0.45, +2.63] MDE 1.61 55y `unresolved` | -- |
| `stack10` | +2.40 [+1.34, +3.50] MDE 1.67 25y `exploratory` | -0.69 [-2.64, +1.45] MDE 3.08 1014y `rejected` | +2.09 [+1.03, +3.23] MDE 1.68 33y `exploratory` | +1.68 [+0.52, +2.92] MDE 1.74 52y `unresolved` | +0.40 [+0.08, +0.73] MDE 0.48 72y `unresolved` |
| `sell_equity10` | +1.63 [+0.50, +2.86] MDE 1.76 60y `unresolved` | -0.73 [-2.67, +1.41] MDE 3.08 917y `rejected` | +2.07 [+1.00, +3.20] MDE 1.68 34y `exploratory` | +1.64 [+0.48, +2.89] MDE 1.75 55y `unresolved` | -0.37 [-0.92, +0.18] MDE 0.80 245y `rejected` |
| `replace_trend15` | +1.68 [+0.97, +2.42] MDE 1.11 22y `exploratory` | -0.68 [-2.15, +0.88] MDE 2.23 557y `rejected` | +1.49 [+0.78, +2.25] MDE 1.11 29y `exploratory` | +1.10 [+0.32, +1.87] MDE 1.16 54y `unresolved` | -0.32 [-1.01, +0.34] MDE 0.99 501y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | flat_equity_decade | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +2.59 | +1.41 | +2.84 | +0.37 | +0.04 |
| `stack10` | +0.65 | +0.15 | +0.47 | -0.08 | -0.28 |
| `sell_equity10` | -0.16 | -0.58 | +0.93 | -1.41 | -1.47 |
| `replace_trend15` | -0.24 | -0.40 | -0.77 | -0.17 | -0.32 |

### Leg correlations: 616 months, worst decile = 61 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.047 | 0.089 |
| equity_carry | -0.049 | -0.077 |
| trend_carry | 0.113 | -0.055 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 7.99 | 15.91 | -8.27 | 0.0 |
| trend | 7.25 | 13.17 | 2.004 | 0.656 |
| carry | 5.14 | 12.2 | 0.355 | 0.574 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1974-02..1999-09 | 308 | 0.161 | -0.147 | 0.076 | 0.093 | -0.364 | 7.61 | 9.18 | 8.38 |
| panel_second_half | 1999-10..2025-05 | 308 | 0.054 | 0.045 | -0.195 | -0.049 | 0.249 | 2.66 | 5.32 | 7.59 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.304 | -0.04 | -0.331 | 0.001 | 0.427 | 5.77 | 10.93 | -4.32 |
| post_2009 | 2009-01..2025-05 | 197 | -0.034 | 0.093 | -0.049 | -0.384 | 0.44 | 0.3 | 1.41 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | -0.032 | -0.008 | -0.067 | -0.459 | 0.687 | -1.72 | 0.43 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (3 ep.) |
| `stack10` | 0.026 (0.574) | 0.0079 (0.65) | -0.14 (3 ep.) | 4.05 (3 ep.) |
| `sell_equity10` | 0.856 (0.984) | 0.0079 (0.65) | 3.39 (3 ep.) | 6.47 (3 ep.) |
| `replace_trend15` | -0.247 (0.393) | 0.0147 (0.37) | -2.32 (3 ep.) | -1.53 (3 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -26.34* (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `stack10` | n/c | n/c | -39.71 (+0.96) | -46.0 (-0.14) | -19.87 (-1.24) | -24.89* (+1.46) | 97.06 (+11.05) | -23.93 (-0.36) |
| `sell_equity10` | n/c | n/c | -35.32 (+5.36) | -41.78 (+4.08) | -17.91 (+0.72) | -21.19* (+5.15) | 98.22 (+12.22) | -21.51 (+2.05) |
| `replace_trend15` | n/c | n/c | -41.91 (-1.23) | -48.74 (-2.88) | -21.48 (-2.85) | -28.56* (-2.22) | 85.06 (-0.94) | -25.01 (-1.44) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +2.00, +1.83 |
| `stack10` | +0.40 | +0.36 | +2.40, +2.19 |
| `sell_equity10` | -0.37 | -0.37 | +1.63, +1.46 |
| `replace_trend15` | -0.32 | -0.32 | +1.68, +1.51 |

## Panel `bond_commodity_secondary_gross` (secondary): 1985-01..2026-02, 494 months, trend `aqr_tsmom`, carry `bond_commodity_gross`

bond_commodity; secondary; gross. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.8948 | 14.5159 | 15.9621 | 0.7986 | -46.71 | 41 | 1.0 | 3.4501 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 16.397 | 14.9906 | 16.1105 | 0.8224 | -46.74 | 39 | 1.1917 | 4.1115 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 15.4996 | 14.3345 | 14.6276 | 0.8447 | -42.54 | 39 | 0.9247 | 3.1902 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.9929 | 13.613 | 16.0433 | 0.738 | -48.99 | 50 | 0.7087 | 2.445 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +3.50 [+2.31, +4.66] MDE 1.63 9y `exploratory` | +0.72 [-1.19, +2.81] MDE 2.71 577y `unresolved` | +3.23 [+1.98, +4.37] MDE 1.64 11y `exploratory` | +3.15 [+1.96, +4.34] MDE 1.74 12y `exploratory` | -- |
| `stack10` | +4.00 [+2.54, +5.36] MDE 1.87 9y `exploratory` | +0.36 [-2.08, +3.02] MDE 3.40 3574y `unresolved` | +3.65 [+2.11, +5.03] MDE 1.89 11y `exploratory` | +3.39 [+1.91, +4.91] MDE 1.99 13y `exploratory` | +0.50 [+0.02, +0.97] MDE 0.77 96y `unresolved` |
| `sell_equity10` | +3.10 [+1.50, +4.61] MDE 1.99 17y `exploratory` | +0.33 [-2.11, +2.99] MDE 3.40 4394y `unresolved` | +3.61 [+2.07, +5.00] MDE 1.90 11y `exploratory` | +3.35 [+1.86, +4.88] MDE 2.00 14y `exploratory` | -0.40 [-1.09, +0.31] MDE 1.02 273y `rejected` |
| `replace_trend15` | +2.59 [+1.50, +3.61] MDE 1.48 13y `exploratory` | -0.18 [-2.08, +1.81] MDE 2.56 8516y `rejected` | +2.28 [+1.16, +3.33] MDE 1.48 17y `exploratory` | +1.97 [+0.74, +3.20] MDE 1.54 23y `exploratory` | -0.90 [-1.64, -0.13] MDE 1.34 91y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | flat_equity_decade | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +5.29 | +1.70 | +4.52 | +0.98 | +0.98 |
| `stack10` | +0.83 | +0.18 | +0.94 | +0.13 | -0.16 |
| `sell_equity10` | -0.01 | -0.78 | +1.40 | -1.19 | -1.35 |
| `replace_trend15` | -1.31 | -0.49 | -0.91 | -0.15 | -0.61 |

### Leg correlations: 494 months, worst decile = 49 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.083 | 0.021 |
| equity_carry | 0.006 | -0.066 |
| trend_carry | 0.102 | -0.118 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 9.27 | 15.48 | -8.231 | 0.0 |
| trend | 12.15 | 12.5 | 2.575 | 0.694 |
| carry | 6.14 | 17.53 | 0.06 | 0.531 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1985-01..2005-07 | 247 | 0.252 | -0.103 | 0.057 | 0.026 | -0.544 | 9.41 | 18.17 | 8.65 |
| panel_second_half | 2005-08..2026-02 | 247 | -0.012 | 0.093 | -0.209 | -0.146 | 0.342 | 2.87 | 6.13 | 9.89 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.382 | -0.04 | -0.268 | 0.661 | 0.427 | 10.47 | 16.56 | -4.32 |
| post_2009 | 2009-01..2025-05 | 197 | -0.04 | 0.093 | -0.202 | -0.335 | 0.44 | 2.44 | 3.47 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | 0.02 | -0.008 | -0.26 | -0.589 | 0.687 | -0.53 | 3.55 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (1 ep.) |
| `stack10` | -0.003 (0.531) | 0.013 (0.65) | 0.01 (3 ep.) | -0.4 (1 ep.) |
| `sell_equity10` | 0.822 (0.939) | 0.013 (0.65) | 3.6 (3 ep.) | 2.16 (1 ep.) |
| `replace_trend15` | -0.377 (0.367) | 0.0304 (0.63) | -2.61 (3 ep.) | -4.33 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -37.96 (+0.00) | -46.71 (+0.00) | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `stack10` | n/c | n/c | -36.14 (+1.82) | -46.74 (-0.03) | -19.61 (-1.77) | n/c | n/c | -18.43 (-0.40) |
| `sell_equity10` | n/c | n/c | -31.51 (+6.45) | -42.54 (+4.17) | -17.65 (+0.19) | n/c | n/c | -15.87 (+2.16) |
| `replace_trend15` | n/c | n/c | -39.45 (-1.49) | -48.99 (-2.29) | -21.88 (-4.04) | n/c | n/c | -22.36 (-4.33) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +3.50, +3.33 |
| `stack10` | +0.50 | +0.46 | +4.00, +3.79 |
| `sell_equity10` | -0.40 | -0.40 | +3.10, +2.93 |
| `replace_trend15` | -0.90 | -0.90 | +2.59, +2.43 |

## Panel `bond_commodity_secondary_costed` (sensitivity): 1985-01..2026-02, 494 months, trend `aqr_tsmom`, carry `bond_commodity_costed`

bond_commodity; secondary; costed. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.8948 | 14.5159 | 15.9621 | 0.7986 | -46.71 | 41 | 1.0 | 3.4501 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 16.197 | 14.7928 | 16.1105 | 0.81 | -46.88 | 40 | 1.1033 | 3.8063 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 15.2996 | 14.1367 | 14.6276 | 0.831 | -42.7 | 39 | 0.8563 | 2.9542 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.6929 | 13.316 | 16.0433 | 0.7193 | -49.21 | 50 | 0.6322 | 2.1812 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +3.50 [+2.33, +4.62] MDE 1.63 9y `exploratory` | +0.72 [-1.23, +2.76] MDE 2.71 577y `unresolved` | +3.23 [+2.02, +4.37] MDE 1.64 11y `exploratory` | +3.15 [+1.98, +4.29] MDE 1.74 12y `exploratory` | -- |
| `stack10` | +3.80 [+2.44, +5.07] MDE 1.87 10y `exploratory` | +0.16 [-2.26, +2.76] MDE 3.40 17534y `unresolved` | +3.45 [+2.04, +4.76] MDE 1.89 12y `exploratory` | +3.19 [+1.67, +4.67] MDE 1.99 15y `exploratory` | +0.30 [-0.17, +0.74] MDE 0.77 264y `unresolved` |
| `sell_equity10` | +2.90 [+1.39, +4.33] MDE 1.99 19y `exploratory` | +0.13 [-2.30, +2.72] MDE 3.40 28615y `unresolved` | +3.41 [+1.99, +4.72] MDE 1.90 13y `exploratory` | +3.15 [+1.63, +4.63] MDE 2.00 15y `exploratory` | -0.60 [-1.27, +0.10] MDE 1.02 120y `rejected` |
| `replace_trend15` | +2.29 [+1.28, +3.26] MDE 1.48 17y `exploratory` | -0.48 [-2.27, +1.46] MDE 2.56 1179y `rejected` | +1.98 [+0.91, +2.96] MDE 1.48 23y `exploratory` | +1.67 [+0.45, +2.81] MDE 1.54 32y `exploratory` | -1.20 [-1.97, -0.44] MDE 1.34 51y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | flat_equity_decade | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +5.29 | +1.70 | +4.52 | +0.98 | +0.98 |
| `stack10` | +0.63 | -0.02 | +0.74 | -0.07 | -0.36 |
| `sell_equity10` | -0.21 | -0.98 | +1.20 | -1.39 | -1.55 |
| `replace_trend15` | -1.61 | -0.79 | -1.21 | -0.45 | -0.91 |

### Leg correlations: 494 months, worst decile = 49 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.083 | 0.021 |
| equity_carry | 0.006 | -0.066 |
| trend_carry | 0.102 | -0.118 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 9.27 | 15.48 | -8.231 | 0.0 |
| trend | 12.15 | 12.5 | 2.575 | 0.694 |
| carry | 4.14 | 17.53 | -0.107 | 0.531 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1985-01..2005-07 | 247 | 0.252 | -0.103 | 0.057 | 0.026 | -0.544 | 7.41 | 18.17 | 8.65 |
| panel_second_half | 2005-08..2026-02 | 247 | -0.012 | 0.093 | -0.209 | -0.146 | 0.342 | 0.87 | 6.13 | 9.89 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.382 | -0.04 | -0.268 | 0.661 | 0.427 | 8.47 | 16.56 | -4.32 |
| post_2009 | 2009-01..2025-05 | 197 | -0.04 | 0.093 | -0.202 | -0.335 | 0.44 | 0.44 | 3.47 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | 0.02 | -0.008 | -0.26 | -0.589 | 0.687 | -2.53 | 3.55 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (1 ep.) |
| `stack10` | -0.02 (0.531) | 0.013 (0.65) | -0.14 (3 ep.) | -0.53 (1 ep.) |
| `sell_equity10` | 0.806 (0.939) | 0.013 (0.65) | 3.44 (3 ep.) | 2.03 (1 ep.) |
| `replace_trend15` | -0.402 (0.367) | 0.0304 (0.63) | -2.82 (3 ep.) | -4.51 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -37.96 (+0.00) | -46.71 (+0.00) | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `stack10` | n/c | n/c | -36.41 (+1.55) | -46.88 (-0.18) | -19.64 (-1.80) | n/c | n/c | -18.55 (-0.53) |
| `sell_equity10` | n/c | n/c | -31.8 (+6.16) | -42.7 (+4.01) | -17.68 (+0.16) | n/c | n/c | -16.0 (+2.03) |
| `replace_trend15` | n/c | n/c | -39.83 (-1.87) | -49.21 (-2.50) | -21.93 (-4.09) | n/c | n/c | -22.54 (-4.51) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +3.50, +3.33 |
| `stack10` | +0.30 | +0.26 | +3.80, +3.59 |
| `sell_equity10` | -0.60 | -0.60 | +2.90, +2.73 |
| `replace_trend15` | -1.20 | -1.20 | +2.29, +2.13 |

## Panel `bond_commodity_secondary_costed_loading` (sensitivity): 1985-01..2026-02, 494 months, trend `aqr_tsmom`, carry `bond_commodity_costed_loading`

bond_commodity; secondary; costed_loading. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.8948 | 14.5159 | 15.9621 | 0.7986 | -46.71 | 41 | 1.0 | 3.4501 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 16.0651 | 14.6726 | 16.0425 | 0.8052 | -46.85 | 40 | 1.0559 | 3.643 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 15.1676 | 14.0165 | 14.553 | 0.8262 | -42.66 | 39 | 0.8198 | 2.8283 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.495 | 13.1403 | 15.912 | 0.7128 | -49.16 | 51 | 0.5941 | 2.0498 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +3.50 [+2.33, +4.66] MDE 1.63 9y `exploratory` | +0.72 [-1.16, +2.73] MDE 2.71 577y `unresolved` | +3.23 [+2.04, +4.41] MDE 1.64 11y `exploratory` | +3.15 [+1.99, +4.28] MDE 1.74 12y `exploratory` | -- |
| `stack10` | +3.67 [+2.32, +4.94] MDE 1.76 10y `exploratory` | +0.03 [-2.36, +2.51] MDE 3.34 430505y `unresolved` | +3.35 [+1.97, +4.65] MDE 1.78 12y `exploratory` | +3.16 [+1.78, +4.50] MDE 1.88 14y `exploratory` | +0.17 [-0.14, +0.49] MDE 0.52 386y `unresolved` |
| `sell_equity10` | +2.77 [+1.31, +4.14] MDE 1.88 19y `exploratory` | -0.00 [-2.40, +2.48] MDE 3.34 47413834y `rejected` | +3.32 [+1.93, +4.63] MDE 1.78 12y `exploratory` | +3.12 [+1.73, +4.46] MDE 1.88 14y `exploratory` | -0.73 [-1.30, -0.14] MDE 0.85 56y `rejected` |
| `replace_trend15` | +2.10 [+1.24, +2.92] MDE 1.19 13y `exploratory` | -0.68 [-2.38, +1.09] MDE 2.40 521y `rejected` | +1.86 [+0.95, +2.69] MDE 1.19 17y `exploratory` | +1.64 [+0.65, +2.57] MDE 1.24 22y `exploratory` | -1.40 [-2.01, -0.78] MDE 1.07 24y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | flat_equity_decade | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +5.29 | +1.70 | +4.52 | +0.98 | +0.98 |
| `stack10` | +0.39 | -0.05 | +0.47 | -0.08 | -0.28 |
| `sell_equity10` | -0.44 | -1.01 | +0.93 | -1.41 | -1.47 |
| `replace_trend15` | -1.97 | -0.83 | -1.62 | -0.48 | -0.79 |

### Leg correlations: 494 months, worst decile = 49 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.083 | 0.021 |
| equity_carry | 0.006 | -0.066 |
| trend_carry | 0.102 | -0.118 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 9.27 | 15.48 | -8.231 | 0.0 |
| trend | 12.15 | 12.5 | 2.575 | 0.694 |
| carry | 2.82 | 11.94 | -0.073 | 0.531 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1985-01..2005-07 | 247 | 0.252 | -0.103 | 0.057 | 0.026 | -0.544 | 5.04 | 18.17 | 8.65 |
| panel_second_half | 2005-08..2026-02 | 247 | -0.012 | 0.093 | -0.209 | -0.146 | 0.342 | 0.59 | 6.13 | 9.89 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.382 | -0.04 | -0.268 | 0.661 | 0.427 | 5.77 | 16.56 | -4.32 |
| post_2009 | 2009-01..2025-05 | 197 | -0.04 | 0.093 | -0.202 | -0.335 | 0.44 | 0.3 | 3.47 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | 0.02 | -0.008 | -0.26 | -0.589 | 0.687 | -1.72 | 3.55 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (1 ep.) |
| `stack10` | -0.017 (0.531) | 0.0088 (0.65) | -0.12 (3 ep.) | -0.38 (1 ep.) |
| `sell_equity10` | 0.809 (0.98) | 0.0088 (0.65) | 3.45 (3 ep.) | 2.18 (1 ep.) |
| `replace_trend15` | -0.397 (0.306) | 0.0242 (0.6) | -2.78 (3 ep.) | -4.29 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -37.96 (+0.00) | -46.71 (+0.00) | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `stack10` | n/c | n/c | -36.96 (+1.00) | -46.85 (-0.15) | -19.07 (-1.23) | n/c | n/c | -18.41 (-0.38) |
| `sell_equity10` | n/c | n/c | -32.38 (+5.58) | -42.66 (+4.04) | -17.11 (+0.73) | n/c | n/c | -15.85 (+2.18) |
| `replace_trend15` | n/c | n/c | -40.61 (-2.65) | -49.16 (-2.46) | -21.08 (-3.24) | n/c | n/c | -22.32 (-4.29) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +3.50, +3.33 |
| `stack10` | +0.17 | +0.13 | +3.67, +3.46 |
| `sell_equity10` | -0.73 | -0.73 | +2.77, +2.60 |
| `replace_trend15` | -1.40 | -1.40 | +2.10, +1.93 |

## Panel `bond_commodity_recent_gross` (check): 2013-09..2026-02, 150 months, trend `aqr_tsmom`, carry `bond_commodity_gross`

bond_commodity; recent; gross. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.3702 | 14.2228 | 14.6254 | 0.9331 | -18.48 | 20 | 1.0 | 1.1244 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 15.132 | 13.9642 | 14.7704 | 0.9075 | -19.61 | 19 | 0.9601 | 1.0795 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 13.9154 | 12.957 | 13.3617 | 0.9121 | -17.65 | 14 | 0.8643 | 0.9717 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.5299 | 13.3196 | 15.082 | 0.8489 | -22.36 | 18 | 0.8962 | 1.0076 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.22 [-0.67, +3.21] MDE 3.11 81y `unresolved` | -2.58 [-5.68, +0.48] MDE 5.32 53y `rejected` | +1.40 [-0.43, +3.38] MDE 3.08 60y `unresolved` | +0.64 [-0.92, +2.19] MDE 3.42 273y `unresolved` | -- |
| `stack10` | +0.98 [-1.25, +3.42] MDE 3.56 164y `unresolved` | -4.00 [-7.97, -0.21] MDE 6.56 34y `rejected` | +1.04 [-1.17, +3.47] MDE 3.55 144y `unresolved` | -0.17 [-2.46, +1.86] MDE 4.01 5133y `rejected` | -0.24 [-1.27, +0.64] MDE 1.68 619y `rejected` |
| `sell_equity10` | -0.23 [-2.91, +2.42] MDE 3.93 3506y `rejected` | -4.03 [-8.01, -0.24] MDE 6.56 33y `rejected` | +1.01 [-1.23, +3.45] MDE 3.56 156y `unresolved` | -0.21 [-2.49, +1.84] MDE 4.02 3371y `rejected` | -1.45 [-2.77, -0.29] MDE 2.05 25y `rejected` |
| `replace_trend15` | +0.38 [-1.51, +2.17] MDE 2.97 764y `unresolved` | -3.42 [-6.47, -0.47] MDE 4.94 26y `rejected` | +0.19 [-1.73, +2.03] MDE 2.99 3047y `unresolved` | -0.82 [-3.31, +1.28] MDE 3.65 190y `rejected` | -0.84 [-2.42, +0.69] MDE 2.95 154y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | +1.69 | +0.75 | +0.98 | +0.98 |
| `stack10` | +0.71 | -1.19 | -0.16 | -0.16 |
| `sell_equity10` | -0.48 | -2.43 | -1.35 | -1.35 |
| `replace_trend15` | +0.35 | -2.03 | -0.61 | -0.61 |

### Leg correlations: 150 months, worst decile = 15 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.262 | -0.519 |
| equity_carry | -0.005 | 0.656 |
| trend_carry | 0.018 | -0.59 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 12.46 | 14.84 | -7.557 | 0.0 |
| trend | 4.34 | 13.32 | 2.203 | 0.6 |
| carry | -1.27 | 21.15 | -1.33 | 0.467 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 2013-09..2019-11 | 75 | 0.144 | 0.105 | -0.164 | -0.333 | 0.222 | 8.24 | 5.92 | 12.22 |
| panel_second_half | 2019-12..2026-02 | 75 | -0.028 | -0.03 | -0.337 | -0.73 | 0.755 | -10.77 | 2.75 | 12.71 |
| post_2009 | 2013-09..2025-05 | 141 | 0.02 | -0.008 | -0.26 | -0.589 | 0.687 | -0.53 | 3.55 | 12.12 |
| post_publication | 2013-09..2025-05 | 141 | 0.02 | -0.008 | -0.26 | -0.589 | 0.687 | -0.53 | 3.55 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (1 ep.) | 0.0 (1 ep.) |
| `stack10` | -0.142 (0.467) | 0.0816 (2.14) | -1.77 (1 ep.) | -0.4 (1 ep.) |
| `sell_equity10` | 0.616 (0.867) | 0.0816 (2.14) | 0.19 (1 ep.) | 2.16 (1 ep.) |
| `replace_trend15` | -0.53 (0.333) | 0.113 (1.43) | -4.04 (1 ep.) | -4.33 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | n/c | n/c | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `stack10` | n/c | n/c | n/c | n/c | -19.61 (-1.77) | n/c | n/c | -18.43 (-0.40) |
| `sell_equity10` | n/c | n/c | n/c | n/c | -17.65 (+0.19) | n/c | n/c | -15.87 (+2.16) |
| `replace_trend15` | n/c | n/c | n/c | n/c | -21.88 (-4.04) | n/c | n/c | -22.36 (-4.33) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +1.22, +1.05 |
| `stack10` | -0.24 | -0.28 | +0.98, +0.77 |
| `sell_equity10` | -1.45 | -1.45 | -0.23, -0.40 |
| `replace_trend15` | -0.84 | -0.84 | +0.38, +0.21 |

## Panel `bond_commodity_recent_costed` (sensitivity): 2013-09..2026-02, 150 months, trend `aqr_tsmom`, carry `bond_commodity_costed`

bond_commodity; recent; costed. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.3702 | 14.2228 | 14.6254 | 0.9331 | -18.48 | 20 | 1.0 | 1.1244 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 14.932 | 13.7663 | 14.7704 | 0.894 | -19.64 | 19 | 0.9402 | 1.0571 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 13.7154 | 12.7589 | 13.3617 | 0.8971 | -17.68 | 14 | 0.8465 | 0.9517 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.2299 | 13.0226 | 15.082 | 0.829 | -22.54 | 18 | 0.8685 | 0.9765 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.22 [-0.66, +3.46] MDE 3.11 81y `unresolved` | -2.58 [-5.82, +0.97] MDE 5.32 53y `rejected` | +1.40 [-0.43, +3.59] MDE 3.08 60y `unresolved` | +0.64 [-0.93, +2.33] MDE 3.42 273y `unresolved` | -- |
| `stack10` | +0.78 [-1.55, +3.33] MDE 3.56 259y `unresolved` | -4.20 [-8.49, +0.04] MDE 6.56 31y `rejected` | +0.84 [-1.47, +3.39] MDE 3.55 221y `unresolved` | -0.37 [-2.53, +1.67] MDE 4.01 1101y `rejected` | -0.44 [-1.49, +0.44] MDE 1.68 183y `rejected` |
| `sell_equity10` | -0.43 [-3.10, +2.43] MDE 3.93 1022y `rejected` | -4.23 [-8.53, +0.00] MDE 6.56 30y `rejected` | +0.81 [-1.53, +3.36] MDE 3.56 243y `unresolved` | -0.41 [-2.59, +1.65] MDE 4.02 897y `rejected` | -1.65 [-3.05, -0.48] MDE 2.05 19y `rejected` |
| `replace_trend15` | +0.08 [-1.91, +2.01] MDE 2.97 17298y `unresolved` | -3.72 [-7.06, -0.55] MDE 4.94 22y `rejected` | -0.11 [-2.13, +1.83] MDE 2.99 9449y `rejected` | -1.12 [-3.51, +0.88] MDE 3.65 101y `rejected` | -1.14 [-2.85, +0.34] MDE 2.95 83y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | +1.69 | +0.75 | +0.98 | +0.98 |
| `stack10` | +0.51 | -1.39 | -0.36 | -0.36 |
| `sell_equity10` | -0.68 | -2.63 | -1.55 | -1.55 |
| `replace_trend15` | +0.05 | -2.33 | -0.91 | -0.91 |

### Leg correlations: 150 months, worst decile = 15 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.262 | -0.519 |
| equity_carry | -0.005 | 0.656 |
| trend_carry | 0.018 | -0.59 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 12.46 | 14.84 | -7.557 | 0.0 |
| trend | 4.34 | 13.32 | 2.203 | 0.6 |
| carry | -3.27 | 21.15 | -1.497 | 0.467 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 2013-09..2019-11 | 75 | 0.144 | 0.105 | -0.164 | -0.333 | 0.222 | 6.24 | 5.92 | 12.22 |
| panel_second_half | 2019-12..2026-02 | 75 | -0.028 | -0.03 | -0.337 | -0.73 | 0.755 | -12.77 | 2.75 | 12.71 |
| post_2009 | 2013-09..2025-05 | 141 | 0.02 | -0.008 | -0.26 | -0.589 | 0.687 | -2.53 | 3.55 | 12.12 |
| post_publication | 2013-09..2025-05 | 141 | 0.02 | -0.008 | -0.26 | -0.589 | 0.687 | -2.53 | 3.55 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (1 ep.) | 0.0 (1 ep.) |
| `stack10` | -0.159 (0.467) | 0.0816 (2.14) | -1.8 (1 ep.) | -0.53 (1 ep.) |
| `sell_equity10` | 0.599 (0.867) | 0.0816 (2.14) | 0.16 (1 ep.) | 2.03 (1 ep.) |
| `replace_trend15` | -0.555 (0.333) | 0.113 (1.43) | -4.09 (1 ep.) | -4.51 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | n/c | n/c | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `stack10` | n/c | n/c | n/c | n/c | -19.64 (-1.80) | n/c | n/c | -18.55 (-0.53) |
| `sell_equity10` | n/c | n/c | n/c | n/c | -17.68 (+0.16) | n/c | n/c | -16.0 (+2.03) |
| `replace_trend15` | n/c | n/c | n/c | n/c | -21.93 (-4.09) | n/c | n/c | -22.54 (-4.51) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +1.22, +1.05 |
| `stack10` | -0.44 | -0.48 | +0.78, +0.57 |
| `sell_equity10` | -1.65 | -1.65 | -0.43, -0.60 |
| `replace_trend15` | -1.14 | -1.14 | +0.08, -0.09 |

## Panel `bond_commodity_recent_costed_loading` (sensitivity): 2013-09..2026-02, 150 months, trend `aqr_tsmom`, carry `bond_commodity_costed_loading`

bond_commodity; recent; costed_loading. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.3702 | 14.2228 | 14.6254 | 0.9331 | -18.48 | 20 | 1.0 | 1.1244 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 15.0362 | 13.8814 | 14.6913 | 0.906 | -19.07 | 19 | 0.9558 | 1.0747 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 13.8196 | 12.8741 | 13.2737 | 0.911 | -17.11 | 14 | 0.8606 | 0.9676 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.3862 | 13.2044 | 14.9078 | 0.8494 | -22.32 | 18 | 0.8913 | 1.0021 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.22 [-0.65, +3.39] MDE 3.11 81y `unresolved` | -2.58 [-5.84, +0.76] MDE 5.32 53y `rejected` | +1.40 [-0.42, +3.55] MDE 3.08 60y `unresolved` | +0.64 [-0.91, +2.28] MDE 3.42 273y `unresolved` | -- |
| `stack10` | +0.89 [-1.19, +3.28] MDE 3.33 177y `unresolved` | -4.09 [-8.04, -0.03] MDE 6.44 31y `rejected` | +1.01 [-1.02, +3.40] MDE 3.31 133y `unresolved` | -0.07 [-1.97, +1.91] MDE 3.69 25592y `rejected` | -0.33 [-1.06, +0.27] MDE 1.14 146y `rejected` |
| `sell_equity10` | -0.33 [-2.73, +2.38] MDE 3.72 1587y `rejected` | -4.13 [-8.08, -0.06] MDE 6.44 30y `rejected` | +0.99 [-1.07, +3.37] MDE 3.32 142y `unresolved` | -0.11 [-2.01, +1.92] MDE 3.70 11424y `rejected` | -1.55 [-2.62, -0.61] MDE 1.64 14y `rejected` |
| `replace_trend15` | +0.24 [-1.20, +1.73] MDE 2.32 1208y `unresolved` | -3.56 [-6.43, -0.76] MDE 4.58 21y `rejected` | +0.19 [-1.25, +1.68] MDE 2.33 1950y `unresolved` | -0.65 [-2.28, +0.89] MDE 2.76 174y `rejected` | -0.98 [-2.43, +0.25] MDE 2.31 69y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | +1.69 | +0.75 | +0.98 | +0.98 |
| `stack10` | +0.31 | -0.98 | -0.28 | -0.28 |
| `sell_equity10` | -0.88 | -2.22 | -1.47 | -1.47 |
| `replace_trend15` | -0.25 | -1.72 | -0.79 | -0.79 |

### Leg correlations: 150 months, worst decile = 15 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.262 | -0.519 |
| equity_carry | -0.005 | 0.656 |
| trend_carry | 0.018 | -0.59 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 12.46 | 14.84 | -7.557 | 0.0 |
| trend | 4.34 | 13.32 | 2.203 | 0.6 |
| carry | -2.22 | 14.41 | -1.019 | 0.467 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 2013-09..2019-11 | 75 | 0.144 | 0.105 | -0.164 | -0.333 | 0.222 | 4.25 | 5.92 | 12.22 |
| panel_second_half | 2019-12..2026-02 | 75 | -0.028 | -0.03 | -0.337 | -0.73 | 0.755 | -8.7 | 2.75 | 12.71 |
| post_2009 | 2013-09..2025-05 | 141 | 0.02 | -0.008 | -0.26 | -0.589 | 0.687 | -1.72 | 3.55 | 12.12 |
| post_publication | 2013-09..2025-05 | 141 | 0.02 | -0.008 | -0.26 | -0.589 | 0.687 | -1.72 | 3.55 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (1 ep.) | 0.0 (1 ep.) |
| `stack10` | -0.111 (0.467) | 0.0556 (2.14) | -1.23 (1 ep.) | -0.38 (1 ep.) |
| `sell_equity10` | 0.647 (1.0) | 0.0556 (2.14) | 0.73 (1 ep.) | 2.18 (1 ep.) |
| `replace_trend15` | -0.483 (0.333) | 0.0739 (1.19) | -3.24 (1 ep.) | -4.29 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | n/c | n/c | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `stack10` | n/c | n/c | n/c | n/c | -19.07 (-1.23) | n/c | n/c | -18.41 (-0.38) |
| `sell_equity10` | n/c | n/c | n/c | n/c | -17.11 (+0.73) | n/c | n/c | -15.85 (+2.18) |
| `replace_trend15` | n/c | n/c | n/c | n/c | -21.08 (-3.24) | n/c | n/c | -22.32 (-4.29) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +1.22, +1.05 |
| `stack10` | -0.33 | -0.38 | +0.89, +0.68 |
| `sell_equity10` | -1.55 | -1.55 | -0.33, -0.50 |
| `replace_trend15` | -0.98 | -0.98 | +0.24, +0.07 |

## Panel `commodity_only_primary_gross` (primary): 1974-02..2025-05, 616 months, trend `own_4_asset_book`, carry `commodity_only_gross`

commodity_only; primary; gross. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 14.2251 | 12.7823 | 16.5129 | 0.6015 | -45.86 | 51 | 1.0 | 2.3856 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 14.6184 | 13.1722 | 16.5081 | 0.6255 | -45.71 | 50 | 1.1899 | 2.8387 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 13.8492 | 12.6542 | 14.9745 | 0.6383 | -41.48 | 50 | 0.9139 | 2.1801 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 13.8946 | 12.4975 | 16.2534 | 0.5907 | -48.34 | 58 | 0.8645 | 2.0625 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +2.00 [+1.03, +3.04] MDE 1.54 31y `exploratory` | -0.36 [-1.94, +1.29] MDE 2.48 2428y `rejected` | +1.70 [+0.72, +2.77] MDE 1.55 43y `exploratory` | +1.50 [+0.46, +2.61] MDE 1.61 55y `unresolved` | -- |
| `stack10` | +2.39 [+1.35, +3.46] MDE 1.59 23y `exploratory` | -0.70 [-2.71, +1.38] MDE 3.03 959y `rejected` | +2.10 [+1.04, +3.16] MDE 1.60 30y `exploratory` | +1.82 [+0.71, +2.92] MDE 1.65 40y `exploratory` | +0.39 [+0.10, +0.67] MDE 0.35 41y `exploratory` |
| `sell_equity10` | +1.62 [+0.50, +2.76] MDE 1.69 56y `unresolved` | -0.74 [-2.74, +1.34] MDE 3.03 868y `rejected` | +2.07 [+1.02, +3.14] MDE 1.61 31y `exploratory` | +1.79 [+0.67, +2.89] MDE 1.66 42y `exploratory` | -0.38 [-0.92, +0.17] MDE 0.73 191y `rejected` |
| `replace_trend15` | +1.67 [+1.02, +2.30] MDE 0.95 16y `exploratory` | -0.69 [-2.16, +0.79] MDE 2.14 494y `rejected` | +1.49 [+0.81, +2.13] MDE 0.95 21y `exploratory` | +1.29 [+0.64, +1.95] MDE 0.97 27y `exploratory` | -0.33 [-1.00, +0.30] MDE 0.92 401y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | flat_equity_decade | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +2.59 | +1.41 | +2.84 | +0.37 | +0.04 |
| `stack10` | +0.41 | +0.38 | +0.72 | +0.17 | +0.04 |
| `sell_equity10` | -0.40 | -0.35 | +1.18 | -1.15 | -1.15 |
| `replace_trend15` | -0.60 | -0.06 | -0.40 | +0.21 | +0.16 |

### Leg correlations: 616 months, worst decile = 61 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.047 | 0.089 |
| equity_carry | -0.039 | 0.062 |
| trend_carry | 0.024 | -0.027 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 7.99 | 15.91 | -8.27 | 0.0 |
| trend | 7.25 | 13.17 | 2.004 | 0.656 |
| carry | 5.05 | 8.94 | 0.247 | 0.525 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1974-02..1999-09 | 308 | 0.02 | -0.128 | 0.076 | 0.151 | 0.124 | 5.17 | 9.18 | 8.38 |
| panel_second_half | 1999-10..2025-05 | 308 | 0.028 | 0.055 | -0.195 | -0.226 | 0.098 | 4.93 | 5.32 | 7.59 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.082 | 0.032 | -0.331 | -0.48 | 0.17 | 8.28 | 10.93 | -4.32 |
| post_2009 | 2009-01..2025-05 | 197 | -0.022 | 0.072 | -0.049 | -0.506 | 0.2 | 2.82 | 1.41 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | 0.031 | 0.068 | -0.067 | -0.458 | 0.317 | 1.48 | 0.43 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (3 ep.) |
| `stack10` | 0.015 (0.525) | 0.0086 (1.0) | -0.02 (3 ep.) | 0.36 (3 ep.) |
| `sell_equity10` | 0.845 (0.984) | 0.0086 (1.0) | 3.5 (3 ep.) | 2.79 (3 ep.) |
| `replace_trend15` | -0.264 (0.393) | 0.0157 (0.47) | -2.16 (3 ep.) | -6.6 (3 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -26.34* (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `stack10` | n/c | n/c | -40.07 (+0.60) | -45.71 (+0.14) | -19.45 (-0.82) | -23.73* (+2.61) | 83.33 (-2.67) | -22.44 (+1.13) |
| `sell_equity10` | n/c | n/c | -35.7 (+4.97) | -41.48 (+4.38) | -17.49 (+1.14) | -19.99* (+6.36) | 84.43 (-1.57) | -19.99 (+3.58) |
| `replace_trend15` | n/c | n/c | -42.44 (-1.77) | -48.34 (-2.48) | -20.86 (-2.23) | -26.9* (-0.56) | 65.99 (-20.01) | -22.8 (+0.77) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +2.00, +1.83 |
| `stack10` | +0.39 | +0.35 | +2.39, +2.18 |
| `sell_equity10` | -0.38 | -0.38 | +1.62, +1.45 |
| `replace_trend15` | -0.33 | -0.33 | +1.67, +1.50 |

## Panel `commodity_only_primary_costed` (sensitivity): 1974-02..2025-05, 616 months, trend `own_4_asset_book`, carry `commodity_only_costed`

commodity_only; primary; costed. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 14.2251 | 12.7823 | 16.5129 | 0.6015 | -45.86 | 51 | 1.0 | 2.3856 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 14.4184 | 12.9741 | 16.5081 | 0.6134 | -45.86 | 51 | 1.0815 | 2.5799 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 13.6492 | 12.4561 | 14.9745 | 0.625 | -41.64 | 50 | 0.8307 | 1.9817 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 13.5946 | 12.2003 | 16.2534 | 0.5723 | -48.56 | 58 | 0.7497 | 1.7885 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +2.00 [+1.02, +2.98] MDE 1.54 31y `exploratory` | -0.36 [-1.94, +1.25] MDE 2.48 2428y `rejected` | +1.70 [+0.70, +2.69] MDE 1.55 43y `exploratory` | +1.50 [+0.48, +2.56] MDE 1.61 55y `unresolved` | -- |
| `stack10` | +2.19 [+1.17, +3.15] MDE 1.59 27y `exploratory` | -0.90 [-2.89, +1.19] MDE 3.03 580y `rejected` | +1.90 [+0.86, +2.89] MDE 1.60 37y `exploratory` | +1.62 [+0.54, +2.67] MDE 1.65 50y `unresolved` | +0.19 [-0.08, +0.49] MDE 0.35 168y `unresolved` |
| `sell_equity10` | +1.42 [+0.29, +2.48] MDE 1.69 73y `unresolved` | -0.94 [-2.92, +1.16] MDE 3.03 537y `rejected` | +1.87 [+0.83, +2.86] MDE 1.61 38y `exploratory` | +1.59 [+0.50, +2.63] MDE 1.66 53y `unresolved` | -0.58 [-1.14, +0.02] MDE 0.73 82y `rejected` |
| `replace_trend15` | +1.37 [+0.75, +1.98] MDE 0.95 25y `exploratory` | -0.99 [-2.49, +0.58] MDE 2.14 240y `rejected` | +1.19 [+0.55, +1.83] MDE 0.95 32y `exploratory` | +0.99 [+0.33, +1.61] MDE 0.97 46y `exploratory` | -0.63 [-1.28, +0.01] MDE 0.92 110y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | flat_equity_decade | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +2.59 | +1.41 | +2.84 | +0.37 | +0.04 |
| `stack10` | +0.21 | +0.18 | +0.52 | -0.03 | -0.16 |
| `sell_equity10` | -0.60 | -0.55 | +0.98 | -1.35 | -1.35 |
| `replace_trend15` | -0.90 | -0.36 | -0.70 | -0.09 | -0.14 |

### Leg correlations: 616 months, worst decile = 61 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.047 | 0.089 |
| equity_carry | -0.039 | 0.062 |
| trend_carry | 0.024 | -0.027 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 7.99 | 15.91 | -8.27 | 0.0 |
| trend | 7.25 | 13.17 | 2.004 | 0.656 |
| carry | 3.05 | 8.94 | 0.081 | 0.492 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1974-02..1999-09 | 308 | 0.02 | -0.128 | 0.076 | 0.151 | 0.124 | 3.17 | 9.18 | 8.38 |
| panel_second_half | 1999-10..2025-05 | 308 | 0.028 | 0.055 | -0.195 | -0.226 | 0.098 | 2.93 | 5.32 | 7.59 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.082 | 0.032 | -0.331 | -0.48 | 0.17 | 6.28 | 10.93 | -4.32 |
| post_2009 | 2009-01..2025-05 | 197 | -0.022 | 0.072 | -0.049 | -0.506 | 0.2 | 0.82 | 1.41 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | 0.031 | 0.068 | -0.067 | -0.458 | 0.317 | -0.52 | 0.43 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (3 ep.) |
| `stack10` | -0.001 (0.475) | 0.0086 (1.0) | -0.17 (3 ep.) | -0.29 (3 ep.) |
| `sell_equity10` | 0.828 (0.984) | 0.0086 (1.0) | 3.34 (3 ep.) | 2.13 (3 ep.) |
| `replace_trend15` | -0.289 (0.393) | 0.0157 (0.47) | -2.37 (3 ep.) | -7.49 (3 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -26.34* (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `stack10` | n/c | n/c | -40.33 (+0.35) | -45.86 (-0.01) | -19.48 (-0.85) | -23.84* (+2.51) | 81.62 (-4.39) | -22.56 (+1.01) |
| `sell_equity10` | n/c | n/c | -35.97 (+4.70) | -41.64 (+4.22) | -17.52 (+1.11) | -20.09* (+6.25) | 82.7 (-3.30) | -20.11 (+3.46) |
| `replace_trend15` | n/c | n/c | -42.81 (-2.13) | -48.56 (-2.70) | -20.9 (-2.27) | -27.05* (-0.71) | 63.66 (-22.34) | -22.98 (+0.59) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +2.00, +1.83 |
| `stack10` | +0.19 | +0.15 | +2.19, +1.98 |
| `sell_equity10` | -0.58 | -0.58 | +1.42, +1.25 |
| `replace_trend15` | -0.63 | -0.63 | +1.37, +1.20 |

## Panel `commodity_only_primary_costed_loading` (sensitivity): 1974-02..2025-05, 616 months, trend `own_4_asset_book`, carry `commodity_only_costed_loading`

commodity_only; primary; costed_loading. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 14.2251 | 12.7823 | 16.5129 | 0.6015 | -45.86 | 51 | 1.0 | 2.3856 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 14.3212 | 12.8785 | 16.5044 | 0.6076 | -45.89 | 51 | 1.0374 | 2.4747 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 13.552 | 12.3607 | 14.9691 | 0.6187 | -41.67 | 50 | 0.7969 | 1.9011 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 13.4487 | 12.0582 | 16.239 | 0.5638 | -48.59 | 58 | 0.7052 | 1.6824 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +2.00 [+1.03, +2.99] MDE 1.54 31y `exploratory` | -0.36 [-1.92, +1.20] MDE 2.48 2428y `rejected` | +1.70 [+0.71, +2.70] MDE 1.55 43y `exploratory` | +1.50 [+0.46, +2.60] MDE 1.61 55y `unresolved` | -- |
| `stack10` | +2.09 [+1.09, +3.11] MDE 1.57 29y `exploratory` | -1.00 [-2.91, +1.02] MDE 3.01 468y `rejected` | +1.80 [+0.78, +2.81] MDE 1.58 39y `exploratory` | +1.55 [+0.48, +2.64] MDE 1.63 53y `unresolved` | +0.10 [-0.10, +0.28] MDE 0.24 315y `unresolved` |
| `sell_equity10` | +1.33 [+0.23, +2.41] MDE 1.67 81y `unresolved` | -1.03 [-2.95, +0.99] MDE 3.01 436y `rejected` | +1.78 [+0.75, +2.78] MDE 1.58 41y `exploratory` | +1.52 [+0.43, +2.60] MDE 1.63 56y `unresolved` | -0.67 [-1.15, -0.19] MDE 0.68 52y `rejected` |
| `replace_trend15` | +1.22 [+0.64, +1.77] MDE 0.86 26y `exploratory` | -1.14 [-2.53, +0.30] MDE 2.10 175y `rejected` | +1.05 [+0.47, +1.62] MDE 0.86 34y `exploratory` | +0.89 [+0.32, +1.45] MDE 0.88 48y `exploratory` | -0.78 [-1.38, -0.23] MDE 0.84 61y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | flat_equity_decade | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +2.59 | +1.41 | +2.84 | +0.37 | +0.04 |
| `stack10` | +0.10 | +0.09 | +0.32 | -0.06 | -0.15 |
| `sell_equity10` | -0.70 | -0.64 | +0.78 | -1.38 | -1.33 |
| `replace_trend15` | -1.05 | -0.50 | -1.00 | -0.13 | -0.12 |

### Leg correlations: 616 months, worst decile = 61 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.047 | 0.089 |
| equity_carry | -0.039 | 0.062 |
| trend_carry | 0.024 | -0.027 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 7.99 | 15.91 | -8.27 | 0.0 |
| trend | 7.25 | 13.17 | 2.004 | 0.656 |
| carry | 2.08 | 6.09 | 0.055 | 0.492 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1974-02..1999-09 | 308 | 0.02 | -0.128 | 0.076 | 0.151 | 0.124 | 2.16 | 9.18 | 8.38 |
| panel_second_half | 1999-10..2025-05 | 308 | 0.028 | 0.055 | -0.195 | -0.226 | 0.098 | 1.99 | 5.32 | 7.59 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.082 | 0.032 | -0.331 | -0.48 | 0.17 | 4.27 | 10.93 | -4.32 |
| post_2009 | 2009-01..2025-05 | 197 | -0.022 | 0.072 | -0.049 | -0.506 | 0.2 | 0.56 | 1.41 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | 0.031 | 0.068 | -0.067 | -0.458 | 0.317 | -0.35 | 0.43 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (3 ep.) |
| `stack10` | -0.004 (0.459) | 0.0058 (1.0) | -0.14 (3 ep.) | -0.32 (3 ep.) |
| `sell_equity10` | 0.826 (1.0) | 0.0058 (1.0) | 3.37 (3 ep.) | 2.1 (3 ep.) |
| `replace_trend15` | -0.292 (0.344) | 0.0116 (0.37) | -2.32 (3 ep.) | -7.56 (3 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -26.34* (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `stack10` | n/c | n/c | -40.48 (+0.19) | -45.89 (-0.03) | -19.21 (-0.58) | -24.66* (+1.68) | 82.71 (-3.30) | -22.9 (+0.67) |
| `sell_equity10` | n/c | n/c | -36.14 (+4.54) | -41.67 (+4.19) | -17.25 (+1.38) | -20.96* (+5.39) | 83.81 (-2.19) | -20.46 (+3.10) |
| `replace_trend15` | n/c | n/c | -43.03 (-2.35) | -48.59 (-2.73) | -20.51 (-1.88) | -28.24* (-1.90) | 65.14 (-20.86) | -23.48 (+0.08) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +2.00, +1.83 |
| `stack10` | +0.10 | +0.05 | +2.09, +1.88 |
| `sell_equity10` | -0.67 | -0.67 | +1.33, +1.16 |
| `replace_trend15` | -0.78 | -0.78 | +1.22, +1.05 |

## Panel `commodity_only_secondary_gross` (secondary): 1985-01..2026-02, 494 months, trend `aqr_tsmom`, carry `commodity_only_gross`

commodity_only; secondary; gross. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.8948 | 14.5159 | 15.9621 | 0.7986 | -46.71 | 41 | 1.0 | 3.4501 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 16.224 | 14.8287 | 16.0376 | 0.8154 | -46.57 | 40 | 1.1338 | 3.9118 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 15.3266 | 14.1732 | 14.5462 | 0.8375 | -42.36 | 39 | 0.8806 | 3.038 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.7334 | 13.378 | 15.8868 | 0.7289 | -48.76 | 51 | 0.6624 | 2.2852 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +3.50 [+2.37, +4.71] MDE 1.63 9y `exploratory` | +0.72 [-1.12, +2.76] MDE 2.71 577y `unresolved` | +3.23 [+2.05, +4.44] MDE 1.64 11y `exploratory` | +3.15 [+1.97, +4.27] MDE 1.74 12y `exploratory` | -- |
| `stack10` | +3.82 [+2.56, +5.07] MDE 1.73 8y `exploratory` | +0.19 [-2.14, +2.69] MDE 3.32 12353y `unresolved` | +3.52 [+2.23, +4.80] MDE 1.75 10y `exploratory` | +3.51 [+2.21, +4.75] MDE 1.86 11y `exploratory` | +0.33 [+0.08, +0.58] MDE 0.38 55y `unresolved` |
| `sell_equity10` | +2.93 [+1.56, +4.33] MDE 1.85 17y `exploratory` | +0.16 [-2.17, +2.66] MDE 3.32 18676y `unresolved` | +3.49 [+2.20, +4.76] MDE 1.75 10y `exploratory` | +3.47 [+2.17, +4.72] MDE 1.87 11y `exploratory` | -0.57 [-1.11, +0.00] MDE 0.77 75y `rejected` |
| `replace_trend15` | +2.33 [+1.56, +3.06] MDE 1.07 9y `exploratory` | -0.44 [-2.05, +1.33] MDE 2.34 1179y `rejected` | +2.11 [+1.34, +2.87] MDE 1.07 11y `exploratory` | +2.18 [+1.36, +2.95] MDE 1.14 10y `exploratory` | -1.16 [-1.80, -0.52] MDE 0.92 26y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | flat_equity_decade | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +5.29 | +1.70 | +4.52 | +0.98 | +0.98 |
| `stack10` | +0.38 | +0.27 | +0.72 | +0.17 | +0.04 |
| `sell_equity10` | -0.45 | -0.69 | +1.18 | -1.15 | -1.15 |
| `replace_trend15` | -1.98 | -0.34 | -1.24 | -0.10 | -0.31 |

### Leg correlations: 494 months, worst decile = 49 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.083 | 0.021 |
| equity_carry | 0.023 | 0.124 |
| trend_carry | 0.153 | -0.003 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 9.27 | 15.48 | -8.231 | 0.0 |
| trend | 12.15 | 12.5 | 2.575 | 0.694 |
| carry | 4.41 | 8.74 | -0.105 | 0.49 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1985-01..2005-07 | 247 | 0.187 | -0.04 | 0.057 | 0.22 | 0.199 | 4.96 | 18.17 | 8.65 |
| panel_second_half | 2005-08..2026-02 | 247 | 0.121 | 0.088 | -0.209 | -0.127 | 0.099 | 3.85 | 6.13 | 9.89 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.222 | 0.032 | -0.268 | 0.014 | 0.17 | 8.28 | 16.56 | -4.32 |
| post_2009 | 2009-01..2025-05 | 197 | 0.145 | 0.072 | -0.202 | -0.179 | 0.2 | 2.82 | 3.47 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | 0.2 | 0.068 | -0.26 | -0.174 | 0.317 | 1.48 | 3.55 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (1 ep.) |
| `stack10` | -0.02 (0.49) | 0.0135 (1.66) | -0.02 (3 ep.) | 1.17 (1 ep.) |
| `sell_equity10` | 0.806 (0.98) | 0.0135 (1.66) | 3.55 (3 ep.) | 3.77 (1 ep.) |
| `replace_trend15` | -0.402 (0.347) | 0.0311 (1.06) | -2.62 (3 ep.) | -2.04 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -37.96 (+0.00) | -46.71 (+0.00) | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `stack10` | n/c | n/c | -37.34 (+0.62) | -46.57 (+0.14) | -18.66 (-0.82) | n/c | n/c | -16.85 (+1.17) |
| `sell_equity10` | n/c | n/c | -32.79 (+5.17) | -42.36 (+4.35) | -16.7 (+1.15) | n/c | n/c | -14.26 (+3.77) |
| `replace_trend15` | n/c | n/c | -41.16 (-3.20) | -48.76 (-2.06) | -20.46 (-2.62) | n/c | n/c | -20.07 (-2.04) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +3.50, +3.33 |
| `stack10` | +0.33 | +0.29 | +3.82, +3.61 |
| `sell_equity10` | -0.57 | -0.57 | +2.93, +2.76 |
| `replace_trend15` | -1.16 | -1.16 | +2.33, +2.17 |

## Panel `commodity_only_secondary_costed` (sensitivity): 1985-01..2026-02, 494 months, trend `aqr_tsmom`, carry `commodity_only_costed`

commodity_only; secondary; costed. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.8948 | 14.5159 | 15.9621 | 0.7986 | -46.71 | 41 | 1.0 | 3.4501 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 16.024 | 14.631 | 16.0376 | 0.8029 | -46.72 | 41 | 1.0499 | 3.6223 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 15.1266 | 13.9753 | 14.5462 | 0.8237 | -42.52 | 39 | 0.8156 | 2.8139 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.4334 | 13.081 | 15.8868 | 0.71 | -48.97 | 51 | 0.5913 | 2.0399 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +3.50 [+2.27, +4.63] MDE 1.63 9y `exploratory` | +0.72 [-1.39, +2.69] MDE 2.71 577y `unresolved` | +3.23 [+1.96, +4.37] MDE 1.64 11y `exploratory` | +3.15 [+2.04, +4.32] MDE 1.74 12y `exploratory` | -- |
| `stack10` | +3.62 [+2.32, +4.82] MDE 1.73 9y `exploratory` | -0.01 [-2.51, +2.41] MDE 3.32 6437169y `rejected` | +3.32 [+1.93, +4.56] MDE 1.75 11y `exploratory` | +3.31 [+2.07, +4.57] MDE 1.86 12y `exploratory` | +0.13 [-0.13, +0.37] MDE 0.38 359y `unresolved` |
| `sell_equity10` | +2.73 [+1.23, +4.08] MDE 1.85 19y `exploratory` | -0.04 [-2.54, +2.37] MDE 3.32 232441y `rejected` | +3.29 [+1.89, +4.54] MDE 1.75 12y `exploratory` | +3.27 [+2.03, +4.54] MDE 1.87 12y `exploratory` | -0.77 [-1.32, -0.20] MDE 0.77 41y `rejected` |
| `replace_trend15` | +2.03 [+1.25, +2.76] MDE 1.07 11y `exploratory` | -0.74 [-2.46, +0.99] MDE 2.34 415y `rejected` | +1.81 [+0.99, +2.57] MDE 1.07 14y `exploratory` | +1.88 [+1.11, +2.68] MDE 1.14 14y `exploratory` | -1.46 [-2.08, -0.82] MDE 0.92 16y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | flat_equity_decade | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +5.29 | +1.70 | +4.52 | +0.98 | +0.98 |
| `stack10` | +0.18 | +0.07 | +0.52 | -0.03 | -0.16 |
| `sell_equity10` | -0.65 | -0.89 | +0.98 | -1.35 | -1.35 |
| `replace_trend15` | -2.28 | -0.64 | -1.54 | -0.40 | -0.61 |

### Leg correlations: 494 months, worst decile = 49 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.083 | 0.021 |
| equity_carry | 0.023 | 0.124 |
| trend_carry | 0.153 | -0.003 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 9.27 | 15.48 | -8.231 | 0.0 |
| trend | 12.15 | 12.5 | 2.575 | 0.694 |
| carry | 2.41 | 8.74 | -0.271 | 0.469 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1985-01..2005-07 | 247 | 0.187 | -0.04 | 0.057 | 0.22 | 0.199 | 2.96 | 18.17 | 8.65 |
| panel_second_half | 2005-08..2026-02 | 247 | 0.121 | 0.088 | -0.209 | -0.127 | 0.099 | 1.85 | 6.13 | 9.89 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.222 | 0.032 | -0.268 | 0.014 | 0.17 | 6.28 | 16.56 | -4.32 |
| post_2009 | 2009-01..2025-05 | 197 | 0.145 | 0.072 | -0.202 | -0.179 | 0.2 | 0.82 | 3.47 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | 0.2 | 0.068 | -0.26 | -0.174 | 0.317 | -0.52 | 3.55 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (1 ep.) |
| `stack10` | -0.036 (0.449) | 0.0135 (1.66) | -0.17 (3 ep.) | 1.05 (1 ep.) |
| `sell_equity10` | 0.789 (0.98) | 0.0135 (1.66) | 3.39 (3 ep.) | 3.64 (1 ep.) |
| `replace_trend15` | -0.427 (0.347) | 0.0311 (1.06) | -2.84 (3 ep.) | -2.22 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -37.96 (+0.00) | -46.71 (+0.00) | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `stack10` | n/c | n/c | -37.61 (+0.35) | -46.72 (-0.01) | -18.69 (-0.85) | n/c | n/c | -16.98 (+1.05) |
| `sell_equity10` | n/c | n/c | -33.08 (+4.88) | -42.52 (+4.19) | -16.73 (+1.11) | n/c | n/c | -14.39 (+3.64) |
| `replace_trend15` | n/c | n/c | -41.53 (-3.57) | -48.97 (-2.27) | -20.51 (-2.67) | n/c | n/c | -20.25 (-2.22) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +3.50, +3.33 |
| `stack10` | +0.13 | +0.09 | +3.62, +3.41 |
| `sell_equity10` | -0.77 | -0.77 | +2.73, +2.56 |
| `replace_trend15` | -1.46 | -1.46 | +2.03, +1.87 |

## Panel `commodity_only_secondary_costed_loading` (sensitivity): 1985-01..2026-02, 494 months, trend `aqr_tsmom`, carry `commodity_only_costed_loading`

commodity_only; secondary; costed_loading. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.8948 | 14.5159 | 15.9621 | 0.7986 | -46.71 | 41 | 1.0 | 3.4501 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 15.9472 | 14.5599 | 16.0083 | 0.7996 | -46.74 | 41 | 1.02 | 3.5191 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 15.0498 | 13.9041 | 14.5147 | 0.8202 | -42.54 | 39 | 0.7924 | 2.7338 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.3183 | 12.9746 | 15.8404 | 0.7048 | -49.01 | 57 | 0.5666 | 1.9548 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +3.50 [+2.28, +4.63] MDE 1.63 9y `exploratory` | +0.72 [-1.28, +2.75] MDE 2.71 577y `unresolved` | +3.23 [+1.98, +4.37] MDE 1.64 11y `exploratory` | +3.15 [+1.98, +4.29] MDE 1.74 12y `exploratory` | -- |
| `stack10` | +3.55 [+2.26, +4.75] MDE 1.69 9y `exploratory` | -0.09 [-2.49, +2.39] MDE 3.30 61815y `rejected` | +3.25 [+1.94, +4.45] MDE 1.71 11y `exploratory` | +3.22 [+1.96, +4.45] MDE 1.81 12y `exploratory` | +0.05 [-0.13, +0.23] MDE 0.26 1012y `unresolved` |
| `sell_equity10` | +2.65 [+1.21, +3.99] MDE 1.82 19y `exploratory` | -0.12 [-2.52, +2.35] MDE 3.30 30649y `rejected` | +3.23 [+1.90, +4.43] MDE 1.71 12y `exploratory` | +3.19 [+1.92, +4.42] MDE 1.82 12y `exploratory` | -0.85 [-1.35, -0.29] MDE 0.72 30y `rejected` |
| `replace_trend15` | +1.92 [+1.18, +2.60] MDE 0.96 10y `exploratory` | -0.85 [-2.50, +0.91] MDE 2.30 299y `rejected` | +1.72 [+0.97, +2.41] MDE 0.96 13y `exploratory` | +1.76 [+1.02, +2.43] MDE 1.02 13y `exploratory` | -1.58 [-2.13, -1.01] MDE 0.85 12y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | flat_equity_decade | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | +5.29 | +1.70 | +4.52 | +0.98 | +0.98 |
| `stack10` | +0.09 | +0.01 | +0.32 | -0.06 | -0.15 |
| `sell_equity10` | -0.75 | -0.94 | +0.78 | -1.38 | -1.33 |
| `replace_trend15` | -2.42 | -0.73 | -1.84 | -0.44 | -0.59 |

### Leg correlations: 494 months, worst decile = 49 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.083 | 0.021 |
| equity_carry | 0.023 | 0.124 |
| trend_carry | 0.153 | -0.003 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 9.27 | 15.48 | -8.231 | 0.0 |
| trend | 12.15 | 12.5 | 2.575 | 0.694 |
| carry | 1.64 | 5.95 | -0.185 | 0.469 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 1985-01..2005-07 | 247 | 0.187 | -0.04 | 0.057 | 0.22 | 0.199 | 2.02 | 18.17 | 8.65 |
| panel_second_half | 2005-08..2026-02 | 247 | 0.121 | 0.088 | -0.209 | -0.127 | 0.099 | 1.26 | 6.13 | 9.89 |
| flat_equity_decade | 1999-03..2009-02 | 120 | 0.222 | 0.032 | -0.268 | 0.014 | 0.17 | 4.27 | 16.56 | -4.32 |
| post_2009 | 2009-01..2025-05 | 197 | 0.145 | 0.072 | -0.202 | -0.179 | 0.2 | 0.56 | 3.47 | 13.54 |
| post_publication | 2013-09..2025-05 | 141 | 0.2 | 0.068 | -0.26 | -0.174 | 0.317 | -0.35 | 3.55 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (1 ep.) |
| `stack10` | -0.028 (0.429) | 0.0092 (1.66) | -0.14 (3 ep.) | 0.69 (1 ep.) |
| `sell_equity10` | 0.798 (1.0) | 0.0092 (1.66) | 3.42 (3 ep.) | 3.27 (1 ep.) |
| `replace_trend15` | -0.414 (0.306) | 0.0247 (0.88) | -2.79 (3 ep.) | -2.74 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -37.96 (+0.00) | -46.71 (+0.00) | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `stack10` | n/c | n/c | -37.77 (+0.19) | -46.74 (-0.03) | -18.43 (-0.58) | n/c | n/c | -17.34 (+0.69) |
| `sell_equity10` | n/c | n/c | -33.25 (+4.71) | -42.54 (+4.16) | -16.46 (+1.38) | n/c | n/c | -14.75 (+3.27) |
| `replace_trend15` | n/c | n/c | -41.76 (-3.80) | -49.01 (-2.30) | -20.11 (-2.27) | n/c | n/c | -20.77 (-2.74) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +3.50, +3.33 |
| `stack10` | +0.05 | +0.01 | +3.55, +3.34 |
| `sell_equity10` | -0.84 | -0.84 | +2.65, +2.48 |
| `replace_trend15` | -1.58 | -1.58 | +1.92, +1.75 |

## Panel `commodity_only_recent_gross` (check): 2013-09..2026-02, 150 months, trend `aqr_tsmom`, carry `commodity_only_gross`

commodity_only; recent; gross. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.3702 | 14.2228 | 14.6254 | 0.9331 | -18.48 | 20 | 1.0 | 1.1244 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 15.4361 | 14.2636 | 14.7888 | 0.9274 | -18.66 | 14 | 1.0085 | 1.1339 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 14.2194 | 13.2575 | 13.3721 | 0.9347 | -16.7 | 14 | 0.9083 | 1.0212 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.9859 | 13.7869 | 14.9924 | 0.8851 | -20.48 | 18 | 0.9672 | 1.0875 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.22 [-0.65, +3.25] MDE 3.11 81y `unresolved` | -2.58 [-5.75, +0.62] MDE 5.32 53y `rejected` | +1.40 [-0.45, +3.41] MDE 3.08 60y `unresolved` | +0.64 [-0.87, +2.34] MDE 3.42 273y `unresolved` | -- |
| `stack10` | +1.29 [-0.78, +3.45] MDE 3.35 85y `unresolved` | -3.69 [-7.45, +0.11] MDE 6.40 38y `rejected` | +1.33 [-0.73, +3.48] MDE 3.34 79y `unresolved` | +0.67 [-1.11, +2.69] MDE 3.75 301y `unresolved` | +0.07 [-0.46, +0.57] MDE 0.77 1714y `unresolved` |
| `sell_equity10` | +0.07 [-2.31, +2.42] MDE 3.72 35821y `unresolved` | -3.73 [-7.48, +0.08] MDE 6.40 37y `rejected` | +1.30 [-0.77, +3.47] MDE 3.35 83y `unresolved` | +0.63 [-1.15, +2.67] MDE 3.75 342y `unresolved` | -1.15 [-2.01, -0.20] MDE 1.35 17y `rejected` |
| `replace_trend15` | +0.84 [-0.50, +2.13] MDE 2.11 79y `unresolved` | -2.96 [-5.60, -0.17] MDE 4.39 27y `rejected` | +0.72 [-0.65, +2.04] MDE 2.11 108y `unresolved` | +0.48 [-1.11, +2.00] MDE 2.48 251y `unresolved` | -0.38 [-1.59, +0.78] MDE 1.78 267y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | +1.69 | +0.75 | +0.98 | +0.98 |
| `stack10` | -0.08 | +0.21 | +0.04 | +0.04 |
| `sell_equity10` | -1.27 | -1.03 | -1.15 | -1.15 |
| `replace_trend15` | -0.83 | +0.07 | -0.31 | -0.31 |

### Leg correlations: 150 months, worst decile = 15 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.262 | -0.519 |
| equity_carry | 0.079 | 0.259 |
| trend_carry | 0.188 | -0.168 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 12.46 | 14.84 | -7.557 | 0.0 |
| trend | 4.34 | 13.32 | 2.203 | 0.6 |
| carry | 1.77 | 9.74 | -0.614 | 0.533 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 2013-09..2019-11 | 75 | 0.127 | 0.144 | -0.164 | -0.396 | -0.092 | 0.36 | 5.92 | 12.22 |
| panel_second_half | 2019-12..2026-02 | 75 | 0.242 | 0.044 | -0.337 | -0.295 | 0.428 | 3.19 | 2.75 | 12.71 |
| post_2009 | 2013-09..2025-05 | 141 | 0.2 | 0.068 | -0.26 | -0.174 | 0.317 | 1.48 | 3.55 | 12.12 |
| post_publication | 2013-09..2025-05 | 141 | 0.2 | 0.068 | -0.26 | -0.174 | 0.317 | 1.48 | 3.55 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (1 ep.) | 0.0 (1 ep.) |
| `stack10` | -0.071 (0.533) | 0.0197 (0.91) | -0.82 (1 ep.) | 1.17 (1 ep.) |
| `sell_equity10` | 0.687 (0.933) | 0.0197 (0.91) | 1.15 (1 ep.) | 3.77 (1 ep.) |
| `replace_trend15` | -0.423 (0.467) | 0.0202 (0.38) | -2.62 (1 ep.) | -2.04 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | n/c | n/c | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `stack10` | n/c | n/c | n/c | n/c | -18.66 (-0.82) | n/c | n/c | -16.85 (+1.17) |
| `sell_equity10` | n/c | n/c | n/c | n/c | -16.7 (+1.15) | n/c | n/c | -14.26 (+3.77) |
| `replace_trend15` | n/c | n/c | n/c | n/c | -20.46 (-2.62) | n/c | n/c | -20.07 (-2.04) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +1.22, +1.05 |
| `stack10` | +0.07 | +0.02 | +1.29, +1.08 |
| `sell_equity10` | -1.15 | -1.15 | +0.07, -0.10 |
| `replace_trend15` | -0.38 | -0.38 | +0.84, +0.67 |

## Panel `commodity_only_recent_costed` (sensitivity): 2013-09..2026-02, 150 months, trend `aqr_tsmom`, carry `commodity_only_costed`

commodity_only; recent; costed. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.3702 | 14.2228 | 14.6254 | 0.9331 | -18.48 | 20 | 1.0 | 1.1244 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 15.2361 | 14.0658 | 14.7888 | 0.9139 | -18.69 | 14 | 0.9876 | 1.1104 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 14.0194 | 13.0595 | 13.3721 | 0.9197 | -16.73 | 14 | 0.8896 | 1.0003 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.6859 | 13.49 | 14.9924 | 0.8651 | -20.55 | 18 | 0.9375 | 1.0541 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.22 [-0.66, +3.35] MDE 3.11 81y `unresolved` | -2.58 [-5.53, +0.69] MDE 5.32 53y `rejected` | +1.40 [-0.46, +3.50] MDE 3.08 60y `unresolved` | +0.64 [-0.81, +2.29] MDE 3.42 273y `unresolved` | -- |
| `stack10` | +1.09 [-1.02, +3.34] MDE 3.35 119y `unresolved` | -3.89 [-7.48, -0.03] MDE 6.40 34y `rejected` | +1.13 [-0.97, +3.39] MDE 3.34 109y `unresolved` | +0.47 [-1.29, +2.43] MDE 3.75 616y `unresolved` | -0.13 [-0.70, +0.38] MDE 0.77 414y `rejected` |
| `sell_equity10` | -0.13 [-2.47, +2.37] MDE 3.72 10128y `rejected` | -3.93 [-7.52, -0.06] MDE 6.40 33y `rejected` | +1.10 [-1.00, +3.36] MDE 3.35 115y `unresolved` | +0.43 [-1.33, +2.40] MDE 3.75 739y `unresolved` | -1.35 [-2.23, -0.44] MDE 1.35 13y `rejected` |
| `replace_trend15` | +0.54 [-0.79, +1.88] MDE 2.11 193y `unresolved` | -3.26 [-5.83, -0.57] MDE 4.39 23y `rejected` | +0.42 [-0.94, +1.79] MDE 2.11 319y `unresolved` | +0.18 [-1.28, +1.66] MDE 2.48 1758y `unresolved` | -0.68 [-1.95, +0.46] MDE 1.78 84y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | +1.69 | +0.75 | +0.98 | +0.98 |
| `stack10` | -0.28 | +0.01 | -0.16 | -0.16 |
| `sell_equity10` | -1.47 | -1.23 | -1.35 | -1.35 |
| `replace_trend15` | -1.13 | -0.23 | -0.61 | -0.61 |

### Leg correlations: 150 months, worst decile = 15 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.262 | -0.519 |
| equity_carry | 0.079 | 0.259 |
| trend_carry | 0.188 | -0.168 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 12.46 | 14.84 | -7.557 | 0.0 |
| trend | 4.34 | 13.32 | 2.203 | 0.6 |
| carry | -0.23 | 9.74 | -0.781 | 0.533 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 2013-09..2019-11 | 75 | 0.127 | 0.144 | -0.164 | -0.396 | -0.092 | -1.64 | 5.92 | 12.22 |
| panel_second_half | 2019-12..2026-02 | 75 | 0.242 | 0.044 | -0.337 | -0.295 | 0.428 | 1.19 | 2.75 | 12.71 |
| post_2009 | 2013-09..2025-05 | 141 | 0.2 | 0.068 | -0.26 | -0.174 | 0.317 | -0.52 | 3.55 | 12.12 |
| post_publication | 2013-09..2025-05 | 141 | 0.2 | 0.068 | -0.26 | -0.174 | 0.317 | -0.52 | 3.55 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (1 ep.) | 0.0 (1 ep.) |
| `stack10` | -0.087 (0.467) | 0.0197 (0.91) | -0.85 (1 ep.) | 1.05 (1 ep.) |
| `sell_equity10` | 0.671 (0.933) | 0.0197 (0.91) | 1.11 (1 ep.) | 3.64 (1 ep.) |
| `replace_trend15` | -0.448 (0.467) | 0.0202 (0.38) | -2.67 (1 ep.) | -2.22 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | n/c | n/c | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `stack10` | n/c | n/c | n/c | n/c | -18.69 (-0.85) | n/c | n/c | -16.98 (+1.05) |
| `sell_equity10` | n/c | n/c | n/c | n/c | -16.73 (+1.11) | n/c | n/c | -14.39 (+3.64) |
| `replace_trend15` | n/c | n/c | n/c | n/c | -20.51 (-2.67) | n/c | n/c | -20.25 (-2.22) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +1.22, +1.05 |
| `stack10` | -0.13 | -0.18 | +1.09, +0.88 |
| `sell_equity10` | -1.35 | -1.35 | -0.13, -0.30 |
| `replace_trend15` | -0.68 | -0.68 | +0.54, +0.37 |

## Panel `commodity_only_recent_costed_loading` (sensitivity): 2013-09..2026-02, 150 months, trend `aqr_tsmom`, carry `commodity_only_costed_loading`

commodity_only; recent; costed_loading. Same window across definitions. Sensitivity is charged inside monthly returns.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | carry | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.3702 | 14.2228 | 14.6254 | 0.9331 | -18.48 | 20 | 1.0 | 1.1244 |
| `stack10` | 1.422 | 1.022 | 0.300 | 0.100 | 0.000 | 15.2433 | 14.0817 | 14.7299 | 0.918 | -18.43 | 14 | 0.988 | 1.1108 |
| `sell_equity10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 14.0266 | 13.0751 | 13.3097 | 0.9245 | -16.46 | 14 | 0.8898 | 1.0005 |
| `replace_trend15` | 1.322 | 1.022 | 0.150 | 0.150 | 0.000 | 14.6967 | 13.5142 | 14.9041 | 0.8709 | -20.77 | 18 | 0.938 | 1.0546 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.22 [-0.62, +3.32] MDE 3.11 81y `unresolved` | -2.58 [-5.70, +0.66] MDE 5.32 53y `rejected` | +1.40 [-0.40, +3.47] MDE 3.08 60y `unresolved` | +0.64 [-0.89, +2.35] MDE 3.42 273y `unresolved` | -- |
| `stack10` | +1.09 [-0.93, +3.25] MDE 3.26 111y `unresolved` | -3.89 [-7.55, -0.03] MDE 6.36 34y `rejected` | +1.19 [-0.80, +3.33] MDE 3.24 93y `unresolved` | +0.49 [-1.18, +2.49] MDE 3.62 518y `unresolved` | -0.13 [-0.49, +0.22] MDE 0.53 215y `rejected` |
| `sell_equity10` | -0.12 [-2.44, +2.33] MDE 3.64 10872y `rejected` | -3.92 [-7.59, -0.07] MDE 6.36 33y `rejected` | +1.16 [-0.85, +3.31] MDE 3.25 98y `unresolved` | +0.45 [-1.22, +2.48] MDE 3.62 607y `unresolved` | -1.34 [-2.07, -0.57] MDE 1.25 11y `rejected` |
| `replace_trend15` | +0.55 [-0.62, +1.71] MDE 1.87 146y `unresolved` | -3.25 [-5.68, -0.66] MDE 4.31 22y `rejected` | +0.50 [-0.68, +1.69] MDE 1.87 175y `unresolved` | +0.22 [-0.91, +1.50] MDE 2.15 932y `unresolved` | -0.67 [-1.80, +0.30] MDE 1.63 73y `rejected` |

### Era gaps against the reference arm, pp/yr (descriptive; the trend leg cancels)

| arm | panel_first_half | panel_second_half | post_2009 | post_publication |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | +1.69 | +0.75 | +0.98 | +0.98 |
| `stack10` | -0.22 | -0.03 | -0.15 | -0.15 |
| `sell_equity10` | -1.42 | -1.27 | -1.33 | -1.33 |
| `replace_trend15` | -1.06 | -0.29 | -0.59 | -0.59 |

### Leg correlations: 150 months, worst decile = 15 months (descriptive)

| pair | full sample | worst decile of equity months |
| --- | ---: | ---: |
| equity_trend | -0.262 | -0.519 |
| equity_carry | 0.079 | 0.259 |
| trend_carry | 0.188 | -0.168 |

| leg | mean excess pp/yr | vol % | worst-decile mean pp/month | worst-decile hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 12.46 | 14.84 | -7.557 | 0.0 |
| trend | 4.34 | 13.32 | 2.203 | 0.6 |
| carry | -0.15 | 6.63 | -0.532 | 0.533 |

### Correlations and leg means by era (descriptive)

| era | window | months | carry-trend | carry-equity | trend-equity | carry-trend (worst decile) | carry-equity (worst decile) | carry pp/yr | trend pp/yr | equity pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_first_half | 2013-09..2019-11 | 75 | 0.127 | 0.144 | -0.164 | -0.396 | -0.092 | -1.11 | 5.92 | 12.22 |
| panel_second_half | 2019-12..2026-02 | 75 | 0.242 | 0.044 | -0.337 | -0.295 | 0.428 | 0.81 | 2.75 | 12.71 |
| post_2009 | 2013-09..2025-05 | 141 | 0.2 | 0.068 | -0.26 | -0.174 | 0.317 | -0.35 | 3.55 | 12.12 |
| post_publication | 2013-09..2025-05 | 141 | 0.2 | 0.068 | -0.26 | -0.174 | 0.317 | -0.35 | 3.55 | 12.12 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp |
| --- | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (1 ep.) | 0.0 (1 ep.) |
| `stack10` | -0.062 (0.4) | 0.0134 (0.91) | -0.58 (1 ep.) | 0.69 (1 ep.) |
| `sell_equity10` | 0.696 (1.0) | 0.0134 (0.91) | 1.38 (1 ep.) | 3.27 (1 ep.) |
| `replace_trend15` | -0.41 (0.333) | 0.0107 (0.24) | -2.27 (1 ep.) | -2.74 (1 ep.) |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | n/c | n/c | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `stack10` | n/c | n/c | n/c | n/c | -18.43 (-0.58) | n/c | n/c | -17.34 (+0.69) |
| `sell_equity10` | n/c | n/c | n/c | n/c | -16.46 (+1.38) | n/c | n/c | -14.75 (+3.27) |
| `replace_trend15` | n/c | n/c | n/c | n/c | -20.11 (-2.27) | n/c | n/c | -20.77 (-2.74) |

### Financing sensitivity: gap against the reference arm at each equity basis (pp/yr), then against the cheap control


equity basis, bp: 62, 231
ordering against reference stable across the band: `True`

| arm | 62 | 231 | vs cheap at each point |
| --- | ---: | ---: | --- |
| `base_trend30` | -- | -- | +1.22, +1.05 |
| `stack10` | -0.13 | -0.17 | +1.09, +0.88 |
| `sell_equity10` | -1.34 | -1.34 | -0.12, -0.29 |
| `replace_trend15` | -0.67 | -0.67 | +0.55, +0.38 |

## Paired growth and historical ten-year outcomes

| panel | arm | comparator | arithmetic gap, pp/yr | MDE | log gap [95%], pp/yr | losing 10-year windows | worst 10-year shortfall |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: |
| all_macro_primary_gross | stack10 | reference | +0.673 | 0.463 | +0.638 [+0.272, +1.027] | 13.7% | -6.23% |
| all_macro_primary_gross | stack10 | cheap | +2.671 | 1.646 | +2.513 [+1.484, +3.607] | 8.2% | -7.81% |
| all_macro_primary_gross | sell_equity10 | reference | -0.096 | 0.742 | +0.122 [-0.459, +0.707] | 33.0% | -15.72% |
| all_macro_primary_gross | sell_equity10 | cheap | +1.902 | 1.723 | +1.997 [+0.842, +3.207] | 16.1% | -15.29% |
| all_macro_primary_gross | replace_trend15 | reference | +0.089 | 1.003 | +0.086 [-0.658, +0.810] | 54.3% | -8.63% |
| all_macro_primary_gross | replace_trend15 | cheap | +2.087 | 1.086 | +1.961 [+1.190, +2.727] | 10.9% | -8.13% |
| all_macro_primary_costed | stack10 | reference | +0.473 | 0.463 | +0.440 [+0.065, +0.797] | 21.5% | -8.08% |
| all_macro_primary_costed | stack10 | cheap | +2.471 | 1.646 | +2.315 [+1.218, +3.329] | 11.5% | -9.62% |
| all_macro_primary_costed | sell_equity10 | reference | -0.296 | 0.742 | -0.076 [-0.657, +0.515] | 46.3% | -17.37% |
| all_macro_primary_costed | sell_equity10 | cheap | +1.702 | 1.723 | +1.799 [+0.684, +2.961] | 16.7% | -16.95% |
| all_macro_primary_costed | replace_trend15 | reference | -0.211 | 1.003 | -0.211 [-0.959, +0.530] | 71.2% | -11.31% |
| all_macro_primary_costed | replace_trend15 | cheap | +1.787 | 1.086 | +1.664 [+0.910, +2.409] | 12.9% | -10.82% |
| all_macro_primary_costed_loading | stack10 | reference | +0.286 | 0.316 | +0.266 [+0.027, +0.512] | 22.1% | -5.90% |
| all_macro_primary_costed_loading | stack10 | cheap | +2.285 | 1.600 | +2.141 [+1.147, +3.170] | 10.9% | -8.04% |
| all_macro_primary_costed_loading | sell_equity10 | reference | -0.483 | 0.672 | -0.251 [-0.753, +0.276] | 65.8% | -16.18% |
| all_macro_primary_costed_loading | sell_equity10 | cheap | +1.516 | 1.684 | +1.625 [+0.559, +2.719] | 16.7% | -15.50% |
| all_macro_primary_costed_loading | replace_trend15 | reference | -0.491 | 0.878 | -0.470 [-1.078, +0.137] | 84.1% | -12.39% |
| all_macro_primary_costed_loading | replace_trend15 | cheap | +1.507 | 0.944 | +1.405 [+0.832, +2.058] | 11.9% | -7.68% |
| all_macro_secondary_gross | stack10 | reference | +0.534 | 0.514 | +0.487 [+0.119, +0.877] | 20.5% | -6.23% |
| all_macro_secondary_gross | stack10 | cheap | +4.030 | 1.767 | +3.872 [+2.602, +5.205] | 3.7% | -4.07% |
| all_macro_secondary_gross | sell_equity10 | reference | -0.363 | 0.785 | -0.166 [-0.783, +0.471] | 43.7% | -15.79% |
| all_macro_secondary_gross | sell_equity10 | cheap | +3.132 | 1.860 | +3.219 [+1.692, +4.766] | 12.8% | -12.89% |
| all_macro_secondary_gross | replace_trend15 | reference | -0.854 | 1.067 | -0.879 [-1.506, -0.216] | 99.7% | -14.66% |
| all_macro_secondary_gross | replace_trend15 | cheap | +2.642 | 1.196 | +2.506 [+1.584, +3.441] | 6.1% | -5.03% |
| all_macro_secondary_costed | stack10 | reference | +0.334 | 0.514 | +0.290 [-0.092, +0.665] | 30.9% | -8.07% |
| all_macro_secondary_costed | stack10 | cheap | +3.830 | 1.767 | +3.674 [+2.305, +4.951] | 3.7% | -5.95% |
| all_macro_secondary_costed | sell_equity10 | reference | -0.563 | 0.785 | -0.363 [-0.946, +0.302] | 54.1% | -17.44% |
| all_macro_secondary_costed | sell_equity10 | cheap | +2.932 | 1.860 | +3.021 [+1.557, +4.454] | 16.3% | -14.60% |
| all_macro_secondary_costed | replace_trend15 | reference | -1.154 | 1.067 | -1.176 [-1.832, -0.553] | 100.0% | -17.16% |
| all_macro_secondary_costed | replace_trend15 | cheap | +2.342 | 1.196 | +2.209 [+1.246, +3.159] | 12.5% | -7.82% |
| all_macro_secondary_costed_loading | stack10 | reference | +0.192 | 0.350 | +0.164 [-0.086, +0.416] | 31.7% | -5.89% |
| all_macro_secondary_costed_loading | stack10 | cheap | +3.687 | 1.708 | +3.548 [+2.294, +4.809] | 3.7% | -4.49% |
| all_macro_secondary_costed_loading | sell_equity10 | reference | -0.705 | 0.712 | -0.490 [-1.035, +0.119] | 67.2% | -16.26% |
| all_macro_secondary_costed_loading | sell_equity10 | cheap | +2.790 | 1.814 | +2.894 [+1.476, +4.294] | 13.6% | -13.33% |
| all_macro_secondary_costed_loading | replace_trend15 | reference | -1.367 | 0.927 | -1.363 [-1.926, -0.801] | 100.0% | -18.88% |
| all_macro_secondary_costed_loading | replace_trend15 | cheap | +2.128 | 1.029 | +2.021 [+1.223, +2.810] | 6.4% | -5.40% |
| all_macro_recent_gross | stack10 | reference | -0.315 | 0.854 | -0.347 [-0.853, +0.151] | 100.0% | -4.65% |
| all_macro_recent_gross | stack10 | cheap | +0.905 | 3.281 | +0.893 [-1.136, +3.031] | 45.2% | -4.07% |
| all_macro_recent_gross | sell_equity10 | reference | -1.532 | 1.339 | -1.352 [-2.110, -0.603] | 100.0% | -13.22% |
| all_macro_recent_gross | sell_equity10 | cheap | -0.312 | 3.632 | -0.112 [-2.335, +2.352] | 77.4% | -12.89% |
| all_macro_recent_gross | replace_trend15 | reference | -0.956 | 1.981 | -1.023 [-2.347, +0.176] | 100.0% | -12.26% |
| all_macro_recent_gross | replace_trend15 | cheap | +0.264 | 2.080 | +0.218 [-1.056, +1.457] | 64.5% | -5.03% |
| all_macro_recent_costed | stack10 | reference | -0.515 | 0.854 | -0.545 [-1.061, -0.042] | 100.0% | -6.52% |
| all_macro_recent_costed | stack10 | cheap | +0.705 | 3.281 | +0.695 [-1.349, +2.817] | 45.2% | -5.95% |
| all_macro_recent_costed | sell_equity10 | reference | -1.732 | 1.339 | -1.550 [-2.349, -0.761] | 100.0% | -14.93% |
| all_macro_recent_costed | sell_equity10 | cheap | -0.512 | 3.632 | -0.310 [-2.486, +2.006] | 93.5% | -14.60% |
| all_macro_recent_costed | replace_trend15 | reference | -1.256 | 1.981 | -1.320 [-2.607, -0.188] | 100.0% | -14.83% |
| all_macro_recent_costed | replace_trend15 | cheap | -0.036 | 2.080 | -0.079 [-1.332, +1.146] | 100.0% | -7.82% |
| all_macro_recent_costed_loading | stack10 | reference | -0.386 | 0.581 | -0.405 [-0.738, -0.069] | 100.0% | -4.81% |
| all_macro_recent_costed_loading | stack10 | cheap | +0.834 | 3.203 | +0.835 [-1.011, +2.907] | 45.2% | -4.49% |
| all_macro_recent_costed_loading | sell_equity10 | reference | -1.603 | 1.226 | -1.411 [-2.070, -0.748] | 100.0% | -13.69% |
| all_macro_recent_costed_loading | sell_equity10 | cheap | -0.383 | 3.575 | -0.171 [-2.457, +2.205] | 77.4% | -13.33% |
| all_macro_recent_costed_loading | replace_trend15 | reference | -1.063 | 1.766 | -1.108 [-2.286, -0.062] | 100.0% | -12.65% |
| all_macro_recent_costed_loading | replace_trend15 | cheap | +0.158 | 1.828 | +0.133 [-0.952, +1.228] | 64.5% | -5.40% |
| bond_commodity_primary_gross | stack10 | reference | +0.842 | 0.701 | +0.825 [+0.359, +1.305] | 1.6% | -4.03% |
| bond_commodity_primary_gross | stack10 | cheap | +2.841 | 1.764 | +2.700 [+1.571, +3.786] | 1.2% | -7.43% |
| bond_commodity_primary_gross | sell_equity10 | reference | +0.073 | 0.960 | +0.306 [-0.363, +0.985] | 32.8% | -11.83% |
| bond_commodity_primary_gross | sell_equity10 | cheap | +2.072 | 1.861 | +2.181 [+1.001, +3.443] | 14.1% | -14.96% |
| bond_commodity_primary_gross | replace_trend15 | reference | +0.343 | 1.232 | +0.364 [-0.461, +1.193] | 32.8% | -9.59% |
| bond_commodity_primary_gross | replace_trend15 | cheap | +2.341 | 1.371 | +2.239 [+1.374, +3.145] | 0.2% | -6.95% |
| bond_commodity_primary_costed | stack10 | reference | +0.642 | 0.701 | +0.627 [+0.162, +1.114] | 5.8% | -5.91% |
| bond_commodity_primary_costed | stack10 | cheap | +2.641 | 1.764 | +2.502 [+1.354, +3.638] | 2.0% | -9.25% |
| bond_commodity_primary_costed | sell_equity10 | reference | -0.127 | 0.960 | +0.108 [-0.538, +0.807] | 42.7% | -13.56% |
| bond_commodity_primary_costed | sell_equity10 | cheap | +1.872 | 1.861 | +1.983 [+0.760, +3.252] | 15.3% | -16.63% |
| bond_commodity_primary_costed | replace_trend15 | reference | +0.043 | 1.232 | +0.067 [-0.756, +0.937] | 53.3% | -12.25% |
| bond_commodity_primary_costed | replace_trend15 | cheap | +2.041 | 1.371 | +1.942 [+1.083, +2.859] | 2.8% | -9.68% |
| bond_commodity_primary_costed_loading | stack10 | reference | +0.402 | 0.477 | +0.395 [+0.077, +0.726] | 6.4% | -4.35% |
| bond_commodity_primary_costed_loading | stack10 | cheap | +2.400 | 1.665 | +2.270 [+1.199, +3.297] | 1.6% | -7.74% |
| bond_commodity_primary_costed_loading | sell_equity10 | reference | -0.367 | 0.802 | -0.123 [-0.678, +0.457] | 66.8% | -12.13% |
| bond_commodity_primary_costed_loading | sell_equity10 | cheap | +1.631 | 1.764 | +1.752 [+0.566, +2.921] | 15.9% | -15.25% |
| bond_commodity_primary_costed_loading | replace_trend15 | reference | -0.318 | 0.992 | -0.276 [-0.940, +0.411] | 72.4% | -13.85% |
| bond_commodity_primary_costed_loading | replace_trend15 | cheap | +1.681 | 1.110 | +1.599 [+0.891, +2.318] | 2.4% | -7.31% |
| bond_commodity_secondary_gross | stack10 | reference | +0.502 | 0.766 | +0.475 [-0.003, +0.932] | 4.5% | -6.09% |
| bond_commodity_secondary_gross | stack10 | cheap | +3.998 | 1.873 | +3.859 [+2.427, +5.244] | 2.7% | -4.84% |
| bond_commodity_secondary_gross | sell_equity10 | reference | -0.395 | 1.018 | -0.181 [-0.906, +0.543] | 44.8% | -15.80% |
| bond_commodity_secondary_gross | sell_equity10 | cheap | +3.100 | 1.986 | +3.203 [+1.632, +4.669] | 5.1% | -14.11% |
| bond_commodity_secondary_gross | replace_trend15 | reference | -0.902 | 1.341 | -0.903 [-1.651, -0.151] | 82.9% | -17.99% |
| bond_commodity_secondary_gross | replace_trend15 | cheap | +2.593 | 1.478 | +2.482 [+1.477, +3.522] | 2.7% | -7.09% |
| bond_commodity_secondary_costed | stack10 | reference | +0.302 | 0.766 | +0.277 [-0.208, +0.744] | 10.1% | -7.93% |
| bond_commodity_secondary_costed | stack10 | cheap | +3.798 | 1.873 | +3.662 [+2.323, +4.952] | 2.9% | -6.71% |
| bond_commodity_secondary_costed | sell_equity10 | reference | -0.595 | 1.018 | -0.379 [-1.114, +0.277] | 55.2% | -17.45% |
| bond_commodity_secondary_costed | sell_equity10 | cheap | +2.900 | 1.986 | +3.006 [+1.503, +4.526] | 7.2% | -15.79% |
| bond_commodity_secondary_costed | replace_trend15 | reference | -1.202 | 1.341 | -1.200 [-1.914, -0.481] | 96.5% | -20.38% |
| bond_commodity_secondary_costed | replace_trend15 | cheap | +2.293 | 1.478 | +2.185 [+1.099, +3.199] | 2.7% | -9.81% |
| bond_commodity_secondary_costed_loading | stack10 | reference | +0.170 | 0.521 | +0.157 [-0.161, +0.477] | 10.9% | -5.75% |
| bond_commodity_secondary_costed_loading | stack10 | cheap | +3.666 | 1.764 | +3.541 [+2.289, +4.831] | 2.9% | -4.89% |
| bond_commodity_secondary_costed_loading | sell_equity10 | reference | -0.727 | 0.851 | -0.499 [-1.082, +0.121] | 76.5% | -15.50% |
| bond_commodity_secondary_costed_loading | sell_equity10 | cheap | +2.768 | 1.884 | +2.885 [+1.509, +4.343] | 8.0% | -14.07% |
| bond_commodity_secondary_costed_loading | replace_trend15 | reference | -1.400 | 1.073 | -1.376 [-2.010, -0.780] | 98.7% | -21.72% |
| bond_commodity_secondary_costed_loading | replace_trend15 | cheap | +2.096 | 1.190 | +2.009 [+1.165, +2.818] | 2.7% | -6.48% |
| bond_commodity_recent_gross | stack10 | reference | -0.238 | 1.676 | -0.259 [-1.277, +0.630] | 54.8% | -6.09% |
| bond_commodity_recent_gross | stack10 | cheap | +0.982 | 3.560 | +0.982 [-1.282, +3.703] | 32.3% | -4.84% |
| bond_commodity_recent_gross | sell_equity10 | reference | -1.455 | 2.053 | -1.266 [-2.548, -0.138] | 100.0% | -15.80% |
| bond_commodity_recent_gross | sell_equity10 | cheap | -0.235 | 3.929 | -0.026 [-2.611, +2.585] | 58.1% | -14.11% |
| bond_commodity_recent_gross | replace_trend15 | reference | -0.840 | 2.947 | -0.903 [-2.516, +0.794] | 87.1% | -8.92% |
| bond_commodity_recent_gross | replace_trend15 | cheap | +0.380 | 2.971 | +0.337 [-1.568, +2.127] | 32.3% | -7.09% |
| bond_commodity_recent_costed | stack10 | reference | -0.438 | 1.676 | -0.457 [-1.491, +0.408] | 96.8% | -7.93% |
| bond_commodity_recent_costed | stack10 | cheap | +0.782 | 3.560 | +0.784 [-1.399, +3.163] | 35.5% | -6.71% |
| bond_commodity_recent_costed | sell_equity10 | reference | -1.655 | 2.053 | -1.464 [-2.719, -0.365] | 100.0% | -17.45% |
| bond_commodity_recent_costed | sell_equity10 | cheap | -0.435 | 3.929 | -0.224 [-2.900, +2.423] | 64.5% | -15.79% |
| bond_commodity_recent_costed | replace_trend15 | reference | -1.140 | 2.947 | -1.200 [-2.786, +0.248] | 100.0% | -11.59% |
| bond_commodity_recent_costed | replace_trend15 | cheap | +0.080 | 2.971 | +0.040 [-1.861, +1.830] | 32.3% | -9.81% |
| bond_commodity_recent_costed_loading | stack10 | reference | -0.334 | 1.142 | -0.341 [-1.033, +0.251] | 100.0% | -5.75% |
| bond_commodity_recent_costed_loading | stack10 | cheap | +0.886 | 3.333 | +0.899 [-1.240, +3.288] | 35.5% | -4.89% |
| bond_commodity_recent_costed_loading | sell_equity10 | reference | -1.551 | 1.643 | -1.349 [-2.303, -0.465] | 100.0% | -15.50% |
| bond_commodity_recent_costed_loading | sell_equity10 | cheap | -0.330 | 3.723 | -0.108 [-2.446, +2.419] | 61.3% | -14.07% |
| bond_commodity_recent_costed_loading | replace_trend15 | reference | -0.984 | 2.311 | -1.018 [-2.353, +0.190] | 100.0% | -9.03% |
| bond_commodity_recent_costed_loading | replace_trend15 | cheap | +0.236 | 2.321 | +0.222 [-1.259, +1.615] | 32.3% | -6.48% |
| commodity_only_primary_gross | stack10 | reference | +0.393 | 0.350 | +0.390 [+0.111, +0.661] | 13.3% | -2.24% |
| commodity_only_primary_gross | stack10 | cheap | +2.392 | 1.591 | +2.265 [+1.218, +3.325] | 1.6% | -3.51% |
| commodity_only_primary_gross | sell_equity10 | reference | -0.376 | 0.726 | -0.128 [-0.668, +0.446] | 67.2% | -14.46% |
| commodity_only_primary_gross | sell_equity10 | cheap | +1.622 | 1.691 | +1.747 [+0.627, +2.860] | 16.1% | -13.14% |
| commodity_only_primary_gross | replace_trend15 | reference | -0.331 | 0.923 | -0.285 [-0.941, +0.350] | 93.8% | -14.38% |
| commodity_only_primary_gross | replace_trend15 | cheap | +1.668 | 0.946 | +1.590 [+0.953, +2.206] | 0.8% | -0.56% |
| commodity_only_primary_costed | stack10 | reference | +0.193 | 0.350 | +0.192 [-0.091, +0.477] | 36.6% | -4.16% |
| commodity_only_primary_costed | stack10 | cheap | +2.192 | 1.591 | +2.067 [+1.050, +3.026] | 8.2% | -5.41% |
| commodity_only_primary_costed | sell_equity10 | reference | -0.576 | 0.726 | -0.326 [-0.904, +0.237] | 75.9% | -16.14% |
| commodity_only_primary_costed | sell_equity10 | cheap | +1.422 | 1.691 | +1.549 [+0.461, +2.670] | 16.3% | -14.84% |
| commodity_only_primary_costed | replace_trend15 | reference | -0.631 | 0.923 | -0.582 [-1.199, +0.050] | 98.2% | -16.88% |
| commodity_only_primary_costed | replace_trend15 | cheap | +1.368 | 0.946 | +1.293 [+0.631, +1.959] | 10.9% | -3.46% |
| commodity_only_primary_costed_loading | stack10 | reference | +0.096 | 0.238 | +0.096 [-0.090, +0.280] | 42.9% | -3.18% |
| commodity_only_primary_costed_loading | stack10 | cheap | +2.094 | 1.568 | +1.971 [+1.029, +2.977] | 4.8% | -5.42% |
| commodity_only_primary_costed_loading | sell_equity10 | reference | -0.673 | 0.675 | -0.422 [-0.883, +0.083] | 82.9% | -15.37% |
| commodity_only_primary_costed_loading | sell_equity10 | cheap | +1.325 | 1.667 | +1.453 [+0.399, +2.494] | 16.3% | -15.10% |
| commodity_only_primary_costed_loading | replace_trend15 | reference | -0.776 | 0.843 | -0.724 [-1.287, -0.161] | 98.2% | -15.85% |
| commodity_only_primary_costed_loading | replace_trend15 | cheap | +1.222 | 0.861 | +1.151 [+0.573, +1.704] | 9.5% | -2.84% |
| commodity_only_secondary_gross | stack10 | reference | +0.329 | 0.382 | +0.313 [+0.051, +0.562] | 13.3% | -2.27% |
| commodity_only_secondary_gross | stack10 | cheap | +3.825 | 1.733 | +3.698 [+2.506, +4.888] | 0.0% | 0.00% |
| commodity_only_secondary_gross | sell_equity10 | reference | -0.568 | 0.768 | -0.343 [-0.869, +0.256] | 62.1% | -14.60% |
| commodity_only_secondary_gross | sell_equity10 | cheap | +2.927 | 1.854 | +3.042 [+1.620, +4.402] | 9.1% | -8.69% |
| commodity_only_secondary_gross | replace_trend15 | reference | -1.161 | 0.925 | -1.138 [-1.744, -0.560] | 96.3% | -19.77% |
| commodity_only_secondary_gross | replace_trend15 | cheap | +2.334 | 1.071 | +2.247 [+1.515, +2.973] | 0.0% | 0.00% |
| commodity_only_secondary_costed | stack10 | reference | +0.129 | 0.382 | +0.115 [-0.148, +0.362] | 32.5% | -4.18% |
| commodity_only_secondary_costed | stack10 | cheap | +3.625 | 1.733 | +3.500 [+2.274, +4.719] | 1.1% | -0.93% |
| commodity_only_secondary_costed | sell_equity10 | reference | -0.768 | 0.768 | -0.541 [-1.084, +0.072] | 70.7% | -16.27% |
| commodity_only_secondary_costed | sell_equity10 | cheap | +2.727 | 1.854 | +2.844 [+1.454, +4.168] | 10.4% | -10.48% |
| commodity_only_secondary_costed | replace_trend15 | reference | -1.461 | 0.925 | -1.435 [-2.039, -0.813] | 99.5% | -22.11% |
| commodity_only_secondary_costed | replace_trend15 | cheap | +2.034 | 1.071 | +1.950 [+1.198, +2.643] | 1.3% | -0.27% |
| commodity_only_secondary_costed_loading | stack10 | reference | +0.052 | 0.260 | +0.044 [-0.127, +0.220] | 35.7% | -3.20% |
| commodity_only_secondary_costed_loading | stack10 | cheap | +3.548 | 1.692 | +3.429 [+2.172, +4.613] | 1.3% | -0.96% |
| commodity_only_secondary_costed_loading | sell_equity10 | reference | -0.845 | 0.718 | -0.612 [-1.143, -0.066] | 78.4% | -15.50% |
| commodity_only_secondary_costed_loading | sell_equity10 | cheap | +2.650 | 1.816 | +2.773 [+1.481, +4.084] | 10.4% | -10.51% |
| commodity_only_secondary_costed_loading | replace_trend15 | reference | -1.577 | 0.852 | -1.541 [-2.128, -0.949] | 99.7% | -21.99% |
| commodity_only_secondary_costed_loading | replace_trend15 | cheap | +1.919 | 0.962 | +1.843 [+1.174, +2.508] | 0.8% | -0.28% |
| commodity_only_recent_gross | stack10 | reference | +0.066 | 0.772 | +0.041 [-0.477, +0.585] | 35.5% | -1.02% |
| commodity_only_recent_gross | stack10 | cheap | +1.286 | 3.349 | +1.281 [-0.749, +3.406] | 0.0% | 0.00% |
| commodity_only_recent_gross | sell_equity10 | reference | -1.151 | 1.354 | -0.965 [-1.833, -0.085] | 100.0% | -9.93% |
| commodity_only_recent_gross | sell_equity10 | cheap | +0.069 | 3.717 | +0.275 [-2.004, +2.672] | 51.6% | -8.69% |
| commodity_only_recent_gross | replace_trend15 | reference | -0.384 | 1.777 | -0.436 [-1.674, +0.709] | 54.8% | -7.40% |
| commodity_only_recent_gross | replace_trend15 | cheap | +0.836 | 2.106 | +0.804 [-0.493, +2.120] | 0.0% | 0.00% |
| commodity_only_recent_costed | stack10 | reference | -0.134 | 0.772 | -0.157 [-0.644, +0.360] | 100.0% | -2.96% |
| commodity_only_recent_costed | stack10 | cheap | +1.086 | 3.349 | +1.083 [-0.899, +3.283] | 12.9% | -0.93% |
| commodity_only_recent_costed | sell_equity10 | reference | -1.351 | 1.354 | -1.163 [-2.060, -0.281] | 100.0% | -11.69% |
| commodity_only_recent_costed | sell_equity10 | cheap | -0.131 | 3.717 | +0.077 [-2.153, +2.365] | 61.3% | -10.48% |
| commodity_only_recent_costed | replace_trend15 | reference | -0.684 | 1.777 | -0.733 [-1.942, +0.445] | 93.5% | -10.11% |
| commodity_only_recent_costed | replace_trend15 | cheap | +0.536 | 2.106 | +0.507 [-0.800, +1.828] | 12.9% | -0.27% |
| commodity_only_recent_costed_loading | stack10 | reference | -0.127 | 0.526 | -0.141 [-0.500, +0.201] | 100.0% | -2.36% |
| commodity_only_recent_costed_loading | stack10 | cheap | +1.093 | 3.255 | +1.099 [-0.796, +3.154] | 16.1% | -0.96% |
| commodity_only_recent_costed_loading | sell_equity10 | reference | -1.344 | 1.249 | -1.148 [-1.868, -0.373] | 100.0% | -11.57% |
| commodity_only_recent_costed_loading | sell_equity10 | cheap | -0.123 | 3.638 | +0.093 [-2.128, +2.574] | 61.3% | -10.51% |
| commodity_only_recent_costed_loading | replace_trend15 | reference | -0.673 | 1.631 | -0.709 [-1.835, +0.317] | 96.8% | -9.37% |
| commodity_only_recent_costed_loading | replace_trend15 | cheap | +0.547 | 1.866 | +0.532 [-0.579, +1.746] | 9.7% | -0.28% |

Window frequencies overlap heavily and are historical descriptions, not probabilities of future success.

## Selective carry against all-macro carry, identical funding

| panel | arm | comparator | arithmetic gap, pp/yr | MDE | log gap [95%], pp/yr | losing 10-year windows | worst 10-year shortfall |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: |
| bond_commodity_primary_gross | stack10 | all_macro_primary_gross | +0.170 | 0.484 | +0.188 [-0.178, +0.554] | 43.3% | -7.27% |
| bond_commodity_primary_gross | sell_equity10 | all_macro_primary_gross | +0.170 | 0.484 | +0.184 [-0.187, +0.534] | 43.5% | -7.32% |
| bond_commodity_primary_gross | replace_trend15 | all_macro_primary_gross | +0.255 | 0.725 | +0.278 [-0.268, +0.814] | 43.3% | -10.75% |
| bond_commodity_primary_costed | stack10 | all_macro_primary_costed | +0.170 | 0.484 | +0.188 [-0.155, +0.547] | 43.3% | -7.27% |
| bond_commodity_primary_costed | sell_equity10 | all_macro_primary_costed | +0.170 | 0.484 | +0.184 [-0.170, +0.556] | 43.5% | -7.32% |
| bond_commodity_primary_costed | replace_trend15 | all_macro_primary_costed | +0.255 | 0.725 | +0.278 [-0.241, +0.788] | 43.3% | -10.75% |
| bond_commodity_primary_costed_loading | stack10 | all_macro_primary_costed_loading | +0.116 | 0.329 | +0.130 [-0.109, +0.373] | 43.1% | -5.00% |
| bond_commodity_primary_costed_loading | sell_equity10 | all_macro_primary_costed_loading | +0.116 | 0.329 | +0.127 [-0.110, +0.375] | 43.5% | -5.04% |
| bond_commodity_primary_costed_loading | replace_trend15 | all_macro_primary_costed_loading | +0.173 | 0.494 | +0.194 [-0.145, +0.557] | 43.3% | -7.43% |
| bond_commodity_secondary_gross | stack10 | all_macro_secondary_gross | -0.032 | 0.532 | -0.013 [-0.414, +0.413] | 49.3% | -7.26% |
| bond_commodity_secondary_gross | sell_equity10 | all_macro_secondary_gross | -0.032 | 0.532 | -0.016 [-0.397, +0.358] | 49.6% | -7.30% |
| bond_commodity_secondary_gross | replace_trend15 | all_macro_secondary_gross | -0.048 | 0.798 | -0.024 [-0.604, +0.547] | 49.3% | -10.74% |
| bond_commodity_secondary_costed | stack10 | all_macro_secondary_costed | -0.032 | 0.532 | -0.013 [-0.401, +0.371] | 49.3% | -7.26% |
| bond_commodity_secondary_costed | sell_equity10 | all_macro_secondary_costed | -0.032 | 0.532 | -0.016 [-0.403, +0.353] | 49.6% | -7.30% |
| bond_commodity_secondary_costed | replace_trend15 | all_macro_secondary_costed | -0.048 | 0.798 | -0.024 [-0.584, +0.571] | 49.3% | -10.74% |
| bond_commodity_secondary_costed_loading | stack10 | all_macro_secondary_costed_loading | -0.022 | 0.362 | -0.007 [-0.251, +0.253] | 49.1% | -4.99% |
| bond_commodity_secondary_costed_loading | sell_equity10 | all_macro_secondary_costed_loading | -0.022 | 0.362 | -0.009 [-0.258, +0.259] | 49.6% | -5.02% |
| bond_commodity_secondary_costed_loading | replace_trend15 | all_macro_secondary_costed_loading | -0.033 | 0.543 | -0.012 [-0.413, +0.389] | 49.3% | -7.42% |
| bond_commodity_recent_gross | stack10 | all_macro_recent_gross | +0.077 | 1.149 | +0.088 [-0.756, +0.816] | 29.0% | -3.32% |
| bond_commodity_recent_gross | sell_equity10 | all_macro_recent_gross | +0.077 | 1.149 | +0.086 [-0.764, +0.808] | 29.0% | -3.34% |
| bond_commodity_recent_gross | replace_trend15 | all_macro_recent_gross | +0.115 | 1.724 | +0.119 [-1.171, +1.199] | 29.0% | -5.13% |
| bond_commodity_recent_costed | stack10 | all_macro_recent_costed | +0.077 | 1.149 | +0.088 [-0.782, +0.791] | 29.0% | -3.32% |
| bond_commodity_recent_costed | sell_equity10 | all_macro_recent_costed | +0.077 | 1.149 | +0.086 [-0.726, +0.797] | 29.0% | -3.34% |
| bond_commodity_recent_costed | replace_trend15 | all_macro_recent_costed | +0.115 | 1.724 | +0.119 [-1.179, +1.224] | 29.0% | -5.13% |
| bond_commodity_recent_costed_loading | stack10 | all_macro_recent_costed_loading | +0.052 | 0.783 | +0.064 [-0.520, +0.558] | 29.0% | -2.23% |
| bond_commodity_recent_costed_loading | sell_equity10 | all_macro_recent_costed_loading | +0.052 | 0.783 | +0.062 [-0.499, +0.573] | 29.0% | -2.24% |
| bond_commodity_recent_costed_loading | replace_trend15 | all_macro_recent_costed_loading | +0.079 | 1.174 | +0.089 [-0.779, +0.807] | 29.0% | -3.42% |
| commodity_only_primary_gross | stack10 | all_macro_primary_gross | -0.279 | 0.446 | -0.248 [-0.544, +0.075] | 77.5% | -8.91% |
| commodity_only_primary_gross | sell_equity10 | all_macro_primary_gross | -0.279 | 0.446 | -0.250 [-0.551, +0.067] | 78.3% | -8.92% |
| commodity_only_primary_gross | replace_trend15 | all_macro_primary_gross | -0.419 | 0.668 | -0.371 [-0.843, +0.113] | 77.5% | -13.08% |
| commodity_only_primary_costed | stack10 | all_macro_primary_costed | -0.279 | 0.446 | -0.248 [-0.556, +0.069] | 77.5% | -8.91% |
| commodity_only_primary_costed | sell_equity10 | all_macro_primary_costed | -0.279 | 0.446 | -0.250 [-0.543, +0.057] | 78.3% | -8.93% |
| commodity_only_primary_costed | replace_trend15 | all_macro_primary_costed | -0.419 | 0.668 | -0.371 [-0.844, +0.106] | 77.5% | -13.08% |
| commodity_only_primary_costed_loading | stack10 | all_macro_primary_costed_loading | -0.190 | 0.303 | -0.169 [-0.373, +0.045] | 77.7% | -6.17% |
| commodity_only_primary_costed_loading | sell_equity10 | all_macro_primary_costed_loading | -0.190 | 0.303 | -0.171 [-0.378, +0.038] | 78.3% | -6.18% |
| commodity_only_primary_costed_loading | replace_trend15 | all_macro_primary_costed_loading | -0.285 | 0.455 | -0.254 [-0.580, +0.071] | 77.5% | -9.13% |
| commodity_only_secondary_gross | stack10 | all_macro_secondary_gross | -0.205 | 0.503 | -0.175 [-0.484, +0.148] | 68.3% | -8.65% |
| commodity_only_secondary_gross | sell_equity10 | all_macro_secondary_gross | -0.205 | 0.503 | -0.177 [-0.474, +0.135] | 69.3% | -8.67% |
| commodity_only_secondary_gross | replace_trend15 | all_macro_secondary_gross | -0.308 | 0.755 | -0.259 [-0.728, +0.236] | 68.0% | -12.70% |
| commodity_only_secondary_costed | stack10 | all_macro_secondary_costed | -0.205 | 0.503 | -0.175 [-0.495, +0.133] | 68.3% | -8.65% |
| commodity_only_secondary_costed | sell_equity10 | all_macro_secondary_costed | -0.205 | 0.503 | -0.177 [-0.498, +0.164] | 69.3% | -8.67% |
| commodity_only_secondary_costed | replace_trend15 | all_macro_secondary_costed | -0.308 | 0.755 | -0.259 [-0.747, +0.216] | 68.0% | -12.70% |
| commodity_only_secondary_costed_loading | stack10 | all_macro_secondary_costed_loading | -0.140 | 0.343 | -0.120 [-0.334, +0.101] | 68.5% | -5.99% |
| commodity_only_secondary_costed_loading | sell_equity10 | all_macro_secondary_costed_loading | -0.140 | 0.343 | -0.121 [-0.346, +0.087] | 69.3% | -6.00% |
| commodity_only_secondary_costed_loading | replace_trend15 | all_macro_secondary_costed_loading | -0.209 | 0.514 | -0.178 [-0.530, +0.148] | 68.0% | -8.86% |
| commodity_only_recent_gross | stack10 | all_macro_recent_gross | +0.381 | 0.873 | +0.388 [-0.100, +0.909] | 0.0% | 0.00% |
| commodity_only_recent_gross | sell_equity10 | all_macro_recent_gross | +0.381 | 0.873 | +0.387 [-0.124, +0.873] | 0.0% | 0.00% |
| commodity_only_recent_gross | replace_trend15 | all_macro_recent_gross | +0.571 | 1.310 | +0.587 [-0.141, +1.343] | 0.0% | 0.00% |
| commodity_only_recent_costed | stack10 | all_macro_recent_costed | +0.381 | 0.873 | +0.388 [-0.130, +0.868] | 0.0% | 0.00% |
| commodity_only_recent_costed | sell_equity10 | all_macro_recent_costed | +0.381 | 0.873 | +0.387 [-0.106, +0.862] | 0.0% | 0.00% |
| commodity_only_recent_costed | replace_trend15 | all_macro_recent_costed | +0.571 | 1.310 | +0.587 [-0.137, +1.359] | 0.0% | 0.00% |
| commodity_only_recent_costed_loading | stack10 | all_macro_recent_costed_loading | +0.259 | 0.595 | +0.264 [-0.065, +0.598] | 0.0% | 0.00% |
| commodity_only_recent_costed_loading | sell_equity10 | all_macro_recent_costed_loading | +0.259 | 0.595 | +0.263 [-0.051, +0.599] | 0.0% | 0.00% |
| commodity_only_recent_costed_loading | replace_trend15 | all_macro_recent_costed_loading | +0.389 | 0.892 | +0.399 [-0.112, +0.898] | 0.0% | 0.00% |

Window frequencies overlap heavily and are historical descriptions, not probabilities of future success.
