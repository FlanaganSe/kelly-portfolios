import type { AsOf, Citation, EvidenceStatus } from "~/content/types";
import { asOf } from "~/content/types";

/**
 * The fund shelf: every product this repository has actually priced or regressed.
 *
 * This is the canonical record for a ticker. Four rules, all of them the reason the
 * file exists rather than a table inside a route:
 *
 * 1. **A loading names its panel.** The same fund reads +0.237 on the emerging panel
 *    and −0.074 on the US one, and a loading printed without its panel is a different
 *    number pretending to be the same one (`docs/research/factor-products.md`).
 * 2. **A loading names its window, and the windows differ.** Every loading here was fitted
 *    on the months that fund had filed, so VTV carries 72 and DFLV 36 — and on the 36
 *    months they share, VTV's HML rises from +0.337 to +0.520 and the published ordering
 *    of the US value shelf comes apart. The window is therefore part of the loading rather
 *    than a note beside it, and there is no `months` field to read without it. Use
 *    `rankLoadings` in `src/lib/loadings.ts`, which refuses a mixed-window set
 *    (`docs/research/loading-comparability-and-wrapper-exposure.md`).
 * 3. **An alpha prints its pedestal and its detection floor.** The model misfits by
 *    −0.55 pp/yr on the US shelf before any fund is examined, and the median alpha this
 *    instrument could detect is about 5 pp/yr against roughly 1.25 pp/yr of true
 *    dispersion. An alpha without those two numbers reads as a finding when it is noise.
 * 4. **Cost is `fee − securities lending`.** The two rankings are different rankings.
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

/**
 * The months a loading was estimated on, `YYYY-MM` inclusive at both ends.
 *
 * A window is part of a loading's identity, not metadata about it: two loadings fitted on
 * different months are answers to different questions, and the length is derived from the
 * window rather than stored beside it so that the two cannot drift apart.
 */
export interface LoadingWindow {
  readonly from: string;
  readonly to: string;
}

export interface FactorLoading {
  readonly factor: "HML" | "SMB" | "RMW" | "CMA" | "UMD" | "TSMOM";
  readonly value: number;
  /** As printed by the owning page, e.g. `[+0.22, +0.46]`. `null` where none was given. */
  readonly interval: string | null;
  readonly panel: Panel;
  /**
   * The estimation window. `null` only where no experiment recorded one — never omitted,
   * and never inferred from a fund's age. Every window here is shorter than one cycle.
   */
  readonly window: LoadingWindow | null;
}

/**
 * What a stacked fund holds per dollar of capital, from its own filing.
 *
 * A wrapper's exposures do not fit `loadings`: they are positions read off an N-PORT, not
 * regression coefficients, and they must never be presented as evidence that the sleeve
 * inside the wrapper delivers anything. `notionalExposure` and `loadings` being separate
 * fields is how a route is stopped from printing "107% equity + 100% trend" where a
 * measured trend loading belongs. RSST now has both, and they say different things: the
 * filing says it holds one dollar of trend notional per dollar of capital, and the
 * regression says +0.681 of that arrived in the return.
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
 * (`docs/research/capital-efficiency-and-breadth.md`, "A wrapper's structure enters exactly
 * once"). The base leg is the sum of every instrument delivering the base, which on a stacked
 * fund includes at least one index future — reading the largest holding alone is the error
 * that page records. None of these fields says
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

/**
 * A fact read off the issuer's own filing or fund page rather than out of this
 * repository's research.
 *
 * Kept in its own field, with its own source and its own access date, so that a reader
 * and a later agent can both tell at a glance which figures were measured here and which
 * were merely read. An issuer fact may state structure, cost and disclosure; it may never
 * stand in for a loading, an alpha or a return this repository has not measured.
 */
export interface IssuerRecord {
  readonly notes: readonly string[];
  readonly source: Citation;
  /** The date the page or filing was read. Fund facts go stale; re-read, do not re-quote. */
  readonly readOn: AsOf;
}

/**
 * A recheck with a date on it, not a condition.
 *
 * Most of what is unknown on this shelf is unknown because no experiment has been run, and
 * that has no due date. A few facts are unknown because a filing does not exist yet, and
 * those expire. Only the second kind belongs here: `on` is the date by which the source
 * should exist, and `what` says what to read and what the answer would change.
 */
export interface ReviewTrigger {
  readonly on: AsOf;
  readonly what: string;
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
  /** Present where a fact is missing because a filing does not exist yet, and will. */
  readonly reviewTrigger?: ReviewTrigger;
  /** Present only where a filing was read. An empty list would claim the fund holds nothing. */
  readonly notionalExposure?: readonly NotionalExposure[];
  /** Present where a primary filing was read directly. Absent means nobody looked. */
  readonly issuer?: IssuerRecord;
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
const alternatives: Citation = {
  label: "The alternative-sleeves audit",
  docPath: "docs/research/alternative-sleeves-audit.md",
};
const capital: Citation = {
  label: "Capital efficiency and breadth",
  docPath: "docs/research/capital-efficiency-and-breadth.md",
};
const trend: Citation = { label: "The marginal value of trend", docPath: "docs/research/trend-marginal-value.md" };
const untestedTilts: Citation = {
  label: "Four tilts the recommendation never priced",
  docPath: "docs/research/untested-tilt-candidates.md",
};
const finalTest: Citation = {
  label: "The final construction, tested",
  docPath: "docs/research/final-construction-test.md",
};

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
    mandate: "The whole US market at capitalisation weight. The yardstick every US result here is measured against.",
    expenseRatioBp: 3,
    securitiesLendingBp: 1.84,
    netCostBp: 1.16,
    turnoverPercent: 3,
    loadings: [
      { factor: "HML", value: 0.0247, interval: null, panel: "us", window: { from: "2020-01", to: "2025-12" } },
    ],
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
    mandate:
      "The S&P 500 at capitalisation weight. Priced as an alternative to VTI and never measured against a model.",
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
    mandate: "The same index as VOO in a 1993 trust, and the fund the real cost of lending is measured on.",
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
    mandate: "Big cheap US companies, weighted by size, for 0.03% a year. Part of the yardstick rather than a bet.",
    expenseRatioBp: 3,
    securitiesLendingBp: 0.3,
    netCostBp: 2.7,
    turnoverPercent: 8,
    loadings: [
      {
        factor: "HML",
        value: 0.337,
        interval: "[+0.225, +0.471]",
        panel: "us",
        window: { from: "2020-01", to: "2025-12" },
      },
    ],
    alphaPpYr: -2.6,
    alphaDetectionFloorPpYr: 3.28,
    pedestalPpYr: US_PEDESTAL,
    status: "rejected",
    verdict:
      "Delivers HML +0.337 and is still rejected on clause (c): a +2.57 pp/yr shortfall to a cheap combination that is 78% VTI plus 22% VB. Read that as 'value can be approximated with VTI and VB', not as a defect in the fund.",
    caution:
      "It is inside the basis every other US product is scored against, so its own rejection is partly a statement about the test.",
    source: products,
    asOf: READ,
  },
  {
    ticker: "AVUV",
    name: "Avantis U.S. Small Cap Value ETF",
    category: "us-value",
    mandate: "Small cheap US companies that also make money. The strongest lean toward cheap on the US small shelf.",
    expenseRatioBp: 25,
    securitiesLendingBp: 0.46,
    netCostBp: 24.54,
    turnoverPercent: 6,
    loadings: [
      {
        factor: "HML",
        value: 0.537,
        interval: "[+0.43, +0.64]",
        panel: "us",
        window: { from: "2020-01", to: "2025-12" },
      },
      { factor: "SMB", value: 0.88, interval: null, panel: "us", window: { from: "2020-01", to: "2025-12" } },
    ],
    alphaPpYr: 0.39,
    alphaDetectionFloorPpYr: 3.64,
    pedestalPpYr: US_PEDESTAL,
    status: "exploratory",
    verdict:
      "The largest implementation shortfall on the shelf, −4.92 pp/yr on the frozen basis and −4.23 on a cheap style grid that can express small value: the best in-sample combination of VTI, VUG, VTV and VB could not get within four points a year of it.",
    caution:
      "Its SMB leg of +0.88 is the largest of any US value product here and the size premium is not signable on any panel (+0.33 against a 2.47 pp/yr floor). At a 20% weight it buys +43.1 bp for 312 bp of tracking error and reaches 90% confidence in 86 years. Against a portfolio that already holds a US value line it adds nothing: its active leg over VTI is +0.455 correlated with the recommended portfolio's own, and 87% of what it delivers beyond VTV is size.",
    issuer: {
      notes: [
        "0.25% total annual fund operating expenses and 6% portfolio turnover in the most recent fiscal year, per its summary prospectus dated 2025-12-31.",
        "Five-year return before taxes 14.12% and after taxes on distributions 13.68% to 2024-12, a drag of 0.44 pp/yr against VTI's 0.42: parity.",
        "Median net securities-lending income of 0.46 bp/yr across six fiscal years of Form N-CEN, 2020-08-31 to 2025-08-31, so its net cost is 24.54 bp. Lending barely moves it: US small value is not what short sellers borrow.",
      ],
      source: {
        label: "Avantis U.S. Small Cap Value ETF, Form 497K dated 2025-12-31",
        docPath: "docs/research/untested-tilt-candidates.md",
        href: "https://www.sec.gov/Archives/edgar/data/1710607/000171060725000416/acetftavuv497k.htm",
      },
      readOn: asOf("2026-08-23"),
    },
    source: recommendation,
    asOf: asOf("2026-08-23"),
  },
  {
    ticker: "DFUV",
    name: "Dimensional US Marketwide Value ETF",
    category: "us-value",
    mandate: "Big cheap US companies. The most growth per unit of drift of any US value fund except AVLV.",
    expenseRatioBp: 21,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 5,
    loadings: [
      {
        factor: "HML",
        value: 0.515,
        interval: "[+0.35, +0.71]",
        panel: "us",
        window: { from: "2022-06", to: "2025-12" },
      },
      { factor: "SMB", value: 0.12, interval: null, panel: "us", window: { from: "2022-06", to: "2025-12" } },
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
    mandate: "Big cheap US companies, on the shortest run of history of any fund audited here.",
    expenseRatioBp: 21,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 5,
    loadings: [
      {
        factor: "HML",
        value: 0.637,
        interval: "[+0.42, +0.82]",
        panel: "us",
        window: { from: "2023-01", to: "2025-12" },
      },
      { factor: "SMB", value: -0.05, interval: null, panel: "us", window: { from: "2023-01", to: "2025-12" } },
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
    mandate: "Small cheap US companies.",
    expenseRatioBp: 30,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 9,
    loadings: [
      {
        factor: "HML",
        value: 0.442,
        interval: "[+0.34, +0.64]",
        panel: "us",
        window: { from: "2022-03", to: "2025-12" },
      },
      { factor: "SMB", value: 0.85, interval: null, panel: "us", window: { from: "2022-03", to: "2025-12" } },
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
    mandate: "Small cheap US companies, on the longest run of history of any Dimensional fund here.",
    expenseRatioBp: 28,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 9,
    loadings: [
      {
        factor: "HML",
        value: 0.433,
        interval: "[+0.37, +0.55]",
        panel: "us",
        window: { from: "2021-07", to: "2025-12" },
      },
      { factor: "SMB", value: 0.83, interval: null, panel: "us", window: { from: "2021-07", to: "2025-12" } },
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
    mandate: "Cheap US companies, rebuilt to an index. The strongest lean toward cheap on the whole US shelf.",
    expenseRatioBp: 35,
    securitiesLendingBp: 1.13,
    netCostBp: 33.87,
    turnoverPercent: 42,
    loadings: [
      {
        factor: "HML",
        value: 0.71,
        interval: "[+0.53, +0.83]",
        panel: "us",
        window: { from: "2020-01", to: "2025-12" },
      },
      { factor: "SMB", value: 0.2, interval: null, panel: "us", window: { from: "2020-01", to: "2025-12" } },
    ],
    alphaPpYr: -2.8,
    alphaDetectionFloorPpYr: 6.5,
    pedestalPpYr: US_PEDESTAL,
    status: "rejected",
    verdict:
      "The deepest US value exposure on the shelf and still a subtraction. Over VTV on 78 months (2019-10\u20262026-03) it delivers HML +0.369 [+0.249, +0.490] and SMB +0.199, but also RMW \u22120.204 [\u22120.361, \u22120.047] and UMD \u22120.173 [\u22120.337, \u22120.008]: the value it buys is partly paid for by selling momentum. Net of a 33.87 bp cost and 42%/yr of turnover against VTV\u2019s 8%, replacing VTV with it at 15% changes portfolio return by about \u22120.10% a year, and it is negative under all four of this repository\u2019s premium scenarios.",
    caution:
      "42%/yr of turnover, the highest of any US value product audited and five times the incumbent\u2019s \u2014 its sort is an index reconstitution, which is exactly the case Experiment 007\u2019s 20\u201340% assumption was right about. The tax objection, however, is false: its distribution drag is 0.62 pp/yr against VTV\u2019s 0.67 over the same five years. Its 106 constituents are weighted by value score rather than by capitalisation, so it is a concentrated active position wearing an index label.",
    issuer: {
      notes: [
        "0.35% management fee, no other expenses, and 42% portfolio turnover in the most recent fiscal year, per its summary prospectus dated 2025-08-28.",
        "Five-year return before taxes 7.99% and after taxes on distributions 7.37% to 2024-12, a drag of 0.62 pp/yr \u2014 below VTV\u2019s 0.67 over the same period.",
        "Median net securities-lending income of 1.13 bp/yr across eight fiscal years of Form N-CEN, 2019-04-30 to 2026-04-30. The fiscal-2026 filing reports 26.65 bp, eight times any prior year, and is an outlier the median deliberately does not follow.",
        "As of 2025-06-30 the underlying index held 106 constituents drawn from the S&P 500, weighted by value score, with market capitalisations from $5.9bn to $464.6bn.",
      ],
      source: {
        label: "Invesco S&P 500 Pure Value ETF, Form 497K dated 2025-08-28",
        docPath: "docs/research/final-construction-test.md",
        href: "https://www.sec.gov/Archives/edgar/data/1209466/000119312525190419/d56632d497k.htm",
      },
      readOn: asOf("2026-08-23"),
    },
    source: finalTest,
    asOf: asOf("2026-08-23"),
  },
  {
    ticker: "VBR",
    name: "Vanguard Morningstar Small-Cap Value ETF",
    category: "us-value",
    mandate:
      "The cheap index fund for small cheap US companies, and the optional holding the reference portfolio names.",
    expenseRatioBp: 5,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 25,
    loadings: [
      {
        factor: "HML",
        value: 0.41,
        interval: "[+0.322, +0.480]",
        panel: "us",
        window: { from: "2020-01", to: "2025-12" },
      },
      { factor: "SMB", value: 0.56, interval: null, panel: "us", window: { from: "2020-01", to: "2025-12" } },
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
    mandate: "Big cheap US companies that also make money, and it trades very little.",
    expenseRatioBp: 15,
    securitiesLendingBp: 0.06,
    netCostBp: 14.94,
    turnoverPercent: 7,
    loadings: [
      {
        factor: "HML",
        value: 0.322,
        interval: "[+0.22, +0.46]",
        panel: "us",
        window: { from: "2021-10", to: "2025-12" },
      },
      { factor: "SMB", value: 0.12, interval: null, panel: "us", window: { from: "2021-10", to: "2025-12" } },
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
    ticker: "QVAL",
    name: "Alpha Architect U.S. Quantitative Value ETF",
    category: "us-value",
    mandate: "Cheap US companies, only about fifty of them, rebuilt every quarter.",
    expenseRatioBp: 28,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 332,
    loadings: [
      {
        factor: "HML",
        value: 0.503,
        interval: "[+0.26, +0.74]",
        panel: "us",
        window: { from: "2021-10", to: "2026-03" },
      },
      {
        factor: "SMB",
        value: 0.409,
        interval: "[+0.15, +0.67]",
        panel: "us",
        window: { from: "2021-10", to: "2026-03" },
      },
      {
        factor: "RMW",
        value: 0.396,
        interval: "[+0.12, +0.67]",
        panel: "us",
        window: { from: "2021-10", to: "2026-03" },
      },
    ],
    alphaPpYr: -0.96,
    alphaDetectionFloorPpYr: 8.52,
    pedestalPpYr: US_PEDESTAL,
    status: "rejected",
    verdict:
      "A genuinely deep value tilt destroyed by its own trading. It files 332%/yr of portfolio turnover against VTI's 3%, which costs 3.54 to 5.86 pp/yr at the repository's 1.0-to-1.7 coefficient against a gross factor gain of about 1.1 pp/yr. At a 5% weight it is the only candidate whose portfolio effect this data can resolve, and it resolves to about -0.30% a year.",
    caution:
      "Its loadings are stated over its own filings and its incumbent's, not over the shelf's other value products: EDGAR lists no Form N-PORT for the quarter ending 2021-09-30, so its history has a three-month hole and only the 54 gapless months after it are usable. Its active leg is +0.754 correlated with AVUV's, so it duplicates a position rather than adding one.",
    issuer: {
      notes: [
        "0.28% total annual fund operating expenses, management fee restated to the current rate, with no 12b-1 fee and no other expenses, per its summary prospectus dated 2026-02-01.",
        "Portfolio turnover 332% of average portfolio value in the most recent fiscal year - the highest of any fund on this shelf by a factor of three.",
        "Commenced operations 2014-10-21 against the Solactive GBS United States 1000 Index. Ten-year return before taxes 10.02% and after taxes on distributions 9.59% to 2025-12, a distribution drag of 0.43 pp/yr.",
      ],
      source: {
        label: "Alpha Architect U.S. Quantitative Value ETF, Form 497K dated 2026-02-01",
        docPath: "docs/research/untested-tilt-candidates.md",
        href: "https://www.sec.gov/Archives/edgar/data/1592900/000159290026000383/alphaarchitectusquantitati.htm",
      },
      readOn: asOf("2026-08-23"),
    },
    source: untestedTilts,
    asOf: asOf("2026-08-23"),
  },
  {
    ticker: "AVSC",
    name: "Avantis U.S. Small Cap Equity ETF",
    category: "us-small",
    mandate: "Small US companies. It delivers more small-company exposure than anything else on the US shelf.",
    expenseRatioBp: 25,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 5,
    loadings: [
      {
        factor: "SMB",
        value: 1.058,
        interval: "[+0.98, +1.11]",
        panel: "us",
        window: { from: "2022-02", to: "2025-12" },
      },
      { factor: "HML", value: 0.243, interval: null, panel: "us", window: { from: "2022-02", to: "2025-12" } },
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
    mandate: "Small US companies.",
    expenseRatioBp: 26,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 6,
    loadings: [
      {
        factor: "SMB",
        value: 0.816,
        interval: "[+0.74, +0.91]",
        panel: "us",
        window: { from: "2021-07", to: "2025-12" },
      },
      { factor: "HML", value: 0.241, interval: null, panel: "us", window: { from: "2021-07", to: "2025-12" } },
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
    mandate: "Plain small US companies for 0.03% a year. Part of the yardstick rather than a holding.",
    expenseRatioBp: 3,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [
      {
        factor: "SMB",
        value: 0.599,
        interval: "[+0.516, +0.684]",
        panel: "us",
        window: { from: "2020-01", to: "2025-12" },
      },
    ],
    alphaPpYr: -2.97,
    alphaDetectionFloorPpYr: 3.16,
    pedestalPpYr: US_PEDESTAL,
    status: "rejected",
    verdict:
      "Rejected on clause (c) at a +2.89 pp/yr shortfall, its cheap replication being 0.733 VTI plus 0.267 VTV. Its 2.72 bp round trip is nearly a year of expense ratio and is the binding constraint on rebalancing frequency.",
    caution:
      "Like VTV, it sits inside the basis it is scored against, so the rejection reads as 'small-cap is approximable', not as a defect.",
    issuer: {
      notes: [
        'The name is verified, not inferred. Vanguard Index Funds\' supplement of 2026-07-29 enumerates all ten renamed funds and gives this one explicitly: "Vanguard Small-Cap Index Fund → Vanguard Morningstar Small-Cap Index Fund → Vanguard Morningstar Small-Cap ETF". The same table carries VTI and VBR.',
        'Its target index was renamed on the same date, CRSP US Small Cap Index to Morningstar US Small Cap Index, and the filing states that "Each Fund\'s investment objective, strategies, and polices remain unchanged." The rename is a rebranding after Morningstar acquired CRSP; no loading on this shelf is affected by it.',
      ],
      source: {
        label: "Vanguard Index Funds, 497 supplement dated 2026-07-29",
        docPath: "docs/research/factor-products.md",
        href: "https://www.sec.gov/Archives/edgar/data/36405/000003640526000386/f45788d1.htm",
      },
      readOn: asOf("2026-08-22"),
    },
    source: products,
    asOf: asOf("2026-08-22"),
  },
  // -------------------------------------------------------------------------
  // US momentum and quality. Momentum is excluded on turnover and on a 4.98 pp/yr
  // detection floor; quality is `rejected` and closed on public data (decision 0005).
  // -------------------------------------------------------------------------
  {
    ticker: "MTUM",
    name: "iShares MSCI USA Momentum Factor ETF",
    category: "us-momentum",
    mandate: "Big US companies whose shares have been going up. For years the only one you could buy; now one of six.",
    expenseRatioBp: 15,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 116,
    loadings: [
      {
        factor: "UMD",
        value: 0.444,
        interval: "[+0.277, +0.562]",
        panel: "us",
        window: { from: "2020-01", to: "2025-12" },
      },
    ],
    alphaPpYr: -2.95,
    alphaDetectionFloorPpYr: 7.34,
    pedestalPpYr: US_PEDESTAL,
    status: "rejected",
    verdict:
      "Delivers UMD +0.444 and is rejected anyway on a +1.10 pp/yr shortfall to a cheap combination. That it was 'the entire momentum shelf' was a property of Experiment 002's census frame, not of the market.",
    caution:
      "Its 7.34 pp/yr detection floor is the worst on the US shelf, so its −2.95 alpha means nothing either way. Turnover is now measured and it is what decides the fund: 116%/yr against VTI's 3% costs 1.25 to 2.06 pp/yr, against a gross exposure gain of +1.78 pp/yr on a US momentum premium of +4.19 that is itself under a 7.27 pp/yr floor. The tax objection, by contrast, is false — its filed distribution drag is 11 bp/yr *below* VTI's.",
    issuer: {
      notes: [
        "0.15% total annual fund operating expenses, no 12b-1 fee and no other expenses, per its summary prospectus dated 2025-11-28.",
        "Portfolio turnover 116% of average portfolio value in the most recent fiscal year.",
        "Five-year return before taxes 11.77% and after taxes on distributions 11.46% to 2024-12, a distribution drag of 0.31 pp/yr against VTI's 0.42 over the same period. The ETF in-kind redemption shield survives this fund's turnover on the distribution measure.",
      ],
      source: {
        label: "iShares MSCI USA Momentum Factor ETF, Form 497K dated 2025-11-28",
        docPath: "docs/research/untested-tilt-candidates.md",
        href: "https://www.sec.gov/Archives/edgar/data/1100663/000119312525302119/d28465d497k.htm",
      },
      readOn: asOf("2026-08-23"),
    },
    source: products,
    asOf: asOf("2026-08-23"),
  },
  {
    ticker: "SPMO",
    name: "Invesco S&P 500 Momentum ETF",
    category: "us-momentum",
    mandate: "Big US companies whose shares have been going up, cheaper than MTUM and trading far less.",
    expenseRatioBp: 13,
    securitiesLendingBp: 0.07,
    netCostBp: 12.93,
    turnoverPercent: 44,
    loadings: [{ factor: "UMD", value: 0.414, interval: null, panel: "us", window: null }],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: US_PEDESTAL,
    status: "rejected",
    verdict:
      "Its facts are now read and they favour it over MTUM on every knowable dimension — 13 bp against 15, 44%/yr of turnover against 116%, 12.93 bp of net cost, and a distribution tax drag of 0.37 pp/yr against VTI\u2019s 0.42. Over VTI it delivers UMD +0.395 [+0.281, +0.508] on 78 months (2019-10\u20262026-03). At a 5% weight it still changes portfolio return by about +0.02% a year, plausibly \u22120.14% to +0.18%.",
    caution:
      "The published +0.414 carries NO WINDOW and must not be compared with any other fund\u2019s loading; the +0.395 above is fitted here on a stated window and is the delivered exposure over VTI, not the fund\u2019s own loading. The exposure it buys sits on a US momentum premium of +4.19 pp/yr against a 7.27 pp/yr detection floor, and its active leg is +0.626 correlated with IDMO\u2019s \u2014 a tighter overlap than MTUM\u2019s +0.554, so a portfolio already holding international momentum buys less than it looks.",
    issuer: {
      notes: [
        "0.13% management fee, no other expenses, and 44% portfolio turnover in the most recent fiscal year, per its summary prospectus dated 2025-12-19.",
        "Five-year return before taxes 19.23% and after taxes on distributions 18.86% to 2024-12, a drag of 0.37 pp/yr against VTI\u2019s 0.42.",
        "Median net securities-lending income of 0.07 bp/yr across seven fiscal years of Form N-CEN, 2019-08-31 to 2025-08-31 \u2014 the lowest on this shelf, so its 13 bp fee is very nearly its net cost.",
        "Approximately 100 constituents from the S&P 500, weighted by market capitalisation times momentum score, and the fund is non-diversified.",
      ],
      source: {
        label: "Invesco S&P 500 Momentum ETF, Form 497K dated 2025-12-19",
        docPath: "docs/research/final-construction-test.md",
        href: "https://www.sec.gov/Archives/edgar/data/1378872/000119312525325661/d54028d497k.htm",
      },
      readOn: asOf("2026-08-23"),
    },
    source: finalTest,
    asOf: asOf("2026-08-23"),
  },
  {
    ticker: "QUAL",
    name: "iShares MSCI USA Quality Factor ETF",
    category: "us-quality",
    mandate: "US companies that actually make money.",
    expenseRatioBp: 15,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [
      {
        factor: "RMW",
        value: 0.186,
        interval: "[+0.101, +0.247]",
        panel: "us",
        window: { from: "2020-01", to: "2025-12" },
      },
    ],
    alphaPpYr: -2.15,
    alphaDetectionFloorPpYr: 3.13,
    pedestalPpYr: US_PEDESTAL,
    status: "rejected",
    verdict: "Rejected on clause (c) at a +1.14 pp/yr shortfall, on an RMW loading of +0.186.",
    caution:
      "The exposure is not purchasable at this threshold anywhere on the shelf — nine quality products and the largest RMW loading is +0.228 — and the premium behind it is rejected and closed on public data (decision 0005). A product's own quality is irrelevant when the premium cannot be signed.",
    source: products,
    asOf: READ,
  },
  {
    ticker: "SPHQ",
    name: "Invesco S&P 500 Quality ETF",
    category: "us-quality",
    mandate: "US companies that actually make money.",
    expenseRatioBp: 15,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [
      {
        factor: "RMW",
        value: 0.176,
        interval: "[+0.079, +0.296]",
        panel: "us",
        window: { from: "2020-01", to: "2025-12" },
      },
    ],
    alphaPpYr: -0.56,
    alphaDetectionFloorPpYr: 3.75,
    pedestalPpYr: US_PEDESTAL,
    status: "unresolved",
    verdict:
      "Unresolved: its RMW interval straddles the 0.15 bar, so the window could not say whether the exposure is there. Shortfall −0.13.",
    caution: "RMW is closed on public data. Nothing this fund does can reopen it.",
    source: products,
    asOf: READ,
  },
  {
    ticker: "DUHP",
    name: "Dimensional US High Profitability ETF",
    category: "us-quality",
    mandate: "US companies that actually make money, from the sponsor whose value funds all reach exploratory.",
    expenseRatioBp: 20,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [
      {
        factor: "RMW",
        value: 0.179,
        interval: "[+0.03, +0.29]",
        panel: "us",
        window: { from: "2022-03", to: "2025-12" },
      },
    ],
    alphaPpYr: -1.43,
    alphaDetectionFloorPpYr: 4.46,
    pedestalPpYr: US_PEDESTAL,
    status: "unresolved",
    verdict: "Unresolved on the same clause as SPHQ: the interval contains 0.15 on 46 months. Shortfall −0.11.",
    caution: "The only Dimensional product on the US shelf that does not reach exploratory, and the factor is why.",
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
    mandate: "Developed markets outside the US, weighted by size. The thing every foreign fund here is priced against.",
    expenseRatioBp: 3,
    securitiesLendingBp: 3.3,
    netCostBp: -0.3,
    turnoverPercent: 4,
    loadings: [
      {
        factor: "HML",
        value: 0.015,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      { factor: "UMD", value: 0.006, interval: null, panel: "developed-ex-us", window: null },
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
    mandate: "Big cheap companies in developed markets outside the US, and the strongest such lean audited here.",
    expenseRatioBp: 27,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 6,
    loadings: [
      {
        factor: "HML",
        value: 0.662,
        interval: "[+0.53, +0.85]",
        panel: "developed-ex-us",
        window: { from: "2021-10", to: "2025-12" },
      },
      {
        factor: "SMB",
        value: -0.114,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2021-10", to: "2025-12" },
      },
      {
        factor: "RMW",
        value: -0.001,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2021-10", to: "2025-12" },
      },
      {
        factor: "CMA",
        value: -0.122,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2021-10", to: "2025-12" },
      },
      {
        factor: "UMD",
        value: 0.016,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2021-10", to: "2025-12" },
      },
    ],
    alphaPpYr: -4.11,
    alphaDetectionFloorPpYr: 3.52,
    pedestalPpYr: DEVELOPED_PEDESTAL,
    status: "exploratory",
    verdict:
      "The strongest tilt this repository has priced: at an 8% substitution out of VEA it is the only line whose edge, +27.1 bp, sits above its own 30-year detection floor of 21.6 bp.",
    caution:
      "Its own alpha is −4.11 pp/yr against a 3.52 pp/yr floor — measurably negative, and one of four ex-US large-value funds reading −2.2 to −4.1. Charging that alpha takes the same tilt from +27.1 bp to −8.2 bp.",
    issuer: {
      notes: [
        "$19.32bn of net assets at 2026-04-30 from its own Form N-PORT, which marks the filing not final. Size is the one risk this fund does not carry.",
        "0.27% total annual fund operating expenses — a 0.25% management fee plus 0.02% of other expenses — with no waiver and no expense cap, per its summary prospectus dated 2026-02-28.",
      ],
      source: {
        label: "Dimensional International Value ETF, Form N-PORT for 2026-04-30",
        docPath: "docs/research/portfolio-recommendation.md",
        href: "https://www.sec.gov/Archives/edgar/data/1816125/000100472626005680/primary_doc.xml",
      },
      readOn: asOf("2026-08-22"),
    },
    source: recommendation,
    asOf: asOf("2026-08-22"),
  },
  {
    ticker: "AVIV",
    name: "Avantis International Large Cap Value ETF",
    category: "intl-value",
    mandate: "Big cheap companies outside the US, and the one of the five that drifts least from its index.",
    expenseRatioBp: 25,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 11,
    loadings: [
      {
        factor: "HML",
        value: 0.489,
        interval: "[+0.36, +0.63]",
        panel: "developed-ex-us",
        window: { from: "2021-10", to: "2025-12" },
      },
      {
        factor: "SMB",
        value: -0.285,
        interval: "[−0.47, −0.13]",
        panel: "developed-ex-us",
        window: { from: "2021-10", to: "2025-12" },
      },
      {
        factor: "RMW",
        value: -0.031,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2021-10", to: "2025-12" },
      },
      {
        factor: "CMA",
        value: -0.182,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2021-10", to: "2025-12" },
      },
      {
        factor: "UMD",
        value: -0.109,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2021-10", to: "2025-12" },
      },
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
    mandate: "Big cheap companies outside the US, on the longest run of history of the four.",
    expenseRatioBp: 31,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 16,
    loadings: [
      {
        factor: "HML",
        value: 0.475,
        interval: "[+0.33, +0.60]",
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "SMB",
        value: -0.121,
        interval: "[−0.32, +0.07]",
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "RMW",
        value: 0.053,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "CMA",
        value: 0.02,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "UMD",
        value: -0.083,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
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
    mandate: "Big cheap companies outside the US, tracking an index, and part of the yardstick.",
    expenseRatioBp: 31,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 23,
    loadings: [
      {
        factor: "HML",
        value: 0.368,
        interval: "[+0.26, +0.49]",
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "SMB",
        value: -0.16,
        interval: "[−0.31, −0.06]",
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "RMW",
        value: -0.006,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "CMA",
        value: 0.17,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "UMD",
        value: -0.069,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
    ],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 2.22,
    pedestalPpYr: DEVELOPED_PEDESTAL,
    status: "exploratory",
    verdict:
      "Shortfall −1.19 frozen and −1.20 expressive, and it survives every basis except the placebo that hands a second EAFE value fund to a fund that *is* EAFE value — a change in what is measured, not in the fund.",
    caution:
      "Only its shrunk alpha, −1.58 pp/yr against a 2.22 floor, was published; the raw figure is not in this repository, so alphaPpYr is null rather than the shrunk number wearing a raw label.",
    source: products,
    asOf: READ,
  },
  {
    ticker: "AVDV",
    name: "Avantis International Small Cap Value ETF",
    category: "intl-small-value",
    mandate: "Small cheap companies in developed markets outside the US. The only fund that can buy you that corner.",
    expenseRatioBp: 36,
    securitiesLendingBp: 5.97,
    netCostBp: 30.03,
    turnoverPercent: 4,
    loadings: [
      {
        factor: "HML",
        value: 0.51,
        interval: "[+0.32, +0.78]",
        panel: "developed-ex-us",
        window: { from: "2019-10", to: "2025-12" },
      },
      {
        factor: "SMB",
        value: 0.671,
        interval: "[+0.46, +0.84]",
        panel: "developed-ex-us",
        window: { from: "2019-10", to: "2025-12" },
      },
      {
        factor: "RMW",
        value: 0.386,
        interval: "[+0.12, +0.65]",
        panel: "developed-ex-us",
        window: { from: "2019-10", to: "2025-12" },
      },
      {
        factor: "CMA",
        value: -0.114,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2019-10", to: "2025-12" },
      },
      {
        factor: "UMD",
        value: 0.008,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2019-10", to: "2025-12" },
      },
    ],
    alphaPpYr: 2.47,
    alphaDetectionFloorPpYr: 3.96,
    pedestalPpYr: DEVELOPED_PEDESTAL,
    status: "exploratory",
    verdict:
      "Keeps a −4.58 pp/yr shortfall under all seven bases, including the ones containing itself, because no other column can express developed-ex-US small value. It files 4%/yr of turnover, the lowest of any factor product in either audit.",
    caution:
      "The only value fund on the shelf carrying two side loads whose intervals exclude zero: SMB +0.671 on a premium of +0.49 [−1.44, +2.44], and RMW +0.386 on a rejected factor. It is fourth or fifth of five on growth per unit of tracking error in every window. Its alpha is a window artefact: +2.47 on 45 months, +0.55 on 75 and +1.84 on 55, against floors of 3.96 to 4.64. None of the three is evidence and no verdict may rest on one.",
    issuer: {
      notes: [
        "0.36% total annual fund operating expenses and 4% portfolio turnover in the most recent fiscal year — the lowest turnover of any factor product on this shelf — per its summary prospectus dated 2025-12-31.",
        "Five-year return before taxes 6.35% and after taxes on distributions 5.57% to 2024-12, a drag of 0.78 pp/yr against VXUS's 0.79 over the same period: parity with the fund it would displace.",
        "Median net securities-lending income of 5.97 bp/yr across six fiscal years of Form N-CEN, 2020-08-31 to 2025-08-31, so its net cost is 30.03 bp rather than 36 \u2014 the largest fee-to-cost gap of any tilt on this shelf.",
      ],
      source: {
        label: "Avantis International Small Cap Value ETF, Form 497K dated 2025-12-31",
        docPath: "docs/research/untested-tilt-candidates.md",
        href: "https://www.sec.gov/Archives/edgar/data/1710607/000171060725000402/acetftavdv497k.htm",
      },
      readOn: asOf("2026-08-23"),
    },
    source: untestedTilts,
    asOf: asOf("2026-08-23"),
  },
  {
    ticker: "DISV",
    name: "Dimensional International Small Cap Value ETF",
    category: "intl-small-value",
    mandate: "Small cheap companies in developed markets outside the US.",
    expenseRatioBp: 42,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 8,
    loadings: [
      {
        factor: "HML",
        value: 0.495,
        interval: "[+0.36, +0.64]",
        panel: "developed-ex-us",
        window: { from: "2022-04", to: "2025-12" },
      },
      {
        factor: "SMB",
        value: 0.431,
        interval: "[+0.23, +0.65]",
        panel: "developed-ex-us",
        window: { from: "2022-04", to: "2025-12" },
      },
      {
        factor: "RMW",
        value: 0.049,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2022-04", to: "2025-12" },
      },
      {
        factor: "CMA",
        value: -0.005,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2022-04", to: "2025-12" },
      },
      {
        factor: "UMD",
        value: -0.088,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2022-04", to: "2025-12" },
      },
    ],
    alphaPpYr: -0.21,
    alphaDetectionFloorPpYr: 3.98,
    pedestalPpYr: DEVELOPED_PEDESTAL,
    status: "exploratory",
    verdict:
      "The largest basis effect on the ex-US shelf: its shortfall goes from −2.89 to +0.05 once a small-value column exists, on a replication that puts 69% of its weight on AVDV. It keeps exploratory only because +0.05 sits under the 0.50 threshold.",
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
      {
        factor: "HML",
        value: -0.032,
        interval: "[−0.16, +0.14]",
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "SMB",
        value: 0.551,
        interval: "[+0.43, +0.64]",
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "RMW",
        value: 0.041,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "CMA",
        value: 0.036,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "UMD",
        value: -0.024,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
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
    mandate:
      "Small companies in developed markets outside the US. The largest exposure any foreign fund here sets out to deliver.",
    expenseRatioBp: null,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [
      {
        factor: "SMB",
        value: 0.856,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2019-07", to: "2025-12" },
      },
    ],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 2.5,
    pedestalPpYr: DEVELOPED_PEDESTAL,
    status: "rejected",
    verdict:
      "Rejected on clause (c) at +1.24 pp/yr under all seven bases — and the rejection turns on one month. GWX files from 2019-07, which only three basis constituents cover, so its 'cheap replication' is VEA at weight 1.000: a large-cap fund standing in for a small-cap one.",
    caution:
      "Trim that single uncovered month and the shortfall falls to between +0.00 and +0.39, all under the threshold. The published verdict stands because the specification was frozen, but it must be read as 'the comparator did not exist for one of its months'. Its fee was never read.",
    source: products,
    asOf: READ,
  },
  {
    ticker: "IDMO",
    name: "Invesco S&P International Developed Momentum ETF",
    category: "intl-momentum",
    mandate:
      "Foreign developed shares that have been going up, and the one such reward that clears what the test could see.",
    expenseRatioBp: 25,
    securitiesLendingBp: 2.41,
    netCostBp: 22.59,
    turnoverPercent: 105,
    loadings: [
      {
        factor: "UMD",
        value: 0.54,
        interval: "[+0.39, +0.71]",
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "HML",
        value: 0.218,
        interval: "[−0.13, +0.52]",
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "SMB",
        value: -0.164,
        interval: "[−0.34, +0.04]",
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "RMW",
        value: 0.04,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "CMA",
        value: -0.394,
        interval: "[−0.72, −0.06]",
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
    ],
    alphaPpYr: 0.11,
    alphaDetectionFloorPpYr: 5.34,
    pedestalPpYr: DEVELOPED_PEDESTAL,
    status: "exploratory",
    verdict:
      "Delivers +0.535 of UMD over VEA on a signable premium (+8.35 [+4.82, +11.66] against a 5.21 floor), worth +4.47 pp/yr gross and +2.53 net per dollar of sleeve. It survives all seven bases at −5.43 to −5.18, and at 0.25% it is what causes IMTM to be rejected.",
    caution:
      "Excluded from the reference portfolio anyway. It files 105%/yr of turnover against VEA's 4%, so cost takes 43% of the gross exposure at k = 1.7 (28% at k = 1.0), and it carries CMA −0.394 on a rejected factor.",
    source: products,
    asOf: READ,
  },
  {
    ticker: "IMTM",
    name: "iShares MSCI Intl Momentum Factor ETF",
    category: "intl-momentum",
    mandate: "Foreign developed shares that have been going up, and the dearer of the two on the shelf.",
    expenseRatioBp: 30,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [
      {
        factor: "UMD",
        value: 0.505,
        interval: "[+0.44, +0.59]",
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "HML",
        value: 0.088,
        interval: "[−0.04, +0.21]",
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "SMB",
        value: -0.306,
        interval: "[−0.44, −0.16]",
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "RMW",
        value: -0.012,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
      {
        factor: "CMA",
        value: -0.241,
        interval: null,
        panel: "developed-ex-us",
        window: { from: "2019-08", to: "2025-12" },
      },
    ],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 3.81,
    pedestalPpYr: DEVELOPED_PEDESTAL,
    status: "rejected",
    verdict:
      "Exploratory at −2.31 on the frozen basis and rejected at +0.91 once the basis can hold IDMO at 0.25%, which takes 57.5% of the fitted weight. The loss is a cheaper fund in its own cell, which is exactly what clause (c) exists to find.",
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
    mandate: "Emerging markets weighted by size, and the yardstick every emerging-market fund here is read against.",
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
    mandate: "The same emerging-market claim as VWO, priced only as plain market exposure.",
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
    mandate: "Cheap emerging-market shares, in the region where cheapness has paid the most in our data.",
    expenseRatioBp: 36,
    securitiesLendingBp: 6.79,
    netCostBp: 29.21,
    turnoverPercent: null,
    loadings: [
      { factor: "HML", value: 0.237, interval: null, panel: "emerging", window: { from: "2021-10", to: "2025-12" } },
      { factor: "HML", value: -0.074, interval: null, panel: "us", window: { from: "2021-10", to: "2025-12" } },
    ],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 4.48,
    pedestalPpYr: EMERGING_PEDESTAL,
    status: "unresolved",
    verdict:
      "Unresolved on window length, not on failure: 51 months put its interval across the 0.15 bar. The verdict is basis-invariant — no comparator, however expressive, can move an emerging product to exploratory, because clause (a) reads the loading and unresolved reads its interval and neither reads the basis.",
    caution:
      "The panel does the heaviest work here: the same fund reads −0.074 on the US panel, which would flip the sign of the only evidence that the emerging value premium is purchasable at all. At 36 bp it costs 27 bp a year more than IEMG's 9 bp, which is the incremental cost the tilt has to clear before its loading matters — and its loading is the one this shelf cannot sign. Its net cost is 29.21 bp: 36 bp less a median 6.79 bp of securities lending across four fiscal years of Form N-CEN, 2022-08-31 to 2025-08-31. Turnover and every tax figure for AVES remain unread. Only its shrunk alpha, −0.16 against a 4.48 floor, was published.",
    issuer: {
      notes: [
        "36 bp, gross equal to net, with no fee waiver and no expense cap — so unlike IEMG's contractual 9 bp cap there is nothing here to expire and nothing to be recouped.",
        "$1.5B of net assets and inception 2021-09-28, against the MSCI Emerging Markets IMI Value Index. No closure, liquidation or adviser change is disclosed.",
      ],
      source: {
        label: "Avantis Emerging Markets Value ETF quarterly fact sheet, as of 2026-06-30",
        docPath: "docs/research/factor-products.md",
        href: "https://res.avantisinvestors.com/docs/avantis-emerging-markets-value-aves-etf-fact-sheet.pdf",
      },
      readOn: asOf("2026-08-22"),
    },
    source: products,
    asOf: asOf("2026-08-22"),
  },
  {
    ticker: "DFEV",
    name: "Dimensional Emerging Markets Value ETF",
    category: "emerging-value",
    mandate: "Cheap emerging-market shares, on the shortest run of foreign history audited here.",
    expenseRatioBp: null,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [
      { factor: "HML", value: 0.267, interval: null, panel: "emerging", window: { from: "2022-05", to: "2025-12" } },
      { factor: "HML", value: -0.092, interval: null, panel: "us", window: { from: "2022-05", to: "2025-12" } },
    ],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 3.23,
    pedestalPpYr: EMERGING_PEDESTAL,
    status: "unresolved",
    verdict:
      "The larger of the two emerging value loadings and the shorter window: 44 months, interval across the bar, shortfall −2.19 frozen and −2.03 expressive. unresolved, basis-invariant.",
    caution:
      "Reads −0.092 on the US panel. With AVES it is why the region with the largest measured HML premium — +7.58 [+4.34, +11.01] — has nothing investable audited here. No fee was read. Only its shrunk alpha, −1.19 against a 3.23 floor, was published.",
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
    mandate: "Broad high-quality US bonds. You are paid for lending long and for credit risk, and it is a brake.",
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
    mandate:
      "A copy of the average large managed-futures fund. The only trend fund we have ever measured against a model.",
    expenseRatioBp: 85,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [
      {
        factor: "TSMOM",
        value: 0.671,
        interval: "[+0.513, +0.829]",
        panel: "aqr-tsmom",
        window: { from: "2021-07", to: "2025-12" },
      },
    ],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 10.93,
    pedestalPpYr: null,
    status: "exploratory",
    verdict:
      "The one product that delivers this benchmark's exposure: the interval clears the frozen 0.50 bar, one regressor explains 52% of its monthly variance, and the loading holds across the fixed split and all 19 rolling windows with no sign change. It trailed a cost-free vendor index by 0.48 pp/yr against its 85 bp fee.",
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
    ticker: "SDMF",
    name: "Simplify DBi CTA Managed Futures Index ETF",
    category: "managed-futures",
    mandate: "An index copy of managed futures. Widely reported as a two-for-one fund; it is not one.",
    expenseRatioBp: 35,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Audited as a candidate wrapper and it is not in that category at all. Its 2026-03-31 N-PORT holds no equity ETF, no equity index future and no equity of any kind: 89.5% of net assets in Treasury bills, 4.4% in a money fund, and four total return swaps on DBi managed-futures indices. b is zero, so delta is 1.000 and it keeps none of the +2.44 pp/yr funding-rule gap — the same arithmetic as DBMF, KMLM or any standalone trend fund. 0.20% management plus 0.15% acquired-fund fees is 0.35% with no waiver.",
    caution:
      "$4.38m of net assets at 2026-03-31 makes it the smallest fund on this shelf, below even JPFP, and it did not exist at 2025-12-31. Its whole diversifier leg is bilateral swap exposure, and its Cayman subsidiary held 22.50% of total assets against the 25% RIC cap. Bought at a 30% weight it would pay the full funding-rule gap that the wrappers exist to avoid, so its 35 bp is cheap for the wrong product rather than cheap for the right one.",
    wrapper: {
      delta: 1,
      fundingCapturePercent: 0,
      allInCostBp: 35,
      grossNotionalPerDollar: 1,
      distributionTaxDragPpYr: null,
      incrementalTaxDragBp: null,
      structureAsOf: asOf("2026-03-31"),
    },
    source: trend,
    asOf: asOf("2026-08-22"),
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
    loadings: [
      {
        factor: "TSMOM",
        value: 0.475,
        interval: "[+0.058, +0.991]",
        panel: "aqr-tsmom",
        window: { from: "2022-03", to: "2025-12" },
      },
    ],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 13.14,
    pedestalPpYr: null,
    status: "rejected",
    verdict:
      "Rejected against the frozen 0.50 bar: the point estimate is below it and the interval spans from 0.058 to 0.991, on 46 months with an R² of 0.137 and a +1.90 pp/yr tracking difference.",
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
    loadings: [
      {
        factor: "TSMOM",
        value: 0.245,
        interval: "[−0.148, +0.446]",
        panel: "aqr-tsmom",
        window: { from: "2021-01", to: "2025-12" },
      },
    ],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 16.49,
    pedestalPpYr: null,
    status: "rejected",
    verdict:
      "Rejected at +0.245 with an interval containing zero. The shortfall is partly definitional and must not be read as a defect: its index holds none of the nine equity futures in AQR's universe.",
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
    loadings: [
      {
        factor: "TSMOM",
        value: 0.303,
        interval: "[+0.183, +0.420]",
        panel: "aqr-tsmom",
        window: { from: "2019-07", to: "2025-12" },
      },
    ],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 6.64,
    pedestalPpYr: null,
    status: "rejected",
    verdict:
      "Rejected at +0.303 on 78 months — the tightest interval of the four rejections and clearly under the 0.50 bar, so this is a delivered-exposure verdict rather than an underpowered one.",
    caution: "The dearest of the five tested at 98 bp.",
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
    mandate:
      "A rules-based managed-futures fund, audited against the same 0.50 delivered-exposure bar as the rest of the shelf.",
    expenseRatioBp: 66,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [
      {
        factor: "TSMOM",
        value: 0.099,
        interval: "[+0.003, +0.201]",
        panel: "aqr-tsmom",
        window: { from: "2019-09", to: "2025-12" },
      },
    ],
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
  // Capital-efficient wrappers. Every one of these has a null alpha, and that is still
  // the most important fact on the entry: what is verified is structure and cost from
  // filings, never that the sleeve inside earns anything.
  //
  // Two of them now carry a loading. A fund's own monthly total return is filed in
  // Item B.5 of Form N-PORT, so a wrapper old enough to have filed can be regressed like
  // any other fund, and RSST and RSSB have been
  // (`docs/research/loading-comparability-and-wrapper-exposure.md`). The rest still carry
  // an empty list because they are three to eight months old, not because the measurement
  // is impossible. A loading is exposure delivered; it is not evidence that the exposure
  // pays, and `notionalExposure` remains a separate field for the separate question of
  // what the fund holds.
  // -------------------------------------------------------------------------
  {
    ticker: "RSST",
    name: "Return Stacked U.S. Stocks & Managed Futures ETF",
    category: "capital-efficient",
    mandate:
      "US stocks plus managed futures on top, paid for by borrowing inside the fund rather than by selling the stocks.",
    expenseRatioBp: 99,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [
      {
        factor: "TSMOM",
        value: 0.681,
        interval: "[+0.406, +0.955]",
        panel: "aqr-tsmom",
        window: { from: "2023-10", to: "2026-04" },
      },
    ],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: "exploratory",
    verdict:
      "It delivers the trend exposure it sells, and this is the first measurement of it: TSMOM +0.681 [+0.406, +0.955] over 31 filed months to 2026-04, beside an equity beta of +0.979 [+0.763, +1.195] — one dollar of equity and about seven tenths of a dollar of trend, per dollar of capital, against a filed notional of one and one. Regressed on DBMF instead of on the vendor index it reads +0.857 [+0.719, +0.995]. Structure and cost are from filings. Its 2026-04-30 N-PORT shows SPDR Portfolio S&P 500 at 74.09% of net assets plus E-mini futures at 33.1% — 107.2% equity — with a government money fund at 16.04% as collateral and a trend book running ~294% of net assets in gross notional to deliver ~100% of risk exposure. delta is −0.07, so it keeps 100% of the +2.44 pp/yr funding-rule gap and its sleeve hurdle is 0.00 where a standalone managed-futures fund pays the full 2.44. All-in 0.99%, no waiver, and Form N-CEN for the year ended 2026-01-31 reports no recoupment clause. Distribution tax drag 0.32 pp/yr, 4.5 bp of it incremental once the VTI it displaces is subtracted, and 1.3 bp of portfolio return at a 30% notional weight.",
    caution:
      "The trend loading above rests on 31 filed months, which is roughly one market regime. Its 95% interval runs from +0.406 to +0.955, so this window cannot tell one dollar of delivered trend from four fifths of one, and the smallest loading it could have detected at 80% power is 0.392. It is exposure delivered, not a return earned: there is still no alpha, no Sharpe and no drawdown measured for the fund. It does not disclose its financing cost and files 0.00% of interest expense, like every fund in its family. Its 28-month tax window is entirely a rising market; the failure mode is a flat-equity, strong-trend year, which is the year the sleeve exists for. Under three years old.",
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
    issuer: {
      notes: [
        "The fund's own words: \"one dollar invested in the Fund provides approximately one dollar of exposure to the Fund's U.S. Equity strategy and approximately one dollar of exposure to the Fund's Managed Futures strategy\", targeting 100% of each.",
        "The managed-futures leg runs through a wholly-owned Cayman subsidiary capped at 25% of total assets, tested quarterly. The subsidiary is not registered under the 1940 Act, and breaching the cap would put the fund's RIC status at risk.",
        "35 months live at 2026-08-17, at $508.70m of net assets on 2026-08-14. The fee table shows no waiver line at all, so 99 bp is both gross and net.",
        "Over its short life it has trailed US equity: the prospectus reports 17.17% a year since inception on 2023-09-05 against 21.50% for the S&P 500. Thirty-five months settles nothing about a sleeve whose whole purpose is the years equities lose, and it is not evidence either way.",
      ],
      source: {
        label: "RSST summary prospectus, 497K filed 2026-04-27",
        docPath: "docs/research/capital-efficiency-and-breadth.md",
        href: "https://www.sec.gov/Archives/edgar/data/1924868/000199937126009152/rsst-497k_042726.htm",
      },
      readOn: asOf("2026-08-17"),
    },
    source: capital,
    asOf: READ,
  },
  {
    ticker: "CTAP",
    name: "Simplify US Equity PLUS Managed Futures Strategy ETF",
    category: "capital-efficient",
    mandate:
      "US stocks plus a dollar of an affiliated trend fund, delivered through a swap rather than through futures.",
    expenseRatioBp: 28,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: "exploratory",
    verdict:
      "The tightest delta on the wrapper shelf, and the fee table that least resembles what the fund costs. Its 2026-03-31 N-PORT reads iShares Core S&P 500 at 70.41% of net assets plus a long E-mini S&P 500 future at 32.23% — 102.64% equity — against 95.17% of total-return-swap notional on CTA plus 3.71% of CTA held outright, 98.88% of trend. delta is −0.027, it keeps the whole +2.44 pp/yr funding-rule gap, its sleeve hurdle is 0.00, and 18.79% sits in T-bills as collateral. Net assets went $4.47m at 2025-12-31 to $123.41m at 2026-03-31 to $157.88m on 2026-08-21.",
    caution:
      "The 0.10% is real, contractual and expiring, and it is not what the trend dollar costs. A total return swap pays the reference fund's return net of that fund's fees, and Acquired Fund Fees and Expenses reaches direct holdings rather than a swap reference — so CTA's own 0.75%, which carries no waiver, rides inside 95.17% of net assets and appears nowhere in this fee table. All-in is about 0.81%/yr today and about 0.99% once the waiver lapses on 2026-12-04, against RSST's 0.99% and MATE's 0.97%. Three further asymmetries, none of them in a fee table: 82.48% of net assets is bilateral swap exposure to Bank of America and 12.70% to Citibank, rather than to a clearing house; the trend leg is an affiliated fund and the prospectus concedes the conflict; and a swap is not a §1256 contract, so the 60/40 split that reaches RSST's and MATE's futures does not reach 95% of this fund's diversifier. Eight months old, and it lost a portfolio manager on 2026-08-07. Its trend loading is unmeasured because it has three filed monthly returns, not because a wrapper cannot be regressed — RSST's was measured on 31.",
    wrapper: {
      delta: -0.027,
      fundingCapturePercent: 100,
      allInCostBp: 81,
      grossNotionalPerDollar: 2.015,
      distributionTaxDragPpYr: null,
      incrementalTaxDragBp: null,
      structureAsOf: asOf("2026-03-31"),
    },
    notionalExposure: [
      { kind: "us-equity", perDollarOfCapital: 1.0264 },
      { kind: "trend", perDollarOfCapital: 0.9888 },
    ],
    reviewTrigger: {
      on: asOf("2026-12-04"),
      what: "Two dates, and the near one is a filing. Its next Form N-PORT, for the quarter ending 2026-06-30, is due 2026-08-29: reread the base leg and the swap notional and recompute delta. Then on 2026-12-04 the fee waiver lapses unless renewed, taking the filed net expense from 0.10% to 0.28% and the all-in trend dollar from about 0.81% to about 0.99% — at which point it is the same price as RSST with an affiliated-fund conflict and single-bank counterparty exposure attached. If the waiver is renewed on the same terms and the counterparty concentration falls, this becomes the cheapest verified wrapper on the shelf and the ranking is worth reopening; if it lapses, nothing about the cost case survives.",
    },
    issuer: {
      notes: [
        "Inception 2025-12-08, so eight months live at 2026-08-22, and $157,883,998.76 of net assets on 2026-08-21 — larger than MATE and JPFP together, and the fastest asset growth on this shelf.",
        'Its own words fix both legs: "The Fund uses derivatives to overlay the Managed Futures Strategy on top of the US Equity Strategy such that for each one dollar invested, the Fund has one dollar of US equity exposure and one dollar of CTA futures exposure."',
        'The trend leg is an affiliated fund reached by swap: "The Fund primarily executes the Managed Futures Strategy indirectly by investing in a total return swap on the Simplify Managed Futures Strategy ETF ("CTA"), which is a US domiciled exchange-traded fund managed by the adviser." The prospectus concedes the conflict: "The adviser is subject to an indirect conflict of interest in allocating the Fund\'s assets to a swap linked to CTA, as CTA is an affiliated fund that may underperform other futures-based funds."',
        'The fee table reads 0.25% management plus 0.03% acquired-fund fees for 0.28% gross, less an 0.18% waiver, for 0.10% net. The waiver is a fee reduction and not an expense cap: "The Fund\'s adviser has contractually agreed, through at least December 4, 2026, to reduce its management fees to 0.07% of the Fund\'s average daily net assets. This agreement may be terminated only by the Simplify Exchange Traded Funds\' Board of Trustees." The words "recoup" and "recapture" do not appear anywhere in the statutory prospectus, so there is nothing to be clawed back — the risk here is the expiry, not a recoupment.',
        "It runs no Cayman subsidiary of its own — Form N-PORT reports zero assets invested in a controlled foreign corporation — because its commodity exposure sits inside CTA, which has one. The 25% RIC cap therefore binds CTA rather than this fund.",
        "Every swap files its financing leg as SOFR plus a spread of 0.00000000, which makes CTAP the only wrapper on this shelf whose financing spread is disclosed at all. Termination dates are 2049-12-31, so the swaps are evergreen rather than rolling.",
      ],
      source: {
        label: "Simplify US Equity PLUS Managed Futures Strategy ETF, 497K dated 2025-12-05",
        docPath: "docs/research/capital-efficiency-and-breadth.md",
        href: "https://www.sec.gov/Archives/edgar/data/1810747/000182912625009650/simplifyetf_497k.htm",
      },
      readOn: asOf("2026-08-22"),
    },
    source: capital,
    asOf: asOf("2026-08-22"),
  },
  {
    ticker: "RSSB",
    name: "Return Stacked Global Stocks & Bonds ETF",
    category: "capital-efficient",
    mandate:
      "Global stocks plus a full dollar of Treasury exposure through futures. The best-built two-for-one fund here.",
    expenseRatioBp: 39,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [
      {
        factor: "TSMOM",
        value: -0.101,
        interval: "[−0.358, +0.155]",
        panel: "aqr-tsmom",
        window: { from: "2023-12", to: "2026-04" },
      },
    ],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "The clean read, and it verifies the marketing exactly: two equity ETFs at 90.53% of net assets plus one equity-index future at 9.54% is 100.07% equity, and four Treasury futures total 100.33%. The two legs use different N-PORT asset categories, so nothing is commingled and delta is −0.0007 at 0.39% all-in with no waiver.",
    caution:
      "Its own trend loading is −0.101 [−0.358, +0.155] on 29 filed months — the negative control that makes RSST's +0.681 readable, since the same sponsor, the same wrapper and the same regression return nothing where there is no trend book. Rejected as a second overlay and as a replacement. A bond overlay does not inherit trend's flat drawdown: resampled, it is the deeper drawdown in 49.7% of histories at 30% notional and 70.0% at 100%, against trend's 6.9%; at matched 1.6× gross, 60% trend beats 30% trend plus 30% bonds by +1.40 pp/yr and on Sharpe. Its base leg is *global* equity where the incumbent is US, so no single delta scores it for a US-based reader.",
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
    issuer: {
      notes: [
        'One dollar of global equity plus one dollar of US Treasury futures, and 39 bp rather than RSST\'s 99 — because Treasury futures generate qualifying income, so no Cayman subsidiary is needed. The words "Cayman" and "Subsidiary" do not appear in its summary prospectus.',
        'Its expense example still carries the sentence "The management fee waiver discussed above is reflected only through May 31, 2026" although no waiver is discussed and none appears in the fee table. Read gross = net = 39 bp and treat the sentence as stale boilerplate.',
      ],
      source: {
        label: "RSSB summary prospectus, 497K filed 2026-04-27",
        docPath: "docs/research/capital-efficiency-and-breadth.md",
        href: "https://www.sec.gov/Archives/edgar/data/1924868/000199937126009149/rssb-497k_042726.htm",
      },
      readOn: asOf("2026-08-17"),
    },
    source: capital,
    asOf: READ,
  },
  {
    ticker: "NTSX",
    name: "WisdomTree U.S. Efficient Core Fund",
    category: "capital-efficient",
    mandate: "90 cents of US stocks and 60 of Treasuries per dollar. The reference case for how you pay for an add-on.",
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
      "Its 2026-03-31 N-PORT reads 90.83% equity plus 63.50% Treasury futures, 1.543× gross, delta 0.144 — so it keeps 85.6% of the funding-rule gap and its sleeve hurdle is 0.35 pp/yr. The 0.20% fee converted to overlay notional is 0.315%.",
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
    mandate: "US stocks with roughly a matching dollar of gold exposure stacked on top.",
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
      "Its 2026-02-28 N-PORT reads 84.80% equity plus 83.63% gold futures, 1.684× gross, delta 0.182, keeping 81.8% of the funding-rule gap. The all-in overlay cost is about 0.60%/yr once ≤40 bp of gold-futures financing is added to the 0.20% fee.",
    caution:
      "As a sleeve it contributes +0.09 pp/yr against a detection floor of 1.68 — unmeasurable. Its 1.53 pp/yr distribution tax drag is the second largest on the wrapper shelf (1.31 restated at a 24%/15%-federal plus 9.3%-CA investor), and the naive rule 'shelter the highest drag' puts it at the front of the queue, which is exactly backwards.",
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
    mandate: "US stocks topped up with S&P futures, plus a spread-out trend position bought with borrowing on top.",
    expenseRatioBp: 97,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: "exploratory",
    verdict:
      "Measured from the holdings, and the gap this row used to describe is closed. Its 2026-05-31 N-PORT reads iShares Core S&P 500 at 50.30% of net assets plus one long E-mini S&P 500 future at 65.57% — 115.87% US equity, not the 49.8% base leg recorded here before — against a filed 100% trend target, so delta is −0.159, it keeps the whole +2.44 pp/yr funding-rule gap, and its sleeve hurdle is 0.00 where a standalone managed-futures fund pays the full 2.44. Net assets $39.41m, T-bill collateral 29.54%, and the derivative book runs 404.5% of net assets in gross notional (284.2% futures, 120.3% FX forwards) to deliver it. The 2026-02-28 filing reads the same way at 111.56% equity and delta −0.116. All-in 0.97%, no waiver.",
    caution:
      "The 65.57% E-mini line is not separable into base completion and the trend book's own equity position, because the trend book trades equity-index futures too and no filing tags a contract by sleeve. 115.87% is the filed US-equity total, not a contractual base leg; the contractual floor is the prospectus's 100%, where delta is 0.00. Both reads keep the whole gap, so the conclusion survives the ambiguity and the exact delta does not. Beyond that: eight months old at $39.41m, which is closure territory; the Cayman subsidiary held 21.09% of total assets at 2026-05-31 and 22.12% three months earlier against a 25% cap that costs RIC status if breached and not cured; no loading on any trend benchmark, no return, no Sharpe and no drawdown has been measured for it, and with six filed monthly returns none can be — the constraint is its age, not the source; and it has no SEC-standardised after-tax table because it has not completed a calendar year, so its distribution tax drag is unknown rather than small.",
    wrapper: {
      delta: -0.159,
      fundingCapturePercent: 100,
      allInCostBp: 97,
      grossNotionalPerDollar: 2.159,
      distributionTaxDragPpYr: null,
      incrementalTaxDragBp: null,
      structureAsOf: asOf("2026-05-31"),
    },
    notionalExposure: [
      { kind: "us-equity", perDollarOfCapital: 1.1587 },
      { kind: "trend", perDollarOfCapital: 1.0 },
    ],
    issuer: {
      notes: [
        "Man Active Trend Enhanced ETF — a Man Group fund sub-advised by AHL Partners, not a Return Stacked product and not merger arbitrage. Inception 2025-12-16, so eight months live at 2026-08-22.",
        '97 bp all-in: a 0.95% unitary fee plus 0.02% of acquired-fund fees, both "based on estimated amounts for the current fiscal year" rather than incurred. No waiver. A 12b-1 plan of up to 25 bp is adopted but dormant.',
        'Its own words fix the diversifier leg the delta divides by: "The Fund will target a 100% exposure to each of its Trend-Following Strategy and Equity Strategy."',
        'The Cayman subsidiary carries commodities only, not the whole trend book — "The Fund intends to gain exposure to the commodities futures markets by investing through a wholly-owned subsidiary" — and the fund "intends to manage the exposure to the Subsidiary so that the Fund\'s investments in the Subsidiary do not exceed 25% of the total assets at the end of any quarter."',
        'It states the §1256 treatment outright: the fund is "required, for federal income tax purposes, to mark to market and recognize as income for each taxable year its net unrealized gains and losses as of the end of such year on certain regulated futures contracts", and that gain is "generally 60% long-term and 40% short-term". That forces recognition of unrealised gains at year end, which in a taxable account is phantom income.',
      ],
      source: {
        label: "Man Active Trend Enhanced ETF, 485BPOS effective 2025-12-13",
        docPath: "docs/research/capital-efficiency-and-breadth.md",
        href: "https://www.sec.gov/Archives/edgar/data/2065379/000119312525316292/d98016d485bpos.htm",
      },
      readOn: asOf("2026-08-22"),
    },
    source: capital,
    asOf: asOf("2026-08-22"),
  },
  {
    ticker: "JPFP",
    name: "JPMorgan Managed Futures Plus ETF",
    category: "capital-efficient",
    mandate: "A stacked managed-futures and US equity ETF, listed two months before this shelf was read.",
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
      "Still unmeasurable, and now for a filing-level reason rather than an unexamined one: no Form N-PORT exists for it. Its series is S000101300 in the SEC's own ticker map, and none of the 24 N-PORT filings the J.P. Morgan Exchange-Traded Fund Trust made for the 2026-05-31 period carries that series. It commenced 2026-05-27, so its first holdings filing belongs to the quarter ending 2026-06-30 or 2026-07-31 and is due 2026-08-29 or 2026-09-29. Until one is filed there is no base leg, no diversifier leg and therefore no delta; its stack rests on the prospectus sentence 'aggregate notional exposure will exceed its net assets' and nothing else. Checked 2026-08-22.",
    caution:
      "It is the one product that would reorder the wrapper cost ranking outright — a 40 bp saving against RSST's 99 bp, on a line where 40 bp is a third of the whole fee — and it cannot yet be recommended. Three months live at $17.07m makes it the smallest fund on this shelf and the likeliest to close. It also carries one tax cost the other wrappers do not disclose: it expects to create and redeem in cash, which forfeits the in-kind shield on its equity leg as well as its overlay. No delta, no loading, no record — and no Form N-PORT, so all three wait on the same filing.",
    /**
     * The dated review trigger. This is the only entry on the shelf whose structure is
     * unknown for a reason that expires, so the recheck has a date rather than a condition.
     */
    reviewTrigger: {
      on: asOf("2026-09-29"),
      what: "Read JPFP's first Form N-PORT — its series is S000101300, and the filing is due 2026-08-29 if its first reporting period ends 2026-06-30 or 2026-09-29 if it ends 2026-07-31 — and compute delta from the base leg and the diversifier leg the way MATE's was computed, summing the equity ETF holding and the index future that completes it rather than reading the largest line alone. If delta comes back at or below zero, JPFP keeps the whole funding-rule gap at 59 bp against RSST's 99 and MATE's 97, and it reorders the wrapper cost ranking outright. That still would not make it holdable at a 30% weight: at $17.07m it would be the smallest fund on this shelf with three months of record, so a negative delta buys it a place in the comparison, not the allocation. If no filing has appeared by 2026-09-29, that is itself the finding and the next date is the following quarter.",
    },
    wrapper: {
      delta: null,
      fundingCapturePercent: null,
      allInCostBp: 59,
      grossNotionalPerDollar: null,
      distributionTaxDragPpYr: null,
      incrementalTaxDragBp: null,
      structureAsOf: null,
    },
    issuer: {
      notes: [
        "It has since commenced. Performance inception 2026-05-27, so three months live at 2026-08-22, with $17.07m of net assets on its 2026-06-30 fact sheet — the smallest fund on this shelf and the one with the highest closure risk. No later issuer figure was reachable: the J.P. Morgan product page renders its data client-side and returned none.",
        "59 bp unitary, no waiver, no recoupment: 40 bp cheaper than RSST for a structurally similar product, which is why it is a standing review trigger in the research rather than a footnote.",
        'It says only that it "seeks to provide full exposure to each of the Managed Futures Strategy and the U.S. Equity Strategy, simultaneously" and that "aggregate notional exposure will exceed its net assets". Unlike RSST, RSSB and MATE it publishes no numeric per-dollar breakdown anywhere, so none is stated here.',
        'The commodity leg runs through Managed Futures Plus Fund CS Ltd., a wholly-owned Cayman subsidiary, and the fund gains commodity exposure "by investing up to 25% of the Fund\'s assets" in it.',
        'It discloses a tax cost the other two candidates do not: "the Fund expects to generally effect its creations and redemptions entirely or partially in cash, rather than primarily for in-kind securities. Therefore, it will be required to sell portfolio securities and subsequently recognize a gain on such sales that the Fund might not have recognized if it were to distribute portfolio securities in kind."',
        "Its registration statement never states the §1256 mark-to-market rule for the fund's own regulated futures contracts; the single mention of §1256 in the whole filing is inside the §988(a)(1)(B) foreign-currency election. The rule applies regardless, so this is a disclosure difference from MATE and not an exposure difference.",
      ],
      source: {
        label: "JPMorgan Managed Futures Plus ETF, 485BPOS filed 2026-04-15",
        docPath: "docs/research/capital-efficiency-and-breadth.md",
        href: "https://www.sec.gov/Archives/edgar/data/1485894/000119312526156138/d63821d485bpos.htm",
      },
      readOn: asOf("2026-08-22"),
    },
    source: capital,
    asOf: asOf("2026-08-22"),
  },
  {
    ticker: "SCHD",
    name: "Schwab U.S. Dividend Equity ETF",
    category: "alternative",
    mandate: "US shares screened for dividends, audited as possible ballast rather than as a value fund.",
    expenseRatioBp: 6,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: 10.93,
    pedestalPpYr: -0.55,
    status: "rejected",
    verdict:
      "Dominated. Sharpe 0.643 at a correlation of +0.820 to the equity core, against 6 bp of fee and 0.51 pp/yr of distribution tax. It is the equity sleeve with a screen and a tax bill, not a second engine.",
    caution:
      "The detection floor on its alpha is 10.93 pp/yr, so the rejection rests on dominance and correlation rather than on a measured alpha. rejected means a falsifier fired, never that the effect is zero.",
    source: alternatives,
    asOf: READ,
  },
  {
    ticker: "VNQ",
    name: "Vanguard Real Estate ETF",
    category: "alternative",
    mandate: "US listed real estate, audited as a candidate diversifier.",
    expenseRatioBp: 13,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: "rejected",
    verdict:
      "Dominated. Sharpe 0.157 at a correlation of +0.839 to equity, 13 bp of fee and 0.61 pp/yr of distribution tax. Listed real estate delivered 112% of the downside for 80% of the upside.",
    caution:
      "A rejection on dominance, measured against this repository's own equity core rather than in the abstract.",
    source: alternatives,
    asOf: READ,
  },
  {
    ticker: "TIP",
    name: "iShares TIPS Bond ETF",
    category: "alternative",
    mandate: "Inflation-linked Treasuries, audited as a candidate second fixed-income engine.",
    expenseRatioBp: null,
    securitiesLendingBp: null,
    netCostBp: 17.92,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: "rejected",
    verdict:
      "Not a second engine. Its correlation to the nominal bond funds beside it runs +0.76 to +0.85, and its correlation to equity is +0.131 against nominal bonds' \u22120.076. It is the worse diversifier of the two, which is the opposite of the usual claim.",
    caution:
      "Its net cost of 17.92 bp against SCHP's 2.99 bp is the sharper point: the two correlate +0.9997, so the fee difference is the entire decision.",
    source: alternatives,
    asOf: READ,
  },
  {
    ticker: "SCHP",
    name: "Schwab U.S. TIPS ETF",
    category: "alternative",
    mandate: "The same inflation-linked Treasuries, at a fifth of the cost.",
    expenseRatioBp: null,
    securitiesLendingBp: null,
    netCostBp: 2.99,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: "rejected",
    verdict:
      "Correlated +0.9997 with TIP and costs 2.99 bp net against its 17.92. If a TIPS sleeve is held at all, that arithmetic is the whole of the decision about which one.",
    caution:
      "The sleeve itself is rejected on correlation. Being the cheaper way to hold it is not an argument for holding it.",
    source: alternatives,
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

/**
 * The audit as a whole, rather than any one fund.
 *
 * These are the numbers a page reaches for when it wants to say what the *instrument*
 * can and cannot see, and they belong here rather than in a route: a count typed into a
 * paragraph is a number with no source and no `as of`.
 */
export const shelfAudit = {
  usProductsAudited: 109,
  loadingsSurvivingCorrection: 96,
  alphaTests: 327,
  alphaTestsSurviving: 5,
  alphaTestsSurvivingAllNegative: true,
  medianDetectableAlphaUsPpYr: 5.01,
  medianDetectableAlphaExUsPpYr: 3.23,
  medianDetectableAlphaManagedFuturesPpYr: 12.75,
  trueAlphaDispersionPpYr: 1.25,
  correction: "Benjamini–Hochberg on the loadings, Holm on the alphas",
  note: "Exposure is measurable and skill is not. The median alpha this instrument can detect is about four times the true dispersion between funds, so most alpha findings on any shelf are noise by construction.",
  source: products,
  asOf: READ,
} as const;

/**
 * The funding-rule gap: what financing a diversifier as notional is worth for a 100%
 * equity base, before anything at all is said about the diversifier.
 */
export const fundingRuleGapPpYr = {
  value: 2.44,
  basis: "100% equity base; 2.08 pp/yr for a 60/40 base",
  formula: "a_p − σ_p² = σ_p²(L_p* − 1)",
  source: capital,
  asOf: READ,
} as const;

export const shelfAsOf = READ;

/** Re-exported so a route can name the owning page without re-declaring a citation. */
export const shelfSources = { products, recommendation, structural, capital, trend } as const;
