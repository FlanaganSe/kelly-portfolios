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
    "The asymmetry is multiplicative rather than additive, so erring low is cheap and erring high is not. In this portfolio you cannot err high anyway: with borrowing fixed at zero the growth-optimal weight sits above 1 — about 2.28 at the sample premium — so every reachable equity share is on the left branch of the curve, and the only question is how far left you sit.",
  retainedAtHalf: 0.75,
  retainedAtDouble: 0.0,
  unconstrainedOptimalWeight: 2.28,
  cornerSolution:
    "Growth-optimal sizing carries no risk-aversion parameter, so with borrowing at zero the objective on its own returns a corner solution of 100% equity for any equity-over-bond arithmetic premium above about 2.06 to 2.68%/yr. Every bond in the mixed and short-horizon variants comes from the drawdown constraint, not from the objective. Read the other way: choosing 60/40 asserts a premium forecast of about 1.18 to 1.30%/yr.",
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

/**
 * The figure above is one country, and it is close to the best one. Sixteen countries
 * of annual real total returns rank the United States 15th of 16 on the full sample and
 * 16th of 16 from 1963. Rendering -50.3% without this reads as a worst case when it is
 * nearly a best case.
 */
export const drawdownAcrossCountries = {
  headline: "That is one country, and it is close to the luckiest one.",
  detail:
    "Across sixteen countries of annual real total returns, the median market lost about three quarters of its real value at some point. In the same window this anchor is drawn from, every one of the other fifteen did worse than the United States, and fourteen of fifteen did worse than -50%. France fell 97.7% from its 1942 peak and had not regained it 78 years later.",
  countries: 16,
  usRankFullSample: 15,
  usRankFrom1963: 16,
  medianDrawdownPercent: -74.4,
  worstDrawdownPercent: -98.4,
  worstCountry: "Portugal",
  caveat:
    "Annual and real against this anchor's monthly and nominal, so the like-for-like US figure is -47.2%. Portugal's worst years are source-flagged interpolations; without them it is -80.1% and the cleanest fully-measured near-total loss is France's.",
  status: "exploratory",
  source: {
    label: "Setting the equity share",
    docPath: "docs/research/setting-the-equity-share.md",
    anchor: "5-the-drawdown-anchor-which-is-the-operational-form-of-the-answer",
  },
  asOf: asOf("2026-08-16"),
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
    "A US 45 / international 35 proposal is a 56:44 split against this 60:40, and no page here can distinguish them. There is no global market-capitalisation series in this repository and no experiment signed a regional lean. Choose either and stop.",
  source: recommendation,
  asOf: asOf("2026-08-12"),
} as const;

// ---------------------------------------------------------------------------
// The funds
// ---------------------------------------------------------------------------

export type FundRole = "core" | "core-alternative" | "optional-holding" | "priced-but-not-held";

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
  /**
   * 30-day median bid/ask spread, basis points, from the issuer's own Rule 6c-11(c)(1)
   * disclosure as of 2026-08-14. **A one-time cost at purchase, not a recurring one**, so
   * it must never be allowed to outrank the expense ratio for a long holder — SPY has the
   * tightest spread on the shelf and the highest cost of ownership on it.
   */
  readonly spreadBp: number | null;
  /**
   * Net securities-lending income over average net assets, basis points a year: the
   * **median** over every fiscal year Form N-CEN has filed. Measured, not promised — the
   * fee is contractual and borrow demand is not.
   */
  readonly securitiesLendingBp: string | null;
  /**
   * `expense ratio - securities lending`, basis points a year, and the quantity a fee
   * comparison leaves out. Both terms are measured against the fund's own net assets, so
   * adding them is not a benchmark switch. Can be negative.
   */
  readonly netCostBp: number | null;
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

/** Every core fee below is a 497K summary-prospectus fee table read on this date. */
const FEE_TABLES_READ = asOf("2026-08-17");

export const funds: readonly Fund[] = [
  {
    id: "vti",
    ticker: "VTI",
    name: "Vanguard Morningstar Total Stock Market ETF",
    sleeve: "US total market",
    role: "core",
    expenseRatioBp: 3,
    expenseRatioAsOf: FEE_TABLES_READ,
    spreadBp: 0.55,
    securitiesLendingBp: "1.84",
    netCostBp: 1.16,
    alternates: [
      {
        ticker: "ITOT",
        name: "iShares Core S&P Total US Stock Market ETF",
        expenseRatioBp: 3,
        note: "lending 1.96 bp, net cost 1.04 bp — marginally cheaper to own.",
      },
      {
        ticker: "VOO",
        name: "Vanguard S&P 500 ETF",
        expenseRatioBp: 3,
        note: "spread 0.58 bp; lending 0.06 bp, net cost 2.94 bp. Same fee, 1.78 bp less lending.",
      },
    ],
    whatItBuys:
      "The equity risk premium at a net cost of 1.16 bp/yr — a 3 bp fee less 1.84 bp of securities lending — plus about 1.3 bp of round-trip friction paid once. The cost is certain. The return is not, and no page here forecasts it.",
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
    expenseRatioBp: 3,
    expenseRatioAsOf: FEE_TABLES_READ,
    spreadBp: 1.41,
    securitiesLendingBp: "3.30",
    netCostBp: -0.3,
    alternates: [
      {
        ticker: "SPDW",
        name: "SPDR Portfolio Developed World ex-US ETF",
        expenseRatioBp: 3,
        note: "lending 4.63 bp, net cost -1.63 bp — the cheapest developed ex-US fund audited.",
      },
      {
        ticker: "IEFA",
        name: "iShares Core MSCI EAFE ETF",
        expenseRatioBp: 7,
        note: "lending 2.35 bp, net cost 4.65 bp.",
      },
    ],
    whatItBuys:
      "Diversification of the equity claim, not an edge, at a net cost of -0.30 bp/yr: 3.30 bp of securities lending more than covers the 3 bp fee. Its foreign tax credit is worth 15.78 bp/yr and only in a taxable account.",
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
    expenseRatioBp: 6,
    expenseRatioAsOf: FEE_TABLES_READ,
    spreadBp: 1.7,
    securitiesLendingBp: "4.33",
    netCostBp: 1.67,
    alternates: [
      {
        ticker: "IEMG",
        name: "iShares Core MSCI Emerging Markets ETF",
        expenseRatioBp: 9,
        note: "lending 9.87 bp, net cost -0.87 bp. A 50% higher fee and the cheaper fund to own. Its fee is capped at 0.09% through 2030-12-31, with no recoupment.",
      },
    ],
    whatItBuys:
      "The same diversification, at a net cost of 1.67 bp/yr. Its credit is worth 20.00 bp/yr in taxable, and it is the holding the placement arithmetic moves.",
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
    expenseRatioBp: 3,
    expenseRatioAsOf: FEE_TABLES_READ,
    spreadBp: 1.38,
    securitiesLendingBp: "0.00 — does not lend",
    netCostBp: 3.0,
    alternates: [
      {
        ticker: "SPAB",
        name: "SPDR Portfolio Aggregate Bond ETF",
        expenseRatioBp: 3,
        note: "lending 0.91 bp, net cost 2.09 bp.",
      },
      { ticker: "—", name: "A Treasury fund", expenseRatioBp: null, note: feeNotRead },
    ],
    whatItBuys:
      "Term and credit compensation, and a risk brake, at a net cost of 3.00 bp/yr — the dearest aggregate-bond fund audited, because it is the only one that does not lend securities at all. Sized by the investor's risk capacity. Booking a term premium as an edge over an equity index swaps the benchmark rather than adding return.",
    certaintyClass: "different-benchmark",
    status: null,
    source: recommendation,
  },
  {
    id: "vxus",
    ticker: "VXUS",
    name: "Vanguard Total International Stock ETF",
    sleeve: "Whole international slice in one fund",
    role: "core-alternative",
    expenseRatioBp: 5,
    expenseRatioAsOf: FEE_TABLES_READ,
    expenseRatioNote:
      "5 bp from the 497K fee table dated 2026-02-27. This repository previously recorded 3 bp, which was wrong.",
    spreadBp: 1.18,
    securitiesLendingBp: "3.57",
    netCostBp: 1.43,
    alternates: [
      { ticker: "VEU", name: "Vanguard FTSE All-World ex-US ETF", expenseRatioBp: 4, note: "net cost 1.61 bp." },
      {
        ticker: "IXUS",
        name: "iShares Core MSCI Total International Stock ETF",
        expenseRatioBp: 7,
        note: "net cost 3.99 bp.",
      },
    ],
    whatItBuys:
      "Developed and emerging international equity in one holding, at 1.43 bp net — the cheapest total-international fund audited, and still dearer than holding the two separately. The trade-off is set out below.",
    certaintyClass: "nothing-better-exists",
    status: null,
    source: decomposition,
  },
  {
    id: "vbr",
    ticker: "VBR",
    name: "Vanguard Morningstar Small-Cap Value ETF",
    sleeve: "Small-cap value lean",
    role: "optional-holding",
    expenseRatioBp: 5,
    expenseRatioAsOf: asOf("2026-08-12"),
    expenseRatioNote: "Read from the sponsor's own prospectus or fund page, with the URL and date recorded.",
    spreadBp: null,
    securitiesLendingBp: null,
    netCostBp: null,
    alternates: [],
    whatItBuys:
      "An HML exposure of +0.410 [+0.322, +0.480], delivered and stable, at 5 bp, with a negative shortfall against a fitted four-fund combination. It is the only US value product that both delivers its exposure and does not lose to a cheap mix. It is not here because the chain is positive.",
    certaintyClass: "risk-premium",
    status: "exploratory",
    source: recommendation,
  },
  {
    id: "dbmf",
    ticker: "DBMF",
    name: "iMGP DBi Managed Futures Strategy ETF",
    sleeve: "Managed futures",
    role: "optional-holding",
    expenseRatioBp: 85,
    expenseRatioAsOf: asOf("2026-08-12"),
    expenseRatioNote: "Read from the fund's SEC-filed 497K summary prospectus fee table, with its accession number.",
    spreadBp: null,
    securitiesLendingBp: null,
    netCostBp: null,
    alternates: [],
    whatItBuys:
      "An exposure of +0.671 [+0.513, +0.829] on the AQR time-series-momentum index, stable across the fixed split and all 19 rolling windows, trailing a cost-free vendor index by 0.48 pp/yr against an 0.85% fee. Crisis correlation −0.59 and downside beta −0.67 — but the post-publication interval includes zero and fails Holm.",
    certaintyClass: "risk-premium",
    status: "exploratory",
    source: recommendation,
  },
  {
    id: "vb",
    ticker: "VB",
    name: "Vanguard Morningstar Small-Cap ETF",
    sleeve: "Plain small-cap",
    role: "priced-but-not-held",
    expenseRatioBp: 3,
    expenseRatioAsOf: asOf("2026-08-10"),
    spreadBp: 2.72,
    securitiesLendingBp: "~3.0–3.1",
    netCostBp: null,
    alternates: [],
    whatItBuys:
      "Nothing this construction holds. It is priced here because it is one of the four funds the cheap replication is built from, and because its 2.72 bp round trip is nearly a year of expense ratio — which is the binding constraint on rebalancing frequency, and larger than the 2.4 bp/yr the rebalancing line was ever budgeted.",
    certaintyClass: "risk-premium",
    status: "rejected",
    source: decomposition,
  },
];

export const vxusTradeoff = {
  headline: "Hold VEA + VWO rather than VXUS. The split is cheaper before any placement argument.",
  why: "VXUS costs 5 bp against a 75/25 blend of VEA and VWO at 3.75, and lending is a wash — so splitting saves 1.25 bp/yr on the international slice, 0.50 bp of equity, whatever accounts the reader has. The placement result is separate and smaller: 1.33 bp/yr of equity at a 23.8% qualified rate, 0.96 at 15%, and exactly zero once the shelter holds the whole equity slice. VXUS buys one fewer holding, one fewer spread crossing, and market weights this repository cannot otherwise supply.",
  vxusFacts:
    "Expense ratio 5 bp from the 497K fee table dated 2026-02-27, securities lending 3.57 bp, net cost 1.43 bp, 30-day median bid/ask spread 1.18 bp as of 2026-08-10. This repository previously recorded VXUS at 3 bp, which was wrong.",
  asOf: asOf("2026-08-17"),
  source: recommendation,
} as const;

export const feePolicy = {
  headline: "A fee comparison is not a cost comparison, and every core fee here is now a filed one.",
  detail:
    "The four core funds and twenty-one alternates were audited on 2026-08-17 from SEC-filed 497K fee tables and 110 Form N-CEN filings, so net cost — the fee less securities-lending income — is measured rather than looked up. It reorders the shelf: IEMG charges 9 bp against VWO's 6 and costs less to own, and BND is the dearest aggregate-bond fund audited because it is the only one that does not lend at all. The recommended four cost 1.36 bp/yr against 0.76 for the cheapest combination available, so the whole fund-selection decision is 0.60 bp/yr. VBR at 5 bp and every factor fee comes from the sponsor's own prospectus with its URL and date; every managed-futures fee comes from the fund's 497K fee table with its accession number, both as of 2026-08-12.",
  instruction:
    "The fee is contractual and the lending income is a measurement over the fiscal years on file. Do not read the second as a promise, and never rank two funds on a tracking difference taken against two different indices.",
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
      "An exploratory product on an exploratory premium. Its best case is +43 bp/yr of edge against 312 bp of tracking error, worth +21 bp of geometric growth and 6.6% more terminal wealth over thirty years; on the US-only post-publication premium the growth contribution is negative at every weight. The +15 bp/yr this page carried until 2026-08-17 multiplied an exposure by a capture fraction, which is the same quantity measured a second way.",
    sizingNote:
      "VBR's yield is higher than the market's, which raises its shelter priority above the 26.2 / 20.7 / 16.5 bp of plain US equity. By how much is not measured here. A small-value fund also carries an SMB exposure near +0.85 whose premium this repository tested and could not sign, so a large-value fund buys comparable HML exposure at roughly half the tracking error.",
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
      "An exploratory product on an unresolved index, with single-product risk: four of the five listed managed-futures ETFs fail the 0.50 exposure bar, so there is no fallback. Its 2.09 pp/yr distribution tax drag is 2.5× its own fee in a taxable account and zero in a shelter.",
    sizingNote:
      "Experiment 004 priced a 15% trend holding, not a 10% one. The cap is set below the tested weight because one product delivers the exposure and there is no fallback, not because 10% was measured to be better.",
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
    "The disciplines are worth more than the holdings. About 109 bp/yr against your own counterfactual, 99% confident in about twelve months, against a best case of 43.1 bp for a 20% small-value lean — 21 bp of it in geometric growth — and 90 bp for a sheltered trend holding.",
  source: recommendation,
  asOf: asOf("2026-08-17"),
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
      "No holding reached production-eligible, or walk-forward-tested, or even independently-reproduced. VBR and DBMF are exploratory products, which permits them to be used as implementation proxies in a later experiment and permits nothing else.",
  },
  {
    claim: "Not a claim of outperformance against an index",
    detail:
      "Against a cheap index the whole honest budget is about 5.4 bp against 313 bp of tracking error — a 0.538 probability of being ahead after thirty years, which is a coin flip.",
  },
  {
    claim: "Not net of everything",
    detail:
      "No page here has a full after-tax, after-spread, after-turnover return for any product. Bid-ask, brokerage, realised distributions and portfolio turnover are absent from the product audit entirely.",
  },
  {
    claim: "Not free of model risk",
    detail:
      "FF5+UMD prices VTI itself at −0.55 pp/yr with a t of −3.41 on error bars widened for clustered, uneven returns, over 2020–2025. The standard model does not span the control, and every alpha here is a distance from that pedestal rather than from zero.",
  },
  {
    claim: "Not vintage-stable",
    detail:
      "Ken French rebuilds the whole history from the current vintage on every rebuild, and the Phase 1 gate is unresolved. HML's and RMW's standard deviations do not reproduce, leaving a systematic 3–5% band on anything that divides by them. Five series carry no measured band at all, which is weaker than a band of zero — including all three momentum files.",
  },
];
