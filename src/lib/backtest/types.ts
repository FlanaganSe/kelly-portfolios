/**
 * The vocabulary of the portfolio engine.
 *
 * Every series here is a **monthly total return**, expressed as a decimal fraction
 * (0.0123 is +1.23% for the month), and every function in this directory is pure.
 * Nothing in here knows where a series came from; the provenance of a series is the
 * content layer's problem, and a series with no honest source must never reach it.
 */

/** Months since 1970-01. The engine's internal clock. */
export type MonthIndex = number;

/** A contiguous run of monthly total returns starting at `start`. No gaps allowed. */
export interface ReturnSeries {
  readonly id: string;
  /** Month of the first observation, as a `MonthIndex`. */
  readonly start: MonthIndex;
  readonly returns: readonly number[];
}

/** An inclusive span of months. */
export interface MonthRange {
  readonly start: MonthIndex;
  readonly end: MonthIndex;
}

/** How often the engine returns the portfolio to its target weights. */
export type RebalanceFrequency = "monthly" | "quarterly" | "annually" | "never";

/** One line of a portfolio. `weight` is a fraction of capital, not a percentage. */
export interface Allocation {
  readonly symbol: string;
  readonly weight: number;
  /** Annual expense ratio as a decimal fraction. Omitted means no fee is charged. */
  readonly expenseRatio?: number;
}

export interface SimulationInput {
  readonly allocations: readonly Allocation[];
  /** Every series the allocations reference, by symbol. */
  readonly series: ReadonlyMap<string, ReturnSeries>;
  readonly rebalance: RebalanceFrequency;
  /** Restricts the test. Defaults to the common history of the allocations. */
  readonly range?: MonthRange;
  /** Charge each holding's expense ratio. Off means gross-of-fee. */
  readonly applyExpenses: boolean;
  /**
   * What unallocated capital earns when the weights sum to less than one. A missing
   * series means it earns nothing, which is a real assumption and is reported.
   */
  readonly cashSeries?: ReturnSeries;
}

export interface SimulationResult {
  readonly range: MonthRange;
  /** Monthly total returns of the portfolio, time-weighted, net of any fee charged. */
  readonly returns: readonly number[];
  /** Growth of 1 unit, length `returns.length + 1`, starting at 1. */
  readonly growth: readonly number[];
  /** The weight actually used per symbol after normalisation is declined. */
  readonly weights: ReadonlyMap<string, number>;
  /** Capital left in cash because the weights summed to less than one. */
  readonly cashWeight: number;
  /** Weighted expense ratio actually charged, annual decimal. Zero when off. */
  readonly effectiveExpenseRatio: number;
}
