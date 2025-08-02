/**
 * Kelly Criterion Portfolio Optimizer
 * Production-ready, type-safe, minimal implementation
 */

type Portfolio = {
	returns: number[];
	volatility: number[];
	correlations: number[][];
	gamma?: number;
	bounds?: [min: number, max: number][];
};

type Result = {
	weights: number[];
	expectedReturn: number;
	risk: number;
	utility: number;
};

/**
 * Calculate portfolio statistics
 */
const portfolioStats = (
	weights: number[],
	{ returns, volatility, correlations }: Portfolio,
): [mean: number, std: number] => {
	const mean = weights.reduce((sum, w, i) => sum + w * returns[i], 0);

	let variance = 0;
	for (let i = 0; i < weights.length; i++) {
		for (let j = 0; j < weights.length; j++) {
			variance +=
				weights[i] *
				weights[j] *
				volatility[i] *
				volatility[j] *
				correlations[i][j];
		}
	}

	return [mean, Math.sqrt(variance)];
};

/**
 * Project weights to satisfy constraints: sum=1 and bounds
 */
const project = (weights: number[], bounds: [number, number][]): number[] => {
	const n = weights.length;
	let w = [...weights];

	// Alternating projection algorithm
	for (let iter = 0; iter < 50; iter++) {
		// Project onto sum constraint
		const adjustment = (1 - w.reduce((s, x) => s + x, 0)) / n;
		w = w.map((x) => x + adjustment);

		// Project onto box constraints
		w = w.map((x, i) => Math.max(bounds[i][0], Math.min(bounds[i][1], x)));

		// Check if we're close enough
		if (Math.abs(w.reduce((s, x) => s + x, 0) - 1) < 1e-10) break;
	}

	return w;
};

/**
 * Optimize portfolio using projected gradient descent
 */
export const optimizePortfolio = (portfolio: Portfolio): Result => {
	const { gamma = 2 } = portfolio;
	const n = portfolio.returns.length;
	const bounds = portfolio.bounds || Array(n).fill([0, 1]);

	// Objective: maximize utility = return - 0.5 * gamma * variance
	const objective = (w: number[]) => {
		const [mean, std] = portfolioStats(w, portfolio);
		return -(mean - 0.5 * gamma * std * std);
	};

	// Numerical gradient
	const gradient = (w: number[]) => {
		const h = 1e-8;
		return w.map((_, i) => {
			const wPlus = [...w];
			const wMinus = [...w];
			wPlus[i] += h;
			wMinus[i] -= h;

			// Re-normalize
			const normalize = (x: number[]) => {
				const sum = x.reduce((s, v) => s + v, 0);
				return x.map((v) => v / sum);
			};

			return (
				(objective(normalize(wPlus)) - objective(normalize(wMinus))) / (2 * h)
			);
		});
	};

	// Initialize: equal weights respecting bounds
	let weights = Array(n).fill(1 / n);
	weights = project(weights, bounds);

	// Gradient descent with backtracking line search
	let stepSize = 0.1;
	for (let iter = 0; iter < 500; iter++) {
		const grad = gradient(weights);
		const currentObj = objective(weights);

		// Backtracking line search
		let improved = false;
		for (const scale of [1, 0.5, 0.1, 0.01]) {
			const step = stepSize * scale;
			const newWeights = project(
				weights.map((w, i) => w - step * grad[i]),
				bounds,
			);

			if (objective(newWeights) < currentObj) {
				weights = newWeights;
				stepSize *= 1.1; // Increase step size on success
				improved = true;
				break;
			}
		}

		if (!improved) {
			stepSize *= 0.5;
			if (stepSize < 1e-16) break;
		}
	}

	const [expectedReturn, risk] = portfolioStats(weights, portfolio);
	const utility = expectedReturn - 0.5 * gamma * risk * risk;

	return { weights, expectedReturn, risk, utility };
};

/**
 * Example usage
 */
export const example = () => {
	const result = optimizePortfolio({
		// Annual returns: Cash, SPY, TLT, GLD, GBTC
		returns: [0.005, 0.1, 0.04, 0.06, 0.15],

		// Annual volatility
		volatility: [0.0, 0.16, 0.12, 0.18, 0.65],

		// Correlation matrix
		correlations: [
			[1.0, 0.0, 0.0, 0.0, 0.0], // Cash
			[0.0, 1.0, -0.3, 0.4, 0.6], // SPY
			[0.0, -0.3, 1.0, -0.1, -0.2], // TLT
			[0.0, 0.4, -0.1, 1.0, 0.3], // GLD
			[0.0, 0.6, -0.2, 0.3, 1.0], // GBTC
		],

		gamma: 3.0,

		// Bounds: [min, max]
		bounds: [
			[-1, 1], // Cash (allows leverage)
			[0.001, 1000], // SPY
			[0.001, 1000], // TLT
			[0.001, 0.15], // GLD
			[0.001, 0.1], // GBTC
		],
	});

	const assets = ["Cash", "SPY", "TLT", "GLD", "GBTC"];

	console.log("Optimal Portfolio:");
	result.weights.forEach((w, i) =>
		console.log(`${assets[i]}: ${(w * 100).toFixed(2)}%`),
	);
	console.log(
		`\nExpected Return: ${(result.expectedReturn * 100).toFixed(2)}%`,
	);
	console.log(`Risk (Std Dev): ${(result.risk * 100).toFixed(2)}%`);
	console.log(`Utility: ${result.utility.toFixed(6)}`);

	return result;
};

// Run example
example();
