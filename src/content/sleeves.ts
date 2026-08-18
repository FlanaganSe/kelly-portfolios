import { type AsOf, asOf, type Citation, type EvidenceStatus, type KeyNumber } from "~/content/types";

/**
 * Every candidate return source that was tested, including the ones that lost.
 *
 * The rejections carry their reasons because the reasons are not interchangeable.
 * "KMLM's loading interval includes zero" reads as "KMLM is not *this* index", not
 * as "KMLM is not trend". "VTV's replication is degenerate" reads as "value
 * underperformed the market over these 72 months", not as a defect in the fund. And
 * momentum is excluded despite carrying the largest gross premium measured anywhere
 * here.
 */

const productAudit: Citation = {
  label: "Investable factor products",
  docPath: "docs/research/factor-products.md",
};
const trend: Citation = {
  label: "Trend: the index, the products, and an ambiguous clause",
  docPath: "docs/research/trend-marginal-value.md",
  anchor: "experiment-008--the-products",
};
const persistence: Citation = { label: "Factor persistence and decay", docPath: "docs/research/factor-persistence.md" };
const capture: Citation = { label: "The long-only capture fraction", docPath: "docs/research/long-only-capture.md" };
const recommendation: Citation = {
  label: "The recommended portfolio",
  docPath: "docs/research/portfolio-recommendation.md",
};
const structural: Citation = {
  label: "Structural and tax-aware edges",
  docPath: "docs/research/structural-and-tax-edges.md",
};
const marginalValue: Citation = {
  label: "What a sleeve is worth inside a portfolio, rather than on its own",
  docPath: "docs/research/marginal-sleeve-value.md",
};

export type SleeveVerdict = "hold" | "optional" | "excluded" | "untested";

export interface Loading {
  /** The factor the loading is on, as the audit graded it. */
  readonly factor: string;
  readonly value: number;
  /** The interval as printed. A loading without it is a misquote. */
  readonly interval: string;
  readonly note?: string;
}

export interface Sleeve {
  readonly id: string;
  readonly label: string;
  /** `null` where the candidate is not a product. */
  readonly ticker: string | null;
  readonly verdict: SleeveVerdict;
  /** `null` where no experiment here assigned a status. */
  readonly status: EvidenceStatus | null;
  readonly statusNote?: string;
  /** `null` where the exposure was never measured, or the candidate is not a product. */
  readonly loading: Loading | null;
  /** Basis points a year. `null` where no experiment here read it. */
  readonly feeBp: number | null;
  readonly feeAsOf: AsOf | null;
  /** One or two sentences. Why it lands where it lands. */
  readonly reason: string;
  /** The counter-evidence that travels with the verdict, where the verdict alone would mislead. */
  readonly caveat?: string;
  readonly source: Citation;
}

export const sleeves: readonly Sleeve[] = [
  {
    id: "cheap-broad-market",
    label: "Cheap broad market",
    ticker: "VTI",
    verdict: "hold",
    status: null,
    statusNote: "It is the control, not a candidate. Every candidate was measured against it and none beat it.",
    loading: null,
    feeBp: 3,
    feeAsOf: asOf("2026-08-10"),
    reason:
      "The only line in the whole record whose delivery is contractual rather than statistical. Its cost is certain; its return is not, and no page here forecasts it.",
    caveat:
      "The standard factor model does not even span it: FF5+UMD prices VTI at −0.55 pp/yr with a HAC t of −3.41 over 2020–2025.",
    source: {
      label: "0003 — The cheap broad-market control",
      docPath: "docs/decisions/0003-cheap-broad-market-control.md",
    },
  },
  {
    id: "vbr-small-value",
    label: "Small-cap value",
    ticker: "VBR",
    verdict: "optional",
    status: "exploratory",
    statusNote: "An `exploratory` product on an `exploratory` premium. Both rungs are the lowest one.",
    loading: {
      factor: "HML",
      value: 0.41,
      interval: "[+0.322, +0.480]",
      note: "delivered and stable across the fixed split",
    },
    feeBp: 5,
    feeAsOf: asOf("2026-08-12"),
    reason:
      "It is the only US value product that both delivers its exposure and does not lose to a cheap combination — a shortfall of −0.62 pp/yr, meaning it beat the fitted four-fund mix. It is not here because the chain is positive.",
    caveat:
      "The chain carries no capture term: a capture fraction is itself an HML loading, so multiplying the two discounted one exposure twice. Restated as weight × (loading − VTI's +0.0247) × premium − cost, a 20% VBR tilt is +28.7 bp of edge and +18.2 bp of growth on the pooled premium. AVUV, which the corrected census frame admitted after this sleeve was written, delivers +0.537 rather than +0.410. VBR's tracking error against VTI is 10.48 pp/yr, measured over 2020-01…2025-12.",
    source: recommendation,
  },
  {
    id: "dbmf-managed-futures",
    label: "Managed futures",
    ticker: "DBMF",
    verdict: "optional",
    status: "exploratory",
    statusNote: "An `exploratory` product on an `unresolved` index.",
    loading: {
      factor: "AQR TSMOM index",
      value: 0.671,
      interval: "[+0.513, +0.829]",
      note: "halves +0.59 then +0.73; all 19 rolling windows 0.658 to 0.816, no sign change",
    },
    feeBp: 85,
    feeAsOf: asOf("2026-08-12"),
    reason:
      "One product on the listed shelf delivers the index's exposure, and it is the one that sells replication. It trailed a cost-free vendor index by 0.48 pp/yr against an 0.85% fee. Three independent measurements agree it is the index scaled down by about two thirds.",
    caveat:
      "Fifty-four months, one benchmark, no bid-ask or brokerage. Its distribution tax drag is 2.09 pp/yr in a taxable account — 2.5× the fee — and zero in a shelter; the same trend notional held through the return-stacked wrapper RSST carries 0.32 pp/yr. The listed shelf has gone from five funds to fifteen, so the fallback risk has eased, but none of the newcomers has been tested. The index's own post-publication interval includes zero and fails Holm.",
    source: trend,
  },
  {
    id: "mtum-momentum",
    label: "Momentum",
    ticker: "MTUM",
    verdict: "excluded",
    status: "rejected",
    statusNote: "Rejected on cost, not on premium weakness.",
    loading: {
      factor: "UMD",
      value: 0.444,
      interval: "[+0.277, +0.562]",
      note: "sign stable across the fixed split and all 37 rolling windows",
    },
    feeBp: 15,
    feeAsOf: asOf("2026-08-12"),
    reason:
      "Momentum is the largest gross premium in this repository, pooled +7.33 pp/yr, and MTUM delivers the exposure cleanly. It is excluded on two other grounds: turnover, and three regions that crash together.",
    caveat:
      "It lost 1.22 pp/yr to a three-fund combination whose fee premium over it was 0.12 — leaving the audit's 1.10 pp/yr shortfall figure, which is the tracking difference net of that fee advantage. Its pooled detection threshold is 4.98 pp/yr, the worst here; its three regions are worth 1.33 effective regions and all lost their worst calendar year in 2009; and the academic construction rebalances monthly at an assumed 3.30–18.67 pp/yr of cost against a 7.33 gross premium. The third ground has gone: `MTUM is the entire retail momentum shelf` was true of the census frame Experiment 002 screened, and the corrected frame carries six momentum products of which four reach `exploratory`.",
    source: productAudit,
  },
  {
    id: "qual-quality",
    label: "Quality",
    ticker: "QUAL",
    verdict: "excluded",
    status: "rejected",
    loading: { factor: "RMW", value: 0.186, interval: "[+0.101, +0.247]" },
    feeBp: 15,
    feeAsOf: asOf("2026-08-12"),
    reason:
      "The profitability premium is `rejected` and closed on public data. An unsigned premium makes the product's own quality irrelevant to the decision.",
    caveat:
      "`Rejected` does not mean the premium is zero. It means the publicly available data cannot sign it either way, and that adding more of the same data provably will not: RMW pooled at +2.53 pp/yr against its own measured 2.62 pp/yr detection threshold.",
    source: {
      label: "0005 — Profitability and investment premia are closed on public data",
      docPath: "docs/decisions/0005-factor-premia-closed-on-public-data.md",
    },
  },
  {
    id: "sphq-quality",
    label: "Quality, second product",
    ticker: "SPHQ",
    verdict: "excluded",
    status: "unresolved",
    statusNote:
      "Unresolved on its own exposure: the interval straddles the 0.15 threshold and 72 months cannot say more.",
    loading: { factor: "RMW", value: 0.176, interval: "[+0.079, +0.296]" },
    feeBp: 15,
    feeAsOf: asOf("2026-08-12"),
    reason:
      "Same reason as QUAL, and it does not turn on the product. Its shortfall against the cheap combination is −0.13, so nothing about the fund decides this.",
    caveat:
      "`QUAL and SPHQ are the entire quality shelf` was true of Experiment 002's census frame. The corrected frame carries nine quality products and NOT ONE reaches `exploratory`: five fire a falsifier clause and four are unresolved with intervals straddling 0.15. A quality proxy is not purchasable on this shelf at this threshold, which is a stronger statement than the old one.",
    source: productAudit,
  },
  {
    id: "vtv-large-value",
    label: "Large-cap value",
    ticker: "VTV",
    verdict: "excluded",
    status: "rejected",
    loading: { factor: "HML", value: 0.337, interval: "[+0.225, +0.471]" },
    feeBp: 3,
    feeAsOf: asOf("2026-08-12"),
    reason:
      "It delivers a real HML loading at 3 bp and still carries a +2.57 pp/yr shortfall against the fitted cheap combination.",
    caveat:
      'That shortfall is not a defect in the fund. VTV is itself one of the four funds the replication is built from, and a fund is never in its own basis, so its replication degenerates to 0.784 VTI + 0.216 VB at 7.48 pp/yr of tracking error. Read the rejection as "value underperformed the market over these 72 months" — a return finding the audit is not entitled to make.',
    source: { ...productAudit, anchor: "the-comparator-shrinkage-and-two-traps" },
  },
  {
    id: "vb-small-cap",
    label: "Plain small-cap",
    ticker: "VB",
    verdict: "excluded",
    status: "rejected",
    loading: { factor: "SMB", value: 0.599, interval: "[+0.516, +0.684]" },
    feeBp: 3,
    feeAsOf: asOf("2026-08-10"),
    reason:
      "The largest shortfall on the shelf at +2.89 pp/yr, and the size premium underneath it is not signable: +1.91 pp/yr over 750 months against its own 4.73 pp/yr detection threshold, and +0.41 post-publication.",
    caveat:
      "VB's replication is degenerate for the same reason as VTV's — 0.733 VTI + 0.267 VTV at 8.31 pp/yr of tracking error — so the shortfall is the realised style return of 2020–2025. Its 2.72 bp round-trip spread is nearly a full year of expense ratio.",
    source: { ...capture, anchor: "momentum-and-size" },
  },
  {
    id: "cta-managed-futures",
    label: "Managed futures, Simplify",
    ticker: "CTA",
    verdict: "excluded",
    status: "rejected",
    loading: {
      factor: "AQR TSMOM index",
      value: 0.475,
      interval: "[+0.058, +0.991]",
      note: "halves −0.31 then +0.81; the point estimate misses the 0.50 bar by 0.025",
    },
    feeBp: 75,
    feeAsOf: asOf("2026-08-12"),
    reason:
      "Forty-six months and an interval running from +0.058 to +0.991. Under the frozen rule the point estimate decides, and this is the shakiest classification on the page.",
    caveat:
      "Its exposure profile is the odd one on the shelf: a static market beta of −0.053 and a negative volatility-scaled loading, which is not the trend shape at all over these months, whatever it is.",
    source: trend,
  },
  {
    id: "fmf-managed-futures",
    label: "Managed futures, First Trust",
    ticker: "FMF",
    verdict: "excluded",
    status: "rejected",
    loading: {
      factor: "AQR TSMOM index",
      value: 0.303,
      interval: "[+0.183, +0.420]",
      note: "78 months, the longest history on the shelf; 43 rolling windows 0.235 to 0.483",
    },
    feeBp: 98,
    feeAsOf: asOf("2026-08-12"),
    reason: "It stably delivers about a third of the index, which is below the frozen 0.50 bar.",
    source: trend,
  },
  {
    id: "kmlm-managed-futures",
    label: "Managed futures, KraneShares",
    ticker: "KMLM",
    verdict: "excluded",
    status: "rejected",
    loading: {
      factor: "AQR TSMOM index",
      value: 0.245,
      interval: "[−0.148, +0.446]",
      note: "the interval includes zero",
    },
    feeBp: 90,
    feeAsOf: asOf("2026-08-12"),
    reason:
      "It does not deliver this benchmark's exposure, and part of that is definitional rather than a shortcoming. Its own index holds 22 futures and no equity index futures at all, while AQR's universe holds nine.",
    caveat:
      'Read the firing as "KMLM is not *this* index", never as "KMLM is not trend". A per-fund benchmark built from each fund\'s own stated universe would separate the two, and does not exist here.',
    source: trend,
  },
  {
    id: "wtmf-managed-futures",
    label: "Managed futures, WisdomTree",
    ticker: "WTMF",
    verdict: "excluded",
    status: "rejected",
    loading: {
      factor: "AQR TSMOM index",
      value: 0.099,
      interval: "[+0.003, +0.201]",
      note: "76 months, range 0.033 to 0.115",
    },
    feeBp: 66,
    feeAsOf: asOf("2026-08-12"),
    reason: "It delivers almost none of the index's exposure.",
    caveat:
      "Its raw tracking difference is +2.31 pp/yr, meaning it beat the index — which is a return finding nobody is entitled to make on 76 months against a 13.66 pp/yr tracking error.",
    source: trend,
  },
  {
    id: "ntsx-return-stacking",
    label: "Return stacking, and any 90/60 fund",
    ticker: "NTSX",
    verdict: "excluded",
    status: null,
    statusNote:
      "No experiment here graded it. It is priced from the arithmetic of what it would have to earn, and its structure is read from its own N-PORT holdings.",
    loading: null,
    feeBp: 20,
    feeAsOf: asOf("2026-08-17"),
    reason:
      "A 90/60 fund needs 48.3 bp/yr of Treasury excess return over cash before the overlay contributes anything, at the 12–18 bp OIS benchmark a fund actually finances at. The 92.0 bp this line used to state came from a special-collateral repo basis that is not a rate a fund pays. Both inputs are forecasts.",
    caveat:
      "Holdings put it at 90.83% equity plus 63.50% of Treasury futures notional, so 1.54x gross and delta 0.14 — it keeps 85.6% of the funding-rule benefit rather than all of it. Its own record does not settle the overlay either way, and its two siblings are the counter-evidence: NTSI and NTSE have each lost to their own equity leg's index by about 3 pp/yr since 2021. Its zero-capital-gain record comes from $163m of capital loss carryforwards and in-kind redemption relief, not from Treasury futures being elegant.",
    source: { ...structural, anchor: "3-section-1256-and-capital-efficiency-handled-honestly" },
  },
  {
    id: "leverage",
    label: "Leverage of any kind",
    ticker: null,
    verdict: "excluded",
    status: null,
    statusNote: "Zero, and it stays zero.",
    loading: null,
    feeBp: null,
    feeAsOf: null,
    reason: "It was conditioned on an unlevered edge surviving the protocol. None has, so there is nothing to lever.",
    caveat:
      "Four measurable conditions would reopen it together: a measured implied financing spread on the specific contracts a candidate rolls, a term premium signed under this repository's own protocol, a defined investor policy, and a modelled margin and forced-liquidation path.",
    source: { label: "0004 — No sleeve is promoted", docPath: "docs/decisions/0004-no-sleeve-promoted.md" },
  },
  {
    id: "rebalancing-as-return",
    label: "Rebalancing as a source of return",
    ticker: null,
    verdict: "excluded",
    status: "rejected",
    statusNote: "Retained as risk control, forbidden as return.",
    loading: null,
    feeBp: null,
    feeAsOf: null,
    reason:
      "Measured at −38.7 bp/yr on the portfolio and −62.9 bp/yr on the US against developed ex-US pair over 420 months. The realised drift gap ran about 35× the excess growth rate, and relative regional performance trends rather than reverts.",
    caveat:
      "What it did buy is real and is not return: it held exposure within 0.6 to 3.1 percentage points of target against buy-and-hold's 14.8, for 0.3 to 1.2 bp/yr. Anyone who wants their declared allocation to remain their actual allocation should rebalance.",
    source: { label: "Rebalancing policy on real regional equity", docPath: "docs/research/rebalancing-policy.md" },
  },
  {
    id: "academic-small-value-corner",
    label: "The small-value corner, as the academic literature defines it",
    ticker: null,
    verdict: "excluded",
    status: null,
    statusNote: "A real result about a portfolio nobody can hold at scale.",
    loading: null,
    feeBp: null,
    feeAsOf: null,
    reason:
      "The ME1 × BM5 cell held 21.24% of listed firms and 0.236% of market capitalisation at 2025-12. A cell holding a fifth of the listed companies and under a quarter of a percent of the money cannot absorb meaningful assets at the prices its own return series assumes.",
    caveat:
      "The result does not depend on microcaps, which is what makes it interesting: dropping the smallest quintile entirely costs 0.71 pp/yr of a 3.85 pp/yr excess. The investable version delivers +3.14 pp/yr over the market rather than +3.85, gross.",
    source: capture,
  },
  {
    id: "gold",
    label: "Gold",
    ticker: "GLDM",
    verdict: "excluded",
    status: "exploratory",
    statusNote:
      "The gold price is a documented, FCA-regulated benchmark rather than a free price feed, and bullion pays no distribution, so price return minus a stated carry cost is exactly total return. What keeps it exploratory is narrower: no vintage archive, an auction price that is not a retail execution, and a carry cost that is assumed.",
    loading: null,
    feeBp: 10,
    feeAsOf: asOf("2026-08-17"),
    reason:
      "Tested 2026-08-17 under both funding rules, over 618 months from 1975-01 — the first month a US person could legally own it. Its Sharpe ratio is 0.18 against equity's 0.59, and everything follows from that. Funded by selling equity, which is what a physical gold ETF imposes, it loses 0.40 pp/yr against a 0.30 bar. Funded as a financed overlay, which is what a return-stacked wrapper imposes, it gains 0.18 pp/yr — still below the bar and below its own 0.73 detection floor. Its correlation to equity is zero rather than negative, −0.02 to +0.03 and −0.04 to +0.08 inside equity drawdowns, which confirms the prior that it is an average hedge rather than a universal negative-correlation asset.",
    caveat:
      "The forty months from 1971-09 to 1974-12 carry about 40% of the full-sample Sharpe ratio, and private US gold ownership was illegal throughout them, so every figure here excludes them. Beside a trend overlay gold adds rather than substitutes — the two correlate +0.07 — but the increment is 0.09 pp/yr against a detection floor of 1.68. Tax decides where to hold it, not whether: a bullion ETF pays 28% as a collectible plus 3.8% on a gain it can defer for decades, while the overlay wrapper distributes ordinary income every year at a measured 1.53 pp/yr.",
    source: {
      label: "What a sleeve is worth inside a portfolio, rather than on its own",
      docPath: "docs/research/marginal-sleeve-value.md",
    },
  },
  {
    id: "tail-hedges",
    label: "Tail hedges and protective puts",
    ticker: null,
    verdict: "untested",
    status: null,
    loading: null,
    feeBp: null,
    feeAsOf: null,
    reason:
      "No experiment here has run on it. A protective put has to be benchmarked against a return-matched equity/cash mix; comparing it to the fully invested index flatters it, which is the same trap the trend experiment's risk-matched comparator exists to catch.",
    source: {
      label: "Portfolio edge research framework",
      docPath: "docs/research/portfolio-edge-research-framework.md",
    },
  },
  {
    id: "private-credit",
    label: "Private credit",
    ticker: null,
    verdict: "untested",
    status: null,
    loading: null,
    feeBp: null,
    feeAsOf: null,
    reason: "No experiment here has run on it.",
    source: {
      label: "Portfolio edge research framework",
      docPath: "docs/research/portfolio-edge-research-framework.md",
    },
  },
  {
    id: "catastrophe-bonds",
    label: "Catastrophe bonds",
    ticker: null,
    verdict: "untested",
    status: null,
    loading: null,
    feeBp: null,
    feeAsOf: null,
    reason:
      "No experiment here has run on it. Of five capacity-constrained strategies the framework reviewed, four are refuted outright and catastrophe risk is the one left unproven rather than disproven.",
    source: {
      label: "Portfolio edge research framework",
      docPath: "docs/research/portfolio-edge-research-framework.md",
    },
  },
  {
    id: "merger-arbitrage",
    label: "Merger arbitrage",
    ticker: null,
    verdict: "untested",
    status: null,
    loading: null,
    feeBp: null,
    feeAsOf: null,
    reason: "No experiment here has run on it.",
    source: {
      label: "Portfolio edge research framework",
      docPath: "docs/research/portfolio-edge-research-framework.md",
    },
  },
];

// ---------------------------------------------------------------------------
// The ceiling on what diversification can be worth
// ---------------------------------------------------------------------------

/**
 * A base portfolio and the largest diversification credit anything could earn
 * against it.
 *
 * The ceiling is a fact about the base portfolio's variance and about no sleeve,
 * which is why it is held per base rather than per candidate.
 */
export interface CreditCeiling {
  readonly id: string;
  readonly label: string;
  readonly composition: string;
  /** Annualised, as the source page printed it. */
  readonly volatility: string;
  /** The credit a zero-beta sleeve earns at the reference weight, which is `sigma_p^2`. */
  readonly ceilingAtReferenceWeight: string;
}

/** One sleeve's beta to the equity core, and the credit that beta buys. */
export interface CreditRow {
  readonly sleeve: string;
  readonly kind: string;
  readonly beta: string;
  readonly perUnitWeight: string;
  readonly atReferenceWeight: string;
  readonly note: string;
}

/**
 * Why no trend, momentum or managed-futures sleeve is held, stated as the bound it
 * is rather than as a disappointing measurement.
 *
 * Every figure is quoted as the string `docs/research/marginal-sleeve-value.md`
 * printed it. The family is `rejected` and every input is a paper portfolio, a
 * vendor series or a model, so nothing here is investable and the copy must not
 * imply that it is.
 */
export const diversificationCredit = {
  heading: "Why there is no trend, momentum or managed-futures sleeve",
  headline:
    "The credit a sleeve earns for not moving with the portfolio has a ceiling, and the ceiling sits below the bar. That is arithmetic, not a disappointing result.",
  mechanism:
    "Fund a sleeve pro rata out of the portfolio you already hold, and its diversification credit is the portfolio's variance times one minus the sleeve's beta. Set the beta to zero and the credit is exactly the portfolio's variance. That number belongs to the base portfolio. No sleeve can raise it.",
  referenceWeight: "10%",
  materialityThreshold: "0.30 pp/yr",
  bases: [
    {
      id: "global-equity-core",
      label: "Global equity core",
      composition: "60% US, 30% developed ex-US, 10% emerging, monthly rebalanced",
      volatility: "14.73%",
      ceilingAtReferenceWeight: "+0.217 pp/yr",
    },
    {
      id: "balanced-60-40",
      label: "Balanced 60/40",
      composition: "60% of that core plus 40% cash",
      volatility: "8.85%",
      ceilingAtReferenceWeight: "+0.078 pp/yr",
    },
  ] as const satisfies readonly CreditCeiling[],
  verdict:
    "A perfect zero-beta asset, added at a 10% weight, fails on the credit alone. Nothing beats a bound it cannot reach.",
  corollary:
    "The direction catches people out. The ceiling falls as the base portfolio calms down, so a portfolio holding bonds or cash gets a smaller credit, not a larger one. The equity-heavy portfolio is the best case for diversification and it still fails.",
  creditRows: [
    {
      sleeve: "Cash, as a control",
      kind: "Control, built to be worth nothing",
      beta: "+0.001",
      perUnitWeight: "+2.168",
      atReferenceWeight: "+0.217",
      note: "Zero beta, so it lands exactly on the ceiling. It supplies nothing else.",
    },
    {
      sleeve: "Diversified trend",
      kind: "Funded long-short, vendor series",
      beta: "−0.132",
      perUnitWeight: "+2.457",
      atReferenceWeight: "+0.246",
      note: "Nearly the whole of its +0.258 total. Negative beta buys more than the ceiling and pays for it elsewhere.",
    },
  ] as const satisfies readonly CreditRow[],
  ruler:
    "The experiment carried a control designed to supply nothing: cash added to a 100% equity core, funded pro rata out of it. It sits at a beta of +0.001 and lands on the ceiling, +0.217 pp/yr at a 10% weight. The algebra is confirmed by a sleeve built to be worthless.",
  aboveTheCeiling:
    "Five sleeves earn more than the ceiling — the four funded long-short overlays and a modelled Treasury proxy — and every one of them does it with a negative beta rather than a zero one. All five pay for it in the standalone return term instead.",
  trendReading:
    "Trend's own beta to the core is −0.132, worth +0.246 pp/yr at a 10% weight against a total marginal growth contribution of +0.258. So essentially all of what trend contributes is credit rather than return it earned standing alone. It misses the 0.30 bar, its interval runs from −0.545 to +1.069, and its Holm-adjusted p is 1.0000. Nothing in the family of ten survives Holm at 0.05; the best adjusted p anywhere is long-only US momentum's 0.1890, and it fails the bar too at +0.269.",
  fragility:
    "The sleeves whose value is a credit earned it in one crisis. Every negative-beta sleeve collapses in the second half of the sample and every one loses its best year to 2008. Trend goes from +1.243 pp/yr over 1991–2008 to −0.823 over 2009–2025, and doubling the cost assumption alone takes its full-period figure to −0.009.",
  deRisking: {
    headline:
      "The same control is why growth decides here and a certainty equivalent does not. On a CRRA certainty equivalent at gamma = 3 the cash control scores +0.166 pp/yr, while losing 0.643 pp/yr of geometric growth. The gap between the two is payment for holding less equity. Any investor can have that for free.",
    figures: [
      {
        label: "Certainty equivalent, gamma = 3",
        value: "+0.166",
        unit: "pp/yr",
        note: "What the cash control scored on the metric that used to decide.",
      },
      {
        label: "Geometric growth, gamma = 1",
        value: "−0.643",
        unit: "pp/yr",
        note: "What it scored on the metric that decides now.",
      },
      {
        label: "The de-risking reward",
        value: "+0.809",
        unit: "pp/yr",
        note: "The difference, and 2.7× the 0.30 materiality threshold, for a sleeve that supplies nothing.",
      },
    ] as const satisfies readonly KeyNumber[],
    source: {
      label: "0008 — Geometric growth decides; the certainty equivalent reports beside it",
      docPath: "docs/decisions/0008-growth-decides-crra-reports.md",
    } as const satisfies Citation,
  },
  caveat:
    "The ceiling is arithmetic. What goes into it is not. The volatilities and the betas are estimates from 420 months, 1991 to 2025, and the credit is a difference of two covariances — several of these move by more than themselves when the correlation moves by 0.10. Gold has since been tested and it lands exactly on the ceiling: its beta to the equity core measures zero, so it takes the whole credit and still loses 0.10 pp/yr. Per unit of weight the credit is 2.17 pp/yr against a standalone shortfall of 2.95, so the most the credit can ever pay is 74% of the gap — and because both scale with the weight, holding more does not close it.",
  status: "rejected" as EvidenceStatus,
  statusNote:
    "A falsifier written down before the result fired. Two specifications judged the same data, one on a certainty equivalent and one on growth; growth decides, and that is what moved the family from `unresolved` to `rejected`. Every input is a paper portfolio, a vendor series or a model. None of it is investable, and none of it says trend is worthless.",
  source: marginalValue,
  asOf: asOf("2026-08-12"),
} as const;

// ---------------------------------------------------------------------------
// The premia underneath the products
// ---------------------------------------------------------------------------

export interface FactorPremium {
  readonly id: string;
  readonly label: string;
  readonly status: EvidenceStatus | null;
  readonly statusNote: string;
  /** Pooled across US, developed ex-US and emerging, over the frozen post-publication era. Gross, long-short, not investable. */
  readonly pooledPremium: string | null;
  readonly pooledInterval: string | null;
  /** The smallest premium the pooled window could have detected at 80% power. */
  readonly detectionThreshold: string | null;
  /** What three correlated regions were actually worth. */
  readonly effectiveRegions: string | null;
  readonly byRegion: string | null;
  /** Size-neutral long-only capture, where it was measured. */
  readonly longOnlyCapture: string | null;
  readonly source: Citation;
}

export const factorPremia: readonly FactorPremium[] = [
  {
    id: "hml",
    label: "Value (HML)",
    status: "exploratory",
    statusNote:
      "It advanced because its premium is larger than its window's blind spot, not because the blind spot closed. A premium between 2.0 and 3.35 pp/yr is still invisible to this grid.",
    pooledPremium: "+4.74 pp/yr",
    pooledInterval: "[+1.46, +8.10]",
    detectionThreshold: "3.35 pp/yr",
    effectiveRegions: "1.49 of 3 [1.39, 1.68], mean cross-region correlation 0.52",
    byRegion: "US +1.57, developed ex-US +5.07, emerging +7.58 pp/yr",
    longOnlyCapture: "0.520 [0.434, 0.722] size-neutral; 0.958 against the market; the gap is a size premium",
    source: { ...persistence, anchor: "experiment-005--the-regional-replication" },
  },
  {
    id: "umd",
    label: "Momentum (UMD)",
    status: "exploratory",
    statusNote:
      "The largest gross premium here and the worst-diversified. Branch (b) was never reached and would have fired: the detection threshold is 4.98 pp/yr against a 2.0 materiality bar.",
    pooledPremium: "+7.33 pp/yr",
    pooledInterval: "[+3.92, +10.31]",
    detectionThreshold: "4.98 pp/yr, the worst in this repository",
    effectiveRegions: "1.33 of 3, mean cross-region correlation 0.66; all three shared 2009 as their worst year",
    byRegion: "US +4.19, developed ex-US +8.35, emerging +9.44 pp/yr; US recent decade +0.37",
    longOnlyCapture: "0.501 [0.438, 0.565] size-neutral",
    source: { ...persistence, anchor: "experiment-006--regional-momentum" },
  },
  {
    id: "rmw",
    label: "Profitability (RMW)",
    status: "rejected",
    statusNote:
      "Closed on public data. Its pooled premium is smaller than the smallest premium its own pooled window can resolve — and RMW is the factor pooling helped most, because its regions are the least correlated in the grid.",
    pooledPremium: "+2.53 pp/yr",
    pooledInterval: "[+1.07, +3.96]",
    detectionThreshold: "2.62 pp/yr [2.15, 3.07]",
    effectiveRegions: "2.26 of 3 [2.01, 2.65], mean cross-region correlation 0.18",
    byRegion: "US +3.04, developed ex-US +1.68, emerging +2.88 pp/yr",
    longOnlyCapture: null,
    source: {
      label: "0005 — Profitability and investment premia are closed on public data",
      docPath: "docs/decisions/0005-factor-premia-closed-on-public-data.md",
    },
  },
  {
    id: "cma",
    label: "Investment (CMA)",
    status: "rejected",
    statusNote:
      "Closed on public data. Outside the US its post-publication premium is about zero rather than negative, so the US sign flip does not replicate and the rejection rests on materiality rather than on the flip.",
    pooledPremium: "+0.20 pp/yr",
    pooledInterval: "[−2.57, +3.44]",
    detectionThreshold: "3.41 pp/yr [2.60, 4.12]",
    effectiveRegions: "1.76 of 3 [1.60, 1.97]; the one factor whose three regions share the same best year, 2022",
    byRegion: "US −1.39, developed ex-US +0.53, emerging +1.46 pp/yr",
    longOnlyCapture: null,
    source: {
      label: "0005 — Profitability and investment premia are closed on public data",
      docPath: "docs/decisions/0005-factor-premia-closed-on-public-data.md",
    },
  },
  {
    id: "smb",
    label: "Size (SMB)",
    status: null,
    statusNote:
      "Tested as a premium for the first time and not signable. Every interval contains zero and every point estimate sits below its own window's detection threshold.",
    pooledPremium: "+1.91 pp/yr, US, 750 months, smallest minus largest quintile",
    pooledInterval: "[−1.90, +6.00]",
    detectionThreshold: "4.73 pp/yr",
    effectiveRegions: null,
    byRegion: "US only. Post-publication the quintile spread is +0.41 pp/yr and the decile spread −0.01",
    longOnlyCapture:
      "Nominally 0.836 [0.555, 1.135], but it is a ratio of a small number to a smaller one and should not be used",
    source: { ...capture, anchor: "momentum-and-size" },
  },
  {
    id: "trend",
    label: "Diversified trend (AQR TSMOM index)",
    status: "unresolved",
    statusNote:
      "`Rejected` under the absolute reading of clause (d) as frozen, `unresolved` under the relative reading that Experiment 008 judges better justified. Unresolved is not a promotion, and a vendor-series evaluation is capped at `exploratory` in any case.",
    // Decision 0008 constraint 2: growth, the certainty equivalent and the de-risking
    // component between them are published as three numbers or as none. This record
    // carried the CE alone until 2026-08-12.
    pooledPremium:
      "+1.312 pp/yr of marginal geometric growth at a 15% sleeve weight, against +1.342 of CRRA certainty equivalent, so +0.030 of it is de-risking",
    pooledInterval:
      "[+0.759, +1.916] over 432 months, on the certainty equivalent, which is what the frozen specification named as primary and what the risk-matched comparator uniquely entitles it to be. Post-publication +0.883 growth against +1.011 CE, interval [−0.175, +2.165], failing Holm",
    detectionThreshold: null,
    effectiveRegions: null,
    byRegion: null,
    longOnlyCapture: null,
    source: {
      label: "Trend: the index, the products, and an ambiguous clause",
      docPath: "docs/research/trend-marginal-value.md",
      anchor: "clause-d-re-read-under-both-readings",
    },
  },
];

/** Shared exposures the sleeves above do not diversify away from each other. */
export const sharedExposures: readonly string[] = [
  "HML and CMA correlate 0.63 over the common US post-publication window and must never be counted as two independent bets.",
  "Regional factor sleeves are not independent either: US, developed ex-US and emerging HML correlate 0.52 and amount to an effective 1.49 regions; the same three momentum series correlate 0.66 and amount to 1.33.",
  "A momentum tilt gets no regional diversification at all in a crash. All three regions lost their worst calendar year in 2009, and all ten worst pooled months are negative in every region.",
  "Trend is a levered futures book. It shares leverage, funding liquidity, volatility estimation and short borrow with everything else levered.",
  "A factor tilt and a rebalancing policy sit inside the same equity portfolio, so combining their tracking errors in quadrature assumes an independence that is optimistic.",
  "Twenty independent 55% bets give a strict majority only 59.1% of the time, and independence is itself estimated from the same selected history.",
];

export const sleeveAsOf = asOf("2026-08-12");
