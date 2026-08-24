import { asOf, type Citation } from "~/content/types";

/**
 * What is still open, and what would settle it. Each item is a measurable target,
 * not a hope.
 *
 * Three groups: the conditions that would change the recommended construction, the
 * framework's open decisions, and the investor-policy inputs nobody has supplied.
 */

const recommendation: Citation = {
  label: "The recommended portfolio",
  docPath: "docs/research/portfolio-recommendation.md",
  anchor: "what-would-change-the-position",
};

const framework: Citation = {
  label: "Portfolio edge research framework",
  docPath: "docs/research/portfolio-edge-research-framework.md",
  anchor: "assumptions-and-open-questions",
};

export type OpenQuestionGroup = "changes-the-construction" | "framework-open-decision" | "investor-policy";

export interface OpenQuestion {
  readonly id: string;
  readonly group: OpenQuestionGroup;
  readonly question: string;
  readonly whyItIsOpen: string;
  readonly whatWouldSettleIt: string;
  readonly source: Citation;
}

export const openQuestions: readonly OpenQuestion[] = [
  // --- What would change the construction -----------------------------------
  {
    id: "etf-share-classes",
    group: "changes-the-construction",
    question: "Do ETF share classes spread far enough to kill the fund-structure line?",
    whyItIsOpen:
      "94 SEC orders are granted as of 2026-08-11, covering roughly ninety fund families, with only two applications still noticed and unordered. The run rate has fallen to single digits a month, so this is routine processing rather than an open policy question — but nobody has measured whether the new share classes actually eliminate the distributions.",
    whatWouldSettleIt:
      "Broad adoption takes the +23 bp line towards zero and the budget to about 86 bp. Re-check the order count before leaning on that line. No SEC document quantifies the benefit, and the operative conditions live in each applicant's own 40-APP application, which was not read.",
    source: recommendation,
  },
  {
    id: "852b6-repeal",
    group: "changes-the-construction",
    question: "Is §852(b)(6) repealed?",
    whyItIsOpen:
      "A 2021 Senate Finance discussion draft proposed exactly that. It was never enacted and no successor bill was found, though Treasury and IRS officials discussed boundary cases publicly in July 2026.",
    whatWouldSettleIt: "Enactment removes the ETF wrapper advantage outright.",
    source: recommendation,
  },
  {
    id: "qualified-rate-changes",
    group: "changes-the-construction",
    question: "What happens to placement if the qualified-dividend schedule moves?",
    whyItIsOpen: "The whole inversion turns on where the break-evens fall relative to four live rates.",
    whatWouldSettleIt:
      "Below 10.52%, developed ex-US belongs in taxable too. At or above 21.51%, emerging returns to the shelter and the inversion disappears.",
    source: recommendation,
  },
  {
    id: "licensed-price-source",
    group: "changes-the-construction",
    question: "Can a licensed, survivorship-free, point-in-time total-return source be obtained?",
    whyItIsOpen:
      "Every free source tested is unusable, and not because of reachability: none publishes a documented total-return contract, corporate-action treatment, delisting coverage or revision history. This is the single binding constraint on every investable conclusion.",
    whatWouldSettleIt:
      "A source covering the listed shelf from at least 2003 — so the window is 240 months rather than 72 — with coded exit reasons, stable economic fund identity, inception and vendor first-seen dates, point-in-time fees and net assets, and retrievable vintages. A source supplying returns but not exit reasons or vintages lifts nothing, and paying for one would be the most expensive way to learn nothing.",
    source: {
      label: "0002 — No research-grade free price source",
      docPath: "docs/decisions/0002-no-research-grade-free-price-source.md",
    },
  },
  {
    id: "exus-factor-product",
    group: "changes-the-construction",
    question: "Does any audited ex-US or emerging value product exist?",
    whyItIsOpen:
      "The value premium's weight is +5.07 pp/yr developed ex-US and +7.58 emerging against +1.57 in the US, and the US product audit's screen removed 185 international, 82 global and 51 emerging series. This repository has audited zero ex-US factor products.",
    whatWouldSettleIt:
      "Running Experiment 009, whose specification is frozen. It is the single largest gap between where a premium was measured and where a product was tested, and it needs no purchase.",
    source: recommendation,
  },
  {
    id: "second-trend-product",
    group: "changes-the-construction",
    question: "Is there a second managed-futures ETF with a loading at or above 0.50?",
    whyItIsOpen: "One listed product delivers the exposure, so a manager or structure failure has no fallback.",
    whatWouldSettleIt:
      'A second product measured against a per-fund benchmark built from its own stated universe, which would also separate "does not deliver trend" from "does not deliver this trend".',
    source: recommendation,
  },
  {
    id: "momentum-turnover",
    group: "changes-the-construction",
    question: "What does a long-only momentum fund actually turn over?",
    whyItIsOpen:
      "The 27.5–91.5%/month figure belongs to a monthly-rebalanced academic long-short spread and must never be applied to a fund. Applying it overstates a fund's cost by roughly an order of magnitude, and an earlier analysis here did exactly that.",
    whatWouldSettleIt:
      "A measured one-sided monthly turnover below 50% for a long-only momentum fund reopens momentum.",
    source: recommendation,
  },
  {
    id: "leverage-reopening",
    group: "changes-the-construction",
    question: "What would reopen the zero-leverage rule?",
    whyItIsOpen: "Leverage was conditioned on an unlevered edge surviving the protocol. None has.",
    whatWouldSettleIt:
      "All four together: a measured implied financing spread on the specific contracts a candidate rolls, a term premium signed under this repository's own protocol, a defined investor policy, and a modelled forced-liquidation path.",
    source: recommendation,
  },
  {
    id: "rmw-cma-reopening",
    group: "changes-the-construction",
    question: "Could profitability or investment ever be reopened?",
    whyItIsOpen:
      "Both are closed on public data, which is a bounded final answer rather than a request for more research. The pooled detection threshold scales as one over the square root of the sample.",
    whatWouldSettleIt:
      "Roughly a further decade — about 245 months, ending near 2035 — or a genuinely independent non-French construction on a different universe and a different vendor's accounting data. A new vintage of the same files, a different block length, a different pooling weight or a different era boundary inside the same sample does not.",
    source: {
      label: "0005 — Profitability and investment premia are closed on public data",
      docPath: "docs/decisions/0005-factor-premia-closed-on-public-data.md",
    },
  },
  {
    id: "holdout-window",
    group: "changes-the-construction",
    question: "When should the 2026-01-onward window be read?",
    whyItIsOpen:
      "It is unread in every file and is a genuine holdout. Looking once converts a holdout into training data.",
    whatWouldSettleIt:
      "Not yet. Six to eight months against a 2.6 pp/yr detection floor spends a genuine holdout for very little. It is the natural confirmatory test under a new frozen specification, later.",
    source: recommendation,
  },
  {
    id: "phase1-vintage",
    group: "changes-the-construction",
    question: "Can the 2013–14 CRSP vintage be obtained?",
    whyItIsOpen:
      "It is the one observation that would settle whether HML's and RMW's second moments moved because of retroactive restatement or because of a construction difference. Ken French publishes no vintage archive.",
    whatWouldSettleIt:
      "A co-author's archive, a replication package or an institutional mirror. Worth stating plainly: the band it would remove is checked cell by cell in both experiments and changes no conclusion anywhere.",
    source: {
      label: "Fama-French factor reproduction",
      docPath: "docs/research/fama-french-reproduction.md",
    },
  },

  // --- The framework's open decisions ---------------------------------------
  {
    id: "framework-1-investor",
    group: "framework-open-decision",
    question: "Who is the modelled investor?",
    whyItIsOpen:
      "Taxable or tax-advantaged, horizon, currency, liabilities, cash flows, drawdown tolerance and accessible instruments are all unset. Two experiments each declared a CRRA gamma of 3 for their own comparison; that is a per-experiment preference, not a product decision.",
    whatWouldSettleIt:
      "A stated investor policy. It is the binding constraint on producing an allocation rather than a design map, and without it the equity/bond variants are ranges rather than an answer.",
    source: framework,
  },
  {
    id: "framework-3-datasets",
    group: "framework-open-decision",
    question:
      "Which point-in-time datasets are licensed, reproducible and rich enough to model delistings, publications, spreads, borrow, futures and options?",
    whyItIsOpen: "None currently available is. See the licensed-source question above, which is the same constraint.",
    whatWouldSettleIt:
      "A budget decision that has not been taken, against a contents specification that already exists.",
    source: framework,
  },
  {
    id: "framework-4-implementability",
    group: "framework-open-decision",
    question:
      "What capital scale, tax model, leverage source, margin rules and liquidity reserve define implementability?",
    whyItIsOpen: 'None of them is declared, so "implementable at realistic scale" has no test behind it.',
    whatWouldSettleIt: "The same investor policy that closes open decision 1.",
    source: framework,
  },
  {
    id: "framework-6-constructions",
    group: "framework-open-decision",
    question:
      "Which factor themes survive both the strict frequentist and the hierarchical Bayesian construction, and stay positive after executable costs?",
    whyItIsOpen:
      "Four factors were measured on the value-weighted French construction only. The equal-weighted variant is not distributed and the test was not run, which matters because that single choice moves published replication rates from 35% to 58.6%.",
    whatWouldSettleIt: "The underlying sorted portfolios, which the distributed files do not supply.",
    source: framework,
  },
  {
    id: "framework-7-net-of-cost",
    group: "framework-open-decision",
    question: "What is the net-of-cost equivalent of each gross figure?",
    whyItIsOpen:
      "Every academic long-short figure in the record is gross of transaction costs, shorting costs, borrow, fees and taxes, and is an upper bound of unknown tightness. Turnover cannot be recovered from a return series.",
    whatWouldSettleIt:
      "A measured turnover for the specific product in question, never an academic assumption imported onto a fund.",
    source: framework,
  },
  {
    id: "framework-8-kelly",
    group: "framework-open-decision",
    question: "Does risk-constrained Kelly beat fractional Kelly on bootstrapped historical returns?",
    whyItIsOpen:
      "The published advantage is about 34% in growth at matched drawdown risk on a finite-outcome case, and it vanished on that same paper's fat-tailed mixture — the case it says resembles a real portfolio problem. Only two synthetic single draws were ever tested.",
    whatWouldSettleIt: "Nothing yet, and correctly deferred: it sizes an edge, and there is no edge to size.",
    source: framework,
  },
  {
    id: "framework-9-covariance",
    group: "framework-open-decision",
    question: "What estimation window and regime-conditioning should a covariance matrix use?",
    whyItIsOpen:
      "The bond–stock beta sign flipped positive 1970–2000, negative 2000–2022, and positive again 2023–2025Q2 across the US, UK and Eurozone. For HML and RMW any such matrix also inherits Phase 1's 3–5% systematic volatility band.",
    whatWouldSettleIt: "A conditioning scheme argued and frozen before it is fitted.",
    source: framework,
  },
  {
    id: "framework-10-liquidity",
    group: "framework-open-decision",
    question:
      "How many days of autonomous cash liquidity are required, and which assets are genuinely monetizable under stress?",
    whyItIsOpen:
      "The framework requires a liquidity reserve and no experiment here sizes one. March 2020 impaired even the Treasury market.",
    whatWouldSettleIt: "An investor-policy input. It is still missing.",
    source: framework,
  },
  {
    id: "fund-delivered-capture",
    group: "framework-open-decision",
    question: "What is a real fund's delivered capture?",
    whyItIsOpen:
      "Every capture figure here comes from research portfolios. A fund's tilt is its holdings, not a sort, and the two are not the same quantity.",
    whatWouldSettleIt:
      "Holdings rather than returns — the product audit's data rather than the capture experiment's. It is the next move and nobody has made it.",
    source: {
      label: "The long-only capture fraction",
      docPath: "docs/research/long-only-capture.md",
    },
  },
  {
    id: "emerging-inversion-durability",
    group: "framework-open-decision",
    question: "Does the emerging-market placement inversion survive capital-gain distributions and harvesting value?",
    whyItIsOpen:
      "Neither is quantified anywhere here, both cut against the inversion, and either could close a 6 bp gap.",
    whatWouldSettleIt: "Sizing both, against the same reference investor.",
    source: {
      label: "Structural and tax-aware edges",
      docPath: "docs/research/structural-and-tax-edges.md",
    },
  },
];

/**
 * The investor-policy inputs nobody has supplied. Without these the equity/bond
 * variants are ranges rather than an answer, and no page here can narrow them.
 */
export const missingInvestorPolicyInputs: readonly string[] = [
  "Horizon and liability model.",
  "Drawdown and shortfall tolerance, and the loss that would force a sale.",
  "Cash flows in and out, and whether contributions continue.",
  "Marginal federal and state bracket, now and expected at withdrawal.",
  "Balances by account type and remaining contribution capacity.",
  "High-deductible-plan status.",
  "Existing lots and their basis.",
  "Employer stock in a qualified plan, for the §402(e)(4)(B) net-unrealised-appreciation election.",
  "Currency and home-country bias.",
  "Capital scale.",
  "Permitted instruments.",
  "Liquidity reserve, in days.",
  "The objective. Net geometric growth is declared here as a preference, and a consumption or shortfall objective would change the answer.",
];

export const missingInputsSource: Citation = {
  label: "The recommended portfolio, the investor-policy inputs still missing",
  docPath: "docs/research/portfolio-recommendation.md",
  anchor: "what-would-change-the-position",
};

export const openQuestionsAsOf = asOf("2026-08-12");
