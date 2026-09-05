/**
 * Weighted expense ratios, so a portfolio's fee is arithmetic on the shelf rather than a
 * number someone typed. One basis point on $10,000 is one dollar, which is why the
 * dollar form needs no second conversion.
 */
import { roundTo } from "~/lib/format";

export interface WeightedHolding {
  readonly ticker: string;
  readonly weight: number;
}

const WEIGHT_TOLERANCE = 1e-9;

/** Basis points a year, weighted by each holding's share of the money (weights in percent). */
export function weightedExpenseRatioBp(
  holdings: readonly WeightedHolding[],
  expenseRatioBp: (ticker: string) => number
): number {
  const total = holdings.reduce((sum, h) => sum + h.weight, 0);
  if (Math.abs(total - 100) > WEIGHT_TOLERANCE) {
    throw new RangeError(`holdings weigh ${total}%, not 100%`);
  }
  return holdings.reduce((sum, h) => sum + (h.weight * expenseRatioBp(h.ticker)) / 100, 0);
}

/** `20.585` bp renders as `0.21%`. */
export function feePercentText(bp: number): string {
  return `${roundTo(bp / 100, 2).toFixed(2)}%`;
}

/** The same fee on $10,000, whole dollars: `20.585` bp is `$21`. */
export function feeOn10kText(bp: number): string {
  return `$${Math.round(bp)}`;
}
