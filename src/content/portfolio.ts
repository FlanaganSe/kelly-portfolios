import { type AsOf, asOf, type CertaintyClass, type Citation, type EvidenceStatus } from "~/content/types";

/**
 * The reference construction: named funds, weights and accounts.
 *
 * "Recommended" here means the best-supported construction given the evidence. It
 * does not mean it will beat an index, and it advances no sleeve's status. Nothing
 * on this page reached `production-eligible`, `walk-forward-tested` or even
 * `independently-reproduced` (decision 0006).
 *
 * Every fund-specific fact below is dated and must be re-checked rather than
 * re-quoted. Where a fee was never read by any experiment here, it is `null`.
 */

const recommendation: Citation = {
  label: "The recommended portfolio",
  docPath: "docs/research/portfolio-recommendation.md",
};

const decomposition: Citation = {
  label: "Where outperformance can come from",
  docPath: "docs/research/expected-edge-decomposition.md",
};
const equityShare: Citation = {
  label: "Setting the equity share",
  docPath: "docs/research/setting-the-equity-share.md",
};

// ---------------------------------------------------------------------------
// The one parameter the evidence cannot set
// ---------------------------------------------------------------------------

export interface RiskVariant {
  readonly id: "A" | "B" | "C" | "D";
  readonly label: string;
  readonly appliesWhen: string;
  /** `null` where the range is set by something other than the horizon. */
  readonly equityPercent: readonly [number, number] | null;
  readonly bondPercent: readonly [number, number] | null;
  /** Why the range is what it is, where that is not obvious from the row. */
  readonly note?: string;
}

export const riskVariants: readonly RiskVariant[] = [
  {
    id: "A",
    label: "Long horizon",
    appliesWhen:
      "20+ years, no liability inside it, contributions continuing, and a −50% equity fall changes no plan you have",
    equityPercent: [90, 100],
    bondPercent: [0, 10],
  },
  {
    id: "B",
    label: "Mixed",
    appliesWhen: "10 to 20 years, or a known liability inside the horizon",
    equityPercent: [70, 80],
    bondPercent: [20, 30],
  },
  {
    id: "C",
    label: "Short horizon",
    appliesWhen: "Under 10 years, whatever the cash flows",
    equityPercent: [40, 60],
    bondPercent: [40, 60],
  },
  {
    id: "D",
    label: "Drawing down",
    appliesWhen: "Withdrawals have begun over a long remaining horizon",
    equityPercent: null,
    bondPercent: null,
    note: "Set by the withdrawal rate, not by the horizon. C and D were one row until they were measured, and they point opposite ways.",
  },
];

/**
 * Failure probability over a 30-year real drawdown, by equity share and withdrawal rate.
 *
 * The drawdown ladder is monotone. This one is not, and that is the finding: the minimum
 * walks right as the withdrawal rate rises. Above about a 4% real draw, holding too few
 * equities is the larger risk.
 */
export const withdrawalFailureLadder = {
  equityShares: [20, 30, 40, 50, 60, 70, 80, 90, 100],
  rows: [
    {
      realWithdrawalPercent: 3,
      failurePercent: [0.07, 0.03, 0.03, 0.04, 0.07, 0.15, 0.27, 0.41, 0.64],
      safestIndex: 2,
    },
    { realWithdrawalPercent: 4, failurePercent: [6.82, 3.78, 2.88, 2.5, 2.43, 2.71, 3.17, 3.6, 4.24], safestIndex: 4 },
    {
      realWithdrawalPercent: 5,
      failurePercent: [47.34, 32.41, 22.74, 17.51, 14.87, 13.56, 13.06, 12.86, 13.16],
      safestIndex: 7,
    },
    {
      realWithdrawalPercent: 6,
      failurePercent: [86.77, 74.97, 60.77, 49.05, 40.96, 35.16, 31.31, 28.74, 27.27],
      safestIndex: 8,
    },
  ],
  basis:
    "CPI-deflated, level real withdrawal, 30-year horizon, 20,000 reorderings of 748 months of data. Real equity 6.66%/yr, real bond 1.98%/yr.",
  finding:
    "At 3% real the safest portfolio is genuinely the safe one. At 4% the minimum sits at 60% equity and a 20%-equity portfolio is nearly three times as likely to fail. At 5% and 6% failure falls almost all the way to 100% equity, because the withdrawal outruns the return and no ordering of a 1.98%/yr real bond supports a 5% real draw for thirty years.",
  caveat:
    "One country, one modelled bond, an iid permutation null, and a real bond return of 1.98%/yr that no reader should assume forward. It is enough to show that a single short-or-drawing row conflates two opposite cases, and not enough to set anyone's equity share.",
  status: "exploratory",
  source: equityShare,
  asOf: asOf("2026-08-12"),
} as const;

/**
 * The parameter-free half of the split decision: growth retained is `1 − (1 − f/f*)²`.
 *
 * The reason this is worth showing rather than an optimiser: the optimum itself is not
 * estimable. The standard error on the estimated growth-optimal fraction is about 2.05
 * at ten years of data at 15.4% volatility, and still 0.65 at a hundred years.
 */
export const growthPenalty = {
  headline:
    "Holding half the growth-optimal equity exposure costs a quarter of the peak excess growth. Holding double it costs all of it.",
  detail:
    "The asymmetry is multiplicative rather than additive, so erring low is cheap and erring high is not. In this portfolio you cannot err high anyway: with leverage fixed at zero the growth-optimal weight sits above 1 — about 2.28 at the sample premium — so every reachable equity share is on the left branch of the curve, and the only question is how far left you sit.",
  retainedAtHalf: 0.75,
  retainedAtDouble: 0.0,
  unconstrainedOptimalWeight: 2.28,
  cornerSolution:
    "Growth-optimal sizing carries no risk-aversion parameter, so with leverage at zero the objective on its own returns a corner solution of 100% equity for any equity-over-bond arithmetic premium above about 2.06 to 2.68%/yr. Every bond in the mixed and short-horizon variants comes from the drawdown constraint, not from the objective. Read the other way: choosing 60/40 asserts a premium forecast of about 1.18 to 1.30%/yr.",
  estimationCost:
    "The growth cost of estimating the optimum rather than knowing it is 1/(2T), free of every parameter — 2.50%/yr on twenty years of data and 0.80%/yr on sixty-two. Optimal shrinkage at the sample Sharpe over that longer record is 0.931, not the half-Kelly rule of thumb; half-Kelly would be claiming those sixty-two years are worth 4.66.",
  consequence:
    "Which is why the answer here ends on a drawdown you would have to sit through rather than on a number an optimiser produced.",
  status: "exploratory",
  source: equityShare,
} as const;

export const equityBondSplit = {
  headline: "The equity/bond split is the investor's to set and nothing here can set it.",
  detail:
    "It is the largest single decision in the portfolio and the only one the evidence is silent on. Everything below it follows from evidence. The three variants differ only in the equity share; the equity composition is identical in all three.",
  anchor:
    "Set the equity share at the level whose worst case you would hold through, then stop. The anchor is a measured drawdown, not a risk questionnaire.",
  sequenceRisk:
    "Sequence risk is a cash-flow interaction, not a premium. Without external cash flows, permuting the order of returns leaves terminal wealth unchanged. Variant C exists because contributions and withdrawals break that identity, not because equities are riskier over short horizons in some deeper sense.",
  source: recommendation,
} as const;

/** The measured worst case, from research portfolios rather than a questionnaire. */
export const drawdownAnchor = {
  asset: "US total market",
  geometricReturnPercent: 10.8,
  volatilityPercent: 15.4,
  maxDrawdownPercent: -50.3,
  monthsUnderWater: 72,
  window: "1963-07…2025-12",
  source: {
    label: "The long-only capture fraction, the small-value corner",
    docPath: "docs/research/long-only-capture.md",
    anchor: "the-small-value-corner",
  },
  asOf: asOf("2026-08-12"),
} as const;

// ---------------------------------------------------------------------------
// The equity sleeve weights
// ---------------------------------------------------------------------------

/**
 * These are the repository's own declared research weights, frozen in Experiment
 * 003's specification before any result was examined. They are a stated choice, not
 * a measured optimum and not a market weight. No global market-capitalisation series
 * exists in this repository, so no page here can tell you the market weight.
 */
export const equitySleeveWeights = {
  weights: [
    { sleeve: "US total market", percentOfEquity: 60 },
    { sleeve: "Developed ex-US", percentOfEquity: 30 },
    { sleeve: "Emerging markets", percentOfEquity: 10 },
  ],
  isMeasuredOptimum: false,
  isMarketWeight: false,
  provenance: "A declared research weight, frozen before results were examined (Experiment 003's specification).",
  caveat:
    "A US 45 / international 35 proposal is a 56:44 split against this 60:40, and no page here can distinguish them. There is no global market-capitalisation series in this repository and no experiment signed a regional tilt. Choose either and stop.",
  source: recommendation,
  asOf: asOf("2026-08-12"),
} as const;

// ---------------------------------------------------------------------------
// The funds
// ---------------------------------------------------------------------------

export type FundRole = "core" | "core-alternative" | "optional-sleeve" | "priced-but-not-held";

export interface FundAlternate {
  readonly ticker: string;
  readonly name: string;
  /** Basis points a year. `null` means no experiment here read it. */
  readonly expenseRatioBp: number | null;
  readonly note?: string;
}

export interface Fund {
  readonly id: string;
  readonly ticker: string;
  readonly name: string;
  readonly sleeve: string;
  readonly role: FundRole;
  /** Basis points a year. `null` means no experiment in this repository priced it — look it up. */
  readonly expenseRatioBp: number | null;
  readonly expenseRatioAsOf: AsOf | null;
  readonly expenseRatioNote?: string;
  /** 30-day median bid/ask spread, basis points. */
  readonly spreadBp: number | null;
  /** Net securities-lending income as a fraction of average net assets, as the filing supports it. */
  readonly securitiesLendingBp: string | null;
  readonly alternates: readonly FundAlternate[];
  /** What the line buys, and its class. A risk premium may never be described as an edge. */
  readonly whatItBuys: string;
  readonly certaintyClass: CertaintyClass;
  /** The status of what it buys, where an experiment set one. */
  readonly status: EvidenceStatus | null;
  readonly source: Citation;
}

const feeNotRead =
  "Never priced by any experiment in this repository. Look it up; do not take a number from here that this repository does not have.";

export const funds: readonly Fund[] = [
  {
    id: "vti",
    ticker: "VTI",
    name: "Vanguard Total Stock Market ETF",
    sleeve: "US total market",
    role: "core",
    expenseRatioBp: 3,
    expenseRatioAsOf: asOf("2026-08-10"),
    spreadBp: 0.55,
    securitiesLendingBp: "1.01",
    alternates: [
      { ticker: "VOO", name: "Vanguard S&P 500 ETF", expenseRatioBp: 3, note: "spread 0.58 bp; lending 0.07 bp" },
      {
        ticker: "ITOT",
        name: "iShares Core S&P Total US Stock Market ETF",
        expenseRatioBp: null,
        note: `${feeNotRead} Lending 1.03 bp.`,
      },
    ],
    whatItBuys:
      "The equity risk premium at 3 bp, about 1.3 bp of round-trip friction, plus roughly 1.01 bp/yr of securities-lending pass-through. The cost is certain. The return is not, and no page here forecasts it.",
    certaintyClass: "nothing-better-exists",
    status: null,
    source: recommendation,
  },
  {
    id: "vea",
    ticker: "VEA",
    name: "Vanguard FTSE Developed Markets ETF",
    sleeve: "Developed ex-US",
    role: "core",
    expenseRatioBp: null,
    expenseRatioAsOf: null,
    expenseRatioNote: feeNotRead,
    spreadBp: null,
    securitiesLendingBp: "~2.97",
    alternates: [
      {
        ticker: "IEFA",
        name: "iShares Core MSCI EAFE ETF",
        expenseRatioBp: null,
        note: `${feeNotRead} Lending 1.08–1.11 bp.`,
      },
    ],
    whatItBuys:
      "Diversification of the equity claim, not an edge. Its foreign tax credit is worth 15.78 bp/yr and only in a taxable account.",
    certaintyClass: "nothing-better-exists",
    status: null,
    source: recommendation,
  },
  {
    id: "vwo",
    ticker: "VWO",
    name: "Vanguard FTSE Emerging Markets ETF",
    sleeve: "Emerging markets",
    role: "core",
    expenseRatioBp: null,
    expenseRatioAsOf: null,
    expenseRatioNote: feeNotRead,
    spreadBp: null,
    securitiesLendingBp: "~4.9–5.2",
    alternates: [
      {
        ticker: "IEMG",
        name: "iShares Core MSCI Emerging Markets ETF",
        expenseRatioBp: null,
        note: `${feeNotRead} Lending 9.2–9.7 bp.`,
      },
    ],
    whatItBuys:
      "The same diversification. Its credit is worth 20.00 bp/yr in taxable, and it is the sleeve the placement arithmetic moves.",
    certaintyClass: "nothing-better-exists",
    status: null,
    source: recommendation,
  },
  {
    id: "bnd",
    ticker: "BND",
    name: "Vanguard Total Bond Market ETF",
    sleeve: "Investment-grade bonds",
    role: "core",
    expenseRatioBp: null,
    expenseRatioAsOf: null,
    expenseRatioNote: feeNotRead,
    spreadBp: null,
    securitiesLendingBp: null,
    alternates: [{ ticker: "—", name: "A Treasury fund", expenseRatioBp: null, note: feeNotRead }],
    whatItBuys:
      "Term and credit compensation, and a risk brake. Sized by the investor's risk capacity. Booking a term premium as an edge over an equity index swaps the benchmark rather than adding return.",
    certaintyClass: "different-benchmark",
    status: null,
    source: recommendation,
  },
  {
    id: "vxus",
    ticker: "VXUS",
    name: "Vanguard Total International Stock ETF",
    sleeve: "Whole international sleeve in one fund",
    role: "core-alternative",
    expenseRatioBp: 3,
    expenseRatioAsOf: asOf("2026-08-10"),
    spreadBp: 1.18,
    securitiesLendingBp: "~3.4–3.6",
    alternates: [],
    whatItBuys:
      "Developed and emerging international equity in one holding, at the cost of the placement result. See `vxusTradeoff`.",
    certaintyClass: "nothing-better-exists",
    status: null,
    source: decomposition,
  },
  {
    id: "vbr",
    ticker: "VBR",
    name: "Vanguard Small-Cap Value ETF",
    sleeve: "Small-cap value tilt",
    role: "optional-sleeve",
    expenseRatioBp: 5,
    expenseRatioAsOf: asOf("2026-08-12"),
    expenseRatioNote: "Read from the sponsor's own prospectus or fund page, with the URL and date recorded.",
    spreadBp: null,
    securitiesLendingBp: null,
    alternates: [],
    whatItBuys:
      "An HML loading of +0.410 [+0.322, +0.480], delivered and stable, at 5 bp, with a negative shortfall against a fitted four-fund combination. It is the only US value product that both delivers its exposure and does not lose to a cheap mix. It is not here because the chain is positive.",
    certaintyClass: "risk-premium",
    status: "exploratory",
    source: recommendation,
  },
  {
    id: "dbmf",
    ticker: "DBMF",
    name: "iMGP DBi Managed Futures Strategy ETF",
    sleeve: "Managed futures",
    role: "optional-sleeve",
    expenseRatioBp: 85,
    expenseRatioAsOf: asOf("2026-08-12"),
    expenseRatioNote: "Read from the fund's SEC-filed 497K summary prospectus fee table, with its accession number.",
    spreadBp: null,
    securitiesLendingBp: null,
    alternates: [],
    whatItBuys:
      "A loading of +0.671 [+0.513, +0.829] on the AQR time-series-momentum index, stable across the fixed split and all 19 rolling windows, trailing a cost-free vendor index by 0.48 pp/yr against an 0.85% fee. Crisis correlation −0.59 and downside beta −0.67 — but the post-publication interval includes zero and fails Holm.",
    certaintyClass: "risk-premium",
    status: "exploratory",
    source: recommendation,
  },
  {
    id: "vb",
    ticker: "VB",
    name: "Vanguard Small-Cap ETF",
    sleeve: "Plain small-cap",
    role: "priced-but-not-held",
    expenseRatioBp: 3,
    expenseRatioAsOf: asOf("2026-08-10"),
    spreadBp: 2.72,
    securitiesLendingBp: "~3.0–3.1",
    alternates: [],
    whatItBuys:
      "Nothing this construction holds. It is priced here because it is one of the four funds the cheap replication is built from, and because its 2.72 bp round trip is nearly a year of expense ratio — which is the binding constraint on rebalancing frequency, and larger than the 2.4 bp/yr the rebalancing line was ever budgeted.",
    certaintyClass: "risk-premium",
    status: "rejected",
    source: decomposition,
  },
];

export const vxusTradeoff = {
  headline: "Use VXUS instead of VEA + VWO only if you will hold the whole international sleeve in one account.",
  why: "Splitting developed from emerging is what makes the placement result available, and VXUS forecloses it. The emerging inversion depends on emerging being separately holdable.",
  vxusFacts: "Expense ratio 3 bp, 30-day median bid/ask spread 1.18 bp.",
  asOf: asOf("2026-08-10"),
  source: recommendation,
} as const;

export const feePolicy = {
  headline: "Fees not read here are not omissions of convenience.",
  detail:
    "VTI, VOO, VXUS and VB are confirmed at 3 bp as of 2026-08-10. VBR at 5 bp and every other factor fee comes from the sponsor's own prospectus or fund page with its URL and date recorded; every managed-futures fee comes from the fund's SEC-filed 497K summary prospectus fee table with its accession number, both as of 2026-08-12. VEA, VWO, BND, IEFA and IEMG were never priced by any experiment here.",
  instruction: "Look them up. Do not take a number from this content layer that this repository does not have.",
  source: recommendation,
} as const;

// ---------------------------------------------------------------------------
// The two optional sleeves
// ---------------------------------------------------------------------------

export interface OptionalSleeve {
  readonly id: string;
  readonly label: string;
  readonly ticker: string;
  readonly expenseRatioBp: number;
  readonly expenseRatioAsOf: AsOf;
  readonly size: string;
  readonly requiredAccount: string;
  readonly verdict: string;
  readonly sizingNote: string;
  readonly productStatus: EvidenceStatus;
  readonly underlyingStatus: EvidenceStatus;
  readonly source: Citation;
}

export const optionalSleeves: readonly OptionalSleeve[] = [
  {
    id: "small-cap-value",
    label: "Small-cap value",
    ticker: "VBR",
    expenseRatioBp: 5,
    expenseRatioAsOf: asOf("2026-08-12"),
    size: "0–20% of US equity",
    requiredAccount: "Anywhere. Treat it as US equity in the placement ranking",
    verdict:
      "An `exploratory` product on an `exploratory` premium, and the chain is negative on the defensible reading of both terms. Its best case is +15 bp/yr against 140 bp of tracking error; its worst is a persistent loss.",
    sizingNote:
      "VBR's yield is higher than the market's, which raises its shelter priority above the 26.2 / 20.7 / 16.5 bp of plain US equity. By how much is not measured here.",
    productStatus: "exploratory",
    underlyingStatus: "exploratory",
    source: recommendation,
  },
  {
    id: "managed-futures",
    label: "Managed futures",
    ticker: "DBMF",
    expenseRatioBp: 85,
    expenseRatioAsOf: asOf("2026-08-12"),
    size: "0–10% of total",
    requiredAccount: "Tax-deferred only",
    verdict:
      "An `exploratory` product on an `unresolved` index, with single-product risk: four of the five listed managed-futures ETFs fail the 0.50 loading bar, so there is no fallback. Its 2.09 pp/yr distribution tax drag is 2.5× its own fee in a taxable account and zero in a shelter.",
    sizingNote:
      "Experiment 004 priced a 15% trend sleeve, not a 10% one. The cap is set below the tested weight because one product delivers the exposure and there is no fallback, not because 10% was measured to be better.",
    productStatus: "exploratory",
    underlyingStatus: "unresolved",
    source: recommendation,
  },
];

// ---------------------------------------------------------------------------
// The disciplines, and what the construction is not
// ---------------------------------------------------------------------------

export const constructionSummary = {
  headline: "The portfolio is the control plus placement.",
  detail:
    "A cheap, broad, long-only, fully invested global equity/bond portfolio, held in the right accounts, with lot discipline, and not traded. That is not a default chosen for want of anything better. It is the only construction whose delivery is contractual rather than statistical.",
  disciplinesAreWorthMore:
    "The disciplines are worth more than the sleeves. About 109 bp/yr against your own counterfactual, 99% confident in about twelve months, against a best case of 15.2 bp for a 20% small-value tilt and 90 bp for a sheltered trend sleeve.",
  source: recommendation,
  asOf: asOf("2026-08-12"),
} as const;

export const whatThisIsNot: readonly { readonly claim: string; readonly detail: string }[] = [
  {
    claim: "Not personalised advice",
    detail:
      "A construction derived from measurements, for one stated reference investor: US federal, top or specified bracket, thirty-year horizon, contributions continuing, state tax excluded.",
  },
  {
    claim: "Not a forecast",
    detail:
      "No expected return for any market appears anywhere in this content. Every probability is conditional on edges being what the cited pages measured, and every one is an upper bound because it treats those edges as known.",
  },
  {
    claim: "Not a promotion",
    detail:
      "No sleeve reached `production-eligible`, or `walk-forward-tested`, or even `independently-reproduced`. VBR and DBMF are `exploratory` products, which permits them to be used as implementation proxies in a later experiment and permits nothing else.",
  },
  {
    claim: "Not a claim of outperformance against an index",
    detail:
      "Against a cheap index the whole honest budget is about 24 bp against 401 bp of tracking error — a 0.631 probability of being ahead after thirty years.",
  },
  {
    claim: "Not net of everything",
    detail:
      "No page here has a full after-tax, after-spread, after-turnover return for any product. Bid-ask, brokerage, realised distributions and portfolio turnover are absent from the product audit entirely.",
  },
  {
    claim: "Not free of model risk",
    detail:
      "FF5+UMD prices VTI itself at −0.55 pp/yr with a HAC t of −3.41 over 2020–2025. The standard model does not span the control, and every alpha here is a distance from that pedestal rather than from zero.",
  },
  {
    claim: "Not vintage-stable",
    detail:
      "Ken French rebuilds the whole history from the current vintage on every rebuild, and the Phase 1 gate is `unresolved`. HML's and RMW's standard deviations do not reproduce, leaving a systematic 3–5% band on anything that divides by them. Five series carry no measured band at all, which is weaker than a band of zero — including all three momentum files.",
  },
];
