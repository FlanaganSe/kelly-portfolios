# Carry as a second financed engine

**Question.** The recommended construction is 70% cheap equity core plus 30% of an
RSST-like stocks-plus-trend wrapper, and the stacking arithmetic says a second financed
engine earns its place only with a positive expected excess return and a low correlation
to what is already held. Is multi-asset futures carry, the engine inside the RSSY wrapper
(US stocks 100% plus "futures yield" 100%), that second engine, either stacked on top of
the trend overlay or substituted for half of it?

**Decision it informs.** Whether to add a 10- or 20-point RSSY-like line to the published
vector RSST 30 / VTI 19 / VTV 15 / VXUS 16 / AVDV 10 / IDMO 5 / AVES 5, or to split the
30-point wrapper between trend and carry, and where such a line could be held.

**Out of scope.** Whether the trend overlay itself earns its place
([defensive engines](defensive-engines-in-the-construction.md) §2,
[trend weight](trend-weight-under-uncertainty.md)); long/short commodity carry alone,
which [the sleeves audit](alternative-sleeves-audit.md) §8 rejected on overlap with trend
and which this page does not reopen; currency carry as a hedging decision
([currency](currency-and-the-international-sleeve.md)).

`as of 2026-09-02`. **`exploratory`.** [Experiment 019](../../research/experiments/exp_019_carry_engine.yaml),
spec `692359e3…`, run
[`fd023828…`](../../research/artifacts/fd023828337641fa8cfdbc44e1c5ffe3/summary.md), with
the per-panel tables in
[`tables.md`](../../research/artifacts/fd023828337641fa8cfdbc44e1c5ffe3/tables.md): 96
arm-against-control comparisons on four scored panels and four hostile re-runs, on
Experiment 018's panels with one new source. The specification predicted, before the run,
a bracket rather than a null: `exploratory` for the stacked arms at the vendor's gross
series and full loading, `unresolved` under a 2 pp/yr trading-cost haircut and a 0.681
delivered loading. Both halves came in.

---

## Conclusion

1. **The premise holds.** Cross-asset carry is the first candidate this repository has
   measured that is nearly uncorrelated with the trend overlay: **+0.063** on 1,157 months
   from 1929, **+0.066** in the worst decile of equity months, +0.069 and −0.02 on the
   four-asset-class window from 1974, +0.101 and −0.036 against AQR's TSMOM from 1985. The
   commodity-carry overlap the sleeves audit rejected is not in the composite: the
   commodity carry leg correlates +0.04 with the trend book. Carry is not equity-neutral,
   though: +0.119 to equity over the full window and **+0.219 in equity's worst decile**,
   rising to +0.25 after 2009 and +0.61 in the tail after 2013, and the equity-index and
   currency legs are where that comes from. §2.
2. **The stack adds as a sum, and the sum clears its floor at the top of the bracket.** A
   10-point RSSY-like stack beats the reference construction by **+0.58 pp/yr [+0.28, +0.86]
   against a 0.35 floor** on 96 years, +0.56 [+0.24, +0.87] against 0.40 from 1974, and
   +0.44 [+0.12, +0.76] against a 0.44 floor on the AQR panel from 1985, exactly at its floor.
   Twenty points doubles it. The sum-rule residual is 0.0002 pp/yr: the overlay adds its
   edge as a sum, as [stacking](stacking-and-effective-breadth.md) §1 says a financed
   overlay must. Charging 2 pp/yr on the carry leg takes the 10-point gap to +0.38 against
   0.35; delivering it at 0.681 of a unit takes it to +0.36 against 0.24; **both together,
   by hand, +0.22 against 0.35: `unresolved`.** §3.
3. **Substitution does not work.** Fifteen points of trend swapped for fifteen of carry
   reads **−0.13 [−0.69, +0.44]** against the reference on 96 years, inside a 0.72 floor,
   and **−1.09 [−1.72, −0.48]** on the AQR panel, where the vendor's trend series earns 12.2
   pp/yr. Carry alone at 30 points in place of the trend wrapper is −0.25 (1929) and −2.17
   (1985) against the reference. The candidate is a second engine, not a replacement. §3.
4. **The last twelve and a half years are negative.** On the vendor's own series carry
   earned +0.77 pp/yr gross from 2009 and **−2.96 pp/yr from 2013-09**, the month after the
   carry paper circulated; the 10-point stack reads −0.03 and −0.41 against the reference on
   those windows, against floors of 0.9 and 1.0. The same post-2009 decay Experiment 018
   found on trend is here on carry, unresolvable on the same windows. §4.
5. **Consequence.** Not added to the vector by default. It is the best-supported second
   engine the repository has measured, better than the Treasury stack on every axis
   Experiment 018 scored, and its resolvable half rests on a gross vendor reconstruction at
   full loading. RSSY itself has 27 months of history and returned −0.88%/yr against the
   S&P 500's 18.87% from inception to 2025-12-31. §7 sizes the line for an investor who
   wants it anyway: 10 points from VTI, entirely in shelter, at a placement cost of about
   6 bp/yr.

---

## 1. Design

| Panel | Window | Months | Trend leg | Carry leg |
| --- | --- | ---: | --- | --- |
| primary | 1929-01…2025-05 | 1,157 | own 4-asset book, ×1.9771 to 12.38% volatility (Experiment 018's) | AQR `All Macro Carry`, ×2.7575 to 12.38% |
| four-class sub-window | 1974-02…2025-05 | 616 | own book | the same, from the month the currency leg begins |
| secondary | 1985-01…2026-02 | 494 | AQR TSMOM, gross of its trading costs | the same |
| post-publication check | 2013-09…2026-02 | 150 | AQR TSMOM | the same; a check, floors near 1 pp/yr |
| four hostile re-runs | 1929-01…2025-05 | 1,157 | own book | 1 and 2 pp/yr charged on every unit of carry notional; 0.681 of a unit delivered; the series moved one month |

**The carry leg** is the cross-sectional, rank-weighted long/short carry factor averaged
across equity indices, fixed income, currencies and commodities from AQR's
century-of-factor-premia workbook (Ilmanen, Israel, Lee, Moskowitz and Thapar 2021), the
only free cross-asset carry return series. Its sheet says returns are gross of trading
costs and fees; its factor definitions are shipped as pictures with no recoverable text;
the currency leg begins 1974-02, so the composite is three asset classes before that
month and four after, weighted in a way the workbook does not state. Realised volatility
on the primary window is 4.49%, so one unit of carry notional here is 2.76 units of the
vendor's composite. Scaling it to the trend leg's 12.38% makes the substitution arm swap
like for like; every carry gap is linear in the carry weight, so a reader who believes
RSSY runs its leg at 10% reads the 10-point stack as an 8-point one.

**Wrappers are assumed exposure vectors, not fund returns.** RSSY-like: 1.0 equity (75%
ETF plus 25% E-mini, from the summary prospectus) plus 1.0 carry, 99 bp, financing at 62 bp
on the 0.25 of equity futures, the long/short book charged no signed basis. RSST-like and
the 3 bp core as in Experiment 018. The certain cost of ten stacked points is
`0.10 × (99 + 0.25 × 62 − 3) = 11.15 bp/yr`; the specification's mechanism note says
11.45, an arithmetic slip of 0.3 bp left in the frozen file rather than edited after the
run.

Arms: the reference `base_trend30`; the carry wrapper stacked at 10 and 20 points in place
of core (equity notional unchanged at 1.022, gross 1.42 and 1.52); 15 trend / 15 carry;
30 trend + 30 carry; and carry alone at 30 points. Controls, statistics, falsifier,
bootstrap, Benjamini-Hochberg and the eight crisis episodes are Experiment 018's, reused
by import.

---

## 2. The correlations, which are the premise

Primary panel, 1,157 months; conditional entries are on the 115 worst equity months and
are biased toward zero by the truncation, so they are read against each other only.

| Pair | Full sample | Worst decile of equity months |
| --- | ---: | ---: |
| carry, trend | **+0.063** | **+0.066** |
| carry, equity | +0.119 | **+0.219** |
| trend, equity | −0.074 | +0.072 |

| Leg | Mean excess, pp/yr | Volatility | Worst-decile mean, pp/month | Hit rate |
| --- | ---: | ---: | ---: | ---: |
| equity | 7.75 | 18.53 | −9.36 | 0.00 |
| trend | 7.22 | 12.38 | +1.57 | 0.63 |
| carry | 6.89 | 12.38 | +0.17 | 0.57 |

Carry's gross Sharpe ratio at this scaling is 0.56 from 1929, 0.66 from 1974, 0.55 from
1985 and negative from 2013, inside the 0.5 to 0.8 the specification assumed. **Trend and
carry are two engines**, on every window and in the tail. The paper's claim survives on a
century of the vendor's own reconstruction.

**Where the equity correlation lives.** Each per-asset-class carry column against the own
trend book and equity, unscaled:

| Component | Months | With trend | With equity | With equity, worst decile | Mean, pp/yr | Volatility |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| equity indices carry | 1,157 | −0.02 | **+0.23** | **+0.33** | 1.86 | 12.6 |
| fixed income carry | 1,157 | +0.10 | −0.05 | −0.04 | 2.56 | 4.8 |
| currencies carry | 616 | −0.01 | **+0.34** | **+0.37** | 2.61 | 6.4 |
| commodities carry | 1,084 | +0.04 | −0.07 | 0.00 | 5.82 | 16.9 |

The bond and commodity legs are equity-neutral; the equity-index and currency legs are
long equity risk, and they are why the composite loses in the tail after 2013 (worst-decile
mean −1.50 pp/month, hit rate 0.40, correlation +0.61 on 15 months). Koijen, Moskowitz,
Pedersen and Vrugt report that diversified carry does poorly in global recessions, and the
episode table agrees: the 10-point stack gives up 0.9 pp across the GFC and 1.1 pp across
covid against the reference and picks up 2.4 to 2.6 pp across 1973 and 1977–81.

**By era**, carry-trend correlation is +0.04 to +0.13 on every declared window except the
38 months from 1974-02 (−0.32, too short to read); carry-equity in the worst decile is
+0.28 before 1977, +0.19 after, +0.51 in the flat equity decade and +0.61 after 2013.

---

## 3. The stacked leg, the substitution and the sum rule

Primary panel, gaps against the reference arm, in which the trend leg cancels:

| Arm | Gap, pp/yr | 95% interval | Floor | Years | Max drawdown, arm / reference | Status |
| --- | ---: | :---: | ---: | ---: | ---: | --- |
| carry stack 10 | **+0.58** | [+0.28, +0.86] | 0.35 | 36 | −81.82 / −82.78 | `exploratory` |
| carry stack 20 | **+1.15** | [+0.57, +1.72] | 0.71 | 36 | −80.83 / −82.78 | `exploratory` |
| trend 15 / carry 15 | **−0.13** | [−0.69, +0.44] | 0.72 | 3,166 | −81.81 / −82.78 | `rejected` on sign, inside its floor |
| trend 30 + carry 30 | +1.73 | [+0.85, +2.58] | 1.06 | 36 | −79.80 / −82.78 | `exploratory` |
| carry 30 alone | −0.25 | [−1.38, +0.87] | 1.44 | 3,165 | −80.84 / −82.78 | `rejected` on sign, inside its floor |

The same rows on the other scored panels:

| Arm vs reference | 1974– (616 mo) | Floor | 1985–, AQR TSMOM (494 mo) | Floor | 2013-09– (150 mo) | Floor |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| carry stack 10 | +0.56 [+0.24, +0.87] | 0.40 | **+0.44 [+0.12, +0.76]** | **0.44** | −0.29 [−0.70, +0.12] | 0.73 |
| carry stack 20 | +1.12 [+0.48, +1.74] | 0.79 | +0.88 [+0.23, +1.52] | 0.88 | −0.57 [−1.40, +0.24] | 1.46 |
| trend 15 / carry 15 | −0.16 [−0.85, +0.51] | 0.94 | **−1.09 [−1.72, −0.48]** | 0.99 | −1.04 [−2.27, +0.03] | 1.84 |
| carry 30 alone | −0.32 [−1.70, +1.02] | 1.88 | **−2.17 [−3.44, −0.96]** | 1.98 | −2.08 [−4.54, +0.06] | 3.68 |

**By hand**, `0.10 × 6.89 − 0.1115 = +0.58` and `0.20 × 6.89 − 0.223 = +1.15`: the paired
gap is the carry leg's gross mean times its weight less the certain cost, and the
correlation contributes nothing to an arithmetic mean. What the correlation buys is
visible elsewhere: the 10-point stack's volatility is 19.19% against the reference's
18.99% for 0.10 more of gross, its maximum drawdown is 1 pp shallower, its longest run
under water is 88 months against 164 (the 1929 run, as the bond stack also halved), and on
log growth it beats the reference by +0.53 pp/yr and its 1.42× leverage-matched control by
+1.19, a control that draws down −93.7%. On arithmetic mean every arm loses to its
leverage-matched control, as the trend wrapper does (§2 of the defensive-engines page
explains why that control is the wrong statistic on a path that loses nine tenths of its
value), and the ex-post volatility-matched control is beaten by +2.29 [+1.50, +3.11].

**The sum rule.** `gap(trend 30 + carry 30) = +3.72`, `gap(trend 30) = +1.98`,
`gap(carry 30) = +1.73`, residual **+0.0002 pp/yr** on every scored panel. The overlay adds
as a sum, exactly, and the substitution arm shows the other half of the same identity: it
averages two engines of nearly equal gross mean and pays 0.15 of a unit of trend for 0.15
of a unit of carry, which on this instrument is a wash on 96 years and a loss wherever the
vendor's trend series is the stronger leg.

**The hostile re-runs**, primary panel, gap against the reference:

| Carry leg | Stack 10 | Floor | Stack 20 | Floor | 15 / 15 | Carry 30 alone vs cheap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| published, gross, full loading | +0.58 | 0.35 | +1.15 | 0.71 | −0.13 | +1.73 |
| 1 pp/yr charged on the carry leg | +0.48 | 0.35 | +0.95 | 0.71 | −0.28 | +1.43 |
| 2 pp/yr charged | **+0.38** | 0.35 | +0.75 | 0.71 | −0.43 | +1.13 |
| delivered at 0.681 of a unit | **+0.36** | 0.24 | +0.72 | 0.48 | −0.46 | +1.07 |
| 2 pp/yr and 0.681 together, by hand | **+0.22** | 0.35 | +0.45 | 0.71 | | |
| series moved one month (alignment) | +0.60 | 0.35 | +1.19 | 0.70 | −0.10 | +1.79 |

The haircuts are assumptions: the vendor states no cost, a rank-weighted cross-sectional
book rebalanced monthly turns over less than a trend book on bonds and currencies and more
on commodities, and 2 pp/yr is the pessimistic bound. The alignment row moves the carry
series one month later, which keeps its mean and drops its same-month co-movement with
equity and trend; the gaps do not move, which says the paired result is a mean and not a
diversification effect. The equity-financing band 62 to 231 bp moves the 10-point gap from
+0.58 to +0.54 and leaves the arm ordering unchanged at every point.

**Where the bracket sits.** Top: +0.58 against 0.35, `exploratory` on three of four
scored panels and at its floor on the fourth. Bottom: +0.22 against 0.35, `unresolved`.
The prediction said 0.30 for the bottom; the realised gross mean was 6.89 rather than the
8 assumed. A 10-point stack is 1.2 points of tracking error against the reference for
+0.2 to +0.6 pp/yr, which is a better trade on every axis than the Treasury stack's
+0.34 for 1.7 points, and it is not a resolved one.

---

## 4. The eras the paper could not have fitted

Gap of the 10-point stack against the reference, pp/yr, and the carry leg's gross mean:

| Era | Months | Stack 10 vs reference | Carry mean, pp/yr | Carry-equity, worst decile |
| --- | ---: | ---: | ---: | ---: |
| 1929-01…1977-03 | 579 | +0.71 | 8.21 | +0.28 |
| 1977-04…2025-05 | 578 | +0.44 | 5.56 | +0.19 |
| flat equity decade, 1999-03…2009-02 | 120 | +0.77 | 8.78 | +0.51 |
| three-class composite, 1929-01…1974-01 | 541 | +0.60 | 7.09 | +0.28 |
| four-class composite, 1974-02…2025-05 | 616 | +0.56 | 6.71 | +0.16 |
| post-2009 | 197 | **−0.03** | 0.77 | +0.29 |
| post-publication, 2013-09…2025-05 | 141 | **−0.41** | **−2.96** | **+0.61** |

Trend on the same windows reads +0.37 (post-2009) and +0.04 (post-2013) against the cheap
control on Experiment 018's instrument; carry's decay is of the same shape and one step
worse. Neither is resolvable on 141 to 197 months (floors 0.9 to 2.2 pp/yr), and a decade
of a market-neutral factor earning nothing is inside the century's own dispersion. It is
also exactly the window RSSY's own record sits in.

---

## 5. What an RSSY line would actually be

`as of 2026-09-02`, from the fund's summary prospectus of 2026-04-27 and the issuer's
page.

| | RSSY |
| --- | --- |
| Name, issuer | Return Stacked U.S. Stocks & Futures Yield ETF; Tidal Investments as adviser, Newfound Research as sub-adviser for the equity leg, ReSolve Asset Management SEZC (Cayman) as futures trading advisor |
| Inception | 2024-05-28 |
| Fee | **0.99%**: 0.95% management plus 0.04% acquired-fund fees; no waiver |
| Net assets | **$94.72M** at 2026-08-31 |
| Per dollar of capital | 1.00 of large-cap US equity (design 75% ETF plus 25% S&P 500 E-mini; holdings at 2026-09-01 show IVV 74.29% and E-mini 13.82% of net assets, read as a snapshot) plus 1.00 of futures-yield notional |
| The carry engine | No index. A proprietary, systematic ReSolve process "evaluating the carry premium in commodity, currency, equity, volatility, credit and fixed income instruments", long positive-carry and short negative-carry contracts across four asset classes, risk-weighted on 30-day trailing volatility, rebalanced daily; no stated volatility target |
| Structure | Futures held directly or through a wholly-owned Cayman subsidiary capped at 25% of assets; collateral 25% to 100% in bills and cash equivalents; 83% portfolio turnover in the year to 2026-01-31; distributions annual |
| Record | Calendar 2025 **−2.97%** against the S&P 500's 17.88%; since inception to 2025-12-31 **−0.88%/yr against 18.87%**; worst quarter −12.02% (2025 Q1), best +8.78% (2025 Q3); year to 2026-03-31 +15.51% |

The record is the product fact that matters. Over 19 months the fund trailed its equity
leg's index by about 20 pp/yr, which after 99 bp of fee and roughly 1.3 pp of financing on
the E-mini leg is a futures-yield leg near **−17 pp/yr gross**. On the vendor's composite,
scaled as here, 2024-06…2026-02 is also negative; the fund's strategy is proprietary and
daily, and nothing here measures what it delivers per unit of any carry index. Thirty-six
filed months, the threshold [comparability](loading-comparability-and-wrapper-exposure.md)
used for RSST, arrive in 2027-06.

---

## 6. Where it could be held

By [the placement logic](portfolio-for-one-investor.md) §3, a futures leg through a Cayman
subsidiary yields subpart F ordinary income, its collateral yield is ordinary, and it
forfeits the deferral that [structural and tax edges](structural-and-tax-edges.md) §4
prices as the largest number on that page, so an RSSY line belongs in shelter beside RSST.
The traditional third is the right account for the least-established expected return in
the portfolio, and it is 90% RSST at a 30-point wrapper: 3.3 points of a 10-point RSSY line
fit there and 6.7 must go to the Roth, whose premium is proportional to expected return,
which is the wrong account by the page's own argument. Shelter demand at RSST 30 + RSSY 10
+ IDMO 5 + AVES 5 + AVDV 10 + VXUS 16 is 76 points against 66.7 of capacity, so about 9.3
points of VXUS are pushed into the taxable account at 64.9 bp per dollar sheltered: about
**6 bp/yr**, roughly the whole booked placement edge of +2 to +7 bp/yr. A line that fits
only by evicting the fund that ranks fifth in the shelter queue is a line the accounts do
not have room for, unless the wrapper shrinks.

---

## 7. The consequence for the decision

**The vector does not change:** RSST 30 / VTI 19 / VTV 15 / VXUS 16 / AVDV 10 / IDMO 5 /
AVES 5. The reasons, in order: the resolvable half of the bracket is the vendor's gross
reconstruction at a full unit, and the costed, loading-adjusted half is inside its floor;
the engine's own last twelve and a half years and the fund's own 19 months are negative;
and the accounts have no room for it at a 30-point trend wrapper without paying the
placement edge.

**What the evidence does say.** Cross-asset carry is a second engine in the sense the
stacking page defines: near-zero correlation to trend on a century, an edge that adds as a
sum, a drawdown 1 pp shallower and a 1929 run under water half as long. It is not a
defensive engine: it is long equity risk in the tail through its equity-index and currency
legs. It is the best second-engine candidate this repository has measured, and the
Treasury stack, the gold stack and every substitution Experiment 018 scored rank below it.

**The sized line for an investor who wants it anyway.** Ten points of RSSY funded from
VTI, which keeps US equity notional at 1.022, the international weight unchanged and gross
at 1.42: **RSST 30 / RSSY 10 / VTI 9 / VTV 15 / VXUS 16 / AVDV 10 / IDMO 5 / AVES 5.**
Expected contribution +0.2 to +0.6 pp/yr against 1.2 points of tracking error, certain
cost 11 bp/yr, placement cost about 6 bp/yr, entirely in shelter, with the traditional
third holding RSST 30 and RSSY 3.3 and the Roth the other 6.7. Not twenty points: the
20-point line is 1.52× gross for a floor-clearing +1.15 that halves under the same
haircuts, and its levered control draws down −95%. Not a split wrapper: 15 / 15 is a wash
on the best evidence and a loss on the vendor's.

**Reopening conditions.** Thirty-six months of RSSY filings (2027-06) fitting a loading on
a carry index the way RSST's was fitted, at which point the 0.681 row becomes a measured
one; a carry series with a stated cost basis, which would replace the haircut band; or a
five-year window from 2013-09 on which the post-publication gap clears its floor in either
direction.

---

## Verified, assumed, open

**Verified.** Every gap, interval, floor, drawdown, correlation, era and episode figure in
§2–§4, from run `fd023828…` against a specification hashed before the run; the sum-rule
residual of 0.0002 pp/yr; the by-hand decomposition of the 10- and 20-point gaps to two
decimals; the trend-book scalar 1.9771 reproducing Experiment 018's on the identical
window. The carry workbook's sha256, sheet, columns and coverage are in
[its manifest](../../research/data-manifests/aqr_century_factor_premia_monthly.json).
Product facts in §5 from the summary prospectus and issuer page.

**Assumed.** The RSSY-like exposure vector, from the prospectus design rather than a
filing. The carry leg scaled to 12.38% by one full-window constant; RSSY states no
volatility target. Trading-cost haircuts of 1 and 2 pp/yr. A 0.681 loading borrowed from
RSST's trend leg. The composite's three-to-four-class splice at 1974-02 and its unstated
weighting. No tax anywhere in §2–§4. The placement arithmetic in §6 uses the
portfolio-for-one-investor page's yields and ranking.

**Open.**

1. RSSY's delivered loading on any carry index, and its 2025 attribution by asset class.
2. A carry series with costs, or a repository-built cross-asset carry book on public
   yields, which would put the trading cost inside the rule instead of in a band.
3. Whether the equity-index and currency carry legs can be dropped without losing the
   composite's mean, since they carry the equity tail risk and 4.5 pp/yr of the 6.9.
4. The correlation-regime question Experiment 018 left open applies here too: carry's
   worst-decile correlation to equity has risen in every era since 1977.

## What this does not establish

- **Not** that carry beats anything after cost: the costed, loading-adjusted gap is inside
  its floor.
- **Not** that RSSY delivers the engine: 19 months of the fund's record run the other way,
  and no loading has been fitted.
- **Not** that carry is harmful: every long-window gap is positive, and the post-2013
  reading is unresolvable.
- **Not** a promotion. Nothing here is above `exploratory`, and
  [decision 0004](../decisions/0004-no-sleeve-promoted.md)'s non-promotion stands.

## Reproduce it

```sh
cd research
uv run python -m portfolio_edge.experiments.exp_019_carry_engine --view-results
uv run pytest tests/unit -k carry_engine
```

The carry workbook is registered as `aqr_century_factor_premia` in
[`data/aqr.py`](../../research/src/portfolio_edge/data/aqr.py); a new run requires the
cached file to hash to the pinned digest.
