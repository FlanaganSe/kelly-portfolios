import { type AsOf, asOf, type Citation, type EvidenceStatus } from "~/content/types";

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
  docPath: "docs/research/factor-product-audit.md",
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
      "Chaining premium × loading × capture − cost gives +0.09 to −0.39 pp/yr on the US premium and +0.28 to +0.76 on the pooled one. It is negative on the defensible reading of both terms. VBR's own tracking error is not published anywhere in this repository.",
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
      "Fifty-four months, one benchmark, no bid-ask or brokerage, and no fallback if this single fund fails. Its distribution tax drag is 2.09 pp/yr in a taxable account — 2.5× the fee — and zero in a shelter. The index's own post-publication interval includes zero and fails Holm.",
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
      "Momentum is the largest gross premium in this repository, pooled +7.33 pp/yr, and MTUM delivers the exposure cleanly. It is excluded on three other grounds: turnover, a shelf of one, and three regions that crash together.",
    caveat:
      "It lost 1.22 pp/yr to a three-fund combination whose fee premium over it was 0.12 — leaving the audit's 1.10 pp/yr shortfall figure, which is the tracking difference net of that fee advantage. Its pooled detection threshold is 4.98 pp/yr, the worst here; its three regions are worth 1.33 effective regions and all lost their worst calendar year in 2009; and the academic construction rebalances monthly at an assumed 3.30–18.67 pp/yr of cost against a 7.33 gross premium. MTUM is the entire retail momentum shelf clearing $1bn and 0.60%.",
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
    caveat: "QUAL and SPHQ are the entire quality shelf. Any later work needing a quality proxy has two candidates.",
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
    source: { ...productAudit, anchor: "7-shrinkage-the-annualisation-trap-and-the-look-ahead-replication" },
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
    statusNote: "No experiment here graded it. It is priced from the arithmetic of what it would have to earn.",
    loading: null,
    feeBp: 20,
    feeAsOf: asOf("2026-08-12"),
    reason:
      "A 90/60 fund needs 92.0 bp/yr of Treasury excess return over cash before the overlay contributes anything, against a measured futures funding basis of 58.70 bp/yr that was positive in all 28 years measured. Both inputs are forecasts.",
    caveat:
      "Its own record does not settle it either way: +2.57 pp/yr against 60/40 since inception and −1.97 pp/yr against equities, and no 90/60 blended comparator is published. Outperforming a lower-risk portfolio in an equity bull market is exactly the trap a risk-matched comparator exists to catch. It also made no capital-gains distributions in any year 2022–2026, which is a real and separate point in its favour.",
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
    ticker: null,
    verdict: "untested",
    status: null,
    loading: null,
    feeBp: null,
    feeAsOf: null,
    reason:
      "No experiment here has run on it. The prior from the literature is that it is an average hedge and a short-lived safe haven in some countries and samples, not a universal negative-correlation asset.",
    source: {
      label: "Portfolio edge research framework",
      docPath: "docs/research/portfolio-edge-research-framework.md",
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
    pooledPremium: "+1.342 pp/yr of marginal certainty equivalent at a 15% sleeve weight",
    pooledInterval: "[+0.759, +1.916] over 432 months; +1.011 [−0.175, +2.165] post-publication",
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
