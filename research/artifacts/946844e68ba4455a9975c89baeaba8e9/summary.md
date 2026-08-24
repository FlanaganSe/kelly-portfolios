### How many correlated strategies a long-only optimiser actually holds

- **Status:** `exploratory` — a search, not a finding; it may not be quoted as evidence that anything works
- **Run:** `946844e68ba4455a9975c89baeaba8e9`
- **Experiment family:** `exp_017_longonly_ladder`
- **Specification hash:** `7c3822a2dcc0810b2efc0039f6af24630204951b0b927b33ff67c26893f57c67`
- **Run kind:** `exploratory`
- **Evidence class:** `policy-simulation`
- **Falsifier:** This experiment CANNOT be falsified by data, and saying so is part of freezing it: the arithmetic is deterministic and exact given the inputs, so there is no sampling distribution, no p-value, no detection floor and no interval. What can be falsified is the CLAIM the page makes from it, and the falsifiers are: (a) THE COUNT IS NOT ROBUST TO DISPERSION. If the candidates are given identical edges, equal weighting is optimal, the transfer coefficient is 1.000 and the optimiser holds all of them. The declared dispersion is therefore load-bearing and the run must report the identical-edge case beside the headline. If the identical-edge case does NOT recover a transfer coefficient of 1.000, the implementation is wrong. (b) THE COUNT IS NOT A CONSTANT. It is monotone in rho and the run must report the sweep. If the held count does not fall as rho rises, or if the unconstrained and long-only columns do not diverge, the mechanism above is wrong. (c) THE EQUAL-WEIGHT OPTIMUM IS NOT A COST RESULT. If setting every cost to zero moves the equal-weighted optimum, then the claim that dilution alone produces the shape is false and must be withdrawn. (d) THE OPTIMISER MUST BE EXACT. If a dense random search over the non-negative simplex beats the enumerated optimum by more than floating-point noise, the enumeration is wrong and the run is void.

On the frozen twelve-candidate ladder at rho = 0.435, the best equal-weighted portfolio holds 2 candidates and the exact long-only optimum holds 3, unchanged from three candidates upward, while the unconstrained optimum keeps improving to 0.727 — a transfer coefficient of 0.636, with 7 of twelve unconstrained weights short and net long exposure at 0.084 of gross. EVERY EDGE IS AN ASSUMPTION: this experiment reads no market data, so the result is a property of the stated ladder rather than of markets, and the 0.435 correlation is one portfolio's measurement rather than a market constant.

Gross, net-optimistic and net-pessimistic are separate columns and are never collapsed; the spread between them is the cost-model uncertainty.

| Statistic | Units | Gross | Net-optimistic | Net-pessimistic | Interval method |
| --- | --- | --- | --- | --- | --- |
| sleeves held at the long-only optimum, twelve candidates | count | not reported | 3 (no interval: Deterministic given the stated ladder. Nothing is sampled, so there is no sampling distribution and an interval would be a fabrication. The declared correlation and dispersion sweeps stand in its place: the count spans 2 to 5 across the correlation grid and reaches every candidate under identical edges.) | not reported | not reported |
| candidates held by the best equal-weighted portfolio | count | 2 (no interval: Deterministic given the stated ladder.) | 2 (no interval: Deterministic given the stated ladder.) | 2 (no interval: Deterministic given the stated ladder.) | not reported |
| long-only transfer coefficient, twelve candidates | ratio | not reported | 0.6364 (no interval: Deterministic. Across the declared correlation grid it spans 0.443 to 0.908.) | not reported | not reported |
| long-only information ratio, twelve candidates | ratio | not reported | 0.4627 (no interval: Deterministic given the stated ladder.) | not reported | not reported |
| unconstrained information ratio, twelve candidates | ratio | not reported | 0.727 (no interval: Deterministic given the stated ladder.) | not reported | not reported |
| equal-weight information ratio, twelve candidates | ratio | not reported | 0.159 (no interval: Deterministic given the stated ladder.) | not reported | not reported |

Statistics with no cost basis:

| Statistic | Units | Value | Interval method | Observations |
| --- | --- | --- | --- | --- |
| short positions at the unconstrained optimum, twelve candidates | count | 7 (no interval: Deterministic given the stated ladder.) | not reported | not reported |

**Caveats.**
- No market data is read and no premium is estimated. Every candidate edge is an input declared in the specification.
- The 0.435 correlation is measured on the candidate portfolio's own four value and momentum tilts plus a trend overlay. A genuinely wider stack would sit lower and hold more candidates.
- The count depends on edge DISPERSION as much as on correlation. Give every candidate the same edge and the optimiser holds all 8 at a transfer coefficient of 1.000.
- The ladder omits skew, fat tails, time-varying correlation and estimation error in the edges. Each omission favours the thesis, so this is the generous case.
- The result has no interval and none may be invented; the declared sweeps are the sensitivity.
- Nothing here is promotable. An experiment with no data cannot supply evidence about markets; it can only make an argument reproducible.
