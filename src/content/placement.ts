import { type AsOf, asOf, type Citation } from "~/content/types";
import type { ForeignSleeve, ShelterCandidate, TaxRegime } from "~/lib/placement";

/**
 * Asset location, as data for a calculator rather than as a maxim.
 *
 * "Shelter the higher-yielding asset" is right for bonds by a factor of four and
 * wrong for emerging-market equity at two of the four US dividend rates. Anything
 * built on this must run the expression and state the bracket it assumed.
 *
 * Every figure is US federal, for the stated reference investor. State income tax is
 * excluded and additive. Non-US investors differ on every line.
 */

const structural: Citation = {
  label: "Structural and tax-aware edges",
  docPath: "docs/research/structural-and-tax-edges.md",
};

const recommendation: Citation = {
  label: "The recommended portfolio",
  docPath: "docs/research/portfolio-recommendation.md",
};

// ---------------------------------------------------------------------------
// The rule
// ---------------------------------------------------------------------------

export const priorityRule = {
  formula: "priority = (recurring tax if held in taxable) − (irrecoverable withholding if sheltered)",
  plain:
    "The right question for a scarce shelter is what a sheltered dollar saves, not which asset sounds tax-inefficient. For everything except a foreign holding the second term is zero and this collapses to the familiar rule.",
  whyForeignIsDifferent:
    "Foreign withholding is paid and permanently lost inside a traditional IRA and a Roth alike. An IRA is exempt from taxation under this subtitle, so it has no tax to credit against and a §904 numerator of zero. No IRS publication states this in terms; it is asserted from the statute.",
  treatyRoute:
    "The treaty route does not rescue it. The US–Japan and US–UK conventions exempt a resident pension fund from dividend withholding, then disapply the exemption for a pooled investment vehicle. The beneficial owner of the shares inside VEA is the fund, not the IRA, so the pension rate is unreachable through an index fund by construction.",
  source: structural,
} as const;

// ---------------------------------------------------------------------------
// The dated inputs
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
      "Vanguard's 2025 foreign tax credit worksheet states foreign tax as a share of ordinary cash dividends: VEA 6.46%, VXUS 7.11%, VWO 10.93%. Converting to the grossed-up §853 Box 1a basis the shareholder actually reports gives 6.068%. iShares' 2025 tax supplement cross-validates the method from a different sponsor.",
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
      "Top marginal rate including the §1411 surtax. It belongs with the 23.8% qualified rate and with no other column.",
    source: structural,
  },
];

/** The four US qualified-dividend rates. The schedule is why one sleeve inverts and the other does not. */
export const qualifiedRates: readonly number[] = [0, 15, 18.8, 23.8];

// ---------------------------------------------------------------------------
// What a shelter costs an international sleeve
// ---------------------------------------------------------------------------

export const withholdingForfeited = {
  developedBp: 15.78,
  emergingBp: 20.0,
  blend70_30Bp: 17.04,
  blendAt30PercentOfEquityBp: 5.11,
  arithmetic: "developed: 2.60% × 6.068% = 15.78 bp/yr. emerging: 2.03% × 9.853% = 20.00 bp/yr.",
  note: "The two sleeves cannot be treated as one international line.",
  source: structural,
  asOf: asOf("2026-08-12"),
} as const;

export const breakEvens = {
  formula: "q* = u·w·y_i / (y_i − y_d)",
  developedPercent: 10.52,
  emergingPercent: 21.51,
  whyEmergingInverts:
    "The US schedule offers 0%, 15%, 18.8% and 23.8%. The developed break-even falls below every positive rate, so developed ex-US always belongs in the shelter ahead of US equity. The emerging break-even falls between two live rates. That is a fact about the bracket schedule, not about the funds.",
  zeroBracketTrap:
    "The 0% bracket looks like the strongest case for holding international in taxable and is worth exactly nothing. §904 limits the credit to US tax on foreign-source income, and there is none, so such an investor forfeits the withholding in both locations. The credit is not an argument for either.",
  source: structural,
  asOf: asOf("2026-08-12"),
} as const;

// ---------------------------------------------------------------------------
// The ranking
// ---------------------------------------------------------------------------

export interface PriorityRow {
  readonly asset: string;
  readonly taxableCost: string;
  readonly shelteredCostBp: number;
  /** Priority per dollar of shelter capacity, bp/yr, by qualified-dividend rate. */
  readonly at23_8Bp: number;
  readonly at18_8Bp: number;
  readonly at15Bp: number;
  readonly caveat?: string;
}

export const priorityTable: readonly PriorityRow[] = [
  {
    asset: "Taxable investment-grade bonds",
    taxableCost: "yield × 40.8%",
    shelteredCostBp: 0,
    at23_8Bp: 189.7,
    at18_8Bp: 189.7,
    at15Bp: 189.7,
    caveat:
      "189.7 uses the 40.8% top ordinary rate, which belongs with the 23.8% qualified rate and not with the other two columns. See `bondRowCaveat`.",
  },
  {
    asset: "Developed ex-US equity",
    taxableCost: "2.60% × q",
    shelteredCostBp: 15.78,
    at23_8Bp: 46.1,
    at18_8Bp: 33.1,
    at15Bp: 23.2,
  },
  {
    asset: "Emerging-market equity",
    taxableCost: "2.03% × q",
    shelteredCostBp: 20.0,
    at23_8Bp: 28.3,
    at18_8Bp: 18.2,
    at15Bp: 10.4,
  },
  {
    asset: "US equity",
    taxableCost: "1.10% × q",
    shelteredCostBp: 0,
    at23_8Bp: 26.2,
    at18_8Bp: 20.7,
    at15Bp: 16.5,
  },
];

export const bondRowCaveat = {
  headline: "The printed 189.7 is a top-bracket figure and must be restated at the investor's own ordinary rate.",
  detail:
    "A taxpayer whose qualified rate is 15% faces an ordinary rate nearer 12–24%, so the bond line falls to roughly 4.65% × 22% = 102 bp. It still dominates the next line by more than four to one, which is why the ranking does not move — but a table that prints the top-bracket number in all three columns is internally inconsistent, and this is the fix.",
  source: recommendation,
} as const;

export interface FillOrder {
  readonly qualifiedRatePercent: number;
  readonly order: readonly string[];
  readonly reading: string;
  readonly inverted: boolean;
}

export const fillOrders: readonly FillOrder[] = [
  {
    qualifiedRatePercent: 23.8,
    order: ["bonds", "developed ex-US", "emerging", "US"],
    reading:
      "The conventional order survives, but emerging's margin over US collapses from 22.1 bp to 2.1 bp. Treat it as a tie.",
    inverted: false,
  },
  {
    qualifiedRatePercent: 18.8,
    order: ["bonds", "developed ex-US", "US", "emerging"],
    reading: "Inverted. Emerging goes to the taxable account.",
    inverted: true,
  },
  {
    qualifiedRatePercent: 15,
    order: ["bonds", "developed ex-US", "US", "emerging"],
    reading: "Inverted, by 6.1 bp.",
    inverted: true,
  },
  {
    qualifiedRatePercent: 0,
    order: ["the credit is worth nothing either way"],
    reading:
      "§904 limits the credit to US tax on foreign-source income, and there is none. The 0% bracket forfeits the withholding in both locations.",
    inverted: false,
  },
];

// ---------------------------------------------------------------------------
// Account by account
// ---------------------------------------------------------------------------

export interface AccountPlacement {
  readonly id: string;
  readonly account: string;
  readonly holds: string;
  readonly why: string;
  readonly conditions?: readonly string[];
}

export const accountOrder: readonly AccountPlacement[] = [
  {
    id: "hsa",
    account: "HSA",
    holds: "Equity, the highest-growth sleeve",
    why: "The only US account untaxed at all three points, and payroll contributions escape FICA on top. That is not a rate forecast; it is a strictly dominant wrapper.",
    conditions: [
      "It requires a high-deductible health plan.",
      "Its value is a dollar limit rather than a rate, so it cannot be expressed as basis points on a portfolio of arbitrary size.",
      "California breaks all three legs: no deduction, interest and earnings taxable in the year earned, and internal sales are realisation events. For a Californian an HSA is federally dominant and worse than a taxable brokerage account on one axis.",
      "New Jersey is widely reported to do the same and no primary source addressing HSAs was found at all. Treat that as inference from omission.",
    ],
  },
  {
    id: "traditional",
    account: "Traditional 401(k) or IRA",
    holds:
      "Bonds first, then developed ex-US, then by the ranking above. A pro-rata managed-futures fund here or not at all",
    why: "Bonds dominate by a factor of four. DBMF's 2.09 pp/yr distribution tax drag is zero here, and 1.44 pp/yr of it is incremental over the equity it is sold to buy. A trend overlay held through the return-stacked wrapper RSST does not need this shelter: 4.5 bp per dollar in a taxable account, because the wrapper contains the equity fund it displaces.",
  },
  {
    id: "roth",
    account: "Roth",
    holds: "The highest-expected-growth sleeve that fits after bonds — US equity, or the small-value tilt",
    why: "Identical to a traditional account on foreign withholding: both forfeit it. The traditional-versus-Roth choice itself is a rate forecast, not a structure, and does not belong in a contractual budget.",
  },
  {
    id: "taxable",
    account: "Taxable",
    holds: "US total market; emerging-market equity at a 15% or 18.8% rate; whatever does not fit above",
    why: "ETFs, specific-identification lots as a standing instruction, no turnover.",
  },
];

/** 2026 figures. Rev. Proc. 2025-19 for the limits; the catch-up is hardcoded in statute. */
export const hsaLimits = {
  selfOnlyUsd: 4400,
  familyUsd: 8750,
  age55CatchUpUsd: 1000,
  catchUpNote: "Hardcoded in §223(b)(3) and never indexed.",
  taxYear: 2026,
  source: { ...structural, href: "https://www.irs.gov/pub/irs-drop/rp-25-19.pdf" },
  asOf: asOf("2026-08-12"),
} as const;

// ---------------------------------------------------------------------------
// Three conditions that decide more than the ranking
// ---------------------------------------------------------------------------

export const deferredBalanceIsNotYourMoney = {
  headline: "A tax-deferred balance is not the investor's money.",
  detail:
    "At a 24% withdrawal rate, $100,000 of traditional IRA is $76,000 of investor wealth and $24,000 of government wealth. An allocation stated on nominal balances misstates true equity exposure, and a location comparison run on nominal rather than after-tax dollars is systematically wrong. The ranking above is stated per dollar of shelter capacity precisely to sidestep that.",
  source: structural,
} as const;

export const form1116Threshold = {
  singleUsd: 300,
  jointUsd: 600,
  holdingsSingleUsd: 190153,
  holdingsJointUsd: 380305,
  detail:
    "Below $300 of creditable foreign tax ($600 joint) the credit is claimed on Schedule 3 with no Form 1116 and no §904 limitation. At the developed sleeve's withholding rate that threshold arrives at $190,153 of holdings, or $380,305 filing jointly.",
  caveats: [
    "Neither figure is indexed, so the fraction of investors pushed onto Form 1116 rises mechanically every year.",
    "Unused credit carries back one year and forward ten under §904(c), and is not refundable.",
    "No carryover is available in any year the $300/$600 election is used.",
    "§901(k)(1)(A) disallows the credit entirely on a dividend where the stock was held 15 days or less inside the 31-day window around the ex-dividend date.",
  ],
  source: { ...structural, href: "https://www.irs.gov/instructions/i1116" },
  asOf: asOf("2026-08-12"),
} as const;

export const washSaleTrap = {
  headline: "Wash-sale scanning has to be household-wide, and this is why.",
  detail:
    "An ordinary wash sale merely defers the loss, because §1091(d) adds it to the replacement shares' basis. Revenue Ruling 2008-5 removes that repair when the replacement is bought inside the taxpayer's IRA: the loss is disallowed and the IRA's basis is not increased, so the deduction is destroyed rather than deferred.",
  costBp: 119,
  costBasis: "A 5%-of-portfolio disallowance at the top rate.",
  whyItMatters:
    "It is the only tax-loss mechanic on record here whose damage is permanent rather than timing. A same-account check turns a deferred loss into a destroyed one, so the scan has to cover IRAs and a spouse's accounts too.",
  source: structural,
  asOf: asOf("2026-08-12"),
} as const;

/** Two omissions, both cutting against the emerging-market inversion, neither quantified. */
export const statedOmissions: readonly { readonly id: string; readonly text: string }[] = [
  {
    id: "capital-gain-distributions",
    text: "A shelter also shelters capital-gain distributions and rebalancing turnover, which emerging-market funds generate more of.",
  },
  {
    id: "harvesting-value",
    text: "A taxable international position is a better loss-harvesting candidate, because it is more volatile.",
  },
];

export const omissionsNote =
  "Neither is quantified anywhere here, and either could close a 6 bp gap. The emerging inversion should be presented with both attached.";

export const placementSource = { structural, recommendation } as const;
export const placementAsOf = asOf("2026-08-12");

// ---------------------------------------------------------------------------
// The same inputs, in the shape the arithmetic consumes
// ---------------------------------------------------------------------------

/**
 * `placementInputs`, `priorityTable` and `fillOrders` above are the display twins of
 * what follows: one dated row per figure, in percent, already ranked, for a reader who
 * only wants to look. These are the machine-readable versions of the same figures —
 * decimals, grouped the way `~/lib/placement` takes them — so a page can run the
 * ranking at the reader's own bracket instead of printing three columns of it.
 *
 * The split is deliberate. `~/lib/placement` carries no data at all, because a tax rate
 * "must be a dated jurisdiction-specific input, never a hardcoded financial truth", and
 * a number written into a route or a component is a defect under decision 0007. This is
 * the one place the two meet.
 *
 * They have to agree with the research workspace rather than merely with each other:
 * `src/state/investorPolicy.test.ts` feeds these constants through `shelterPriorityBp`
 * and checks the ranking against the `shelterPriority` fixture, regime by regime.
 */

/** The regime ids the investor-policy store persists. Renaming one is a storage change. */
export type TaxRegimeId = "us-top" | "us-upper-middle" | "us-zero-ltcg";

export interface NamedTaxRegime extends TaxRegime {
  readonly id: TaxRegimeId;
  readonly source: Citation;
}

/** 37% ordinary, 20% long-term, plus the §1411 surtax. The reference investor's bracket. */
const usTopBracket: NamedTaxRegime = {
  id: "us-top",
  label: "US top marginal bracket",
  asOf: asOf("2026-08-12"),
  ordinaryIncome: 0.37,
  longTermCapitalGain: 0.2,
  netInvestmentIncome: 0.038,
  source: structural,
};

/** 24% ordinary, 15% long-term, below the §1411 threshold. */
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

/** MSCI EAFE's yield, withheld at the grossed-up §853 rate. */
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

/** A stated input rather than a retrieved measurement, and the yield every break-even is stated against. */
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
