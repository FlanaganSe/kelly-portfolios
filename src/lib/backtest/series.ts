/**
 * Alignment. Two funds with different inception dates share only the window both
 * of them cover, and the engine refuses to invent the rest.
 *
 * The rule this file exists to enforce: a missing observation is never filled, never
 * carried forward, and never proxied. If a test cannot be run over a window, the
 * caller is told which symbol is short and by how much.
 */

import type { MonthRange, ReturnSeries } from "~/lib/backtest/types";

/** The month of the last observation. */
export function seriesEnd(series: ReturnSeries): number {
  return series.start + series.returns.length - 1;
}

export function coversRange(series: ReturnSeries, range: MonthRange): boolean {
  return series.start <= range.start && seriesEnd(series) >= range.end;
}

/**
 * The window every series covers. `null` when the series do not overlap at all,
 * which is a real answer and not an error: two funds can simply never have coexisted.
 */
export function commonRange(series: readonly ReturnSeries[]): MonthRange | null {
  if (series.length === 0) {
    return null;
  }
  let start = Number.NEGATIVE_INFINITY;
  let end = Number.POSITIVE_INFINITY;
  for (const one of series) {
    if (one.returns.length === 0) {
      return null;
    }
    start = Math.max(start, one.start);
    end = Math.min(end, seriesEnd(one));
  }
  return start > end ? null : { start, end };
}

/**
 * The observations for `range`, in order. Throws rather than padding: a caller that
 * wants a shorter test has to ask for a shorter range.
 */
export function slice(series: ReturnSeries, range: MonthRange): readonly number[] {
  if (!coversRange(series, range)) {
    throw new Error(
      `series "${series.id}" covers ${series.start}..${seriesEnd(series)} and cannot supply ${range.start}..${range.end}`
    );
  }
  return series.returns.slice(range.start - series.start, range.end - series.start + 1);
}

export function rangeLength(range: MonthRange): number {
  return range.end - range.start + 1;
}

/** Whether the two ranges describe the same window. */
export function sameRange(a: MonthRange, b: MonthRange): boolean {
  return a.start === b.start && a.end === b.end;
}
