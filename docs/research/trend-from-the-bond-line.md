# Engines on the bond line of the cautious portfolio

**Question.** The published cautious portfolio (SCHP 50 / RSST 15 / stocks 35, [decision
0014](../decisions/0014-cautious-constructions-are-labelled-by-the-history-they-held.md))
holds half its capital in a ten-year Treasury line whose worst measured episode is 1977–81.
Every trend test in this repository funded trend from stocks. Does funding trend from the
bond line instead, stacked (an RSBT-like wrapper, bond kept) or sold (a standalone trend
fund, bond given up), improve the cautious portfolio as a whole? And does a gold stack on
its stock line (GDE-like) do the same?

**Decision it informs.** Whether the published cautious vector changes, whether an engine on
its bond line is offered beside it as the reader's option, or whether 0014 stands.

**Out of scope.** The choice between RSST and RSBT as the carrier of the existing 15-point
trend line (arithmetic, not a measurement: the two wrappers' costs differ by about 1 bp/yr
of the portfolio); carry on the bond line; TIPS before 2003; taxes and placement; any
weight search.

`as of 2026-09-05`. **`exploratory`.**
[Experiment 026](../../research/experiments/exp_026_trend_from_the_bond_line.yaml), spec
`dd8de1bd…`, run
[`feeae9c7…`](../../research/artifacts/feeae9c7b5f44466a44ca5828384a166/summary.md), with
the per-panel tables in
[`tables.md`](../../research/artifacts/feeae9c7b5f44466a44ca5828384a166/tables.md). The
specification was frozen before any module existed and predicted every headline figure
from the closed form `X × (trend premium − cost)` on 025's realised premia: RSBT-stacked
+0.62 / +1.23 / +1.85 pp/yr at 10 / 20 / 30 points (observed +0.61 / +1.23 / +1.84), the
sold-from-bonds arm marginal (observed `exploratory` by 0.1 to 0.3 pp/yr over its floor), the
gold arms `unresolved` at every size (observed so), and the forward reading inside its floor
at every size by construction (observed so). 025's `ladder40` reproduced to four places on
both panels and 016f's rec30-minus-rec25 pair to four places before any candidate was scored.

## 1. Conclusion

Trend funded from the bond line adds to the cautious portfolio at realised premia, on both
histories, at every size tested, and costs nothing in worst fall. It is the sum the funding
rule predicts, `X × (7.22 − 1.07)` on 96 years, and it is made entirely before 2009, where
every prior trend result was also made. At the repository's central forward trend premium
(4.07 pp/yr gross) the same arithmetic gives +0.30 / +0.60 / +0.90 pp/yr for 10 / 20 / 30
points against floors of 0.35 / 0.71 / 1.06: inside the floor at every size, in the ratio
0.85 that does not depend on X. **The published cautious vector should not change.** Under
the rule frozen before the run, the RSBT-stacked line is offered beside it as the reader's
option with its regret row, the treatment 0014 clause 2 gives the plain twins; that is
[draft decision 0015](../decisions/0015-an-engine-on-the-bond-line-is-the-readers-option.md),
PROPOSED and not adopted. Gold on the stock line is `unresolved` everywhere and reads as a
1970s story.

## 2. Design

The reference arm `cautious` is the published construction in capital weights on 025's
primary panel (CORE 0.35 / RSST-like 0.15 / ten-year 0.50: equity 0.511, trend 0.15, bond
0.50, gross 1.16) and the published fund weights exactly on the tournament panel. Nine
candidates differ from it by one engine on one line, at 10, 20 and 30 points:

- `rsbtX`: X of the ten-year line becomes an RSBT-like wrapper, 1.0 of the *same* ten-year
  plus 1.0 trend, financed at the 15 bp Treasury basis, at 97 bp. Bond notional unchanged;
  trend rises to 0.15 + X. Funding rule: on top.
- `trendfundX`: X of the ten-year line becomes an unlevered trend fund, 1.0 trend at 85 bp.
  Bond falls to 0.50 − X. Funding rule: sold from bonds.
- `gdeX`: 0.9 X of the stock line and 0.1 X of the bond line become a GDE-like wrapper, 0.9
  equity plus 0.9 gold financed at an assumed 30 bp, at 20 bp. Equity unchanged; gold 0.9 X.

Panels: 1929-01…2025-05 (1,157 months, own 4-asset trend book, modelled nominal ten-year,
monthly rebalancing) for the trend arms; 1968-05…2025-05 (685 months, LBMA gold added) for
the gold arms with every trend arm re-run beside them; 016f's fund-list panel 1990-11…2026-05
(427 months, AQR TSMOM, LBMA gold, annual rebalancing) for all nine. Controls, four
families never added: the cautious portfolio itself (the primary comparison), the cheap
100%-equity index, a cheap 60/40, and the equity core levered or scaled to each arm's gross.
Nine crisis episodes; financing swept 62–231 bp equity, 0–50 bp Treasury, 0–60 bp gold.

## 3. What each arm did, on both histories

Arithmetic gap against `cautious`, pp/yr, bootstrap 95%, floor at 80% power; worst fall
with `cautious`'s beside it; the two decision episodes on the primary panel
([tables](../../research/artifacts/feeae9c7b5f44466a44ca5828384a166/tables.md)):

| arm | 1929–2025 gap | 95% | floor | 1990–2026 gap | 95% | floor | worst fall 1929– / 1990– (cautious −54.0 / −18.1) | 1977–81 (cautious +35.9) | 2022 Jan–Sep (cautious −19.3) | freeze note 6 |
| --- | ---: | :---: | ---: | ---: | :---: | ---: | --- | ---: | ---: | --- |
| `rsbt10` | +0.61 | [+0.37, +0.86] | 0.35 | +0.99 | [+0.54, +1.44] | 0.61 | −52.6 / −15.6 | +44.8 | −18.7 | (b) option |
| `rsbt20` | +1.23 | [+0.75, +1.72] | 0.71 | +1.97 | [+1.07, +2.87] | 1.20 | −51.3 / −13.2 | +54.1 | −18.0 | (b) option |
| `rsbt30` | +1.84 | [+1.12, +2.58] | 1.06 | +2.95 | [+1.61, +4.27] | 1.79 | −49.9 / −12.0 | +63.9 | −17.4 | (b) option |
| `trendfund10` | +0.48 | [+0.22, +0.75] | 0.39 | +0.74 | [+0.32, +1.17] | 0.62 | −52.8 / −17.2 | +52.0 | −17.2 | (b) option |
| `trendfund20` | +0.96 | [+0.44, +1.51] | 0.78 | +1.48 | [+0.65, +2.32] | 1.23 | −51.5 / −16.4 | +69.6 | −15.1 | (b) option |
| `trendfund30` | +1.44 | [+0.66, +2.26] | 1.18 | +2.22 | [+0.97, +3.47] | 1.83 | −50.2 / −15.5 | +88.8 | −12.9 | (b) option |
| `gde10` (1968–) | +0.40 | [−0.14, +0.98] | 0.64 | +0.52 | [+0.04, +1.02] | 0.65 | −19.8 / −17.3 (cautious −19.3 / −18.1) | +47.9 | −19.8 | (c) stands |
| `gde20` (1968–) | +0.81 | [−0.29, +1.96] | 1.28 | +1.03 | [+0.09, +2.03] | 1.29 | −20.4 / −17.3 | +60.4 | −20.2 | (c) stands |
| `gde30` (1968–) | +1.21 | [−0.43, +2.94] | 1.92 | +1.54 | [+0.14, +3.02] | 1.92 | −21.9 / −17.8 | +73.2 | −20.7 | (c) stands |

Every trend arm is `exploratory` against the cautious portfolio on both panels; every gold
arm is `unresolved` on both. All nine keep their sign across every financing band. Log-growth
gaps trail the arithmetic gaps by 0.02 to 0.15 pp/yr (the variance the stacked arms add).

## 4. The trend arms: where the sum was made

The pair is a pure sum and the sub-windows show it
([tables](../../research/artifacts/feeae9c7b5f44466a44ca5828384a166/tables.md), "Sub-window
gaps against reference"):

- **Before 1981-10** (633 months, ten-year 0.04 pp/yr over cash, trend 8.03): `rsbt`
  +0.70 / +1.39 / +2.09 against floors 0.47 / 0.94 / 1.41; `trendfund` +0.72 / +1.44 / +2.16
  against 0.54 / 1.08 / 1.62. The whole result lives here.
- **The bond bull market, 1981-10…2020-07** (ten-year 4.75): `rsbt` +0.60 / +1.20 / +1.80
  against floors 0.58 / 1.17 / 1.75, on the line; `trendfund` +0.15 / +0.30 / +0.45 against
  0.61 / 1.22 / 1.84, inside, because the bond it sold earned 4.75 over cash.
- **Since 2009** (own book 1.41): `rsbt` +0.03 / +0.07 / +0.10, `trendfund` +0.01 / +0.02 /
  +0.03, against floors of 0.74 to 2.4. Nothing. On the tournament panel since 2009, +0.19 to
  +0.60 against floors of 0.9 to 3.0.
- **Since 2020-08** (ten-year −6.54, trend −0.39): `rsbt` −0.15 / −0.29 / −0.44, `trendfund`
  +0.53 / +1.07 / +1.60, both inside floors of 1.1 to 4.7. The sold arm won 2022 because it
  did not hold the bond; the stacked arm paid its fee on a trend book that was flat.

The two funding rules differ exactly as the mechanism says. The stacked arm's hurdle is its
cost, 1.07 pp/yr per unit; the sold arm's hurdle is 0.80 plus the bond's excess over cash,
1.61 realised, 0.8 forward. On 96 years the stacked arm won by 0.13 / 0.27 / 0.40 pp/yr more;
in the bond bull market by 0.45 / 0.90 / 1.35 more; after 2020 it lost by 0.7 / 1.4 / 2.0.
The one earlier substitution test from *equity* (019, 50/50 RSST/RSSY) read −0.13; the
substitution from *bonds* here reads +0.48 to +1.44. That difference is the equity premium
over the term premium and is the reason this experiment was run.

## 5. Drawdown and the inflation episodes

Descriptive; one path each. Worst fall in percent, months under water in brackets, difference
against `cautious` in points (positive is shallower):

| window | `cautious` | `rsbt10` | `rsbt20` | `rsbt30` | `trendfund10` | `trendfund20` | `trendfund30` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1929–2025 | −54.0 (74) | −52.6 (73) +1.4 | −51.3 (70) +2.8 | −49.9 (70) +4.2 | −52.8 (73) +1.3 | −51.5 (73) +2.6 | −50.2 (72) +3.8 |
| from 1934 | −26.8 (39) | −26.9 (33) −0.1 | −27.0 (33) −0.2 | −27.1 (33) −0.3 | −27.2 (36) −0.4 | −27.6 (36) −0.7 | −27.9 (36) −1.1 |
| from 1946 | −19.3 (39) | −18.7 (32) +0.6 | −18.0 (31) +1.3 | −18.0 (27) +1.3 | −17.3 (32) +2.0 | −17.4 (32) +1.9 | −18.1 (31) +1.2 |
| 1990–2026 (fund panel) | −18.1 (26) | −15.6 (27) +2.5 | −13.2 (27) +4.9 | −12.0 (22) +6.1 | −17.2 (27) +0.9 | −16.4 (24) +1.7 | −15.5 (24) +2.6 |

The stacked arm never falls deeper than the cautious portfolio by more than 0.3 points on
any window and falls 1.4 to 6.1 points less on the two full panels; the sold arm is 0.4 to
1.1 points deeper from 1934 (the bond it gave up was the 1937 and 1974 cushion) and
shallower elsewhere. The 1929–32 fall is 50 to 53% for every trend arm: nothing here changes
0014 clause 4.

Episodes, cumulative return in percent, primary panel:

| episode | `cautious` | `rsbt10` | `rsbt20` | `rsbt30` | `trendfund10` | `trendfund20` | `trendfund30` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1929-09…1932-06 | −54.0 | −52.6 | −51.3 | −49.8 | −52.8 | −51.5 | −50.2 |
| 1937-03…1938-03 | −26.8 | −26.9 | −27.0 | −27.1 | −27.2 | −27.6 | −27.9 |
| 1973-01…1974-09 | −18.3 | −12.1 | −5.6 | +1.4 | −11.0 | −3.1 | +5.3 |
| 1977-01…1981-09 | +35.9 | +44.8 | +54.1 | +63.9 | +52.0 | +69.6 | +88.8 |
| 2000-09…2002-09 | −11.3 | −8.8 | −6.3 | −3.8 | −10.5 | −9.7 | −9.0 |
| 2007-11…2009-02 | −18.6 | −16.0 | −13.3 | −10.7 | −17.3 | −16.1 | −14.9 |
| 2020-02…2020-03 | −5.3 | −4.6 | −3.9 | −3.1 | −5.4 | −5.5 | −5.6 |
| 2022-01…2022-09 | −19.3 | −18.7 | −18.0 | −17.4 | −17.2 | −15.1 | −12.9 |
| 2022 calendar | −16.5 | −16.0 | −15.5 | −15.0 | −14.4 | −12.3 | −10.1 |

The 1977–81 episode was the cautious portfolio's worst against the published 30%
construction (+36% against +86%). Thirty points of trend sold from the bond line closes that
gap entirely (+88.8%); thirty points stacked closes most of it (+63.9%). 2022 moves by 0.6
to 6.4 points; nothing here turns 2022 positive, because the bond line is 20 to 50 points
of a nominal ten-year in every arm. On the fund-list panel the same order holds: 2008 −10.3%
for `rsbt30` against −18.1%, 2022 Jan–Sep −7.7% (`rsbt30`) and −2.0% (`trendfund30`) against
−16.1%.

## 6. The gold arms

On 1968-05…2025-05 gold earned 5.18 pp/yr over cash at 0.016 correlation to equity, 14.5
pp/yr before 1981-10 and 1.49 in the bond bull market. Stacked on the stock line at 9 / 18 /
27 points of gold the arm reads +0.40 / +0.81 / +1.21 pp/yr against floors of 0.64 / 1.28 /
1.92, `unresolved`, and the same on the fund-list panel (+0.52 / +1.03 / +1.54 against 0.65 /
1.29 / 1.92). It adds 12 to 37 points across 1977–81 and 6 to 20 across 1973–74; it is 0.5 to
1.4 points *worse* in 2022 and falls 0.5 to 2.6 points deeper on the 1968 window (gold did
not offset the 2022 bond loss, and 1980–82 took 60% off the gold price). At the 0.0 gold
premium the repository treats as central the closed form is the cost, −0.05 / −0.10 / −0.16
pp/yr; the break-even gold excess is 0.58 pp/yr. This is 018's `trend30_goldstack10` reading
(+0.35 against 0.64) at three sizes inside a bond-heavy book: a 1970s story with no
resolvable mean and no forward premium estimate to price it at.

## 7. The price at forward premia

Closed form, candidate minus `cautious`, arithmetic pp/yr; the log cell subtracts 0.02 to
0.11 of variance drag
([tables](../../research/artifacts/feeae9c7b5f44466a44ca5828384a166/tables.md), "Regret at
forward premia"):

| gross trend premium pp/yr | `rsbt10` | `rsbt20` | `rsbt30` | `trendfund10` (λ = 1 / 0.671) | `trendfund20` | `trendfund30` |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1.74 | +0.07 | +0.13 | +0.20 | +0.01 / −0.04 | +0.03 / −0.09 | +0.04 / −0.13 |
| 3.90 | +0.28 | +0.57 | +0.85 | +0.23 / +0.10 | +0.46 / +0.20 | +0.69 / +0.31 |
| **4.07 (central)** | **+0.30** | **+0.60** | **+0.90** | **+0.25 / +0.11** | **+0.49 / +0.23** | **+0.74 / +0.34** |
| 5.32 | +0.43 | +0.85 | +1.28 | +0.37 / +0.20 | +0.74 / +0.39 | +1.12 / +0.59 |
| 7.18 | +0.61 | +1.22 | +1.83 | +0.56 / +0.32 | +1.12 / +0.64 | +1.67 / +0.97 |
| floor (1929–2025) | 0.35 | 0.71 | 1.06 | 0.39 | 0.78 | 1.18 |
| break-even premium | 1.07 | 1.07 | 1.07 | 1.60 / 2.39 | 1.60 / 2.39 | 1.60 / 2.39 |

The stacked line clears its own floor above about 4.6 pp/yr of gross trend premium, at any
size; the repository's central 4.07 is below that and its 5.32 row (the realised own-book
premium less a 20 bp one-way trading cost) is above it. A reader who believes the century
believes the option; a reader who believes the trend-weight page's weighted range does not
get a resolvable answer. That is the same position the existing 15-point RSST line is in,
and it is why freeze note 6 (a4) fails for every arm and (b) applies.

## 8. What the result licenses, and what it does not

Freeze note 6 read mechanically
([diagnostics](../../research/artifacts/feeae9c7b5f44466a44ca5828384a166/summary.md),
`freeze_note_6_reading`): every trend arm meets (a1) `exploratory` on both panels, (a2) not
deeper than the cautious portfolio by more than 2 points on any read window, and (a3) not
below it in 1977–81 or 2022 Jan–Sep; every trend arm fails (a4), the forward gap above its own
floor. Outcome **(b)** for all six: PROPOSED as a printed option beside the published
cautious vector, the vector unchanged. Every gold arm fails (a1) and (a3) and `gde30` fails
(a2): outcome **(c)**, 0014 stands.

Which option to print, if the site owner accepts 0015: the stacked line rather than the sold
one, because it keeps the bond's deflation cushion (flat from 1934 where the sold arm is
deeper), because its break-even does not depend on an unlevered fund's delivered loading
(1.07 against 1.60 at full loading and 2.39 at DBMF's measured 0.671), and because it fell
less on every window. At 10 points, not 30: the ratio of forward gap to floor is the same at
every size, so size buys nothing in resolution, while gross notional rises from 1.16 to 1.46
and a third stacked wrapper's fee, closure risk and ordinary-income distribution rise with it.
The plain twin from 025 remains the other option in the other direction.

What the result does not license: any change to the vector; any claim that RSBT the fund
delivers this (its 2023–26 record is −0.38%/yr against the Agg's +3.16% until the trailing
year); any reading of the trend arms as evidence about the trend premium, which they take as
an input; any claim about 2022, which every arm lost.

## 9. Scope and limits

- Constructions on public series, not funds: the RSBT-like wrapper is an assumed 1.0
  ten-year plus 1.0 trend at 97 bp plus 15 bp; the trend fund an assumed 1.0 trend at 85 bp;
  the GDE-like wrapper 018's 0.9 / 0.9 at 20 bp plus an assumed 30 bp gold basis, swept.
- The bond line is a nominal ten-year on every panel; at 47 to 50 points the 1973–74 and
  1977–81 figures overstate what a TIPS book would have lost, for the cautious portfolio and
  for every arm alike.
- The trend book is charged no trading (the 5.32 row approximates it); TSMOM is gross of the
  vendor's costs. The gold sub-window includes 1971–74.
- The pairs are sums by construction; their sub-window pattern is the trend premium's, and
  since 2009 the instrument cannot see them.
- Drawdown, months under water, episodes and terminal wealth are one order statistic of one
  path. No tax; the wrappers distribute ordinary income and belong in the sheltered third
  the cautious page already sends the bond line to.
- The arms were chosen after 018, 024, 025 and the candidates note were read;
  `run_kind: exploratory` records that.

## 10. What would change this

A registered forward trend premium above about 4.6 pp/yr gross would move the stacked line
from (b) to (a) at every size. A gold forward premium estimate, or a gold series before
1968, would let the gold arms be priced rather than described. A delivered loading above 0.9
at 85 bp would bring the sold arm's break-even to the stacked arm's. A post-2009 window long
enough to resolve 0.3 pp/yr at 1.2 points of tracking error is about a century away, as it
was for the RSST line.
