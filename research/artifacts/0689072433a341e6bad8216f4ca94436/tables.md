# Experiment 021: leveraged ETFs and the 200-day moving average

Run `0689072433a341e6bad8216f4ca94436`; specification hash `81e165c6501ff385119b9fb234775980c723d8d328aa42ad66bbd9c37a41bc59`.

FUNDS ARE MODELLED EXPOSURES, NOT FUND RETURNS: RF + L (Mkt - RF) less fee and spread, compounded daily. The signal index is the TOTAL-RETURN index because the library has no daily price index; the price proxy is a sensitivity. The financing spread is an assumption at 40 bp with an 80 bp stress case. The HFEA bond leg is monthly and contains the 1981-2020 bull market. Every timed mean gap was predicted `unresolved` before the run.

Base settings: spread 40 bp, stress 80 bp, fees 3/89/89/100 bp (1x/2x/3x/TMF-like), 1.3x control 15.9 bp, one-way cost 10 bp, lookback 200 days, band 0.01, lag 1 day(s). Gap cells read: point [95% HAC] floor at 80% power, years to distinguish, falsifier status.

## Window `full_daily` (daily): 1927-03-05..2026-06-30, 26073 rows, 99.3 years


### Arms (descriptive)

| arm | CAGR % | arith % | vol % | Sharpe | max DD % | under water (yrs) | in market | round trips/yr | terminal $1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hold_1x` | 10.17 | 11.23 | 17.51 | 0.462 | -84.09 | 17.6 | -- | -- | 15120.06 |
| `hold_2x` | 12.65 | 18.08 | 35.02 | 0.427 | -98.42 | 24.3 | -- | -- | 137173.73 |
| `hold_3x` | 12.54 | 25.80 | 52.53 | 0.431 | -99.89 | 28.2 | -- | -- | 124750.59 |
| `lev_130` | 11.42 | 13.41 | 22.76 | 0.451 | -91.68 | 18.3 | -- | -- | 46123.18 |
| `sma200_1x` | 10.01 | 10.22 | 11.62 | 0.609 | -41.10 | 5.0 | 0.725 | 2.83 | 13036.69 |
| `sma200_1x_band` | 10.13 | 10.34 | 11.67 | 0.616 | -39.36 | 4.9 | 0.721 | 1.26 | 14520.35 |
| `sma200_2x` | 15.30 | 16.97 | 23.24 | 0.595 | -68.27 | 5.1 | 0.725 | 2.83 | 1380471.00 |
| `sma200_2x_band` | 15.17 | 16.89 | 23.34 | 0.589 | -66.87 | 5.5 | 0.721 | 1.26 | 1241741.32 |
| `sma200_3x` | 19.88 | 24.35 | 34.85 | 0.608 | -84.55 | 6.1 | 0.725 | 2.83 | 66322471.90 |
| `sma200_3x_band` | 19.47 | 24.07 | 35.02 | 0.598 | -86.97 | 8.3 | 0.721 | 1.26 | 47269679.23 |
| `control: cheap` | 10.17 | 11.23 | 17.51 | 0.462 | -84.09 | 17.6 | -- | -- | 15120.06 |
| `control: leverage_matched_130` | 11.42 | 13.41 | 22.76 | 0.451 | -91.68 | 18.3 | -- | -- | 46123.18 |

### Gaps: point [95% HAC] floor years status

| arm | vs cheap 1x | vs 1.3x | vs exposure-matched |
| --- | --- | --- | --- |
| `hold_1x` | identical | -2.19 [-3.27, -1.10] MDE 1.55 45y `rejected` | identical |
| `hold_2x` | +6.86 [+3.24, +10.47] MDE 5.17 51y `exploratory` | +4.67 [+2.14, +7.20] MDE 3.62 54y `exploratory` | identical |
| `hold_3x` | +14.57 [+7.34, +21.80] MDE 10.33 45y `exploratory` | +12.39 [+6.24, +18.53] MDE 8.78 45y `exploratory` | identical |
| `lev_130` | +2.19 [+1.10, +3.27] MDE 1.55 45y `exploratory` | identical | -- |
| `sma200_1x` | -1.01 [-3.60, +1.59] MDE 3.71 1330y `rejected` | -3.19 [-6.67, +0.28] MDE 4.97 233y `rejected` | +1.22 [-0.76, +3.19] MDE 2.82 530y `unresolved` |
| `sma200_1x_band` | -0.89 [-3.47, +1.68] MDE 3.68 1682y `rejected` | -3.08 [-6.53, +0.37] MDE 4.93 249y `rejected` | +1.37 [-0.59, +3.32] MDE 2.80 417y `unresolved` |
| `sma200_2x` | +5.74 [+2.27, +9.21] MDE 4.96 73y `exploratory` | +3.56 [-0.15, +7.26] MDE 5.30 221y `unresolved` | +3.00 [-0.93, +6.93] MDE 5.62 350y `unresolved` |
| `sma200_2x_band` | +5.66 [+2.17, +9.15] MDE 4.99 75y `exploratory` | +3.48 [-0.22, +7.18] MDE 5.29 230y `unresolved` | +2.98 [-0.93, +6.88] MDE 5.58 351y `unresolved` |
| `sma200_3x` | +13.12 [+7.74, +18.50] MDE 7.69 32y `exploratory` | +10.93 [+5.74, +16.13] MDE 7.42 45y `exploratory` | +4.79 [-1.10, +10.67] MDE 8.41 310y `unresolved` |
| `sma200_3x_band` | +12.84 [+7.39, +18.29] MDE 7.79 34y `exploratory` | +10.66 [+5.41, +15.90] MDE 7.49 47y `exploratory` | +4.60 [-1.26, +10.45] MDE 8.36 332y `unresolved` |

### Sensitivities: point gap pp/yr against each control (base / stress spread / other)

| arm | control | base | 80 bp spread | sensitivities |
| --- | --- | ---: | ---: | --- |
| `hold_1x` | leverage_matched_130 | -2.19 | -2.07 | lag0 -2.19, price_proxy_2.5pct -2.19, cost0bp -2.19, cost5bp -2.19, cost25bp -2.19 |
| `hold_2x` | cheap | +6.86 | +6.46 | lag0 +6.86, price_proxy_2.5pct +6.86, cost0bp +6.86, cost5bp +6.86, cost25bp +6.86 |
| `hold_2x` | leverage_matched_130 | +4.67 | +4.39 | lag0 +4.67, price_proxy_2.5pct +4.67, cost0bp +4.67, cost5bp +4.67, cost25bp +4.67 |
| `hold_3x` | cheap | +14.57 | +13.77 | lag0 +14.57, price_proxy_2.5pct +14.57, cost0bp +14.57, cost5bp +14.57, cost25bp +14.57 |
| `hold_3x` | leverage_matched_130 | +12.39 | +11.71 | lag0 +12.39, price_proxy_2.5pct +12.39, cost0bp +12.39, cost5bp +12.39, cost25bp +12.39 |
| `lev_130` | cheap | +2.19 | +2.07 | lag0 +2.19, price_proxy_2.5pct +2.19, cost0bp +2.19, cost5bp +2.19, cost25bp +2.19 |
| `sma200_1x` | cheap | -1.01 | -1.01 | lag0 -0.23, price_proxy_2.5pct -0.55, cost0bp -0.44, cost5bp -0.72, cost25bp -1.86 |
| `sma200_1x` | leverage_matched_130 | -3.19 | -3.07 | lag0 -2.42, price_proxy_2.5pct -2.73, cost0bp -2.63, cost5bp -2.91, cost25bp -4.04 |
| `sma200_1x` | exposure_matched | +1.22 | +1.22 | lag0 +2.00, price_proxy_2.5pct +1.94, cost0bp +1.79, cost5bp +1.50, cost25bp +0.37 |
| `sma200_1x_band` | cheap | -0.89 | -0.89 | lag0 -0.35, price_proxy_2.5pct -0.98, cost0bp -0.64, cost5bp -0.77, cost25bp -1.27 |
| `sma200_1x_band` | leverage_matched_130 | -3.08 | -2.96 | lag0 -2.54, price_proxy_2.5pct -3.17, cost0bp -2.83, cost5bp -2.95, cost25bp -3.46 |
| `sma200_1x_band` | exposure_matched | +1.37 | +1.37 | lag0 +1.90, price_proxy_2.5pct +1.53, cost0bp +1.62, cost5bp +1.49, cost25bp +0.99 |
| `sma200_2x` | cheap | +5.74 | +5.45 | lag0 +7.30, price_proxy_2.5pct +6.70, cost0bp +6.31, cost5bp +6.03, cost25bp +4.89 |
| `sma200_2x` | leverage_matched_130 | +3.56 | +3.39 | lag0 +5.11, price_proxy_2.5pct +4.51, cost0bp +4.12, cost5bp +3.84, cost25bp +2.71 |
| `sma200_2x` | exposure_matched | +3.00 | +3.00 | lag0 +4.55, price_proxy_2.5pct +4.44, cost0bp +3.57, cost5bp +3.28, cost25bp +2.15 |
| `sma200_2x_band` | cheap | +5.66 | +5.37 | lag0 +6.74, price_proxy_2.5pct +5.53, cost0bp +5.92, cost5bp +5.79, cost25bp +5.29 |
| `sma200_2x_band` | leverage_matched_130 | +3.48 | +3.31 | lag0 +4.56, price_proxy_2.5pct +3.35, cost0bp +3.73, cost5bp +3.60, cost25bp +3.10 |
| `sma200_2x_band` | exposure_matched | +2.98 | +2.98 | lag0 +4.06, price_proxy_2.5pct +3.31, cost0bp +3.23, cost5bp +3.10, cost25bp +2.60 |
| `sma200_3x` | cheap | +13.12 | +12.54 | lag0 +15.45, price_proxy_2.5pct +14.54, cost0bp +13.68, cost5bp +13.40, cost25bp +12.27 |
| `sma200_3x` | leverage_matched_130 | +10.93 | +10.47 | lag0 +13.26, price_proxy_2.5pct +12.35, cost0bp +11.50, cost5bp +11.22, cost25bp +10.08 |
| `sma200_3x` | exposure_matched | +4.79 | +4.78 | lag0 +7.12, price_proxy_2.5pct +6.94, cost0bp +5.35, cost5bp +5.07, cost25bp +3.94 |
| `sma200_3x_band` | cheap | +12.84 | +12.26 | lag0 +14.46, price_proxy_2.5pct +12.65, cost0bp +13.09, cost5bp +12.97, cost25bp +12.46 |
| `sma200_3x_band` | leverage_matched_130 | +10.66 | +10.20 | lag0 +12.27, price_proxy_2.5pct +10.46, cost0bp +10.91, cost5bp +10.78, cost25bp +10.28 |
| `sma200_3x_band` | exposure_matched | +4.60 | +4.59 | lag0 +6.21, price_proxy_2.5pct +5.10, cost0bp +4.85, cost5bp +4.72, cost25bp +4.22 |

### Crisis episodes: cumulative % (peak-to-trough %); * partial, n/c not covered

| arm | crash_1929 | october_1987 | dotcom_2000 | gfc_2008 | covid_2020 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `hold_1x` | -83.91 (-84.03) | -28.31 (-30.98) | -49.2 (-49.26) | -54.23 (-54.58) | -33.82 (-34.22) | -24.87 (-25.45) |
| `hold_2x` | -98.38 (-98.39) | -52.96 (-55.67) | -80.47 (-80.51) | -83.58 (-83.83) | -59.24 (-59.73) | -47.15 (-47.9) |
| `hold_3x` | -99.89 (-99.89) | -72.21 (-74.15) | -93.37 (-93.39) | -95.15 (-95.27) | -76.79 (-77.2) | -64.47 (-65.22) |
| `lev_130` | -91.55 (-91.59) | -36.24 (-39.08) | -61.15 (-61.21) | -65.56 (-65.91) | -42.33 (-42.78) | -31.96 (-32.59) |
| `sma200_1x` | -19.21 (-20.28) | -26.25 (-28.07) | -22.98 (-23.78) | -14.95 (-16.27) | -10.58 (-12.8) | -13.22 (-14.29) |
| `sma200_1x_band` | -23.64 (-25.73) | -26.25 (-28.07) | -25.03 (-25.97) | -11.95 (-14.25) | -20.17 (-20.73) | -13.12 (-14.4) |
| `sma200_2x` | -38.11 (-39.14) | -48.83 (-50.95) | -46.49 (-47.1) | -29.17 (-30.81) | -20.37 (-24.31) | -24.72 (-26.16) |
| `sma200_2x_band` | -45.33 (-47.01) | -48.83 (-50.95) | -50.18 (-50.85) | -24.67 (-27.2) | -37.2 (-38.01) | -24.87 (-26.73) |
| `sma200_3x` | -53.11 (-54.06) | -67.2 (-69.1) | -63.62 (-64.07) | -41.27 (-43.06) | -29.53 (-34.6) | -34.87 (-36.57) |
| `sma200_3x_band` | -61.45 (-62.76) | -67.2 (-69.1) | -67.6 (-68.07) | -35.82 (-38.44) | -51.39 (-52.29) | -35.19 (-37.46) |

## Window `modern_daily` (daily): 1990-11-01..2026-06-30, 8978 rows, 35.7 years


### Arms (descriptive)

| arm | CAGR % | arith % | vol % | Sharpe | max DD % | under water (yrs) | in market | round trips/yr | terminal $1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hold_1x` | 11.75 | 12.76 | 18.13 | 0.562 | -54.58 | 6.6 | -- | -- | 52.64 |
| `hold_2x` | 16.31 | 21.73 | 36.26 | 0.528 | -87.57 | 13.9 | -- | -- | 219.14 |
| `hold_3x` | 18.05 | 31.55 | 54.39 | 0.533 | -97.98 | 17.8 | -- | -- | 371.29 |
| `lev_130` | 13.65 | 15.58 | 23.57 | 0.552 | -65.91 | 7.1 | -- | -- | 95.81 |
| `sma200_1x` | 9.13 | 9.43 | 11.75 | 0.584 | -24.23 | 3.8 | 0.773 | 3.03 | 22.53 |
| `sma200_1x_band` | 9.62 | 9.88 | 11.82 | 0.619 | -25.97 | 3.8 | 0.772 | 1.37 | 26.43 |
| `sma200_2x` | 14.07 | 15.95 | 23.50 | 0.569 | -47.53 | 5.3 | 0.773 | 3.03 | 109.34 |
| `sma200_2x_band` | 14.70 | 16.53 | 23.64 | 0.591 | -51.17 | 5.8 | 0.772 | 1.37 | 132.92 |
| `sma200_3x` | 18.35 | 23.13 | 35.25 | 0.583 | -64.68 | 6.0 | 0.773 | 3.03 | 406.70 |
| `sma200_3x_band` | 19.09 | 23.84 | 35.46 | 0.600 | -69.57 | 7.9 | 0.772 | 1.37 | 507.77 |
| `control: cheap` | 11.75 | 12.76 | 18.13 | 0.562 | -54.58 | 6.6 | -- | -- | 52.64 |
| `control: leverage_matched_130` | 13.65 | 15.58 | 23.57 | 0.552 | -65.91 | 7.1 | -- | -- | 95.81 |

### Gaps: point [95% HAC] floor years status

| arm | vs cheap 1x | vs 1.3x | vs exposure-matched |
| --- | --- | --- | --- |
| `hold_1x` | identical | -2.82 [-4.39, -1.25] MDE 2.25 29y `rejected` | identical |
| `hold_2x` | +8.96 [+3.72, +14.21] MDE 7.50 32y `exploratory` | +6.15 [+2.48, +9.82] MDE 5.25 33y `exploratory` | identical |
| `hold_3x` | +18.79 [+8.30, +29.28] MDE 14.99 29y `exploratory` | +15.97 [+7.06, +24.89] MDE 12.74 29y `exploratory` | identical |
| `lev_130` | +2.82 [+1.25, +4.39] MDE 2.25 29y `exploratory` | identical | -- |
| `sma200_1x` | -3.33 [-7.17, +0.50] MDE 5.48 135y `rejected` | -6.15 [-11.22, -1.09] MDE 7.24 69y `rejected` | -0.53 [-3.53, +2.47] MDE 4.29 3121y `rejected` |
| `sma200_1x_band` | -2.88 [-6.64, +0.88] MDE 5.37 179y `rejected` | -5.70 [-10.67, -0.72] MDE 7.11 80y `rejected` | -0.03 [-2.97, +2.91] MDE 4.20 836263y `rejected` |
| `sma200_2x` | +3.18 [-2.22, +8.58] MDE 7.72 255y `unresolved` | +0.36 [-5.30, +6.03] MDE 8.10 23038y `unresolved` | -0.51 [-6.46, +5.45] MDE 8.51 13555y `rejected` |
| `sma200_2x_band` | +3.77 [-1.62, +9.16] MDE 7.70 182y `unresolved` | +0.95 [-4.66, +6.55] MDE 8.01 3381y `unresolved` | +0.15 [-5.70, +6.01] MDE 8.37 148794y `unresolved` |
| `sma200_3x` | +10.37 [+1.95, +18.78] MDE 12.02 54y `unresolved` | +7.55 [-0.56, +15.66] MDE 11.59 99y `unresolved` | -0.44 [-9.36, +8.47] MDE 12.74 39769y `rejected` |
| `sma200_3x_band` | +11.08 [+2.58, +19.57] MDE 12.15 48y `unresolved` | +8.26 [+0.12, +16.40] MDE 11.64 83y `unresolved` | +0.38 [-8.39, +9.15] MDE 12.54 53751y `unresolved` |

### Sensitivities: point gap pp/yr against each control (base / stress spread / other)

| arm | control | base | 80 bp spread | sensitivities |
| --- | --- | ---: | ---: | --- |
| `hold_1x` | leverage_matched_130 | -2.82 | -2.70 | lag0 -2.82, price_proxy_2.5pct -2.82, cost0bp -2.82, cost5bp -2.82, cost25bp -2.82 |
| `hold_2x` | cheap | +8.96 | +8.56 | lag0 +8.96, price_proxy_2.5pct +8.96, cost0bp +8.96, cost5bp +8.96, cost25bp +8.96 |
| `hold_2x` | leverage_matched_130 | +6.15 | +5.87 | lag0 +6.15, price_proxy_2.5pct +6.15, cost0bp +6.15, cost5bp +6.15, cost25bp +6.15 |
| `hold_3x` | cheap | +18.79 | +17.99 | lag0 +18.79, price_proxy_2.5pct +18.79, cost0bp +18.79, cost5bp +18.79, cost25bp +18.79 |
| `hold_3x` | leverage_matched_130 | +15.97 | +15.29 | lag0 +15.97, price_proxy_2.5pct +15.97, cost0bp +15.97, cost5bp +15.97, cost25bp +15.97 |
| `lev_130` | cheap | +2.82 | +2.70 | lag0 +2.82, price_proxy_2.5pct +2.82, cost0bp +2.82, cost5bp +2.82, cost25bp +2.82 |
| `sma200_1x` | cheap | -3.33 | -3.33 | lag0 -3.53, price_proxy_2.5pct -2.39, cost0bp -2.73, cost5bp -3.03, cost25bp -4.25 |
| `sma200_1x` | leverage_matched_130 | -6.15 | -6.03 | lag0 -6.34, price_proxy_2.5pct -5.21, cost0bp -5.54, cost5bp -5.85, cost25bp -7.07 |
| `sma200_1x` | exposure_matched | -0.53 | -0.53 | lag0 -0.72, price_proxy_2.5pct +0.74, cost0bp +0.08, cost5bp -0.22, cost25bp -1.44 |
| `sma200_1x_band` | cheap | -2.88 | -2.88 | lag0 -2.82, price_proxy_2.5pct -3.03, cost0bp -2.60, cost5bp -2.74, cost25bp -3.29 |
| `sma200_1x_band` | leverage_matched_130 | -5.70 | -5.58 | lag0 -5.64, price_proxy_2.5pct -5.85, cost0bp -5.42, cost5bp -5.56, cost25bp -6.11 |
| `sma200_1x_band` | exposure_matched | -0.03 | -0.03 | lag0 +0.03, price_proxy_2.5pct +0.13, cost0bp +0.25, cost5bp +0.11, cost25bp -0.45 |
| `sma200_2x` | cheap | +3.18 | +2.87 | lag0 +2.80, price_proxy_2.5pct +5.10, cost0bp +3.79, cost5bp +3.49, cost25bp +2.27 |
| `sma200_2x` | leverage_matched_130 | +0.36 | +0.18 | lag0 -0.02, price_proxy_2.5pct +2.28, cost0bp +0.97, cost5bp +0.67, cost25bp -0.55 |
| `sma200_2x` | exposure_matched | -0.51 | -0.53 | lag0 -0.89, price_proxy_2.5pct +2.03, cost0bp +0.10, cost5bp -0.20, cost25bp -1.42 |
| `sma200_2x_band` | cheap | +3.77 | +3.46 | lag0 +3.89, price_proxy_2.5pct +3.51, cost0bp +4.05, cost5bp +3.91, cost25bp +3.35 |
| `sma200_2x_band` | leverage_matched_130 | +0.95 | +0.76 | lag0 +1.07, price_proxy_2.5pct +0.69, cost0bp +1.23, cost5bp +1.09, cost25bp +0.53 |
| `sma200_2x_band` | exposure_matched | +0.15 | +0.13 | lag0 +0.27, price_proxy_2.5pct +0.49, cost0bp +0.43, cost5bp +0.29, cost25bp -0.26 |
| `sma200_3x` | cheap | +10.37 | +9.75 | lag0 +9.79, price_proxy_2.5pct +13.24, cost0bp +10.97, cost5bp +10.67, cost25bp +9.45 |
| `sma200_3x` | leverage_matched_130 | +7.55 | +7.05 | lag0 +6.97, price_proxy_2.5pct +10.42, cost0bp +8.16, cost5bp +7.85, cost25bp +6.63 |
| `sma200_3x` | exposure_matched | -0.44 | -0.48 | lag0 -1.02, price_proxy_2.5pct +3.37, cost0bp +0.17, cost5bp -0.14, cost25bp -1.36 |
| `sma200_3x_band` | cheap | +11.08 | +10.46 | lag0 +11.26, price_proxy_2.5pct +10.68, cost0bp +11.35, cost5bp +11.22, cost25bp +10.66 |
| `sma200_3x_band` | leverage_matched_130 | +8.26 | +7.76 | lag0 +8.44, price_proxy_2.5pct +7.86, cost0bp +8.54, cost5bp +8.40, cost25bp +7.84 |
| `sma200_3x_band` | exposure_matched | +0.38 | +0.34 | lag0 +0.56, price_proxy_2.5pct +0.88, cost0bp +0.66, cost5bp +0.52, cost25bp -0.04 |

### Crisis episodes: cumulative % (peak-to-trough %); * partial, n/c not covered

| arm | crash_1929 | october_1987 | dotcom_2000 | gfc_2008 | covid_2020 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `hold_1x` | n/c | n/c | -49.2 (-49.26) | -54.23 (-54.58) | -33.82 (-34.22) | -24.87 (-25.45) |
| `hold_2x` | n/c | n/c | -80.47 (-80.51) | -83.58 (-83.83) | -59.24 (-59.73) | -47.15 (-47.9) |
| `hold_3x` | n/c | n/c | -93.37 (-93.39) | -95.15 (-95.27) | -76.79 (-77.2) | -64.47 (-65.22) |
| `lev_130` | n/c | n/c | -61.15 (-61.21) | -65.56 (-65.91) | -42.33 (-42.78) | -31.96 (-32.59) |
| `sma200_1x` | n/c | n/c | -22.98 (-23.78) | -14.95 (-16.27) | -10.58 (-12.8) | -13.22 (-14.29) |
| `sma200_1x_band` | n/c | n/c | -25.03 (-25.97) | -11.95 (-14.25) | -20.17 (-20.73) | -13.12 (-14.4) |
| `sma200_2x` | n/c | n/c | -46.49 (-47.1) | -29.17 (-30.81) | -20.37 (-24.31) | -24.72 (-26.16) |
| `sma200_2x_band` | n/c | n/c | -50.18 (-50.85) | -24.67 (-27.2) | -37.2 (-38.01) | -24.87 (-26.73) |
| `sma200_3x` | n/c | n/c | -63.62 (-64.07) | -41.27 (-43.06) | -29.53 (-34.6) | -34.87 (-36.57) |
| `sma200_3x_band` | n/c | n/c | -67.6 (-68.07) | -35.82 (-38.44) | -51.39 (-52.29) | -35.19 (-37.46) |

## Window `full_monthly` (monthly): 1926-07..2025-12, 1194 rows, 99.5 years


### Arms (descriptive)

| arm | CAGR % | arith % | vol % | Sharpe | max DD % | under water (yrs) | in market | round trips/yr | terminal $1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hfea_55_45` | 15.98 | 20.54 | 34.58 | 0.502 | -93.04 | 10.0 | -- | -- | 2547759.25 |
| `hfea_equity_leg_3x` | 12.63 | 27.89 | 56.95 | 0.434 | -99.89 | 25.6 | -- | -- | 138336.19 |
| `hfea_treasury_leg_3x` | 5.15 | 8.18 | 25.27 | 0.199 | -90.63 | 41.7 | -- | -- | 148.40 |
| `control: cheap` | 10.19 | 11.43 | 18.36 | 0.450 | -83.91 | 15.4 | -- | -- | 15628.79 |
| `control: leverage_matched_130` | 11.44 | 13.75 | 23.97 | 0.441 | -91.55 | 16.1 | -- | -- | 48120.66 |

### Gaps: point [95% HAC] floor years status

| arm | vs cheap 1x | vs 1.3x | vs exposure-matched |
| --- | --- | --- | --- |
| `hfea_55_45` | +9.11 [+5.21, +13.01] MDE 5.58 34y `exploratory` | +6.79 [+3.61, +9.96] MDE 4.54 40y `exploratory` | -- |

### Sensitivities: point gap pp/yr against each control (base / stress spread / other)

| arm | control | base | 80 bp spread | sensitivities |
| --- | --- | ---: | ---: | --- |
| `hfea_55_45` | cheap | +9.11 | +8.30 | -- |
| `hfea_55_45` | leverage_matched_130 | +6.79 | +5.98 | -- |

### Crisis episodes: cumulative % (peak-to-trough %); * partial, n/c not covered

| arm | crash_1929 | october_1987 | dotcom_2000 | gfc_2008 | covid_2020 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `hfea_55_45` | -93.04 (-93.04) | -31.79 (-31.79) | -40.91 (-51.62) | -55.72 (-64.83) | -11.69 (-11.69) | -47.18 (-52.24) |
| `hfea_equity_leg_3x` | -99.89 (-99.89) | -72.21 (-72.21) | -87.86 (-91.28) | -91.8 (-93.6) | -60.92 (-60.92) | -55.86 (-64.17) |
| `hfea_treasury_leg_3x` | 22.48 (-24.69) | 17.65 (0.0) | 85.44 (-25.76) | 56.72 (-35.09) | 38.78 (0.0) | -39.97 (-39.97) |

## Window `modern_monthly` (monthly): 1990-11..2025-12, 422 rows, 35.2 years


### Arms (descriptive)

| arm | CAGR % | arith % | vol % | Sharpe | max DD % | under water (yrs) | in market | round trips/yr | terminal $1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `hfea_55_45` | 21.51 | 23.26 | 26.74 | 0.774 | -64.83 | 4.7 | -- | -- | 944.84 |
| `hfea_equity_leg_3x` | 17.63 | 27.47 | 45.91 | 0.543 | -97.08 | 17.6 | -- | -- | 301.51 |
| `hfea_treasury_leg_3x` | 10.24 | 14.01 | 29.18 | 0.392 | -64.75 | 5.4 | -- | -- | 30.82 |
| `control: cheap` | 11.63 | 12.20 | 15.09 | 0.639 | -50.19 | 6.5 | -- | -- | 47.96 |
| `control: leverage_matched_130` | 13.49 | 14.68 | 19.67 | 0.616 | -61.49 | 7.0 | -- | -- | 85.57 |

### Gaps: point [95% HAC] floor years status

| arm | vs cheap 1x | vs 1.3x | vs exposure-matched |
| --- | --- | --- | --- |
| `hfea_55_45` | +11.06 [+6.12, +15.99] MDE 7.05 16y `exploratory` | +8.58 [+4.02, +13.14] MDE 6.52 22y `exploratory` | -- |

### Sensitivities: point gap pp/yr against each control (base / stress spread / other)

| arm | control | base | 80 bp spread | sensitivities |
| --- | --- | ---: | ---: | --- |
| `hfea_55_45` | cheap | +11.06 | +10.25 | -- |
| `hfea_55_45` | leverage_matched_130 | +8.58 | +7.77 | -- |

### Crisis episodes: cumulative % (peak-to-trough %); * partial, n/c not covered

| arm | crash_1929 | october_1987 | dotcom_2000 | gfc_2008 | covid_2020 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `hfea_55_45` | n/c | n/c | -40.91 (-51.62) | -55.72 (-64.83) | -11.69 (-11.69) | -47.18 (-52.24) |
| `hfea_equity_leg_3x` | n/c | n/c | -87.86 (-91.28) | -91.8 (-93.6) | -60.92 (-60.92) | -55.86 (-64.17) |
| `hfea_treasury_leg_3x` | n/c | n/c | 85.44 (-25.76) | 56.72 (-35.09) | 38.78 (0.0) | -39.97 (-39.97) |

## Deflation over the declared grid: 28 rules, 25972 rows, 1927-07-06..2026-06-30

trial Sharpe dispersion 0.003139; mean off-diagonal correlation of active returns 0.7388; effective independent trials 8.05; best in grid `sma250_3x_band0.01`

| candidate | active SR ann. | active mean pp/yr | N trials | SR* ann. | DSR |
| --- | ---: | ---: | ---: | ---: | ---: |
| sma200_2x_band0 | 0.1492 | 2.992 | 8.05 | 0.0744 | 0.7712 |
|  |  |  | 14.8 | 0.0897 | 0.7225 |
|  |  |  | 100.0 | 0.1287 | 0.5807 |
|  |  |  | 10000.0 | 0.1963 | 0.32 |
| sma200_2x_band0.01 | 0.149 | 2.969 | 8.05 | 0.0744 | 0.7705 |
|  |  |  | 14.8 | 0.0897 | 0.7217 |
|  |  |  | 100.0 | 0.1287 | 0.5798 |
|  |  |  | 10000.0 | 0.1963 | 0.3192 |
| sma200_3x_band0 | 0.1586 | 4.772 | 8.05 | 0.0744 | 0.7986 |
|  |  |  | 14.8 | 0.0897 | 0.7531 |
|  |  |  | 100.0 | 0.1287 | 0.617 |
|  |  |  | 10000.0 | 0.1963 | 0.3543 |
| sma200_3x_band0.01 | 0.1532 | 4.581 | 8.05 | 0.0744 | 0.7831 |
|  |  |  | 14.8 | 0.0897 | 0.7357 |
|  |  |  | 100.0 | 0.1287 | 0.5962 |
|  |  |  | 10000.0 | 0.1963 | 0.3345 |
| sma250_3x_band0.01 | 0.1993 | 5.915 | 8.05 | 0.0744 | 0.8922 |
|  |  |  | 14.8 | 0.0897 | 0.8613 |
|  |  |  | 100.0 | 0.1287 | 0.758 |
|  |  |  | 10000.0 | 0.1963 | 0.5118 |

## After tax on 1990-11-01..2026-06-30 (35.66 years, 252 rows a year)

| arm | account | terminal $1 | tax paid | growth %/yr | vs hold_1x same account | tax cost pp/yr |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `sma200_3x` | sheltered | 406.814 | 0.0 | 16.865 | -- | -- |
| `sma200_2x` | sheltered | 109.359 | 0.0 | 13.177 | -- | -- |
| `sma200_1x` | sheltered | 22.527 | 0.0 | 8.743 | -- | -- |
| `hold_3x` | sheltered | 370.918 | 0.0 | 16.605 | -- | -- |
| `hold_2x` | sheltered | 218.918 | 0.0 | 15.125 | -- | -- |
| `hold_1x` | sheltered | 52.59 | 0.0 | 11.122 | -- | -- |
| `sma200_3x` | taxable top step_up | 110.263 | 32.821 | 13.2 | 2.494 | 3.248 |
| `sma200_2x` | taxable top step_up | 36.476 | 11.585 | 10.095 | -0.611 | 2.666 |
| `sma200_1x` | taxable top step_up | 10.155 | 3.283 | 6.506 | -4.2 | 1.82 |
| `hold_3x` | taxable top step_up | 355.522 | 1.826 | 16.486 | 5.78 | -0.297 |
| `hold_2x` | taxable top step_up | 209.834 | 1.264 | 15.006 | 4.3 | -0.297 |
| `hold_1x` | taxable top step_up | 45.34 | 1.509 | 10.706 | 0.0 | 0.0 |
| `sma200_3x` | taxable top liquidate | 100.009 | 43.074 | 12.926 | 2.873 | 2.87 |
| `sma200_2x` | taxable top liquidate | 34.043 | 14.018 | 9.902 | -0.152 | 2.207 |
| `sma200_1x` | taxable top liquidate | 9.786 | 3.651 | 6.402 | -3.651 | 1.271 |
| `hold_3x` | taxable top liquidate | 272.537 | 84.811 | 15.74 | 5.687 | -0.204 |
| `hold_2x` | taxable top liquidate | 161.094 | 50.003 | 14.264 | 4.211 | -0.208 |
| `hold_1x` | taxable top liquidate | 35.937 | 10.912 | 10.053 | 0.0 | 0.0 |
| `sma200_3x` | taxable upper_middle step_up | 184.531 | 29.764 | 14.646 | 3.786 | 1.957 |
| `sma200_2x` | taxable upper_middle step_up | 56.131 | 9.699 | 11.305 | 0.445 | 1.61 |
| `sma200_1x` | taxable upper_middle step_up | 13.838 | 2.475 | 7.375 | -3.485 | 1.105 |
| `hold_3x` | taxable upper_middle step_up | 361.139 | 1.165 | 16.53 | 5.67 | -0.187 |
| `hold_2x` | taxable upper_middle step_up | 213.148 | 0.807 | 15.05 | 4.19 | -0.187 |
| `hold_1x` | taxable upper_middle step_up | 47.896 | 0.99 | 10.86 | 0.0 | 0.0 |
| `sma200_3x` | taxable upper_middle liquidate | 174.437 | 39.858 | 14.488 | 4.017 | 1.726 |
| `sma200_2x` | taxable upper_middle liquidate | 53.929 | 11.901 | 11.193 | 0.722 | 1.333 |
| `sma200_1x` | taxable upper_middle liquidate | 13.542 | 2.77 | 7.314 | -3.157 | 0.777 |
| `hold_3x` | taxable upper_middle liquidate | 308.109 | 54.196 | 16.085 | 5.613 | -0.13 |
| `hold_2x` | taxable upper_middle liquidate | 182.011 | 31.943 | 14.607 | 4.136 | -0.133 |
| `hold_1x` | taxable upper_middle liquidate | 41.703 | 7.183 | 10.471 | 0.0 | 0.0 |
