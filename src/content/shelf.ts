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
  /** Notional per $1 of capital, as a fraction. 1.05 means 105% of net assets. */
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
 * The 30-day median bid-ask spread every ETF must publish under Rule 6c-11(c)(1)(v),
 * with the date the disclosure was read.
 *
 * Absent means nobody read the disclosure for that fund, which is the case for most of
 * this shelf. It is not a claim that the spread is small. A spread is a **one-time entry
 * cost**, so it must never be allowed to outrank an expense ratio for a long holder: SPY
 * is the shelf's own example, with the tightest spread on it and the highest cost of
 * owning it. Held beside `netCostBp` and never added to it — one is paid once and the
 * other every year — and the comparison only becomes decisive when a fund is rebalanced,
 * which is the case `docs/research/market-scan-2026.md` §6.2 makes against CTAP.
 */
export interface SpreadFact {
  /** Basis points. A one-time cost at purchase, never a recurring one. */
  readonly bp: number;
  readonly asOf: AsOf;
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
  /** Present only where the Rule 6c-11 disclosure was read. Absent means nobody read it. */
  readonly spread?: SpreadFact;
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
  label: "Our audit of the alternatives",
  docPath: "docs/research/alternative-sleeves-audit.md",
};
const capital: Citation = {
  label: "Capital efficiency and how many different bets you hold",
  docPath: "docs/research/capital-efficiency-and-breadth.md",
};
const trend: Citation = { label: "The marginal value of trend", docPath: "docs/research/trend-marginal-value.md" };
const untestedTilts: Citation = {
  label: "Four leans the recommendation never priced",
  docPath: "docs/research/untested-tilt-candidates.md",
};
const finalTest: Citation = {
  label: "The final construction, tested",
  docPath: "docs/research/final-construction-test.md",
};
const scan: Citation = { label: "Market scan, August 2026", docPath: "docs/research/market-scan-2026.md" };
const liveStacked: Citation = {
  label: "Live stacked funds: what the second dollar has actually paid",
  docPath: "docs/research/live-stacked-fund-records.md",
};

const READ = asOf("2026-08-17");

/**
 * The 2026-09-01 refresh: the latest Form N-PORT per stacked fund re-read from EDGAR, the
 * Return Stacked and Simplify issuer pages re-read for size and spread, and RSST's equity
 * line re-derived from the filing's own contract values. Only the records that changed
 * carry this date; the rest still carry the date they were actually read.
 */
const REFRESH = asOf("2026-09-01");

const evidence: Citation = { label: "The evidence base", docPath: "docs/research/evidence-base.md" };
const leveraged: Citation = {
  label: "Two-times and three-times funds and the 200-day rule",
  docPath: "docs/research/leveraged-etfs-and-timing-rules.md",
};
const discovery: Citation = {
  label: "Discovery sweep, September 2026",
  docPath: "docs/research/discovery-sweep-2026-09.md",
};
const currency: Citation = {
  label: "Currency and the international holding",
  docPath: "docs/research/currency-and-the-international-sleeve.md",
};

/**
 * The 2026-09-02 extension: the asset classes a casual investor asks about, read from
 * issuer pages, fact sheets and EDGAR filings on that date. None of these funds has been
 * regressed or scored here; their records carry cost and structure and say so.
 */
const WEB_READ = asOf("2026-09-02");

/**
 * The two dates behind every {@link SpreadFact} on this shelf. Rule 6c-11 spreads were
 * read from issuer pages on 2026-08-22/23 for the diversifier and factor funds
 * (`docs/research/market-scan-2026.md` §6.2), and the six the reference portfolio prices
 * were read a week earlier and live in `src/content/portfolio.ts`.
 */
const SPREADS_READ = asOf("2026-08-22");
const PORTFOLIO_SPREADS_READ = asOf("2026-08-14");

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
    mandate: "The whole US market at capitalisation weight. What every US result here is measured against.",
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
    issuer: {
      notes: [
        'The "Morningstar" in the name is the fund\'s own, not a typo: Vanguard Index Funds\' supplement of 2026-07-29 renames "Vanguard Total Stock Market Index Fund" to "Vanguard Morningstar Total Stock Market Index Fund", and its ETF share class to "Vanguard Morningstar Total Stock Market ETF", after Morningstar acquired CRSP and rebranded the indexes.',
        'Its target index became the Morningstar US Total Market Index on the same date, and the filing states that "Each Fund\'s investment objective, strategies, and polices remain unchanged." Ticker, fee, holdings and every exposure on this shelf are unaffected.',
      ],
      source: {
        label: "Vanguard Index Funds, 497 supplement dated 2026-07-29",
        docPath: "docs/research/market-scan-2026.md",
        anchor: "the-one-real-product-change-vanguards-funds-were-renamed",
        href: "https://www.sec.gov/Archives/edgar/data/36405/000003640526000386/f45788d1.htm",
      },
      readOn: asOf("2026-08-22"),
    },
    spread: { bp: 0.55, asOf: PORTFOLIO_SPREADS_READ },
    source: recommendation,
    asOf: asOf("2026-08-24"),
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
      "The whole difference from VTI is 1.78 bp of securities lending — VOO earns the least of any fund on the core shelf in all eight filed years — and P(ahead at 30 yr) is 0.52 to 0.54. No factor experiment read it, so it has no measured exposure and no alpha.",
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
    spread: { bp: 0, asOf: READ },
    source: structural,
    asOf: READ,
  },
  {
    ticker: "VT",
    name: "Vanguard Total World Stock ETF",
    category: "us-core",
    mandate:
      "The whole world at capitalisation weight, US included, in one fund. What portfolios 1 and 2 hold, and the one-fund answer to the whole equity question.",
    expenseRatioBp: 6,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: 3,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Held as the whole of portfolios 1 and 2 and never regressed, because it is the market rather than a bet against it. Its 6 bp fee is twice VTI's 3 bp plus VXUS's 5 bp blended, which is the price of one ticker instead of two. No Form N-CEN was read for it, so its lending income and net cost are unknown rather than zero.",
    caution:
      "Roughly three fifths of it is the US market, so a reader holding it beside VTI owns the US twice. Sold as a single fund it cannot be rebalanced between regions, which is the whole of what portfolios 3 and 4 buy with their extra tickers.",
    issuer: {
      notes: [
        "0.05% management fee, no 12b-1 fee, 0.01% other expenses and 0.06% total annual fund operating expenses, from the ETF Shares summary prospectus dated 2026-02-27. Tracks the FTSE Global All Cap Index. Portfolio turnover 3% in the most recent fiscal year. The prospectus says nothing about securities lending.",
        "Inception 2008-06-24 and $77,627m of ETF net assets at 2026-06-30, from Vanguard's own investment profile dated as of 2026-06-30. The 0.06% printed there matches the prospectus. Vanguard's product page is rendered by script and could not be read; an aggregator showed $81.26bn on 2026-09-02, which is a later date and not an issuer figure.",
        "Not on Vanguard's 2026-02-01 fee-cut list, which named 53 funds and 84 share classes; the fee has been 0.06% since at least the 2025 prospectus.",
      ],
      source: {
        label: "Vanguard Total World Stock Index Fund, ETF Shares 497K dated 2026-02-27",
        docPath: "docs/research/portfolio-recommendation.md",
        href: "https://www.sec.gov/Archives/edgar/data/857489/000119312526077566/f44201d1.htm",
      },
      readOn: WEB_READ,
    },
    source: recommendation,
    asOf: WEB_READ,
  },
  // -------------------------------------------------------------------------
  // US value and small. Nine systematic products, all `exploratory`, and the two
  // cheap incumbents the frozen comparator is built from, both `rejected`.
  // -------------------------------------------------------------------------
  {
    ticker: "VTV",
    name: "Vanguard Value ETF",
    category: "us-value",
    mandate:
      "Big cheap US companies, weighted by size, for 0.03% a year. Part of what results are measured against, rather than a bet.",
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
      "The largest implementation shortfall on the fund list, −4.92 pp/yr on the frozen basis and −4.23 on a cheap style grid that can express small value: the best in-sample combination of VTI, VUG, VTV and VB could not get within four points a year of it.",
    caution:
      "Its SMB leg of +0.88 is the largest of any US value product here and the size premium is not signable on any panel (+0.33 against a 2.47 pp/yr floor). At a 20% weight it buys +43.1 bp for 312 bp of drift and reaches 90% confidence in 86 years. Against a portfolio that already holds a US value line it adds nothing: its active leg over VTI is +0.455 correlated with the recommended portfolio's own, and 87% of what it delivers beyond VTV is size.",
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
      "Buys HML +0.515 with an SMB leg of +0.12, so a 20% weight costs 160 bp of drift against AVUV's 312 for a comparable exposure. Its +0.11 shortfall is the only positive one among the nine systematic products.",
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
      "The largest HML exposure among the US large-value funds, and on that alone a 20% weight prices at +53.8 bp for 163 bp of drift — the best ratio in the table.",
    caution:
      "Disqualifying: its raw alpha of −6.06 pp/yr is larger than the 5.69 pp/yr its own window could have resolved, one of sixteen such funds on a 109-fund shelf and all sixteen negative. Charging it takes the lean to about −67 bp, or −54 bp against its own 36-month pedestal of −0.65 pp/yr.",
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
      "The same unpriced SMB leg as every small-value fund: +0.85, on a premium that cannot be signed. 262 bp of drift at a 20% weight, and 109 years to 90% confidence.",
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
    caution: "SMB +0.83 on an unsignable premium; 239 bp of drift at 20%.",
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
      "The deepest US value exposure on the fund list and still a subtraction. Over VTV on 78 months (2019-10\u20262026-03) it delivers HML +0.369 [+0.249, +0.490] and SMB +0.199, but also RMW \u22120.204 [\u22120.361, \u22120.047] and UMD \u22120.173 [\u22120.337, \u22120.008]: the value it buys is partly paid for by selling momentum. Net of a 33.87 bp cost and 42%/yr of turnover against VTV\u2019s 8%, replacing VTV with it at 15% changes portfolio return by about \u22120.10% a year, and it is negative under all four of this repository\u2019s premium scenarios.",
    caution:
      "42%/yr of turnover, the highest of any US value product audited and five times the incumbent\u2019s — its sort is an index reconstitution, which is exactly the case Experiment 007\u2019s 20\u201340% assumption was right about. The tax objection, however, is false: its distribution drag is 0.62 pp/yr against VTV\u2019s 0.67 over the same five years. Its 106 constituents are weighted by value score rather than by capitalisation, so it is a concentrated active position wearing an index label.",
    issuer: {
      notes: [
        "0.35% management fee, no other expenses, and 42% portfolio turnover in the most recent fiscal year, per its summary prospectus dated 2025-08-28.",
        "Five-year return before taxes 7.99% and after taxes on distributions 7.37% to 2024-12, a drag of 0.62 pp/yr — below VTV\u2019s 0.67 over the same period.",
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
      "The only US value product that both delivers its exposure and does not lose to a cheap mix, at 5 bp. It is the optional holding because of the fee, not because the chain is positive.",
    caution:
      "Its alpha is −2.78 against a 3.22 floor — the closest to measurable of the cheap products — and 25%/yr of turnover puts it with RPV rather than with the systematic funds.",
    issuer: {
      notes: [
        'The "Morningstar" in the name is the fund\'s own, not a typo: Vanguard Index Funds\' supplement of 2026-07-29 renames "Vanguard Small-Cap Value Index Fund" to "Vanguard Morningstar Small-Cap Value Index Fund", and its ETF share class to "Vanguard Morningstar Small-Cap Value ETF", after Morningstar acquired CRSP and rebranded the indexes.',
        'Its target index became the Morningstar US Small Cap Value Index on the same date, and the filing states that "Each Fund\'s investment objective, strategies, and polices remain unchanged." The rename touches neither the 5 bp fee nor the +0.41 HML exposure above.',
      ],
      source: {
        label: "Vanguard Index Funds, 497 supplement dated 2026-07-29",
        docPath: "docs/research/market-scan-2026.md",
        anchor: "the-one-real-product-change-vanguards-funds-were-renamed",
        href: "https://www.sec.gov/Archives/edgar/data/36405/000003640526000386/f45788d1.htm",
      },
      readOn: asOf("2026-08-22"),
    },
    source: recommendation,
    asOf: asOf("2026-08-24"),
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
      "Delivers its exposure and keeps its status under every comparator basis tested. It buys comparable HML to a small-value fund at roughly half the drift.",
    caution:
      "The US value premium on its own panel is +1.57 pp/yr against a 5.03 pp/yr floor and is not signable. Only the pooled three-region premium makes this lean's growth contribution positive.",
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
      "A genuinely deep value lean destroyed by its own trading. It files 332%/yr of portfolio turnover against VTI's 3%, which costs 3.54 to 5.86 pp/yr at the repository's 1.0-to-1.7 coefficient against a gross factor gain of about 1.1 pp/yr. At a 5% weight it is the only candidate whose portfolio effect this data can resolve, and it resolves to about -0.30% a year.",
    caution:
      "Its exposures are stated over its own filings and its incumbent's, not over the other value products on the fund list: EDGAR lists no Form N-PORT for the quarter ending 2021-09-30, so its history has a three-month hole and only the 54 gapless months after it are usable. Its active leg is +0.754 correlated with AVUV's, so it duplicates a position rather than adding one.",
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
      "What it sells cannot be priced. At a 20% weight the exposure is worth +15.7 bp against 252 bp of drift, +6.1 bp of growth, and 425 years to 90% confidence.",
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
    mandate:
      "Plain small US companies for 0.03% a year. Part of what results are measured against, rather than a holding.",
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
        "The name is verified, not inferred. Vanguard Index Funds' supplement of 2026-07-29 enumerates the ten funds of that registrant and gives this one explicitly: Vanguard Small-Cap Index Fund becomes Vanguard Morningstar Small-Cap Index Fund, and the ETF share class becomes Vanguard Morningstar Small-Cap ETF. The same table carries VTI and VBR.",
        "Ten and thirteen are the same event counted twice over. Vanguard announced on 2026-04-29 that it would rename 13 US equity index funds across all share classes; ten of them are in the Vanguard Index Funds registrant and are supplemented here, and Vanguard World Fund filed its own supplement on the same date for the rest. Nothing on this shelf sits outside the ten.",
        'Its target index was renamed on the same date, CRSP US Small Cap Index to Morningstar US Small Cap Index, and the filing states that "Each Fund\'s investment objective, strategies, and polices remain unchanged." The rename is a rebranding after Morningstar acquired CRSP; no exposure on this shelf is affected by it.',
      ],
      source: {
        label: "Vanguard Index Funds, 497 supplement dated 2026-07-29",
        docPath: "docs/research/market-scan-2026.md",
        anchor: "the-one-real-product-change-vanguards-funds-were-renamed",
        href: "https://www.sec.gov/Archives/edgar/data/36405/000003640526000386/f45788d1.htm",
      },
      readOn: asOf("2026-08-22"),
    },
    spread: { bp: 2.72, asOf: PORTFOLIO_SPREADS_READ },
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
      "The smallest alpha its window could have found is 7.34 pp/yr, the worst on the US shelf, so its −2.95 alpha means nothing either way. Turnover is now measured and it is what decides the fund: 116%/yr against VTI's 3% costs 1.25 to 2.06 pp/yr, against a gross exposure gain of +1.78 pp/yr on a US momentum premium of +4.19 that is itself under a 7.27 pp/yr floor. The tax objection, by contrast, is false — its filed distribution drag is 11 bp/yr *below* VTI's.",
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
    spread: { bp: 3, asOf: SPREADS_READ },
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
      "The published +0.414 carries NO WINDOW and must not be compared with any other fund\u2019s exposure figure; the +0.395 above is fitted here on a stated window and is the exposure delivered over VTI rather than the fund\u2019s own measured exposure. The exposure it buys sits on a US momentum premium of +4.19 pp/yr, against 7.27 pp/yr as the smallest premium that window could have found, and its active leg is +0.626 correlated with IDMO\u2019s — a tighter overlap than MTUM\u2019s +0.554, so a portfolio already holding international momentum buys less than it looks.",
    issuer: {
      notes: [
        "0.13% management fee, no other expenses, and 44% portfolio turnover in the most recent fiscal year, per its summary prospectus dated 2025-12-19.",
        "Five-year return before taxes 19.23% and after taxes on distributions 18.86% to 2024-12, a drag of 0.37 pp/yr against VTI\u2019s 0.42.",
        "Median net securities-lending income of 0.07 bp/yr across seven fiscal years of Form N-CEN, 2019-08-31 to 2025-08-31 — the lowest on this shelf, so its 13 bp fee is very nearly its net cost.",
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
    verdict: "Rejected on clause (c) at a +1.14 pp/yr shortfall, on an RMW exposure of +0.186.",
    caution:
      "The exposure is not purchasable at this threshold anywhere on the fund list — nine quality products and the largest RMW exposure is +0.228 — and the premium behind it is rejected and closed on public data (decision 0005). A product's own quality is irrelevant when the premium cannot be signed.",
    spread: { bp: 3, asOf: SPREADS_READ },
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
      "Costs −0.30 bp/yr to own: 3.30 bp of securities lending more than covers the 3 bp fee. Its own exposures are the term every ex-US lean is measured against, and its −0.31 pp/yr alpha is the developed-ex-US pedestal.",
    caution:
      "It beat its region's French market portfolio by 0.517 pp/yr beyond its fee. That is recorded as an index-construction difference and is not a finding. Its foreign tax credit is worth 15.78 bp/yr and only in a taxable account.",
    spread: { bp: 1.41, asOf: PORTFOLIO_SPREADS_READ },
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
      "The cheapest total-international fund audited at 1.43 bp net, and still dearer than holding VEA and VWO separately: splitting saves 1.25 bp/yr on the international holding before any placement argument.",
    caution:
      "This repository previously recorded VXUS at 3 bp, which was wrong. The 5 bp is from the 497K fee table dated 2026-02-27.",
    spread: { bp: 1.18, asOf: PORTFOLIO_SPREADS_READ },
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
      "The strongest lean this repository has priced: at an 8% substitution out of VEA it is the only line whose edge, +27.1 bp, sits above the 21.6 bp that 30 years of data could have resolved.",
    caution:
      "Its own alpha is −4.11 pp/yr against a 3.52 pp/yr floor — measurably negative, and one of four ex-US large-value funds reading −2.2 to −4.1. Charging that alpha takes the same lean from +27.1 bp to −8.2 bp.",
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
      "Second on growth per unit of drift at 0.576, and the lowest drift of the five at 31.3 bp for an 8% substitution. Shortfall −0.51 frozen, −0.16 expressive.",
    caution:
      "Its −3.13 pp/yr alpha against a 1.81 floor is the most clearly measurable negative on the ex-US shelf; charging it takes an 8% lean from +18.0 bp to −9.5 bp.",
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
      "The only large-value fund of the four whose alpha the window cannot measure: −2.53 sits inside a 2.63 floor, so on the alpha-charged reading this repository's answer is IVLU rather than DFIV, at 0.552 growth per unit of drift.",
    caution:
      "Its edge is smaller than DFIV's (+19.4 bp against +27.1 at an 8% substitution) and its shortfall of −1.19 does not move under any of the seven bases. Its 31 bp is the fee table's total, not its management fee: an aggregator reading of 0.30% is the 0.30% management line with the 0.01% of other expenses left off, and quoting it would understate what a holder pays.",
    issuer: {
      notes: [
        "0.30% management fee, no 12b-1 fee, 0.01% other expenses and 0.31% total annual fund operating expenses, with no waiver line, per its summary prospectus dated 2025-11-28.",
      ],
      source: {
        label: "iShares MSCI Intl Value Factor ETF, Form 497K dated 2025-11-28",
        docPath: "docs/research/market-scan-2026.md",
        href: "https://www.sec.gov/Archives/edgar/data/1100663/000119312525302146/d90140d497k.htm",
      },
      readOn: asOf("2026-08-24"),
    },
    spread: { bp: 2, asOf: SPREADS_READ },
    source: recommendation,
    asOf: asOf("2026-08-24"),
  },
  {
    ticker: "EFV",
    name: "iShares MSCI EAFE Value ETF",
    category: "intl-value",
    mandate: "Big cheap companies outside the US, tracking an index, and part of what results are measured against.",
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
      "Only its shrunk alpha, −1.58 pp/yr against a 2.22 floor, was published; the raw figure is not in this repository, so alphaPpYr is null rather than the shrunk number wearing a raw label. Its 31 bp is the fee table's total and its management fee both, with 0.00% of other expenses; a 0.33% reading of this fund is not in its prospectus.",
    issuer: {
      notes: [
        "0.31% management fee, no 12b-1 fee, 0.00% other expenses and 0.31% total annual fund operating expenses, with no waiver line, per its summary prospectus dated 2025-11-28.",
      ],
      source: {
        label: "iShares MSCI EAFE Value ETF, Form 497K dated 2025-11-28",
        docPath: "docs/research/market-scan-2026.md",
        href: "https://www.sec.gov/Archives/edgar/data/1100663/000119312525302176/d949816d497k.htm",
      },
      readOn: asOf("2026-08-24"),
    },
    source: products,
    asOf: asOf("2026-08-24"),
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
      "The only value fund we priced carrying two side loads whose intervals exclude zero: SMB +0.671 on a premium of +0.49 [−1.44, +2.44], and RMW +0.386 on a rejected factor. It is fourth or fifth of five on growth per unit of drift in every window. Its alpha is a window artefact: +2.47 on 45 months, +0.55 on 75 and +1.84 on 55, against floors of 3.96 to 4.64. None of the three is evidence and no verdict may rest on one.",
    issuer: {
      notes: [
        "0.36% total annual fund operating expenses and 4% portfolio turnover in the most recent fiscal year — the lowest turnover of any factor product on this shelf — per its summary prospectus dated 2025-12-31.",
        "Five-year return before taxes 6.35% and after taxes on distributions 5.57% to 2024-12, a drag of 0.78 pp/yr against VXUS's 0.79 over the same period: parity with the fund it would displace.",
        "Median net securities-lending income of 5.97 bp/yr across six fiscal years of Form N-CEN, 2020-08-31 to 2025-08-31, so its net cost is 30.03 bp rather than 36 — the largest fee-to-cost gap of any lean on this shelf.",
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
      "Worst of five on drift per unit of HML at 11.6, and its SMB leg of +0.431 is on a premium that cannot be signed.",
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
    spread: { bp: 1, asOf: SPREADS_READ },
    source: products,
    asOf: READ,
  },
  {
    ticker: "GWX",
    name: "SPDR S&P International Small Cap ETF",
    category: "intl-core",
    mandate:
      "Small companies in developed markets outside the US. The largest exposure any foreign fund here sets out to deliver.",
    expenseRatioBp: 40,
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
      "Trim that single uncovered month and the shortfall falls to between +0.00 and +0.39, all under the threshold. The published verdict stands because the specification was frozen, but it must be read as 'the comparator did not exist for one of its months'. The 40 bp is the whole fee table and there is no waiver line, but no Form N-CEN lending figure was read for it, so its net cost is still unknown.",
    issuer: {
      notes: [
        "0.40% management fee, no 12b-1 fee, 0.00% other expenses and 0.40% total annual fund operating expenses, with no waiver line, per its summary prospectus dated 2026-01-31. The registrant now styles the fund State Street SPDR S&P International Small Cap ETF.",
      ],
      source: {
        label: "SPDR Index Shares Funds, Form 497K dated 2026-01-30",
        docPath: "docs/research/market-scan-2026.md",
        href: "https://www.sec.gov/Archives/edgar/data/1168164/000119312526031217/d833468d497k.htm",
      },
      readOn: asOf("2026-08-24"),
    },
    source: products,
    asOf: asOf("2026-08-24"),
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
      "Delivers +0.535 of UMD over VEA on a signable premium (+8.35 [+4.82, +11.66] against a 5.21 floor), worth +4.47 pp/yr gross and +2.53 net per dollar held. It survives all seven bases at −5.43 to −5.18, and at 0.25% it is what causes IMTM to be rejected.",
    caution:
      "Excluded from the reference portfolio anyway. It files 105%/yr of turnover against VEA's 4%, so cost takes 43% of the gross exposure at k = 1.7 (28% at k = 1.0), and it carries CMA −0.394 on a rejected factor.",
    source: products,
    asOf: READ,
  },
  {
    ticker: "IMTM",
    name: "iShares MSCI Intl Momentum Factor ETF",
    category: "intl-momentum",
    mandate: "Foreign developed shares that have been going up, and the dearer of the two on the fund list.",
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
    mandate: "Emerging markets weighted by size, and what every emerging-market fund here is read against.",
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
    spread: { bp: 1.7, asOf: PORTFOLIO_SPREADS_READ },
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
      "A 50% higher fee than VWO and the cheaper fund to own: lending covers the whole 9 bp and 0.87 bp besides. Its fee is capped at 0.09% to 2030-12-31 with no recoupment — the most durable fee commitment on the fund list.",
    caution:
      "No factor exposure, no alpha and no usable tracking difference were read for it. A high lending yield is partly compensation for holding what short sellers want.",
    spread: { bp: 1, asOf: SPREADS_READ },
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
      "Unresolved on window length, not on failure: 51 months put its interval across the 0.15 bar. The verdict is basis-invariant — no comparator, however expressive, can move an emerging product to exploratory, because clause (a) reads the exposure and unresolved reads its interval and neither reads the basis.",
    caution:
      "The panel does the heaviest work here: the same fund reads −0.074 on the US panel, which would flip the sign of the only evidence that the emerging value premium is purchasable at all. At 36 bp it costs 27 bp a year more than IEMG's 9 bp, which is the extra cost the lean has to clear before its exposure matters — and that exposure is the one this shelf cannot sign. Its net cost is 29.21 bp: 36 bp less a median 6.79 bp of securities lending across four fiscal years of Form N-CEN, 2022-08-31 to 2025-08-31. Turnover and every tax figure for AVES remain unread. Only its shrunk alpha, −0.16 against a 4.48 floor, was published.",
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
    expenseRatioBp: 43,
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
      "The larger of the two emerging value exposures and the shorter window: 44 months, interval across the bar, shortfall −2.19 frozen and −2.03 expressive. unresolved, basis-invariant.",
    caution:
      "Reads −0.092 on the US panel. With AVES it is why the region with the largest measured HML premium — +7.58 [+4.34, +11.01] — has nothing investable audited here. The 43 bp is a net figure that depends on a waiver running only to 2027-02-28; the fee table's gross is 46 bp, and 43 is what the fund list carries because it is what a buyer pays today. Only its shrunk alpha, −1.19 against a 3.23 floor, was published.",
    issuer: {
      notes: [
        "0.38% management fee plus 0.08% other expenses is 0.46% gross, less a 0.03% fee waiver, for 0.43% net, per its summary prospectus dated 2026-02-28. The waiver agreement runs through 2027-02-28.",
      ],
      source: {
        label: "Dimensional ETF Trust, Form 497K dated 2026-02-27",
        docPath: "docs/research/market-scan-2026.md",
        href: "https://www.sec.gov/Archives/edgar/data/1816125/000181612526000066/c497k.htm",
      },
      readOn: asOf("2026-08-24"),
    },
    reviewTrigger: {
      on: asOf("2027-02-28"),
      what: "DFEV's 43 bp is a waived figure. Read the next Dimensional ETF Trust 497K: if the waiver is not renewed the fee goes to the 46 bp gross the same table prints, and the cheapest emerging-value line on this shelf moves by 3 bp. Nothing about the exposure or the unresolved verdict turns on it.",
    },
    source: products,
    asOf: asOf("2026-08-24"),
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
    spread: { bp: 1.38, asOf: PORTFOLIO_SPREADS_READ },
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
    verdict: "2.09 bp net, and the bond leg of the cheapest combination on the fund list at 0.76 bp/yr.",
    caution: null,
    source: structural,
    asOf: READ,
  },
  // -------------------------------------------------------------------------
  // The rest of the bond aisle, added 2026-09-02. TIPS, Treasuries by maturity, cash
  // substitutes, bonds outside the US and corporate credit. Wherever a fund is in the
  // fixed-income cost audit behind `docs/research/setting-the-equity-share.md`, its fee
  // is the fund's own Form 497K fee table and its lending income the median over the
  // fiscal years of Form N-CEN Item C.6, both held as manifests under
  // `research/data-manifests/fixed_income_shelf/` and cited by path; a fund whose N-CEN
  // answers "No" to lending in every filed year carries 0, as BND does. The rest are
  // issuer pages read that day, and say so. None of these has a verdict of its own: the asset-class
  // findings live on the alternatives audit and the evidence base, and a fund is not
  // an asset class.
  // -------------------------------------------------------------------------
  {
    ticker: "VTIP",
    name: "Vanguard Short-Term Inflation-Protected Securities ETF",
    category: "bonds",
    mandate: "TIPS maturing inside five years. Inflation protection with almost no interest-rate risk.",
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
      "Priced only. 3 bp with no lending at all: Vanguard answers Form N-CEN Item C.6.a 'No' in every fiscal year from 2018-09 to 2025-09, so the fee is the whole cost. TIPS and nominal Treasuries are one bet on this repository's measurements, correlated +0.76 to +0.85 across eighteen bond funds, so this adds inflation matching rather than a second way of making money.",
    caution:
      "Short TIPS match a real spending liability and little else; over the 79 filed months every TIPS fund trailed VTI at matched volatility by more than the test could resolve, which is a statement about a bond bear market and not about the fund.",
    issuer: {
      notes: [
        "0.03% total annual fund operating expenses with no waiver, from the ETF Shares 497K dated 2026-01-28, which names the Bloomberg U.S. Treasury Inflation-Protected Securities 0-5 Years Index. Vanguard's 2026-02-01 fee cuts moved the Institutional share class to 0.02%; the ETF class still printed 0.03% on Vanguard's product page on 2026-09-02, with a fee as-of date of 2026-01-28.",
        "Inception 2012-10-12 and $20.5bn of ETF net assets at 2026-08-31, from Vanguard's investor and advisor pages read on 2026-09-02.",
      ],
      source: {
        label: "Vanguard Short-Term Inflation-Protected Securities Index Fund, ETF Shares 497K dated 2026-01-28",
        docPath: "research/data-manifests/fixed_income_shelf/product_facts.json",
        href: "https://www.sec.gov/Archives/edgar/data/836906/000119312526024990/f43883d1.htm",
      },
      readOn: WEB_READ,
    },
    source: {
      ...alternatives,
      anchor: "6c-tips-and-nominal-bonds-are-one-engine-and-that-is-not-an-argument-against-holding-tips",
    },
    asOf: WEB_READ,
  },
  {
    ticker: "STIP",
    name: "iShares 0-5 Year TIPS Bond ETF",
    category: "bonds",
    mandate: "The same short TIPS claim as VTIP, from iShares.",
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
      "Priced only. 3 bp less a 0.06 bp median of lending income over seven filed fiscal years to 2025-10, so 2.94 bp net and a hair cheaper than VTIP to own. Same one-bet reading as VTIP: TIPS and nominal Treasuries move together.",
    caution:
      "Its lending income fell to 0.002 bp in the 2025 fiscal year, so the 0.06 bp difference from VTIP is a median of small numbers and may not persist.",
    issuer: {
      notes: [
        "0.03% management fee and 0.03% total, no waiver, from the 497K dated 2026-02-27, which names the ICE U.S. Treasury 0-5 Year Inflation Linked Bond Index.",
        "Inception 2010-12-01 and $16,280,812,836 of net assets at 2026-09-02, from the iShares product page; the fact sheet printed $15,883.69m at 2026-06-30.",
      ],
      source: {
        label: "iShares 0-5 Year TIPS Bond ETF, Form 497K dated 2026-02-27",
        docPath: "research/data-manifests/fixed_income_shelf/product_facts.json",
        href: "https://www.sec.gov/Archives/edgar/data/1100663/000119312526081782/d33535d497k.htm",
      },
      readOn: WEB_READ,
    },
    source: {
      ...alternatives,
      anchor: "6c-tips-and-nominal-bonds-are-one-engine-and-that-is-not-an-argument-against-holding-tips",
    },
    asOf: WEB_READ,
  },
  {
    ticker: "LTPZ",
    name: "PIMCO 15+ Year U.S. TIPS Index Exchange-Traded Fund",
    category: "bonds",
    mandate: "TIPS with fifteen or more years to run. The most interest-rate risk any inflation-linked fund carries.",
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
      "Priced only, and the dearest TIPS fund on this list at 20 bp against 3 bp for SCHP, VTIP and STIP. Its Form N-CEN says it lends but files no income figure in any of eight fiscal years, so the net cost is unknown rather than 20.",
    caution:
      "The target index's dollar-weighted average maturity was 18.89 years at 2025-09-30, and a real yield move of one point moves a fund of that maturity by roughly a sixth of its value. It fell furthest of the TIPS funds in 2022 for that reason.",
    issuer: {
      notes: [
        "0.20% management fee and 0.20% total, with no 'other expenses' line and no waiver, from the 497K dated 2025-10-31, which names the ICE BofA 15+ Year US Inflation-Linked Treasury Index and its 18.89-year index maturity at 2025-09-30.",
        "Inception 2009-09-03 and $708m of net assets at 2026-06-30, from PIMCO's own ETF quicksheet dated as of that day; PIMCO's product page rendered no data on 2026-09-02. An aggregator showed $877.67m at 2026-09-03.",
      ],
      source: {
        label: "PIMCO 15+ Year U.S. TIPS Index ETF, Form 497K dated 2025-10-31",
        docPath: "research/data-manifests/fixed_income_shelf/product_facts.json",
        href: "https://www.sec.gov/Archives/edgar/data/1450011/000119312525249126/d25858d497k.htm",
      },
      readOn: WEB_READ,
    },
    source: {
      ...alternatives,
      anchor: "6c-tips-and-nominal-bonds-are-one-engine-and-that-is-not-an-argument-against-holding-tips",
    },
    asOf: WEB_READ,
  },
  {
    ticker: "TIPX",
    name: "SPDR Bloomberg 1-10 Year TIPS ETF",
    category: "bonds",
    mandate: "TIPS between one and ten years. The middle of the maturity range, from State Street.",
    expenseRatioBp: 15,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Priced only, from the issuer page rather than a filing: 15 bp gross, five times SCHP for a narrower maturity band. No Form N-CEN was read for it, so lending and net cost are unknown.",
    caution:
      "It was not in the fixed-income audit, so its fee is an issuer-page figure and not a fee-table one; the 497K should be read before it is quoted as a cost.",
    issuer: {
      notes: [
        "0.15% gross expense ratio, with no net figure printed and no waiver stated, inception 2013-05-29 and $2,064.86m of net assets at 2026-09-01, from the State Street product page. Tracks the Bloomberg 1-10 Year U.S. Government Inflation-Linked Bond Index.",
        "State Street Global Advisors became State Street Investment Management on 2025-06-30 and the fund's name now carries the 'State Street SPDR' prefix; ticker, index and fee are unchanged.",
      ],
      source: {
        label: "State Street SPDR Bloomberg 1-10 Year TIPS ETF, issuer page",
        docPath: "docs/research/alternative-sleeves-audit.md",
        href: "https://www.ssga.com/us/en/intermediary/etfs/spdr-bloomberg-1-10-year-tips-etf-tipx",
      },
      readOn: WEB_READ,
    },
    source: {
      ...alternatives,
      anchor: "6c-tips-and-nominal-bonds-are-one-engine-and-that-is-not-an-argument-against-holding-tips",
    },
    asOf: WEB_READ,
  },
  {
    ticker: "VGIT",
    name: "Vanguard Intermediate-Term Treasury ETF",
    category: "bonds",
    mandate: "US Treasuries of three to ten years. The middle of the curve, and nothing else.",
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
      "Priced only. 3 bp and no lending in any of eight filed fiscal years, so 3 bp is the cost. The alternatives audit's third-ranked move is raising the cash and short-to-intermediate Treasury allocation instead of buying a tail hedge, and this is one of the funds that move would be made with.",
    caution:
      "Over the 79 filed months to 2026-05 every nominal Treasury fund's excess return was negative; that is a bond bear market and settles nothing about the next one. A Treasury's pay in a crash is era-dependent, positive in seven of twelve five-year blocks and negative in five.",
    issuer: {
      notes: [
        "0.03% total annual fund operating expenses, no waiver, from the ETF Shares 497K dated 2025-12-19 as supplemented 2026-06-30, whose target index had a dollar-weighted average maturity of 5.6 years at 2025-08-31. Vanguard's 2026-02-01 cuts took the Institutional class to 0.03% from 0.04%; the ETF class was already there.",
        "Inception 2009-11-19 and $39.8bn of ETF net assets at 2026-08-31, from Vanguard's investor and advisor pages read 2026-09-02. Tracks the Bloomberg U.S. Treasury 3-10 Year Index.",
      ],
      source: {
        label: "Vanguard Intermediate-Term Treasury Index Fund, ETF Shares 497K dated 2025-12-19",
        docPath: "research/data-manifests/fixed_income_shelf/product_facts.json",
        href: "https://www.sec.gov/Archives/edgar/data/1021882/000102188226000464/f45475d1.htm",
      },
      readOn: WEB_READ,
    },
    source: { ...alternatives, anchor: "10-consequence-for-the-portfolio" },
    asOf: WEB_READ,
  },
  {
    ticker: "VGLT",
    name: "Vanguard Long-Term Treasury ETF",
    category: "bonds",
    mandate: "US Treasuries of ten years and longer, at Vanguard's price.",
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
      "Priced only. 3 bp with no lending, one fifth of TLT's 15 bp for a similar claim on the long end. Long Treasuries paid in every growth and deflation shock on the century-long panel and lost up to 40% in the inflation ones.",
    caution:
      "The target index's average maturity was 22 years at 2025-08-31. Experiment 018 already declined a stacked long-Treasury leg at 20 points, and the 2022 loss is what a fund of this maturity does when real yields rise two points.",
    issuer: {
      notes: [
        "0.03% total annual fund operating expenses, no waiver, from the ETF Shares 497K dated 2025-12-19 as supplemented 2026-06-30, whose target index had a dollar-weighted average maturity of 22 years at 2025-08-31.",
        "Inception 2009-11-19 and $10.6bn of ETF net assets at 2026-08-31, from Vanguard's pages read 2026-09-02. Tracks the Bloomberg U.S. Long Treasury Bond Index.",
      ],
      source: {
        label: "Vanguard Long-Term Treasury Index Fund, ETF Shares 497K dated 2025-12-19",
        docPath: "research/data-manifests/fixed_income_shelf/product_facts.json",
        href: "https://www.sec.gov/Archives/edgar/data/1021882/000102188226000463/f45478d1.htm",
      },
      readOn: WEB_READ,
    },
    source: { ...alternatives, anchor: "10-consequence-for-the-portfolio" },
    asOf: WEB_READ,
  },
  {
    ticker: "GOVT",
    name: "iShares U.S. Treasury Bond ETF",
    category: "bonds",
    mandate: "The whole Treasury curve from one to thirty years in one fund.",
    expenseRatioBp: 5,
    securitiesLendingBp: 0.05,
    netCostBp: 4.95,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Priced only. 5 bp less a 0.05 bp median of lending income over eight fiscal years to 2025-10, so 4.95 bp net: dearer than VGIT and VGLT and cheaper than TLT for a claim that spans both of theirs.",
    caution:
      "It is the whole curve at market weight, so its interest-rate risk is set by what the Treasury chooses to issue rather than by the holder.",
    issuer: {
      notes: [
        "0.05% management fee and 0.05% total, no waiver, from the 497K dated 2026-02-27.",
        "Inception 2012-02-14 and $41,601,260,510 of net assets at 2026-09-02, from the iShares product page; the fact sheet printed $43,729.89m at 2026-06-30. Tracks the ICE US Treasury Core Bond Index.",
      ],
      source: {
        label: "iShares U.S. Treasury Bond ETF, Form 497K dated 2026-02-27",
        docPath: "research/data-manifests/fixed_income_shelf/product_facts.json",
        href: "https://www.sec.gov/Archives/edgar/data/1100663/000119312526081797/d50915d497k.htm",
      },
      readOn: WEB_READ,
    },
    source: { ...alternatives, anchor: "10-consequence-for-the-portfolio" },
    asOf: WEB_READ,
  },
  {
    ticker: "SGOV",
    name: "iShares 0-3 Month Treasury Bond ETF",
    category: "bonds",
    mandate: "Treasury bills of three months or less. Cash, as a fund.",
    expenseRatioBp: 9,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Priced only, from the issuer page: 9 bp, which is 4.5 bp cheaper than BIL for the same bills. In the lower tail of equity months, cash is the benchmark almost nothing on the alternatives audit beats, and this is the cheapest listed way to hold it.",
    caution:
      "Not in the fixed-income audit, so no fee table or Form N-CEN was read; the 9 bp is the product page's figure. Its income is ordinary and state-tax-exempt, which is a placement question rather than a return one.",
    issuer: {
      notes: [
        "0.09% expense ratio, with the fact sheet showing a 0.09% management fee, 0.00% other expenses and no waiver line; the earlier waiver expired in July 2024. Inception 2020-05-26 and $106,698,501,969 of net assets at 2026-09-02, from the iShares product page. Tracks the ICE 0-3 Month US Treasury Securities Index. Prospectus dated 2026-06-29.",
      ],
      source: {
        label: "iShares 0-3 Month Treasury Bond ETF, issuer page",
        docPath: "docs/research/alternative-sleeves-audit.md",
        href: "https://www.ishares.com/us/products/314116/ishares-0-3-month-treasury-bond-etf",
      },
      readOn: WEB_READ,
    },
    source: { ...alternatives, anchor: "10-consequence-for-the-portfolio" },
    asOf: WEB_READ,
  },
  {
    ticker: "BIL",
    name: "SPDR Bloomberg 1-3 Month T-Bill ETF",
    category: "bonds",
    mandate: "The same Treasury bills as SGOV, in the older and larger fund.",
    expenseRatioBp: 13.53,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict: "Priced only. 13.53 bp gross against SGOV's 9 for the same bills, which is the whole comparison.",
    caution: "The fee is the issuer page's gross figure with no net printed; no filing was read for it.",
    issuer: {
      notes: [
        "0.1353% gross expense ratio, no net figure and no waiver stated, inception 2007-05-25 and $46,183.83m of net assets at 2026-09-01, from the State Street product page. Tracks the Bloomberg 1-3 Month U.S. Treasury Bill Index. Renamed with the 'State Street SPDR' prefix after the 2025-06-30 rebrand; ticker, index and fee unchanged.",
      ],
      source: {
        label: "State Street SPDR Bloomberg 1-3 Month T-Bill ETF, issuer page",
        docPath: "docs/research/alternative-sleeves-audit.md",
        href: "https://www.ssga.com/us/en/intermediary/etfs/spdr-bloomberg-1-3-month-t-bill-etf-bil",
      },
      readOn: WEB_READ,
    },
    source: { ...alternatives, anchor: "10-consequence-for-the-portfolio" },
    asOf: WEB_READ,
  },
  {
    ticker: "BOXX",
    name: "Alpha Architect 1-3 Month Box ETF",
    category: "bonds",
    mandate: "A bill-like return built from index option box spreads, paid as price rather than as interest.",
    expenseRatioBp: 19.49,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "The one fund here whose filed returns were read: 4.28% a year at 0.39% volatility over 44 months from its N-PORT, with a correlation of 0.00 to VTI, and 4.70% a year since 2022-12 by the issuer's own table. The discovery sweep's use for it is as the taxable account's cash and as the observable financing rate that prices the alternative to a stacked fund.",
    caution:
      "The whole case rests on tax treatment that has not been ruled on. The prospectus taxes index options under section 1256 and warns that section 1258 conversion-transaction rules could turn the gain into ordinary income and that the IRS could disagree; press reports in 2026-05 say the IRS has started asking questions, and no ruling either way has been found. It paid an unintended taxable distribution in 2024-08. Its 19.49 bp net fee rests on a 5 bp waiver.",
    reviewTrigger: {
      on: asOf("2027-02-01"),
      what: "Read the prospectus dated on or after 2027-02-01 for the fee waiver. The 2026-02-01 prospectus caps expenses at 0.1949% 'until at least February 1, 2027'; if the cap lapses the fee is 24.49 bp, and if the tax section changes the fund's reason for being here changes with it.",
    },
    issuer: {
      notes: [
        "0.2449% gross less a 0.0500% waiver for 0.1949% net, from the issuer page at 2026-09-02 and the prospectus dated 2026-02-01, which holds the cap 'in place until at least February 1, 2027' and terminable only by the board. Inception 2022-12-27 and $14,636.63m of net assets at 2026-09-02.",
        "Actively managed. It buys exchange-listed box spreads on indexes such as the S&P 500 as synthetic zero-coupon bonds in the one-to-three-month sector; the issuer calls the box market 'an alternative lending market'. The objective no longer mentions capital-gain treatment. The old boxxetf.com domain is parked; the issuer page is funds.alphaarchitect.com.",
      ],
      source: {
        label: "Alpha Architect 1-3 Month Box ETF, issuer page and prospectus dated 2026-02-01",
        docPath: "docs/research/discovery-sweep-2026-09.md",
        href: "https://funds.alphaarchitect.com/boxetf/",
      },
      readOn: WEB_READ,
    },
    source: discovery,
    asOf: WEB_READ,
  },
  {
    ticker: "TLT",
    name: "iShares 20+ Year Treasury Bond ETF",
    category: "bonds",
    mandate:
      "US Treasuries of twenty years and longer. The long end, and the fund the research uses as its duration control.",
    expenseRatioBp: 15,
    securitiesLendingBp: 0.003,
    netCostBp: 14.997,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Priced only. 15 bp less a lending median of 0.003 bp over seven filed fiscal years to 2026-02, which rounds to nothing, so the fee is the cost and it is five times VGLT's. Its own filed monthly return is the duration factor the real-estate regression uses.",
    caution:
      "It is the longest nominal Treasury exposure on this list and the one the 2022 rate rise hurt most. Its 15 bp buys nothing VGLT's 3 bp does not, except a deeper options market that a long holder never uses.",
    issuer: {
      notes: [
        "0.15% management fee and 0.15% total, with 0.00% other expenses and no waiver, from the 497K dated 2026-06-29.",
        "Inception 2002-07-22 and $46,667,171,682 of net assets at 2026-09-02, from the iShares product page; the fact sheet printed $41,099.93m at 2026-06-30. Tracks the ICE US Treasury 20+ Year Bond Index.",
      ],
      source: {
        label: "iShares 20+ Year Treasury Bond ETF, Form 497K dated 2026-06-29",
        docPath: "research/data-manifests/fixed_income_shelf/product_facts.json",
        href: "https://www.sec.gov/Archives/edgar/data/1100663/000119312526287948/d128154d497k.htm",
      },
      readOn: WEB_READ,
    },
    source: { ...alternatives, anchor: "10-consequence-for-the-portfolio" },
    asOf: WEB_READ,
  },
  {
    ticker: "BNDX",
    name: "Vanguard Total International Bond ETF",
    category: "bonds",
    mandate: "Investment-grade bonds outside the US, with the currency risk hedged back to dollars.",
    expenseRatioBp: 7,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Priced only, and nothing about it has been measured: this repository holds no bond history outside the United States beyond an annual panel, which the evidence base names as a gap. 7 bp from Vanguard's fact sheet; no N-CEN read, so lending and net cost are unknown.",
    caution:
      "A hedged fund converts its currency gains into currently taxed income. The currency page reaches 'disqualified from the taxable account' for hedged equity funds on that mechanism; whether the same arithmetic transfers to a hedged bond fund was not examined here.",
    issuer: {
      notes: [
        "0.07% expense ratio as reported in the most recent prospectus, inception 2013-05-31 and $82,965m of ETF net assets ($123,286m for the whole fund) at 2026-06-30, from Vanguard's own fact sheet dated as of that day. Tracks the Bloomberg Global Aggregate ex-USD Float Adjusted RIC Capped Index, hedged, by sampling. Vanguard's script-rendered product pages could not be read on 2026-09-02.",
        "Not on Vanguard's 2026-02-01 fee-cut list for the ETF class; the Institutional class went to 0.03% from 0.06% that day. The last documented ETF cut was to 0.07% from 0.08% in 2022-02.",
      ],
      source: {
        label: "Vanguard Total International Bond ETF, fact sheet as of 2026-06-30",
        docPath: "docs/research/evidence-base.md",
        href: "https://workplace.vanguard.com/assets/corp/fund_communications/pdf_publish/us-products/fact-sheet/F3711.pdf",
      },
      readOn: WEB_READ,
    },
    source: evidence,
    asOf: WEB_READ,
  },
  {
    ticker: "IAGG",
    name: "iShares Core International Aggregate Bond ETF",
    category: "bonds",
    mandate: "The same hedged non-US investment-grade bond claim as BNDX, from iShares.",
    expenseRatioBp: 7,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Priced only, at the same 7 bp as BNDX for a similar index, and unmeasured for the same reason: no bond history outside the US is held here.",
    caution: "Same hedged-fund tax question as BNDX, unexamined for bonds.",
    issuer: {
      notes: [
        "0.07% expense ratio as stated in the prospectus, no waiver, inception 2015-11-30 and $11,850,751,702 of net assets at 2026-09-02, from the iShares product page. Tracks the Bloomberg Global Aggregate ex USD 10% Issuer Capped (Hedged to USD) Index. The last documented cut was to 0.07% from 0.08% on 2022-04-01.",
      ],
      source: {
        label: "iShares Core International Aggregate Bond ETF, issuer page",
        docPath: "docs/research/evidence-base.md",
        href: "https://www.ishares.com/us/products/279626/ishares-international-aggregate-bond-etf",
      },
      readOn: WEB_READ,
    },
    source: evidence,
    asOf: WEB_READ,
  },
  {
    ticker: "BWX",
    name: "SPDR Bloomberg International Treasury Bond ETF",
    category: "bonds",
    mandate:
      "Government bonds outside the US in their own currencies, unhedged. A currency position as much as a bond one.",
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
      "Priced only: 35 bp gross, five times BNDX, for the unhedged version of a similar claim. Unmeasured; the currency page measured what a dollar holder gets from unhedged developed-market exposure through equity funds, not through this.",
    caution:
      "Most of its volatility is exchange rates rather than bonds, so it answers a currency question the holder may not have meant to ask.",
    issuer: {
      notes: [
        "0.35% gross expense ratio, no net printed and no waiver listed, inception 2007-10-02 and $1,306.71m of net assets at 2026-09-01, from the State Street product page. Tracks the Bloomberg Global Treasury ex-US Capped Index, unhedged.",
        "Renamed 'State Street SPDR Bloomberg International Treasury Bond ETF' between the 2025-10-31 and 2026-04-30 schedules of series; ticker, index and fee unchanged. Not among the four funds State Street closed in 2026-05.",
      ],
      source: {
        label: "State Street SPDR Bloomberg International Treasury Bond ETF, issuer page",
        docPath: "docs/research/currency-and-the-international-sleeve.md",
        href: "https://www.ssga.com/us/en/intermediary/etfs/spdr-bloomberg-international-treasury-bond-etf-bwx",
      },
      readOn: WEB_READ,
    },
    source: currency,
    asOf: WEB_READ,
  },
  {
    ticker: "EMB",
    name: "iShares J.P. Morgan USD Emerging Markets Bond ETF",
    category: "bonds",
    mandate: "Emerging-market government bonds issued in dollars. Credit risk on countries, without the currency.",
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
      "Priced only, at 39 bp against VWOB's 15 for a similar dollar-denominated index. Unmeasured: no emerging-market bond history is held here.",
    caution:
      "Sovereign credit spreads widen in the same states that hurt equity, so read it as credit rather than as a second way of making money until something here measures it.",
    issuer: {
      notes: [
        "0.39% expense ratio as stated in the prospectus, no waiver, inception 2007-12-17 and $14,658,306,397 of net assets at 2026-09-02, from the iShares product page. Tracks the J.P. Morgan EMBI Global Diversified Core index. Not among BlackRock's 2026-06-12 liquidations.",
      ],
      source: {
        label: "iShares J.P. Morgan USD Emerging Markets Bond ETF, issuer page",
        docPath: "docs/research/evidence-base.md",
        href: "https://www.ishares.com/us/products/239572/ishares-jp-morgan-usd-emerging-markets-bond-etf",
      },
      readOn: WEB_READ,
    },
    source: evidence,
    asOf: WEB_READ,
  },
  {
    ticker: "VWOB",
    name: "Vanguard Emerging Markets Government Bond ETF",
    category: "bonds",
    mandate: "The same dollar-denominated emerging-market government bond claim as EMB, at Vanguard's price.",
    expenseRatioBp: 15,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Priced only. 15 bp against EMB's 39, which is the whole comparison between the two; neither has been measured here.",
    caution: "Same credit reading as EMB.",
    issuer: {
      notes: [
        "0.13% management fee plus 0.02% other expenses for 0.15% total, with no waiver line, from the prospectus dated 2026-02-27; the fact sheet as of 2026-06-30 prints the same 0.15%, inception 2013-05-31 and $6,278m of ETF net assets ($6,761m for the whole fund). Tracks the Bloomberg USD Emerging Markets Government RIC Capped Index by sampling.",
        "Cut to 0.15% from 0.20% on 2025-02-01, the largest of Vanguard's bond-ETF cuts that year; the Institutional class went to 0.08% from 0.13% on 2026-02-01 and the ETF class did not move.",
      ],
      source: {
        label: "Vanguard Emerging Markets Government Bond ETF, prospectus dated 2026-02-27",
        docPath: "docs/research/evidence-base.md",
        href: "https://fund-docs.vanguard.com/p3820.pdf",
      },
      readOn: WEB_READ,
    },
    source: evidence,
    asOf: WEB_READ,
  },
  {
    ticker: "LQD",
    name: "iShares iBoxx $ Investment Grade Corporate Bond ETF",
    category: "bonds",
    mandate: "Investment-grade US corporate bonds, with all their interest-rate risk left in.",
    expenseRatioBp: 14,
    securitiesLendingBp: 1.94,
    netCostBp: 12.06,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "14 bp less a 1.94 bp lending median over eight fiscal years to 2026-02, so 12.06 bp net: four times VCIT's cost for a similar claim. Its filed monthly returns were regressed against VTI at matched volatility over 79 months and the gap excluded zero, at a floor the test could not otherwise resolve. The alternatives audit's finding is about the instrument: unhedged corporate credit correlates +0.83 with Treasuries, and the duration-hedged spread is the part that is a separate bet.",
    caution:
      "Its lending income runs 0.95 to 3.11 bp across years, so the net cost moves by a couple of bp with the lending market. It is the fund the audit rejected for carrying twenty years of duration in front of the credit it was bought for.",
    issuer: {
      notes: [
        "0.14% management fee and 0.14% total, no waiver, from the 497K dated 2026-06-29.",
        "Inception 2002-07-22 and $31,131,899,302 of net assets at 2026-09-02, from the iShares product page. Tracks the iBoxx USD Liquid Investment Grade Index. LQDW, a different fund, is being renamed around 2026-09-17; LQD is unaffected.",
      ],
      source: {
        label: "iShares iBoxx $ Investment Grade Corporate Bond ETF, Form 497K dated 2026-06-29",
        docPath: "research/data-manifests/fixed_income_shelf/product_facts.json",
        href: "https://www.sec.gov/Archives/edgar/data/1100663/000119312526287952/d128812d497k.htm",
      },
      readOn: WEB_READ,
    },
    source: {
      ...alternatives,
      anchor: "6-duration-hedged-credit-the-rejection-was-about-the-instrument-not-the-mechanism",
    },
    asOf: WEB_READ,
  },
  {
    ticker: "VCIT",
    name: "Vanguard Intermediate-Term Corporate Bond ETF",
    category: "bonds",
    mandate: "Investment-grade US corporate bonds of five to ten years, at Vanguard's price.",
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
      "3 bp with no lending in any of eight filed fiscal years to 2025-08, so 3 bp is the cost and it is the cheapest corporate-bond fund here by a factor of four. Regressed against VTI at matched volatility over 79 filed months alongside LQD and HYG, with the same result: a gap excluding zero on a window that is a bond bear market.",
    caution:
      "Same instrument problem as LQD in a shorter form: the credit spread arrives with seven years of duration attached, and the audit's admitted version of credit has the duration hedged out.",
    issuer: {
      notes: [
        "0.03% total annual fund operating expenses, no waiver, from the ETF Shares 497K dated 2025-12-19 as supplemented 2026-06-30, whose target index had a dollar-weighted average maturity of 7.4 years at 2025-08-31.",
        "Inception 2009-11-19 and $67,268m of ETF net assets ($69,479m for the whole fund) at 2026-06-30, from Vanguard's fact sheet as of that day. Tracks the Bloomberg U.S. 5-10 Year Corporate Bond Index by sampling. A cut to 0.03% from 0.04% on 2025-02-01 appears in search snippets only and was not verified from a fetched page.",
      ],
      source: {
        label: "Vanguard Intermediate-Term Corporate Bond Index Fund, ETF Shares 497K dated 2025-12-19",
        docPath: "research/data-manifests/fixed_income_shelf/product_facts.json",
        href: "https://www.sec.gov/Archives/edgar/data/1021882/000102188226000461/f45481d1.htm",
      },
      readOn: WEB_READ,
    },
    source: {
      ...alternatives,
      anchor: "6-duration-hedged-credit-the-rejection-was-about-the-instrument-not-the-mechanism",
    },
    asOf: WEB_READ,
  },
  {
    ticker: "HYG",
    name: "iShares iBoxx $ High Yield Corporate Bond ETF",
    category: "bonds",
    mandate: "Below-investment-grade US corporate bonds. Equity risk wearing a coupon.",
    expenseRatioBp: 49,
    securitiesLendingBp: 9.19,
    netCostBp: 39.81,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "49 bp less the largest lending income of any bond fund audited, a 9.19 bp median over eight fiscal years to 2026-02, so 39.81 bp net. Regressed against VTI at matched volatility over 79 filed months with LQD and VCIT, with the gap excluding zero. High-yield credit's left tail is the corporate-default state that also hurts equity, which is the audit's reason to hold credit for return rather than for protection.",
    caution:
      "Its lending income swung between 3.6 and 14.8 bp across the eight years, so a third of the fee comes back in good lending years and a twelfth in bad ones. At 39.81 bp net it is thirteen times VCIT.",
    issuer: {
      notes: [
        "0.49% management fee and 0.49% total, no waiver, from the 497K dated 2026-06-29.",
        "Inception 2007-04-04 and $15,546,709,126 of net assets at 2026-09-02, from the iShares product page. Tracks the iBoxx USD Liquid High Yield Index.",
      ],
      source: {
        label: "iShares iBoxx $ High Yield Corporate Bond ETF, Form 497K dated 2026-06-29",
        docPath: "research/data-manifests/fixed_income_shelf/product_facts.json",
        href: "https://www.sec.gov/Archives/edgar/data/1100663/000119312526287950/d128451d497k.htm",
      },
      readOn: WEB_READ,
    },
    source: {
      ...alternatives,
      anchor: "6-duration-hedged-credit-the-rejection-was-about-the-instrument-not-the-mechanism",
    },
    asOf: WEB_READ,
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
      "The one product that delivers this benchmark's exposure: the interval clears the frozen 0.50 bar, one regressor explains 52% of its monthly variance, and the exposure holds across the fixed split and all 19 rolling windows with no sign change. It trailed a cost-free vendor index by 0.48 pp/yr against its 85 bp fee.",
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
      "Audited as a candidate stacked fund and it is not in that category at all. Its 2026-03-31 N-PORT holds no equity ETF, no equity index future and no equity of any kind: 89.5% of net assets in Treasury bills, 4.4% in a money fund, and four total return swaps on DBi managed-futures indices. b is zero, so delta is 1.000 and it keeps none of the +2.44 pp/yr funding-rule gap — the same arithmetic as DBMF, KMLM or any standalone trend fund. 0.20% management plus 0.15% acquired-fund fees is 0.35% with no waiver.",
    caution:
      "$4.38m of net assets at 2026-03-31 makes it the smallest fund on this shelf, below even JPFP, and it did not exist at 2025-12-31. Its whole diversifier leg is bilateral swap exposure, and its Cayman subsidiary held 22.50% of total assets against the 25% RIC cap. Bought at a 30% weight it would pay the full funding-rule gap that the stacked funds exist to avoid, so its 35 bp is cheap for the wrong product rather than cheap for the right one.",
    wrapper: {
      delta: 1,
      fundingCapturePercent: 0,
      allInCostBp: 35,
      grossNotionalPerDollar: 1,
      distributionTaxDragPpYr: null,
      incrementalTaxDragBp: null,
      structureAsOf: asOf("2026-03-31"),
    },
    spread: { bp: 24, asOf: SPREADS_READ },
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
      "Its window could only have found an alpha of 13.14 pp/yr or larger. That is a statement about what the window could see, not that the fund holds no trend.",
    wrapper: {
      delta: 1,
      fundingCapturePercent: 0,
      allInCostBp: 75,
      grossNotionalPerDollar: 1,
      distributionTaxDragPpYr: null,
      incrementalTaxDragBp: null,
      structureAsOf: null,
    },
    spread: { bp: 14, asOf: SPREADS_READ },
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
    caution:
      "Its window could only have found an alpha of 16.49 pp/yr or larger, the worst of the five, on an R² of 0.066.",
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
      "A rules-based managed-futures fund, audited against the same 0.50 delivered-exposure bar as the rest of the fund list.",
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
      "The lowest exposure of the five at +0.099 with an R² of 0.042: on this benchmark it is very nearly not a trend fund at all.",
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
  {
    ticker: "FFUT",
    name: "Fidelity Managed Futures ETF",
    category: "managed-futures",
    mandate: "Trend-following across equity, rates, FX and commodities, from an issuer with distribution.",
    expenseRatioBp: 80,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Repackaging of a mechanism this shelf has already priced five times, and the one variable it changes is the one that has actually decided outcomes here. It listed 2025-06-05 and holds $346.23m at 2026-08-22, which makes it the third-largest managed-futures ETF on this shelf behind DBMF and CTA. `docs/research/live-managed-futures.md` measures 52% attrition of the 2019 cohort inside 6.5 years, and an issuer with Fidelity's distribution is the least likely of these to stop filing.",
    caution:
      "No exposure, no alpha and no tracking difference were measured for it: Experiment 008 predates its inception and it has not been regressed against the AQR index the rest of the trend shelf is scored on, so nothing here says whether it delivers trend. Its 0.80% is a capped figure and not a fee: 0.80% management plus 0.02% of other expenses is 0.82% gross, held to 0.80% by an expense cap that FDS may recoup within the fiscal year. The two net-asset figures in this repository are a quarter apart and both are current for their date — $255.9m at 2026Q2 (`docs/research/trend-marginal-value.md`, its second census table) and $346.23m at 2026-08-22 — and this record carries the later one.",
    issuer: {
      notes: [
        "0.80% management fee plus 0.02% other expenses is 0.82% gross, less a 0.02% fee waiver, for 0.80% net, per its summary prospectus dated 2026-05-30.",
        'The 0.80% is an expense cap rather than a plain waiver, and FDS "reserves the right to recoup through the end of the fiscal year any expenses that were reimbursed during the current fiscal year up to, but not in excess of, the Expense Cap". The arrangement runs through 2027-05-31.',
        "The commodity leg runs through a wholly owned subsidiary, whose fees and expenses the cap excludes.",
      ],
      source: {
        label: "Fidelity Managed Futures ETF, Form 497K dated 2026-05-29",
        docPath: "docs/research/market-scan-2026.md",
        href: "https://www.sec.gov/Archives/edgar/data/1898391/000189839126000077/filing11811.htm",
      },
      readOn: asOf("2026-08-24"),
    },
    reviewTrigger: {
      on: asOf("2027-05-31"),
      what: "The 0.80% expense cap lapses unless the Board extends it, taking the filed net expense to the 0.82% gross the same table prints. The larger question has no date on it and is not answered by re-reading a fee table: whether this fund delivers the AQR index's exposure the way Experiment 008 asked of the other five. It will have three filed years by then, which is still short of the history the trend shelf needs before an alpha can be told from noise.",
    },
    source: scan,
    asOf: asOf("2026-08-22"),
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
      "It delivers the trend exposure it sells, and this is the first measurement of it: TSMOM +0.681 [+0.406, +0.955] over 31 filed months to 2026-04, beside an equity beta of +0.979 [+0.763, +1.195] — one dollar of equity and about seven tenths of a dollar of trend, per dollar of capital, against a filed exposure of one and one. Regressed on DBMF instead of on the vendor index it reads +0.857 [+0.719, +0.995]. Structure and cost are from filings. Its 2026-04-30 N-PORT shows SPDR Portfolio S&P 500 at 74.09% of net assets plus a long E-mini S&P 500 future at 30.94% — 105.0% equity, with a further 6.63% in a Nasdaq-100 future that belongs to the trend book — with a government money fund at 16.04% as collateral and a trend book running ~294% of net assets in gross exposure to deliver ~100% of risk exposure. delta is −0.05, so it keeps 100% of the +2.44 pp/yr funding-rule gap and the hurdle this holding has to clear is 0.00 where a standalone managed-futures fund pays the full 2.44. All-in 0.99%, no waiver, and Form N-CEN for the year ended 2026-01-31 reports no recoupment clause. Distribution tax drag 0.32 pp/yr, 4.5 bp of it incremental once the VTI it displaces is subtracted, and 1.3 bp of portfolio return at a 30% exposure weight.",
    caution:
      "The trend exposure above rests on 31 filed months, which is roughly one market regime. Its 95% interval runs from +0.406 to +0.955, so this window cannot tell one dollar of delivered trend from four fifths of one, and the smallest exposure it could have detected at 80% power is 0.392. It is exposure delivered, not a return earned: there is still no alpha, no Sharpe and no drawdown measured for the fund. It does not disclose its financing cost and files 0.00% of interest expense, like every fund in its family. Its 28-month tax window is entirely a rising market; the failure mode is a flat-equity, strong-trend year, which is the year the holding exists for. Under three years old. Its 9 bp median spread against CTAP's 33 is what separates the two once entry cost is counted — 24 bp/yr on a one-year hold, against 18 bp of fee dispersion across the three stacked funds (`docs/research/market-scan-2026.md` §6.2) — and a spread is paid once where a fee is paid every year.",
    wrapper: {
      delta: -0.05,
      fundingCapturePercent: 100,
      allInCostBp: 99,
      grossNotionalPerDollar: 2.05,
      distributionTaxDragPpYr: 0.32,
      incrementalTaxDragBp: 4.5,
      structureAsOf: asOf("2026-04-30"),
    },
    notionalExposure: [
      { kind: "us-equity", perDollarOfCapital: 1.05 },
      { kind: "trend", perDollarOfCapital: 1.0 },
    ],
    /**
     * The 2026-07-31 filing is the only dated unknown on this record: it extends the trend
     * regression by three months and re-reads the base leg, and it does not exist yet.
     */
    reviewTrigger: {
      on: asOf("2026-09-29"),
      what: "RSST's own Form N-PORT for the period ending 2026-07-31 is due by 2026-09-29 and had not been filed at 2026-09-01; the 2026-04-30 filing of 2026-06-25 is still the latest. Read it for three things. The base leg, summed as the S&P 500 fund plus the S&P 500 future, the way this record now reads it. Item B.5 monthly returns for May, June and July 2026, which extend the trend regression from 31 filed months to 34. And whether the Nasdaq-100 contract is still in the book. A base leg that moves by several points changes the delta above; a refreshed exposure whose interval no longer clears 0.4 changes the verdict; nothing in that filing can promote the fund.",
    },
    issuer: {
      notes: [
        "The fund's own words: \"one dollar invested in the Fund provides approximately one dollar of exposure to the Fund's U.S. Equity strategy and approximately one dollar of exposure to the Fund's Managed Futures strategy\", targeting 100% of each.",
        "The managed-futures leg runs through a wholly-owned Cayman subsidiary capped at 25% of total assets, tested quarterly. The subsidiary is not registered under the 1940 Act, and breaching the cap would put the fund's RIC status at risk.",
        "35 months live at 2026-08-17, at $508.70m of net assets on 2026-08-14 and $528.93m on 2026-08-31, both from the issuer page. The fee table shows no waiver line at all, so 99 bp is both gross and net.",
        "Over its short life it has trailed US equity: the prospectus reports 17.17% a year since inception on 2023-09-05 against 21.50% for the S&P 500. Thirty-five months settles nothing about a holding whose whole purpose is the years equities lose, and it is not evidence either way.",
        "Corrected 2026-09-01. This record previously carried the E-mini S&P 500 line at 33.1% of net assets and the equity leg at 107.2%. The 2026-04-30 filing's own contract value for that position is $128,379,507 against $414,986,862 of net assets, which is 30.94%, and no line in the filing reads 33.1%: the figure is consistent with the filed 373 contracts repriced at a later index level of about 7,365 rather than the filing's 6,884. The equity leg is therefore 105.0%, the delta −0.05 and the gross exposure 2.05 per dollar, and the same read applied to the 2026-04-30 filing of RSSB, MATE and CTAP is what those records already carry. The filing also holds a Nasdaq-100 future at 6.63%, which takes every US equity instrument to 111.7%. It is counted with the trend book rather than the base leg, for the reason MATE's record gives: RSBT runs the identical trend book on a bond base and holds the same Nasdaq contract at 6.64% beside an S&P 500 future at 7.49%, so about 14 points of RSST's index futures are the book's own positions and the base leg is the S&P 500 fund plus the S&P 500 future, as it is for the other two. Under either reading delta is below zero and nothing about the verdict moves.",
      ],
      source: {
        label: "RSST summary prospectus, 497K filed 2026-04-27",
        docPath: "docs/research/capital-efficiency-and-breadth.md",
        href: "https://www.sec.gov/Archives/edgar/data/1924868/000199937126009152/rsst-497k_042726.htm",
      },
      readOn: REFRESH,
    },
    spread: { bp: 9, asOf: SPREADS_READ },
    source: capital,
    asOf: REFRESH,
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
      "The tightest delta on the stacked-fund shelf, and the fee table that least resembles what the fund costs. Its 2026-03-31 N-PORT reads iShares Core S&P 500 at 70.41% of net assets plus a long E-mini S&P 500 future at 32.23% — 102.64% equity — against 95.17% of total-return-swap exposure on CTA plus 3.71% of CTA held outright, 98.88% of trend. delta is −0.027, it keeps the whole +2.44 pp/yr funding-rule gap, the hurdle this holding has to clear is 0.00, and 18.79% sits in T-bills as collateral. Net assets went $4.47m at 2025-12-31 to $123.41m at 2026-03-31 to $157.88m on 2026-08-21.",
    caution:
      "The 0.10% is real, contractual and expiring, and it is not what the trend dollar costs. A total return swap pays the reference fund's return net of that fund's fees, and Acquired Fund Fees and Expenses reaches direct holdings rather than a swap reference — so CTA's own 0.75%, which carries no waiver, rides inside 95.17% of net assets and appears nowhere in this fee table. All-in is about 0.81%/yr today and about 0.99% once the waiver lapses on 2026-12-04, against RSST's 0.99% and MATE's 0.97%. Three further asymmetries, none of them in a fee table: 82.48% of net assets is bilateral swap exposure to Bank of America and 12.70% to Citibank, rather than to a clearing house; the trend leg is an affiliated fund and the prospectus concedes the conflict; and a swap is not a §1256 contract, so the 60/40 split that reaches RSST's and MATE's futures does not reach 95% of this fund's diversifier. Eight months old, and it lost a portfolio manager on 2026-08-07. Its trend exposure is unmeasured because it has three filed monthly returns, not because a stacked fund cannot be regressed — RSST's was measured on 31. Its 30-day median bid-ask spread is 33 bp against RSST's 9, which on a one-year hold is a 24 bp/yr difference on a shelf whose entire fee dispersion across the three candidate stacked funds is 18 bp — so once entry cost is counted CTAP is the dearest of the three and not the cheapest (`docs/research/market-scan-2026.md` §6.2).",
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
      what: "Two dates, and the near one has arrived. Its Form N-PORT for 2026-06-30, filed 2026-08-24, reads iShares Core S&P 500 at 78.45% of net assets plus the E-mini at 30.99%, 109.44% equity, against 113.1% of total-return-swap exposure — 93.2% on a CTA index and 19.9% on CTA itself, all receive-index and pay-SOFR, with Bank of America, BNP Paribas and Citi — so delta is −0.083 on that filing and the conclusion above stands; the structure block still carries the 2026-03-31 read until the verdict is rewritten against the new one. Then on 2026-12-04 the fee waiver lapses unless renewed, taking the filed net expense from 0.10% to 0.28% and the all-in trend dollar from about 0.81% to about 0.99% — at which point it is the same price as RSST with an affiliated-fund conflict and single-bank counterparty exposure attached. If the waiver is renewed on the same terms and the counterparty concentration falls, this becomes the cheapest verified stacked fund on the fund list and the ranking is worth reopening; if it lapses, nothing about the cost case survives.",
    },
    issuer: {
      notes: [
        "Inception 2025-12-08, so eight months live at 2026-08-22, and $157,883,998.76 of net assets on 2026-08-21 — larger than MATE and JPFP together, and the fastest asset growth on this shelf. Its 2026-06-30 N-PORT, filed 2026-08-24, reports $163,366,486; the issuer page reports $153,670,684 on 2026-08-31. The management-fee reduction to 0.07% runs through at least 2026-12-04.",
        "The prospectus fixes both legs in its own summary: the fund uses derivatives to add the Managed Futures Strategy on top of the US Equity Strategy, so that for each one dollar invested it has one dollar of US equity exposure and one dollar of CTA futures exposure.",
        'The trend leg is an affiliated fund reached by swap: "The Fund primarily executes the Managed Futures Strategy indirectly by investing in a total return swap on the Simplify Managed Futures Strategy ETF ("CTA"), which is a US domiciled exchange-traded fund managed by the adviser." The prospectus concedes the conflict: "The adviser is subject to an indirect conflict of interest in allocating the Fund\'s assets to a swap linked to CTA, as CTA is an affiliated fund that may underperform other futures-based funds."',
        'The fee table reads 0.25% management plus 0.03% acquired-fund fees for 0.28% gross, less an 0.18% waiver, for 0.10% net. The waiver is a fee reduction and not an expense cap: "The Fund\'s adviser has contractually agreed, through at least December 4, 2026, to reduce its management fees to 0.07% of the Fund\'s average daily net assets. This agreement may be terminated only by the Simplify Exchange Traded Funds\' Board of Trustees." The words "recoup" and "recapture" do not appear anywhere in the statutory prospectus, so there is nothing to be clawed back — the risk here is the expiry, not a recoupment.',
        "It runs no Cayman subsidiary of its own — Form N-PORT reports zero assets invested in a controlled foreign corporation — because its commodity exposure sits inside CTA, which has one. The 25% RIC cap therefore binds CTA rather than this fund.",
        "Every swap files its financing leg as SOFR plus a spread of 0.00000000, which makes CTAP the only stacked fund on this shelf whose financing spread is disclosed at all. Termination dates are 2049-12-31, so the swaps are evergreen rather than rolling.",
      ],
      source: {
        label: "Simplify US Equity PLUS Managed Futures Strategy ETF, 497K dated 2025-12-05",
        docPath: "docs/research/capital-efficiency-and-breadth.md",
        href: "https://www.sec.gov/Archives/edgar/data/1810747/000182912625009650/simplifyetf_497k.htm",
      },
      readOn: REFRESH,
    },
    spread: { bp: 33, asOf: SPREADS_READ },
    source: capital,
    asOf: REFRESH,
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
      "Its own trend exposure is −0.101 [−0.358, +0.155] on 29 filed months — the negative control that makes RSST's +0.681 readable, since the same sponsor, the same fund structure and the same regression return nothing where there is no trend book. Rejected as a second financed addition and as a replacement. Bonds added on top, paid for by borrowing, do not inherit trend's flat drawdown: resampled, they are the deeper drawdown in 49.7% of histories at 30% exposure and 70.0% at 100%, against trend's 6.9%; at matched 1.6× gross, 60% trend beats 30% trend plus 30% bonds by +1.40 pp/yr and on Sharpe. Its base leg is *global* equity where the incumbent is US, so no single delta scores it for a US-based reader.",
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
        'Its expense example still carries the sentence "The management fee waiver discussed above is reflected only through May 31, 2026" although no waiver appears in the fee table. The statutory prospectus of the same date settles it: before 2026-04-27 the adviser waived its 0.50% unitary fee down to 0.35%, and on 2026-04-27 the board terminated the waiver and cut the management fee itself to 0.35%. So 0.39% (0.35% plus 0.04% of acquired-fund fees) is gross, net and permanent, with nothing to expire and nothing to recoup; the annual report for the year ended 2026-01-31 shows the pre-cut contract at 0.50% waived to 0.35%, waivers not recoupable.',
        "$520.83m of net assets on 2026-08-31 from the issuer page, against $476.6m in the 2026-04-30 N-PORT. Its 30-day median bid-ask spread on the same page and date is 0.16%.",
        "The equity leg is 63% US and 37% ex-US: SPDR Portfolio S&P 1500 at 53.38% of net assets plus the S&P 500 future at 9.54%, against Vanguard Total International at 37.15%, at 2026-04-30; 63.3% and 36.7% on the issuer's 2026-09-01 holdings. The prospectus floor is 40% non-US, or 30% when it judges conditions unfavourable.",
        "The 2025 distribution, paid 2025-12-29 at $0.97883 a share, was about 3.4% of NAV: 73% ordinary income and 27% long-term capital gain, no return of capital, from the annual report for the year ended 2026-01-31. That is the Treasury futures' year-end mark-to-market arriving as a distribution, and it is why this fund sits in a sheltered account or not at all.",
      ],
      source: {
        label: "RSSB summary prospectus, 497K filed 2026-04-27",
        docPath: "docs/research/capital-efficiency-and-breadth.md",
        href: "https://www.sec.gov/Archives/edgar/data/1924868/000199937126009149/rssb-497k_042726.htm",
      },
      readOn: REFRESH,
    },
    spread: { bp: 16, asOf: asOf("2026-08-31") },
    source: capital,
    asOf: REFRESH,
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
      "Its 2026-03-31 N-PORT reads 90.83% equity plus 63.50% Treasury futures, 1.543× gross, delta 0.144 — so it keeps 85.6% of the funding-rule gap and the hurdle this holding has to clear is 0.35 pp/yr. Spread across the exposure added on top, the 0.20% fee is 0.315%.",
    caution:
      "It needs 48.3 bp/yr of Treasury excess return over cash at the 15 bp OIS financing benchmark before the financed addition contributes anything, and both inputs are forecasts. This row previously said 92.0 bp against a basis measured on special-collateral repo, which is not a rate a fund pays. No exposure of any kind has been measured for it.",
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
    ticker: "NTSI",
    name: "WisdomTree International Efficient Core Fund",
    category: "capital-efficient",
    mandate:
      "90 cents of developed-market stocks outside the US and 60 of US Treasuries per dollar. NTSX's international twin.",
    expenseRatioBp: 26,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Same mechanism as NTSX at a 6 bp higher fee, and no Form N-PORT of its own has been read here, so it carries no delta and no measured exposure. The issuer's own standardised figures to 2026-06-30 put it at +6.29% a year since its 2021-05-20 inception against NTSX's +12.81%, and on its filed basis it trailed MSCI EAFE by roughly 3 pp a year while the Treasury leg ran through the 2022 rate rise.",
    caution:
      "A five-year record that begins in 2021 is mostly the 2022 bond bear market, and the mechanism supplies exposure rather than a premium. Its prospectus prints no blended 90/60 benchmark, so no risk-matched comparison exists for it. The 60% Treasury leg is a term premium, which this repository does not count as an edge over an equity index.",
    issuer: {
      notes: [
        "0.26% management fee and 0.26% total annual fund operating expenses, with no waiver, from the summary prospectus dated 2025-11-01. The same document says approximately 90% of net assets in developed-market equities outside the US and Canada, and US Treasury futures at approximately 60% of net assets. The 2021 launch prospectus printed the same fee and the same split.",
        "Inception 2021-05-20. WisdomTree's own pages refused an automated reader on 2026-09-02, so the only size on file is an aggregator's $503.16m at 2026-09-03 and the issuer's $497m at 2026-06-30 recorded in the live stacked-fund page. The FY2025 N-CSR, which would carry lending income, was not read.",
      ],
      source: {
        label: "WisdomTree International Efficient Core Fund, Form 497K dated 2025-11-01",
        docPath: "docs/research/live-stacked-fund-records.md",
        href: "https://www.sec.gov/Archives/edgar/data/1350487/000121465925015714/ntsi497k1025.htm",
      },
      readOn: WEB_READ,
    },
    source: liveStacked,
    asOf: WEB_READ,
  },
  {
    ticker: "NTSE",
    name: "WisdomTree Emerging Markets Efficient Core Fund",
    category: "capital-efficient",
    mandate:
      "90 cents of emerging-market stocks and 60 of US Treasuries per dollar. The smallest of the three Efficient Core funds.",
    expenseRatioBp: 32,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Same mechanism as NTSX at a 12 bp higher fee, no Form N-PORT read here, no delta and no measured exposure. The issuer's own figures to 2026-06-30 give +6.70% a year since 2021-05-20, and on the filed basis it trailed MSCI Emerging Markets by roughly 3 pp a year over the same window.",
    caution:
      "At $57.1m on 2026-06-30 and $56.2m on an aggregator at 2026-09-03 it sits in the size band where this repository's own attrition measurement bites, and an emerging-market equity leg financed with a US Treasury leg is two different bets in one ticker. No risk-matched benchmark is published for it.",
    issuer: {
      notes: [
        "0.32% management fee and 0.32% total annual fund operating expenses, with no waiver, from the summary prospectus dated 2025-11-01, which states approximately 90% of net assets in emerging-market equities and US Treasury futures at approximately 60% of net assets. Unchanged from the 2021 launch documents.",
        "Inception 2021-05-20. WisdomTree's pages refused an automated reader on 2026-09-02; the sizes on file are the issuer's $57.1m at 2026-06-30 from the live stacked-fund page and an aggregator's $56.20m at 2026-09-03.",
      ],
      source: {
        label: "WisdomTree Emerging Markets Efficient Core Fund, Form 497K dated 2025-11-01",
        docPath: "docs/research/live-stacked-fund-records.md",
        href: "https://www.sec.gov/Archives/edgar/data/1350487/000121465925015713/ntse497k1025.htm",
      },
      readOn: WEB_READ,
    },
    source: liveStacked,
    asOf: WEB_READ,
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
      "Its 2026-02-28 N-PORT reads 84.80% equity plus 83.63% gold futures, 1.684× gross, delta 0.182, keeping 81.8% of the funding-rule gap. The all-in cost of the exposure added on top is about 0.60%/yr once ≤40 bp of gold-futures financing is added to the 0.20% fee.",
    caution:
      "As a holding it contributes +0.09 pp/yr where the smallest effect the test could have found is 1.68 — unmeasurable. Its 1.53 pp/yr distribution tax drag is the second largest on the stacked-fund shelf (1.31 restated at a 24%/15%-federal plus 9.3%-CA investor), and the naive rule 'shelter the highest drag' puts it at the front of the queue, which is exactly backwards.",
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
      "Measured from the holdings, and the gap this row used to describe is closed. Its 2026-05-31 N-PORT reads iShares Core S&P 500 at 50.30% of net assets plus one long E-mini S&P 500 future at 65.57% — 115.87% US equity, not the 49.8% base leg recorded here before — against a filed 100% trend target, so delta is −0.159, it keeps the whole +2.44 pp/yr funding-rule gap, and the hurdle this holding has to clear is 0.00 where a standalone managed-futures fund pays the full 2.44. Net assets $39.41m, T-bill collateral 29.54%, and the derivative book runs 404.5% of net assets in gross exposure (284.2% futures, 120.3% FX forwards) to deliver it. The 2026-02-28 filing reads the same way at 111.56% equity and delta −0.116. All-in 0.97%, no waiver.",
    caution:
      "The 65.57% E-mini line is not separable into base completion and the trend book's own equity position, because the trend book trades equity-index futures too and no filing tags a contract to one leg or the other. 115.87% is the filed US-equity total, not a contractual base leg; the contractual floor is the prospectus's 100%, where delta is 0.00. Both reads keep the whole gap, so the conclusion survives the ambiguity and the exact delta does not. Beyond that: eight months old at $39.41m, which is closure territory; the Cayman subsidiary held 21.09% of total assets at 2026-05-31 and 22.12% three months earlier against a 25% cap that costs RIC status if breached and not cured; no exposure measured on any trend benchmark, no return, no Sharpe and no drawdown has been measured for it, and with six filed monthly returns none can be — the constraint is its age, not the source; and it has no SEC-standardised after-tax table because it has not completed a calendar year, so its distribution tax drag is unknown rather than small.",
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
        "Man Active Trend Enhanced ETF — a Man Group fund sub-advised by AHL Partners, not a Return Stacked product and not merger arbitrage. Inception 2025-12-16, so eight months live at 2026-08-22. $39.41m of net assets in the 2026-05-31 N-PORT, which is still its latest filing at 2026-09-01, and $39.87m on 2026-09-01 from an aggregator.",
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
      readOn: REFRESH,
    },
    source: capital,
    asOf: REFRESH,
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
      "Still unmeasurable, and now for a filing-level reason rather than an unexamined one: no Form N-PORT exists for it. Its series is S000101300 in the SEC's own ticker map, and none of the 24 N-PORT filings the J.P. Morgan Exchange-Traded Fund Trust made for the 2026-05-31 period carries that series. It commenced 2026-05-27, so its first holdings filing belongs to the quarter ending 2026-06-30 or 2026-07-31 and is due 2026-08-29 or 2026-09-29. Until one is filed there is no base leg, no diversifier leg and therefore no delta; its stack rests on one sentence of the prospectus, which says only that its total exposure will exceed its net assets, and nothing else. Checked 2026-08-22 and again 2026-09-01: still none, so the 2026-08-29 date has passed and 2026-09-29 is the one that remains.",
    caution:
      "It is the one product that would reorder the stacked-fund cost ranking outright — a 40 bp saving against RSST's 99 bp, on a line where 40 bp is a third of the whole fee — and it cannot yet be recommended. Three months live at about $33m makes it one of the smallest funds on this shelf and among the likeliest to close. It also carries one tax cost the other stacked funds do not disclose: it expects to create and redeem in cash, which forfeits the in-kind shield on its equity leg as well as on what it adds on top. No delta, no exposure, no record — and no Form N-PORT, so all three wait on the same filing.",
    /**
     * The dated review trigger. This is the only entry on the shelf whose structure is
     * unknown for a reason that expires, so the recheck has a date rather than a condition.
     */
    reviewTrigger: {
      on: asOf("2026-09-29"),
      what: "Read JPFP's first Form N-PORT, series S000101300. None had been filed at 2026-09-01: its filings to date are the registration statement, the 497K and 497J of 2026-04-15, a trust SAI of 2026-06-24 and an N-PX of 2026-08-28. So the 2026-08-29 date for a first period ending 2026-06-30 has passed, and the filing is due by 2026-09-29 for a period ending 2026-07-31. Compute delta from the base leg and the diversifier leg the way MATE's and RSST's were computed, summing any equity fund holding and the S&P 500 future that completes it rather than reading the largest line alone. The 497K says what to expect. The managed-futures side is direct futures, forwards and swaps on equity, rate and currency markets, with commodities through a wholly owned Cayman subsidiary of up to 25% of assets; the equity side is direct large-cap US stocks and/or US equity index futures. No ETF and no swap on an affiliated fund, so there is no acquired-fund fee under the 0.59% unitary fee and no CTAP-style swap conflict, and there is no numeric target for either leg. If delta comes back at or below zero, JPFP keeps the whole funding-rule gap at 59 bp against RSST's 99 and MATE's 97, and it reorders the stacked-fund cost ranking outright. That still would not make it holdable at a 30% weight: at about $33m it would be one of the smallest funds on this shelf with three months of record, so a negative delta buys it a place in the comparison, not the allocation. If no filing has appeared by 2026-09-29, that is itself the finding and the next date is the following quarter.",
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
        "It has since commenced. Performance inception 2026-05-27 and Nasdaq listing 2026-05-28, so three months live at 2026-09-01, with $17.07m of net assets on its 2026-06-30 fact sheet and about $33.4m on 2026-09-02 from an aggregator — one of the smallest funds on this shelf and among those with the highest closure risk. No issuer figure was reachable: the J.P. Morgan product page renders its data client-side and returned none.",
        "59 bp unitary, no waiver, no recoupment: 40 bp cheaper than RSST for a structurally similar product, which is why it is a standing review trigger in the research rather than a footnote.",
        "The structure the first N-PORT will be read against, from the 497K of 2026-04-15: the Managed Futures Strategy holds futures, forwards and swaps directly on equity, rate and currency markets, with commodities through the Cayman subsidiary; the U.S. Equity Strategy holds large-cap US stocks replicating broad indexes and/or US equity index futures. No ETF is mentioned on either side, and there is no swap on an index or on an affiliated fund. No N-PORT had been filed at 2026-09-01.",
        'It says only that it "seeks to provide full exposure to each of the Managed Futures Strategy and the U.S. Equity Strategy, simultaneously" and that its total exposure will exceed its net assets. Unlike RSST, RSSB and MATE it publishes no numeric per-dollar breakdown anywhere, so none is stated here.',
        'The commodity leg runs through Managed Futures Plus Fund CS Ltd., a wholly-owned Cayman subsidiary, and the fund gains commodity exposure "by investing up to 25% of the Fund\'s assets" in it.',
        'It discloses a tax cost the other two candidates do not: "the Fund expects to generally effect its creations and redemptions entirely or partially in cash, rather than primarily for in-kind securities. Therefore, it will be required to sell portfolio securities and subsequently recognize a gain on such sales that the Fund might not have recognized if it were to distribute portfolio securities in kind."',
        "Its registration statement never states the §1256 mark-to-market rule for the fund's own regulated futures contracts; the single mention of §1256 in the whole filing is inside the §988(a)(1)(B) foreign-currency election. The rule applies regardless, so this is a disclosure difference from MATE and not an exposure difference.",
      ],
      source: {
        label: "JPMorgan Managed Futures Plus ETF, 485BPOS filed 2026-04-15",
        docPath: "docs/research/capital-efficiency-and-breadth.md",
        href: "https://www.sec.gov/Archives/edgar/data/1485894/000119312526156138/d63821d485bpos.htm",
      },
      readOn: REFRESH,
    },
    source: capital,
    asOf: REFRESH,
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
      "Dominated. Sharpe 0.643 at a correlation of +0.820 to the equity core, against 6 bp of fee and 0.51 pp/yr of distribution tax. It is the equity holding with a screen and a tax bill, not a second way of making money.",
    caution:
      "The smallest alpha this test could have found is 10.93 pp/yr, so the rejection rests on dominance and correlation rather than on a measured alpha. rejected means a falsifier fired, never that the effect is zero.",
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
    category: "bonds",
    mandate: "Inflation-linked Treasuries, audited as a candidate second way of making money in bonds.",
    expenseRatioBp: 18,
    securitiesLendingBp: 0.08,
    netCostBp: 17.92,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: "rejected",
    verdict:
      "Not a second way of making money. Its correlation to the nominal bond funds beside it runs +0.76 to +0.85, and its correlation to equity is +0.131 against nominal bonds' \u22120.076. It is the worse diversifier of the two, which is the opposite of the usual claim.",
    caution:
      "Its net cost of 17.92 bp against SCHP's 2.99 bp is the sharper point: the two correlate +0.9997, so the fee difference is the entire decision. The 0.08 bp of lending is the median of Item C.6 over eight Form N-CEN fiscal years to 2025-10 in the fixed-income audit's manifest, which is where the 17.92 came from; it ran from 0.00 to 0.23 bp across those years.",
    issuer: {
      notes: [
        "0.18% management fee, no 12b-1 fee, 0.00% other expenses and 0.18% total annual fund operating expenses, per its summary prospectus dated 2026-02-27.",
      ],
      source: {
        label: "iShares TIPS Bond ETF, Form 497K dated 2026-02-27",
        docPath: "docs/research/market-scan-2026.md",
        href: "https://www.sec.gov/Archives/edgar/data/1100663/000119312526081826/d191245d497k.htm",
      },
      readOn: asOf("2026-08-24"),
    },
    source: alternatives,
    asOf: asOf("2026-08-24"),
  },
  {
    ticker: "SCHP",
    name: "Schwab U.S. TIPS ETF",
    category: "bonds",
    mandate: "The same inflation-linked Treasuries, at a fifth of the cost.",
    expenseRatioBp: 3,
    securitiesLendingBp: null,
    netCostBp: 2.99,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: "rejected",
    verdict:
      "Correlated +0.9997 with TIP and costs 2.99 bp net against its 17.92. If any TIPS position is held at all, that arithmetic is the whole of the decision about which one.",
    caution:
      "The position itself is rejected on correlation. Being the cheaper way to hold it is not an argument for holding it. The 2.99 bp net rests on the one fiscal year, 2020, in which its Form N-CEN filed a lending income figure; the other seven filed none, so `securitiesLendingBp` stays null.",
    issuer: {
      notes: [
        "0.030% total expense ratio, a single figure with no waiver, inception 2010-08-05 and $16,028,810,838.44 of net assets at 2026-09-01, from Schwab's product page read in a browser on 2026-09-02; the page refuses an automated reader. The 497K dated 2026-04-28 prints the same 0.03% management fee and total, and names the Bloomberg US Treasury Inflation-Linked Bond Index (Series-L); the fund's own N-CSR gives a 7.1-year weighted average maturity and 6.3-year duration at 2025-12-31.",
        "Not among the four Schwab funds whose fees were cut on 2026-06-11.",
      ],
      source: {
        label: "Schwab U.S. TIPS ETF, issuer page and Form 497K dated 2026-04-28",
        docPath: "research/data-manifests/fixed_income_shelf/product_facts.json",
        href: "https://www.schwabassetmanagement.com/products/schp",
      },
      readOn: WEB_READ,
    },
    source: alternatives,
    asOf: WEB_READ,
  },
  // -------------------------------------------------------------------------
  // Gold, commodities, bitcoin, real estate outside the US and a 2x fund, added
  // 2026-09-02. The alternatives audit measured each asset class from long series and
  // never from these funds, so each carries the class finding in its verdict and a
  // null status of its own. A bullion or bitcoin trust holds no securities to lend, so
  // its lending income is 0 by structure, as SPY's is, and its net cost is its fee.
  // -------------------------------------------------------------------------
  {
    ticker: "GLD",
    name: "SPDR Gold Shares",
    category: "alternative",
    mandate: "Physical gold in a trust. The oldest and largest of the four bullion funds, and the dearest.",
    expenseRatioBp: 40,
    securitiesLendingBp: 0,
    netCostBp: 40,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Four times GLDM's fee for the same gold. The audit's verdict on the asset is optional, at most 5%, and only in place of cash or bonds: gold buys about twelve bp a month of lower-tail protection over bills at 16.24% volatility and a 91.2% peak-to-trough, and has earned +1.75% a year over bills since 1975 at a Sharpe of 0.18. None of that was measured on this fund.",
    caution:
      "A bullion trust's long-term gain is taxed as a collectible at 28% plus 3.8%, against 23.8% for equity; GLD's own 10-K says so. Its size buys an options market a long holder never uses, and its fee is paid by selling gold, which is itself a taxable disposal.",
    issuer: {
      notes: [
        "0.40% gross expense ratio, the only figure printed, no waiver stated, inception 2004-11-18 and $146,434.15m of net assets at 2026-09-01, from the State Street product page. A grantor trust holding gold bullion, valued at the LBMA Gold Price PM, with HSBC Bank plc and JPMorgan Chase Bank as custodians.",
        "The 2026-02-09 8-K appointed a new principal executive officer at the sponsor and changed nothing about the fund.",
      ],
      source: {
        label: "SPDR Gold Shares, issuer page",
        docPath: "docs/research/structural-and-tax-edges.md",
        href: "https://www.ssga.com/us/en/intermediary/etfs/spdr-gold-shares-gld",
      },
      readOn: WEB_READ,
    },
    source: {
      ...alternatives,
      anchor: "8-gold-and-commodities-right-about-the-state-wrong-about-the-state-that-hurts",
    },
    asOf: WEB_READ,
  },
  {
    ticker: "IAU",
    name: "iShares Gold Trust",
    category: "alternative",
    mandate: "Physical gold in a trust, from iShares, at 25 bp.",
    expenseRatioBp: 25,
    securitiesLendingBp: 0,
    netCostBp: 25,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "The same gold as GLD at 25 bp instead of 40, and still nearly three times IAUM, its own sponsor's cheaper twin. The audit's gold verdict applies to it unchanged, and nothing was measured on the fund.",
    caution:
      "Collectibles rate on long-term gains, as for every bullion trust. IAU discloses an IRS private letter ruling that an IRA's purchase is not a collectible acquisition, but does not disclose the ruling number, and a ruling binds only its requester.",
    issuer: {
      notes: [
        "0.25% sponsor fee, no waiver stated, inception 2005-01-21 and $64,865,740,715 of net assets at 2026-09-02, from the iShares product page. A grantor trust holding gold bullion; not a 1940-Act investment company.",
      ],
      source: {
        label: "iShares Gold Trust, issuer page",
        docPath: "docs/research/structural-and-tax-edges.md",
        href: "https://www.ishares.com/us/products/239561/ishares-gold-trust-fund",
      },
      readOn: WEB_READ,
    },
    source: {
      ...alternatives,
      anchor: "8-gold-and-commodities-right-about-the-state-wrong-about-the-state-that-hurts",
    },
    asOf: WEB_READ,
  },
  {
    ticker: "IAUM",
    name: "iShares Gold Trust Micro",
    category: "alternative",
    mandate: "Physical gold in a trust, at the lowest fee of the four.",
    expenseRatioBp: 9,
    securitiesLendingBp: 0,
    netCostBp: 9,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "The cheapest listed gold at 9 bp, one bp under GLDM. If gold is held at all, the 31 bp gap to GLD is the whole of the decision about which fund. The asset itself carries the audit's verdict, not a promotion.",
    caution:
      "Collectibles rate on long-term gains. At $7.9bn it is a twentieth of GLD's size, which matters to a trader and not to a holder.",
    issuer: {
      notes: [
        "0.09% sponsor fee, no waiver stated, inception 2021-06-15 and $7,870,219,513 of net assets at 2026-09-02, holding 55.86 tonnes of gold, from the iShares product page. A grantor trust valued at the LBMA Gold Price PM; not a 1940-Act company and not a commodity pool.",
      ],
      source: {
        label: "iShares Gold Trust Micro, issuer page",
        docPath: "docs/research/structural-and-tax-edges.md",
        href: "https://www.ishares.com/us/products/306979/ishares-gold-trust-micro",
      },
      readOn: WEB_READ,
    },
    source: {
      ...alternatives,
      anchor: "8-gold-and-commodities-right-about-the-state-wrong-about-the-state-that-hurts",
    },
    asOf: WEB_READ,
  },
  {
    ticker: "GLDM",
    name: "SPDR Gold MiniShares Trust",
    category: "alternative",
    mandate: "Physical gold in a trust, from the sponsor of GLD, at a quarter of GLD's fee.",
    expenseRatioBp: 10,
    securitiesLendingBp: 0,
    netCostBp: 10,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "10 bp for the same gold GLD charges 40 for, and one bp above IAUM. The asset's verdict is the audit's; the fund was not measured.",
    caution:
      "Collectibles rate on long-term gains. Its 2025-12 custodian change was administrative and cost holders nothing.",
    issuer: {
      notes: [
        "0.10% gross expense ratio, the only figure printed, no waiver stated, inception 2018-06-25 and $31,503.40m of net assets at 2026-09-01, from the State Street product page. A series of the World Gold Trust holding gold bullion.",
        "The 8-K filed 2025-12-05 removed ICBC Standard Bank plc as a custodian, leaving JPMorgan Chase Bank as sole custodian, at no cost to shareholders.",
      ],
      source: {
        label: "SPDR Gold MiniShares Trust, issuer page",
        docPath: "docs/research/structural-and-tax-edges.md",
        href: "https://www.ssga.com/us/en/intermediary/etfs/spdr-gold-minishares-trust-gldm",
      },
      readOn: WEB_READ,
    },
    source: {
      ...alternatives,
      anchor: "8-gold-and-commodities-right-about-the-state-wrong-about-the-state-that-hurts",
    },
    asOf: WEB_READ,
  },
  {
    ticker: "PDBC",
    name: "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF",
    category: "alternative",
    mandate: "A broad basket of commodity futures held through a 1940-Act fund, so it sends a 1099 rather than a K-1.",
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
      "The audit rejects long-only commodities as a diversifier and admits them only as an inflation hedge: their mean in the worst decile of equity months is −1.84%, positive in 36% of them, and they paid in 1973-74 and 2022. That was measured on a century-long series and not on this fund, which is the cheaper and simpler of the two Invesco vehicles to hold.",
    caution:
      "Its 0.59% net rests on a waiver of the 0.15% of acquired-fund fees through 2027-08-31; the gross total is 0.74%. It rebalances by rule and the index it follows changed method on 2025-11-10. The long/short version of this idea is already inside the trend holding, which is why the audit rejects it on overlap rather than on the premium.",
    reviewTrigger: {
      on: asOf("2027-08-31"),
      what: "Read the 497K dated on or after 2027-02-27 for the waiver. The 2026-02-27 prospectus waives the acquired-fund fees 'through August 31, 2027'; if it lapses the fee is 74 bp.",
    },
    issuer: {
      notes: [
        "0.59% management fee, no other expenses, 0.15% acquired fund fees and expenses, 0.74% total, a 0.15% waiver and 0.59% after it, from the 497K dated 2026-02-27, which holds the waiver 'through August 31, 2027'. No portfolio turnover rate is reported because the fund holds only instruments excluded from the calculation.",
        "Inception 2014-11-07 and $7.43bn of market value at 2026-09-01, from the Invesco product page. Actively managed, invests through a Cayman subsidiary, and seeks to exceed the DBIQ Optimum Yield Diversified Commodity Index Excess Return. That index changed method on 2025-11-10: a wider universe chosen annually, annual review of base weights, sector and single-commodity caps and an intra-year rebalance trigger; Invesco says the objective is unchanged.",
      ],
      source: {
        label: "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF, Form 497K dated 2026-02-27",
        docPath: "docs/research/alternative-sleeves-audit.md",
        href: "https://www.sec.gov/Archives/edgar/data/1595386/000119312526079092/d67468d497k.htm",
      },
      readOn: WEB_READ,
    },
    source: {
      ...alternatives,
      anchor: "8-gold-and-commodities-right-about-the-state-wrong-about-the-state-that-hurts",
    },
    asOf: WEB_READ,
  },
  {
    ticker: "DBC",
    name: "Invesco DB Commodity Index Tracking Fund",
    category: "alternative",
    mandate: "The same commodity index as PDBC in a commodity pool, which sends a K-1.",
    expenseRatioBp: 82,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "The older and dearer of the two Invesco commodity funds: 82 bp net against PDBC's 59, plus a Schedule K-1 every spring. The audit's commodity verdict applies to it unchanged, and it was not measured.",
    caution:
      "The structural split the audit names, 1099 against K-1, is larger than the fee difference for most investors and decides which account can hold it at all. Its 0.82% net rests on management-fee waivers reported in its 10-Q rather than in a fee-table line.",
    issuer: {
      notes: [
        "0.85% management fee, an estimated 0.04% futures brokerage fee, 0.89% total and 0.82% net, from the Invesco product page at 2026-09-01, which prints no waiver sentence; the Q2 2026 10-Q reports management-fee waivers of $629,135 for the half year, per a search summary that was not read directly. Inception 2006-02-03 and $1.87bn of market value at 2026-09-01.",
        "A commodity pool, not a 1940-Act company: 'This Fund issues a Schedule K-1'. Tracks the DBIQ Optimum Yield Diversified Commodity Index Excess Return plus bill income, and its 8-K of 2025-09-26 announced the same 2025-11-10 index method change PDBC carries; the page now lists 30 holdings against the old 14.",
      ],
      source: {
        label: "Invesco DB Commodity Index Tracking Fund, issuer page",
        docPath: "docs/research/alternative-sleeves-audit.md",
        href: "https://www.invesco.com/us/en/financial-products/etfs/invesco-db-commodity-index-tracking-fund.html",
      },
      readOn: WEB_READ,
    },
    source: {
      ...alternatives,
      anchor: "8-gold-and-commodities-right-about-the-state-wrong-about-the-state-that-hurts",
    },
    asOf: WEB_READ,
  },
  {
    ticker: "IBIT",
    name: "iShares Bitcoin Trust ETF",
    category: "alternative",
    mandate: "Bitcoin in a trust. The largest of the eleven US spot bitcoin funds.",
    expenseRatioBp: 25,
    securitiesLendingBp: 0,
    netCostBp: 25,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "25 bp against 15 for the Grayscale mini trust and 20 for Bitwise, for the same coin. The audit's verdict on the asset is a declared speculation at 0 to 2%, sized so that total loss is survivable: it has no cash-flow claim, a beta of 1.5 to 1.6 to equity, a mean of −7.51% in the worst decile of equity months, and it deepened portfolio drawdown at every weight tested. Its own one-year return at NAV to 2026-06-30 was −45.62%.",
    caution:
      "Nothing about it diversifies; the case for a position is that the investor wants one and understands it. A 1933-Act grantor trust, not a 1940-Act fund: each sale of coin to pay the fee is a taxable disposal for the holder, and the 28% collectibles rate on gold is not asserted for bitcoin, whose prospectus tax section does not mention it.",
    issuer: {
      notes: [
        "0.25% sponsor fee, no current waiver, inception 2024-01-05 and $60,018,939,295 of net assets at 2026-09-02, from the iShares product page. The Q2 2026 10-Q read on 2026-08-22 gave $43.4bn at 2026-06-30 and the CME CF Bitcoin Reference Rate New York Variant as the pricing benchmark.",
      ],
      source: {
        label: "iShares Bitcoin Trust ETF, issuer page",
        docPath: "docs/research/alternative-sleeves-audit.md",
        href: "https://www.ishares.com/us/products/333011/ishares-bitcoin-trust-etf",
      },
      readOn: WEB_READ,
    },
    source: { ...alternatives, anchor: "3-crypto-the-investor-asked-so-here-is-the-arithmetic" },
    asOf: WEB_READ,
  },
  {
    ticker: "FBTC",
    name: "Fidelity Wise Origin Bitcoin Fund",
    category: "alternative",
    mandate: "Bitcoin in a trust, custodied by Fidelity itself.",
    expenseRatioBp: 25,
    securitiesLendingBp: 0,
    netCostBp: 25,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "The same 25 bp as IBIT for the same coin, priced against Fidelity's own reference rate rather than the CME CF one, which marked the same bitcoin differently on 2026-06-30. The audit's speculation verdict applies unchanged.",
    caution: "Same as IBIT. Fidelity prints no net-asset figure on its own pages; the size on file is an aggregator's.",
    issuer: {
      notes: [
        "0.25% contractual expense ratio, described in the prospectus dated 2026-04-29 as an annual unified fee of 0.25% of the trust's bitcoin holdings, with no waiver in force; inception 2024-01-10, from Fidelity's overview document dated 2026-08-21. A grantor trust, not a 1940-Act company and not a commodity pool, tracking the Fidelity Bitcoin Reference Rate, with Fidelity Digital Assets, N.A. as custodian and BitGo Bank & Trust as an additional custodian named in the 2026 prospectus.",
        "Fidelity publishes no net-asset figure on the pages read; the Q2 2026 10-Q gave $10.3bn at 2026-06-30 and an aggregator showed $13.55bn at 2026-09-02. The prospectus says a grantor trust may not take part in lending activity.",
      ],
      source: {
        label: "Fidelity Wise Origin Bitcoin Fund, issuer page and prospectus dated 2026-04-29",
        docPath: "docs/research/alternative-sleeves-audit.md",
        href: "https://www.fidelity.com/etfs/fbtc",
      },
      readOn: WEB_READ,
    },
    source: { ...alternatives, anchor: "3-crypto-the-investor-asked-so-here-is-the-arithmetic" },
    asOf: WEB_READ,
  },
  {
    ticker: "BTC",
    name: "Grayscale Bitcoin Mini Trust ETF",
    category: "alternative",
    mandate: "Bitcoin in a trust, at the lowest fee of the eleven.",
    expenseRatioBp: 15,
    securitiesLendingBp: 0,
    netCostBp: 15,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "15 bp for the same coin IBIT charges 25 for. If a bitcoin position is held at all, the fee gap is most of the decision about which trust; the position itself carries the audit's speculation verdict.",
    caution:
      "Same grantor-trust tax mechanics as IBIT. It is a Grayscale product and not an iShares one, whatever a ticker of BTC suggests; the iShares trust is IBIT.",
    issuer: {
      notes: [
        "A sponsor's fee of 0.15% a year of the trust's assets less liabilities, with no waiver, $3,188,712,000 of net assets at 2026-06-30 and commencement of operations on 2024-07-31, from the Form 10-Q for the quarter ended 2026-06-30, filed 2026-08-04. Priced against the CoinDesk Bitcoin Benchmark Rate from 2026-04-01, with Coinbase Custody Trust Company as custodian; the sponsor treats the trust as a grantor trust for tax. Grayscale's own product page refused an automated reader on 2026-09-02; an aggregator showed $4.79bn that day.",
      ],
      source: {
        label: "Grayscale Bitcoin Mini Trust ETF, Form 10-Q for the quarter ended 2026-06-30",
        docPath: "docs/research/alternative-sleeves-audit.md",
        href: "https://www.sec.gov/Archives/edgar/data/2015034/000201503426000008/btc-20260630.htm",
      },
      readOn: WEB_READ,
    },
    source: { ...alternatives, anchor: "3-crypto-the-investor-asked-so-here-is-the-arithmetic" },
    asOf: WEB_READ,
  },
  {
    ticker: "BITB",
    name: "Bitwise Bitcoin ETF",
    category: "alternative",
    mandate: "Bitcoin in a trust, from Bitwise, at 20 bp.",
    expenseRatioBp: 20,
    securitiesLendingBp: 0,
    netCostBp: 20,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "20 bp, between the Grayscale mini trust's 15 and IBIT's 25, for the same coin. The audit's speculation verdict applies unchanged.",
    caution:
      "Same grantor-trust tax mechanics as IBIT. Its launch waiver ended in 2024-07 and the 20 bp is the whole fee.",
    issuer: {
      notes: [
        "0.20% sponsor fee, inception 2024-01-10 and $2,924,613,783 of net assets at 2026-09-01, from the Bitwise product page, with Bank of New York Mellon as trust custodian and Coinbase Custody as digital-asset custodian. The page still prints the launch waiver of the whole fee on the first $1bn for six months from listing, which ended in 2024-07. The Q2 2026 10-Q read on 2026-08-22 gave $2.13bn at 2026-06-30 and the CME CF Bitcoin Reference Rate New York Variant as its benchmark.",
      ],
      source: {
        label: "Bitwise Bitcoin ETF, issuer page",
        docPath: "docs/research/alternative-sleeves-audit.md",
        href: "https://bitbetf.com/",
      },
      readOn: WEB_READ,
    },
    source: { ...alternatives, anchor: "3-crypto-the-investor-asked-so-here-is-the-arithmetic" },
    asOf: WEB_READ,
  },
  {
    ticker: "VNQI",
    name: "Vanguard Global ex-U.S. Real Estate ETF",
    category: "alternative",
    mandate: "Listed real estate outside the US, developed and emerging together.",
    expenseRatioBp: 12,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Unmeasured. VNQ's rejection was on dominance against this repository's own equity core, with a Sharpe of 0.157 at a correlation of +0.839, and that was measured on US listed real estate; nothing here has read this fund's returns, so the US finding is a reason to expect the same rather than evidence of it.",
    caution:
      "It holds emerging-market property companies unhedged, at 12 bp, and no Form N-CEN was read for it, so lending and net cost are unknown.",
    issuer: {
      notes: [
        "0.08% management fee plus 0.04% other expenses for 0.12% total, from the prospectus dated 2026-02-27 as supplemented 2026-04-21; Vanguard's product page prints 0.12% as of 2026-02-27. Inception 2010-11-01. $3.6bn of share-class net assets and $3.9bn for the whole fund at 2026-07-31 from the product page; the fact sheet printed $3,421m of ETF net assets at 2026-06-30. Full replication of the S&P Global ex-U.S. Property Index.",
        "Not on Vanguard's 2026-02-01 fee-cut list. The 2026-04-21 supplement's content was not extracted.",
      ],
      source: {
        label: "Vanguard Global ex-U.S. Real Estate Index Fund, prospectus dated 2026-02-27",
        docPath: "docs/research/alternative-sleeves-audit.md",
        href: "https://fund-docs.vanguard.com/p3358.pdf",
      },
      readOn: WEB_READ,
    },
    source: { ...alternatives, anchor: "10-consequence-for-the-portfolio" },
    asOf: WEB_READ,
  },
  {
    ticker: "SSO",
    name: "ProShares Ultra S&P500",
    category: "alternative",
    mandate: "Twice the daily move of the S&P 500, reset every day. Borrowed money in a fund.",
    expenseRatioBp: 87,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "The fund the 2x rows of the daily-reset experiment stand for, priced there at a declared 89 bp fee and a 40 bp swap spread rather than measured. On 99 years of the index a held 2x compounds at 12.65% against 10.17% for 1x, after a 98.4% drawdown and 24 years under water; since 1990 the rows read 16.31% against 11.75% with drawdowns of 87.6% and 54.6%. The decision page's default for this investor is none.",
    caution:
      "The conditional case is a holdability argument and not a return one: an investor whose stated purpose is equity exposure above one with a slow-crash brake, holding no other such fund, could hold 10 to 15 points under a 200-day rule in a sheltered account, displacing stacked-fund capital rather than adding to it. That rule pays 2.7 pp a year of tax in a taxable account and showed zero measurable timing content. The daily reset means a holding period longer than a day returns something other than twice the index, and the issuer says so.",
    issuer: {
      notes: [
        "0.88% gross and 0.87% net expense ratio, with a contractual waiver through 2026-09-30, inception 2006-06-19 and $8,993,790,119 of net assets at 2026-09-02, from the ProShares product page, which states the objective as two times the daily performance of the S&P 500 and warns that 'for any holding period other than a day, your return may be higher or lower than the Daily Target'. The experiment's 89 bp is the earlier published figure.",
        "A 2:1 forward split took effect before the open on 2025-11-20, with ticker and CUSIP unchanged; SSO was not in the 2026-05 split round.",
      ],
      source: {
        label: "ProShares Ultra S&P500, issuer page",
        docPath: "docs/research/leveraged-etfs-and-timing-rules.md",
        href: "https://www.proshares.com/our-etfs/leveraged-and-inverse/sso",
      },
      readOn: WEB_READ,
    },
    reviewTrigger: {
      on: asOf("2026-10-01"),
      what: "Re-read the ProShares page for the fee after the 2026-09-30 waiver date. If the waiver lapses the fee is 88 bp; either figure is inside the 89 the experiment declared.",
    },
    source: { ...leveraged, anchor: "9-the-decision" },
    asOf: WEB_READ,
  },
  // -------------------------------------------------------------------------
  // The rest of the Return Stacked family. Six funds, no measurement, and a category
  // that is deliberately not the wrapper one: `capital-efficient` on this shelf means a
  // base leg and a diversifier leg read off a filing and turned into a delta, and not one
  // of these six has had a Form N-PORT read here. Their fees are their own 497K fee
  // tables; their sizes and since-inception differences are the issuer's own standardised
  // figures, read on 2026-08-23 (`docs/research/live-stacked-fund-records.md`). Five of
  // the five clean cases trail the benchmark the issuer prints beside them, which is a
  // fact about five short windows and not a verdict on stacking.
  // -------------------------------------------------------------------------
  {
    ticker: "RSIT",
    name: "Return Stacked International Stocks & Managed Futures ETF",
    category: "capital-efficient",
    mandate: "Developed international stocks plus a dollar of managed futures on top, financed inside the fund.",
    expenseRatioBp: 98,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "The international twin of RSST, and nothing about it has been measured. It listed 2026-05-06 at $68.53m and is the first fund to stack the two legs this repository separately reaches for — a developed ex-US holding and trend. The only structure available is an issuer-page estimate rather than a filed measurement: an equity leg of roughly 75% SPDW plus 25% MSCI EAFE index futures, so a base leg near 1.00 against a trend leg of 1.00 and a delta near 0.00. Read that as a description off a marketing page. RSST's delta of −0.07 was computed from an N-PORT; this one was not computed at all, which is why this record carries no fund-structure block.",
    caution:
      "Three and a half months old, no Form N-PORT, no filed monthly return, and therefore no exposure, no alpha, no delta and no place in the stacked-fund comparison. Its 15 bp median spread is the second widest of the funds whose Rule 6c-11 disclosure was read, and at $73.39m on 2026-08-31 it sits in the size band where this repository's own attrition measurement bites. It sits in the stacked-fund category on its mandate; it carries no `wrapper` block, because the two legs of that block are read off a filing and this fund has not made one.",
    spread: { bp: 15, asOf: SPREADS_READ },
    reviewTrigger: {
      on: asOf("2026-09-29"),
      what: "Read RSIT's first Form N-PORT — series S000103919, class C000274517, in Tidal Trust II — and compute delta from the base leg and the diversifier leg, summing the equity ETF holding and the index future that completes it rather than reading the largest line alone. None had been filed at 2026-09-01, and none could have been: a fund that commenced 2026-05-06 has its first reporting period ending 2026-07-31, and the filing is due by 2026-09-29, the same date as RSST's own 2026-07-31 filing. A delta at or below zero would put it beside RSST at a 1 bp lower fee; it would still have no measured exposure, because an exposure needs filed monthly returns and one quarter is not a window.",
    },
    issuer: {
      notes: [
        "0.98% all-in from the 497K dated 2026-05-04: a 0.95% management fee, 0.02% of other expenses and 0.01% of acquired-fund fees, with no waiver.",
        "$73.39m of net assets and a 0.14% 30-day median spread on 2026-08-31, both from the issuer page. Inception 2026-05-06.",
      ],
      source: {
        label: "RSIT registration statement, 485BPOS filed 2026-05-04",
        docPath: "docs/research/market-scan-2026.md",
        href: "https://www.sec.gov/Archives/edgar/data/0001924868/000199937126009889/rsit-485bpos_050426.htm",
      },
      readOn: REFRESH,
    },
    source: scan,
    asOf: REFRESH,
  },
  {
    ticker: "RSSX",
    name: "Return Stacked U.S. Stocks & Gold/Bitcoin ETF",
    category: "capital-efficient",
    mandate: "US stocks plus a financed gold-and-bitcoin holding, reached through IBIT and CME bitcoin futures.",
    expenseRatioBp: 67,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "It exists, which is the finding. `docs/research/alternative-sleeves-audit.md` concludes that bitcoin should be funded from the speculation budget by selling equity, and that conclusion is written against a pro-rata construction; this is a financed one, at 0.67% and $70.59m since 2025-05-29. Financing improves the hurdle such a holding has to clear. It does not create a premium where the return evidence is a price expectation, so the audit's verdict is untouched and its scope is not.",
    caution:
      "No exposure, no alpha, no filed delta, and the widest median spread of any fund on this shelf at 28 bp — which on a one-year hold is 42% of its own annual fee. Its since-inception return is +16.44% a year against the S&P 500 total return's +23.81% over the same stretch, both to 2026-07-31 and both the issuer's own standardised figures: a 7.37 pp/yr shortfall over fourteen months, which is a statement about fourteen months of a rising equity market and not about the construction. Its second leg carries the two assets this repository prices most cautiously.",
    spread: { bp: 28, asOf: SPREADS_READ },
    source: liveStacked,
    asOf: asOf("2026-08-22"),
  },
  {
    ticker: "RSSY",
    name: "Return Stacked U.S. Stocks & Futures Yield ETF",
    category: "capital-efficient",
    mandate: "US stocks plus a futures-yield carry book on top, financed inside the fund.",
    expenseRatioBp: 99,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "On the fund list for completeness rather than as a candidate. It listed 2024-05-28 and holds $94.46m, and its second leg is a carry strategy no experiment in this repository has priced or regressed. Since inception it has returned +11.68% a year against the S&P 500 total return's +18.66%, both to 2026-07-31 from the issuer's own standardised table — the second-largest shortfall in the family.",
    caution:
      "No exposure, no alpha, no filed delta and no spread on file. A shortfall against an equity index is what a stacked fund is supposed to produce in a rising equity market, so it falsifies nothing on its own; it is recorded because the whole family's record is, and because a reader comparing the eight funds should not have to reconstruct which six are missing.",
    source: liveStacked,
    asOf: asOf("2026-08-22"),
  },
  {
    ticker: "RSBT",
    name: "Return Stacked Bonds & Managed Futures ETF",
    category: "capital-efficient",
    mandate: "Aggregate bonds plus a dollar of managed futures on top, financed inside the fund.",
    expenseRatioBp: 101,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "The oldest of the six and the one whose base leg this repository would actually pay for: bonds rather than equity, so its funding arithmetic is the 2.08 pp/yr case rather than the 2.44 one. Listed 2023-02-07, $147.27m. Since inception it has returned −0.38% a year against the Bloomberg US Aggregate's +3.16%, both to 2026-07-31 from the issuer's own table.",
    caution:
      "No exposure, no alpha, no filed delta and no spread on file, so it enters no comparison here. Its 101 bp is the dearest fee on this shelf outside KMLM, against a base leg — aggregate bonds — that costs 3 bp to buy on its own, which is the whole of what a stacked bond fund has to justify.",
    source: liveStacked,
    asOf: asOf("2026-08-22"),
  },
  {
    ticker: "RSBY",
    name: "Return Stacked Bonds & Futures Yield ETF",
    category: "capital-efficient",
    mandate: "Aggregate bonds plus a futures-yield carry book on top, financed inside the fund.",
    expenseRatioBp: 101,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "Listed 2024-08-20 at $55.63m, and the worst absolute record in the family: −3.58% a year since inception against the Bloomberg US Aggregate's +2.22%, both to 2026-07-31 from the issuer's own table. Two years is not a verdict on a carry position, and the second-smallest fund in a family whose documented failure mode is closure is not a candidate either.",
    caution:
      "No exposure, no alpha, no filed delta and no spread on file. Its second leg is the same unpriced carry strategy as RSSY's, and neither has been regressed against anything here, so a 5.80 pp/yr shortfall says only that the two years it lived were not the years the position is sold for.",
    source: liveStacked,
    asOf: asOf("2026-08-22"),
  },
  {
    ticker: "RSBA",
    name: "Return Stacked Bonds & Merger Arbitrage ETF",
    category: "capital-efficient",
    mandate: "Aggregate bonds plus a merger-arbitrage book on top, financed inside the fund.",
    expenseRatioBp: 101,
    securitiesLendingBp: null,
    netCostBp: null,
    turnoverPercent: null,
    loadings: [],
    alphaPpYr: null,
    alphaDetectionFloorPpYr: null,
    pedestalPpYr: null,
    status: null,
    verdict:
      "The one clear win in the family and the dullest holding in it. Listed 2024-12-17 at $52.33m, it has returned +4.11% a year since inception against the Bloomberg US Treasury index's +2.87%, both to 2026-07-31 from the issuer's own table — a +1.24 pp/yr difference where five of the other five clean cases are negative. The ordering is worth more than the number: the stacked legs with the largest advertised upside have the largest shortfalls.",
    caution:
      "Twenty months, a subtraction of two figures the issuer prints beside each other, and a benchmark this repository did not choose — that is not a measurement and it is not evidence that merger arbitrage pays. No exposure, no alpha, no filed delta, no spread on file, and at $52.33m it is the smallest of the six. A single positive difference over one short window is exactly the shape of result this shelf discounts, by asking first what its windows could have resolved at all.",
    source: liveStacked,
    asOf: asOf("2026-08-22"),
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
  correction: "Benjamini–Hochberg on the exposures, Holm on the alphas",
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

/** The latest date any record on the shelf was read; every record's own `asOf` is on or before it. */
export const shelfAsOf = WEB_READ;

/** Re-exported so a route can name the owning page without re-declaring a citation. */
export const shelfSources = { products, recommendation, structural, capital, trend } as const;
