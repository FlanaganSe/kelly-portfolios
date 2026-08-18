import type { AsOf, CertaintyClass, Citation, EvidenceStatus } from "~/content/types";
import { asOf } from "~/content/types";

/**
 * The portfolio candidates.
 *
 * Four constructions, ordered by how much of their case is contractual and how much is
 * a bet. They are not four risk levels. The first is the thing the other three have to
 * beat; the second changes no holding and is the only one whose edge is an accounting
 * identity; the third takes the two tilts this repository's evidence actually supports;
 * the fourth is a reader's proposal, priced honestly against the same shelf.
 *
 * Three rules govern every record here, all of them from
 * [decision 0006](docs/decisions/0006-reference-portfolio-without-promotion.md):
 *
 * 1. Every holding carries its evidence status and its certainty class. **A risk
 *    premium is never called an edge.**
 * 2. Every tilt is priced in confidence terms — edge, tracking error, and how long a
 *    holder would have to wait to know. A tilt quoted as `+X pp/yr` without its
 *    tracking error is not reportable.
 * 3. "Best-supported" means best-supported by this evidence. **Nothing here is
 *    promoted, and no portfolio on this page is claimed to beat an index.**
 */

/** What a line of a portfolio is actually buying. */
export type ReturnEngine = "equity-beta" | "value" | "momentum" | "trend" | "term-and-credit" | "cost-and-tax" | "cash";

export interface EngineMeta {
  readonly label: string;
  readonly gloss: string;
}

export const engineMeta = {
  "equity-beta": {
    label: "Equity risk premium",
    gloss: "Pay for owning the residual claim on corporate cash flows. The bulk of every portfolio here.",
  },
  value: {
    label: "Value",
    gloss:
      "A measured tilt toward cheap stocks. The only factor premium in this repository to advance on its own strength.",
  },
  momentum: {
    label: "Momentum",
    gloss: "Recent winners keep winning. The largest gross premium measured here, and the one implementation destroys.",
  },
  trend: {
    label: "Trend",
    gloss: "A long/short futures book that is near-uncorrelated with equity and negatively correlated inside crises.",
  },
  "term-and-credit": {
    label: "Term and credit",
    gloss: "Lending money for duration. Real pay for a real risk, measured against a different benchmark.",
  },
  "cost-and-tax": {
    label: "Cost and tax",
    gloss:
      "Fee, wrapper, lot method and account placement. Statutory and accounting facts whose sign is known in advance.",
  },
  cash: { label: "Cash", gloss: "Unallocated capital. Earns the bill rate and nothing else." },
} as const satisfies Readonly<Record<ReturnEngine, EngineMeta>>;

export interface PortfolioHolding {
  readonly ticker: string;
  /** Percent of capital. The lines must sum to exactly 100. */
  readonly percent: number;
  readonly engine: ReturnEngine;
  /** Why this line is here, in one sentence. */
  readonly why: string;
  readonly status: EvidenceStatus | null;
  readonly certainty: CertaintyClass;
}

/**
 * Notional exposure per $1 of capital. A capital-efficient fund's capital weight does
 * not describe its risk, and the repository refuses to compare a weight stated in
 * capital with one stated in notional.
 */
export interface NotionalLine {
  readonly label: string;
  /** Percent of portfolio capital, as notional. Can exceed the capital weight. */
  readonly percent: number;
  readonly note?: string;
}

/**
 * A priced line: edge, its dispersion, and how long before a holder could tell.
 *
 * `edgeBp` and `trackingErrorBp` are both nullable because some results are not of that
 * shape at all. A marginal *growth* contribution measured against a frozen bar has no
 * edge and no tracking error, and forcing one into those fields would relabel it as
 * something a reader could compare with a tilt. Decision 0006 still binds the other way:
 * a risk premium that does quote an edge must quote its dispersion beside it.
 */
export interface PricedLine {
  readonly label: string;
  readonly edgeBp: number | null;
  readonly trackingErrorBp: number | null;
  /** Geometric growth contribution where the owning page states one, bp/yr. */
  readonly growthBp: number | null;
  readonly horizonNote: string;
  readonly certainty: CertaintyClass;
  readonly status: EvidenceStatus | null;
  readonly source: Citation;
}

export interface FailureMode {
  readonly title: string;
  readonly detail: string;
}

export type Complexity = "low" | "moderate" | "high";

/** A concrete change to the construction, and the measured reason for it. */
export interface SuggestedChange {
  readonly change: string;
  readonly because: string;
}

export interface PortfolioCandidate {
  readonly id: string;
  readonly name: string;
  /** The thesis, in one sentence. No hedging and no marketing. */
  readonly thesis: string;
  /** Who this is the answer for. */
  readonly forWhom: string;
  readonly holdings: readonly PortfolioHolding[];
  /** Notional exposure, where it differs from capital. Empty when the two agree. */
  readonly notional: readonly NotionalLine[];
  /** Total notional as a percent of capital. 100 for an unlevered portfolio. */
  readonly grossExposurePercent: number;
  readonly benchmark: {
    readonly label: string;
    readonly why: string;
  };
  readonly priced: readonly PricedLine[];
  readonly mayOutperform: readonly string[];
  readonly mayUnderperform: readonly string[];
  readonly failureModes: readonly FailureMode[];
  readonly trackingErrorCharacter: string;
  readonly complexity: Complexity;
  readonly tax: string;
  readonly rebalancing: string;
  readonly placement: string;
  /** The honest one-paragraph summary of how much of this is evidence. */
  readonly evidenceSummary: string;
  /** Where this construction is editorial rather than measured. Never empty. */
  readonly editorialNote: string;
  /**
   * What this evidence would change about the construction, stated as specific swaps
   * rather than as a general warning. Editorial, and marked as such on the page.
   */
  readonly suggestedChanges?: readonly SuggestedChange[];
  readonly benchmarkTicker: string;
  readonly sources: readonly Citation[];
  readonly asOf: AsOf;
}

const recommendation: Citation = {
  label: "The recommended portfolio",
  docPath: "docs/research/portfolio-recommendation.md",
};
const decomposition: Citation = {
  label: "Where outperformance can come from",
  docPath: "docs/research/expected-edge-decomposition.md",
};
const structural: Citation = {
  label: "Structural and tax edges",
  docPath: "docs/research/structural-and-tax-edges.md",
};
const capital: Citation = {
  label: "Capital efficiency and breadth",
  docPath: "docs/research/capital-efficiency-and-breadth.md",
};
const products: Citation = { label: "The factor-product audit", docPath: "docs/research/factor-products.md" };
const trendValue: Citation = { label: "The marginal value of trend", docPath: "docs/research/trend-marginal-value.md" };
const persistence: Citation = { label: "Factor persistence", docPath: "docs/research/factor-persistence.md" };
const noSleeve: Citation = {
  label: "Decision 0004 — no sleeve promoted",
  docPath: "docs/decisions/0004-no-sleeve-promoted.md",
};

const READ = asOf("2026-08-17");

// ---------------------------------------------------------------------------

const control: PortfolioCandidate = {
  id: "control",
  name: "The control",
  thesis: "Own every listed company in the world at its market weight, for about half a basis point a year.",
  forWhom: "Everyone, as the starting position. Every other portfolio on this site has to beat this one.",
  holdings: [
    {
      ticker: "VTI",
      percent: 60,
      engine: "equity-beta",
      why: "The whole US market at 1.16 bp net of securities lending, with zero capital-gain distributions across 44 fund-years.",
      status: null,
      certainty: "nothing-better-exists",
    },
    {
      ticker: "VEA",
      percent: 30,
      engine: "equity-beta",
      why: "Developed markets outside the US at a net cost of −0.30 bp: lending more than covers the fee.",
      status: null,
      certainty: "nothing-better-exists",
    },
    {
      ticker: "IEMG",
      percent: 10,
      engine: "equity-beta",
      why: "Emerging markets at −0.87 bp net, under a fee cap running to 2030 with no recoupment — the most durable fee commitment on the shelf.",
      status: null,
      certainty: "nothing-better-exists",
    },
  ],
  notional: [],
  grossExposurePercent: 100,
  benchmark: {
    label: "A cheap global index fund",
    why: "The control is the benchmark. Its purpose is to be the thing that has to be beaten, not to beat anything.",
  },
  priced: [],
  mayOutperform: [
    "It does not have to. Ninety-six of the 109 US factor loadings audited here survive multiple-comparison correction; five of 327 alpha tests do, and all five are negative. Exposure is measurable and skill is not.",
    "Its cost, net of securities lending, is about 0.52 bp a year, against 0.76 bp for the cheapest combination on the shelf and 3.12 for the dearest plausible one. The whole fund-selection decision inside this construction is worth 0.60 bp/yr, against an 84 bp/yr hurdle for the turnover needed to capture it.",
  ],
  mayUnderperform: [
    "It will track the market down as well as up. The US market lost 50.3% over the modern sample and 83.7% over the full hundred-year record.",
    "The 60/30/10 regional split is a declared research weight frozen before results were examined. It is not a market weight and no experiment here signed it.",
  ],
  failureModes: [
    {
      title: "The equity premium is not a promise",
      detail:
        "Across sixteen countries of annual real returns the US ranks 16th of 16 from 1963. The median market lost about three quarters of its real value at some point. Nothing in this repository forecasts any market's return.",
    },
    {
      title: "The regional split is asserted",
      detail:
        "A US 45 / international 35 proposal is a 56:44 split against this 60:40 of equity, and no page here can distinguish them. Choose one and stop.",
    },
  ],
  trackingErrorCharacter:
    "Zero against itself, by construction. Against any other global index fund the difference is a few basis points of fee and index-construction noise.",
  complexity: "low",
  tax: "All three funds distributed zero capital gains in every fiscal year on file. The foreign tax credit on VEA is worth 15.78 bp/yr and only in a taxable account.",
  rebalancing:
    "Annually or on a 25% relative band. Rebalancing is `rejected` here as a source of return — it measured −38.7 bp/yr — and retained as risk control, which is what the 0.3–1.2 bp/yr buys.",
  placement:
    "Bonds first if you hold any, then developed ex-US, then US, then emerging — but the order between developed and emerging inverts between two live US dividend rates, so compute it rather than asserting it.",
  evidenceSummary:
    "Nothing here is a bet on a premium beyond the equity premium itself. Its costs are contractual and measured across 25 funds and 110 regulatory filings.",
  editorialNote:
    "The 60/30/10 regional split is a research weight, not a measured optimum and not a market weight. This repository holds no global capitalisation series and cannot tell you the market weight.",
  benchmarkTicker: "VT",
  sources: [recommendation, structural],
  asOf: READ,
};

const disciplined: PortfolioCandidate = {
  id: "disciplined",
  name: "The control, held properly",
  thesis:
    "The same three funds, with the fee, wrapper, lot method and account placement decided deliberately — about 109 bp a year against the portfolio most readers already own, and roughly 99% confident inside a year.",
  forWhom:
    "A reader holding an expensive active fund, in the wrong account, with average-cost lots. For a reader already in cheap index funds in one tax-deferred account, the honest figure is close to zero.",
  holdings: control.holdings,
  notional: [],
  grossExposurePercent: 100,
  benchmark: {
    label: "The portfolio you would otherwise have owned",
    why: "This is a different benchmark from an index, and the two may never be added. Against a cheap index the same discipline is worth about 46 bp against 313 bp of tracking error.",
  },
  priced: [
    {
      label: "Fund cost reduction",
      edgeBp: 49,
      trackingErrorBp: 0,
      growthBp: null,
      horizonNote:
        "The only unconditional line. It needs nothing to be true but that you currently hold an expensive fund.",
      certainty: "contractual",
      status: null,
      source: decomposition,
    },
    {
      label: "Tax-loss harvesting, gross of its own fee",
      edgeBp: 30,
      trackingErrorBp: 0,
      growthBp: null,
      horizonNote:
        "0–90 bp. Net of a 9 bp direct-indexing fee it is 25.6 bp, and it needs a taxable account with gains to offset.",
      certainty: "contractual",
      status: null,
      source: structural,
    },
    {
      label: "ETF rather than active mutual-fund wrapper",
      edgeBp: 23,
      trackingErrorBp: 0,
      growthBp: null,
      horizonNote:
        "0–49 bp, and decaying: 94 SEC orders and 89 filings now name an ETF share class, against two before the first order.",
      certainty: "contractual",
      status: null,
      source: structural,
    },
    {
      label: "Asset location",
      edgeBp: 10,
      trackingErrorBp: 0,
      growthBp: null,
      horizonNote: "0–21 bp, and it needs more than one account type to exist at all.",
      certainty: "contractual",
      status: null,
      source: decomposition,
    },
    {
      label: "Specific identification of lots",
      edgeBp: 5,
      trackingErrorBp: 0,
      growthBp: null,
      horizonNote: "0–44 bp. A brokerage setting, changed once.",
      certainty: "contractual",
      status: null,
      source: structural,
    },
    {
      label: "Foreign tax credit forfeited inside a shelter",
      edgeBp: -3.4,
      trackingErrorBp: 0,
      growthBp: null,
      horizonNote:
        "−6 to 0 bp. A correction rather than a line: sheltering a foreign fund pays the withholding and permanently loses the credit.",
      certainty: "contractual",
      status: null,
      source: structural,
    },
    {
      label: "Direct-indexing fee, netted against harvesting",
      edgeBp: -4.4,
      trackingErrorBp: 0,
      growthBp: null,
      horizonNote: "−30 to +6 bp. The fee the harvesting line above never subtracted.",
      certainty: "contractual",
      status: null,
      source: structural,
    },
    {
      label: "The whole budget, against your own counterfactual",
      edgeBp: 109,
      trackingErrorBp: 46,
      growthBp: null,
      horizonNote:
        "The five positive lines sum to 117 and the two corrections bring it to 109.2. About 3.5 months to 90% confidence and about twelve to 99% — but the 46 bp tracking error is assumed rather than measured, and the components are not independent.",
      certainty: "contractual",
      status: null,
      source: structural,
    },
    {
      label: "The same discipline, against a cheap index",
      edgeBp: 46,
      trackingErrorBp: 313,
      growthBp: null,
      horizonNote:
        "P(ahead at 30 years) = 0.792; 0.681 at ten years; about 74 years to 90% confidence. This is an upper bound on an upper bound.",
      certainty: "risk-premium",
      status: null,
      source: decomposition,
    },
  ],
  mayOutperform: [
    "Every line is an accounting or statutory fact rather than a forecast: §852(b)(6) in-kind redemption, §853 credit pass-through, specific-lot identification, and the ordering of accounts.",
    "The confidence horizon is short. At 46 bp of tracking error a 109 bp edge is about 99% established inside a year, which is not true of any bet on a premium.",
  ],
  mayUnderperform: [
    "Every line but the 49 bp fee reduction is conditional. Some readers have none of the conditions.",
    "Against a cheap index rather than your own past behaviour, the same work is 46 bp against 313 bp of tracking error, and 30 years is not long enough to demonstrate it.",
  ],
  failureModes: [
    {
      title: "The wrapper line is decaying",
      detail:
        "The ETF-versus-mutual-fund advantage rests on active managers not having an ETF share class. Fourteen registrants now do. The line is +23 bp today and its mechanism is visibly closing.",
    },
    {
      title: "The tracking error is assumed",
      detail:
        "46 bp was assumed, not measured, and the components are not independent. Every confidence horizon on this page inherits that assumption.",
    },
    {
      title: "Turnover destroys it",
      detail:
        "In a taxable account there is a horizon-free 162 bp/yr hurdle on realising gains, 84 bp at thirty years. Realising even 10% of standing gain a year already costs 41.5 bp of the 84.",
    },
  ],
  trackingErrorCharacter:
    "Essentially none against the control. This portfolio holds the same three funds; what changes is which account each sits in, how lots are identified, and what wrapper the money left behind.",
  complexity: "low",
  tax: "This is the tax portfolio. The emerging-market withholding input, 9.853%, is below ten of eleven funds' filed rates, and correcting it would move the placement ranking rather than the size of the prize.",
  rebalancing: control.rebalancing,
  placement:
    "Bonds dominate the shelter by more than four to one at every rate. Between developed and emerging the ranking inverts at a 21.51% qualified dividend rate, which sits between two live US brackets — so the ordering has to be computed for your own bracket rather than asserted.",
  evidenceSummary:
    "The largest reliably available result in this repository, and the only one whose sign is known before the fact. It is also the one most often quoted at the wrong size: it is measured against your own counterfactual, never against an index.",
  editorialNote:
    "The 109 bp is a per-reader figure sized for one stated reference investor. Quoting a per-sleeve number as a portfolio number is how tax figures get inflated.",
  benchmarkTicker: "VT",
  sources: [structural, decomposition],
  asOf: READ,
};

const evidenceLed: PortfolioCandidate = {
  id: "evidence-led",
  name: "The evidence-led tilt",
  thesis:
    "The control plus the only two tilts this repository has priced whose case survives its own comparators — US large value and developed ex-US large value — at exactly the weights they were priced at.",
  forWhom:
    "A reader who wants a factor tilt and wants it sized by what was measured rather than by conviction. It accepts decades of tracking error for tens of basis points of expected edge.",
  holdings: [
    {
      ticker: "VTI",
      percent: 40,
      engine: "equity-beta",
      why: "The US core, reduced to make room for the value tilt rather than levered against it.",
      status: null,
      certainty: "nothing-better-exists",
    },
    {
      ticker: "AVLV",
      percent: 20,
      engine: "value",
      why: "HML +0.322 [+0.22, +0.46] over 51 months on the US panel, against VTI's +0.0247, at 15 bp and 7%/yr turnover. Less value exposure than a small-value fund and under half the tracking error — and none of its SMB loading, which is variance this repository cannot price.",
      status: "exploratory",
      certainty: "risk-premium",
    },
    {
      ticker: "VEA",
      percent: 22,
      engine: "equity-beta",
      why: "The developed ex-US core, at a negative net cost.",
      status: null,
      certainty: "nothing-better-exists",
    },
    {
      ticker: "DFIV",
      percent: 8,
      engine: "value",
      why: "HML +0.662 [+0.53, +0.85] over 51 months on the developed ex-US panel — the deepest on the audited ex-US shelf, on the one panel where the value premium is signable. The priced line below uses the +0.698 measured over the 45 months common to the shelf.",
      status: "exploratory",
      certainty: "risk-premium",
    },
    {
      ticker: "IEMG",
      percent: 10,
      engine: "equity-beta",
      why: "Emerging beta at −0.87 bp net. No emerging value product on this shelf reaches `exploratory`, so the region with the largest measured premium is held plain.",
      status: null,
      certainty: "nothing-better-exists",
    },
  ],
  notional: [],
  grossExposurePercent: 100,
  benchmark: {
    label: "The control",
    why: "The tilts are substitutions inside the same regional split, so the honest comparison holds the split fixed and changes only the funds.",
  },
  priced: [
    {
      label: "US large value at 20% of portfolio",
      edgeBp: 24.4,
      trackingErrorBp: 135,
      growthBp: 24.9,
      horizonNote:
        "Wealth multiple 1.078 over thirty years; 90% confidence at about fifty. The certainty equivalent at γ=3 is +26.0 bp.",
      certainty: "risk-premium",
      status: "exploratory",
      source: recommendation,
    },
    {
      label: "Developed ex-US large value at 8% of portfolio",
      edgeBp: 27.1,
      trackingErrorBp: 47.6,
      growthBp: 29.5,
      horizonNote:
        "The only tilt in this repository whose 30-year detection floor, 21.6 bp, sits below its own edge. Growth per unit of tracking error 0.620, the best of the five priced.",
      certainty: "risk-premium",
      status: "exploratory",
      source: recommendation,
    },
  ],
  mayOutperform: [
    "Both tilts buy a factor whose pooled premium is `exploratory` at +4.74 pp/yr [+1.46, +8.10] against a 3.35 pp/yr detection floor, positive in all three regions and surviving multiple-comparison correction.",
    "Both funds deliver the exposure they advertise. Their loadings survive Benjamini–Hochberg correction and keep their status under every comparator basis tested.",
    "Large value rather than small value is a measured choice, not a compromise: a small-value fund's size leg is variance with no priced expectation, since the size premium is +0.33 pp/yr against a 2.47 pp/yr floor and is not signable on any panel.",
  ],
  mayUnderperform: [
    "The US value premium on its own panel is +1.57 pp/yr [−2.28, +5.54] against a 5.03 pp/yr detection floor, and is not signable. Only the pooled three-region figure makes the AVLV line's growth contribution positive.",
    "DFIV's own alpha is −4.11 pp/yr against a 3.52 pp/yr detection floor. Charge it and the 8% tilt goes from +27.1 bp to −8.2 bp. Four ex-US large-value funds read −2.2 to −4.1 and nobody here knows why.",
    "Every fund window on this shelf is shorter than one value cycle. Whether 36 to 72 months of loading forecasts the next 36 to 72 is an open question nothing here tests.",
  ],
  failureModes: [
    {
      title: "The premium is gross, long-short and unimplementable",
      detail:
        "+4.74 pp/yr is a Ken French long-short spread with no costs and no shorting constraint. A long-only fund receives weight × (fund loading − incumbent loading) × premium, less cost — three terms. Multiplying by a further capture fraction is banned in this repository's code, and doing it understated the tilt by about half in five places.",
    },
    {
      title: "Thirty years may not settle it",
      detail:
        "Scaled to AVLV's 135 bp of tracking error, the thirty-year detection floor at a 20% weight is about 61 bp against its +24.4 bp edge. The small-value alternative is worse: 142 bp against 43. Either way you would hold the tilt for a working lifetime and still not know whether it worked.",
    },
    {
      title: "The alpha problem is unexplained",
      detail:
        "Five of 327 alpha tests survive Holm correction on this shelf and all five are negative. On the alpha-charged reading of the ex-US shelf the answer is IVLU, not DFIV.",
    },
  ],
  trackingErrorCharacter:
    "About 135 bp on the US leg and 48 bp on the ex-US leg. Long stretches behind the control are the normal behaviour of this portfolio, not evidence against it.",
  complexity: "moderate",
  tax: "Both tilt funds are low-turnover — 7%/yr and 6%/yr — which matters more than the fee difference given the 162 bp/yr horizon-free hurdle on realised gains. Neither has ever distributed a capital gain in the years on file.",
  rebalancing:
    "Annually, or on bands. Do not rebalance to harvest a bonus — there is none. Every rebalanced policy tested here had an equal or worse maximum drawdown than buy-and-hold.",
  placement:
    "Same ordering as the control. The tilt funds are US and developed ex-US, so neither changes the shelter ranking.",
  evidenceSummary:
    "Two `exploratory` tilts, which is the highest status anything in this repository has reached. `exploratory` means a product may stand in for a real one in a later experiment. It does not mean the tilt works.",
  editorialNote:
    "This construction is editorial. The repository's own reference portfolio holds no tilt at all — decision 0004 promotes no sleeve — and the weights here are the weights at which each tilt was priced, chosen so that its published edge and tracking error can be quoted without rescaling.",
  benchmarkTicker: "VT",
  sources: [recommendation, products, persistence, noSleeve],
  asOf: READ,
};

const candidate: PortfolioCandidate = {
  id: "candidate",
  name: "The stacked candidate",
  thesis:
    "A capital-efficient sleeve carries a trend overlay alongside a full equity allocation, with value and momentum tilts across both regions — about 132% of gross exposure for 100% of capital.",
  forWhom:
    "A reader who has decided that diversifying the return engine matters more than keeping the construction simple, and who can hold an unfamiliar drawdown pattern without selling it.",
  holdings: [
    {
      ticker: "RSST",
      percent: 30,
      engine: "trend",
      why: "107.2% equity plus roughly 100% managed-futures notional per dollar, at delta −0.07 — the sleeve keeps essentially all of the funding advantage a standalone trend fund gives away.",
      status: null,
      certainty: "risk-premium",
    },
    {
      ticker: "VTI",
      percent: 20,
      engine: "equity-beta",
      why: "The US core.",
      status: null,
      certainty: "nothing-better-exists",
    },
    {
      ticker: "AVLV",
      percent: 15,
      engine: "value",
      why: "The US value tilt, at three quarters of the weight it was priced at.",
      status: "exploratory",
      certainty: "risk-premium",
    },
    {
      ticker: "DFIV",
      percent: 10,
      engine: "value",
      why: "The developed ex-US value tilt, at 1.25× the weight it was priced at.",
      status: "exploratory",
      certainty: "risk-premium",
    },
    {
      ticker: "VEA",
      percent: 10,
      engine: "equity-beta",
      why: "The developed ex-US core.",
      status: null,
      certainty: "nothing-better-exists",
    },
    {
      ticker: "IDMO",
      percent: 5,
      engine: "momentum",
      why: "UMD +0.540 [+0.39, +0.71] over 77 months on the developed ex-US panel, the one momentum premium that clears its own detection floor.",
      status: "exploratory",
      certainty: "risk-premium",
    },
    {
      ticker: "IEMG",
      percent: 5,
      engine: "equity-beta",
      why: "Emerging beta at −0.87 bp net.",
      status: null,
      certainty: "nothing-better-exists",
    },
    {
      ticker: "AVES",
      percent: 5,
      engine: "value",
      why: "The emerging value tilt, into the region with the largest measured HML premium: +7.58 pp/yr [+4.34, +11.01]. AVES's own HML reads +0.237 on the emerging panel and −0.074 on the US one.",
      status: "unresolved",
      certainty: "risk-premium",
    },
  ],
  notional: [
    { label: "US equity", percent: 67.2, note: "20 VTI + 15 AVLV + 32.2 from RSST's 107.2% equity leg." },
    { label: "Developed ex-US equity", percent: 25 },
    { label: "Emerging equity", percent: 10 },
    {
      label: "Managed futures",
      percent: 30,
      note: "RSST's trend leg, roughly 100% of notional per dollar of capital.",
    },
  ],
  grossExposurePercent: 132,
  benchmark: {
    label: "A leverage-matched control, not the unlevered index",
    why: "At 132% of gross exposure the honest comparison is against the same equity risk taken directly. Comparing a levered portfolio with an unlevered index credits the leverage to the strategy.",
  },
  priced: [
    {
      label: "US large value at 20% (the weight it was priced at)",
      edgeBp: 24.4,
      trackingErrorBp: 135,
      growthBp: 24.9,
      horizonNote: "Quoted at 20%. This portfolio holds 15%, and the repository publishes no figure at that weight.",
      certainty: "risk-premium",
      status: "exploratory",
      source: recommendation,
    },
    {
      label: "Developed ex-US large value at 8% (the weight it was priced at)",
      edgeBp: 27.1,
      trackingErrorBp: 47.6,
      growthBp: 29.5,
      horizonNote:
        "Quoted at 8%. This portfolio holds 10%, and its own alpha of −4.11 pp/yr would take the priced line negative.",
      certainty: "risk-premium",
      status: "exploratory",
      source: recommendation,
    },
    {
      label: "A 10% trend sleeve against a global equity core",
      edgeBp: null,
      trackingErrorBp: null,
      growthBp: 25.8,
      horizonNote:
        "Quoted at the 10% reference weight Experiment 010 used. This portfolio carries about 30% of trend notional, the repository publishes no figure at that weight, and its own search-coverage audit records that this closure turns on the reference weight rather than on evidence. The certainty equivalent at γ=3 for the same row is +1.172 pp/yr, and decision 0008 says growth decides when the two disagree. A different experiment, measuring the vendor index at a 15% weight against a risk-matched cash comparator rather than an equity core, reads +1.312 — a different question, and not a figure that may be carried back to this line.",
      certainty: "risk-premium",
      status: "rejected",
      source: capital,
    },
  ],
  mayOutperform: [
    "The funding rule is worth more than any sleeve. Financing a diversifier as notional rather than selling equity to buy it is worth about +2.44 pp/yr for a 100% equity base, and that figure contains nothing at all about trend. RSST's delta of −0.07 keeps essentially all of it; a standalone managed-futures fund keeps none.",
    "Trend's correlation to equity is negative when it matters. Three independent instruments agree: −0.07 built here, −0.11 across 46 live funds, −0.08 from the vendor index, and −0.59 inside crisis months with a downside beta of −0.67.",
    "It buys four engines rather than one, and the two value tilts inside it are the same ones the evidence-led portfolio holds.",
  ],
  mayUnderperform: [
    "Three of its eight lines have no measured factor exposure of any kind. RSST's loading on any trend benchmark has never been measured here — the statement appears three separate times in the research.",
    "Trend's mean does not resolve. Post-publication the sleeve measures +0.883 pp/yr with an interval containing zero, failing Holm correction, and the standalone index's Sharpe fell from 1.34 to 0.18 across three eras.",
    "Momentum is excluded by this repository's own audit. IDMO files 105%/yr of turnover, which takes 43% of the gross exposure in cost, and momentum's pooled detection floor of 4.98 pp/yr is the worst measured here.",
    "AVES is `unresolved`, and no comparator however expressive can move an emerging-market value product to `exploratory` on the windows available.",
  ],
  failureModes: [
    {
      title: "The cost stack binds before the correlation does",
      detail:
        "Financing plus fee plus distribution-tax character runs about 1.4 pp/yr sheltered and about 3.5 pp/yr taxable, against a post-publication trend excess return of roughly 1.8 pp/yr. No wrapper on this shelf quantifies its financing cost anywhere, and the family's only disclosed rate, OBFR + 6.64%, more than doubled in a single quarter.",
    },
    {
      title: "The overlay is the deeper drawdown above a weight this portfolio is near",
      detail:
        "The resampled probability that the overlay is the deeper drawdown is 6.9% at 30% of notional, and then doubles from 10.8% to 18.9% between 58% and 60%. That is a cliff rather than a ramp, and it is why the implied ceiling is near 55%. This portfolio sits at 30%, clear of it — and the cliff is the reason the weight cannot simply be raised.",
    },
    {
      title: "Trend fails exactly when it is needed",
      detail:
        "The whole diversification case breaks if the correlation inside equity drawdowns reaches +0.20, and that conditional correlation is unmeasured going forward. A static plus volatility-scaled replica already delivers 44% of the benefit for none of the fee.",
    },
    {
      title: "The funds may not survive",
      detail:
        "52% of the managed-futures ETFs listed in 2019 were gone by the end of 2025 — a 10.7%/yr hazard, 43% at five years. RSST itself is under three years old and its 28-month tax window is entirely a rising market.",
    },
    {
      title: "The three stacked wrappers are not interchangeable",
      detail:
        "RSST, MATE and JPFP look like the same product and are not. RSST costs 99 bp, has 35 months of record and publishes an explicit dollar-for-dollar target. MATE costs 97 bp, has eight months, quotes its Other Expenses as estimates, and is the only one whose prospectus states §1256 mark-to-market outright — 60/40 treatment with unrealised gains recognised at year end, which is phantom income in a taxable account and the opposite of the deferral the wrapper case elsewhere rests on. JPFP costs 59 bp, which would change the ranking, and has two months of record and $17.07m of assets. All three run a Cayman subsidiary capped at 25% of assets, and this repository has measured a trend loading for none of them.",
    },
    {
      title: "It is levered, and this repository does not permit that",
      detail:
        "Decision 0004 holds leverage at zero and is unsuperseded. This portfolio runs about 132% of gross exposure. That is a deliberate departure from the research, not a conclusion of it.",
    },
  ],
  trackingErrorCharacter:
    "Large and unfamiliar. The trend leg will be flat or negative through a strong equity year and is expected to earn its keep in the years the equity leg loses. There is no published tracking-error figure for this construction because no experiment here has ever tested a portfolio like it.",
  complexity: "high",
  tax: "RSST's distribution drag is 0.32 pp/yr — 4.5 bp incremental once the VTI it displaces is subtracted, or 1.3 bp of portfolio return at a 30% weight. That is small. DBMF's equivalent is 143.9 bp, which is the comparison worth carrying: the wrapper, not the strategy, decides the tax outcome.",
  rebalancing:
    "The trend leg's weight is stated in notional, and the equity legs' in capital. Those units are not comparable and must never be rebalanced against each other as though they were.",
  placement:
    "The obvious rule — shelter the highest tax drag — is exactly backwards here. It puts DBMF and GDE at the front and RSST near the back, when RSST is the one whose marginal contribution clears its own detection floor and the one that needs the shelter least.",
  evidenceSummary:
    "Two lines are `exploratory`, one is `unresolved`, one is `rejected` on the repository's own bar, and the largest holding has never been measured at all. The construction's case rests on a funding identity that is closed-form and solid, applied to a sleeve whose return this evidence cannot sign.",
  suggestedChanges: [
    {
      change: "Drop IDMO and put the 5% back into VEA.",
      because:
        "Momentum's pooled detection floor is 4.98 pp/yr, the worst measured here, its three regions are worth 1.33 effective regions and all three lost their worst calendar year in 2009. IDMO turns over 105% a year, which takes 43% of the gross exposure in cost. This repository's product audit excludes it by name.",
    },
    {
      change: "Drop AVES and hold the emerging sleeve plain in IEMG.",
      because:
        "AVES is `unresolved` on window length, and no comparator however expressive can move an emerging-market value product to `exploratory` on the windows available. The emerging HML premium is the largest measured anywhere here, at +7.58 pp/yr, and there is nothing audited to buy it with.",
    },
    {
      change: "Take the 30% wrapper line to RSST specifically, or leave it out.",
      because:
        "Of the three, only RSST has a verified structure, a published dollar-for-dollar target, a computed delta of −0.07 and a measured tax drag. MATE has eight months, estimated expenses, no delta, and states §1256 mark-to-market outright — phantom income in a taxable account. JPFP has two months and $17.07m. None of the three has a measured trend loading.",
    },
    {
      change: "Move AVLV to 20% and DFIV to 8%, the weights they were priced at.",
      because:
        "Those are the only two weights at which this repository publishes an edge, a tracking error and a growth contribution. At any other weight the figures have to be recomputed, which the lab will do — but the published line is the one that has been checked.",
    },
    {
      change: "Decide the equity-versus-bond split before any of the above.",
      because:
        "Moving 60/40 to 90/10 is worth about +127 bp a year against 485 bp of tracking error — larger than every tilt on this page combined. This portfolio holds no bonds at all, which is a position rather than an oversight, and it should be a deliberate one.",
    },
  ],
  editorialNote:
    "This is a reader's proposal, priced against the same shelf as everything else here. It departs from this repository's research in three specific ways: it is levered, it holds a momentum fund the product audit excludes, and it holds an emerging value fund that is `unresolved`. Those are stated, not hidden.",
  benchmarkTicker: "VT",
  sources: [capital, trendValue, recommendation, noSleeve],
  asOf: READ,
};

export const portfolios: readonly PortfolioCandidate[] = [control, disciplined, evidenceLed, candidate];

export function portfolioById(id: string): PortfolioCandidate | undefined {
  return portfolios.find((one) => one.id === id);
}

/** Total capital weight. Every portfolio here must sum to exactly 100. */
export function totalWeight(portfolio: PortfolioCandidate): number {
  return Math.round(portfolio.holdings.reduce((sum, one) => sum + one.percent, 0) * 100) / 100;
}

/** Capital weight by return engine, in the engine order declared above. */
export function weightByEngine(portfolio: PortfolioCandidate): { engine: ReturnEngine; percent: number }[] {
  const totals = new Map<ReturnEngine, number>();
  for (const holding of portfolio.holdings) {
    totals.set(holding.engine, (totals.get(holding.engine) ?? 0) + holding.percent);
  }
  return (Object.keys(engineMeta) as ReturnEngine[])
    .filter((engine) => totals.has(engine))
    .map((engine) => ({ engine, percent: Math.round((totals.get(engine) ?? 0) * 100) / 100 }));
}

export const portfoliosAsOf = READ;
