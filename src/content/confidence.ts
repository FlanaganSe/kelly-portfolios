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
    edgeBp: 5.4,
    trackingErrorBp: 313,
    benchmark: "stated index",
    probability10yr: 0.522,
    probability30yr: 0.538,
    ninetyPercentAt: "far beyond any horizon worth stating",
    note: "This is a coin flip, and saying so is the finding. The budget carries two probabilistic lines against a cheap index — a value tilt at +43.1 bp and a rebalancing line measured at −38.7 bp over 420 months — and they very nearly cancel. The range runs from −91.6 to +82.9, so the sign is not robust. Against this benchmark the repository can demonstrate nothing; what it can demonstrate is the contractual budget above, against the portfolio you would otherwise have owned.",
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
 * A small-value tilt via AVUV. Nine corners: three premia by three weights.
 *
 * The chain is `weight × (fund loading − VTI's loading) × premium − weight × cost` and
 * carries NO capture term. A capture fraction is itself an HML loading — 94% of the
 * size-neutral 0.520 is the loading 0.4891 — so the earlier
 * `weight × loading × capture × premium` discounted one exposure twice and understated
 * every figure here by roughly a factor of two.
 *
 * `growthBp` is the marginal contribution to geometric growth, which is the edge less
 * the variance the swap adds, and it is what decides; the certainty equivalent at
 * gamma = 3 reports beside it. Regenerated by `studies/value_tilt.py`.
 */
export const smallValueCorners: readonly {
  readonly id: string;
  readonly premiumUsed: string;
  readonly weight: number;
  readonly netEdgeBp: number;
  readonly trackingErrorBp: number;
  readonly growthBp: number;
  readonly certaintyEquivalentBp: number;
  readonly wealthMultiple30yr: number;
  readonly probability30yr: number;
  readonly ninetyPercentAt: string;
  readonly isDefensibleReading: boolean;
}[] = [
  {
    id: "pooled-10",
    premiumUsed: "Pooled +4.74 pp/yr",
    weight: 0.1,
    netEdgeBp: 21.6,
    trackingErrorBp: 156,
    growthBp: 11.9,
    certaintyEquivalentBp: -7.4,
    wealthMultiple30yr: 1.036,
    probability30yr: 0.776,
    ninetyPercentAt: "86 years",
    isDefensibleReading: false,
  },
  {
    id: "pooled-20",
    premiumUsed: "Pooled +4.74 pp/yr",
    weight: 0.2,
    netEdgeBp: 43.1,
    trackingErrorBp: 312,
    growthBp: 21.4,
    certaintyEquivalentBp: -22.0,
    wealthMultiple30yr: 1.066,
    probability30yr: 0.776,
    ninetyPercentAt: "86 years",
    isDefensibleReading: false,
  },
  {
    id: "pooled-30",
    premiumUsed: "Pooled +4.74 pp/yr",
    weight: 0.3,
    netEdgeBp: 64.7,
    trackingErrorBp: 468,
    growthBp: 28.5,
    certaintyEquivalentBp: -44.0,
    wealthMultiple30yr: 1.089,
    probability30yr: 0.776,
    ninetyPercentAt: "86 years",
    isDefensibleReading: false,
  },
  {
    id: "us-full-20",
    premiumUsed: "US full sample +3.45 pp/yr",
    weight: 0.2,
    netEdgeBp: 29.9,
    trackingErrorBp: 312,
    growthBp: 8.2,
    certaintyEquivalentBp: -35.3,
    wealthMultiple30yr: 1.025,
    probability30yr: 0.7,
    ninetyPercentAt: "178 years",
    isDefensibleReading: true,
  },
  {
    id: "us-post-pub-10",
    premiumUsed: "US post-publication +1.57 pp/yr",
    weight: 0.1,
    netEdgeBp: 5.3,
    trackingErrorBp: 156,
    growthBp: -4.3,
    certaintyEquivalentBp: -23.6,
    wealthMultiple30yr: 0.987,
    probability30yr: 0.574,
    ninetyPercentAt: "1,405 years",
    isDefensibleReading: true,
  },
  {
    id: "us-post-pub-20",
    premiumUsed: "US post-publication +1.57 pp/yr",
    weight: 0.2,
    netEdgeBp: 10.7,
    trackingErrorBp: 312,
    growthBp: -11.1,
    certaintyEquivalentBp: -54.5,
    wealthMultiple30yr: 0.967,
    probability30yr: 0.574,
    ninetyPercentAt: "1,405 years",
    isDefensibleReading: true,
  },
  {
    id: "us-post-pub-30",
    premiumUsed: "US post-publication +1.57 pp/yr",
    weight: 0.3,
    netEdgeBp: 16.0,
    trackingErrorBp: 468,
    growthBp: -20.2,
    certaintyEquivalentBp: -92.7,
    wealthMultiple30yr: 0.941,
    probability30yr: 0.574,
    ninetyPercentAt: "1,405 years",
    isDefensibleReading: true,
  },
];

export const smallValueReading = {
  headline: "The premium decides the sign, and the variance decides how much survives.",
  detail:
    "The probability of being ahead does not move with the weight, because edge and tracking error are both linear in it: weight sets the size of the bet, never its demonstrability. On the pooled premium a 20% tilt adds 43 bp of arithmetic edge and 21 bp of geometric growth — the difference is the portfolio variance the swap adds, which no chain of the form premium × loading − cost can see. On the US-only post-publication premium the growth contribution is negative at every weight.",
  assumption:
    "Tracking error is now measured rather than assumed: AVUV against VTI over 2020-01…2025-12 reads 15.59 pp/yr, against the 7 pp/yr this page previously assumed. French's small-value research portfolio reads 16.47 pp/yr over the same months and 11.13 over 1963–2025, so the fund's window is high but not aberrant. On the 62-year moments the same 20% tilt gives 223 bp of tracking error and 36.9 bp of growth.",
  costAssumption:
    "Fee and turnover are read from each fund's own SEC filing and charged incrementally over VTI: AVUV 0.25% and 6%/yr against VTI's 0.03% and 3%/yr, giving 0.271 pp/yr. Experiment 007 assumed 20–40%/yr of sort turnover, which is four to eight times what the systematic funds actually file.",
  correction:
    "The +15.2 bp published here on 2026-08-12 is withdrawn. It multiplied VBR's HML loading by a long-only capture fraction, which is the same quantity measured a second way, and used a fund the corrected census frame has since superseded.",
  detectability:
    "A positive expected edge below its detection floor is still a positive expected edge. At a 20% weight the smallest edge thirty years could detect at 80% power is 142 bp, against the 43 bp best case.",
  source: recommendation,
} as const;

/** A 15%-of-portfolio managed-futures sleeve via DBMF. The wrapper is the largest controllable term. */
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
    label: "Post-publication, taxable (less 0.15 × 1.439)",
    netEdgeBp: 46,
    trackingErrorBp: 251,
    probability30yr: 0.842,
    ninetyPercentAt: "49 years",
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
  headline: "The wrapper, not the account, is the largest controllable term.",
  detail:
    "Moving DBMF into a shelter is worth 21.6 bp/yr of portfolio return once you subtract the distribution tax the equity it displaced was paying anyway. This row previously charged the full 2.09 pp/yr and said the account decides the sleeve's sign; that is a fact about DBMF and not about the exposure. The same trend notional through the return-stacked wrapper RSST carries 0.32 pp/yr gross and 4.5 bp incremental, so its account decides almost nothing — while the funding rule the wrapper sets moves the sleeve's hurdle by 2.44 pp/yr. Set that against the rest of the record: the index's standalone Sharpe fell 1.34 to 0.18 and its geometric return 19.4% to 3.1% after publication, the vendor states no cost basis anywhere in the archived workbook, comparable CTA survivorship and backfill distortion is 7.7 pp/yr — larger than the strategy's entire gross premium — and seven products' loadings have been measured on a shelf of fifteen, on seven different windows, which is why they are not rankable as published.",
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
    // "not trading" was in this label and is deliberately out of it. The ledger behind
    // 109 bp is 49 + 30 + 10 + 23 + 5 − 3.4 − 4.4 and contains no behaviour line; the gap
    // that would justify one is measured against the average investor, not against this
    // benchmark. See expected-edge-decomposition.md §2.4.
    label: "Fund cost, wrapper, lot method and placement",
    edgeBp: 109,
    trackingErrorBp: 46,
    ninetyNinePercentAt: "about twelve months",
  },
  {
    id: "small-value-best-case",
    label: "Best case for a 20% small-value tilt",
    edgeBp: 43.1,
    trackingErrorBp: 312,
    ninetyNinePercentAt: "about 283 years",
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
  thirtyYearsBp: 73,
  fiftyYearsBp: 57,
  confidence: "90%",
  reading:
    "No probabilistic line in this budget is demonstrable from an investor's own experience. Evidence has to come from somewhere other than a track record.",
  source: decomposition,
} as const;

export const confidenceAsOf = asOf("2026-08-17");
