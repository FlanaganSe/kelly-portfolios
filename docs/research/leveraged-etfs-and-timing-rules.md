# Leveraged ETFs and the 200-day rule: the leverage is real, the timing is not, and the drawdown protection covers slow bear markets only

**Question.** The investor asked whether "strategies like the 200 day SMA" belong in the
portfolio, and has said leverage is acceptable when it has a purpose. Two retail
constructions pair the signal with daily-reset leveraged funds: Gayed's *Leverage for the
Long Run* (2016), which holds a 2x or 3x S&P 500 fund above the 200-day moving average and
bills below it, and the static 55/45 UPRO/TMF mix known as HFEA, rebalanced quarterly. Are
they dominated by the financed trend overlay the portfolio already holds, or do they add
something at the right price?

**Decision it informs.** Whether any leveraged timing rule or static leveraged mix belongs in
one of the investor's sheltered thirds, at what size, and whether it duplicates the 30%
stacked trend position.

**Out of scope.** The unlevered 10-month rule at monthly resolution, which
[timing rules on the equity sleeve](timing-rules-on-the-equity-sleeve.md) owns and this page
reconciles with in one row; the trend weight
([trend weight](trend-weight-under-uncertainty.md)); whether to hold equity leverage as such
([leverage and the notional budget](leverage-and-the-notional-budget.md)).

`as of 2026-09-02`. **`exploratory`.**
[Experiment 021](../../research/experiments/exp_021_leveraged_etf_rules.yaml), spec
`81e165c6…`, run
[`06890724…`](../../research/artifacts/0689072433a341e6bad8216f4ca94436/summary.md), with
every table in
[`tables.md`](../../research/artifacts/0689072433a341e6bad8216f4ca94436/tables.md). Code:
[`experiments/exp_021_leveraged_etf_rules.py`](../../research/src/portfolio_edge/experiments/exp_021_leveraged_etf_rules.py),
fixtures in `research/tests/unit/test_experiments_exp_021_leveraged_etf_rules.py`. The daily
Ken French file is new to the repository:
[`data-manifests/french_us_ff3_daily.json`](../../research/data-manifests/french_us_ff3_daily.json),
26,274 trading days 1926-07-01 to 2026-06-30, sha256 `39f9ae1d…`. The specification
predicted, before the run, that every timed arm's mean gap would come back `unresolved`
against every control. That prediction held for the control that isolates timing and failed
for the two that do not; section 2 says why the failure is a leverage result.

---

## Conclusion

1. **The rule adds no measurable timing content at any leverage, and post-1990 the point
   estimate is negative.** Scored against the same leveraged fund held at the rule's own
   average exposure, the control the earlier study called the honest one, the 200-day rule
   on a 3x fund reads **+4.79 pp/yr [-1.10, +10.67] against an 8.41 floor** on 99 years
   (`unresolved`) and **-0.44 [-9.36, +8.47] against 12.74** from 1990-11 (`rejected`). On 2x:
   +3.00 against 5.62, then -0.51. On 1x at daily resolution: +1.22 against 2.82, then
   -0.53, which reproduces the monthly page's +0.74 against 3.03. The one-day execution lag
   the specification imposes costs the 3x rule 2.3 pp/yr of that content (lag 0 reads
   +7.12); the total-return signal index costs it another 2 (the price proxy reads +6.94).
   Neither moves the reading out of its floor. Sections 3 and 4.
2. **Everything else the rule appears to earn is leverage.** The 3x rule beats the unlevered
   index by +13.12 pp/yr [+7.74, +18.50] on 99 years and the continuous 1.3x control by
   +10.93; buy-and-hold 3x beats them by +14.57 and +12.39. Those gaps clear their floors
   and the falsifier marks them `exploratory`, which is the whole-experiment status. They
   are arithmetic means of paths that draw down 85 to 99.9 percent, on an arm carrying 2.2
   units of equity beta against a control carrying 1.0 or 1.3, and they are the same
   quantity Experiment 018 refused to size on when a leverage-matched control drew down
   92 percent. Section 2.
3. **The drawdown protection is a property of slow bear markets and it fails in fast ones.**
   The 3x rule cut 1929-32 from -99.9 to -53 percent, 2000-02 from -93 to -64, 2008-09 from
   -95 to -41 and 2020 from -77 to -30. It did nothing in **October 1987: -67 percent
   against buy-and-hold's -72**, because a crash inside three weeks cannot be exited by a
   200-day average. And its deepest drawdown of the century is not a crash at all: **-84.6
   percent from 1933-07 to 1935-04**, a run of whipsaws taken at 3x, deeper than the
   unlevered index's 1929-32 fall. Section 4.
4. **HFEA is a bond bull market with equity leverage attached.** +9.11 pp/yr [+5.21, +13.01]
   against the index on 1926-2025 and +11.06 from 1990-11, both clearing their floors, both
   leverage: 1.65 units of equity plus 1.35 of 20-year Treasuries. It drew down **-93 percent
   in 1929-32**, lost **52 percent of its wealth across 1972-81 while the index gained 60**,
   and lost 47 percent in 2022. Its 35-year record is the era Experiment 018 already showed a
   stacked Treasury leg's whole contribution sits inside. Section 5.
5. **Deflated on the active return, the rule reads 0.80 at 8.05 effective trials, 0.75 at
   the earlier study's 14.8, and 0.35 at 10,000.** It clears nothing at 0.95 at any count.
   Section 6.
6. **In a taxable account the rule costs 3.2 pp/yr at the top bracket on 3x, 2.7 on 2x and
   1.8 on 1x**, against nothing for holding the same fund (-0.3): it realises the entire position about
   three times a year. That settles the taxable third. Section 7.
7. **Against the financed trend overlay the portfolio holds, the two constructions buy
   different things.** The overlay is the mean: +1.98 pp/yr [+1.26, +2.73] against a 1.06
   floor on 96 years, with under one point of drawdown reduction. The rule is the drawdown:
   30 to 55 points off a slow bear market at the same leverage, with a mean that no window
   can resolve. They overlap on one market of the roughly fifty the overlay trades, and the
   rule's active return correlates with the overlay's equity leg at 0.36 to 0.57. Section 8.
8. **Consequence.** No leveraged fund, timed or static, enters the published vector
   RSST 30 / VTI 19 / VTV 15 / VXUS 16 / AVDV 10 / IDMO 5 / AVES 5. The one construction
   this page can defend is a small sheltered 2x line under the 200-day rule for an investor
   whose purpose is equity leverage with a slow-crash brake, sized inside the 15 to 25 point
   band the notional budget already allows and displacing part of the wrapper, not added
   to it; the case for it is holdability and not return. Section 9.

---

## 1. Design

| Piece | What was run |
| --- | --- |
| Fund model | `RF + L (Mkt - RF)` per day, less 0.89 percent a year of fee and a 40 bp swap spread on the borrowed `L - 1`, accrued per calendar day; compounded daily. The reset drag is compounding, not a parameter. 80 bp is the stress case |
| Signal | Total-return index close against its 200-day average, inclusive; in above, bills below; a 1 percent hysteresis band as a second arm; read at one close, traded at the next (lag 1); lag 0 and a price-index proxy deflated 2.5 percent a year as sensitivities |
| Arms | buy-and-hold 1x, 2x, 3x; the rule on 1x, 2x, 3x with and without the band; a continuous 1.3x; HFEA 55/45 UPRO/TMF quarterly on monthly data, the equity leg compounded from the daily 3x fund and the Treasury leg `RF + 3 (ltr - RF)` on Goyal-Welch's 20-year series |
| Controls | the 3 bp index; a continuous daily-reset 1.3x (85 percent index, 15 percent 3x fund, 15.9 bp) at the portfolio's own gross notional; the same fund at the rule's average time in market, remainder in bills, no cost |
| Windows | 1927-03-05 to 2026-06-30 (26,073 days) and 1990-11-01 onward (8,978); HFEA 1926-07 to 2025-12 and 1990-11 onward |
| Inference | Newey-West with 21 lags, 95 percent interval, floor `2.8016 x SE`; a 21-day block bootstrap beside it; Benjamini-Hochberg per control per window; a sign check at the stress spread |
| Costs inside the path | 10 bp one way at every switch, so a whipsaw pays 20; the same on HFEA's rebalance turnover |

The floors are what the specification computed before the run: 0.28 pp/yr per point of
tracking error on the long window and 0.47 on the modern one, which at the 25 to 35 points a
levered timed arm tracks its controls is 7 to 10 and 12 to 16 pp/yr.

---

## 2. The leverage, on its own

| 1927-2026, 99.3 years | CAGR | arith. | vol | max DD | years under water | gap vs 1x, floor | status |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| index 1x | 10.17 | 11.23 | 17.5 | -84.1 | 17.6 | | |
| continuous 1.3x | 11.42 | 13.41 | 22.8 | -91.7 | 18.3 | +2.19 [+1.10, +3.27], 1.55 | `exploratory` |
| hold 2x | 12.65 | 18.08 | 35.0 | -98.4 | 24.3 | +6.86 [+3.24, +10.47], 5.17 | `exploratory` |
| hold 3x | 12.54 | 25.80 | 52.5 | -99.9 | 28.2 | +14.57 [+7.34, +21.80], 10.33 | `exploratory` |

**The arithmetic gap is the wrong statistic for a levered path, and the specification says so
while scoring on it.** A 3x fund's arithmetic mean is mechanically 2.3 times the index's and
its interval excludes zero on a century; its compound growth is 12.54 percent against the
index's 10.17 after a 99.9 percent drawdown and 28 years under water. The falsifier's clauses
(a) to (e) were written for gaps of a few points between constructions at similar leverage and
they pass a beta result here. Every `exploratory` status on this page against the index or the
1.3x control is of this kind, and the whole-experiment status inherits it. The control that
strips the beta is the exposure-matched one in sections 3 and 4.

From 1990-11 the same rows read 11.75 / 13.65 / 16.31 / 18.05 percent CAGR with drawdowns of
-54.6 / -65.9 / -87.6 / -98.0.

---

## 3. The 1x rule, reconciled with the monthly page

| window | gap vs exposure-matched, floor | status | max DD, rule vs index | round trips a year |
| --- | --- | --- | --- | ---: |
| 1927-2026 daily, this page | +1.22 [-0.76, +3.19], 2.82 | `unresolved` | -41.1 vs -84.1 | 2.83 |
| 1926-2026 monthly, [earlier page](timing-rules-on-the-equity-sleeve.md) | +0.74 [-1.38, +2.87], 3.03 | `unresolved` | -43.1 vs -83.7 | 0.74 |
| 1990-2026 daily, this page | -0.53 [-3.53, +2.47], 4.29 | `rejected` | -24.2 vs -54.6 | 3.03 |
| 1990-2026 monthly, earlier page | +0.35, 4.09 | `unresolved` | -18.1 vs -41.1 | |

Daily resolution changes nothing the design can see: the same sign, the same order, the same
floor. What it changes is the whipsaw count, from three exits a decade to three a year, and
with a 1 percent band to 1.3 a year at the same drawdown. Against the index the 1x rule
trails by 1.0 pp/yr of arithmetic mean on the century and by 3.3 since 1990 (a CAGR of 9.13
against 11.75), and it has been behind the index since 1932-07, 97 years without a
new relative high; since 2009-03, 17.3 years.

---

## 4. Gayed's rule on 2x and 3x

| arm | window | CAGR | max DD | under water | vs index, floor | vs 1.3x, floor | vs exposure-matched, floor | status of the last |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |
| rule on 2x | 1927-2026 | 15.30 | -68.3 | 5.1 y | +5.74, 4.96 | +3.56, 5.30 | **+3.00 [-0.93, +6.93], 5.62** | `unresolved` |
| rule on 3x | 1927-2026 | 19.88 | -84.6 | 6.1 y | +13.12, 7.69 | +10.93, 7.42 | **+4.79 [-1.10, +10.67], 8.41** | `unresolved` |
| rule on 2x | 1990-2026 | 14.07 | -47.5 | 5.3 y | +3.18, 7.72 | +0.36, 8.10 | **-0.51 [-6.46, +5.45], 8.51** | `rejected` |
| rule on 3x | 1990-2026 | 18.35 | -64.7 | 6.0 y | +10.37, 12.02 | +7.55, 11.59 | **-0.44 [-9.36, +8.47], 12.74** | `rejected` |

The band arms differ from these by under 0.4 pp/yr on every gap and by 1 to 5 points of
drawdown, worse in three of the four cases, at half the round trips; they are in the artifact and not
repeated.

**Read the last column.** The rule spends 72.5 percent of its days in the fund, so its average
exposure is 2.17 units of equity on 3x and 1.45 on 2x. A constant-weight portfolio at that
exposure, in the same fund with the same fee and spread, earns the rule's beta with no timing
and no trading cost, and the rule's gap against it is +4.79 pp/yr inside an 8.41 floor, then
negative. The first two gap columns are the difference between 2.17 units of beta and 1.0 or
1.3; they are what section 2 measured, with the rule's drawdown attached.

**Where the drawdowns sit.**

| arm, 1927-2026 | deepest drawdown | from | to | what it was |
| --- | ---: | --- | --- | --- |
| index 1x | -84.1 | 1929-09-03 | 1932-07-08 | the crash |
| rule on 1x | -41.1 | 1933-07-18 | 1935-04-11 | whipsaws after the crash |
| rule on 2x | -68.3 | 1933-07-18 | 1935-04-11 | the same whipsaws at 2x |
| rule on 3x | -84.6 | 1933-07-18 | 1935-04-11 | the same whipsaws at 3x |
| hold 3x | -99.9 | 1929-09-03 | 1932-07-08 | the crash at 3x |

The rule's protection in the crash was real: -53 percent on 3x across 1929-09 to 1932-06
against -99.9. Its worst outcome came afterwards, in the two years of false starts that
followed, when it was whipped out and back in three times a year at triple leverage. From
1990 the deepest fall is 2000-03 to 2003-04, -64.7 percent on 3x and -47.5 on 2x, against the
index's -54.6 in 2007-09.

| crisis episode | index | rule on 2x | rule on 3x | hold 3x |
| --- | ---: | ---: | ---: | ---: |
| 1929-09 to 1932-06 | -83.9 | -38.1 | -53.1 | -99.9 |
| **October 1987** | -28.3 | **-48.8** | **-67.2** | -72.2 |
| 2000-03 to 2002-10 | -49.2 | -46.5 | -63.6 | -93.4 |
| 2007-10 to 2009-03 | -54.2 | -29.2 | -41.3 | -95.2 |
| 2020-02-19 to 03-23 | -33.8 | -20.4 | -29.5 | -76.8 |
| 2022-01 to 2022-10 | -24.9 | -24.7 | -34.9 | -64.5 |

Cumulative return inside the window. A slow bear market is where the rule pays: 2008-09 at 3x
is a shallower loss than the unlevered index. A three-week crash is where it does not: October
1987 at 3x is 67 percent of the position, five points better than holding, and 2022, a rate
shock with rallies, is worse than the index at either leverage.

**Holdability, measured as relative wealth.** The 3x rule fell 85.5 percent behind the index
between 1932-07 and 1935-04 and spent 15.0 years behind it; since 1990 it fell 56 percent
behind between 1998-07 and 2002-05 and was 11.7 years behind. The 2x rule has been behind the
continuous 1.3x control for 17.3 years, since 2009-03, and still is. These are the stretches
an investor would have to sit through at two to three times leverage while continuing to
follow the signal.

---

## 5. HFEA

| window | CAGR | vol | max DD | under water | vs index, floor | vs 1.3x, floor |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| 1926-07 to 2025-12 | 15.98 | 34.6 | -93.0 | 10.0 y | +9.11 [+5.21, +13.01], 5.58 | +6.79 [+3.61, +9.96], 4.54 |
| 1990-11 to 2025-12 | 21.51 | 26.7 | -64.8 | 4.7 y | +11.06 [+6.12, +15.99], 7.05 | +8.58 [+4.02, +13.14], 6.52 |

Both `exploratory` by the falsifier, both leverage in the sense of section 2: 1.65 units of
equity and 1.35 of a 20-year Treasury, 3.0x gross. The Treasury leg alone at 3x compounded at
5.15 percent over the century and 10.24 since 1990, which is the 1981-2020 bond bull market
Experiment 018 showed to be the whole of a stacked Treasury leg's contribution
([defensive engines](defensive-engines-in-the-construction.md)). Outside it: **-51.6 percent
across 1972-12 to 1981-09 while the index made +59.8**, -93 percent in 1929-32, -47 percent in
2022 (-52 peak to trough) when both legs fell together, and since 2020-08 +76 against the
index's +122. The construction has no brake: its 2000-02 and 2008-09 drawdowns are -52 and
-65 peak to trough. The Treasury leg is reset monthly rather than daily because no daily
bond series exists here, which omits an intra-month reset drag of the order of a point a
year on that leg; the reading does not turn on it.

---

## 6. Deflation

Declared family: lookbacks of 20 to 300 days, band 0 and 1 percent, 2x and 3x; 28 rules on
25,972 common days, each scored as its beta-matched active return. Trial Sharpe dispersion
0.0031 a day; mean off-diagonal correlation of the active returns 0.739; **8.05 effective
independent trials**. The best member is the 250-day rule on 3x with the band, which is one
reason to distrust the count: the true search over daily US equity history is far larger than
28, so the count is a lower bound and every significance below an upper bound.

| candidate | active Sharpe, annualised | N trials | SR\* | deflated significance |
| --- | ---: | ---: | ---: | ---: |
| 200-day on 3x | 0.159 | 8.05 | 0.074 | 0.80 |
| | | 14.8 | 0.090 | 0.75 |
| | | 100 | 0.129 | 0.62 |
| | | 10,000 | 0.196 | 0.35 |
| 200-day on 2x | 0.149 | 8.05 | 0.074 | 0.77 |
| | | 10,000 | 0.196 | 0.32 |
| best in grid, 250-day on 3x with band | 0.199 | 8.05 | 0.074 | 0.89 |

The daily panel gives the probabilistic Sharpe ratio 26,000 observations, which is why these
read higher than the monthly page's 0.33; none reaches 0.95 at any count, and the effective
count's linear interpolation carries the `UNVERIFIED` marker the earlier page recorded.

---

## 7. After tax, 1990-11 to 2026-06

Realised path, average-cost basis, a holding-period boundary at 252 trading days, loss
carryforwards against later capital gains only, tax paid out of the account, dividend yield
0.5 percent on the levered funds and 1.75 on the index. Growth is annualised log growth of
one dollar; the tax cost of an arm is the widening of its shortfall against the unlevered index
between the sheltered and the taxable account.

| arm | sheltered growth | top bracket, step-up | top bracket, liquidate | upper-middle, step-up | **tax cost, top step-up** |
| --- | ---: | ---: | ---: | ---: | ---: |
| rule on 3x | 16.87 | 13.20 | 12.93 | 14.65 | **3.25** |
| rule on 2x | 13.18 | 10.10 | 9.90 | 11.31 | **2.67** |
| rule on 1x | 8.74 | 6.51 | 6.40 | 7.38 | **1.82** |
| hold 3x | 16.61 | 16.49 | 15.74 | 16.53 | -0.30 |
| hold 1x | 11.12 | 10.71 | 10.05 | 10.86 | 0.00 |

The 1x figure reproduces the monthly page's 1.92 at daily resolution. At 3x the rule realises
its whole position about three times a year, pays 32.8 dollars of tax per dollar invested over
36 years under a step-up against the held fund's 1.8, and in the taxable account **the held 3x
fund out-grows the timed one by 3.3 pp/yr** while drawing down 98 percent. The rule's only
defensible home is a sheltered third, where its sheltered growth at 3x is 0.26 pp/yr above the
held fund's with a 65 point rather than 98 point drawdown.

---

## 8. Against the financed trend overlay already held

The published construction holds 30 points of an RSST-like wrapper: 1.02 units of equity plus
0.30 of a diversified trend book, 1.32x gross. On 96 years it beats the cheap index by **+1.98
pp/yr [+1.26, +2.73] against a 1.06 floor**, +1.84 from 1990-11 against 1.78, and it changes
the maximum drawdown by under one point (-82.8 against -83.7); its whole defensive value is
conditional, about +9.5 pp/yr through the 1999-2009 flat decade
([the recommendation](portfolio-recommendation.md),
[defensive engines](defensive-engines-in-the-construction.md)). The overlay therefore buys the
**mean**, at a resolution the design can see, and buys almost no unconditional drawdown. The
200-day rule on a levered fund buys the **drawdown**, 30 to 55 points off a slow bear market
at the same leverage, and buys a mean that is +4.79 pp/yr inside an 8.41 floor on the century
and negative since 1990. The prices differ too: the overlay costs 99 bp of fee and 20 bp of
basis on 30 points of capital, about 35 bp of portfolio, with 0.32 pp/yr of distribution drag;
the rule on 3x costs 89 bp of fee plus 80 bp of spread on the whole line, three round trips a
year and 3.2 pp/yr of tax if taxable. They overlap: the rule applies a 200-day trend signal,
long only, to one market of the roughly fifty the trend leg trades long and short, and the
monthly page measured the rule's active return correlating with the overlay's equity leg at
0.36 to 0.57, with negative alpha once the leg is held. The rule is a concentrated, long-only, sold-not-financed dose of a
signal the portfolio already holds in a broader and cheaper form, whose one distinct
contribution is a slow-crash brake on equity leverage the portfolio does not otherwise carry.

---

## 9. The decision

**Nothing on this page enters the vector.** The published RSST 30 / VTI 19 / VTV 15 / VXUS
16 / AVDV 10 / IDMO 5 / AVES 5 stands.

| construction | taxable third | traditional or Roth third |
| --- | --- | --- |
| HFEA | no; 1.35 units of 20-year duration financed at 3x is the 2022 and 1972-81 loss with no brake | no; the mean is the bond bull market and Experiment 018 already declined the stacked Treasury leg at 20 points |
| rule on 3x | no; 3.2 pp/yr of tax | no; -84.6 percent in 1933-35 and -67 in October 1987 at a timing content of +4.8 inside 8.4 |
| rule on 2x | no; 2.7 pp/yr of tax | **conditional**: an investor whose stated purpose is equity leverage with a slow-crash brake, who holds no other levered equity, can hold at most 10 to 15 points, inside the 15 to 25 point notional band and displacing wrapper capital rather than adding to it |
| rule on 1x | no | no; the monthly page's verdict stands, now at daily resolution |

The conditional row is a holdability argument and not a return argument. At 2x the rule's
CAGR since 1990 is 14.07 against the continuous 1.3x control's 13.65 with a 47.5 rather than
65.9 point drawdown, at zero measurable timing content, 3 round trips a year and 17.3 years
behind that control since 2009. An investor who wants that trade is buying a brake and paying
for it in whipsaws; the investor's own condition, *"we have to have confidence and
understanding in them"*, is met only if the 1933-35 and 1998-2002 relative runs are read
first. The default for this investor, who already holds 30 points of a broader version of the
same signal, is none.

---

## Verified, interpretation, open

**Verified.** Daily-reset compounding, per-calendar-day accrual, the hysteresis signal, the
one-day lag, the switch cost, the exposure-matched identity, the quarterly rebalance and the
episode arithmetic are pinned by hand-computed fixtures in the test file, including a
perturbation test that moves a later close and asserts no earlier position changes. The
daily file compounds to the monthly file's returns to within 5 bp a month at four checked
months. All three source hashes match their committed manifests. Every figure above is in the
run artifact.

**Interpretation.** That the exposure-matched control is the one that answers the question
and the other two measure leverage; that October 1987 and 1933-35 are the rule's
characteristic failures rather than accidents of one path; that the sheltered 2x row is
defensible at all. The fee, spread and cost figures are declared, not measured: SSO's stated
ratio, an 80 bp stress on a spread no issuer publishes, and 10 bp a switch. The signal index is
the total-return index, which biases the signal toward the market by roughly the dividend
yield over half the window; the price-proxy sensitivity moves the 3x timing content from
+4.79 to +6.94, inside the floor.

**Open.**

1. **The rule's drawdown benefit is measured on one path and never deflated**; the two
   statistics the investor cares about most, 1929-32 and 2008-09 at 3x, are one observation
   each.
2. **No daily bond series**, so HFEA's Treasury leg is reset monthly and the intra-month drag
   is stated rather than modelled. A daily Treasury total-return series would close it.
3. **Whether any lookback other than 200 days is different.** The grid says the best of 28 is
   the 250-day band rule at a deflated 0.89, which is a reason to expect that a search would
   find one that clears 0.95 in sample and a reason to distrust it if it did.
4. **The rule's loading on the wrapper actually held** rather than on a vendor index, which
   is the monthly page's open question 4 and applies here unchanged.
