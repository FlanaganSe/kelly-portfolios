### Unlevered rebalancing policy comparison on regional equity sleeves, pretax

- **Status:** `rejected` — the predeclared falsifier fired
- **Run:** `add1e77a184d45808bc062ac372f44ca`
- **Experiment family:** `exp_003_rebalancing`
- **Specification hash:** `fe521d2fbc0258027294e3eaebc402fdf74ee2543715adebb4bb8ed6a9ea4a72`
- **Run kind:** `confirmatory`
- **Evidence class:** `policy-simulation`
- **Falsifier:** The hypothesis is rejected when no policy's pretax net certainty-equivalent return exceeds buy-and-hold's by at least 0.25 percentage points per year with a two-sided 95% block-bootstrap interval on the DIFFERENCE that excludes zero, or when every policy that clears that bar also has a maximum drawdown at least 1.0 percentage point worse than buy-and-hold. The hypothesis is additionally rejected if the surviving advantage is not present in at least two of the three frozen non-overlapping eras, since a single-era advantage is a diagnostic and not a finding.

REJECTED: PRETAX. Over 420 months (1991-01..2025-12) on us_equity, developed_ex_us_equity, emerging_equity, the best policy against buy-and-hold on the net-pessimistic basis is annual_calendar at -0.199 pp/yr certainty-equivalent [-1.829, +0.402], against a frozen materiality threshold of 0.25 pp/yr. gamma_star on the three-sleeve portfolio and every regional pair is reported predicted against realised, and the kappa serial-dependence diagnostic decides whether the mechanism that could make rebalancing profitable is present.

Gross, net-optimistic and net-pessimistic are separate columns and are never collapsed; the spread between them is the cost-model uncertainty.

| Statistic | Units | Gross | Net-optimistic | Net-pessimistic | Interval method |
| --- | --- | --- | --- | --- | --- |
| buy_and_hold certainty-equivalent return | percentage points per year | 6.37 (no interval: the decision is taken on the paired difference, so the level's interval would invite a comparison the specification forbids; the paired intervals below are the reportable uncertainty) | 6.37 (no interval: the decision is taken on the paired difference, so the level's interval would invite a comparison the specification forbids; the paired intervals below are the reportable uncertainty) | 6.37 (no interval: the decision is taken on the paired difference, so the level's interval would invite a comparison the specification forbids; the paired intervals below are the reportable uncertainty) | not reported |
| annual_calendar minus buy-and-hold certainty-equivalent return | percentage points per year | -0.1944 [-1.826, 0.4064] | -0.1957 [-1.827, 0.4052] | -0.1995 [-1.829, 0.4022] | stationary block bootstrap on the joint sleeve panel, mean block 24 months frozen not tuned, percentile interval on the paired difference |
| cash_flow_directed minus buy-and-hold certainty-equivalent return | percentage points per year | -0.3731 [-0.8714, 0.2556] | -0.3731 [-0.8714, 0.2556] | -0.3731 [-0.8714, 0.2556] | stationary block bootstrap on the joint sleeve panel, mean block 24 months frozen not tuned, percentile interval on the paired difference |
| monthly_calendar minus buy-and-hold certainty-equivalent return | percentage points per year | -0.3262 [-1.938, 0.3244] | -0.3293 [-1.941, 0.3215] | -0.3386 [-1.951, 0.3126] | stationary block bootstrap on the joint sleeve panel, mean block 24 months frozen not tuned, percentile interval on the paired difference |
| relative_threshold_25pct minus buy-and-hold certainty-equivalent return | percentage points per year | -0.2102 [-1.694, 0.4477] | -0.2109 [-1.695, 0.4467] | -0.2129 [-1.698, 0.4444] | stationary block bootstrap on the joint sleeve panel, mean block 24 months frozen not tuned, percentile interval on the paired difference |

Statistics with no cost basis:

| Statistic | Units | Value | Interval method | Observations |
| --- | --- | --- | --- | --- |
| us_equity\|developed_ex_us_equity gamma_star, realised minus predicted | basis points per year | 0.1648 (no interval: both terms are computed from the same single realised path, so their difference has no sampling distribution that is not the path's own; the discrete-monthly prediction beside it is the size of the model's own approximation) | not reported | 420 |
| us_equity\|developed_ex_us_equity realised rebalanced minus buy-and-hold log growth | basis points per year | -62.89 [-33.13, 12.48] | closed-form 5th and 95th percentiles of the equal-drift model, not a sampling interval: it is the model's own predicted band and the realised value is asked whether it falls inside it | 420 |
| us_equity\|emerging_equity gamma_star, realised minus predicted | basis points per year | -0.001592 (no interval: both terms are computed from the same single realised path, so their difference has no sampling distribution that is not the path's own; the discrete-monthly prediction beside it is the size of the model's own approximation) | not reported | 420 |
| us_equity\|emerging_equity realised rebalanced minus buy-and-hold log growth | basis points per year | -1.516 [-63.02, 25.43] | closed-form 5th and 95th percentiles of the equal-drift model, not a sampling interval: it is the model's own predicted band and the realised value is asked whether it falls inside it | 420 |
| developed_ex_us_equity\|emerging_equity gamma_star, realised minus predicted | basis points per year | -0.022 (no interval: both terms are computed from the same single realised path, so their difference has no sampling distribution that is not the path's own; the discrete-monthly prediction beside it is the size of the model's own approximation) | not reported | 420 |
| developed_ex_us_equity\|emerging_equity realised rebalanced minus buy-and-hold log growth | basis points per year | 6.941 [-53.42, 21.08] | closed-form 5th and 95th percentiles of the equal-drift model, not a sampling interval: it is the model's own predicted band and the realised value is asked whether it falls inside it | 420 |
| us_equity\|developed_ex_us_equity kappa lag-1 autocorrelation | correlation | 0.08081 [-0.02049, 0.1522] | stationary block bootstrap percentile interval, mean block 24 months, frozen not tuned | 420 |
| us_equity\|emerging_equity kappa lag-1 autocorrelation | correlation | 0.203 [0.04727, 0.2968] | stationary block bootstrap percentile interval, mean block 24 months, frozen not tuned | 420 |
| developed_ex_us_equity\|emerging_equity kappa lag-1 autocorrelation | correlation | 0.1283 [-0.03961, 0.2184] | stationary block bootstrap percentile interval, mean block 24 months, frozen not tuned | 420 |

**Caveats.**
- PRETAX. No tax of any kind is modelled and no constant tax haircut is applied. The simulation holds no tax lots, so it cannot know a basis and therefore may not price a realisation. In a taxable account the ranking would move against the higher-turnover policies, because a rebalance realises gain that buy-and-hold defers; the size of that move is not estimated here and must not be guessed.
- These are index-like regional total returns, not investable funds. They carry no expense ratio, no bid-ask spread, no tracking difference and no withholding tax. Those are reported in the investability_drag column and never applied to a return. Any claim about what an investor would have received is capped at exploratory by decision 0002.
- The decades are DIAGNOSTICS. Three overlapping regimes inside one 35-year sample are not three independent observations, and no statement about any policy is made from a single era.
- Ken French rebuilds each region's whole history from every new source vintage and publishes no vintage archive. The sha256 pins identify which files were used; they do not establish what was available at any earlier date, so nothing here is point-in-time.
- The source is monthly, so intramonth threshold breaches are invisible and no intramonth execution is modelled. A daily threshold policy would trade more often than the one measured here.
- Deploying a contribution is charged no transaction cost, for every policy identically. The total notional deployed is the contribution itself and is the same under every policy, so at a flat basis-point rate this omission cancels in every paired difference; it understates every policy's absolute cost by the same amount.
- The stationary bootstrap preserves short-range dependence at the frozen 24-month mean block length and attenuates it beyond that. Autocorrelations at lags approaching or exceeding the block length have conservatively wide intervals for that reason.
- Rolling-window win frequencies use overlapping windows, which are not independent observations. A 30-year window inside a 35-year sample has six distinct start months.
