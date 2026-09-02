# Research agenda: where a better test can change the portfolio

**Question.** What should be researched next, given the current portfolio decision and the
limitations of the instruments already used?

**Answer.** Prioritize questions capable of changing the whole construction, not another
small isolated-premium estimate on the same underpowered data. The programme's null result
is partly a design finding: some thresholds exceeded arithmetic ceilings, some MDEs exceeded
the effect that mattered, a fitted comparator decided a product verdict, and an initial
fund census omitted much of the later shelf. Those observations justify better designs;
they do not imply that a candidate will succeed.

This is a ranked agenda, not a permission boundary. Cheap exploratory work can enter from
outside it when the mechanism and decision relevance are stated.

## 1. Compare portfolios as portfolios

Run a common construction tournament across feasible combinations of the core, bonds,
trend, gold, and other accessible diversifiers, with predeclared investor scenarios,
pro-rata, cash and financed funding rules compared rather than chosen, MDE computed before
freezing, risk- and leverage-matched controls, and expected-return assumptions kept apart
from diversification effects.

Run so far: the [construction tournament](construction-tournament.md) and
[final construction](final-construction-test.md) on the equity-plus-trend candidates
(Experiments 016–016f), and now a defensive arm,
[Experiment 018](defensive-engines-in-the-construction.md), which holds stacked Treasury,
gold and TIPS legs and three substitutions inside the leveraged construction on 96 years
against cheap, leverage-matched and volatility-matched controls. Every mean gap for a
defensive leg came back `unresolved` or `rejected`, as its freeze note predicted.

The September 2026 round added four registered experiments on the same machinery. The
bond-regime-conditioned stack ([Experiment 020](defensive-engines-in-the-construction.md))
did not resolve the Treasury leg: the correlation signal sorts months only inside the
1981–2020 bull market and picks the losing ones outside it, and its regret surface is 15 bp
wide. Cross-asset carry ([Experiment 019](carry-as-a-second-engine.md)) is the first second
engine that adds as a sum, at +0.58 pp/yr gross and +0.22 after cost and delivered loading
against a 0.35 floor, and is not added by default. Leveraged 200-day rules and the UPRO/TMF
mix ([Experiment 021](leveraged-etfs-and-timing-rules.md)) carry no resolvable timing
content. A financed gold-and-bitcoin stack ([audit](alternative-sleeves-audit.md) §3.1) is
worth exactly the funding-rule algebra.

What remains: a **TIPS series before 2003**, without which the leg the valuation argument
points at cannot be scored on a panel containing 1970–81; a **term-premium-conditioned
stack**, since the correlation rule cannot see carry and needs a point-in-time term-premium
series before 1990; a **costed cross-asset carry series** or a repository-built carry book on
public yields, to replace the 1–2 pp/yr haircut band; and whether dropping carry's
equity-index and currency legs, which hold its equity tail risk, leaves a usable engine.

## 2. Measure crisis-conditional dependence

Trend's allocation case depends more on its relationship with equity in bad states than on
its full-sample average, and so does every defensive leg's.

Measured so far: the tilt-plus-trend correlation matrix in the worst decile of equity
months and three other conditions ([stacking](stacking-and-effective-breadth.md) §6: the
three value tilts merge, IDMO–trend rises to +0.64, effective bets fall from 3.71 to
2.7–2.9, no sleeve's conditional mean is negative), and Experiment 018's episode tables
([defensive engines](defensive-engines-in-the-construction.md) §3), which score every arm
on eight frozen deflationary and inflationary episodes and read the bond-equity
correlation era by era.

What remains: a term-premium-conditioned test (item 1); **RSST's own tail
behaviour from its filings at its delivered loading**, because every conditional trend
figure so far is a vendor index or a fund-free construction, and the loading refresh due
at its 2026-07-31 N-PORT (filing deadline 2026-09-29); **JPFP's first N-PORT**, due by the
same date, before any wrapper comparison can include it; a state model rather than a
regime label, so that the conditional figures could be acted on; and the same measurement
for duration-hedged credit and any new candidate. Low average correlation is only an
admission signal.

## 3. Build a point-in-time live-product panel

Create a dated, union-census panel with net fund returns, closures, mergers, strategy or
benchmark changes, fees, assets, and availability. Include dead funds and preserve the
selection rule before looking at returns.

Why it matters: current live managed-futures and factor-product conclusions are constrained
by short public filing histories, survivorship, changing shelves, and method drift. This
work tests implementation rather than relying on a vendor index or today's survivors.

## 4. Independently construct diversified trend

Acquire contract-level futures histories with point-in-time roll, collateral, and
availability conventions. Implement a frozen diversified trend rule across more than four
markets and compare it with vendor series and live funds.

Why it matters: current sources agree on a useful sign more than a reliable magnitude. An
independent construction separates the strategy mechanism from vendor reconstruction and
product replication.

## 5. Improve exposure delivery research

For factors and other premia, focus on questions the data can resolve:

- holdings-based delivered exposure and turnover;
- cheap replication bases expressive enough for the product;
- tracking difference, lending, fee waivers, and tax structure;
- loading stability and capacity;
- alpha intervals reported as unresolved when the panel cannot distinguish them.

More regressions on the same short return window have low information value unless the
estimand or instrument changes. The instrument did change once: Experiment 023 scored the
tilt complex on AQR's 1972-onward stock-selection factors, giving the 1981–1990 window the
French-basis result never had. What remains there is a size factor before 1990, which no
free ex-US source supplies, and the emerging leg before 1990, which none supplies at all.

## 6. Resolve global versus US exposure as a robustness decision

Compare global and US cores under currency, valuation, tax-credit, product, and historical
survivor uncertainty. Frame the result as regret across plausible futures rather than an
expected-return winner that history cannot reliably identify.

Run on 2026-09-02 as an exploratory grid ([valuation](valuation-and-the-allocation.md) §5.7):
minimax regret sits at 50/50, expected regret at the grid floor because a 1.4 pp dividend-yield
gap is a sign bet, and the log-wealth criterion moves 85 points of split per pp of expected
differential, so tracking error is what constrains the answer. 60/40 by contributions stands
as the first stop. What remains is the investor's tracking-error tolerance, and an anchor for
relative CAPE that is buyback- and sector-adjusted.

## 7. Parameterize the investor

The recommendation should update from contribution and withdrawal paths, embedded gains,
account capacity, tax rates, human capital, liabilities, and tolerable drawdown/tracking
error. Sensitivity analysis on these inputs may change the portfolio more than another
strategy experiment.

Done so far: the drawdown ladder is published on the site, the contribution flow by account
is worked through in [part A](portfolio-for-one-investor.md) §3.8, and the holdability band
is re-run at the corrected premium with a contribution stream
([trend weight](trend-weight-under-uncertainty.md) §4). The one input that still moves the
most points of the vector is the investor's tolerable drawdown, which nobody has supplied:
at −60% or tighter the wrapper falls to 23.7% or below under the programme's own rule.
Human capital and job correlation with the equity sleeve remain unexamined.

## 8. Broaden discovery before closing families

The [September 2026 sweep](discovery-sweep-2026-09.md) screened the 2025–26 launches from
issuer pages and Form N-PORT: cross-asset carry was the one new financed engine and has
since been measured; intangible-adjusted value (ITAN) is scored in
[untested tilt candidates](untested-tilt-candidates.md); box spreads price the financing
alternative to a 99 bp wrapper; bank quant baskets, defensive equity and bitcoin income
products are closed on their live records. Continue inexpensive screens of catastrophe risk,
duration-hedged credit, long/short commodities, defensive option structures, and other
economically distinct mechanisms.
Classify access, payoff shape, plausible net return, shared failure modes, and the instrument
needed for evaluation. A missing retail vehicle is an implementation finding, not proof that
the return source is absent.

## Designs not worth repeating unchanged

- A null test whose MDE exceeds the decision-relevant effect.
- A sleeve hurdle above the construction's arithmetic ceiling.
- A product comparison against a basis that cannot express the admitted exposure.
- A current-shelf backtest presented as point-in-time selection evidence.
- A vendor-series evaluation presented as independent strategy replication.
- A factor loading multiplied by a long-only capture fraction.

These are scoped lessons about instruments. Change the source, estimand, comparator,
funding rule, or claim and the research question is open again.

## How the agenda changes

Re-rank when new investor inputs arrive, a source contract changes, a product opens or
closes, monitoring crosses a predeclared boundary, or an experiment materially changes the
portfolio decision. Retire a question when the expected value of a better answer is below
the cost of delay or the next planned review—not because an old document used the word
“closed.”
