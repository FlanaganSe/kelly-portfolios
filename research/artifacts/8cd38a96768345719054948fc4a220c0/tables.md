# Cautious defensive-budget comparisons

Exploratory actual-NAV portfolios. Every candidate replaces only the defensive 50%.

Nominal drawdown uses all fund-return months. Real drawdown/shortfall uses only observed CPI dates and misses 2025-10: it can understate full-month downside.

Real endpoint wealth/growth uses observed CPI endpoints. CPI is a monthly price index, not a trading-date deflator. No interpolation or extra TIPS inflation return.

No withdrawals: incomplete monthly CPI prevents the optional indexed-spending test. No retirement adequacy or future shortfall claim.

5/25 bp roundtrip means 2.5/12.5 bp per dollar bought/sold, initial purchase and annual rebalance paid. NAV already includes internal costs; no taxes or terminal sale.

Paired six-month-block/2000-draw bootstrap reruns all execution paths. Cheap control is 32.5% VTI / 17.5% VXUS / 50% SCHP, not risk-, beta- or leverage-matched.

## actual_cautious: 2023-10 to 2026-03, 5bp

Published Cautious non-defensive holdings, including RSST 15%, stay fixed.

| Arm | Nominal CAGR% | Nominal DD% all months | Real terminal wealth | Real CAGR% | Real DD% observed CPI | Max real-principal shortfall% observed CPI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| schp | 12.601 | -4.501 | 1.2541 | 9.478 | -5.492 | 1.884 |
| short_tips | 12.750 | -3.846 | 1.2582 | 9.622 | -4.845 | 1.328 |
| bills | 12.237 | -3.733 | 1.2439 | 9.123 | -4.733 | 1.293 |
| intermediate_treasury | 12.546 | -4.943 | 1.2525 | 9.425 | -5.930 | 2.479 |
| short_tips_bills | 12.493 | -3.790 | 1.2511 | 9.373 | -4.789 | 1.311 |
| schp_bills | 12.421 | -4.117 | 1.2490 | 9.303 | -5.113 | 1.589 |
| cheap | 12.558 | -3.916 | 1.2528 | 9.435 | -4.914 | 1.825 |

| Comparison | Log gap pp/yr[95%] | Wealth ratio | TE pp/yr | Losing rolling 12m | Worst rolling 12m ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| schp vs cheap | +0.039 [-2.185,+2.808] | 1.0010 | 1.941 | 68.4% | 0.9704 |
| short_tips vs schp | +0.131 [-0.844,+1.159] | 1.0033 | 1.445 | 36.8% | 0.9906 |
| short_tips vs cheap | +0.170 [-2.442,+3.005] | 1.0043 | 2.415 | 57.9% | 0.9682 |
| bills vs schp | -0.325 [-1.790,+1.070] | 0.9919 | 2.055 | 73.7% | 0.9818 |
| bills vs cheap | -0.286 [-3.236,+2.900] | 0.9929 | 2.842 | 68.4% | 0.9580 |
| intermediate_treasury vs schp | -0.049 [-1.080,+0.973] | 0.9988 | 1.450 | 47.4% | 0.9856 |
| intermediate_treasury vs cheap | -0.010 [-2.504,+2.837] | 0.9998 | 2.326 | 68.4% | 0.9684 |
| short_tips_bills vs schp | -0.096 [-1.299,+1.086] | 0.9976 | 1.730 | 57.9% | 0.9862 |
| short_tips_bills vs cheap | -0.057 [-2.812,+2.931] | 0.9986 | 2.606 | 57.9% | 0.9646 |
| schp_bills vs schp | -0.160 [-0.888,+0.537] | 0.9960 | 1.028 | 73.7% | 0.9909 |
| schp_bills vs cheap | -0.121 [-2.615,+2.789] | 0.9970 | 2.206 | 68.4% | 0.9642 |
| cheap vs schp | -0.039 [-2.808,+2.185] | 0.9990 | 1.941 | 31.6% | 0.9702 |

## actual_cautious: 2023-10 to 2026-03, 25bp

Published Cautious non-defensive holdings, including RSST 15%, stay fixed.

| Arm | Nominal CAGR% | Nominal DD% all months | Real terminal wealth | Real CAGR% | Real DD% observed CPI | Max real-principal shortfall% observed CPI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| schp | 12.550 | -4.501 | 1.2526 | 9.428 | -5.492 | 1.982 |
| short_tips | 12.698 | -3.846 | 1.2568 | 9.572 | -4.845 | 1.427 |
| bills | 12.185 | -3.733 | 1.2425 | 9.073 | -4.733 | 1.392 |
| intermediate_treasury | 12.495 | -4.943 | 1.2511 | 9.375 | -5.930 | 2.576 |
| short_tips_bills | 12.442 | -3.790 | 1.2496 | 9.323 | -4.789 | 1.410 |
| schp_bills | 12.370 | -4.117 | 1.2476 | 9.253 | -5.113 | 1.687 |
| cheap | 12.506 | -3.916 | 1.2514 | 9.385 | -4.914 | 1.923 |

| Comparison | Log gap pp/yr[95%] | Wealth ratio | TE pp/yr | Losing rolling 12m | Worst rolling 12m ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| schp vs cheap | +0.040 [-2.186,+2.805] | 1.0010 | 1.941 | 68.4% | 0.9705 |
| short_tips vs schp | +0.131 [-0.844,+1.159] | 1.0033 | 1.444 | 36.8% | 0.9906 |
| short_tips vs cheap | +0.171 [-2.442,+3.001] | 1.0043 | 2.415 | 57.9% | 0.9682 |
| bills vs schp | -0.325 [-1.790,+1.070] | 0.9919 | 2.054 | 73.7% | 0.9818 |
| bills vs cheap | -0.286 [-3.238,+2.898] | 0.9929 | 2.842 | 68.4% | 0.9580 |
| intermediate_treasury vs schp | -0.049 [-1.080,+0.973] | 0.9988 | 1.450 | 47.4% | 0.9856 |
| intermediate_treasury vs cheap | -0.009 [-2.506,+2.835] | 0.9998 | 2.325 | 68.4% | 0.9684 |
| short_tips_bills vs schp | -0.096 [-1.300,+1.086] | 0.9976 | 1.729 | 57.9% | 0.9862 |
| short_tips_bills vs cheap | -0.057 [-2.812,+2.929] | 0.9986 | 2.606 | 57.9% | 0.9646 |
| schp_bills vs schp | -0.161 [-0.889,+0.537] | 0.9960 | 1.028 | 73.7% | 0.9909 |
| schp_bills vs cheap | -0.121 [-2.613,+2.788] | 0.9970 | 2.206 | 68.4% | 0.9642 |
| cheap vs schp | -0.040 [-2.805,+2.186] | 0.9990 | 1.941 | 31.6% | 0.9702 |

## no_trend_diagnostic: 2021-10 to 2026-03, 5bp

RSST 15% becomes additional VTI 15% in every arm: a different portfolio.

| Arm | Nominal CAGR% | Nominal DD% all months | Real terminal wealth | Real CAGR% | Real DD% observed CPI | Max real-principal shortfall% observed CPI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| schp | 5.628 | -18.716 | 1.0628 | 1.363 | -23.647 | 21.476 |
| short_tips | 7.108 | -14.065 | 1.1315 | 2.783 | -19.278 | 17.432 |
| bills | 7.456 | -11.888 | 1.1481 | 3.117 | -17.234 | 15.814 |
| intermediate_treasury | 4.702 | -19.822 | 1.0215 | 0.475 | -24.686 | 23.319 |
| short_tips_bills | 7.283 | -12.980 | 1.1398 | 2.951 | -18.259 | 16.623 |
| schp_bills | 6.554 | -15.321 | 1.1054 | 2.252 | -20.458 | 18.645 |
| cheap | 5.093 | -19.662 | 1.0388 | 0.849 | -24.536 | 22.435 |

| Comparison | Log gap pp/yr[95%] | Wealth ratio | TE pp/yr | Losing rolling 12m | Worst rolling 12m ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| schp vs cheap | +0.508 [-0.203,+1.263] | 1.0231 | 0.867 | 34.9% | 0.9906 |
| short_tips vs schp | +1.391 [-0.039,+2.997] | 1.0646 | 1.932 | 16.3% | 0.9907 |
| short_tips vs cheap | +1.899 [+0.052,+3.989] | 1.0892 | 2.291 | 9.3% | 0.9884 |
| bills vs schp | +1.716 [-0.424,+4.077] | 1.0803 | 3.108 | 34.9% | 0.9821 |
| bills vs cheap | +2.224 [-0.262,+4.939] | 1.1052 | 3.338 | 30.2% | 0.9798 |
| intermediate_treasury vs schp | -0.880 [-2.139,+0.239] | 0.9612 | 1.921 | 67.4% | 0.9714 |
| intermediate_treasury vs cheap | -0.372 [-1.457,+0.744] | 0.9834 | 1.956 | 67.4% | 0.9823 |
| short_tips_bills vs schp | +1.555 [-0.204,+3.514] | 1.0725 | 2.496 | 27.9% | 0.9864 |
| short_tips_bills vs cheap | +2.063 [-0.090,+4.455] | 1.0973 | 2.780 | 18.6% | 0.9841 |
| schp_bills vs schp | +0.873 [-0.209,+2.072] | 1.0401 | 1.566 | 34.9% | 0.9910 |
| schp_bills vs cheap | +1.381 [-0.116,+2.985] | 1.0641 | 1.891 | 23.3% | 0.9888 |
| cheap vs schp | -0.508 [-1.263,+0.203] | 0.9774 | 0.867 | 65.1% | 0.9811 |

## no_trend_diagnostic: 2021-10 to 2026-03, 25bp

RSST 15% becomes additional VTI 15% in every arm: a different portfolio.

| Arm | Nominal CAGR% | Nominal DD% all months | Real terminal wealth | Real CAGR% | Real DD% observed CPI | Max real-principal shortfall% observed CPI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| schp | 5.598 | -18.716 | 1.0614 | 1.334 | -23.647 | 21.555 |
| short_tips | 7.076 | -14.065 | 1.1300 | 2.753 | -19.278 | 17.515 |
| bills | 7.424 | -11.888 | 1.1466 | 3.086 | -17.234 | 15.898 |
| intermediate_treasury | 4.672 | -19.822 | 1.0202 | 0.446 | -24.686 | 23.396 |
| short_tips_bills | 7.251 | -12.980 | 1.1383 | 2.921 | -18.259 | 16.707 |
| schp_bills | 6.523 | -15.321 | 1.1039 | 2.222 | -20.458 | 18.727 |
| cheap | 5.063 | -19.662 | 1.0375 | 0.820 | -24.536 | 22.512 |

| Comparison | Log gap pp/yr[95%] | Wealth ratio | TE pp/yr | Losing rolling 12m | Worst rolling 12m ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| schp vs cheap | +0.508 [-0.203,+1.263] | 1.0231 | 0.867 | 34.9% | 0.9906 |
| short_tips vs schp | +1.390 [-0.039,+2.996] | 1.0646 | 1.932 | 16.3% | 0.9907 |
| short_tips vs cheap | +1.898 [+0.052,+3.987] | 1.0892 | 2.291 | 9.3% | 0.9885 |
| bills vs schp | +1.715 [-0.425,+4.075] | 1.0802 | 3.108 | 34.9% | 0.9821 |
| bills vs cheap | +2.222 [-0.262,+4.937] | 1.1052 | 3.338 | 30.2% | 0.9798 |
| intermediate_treasury vs schp | -0.880 [-2.140,+0.239] | 0.9612 | 1.921 | 67.4% | 0.9714 |
| intermediate_treasury vs cheap | -0.372 [-1.459,+0.743] | 0.9834 | 1.956 | 67.4% | 0.9823 |
| short_tips_bills vs schp | +1.554 [-0.204,+3.513] | 1.0724 | 2.496 | 27.9% | 0.9864 |
| short_tips_bills vs cheap | +2.062 [-0.091,+4.454] | 1.0972 | 2.780 | 18.6% | 0.9841 |
| schp_bills vs schp | +0.873 [-0.209,+2.070] | 1.0400 | 1.566 | 34.9% | 0.9910 |
| schp_bills vs cheap | +1.380 [-0.116,+2.985] | 1.0641 | 1.891 | 23.3% | 0.9888 |
| cheap vs schp | -0.508 [-1.263,+0.203] | 0.9774 | 0.867 | 65.1% | 0.9811 |
