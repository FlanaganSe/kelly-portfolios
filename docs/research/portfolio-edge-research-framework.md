# Portfolio-edge research framework

**Question.** What evidence would justify changing a cheap, diversified portfolio for a
stated investor?

**Current answer.** The repository has found useful implementation and tax decisions, but
has not established a near-certain strategy edge over a cheap index. That is not a closed
worldview. Several nulls came from instruments unable to resolve the relevant effect,
incomplete product frames, fitted comparators, or a funding rule that imposed a larger
hurdle than the sleeve could arithmetically clear. The next round should improve portfolio
designs and instruments, not repeat the same isolated screens.

The working portfolio is therefore a hypothesis: low-cost diversified beta, an equity share
chosen from investor constraints, disciplined placement and trading, and optional modest
diversifiers or tilts only where their specific uncertainty and tracking error are acceptable.
See the [recommendation](portfolio-recommendation.md) for the current construction and
[search coverage](search-coverage.md) for the agenda.

## The unit of research is a claim

Statuses attach to a claim made by a particular instrument:

- **Observed:** arithmetic, a filing, or a directly measured implementation fact.
- **Suggestive:** the sign or mechanism is informative, but design, power, independence, or
  investability limits the conclusion.
- **Unresolved:** the instrument cannot distinguish decision-relevant alternatives.
- **Contradicted:** evidence weighs against the predeclared claim on the tested scope.

The experiment ledger retains its more granular machine statuses. Translation is explicit:
a `rejected` loading clause can contradict a product-exposure claim without contradicting a
strategy; an `exploratory` factor result can be suggestive without supporting allocation.
“Works” is not a useful status.

## Four separations that prevent false conclusions

### Benchmark

Name the counterfactual before estimating edge. A cheap index, the investor's actual
alternative, and typical investor behavior answer different questions and do not aggregate.
Add risk-, beta-, leverage-, or liability-matched controls when the candidate changes those
dimensions.

### Funding

A sleeve funded by selling the existing portfolio faces a different hurdle from a financed
overlay. Pro-rata funding, cash funding, leverage matching, and capital-efficient wrappers
are distinct hypotheses. Report the funding rule beside every marginal contribution.

### Evidence layer

Keep strategy evidence, product delivery, and portfolio contribution separate:

1. Does a return mechanism appear in research data?
2. Does an implementable product deliver it after cost and tax?
3. Does adding it improve this investor's portfolio under the stated funding rule?

Passing one layer does not pass the next. A long-short premium is not a fund return. A fund
loading and a long-only capture fraction are two measurements of the same exposure and must
not be multiplied.

### Time and availability

Separate full-sample explanation from point-in-time decision evidence. Revised factor files,
surviving funds, fitted models, and modern product shelves can answer useful questions, but
not what an investor could have selected contemporaneously unless availability is modelled.

## Research protocol

The protocol scales with the claim.

### Explore

Use inexpensive work to learn whether the mechanism, data, approximate magnitude, cost, and
failure modes justify a stronger test. Record source provenance, the searched family, and
hypothesis-bearing choices. Exploration may use imperfect but honestly labelled sources. It
does not support promotion or shipped performance claims.

### Evaluate

Before inspecting the deciding result, freeze:

- the claim and decision it informs;
- benchmark and funding rule;
- sample and availability policy;
- primary outcome and materiality rationale;
- cost/tax treatment appropriate to the claim;
- inference and search family;
- hostile tests selected from the actual threat model.

Power is part of design. Compare materiality with MDE and with any arithmetic ceiling. If
the instrument cannot resolve the decision, redesign it or accept `unresolved`; do not turn
low power into evidence of absence.

Relevant hostile tests may include alternate windows and eras, realistic costs, omitted or
dead products, placebo or cheap replication, beta/risk/leverage matching, crisis dependence,
method drift, look-ahead, concentration, financing, tax, and operational failure. Not every
test belongs in every experiment; state applicability.

### Promote

A promoted or published allocation claim needs more than a successful backtest. Add the
strongest feasible evidence for independence and forward validity—independent replication,
walk-forward evaluation, a live implementation panel, or shadow-live monitoring—and show
that the vehicle, liquidity, tax, financing, and behavioral burden fit the reference
investor. Promotion is a decision made from the evidence, not an experiment status.

## What the current evidence changes

- **Implementation dominates confidence.** Cheap funds, appropriate account placement,
  lot discipline, and avoiding unnecessary realization can improve an investor's own
  counterfactual, but the value is conditional on their actual holdings and accounts.
- **Equity share dominates expected outcome but is not identified by history alone.** The
  feasible share depends on withdrawals, human capital, drawdown tolerance, and persistence.
- **Factor research does not travel directly to products.** Post-publication decay, regional
  dependence, delivered loading, turnover, and comparator choice are load-bearing.
- **Trend is the strongest current diversifier candidate, not a proved allocation.** Vendor
  data, independent constructions, and live funds agree more on direction and correlation
  than magnitude. Crisis dependence, product survival, method changes, financing, and tax
  can reverse the case.
- **Rebalancing controls exposure.** Its return contribution changes sign with the drift gap
  and should not be booked as a stable bonus.
- **The accessible shelf is not the opportunity set.** Several mechanisms lack affordable
  retail vehicles; absence from the current portfolio can be an access finding rather than
  a market conclusion.

## Assumptions and open questions

The largest unresolved investor input is the contribution and withdrawal path, followed by
embedded gains, account capacity, tax rates, and the drawdown or tracking error the investor
can actually hold. Without them, precise weights are scenarios rather than conclusions.

The largest unresolved research questions are:

1. Which feasible combination of equity, bonds, trend, gold, and other accessible
   diversifiers is robust across explicit funding and drawdown constraints?
2. Does trend's equity dependence remain favorable in the crises that matter, after product
   closure and method drift?
3. How different is the live-fund conclusion in a point-in-time panel that includes dead
   funds and net returns?
4. Can a contract-level independent trend construction reproduce the mechanism beyond a
   vendor series?
5. Which investor inputs materially change the working portfolio?

These questions rank work; they do not forbid other exploration.

## The ledger, counted rather than described

Run counts, specification counts, and statuses are generated from `research/ledger.jsonl`:

```sh
cd research && uv run python -m portfolio_edge.reporting.programme_status
```

The distinct-specification count is an upper bound on statistically independent trials
because specifications share data, eras, universes, and design choices. The ledger makes a
later dependence estimate possible; it does not solve that problem.

## Consequence for this repository

Detailed run tables live in `research/artifacts/*/summary.md`. Topical syntheses should state
the few decisive findings, scope, and next informative test, then link the artifact. New
research begins in the exploratory lane unless it is intended to support a stronger claim;
old empirical conclusions do not require permission to revisit.

## The design map

The current design map is the claim/evidence/funding structure above; live experiment counts
and statuses come from the generated programme report.
