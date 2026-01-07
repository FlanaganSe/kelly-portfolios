import type { Asset, AssetCategory } from "~/types";

export interface AssetDefinition {
  id: string;
  name: string;
  category: AssetCategory;
  basePrice: number;
  annualVolatility: number; // Used for generating mock data
  expectedAnnualReturn: number; // Base expected return
  betaVsSPY: number;
}

// Asset definitions with realistic characteristics
export const ASSET_DEFINITIONS: AssetDefinition[] = [
  {
    id: "SPY",
    name: "SPDR S&P 500 ETF Trust",
    category: "Equity",
    basePrice: 450,
    annualVolatility: 0.18,
    expectedAnnualReturn: 0.1,
    betaVsSPY: 1.0,
  },
  {
    id: "QQQ",
    name: "Invesco QQQ Trust (Nasdaq-100)",
    category: "Equity",
    basePrice: 380,
    annualVolatility: 0.24,
    expectedAnnualReturn: 0.12,
    betaVsSPY: 1.15,
  },
  {
    id: "TLT",
    name: "iShares 20+ Year Treasury Bond ETF",
    category: "Bond",
    basePrice: 100,
    annualVolatility: 0.16,
    expectedAnnualReturn: 0.04,
    betaVsSPY: -0.3,
  },
  {
    id: "GLD",
    name: "SPDR Gold Shares",
    category: "Commodity",
    basePrice: 180,
    annualVolatility: 0.15,
    expectedAnnualReturn: 0.05,
    betaVsSPY: 0.05,
  },
  {
    id: "VNQ",
    name: "Vanguard Real Estate ETF",
    category: "REIT",
    basePrice: 90,
    annualVolatility: 0.2,
    expectedAnnualReturn: 0.08,
    betaVsSPY: 0.85,
  },
  {
    id: "BTC",
    name: "Bitcoin",
    category: "Crypto",
    basePrice: 45000,
    annualVolatility: 0.7,
    expectedAnnualReturn: 0.25,
    betaVsSPY: 1.5,
  },
  {
    id: "ETH",
    name: "Ethereum",
    category: "Crypto",
    basePrice: 3000,
    annualVolatility: 0.8,
    expectedAnnualReturn: 0.3,
    betaVsSPY: 1.6,
  },
  {
    id: "HYG",
    name: "iShares iBoxx High Yield Corporate Bond ETF",
    category: "Bond",
    basePrice: 78,
    annualVolatility: 0.1,
    expectedAnnualReturn: 0.055,
    betaVsSPY: 0.4,
  },
  {
    id: "LQD",
    name: "iShares iBoxx Investment Grade Corporate Bond ETF",
    category: "Bond",
    basePrice: 115,
    annualVolatility: 0.08,
    expectedAnnualReturn: 0.045,
    betaVsSPY: 0.15,
  },
  {
    id: "CASH",
    name: "Cash Equivalent (Money Market)",
    category: "Cash",
    basePrice: 1,
    annualVolatility: 0.001,
    expectedAnnualReturn: 0.045,
    betaVsSPY: 0.0,
  },
];

// Create Asset objects from definitions (metrics will be calculated from price history)
export function createAssets(priceData: Map<string, number[]>): Map<string, Asset> {
  const assets = new Map<string, Asset>();

  for (const def of ASSET_DEFINITIONS) {
    const prices = priceData.get(def.id);
    const currentPrice = prices ? prices[prices.length - 1] : def.basePrice;

    assets.set(def.id, {
      id: def.id,
      name: def.name,
      category: def.category,
      price: currentPrice ?? def.basePrice,
      metrics: {
        volatility: def.annualVolatility,
        beta: def.betaVsSPY,
        expectedReturn: def.expectedAnnualReturn,
      },
    });
  }

  return assets;
}

// Category colors for UI
export const CATEGORY_COLORS: Record<AssetCategory, string> = {
  Equity: "#3B82F6", // Blue
  Bond: "#10B981", // Green
  Commodity: "#F59E0B", // Amber
  Crypto: "#8B5CF6", // Purple
  Cash: "#6B7280", // Gray
  REIT: "#EC4899", // Pink
};
