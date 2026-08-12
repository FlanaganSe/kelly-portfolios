import { asOf, type Citation } from "~/content/types";

/**
 * The confidence horizon: how long it takes before an edge is demonstrable.
 *
 * Data only. The arithmetic belongs in `src/lib/`, not here.
 *
 * The one thing to carry through every rendering of this: every probability below
 * is an **upper bound**, because the machinery treats the edge as known. That
 * removes the dominant source of uncertainty.
 */

const recommendation: Citation = {
  label: "The recommended portfolio",
  docPath: "docs/research/portfolio-recommendation.md",
};

const decomposition: Citation = {
  label: "Where outperformance can come from",
  docPath: "docs/research/expected-edge-decomposition.md",
  anchor: "3-what-probability-is-actually-attainable",
};

export const formulas = {
  probability: "P(outperform) = Phi(e * sqrt(T) / s)",
  horizon: "T(confidence) = (z * s / e)^2",
  variables: "e is the annual edge, s the annual tracking error, T the horizon in years, Phi the standard normal CDF.",
  theLesson:
    "The horizon scales with the square of s/e, so tracking error rather than edge size decides whether a lifetime is enough. The same 50 bp edge reaches 90% confidence in 24 days against 10 bp of tracking error and in 105 years against 400 bp.",
  implementation: "research/src/portfolio_edge/studies/outperformance_horizon.py",
  source: decomposition,
} as const;

/** Print this beside every probability, without exception. */
export const upperBoundWarning =
  "Every probability here is an upper bound. The machinery treats the edge as known, which removes the dominant source of uncertainty. Returns are also assumed independent across years and lognormal, and none of that holds.";

export interface ConfidenceRow {
  readonly id: string;
  readonly label: string;
  /** Basis points a year. */
  readonly edgeBp: number;
  /** Basis points a year. */
  readonly trackingErrorBp: number;
  readonly benchmark: "own counterfactual" | "stated index" | "average investor" | "risk-matched comparator";
  readonly probability10yr?: number;
  readonly probability30yr?: number;
  readonly ninetyPercentAt?: string;
  readonly ninetyNinePercentAt?: string;
  readonly note?: string;
  readonly source: Citation;
}

/** The contractual line, and what it looks like against the two benchmarks it is not measured against. */
export const contractualRows: readonly ConfidenceRow[] = [
  {
    id: "contractual-109",
    label: "Cost, tax and placement, against your own counterfactual",
    edgeBp: 109,
    trackingErrorBp: 46,
    benchmark: "own counterfactual",
    probability10yr: 1.0,
    probability30yr: 1.0,
    ninetyPercentAt: "about 3.5 months",
    ninetyNinePercentAt: "about twelve months",
    note: "The probabilities are ~1.00 rather than exactly 1. This is the whole of the near-definite part, and none of it needs a view on any market.",
    source: recommendation,
  },
  {
    id: "contractual-89",
    label: "The same budget before the 2026 revision",
    edgeBp: 89,
    trackingErrorBp: 41,
    benchmark: "own counterfactual",
    probability10yr: 1.0,
    probability30yr: 1.0,
    ninetyPercentAt: "4.2 months",
    ninetyNinePercentAt: "13.8 months",
    note: "A fifth more edge bought about two months. Certainty is a property of the pairing, not of the edge's size.",
    source: recommendation,
  },
  {
    id: "vs-cheap-index",
    label: "The whole honest budget, against a cheap index",
    edgeBp: 24.4,
    trackingErrorBp: 401,
    benchmark: "stated index",
    probability10yr: 0.576,
    probability30yr: 0.631,
    ninetyPercentAt: "about 443 years",
    note: "Read this as an upper bound on an upper bound: its rebalancing line has since been measured negative on real data, and the factor line's sign turns on a benchmark choice the budget never states. The range around 24.4 bp runs from −30 to +101.",
    source: recommendation,
  },
  {
    id: "vs-average-investor",
    label: "Against the average investor",
    edgeBp: 15,
    trackingErrorBp: 150,
    benchmark: "average investor",
    probability10yr: 0.624,
    probability30yr: 0.708,
    ninetyPercentAt: "about 164 years",
    note: "The behaviour gap is real and roughly ten times smaller than the vendor headline. The peer-reviewed refutation puts poor timing at 0.10 pp/yr on the same sample. DALBAR must not be cited: its method compounds a dollar amount rather than computing an internal rate of return.",
    source: decomposition,
  },
];

/**
 * A 20%-of-portfolio small-value tilt via VBR. Four corners, and the table is the
 * whole case both for and against. Gross contribution is
 * `weight × loading × capture × premium`; cost is the assumed sort turnover plus a fee.
 */
export const smallValueCorners: readonly {
  readonly id: string;
  readonly premiumUsed: string;
  readonly sleeveCostPpYr: number;
  readonly netEdgeBp: number;
  readonly trackingErrorBp: number;
  readonly probability30yr: number;
  readonly ninetyPercentAt: string;
  readonly isDefensibleReading: boolean;
}[] = [
  {
    id: "pooled-low-cost",
    premiumUsed: "Pooled +4.74 pp/yr",
    sleeveCostPpYr: 0.25,
    netEdgeBp: 15.2,
    trackingErrorBp: 140,
    probability30yr: 0.724,
    ninetyPercentAt: "139 years",
    isDefensibleReading: false,
  },
  {
    id: "pooled-high-cost",
    premiumUsed: "Pooled +4.74 pp/yr",
    sleeveCostPpYr: 0.73,
    netEdgeBp: 5.6,
    trackingErrorBp: 140,
    probability30yr: 0.587,
    ninetyPercentAt: "1,026 years",
    isDefensibleReading: false,
  },
  {
    id: "us-only-low-cost",
    premiumUsed: "US-only +1.57 pp/yr",
    sleeveCostPpYr: 0.25,
    netEdgeBp: 1.8,
    trackingErrorBp: 140,
    probability30yr: 0.528,
    ninetyPercentAt: "about 10,000 years",
    isDefensibleReading: true,
  },
  {
    id: "us-only-high-cost",
    premiumUsed: "US-only +1.57 pp/yr",
    sleeveCostPpYr: 0.73,
    netEdgeBp: -7.8,
    trackingErrorBp: 140,
    probability30yr: 0.38,
    ninetyPercentAt: "never",
    isDefensibleReading: true,
  },
];

export const smallValueReading = {
  headline: "That table is the whole case, for and against.",
  detail:
    "The best corner requires believing a premium whose weight sits in the two regions where shorting is hardest and where no audited product exists here, and the worst corner is a persistent loss. At no corner is the tilt demonstrable from the investor's own experience.",
  assumption:
    "Tracking error is taken at 7 pp/yr for the sleeve, inside the 1.38–8.65 pp/yr range the product audit measured against a cheap combination — an assumption, since VBR's own tracking error is not published anywhere in this repository. The horizon column is proportionally sensitive to it; the sign is not.",
  costAssumption:
    "VBR's actual 5 bp fee is below the 15–25 bp the cost table assumes, giving a 0.25–0.73 pp/yr sleeve cost rather than 0.35–0.93.",
  source: recommendation,
} as const;

/** A 15%-of-portfolio managed-futures sleeve via DBMF. The account is the largest controllable term. */
export const managedFuturesCases: readonly {
  readonly id: string;
  readonly label: string;
  readonly netEdgeBp: number;
  readonly trackingErrorBp: number;
  readonly probability30yr: number;
  readonly ninetyPercentAt: string;
}[] = [
  {
    id: "post-pub-deferred",
    label: "Post-publication, tax-deferred (0.671 × 1.011)",
    netEdgeBp: 68,
    trackingErrorBp: 251,
    probability30yr: 0.931,
    ninetyPercentAt: "22 years",
  },
  {
    id: "post-pub-taxable",
    label: "Post-publication, taxable (less 0.15 × 2.09)",
    netEdgeBp: 37,
    trackingErrorBp: 251,
    probability30yr: 0.79,
    ninetyPercentAt: "76 years",
  },
  {
    id: "full-period-deferred",
    label: "Full period, tax-deferred (0.671 × 1.342)",
    netEdgeBp: 90,
    trackingErrorBp: 251,
    probability30yr: 0.975,
    ninetyPercentAt: "13 years",
  },
];

export const managedFuturesReading = {
  headline: "The account, not the product, is the largest controllable term.",
  detail:
    "Moving the sleeve into a shelter is worth 31 bp/yr of portfolio return, larger than the whole fee. Set that against the rest of the record: the index's standalone Sharpe fell 1.34 to 0.18 and its geometric return 19.4% to 3.1% after publication, the vendor states no cost basis anywhere in the archived workbook, comparable CTA survivorship and backfill distortion is 7.7 pp/yr — larger than the strategy's entire gross premium — and one product delivers the exposure with no fallback.",
  assumptions: [
    "That a trend sleeve's marginal certainty equivalent scales linearly in the product's loading on the index. 0.671 × 1.011 is an approximation; the experiment measured the index at a 15% weight, not DBMF at any weight. The product audit's own marginal-contribution arm is labelled invalid for every fund on warm-up grounds, so no direct measurement exists.",
    "A derived 2.52 pp/yr tracking error, computed from the published volatilities and correlation against the fully invested passive benchmark rather than the risk-matched comparator the experiment used as primary: sqrt(7.65² + 9.12² − 2 × 0.97 × 7.65 × 9.12).",
  ],
  source: recommendation,
} as const;

/** The comparison that decides the construction. */
export const decidingComparison: readonly {
  readonly id: string;
  readonly label: string;
  readonly edgeBp: number;
  readonly trackingErrorBp: number;
  readonly ninetyNinePercentAt: string;
}[] = [
  {
    id: "contractual",
    label: "Cost, placement, lot discipline, not trading",
    edgeBp: 109,
    trackingErrorBp: 46,
    ninetyNinePercentAt: "about twelve months",
  },
  {
    id: "small-value-best-case",
    label: "Best case for a 20% small-value tilt",
    edgeBp: 15.2,
    trackingErrorBp: 140,
    ninetyNinePercentAt: "about 460 years",
  },
  {
    id: "trend-best-case",
    label: "Best case for a 15% trend sleeve in a shelter",
    edgeBp: 90,
    trackingErrorBp: 251,
    ninetyNinePercentAt: "about 42 years",
  },
];

export const decidingComparisonReading =
  "A certain 109 bp is worth more than any tilt's gross premium, and it is available first. That is not a rhetorical preference; it is what the pairing of edge and tracking error produces.";

/** What thirty and fifty years can demonstrate at all, against 400 bp of tracking error. */
export const demonstrability = {
  thirtyYearsBp: 94,
  fiftyYearsBp: 72,
  confidence: "90%",
  reading:
    "No probabilistic line in this budget is demonstrable from an investor's own experience. Evidence has to come from somewhere other than a track record.",
  source: decomposition,
} as const;

export const confidenceAsOf = asOf("2026-08-12");
