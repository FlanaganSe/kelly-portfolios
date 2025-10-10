import { createMemo, createSignal, For, Show } from "solid-js";
import { createStore } from "solid-js/store";
import { Icon } from "~/components/Icon";
import type { Asset, AssetFormData } from "~/types/portfolio";
import { optimizePortfolio } from "~/utils/calculateOptimizedPortfolio";
import { validateExpectedReturn, validateName, validateSymbol, validateVolatility } from "~/utils/validation";

interface OptimizationSettings {
  riskFreeRate: number;
  riskAversion: number;
}

interface OptimizationResult {
  weights: number[];
  expectedReturn: number;
  risk: number;
  utility: number;
}

const validateField = (field: keyof AssetFormData, value: string, assets: Asset[]): string | undefined => {
  switch (field) {
    case "symbol":
      return validateSymbol(value, assets);
    case "name":
      return validateName(value);
    case "expectedReturn":
      return validateExpectedReturn(value);
    case "volatility":
      return validateVolatility(value);
    default:
      return undefined;
  }
};

export default function Calculator() {
  const [assets, setAssets] = createStore<Asset[]>([]);
  const [settings, setSettings] = createStore<OptimizationSettings>({
    riskFreeRate: 0.03,
    riskAversion: 5,
  });
  const [formData, setFormData] = createStore<AssetFormData>({
    symbol: "",
    name: "",
    expectedReturn: "",
    volatility: "",
    allocation: "",
  });
  const [formErrors, setFormErrors] = createStore<Partial<AssetFormData>>({});
  const [isAddingAsset, setIsAddingAsset] = createSignal(false);
  const [isOptimizing, setIsOptimizing] = createSignal(false);
  const [showSuccessMessage, setShowSuccessMessage] = createSignal(false);

  const handleInputChange = (field: keyof AssetFormData, value: string) => {
    setFormData(field, value);
    if (formErrors[field]) {
      setFormErrors(field, undefined);
    }
  };

  const validateForm = (): boolean => {
    const errors: Partial<AssetFormData> = {};
    (Object.keys(formData) as Array<keyof AssetFormData>).forEach((field) => {
      if (field !== "allocation") {
        const error = validateField(field, formData[field], assets);
        if (error) errors[field] = error;
      }
    });
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const resetForm = () => {
    setFormData({
      symbol: "",
      name: "",
      expectedReturn: "",
      volatility: "",
      allocation: "",
    });
    setFormErrors({});
  };

  const handleAddAsset = async () => {
    if (!validateForm()) return;
    setIsAddingAsset(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 300));
      const newAsset: Asset = {
        id: crypto.randomUUID(),
        symbol: formData.symbol.toUpperCase().trim(),
        name: formData.name.trim(),
        expectedReturn: parseFloat(formData.expectedReturn) / 100,
        volatility: parseFloat(formData.volatility) / 100,
        allocation: 0,
      };
      setAssets([...assets, newAsset]);
      resetForm();
      setShowSuccessMessage(true);
      setTimeout(() => setShowSuccessMessage(false), 3000);
    } finally {
      setIsAddingAsset(false);
    }
  };

  const handleRemoveAsset = (id: string) => {
    setAssets(assets.filter((asset) => asset.id !== id));
  };

  const getOptimizationResult = (): OptimizationResult | null => {
    if (assets.length === 0) return null;
    if (assets.length === 1) {
      const asset = assets[0];
      if (!asset) return null;
      return {
        weights: [1.0],
        expectedReturn: asset.expectedReturn,
        risk: asset.volatility,
        utility: asset.expectedReturn - 0.5 * settings.riskAversion * asset.volatility * asset.volatility,
      };
    }

    try {
      const n = assets.length;
      const correlations = Array(n)
        .fill(null)
        .map(() => Array(n).fill(0));
      for (let i = 0; i < n; i++) {
        const row = correlations[i];
        if (row) row[i] = 1;
      }

      const result = optimizePortfolio({
        returns: assets.map((asset) => asset.expectedReturn),
        volatility: assets.map((asset) => asset.volatility),
        correlations,
        gamma: settings.riskAversion,
      });

      if (!result || !result.weights || result.weights.some((w: number) => Number.isNaN(w) || w < 0)) {
        return null;
      }
      return result;
    } catch {
      return null;
    }
  };

  const optimizePortfolioAllocation = () => {
    if (!assets.length) return;
    setIsOptimizing(true);
    try {
      const result = getOptimizationResult();
      if (result) {
        setAssets(
          assets.map((asset, index) => ({
            ...asset,
            allocation: result.weights?.[index] ?? 0,
          }))
        );
      }
    } finally {
      setIsOptimizing(false);
    }
  };

  const optimizationResult = createMemo(() => getOptimizationResult());

  return (
    <div class="hero-gradient min-h-screen">
      <div class="container mx-auto px-6 py-20">
        <div class="text-center mb-16">
          <h1 class="text-5xl md:text-7xl font-bold gradient-text mb-6 text-balance">Portfolio Calculator</h1>
          <p class="text-xl text-slate-600 max-w-3xl mx-auto font-light text-balance">
            Build your investment portfolio and find optimal allocations using advanced portfolio optimization with
            Kelly Criterion
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
                <Icon name="add" size={6} class="text-white" aria-label="Add asset" />
              </div>
              Add Asset
            </h2>

            <div class="space-y-6">
              <div class="grid md:grid-cols-2 gap-6">
                <div>
                  <label for="symbol" class="block text-sm font-semibold text-slate-700 mb-3">
                    Symbol
                  </label>
                  <div class="relative">
                    <input
                      id="symbol"
                      type="text"
                      value={formData.symbol}
                      onInput={(e) => handleInputChange("symbol", e.target.value)}
                      placeholder="AAPL, MSFT, GOOGL..."
                      class={`input-field text-lg pr-12 ${
                        formErrors.symbol ? "border-red-300 focus:border-red-500 focus:ring-red-500/20" : ""
                      }`}
                    />
                    <div class="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400">
                      <Icon name="search" size={5} aria-label="Search icon" />
                    </div>
                  </div>
                  <Show when={formErrors.symbol}>
                    <p class="text-sm text-red-600 mt-1">{formErrors.symbol}</p>
                  </Show>
                </div>
                <div>
                  <label for="name" class="block text-sm font-semibold text-slate-700 mb-3">
                    Name
                  </label>
                  <input
                    id="name"
                    type="text"
                    value={formData.name}
                    onInput={(e) => handleInputChange("name", e.target.value)}
                    placeholder="Apple Inc."
                    class={`input-field text-lg ${
                      formErrors.name ? "border-red-300 focus:border-red-500 focus:ring-red-500/20" : ""
                    }`}
                  />
                  <Show when={formErrors.name}>
                    <p class="text-sm text-red-600 mt-1">{formErrors.name}</p>
                  </Show>
                </div>
              </div>

              <div class="grid md:grid-cols-2 gap-6">
                <div>
                  <label for="expectedReturn" class="block text-sm font-semibold text-slate-700 mb-3">
                    Expected Return (%)
                  </label>
                  <input
                    id="expectedReturn"
                    type="number"
                    value={formData.expectedReturn}
                    onInput={(e) => handleInputChange("expectedReturn", e.target.value)}
                    placeholder="12.5"
                    step="0.1"
                    class={`input-field text-lg ${
                      formErrors.expectedReturn ? "border-red-300 focus:border-red-500 focus:ring-red-500/20" : ""
                    }`}
                  />
                  <Show when={formErrors.expectedReturn}>
                    <p class="text-sm text-red-600 mt-1">{formErrors.expectedReturn}</p>
                  </Show>
                </div>
                <div>
                  <label for="volatility" class="block text-sm font-semibold text-slate-700 mb-3">
                    Volatility (%)
                  </label>
                  <input
                    id="volatility"
                    type="number"
                    value={formData.volatility}
                    onInput={(e) => handleInputChange("volatility", e.target.value)}
                    placeholder="20.0"
                    step="0.1"
                    class={`input-field text-lg ${
                      formErrors.volatility ? "border-red-300 focus:border-red-500 focus:ring-red-500/20" : ""
                    }`}
                  />
                  <Show when={formErrors.volatility}>
                    <p class="text-sm text-red-600 mt-1">{formErrors.volatility}</p>
                  </Show>
                </div>
              </div>

              <button
                type="button"
                onClick={handleAddAsset}
                disabled={isAddingAsset()}
                class="w-full btn-primary text-lg flex items-center justify-center space-x-2"
              >
                <Show
                  when={!isAddingAsset()}
                  fallback={
                    <>
                      <Icon name="spinner" size={5} class="animate-spin" aria-label="Loading" />
                      <span>Adding Asset...</span>
                    </>
                  }
                >
                  <Icon name="add" size={5} aria-label="Add" />
                  <span>Add Asset to Portfolio</span>
                </Show>
              </button>
            </div>
          </div>

          <div class="card p-10">
            <div class="flex items-center justify-between mb-8">
              <h2 class="text-3xl font-bold text-slate-900 flex items-center">
                <div class="bg-gradient-to-br from-emerald-600 to-cyan-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-900/25 w-12 h-12 mr-4">
                  <Icon name="chart" size={6} class="text-white" aria-label="Portfolio chart" />
                </div>
                Optimized Portfolio
              </h2>
              <Show when={assets.length > 0}>
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
                  when={assets.length > 0}
                  fallback={
                    <div class="text-center py-12 text-slate-500 text-lg">
                      Add assets and click optimize to see results
                    </div>
                  }
                >
                  <div class="text-center py-12">
                    <div class="bg-red-50 border border-red-200 rounded-xl p-6 mb-4">
                      <div class="flex items-center justify-center mb-4">
                        <Icon name="error" size={8} class="text-red-600" aria-label="Error" />
                      </div>
                      <h3 class="text-lg font-semibold text-red-800 mb-2">Optimization Failed</h3>
                      <p class="text-red-700 mb-4">
                        Unable to optimize portfolio. Please check your asset parameters and try again.
                      </p>
                    </div>
                  </div>
                </Show>
              }
            >
              {(result) => (
                <div class="space-y-6">
                  <div class="grid grid-cols-2 gap-6">
                    <div class="metric-card">
                      <div class="text-sm font-semibold text-slate-500 mb-2">Expected Return</div>
                      <div class="text-3xl font-bold text-emerald-600">
                        {(result().expectedReturn * 100).toFixed(2)}%
                      </div>
                    </div>
                    <div class="metric-card">
                      <div class="text-sm font-semibold text-slate-500 mb-2">Risk (Volatility)</div>
                      <div class="text-3xl font-bold text-amber-600">{(result().risk * 100).toFixed(2)}%</div>
                    </div>
                    <div class="metric-card">
                      <div class="text-sm font-semibold text-slate-500 mb-2">Sharpe Ratio</div>
                      <div class="text-3xl font-bold text-blue-600">
                        {((result().expectedReturn - settings.riskFreeRate) / result().risk).toFixed(3)}
                      </div>
                    </div>
                    <div class="metric-card">
                      <div class="text-sm font-semibold text-slate-500 mb-2">Utility Score</div>
                      <div class="text-3xl font-bold text-indigo-600">{result().utility.toFixed(4)}</div>
                    </div>
                  </div>

                  <div class="bg-slate-50 rounded-xl p-6">
                    <h3 class="text-lg font-semibold text-slate-700 mb-4">Optimization Settings</h3>
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
                {(asset, index) => {
                  const optimizedWeight = () => optimizationResult()?.weights?.[index()] || 0;
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
                              Risk:{" "}
                              <span class="text-amber-600 font-semibold">{(asset.volatility * 100).toFixed(1)}%</span>
                            </div>
                          </div>
                        </div>

                        <div class="flex items-center space-x-6">
                          <div class="text-right">
                            <div class="text-2xl font-bold text-indigo-600">
                              {(optimizedWeight() * 100).toFixed(1)}%
                            </div>
                            <div class="text-sm text-slate-500">Optimal Weight</div>
                          </div>

                          <div class="w-24 bg-white rounded-full h-3 shadow-inner">
                            <div
                              class="h-3 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full transition-all duration-500"
                              style={{ width: `${Math.min(optimizedWeight() * 100, 100)}%` }}
                            />
                          </div>

                          <button
                            type="button"
                            onClick={() => handleRemoveAsset(asset.id)}
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
    </div>
  );
}
