# Trend wrapper and funding portfolio comparisons

All comparisons are exploratory.

## with-trend: 2023-10 to 2026-03 (30 months)

| Arm | Intended stock % | SCHP % | SGOV % | Standalone trend % | Stacked trend % |
| --- | ---: | ---: | ---: | ---: | ---: |
| unchanged | 95.0 | 5.0 | 0.0 | 0.0 | 25.0 |
| no_trend | 95.0 | 5.0 | 0.0 | 0.0 | 0.0 |
| direct_dbmf | 70.0 | 5.0 | 0.0 | 25.0 | 0.0 |
| direct_kmlm | 70.0 | 5.0 | 0.0 | 25.0 | 0.0 |
| direct_mix | 70.0 | 5.0 | 0.0 | 25.0 | 0.0 |
| bond_dbmf | 95.0 | 0.0 | 0.0 | 5.0 | 0.0 |
| bond_kmlm | 95.0 | 0.0 | 0.0 | 5.0 | 0.0 |
| bond_mix | 95.0 | 0.0 | 0.0 | 5.0 | 0.0 |
| bond_cash | 95.0 | 0.0 | 5.0 | 0.0 | 0.0 |
| cheap | 95.0 | 5.0 | 0.0 | 0.0 | 0.0 |

Stock includes RSST's intended stock capital. Stacked trend overlaps that capital; other columns are funded allocations, not matched risk.

### 5 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +17.515 | +19.143 | +18.281 | -7.030 |
| no_trend | +18.063 | +19.798 | +18.772 | -6.379 |
| direct_dbmf | +15.752 | +17.060 | +16.256 | -6.008 |
| direct_kmlm | +13.358 | +14.292 | +13.790 | -5.199 |
| direct_mix | +14.561 | +15.675 | +15.020 | -5.608 |
| bond_dbmf | +18.212 | +19.976 | +18.921 | -6.468 |
| bond_kmlm | +17.751 | +19.424 | +18.445 | -6.306 |
| bond_mix | +17.982 | +19.700 | +18.683 | -6.387 |
| bond_cash | +18.037 | +19.766 | +18.732 | -6.304 |
| cheap | +17.245 | +18.821 | +17.958 | -6.106 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| unchanged vs cheap | +0.270 [-3.515, +4.656] | 1.0068 | 3.400 | 68.4% | 0.9528 |
| no_trend vs unchanged | +0.548 [-2.907, +3.590] | 1.0138 | 2.719 | 31.6% | 0.9747 |
| no_trend vs cheap | +0.818 [-0.639, +2.471] | 1.0207 | 1.651 | 31.6% | 0.9913 |
| direct_dbmf vs unchanged | -1.763 [-4.546, +0.795] | 0.9569 | 3.255 | 100.0% | 0.9535 |
| direct_dbmf vs cheap | -1.493 [-6.730, +4.061] | 0.9634 | 4.949 | 73.7% | 0.9176 |
| direct_dbmf vs no_trend | -2.311 [-6.323, +1.801] | 0.9439 | 3.958 | 84.2% | 0.9234 |
| direct_kmlm vs unchanged | -4.157 [-8.392, -0.587] | 0.9013 | 4.371 | 89.5% | 0.9291 |
| direct_kmlm vs cheap | -3.887 [-8.363, +0.347] | 0.9074 | 4.740 | 94.7% | 0.9078 |
| direct_kmlm vs no_trend | -4.705 [-8.093, -1.745] | 0.8890 | 3.819 | 100.0% | 0.9129 |
| direct_mix vs unchanged | -2.954 [-6.351, -0.253] | 0.9288 | 3.616 | 89.5% | 0.9413 |
| direct_mix vs cheap | -2.684 [-7.261, +2.273] | 0.9351 | 4.662 | 84.2% | 0.9197 |
| direct_mix vs no_trend | -3.502 [-6.853, -0.011] | 0.9162 | 3.657 | 94.7% | 0.9248 |
| bond_dbmf vs unchanged | +0.697 [-2.090, +3.117] | 1.0176 | 2.271 | 31.6% | 0.9847 |
| bond_dbmf vs cheap | +0.967 [-0.834, +3.010] | 1.0245 | 1.833 | 52.6% | 0.9895 |
| bond_dbmf vs no_trend | +0.149 [-0.522, +0.828] | 1.0037 | 0.576 | 57.9% | 0.9914 |
| bond_dbmf vs bond_cash | +0.175 [-0.470, +0.826] | 1.0044 | 0.523 | 57.9% | 0.9925 |
| bond_kmlm vs unchanged | +0.236 [-3.054, +3.093] | 1.0059 | 2.640 | 31.6% | 0.9755 |
| bond_kmlm vs cheap | +0.506 [-1.150, +2.233] | 1.0127 | 1.753 | 57.9% | 0.9868 |
| bond_kmlm vs no_trend | -0.312 [-0.774, +0.037] | 0.9922 | 0.492 | 89.5% | 0.9924 |
| bond_kmlm vs bond_cash | -0.286 [-0.698, +0.039] | 0.9929 | 0.436 | 89.5% | 0.9940 |
| bond_mix vs unchanged | +0.467 [-2.559, +3.096] | 1.0117 | 2.449 | 31.6% | 0.9801 |
| bond_mix vs cheap | +0.737 [-0.973, +2.660] | 1.0186 | 1.774 | 52.6% | 0.9892 |
| bond_mix vs no_trend | -0.081 [-0.607, +0.388] | 0.9980 | 0.467 | 73.7% | 0.9926 |
| bond_mix vs bond_cash | -0.055 [-0.528, +0.375] | 0.9986 | 0.404 | 78.9% | 0.9937 |
| bond_cash vs unchanged | +0.522 [-2.906, +3.566] | 1.0131 | 2.702 | 31.6% | 0.9743 |
| bond_cash vs cheap | +0.792 [-0.664, +2.455] | 1.0200 | 1.617 | 31.6% | 0.9925 |
| bond_cash vs no_trend | -0.026 [-0.163, +0.105] | 0.9993 | 0.202 | 73.7% | 0.9983 |

| Arm | Intended stock % | SCHP % | SGOV % | Standalone trend % | Stacked trend % |
| --- | ---: | ---: | ---: | ---: | ---: |
| unchanged | 95.0 | 5.0 | 0.0 | 0.0 | 25.0 |
| no_trend | 95.0 | 5.0 | 0.0 | 0.0 | 0.0 |
| direct_dbmf | 70.0 | 5.0 | 0.0 | 25.0 | 0.0 |
| direct_kmlm | 70.0 | 5.0 | 0.0 | 25.0 | 0.0 |
| direct_mix | 70.0 | 5.0 | 0.0 | 25.0 | 0.0 |
| bond_dbmf | 95.0 | 0.0 | 0.0 | 5.0 | 0.0 |
| bond_kmlm | 95.0 | 0.0 | 0.0 | 5.0 | 0.0 |
| bond_mix | 95.0 | 0.0 | 0.0 | 5.0 | 0.0 |
| bond_cash | 95.0 | 0.0 | 5.0 | 0.0 | 0.0 |
| cheap | 95.0 | 5.0 | 0.0 | 0.0 | 0.0 |

Stock includes RSST's intended stock capital. Stacked trend overlaps that capital; other columns are funded allocations, not matched risk.

### 25 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +17.472 | +19.091 | +18.239 | -7.030 |
| no_trend | +18.020 | +19.746 | +18.731 | -6.379 |
| direct_dbmf | +15.706 | +17.006 | +16.211 | -6.008 |
| direct_kmlm | +13.310 | +14.236 | +13.743 | -5.199 |
| direct_mix | +14.514 | +15.620 | +14.974 | -5.608 |
| bond_dbmf | +18.169 | +19.924 | +18.879 | -6.468 |
| bond_kmlm | +17.708 | +19.372 | +18.403 | -6.306 |
| bond_mix | +17.939 | +19.648 | +18.641 | -6.387 |
| bond_cash | +17.994 | +19.714 | +18.690 | -6.304 |
| cheap | +17.203 | +18.771 | +17.917 | -6.106 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| unchanged vs cheap | +0.269 [-3.517, +4.655] | 1.0067 | 3.399 | 68.4% | 0.9528 |
| no_trend vs unchanged | +0.549 [-2.905, +3.592] | 1.0138 | 2.719 | 31.6% | 0.9748 |
| no_trend vs cheap | +0.818 [-0.639, +2.471] | 1.0206 | 1.651 | 31.6% | 0.9913 |
| direct_dbmf vs unchanged | -1.766 [-4.548, +0.795] | 0.9568 | 3.254 | 100.0% | 0.9535 |
| direct_dbmf vs cheap | -1.497 [-6.733, +4.059] | 0.9633 | 4.949 | 73.7% | 0.9176 |
| direct_dbmf vs no_trend | -2.315 [-6.329, +1.799] | 0.9438 | 3.958 | 84.2% | 0.9234 |
| direct_kmlm vs unchanged | -4.162 [-8.395, -0.588] | 0.9012 | 4.369 | 89.5% | 0.9291 |
| direct_kmlm vs cheap | -3.893 [-8.367, +0.345] | 0.9073 | 4.739 | 94.7% | 0.9078 |
| direct_kmlm vs no_trend | -4.711 [-8.101, -1.745] | 0.8889 | 3.817 | 100.0% | 0.9129 |
| direct_mix vs unchanged | -2.958 [-6.358, -0.255] | 0.9287 | 3.614 | 89.5% | 0.9413 |
| direct_mix vs cheap | -2.689 [-7.263, +2.270] | 0.9350 | 4.662 | 84.2% | 0.9197 |
| direct_mix vs no_trend | -3.507 [-6.856, -0.013] | 0.9161 | 3.656 | 94.7% | 0.9248 |
| bond_dbmf vs unchanged | +0.697 [-2.088, +3.118] | 1.0176 | 2.271 | 31.6% | 0.9847 |
| bond_dbmf vs cheap | +0.966 [-0.833, +3.008] | 1.0245 | 1.833 | 52.6% | 0.9896 |
| bond_dbmf vs no_trend | +0.149 [-0.522, +0.828] | 1.0037 | 0.576 | 57.9% | 0.9914 |
| bond_dbmf vs bond_cash | +0.175 [-0.470, +0.826] | 1.0044 | 0.523 | 57.9% | 0.9925 |
| bond_kmlm vs unchanged | +0.236 [-3.053, +3.091] | 1.0059 | 2.639 | 31.6% | 0.9755 |
| bond_kmlm vs cheap | +0.505 [-1.151, +2.232] | 1.0127 | 1.753 | 57.9% | 0.9868 |
| bond_kmlm vs no_trend | -0.313 [-0.775, +0.037] | 0.9922 | 0.492 | 89.5% | 0.9924 |
| bond_kmlm vs bond_cash | -0.286 [-0.698, +0.039] | 0.9929 | 0.436 | 89.5% | 0.9940 |
| bond_mix vs unchanged | +0.467 [-2.557, +3.098] | 1.0117 | 2.448 | 31.6% | 0.9801 |
| bond_mix vs cheap | +0.736 [-0.973, +2.656] | 1.0186 | 1.775 | 52.6% | 0.9892 |
| bond_mix vs no_trend | -0.082 [-0.607, +0.389] | 0.9980 | 0.467 | 73.7% | 0.9926 |
| bond_mix vs bond_cash | -0.055 [-0.529, +0.375] | 0.9986 | 0.404 | 78.9% | 0.9937 |
| bond_cash vs unchanged | +0.522 [-2.904, +3.569] | 1.0131 | 2.702 | 31.6% | 0.9743 |
| bond_cash vs cheap | +0.791 [-0.664, +2.453] | 1.0200 | 1.618 | 31.6% | 0.9926 |
| bond_cash vs no_trend | -0.027 [-0.163, +0.105] | 0.9993 | 0.202 | 73.7% | 0.9983 |

## cautious: 2023-10 to 2026-03 (30 months)

| Arm | Intended stock % | SCHP % | SGOV % | Standalone trend % | Stacked trend % |
| --- | ---: | ---: | ---: | ---: | ---: |
| unchanged | 50.0 | 50.0 | 0.0 | 0.0 | 15.0 |
| no_trend | 50.0 | 50.0 | 0.0 | 0.0 | 0.0 |
| direct_dbmf | 35.0 | 50.0 | 0.0 | 15.0 | 0.0 |
| direct_kmlm | 35.0 | 50.0 | 0.0 | 15.0 | 0.0 |
| direct_mix | 35.0 | 50.0 | 0.0 | 15.0 | 0.0 |
| bond_dbmf | 50.0 | 35.0 | 0.0 | 15.0 | 0.0 |
| bond_kmlm | 50.0 | 35.0 | 0.0 | 15.0 | 0.0 |
| bond_mix | 50.0 | 35.0 | 0.0 | 15.0 | 0.0 |
| bond_cash | 50.0 | 35.0 | 15.0 | 0.0 | 0.0 |
| cheap | 50.0 | 50.0 | 0.0 | 0.0 | 0.0 |

Stock includes RSST's intended stock capital. Stacked trend overlaps that capital; other columns are funded allocations, not matched risk.

### 5 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +11.868 | +12.601 | +12.200 | -4.501 |
| no_trend | +12.244 | +13.025 | +12.561 | -4.047 |
| direct_dbmf | +10.735 | +11.333 | +10.965 | -3.865 |
| direct_kmlm | +9.241 | +9.681 | +9.444 | -3.327 |
| direct_mix | +9.990 | +10.506 | +10.203 | -3.598 |
| bond_dbmf | +12.664 | +13.500 | +12.979 | -4.376 |
| bond_kmlm | +11.198 | +11.849 | +11.483 | -3.846 |
| bond_mix | +11.933 | +12.674 | +12.230 | -4.113 |
| bond_cash | +12.151 | +12.920 | +12.436 | -3.812 |
| cheap | +11.829 | +12.558 | +12.143 | -3.916 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| unchanged vs cheap | +0.039 [-2.245, +2.735] | 1.0010 | 1.941 | 68.4% | 0.9704 |
| no_trend vs unchanged | +0.375 [-1.908, +2.316] | 1.0094 | 1.655 | 31.6% | 0.9846 |
| no_trend vs cheap | +0.414 [-0.286, +1.222] | 1.0104 | 0.786 | 26.3% | 0.9966 |
| direct_dbmf vs unchanged | -1.133 [-2.921, +0.507] | 0.9721 | 1.974 | 100.0% | 0.9701 |
| direct_dbmf vs cheap | -1.094 [-4.215, +2.188] | 0.9730 | 2.858 | 73.7% | 0.9487 |
| direct_dbmf vs no_trend | -1.509 [-4.094, +1.101] | 0.9630 | 2.419 | 84.2% | 0.9509 |
| direct_kmlm vs unchanged | -2.628 [-5.163, -0.393] | 0.9364 | 2.667 | 89.5% | 0.9545 |
| direct_kmlm vs cheap | -2.589 [-5.228, -0.031] | 0.9373 | 2.732 | 94.7% | 0.9415 |
| direct_kmlm vs no_trend | -3.003 [-5.196, -1.112] | 0.9277 | 2.329 | 100.0% | 0.9436 |
| direct_mix vs unchanged | -1.878 [-3.910, -0.110] | 0.9541 | 2.199 | 89.5% | 0.9623 |
| direct_mix vs cheap | -1.839 [-4.625, +1.069] | 0.9551 | 2.675 | 84.2% | 0.9492 |
| direct_mix vs no_trend | -2.253 [-4.495, -0.049] | 0.9452 | 2.231 | 94.7% | 0.9514 |
| bond_dbmf vs unchanged | +0.795 [-0.181, +1.424] | 1.0201 | 1.023 | 0.0% | 1.0001 |
| bond_dbmf vs cheap | +0.834 [-1.731, +3.510] | 1.0211 | 2.056 | 52.6% | 0.9738 |
| bond_dbmf vs no_trend | +0.420 [-1.798, +2.539] | 1.0106 | 1.770 | 57.9% | 0.9734 |
| bond_dbmf vs bond_cash | +0.512 [-1.565, +2.509] | 1.0129 | 1.613 | 57.9% | 0.9772 |
| bond_kmlm vs unchanged | -0.670 [-2.620, +0.860] | 0.9834 | 1.942 | 57.9% | 0.9778 |
| bond_kmlm vs cheap | -0.631 [-2.323, +1.015] | 0.9843 | 1.751 | 84.2% | 0.9732 |
| bond_kmlm vs no_trend | -1.046 [-2.442, +0.051] | 0.9742 | 1.501 | 89.5% | 0.9754 |
| bond_kmlm vs bond_cash | -0.953 [-2.193, +0.009] | 0.9765 | 1.334 | 89.5% | 0.9807 |
| bond_mix vs unchanged | +0.065 [-1.210, +0.966] | 1.0016 | 1.324 | 36.8% | 0.9902 |
| bond_mix vs cheap | +0.104 [-1.871, +2.213] | 1.0026 | 1.731 | 73.7% | 0.9773 |
| bond_mix vs no_trend | -0.311 [-1.966, +1.255] | 0.9923 | 1.429 | 78.9% | 0.9770 |
| bond_mix vs bond_cash | -0.218 [-1.698, +1.202] | 0.9946 | 1.241 | 78.9% | 0.9807 |
| bond_cash vs unchanged | +0.283 [-1.953, +2.143] | 1.0071 | 1.696 | 31.6% | 0.9832 |
| bond_cash vs cheap | +0.322 [-0.468, +1.206] | 1.0081 | 0.884 | 31.6% | 0.9923 |
| bond_cash vs no_trend | -0.092 [-0.509, +0.335] | 0.9977 | 0.614 | 73.7% | 0.9946 |

| Arm | Intended stock % | SCHP % | SGOV % | Standalone trend % | Stacked trend % |
| --- | ---: | ---: | ---: | ---: | ---: |
| unchanged | 50.0 | 50.0 | 0.0 | 0.0 | 15.0 |
| no_trend | 50.0 | 50.0 | 0.0 | 0.0 | 0.0 |
| direct_dbmf | 35.0 | 50.0 | 0.0 | 15.0 | 0.0 |
| direct_kmlm | 35.0 | 50.0 | 0.0 | 15.0 | 0.0 |
| direct_mix | 35.0 | 50.0 | 0.0 | 15.0 | 0.0 |
| bond_dbmf | 50.0 | 35.0 | 0.0 | 15.0 | 0.0 |
| bond_kmlm | 50.0 | 35.0 | 0.0 | 15.0 | 0.0 |
| bond_mix | 50.0 | 35.0 | 0.0 | 15.0 | 0.0 |
| bond_cash | 50.0 | 35.0 | 15.0 | 0.0 | 0.0 |
| cheap | 50.0 | 50.0 | 0.0 | 0.0 | 0.0 |

Stock includes RSST's intended stock capital. Stacked trend overlaps that capital; other columns are funded allocations, not matched risk.

### 25 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +11.823 | +12.550 | +12.156 | -4.501 |
| no_trend | +12.198 | +12.973 | +12.516 | -4.047 |
| direct_dbmf | +10.689 | +11.282 | +10.920 | -3.865 |
| direct_kmlm | +9.194 | +9.630 | +9.398 | -3.327 |
| direct_mix | +9.944 | +10.455 | +10.158 | -3.598 |
| bond_dbmf | +12.617 | +13.447 | +12.933 | -4.376 |
| bond_kmlm | +11.150 | +11.796 | +11.437 | -3.846 |
| bond_mix | +11.886 | +12.621 | +12.184 | -4.113 |
| bond_cash | +12.105 | +12.868 | +12.390 | -3.812 |
| cheap | +11.783 | +12.506 | +12.098 | -3.916 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| unchanged vs cheap | +0.040 [-2.246, +2.731] | 1.0010 | 1.941 | 68.4% | 0.9705 |
| no_trend vs unchanged | +0.374 [-1.906, +2.315] | 1.0094 | 1.654 | 31.6% | 0.9846 |
| no_trend vs cheap | +0.414 [-0.285, +1.221] | 1.0104 | 0.786 | 26.3% | 0.9966 |
| direct_dbmf vs unchanged | -1.134 [-2.922, +0.507] | 0.9721 | 1.974 | 100.0% | 0.9701 |
| direct_dbmf vs cheap | -1.094 [-4.215, +2.187] | 0.9730 | 2.858 | 73.7% | 0.9487 |
| direct_dbmf vs no_trend | -1.508 [-4.094, +1.100] | 0.9630 | 2.419 | 84.2% | 0.9510 |
| direct_kmlm vs unchanged | -2.629 [-5.163, -0.393] | 0.9364 | 2.666 | 89.5% | 0.9545 |
| direct_kmlm vs cheap | -2.590 [-5.228, -0.031] | 0.9373 | 2.732 | 94.7% | 0.9415 |
| direct_kmlm vs no_trend | -3.004 [-5.196, -1.113] | 0.9277 | 2.329 | 100.0% | 0.9436 |
| direct_mix vs unchanged | -1.879 [-3.909, -0.108] | 0.9541 | 2.199 | 89.5% | 0.9623 |
| direct_mix vs cheap | -1.839 [-4.623, +1.069] | 0.9551 | 2.675 | 84.2% | 0.9492 |
| direct_mix vs no_trend | -2.253 [-4.494, -0.050] | 0.9452 | 2.231 | 94.7% | 0.9514 |
| bond_dbmf vs unchanged | +0.794 [-0.182, +1.424] | 1.0200 | 1.022 | 0.0% | 1.0001 |
| bond_dbmf vs cheap | +0.833 [-1.732, +3.507] | 1.0211 | 2.056 | 52.6% | 0.9737 |
| bond_dbmf vs no_trend | +0.419 [-1.800, +2.538] | 1.0105 | 1.770 | 57.9% | 0.9734 |
| bond_dbmf vs bond_cash | +0.512 [-1.566, +2.510] | 1.0129 | 1.613 | 57.9% | 0.9772 |
| bond_kmlm vs unchanged | -0.673 [-2.620, +0.858] | 0.9833 | 1.940 | 57.9% | 0.9778 |
| bond_kmlm vs cheap | -0.633 [-2.324, +1.014] | 0.9843 | 1.750 | 84.2% | 0.9732 |
| bond_kmlm vs no_trend | -1.047 [-2.444, +0.051] | 0.9742 | 1.500 | 89.5% | 0.9754 |
| bond_kmlm vs bond_cash | -0.955 [-2.195, +0.008] | 0.9764 | 1.334 | 89.5% | 0.9807 |
| bond_mix vs unchanged | +0.063 [-1.211, +0.966] | 1.0016 | 1.323 | 36.8% | 0.9902 |
| bond_mix vs cheap | +0.103 [-1.872, +2.211] | 1.0026 | 1.731 | 73.7% | 0.9773 |
| bond_mix vs no_trend | -0.312 [-1.968, +1.255] | 0.9922 | 1.429 | 78.9% | 0.9770 |
| bond_mix vs bond_cash | -0.219 [-1.699, +1.201] | 0.9945 | 1.241 | 78.9% | 0.9807 |
| bond_cash vs unchanged | +0.282 [-1.951, +2.142] | 1.0071 | 1.696 | 31.6% | 0.9832 |
| bond_cash vs cheap | +0.322 [-0.468, +1.205] | 1.0081 | 0.884 | 31.6% | 0.9923 |
| bond_cash vs no_trend | -0.093 [-0.510, +0.335] | 0.9977 | 0.614 | 73.7% | 0.9946 |
