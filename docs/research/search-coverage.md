# Where the search has looked, and why the null result is partly self-inflicted

**Question.** Seventeen experiment families have run and nothing is promoted. Is that a
finding about markets, or a finding about the search?

**Decision it informs.** What round two tests, and which of the programme's existing
closures should be reopened. This page is an audit of the *design* of the search, not
of any result in it. Every number here is quoted from an experiment page; none is new.

**Conclusion, stated directly.** **Mostly a finding about the search.** Four specific
design choices — each defensible when it was made, each now measurably load-bearing —
mean the programme has been looking in places where finding something was close to
arithmetically impossible, and in one case at a shelf two thirds of which was invisible. A
fourth problem is coverage: entire asset classes, the whole of conditional allocation, and
the only test that treats a portfolio as a joint object had never been run at all. **The
asset-class half of that closed on 2026-08-17** and none of it needed a purchase — the
last piece, a bond total-return history, was already in this repository's own manifests.

Two things this does **not** mean. It is not an argument that a tilt would have worked.
And it does not touch the results that are robust for reasons no amount of further
searching can overturn — those are in §4, and they are the most valuable things the
programme has produced.

`as of 2026-08-17`.

---

## 1. Four designs that could not have found much

### 1.1 A threshold above the arithmetic ceiling of the thing being measured

[Experiment 010](marginal-sleeve-value.md) asks the portfolio question: does adding a
sleeve to a portfolio that already exists raise its growth rate? Under pro-rata funding
the diversification credit is exactly `sigma_p**2 (1 − beta)` per unit of sleeve weight,
so at `beta = 0` it equals `sigma_p**2` and can go no higher:

| Base portfolio | Volatility | Ceiling at **10% weight** | Ceiling at the **20% cap** | Frozen bar |
| --- | ---: | ---: | ---: | ---: |
| `global_equity_core` | 14.73% | **+0.217 pp/yr** | **+0.434 pp/yr** | 0.30 |
| `balanced_60_40` | 8.85% | +0.078 pp/yr | +0.157 pp/yr | 0.30 |

The page states the first column and concludes that "the portfolio-level view is closed as
a route to rescuing a dismissed sleeve", because a perfect zero-beta asset would fail on
the credit alone.

**That closure is a property of the reference weight, and the reference weight was frozen
at 10% while the specification's own cap is 20%.** At the cap the ceiling exceeds the bar.
**The closure does not survive its own experiment's weight cap, and the page does not
revisit it there.** Nor is the weight question hypothetical inside the experiment: its own
re-selected-optimum table puts the in-sample optimum for all three small-value sleeves **at
the 0.20 cap**, with re-selected median gains of +0.75, +1.05 and +0.04 pp/yr. Those
medians are what an in-sample searcher would report and their intervals all reach exactly
zero, so they establish nothing — **but they are a live question the headline closure does
not engage.**

Two further limits on how much that experiment can settle. **Be precise about what it
does measure**, because the frozen specification is careful here and a loose reading would
repeat the error this page exists to name: the deciding clause reads a **finite difference
at the 10% weight**, not a derivative at zero, and the specification explicitly rejects the
derivative-at-zero as a criterion that "favours any low-beta asset by construction". The
`sigma_p**2 (1 − beta)` ceiling is the **first-order credit term**, and it is the credit
clause and the closure sentence that inherit the weight dependence.

- **A sleeve bolted onto a fixed base is not "the portfolio-level view".** Two base
  portfolios, both declared in advance, both equity-dominated, with one sleeve varied at a
  time. The portfolio-level question is the joint weighting of everything at once, which is
  the construction tournament — designed in the framework, never run.
- **Pro-rata funding is the least favourable rule for a diversifier.** Funding out of the
  highest-beta leg is the realistic alternative. The experiment computes `named_leg`
  results and reports the pro-rata ones as the headline.

**What is genuinely established by Experiment 010, and stands:** the credit is bounded by
`sigma_p**2 (1 − beta)`, it is *negative* for any sleeve with `beta > 1`, and every
long-only equity sleeve added to a 60/40 base has `beta > 1`. Adding equity to a
part-cash portfolio raises its risk and the credit charges for that correctly. **That is a
real result, and it is not what the closure sentence claims.**

**Update, 2026-08-17: this subsection's own question has been answered empirically, and the
answer is that the weight was the wrong thing to blame — the *funding rule* was.** Gold was run through the same
construction. Its beta to `global_equity_core` measures **+0.000**, so it takes the entire
`sigma_p**2 w` credit — **+0.217 at 10% and +0.434 at the 20% cap, the exact ceiling in
both cells, and the second is above the 0.30 bar.** Its marginal growth at the cap is
**−0.241 pp/yr.** So the cap does make the ceiling reachable, a real asset does reach it,
and **the sleeve fails anyway.** Per unit of weight the credit is **+2.171 pp/yr** and
gold's standalone shortfall against that base is **−2.95**, so the credit covers 74% of the
shortfall — **and because both terms are linear in the weight, that ratio does not move
when the weight does.** Raising the weight scales the loss rather than closing it. **The
design flaw this subsection names is real and it is not what was producing the nulls.** Round two's item 1 should be re-scoped accordingly: raising the
weight and deriving the bar from the ceiling are both correct and neither is sufficient.

### 1.2 A detection floor above the effect size that matters

[Decision 0005](../decisions/0005-factor-premia-closed-on-public-data.md) records the
measurement: across every independent region the Ken French library distributes, the best
pooled minimum detectable effect is **2.62 pp/yr**, against a 2.0 pp/yr materiality
threshold. Momentum's is **4.98**. The US-only figures are worse still.

That is an honest and unusually well-measured statement — and it means that **for the
whole factor programme, a null result was close to guaranteed before any data was read.**
Sixteen of Experiment 001's twenty cells hold a premium smaller than their own window can
detect. A zero-mean Gaussian series with HML's length and volatility, put through the
identical procedure, returns +1.98 pp/yr with a −53.2% drawdown; HML's real
post-publication figures are +1.57 and −57.8%. The instrument cannot tell them apart.

The corpus states this carefully and then, in its summary language, slides from *"public
factor data cannot sign this premium"* to *"the premium is closed"* to a general
programme-level pessimism about factor investing. Only the first is supported. The two
factors that did advance did so **because their premia are larger than the blind spot,
not because the blind spot closed** — and both pages say so.

**A fifth factor joined the list on 2026-08-18 and is the cleanest instance yet.** SMB was
measured on all three panels with the same machinery and reads **+0.33 pp/yr pooled,
`[−1.32, +2.06]`, against a 2.47 detection floor**
([factor persistence, §Size](factor-persistence.md#size-on-the-three-panels--a-study-not-an-experiment)).
The floor sits **above** the 2.0 materiality threshold, so the null was guaranteed in the
same way — and the study says so in its own text rather than leaving it to this page. What
makes it worth recording here is that the measurement was taken **because the US answer
might not have transferred**: HML is three times larger outside the United States, so
assuming SMB behaved the same way would have been a search failure of exactly the kind
[§2](#2-the-universe-and-how-much-of-it-has-been-searched) catalogues. It did transfer, and that is now a
measurement rather than an assumption.

**The consequence for round two is narrow and useful:** no further experiment on these
files can resolve anything in the 0–2.6 pp/yr range, so a question in that range needs a
different instrument, not a different pooling scheme. Decision 0005's reopening
conditions are correct. Its framing — "closed, not paused", "provably will not" — is
stronger than the evidence, since one of its own reopening conditions is simply the
passage of about a decade.

### 1.3 A rejection rule driven by an in-sample fitted comparator

Clause (c) of the product falsifier rejects a fund whose tracking difference against a
combination of cheap broad funds is worse than its fee advantage by more than
0.50 pp/yr. The combination's weights are fitted **by constrained least squares on the
same months being evaluated**.

It fired on **22 of the 24 US rejections** and **5 of the 8 ex-US ones** — 27 of 32
rejections in the whole product programme.

Both pages state the look-ahead plainly and instruct the reader to interpret every (c)
rejection as *"a look-ahead combination of cheap funds beat this product over these
months"*, never as *"this product is badly run"*. That instruction is correct and it is
routinely dropped when the counts are quoted. Three facts make the counts weaker than
they look:

- **Tracking error against the combination runs 1.38 to 8.65 pp/yr, median about 5.** A
  difference of means with that dispersion over 72 months is not resolvable at
  0.50 pp/yr. Clause (c) is a decision rule applied as frozen, not a measurement.
- **Three of the four US basis funds are themselves audited products**, and a fund is
  never in its own basis, so the replication degenerates for exactly those three. VB's
  and VTV's rejections read as *"small-cap and value underperformed the market over
  2020–2025"* — a statement about the window.
- **The largest intended loading in the entire ex-US audit, GWX at +0.856, belongs to a
  rejected fund.** Exposure delivery and implementation value are different questions and
  the rejection counts answer only the second.

The honest summary of the product work is the asymmetry, not the counts: **96 of 109
loadings survive correction and 5 of 327 alphas do, all five negative.** Exposure is
measurable; implementation value over 72 months against a fitted comparator is a
judgement call applied consistently.

**Update, 2026-08-17. The counts in this subsection were also a property of the census
frame, and §1.4 is now the larger version of the same problem.** Clause (c) fired on 22 of
the 44 products Experiment 002's frame could see. On the frame that sees the whole US
shelf it fires on 35 of 109 — and on only 13 of the 65 funds the correction admits, whose
median shortfall is **−0.48 pp/yr**. The design criticism above stands in full: the
comparator is still fitted in sample and the tracking error still dwarfs the threshold.
What changes is its direction. **It was suppressing a positive answer, not manufacturing
a negative one**, and the funds it was hardest on were the ones the frame had already
removed.

**Second update, same day, and it upgrades this subsection from a criticism to a
measurement.** Experiment 013 flagged, against itself, that its basis contains **no
small-value fund** and therefore cannot express what the products with the largest negative
shortfalls deliver.
[Experiment 014](factor-products.md#what-the-comparator-decided-measured) re-scored the
same 109 funds under **six bases**, varying nothing else and reproducing the frozen basis
to zero difference first. Three results, and the third is the one this page exists for:

- **The nine systematic value and small-value products keep 73% of their shortfall
  magnitude** under a complete cheap style grid, and **all nine keep their status**. AVUV
  goes from −4.92 to −4.23 pp/yr; the largest single attribution is DFAT's +1.62; two of
  the nine move the other way, the frozen basis having been *harder* on them.
- **47 of the 48 `exploratory` statuses survive.** The one casualty is IWN, and the shelf's
  count reads 47 to 49 across expressive bases.
- **Two placebo bases — as many columns as the most expressive basis, and not one new
  size-by-style cell — moved 9 and 15 verdicts, against 1, 5 and 5 for the expressive
  ones.** So across the shelf **clause (c) responds more to the number of columns a
  look-ahead fit is handed than to what they span**, and the two placebos differ from each
  other by six verdicts, which is the noise floor under any comparison of this kind.

**The generalisable rule: an experiment that fits a comparator must fit a placebo
comparator beside it.** Without one, a movement in the count cannot be attributed to what
the added funds express, and this repository would have attributed it wrongly — the
expressive bases look like the larger intervention and are the smaller one. **The ex-US
audit's five clause (c) rejections have never had this treatment and are owed it.**

### 1.4 A frame that could not see the shelf it was auditing

**This one is not a threshold or a floor. It is a census that does not contain what it
was assumed to contain, and it is the only entry in this section whose correction has
already been run and has already changed a published conclusion.**

[Experiment 002](factor-products.md#the-us-shelf-as-experiment-002-framed-it) screened the
SEC's **2019Q4** Form N-PORT data set — every fund that filed for the quarter — and took
its frame at the start of the window on the correct general principle that screening
today's listings selects on survival. Nobody checked what that file contains.

**Form N-PORT is filed on each series' own fiscal calendar, and public reporting begins
with periods ending 2019-09-30.** The 2019Q4 file therefore carries fiscal quarters ending
2019-09-30 and 2019-10-31 and nothing else. It contains **zero series with an August
fiscal quarter-end, against 2,507 in the 2025Q4 file.**

So the frame excluded, by accounting calendar rather than by any screen criterion, the
whole of Schwab's equity range, Vanguard's ETF-only trusts, Invesco's S&P factor range and
Avantis. The 2016-12-31 inception cutoff then removed, latently, every product that
launched or converted later — Dimensional's 2021 and 2022 ETFs among them. **Experiment
002 audited 44 US factor products. The union of the two censuses contains 109.**

Three things make this the most consequential design flaw on this page.

- **The exclusion is not random and its direction is knowable in advance.** It removes the
  newest products, which on this shelf means the cheapest systematic ones. Every US
  systematic value and small-value product — AVUV, AVLV, AVSC, DFAT, DFSV, DFUV, DFLV,
  DFAS — was outside the frame.
- **It moved the conclusion, not just the counts.** Clause (c) fired on 22 of the 44
  products inside the frame and on **13 of the 65 outside it**, whose median shortfall to
  the cheap replication is **−0.48 pp/yr rather than +0.53**. The page's title claim,
  *"the exposure is delivered, the value is not"*, was true of the funds a filing calendar
  let it see.
- **The repository already knew the fix and applied it to the other shelf.**
  [Experiment 009](factor-products.md#the-ex-us-shelf) used the union of the two censuses
  in August 2026 and wrote down exactly why: *"A 2019Q4-only frame would have excluded
  exactly the products the question is about."* That sentence was about ex-US products and
  it was equally true of US ones. **The gap was between two experiments in the same
  repository, a fortnight apart, and nothing flagged it.**

**What this costs and what it does not.**
[Experiment 013](factor-products.md#the-us-shelf-on-the-corrected-frame) re-ran Experiment
002 with two criteria moved and nothing else, and reproduced every one of its 44 funds to
**zero difference** in loading, alpha, shortfall and status. So no arithmetic was wrong
and no method was wrong. What was wrong was a claim about a shelf, drawn from a census
that held a third of it.

**The generalisable rule, which is the reason this belongs on this page**: a screen
applied to a periodic regulatory filing inherits that filing's own calendar. **State which
periods the file contains before reporting a count from it.**

**Checked, and Experiment 002 is the only page exposed.** The 2025Q4 file carries fiscal
quarters ending in August, September and October, and every registrant has exactly one
quarter-end in that span, so a union frame containing it is calendar-complete. Experiments
008, 009, 012 and 013 all use that union. Experiment 002 is the only census-based screen
in this repository that used the 2019Q4 file alone, and it was the first one written.

---

## 2. The universe, and how much of it has been searched

The denominator. Eight families were named at the outset; the programme has run
seventeen experiment families, almost all of them inside two of the eight. This table is
the honest ratio of searched to searchable, and it is the reason the null result is
mostly a fact about coverage.

| Family | Named at the outset | Searched | Status |
| --- | --- | --- | --- |
| **A. Equity factor premia** | value, momentum, quality, profitability, investment, size, size×quality, low beta, multifactor integration, shareholder yield and buybacks, earnings revisions, PEAD, accruals, net issuance, short- and long-term reversal, equal weighting, concentrated vs diluted factor portfolios, international and emerging implementations | HML, UMD, RMW, CMA, SMB on three regions; BAB, STR, LTR, buybacks, net issuance, QMJ, accruals full-sample and post-publication | **Partly.** Value and momentum `exploratory`; RMW and CMA unresolvable at this floor; SMB unsignable. Seven further families measured and every post-publication estimate sits below its own detection floor. **PEAD is published by neither French nor AQR and was never tested.** Earnings revisions, size×quality, integration-vs-sleeves, and simple-sort-vs-continuous-signal are untouched |
| **B. Trend and managed futures** | signal speeds and ensembles, breadth across four asset classes, programs with and without equity-index futures, volatility scaling, direct models vs replication, single- vs multi-manager, crisis behaviour, whipsaw, inflation regimes, collateral yield, notional and vol target, tax | one vendor index, five then fifteen listed products, and 46 funds' filed net returns | **Deeply.** Three independent instruments agree on sign. Signal speed, ensembles and direct implementation are untested; every result is on someone else's signal |
| **C. Cross-asset alternative risk premia** | cross-asset value, carry, momentum, defensive, factor momentum, macro momentum, curve and term premia, currency and commodity value/carry/momentum, credit, market-neutral multifactor, global macro, VRP, tail risk | AQR Century of Factor Premia at the aggregate level; VRP through PUT and BXM | **Barely.** Rejected **on cost** — gross long-shorts at 2–5% vol against a ~1.5% retail wrapper, needing ~5× notional — not on decay. No individual premium was tested on its own terms |
| **D. Capital efficiency and portable alpha** | return stacking, financing, collateral, margin, portable alpha | eight wrappers audited from filings; the funding-rule algebra derived and measured | **Well, and the finding is the largest on the page**: the funding rule moves a sleeve's hurdle by ~2.44 pp/yr, containing nothing about the sleeve |
| **E. Commodities, gold, inflation** | physical gold, gold futures, miners, diversified commodities, commodity trend/carry/value, inflation swaps, TIPS, breakevens, resource equities, collateral | gold on 618 holdable months and through two wrappers; commodities via AQR CLR; TIPS against nominals | **Partly.** Gold passes admission and is dominated; commodities pass and are dominated; TIPS are inside the nominal engine. **Commodity trend, carry and value as separate signals, miners, breakevens and resource equities are untouched** |
| **F. Event-driven and structural** | merger arb, convertible arb, equity market neutral, closed-end discounts, spin-offs, index reconstitution, cat bonds, securities lending, volatility selling, put writing, covered calls, defensive overlays, dispersion, direct indexing | cat bonds, merger arb, closed-end funds, lending, direct indexing, dividend, REITs, buffer, bitcoin | **Partly.** Cat bonds are the only pass and are vehicle-constrained. **Convertible arb, equity market neutral, spin-offs, index reconstitution and dispersion were never mentioned** |
| **G. Illiquid and private markets** | private equity, venture, private credit, direct lending, real estate, infrastructure, secondaries, interval and tender-offer funds | nothing | **Never started, and never recorded as skipped.** The largest untouched family. It needs the stale-pricing, smoothing, backfill, leverage, carry, dispersion, lockup and PME corrections the outset already listed |
| **H. Exploratory** | ML stock selection, nonlinear interactions, alternative data, sentiment, insider and congressional trading, options-derived signals, crypto momentum/carry/value/network, capacity-limited microcap, concentrated systematic, tactical valuation, dynamic factor timing, country and industry momentum | spot bitcoin only | **Barely.** Thirteen of fourteen untouched. A higher evidence burden is not a reason not to look |

**Two families carry almost the whole programme.** A and B account for fourteen of the
seventeen experiment families. C, G and H — three of the eight — hold one tested item
between them. A null over that distribution is a statement about where the light was
pointed.

### What has never been tested, across families

| Never tested | Why it is absent | What it would need |
| --- | --- | --- |
| **Joint portfolio construction** — market weight, equal weight, inverse volatility, constrained minimum variance, linear-shrinkage minimum variance and ERC compared on identical point-in-time inputs | It was designed in the framework with comparators and falsifiers, then blocked by [decision 0004](../decisions/0004-no-sleeve-promoted.md) because "step 6 combines sleeves and there are none" | **Nothing.** A construction tournament compares *weighting methods* on assets that already exist and needs no promoted sleeve. [Decision 0009](../decisions/0009-blocks-lifted-and-closures-rescoped.md) lifts the block |
| **Leverage and financing as a research question** | Deferred on the grounds that it "sizes an edge and there is none" | **Nothing, and the deferral was the costly one.** Whether a sleeve *has* an edge depends on its funding rule, and the funding rule is what the deferral forbade. Gold's marginal contribution swings −0.395 → +0.182 pp/yr on the funding rule alone, against a 0.30 bar |
| **Any conditional or dynamic allocation** — valuation-conditioned equity share, regime conditioning, trend applied to the portfolio rather than as a sleeve | Never proposed | An experiment. The Goyal–Welch and Shiller instruments are held |
| **Concentration** | Every sleeve tested is a diversifier or a tilt. The variance penalty is measured at **0.17 pp/yr at twenty-five names**, so the objective is near-indifferent above ~25 and the real argument is return skewness, which `gamma_star` does not contain ([capital efficiency §8](capital-efficiency-and-breadth.md)) | A cross-sectional skewness test. No detection floor here resolves it |
| **Whether a fund's 36–72-month loading forecasts the next 36–72** | Named as open on three pages and owned by none | **Nothing — this is the cheapest unrun experiment in the repository.** N-PORT Item B.5 gives 78 months across 109 funds and is already held. It is the gating condition on the value tilt in the framework's own design map |
| **Delivered exposure from a fund's holdings** | Named as the next experiment and not run. Every exposure figure here comes from a return regression | N-PORT holdings, already held |
| **Any equity market's history but the US at long horizon** | No longer blocked — the Jordà–Schularick–Taylor panel gives 16 countries, 1870–2020 ([evidence base §2](evidence-base.md)). It already shows **−50.3% is nowhere near a bound**: 15 of 16 countries did worse inside the same 1963-onward window | An experiment, not an acquisition |
| **After-tax anything, at the lot level** | No experiment holds a tax lot, so none may price a realisation | Lot-level modelling |

### The search failure that recurs

Six sources were recorded as unavailable and were published the whole time:
Goyal–Welch, Shiller, gold, French's `RlEst` industry return, FRED's bitcoin price, and —
worst — the bond total-return leg, which was **already downloaded, parsed, hashed and
manifested in this repository** while every published bond figure came from a modelled
`GS10` proxy.

A seventh instance is not a data failure but an imagination one. The audit had covered 69
factor ETFs, 15 managed-futures ETFs, 8 capital-efficient overlays, catastrophe bonds,
merger arbitrage, closed-end funds, commodities and gold — and had never mentioned SCHD,
REITs, the buffer family or spot bitcoin, because the list it was working from contained
only exotic strategies. All four are now audited, none is promoted, and **the four fail
for four different reasons**, which is the evidence that the omission cost information
rather than merely looking careless.

**The rule, in its strongest form: before pricing an acquisition, check whether the thing
is published — and before that, check `data-manifests/`. Then check the *reasoning* of
any decision that appears to forbid a source**, because a rule written against one
failure mode does not reach an asset that cannot exhibit it.

---

## 3. The answer to "there is no way this is correct at the portfolio level"

It is a fair objection and it lands, but not quite where it aims.

**Where it is right.** The repository has not taken entire portfolios into context. It has
tested ten marginal 10% sleeve additions to two fixed, equity-dominated base portfolios,
one sleeve at a time, funded by the rule least favourable to a diversifier, against a
diversification credit whose arithmetic ceiling at that weight sits below its own bar — and
it has never once optimised or compared a whole portfolio. The one experiment designed to
do that is unrun and blocked on a circular argument. So the sentence *"the portfolio-level
view cannot rescue a sleeve the standalone chain dismissed"* is doing far more work than
the evidence behind it supports.

**Where it is wrong, and this part will not move.** Portfolio-level thinking does not
repeal any of the following, and round two will not change them:

- **Sharpe's identity.** Before costs the average actively managed dollar earns the
  average passively managed dollar's return; after costs it earns less. This depends
  only on addition and subtraction. Aggregate active outperformance is bounded at zero
  by construction, whatever any individual portfolio does.
- **Tracking error, not edge size, decides whether a lifetime is long enough.** Because
  `T = (z s / e)**2`, the same 50 bp edge reaches 90% confidence in 24 days against 10 bp
  of tracking error and in 105 years against 400 bp. Combining sleeves *raises* tracking
  error against an index. A whole-portfolio construction that adds edge and dispersion in
  the same proportion buys no confidence at all.
- **The rebalancing result is not a power problem.** The realised drift gap between US
  and developed-ex-US equity ran 4.34 pp/yr against a `gamma_star` of 12.5 bp — a factor
  of 35 — and relative regional performance *trends* rather than reverts, at conventional
  significance in every pair. The theory predicted the loss to within 8 bp. That is a
  measured mechanism, not an unpowered null.
- **The largest reliably available edge is not a portfolio construction at all.** Fund
  cost, wrapper, account placement and lot method are worth far more, far more certainly,
  than any tilt this programme has priced. That ordering is robust to everything in §2.

---

## 4. What is robust regardless of round two

Recorded here so a re-specification does not accidentally relitigate settled work.

- **The closed forms**, all re-derived rather than cited, all pinned by tests that need no
  market data: the Kelly vertex form and its two boundaries; `gamma_star` and its exact
  break-even condition `g_p > max_i g_i`; the two-period rebalance identity; the
  `1 − (1 − f)**2` growth-retention curve; the exact `1/(2T)` cost of estimating the
  growth-optimal exposure; ERC's ordering and its two-asset collapse to inverse
  volatility.
- **`gamma_star` reproduces on real data to 0.09 bp/yr** on the portfolio, and its 68.27%
  win-probability floor does **not** survive real drift gaps — zero of 61 rolling 30-year
  windows.
- **Effective sample size is a measurable quantity and pooling correlated regions buys
  far less than it promises**: 1.49 effective regions of three for value, 1.33 for
  momentum, 2.26 for profitability. Resampling regions independently manufactures a
  significant result in at least one cell that the correct joint procedure cannot support.
- **Geometric growth must decide and the certainty equivalent must report beside it**
  ([decision 0008](../decisions/0008-growth-decides-crra-reports.md)). A cash control
  supplying nothing scored +0.809 pp/yr purely for de-risking. That was found by a control
  with a known answer, and controls-with-known-answers are now the pattern.
- **Benchmarks never aggregate.** A cheap index, the average investor and the reader's own
  counterfactual are three different claims, and `aggregate()` raises rather than summing
  them.
- **Exposure is measurable and alpha is not**, on every fund window available here.
- **The evidence base's resolution limits themselves** — see
  [evidence base](evidence-base.md) §1. Knowing what an instrument cannot see is a durable
  result.

---

## 5. Round two, ranked

Ordered by information per unit of cost. The first three need no acquisition.

### 1. Re-specify the portfolio-level test so that it can pass

**Free.** Directly answers the objection in §3 and repairs §1.1.

Freeze a new specification that: evaluates the growth surface across the whole weight
grid up to the 20% cap rather than reporting a 10% reference point; sets the materiality
threshold from the credit ceiling `sigma_p**2 w` rather than at a fixed 0.30 pp/yr, so the
bar is reachable by construction; and includes at least one genuinely low-beta asset.
**Pass condition:** any sleeve whose net-pessimistic marginal growth clears a
ceiling-derived bar with an interval excluding zero after Holm.

**Two amendments, both from the gold result of 2026-08-17.** *First, the "genuinely
low-beta asset" clause is now satisfied and has already been exercised* — gold lands at
`beta = +0.000` and fails anyway, so the successor gains nothing by adding it again as a
headline sleeve; it should be a **calibration row beside `cash_control`**, marking where a
real asset sits on the ceiling. *Second, the funding rule matters more than the leg, and this
is now measured rather than argued.* **The primary arm is the financed overlay, not the
named leg.** Re-running gold under overlay
funding **changes the sign of its marginal contribution, from −0.395 to +0.182 pp/yr**
against the leverage-matched control at the same reference weight — a swing of 0.58 pp/yr
from the funding rule alone, on a bar of 0.30. [Capital efficiency
§1](capital-efficiency-and-breadth.md) prices the gap at 5.17–6.69 pp/yr with nothing about
the sleeve in it, and §6a shows it is a property of the ticker. **Pro rata and named-leg
differ by which covariance enters; overlay versus pro rata differs by more than any premium
this repository has measured, and it decides signs.** Overlay primary, pro rata as the
robustness arm, named-leg as a diagnostic — **and every arm reported against a
leverage-matched control**, because that control is what rejects gold at the weight its
own wrapper runs even where the first-order bar accepts it.

Reopens: the closure in Experiment 010's consequence 1.

### 2. Run the construction tournament

**Free.** The only experiment that treats a portfolio as a joint object, and the only one
that speaks to the objection directly.

Compare drifting buy-and-hold, market weight, equal weight, inverse volatility,
sample-covariance constrained minimum variance, linear-shrinkage minimum variance and ERC
on the same shrunk covariance — identical point-in-time inputs, execution lag, costs and
rebalance dates, all choices inside chronological nested folds, primary metric net
geometric growth. Nonlinear shrinkage as the first challenger.

**Unblock it first.** Decision 0004 blocks step 6 because "there are no sleeves to
combine". A construction tournament compares weighting *methods* on the three regional
equity sleeves and the cash leg that already exist. That blocking rationale should be
amended.

### 3. Delivered capture, from holdings rather than sorts

**Free** — the data is already held and unused.

[Experiment 007](long-only-capture.md) measured the capture fraction from Ken French
sorted portfolios, found it a range rather than a number spanning 0.846 across five
defensible benchmarks, and has since shown it to be
[an HML loading rather than a multiplier](long-only-capture.md#the-correction-a-capture-fraction-is-a-loading-so-it-may-not-multiply-one).
**That lowers this item's priority without removing it.** A budget needs the loading,
which Experiments 002 and 013 already measure from returns; what holdings would add is the
first exposure figure here that does not come from a return regression, and therefore the
first that could contradict one. A fund's tilt is its holdings, not a sort. N-PORT carries
position-level holdings and no experiment has read them.

Pass condition: a holdings-derived HML exposure with an interval, for at least one
`exploratory` product on each of the US and developed-ex-US shelves, reported beside that
product's return-regression loading.

### 4. Buy breadth before buying depth — **and check whether it needs buying first**

**Mostly free, as it turned out.** This item asked for a documented total-return series for
bonds, gold, commodities and REITs. **Gold cost nothing**: the World Bank Pink Sheet has
published a documented monthly gold price under CC BY 4.0 back to 1960 the whole time, and
the LBMA benchmark it is built from is reachable as a cross-check. Landed and tested
2026-08-17. Commodities were already held via AQR CLR.

**The lesson is the same one [§3 of the evidence base](evidence-base.md) draws about
Goyal–Welch and Shiller, and it has now happened six times.** A source recorded as
absent was not absent. **Before pricing an acquisition, check whether the thing is
published** — and check the *reasoning* of any decision that appears to forbid it, because
decision 0002's two failure modes do not reach an asset that pays no distribution. **The
sixth instance raises the bar on that rule**: the bond leg was not merely published, it was
already in this repository's own cache and manifest directory. **Search the manifests before
searching the internet.**

**The bond leg landed on 2026-08-17 and it cost nothing at all**, which makes it the
sharpest instance of this item's own lesson. Goyal–Welch `ltr` and `corpr` — a hundred
years of measured long-Treasury and long-corporate total return — had been downloaded,
parsed, hashed and manifested in this repository since 2026-08-16 and read by one page for
one table, while every bond figure the programme published was computed from a modelled
`GS10` proxy. The two are not the same exposure: on the 750 months both cover they
correlate **+0.663**, and the proxy runs 3.4 pp/yr less volatile and 0.8 pp/yr lower in
excess return. TIPS and standalone credit landed the same day, TIPS modelled from the
Treasury's real curve back to 2003 and both measured on eighteen funds' filed returns from
2019. **One long-horizon non-US equity history was the other half of this item and it
landed on 2026-08-16.** This item is now closed; see
[alternative sleeves audit §8](alternative-sleeves-audit.md).

### 5. Test conditional allocation for the first time

Needs Goyal–Welch at its current URL and an inflation series. Valuation-conditioned
equity share, with a frozen rule and a falsifier, against the static constant mix.
Nothing conditional has ever been tried here, and the framework's own record of the
literature says regime models must use recursively estimated parameters and filtered
probabilities available on the decision date — which is a specification, not a warning.

### 6. The licensed fund-return source, last

**Money, the large kind.** Its required contents are in
[evidence base](evidence-base.md) §4 and should not be relaxed. Buy it after 1–3 have
narrowed what it is for: it purchases resolution on the alpha term, which is the term
every audit here has found unmeasurable, and it does nothing for the premium term, which
is now the whole of a factor line's uncertainty.

### Deliberately not in round two

- **Another public-data premium experiment on RMW or CMA.** Forbidden by decision 0005 and
  the floor is measured. Correct.
- **Reading the 2026-01-onward holdout.** Six to eight months against a 2.6 pp/yr floor
  spends a genuine holdout for nothing. Correct.
- **Obtaining the 2013–14 CRSP vintage.** It would remove the Phase 1 band, which is
  checked cell by cell and changes no conclusion anywhere.
- **Leverage and financing.** Still sizing an edge that does not exist.

---

## Consequence for this repository

1. **Two closures should be reopened as re-specifications rather than as new questions.**
   Experiment 010's portfolio-level closure is weight-dependent, and decision 0004's block
   on the construction tournament is circular. Both are recorded on their own pages.
   **The weight half is now measured rather than argued**: a real asset reaches the credit
   ceiling at the cap and still fails, so the re-specification should target the funding
   rule rather than the weight. §1.1 and §5.
2. **"No research-grade series is held" needs the same treatment as "closed".** It is a
   statement about what has been looked for, and it was wrong about gold for as long as it
   was written down. Any row in §2 blocked on an acquisition must name the source that was
   checked and the date, or it is an assumption wearing a constraint's clothes.
3. **The rejection counts must always travel with their clause, their frame and their
   comparator.** "24 of 44 rejected" is not a finding about the funds: 22 of those 24 fired
   on an in-sample fitted comparator, and the 44 were the products one quarterly filing
   happened to contain. On the corrected frame it is 48 of 109, and 24 of the 65 funds that
   frame adds — **and 35 to 49 depending on which cheap funds the comparator is built
   from**. §1.3.
   **A fitted comparator gets a placebo comparator beside it**, of the same width and with
   no added span, or the count cannot be attributed. That control has been run once, on the
   US shelf, and it moved more than the intervention it was controlling for.
4. **A null result from an underpowered instrument is not evidence of absence**, and the
   [resolution table](evidence-base.md#1-the-resolution-table--read-this-before-proposing-an-experiment)
   is how to check before committing.
5. **The programme's pessimism should be stated with its scope.** What has been shown is
   that a narrow set of gross academic factor spreads and a 72-month unaudited fund window
   cannot support a promotion. That is a long way from a statement about portfolios.
6. **A screen against a periodic filing states which periods that filing contains.** §1.4
   is the one design flaw on this page whose correction has been run, and it is the one
   that changed a published conclusion rather than a caveat. It was found by asking what
   was in the file, not by re-reading any result. **The cheapest audit in this repository
   is to ask, of any frame, what it physically cannot contain.**
