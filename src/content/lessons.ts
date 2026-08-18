/**
 * The short course.
 *
 * Fourteen things a reader has to understand before any other page on this site is
 * useful, each written to be read in under a minute and each grounded in a number this
 * repository actually measured. They are ordered so that each one depends only on the
 * ones above it.
 *
 * These are explanations, not findings. Where a lesson quotes a figure, the figure's
 * owner is the page `href` points at, and that page carries its status and its interval.
 */

export interface Lesson {
  readonly id: string;
  /** A claim, not a topic. "What the market benchmark means" is a topic; state the claim. */
  readonly title: string;
  readonly body: string;
  /** Where to go for the evidence. A site path, not a document. */
  readonly href: string;
  readonly hrefLabel: string;
}

export const lessons: readonly Lesson[] = [
  {
    id: "which-market",
    title: "“The market” is two different benchmarks, and they never add",
    body: "Beating a cheap index fund and beating the portfolio you would otherwise have owned are different claims about different reference portfolios. Cost and tax discipline is worth about 109 bp a year against the second and about 46 bp against the first, and adding them would double-count the same work. This repository's own code raises an error rather than summing lines measured against different benchmarks, because it made that mistake in four places before it did.",
    href: "/research/structural-and-tax",
    hrefLabel: "The contractual budget",
  },
  {
    id: "alpha-vs-beta",
    title: "Extra return from extra risk is not skill",
    body: "A portfolio that holds more equity, or that borrows to hold more of everything, should earn more on average. That is more beta, not alpha, and the honest comparison is against the same risk taken the simple way. Moving from 60/40 to 90/10 is worth about +127 bp a year against 485 bp of tracking error: more than every factor tilt on this site combined, and still only 92% likely to be ahead after thirty years. It is not an edge, because anyone can do it by changing one number.",
    href: "/research/equity-share",
    hrefLabel: "The equity share",
  },
  {
    id: "tracking-error-decides",
    title: "Tracking error, not the size of the edge, decides whether a lifetime is enough",
    body: "Time to any confidence level scales with the square of tracking error over edge: T = (z·s/e)². The same 50 bp edge reaches 90% confidence in about 24 days at 10 bp of tracking error and in about 105 years at 400 bp. It is why a 109 bp contractual edge is 99% established inside a year while a 46 bp index-relative one needs about 245 years for the same confidence, and 74 even for 90%. The smaller number is not the reason.",
    href: "/lab",
    hrefLabel: "Try it in the lab",
  },
  {
    id: "positive-and-losing",
    title: "A strategy with a positive expected return can lose for decades",
    body: "If a tilt earns 25 bp a year against 135 bp of dispersion, a run of ten bad years is ordinary rather than evidence of anything. Simulating the same model shows the route as well as the destination: at a small edge against a large tracking error, most paths spend years below their own previous best relative to the benchmark. Deciding in advance how long you will hold is the only defence, because deciding afterwards always looks like the strategy broke.",
    href: "/lab",
    hrefLabel: "See the drought",
  },
  {
    id: "correlated-is-not-diverse",
    title: "Stacking several correlated strategies is not diversification",
    body: "Momentum across three regions is worth about 1.33 effective regions, and all three lost their worst calendar year in the same year. Credit correlates +0.835 with Treasuries and TIPS +0.76 to +0.85 with the nominal bond funds beside them — one engine, not two. The test is what the sleeves do together in the months that matter, not how different their names are.",
    href: "/research/alternatives",
    hrefLabel: "The alternatives audit",
  },
  {
    id: "capital-is-not-exposure",
    title: "A capital weight does not tell you what you are exposed to",
    body: "A fund holding 30% of a portfolio can carry 32% of equity and 30% of managed futures at the same time, because the futures are financed rather than bought. Every portfolio on this site that uses one shows its notional exposure separately, and weights stated in capital may never be compared with weights stated in notional.",
    href: "/research/capital-efficiency",
    hrefLabel: "Return stacking",
  },
  {
    id: "cost-eats-premia",
    title: "Implementation cost routinely erases a paper premium",
    body: "The largest gross factor premium measured here is momentum at +7.33 pp/yr. The academic construction turns over 27.5% to 91.5% of its book a month, which implies 3.3 to 18.7 pp/yr of trading cost. The one investable route audited files 105% annual turnover and loses 43% of its gross exposure to cost. The premium is real and it does not reach the shareholder.",
    href: "/research/momentum",
    hrefLabel: "Momentum",
  },
  {
    id: "fund-not-strategy",
    title: "Two funds with the same label are not the same fund",
    body: "Among audited US value products the HML loading ranges from +0.32 to +0.71 and the fee from 5 bp to 35 bp, and a fund's cost is its fee less its securities-lending income — which reorders the shelf. IEMG costs less to own than VWO at a 50% higher fee. Buy the exposure and the cost, never the category.",
    href: "/funds",
    hrefLabel: "The shelf",
  },
  {
    id: "long-only-is-not-long-short",
    title: "A long-only fund is not the academic factor",
    body: "Published premia are long-short spreads with no costs and no shorting constraint. What a shareholder receives is weight × (fund loading − incumbent loading) × premium, less the incremental cost. Three terms. Multiplying by a further “capture fraction” discounts the same exposure twice — 94% of the measured 0.520 capture is the 0.4891 loading, an identity exact to 4.4 × 10⁻¹⁶ — and doing it understated this repository's own value tilt by about half.",
    href: "/research/value",
    hrefLabel: "Value",
  },
  {
    id: "trend-is-insurance",
    title: "Trend following is a correlation claim before it is a return claim",
    body: "Managed futures correlate near zero with equity unconditionally and about −0.59 inside crisis months, with a downside beta of −0.67. That part holds on three independent instruments. The mean return does not resolve on any of them: post-publication the sleeve measures +0.883 pp/yr with an interval containing zero. Size it for the drawdown it changes, not for the return it might add.",
    href: "/research/trend",
    hrefLabel: "Trend",
  },
  {
    id: "gold",
    title: "An asset can be useful without being expected to beat equities",
    body: "Gold's Sharpe ratio is 0.18 against equity's 0.59 since 1975, and its correlation to equity sits between −0.02 and +0.03. Held pro rata it costs about 0.40 pp/yr of growth; held as a financed overlay it adds about 0.18. Its case is entirely about what it does beside other things, and on this repository's 0.30 pp/yr bar it still fails.",
    href: "/research/alternatives",
    hrefLabel: "The alternatives audit",
  },
  {
    id: "rebalancing",
    title: "Rebalancing is risk control, not a source of return",
    body: "The rebalancing premium is real and tiny: γ* = ½(Σwᵢσᵢ² − σp²). Measured over 420 months the drift gap ran 35 times larger than the premium, and rebalancing lost 38.7 bp a year against buy-and-hold. What it bought was exposure control — mean drift held to 0.6–3.1 points instead of 14.8 — for 0.3 to 1.2 bp a year. Keep doing it. Do not budget a bonus for it.",
    href: "/research/rebalancing",
    hrefLabel: "Rebalancing",
  },
  {
    id: "taxes-and-accounts",
    title: "Where a fund is held changes what you keep",
    body: "Foreign withholding is paid and permanently lost inside an IRA, because §408(e)(1) exempts the account and §904's numerator becomes zero. The resulting ranking between developed and emerging markets inverts at a 21.51% qualified dividend rate, which sits between two live US brackets — so a rule of thumb is wrong for a large share of readers and the arithmetic has to be done for your own bracket.",
    href: "/research/placement",
    hrefLabel: "Asset location",
  },
  {
    id: "backtest-is-not-proof",
    title: "A backtest is evidence, and a weak kind",
    body: "On this shelf 96 of 109 factor loadings survive multiple-comparison correction, and 5 of 327 alpha tests do — all five negative. The median alpha these windows could detect is about 5 pp/yr against roughly 1.25 pp/yr of true dispersion between funds, so most alpha findings are noise by construction. Exposure is measurable; skill is not.",
    href: "/method",
    hrefLabel: "How a result earns a status",
  },
];
