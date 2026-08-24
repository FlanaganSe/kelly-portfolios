# Independent engines: how many exist outside this repository's own data, and what the stack is worth

**Question.** [Stacking and effective breadth](stacking-and-effective-breadth.md) measures
an average pairwise correlation of 0.435 on this portfolio's own active positions, caps an
unlimited stack of 55% bets at 57.6%, and ends on an instruction: lower the correlation
rather than raise the count. That instruction leaves two questions open, and both of them
are the reader's next question. **What is genuinely uncorrelated and buyable, and what is
the whole exercise worth when it is done well?** This page answers both from evidence
outside this repository, so that the answer does not rest on one portfolio's 422 months.

**Decision it informs.** Whether the ceiling measured here is a property of this
portfolio's ingredients or a property of the available ingredients generally; what an
honest headline number for a completed stack should be; and which of the mechanisms on the
shelf are exposed to capacity decay. Out of scope: whether to hold any of them
([decision 0004](../decisions/0004-no-sleeve-promoted.md)), the funding arithmetic
([capital efficiency](capital-efficiency-and-breadth.md)), and the screen of individual
mechanisms ([alternative engines](alternative-sleeves-audit.md)).

**Status: `source-reproduced`.** `as of 2026-08-24`. Every figure is read from a manager's
published research, a fund's own standardised performance table, an SEC filing, Ken
French's data library or FRED. The only arithmetic performed here is the breadth
calculation in section 1, which is Grinold's identity applied to a stated correlation, and
subtracting two numbers a source printed side by side. **Nothing here is a repository
measurement, nothing here is a backtest, and two of the four headline numbers are
forecasts rather than records.** Section [What is thin](#what-is-thin) says which.

## Conclusion

1. **The thesis, as a number, is weak.** A 55% win rate against a cheap index is an
   information ratio of about **0.126**. Twenty genuinely independent bets at that ratio,
   with no fees and no shared behaviour, still lose to the index **29 times in a hundred**
   over one year. At an average correlation of **0.2**, modest by the standard of anything
   actually purchasable, twenty bets are worth **4.2** and the one-year odds fall to 60%.
   This reproduces the repository's own ceiling from a completely different direction.
2. **The best-built live implementation delivered about a quarter of its theoretical
   forecast.** AQR's multi-strategy alternative fund runs four styles across five asset
   groups at roughly 1,205% gross exposure per 100% of capital. Its beta to the S&P 500
   since inception is **−0.01**, so the independence is genuine and this is a fair test of
   the idea. Sharpe since inception, October 2013 to June 2026, is **0.46** against a
   stated theoretical forecast for such a composite **above 2**. Return **7.57%/yr**
   against the S&P 500's roughly **13.5%/yr** over the same stretch.
3. **About four or five genuinely distinct sources exist for a US retail investor, not
   twenty.** On AQR's own March 2026 capital market assumptions, only three of ten asset
   classes carry a meaningfully positive appraisal ratio against a global stock and bond
   portfolio: commodities 0.24, absolute-return hedge funds 0.29, trend following 0.26.
   Six of the ten correlate **0.68 to 0.93** with equities. In the same firm's
   decomposition of a typical eight-asset institutional portfolio, **equity alone
   contributes 81% of total risk** and equity plus credit over 90%.
4. **The honest prize is about 1.5 to 2.0 percentage points a year.** AQR's own numbers for
   a well-built diversified portfolio give an expected return of **6.5% to 8.1%** at a
   Sharpe of **0.26 to 0.35**. Real money against the portfolio a normal investor would
   otherwise hold. Not a claim to beat the index.
5. **The largest free gain available is structural and nobody markets it.** ETF in-kind
   redemption raised long-term investors' after-tax returns by **1.05%/yr** relative to
   equivalent mutual funds. Zero cost, no minimum, no lock-in, and the same order of
   magnitude as the entire direct-indexing tax case.
6. **Capacity decay is the recurring mechanism and it is measurable.** Merger arbitrage
   spreads down more than 400 bp since 2002. Commodity roll return **+1.95%/yr (1970-2004)
   against −9.29%/yr (2004-2015)** as index money arrived. Catastrophe bond spreads 11.31%
   to 5.53% while dedicated capital grew 31%. Published factors decayed **26% to 58%**
   after publication.

## 1. The thesis converted into a number

Grinold's identity says the information ratio of a combination rises with the square root
of the number of independent bets. Inverting a 55% one-year win rate against a cheap index
gives a per-bet information ratio of about 0.126. The one-year odds of finishing ahead
follow directly.

| Independent bets | Chance of beating the index in a year |
| ---: | ---: |
| 1 | 55% |
| 5 | 61% |
| 10 | 65% |
| 20 | 71% |

**Twenty is not a lot.** Twenty independent bets, no fees, no shared behaviour, is a
71% chance of finishing ahead over one year, which is a 29% chance of not. The
frictionless best case for a portfolio nobody can build still loses to the index almost
three years in ten.

Introduce a modest amount of shared behaviour and the count collapses. At an average
pairwise correlation of 0.2 the effective count of twenty holdings is **4.2**, and the
one-year odds fall to **60%**. This repository measured 0.435 on its own active positions
and got a hard ceiling of 57.6%; an outside reading of 0.2, which is more generous than
anything measured here, lands in the same neighbourhood.

## 2. The live composite, and the size of the haircut

AQR's multi-strategy alternative fund is the literal implementation of the stacking thesis.
Dozens of individual premiums, four styles, five asset groups, market-neutral by
construction, built by the authors of the theory with institutional execution and
institutional financing. It is the strongest available test of what the idea delivers when
nothing is done badly.

| Reading | Value | Window |
| --- | ---: | --- |
| Beta to the S&P 500 | −0.01 | Since inception |
| Sharpe, since inception | 0.46 | 2013-10 to 2026-06 |
| Stated theoretical forecast for such a composite | above 2 | Forecast, not a record |
| Return | 7.57%/yr | Since inception |
| S&P 500 over the same stretch | ~13.5%/yr | Since inception |

Two readings, and both matter.

**The independence is real.** A beta of −0.01 to the index over twelve and a half years is
what genuine independence looks like, and it is the part of the thesis that survives. This
is not a stock fund wearing a costume.

**The delivered result is roughly a quarter of the forecast.** A four-fold haircut between
the stacking mathematics and the record, absorbed by fees, financing, implementation
shortfall, and holdings that turned out less independent than modelled. Every one of those
four is larger for a retail investor than for this fund.

**The return comparison against the S&P 500 is the wrong comparison and is reported
anyway.** A market-neutral composite is an addition to an equity portfolio, not a
substitute for one, and the funding arithmetic in
[capital efficiency](capital-efficiency-and-breadth.md) is exactly the reason: sold-to-fund,
its edge competes with equity's and the average can never exceed its largest member;
financed, the edges add. The 7.57% against 13.5% is reported because a reader will find it
and should meet it here first, with its interpretation attached. What it does establish is
that a market-neutral stack of dozens of premiums, run by the people who invented the
approach, lost decisively to the index as a standalone holding over its whole life.

## 3. How many independent engines exist

AQR's March 2026 capital market assumptions publish appraisal ratios against a global
stock and bond portfolio, which is the right question: what does each asset class add once
the equity exposure inside it has been removed.

| Asset class | Appraisal ratio against global stocks and bonds |
| --- | ---: |
| Absolute-return hedge funds | 0.29 |
| Trend following | 0.26 |
| Commodities | 0.24 |
| Private equity | 0.06 |
| Real estate | −0.03 |
| High yield credit | −0.06 |

**Three positive, one at noise, two negative.** Six of the ten asset classes in the same
publication correlate **0.68 to 0.93** with equities, which is the arithmetic behind the
firm's own term for the illusion, "pie chart diversification".

The decomposition makes the point sharper than the correlation table does. In a typical
eight-asset institutional portfolio, the kind held up as the diversified benchmark,
**equity alone contributes 81% of total risk** and equity plus credit contributes over
90%. Eight line items, one and a fraction of a bet.

This corroborates [the engines audit](alternative-sleeves-audit.md) from outside. That page
counted, on this repository's own screen, six reachable engines for a US retail investor:
broad equity, an equity style lean, government bonds, duration-hedged credit, managed
futures and catastrophe risk. An independent review of a manager's published forward
assumptions gets three to four with a positive expected edge. The two counts are close, and
neither is twenty.

## 4. The size of the prize

On AQR's own numbers, a well-built diversified portfolio has an expected return of **6.5%
to 8.1%** at a Sharpe of **0.26 to 0.35**. Against the portfolio a normal investor would
otherwise hold, the improvement is **about 1.5 to 2.0 percentage points a year**.

That is the honest headline for the whole exercise. It is real money and it compounds. It
is also a forecast built on a manager's assumed capital market expectations rather than a
measured record, published by a firm that sells the products it is forecasting, and it
sits well inside the resolution of any test a retail investor could run on their own
account. The claim it does not support is that a stack will beat the index.

## 5. The structural gain nobody markets

ETF in-kind redemption raised long-term investors' after-tax returns by **1.05% a year**
relative to equivalent mutual funds (Moussawi, Shen and Velthuis, *Review of Financial
Studies*, 2025). Zero cost, no minimum, no lock-in, no forecast, and available to anybody
with a brokerage account and a taxable holding.

**That is the same order of magnitude as the entire direct-indexing tax case**, which
[harvesting and direct indexing](harvesting-and-direct-indexing.md) prices at roughly zero
net of its own fee. One is sold hard, at 25 to 40 bp a year plus paperwork. The other is
free and is marketed by nobody, because nobody is paid when an investor does it. This is
the same shape as the repository's own largest reliable line, which is
[structural and tax edges](structural-and-tax-edges.md): the money that is nearly certain
comes out of contracts and tax law rather than out of a forecast.

## 6. Capacity decay as the recurring mechanism

Five independent instances of one mechanism.

| Premium | Before | After | What changed |
| --- | ---: | ---: | --- |
| Merger arbitrage spreads | — | down >400 bp | Since 2002 |
| Commodity roll return | +1.95%/yr, 1970-2004 | −9.29%/yr, 2004-2015 | Index money arrived |
| Catastrophe bond spreads | 11.31% | 5.53% | Dedicated capital grew 31% |
| Published equity factors | — | decayed 26% to 58% | After publication |
| A currency carry ETF | +0.51%/yr over 16 years | liquidated | Nobody stayed |

**The generalisation this supports is narrow and useful.** A premium whose supply of risk
is fixed and whose demand can be scaled by an index product decays as capital arrives. That
is a testable property of a mechanism rather than a mood about markets, and it is a
standing reason to be most suspicious of whatever is being marketed hardest. In 2026 that
is return stacking and options income, which is also what
[live stacked fund records](live-stacked-fund-records.md) finds trailing its own printed
benchmarks.

## 7. What this corroborates

The strongest thing on this page is not any single number. It is that two evidence bases
with nothing in common reached the same three conclusions.

| This repository, from its own data | This page, from outside evidence |
| --- | --- |
| Average pairwise correlation 0.435 on 422 months; unlimited stack of 55% bets caps at 57.6% | Twenty independent bets reach 71%; at ρ = 0.2 they are worth 4.2 and reach 60% |
| Eight tickers are worth about 3.71 separate bets; six reachable engines on the screen | Three of ten asset classes carry a positive appraisal ratio; equity is 81% of an eight-asset portfolio's risk |
| The funding rule is worth more than any premium measured: about 2.44 pp/yr | A market-neutral stack delivered 0.46 Sharpe against a forecast above 2, and lost to the index as a standalone holding |
| The largest reliable line is contractual, not forecast | The largest free gain available is a fund structure, at 1.05%/yr after tax |

Neither route is strong on its own. The repository's correlation is one portfolio's
measurement over one window. The outside evidence is one manager's forecasts plus one
fund's record. **Agreement between two weak instruments that share no data is worth more
than either**, and it is the closest thing to independent confirmation this project has.

## What is thin

Carried forward from the source review rather than dropped.

1. **Two of the four headline numbers are forecasts.** The appraisal ratios in section 3
   and the 1.5 to 2.0 pp prize in section 4 are capital market assumptions, which are a
   manager's forward view rather than a measured record. They are also published by a firm
   that sells products in the categories being forecast. The direction of that conflict
   points *against* the conclusion here, which is mild reassurance and not a control.
2. **The composite in section 2 is one fund over one window.** Twelve and a half years, one
   manager, one implementation. It is the best available test and it is still n = 1. A
   different decade would produce a different Sharpe, and the 0.46 should be read as
   evidence about the size of the haircut rather than as an estimate of the strategy's
   mean.
3. **The comparison in section 2 against the S&P 500 puts a financed holding beside an
   unfinanced index** and is reported for that reason with its interpretation attached. It answers "what did this
   pay a standalone holder", not "was the second dollar worth buying".
4. **The capacity table mixes windows and instruments.** Five instances of one mechanism,
   each read from its own source over its own period, assembled here rather than measured
   together. It supports the mechanism. It does not support a rate of decay.
5. **Nothing on this page was reproduced from primary series.** Every number is a source's
   own published figure, re-read on 2026-08-24. Standardised performance updates on the
   manager's schedule; re-read before quoting.

## What would change this page

- **A market-neutral multi-premium fund reaching a ten-year Sharpe above 1.** That would
  move the haircut in section 2 from four-fold to something the theory can carry, and would
  reopen the size of the prize in section 4.
- **A published appraisal ratio above 0.2 for an asset class this project currently counts
  as duplicated.** The count in section 3 is the binding constraint on everything else, and
  it moves on ingredients rather than on arithmetic.
- **A capital market assumptions release from a manager with no product in the category.**
  The conflict in section 4 is the weakest joint in the argument and a second, disinterested
  source would close it.
- **Evidence that the ETF after-tax advantage narrows.** The 1.05%/yr rests on a tax
  treatment of in-kind redemption that is a policy choice rather than a law of nature, and
  has been raised in more than one legislative proposal.
- **A capacity instance running the other way**, meaning a premium whose spread widened as
  dedicated capital grew. None was found. One would materially weaken section 6.
