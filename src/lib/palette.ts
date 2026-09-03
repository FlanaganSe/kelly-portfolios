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
