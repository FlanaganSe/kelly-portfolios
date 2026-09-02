# Documentation

This is a reading map, not a second source of research facts. Detailed experiment output
lives in committed run artifacts; each synthesis links its evidence.

## What should I believe now?

Start with the [research framework](research/portfolio-edge-research-framework.md) for the
short current position and evidence model, then read the
[portfolio recommendation](research/portfolio-recommendation.md) as a provisional decision
for the stated reference investor. The [edge decomposition](research/expected-edge-decomposition.md)
keeps three different benchmarks from being mixed.

For the major decisions:

- [Equity share](research/setting-the-equity-share.md): what arithmetic can say and which
  investor constraints decide the rest.
- [Valuation and the allocation](research/valuation-and-the-allocation.md): what an August
  2026 CAPE of 41 licenses — a wider drawdown assumption, not a timing rule — and why the
  US/international spread is a differently identified question from the US level.
  [Decision 0012](decisions/0012-valuation-enters-through-the-drawdown-assumption.md)
  records why the CAPE enters the construction as a wider drawdown assumption and a
  conditional TIPS rule rather than a forecast, and why no bond stack was added.
- [Current regime and pricing](research/current-regime-and-pricing.md): which of the
  portfolio's engines are cheap and which are expensive *today*, each level beside its own
  historical percentile — and which conditioning variables have ever predicted anything.
  Credit is at the tightest quality spread since 1990 and is the one engine whose entry
  price has an out-of-sample record; long real yields are at the top of theirs; nothing
  tested predicts equity returns out of sample.
- [Currency and the international sleeve](research/currency-and-the-international-sleeve.md):
  whether the unhedged foreign-currency position inside the 35% international allocation is
  compensated — the mean is unresolvable, the variance reduction is not, and the account it
  would have to live in is decided by tax rather than by the measurement.
- [Structural and tax edges](research/structural-and-tax-edges.md): implementation gains
  that are conditional on accounts, taxes, holdings, and behavior.
- [Harvesting and direct indexing](research/harvesting-and-direct-indexing.md): what
  tax-loss harvesting is actually worth once §1211(b)'s $3,000 cap decides how much of the
  loss can ever be deducted, why a step-up and a liquidation give answers 14 bp apart, and
  why the free route — harvesting between two similar funds — beats a 9 bp direct-indexed
  account below about 2.5% of the account a year in realised gains.
- [Factors](research/factor-persistence.md), [delivered loading](research/long-only-capture.md),
  and [products](research/factor-products.md): the evidence chain from research premium to
  investable exposure.
- [Loading comparability and wrapper exposure](research/loading-comparability-and-wrapper-exposure.md):
  why two published loadings usually cannot be ranked against each other — every one was
  fitted on the months its own fund had filed — what the US value and managed-futures
  shelves look like refitted on matched windows, and the first measurement of a stacked
  wrapper's delivered trend exposure, taken from the fund's own SEC filings rather than
  from a price feed.
- [Tilts the recommendation never priced](research/untested-tilt-candidates.md): AVDV,
  AVUV, MTUM, QVAL and ITAN scored against the portfolio actually held rather than against each
  other — why the negative delivered return found for large-cap international value turns
  out to be a property of the measurement window rather than of capitalisation, why a
  116%-turnover momentum fund is nonetheless more tax-efficient than a total-market index
  fund, and what each candidate is worth as a plain change in yearly portfolio return.
- [Trend and managed futures](research/trend-marginal-value.md) and
  [live-fund evidence](research/live-managed-futures.md): the strongest current diversifier
  candidate and its unresolved implementation risks.
- [Timing rules on the equity sleeve](research/timing-rules-on-the-equity-sleeve.md): the
  same signal applied to the base portfolio instead — a different funding rule, a different
  tax outcome, and largely the same bet as a trend overlay.
- [Rebalancing](research/rebalancing-policy.md): useful exposure control, with no stable
  return bonus established — and the operating half, covering the capital-versus-notional
  unit trap, the exact condition under which a portfolio target can be restored without
  selling in a taxable account, the recommended policy, and how many lines to hold.
- [Other diversifiers](research/alternative-sleeves-audit.md) and
  [capital efficiency](research/capital-efficiency-and-breadth.md): candidate mechanisms,
  access, financing, and failure modes — including the cross-engine stress table, the
  verdicts on crypto and tail hedging, and why duration-hedged credit is a separate engine
  when unhedged credit is not.
- [Leverage and the notional budget](research/leverage-and-the-notional-budget.md): what
  gross and net exposure a 30% stacked-fund line actually carries, what the growth objective
  wants across the premium surface, what the embedded financing costs, and why the binding
  constraint is holdability rather than drawdown — with the tracking-error route re-run at
  the corrected premium, which moved the band from 15–25% to 20–30%.
- [Stacking and effective breadth](research/stacking-and-effective-breadth.md): what a
  pile of sleeves is worth once their excess returns are correlated, how many
  independent bets the proposed portfolio is actually making, and — under
  [Experiment 017](../research/experiments/exp_017_longonly_ladder.yaml) — how many
  candidates a long-only optimiser holds out of a shelf of twelve, why it stops at three,
  and why that count depends on the dispersion of the candidates' edges as much as on
  their correlation.
- [How many independent engines exist](research/how-many-independent-engines.md): the same
  ceiling reached from evidence this repository did not produce — a manager's published
  capital market assumptions, one market-neutral multi-premium fund's whole live record,
  and five instances of capacity decay. It answers what `stacking and effective breadth`
  leaves open, namely which engines are genuinely distinct and what a completed stack is
  worth, and it is the page to read for the size of the haircut between the stacking
  mathematics and anything delivered.
- [Live stacked fund records](research/live-stacked-fund-records.md): what the retail
  return-stacking shelf has actually paid its investors, read from issuer-published
  standardised returns rather than from a backtest — six of seven Return Stacked funds
  behind the benchmark their own issuer prints, the trailing year in which trend reversed
  that, the roughly 70 basis points the idea's leading advocate forecasts for it, NTSX as
  the version of the idea that worked. It is also the page that says why none of these
  issuer comparisons is matched on borrowing, and what each of them can therefore answer.
- [The construction tournament](research/construction-tournament.md): twenty-five whole
  portfolios scored against three benchmarks — which differences this data can resolve,
  which it cannot, and how many years an investor would have to hold each one before
  finding out.
- [The final construction, tested](research/final-construction-test.md): the recommended
  portfolio put through the same tournament as a single object rather than sleeve by sleeve —
  what it is worth against a leverage-matched cheap index and against the three constructions
  it was chosen over, why only one of those comparisons is resolvable and why that one is
  measuring leverage, what every fund on the tilt shelf actually costs once Form N-CEN's
  securities-lending income is netted off the fee, and why RPV and SPMO are both rejected.
- [Defensive engines inside the construction](research/defensive-engines-in-the-construction.md):
  the first experiment to hold a stacked Treasury, gold or TIPS leg, or a cash or
  long-Treasury substitution, *inside* the leveraged construction rather than beside an
  unlevered base — the 96-year bracket on the trend overlay whose top clears its floor and
  whose bottom does not, why the bond stack's whole contribution is the 1981–2020 bull
  market and what it is worth at today's term premium, the one defensive trade the design
  can resolve, what an RSSB or NTSX leg would actually be, and the conditional TIPS rule
  that follows. [Experiment 020](../research/experiments/exp_020_conditional_treasury_stack.yaml)
  adds the regime-conditioned stack the agenda asked for: switched on by trailing
  bond–equity correlation, it sorts months only inside the 1981–2020 bull market and picks
  the losing ones outside it.
- [The trend weight under acknowledged ignorance](research/trend-weight-under-uncertainty.md):
  the tournament's number-one next test — the forward trend premium as a weighted range on one
  stated basis, the regret surface over weight and premium against two benchmarks that give
  opposite answers, why a minimax rule relocates the prior rather than removing it, the two
  arms of the asymmetry that decide the size, and why a contribution stream does not carry
  the position through a drought.
- [Adversarial review](research/adversarial-review.md): a red team on the August 2026
  session — which of its conclusions survive their own detection floors, where a forward
  premium was compared on the wrong basis, and what the resolvable edge is worth against
  a savings rate.
- [Carry as a second financed engine](research/carry-as-a-second-engine.md): the first
  candidate measured that is nearly uncorrelated with the trend overlay (+0.06 on a
  century), stacked inside the construction under
  [Experiment 019](../research/experiments/exp_019_carry_engine.yaml) — the sum rule holds
  to the fourth decimal, the gross vendor series clears its floor at full loading and
  falls back inside it once a trading-cost haircut and a delivered loading are charged,
  substitution for trend fails, and the one live fund is 27 months old and behind. Not
  added; sized for an investor who wants it anyway.
- [Leveraged ETFs and the 200-day rule](research/leveraged-etfs-and-timing-rules.md):
  Gayed's 2x and 3x rule and the UPRO/TMF mix on a century of daily data under
  [Experiment 021](../research/experiments/exp_021_leveraged_etf_rules.yaml) — the timing
  content is unresolved at every leverage and negative since 1990, everything else is
  beta, the protection covers slow bear markets and not October 1987, and the rule's
  deepest drawdown is a run of whipsaws in 1933–35. None belongs in any third.
- [Discovery sweep, September 2026](research/discovery-sweep-2026-09.md): what exists
  that the audit and the market scan never screened, read from issuer pages and Form
  N-PORT — cross-asset carry as the one new financed engine, intangible-adjusted value
  as the one equity idea outside the held value funds, box spreads as an observable
  financing rate, and what the live records of bank quant baskets, defensive equity and
  bitcoin income products have already settled.

## What should we research next?

Read [search coverage](research/search-coverage.md). It is the ranked agenda, not a
permission boundary. Check the [evidence base](research/evidence-base.md) before designing
the next test: it records source fitness, resolution, and limitations. A current instrument
that cannot resolve the effect is a reason to acquire or design a better one, not to stop
asking the question.

The highest-value open work is portfolio-level rather than another isolated sleeve screen:
compare feasible diversifiers under a common set of investor constraints and explicit
funding rules; measure crisis-conditional dependence; improve point-in-time live-fund
coverage including dead funds; and parameterize the recommendation by investor inputs.

## How do I reproduce a result?

Follow the synthesis link to its `research/artifacts/*/summary.md`, then to the frozen YAML
specification, manifests, and implementation. The [research workspace README](../research/README.md)
contains commands and integrity requirements. Experiment counts and statuses are generated:

```sh
cd research && uv run python -m portfolio_edge.reporting.programme_status
```

## Governance and method

- [Charter](charter.md): objective, reference scenario, benchmarks, and decision sufficiency.
- [Documentation protocol](AGENTS.md): canonical homes and tiered evidence standards.
- [Numerical engine](research/portfolio-engine-specification.md): mathematical architecture.
- [Decision records](decisions/README.md): current and historical choices, with
  supersession made explicit.
- [Deploying](deploying.md): how the site is built and published, and the exact Route 53
  records the apex needs.

## Complete file map

Topical pages not already named above: [Fama–French reproduction](research/fama-french-reproduction.md),
[marginal sleeve value](research/marginal-sleeve-value.md),
[expected-edge decomposition](research/expected-edge-decomposition.md), and the
[numerical engine](research/portfolio-engine-specification.md).

Two pages written for the public site and kept because the site cites them by path:
[market scan 2026](research/market-scan-2026.md), an outside-in check on what has changed
in the real world and what the audited shelf would now get wrong, and
[the portfolio for one investor](research/portfolio-for-one-investor.md), the derivation
behind `/portfolio/`. Both are scoped to one reader and one read date, and neither
supersedes the pages above.

Decision records: [0001](decisions/0001-contained-python-research-workspace.md),
[0002](decisions/0002-no-research-grade-free-price-source.md),
[0003](decisions/0003-cheap-broad-market-control.md),
[0004](decisions/0004-no-sleeve-promoted.md),
[0005](decisions/0005-factor-premia-closed-on-public-data.md),
[0006](decisions/0006-reference-portfolio-without-promotion.md),
[0007](decisions/0007-application-may-render-research.md),
[0008](decisions/0008-growth-decides-crra-reports.md),
[0009](decisions/0009-blocks-lifted-and-closures-rescoped.md),
[0010](decisions/0010-bars-carry-a-reopening-condition.md),
[0011](decisions/0011-the-site-publishes-answers-not-notes.md), and
[0012](decisions/0012-valuation-enters-through-the-drawdown-assumption.md).
