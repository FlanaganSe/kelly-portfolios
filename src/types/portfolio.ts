export interface Asset {
  id: string;
  symbol: string;
  name: string;
  expectedReturn: number;
  volatility: number;
  allocation: number;
  historicalData?: number[];
}

export interface Portfolio {
  id: string;
  name: string;
  assets: Asset[];
  totalValue: number;
  riskFreeRate: number;
  targetReturn?: number;
  kellyFraction?: number;
}

export interface AssetFormData {
  symbol: string;
  name: string;
  expectedReturn: string;
  volatility: string;
  allocation: string;
}
