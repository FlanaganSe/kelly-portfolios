import {
  calculateBetas,
  calculateCAPMReturns,
  calculateCovarianceMatrix,
  calculatePortfolioReturn,
  calculatePortfolioVolatility,
  calculateSharpeRatio,
  calculateVolatilities,
  priceHistoryToReturns,
} from "~/core/math/statistics";
import type {
  CovarianceMatrix,
  EfficientFrontierPoint,
  OptimizationResult,
  PortfolioConfig,
  PriceHistory,
  ReturnsData,
} from "~/types";

// Result from the QP solver
interface QPResult {
  weights: Record<string, number>;
  utility: number;
}

/**
 * Solve the Mean-Variance Optimization problem using Quadratic Programming
 *
 * Maximize: U = w^T * mu_net - (gamma/2) * w^T * Sigma * w
 *
 * Subject to:
 * - w_i >= 0 (long only)
 * - sum(w_i) >= 0.1 (minimum investment)
 * - sum(w_i) <= maxLeverage
 *
 * The optimization uses an active set method with analytical solutions
 * for subproblems.
 */
export function solveQP(
  tickers: string[],
  expectedReturns: Record<string, number>,
  covMatrix: CovarianceMatrix,
  riskAversion: number,
  maxLeverage: number,
  borrowRate: number
): QPResult {
  const n = tickers.length;

  // Adjust returns for leverage cost: q_i = E[R_i] - R_borrow
  const adjustedReturns: number[] = tickers.map((t) => (expectedReturns[t] ?? 0) - borrowRate);

  // Get covariance matrix in array form for the tickers
  const sigmaMatrix: number[][] = [];
  for (let i = 0; i < n; i++) {
    const row: number[] = [];
    sigmaMatrix[i] = row;
    for (let j = 0; j < n; j++) {
      const idxI = covMatrix.tickers.indexOf(tickers[i]!);
      const idxJ = covMatrix.tickers.indexOf(tickers[j]!);
      if (idxI >= 0 && idxJ >= 0) {
        row[j] = covMatrix.matrix[idxI]?.[idxJ] ?? 0;
      } else {
        row[j] = i === j ? 0.04 : 0; // Default variance
      }
    }
  }

  // Use coordinate descent with projection for constrained QP
  const weights = solveConstrainedQP(adjustedReturns, sigmaMatrix, riskAversion, maxLeverage, n);

  // Calculate utility for the solution
  const utility = calculateUtility(weights, adjustedReturns, sigmaMatrix, riskAversion);

  // Convert weights array to record
  const weightRecord: Record<string, number> = {};
  for (let i = 0; i < n; i++) {
    const ticker = tickers[i];
    if (ticker && (weights[i] ?? 0) > 0.001) {
      // Filter out negligible weights
      weightRecord[ticker] = weights[i]!;
    }
  }

  return { weights: weightRecord, utility };
}

/**
 * Solve constrained QP using projected gradient descent with momentum
 */
function solveConstrainedQP(
  returns: number[],
  sigma: number[][],
  gamma: number,
  maxLeverage: number,
  n: number
): number[] {
  const maxIter = 1000;
  const tolerance = 1e-8;
  const learningRate = 0.01;

  // Initialize with equal weights
  let weights = Array(n).fill(maxLeverage / n);
  let prevWeights = [...weights];
  const momentum = Array(n).fill(0);
  const beta = 0.9; // Momentum coefficient

  for (let iter = 0; iter < maxIter; iter++) {
    // Compute gradient: gradient = gamma * Sigma * w - returns
    const gradient = computeGradient(weights, returns, sigma, gamma);

    // Update with momentum
    for (let i = 0; i < n; i++) {
      momentum[i] = beta * (momentum[i] ?? 0) + (1 - beta) * (gradient[i] ?? 0);
      weights[i] = (weights[i] ?? 0) - learningRate * (momentum[i] ?? 0);
    }

    // Project onto constraints
    weights = projectToConstraints(weights, maxLeverage);

    // Check convergence
    let maxDiff = 0;
    for (let i = 0; i < n; i++) {
      maxDiff = Math.max(maxDiff, Math.abs((weights[i] ?? 0) - (prevWeights[i] ?? 0)));
    }

    if (maxDiff < tolerance) break;

    prevWeights = [...weights];
  }

  return weights;
}

/**
 * Compute gradient of the objective function
 * For minimization: gradient = gamma * Sigma * w - q
 */
function computeGradient(weights: number[], returns: number[], sigma: number[][], gamma: number): number[] {
  const n = weights.length;
  const gradient: number[] = [];

  for (let i = 0; i < n; i++) {
    let sigmaW = 0;
    for (let j = 0; j < n; j++) {
      sigmaW += (sigma[i]?.[j] ?? 0) * (weights[j] ?? 0);
    }
    // Gradient for maximization (negative of minimization gradient)
    gradient[i] = gamma * sigmaW - (returns[i] ?? 0);
  }

  return gradient;
}

/**
 * Project weights onto the constraint set:
 * - w_i >= 0
 * - sum(w_i) >= 0.1
 * - sum(w_i) <= maxLeverage
 */
function projectToConstraints(weights: number[], maxLeverage: number): number[] {
  const n = weights.length;
  const minInvestment = 0.1;

  // Step 1: Project to non-negative
  const projected = weights.map((w) => Math.max(0, w));

  // Step 2: Check sum constraints
  const sum = projected.reduce((a, b) => a + b, 0);

  if (sum < minInvestment) {
    // Scale up to minimum investment
    const scale = minInvestment / (sum || 0.001);
    return projected.map((w) => w * scale);
  }

  if (sum > maxLeverage) {
    // Scale down to max leverage
    const scale = maxLeverage / sum;
    return projected.map((w) => w * scale);
  }

  return projected;
}

/**
 * Calculate the utility value for given weights
 */
function calculateUtility(weights: number[], returns: number[], sigma: number[][], gamma: number): number {
  const n = weights.length;

  // Expected return term: w^T * mu
  let returnTerm = 0;
  for (let i = 0; i < n; i++) {
    returnTerm += (weights[i] ?? 0) * (returns[i] ?? 0);
  }

  // Variance term: w^T * Sigma * w
  let varianceTerm = 0;
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      varianceTerm += (weights[i] ?? 0) * (weights[j] ?? 0) * (sigma[i]?.[j] ?? 0);
    }
  }

  return returnTerm - (gamma / 2) * varianceTerm;
}

/**
 * Main optimization function that ties everything together
 */
export function runOptimization(priceHistory: PriceHistory[], config: PortfolioConfig): OptimizationResult {
  // Step 1: Calculate returns from price history
  const returnsData: ReturnsData[] = priceHistory.map(priceHistoryToReturns);

  // Step 2: Calculate covariance matrix
  const covMatrix = calculateCovarianceMatrix(returnsData);

  // Step 3: Calculate betas
  const betas = calculateBetas(returnsData);

  // Step 4: Calculate expected returns using CAPM
  const expectedReturns = calculateCAPMReturns(betas, config.riskFreeRate);

  // Step 5: Apply user overrides
  for (const [ticker, override] of Object.entries(config.userReturnOverrides)) {
    expectedReturns[ticker] = override;
  }

  // Step 6: Calculate volatilities for reference
  const volatilities = calculateVolatilities(returnsData);

  // Step 7: Solve the QP problem
  const tickers = config.assets;
  const qpResult = solveQP(
    tickers,
    expectedReturns,
    covMatrix,
    config.riskAversion,
    config.maxLeverage,
    config.borrowRate
  );

  // Step 8: Calculate portfolio statistics
  const portfolioReturn = calculatePortfolioReturn(qpResult.weights, expectedReturns);
  const portfolioVolatility = calculatePortfolioVolatility(qpResult.weights, covMatrix);
  const sharpeRatio = calculateSharpeRatio(portfolioReturn, portfolioVolatility, config.riskFreeRate);
  const totalLeverage = Object.values(qpResult.weights).reduce((a, b) => a + b, 0);

  // Step 9: Generate efficient frontier
  const efficientFrontier = generateEfficientFrontier(
    tickers,
    expectedReturns,
    covMatrix,
    config.maxLeverage,
    config.borrowRate
  );

  return {
    weights: qpResult.weights,
    stats: {
      portfolioReturn,
      portfolioVolatility,
      sharpeRatio,
      totalLeverage,
    },
    efficientFrontier,
  };
}

/**
 * Generate the efficient frontier by varying risk aversion
 */
function generateEfficientFrontier(
  tickers: string[],
  expectedReturns: Record<string, number>,
  covMatrix: CovarianceMatrix,
  maxLeverage: number,
  borrowRate: number
): EfficientFrontierPoint[] {
  const points: EfficientFrontierPoint[] = [];

  // Vary risk aversion from low (aggressive) to high (conservative)
  const riskAversionLevels = [0.5, 1, 1.5, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20];

  for (const gamma of riskAversionLevels) {
    const result = solveQP(tickers, expectedReturns, covMatrix, gamma, maxLeverage, borrowRate);

    const portfolioReturn = calculatePortfolioReturn(result.weights, expectedReturns);
    const portfolioVolatility = calculatePortfolioVolatility(result.weights, covMatrix);

    points.push({
      x: portfolioVolatility,
      y: portfolioReturn,
    });
  }

  // Sort by volatility (x)
  points.sort((a, b) => a.x - b.x);

  // Remove duplicates and dominated points
  const frontier: EfficientFrontierPoint[] = [];
  let maxReturn = -Infinity;

  for (const point of points) {
    if (point.y >= maxReturn - 0.001) {
      // Slight tolerance
      frontier.push(point);
      maxReturn = Math.max(maxReturn, point.y);
    }
  }

  return frontier;
}

/**
 * Calculate metrics for a given asset based on price history
 */
export function calculateAssetMetrics(
  history: PriceHistory,
  benchmarkHistory: PriceHistory | null,
  riskFreeRate: number
): { volatility: number; beta: number; expectedReturn: number } {
  const returns = priceHistoryToReturns(history);
  const volatilities = calculateVolatilities([returns]);
  const volatility = volatilities[history.ticker] ?? 0;

  let beta = 1;
  if (benchmarkHistory) {
    const benchmarkReturns = priceHistoryToReturns(benchmarkHistory);
    const betas = calculateBetas([returns, benchmarkReturns], "SPY");
    beta = betas[history.ticker] ?? 1;
  }

  // CAPM expected return
  const marketReturn = 0.1; // Historical average
  const expectedReturn = riskFreeRate + beta * (marketReturn - riskFreeRate);

  return { volatility, beta, expectedReturn };
}
