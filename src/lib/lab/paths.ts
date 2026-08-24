/**
 * What an edge and a tracking error actually feel like to hold.
 *
 * This is a **simulation from stated assumptions, not a history**. Nothing in it is
 * evidence about any fund. Its whole job is to answer the question a table of expected
 * returns cannot: if a portfolio really does earn `edge` basis points a year over a
 * benchmark, with `trackingError` basis points of annual dispersion around it, how long
 * can it sit behind on the way there?
 *
 * The model is the same one `src/lib/horizon.ts` uses in closed form — relative
 * performance as a random walk with drift, log-normal in the ratio — so the fraction of
 * paths ahead at a horizon reproduces `probabilityOfOutperformance` rather than
 * competing with it. Paths add the shape of the journey, not a second answer.
 *
 * Everything is seeded. The same inputs give the same picture on every machine, every
 * reload and in every test, so a reader can quote a number off it.
 */

import { normalPpf } from "~/lib/normal";

/** Mulberry32. Small, fast, and identical everywhere: the point is reproducibility. */
function seededRandom(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const MONTHS_PER_YEAR = 12;
const BP = 10_000;

export interface RelativePathInput {
  readonly edgeBp: number;
  readonly trackingErrorBp: number;
  readonly horizonYears: number;
  readonly paths: number;
  readonly seed: number;
}

export interface RelativePathResult {
  readonly months: number;
  /** Percentile bands of relative wealth, one value per month end, starting at 1. */
  readonly bands: Readonly<Record<PercentileKey, readonly number[]>>;
  /** Share of paths ending above 1. Reproduces the closed-form probability. */
  readonly fractionAhead: number;
  /** Median longest run of months spent below the previous relative-wealth peak. */
  readonly medianLongestDroughtMonths: number;
  /** Median worst shortfall against the previous relative peak, as a fraction. */
  readonly medianWorstShortfall: number;
  /** The share of paths that spend at least three years behind at some point. */
  readonly fractionWithLongDrought: number;
}

export type PercentileKey = "p05" | "p25" | "p50" | "p75" | "p95";

const PERCENTILES: Readonly<Record<PercentileKey, number>> = {
  p05: 0.05,
  p25: 0.25,
  p50: 0.5,
  p75: 0.75,
  p95: 0.95,
};

/** Linear-interpolated percentile of an already-sorted array. */
export function percentileOfSorted(sorted: readonly number[], fraction: number): number {
  if (sorted.length === 0) {
    return Number.NaN;
  }
  const position = (sorted.length - 1) * fraction;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  const low = sorted[lower] ?? 0;
  const high = sorted[upper] ?? low;
  return low + (high - low) * (position - lower);
}

const LONG_DROUGHT_MONTHS = 36;

export function simulateRelativePaths(input: RelativePathInput): RelativePathResult {
  const months = Math.max(1, Math.round(input.horizonYears * MONTHS_PER_YEAR));
  const pathCount = Math.max(1, Math.round(input.paths));

  // Arithmetic drift and dispersion of the log relative wealth. The closed form in
  // `horizon.ts` treats the edge as a drift in the same units, so they agree.
  const drift = input.edgeBp / BP / MONTHS_PER_YEAR;
  const dispersion = input.trackingErrorBp / BP / Math.sqrt(MONTHS_PER_YEAR);

  const random = seededRandom(input.seed);
  const columns: number[][] = Array.from({ length: months + 1 }, () => []);
  const droughts: number[] = [];
  const shortfalls: number[] = [];
  let ahead = 0;
  let longDroughts = 0;

  for (let path = 0; path < pathCount; path += 1) {
    let logWealth = 0;
    let peak = 0;
    let currentDrought = 0;
    let longestDrought = 0;
    let worstShortfall = 0;
    columns[0]?.push(1);

    for (let month = 1; month <= months; month += 1) {
      // Inverse-CDF sampling: exact normals from one uniform, and no rejection loop
      // whose iteration count would depend on the seed.
      const uniform = Math.min(1 - 1e-12, Math.max(1e-12, random()));
      logWealth += drift + dispersion * normalPpf(uniform);
      columns[month]?.push(Math.exp(logWealth));

      if (logWealth >= peak) {
        peak = logWealth;
        currentDrought = 0;
      } else {
        currentDrought += 1;
        longestDrought = Math.max(longestDrought, currentDrought);
        worstShortfall = Math.min(worstShortfall, Math.expm1(logWealth - peak));
      }
    }

    if (logWealth > 0) {
      ahead += 1;
    }
    if (longestDrought >= LONG_DROUGHT_MONTHS) {
      longDroughts += 1;
    }
    droughts.push(longestDrought);
    shortfalls.push(worstShortfall);
  }

  const bands = {} as Record<PercentileKey, number[]>;
  for (const key of Object.keys(PERCENTILES) as PercentileKey[]) {
    bands[key] = [];
  }
  for (const column of columns) {
    const sorted = [...column].sort((a, b) => a - b);
    for (const [key, fraction] of Object.entries(PERCENTILES) as [PercentileKey, number][]) {
      bands[key]?.push(percentileOfSorted(sorted, fraction));
    }
  }

  const sortedDroughts = [...droughts].sort((a, b) => a - b);
  const sortedShortfalls = [...shortfalls].sort((a, b) => a - b);

  return {
    months,
    bands,
    fractionAhead: ahead / pathCount,
    medianLongestDroughtMonths: percentileOfSorted(sortedDroughts, 0.5),
    medianWorstShortfall: percentileOfSorted(sortedShortfalls, 0.5),
    fractionWithLongDrought: longDroughts / pathCount,
  };
}
