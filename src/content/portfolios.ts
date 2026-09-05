/**
 * The four portfolios, as data: one place for the holdings, the fee and the one-line
 * description, read by the home page, the comparison page and each portfolio's own page.
 *
 * Nothing numeric here is typed. The fee is each fund's published expense ratio from
 * `src/content/shelf.ts`, weighted by the holdings. The worst fall is read from the series
 * the research emitter writes to `src/content/series/`, computed for exactly these weights
 * on the 1990 to 2026 history (`src/lib/series.ts`), and a vitest asserts that the weights
 * below equal the weights the emitter scored, so the two cannot drift apart unnoticed.
 *
 * One version of each portfolio. The 30% cautious version is kept only as data for the
 * one sentence the cautious page spends on it.
 */
import { fundByTicker } from "~/content/shelf";
import { feeOn10kText, feePercentText, weightedExpenseRatioBp } from "~/lib/fees";
import { formatSignedPercent } from "~/lib/format";
import type { Confidence } from "~/lib/rungs";
import { portfolioSummary } from "~/lib/series";

/** One line of a portfolio: a ticker and its share of the money, in percent. */
export interface Holding {
  readonly ticker: string;
  readonly weight: number;
  readonly label?: string;
}

export interface Portfolio {
  readonly number: 1 | 2 | 3 | 4;
  readonly slug: "one-fund" | "value-lean" | "with-trend" | "cautious";
  readonly name: string;
  readonly href: string;
  readonly tagline: string;
  readonly holdings: readonly Holding[];
  /** Weighted expense ratio, as text. */
  readonly fee: string;
  /** The fee on $10,000, as text. */
  readonly feeOn10k: string;
  /** The deepest fall of a simulated $10,000, 1990 to 2026, as signed text. */
  readonly worstFall: string;
  readonly worstFallNote: string;
  readonly confidence: Confidence;
}

const BOND_LABEL = "Inflation-protected government bonds";

export const VALUE_LEAN_HOLDINGS: readonly Holding[] = [
  { ticker: "VTI", weight: 49 },
  { ticker: "VXUS", weight: 16 },
  { ticker: "VTV", weight: 15 },
  { ticker: "AVDV", weight: 10 },
  { ticker: "IDMO", weight: 5 },
  { ticker: "AVES", weight: 5 },
];

/** The value lean plus a trend-following fund, with five points in ten-year TIPS. */
export const WITH_TREND_HOLDINGS: readonly Holding[] = [
  { ticker: "RSST", weight: 25 },
  { ticker: "VTI", weight: 19 },
  { ticker: "VXUS", weight: 16 },
  { ticker: "VTV", weight: 15 },
  { ticker: "AVDV", weight: 10 },
  { ticker: "IDMO", weight: 5 },
  { ticker: "AVES", weight: 5 },
  { ticker: "SCHP", weight: 5, label: BOND_LABEL },
];

/**
 * The cautious portfolio, for a fall of about 40%: portfolio three's funds scaled to 35
 * points of stocks and 15 of RSST, the rest in TIPS. Sums to 100.
 */
export const CAUTIOUS_40_HOLDINGS: readonly Holding[] = [
  { ticker: "SCHP", weight: 50, label: BOND_LABEL },
  { ticker: "RSST", weight: 15 },
  { ticker: "VTI", weight: 9.5 },
  { ticker: "VXUS", weight: 8 },
  { ticker: "VTV", weight: 7.5 },
  { ticker: "AVDV", weight: 5 },
  { ticker: "IDMO", weight: 2.5 },
  { ticker: "AVES", weight: 2.5 },
];

/**
 * The retired version for a fall of about 30%: 26 points of stocks, 11 of RSST, 63 of TIPS.
 * Data for one sentence on the cautious page; its own series is `cautious-30`.
 */
export const CAUTIOUS_30_HOLDINGS: readonly Holding[] = [
  { ticker: "SCHP", weight: 63, label: BOND_LABEL },
  { ticker: "RSST", weight: 11 },
  { ticker: "VTI", weight: 7.1 },
  { ticker: "VXUS", weight: 5.9 },
  { ticker: "VTV", weight: 5.6 },
  { ticker: "AVDV", weight: 3.7 },
  { ticker: "IDMO", weight: 1.9 },
  { ticker: "AVES", weight: 1.8 },
];

function fee(holdings: readonly Holding[]): Pick<Portfolio, "fee" | "feeOn10k"> {
  const bp = weightedExpenseRatioBp(holdings, (ticker) => {
    const ratio = fundByTicker(ticker).expenseRatioBp;
    if (ratio === null) throw new Error(`${ticker} has no expense ratio on the shelf`);
    return ratio;
  });
  return { fee: feePercentText(bp), feeOn10k: feeOn10kText(bp) };
}

function worstFall(slug: Portfolio["slug"]): Pick<Portfolio, "worstFall" | "worstFallNote"> {
  return {
    worstFall: formatSignedPercent(portfolioSummary(slug).worstFall.pct),
    worstFallNote: "1990 to 2026, simulated",
  };
}

const ONE_FUND_HOLDINGS: readonly Holding[] = [{ ticker: "VT", weight: 100 }];

export const PORTFOLIOS: readonly Portfolio[] = [
  {
    number: 1,
    slug: "one-fund",
    name: "One fund, held well",
    href: "/portfolios/one-fund/",
    tagline:
      "The whole world's stock market in a single fund, in its cheapest form, in the right account, and never traded.",
    holdings: ONE_FUND_HOLDINGS,
    ...fee(ONE_FUND_HOLDINGS),
    ...worstFall("one-fund"),
    confidence: "Settled",
  },
  {
    number: 2,
    slug: "value-lean",
    name: "A lean toward value",
    href: "/portfolios/value-lean/",
    tagline: "Six funds that lean toward cheaper, smaller, more profitable companies.",
    holdings: VALUE_LEAN_HOLDINGS,
    ...fee(VALUE_LEAN_HOLDINGS),
    ...worstFall("value-lean"),
    confidence: "Probably",
  },
  {
    number: 3,
    slug: "with-trend",
    name: "The same, plus trend",
    href: "/portfolios/with-trend/",
    tagline: "The value lean, plus a fund that adds a trend-following program on top of its stocks.",
    holdings: WITH_TREND_HOLDINGS,
    ...fee(WITH_TREND_HOLDINGS),
    ...worstFall("with-trend"),
    confidence: "Too close to call",
  },
  {
    number: 4,
    slug: "cautious",
    name: "The cautious version",
    href: "/portfolios/cautious/",
    tagline:
      "Portfolio three with the stock share cut and the rest in TIPS, for someone who would sell after a fall of about 30% or 40%.",
    holdings: CAUTIOUS_40_HOLDINGS,
    ...fee(CAUTIOUS_40_HOLDINGS),
    ...worstFall("cautious"),
    confidence: "Too close to call",
  },
];

export function portfolio(slug: Portfolio["slug"]): Portfolio {
  const found = PORTFOLIOS.find((p) => p.slug === slug);
  if (found === undefined) throw new Error(`No portfolio named ${slug}`);
  return found;
}
