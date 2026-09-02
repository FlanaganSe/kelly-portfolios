# Experiment 020: a bond-regime-conditioned Treasury stack

Run `149509ed5b964f928afb8ee973e669ac`; specification hash `acbe4f8798d22aa5cb442a678a99f9af9732e0131683f59107c287cb05fd9c1f`.

WRAPPERS ARE ASSUMED EXPOSURE VECTORS, NOT FUND RETURNS. The bond leg is a ~20-year bond whose history contains the 1981-2020 bull market. The signal is the trailing correlation of equity and Treasury excess returns through month t-1, applied to month t. Four rules on one signal were declared before the run with one primary; every mean gap was predicted `unresolved`. No TIPS series exists before 2003 in the panel and none was built. The regret table is arithmetic on stated inputs.

Panel 1929-01..2025-05, 1157 months. Trend-book volatility scalar 1.9771 (realised 6.26% on 1929-01..2025-05, target 12.38%). Switching cost 10 bp one-way on each dollar moved; certain cost of the leg while on 0.114 pp/yr.

Gap cells read: point estimate [95% Newey-West interval] MDE at 80% power, years to distinguish, status; scored cells also carry the block-bootstrap interval.

### Arms: state, notional, growth, drawdown (descriptive)

| arm | first month | months | on | switches | mean on-spell | longest off-spell | gross on/off | arith pp/yr | log growth | vol % | Sharpe | max DD % | ref max DD % | months under water | TW vs ref | TW vs unconditional |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | 1929-01 | 1157 | 0.0 | 0 | -- | -- | 1.322/1.322 | 12.9362 | 11.0753 | 18.9893 | 0.51 | -82.78 | -82.78 | 164 | 1.0 | 0.7757 |
| `trend30_bondstack20` | 1929-01 | 1157 | 1.0 | 0 | -- | -- | 1.522/1.522 | 13.2737 | 11.3705 | 19.2099 | 0.5216 | -82.53 | -82.78 | 88 | 1.2891 | 1.0 |
| `cond36_below0` | 1929-07 | 1151 | 0.394 | 18 | 50.4 | 278 | 1.522/1.322 | 13.034 | 11.1687 | 19.0033 | 0.515 | -82.94 | -82.78 | 164 | 1.1653 | 0.9034 |
| `cond60_below0` | 1931-07 | 1127 | 0.367 | 9 | 82.8 | 423 | 1.522/1.322 | 13.8109 | 12.0209 | 18.6004 | 0.5671 | -63.1 | -62.99 | 74 | 1.1504 | 0.8934 |
| `cond36_below_minus02` | 1929-07 | 1151 | 0.24 | 30 | 18.4 | 434 | 1.522/1.322 | 12.9155 | 11.0538 | 18.9907 | 0.5092 | -82.85 | -82.78 | 164 | 1.0505 | 0.8144 |
| `cond36_below_median120` | 1939-06 | 1032 | 0.481 | 62 | 16.0 | 99 | 1.522/1.322 | 13.9252 | 12.5698 | 15.9716 | 0.6503 | -45.65 | -45.86 | 50 | 1.0603 | 0.8594 |

### Arithmetic gap against `reference` by window: gap [95% HAC interval] MDE years status (boot interval on scored cells); on-fraction in the second row

| arm | full | complement_of_bond_bull | before_bond_bull | bond_bull_market | after_bond_bull | flat_equity_decade | inflation_1977 | rate_shock_2022 | positive_bond_equity_correlation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `trend30_bondstack20` | +0.34 [-0.00, +0.68] MDE 0.49 201y `reported` boot [-0.00, +0.68] | -0.25 [-0.60, +0.11] MDE 0.48 223y `reported` boot [-0.68, +0.15] | -0.15 [-0.50, +0.21] MDE 0.50 613y `reported` | +1.20 [+0.55, +1.86] MDE 0.96 25y `reported` | -1.32 [-2.61, -0.04] MDE 1.80 9y `reported` | +0.83 [-0.22, +1.87] MDE 1.93 55y `reported` | -2.59 [-4.66, -0.53] MDE 3.15 7y `reported` | -3.94 [-6.27, -1.61] MDE 3.88 1y `reported` | +0.23 [-0.51, +0.97] MDE 1.04 679y `reported` |
| `trend30_bondstack20` detail | log +0.30; TE 1.71 | log -0.28; TE 1.31 | log -0.18; TE 1.30 | log +1.15; TE 2.15 | log -1.40; TE 1.41 | log +0.81; TE 2.18 | log -2.66; TE 2.45 | log -4.22; TE 1.20 | log +0.10; TE 2.11 |
| `cond36_below0` | +0.16 [-0.06, +0.38] MDE 0.32 377y `unresolved` boot [-0.05, +0.40] | -0.15 [-0.33, +0.04] MDE 0.23 140y `rejected` boot [-0.34, +0.02] | -0.07 [-0.23, +0.09] MDE 0.21 512y `reported` | +0.61 [+0.14, +1.08] MDE 0.71 52y `reported` | -1.01 [-2.20, +0.18] MDE 1.49 11y `reported` | +0.85 [-0.15, +1.86] MDE 1.90 49y `reported` | -0.00 [-0.00, +0.00] MDE 0.00 56y `reported` | -3.94 [-6.27, -1.61] MDE 3.88 1y `reported` | -0.10 [-0.21, +0.01] MDE 0.11 36y `reported` |
| `cond36_below0` detail | on 39%, 18 sw; log +0.16; TE 1.12 | on 31%, 14 sw; log -0.16; TE 0.61 | on 29%, 12 sw; log -0.08; TE 0.53 | on 52%, 5 sw; log +0.63; TE 1.58 | on 52%, 1 sw; log -1.06; TE 1.17 | on 86%, 1 sw; log +0.85; TE 2.14 | on 0%, 0 sw; log -0.00; TE 0.00 | on 100%, 0 sw; log -4.22; TE 1.20 | on 3%, 5 sw; log -0.10; TE 0.21 |
| `cond60_below0` | +0.15 [-0.08, +0.38] MDE 0.32 422y `unresolved` boot [-0.07, +0.39] | -0.16 [-0.36, +0.03] MDE 0.25 125y `rejected` boot [-0.37, +0.02] | -0.05 [-0.22, +0.12] MDE 0.21 959y `reported` | +0.60 [+0.14, +1.06] MDE 0.69 52y `reported` | -1.36 [-2.60, -0.13] MDE 1.70 8y `reported` | +0.71 [-0.25, +1.67] MDE 1.82 66y `reported` | +0.00 [-0.00, +0.00] MDE 0.00 94y `reported` | -3.94 [-6.27, -1.61] MDE 3.88 1y `reported` | -0.05 [-0.12, +0.02] MDE 0.09 104y `reported` |
| `cond60_below0` detail | on 37%, 9 sw; log +0.15; TE 1.12 | on 29%, 7 sw; log -0.18; TE 0.66 | on 24%, 5 sw; log -0.06; TE 0.54 | on 48%, 3 sw; log +0.62; TE 1.54 | on 78%, 1 sw; log -1.44; TE 1.34 | on 72%, 1 sw; log +0.69; TE 2.06 | on 0%, 0 sw; log +0.00; TE 0.00 | on 100%, 0 sw; log -4.22; TE 1.20 | on 2%, 1 sw; log -0.05; TE 0.18 |
| `cond36_below_minus02` | +0.04 [-0.13, +0.21] MDE 0.25 3171y `unresolved` boot [-0.11, +0.21] | -0.17 [-0.31, -0.02] MDE 0.18 65y `rejected` boot [-0.32, -0.04] | -0.10 [-0.22, +0.02] MDE 0.15 115y `reported` | +0.35 [-0.01, +0.71] MDE 0.54 94y `reported` | -0.88 [-2.00, +0.24] MDE 1.32 11y `reported` | +0.77 [-0.00, +1.54] MDE 1.41 34y `reported` | -0.00 [-0.00, +0.00] MDE 0.00 4060y `reported` | -2.68 [-4.91, -0.44] MDE 2.96 1y `reported` | -0.00 [-0.00, +0.00] MDE 0.00 251y `reported` |
| `cond36_below_minus02` detail | on 24%, 30 sw; log +0.04; TE 0.86 | on 16%, 18 sw; log -0.17; TE 0.48 | on 14%, 16 sw; log -0.10; TE 0.38 | on 36%, 13 sw; log +0.36; TE 1.21 | on 40%, 1 sw; log -0.90; TE 1.04 | on 56%, 8 sw; log +0.76; TE 1.59 | on 0%, 0 sw; log +0.00; TE 0.00 | on 67%, 1 sw; log -2.81; TE 0.92 | on 0%, 0 sw; log -0.00; TE 0.01 |
| `cond36_below_median120` | +0.10 [-0.14, +0.33] MDE 0.35 1122y `unresolved` boot [-0.14, +0.33] | -0.22 [-0.49, +0.04] MDE 0.32 96y `rejected` boot [-0.62, +0.08] | -0.18 [-0.45, +0.09] MDE 0.33 141y `reported` | +0.49 [+0.05, +0.92] MDE 0.68 75y `reported` | -0.59 [-1.53, +0.34] MDE 1.13 18y `reported` | +0.68 [-0.20, +1.55] MDE 1.53 51y `reported` | -1.68 [-3.09, -0.28] MDE 1.94 6y `reported` | -0.57 [-1.57, +0.42] MDE 1.44 5y `reported` | +0.03 [-0.36, +0.43] MDE 0.60 10190y `reported` |
| `cond36_below_median120` detail | on 48%, 62 sw; log +0.08; TE 1.17 | on 37%, 30 sw; log -0.23; TE 0.78 | on 39%, 27 sw; log -0.19; TE 0.76 | on 61%, 32 sw; log +0.46; TE 1.51 | on 24%, 3 sw; log -0.59; TE 0.89 | on 93%, 5 sw; log +0.68; TE 1.72 | on 30%, 5 sw; log -1.72; TE 1.51 | on 11%, 1 sw; log -0.60; TE 0.45 | on 27%, 23 sw; log -0.02; TE 1.21 |

### Arithmetic gap against `unconditional_stack` by window: gap [95% HAC interval] MDE years status (boot interval on scored cells); on-fraction in the second row

| arm | full | complement_of_bond_bull | before_bond_bull | bond_bull_market | after_bond_bull | flat_equity_decade | inflation_1977 | rate_shock_2022 | positive_bond_equity_correlation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `base_trend30` | -0.34 [-0.68, +0.00] MDE 0.49 201y `reported` boot [-0.68, +0.00] | +0.25 [-0.11, +0.60] MDE 0.48 223y `reported` boot [-0.15, +0.68] | +0.15 [-0.21, +0.50] MDE 0.50 613y `reported` | -1.20 [-1.86, -0.55] MDE 0.96 25y `reported` | +1.32 [+0.04, +2.61] MDE 1.80 9y `reported` | -0.83 [-1.87, +0.22] MDE 1.93 55y `reported` | +2.59 [+0.53, +4.66] MDE 3.15 7y `reported` | +3.94 [+1.61, +6.27] MDE 3.88 1y `reported` | -0.23 [-0.97, +0.51] MDE 1.04 679y `reported` |
| `base_trend30` detail | log -0.30; TE 1.71 | log +0.28; TE 1.31 | log +0.18; TE 1.30 | log -1.15; TE 2.15 | log +1.40; TE 1.41 | log -0.81; TE 2.18 | log +2.66; TE 2.45 | log +4.22; TE 1.20 | log -0.10; TE 2.11 |
| `cond36_below0` | -0.19 [-0.46, +0.08] MDE 0.37 378y `rejected` boot [-0.47, +0.10] | +0.09 [-0.22, +0.39] MDE 0.43 1398y `unresolved` boot [-0.24, +0.46] | +0.07 [-0.27, +0.40] MDE 0.46 2538y `reported` | -0.59 [-1.08, -0.10] MDE 0.66 49y `reported` | +0.31 [-0.32, +0.95] MDE 1.04 53y `reported` | +0.03 [-0.26, +0.32] MDE 0.36 1601y `reported` | +2.59 [+0.53, +4.66] MDE 3.15 7y `reported` | -0.00 [-0.00, +0.00] MDE 0.00 152y `reported` | -0.33 [-1.06, +0.41] MDE 1.04 323y `reported` |
| `cond36_below0` detail | on 39%, 18 sw; log -0.15; TE 1.30 | on 31%, 14 sw; log +0.11; TE 1.16 | on 29%, 12 sw; log +0.09; TE 1.19 | on 52%, 5 sw; log -0.52; TE 1.47 | on 52%, 1 sw; log +0.34; TE 0.82 | on 86%, 1 sw; log +0.03; TE 0.41 | on 0%, 0 sw; log +2.66; TE 2.45 | on 100%, 0 sw; log -0.00; TE 0.00 | on 3%, 5 sw; log -0.21; TE 2.10 |
| `cond60_below0` | -0.19 [-0.47, +0.09] MDE 0.38 378y `rejected` boot [-0.48, +0.09] | +0.10 [-0.21, +0.41] MDE 0.44 1040y `unresolved` boot [-0.23, +0.49] | +0.11 [-0.23, +0.45] MDE 0.47 875y `reported` | -0.60 [-1.10, -0.10] MDE 0.68 50y `reported` | -0.04 [-0.43, +0.34] MDE 0.56 933y `reported` | -0.12 [-0.56, +0.32] MDE 0.66 319y `reported` | +2.59 [+0.53, +4.66] MDE 3.15 7y `reported` | -0.00 [-0.00, +0.00] MDE 0.00 19y `reported` | -0.28 [-1.02, +0.46] MDE 1.04 453y `reported` |
| `cond60_below0` detail | on 37%, 9 sw; log -0.14; TE 1.32 | on 29%, 7 sw; log +0.13; TE 1.15 | on 24%, 5 sw; log +0.15; TE 1.20 | on 48%, 3 sw; log -0.53; TE 1.51 | on 78%, 1 sw; log -0.03; TE 0.44 | on 72%, 1 sw; log -0.12; TE 0.74 | on 0%, 0 sw; log +2.66; TE 2.45 | on 100%, 0 sw; log -0.00; TE 0.00 | on 2%, 1 sw; log -0.15; TE 2.10 |
| `cond36_below_minus02` | -0.31 [-0.61, -0.01] MDE 0.42 184y `rejected` boot [-0.61, +0.00] | +0.07 [-0.25, +0.38] MDE 0.45 2717y `unresolved` boot [-0.28, +0.46] | +0.03 [-0.31, +0.37] MDE 0.48 12539y `reported` | -0.85 [-1.43, -0.27] MDE 0.80 35y `reported` | +0.44 [-0.32, +1.20] MDE 1.26 40y `reported` | -0.06 [-0.77, +0.66] MDE 1.33 5453y `reported` | +2.59 [+0.53, +4.66] MDE 3.15 7y `reported` | +1.26 [-1.28, +3.80] MDE 3.66 6y `reported` | -0.23 [-0.97, +0.51] MDE 1.04 672y `reported` |
| `cond36_below_minus02` detail | on 24%, 30 sw; log -0.26; TE 1.48 | on 16%, 18 sw; log +0.10; TE 1.22 | on 14%, 16 sw; log +0.06; TE 1.24 | on 36%, 13 sw; log -0.79; TE 1.79 | on 40%, 1 sw; log +0.50; TE 0.99 | on 56%, 8 sw; log -0.05; TE 1.50 | on 0%, 0 sw; log +2.66; TE 2.45 | on 67%, 1 sw; log +1.41; TE 1.13 | on 0%, 0 sw; log -0.11; TE 2.11 |
| `cond36_below_median120` | -0.20 [-0.47, +0.08] MDE 0.41 364y `rejected` boot [-0.48, +0.09] | +0.23 [-0.07, +0.53] MDE 0.46 192y `unresolved` boot [-0.05, +0.53] | +0.17 [-0.14, +0.49] MDE 0.49 340y `reported` | -0.72 [-1.19, -0.24] MDE 0.70 37y `reported` | +0.73 [-0.18, +1.64] MDE 1.44 19y `reported` | -0.15 [-0.82, +0.52] MDE 1.20 636y `reported` | +0.91 [-0.79, +2.61] MDE 2.59 38y `reported` | +3.37 [+0.96, +5.78] MDE 4.08 1y `reported` | -0.19 [-0.77, +0.39] MDE 0.85 629y `reported` |
| `cond36_below_median120` detail | on 48%, 62 sw; log -0.17; TE 1.34 | on 37%, 30 sw; log +0.26; TE 1.13 | on 39%, 27 sw; log +0.19; TE 1.13 | on 61%, 32 sw; log -0.69; TE 1.55 | on 24%, 3 sw; log +0.81; TE 1.13 | on 93%, 5 sw; log -0.13; TE 1.35 | on 30%, 5 sw; log +0.94; TE 2.02 | on 11%, 1 sw; log +3.62; TE 1.26 | on 27%, 23 sw; log -0.12; TE 1.73 |

### Arithmetic gap against `cheap` by window: gap [95% HAC interval] MDE years status (boot interval on scored cells); on-fraction in the second row

| arm | full | complement_of_bond_bull | before_bond_bull | bond_bull_market | after_bond_bull | flat_equity_decade | inflation_1977 | rate_shock_2022 | positive_bond_equity_correlation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.98 [+1.21, +2.76] MDE 1.06 27y `reported` | +2.00 [+1.00, +3.01] MDE 1.31 25y `reported` | +2.21 [+1.12, +3.29] MDE 1.40 21y `reported` | +1.95 [+0.73, +3.18] MDE 1.76 32y `reported` | -0.21 [-2.17, +1.74] MDE 3.39 1241y `reported` | +2.84 [+0.68, +4.99] MDE 3.58 16y `reported` | +4.04 [-0.78, +8.86] MDE 5.98 10y `reported` | +2.20 [-4.97, +9.37] MDE 12.06 23y `reported` | +2.58 [+0.96, +4.20] MDE 2.17 23y `reported` |
| `base_trend30` detail | log +1.87; TE 3.71 | log +1.91; TE 3.56 | log +2.11; TE 3.62 | log +1.80; TE 3.92 | log -0.25; TE 2.66 | log +2.94; TE 4.04 | log +3.89; TE 4.65 | log +2.28; TE 3.73 | log +2.41; TE 4.38 |
| `trend30_bondstack20` | +2.32 [+1.45, +3.19] MDE 1.19 25y `reported` | +1.76 [+0.79, +2.73] MDE 1.28 30y `reported` | +2.06 [+1.03, +3.08] MDE 1.35 23y `reported` | +3.16 [+1.57, +4.74] MDE 2.26 20y `reported` | -1.53 [-3.52, +0.46] MDE 3.48 25y `reported` | +3.66 [+0.76, +6.57] MDE 4.81 17y `reported` | +1.45 [-2.02, +4.91] MDE 4.21 40y `reported` | -1.75 [-8.12, +4.62] MDE 11.26 31y `reported` | +2.81 [+1.07, +4.54] MDE 2.27 21y `reported` |
| `trend30_bondstack20` detail | log +2.16; TE 4.17 | log +1.63; TE 3.46 | log +1.93; TE 3.51 | log +2.95; TE 5.04 | log -1.65; TE 2.73 | log +3.76; TE 5.43 | log +1.23; TE 3.27 | log -1.94; TE 3.48 | log +2.52; TE 4.59 |
| `cond36_below0` | +2.13 [+1.31, +2.96] MDE 1.16 28y `reported` | +1.84 [+0.82, +2.86] MDE 1.33 30y `reported` | +2.12 [+1.03, +3.22] MDE 1.41 23y `reported` | +2.57 [+1.16, +3.97] MDE 2.08 26y `reported` | -1.22 [-3.26, +0.82] MDE 3.55 41y `reported` | +3.69 [+0.80, +6.57] MDE 4.82 17y `reported` | +4.04 [-0.78, +8.86] MDE 5.98 10y `reported` | -1.75 [-8.12, +4.62] MDE 11.26 31y `reported` | +2.48 [+0.85, +4.11] MDE 2.17 25y `reported` |
| `cond36_below0` detail | on 39%, 18 sw; log +2.01; TE 4.04 | on 31%, 14 sw; log +1.73; TE 3.59 | on 29%, 12 sw; log +2.01; TE 3.65 | on 52%, 5 sw; log +2.43; TE 4.63 | on 52%, 1 sw; log -1.31; TE 2.78 | on 86%, 1 sw; log +3.79; TE 5.44 | on 0%, 0 sw; log +3.89; TE 4.65 | on 100%, 0 sw; log -1.94; TE 3.48 | on 3%, 5 sw; log +2.31; TE 4.38 |
| `cond60_below0` | +2.14 [+1.32, +2.97] MDE 1.16 27y `reported` | +1.85 [+0.83, +2.87] MDE 1.34 29y `reported` | +2.18 [+1.08, +3.27] MDE 1.43 22y `reported` | +2.56 [+1.17, +3.94] MDE 2.05 25y `reported` | -1.57 [-3.53, +0.38] MDE 3.39 22y `reported` | +3.54 [+0.75, +6.34] MDE 4.65 17y `reported` | +4.04 [-0.78, +8.86] MDE 5.98 10y `reported` | -1.75 [-8.12, +4.62] MDE 11.26 31y `reported` | +2.53 [+0.91, +4.15] MDE 2.16 23y `reported` |
| `cond60_below0` detail | on 37%, 9 sw; log +2.02; TE 4.00 | on 29%, 7 sw; log +1.74; TE 3.55 | on 24%, 5 sw; log +2.07; TE 3.61 | on 48%, 3 sw; log +2.42; TE 4.56 | on 78%, 1 sw; log -1.68; TE 2.66 | on 72%, 1 sw; log +3.64; TE 5.24 | on 0%, 0 sw; log +3.89; TE 4.65 | on 100%, 0 sw; log -1.94; TE 3.48 | on 2%, 1 sw; log +2.36; TE 4.36 |
| `cond36_below_minus02` | +2.02 [+1.20, +2.83] MDE 1.13 30y `reported` | +1.82 [+0.79, +2.85] MDE 1.33 31y `reported` | +2.09 [+0.99, +3.19] MDE 1.41 24y `reported` | +2.30 [+0.96, +3.65] MDE 1.98 29y `reported` | -1.09 [-3.27, +1.08] MDE 3.77 57y `reported` | +3.60 [+1.00, +6.21] MDE 4.32 14y `reported` | +4.04 [-0.78, +8.86] MDE 5.98 10y `reported` | -0.48 [-8.43, +7.47] MDE 13.18 559y `reported` | +2.58 [+0.96, +4.20] MDE 2.17 23y `reported` |
| `cond36_below_minus02` detail | on 24%, 30 sw; log +1.90; TE 3.94 | on 16%, 18 sw; log +1.72; TE 3.59 | on 14%, 16 sw; log +1.99; TE 3.63 | on 36%, 13 sw; log +2.16; TE 4.40 | on 40%, 1 sw; log -1.15; TE 2.96 | on 56%, 8 sw; log +3.71; TE 4.87 | on 0%, 0 sw; log +3.89; TE 4.65 | on 67%, 1 sw; log -0.53; TE 4.08 | on 0%, 0 sw; log +2.41; TE 4.38 |
| `cond36_below_median120` | +2.04 [+1.16, +2.93] MDE 1.23 31y `reported` | +1.72 [+0.59, +2.85] MDE 1.47 35y `reported` | +2.01 [+0.78, +3.23] MDE 1.58 26y `reported` | +2.44 [+1.02, +3.86] MDE 2.05 27y `reported` | -0.81 [-2.87, +1.26] MDE 3.63 98y `reported` | +3.51 [+0.84, +6.18] MDE 4.55 17y `reported` | +2.36 [-2.30, +7.01] MDE 5.76 28y `reported` | +1.62 [-5.07, +8.31] MDE 11.85 40y `reported` | +2.61 [+0.93, +4.30] MDE 2.21 23y `reported` |
| `cond36_below_median120` detail | on 48%, 62 sw; log +1.89; TE 4.06 | on 37%, 30 sw; log +1.58; TE 3.60 | on 39%, 27 sw; log +1.86; TE 3.67 | on 61%, 32 sw; log +2.26; TE 4.55 | on 24%, 3 sw; log -0.84; TE 2.85 | on 93%, 5 sw; log +3.63; TE 5.13 | on 30%, 5 sw; log +2.17; TE 4.48 | on 11%, 1 sw; log +1.67; TE 3.66 | on 27%, 23 sw; log +2.39; TE 4.46 |

### Arithmetic gap against `leverage_matched` by window: gap [95% HAC interval] MDE years status (boot interval on scored cells); on-fraction in the second row

| arm | full | complement_of_bond_bull | before_bond_bull | bond_bull_market | after_bond_bull | flat_equity_decade | inflation_1977 | rate_shock_2022 | positive_bond_equity_correlation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `base_trend30` | -0.30 [-1.75, +1.15] MDE 1.97 4181y `reported` | -0.09 [-2.16, +1.97] MDE 2.76 51084y `reported` | +0.25 [-1.97, +2.47] MDE 2.92 7265y `reported` | -0.61 [-2.51, +1.29] MDE 2.70 769y `reported` | -3.82 [-8.05, +0.40] MDE 7.66 19y `reported` | +4.43 [-0.44, +9.31] MDE 6.50 22y `reported` | +3.82 [-2.24, +9.87] MDE 8.83 25y `reported` | +14.00 [+1.23, +26.78] MDE 27.39 3y `reported` | +0.91 [-1.54, +3.35] MDE 3.18 396y `reported` |
| `base_trend30` detail | log +0.88; TE 6.91 | log +1.37; TE 7.47 | log +1.75; TE 7.58 | log +0.17; TE 6.00 | log -2.79; TE 6.01 | log +5.57; TE 7.34 | log +4.60; TE 6.87 | log +16.22; TE 8.47 | log +1.65; TE 6.43 |
| `trend30_bondstack20` | -1.38 [-3.53, +0.77] MDE 2.94 436y `reported` | -1.64 [-4.63, +1.35] MDE 4.05 352y `reported` | -1.11 [-4.33, +2.10] MDE 4.31 788y `reported` | -1.00 [-3.94, +1.95] MDE 4.12 666y `reported` | -7.39 [-13.67, -1.11] MDE 11.03 11y `reported` | +6.25 [-1.42, +13.93] MDE 9.85 25y `reported` | +1.08 [-5.57, +7.74] MDE 10.28 428y `reported` | +17.41 [+1.02, +33.79] MDE 38.14 4y `reported` | +0.09 [-3.06, +3.25] MDE 4.14 67433y `reported` |
| `trend30_bondstack20` detail | log +0.76; TE 10.29 | log +0.98; TE 10.98 | log +1.58; TE 11.17 | log +0.44; TE 9.17 | log -5.62; TE 8.66 | log +8.17; TE 11.11 | log +2.52; TE 8.00 | log +20.99; TE 11.79 | log +1.42; TE 8.36 |
| `cond36_below0` | -0.33 [-2.16, +1.50] MDE 2.47 5368y `reported` | -0.22 [-2.67, +2.23] MDE 3.28 12732y `reported` | +0.30 [-2.31, +2.92] MDE 3.45 6758y `reported` | -0.49 [-3.20, +2.22] MDE 3.75 2246y `reported` | -5.87 [-11.65, -0.09] MDE 10.26 15y `reported` | +6.55 [-1.00, +14.09] MDE 9.65 22y `reported` | +3.82 [-2.24, +9.87] MDE 8.83 25y `reported` | +17.41 [+1.02, +33.79] MDE 38.14 4y `reported` | +0.94 [-1.51, +3.39] MDE 3.20 374y `reported` |
| `cond36_below0` detail | on 39%, 18 sw; log +1.25; TE 8.64 | on 31%, 14 sw; log +1.65; TE 8.84 | on 29%, 12 sw; log +2.21; TE 8.90 | on 52%, 5 sw; log +0.67; TE 8.35 | on 52%, 1 sw; log -4.33; TE 8.05 | on 86%, 1 sw; log +8.37; TE 10.89 | on 0%, 0 sw; log +4.60; TE 6.87 | on 100%, 0 sw; log +20.99; TE 11.79 | on 3%, 5 sw; log +1.70; TE 6.47 |
| `cond60_below0` | -0.67 [-2.46, +1.12] MDE 2.40 1200y `reported` | -0.67 [-3.09, +1.74] MDE 3.20 1245y `reported` | -0.07 [-2.64, +2.49] MDE 3.34 109119y `reported` | -0.67 [-3.31, +1.97] MDE 3.64 1139y `reported` | -6.91 [-12.98, -0.85] MDE 10.73 12y `reported` | +5.87 [-1.35, +13.08] MDE 8.99 23y `reported` | +3.82 [-2.24, +9.87] MDE 8.83 25y `reported` | +17.41 [+1.02, +33.79] MDE 38.14 4y `reported` | +0.97 [-1.49, +3.43] MDE 3.20 350y `reported` |
| `cond60_below0` detail | on 37%, 9 sw; log +0.80; TE 8.31 | on 29%, 7 sw; log +1.05; TE 8.47 | on 24%, 5 sw; log +1.66; TE 8.46 | on 48%, 3 sw; log +0.44; TE 8.09 | on 78%, 1 sw; log -5.24; TE 8.42 | on 72%, 1 sw; log +7.49; TE 10.15 | on 0%, 0 sw; log +4.60; TE 6.87 | on 100%, 0 sw; log +20.99; TE 11.79 | on 2%, 1 sw; log +1.73; TE 6.46 |
| `cond36_below_minus02` | -0.47 [-2.17, +1.23] MDE 2.27 2211y `reported` | -0.24 [-2.56, +2.09] MDE 3.03 9285y `reported` | +0.24 [-2.23, +2.71] MDE 3.19 9350y `reported` | -0.82 [-3.22, +1.58] MDE 3.41 674y `reported` | -5.38 [-11.19, +0.43] MDE 9.32 15y `reported` | +5.63 [-0.94, +12.19] MDE 8.57 23y `reported` | +3.82 [-2.24, +9.87] MDE 8.83 25y `reported` | +17.68 [+4.55, +30.81] MDE 31.74 2y `reported` | +0.90 [-1.54, +3.35] MDE 3.18 397y `reported` |
| `cond36_below_minus02` detail | on 24%, 30 sw; log +0.93; TE 7.93 | on 16%, 18 sw; log +1.43; TE 8.16 | on 14%, 16 sw; log +1.94; TE 8.23 | on 36%, 13 sw; log +0.19; TE 7.58 | on 40%, 1 sw; log -4.02; TE 7.31 | on 56%, 8 sw; log +7.17; TE 9.67 | on 0%, 0 sw; log +4.60; TE 6.87 | on 67%, 1 sw; log +20.67; TE 9.81 | on 0%, 0 sw; log +1.65; TE 6.43 |
| `cond36_below_median120` | -1.25 [-2.92, +0.42] MDE 2.21 268y `reported` | -1.47 [-3.64, +0.70] MDE 2.71 160y `reported` | -1.00 [-3.34, +1.33] MDE 2.84 339y `reported` | -0.98 [-3.52, +1.55] MDE 3.63 527y `reported` | -5.56 [-11.13, +0.01] MDE 8.82 12y `reported` | +5.71 [-1.29, +12.70] MDE 9.55 28y `reported` | +3.00 [-3.43, +9.43] MDE 9.42 47y `reported` | +15.09 [+1.35, +28.83] MDE 28.31 3y `reported` | +0.52 [-2.04, +3.08] MDE 3.42 1401y `reported` |
| `cond36_below_median120` detail | on 48%, 62 sw; log -0.20; TE 7.32 | on 37%, 30 sw; log -0.51; TE 6.64 | on 39%, 27 sw; log -0.08; TE 6.60 | on 61%, 32 sw; log +0.17; TE 8.07 | on 24%, 3 sw; log -4.33; TE 6.92 | on 93%, 5 sw; log +7.56; TE 10.78 | on 30%, 5 sw; log +4.03; TE 7.33 | on 11%, 1 sw; log +17.43; TE 8.75 | on 27%, 23 sw; log +1.40; TE 6.91 |

### Arithmetic gap against `volatility_matched_expost` by window: gap [95% HAC interval] MDE years status (boot interval on scored cells); on-fraction in the second row

| arm | full | complement_of_bond_bull | before_bond_bull | bond_bull_market | after_bond_bull | flat_equity_decade | inflation_1977 | rate_shock_2022 | positive_bond_equity_correlation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `base_trend30` | +1.79 [+1.01, +2.57] MDE 1.06 34y `reported` | +1.83 [+0.81, +2.85] MDE 1.33 30y `reported` | +2.04 [+0.94, +3.15] MDE 1.41 25y `reported` | +1.74 [+0.52, +2.96] MDE 1.75 39y `reported` | -0.51 [-2.46, +1.44] MDE 3.43 218y `reported` | +2.97 [+0.69, +5.25] MDE 3.70 16y `reported` | +4.02 [-0.79, +8.83] MDE 6.00 11y `reported` | +3.17 [-4.17, +10.52] MDE 12.48 12y `reported` | +2.44 [+0.81, +4.07] MDE 2.16 25y `reported` |
| `base_trend30` detail | log +1.77; TE 3.72 | log +1.85; TE 3.60 | log +2.06; TE 3.67 | log +1.65; TE 3.90 | log -0.47; TE 2.69 | log +3.15; TE 4.17 | log +3.94; TE 4.67 | log +3.41; TE 3.86 | log +2.34; TE 4.37 |
| `trend30_bondstack20` | +2.05 [+1.17, +2.92] MDE 1.19 33y `reported` | +1.51 [+0.52, +2.50] MDE 1.29 42y `reported` | +1.82 [+0.78, +2.87] MDE 1.37 30y `reported` | +2.85 [+1.26, +4.44] MDE 2.26 24y `reported` | -1.97 [-3.91, -0.02] MDE 3.41 15y `reported` | +3.85 [+0.74, +6.97] MDE 4.98 17y `reported` | +1.42 [-1.95, +4.79] MDE 4.06 39y `reported` | -0.33 [-6.77, +6.10] MDE 11.42 889y `reported` | +2.61 [+0.89, +4.32] MDE 2.23 23y `reported` |
| `trend30_bondstack20` detail | log +2.02; TE 4.19 | log +1.54; TE 3.50 | log +1.86; TE 3.55 | log +2.74; TE 5.03 | log -1.97; TE 2.68 | log +4.06; TE 5.62 | log +1.31; TE 3.16 | log -0.31; TE 3.53 | log +2.41; TE 4.49 |
| `cond36_below0` | +1.94 [+1.11, +2.78] MDE 1.16 34y `reported` | +1.67 [+0.63, +2.70] MDE 1.34 37y `reported` | +1.96 [+0.85, +3.07] MDE 1.43 28y `reported` | +2.35 [+0.94, +3.76] MDE 2.09 31y `reported` | -1.53 [-3.54, +0.49] MDE 3.52 26y `reported` | +3.82 [+0.80, +6.85] MDE 4.93 17y `reported` | +4.02 [-0.79, +8.83] MDE 6.00 11y `reported` | -0.75 [-7.15, +5.64] MDE 11.30 170y `reported` | +2.34 [+0.70, +3.98] MDE 2.17 27y `reported` |
| `cond36_below0` detail | on 39%, 18 sw; log +1.92; TE 4.07 | on 31%, 14 sw; log +1.67; TE 3.62 | on 29%, 12 sw; log +1.97; TE 3.68 | on 52%, 5 sw; log +2.28; TE 4.65 | on 52%, 1 sw; log -1.53; TE 2.77 | on 86%, 1 sw; log +4.00; TE 5.57 | on 0%, 0 sw; log +3.94; TE 4.67 | on 100%, 0 sw; log -0.79; TE 3.49 | on 3%, 5 sw; log +2.23; TE 4.37 |
| `cond60_below0` | +1.92 [+1.08, +2.75] MDE 1.16 34y `reported` | +1.63 [+0.59, +2.67] MDE 1.35 38y `reported` | +1.97 [+0.85, +3.08] MDE 1.44 27y `reported` | +2.33 [+0.93, +3.72] MDE 2.06 30y `reported` | -1.90 [-3.81, +0.02] MDE 3.32 15y `reported` | +3.69 [+0.74, +6.63] MDE 4.76 17y `reported` | +4.02 [-0.79, +8.83] MDE 6.01 11y `reported` | -0.70 [-7.10, +5.70] MDE 11.32 198y `reported` | +2.38 [+0.75, +4.01] MDE 2.16 26y `reported` |
| `cond60_below0` detail | on 37%, 9 sw; log +1.89; TE 4.02 | on 29%, 7 sw; log +1.63; TE 3.58 | on 24%, 5 sw; log +1.97; TE 3.64 | on 48%, 3 sw; log +2.26; TE 4.57 | on 78%, 1 sw; log -1.92; TE 2.61 | on 72%, 1 sw; log +3.86; TE 5.38 | on 0%, 0 sw; log +3.95; TE 4.67 | on 100%, 0 sw; log -0.73; TE 3.50 | on 2%, 1 sw; log +2.28; TE 4.35 |
| `cond36_below_minus02` | +1.83 [+1.01, +2.65] MDE 1.13 37y `reported` | +1.65 [+0.61, +2.69] MDE 1.34 38y `reported` | +1.93 [+0.81, +3.05] MDE 1.42 28y `reported` | +2.09 [+0.75, +3.44] MDE 1.98 35y `reported` | -1.39 [-3.55, +0.77] MDE 3.78 36y `reported` | +3.74 [+1.00, +6.47] MDE 4.43 14y `reported` | +4.02 [-0.79, +8.83] MDE 6.00 11y `reported` | +0.49 [-7.58, +8.56] MDE 13.50 577y `reported` | +2.44 [+0.81, +4.07] MDE 2.16 25y `reported` |
| `cond36_below_minus02` detail | on 24%, 30 sw; log +1.80; TE 3.96 | on 16%, 18 sw; log +1.66; TE 3.63 | on 14%, 16 sw; log +1.94; TE 3.67 | on 36%, 13 sw; log +2.01; TE 4.41 | on 40%, 1 sw; log -1.37; TE 2.97 | on 56%, 8 sw; log +3.91; TE 5.00 | on 0%, 0 sw; log +3.94; TE 4.67 | on 67%, 1 sw; log +0.59; TE 4.17 | on 0%, 0 sw; log +2.34; TE 4.37 |
| `cond36_below_median120` | +1.60 [+0.69, +2.51] MDE 1.23 51y `reported` | +1.29 [+0.11, +2.46] MDE 1.48 63y `reported` | +1.60 [+0.32, +2.87] MDE 1.59 42y `reported` | +1.99 [+0.56, +3.42] MDE 2.05 41y `reported` | -1.45 [-3.65, +0.75] MDE 3.83 34y `reported` | +3.79 [+0.83, +6.75] MDE 4.83 16y `reported` | +2.32 [-2.27, +6.91] MDE 5.76 29y `reported` | +3.72 [-3.43, +10.87] MDE 13.00 9y `reported` | +2.32 [+0.61, +4.02] MDE 2.19 29y `reported` |
| `cond36_below_median120` detail | on 48%, 62 sw; log +1.59; TE 4.08 | on 37%, 30 sw; log +1.29; TE 3.63 | on 39%, 27 sw; log +1.58; TE 3.69 | on 61%, 32 sw; log +1.95; TE 4.56 | on 24%, 3 sw; log -1.31; TE 3.00 | on 93%, 5 sw; log +4.07; TE 5.45 | on 30%, 5 sw; log +2.28; TE 4.48 | on 11%, 1 sw; log +4.10; TE 4.02 | on 27%, 23 sw; log +2.24; TE 4.43 |

### The mechanism: bond excess return and realised correlation in on-months and off-months (descriptive)

| arm | window | months | on | on bond excess pp/yr | on corr | off bond excess pp/yr | off corr | all bond excess | all corr |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `cond36_below0` | full | 1151 | 0.394 | 2.71 | -0.1 | 2.05 | 0.195 | 2.31 | 0.075 |
| `cond36_below0` | complement_of_bond_bull | 685 | 0.309 | -1.63 | 0.167 | -0.12 | 0.163 | -0.59 | 0.164 |
| `cond36_below0` | before_bond_bull | 627 | 0.29 | -0.4 | 0.149 | 0.04 | 0.153 | -0.09 | 0.15 |
| `cond36_below0` | bond_bull_market | 466 | 0.519 | 6.52 | -0.289 | 6.66 | 0.284 | 6.58 | -0.021 |
| `cond36_below0` | after_bond_bull | 58 | 0.517 | -9.1 | 0.324 | -2.76 | 0.481 | -6.04 | 0.374 |
| `cond36_below0` | flat_equity_decade | 120 | 0.858 | 5.57 | -0.181 | -0.58 | 0.108 | 4.7 | -0.164 |
| `cond36_below0` | inflation_1977 | 57 | 0.0 | None | None | -12.4 | 0.355 | -12.4 | 0.355 |
| `cond36_below0` | rate_shock_2022 | 9 | 1.0 | -19.14 | 0.635 | None | None | -19.14 | 0.635 |
| `cond36_below0` | positive_bond_equity_correlation | 384 | 0.026 | -17.46 | 0.659 | 2.22 | 0.353 | 1.7 | 0.36 |
| `cond60_below0` | full | 1127 | 0.367 | 2.7 | -0.096 | 2.04 | 0.2 | 2.28 | 0.087 |
| `cond60_below0` | complement_of_bond_bull | 661 | 0.289 | -2.19 | 0.188 | -0.16 | 0.194 | -0.75 | 0.194 |
| `cond60_below0` | before_bond_bull | 603 | 0.242 | -0.35 | 0.137 | -0.21 | 0.194 | -0.24 | 0.181 |
| `cond60_below0` | bond_bull_market | 466 | 0.479 | 6.89 | -0.308 | 6.3 | 0.243 | 6.58 | -0.021 |
| `cond60_below0` | after_bond_bull | 58 | 0.776 | -8.15 | 0.408 | 1.28 | 0.141 | -6.04 | 0.374 |
| `cond60_below0` | flat_equity_decade | 120 | 0.725 | 5.49 | -0.16 | 2.61 | -0.217 | 4.7 | -0.164 |
| `cond60_below0` | inflation_1977 | 57 | 0.0 | None | None | -12.4 | 0.355 | -12.4 | 0.355 |
| `cond60_below0` | rate_shock_2022 | 9 | 1.0 | -19.14 | 0.635 | None | None | -19.14 | 0.635 |
| `cond60_below0` | positive_bond_equity_correlation | 384 | 0.021 | -11.08 | 0.131 | 1.98 | 0.359 | 1.7 | 0.36 |
| `cond36_below_minus02` | full | 1151 | 0.24 | 1.73 | -0.165 | 2.5 | 0.143 | 2.31 | 0.075 |
| `cond36_below_minus02` | complement_of_bond_bull | 685 | 0.159 | -4.29 | -0.002 | 0.11 | 0.188 | -0.59 | 0.164 |
| `cond36_below_minus02` | before_bond_bull | 627 | 0.137 | -2.64 | -0.044 | 0.32 | 0.171 | -0.09 | 0.15 |
| `cond36_below_minus02` | bond_bull_market | 466 | 0.358 | 5.66 | -0.294 | 7.1 | 0.104 | 6.58 | -0.021 |
| `cond36_below_minus02` | after_bond_bull | 58 | 0.397 | -10.45 | 0.157 | -3.14 | 0.565 | -6.04 | 0.374 |
| `cond36_below_minus02` | flat_equity_decade | 120 | 0.558 | 7.75 | -0.188 | 0.84 | -0.144 | 4.7 | -0.164 |
| `cond36_below_minus02` | inflation_1977 | 57 | 0.0 | None | None | -12.4 | 0.355 | -12.4 | 0.355 |
| `cond36_below_minus02` | rate_shock_2022 | 9 | 0.667 | -19.1 | 0.096 | -19.2 | 0.994 | -19.14 | 0.635 |
| `cond36_below_minus02` | positive_bond_equity_correlation | 384 | 0.0 | None | None | 1.7 | 0.36 | 1.7 | 0.36 |
| `cond36_below_median120` | full | 1032 | 0.481 | 1.9 | 0.041 | 2.19 | 0.109 | 2.05 | 0.079 |
| `cond36_below_median120` | complement_of_bond_bull | 566 | 0.373 | -2.06 | 0.172 | -1.46 | 0.238 | -1.69 | 0.215 |
| `cond36_below_median120` | before_bond_bull | 508 | 0.388 | -1.41 | 0.198 | -1.05 | 0.197 | -1.19 | 0.197 |
| `cond36_below_median120` | bond_bull_market | 466 | 0.612 | 4.83 | -0.013 | 9.34 | -0.033 | 6.58 | -0.021 |
| `cond36_below_median120` | after_bond_bull | 58 | 0.241 | -11.22 | 0.038 | -4.39 | 0.546 | -6.04 | 0.374 |
| `cond36_below_median120` | flat_equity_decade | 120 | 0.933 | 4.3 | -0.223 | 10.29 | 0.054 | 4.7 | -0.164 |
| `cond36_below_median120` | inflation_1977 | 57 | 0.298 | -26.9 | 0.364 | -6.23 | 0.311 | -12.4 | 0.355 |
| `cond36_below_median120` | rate_shock_2022 | 9 | 0.111 | -22.73 | None | -18.69 | 0.636 | -19.14 | 0.635 |
| `cond36_below_median120` | positive_bond_equity_correlation | 384 | 0.271 | 1.76 | 0.516 | 1.68 | 0.293 | 1.7 | 0.36 |

### Crisis episodes: arm cumulative return % (offset vs reference pp; offset vs unconditional pp; fraction on); * partial, n/c not covered

| arm | crash_1929 | recession_1937 | dotcom_2000 | gfc_2008 | covid_2020 | oil_1973 | inflation_1977 | rate_shock_2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base_trend30` | -82.78 (0.0; -0.25; on 0.0) | -50.34 (0.0; 0.07; on 0.0) | -40.68 (0.0; -2.31; on 0.0) | -45.86 (0.0; -1.46; on 0.0) | -18.63 (0.0; -2.14; on 0.0) | -34.29 (0.0; 2.54; on 0.0) | 86.01 (0.0; 22.07; on 0.0) | -23.57 (0.0; 2.38; on 0.0) |
| `trend30_bondstack20` | -82.53 (0.25; 0.0; on 1.0) | -50.42 (-0.07; 0.0; on 1.0) | -38.37 (2.31; 0.0; on 1.0) | -44.4 (1.46; 0.0; on 1.0) | -16.48 (2.14; 0.0; on 1.0) | -36.83 (-2.54; 0.0; on 1.0) | 63.93 (-22.07; 0.0; on 1.0) | -25.95 (-2.38; 0.0; on 1.0) |
| `cond36_below0` | -82.94 (-0.16; -0.42; on 0.912) | -50.62 (-0.28; -0.2; on 0.385) | -38.37 (2.31; -0.0; on 1.0) | -44.4 (1.46; 0.0; on 1.0) | -16.48 (2.14; 0.0; on 1.0) | -34.29 (0.0; 2.54; on 0.0) | 86.01 (-0.0; 22.07; on 0.0) | -25.95 (-2.38; -0.0; on 1.0) |
| `cond60_below0` | -64.62* (-0.14; 0.0; on 1.0) | -50.34 (0.0; 0.07; on 0.0) | -39.12 (1.56; -0.75; on 0.4) | -44.4 (1.46; -0.0; on 1.0) | -16.48 (2.14; 0.0; on 1.0) | -34.29 (-0.0; 2.54; on 0.0) | 86.01 (0.0; 22.07; on 0.0) | -25.95 (-2.38; -0.0; on 1.0) |
| `cond36_below_minus02` | -82.85 (-0.07; -0.33; on 0.647) | -50.78 (-0.44; -0.37; on 0.077) | -39.14 (1.53; -0.77; on 0.28) | -44.66 (1.2; -0.26; on 0.812) | -16.48 (2.14; 0.0; on 1.0) | -34.29 (0.0; 2.54; on 0.0) | 86.01 (-0.0; 22.07; on 0.0) | -25.16 (-1.6; 0.79; on 0.667) |
| `cond36_below_median120` | n/c | n/c | -38.37 (2.31; -0.0; on 1.0) | -45.65 (0.21; -1.25; on 0.75) | -17.54 (1.09; -1.05; on 0.5) | -34.8 (-0.5; 2.03; on 0.048) | 71.4 (-14.61; 7.47; on 0.298) | -23.91 (-0.35; 2.04; on 0.111) |

### On-spells of each conditioned arm

- `cond36_below0`: 1929-11..1932-03, 1932-05..1932-07, 1936-08..1937-07, 1939-10..1940-05, 1955-10..1966-02, 1966-04..1966-08, 1989-11..1990-01, 2000-08..2009-03, 2009-05..2023-01
- `cond60_below0`: 1931-07..1932-07, 1939-10..1940-05, 1956-04..1966-08, 2001-12..2009-03, 2009-05..2024-04
- `cond36_below_minus02`: 1929-12..1931-09, 1937-02..1937-03, 1956-05..1956-12, 1957-02..1960-04, 1960-08..1961-02, 1961-04..1961-06, 1965-07..1965-07, 1965-09..1965-12, 2002-03..2005-10, 2006-06..2006-09, 2007-05..2008-10, 2008-12..2008-12, 2011-10..2018-10, 2019-01..2019-01, 2019-06..2022-06
- `cond36_below_median120`: 1939-10..1942-09, 1943-07..1943-11, 1944-02..1944-04, 1948-12..1949-04, 1949-09..1951-09, 1953-01..1953-02, 1953-07..1961-07, 1965-07..1965-07, 1965-09..1965-12, 1974-04..1974-04, 1974-10..1974-10, 1980-02..1980-03, 1980-05..1980-05, 1980-08..1981-12, 1982-03..1982-05, 1982-07..1982-08, 1985-09..1985-12, 1987-06..1987-07, 1987-11..1990-10, 1993-09..1994-02, 1995-08..2006-03, 2006-05..2006-10, 2007-02..2008-10, 2011-11..2015-12, 2016-02..2016-10, 2016-12..2016-12, 2017-09..2018-02, 2018-08..2018-09, 2019-11..2019-11, 2020-03..2021-06, 2021-11..2022-01

### Deflation across the four arms

Mean off-diagonal correlation of the paired differences 0.694 on 1032 common months from 1939-06; effective trials 1.92 of 4 (linear reading, UNVERIFIED). Primary arm monthly Sharpe of the paired difference 0.0436 (annualised 0.1511); trial dispersion 0.0119.

| trials | SR* (monthly) | deflated significance |
| --- | ---: | ---: |
| effective (1.92) | 0.0057 | 0.8918 |
| declared_4 (4.0) | 0.0125 | 0.8448 |
| 100 (100.0) | 0.03 | 0.6708 |

### Regret, bp/yr of expected log growth (arithmetic on stated inputs; no status)

Inputs from the run: points 0.2, certain_cost_pp_yr_while_on 0.1144, fraction_on_full_window 0.394, switching_cost_pp_yr_realised 0.0075, rho_full_window 0.075, rho_on_state_realised -0.1, rho_after_bond_bull 0.374, sigma_bond_pct 8.55, sigma_reference_pct 19.01, bond_excess_full_window_pp_yr 2.31.

| state | term premium pp/yr | gap: conditioned | unconditional | neither | regret: conditioned | unconditional | neither |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| persists | -0.5 | -0.0 | -35.1 | 0.0 | 0.0 | 35.1 | -0.0 |
| persists | 0.0 | -0.0 | -25.1 | 0.0 | 0.0 | 25.1 | -0.0 |
| persists | 0.5 | -0.0 | -15.1 | 0.0 | 0.0 | 15.1 | -0.0 |
| persists | 1.0 | -0.0 | -5.1 | 0.0 | 0.0 | 5.1 | -0.0 |
| persists | 1.5 | 0.0 | 4.9 | 0.0 | 4.9 | 0.0 | 4.9 |
| reverts | -0.5 | -8.5 | -25.3 | 0.0 | 8.5 | 25.3 | 0.0 |
| reverts | 0.0 | -4.6 | -15.3 | 0.0 | 4.6 | 15.3 | 0.0 |
| reverts | 0.5 | -0.6 | -5.3 | 0.0 | 0.6 | 5.3 | 0.0 |
| reverts | 1.0 | 3.3 | 4.7 | 0.0 | 1.3 | 0.0 | 4.7 |
| reverts | 1.5 | 7.3 | 14.7 | 0.0 | 7.4 | 0.0 | 14.7 |

Max regret: conditioned 8.5, unconditional 35.1, neither 14.7; minimax action `conditioned`.
