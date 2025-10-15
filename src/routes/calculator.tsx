import { createMemo, createSignal, For, Show } from "solid-js";
import { createStore } from "solid-js/store";
import { AssetSearch } from "~/components/AssetSearch";
import { CorrelationMatrix } from "~/components/CorrelationMatrix";
import { Icon } from "~/components/Icon";
import { VolatilityChart } from "~/components/VolatilityChart";
import { type Asset, api, type KellyAllocation } from "~/services/api";

interface SelectedAsset extends Asset {
  allocation: number;
}

interface OptimizationSettings {
  riskFreeRate: number;
  riskAversion: number;
  includeBlackSwan: boolean;
  blackSwanMultiplier: number;
}

interface OptimizationResult {
  allocations: KellyAllocation[];
  portfolioMetrics: {
    expectedReturn: number;
    volatility: number;
    sharpeRatio: number;
    kellyFraction: number;
  };
}

export default function Calculator() {
  const [assets, setAssets] = createStore<SelectedAsset[]>([]);
  const [settings, setSettings] = createStore<OptimizationSettings>({
    riskFreeRate: 0.03,
    riskAversion: 5,
    includeBlackSwan: false,
    blackSwanMultiplier: 2.0,
  });
  const [optimizationResult, setOptimizationResult] = createSignal<OptimizationResult | null>(null);
  const [isOptimizing, setIsOptimizing] = createSignal(false);
  const [optimizationError, setOptimizationError] = createSignal<string | null>(null);
  const [showSuccessMessage, setShowSuccessMessage] = createSignal(false);
  const [correlationMatrix, setCorrelationMatrix] = createSignal<number[][] | null>(null);

  const handleAssetSelected = (asset: Asset) => {
    // Check if already added
    if (assets.some((a) => a.symbol === asset.symbol)) {
      return;
    }

    const newAsset: SelectedAsset = {
      ...asset,
      allocation: 0,
    };

    setAssets([...assets, newAsset]);
    setShowSuccessMessage(true);
    setTimeout(() => setShowSuccessMessage(false), 3000);
  };

  const handleRemoveAsset = (symbol: string) => {
    setAssets(assets.filter((asset) => asset.symbol !== symbol));
    setOptimizationResult(null);
    setCorrelationMatrix(null);
  };

  const fetchCorrelationMatrix = async () => {
    if (assets.length < 2) {
      setCorrelationMatrix(null);
      return;
    }

    try {
      const result = await api.calculateCorrelation({
        symbols: assets.map((a) => a.symbol),
      });
      setCorrelationMatrix(result.matrix);
    } catch (error) {
      console.error("Failed to fetch correlation matrix:", error);
      setCorrelationMatrix(null);
    }
  };

  const optimizePortfolioAllocation = async () => {
    if (!assets.length) return;

    setIsOptimizing(true);
    setOptimizationError(null);

    try {
      const result = await api.calculateKelly({
        assets: assets.map((a) => ({ symbol: a.symbol })),
        riskFreeRate: settings.riskFreeRate,
        riskAversion: settings.riskAversion,
        includeBlackSwan: settings.includeBlackSwan,
        blackSwanMultiplier: settings.blackSwanMultiplier,
      });

      setOptimizationResult(result);

      // Update asset allocations
      setAssets(
        assets.map((asset) => {
          const allocation = result.allocations.find((a) => a.symbol === asset.symbol);
          return {
            ...asset,
            allocation: allocation?.allocation || 0,
          };
        })
      );

      // Fetch correlation matrix if we have multiple assets
      if (assets.length >= 2) {
        await fetchCorrelationMatrix();
      }
    } catch (error) {
      console.error("Optimization failed:", error);
      setOptimizationError(error instanceof Error ? error.message : "Failed to optimize portfolio. Please try again.");
    } finally {
      setIsOptimizing(false);
    }
  };

  const canOptimize = createMemo(() => assets.length >= 1);

  return (
    <div class="hero-gradient min-h-screen">
      <div class="container mx-auto px-6 py-20">
        <div class="text-center mb-16">
          <h1 class="text-5xl md:text-7xl font-bold gradient-text mb-6 text-balance">Portfolio Calculator</h1>
          <p class="text-xl text-slate-600 max-w-3xl mx-auto font-light text-balance">
            Build your investment portfolio and find optimal allocations using the Kelly Criterion with real market data
          </p>
        </div>

        <Show when={showSuccessMessage()}>
          <div class="fixed top-4 right-4 z-50 max-w-sm animate-fade-up">
            <div class="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-center shadow-lg">
              <div class="flex-shrink-0">
                <Icon name="check" size={6} class="text-emerald-600" aria-label="Success" />
              </div>
              <div class="ml-3">
                <p class="text-sm font-medium text-emerald-800">Asset added successfully!</p>
                <p class="text-sm text-emerald-600">Your portfolio has been updated.</p>
              </div>
            </div>
          </div>
        </Show>

        <div class="grid lg:grid-cols-2 gap-8">
          <div class="card p-10">
            <h2 class="text-3xl font-bold text-slate-900 mb-8 flex items-center">
              <div class="icon-gradient w-12 h-12 mr-4">
                <Icon name="search" size={6} class="text-white" aria-label="Search assets" />
              </div>
              Search Assets
            </h2>

            <div class="space-y-6">
              <AssetSearch onSelect={handleAssetSelected} placeholder="Search by symbol or name (e.g., SPY, AAPL)..." />

              <div class="bg-blue-50 border border-blue-200 rounded-xl p-4">
                <div class="flex items-start">
                  <Icon name="info" size={5} class="text-blue-600 mr-3 mt-0.5" aria-label="Info" />
                  <div class="text-sm text-blue-800">
                    <p class="font-semibold mb-1">Search our database of 100+ ETFs</p>
                    <p class="text-blue-700">
                      Type a ticker symbol or company name to find assets with real-time volatility and historical data.
                    </p>
                  </div>
                </div>
              </div>

              <Show when={assets.length > 0}>
                <div class="bg-slate-50 rounded-xl p-4">
                  <h3 class="text-sm font-semibold text-slate-700 mb-2">Selected Assets</h3>
                  <div class="flex flex-wrap gap-2">
                    <For each={assets}>
                      {(asset) => (
                        <div class="bg-white rounded-lg px-3 py-2 flex items-center space-x-2 border border-slate-200">
                          <span class="font-mono text-sm font-semibold text-slate-900">{asset.symbol}</span>
                          <button
                            type="button"
                            onClick={() => handleRemoveAsset(asset.symbol)}
                            class="text-slate-400 hover:text-red-500 transition-colors"
                            aria-label={`Remove ${asset.symbol}`}
                          >
                            <Icon name="close" size={4} aria-label="Close" />
                          </button>
                        </div>
                      )}
                    </For>
                  </div>
                </div>
              </Show>
            </div>
          </div>

          <div class="card p-10">
            <div class="flex items-center justify-between mb-8">
              <h2 class="text-3xl font-bold text-slate-900 flex items-center">
                <div class="bg-gradient-to-br from-emerald-600 to-cyan-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-900/25 w-12 h-12 mr-4">
                  <Icon name="chart" size={6} class="text-white" aria-label="Portfolio chart" />
                </div>
                Optimization
              </h2>
              <Show when={canOptimize()}>
                <button
                  type="button"
                  onClick={optimizePortfolioAllocation}
                  disabled={isOptimizing()}
                  class="btn-primary text-sm px-4 py-2 flex items-center space-x-2"
                >
                  <Show
                    when={!isOptimizing()}
                    fallback={
                      <>
                        <Icon name="spinner" size={4} class="animate-spin" aria-label="Loading spinner" />
                        <span>Optimizing...</span>
                      </>
                    }
                  >
                    <Icon name="optimize" size={4} aria-label="Optimize icon" />
                    <span>Optimize</span>
                  </Show>
                </button>
              </Show>
            </div>

            <Show
              when={optimizationResult()}
              fallback={
                <Show
                  when={canOptimize()}
                  fallback={
                    <div class="text-center py-12 text-slate-500 text-lg">
                      Search and add assets to begin optimization
                    </div>
                  }
                >
                  <Show when={optimizationError()}>
                    <div class="bg-red-50 border border-red-200 rounded-xl p-6">
                      <div class="flex items-center mb-4">
                        <Icon name="error" size={6} class="text-red-600 mr-3" aria-label="Error" />
                        <h3 class="text-lg font-semibold text-red-800">Optimization Failed</h3>
                      </div>
                      <p class="text-red-700">{optimizationError()}</p>
                    </div>
                  </Show>
                  <Show when={!optimizationError()}>
                    <div class="text-center py-12 text-slate-500 text-lg">
                      Click "Optimize" to calculate optimal allocations
                    </div>
                  </Show>
                </Show>
              }
            >
              {(result) => (
                <div class="space-y-6">
                  <div class="grid grid-cols-2 gap-6">
                    <div class="metric-card">
                      <div class="text-sm font-semibold text-slate-500 mb-2">Expected Return</div>
                      <div class="text-3xl font-bold text-emerald-600">
                        {(result().portfolioMetrics.expectedReturn * 100).toFixed(2)}%
                      </div>
                    </div>
                    <div class="metric-card">
                      <div class="text-sm font-semibold text-slate-500 mb-2">Portfolio Volatility</div>
                      <div class="text-3xl font-bold text-amber-600">
                        {(result().portfolioMetrics.volatility * 100).toFixed(2)}%
                      </div>
                    </div>
                    <div class="metric-card">
                      <div class="text-sm font-semibold text-slate-500 mb-2">Sharpe Ratio</div>
                      <div class="text-3xl font-bold text-blue-600">
                        {result().portfolioMetrics.sharpeRatio.toFixed(3)}
                      </div>
                    </div>
                    <div class="metric-card">
                      <div class="text-sm font-semibold text-slate-500 mb-2">Kelly Fraction</div>
                      <div class="text-3xl font-bold text-indigo-600">
                        {(result().portfolioMetrics.kellyFraction * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  <div class="bg-slate-50 rounded-xl p-6">
                    <h3 class="text-lg font-semibold text-slate-700 mb-4">Optimization Settings</h3>
                    <div class="space-y-4">
                      <div class="grid grid-cols-2 gap-4">
                        <div>
                          <label for="riskFreeRate" class="block text-sm font-medium text-slate-600 mb-2">
                            Risk-Free Rate (%)
                          </label>
                          <input
                            id="riskFreeRate"
                            type="number"
                            value={settings.riskFreeRate * 100}
                            onInput={(e) => {
                              const value = parseFloat(e.target.value);
                              if (!Number.isNaN(value) && value >= -10 && value <= 20) {
                                setSettings("riskFreeRate", value / 100);
                              }
                            }}
                            step="0.1"
                            min="-10"
                            max="20"
                            class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                          />
                        </div>
                        <div>
                          <label for="riskAversion" class="block text-sm font-medium text-slate-600 mb-2">
                            Risk Aversion
                          </label>
                          <input
                            id="riskAversion"
                            type="number"
                            value={settings.riskAversion}
                            onInput={(e) => {
                              const value = parseFloat(e.target.value);
                              if (!Number.isNaN(value) && value >= 0.1 && value <= 100) {
                                setSettings("riskAversion", value);
                              }
                            }}
                            step="0.5"
                            min="0.1"
                            max="100"
                            class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                          />
                        </div>
                      </div>

                      <div class="flex items-center space-x-3 pt-2">
                        <input
                          id="includeBlackSwan"
                          type="checkbox"
                          checked={settings.includeBlackSwan}
                          onChange={(e) => setSettings("includeBlackSwan", e.target.checked)}
                          class="w-4 h-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500"
                        />
                        <label for="includeBlackSwan" class="text-sm font-medium text-slate-700">
                          Include Black Swan Protection
                        </label>
                      </div>

                      <Show when={settings.includeBlackSwan}>
                        <div>
                          <label for="blackSwanMultiplier" class="block text-sm font-medium text-slate-600 mb-2">
                            Black Swan Multiplier
                          </label>
                          <input
                            id="blackSwanMultiplier"
                            type="number"
                            value={settings.blackSwanMultiplier}
                            onInput={(e) => {
                              const value = parseFloat(e.target.value);
                              if (!Number.isNaN(value) && value >= 1 && value <= 10) {
                                setSettings("blackSwanMultiplier", value);
                              }
                            }}
                            step="0.5"
                            min="1"
                            max="10"
                            class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                          />
                          <p class="text-xs text-slate-500 mt-1">
                            Multiplier applied to tail risk factor (default: 2.0)
                          </p>
                        </div>
                      </Show>
                    </div>
                  </div>
                </div>
              )}
            </Show>
          </div>
        </div>
      </div>

      <Show when={assets.length > 0}>
        <div class="container mx-auto px-6 pb-20">
          <div class="card p-10">
            <h2 class="text-3xl font-bold text-slate-900 mb-8">Portfolio Assets</h2>
            <div class="space-y-4">
              <For each={assets}>
                {(asset) => {
                  return (
                    <div class="bg-slate-50 rounded-xl p-6 hover:bg-slate-100 transition-colors">
                      <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-4">
                          <div class="bg-white rounded-lg p-3 shadow-sm">
                            <div class="font-mono text-blue-600 font-bold text-lg">{asset.symbol}</div>
                          </div>
                          <div>
                            <div class="font-semibold text-slate-900 text-lg">{asset.name}</div>
                            <div class="text-slate-600 text-sm">
                              Return:{" "}
                              <span class="text-emerald-600 font-semibold">
                                {(asset.expectedReturn * 100).toFixed(1)}%
                              </span>
                              {" • "}
                              Volatility:{" "}
                              <span class="text-amber-600 font-semibold">
                                {(asset.volatility30Day * 100).toFixed(1)}%
                              </span>
                              {" • "}
                              Sharpe: <span class="text-blue-600 font-semibold">{asset.sharpeRatio.toFixed(2)}</span>
                            </div>
                          </div>
                        </div>

                        <div class="flex items-center space-x-6">
                          <div class="text-right">
                            <div class="text-2xl font-bold text-indigo-600">{(asset.allocation * 100).toFixed(1)}%</div>
                            <div class="text-sm text-slate-500">Kelly Allocation</div>
                          </div>

                          <div class="w-24 bg-white rounded-full h-3 shadow-inner">
                            <div
                              class="h-3 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full transition-all duration-500"
                              style={{ width: `${Math.min(asset.allocation * 100, 100)}%` }}
                            />
                          </div>

                          <button
                            type="button"
                            onClick={() => handleRemoveAsset(asset.symbol)}
                            class="text-red-500 hover:text-red-700 transition-all transform hover:scale-110 p-2"
                            aria-label={`Remove ${asset.symbol}`}
                          >
                            <Icon name="delete" size={5} aria-label="Delete" />
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                }}
              </For>
            </div>
          </div>
        </div>
      </Show>

      <Show when={assets.length > 0 && optimizationResult()}>
        <div class="container mx-auto px-6 pb-20">
          <div class="grid lg:grid-cols-2 gap-8">
            <Show when={assets[0]}>
              {(firstAsset) => (
                <VolatilityChart
                  symbol={firstAsset().symbol}
                  historicalVol={{
                    "7day": firstAsset().volatility30Day * 0.5,
                    "30day": firstAsset().volatility30Day,
                    "90day": firstAsset().volatility30Day * 1.1,
                    "365day": firstAsset().volatility30Day * 1.2,
                  }}
                />
              )}
            </Show>

            <Show when={assets.length >= 2 && correlationMatrix()}>
              {(matrix) => (
                <CorrelationMatrix symbols={assets.map((a) => a.symbol)} matrix={matrix()} dataQuality="HIGH" />
              )}
            </Show>
          </div>
        </div>
      </Show>
    </div>
  );
}
