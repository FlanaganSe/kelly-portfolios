/**
 * The lab's whole state, encoded into the query string.
 *
 * The point is a link that reproduces an experiment exactly, with no account and no
 * server. Two rules make that work:
 *
 * 1. **Round-tripping is lossless for anything the parser accepts.** `parseLabConfig`
 *    followed by `toSearchParams` returns the same configuration.
 * 2. **A malformed field falls back to the default and the rest of the link still
 *    loads.** A shared URL that half-works is more useful than an error page, and the
 *    interface shows what was dropped.
 *
 * Weights are held as percentages here, because that is what the reader types. The
 * engine takes fractions, and `toAllocations` is the only place the conversion happens.
 */

import { toMonthIndex, toYearMonth } from "~/lib/backtest/calendar";
import type { Allocation, MonthRange, RebalanceFrequency } from "~/lib/backtest/types";

export interface LabHolding {
  readonly symbol: string;
  /** Percent of capital. 15 is 15%. */
  readonly percent: number;
}

export interface LabConfig {
  readonly holdings: readonly LabHolding[];
  readonly benchmark: string;
  readonly rebalance: RebalanceFrequency;
  readonly applyExpenses: boolean;
  /** `null` means the full common history of the holdings. */
  readonly from: string | null;
  readonly to: string | null;
  /** The starting investment, for the growth chart only. Affects no rate. */
  readonly initial: number;
}

export const DEFAULT_BENCHMARK = "VT";

export const defaultLabConfig: LabConfig = {
  holdings: [],
  benchmark: DEFAULT_BENCHMARK,
  rebalance: "annually",
  applyExpenses: true,
  from: null,
  to: null,
  initial: 10_000,
};

const REBALANCE_VALUES: readonly RebalanceFrequency[] = ["monthly", "quarterly", "annually", "never"];

function isRebalance(value: string): value is RebalanceFrequency {
  return (REBALANCE_VALUES as readonly string[]).includes(value);
}

const SYMBOL = /^[A-Z][A-Z0-9.-]{0,9}$/;
const YEAR_MONTH = /^\d{4}-\d{2}$/;

function normaliseSymbol(raw: string): string | null {
  const symbol = raw.trim().toUpperCase();
  return SYMBOL.test(symbol) ? symbol : null;
}

/** Two decimal places is the finest weight the interface offers. */
function roundPercent(value: number): number {
  return Math.round(value * 100) / 100;
}

/**
 * `VTI:20,AVLV:15` → holdings. A line with an unreadable symbol or weight is dropped
 * rather than defaulting to zero, so a typo cannot silently become a real position.
 */
export function parseHoldings(raw: string): LabHolding[] {
  const holdings: LabHolding[] = [];
  for (const part of raw.split(",")) {
    if (part.trim() === "") {
      continue;
    }
    const [symbolPart = "", percentPart = ""] = part.split(":");
    const symbol = normaliseSymbol(symbolPart);
    // `Number("")` is 0, so an empty weight would otherwise become a real 0% line.
    const percent = percentPart.trim() === "" ? Number.NaN : Number(percentPart);
    if (symbol === null || !Number.isFinite(percent) || percent < 0) {
      continue;
    }
    const existing = holdings.findIndex((one) => one.symbol === symbol);
    if (existing >= 0) {
      const previous = holdings[existing]?.percent ?? 0;
      holdings[existing] = { symbol, percent: roundPercent(previous + percent) };
      continue;
    }
    holdings.push({ symbol, percent: roundPercent(percent) });
  }
  return holdings;
}

export function serialiseHoldings(holdings: readonly LabHolding[]): string {
  return holdings.map((one) => `${one.symbol}:${roundPercent(one.percent)}`).join(",");
}

function parseMonth(raw: string | null): string | null {
  if (raw === null || !YEAR_MONTH.test(raw)) {
    return null;
  }
  try {
    toMonthIndex(raw);
    return raw;
  } catch {
    return null;
  }
}

export function parseLabConfig(search: string | URLSearchParams): LabConfig {
  const params = typeof search === "string" ? new URLSearchParams(search) : search;
  const rebalance = params.get("r") ?? "";
  const initial = Number(params.get("v"));
  const benchmark = normaliseSymbol(params.get("b") ?? "");

  return {
    holdings: parseHoldings(params.get("p") ?? ""),
    benchmark: benchmark ?? defaultLabConfig.benchmark,
    rebalance: isRebalance(rebalance) ? rebalance : defaultLabConfig.rebalance,
    // Fees are charged unless the link says otherwise, so a truncated link is
    // pessimistic rather than flattering.
    applyExpenses: params.get("f") !== "0",
    from: parseMonth(params.get("from")),
    to: parseMonth(params.get("to")),
    initial: Number.isFinite(initial) && initial > 0 ? initial : defaultLabConfig.initial,
  };
}

/** Only what differs from the defaults is written, so a plain link stays short. */
export function toSearchParams(config: LabConfig): URLSearchParams {
  const params = new URLSearchParams();
  if (config.holdings.length > 0) {
    params.set("p", serialiseHoldings(config.holdings));
  }
  if (config.benchmark !== defaultLabConfig.benchmark) {
    params.set("b", config.benchmark);
  }
  if (config.rebalance !== defaultLabConfig.rebalance) {
    params.set("r", config.rebalance);
  }
  if (!config.applyExpenses) {
    params.set("f", "0");
  }
  if (config.from !== null) {
    params.set("from", config.from);
  }
  if (config.to !== null) {
    params.set("to", config.to);
  }
  if (config.initial !== defaultLabConfig.initial) {
    params.set("v", String(config.initial));
  }
  return params;
}

export function toLabHref(config: LabConfig, path = "/lab"): string {
  const query = toSearchParams(config).toString();
  return query === "" ? path : `${path}?${query}`;
}

export const totalPercent = (holdings: readonly LabHolding[]): number =>
  roundPercent(holdings.reduce((sum, one) => sum + one.percent, 0));

/** Scales the weights to 100% and keeps the total exact by adjusting the last line. */
export function normalise(holdings: readonly LabHolding[]): LabHolding[] {
  const total = totalPercent(holdings);
  if (total <= 0 || holdings.length === 0) {
    return [...holdings];
  }
  const scaled = holdings.map((one) => ({ symbol: one.symbol, percent: roundPercent((one.percent / total) * 100) }));
  const drift = roundPercent(100 - totalPercent(scaled));
  const last = scaled[scaled.length - 1];
  if (last !== undefined && drift !== 0) {
    scaled[scaled.length - 1] = { symbol: last.symbol, percent: roundPercent(last.percent + drift) };
  }
  return scaled;
}

export function toAllocations(
  holdings: readonly LabHolding[],
  expenseRatioOf: (symbol: string) => number | undefined
): Allocation[] {
  return holdings.map((one) => {
    const expenseRatio = expenseRatioOf(one.symbol);
    return expenseRatio === undefined
      ? { symbol: one.symbol, weight: one.percent / 100 }
      : { symbol: one.symbol, weight: one.percent / 100, expenseRatio };
  });
}

/** The window the config asks for, clipped to what the data can actually supply. */
export function requestedRange(config: LabConfig, available: MonthRange): MonthRange {
  const from = config.from === null ? available.start : Math.max(available.start, toMonthIndex(config.from));
  const to = config.to === null ? available.end : Math.min(available.end, toMonthIndex(config.to));
  return from > to ? available : { start: from, end: to };
}

export const monthLabel = toYearMonth;
