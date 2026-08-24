# Research charter

## Aim

Build the best-supported implementable portfolio for a stated investor, while learning
where additional research is most likely to change the decision. “Optimal” is conditional:
it depends on objectives, taxes, liabilities, horizon, available accounts, implementation
costs, and the ability to remain invested.

The programme searches broadly. A weak first result is a reason to improve the question or
instrument, not to remove a strategy from consideration. Research conclusions are current
positions with scope and updating conditions, not permanent closures.

## Reference scenario

To make comparisons concrete, research may use a US investor with a long horizon, taxable
and tax-advantaged accounts, no near-term withdrawal need, and a cheap diversified passive
portfolio as the counterfactual. This is a versioned scenario, not a universal investor.
Results that depend on missing inputs—especially contribution rate, withdrawal path,
embedded gains, tax rates, account capacity, and tolerable drawdown or tracking error—must
show that dependency instead of silently selecting a value.

## Decision objective

For the reference scenario, the default objective is expected after-tax log terminal wealth
relative to an explicit benchmark, subject to liquidity, solvency, drawdown, and holdability
constraints. Log growth is a core diagnostic, not the only admissible objective. A study may
predeclare liability-relative wealth, expected utility, shortfall, or another decision-fit
objective and explain why it better represents the question.

Every allocation comparison should report enough of the outcome distribution to expose its
trade-off. The small common core is:

- after-cost, after-tax relative terminal wealth or growth;
- material downside, drawdown, or shortfall;
- benchmark-relative risk and the probability and magnitude of underperformance;
- implementation burden and failure modes relevant to the construction.

Additional metrics are selected from the threat model; they are not a universal checklist.

## Benchmarks and funding

“Beat the market” has no meaning until the comparator is named. A cheap broad-market
portfolio is the usual primary control. Add a risk-, beta-, leverage-, or liability-matched
comparator when the candidate changes that dimension. Market-neutral candidates compare
with cash plus a stated premium.

Three recurring questions use different benchmarks and their answers do not add:

1. Can a construction beat a cheap index?
2. Can it improve the investor's actual counterfactual?
3. Can it reduce mistakes relative to typical investor behavior?

The funding rule is part of the hypothesis. Selling the existing portfolio to fund a sleeve
and financing an overlay are different experiments; neither is the universally correct
frame.

## Evidence principles

- Separate market evidence, implementation evidence, and investor-specific inference.
- Label beta, leverage, and risk transfer honestly; do not rename them alpha.
- Treat low average correlation as incomplete evidence about crisis dependence.
- Count distinct return engines and failure modes, not ticker symbols.
- Preserve failed and ambiguous tests when they bear on the effective search history.
- Keep conclusions no broader than the source, window, instrument, and estimand tested.

## When a decision is ready

A portfolio decision is sufficient for now when the leading feasible alternatives have been
compared on decision-relevant outcomes, the uncertainties most capable of reversing the
choice are bounded or made explicit, implementation is understood well enough for the claim
being made, and the expected value of another research loop is lower than the cost of delay
or a planned review.

That is a review point, not the end of research. New data, products, investor inputs, or a
better design can reopen any empirical conclusion.
