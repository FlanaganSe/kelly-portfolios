import type { FactorLoading, LoadingWindow, ShelfFund } from "~/content/shelf";

/**
 * Comparing factor loadings, and refusing to when they are not comparable.
 *
 * Every loading on the shelf was fitted on the months that fund had filed with the SEC, so
 * the windows differ: VTV carries 72 months, AVLV 51, DFLV 36. Sorting those nine numbers
 * produces an ordering of launch dates as much as an ordering of funds, and the size of
 * the error is not small. Refitted on the 36 months all nine share, VTV's HML rises from
 * +0.337 to +0.520 and AVLV's from +0.322 to +0.413 — AVLV goes from third-lowest to last,
 * and VTV overtakes three systematic funds it trailed on the published numbers.
 *
 * So `rankLoadings` throws rather than sorts when the windows differ, the way
 * `studies/outperformance_horizon.aggregate()` in the research workspace raises rather
 * than adding results measured against different benchmarks. A caller that wants an
 * ordering anyway must first say which window it means.
 *
 * See `docs/research/loading-comparability-and-wrapper-exposure.md`.
 */

/** Thrown when loadings fitted on different months were about to be ranked. */
export class IncomparableWindowsError extends Error {
  readonly windows: readonly string[];

  constructor(message: string, windows: readonly string[]) {
    super(message);
    this.name = "IncomparableWindowsError";
    this.windows = windows;
  }
}

/** `2020-01..2025-12`. The identity of a window, and what a reader should see. */
export function windowLabel(window: LoadingWindow | null): string {
  return window === null ? "—" : `${window.from}..${window.to}`;
}

/** Months in a window, both ends inclusive. Derived, never stored, so it cannot drift. */
export function windowMonths(window: LoadingWindow | null): number | null {
  if (window === null) return null;
  return monthIndex(window.to) - monthIndex(window.from) + 1;
}

/** `2020-01..2025-12 (72m)`. The window and its length, never one without the other. */
export function windowSummary(window: LoadingWindow | null): string {
  const months = windowMonths(window);
  return months === null ? "—" : `${windowLabel(window)} (${months}m)`;
}

/** Whether two loadings were fitted on exactly the same months. */
export function sameWindow(a: FactorLoading, b: FactorLoading): boolean {
  if (a.window === null || b.window === null) return false;
  return a.window.from === b.window.from && a.window.to === b.window.to;
}

/** The distinct windows in a set of loadings, as labels, in the order first seen. */
export function distinctWindows(loadings: readonly FactorLoading[]): readonly string[] {
  const seen: string[] = [];
  for (const loading of loadings) {
    const label = windowLabel(loading.window);
    if (!seen.includes(label)) seen.push(label);
  }
  return seen;
}

/**
 * The months every loading in the set shares, or `null` when they never overlap.
 *
 * This is the window a comparison would have to be refitted on. It is not a way to make
 * the published numbers comparable — they were fitted on their own windows and stay that
 * way — it is what a new estimate would use.
 */
export function commonWindow(loadings: readonly FactorLoading[]): LoadingWindow | null {
  const windows = loadings.map((loading) => loading.window);
  if (windows.length === 0 || windows.some((window) => window === null)) return null;
  let from = windows[0]?.from ?? "";
  let to = windows[0]?.to ?? "";
  for (const window of windows) {
    if (window === null) return null;
    if (window.from > from) from = window.from;
    if (window.to < to) to = window.to;
  }
  return monthIndex(to) < monthIndex(from) ? null : { from, to };
}

/**
 * `loadings` sorted by value, largest first — but only when they are comparable.
 *
 * Throws `IncomparableWindowsError` when the loadings were not all fitted on the same
 * months, on different factors, or on different panels. Those are the three ways a shelf
 * table silently compares two different quantities.
 */
export function rankLoadings(loadings: readonly FactorLoading[]): readonly FactorLoading[] {
  if (loadings.length === 0) return [];
  const windows = distinctWindows(loadings);
  if (windows.length > 1 || windows[0] === "—") {
    throw new IncomparableWindowsError(
      `refusing to rank loadings fitted on different months: ${windows.join(", ")}. ` +
        "Refit them on the window they share; a ranking across unequal windows orders launch dates as well as funds.",
      windows
    );
  }
  const factors = new Set(loadings.map((loading) => loading.factor));
  const panels = new Set(loadings.map((loading) => loading.panel));
  if (factors.size > 1 || panels.size > 1) {
    throw new IncomparableWindowsError(
      `refusing to rank across factors ${[...factors].join("/")} on panels ${[...panels].join("/")}: ` +
        "those are different quantities.",
      windows
    );
  }
  return [...loadings].sort((a, b) => b.value - a.value);
}

/** Every loading on `factor` and `panel` across `funds`, paired with its ticker. */
export function loadingsFor(
  funds: readonly ShelfFund[],
  factor: FactorLoading["factor"],
  panel: FactorLoading["panel"]
): readonly { readonly ticker: string; readonly loading: FactorLoading }[] {
  const found: { ticker: string; loading: FactorLoading }[] = [];
  for (const fund of funds) {
    for (const loading of fund.loadings) {
      if (loading.factor === factor && loading.panel === panel) found.push({ ticker: fund.ticker, loading });
    }
  }
  return found;
}

function monthIndex(period: string): number {
  const year = Number(period.slice(0, 4));
  const month = Number(period.slice(5, 7));
  if (!Number.isInteger(year) || !Number.isInteger(month) || month < 1 || month > 12) {
    throw new Error(`expected a YYYY-MM period, got ${period}`);
  }
  return year * 12 + month - 1;
}
