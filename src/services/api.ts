/**
 * API Client for Portfolio Optimizer Backend
 * Communicates with AWS Lambda functions via API Gateway
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "";

interface APIError {
  error: string;
  message: string;
  requestId?: string;
}

class PortfolioAPIError extends Error {
  constructor(
    message: string,
    public code: string,
    public requestId?: string
  ) {
    super(message);
    this.name = "PortfolioAPIError";
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error: APIError = await response.json();
    throw new PortfolioAPIError(error.message || "API request failed", error.error || "UNKNOWN_ERROR", error.requestId);
  }
  return response.json();
}

// Asset Types (matching backend)
export interface Asset {
  symbol: string;
  name: string;
  category: string;
  assetClass: string;
  currentImpliedVol30Day: number;
  volatility30Day: number;
  expectedReturn: number;
  sharpeRatio: number;
  lastUpdated: string;
}

export interface GetAssetsResponse {
  assets: Asset[];
  nextCursor?: string;
  total: number;
}

export interface GetAssetResponse extends Asset {}

export interface VolatilityResponse {
  symbol: string;
  volatility30Day: number;
  impliedVol30Day: number;
  historicalVolatility?: {
    "7day": number;
    "30day": number;
    "90day": number;
    "365day": number;
  };
  lastUpdated: string;
}

export interface CorrelationRequest {
  symbols: string[];
  startDate?: string;
  endDate?: string;
}

export interface CorrelationResponse {
  matrix: number[][];
  symbols: string[];
  startDate: string;
  endDate: string;
  dataQuality: "HIGH" | "MEDIUM" | "LOW";
}

export interface KellyAsset {
  symbol: string;
  expectedReturn?: number;
  volatility?: number;
}

export interface KellyRequest {
  assets: KellyAsset[];
  riskFreeRate: number;
  riskAversion: number;
  includeBlackSwan?: boolean;
  blackSwanMultiplier?: number;
}

export interface KellyAllocation {
  symbol: string;
  allocation: number;
  expectedReturn: number;
  volatility: number;
}

export interface KellyResponse {
  allocations: KellyAllocation[];
  portfolioMetrics: {
    expectedReturn: number;
    volatility: number;
    sharpeRatio: number;
    kellyFraction: number;
  };
  blackSwanAdjusted?: {
    allocations: KellyAllocation[];
    expectedReturn: number;
    volatility: number;
  };
}

/**
 * API Client Class
 */
export class PortfolioAPI {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL.replace(/\/$/, ""); // Remove trailing slash
  }

  /**
   * GET /assets - Retrieve assets with optional filtering
   */
  async getAssets(params?: {
    category?: string;
    assetClass?: string;
    limit?: number;
    cursor?: string;
  }): Promise<GetAssetsResponse> {
    const queryParams = new URLSearchParams();
    if (params?.category) queryParams.set("category", params.category);
    if (params?.assetClass) queryParams.set("assetClass", params.assetClass);
    if (params?.limit) queryParams.set("limit", params.limit.toString());
    if (params?.cursor) queryParams.set("cursor", params.cursor);

    const url = `${this.baseURL}/assets${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    const response = await fetch(url, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    return handleResponse<GetAssetsResponse>(response);
  }

  /**
   * GET /assets/:symbol - Get single asset details
   */
  async getAsset(symbol: string): Promise<GetAssetResponse> {
    const response = await fetch(`${this.baseURL}/assets/${symbol}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    return handleResponse<GetAssetResponse>(response);
  }

  /**
   * GET /volatility/:symbol - Get volatility data for an asset
   */
  async getVolatility(symbol: string): Promise<VolatilityResponse> {
    const response = await fetch(`${this.baseURL}/volatility/${symbol}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    return handleResponse<VolatilityResponse>(response);
  }

  /**
   * POST /calculate/correlation - Calculate correlation matrix
   */
  async calculateCorrelation(request: CorrelationRequest): Promise<CorrelationResponse> {
    const response = await fetch(`${this.baseURL}/calculate/correlation`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    return handleResponse<CorrelationResponse>(response);
  }

  /**
   * POST /calculate/kelly - Calculate Kelly Criterion optimal allocations
   */
  async calculateKelly(request: KellyRequest): Promise<KellyResponse> {
    const response = await fetch(`${this.baseURL}/calculate/kelly`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    return handleResponse<KellyResponse>(response);
  }

  /**
   * Search assets by symbol prefix
   */
  async searchAssets(query: string, limit = 10): Promise<Asset[]> {
    const response = await this.getAssets({ limit: 100 });
    const normalizedQuery = query.toUpperCase().trim();

    return response.assets
      .filter((asset) => asset.symbol.toUpperCase().startsWith(normalizedQuery) || asset.name.toUpperCase().includes(normalizedQuery))
      .slice(0, limit);
  }
}

// Export singleton instance
export const api = new PortfolioAPI();
