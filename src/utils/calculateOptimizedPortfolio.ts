/**
 * Kelly Criterion Portfolio Optimizer
 */

type Portfolio = {
  returns: number[];
  volatility: number[];
  correlations: number[][];
  gamma?: number;
  bounds?: [number, number][];
};

type Result = {
  weights: number[];
  expectedReturn: number;
  risk: number;
  utility: number;
};

const dot = (a: number[], b: number[]) => a.reduce((sum, x, i) => sum + x * b[i], 0);

const sum = (arr: number[]) => arr.reduce((a, b) => a + b, 0);

/** Calculate portfolio mean return and standard deviation */
const stats = (w: number[], p: Portfolio): [number, number] => {
  const mean = dot(w, p.returns);

  let variance = 0;
  for (let i = 0; i < w.length; i++)
    for (let j = 0; j < w.length; j++)
      variance += w[i] * w[j] * p.volatility[i] * p.volatility[j] * p.correlations[i][j];

  return [mean, Math.sqrt(variance)];
};

/** Project weights onto constraints (sum=1, bounds) */
const project = (w: number[], bounds: [number, number][]): number[] => {
  const n = w.length;
  let x = [...w];

  // Alternating projection: sum constraint + box constraints
  for (let i = 0; i < 50; i++) {
    x = x.map((v) => v + (1 - sum(x)) / n);
    x = x.map((v, i) => Math.max(bounds[i][0], Math.min(bounds[i][1], v)));
    if (Math.abs(sum(x) - 1) < 1e-10) break;
  }

  return x;
};

/** Optimize portfolio using projected gradient descent */
export const optimizePortfolio = (portfolio: Portfolio): Result => {
  const { gamma = 5 } = portfolio;
  const n = portfolio.returns.length;
  const bounds = portfolio.bounds || Array(n).fill([0, 1]);

  // Objective: maximize return - 0.5 * gamma * variance
  const objective = (w: number[]) => {
    const [mean, std] = stats(w, portfolio);
    return -(mean - 0.5 * gamma * std * std);
  };

  // Numerical gradient
  const gradient = (w: number[]) => {
    const h = 1e-8;
    const normalize = (x: number[]) => x.map((v) => v / sum(x));

    return w.map((_, i) => {
      const wPlus = [...w],
        wMinus = [...w];
      wPlus[i] += h;
      wMinus[i] -= h;
      return (objective(normalize(wPlus)) - objective(normalize(wMinus))) / (2 * h);
    });
  };

  // Initialize with equal weights
  let weights = project(Array(n).fill(1 / n), bounds);
  let stepSize = 0.1;

  // Gradient descent with line search
  for (let iter = 0; iter < 500; iter++) {
    const grad = gradient(weights);
    const currentObj = objective(weights);

    // Backtracking line search
    let improved = false;
    for (const scale of [1, 0.5, 0.1, 0.01]) {
      const newWeights = project(
        weights.map((w, i) => w - stepSize * scale * grad[i]),
        bounds
      );

      if (objective(newWeights) < currentObj) {
        weights = newWeights;
        stepSize *= 1.1;
        improved = true;
        break;
      }
    }

    if (!improved) {
      stepSize *= 0.5;
      if (stepSize < 1e-16) break;
    }
  }

  const [expectedReturn, risk] = stats(weights, portfolio);
  return {
    weights,
    expectedReturn,
    risk,
    utility: expectedReturn - 0.5 * gamma * risk * risk,
  };
};
