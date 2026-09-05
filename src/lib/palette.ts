/**
 * One colour per fund, the same on every page.
 *
 * An allocation bar names a fund by colour before a reader finds the legend, so the
 * mapping is fixed here rather than assigned in order on each page: VTI is the same hue
 * on the home page, the comparison table and the portfolio page. Each entry names a CSS
 * custom property defined in `styles.css`, once for light and once for dark, so the
 * component never carries a hex value and the theme swap stays in one file.
 *
 * Hues are muted and spread around the wheel. Nothing here is red for bad or green for
 * good; the bar shows what a portfolio holds, not a judgement about it.
 */

export const FUND_COLOURS = {
  VT: "var(--fund-vt)",
  VTI: "var(--fund-vti)",
  VOO: "var(--fund-vti)",
  VTV: "var(--fund-vtv)",
  VXUS: "var(--fund-vxus)",
  AVDV: "var(--fund-avdv)",
  IDMO: "var(--fund-idmo)",
  AVES: "var(--fund-aves)",
  RSST: "var(--fund-rsst)",
  TIPS: "var(--fund-tips)",
  SCHP: "var(--fund-tips)",
  CASH: "var(--fund-cash)",
} as const satisfies Readonly<Record<string, string>>;

/** The colour for any ticker, falling back to a neutral ink for one not listed. */
export function fundColour(ticker: string): string {
  const colours: Readonly<Record<string, string | undefined>> = FUND_COLOURS;
  return colours[ticker.toUpperCase()] ?? "var(--fund-other)";
}

/**
 * One colour per portfolio line on a chart, fixed by id so the same portfolio is the
 * same hue on every chart. The market and the 60/40 comparison lines are neutral ink,
 * because they are the yardstick and never the subject. Anything else takes the next
 * unused slot. The four hues were checked as a set for colour-vision separation in
 * both themes, with the direct end label and line weight as the second channel.
 */
export const SERIES_COLOURS = {
  "one-fund": "var(--series-1)",
  "value-lean": "var(--series-2)",
  "with-trend": "var(--series-3)",
  cautious: "var(--series-4)",
  "cautious-30": "var(--series-4)",
  market: "var(--series-market)",
  "sixty-forty": "var(--series-market)",
} as const satisfies Readonly<Record<string, string>>;

const SERIES_SLOTS = ["var(--series-1)", "var(--series-2)", "var(--series-3)", "var(--series-4)"] as const;

/** Whether a series is a comparison line rather than a portfolio. */
export function isBenchmark(id: string): boolean {
  return id === "market" || id === "sixty-forty";
}

/** The colour for a series id; an unknown id gets the slot at `index`, wrapping. */
export function seriesColour(id: string, index = 0): string {
  const colours: Readonly<Record<string, string | undefined>> = SERIES_COLOURS;
  return colours[id] ?? (SERIES_SLOTS[index % SERIES_SLOTS.length] as string);
}
