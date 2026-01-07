import type { PriceHistory } from "~/types";
import { ASSET_DEFINITIONS } from "./mockAssets";

// Correlation matrix for generating correlated returns
// Order: SPY, QQQ, TLT, GLD, VNQ, BTC, ETH, HYG, LQD, CASH
const CORRELATION_MATRIX: number[][] = [
  //       SPY   QQQ   TLT   GLD   VNQ   BTC   ETH   HYG   LQD   CASH
  /* SPY */ [1.0, 0.9, -0.3, 0.05, 0.75, 0.45, 0.42, 0.6, 0.25, 0.0],
  /* QQQ */ [0.9, 1.0, -0.35, 0.0, 0.65, 0.5, 0.48, 0.5, 0.2, 0.0],
  /* TLT */ [-0.3, -0.35, 1.0, 0.3, -0.15, -0.1, -0.1, 0.4, 0.7, 0.0],
  /* GLD */ [0.05, 0.0, 0.3, 1.0, 0.1, 0.25, 0.22, 0.15, 0.25, 0.0],
  /* VNQ */ [0.75, 0.65, -0.15, 0.1, 1.0, 0.35, 0.32, 0.55, 0.35, 0.0],
  /* BTC */ [0.45, 0.5, -0.1, 0.25, 0.35, 1.0, 0.85, 0.3, 0.1, 0.0],
  /* ETH */ [0.42, 0.48, -0.1, 0.22, 0.32, 0.85, 1.0, 0.28, 0.08, 0.0],
  /* HYG */ [0.6, 0.5, 0.4, 0.15, 0.55, 0.3, 0.28, 1.0, 0.7, 0.0],
  /* LQD */ [0.25, 0.2, 0.7, 0.25, 0.35, 0.1, 0.08, 0.7, 1.0, 0.0],
  /* CASH */ [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
];

// Cholesky decomposition for generating correlated random variables
function choleskyDecomposition(matrix: number[][]): number[][] {
  const n = matrix.length;
  const L: number[][] = Array.from({ length: n }, () => Array(n).fill(0));

  for (let i = 0; i < n; i++) {
    for (let j = 0; j <= i; j++) {
      let sum = 0;
      for (let k = 0; k < j; k++) {
        sum += (L[i]?.[k] ?? 0) * (L[j]?.[k] ?? 0);
      }

      if (i === j) {
        const val = (matrix[i]?.[i] ?? 0) - sum;
        L[i]![j] = Math.sqrt(Math.max(0, val));
      } else {
        const ljj = L[j]?.[j] ?? 1;
        L[i]![j] = ljj === 0 ? 0 : ((matrix[i]?.[j] ?? 0) - sum) / ljj;
      }
    }
  }

  return L;
}

// Seeded random number generator for reproducibility
class SeededRandom {
  private seed: number;

  constructor(seed: number) {
    this.seed = seed;
  }

  // Mulberry32 PRNG
  next(): number {
    let t = (this.seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }

  // Box-Muller transform for normal distribution
  nextGaussian(): number {
    const u1 = this.next();
    const u2 = this.next();
    return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  }
}

// Generate weekly dates for the past 2 years
function generateDates(weeks: number): string[] {
  const dates: string[] = [];
  const endDate = new Date("2024-12-27"); // Fixed end date for reproducibility

  for (let i = weeks - 1; i >= 0; i--) {
    const date = new Date(endDate);
    date.setDate(date.getDate() - i * 7);
    dates.push(date.toISOString().split("T")[0]!);
  }

  return dates;
}

// Generate correlated returns
function generateCorrelatedReturns(
  rng: SeededRandom,
  choleskyL: number[][],
  weeklyVolatilities: number[],
  weeklyReturns: number[]
): number[] {
  const n = choleskyL.length;
  const independent: number[] = [];

  // Generate independent standard normal random variables
  for (let i = 0; i < n; i++) {
    independent.push(rng.nextGaussian());
  }

  // Transform to correlated variables
  const correlated: number[] = [];
  for (let i = 0; i < n; i++) {
    let sum = 0;
    for (let j = 0; j <= i; j++) {
      sum += (choleskyL[i]?.[j] ?? 0) * (independent[j] ?? 0);
    }
    // Apply weekly volatility and drift
    const weeklyReturn = (weeklyReturns[i] ?? 0) + (weeklyVolatilities[i] ?? 0) * sum;
    correlated.push(weeklyReturn);
  }

  return correlated;
}

// Generate mock price history
export function generateMockHistory(seed = 42): Map<string, PriceHistory> {
  const NUM_WEEKS = 104; // 2 years
  const rng = new SeededRandom(seed);
  const choleskyL = choleskyDecomposition(CORRELATION_MATRIX);
  const dates = generateDates(NUM_WEEKS);

  // Convert annual volatility to weekly and annual return to weekly
  const weeklyVolatilities = ASSET_DEFINITIONS.map((a) => a.annualVolatility / Math.sqrt(52));
  const weeklyReturns = ASSET_DEFINITIONS.map((a) => a.expectedAnnualReturn / 52);

  // Initialize prices with base prices
  const prices: number[][] = ASSET_DEFINITIONS.map((a) => [a.basePrice]);

  // Generate price paths
  for (let week = 1; week < NUM_WEEKS; week++) {
    const returns = generateCorrelatedReturns(rng, choleskyL, weeklyVolatilities, weeklyReturns);

    for (let i = 0; i < ASSET_DEFINITIONS.length; i++) {
      const prevPrice = prices[i]?.[week - 1] ?? 1;
      // Use geometric returns (log-normal)
      const newPrice = prevPrice * Math.exp(returns[i] ?? 0);
      prices[i]!.push(newPrice);
    }
  }

  // Create PriceHistory map
  const historyMap = new Map<string, PriceHistory>();

  for (let i = 0; i < ASSET_DEFINITIONS.length; i++) {
    const def = ASSET_DEFINITIONS[i];
    const assetPrices = prices[i];
    if (def && assetPrices) {
      historyMap.set(def.id, {
        ticker: def.id,
        dates: dates,
        prices: assetPrices,
      });
    }
  }

  return historyMap;
}

// Pre-generated history for consistent behavior
let cachedHistory: Map<string, PriceHistory> | null = null;

export function getMockHistory(): Map<string, PriceHistory> {
  if (!cachedHistory) {
    cachedHistory = generateMockHistory(42);
  }
  return cachedHistory;
}

// Get history for specific tickers
export function getHistoryForTickers(tickers: string[]): PriceHistory[] {
  const history = getMockHistory();
  return tickers.map((ticker) => history.get(ticker)).filter((h): h is PriceHistory => h !== undefined);
}
