# Funded crash hedge comparisons

All comparisons are exploratory. Monthly NAV execution; no investor taxes.

Only complete episodes have returns in result.json; partial episodes are flagged.

## tail_long: 2020-02 to 2026-03 (74 months)

### 12-month resets, 5 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +11.274 | +11.935 | +12.738 | -25.584 |
| TAIL | +10.499 | +11.070 | +11.753 | -24.639 |
| bills | +10.884 | +11.499 | +12.199 | -24.363 |
| duration | +10.745 | +11.343 | +12.078 | -25.047 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| TAIL vs unchanged | -0.776 [-1.388, +0.149] | 0.9533 | 1.349 | 88.9% | 0.9619 |
| TAIL vs bills | -0.386 [-0.668, +0.060] | 0.9765 | 0.595 | 85.7% | 0.9853 |
| TAIL vs duration | -0.246 [-0.450, +0.110] | 0.9850 | 0.574 | 82.5% | 0.9890 |

### 12-month resets, 25 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +11.254 | +11.911 | +12.718 | -25.588 |
| TAIL | +10.477 | +11.046 | +11.733 | -24.643 |
| bills | +10.863 | +11.475 | +12.179 | -24.367 |
| duration | +10.723 | +11.319 | +12.058 | -25.051 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| TAIL vs unchanged | -0.776 [-1.389, +0.148] | 0.9532 | 1.349 | 88.9% | 0.9619 |
| TAIL vs bills | -0.386 [-0.669, +0.059] | 0.9765 | 0.595 | 85.7% | 0.9853 |
| TAIL vs duration | -0.246 [-0.451, +0.109] | 0.9849 | 0.574 | 82.5% | 0.9890 |

### 3-month resets, 5 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +11.263 | +11.921 | +12.725 | -25.533 |
| TAIL | +10.531 | +11.105 | +11.787 | -24.578 |
| bills | +10.894 | +11.509 | +12.211 | -24.350 |
| duration | +10.754 | +11.354 | +12.088 | -24.992 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| TAIL vs unchanged | -0.732 [-1.511, +0.209] | 0.9559 | 1.333 | 90.5% | 0.9647 |
| TAIL vs bills | -0.363 [-0.748, +0.106] | 0.9779 | 0.594 | 81.0% | 0.9866 |
| TAIL vs duration | -0.223 [-0.523, +0.135] | 0.9863 | 0.565 | 71.4% | 0.9898 |

### 3-month resets, 25 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +11.239 | +11.895 | +12.703 | -25.534 |
| TAIL | +10.506 | +11.077 | +11.763 | -24.580 |
| bills | +10.869 | +11.482 | +12.187 | -24.352 |
| duration | +10.730 | +11.326 | +12.064 | -24.994 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| TAIL vs unchanged | -0.734 [-1.513, +0.206] | 0.9558 | 1.333 | 90.5% | 0.9646 |
| TAIL vs bills | -0.363 [-0.748, +0.104] | 0.9778 | 0.594 | 81.0% | 0.9866 |
| TAIL vs duration | -0.224 [-0.524, +0.134] | 0.9863 | 0.565 | 71.4% | 0.9898 |

## current_etfs: 2023-04 to 2026-03 (36 months)

### 12-month resets, 5 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +15.752 | +17.060 | +16.521 | -9.667 |
| TAIL | +14.891 | +16.057 | +15.582 | -9.294 |
| CAOS | +15.262 | +16.488 | +15.967 | -9.197 |
| bills | +15.232 | +16.453 | +15.933 | -9.158 |
| duration | +15.143 | +16.350 | +15.862 | -9.457 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| TAIL vs unchanged | -0.861 [-1.366, -0.255] | 0.9745 | 0.730 | 100.0% | 0.9850 |
| TAIL vs bills | -0.341 [-0.661, +0.030] | 0.9898 | 0.390 | 72.0% | 0.9917 |
| TAIL vs duration | -0.252 [-0.484, +0.055] | 0.9925 | 0.349 | 88.0% | 0.9944 |
| CAOS vs unchanged | -0.490 [-0.896, -0.045] | 0.9854 | 0.524 | 100.0% | 0.9894 |
| CAOS vs bills | +0.030 [-0.045, +0.128] | 1.0009 | 0.095 | 72.0% | 0.9993 |
| CAOS vs duration | +0.119 [-0.115, +0.425] | 1.0036 | 0.286 | 60.0% | 0.9977 |

### 12-month resets, 25 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +15.717 | +17.019 | +16.485 | -9.667 |
| TAIL | +14.855 | +16.015 | +15.546 | -9.294 |
| CAOS | +15.226 | +16.447 | +15.932 | -9.197 |
| bills | +15.196 | +16.412 | +15.897 | -9.158 |
| duration | +15.107 | +16.308 | +15.826 | -9.457 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| TAIL vs unchanged | -0.862 [-1.368, -0.255] | 0.9745 | 0.730 | 100.0% | 0.9850 |
| TAIL vs bills | -0.342 [-0.661, +0.030] | 0.9898 | 0.390 | 72.0% | 0.9917 |
| TAIL vs duration | -0.252 [-0.485, +0.055] | 0.9925 | 0.349 | 88.0% | 0.9944 |
| CAOS vs unchanged | -0.490 [-0.896, -0.045] | 0.9854 | 0.524 | 100.0% | 0.9894 |
| CAOS vs bills | +0.030 [-0.045, +0.128] | 1.0009 | 0.095 | 72.0% | 0.9993 |
| CAOS vs duration | +0.119 [-0.115, +0.425] | 1.0036 | 0.286 | 60.0% | 0.9977 |

### 3-month resets, 5 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +15.783 | +17.096 | +16.548 | -9.690 |
| TAIL | +14.866 | +16.028 | +15.546 | -9.267 |
| CAOS | +15.284 | +16.513 | +15.983 | -9.218 |
| bills | +15.252 | +16.476 | +15.946 | -9.163 |
| duration | +15.144 | +16.351 | +15.856 | -9.465 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| TAIL vs unchanged | -0.917 [-1.497, -0.247] | 0.9729 | 0.787 | 100.0% | 0.9836 |
| TAIL vs bills | -0.386 [-0.754, +0.065] | 0.9885 | 0.413 | 72.0% | 0.9903 |
| TAIL vs duration | -0.278 [-0.565, +0.081] | 0.9917 | 0.378 | 84.0% | 0.9932 |
| CAOS vs unchanged | -0.499 [-0.953, -0.038] | 0.9851 | 0.542 | 100.0% | 0.9894 |
| CAOS vs bills | +0.032 [-0.049, +0.133] | 1.0010 | 0.099 | 64.0% | 0.9992 |
| CAOS vs duration | +0.140 [-0.130, +0.452] | 1.0042 | 0.292 | 60.0% | 0.9976 |

### 3-month resets, 25 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +15.743 | +17.050 | +16.508 | -9.690 |
| TAIL | +14.825 | +15.980 | +15.505 | -9.268 |
| CAOS | +15.243 | +16.467 | +15.943 | -9.218 |
| bills | +15.211 | +16.429 | +15.905 | -9.163 |
| duration | +15.103 | +16.304 | +15.815 | -9.465 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| TAIL vs unchanged | -0.918 [-1.498, -0.248] | 0.9728 | 0.787 | 100.0% | 0.9835 |
| TAIL vs bills | -0.386 [-0.755, +0.064] | 0.9885 | 0.413 | 72.0% | 0.9903 |
| TAIL vs duration | -0.278 [-0.566, +0.081] | 0.9917 | 0.378 | 84.0% | 0.9932 |
| CAOS vs unchanged | -0.500 [-0.954, -0.038] | 0.9851 | 0.542 | 100.0% | 0.9894 |
| CAOS vs bills | +0.032 [-0.049, +0.133] | 1.0010 | 0.099 | 64.0% | 0.9992 |
| CAOS vs duration | +0.140 [-0.130, +0.451] | 1.0042 | 0.292 | 60.0% | 0.9976 |

## cautious: 2023-10 to 2026-03 (30 months)

### 12-month resets, 5 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +11.868 | +12.601 | +12.200 | -4.501 |
| TAIL | +11.590 | +12.289 | +11.907 | -4.410 |
| CAOS | +11.825 | +12.553 | +12.147 | -4.422 |
| bills | +11.833 | +12.562 | +12.154 | -4.425 |
| duration | +11.861 | +12.593 | +12.197 | -4.533 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| TAIL vs unchanged | -0.278 [-0.579, +0.089] | 0.9931 | 0.388 | 68.4% | 0.9938 |
| TAIL vs bills | -0.243 [-0.571, +0.155] | 0.9939 | 0.418 | 63.2% | 0.9929 |
| TAIL vs duration | -0.270 [-0.570, +0.098] | 0.9933 | 0.388 | 78.9% | 0.9937 |
| CAOS vs unchanged | -0.043 [-0.165, +0.092] | 0.9989 | 0.193 | 84.2% | 0.9979 |
| CAOS vs bills | -0.008 [-0.056, +0.051] | 0.9998 | 0.071 | 73.7% | 0.9993 |
| CAOS vs duration | -0.036 [-0.225, +0.161] | 0.9991 | 0.282 | 63.2% | 0.9975 |

### 12-month resets, 25 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +11.823 | +12.550 | +12.156 | -4.501 |
| TAIL | +11.545 | +12.238 | +11.863 | -4.410 |
| CAOS | +11.780 | +12.502 | +12.103 | -4.422 |
| bills | +11.788 | +12.511 | +12.110 | -4.425 |
| duration | +11.815 | +12.542 | +12.153 | -4.533 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| TAIL vs unchanged | -0.278 [-0.579, +0.089] | 0.9931 | 0.388 | 68.4% | 0.9938 |
| TAIL vs bills | -0.243 [-0.571, +0.155] | 0.9939 | 0.418 | 63.2% | 0.9929 |
| TAIL vs duration | -0.271 [-0.571, +0.098] | 0.9933 | 0.388 | 78.9% | 0.9937 |
| CAOS vs unchanged | -0.043 [-0.165, +0.092] | 0.9989 | 0.193 | 84.2% | 0.9979 |
| CAOS vs bills | -0.008 [-0.056, +0.051] | 0.9998 | 0.071 | 73.7% | 0.9993 |
| CAOS vs duration | -0.036 [-0.225, +0.161] | 0.9991 | 0.282 | 63.2% | 0.9975 |

### 3-month resets, 5 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +11.874 | +12.608 | +12.203 | -4.414 |
| TAIL | +11.574 | +12.270 | +11.887 | -4.317 |
| CAOS | +11.828 | +12.556 | +12.147 | -4.334 |
| bills | +11.836 | +12.564 | +12.153 | -4.338 |
| duration | +11.867 | +12.599 | +12.200 | -4.448 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| TAIL vs unchanged | -0.300 [-0.629, +0.115] | 0.9925 | 0.395 | 68.4% | 0.9932 |
| TAIL vs bills | -0.262 [-0.626, +0.181] | 0.9935 | 0.428 | 63.2% | 0.9925 |
| TAIL vs duration | -0.293 [-0.626, +0.120] | 0.9927 | 0.394 | 78.9% | 0.9931 |
| CAOS vs unchanged | -0.046 [-0.174, +0.095] | 0.9988 | 0.194 | 84.2% | 0.9980 |
| CAOS vs bills | -0.008 [-0.060, +0.053] | 0.9998 | 0.075 | 68.4% | 0.9992 |
| CAOS vs duration | -0.039 [-0.236, +0.167] | 0.9990 | 0.285 | 73.7% | 0.9976 |

### 3-month resets, 25 bp roundtrip execution

| Arm | Log growth pp/yr | CAGR % | Arithmetic pp/yr | Max drawdown % |
| --- | ---: | ---: | ---: | ---: |
| unchanged | +11.823 | +12.551 | +12.153 | -4.414 |
| TAIL | +11.523 | +12.213 | +11.837 | -4.317 |
| CAOS | +11.777 | +12.499 | +12.097 | -4.334 |
| bills | +11.785 | +12.507 | +12.103 | -4.338 |
| duration | +11.816 | +12.542 | +12.150 | -4.448 |

| Comparison | Log gap pp/yr [95%] | Wealth ratio | TE pp/yr | Rolling 12m losing fraction | Worst 12m wealth ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| TAIL vs unchanged | -0.301 [-0.630, +0.115] | 0.9925 | 0.395 | 68.4% | 0.9932 |
| TAIL vs bills | -0.262 [-0.627, +0.181] | 0.9935 | 0.428 | 63.2% | 0.9924 |
| TAIL vs duration | -0.293 [-0.626, +0.119] | 0.9927 | 0.394 | 78.9% | 0.9931 |
| CAOS vs unchanged | -0.047 [-0.174, +0.094] | 0.9988 | 0.194 | 84.2% | 0.9980 |
| CAOS vs bills | -0.008 [-0.060, +0.053] | 0.9998 | 0.075 | 68.4% | 0.9992 |
| CAOS vs duration | -0.039 [-0.236, +0.167] | 0.9990 | 0.285 | 73.7% | 0.9976 |
