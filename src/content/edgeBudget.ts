import { asOf, type CertaintyClass, type Citation } from "~/content/types";

/**
 * The contractual budget: about 109 basis points a year against the portfolio the
 * investor would otherwise have owned.
 *
 * It is not an edge over an index. Against a cheap index the honest number is about
 * 46 bp against 313 bp of tracking error — see `src/content/confidence.ts`. The two
 * benchmarks never aggregate.
 */

const structural: Citation = {
  label: "Structural and tax-aware edges",
  docPath: "docs/research/structural-and-tax-edges.md",
};

const recommendation: Citation = {
  label: "The recommended portfolio",
  docPath: "docs/research/portfolio-recommendation.md",
};

const decomposition: Citation = {
  label: "Where outperformance can come from",
  docPath: "docs/research/expected-edge-decomposition.md",
};

/** What a line does to the total, which is not the same as how large it is. */
export type BudgetRole =
  /** One of the three lines in the original 89 bp budget. */
  | "base"
  /** Genuinely new, and added to the total. */
  | "additive"
  /** A revision to a line already counted, with the sign reversed. */
  | "correction"
  /** The cost of a policy nobody proposed. Deliberately not booked as a saving. */
  | "hurdle"
  /** Bought for exposure control, not for return. */
  | "risk-control"
  /** Measured and reported, but booked against a different benchmark. */
  | "reported-not-booked";

export interface EdgeBudgetLine {
  readonly id: string;
  readonly label: string;
  /** Basis points a year at portfolio level, for the stated reference investor. Negative for corrections. */
  readonly basisPoints: number;
  readonly range?: readonly [number, number];
  readonly role: BudgetRole;
  readonly certaintyClass: CertaintyClass;
  readonly decaying: boolean;
  /** The condition without which this line is zero. */
  readonly appliesWhen: string;
  /** Two or three sentences a non-quant can act on. */
  readonly explanation: string;
  readonly caveat?: string;
  readonly source: Citation;
  readonly asOf?: ReturnType<typeof asOf>;
}

export const edgeBudgetLines: readonly EdgeBudgetLine[] = [
  {
    id: "fund-cost",
    label: "Hold index funds rather than the average active dollar",
    basisPoints: 49,
    range: [40, 59],
    role: "base",
    certaintyClass: "contractual",
    decaying: false,
    appliesWhen: "Any account. Measured against the fund you would otherwise have held, never against the index",
    explanation:
      "Asset-weighted fees run about 0.09% for broad index funds against 0.57% for active ones, and ICI puts the gap wider still. Sharpe's arithmetic makes this half an identity rather than a forecast: before costs the average active dollar earns the average passive dollar, so after costs it earns less by the fee. The saving is real and it is spent once — an index fund cannot beat its own index by cutting its fee again.",
    caveat:
      "Switching out of one randomly chosen active fund carries that fund's own idiosyncratic risk. At 350 bp of tracking error a 50 bp fee edge is only 78% likely to be ahead after thirty years. Against the average active dollar the tracking error collapses and the saving is near-certain, so the certainty comes from the pairing rather than from the fee.",
    source: decomposition,
  },
  {
    id: "tax-loss-harvesting",
    label: "Tax-loss harvesting, gross of its own fee",
    basisPoints: 30,
    range: [0, 90],
    role: "base",
    certaintyClass: "contractual",
    decaying: true,
    appliesWhen:
      "Taxable account, direct ownership of securities rather than a fund, offsetting gains available, and contributions still arriving",
    explanation:
      "Harvesting losses against gains is worth roughly 30 bp a year to an investor who keeps adding money. It decays hard without new money, because the process sells the loss lots and keeps the gain lots until the portfolio's basis is too low to harvest against. For a static investor with only long-term gains the honest thirty-year figure is 5.6 bp, and negative at any fee.",
    caveat:
      "A fund cannot pass through security-level losses, so capturing this at all requires direct ownership — which is what the direct-indexing fee line below then charges for. The $3,000 annual cap on net capital loss against ordinary income has not been indexed since 1978, so its value falls with portfolio size: at most $1,224 a year at the top rate, which is 122 bp of $100,000 and 1.2 bp of $10m.",
    source: decomposition,
  },
  {
    id: "asset-location",
    label: "Asset location, computed rather than asserted",
    basisPoints: 10,
    range: [0, 21],
    role: "base",
    certaintyClass: "contractual",
    decaying: false,
    appliesWhen: "More than one account type and more than one asset class",
    explanation:
      'Putting the right asset in the right account is worth about 10 bp a year. No peer-reviewed source states a per-year figure at all, which is itself the finding; the practitioner range is 5 to 30 bp with typical cells at 5 to 13. The ranking has to be computed from the investor\'s own bracket, because "shelter the higher-yielding asset" is right for bonds by a factor of four and wrong for emerging-market equity at two of the four US dividend rates.',
    caveat:
      "None of the sources behind this line models foreign dividend withholding, which is what the correction below fixes.",
    source: decomposition,
  },
  {
    id: "fund-structure",
    label: "Hold ETFs rather than active mutual funds in a taxable account",
    basisPoints: 23,
    range: [0, 50],
    role: "additive",
    certaintyClass: "contractual",
    decaying: true,
    appliesWhen: "Taxable account only, and only against an active mutual fund you would otherwise have held",
    explanation:
      "An ETF hands appreciated shares to an authorised participant and recognises no gain; an equivalent mutual fund sells, recognises, and has to distribute. Vanguard's index funds show zero capital-gain distributions across 44 fund-years, while two of the largest active funds averaged 6.6% and 7.0% of net asset value — one of them distributing 7.25% in a year it lost 28%. Booked at 23 bp: 38.3 bp of drag on the taxable equity sleeve at a 3%-of-NAV counterfactual, times the 60% of the portfolio that sleeve occupies.",
    caveat:
      "This is the biggest new line and it is decaying while being measured. The SEC has granted 94 orders letting mutual funds add ETF share classes, covering roughly ninety fund families, with only two applications still noticed and unordered. Re-check the order count before leaning on this line. The advantage is also against active and non-Vanguard index funds, never against a low-turnover index mutual fund: Poterba and Shoven found before- and after-tax returns very similar for an SPDR trust and its mutual-fund equivalent.",
    source: structural,
    asOf: asOf("2026-08-11"),
  },
  {
    id: "specific-identification",
    label: "Specific identification of lots, as a standing instruction",
    basisPoints: 5,
    range: [0, 44],
    role: "additive",
    certaintyClass: "contractual",
    decaying: false,
    appliesWhen: "Taxable account, and only when you actually sell",
    explanation:
      "The default is first-in-first-out, which realises the most gain available. A standing instruction to sell the highest-basis lots is accepted by regulation, is not a method of accounting, and costs nothing to switch to. On a worked model — twenty annual $10,000 purchases compounding at 7%, selling a quarter of the position — it realises $31,944 of gain instead of $83,159.",
    caveat:
      "Booked at 5 bp, heavily shrunk from the 73 bp the only measurement found. That study is a 1984–98 simulation on a turning-over separate account, and a buy-and-hold investor who never sells realises nothing at all. It is the weakest additive line in the budget and the page says so.",
    source: structural,
  },
  {
    id: "foreign-tax-credit-forfeited",
    label: "Foreign tax credit forfeited inside a shelter",
    basisPoints: -3.4,
    range: [-6, 0],
    role: "correction",
    certaintyClass: "contractual",
    decaying: false,
    appliesWhen: "An international sleeve held inside a traditional account or a Roth",
    explanation:
      "A foreign government withholds tax on foreign dividends before the fund gets them. In a taxable account you can credit that against your US tax. Inside an IRA or a Roth there is no US tax to credit it against, so it is paid and permanently lost — 15.78 bp a year on a developed sleeve and 20.00 bp on emerging.",
    caveat:
      "This is a correction to the 10 bp asset-location line, not a new negative line. Booking it separately would count the same dollars twice with the sign reversed. No IRS publication states the IRA result in terms; it is asserted from the statute.",
    source: structural,
    asOf: asOf("2026-08-12"),
  },
  {
    id: "direct-indexing-fee",
    label: "The direct-indexing fee the harvesting line never subtracted",
    basisPoints: -4.4,
    range: [-30, 6],
    role: "correction",
    certaintyClass: "contractual",
    decaying: false,
    appliesWhen: "Wherever the harvesting line above is claimed, since it already assumes direct security ownership",
    explanation:
      "The 30 bp harvesting figure requires owning the securities directly, and buying that costs a fee the budget never charged. Netting 9 bp against the thirty-year average leaves 25.6 bp for a contributing investor. Retail direct indexing has split into a 9–12 bp automated tier and a 40 bp incumbent-brokerage tier.",
    caveat:
      "At the 40 bp tier no scenario measured is positive over thirty years, including the one that needs systematic short-term gains. Vendor headlines quote year one, which is the largest number any of these decay profiles ever takes.",
    source: structural,
    asOf: asOf("2026-08-12"),
  },
  {
    id: "deferral-hurdle",
    label: "Do not turn over the taxable account",
    basisPoints: 84.1,
    range: [0, 162],
    role: "hurdle",
    certaintyClass: "contractual",
    decaying: false,
    appliesWhen: "Taxable account, at a thirty-year horizon, at a positive long-term rate",
    explanation:
      "An unrealised gain is an interest-free loan from the government whose principal compounds with the position. Realising it turns the loan into a payment. At thirty years that deferral is worth 84.1 bp a year, which is more than every line in the budget except fund cost.",
    caveat:
      'This is a hurdle, not a saving, and it is deliberately not booked. Crediting yourself for not doing something nobody proposed is how these budgets get inflated. What it is for is pricing any future sleeve that trades: it has to out-earn 84 bp before its fee and its spread. And "low turnover" is not a defence, because the function is sharply concave — see `deferralHurdle` below.',
    source: structural,
  },
  {
    id: "rebalancing",
    label: "Rebalance to hold the declared weights",
    basisPoints: 0,
    range: [-1.2, -0.3],
    role: "risk-control",
    certaintyClass: "contractual",
    decaying: false,
    appliesWhen: "Any multi-sleeve portfolio whose owner wants the declared allocation to stay the actual allocation",
    explanation:
      "Holding the weights costs 0.3 to 1.2 bp a year and buys exposure control, not return. Left alone, a 60/30/10 portfolio drifted a mean 14.83 percentage points from target and reached 26.36 at its worst; monthly rebalancing held that to 0.60 and 2.62. That is keeping a promise, and it is the only claim the evidence supports.",
    caveat:
      "Measured as a source of return over 35 years it was −38.7 bp/yr on the portfolio and −62.9 bp/yr on the US against developed ex-US pair, and every rebalanced policy had an equal or worse maximum drawdown than leaving it alone. No rebalancing-bonus feature may be built.",
    source: {
      label: "Rebalancing policy on real regional equity",
      docPath: "docs/research/rebalancing-policy.md",
    },
  },
  {
    id: "securities-lending",
    label: "Securities-lending pass-through, measured across 25 funds",
    basisPoints: 0.83,
    range: [0.45, 2.6],
    role: "reported-not-booked",
    certaintyClass: "different-benchmark",
    decaying: false,
    appliesWhen: "Any fund that lends. Larger for international and emerging funds than for US large-cap ones",
    explanation:
      "Funds lend their holdings and pass most of the fee back. Median over every fiscal year Form N-CEN has filed: VTI 1.84 bp a year, VOO 0.06, VEA 3.30, VWO 4.33, IEMG 9.87. The recommended holdings earn 1.83 bp rather than the 1.0 originally booked, so the correction is +0.83, and fund choice alone moves it between 0.45 and 2.60.",
    caveat:
      "The fee is contractual and this is not: borrow demand is measured, not promised, and a high lending yield is partly compensation for holding what short sellers want. It is booked against a stated index rather than the investor's own counterfactual, so it does not enter the 109 bp total. It is not a size effect: VB, US small-cap, earns 3.0 bp — the same as VEA, large-cap developed. And two funds lend nothing — BND by choice, SPY because its trust deed forbids it.",
    source: structural,
  },
];

/** The revised own-counterfactual budget, and the pairing that makes it certain. */
export const edgeBudgetTotal = {
  basisPoints: 109,
  /** An outer bound, not a distribution: it assumes every condition fails together, then succeeds together. */
  outerBound: [4, 270] as const,
  priorBudget: { basisPoints: 89, range: [40, 170] as const },
  additiveTotal: 28.0,
  corrections: -7.8,
  combinedTrackingErrorBp: 46,
  priorTrackingErrorBp: 41,
  ninetyPercentConfidence: "about 3.5 months",
  ninetyNinePercentConfidence: "about twelve months",
  priorNinetyPercentConfidence: "4.2 months",
  priorNinetyNinePercentConfidence: "13.8 months",
  benchmark: "the portfolio the investor would otherwise have owned",
  certaintyClass: "contractual" as CertaintyClass,
  note: "A fifth more edge buys about two months. Certainty is a property of the pairing of edge and benchmark, not of the edge's size.",
  asOf: asOf("2026-08-12"),
  source: structural,
} as const;

/** The reference investor every line above is sized for. Quoting a per-sleeve number as a portfolio number is how tax figures get inflated. */
export const referenceInvestor = {
  jurisdiction: "US federal individual, state tax excluded and additive",
  bracket: "top: 40.8% ordinary, 23.8% qualified",
  horizon: "30 years, liquidating at the end",
  allocation: "60% US equity, 14% developed ex-US, 6% emerging, 20% taxable bonds",
  accounts: "40% of the portfolio in tax-advantaged capacity, 60% taxable",
  growthAssumption: "7% pre-tax log growth, constant parameters, no volatility, no cash flows",
  asOf: asOf("2026-08-12"),
  source: structural,
} as const;

/**
 * Deferral and the step-up: the largest number in the record, and it is a hurdle.
 * The total is horizon-free because both endpoints compound at constant rates; the
 * horizon only decides how it splits.
 */
export const deferralHurdle = {
  horizonFreeTotalBp: 162.21,
  byHorizon: [
    { years: 10, deferralBp: 34.6, stepUpBp: 127.6, totalBp: 162.2 },
    { years: 20, deferralBp: 63.4, stepUpBp: 98.8, totalBp: 162.2 },
    { years: 30, deferralBp: 84.1, stepUpBp: 78.1, totalBp: 162.2 },
    { years: 40, deferralBp: 99.0, stepUpBp: 63.3, totalBp: 162.2 },
  ],
  /** Half the penalty arrives in the first tenth of the turnover. "Low turnover" is not a defence. */
  concavityAtThirtyYears: [
    { shareOfStandingGainRealisedAnnually: 0.1, costBp: 41.5 },
    { shareOfStandingGainRealisedAnnually: 0.25, costBp: 63.9 },
    { shareOfStandingGainRealisedAnnually: 0.5, costBp: 76.4 },
    { shareOfStandingGainRealisedAnnually: 1.0, costBp: 84.1 },
  ],
  vanishesWhen: "In every sheltered account and in the 0% long-term bracket, where the whole expression is zero.",
  note: "The 84.1 bp deferral component alone is 95% of the entire 89 bp budget the repository had already booked. Any strategy that fully turns over a taxable portfolio must out-earn it before its fee and its spread.",
  source: structural,
  asOf: asOf("2026-08-12"),
} as const;

/** Two levers priced and left out on purpose, because their sign cannot be checked here. */
export const notBooked = [
  {
    id: "capital-efficiency",
    label: "Return-stacking and capital efficiency",
    reason:
      "A 90/60 fund needs 92.0 bp/yr of Treasury excess return over cash before its overlay contributes anything, against a measured futures funding basis of 58.70 bp/yr that was positive in all 28 years measured. Both inputs are forecasts, so it cannot enter a contractual budget however good the mechanism looks.",
    source: structural,
  },
  {
    id: "section-1256",
    label: "Section 1256 60/40 treatment",
    reason:
      "Worth 51 bp/yr against ordinary annual treatment and −31 bp/yr against a deferred long-only holding, so the counterfactual decides the sign and the statute does not settle it. In practice the split reached no shareholder of any fund checked: DBMF, KMLM and CTA all distributed 100% ordinary income.",
    source: structural,
  },
  {
    id: "traditional-vs-roth",
    label: "Traditional against Roth",
    reason:
      "Multiplication commutes, so the two are identical whenever the contribution and withdrawal rates are equal. The entire difference is a forecast of your own marginal rate decades out, which is probabilistic and does not belong in a contractual budget.",
    source: structural,
  },
  {
    id: "municipal-bonds",
    label: "Municipal bonds",
    reason:
      "Real and maturity-dependent — the break-even marginal rate falls from 39.8% at two years to 15.6% at thirty, so a top-bracket investor gains 7 bp at two years and 222 at thirty. Booked at zero for the reference investor because bonds go into the shelter first by a factor of four, and municipals only activate once the bond allocation exceeds shelter capacity.",
    source: structural,
  },
  {
    id: "errors-avoided",
    label: "Wash sales into an IRA, and non-qualified dividends",
    reason:
      "An avoided mistake is not a return source. Both are sized so they can be dismissed with a number: 119 bp for a 5%-of-portfolio disallowance at the top rate, and 10.2 bp for a fund only 70% qualified on a 2% yield.",
    source: structural,
  },
] as const;

/** What the whole budget assumes. Every one fails in a direction that mostly reduces the measured advantage. */
export const budgetAssumptions: readonly string[] = [
  "7% pre-tax log growth with constant parameters, no volatility and no cash flows.",
  "Tax paid out of the account rather than from an external wallet, and distributions reinvested.",
  "Rates constant over thirty years, which no thirty-year period in US history has satisfied. This is the one assumption that cuts both ways.",
  "The reference investor's allocation and account split held fixed.",
  "US federal only. State tax is excluded and additive; a jurisdiction with no foreign tax credit turns the location question into a pure cost, and one taxing gains on accrual removes the deferral hurdle entirely.",
];

export const edgeBudgetSources = { structural, recommendation, decomposition } as const;
