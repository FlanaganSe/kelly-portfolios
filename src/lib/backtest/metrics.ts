/**
 * The summary statistics.
 *
 * Each function takes monthly total returns and returns one number, so each can be
 * checked against a hand-computed fixture. Three conventions are fixed here and
 * stated on the page that displays them, because they are the ones that quietly
 * differ between tools:
 *
 * 1. **Volatility is the sample standard deviation** of monthly returns times √12.
 *    A monthly series annualised this way is not the same as the volatility of
 *    annual returns, and is the near-universal convention.
 * 2. **Sharpe uses the arithmetic mean of monthly excess returns**, annualised by
 *    ×12, over annualised volatility. It is not `(CAGR − rf) / σ`; the two differ by
 *    the variance drag and the difference is not small at equity volatility.
 * 3. **Drawdown is measured on month-end values.** An intra-month low is invisible
 *    to a monthly series, so every drawdown here is an understatement of the worst
 *    price a holder actually saw.
 */

import { monthOfYear, yearOf } from "~/lib/backtest/calendar";
import type { MonthIndex } from "~/lib/backtest/types";

const MONTHS_PER_YEAR = 12;

function mean(values: readonly number[]): number {
  if (values.length === 0) {
    return Number.NaN;
  }
  return values.reduce((sum, one) => sum + one, 0) / values.length;
}

/** Sample standard deviation. `NaN` below two observations, which is the truth. */
export function standardDeviation(values: readonly number[]): number {
  if (values.length < 2) {
    return Number.NaN;
  }
  const average = mean(values);
  const sumSquares = values.reduce((sum, one) => sum + (one - average) ** 2, 0);
  return Math.sqrt(sumSquares / (values.length - 1));
}

/** Compound growth of 1 unit. */
export function totalReturn(returns: readonly number[]): number {
  return returns.reduce((product, one) => product * (1 + one), 1) - 1;
}

/**
 * Compound annual growth rate. Defined for any positive number of months; a
 * sub-annual window is annualised, which the interface labels as such rather than
 * printing it as though a year had passed.
 */
export function cagr(returns: readonly number[]): number {
  if (returns.length === 0) {
    return Number.NaN;
  }
  const growth = returns.reduce((product, one) => product * (1 + one), 1);
  if (growth <= 0) {
    // A portfolio that reached zero has no growth rate. Reporting −100% is honest;
    // reporting a root of a negative number is not.
    return -1;
  }
  return growth ** (MONTHS_PER_YEAR / returns.length) - 1;
}

export function annualisedVolatility(returns: readonly number[]): number {
  return standardDeviation(returns) * Math.sqrt(MONTHS_PER_YEAR);
}

/** Growth of 1 unit, month by month, starting at 1. Length is `returns.length + 1`. */
export function growthPath(returns: readonly number[]): number[] {
  const path = [1];
  for (const one of returns) {
    path.push((path[path.length - 1] ?? 1) * (1 + one));
  }
  return path;
}

/** Fraction below the running peak at each month end. Zero or negative. */
export function drawdownPath(returns: readonly number[]): number[] {
  const path = growthPath(returns);
  let peak = Number.NEGATIVE_INFINITY;
  return path.map((value) => {
    peak = Math.max(peak, value);
    return peak === 0 ? 0 : value / peak - 1;
  });
}

export interface Drawdown {
  /** Negative. −0.34 is a 34% fall. */
  readonly depth: number;
  /** Offsets into the growth path, where 0 is the month before the first return. */
  readonly peakIndex: number;
  readonly troughIndex: number;
  /** `null` when the series ends before the previous peak was regained. */
  readonly recoveryIndex: number | null;
}

export function maxDrawdown(returns: readonly number[]): Drawdown {
  const path = growthPath(returns);
  let peak = path[0] ?? 1;
  let peakIndex = 0;
  let worst: Drawdown = { depth: 0, peakIndex: 0, troughIndex: 0, recoveryIndex: 0 };

  for (let index = 1; index < path.length; index += 1) {
    const value = path[index] ?? 1;
    if (value > peak) {
      peak = value;
      peakIndex = index;
      continue;
    }
    const depth = peak === 0 ? 0 : value / peak - 1;
    if (depth < worst.depth) {
      worst = { depth, peakIndex, troughIndex: index, recoveryIndex: null };
    }
  }

  if (worst.depth === 0) {
    return worst;
  }
  const peakValue = path[worst.peakIndex] ?? 1;
  for (let index = worst.troughIndex + 1; index < path.length; index += 1) {
    if ((path[index] ?? 0) >= peakValue) {
      return { ...worst, recoveryIndex: index };
    }
  }
  return worst;
}

/**
 * Annualised Sharpe. `riskFree` is a monthly series aligned to `returns`; a single
 * number is read as a constant monthly rate. Returns `null` rather than a divide by
 * zero when the series has no variation.
 */
export function sharpeRatio(returns: readonly number[], riskFree: readonly number[] | number): number | null {
  const excess = returns.map((one, index) =>
    typeof riskFree === "number" ? one - riskFree : one - (riskFree[index] ?? 0)
  );
  const volatility = standardDeviation(excess) * Math.sqrt(MONTHS_PER_YEAR);
  if (!Number.isFinite(volatility) || volatility === 0) {
    return null;
  }
  return (mean(excess) * MONTHS_PER_YEAR) / volatility;
}

/**
 * Annualised Sortino against a minimum acceptable monthly return.
 *
 * The downside deviation divides by the **full** count of observations, not by the
 * count of losing ones. Dividing by the losing count is a common implementation and
 * it makes a portfolio look better the fewer times it loses, which is backwards.
 */
export function sortinoRatio(returns: readonly number[], minimumAcceptable = 0): number | null {
  if (returns.length < 2) {
    return null;
  }
  const shortfalls = returns.map((one) => Math.min(0, one - minimumAcceptable));
  const downside = Math.sqrt(shortfalls.reduce((sum, one) => sum + one ** 2, 0) / returns.length);
  const annualisedDownside = downside * Math.sqrt(MONTHS_PER_YEAR);
  if (annualisedDownside === 0) {
    return null;
  }
  return ((mean(returns) - minimumAcceptable) * MONTHS_PER_YEAR) / annualisedDownside;
}

export function correlation(a: readonly number[], b: readonly number[]): number | null {
  if (a.length !== b.length || a.length < 2) {
    return null;
  }
  const meanA = mean(a);
  const meanB = mean(b);
  let covariance = 0;
  let varianceA = 0;
  let varianceB = 0;
  for (let index = 0; index < a.length; index += 1) {
    const da = (a[index] ?? 0) - meanA;
    const db = (b[index] ?? 0) - meanB;
    covariance += da * db;
    varianceA += da * da;
    varianceB += db * db;
  }
  if (varianceA === 0 || varianceB === 0) {
    return null;
  }
  return covariance / Math.sqrt(varianceA * varianceB);
}

/** Ordinary least squares slope of `returns` on `benchmark`. */
export function beta(returns: readonly number[], benchmark: readonly number[]): number | null {
  if (returns.length !== benchmark.length || returns.length < 2) {
    return null;
  }
  const meanB = mean(benchmark);
  const meanR = mean(returns);
  let covariance = 0;
  let variance = 0;
  for (let index = 0; index < returns.length; index += 1) {
    const db = (benchmark[index] ?? 0) - meanB;
    covariance += db * ((returns[index] ?? 0) - meanR);
    variance += db * db;
  }
  if (variance === 0) {
    return null;
  }
  return covariance / variance;
}

/** Annualised standard deviation of the monthly return difference. */
export function trackingError(returns: readonly number[], benchmark: readonly number[]): number | null {
  if (returns.length !== benchmark.length || returns.length < 2) {
    return null;
  }
  const difference = returns.map((one, index) => one - (benchmark[index] ?? 0));
  return standardDeviation(difference) * Math.sqrt(MONTHS_PER_YEAR);
}

/** Mean monthly excess return annualised, over tracking error. */
export function informationRatio(returns: readonly number[], benchmark: readonly number[]): number | null {
  const error = trackingError(returns, benchmark);
  if (error === null || error === 0) {
    return null;
  }
  const difference = returns.map((one, index) => one - (benchmark[index] ?? 0));
  return (mean(difference) * MONTHS_PER_YEAR) / error;
}

export interface CalendarYear {
  readonly year: number;
  readonly portfolio: number;
  readonly benchmark: number | null;
  /** False when the window starts or ends mid-year. Partial years are labelled. */
  readonly complete: boolean;
}

export function calendarYears(
  returns: readonly number[],
  startMonth: MonthIndex,
  benchmark?: readonly number[]
): CalendarYear[] {
  const byYear = new Map<number, { portfolio: number[]; benchmark: number[] }>();
  for (let index = 0; index < returns.length; index += 1) {
    const month = startMonth + index;
    const year = yearOf(month);
    const bucket = byYear.get(year) ?? { portfolio: [], benchmark: [] };
    bucket.portfolio.push(returns[index] ?? 0);
    if (benchmark !== undefined) {
      bucket.benchmark.push(benchmark[index] ?? 0);
    }
    byYear.set(year, bucket);
  }

  const firstMonth = monthOfYear(startMonth);
  const lastMonth = monthOfYear(startMonth + returns.length - 1);
  const firstYear = yearOf(startMonth);
  const lastYear = yearOf(startMonth + returns.length - 1);

  return [...byYear.entries()]
    .sort(([a], [b]) => a - b)
    .map(([year, bucket]) => ({
      year,
      portfolio: totalReturn(bucket.portfolio),
      benchmark: benchmark === undefined ? null : totalReturn(bucket.benchmark),
      complete: !((year === firstYear && firstMonth !== 0) || (year === lastYear && lastMonth !== 11)),
    }));
}

export interface RollingWindow {
  /** Month index of the last month in the window. */
  readonly endMonth: MonthIndex;
  readonly portfolio: number;
  readonly benchmark: number;
  readonly excess: number;
}

/**
 * Annualised return over each rolling window of `windowMonths`, alongside the
 * benchmark's, and the difference. Excess is a difference of annualised rates, which
 * is the readable form; it is not a compounded excess and is not labelled as one.
 */
export function rollingExcess(
  returns: readonly number[],
  benchmark: readonly number[],
  startMonth: MonthIndex,
  windowMonths: number
): RollingWindow[] {
  if (windowMonths <= 0 || returns.length < windowMonths || returns.length !== benchmark.length) {
    return [];
  }
  const windows: RollingWindow[] = [];
  for (let start = 0; start + windowMonths <= returns.length; start += 1) {
    const portfolio = cagr(returns.slice(start, start + windowMonths));
    const bench = cagr(benchmark.slice(start, start + windowMonths));
    windows.push({
      endMonth: startMonth + start + windowMonths - 1,
      portfolio,
      benchmark: bench,
      excess: portfolio - bench,
    });
  }
  return windows;
}

/** The share of rolling windows in which the portfolio finished ahead. */
export function fractionAhead(windows: readonly RollingWindow[]): number | null {
  if (windows.length === 0) {
    return null;
  }
  return windows.filter((one) => one.excess > 0).length / windows.length;
}
