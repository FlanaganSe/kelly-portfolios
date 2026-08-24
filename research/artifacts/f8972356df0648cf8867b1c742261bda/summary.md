### Phase 1 published-result reproduction gate, Fama-French (2015) Table 4 Panel A

- **Status:** `unresolved` — the available evidence cannot answer the question; this is not a negative result
- **Run:** `f8972356df0648cf8867b1c742261bda`
- **Experiment family:** `phase1_ff_reproduction`
- **Specification hash:** `5bf03adea82069ee00c7e875321c450983626b0d50beb5374cf54c5d56075976`
- **Run kind:** `confirmatory`
- **Evidence class:** `source-reproduction`
- **Falsifier:** The reproduction is REJECTED -- meaning this repository's ingestion and statistics path is treated as broken -- if ANY of the following holds. (a) The sha256 of the downloaded bytes is not the pinned cbc3724812132654fbbe8daae3c46e0f90e70008434f94a7986fe49f1db6ad3b, so the vintage under test is not the vintage this specification was written against. (b) Any sample-boundary check fails: the frozen window does not contain exactly 606 monthly observations, or the period labels are not strictly increasing, or a month is duplicated, or a month is missing from the window, or a declared missing-data sentinel survived parsing into the data, or any of the five factor columns holds a missing value inside the window. (c) Any factor's monthly mean differs from the printed value by more than 0.10 percentage points per month, or differs in sign. That is five times the gate tolerance and is far larger than any plausible CRSP restatement of a 606-month average; a difference that size is an implementation error, not a revision. The reproduction is UNRESOLVED if no clause above fires but some cell lies outside the gate tolerance. It PASSES only if every gating cell lies inside it. Failing to match is a finding to be reported, never a reason to widen the tolerance. The tolerance below may not be edited to make this run pass; editing it produces a different specification hash and a visibly different hypothesis.

UNRESOLVED: 13 of 15 gating cells of Fama-French (2015) Table 4 Panel A (2x3 block, 1963-07..2013-12, 606 months) reproduce within the predeclared tolerance, and 2 of 15 round to the printed value exactly, from the 202606 CRSP vintage (sha256 cbc372481213...).

Statistics with no cost basis:

| Statistic | Units | Value | Interval method | Observations |
| --- | --- | --- | --- | --- |
| Mkt-RF monthly mean | percent per month | 0.501 [0.1202, 0.8818] | normal 95% interval from a Newey-West HAC standard error, Bartlett kernel, L=5 from floor(4*(T/100)**(2/9)) at T=606 | 606 |
| Mkt-RF annualised arithmetic premium | percentage points per year | 6.012 [1.443, 10.58] | 12 x the monthly mean and its bounds; normal 95% interval from a Newey-West HAC standard error, Bartlett kernel, L=5 from floor(4*(T/100)**(2/9)) at T=606 | 606 |
| Mkt-RF annualised volatility | percentage points per year | 15.53 (no interval: no interval is computed for a volatility here: this experiment resamples nothing, and a chi-squared interval would assume the normality that monthly factor returns violate) | not reported | 606 |
| Mkt-RF annualised Sharpe ratio | ratio | 0.3871 [0.1104, 0.6637] | normal 95% interval from sqrt((1 + SR^2/2)/T) on the monthly Sharpe, scaled by sqrt(12); assumes i.i.d. normal returns, which these are not | 606 |
| Mkt-RF difference from published monthly mean | percentage points per month | 0.0009901 (no interval: the printed value is a constant, not a resamplable estimate; the relevant uncertainty is the +/-0.005 printing precision, which the declared tolerance carries) | not reported | 606 |
| SMB monthly mean | percent per month | 0.2788 [0.02225, 0.5354] | normal 95% interval from a Newey-West HAC standard error, Bartlett kernel, L=5 from floor(4*(T/100)**(2/9)) at T=606 | 606 |
| SMB annualised arithmetic premium | percentage points per year | 3.346 [0.267, 6.425] | 12 x the monthly mean and its bounds; normal 95% interval from a Newey-West HAC standard error, Bartlett kernel, L=5 from floor(4*(T/100)**(2/9)) at T=606 | 606 |
| SMB annualised volatility | percentage points per year | 10.55 (no interval: no interval is computed for a volatility here: this experiment resamples nothing, and a chi-squared interval would assume the normality that monthly factor returns violate) | not reported | 606 |
| SMB annualised Sharpe ratio | ratio | 0.3172 [0.04081, 0.5936] | normal 95% interval from sqrt((1 + SR^2/2)/T) on the monthly Sharpe, scaled by sqrt(12); assumes i.i.d. normal returns, which these are not | 606 |
| SMB difference from published monthly mean | percentage points per month | -0.01117 (no interval: the printed value is a constant, not a resamplable estimate; the relevant uncertainty is the +/-0.005 printing precision, which the declared tolerance carries) | not reported | 606 |
| HML monthly mean | percent per month | 0.3826 [0.1207, 0.6445] | normal 95% interval from a Newey-West HAC standard error, Bartlett kernel, L=5 from floor(4*(T/100)**(2/9)) at T=606 | 606 |
| HML annualised arithmetic premium | percentage points per year | 4.591 [1.448, 7.735] | 12 x the monthly mean and its bounds; normal 95% interval from a Newey-West HAC standard error, Bartlett kernel, L=5 from floor(4*(T/100)**(2/9)) at T=606 | 606 |
| HML annualised volatility | percentage points per year | 9.674 (no interval: no interval is computed for a volatility here: this experiment resamples nothing, and a chi-squared interval would assume the normality that monthly factor returns violate) | not reported | 606 |
| HML annualised Sharpe ratio | ratio | 0.4746 [0.1975, 0.7517] | normal 95% interval from sqrt((1 + SR^2/2)/T) on the monthly Sharpe, scaled by sqrt(12); assumes i.i.d. normal returns, which these are not | 606 |
| HML difference from published monthly mean | percentage points per month | 0.01262 (no interval: the printed value is a constant, not a resamplable estimate; the relevant uncertainty is the +/-0.005 printing precision, which the declared tolerance carries) | not reported | 606 |
| RMW monthly mean | percent per month | 0.2642 [0.0619, 0.4664] | normal 95% interval from a Newey-West HAC standard error, Bartlett kernel, L=5 from floor(4*(T/100)**(2/9)) at T=606 | 606 |
| RMW annualised arithmetic premium | percentage points per year | 3.17 [0.7428, 5.597] | 12 x the monthly mean and its bounds; normal 95% interval from a Newey-West HAC standard error, Bartlett kernel, L=5 from floor(4*(T/100)**(2/9)) at T=606 | 606 |
| RMW annualised volatility | percentage points per year | 7.791 (no interval: no interval is computed for a volatility here: this experiment resamples nothing, and a chi-squared interval would assume the normality that monthly factor returns violate) | not reported | 606 |
| RMW annualised Sharpe ratio | ratio | 0.4069 [0.1301, 0.6837] | normal 95% interval from sqrt((1 + SR^2/2)/T) on the monthly Sharpe, scaled by sqrt(12); assumes i.i.d. normal returns, which these are not | 606 |
| RMW difference from published monthly mean | percentage points per month | 0.01417 (no interval: the printed value is a constant, not a resamplable estimate; the relevant uncertainty is the +/-0.005 printing precision, which the declared tolerance carries) | not reported | 606 |
| CMA monthly mean | percent per month | 0.3256 [0.1452, 0.506] | normal 95% interval from a Newey-West HAC standard error, Bartlett kernel, L=5 from floor(4*(T/100)**(2/9)) at T=606 | 606 |
| CMA annualised arithmetic premium | percentage points per year | 3.907 [1.743, 6.072] | 12 x the monthly mean and its bounds; normal 95% interval from a Newey-West HAC standard error, Bartlett kernel, L=5 from floor(4*(T/100)**(2/9)) at T=606 | 606 |
| CMA annualised volatility | percentage points per year | 6.926 (no interval: no interval is computed for a volatility here: this experiment resamples nothing, and a chi-squared interval would assume the normality that monthly factor returns violate) | not reported | 606 |
| CMA annualised Sharpe ratio | ratio | 0.5642 [0.2865, 0.8418] | normal 95% interval from sqrt((1 + SR^2/2)/T) on the monthly Sharpe, scaled by sqrt(12); assumes i.i.d. normal returns, which these are not | 606 |
| CMA difference from published monthly mean | percentage points per month | -0.004389 (no interval: the printed value is a constant, not a resamplable estimate; the relevant uncertainty is the +/-0.005 printing precision, which the declared tolerance carries) | not reported | 606 |

**Caveats.**
- Passing this gate does NOT verify portfolio accounting, rebalancing, transaction costs, tax lots, corporate actions, insolvency behaviour, missing-data handling, look-ahead protection, or optimisation constraints. None of them is exercised here.
- The published factor file already contains the authors' own calculated returns. Matching their table shows we read and summarised their numbers correctly; it does not show that we could have computed them.
- This check can match despite compensating errors. It is a necessary condition for trusting the ingestion path, not a sufficient one.
- Every figure is gross of transaction costs, shorting costs, fees and taxes, because the source series are. The long-short series are not investable and no premium here is achievable.
- Mkt-RF, SMB, HML, RMW and CMA are ALL already excess or long-short returns. RF was not subtracted from any of them. The wrong_risk_free_treatment diagnostic measures how far each mean would move if it had been.
- The file was built from a CRSP vintage roughly twelve years later than the one the authors used, and no vintage archive exists, so an exactly like-for-like reproduction is unavailable at any tolerance. A sha256 pins which file was used; it does not establish what was available in 2014.
- sqrt(12) annualisation of volatility and of the Sharpe ratio assumes serially independent monthly returns, which these are not. The HAC standard error beside each conventional one is the size of that assumption.
