# Current portfolio position

**Question.** Which portfolios can a reader reasonably choose now, what trade-offs do they
make, and what evidence could change the choice?

**Status: working decision, as of 2026-09-05.** The site publishes four conditional choices.
Their exact holdings live in [`src/content/portfolios.ts`](../../src/content/portfolios.ts);
fund facts and dated sources live in [`src/content/shelf.ts`](../../src/content/shelf.ts).
No strategy is promoted as a dependable way to beat the market. That does not prevent a
reviewable choice under stated assumptions.

## Current answer

Choose the amount of stock-market risk before choosing extra strategies. Money needed for
spending soon, a fragile income stream, or an inability to remain invested through losses
can change the whole allocation. The site does not assume an income, account split, tax
bracket, existing portfolio or withdrawal schedule.

| Published choice | Construction | Why choose it | Main trade-off |
| --- | --- | --- | --- |
| **One fund** | VT, the global stock market | The site's default for the equity allocation: broad ownership and little maintenance | It remains an all-stock portfolio and can suffer a deep, prolonged loss |
| **Value lean** | US and international stock funds, with value and momentum tilts | A reader wants those exposures and accepts long periods behind a broad index | Extra funds and tracking error; neither the chosen funds nor the tilt sizes are established as best |
| **Plus trend** | The stock allocation with 25% RSST and 5% SCHP | A reader wants trend exposure alongside stocks and accepts the wrapper's leverage, cost and uncertainty | Trend can disappoint for years and does not guarantee protection in a fast crash |
| **Cautious** | 50% SCHP, 15% RSST and 35% other stock funds | A reader wants less stock exposure and accepts the resulting growth trade-off | Bonds have interest-rate risk; the name and historical loss figures are not a loss limit |

These are alternatives, not steps every investor should climb. One fund is the simpler
equity default, not a claim that everyone should hold only stocks. Cautious is the
published lower-stock example, not proof that its defensive assets or its trend holding
are optimal. The retired 63%-SCHP construction remains supporting data, not a fifth
published portfolio.

Earlier experiments also used a seven-fund portfolio with **30% RSST and no SCHP**, or a
70%-US-core/30%-trend-wrapper proxy. Those are research comparators; they are not the
current published Plus trend portfolio. The [construction evidence](final-construction-test.md)
identifies which weights, return sources and execution rules each result actually scored.

A new investor can choose a conditional portfolio without waiting for an elusive precise
ranking. An existing investor must also compare the benefit of changing with the tax,
trading and maintenance costs of leaving their current holdings. The reference investor
in [the worked example](portfolio-for-one-investor.md) is one scenario, not this page's
assumption about the reader.

## What is relatively dependable

Lower costs help when the exposures and services being purchased are comparable. Account
placement and tax-lot decisions depend on the investor's actual circumstances. Cash flows
and rebalancing can control exposure; a stable return bonus from rebalancing is not booked.
See [implementation and taxes](structural-and-tax-edges.md) and
[rebalancing](rebalancing-policy.md).

The funding rule is part of every investment comparison. Buying a strategy by selling
stocks gives up those stocks' return. Financing it retains the stocks and adds financing,
fees and leverage. Both can improve a portfolio: a lower-return replacement can improve
compounded growth or reduce a relevant risk. An arithmetic mean that is a weighted average
does not rule out those benefits. [Stacking and dependence](stacking-and-effective-breadth.md)
and [funded portfolio tests](final-construction-test.md#current-published-portfolios-funded-fund-substitutions)
keep these questions separate.

Use both a cheap broad-market comparator and the investor's unchanged portfolio. Add a
risk- or leverage-matched control when the candidate changes those exposures. A favourable
result against one does not answer the others, and their gains cannot be added. Confidence
intervals and detection floors describe uncertainty in a measurement; they are not rules
requiring investors to wait until every useful effect becomes statistically distinguishable.

## Optional factor tilts

Value and momentum have research support, but a long/short factor return is not the return
of a fund a reader can buy. Product exposure, costs, turnover, tax treatment and the holding
being sold determine what reaches the portfolio. The [factor evidence](factor-persistence.md)
and [fund comparison](untested-tilt-candidates.md) separate these layers.

VTV remains in the published examples; its presence does not establish that it is the best
value fund. AVUV adds a different size exposure. SPMO changes momentum exposure. Their
combinations have been tested as complete funded portfolios, including the VTI or VTV sold
to buy them. The [current comparisons](final-construction-test.md#current-published-portfolios-funded-fund-substitutions)
separate assumptions about future premiums from actual filed fund returns. They support
reconsideration, not a reliable forward ranking from a short recent window.

International ownership spreads exposure across countries, currencies and market outcomes.
Regional value funds can nevertheless share much of the same active risk. Correlation
between their tilts is not a finding that geography cannot diversify a stock portfolio.
Choose the regional split with its costs, concentration and benchmark-relative discomfort
in view; see [global allocation and valuation](valuation-and-the-allocation.md).

## Optional financed trend

Trend remains the leading diversifier candidate in this programme. Its case combines
historical strategy returns, the repository's own constructions and live-product evidence.
Those sources agree more on the relationship with stocks than on the return a particular
fund will deliver. [Trend research](trend-marginal-value.md),
[live funds](live-managed-futures.md) and [wrapper delivery](loading-comparability-and-wrapper-exposure.md)
state the differences.

The published 25% RSST holding is a working construction choice, not an estimated optimum.
More trend can help under a positive future premium and disappoint under a weak one;
leverage and sustained underperformance may make it harder to hold. The
[weight-under-uncertainty analysis](trend-weight-under-uncertainty.md) presents that trade.
[Funding trend from bonds](trend-from-the-bond-line.md) changes the return forgone, but its
simulated wrapper paths do not establish actual RSBT or standalone-fund delivery.

A second trend fund need not be a second independent premium to be useful. Differences in
markets, signals, execution and operational exposure could diversify implementation risk.
That requires an actual portfolio comparison after costs; it is neither established nor
excluded by calling both holdings trend.

## Bonds, gold, and other alternatives

The defensive allocation has to serve its purpose inside the whole portfolio. SCHP is a
TIPS fund with interest-rate risk, not a promise to return the initial investment on the
reader's spending date. A short-duration fund, cash reserve or maturity-matched bonds may
fit a different purpose. The long historical tests often substitute nominal Treasuries
for TIPS; their inflation episodes cannot establish SCHP's behaviour. See
[cautious constructions](cautious-constructions.md) and
[setting the equity share](setting-the-equity-share.md).

Gold, commodities, duration-hedged credit, catastrophe risk and crypto remain candidates
with different mechanisms and implementation problems. A weak standalone return or a
shared crash exposure does not by itself settle their role at a funded portfolio weight.
The [alternatives audit](alternative-sleeves-audit.md) records the available measurements;
its product findings and rejection labels apply to the instruments and designs tested.

[Selective carry](carry-as-a-second-engine.md#8-does-removing-stock-and-currency-carry-solve-the-tail-problem)
illustrates the distinction: removing stock and currency carry improved some long-window
funded outcomes, but equity-tail dependence returned in the recent window. Costs, unstable
risk scaling and unknown retail delivery prevent treating the selective blend as a winner.
A new carry or defensive holding is not added to the published portfolios by this review.

Likewise, the tested [equity timing rules](timing-rules-on-the-equity-sleeve.md) and
[leveraged versions](leveraged-etfs-and-timing-rules.md) do not establish a dependable
improvement after their funding and trading costs. They do not prohibit a different
executable risk-control rule. A new test should compare whole-portfolio growth and downside
with a simpler static allocation at comparable risk.

## Operating the portfolio

Choose one set of **capital weights** across the actual accounts. Derive the stock, bond
and other exposures inside wrappers separately; a wrapper's purchase weight is not its
underlying market exposure.

Direct contributions and withdrawals toward the desired allocation where practical, then
review on a calendar and when circumstances change. The [operating study](rebalancing-policy.md)
compares bands, costs and account constraints. Its result for a particular account split
is not an instruction to sell appreciated holdings in every investor's taxable account.

Keep enough flexibility to restore the targets. When a taxable holding already exceeds its
whole-portfolio target, trades only in sheltered accounts cannot reduce it; contributions,
a revised target or a taxable sale may be needed. Account capacity, gains and tax rates
belong in that decision. [Placement](structural-and-tax-edges.md) and
[harvesting](harvesting-and-direct-indexing.md) explain the conditional benefits rather
than assigning the same tax savings to every reader.

## What this construction will feel like

The published portfolios can lose money and lag a familiar benchmark for years. Their
illustrations use simulated history, including periods before the named ETFs existed.
The website's historical worst fall is an observation on that simulation, not a forecast
or a maximum possible loss.

Three historical examples underpin the site's figures. The earlier US value comparison
ran **54.3% behind over 17.7 years**; international stocks ran **69.0% behind US stocks over
18.2 years**. Those comparisons were recorded as of 2026-08-23. US stocks returned
**−2.55% a year from March 1999 through February 2009**; the earlier 30%-trend-overlay
illustration, under its prior-median return assumption, brought that period to about
**+0.05% a year**, recorded as of 2026-09-02.
These are specific sleeve and overlay illustrations, not results for today's four printed
portfolios. The [rebalancing and relative-loss study](rebalancing-policy.md) and
[trend analysis](trend-weight-under-uncertainty.md) retain the methods and limitations.

The practical choice is how much stock loss, interest-rate risk, leverage and time behind
a benchmark the reader can carry. There is no measured portfolio here that combines the
highest return, the smallest loss and the strongest confidence in every plausible future.

## What would change the position

Investor inputs can change the choice immediately: spending and withdrawal needs, income
risk, liabilities, tolerable losses, liquidity, account access, embedded gains and willingness
to track a portfolio with several funds. No new premium estimate is required to act on them.

The [research agenda](search-coverage.md) prioritises evidence that could change the whole
construction. High-value questions include actual trend-wrapper delivery and alternative
funding, the composition and duration of a large defensive allocation, and joint outcomes
under weaker premiums and adverse correlations. Better sources, changed fund mandates,
fees, tax treatment or liquidity can reopen a prior conclusion. Statistical significance
on the same short history is not the only evidence capable of changing a choice.

## Review policy

Review the working choices when those conditions change and at a scheduled portfolio
review. Poor performance deserves examination of exposure, implementation and the mechanism;
it is neither automatic proof of failure nor a reason to ignore new evidence indefinitely.
A liquidation or mandate change requires a concrete replacement decision using the actual
holdings and accounts, not a fallback vector copied from an earlier portfolio.

Maintain a conditional choice while research continues. A further experiment earns priority
when it can change the allocation, reveal a material implementation problem or bound an
important risk. Repeating an inconclusive fund ranking without changing the question or
source should not delay that choice.
