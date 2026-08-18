/**
 * The lab's whole state, encoded into the query string.
 *
 * The point is a link that reproduces an experiment exactly, with no account and no
 * server. Two rules make that work:
 *
 * 1. **Round-tripping is lossless for anything the parser accepts.** `parseLabConfig`
 *    followed by `toSearchParams` returns the same configuration.
 * 2. **A malformed field falls back to its default and the rest of the link still
 *    loads.** A shared link that half-works is more useful than an error page, and the
 *    interface shows what it dropped.
 *
 * Weights are percentages here, because that is what a reader types.
 */

/** Which comparison the edge is measured against. The two may never be added. */
export type LabBenchmark = "cheap-index" | "own-counterfactual";

export interface LabHolding {
  readonly ticker: string;
  /** Percent of capital. 15 is 15%. */
  readonly percent: number;
}

export interface LabConfig {
  readonly holdings: readonly LabHolding[];
  readonly benchmark: LabBenchmark;
  /** Expected annual edge over the benchmark, basis points. May be negative. */
  readonly edgeBp: number;
  /** Annual standard deviation of the difference, basis points. Never negative. */
  readonly trackingErrorBp: number;
  readonly horizonYears: number;
  /** Fixes the simulated paths, so a link shows the same picture to everyone. */
  readonly seed: number;
}

export const defaultLabConfig: LabConfig = {
  holdings: [],
  benchmark: "cheap-index",
  edgeBp: 46,
  trackingErrorBp: 313,
  horizonYears: 30,
  seed: 1,
};

const SYMBOL = /^[A-Z][A-Z0-9.-]{0,9}$/;

function normaliseTicker(raw: string): string | null {
  const ticker = raw.trim().toUpperCase();
  return SYMBOL.test(ticker) ? ticker : null;
}

/** Two decimal places is the finest weight the interface offers. */
function roundPercent(value: number): number {
  return Math.round(value * 100) / 100;
}

/**
 * `VTI:20,AVLV:15` → holdings. A line with an unreadable ticker or weight is dropped
 * rather than defaulting to zero, so a typo cannot silently become a real position.
 */
export function parseHoldings(raw: string): LabHolding[] {
  const holdings: LabHolding[] = [];
  for (const part of raw.split(",")) {
    if (part.trim() === "") {
      continue;
    }
    const [tickerPart = "", percentPart = ""] = part.split(":");
    const ticker = normaliseTicker(tickerPart);
    // `Number("")` is 0, so an empty weight would otherwise become a real 0% line.
    const percent = percentPart.trim() === "" ? Number.NaN : Number(percentPart);
    if (ticker === null || !Number.isFinite(percent) || percent < 0) {
      continue;
    }
    const existing = holdings.findIndex((one) => one.ticker === ticker);
    if (existing >= 0) {
      holdings[existing] = { ticker, percent: roundPercent((holdings[existing]?.percent ?? 0) + percent) };
      continue;
    }
    holdings.push({ ticker, percent: roundPercent(percent) });
  }
  return holdings;
}

export function serialiseHoldings(holdings: readonly LabHolding[]): string {
  return holdings.map((one) => `${one.ticker}:${roundPercent(one.percent)}`).join(",");
}

function numberOr(
  raw: string | null,
  fallback: number,
  { min = Number.NEGATIVE_INFINITY, max = Number.POSITIVE_INFINITY } = {}
): number {
  const parsed = Number(raw);
  if (raw === null || raw.trim() === "" || !Number.isFinite(parsed) || parsed < min || parsed > max) {
    return fallback;
  }
  return parsed;
}

const BENCHMARK_CODE: Readonly<Record<LabBenchmark, string>> = {
  "cheap-index": "index",
  "own-counterfactual": "self",
};

export function parseLabConfig(search: string | URLSearchParams): LabConfig {
  const params = typeof search === "string" ? new URLSearchParams(search) : search;
  const benchmark = params.get("b") === BENCHMARK_CODE["own-counterfactual"] ? "own-counterfactual" : "cheap-index";

  return {
    holdings: parseHoldings(params.get("p") ?? ""),
    benchmark,
    edgeBp: numberOr(params.get("e"), defaultLabConfig.edgeBp, { min: -1000, max: 1000 }),
    trackingErrorBp: numberOr(params.get("te"), defaultLabConfig.trackingErrorBp, { min: 0, max: 3000 }),
    horizonYears: numberOr(params.get("h"), defaultLabConfig.horizonYears, { min: 1, max: 60 }),
    seed: Math.round(numberOr(params.get("s"), defaultLabConfig.seed, { min: 1, max: 9999 })),
  };
}

/** Only what differs from the defaults is written, so a plain link stays short. */
export function toSearchParams(config: LabConfig): URLSearchParams {
  const params = new URLSearchParams();
  if (config.holdings.length > 0) {
    params.set("p", serialiseHoldings(config.holdings));
  }
  if (config.benchmark !== defaultLabConfig.benchmark) {
    params.set("b", BENCHMARK_CODE[config.benchmark]);
  }
  if (config.edgeBp !== defaultLabConfig.edgeBp) {
    params.set("e", String(config.edgeBp));
  }
  if (config.trackingErrorBp !== defaultLabConfig.trackingErrorBp) {
    params.set("te", String(config.trackingErrorBp));
  }
  if (config.horizonYears !== defaultLabConfig.horizonYears) {
    params.set("h", String(config.horizonYears));
  }
  if (config.seed !== defaultLabConfig.seed) {
    params.set("s", String(config.seed));
  }
  return params;
}

export function toLabHref(config: LabConfig, path = "/lab"): string {
  const query = toSearchParams(config).toString();
  return query === "" ? path : `${path}?${query}`;
}

export function totalPercent(holdings: readonly LabHolding[]): number {
  return roundPercent(holdings.reduce((sum, one) => sum + one.percent, 0));
}

/** Scales the weights to 100% and keeps the total exact by adjusting the last line. */
export function normalise(holdings: readonly LabHolding[]): LabHolding[] {
  const total = totalPercent(holdings);
  if (total <= 0 || holdings.length === 0) {
    return [...holdings];
  }
  const scaled = holdings.map((one) => ({ ticker: one.ticker, percent: roundPercent((one.percent / total) * 100) }));
  const drift = roundPercent(100 - totalPercent(scaled));
  const last = scaled[scaled.length - 1];
  if (last !== undefined && drift !== 0) {
    scaled[scaled.length - 1] = { ticker: last.ticker, percent: roundPercent(last.percent + drift) };
  }
  return scaled;
}
