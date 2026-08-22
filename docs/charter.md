# Charter

What this programme is trying to do, for whom, and against what. Everything else in
`docs/` answers a question this page poses. It carries no results; the pages it points
to do.

Until 2026-08-22 this material lived only in `docs/the-plan.md`, an orchestration prompt
that was correctly untracked and is now deleted — while five research pages and nine
files in `research/` cited it. Those citations pointed at nothing on a fresh clone.

## The question

Find, falsify, and construct the best implementable portfolio for after-fee, after-tax
geometric outperformance of a cheap market benchmark. The target is not "a good
diversified portfolio", and a cap-weighted portfolio is a legitimate **benchmark** and a
legitimate **answer** — but not an unexplained one.

The order of work: identify distinct return engines; find which survive implementation;
measure their shared exposures; combine them so *effective breadth* rises rather than the
ticker count; test whether leverage, capital-efficient wrappers, concentration or
manager selection improve expected terminal wealth; produce exact portfolios; and say how
each could fail.

## The reference investor

One stated investor, so that "it depends" has a default. Every figure sized against these
is labelled with them, and a different investor must restate rather than rescale.

| Input | Value |
| --- | --- |
| Age, horizon | ~28, multi-decade |
| Invested | ~$400k — ~$160k taxable (with embedded gain), ~$120k IRA/Roth, ~$120k 401(k) |
| Income | ~$180k employment |
| Domicile | California — 9.3% at no preferential capital-gain rate |
| Federal rates | 24% ordinary, 15% qualified, no §1411 |
| Risk | High willingness to accept tracking error |
| Near-term | Possible coast-FI or lower-stress work in ~5 years |

Two constraints this creates. Existing holdings carry embedded gains and are not freely
liquidatable, so **capital that can be moved without realising a gain** is a binding
input — see [capital efficiency §7.3](research/capital-efficiency-and-breadth.md). And the
five-year transition is a sequence-risk constraint, not a reason to hold a target-date
fund; model the tension rather than resolving it by convention.

**The contribution rate is `not found`, and it is the single input that most decides the
overlay weight.** Supplying it is worth more than any further experiment on the current
data.

## Benchmarks

"Beating the market" is underspecified without one. The primary is a cheap US
total-market total return; the secondary set is the S&P 500, a global cap-weighted
equity index, a globally diversified passive portfolio, and — whenever a candidate
changes risk — a **volatility-matched and a leverage-matched** version of the primary.
Market-neutral candidates are measured against cash plus a stated premium.

A candidate that beats the primary by carrying more equity beta is **leveraged beta, not
alpha**, and must be labelled that way. [Decision 0003](decisions/0003-cheap-broad-market-control.md)
makes the control and its comparators mandatory.

Three benchmarks recur and **never aggregate**: a cheap index, the reader's own
counterfactual, and the average investor. Summing across them is the error this
repository has actually made
([edge decomposition](research/expected-edge-decomposition.md)).

## Objective

**Maximise expected after-tax log terminal wealth relative to the benchmark.** Geometric
growth decides; a certainty equivalent reports beside it and never alone
([decision 0008](decisions/0008-growth-decides-crra-reports.md)). Sharpe is never
substituted for terminal wealth, and a win rate is never maximised without its payoff
asymmetry.

Report alongside: geometric excess return; median and 25th/10th/5th-percentile relative
terminal wealth; probability of outperformance at 5, 10 and 20 years; expected magnitude
of out- and under-performance; maximum drawdown and drawdown relative to the benchmark;
expected shortfall; time under water; tracking error and information ratio; exposure to
equity beta and to each shared engine; probability of a leverage, liquidity or
behavioural failure; tax drag; and operational burden.

## Standing cautions

Most of the original anti-goal list has become a trap in [`AGENTS.md`](../AGENTS.md), a
rule in [`research/README.md`](../research/README.md), or a decision record. What has no
other home:

- **Do not exclude a strategy because initial confidence is low.** Register it and
  classify it. Researching a strategy is not allocating to it.
- **Do not start from tickers.** Start from return engines, evidence and risk exposures.
- **Do not assume low average correlation means low crisis correlation**, or that a
  diversifier must beat the benchmark standalone to improve compounding.
- **Do not count two funds as diversification when they share a failure mode.** Credit
  beside Treasuries and TIPS beside nominals are the two measured instances.
- **Do not erase failed experiments.** The ledger records abandoned and failed runs
  because the trial count cannot be reconstructed afterwards.

## Stopping conditions

Not met, and none is close. Completion requires: every major strategy family carries a
recorded status; the strongest candidates have been red-teamed; product details are
verified from primary sources; strategy, index and live-fund evidence are kept separate;
costs and taxes are modelled or bounded; candidates are compared against risk-matched
simple benchmarks; alpha estimates are haircut severely; stress correlations and leverage
risk are modelled; results reproduce; no unresolved data gap could reverse the leading
decision; the recommendation explains both why it may work and why it may fail; and the
marginal value of another research loop is low against the remaining uncertainty.

[Search coverage](research/search-coverage.md) audits the first of those and holds the
ranked agenda for the next round.
