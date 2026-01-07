// Asset entity
export interface Asset {
  id: string; // Ticker symbol e.g., "SPY"
  name: string; // Full name e.g., "SPDR S&P 500 ETF"
  category: AssetCategory;
  price: number; // Current price
  metrics: AssetMetrics;
}

export type AssetCategory = "Equity" | "Bond" | "Commodity" | "Crypto" | "Cash" | "REIT";

export interface AssetMetrics {
  volatility: number; // Annualized standard deviation
  beta: number; // Beta vs SPY
  expectedReturn: number; // CAPM-based expected return
}

// User configuration / state
export interface PortfolioConfig {
  assets: string[]; // List of ticker symbols
  riskFreeRate: number; // e.g., 0.045 (4.5%)
  borrowRate: number; // e.g., 0.065 (6.5%)
  riskAversion: number; // 1.0 (Aggressive) to 10.0 (Conservative)
  maxLeverage: number; // 1.0 to 3.0
  userReturnOverrides: Record<string, number>; // Manual overrides e.g., { "BTC": 0.15 }
}

// Optimization output
export interface OptimizationResult {
  weights: Record<string, number>; // e.g., { "SPY": 0.6, "TLT": 0.4 }
  stats: PortfolioStats;
  efficientFrontier: EfficientFrontierPoint[];
}

export interface PortfolioStats {
  portfolioReturn: number; // Expected annual return
  portfolioVolatility: number; // Annual volatility (std dev)
  sharpeRatio: number; // (Return - RiskFree) / Volatility
  totalLeverage: number; // Sum of weights
}

export interface EfficientFrontierPoint {
  x: number; // Volatility (risk)
  y: number; // Expected return
}

// Price history for calculations
export interface PriceHistory {
  ticker: string;
  dates: string[]; // ISO date strings
  prices: number[]; // Closing prices
}

// Weekly returns data
export interface ReturnsData {
  ticker: string;
  returns: number[]; // Logarithmic weekly returns
}

// Worker message types
export interface WorkerRequest {
  type: "optimize";
  payload: {
    priceHistory: PriceHistory[];
    config: PortfolioConfig;
  };
}

export interface WorkerResponse {
  type: "result" | "error" | "progress";
  payload: OptimizationResult | string | number;
}

// Stress test scenario
export interface StressScenario {
  name: string;
  description: string;
  impacts: Record<string, number>; // Asset returns during the scenario
}

// Covariance matrix representation
export interface CovarianceMatrix {
  tickers: string[];
  matrix: number[][];
}
