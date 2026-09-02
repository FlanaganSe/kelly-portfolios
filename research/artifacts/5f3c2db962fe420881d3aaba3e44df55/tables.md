# Experiment 024: the working default scored as one object

Run `5f3c2db962fe420881d3aaba3e44df55`; specification hash `d1ef495097097d019e3a4a3b0622783b46061b8a5c0c24cb6f9d868b320075f2`.

WRAPPERS ARE ASSUMED EXPOSURE VECTORS, NOT FUND RETURNS; the tournament panel's tickers are 016f's basis expressions. THE TIPS LINE IS A NOMINAL TEN-YEAR TREASURY modelled as a rolled par bond on FRED GS10 from 1953-04 and Shiller's long rate before it, because no TIPS series exists before 2003; reading it as TIPS assumes the real bond's excess, volatility and equity correlation resemble the nominal bond's, which is false in 1970-81 in the direction that flatters the nominal line's inflation-episode losses. The trend leg is the repository's own 4-asset book scaled by one full-window constant and charged no trading; AQR's TSMOM on the tournament panel is gross of the vendor's trading costs. The primary pair was predicted `rejected` before the run as a leverage result at realised premia; the forward reading is the regret table.

Trend-book volatility scalar 1.9771 (realised 6.26% on 1929-01..2025-05, target 12.38%; 018's 1.9771, reproduced `True`). Shiller long rate against FRED GS10 on 880 overlapping months: largest difference 43.00 bp.

Gap cells read: point estimate, bootstrap and HAC 95% intervals, MDE at 80% power, log-growth gap, years to distinguish, falsifier status. Descriptive tables carry no status.

## Panel `primary`: 1929-01..2025-05, 1157 months, own trend book, monthly rebalancing


### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | bond | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `published_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 12.9362 | 11.0753 | 18.9893 | 0.51 | -82.78 | 164 | 1.0 | 5.1688 |
| `working_default` | 1.268 | 0.968 | 0.250 | 0.050 | 0.000 | 12.2975 | 10.6326 | 17.97 | 0.5034 | -81.0 | 163 | 0.6408 | 3.3122 |
| `trend25_cash5` | 1.218 | 0.968 | 0.250 | 0.000 | 0.050 | 12.2197 | 10.5595 | 17.9451 | 0.4997 | -81.03 | 164 | 0.6023 | 3.1134 |
| `trend25_ltbond5` | 1.268 | 0.968 | 0.250 | 0.050 | 0.000 | 12.3302 | 10.6624 | 17.986 | 0.5047 | -80.95 | 89 | 0.6585 | 3.4038 |
| `trend25_core75` | 1.268 | 1.018 | 0.250 | 0.000 | 0.000 | 12.6057 | 10.7742 | 18.8576 | 0.496 | -82.92 | 165 | 0.7655 | 3.9569 |

### Arithmetic gaps against each control: gap, bootstrap and HAC intervals, MDE, log-growth gap, years-to-distinguish, status

| arm | vs reference | vs cheap | vs leverage_matched | vs volatility_matched_expost | vs volatility_matched_exante | vs mix85 |
| --- | --- | --- | --- | --- | --- | --- |
| `published_trend30` | -- | +1.98 boot [+1.26, +2.71] HAC [+1.21, +2.76] MDE 1.06 log +1.87 27y `exploratory` | -0.30 boot [-1.63, +1.16] HAC [-1.75, +1.15] MDE 1.97 log +0.88 4181y `rejected` | +1.79 boot [+1.07, +2.53] HAC [+1.01, +2.57] MDE 1.06 log +1.77 34y `exploratory` | +1.59 boot [+0.81, +2.38] HAC [+0.80, +2.37] MDE 1.11 log +1.61 45y `exploratory` | +2.91 boot [+1.99, +3.82] HAC [+1.94, +3.88] MDE 1.36 log +2.32 21y `exploratory` |
| `working_default` | -0.64 boot [-0.86, -0.41] HAC [-0.87, -0.40] MDE 0.33 log -0.44 25y `rejected` | +1.34 boot [+0.71, +1.99] HAC [+0.67, +2.02] MDE 0.91 log +1.42 44y `exploratory` | -0.56 boot [-1.82, +0.83] HAC [-1.93, +0.81] MDE 1.87 log +0.58 1079y `rejected` | +1.56 boot [+0.95, +2.18] HAC [+0.91, +2.22] MDE 0.88 log +1.55 31y `exploratory` | +1.39 boot [+0.73, +2.06] HAC [+0.74, +2.05] MDE 0.92 log +1.41 41y `exploratory` | +2.27 boot [+1.56, +2.98] HAC [+1.52, +3.02] MDE 1.05 log +1.88 21y `exploratory` |
| `trend25_cash5` | -0.72 boot [-0.94, -0.49] HAC [-0.95, -0.49] MDE 0.32 log -0.52 20y `rejected` | +1.27 boot [+0.65, +1.91] HAC [+0.59, +1.94] MDE 0.91 log +1.35 50y `exploratory` | -0.28 boot [-1.39, +0.94] HAC [-1.49, +0.93] MDE 1.64 log +0.64 3304y `rejected` | +1.50 boot [+0.89, +2.11] HAC [+0.85, +2.15] MDE 0.88 log +1.48 34y `exploratory` | +1.33 boot [+0.68, +1.98] HAC [+0.68, +1.98] MDE 0.92 log +1.34 45y `exploratory` | +2.19 boot [+1.47, +2.91] HAC [+1.43, +2.95] MDE 1.06 log +1.81 23y `exploratory` |
| `trend25_ltbond5` | -0.61 boot [-0.83, -0.38] HAC [-0.84, -0.37] MDE 0.33 log -0.41 29y `rejected` | +1.38 boot [+0.74, +2.03] HAC [+0.70, +2.06] MDE 0.92 log +1.45 43y `exploratory` | -0.53 boot [-1.79, +0.86] HAC [-1.90, +0.85] MDE 1.87 log +0.61 1224y `rejected` | +1.59 boot [+0.97, +2.21] HAC [+0.93, +2.25] MDE 0.90 log +1.57 31y `exploratory` | +1.42 boot [+0.76, +2.08] HAC [+0.76, +2.08] MDE 0.93 log +1.43 41y `exploratory` | +2.30 boot [+1.59, +3.01] HAC [+1.55, +3.06] MDE 1.06 log +1.91 21y `exploratory` |
| `trend25_core75` | -0.33 boot [-0.45, -0.21] HAC [-0.46, -0.20] MDE 0.18 log -0.30 27y `rejected` | +1.65 boot [+1.05, +2.26] HAC [+1.01, +2.30] MDE 0.88 log +1.56 27y `exploratory` | -0.25 boot [-1.36, +0.97] HAC [-1.46, +0.96] MDE 1.64 log +0.72 4180y `rejected` | +1.51 boot [+0.91, +2.12] HAC [+0.87, +2.16] MDE 0.88 log +1.49 33y `exploratory` | +1.35 boot [+0.70, +2.01] HAC [+0.70, +2.00] MDE 0.92 log +1.37 43y `exploratory` | +2.58 boot [+1.76, +3.40] HAC [+1.71, +3.45] MDE 1.22 log +2.02 22y `exploratory` |

### Sub-windows against `reference`: gap [HAC 95%] floor, per window

| arm | panel_first_half | panel_second_half | from_1934 | from_1946 | from_1970 | from_1990_11 | post_2009 | flat_equity_decade | bond_bull_market | before_bond_bull | after_bond_bull |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `working_default` | -0.64 [-1.00, -0.28] MDE 0.49 (578m) | -0.64 [-0.94, -0.33] MDE 0.44 (579m) | -0.69 [-0.91, -0.46] MDE 0.31 (1097m) | -0.64 [-0.86, -0.41] MDE 0.32 (953m) | -0.61 [-0.89, -0.34] MDE 0.40 (665m) | -0.65 [-0.98, -0.32] MDE 0.48 (415m) | -0.71 [-1.17, -0.26] MDE 0.71 (197m) | -0.08 [-0.73, +0.56] MDE 0.84 (120m) | -0.52 [-0.85, -0.19] MDE 0.48 (466m) | -0.70 [-1.05, -0.36] MDE 0.47 (633m) | -0.89 [-1.61, -0.16] MDE 1.22 (58m) |
| `trend25_cash5` | -0.68 [-1.04, -0.33] MDE 0.49 (578m) | -0.75 [-1.04, -0.45] MDE 0.42 (579m) | -0.76 [-0.98, -0.55] MDE 0.31 (1097m) | -0.70 [-0.92, -0.48] MDE 0.32 (953m) | -0.72 [-0.99, -0.46] MDE 0.39 (665m) | -0.78 [-1.09, -0.46] MDE 0.47 (415m) | -0.74 [-1.16, -0.32] MDE 0.67 (197m) | -0.26 [-0.82, +0.31] MDE 0.81 (120m) | -0.75 [-1.09, -0.42] MDE 0.48 (466m) | -0.70 [-1.04, -0.37] MDE 0.46 (633m) | -0.56 [-1.28, +0.16] MDE 1.22 (58m) |
| `trend25_ltbond5` | -0.64 [-1.00, -0.28] MDE 0.49 (578m) | -0.57 [-0.89, -0.25] MDE 0.45 (579m) | -0.65 [-0.88, -0.42] MDE 0.32 (1097m) | -0.61 [-0.84, -0.38] MDE 0.34 (953m) | -0.56 [-0.84, -0.27] MDE 0.42 (665m) | -0.56 [-0.90, -0.21] MDE 0.50 (415m) | -0.62 [-1.12, -0.11] MDE 0.76 (197m) | -0.02 [-0.66, +0.61] MDE 0.85 (120m) | -0.43 [-0.77, -0.08] MDE 0.49 (466m) | -0.71 [-1.06, -0.37] MDE 0.48 (633m) | -0.86 [-1.65, -0.08] MDE 1.20 (58m) |
| `trend25_core75` | -0.33 [-0.51, -0.15] MDE 0.24 (578m) | -0.33 [-0.52, -0.15] MDE 0.26 (579m) | -0.34 [-0.47, -0.21] MDE 0.18 (1097m) | -0.31 [-0.45, -0.17] MDE 0.20 (953m) | -0.36 [-0.54, -0.18] MDE 0.25 (665m) | -0.31 [-0.51, -0.10] MDE 0.30 (415m) | -0.06 [-0.30, +0.18] MDE 0.37 (197m) | -0.47 [-0.83, -0.11] MDE 0.60 (120m) | -0.33 [-0.53, -0.12] MDE 0.29 (466m) | -0.37 [-0.55, -0.19] MDE 0.23 (633m) | +0.04 [-0.29, +0.36] MDE 0.56 (58m) |

### Sub-windows against `cheap`: gap [HAC 95%] floor, per window

| arm | panel_first_half | panel_second_half | from_1934 | from_1946 | from_1970 | from_1990_11 | post_2009 | flat_equity_decade | bond_bull_market | before_bond_bull | after_bond_bull |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `published_trend30` | +1.98 [+0.88, +3.08] MDE 1.42 (578m) | +1.99 [+0.88, +3.09] MDE 1.57 (579m) | +2.04 [+1.25, +2.83] MDE 1.08 (1097m) | +1.86 [+0.99, +2.72] MDE 1.19 (953m) | +2.17 [+1.11, +3.23] MDE 1.50 (665m) | +1.84 [+0.61, +3.08] MDE 1.78 (415m) | +0.37 [-1.08, +1.81] MDE 2.21 (197m) | +2.84 [+0.68, +4.99] MDE 3.58 (120m) | +1.95 [+0.73, +3.18] MDE 1.76 (466m) | +2.21 [+1.12, +3.29] MDE 1.40 (633m) | -0.21 [-2.17, +1.74] MDE 3.39 (58m) |
| `working_default` | +1.34 [+0.37, +2.30] MDE 1.24 (578m) | +1.35 [+0.39, +2.31] MDE 1.33 (579m) | +1.35 [+0.67, +2.03] MDE 0.91 (1097m) | +1.22 [+0.46, +1.97] MDE 1.01 (953m) | +1.55 [+0.61, +2.49] MDE 1.28 (665m) | +1.19 [+0.06, +2.33] MDE 1.56 (415m) | -0.35 [-1.62, +0.93] MDE 1.93 (197m) | +2.75 [+0.55, +4.95] MDE 3.33 (120m) | +1.43 [+0.35, +2.51] MDE 1.51 (466m) | +1.50 [+0.56, +2.44] MDE 1.21 (633m) | -1.10 [-2.67, +0.47] MDE 2.91 (58m) |
| `trend25_cash5` | +1.29 [+0.31, +2.28] MDE 1.25 (578m) | +1.24 [+0.31, +2.17] MDE 1.32 (579m) | +1.27 [+0.60, +1.95] MDE 0.91 (1097m) | +1.15 [+0.40, +1.90] MDE 1.01 (953m) | +1.44 [+0.52, +2.37] MDE 1.28 (665m) | +1.07 [-0.01, +2.15] MDE 1.52 (415m) | -0.37 [-1.59, +0.85] MDE 1.89 (197m) | +2.58 [+0.51, +4.65] MDE 3.24 (120m) | +1.20 [+0.17, +2.23] MDE 1.48 (466m) | +1.50 [+0.54, +2.47] MDE 1.23 (633m) | -0.77 [-2.45, +0.92] MDE 3.01 (58m) |
| `trend25_ltbond5` | +1.34 [+0.37, +2.30] MDE 1.24 (578m) | +1.42 [+0.45, +2.39] MDE 1.37 (579m) | +1.38 [+0.70, +2.07] MDE 0.93 (1097m) | +1.25 [+0.49, +2.01] MDE 1.02 (953m) | +1.61 [+0.66, +2.56] MDE 1.31 (665m) | +1.29 [+0.13, +2.45] MDE 1.63 (415m) | -0.25 [-1.56, +1.07] MDE 2.03 (197m) | +2.81 [+0.57, +5.06] MDE 3.50 (120m) | +1.53 [+0.43, +2.62] MDE 1.57 (466m) | +1.49 [+0.56, +2.43] MDE 1.20 (633m) | -1.07 [-2.67, +0.53] MDE 2.89 (58m) |
| `trend25_core75` | +1.65 [+0.73, +2.56] MDE 1.18 (578m) | +1.66 [+0.74, +2.58] MDE 1.31 (579m) | +1.70 [+1.04, +2.36] MDE 0.90 (1097m) | +1.55 [+0.83, +2.27] MDE 0.99 (953m) | +1.81 [+0.92, +2.69] MDE 1.25 (665m) | +1.54 [+0.50, +2.57] MDE 1.49 (415m) | +0.30 [-0.90, +1.51] MDE 1.84 (197m) | +2.36 [+0.57, +4.16] MDE 2.99 (120m) | +1.63 [+0.61, +2.65] MDE 1.47 (466m) | +1.84 [+0.94, +2.74] MDE 1.17 (633m) | -0.18 [-1.81, +1.45] MDE 2.82 (58m) |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | deflationary episodes mean pp | inflation episodes mean pp | flat decade gap vs ref pp/yr |
| --- | ---: | ---: | ---: | ---: |
| `published_trend30` | -- | 0.0 (5 ep.) | 0.0 (3 ep.) | -- |
| `working_default` | 0.435 (0.922) | 1.76 (5 ep.) | -3.0 (3 ep.) | -0.08 |
| `trend25_cash5` | 0.428 (0.948) | 1.44 (5 ep.) | -1.25 (3 ep.) | -0.26 |
| `trend25_ltbond5` | 0.436 (0.913) | 1.77 (5 ep.) | -3.44 (3 ep.) | -0.02 |
| `trend25_core75` | -0.04 (0.426) | -0.35 (5 ep.) | -2.64 (3 ep.) | -0.47 |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `published_trend30` | -82.78 (+0.00) | -50.34 (+0.00) | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -34.29 (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `working_default` | -81.0 (+1.78) | -48.18 (+2.16) | -38.69 (+1.99) | -44.1 (+1.76) | -17.53 (+1.10) | -34.38 (-0.09) | 76.8 (-9.20) | -23.28 (+0.29) |
| `trend25_cash5` | -81.03 (+1.75) | -48.29 (+2.06) | -39.31 (+1.37) | -44.57 (+1.29) | -17.92 (+0.71) | -33.97 (+0.32) | 80.96 (-5.04) | -22.59 (+0.98) |
| `trend25_ltbond5` | -80.95 (+1.84) | -48.29 (+2.06) | -38.69 (+1.99) | -44.16 (+1.70) | -17.38 (+1.25) | -34.59 (-0.29) | 75.59 (-10.42) | -23.18 (+0.39) |
| `trend25_core75` | -82.92 (-0.14) | -50.19 (+0.15) | -41.41 (-0.73) | -46.61 (-0.75) | -18.9 (-0.27) | -36.49 (-2.20) | 80.49 (-5.52) | -23.78 (-0.21) |

### The ten-year leg by era (its realised history, to haircut against)

| era | window | months | ten-year/equity corr | ten-year excess pp/yr | ten-year vol % | long bond excess pp/yr | equity excess pp/yr | trend excess pp/yr | cash pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_full | 1929-01..2025-05 | 1157 | 0.09 | 1.61 | 5.54 | 2.26 | 7.75 | 7.22 | 3.23 |
| panel_first_half | 1929-01..1977-02 | 578 | 0.133 | 0.93 | 3.11 | 0.94 | 7.12 | 7.25 | 2.31 |
| panel_second_half | 1977-03..2025-05 | 579 | 0.086 | 2.28 | 7.18 | 3.58 | 8.38 | 7.19 | 4.16 |
| from_1934 | 1934-01..2025-05 | 1097 | 0.105 | 1.57 | 5.68 | 2.28 | 8.53 | 7.34 | 3.31 |
| from_1946 | 1946-01..2025-05 | 953 | 0.119 | 1.36 | 6.09 | 1.91 | 7.91 | 6.79 | 3.78 |
| from_1970 | 1970-01..2025-05 | 665 | 0.125 | 2.22 | 7.01 | 3.38 | 7.27 | 7.87 | 4.35 |
| from_1990_11 | 1990-11..2025-05 | 415 | -0.047 | 2.64 | 6.24 | 4.45 | 9.44 | 6.63 | 2.54 |
| post_2009 | 2009-01..2025-05 | 197 | -0.078 | 0.52 | 6.13 | 2.48 | 13.54 | 1.41 | 1.15 |
| flat_equity_decade | 1999-03..2009-02 | 120 | -0.125 | 3.46 | 6.79 | 4.7 | -4.32 | 10.93 | 3.1 |
| bond_bull_market | 1981-10..2020-07 | 466 | 0.035 | 4.75 | 6.78 | 6.58 | 8.61 | 7.06 | 3.73 |
| before_bond_bull | 1929-01..1981-09 | 633 | 0.13 | 0.04 | 4.13 | -0.16 | 6.73 | 8.03 | 2.91 |
| after_bond_bull | 2020-08..2025-05 | 58 | 0.309 | -6.54 | 6.51 | -6.04 | 11.88 | -0.39 | 2.73 |

### Financing sensitivity: gap against the reference arm at each equity basis (bp), then against the cheap control

ordering against reference stable across the band: `True`

| arm | 62 | 98 | 130 | 165 | 200 | 231 | vs cheap at each point |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `published_trend30` | -- | -- | -- | -- | -- | -- | +1.98, +1.95, +1.92, +1.88, +1.85, +1.82 |
| `working_default` | -0.64 | -0.63 | -0.63 | -0.62 | -0.62 | -0.61 | +1.34, +1.31, +1.29, +1.26, +1.23, +1.20 |
| `trend25_cash5` | -0.72 | -0.71 | -0.71 | -0.70 | -0.69 | -0.69 | +1.27, +1.24, +1.21, +1.18, +1.15, +1.13 |
| `trend25_ltbond5` | -0.61 | -0.60 | -0.59 | -0.59 | -0.58 | -0.58 | +1.38, +1.35, +1.32, +1.29, +1.26, +1.24 |
| `trend25_core75` | -0.33 | -0.32 | -0.32 | -0.31 | -0.31 | -0.30 | +1.65, +1.62, +1.60, +1.57, +1.54, +1.51 |

### Regret at forward premia: working default minus published, pp/yr, arithmetic / log (positive means the working default wins)

Bond excess over cash 0.8 pp/yr; variance-drag constant 0.1884 pp/yr added to every log cell.

| gross trend premium pp/yr | equity over bonds 0.0 | equity over bonds 1.5 | equity over bonds 3.0 | equity over bonds 5.0 |
| --- | ---: | ---: | ---: | ---: |
| 0.0 | +0.05 / +0.24 | -0.03 / +0.16 | -0.11 / +0.08 | -0.21 / -0.03 |
| 1.74 | -0.03 / +0.16 | -0.11 / +0.07 | -0.19 / -0.01 | -0.30 / -0.11 |
| 3.9 | -0.14 / +0.05 | -0.22 / -0.03 | -0.30 / -0.11 | -0.41 / -0.22 |
| 4.07 (central) | -0.15 / +0.04 | -0.23 / -0.04 | -0.31 / -0.12 | -0.42 / -0.23 |
| 5.32 | -0.21 / -0.02 | -0.29 / -0.10 | -0.37 / -0.18 | -0.48 / -0.29 |
| 7.18 | -0.30 / -0.12 | -0.39 / -0.20 | -0.47 / -0.28 | -0.57 / -0.38 |
| 10.98 | -0.49 / -0.31 | -0.57 / -0.39 | -0.66 / -0.47 | -0.76 / -0.57 |

Break-even gross trend premium (the working default wins below it):

| equity over bonds pp/yr | arithmetic | log |
| ---: | ---: | ---: |
| 0.0 | 1.088 | 4.855 |
| 1.5 | -0.52 | 3.247 |
| 3.0 | -2.128 | 1.639 |
| 5.0 | -4.272 | -0.505 |

## Panel `tournament_1990`: 1990-11..2026-05, 427 months, 016f's basis-mapped funds and AQR TSMOM, annual rebalancing

Reproduction of 016f's rec30 minus rec25 log gap: observed 0.5101 against 0.5101, reproduced `True`.


### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | bond | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `published` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 15.1261 | 13.9474 | 14.772 | -- | -49.69 | 42 | -- | -- |
| `working_default` | 1.268 | 0.968 | 0.250 | 0.050 | 0.000 | 14.2586 | 13.2079 | 13.9455 | -- | -47.38 | 42 | -- | -- |
| `trend25_cash5` | 1.218 | 0.968 | 0.250 | 0.000 | 0.050 | 14.1353 | 13.0835 | 13.9606 | -- | -48.0 | 42 | -- | -- |
| `rec25` | 1.268 | 1.018 | 0.250 | 0.000 | 0.000 | 14.595 | 13.4373 | 14.6613 | -- | -50.27 | 42 | -- | -- |

### Arithmetic gaps against each control: gap, bootstrap and HAC intervals, MDE, log-growth gap, years-to-distinguish, status

| arm | vs reference | vs cheap | vs leverage_matched |
| --- | --- | --- | --- |
| `published` | -- | +3.99 boot [+2.43, +5.50] HAC [+2.61, +5.37] MDE 1.88 log +3.95 8y `exploratory` | +1.64 boot [-0.82, +4.15] HAC [-0.85, +4.12] MDE 3.25 log +2.50 140y `unresolved` |
| `working_default` | -0.87 boot [-1.20, -0.52] HAC [-1.19, -0.54] MDE 0.46 log -0.74 10y `rejected` | +3.12 boot [+1.66, +4.55] HAC [+1.82, +4.42] MDE 1.72 log +3.21 11y `exploratory` | +1.15 boot [-1.15, +3.54] HAC [-1.19, +3.49] MDE 3.05 log +1.97 248y `unresolved` |
| `trend25_cash5` | -0.99 boot [-1.31, -0.68] HAC [-1.29, -0.69] MDE 0.44 log -0.86 7y `rejected` | +3.00 boot [+1.56, +4.38] HAC [+1.74, +4.26] MDE 1.69 log +3.09 11y `exploratory` | +1.39 boot [-0.68, +3.51] HAC [-0.67, +3.45] MDE 2.71 log +2.05 135y `unresolved` |
| `rec25` | -0.53 boot [-0.75, -0.31] HAC [-0.74, -0.32] MDE 0.30 log -0.51 11y `rejected` | +3.46 boot [+2.11, +4.76] HAC [+2.28, +4.64] MDE 1.59 log +3.44 8y `exploratory` | +1.49 boot [-0.59, +3.61] HAC [-0.59, +3.57] MDE 2.73 log +2.20 119y `unresolved` |

### Sub-windows against `reference`: gap [HAC 95%] floor, per window

| arm | panel_first_half | panel_second_half | post_2009 | flat_equity_decade |
| --- | --- | --- | --- | --- |
| `working_default` | -0.99 [-1.39, -0.58] MDE 0.60 (213m) | -0.75 [-1.24, -0.26] MDE 0.69 (214m) | -0.82 [-1.25, -0.38] MDE 0.70 (197m) | -0.23 [-0.98, +0.52] MDE 0.89 (120m) |
| `trend25_cash5` | -1.17 [-1.59, -0.76] MDE 0.60 (213m) | -0.81 [-1.23, -0.39] MDE 0.65 (214m) | -0.82 [-1.22, -0.43] MDE 0.66 (197m) | -0.45 [-1.08, +0.19] MDE 0.84 (120m) |
| `rec25` | -0.82 [-1.08, -0.55] MDE 0.38 (213m) | -0.24 [-0.56, +0.07] MDE 0.44 (214m) | -0.16 [-0.47, +0.16] MDE 0.46 (197m) | -0.74 [-1.09, -0.39] MDE 0.55 (120m) |
