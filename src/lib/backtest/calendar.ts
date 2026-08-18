/**
 * Month arithmetic. The engine counts months since 1970-01 so that alignment,
 * rebalancing and calendar-year grouping are integer work rather than date work.
 */

import type { MonthIndex } from "~/lib/backtest/types";

const EPOCH_YEAR = 1970;

/** `"2001-03"` → the month index of March 2001. Throws on anything else. */
export function toMonthIndex(yearMonth: string): MonthIndex {
  const match = /^(\d{4})-(\d{2})$/.exec(yearMonth);
  if (match === null) {
    throw new Error(`month must be "YYYY-MM", received "${yearMonth}"`);
  }
  const year = Number(match[1]);
  const month = Number(match[2]);
  if (month < 1 || month > 12) {
    throw new Error(`month out of range in "${yearMonth}"`);
  }
  return (year - EPOCH_YEAR) * 12 + (month - 1);
}

/** The inverse of `toMonthIndex`. */
export function toYearMonth(index: MonthIndex): string {
  const year = EPOCH_YEAR + Math.floor(index / 12);
  const month = (((index % 12) + 12) % 12) + 1;
  return `${String(year).padStart(4, "0")}-${String(month).padStart(2, "0")}`;
}

export function yearOf(index: MonthIndex): number {
  return EPOCH_YEAR + Math.floor(index / 12);
}

/** 0 for January, 11 for December. */
export function monthOfYear(index: MonthIndex): number {
  return ((index % 12) + 12) % 12;
}
