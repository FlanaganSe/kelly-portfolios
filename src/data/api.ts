import type { Asset, PriceHistory } from "~/types";
import { createAssets } from "./mock/mockAssets";
import { getHistoryForTickers, getMockHistory } from "./mock/mockHistory";

// Data service interface - allows swapping implementations later
export interface DataService {
  getAvailableAssets(): Promise<Asset[]>;
  getAsset(ticker: string): Promise<Asset | null>;
  getPriceHistory(ticker: string): Promise<PriceHistory | null>;
  getPriceHistoryBatch(tickers: string[]): Promise<PriceHistory[]>;
  searchAssets(query: string): Promise<Asset[]>;
}

// Simulate network delay for realistic UX (only in development)
const MOCK_DELAY_MS = import.meta.env.DEV ? 200 : 0;

function delay(ms: number): Promise<void> {
  if (ms === 0) return Promise.resolve();
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Mock implementation of the data service
export class MockDataService implements DataService {
  private assets: Map<string, Asset>;
  private history: Map<string, PriceHistory>;

  constructor() {
    this.history = getMockHistory();
    this.assets = createAssets(new Map(Array.from(this.history.entries()).map(([k, v]) => [k, v.prices])));
  }

  async getAvailableAssets(): Promise<Asset[]> {
    await delay(MOCK_DELAY_MS);
    return Array.from(this.assets.values());
  }

  async getAsset(ticker: string): Promise<Asset | null> {
    await delay(MOCK_DELAY_MS / 2);
    return this.assets.get(ticker) ?? null;
  }

  async getPriceHistory(ticker: string): Promise<PriceHistory | null> {
    await delay(MOCK_DELAY_MS);
    return this.history.get(ticker) ?? null;
  }

  async getPriceHistoryBatch(tickers: string[]): Promise<PriceHistory[]> {
    await delay(MOCK_DELAY_MS);
    return getHistoryForTickers(tickers);
  }

  async searchAssets(query: string): Promise<Asset[]> {
    await delay(MOCK_DELAY_MS / 2);
    const lowerQuery = query.toLowerCase();
    return Array.from(this.assets.values()).filter(
      (asset) => asset.id.toLowerCase().includes(lowerQuery) || asset.name.toLowerCase().includes(lowerQuery)
    );
  }
}

// Singleton instance
let dataServiceInstance: DataService | null = null;

export function getDataService(): DataService {
  if (!dataServiceInstance) {
    dataServiceInstance = new MockDataService();
  }
  return dataServiceInstance;
}

// Helper functions for common operations
export async function fetchAssets(): Promise<Asset[]> {
  return getDataService().getAvailableAssets();
}

export async function fetchPriceHistory(tickers: string[]): Promise<PriceHistory[]> {
  return getDataService().getPriceHistoryBatch(tickers);
}

export async function searchAssets(query: string): Promise<Asset[]> {
  return getDataService().searchAssets(query);
}
