# Cautious constructions scored as objects

**Question.** The site tells a reader who could not sit through a fall of about 30% or
40% to hold fewer stocks and more bonds, and names no construction. What does a bond-heavy
book built from the same funds plus an unlevered ten-year Treasury (the TIPS proxy) draw
down on each history the repository holds, what does it cost against the cheap index and
against the published 30% construction, and does an 11 to 15 point financed trend line on
top of it help at matched equity?

**Decision it informs.** Which construction, if any, the site may publish for a stated
tolerance of about −30% or −40%; whether that construction carries the trend line; and
what the reader gives up for the shallower fall.

**Out of scope.** The equity share for a withdrawing investor
([equity share](setting-the-equity-share.md) §5.1), duration beyond one sensitivity arm,
TIPS before 2003 (no series exists), account placement of a 50 to 63 point bond line
([portfolio for one investor](portfolio-for-one-investor.md) §7), and any weight search.

`as of 2026-09-03`. **`exploratory`.**
[Experiment 025](../../research/experiments/exp_025_cautious_constructions.yaml), spec
`929937d2…`, run
[`00c0b8b0…`](../../research/artifacts/00c0b8b0b1894993afdc07236e402451/summary.md), with
the per-panel tables in
[`tables.md`](../../research/artifacts/00c0b8b0b1894993afdc07236e402451/tables.md). The
specification was frozen before any module existed and predicted, before the run, that no
construction on the 96-year panel would hold a −30% worst fall with more than about 35
points of equity, that the three primary pairs would read `exploratory` at realised premia
and inside their floors since 2009, and that every cautious arm would be `rejected` on the
mean against the cheap 100%-equity control. All three predictions held. 016f's
rec30-minus-rec25 log gap reproduced to four places (0.5101) before any cautious arm was
scored, and the trend-book scalar reproduced 018's 1.9771.

## 1. Design

Ten arms in capital weights on 024's primary panel (1929-01…2025-05, 1,157 months, US
equity, the repository's own 4-asset trend book at 12.38% volatility, a modelled ten-year
par bond on FRED GS10 spliced to Shiller's long rate, monthly rebalancing, every cost inside
the rule): two plain mixes (`plain60_40`, `plain40_60`), two trend arms at the same equity
(`trend15_eq60`: RSST-like 15 / core 44 / ten-year 41; `trend11_eq40`: 11 / 28 / 61), the
notional ladder's CAPE-conditioned −40% and −30% rows applied whole (`ladder40`: 14.9 / 34.8
/ 50.3, equity 0.508; `ladder30`: 11.0 / 25.8 / 63.2, equity 0.376) each with a plain twin
at matched equity, a 20-year-bond sensitivity, and the published 30% construction as the
reference. The same arms run on 016f's 427-month fund-list panel (1990-11…2026-05, AQR
TSMOM, annual rebalancing) with the tilt book VTI 19 / VTV 15 / VXUS 16 / AVDV 10 / IDMO 5 /
AVES 5 scaled whole to each arm's unlevered equity, plus a cheap untilted 60/40 as a second
control. A check panel from 2003-02 runs every arm twice, with the nominal ten-year and with
018's modelled TIPS leg. Six controls are six families and are never added. The three
primary comparisons are trend arm minus plain twin.

## 2. What fell how far

Drawdown is the reason the file exists and carries no status. Worst fall in percent, months
under water in brackets, each window started fresh
([tables](../../research/artifacts/00c0b8b0b1894993afdc07236e402451/tables.md) "Drawdown by
era"):

| arm | equity | 1929–2025 | from 1934 | from 1963-07 | 1990-11–2025 (US legs) | 1990-11–2026 (fund panel) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cheap 100% equity / cheap 65/35 | 1.00 | −83.7 (184) | −50.3 (74) | −50.3 (73) | −50.3 (73) | −52.7 (63) |
| `published_trend30` | 1.02 | −82.8 (164) | −50.3 (74) | −45.9 (51) | −45.9 (51) | −49.7 (42) |
| `plain60_40` | 0.60 | −63.0 (82) | −31.4 (70) | −30.7 (40) | −28.4 (40) | −28.3 (37) |
| `trend15_eq60` | 0.60 | −61.3 (76) | −31.5 (70) | −24.8 (37) | −24.8 (37) | −24.9 (31) |
| `ladder40` | 0.51 | −53.8 (74) | −26.7 (39) | −19.3 (32) | −19.3 (32) | −18.1 (26) |
| `ladder40_plain` | 0.51 | −55.8 (76) | −26.6 (39) | −26.5 (38) | −22.3 (38) | −21.6 (31) |
| `plain40_60` | 0.40 | −46.0 (73) | −21.4 (38) | −21.4 (36) | −19.0 (32) | −18.5 (32) |
| `trend11_eq40` | 0.40 | −44.0 (70) | −20.7 (31) | −18.4 (31) | −18.4 (31) | −16.0 (31) |
| `ladder30` | 0.38 | −41.7 (69) | −19.5 (31) | −18.2 (31) | −18.2 (31) | −15.8 (31) |
| `ladder30_plain` | 0.38 | −43.6 (71) | −20.2 (38) | −20.2 (36) | −18.8 (31) | −18.4 (32) |

Three readings. First, the 1963-07 window reproduces the equity-share table
([equity share](setting-the-equity-share.md) §5): 60/40 −30.7% against the table's −30.6%,
40/60 −21.4% against −21.3%, so the two pages are one measurement. Second, **no
construction holds a −30% worst fall across 1929–32**, as predicted: the shallowest arm on
96 years is `ladder30` at −41.7%, with 38 points of equity. A 60/40 fell 63%. Every
"−30%" claim on this site is therefore a claim about 1934 onward, and freeze note 6 says the
96-year figure travels in the same sentence. Third, the trend arm fell less than its plain
twin on every panel and every era but the two from-1934 cells where the pairs sit within
0.1 point of each other, by 0.1 to 7 points elsewhere; the ladder's "one to three points of equity at the same drawdown" is
reproduced as a construction property.

## 3. The primary pairs: the trend line at matched equity

Arithmetic mean gap, trend arm minus plain twin, pp/yr, bootstrap 95%, floor at 80% power,
1929–2025:

| pair | gap | 95% | floor | log gap | since 2009 | status |
| --- | ---: | :---: | ---: | ---: | ---: | --- |
| `trend15_eq60` − `plain60_40` | +0.93 | [+0.56, +1.29] | 0.53 | +0.92 | +0.05 vs 1.11 | `exploratory` |
| `ladder40` − `ladder40_plain` | +0.92 | [+0.54, +1.27] | 0.53 | +0.91 | +0.04 vs 1.10 | `exploratory` |
| `ladder30` − `ladder30_plain` | +0.68 | [+0.40, +0.94] | 0.39 | +0.67 | +0.03 vs 0.81 | `exploratory` |

Positive in every declared era before 2009 (from 1934, 1946, 1963, 1970, 1990-11, the
bond bull market and its complement); not resolvable since 2009 and slightly negative
since 2020-08 (−0.22 to −0.31 against floors of 1.2 to 1.7). On the fund-list panel at AQR
TSMOM's realised premium the same pairs read +1.70, +1.69 and +1.25 against floors of about
1.0 and 0.75, `exploratory`. The sign survives every point of the 62–231 bp financing band.
At the 4.07 pp/yr forward trend premium the closed form gives +0.43 (15 points) and +0.32
(11 points); the break-even gross trend premium is about 1.2 pp/yr at any equity premium.
This is 018's overlay result at a third to a half of the weight: the trend line adds as a
sum because it is financed, and its whole measured contribution predates 2009.

## 4. The price of the drawdown

Against the cheap 100%-equity control on 96 years, every cautious arm is `rejected` on the
mean, by −1.5 (`trend15_eq60`) to −3.9 (`ladder30_plain`) pp/yr arithmetic and −0.5 to
−2.4 pp/yr of log growth. Against the published 30% construction, −3.5 to −5.8. On the
fund-list panel against the cheap 65/35, −0.25 (`trend15_eq60`) to −3.4; against a cheap
untilted 60/40, the 60-equity trend arm reads +2.04 [+1.20, +2.87] vs 0.98 and `ladder40`
+1.43 vs 1.27, both `exploratory`, while the plain arms are inside their floors. Against a
volatility-matched equity-plus-bills control every plain arm is +0.4 to +0.6 inside a 0.6
to 1.0 floor (`unresolved`) and every trend arm +1.2 to +1.4, `exploratory`: the bond line's
term premium and diversification are not separable from the equity share on this panel, the
trend line is.

At forward premia the price is the equity premium over bonds times the equity the arm gives
up. Plain arm minus 100% stocks, pp/yr, arithmetic / log growth
([tables](../../research/artifacts/00c0b8b0b1894993afdc07236e402451/tables.md) "The price
of the drawdown"):

| arm | equity | E = 0 | E = 1.5 | E = 3 | E = 5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `plain60_40` | 0.60 | −0.01 / +1.04 | −0.61 / +0.44 | −1.21 / −0.16 | −2.01 / −0.96 |
| `ladder40_plain` | 0.51 | −0.01 / +1.20 | −0.75 / +0.46 | −1.49 / −0.28 | −2.47 / −1.26 |
| `plain40_60` | 0.40 | −0.01 / +1.35 | −0.91 / +0.45 | −1.81 / −0.45 | −3.01 / −1.65 |
| `ladder30_plain` | 0.38 | −0.01 / +1.38 | −0.95 / +0.44 | −1.88 / −0.50 | −3.13 / −1.75 |

At the 0 to 1.5 pp/yr equity premium over TIPS that four of six managers' 2026 assumptions
imply ([valuation](valuation-and-the-allocation.md) §1.4), a 40/60 costs 0 to 0.9 pp/yr of
arithmetic return and gains 0.4 to 1.4 pp/yr of log growth from the variance it does not
carry; at 3 pp/yr it costs 1.8 arithmetic and 0.5 log; at the 96-year realised 7.75 it cost
3.7. The reader picks the row they believe, which is what decision 0012 clause 1(a) asks for.

## 5. Which bond

The check panel (2003-02…2025-05, 268 months) runs every arm with the nominal ten-year and
with 018's modelled TIPS leg. TIPS in the bond line earned +0.25 to +0.39 pp/yr more on
every arm, inside floors of 0.9 to 1.5, and fell 0.5 to 4.4 points deeper at the worst
(2013 and 2022), except `ladder30` where it fell 0.4 points less. In 2022 the TIPS version
lost about one point less on every arm (−16.9% against −18.2% for `ladder30`). Nothing in
this window separates the two; the case for TIPS is the contractual 2.44% real yield, not
this table. The 20-year bond in place of the ten-year (`plain60_40_ltbond`) adds +0.26
[+0.00, +0.53] against a 0.74 floor on 96 years, `unresolved`, all of it 1981–2020, and
draws down 0.8 points less on 96 years and 0.8 points more since 1990. The bond line's fee
matters less than any gap here: 3 bp instead of 5 on the largest line is +1.3 bp/yr, 18 bp
is −8.2.

The 1977–81 episode is where the nominal stand-in is weakest: the cautious arms returned
+16% to +42% across it against +86% for the published construction, 44 to 70 points behind,
and a TIPS book would have done better by an amount no series can measure. The 1973–74
episode shows the same direction at a third of the size.

## 6. What the publication rule licenses

Freeze note 6 publishes a construction for a tolerance only if some arm's worst fall lands
within 5 points of it on every scored panel. **No arm satisfies that clause for −30% or
−40%**: the 96-year panel puts every arm 12 to 33 points deeper than the modern panels do,
and the arms that hold −30% since 1934 hold −16% to −19% on the fund-list panel. The rule's
last clause is what applies: a construction may be labelled for the tolerance its 1990-11
panel fall supports, with the 96-year figure printed in the same sentence, and nothing deeper
than −45% on 96 years may be labelled for −30%.

Read mechanically ([diagnostics](../../research/artifacts/00c0b8b0b1894993afdc07236e402451/summary.md),
`publication_reading`):

- **For about −30%:** `ladder30` (RSST-like 11 / equity 25.8 / ten-year 63.2). Worst fall
  −18% on 1990–2026 on both panels, −19.5% from 1934, **−41.7% across 1929–32**. The only
  arms under the −45% line are `ladder30`, its plain twin and `trend11_eq40`. The trend line
  survives: its pair is `exploratory` and it fell less than the twin on every panel.
- **For about −40%:** `ladder40` (RSST-like 14.9 / equity 34.8 / ten-year 50.3). Worst fall
  −18% to −19% on 1990–2026, −26.7% from 1934, **−53.8% across 1929–32**. Trend line
  survives on the same two tests. The plain 60/40 and `trend15_eq60` are the looser
  reading: −25% to −28% on 1990–2026, −31% from 1934, −61% to −63% across 1929–32.
- **Neither may be labelled "for −30%" on the 96-year history.** A reader who takes 1929–32
  as live has no construction on this site with less than a 42% fall short of holding
  fewer than 38 points of equity, which the equity-share table's 30% row (−17.9% on
  1963–2025, unscored here) would be.

In fund weights, with the tilt book scaled and SCHP as the ten-year line (weighted fee from
`shelf.ts` fees, arithmetic, not a run):

| label | RSST | VTI | VTV | VXUS | AVDV | IDMO | AVES | SCHP | fee |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| for about −30% (`ladder30`) | 11 | 7.1 | 5.6 | 5.9 | 3.7 | 1.9 | 1.8 | 63 | ~16 bp |
| for about −40% (`ladder40`) | 15 | 9.6 | 7.5 | 8.0 | 5.0 | 2.5 | 2.5 | 50 | ~20 bp |

The bond line belongs in the traditional third first, then the Roth, and in taxable last,
and at 50 to 63 points it overflows every shelter an equal-thirds investor has; the
placement cost of that is priced on the page, not here.

## 7. Scope and limits

- Constructions on public series, not funds: RSST-like is an assumed 1.072 equity + 1.000
  trend vector at 99 bp; the trend book is a construction charged no trading cost; AQR's
  TSMOM is gross of the vendor's costs.
- The bond line is a nominal ten-year on both scored panels. At 40 to 63 points of capital
  the 1973–74 and 1977–81 losses overstate what a TIPS book would have lost; the 2003
  check panel is one era of correlation and separates nothing.
- Before 1953-04 the Shiller long rate is not a ten-year constant-maturity yield.
- The arms were chosen after the equity-share table, the ladder, 018 and 024 were read;
  `run_kind: exploratory` records that. No arm's weights were searched.
- Drawdown, months under water, crisis episodes, worst-decile offsets and terminal wealth
  are one order statistic of one path each.
- No tax; no withdrawals; the flat-decade and 2022 readings are the same single episodes
  every other page reads.

## 8. What would change this

A TIPS series before 2003 would replace the stand-in and re-read 1973–81. A supplied
tolerance replaces the label on the day it arrives (decision 0013 clause 5). A post-2009
window long enough to resolve a 0.3 to 0.4 pp/yr trend-line gap at 1.3 points of tracking
error needs about 100 years, so the trend line's forward reading stays the regret table.
The equity-share table's 30% row, scored as one object with the trend line, is the open
arm for a reader who takes 1929–32 as live. An engine funded from the bond line of the −40%
construction is scored in [trend from the bond line](trend-from-the-bond-line.md)
(Experiment 026): it clears its floor at realised premia and not at the forward premium, and
does not change the vector.
