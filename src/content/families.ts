import type { AsOf, CertaintyClass, Citation, EvidenceStatus } from "~/content/types";
import { asOf } from "~/content/types";

/**
 * The research library, organised by what a strategy claims rather than by which file
 * happens to hold it.
 *
 * Each family answers the same ten questions in the same order, because the interesting
 * comparison between two return engines is not which sounds better — it is which one
 * survives the same interrogation. `headline` is the number a reader should leave with;
 * `strength` is this repository's own status word for it, never a grade invented here.
 */

export interface FamilyFailure {
  readonly title: string;
  readonly detail: string;
}

export interface StrategyFamily {
  readonly slug: string;
  readonly name: string;
  /** One sentence. What the strategy claims, not what it is called. */
  readonly claim: string;
  /** The short answer, near the top of the page. Two or three sentences at most. */
  readonly inPractice: string;
  readonly mechanism: string;
  /**
   * What kind of thing this family's return is. It governs the wording: a risk premium
   * may never be called an edge, and a contractual line is not graded on the experiment
   * ladder at all — which is why `status` is nullable rather than forced to a word that
   * would overstate it.
   */
  readonly certainty: CertaintyClass;
  readonly status: EvidenceStatus | null;
  /** Why the status is that word and not a neighbouring one. */
  readonly statusReason: string;
  readonly headline: {
    readonly value: string;
    readonly label: string;
    readonly interval?: string;
    readonly note?: string;
  };
  readonly evidenceFor: readonly string[];
  readonly evidenceAgainst: readonly string[];
  readonly failureModes: readonly FamilyFailure[];
  readonly implementation: string;
  readonly cost: string;
  /** What it overlaps with, and what it is genuinely distinct from. */
  readonly overlap: string;
  readonly roleInPortfolio: string;
  /** Portfolio ids from `src/content/portfolios.ts`. */
  readonly portfolios: readonly string[];
  readonly tickers: readonly string[];
  readonly sources: readonly Citation[];
  readonly asOf: AsOf;
}

const persistence: Citation = { label: "Factor persistence", docPath: "docs/research/factor-persistence.md" };
const products: Citation = { label: "The factor-product audit", docPath: "docs/research/factor-products.md" };
const capture: Citation = { label: "Long-only capture", docPath: "docs/research/long-only-capture.md" };
const recommendation: Citation = {
  label: "The recommended portfolio",
  docPath: "docs/research/portfolio-recommendation.md",
};
const trendValue: Citation = { label: "The marginal value of trend", docPath: "docs/research/trend-marginal-value.md" };
const liveTrend: Citation = { label: "Live managed futures", docPath: "docs/research/live-managed-futures.md" };
const capital: Citation = {
  label: "Capital efficiency and breadth",
  docPath: "docs/research/capital-efficiency-and-breadth.md",
};
const structural: Citation = {
  label: "Structural and tax edges",
  docPath: "docs/research/structural-and-tax-edges.md",
};
const decomposition: Citation = {
  label: "Where outperformance can come from",
  docPath: "docs/research/expected-edge-decomposition.md",
};
const rebalancingDoc: Citation = { label: "Rebalancing policy", docPath: "docs/research/rebalancing-policy.md" };
const equityShare: Citation = {
  label: "Setting the equity share",
  docPath: "docs/research/setting-the-equity-share.md",
};
const alternatives: Citation = {
  label: "The alternative-sleeves audit",
  docPath: "docs/research/alternative-sleeves-audit.md",
};
const marginal: Citation = { label: "Marginal sleeve value", docPath: "docs/research/marginal-sleeve-value.md" };
const closedPremia: Citation = {
  label: "Decision 0005 — RMW and CMA closed on public data",
  docPath: "docs/decisions/0005-factor-premia-closed-on-public-data.md",
};

const READ = asOf("2026-08-17");

export const families: readonly StrategyFamily[] = [
  {
    slug: "structural-and-tax",
    name: "Cost, wrapper and tax",
    claim:
      "Fee, fund structure, lot method and account placement are worth about 109 bp a year, and their sign is known in advance.",
    inPractice:
      "This is the only part of the site where the arithmetic is an accounting identity rather than a bet. If you hold an expensive active fund, in one account, on average-cost lots, roughly 109 bp a year is available for work you can finish in an afternoon. If you already hold cheap index funds in a single tax-deferred account, the honest figure for you is close to zero.",
    mechanism:
      "Four statutes and one accounting rule do the work: §852(b)(6) lets an ETF push appreciated stock out in kind rather than selling it, §853 passes foreign tax through to the shareholder, §904 limits what can be credited, specific-lot identification decides which gain is realised, and §1014 resets basis at death. None of them requires a view on any market.",
    certainty: "contractual",
    status: null,
    statusReason:
      "Contractual, and therefore not on the experiment ladder at all — there is no hypothesis here to promote or reject. The lines are measured across 25 funds and 110 regulatory filings rather than estimated, and each is an arithmetic consequence of a filed number. That says nothing about whether the conditions hold for your account.",
    headline: {
      value: "109 bp/yr",
      label: "Against the portfolio you would otherwise have owned",
      interval: "outer bound 4–270",
      note: "About 99% confident inside twelve months at the assumed 46 bp of tracking error. Against a cheap index the same work is 46 bp against 313 bp, a 0.792 chance of being ahead after thirty years.",
    },
    evidenceFor: [
      "A fund's cost is fee less securities lending, and the two rankings differ. IEMG costs less to own than VWO at a 50% higher fee; BND is the dearest aggregate bond fund audited because it is the only one that does not lend at all; SPY runs 9.45 bp because a unit investment trust cannot lend.",
      "Every one of the 25 audited core funds distributed zero capital gains in every fiscal year on file.",
      "The confidence horizon is short. At 46 bp of tracking error a 109 bp edge is about 90% established in three and a half months.",
    ],
    evidenceAgainst: [
      "Only the 49 bp fee line is unconditional. Harvesting needs a taxable account with gains, placement needs more than one account type, and the wrapper line needs you to be leaving an active mutual fund.",
      "The 46 bp tracking error is assumed rather than measured, and the components are not independent. Every horizon on the page inherits that.",
      "The emerging-market withholding input, 9.853%, is below ten of eleven funds' filed rates of 9.12–14.23%.",
    ],
    failureModes: [
      {
        title: "The wrapper advantage is closing",
        detail:
          "The +23 bp ETF-versus-mutual-fund line depends on active managers not having an ETF share class. There are now 94 SEC orders and 89 filings naming one, against two before the first order, from fourteen registrants — though only nine funds have actually listed.",
      },
      {
        title: "Turnover eats it",
        detail:
          "A taxable account faces a horizon-free 162 bp/yr hurdle on realising gains, 84 bp at thirty years. Realising 10% of standing gain a year already costs 41.5 of that 84, so 'low turnover' is not by itself a defence.",
      },
      {
        title: "It is a per-reader number",
        detail:
          "The budget is sized for one stated reference investor. Quoting a per-sleeve figure as a portfolio figure is the standard way tax numbers get inflated, and this repository has made that error itself.",
      },
    ],
    implementation:
      "Move to funds whose fee less lending is lowest, hold them in an ETF wrapper, set specific-lot identification once at the brokerage, and place each sleeve by computed priority rather than by rule of thumb.",
    cost: "The whole fund-selection decision inside a cheap four-fund construction is worth 0.60 bp/yr — 1.36 against 0.76 — against an 84 bp/yr hurdle for the turnover needed to capture it.",
    overlap:
      "It overlaps with nothing else on this site, which is the point. It is the one line that adds to a factor tilt rather than competing with it — as long as the two are not quoted against different benchmarks and then summed.",
    roleInPortfolio:
      "The first thing to do and the last thing to give up. It changes no holding you need to believe in.",
    portfolios: ["disciplined"],
    tickers: ["VTI", "VEA", "IEMG", "BND", "SPY", "VWO"],
    sources: [structural, decomposition],
    asOf: READ,
  },
  {
    slug: "value",
    name: "Value",
    claim: "Cheap stocks have earned more than expensive ones, and a long-only fund can capture part of the spread.",
    inPractice:
      "Value is the only factor premium in this repository that advanced on its own strength. Pooled across three regions it measures +4.74 pp/yr against a detection floor of 3.35. But that figure is a gross long-short spread you cannot buy, and what reaches a shareholder is `weight × (fund loading − incumbent loading) × premium − cost`. At a 20% weight in a US large-value fund that is about 24 bp a year against 135 bp of tracking error.",
    mechanism:
      "Either a risk story — cheap firms are distressed and their cash flows are more exposed to bad states — or a behavioural one, that investors over-extrapolate growth. This repository does not adjudicate between them, and the distinction matters only for whether the premium should survive being known.",
    certainty: "risk-premium",
    status: "exploratory",
    statusReason:
      "The premium clears its own detection floor pooled across three regions and survives Holm correction and the removal of its best year. The missing promotion clause is a prior-window replication that no experiment here has fitted.",
    headline: {
      value: "+4.74 pp/yr",
      label: "HML pooled post-publication, three regions, 384 months",
      interval: "[+1.46, +8.10] against a 3.35 detection floor",
      note: "Gross, long-short and not investable. 1.49 effective regions after correlation, average pairwise 0.52.",
    },
    evidenceFor: [
      "Positive in all three regions post-publication: +1.57 US, +5.07 developed ex-US, +7.58 emerging.",
      "Nine systematic value and small-value products keep their `exploratory` status under every comparator basis tested. The exposure they sell is genuinely delivered.",
      "The developed ex-US tilt is the only line in this repository whose thirty-year detection floor, 21.6 bp, sits below its own edge of 27.1 bp.",
    ],
    evidenceAgainst: [
      "The US leg alone is +1.57 pp/yr [−2.28, +5.54] against a 5.03 floor and survives no correction. On the US-only premium a 20% tilt's growth contribution is negative at every weight.",
      "The pooled figure is carried by the two non-US regions, with the largest leg in emerging markets, where shorting is hardest and the long-short construction least plausible.",
      "Four ex-US large-value funds read alphas of −2.2 to −4.1 pp/yr, and nobody here knows why. That is the largest open question in the product audit.",
    ],
    failureModes: [
      {
        title: "The capture double-count",
        detail:
          "A long-only fund's 'capture fraction' and its factor loading are the same quantity measured two ways — 94% of the 0.520 capture is the 0.4891 loading, an identity exact to 4.4 × 10⁻¹⁶. Multiplying them discounts one exposure twice, and doing so understated this repository's own value tilt by about a factor of two in five places. The code now raises rather than allowing it.",
      },
      {
        title: "A working lifetime may not settle it",
        detail:
          "At a 20% weight the thirty-year detection floor is 142 bp against a 43 bp edge. You would hold the tilt for thirty years and still not know.",
      },
      {
        title: "Small value is the worse trade",
        detail:
          "The size premium is +0.33 pp/yr against a 2.47 floor and is not signable on any panel, so a small-value fund's size leg is variance with no priced expectation. A large-value fund is ahead on both shelves — measured independently on each.",
      },
    ],
    implementation:
      "A long-only systematic value fund with a real loading and low turnover. AVLV delivers HML +0.322 at 15 bp and 7%/yr turnover; DFIV delivers +0.662 at 27 bp and 6%/yr on the developed ex-US panel. Both hold their status under every basis tested.",
    cost: "15 to 27 bp of fee, plus the trading implied by 6–7%/yr turnover. Neither fund has distributed a capital gain in the years on file.",
    overlap:
      "A value tilt overlaps heavily with the market it is drawn from: at a 20% weight the tracking error against the control is 135 bp on a portfolio whose own volatility is ten times that. It does not overlap with trend, and it overlaps with momentum negatively.",
    roleInPortfolio:
      "A sized bet, not a core. The two tilts this repository has priced sit at 20% and 8% of capital and together buy tens of basis points of expected edge for decades of tracking error.",
    portfolios: ["evidence-led", "candidate"],
    tickers: ["AVLV", "DFIV", "AVUV", "VBR", "IVLU", "AVES"],
    sources: [persistence, capture, products, recommendation],
    asOf: READ,
  },
  {
    slug: "momentum",
    name: "Momentum",
    claim: "Recent winners keep winning for long enough to trade.",
    inPractice:
      "Momentum has the largest gross premium in this repository — +7.33 pp/yr pooled — and is the clearest case of a real effect that implementation destroys. The one investable route audited here files 105% annual turnover, and cost takes 43% of the gross exposure. It is excluded from the reference portfolio on those grounds, not on the premium's.",
    mechanism:
      "Under-reaction to news followed by over-extrapolation, with the academic construction re-forming every month. The mechanism implies turnover, and the turnover is the problem.",
    certainty: "risk-premium",
    status: "exploratory",
    statusReason:
      "The premium clears its own floor pooled, so the effect is `exploratory`. The implementation is separately excluded, and those are two different findings that are frequently merged into one.",
    headline: {
      value: "+7.33 pp/yr",
      label: "UMD pooled post-publication, three regions",
      interval: "[+3.92, +10.31] against a 4.98 detection floor",
      note: "The worst detection floor measured anywhere in this repository.",
    },
    evidenceFor: [
      "Positive in every region post-publication: +4.19 US, +8.35 developed ex-US, +9.44 emerging.",
      "IDMO delivers UMD +0.540 [+0.39, +0.71] over 77 months and survives all seven comparator bases, on the one regional premium that clears its own floor.",
    ],
    evidenceAgainst: [
      "Three regions are worth 1.33 effective regions after correlation — the fewest measured anywhere here — with an average pairwise correlation of 0.66.",
      "All three regions lost their worst calendar year in the same year, 2009: US −52.9%, developed ex-US −36.8%, emerging −28.9%. All three sat in their own worst decile in 3.65% of months against 0.1% under independence.",
      "Academic turnover of 27.5–91.5% a month implies 3.30–18.67 pp/yr of cost against a 7.33 pp/yr gross premium. The US premium over the recent decade is +0.37 pp/yr.",
    ],
    failureModes: [
      {
        title: "The crash is the strategy",
        detail:
          "Momentum reverses violently after market rebounds, and it does so in every region at once. Diversifying momentum across regions buys almost nothing, which is exactly when a diversification argument is most often made for it.",
      },
      {
        title: "Turnover is the whole trade",
        detail:
          "IDMO's 105%/yr turnover costs about 1.72 pp/yr at a realistic impact multiple, taking 43% of a +4.47 pp/yr gross exposure. What survives is +2.53 pp/yr before anything else goes wrong.",
      },
      {
        title: "It carries a rejected factor",
        detail:
          "IDMO also loads −0.394 on CMA, a factor this repository has closed on public data. Part of what a momentum fund sells is exposure to a premium that cannot be signed.",
      },
    ],
    implementation:
      "IDMO at 25 bp is the cheapest audited route and is what causes IMTM at 30 bp to be rejected. MTUM is `rejected` on its shortfall against a cheap fitted combination.",
    cost: "25 bp of fee and roughly 1.7 pp/yr of trading at 105% turnover. In a taxable account the turnover meets the 162 bp/yr realisation hurdle head-on.",
    overlap:
      "Momentum is genuinely distinct from value — the two are negatively correlated — which is the strongest argument for holding it. It overlaps with trend conceptually and not statistically: trend is time-series, momentum is cross-sectional.",
    roleInPortfolio:
      "This repository excludes it. A reader who holds it anyway should size it knowing that its detection floor is the worst here and its regional diversification is close to imaginary.",
    portfolios: ["candidate"],
    tickers: ["IDMO", "MTUM", "SPMO", "IMTM"],
    sources: [persistence, products, recommendation],
    asOf: READ,
  },
  {
    slug: "trend",
    name: "Trend and managed futures",
    claim:
      "A diversified long/short futures book earns a positive expected return and is uncorrelated with equity, or negatively correlated when it matters.",
    inPractice:
      "Trend's correlation claim holds on three independent instruments. Its return claim does not resolve on any of them. Treat a trend sleeve as a risk-reduction decision that may also pay, and size it as though the mean were zero.",
    mechanism:
      "Futures markets under-react to slow-moving information, so a systematic long/short book across dozens of markets earns a premium — and because it can be short, its correlation to equity is near zero unconditionally and negative inside sustained equity declines.",
    certainty: "risk-premium",
    status: "unresolved",
    statusReason:
      "The vendor index is `rejected` against the falsifier frozen before the run, and `unresolved` on the reading the experiment itself judges better. DBMF is `exploratory`. Nothing is promoted, and the mean does not resolve on any instrument tried.",
    headline: {
      value: "+1.312 pp/yr",
      label: "Marginal growth of a 15% sleeve against a risk-matched cash comparator, 432 months",
      interval: "certainty equivalent +1.342 [+0.759, +1.916]",
      note: "Against a global equity core rather than cash, a 10% sleeve measures +0.258 pp/yr against a frozen 0.30 bar and is `rejected`.",
    },
    evidenceFor: [
      "The correlation holds three ways: −0.07 in the construction built here, −0.11 across 46 live funds, −0.08 from the vendor index. Inside crisis months it is −0.59, with a downside beta of −0.67.",
      "Marginal contribution in the four worst equity episodes: +2.11 pp in the dotcom decline, +2.44 in the financial crisis, +0.40 through Covid, +5.69 in the 2022 inflation drawdown.",
      "Live funds, net of their own fees, returned +2.84%/yr at Sharpe 0.329 over 78 months — ahead of the vendor index over the same window, which is the opposite of the usual survivorship story.",
    ],
    evidenceAgainst: [
      "Post-publication the sleeve measures +0.883 pp/yr with an interval containing zero, failing Holm correction.",
      "A static plus volatility-scaled replica delivers 44% of the benefit for none of the fee — which is the clause that fired the falsifier.",
      "The standalone index's Sharpe fell from 1.34 to 0.83 to 0.18 across three eras, and its geometric return from 19.4% to 3.1%.",
    ],
    failureModes: [
      {
        title: "The correlation is the whole case, and it is conditional",
        detail:
          "If the correlation inside equity drawdowns reaches +0.20 the result breaks entirely. That conditional correlation is measured on 53 crisis months — about 4.4 effective observations — and is unmeasured going forward.",
      },
      {
        title: "The funds do not survive",
        detail:
          "52% of the managed-futures ETFs listed in 2019 were gone by the end of 2025: a 10.7%/yr hazard, 43% at five years, 90% at twenty. Fifteen are listed now and eleven of them have never been tested here.",
      },
      {
        title: "Nobody discloses the financing cost",
        detail:
          "Every Return Stacked fund files 0.00% of interest expense because futures financing sits inside the contract price. The family's only disclosed financing rate is OBFR + 6.64%, and it more than doubled in one quarter.",
      },
    ],
    implementation:
      "DBMF is the only managed-futures ETF whose loading on the vendor index has been measured here: +0.671 [+0.513, +0.829] against a frozen 0.50 bar. CTA, KMLM, FMF and WTMF are all `rejected` against the same bar. RSST delivers the exposure as notional rather than capital, and its own loading has never been measured.",
    cost: "85 bp for DBMF and 99 bp all-in for RSST, plus a distribution tax drag of 2.09 pp/yr and 0.32 pp/yr respectively. Once the equity each displaces is subtracted, that is 143.9 bp against 4.5 bp — the wrapper, not the strategy, decides the tax outcome.",
    overlap:
      "Trend is the one engine on this site genuinely uncorrelated with equity. It overlaps with nothing else here, which is why its diversification credit survives even when its mean does not.",
    roleInPortfolio:
      "A sleeve sized by the drawdown it changes, not by the return it might add. The resampled probability that the overlay produces the deeper drawdown roughly doubles between 30% and 60% of notional, which sets a practical ceiling near 55%.",
    portfolios: ["candidate"],
    tickers: ["DBMF", "RSST", "KMLM", "CTA"],
    sources: [trendValue, liveTrend, capital, marginal],
    asOf: READ,
  },
  {
    slug: "capital-efficiency",
    name: "Capital efficiency and return stacking",
    claim:
      "Getting a diversifier as financed notional instead of selling equity to buy it lowers its hurdle, so a sleeve that would not be worth holding becomes worth holding.",
    inPractice:
      "This is the strongest closed-form result on the site and the one most often misread. The funding rule is worth about +2.44 pp/yr for a 100% equity base — and that number contains nothing whatever about the sleeve being stacked. What decides whether a particular wrapper delivers it is one quantity, `delta = (1 − b) / d`, and a fund with a half-sized equity base can be arithmetically worse than simply selling equity.",
    mechanism:
      "Buying a sleeve with capital forces you to sell base exposure, so the sleeve must clear `a_p − σ_p²(1 − β)`. Financing it as notional removes that sale, and the hurdle falls to `ρ σ_p σ_d`. The wrapper's structure enters exactly once, through `delta`.",
    certainty: "risk-premium",
    status: "exploratory",
    statusReason:
      "No specification was frozen before these numbers were examined, and the page says so. What is established is the closed form and the structural verification of individual funds from their own holdings — not a return.",
    headline: {
      value: "+2.44 pp/yr",
      label: "The funding-rule gap for a 100% equity base",
      note: "`a_p − σ_p² = σ_p²(L_p* − 1)`. It contains nothing about the sleeve. RSST's delta of −0.07 keeps 100% of it; a standalone managed-futures fund keeps 0%.",
    },
    evidenceFor: [
      "The result is closed-form and pinned by tests, not estimated from a window.",
      "RSST's structure is verified from its own Form N-PORT: 74.09% of net assets in an S&P 500 fund plus 33.1% in E-mini futures is 107.2% equity, with a government money fund at 16.04% as futures collateral.",
      "A 25% trend overlay improved the Sharpe ratio by +0.050 against +0.001 for the same base levered to identical volatility over 426 months. The overlay is not merely leverage.",
    ],
    evidenceAgainst: [
      "The cost stack binds before the correlation does: financing plus fee plus distribution-tax character runs about 1.4 pp/yr sheltered and 3.5 pp/yr taxable, against a post-publication trend excess return of roughly 1.8 pp/yr.",
      "No wrapper on the shelf quantifies its financing cost anywhere.",
      "NTSI and NTSE each lost to their own equity leg's index by about 3 pp/yr since 2021.",
    ],
    failureModes: [
      {
        title: "A wrapper can be worse than selling equity",
        detail:
          "At a 40% equity base with a 30% sleeve, delta is 2.0 and the wrapper is arithmetically worse than selling the equity outright to buy the sleeve. There is no name for this category in the marketing vocabulary, and a gross-notional figure cannot distinguish it from the good case.",
      },
      {
        title: "The growth optimum is unholdable",
        detail:
          "The growth-optimal trend overlay through RSST's delta is 3.04 units of notional. This repository refuses that number. The realised growth optimum on levered equity over a century is 2.2× at a −99.3% drawdown and 296 months under water.",
      },
      {
        title: "Leverage stays at zero",
        detail:
          "Decision 0004 holds leverage at zero and is unsuperseded. A portfolio using these wrappers departs from this repository's research deliberately.",
      },
    ],
    implementation:
      "Compute `delta = (1 − b) / d` for the fund and convert its fee to `fee / d` before comparing anything. RSST reads −0.07, RSSB −0.00, NTSX 0.144, GDE 0.182, and a standalone managed-futures fund 1.000. A wrapper whose base leg is not your own base gets a refusal, not a number.",
    cost: "99 bp all-in for RSST with no waiver and no recoupment clause. The financing cost is undisclosed and is the largest unpriced term in the whole family.",
    overlap:
      "Capital efficiency is not a return engine. It is a funding decision applied to whatever engine you already chose, and it is the reason a trend sleeve is cheaper to hold inside a stacked fund than beside one.",
    roleInPortfolio:
      "It changes how a sleeve is paid for, never whether the sleeve is worth owning. Answer that question first.",
    portfolios: ["candidate"],
    tickers: ["RSST", "RSSB", "NTSX", "GDE"],
    sources: [capital],
    asOf: READ,
  },
  {
    slug: "quality",
    name: "Quality and profitability",
    claim: "Profitable firms outperform unprofitable ones for their risk.",
    inPractice:
      "Closed. The pooled premium is +2.53 pp/yr against its own measured detection floor of 2.62 — the instrument cannot see an effect of the size being claimed. Reopening it needs about 245 months of additional data, around 2035, or a construction that is not Ken French's.",
    mechanism:
      "Profitable firms with the same book value have higher expected cash flows, so at the same price they must have higher expected returns. The logic is an identity; whether the market prices it away is the question.",
    certainty: "risk-premium",
    status: "rejected",
    statusReason:
      "The falsifier fired: the premium sits below the floor its own window could detect. `rejected` here means the test fired, never that the premium is zero — and decision 0005 records exactly that distinction.",
    headline: {
      value: "+2.53 pp/yr",
      label: "RMW pooled, against a 2.62 pp/yr detection floor",
      interval: "[+1.07, +3.96]",
      note: "The best pooled floor across twelve cells is 2.62 against a 2.0 pp/yr materiality threshold.",
    },
    evidenceFor: [
      "The pooled point estimate is positive and its interval excludes zero.",
      "The mechanism is an accounting identity rather than a behavioural story, which is a stronger prior than most factors have.",
    ],
    evidenceAgainst: [
      "62% of the US premium is the single year 2021. Dropping the pooled best year takes it to +1.79 pp/yr.",
      "Its volatility carries an unresolved ±5.09% band from the Phase 1 reproduction gate, so anything dividing by it inherits that.",
      "Nine quality products on the US shelf and not one reaches `exploratory`. The largest RMW loading found is +0.228.",
    ],
    failureModes: [
      {
        title: "An unsigned premium makes the product irrelevant",
        detail:
          "If the premium cannot be signed, how cheaply a fund delivers exposure to it does not matter. That is why the product side is closed alongside the premium.",
      },
      {
        title: "Adding data will not help soon",
        detail:
          "The detection floor falls with the square root of time. Reaching materiality needs roughly 245 more months, which is about 2035 — and only if the effect is at the top of its interval.",
      },
    ],
    implementation:
      "None recommended. QUAL and SPHQ are `rejected` and `unresolved` respectively; DUHP is `unresolved`.",
    cost: "Immaterial, because there is nothing to buy.",
    overlap:
      "Quality overlaps with value negatively — cheap firms are often unprofitable — which is why systematic value funds increasingly screen on profitability. That screen is inside AVLV and DFIV already.",
    roleInPortfolio: "None as a standalone sleeve. As a screen inside a value fund it is already present.",
    portfolios: [],
    tickers: ["QUAL", "SPHQ", "DUHP"],
    sources: [closedPremia, persistence, products],
    asOf: READ,
  },
  {
    slug: "alternatives",
    name: "Carry, credit and the alternatives shelf",
    claim:
      "Term, credit, insurance, volatility and merger spreads are separate return engines worth adding to an equity portfolio.",
    inPractice:
      "Almost all of it fails, and mostly on cost or on benchmark rather than on the premium. The recurring error is booking a distinct risk premium as an edge over an equity index: that is a benchmark switch, not a return source.",
    mechanism:
      "Each of these earns compensation for bearing a risk somebody else wants to shed. That is real pay for real risk — the question is whether the vehicle available to a retail holder keeps enough of it.",
    certainty: "different-benchmark",
    status: "rejected",
    statusReason:
      "Family by family the falsifiers fired: put-writing on live-only alpha, credit on its correlation to Treasuries, REITs and dividend funds on dominance, TIPS on correlation, buffered products on the option arithmetic. Catastrophe bonds pass the correlation test and fail on the vehicle.",
    headline: {
      value: "−0.09 to −0.88 %/yr",
      label: "Live-only alpha of put-writing at correlation 0.86–0.95",
      note: "Its up-beta is 0.45 against a down-beta of 0.86, and the record before 2007 is a backtest.",
    },
    evidenceFor: [
      "Catastrophe bonds genuinely pass the correlation screen at about 0.10 to equity.",
      "Merger arbitrage is borderline rather than refuted: MERFX earned +2.06%/yr over cash across ten years, +0.30% across five.",
    ],
    evidenceAgainst: [
      "Credit is not a second engine: its correlation to Treasuries is +0.835. TIPS correlate +0.76 to +0.85 with the nominal bond funds beside them and +0.131 to equity, against nominal bonds' −0.076.",
      "REITs give 112% of the downside for 80% of the upside. SCHD and VNQ are both dominated on Sharpe at correlations of +0.82 and +0.84.",
      "The only catastrophe-bond vehicle is 16 months old at $85.8m, costs 2.00%, and its premium multiple has fallen from 4.54× to 2.40×.",
      "Gold's Sharpe is 0.18 against equity's 0.59 since 1975, and its diversification credit at the ceiling still fails the growth bar.",
    ],
    failureModes: [
      {
        title: "A different benchmark is not an edge",
        detail:
          "Booking a term or credit premium as outperformance against an equity index swaps the yardstick rather than adding return. This is the error the repository has actually made, in four places.",
      },
      {
        title: "The wrapper eats the premium",
        detail:
          "Alternative risk premia earn 0.3–1.0%/yr gross post-2019 at 2–5% volatility, against a retail wrapper costing about 1.5%.",
      },
    ],
    implementation: "None promoted. The audited vehicles are listed with their measured correlations and costs.",
    cost: "0.13% to 2.00% depending on the sleeve, against gross premia that are frequently smaller than the fee.",
    overlap:
      "The recurring finding is that these sleeves overlap far more than their labels suggest. Credit is Treasuries plus equity; TIPS are nominal bonds plus an inflation basis; dividend funds are value with a screen.",
    roleInPortfolio:
      "None supported. The bar a new sleeve has to clear is 0.30 pp/yr of marginal growth, and ten candidates failed it.",
    portfolios: [],
    tickers: ["SCHD", "VNQ", "TIP", "SCHP"],
    sources: [alternatives, marginal, decomposition],
    asOf: READ,
  },
  {
    slug: "rebalancing",
    name: "Rebalancing",
    claim: "Selling what rose and buying what fell earns a return premium of its own.",
    inPractice:
      "It does not, and this is the one rejection here that is not an underpowered null. Rebalancing measured −38.7 bp/yr against buy-and-hold across 420 months. Keep rebalancing — it is how you control exposure — but do not budget a bonus for it.",
    mechanism:
      "Constant weights earn `γ* = ½(Σ wᵢσᵢ² − σ_p²) ≥ 0` in excess growth. The catch is that the term is tiny, and it is exactly a short straddle on relative log performance struck at zero, so trending components take more than the premium pays.",
    certainty: "risk-premium",
    status: "rejected",
    statusReason:
      "The effect is large, negative, and its mechanism is measured rather than assumed. The closed form reproduces on real data to 0.09 bp/yr, so the arithmetic is not in doubt — only the claim built on it.",
    headline: {
      value: "−38.7 bp/yr",
      label: "Measured advantage of rebalancing over buy-and-hold, 420 months",
      note: "The drift gap ran 35× γ*. The theoretical win-probability floor of 68.27% realised in 0.0% of 61 rolling thirty-year windows.",
    },
    evidenceFor: [
      "The closed form is right: the mathematics reproduces to 0.09 bp/yr on real data.",
      "Rebalancing does what it is actually for. It held mean drift to 0.6–3.1 percentage points against 14.83 for buy-and-hold, and cost 0.3–1.2 bp/yr to do it.",
    ],
    evidenceAgainst: [
      "Every rebalanced policy tested had an equal or worse maximum drawdown than buy-and-hold.",
      "Relative regional performance trends rather than reverting: every variance ratio at every horizon in every pair exceeds one, with first-order autocorrelation up to +0.203.",
      "Costs are not the explanation. The dearest policy paid 1.2 bp/yr, against a 38.7 bp gap.",
    ],
    failureModes: [
      {
        title: "The result is scoped",
        detail:
          "Over 1871–2020 against an equal-weight ex-US basket the same test wins by 12 to 18 bp/yr. That is a rounding error of the opposite sign, and it is why the verdict names its window and universe.",
      },
      {
        title: "The 68.27% floor is an assumption, not a theorem about markets",
        detail:
          "It is a property of equal drift between components. Drift was not equal, and the floor realised zero times in 61 windows.",
      },
    ],
    implementation:
      "Annually or on a 25% relative band, whichever produces fewer trades. Direct new contributions at the underweight sleeve before selling anything.",
    cost: "0.3 to 1.2 bp/yr. The binding constraint is the spread: VB's 2.72 bp round trip is nearly a year of its own expense ratio.",
    overlap:
      "It interacts with tax more than with any return engine. In a taxable account rebalancing by selling meets the 162 bp/yr realisation hurdle.",
    roleInPortfolio: "Risk control. Nothing else.",
    portfolios: ["control", "disciplined", "evidence-led", "candidate"],
    tickers: [],
    sources: [rebalancingDoc],
    asOf: READ,
  },
  {
    slug: "placement",
    name: "Asset location",
    claim: "Which account holds which fund changes terminal wealth.",
    inPractice:
      "It does, by about 10 bp a year, and it is the one decision on this site that genuinely requires a calculator rather than a rule: the ranking between developed and emerging markets inverts between two live US dividend rates, so any page that states one ordering is wrong for a large share of its readers.",
    mechanism:
      "`priority = (recurring tax if held in taxable) − (irrecoverable withholding if sheltered)`. For a domestic asset the second term is zero and this collapses to the familiar rule. For a foreign fund it does not: §408(e)(1) exempts the account from tax, so §904's numerator is zero and foreign withholding is paid and permanently lost inside a traditional IRA and a Roth alike.",
    certainty: "contractual",
    status: null,
    statusReason:
      "Every term is a statute or a filed number, and the inversion is reproduced from the funds' own filings.",
    headline: {
      value: "189.7 bp/yr",
      label: "Shelter priority of a bond fund, at the top ordinary rate",
      note: "Bonds dominate by more than four to one at every rate. Restated at a 22% bracket the same figure is about 102 bp.",
    },
    evidenceFor: [
      "The break-even qualified-dividend rate is 10.52% for developed markets and 21.51% for emerging — and 21.51% sits between two live US brackets.",
      "The foreign tax credit is worth 15.78 bp/yr on a developed fund and 20.00 bp on an emerging one, in a taxable account and nowhere else.",
      "Splitting VEA and VWO rather than holding VXUS is worth 1.334 bp of equity at a 23.8% qualified rate and exactly zero once the shelter holds the whole equity sleeve.",
    ],
    evidenceAgainst: [
      "No IRS publication states the IRA result. It is asserted from the statute.",
      "The withholding input that decides the inversion is probably understated: filed rates run 9.12–14.23% against the 9.853% used, which would push the break-even to 24.40–27.48% and extend the inversion to the top bracket.",
    ],
    failureModes: [
      {
        title: "The naive rule is backwards for wrappers",
        detail:
          "'Shelter the highest tax drag' puts DBMF and GDE at the front and RSST near the back — when RSST is the only one of the three whose marginal contribution clears its own detection floor, and the one that needs the shelter least.",
      },
      {
        title: "Wash sales destroy rather than defer",
        detail:
          "Under Rev. Rul. 2008-5 a repurchase inside an IRA destroys the deduction outright. On a 5%-of-portfolio disallowance that is 119 bp. Scanning has to be household-wide.",
      },
    ],
    implementation:
      "Compute the priority for your own bracket, fill the shelter in that order, and keep foreign funds in taxable while the credit is worth more than the sheltered drag.",
    cost: "Nothing but attention, once. Form 1116 is not needed below $300 of creditable foreign tax, about $190,153 of holdings.",
    overlap: "It is part of the contractual budget, and it must never be added to a figure measured against an index.",
    roleInPortfolio: "A free 10 bp for readers with more than one account type, and exactly zero for readers with one.",
    portfolios: ["disciplined"],
    tickers: ["VEA", "VWO", "IEMG", "BND"],
    sources: [structural, recommendation],
    asOf: READ,
  },
  {
    slug: "equity-share",
    name: "The equity share",
    claim: "How much of the portfolio is in equities matters more than which equities.",
    inPractice:
      "It does, and this repository cannot set it for you. Moving from 60/40 to 90/10 is worth +127.1 bp a year against 485 bp of tracking error — larger than every factor tilt priced here combined. It is also the only decision on the site that depends on facts about you rather than about markets.",
    mechanism:
      "Equities pay a premium for a risk that shows up as drawdown. The optimal share is a function of that premium, its volatility and your horizon — and the premium is not estimable to the precision the answer requires.",
    certainty: "risk-premium",
    status: "exploratory",
    statusReason:
      "The drawdown and withdrawal work is measured across sixteen countries and a century, but every forward figure rests on an equity premium nobody here forecasts.",
    headline: {
      value: "+127.1 bp/yr",
      label: "Moving 60/40 to 90/10, against 485 bp of tracking error",
      note: "P(ahead at 30 years) 0.924; 90% confidence at 24 years.",
    },
    evidenceFor: [
      "For any equity-over-bond arithmetic premium above roughly 2.06–2.68%/yr, the arithmetic gives a corner solution at 100% equity. A 60/40 portfolio asserts a forecast of about 1.18–1.30%/yr, whether or not its holder knows it.",
      "At a 4% real withdrawal the safest thirty-year portfolio holds 60% equity, and a 20%-equity portfolio is nearly three times as likely to fail. The minimum walks right as the withdrawal rate rises.",
      "An all-bond portfolio's drawdown was −25.1%, deeper than a 30/70 mix's −17.9%.",
    ],
    evidenceAgainst: [
      "−50.3% is not a worst case. Over the full hundred-year US record it is −83.7%, and across sixteen countries the US ranks 16th of 16 from 1963 while the median market lost about three quarters of its real value.",
      "The bond–equity correlation is not stable: beta ran +0.129, then −0.055, then +0.116, then −0.109 across four regimes.",
      "The cost of estimating the optimum is `1/(2T)` — about 0.80%/yr even with 62 years of data.",
    ],
    failureModes: [
      {
        title: "Overshooting is asymmetric",
        detail:
          "Growth retained at a fraction `f` of the optimum is `1 − (1 − f)²`: half the optimal share keeps 75% of the growth, and twice it keeps none at all.",
      },
      {
        title: "The horizon is not the only input",
        detail:
          "A short horizon and a drawdown phase point in opposite directions, and were one row in this repository's own table until they were measured.",
      },
    ],
    implementation:
      "Pick a share you can hold through an 80% decline, write down why, and change it only when the reason changes.",
    cost: "None directly. The cost is the drawdown you have to sit through.",
    overlap:
      "It dominates everything else on this site. A 30-percentage-point change in equity share is worth roughly five times the largest factor tilt priced here.",
    roleInPortfolio: "The first decision, and the one the evidence is most honestly silent on.",
    portfolios: ["control", "candidate"],
    tickers: ["VTI", "BND"],
    sources: [equityShare, recommendation],
    asOf: READ,
  },
];

export function familyBySlug(slug: string): StrategyFamily | undefined {
  return families.find((one) => one.slug === slug);
}

export const familiesAsOf = READ;
