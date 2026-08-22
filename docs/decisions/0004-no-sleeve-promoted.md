# 0004 — No sleeve is promoted; the portfolio is the control alone

Date: 2026-08-12. Status: accepted. Amended 2026-08-12, 2026-08-16 and 2026-08-17 as
Experiments 005, 013, 014 and 015 landed; **the non-promotion itself has never changed.**
[Decision 0009](0009-blocks-lifted-and-closures-rescoped.md) lifts the step 6 and step 7
blocks this record argues against itself about below, and leaves the non-promotion
standing. Supersede rather than amend when the first sleeve is promoted.

## Context

A research programme with this much apparatus invites the assumption that the apparatus
produced a portfolio. It has not.

**The per-hypothesis status table that used to sit here is deleted.** It was a snapshot
that was deliberately not refreshed, and a decision record holding a stale copy of
generated facts is a status journal wearing an ADR's clothes. The ledger is the only
thing that knows what was run:

```sh
cd research && uv run python -m portfolio_edge.reporting.programme_status
```

The per-candidate reading is on the [design map](../research/portfolio-edge-research-framework.md#the-design-map);
the instrument's limits are in [the evidence base](../research/evidence-base.md).

What matters for this decision is the shape rather than the counts. Every terminal status
is `rejected`, `unresolved`, or capped at `exploratory` by the fund-level data contract
([decision 0002](0002-no-research-grade-free-price-source.md)). Nothing has reached
`walk-forward-tested`, `shadow-live` or `production-eligible`, and nothing could have.
Where a row is `unresolved` the window could not detect the effect — which is not the
same as the effect being absent, and
[decision 0009](0009-blocks-lifted-and-closures-rescoped.md) now requires that
distinction to be carried in the verdict rather than in a footnote.

Recording this is not bookkeeping. The failure mode of a research programme with this
much apparatus is that a reader assumes the apparatus produced a portfolio.

## Decision

**No candidate sleeve is promoted. The research portfolio is the cheap broad-market
control alone** ([decision 0003](0003-cheap-broad-market-control.md)), plus the
deterministic cost, tax-location and do-not-trade discipline that the
[edge decomposition](../research/expected-edge-decomposition.md) prices at about
89 bp/yr against the investor's own counterfactual.

Consequently:

- **Leverage stays at zero.** It was conditioned on an unlevered edge surviving the
  protocol. None has, so there is nothing to lever. **The reasoning is contested and
  the contest is derived, not rhetorical** — see the consequences below, where the
  hurdle a sleeve must clear is shown to move by `a_p - sigma_p**2` with the funding
  rule. The rule stands until a decision supersedes it; what has changed is that its
  cost is now a measured number rather than an assumption.
- **Rebalancing is retained as risk control and forbidden as return.** It held
  exposure within 0.6 to 3.1 percentage points of target against buy-and-hold's 14.8,
  for 0.3 to 1.2 bp/yr. Anyone who wants their declared allocation to remain their
  actual allocation should rebalance. No rebalancing-bonus feature may be built.
- **The forty-eight `exploratory` US products and twelve ex-US products may be used as
  implementation proxies in a later experiment and for nothing else — and on the ex-US side
  only eight of the twelve survive a fair comparator.** That list was
  fifteen US products until 2026-08-17 and the change is a frame correction, not a new
  result: Experiment 002's numbers reproduce to zero difference on every fund it audited.
  **The shortlist now includes every systematic value and small-value product on the US
  shelf** — AVUV, AVLV, AVSC, DFAT, DFSV, DFUV, DFLV, DFAS — which the old frame excluded
  by construction. `exploratory` still permits testing and nothing else, and none of them
  has an alpha its own window could measure.
  **The count is 48 on the frozen comparator and 47 to 49 on comparators that can express
  what these funds deliver**, so the number quoted must always name its basis. The single
  US product whose status does not survive a fair comparator is **IWN**, replaced at a corner
  by a small-value index fund at a fifth of its fee; **all nine systematic value and
  small-value products survive every basis tested**
  ([Experiment 014](../research/factor-products.md#what-the-comparator-decided-measured)).
  **The ex-US list is the one that shrinks.** Of its twelve, **AVDV, AVIV, DFIV, DISV,
  IDMO, IVLU and SCZ survive every basis tested**, EFV survives all but the one that hands
  a second EAFE value fund to a fund that *is* EAFE value, and **IMTM, FNDC, SCHC and DFIS
  do not survive at all**: each loses to a cheaper fund in its own cell once the basis
  carries one — IMTM to IDMO at 0.25% against its own 0.30%, the other three to a
  developed-ex-US small-value column
  ([Experiment 015](../research/factor-products.md#do-the-twelve-incumbents-hold-four-of-them-do-not)).
  **The seven survivors have since been decomposed into every leg on their own panel**, and
  the two small-value ones — AVDV and DISV — carry SMB loadings of **+0.671 and +0.431**
  against −0.11 to −0.29 for the four large-value funds, with AVDV carrying **RMW +0.386**
  besides. Both legs are exposures to premia this repository cannot sign, so **the ex-US
  shelf reproduces the US shelf's ordering: large value ahead of small value**, from
  independent data ([factor products](../research/factor-products.md#what-the-value-funds-also-buy)).
  Nothing about that promotes the large-value funds; two of them carry raw alphas their own
  windows can measure and both are negative.
- ~~**No number from `research/` may appear in the shipped application as a
  finding.**~~ **Lifted by [decision 0007](0007-application-may-render-research.md)**,
  which replaces the ban with four constraints. Everything else in this record stands
  in full, including the non-promotion itself.

## The conditions that would change this

Each is a measurable target, not a hope. A sleeve is promoted only when its own row's
condition is met *and* it beats the control on the terms in decision 0003.

The chain matters as much as the rows. What a shareholder receives is
`premium × delivered loading − cost`. Experiment 002 measured the second and third and
found the loading delivered and the cost measurable; Experiment 001 could not sign the
first for any factor. **No product can be promoted while its underlying factor is
unsigned**, which is why every product row below points back at a factor row.

| Candidate | Condition for promotion |
| --- | --- |
| Value | The premium is now signed (`exploratory`), so **one condition remains** — the capture fraction is no longer among them, because [it is an HML loading rather than a multiplier](../research/long-only-capture.md#the-correction-a-capture-fraction-is-a-loading-so-it-may-not-multiply-one) and Experiments 002 and 013 already measure those. What remains is a product meeting Experiment 002's frozen promotion protocol — loading ≥ 0.15 with a 95% interval excluding 0.15 from below, the same on both fixed halves, shortfall ≤ 0 pp/yr against a replication fitted on a **prior** window, and total cost of ownership including realised distributions and turnover ≤ 1.0 pp/yr. **The candidate set is larger and higher-loading than it was.** VBR already met the first two clauses on Experiment 002's frame at +0.410, with halves of +0.431 and +0.451. On the corrected frame AVUV does so at **+0.537 `[+0.43, +0.64]` over all 72 months, with halves of +0.603 and +0.467**, and beats an *in-sample* four-fund replication by 4.92 pp/yr — **4.23 pp/yr of which survives a replication that contains a small-value fund**, the remaining 0.69 having been the comparator's inability to express small value ([Experiment 014](../research/factor-products.md#what-the-comparator-decided-measured)); DFAT, DFSV, AVLV, DFUV, DFLV and RPV clear the loading clause too, five of them on windows shorter than the fixed halves. What is still missing is unchanged and still binds: the **prior-window** replication the protocol asks for, which no experiment here has fitted; a bootstrap interval on each half, which none computes; and any evidence that a 36-to-72-month loading forecasts the next one |
| Profitability (RMW) | **Closed on public data** ([decision 0005](0005-factor-premia-closed-on-public-data.md)). Reopening needs a materially longer out-of-sample window — roughly a further decade — or a genuinely independent, non-French premium series. Not another pass over these files |
| Momentum | A net premium computed from **observed** turnover rather than assumed tiers, with one-sided monthly turnover below 50%. **The second condition is met and was met by a frame correction rather than by a new product.** "The entire retail shelf clearing a $1bn / 0.60% screen is one fund" was true of the 2019Q4 census only: the corrected frame carries six — MTUM, SPMO, XSMO, XMMO, VFMO and JMOM — of which four reach `exploratory` with loadings from +0.372 to +0.462 and shortfalls from −2.49 to −4.53 pp/yr. The premium condition is untouched and still binds. **The ex-US momentum path, which is where Experiment 006 located the premium, is two funds and one of them does not survive its own comparator**: IDMO at 0.25% holds `exploratory` under every basis tested, and IMTM at 0.30% is `rejected` once the basis carries IDMO ([Experiment 015](../research/factor-products.md#do-the-twelve-incumbents-hold-four-of-them-do-not)) |
| Investment (CMA) | **Closed on public data** ([decision 0005](0005-factor-premia-closed-on-public-data.md)). Re-entry requires a new frozen specification on a genuinely post-2026 window. The current rejection stands |
| Size | **The premium test has now been run and it fails, on every panel this repository can reach.** SMB is **+0.33 pp/yr pooled over three regions, `[−1.32, +2.06]`, against a 2.47 pp/yr detection floor**; developed ex-US +0.49 against 2.83, emerging −0.05, US +0.29 post-Banz ([factor persistence, §Size](../research/factor-persistence.md#size-on-the-three-panels--a-study-not-an-experiment)). **The ex-US legs were measured and not transferred**, which mattered because HML is three times larger abroad. The consequence is not a status for a factor but a restriction on every product row: **no chain may price an SMB loading**, so a small-value fund's size leg is variance with no priced expectation on both shelves. Reopening needs an instrument that can resolve below 2.5 pp/yr, which no pooling of these files can |
| Trend | A multi-asset attribution leaving a residual after non-US-equity exposures; a fund-level audit on a licensed total-return source with real fees; and a contract-level test of the volatility scaling, which no public aggregate can support |
| Rebalancing as return | A real, investable, low-correlation pair whose drift gap is genuinely below its `gamma_star`. **Half-met, and the half that is met does not promote anything.** Over 1963-2020 US against an equal-weight ex-US basket had a drift gap of 0.05 pp/yr against a `gamma_star` of 17.2 bp — the condition holds — but the correlation is **+0.75, not low**, the near-equal drift is known only in retrospect, and the measured prize is **12-18 bp/yr gross** ([rebalancing §6](../research/rebalancing-policy.md)). A rounding error is not a sleeve |
| Anything fund-level | A licensed, survivorship-free, point-in-time total-return source covering the listed shelf from at least 2003, so the window is 240 months rather than 72. Required contents are specified in the research framework under "The next experiment" |

**Experiment 005 has run and did both things at once.** Value advanced; profitability
and investment were closed on public data. The next step was recorded here as the
measurement of the long-only capture fraction. **Experiment 007 took it, and the answer
removed the term rather than filling it in**: a capture fraction is an HML loading
measured a second way, so the chain for value is
`premium × (fund loading − incumbent loading) − cost` and every term in it is already
measured ([Experiment 007](../research/long-only-capture.md#the-correction-a-capture-fraction-is-a-loading-so-it-may-not-multiply-one)).
**The immediate next step is still not a promotion attempt and still not the purchase.**
It is the **prior-window** replication the frozen protocol asks for, which no experiment
here has fitted.

## Alternatives considered

**Promote the trend sleeve as `exploratory` and build it.** Rejected. Its own
specification caps a vendor-series evaluation at `exploratory`, its falsifier fired,
and the vendor states no cost basis anywhere in the archived workbook, so every
figure is gross of the vendor's own trading costs by omission.

**Promote RMW on the grounds that it is the only factor that did not decay (96%
retained).** Rejected then as a prioritisation rather than a finding, and now closed
outright: pooled across three regions its premium is +2.53 pp/yr against its own
measured 2.62 pp/yr detection threshold, 62% of its US premium is the single year
2021, dropping the pooled best year takes it to +1.79, and its volatility carries an
unresolved ±5.09% systematic band from Phase 1
([decision 0005](0005-factor-premia-closed-on-public-data.md)).

**Promote value now that its premium is signed.** Rejected. `exploratory` is the
lowest rung of the ladder and permits an implementation to be *tested*, nothing more.
The premium is gross, long-short and not investable; what a long-only fund delivers of
it is a **measured** loading of +0.537 rather than the whole of it; and its pooled figure
is carried by the two non-US regions, with the largest leg in emerging markets where
shorting is hardest and dearest. The US leg alone is +1.57 on an interval of
`[−2.28, +5.54]`, and on that premium a 20% tilt's contribution to geometric growth is
**negative at every weight**.

**Report the 2000–2019 era, in which annual rebalancing was worth +0.575 pp/yr and
cleared the materiality threshold twice over.** Rejected, and the rejection rule was
frozen in advance precisely so this could not be reported as a finding: it is one
twenty-year window inside a thirty-five-year sample, bracketed by two windows of the
opposite sign.

**Say nothing and leave the absence implicit.** Rejected. An unrecorded non-promotion
decays into an assumed promotion.

## Consequences

The deliverable of this research programme is a design map and a control, not an
allocation. An allocation becomes appropriate only after the investor policy is
defined — benchmark, horizon, tax status, liabilities, cash flows, drawdown
tolerance, liquidity reserve, permitted instruments and objective — which remains
open decision 1 in the research framework.

Steps 6 and 7 of the framework's build order — portfolio combination, then
fractional/risk-constrained Kelly and leverage — are blocked, and not on effort.
Step 6 combines sleeves and there are none; step 7 sizes an edge and there is none.

**Step 6's block is contested and should be lifted.** The reasoning above is circular
as applied to the *construction tournament*, which compares weighting **methods** —
market weight, equal weight, inverse volatility, constrained minimum variance,
linear-shrinkage minimum variance, equal risk contribution — on the three regional
equity sleeves and the cash leg that already exist. It does not need a promoted sleeve,
and it is the only designed experiment that treats a portfolio as a joint object rather
than as a base plus a marginal addition. The argument is in
[search coverage](../research/search-coverage.md) §5, together with the observation
that Experiment 010's portfolio-level closure turns on its 10% reference weight rather
than on evidence.

**Step 7's block is circular in the same way, and this is now derived rather than
argued.** The block reads *"it sizes an edge, and there is none"*. That is true of
leverage applied to a sleeve whose value has already been established. It is **false**
of the prior question, because whether a sleeve has positive marginal value **depends
on the funding rule**, and the funding rule is what step 7 forbids. From
[`studies/overlay_growth.py`](../../research/src/portfolio_edge/studies/overlay_growth.py),
which is closed-form algebra pinned by tests needing no market data:

- Funded **pro rata** — sell the base to buy the sleeve, which is what every marginal
  experiment here has done — the first sleeve dollar must clear
  `a_p - sigma_p**2 (1 - beta)`.
- Funded as a **financed overlay** — sell nothing, finance the notional, which is what
  a capital-efficient fund does — it must clear `rho sigma_p sigma_d`.
- The difference is **`a_p - sigma_p**2 = sigma_p**2 (L_p* - 1)`**, in which *every
  term involving the sleeve cancels*. It is **+2.44 pp/yr** for a 100%-equity base at
  a 5.0% arithmetic excess and 16% volatility, and **+2.08** for the 60/40 base
  Experiment 004 used.

So the zero-leverage rule is not a conservative simplification that costs a little
return. **It raises the hurdle every candidate sleeve in this repository has been
judged against by more than two percentage points a year** — larger than any premium
the programme has attempted to measure, and larger than the entire measured edge
budget. "There is no edge" and "no edge clears the pro-rata bar" have been used
interchangeably, and they are not the same statement.

**What follows, and what does not.** This is an argument for *asking* the question,
not for an affirmative answer, and three things stand in its way. Two are recorded
here rather than left for a later reader to discover:

1. **The cost stack, not the correlation, is what binds.** Financing spread plus fund
   fee plus distribution tax character is on the order of **1.4 pp/yr in a sheltered
   account and 3.5 pp/yr in a taxable one** on the placeholders currently available —
   against a post-publication trend excess return this repository measures at roughly
   1.8 pp/yr. The overlay bar is near zero; the cost stack is not.
2. **The honest control is leverage-matched, not unlevered.** At matched volatility
   the variance terms cancel and the higher Sharpe ratio wins outright, so an overlay
   that raises growth over *unlevered* equity while lowering the portfolio's Sharpe
   ratio has bought its gain with beta and must be labelled that way.
3. **The instrument is weaker than the effect.** A portfolio-level growth difference
   of the size at stake sits near the detection floor of a 35-year monthly window, so
   the experiment this unblocks is a **sizing** question with an interval, not a
   detection question with a verdict. Freezing it as the latter would repeat the
   error [search coverage](../research/search-coverage.md) §1.2 exists to name.

**Both blocks are lifted by [decision 0009](0009-blocks-lifted-and-closures-rescoped.md),
and the non-promotion in this record is untouched by that.** The step 6 tournament may
run, and the funding rule may be *measured* with overlay funding as a primary arm against
a leverage-matched control. What 0009 does not do is authorise leverage in a recommended
portfolio; the zero-leverage default and the non-promotion both stand.

This record should be superseded, not amended, when the first sleeve is promoted.
