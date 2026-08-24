# Capital efficiency and accessible diversifiers

**Question.** How does the funding rule change the value of a diversifier, and which
economically distinct return sources can a retail investor currently access at plausible
cost?

**Current answer.** Funding is load-bearing. Selling the core to fund a sleeve and financing
an overlay are different portfolio constructions, and the difference can be larger than the
premium being studied. Trend is the best-supported accessible financed diversifier in the
current evidence; gold is easy to finance but has weaker expected-return evidence; several
other mechanisms appear distinct on paper but are inaccessible, expensive, short-lived, or
poorly measured. Among the stacked trend wrappers a retail investor can actually buy, neither
the funding rule nor the fee table separates the candidates — all three whose holdings are
filed keep the whole gap, and the one advertising a ten-to-one cost advantage has none once
its swap layer is counted — so age, size, survival, counterparty and tax placement decide. This is a finding about the
present vehicle and evidence shelf, not about the number of return engines in markets.

## Funding algebra

For a sleeve added by pro-rata sale of a base portfolio, the hurdle differs from a financed
overlay by:

```text
a_p - sigma_p²
```

where `a_p` is the base portfolio's arithmetic return and `sigma_p` its volatility. In the
100%-equity reference case previously tested, that gap was about **2.44 percentage points a
year**—larger than the effects most sleeve experiments attempted to resolve. The expression
contains no sleeve property. It explains why a pro-rata test can reject candidates that may
still improve a leverage-matched financed construction.

This does not mean financing is free. A wrapper retains only the part of the gap left after
financing, fee, collateral, rebalance, tax, and implementation costs. It also adds leverage,
liquidity, counterparty, path, and behavioral failure modes. Funding must therefore be part
of the hypothesis and comparator, not a default chosen for prudence or optimism.

## A wrapper's structure enters exactly once

Real wrappers are not a dichotomy between pro-rata sale and financed overlay. They are a
continuum, and one number places a fund on it. For a wrapper delivering `b` of base and `d` of
diversifier notional per dollar of capital,

```text
dg/dw at w=0  =  (a_net - rho sigma_p sigma_d) - delta (a_p - sigma_p**2),
delta = (1 - b) / d
```

so the wrapper's structure enters exactly once, as a multiplier on the gap above. `delta` is
the base sold per unit of diversifier notional obtained, and `1 - delta` is the share of the
funding-rule benefit the wrapper keeps. The identity is implemented and tested in
[`studies/wrapper_economics.py`](../../research/src/portfolio_edge/studies/wrapper_economics.py).

Two consequences bite on the real shelf.

- **Gross notional per dollar decides nothing.** A 50/50 equity-and-trend fund and a
  standalone trend fund both show 1.0x gross and both pay the gap in full; a 90/60 fund shows
  1.5x and pays a seventh of it. A wrapper at 40% equity and 30% trend has `delta = 2.0` and is
  worse than selling equity outright — a case the gross-notional figure cannot distinguish
  from the good one, and one with no name in the marketing vocabulary.
- **An expense ratio is quoted in the wrong units.** The hurdle is stated per unit of
  *notional*; a fee is charged on *capital*. The conversion is `fee / d`, so a wrapper charging
  20 bp for 0.10 of notional is dearer than one charging 100 bp for 1.00.

### Read the base leg from the whole filing, not from its largest line

The error this page has actually produced is not a bad model. It is reading one holding and
stopping. MATE's 2026-02-28 Form N-PORT shows an S&P 500 ETF at 49.8% of net assets, which is
squarely inside the range above where a wrapper is worse than selling equity; the same filing
shows a long E-mini S&P 500 future at 61.8%, which takes the base leg to 111.6% and `delta` to
-0.116. At 2026-05-31 the two lines read 50.30% and 65.57%, a base leg of 115.87% and
`delta = -0.159`. **A stacked fund's base leg is the sum of every instrument that delivers the
base, and on these products at least one of them is a future.**

**CTAP repeats the error and the fix.** Its 2026-03-31 filing shows an S&P 500 ETF at 70.41% of
net assets; reading that line alone gives `delta = +0.299`, deep in the range where a wrapper is
worse than selling equity. The same filing shows a long E-mini S&P 500 future at 32.23%, taking
the base leg to 102.64% and `delta` to **−0.027** — the tightest on the shelf. Two funds, two
quarters apart, same mistake available and the same instrument fixing it.

Two caveats travel with any such reading. The index future is **not separable** into base
completion and the trend book's own equity position, because both sleeves trade equity-index
futures and no filing tags a contract by sleeve; the contractual floor is the prospectus target,
and for MATE that is 100% and `delta = 0.00`. And gross notional on a volatility-targeted trend
book is an artefact of the risk target rather than an exposure: MATE's whole derivative book
ran 339% of net assets in February and 405% in May while its stated targets did not move.

### A leg that has not been filed is not a missing measurement

JPFP commenced operations on 2026-05-27 and has filed no Form N-PORT. Its series is S000101300
in the SEC's own ticker map, and that series appears in none of the 24 N-PORT filings its trust
made for the 2026-05-31 period. Its first holdings filing belongs to the quarter ending
2026-06-30 or 2026-07-31 and is due 2026-08-29 or 2026-09-29, so `delta` is not computable
before then. `not filed`, with a date attached, is the finding.

### A cheap fee on the wrong category is not a cheap wrapper

SDMF was reported to this repository as a stacked equity-plus-managed-futures wrapper at 0.35%.
Its 2026-03-31 Form N-PORT holds **no equity ETF, no equity index future and no equity of any
kind** — 89.5% of net assets in Treasury bills, 4.4% in a money fund, and four total return
swaps on DBi managed-futures indices. `b` is zero, so `delta = 1.000` and it keeps **none** of
the funding-rule gap: it is a standalone trend fund, arithmetically identical at the margin to
selling equity to buy DBMF. Its 0.35% is cheap for that category and irrelevant to this one.

This is the same trap in a new place. Gross notional cannot tell a good wrapper from a bad one,
and a headline fee cannot tell a wrapper from a trend fund. Only `b` and `d`, read off the
holdings, say which object is on the table.

### The fee table is the wrong instrument, in two different ways

**First, financing.** RSST files 0.00% of interest expense. MATE's unitary fee excludes interest
expenses and its Other Expenses line is 0.00%, estimated. JPFP's unitary fee excludes them
likewise. Futures financing is not an expense item: it sits inside the futures basis and is paid
out of the contract's return, so those zeros are accurate and uninformative. The one exception is
CTAP, whose diversifier is a swap rather than a futures book: every one of its swaps files its
financing leg as SOFR plus a spread of `0.00000000`, which makes it the only wrapper here whose
financing spread is stated at all.

**Second, and larger, the diversifier's own fee.** A total return swap pays the reference
fund's return **net of that fund's fees**, and `Acquired Fund Fees and Expenses` reaches direct
holdings rather than a swap reference. So when a wrapper buys its diversifier as a swap on
another fund, that fund's expense ratio is charged to the investor and appears **nowhere in the
wrapper's fee table**. CTAP is the worked case: 0.28% gross and 0.10% net after a waiver, with
95.17% of net assets in a swap on CTA — an affiliated fund charging 0.75% with no waiver — plus
3.71% of CTA held outright, which is the part the 0.03% AFFE line does reach. All-in for the
trend dollar is therefore about **0.81%/yr today and about 0.99% once the waiver lapses on
2026-12-04**, against RSST's 0.99% and MATE's 0.97%. **The two fact sheets report that near-tie
as a ten-to-one gap.**

The general rule: read what the diversifier leg *is* before reading what the wrapper charges. A
fee table prices the wrapper, not the exposure, and the gap between the two is a whole fund's
expense ratio when the leg is a swap on a fund. It also travels with three costs no fee table
carries — CTAP's trend exposure is bilateral counterparty exposure to Bank of America at 82.48%
of net assets and to Citibank at 12.70%, rather than to a clearing house; the reference fund is
affiliated and the prospectus concedes the conflict; and a swap is not a Section 1256 contract,
so the 60/40 treatment below does not reach 95% of its diversifier.

## Where a stacked wrapper belongs, and why it is not the taxable account

The deferral argument that makes a financed overlay attractive does not survive the filings.
Three mechanisms, all from primary sources, all annual, none optional.

- **Section 1256 marks the futures book to market every year.** Gain on regulated futures
  contracts is recognised at year end whether or not a contract is closed, and is 60% long-term
  and 40% short-term. MATE's registration statement states this plainly; RSST's 2026-04-27
  statutory prospectus does not contain the string `1256` at all, and JPFP's registration
  statement mentions it only inside the Section 988(a)(1)(B) currency election. **That is a
  disclosure difference, not an exposure difference** — the rule is statutory and reaches all
  three identically.
- **A Cayman subsidiary converts the commodity sleeve into ordinary income.** Each fund's
  subsidiary is a controlled foreign corporation, so the fund must include its subpart F income
  in gross income annually whether or not it is distributed; "it is expected that all of the
  Subsidiary's income will be 'subpart F income'"; and that income "is generally treated as
  ordinary income, regardless of the character of the Subsidiary's underlying income". The loss
  side is worse: a subsidiary net loss "is not generally available to offset the income earned
  by a Fund and such loss cannot be carried forward"
  ([J.P. Morgan ETF Trust SAI Part II, effective 2026-07-01](https://www.sec.gov/Archives/edgar/data/1485894/000119312526280973/d114090d497.htm),
  read 2026-08-22). RSST's prospectus states the same expectation of annual distribution.
- **A cash-creation ETF forfeits the in-kind shield.** JPFP "expects to generally effect its
  creations and redemptions entirely or partially in cash", so it "will be required to sell
  portfolio securities and subsequently recognize a gain" — on its equity leg as well as its
  overlay.

**The placement that follows is the pre-tax account, not the Roth and not the taxable one.** A
wrapper's tax cost is the conversion of return into currently recognised ordinary and
short-term income. A traditional account already converts every dollar it holds into ordinary
income on withdrawal, so that conversion costs nothing there. A Roth would spend the most
valuable shelter in the portfolio on the sleeve with the least established expected return. A
taxable account pays the cost in full, including phantom income in any year when the fund's
unrealised futures gain exceeds the cash it distributes.

**Two limits on that conclusion.** No SEC-standardised after-tax table exists for MATE or JPFP,
because neither has completed a calendar year, so the only measured distribution drag on a trend
wrapper here is RSST's, over a window that is entirely a rising equity market — the wrong window
for the year the sleeve exists for. And a 30%-of-portfolio wrapper consumes roughly nine tenths
of a one-third pre-tax account, which concentrates that account in a single product before any
return argument is made.

**What the wrapper actually delivers, as opposed to what it holds.** Everything above reads
positions off a filing. The complementary question — how much of the trend exposure reaches
the *return* — is answered from the same filings' Item B.5 total returns and lives in
[loading comparability and wrapper exposure](loading-comparability-and-wrapper-exposure.md):
RSST's trend loading is **+0.681 [+0.406, +0.955]** over 31 months to 2026-04, against an
equity beta of +0.979, with RSSB as a negative control at −0.101. A filed notional and a
measured loading are different quantities and this page owns only the first.

## Why levering equity is not the answer

Historical growth optimization of equity alone can select exposure no investor can survive.
In the tested long US sample, the unconstrained optimum was around 2.2× with an almost total
drawdown and decades under water. The useful conclusion is not that the estimate is the
right leverage; it is that feasible exposure is set by drawdown, liquidity, withdrawal, and
holdability constraints before an estimated growth optimum binds.

## Accessible return sources

Use “engine” to mean a distinct economic mechanism and failure mode, not a ticker or a low
full-sample correlation.

| Candidate | Current evidence | Access and main uncertainty |
| --- | --- | --- |
| Trend / managed futures | Most consistent positive marginal sign and low average equity relationship across vendor, independent, and live-fund layers | Financed retail wrappers exist; magnitude, crisis dependence, survivorship, method drift, financing, fee, and tax remain material |
| Gold | Diversified tested samples; weak or dominated return contribution at examined weights | Cheap direct and financed wrappers exist; expected return and crisis role are unstable |
| Bonds / Treasury overlay | Contractual yield and potential defensive role, with strong era dependence | Cheap access and financed wrappers exist; nominal duration, inflation exposure, leverage, and equity correlation can all dominate |
| Duration-hedged credit | Economically distinct credit-spread candidate | Retail implementation and long point-in-time evidence remain limited |
| Long/short commodities | Distinct futures mechanism in research data | Retail wrapper cost, construction, collateral, and capacity matter |
| Catastrophe risk | Distinct insured-event risk with attractive conceptual diversification | Retail history is short; fee, spread compression, tail dependence, and access prevent a confident allocation claim |
| Alternative risk premia | Several paper engines with low average correlation | The examined retail cost stack consumed much of the post-2019 gross return |
| Short-term reversal, BAB, accruals | Broaden paper opportunity set | No adequate registered implementation was established in the audited shelf |

“One engine” was too strong a phrase. The evidence supports a narrower statement: among the
financed retail vehicles examined, trend currently has the clearest multi-layer case. The
shelf can change and does not define market ontology.

**Counting engines is now a measurement rather than a judgement.**
[Stacking and effective breadth](stacking-and-effective-breadth.md) computes `1'R^-1 1` on
the excess returns themselves: five French factors across three regions plus trend are worth
**10.23 of 16**, one factor across three regions is worth **1.35 to 1.55 of 3**, and five
factors inside one region are worth **5.52 of 5**. Geography is nearly free breadth and style
is real breadth. That page also owns the probability arithmetic — what a stack of sleeves
each *n*% likely to win is jointly likely to do — which is a different question from the
growth arithmetic here and does not aggregate with it.

## What sets an overlay weight

No single historical optimum should decide. Size an overlay across a surface of:

- investor drawdown and tracking-error limits;
- account capacity, taxes, and withdrawal needs;
- financing cost and stress behavior;
- expected net sleeve return;
- average and crisis-conditional dependence;
- product closure, method change, and operational failure;
- regret if the expected return is overestimated.

The current missing contribution and withdrawal path can change feasible sizing more than a
small refinement to expected return. Until investor constraints and the joint portfolio test
exist, exact overlay weights are scenarios.

One measured boundary is available and is not a scenario. For a **financed** trend overlay on
a 65/25/10 global equity blend over 1990-07…2025-12, portfolio variance is minimised at
**21.6% of notional**, from `w* = −rho × sigma_equity / sigma_trend` and three measured
numbers — no premium, no benchmark and no forecast. Its sensitivity is the correlation's:
the 95% interval on `rho` of `[−0.277, −0.088]` puts `w*` between **10.3% and 32.8%**, so a
30% notional sits inside what the instrument supports but past the centre of it
([stacking and effective breadth](stacking-and-effective-breadth.md)). The credit is much
smaller than the pro-rata identity in [marginal sleeve value](marginal-sleeve-value.md)
suggests — about +0.03 pp/yr of growth rather than +0.22 at a 10% weight — because a
substitution sells the base and removes its variance while an overlay keeps the variance and
the return. That difference is the funding-rule gap seen from the variance side.

## Global versus US is a separate decision

Local-currency long-history and modern USD evidence can point in different directions. That
disagreement is not resolved by selecting the sample with the preferred answer. Currency,
valuation, tax credit, survivor composition, and investable vehicle all matter. Treat the
US/global split as a robustness and regret decision; do not bury it inside a diversifier
weight.

## Evidence and provenance

The funding identities and portfolio primitives are tested in `research/`. Experiment 011's
financed overlay result is recorded in
[`research/artifacts/1e504717fa664a0dabf1cceca5c0a7d6/summary.md`](../../research/artifacts/1e504717fa664a0dabf1cceca5c0a7d6/summary.md).
Product facts and primary filing links — including each wrapper's legs, `delta`, all-in cost,
filing date and read date — are canonical in `research/data-manifests/` and the typed client
shelf under `src/content/`; they should be rechecked before a transaction.

The earlier long tables, one-investor tax examples, and product-by-product narratives are
not repeated here. They remain in manifests, tests, client content, and Git history; the
current synthesis owns interpretation rather than duplicating those stores.

## Next informative tests

1. Run the portfolio-level tournament in the [research agenda](search-coverage.md) under
   explicit pro-rata and financed comparators.
2. Estimate crisis-conditional dependence and predeclare a monitoring boundary.
3. Build a point-in-time live-fund panel including closures and method changes.
4. Independently implement diversified trend from contract-level data.
5. Read JPFP's first Form N-PORT and compute its `delta`. It is the only candidate whose
   structure is still unknown and the one whose 59 bp would reorder the cost ranking; the
   filing date and what the answer would change are on its shelf entry's review trigger.
6. Revisit other mechanisms when a cheaper vehicle, longer live record, or better instrument
   changes the access or evidence constraint.

No candidate is promoted by this page. The conclusion is designed to be easy to update when
the investor, evidence, or retail shelf changes.
