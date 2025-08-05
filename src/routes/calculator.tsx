import { useState } from "preact/hooks";
import type { Asset, AssetFormData } from "~/types/portfolio";
import { optimizePortfolio } from "~/utils/calculateOptimizedPortfolio";

interface OptimizationSettings {
  riskFreeRate: number;
  riskAversion: number;
  correlationMatrix: "identity" | "estimated";
}

export default function Calculator() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [settings, setSettings] = useState<OptimizationSettings>({
    riskFreeRate: 0.03,
    riskAversion: 5,
    correlationMatrix: "identity",
  });
  const [formData, setFormData] = useState<AssetFormData>({
    symbol: "",
    name: "",
    expectedReturn: "",
    volatility: "",
    allocation: "",
  });
  const [formErrors, setFormErrors] = useState<Partial<AssetFormData>>({});
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [isAddingAsset, setIsAddingAsset] = useState(false);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);

  const validateForm = (): boolean => {
    const errors: Partial<AssetFormData> = {};

    if (!formData.symbol.trim()) {
      errors.symbol = "Symbol is required";
    } else if (formData.symbol.length > 10) {
      errors.symbol = "Symbol must be 10 characters or less";
    } else if (assets.some((asset) => asset.symbol.toUpperCase() === formData.symbol.toUpperCase())) {
      errors.symbol = "Asset already exists in portfolio";
    }

    if (!formData.name.trim()) {
      errors.name = "Name is required";
    } else if (formData.name.length > 100) {
      errors.name = "Name must be 100 characters or less";
    }

    const expectedReturn = parseFloat(formData.expectedReturn);
    if (!formData.expectedReturn.trim() || Number.isNaN(expectedReturn)) {
      errors.expectedReturn = "Expected return is required and must be a number";
    } else if (expectedReturn < -100 || expectedReturn > 1000) {
      errors.expectedReturn = "Expected return must be between -100% and 1000%";
    }

    const volatility = parseFloat(formData.volatility);
    if (!formData.volatility.trim() || Number.isNaN(volatility)) {
      errors.volatility = "Volatility is required and must be a number";
    } else if (volatility < 0 || volatility > 1000) {
      errors.volatility = "Volatility must be between 0% and 1000%";
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleInputChange = (field: keyof AssetFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error for this field when user starts typing
    if (formErrors[field]) {
      setFormErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const handleAddAsset = async () => {
    if (!validateForm()) {
      return;
    }

    setIsAddingAsset(true);

    try {
      // Simulate brief processing time for better UX
      await new Promise((resolve) => setTimeout(resolve, 300));

      const newAsset: Asset = {
        id: crypto.randomUUID(),
        symbol: formData.symbol.toUpperCase().trim(),
        name: formData.name.trim(),
        expectedReturn: parseFloat(formData.expectedReturn) / 100,
        volatility: parseFloat(formData.volatility) / 100,
        allocation: 0, // Will be optimized
      };

      setAssets((prev) => [...prev, newAsset]);
      setFormData({
        symbol: "",
        name: "",
        expectedReturn: "",
        volatility: "",
        allocation: "",
      });
      setFormErrors({});

      // Show success message
      setShowSuccessMessage(true);
      setTimeout(() => setShowSuccessMessage(false), 3000);
    } finally {
      setIsAddingAsset(false);
    }
  };

  const handleRemoveAsset = (id: string) => {
    setAssets((prev) => prev.filter((asset) => asset.id !== id));
  };

  const optimizePortfolioAllocation = () => {
    if (assets.length === 0) return null;

    setIsOptimizing(true);

    try {
      const result = getOptimizationResult();
      if (!result) return null;

      // Update assets with optimized allocations
      const optimizedAssets = assets.map((asset, index) => ({
        ...asset,
        allocation: result.weights[index],
      }));

      setAssets(optimizedAssets);
      return result;
    } catch (error) {
      console.error("Optimization failed:", error);
      return null;
    } finally {
      setIsOptimizing(false);
    }
  };

  const optimizationResult = assets.length > 0 ? getOptimizationResult() : null;

  function getOptimizationResult() {
    if (assets.length === 0) return null;
    if (assets.length === 1) {
      // Special case for single asset
      const asset = assets[0];
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
        correlations[i][i] = 1;
      }

      const result = optimizePortfolio({
        returns: assets.map((asset) => asset.expectedReturn),
        volatility: assets.map((asset) => asset.volatility),
        correlations,
        gamma: settings.riskAversion,
      });

      // Validate result
      if (!result || !result.weights || result.weights.some((w) => Number.isNaN(w) || w < 0)) {
        console.warn("Optimization returned invalid result");
        return null;
      }

      return result;
    } catch (error) {
      console.error("Portfolio optimization failed:", error);
      return null;
    }
  }

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
          <div className="max-w-md mx-auto mb-8">
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-center animate-fade-up">
              <div className="flex-shrink-0">
                <svg
                  className="w-6 h-6 text-emerald-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  role="img"
                  aria-label="Success"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
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
                <svg
                  className="w-6 h-6 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  role="img"
                  aria-label="Add asset"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
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
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        role="img"
                        aria-label="Search icon"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        />
                      </svg>
                    </div>
                  </div>
                  {formErrors.symbol ? (
                    <p className="text-sm text-red-600 mt-1">{formErrors.symbol}</p>
                  ) : (
                    <p className="text-xs text-slate-500 mt-1">Future: Search and select from database</p>
                  )}
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
                    <svg
                      className="w-5 h-5 animate-spin"
                      fill="none"
                      viewBox="0 0 24 24"
                      role="img"
                      aria-label="Loading"
                    >
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    <span>Adding Asset...</span>
                  </>
                ) : (
                  <>
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      role="img"
                      aria-label="Add"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                      />
                    </svg>
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
                  <svg
                    className="w-6 h-6 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    role="img"
                    aria-label="Portfolio chart"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a1 1 0 012-2h2a1 1 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
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
                      <svg
                        className="w-4 h-4 animate-spin"
                        fill="none"
                        viewBox="0 0 24 24"
                        role="img"
                        aria-label="Loading spinner"
                      >
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                      <span>Optimizing...</span>
                    </>
                  ) : (
                    <>
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        role="img"
                        aria-label="Optimize icon"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M13 10V3L4 14h7v7l9-11h-7z"
                        />
                      </svg>
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
                    <svg
                      className="w-8 h-8 text-red-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      role="img"
                      aria-label="Error"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-red-800 mb-2">Optimization Failed</h3>
                  <p className="text-red-700 mb-4">
                    Unable to optimize portfolio. Please check your asset parameters and try again.
                  </p>
                  <div className="text-sm text-red-600">
                    <p>Possible issues:</p>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>Invalid expected return or volatility values</li>
                      <li>Extreme risk parameters</li>
                      <li>Mathematical convergence issues</li>
                    </ul>
                  </div>
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
                const optimizedWeight = optimizationResult?.weights[index] || 0;
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
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                            role="img"
                            aria-label="Delete"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                            />
                          </svg>
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
