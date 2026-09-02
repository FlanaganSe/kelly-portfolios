# Experiment 018: defensive engines inside the leveraged construction

Run `311048fbc6b44072a3715ff24d1507a4`; specification hash `40252300638012d1aebff0582bce39a185fa5a3e555f0c5cdcf4e5bcbbe9dd0f`.

WRAPPERS ARE ASSUMED EXPOSURE VECTORS, NOT FUND RETURNS. The bond leg is realised history that contains the 1981-2020 bull market and is a ~20-year bond, longer than the Treasury-futures ladders RSSB and NTSX hold. The long-panel trend leg is this repository's own 4-asset book scaled by one full-window constant; the secondary panel's is AQR's TSMOM, gross of the vendor's trading costs by omission. The gold sub-window includes 1971-08..1974-12, when the dollar gold price was an administered peg and private US ownership was illegal. Gold financing at 30 bp is an assumption. Every mean gap was predicted `unresolved` before the run.

Trend-book volatility scalar 1.9771 (realised 6.26% on 1929-01..2025-05, target 12.38%).

Gap cells read: point estimate [95% block-bootstrap interval] MDE at 80% power, years to distinguish, falsifier status. A control column marked `identical` is the arm itself. Descriptive tables carry no status by design.

## Panel `primary` (primary): 1929-01..2025-05, 1157 months, trend `own_4_asset_book`, bond `goyal_welch_ltr`

The longest window on which equity, T-bills, long government bonds and the own trend book all exist. Expected 1929-01..2025-05, 1157 months.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | bond | gold | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 0.000 | 12.9362 | 11.0753 | 18.9893 | 0.51 | -82.78 | 164 | 1.0 | 5.1688 |
| `base_no_trend` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 10.9532 | 9.21 | 18.4972 | 0.4165 | -83.67 | 184 | 0.1935 | 1.0 |
| `trend30_bondstack20` | 1.522 | 1.022 | 0.300 | 0.200 | 0.000 | 0.000 | 13.2737 | 11.3705 | 19.2099 | 0.5216 | -82.53 | 88 | 1.2891 | 6.6631 |
| `trend30_bondstack40` | 1.722 | 1.022 | 0.300 | 0.400 | 0.000 | 0.000 | 13.6113 | 11.6365 | 19.5777 | 0.529 | -82.28 | 86 | 1.619 | 8.3682 |
| `trend20_rsbt10` | 1.314 | 0.914 | 0.300 | 0.100 | 0.000 | 0.000 | 12.339 | 10.8185 | 17.1417 | 0.5301 | -78.27 | 86 | 0.7157 | 3.6995 |
| `ntsx100` | 1.500 | 0.900 | 0.000 | 0.600 | 0.000 | 0.000 | 11.2741 | 9.6625 | 17.7836 | 0.4512 | -78.98 | 87 | 0.2533 | 1.3091 |
| `trend30_cash10` | 1.222 | 0.922 | 0.300 | 0.000 | 0.000 | 0.100 | 12.1642 | 10.6379 | 17.1775 | 0.5188 | -78.78 | 86 | 0.616 | 3.1838 |
| `trend30_ltbond10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 0.000 | 12.3852 | 10.842 | 17.2716 | 0.5288 | -78.59 | 86 | 0.7356 | 3.8022 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.98 [+1.26, +2.73] MDE 1.06 27y `exploratory` | -0.30 [-1.63, +1.15] MDE 1.97 4181y `rejected` | +1.79 [+1.06, +2.54] MDE 1.06 34y `exploratory` | +1.59 [+0.82, +2.38] MDE 1.11 45y `exploratory` | -- |
| `base_no_trend` | identical | identical | identical | -0.00 [-0.00, +0.00] MDE 0.00 424y `rejected` | -1.98 [-2.73, -1.26] MDE 1.06 27y `rejected` |
| `trend30_bondstack20` | +2.32 [+1.50, +3.17] MDE 1.19 25y `exploratory` | -1.38 [-3.34, +0.78] MDE 2.94 436y `rejected` | +2.05 [+1.22, +2.89] MDE 1.19 33y `exploratory` | +1.82 [+0.96, +2.67] MDE 1.24 43y `exploratory` | +0.34 [-0.01, +0.69] MDE 0.49 201y `unresolved` |
| `trend30_bondstack40` | +2.66 [+1.63, +3.73] MDE 1.48 30y `exploratory` | -2.46 [-5.13, +0.47] MDE 3.99 253y `rejected` | +2.24 [+1.22, +3.31] MDE 1.49 42y `exploratory` | +1.97 [+0.90, +3.03] MDE 1.54 57y `exploratory` | +0.68 [-0.01, +1.37] MDE 0.97 201y `unresolved` |
| `trend20_rsbt10` | +1.39 [+0.56, +2.24] MDE 1.21 74y `exploratory` | -0.85 [-2.48, +0.95] MDE 2.44 800y `rejected` | +1.95 [+1.20, +2.72] MDE 1.10 31y `exploratory` | +1.72 [+0.91, +2.51] MDE 1.15 42y `exploratory` | -0.60 [-1.01, -0.17] MDE 0.60 97y `rejected` |
| `ntsx100` | +0.32 [-0.74, +1.36] MDE 1.52 2153y `unresolved` | -3.23 [-5.54, -0.82] MDE 3.39 106y `rejected` | +0.62 [-0.42, +1.65] MDE 1.47 547y `unresolved` | +0.56 [-0.54, +1.62] MDE 1.52 686y `unresolved` | -1.66 [-2.95, -0.45] MDE 1.81 114y `rejected` |
| `trend30_cash10` | +1.21 [+0.43, +2.04] MDE 1.17 89y `exploratory` | -0.36 [-1.69, +1.09] MDE 1.97 2865y `rejected` | +1.76 [+1.03, +2.51] MDE 1.06 35y `exploratory` | +1.54 [+0.76, +2.33] MDE 1.11 49y `exploratory` | -0.77 [-1.14, -0.38] MDE 0.53 45y `rejected` |
| `trend30_ltbond10` | +1.43 [+0.62, +2.28] MDE 1.20 67y `exploratory` | -0.85 [-2.48, +0.95] MDE 2.44 791y `rejected` | +1.94 [+1.19, +2.72] MDE 1.10 31y `exploratory` | +1.71 [+0.90, +2.51] MDE 1.15 42y `exploratory` | -0.55 [-0.94, -0.15] MDE 0.57 101y `rejected` |

### The controls themselves: what the levered and volatility-matched comparators cost in drawdown (descriptive)

| arm | control | definition | arith pp/yr | log growth | vol % | max DD % | months under water |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | leverage_matched | 1.3216 x CORE, financed at the equity basis | 13.2356 | 10.1905 | 24.4527 | -92.06 | 194 |
| `base_trend30` | volatility_matched_expost | 1.0266 x CORE, financed at the equity basis (full-window volatility match) | 11.142 | 9.3053 | 18.9897 | -84.58 | 185 |
| `base_trend30` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 12.6311 | 10.8811 | 18.492 | -53.03 | 79 |
| `base_no_trend` | leverage_matched | 1.0000 x CORE, financed at the equity basis | 10.9532 | 9.21 | 18.4972 | -83.67 | 184 |
| `base_no_trend` | volatility_matched_expost | 1.0000 x CORE + 0.0000 x CASH (full-window volatility match) | 10.9532 | 9.21 | 18.4972 | -83.67 | 184 |
| `base_no_trend` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 12.2585 | 10.6576 | 17.7442 | -50.33 | 74 |
| `trend30_bondstack20` | leverage_matched | 1.5216 x CORE, financed at the equity basis | 14.6549 | 10.6075 | 28.1575 | -95.11 | 245 |
| `trend30_bondstack20` | volatility_matched_expost | 1.0385 x CORE, financed at the equity basis (full-window volatility match) | 11.2266 | 9.3472 | 19.2106 | -84.97 | 185 |
| `trend30_bondstack20` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 12.7659 | 10.9652 | 18.7468 | -53.31 | 79 |
| `trend30_bondstack40` | leverage_matched | 1.7216 x CORE, financed at the equity basis | 16.0741 | 10.8703 | 31.8627 | -97.08 | 255 |
| `trend30_bondstack40` | volatility_matched_expost | 1.0584 x CORE, financed at the equity basis (full-window volatility match) | 11.3677 | 9.4159 | 19.5787 | -85.6 | 185 |
| `trend30_bondstack40` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 12.9756 | 11.0896 | 19.1697 | -53.63 | 79 |
| `trend20_rsbt10` | leverage_matched | 1.3144 x CORE, financed at the equity basis | 13.1845 | 10.1726 | 24.3194 | -91.93 | 194 |
| `trend20_rsbt10` | volatility_matched_expost | 0.9267 x CORE + 0.0733 x CASH (full-window volatility match) | 10.3873 | 8.8893 | 17.1407 | -80.94 | 182 |
| `trend20_rsbt10` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.7835 | 10.3435 | 16.7433 | -49.17 | 78 |
| `ntsx100` | leverage_matched | 1.5000 x CORE, financed at the equity basis | 14.5016 | 10.5698 | 27.7573 | -94.84 | 200 |
| `ntsx100` | volatility_matched_expost | 0.9614 x CORE + 0.0386 x CASH (full-window volatility match) | 10.6553 | 9.0435 | 17.783 | -82.28 | 183 |
| `ntsx100` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.9684 | 10.4406 | 17.2938 | -48.55 | 73 |
| `trend30_cash10` | leverage_matched | 1.2216 x CORE, financed at the equity basis | 12.5259 | 9.9259 | 22.6006 | -89.99 | 192 |
| `trend30_cash10` | volatility_matched_expost | 0.9287 x CORE + 0.0713 x CASH (full-window volatility match) | 10.4023 | 8.898 | 17.1765 | -81.02 | 182 |
| `trend30_cash10` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.7843 | 10.3428 | 16.7585 | -49.3 | 78 |
| `trend30_ltbond10` | leverage_matched | 1.3216 x CORE, financed at the equity basis | 13.2356 | 10.1905 | 24.4527 | -92.06 | 194 |
| `trend30_ltbond10` | volatility_matched_expost | 0.9337 x CORE + 0.0663 x CASH (full-window volatility match) | 10.4416 | 8.9208 | 17.2707 | -81.22 | 182 |
| `trend30_ltbond10` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.845 | 10.3839 | 16.8674 | -49.44 | 78 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp | flat decade gap vs ref pp/yr | flat decade gap vs cheap pp/yr |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (5 ep.) | 0.0 (3 ep.) | -- | +2.84 |
| `base_no_trend` | -0.239 (0.426) | -0.038 (-1.29) | -2.09 (5 ep.) | -14.98 (3 ep.) | -2.84 | +0.00 |
| `trend30_bondstack20` | 0.025 (0.522) | -0.01 (-1.24) | 1.22 (5 ep.) | -9.0 (3 ep.) | +0.83 | +3.66 |
| `trend30_bondstack40` | 0.049 (0.522) | -0.02 (-1.24) | 2.43 (5 ep.) | -17.22 (3 ep.) | +1.65 | +4.49 |
| `trend20_rsbt10` | 1.021 (0.983) | -0.005 (-1.24) | 4.63 (5 ep.) | -1.35 (3 ep.) | +0.94 | +3.78 |
| `ntsx100` | 0.777 (0.696) | -0.068 (-1.65) | 5.22 (5 ep.) | -33.89 (3 ep.) | +0.16 | +2.99 |
| `trend30_cash10` | 0.936 (1.0) | 0.0 (4.89) | 3.66 (5 ep.) | 2.87 (3 ep.) | +0.44 | +3.27 |
| `trend30_ltbond10` | 0.953 (0.983) | -0.005 (-1.24) | 4.34 (5 ep.) | -1.59 (3 ep.) | +0.90 | +3.74 |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | -82.78 (+0.00) | -50.34 (+0.00) | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -34.29 (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `base_no_trend` | -83.67 (-0.89) | -49.47 (+0.87) | -45.03 (-4.35) | -50.33 (-4.47) | -20.22 (-1.59) | -46.54 (-12.24) | 54.6 (-31.41) | -24.86 (-1.29) |
| `trend30_bondstack20` | -82.53 (+0.25) | -50.42 (-0.07) | -38.37 (+2.31) | -44.4 (+1.46) | -16.48 (+2.14) | -36.83 (-2.54) | 63.93 (-22.07) | -25.95 (-2.38) |
| `trend30_bondstack40` | -82.28 (+0.50) | -50.49 (-0.15) | -36.02 (+4.65) | -43.02 (+2.84) | -14.31 (+4.32) | -39.3 (-5.00) | 44.04 (-41.96) | -28.27 (-4.70) |
| `trend20_rsbt10` | -78.27 (+4.51) | -46.2 (+4.14) | -34.75 (+5.92) | -40.49 (+5.37) | -15.43 (+3.20) | -29.91 (+4.38) | 76.18 (-9.83) | -22.18 (+1.39) |
| `ntsx100` | -78.98 (+3.80) | -45.72 (+4.63) | -33.62 (+7.06) | -42.14 (+3.72) | -11.73 (+6.90) | -48.75 (-14.45) | 4.71 (-81.30) | -29.5 (-5.93) |
| `trend30_cash10` | -78.78 (+4.00) | -46.49 (+3.86) | -36.38 (+4.30) | -41.66 (+4.20) | -16.66 (+1.97) | -29.0 (+5.29) | 86.92 (+0.92) | -21.16 (+2.40) |
| `trend30_ltbond10` | -78.59 (+4.19) | -46.49 (+3.85) | -35.09 (+5.59) | -40.82 (+5.04) | -15.57 (+3.06) | -30.31 (+3.98) | 76.04 (-9.96) | -22.36 (+1.21) |

### Bond-equity regime by era (the bond leg's realised history, to haircut against)

| era | window | months | bond-equity corr | bond excess pp/yr | bond vol % | equity excess pp/yr | trend excess pp/yr | cash pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_full | 1929-01..2025-05 | 1157 | 0.076 | 2.26 | 8.54 | 7.75 | 7.22 | 3.23 |
| panel_first_half | 1929-01..1977-02 | 578 | 0.133 | 0.94 | 5.53 | 7.12 | 7.25 | 2.31 |
| panel_second_half | 1977-03..2025-05 | 579 | 0.051 | 3.58 | 10.73 | 8.38 | 7.19 | 4.16 |
| first_half | 1929-01..1977-03 | 579 | 0.133 | 0.95 | 5.53 | 7.08 | 7.26 | 2.31 |
| second_half | 1977-04..2025-05 | 578 | 0.051 | 3.57 | 10.74 | 8.42 | 7.18 | 4.16 |
| flat_equity_decade | 1999-03..2009-02 | 120 | -0.164 | 4.7 | 10.91 | -4.32 | 10.93 | 3.1 |
| bond_bull_market | 1981-10..2020-07 | 466 | -0.021 | 6.58 | 10.73 | 8.61 | 7.06 | 3.73 |
| before_bond_bull | 1929-01..1981-09 | 633 | 0.152 | -0.16 | 6.49 | 6.73 | 8.03 | 2.91 |
| after_bond_bull | 2020-08..2025-05 | 58 | 0.374 | -6.04 | 7.05 | 11.88 | -0.39 | 2.73 |
| positive_bond_equity_correlation | 1966-01..1997-12 | 384 | 0.36 | 1.7 | 10.53 | 5.86 | 9.34 | 6.44 |

### Financing sensitivity: gap against the reference arm at each basis (pp/yr), then against the cheap control


equity basis, bp: 62, 98, 130, 165, 200, 231
ordering against reference stable across the band: `False`

| arm | 62 | 98 | 130 | 165 | 200 | 231 | vs cheap at each point |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `base_trend30` | -- | -- | -- | -- | -- | -- | +1.98, +1.95, +1.92, +1.88, +1.85, +1.82 |
| `base_no_trend` | -1.98 | -1.95 | -1.92 | -1.88 | -1.85 | -1.82 | +0.00, +0.00, +0.00, +0.00, +0.00, +0.00 |
| `trend30_bondstack20` | +0.34 | +0.33 | +0.32 | +0.32 | +0.31 | +0.30 | +2.32, +2.28, +2.24, +2.20, +2.16, +2.12 |
| `trend30_bondstack40` | +0.68 | +0.66 | +0.65 | +0.63 | +0.62 | +0.61 | +2.66, +2.61, +2.56, +2.51, +2.47, +2.42 |
| `trend20_rsbt10` | -0.60 | -0.59 | -0.57 | -0.56 | -0.55 | -0.54 | +1.39, +1.36, +1.34, +1.32, +1.29, +1.27 |
| `ntsx100` | -1.66 | -1.63 | -1.59 | -1.56 | -1.53 | -1.49 | +0.32, +0.32, +0.32, +0.32, +0.32, +0.32 |
| `trend30_cash10` | -0.77 | -0.77 | -0.77 | -0.77 | -0.77 | -0.77 | +1.21, +1.18, +1.14, +1.11, +1.07, +1.04 |
| `trend30_ltbond10` | -0.55 | -0.55 | -0.55 | -0.55 | -0.55 | -0.55 | +1.43, +1.40, +1.36, +1.33, +1.29, +1.26 |

treasury basis, bp: 0, 15, 30, 50
ordering against reference stable across the band: `True`

| arm | 0 | 15 | 30 | 50 | vs cheap at each point |
| --- | ---: | ---: | ---: | ---: | --- |
| `base_trend30` | -- | -- | -- | -- | +1.98, +1.98, +1.98, +1.98 |
| `base_no_trend` | -1.98 | -1.98 | -1.98 | -1.98 | +0.00, +0.00, +0.00, +0.00 |
| `trend30_bondstack20` | +0.37 | +0.34 | +0.31 | +0.27 | +2.35, +2.32, +2.29, +2.25 |
| `trend30_bondstack40` | +0.73 | +0.68 | +0.61 | +0.54 | +2.72, +2.66, +2.60, +2.52 |
| `trend20_rsbt10` | -0.58 | -0.60 | -0.61 | -0.63 | +1.40, +1.39, +1.37, +1.35 |
| `ntsx100` | -1.57 | -1.66 | -1.75 | -1.87 | +0.41, +0.32, +0.23, +0.11 |
| `trend30_cash10` | -0.77 | -0.77 | -0.77 | -0.77 | +1.21, +1.21, +1.21, +1.21 |
| `trend30_ltbond10` | -0.55 | -0.55 | -0.55 | -0.55 | +1.43, +1.43, +1.43, +1.43 |

## Panel `primary_gold_subwindow` (primary_subwindow): 1968-05..2025-05, 685 months, trend `own_4_asset_book`, bond `goyal_welch_ltr`

The primary panel from the first LBMA monthly return (1968-05) so that the gold arm can run beside every other arm on the own trend book. It INCLUDES 1971-08..1974-12; freeze note 5.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | bond | gold | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 0.000 | 13.3917 | 11.9817 | 16.3686 | 0.5482 | -45.86 | 51 | 1.0 | 2.7561 |
| `base_no_trend` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 11.2609 | 9.96 | 15.8063 | 0.433 | -50.33 | 73 | 0.3628 | 1.0 |
| `trend30_bondstack20` | 1.522 | 1.022 | 0.300 | 0.200 | 0.000 | 0.000 | 13.8725 | 12.4023 | 16.7293 | 0.565 | -44.4 | 50 | 1.2954 | 3.5703 |
| `trend30_bondstack40` | 1.722 | 1.022 | 0.300 | 0.400 | 0.000 | 0.000 | 14.3533 | 12.7794 | 17.3365 | 0.5729 | -43.02 | 41 | 1.6415 | 4.5241 |
| `trend20_rsbt10` | 1.314 | 0.914 | 0.300 | 0.100 | 0.000 | 0.000 | 12.9575 | 11.7875 | 14.8828 | 0.5738 | -40.49 | 49 | 0.8909 | 2.4553 |
| `ntsx100` | 1.500 | 0.900 | 0.000 | 0.600 | 0.000 | 0.000 | 12.0971 | 10.7574 | 16.0735 | 0.4777 | -49.1 | 50 | 0.6067 | 1.6721 |
| `trend30_goldstack10` | 1.402 | 1.012 | 0.300 | 0.000 | 0.090 | 0.000 | 13.7449 | 12.3331 | 16.3597 | 0.5698 | -44.42 | 50 | 1.1784 | 3.2479 |
| `trend30_cash10` | 1.222 | 0.922 | 0.300 | 0.000 | 0.000 | 0.100 | 12.705 | 11.542 | 14.8391 | 0.5585 | -41.66 | 50 | 0.7704 | 2.1234 |
| `trend30_ltbond10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 0.000 | 12.9976 | 11.8108 | 14.9921 | 0.5723 | -40.82 | 50 | 0.9038 | 2.4909 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +2.13 [+1.15, +3.18] MDE 1.48 27y `exploratory` | +0.12 [-1.52, +1.87] MDE 2.38 21495y `unresolved` | +1.91 [+0.90, +2.97] MDE 1.49 35y `exploratory` | +1.89 [+0.81, +3.01] MDE 1.56 37y `exploratory` | -- |
| `base_no_trend` | identical | identical | identical | +0.00 [-0.00, +0.00] MDE 0.00 16155y `unresolved` | -2.13 [-3.18, -1.15] MDE 1.48 27y `rejected` |
| `trend30_bondstack20` | +2.61 [+1.47, +3.81] MDE 1.72 25y `exploratory` | -0.65 [-2.98, +1.80] MDE 3.43 1613y `rejected` | +2.25 [+1.05, +3.46] MDE 1.74 34y `exploratory` | +2.22 [+1.02, +3.45] MDE 1.82 36y `exploratory` | +0.48 [-0.06, +1.01] MDE 0.78 148y `unresolved` |
| `trend30_bondstack40` | +3.09 [+1.58, +4.63] MDE 2.23 30y `exploratory` | -1.41 [-4.52, +1.83] MDE 4.64 615y `rejected` | +2.49 [+0.93, +4.06] MDE 2.26 47y `exploratory` | +2.45 [+0.93, +4.01] MDE 2.35 50y `exploratory` | +0.96 [-0.11, +2.01] MDE 1.55 148y `unresolved` |
| `trend20_rsbt10` | +1.70 [+0.56, +2.87] MDE 1.66 54y `exploratory` | -0.27 [-2.24, +1.82] MDE 2.87 6635y `rejected` | +2.10 [+1.03, +3.20] MDE 1.57 32y `exploratory` | +2.07 [+0.96, +3.23] MDE 1.65 34y `exploratory` | -0.43 [-0.89, +0.04] MDE 0.71 152y `rejected` |
| `ntsx100` | +0.84 [-0.74, +2.40] MDE 2.34 449y `unresolved` | -2.29 [-4.90, +0.39] MDE 4.04 178y `rejected` | +0.73 [-0.85, +2.30] MDE 2.36 596y `unresolved` | +0.87 [-0.81, +2.53] MDE 2.42 413y `unresolved` | -1.29 [-3.19, +0.42] MDE 2.67 243y `rejected` |
| `trend30_goldstack10` | +2.48 [+1.27, +3.83] MDE 1.65 25y `exploratory` | -0.02 [-2.15, +2.28] MDE 2.90 852883y `rejected` | +2.27 [+1.02, +3.63] MDE 1.67 31y `exploratory` | +2.28 [+0.86, +3.79] MDE 1.77 33y `exploratory` | +0.35 [-0.20, +0.94] MDE 0.64 190y `unresolved` |
| `trend30_cash10` | +1.44 [+0.34, +2.57] MDE 1.58 68y `unresolved` | +0.06 [-1.58, +1.81] MDE 2.38 88775y `unresolved` | +1.86 [+0.85, +2.93] MDE 1.49 36y `exploratory` | +1.83 [+0.75, +2.96] MDE 1.56 39y `exploratory` | -0.69 [-1.08, -0.27] MDE 0.59 42y `rejected` |
| `trend30_ltbond10` | +1.74 [+0.60, +2.90] MDE 1.64 51y `exploratory` | -0.27 [-2.24, +1.81] MDE 2.87 6401y `rejected` | +2.09 [+1.02, +3.19] MDE 1.57 32y `exploratory` | +2.06 [+0.95, +3.22] MDE 1.65 35y `exploratory` | -0.39 [-0.83, +0.05] MDE 0.67 166y `rejected` |

### The controls themselves: what the levered and volatility-matched comparators cost in drawdown (descriptive)

| arm | control | definition | arith pp/yr | log growth | vol % | max DD % | months under water |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | leverage_matched | 1.3216 x CORE, financed at the equity basis | 13.2691 | 11.0023 | 20.8986 | -61.52 | 81 |
| `base_trend30` | volatility_matched_expost | 1.0356 x CORE, financed at the equity basis (full-window volatility match) | 11.483 | 10.0888 | 16.3694 | -51.69 | 78 |
| `base_trend30` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.8748 | 10.4119 | 16.7136 | -51.07 | 79 |
| `base_no_trend` | leverage_matched | 1.0000 x CORE, financed at the equity basis | 11.2609 | 9.96 | 15.8063 | -50.33 | 73 |
| `base_no_trend` | volatility_matched_expost | 1.0000 x CORE + 0.0000 x CASH (full-window volatility match) | 11.2609 | 9.96 | 15.8063 | -50.33 | 73 |
| `base_no_trend` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.5601 | 10.2609 | 15.7819 | -50.33 | 73 |
| `trend30_bondstack20` | leverage_matched | 1.5216 x CORE, financed at the equity basis | 14.5179 | 11.5096 | 24.0669 | -67.36 | 85 |
| `trend30_bondstack20` | volatility_matched_expost | 1.0584 x CORE, financed at the equity basis (full-window volatility match) | 11.6255 | 10.1697 | 16.7307 | -52.54 | 78 |
| `trend30_bondstack20` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 12.0781 | 10.5381 | 17.1343 | -50.22 | 79 |
| `trend30_bondstack40` | leverage_matched | 1.7216 x CORE, financed at the equity basis | 15.7665 | 11.9059 | 27.2358 | -72.48 | 153 |
| `trend30_bondstack40` | volatility_matched_expost | 1.0968 x CORE, financed at the equity basis (full-window volatility match) | 11.8654 | 10.3027 | 17.3388 | -53.95 | 78 |
| `trend30_bondstack40` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 12.3906 | 10.7214 | 17.8227 | -50.45 | 79 |
| `trend20_rsbt10` | leverage_matched | 1.3144 x CORE, financed at the equity basis | 13.2241 | 10.982 | 20.7845 | -61.3 | 81 |
| `trend20_rsbt10` | volatility_matched_expost | 0.9416 x CORE + 0.0584 x CASH (full-window volatility match) | 10.8596 | 9.705 | 14.8817 | -48.06 | 67 |
| `trend20_rsbt10` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.248 | 10.0248 | 15.2631 | -46.59 | 78 |
| `ntsx100` | leverage_matched | 1.5000 x CORE, financed at the equity basis | 14.383 | 11.4601 | 23.7246 | -66.76 | 85 |
| `ntsx100` | volatility_matched_expost | 1.0169 x CORE, financed at the equity basis (full-window volatility match) | 11.3664 | 10.0216 | 16.0738 | -50.98 | 73 |
| `ntsx100` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.6618 | 10.2773 | 16.2827 | -48.55 | 72 |
| `trend30_goldstack10` | leverage_matched | 1.4016 x CORE, financed at the equity basis | 13.7686 | 11.2184 | 22.1658 | -63.95 | 84 |
| `trend30_goldstack10` | volatility_matched_expost | 1.0350 x CORE, financed at the equity basis (full-window volatility match) | 11.4795 | 10.0868 | 16.3605 | -51.67 | 78 |
| `trend30_goldstack10` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.8822 | 10.4213 | 16.7147 | -51.82 | 79 |
| `trend30_cash10` | leverage_matched | 1.2216 x CORE, financed at the equity basis | 12.6447 | 10.7078 | 19.3148 | -58.29 | 80 |
| `trend30_cash10` | volatility_matched_expost | 0.9388 x CORE + 0.0612 x CASH (full-window volatility match) | 10.8406 | 9.6927 | 14.838 | -47.95 | 67 |
| `trend30_cash10` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.2031 | 9.9926 | 15.1903 | -47.39 | 78 |
| `trend30_ltbond10` | leverage_matched | 1.3216 x CORE, financed at the equity basis | 13.2691 | 11.0023 | 20.8986 | -61.52 | 81 |
| `trend30_ltbond10` | volatility_matched_expost | 0.9485 x CORE + 0.0515 x CASH (full-window volatility match) | 10.9071 | 9.7356 | 14.9911 | -48.33 | 72 |
| `trend30_ltbond10` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.2966 | 10.0561 | 15.3718 | -46.86 | 78 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp | flat decade gap vs ref pp/yr | flat decade gap vs cheap pp/yr |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (3 ep.) | -- | +2.84 |
| `base_no_trend` | -0.444 (0.338) | 0.012 (0.23) | -3.47 (3 ep.) | -14.98 (3 ep.) | -2.84 | +0.00 |
| `trend30_bondstack20` | 0.023 (0.456) | -0.0248 (-1.52) | 1.97 (3 ep.) | -9.0 (3 ep.) | +0.83 | +3.66 |
| `trend30_bondstack40` | 0.046 (0.456) | -0.0495 (-1.52) | 3.94 (3 ep.) | -17.22 (3 ep.) | +1.65 | +4.49 |
| `trend20_rsbt10` | 0.907 (0.971) | -0.0124 (-1.52) | 4.83 (3 ep.) | -1.35 (3 ep.) | +0.94 | +3.78 |
| `ntsx100` | 0.463 (0.603) | -0.0622 (-0.75) | 5.89 (3 ep.) | -33.89 (3 ep.) | +0.16 | +2.99 |
| `trend30_goldstack10` | 0.159 (0.691) | 0.0061 (0.41) | 0.88 (3 ep.) | 6.82 (3 ep.) | +0.93 | +3.77 |
| `trend30_cash10` | 0.83 (1.0) | 0.0 (2.8) | 3.49 (3 ep.) | 2.87 (3 ep.) | +0.44 | +3.27 |
| `trend30_ltbond10` | 0.846 (0.971) | -0.0124 (-1.52) | 4.56 (3 ep.) | -1.59 (3 ep.) | +0.90 | +3.74 |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -34.29 (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `base_no_trend` | n/c | n/c | -45.03 (-4.35) | -50.33 (-4.47) | -20.22 (-1.59) | -46.54 (-12.24) | 54.6 (-31.41) | -24.86 (-1.29) |
| `trend30_bondstack20` | n/c | n/c | -38.37 (+2.31) | -44.4 (+1.46) | -16.48 (+2.14) | -36.83 (-2.54) | 63.93 (-22.07) | -25.95 (-2.38) |
| `trend30_bondstack40` | n/c | n/c | -36.02 (+4.65) | -43.02 (+2.84) | -14.31 (+4.32) | -39.3 (-5.00) | 44.04 (-41.96) | -28.27 (-4.70) |
| `trend20_rsbt10` | n/c | n/c | -34.75 (+5.92) | -40.49 (+5.37) | -15.43 (+3.20) | -29.91 (+4.38) | 76.18 (-9.83) | -22.18 (+1.39) |
| `ntsx100` | n/c | n/c | -33.62 (+7.06) | -42.14 (+3.72) | -11.73 (+6.90) | -48.75 (-14.45) | 4.71 (-81.30) | -29.5 (-5.93) |
| `trend30_goldstack10` | n/c | n/c | -39.76 (+0.92) | -44.42 (+1.44) | -18.34 (+0.29) | -28.62 (+5.68) | 101.14 (+15.13) | -23.92 (-0.35) |
| `trend30_cash10` | n/c | n/c | -36.38 (+4.30) | -41.66 (+4.20) | -16.66 (+1.97) | -29.0 (+5.29) | 86.92 (+0.92) | -21.16 (+2.40) |
| `trend30_ltbond10` | n/c | n/c | -35.09 (+5.59) | -40.82 (+5.04) | -15.57 (+3.06) | -30.31 (+3.98) | 76.04 (-9.96) | -22.36 (+1.21) |

### Bond-equity regime by era (the bond leg's realised history, to haircut against)

| era | window | months | bond-equity corr | bond excess pp/yr | bond vol % | equity excess pp/yr | trend excess pp/yr | cash pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_full | 1968-05..2025-05 | 685 | 0.095 | 2.98 | 10.45 | 6.9 | 7.77 | 4.39 |
| panel_first_half | 1968-05..1996-10 | 342 | 0.357 | 2.01 | 10.78 | 5.24 | 9.06 | 6.65 |
| panel_second_half | 1996-11..2025-05 | 343 | -0.179 | 3.94 | 10.13 | 8.55 | 6.49 | 2.14 |
| first_half | 1968-05..1977-03 | 107 | 0.35 | -0.25 | 8.75 | -1.34 | 10.97 | 5.66 |
| second_half | 1977-04..2025-05 | 578 | 0.051 | 3.57 | 10.74 | 8.42 | 7.18 | 4.16 |
| flat_equity_decade | 1999-03..2009-02 | 120 | -0.164 | 4.7 | 10.91 | -4.32 | 10.93 | 3.1 |
| bond_bull_market | 1981-10..2020-07 | 466 | -0.021 | 6.58 | 10.73 | 8.61 | 7.06 | 3.73 |
| before_bond_bull | 1968-05..1981-09 | 161 | 0.333 | -4.21 | 10.24 | 0.13 | 12.78 | 6.9 |
| after_bond_bull | 2020-08..2025-05 | 58 | 0.374 | -6.04 | 7.05 | 11.88 | -0.39 | 2.73 |
| positive_bond_equity_correlation | 1968-05..1997-12 | 356 | 0.367 | 2.27 | 10.72 | 5.98 | 9.77 | 6.59 |

### Financing sensitivity: gap against the reference arm at each basis (pp/yr), then against the cheap control


equity basis, bp: 62, 98, 130, 165, 200, 231
ordering against reference stable across the band: `False`

| arm | 62 | 98 | 130 | 165 | 200 | 231 | vs cheap at each point |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `base_trend30` | -- | -- | -- | -- | -- | -- | +2.13, +2.10, +2.06, +2.03, +1.99, +1.96 |
| `base_no_trend` | -2.13 | -2.10 | -2.06 | -2.03 | -1.99 | -1.96 | +0.00, +0.00, +0.00, +0.00, +0.00, +0.00 |
| `trend30_bondstack20` | +0.48 | +0.47 | +0.47 | +0.46 | +0.45 | +0.45 | +2.61, +2.57, +2.53, +2.49, +2.45, +2.41 |
| `trend30_bondstack40` | +0.96 | +0.95 | +0.93 | +0.92 | +0.91 | +0.89 | +3.09, +3.04, +3.00, +2.95, +2.90, +2.86 |
| `trend20_rsbt10` | -0.43 | -0.42 | -0.41 | -0.40 | -0.39 | -0.38 | +1.70, +1.67, +1.65, +1.63, +1.61, +1.58 |
| `ntsx100` | -1.29 | -1.26 | -1.23 | -1.19 | -1.16 | -1.13 | +0.84, +0.84, +0.84, +0.84, +0.84, +0.84 |
| `trend30_goldstack10` | +0.35 | +0.35 | +0.35 | +0.35 | +0.35 | +0.35 | +2.48, +2.45, +2.42, +2.38, +2.35, +2.32 |
| `trend30_cash10` | -0.69 | -0.69 | -0.69 | -0.69 | -0.69 | -0.69 | +1.44, +1.41, +1.38, +1.34, +1.31, +1.28 |
| `trend30_ltbond10` | -0.39 | -0.39 | -0.39 | -0.39 | -0.39 | -0.39 | +1.74, +1.70, +1.67, +1.63, +1.60, +1.57 |

treasury basis, bp: 0, 15, 30, 50
ordering against reference stable across the band: `True`

| arm | 0 | 15 | 30 | 50 | vs cheap at each point |
| --- | ---: | ---: | ---: | ---: | --- |
| `base_trend30` | -- | -- | -- | -- | +2.13, +2.13, +2.13, +2.13 |
| `base_no_trend` | -2.13 | -2.13 | -2.13 | -2.13 | +0.00, +0.00, +0.00, +0.00 |
| `trend30_bondstack20` | +0.51 | +0.48 | +0.45 | +0.41 | +2.64, +2.61, +2.58, +2.54 |
| `trend30_bondstack40` | +1.02 | +0.96 | +0.90 | +0.82 | +3.15, +3.09, +3.03, +2.95 |
| `trend20_rsbt10` | -0.42 | -0.43 | -0.45 | -0.47 | +1.71, +1.70, +1.68, +1.66 |
| `ntsx100` | -1.20 | -1.29 | -1.38 | -1.50 | +0.93, +0.84, +0.75, +0.63 |
| `trend30_goldstack10` | +0.35 | +0.35 | +0.35 | +0.35 | +2.48, +2.48, +2.48, +2.48 |
| `trend30_cash10` | -0.69 | -0.69 | -0.69 | -0.69 | +1.44, +1.44, +1.44, +1.44 |
| `trend30_ltbond10` | -0.39 | -0.39 | -0.39 | -0.39 | +1.74, +1.74, +1.74, +1.74 |

gold basis, bp: 0, 15, 30, 45, 60
ordering against reference stable across the band: `True`

| arm | 0 | 15 | 30 | 45 | 60 | vs cheap at each point |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `base_trend30` | -- | -- | -- | -- | -- | +2.13, +2.13, +2.13, +2.13, +2.13 |
| `base_no_trend` | -2.13 | -2.13 | -2.13 | -2.13 | -2.13 | +0.00, +0.00, +0.00, +0.00, +0.00 |
| `trend30_bondstack20` | +0.48 | +0.48 | +0.48 | +0.48 | +0.48 | +2.61, +2.61, +2.61, +2.61, +2.61 |
| `trend30_bondstack40` | +0.96 | +0.96 | +0.96 | +0.96 | +0.96 | +3.09, +3.09, +3.09, +3.09, +3.09 |
| `trend20_rsbt10` | -0.43 | -0.43 | -0.43 | -0.43 | -0.43 | +1.70, +1.70, +1.70, +1.70, +1.70 |
| `ntsx100` | -1.29 | -1.29 | -1.29 | -1.29 | -1.29 | +0.84, +0.84, +0.84, +0.84, +0.84 |
| `trend30_goldstack10` | +0.38 | +0.37 | +0.35 | +0.34 | +0.33 | +2.51, +2.50, +2.48, +2.47, +2.46 |
| `trend30_cash10` | -0.69 | -0.69 | -0.69 | -0.69 | -0.69 | +1.44, +1.44, +1.44, +1.44, +1.44 |
| `trend30_ltbond10` | -0.39 | -0.39 | -0.39 | -0.39 | -0.39 | +1.74, +1.74, +1.74, +1.74, +1.74 |

## Panel `secondary` (secondary): 1985-01..2025-12, 492 months, trend `aqr_tsmom`, bond `goyal_welch_ltr`

AQR TSMOM replaces the own book; 1985-01..2026-05 less the bond series' 2025-12 end.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | bond | gold | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 0.000 | 15.8952 | 14.5115 | 15.992 | 0.7972 | -46.71 | 41 | 1.0 | 3.376 |
| `base_no_trend` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 12.4393 | 11.1661 | 15.5104 | 0.5984 | -50.33 | 73 | 0.2962 | 1.0 |
| `trend30_bondstack20` | 1.522 | 1.022 | 0.300 | 0.200 | 0.000 | 0.000 | 16.7189 | 15.3028 | 16.1632 | 0.8399 | -45.28 | 39 | 1.3452 | 4.5412 |
| `trend30_bondstack40` | 1.722 | 1.022 | 0.300 | 0.400 | 0.000 | 0.000 | 17.5427 | 16.0537 | 16.576 | 0.8689 | -43.93 | 39 | 1.7859 | 6.029 |
| `trend20_rsbt10` | 1.314 | 0.914 | 0.300 | 0.100 | 0.000 | 0.000 | 15.3737 | 14.2363 | 14.4501 | 0.8465 | -41.38 | 39 | 0.8956 | 3.0237 |
| `ntsx100` | 1.500 | 0.900 | 0.000 | 0.600 | 0.000 | 0.000 | 14.0629 | 12.8662 | 14.9814 | 0.7285 | -42.14 | 50 | 0.5383 | 1.8171 |
| `trend30_goldstack10` | 1.402 | 1.012 | 0.300 | 0.000 | 0.090 | 0.000 | 16.1608 | 14.7953 | 15.8596 | 0.8204 | -45.31 | 40 | 1.1272 | 3.8053 |
| `trend30_cash10` | 1.222 | 0.922 | 0.300 | 0.000 | 0.000 | 0.100 | 14.9671 | 13.8259 | 14.4922 | 0.8159 | -42.53 | 40 | 0.7688 | 2.5954 |
| `trend30_ltbond10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 0.000 | 15.4312 | 14.2775 | 14.5569 | 0.8443 | -41.71 | 39 | 0.9099 | 3.0718 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +3.46 [+2.31, +4.63] MDE 1.64 9y `exploratory` | +0.67 [-1.33, +2.67] MDE 2.72 673y `unresolved` | +3.19 [+2.02, +4.39] MDE 1.65 11y `exploratory` | +3.10 [+1.94, +4.28] MDE 1.75 12y `exploratory` | -- |
| `base_no_trend` | identical | identical | identical | -0.00 [-0.00, +0.00] MDE 0.00 165y `rejected` | -3.46 [-4.63, -2.31] MDE 1.64 9y `rejected` |
| `trend30_bondstack20` | +4.28 [+2.84, +5.71] MDE 2.05 9y `exploratory` | -0.24 [-3.14, +2.75] MDE 4.11 12399y `rejected` | +3.92 [+2.45, +5.39] MDE 2.07 11y `exploratory` | +3.64 [+2.23, +5.06] MDE 2.11 13y `exploratory` | +0.82 [+0.28, +1.36] MDE 0.88 46y `unresolved` |
| `trend30_bondstack40` | +5.10 [+3.25, +6.93] MDE 2.69 11y `exploratory` | -1.14 [-5.03, +2.94] MDE 5.64 996y `rejected` | +4.51 [+2.60, +6.39] MDE 2.74 15y `exploratory` | +4.03 [+2.18, +5.88] MDE 2.74 18y `exploratory` | +1.65 [+0.57, +2.73] MDE 1.75 46y `unresolved` |
| `trend20_rsbt10` | +2.93 [+1.52, +4.35] MDE 1.95 18y `exploratory` | +0.21 [-2.22, +2.69] MDE 3.39 10437y `unresolved` | +3.57 [+2.26, +4.88] MDE 1.82 11y `exploratory` | +3.38 [+2.12, +4.68] MDE 1.89 12y `exploratory` | -0.52 [-1.08, +0.08] MDE 0.86 113y `rejected` |
| `ntsx100` | +1.62 [-0.08, +3.32] MDE 2.74 117y `unresolved` | -2.71 [-5.87, +0.74] MDE 4.93 136y `rejected` | +1.94 [+0.29, +3.60] MDE 2.68 78y `unresolved` | +1.50 [-0.33, +3.34] MDE 2.68 122y `unresolved` | -1.83 [-3.52, -0.09] MDE 2.82 97y `rejected` |
| `trend30_goldstack10` | +3.72 [+2.60, +4.86] MDE 1.77 9y `exploratory` | +0.24 [-2.07, +2.62] MDE 3.32 7548y `unresolved` | +3.53 [+2.37, +4.69] MDE 1.79 11y `exploratory` | +3.40 [+2.18, +4.69] MDE 1.92 12y `exploratory` | +0.27 [-0.22, +0.75] MDE 0.61 215y `unresolved` |
| `trend30_cash10` | +2.53 [+1.24, +3.83] MDE 1.77 20y `exploratory` | +0.61 [-1.40, +2.61] MDE 2.72 817y `unresolved` | +3.14 [+1.97, +4.34] MDE 1.65 11y `exploratory` | +3.04 [+1.87, +4.23] MDE 1.75 13y `exploratory` | -0.93 [-1.37, -0.44] MDE 0.68 22y `rejected` |
| `trend30_ltbond10` | +2.99 [+1.60, +4.40] MDE 1.93 17y `exploratory` | +0.21 [-2.23, +2.68] MDE 3.39 10930y `unresolved` | +3.56 [+2.26, +4.87] MDE 1.82 11y `exploratory` | +3.38 [+2.12, +4.68] MDE 1.89 12y `exploratory` | -0.46 [-0.99, +0.11] MDE 0.82 129y `rejected` |

### The controls themselves: what the levered and volatility-matched comparators cost in drawdown (descriptive)

| arm | control | definition | arith pp/yr | log growth | vol % | max DD % | months under water |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | leverage_matched | 1.3216 x CORE, financed at the equity basis | 15.2237 | 13.0026 | 20.4931 | -61.52 | 81 |
| `base_trend30` | volatility_matched_expost | 1.0311 x CORE, financed at the equity basis (full-window volatility match) | 12.7082 | 11.3553 | 15.9914 | -51.52 | 73 |
| `base_trend30` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 12.1641 | 10.8797 | 15.621 | -54.66 | 78 |
| `base_no_trend` | leverage_matched | 1.0000 x CORE, financed at the equity basis | 12.4393 | 11.1661 | 15.5104 | -50.33 | 73 |
| `base_no_trend` | volatility_matched_expost | 1.0000 x CORE + 0.0000 x CASH (full-window volatility match) | 12.4393 | 11.1661 | 15.5104 | -50.33 | 73 |
| `base_no_trend` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 12.0455 | 10.864 | 14.9902 | -50.33 | 73 |
| `trend30_bondstack20` | leverage_matched | 1.5216 x CORE, financed at the equity basis | 16.9553 | 14.0055 | 23.5927 | -67.36 | 85 |
| `trend30_bondstack20` | volatility_matched_expost | 1.0421 x CORE, financed at the equity basis (full-window volatility match) | 12.8037 | 11.4219 | 16.1624 | -51.93 | 78 |
| `trend30_bondstack20` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 12.3636 | 11.0678 | 15.6894 | -53.33 | 78 |
| `trend30_bondstack40` | leverage_matched | 1.7216 x CORE, financed at the equity basis | 18.6867 | 14.8982 | 26.6927 | -72.48 | 153 |
| `trend30_bondstack40` | volatility_matched_expost | 1.0687 x CORE, financed at the equity basis (full-window volatility match) | 13.0341 | 11.5812 | 16.5746 | -52.92 | 78 |
| `trend30_bondstack40` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 12.7122 | 11.3626 | 16.0123 | -52.77 | 78 |
| `trend20_rsbt10` | leverage_matched | 1.3144 x CORE, financed at the equity basis | 15.1614 | 12.9645 | 20.3816 | -61.3 | 81 |
| `trend20_rsbt10` | volatility_matched_expost | 0.9316 x CORE + 0.0684 x CASH (full-window volatility match) | 11.8048 | 10.6987 | 14.4516 | -47.67 | 67 |
| `trend20_rsbt10` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.3346 | 10.2886 | 14.0844 | -50.09 | 73 |
| `ntsx100` | leverage_matched | 1.5000 x CORE, financed at the equity basis | 16.7683 | 13.9024 | 23.258 | -66.76 | 85 |
| `ntsx100` | volatility_matched_expost | 0.9659 x CORE + 0.0341 x CASH (full-window volatility match) | 12.1227 | 10.9344 | 14.9821 | -49.02 | 72 |
| `ntsx100` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.9308 | 10.8508 | 14.3226 | -46.3 | 72 |
| `trend30_goldstack10` | leverage_matched | 1.4016 x CORE, financed at the equity basis | 15.9164 | 13.4168 | 21.7329 | -63.95 | 84 |
| `trend30_goldstack10` | volatility_matched_expost | 1.0225 x CORE, financed at the equity basis (full-window volatility match) | 12.6342 | 11.3035 | 15.8591 | -51.19 | 73 |
| `trend30_goldstack10` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 12.0903 | 10.8169 | 15.555 | -55.05 | 78 |
| `trend30_cash10` | leverage_matched | 1.2216 x CORE, financed at the equity basis | 14.358 | 12.4608 | 18.9435 | -58.29 | 80 |
| `trend30_cash10` | volatility_matched_expost | 0.9344 x CORE + 0.0656 x CASH (full-window volatility match) | 11.83 | 10.7175 | 14.4937 | -47.78 | 67 |
| `trend30_cash10` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.3074 | 10.2481 | 14.1758 | -51.15 | 73 |
| `trend30_ltbond10` | leverage_matched | 1.3216 x CORE, financed at the equity basis | 15.2237 | 13.0026 | 20.4931 | -61.52 | 81 |
| `trend30_ltbond10` | volatility_matched_expost | 0.9385 x CORE + 0.0615 x CASH (full-window volatility match) | 11.8687 | 10.7463 | 14.5582 | -47.94 | 67 |
| `trend30_ltbond10` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.396 | 10.3348 | 14.1873 | -50.36 | 73 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp | flat decade gap vs ref pp/yr | flat decade gap vs cheap pp/yr |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (1 ep.) | -- | +4.52 |
| `base_no_trend` | -0.565 (0.327) | 0.0239 (0.44) | -4.36 (3 ep.) | -6.83 (1 ep.) | -4.52 | +0.00 |
| `trend30_bondstack20` | 0.217 (0.551) | -0.0254 (-1.33) | 2.01 (3 ep.) | -2.52 (1 ep.) | +0.83 | +5.35 |
| `trend30_bondstack40` | 0.433 (0.551) | -0.0509 (-1.33) | 4.02 (3 ep.) | -4.98 (1 ep.) | +1.65 | +6.17 |
| `trend20_rsbt10` | 0.996 (0.98) | -0.0127 (-1.33) | 4.91 (3 ep.) | 1.47 (1 ep.) | +0.94 | +5.46 |
| `ntsx100` | 0.914 (0.571) | -0.0524 (-0.64) | 5.01 (3 ep.) | -11.47 (1 ep.) | -1.53 | +2.99 |
| `trend30_goldstack10` | 0.225 (0.714) | -0.0002 (-0.02) | 0.88 (3 ep.) | -0.38 (1 ep.) | +0.93 | +5.45 |
| `trend30_cash10` | 0.823 (1.0) | 0.0 (3.86) | 3.54 (3 ep.) | 2.55 (1 ep.) | +0.44 | +4.96 |
| `trend30_ltbond10` | 0.936 (0.98) | -0.0127 (-1.33) | 4.63 (3 ep.) | 1.28 (1 ep.) | +0.90 | +5.42 |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -37.96 (+0.00) | -46.71 (+0.00) | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `base_no_trend` | n/c | n/c | -45.03 (-7.07) | -50.33 (-3.63) | -20.22 (-2.38) | n/c | n/c | -24.86 (-6.83) |
| `trend30_bondstack20` | n/c | n/c | -35.51 (+2.45) | -45.28 (+1.43) | -15.69 (+2.15) | n/c | n/c | -20.55 (-2.52) |
| `trend30_bondstack40` | n/c | n/c | -33.01 (+4.95) | -43.93 (+2.77) | -13.51 (+4.33) | n/c | n/c | -23.0 (-4.98) |
| `trend20_rsbt10` | n/c | n/c | -31.77 (+6.19) | -41.38 (+5.32) | -14.63 (+3.21) | n/c | n/c | -16.56 (+1.47) |
| `ntsx100` | n/c | n/c | -33.62 (+4.34) | -42.14 (+4.56) | -11.73 (+6.11) | n/c | n/c | -29.5 (-11.47) |
| `trend30_goldstack10` | n/c | n/c | -37.0 (+0.96) | -45.31 (+1.40) | -17.55 (+0.30) | n/c | n/c | -18.41 (-0.38) |
| `trend30_cash10` | n/c | n/c | -33.49 (+4.47) | -42.53 (+4.17) | -15.87 (+1.97) | n/c | n/c | -15.48 (+2.55) |
| `trend30_ltbond10` | n/c | n/c | -32.12 (+5.84) | -41.71 (+5.00) | -14.78 (+3.06) | n/c | n/c | -16.74 (+1.28) |

### Bond-equity regime by era (the bond leg's realised history, to haircut against)

| era | window | months | bond-equity corr | bond excess pp/yr | bond vol % | equity excess pp/yr | trend excess pp/yr | cash pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_full | 1985-01..2025-12 | 492 | -0.041 | 4.69 | 10.01 | 9.31 | 12.02 | 3.16 |
| panel_first_half | 1985-01..2005-06 | 246 | 0.116 | 6.27 | 9.61 | 8.49 | 18.21 | 4.67 |
| panel_second_half | 2005-07..2025-12 | 246 | -0.186 | 3.11 | 10.38 | 10.13 | 5.82 | 1.65 |
| second_half | 1985-01..2025-05 | 485 | -0.041 | 4.73 | 10.07 | 9.11 | 12.07 | 3.15 |
| flat_equity_decade | 1999-03..2009-02 | 120 | -0.164 | 4.7 | 10.91 | -4.32 | 16.56 | 3.1 |
| bond_bull_market | 1985-01..2020-07 | 427 | -0.081 | 6.19 | 10.35 | 8.73 | 13.55 | 3.2 |
| after_bond_bull | 2020-08..2025-05 | 58 | 0.374 | -6.04 | 7.05 | 11.88 | 1.14 | 2.73 |
| positive_bond_equity_correlation | 1985-01..1997-12 | 156 | 0.358 | 6.81 | 9.88 | 11.67 | 18.15 | 5.53 |

### Financing sensitivity: gap against the reference arm at each basis (pp/yr), then against the cheap control


equity basis, bp: 62, 98, 130, 165, 200, 231
ordering against reference stable across the band: `True`

| arm | 62 | 98 | 130 | 165 | 200 | 231 | vs cheap at each point |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `base_trend30` | -- | -- | -- | -- | -- | -- | +3.46, +3.42, +3.39, +3.35, +3.32, +3.29 |
| `base_no_trend` | -3.46 | -3.42 | -3.39 | -3.35 | -3.32 | -3.29 | +0.00, +0.00, +0.00, +0.00, +0.00, +0.00 |
| `trend30_bondstack20` | +0.82 | +0.82 | +0.81 | +0.80 | +0.80 | +0.79 | +4.28, +4.24, +4.20, +4.16, +4.12, +4.08 |
| `trend30_bondstack40` | +1.65 | +1.63 | +1.62 | +1.61 | +1.59 | +1.58 | +5.10, +5.05, +5.01, +4.96, +4.91, +4.87 |
| `trend20_rsbt10` | -0.52 | -0.51 | -0.50 | -0.49 | -0.48 | -0.47 | +2.93, +2.91, +2.89, +2.87, +2.84, +2.82 |
| `ntsx100` | -1.83 | -1.80 | -1.76 | -1.73 | -1.70 | -1.66 | +1.62, +1.62, +1.62, +1.62, +1.62, +1.62 |
| `trend30_goldstack10` | +0.27 | +0.27 | +0.27 | +0.27 | +0.27 | +0.27 | +3.72, +3.69, +3.65, +3.62, +3.58, +3.55 |
| `trend30_cash10` | -0.93 | -0.93 | -0.93 | -0.93 | -0.93 | -0.93 | +2.53, +2.49, +2.46, +2.43, +2.39, +2.36 |
| `trend30_ltbond10` | -0.46 | -0.46 | -0.46 | -0.46 | -0.46 | -0.46 | +2.99, +2.96, +2.92, +2.89, +2.85, +2.82 |

treasury basis, bp: 0, 15, 30, 50
ordering against reference stable across the band: `True`

| arm | 0 | 15 | 30 | 50 | vs cheap at each point |
| --- | ---: | ---: | ---: | ---: | --- |
| `base_trend30` | -- | -- | -- | -- | +3.46, +3.46, +3.46, +3.46 |
| `base_no_trend` | -3.46 | -3.46 | -3.46 | -3.46 | +0.00, +0.00, +0.00, +0.00 |
| `trend30_bondstack20` | +0.85 | +0.82 | +0.79 | +0.75 | +4.31, +4.28, +4.25, +4.21 |
| `trend30_bondstack40` | +1.71 | +1.65 | +1.59 | +1.51 | +5.16, +5.10, +5.04, +4.96 |
| `trend20_rsbt10` | -0.51 | -0.52 | -0.54 | -0.56 | +2.95, +2.93, +2.92, +2.90 |
| `ntsx100` | -1.74 | -1.83 | -1.92 | -2.04 | +1.71, +1.62, +1.53, +1.41 |
| `trend30_goldstack10` | +0.27 | +0.27 | +0.27 | +0.27 | +3.72, +3.72, +3.72, +3.72 |
| `trend30_cash10` | -0.93 | -0.93 | -0.93 | -0.93 | +2.53, +2.53, +2.53, +2.53 |
| `trend30_ltbond10` | -0.46 | -0.46 | -0.46 | -0.46 | +2.99, +2.99, +2.99, +2.99 |

gold basis, bp: 0, 15, 30, 45, 60
ordering against reference stable across the band: `True`

| arm | 0 | 15 | 30 | 45 | 60 | vs cheap at each point |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `base_trend30` | -- | -- | -- | -- | -- | +3.46, +3.46, +3.46, +3.46, +3.46 |
| `base_no_trend` | -3.46 | -3.46 | -3.46 | -3.46 | -3.46 | +0.00, +0.00, +0.00, +0.00, +0.00 |
| `trend30_bondstack20` | +0.82 | +0.82 | +0.82 | +0.82 | +0.82 | +4.28, +4.28, +4.28, +4.28, +4.28 |
| `trend30_bondstack40` | +1.65 | +1.65 | +1.65 | +1.65 | +1.65 | +5.10, +5.10, +5.10, +5.10, +5.10 |
| `trend20_rsbt10` | -0.52 | -0.52 | -0.52 | -0.52 | -0.52 | +2.93, +2.93, +2.93, +2.93, +2.93 |
| `ntsx100` | -1.83 | -1.83 | -1.83 | -1.83 | -1.83 | +1.62, +1.62, +1.62, +1.62, +1.62 |
| `trend30_goldstack10` | +0.29 | +0.28 | +0.27 | +0.25 | +0.24 | +3.75, +3.74, +3.72, +3.71, +3.69 |
| `trend30_cash10` | -0.93 | -0.93 | -0.93 | -0.93 | -0.93 | +2.53, +2.53, +2.53, +2.53, +2.53 |
| `trend30_ltbond10` | -0.46 | -0.46 | -0.46 | -0.46 | -0.46 | +2.99, +2.99, +2.99, +2.99, +2.99 |

## Panel `tertiary_check` (check): 2003-02..2025-12, 275 months, trend `aqr_tsmom`, bond `goyal_welch_ltr`

A CHECK, NOT A TEST: 280 months from 2003-02, on which the modelled TIPS series exists, so that a TIPS-stack arm can at least be described.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | bond | gold | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 0.000 | 14.278 | 13.0687 | 15.0676 | 0.8394 | -46.71 | 39 | 1.0 | 1.382 |
| `base_no_trend` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 12.3619 | 11.1876 | 14.9356 | 0.7188 | -50.33 | 51 | 0.7236 | 1.0 |
| `trend30_bondstack20` | 1.522 | 1.022 | 0.300 | 0.200 | 0.000 | 0.000 | 14.8728 | 13.6733 | 14.9584 | 0.885 | -45.28 | 37 | 1.1177 | 1.5447 |
| `trend30_tipsstack20` | 1.522 | 1.022 | 0.300 | 0.200 | 0.000 | 0.000 | 14.5919 | 13.3484 | 15.261 | 0.8491 | -46.2 | 37 | 1.0468 | 1.4466 |
| `trend30_goldstack10` | 1.402 | 1.012 | 0.300 | 0.000 | 0.090 | 0.000 | 15.0826 | 13.8548 | 15.1347 | 0.8891 | -45.31 | 37 | 1.1645 | 1.6093 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.92 [+0.60, +3.25] MDE 2.26 32y `unresolved` | -1.34 [-3.81, +1.33] MDE 3.77 181y `rejected` | +1.83 [+0.50, +3.17] MDE 2.27 35y `unresolved` | +1.83 [+0.34, +3.43] MDE 2.57 40y `unresolved` | -- |
| `base_no_trend` | identical | identical | identical | -0.00 [-0.00, +0.00] MDE 0.00 889y `rejected` | -1.92 [-3.25, -0.60] MDE 2.26 32y `rejected` |
| `trend30_bondstack20` | +2.51 [+0.90, +4.16] MDE 2.79 28y `unresolved` | -2.77 [-6.44, +1.27] MDE 5.70 97y `rejected` | +2.50 [+0.89, +4.14] MDE 2.79 29y `unresolved` | +2.50 [+0.63, +4.48] MDE 3.04 30y `unresolved` | +0.59 [-0.16, +1.35] MDE 1.22 97y `unresolved` |
| `trend30_tipsstack20` | +2.23 [+0.85, +3.64] MDE 2.36 26y `unresolved` | -3.05 [-6.46, +0.76] MDE 5.24 68y `rejected` | +2.01 [+0.60, +3.45] MDE 2.38 32y `unresolved` | +1.95 [+0.35, +3.67] MDE 2.62 36y `unresolved` | +0.31 [-0.24, +0.86] MDE 0.69 110y `unresolved` |
| `trend30_goldstack10` | +2.72 [+1.30, +4.15] MDE 2.53 20y `exploratory` | -1.34 [-4.28, +1.92] MDE 4.53 260y `rejected` | +2.59 [+1.14, +4.04] MDE 2.54 22y `exploratory` | +2.59 [+0.93, +4.38] MDE 2.86 24y `unresolved` | +0.80 [+0.21, +1.39] MDE 0.88 27y `unresolved` |

### The controls themselves: what the levered and volatility-matched comparators cost in drawdown (descriptive)

| arm | control | definition | arith pp/yr | log growth | vol % | max DD % | months under water |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | leverage_matched | 1.3216 x CORE, financed at the equity basis | 15.6169 | 13.5702 | 19.7399 | -61.52 | 58 |
| `base_trend30` | volatility_matched_expost | 1.0088 x CORE, financed at the equity basis (full-window volatility match) | 12.4513 | 11.2563 | 15.0676 | -50.67 | 52 |
| `base_trend30` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.2635 | 9.9378 | 15.9331 | -54.66 | 62 |
| `base_no_trend` | leverage_matched | 1.0000 x CORE, financed at the equity basis | 12.3619 | 11.1876 | 14.9356 | -50.33 | 51 |
| `base_no_trend` | volatility_matched_expost | 1.0000 x CORE + 0.0000 x CASH (full-window volatility match) | 12.3619 | 11.1876 | 14.9356 | -50.33 | 51 |
| `base_no_trend` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.607 | 10.3392 | 15.5902 | -50.33 | 51 |
| `trend30_bondstack20` | leverage_matched | 1.5216 x CORE, financed at the equity basis | 17.6411 | 14.9273 | 22.7281 | -67.36 | 62 |
| `trend30_bondstack20` | volatility_matched_expost | 1.0015 x CORE, financed at the equity basis (full-window volatility match) | 12.3773 | 11.1995 | 14.9584 | -50.39 | 51 |
| `trend30_bondstack20` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.1649 | 9.8812 | 15.687 | -53.33 | 62 |
| `trend30_tipsstack20` | leverage_matched | 1.5216 x CORE, financed at the equity basis | 17.6411 | 14.9273 | 22.7281 | -67.36 | 62 |
| `trend30_tipsstack20` | volatility_matched_expost | 1.0218 x CORE, financed at the equity basis (full-window volatility match) | 12.5824 | 11.3567 | 15.261 | -51.17 | 52 |
| `trend30_tipsstack20` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.3948 | 10.043 | 16.0973 | -54.48 | 62 |
| `trend30_goldstack10` | leverage_matched | 1.4016 x CORE, financed at the equity basis | 16.4266 | 14.1246 | 20.9352 | -63.95 | 58 |
| `trend30_goldstack10` | volatility_matched_expost | 1.0133 x CORE, financed at the equity basis (full-window volatility match) | 12.4967 | 11.2912 | 15.1347 | -50.84 | 52 |
| `trend30_goldstack10` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.2634 | 9.9286 | 15.9919 | -55.05 | 62 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp | flat decade gap vs ref pp/yr | flat decade gap vs cheap pp/yr |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (2 ep.) | 0.0 (1 ep.) | -- | +4.37 |
| `base_no_trend` | -0.378 (0.444) | 0.0041 (0.08) | -3.0 (2 ep.) | -6.83 (1 ep.) | -4.37 | +0.00 |
| `trend30_bondstack20` | 0.36 (0.593) | 0.0015 (0.05) | 1.79 (2 ep.) | -2.52 (1 ep.) | +0.79 | +5.16 |
| `trend30_tipsstack20` | -0.048 (0.519) | 0.0284 (1.25) | 0.35 (2 ep.) | -2.58 (1 ep.) | +0.47 | +4.84 |
| `trend30_goldstack10` | 0.221 (0.704) | -0.0093 (-0.46) | 0.85 (2 ep.) | -0.38 (1 ep.) | +1.30 | +5.67 |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | n/c | -46.71 (+0.00) | -17.84 (+0.00) | n/c | n/c | -18.03 (+0.00) |
| `base_no_trend` | n/c | n/c | n/c | -50.33 (-3.63) | -20.22 (-2.38) | n/c | n/c | -24.86 (-6.83) |
| `trend30_bondstack20` | n/c | n/c | n/c | -45.28 (+1.43) | -15.69 (+2.15) | n/c | n/c | -20.55 (-2.52) |
| `trend30_tipsstack20` | n/c | n/c | n/c | -46.2 (+0.50) | -17.64 (+0.20) | n/c | n/c | -20.61 (-2.58) |
| `trend30_goldstack10` | n/c | n/c | n/c | -45.31 (+1.40) | -17.55 (+0.30) | n/c | n/c | -18.41 (-0.38) |

### Bond-equity regime by era (the bond leg's realised history, to haircut against)

| era | window | months | bond-equity corr | bond excess pp/yr | bond vol % | equity excess pp/yr | trend excess pp/yr | cash pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_full | 2003-02..2025-12 | 275 | -0.176 | 3.55 | 10.45 | 10.77 | 6.78 | 1.62 |
| panel_first_half | 2003-02..2014-06 | 137 | -0.265 | 5.37 | 11.86 | 9.73 | 9.86 | 1.42 |
| panel_second_half | 2014-07..2025-12 | 138 | -0.067 | 1.73 | 8.85 | 11.81 | 3.72 | 1.82 |
| second_half | 2003-02..2025-05 | 268 | -0.178 | 3.58 | 10.58 | 10.45 | 6.73 | 1.55 |
| flat_equity_decade | 2003-02..2009-02 | 73 | -0.037 | 4.53 | 12.41 | -1.18 | 15.82 | 2.62 |
| bond_bull_market | 2003-02..2020-07 | 210 | -0.292 | 6.24 | 11.26 | 10.05 | 8.28 | 1.23 |
| after_bond_bull | 2020-08..2025-05 | 58 | 0.374 | -6.04 | 7.05 | 11.88 | 1.14 | 2.73 |

### Financing sensitivity: gap against the reference arm at each basis (pp/yr), then against the cheap control


equity basis, bp: 62, 98, 130, 165, 200, 231
ordering against reference stable across the band: `True`

| arm | 62 | 98 | 130 | 165 | 200 | 231 | vs cheap at each point |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `base_trend30` | -- | -- | -- | -- | -- | -- | +1.92, +1.88, +1.85, +1.81, +1.78, +1.75 |
| `base_no_trend` | -1.92 | -1.88 | -1.85 | -1.81 | -1.78 | -1.75 | +0.00, +0.00, +0.00, +0.00, +0.00, +0.00 |
| `trend30_bondstack20` | +0.59 | +0.59 | +0.58 | +0.57 | +0.57 | +0.56 | +2.51, +2.47, +2.43, +2.39, +2.35, +2.31 |
| `trend30_tipsstack20` | +0.31 | +0.31 | +0.30 | +0.29 | +0.29 | +0.28 | +2.23, +2.19, +2.15, +2.11, +2.07, +2.03 |
| `trend30_goldstack10` | +0.80 | +0.80 | +0.80 | +0.80 | +0.80 | +0.80 | +2.72, +2.69, +2.65, +2.62, +2.58, +2.55 |

treasury basis, bp: 0, 15, 30, 50
ordering against reference stable across the band: `True`

| arm | 0 | 15 | 30 | 50 | vs cheap at each point |
| --- | ---: | ---: | ---: | ---: | --- |
| `base_trend30` | -- | -- | -- | -- | +1.92, +1.92, +1.92, +1.92 |
| `base_no_trend` | -1.92 | -1.92 | -1.92 | -1.92 | +0.00, +0.00, +0.00, +0.00 |
| `trend30_bondstack20` | +0.62 | +0.59 | +0.56 | +0.52 | +2.54, +2.51, +2.48, +2.44 |
| `trend30_tipsstack20` | +0.31 | +0.31 | +0.31 | +0.31 | +2.23, +2.23, +2.23, +2.23 |
| `trend30_goldstack10` | +0.80 | +0.80 | +0.80 | +0.80 | +2.72, +2.72, +2.72, +2.72 |

gold basis, bp: 0, 15, 30, 45, 60
ordering against reference stable across the band: `True`

| arm | 0 | 15 | 30 | 45 | 60 | vs cheap at each point |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `base_trend30` | -- | -- | -- | -- | -- | +1.92, +1.92, +1.92, +1.92, +1.92 |
| `base_no_trend` | -1.92 | -1.92 | -1.92 | -1.92 | -1.92 | +0.00, +0.00, +0.00, +0.00, +0.00 |
| `trend30_bondstack20` | +0.59 | +0.59 | +0.59 | +0.59 | +0.59 | +2.51, +2.51, +2.51, +2.51, +2.51 |
| `trend30_tipsstack20` | +0.31 | +0.31 | +0.31 | +0.31 | +0.31 | +2.23, +2.23, +2.23, +2.23, +2.23 |
| `trend30_goldstack10` | +0.83 | +0.82 | +0.80 | +0.79 | +0.78 | +2.75, +2.73, +2.72, +2.71, +2.69 |

## Panel `bond_series_sensitivity` (sensitivity): 1953-05..2025-05, 865 months, trend `own_4_asset_book`, bond `gs10_par_bond`

The primary arms re-run from 1953-05 with a 10-year par bond modelled from FRED GS10 in place of `ltr`, and again on the same window with `ltr`, so the duration of the bond leg can be read as a difference on one window.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | bond | gold | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 0.000 | 13.5702 | 12.2691 | 15.6879 | 0.6043 | -45.86 | 51 | 1.0 | 3.2391 |
| `base_no_trend` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 11.7813 | 10.5894 | 15.0804 | 0.5101 | -50.33 | 73 | 0.3087 | 1.0 |
| `trend30_bondstack20` | 1.522 | 1.022 | 0.300 | 0.200 | 0.000 | 0.000 | 13.7414 | 12.4094 | 15.8807 | 0.6077 | -44.09 | 50 | 1.1136 | 3.6071 |
| `trend30_bondstack40` | 1.722 | 1.022 | 0.300 | 0.400 | 0.000 | 0.000 | 13.9125 | 12.5336 | 16.1726 | 0.6073 | -42.29 | 41 | 1.2267 | 3.9734 |
| `trend20_rsbt10` | 1.314 | 0.914 | 0.300 | 0.100 | 0.000 | 0.000 | 12.8896 | 11.8178 | 14.2092 | 0.6194 | -40.34 | 50 | 0.7526 | 2.4378 |
| `ntsx100` | 1.500 | 0.900 | 0.000 | 0.600 | 0.000 | 0.000 | 11.6029 | 10.4967 | 14.5479 | 0.5166 | -46.67 | 51 | 0.3087 | 1.0 |
| `trend30_cash10` | 1.222 | 0.922 | 0.300 | 0.000 | 0.000 | 0.100 | 12.798 | 11.7236 | 14.2298 | 0.6121 | -41.66 | 50 | 0.7008 | 2.2699 |
| `trend30_ltbond10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 0.000 | 12.9358 | 11.8486 | 14.3138 | 0.6181 | -40.66 | 50 | 0.7677 | 2.4866 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.79 [+0.92, +2.57] MDE 1.29 37y `exploratory` | -0.49 [-1.95, +0.83] MDE 2.03 1215y `rejected` | +1.50 [+0.62, +2.35] MDE 1.30 54y `exploratory` | +1.60 [+0.82, +2.69] MDE 1.37 51y `exploratory` | -- |
| `base_no_trend` | identical | identical | identical | -0.00 [-0.00, +0.00] MDE 0.00 227y `rejected` | -1.79 [-2.57, -0.92] MDE 1.29 37y `rejected` |
| `trend30_bondstack20` | +1.96 [+1.00, +2.76] MDE 1.34 34y `exploratory` | -1.74 [-3.84, +0.11] MDE 2.85 193y `rejected` | +1.58 [+0.57, +2.47] MDE 1.35 52y `exploratory` | +1.69 [+0.78, +2.85] MDE 1.42 49y `exploratory` | +0.17 [-0.17, +0.55] MDE 0.42 438y `unresolved` |
| `trend30_bondstack40` | +2.13 [+0.99, +3.12] MDE 1.52 37y `exploratory` | -2.99 [-5.83, -0.42] MDE 3.78 115y `rejected` | +1.62 [+0.42, +2.68] MDE 1.53 64y `exploratory` | +1.75 [+0.54, +3.10] MDE 1.60 58y `exploratory` | +0.34 [-0.34, +1.10] MDE 0.84 438y `unresolved` |
| `trend20_rsbt10` | +1.11 [+0.10, +2.01] MDE 1.38 112y `unresolved` | -1.12 [-2.85, +0.46] MDE 2.42 334y `rejected` | +1.55 [+0.61, +2.34] MDE 1.31 51y `exploratory` | +1.65 [+0.83, +2.79] MDE 1.38 48y `exploratory` | -0.68 [-1.10, -0.27] MDE 0.55 47y `rejected` |
| `ntsx100` | -0.18 [-1.24, +1.09] MDE 1.30 3837y `rejected` | -3.73 [-6.06, -1.42] MDE 3.11 50y `rejected` | +0.09 [-0.92, +1.35] MDE 1.27 13020y `unresolved` | +0.24 [-0.90, +1.43] MDE 1.31 2140y `unresolved` | -1.97 [-3.24, -0.28] MDE 1.87 65y `rejected` |
| `trend30_cash10` | +1.02 [+0.02, +1.95] MDE 1.37 130y `unresolved` | -0.56 [-2.01, +0.77] MDE 2.03 958y `rejected` | +1.45 [+0.56, +2.31] MDE 1.30 58y `exploratory` | +1.55 [+0.74, +2.65] MDE 1.37 54y `exploratory` | -0.77 [-1.14, -0.47] MDE 0.50 30y `rejected` |
| `trend30_ltbond10` | +1.15 [+0.17, +2.03] MDE 1.37 101y `unresolved` | -1.13 [-2.85, +0.45] MDE 2.42 331y `rejected` | +1.55 [+0.61, +2.33] MDE 1.31 52y `exploratory` | +1.65 [+0.82, +2.79] MDE 1.38 48y `exploratory` | -0.63 [-1.02, -0.25] MDE 0.52 48y `rejected` |

### The controls themselves: what the levered and volatility-matched comparators cost in drawdown (descriptive)

| arm | control | definition | arith pp/yr | log growth | vol % | max DD % | months under water |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | leverage_matched | 1.3216 x CORE, financed at the equity basis | 14.0646 | 11.9901 | 19.9423 | -61.52 | 81 |
| `base_trend30` | volatility_matched_expost | 1.0403 x CORE, financed at the equity basis (full-window volatility match) | 12.0674 | 10.7785 | 15.6892 | -51.87 | 78 |
| `base_trend30` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.3675 | 10.0075 | 16.1257 | -51.07 | 79 |
| `base_no_trend` | leverage_matched | 1.0000 x CORE, financed at the equity basis | 11.7813 | 10.5894 | 15.0804 | -50.33 | 73 |
| `base_no_trend` | volatility_matched_expost | 1.0000 x CORE + 0.0000 x CASH (full-window volatility match) | 11.7813 | 10.5894 | 15.0804 | -50.33 | 73 |
| `base_no_trend` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.1507 | 9.9441 | 15.2089 | -50.33 | 73 |
| `trend30_bondstack20` | leverage_matched | 1.5216 x CORE, financed at the equity basis | 15.4844 | 12.7334 | 22.9672 | -67.36 | 85 |
| `trend30_bondstack20` | volatility_matched_expost | 1.0531 x CORE, financed at the equity basis (full-window volatility match) | 12.1582 | 10.8377 | 15.8825 | -52.35 | 78 |
| `trend30_bondstack20` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.455 | 10.0595 | 16.3354 | -50.82 | 79 |
| `trend30_bondstack40` | leverage_matched | 1.7216 x CORE, financed at the equity basis | 16.9041 | 13.3765 | 25.9928 | -72.48 | 153 |
| `trend30_bondstack40` | volatility_matched_expost | 1.0724 x CORE, financed at the equity basis (full-window volatility match) | 12.2956 | 10.9266 | 16.175 | -53.06 | 78 |
| `trend30_bondstack40` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.5798 | 10.1304 | 16.6484 | -50.92 | 80 |
| `trend20_rsbt10` | leverage_matched | 1.3144 x CORE, financed at the equity basis | 14.0135 | 11.9615 | 19.8334 | -61.3 | 81 |
| `trend20_rsbt10` | volatility_matched_expost | 0.9422 x CORE + 0.0578 x CASH (full-window volatility match) | 11.3352 | 10.2756 | 14.2075 | -48.09 | 67 |
| `trend20_rsbt10` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 10.7165 | 9.5928 | 14.6448 | -46.95 | 78 |
| `ntsx100` | leverage_matched | 1.5000 x CORE, financed at the equity basis | 15.3311 | 12.6579 | 22.6405 | -66.76 | 85 |
| `ntsx100` | volatility_matched_expost | 0.9647 x CORE + 0.0353 x CASH (full-window volatility match) | 11.5086 | 10.3985 | 14.5468 | -48.97 | 72 |
| `ntsx100` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 10.8415 | 9.7077 | 14.747 | -47.15 | 73 |
| `trend30_cash10` | leverage_matched | 1.2216 x CORE, financed at the equity basis | 13.3546 | 11.5814 | 18.4302 | -58.29 | 80 |
| `trend30_cash10` | volatility_matched_expost | 0.9436 x CORE + 0.0564 x CASH (full-window volatility match) | 11.3457 | 10.2831 | 14.2281 | -48.14 | 67 |
| `trend30_cash10` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 10.723 | 9.5973 | 14.6581 | -47.39 | 78 |
| `trend30_ltbond10` | leverage_matched | 1.3216 x CORE, financed at the equity basis | 14.0646 | 11.9901 | 19.9423 | -61.52 | 81 |
| `trend30_ltbond10` | volatility_matched_expost | 0.9492 x CORE + 0.0508 x CASH (full-window volatility match) | 11.3887 | 10.3137 | 14.3122 | -48.36 | 72 |
| `trend30_ltbond10` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 10.7635 | 9.6237 | 14.75 | -47.22 | 78 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp | flat decade gap vs ref pp/yr | flat decade gap vs cheap pp/yr |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (3 ep.) | -- | +2.84 |
| `base_no_trend` | -0.383 (0.349) | 0.0184 (0.38) | -3.47 (3 ep.) | -14.98 (3 ep.) | -2.84 | +0.00 |
| `trend30_bondstack20` | -0.003 (0.5) | -0.0162 (-1.55) | 1.87 (3 ep.) | -7.32 (3 ep.) | +0.58 | +3.41 |
| `trend30_bondstack40` | -0.005 (0.5) | -0.0325 (-1.55) | 3.78 (3 ep.) | -14.14 (3 ep.) | +1.15 | +3.99 |
| `trend20_rsbt10` | 0.842 (1.0) | -0.0081 (-1.55) | 4.78 (3 ep.) | -0.47 (3 ep.) | +0.82 | +3.65 |
| `ntsx100` | 0.398 (0.616) | -0.0303 (-0.52) | 5.61 (3 ep.) | -30.22 (3 ep.) | -0.59 | +2.25 |
| `trend30_cash10` | 0.782 (1.0) | 0.0 (2.67) | 3.49 (3 ep.) | 2.87 (3 ep.) | +0.44 | +3.27 |
| `trend30_ltbond10` | 0.785 (1.0) | -0.0081 (-1.55) | 4.51 (3 ep.) | -0.71 (3 ep.) | +0.78 | +3.61 |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -34.29 (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `base_no_trend` | n/c | n/c | -45.03 (-4.35) | -50.33 (-4.47) | -20.22 (-1.59) | -46.54 (-12.24) | 54.6 (-31.41) | -24.86 (-1.29) |
| `trend30_bondstack20` | n/c | n/c | -38.37 (+2.31) | -44.09 (+1.77) | -17.09 (+1.53) | -36.04 (-1.74) | 68.59 (-17.42) | -26.36 (-2.80) |
| `trend30_bondstack40` | n/c | n/c | -36.0 (+4.68) | -42.29 (+3.57) | -15.55 (+3.08) | -37.75 (-3.45) | 52.54 (-33.47) | -29.08 (-5.51) |
| `trend20_rsbt10` | n/c | n/c | -34.75 (+5.92) | -40.34 (+5.52) | -15.74 (+2.89) | -29.48 (+4.82) | 78.6 (-7.41) | -22.39 (+1.17) |
| `ntsx100` | n/c | n/c | -33.66 (+7.02) | -41.05 (+4.81) | -13.62 (+5.01) | -46.67 (-12.37) | 14.81 (-71.19) | -30.66 (-7.09) |
| `trend30_cash10` | n/c | n/c | -36.38 (+4.30) | -41.66 (+4.20) | -16.66 (+1.97) | -29.0 (+5.29) | 86.92 (+0.92) | -21.16 (+2.40) |
| `trend30_ltbond10` | n/c | n/c | -35.09 (+5.59) | -40.66 (+5.20) | -15.88 (+2.75) | -29.88 (+4.41) | 78.46 (-7.54) | -22.57 (+1.00) |

### Bond-equity regime by era (the bond leg's realised history, to haircut against)

| era | window | months | bond-equity corr | bond excess pp/yr | bond vol % | equity excess pp/yr | trend excess pp/yr | cash pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_full | 1953-05..2025-05 | 865 | 0.124 | 1.43 | 6.39 | 7.75 | 6.57 | 4.06 |
| panel_first_half | 1953-05..1989-04 | 432 | 0.269 | 0.22 | 6.56 | 6.8 | 6.7 | 5.36 |
| panel_second_half | 1989-05..2025-05 | 433 | -0.03 | 2.63 | 6.21 | 8.7 | 6.44 | 2.76 |
| first_half | 1953-05..1977-03 | 287 | 0.264 | -0.31 | 4.34 | 6.4 | 5.35 | 3.86 |
| second_half | 1977-04..2025-05 | 578 | 0.086 | 2.29 | 7.19 | 8.42 | 7.18 | 4.16 |
| flat_equity_decade | 1999-03..2009-02 | 120 | -0.125 | 3.46 | 6.79 | -4.32 | 10.93 | 3.1 |
| bond_bull_market | 1981-10..2020-07 | 466 | 0.035 | 4.75 | 6.78 | 8.61 | 7.06 | 3.73 |
| before_bond_bull | 1953-05..1981-09 | 341 | 0.24 | -1.75 | 5.55 | 5.87 | 7.09 | 4.73 |
| after_bond_bull | 2020-08..2025-05 | 58 | 0.309 | -6.54 | 6.51 | 11.88 | -0.39 | 2.73 |
| positive_bond_equity_correlation | 1966-01..1997-12 | 384 | 0.328 | 1.54 | 7.32 | 5.86 | 9.34 | 6.44 |

## Panel `bond_series_sensitivity_ltr` (sensitivity): 1953-05..2025-05, 865 months, trend `own_4_asset_book`, bond `goyal_welch_ltr`

The `ltr` companion to the GS10 sensitivity, on the identical window.

### Arms: notional, growth, drawdown (descriptive)

| arm | gross | equity | trend | bond | gold | cash | arith pp/yr | log growth | vol % | Sharpe | max DD % | months under water | TW ratio vs ref | TW ratio vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1.322 | 1.022 | 0.300 | 0.000 | 0.000 | 0.000 | 13.5702 | 12.2691 | 15.6879 | 0.6043 | -45.86 | 51 | 1.0 | 3.2391 |
| `base_no_trend` | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 11.7813 | 10.5894 | 15.0804 | 0.5101 | -50.33 | 73 | 0.3087 | 1.0 |
| `trend30_bondstack20` | 1.522 | 1.022 | 0.300 | 0.200 | 0.000 | 0.000 | 13.8931 | 12.5482 | 15.966 | 0.6139 | -44.4 | 50 | 1.231 | 3.9874 |
| `trend30_bondstack40` | 1.722 | 1.022 | 0.300 | 0.400 | 0.000 | 0.000 | 14.2161 | 12.7907 | 16.4644 | 0.615 | -43.02 | 41 | 1.478 | 4.7873 |
| `trend20_rsbt10` | 1.314 | 0.914 | 0.300 | 0.100 | 0.000 | 0.000 | 12.9654 | 11.8895 | 14.2394 | 0.6234 | -40.49 | 49 | 0.7927 | 2.5675 |
| `ntsx100` | 1.500 | 0.900 | 0.000 | 0.600 | 0.000 | 0.000 | 12.0583 | 10.8626 | 15.1454 | 0.5263 | -49.1 | 50 | 0.4047 | 1.311 |
| `trend30_cash10` | 1.222 | 0.922 | 0.300 | 0.000 | 0.000 | 0.100 | 12.798 | 11.7236 | 14.2298 | 0.6121 | -41.66 | 50 | 0.7008 | 2.2699 |
| `trend30_ltbond10` | 1.322 | 0.922 | 0.300 | 0.100 | 0.000 | 0.000 | 13.0117 | 11.9204 | 14.3437 | 0.622 | -40.82 | 50 | 0.8085 | 2.6189 |

### Arithmetic gaps against each control: gap [95% interval] MDE years-to-distinguish status

| arm | vs cheap | vs leverage-matched | vs vol-matched (ex post) | vs vol-matched (ex ante, from month 37) | vs reference |
| --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.79 [+1.02, +2.78] MDE 1.29 37y `exploratory` | -0.49 [-1.80, +0.92] MDE 2.03 1215y `rejected` | +1.50 [+0.72, +2.55] MDE 1.30 54y `exploratory` | +1.60 [+0.65, +2.52] MDE 1.37 51y `exploratory` | -- |
| `base_no_trend` | identical | identical | identical | -0.00 [-0.00, +0.00] MDE 0.00 227y `rejected` | -1.79 [-2.78, -1.02] MDE 1.29 37y `rejected` |
| `trend30_bondstack20` | +2.11 [+1.31, +3.08] MDE 1.46 34y `exploratory` | -1.59 [-3.63, +0.35] MDE 2.91 241y `rejected` | +1.69 [+0.95, +2.71] MDE 1.47 54y `exploratory` | +1.78 [+0.74, +2.85] MDE 1.53 51y `exploratory` | +0.32 [-0.11, +0.72] MDE 0.63 277y `unresolved` |
| `trend30_bondstack40` | +2.43 [+1.44, +3.58] MDE 1.84 41y `exploratory` | -2.69 [-5.32, -0.07] MDE 3.93 154y `rejected` | +1.78 [+0.76, +2.91] MDE 1.87 79y `unresolved` | +1.87 [+0.67, +3.17] MDE 1.94 74y `unresolved` | +0.65 [-0.22, +1.45] MDE 1.27 277y `unresolved` |
| `trend20_rsbt10` | +1.18 [+0.37, +2.22] MDE 1.42 103y `unresolved` | -1.05 [-2.78, +0.66] MDE 2.44 391y `rejected` | +1.61 [+0.87, +2.61] MDE 1.35 50y `exploratory` | +1.70 [+0.75, +2.69] MDE 1.42 48y `exploratory` | -0.60 [-0.98, -0.23] MDE 0.60 71y `rejected` |
| `ntsx100` | +0.28 [-0.91, +1.58] MDE 1.93 3486y `unresolved` | -3.27 [-5.37, -1.22] MDE 3.42 79y `rejected` | +0.25 [-0.94, +1.56] MDE 1.93 4425y `unresolved` | +0.39 [-0.84, +1.99] MDE 1.99 1805y `unresolved` | -1.51 [-3.01, -0.06] MDE 2.28 164y `rejected` |
| `trend30_cash10` | +1.02 [+0.26, +2.10] MDE 1.37 130y `unresolved` | -0.56 [-1.86, +0.86] MDE 2.03 958y `rejected` | +1.45 [+0.67, +2.51] MDE 1.30 58y `exploratory` | +1.55 [+0.60, +2.46] MDE 1.37 54y `exploratory` | -0.77 [-1.12, -0.42] MDE 0.50 30y `rejected` |
| `trend30_ltbond10` | +1.23 [+0.43, +2.26] MDE 1.41 94y `unresolved` | -1.05 [-2.79, +0.65] MDE 2.44 388y `rejected` | +1.61 [+0.86, +2.60] MDE 1.35 51y `exploratory` | +1.70 [+0.75, +2.69] MDE 1.42 48y `exploratory` | -0.56 [-0.91, -0.22] MDE 0.57 75y `rejected` |

### The controls themselves: what the levered and volatility-matched comparators cost in drawdown (descriptive)

| arm | control | definition | arith pp/yr | log growth | vol % | max DD % | months under water |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | leverage_matched | 1.3216 x CORE, financed at the equity basis | 14.0646 | 11.9901 | 19.9423 | -61.52 | 81 |
| `base_trend30` | volatility_matched_expost | 1.0403 x CORE, financed at the equity basis (full-window volatility match) | 12.0674 | 10.7785 | 15.6892 | -51.87 | 78 |
| `base_trend30` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.3675 | 10.0075 | 16.1257 | -51.07 | 79 |
| `base_no_trend` | leverage_matched | 1.0000 x CORE, financed at the equity basis | 11.7813 | 10.5894 | 15.0804 | -50.33 | 73 |
| `base_no_trend` | volatility_matched_expost | 1.0000 x CORE + 0.0000 x CASH (full-window volatility match) | 11.7813 | 10.5894 | 15.0804 | -50.33 | 73 |
| `base_no_trend` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.1507 | 9.9441 | 15.2089 | -50.33 | 73 |
| `trend30_bondstack20` | leverage_matched | 1.5216 x CORE, financed at the equity basis | 15.4844 | 12.7334 | 22.9672 | -67.36 | 85 |
| `trend30_bondstack20` | volatility_matched_expost | 1.0587 x CORE, financed at the equity basis (full-window volatility match) | 12.1983 | 10.8638 | 15.9679 | -52.56 | 78 |
| `trend30_bondstack20` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.5122 | 10.0945 | 16.4528 | -50.22 | 79 |
| `trend30_bondstack40` | leverage_matched | 1.7216 x CORE, financed at the equity basis | 16.9041 | 13.3765 | 25.9928 | -72.48 | 153 |
| `trend30_bondstack40` | volatility_matched_expost | 1.0918 x CORE, financed at the equity basis (full-window volatility match) | 12.4329 | 11.0146 | 16.4675 | -53.77 | 78 |
| `trend30_bondstack40` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.7506 | 10.2308 | 17.0225 | -50.45 | 79 |
| `trend20_rsbt10` | leverage_matched | 1.3144 x CORE, financed at the equity basis | 14.0135 | 11.9615 | 19.8334 | -61.3 | 81 |
| `trend20_rsbt10` | volatility_matched_expost | 0.9442 x CORE + 0.0558 x CASH (full-window volatility match) | 11.3506 | 10.2866 | 14.2377 | -48.17 | 67 |
| `trend20_rsbt10` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 10.7403 | 9.609 | 14.6893 | -46.59 | 78 |
| `ntsx100` | leverage_matched | 1.5000 x CORE, financed at the equity basis | 15.3311 | 12.6579 | 22.6405 | -66.76 | 85 |
| `ntsx100` | volatility_matched_expost | 1.0043 x CORE, financed at the equity basis (full-window volatility match) | 11.812 | 10.6098 | 15.1456 | -50.5 | 73 |
| `ntsx100` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 11.117 | 9.8623 | 15.5032 | -48.55 | 72 |
| `trend30_cash10` | leverage_matched | 1.2216 x CORE, financed at the equity basis | 13.3546 | 11.5814 | 18.4302 | -58.29 | 80 |
| `trend30_cash10` | volatility_matched_expost | 0.9436 x CORE + 0.0564 x CASH (full-window volatility match) | 11.3457 | 10.2831 | 14.2281 | -48.14 | 67 |
| `trend30_cash10` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 10.723 | 9.5973 | 14.6581 | -47.39 | 78 |
| `trend30_ltbond10` | leverage_matched | 1.3216 x CORE, financed at the equity basis | 14.0646 | 11.9901 | 19.9423 | -61.52 | 81 |
| `trend30_ltbond10` | volatility_matched_expost | 0.9511 x CORE + 0.0489 x CASH (full-window volatility match) | 11.404 | 10.3246 | 14.3422 | -48.44 | 72 |
| `trend30_ltbond10` | volatility_matched_exante | CORE scaled each month to the trailing 36-month volatility ratio, remainder in CASH, excess above one financed at the equity basis | 10.7871 | 9.6397 | 14.7941 | -46.86 | 78 |

### Crisis behaviour against the reference arm (descriptive)

| arm | worst-decile offset pp/month (hit rate) | convexity kappa (t) | deflationary episodes mean pp | inflation episodes mean pp | flat decade gap vs ref pp/yr | flat decade gap vs cheap pp/yr |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | -- | -- | 0.0 (3 ep.) | 0.0 (3 ep.) | -- | +2.84 |
| `base_no_trend` | -0.383 (0.349) | 0.0184 (0.38) | -3.47 (3 ep.) | -14.98 (3 ep.) | -2.84 | +0.00 |
| `trend30_bondstack20` | 0.013 (0.477) | -0.0221 (-1.51) | 1.97 (3 ep.) | -9.0 (3 ep.) | +0.83 | +3.66 |
| `trend30_bondstack40` | 0.025 (0.477) | -0.0442 (-1.51) | 3.94 (3 ep.) | -17.22 (3 ep.) | +1.65 | +4.49 |
| `trend20_rsbt10` | 0.849 (0.977) | -0.0111 (-1.51) | 4.83 (3 ep.) | -1.35 (3 ep.) | +0.94 | +3.78 |
| `ntsx100` | 0.444 (0.593) | -0.0479 (-0.64) | 5.89 (3 ep.) | -33.89 (3 ep.) | +0.16 | +2.99 |
| `trend30_cash10` | 0.782 (1.0) | 0.0 (2.67) | 3.49 (3 ep.) | 2.87 (3 ep.) | +0.44 | +3.27 |
| `trend30_ltbond10` | 0.792 (0.977) | -0.0111 (-1.51) | 4.56 (3 ep.) | -1.59 (3 ep.) | +0.90 | +3.74 |

### Crisis episodes: arm cumulative return % (offset against reference, pp); * marks partial coverage, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | n/c | n/c | -40.68 (+0.00) | -45.86 (+0.00) | -18.63 (+0.00) | -34.29 (+0.00) | 86.01 (+0.00) | -23.57 (+0.00) |
| `base_no_trend` | n/c | n/c | -45.03 (-4.35) | -50.33 (-4.47) | -20.22 (-1.59) | -46.54 (-12.24) | 54.6 (-31.41) | -24.86 (-1.29) |
| `trend30_bondstack20` | n/c | n/c | -38.37 (+2.31) | -44.4 (+1.46) | -16.48 (+2.14) | -36.83 (-2.54) | 63.93 (-22.07) | -25.95 (-2.38) |
| `trend30_bondstack40` | n/c | n/c | -36.02 (+4.65) | -43.02 (+2.84) | -14.31 (+4.32) | -39.3 (-5.00) | 44.04 (-41.96) | -28.27 (-4.70) |
| `trend20_rsbt10` | n/c | n/c | -34.75 (+5.92) | -40.49 (+5.37) | -15.43 (+3.20) | -29.91 (+4.38) | 76.18 (-9.83) | -22.18 (+1.39) |
| `ntsx100` | n/c | n/c | -33.62 (+7.06) | -42.14 (+3.72) | -11.73 (+6.90) | -48.75 (-14.45) | 4.71 (-81.30) | -29.5 (-5.93) |
| `trend30_cash10` | n/c | n/c | -36.38 (+4.30) | -41.66 (+4.20) | -16.66 (+1.97) | -29.0 (+5.29) | 86.92 (+0.92) | -21.16 (+2.40) |
| `trend30_ltbond10` | n/c | n/c | -35.09 (+5.59) | -40.82 (+5.04) | -15.57 (+3.06) | -30.31 (+3.98) | 76.04 (-9.96) | -22.36 (+1.21) |

### Bond-equity regime by era (the bond leg's realised history, to haircut against)

| era | window | months | bond-equity corr | bond excess pp/yr | bond vol % | equity excess pp/yr | trend excess pp/yr | cash pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| panel_full | 1953-05..2025-05 | 865 | 0.078 | 2.19 | 9.59 | 7.75 | 6.57 | 4.06 |
| panel_first_half | 1953-05..1989-04 | 432 | 0.263 | 0.03 | 9.38 | 6.8 | 6.7 | 5.36 |
| panel_second_half | 1989-05..2025-05 | 433 | -0.098 | 4.34 | 9.77 | 8.7 | 6.44 | 2.76 |
| first_half | 1953-05..1977-03 | 287 | 0.175 | -0.6 | 6.67 | 6.4 | 5.35 | 3.86 |
| second_half | 1977-04..2025-05 | 578 | 0.051 | 3.57 | 10.74 | 8.42 | 7.18 | 4.16 |
| flat_equity_decade | 1999-03..2009-02 | 120 | -0.164 | 4.7 | 10.91 | -4.32 | 10.93 | 3.1 |
| bond_bull_market | 1981-10..2020-07 | 466 | -0.021 | 6.58 | 10.73 | 8.61 | 7.06 | 3.73 |
| before_bond_bull | 1953-05..1981-09 | 341 | 0.22 | -2.42 | 7.94 | 5.87 | 7.09 | 4.73 |
| after_bond_bull | 2020-08..2025-05 | 58 | 0.374 | -6.04 | 7.05 | 11.88 | -0.39 | 2.73 |
| positive_bond_equity_correlation | 1966-01..1997-12 | 384 | 0.36 | 1.7 | 10.53 | 5.86 | 9.34 | 6.44 |
