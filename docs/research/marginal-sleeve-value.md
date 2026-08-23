# Marginal value of a sleeve

**Question.** What does a candidate add inside an existing portfolio, and how much of that
contribution is standalone return versus diversification?

**Current answer.** The answer is dominated by the funding rule and objective. Under
pro-rata funding, the diversification credit is arithmetically small at modest weights and
many tested effects are below the design's resolution. Under financed or leverage-matched
funding, the hurdle can be materially lower. The experiments establish useful signs and
decompositions, but not precise optimal sleeve weights.

## Identity

For a small pro-rata-funded sleeve weight `w`, write marginal growth as:

```text
w × (standalone return - funding cost) + w × sigma_p² × (1 - beta)
```

The second term is the diversification credit, where `sigma_p` is base-portfolio volatility
and `beta` is the sleeve beta to that portfolio. At `beta = 0`, the credit ceiling is
`w × sigma_p²`. A negative beta can exceed the zero-beta ceiling; that is not alpha, but a
more valuable covariance relationship.

For the tested reference portfolios, the zero-beta ceiling was about **0.217 pp/yr at a 10%
weight** for the global-equity core and **0.078 pp/yr** for the balanced 60/40 portfolio.
This makes a fixed 0.30 pp/yr hurdle unattainable for many otherwise useful diversifiers,
especially in the lower-volatility base. That hurdle is now a reporting sensitivity rather
than a universal decision rule.

## What Experiment 010 established

The frozen experiment decomposed factor, trend, gold, bond, credit, commodity, and other
sleeves inside two base portfolios. Its original branches and statuses remain in the ledger
and artifacts. The current interpretation is claim-scoped:

- the estimated sign is informative for several candidates;
- most effect sizes and differences are too small for the 420-month instrument to resolve;
- Holm correction was appropriate to the declared family but too demanding to turn an
  exploratory tournament into a useful ranking;
- a negative or unresolved pro-rata result does not answer the financed-overlay question;
- a point estimate is not a recommended weight.

Detailed run summaries:

- [`11d76e907a04474e844eee4ff80582fe`](../../research/artifacts/11d76e907a04474e844eee4ff80582fe/summary.md)
- [`7e5016a3d9a8487ea34fc67643bd471a`](../../research/artifacts/7e5016a3d9a8487ea34fc67643bd471a/summary.md)
- [`b27643d6d9124d9fa18beb1758515dc4`](../../research/artifacts/b27643d6d9124d9fa18beb1758515dc4/summary.md)

Experiment 010b separated geometric growth from a higher-risk-aversion certainty equivalent.
Across its tested sleeves, the average certainty-equivalent contribution was **+0.166
pp/yr**, geometric growth was **−0.643 pp/yr**, and the difference—de-risking rewarded by
that utility—was **+0.809 pp/yr**. Neither number is wrong; they answer different objectives.
For the reference charter, geometric growth is the default and the companion utility metric
reports the trade-off. Full result:

- [`cb564f2a4dc841feaa35cc13b0254878`](../../research/artifacts/cb564f2a4dc841feaa35cc13b0254878/summary.md)

## Trend as the clearest example

In the tested global-equity core, trend's beta was about **−0.132**. At a 10% weight, its
diversification credit was roughly **+0.246 pp/yr** and total marginal geometric contribution
about **+0.258 pp/yr**. Almost the whole point estimate therefore came from covariance, not a
standalone premium. In another tested construction at 15%, the point estimate was about
**+1.312 pp/yr** of marginal geometric growth against **+1.342** of certainty-equivalent
contribution, leaving only **+0.030** attributed to de-risking under that comparison.

These are not competing universal values for trend. They use different portfolios, weights,
funding, and controls. Quote the whole pairing or do not quote the number.

## What this changes

- Evaluate sleeves inside the portfolio, not solely by standalone Sharpe or return.
- Freeze funding and benchmark because they can decide the sign.
- Derive materiality from investor constraints and arithmetic rather than inherit a fixed
  threshold.
- Compare materiality with MDE before evaluation.
- Report growth and any alternate utility separately; do not let de-risking masquerade as
  expected return.
- Treat beta and crisis-conditional dependence as estimates with substantial uncertainty.

## Next test

Run a portfolio-level tournament with common investor scenarios, explicit pro-rata and
financed funding, achievable thresholds, risk/leverage-matched controls, and a predeclared
crisis-dependence analysis. The [research agenda](search-coverage.md) specifies the design
questions. No sleeve is promoted by the current decomposition.

## The sleeve table

The canonical full table is in the linked Experiment 010 artifacts; the current
interpretation is summarized in [what Experiment 010 established](#what-experiment-010-established).

## Gold, tested

Gold's current portfolio interpretation is summarized in
[alternative sleeves](alternative-sleeves-audit.md#2-candidate-map) and
[capital efficiency](capital-efficiency-and-breadth.md#accessible-return-sources).
