import { asOf, type Citation, type EvidenceStatus, type KeyNumber } from "~/content/types";

/**
 * One entry per experiment family. Statuses are the terminal result the ledger
 * records, never a summary of how the result reads.
 */

/** Whether a family produced a ledgered result, and whether anyone has written it up. */
export type RunState =
  /** Ran, ledgered a terminal status, and has a synthesis page under `docs/research/`. */
  | "synthesised"
  /**
   * Ran and ledgered something, in an uncommitted working tree, with no synthesis
   * page. No number from such a run appears anywhere in this content layer, and its
   * `status` stays `null`: a raw ledger line can be superseded by the next run, and
   * the closed-vocabulary status the app displays is set by a synthesis, not by a
   * log entry.
   */
  | "run-not-synthesised"
  /** A frozen specification exists and nothing has been run against it. */
  | "specified-not-run";

export interface Experiment {
  readonly id: string;
  /** "Phase 1", "001" … as the pages name it. */
  readonly number: string;
  readonly title: string;
  /** One sentence: what it actually asked. */
  readonly question: string;
  readonly kind: "confirmatory" | "exploratory";
  readonly runState: RunState;
  /** `null` where no run has produced a terminal status. */
  readonly status: EvidenceStatus | null;
  /** Why the status reads the way it does, where the single word would mislead. */
  readonly statusNote?: string;
  /** Plain English, 2–3 sentences: what it found. */
  readonly verdict: string;
  readonly keyNumbers: readonly KeyNumber[];
  readonly whyItMatters: string;
  readonly whatWouldChangeIt: readonly string[];
  readonly source: Citation;
}

const persistence: Citation = {
  label: "Factor persistence and decay",
  docPath: "docs/research/factor-persistence.md",
};

export const experiments: readonly Experiment[] = [
  {
    id: "phase1-ff-reproduction",
    number: "Phase 1",
    title: "The Fama-French ingestion gate",
    question:
      "Does the download, parse, unit-conversion and summary path reproduce a precisely identified published table?",
    kind: "confirmatory",
    runState: "synthesised",
    status: "unresolved",
    statusNote:
      "Thirteen of fifteen gating cells reproduce. The two that do not are the standard deviations of HML and RMW, against two independently typeset vintages, so the disagreement is systematic rather than sampling error.",
    verdict:
      "Every mean and every t-statistic reproduces, and so does the whole correlation structure. HML's standard deviation comes out 3.0% low and RMW's 5.1% high, and they miss by the same amount against both printed vintages. Exact reproduction is not available at any tolerance, because Ken French publishes no vintage archive and the 2013–14 CRSP vintage the paper used cannot be obtained.",
    keyNumbers: [
      { label: "Gating cells that reproduce", value: "13 of 15" },
      { label: "HML standard deviation", value: "2.7926", unit: "%/mo", note: "against a printed 2.88, 3.0% low" },
      { label: "RMW standard deviation", value: "2.2490", unit: "%/mo", note: "against a printed 2.14, 5.1% high" },
      {
        label: "Largest mean miss",
        value: "+0.0142",
        unit: "pp/mo",
        note: "RMW, against a declared tolerance of 0.02",
      },
      {
        label: "Systematic band carried downstream",
        value: "3–5%",
        note: "on anything that divides by an HML or RMW volatility",
      },
    ],
    whyItMatters:
      "Any Sharpe ratio, volatility-scaled sleeve, risk-parity weight, covariance matrix or Kelly fraction built on those two factors inherits a denominator error that will not shrink with more data.",
    whatWouldChangeIt: [
      "A 2013–14 vintage of the five-factor file from a co-author's archive, a replication package or an institutional mirror.",
      "The six underlying Size-B/M and Size-OP portfolios, which would show whether the gap persists in the 2×2 and 2×2×2×2 blocks.",
      "The published monthly series, which would show whether the disagreement is localised to 2000–2002 or spread across the sample.",
    ],
    source: {
      label: "Fama-French factor reproduction",
      docPath: "docs/research/fama-french-reproduction.md",
    },
  },
  {
    id: "exp-001-factor-decay",
    number: "001",
    title: "Factor persistence across frozen eras in the United States",
    question:
      "Do HML, UMD, RMW and CMA hold a positive, economically meaningful premium after their own publication dates?",
    kind: "exploratory",
    runState: "synthesised",
    status: "unresolved",
    statusNote:
      "Unresolved on power, not on sign. CMA was rejected here and later confirmed rejected; the other three went to Experiments 005 and 006.",
    verdict:
      "Sixteen of the twenty factor-by-era cells hold a premium smaller than their own window could have detected at 80% power, and the four exceptions are the four original paper samples. Not one post-publication cell survives either multiple-testing correction. A zero-mean Gaussian series with HML's length and volatility produced +1.98 pp/yr through the same machinery, against HML's real +1.57.",
    keyNumbers: [
      { label: "Cells underpowered for their own premium", value: "16 of 20" },
      { label: "US HML, full post-publication", value: "+1.57", unit: "pp/yr", interval: "[−2.28, +5.54]" },
      { label: "US UMD, full post-publication", value: "+4.19", unit: "pp/yr", interval: "[−0.34, +8.50]" },
      { label: "US CMA, full post-publication", value: "−1.39", unit: "pp/yr", interval: "[−5.00, +3.02]" },
      { label: "Share of HML's post-publication premium in one year", value: "79%", note: "the year 2000" },
      { label: "HML time under water, post-publication", value: "228 of 384 months" },
    ],
    whyItMatters:
      "It settled that no US post-publication window in the public data can answer the question, which is what sent the work to other regions rather than to more US history.",
    whatWouldChangeIt: [
      "Nothing available in US data alone: the post-publication window is the length it is and it ends at the frozen sample boundary.",
      "Equal-weighted constructions, which the Ken French library does not distribute and which move published replication rates from 35% to 58.6%.",
    ],
    source: { ...persistence, anchor: "experiment-001--the-united-states-grid" },
  },
  {
    id: "exp-002-fund-exposure",
    number: "002",
    title: "The US factor product audit",
    question:
      "Do exchange-traded factor products deliver the exposure they advertise, at a cost that leaves the exposure worth buying?",
    kind: "exploratory",
    runState: "synthesised",
    status: "exploratory",
    statusNote:
      "Superseded as a description of the US shelf by Experiment 013, which re-ran it on a census frame that can see the whole shelf and reproduced every one of these 44 funds to zero difference. Read every count here as counting only the 44 products the 2019Q4 filing quarter contained. Fifteen of them reached the per-fund status exploratory, which permits use as an implementation proxy in a later experiment and nothing else.",
    verdict:
      'Exposure is delivered and alpha is not measurable, and those are two different findings. Thirty-eight of 44 funds reject a zero loading in their mandate\'s own direction, while only five of 132 alpha tests survive a correction valid under dependence, and all five are negative. The comparison that rejected most products is a four-fund combination fitted in sample, so every such rejection reads as "a look-ahead mix of cheap funds beat this over 72 months". The 44 were not the shelf: the frame missed two thirds of it, which is what Experiment 013 corrects.',
    keyNumbers: [
      {
        label: "Screened to audited",
        value: "8,563 → 2,105 → 44",
        note: "the 2019Q4 census alone; see Experiment 013",
      },
      { label: "Statuses", value: "15 exploratory, 24 rejected, 5 unresolved" },
      { label: "Loadings surviving correction", value: "38 of 44", note: "Benjamini-Hochberg at 0.10" },
      { label: "Alpha tests surviving Holm", value: "5 of 132", note: "all negative; five tests are three products" },
      { label: "Median minimum detectable alpha", value: "4.52", unit: "pp/yr" },
      {
        label: "Model-misfit pedestal",
        value: "−0.55",
        unit: "pp/yr",
        note: "VTI's own alpha under FF5+UMD, HAC t = −3.41. Read every alpha as a distance from this, not from zero",
      },
      { label: "2019 factor shelf gone by 2025", value: "20.6%", note: "a lower bound; N-PORT filings begin in 2019" },
    ],
    whyItMatters:
      "It is where a product's delivered exposure was first measured, and where the difference between a fee comparison and a cost comparison showed up. It is also the clearest case in this repository of a correct calculation on the wrong frame.",
    whatWouldChangeIt: [
      "A licensed, survivorship-free, point-in-time total-return source covering the listed shelf from at least 2003, so the window is 240 months rather than 72.",
      "A replication whose weights are fitted on a prior window, which would remove the look-ahead from the clause that did most of the rejecting.",
      "Form N-CSR distributions and turnover, so the cost-of-ownership clause could be evaluated with the term it names.",
      "A census frame that contains the shelf. Done, in Experiment 013.",
    ],
    source: { label: "Investable factor products", docPath: "docs/research/factor-products.md" },
  },
  {
    id: "exp-003-rebalancing",
    number: "003",
    title: "Rebalancing policy on real regional equity",
    question:
      "Does any rebalancing policy beat buy-and-hold on real multi-region equity, from identical weights and identical cash flows, net of the costs it pays?",
    kind: "confirmatory",
    runState: "synthesised",
    status: "rejected",
    verdict:
      "Every policy lost, on all three cost bases, over 35 years, and four independent rejection clauses fired at once. Costs are not the explanation: the dearest policy paid 1.2 bp/yr, and quadrupling every cost moved the result by about a tenth. Relative regional performance trends rather than reverts, and rebalancing is short exactly that.",
    keyNumbers: [
      { label: "Portfolio advantage over buy-and-hold", value: "−38.7", unit: "bp/yr" },
      { label: "US against developed ex-US", value: "−62.9", unit: "bp/yr" },
      { label: "Realised drift gap against gamma-star", value: "about 35×", note: "4.34 pp/yr against 12.5 bp/yr" },
      {
        label: "The 68.27% win-probability floor, realised",
        value: "0.0%",
        note: "zero of 61 rolling 30-year windows on the US / developed ex-US pair",
      },
      { label: "Excess-growth closed form, error", value: "+0.09", unit: "bp/yr", note: "on the portfolio" },
      { label: "Weight drift, untouched against monthly", value: "14.83 pp against 0.60 pp", note: "mean absolute" },
      { label: "Cost of holding the weights", value: "0.3–1.2", unit: "bp/yr" },
    ],
    whyItMatters:
      "The commissioning premise for the whole project was that a rebalancing bonus makes beating the market straightforward. The mathematics is right and the premise about real markets is not.",
    whatWouldChangeIt: [
      "A real, investable, low-correlation pair whose drift gap is genuinely below its excess growth rate. Every pair tested correlated 0.72 to 0.79 in logs.",
      "An after-tax test, which needs tax lots the simulation does not hold. Its direction is clear and its size must not be guessed.",
      "Daily data, which would show intramonth breaches the monthly series cannot see.",
    ],
    source: { label: "Rebalancing policy on real regional equity", docPath: "docs/research/rebalancing-policy.md" },
  },
  {
    id: "exp-004-trend-index",
    number: "004",
    title: "What a trend sleeve adds to a portfolio that already exists",
    question:
      "Does a 15% time-series-momentum sleeve raise a passive portfolio's certainty-equivalent return against a risk-matched increase in cash?",
    kind: "exploratory",
    runState: "synthesised",
    status: "rejected",
    statusNote:
      "Rejected under the absolute reading of its clause (d), as frozen. Under the relative reading, which Experiment 008 judges better justified, the verdict is unresolved. Unresolved is not a promotion.",
    verdict:
      "The sleeve added +1.342 pp/yr of certainty equivalent over a risk-matched comparator, and survived every hostile test including removal of its best crisis. It then fired its own falsifier: a replica built only from a static and a volatility-scaled market position, with the intercept stripped out, reproduces 44% of that. The standalone series decayed enormously after publication while the marginal benefit barely moved, which is the finding underneath the verdict.",
    keyNumbers: [
      {
        label: "Marginal certainty equivalent, full period",
        value: "+1.342",
        unit: "pp/yr",
        interval: "[+0.759, +1.916]",
      },
      {
        label: "Post-publication, 2012–2025",
        value: "+1.011",
        unit: "pp/yr",
        interval: "[−0.175, +2.165]",
        note: "contains zero and fails Holm",
      },
      { label: "Static + volatility replica", value: "+0.586", unit: "pp/yr", note: "43.7% of the sleeve" },
      { label: "Sleeve's margin over its own replica", value: "+0.756", unit: "pp/yr" },
      { label: "Standalone Sharpe, across three eras", value: "1.34 → 0.83 → 0.18" },
      { label: "Standalone geometric return", value: "19.4% → 12.3% → 3.1%", unit: "/yr" },
      { label: "Crisis correlation to the passive portfolio", value: "−0.59", note: "−0.17 over all months" },
      { label: "Downside beta", value: "−0.67" },
      {
        label: "Vendor's stated cost basis",
        value: "none",
        note: "no fee, transaction-cost, slippage or financing assumption appears anywhere in the archived workbook",
      },
      {
        label: "Comparable CTA survivorship and backfill distortion",
        value: "7.7",
        unit: "pp/yr",
        note: "larger than the strategy's entire gross premium",
      },
    ],
    whyItMatters:
      "It is the cleanest example in the repository of a benchmark choosing the answer, and of a falsifier written in prose rather than as an expression producing two defensible opposite verdicts from the same two numbers.",
    whatWouldChangeIt: [
      "A multi-asset attribution. The current one can only see the US equity market while the sleeve trades 58 instruments, so its 12.6% R-squared is a lower bound on what simple exposures explain.",
      "A contract-level test of the volatility scaling, which no public aggregate can support.",
      "A vendor cost basis, which the workbook does not state anywhere.",
    ],
    source: {
      label: "Trend: the index, the products, and an ambiguous clause",
      docPath: "docs/research/trend-marginal-value.md",
      anchor: "experiment-004--the-index",
    },
  },
  {
    id: "exp-005-regional-replication",
    number: "005",
    title: "The regional replication of value, profitability and investment",
    question:
      "When the United States window is too short to sign a premium, do independent regions supply the sample size it lacks?",
    kind: "exploratory",
    runState: "synthesised",
    status: "exploratory",
    statusNote:
      "The family's terminal ledger status. Per factor: HML advanced to exploratory, RMW and CMA are rejected and closed on public data.",
    verdict:
      "Both branches of the falsifier fired, which is what it was designed for. Value cleared every clause on a pooled +4.74 pp/yr. Profitability and investment did not, and the experiment measured why: pooling three correlated regions bought far less than three regions' worth of evidence, leaving detection thresholds above the repository's own materiality bar. That closes those two on public data permanently rather than asking for another pass.",
    keyNumbers: [
      { label: "Pooled HML, post-publication", value: "+4.74", unit: "pp/yr", interval: "[+1.46, +8.10]" },
      {
        label: "Pooled RMW",
        value: "+2.53",
        unit: "pp/yr",
        interval: "[+1.07, +3.96]",
        note: "below its own 2.62 detection threshold",
      },
      { label: "Pooled CMA", value: "+0.20", unit: "pp/yr", interval: "[−2.57, +3.44]" },
      {
        label: "HML effective regions",
        value: "1.49",
        interval: "[1.39, 1.68]",
        note: "1,152 naive region-months bought 573",
      },
      {
        label: "RMW effective regions",
        value: "2.26",
        interval: "[2.01, 2.65]",
        note: "the least correlated, so pooling helped it most",
      },
      { label: "HML by region", value: "US +1.57, developed ex-US +5.07, emerging +7.58", unit: "pp/yr" },
      {
        label: "Pool excluding the US entirely",
        value: "+6.33",
        unit: "pp/yr",
        interval: "[+3.19, +9.58]",
        note: "stronger without the US",
      },
      {
        label: "Naive independent resampling",
        value: "narrows intervals ~1.5×",
        note: "in HML's recent decade it manufactures a significant result the valid procedure cannot support",
      },
    ],
    whyItMatters:
      "It replaced an assumption with a measurement: pooling n correlated series does not add n times the evidence, and this is the machinery that says how much it does add.",
    whatWouldChangeIt: [
      "For RMW and CMA, roughly a further decade of out-of-sample months — about 245, ending near 2035 — since the detection threshold scales as one over the square root of the sample.",
      "A genuinely independent, non-French construction of the same economic factor on a different universe and a different vendor's accounting data.",
      "A regional sorted-portfolio source supporting a materially lower-variance estimator of the same premium.",
    ],
    source: { ...persistence, anchor: "experiment-005--the-regional-replication" },
  },
  {
    id: "exp-006-regional-momentum",
    number: "006",
    title: "Regional momentum",
    question: "Does the momentum premium hold outside the United States, on the same frozen eras and the same design?",
    kind: "exploratory",
    runState: "synthesised",
    status: "exploratory",
    statusNote:
      "UMD advanced under branch (a). Branch (b) was never reached, and it would have fired: the pooled detection threshold is 4.98 pp/yr against a 2.0 materiality bar.",
    verdict:
      "Momentum is the largest gross premium measured anywhere in this repository, pooled +7.33 pp/yr and positive in all three regions. It is also the worst-diversified: three regions are worth 1.33 independent looks, and all three lost their worst calendar year in 2009. A tilt split across regions buys no protection in the one episode where a holder would want it.",
    keyNumbers: [
      { label: "Pooled UMD, post-publication", value: "+7.33", unit: "pp/yr", interval: "[+3.92, +10.31]" },
      {
        label: "Pooled detection threshold",
        value: "4.98",
        unit: "pp/yr",
        interval: "[3.87, 5.98]",
        note: "the worst in this repository",
      },
      {
        label: "Effective regions",
        value: "1.33",
        note: "512 effective months out of 1,152 naive; the fewest measured here",
      },
      { label: "Mean cross-region correlation", value: "0.66" },
      { label: "UMD by region", value: "US +4.19, developed ex-US +8.35, emerging +9.44", unit: "pp/yr" },
      { label: "US recent decade", value: "+0.37", unit: "pp/yr", note: "against +5.75 and +10.33 abroad" },
      { label: "Worst shared year, 2009", value: "US −52.9%, developed ex-US −36.8%, emerging −28.9%" },
      {
        label: "All three regions in their own worst decile",
        value: "3.65% of months",
        note: "against 0.1% under independence, a factor of 36",
      },
      {
        label: "Assumed cost of the academic construction",
        value: "3.30–18.67",
        unit: "pp/yr",
        note: "belongs to a monthly-rebalanced long-short spread and must never be applied to a fund",
      },
    ],
    whyItMatters:
      "It reversed the earlier answer that momentum was the weakest factor here. The case against a momentum sleeve is now entirely about turnover, product shelf and a shared crash, not about the premium.",
    whatWouldChangeIt: [
      "A measured one-sided monthly turnover below 50% for a long-only momentum fund. The 27.5–91.5% figure belongs to the academic spread, not to any product.",
      "A second investable product, since the entire retail shelf clearing a $1bn and 0.60% screen is MTUM.",
      "A long-only capture fraction measured from a fund's holdings rather than from research portfolios.",
    ],
    source: { ...persistence, anchor: "experiment-006--regional-momentum" },
  },
  {
    id: "exp-007-longonly-capture",
    number: "007",
    title: "The long-only capture fraction",
    question: "What fraction of a long-short factor premium does a long-only tilt actually deliver?",
    kind: "exploratory",
    runState: "synthesised",
    status: "rejected",
    statusNote:
      "What was rejected is not the capture fraction. It is the premise that there is one: five defensible benchmarks span 0.846, against a 0.30 threshold frozen in advance as the point at which a multiplier stops being a multiplier. A later correction went further: the fraction is itself an HML loading, so it may not multiply one.",
    verdict:
      "Against a size-neutral benchmark the capture is about 0.520, in the US, in developed ex-US, in emerging markets, and for momentum as well as value — a structural one half, because a long leg is one half of a symmetric spread. Against the capitalisation-weighted market the same tilt reads 0.958, and the whole difference is a size premium wearing a value label. Regress that same spread on the factors and 94% of the 0.520 is simply its HML coefficient, 0.4891, so every chain of the form loading × capture discounted one exposure twice and understated a long-only value tilt by roughly a factor of two.",
    keyNumbers: [
      {
        label: "Size-neutral value capture",
        value: "0.520",
        interval: "[0.434, 0.722]",
        note: "1963-07…2025-12, 750 months, gross",
      },
      { label: "Spread across five defensible benchmarks", value: "0.846" },
      {
        label: "HML loading of the same size-neutral spread",
        value: "0.4891",
        note: "94% of the 0.520 capture; identity holds to 4.4e-16, so the two may not be multiplied",
      },
      { label: "Against the capitalisation-weighted market", value: "0.958", interval: "[0.586, 1.662]" },
      {
        label: "Small-value half against the market",
        value: "1.287",
        interval: "[0.603, 2.788]",
        note: "more than the whole spread, from one leg of it",
      },
      { label: "Momentum, size-neutral", value: "0.501", interval: "[0.438, 0.565]" },
      {
        label: "Size premium, smallest minus largest quintile",
        value: "+1.91",
        unit: "pp/yr",
        interval: "[−1.90, +6.00]",
        note: "against its own 4.73 detection threshold; +0.41 post-publication",
      },
      {
        label: "Reconstruction residual",
        value: "0.005",
        unit: "pp/mo",
        note: "half of the last printed digit, over 1,194 months",
      },
      {
        label: "The academic small-value corner at 2025-12",
        value: "21.24% of listed firms, 0.236% of market capitalisation",
      },
      {
        label: "US total market, 1963-07…2025-12",
        value: "10.80%/yr geometric at 15.40% volatility, −50.3% max drawdown, 72 months under water",
      },
    ],
    whyItMatters:
      "It replaced the edge budget's assumed 0.40 with a measurement, showed the assumption was under-specified rather than wrong, and then removed the term from the budget altogether. A factor line is weight × (fund loading − incumbent loading) × premium − cost, and it carries no capture at all.",
    whatWouldChangeIt: [
      "A fund's delivered capture, which needs holdings rather than returns, and is Experiment 002's data rather than this one's. It now matters less, since a budget needs the loading and not the ratio.",
      "Evidence that a loading estimated on 36 to 72 months forecasts the next 36 to 72, which nothing here tests.",
    ],
    source: { label: "The long-only capture fraction", docPath: "docs/research/long-only-capture.md" },
  },
  {
    id: "exp-008-managed-futures-products",
    number: "008",
    title: "The managed-futures ETF audit",
    question:
      "Do the US-listed managed-futures ETFs an investor can buy deliver the AQR index's exposure, at a tracking difference their fee can account for?",
    kind: "exploratory",
    runState: "synthesised",
    status: "exploratory",
    statusNote:
      "DBMF reached exploratory; CTA, FMF, KMLM and WTMF are rejected against the frozen 0.50 loading bar. Decision 0002 caps the whole audit at exploratory.",
    verdict:
      "One product on the listed shelf delivers the exposure, and it is the one that sells replication. DBMF loads +0.671 with an interval clear of the bar, holds it across every split the window supports, and trailed a cost-free vendor index by less than it charges. The tax the funds distribute is two to three times their fee, and it is zero inside a shelter — but that is a fact about a pro-rata fund, not about the exposure: the same trend notional through a return-stacked wrapper carries 0.32 pp/yr, of which 4.5 bp is incremental over the equity fund inside it. The wrapper decides more than the account does.",
    keyNumbers: [
      {
        label: "DBMF loading on the AQR index",
        value: "+0.671",
        interval: "[+0.513, +0.829]",
        note: "54 months; halves +0.59 then +0.73",
      },
      {
        label: "The other four",
        value: "CTA +0.475, FMF +0.303, KMLM +0.245, WTMF +0.099",
        note: "against a frozen 0.50 bar",
      },
      { label: "DBMF tracking difference", value: "−0.48", unit: "pp/yr", note: "against an 0.85% fee" },
      { label: "Tracking errors across the shelf", value: "9.66–15.79", unit: "pp/yr" },
      {
        label: "Median minimum detectable alpha",
        value: "12.75",
        unit: "pp/yr",
        note: "larger than any plausible true value",
      },
      { label: "Alpha tests surviving any correction", value: "0 of 15" },
      {
        label: "Distribution tax drag",
        value: "0.76–2.53",
        unit: "pp/yr",
        note: "DBMF 2.09, which is 2.5× its own fee; zero in a tax-deferred account",
      },
      {
        label: "2019 managed-futures shelf gone by 2025",
        value: "54.2%",
        note: "13 of 24 series, 2.99 bn USD; a lower bound",
      },
    ],
    whyItMatters:
      "Experiment 004 evaluated an index and its verdict was for a time repeated as though it applied to these products. It did not, and testing them reached a different answer for one of them.",
    whatWouldChangeIt: [
      'A per-fund benchmark built from each fund\'s own stated universe, which would separate "does not deliver trend" from "does not deliver this trend".',
      "A second product with a loading at or above 0.50, which would remove DBMF's single-product risk.",
      "A licensed total-return source and a real cost model, since the window is 46 to 78 months of unaudited self-reported returns with no independent corroboration.",
    ],
    source: {
      label: "Trend: the index, the products, and an ambiguous clause",
      docPath: "docs/research/trend-marginal-value.md",
      anchor: "experiment-008--the-products",
    },
  },
  {
    id: "exp-009-exus-factor-products",
    number: "009",
    title: "Ex-US factor product exposure and implementation audit",
    question:
      "Do ex-US factor products deliver their intended exposure against their own region's factor panel, at a cost that leaves it worth buying?",
    kind: "exploratory",
    runState: "synthesised",
    status: "exploratory",
    statusNote:
      "Exploratory by decision rather than by outcome. Decision 0002 caps all fund-level work there, and a window beginning in 2019 caps it again. This may not promote a sleeve, and the per-fund statuses below permit these products to be used as implementation proxies in a later experiment and permit nothing else.",
    verdict:
      "This is the missing half of Experiment 002, and the exposure is delivered. That audit's exclusion pattern removed every international, global, emerging, developed and ex-US series, while Experiments 005 and 007 put nearly all of the value premium's measurable weight outside the United States — so the repository had audited products where the premium is weakest and none where it is strongest. Of 25 funds with enough filed history, 12 reached exploratory, 8 were rejected and 5 are unresolved. Every one of the twelve is developed ex-US; no emerging-market product reached exploratory at all.",
    keyNumbers: [
      { label: "Series screened, of which 26 passed and 25 had enough history", value: "537" },
      { label: "Reaching exploratory, all of them developed ex-US", value: "12 of 25" },
      { label: "Value premium by region", value: "US +1.57, developed ex-US +5.07, emerging +7.58", unit: "pp/yr" },
      {
        label: "Funds below the loading bar on the US panel instead of their own region's",
        value: "16 of 25",
        note: "Against 5 on the correct regional panel. A published ex-US loading without its panel named is not a number.",
      },
      {
        label: "Rejections decided by cost rather than by exposure",
        value: "5 of 8",
        note: "Clause (c): the fund lost more to an in-sample fitted combination of cheap ex-US funds than its fee premium explains. The replication has look-ahead, so read it as a deliberately hard test rather than as a verdict on the manager.",
      },
    ],
    whyItMatters:
      "It is the single largest gap between where a premium was measured and where a product was tested, and closing it needed no purchase. It also shows the regional panel is not a refinement but the thing that decides the verdict.",
    whatWouldChangeIt: [
      "An emerging-market product with a long enough window: both emerging value funds are unresolved on 44 and 51 months, and their point estimates are positive.",
      "A method that separates foreign withholding from index-construction differences. This one could not bound the drag at all, because VEA beat its own region's benchmark while VTI trailed the US one — a difference of +0.866 pp/yr in the wrong direction.",
    ],
    source: {
      label: "Frozen specification, exp_009_exus_factor_products.yaml",
      docPath: "research/experiments/exp_009_exus_factor_products.yaml",
    },
  },
  {
    id: "exp-013-us-products-union-frame",
    number: "013",
    title: "The US factor product audit, on a frame that can see the shelf",
    question:
      "How much of Experiment 002's conclusion was a property of the one quarterly filing its census frame happened to contain?",
    kind: "exploratory",
    runState: "synthesised",
    status: "exploratory",
    statusNote:
      "Exploratory by decision rather than by outcome: decision 0002 caps all fund-level work there. Forty-eight products reached the per-fund status exploratory, which permits use as an implementation proxy in a later experiment and nothing else. Nothing here is promoted and no residual return is claimed.",
    verdict:
      "Most of it. Form N-PORT is filed on each fund's own fiscal calendar and public reporting begins with periods ending 2019-09-30, so the 2019Q4 census carries no fund with an August fiscal year — Schwab's equity range, Vanguard's ETF-only trusts, Invesco's S&P factor range and Avantis among them — and the 2016 inception cutoff then removed every product that launched later. Experiment 002 could see 44 US factor products; the union of the 2019Q4 and 2025Q4 censuses contains 109. Two criteria moved and nothing else, and all 44 of the original funds reproduce to zero difference in loading, alpha, shortfall and status.",
    keyNumbers: [
      {
        label: "Screened to audited",
        value: "14,742 → 3,169 → 116 → 109",
        note: "union of the two censuses; Experiment 002 reached 44",
      },
      { label: "Statuses", value: "48 exploratory, 48 rejected, 13 unresolved" },
      {
        label: "Products the corrected frame adds",
        value: "65",
        note: "42 absent from the 2019Q4 census, 23 excluded by a criterion that moved. 33 of them reach exploratory",
      },
      {
        label: "Median shortfall to the cheap replication",
        value: "+0.53 inside the old frame, −0.48 outside it",
        unit: "pp/yr",
        note: "Positive means the product lost to an in-sample fitted mix of VTI, VUG, VTV and VB. The comparator has look-ahead, so a negative figure is the stronger evidence: the mix had the whole window to fit itself and still lost",
      },
      {
        label: "Clause (c) rejections",
        value: "35 of 109",
        note: "22 of 44 on Experiment 002's frame; 13 of the 65 funds it could not see",
      },
      { label: "Loadings surviving correction", value: "96 of 109", note: "Benjamini-Hochberg at 0.10" },
      {
        label: "Alpha tests surviving Holm",
        value: "5 of 327",
        note: "all negative. Sixteen raw alphas exceed what their own window could detect at 80% power and every one of the sixteen is negative",
      },
      {
        label: "Median minimum detectable alpha",
        value: "5.01",
        unit: "pp/yr",
        note: "against a cross-sectional dispersion of true alpha near 1.25",
      },
      {
        label: "AVUV, the largest product the old frame missed",
        value: "+0.537",
        interval: "[+0.43, +0.64]",
        note: "HML loading over all 72 months, sign-adjusted for its mandate; it beat its in-sample cheap replication by 4.92 pp/yr and its alpha of +0.39 sits far inside a 3.64 detection threshold",
      },
    ],
    whyItMatters:
      "It is the only place in this repository where a published conclusion was overturned by asking what a data file physically contains rather than by re-reading a result. The shortlist of products a later experiment may test went from fifteen index trackers to forty-eight, and now includes every systematic value and small-value product on the US shelf.",
    whatWouldChangeIt: [
      "A replication whose weights are fitted on a prior window. Clause (c) separates the 48 exploratory products from the 48 rejected ones and it is still decided with hindsight.",
      "A comparator basis containing a small-value building block. The frozen basis has none, so a small-value product is scored against a mix that cannot express it.",
      "A licensed, survivorship-free total-return source from at least 2003. Nothing here makes the alpha column measurable and a longer window is the only thing that would.",
    ],
    source: {
      label: "Investable factor products",
      docPath: "docs/research/factor-products.md",
      anchor: "the-us-shelf-on-the-corrected-frame",
    },
  },
  {
    id: "exp-010-marginal-sleeve-value",
    number: "010",
    title: "Marginal sleeve value inside a real portfolio",
    question:
      "Does adding a small weight to an existing portfolio raise its growth rate once the diversification credit the standalone chain omits is counted?",
    kind: "exploratory",
    runState: "synthesised",
    status: "rejected",
    statusNote:
      "Two specifications judged the same data and added no trials between them: one on a certainty equivalent at gamma = 3, one on geometric growth. Growth decides, and that is what moved the family from unresolved to rejected. Every input is a paper portfolio, a vendor series or a modelled proxy, and the weights are evaluated in sample, so the family is capped at exploratory whatever it had found.",
    verdict:
      "Every sleeve except trend had been judged by a standalone chain, which sets the covariance term to zero by construction. Judged inside a portfolio instead, no sleeve survives, and the reason is a bound rather than a measurement: the diversification credit has a ceiling set by the base portfolio's own variance, and the ceiling is below the bar. The portfolio view rescues nothing the standalone chain dismissed, and against a 60/40 base it strengthens six of those dismissals instead. The bound and what it means for a trend sleeve are on the portfolio page.",
    keyNumbers: [
      { label: "Sleeves tested", value: "10 in the Holm family, plus a modelled proxy and a control" },
      { label: "Sleeves surviving Holm at 0.05", value: "0 of 10" },
      {
        label: "Sleeves clearing the bar on the certainty equivalent, then failing it on growth",
        value: "6 of 7",
      },
      {
        label: "Sample",
        value: "420 months",
        note: "1991-01 to 2025-12, 35 whole calendar years, one lead month read and never reported",
      },
    ],
    whyItMatters:
      "It bounds what the portfolio-level view can rescue, and a later test of gold shows the bound is reachable and still not enough. A zero-beta asset takes the entire credit and remains 0.10 pp/yr behind: the credit is 2.17 pp/yr per unit of weight against a standalone shortfall of 2.95, and both scale with the weight, so holding more cannot close the gap. The ceiling on the credit, and what it means for a trend or momentum sleeve, is set out on the portfolio page.",
    whatWouldChangeIt: [
      "A funding rule that finances the sleeve instead of selling the base, and a leverage-matched control on every arm. Gold was landed and tested on 2026-08-17: it lands exactly on the credit ceiling with a beta of zero and still fails, so the ceiling was never the binding term. Re-run under overlay funding its marginal contribution changes sign, from −0.40 to +0.18 pp/yr — a swing of 0.58 from the funding rule alone, against a bar of 0.30 — and it still clears neither the bar nor its own detection floor.",
      "An investable bond total-return history, which would replace the modelled duration proxy that clause (u5) forbids from resolving anything.",
      "A base portfolio whose volatility is high enough for the ceiling to clear the bar, which is the opposite of what most readers would want to hold.",
    ],
    source: {
      label: "What a sleeve is worth inside a portfolio, rather than on its own",
      docPath: "docs/research/marginal-sleeve-value.md",
    },
  },
];

/**
 * The append-only run record, counted rather than transcribed. The framework page
 * verifies these directly from `research/ledger.jsonl`.
 */
export const ledgerSummary = {
  entries: 128,
  runs: 45,
  distinctSpecifications: 25,
  experimentFamilies: 21,
  runsRecordingResultsViewed: 37,
  runsConsumingTheFinalHoldout: 0,
  terminalOutcomes: [
    {
      status: "unresolved" as const,
      runs: 9,
      which:
        "Phase 1; Experiment 001; Experiment 007's superseded specification; Experiment 010, three executions of one specification; Experiment 011; Experiment 012, two executions of one question",
    },
    {
      status: "rejected" as const,
      runs: 9,
      which:
        "Experiment 003; Experiment 004, five executions of one specification; Experiment 007; Experiment 010b, two executions",
    },
    {
      status: "exploratory" as const,
      runs: 19,
      which:
        "Experiments 002, 008 and 009, three executions each; Experiments 005 and 006; Experiment 013, two executions; Experiments 014 and 015; Experiment 016 and its three follow-ons, 016b, 016c and 016d",
    },
  ],
  noTerminalStatus: {
    runs: 8,
    which:
      "3 failed — a parser table-name error, a clause-(d) verification guard refusing a run, and a NaN that is not JSON-compliant — and 5 abandoned",
  },
  asOf: asOf("2026-08-22"),
  note: "Twenty-five, not forty-five, is the number a deflated-Sharpe trial count starts from: repeated executions of one specification are not independent hypotheses. Twenty-five is itself an upper bound, because Experiment 010b re-judges data Experiment 010 had already spent, because Experiments 013, 014 and 015 re-run an earlier falsifier on data it had already spent rather than asking a new question, and because Experiments 016b, 016c and 016d re-score 016's arms on the identical panel — 016b adding four arms chosen after seeing its results, and 016c and 016d changing no arm at all and only sweeping an input.",
  source: {
    label: "Portfolio edge research framework, the ledger counted rather than described",
    docPath: "docs/research/portfolio-edge-research-framework.md",
    anchor: "the-ledger-counted-rather-than-described",
  },
} as const;

/** Nothing in this repository reached this rung, and the copy must never imply otherwise. */
export const highestStatusReached: EvidenceStatus = "exploratory";
