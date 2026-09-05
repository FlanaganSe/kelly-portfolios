# Interpretation and specification limitations

Exploratory run `c9c0b898cf644ca0a2723d7ea0b02255`, specification
`924ec9870e6ac32b5fe3537c2e05c393121f3e2bcd0d730d02a8cefffdb43d05`,
code commit `c16d226434404e4ff0ff67b87ec84713387f75f7`. These notes interpret the
unaltered generated `result.json`, `summary.md` and `tables.md`.

The five percent TAIL allocation protected the equity portfolio more than bills during
February–March 2020, but lost log growth and had a deeper full-window month-end drawdown
than the bill-funded control. This is a path-dependent trade-off, not evidence that
protection never works. CAOS behaved much like the bill-funded control on the short
current-ETF window. Neither result promotes a crash-hedge allocation.

All figures below use annual resets and 5 bp roundtrip execution. The complete tables
also show quarterly resets and 25 bp execution; neither sensitivity creates a material
change to this interpretation. Log gaps are percentage points per year.

| Window and hedge | Log gap versus unchanged [paired 95% interval] | Log gap versus bills [95%] |
| --- | ---: | ---: |
| Equity, February 2020–March 2026, TAIL | −0.776 [−1.388, +0.149] | −0.386 [−0.668, +0.060] |
| Equity, April 2023–March 2026, TAIL | −0.861 [−1.366, −0.255] | −0.341 [−0.661, +0.030] |
| Equity, April 2023–March 2026, CAOS | −0.490 [−0.896, −0.045] | +0.030 [−0.045, +0.128] |
| Cautious, October 2023–March 2026, TAIL | −0.278 [−0.579, +0.089] | −0.243 [−0.571, +0.155] |
| Cautious, October 2023–March 2026, CAOS | −0.043 [−0.165, +0.092] | −0.008 [−0.056, +0.051] |

For the longest equity window, unchanged/TAIL/bills/duration-control month-end maximum
drawdowns were −25.58%/−24.64%/−24.36%/−25.05%. The same order's complete
February–March 2020 portfolio returns were −21.16%/−19.09%/−20.08%/−19.79%.
Initial purchase costs are included in that first episode for every arm.
TAIL therefore improved that crash episode by approximately 0.99 percentage points over
bills while costing 0.39 pp/yr of log growth over the full measured window. Calendar 2022
returns were −18.37%/−18.16%/−17.45%/−18.15%; the duration control matters to the
interpretation. No option-leg P&L is identified by these differences.

The full calendar 2020 episode is incomplete and has no reported return. Neither short
window contains the 2020 or 2022 crises. The cautious window contains only the last month
of the declared July–October 2023 episode, so that episode also has no reported return.
The JSON preserves desired months, available months and completeness for each arm.

The frozen cost-model and secondary-metric prose inherited references to annual trading.
Its explicit rebalance rule and parameters prescribe both 12- and 3-month schedules;
implementation charges every scheduled trade in both. Quarterly means every three months
from the sample's starting month, not necessarily calendar-quarter ends. Initial purchases
are charged, terminal liquidation and investor taxes are omitted, and monthly NAV execution
is an approximation to exchange trading. Internal option purchases and fees are not
subtracted again from net NAV returns.

CAOS's current ETF history is not a constant-strategy claim. Conversion-era disclosure
specified a typical upper equity exposure of 100%; by January 2025 it was 120%. The
current fund's protective options, variable equity and collateral prevent attribution of
its stock-relative return gap to option-premium bleed. The reverse split requires no
additional adjustment to filed total returns. Sources:
[2023 summary](https://www.sec.gov/Archives/edgar/data/1592900/000182912623001899/easeries-caos_497k.htm),
[2025 summary](https://www.sec.gov/Archives/edgar/data/1592900/000159290025000250/caos497ksummaryprospectus.htm).

TAIL's longer source is available: the
[2025 SEC shareholder report](https://www.sec.gov/Archives/edgar/data/1529390/000199937125008871/cambria_ncsr-043025.htm)
contains rounded monthly total-return wealth back to 2017. This experiment uses contiguous
N-PORT data from February 2020 and does not claim that earlier history is unavailable.
Extending with rounded wealth requires a separate source contract, overlap check and
consistent control histories. The present comparison is a current-survivor test, not a
fund-family census including closures.

`result.json` records 301 source byte identities, URLs and retrieval timestamps, all fund
series/class IDs, weights, monthly portfolio returns and wealth, costs, relative metrics,
bootstrap intervals and episode coverage. Exact byte identities do not establish historical
availability or future strategy continuity. IEF/BIL is an approximate duration control;
its historical exposures are not fitted to TAIL. Bootstrap uncertainty is descriptive and
is not an investment rule or a forecast of underperformance probability.
