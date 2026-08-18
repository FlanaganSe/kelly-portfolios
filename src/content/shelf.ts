import type { AsOf, Citation, EvidenceStatus } from "~/content/types";
import { asOf } from "~/content/types";

/**
 * The fund shelf: every product this repository has actually priced or regressed.
 *
 * This is the canonical record for a ticker. Three rules, all of them the reason the
 * file exists rather than a table inside a route:
 *
 * 1. **A loading names its panel.** The same fund reads +0.237 on the emerging panel
 *    and −0.074 on the US one, and a loading printed without its panel is a different
 *    number pretending to be the same one (`docs/research/factor-products.md`).
 * 2. **An alpha prints its pedestal and its detection floor.** The model misfits by
 *    −0.55 pp/yr on the US shelf before any fund is examined, and the median alpha this
 *    instrument could detect is about 5 pp/yr against roughly 1.25 pp/yr of true
 *    dispersion. An alpha without those two numbers reads as a finding when it is noise.
 * 3. **Cost is `fee − securities lending`.** The two rankings are different rankings.
 *
 * Where a field is `null`, no experiment in this repository read it. That is not an
 * invitation to fill it in from memory.
 */

export type ShelfCategory =
  | "us-core"
  | "us-value"
  | "us-small"
  | "us-momentum"
  | "us-quality"
  | "intl-core"
  | "intl-value"
  | "intl-small-value"
  | "intl-momentum"
  | "emerging-core"
  | "emerging-value"
  | "bonds"
  | "managed-futures"
  | "capital-efficient"
  | "alternative";

/** Which regression panel a loading was measured on. Never omitted. */
export type Panel = "us" | "developed-ex-us" | "emerging" | "aqr-tsmom";

export interface FactorLoading {
  readonly factor: "HML" | "SMB" | "RMW" | "CMA" | "UMD" | "TSMOM";
  readonly value: number;
  /** As printed by the owning page, e.g. `[+0.22, +0.46]`. `null` where none was given. */
  readonly interval: string | null;
  readonly panel: Panel;
  /** Months of data behind the estimate. Every window here is shorter than one cycle. */
  readonly months: number | null;
}

/**
 * What a stacked fund holds per dollar of capital, from its own filing.
 *
 * A wrapper's exposures do not fit `loadings`: they are positions read off an N-PORT, not
 * regression coefficients, and they must never be presented as evidence that the sleeve
 * inside the wrapper delivers anything. `notionalExposure` and `loadings` being separate
 * fields is how a route is stopped from printing "107% equity + 100% trend" where a
 * measured trend loading belongs.
 */
export interface NotionalExposure {
  readonly kind: "us-equity" | "global-equity" | "equity" | "treasury-futures" | "gold-futures" | "trend";
  /** Notional per $1 of capital, as a fraction. 1.072 means 107.2% of net assets. */
  readonly perDollarOfCapital: number;
}

/**
 * The wrapper arithmetic, which is a different quantity from a fee and a different
 * quantity from a loading.
 *
 * A wrapper may not be scored from its gross notional. The deciding number is
 * `delta = (1 − b) / d` — the base sold per unit of diversifier notional obtained — and
 * `1 − delta` is the share of the +2.44 pp/yr funding-rule gap the wrapper keeps
 * (`docs/research/capital-efficiency-and-breadth.md` §§1, 6a). None of these fields says
 * anything about the sleeve; that is the whole point of keeping them out of `loadings`.
 */
export interface WrapperFacts {
  /** `(1 − b) / d`. Negative means the wrapper sells no base at all. */
  readonly delta: number | null;
  /** `1 − delta` as a percentage: the share of the funding-rule gap retained. */
  readonly fundingCapturePercent: number | null;
  /** Management fee plus acquired-fund fees, basis points, from the fund's own fee table. */
  readonly allInCostBp: number | null;
  /** Gross notional per $1 of capital, from the filing named by `structureAsOf`. */
  readonly grossNotionalPerDollar: number | null;
  /** Distribution tax drag, pp/yr, from the fund's own SEC-standardised after-tax table. */
  readonly distributionTaxDragPpYr: number | null;
  /** The same drag less the drag of the fund it displaces. A drag quoted alone is not quotable. */
  readonly incrementalTaxDragBp: number | null;
  /** The report date of the holdings filing the structure was read from. */
  readonly structureAsOf: AsOf | null;
}

export interface ShelfFund {
  readonly ticker: string;
  readonly name: string;
  readonly category: ShelfCategory;
  /** One line: what the fund is for. Not marketing copy. */
  readonly mandate: string;
  /** Annual expense ratio in basis points. */
  readonly expenseRatioBp: number | null;
  /** Median net securities-lending income, bp/yr, from Form N-CEN. */
  readonly securitiesLendingBp: number | null;
  /** `expenseRatioBp − securitiesLendingBp`. Can be negative. */
  readonly netCostBp: number | null;
  /** Portfolio turnover from Item 3 of the annual report, percent a year. */
  readonly turnoverPercent: number | null;
  readonly loadings: readonly FactorLoading[];
  /** Raw FF5+UMD alpha, pp/yr, on the panel named by `loadings`. */
  readonly alphaPpYr: number | null;
  /** The smallest alpha the window could have detected at 80% power, pp/yr. */
  readonly alphaDetectionFloorPpYr: number | null;
  /** The model-misfit pedestal for this fund's panel, pp/yr. */
  readonly pedestalPpYr: number | null;
  readonly status: EvidenceStatus | null;
  /** Why the status is what it is. One or two sentences, no decoration. */
  readonly verdict: string;
  /** What would have to be true for this fund to be a mistake. */
  readonly caution: string | null;
  /** Present only on wrappers. Absent means the question was never asked of this fund. */
  readonly wrapper?: WrapperFacts;
  /** Present only where a filing was read. An empty list would claim the fund holds nothing. */
  readonly notionalExposure?: readonly NotionalExposure[];
  readonly source: Citation;
  readonly asOf: AsOf;
}

const products: Citation = { label: "The factor-product audit", docPath: "docs/research/factor-products.md" };
const recommendation: Citation = {
  label: "The recommended portfolio",
  docPath: "docs/research/portfolio-recommendation.md",
};
const structural: Citation = {
  label: "Structural and tax edges",
  docPath: "docs/research/structural-and-tax-edges.md",
};
const capital: Citation = {
  label: "Capital efficiency and breadth",
  docPath: "docs/research/capital-efficiency-and-breadth.md",
};
const trend: Citation = { label: "The marginal value of trend", docPath: "docs/research/trend-marginal-value.md" };

const READ = asOf("2026-08-17");

/** The three regional pedestals every alpha on this shelf is a distance from. */
const US_PEDESTAL = -0.55;
const DEVELOPED_PEDESTAL = -0.31;
const EMERGING_PEDESTAL = 1.5;

export const shelf: readonly ShelfFund[] = [
  // -------------------------------------------------------------------------
  // US core. Four funds, one regression: only VTI was ever run as a control.
  // -------------------------------------------------------------------------
  {
    ticker: "VTI",
    name: "Vanguard Morningstar Total Stock Market ETF",
    category: "us-core",
    mandate: "The whole US market at capitalisation weight. The control every US result here is measured against.",
    expenseRatioBp: 3,
    securitiesLendingBp: 1.84,
    netCostBp: 1.16,
    turnoverPercent: 3,
    loadings: [{ factor: "HML", value: 0.0247, interval: null, panel: "us", months: 72 }],
    alphaPpYr: -0.547,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: US_PEDESTAL,
    status: null,
    verdict:
      "The incumbent. Its −0.55 pp/yr alpha is the model misfitting a cap-weighted market, not the fund losing money, and it is the pedestal every other US alpha on this shelf is a distance from.",
    caution: null,
    source: recommendation,
    asOf: READ,
  },
  {
    ticker: "VOO",
    name: "Vanguard S&P 500 ETF",
    category: "us-core",
    mandate: "The S&P 500 at capitalisation weight. Priced as an alternate to VTI and never regressed.",
    expenseRatioBp: 3,
    securitiesLendingBp: 0.06,
    netCostBp: 2.94,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "The whole difference from VTI is 1.78 bp of securities lending — VOO earns the least of any fund on the core shelf in all eight filed years — and P(ahead at 30 yr) is 0.52 to 0.54. No factor experiment read it, so it has no loading and no alpha.",
    caution: null,
    source: structural,
    asOf: READ,
  },
  {
    ticker: "ITOT",
    name: "iShares Core S&P Total US Stock Market ETF",
    category: "us-core",
    mandate: "The same US total-market claim as VTI, and the cheapest of the four to own.",
    expenseRatioBp: 3,
    securitiesLendingBp: 1.96,
    netCostBp: 1.04,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Cheapest US total-market fund on net cost at 1.04 bp, and the US leg of the cheapest combination on the whole shelf (0.76 bp/yr against the recommended four at 1.36). Never regressed.",
    caution: null,
    source: structural,
    asOf: READ,
  },
  {
    ticker: "SPY",
    name: "SPDR S&P 500 ETF Trust",
    category: "us-core",
    mandate: "The same index as VOO in a 1993 unit investment trust, and the fund cost is measured on.",
    expenseRatioBp: 9.45,
    securitiesLendingBp: 0,
    netCostBp: 9.45,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Five times any other S&P 500 fund at 9.45 bp, because a unit investment trust cannot lend its securities, cannot reinvest dividends and cannot hold anything but the index. Its 0.00 bp spread is what a trader pays; the holder pays 9.45 bp a year.",
    caution: null,
    source: structural,
    asOf: READ,
  },
  // -------------------------------------------------------------------------
  // US value and small. Nine systematic products, all `exploratory`, and the two
  // cheap incumbents the frozen comparator is built from, both `rejected`.
  // -------------------------------------------------------------------------
  {
    ticker: "VTV",
    name: "Vanguard Value ETF",
    category: "us-value",
    mandate: "A cap-weighted US large-value index at 3 bp. A building block of the frozen comparator, not a tilt.",
    expenseRatioBp: 3,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [{ factor: "HML", value: 0.337, interval: "[+0.225, +0.471]", panel: "us", months: 72 }],
    alphaPpYr: -2.6,
    alphaDetectionFloorPpYr: 3.28,
    pedestalPpYr: US_PEDESTAL,
    status: "rejected",
    verdict:
      "Delivers HML +0.337 and is still `rejected` on clause (c): a +2.57 pp/yr shortfall to a cheap combination that is 78% VTI plus 22% VB. Read that as 'value can be approximated with VTI and VB', not as a defect in the fund.",
    caution:
      "It is inside the basis every other US product is scored against, so its own rejection is partly a statement about the test.",
    source: products,
    asOf: READ,
  },
  {
    ticker: "AVUV",
    name: "Avantis U.S. Small Cap Value ETF",
    category: "us-value",
    mandate: "A systematic US small-value tilt with a profitability screen. The deepest HML on the US small shelf.",
    expenseRatioBp: 25,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 6,
    loadings: [
      { factor: "HML", value: 0.537, interval: "[+0.43, +0.64]", panel: "us", months: 72 },
      { factor: "SMB", value: 0.88, interval: null, panel: "us", months: 72 },
    ],
    alphaPpYr: 0.39,
    alphaDetectionFloorPpYr: 3.64,
    pedestalPpYr: US_PEDESTAL,
    status: "exploratory",
    verdict:
      "The largest implementation shortfall on the shelf, −4.92 pp/yr on the frozen basis and −4.23 on a cheap style grid that can express small value: the best in-sample combination of VTI, VUG, VTV and VB could not get within four points a year of it.",
    caution:
      "Its SMB leg of +0.88 is the largest of any US value product here and the size premium is not signable on any panel (+0.33 against a 2.47 pp/yr floor). At a 20% weight it buys +43.1 bp for 312 bp of tracking error and reaches 90% confidence in 86 years.",
    source: recommendation,
    asOf: READ,
  },
  {
    ticker: "DFUV",
    name: "Dimensional US Marketwide Value ETF",
    category: "us-value",
    mandate: "A systematic US large-value tilt. The best growth-per-tracking-error US value fund after AVLV.",
    expenseRatioBp: 21,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 5,
    loadings: [
      { factor: "HML", value: 0.515, interval: "[+0.35, +0.71]", panel: "us", months: 43 },
      { factor: "SMB", value: 0.12, interval: null, panel: "us", months: 43 },
    ],
    alphaPpYr: -2.06,
    alphaDetectionFloorPpYr: 5.21,
    pedestalPpYr: US_PEDESTAL,
    status: "exploratory",
    verdict:
      "Buys HML +0.515 with an SMB leg of +0.12, so a 20% weight costs 160 bp of tracking error against AVUV's 312 for a comparable exposure. Its +0.11 shortfall is the only positive one among the nine systematic products.",
    caution: "43 months, and its −2.06 alpha sits inside a 5.21 pp/yr floor — unmeasurable rather than absent.",
    source: recommendation,
    asOf: READ,
  },
  {
    ticker: "DFLV",
    name: "Dimensional US Large Cap Value ETF",
    category: "us-value",
    mandate: "A systematic US large-value tilt on the shortest window of any product audited here.",
    expenseRatioBp: 21,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 5,
    loadings: [
      { factor: "HML", value: 0.637, interval: "[+0.42, +0.82]", panel: "us", months: 36 },
      { factor: "SMB", value: -0.05, interval: null, panel: "us", months: 36 },
    ],
    alphaPpYr: -6.06,
    alphaDetectionFloorPpYr: 5.69,
    pedestalPpYr: US_PEDESTAL,
    status: "exploratory",
    verdict:
      "The largest HML loading on the US large-value shelf, and on exposure alone a 20% weight prices at +53.8 bp for 163 bp of tracking error — the best ratio in the table.",
    caution:
      "Disqualifying: its raw alpha of −6.06 pp/yr exceeds its own 5.69 detection floor, one of sixteen such funds on a 109-fund shelf and all sixteen negative. Charging it takes the tilt to about −67 bp, or −54 bp against its own 36-month pedestal of −0.65 pp/yr.",
    source: recommendation,
    asOf: READ,
  },
  {
    ticker: "DFSV",
    name: "Dimensional US Small Cap Value ETF",
    category: "us-value",
    mandate: "A systematic US small-value tilt.",
    expenseRatioBp: 30,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 9,
    loadings: [
      { factor: "HML", value: 0.442, interval: "[+0.34, +0.64]", panel: "us", months: 46 },
      { factor: "SMB", value: 0.85, interval: null, panel: "us", months: 46 },
    ],
    alphaPpYr: 0.45,
    alphaDetectionFloorPpYr: 4.84,
    pedestalPpYr: US_PEDESTAL,
    status: "exploratory",
    verdict: "Delivers its exposure and beats its cheap replication by 1.83 pp/yr on the frozen basis.",
    caution:
      "The same unpriced SMB leg as every small-value fund: +0.85, on a premium that cannot be signed. 262 bp of tracking error at a 20% weight, and 109 years to 90% confidence.",
    source: recommendation,
    asOf: READ,
  },
  {
    ticker: "DFAT",
    name: "Dimensional US Targeted Value ETF",
    category: "us-value",
    mandate: "A systematic US small-value tilt with the longest Dimensional window on this shelf.",
    expenseRatioBp: 28,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 9,
    loadings: [
      { factor: "HML", value: 0.433, interval: "[+0.37, +0.55]", panel: "us", months: 54 },
      { factor: "SMB", value: 0.83, interval: null, panel: "us", months: 54 },
    ],
    alphaPpYr: 0.33,
    alphaDetectionFloorPpYr: 3.79,
    pedestalPpYr: US_PEDESTAL,
    status: "exploratory",
    verdict:
      "Shortfall −3.44 pp/yr frozen and −1.82 on the full cheap style grid: the largest basis attribution of the nine, at +1.62 pp/yr, and it keeps its status anyway.",
    caution: "SMB +0.83 on an unsignable premium; 239 bp of tracking error at 20%.",
    source: recommendation,
    asOf: READ,
  },
  {
    ticker: "RPV",
    name: "Invesco S&P 500 Pure Value ETF",
    category: "us-value",
    mandate: "An index-reconstitution US value tilt — the deepest HML on the whole US shelf.",
    expenseRatioBp: 35,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 42,
    loadings: [
      { factor: "HML", value: 0.71, interval: "[+0.53, +0.83]", panel: "us", months: 72 },
      { factor: "SMB", value: 0.2, interval: null, panel: "us", months: 72 },
    ],
    alphaPpYr: -2.8,
    alphaDetectionFloorPpYr: 6.5,
    pedestalPpYr: US_PEDESTAL,
    status: "exploratory",
    verdict:
      "HML +0.710 over the full 72-month window and a −0.95 pp/yr shortfall, on 72 months rather than the 36 to 54 most of this shelf has.",
    caution:
      "42%/yr of turnover, the highest of any US value product audited and fourteen times the incumbent's — its sort is an index reconstitution, which is exactly the case Experiment 007's 20–40% assumption was right about. 275 bp of tracking error at a 20% weight.",
    source: recommendation,
    asOf: READ,
  },
  {
    ticker: "VBR",
    name: "Vanguard Morningstar Small-Cap Value ETF",
    category: "us-value",
    mandate: "The cheap US small-value index tilt, and the optional sleeve the reference portfolio actually names.",
    expenseRatioBp: 5,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 25,
    loadings: [
      { factor: "HML", value: 0.41, interval: "[+0.322, +0.480]", panel: "us", months: 72 },
      { factor: "SMB", value: 0.56, interval: null, panel: "us", months: 72 },
    ],
    alphaPpYr: -2.78,
    alphaDetectionFloorPpYr: 3.22,
    pedestalPpYr: US_PEDESTAL,
    status: "exploratory",
    verdict:
      "The only US value product that both delivers its exposure and does not lose to a cheap mix, at 5 bp. It is the optional sleeve because of the fee, not because the chain is positive.",
    caution:
      "Its alpha is −2.78 against a 3.22 floor — the closest to measurable of the cheap products — and 25%/yr of turnover puts it with RPV rather than with the systematic funds.",
    source: recommendation,
    asOf: READ,
  },
  {
    ticker: "AVLV",
    name: "Avantis U.S. Large Cap Value ETF",
    category: "us-value",
    mandate: "A systematic US large-value tilt with a profitability screen and low turnover.",
    expenseRatioBp: 15,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 7,
    loadings: [
      { factor: "HML", value: 0.322, interval: "[+0.22, +0.46]", panel: "us", months: 51 },
      { factor: "SMB", value: 0.12, interval: null, panel: "us", months: 51 },
    ],
    alphaPpYr: -0.92,
    alphaDetectionFloorPpYr: 5.28,
    pedestalPpYr: US_PEDESTAL,
    status: "exploratory",
    verdict:
      "Delivers its exposure and keeps its status under every comparator basis tested. It buys comparable HML to a small-value fund at roughly half the tracking error.",
    caution:
      "The US value premium on its own panel is +1.57 pp/yr against a 5.03 pp/yr floor and is not signable. Only the pooled three-region premium makes this tilt's growth contribution positive.",
    source: products,
    asOf: READ,
  },
  {
    ticker: "AVSC",
    name: "Avantis U.S. Small Cap Equity ETF",
    category: "us-small",
    mandate: "A systematic US small-cap tilt. The largest SMB loading on the US shelf.",
    expenseRatioBp: 25,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 5,
    loadings: [
      { factor: "SMB", value: 1.058, interval: "[+0.98, +1.11]", panel: "us", months: 47 },
      { factor: "HML", value: 0.243, interval: null, panel: "us", months: 47 },
    ],
    alphaPpYr: 0.62,
    alphaDetectionFloorPpYr: 3.14,
    pedestalPpYr: US_PEDESTAL,
    status: "exploratory",
    verdict: "SMB +1.058 on a tight interval, and a −0.72 pp/yr shortfall: it delivers exactly what it sells.",
    caution:
      "What it sells cannot be priced. At a 20% weight the exposure is worth +15.7 bp against 252 bp of tracking error, +6.1 bp of growth, and 425 years to 90% confidence.",
    source: recommendation,
    asOf: READ,
  },
  {
    ticker: "DFAS",
    name: "Dimensional U.S. Small Cap ETF",
    category: "us-small",
    mandate: "A systematic US small-cap tilt.",
    expenseRatioBp: 26,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 6,
    loadings: [
      { factor: "SMB", value: 0.816, interval: "[+0.74, +0.91]", panel: "us", months: 54 },
      { factor: "HML", value: 0.241, interval: null, panel: "us", months: 54 },
    ],
    alphaPpYr: -1.4,
    alphaDetectionFloorPpYr: 2.97,
    pedestalPpYr: US_PEDESTAL,
    status: "exploratory",
    verdict: "SMB +0.816 delivered, shortfall −1.16 pp/yr.",
    caution: "265 years to 90% confidence at a 20% weight. The size leg is variance with no priced expectation.",
    source: recommendation,
    asOf: READ,
  },
  {
    ticker: "VB",
    name: "Vanguard Morningstar Small-Cap ETF",
    category: "us-small",
    mandate: "Plain US small-cap at 3 bp. A building block of the frozen comparator rather than a holding.",
    expenseRatioBp: 3,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [{ factor: "SMB", value: 0.599, interval: "[+0.516, +0.684]", panel: "us", months: 72 }],
    alphaPpYr: -2.97,
    alphaDetectionFloorPpYr: 3.16,
    pedestalPpYr: US_PEDESTAL,
    status: "rejected",
    verdict:
      "`rejected` on clause (c) at a +2.89 pp/yr shortfall, its cheap replication being 0.733 VTI plus 0.267 VTV. Its 2.72 bp round trip is nearly a year of expense ratio and is the binding constraint on rebalancing frequency.",
    caution:
      "Like VTV, it sits inside the basis it is scored against, so the rejection reads as 'small-cap is approximable', not as a defect.",
    source: products,
    asOf: READ,
  },
  // -------------------------------------------------------------------------
  // US momentum and quality. Momentum is excluded on turnover and on a 4.98 pp/yr
  // detection floor; quality is `rejected` and closed on public data (decision 0005).
  // -------------------------------------------------------------------------
  {
    ticker: "MTUM",
    name: "iShares MSCI USA Momentum Factor ETF",
    category: "us-momentum",
    mandate: "A US large-cap momentum tilt. For years the whole retail US momentum shelf; now one of six.",
    expenseRatioBp: 15,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [{ factor: "UMD", value: 0.444, interval: "[+0.277, +0.562]", panel: "us", months: 72 }],
    alphaPpYr: -2.95,
    alphaDetectionFloorPpYr: 7.34,
    pedestalPpYr: US_PEDESTAL,
    status: "rejected",
    verdict:
      "Delivers UMD +0.444 and is `rejected` anyway on a +1.10 pp/yr shortfall to a cheap combination. That it was 'the entire momentum shelf' was a property of Experiment 002's census frame, not of the market.",
    caution:
      "Its 7.34 pp/yr detection floor is the worst on the US shelf, so its −2.95 alpha means nothing either way. The sleeve stays excluded on the premium and on turnover, which the corrected frame did not touch.",
    source: products,
    asOf: READ,
  },
  {
    ticker: "SPMO",
    name: "Invesco S&P 500 Momentum ETF",
    category: "us-momentum",
    mandate: "A US large-cap momentum tilt, and one of the four products the corrected census frame added.",
    expenseRatioBp: null,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [{ factor: "UMD", value: 0.414, interval: null, panel: "us", months: null }],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: US_PEDESTAL,
    status: "exploratory",
    verdict:
      "Reaches `exploratory` on UMD +0.414 with a −4.53 pp/yr shortfall — the deepest of the four momentum products the corrected frame found. The page prints the loading and the shortfall and nothing else.",
    caution:
      "No fee, no window, no interval and no alpha were recorded for it here, so it cannot be compared with MTUM on cost. Momentum is excluded regardless: the pooled premium's detection floor is 4.98 pp/yr and its three regions are worth 1.33 effective regions.",
    source: products,
    asOf: READ,
  },
  {
    ticker: "QUAL",
    name: "iShares MSCI USA Quality Factor ETF",
    category: "us-quality",
    mandate: "A US profitability tilt.",
    expenseRatioBp: 15,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [{ factor: "RMW", value: 0.186, interval: "[+0.101, +0.247]", panel: "us", months: 72 }],
    alphaPpYr: -2.15,
    alphaDetectionFloorPpYr: 3.13,
    pedestalPpYr: US_PEDESTAL,
    status: "rejected",
    verdict: "`rejected` on clause (c) at a +1.14 pp/yr shortfall, on an RMW loading of +0.186.",
    caution:
      "The exposure is not purchasable at this threshold anywhere on the shelf — nine quality products and the largest RMW loading is +0.228 — and the premium behind it is `rejected` and closed on public data (decision 0005). A product's own quality is irrelevant when the premium cannot be signed.",
    source: products,
    asOf: READ,
  },
  {
    ticker: "SPHQ",
    name: "Invesco S&P 500 Quality ETF",
    category: "us-quality",
    mandate: "A US profitability tilt.",
    expenseRatioBp: 15,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [{ factor: "RMW", value: 0.176, interval: "[+0.079, +0.296]", panel: "us", months: 72 }],
    alphaPpYr: -0.56,
    alphaDetectionFloorPpYr: 3.75,
    pedestalPpYr: US_PEDESTAL,
    status: "unresolved",
    verdict:
      "`unresolved`: its RMW interval straddles the 0.15 bar, so the window could not say whether the exposure is there. Shortfall −0.13.",
    caution: "RMW is closed on public data. Nothing this fund does can reopen it.",
    source: products,
    asOf: READ,
  },
  {
    ticker: "DUHP",
    name: "Dimensional US High Profitability ETF",
    category: "us-quality",
    mandate: "A US profitability tilt from the sponsor whose value products all reach `exploratory`.",
    expenseRatioBp: 20,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [{ factor: "RMW", value: 0.179, interval: "[+0.03, +0.29]", panel: "us", months: 46 }],
    alphaPpYr: -1.43,
    alphaDetectionFloorPpYr: 4.46,
    pedestalPpYr: US_PEDESTAL,
    status: "unresolved",
    verdict: "`unresolved` on the same clause as SPHQ: the interval contains 0.15 on 46 months. Shortfall −0.11.",
    caution: "The only Dimensional product on the US shelf that does not reach `exploratory`, and the factor is why.",
    source: products,
    asOf: READ,
  },
  // -------------------------------------------------------------------------
  // Developed ex-US. Every loading below is on the developed-ex-US panel, which is
  // the only thing that makes any of them comparable; the US panel would put 16 of
  // 25 below the bar rather than 5.
  // -------------------------------------------------------------------------
  {
    ticker: "VEA",
    name: "Vanguard FTSE Developed Markets ETF",
    category: "intl-core",
    mandate: "Developed ex-US at capitalisation weight. The incumbent term in every ex-US factor chain.",
    expenseRatioBp: 3,
    securitiesLendingBp: 3.3,
    netCostBp: -0.3,
    turnoverPercent: 4,
    loadings: [
      { factor: "HML", value: 0.015, interval: null, panel: "developed-ex-us", months: 77 },
      { factor: "UMD", value: 0.006, interval: null, panel: "developed-ex-us", months: null },
    ],
    alphaPpYr: -0.31,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: DEVELOPED_PEDESTAL,
    status: null,
    verdict:
      "Costs −0.30 bp/yr to own: 3.30 bp of securities lending more than covers the 3 bp fee. Its own loadings are the term every ex-US tilt is measured against, and its −0.31 pp/yr alpha is the developed-ex-US pedestal.",
    caution:
      "It beat its region's French market portfolio by 0.517 pp/yr beyond its fee. That is recorded as an index-construction difference and is not a finding. Its foreign tax credit is worth 15.78 bp/yr and only in a taxable account.",
    source: recommendation,
    asOf: READ,
  },
  {
    ticker: "SPDW",
    name: "SPDR Portfolio Developed World ex-US ETF",
    category: "intl-core",
    mandate: "The same developed ex-US claim, and the cheapest fund to own on the entire core shelf.",
    expenseRatioBp: 3,
    securitiesLendingBp: 4.63,
    netCostBp: -1.63,
    turnoverPercent: 3,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict: "Its 3 bp fee is covered twice over by lending, at −1.63 bp net. Never regressed.",
    caution: null,
    source: structural,
    asOf: READ,
  },
  {
    ticker: "IEFA",
    name: "iShares Core MSCI EAFE ETF",
    category: "intl-core",
    mandate: "Developed ex-US excluding Canada, priced only on cost.",
    expenseRatioBp: 7,
    securitiesLendingBp: 2.35,
    netCostBp: 4.65,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict: "The dearest developed ex-US fund audited at 4.65 bp net, on a 7 bp fee lending covers only a third of.",
    caution: null,
    source: structural,
    asOf: READ,
  },
  {
    ticker: "VXUS",
    name: "Vanguard Total International Stock ETF",
    category: "intl-core",
    mandate: "Developed and emerging international equity in one holding.",
    expenseRatioBp: 5,
    securitiesLendingBp: 3.57,
    netCostBp: 1.43,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "The cheapest total-international fund audited at 1.43 bp net, and still dearer than holding VEA and VWO separately: splitting saves 1.25 bp/yr on the international sleeve before any placement argument.",
    caution:
      "This repository previously recorded VXUS at 3 bp, which was wrong. The 5 bp is from the 497K fee table dated 2026-02-27.",
    source: structural,
    asOf: READ,
  },
  {
    ticker: "DFIV",
    name: "Dimensional International Value ETF",
    category: "intl-value",
    mandate: "A developed ex-US large-value tilt, the deepest on the audited ex-US shelf.",
    expenseRatioBp: 27,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 6,
    loadings: [
      { factor: "HML", value: 0.662, interval: "[+0.53, +0.85]", panel: "developed-ex-us", months: 51 },
      { factor: "SMB", value: -0.114, interval: null, panel: "developed-ex-us", months: 51 },
      { factor: "RMW", value: -0.001, interval: null, panel: "developed-ex-us", months: 51 },
      { factor: "CMA", value: -0.122, interval: null, panel: "developed-ex-us", months: 51 },
      { factor: "UMD", value: 0.016, interval: null, panel: "developed-ex-us", months: 51 },
    ],
    alphaPpYr: -4.11,
    alphaDetectionFloorPpYr: 3.52,
    pedestalPpYr: DEVELOPED_PEDESTAL,
    status: "exploratory",
    verdict:
      "The strongest tilt this repository has priced: at an 8% substitution out of VEA it is the only line whose edge, +27.1 bp, sits above its own 30-year detection floor of 21.6 bp.",
    caution:
      "Its own alpha is −4.11 pp/yr against a 3.52 pp/yr floor — measurably negative, and one of four ex-US large-value funds reading −2.2 to −4.1. Charging that alpha takes the same tilt from +27.1 bp to −8.2 bp.",
    source: recommendation,
    asOf: READ,
  },
  {
    ticker: "AVIV",
    name: "Avantis International Large Cap Value ETF",
    category: "intl-value",
    mandate: "A developed ex-US large-value tilt with the tightest tracking error of the five ranked.",
    expenseRatioBp: 25,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 11,
    loadings: [
      { factor: "HML", value: 0.489, interval: "[+0.36, +0.63]", panel: "developed-ex-us", months: 51 },
      { factor: "SMB", value: -0.285, interval: "[−0.47, −0.13]", panel: "developed-ex-us", months: 51 },
      { factor: "RMW", value: -0.031, interval: null, panel: "developed-ex-us", months: 51 },
      { factor: "CMA", value: -0.182, interval: null, panel: "developed-ex-us", months: 51 },
      { factor: "UMD", value: -0.109, interval: null, panel: "developed-ex-us", months: 51 },
    ],
    alphaPpYr: -3.13,
    alphaDetectionFloorPpYr: 1.81,
    pedestalPpYr: DEVELOPED_PEDESTAL,
    status: "exploratory",
    verdict:
      "Second on growth per unit of tracking error at 0.576, and the lowest tracking error of the five at 31.3 bp for an 8% substitution. Shortfall −0.51 frozen, −0.16 expressive.",
    caution:
      "Its −3.13 pp/yr alpha against a 1.81 floor is the most clearly measurable negative on the ex-US shelf; charging it takes an 8% tilt from +18.0 bp to −9.5 bp.",
    source: recommendation,
    asOf: READ,
  },
  {
    ticker: "IVLU",
    name: "iShares MSCI Intl Value Factor ETF",
    category: "intl-value",
    mandate: "A developed ex-US large-value tilt on the longest window of the four.",
    expenseRatioBp: 31,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 16,
    loadings: [
      { factor: "HML", value: 0.475, interval: "[+0.33, +0.60]", panel: "developed-ex-us", months: 77 },
      { factor: "SMB", value: -0.121, interval: "[−0.32, +0.07]", panel: "developed-ex-us", months: 77 },
      { factor: "RMW", value: 0.053, interval: null, panel: "developed-ex-us", months: 77 },
      { factor: "CMA", value: 0.02, interval: null, panel: "developed-ex-us", months: 77 },
      { factor: "UMD", value: -0.083, interval: null, panel: "developed-ex-us", months: 77 },
    ],
    alphaPpYr: -2.53,
    alphaDetectionFloorPpYr: 2.63,
    pedestalPpYr: DEVELOPED_PEDESTAL,
    status: "exploratory",
    verdict:
      "The only large-value fund of the four whose alpha is not measurable — −2.53 inside a 2.63 floor — so on the alpha-charged reading this repository's answer is IVLU rather than DFIV, at 0.552 growth per unit of tracking error.",
    caution:
      "Its edge is smaller than DFIV's (+19.4 bp against +27.1 at an 8% substitution) and its shortfall of −1.19 does not move under any of the seven bases.",
    source: recommendation,
    asOf: READ,
  },
  {
    ticker: "EFV",
    name: "iShares MSCI EAFE Value ETF",
    category: "intl-value",
    mandate: "A developed ex-US large-value index tilt, and a column in the comparator basis.",
    expenseRatioBp: 31,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 23,
    loadings: [
      { factor: "HML", value: 0.368, interval: "[+0.26, +0.49]", panel: "developed-ex-us", months: 77 },
      { factor: "SMB", value: -0.16, interval: "[−0.31, −0.06]", panel: "developed-ex-us", months: 77 },
      { factor: "RMW", value: -0.006, interval: null, panel: "developed-ex-us", months: 77 },
      { factor: "CMA", value: 0.17, interval: null, panel: "developed-ex-us", months: 77 },
      { factor: "UMD", value: -0.069, interval: null, panel: "developed-ex-us", months: 77 },
    ],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 2.22,
    pedestalPpYr: DEVELOPED_PEDESTAL,
    status: "exploratory",
    verdict:
      "Shortfall −1.19 frozen and −1.20 expressive, and it survives every basis except the placebo that hands a second EAFE value fund to a fund that *is* EAFE value — a change in what is measured, not in the fund.",
    caution:
      "Only its shrunk alpha, −1.58 pp/yr against a 2.22 floor, was published; the raw figure is not in this repository, so `alphaPpYr` is null rather than the shrunk number wearing a raw label.",
    source: products,
    asOf: READ,
  },
  {
    ticker: "AVDV",
    name: "Avantis International Small Cap Value ETF",
    category: "intl-small-value",
    mandate: "A developed ex-US small-value tilt. The only fund that can express that cell in any comparator here.",
    expenseRatioBp: 36,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 4,
    loadings: [
      { factor: "HML", value: 0.51, interval: "[+0.32, +0.78]", panel: "developed-ex-us", months: 75 },
      { factor: "SMB", value: 0.671, interval: "[+0.46, +0.84]", panel: "developed-ex-us", months: 75 },
      { factor: "RMW", value: 0.386, interval: "[+0.12, +0.65]", panel: "developed-ex-us", months: 75 },
      { factor: "CMA", value: -0.114, interval: null, panel: "developed-ex-us", months: 75 },
      { factor: "UMD", value: 0.008, interval: null, panel: "developed-ex-us", months: 75 },
    ],
    alphaPpYr: 2.47,
    alphaDetectionFloorPpYr: 3.96,
    pedestalPpYr: DEVELOPED_PEDESTAL,
    status: "exploratory",
    verdict:
      "Keeps a −4.58 pp/yr shortfall under all seven bases, including the ones containing itself, because no other column can express developed-ex-US small value. It files 4%/yr of turnover, the lowest of any factor product in either audit.",
    caution:
      "The only value fund on the shelf carrying two side loads whose intervals exclude zero: SMB +0.671 on a premium of +0.49 `[−1.44, +2.44]`, and RMW +0.386 on a `rejected` factor. It is fourth or fifth of five on growth per unit of tracking error in every window. The two owning pages print different alphas for it — +2.47 on the common 45-month window and +0.55 on the ex-US audit page — against the same 3.96 floor; the figure here is the former.",
    source: recommendation,
    asOf: READ,
  },
  {
    ticker: "DISV",
    name: "Dimensional International Small Cap Value ETF",
    category: "intl-small-value",
    mandate: "A developed ex-US small-value tilt.",
    expenseRatioBp: 42,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 8,
    loadings: [
      { factor: "HML", value: 0.495, interval: "[+0.36, +0.64]", panel: "developed-ex-us", months: 45 },
      { factor: "SMB", value: 0.431, interval: "[+0.23, +0.65]", panel: "developed-ex-us", months: 45 },
      { factor: "RMW", value: 0.049, interval: null, panel: "developed-ex-us", months: 45 },
      { factor: "CMA", value: -0.005, interval: null, panel: "developed-ex-us", months: 45 },
      { factor: "UMD", value: -0.088, interval: null, panel: "developed-ex-us", months: 45 },
    ],
    alphaPpYr: -0.21,
    alphaDetectionFloorPpYr: 3.98,
    pedestalPpYr: DEVELOPED_PEDESTAL,
    status: "exploratory",
    verdict:
      "The largest basis effect on the ex-US shelf: its shortfall goes from −2.89 to +0.05 once a small-value column exists, on a replication that puts 69% of its weight on AVDV. It keeps `exploratory` only because +0.05 sits under the 0.50 threshold.",
    caution:
      "Worst of five on tracking error per unit of HML at 11.6, and its SMB leg of +0.431 is on a premium that cannot be signed.",
    source: recommendation,
    asOf: READ,
  },
  {
    ticker: "SCZ",
    name: "iShares MSCI EAFE Small-Cap ETF",
    category: "intl-core",
    mandate: "Developed ex-US small-cap blend.",
    expenseRatioBp: 40,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 18,
    loadings: [
      { factor: "HML", value: -0.032, interval: "[−0.16, +0.14]", panel: "developed-ex-us", months: 77 },
      { factor: "SMB", value: 0.551, interval: "[+0.43, +0.64]", panel: "developed-ex-us", months: 77 },
      { factor: "RMW", value: 0.041, interval: null, panel: "developed-ex-us", months: 77 },
      { factor: "CMA", value: 0.036, interval: null, panel: "developed-ex-us", months: 77 },
      { factor: "UMD", value: -0.024, interval: null, panel: "developed-ex-us", months: 77 },
    ],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 2.43,
    pedestalPpYr: DEVELOPED_PEDESTAL,
    status: "exploratory",
    verdict:
      "Delivers SMB +0.551 and is one of the seven ex-US funds surviving every basis tested, with a shortfall of +0.36 that does not move.",
    caution:
      "A pure size exposure at 40 bp, on a premium that is not signable on any panel. Only its shrunk alpha, −0.39 pp/yr against a 2.43 floor, was published.",
    source: products,
    asOf: READ,
  },
  {
    ticker: "GWX",
    name: "SPDR S&P International Small Cap ETF",
    category: "intl-core",
    mandate: "Developed ex-US small-cap blend. The largest intended loading in the entire ex-US audit.",
    expenseRatioBp: null,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [{ factor: "SMB", value: 0.856, interval: null, panel: "developed-ex-us", months: 78 }],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 2.5,
    pedestalPpYr: DEVELOPED_PEDESTAL,
    status: "rejected",
    verdict:
      "`rejected` on clause (c) at +1.24 pp/yr under all seven bases — and the rejection turns on one month. GWX files from 2019-07, which only three basis constituents cover, so its 'cheap replication' is VEA at weight 1.000: a large-cap fund standing in for a small-cap one.",
    caution:
      "Trim that single uncovered month and the shortfall falls to between +0.00 and +0.39, all under the threshold. The published verdict stands because the specification was frozen, but it must be read as 'the comparator did not exist for one of its months'. Its fee was never read.",
    source: products,
    asOf: READ,
  },
  {
    ticker: "IDMO",
    name: "Invesco S&P International Developed Momentum ETF",
    category: "intl-momentum",
    mandate: "A developed ex-US momentum tilt, on the one momentum premium that clears its own detection floor.",
    expenseRatioBp: 25,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 105,
    loadings: [
      { factor: "UMD", value: 0.54, interval: "[+0.39, +0.71]", panel: "developed-ex-us", months: 77 },
      { factor: "HML", value: 0.218, interval: "[−0.13, +0.52]", panel: "developed-ex-us", months: 77 },
      { factor: "SMB", value: -0.164, interval: "[−0.34, +0.04]", panel: "developed-ex-us", months: 77 },
      { factor: "RMW", value: 0.04, interval: null, panel: "developed-ex-us", months: 77 },
      { factor: "CMA", value: -0.394, interval: "[−0.72, −0.06]", panel: "developed-ex-us", months: 77 },
    ],
    alphaPpYr: 0.11,
    alphaDetectionFloorPpYr: 5.34,
    pedestalPpYr: DEVELOPED_PEDESTAL,
    status: "exploratory",
    verdict:
      "Delivers +0.535 of UMD over VEA on a signable premium (+8.35 `[+4.82, +11.66]` against a 5.21 floor), worth +4.47 pp/yr gross and +2.53 net per dollar of sleeve. It survives all seven bases at −5.43 to −5.18, and at 0.25% it is what causes IMTM to be rejected.",
    caution:
      "Excluded from the reference portfolio anyway. It files 105%/yr of turnover against VEA's 4%, so cost takes 43% of the gross exposure at `k = 1.7` (28% at `k = 1.0`), and it carries CMA −0.394 on a `rejected` factor.",
    source: products,
    asOf: READ,
  },
  {
    ticker: "IMTM",
    name: "iShares MSCI Intl Momentum Factor ETF",
    category: "intl-momentum",
    mandate: "A developed ex-US momentum tilt, and the dearer of the shelf's two.",
    expenseRatioBp: 30,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [
      { factor: "UMD", value: 0.505, interval: "[+0.44, +0.59]", panel: "developed-ex-us", months: 77 },
      { factor: "HML", value: 0.088, interval: "[−0.04, +0.21]", panel: "developed-ex-us", months: 77 },
      { factor: "SMB", value: -0.306, interval: "[−0.44, −0.16]", panel: "developed-ex-us", months: 77 },
      { factor: "RMW", value: -0.012, interval: null, panel: "developed-ex-us", months: 77 },
      { factor: "CMA", value: -0.241, interval: null, panel: "developed-ex-us", months: 77 },
    ],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 3.81,
    pedestalPpYr: DEVELOPED_PEDESTAL,
    status: "rejected",
    verdict:
      "`exploratory` at −2.31 on the frozen basis and `rejected` at +0.91 once the basis can hold IDMO at 0.25%, which takes 57.5% of the fitted weight. The loss is a cheaper fund in its own cell, which is exactly what clause (c) exists to find.",
    caution:
      "Like AVDV it carries two side loads whose intervals exclude zero, SMB −0.306 and CMA −0.241. Only its shrunk alpha, −1.46 against a 3.81 floor, was published.",
    source: products,
    asOf: READ,
  },
  // -------------------------------------------------------------------------
  // Emerging. The pedestal here is +1.50 pp/yr and positive: a cap-weighted index
  // fund earns that much alpha against the research portfolio it is supposed to be,
  // so every emerging alpha below is a distance from +1.50 and not from zero.
  // -------------------------------------------------------------------------
  {
    ticker: "VWO",
    name: "Vanguard FTSE Emerging Markets ETF",
    category: "emerging-core",
    mandate: "Emerging markets at capitalisation weight, and the comparator every emerging alpha is read against.",
    expenseRatioBp: 6,
    securitiesLendingBp: 4.33,
    netCostBp: 1.67,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: 1.5,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: EMERGING_PEDESTAL,
    status: null,
    verdict:
      "Costs 1.67 bp net. Its +1.50 pp/yr alpha over 77 months is the emerging pedestal — large, positive, and basis-invariant, which is why an emerging product reading −0.16 is further below its control than the raw number suggests.",
    caution:
      "Its credit is worth 20.00 bp/yr in taxable, and its filed foreign-tax rate of 12.59% would push the placement break-even to 27.48%, extending the inversion to a 23.8% investor.",
    source: recommendation,
    asOf: READ,
  },
  {
    ticker: "IEMG",
    name: "iShares Core MSCI Emerging Markets ETF",
    category: "emerging-core",
    mandate: "The same emerging claim as VWO, priced only as core beta.",
    expenseRatioBp: 9,
    securitiesLendingBp: 9.87,
    netCostBp: -0.87,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "A 50% higher fee than VWO and the cheaper fund to own: lending covers the whole 9 bp and 0.87 bp besides. Its fee is capped at 0.09% to 2030-12-31 with no recoupment — the most durable fee commitment on the shelf.",
    caution:
      "No factor loading, no alpha and no usable tracking difference were read for it. A high lending yield is partly compensation for holding what short sellers want.",
    source: structural,
    asOf: READ,
  },
  {
    ticker: "AVES",
    name: "Avantis Emerging Markets Value ETF",
    category: "emerging-value",
    mandate: "An emerging-market value tilt, in the region with the largest measured HML premium.",
    expenseRatioBp: null,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [
      { factor: "HML", value: 0.237, interval: null, panel: "emerging", months: 51 },
      { factor: "HML", value: -0.074, interval: null, panel: "us", months: 51 },
    ],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 4.48,
    pedestalPpYr: EMERGING_PEDESTAL,
    status: "unresolved",
    verdict:
      "`unresolved` on window length, not on failure: 51 months put its interval across the 0.15 bar. The verdict is basis-invariant — no comparator, however expressive, can move an emerging product to `exploratory`, because clause (a) reads the loading and `unresolved` reads its interval and neither reads the basis.",
    caution:
      "The panel does the heaviest work here: the same fund reads −0.074 on the US panel, which would flip the sign of the only evidence that the emerging value premium is purchasable at all. No fee, no turnover, no net cost and no tax figure for AVES appears anywhere in this repository. Only its shrunk alpha, −0.16 against a 4.48 floor, was published.",
    source: products,
    asOf: READ,
  },
  {
    ticker: "DFEV",
    name: "Dimensional Emerging Markets Value ETF",
    category: "emerging-value",
    mandate: "An emerging-market value tilt on the shortest ex-US window audited.",
    expenseRatioBp: null,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [
      { factor: "HML", value: 0.267, interval: null, panel: "emerging", months: 44 },
      { factor: "HML", value: -0.092, interval: null, panel: "us", months: 44 },
    ],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 3.23,
    pedestalPpYr: EMERGING_PEDESTAL,
    status: "unresolved",
    verdict:
      "The larger of the two emerging value loadings and the shorter window: 44 months, interval across the bar, shortfall −2.19 frozen and −2.03 expressive. `unresolved`, basis-invariant.",
    caution:
      "Reads −0.092 on the US panel. With AVES it is why the region with the largest measured HML premium — +7.58 `[+4.34, +11.01]` — has nothing investable audited here. No fee was read. Only its shrunk alpha, −1.19 against a 3.23 floor, was published.",
    source: products,
    asOf: READ,
  },
  // -------------------------------------------------------------------------
  // Bonds. Priced on cost only; the equity/bond split is the largest decision in
  // the portfolio and the one the evidence is silent on.
  // -------------------------------------------------------------------------
  {
    ticker: "BND",
    name: "Vanguard Total Bond Market ETF",
    category: "bonds",
    mandate: "Investment-grade US aggregate bonds. Term and credit compensation, and a risk brake.",
    expenseRatioBp: 3,
    securitiesLendingBp: 0,
    netCostBp: 3,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "The dearest aggregate-bond fund audited on an identical 3 bp fee, because it is the only one that does not lend at all: Vanguard answers Item C.6.a 'No' in all eight fiscal years.",
    caution:
      "Booking a term premium as an edge over an equity index swaps the benchmark rather than adding return. Bonds dominate the placement ranking by more than four to one at every rate.",
    source: recommendation,
    asOf: READ,
  },
  {
    ticker: "SPAB",
    name: "SPDR Portfolio Aggregate Bond ETF",
    category: "bonds",
    mandate: "The same aggregate-bond claim, and the cheapest of the four audited to own.",
    expenseRatioBp: 3,
    securitiesLendingBp: 0.91,
    netCostBp: 2.09,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict: "2.09 bp net, and the bond leg of the cheapest combination on the shelf at 0.76 bp/yr.",
    caution: null,
    source: structural,
    asOf: READ,
  },
  // -------------------------------------------------------------------------
  // Managed futures. The loading is on the AQR TSMOM index, which is a different
  // panel from any equity one; a `delta` of 1.000 means these funds keep none of
  // the +2.44 pp/yr funding-rule gap, because they are bought by selling equity.
  // -------------------------------------------------------------------------
  {
    ticker: "DBMF",
    name: "iMGP DBi Managed Futures Strategy ETF",
    category: "managed-futures",
    mandate: "A replication of the average large managed-futures fund. The only trend product ever regressed here.",
    expenseRatioBp: 85,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [{ factor: "TSMOM", value: 0.671, interval: "[+0.513, +0.829]", panel: "aqr-tsmom", months: 54 }],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 10.93,
    pedestalPpYr: null,
    status: "exploratory",
    verdict:
      "The one product that delivers this benchmark's exposure: the interval clears the frozen 0.50 bar, one regressor explains 52% of its monthly variance, and the loading holds across the fixed split and all 19 rolling windows with no sign change. It trailed a cost-free vendor index by 0.48 pp/yr against an 0.85% fee.",
    caution:
      "Its 2.09 pp/yr distribution tax drag is 2.5 times its own fee, 143.9 bp of it incremental over the equity it displaces — 43 bp of portfolio return at a 30% weight. Bought pro rata it keeps none of the funding-rule gap. The post-publication trend interval includes zero and fails Holm.",
    wrapper: {
      delta: 1,
      fundingCapturePercent: 0,
      allInCostBp: 85,
      grossNotionalPerDollar: 1,
      distributionTaxDragPpYr: 2.09,
      incrementalTaxDragBp: 143.9,
      structureAsOf: null,
    },
    source: trend,
    asOf: READ,
  },
  {
    ticker: "CTA",
    name: "Simplify Managed Futures Strategy ETF",
    category: "managed-futures",
    mandate: "A discretionary-systematic managed-futures book.",
    expenseRatioBp: 75,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [{ factor: "TSMOM", value: 0.475, interval: "[+0.058, +0.991]", panel: "aqr-tsmom", months: 46 }],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 13.14,
    pedestalPpYr: null,
    status: "rejected",
    verdict:
      "`rejected` against the frozen 0.50 bar: the point estimate is below it and the interval spans from 0.058 to 0.991, on 46 months with an R² of 0.137 and a +1.90 pp/yr tracking difference.",
    caution:
      "A 13.14 pp/yr detection floor. This is a statement about what the window could see, not that the fund holds no trend.",
    wrapper: {
      delta: 1,
      fundingCapturePercent: 0,
      allInCostBp: 75,
      grossNotionalPerDollar: 1,
      distributionTaxDragPpYr: null,
      incrementalTaxDragBp: null,
      structureAsOf: null,
    },
    source: trend,
    asOf: READ,
  },
  {
    ticker: "KMLM",
    name: "KFA Mount Lucas Managed Futures Index Strategy ETF",
    category: "managed-futures",
    mandate: "The KFA MLM Index: 22 futures and no equity index futures at all.",
    expenseRatioBp: 90,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [{ factor: "TSMOM", value: 0.245, interval: "[−0.148, +0.446]", panel: "aqr-tsmom", months: 60 }],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 16.49,
    pedestalPpYr: null,
    status: "rejected",
    verdict:
      "`rejected` at +0.245 with an interval containing zero. The shortfall is partly definitional and must not be read as a defect: its index holds none of the nine equity futures in AQR's universe.",
    caution: "A 16.49 pp/yr detection floor, the worst of the five, on an R² of 0.066.",
    wrapper: {
      delta: 1,
      fundingCapturePercent: 0,
      allInCostBp: 90,
      grossNotionalPerDollar: 1,
      distributionTaxDragPpYr: 1.81,
      incrementalTaxDragBp: null,
      structureAsOf: null,
    },
    source: trend,
    asOf: READ,
  },
  {
    ticker: "FMF",
    name: "First Trust Managed Futures Strategy Fund",
    category: "managed-futures",
    mandate: "An actively managed futures book on the longest window of the five.",
    expenseRatioBp: 98,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [{ factor: "TSMOM", value: 0.303, interval: "[+0.183, +0.420]", panel: "aqr-tsmom", months: 78 }],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 6.64,
    pedestalPpYr: null,
    status: "rejected",
    verdict:
      "`rejected` at +0.303 on 78 months — the tightest interval of the four rejections and clearly under the 0.50 bar, so this is a delivered-exposure verdict rather than an underpowered one.",
    caution: "The dearest of the five at 0.98%.",
    wrapper: {
      delta: 1,
      fundingCapturePercent: 0,
      allInCostBp: 98,
      grossNotionalPerDollar: 1,
      distributionTaxDragPpYr: null,
      incrementalTaxDragBp: null,
      structureAsOf: null,
    },
    source: trend,
    asOf: READ,
  },
  {
    ticker: "WTMF",
    name: "WisdomTree Managed Futures Strategy Fund",
    category: "managed-futures",
    mandate: "A managed-futures book that the frozen screen admitted and nobody asked for.",
    expenseRatioBp: 66,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [{ factor: "TSMOM", value: 0.099, interval: "[+0.003, +0.201]", panel: "aqr-tsmom", months: 76 }],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 8.94,
    pedestalPpYr: null,
    status: "rejected",
    verdict:
      "The lowest loading of the five at +0.099 with an R² of 0.042: on this benchmark it is very nearly not a trend fund at all.",
    caution: "Its +2.31 pp/yr tracking difference is the largest of the five and sits inside an 8.94 pp/yr floor.",
    wrapper: {
      delta: 1,
      fundingCapturePercent: 0,
      allInCostBp: 66,
      grossNotionalPerDollar: 1,
      distributionTaxDragPpYr: null,
      incrementalTaxDragBp: null,
      structureAsOf: null,
    },
    source: trend,
    asOf: READ,
  },
  // -------------------------------------------------------------------------
  // Capital-efficient wrappers. Every one of these has an empty `loadings` list and
  // a null alpha, and that is the most important fact on the entry: what is verified
  // is structure and cost from filings, never that the sleeve inside delivers
  // anything. No loading has ever been measured for any wrapper on this shelf.
  // -------------------------------------------------------------------------
  {
    ticker: "RSST",
    name: "Return Stacked U.S. Stocks & Managed Futures ETF",
    category: "capital-efficient",
    mandate: "US equity plus a managed-futures overlay as financed notional rather than by selling the base.",
    expenseRatioBp: 99,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: "exploratory",
    verdict:
      "What is established is structure and cost, both from filings. Its 2026-04-30 N-PORT shows SPDR Portfolio S&P 500 at 74.09% of net assets plus E-mini futures at 33.1% — 107.2% equity — with a government money fund at 16.04% as collateral and a trend book running ~294% of net assets in gross notional to deliver ~100% of risk exposure. `delta` is −0.07, so it keeps 100% of the +2.44 pp/yr funding-rule gap and its sleeve hurdle is 0.00 where a standalone managed-futures fund pays the full 2.44. All-in 0.99%, no waiver, and Form N-CEN for the year ended 2026-01-31 reports no recoupment clause. Distribution tax drag 0.32 pp/yr, 4.5 bp of it incremental once the VTI it displaces is subtracted, and 1.3 bp of portfolio return at a 30% notional weight.",
    caution:
      "**Its loading on any trend benchmark has never been measured** — stated three separate times in the owning pages. There is no alpha, no return, no Sharpe and no drawdown for the fund itself, and every trend number in this repository belongs to the AQR index or to DBMF. It does not disclose its financing cost and files 0.00% of interest expense, like every fund in its family. Its 28-month tax window is entirely a rising market; the failure mode is a flat-equity, strong-trend year, which is the year the sleeve exists for. Under three years old.",
    wrapper: {
      delta: -0.07,
      fundingCapturePercent: 100,
      allInCostBp: 99,
      grossNotionalPerDollar: 2.07,
      distributionTaxDragPpYr: 0.32,
      incrementalTaxDragBp: 4.5,
      structureAsOf: asOf("2026-04-30"),
    },
    notionalExposure: [
      { kind: "us-equity", perDollarOfCapital: 1.072 },
      { kind: "trend", perDollarOfCapital: 1.0 },
    ],
    source: capital,
    asOf: READ,
  },
  {
    ticker: "RSSB",
    name: "Return Stacked Global Stocks & Bonds ETF",
    category: "capital-efficient",
    mandate: "Global equity plus 100% Treasury-futures notional. The best-built wrapper on the shelf.",
    expenseRatioBp: 39,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "The clean read, and it verifies the marketing exactly: two equity ETFs at 90.53% of net assets plus one equity-index future at 9.54% is 100.07% equity, and four Treasury futures total 100.33%. The two legs use different N-PORT asset categories, so nothing is commingled and `delta` is −0.0007 at 0.39% all-in with no waiver.",
    caution:
      "Rejected as a second overlay and as a replacement. A bond overlay does not inherit trend's flat drawdown: resampled, it is the deeper drawdown in 49.7% of histories at 30% notional and 70.0% at 100%, against trend's 6.9%; at matched 1.6× gross, 60% trend beats 30% trend plus 30% bonds by +1.40 pp/yr and on Sharpe. Its base leg is *global* equity where the incumbent is US, so no single `delta` scores it for a US-based reader.",
    wrapper: {
      delta: -0.0007,
      fundingCapturePercent: 100,
      allInCostBp: 39,
      grossNotionalPerDollar: 2.004,
      distributionTaxDragPpYr: 0.79,
      incrementalTaxDragBp: null,
      structureAsOf: asOf("2026-04-30"),
    },
    notionalExposure: [
      { kind: "global-equity", perDollarOfCapital: 1.0007 },
      { kind: "treasury-futures", perDollarOfCapital: 1.0033 },
    ],
    source: capital,
    asOf: READ,
  },
  {
    ticker: "NTSX",
    name: "WisdomTree U.S. Efficient Core Fund",
    category: "capital-efficient",
    mandate: "A 90/60 US equity and Treasury-futures stack. The reference case for the funding rule.",
    expenseRatioBp: 20,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Its 2026-03-31 N-PORT reads 90.83% equity plus 63.50% Treasury futures, 1.543× gross, `delta` 0.144 — so it keeps 85.6% of the funding-rule gap and its sleeve hurdle is 0.35 pp/yr. The 0.20% fee converted to overlay notional is 0.315%.",
    caution:
      "It needs 48.3 bp/yr of Treasury excess return over cash at the 15 bp OIS financing benchmark before the overlay contributes anything, and both inputs are forecasts. This row previously said 92.0 bp against a basis measured on special-collateral repo, which is not a rate a fund pays. No loading of any kind has been measured for it.",
    wrapper: {
      delta: 0.144,
      fundingCapturePercent: 85.6,
      allInCostBp: 20,
      grossNotionalPerDollar: 1.543,
      distributionTaxDragPpYr: 0.33,
      incrementalTaxDragBp: null,
      structureAsOf: asOf("2026-03-31"),
    },
    notionalExposure: [
      { kind: "us-equity", perDollarOfCapital: 0.9083 },
      { kind: "treasury-futures", perDollarOfCapital: 0.635 },
    ],
    source: capital,
    asOf: READ,
  },
  {
    ticker: "GDE",
    name: "WisdomTree Efficient Gold Plus Equity Strategy Fund",
    category: "capital-efficient",
    mandate: "US equity with roughly equal gold-futures notional stacked on top.",
    expenseRatioBp: 20,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Its 2026-02-28 N-PORT reads 84.80% equity plus 83.63% gold futures, 1.684× gross, `delta` 0.182, keeping 81.8% of the funding-rule gap. The all-in overlay cost is about 0.60%/yr once ≤40 bp of gold-futures financing is added to the 0.20% fee.",
    caution:
      "As a sleeve it contributes +0.09 pp/yr against an MDE₈₀ of 1.68 — unmeasurable. Its 1.53 pp/yr distribution tax drag is the second largest on the wrapper shelf (1.31 restated at a 24%/15%-federal plus 9.3%-CA investor), and the naive rule 'shelter the highest drag' puts it at the front of the queue, which is exactly backwards.",
    wrapper: {
      delta: 0.182,
      fundingCapturePercent: 81.8,
      allInCostBp: 20,
      grossNotionalPerDollar: 1.684,
      distributionTaxDragPpYr: 1.53,
      incrementalTaxDragBp: null,
      structureAsOf: asOf("2026-02-28"),
    },
    notionalExposure: [
      { kind: "us-equity", perDollarOfCapital: 0.848 },
      { kind: "gold-futures", perDollarOfCapital: 0.8363 },
    ],
    source: capital,
    asOf: READ,
  },
  {
    ticker: "MATE",
    name: "Man Active Trend Enhanced ETF",
    category: "capital-efficient",
    mandate: "An equity ETF base with a futures top-up and a trend overlay. Two mentions in the whole repository.",
    expenseRatioBp: null,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Essentially nothing is known. What the repository has is: an equity ETF leg at 49.8% of net assets plus a futures top-up and a trend sleeve, $36.3m at 2026-02-28, new, an overlay rather than pro rata, and not in Experiment 008. Its fee is `not found` and so is its all-in cost. No `delta` was computed, no loading measured, no tax drag, no survival data, no test of any kind.",
    caution:
      "This is the largest gap in the candidate portfolio, and the missing `delta` is why. A 49.8% base leg sits in the range where a wrapper is *worse* than selling equity outright — the worked warning is that 40% equity with 30% trend gives `delta = 2.0`, and HOLD is the audited instance of that failure at `delta = 0.333`, costing 0.81 pp/yr. A gross-notional figure cannot distinguish that case from the good one. MATE may be in that category and this repository has not checked. The 49.8% below is the only leg filed here; the futures and trend legs are `not found`, so the list is incomplete by construction.",
    wrapper: {
      delta: null,
      fundingCapturePercent: null,
      allInCostBp: null,
      grossNotionalPerDollar: null,
      distributionTaxDragPpYr: null,
      incrementalTaxDragBp: null,
      structureAsOf: asOf("2026-02-28"),
    },
    notionalExposure: [{ kind: "equity", perDollarOfCapital: 0.498 }],
    source: capital,
    asOf: READ,
  },
  {
    ticker: "JPFP",
    name: "JPMorgan Managed Futures Plus ETF",
    category: "capital-efficient",
    mandate: "A stated equity-plus-trend stack that does not exist yet.",
    expenseRatioBp: 59,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "It has not commenced operations (497K of 2026-04-15). A 0.59% unitary fee with no waiver and no recoupment is the only fact that exists. Net assets, holdings and commencement date are all `not found`, so its 100/100 claim rests on the prospectus sentence 'aggregate notional exposure will exceed its net assets' and nothing else.",
    caution:
      "It is the one product that would reorder the wrapper cost ranking outright — a 40 bp saving against RSST's 0.99%, on a line where 40 bp is a third of the whole fee — and it cannot yet be recommended. It is named in three places as a standing review trigger, not as a holding. No `delta`, no loading, no record.",
    wrapper: {
      delta: null,
      fundingCapturePercent: null,
      allInCostBp: 59,
      grossNotionalPerDollar: null,
      distributionTaxDragPpYr: null,
      incrementalTaxDragBp: null,
      structureAsOf: null,
    },
    source: capital,
    asOf: READ,
  },
];

/** Lookup that fails loudly. A page may not quietly render a fund the shelf does not have. */
export function fundByTicker(ticker: string): ShelfFund {
  const found = shelf.find((one) => one.ticker === ticker);
  if (found === undefined) {
    throw new Error(`no shelf record for "${ticker}"; add it with its source rather than inlining a number`);
  }
  return found;
}

export function findFund(ticker: string): ShelfFund | undefined {
  return shelf.find((one) => one.ticker === ticker);
}

export const shelfAsOf = READ;

/** Re-exported so a route can name the owning page without re-declaring a citation. */
export const shelfSources = { products, recommendation, structural, capital, trend } as const;
