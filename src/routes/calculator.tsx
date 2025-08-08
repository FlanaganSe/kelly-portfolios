import { useState } from "preact/hooks";
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
  const [assets, setAssets] = useState<Asset[]>([]);
  const [settings, setSettings] = useState<OptimizationSettings>({
    riskFreeRate: 0.03,
    riskAversion: 5,
  });
  const [formData, setFormData] = useState<AssetFormData>({
    symbol: "",
    name: "",
    expectedReturn: "",
    volatility: "",
    allocation: "",
  });
  const [formErrors, setFormErrors] = useState<Partial<AssetFormData>>({});
  const [isAddingAsset, setIsAddingAsset] = useState(false);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);

  const handleInputChange = (field: keyof AssetFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (formErrors[field]) {
      setFormErrors((prev) => ({ ...prev, [field]: undefined }));
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
      setAssets((prev) => [...prev, newAsset]);
      resetForm();
      setShowSuccessMessage(true);
      setTimeout(() => setShowSuccessMessage(false), 3000);
    } finally {
      setIsAddingAsset(false);
    }
  };

  const handleRemoveAsset = (id: string) => {
    setAssets((prev) => prev.filter((asset) => asset.id !== id));
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
        setAssets((prev) =>
          prev.map((asset, index) => ({
            ...asset,
            allocation: result.weights?.[index] ?? 0,
          }))
        );
      }
    } finally {
      setIsOptimizing(false);
    }
  };

  const optimizationResult = getOptimizationResult();

  return (
    <div className="hero-gradient min-h-screen">
      <div className="container mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-7xl font-bold gradient-text mb-6 text-balance">Portfolio Calculator</h1>
          <p className="text-xl text-slate-600 max-w-3xl mx-auto font-light text-balance">
            Build your investment portfolio and find optimal allocations using advanced portfolio optimization with
            Kelly Criterion
          </p>
        </div>

        {showSuccessMessage && (
          <div className="fixed top-4 right-4 z-50 max-w-sm animate-fade-up">
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-center shadow-lg">
              <div className="flex-shrink-0">
                <Icon name="check" size={6} className="text-emerald-600" aria-label="Success" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-emerald-800">Asset added successfully!</p>
                <p className="text-sm text-emerald-600">Your portfolio has been updated.</p>
              </div>
            </div>
          </div>
        )}

        <div className="grid lg:grid-cols-2 gap-8">
          <div className="card p-10">
            <h2 className="text-3xl font-bold text-slate-900 mb-8 flex items-center">
              <div className="icon-gradient w-12 h-12 mr-4">
                <Icon name="add" size={6} className="text-white" aria-label="Add asset" />
              </div>
              Add Asset
            </h2>

            <div className="space-y-6">
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="symbol" className="block text-sm font-semibold text-slate-700 mb-3">
                    Symbol
                  </label>
                  <div className="relative">
                    <input
                      id="symbol"
                      type="text"
                      value={formData.symbol}
                      onChange={(e) => handleInputChange("symbol", e.currentTarget.value)}
                      placeholder="AAPL, MSFT, GOOGL..."
                      className={`input-field text-lg pr-12 ${
                        formErrors.symbol ? "border-red-300 focus:border-red-500 focus:ring-red-500/20" : ""
                      }`}
                    />
                    <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400">
                      <Icon name="search" size={5} aria-label="Search icon" />
                    </div>
                  </div>
                  {formErrors.symbol && <p className="text-sm text-red-600 mt-1">{formErrors.symbol}</p>}
                </div>
                <div>
                  <label htmlFor="name" className="block text-sm font-semibold text-slate-700 mb-3">
                    Name
                  </label>
                  <input
                    id="name"
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleInputChange("name", e.currentTarget.value)}
                    placeholder="Apple Inc."
                    className={`input-field text-lg ${
                      formErrors.name ? "border-red-300 focus:border-red-500 focus:ring-red-500/20" : ""
                    }`}
                  />
                  {formErrors.name && <p className="text-sm text-red-600 mt-1">{formErrors.name}</p>}
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="expectedReturn" className="block text-sm font-semibold text-slate-700 mb-3">
                    Expected Return (%)
                  </label>
                  <input
                    id="expectedReturn"
                    type="number"
                    value={formData.expectedReturn}
                    onChange={(e) => handleInputChange("expectedReturn", e.currentTarget.value)}
                    placeholder="12.5"
                    step="0.1"
                    className={`input-field text-lg ${
                      formErrors.expectedReturn ? "border-red-300 focus:border-red-500 focus:ring-red-500/20" : ""
                    }`}
                  />
                  {formErrors.expectedReturn && (
                    <p className="text-sm text-red-600 mt-1">{formErrors.expectedReturn}</p>
                  )}
                </div>
                <div>
                  <label htmlFor="volatility" className="block text-sm font-semibold text-slate-700 mb-3">
                    Volatility (%)
                  </label>
                  <input
                    id="volatility"
                    type="number"
                    value={formData.volatility}
                    onChange={(e) => handleInputChange("volatility", e.currentTarget.value)}
                    placeholder="20.0"
                    step="0.1"
                    className={`input-field text-lg ${
                      formErrors.volatility ? "border-red-300 focus:border-red-500 focus:ring-red-500/20" : ""
                    }`}
                  />
                  {formErrors.volatility && <p className="text-sm text-red-600 mt-1">{formErrors.volatility}</p>}
                </div>
              </div>

              <button
                type="button"
                onClick={handleAddAsset}
                disabled={isAddingAsset}
                className="w-full btn-primary text-lg flex items-center justify-center space-x-2"
              >
                {isAddingAsset ? (
                  <>
                    <Icon name="spinner" size={5} className="animate-spin" aria-label="Loading" />
                    <span>Adding Asset...</span>
                  </>
                ) : (
                  <>
                    <Icon name="add" size={5} aria-label="Add" />
                    <span>Add Asset to Portfolio</span>
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="card p-10">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-3xl font-bold text-slate-900 flex items-center">
                <div className="bg-gradient-to-br from-emerald-600 to-cyan-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-900/25 w-12 h-12 mr-4">
                  <Icon name="chart" size={6} className="text-white" aria-label="Portfolio chart" />
                </div>
                Optimized Portfolio
              </h2>
              {assets.length > 0 && (
                <button
                  type="button"
                  onClick={optimizePortfolioAllocation}
                  disabled={isOptimizing}
                  className="btn-primary text-sm px-4 py-2 flex items-center space-x-2"
                >
                  {isOptimizing ? (
                    <>
                      <Icon name="spinner" size={4} className="animate-spin" aria-label="Loading spinner" />
                      <span>Optimizing...</span>
                    </>
                  ) : (
                    <>
                      <Icon name="optimize" size={4} aria-label="Optimize icon" />
                      <span>Optimize</span>
                    </>
                  )}
                </button>
              )}
            </div>

            {optimizationResult ? (
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-6">
                  <div className="metric-card">
                    <div className="text-sm font-semibold text-slate-500 mb-2">Expected Return</div>
                    <div className="text-3xl font-bold text-emerald-600">
                      {(optimizationResult.expectedReturn * 100).toFixed(2)}%
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="text-sm font-semibold text-slate-500 mb-2">Risk (Volatility)</div>
                    <div className="text-3xl font-bold text-amber-600">
                      {(optimizationResult.risk * 100).toFixed(2)}%
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="text-sm font-semibold text-slate-500 mb-2">Sharpe Ratio</div>
                    <div className="text-3xl font-bold text-blue-600">
                      {((optimizationResult.expectedReturn - settings.riskFreeRate) / optimizationResult.risk).toFixed(
                        3
                      )}
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="text-sm font-semibold text-slate-500 mb-2">Utility Score</div>
                    <div className="text-3xl font-bold text-indigo-600">{optimizationResult.utility.toFixed(4)}</div>
                  </div>
                </div>

                <div className="bg-slate-50 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-slate-700 mb-4">Optimization Settings</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="riskFreeRate" className="block text-sm font-medium text-slate-600 mb-2">
                        Risk-Free Rate (%)
                      </label>
                      <input
                        id="riskFreeRate"
                        type="number"
                        value={settings.riskFreeRate * 100}
                        onChange={(e) => {
                          const value = parseFloat(e.currentTarget.value);
                          if (!Number.isNaN(value) && value >= -10 && value <= 20) {
                            setSettings((prev) => ({
                              ...prev,
                              riskFreeRate: value / 100,
                            }));
                          }
                        }}
                        step="0.1"
                        min="-10"
                        max="20"
                        className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                      />
                    </div>
                    <div>
                      <label htmlFor="riskAversion" className="block text-sm font-medium text-slate-600 mb-2">
                        Risk Aversion
                      </label>
                      <input
                        id="riskAversion"
                        type="number"
                        value={settings.riskAversion}
                        onChange={(e) => {
                          const value = parseFloat(e.currentTarget.value);
                          if (!Number.isNaN(value) && value >= 0.1 && value <= 100) {
                            setSettings((prev) => ({ ...prev, riskAversion: value }));
                          }
                        }}
                        step="0.5"
                        min="0.1"
                        max="100"
                        className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                      />
                    </div>
                  </div>
                </div>
              </div>
            ) : assets.length > 0 ? (
              <div className="text-center py-12">
                <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-4">
                  <div className="flex items-center justify-center mb-4">
                    <Icon name="error" size={8} className="text-red-600" aria-label="Error" />
                  </div>
                  <h3 className="text-lg font-semibold text-red-800 mb-2">Optimization Failed</h3>
                  <p className="text-red-700 mb-4">
                    Unable to optimize portfolio. Please check your asset parameters and try again.
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500 text-lg">
                Add assets and click optimize to see results
              </div>
            )}
          </div>
        </div>
      </div>

      {assets.length > 0 && (
        <div className="container mx-auto px-6 pb-20">
          <div className="card p-10">
            <h2 className="text-3xl font-bold text-slate-900 mb-8">Portfolio Assets</h2>
            <div className="space-y-4">
              {assets.map((asset, index) => {
                const optimizedWeight = optimizationResult?.weights?.[index] || 0;
                return (
                  <div key={asset.id} className="bg-slate-50 rounded-xl p-6 hover:bg-slate-100 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="bg-white rounded-lg p-3 shadow-sm">
                          <div className="font-mono text-blue-600 font-bold text-lg">{asset.symbol}</div>
                        </div>
                        <div>
                          <div className="font-semibold text-slate-900 text-lg">{asset.name}</div>
                          <div className="text-slate-600 text-sm">
                            Return:{" "}
                            <span className="text-emerald-600 font-semibold">
                              {(asset.expectedReturn * 100).toFixed(1)}%
                            </span>
                            {" • "}
                            Risk:{" "}
                            <span className="text-amber-600 font-semibold">{(asset.volatility * 100).toFixed(1)}%</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-6">
                        <div className="text-right">
                          <div className="text-2xl font-bold text-indigo-600">
                            {(optimizedWeight * 100).toFixed(1)}%
                          </div>
                          <div className="text-sm text-slate-500">Optimal Weight</div>
                        </div>

                        <div className="w-24 bg-white rounded-full h-3 shadow-inner">
                          <div
                            className="h-3 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full transition-all duration-500"
                            style={{ width: `${Math.min(optimizedWeight * 100, 100)}%` }}
                          />
                        </div>

                        <button
                          type="button"
                          onClick={() => handleRemoveAsset(asset.id)}
                          className="text-red-500 hover:text-red-700 transition-all transform hover:scale-110 p-2"
                          aria-label={`Remove ${asset.symbol}`}
                        >
                          <Icon name="delete" size={5} aria-label="Delete" />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
