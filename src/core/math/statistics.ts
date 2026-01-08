import type { CovarianceMatrix, PriceHistory, ReturnsData } from "~/types";

// Convert price history to logarithmic returns
export function calculateLogReturns(prices: number[]): number[] {
  const returns: number[] = [];
  for (let i = 1; i < prices.length; i++) {
    const prevPrice = prices[i - 1];
    const currentPrice = prices[i];
    if (prevPrice && currentPrice && prevPrice > 0) {
      returns.push(Math.log(currentPrice / prevPrice));
    }
  }
  return returns;
}

// Convert PriceHistory to ReturnsData
export function priceHistoryToReturns(history: PriceHistory): ReturnsData {
  return {
    ticker: history.ticker,
    returns: calculateLogReturns(history.prices),
  };
}

// Calculate mean of an array
export function mean(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}

// Calculate variance of an array (sample variance)
export function variance(values: number[]): number {
  if (values.length < 2) return 0;
  const m = mean(values);
  const squaredDiffs = values.map((v) => (v - m) ** 2);
  return squaredDiffs.reduce((sum, v) => sum + v, 0) / (values.length - 1);
}

// Calculate standard deviation
export function standardDeviation(values: number[]): number {
  return Math.sqrt(variance(values));
}

// Annualize weekly returns
export function annualizeReturn(weeklyReturn: number): number {
  return weeklyReturn * 52;
}

// Annualize weekly volatility
export function annualizeVolatility(weeklyVolatility: number): number {
  return weeklyVolatility * Math.sqrt(52);
}

// Calculate covariance between two return series
export function covariance(x: number[], y: number[]): number {
  const n = Math.min(x.length, y.length);
  if (n < 2) return 0;

  const meanX = mean(x.slice(0, n));
  const meanY = mean(y.slice(0, n));

  let sum = 0;
  for (let i = 0; i < n; i++) {
    sum += ((x[i] ?? 0) - meanX) * ((y[i] ?? 0) - meanY);
  }

  return sum / (n - 1);
}

// Calculate covariance matrix from multiple return series
export function calculateCovarianceMatrix(returnsData: ReturnsData[]): CovarianceMatrix {
  const n = returnsData.length;
  const tickers = returnsData.map((r) => r.ticker);
  const matrix: number[][] = Array.from({ length: n }, () => Array(n).fill(0));

  for (let i = 0; i < n; i++) {
    for (let j = 0; j <= i; j++) {
      const cov = covariance(returnsData[i]?.returns ?? [], returnsData[j]?.returns ?? []);
      // Annualize the covariance (weekly -> annual)
      const annualizedCov = cov * 52;
      matrix[i]![j] = annualizedCov;
      matrix[j]![i] = annualizedCov; // Symmetric
    }
  }

  return { tickers, matrix };
}

// Calculate beta of an asset vs a benchmark
export function calculateBeta(assetReturns: number[], benchmarkReturns: number[]): number {
  const cov = covariance(assetReturns, benchmarkReturns);
  const benchmarkVar = variance(benchmarkReturns);

  if (benchmarkVar === 0) return 1;
  return cov / benchmarkVar;
}

// Calculate betas for multiple assets vs SPY
export function calculateBetas(returnsData: ReturnsData[], benchmarkTicker = "SPY"): Record<string, number> {
  const benchmark = returnsData.find((r) => r.ticker === benchmarkTicker);
  if (!benchmark) {
    // Return 1 for all if no benchmark found
    return Object.fromEntries(returnsData.map((r) => [r.ticker, 1]));
  }

  const betas: Record<string, number> = {};
  for (const data of returnsData) {
    if (data.ticker === benchmarkTicker) {
      betas[data.ticker] = 1;
    } else {
      betas[data.ticker] = calculateBeta(data.returns, benchmark.returns);
    }
  }

  return betas;
}

// Calculate expected returns using CAPM
export function calculateCAPMReturns(
  betas: Record<string, number>,
  riskFreeRate: number,
  marketReturn = 0.1 // Expected market return (historical average ~10%)
): Record<string, number> {
  const marketPremium = marketReturn - riskFreeRate;
  const expectedReturns: Record<string, number> = {};

  for (const [ticker, beta] of Object.entries(betas)) {
    expectedReturns[ticker] = riskFreeRate + beta * marketPremium;
  }

  return expectedReturns;
}

// Calculate annualized volatility from returns data
export function calculateAnnualizedVolatility(returns: number[]): number {
  const weeklyVol = standardDeviation(returns);
  return annualizeVolatility(weeklyVol);
}

// Calculate volatilities for multiple assets
export function calculateVolatilities(returnsData: ReturnsData[]): Record<string, number> {
  const volatilities: Record<string, number> = {};
  for (const data of returnsData) {
    volatilities[data.ticker] = calculateAnnualizedVolatility(data.returns);
  }
  return volatilities;
}

// Calculate Sharpe Ratio
export function calculateSharpeRatio(
  portfolioReturn: number,
  portfolioVolatility: number,
  riskFreeRate: number
): number {
  if (portfolioVolatility === 0) return 0;
  return (portfolioReturn - riskFreeRate) / portfolioVolatility;
}

// Calculate portfolio return from weights and expected returns
export function calculatePortfolioReturn(
  weights: Record<string, number>,
  expectedReturns: Record<string, number>
): number {
  let portfolioReturn = 0;
  for (const [ticker, weight] of Object.entries(weights)) {
    portfolioReturn += weight * (expectedReturns[ticker] ?? 0);
  }
  return portfolioReturn;
}

// Calculate portfolio volatility from weights and covariance matrix
export function calculatePortfolioVolatility(weights: Record<string, number>, covMatrix: CovarianceMatrix): number {
  const { tickers, matrix } = covMatrix;
  let variance = 0;

  for (let i = 0; i < tickers.length; i++) {
    for (let j = 0; j < tickers.length; j++) {
      const tickerI = tickers[i];
      const tickerJ = tickers[j];
      if (tickerI && tickerJ) {
        const wi = weights[tickerI] ?? 0;
        const wj = weights[tickerJ] ?? 0;
        variance += wi * wj * (matrix[i]?.[j] ?? 0);
      }
    }
  }

  return Math.sqrt(Math.max(0, variance));
}
