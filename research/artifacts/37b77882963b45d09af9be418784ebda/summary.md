### Factor persistence and decay across frozen eras

- **Status:** `unresolved` — the available evidence cannot answer the question; this is not a negative result
- **Run:** `37b77882963b45d09af9be418784ebda`
- **Experiment family:** `exp_001_factor_decay`
- **Specification hash:** `f9184dfe26619e85b083fae3a08e283eea83daaea977d058fb707554e68f3d76`
- **Run kind:** `exploratory`
- **Evidence class:** `public-series-evaluation`
- **Falsifier:** The hypothesis is rejected for a factor when ANY of the following holds in the frozen eras. (a) The point estimate of the annualised premium over the full post-publication era is less than or equal to zero. (b) The upper end of the two-sided 90% block-bootstrap interval for the full post-publication annualised premium lies below the materiality threshold of 2.0 percentage points per year, i.e. the factor is economically negligible even under a favourable draw. (c) The full post-publication point estimate is below 25% of the original-sample point estimate AND the recent-era point estimate is less than or equal to zero, i.e. decay is both large and continuing. A one-sided 95% test failing to exclude a zero mean is explicitly NOT a falsifier: long-lived modest premia lack that power over the available sample, and treating the test as a survival criterion would reject economically useful premia for want of data. That case is recorded as `unresolved`.

rejected: CMA, unresolved: HML, RMW, UMD. Of the 20 predeclared cells, 5 have a one-sided HAC p-value at or below 0.05 uncorrected and 4 survive Benjamini-Hochberg at 0.10; 16 hold a premium smaller than what their own window could detect at 80% power. All figures are gross of every cost and are not investable.

Gross, net-optimistic and net-pessimistic are separate columns and are never collapsed; the spread between them is the cost-model uncertainty.

| Statistic | Units | Gross | Net-optimistic | Net-pessimistic | Interval method |
| --- | --- | --- | --- | --- | --- |
| HML original_sample annualised premium | percentage points per year | 4.559 [1.31, 7.656] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| HML original_sample annualised Sharpe | ratio | 0.5184 [0.1727, 0.8531] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| HML first_post_publication annualised premium | percentage points per year | 5.851 [-1.842, 13.98] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| HML first_post_publication annualised Sharpe | ratio | 0.4668 [-0.1547, 1.022] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| HML full_post_publication annualised premium | percentage points per year | 1.566 [-2.28, 5.541] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| HML full_post_publication annualised Sharpe | ratio | 0.137 [-0.2095, 0.4757] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| HML recent annualised premium | percentage points per year | -0.435 [-8.275, 7.271] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| HML recent annualised Sharpe | ratio | -0.03266 [-0.6507, 0.5331] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| HML common_period annualised premium | percentage points per year | -1.352 [-7.752, 5.181] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| HML common_period annualised Sharpe | ratio | -0.1082 [-0.6656, 0.3918] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| UMD original_sample annualised premium | percentage points per year | 9.853 [6.402, 13.32] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| UMD original_sample annualised Sharpe | ratio | 0.8031 [0.526, 1.114] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| UMD first_post_publication annualised premium | percentage points per year | 10.53 [2.781, 18.47] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| UMD first_post_publication annualised Sharpe | ratio | 0.5345 [0.1533, 1.018] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| UMD full_post_publication annualised premium | percentage points per year | 4.195 [-0.3444, 8.504] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| UMD full_post_publication annualised Sharpe | ratio | 0.2535 [-0.02058, 0.5557] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| UMD recent annualised premium | percentage points per year | 0.375 [-4.686, 5.406] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| UMD recent annualised Sharpe | ratio | 0.02819 [-0.3633, 0.4324] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| UMD common_period annualised premium | percentage points per year | 2.098 [-2.115, 6.245] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| UMD common_period annualised Sharpe | ratio | 0.1591 [-0.1599, 0.4936] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| RMW original_sample annualised premium | percentage points per year | 3.17 [1.143, 5.228] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| RMW original_sample annualised Sharpe | ratio | 0.4069 [0.1502, 0.7162] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| RMW first_post_publication annualised premium | percentage points per year | 1.635 [-0.04667, 3.363] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| RMW first_post_publication annualised Sharpe | ratio | 0.3216 [-0.009205, 0.6511] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| RMW full_post_publication annualised premium | percentage points per year | 3.041 [-0.3175, 6.755] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| RMW full_post_publication annualised Sharpe | ratio | 0.414 [-0.05191, 0.8261] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| RMW recent annualised premium | percentage points per year | 3.509 [-0.2331, 7.562] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| RMW recent annualised Sharpe | ratio | 0.458 [-0.03152, 0.893] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| RMW common_period annualised premium | percentage points per year | 3.041 [-0.3134, 6.61] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| RMW common_period annualised Sharpe | ratio | 0.414 [-0.03907, 0.8245] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| CMA original_sample annualised premium | percentage points per year | 3.907 [2.059, 5.854] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| CMA original_sample annualised Sharpe | ratio | 0.5642 [0.32, 0.8113] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| CMA first_post_publication annualised premium | percentage points per year | -2.457 [-4.955, 0.1267] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| CMA first_post_publication annualised Sharpe | ratio | -0.4646 [-0.9919, 0.007631] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| CMA full_post_publication annualised premium | percentage points per year | -1.392 [-5.001, 3.021] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| CMA full_post_publication annualised Sharpe | ratio | -0.1759 [-0.7696, 0.3139] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| CMA recent annualised premium | percentage points per year | -0.601 [-4.856, 4.346] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| CMA recent annualised Sharpe | ratio | -0.07079 [-0.6851, 0.4522] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| CMA common_period annualised premium | percentage points per year | -1.392 [-4.996, 2.931] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |
| CMA common_period annualised Sharpe | ratio | -0.1759 [-0.7898, 0.3223] | not reported | not reported | stationary block bootstrap, two-sided 90%, mean block 12m, 10000 resamples |

**Caveats.**
- These are academic zero-investment long-short research portfolios, gross of transaction costs, shorting costs, borrow, fees and taxes. A retail investor cannot implement most of them at all. Every figure here is an UPPER BOUND of unknown tightness and no factor may be described as working on this evidence.
- The Phase 1 ingestion gate is UNRESOLVED, not passed. The HML and RMW standard deviations do not reproduce Fama and French (2015) Table 4, by 3.03% and 5.09%, against two independently typeset vintages. Every Sharpe ratio, volatility and minimum detectable effect for those two factors carries a systematic band that is reported separately and is NOT in any bootstrap interval.
- UMD comes from the momentum file, which was never gated against a printed table. Its second moment is unmeasured rather than verified, which is a weaker statement than a band of zero.
- A before/after comparison across a publication date is DESCRIPTIVE. It confounds publication with changing composition, valuation regimes, crowding and chance, and this experiment does not claim to identify a publication effect.
- The currently distributed files apply the current CRSP vintage and the current construction to the whole history, including the pre-publication eras. The original-sample figures are therefore NOT the authors' original series, and a difference from their printed table is expected.
- The 20 cells of the multiple-testing family are strongly dependent: eras nest, RMW and CMA share every era, and all four factors are spreads over overlapping holdings of one universe. Benjamini-Hochberg treats them as independent, so the corrected p-values are a LOWER bound on the true correction.
- The cost column is an ILLUSTRATION of the implementation gap for a tradable strategy of comparable turnover. It is never subtracted from a premium, because the French series have no turnover and no tradable form. Novy-Marx and Velikov's haircut is 17% in the low-turnover tier and 144% in the high-turnover tier, where four of six strategies were net negative.
- The equal-weighted robustness test was not run: the library distributes no equal-weighted variant of these files. That sensitivity is untested.
