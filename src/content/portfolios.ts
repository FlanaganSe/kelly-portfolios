/**
 * The four portfolios, as data: one place for the holdings, the fee and the one-line
 * description, read by the home page, the comparison page and each portfolio's own page.
 * The with-trend portfolio has a second version for today's prices, which the comparison
 * page shows as its own column and the with-trend page shows in full. The cautious
 * portfolio has two versions, for a fall of about 40% and about 30%; the card shows the
 * first and its page shows both.
 *
 * Fees are each fund's published expense ratio weighted by the holdings, so they are
 * plain text. Anything measured carries a figure record; the worst-fall text here names
 * the record it repeats so the two cannot drift apart unnoticed.
 */
import type { Confidence } from "~/lib/rungs";

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
  readonly worstFall: string;
  readonly worstFallNote: string;
  readonly confidence: Confidence;
}

export const VALUE_LEAN_HOLDINGS: readonly Holding[] = [
  { ticker: "VTI", weight: 49 },
  { ticker: "VXUS", weight: 16 },
  { ticker: "VTV", weight: 15 },
  { ticker: "AVDV", weight: 10 },
  { ticker: "IDMO", weight: 5 },
  { ticker: "AVES", weight: 5 },
];

export const WITH_TREND_HOLDINGS: readonly Holding[] = [
  { ticker: "RSST", weight: 30 },
  { ticker: "VTI", weight: 19 },
  { ticker: "VXUS", weight: 16 },
  { ticker: "VTV", weight: 15 },
  { ticker: "AVDV", weight: 10 },
  { ticker: "IDMO", weight: 5 },
  { ticker: "AVES", weight: 5 },
];

/**
 * The with-trend portfolio, priced for today's market: 5 points move from RSST into
 * ten-year TIPS, held in a traditional account. SCHP is the cheapest TIPS fund priced.
 */
export const TODAY_HOLDINGS: readonly Holding[] = [
  { ticker: "RSST", weight: 25 },
  { ticker: "VTI", weight: 19 },
  { ticker: "VXUS", weight: 16 },
  { ticker: "VTV", weight: 15 },
  { ticker: "AVDV", weight: 10 },
  { ticker: "IDMO", weight: 5 },
  { ticker: "AVES", weight: 5 },
  { ticker: "SCHP", weight: 5, label: "Ten-year TIPS" },
];

/**
 * The cautious version for a fall of about 40%: portfolio three's funds scaled to 35
 * points of stocks and 15 of RSST, the rest in TIPS. Fell 18.1% since 1990 and 53.8%
 * across 1929 to 1932 (Experiment 025, decision 0014).
 */
export const CAUTIOUS_40_HOLDINGS: readonly Holding[] = [
  { ticker: "SCHP", weight: 50, label: "TIPS" },
  { ticker: "RSST", weight: 15 },
  { ticker: "VTI", weight: 9.6 },
  { ticker: "VXUS", weight: 8 },
  { ticker: "VTV", weight: 7.5 },
  { ticker: "AVDV", weight: 5 },
  { ticker: "IDMO", weight: 2.5 },
  { ticker: "AVES", weight: 2.5 },
];

/**
 * The cautious version for a fall of about 30%: 26 points of stocks, 11 of RSST, 63 of
 * TIPS. Fell 15.8% since 1990 and 41.7% across 1929 to 1932.
 */
export const CAUTIOUS_30_HOLDINGS: readonly Holding[] = [
  { ticker: "SCHP", weight: 63, label: "TIPS" },
  { ticker: "RSST", weight: 11 },
  { ticker: "VTI", weight: 7.1 },
  { ticker: "VXUS", weight: 5.9 },
  { ticker: "VTV", weight: 5.6 },
  { ticker: "AVDV", weight: 3.7 },
  { ticker: "IDMO", weight: 1.9 },
  { ticker: "AVES", weight: 1.8 },
];

export const PORTFOLIOS: readonly Portfolio[] = [
  {
    number: 1,
    slug: "one-fund",
    name: "One fund, held well",
    href: "/portfolios/one-fund/",
    tagline:
      "The whole world's stock market in a single fund, in its cheapest form, in the right account, and never traded.",
    holdings: [{ ticker: "VT", weight: 100 }],
    fee: "0.06%",
    feeOn10k: "$6",
    worstFall: "−52.7%",
    worstFallNote: "Cheap US and international mix, 1990 to 2026",
    confidence: "Settled",
  },
  {
    number: 2,
    slug: "value-lean",
    name: "A lean toward value",
    href: "/portfolios/value-lean/",
    tagline: "Six funds that lean toward cheaper, smaller, more profitable companies.",
    holdings: VALUE_LEAN_HOLDINGS,
    fee: "0.09%",
    feeOn10k: "$9",
    worstFall: "−54.3%",
    worstFallNote: "Cheap US stocks against the whole market, over 17.7 years since 2008 and still behind",
    confidence: "Probably",
  },
  {
    number: 3,
    slug: "with-trend",
    name: "The same, plus trend",
    href: "/portfolios/with-trend/",
    tagline: "The value lean, plus a fund that adds a trend-following program on top of its stocks.",
    holdings: WITH_TREND_HOLDINGS,
    fee: "0.38%",
    feeOn10k: "$38",
    worstFall: "−50.3%",
    worstFallNote: "1990 to 2026, with RSST at 25%",
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
    fee: "0.20%",
    feeOn10k: "$20",
    worstFall: "−18.1%",
    worstFallNote: "1990 to 2026; 54% across 1929 to 1932",
    confidence: "Too close to call",
  },
];

export function portfolio(slug: Portfolio["slug"]): Portfolio {
  const found = PORTFOLIOS.find((p) => p.slug === slug);
  if (found === undefined) throw new Error(`No portfolio named ${slug}`);
  return found;
}
