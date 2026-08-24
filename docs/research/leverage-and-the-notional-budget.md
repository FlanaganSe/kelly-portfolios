# Leverage and the notional budget: what the candidate portfolio already carries, and what it should

**Question.** The investor says *"I am okay with leverage but it absolutely must be with
purpose and must understand market conditions."* Their candidate portfolio puts 30% of
capital in a stacked ETF. What leverage is that, what leverage does the objective want, what
does the leverage cost, and does any conditioning rule survive?

**Decision it informs.** How large the stacked-fund line should be, against which objective,
and which constraint binds. It is **not** a recommendation on the repository's behalf:
[decision 0004](../decisions/0004-no-sleeve-promoted.md)'s non-promotion and its
zero-leverage default for recommended portfolios both stand, and
[decision 0009](../decisions/0009-blocks-lifted-and-closures-rescoped.md) clause 3 unblocks
the *measurement* of the funding rule and nothing else. Everything below informs a
recommendation that a person still has to make.

**Out of scope.** A forecast of any market. Whether trend has a premium — that question is
[capital efficiency](capital-efficiency-and-breadth.md)'s and
[marginal sleeve value](marginal-sleeve-value.md)'s, and this page takes the answer as a
range and shows the decision's sensitivity to it. The equity/bond split, which is
[setting the equity share](setting-the-equity-share.md)'s. The wrapper structure arithmetic
`delta = (1 − b) / d`, which is [capital efficiency](capital-efficiency-and-breadth.md)'s.

`as of 2026-08-22`. Every measured figure regenerates from
[`studies/notional_budget.py`](../../research/src/portfolio_edge/studies/notional_budget.py)
via `cd research && uv run python -m portfolio_edge.studies.notional_budget`, and every
closed form in it is pinned in `research/tests/unit/test_studies_notional_budget.py` against
an independently computed fixture. **No experiment was registered and no ledger entry was
written**: this is a study, and it adjudicates nothing a frozen specification would have to.

---

## Conclusion

1. **The investor is not taking equity leverage. They are taking 30 points of trend
   notional.** 70% of capital in a core US equity fund plus 30% in RSST is **1.3216× gross
   notional**, of which **1.0216 is equity beta** and **0.3000 is trend**. The financed part
   is +0.3216. The equity share is 2.16 points above a fully invested portfolio — a rounding
   detail. **The whole decision is the 0.30.** §1.

2. **The binding constraint is holdability, in two forms, and neither of them is the
   unconditional drawdown.** On this panel the overlay at 0.30 changes maximum drawdown by
   **under one percentage point** (−50.1% against the control's −50.3%), and **no
   unconditional drawdown tolerance tested binds the trend notional at all**. What binds is
   (a) tracking error — **3.77%/yr against 100% equity, of which 3.74% is the overlay alone**,
   with a central-case worst relative run of **−21.3% over 320 months** and a 5th percentile
   of **−42.4%** — and (b) the *valuation-conditioned* drawdown of conclusion 9, which cuts
   the equity notional and takes the overlay down with it. §3, §3.2, §6a.

3. **The growth-optimal size is not identifiable, and 30% is not obviously wrong.** 0.30 of
   trend notional is exactly growth-optimal at a **gross forward trend excess of 1.50%/yr**.
   The break-even, below which the optimum is negative, is **1.19%/yr** — and moves between
   **0.98% and 2.31%** across the whole plausible financing grid. The repository's own
   post-publication estimate, roughly **1.80%/yr**, sits inside that band. **So the sign of
   the overlay's contribution is not established**, and the window in which 0.30 is sensible
   is narrow at both ends. §4, §4a.

4. **The prize is small and the noise is enormous.** At a 1.80% gross forward premium the
   entire trend overlay at 0.30 is worth **18.2 bp/yr** of growth against **374 bp/yr** of
   tracking error — an information ratio of 0.05 and **692 years** to 90% confidence. Moving
   from 0.30 to 0.20 gives up **4.5 bp/yr** and removes a third of the benchmark-relative
   risk. **That asymmetry is the recommendation and it does not depend on the premium
   forecast.** §4a.

5. **The financing cost is the load-bearing estimate on this page, and nobody discloses it.**
   RSST files 0.00% of interest expense and that figure is **accurate and uninformative**: a
   futures position borrows nothing, so financing lives in the basis and never reaches an
   expense ratio. The independent estimate here is **119.5 bp/yr all-in per dollar of RSST**
   — 99 bp of fee plus 20.5 bp of equity-futures basis — which is **35.0 bp/yr of portfolio**
   at a 30% weight and **116.5 bp per unit of trend notional obtained**. **The fee is the
   larger part in every cell of the sensitivity grid.** §4.

6. **Volatility targeting does not survive.** Five windows, one declared target, costs and a
   60 bp spread inside the path, tested against a *volatility-matched constant-leverage*
   control and deflated on the **active series** rather than on the arm's own Sharpe. Four of
   five arms have a **negative** active return; the fifth is **+0.13 pp/yr against an MDE₈₀ of
   1.27**. Deflated significance **0.284** at 2.70 effective trials and **0.048** at the 14.8
   trials [timing rules](timing-rules-on-the-equity-sleeve.md) used. Nothing survives Benjamini–Hochberg or Holm. And
   short windows made the drawdown **worse**, not better. Verdict: **`unresolved`, with the
   point estimates pointing the wrong way.** §6.

7. **The resampled drawdown cliff is real, is seed-stable, and is not a risk gradient.**
   `P(deeper)` reproduces at **6.9% at w=0.30** and jumps **10.8% → 18.8%** between w=0.58
   and w=**0.59** (not 0.60), on four independent seeds. But it **vanishes entirely without
   the 60 bp financing charge** (9.5% → 9.7%), and its mechanism is that the *identity* of the
   worst drawdown episode switches from the GFC — where trend paid — to 1937-38, where it did
   not. A "practical ceiling near 55%" read off it is a statement about which two episodes are
   nearly tied in one panel. §3a.

8. **"How much trend" has three defensible answers because there are three objectives.**
   Minimum variance says **−0.015 on this panel** and **+0.216 in
   [stacking and effective breadth](stacking-and-effective-breadth.md)**; the two differ by nothing but one correlation estimate (+0.011 here against
   an implied −0.166 there). Maximum growth says **+0.49** at a 1.80% premium and **−0.67** at
   0%. Drawdown tolerance does not bind. **Pick the objective before the number.** §8.

9. **Under the valuation-conditioned drawdown assumption the defensible weight falls below the
   30% proposed, and that is a headline rather than a sensitivity.** Entries above CAPE 30 ran
   a median **−51.8% real** drawdown over the following fifteen years against **−36.7%** below
   CAPE 20, and US CAPE is **41.18** at 2026-08-01. Transferring only the **ratio** — 1.411×,
   because those figures are real and this page's ladder is nominal — a stated −50% tolerance
   supports a base notional of **0.651 rather than 0.992**, and at the candidate's own
   overlay-to-equity ratio that is **19.1% of capital in the wrapper, not 30%**. A −40%
   tolerance gives 14.9%. §3.2.

10. **Today's premium proxy sits where the growth objective wants less than a fully invested
    portfolio.** The TIPS-based excess CAPE yield is at the **0th percentile of the entire
    2003–2026 TIPS record** (+0.02 to +0.08 pp) with the 10-year real yield at 2.35%. Mapped
    into this page's units that lands near the 1–2%/yr arithmetic rows, where the frictionless
    growth-optimal exposure is **below 1.0 at every volatility of 15.5% or more**. It is not a
    timing signal — conditioning on it fails out of sample and after tax — but **a leverage
    recommendation derived from a historical premium at a moment when the premium proxy is at
    a record low is exactly the failure this repository exists to prevent.** §2.

11. **Sized recommendation: 15% to 25% of capital in the stacked fund, centre 20%**, which is
    0.15–0.25 of trend notional and a gross notional of **1.16× to 1.27×**. **Two independent
    routes land on the same band** — the tracking-error/holdability route in §6a and the
    valuation-conditioned drawdown route in §3.2 — and neither of them is the growth optimum.
    §9. **The published weight is 30%, above this band**, set in
    [part A](portfolio-for-one-investor.md) §2 on Experiment 016e's growth comparison rather
    than on either holdability route; the trade between the two is stated on
    [the recommendation](portfolio-recommendation.md).

---

## 1. What the portfolio actually holds

Forecast-free. Every figure is a sum of filed notionals per dollar of capital; sources are
canonical in `src/content/shelf.ts` and in
[capital efficiency](capital-efficiency-and-breadth.md).

| 70% core US equity plus 30% of… | gross notional | equity beta | non-equity | financed |
| --- | ---: | ---: | ---: | ---: |
| **RSST** (N-PORT 2026-04-30) | **1.3216** | **1.0216** | trend 0.3000 | **+0.3216** |
| RSSB (N-PORT 2026-04-30) | 1.3012 | 1.0002 | Treasury 0.3010 | +0.3012 |
| NTSX (N-PORT 2026-03-31) | 1.1630 | 0.9725 | Treasury 0.1905 | +0.1630 |
| MATE (N-PORT 2026-05-31) | 1.3476 | 1.0476 | trend 0.3000 | +0.3476 |
| MATE (N-PORT 2026-02-28) | 1.3348 | 1.0348 | trend 0.3000 | +0.3348 |
| **JPFP** | **no figure** | — | — | — |

Four readings the table does not make on its own.

**The equity share barely moves.** 1.0216 against a nominal 1.0000. Anyone comparing this
portfolio with a 100%-equity one on equity exposure is comparing two portfolios that are the
same on that axis. **The 30 points of trend notional are the entire difference.**

**RSSB is two decisions, not one.** Its base leg is *global* equity where this reader's
incumbent is US, so the row above changes the equity composition **and** adds an overlay, and
no single number scores both. Read it beside the US/global question, not inside it.

**MATE's base leg is 1.1587, not 0.498.** Reading the largest holding and stopping put it in
the range where a wrapper is arithmetically worse than selling equity outright; the same
filing carries a long E-mini future at 65.57% that takes the base leg to 115.87%. The trend
leg above is the prospectus's 100% target, because the E-mini line is **not separable** into
base completion and the trend book's own equity position. Full working in
[capital efficiency](capital-efficiency-and-breadth.md).

**JPFP gets no number.** It commenced 2026-05-27 and has filed no Form N-PORT; the first is
due 2026-08-29 or 2026-09-29. A prospectus sentence is not a notional. `not filed`, with a
date, is the finding — assigning it an assumed 1.0 + 1.0 would manufacture the exact quantity
this page exists to compute.

### 1.1 A derivative book is not an exposure, and the two must never be summed

Every figure above is **net economic exposure** — the directional risk the holder carries. It
is not the funds' gross derivative book, which is much larger and counts contracts rather than
risk:

| | gross derivative book | delivered exposure |
| --- | ---: | ---: |
| RSST trend leg | ~294% of net assets | ~100% of trend risk |
| MATE, 2026-05-31 | **404.5%** of net assets (284.2% futures + 120.3% FX forwards) | 100% trend target |
| MATE, 2026-02-28 | 339% of net assets | 100% trend target |

A long/short trend book is long some contracts and short others, so the legs offset; a 120.3%
FX-forward book is not 120.3% of directional risk. **MATE's book moved from 339% to 404.5% of
net assets between two filings while its stated targets did not move at all**, which is the
cleanest available demonstration that the gross derivative number is an artefact of the
volatility target rather than a quantity a portfolio can be sized on. Summing derivative
notionals across the funds would put the candidate near 2.0× on RSST and 2.2× on MATE, and
both numbers would be meaningless.

---

## 2. Where the leverage recommendation changes sign

`L* = (mu − r) / sigma**2` inverts to `mu − r = L sigma**2`. **The exposure you hold is a
premium forecast, whether or not you have written it down.**

| annualised volatility | L = 0.80 | **L = 1.00** | L = 1.3216 | L = 1.50 | L = 2.00 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 13.0% | 1.35% | **1.69%** | 2.23% | 2.54% | 3.38% |
| 15.5% | 1.92% | **2.40%** | 3.18% | 3.60% | 4.81% |
| 18.0% | 2.59% | **3.24%** | 4.28% | 4.86% | 6.48% |
| 22.0% | 3.87% | **4.84%** | 6.40% | 7.26% | 9.68% |

**The middle column is the sign flip.** At this panel's 15.86% equity volatility the
growth-optimal exposure is exactly 1.0 at a premium of **2.51%/yr**. Below it, the growth
objective wants *less* than a fully invested portfolio and any leverage at all is overbetting.
This is the same quantity as [capital efficiency](capital-efficiency-and-breadth.md)'s
funding-rule gap `a_p − sigma_p**2`, written as a break-even rather than as a difference — the
gap changes sign at exactly the premium at which levering stops being growth-optimal.

The growth-optimal exposure on a premium × volatility grid, frictionless:

| `mu − r` | σ = 13.0% | σ = 15.5% | σ = 18.0% | σ = 22.0% |
| ---: | ---: | ---: | ---: | ---: |
| 1.00% | 0.59 | 0.42 | 0.31 | 0.21 |
| 2.00% | 1.18 | 0.83 | 0.62 | 0.41 |
| 2.50% | 1.48 | 1.04 | 0.77 | 0.52 |
| 3.00% | 1.78 | 1.25 | 0.93 | 0.62 |
| 4.00% | 2.37 | 1.66 | 1.23 | 0.83 |
| 5.00% | 2.96 | 2.08 | 1.54 | 1.03 |
| 6.00% | 3.55 | 2.50 | 1.85 | 1.24 |

**Across the plausible corner of that grid the answer runs from 0.31 to 3.55.** An eleven-fold
range, from "hold two thirds of a portfolio" to "hold three and a half", produced entirely by
moving two forecasts inside their honest bounds. Any leverage recommendation quoted without
this surface is quoting one cell of it.

**Where today's premium proxy lands on that grid.** The TIPS-based excess CAPE yield is at the
**0th percentile of the entire 2003–2026 TIPS record**, +0.02 to +0.08 pp, with the 10-year
real yield at 2.35% — real rates at post-2008 highs have closed the premium proxy to roughly
zero ([valuation and the allocation](valuation-and-the-allocation.md)). **Two unit conversions are
needed before that number can be read off the table above**, and skipping them is how this
kind of figure gets misused. An excess CAPE yield is a *geometric real* premium over long
TIPS; the Kelly numerator wants an *arithmetic* excess over *cash*. Converting adds roughly
`sigma**2 / 2` — about 1.26 pp — and then subtracts whatever term premium sits between cash
and the ten-year real yield. That lands somewhere around the **1.00% to 2.00%** rows, where
the frictionless growth-optimal exposure is **0.21 to 1.18 and is below 1.0 at every
volatility of 15.5% or more**. With §2.1's kink and financing it is 0.42 to 1.00.

**This is not a timing signal and must not be used as one** — [valuation and the allocation](valuation-and-the-allocation.md) finds
CAPE-level conditioning loses gross and net, loses out of sample at every horizon since 1990,
and has 73.4% of its slope eaten by Stambaugh bias. It is an argument about where to *centre*
the premium input, not about when to trade. And the direction it points is unambiguous: the
grid's low rows, not its high ones. **The panel's realised 8.54%/yr arithmetic excess, which
produces `L* = 3.40`, is an illustration of the machinery and not a forecast anyone should
size against today.**

### 2.1 The kink, which is where most premium forecasts land

Borrowing costs more than lending, so the objective is piecewise quadratic with a kink at
1.0×. Charging a spread only on the financed part:

| `mu − r` | σ=13.0% | σ=15.5% | σ=18.0% | σ=22.0% | | σ=13.0% | σ=15.5% | σ=18.0% | σ=22.0% |
| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| | *60 bp spread* | | | | | *89.6 bp spread* | | | |
| 2.00% | **1.00** | 0.83 | 0.62 | 0.41 | | **1.00** | 0.83 | 0.62 | 0.41 |
| 2.50% | 1.12 | **1.00** | 0.77 | 0.52 | | **1.00** | **1.00** | 0.77 | 0.52 |
| 3.00% | 1.42 | **1.00** | 0.93 | 0.62 | | 1.25 | **1.00** | 0.93 | 0.62 |
| 4.00% | 2.01 | 1.42 | 1.05 | 0.83 | | 1.84 | 1.29 | **1.00** | 0.83 |
| 5.00% | 2.60 | 1.83 | 1.36 | **1.00** | | 2.43 | 1.71 | 1.27 | **1.00** |

89.6 bp is not an assumption — it is the candidate's own incremental wrapper fee (28.8 bp of
portfolio) divided by the 0.3216 of financed notional it buys.

**The bold cells are the kink, and it is a region rather than a point.** A whole range of
premium forecasts, exactly as wide as the spread in excess-return units, implies **holding
exactly what you already have**. At a 15.5% volatility and an 89.6 bp spread that range runs
from 2.40% to 3.30%/yr — a band that covers most defensible US equity premium forecasts. **The
frictionless answer's precision is an illusion the friction removes.**

### 2.2 Can the data identify it? Not at any horizon an investor plans over

`SE(Lhat*) = 1 / (sigma sqrt(T))` contains no `mu`: precision comes from the **calendar span**
of the sample alone, so sampling more finely inside a window buys nothing
([Merton 1980](https://doi.org/10.1016/0304-405X(80)90007-0)).

| believed stationary sample | plug-in `L*` | `SE` | 95% interval | spans 1.0? |
| ---: | ---: | ---: | --- | --- |
| 10 yr | 3.40 | 1.99 | [−0.51, +7.30] | **yes** |
| 20 yr | 3.40 | 1.41 | [+0.63, +6.16] | **yes** |
| 30 yr | 3.40 | 1.15 | [+1.14, +5.65] | no |
| 90.9 yr (the whole panel) | 3.40 | 0.66 | [+2.10, +4.69] | no |

**On any sample under about twenty-five years the interval on the growth-optimal exposure
includes 1.0 — the data cannot say whether to lever at all.** The two rows that exclude 1.0
require believing that ninety years of US equity returns are one stationary regime, which
[setting the equity share](setting-the-equity-share.md) §6 gives direct evidence against.

### 2.3 Fractional Kelly, and the bias claim done correctly

The commonly made claim is that estimation error *biases the plug-in optimum upward*. **Run
correctly it does not, and the correct version is worse news, not better.** With `sigma` known,
`Lhat*` is **unbiased and noisy**; what the noise damages is achieved growth, not the estimate.
Estimating `sigma` too biases it upward by `(n−1)/(n−3)`, which on 1,091 monthly observations
is **1.0018** — a rounding error. The full derivation is
[setting the equity share](setting-the-equity-share.md) §2.1 and is not repeated here.

The quantity that *is* large is the growth given up, `1/(2T)`, exact and free of every other
parameter, together with the growth-maximising shrinkage `f* = S**2 T / (S**2 T + 1)` at this
panel's Sharpe of 0.5384:

| believed years of stationarity | growth cost `1/(2T)` | growth-maximising `f*` |
| ---: | ---: | ---: |
| 10 | **5.00%/yr** | 0.744 |
| 20 | **2.50%/yr** | 0.853 |
| 30 | 1.67%/yr | 0.897 |
| 90.9 | 0.55%/yr | 0.963 |

**Full Kelly is not the operating point, and the reason is variance under non-stationarity
rather than bias.** But the arithmetic supports a fraction near 0.9, not 0.5, and anyone
using half Kelly here is asserting that ninety years of record are worth about seven years of
stationary information. That may be right; it is a claim about regimes and has to be defended
as one.

Being at a fraction `f` of the optimum retains `1 − (1 − f)**2` of the peak excess growth —
0.75 at half, 1.00 at the optimum, 0.00 at twice it, and negative beyond. **The parabola is
symmetric in exposure, so the asymmetry is multiplicative: underbetting by a factor of two
costs a quarter of the peak, overbetting by a factor of two costs all of it and carries four
times the variance while doing so.**

---

## 3. What the record says, measured

Panel: 1934-07…2025-05, **1,091 months**, imported from
[capital efficiency](capital-efficiency-and-breadth.md)'s own instrument so the two pages
cannot drift. Equity is Ken French `Mkt-RF` (excess 8.54%/yr at 15.86% volatility); the trend
leg is the Moskowitz–Ooi–Pedersen construction on four instruments, volatility-targeted on a
trailing 60-month window and charged 95 bp/yr (excess 7.40%/yr at 12.46%); cash is
Goyal–Welch `Rfree`. Equity/trend correlation **+0.0112**. **1929-32 is absent by
construction** — the trend leg's burn-in consumes the first 96 months — so every drawdown
below is measured on a sample from which the deepest US equity fall on record is missing.

**A. base held at 1.00, trend notional varied.** 96 bp/yr charged on trend notional.

| trend notional | gross | geo | vol | Sharpe | max drawdown | months under water |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.00 | 1.00 | 11.13% | 15.86% | 0.538 | **−50.3%** | 74 |
| **0.30** | **1.30** | **13.19%** | 16.33% | 0.641 | **−49.3%** | 73 |
| 0.60 | 1.60 | 15.13% | 17.61% | 0.705 | −49.3% | 72 |
| 1.00 | 2.00 | 17.50% | 20.28% | 0.739 | −49.4% | 72 |

**B. the same gross notional taken as levered equity**, at a 60 bp financing spread.

| base notional | gross | geo | vol | Sharpe | max drawdown | months under water |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1.00 | 1.00 | 11.13% | 15.86% | 0.538 | −50.3% | 74 |
| 1.30 | 1.30 | 12.79% | 20.62% | 0.530 | **−60.8%** | 86 |
| 1.60 | 1.60 | 14.19% | 25.37% | 0.524 | −69.4% | 92 |
| 2.00 | 2.00 | 15.61% | 31.72% | 0.520 | **−80.2%** | 156 |

**Read A against B at matched gross and the whole case for a stacked fund is visible in one
comparison.** At 1.30× gross, the trend route drew down 49.3% and the levered-equity route
60.8%; the trend route's Sharpe rose from 0.538 to 0.641, the levered route's fell to 0.530.
**A gross-notional figure cannot tell them apart**, which is why no wrapper may be scored from
one. Note also that ladder B's Sharpe declines monotonically — levering a single asset buys
return with beta and nothing else, exactly as
[decision 0004](../decisions/0004-no-sleeve-promoted.md) warns.

**C. the candidate exactly as filed:**

| | geo | vol | Sharpe | max drawdown | months under water |
| --- | ---: | ---: | ---: | ---: | ---: |
| candidate, 1.0216 equity + 0.30 trend | 13.34% | 16.67% | **0.639** | −50.1% | 74 |
| control, 100% equity | 11.13% | 15.86% | 0.538 | −50.3% | 74 |
| levered equity at 1.3216× | 12.90% | 20.96% | 0.529 | **−61.5%** | 86 |

**These are in-sample figures at the panel's realised 7.40%/yr trend excess and must not be
read as a forecast.** §4a restates every one of them at premia the repository can defend.

### 3.1 Sizing by drawdown tolerance, which needs no forecast at all

The tolerances a reader is likely to state are *below* an unlevered equity portfolio's own
drawdown, so the base notional has to be varied downward for the question to have an answer.

| drawdown you would have sat through | max base alone | max base with 0.30 trend | extra base bought |
| ---: | ---: | ---: | ---: |
| −30% | 0.540 | 0.550 | **+0.010** |
| −40% | 0.750 | 0.770 | **+0.019** |
| −50% | 0.992 | 1.016 | **+0.024** |
| −60% | 1.274 | 1.300 | **+0.026** |

**The last column is the honest size of the overlay's drawdown benefit, and it is tiny.** At
every tolerance the 0.30 overlay buys between one and three *points* of extra equity beta at
the same drawdown. It is a real benefit and it is not what a 30% allocation is for.

The ladder a reader can pick a row from directly:

| base notional | gross with 0.30 trend | drawdown alone | drawdown with trend | geo alone | geo with trend |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.50 | 0.800 | −27.9% | −27.6% | 7.53% | 9.54% |
| 0.70 | 1.000 | −37.7% | −36.9% | 9.04% | 11.07% |
| 0.90 | 1.200 | −46.4% | −45.5% | 10.46% | 12.38% |
| **1.00** | **1.300** | **−50.3%** | **−49.4%** | 11.13% | 12.99% |
| 1.30 | 1.600 | −60.8% | −60.0% | 12.79% | 14.67% |

**No drawdown tolerance in the tested range binds the trend notional.** It binds the equity
notional hard — that is what the "base alone" column is — and this asymmetry is the reason a
drawdown-tolerance answer to "how much trend" does not exist *in isolation*. §3.2 shows how it
reappears once the tolerance is applied to a valuation-conditioned drawdown and the overlay is
held at a fixed share of the equity exposure.

### 3.2 The same ladder under the valuation-conditioned drawdown assumption

**This is the section that most changes the answer.** Entries above CAPE 30 ran a median
**−51.8% real** drawdown over the following fifteen years, against **−36.7%** for entries below
CAPE 20; the median buyer above CAPE 30 spent **59.7% of the next fifteen years below their
real entry level** against 5.0% for buyers below CAPE 20. **US CAPE is 41.18 at 2026-08-01** —
a level equalled or exceeded in 19 of the 1,748 months since 1881, **18 of them between March
1999 and September 2000**. Measured in
[valuation and the allocation](valuation-and-the-allocation.md).

**Those two drawdowns are real and this page's ladder is nominal, so only their ratio
transfers: 1.411×.** Applying it is the same operation as asking for a tolerance that much
tighter, which is the honest way to read a conditional drawdown against an unconditional
ladder.

| stated tolerance | max base, panel as measured | max base, CAPE-conditioned | change |
| ---: | ---: | ---: | ---: |
| −30% | 0.540 | 0.376 | −0.165 |
| −40% | 0.750 | 0.508 | −0.243 |
| **−50%** | **0.992** | **0.651** | **−0.341** |
| −60% | 1.274 | 0.808 | −0.467 |

**The equity notional is what moves, and it moves a lot.** A −50% tolerance supports 0.992 of
equity on the panel as measured and 0.651 once the ratio is applied — the same investor, the
same stated tolerance, **a third less equity**.

Holding the overlay at a constant share of the equity exposure — the candidate's own ratio of
0.294 — that converts directly into a weight in the wrapper, because a dollar of RSST delivers
1.000 of trend notional:

| stated tolerance | base notional | trend notional | **capital in the wrapper** | gross |
| ---: | ---: | ---: | ---: | ---: |
| −30% | 0.376 | 0.110 | **11.0%** | 0.486 |
| −40% | 0.508 | 0.149 | **14.9%** | 0.657 |
| **−50%** | 0.651 | 0.191 | **19.1%** | 0.842 |
| −60% | 0.808 | 0.237 | **23.7%** | 1.045 |

**Every row is below the 30% proposed**, and the −50% row — a tolerance most people who say
they can hold through a bear market would give — lands at **19.1%**. This is an *independent*
route to the same answer §9 reaches from tracking error, and the two agreeing is worth more
than either alone: one is a holdability-of-relative-performance argument, the other a
holdability-of-absolute-loss argument, and they are not the same constraint.

**Three limits on it, stated because they cut both ways.** The ratio transfer assumes the
nominal-to-real conversion does not itself depend on the valuation regime, which it may. The
CAPE-conditioned figures rest on a *level* conditioning whose forecasting content [valuation and the allocation](valuation-and-the-allocation.md) found to be nil out of
sample — what survives is the **constraint** reading (what the
buyer had to endure), not the forecast reading. And the whole calculation still terminates in
a tolerable-drawdown number **nobody has supplied**, which is
[setting the equity share](setting-the-equity-share.md)'s standing finding and this page does
not fix it.

---

## 3a. The resampled drawdown cliff, located and explained

[Decision 0009](../decisions/0009-blocks-lifted-and-closures-rescoped.md) cites *"a resampled
`P(deeper)` that doubles between w=0.58 and w=0.60"* as an argument about holdability that no
funding-rule result touches. **It reproduces exactly, and three things about it are new
here.**

Circular block bootstrap, 24-month blocks, 4,000 paired resamples, both arms drawn on the same
history, at the published settings (95 bp fee on trend notional):

| trend w | gross | P(deeper), 60 bp spread | P(deeper), no spread |
| ---: | ---: | ---: | ---: |
| 0.10 | 1.10 | 5.5% | 4.9% |
| **0.30** | 1.30 | **6.9%** | 6.2% |
| 0.50 | 1.50 | 9.6% | 8.3% |
| 0.56 | 1.56 | 10.4% | 9.2% |
| **0.58** | 1.58 | **10.8%** | 9.5% |
| **0.59** | 1.59 | **18.8%** | 9.7% |
| 0.60 | 1.60 | 18.9% | 9.8% |
| 1.00 | 2.00 | 26.9% | 17.6% |
| 2.00 | 3.00 | 78.7% | 75.8% |

**First, the jump is between 0.58 and 0.59, not 0.58 and 0.60**, and it is seed-stable: across
four independent seeds it sits in the same 0.01 of notional (10.8→18.8, 10.5→18.5, 10.7→18.4,
10.9→18.2).

**Second, it disappears without the financing charge.** The right-hand column ramps smoothly
through the same region. The published §7 ladder charges no spread, so the ladder and the
cliff are computed under different assumptions about the same portfolio.

**Third, the mechanism is an episode switch, not a rising risk.** On the actual path the
overlay's worst drawdown moves off **2007-10→2009-02** at w=0, where trend paid, and onto
**1937-02→1938-03** at any overlay weight at all, where it did not — and the depths of the two
are close enough that a large block of resampled histories crosses over at nearly the same
weight. `P(deeper)` is therefore a step function of which of two episodes happens to be deeper
in one panel. **A "practical ceiling near 55%" read off it is a much weaker statement than it
sounds**, and it is well above anything this page recommends anyway.

---

## 4. The financing cost, honestly

**RSST files 0.00% of interest expense. That figure is accurate and uninformative.** A futures
position borrows nothing, so there is no interest-expense line to report; the financing is
embedded in the futures basis over the rate the collateral earns and never appears in an
expense ratio. MATE and JPFP are equally silent — unitary fees exclude interest expense, and
MATE's Other Expenses line is 0.00% and estimated. **Every fee table on this shelf compares
everything except the cost of the leverage**, so the estimate below is load-bearing rather than
supplementary.

Current rates, refreshed 2026-08-22 into `research/cache`: effective fed funds **3.63%**
(2026-08-20), 3-month constant-maturity Treasury **3.87%** (2026-08-20), 3-month bill **3.73%**
(2026-07). **The level nets out of a futures position** — the holder forgoes the cash return on
the notional and earns it on the collateral — so only the basis matters and the stack is a
spread table.

| at 30% of capital | fee | financing | all-in per $1 of fund | per $1 of portfolio | incremental over VTI | per unit of diversifier notional |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **RSST** | 99.0 | 20.5 | **119.5** | **35.9** | **35.0** | **116.5** |
| RSST, trend book at +25 bp | 99.0 | 45.5 | 144.5 | 43.4 | 42.5 | 141.5 |
| NTSX | 20.0 | 9.5 | 29.5 | 8.9 | 8.0 | 41.8 |
| RSSB | 39.0 | 15.0 | 54.0 | 16.2 | 15.3 | 50.9 |

All bp/yr. Legs of the central RSST row, with their sources — none of them measured here:

- **E-mini equity futures, 0.331 of financed notional × 62 bp = 20.5 bp.** The 62 bp is equity
  index futures over 3-month Term SOFR, ten rolls Dec-2022→Mar-2025, a genuine post-2022
  regime change ([structural and tax edges](structural-and-tax-edges.md)).
- **Diversified trend book, 1.000 of financed notional × 0 bp = 0 bp.** Hazelkorn, Moskowitz
  and Vasudevan (2023) measure the *signed* basis at −0.83 bp on average across 18 index
  futures, 2000–2017, against a mean *absolute* basis of 52–64 bp. **A long/short book takes
  both sides by construction**, so a systematic per-contract drag is not supported, and the
  absolute figure must never be applied as one.

**The overlay hurdle** is `rho sigma_p sigma_d + cost per unit notional` = 2.2 + 116.5 =
**118.7 bp/yr of gross trend excess return** before the first dollar of overlay adds any
growth. The covariance term is essentially zero because the correlation is; **the hurdle is
almost entirely cost, and the fee is the larger part of the cost.**

### 4.1 Sensitivity, because this is the estimate the answer turns on

Break-even gross trend excess return, %/yr:

| equity-futures basis ↓ / trend-book drag → | 0 bp | 25 bp | 50 bp | 100 bp |
| ---: | ---: | ---: | ---: | ---: |
| 0 bp | 0.98 | 1.23 | 1.48 | 1.98 |
| 31 bp | 1.08 | 1.33 | 1.58 | 2.08 |
| **62 bp** | **1.19** | 1.44 | 1.69 | 2.19 |
| 100 bp | 1.31 | 1.56 | 1.81 | 2.31 |

The corresponding incremental portfolio cost runs from **28.8 to 68.7 bp/yr**.

**The whole grid spans 0.98% to 2.31%/yr, and the repository's own post-publication trend
estimate of roughly 1.80%/yr sits inside it.** So the *sign* of the overlay's contribution is
decided by a financing spread nobody discloses and this repository has not measured. That is
the single most valuable thing another measurement could resolve.

---

## 4a. Every measured row restated at a forward premium

The panel's realised gross trend excess is 7.40%/yr. **Nothing in this repository signs a
forward number anywhere near it.** Every row below shifts the trend leg's **mean** to a stated
forward premium and leaves its volatility and its correlation with equity exactly unchanged.

| gross trend excess | net of 96 bp | candidate geo | control geo | edge | candidate drawdown | Sharpe | growth-optimal trend notional |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **0.00%** | −0.96% | 10.87% | 11.13% | **−0.26 pp** | −51.4% | 0.506 | **−0.67** |
| **1.80%** | +0.84% | 11.46% | 11.13% | **+0.33 pp** | −51.1% | 0.538 | **+0.49** |
| 3.70% | +2.74% | 12.09% | 11.13% | +0.96 pp | −50.7% | 0.573 | +1.72 |
| 7.40% (realised) | +6.44% | 13.34% | 11.13% | +2.20 pp | −50.1% | 0.639 | +4.10 |

**Inverted: 0.30 of trend notional is exactly growth-optimal at a gross forward trend excess
of 1.50%/yr** (0.54% net). At 1.80% the optimum is 0.49, so **30% is about 61% of the growth
optimum at the best forward number this repository has** — a fractional-Kelly position arrived
at by accident rather than by design.

### 4a.1 The size of the prize, which is what the whole decision turns on

Peak excess growth from the trend leg alone is `a_net**2 / (2 sigma_d**2)` at notional
`a_net / sigma_d**2`; growth at any other notional is that peak times `1 − (1 − f)**2`.
Tracking error against 100% equity is `w sigma_d`.

| gross trend | optimal `w` | peak growth | at w=0.15 | at w=0.20 | at w=0.25 | **at w=0.30** | TE at 0.30 | 90% confident at |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.00% | −0.62 | 29.7 bp | −16.1 | −22.3 | −28.9 | **−35.8 bp** | 3.74% | never |
| **1.80%** | 0.54 | **22.7 bp** | 10.9 | **13.7** | 16.1 | **18.2 bp** | 3.74% | **692 yr** |
| 3.70% | 1.77 | 241.8 bp | 39.4 | 51.7 | 63.6 | 75.2 bp | 3.74% | 41 yr |
| 7.40% | 4.15 | 1337.8 bp | 94.9 | 125.8 | 156.3 | 186.4 bp | 3.74% | 7 yr |

bp/yr of the portfolio's growth rate, from the trend leg alone, on the lognormal model rather
than on the realised path. **The 1.80% row is the decision.** The entire overlay is worth at
most 22.7 bp/yr of growth, 18.2 bp of it captured at 0.30 — against 374 bp/yr of tracking
error, an information ratio of 0.05, and **692 years to 90% confidence**.

**Moving from 0.30 to 0.20 gives up 4.5 bp/yr and removes a third of the benchmark-relative
risk.** That trade holds at every premium in the defensible range, and at a 0% premium it also
removes 13.5 bp/yr of loss.

---

## 5. The outcome distribution

4,000 joint 24-month block resamples; both arms drawn on the same history so each draw is one
investor's two portfolios. Drawdown percentiles are reported rather than the worst resample,
which is an extreme order statistic that moves several points with the seed.

**Trend at the repository's 1.80% forward premium, against 100% equity:**

| horizon | P(underperform) | relative wealth p5 / median / p95 | median drawdown | p5 | p1 |
| ---: | ---: | --- | ---: | ---: | ---: |
| 10 yr | **41.0%** | 0.865 / 1.024 / 1.257 | −29.0% | −51.4% | −60.2% |
| 20 yr | 35.8% | 0.826 / 1.058 / 1.395 | −37.4% | −57.3% | −65.1% |
| 30 yr | **32.1%** | 0.800 / 1.096 / 1.541 | −42.3% | −59.9% | −66.6% |

**At a 0.00% forward premium the sign flips:** P(underperform) 60.6% / 62.1% / 64.2% and a
median relative wealth of 0.933 at thirty years. **At the realised 7.40%** it is 3.0% / 0.3% /
0.1% — which is the number a backtest would report and which nothing here supports as a
forecast.

Against **levered equity at 1.3216×** the candidate underperforms in 75.5% / 80.6% / 85.0% of
resamples at the 1.80% premium. **That comparison is real and it is not the one to size on**:
the levered-equity arm carries a −61.5% drawdown against the candidate's −51.1%, so it wins
terminal wealth by taking a risk the drawdown table already says the investor should not.
These two benchmarks answer different questions and **their answers do not add**.

**The limitation that cuts against every row.** Block resampling preserves dependence to 24
months and destroys it beyond, so a 30-year row is an extrapolation of that null rather than a
measurement of a 30-year holding period.

---

## 6. "Understand market conditions": vol-targeting does not survive

The investor's second requirement is the better-evidenced one — volatility really is far more
forecastable than return, which is why this is tested rather than dismissed. The rule:
`leverage_t = clip(15% / trailing vol(t−w … t−1), 0, 2)` applied to the candidate portfolio's
excess return, with a 60 bp spread on the financed part and 10 bp of round-trip cost per unit
of notional traded, **all inside the path**. Five arms, one declared target, windows 3/6/12/24/36
months.

| window | months | mean L | turnover/yr | geo | vol | Sharpe | max drawdown | trading cost | **active pp/yr** | **MDE₈₀** | HAC t | p |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 1088 | 1.299 | **4.14** | 14.61% | 22.07% | 0.584 | **−72.3%** | 41.4 bp | **−1.16** | 2.73 | −1.11 | 0.267 |
| 6 | 1085 | 1.168 | 1.97 | 12.32% | 19.23% | 0.532 | −61.7% | 19.7 bp | **−2.05** | 2.17 | −2.22 | 0.027 |
| 12 | 1079 | 1.080 | 0.84 | 13.25% | 17.09% | 0.621 | −49.7% | 8.4 bp | −0.27 | 1.71 | −0.40 | 0.686 |
| 24 | 1067 | 1.022 | 0.41 | 12.60% | 16.25% | 0.606 | −53.3% | 4.1 bp | −0.17 | 1.45 | −0.35 | 0.729 |
| 36 | 1055 | 0.995 | 0.25 | 12.76% | 15.95% | 0.622 | −56.0% | 2.5 bp | **+0.13** | 1.27 | +0.27 | 0.788 |

**"Active" is the volatility-matched difference against a constant-leverage arm at the same
mean exposure**, which is the only comparator that makes this a timing test rather than a
leverage test.

**The deflation is run on the active series and never on an arm's own Sharpe.** Every arm here
is long the candidate portfolio all of the time, so its raw Sharpe contains the equity premium
and deflating it returns a pass by construction — the same mis-specification
[timing rules on the equity sleeve](timing-rules-on-the-equity-sleeve.md) identified. The best arm's raw Sharpe is 0.622 and **that is not the number
deflated**.

| | |
| --- | ---: |
| best arm by active Sharpe | 36-month window, monthly active SR **+0.0088** |
| mean off-diagonal correlation across the five active series | 0.5753 |
| effective independent trials | 2.70 |
| trial dispersion `sqrt(V[SR])` | 0.0341 |
| deflated null threshold `SR*` | 0.0264 |
| **deflated significance `P[SR_true > SR*]`** | **0.2842** |
| the same at 14.8 assumed independent trials | **0.0475** |
| the same at 100 | 0.0059 |
| the same at 10,000 | 0.0000 |

Benjamini–Hochberg and Holm across the five arms reject **nothing**: BH-adjusted p-values run
0.133 to 0.788, Holm 0.133 to 1.000. The one arm with a nominally significant raw p (6-month,
p = 0.027) is significant in the **wrong direction** and does not survive correction.

**Verdict: `unresolved`, with the point estimates pointing the wrong way.** Four of five arms
have a negative active return; the one positive arm is +0.13 pp/yr against an MDE₈₀ of 1.27,
a tenth of the smallest effect the design could see. And two facts make the practical case
worse than the statistical one:

- **Short windows made the drawdown deeper, not shallower** — −72.3% at a 3-month window
  against the unconditional −50.1%. The cap binds in calm periods, so the rule is levered
  going into the spike, which is precisely the failure mode §7 exists to price.
- **Turnover is 0.25 to 4.14 whole portfolios of notional a year, and the tax is not priced
  in any row above.** In a taxable account each leverage change is a realisation; at the
  investor's marginal rate a short-term realisation of that size is the largest single term in
  the rule and dwarfs the 2.5 bp of trading cost the best arm actually charges.

**Trading cost is not what kills it.** At the best arm, moving the round-trip assumption from
5 to 20 bp moves the geometric return from 12.78% to 12.74%. The rule fails because there is
no timing effect to capture at this frequency on this portfolio, not because it is expensive.

### 6a. What the tracking error means for the stretch to sit through

| | |
| --- | ---: |
| tracking error of the candidate against 100% equity | **3.77%/yr** |
| of which the trend overlay alone (`w × sigma_d`) | **3.74%/yr** |
| of which the extra equity beta alone | 0.34%/yr |

**The overlay is essentially the entire benchmark-relative risk budget.** This reproduces
[stacking and effective breadth](stacking-and-effective-breadth.md)'s ~400 bp total and 372 bp
from the overlay, from a different code path.

But an annualised standard deviation is not what anybody experiences. The experienced quantity
is the worst run of *relative* underperformance and how long it lasts:

| gross trend excess | worst relative run | months under water | p5 of resampled worst run |
| ---: | ---: | ---: | ---: |
| 0.00% | **−37.2%** | **864** | −59.6% |
| **1.80%** | **−21.3%** | **320** | **−42.4%** |
| 3.70% | −16.6% | 228 | −28.9% |
| 7.40% (realised) | −12.0% | 122 | — |

**At the repository's own forward premium the investor should expect, as a central case, to be
21% behind a simple 100%-equity portfolio at some point, and to spend twenty-six years below a
previous relative high.** The realised-premium row understates this by a factor of two because
it embeds a trend premium nobody will underwrite. **This is the number that decides whether
the position is holdable, and it is why the recommendation in §9 is smaller than 30%.**

---

## 7. The specific danger: leverage, a volatility spike, forced deleveraging

Peak-to-trough inside each named episode from [the evidence base](evidence-base.md):

| episode | months | 100% equity | candidate | levered equity 1.3216× |
| --- | ---: | ---: | ---: | ---: |
| 1929-32 great crash | — | **absent from the panel** | — | — |
| 1937-38 | 13 | −49.3% | −49.4% | **−60.7%** |
| 1973-74 | 24 | −44.9% | **−34.4%** | −57.1% |
| late-1970s inflation | 39 | −12.0% | −13.5% | −16.5% |
| 1987 | 5 | −29.9% | −32.4% | −38.9% |
| 1998 | 4 | −15.6% | −16.1% | −20.8% |
| 2000-02 dotcom | 30 | −45.0% | **−40.8%** | −56.7% |
| 2008-09 GFC | 16 | −48.0% | **−42.6%** | −59.0% |
| 2020 Q1 covid | 3 | −20.2% | −18.8% | −26.4% |
| 2022 inflation | 12 | −20.5% | −21.1% | −26.9% |

**The overlay helped in the slow crises and did not help in the fast ones.** It took 3 to 5
points off the dotcom bust, the GFC and 1973-74, and it was *worse* than the control in 1987,
1937-38 and 2022. That is the signature of a trend book: it needs a trend to form.

**1929-32 is missing by construction** and its absence is not a detail — it is the deepest
equity drawdown in the record, removed from the sample by the trend leg's own burn-in.

**Forced deleveraging**, priced as the wrapper's own risk control cutting the overlay after a
loss and restoring it only at a new high-water mark:

| trigger | months deleveraged | geo | max drawdown | cost vs unconstrained | drawdown change |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 10% | 458 | 12.66% | −50.6% | **−0.54 pp/yr** | **−1.33 pp worse** |
| 15% | 350 | 12.60% | −52.2% | −0.59 pp/yr | −2.91 pp worse |
| 20% | 281 | 12.73% | −52.2% | −0.46 pp/yr | −2.91 pp worse |
| 30% | 174 | 12.97% | −51.3% | −0.22 pp/yr | −1.98 pp worse |

**Cutting the overlay after a loss costs return *and* deepens the drawdown**, because the
sleeve is removed for exactly the part of the path where it would have paid. A return-stacked
ETF cannot margin-call its holders, so this is the fund's own risk control seen from inside —
**and the investor's version of the same mechanism, selling the wrapper after a bad stretch,
is larger and is not estimable from any series held here.** §6a's 320 months of relative
underperformance is the input to that failure mode.

---

## 8. Three answers to "how much trend", each optimising something else

These are **not** competing estimates of one quantity.

| objective | optimal trend notional | what it ignores |
| --- | ---: | --- |
| minimum portfolio variance, **this panel** | **−0.015** | expected return |
| minimum portfolio variance, [stacking and effective breadth](stacking-and-effective-breadth.md) | **+0.216** | expected return |
| maximum growth at a 1.80% gross premium | **+0.49** | drawdown and holdability |
| maximum growth at a 0.00% gross premium | −0.67 | drawdown and holdability |
| drawdown tolerance, any tolerance tested | **not binding** | return entirely |
| the investor proposes | **+0.300** | |

**The two variance-minimising numbers do not disagree about method.** With the base at `b`,
portfolio variance is minimised at `w* = −b rho sigma_e / sigma_d` — an identity. On this
panel the measured equity/trend correlation over 1,091 months is **+0.0112**, statistically
indistinguishable from zero, so `w*` is −0.015. Inverting the identity, **0.216 requires
`rho = −0.166`.** The entire gap between the two answers is one correlation, measured on
different instruments over different windows:

| assumed `rho` | variance-minimising `w*` |
| ---: | ---: |
| −0.30 | +0.390 |
| −0.20 | +0.260 |
| **−0.17** | **+0.221** |
| −0.10 | +0.130 |
| 0.00 | 0.000 |
| **+0.011 (measured here)** | **−0.015** |
| +0.10 | −0.130 |

Neither measurement is resolvable against the other from anything held here, and
[the charter](../charter.md)'s rule applies with force: **a low average correlation is
incomplete evidence about crisis dependence, and this identity uses the average one.** §7's
episode table is the direct evidence — the correlation that matters is the one in 1937-38 and
2022, not the one in the full sample.

### 8.1 If the objective is drawdown control, rank the ways to buy it

| route | max drawdown | geo | turnover/yr | cost |
| --- | ---: | ---: | ---: | ---: |
| **hold less equity (base 0.90)** | **−46.4%** | 10.46% | 0.00 | **0 bp** |
| the 0.30 trend overlay | −50.1% | 13.34% | 0.00 | 28.8 bp |
| vol-target the whole portfolio (36 mo) | −56.0% | 12.76% | 0.25 | 2.5 bp + tax |
| a return-timing rule | see [timing rules](timing-rules-on-the-equity-sleeve.md): `unresolved`, +0.74 pp/yr against MDE₈₀ 3.03 | | | |

**Read the first row against the second.** Holding 0.90 of equity and nothing else buys a
drawdown 3.9 points shallower than 1.00 of equity, for nothing, in one trade, with no wrapper,
no financing, no Cayman subsidiary and no forecast. On this panel the 0.30 overlay's own
drawdown reduction is under one percentage point. **The overlay is not a drawdown instrument at
this size. It is a return bet and it must be argued as one.**

That does not make it a bad bet — its geometric return is 2.9 pp/yr higher than the 0.90-equity
row's, at the panel's realised premium — but it relocates the argument. The overlay's case is
that it raises growth at unchanged drawdown, which requires a forward trend premium above the
break-even in §4.1, and **that is exactly the quantity nobody here can sign.**

---

## 9. The sized recommendation

**Not a recommendation on the repository's behalf.**
[Decision 0004](../decisions/0004-no-sleeve-promoted.md)'s non-promotion stands, no sleeve is
promoted, and the zero-leverage default for what this repository recommends is unchanged.
What follows informs a decision the investor makes.

**Size: 15% to 25% of capital in the stacked fund, centre 20%.** That is 0.15 to 0.25 of trend
notional and a gross notional of **1.16× to 1.27×**, against the proposed 1.32×.

**The objective it is optimal for:** expected after-cost log growth **subject to holdability**
— both kinds. It is not the growth optimum (that is 0.49 at a 1.80% premium) and it is not the
variance minimum (−0.015 here, +0.216 elsewhere).

**Two constraints bind, from opposite directions, and they agree.**

| route | what it constrains | answer |
| --- | --- | ---: |
| §6a, tracking error | how long a stretch of *relative* underperformance is holdable — 374 bp/yr of overlay TE, a central-case worst relative run of −21.3% over 320 months, 5th percentile −42.4% | argues for cutting 0.30 |
| §3.2, valuation-conditioned drawdown | how deep an *absolute* loss is holdable at CAPE 41, applying the 1.411× ratio to a stated tolerance | **19.1%** at a −50% tolerance, 14.9% at −40% |

**What does not bind.** Drawdown as measured on the unconditioned panel — §3.1 shows no
tolerance in range binds the trend notional. The resampled cliff — §3a puts it at 0.58–0.59,
nearly three times anything considered here, and shows it to be an episode-identity artefact
of one panel.
The growth optimum — §2.2 shows its 95% interval spans 1.0 on any sample under about
twenty-five years.

**Both binding routes land inside 15–25% and neither of them is a forecast of trend returns.**
That is the strongest thing this page can say, because the trend forecast is the one input it
cannot supply.

**Why 20% and not 30%, in one line:** the move gives up **4.5 bp/yr** of expected growth at the
repository's own forward premium and removes **a third** of the benchmark-relative risk that
would break the position. Being at 0.20 against the model's own 0.54 optimum retains **60%** of a
peak that is itself only 22.7 bp/yr; **the left branch of the growth parabola is nearly flat here and the
holdability cost is not.**

**Why not zero:** at a 1.80% gross premium the overlay's contribution is positive, the wrapper
keeps 100% of the funding-rule gap (`delta = −0.07`), the structure and cost are verified from
filings, and §7 shows a real 4-to-10-point drawdown benefit in the slow crises (5.4 points in
the GFC, 4.2 in the dotcom bust, 10.5 in 1973-74). **Why not 30%:**
the break-even is 1.19% and moves to 2.31% across the financing grid, so the sign is not
established, and 30% sits at 61% of an optimum computed from a premium the repository will not
underwrite.

**Confidence.** Low on the number, moderate on the direction, high on the framing.

- **High confidence** (arithmetic, or filed): the exposure table in §1, the sign-flip premium,
  the kink, the `1 − (1 − f)**2` retention, the financing identity, and the fact that the
  overlay is the whole tracking-error budget.
- **Moderate confidence** (one panel, `exploratory`): the drawdown ladders, the crisis table,
  the cliff's location and mechanism, the vol-targeting null.
- **Low confidence** (a forecast this repository refuses to make): everything that depends on
  the forward trend premium — which is to say the *sign* of the whole overlay contribution.
  §4.1's grid is the honest statement of that, and 1.80% sits inside it.

**The single measurement that would change this answer** is a fund-level financing spread. It
is no longer a measured RSST trend loading: that has been estimated from the fund's own Form
N-PORT returns at **+0.681 [+0.406, +0.955] over 31 months to 2026-04**, against an equity
beta of +0.979 ([comparability](loading-comparability-and-wrapper-exposure.md)). Every trend
figure on this page is still a figure about *the exposure*, and the correction is now
sized rather than unknown: the fund delivers about seven tenths of a dollar of index per
dollar of filed notional, on an interval wide enough that a full dollar is not excluded.

---

## Verified, assumed, open

**Verified here.** The exposure arithmetic against the filings. The kinked growth optimum
against a 500,001-point grid search on the objective itself. The two-asset optimum against a
1,201² grid search. `premium_for_leverage` as the exact inverse of `kelly_leverage` at twelve
parameter pairs. The trailing-volatility rule's absence of look-ahead, by perturbing one future
observation and checking that no earlier leverage moves. Joint resampling, by confirming that a
constant-ratio pair has zero spread in relative terminal wealth. The published `P(deeper)`
figures of 6.9% and 10.8%→18.9%, reproduced exactly and then localised and explained.

**Assumed on this page.**

1. **The trend leg is a construction, not RSST.** No loading has ever been measured for the
   fund. Every trend figure is about the exposure.
2. **The financing spreads are borrowed, not measured**: 62 bp for equity index futures over
   3-month Term SOFR, 15 bp for Treasury futures over OIS, ≈0 signed for a long/short book.
   §4.1 varies all of them.
3. **The panel excludes 1929-32** by the trend leg's burn-in, so every drawdown is measured on
   a sample missing the deepest US equity fall on record.
4. **§3.2 transfers a ratio, not a level.** The −51.8% and −36.7% are real fifteen-year
   drawdowns from [valuation and the allocation](valuation-and-the-allocation.md); this page's
   ladder is nominal and full-sample. Only 1.411× is carried across, on the assumption that
   the nominal-to-real conversion does not itself depend on the valuation regime.
5. **A block-stationary null** in §5 and §6a, which destroys dependence beyond 24 months.
6. **Nominal, US, pre-tax throughout.** No tax is charged anywhere on this page; §6's turnover
   is the place where that omission is largest and it is named there.
7. **MATE's trend leg is a prospectus target**, not a filed number; JPFP has no profile at all.

**Open.**

1. **The fund-level financing spread.** It decides the sign. Nothing on the shelf discloses it
   and no fee table can.
2. **RSST's loading on a trend benchmark.** Needs a licensed total-return series.
3. **Which correlation is right** — this panel's +0.011 or the +0.216-implying −0.166. §8's
   sensitivity is the honest interim answer, and the crisis-conditional dependence in §7 is
   what would actually settle it.
4. **A tax-aware version of §6.** The vol-targeting null is robust enough that tax cannot
   rescue it, but the same machinery applied to a rule that *did* survive would need it.
5. **The 2.0 pp/yr materiality threshold and the 0.30 pp/yr sleeve bar** remain undefended
   ([decision 0009](../decisions/0009-blocks-lifted-and-closures-rescoped.md) clause 7). This
   page uses neither.

**Reproducibility.** `cd research && uv run python -m portfolio_edge.studies.notional_budget`.
Panel imported from
[`studies/_overlay_stress_tables.py`](../../research/src/portfolio_edge/studies/_overlay_stress_tables.py);
closed forms in
[`studies/notional_budget.py`](../../research/src/portfolio_edge/studies/notional_budget.py);
tests in `research/tests/unit/test_studies_notional_budget.py`. Seeds 20260817 (+1, +3, +5),
12345, 999983, 20260822; 4,000 resamples; 24-month circular blocks. Cash rates refreshed from
FRED on 2026-08-22.
