# Momentum implementation portfolio comparisons

All comparisons are exploratory.

## value-lean: 2021-10 to 2026-03 (54 months)

### 5 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +9.971 | +10.485 | +11.084 | -23.647 |
| spmo | +10.274 | +10.820 | +11.388 | -23.464 |
| mtum | +9.917 | +10.426 | +11.029 | -23.752 |
| equal_mix | +10.096 | +10.623 | +11.208 | -23.608 |
| cheap | +8.933 | +9.345 | +10.095 | -25.506 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| unchanged vs cheap | +1.037 [-0.443, +2.591] | 1.0478 | 1.692 | 32.6% | 0.9819 |
| spmo vs unchanged | +0.303 [-0.139, +0.758] | 1.0137 | 0.457 | 18.6% | 0.9961 |
| spmo vs cheap | +1.341 [-0.266, +2.793] | 1.0622 | 1.812 | 23.3% | 0.9785 |
| mtum vs unchanged | -0.053 [-0.419, +0.344] | 0.9976 | 0.451 | 37.2% | 0.9931 |
| mtum vs cheap | +0.984 [-0.602, +2.456] | 1.0453 | 1.793 | 34.9% | 0.9751 |
| mtum vs spmo | -0.356 [-0.556, -0.160] | 0.9841 | 0.259 | 97.7% | 0.9920 |
| equal_mix vs unchanged | +0.125 [-0.265, +0.536] | 1.0057 | 0.435 | 27.9% | 0.9949 |
| equal_mix vs cheap | +1.163 [-0.424, +2.600] | 1.0537 | 1.797 | 27.9% | 0.9768 |
| equal_mix vs spmo | -0.178 [-0.278, -0.080] | 0.9920 | 0.129 | 97.7% | 0.9960 |
| equal_mix vs mtum | +0.178 [+0.080, +0.278] | 1.0081 | 0.130 | 2.3% | 0.9999 |

### 25 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +9.946 | +10.457 | +11.058 | -23.647 |
| spmo | +10.248 | +10.792 | +11.361 | -23.464 |
| mtum | +9.892 | +10.398 | +11.002 | -23.752 |
| equal_mix | +10.070 | +10.595 | +11.182 | -23.608 |
| cheap | +8.909 | +9.318 | +10.070 | -25.506 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| unchanged vs cheap | +1.036 [-0.444, +2.589] | 1.0477 | 1.693 | 32.6% | 0.9818 |
| spmo vs unchanged | +0.303 [-0.139, +0.758] | 1.0137 | 0.457 | 18.6% | 0.9961 |
| spmo vs cheap | +1.339 [-0.267, +2.791] | 1.0621 | 1.812 | 23.3% | 0.9785 |
| mtum vs unchanged | -0.054 [-0.419, +0.344] | 0.9976 | 0.451 | 37.2% | 0.9931 |
| mtum vs cheap | +0.982 [-0.603, +2.455] | 1.0452 | 1.793 | 34.9% | 0.9751 |
| mtum vs spmo | -0.356 [-0.556, -0.160] | 0.9841 | 0.259 | 97.7% | 0.9919 |
| equal_mix vs unchanged | +0.125 [-0.265, +0.535] | 1.0056 | 0.435 | 27.9% | 0.9948 |
| equal_mix vs cheap | +1.161 [-0.425, +2.599] | 1.0536 | 1.798 | 27.9% | 0.9768 |
| equal_mix vs spmo | -0.178 [-0.277, -0.080] | 0.9920 | 0.129 | 97.7% | 0.9960 |
| equal_mix vs mtum | +0.178 [+0.080, +0.278] | 1.0081 | 0.130 | 2.3% | 0.9999 |

## with-trend: 2023-10 to 2026-03 (30 months)

### 5 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +17.515 | +19.143 | +18.281 | -7.030 |
| spmo | +18.086 | +19.825 | +18.870 | -7.072 |
| mtum | +17.784 | +19.463 | +18.560 | -7.034 |
| equal_mix | +17.935 | +19.644 | +18.715 | -7.053 |
| cheap | +17.245 | +18.821 | +17.958 | -6.106 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| unchanged vs cheap | +0.270 [-3.724, +4.692] | 1.0068 | 3.400 | 68.4% | 0.9528 |
| spmo vs unchanged | +0.571 [+0.045, +1.050] | 1.0144 | 0.430 | 0.0% | 1.0021 |
| spmo vs cheap | +0.841 [-3.109, +4.939] | 1.0213 | 3.329 | 68.4% | 0.9593 |
| mtum vs unchanged | +0.269 [-0.118, +0.632] | 1.0067 | 0.401 | 0.0% | 1.0004 |
| mtum vs cheap | +0.539 [-3.412, +4.841] | 1.0136 | 3.367 | 68.4% | 0.9565 |
| mtum vs spmo | -0.303 [-0.558, -0.038] | 0.9925 | 0.251 | 100.0% | 0.9945 |
| equal_mix vs unchanged | +0.420 [-0.031, +0.819] | 1.0106 | 0.396 | 0.0% | 1.0012 |
| equal_mix vs cheap | +0.690 [-3.272, +4.890] | 1.0174 | 3.346 | 68.4% | 0.9579 |
| equal_mix vs spmo | -0.151 [-0.279, -0.019] | 0.9962 | 0.125 | 100.0% | 0.9973 |
| equal_mix vs mtum | +0.151 [+0.019, +0.279] | 1.0038 | 0.125 | 0.0% | 1.0006 |

### 25 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +17.472 | +19.091 | +18.239 | -7.030 |
| spmo | +18.042 | +19.772 | +18.827 | -7.072 |
| mtum | +17.740 | +19.411 | +18.517 | -7.034 |
| equal_mix | +17.891 | +19.592 | +18.672 | -7.053 |
| cheap | +17.203 | +18.771 | +17.917 | -6.106 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| unchanged vs cheap | +0.269 [-3.729, +4.691] | 1.0067 | 3.399 | 68.4% | 0.9528 |
| spmo vs unchanged | +0.571 [+0.044, +1.048] | 1.0144 | 0.430 | 0.0% | 1.0021 |
| spmo vs cheap | +0.839 [-3.112, +4.936] | 1.0212 | 3.329 | 68.4% | 0.9593 |
| mtum vs unchanged | +0.268 [-0.118, +0.631] | 1.0067 | 0.401 | 0.0% | 1.0003 |
| mtum vs cheap | +0.537 [-3.412, +4.838] | 1.0135 | 3.366 | 68.4% | 0.9565 |
| mtum vs spmo | -0.302 [-0.558, -0.038] | 0.9925 | 0.251 | 100.0% | 0.9945 |
| equal_mix vs unchanged | +0.420 [-0.031, +0.819] | 1.0105 | 0.396 | 0.0% | 1.0012 |
| equal_mix vs cheap | +0.689 [-3.277, +4.890] | 1.0174 | 3.345 | 68.4% | 0.9579 |
| equal_mix vs spmo | -0.151 [-0.279, -0.019] | 0.9962 | 0.125 | 100.0% | 0.9973 |
| equal_mix vs mtum | +0.151 [+0.019, +0.279] | 1.0038 | 0.125 | 0.0% | 1.0006 |

## cautious: 2023-10 to 2026-03 (30 months)

### 5 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +11.868 | +12.601 | +12.200 | -4.501 |
| spmo | +12.174 | +12.947 | +12.512 | -4.520 |
| mtum | +12.013 | +12.764 | +12.348 | -4.500 |
| equal_mix | +12.094 | +12.855 | +12.430 | -4.510 |
| cheap | +11.829 | +12.558 | +12.143 | -3.916 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| unchanged vs cheap | +0.039 [-2.142, +2.851] | 1.0010 | 1.941 | 68.4% | 0.9704 |
| spmo vs unchanged | +0.306 [+0.031, +0.550] | 1.0077 | 0.224 | 0.0% | 1.0012 |
| spmo vs cheap | +0.345 [-1.766, +2.994] | 1.0087 | 1.914 | 68.4% | 0.9739 |
| mtum vs unchanged | +0.144 [-0.057, +0.342] | 1.0036 | 0.205 | 0.0% | 1.0002 |
| mtum vs cheap | +0.183 [-1.917, +2.881] | 1.0046 | 1.928 | 68.4% | 0.9724 |
| mtum vs spmo | -0.162 [-0.300, -0.015] | 0.9960 | 0.129 | 100.0% | 0.9971 |
| equal_mix vs unchanged | +0.225 [-0.011, +0.437] | 1.0056 | 0.205 | 0.0% | 1.0007 |
| equal_mix vs cheap | +0.264 [-1.843, +2.943] | 1.0066 | 1.920 | 68.4% | 0.9731 |
| equal_mix vs spmo | -0.081 [-0.150, -0.007] | 0.9980 | 0.064 | 100.0% | 0.9985 |
| equal_mix vs mtum | +0.081 [+0.007, +0.150] | 1.0020 | 0.064 | 0.0% | 1.0004 |

### 25 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +11.823 | +12.550 | +12.156 | -4.501 |
| spmo | +12.129 | +12.895 | +12.467 | -4.520 |
| mtum | +11.967 | +12.713 | +12.303 | -4.500 |
| equal_mix | +12.048 | +12.804 | +12.385 | -4.510 |
| cheap | +11.783 | +12.506 | +12.098 | -3.916 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| unchanged vs cheap | +0.040 [-2.143, +2.849] | 1.0010 | 1.941 | 68.4% | 0.9705 |
| spmo vs unchanged | +0.306 [+0.031, +0.550] | 1.0077 | 0.224 | 0.0% | 1.0012 |
| spmo vs cheap | +0.345 [-1.766, +2.991] | 1.0087 | 1.914 | 68.4% | 0.9739 |
| mtum vs unchanged | +0.144 [-0.057, +0.341] | 1.0036 | 0.205 | 0.0% | 1.0002 |
| mtum vs cheap | +0.184 [-1.916, +2.878] | 1.0046 | 1.928 | 68.4% | 0.9724 |
| mtum vs spmo | -0.162 [-0.300, -0.015] | 0.9960 | 0.129 | 100.0% | 0.9971 |
| equal_mix vs unchanged | +0.225 [-0.011, +0.436] | 1.0056 | 0.205 | 0.0% | 1.0007 |
| equal_mix vs cheap | +0.265 [-1.843, +2.940] | 1.0066 | 1.920 | 68.4% | 0.9731 |
| equal_mix vs spmo | -0.081 [-0.150, -0.007] | 0.9980 | 0.064 | 100.0% | 0.9985 |
| equal_mix vs mtum | +0.081 [+0.007, +0.150] | 1.0020 | 0.064 | 0.0% | 1.0004 |
