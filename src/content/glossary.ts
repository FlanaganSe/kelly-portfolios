import type { Citation } from "~/content/types";

/**
 * The terms the app's prose uses. Written for someone smart who is not a quant.
 * `short` is one sentence and stays under twenty words, so it can sit in a tooltip.
 */

export interface GlossaryEntry {
  readonly term: string;
  readonly short: string;
  readonly long: string;
  readonly whyYouCare: string;
  readonly source?: Citation;
}

const capture: Citation = { label: "The long-only capture fraction", docPath: "docs/research/long-only-capture.md" };
const decomposition: Citation = {
  label: "Where outperformance can come from",
  docPath: "docs/research/expected-edge-decomposition.md",
};
const structural: Citation = {
  label: "Structural and tax-aware edges",
  docPath: "docs/research/structural-and-tax-edges.md",
};
const persistence: Citation = { label: "Factor persistence and decay", docPath: "docs/research/factor-persistence.md" };
const productAudit: Citation = {
  label: "Investable factor products",
  docPath: "docs/research/factor-product-audit.md",
};
const framework: Citation = {
  label: "Portfolio edge research framework",
  docPath: "docs/research/portfolio-edge-research-framework.md",
};

export const glossary: readonly GlossaryEntry[] = [
  {
    term: "Tracking error",
    short: "How far your returns wander from the thing you are measuring yourself against.",
    long: "It is the standard deviation of the difference between your return and the benchmark's, per year. A small edge against a small tracking error is near-certain quickly; the same edge against a large one may never be provable. Time to any confidence level scales with the square of tracking error divided by edge.",
    whyYouCare:
      "It decides whether an edge is demonstrable within a lifetime, and it matters more than the size of the edge.",
    source: decomposition,
  },
  {
    term: "Certainty equivalent",
    short: "The guaranteed return you would swap a risky one for.",
    long: "A risky portfolio and a certain return are equivalent to you when you would genuinely accept either. The gap between a portfolio's average return and its certainty equivalent is the price you put on its risk, and it depends on a risk preference somebody has to declare. Two experiments here declared a CRRA coefficient of 3 for their own comparison.",
    whyYouCare: "It is how a sleeve's value gets compared once its risk is counted, rather than only its return.",
    source: { label: "Rebalancing policy on real regional equity", docPath: "docs/research/rebalancing-policy.md" },
  },
  {
    term: "Geometric vs arithmetic return",
    short: "What you actually compounded, against the simple average of the yearly numbers.",
    long: "Lose 50% then gain 50% and the arithmetic average is zero while you are down 25%. The geometric return is the one your wealth actually followed. The gap widens with volatility, which is why a volatile strategy's advertised average return overstates what a holder received.",
    whyYouCare: "Only the geometric number buys anything. The arithmetic one flatters volatile strategies.",
    source: decomposition,
  },
  {
    term: "Factor loading",
    short: "How much of a factor's behaviour a fund actually delivers.",
    long: "Regress a fund's returns on a factor and the coefficient is its loading. A loading of 0.41 on value means the fund moves 0.41 units for each unit the value factor moves. It measures manufacturing, not returns: a fund can deliver its exposure perfectly and still be a poor thing to own.",
    whyYouCare:
      "A product that does not deliver the exposure it advertises cannot deliver the premium behind it, whatever the premium turns out to be.",
    source: productAudit,
  },
  {
    term: "Capture fraction",
    short: "The share of a long-short premium that a long-only holder actually receives.",
    long: "Academic factors are long-short spreads with zero net investment that no retail investor can hold. A long-only tilt gets some fraction of the spread, and against a size-neutral benchmark that fraction is about one half — for a structural reason, since the long leg is one half of a symmetric spread. Against the market it reads far higher, and the difference is a size premium wearing another name.",
    whyYouCare:
      "It has no single value. Five defensible benchmarks span 0.846, and the choice decides the sign of a value tilt.",
    source: capture,
  },
  {
    term: "Deflated Sharpe ratio",
    short: "A Sharpe ratio marked down for how many strategies were tried before this one.",
    long: "Search enough variations and one will look good by chance. Deflation adjusts a Sharpe ratio for the number of trials, the length of the sample and the non-normality of the returns. The number of trials it needs is the number of distinct specifications searched, which is why the experiment ledger records every attempt including the failures.",
    whyYouCare:
      "A backtest quoted without its search count is not evidence. Here the count starts at twelve distinct specifications, not twenty-three runs.",
    source: framework,
  },
  {
    term: "Block bootstrap",
    short: "Resampling in chunks, so the resamples keep the clustering the real data has.",
    long: "Ordinary resampling shuffles observations one at a time, which destroys the way market returns cluster and produces intervals that are far too tight. A block bootstrap draws contiguous stretches instead. When several correlated series are pooled, the block indices have to be drawn once and applied to all of them at the same time.",
    whyYouCare:
      "Getting this wrong manufactures results. Resampling three regions independently once turned an interval containing zero into one that excluded it.",
    source: persistence,
  },
  {
    term: "HAC standard errors",
    short: "Error bars that survive returns being autocorrelated and unevenly volatile.",
    long: "HAC stands for heteroskedasticity and autocorrelation consistent — Newey-West is the common version. Ordinary standard errors assume each month is independent and equally noisy, and monthly returns are neither. HAC widens the errors accordingly, typically by 7% to 18% on the series here.",
    whyYouCare: "The gap between the plain and the HAC error is the size of an assumption that is known to be false.",
    source: { label: "Fama-French factor reproduction", docPath: "docs/research/fama-french-reproduction.md" },
  },
  {
    term: "Purged walk-forward",
    short: "Testing on data the rule has never seen, with the overlapping bits cut out.",
    long: "Fit on an early window, test on the next one, roll forward, and never let information from the test period leak backwards. Purging removes observations whose outcomes overlap the boundary, and embargoing leaves a gap after it. A final holdout stays untouched, because looking at it once turns it into training data.",
    whyYouCare: "It is the stage between a backtest and a claim. Nothing in this repository has reached it.",
    source: framework,
  },
  {
    term: "Multiple testing and the Holm correction",
    short: "Adjusting for the fact that testing twenty things guarantees one looks significant.",
    long: "Test twenty independent true nulls at 5% and you expect one false positive. Benjamini-Hochberg controls the share of discoveries that are false and assumes the tests are independent; Holm-Bonferroni controls the chance of any false positive and stays valid under arbitrary dependence. The tests in this record are heavily dependent — nested specifications, shared factors, shared months — so Holm is the defensible one and the BH count is an optimistic bound.",
    whyYouCare:
      "The gap is enormous. In one audit, 54 of 132 tests survived BH and 5 survived Holm, and those five were three products.",
    source: productAudit,
  },
  {
    term: "Minimum detectable effect",
    short: "The smallest true effect a window could have found, if one were there.",
    long: "It answers a different question from a p-value. A p-value asks whether a result could be zero; the minimum detectable effect asks whether the window could have found something worth having. When a measured premium is smaller than its own detection threshold, an interval that excludes zero is not evidence the window can carry.",
    whyYouCare:
      "It is what closed two factors here permanently. The best pooled threshold in public factor data is 2.62 pp/yr, above this repository's own 2.0 materiality bar.",
    source: {
      label: "0005 — Profitability and investment premia are closed on public data",
      docPath: "docs/decisions/0005-factor-premia-closed-on-public-data.md",
    },
  },
  {
    term: "Effective sample size",
    short: "How many independent looks a set of correlated series is actually worth.",
    long: "Three regions of one factor are not three independent tests, because they share global risk factors, construction and accounting definitions. The effective count is measured from the realised sample rather than assumed: three regions of value were worth 1.49, and three of momentum only 1.33. In the tail it is worse still, because that is when they move together.",
    whyYouCare: "Any claim that pooling n series adds n times the evidence has to measure it, and it usually does not.",
    source: persistence,
  },
  {
    term: "Step-up in basis",
    short: "Death resets an asset's cost basis to its market value, forgiving the gain outright.",
    long: "An unrealised gain is an interest-free loan from the government whose principal compounds with the position. Under §1014 that loan is forgiven at death, and a gift of appreciated long-term property to a public charity does the same while you are alive. Deferral is worth 84 bp a year at thirty years and the step-up a further 78, summing to a horizon-free 162.",
    whyYouCare:
      "It is the hurdle every turnover-bearing strategy in a taxable account must clear before its fee and its spread.",
    source: structural,
  },
  {
    term: "Specific identification",
    short: "Telling your broker exactly which shares to sell, rather than letting it pick.",
    long: "Regulation requires only that you specify the particular stock at the time of sale, and it accepts a standing instruction. The default without it is first-in-first-out, which realises the most gain available. Switching is free, needs no form, and is not a method of accounting.",
    whyYouCare: "Booked at 5 bp a year and it costs one instruction to your broker. Set it once and forget it.",
    source: structural,
  },
  {
    term: "Qualified dividend",
    short: "A dividend taxed at long-term capital-gain rates instead of ordinary rates.",
    long: "The US schedule offers 0%, 15%, 18.8% and 23.8%. A dividend qualifies only if the stock was held more than 60 days inside the 121-day window around the ex-dividend date, so a fund only 70% qualified on a 2% yield loses about 10.2 bp a year to the difference.",
    whyYouCare:
      "Which of the four rates you pay decides whether emerging-market equity belongs in your shelter or your taxable account.",
    source: structural,
  },
  {
    term: "Foreign tax credit",
    short: "Credit for tax a foreign government already withheld on your foreign dividends.",
    long: "A US fund pays foreign withholding and may elect to pass it through, after which you credit it against your US tax. Inside an IRA or a Roth there is no US tax to credit against, so the withholding is paid and permanently lost — 15.78 bp a year on a developed sleeve and 20.00 on emerging. Below $300 of creditable tax ($600 joint) you claim it without Form 1116 or its limitation.",
    whyYouCare: "It is the term that inverts the standard placement advice for one sleeve at two of the four US rates.",
    source: structural,
  },
  {
    term: "Securities lending",
    short: "Funds lend their holdings to short sellers and pass most of the fee back to you.",
    long: "It is small and it is real: about 1.01 bp a year for a US total-market fund, 0.07 for an S&P 500 fund, and 9 to 10 for a core emerging-markets one. The premium is international and emerging lending demand rather than a size effect — US small-cap earns the same as large-cap developed international. Unit investment trusts such as SPY and QQQ cannot lend at all.",
    whyYouCare:
      "It offsets 20% to 35% of the holding cost of a broad index ETF, and the sponsor's split matters more than the asset class.",
    source: structural,
  },
  {
    term: "Contango and the funding basis",
    short: "The built-in cost of holding exposure through futures rather than owning the asset.",
    long: "A futures contract embeds a financing rate, and that rate has been measured above cash: 58.70 basis points on five-year Treasury note futures over 1991–2018, positive in all 28 years. Equity futures are similar and more variable, and their sign is not even constant. It is a stable cost rather than a crisis artefact.",
    whyYouCare:
      "It is why a 90/60 return-stacked fund needs 92 bp a year of Treasury excess return before its overlay contributes anything.",
    source: structural,
  },
  {
    term: "Kelly, or growth-optimal sizing",
    short: "The bet size that maximises long-run compound growth, given a known edge.",
    long: "Betting the log-optimal fraction beats any other strategy asymptotically, which is a theorem rather than a preference. It is also unusable without an edge and its uncertainty, and the estimate has to be shrunk by its own standard error first. Omitting that shrinkage is the most likely catastrophic sizing error in a system like this.",
    whyYouCare: "It sizes an edge, and this repository has not established one, so nothing here is sized by it.",
    source: framework,
  },
  {
    term: "Sequence risk",
    short: "The order returns arrive in, which matters only when money is going in or out.",
    long: "Without external cash flows, permuting the order of returns leaves terminal wealth unchanged — it is a multiplication and multiplication commutes. Contributions and withdrawals break that identity, because a bad early year is applied to a different amount of money than a bad late one.",
    whyYouCare:
      "It is why a short-horizon or drawing investor holds less equity, and it is not because equities are riskier over short horizons in some deeper sense.",
    source: { label: "The recommended portfolio", docPath: "docs/research/portfolio-recommendation.md" },
  },
  {
    term: "Drawdown, and time under water",
    short: "The worst peak-to-trough fall, and how long it took to get back.",
    long: "The US total market returned 10.80% a year over 1963-07 to 2025-12 and fell 50.3% along the way, spending 72 months below its previous peak. Drawdown deepens mechanically with sample length, so two drawdowns from windows of different lengths cannot be compared directly.",
    whyYouCare: "Set the equity share at the level whose worst case you would hold through, then stop.",
    source: capture,
  },
  {
    term: "Model-misfit pedestal",
    short: "What a factor model charges a fund that is definitionally the market.",
    long: "A total-market fund is the market portfolio, so under a correctly specified model its alpha should be about minus its three-basis-point fee. Under the standard six-factor model over 2020–2025 it came out at −0.55 percentage points a year, with a HAC t of −3.41. Every fund priced by the same model over the same window carries that offset.",
    whyYouCare:
      'It is the difference between "this index fund destroyed 3 pp/yr" and "this model does not span these years to better than half a point". Read every alpha as a distance from the pedestal, never from zero.',
    source: productAudit,
  },
];
