/**
 * The portfolio path.
 *
 * Weights drift with returns between rebalancing dates and are reset to target on
 * them. The return reported for a month is the capital-weighted return of the
 * holdings at the weights held **entering** that month, which is what a portfolio
 * actually earns and is independent of any contribution schedule. Contributions are
 * deliberately not modelled here: mixing cash flows into a return series produces a
 * money-weighted number that no metric in `metrics.ts` is defined against.
 *
 * Fees are charged geometrically, `(1 + r) * (1 - annual)^(1/12) - 1`, so a year of
 * monthly charges costs exactly the stated annual expense ratio rather than slightly
 * less than it.
 *
 * Weights are **not** normalised. A portfolio adding to 90% holds 10% in cash, and
 * the result says so. Silently scaling a user's weights to 100% would answer a
 * question they did not ask.
 */

import { monthOfYear } from "~/lib/backtest/calendar";
import { commonRange, coversRange, slice } from "~/lib/backtest/series";
import type { MonthRange, RebalanceFrequency, SimulationInput, SimulationResult } from "~/lib/backtest/types";

/** Months between rebalancing dates. `never` is represented by no reset at all. */
function periodMonths(frequency: RebalanceFrequency): number | null {
  switch (frequency) {
    case "monthly":
      return 1;
    case "quarterly":
      return 3;
    case "annually":
      return 12;
    case "never":
      return null;
  }
}

/**
 * Rebalancing is calendar-anchored, not anchored to the start of the test: annual
 * rebalancing happens each January and quarterly in January, April, July and October,
 * so two tests over different windows rebalance on the same dates.
 */
function isRebalanceMonth(month: number, frequency: RebalanceFrequency): boolean {
  const period = periodMonths(frequency);
  return period !== null && monthOfYear(month) % period === 0;
}

export interface MissingHistory {
  readonly symbol: string;
  /** Present when the symbol has no series at all. */
  readonly absent: boolean;
  readonly start?: number;
  readonly end?: number;
}

export class InsufficientHistoryError extends Error {
  readonly missing: readonly MissingHistory[];
  constructor(missing: readonly MissingHistory[]) {
    super(`no common history: ${missing.map((one) => one.symbol).join(", ")}`);
    this.name = "InsufficientHistoryError";
    this.missing = missing;
  }
}

const MONTHS_PER_YEAR = 12;

function monthlyFeeFactor(annual: number): number {
  return (1 - annual) ** (1 / MONTHS_PER_YEAR);
}

/** The window a set of allocations can actually be tested over. */
export function resolvableRange(input: Pick<SimulationInput, "allocations" | "series">): MonthRange | null {
  const held = input.allocations.filter((one) => one.weight !== 0);
  const found = held.map((one) => input.series.get(one.symbol)).filter((one) => one !== undefined);
  if (found.length !== held.length) {
    return null;
  }
  return commonRange(found);
}

export function simulate(input: SimulationInput): SimulationResult {
  const held = input.allocations.filter((one) => one.weight !== 0);

  const missing: MissingHistory[] = [];
  for (const allocation of held) {
    const series = input.series.get(allocation.symbol);
    if (series === undefined) {
      missing.push({ symbol: allocation.symbol, absent: true });
    }
  }
  if (missing.length > 0) {
    throw new InsufficientHistoryError(missing);
  }

  const range = input.range ?? resolvableRange(input);
  if (range === null) {
    throw new InsufficientHistoryError(held.map((one) => ({ symbol: one.symbol, absent: false })));
  }

  const short: MissingHistory[] = [];
  for (const allocation of held) {
    const series = input.series.get(allocation.symbol);
    if (series !== undefined && !coversRange(series, range)) {
      short.push({
        symbol: allocation.symbol,
        absent: false,
        start: series.start,
        end: series.start + series.returns.length - 1,
      });
    }
  }
  if (short.length > 0) {
    throw new InsufficientHistoryError(short);
  }

  // Duplicated symbols are summed rather than rejected: two lines of the same fund
  // are the same holding, and a user who typed it twice meant the total.
  const targets = new Map<string, number>();
  const expenses = new Map<string, number>();
  for (const allocation of held) {
    targets.set(allocation.symbol, (targets.get(allocation.symbol) ?? 0) + allocation.weight);
    if (allocation.expenseRatio !== undefined) {
      expenses.set(allocation.symbol, allocation.expenseRatio);
    }
  }

  const symbols = [...targets.keys()];
  const target = symbols.map((symbol) => targets.get(symbol) ?? 0);
  const invested = target.reduce((sum, weight) => sum + weight, 0);
  const cashWeight = 1 - invested;

  const paths = symbols.map((symbol) => {
    const series = input.series.get(symbol);
    if (series === undefined) {
      throw new InsufficientHistoryError([{ symbol, absent: true }]);
    }
    return slice(series, range);
  });
  const cashPath =
    input.cashSeries !== undefined && coversRange(input.cashSeries, range) ? slice(input.cashSeries, range) : null;

  const feeFactors = symbols.map((symbol) => (input.applyExpenses ? monthlyFeeFactor(expenses.get(symbol) ?? 0) : 1));

  const months = range.end - range.start + 1;
  const returns: number[] = [];
  const growth: number[] = [1];

  // Held capital per symbol, in units of the starting portfolio value, plus cash.
  let holdings = [...target];
  let cash = cashWeight;

  for (let step = 0; step < months; step += 1) {
    const month = range.start + step;
    if (step > 0 && isRebalanceMonth(month, input.rebalance)) {
      const value = holdings.reduce((sum, one) => sum + one, 0) + cash;
      holdings = target.map((weight) => weight * value);
      cash = cashWeight * value;
    }

    const opening = holdings.reduce((sum, one) => sum + one, 0) + cash;
    for (let asset = 0; asset < holdings.length; asset += 1) {
      const monthly = paths[asset]?.[step] ?? 0;
      const factor = feeFactors[asset] ?? 1;
      holdings[asset] = (holdings[asset] ?? 0) * (1 + monthly) * factor;
    }
    cash *= 1 + (cashPath?.[step] ?? 0);

    const closing = holdings.reduce((sum, one) => sum + one, 0) + cash;
    const monthlyReturn = opening === 0 ? 0 : closing / opening - 1;
    returns.push(monthlyReturn);
    growth.push((growth[step] ?? 1) * (1 + monthlyReturn));
  }

  const effectiveExpenseRatio = input.applyExpenses
    ? symbols.reduce((sum, symbol, index) => sum + (target[index] ?? 0) * (expenses.get(symbol) ?? 0), 0)
    : 0;

  return {
    range,
    returns,
    growth,
    weights: targets,
    cashWeight,
    effectiveExpenseRatio,
  };
}
