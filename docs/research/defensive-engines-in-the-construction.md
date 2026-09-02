# Defensive engines inside the construction

**Question.** The recommended construction is 100% equity notional plus a 30% financed
trend overlay, and it holds no bonds, TIPS, gold or cash. Every earlier defensive test
priced those assets alone or at 10% pro rata against an unlevered equity base. Does a
defensive engine held *inside* the leveraged construction improve growth, drawdown and
crisis behaviour against cheap, leverage-matched and volatility-matched controls, and does
the same 96-year panel say anything new about the trend overlay itself?

**Decision it informs.** Whether to add a stacked Treasury leg (RSSB-like, 20 or 40
points), a stacked gold leg (GDE-like, 10 points) or a stacked TIPS leg, or to replace ten
points of the equity core with cash, an unlevered long-Treasury fund or a bonds-plus-trend
wrapper (RSBT-like). The concrete proposal under review was VTI 12 / VXUS 8 replaced by a
20-point RSSB-like stack.

**Out of scope.** The trend weight ([trend weight](trend-weight-under-uncertainty.md)),
the choice of trend wrapper ([live stacked fund records](live-stacked-fund-records.md)),
what today's valuations license ([valuation and the allocation](valuation-and-the-allocation.md)),
and where each line is held ([structural and tax edges](structural-and-tax-edges.md) §8).

`as of 2026-09-01`. **`exploratory`.** [Experiment 018](../../research/experiments/exp_018_defensive_engines.yaml),
spec `40252300…`, run
[`311048fb…`](../../research/artifacts/311048fbc6b44072a3715ff24d1507a4/summary.md):
108 arm-against-control comparisons on four panels, with the per-panel tables in
[`tables.md`](../../research/artifacts/311048fbc6b44072a3715ff24d1507a4/tables.md). The
ledger also holds an identical earlier run, `add4adcc…`, and a failed start, `b773293e…`,
which stopped because the FRED GS10 download no longer hashed to the pinned vintage; the
pin was refreshed and nothing else changed. The specification predicted, before the run,
that every mean gap against every control would come back `unresolved`. A red-team review
re-ran the frozen code paths in memory with one input substituted at a time (4,000
bootstrap resamples where the artifact used 10,000); its reproductions are restated where
they change a reading, and nothing it produced was registered.

---

## Conclusion

1. **The trend overlay clears its floor at the top of a bracket and not at the bottom.**
   On 1,157 months from 1929 the reference construction beats the cheap 100%-equity
   control by **+1.98 pp/yr [+1.26, +2.73] against a 1.06 floor**, and a volatility-matched
   control by +1.79. That gives the wrapper a full unit of trend, charges the trend book
   nothing for its 262% turnover, and trades with no lag. Pricing any two of those puts the
   gap at or under its floor: **+1.30 at RSST's filed 0.681 loading, +1.08 with a 20 bp
   trading cost as well, +0.84 with a one-month lag as well.** The gap is positive in every
   decade from the 1930s to the 2000s, is not a 1929 artefact, and decays after 2009 to a
   size no window can resolve. §2.
2. **A stacked Treasury leg is `unresolved` on the mean and its whole contribution is one
   era.** +0.34 pp/yr [−0.01, +0.69] at 20 points against a 0.49 floor; +0.68 at 40. Inside
   1981-10…2020-07 it reads +1.20; on the 691 months outside, **−0.25 [−0.69, +0.16]**, and
   the stacked portfolio spent **576 consecutive months (1933–1981) behind the reference**.
   It leaves the maximum drawdown within 1 pp, helps the three modern deflationary episodes
   by 1–5 pp, costs 22–42 pp across 1977–81 and 2–5 pp in 2022. At today's 0.8 pp term
   premium its expected contribution is about **+0.04 pp/yr against 1.71 points of tracking
   error**, after an 11 bp certain cost. **Not added.** §3.
3. **Substitution is the one measurable defensive trade, and it is `rejected` on the
   mean.** Ten points of equity moved into cash, long Treasuries or an RSBT-like wrapper
   cost **−0.55 to −0.77 pp/yr** against the reference and cut the 1929 and 2008 drawdowns
   by **4.0–5.4 pp**. NTSX-like in place of the whole construction is rejected everywhere
   (−1.66). §4.
4. **A stacked gold leg is `unresolved`** (+0.35 [−0.20, +0.94] on 1968–2025 against a
   0.64 floor), improves the maximum drawdown by 1.4 pp and adds 6.8 pp across the 1970s
   inflation episodes; the real gold price is at the 98.5th percentile since 1975. **Not
   added.** §5.
5. **A stacked TIPS leg can only be described**: +0.31 against a 0.69 floor on 275 months
   from 2003. §6.
6. **Consequence.** The capital-weight vector does not change. Valuation enters through the
   drawdown assumption rather than through a bond stack: at a stated tolerance of −50% or
   tighter, ten points of long TIPS unlevered in the traditional IRA and a wrapper shrunk
   to the ladder's figure; at −60% or looser, none. §9.

---

## 1. Design

| Panel | Window | Months | Trend leg | Bond leg |
| --- | --- | ---: | --- | --- |
| primary | 1929-01…2025-05 | 1,157 | own 4-asset book, scaled ×1.9771 to 12.38% volatility | Goyal–Welch `ltr`, ~20-year government |
| gold sub-window | 1968-05…2025-05 | 685 | own book | `ltr`; the gold arm runs here |
| secondary | 1985-01…2025-12 | 492 | AQR TSMOM, gross of its trading costs | `ltr` |
| check | 2003-02…2025-12 | 275 | AQR TSMOM | `ltr`; modelled TIPS |
| duration sensitivity | 1953-05…2025-05 | 865 | own book | GS10 10-year par bond, and `ltr` on the same window |

**Wrappers are assumed exposure vectors, not fund returns**: units of equity, Treasury,
trend or gold excess return per dollar of capital, less a fee on the capital and financing
on the notional above it. RSST-like 1.072 equity + 1.000 trend at 99 bp; RSSB-like 1.0
equity + 1.0 Treasury at 39 bp; RSBT-like 1.0 Treasury + 1.0 trend at 97 bp; NTSX-like 0.9
equity + 0.6 Treasury at 20 bp; GDE-like 0.9 equity + 0.9 gold at 20 bp; an unlevered
long-Treasury fund at 5 bp; the core at 3 bp. Financing over cash: 62 bp equity, 15 bp
Treasury, 30 bp gold (an assumption, swept 0–60). Not charged: the trend book's own
trading, AQR's trading costs, any tax.

The reference arm `base_trend30` (70% core, 30% RSST-like: 1.022 equity, 0.300 trend,
1.322 gross) is scored against the 3 bp index, the index levered to the arm's gross
notional at the same financing, and the index scaled to the arm's volatility; every
candidate is scored against those and against the reference. Arithmetic mean gap after
cost, stationary block bootstrap (mean block 12 months, 10,000 resamples), minimum
detectable effect at 80% power from the paired series, Benjamini–Hochberg per control per
panel, and a sign check across the equity-financing band. `rejected` at or below zero;
`unresolved` inside the floor or failing BH or the band; `exploratory` otherwise, and
nothing above it. Drawdown, months under water, worst-decile and crisis-episode tables are
descriptive and carry no status.

---

## 2. The trend overlay on 96 years

| Reference arm against | Gap, pp/yr | 95% interval | Floor | Years | Status |
| --- | ---: | :---: | ---: | ---: | --- |
| cheap 100% equity | **+1.98** | [+1.26, +2.73] | 1.06 | 27 | `exploratory` |
| volatility-matched, ex post (1.027× index) | +1.79 | [+1.06, +2.54] | 1.06 | 34 | `exploratory` |
| volatility-matched, ex ante | +1.59 | [+0.82, +2.38] | 1.11 | 45 | `exploratory` |
| leverage-matched (1.322× index) | −0.30 | [−1.63, +1.15] | 1.97 | 4,181 | `rejected` |

**Three controls, three questions.** The leverage-matched control draws down **−92.06%**
(the 1.72× control for the 40-point bond stack, −97.08%); an arithmetic mean over a path
that loses 92% is the wrong statistic, and the specification says so while scoring on it.
On **log growth the reference arm beats its leverage-matched control by +0.88 pp/yr** over
the full window (11.08 against 10.19), by +0.27 to +0.90 from every start before 1990, and
loses from 1990-11 (−0.18) and from 2009 (−2.91). The reference arm draws down −82.78%
with 164 months under water against the cheap control's −83.67% and 184, at 18.99%
volatility against 18.50%.

**The bracket.** The primary panel's trend leg is the repository's own book scaled by
1.9771: a Sharpe-preserving rescale of a book whose gross notional averages 1.11× unscaled
(peak 1.71×) and 2.19× scaled (peak 3.39×). The financing of a long/short futures book is
near zero; the trading is not priced, and the wrapper is given 1.000 of trend where RSST's
31 filed months fit 0.681 [0.406, 0.955]
([comparability](loading-comparability-and-wrapper-exposure.md)). Re-running the frozen
specification with only the trend series replaced (red team):

| Trend leg on the primary panel | Leg mean | vs cheap | Floor | vs leverage-matched | Bond stack 20 vs reference |
| --- | ---: | ---: | ---: | ---: | ---: |
| published: ×1.977, no cost, no lag | 7.22 | +1.98 [+1.27, +2.75] | 1.06 | −0.30 | +0.34 |
| ×1.977, 20 bp one-way on 262% turnover | 6.18 | +1.67 [+0.93, +2.47] | 1.06 | −0.61 | +0.34 |
| ×1.977, positions lagged one month | 4.99 | +1.31 [+0.55, +2.09] | 1.04 | −0.96 | +0.34 |
| unscaled ×1.0, no cost, no lag | 3.65 | +0.91 [+0.56, +1.28] | 0.54 | −1.37 [−2.54, −0.11] | +0.34 |

By hand, `0.30 × 7.22` trend `+ 0.0216 × 7.75` equity `− 0.35` net cost `= +1.99`;
rescaling only the trend term to 0.681 gives **+1.30, then +1.08 with the 20 bp cost, then
+0.84 with the lag**, against a 1.06 floor. The lag row is a bound, not an estimate: a
monthly book cannot say what a daily programme captures in the month after a signal flip,
and the 2.2 pp/yr it removes is the size of that unknown. The last column is why none of
this touches §3: the trend leg cancels in every paired comparison against the reference.

**Sub-windows**, everything else unchanged (red team):

| Start | Months | vs cheap | Floor (i.i.d. / block) | vs leverage-matched, arithmetic / log | Bond stack 20 vs reference |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1929-01 (published) | 1,157 | +1.98 [+1.27, +2.75] | 1.06 / 1.05 | −0.30 / +0.88 | +0.34 |
| 1934-01 | 1,097 | +2.04 [+1.31, +2.78] | 1.08 / 1.06 | −0.50 / +0.34 | +0.34 |
| 1946-01 | 953 | +1.86 [+1.08, +2.68] | 1.19 / 1.16 | −0.48 / +0.27 | +0.27 |
| 1970-01 | 665 | +2.17 [+1.17, +3.17] | 1.50 / 1.44 | +0.04 / +0.90 | +0.56 |
| 1990-11 (tournament window) | 415 | +1.84 [+0.68, +3.03] | 1.78 / 1.70 | −0.98 / −0.18 | +0.78 |
| 2009-01 | 197 | +0.37 [−0.90, +1.65] | 2.21 / 1.82 | −3.78 / −2.91 | +0.38 |
| AQR secondary, 1985-01 | 492 | +3.46 [+2.26, +4.60] | 1.64 / 1.68 | +0.67 / +1.51 | +0.82 |
| AQR secondary, 2009-01 | 204 | +1.04 [−0.44, +2.65] | 2.62 / 2.25 | −3.21 / −2.30 | +0.38 |

Dropping 1929-09…1932-06 leaves +1.99 [+1.25, +2.73]; those 34 months carry 2.5% of the
gap. By decade the gap is +0.5 to +3.6 from the 1930s through the 2000s, then +0.63 in the
2010s and +0.29 in the 2020s: the post-2009 decay [the adversarial review](adversarial-review.md)
found on three constructions is here on a fourth, unresolvable here too (floors 1.8–2.6).

This is the strongest portfolio-level evidence for the overlay the repository holds: a
bracket whose top clears its floor and whose bottom does not, on a US-only equity base,
with the trend leg a construction rather than a fund. It promotes nothing.

---

## 3. The stacked Treasury leg

| Arm | Panel | Gap vs reference | 95% interval | Floor | Max drawdown, arm / reference | Status |
| --- | --- | ---: | :---: | ---: | ---: | --- |
| bond stack 20 | primary, 1929– | **+0.34** | [−0.01, +0.69] | 0.49 | −82.53 / −82.78 | `unresolved` |
| bond stack 40 | primary | +0.68 | [−0.01, +1.37] | 0.97 | −82.28 / −82.78 | `unresolved` |
| bond stack 20 | gold sub-window, 1968– | +0.48 | [−0.06, +1.01] | 0.78 | −44.40 / −45.86 | `unresolved` |
| bond stack 20 | AQR secondary, 1985– | +0.82 | [+0.28, +1.36] | 0.88 i.i.d. / **0.77 block** | −45.28 / −46.71 | `unresolved`; `exploratory` on the block floor |
| bond stack 40 | AQR secondary | +1.65 | [+0.57, +2.73] | 1.75 i.i.d. / 1.55 block | −43.93 / −46.71 | the same flip |
| bond stack 20 | GS10 10-year bond, 1953– | **+0.17** | [−0.17, +0.55] | 0.42 | −44.09 / −45.86 | `unresolved` |
| bond stack 20 | `ltr` on the same 1953– window | +0.32 | [−0.11, +0.72] | 0.63 | −44.40 / −45.86 | `unresolved` |

Against the cheap control every bond-stack arm is `exploratory` (+2.32 at 20 points on
the primary panel) because the trend leg is inside it; the paired row against the
reference is the one that isolates the bond leg, and it is inside its floor on every panel
where the two floors agree. On the primary panel they do (0.494 against 0.488). On the AQR
panel, which begins inside the bond bull market, the stored block floor is 0.77 against
the printed 0.88; under it both stacks clear clause (b), clear BH (adjusted p 0.006) and
hold their sign on the financing band. A status that depends on which of two stored floors
is printed, on the one panel that starts inside the bull market, is not a status.

**One era.** The specification froze the bond-equity regime by era and predicted this in
its freeze note. The bond leg's realised excess return is 2.26 pp/yr over the full primary
window, **6.58 inside 1981-10…2020-07** (466 months, correlation −0.02), −0.16 before it
(633 months, +0.15) and **−6.04 after it** (2020-08…2025-05, 58 months, **+0.37**).
Splitting the paired series on that frozen era (red team):

| Window | Months | Bond stack 20 vs reference | Floor | Bond stack 40 vs reference |
| --- | ---: | ---: | ---: | ---: |
| full | 1,157 | +0.34 [−0.01, +0.69] | 0.49 | +0.68 |
| inside the bond bull, 1981-10…2020-07 | 466 | **+1.20** | | +2.40 |
| complement | 691 | **−0.25 [−0.69, +0.16]** | 0.48 | −0.49 [−1.36, +0.31] |
| 1946-01…1981-09 | 429 | −0.53 | 0.67 | −1.07 |
| 1966-01…1981-09 | 189 | −0.99 | 1.39 | −1.99 |
| 2020-08…2025-05 | 58 | −1.32 | 1.80 | −2.64 |

The full-window +0.34 is `(466 × 1.20 + 691 × (−0.25)) / 1157`. Relative wealth of the
20-point stack against the reference peaked in 1933, troughed at −18.4% in 1981-09 and
took **576 consecutive months** to regain its peak; the 40-point stack troughed at −33.8%.
Its worst rolling ten-year relative return is −12.5%, and 37% of ten-year windows finish
behind the reference. `ltr` is a ~20-year bond where RSSB's ladder is about 6.4 years and
NTSX's 6.75 (§8); the GS10 sensitivity halves the gap, +0.17 against 0.42, for 1.8 pp of
drawdown on 20 points of extra leverage.

**Crisis episodes**, primary panel, cumulative return offset against the reference in pp
(descriptive):

| Arm | 1929 | 1937 | dotcom | GFC | covid | 1973 oil | 1977–81 | 2022 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bond stack 20 | +0.25 | −0.07 | +2.31 | +1.46 | +2.14 | −2.54 | **−22.07** | −2.38 |
| bond stack 40 | +0.50 | −0.15 | +4.65 | +2.84 | +4.32 | −5.00 | **−41.96** | −4.70 |
| cash 10 | +4.00 | +3.86 | +4.30 | +4.20 | +1.97 | +5.29 | +0.92 | +2.40 |
| long Treasury 10 | +4.19 | +3.85 | +5.59 | +5.04 | +3.06 | +3.98 | −9.96 | +1.21 |
| RSBT-like 10 | +4.51 | +4.14 | +5.92 | +5.37 | +3.20 | +4.38 | −9.83 | +1.39 |
| NTSX-like 100 | +3.80 | +4.63 | +7.06 | +3.72 | +6.90 | −14.45 | **−81.30** | −5.93 |

The 20-point stack halves the reference's longest run under water (164 months to 88, the
1929 run) and leaves the maximum drawdown 0.25 pp shallower; its worst-decile offset is
+0.03 pp/month at a 52% hit rate, against +0.94 to +1.02 for the three substitution arms.
The 2022 window was frozen as 2022-01…09 where [Experiment 004](trend-marginal-value.md)
froze 2022-01…10; on the earlier window the offset is −2.83 rather than −2.38.

**2022 depends on which trend series is read.** On the own book (+7.2% in calendar 2022)
the 20-point stack finished the year at **−21.3% against the reference's −18.8% and the
cheap index's −19.9%**: trend did not cover the bond leg's −14.4% excess even at full
loading. On AQR's series (+31.9% over 2022-01…10) it did. The premise that trend covers
the bond leg's inflation hole is true on one vendor's reconstruction of one year and false
on the repository's own instrument.

**The forward number.** The bond leg's expected excess is the term premium: Kim–Wright
+0.84 and ACM about +0.80 in August 2026 ([market scan](market-scan-2026.md)). Twenty
points at 0.8, less the certain cost `0.2 × (39 + 15 + 0.10 × 62) − 0.2 × 3 = 11.4 bp/yr`,
is **+0.04 pp/yr against 1.71 points of tracking error**: about a 48% chance of trailing
the reference after ten years and 46% after thirty. At a zero term premium it is −0.12
with certainty; the realised +0.34 needs 1981–2020's 6.58 pp/yr to recur. The
[`overlay_growth`](../../research/src/portfolio_edge/studies/overlay_growth.py) condition
for a financed leg to raise growth, net Sharpe above `L × ρ × σ_p`, is about 0.11 at 1.52×
gross, 19% portfolio volatility and the post-2020 correlation of +0.37; a 0.8 pp premium on
7% volatility net of cost is about 0.03. It passes only if the correlation returns to zero
or below, which is a regime forecast the proposal does not state.

**Not recommended.** If an investor wants the leg anyway: at most 10 points (certain cost
6 bp/yr, tracking error 0.85), only in the rollover IRA (§8), as an explicit bet that the
bond–equity correlation reverts.

---

## 4. Substitution: the trade the experiment can measure

| Arm (10 points out of the equity core) | Gap vs reference | 95% interval | Floor | Max drawdown | 1929 / GFC offset, pp | Status |
| --- | ---: | :---: | ---: | ---: | ---: | --- |
| cash | **−0.77** | [−1.14, −0.38] | 0.53 | −78.78 | +4.00 / +4.20 | `rejected` |
| unlevered long Treasury, 5 bp | **−0.55** | [−0.94, −0.15] | 0.57 | −78.59 | +4.19 / +5.04 | `rejected` |
| RSBT-like bonds plus trend, 97 bp | −0.60 | [−1.01, −0.17] | 0.60 | −78.27 | +4.51 / +5.37 | `rejected` |
| NTSX-like in place of the whole construction | −1.66 | [−2.95, −0.45] | 1.81 | −78.98 | +3.80 / +3.72 | `rejected` |

Below zero on every trend variant in §2's bracket, every start date and both bond series
(red team). About **−0.6 pp/yr of mean for 4–5 pp of worst drawdown**, and the one
defensive result the design resolves. The bond stack buys none of that drawdown protection
and is not resolvable; the substitution buys it at a stated price, earned on a panel whose
equity excess return was 7.75 pp/yr. §9 is what the price becomes at today's premium over
TIPS.

---

## 5. The stacked gold leg

On the 685-month gold sub-window, which includes 1971-08…1974-12 (an administered price,
then a market a US person could not hold bullion in), noted and not dropped:

| Gold stack 10 vs reference | Gap, pp/yr | 95% interval | Floor | Status |
| --- | ---: | :---: | ---: | --- |
| own book, 1968– | **+0.35** | [−0.20, +0.94] | 0.64 | `unresolved` |
| AQR, 1985– | +0.27 | [−0.22, +0.75] | 0.61 | `unresolved` |
| check, 2003– | +0.80 | [+0.21, +1.39] | 0.88 | `unresolved` |

Maximum drawdown −44.42% against −45.86%; inflation-episode mean +6.82 pp (1973 +5.68,
1977–81 +15.13, 2022 −0.35); deflationary mean +0.88; worst-decile offset +0.16 pp/month at
a 69% hit rate. The gap moves from +0.38 to +0.33 as gold financing is swept 0–60 bp, with
the arm ordering unchanged. The real gold price is at the **98.5th percentile since 1975**,
above the 1980 and 2011 real peaks ([current regime](current-regime-and-pricing.md) §1.7).
Not added.

---

## 6. The TIPS check

On 275 months from 2003-02, the only window on which the modelled TIPS series exists, a
20-point TIPS stack reads **+0.31 [−0.24, +0.86] against a 0.69 floor** (`unresolved`),
drawdown −46.20% against −46.71%; the nominal stack on the same window reads +0.59 against
1.22. No TIPS-futures market exists, the Treasury financing rate is a placeholder, and the
series is modelled from a real par yield. A check, not a test.

---

## 7. Financing sensitivities

Equity basis swept 62–231 bp, Treasury 0–50, gold 0–60. The reference arm's gap against
the cheap control moves from +1.98 to +1.82 across the equity band. The 20-point bond
stack's gap against the reference moves +0.34 to +0.30 across the equity band and +0.37 to
+0.27 across the Treasury band; the 40-point stack +0.73 to +0.54. The arm ordering
against the reference is stable across the Treasury and gold bands; across the equity band
the RSBT-like arm (−0.60 to −0.54) crosses the long-Treasury arm (−0.55 throughout). No
sign changes anywhere.

---

## 8. What a stacked leg would actually be

`as of 2026-09-01`, from the funds' own filings (N-PORT, N-CSR, 497K) and issuer pages.

| | RSSB | NTSX | GDE |
| --- | --- | --- | --- |
| Issuer, inception | Tidal / Newfound / ReSolve, 2023-12-04 | WisdomTree, 2018-08-02 | WisdomTree, 2022-03-17 |
| Fee | **0.39%** (0.35 unitary + 0.04 acquired-fund). A waiver to 0.35% was ended by an outright cut on 2026-04-27; no expiry | 0.20%, no waiver | 0.20% |
| Per dollar of capital | 1.00 equity (SPTM + VXUS + S&P 500 futures, **63/37 US/ex-US**) + 1.00 Treasury futures | 0.90 US large-cap stocks + 0.60 Treasury futures | ~0.90 US large-cap stocks + ~0.90 gold futures |
| Treasury ladder | 2, 5, 10-year and long bond, ~25% each; duration not published, **~6.4 years derived** | five contracts 2–30 years, **6.75 years** (issuer, 2026-08-21) | none |
| Net assets, spread | $520.8M; 0.16% | $1.36B; spread not retrieved | $496.0M (2026-06-30) |
| Structure and tax character | Futures held directly, no Cayman subsidiary; §1256 60/40 on the futures leg, marked to market annually; collateral ~9% money fund + ~2% cash | same | gold through a **Cayman subsidiary** capped at 25%; subpart F income is ordinary; 60/40 does not reach the holder |
| Distributions | 2025: $0.979/share, **~3.4% of NAV, 73% ordinary / 27% long-term gain**; 2024: ~1.1%, 86% ordinary | ~1.1% of NAV a year, all ordinary; no capital-gain distribution since 2021 | all ordinary every year since inception; 1.53 pp/yr measured drag ([tax edges](structural-and-tax-edges.md) §3) |
| Fee per dollar of Treasury notional, net of displaced core | 0.35% | **0.29%** | — |
| Capital for 20 points of Treasuries | 20 points (brings 20 of global equity) | 33.3 points (brings 30 of US large-cap) | — |
| Portfolio-level cost of that slice | ~7.0 bp/yr net | ~5.8 bp/yr net | — |

NTSX is the cheaper wrapper per Treasury dollar by about 1.2 bp of the portfolio a year;
RSSB is the cleaner one, tying one dollar of global equity to each dollar of Treasuries
where NTSX ties 1.5 of US large-cap, and its 25% long-bond rung carries more long-end
exposure per Treasury dollar. Either fund's futures leg forfeits the deferral that
[structural and tax edges](structural-and-tax-edges.md) §4 prices as the largest number on
that page, and its collateral yield is ordinary, so it belongs in the rollover IRA where
RSST already sits; no employer plan offers a return-stacked ETF (§8.5 there). RSSB's
character is read from its filed distribution table, not from a holder's 1099.

---

## 9. The consequence for the decision

**The vector does not change:** RSST 30 / VTI 19 / VTV 15 / VXUS 16 / AVDV 10 / IDMO 5 /
AVES 5. No bond, TIPS or gold stack is added, and the proposal to replace VTI 12 / VXUS 8
with a 20-point RSSB-like stack is declined on this evidence. The stacking arithmetic says
why the list is short: a financed overlay adds its edge as a sum and a substitution as an
average, so a financed leg earns its place only with a positive expected excess and a low
correlation ([stacking](stacking-and-effective-breadth.md) §1). Trend meets both on 96
years; the Treasury leg meets neither at a 0.8 pp term premium and a +0.37 correlation.

**Valuation enters through the drawdown assumption, not through a stack.** A CAPE above
30 at entry has run a median −51.8% real fifteen-year drawdown with 59.7% of months under
water (0.32 independent observations), which through the notional budget supports a
wrapper of 14.9% / 19.1% / 23.7% at a stated tolerance of −40% / −50% / −60%; the current
book implies a tolerance near −70%, and the investor has not supplied a number
([valuation and the allocation](valuation-and-the-allocation.md),
[decision 0012](../decisions/0012-valuation-enters-through-the-drawdown-assumption.md)).
§4 prices the substitution, and its price scales with the equity premium forgone: −0.55 to
−0.77 pp/yr was earned when equity returned 7.75 pp/yr over cash; at 0 to 1.5 pp/yr over
TIPS the same arithmetic is about 0 to 0.2. With the 10-year TIPS real yield at 2.44% and
the 30-year at 2.99% on 2026-08-31, an unlevered TIPS position is the cheapest that
drawdown protection has been in the record.

**The conditional rule.** At a tolerable drawdown of **−50% or tighter**, hold **10 points
of long TIPS unlevered in the traditional IRA**, funded from VTI and VXUS pro rata, and
shrink the wrapper to the ladder's figure (19.1% at −50%, 14.9% at −40%). At **−60% or
looser, hold none.** The default for this contributing, leverage-accepting investor is
none. The rule costs shelter space: the TIPS line displaces about 10 points of RSST from
the traditional account into the Roth and pushes about 7 points of VXUS into the taxable
account, roughly the whole placement edge ([tax edges](structural-and-tax-edges.md) §8).

**Reopening conditions.** A term-premium estimate above about 1.5 pp/yr, or a year of
negative trailing 36-month bond–equity correlation, reopens the stacked Treasury leg; the
test to freeze then is a correlation-conditioned stack scored on the complement of the
bond bull market. Evidence from RSST's own filings that it covered the 2022 bond loss at
its delivered loading would move §3's 2022 reading. A 30-year TIPS real yield below about
2.0% ends the "cheapest in the record" note; a CAPE below 30 reverts the widened drawdown
assumption.

---

## Verified, assumed, open

**Verified.** Every gap, interval, floor, drawdown, episode and era figure in §2–§7, from
run `311048fb…` against a specification hashed before the run. The costs are charged: zeroing
every fee and financing rate moves the reference arm's mean by 0.3796 pp/yr, which is
`0.7 × 3 + 0.3 × (99 + 0.331 × 62)` bp exactly. The red team's reproduction of the central
case matches the artifact to four decimals before any substitution. Product facts in §8
from the funds' own filings.

**Assumed.** Wrapper exposure vectors modelled on filed structures. A ~20-year bond leg
where the funds hold 6.4–6.75 years. A trend book scaled by one full-window constant and
charged no trading; the 0.681 rescale in §2 is arithmetic on the decomposition, not a
re-simulation, and ignores the loading's own interval. The complement-of-the-bull floor
joins two disjoint eras. Gold financing at 30 bp. The term premium is two model estimates.
No tax anywhere in §2–§7.

**Open.**

1. A bond-regime-conditioned test: a stack switched on by trailing correlation, frozen and
   scored on the 691 months outside 1981–2020.
2. A TIPS series before 2003, without which the leg the valuation argument points at cannot
   be scored on a panel containing 1970–81.
3. RSST's own 2022 from its filings at its delivered loading, rather than from either trend
   series.
4. Whether a daily trend programme lands nearer the no-lag or the one-month-lag row of §2's
   bracket; the repository has no daily data.

## What this does not establish

- **Not** that the construction beats a cheap index: a bracket whose top clears the floor
  and whose bottom does not, on US-only equity with a fund-free trend leg.
- **Not** that a Treasury stack is harmful: inside its floor wherever the floors agree,
  with a sign set by which era is in the window.
- **Not** that the substitution is recommended: it is priced, §9 says when the price is
  worth paying, and the default is that it is not.
- **Not** a promotion. Nothing here is above `exploratory`, and
  [decision 0004](../decisions/0004-no-sleeve-promoted.md)'s non-promotion stands.

## Reproduce it

```sh
cd research
uv run python -m portfolio_edge.experiments.exp_018_defensive_engines --view-results
uv run pytest tests/unit -k defensive_engines
```

A new run requires the FRED GS10 vintage to hash to the pinned value; the failed start
`b773293e…` is what happens when it does not.
