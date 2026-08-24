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
  note: "Developed and emerging cannot be treated as one international line.",
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
      "189.7 uses the 40.8% top ordinary rate, which belongs with the 23.8% qualified rate and not with the other two columns. See bondRowCaveat.",
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
    holds: "Equity, the highest-growth holding",
    why: "The only US account untaxed at all three points, and payroll contributions escape FICA on top. That needs no rate forecast. The structure wins at every rate.",
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
    why: "Bonds dominate by a factor of four. DBMF's 2.09 pp/yr distribution tax drag is zero here, and 1.44 pp/yr of it is incremental over the equity it is sold to buy. Trend exposure added on top through the return-stacked fund RSST does not need this shelter: 4.5 bp per dollar in a taxable account, because RSST contains the equity fund it displaces.",
  },
  {
    id: "roth",
    account: "Roth",
    holds: "The highest-expected-growth holding that fits after bonds: US equity, or the lean into small value",
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
  headline: "Part of a tax-deferred balance belongs to the government rather than to the investor.",
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
    "Below $300 of creditable foreign tax ($600 joint) the credit is claimed on Schedule 3 with no Form 1116 and no §904 limitation. At the developed-markets withholding rate that threshold arrives at $190,153 of holdings, or $380,305 filing jointly.",
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
    "An ordinary wash sale merely defers the loss, because §1091(d) adds it to the replacement shares' basis. Revenue Ruling 2008-5 removes that repair when the replacement is bought inside the taxpayer's IRA: the loss is disallowed and the IRA's basis does not rise to absorb it, so the deduction is destroyed rather than deferred.",
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

// ---------------------------------------------------------------------------
// The investor-specific plan
// ---------------------------------------------------------------------------

/**
 * Everything above this line is stated for an **asset class**. Everything below is stated
 * for a **named fund held by one stated investor**, and the two disagree — because an
 * asset-class table has to assume a qualified fraction and the funds file theirs.
 *
 * Regenerate from `research/src/portfolio_edge/studies/investor_placement.py`; every
 * figure is pinned in `research/tests/unit/test_studies_investor_placement.py`.
 */

const investorPlacement: Citation = {
  label: "Structural and tax-aware edges § the investor's plan",
  docPath: "docs/research/structural-and-tax-edges.md",
};

/** The one input that decides the sign, and the one the asset-class table above assumes away. */
export const qualifiedFractionCorrection = {
  headline:
    "The asset-class ranking above assumes international dividends are fully qualified. Their sponsors file otherwise.",
  detail:
    "A qualified dividend is taxed at the long-term rate; the rest is ordinary income, 17 pp dearer at the top bracket. The asset-class table above takes the qualified fraction as 1.00 for both international classes. Vanguard's own 2025 foreign tax credit worksheet — the same document the withholding input comes from — reports qualified foreign dividend income of 66.2741% of Box 1a for VEA and 34.6250% for VWO. iShares designates 34.82% for IEMG, Avantis 44.48% for AVES and Invesco 25% for IDMO.",
  consequence:
    "Restoring the filed fraction reverses the emerging-market inversion. Both emerging funds this investor holds outrank US equity for shelter capacity at every live US qualified rate, not just at 23.8%. The inversion was an artifact of the assumption, not a property of the funds.",
  asOf: asOf("2026-08-22"),
  source: investorPlacement,
} as const;

/** The open input the page called its largest. It is closed, and it closes in favour of the number already in use. */
export const withholdingDenominatorResolved = {
  headline: "The two withholding rates were never in disagreement. They have different denominators.",
  detail:
    "A sponsor's shareholder worksheet states foreign tax as a share of the dividend; a fund's N-CSR tax note states it as a share of foreign source income; and foreign source income is 77% to 100% of the dividend, never all of it. VEA reconciles exactly: 6.068% of Box 1a divided by 79.6488% foreign source income is 7.618%, and 7.61% is the ratio VEA's own N-CSR files.",
  crossChecks: [
    "Vanguard's worksheet defines Box 1a as ordinary cash dividends plus short-term capital gains plus foreign taxes paid, so the base is gross of the withheld tax by construction.",
    "iShares' 2025 distribution summary gives IEMG cash of $1.848602 plus foreign tax of $0.196929 equal to Box 1a of $2.045531 per share, to the cent.",
    "Avantis' 2025 ICI file gives AVES cash of $1.8479 plus foreign tax of $0.246250712 equal to Box 1a of $2.094150712, to the cent.",
  ],
  consequence:
    "Multiplying a fund's whole dividend yield by a filed foreign-source ratio overstates the withholding by up to a quarter. The existing 6.068% and 9.853% inputs are on the right base and do not move.",
  asOf: asOf("2026-08-22"),
  source: investorPlacement,
} as const;

export interface InvestorHolding {
  readonly ticker: string;
  readonly name: string;
  /** Fraction of the whole portfolio. */
  readonly weight: number;
  readonly expenseRatioBp: number;
  /** The whole annual taxable distribution as a fraction of net assets: Box 1a grossed up for creditable foreign tax, plus Box 2a. */
  readonly boxOneAYield: number;
  /** Share of that taxed at the long-term rate: qualified dividends plus any long-term capital-gain distribution. */
  readonly capitalGainRateFraction: number;
  /** Creditable foreign tax passed through under §853, as a fraction of net assets. */
  readonly creditableForeignTaxYield: number;
  /** Priority per dollar of shelter capacity, bp/yr, at 23.8% / 18.8% / 15% qualified. */
  readonly priorityBp: readonly [number, number, number];
  readonly account: "shelter" | "taxable" | "split";
  readonly provenance: string;
  readonly asOf: AsOf;
}

/** The three qualified-dividend rates the plan is reported across. 20% without the surtax is unreachable. */
export const investorRates: readonly number[] = [23.8, 18.8, 15];

export const investorHoldings: readonly InvestorHolding[] = [
  {
    ticker: "RSST",
    name: "Stacked US equity and managed futures, recognised basis",
    weight: 0.3,
    expenseRatioBp: 99,
    boxOneAYield: 0.09273,
    capitalGainRateFraction: 0.10504,
    creditableForeignTaxYield: 0,
    priorityBp: [361.78, 315.42, 213.79],
    account: "shelter",
    provenance:
      "Tidal Trust II N-CSR for the year ended 2026-01-31. Undistributed ordinary income on a tax basis went from 1.40% to 8.56% of net assets in one year while the fund distributed 0.33% of net assets of ordinary income, so about 8.43% of net assets was recognised and not paid out. The trust's own note: as wholly-owned controlled foreign corporations, the subsidiaries' net income and capital gains are included each year in the fund's investment company taxable income. Nobody can yet say whether or when the queue is distributed; the same note reserves the right to retain income and pay excise tax.",
    asOf: asOf("2026-01-31"),
  },
  {
    ticker: "RSST",
    name: "Stacked US equity and managed futures, distributed basis",
    weight: 0.3,
    expenseRatioBp: 99,
    boxOneAYield: 0.01285,
    capitalGainRateFraction: 0.8565,
    creditableForeignTaxYield: 0,
    priorityBp: [33.72, 27.29, 20.93],
    account: "split",
    provenance:
      "The same filing, counting only what shareholders were actually taxed on: $915,484 of ordinary income and $2,648,642 of long-term capital gain, $0.32 a share on a $24.91 opening net asset value. The fund's own prospectus reports 17.17% a year before tax against 16.85% after taxes on distributions since inception, a 32 bp/yr gap, which is this reading measured independently.",
    asOf: asOf("2026-01-31"),
  },
  {
    ticker: "IDMO",
    name: "Invesco S&P International Developed Momentum ETF",
    weight: 0.05,
    expenseRatioBp: 25,
    boxOneAYield: 0.044031,
    capitalGainRateFraction: 0.2557,
    creditableForeignTaxYield: 0.001229,
    priorityBp: [148.22, 126.2, 83.25],
    account: "shelter",
    provenance:
      "Invesco Exchange-Traded Fund Trust II N-CSR for the year ended 2025-10-31. Qualified dividend income 25% of ordinary income dividends; portfolio turnover 105%; foreign tax $0.0317 against foreign source income $0.5841 a share. Undistributed ordinary income of $32,959,121 and undistributed long-term gain of $11,582,181 on $2,081,578,000 of net assets were paid out on 2025-12-22 as $0.68417 of short-term and $0.27579 of long-term gain a share. One fiscal year, and the capital-gain line is the least durable figure in this table.",
    asOf: asOf("2025-10-31"),
  },
  {
    ticker: "AVES",
    name: "Avantis Emerging Markets Value ETF",
    weight: 0.05,
    expenseRatioBp: 36,
    boxOneAYield: 0.0391,
    capitalGainRateFraction: 0.4448,
    creditableForeignTaxYield: 0.004598,
    priorityBp: [83.98, 64.43, 32.21],
    account: "shelter",
    provenance:
      "Avantis 2025 tax centre: qualified dividend income 44.48%, foreign source income 92.34% of Box 1a, foreign tax 11.759% of Box 1a from the 2025 ICI file. Yield is the fiscal-2025 net investment income ratio of 3.45% from American Century ETF Trust's N-CSR, grossed to the Box 1a base. Fee 0.36% gross equals net, no waiver. No capital-gain distribution since inception.",
    asOf: asOf("2025-08-31"),
  },
  {
    ticker: "IEMG",
    name: "iShares Core MSCI Emerging Markets ETF",
    weight: 0.05,
    expenseRatioBp: 9,
    boxOneAYield: 0.02545,
    capitalGainRateFraction: 0.3482,
    creditableForeignTaxYield: 0.00245,
    priorityBp: [64.27, 51.55, 28.6],
    account: "shelter",
    provenance:
      "iShares 2025 QDI summary: qualified dividend income 34.82%. iShares 2025 distribution summary: Box 1a $2.045531 a share, foreign tax $0.196929, Box 2a zero. Yield is the 12-month trailing yield of 2.30% published 2026-07-31, grossed to the Box 1a base. Fee 0.09%, contractually capped through 2030-12-31 with no recoupment.",
    asOf: asOf("2026-07-31"),
  },
  {
    ticker: "DFIV",
    name: "Dimensional International Value ETF",
    weight: 0.1,
    expenseRatioBp: 27,
    boxOneAYield: 0.04033,
    capitalGainRateFraction: 1,
    creditableForeignTaxYield: 0.003226,
    priorityBp: [63.73, 43.56, 28.23],
    account: "shelter",
    provenance:
      "Dimensional ETF Trust N-CSR for the year ended 2025-10-31. Its tax note designates, as percentages of investment company taxable income, qualifying dividend income 100%, foreign source income 100% and foreign tax credit 8% under §853. Net investment income 3.71% of average net assets, turnover 6%, no capital-gain distribution in five years. Both filed percentages are rounded to a whole point, which is the coarsest input here.",
    asOf: asOf("2025-10-31"),
  },
  {
    ticker: "VEA",
    name: "Vanguard FTSE Developed Markets ETF",
    weight: 0.1,
    expenseRatioBp: 3,
    boxOneAYield: 0.02387,
    capitalGainRateFraction: 0.662741,
    creditableForeignTaxYield: 0.001448432,
    priorityBp: [56.01, 44.07, 28.56],
    account: "shelter",
    provenance:
      "Vanguard's 2025 foreign tax credit worksheet: foreign source income 79.6488% of Box 1a, qualified foreign dividend income 66.2741%, foreign tax 6.46% of ordinary cash dividends or 6.068% of Box 1a. Yield is Vanguard's forecast dividend yield of 2.387% effective 2026-07-31, which is a forecast rather than a realised distribution; Vanguard publishes no SEC yield for VEA.",
    asOf: asOf("2026-07-31"),
  },
  {
    ticker: "AVLV",
    name: "Avantis U.S. Large Cap Value ETF",
    weight: 0.15,
    expenseRatioBp: 15,
    boxOneAYield: 0.0177,
    capitalGainRateFraction: 1,
    creditableForeignTaxYield: 0,
    priorityBp: [42.13, 33.28, 26.55],
    account: "split",
    provenance:
      "American Century ETF Trust N-CSR for the year ended 2025-08-31: net investment income 1.77% of average net assets, fee 0.15% gross equals net, turnover 7%, no capital-gain distribution in four years, actively managed. The qualified fraction of 1.00 is an assumption; Avantis publishes a per-fund figure and AVLV's was not retrieved.",
    asOf: asOf("2025-08-31"),
  },
  {
    ticker: "VTI",
    name: "Vanguard Morningstar Total Stock Market ETF",
    weight: 0.2,
    expenseRatioBp: 3,
    boxOneAYield: 0.01067,
    capitalGainRateFraction: 1,
    creditableForeignTaxYield: 0,
    priorityBp: [25.39, 20.06, 16],
    account: "taxable",
    provenance:
      "Vanguard's published fund-yield endpoint: SEC 30-day yield 1.03% and forecast dividend yield 1.0670%, both effective 2026-07-31, fee 0.03%. Renamed from Vanguard Total Stock Market ETF with the benchmark rebranded CRSP to Morningstar US Total Market effective 2026-07-29; objective and management unchanged. The qualified fraction of 1.00 is an assumption.",
    asOf: asOf("2026-07-31"),
  },
];

/**
 * What the plan is worth, in bp/yr of the whole portfolio, under four rules that bound it.
 *
 * 1. **The control has to be feasible.** Pro-rata placement is impossible when part of the
 *    shelter is a captive employer plan whose menu excludes five of the eight funds, so
 *    the control is what a default-choosing investor with the same accounts would do.
 * 2. **Income recognised inside a fund and not distributed is not yet a saving to
 *    anybody**, so the wrapper's accrual is reported beside the booked figure and never
 *    added to it.
 * 3. **A hurdle avoided is not a saving**, so rebalancing inside the shelter is worth zero
 *    as a line.
 * 4. **Lot selection and never selling are mutually exclusive**, so the lot-selection line
 *    is zero here too.
 *
 * Everything below is against ONE benchmark: the same eight funds, placed the way a
 * default-choosing investor with the same accounts would place them. Lines against a cheap
 * index or against typical behaviour live elsewhere and do not add to these.
 */

/** The share of the tax-deferred third that sits in a rollover IRA rather than an employer plan. */
export interface OpenMenuFraction {
  readonly f: number;
  readonly label: string;
}

export const openMenuFractions: readonly OpenMenuFraction[] = [
  { f: 0, label: "all employer plan" },
  { f: 0.5, label: "half rollover" },
  { f: 1, label: "all rollover IRA" },
];

/** The employer plan can hold these and nothing else this portfolio owns. */
export const employerPlanMenu: readonly string[] = ["VTI", "VEA", "IEMG"];

export const menuConstraint = {
  headline: "The binding constraint is the employer plan's fund menu, not the tax code.",
  bindingFraction: 0.55,
  bindingDerivation:
    "The unconstrained plan already shelters VEA and IEMG — 15% of the portfolio — so while the employer plan is no larger than that it can be filled with exactly those two and costs nothing. 1 − 0.15/0.333 = 0.55. Below that every extra point of employer plan forces one more point of a low-priority index fund into the shelter and evicts a high-priority one.",
  whatItCosts:
    "At f = 0 the two highest-yielding funds in the portfolio — DFIV at 4.03% and AVES at 3.91% — are evicted to the taxable account while VTI, last in the queue at every rate, is forced into the shelter at 18.3% of the portfolio. That is the exact inverse of the ranking, imposed by a fund lineup rather than by any tax fact. Against the same plan at f = 1 it costs 9.09 bp/yr at 23.8%, 6.56 at 18.8% and 3.33 at 15% — identically on both readings of RSST, because RSST is sheltered either way and what the menu reorders is the equity queue behind it.",
  wrapperAlwaysFits:
    "RSST never has to leave the shelter at any f, because the Roth alone is 33.3% against its 30%. The margin is 3.3 points, so that is a coincidence of the stated weights rather than a structural fact.",
  cheapestLever:
    "Consolidating an old employer balance into the rollover IRA buys the whole f = 0 to f = 0.5 improvement for the cost of a form. It is the cheapest lever on this page.",
  source: investorPlacement,
  asOf: asOf("2026-08-22"),
} as const;

export interface PlanValueRow {
  readonly qualifiedRatePercent: number;
  /** Booked edge over the feasible control, audited basis, by open-menu fraction. */
  readonly bookedBp: readonly [number, number, number];
  /** Conditional on the wrapper's recognised income being distributed. Never added. */
  readonly conditionalBp: readonly [number, number, number];
}

export const planValue: readonly PlanValueRow[] = [
  { qualifiedRatePercent: 23.8, bookedBp: [-2.04, 6.66, 5.41], conditionalBp: [49.21, 39.37, 32.81] },
  { qualifiedRatePercent: 18.8, bookedBp: [-1.04, 5.22, 4.24], conditionalBp: [43.22, 34.57, 28.81] },
  { qualifiedRatePercent: 15, bookedBp: [-0.4, 2.56, 2.04], conditionalBp: [28.93, 23.14, 19.29] },
];

export const planValueNote =
  "Booked figures are against a control the investor could actually have executed, on the audited distributed basis. The conditional column is reported and never added: it rests on income recognised inside RSST and not yet distributed to anybody. At f = 0 the booked line is negative: with a wholly captive tax-deferred third, forcing RSST into the Roth costs more on the audited basis than the fund ordering saves. The sign flips at f between 0.02 and 0.05.";

/** Why an unresolved input does not stall the decision. */
export const wrapperRegret = {
  headline: "RSST's unresolved accrual does not need to be settled to make the decision.",
  shelterItCostIfWrongBp: [8.54, 1.12] as const,
  followTheAuditedRankingCostIfWrongBp: [89.88, 42.62] as const,
  reading:
    "At 23.8%, sheltering RSST costs 1.12 bp/yr at f = 1 and 8.54 at f = 0 if the audited basis is right. Following the audited-basis ranking instead costs 42.62 and 89.88 respectively if the accrual is distributed. The asymmetry is ten to one at every f and every bracket, so sheltering it is right under either reading and the measurement can stay open.",
  source: investorPlacement,
  asOf: asOf("2026-08-22"),
} as const;

/** Permanently destroyed by sheltering the international sleeve. Already inside the priority, never added again. */
export const creditForfeitedByPlanBp = 8.81;

export const linesNotBooked: readonly { readonly line: string; readonly why: string }[] = [
  {
    line: "Rebalancing kept inside the shelter, +14 bp/yr",
    why: "A hurdle avoided is not a saving. The deferral line is explicitly a hurdle, and crediting yourself for not doing something nobody proposed is how these budgets get inflated. Withdrawn to zero and reported as a hurdle not paid.",
  },
  {
    line: "Lot selection, up to +2.8 bp/yr",
    why: "Mutually exclusive with the line above. Lot-selection discipline is worth something only when you sell, and the rebalancing claim was that you never sell in the taxable account. With contributions at 5–15%/yr covering the one constrained rebalancing direction between 2.5 and 7.5 times over, there is nothing to select lots across.",
  },
  {
    line: "Fee gap and fund structure",
    why: "Measured against a cheap index rather than against this investor's own counterfactual. Real, but they belong to a different benchmark and may not be added to the location line.",
  },
];

export const contributionCoverage = {
  constrainedRotationPp: 2,
  detail:
    "One rebalancing direction cannot be executed inside the shelter — selling US equity to buy international — because at f = 1 only 1.7% of AVLV sits in the shelter beside RSST. It needs roughly two points of the portfolio a year. Contributions of 5–15%/yr cover it 2.5 to 7.5 times over, so the taxable account never has to sell.",
  coverageAtFivePercent: 2.5,
  coverageAtFifteenPercent: 7.5,
  source: investorPlacement,
  asOf: asOf("2026-08-22"),
} as const;

export const rothVersusTraditional = {
  headline: "The drag cannot decide between a Roth and a traditional account, because it is the same number in both.",
  algebra:
    "Terminal after-tax wealth from putting growth factor A in a Roth of nominal size R and factor B in a traditional of size T at withdrawal rate t is R·A + T(1−t)·B. Swapping them changes it by exactly (R − T(1−t))(A − B). The gain is the after-tax size gap between the accounts times the growth gap between the two holdings, and it is zero when R = T(1−t).",
  valueBp: 1.96,
  valueBasis:
    "Equal nominal thirds, a 24% withdrawal rate, 30 years, a 30% holding swapped, and a 1 pp/yr expected-return gap: 1.96 bp/yr. Comparable to the whole taxable-versus-sheltered decision once that is measured against a feasible control, and unlike it, entirely a forecast.",
  theHonestReading:
    "Holding the same after-tax allocation, this gain is not free. The traditional account makes the government a t-share partner in the outcome, so moving a holding to the Roth raises the investor's share of its dispersion by the same factor it raises the mean. Putting the least-established holding in the traditional is a risk decision rather than an edge.",
  whatIsNotAForecast:
    "Required minimum distributions. The IRS states that withdrawals from Roth IRAs and designated Roth accounts are not required until after the death of the account owner, while a traditional balance must begin distributing at 73. The traditional account is therefore the right home for the holding the investor expects to be trimming anyway, and the Roth for the one they never intend to sell.",
  source: {
    ...investorPlacement,
    href: "https://www.irs.gov/retirement-plans/retirement-plan-and-ira-required-minimum-distributions-faqs",
  },
  asOf: asOf("2026-08-22"),
} as const;

export const contributionDirection = {
  headline:
    "Fill the dollar-limited accounts first, then direct taxable contributions at whatever is furthest below target.",
  limits2026:
    "§402(g) elective deferral $24,500, age-50 catch-up $8,000, ages 60 to 63 $11,250, IRA $7,500 with a $1,100 catch-up, all from IRS Notice 2025-67.",
  theConstraintThatBites:
    "The Roth IRA contribution phases out between $242,000 and $252,000 of modified AGI filing jointly, and the §1411 surtax starts at an unindexed $250,000. An investor paying the surtax — which is every investor in the 18.8% and 23.8% columns — is at or past the Roth IRA phase-out, so their Roth capacity comes from a designated Roth account in an employer plan or from a conversion, not from a direct contribution.",
  rebalancing:
    "The entire international holding and the entire trend position sit inside the shelter, so every trade on those two legs realises nothing. The constrained direction is selling US equity to buy international: only about 1.7% of the portfolio in AVLV sits in the shelter beside RSST, so a rotation larger than about two points either disturbs RSST or realises a gain in the taxable account. Point new contributions at it instead.",
  rebalancingValue:
    "Realising 10% of standing gain a year costs 41.5 bp/yr of the 84.1 bp deferral at a 30-year horizon. Applied to the taxable third of this portfolio, never having to sell there is worth about 14 bp/yr, larger than the entire location decision on RSST's conservative reading.",
  source: { ...investorPlacement, href: "https://www.irs.gov/pub/irs-drop/n-25-67.pdf" },
  asOf: asOf("2026-08-22"),
} as const;

export const investorPlanCaveats: readonly string[] = [
  "The rollover share f of the tax-deferred third has not been measured, and it is the input the plan is most sensitive to: it moves the booked line from −2.0 to +6.7 bp/yr and decides whether DFIV and AVES can be sheltered at all. Ask for it before executing. So has the employer plan's actual lineup — VTI, VEA and IEMG is a typical menu, not a filed one.",
  "Contributions are 5–15%/yr of the portfolio. No conclusion here turns on where in that range the investor sits, because new money covers the one constrained rebalancing direction more than twice over at every point in it.",
  "Three qualified fractions are assumed rather than filed: VTI, AVLV and RSST's undistributed queue. Each assumption pushes its fund toward the taxable account, so the plan is conservative in the direction it is uncertain.",
  "IDMO's capital-gain line rests on one December distribution and one fiscal year's undistributed balance. It is the least durable figure in the table and it is what puts IDMO second in the queue.",
  "Yields mix windows: two are sponsor forecasts effective 2026-07-31, three are audited fiscal-year ratios ending in 2025. A yield is the input a placement ranking is most sensitive to and none of these is point-in-time.",
  "State income tax is excluded and additive. A state that taxes ordinary income and capital gain alike compresses every gap in the table and makes the ranking flatter, not different.",
  "Nothing here is personalised advice. Every figure is a function of stated inputs a different investor should restate.",
];
