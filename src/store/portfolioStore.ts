import { createMemo } from "solid-js";
import { createStore, produce } from "solid-js/store";
import { fetchAssets, fetchPriceHistory } from "~/data/api";
import { calculateScenarioImpact, STRESS_SCENARIOS } from "~/data/mock/scenarios";
import type { Asset, OptimizationResult, PortfolioConfig, PriceHistory, StressScenario } from "~/types";

// localStorage key
const STORAGE_KEY = "portfolio-optimizer-state";

// Default configuration
const DEFAULT_CONFIG: PortfolioConfig = {
  assets: [],
  riskFreeRate: 0.045, // 4.5%
  borrowRate: 0.065, // 6.5%
  marketReturn: 0.1, // 10% historical average
  riskAversion: 3.0, // Moderate
  maxLeverage: 1.0, // No leverage by default
  userReturnOverrides: {},
};

// Persisted state shape
interface PersistedState {
  selectedAssetIds: string[];
  config: PortfolioConfig;
}

// Load persisted state from localStorage
function loadPersistedState(): Partial<PersistedState> {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored) as Partial<PersistedState>;
    }
  } catch {
    // Ignore localStorage errors
  }
  return {};
}

// Save state to localStorage
function persistState(selectedAssetIds: string[], config: PortfolioConfig): void {
  try {
    const state: PersistedState = { selectedAssetIds, config };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Ignore localStorage errors
  }
}

// Store state interface
interface PortfolioState {
  config: PortfolioConfig;
  availableAssets: Asset[];
  selectedAssets: Asset[];
  priceHistory: PriceHistory[];
  optimizationResult: OptimizationResult | null;
  isLoading: boolean;
  isOptimizing: boolean;
  error: string | null;
  optimizationProgress: number;
}

// Load persisted config
const persisted = loadPersistedState();
const initialConfig = persisted.config ? { ...DEFAULT_CONFIG, ...persisted.config } : { ...DEFAULT_CONFIG };

// Create the store
const [state, setState] = createStore<PortfolioState>({
  config: initialConfig,
  availableAssets: [],
  selectedAssets: [],
  priceHistory: [],
  optimizationResult: null,
  isLoading: false,
  isOptimizing: false,
  error: null,
  optimizationProgress: 0,
});

// Derived state: selected asset tickers
export const selectedTickers = createMemo(() => state.selectedAssets.map((a) => a.id));

// Derived state: is ready to optimize (has 2+ assets selected)
export const canOptimize = createMemo(
  () => state.selectedAssets.length >= 2 && !state.isOptimizing && !state.isLoading
);

// Derived state: current portfolio weights
export const currentWeights = createMemo(() => state.optimizationResult?.weights ?? {});

// Derived state: portfolio stats
export const portfolioStats = createMemo(() => state.optimizationResult?.stats ?? null);

// Derived state: efficient frontier points
export const efficientFrontier = createMemo(() => state.optimizationResult?.efficientFrontier ?? []);

// Actions

// Initialize available assets and restore persisted selection
export async function initializeAssets(): Promise<void> {
  setState("isLoading", true);
  setState("error", null);

  try {
    const assets = await fetchAssets();
    setState("availableAssets", assets);

    // Restore persisted selection
    const persistedIds = persisted.selectedAssetIds ?? [];
    if (persistedIds.length > 0) {
      const selectedAssets = assets.filter((a) => persistedIds.includes(a.id));
      setState("selectedAssets", selectedAssets);
      setState(
        "config",
        "assets",
        persistedIds.filter((id) => assets.some((a) => a.id === id))
      );
    }
  } catch (e) {
    setState("error", e instanceof Error ? e.message : "Failed to load assets");
  } finally {
    setState("isLoading", false);
  }
}

// Add asset to selection
export function addAsset(asset: Asset): void {
  // Don't add duplicates
  if (state.selectedAssets.some((a) => a.id === asset.id)) return;

  // Limit to 10 assets
  if (state.selectedAssets.length >= 10) {
    setState("error", "Maximum 10 assets allowed");
    return;
  }

  setState(
    produce((s) => {
      s.selectedAssets.push(asset);
      s.config.assets.push(asset.id);
      s.error = null;
    })
  );

  // Persist
  persistState(
    state.selectedAssets.map((a) => a.id),
    state.config
  );
}

// Remove asset from selection
export function removeAsset(ticker: string): void {
  setState(
    produce((s) => {
      s.selectedAssets = s.selectedAssets.filter((a) => a.id !== ticker);
      s.config.assets = s.config.assets.filter((t) => t !== ticker);
      // Remove any return override
      delete s.config.userReturnOverrides[ticker];
      // Clear optimization result since assets changed
      s.optimizationResult = null;
    })
  );

  // Persist
  persistState(
    state.selectedAssets.map((a) => a.id),
    state.config
  );
}

// Helper to persist current state
function saveState(): void {
  persistState(
    state.selectedAssets.map((a) => a.id),
    state.config
  );
}

// Update risk aversion
export function setRiskAversion(value: number): void {
  setState("config", "riskAversion", Math.max(0.5, Math.min(15, value)));
  saveState();
}

// Update max leverage
export function setMaxLeverage(value: number): void {
  setState("config", "maxLeverage", Math.max(1, Math.min(3, value)));
  saveState();
}

// Update risk-free rate
export function setRiskFreeRate(value: number): void {
  setState("config", "riskFreeRate", Math.max(0, Math.min(0.2, value)));
  saveState();
}

// Update borrow rate
export function setBorrowRate(value: number): void {
  setState("config", "borrowRate", Math.max(0, Math.min(0.3, value)));
  saveState();
}

// Update expected market return
export function setMarketReturn(value: number): void {
  setState("config", "marketReturn", Math.max(0, Math.min(0.3, value)));
  saveState();
}

// Set user return override for an asset
export function setReturnOverride(ticker: string, value: number | null): void {
  setState(
    produce((s) => {
      if (value === null) {
        delete s.config.userReturnOverrides[ticker];
      } else {
        s.config.userReturnOverrides[ticker] = value;
      }
    })
  );
  saveState();
}

// Fetch price history for selected assets
export async function loadPriceHistory(): Promise<void> {
  if (state.selectedAssets.length === 0) return;

  setState("isLoading", true);
  setState("error", null);

  try {
    const tickers = state.selectedAssets.map((a) => a.id);
    const history = await fetchPriceHistory(tickers);
    setState("priceHistory", history);
  } catch (e) {
    setState("error", e instanceof Error ? e.message : "Failed to load price history");
  } finally {
    setState("isLoading", false);
  }
}

// Set optimization result (called from worker hook)
export function setOptimizationResult(result: OptimizationResult | null): void {
  setState("optimizationResult", result);
}

// Set optimizing state
export function setIsOptimizing(value: boolean): void {
  setState("isOptimizing", value);
}

// Set optimization progress
export function setOptimizationProgress(value: number): void {
  setState("optimizationProgress", value);
}

// Set error
export function setError(error: string | null): void {
  setState("error", error);
}

// Clear all selections and reset
export function resetPortfolio(): void {
  setState({
    config: { ...DEFAULT_CONFIG },
    selectedAssets: [],
    priceHistory: [],
    optimizationResult: null,
    error: null,
    optimizationProgress: 0,
  });
  saveState();
}

// Calculate stress test impact
export function calculateStressImpact(scenario: StressScenario): number | null {
  const weights = state.optimizationResult?.weights;
  if (!weights || Object.keys(weights).length === 0) return null;
  return calculateScenarioImpact(weights, scenario);
}

// Get all stress scenarios
export function getStressScenarios(): StressScenario[] {
  return STRESS_SCENARIOS;
}

// Quick add preset portfolios
export function addPresetPortfolio(preset: "balanced" | "aggressive" | "conservative"): void {
  const presetAssets: Record<string, string[]> = {
    balanced: ["SPY", "TLT", "GLD", "VNQ"],
    aggressive: ["QQQ", "BTC", "ETH", "SPY"],
    conservative: ["TLT", "LQD", "GLD", "CASH"],
  };

  const tickers = presetAssets[preset] ?? [];
  const assets = state.availableAssets.filter((a) => tickers.includes(a.id));

  setState(
    produce((s) => {
      s.selectedAssets = assets;
      s.config.assets = tickers;
      s.config.userReturnOverrides = {};
      s.optimizationResult = null;
    })
  );

  // Set risk aversion based on preset (these already call saveState)
  if (preset === "aggressive") setRiskAversion(1.5);
  else if (preset === "conservative") setRiskAversion(8);
  else setRiskAversion(3);
}

// Export state for reading
export { state as portfolioState };

// Export the store type for typing
export type { PortfolioState };
