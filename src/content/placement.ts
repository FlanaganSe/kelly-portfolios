import { type AsOf, asOf, type Citation } from "~/content/types";
import type { ForeignSleeve, ShelterCandidate, TaxRegime } from "~/lib/placement";

/**
 * Asset location, as data for a calculator rather than as a maxim.
 *
 * "Shelter the higher-yielding asset" is right for bonds by a factor of four and wrong
 * for foreign equity funds once the foreign tax credit is counted. Anything built on
 * this must run the expression and state the bracket it assumed.
 *
 * Every figure is US federal. State income tax is excluded and additive. Non-US
 * investors differ on every line.
 *
 * Two halves. The first states an **asset class**: a yield, a withholding rate and a
 * qualified fraction for "developed ex-US equity" and so on, checked against the
 * research workspace's fixture in `placement.test.ts`. The second states the **seven
 * funds the site publishes**, with the fractions each sponsor filed, which is what the
 * calculator ranks. The two disagree where an asset-class table has to assume a
 * qualified fraction and the funds file theirs.
 */

const structural: Citation = {
  label: "Structural and tax-aware edges",
  docPath: "docs/research/structural-and-tax-edges.md",
};

const investorPlacement: Citation = {
  label: "The portfolio for one investor, account placement",
  docPath: "docs/research/portfolio-for-one-investor.md",
};

// ---------------------------------------------------------------------------
// The rule
// ---------------------------------------------------------------------------

export const priorityRule = {
  plain:
    "The question for a retirement account with limited room is what a dollar of it saves. For every fund except a foreign one the answer is the tax you would pay each year on that fund in a taxable account.",
  whyForeignIsDifferent:
    "Foreign governments withhold tax on dividends before they reach you. In a taxable account you can claim that back. Inside a Roth or a traditional IRA there is no US tax to claim it against, so the withholding is gone. That is the one correction to the familiar rule, and it is smaller than the dividend gap it is usually set against.",
  source: structural,
} as const;

// ---------------------------------------------------------------------------
// The dated inputs behind the asset-class figures
// ---------------------------------------------------------------------------

export interface PlacementInput {
  readonly id: string;
  readonly label: string;
  readonly value: number;
  readonly unit: "percent";
  readonly asOf: AsOf | null;
  readonly provenance: string;
  readonly source: Citation;
}

export const placementInputs: readonly PlacementInput[] = [
  {
    id: "bnd-sec-yield",
    label: "BND SEC 30-day yield",
    value: 4.65,
    unit: "percent",
    asOf: asOf("2026-08-10"),
    provenance: "Vanguard's published yield for the fund.",
    source: {
      ...structural,
      href: "https://investor.vanguard.com/investment-products/etfs/profile/api/0584/yields",
    },
  },
  {
    id: "eafe-dividend-yield",
    label: "MSCI EAFE dividend yield",
    value: 2.6,
    unit: "percent",
    asOf: asOf("2026-07-31"),
    provenance: "MSCI index factsheet.",
    source: {
      ...structural,
      href: "https://www.msci.com/documents/10199/822e3d18-16fb-4d23-9295-11bc9e07b8ba",
    },
  },
  {
    id: "em-dividend-yield",
    label: "MSCI Emerging Markets dividend yield",
    value: 2.03,
    unit: "percent",
    asOf: asOf("2026-07-31"),
    provenance: "MSCI index factsheet.",
    source: {
      ...structural,
      href: "https://www.msci.com/documents/10199/255599/msci-emerging-markets-index-usd-net.pdf",
    },
  },
  {
    id: "us-equity-yield",
    label: "US equity dividend yield",
    value: 1.1,
    unit: "percent",
    asOf: null,
    provenance: "A stated input, not a retrieved measurement. Substitute your own.",
    source: structural,
  },
  {
    id: "withholding-developed",
    label: "Effective withholding, developed ex-US",
    value: 6.068,
    unit: "percent",
    asOf: asOf("2026-08-12"),
    provenance:
      "Vanguard's 2025 foreign tax credit worksheet states foreign tax as a share of ordinary cash dividends: VEA 6.46%, VXUS 7.11%, VWO 10.93%. Converting to the grossed-up Box 1a basis the shareholder actually reports gives 6.068%. iShares' 2025 tax supplement cross-validates the method from a different sponsor.",
    source: {
      ...structural,
      href: "https://investor.vanguard.com/content/dam/retail/us/en/pdfs/taxes/ftcws-012026.pdf",
    },
  },
  {
    id: "withholding-emerging",
    label: "Effective withholding, emerging",
    value: 9.853,
    unit: "percent",
    asOf: asOf("2026-08-12"),
    provenance:
      "The same worksheet and the same gross-up. Emerging forfeits more while yielding less, because its withholding rate is 62% higher.",
    source: {
      ...structural,
      href: "https://investor.vanguard.com/content/dam/retail/us/en/pdfs/taxes/ftcws-012026.pdf",
    },
  },
  {
    id: "top-ordinary-rate",
    label: "Top ordinary rate",
    value: 40.8,
    unit: "percent",
    asOf: asOf("2026-08-12"),
    provenance:
      "Top marginal rate including the 3.8% surtax on investment income. It belongs with the 23.8% qualified rate.",
    source: structural,
  },
];

/** The four US qualified-dividend rates. */
export const qualifiedRates: readonly number[] = [0, 15, 18.8, 23.8];

// ---------------------------------------------------------------------------
// Two tax facts a page may quote
// ---------------------------------------------------------------------------

export const form1116Threshold = {
  singleUsd: 300,
  jointUsd: 600,
  holdingsSingleUsd: 190153,
  holdingsJointUsd: 380305,
  detail:
    "Below $300 of foreign tax paid in a year ($600 filing jointly) you claim it back directly with no Form 1116. At the developed-markets withholding rate that threshold arrives at $190,153 of foreign holdings, or $380,305 filing jointly.",
  source: { ...structural, href: "https://www.irs.gov/instructions/i1116" },
  asOf: asOf("2026-08-12"),
} as const;

export const washSaleTrap = {
  headline: "Wash-sale checking has to cover every account in the household.",
  detail:
    "A wash sale in a taxable account only delays the loss, because it is added to the cost of the replacement shares. Buy the replacement inside an IRA instead and the loss is disallowed with nothing to add it to, so the deduction is destroyed rather than delayed.",
  costBp: 119,
  costBasis: "A disallowance of 5% of the portfolio at the top rate.",
  source: structural,
  asOf: asOf("2026-08-12"),
} as const;

export const placementSource = { structural, investorPlacement } as const;
export const placementAsOf = asOf("2026-08-23");

// ---------------------------------------------------------------------------
// The asset-class inputs, in the shape the arithmetic consumes
// ---------------------------------------------------------------------------

/**
 * `~/lib/placement` carries no data at all, because a tax rate "must be a dated
 * jurisdiction-specific input, never a hardcoded financial truth". This is the one place
 * the two meet, and `placement.test.ts` checks these constants against the research
 * workspace's fixture rather than against each other.
 */

export type TaxRegimeId = "us-top" | "us-upper-middle" | "us-zero-ltcg";

export interface NamedTaxRegime extends TaxRegime {
  readonly id: TaxRegimeId;
  readonly source: Citation;
}

/** 37% ordinary, 20% long-term, plus the 3.8% surtax. */
const usTopBracket: NamedTaxRegime = {
  id: "us-top",
  label: "US top marginal bracket",
  asOf: asOf("2026-08-12"),
  ordinaryIncome: 0.37,
  longTermCapitalGain: 0.2,
  netInvestmentIncome: 0.038,
  source: structural,
};

/** 24% ordinary, 15% long-term, below the surtax threshold. */
const usUpperMiddleBracket: NamedTaxRegime = {
  id: "us-upper-middle",
  label: "US upper-middle bracket",
  asOf: asOf("2026-08-12"),
  ordinaryIncome: 0.24,
  longTermCapitalGain: 0.15,
  netInvestmentIncome: 0,
  source: structural,
};

/** 12% ordinary and a 0% long-term rate, where the foreign credit is worth nothing. */
const usZeroLongTermBracket: NamedTaxRegime = {
  id: "us-zero-ltcg",
  label: "US zero long-term-rate bracket",
  asOf: asOf("2026-08-12"),
  ordinaryIncome: 0.12,
  longTermCapitalGain: 0,
  netInvestmentIncome: 0,
  source: structural,
};

export const taxRegimes: readonly NamedTaxRegime[] = [usTopBracket, usUpperMiddleBracket, usZeroLongTermBracket];

/** The bracket every figure assumes until a reader says otherwise. */
export const defaultTaxRegime: NamedTaxRegime = usTopBracket;

export interface NamedShelterCandidate extends ShelterCandidate {
  readonly id: string;
  readonly asOf: AsOf;
  readonly source: Citation;
}

/** BND's SEC 30-day yield, taxed as ordinary income in full. */
export const bondCandidate: NamedShelterCandidate = {
  id: "bonds",
  label: "Taxable investment-grade bonds",
  dividendYield: 0.0465,
  qualifiedFraction: 0,
  foreignWithholdingRate: 0,
  asOf: asOf("2026-08-10"),
  source: structural,
};

/** MSCI EAFE's yield, withheld at the grossed-up rate. */
export const developedCandidate: NamedShelterCandidate = {
  id: "developed",
  label: "Developed ex-US equity",
  dividendYield: 0.026,
  qualifiedFraction: 1,
  foreignWithholdingRate: 0.06068,
  asOf: asOf("2026-07-31"),
  source: structural,
};

/** Yields less than developed and forfeits more, because its withholding rate is 62% higher. */
export const emergingCandidate: NamedShelterCandidate = {
  id: "emerging",
  label: "Emerging-market equity",
  dividendYield: 0.0203,
  qualifiedFraction: 1,
  foreignWithholdingRate: 0.09853,
  asOf: asOf("2026-07-31"),
  source: structural,
};

/** A stated input rather than a retrieved measurement. */
export const usEquityCandidate: NamedShelterCandidate = {
  id: "us-equity",
  label: "US equity",
  dividendYield: 0.011,
  qualifiedFraction: 1,
  foreignWithholdingRate: 0,
  asOf: asOf("2026-08-12"),
  source: structural,
};

export const shelterCandidates: readonly NamedShelterCandidate[] = [
  bondCandidate,
  developedCandidate,
  emergingCandidate,
  usEquityCandidate,
];

export interface NamedForeignSleeve extends ForeignSleeve {
  readonly id: string;
  readonly asOf: AsOf;
  readonly source: Citation;
}

export const developedSleeve: NamedForeignSleeve = {
  id: "developed",
  label: "Developed ex-US equity",
  dividendYield: 0.026,
  withholdingRate: 0.06068,
  asOf: asOf("2026-08-12"),
  source: structural,
};

export const emergingSleeve: NamedForeignSleeve = {
  id: "emerging",
  label: "Emerging-market equity",
  dividendYield: 0.0203,
  withholdingRate: 0.09853,
  asOf: asOf("2026-08-12"),
  source: structural,
};

export const foreignSleeves: readonly NamedForeignSleeve[] = [developedSleeve, emergingSleeve];

// ---------------------------------------------------------------------------
// The eight funds the Plus trend portfolio holds
// ---------------------------------------------------------------------------

/**
 * One row per fund at its printed weight in the Plus trend portfolio: RSST 25, VTI 19,
 * VXUS 16, VTV 15, AVDV 10, IDMO 5, AVES 5, SCHP 5. RSST appears twice because it files
 * two readings of its own income. SCHP has no filed distribution of its own here; it is
 * priced on `bondCandidate`, a plain bond fund's yield taxed like wages in full, which
 * understates it (inflation-protected bonds also owe tax on inflation not yet paid).
 *
 * Three of the yields are filed for this exact fund. Three are derived from a sponsor's
 * filed figures for a sibling fund and say so in `provenance`. Every derived assumption
 * pushes its fund toward the taxable account, so the plan is conservative in the
 * direction it is uncertain.
 *
 * `priorityBp` is the research workspace's own figure at 23.8% / 18.8% / 15% qualified,
 * paired with 40.8% / 35.8% / 24% ordinary. `placement-model.test.ts` reproduces the
 * first and last columns from the three filed inputs.
 */
export interface InvestorHolding {
  readonly ticker: string;
  readonly name: string;
  /** A bond fund is ranked like any other line but is never one of the "US stock funds". */
  readonly assetClass: "stock" | "bond";
  /** Fraction of the whole portfolio. */
  readonly weight: number;
  readonly expenseRatioBp: number;
  /** The whole annual taxable distribution as a fraction of net assets: Box 1a grossed up for creditable foreign tax, plus Box 2a. */
  readonly boxOneAYield: number;
  /** Share of that taxed at the long-term rate: qualified dividends plus any long-term capital-gain distribution. */
  readonly capitalGainRateFraction: number;
  /** Creditable foreign tax passed through to the shareholder, as a fraction of net assets. */
  readonly creditableForeignTaxYield: number;
  /** What a dollar of shelter capacity saves a year, in hundredths of a percent, at 23.8% / 18.8% / 15% qualified. */
  readonly priorityBp: readonly [number, number, number];
  readonly account: "retirement" | "taxable" | "split";
  /** One clause a reader sees beside the account: why this fund lands where it does. */
  readonly reason: string;
  readonly provenance: string;
  readonly asOf: AsOf;
}

/** The three qualified-dividend rates the plan is reported across. 20% without the surtax is unreachable. */
export const investorRates: readonly number[] = [23.8, 18.8, 15];

export const investorHoldings: readonly InvestorHolding[] = [
  {
    ticker: "RSST",
    name: "US stocks plus a trend-following strategy, counting all the income it has recorded",
    assetClass: "stock",
    weight: 0.25,
    expenseRatioBp: 99,
    boxOneAYield: 0.09273,
    capitalGainRateFraction: 0.10504,
    creditableForeignTaxYield: 0,
    priorityBp: [361.78, 315.41, 213.79],
    account: "retirement",
    reason: "its trend profits are taxed like wages, and most of them have not been paid out yet",
    provenance:
      "Tidal Trust II annual report for the year ended 2026-01-31. Income recognised but not paid out went from 1.40% to 8.56% of net assets in one year while the fund paid out 0.33%, so about 8.43% of net assets was recognised and not distributed. The trust's own note says the income of its offshore subsidiaries is included in taxable income each year, and reserves the right to retain it.",
    asOf: asOf("2026-01-31"),
  },
  {
    ticker: "RSST",
    name: "US stocks plus a trend-following strategy, counting only what it has paid out",
    assetClass: "stock",
    weight: 0.25,
    expenseRatioBp: 99,
    boxOneAYield: 0.01285,
    capitalGainRateFraction: 0.8565,
    creditableForeignTaxYield: 0,
    priorityBp: [33.72, 27.29, 20.93],
    account: "split",
    reason: "on what it has actually paid out it is an ordinary US stock fund with a small dividend",
    provenance:
      "The same filing, counting only what shareholders were taxed on: $915,484 of income taxed like wages and $2,648,642 of long-term capital gain, $0.32 a share on a $24.91 opening net asset value. The fund's own prospectus reports 17.17% a year before tax against 16.85% after taxes on distributions since inception, which is this reading measured independently.",
    asOf: asOf("2026-01-31"),
  },
  {
    ticker: "IDMO",
    name: "Invesco S&P International Developed Momentum ETF",
    assetClass: "stock",
    weight: 0.05,
    expenseRatioBp: 25,
    boxOneAYield: 0.044031,
    capitalGainRateFraction: 0.2557,
    creditableForeignTaxYield: 0.001229,
    priorityBp: [148.22, 126.2, 83.25],
    account: "retirement",
    reason:
      "it sells and replaces its whole portfolio every year and pays out the gains, most of them taxed like wages",
    provenance:
      "Invesco Exchange-Traded Fund Trust II annual report for the year ended 2025-10-31. Qualified dividend income 25% of ordinary dividends; portfolio turnover 105%; foreign tax $0.0317 against foreign source income $0.5841 a share. Undistributed income and gains were paid out on 2025-12-22 as $0.68417 of short-term and $0.27579 of long-term gain a share. One fiscal year, and the capital-gain line is the least durable figure in this table.",
    asOf: asOf("2025-10-31"),
  },
  {
    ticker: "AVES",
    name: "Avantis Emerging Markets Value ETF",
    assetClass: "stock",
    weight: 0.05,
    expenseRatioBp: 36,
    boxOneAYield: 0.0391,
    capitalGainRateFraction: 0.4448,
    creditableForeignTaxYield: 0.004598,
    priorityBp: [83.98, 64.43, 32.21],
    account: "retirement",
    reason: "a high dividend, less than half of it taxed at the lower rate",
    provenance:
      "Avantis 2025 tax centre: qualified dividend income 44.48%, foreign source income 92.34% of Box 1a, foreign tax 11.759% of Box 1a from the 2025 ICI file. Yield is the fiscal-2025 net investment income ratio of 3.45% from American Century ETF Trust's annual report, grossed to the Box 1a base. No capital-gain distribution since inception.",
    asOf: asOf("2025-08-31"),
  },
  {
    ticker: "AVDV",
    name: "Avantis International Small Cap Value ETF",
    assetClass: "stock",
    weight: 0.1,
    expenseRatioBp: 36,
    boxOneAYield: 0.027893,
    capitalGainRateFraction: 0.662741,
    creditableForeignTaxYield: 0.0016925,
    priorityBp: [65.45, 51.51, 33.38],
    account: "retirement",
    reason: "a foreign dividend near 2.8%, a third of it taxed like wages",
    provenance:
      "Derived, not filed for this fund: cash yield 2.62% grossed up at the developed ex-US withholding rate of 6.068% of Box 1a, and the qualified fraction taken from VEA's filed 66.2741% because Avantis' per-fund figure for AVDV was not retrieved. Read 2026-08-23.",
    asOf: asOf("2026-08-23"),
  },
  {
    ticker: "VXUS",
    name: "Vanguard Total International Stock ETF",
    assetClass: "stock",
    weight: 0.16,
    expenseRatioBp: 5,
    boxOneAYield: 0.02678,
    capitalGainRateFraction: 0.584,
    creditableForeignTaxYield: 0.001777,
    priorityBp: [64.91, 51.52, 32.43],
    account: "retirement",
    reason:
      "a foreign dividend near 2.7%, and the credit you would keep in a taxable account is a fifth of the tax you would pay there",
    provenance:
      "Derived: cash yield 2.50% grossed up by Vanguard's filed 7.11% of ordinary dividends withheld; qualified fraction a 75/25 blend of VEA's filed 66.27% and VWO's 34.63%, the two funds VXUS combines. Read 2026-08-23.",
    asOf: asOf("2026-08-23"),
  },
  {
    ticker: "VTV",
    name: "Vanguard Value ETF",
    assetClass: "stock",
    weight: 0.15,
    expenseRatioBp: 3,
    boxOneAYield: 0.0181,
    capitalGainRateFraction: 1,
    creditableForeignTaxYield: 0,
    priorityBp: [43.08, 34.03, 27.15],
    account: "split",
    reason: "a modest US dividend, all of it taxed at the lower rate, and no capital-gain payouts",
    provenance:
      "Trailing twelve-month yield 1.81% from StockAnalysis, read 2026-08-23. The qualified fraction of 1.00 is an assumption; Vanguard's per-fund figure was not retrieved.",
    asOf: asOf("2026-08-23"),
  },
  {
    ticker: "VTI",
    name: "Vanguard Total Stock Market ETF",
    assetClass: "stock",
    weight: 0.19,
    expenseRatioBp: 3,
    boxOneAYield: 0.01067,
    capitalGainRateFraction: 1,
    creditableForeignTaxYield: 0,
    priorityBp: [25.39, 20.06, 16.01],
    account: "taxable",
    reason:
      "the smallest dividend on the list, all of it taxed at the lower rate, so it costs the least to leave in a taxable account",
    provenance:
      "Vanguard's published fund-yield endpoint: SEC 30-day yield 1.03% and forecast dividend yield 1.0670%, both effective 2026-07-31, fee 0.03%. Renamed Vanguard Morningstar Total Stock Market ETF on 2026-07-29; objective and management unchanged. The qualified fraction of 1.00 is an assumption.",
    asOf: asOf("2026-07-31"),
  },
  {
    ticker: "SCHP",
    name: "Inflation-protected US government bonds",
    assetClass: "bond",
    weight: 0.05,
    expenseRatioBp: 3,
    boxOneAYield: 0.0465,
    capitalGainRateFraction: 0,
    creditableForeignTaxYield: 0,
    priorityBp: [189.72, 166.47, 111.6],
    account: "retirement",
    reason: "bond interest is taxed like wages, and the inflation adjustment is taxed before it is paid",
    provenance:
      "Not filed for this fund. Priced on a plain bond fund's yield, BND's SEC 30-day yield of 4.65% on 2026-08-10, taxed like wages in full, the same input as `bondCandidate`. An inflation-protected fund also owes tax each year on the inflation adjustment before it is paid, so this understates the case for the retirement account.",
    asOf: asOf("2026-08-10"),
  },
];

/**
 * Foreign tax credit permanently destroyed by sheltering all four international funds,
 * in hundredths of a percent a year of the whole portfolio. Already inside every
 * priority figure above, never added again.
 */
export const creditForfeitedByPlanBp = 7.45;

/**
 * The two shelters treat every fund above identically, so the ranking cannot choose
 * between them. What can: a Roth is never taxed again and never forced to pay out, so
 * it should hold whatever you expect to grow most and never sell; a traditional account
 * must start paying out at 73, so it should hold whatever you expect to trim anyway.
 */
export const rothVersusTraditionalNote =
  "If you have both a Roth and a pre-tax account, RSST and the bond fund go in the pre-tax account and the foreign funds go in the Roth. The Roth is never taxed again and never forced to pay out in your lifetime, so give it what you expect to grow most and never sell. The pre-tax account has to start paying out at 73, so give it what you would trim first.";
