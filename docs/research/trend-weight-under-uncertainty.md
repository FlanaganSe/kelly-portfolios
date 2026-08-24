# The trend weight under acknowledged ignorance

**Question.** [The construction tournament](construction-tournament.md) nominated this as its
number-one next test: how much trend notional should the investor hold, when three
instruments return three different answers and the disagreement is about a forward mean that
no amount of resampling 1990–2026 can identify?

**Decision it informs.** The size of the stacked-fund line, and — more importantly — *what has
to be believed* for any size to be right. It is **not** a recommendation on the repository's
behalf: [decision 0004](../decisions/0004-no-sleeve-promoted.md)'s non-promotion and its
zero-leverage default both stand, and
[decision 0009](../decisions/0009-blocks-lifted-and-closures-rescoped.md) clause 3 unblocks the
*measurement* of the funding rule and nothing else.

**Out of scope.** Which wrapper to buy — the tournament shows the return evidence cannot
separate RSST, MATE and JPFP. The exposure arithmetic, the financing stack and the two
holdability routes, which are
[leverage and the notional budget](leverage-and-the-notional-budget.md)'s. Whether trend has a
premium at all, which is [trend and managed futures](trend-marginal-value.md)'s,
[live managed futures](live-managed-futures.md)'s and now
[the adversarial review](adversarial-review.md) §1's; this page takes their answers as a
**weighted range on one stated basis** and shows what the decision does across it.

`as of 2026-08-22`. Every figure regenerates from
[`studies/trend_weight_regret.py`](../../research/src/portfolio_edge/studies/trend_weight_regret.py)
via `cd research && uv run python -m portfolio_edge.studies.trend_weight_regret`; the closed
forms and the minimax identity are pinned in
`research/tests/unit/test_studies_trend_weight_regret.py` against independently computed
fixtures. **No experiment was registered and no ledger entry was written**: this is a decision
surface over quantities other pages measured.

> **Correction, and it moved the answer.** The first version of this page entered the
> repository's 1.80 pp/yr convention on a gross arithmetic axis.
> [The adversarial review](adversarial-review.md) §1 traced that figure: it is AQR TSMOM's own
> 2012–2025 **geometric** mean **net of a 1.50% fee** that this page's cost term already
> charges. §1.1 reconstructs it from the pinned file and closes the arithmetic exactly. The
> prior below is rebuilt on one stated basis, two independent out-of-window constructions are
> added, and **the recommendation moves from 20% to 25%.** §8 records what changed and what
> did not.

---

## Conclusion

1. **No weight is demonstrably right, and the reason is precise rather than vague.** On the
   corrected prior, against the investor's own unlevered portfolio, every decision rule this
   page can build — minimax regret, minimum expected regret, with and without the investor's
   own capitulation priced inside the path, under every reweighting tried — returns **0.28 to
   0.40**. Against a leverage-matched control at this panel's realised equity premium, every
   one of them returns **0.00 to 0.12**. **The entire disagreement is a choice of comparator,
   not a measurement**, and at a 30% weight it would take **154 years** of holding before this
   instrument could adjudicate it. §2, §3.

2. **Minimax regret does not escape the prior. It relocates it, and the identity says exactly
   where.** Regret is convex in the premium, so max regret sits at an endpoint of the stated
   range; equating the endpoints and applying the envelope theorem gives
   `w_minimax = [G*(m_hi) − G*(m_lo)] / (m_hi − m_lo)`, **the average of the weights that would
   have been optimal, under a uniform prior on the range**. A minimax rule swaps a forecast of
   the premium's *mean* for a forecast of its *endpoints*. **The basis correction is the
   cleanest possible demonstration of this**: it moved the prior's median by 2.10 pp and its
   mean by 1.34 pp and left the full-support minimax weights *exactly* unchanged, because it
   moved no endpoint. §2, §8.

3. **The defensible range for the forward premium is `0.00%` to `10.98%/yr` gross arithmetic**
   per unit of trend notional at this panel's 12.38% trend volatility — `[−1.17%, +9.81%]` net
   of the wrapper's 116.5 bp — **with a weighted median of `+2.73%` net and a mean of
   `+3.35%`.** Eight scenarios, each traced to a page and a window, each carrying its
   gross/net and arithmetic/geometric status, three vendor-authored and labelled, two
   independent of the vendor and of the window. **15% of the prior sits at or below zero.**
   §1.

4. **The repository's 1.80 pp/yr convention is the post-publication era, twice transformed,
   and it is not a separate scenario.** `1.80 + 1.50 + ½ × 13.23²/100 = 4.17%/yr`, against a
   measured 4.17% — the reconstruction closes to the last digit. Entering it raw compared a
   geometric figure with an arithmetic break-even **and** subtracted a fee the cost term
   already charges. The subsample's own 95% interval is `[−2.67, +11.00]` and therefore
   contains the 10.98 it was being used to overturn. §1.1.

5. **The leverage-matched verdict is mostly a statement about the *equity* premium.** At this
   panel's realised 9.82%/yr the trend leg needs **7.68%/yr gross** to beat levering the index
   at a 30% weight, and the minimax weight is 0.12. At
   [decision 0004](../decisions/0004-no-sleeve-promoted.md)'s own 5.00% working figure it needs
   **2.86%** and the minimax weight is **0.30**. At the valuation-proxy mapping's 1.50% it needs
   a *negative* net premium and the minimax weight is the grid ceiling. **Haircutting the trend
   leg to a forward mean while holding the equity leg at its realised one is not a consistent
   comparison.** §2a.

6. **The two errors are asymmetric, they point in opposite directions, and the abandonment arm
   is now almost entirely conditional on the premium being gone.** At the prior's median, a 30%
   weight ends the position in **17.2%** of thirty-year paths at a −20% relative-drawdown
   trigger; at the prior's floor, in **66.7%**. Holding 0% through the panel's one
   flat-to-negative equity decade — **1999-03…2009-02, −2.55%/yr** — forgoes **+2.21 pp/yr** at
   30% and **+1.49** at 20%, against **+0.83** in every other decade. **The position's
   holdability and its return are a bet on the same parameter, which is not a diversification
   of the risk but the same risk twice.** §4, §5.

7. **The exchange-rate argument no longer identifies a cut-off below 30%, and that is the
   largest consequence of the correction.** Priced per percentage point of abandonment
   probability, each step up the ladder now buys **174, 9.18, 3.49, 2.45, 1.81, 1.42 and
   1.06 bp/yr**. On the understated basis the same column fell below 1.0 by `w = 0.20` and was
   read as an elbow; it no longer does. **The `0.20 → 0.30` trade is now +31 bp/yr of expected
   growth for +15 points of abandonment probability — about 2.1 bp per point, against 0.86 before.**
   §4b.

8. **Sized answer: 25% of capital in the wrapper, robust over 20–30%, and 30% is no longer
   excluded.** Nothing in the corrected growth-and-regret arithmetic argues below 0.28 on the
   investor's own benchmark. What still argues lower is the **premium-free** holdability
   evidence in [the notional budget](leverage-and-the-notional-budget.md) — a tracking-error
   route and a CAPE-41 conditioned drawdown route landing at 15–25% — which the basis error
   never touched. **25% is the only weight both routes admit.** §6. **The published weight is
   30%**, which this page's own robust range admits and none of its four routes selects; it
   is set in [part A](portfolio-for-one-investor.md) §2 on Experiment 016e's one resolvable
   whole-portfolio comparison, and [the recommendation](portfolio-recommendation.md) records
   what that comparison does and does not isolate.

9. **Cost is not what decides this.** Every gap depends on the premium and the cost only
   through their difference, so the whole taxable-versus-sheltered question — RSST's 32 bp/yr
   of distribution drag — is a **32 bp translation of the premium axis** and moves no minimax
   weight by more than the grid spacing. §7.

---

## 0. The panel, and why it is the tournament's

US equity is Ken French `Mkt-RF`; the trend leg is AQR's `TSMOM`; cash is French's `RF`. The
window is **1990-11…2026-05, 427 months**, which is
[the tournament](construction-tournament.md)'s and was chosen by the data rather than by
anyone. Using the same window on the same two series means this page's disagreement with the
tournament is a disagreement about a **prior** and never about a sample.

| | excess of cash | volatility |
| --- | ---: | ---: |
| equity `Mkt-RF` | **9.82%/yr** | 15.11% |
| trend `TSMOM` | **10.98%/yr** | 12.38% |
| correlation | **−0.1559** | |
| mean cash rate | 2.57%/yr | |

The 10.98% is the tournament's own input. The decay, recomputed from the same pinned file
rather than quoted:

| era | months | arithmetic excess | volatility | Sharpe |
| --- | ---: | ---: | ---: | ---: |
| 1985-01…2011-12, pre- and at publication | 324 | **+16.09%** | 11.98% | **1.343** |
| 2012-01…2025-12, post-publication | 168 | **+4.17%** | 13.23% | **0.315** |
| 2019-07…2025-12, the live-fund overlap | 78 | **+1.95%** | 13.86% | **0.141** |

These reproduce [live managed futures](live-managed-futures.md) §3 exactly.
[The adversarial review](adversarial-review.md) reproduces the same post-2008 decay on two
constructions this vendor never touched — its own 4-asset book runs Sharpe 0.87 over 1990–2008
and 0.17 over 2009–2025, the JST book 0.55 then 0.19 — **and also records a 1960s decade at
Sharpe 0.07 followed by one at 0.80.** The decay is real, it is not a vendor artefact, and a
fifteen-year dry spell is inside this strategy's historical range of behaviour. That is why
`premium gone` carries 0.15 of the prior below rather than the 0.25 it carried before.

**The one thing to keep in view.** `TSMOM` is a vendor series, authored by a firm that sells
the strategy, rebuilt in full on every update, stating no fee, transaction-cost, slippage or
financing basis anywhere, and therefore **gross of the vendor's own trading costs by
omission**. Three of the eight scenarios below inherit that and are labelled.

---

## 1. The prior, on one stated basis

> **Basis: gross arithmetic excess over cash, per unit of trend notional, at this panel's
> 12.38% trend volatility.** That is what the growth model consumes. Every row is on it and
> every row says so — the labels exist because the error §1.1 records was invisible without
> them.

**One uncertain parameter.** Every gap depends on the forward gross premium `p` and the retail
cost `c` only through their difference, so the axis is `m = p − c`. `c = 1.165%/yr` — 99 bp of
RSST fee plus 20.5 bp of equity-index-futures basis on the 0.331 of financed notional it
carries, less VTI's 3 bp, from
[the notional budget](leverage-and-the-notional-budget.md) §4. §7 sweeps it.

**Two rescalings, both explicit.** A Sharpe measured at another volatility is multiplied by
12.38%, preserving the Sharpe — the right invariant when the volatility of the delivered
exposure changes. A fund's own fee is added back before the wrapper's fee is charged, so no fee
is counted twice.

| scenario | gross | **net `m`** | weight | vendor | basis | what it rests on |
| --- | ---: | ---: | ---: | --- | --- | --- |
| premium gone | 0.00% | **−1.17%** | 0.15 | no | forecast | [Exp 004](trend-marginal-value.md)'s post-publication sleeve is **+0.883 pp/yr, 95% `[−0.175, +2.165]`**, failing Holm; the standalone Sharpe fell 1.34 → 0.18; clause (d)'s replica reproduces **43.7%** for no fee |
| vendor, most recent 78 months | 1.74% | +0.58% | 0.10 | **yes** | gross arith. | `TSMOM` 2019-07…2025-12, Sharpe 0.141, rescaled |
| live funds ex vendor-run, net of fees | 3.70% | +2.53% | 0.15 | no | gross arith. | [Exp 012](live-managed-futures.md)'s 41-fund arm, +1.99%/yr at 8.68% vol, rescaled, median 85 bp shelf fee added back |
| **vendor post-publication era = the restated convention** | 3.90% | **+2.73%** | 0.15 | **yes** | gross arith. | `TSMOM` 2012-01…2025-12, Sharpe 0.315, rescaled. **This is also decision 0004's 1.80 once its basis is undone** (§1.1), so the two are one scenario |
| live funds, headline index | 4.92% | +3.76% | 0.10 | no | gross arith. | [Exp 012](live-managed-futures.md)'s 46-fund index, +2.84%/yr at 8.64% vol, same treatment |
| independent 36-leg JST book, 1880–2020 | 5.32% | +4.16% | 0.10 | **no** | gross arith. | [Adversarial review](adversarial-review.md) §1: 18 JST countries, equity and bonds, 141 annual observations, **Sharpe 0.43, `t` = 6.59**, on this repository's frozen `time_series_momentum` |
| **independent 4-asset book, 1929–2025** | 7.18% | +6.02% | 0.15 | **no** | gross arith. | [Adversarial review](adversarial-review.md) §1: **1,157 months, Sharpe 0.58, `t` = 5.48 — and 0.58 in *both* halves**, 1929–1990 and 1990–2025. Charged 20 bp one-way against 262% turnover it falls to 6.19% |
| full-window realisation | 10.98% | **+9.81%** | 0.10 | **yes** | gross arith. | `TSMOM` 1990-11…2026-05, the number every trend figure in the tournament rests on |

**Mean `+3.35%`, median `+2.73%`, support `[−1.17%, +9.81%]`, `P(m < 0) = 0.15`.**

**Four things about this table matter more than its numbers.**

**The independent constructions are the strongest evidence in it and they were absent before.**
The 4-asset book runs Sharpe 0.58 over 1929–1990, 0.58 over 1990–2025 and 0.58 over the whole
96 years, at `t = 5.48`. **That stability says the tournament's 427-month window is
representative** — the window is not the problem for trend, and a premium *is* resolvable once
the instrument is long enough. Neither book is a product: no trading cost is charged in the
headline figure, there is no capacity constraint, four legs against a vendor's fifty-eight
understates by the breadth identity, and the JST book's annual data with a one-year lookback is
a coarser signal than monthly. They are weighted for what they are.

**The fee add-back is not optimism, it is the avoidance of a double charge.** The live index is
already net of each fund's fee, trading costs and slippage. An investor obtaining trend through
RSST pays *RSST's* fee, which is inside `c`, not DBMF's. The two live scenarios are
consequently the only ones in which implementation costs have actually been paid by anybody.

**Three scenarios are gross of the vendor's own trading costs by omission** and the two
independent books are gross of theirs. The only trading-cost estimate anywhere in the prior is
the review's 20 bp one-way charge on its own book, which moves that row from 7.18% to 6.19%.

**The weights are a judgement.** §2c sweeps them, including a weighting with every
vendor-authored row removed. **The support, not the weights, is what a minimax rule reads.**

### 1.1 Where 1.80 pp/yr came from, reconstructed

**Traced by [the adversarial review](adversarial-review.md) §1 and reconstructed here from the
pinned file.** The only source in the repository is one sentence in
[decision 0004](../decisions/0004-no-sleeve-promoted.md): *"a post-publication trend excess
return this repository measures at roughly 1.8 pp/yr"* — no window, no estimator, no interval.
It is:

| AQR TSMOM 2012-01…2025-12, 168 months | |
| --- | ---: |
| arithmetic excess | 4.17%/yr |
| volatility | 13.23%/yr |
| **geometric excess** | **3.35%/yr** |
| less [Exp 004](trend-marginal-value.md)'s stated 1.50% management fee | **1.85%/yr** |
| decision 0004 records | **1.80%** |

**Undoing both steps returns the era's own arithmetic mean exactly:**
`1.80 + 1.50 + ½ × 13.23²/100 = 4.17%/yr`, against the measured **4.17%**. Sharpe-preserving
rescale to this panel's 12.38% volatility: **3.90%/yr**.

**Three errors followed from entering it raw on a gross arithmetic axis**, and this page
committed the third:

1. **A geometric figure compared with an arithmetic break-even.** The `½σ²` term is 0.88 pp.
2. **A 1.50% management fee subtracted twice** — once inside the figure, once inside the
   wrapper's 99 bp expense ratio that the cost term already charges.
3. **A point estimate used with no error bar.** The subsample's own 95% interval is
   `[−2.67, +11.00]` and **contains the 10.98 it was being used to overturn.**

Consequently the tournament's finding 11 — that at the repository's forward premium the overlay
subtracts — inverts. The like-for-like haircut is **6.91 pp/yr, not 9.18**, against a break-even
of 8.02, and [the review](adversarial-review.md) §1 re-runs the frozen tournament to give
`proposal_rsst` **+0.34** rather than −0.35. **The correct statement is not that the overlay
subtracts at the repository's own premium; it is that the sign is decided inside an interval
nobody can narrow.**

---

## 2. The regret surface

Cells are annual after-cost log-growth gaps in basis points. Regret at `(w, m)` is the gap the
**best weight available on the same grid** would have earned at that `m`, less the gap `w`
earns. The action space is `0.00` to `0.40` in steps of `0.02`; §2b reports how much of the
answer that ceiling decides.

**Benchmark A — the investor's own unlevered portfolio.** The question "should I put this in
the wrapper instead of holding my index fund".

| `w` | E[growth] | max regret | E[regret] | −1.17% | +0.58% | +2.53% | +2.73% | +3.76% | +4.16% | +6.02% | +9.81% |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.00 | 0 | 392 | 140 | −0 | +0 | +0 | +0 | +0 | +0 | +0 | +0 |
| 0.10 | 36 | 292 | 105 | −9 | +8 | +27 | +29 | +40 | +44 | +62 | +100 |
| 0.20 | 70 | 193 | 71 | −21 | +14 | +53 | +57 | +78 | +86 | +123 | +199 |
| 0.30 | 102 | 96 | 38 | −33 | +19 | +78 | +84 | +115 | +127 | +182 | +296 |
| 0.40 | 133 | **47** | **7** | −47 | +22 | +101 | +109 | +150 | +166 | +240 | +392 |

**Minimax-regret weight 0.36** (0.357 in closed form), max regret **41 bp/yr**, robust over
0.36–0.40. **Minimum-expected-regret weight 0.40.** Break-even at `w = 0.30` is `m = −0.06%`,
a **gross premium of 1.10%/yr** — inside
[the notional budget](leverage-and-the-notional-budget.md) §4.1's independently derived
0.98%–2.31% break-even band, from a different code path.

**Benchmark B — the cheap index levered to `1 + w`, charged the same 62 bp financing basis**,
which [decision 0009](../decisions/0009-blocks-lifted-and-closures-rescoped.md) clause 3 makes
mandatory for a funding-rule result. Equity held at this panel's realised 9.82%/yr.

| `w` | E[growth] | max regret | E[regret] | −1.17% | +0.58% | +2.53% | +2.73% | +3.76% | +4.16% | +6.02% | +9.81% |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.00 | 0 | **133** | **13** | +0 | +0 | +0 | +0 | +0 | +0 | +0 | +0 |
| 0.10 | −32 | **101** | 46 | −78 | −60 | −41 | −39 | −28 | −24 | −6 | +32 |
| 0.20 | −64 | 154 | 77 | −154 | −120 | −80 | −76 | −56 | −48 | −11 | +65 |
| 0.30 | −95 | 230 | 108 | −230 | −178 | −119 | −113 | −83 | −71 | −15 | +99 |
| 0.40 | −125 | 306 | 138 | −306 | −236 | −158 | −150 | −109 | −93 | −18 | +133 |

**Minimax-regret weight 0.12** (0.122), max regret **95 bp/yr**, robust over 0.10–0.12.
**Minimum-expected-regret weight 0.00.** Break-even at `w = 0.30` is `m = +6.51%`, a **gross
premium of 7.68%/yr** — a haircut of **3.30 pp/yr** from `TSMOM`'s realised 10.98. Note that
the independent 1929–2025 book's 7.18% sits just below that break-even and the top of its own
95% interval, 9.75%, sits above it.

**Two benchmarks, never added.** The charter forbids combining results measured against
different comparators. What the page shows is that the two answers — 0.36 and 0.12 — **bracket
the investor's 30% from opposite sides**, and that everything between them is decided by which
question is being asked.

### 2a. The leverage-matched verdict is mostly a statement about equity

`gap_matched = gap_index − w (a_e − f − sigma_e²) + w² sigma_e² / 2`. The term separating the
two benchmarks **contains no property of the trend leg except its weight** — pinned as a test —
so the equity premium drives it entirely.

| forward equity premium | break-even `m` at `w = 0.30` | gross-equivalent | minimax `w` |
| --- | ---: | ---: | ---: |
| **realised on this panel, 9.82%** | +6.51% | 7.68% | **0.12** |
| [decision 0004](../decisions/0004-no-sleeve-promoted.md)'s working figure, 5.00% | +1.69% | 2.86% | **0.30** |
| the valuation-proxy mapping, [notional budget](leverage-and-the-notional-budget.md) §2, 1.50% | **−1.81%** | −0.65% | **0.40** |

**A forward view that cuts one leg by 84% and none of the other is not a forward view.** Applied
consistently, the leverage-matched control stops arguing for a small trend weight and starts
arguing for a large one, because a low forward equity premium makes levering equity the
expensive way to buy exposure. The tournament's arms are basis-mapped constructions on a 65/35
global blend rather than on US `Mkt-RF`, so the two are not the same instrument, but the
direction of the correction does not depend on that.

### 2b. What the endpoints and the ceiling decide

Minimax regret reads **only** the endpoints of the support, by the identity in conclusion 2.
So the support is the assumption:

| support | `m` range | minimax, A | minimax, B |
| --- | --- | ---: | ---: |
| full | `[−1.17%, +9.81%]` | 0.357 | 0.122 |
| excluding the full-window realisation | `[−1.17%, +6.02%]` | 0.334 | 0.000 |
| excluding the independent constructions too | `[−1.17%, +3.76%]` | 0.304 | 0.000 |
| **vendor evidence removed entirely** | `[−1.17%, +6.02%]` | **0.334** | 0.000 |
| a zero floor rather than a negative one | `[+0.00%, +9.81%]` | 0.397 | 0.136 |
| independent constructions only | `[+4.16%, +6.02%]` | 0.400 | 0.000 |

And the action space is the other assumption:

| ceiling on `w` | minimax, A | minimax, B |
| ---: | ---: | ---: |
| 0.30 | 0.270 | 0.090 |
| 0.40 | 0.357 | 0.122 |
| 0.60 | 0.527 | 0.186 |
| 1.00 | 0.851 | 0.324 |

**Against the investor's own portfolio the minimax weight tracks the ceiling almost one for
one: it is reporting the grid, not the data.** That is the tournament's finding 6 restated —
with a correlation of −0.156 the marginal hurdle on the first unit of trend notional is
**−29 bp/yr**, so growth wants more of it than any investor would hold and the constraint is
always the cap. **The row that matters most is "vendor evidence removed entirely": at 0.334 it
is barely below the full-support answer, so the conclusion no longer depends on the vendor at
all.**

### 2c. The prior's weights, swept

| weighting | E[`m`] | support | A: minimax / Bayes | B: minimax / Bayes |
| --- | ---: | --- | ---: | ---: |
| as stated | +3.35% | `[−1.17%, +9.81%]` | 0.36 / 0.40 | 0.12 / 0.00 |
| **all mass on decay** | +0.44% | `[−1.17%, +2.73%]` | **0.28** / 0.40 | 0.00 / 0.00 |
| no weight on the full-window realisation | +2.63% | `[−1.17%, +6.02%]` | 0.34 / 0.40 | 0.00 / 0.00 |
| uniform over the eight | +3.55% | `[−1.17%, +9.81%]` | 0.36 / 0.40 | 0.12 / 0.00 |
| vendor evidence removed entirely | +2.95% | `[−1.17%, +6.02%]` | 0.34 / 0.40 | 0.00 / 0.00 |
| independent constructions only | +5.27% | `[+4.16%, +6.02%]` | 0.40 / 0.40 | 0.00 / 0.00 |
| all mass on the live-fund evidence | +3.15% | `[+2.53%, +3.76%]` | 0.40 / 0.40 | 0.00 / 0.00 |

**The most pessimistic reweighting available now returns 0.28, where before the correction it
returned 0.14.** That is the single largest movement the basis fix produced, and it is not a
movement in an endpoint — it is a movement in the *top of the pessimistic support*, which was
being held down by the mis-stated 1.80.

**Minimum expected regret is bang-bang under every weighting tried**, because expected growth
is linear in `E[m]` less a fixed variance drag. **Neither classical decision rule produces an
interior weight out of the growth arithmetic.**

---

## 3. Resolution: the verdict may not outrun the instrument

[Decision 0010](../decisions/0010-bars-carry-a-reopening-condition.md) requires this before any
of the above may be read as evidence rather than as arithmetic.

| `w` | `m` | gap vs the cheap index | MDE₈₀ | years to resolve |
| ---: | ---: | ---: | ---: | ---: |
| 0.20 | +2.73% (median) | 0.57%/yr | 1.16%/yr | **146** |
| 0.20 | +3.35% (mean) | 0.70% | 1.16% | 99 |
| 0.20 | +9.81% | 1.99% | 1.16% | 12 |
| 0.30 | +2.73% | 0.84% | 1.74% | **154** |
| 0.30 | +3.35% | 1.02% | 1.74% | 103 |
| 0.30 | +9.81% | 2.96% | 1.74% | 12 |

**Effective sample size: 427 months at a 24-month block is about 18 independent observations,
and the decade tables below contain about 4 distinct decades.** The correction cut the years to
resolve by a factor of sixteen — 2,479 became 154 — and **154 years is still not a human
investing horizon.** Every number on this page is a decision aid, not a detection.

---

## 4. The asymmetry, arm one: the position ends before the premium arrives

The rule: sell the sleeve the first month relative wealth sits a stated distance below its own
running peak, then hold the control for good. 4,000 joint 24-month block resamples, 30-year
horizon, both arms drawn on the same history. **The trigger is an input, not an estimate** —
nothing in this repository measures a real investor's capitulation threshold, and fitting one
inside an optimiser would manufacture the quantity the design exists to expose. Read −20%
against [the notional budget](leverage-and-the-notional-budget.md) §6a's measured central-case
worst relative run of −21.3%.

At a −20% trigger, `P(the position is sold)` over thirty years:

| `w` | `m = −1.17%` (floor) | `m = +2.73%` (median) | `m = +3.35%` (mean) |
| ---: | ---: | ---: | ---: |
| 0.10 | 0.6% | 0.0% | 0.0% |
| 0.15 | 10.8% | 0.3% | 0.1% |
| **0.20** | **31.8%** | **2.0%** | **1.1%** |
| 0.25 | 50.7% | 7.6% | 4.4% |
| **0.30** | **66.7%** | **17.2%** | **12.1%** |
| 0.40 | 86.2% | 43.3% | 35.2% |

**The correction changed this table more than any other on the page.** At `w = 0.30` and the
prior's median, abandonment fell from **42.3% to 17.2%**. Median time to the sale at the median
premium is now 18.1 years at `w = 0.30` and 22.5 at `w = 0.20`.

**Two readings survive it.**

> **Quitting truncates both tails, and it truncates the good one hardest.** At a negative
> premium abandonment *saves* money (−32 bp/yr held becomes −21 bp/yr after quitting at
> `w = 0.30`); at a positive one it costs (84 → 78). A growth-only surface cannot see this and
> neither can a Sharpe ratio.

> **Holdability and return are now a bet on the same parameter.** Abandonment risk at 30% runs
> 66.7% if the premium is gone and 17.2% if it is the prior's median. **That is not a
> diversification of the risk; it is the same risk twice**, and it is an argument for restraint
> that does not depend on the point estimate.

### 4a. The regret surface with capitulation inside the path

| trigger | benchmark | full support | support without the full-window realisation |
| ---: | --- | --- | --- |
| −15% | A | minimax 0.40 | minimax 0.40, robust 0.30–0.40 |
| −20% | A | minimax 0.40 | minimax 0.40, robust 0.35–0.40 |
| −30% | A | minimax 0.40 | minimax 0.35, robust 0.35–0.40 |
| −15% / −20% | B | minimax 0.40 | **minimax 0.00** |
| −30% | B | minimax 0.10 | **minimax 0.00** |

**Pricing capitulation does not produce an interior optimum on the corrected axis.** It
flattens the top of the ladder — at the prior's median, growth after abandonment runs 44, 57,
69, 78, 85, 87 bp/yr across `w = 0.15 … 0.40`, so the last twenty-five points of notional are
worth **43 bp** — but minimax reads endpoints, and the top endpoint is three and a half times
the median.

### 4b. The marginal trade

Each step up the ladder, priced twice: the expected growth it buys under the prior with
capitulation inside the path, and the abandonment probability it buys. Trigger −20%,
benchmark A.

| step | E[growth] | Δ growth | `P(quit)` | Δ `P(quit)` | **bp per point** | *(before the correction)* |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.05 → 0.10 | 36 bp | +17.6 | 0.1% | +0.1 pp | **174.2** | *62.8* |
| 0.10 → 0.15 | 53 bp | +17.3 | 2.0% | +1.9 pp | **9.18** | *3.29* |
| 0.15 → 0.20 | 70 bp | +16.9 | 6.8% | +4.9 pp | **3.49** | *1.25* |
| 0.20 → 0.25 | 86 bp | +16.2 | 13.5% | +6.6 pp | 2.45 | *0.95* |
| 0.25 → 0.30 | 101 bp | +14.8 | 21.7% | +8.2 pp | 1.81 | *0.76* |
| 0.30 → 0.35 | 114 bp | +12.9 | 30.8% | +9.1 pp | 1.42 | *0.67* |
| 0.35 → 0.40 | 124 bp | +10.3 | 40.5% | +9.7 pp | **1.06** | *0.55* |

**On the understated basis this column fell below 1.0 by `w = 0.20` and was read as an elbow.
It no longer does: every step from 0.15 to 0.40 still buys more than one basis point a year per
percentage point of abandonment risk.** The steep fall is now entirely inside 0.05–0.15.
**Stated as one move: `0.20 → 0.30` buys 31 bp/yr of expected growth and 15 percentage points
of abandonment probability — about 2.1 bp per point, against 0.86 on the old axis.** This is the
largest single consequence of the correction for the recommendation, and it argues the weight
*up*.

---

## 5. The asymmetry, arm two: the decade the sleeve exists for

Every overlapping ten-year window, split on how the *equity* decade went. The windows overlap
heavily, so these are not independent observations, no interval is offered, and the panel
holds about four distinct decades.

| `w` | `m` | worst equity decade | equity | candidate | mean gap, worst decile | mean gap, elsewhere |
| ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 0.20 | −1.17% | 1999-03…2009-02 | −2.55%/yr | −1.58% | **+0.71%** | −0.20% |
| 0.20 | +2.73% | 1999-03…2009-02 | −2.55% | −0.80% | **+1.49%** | +0.57% |
| 0.20 | +3.35% | 1999-03…2009-02 | −2.55% | −0.68% | +1.61% | +0.69% |
| 0.30 | −1.17% | 1999-03…2009-02 | −2.55% | −1.12% | **+1.04%** | −0.33% |
| 0.30 | +2.73% | 1999-03…2009-02 | −2.55% | **+0.05%** | **+2.21%** | +0.83% |
| 0.30 | +3.35% | 1999-03…2009-02 | −2.55% | +0.24% | +2.40% | +1.02% |

**At a 30% weight and the prior's median the overlay turns the worst equity decade in the panel
from −2.55%/yr into +0.05%/yr** — it removes the lost decade rather than softening it. The
overlay is worth roughly two and a half times as much in the worst equity decile as elsewhere,
**and it is worth something there even when the premium is zero** (`+0.71%` at 20% and `+1.04%`
at 30% at `m = −1.17%`), entirely from the correlation.

The named episodes, peak-to-trough drawdown over the frozen windows in
[the evidence base](evidence-base.md), trend restated to the prior's median so the table prices
the **correlation** rather than the realised mean:

| episode | months | equity | `w = 0.20` | `w = 0.30` |
| --- | ---: | ---: | ---: | ---: |
| 2000-02 dotcom | 30 | −45.0% | −41.5% | −39.8% |
| 2007-09 GFC | 16 | −48.0% | −45.6% | −44.5% |
| 2020 Q1 covid | 2 | −13.3% | −11.6% | −10.7% |
| 2022 inflation | 10 | −20.5% | −19.1% | −18.5% |

**1929-32, 1937-38 and 1973-74 are outside this window by construction** — the panel starts
1990-11 — so the crisis-decade arm rests on one bad decade and two bad episodes. That limit
cuts against arm two and is the single largest weakness on this page. The
[adversarial review](adversarial-review.md)'s 1929–2025 book reaches those years and finds the
same Sharpe in both halves, which is reassurance about the *premium* and not about the
*crisis-conditional correlation*, which nobody here has measured over that span.

**The two arms answer the question directly and they do not agree.** Being wrong by holding 30%
when the premium is gone costs roughly 21–32 bp/yr and ends the position two thirds of the
time. Being wrong by holding 0% when the premium is real costs **1.49–2.21 pp/yr in the decade
the investor most needs it** — an order of magnitude larger, in the state that decides whether
the plan survives. **What both arms agree on is that zero is the worse of the two extremes**,
and the correction widened that gap rather than narrowing it.

---

## 6. The outcome distribution, and the sized answer

At the prior's median premium, 4,000 joint 24-month block resamples:

| `w` | benchmark | horizon | `P(underperform)` | p5 / median / p95 relative wealth | median drawdown | p5 |
| ---: | --- | ---: | ---: | --- | ---: | ---: |
| 0.20 | cheap index | 10 yr | **24.9%** | 0.929 / 1.057 / 1.217 | −24.9% | −50.6% |
| 0.20 | cheap index | 20 yr | 15.8% | 0.935 / 1.122 / 1.356 | −37.1% | −56.8% |
| 0.20 | cheap index | 30 yr | 10.9% | 0.948 / 1.190 / 1.493 | −43.5% | −60.4% |
| 0.30 | cheap index | 10 yr | **25.3%** | 0.894 / 1.084 / 1.339 | −24.0% | −49.7% |
| 0.30 | cheap index | 20 yr | 16.7% | 0.899 / 1.183 / 1.571 | −35.8% | −55.1% |
| 0.30 | cheap index | 30 yr | 11.5% | 0.917 / 1.288 / 1.809 | −42.3% | −58.9% |
| 0.20 | leverage-matched | 10 / 20 / 30 yr | **69.7 / 76.8 / 80.5%** | 0.534 / 0.792 / 1.264 at 30 yr | −43.5% | −60.4% |
| 0.30 | leverage-matched | 10 / 20 / 30 yr | **69.5 / 76.5 / 80.2%** | 0.391 / 0.707 / 1.427 at 30 yr | −42.3% | −58.9% |

Tracking error is `w × 12.38%`: **2.48%/yr at 0.20 and 3.71%/yr at 0.30**, reproducing
[the notional budget](leverage-and-the-notional-budget.md) §6a's 3.74% from a different panel.
Note that against a leverage-matched control the position still underperforms in four fifths of
thirty-year histories at the prior's median, and that comparison does not move with the weight.

**The rule.**

> **Hold 25% of capital in the stacked wrapper — 0.25 of trend notional, 1.25× gross — and
> understand that the binding constraint is holdability, not the premium.**

**25% is not the minimax-regret weight on either benchmark and this page does not pretend it
is.** Benchmark A's is 0.36 and benchmark B's is 0.12; the charter forbids averaging results
measured against different comparators. 25% is the weight at which the two *surviving*
constraints overlap:

| route | what it constrains | answer | depends on the premium? |
| --- | --- | ---: | --- |
| this page's regret surface, benchmark A | expected growth against the investor's own portfolio, under every reweighting tried | **0.28–0.40** | yes |
| this page's regret surface, benchmark B | growth against a leverage-matched control at the realised equity premium | 0.00–0.12 | yes, and on the *equity* premium |
| [notional budget](leverage-and-the-notional-budget.md) §6a, tracking error | how long a stretch of relative underperformance is holdable | 15–25% | **no** |
| [notional budget](leverage-and-the-notional-budget.md) §3.2, CAPE-41 drawdown | how deep an absolute loss is holdable | **19.1%** at a −50% tolerance | **no** |

**Robust over 20% to 30%, and 30% is no longer excluded.** It sits inside benchmark A's robust
band, it is exactly the leverage-matched minimax weight at
[decision 0004](../decisions/0004-no-sleeve-promoted.md)'s own 5.00% equity premium, and its
abandonment probability at the prior's median is 17% rather than the 42% the old axis produced.
Below 20% the investor gives up more than a percentage point a year in the decade the sleeve
exists for, for a step whose exchange rate is the best on the ladder.

**Not a repository recommendation.** [Decision 0004](../decisions/0004-no-sleeve-promoted.md)'s
non-promotion and zero-leverage default are untouched.

### 6.1 What would change it

1. **RSST's measured loading on a trend benchmark.** Never estimated anywhere here. Every
   premium above is per unit of *exposure*; if the fund delivers 0.7 of a unit per dollar, the
   same delivered exposure needs a larger capital weight and the same capital weight buys a
   smaller premium. **The single largest unmeasured quantity in the decision**, and it needs a
   licensed total-return series
   ([decision 0002](../decisions/0002-no-research-grade-free-price-source.md)).
2. **A trading-cost model for the independent constructions.** They now carry 0.25 of the prior
   between them and only one cost sensitivity exists (20 bp one-way, moving 7.18% to 6.19%).
   A capacity and market-impact model would be the cheapest way to firm up the upper half of
   the range.
3. **The live-fund panel, survivorship-corrected and extended.** Two scenarios carrying 25% of
   the prior rest on 78 months with a hole that deletes funds from inside the window.
4. **The fund-level financing spread**, which
   [the notional budget](leverage-and-the-notional-budget.md) §4.1 shows decides the *sign* at
   the low end and which no filing discloses.
5. **The forward equity premium**, which moves the leverage-matched minimax weight from 0.12 to
   0.40 across the three anchors this repository already holds (§2a).

### 6.2 The monitoring boundary

**Monitor the evidence, on a calendar, not the price.**

- **Annually**, refresh [Experiment 012](live-managed-futures.md)'s census and recompute the
  live-fund index's excess net of fees, vol-matched to the trend leg. **Halve the sleeve if it
  sits below the wrapper's all-in cost per unit of trend notional for three consecutive annual
  refreshes.** Three, not one: a single reading on 78 months cannot distinguish a drought from
  a death, and §3 says so quantitatively — as does the review's 1960s decade at Sharpe 0.07
  followed by one at 0.80.
- **Remove the sleeve** if RSST's measured trend loading comes in below 0.7, or if the
  wrapper's all-in cost per unit of trend notional exceeds 2.0%/yr — at which point the
  break-even passes the prior's median.

  **That loading has now been measured, and the rule as written does not resolve.** From
  RSST's own Form N-PORT returns it is **+0.681 [+0.406, +0.955]** over 31 months to
  2026-04 ([comparability](loading-comparability-and-wrapper-exposure.md)). The point
  estimate is 0.019 below the trigger and the 95% interval contains both 0.7 and 1.0, on a
  window whose smallest detectable loading is 0.392. Firing a removal rule on a point
  estimate that its own instrument cannot separate from the bar would be the underpowered
  null read as evidence, which is the error this page exists to avoid; and moving the bar
  after seeing the number would be worse. The rule is recorded as **not resolved by this
  measurement** and stays as written. It becomes decidable when the interval clears 0.7 in
  one direction, which needs roughly two more years of filings — review when RSST's filed
  history reaches 48 months, around 2027-09.
- **Do not monitor on relative drawdown.** A rule that cuts after a relative loss is the
  failure mode [the notional budget](leverage-and-the-notional-budget.md) §7 priced from the
  fund's side: cutting the overlay after a loss costs 0.22–0.59 pp/yr **and** deepens the
  maximum drawdown by 1.3–2.9 pp, because the sleeve is removed for exactly the part of the
  path where it would have paid. §4 shows the same shape from the investor's side.
- **A performance review is not a monitoring rule either.** At `w = 0.30` and the prior's
  median, the position underperforms the investor's own portfolio in **25.3%** of resampled
  ten-year histories, and at the prior's floor in **70.8%**. A ten-year review therefore reads
  the premium with about one bit of information, and setting one is a plan to sell after bad
  luck.

---

## 7. Cost, which is a translation and not a decision

| cost per unit of trend notional | shifts every `m` by |
| --- | ---: |
| sheltered, wrapper all-in (central case), 1.165%/yr | — |
| [the notional budget](leverage-and-the-notional-budget.md)'s 96 bp convention | +0.21% |
| taxable, plus RSST's 32 bp of distribution drag | −0.32% |

Because every gap depends on `p` and `c` only through `m = p − c`, **the entire
taxable-versus-sheltered question is a 32 basis point translation of the premium axis**, and it
moves no minimax weight by more than the grid spacing.

---

## 8. What the basis correction changed, and what it did not

| quantity | before | after |
| --- | ---: | ---: |
| prior median, net | +0.63% | **+2.73%** |
| prior mean, net | +2.01% | **+3.35%** |
| `P(m < 0)` | 0.25 | **0.15** |
| **support** | `[−1.17%, +9.81%]` | **unchanged** |
| **minimax `w`, benchmark A, full support** | **0.357** | **unchanged** |
| **minimax `w`, benchmark B, full support** | **0.122** | **unchanged** |
| minimax `w`, A, most pessimistic reweighting | 0.14 | **0.28** |
| years to resolve, `w = 0.30`, at the median | 2,479 | **154** |
| `P(quit)`, `w = 0.30`, at the median, −20% trigger | 42.3% | **17.2%** |
| exchange rate, `0.20 → 0.30` | 0.86 bp/point | **~2.1 bp/point** |
| worst-decile decade gap, `w = 0.30`, at the median | +1.58%/yr | **+2.21%/yr** |
| **recommendation** | 20%, robust 15–25% | **25%, robust 20–30%** |

**The two rows in bold that did not move are the page's own thesis, demonstrated rather than
asserted.** The correction moved the prior's median by 2.10 pp and left both minimax weights
untouched, because minimax regret reads only the endpoints and the correction moved no
endpoint. That is exactly what conclusion 2 says a minimax rule does.

**What was wrong and is retracted.** The first version reached 20% partly on an exchange-rate
elbow that only existed on the understated axis, and it stated the abandonment probability at
`w = 0.30` as 42.3% when the corrected figure is 17.2%. **The "20% over 30%" trade as I
originally quantified it does not survive the correction.** What does survive is the framing —
two benchmarks that bracket the answer, minimax as an endpoint rule, the two-armed asymmetry —
and the premium-free holdability evidence on the sibling page, which is now doing the whole
job of holding the recommendation below the regret surface's own answer.

---

## Verified, assumed, open

**Verified here.** The panel's moments and all three era rows, recomputed from the pinned AQR
and Ken French files and matching [live managed futures](live-managed-futures.md) §3 and the
tournament's 10.98 exactly. **The 1.80 pp/yr reconstruction, which closes to the last
published digit** (§1.1). The leverage-matched closed form, rebuilt in a test from the
definition of log growth — two portfolios' `mean − variance/2`, differenced — sharing no
algebra with the implementation. The break-even as the exact inverse of the gap at five weights
on both benchmarks. The minimax identity, against a brute-force minimax over a 1,001-point
action space and against a 20,001-point numerical average of the optimal weight over the
support. That the term separating the two benchmarks contains no property of the trend leg.
That the capitulation probability rises with the weight, that a trigger which cannot fire
reproduces the held gap exactly, and that a constant-return pair annualises to
`12 log(1+c) − 12 log(1+k)` to 1e-12.

**Assumed.**

1. **The trend leg is `TSMOM`, not RSST.** No loading has ever been measured for the fund, so
   every figure is about the *exposure*.
2. **Three of eight scenarios are vendor-authored and gross of the vendor's own trading costs
   by omission; the two independent books are gross of theirs**, with one 20 bp sensitivity.
3. **The two independent constructions are taken from
   [the adversarial review](adversarial-review.md) §1 rather than recomputed here**, rescaled
   Sharpe-preserving to this panel's trend volatility. They are constructed rules, not
   investable products.
4. **The prior's weights are a judgement.** §2c sweeps them; the support, not the weights, is
   what the minimax answer reads.
5. **The action-space ceiling of 0.40 decides most of the benchmark-A answer.** §2b.
6. **The capitulation trigger is stated, not estimated.**
7. **A block-stationary null** at 24 months, so a 30-year row is an extrapolation of that null.
8. **The correlation is the full-sample −0.156.** The charter's rule applies with force: a low
   average correlation is incomplete evidence about crisis dependence. §5 is the direct
   evidence; [the notional budget](leverage-and-the-notional-budget.md)'s 1934–2025 panel
   measures **+0.011** on a differently constructed trend leg, and this page cannot adjudicate
   between them.
9. **US equity only, nominal, and pre-tax** except in §7.
10. **Log growth is the loss function.** Regret prices terminal wealth and, in §4, the sale of
    the position. It prices no utility over drawdown.

**Open.**

1. **RSST's loading on a trend benchmark**, §6.1 item 1 — the largest unmeasured quantity here.
2. **Trading costs and capacity for the independent constructions**, now 0.25 of the prior.
3. **The pre-2019 live-fund gap**, where a survivorship haircut would actually do its work.
4. **Which correlation is right**, −0.156 here or +0.011 on the longer panel, and what the
   crisis-conditional one is over the 1929–2025 span the review reaches.
5. **A capitulation threshold estimated from anything.** §4's whole arm is a sensitivity to an
   input.

**Reproducibility.** `cd research && uv run python -m portfolio_edge.studies.trend_weight_regret`.
Closed forms and decision rules in
[`studies/trend_weight_regret.py`](../../research/src/portfolio_edge/studies/trend_weight_regret.py);
the cache-touching report in
[`studies/_trend_weight_regret_tables.py`](../../research/src/portfolio_edge/studies/_trend_weight_regret_tables.py);
tests in `research/tests/unit/test_studies_trend_weight_regret.py`. Seed 20260822, 4,000
resamples, 24-month circular blocks.
