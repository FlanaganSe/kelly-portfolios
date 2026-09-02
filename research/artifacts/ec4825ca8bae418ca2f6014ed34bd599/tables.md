### Experiment 022 tables. k = 0.4 was chosen on this workbook by the study this run registers; the status ceiling is exploratory. The workbook is revised on every release and the equity price is a monthly average. The signal is lagged one month; no tax is charged.

**full, monthly clock.** Gap in pp/yr, gross, HAC 95% interval, MDE80 floor beside it; net at 10 bp in the last column against the risk-matched control.

| arm | mean w | turnover/yr | rebal/yr | vs risk_matched | vs equity100 | vs mix85 | net10 vs risk_matched | log gap vs rm | status |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | --- |
| `k02_treasury` | 0.802 | 0.087 | 11.99 | +0.31 [+0.13, +0.50] floor 0.21 | -1.00 [-1.76, -0.23] floor 0.86 | -0.00 [-0.26, +0.26] floor 0.28 | +0.31 | +0.31 | exploratory (e) clears every clause; ceiling is exploratory |
| `k04_treasury` | 0.804 | 0.124 | 11.99 | +0.63 [+0.26, +0.99] floor 0.42 | -0.67 [-1.50, +0.16] floor 0.91 | +0.32 [-0.09, +0.73] floor 0.45 | +0.62 | +0.61 | exploratory (e) clears every clause; ceiling is exploratory |
| `k06_treasury` | 0.802 | 0.160 | 10.83 | +0.92 [+0.39, +1.45] floor 0.61 | -0.39 [-1.31, +0.54] floor 1.00 | +0.61 [+0.04, +1.17] floor 0.63 | +0.91 | +0.88 | exploratory (e) clears every clause; ceiling is exploratory |
| `k02_tips` | 0.802 | 0.085 | 11.99 | +0.31 [+0.13, +0.49] floor 0.21 | -0.98 [-1.73, -0.23] floor 0.84 | -0.00 [-0.26, +0.25] floor 0.28 | +0.31 | +0.30 | exploratory (e) clears every clause; ceiling is exploratory |
| `k04_tips` | 0.804 | 0.123 | 11.99 | +0.62 [+0.25, +0.98] floor 0.42 | -0.66 [-1.47, +0.16] floor 0.89 | +0.32 [-0.09, +0.72] floor 0.45 | +0.61 | +0.59 | exploratory (e) clears every clause; ceiling is exploratory |
| `k06_tips` | 0.802 | 0.159 | 10.83 | +0.90 [+0.37, +1.43] floor 0.61 | -0.38 [-1.29, +0.53] floor 0.98 | +0.59 [+0.03, +1.16] floor 0.62 | +0.89 | +0.86 | exploratory (e) clears every clause; ceiling is exploratory |
| `sens_tips_signal` | 0.802 | 0.120 | 11.99 | +0.61 [+0.24, +0.98] floor 0.42 | -0.70 [-1.54, +0.15] floor 0.92 | +0.30 [-0.12, +0.72] floor 0.45 | +0.61 | +0.59 | exploratory (e) clears every clause; ceiling is exploratory |
| `sens_lag_zero` | 0.803 | 0.147 | 11.99 | +0.49 [+0.15, +0.83] floor 0.40 | -0.81 [-1.63, +0.00] floor 0.90 | +0.18 [-0.21, +0.57] floor 0.43 | +0.48 | +0.47 | exploratory (e) clears every clause; ceiling is exploratory |
| `sens_french` | 0.796 | 0.130 | 11.99 | +0.68 [+0.29, +1.08] floor 0.48 | -0.70 [-1.60, +0.20] floor 1.13 | +0.31 [-0.14, +0.76] floor 0.53 | +0.68 | +0.65 | exploratory (e) clears every clause; ceiling is exploratory |
| `sens_shiller_french_window` | 0.796 | 0.129 | 11.99 | +0.64 [+0.27, +1.01] floor 0.44 | -0.67 [-1.55, +0.21] floor 0.96 | +0.29 [-0.13, +0.72] floor 0.47 | +0.63 | +0.61 | exploratory (e) clears every clause; ceiling is exploratory |

**full, annual_band clock.** Gap in pp/yr, gross, HAC 95% interval, MDE80 floor beside it; net at 10 bp in the last column against the risk-matched control.

| arm | mean w | turnover/yr | rebal/yr | vs risk_matched | vs equity100 | vs mix85 | net10 vs risk_matched | log gap vs rm | status |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | --- |
| `k02_treasury` | 0.802 | 0.030 | 0.37 | +0.26 [+0.05, +0.46] floor 0.22 | -0.88 [-1.68, -0.08] floor 0.93 | -0.03 [-0.31, +0.26] floor 0.30 | +0.25 | +0.25 | exploratory (e) clears every clause; ceiling is exploratory |
| `k04_treasury` | 0.804 | 0.045 | 0.51 | +0.54 [+0.16, +0.92] floor 0.41 | -0.59 [-1.46, +0.29] floor 0.98 | +0.27 [-0.16, +0.70] floor 0.45 | +0.54 | +0.53 | exploratory (e) clears every clause; ceiling is exploratory |
| `k06_treasury` | 0.802 | 0.060 | 0.58 | +0.83 [+0.31, +1.36] floor 0.59 | -0.30 [-1.26, +0.66] floor 1.06 | +0.56 [-0.01, +1.13] floor 0.61 | +0.83 | +0.81 | exploratory (e) clears every clause; ceiling is exploratory |
| `k02_tips` | 0.802 | 0.030 | 0.37 | +0.25 [+0.04, +0.45] floor 0.22 | -0.86 [-1.64, -0.09] floor 0.90 | -0.03 [-0.31, +0.25] floor 0.30 | +0.24 | +0.25 | exploratory (e) clears every clause; ceiling is exploratory |
| `k04_tips` | 0.804 | 0.044 | 0.52 | +0.52 [+0.14, +0.89] floor 0.41 | -0.58 [-1.41, +0.25] floor 0.94 | +0.25 [-0.16, +0.67] floor 0.44 | +0.51 | +0.51 | exploratory (e) clears every clause; ceiling is exploratory |
| `k06_tips` | 0.802 | 0.060 | 0.58 | +0.80 [+0.28, +1.32] floor 0.58 | -0.31 [-1.22, +0.61] floor 1.03 | +0.53 [-0.03, +1.08] floor 0.60 | +0.79 | +0.78 | exploratory (e) clears every clause; ceiling is exploratory |
| `sens_tips_signal` | 0.802 | 0.044 | 0.51 | +0.49 [+0.11, +0.87] floor 0.41 | -0.64 [-1.52, +0.23] floor 0.98 | +0.21 [-0.22, +0.64] floor 0.45 | +0.49 | +0.48 | exploratory (e) clears every clause; ceiling is exploratory |
| `sens_lag_zero` | 0.803 | 0.044 | 0.51 | +0.49 [+0.13, +0.84] floor 0.38 | -0.64 [-1.49, +0.21] floor 0.96 | +0.22 [-0.19, +0.62] floor 0.42 | +0.49 | +0.48 | exploratory (e) clears every clause; ceiling is exploratory |
| `sens_french` | 0.796 | 0.047 | 0.47 | +0.64 [+0.22, +1.07] floor 0.53 | -0.55 [-1.54, +0.44] floor 1.28 | +0.31 [-0.19, +0.81] floor 0.63 | +0.64 | +0.65 | exploratory (e) clears every clause; ceiling is exploratory |
| `sens_shiller_french_window` | 0.796 | 0.048 | 0.50 | +0.58 [+0.21, +0.95] floor 0.45 | -0.45 [-1.42, +0.51] floor 1.03 | +0.34 [-0.15, +0.83] floor 0.52 | +0.58 | +0.57 | exploratory (e) clears every clause; ceiling is exploratory |

**modern, monthly clock.** Gap in pp/yr, gross, HAC 95% interval, MDE80 floor beside it; net at 10 bp in the last column against the risk-matched control.

| arm | mean w | turnover/yr | rebal/yr | vs risk_matched | vs equity100 | vs mix85 | net10 vs risk_matched | log gap vs rm | status |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | --- |
| `k02_treasury` | 0.772 | 0.091 | 11.97 | +0.18 [-0.04, +0.41] floor 0.24 | -1.32 [-2.67, +0.03] floor 1.50 | -0.33 [-0.83, +0.17] floor 0.53 | +0.18 | +0.18 | unresolved (b) gap inside its own 80%-power floor |
| `k04_treasury` | 0.744 | 0.136 | 11.97 | +0.37 [-0.09, +0.83] floor 0.49 | -1.32 [-2.86, +0.23] floor 1.68 | -0.33 [-1.07, +0.41] floor 0.77 | +0.36 | +0.35 | unresolved (b) gap inside its own 80%-power floor |
| `k06_treasury` | 0.716 | 0.185 | 11.97 | +0.55 [-0.13, +1.24] floor 0.73 | -1.32 [-3.08, +0.44] floor 1.89 | -0.33 [-1.33, +0.67] floor 1.03 | +0.54 | +0.52 | unresolved (b) gap inside its own 80%-power floor |
| `k02_tips` | 0.772 | 0.087 | 11.97 | +0.15 [-0.06, +0.36] floor 0.22 | -1.26 [-2.52, +0.00] floor 1.40 | -0.33 [-0.81, +0.15] floor 0.51 | +0.15 | +0.15 | unresolved (b) gap inside its own 80%-power floor |
| `k04_tips` | 0.744 | 0.133 | 11.97 | +0.30 [-0.11, +0.72] floor 0.44 | -1.28 [-2.75, +0.19] floor 1.59 | -0.35 [-1.08, +0.38] floor 0.75 | +0.30 | +0.29 | unresolved (b) gap inside its own 80%-power floor |
| `k06_tips` | 0.716 | 0.182 | 11.97 | +0.46 [-0.17, +1.08] floor 0.66 | -1.30 [-2.99, +0.39] floor 1.81 | -0.37 [-1.36, +0.61] floor 1.01 | +0.45 | +0.43 | unresolved (b) gap inside its own 80%-power floor |
| `sens_tips_signal` | 0.740 | 0.125 | 11.97 | +0.32 [-0.12, +0.76] floor 0.46 | -1.39 [-2.99, +0.20] floor 1.72 | -0.41 [-1.18, +0.37] floor 0.79 | +0.32 | +0.31 | unresolved (b) gap inside its own 80%-power floor |
| `sens_lag_zero` | 0.744 | 0.163 | 11.97 | +0.27 [-0.19, +0.72] floor 0.49 | -1.42 [-2.95, +0.10] floor 1.65 | -0.43 [-1.16, +0.29] floor 0.75 | +0.26 | +0.24 | unresolved (b) gap inside its own 80%-power floor |
| `sens_french` | 0.744 | 0.140 | 11.97 | +0.40 [-0.08, +0.88] floor 0.57 | -1.41 [-2.98, +0.16] floor 1.99 | -0.35 [-1.11, +0.41] floor 0.94 | +0.40 | +0.38 | unresolved (b) gap inside its own 80%-power floor |
| `sens_shiller_french_window` | 0.744 | 0.136 | 11.97 | +0.37 [-0.08, +0.83] floor 0.49 | -1.30 [-2.84, +0.25] floor 1.69 | -0.32 [-1.06, +0.43] floor 0.77 | +0.37 | +0.35 | unresolved (b) gap inside its own 80%-power floor |

**modern, annual_band clock.** Gap in pp/yr, gross, HAC 95% interval, MDE80 floor beside it; net at 10 bp in the last column against the risk-matched control.

| arm | mean w | turnover/yr | rebal/yr | vs risk_matched | vs equity100 | vs mix85 | net10 vs risk_matched | log gap vs rm | status |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | --- |
| `k02_treasury` | 0.772 | 0.027 | 0.31 | +0.14 [-0.11, +0.39] floor 0.30 | -1.12 [-2.50, +0.26] floor 1.52 | -0.36 [-0.89, +0.16] floor 0.57 | +0.14 | +0.13 | unresolved (b) gap inside its own 80%-power floor |
| `k04_treasury` | 0.744 | 0.041 | 0.36 | +0.28 [-0.16, +0.72] floor 0.50 | -1.15 [-2.87, +0.58] floor 1.85 | -0.39 [-1.27, +0.49] floor 0.92 | +0.27 | +0.28 | unresolved (b) gap inside its own 80%-power floor |
| `k06_treasury` | 0.716 | 0.061 | 0.45 | +0.49 [-0.17, +1.15] floor 0.75 | -1.09 [-3.07, +0.89] floor 2.10 | -0.34 [-1.50, +0.82] floor 1.21 | +0.49 | +0.49 | unresolved (b) gap inside its own 80%-power floor |
| `k02_tips` | 0.772 | 0.029 | 0.31 | +0.16 [-0.07, +0.39] floor 0.29 | -1.04 [-2.34, +0.26] floor 1.45 | -0.23 [-0.79, +0.33] floor 0.60 | +0.16 | +0.16 | unresolved (b) gap inside its own 80%-power floor |
| `k04_tips` | 0.744 | 0.035 | 0.31 | +0.17 [-0.26, +0.61] floor 0.51 | -1.18 [-2.68, +0.31] floor 1.65 | -0.37 [-1.16, +0.42] floor 0.84 | +0.17 | +0.17 | unresolved (b) gap inside its own 80%-power floor |
| `k06_tips` | 0.716 | 0.057 | 0.39 | +0.35 [-0.28, +0.98] floor 0.74 | -1.13 [-2.93, +0.67] floor 1.96 | -0.31 [-1.43, +0.80] floor 1.19 | +0.35 | +0.35 | unresolved (b) gap inside its own 80%-power floor |
| `sens_tips_signal` | 0.740 | 0.035 | 0.31 | +0.16 [-0.26, +0.57] floor 0.48 | -1.29 [-2.92, +0.34] floor 1.78 | -0.54 [-1.34, +0.27] floor 0.86 | +0.15 | +0.15 | unresolved (b) gap inside its own 80%-power floor |
| `sens_lag_zero` | 0.744 | 0.040 | 0.34 | +0.22 [-0.21, +0.64] floor 0.49 | -1.21 [-2.87, +0.46] floor 1.81 | -0.45 [-1.28, +0.38] floor 0.89 | +0.21 | +0.22 | unresolved (b) gap inside its own 80%-power floor |
| `sens_french` | 0.744 | 0.042 | 0.37 | +0.31 [-0.16, +0.77] floor 0.59 | -1.31 [-3.06, +0.44] floor 2.14 | -0.37 [-1.29, +0.54] floor 1.07 | +0.31 | +0.32 | unresolved (b) gap inside its own 80%-power floor |
| `sens_shiller_french_window` | 0.744 | 0.041 | 0.37 | +0.28 [-0.17, +0.72] floor 0.50 | -1.13 [-2.86, +0.60] floor 1.86 | -0.38 [-1.26, +0.50] floor 0.92 | +0.27 | +0.28 | unresolved (b) gap inside its own 80%-power floor |

**Holm within the six-arm family, risk-matched control, gross.**

| window | arm | gap pp/yr | HAC p | Holm-adjusted p |
| --- | --- | ---: | ---: | ---: |
| full | `k02_treasury` | +0.315 | 0.0007 | 0.0041 |
| full | `k04_treasury` | +0.629 | 0.0007 | 0.0041 |
| full | `k06_treasury` | +0.921 | 0.0007 | 0.0041 |
| full | `k02_tips` | +0.308 | 0.0009 | 0.0041 |
| full | `k04_tips` | +0.616 | 0.0009 | 0.0041 |
| full | `k06_tips` | +0.901 | 0.0009 | 0.0041 |
| modern | `k02_treasury` | +0.184 | 0.1141 | 0.6845 |
| modern | `k04_treasury` | +0.369 | 0.1141 | 0.6845 |
| modern | `k06_treasury` | +0.553 | 0.1141 | 0.6845 |
| modern | `k02_tips` | +0.152 | 0.1510 | 0.6845 |
| modern | `k04_tips` | +0.305 | 0.1510 | 0.6845 |
| modern | `k06_tips` | +0.457 | 0.1510 | 0.6845 |

**Deflated Sharpe of the primary active return.** monthly SR 0.1175, trial dispersion 0.0012, mean off-diagonal rho 0.998, effective trials 1.01 of 6; DSR nominal_6: 1.000, effective: 1.000, 100: 1.000

**Rolling 30-year windows, full window, monthly clock, gross.**

| arm | control | windows | independent | share ahead | median bp | p10 bp | p90 bp |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `k02_treasury` | risk_matched | 908 | 2.52 | 0.999 | +17.5 | +6.9 | +78.3 |
| `k02_treasury` | equity100 | 908 | 2.52 | 0.000 | -78.4 | -155.1 | -39.5 |
| `k02_treasury` | mix85 | 908 | 2.52 | 0.304 | -5.9 | -14.8 | +37.9 |
| `k04_treasury` | risk_matched | 908 | 2.52 | 0.999 | +34.9 | +13.8 | +156.7 |
| `k04_treasury` | equity100 | 908 | 2.52 | 0.080 | -56.9 | -114.1 | -6.7 |
| `k04_treasury` | mix85 | 908 | 2.52 | 0.850 | +16.0 | -7.2 | +119.3 |
| `k06_treasury` | risk_matched | 908 | 2.52 | 1.000 | +53.4 | +22.0 | +226.6 |
| `k06_treasury` | equity100 | 908 | 2.52 | 0.169 | -41.7 | -84.8 | +59.7 |
| `k06_treasury` | mix85 | 908 | 2.52 | 0.907 | +33.9 | +1.2 | +189.5 |
| `k02_tips` | risk_matched | 908 | 2.52 | 0.998 | +17.5 | +4.9 | +78.3 |
| `k02_tips` | equity100 | 908 | 2.52 | 0.000 | -78.1 | -155.1 | -38.2 |
| `k02_tips` | mix85 | 908 | 2.52 | 0.322 | -6.2 | -15.4 | +37.9 |
| `k04_tips` | risk_matched | 908 | 2.52 | 0.998 | +34.9 | +9.8 | +156.7 |
| `k04_tips` | equity100 | 908 | 2.52 | 0.080 | -56.8 | -112.7 | -6.3 |
| `k04_tips` | mix85 | 908 | 2.52 | 0.839 | +16.5 | -9.2 | +119.3 |
| `k06_tips` | risk_matched | 908 | 2.52 | 1.000 | +53.4 | +16.0 | +226.6 |
| `k06_tips` | equity100 | 908 | 2.52 | 0.169 | -42.3 | -84.8 | +59.7 |
| `k06_tips` | mix85 | 908 | 2.52 | 0.867 | +34.7 | -3.5 | +189.5 |
| `sens_tips_signal` | risk_matched | 908 | 2.52 | 0.998 | +34.7 | +12.8 | +157.8 |
| `sens_tips_signal` | equity100 | 908 | 2.52 | 0.081 | -57.6 | -115.5 | -5.7 |
| `sens_tips_signal` | mix85 | 908 | 2.52 | 0.845 | +15.9 | -8.5 | +119.3 |
| `sens_lag_zero` | risk_matched | 908 | 2.52 | 0.948 | +27.6 | +3.3 | +128.0 |
| `sens_lag_zero` | equity100 | 908 | 2.52 | 0.001 | -64.6 | -122.2 | -24.6 |
| `sens_lag_zero` | mix85 | 908 | 2.52 | 0.693 | +7.7 | -17.3 | +90.7 |
| `sens_french` | risk_matched | 841 | 2.34 | 1.000 | +40.1 | +16.8 | +102.9 |
| `sens_french` | equity100 | 841 | 2.34 | 0.032 | -69.2 | -123.0 | -26.1 |
| `sens_french` | mix85 | 841 | 2.34 | 0.844 | +15.0 | -10.1 | +54.4 |
| `sens_shiller_french_window` | risk_matched | 841 | 2.34 | 1.000 | +34.8 | +16.6 | +107.6 |
| `sens_shiller_french_window` | equity100 | 841 | 2.34 | 0.036 | -61.4 | -114.6 | -16.5 |
| `sens_shiller_french_window` | mix85 | 841 | 2.34 | 0.841 | +13.8 | -7.6 | +59.3 |

**Drawdown, full window, monthly clock, gross (descriptive).**

| arm | mean_weight | max_drawdown_pct | time_under_water_months | risk_matched_max_drawdown_pct | equity100_max_drawdown_pct | mix85_max_drawdown_pct | min_weight | max_weight |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k02_treasury | 0.8018 | -63.79 | 141.0 | -65.88 | -76.8 | -68.88 | 0.7014 | 0.9 |
| k04_treasury | 0.8036 | -61.76 | 123.0 | -66.0 | -76.8 | -68.88 | 0.6028 | 1.0 |
| k06_treasury | 0.8024 | -59.67 | 122.0 | -65.92 | -76.8 | -68.88 | 0.5042 | 1.0 |
| k02_tips | 0.8018 | -63.79 | 141.0 | -65.88 | -76.8 | -68.88 | 0.7014 | 0.9 |
| k04_tips | 0.8036 | -61.76 | 123.0 | -66.0 | -76.8 | -68.88 | 0.6028 | 1.0 |
| k06_tips | 0.8024 | -59.67 | 122.0 | -65.92 | -76.8 | -68.88 | 0.5042 | 1.0 |
| sens_tips_signal | 0.8021 | -61.76 | 123.0 | -65.9 | -76.8 | -68.88 | 0.6028 | 1.0 |
| sens_lag_zero | 0.8034 | -62.88 | 123.0 | -65.98 | -76.8 | -68.88 | 0.6028 | 0.9958 |
| sens_french | 0.7956 | -63.69 | 120.0 | -68.14 | -79.2 | -71.5 | 0.6028 | 0.9693 |
| sens_shiller_french_window | 0.7956 | -61.76 | 123.0 | -65.48 | -76.8 | -68.88 | 0.6028 | 0.9693 |

**Crisis episodes, primary arm (descriptive).**

| episode | start | end | covered | months | entry_equity_weight | rule_cumulative_pct | rule_worst_drawdown_pct | risk_matched_cumulative_pct | risk_matched_worst_drawdown_pct | equity100_cumulative_pct | equity100_worst_drawdown_pct | mix85_cumulative_pct | mix85_worst_drawdown_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| crash_1929 | 1929-09 | 1932-06 | True | 34 | 0.6295 | -59.56 | -61.76 | -64.28 | -66.0 | -75.37 | -76.8 | -67.24 | -68.88 |
| dotcom_2000 | 2000-09 | 2002-09 | True | 25 | 0.6123 | -24.65 | -24.65 | -32.74 | -32.74 | -42.55 | -42.55 | -35.17 | -35.17 |
| gfc_2008 | 2007-11 | 2009-02 | True | 16 | 0.7233 | -38.66 | -39.37 | -37.8 | -38.55 | -47.1 | -47.79 | -40.11 | -40.84 |
| covid_2020 | 2020-02 | 2020-03 | True | 2 | 0.7904 | -9.52 | -13.48 | -9.87 | -13.81 | -14.66 | -18.74 | -11.0 | -14.98 |
| rate_shock_2022 | 2022-01 | 2022-09 | True | 9 | 0.7918 | -21.79 | -21.79 | -21.85 | -21.85 | -22.24 | -22.24 | -21.94 | -21.94 |

**Eras, primary arm against the risk-matched control, gross.**

| era | months | gap_vs_risk_matched_bp_yr | mean_weight |
| --- | --- | --- | --- |
| full | 1267 | 62.9 | 0.8036 |
| modern | 429 | -2.4 | 0.744 |
| study_1921_1950 | 348 | 149.5 | 0.8562 |
| study_1950_1980 | 360 | 56.4 | 0.8117 |
| study_1980_2000 | 240 | -24.0 | 0.7694 |
| study_2000_on | 319 | 41.2 | 0.7628 |
| tips_era | 282 | -5.0 | 0.7751 |

**Stambaugh bias of the signal's one-month predictive slope.**

| alignment | autoregressive_root_monthly | innovation_correlation | slope_monthly_per_pp | bias_monthly_per_pp | bias_share_of_slope | slope_annualised_uncorrected | slope_annualised_corrected | n_observations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| row_t_page_convention | 0.987948 | -0.241193 | 0.001092 | 8.2e-05 | 0.075014 | 0.013106 | 0.012123 | 1267.0 |
| lag_1_as_traded | 0.986712 | 0.030041 | 0.001353 | -1e-05 | -0.007483 | 0.016237 | 0.016358 | 1267.0 |

**Regret of the 85/15 position against 100% equity (arithmetic, no forecast).**

| premium_over_bond_pp_yr | arithmetic_cost_bp_yr | log_growth_gap_bp_yr | regret_of_position_bp_yr | regret_of_counterfactual_bp_yr | terminal_wealth_ratio_10y_pct | terminal_wealth_ratio_30y_pct |
| --- | --- | --- | --- | --- | --- | --- |
| 0.0 | 0.0 | 30.7 | 0.0 | 30.7 | 3.11 | 9.64 |
| 1.5 | 22.5 | 8.2 | 0.0 | 8.2 | 0.82 | 2.48 |
| 3.0 | 45.0 | -14.3 | 14.3 | 0.0 | -1.42 | -4.21 |
| 5.0 | 75.0 | -44.3 | 44.3 | 0.0 | -4.34 | -12.45 |

**Today.** {'row': '2026-08', 'shiller': {'signal_pp': 0.974, 'expanding_percentile': 0.1872, 'weight_k0.4': 0.6749, 'scaled_to_all_equity_divide': 0.8436, 'scaled_to_all_equity_cut': 0.8749}, 'tips_spliced': {'signal_pp': 0.029, 'expanding_percentile': 0.0693, 'weight_k0.4': 0.6277, 'scaled_to_all_equity_divide': 0.7846, 'scaled_to_all_equity_cut': 0.8277}, 'tips_first_return_month': '2003-02'}

**Construction.** {'third_size_pp': 33.3, 'rule_equity_weight_today': 0.8436, 'bond_pp_of_portfolio': 5.21, 'line_sold': 'RSST', 'rsst_before_pp': 30.0, 'rsst_after_pp': 24.79, 'idmo_unchanged_pp': 3.3, 'equity_notional_cut_pp': 5.59, 'trend_notional_cut_pp': 5.21, 'published_vector_sums_to': 100.0, 'gross_exposure_before': 1.3216, 'gross_exposure_after': 1.2657, 'note': 'Selling the wrapper line keeps IDMO, which the rebalancing page says to keep, and moves no taxable line, so headroom is unchanged; the cost is the trend notional the wrapper carried on the sold capital.'}