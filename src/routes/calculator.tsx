import { useState } from "preact/hooks";
import type { Asset, AssetFormData, Portfolio, PortfolioMetrics } from "~/types/portfolio";

export default function Calculator() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [portfolio, _setPortfolio] = useState<Portfolio>({
    id: "1",
    name: "My Portfolio",
    assets: [],
    totalValue: 100000,
    riskFreeRate: 0.03,
  });
  const [formData, setFormData] = useState<AssetFormData>({
    symbol: "",
    name: "",
    expectedReturn: "",
    volatility: "",
    allocation: "",
  });

  const handleInputChange = (field: keyof AssetFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleAddAsset = () => {
    if (
      !formData.symbol ||
      !formData.name ||
      !formData.expectedReturn ||
      !formData.volatility ||
      !formData.allocation
    ) {
      return;
    }

    const newAsset: Asset = {
      id: crypto.randomUUID(),
      symbol: formData.symbol.toUpperCase(),
      name: formData.name,
      expectedReturn: parseFloat(formData.expectedReturn) / 100,
      volatility: parseFloat(formData.volatility) / 100,
      allocation: parseFloat(formData.allocation) / 100,
    };

    setAssets((prev) => [...prev, newAsset]);
    setFormData({
      symbol: "",
      name: "",
      expectedReturn: "",
      volatility: "",
      allocation: "",
    });
  };

  const handleRemoveAsset = (id: string) => {
    setAssets((prev) => prev.filter((asset) => asset.id !== id));
  };

  const calculateKellyFraction = (expectedReturn: number, volatility: number, riskFreeRate: number): number => {
    const excessReturn = expectedReturn - riskFreeRate;
    return excessReturn / (volatility * volatility);
  };

  const calculatePortfolioMetrics = (): PortfolioMetrics | null => {
    if (assets.length === 0) return null;

    const totalAllocation = assets.reduce((sum, asset) => sum + asset.allocation, 0);
    const weightedReturn =
      assets.reduce((sum, asset) => sum + asset.expectedReturn * asset.allocation, 0) / totalAllocation;
    const weightedVolatility = Math.sqrt(
      assets.reduce((sum, asset) => sum + (asset.volatility * asset.allocation) ** 2, 0) /
        (totalAllocation * totalAllocation)
    );

    const excessReturn = weightedReturn - portfolio.riskFreeRate;
    const sharpeRatio = excessReturn / weightedVolatility;
    const kellyFraction = calculateKellyFraction(weightedReturn, weightedVolatility, portfolio.riskFreeRate);

    return {
      expectedReturn: weightedReturn,
      volatility: weightedVolatility,
      sharpeRatio,
      kellyFraction,
      diversificationRatio: assets.length > 1 ? 1 / Math.sqrt(assets.length) : 1,
    };
  };

  const metrics = calculatePortfolioMetrics();

  return (
    <div className="hero-gradient min-h-screen">
      <div className="container mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-7xl font-bold gradient-text mb-6 text-balance">Portfolio Calculator</h1>
          <p className="text-xl text-slate-600 max-w-3xl mx-auto font-light text-balance">
            Build your investment portfolio and calculate optimal Kelly Criterion allocations for maximum risk-adjusted
            returns
          </p>
        </div>

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
                  <input
                    id="symbol"
                    type="text"
                    value={formData.symbol}
                    onChange={(e) => handleInputChange("symbol", e.currentTarget.value)}
                    placeholder="AAPL"
                    className="input-field text-lg"
                  />
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
                    className="input-field text-lg"
                  />
                </div>
              </div>

              <div className="grid md:grid-cols-3 gap-6">
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
                    className="input-field text-lg"
                  />
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
                    className="input-field text-lg"
                  />
                </div>
                <div>
                  <label htmlFor="allocation" className="block text-sm font-semibold text-slate-700 mb-3">
                    Allocation (%)
                  </label>
                  <input
                    id="allocation"
                    type="number"
                    value={formData.allocation}
                    onChange={(e) => handleInputChange("allocation", e.currentTarget.value)}
                    placeholder="25.0"
                    step="0.1"
                    className="input-field text-lg"
                  />
                </div>
              </div>

              <button type="button" onClick={handleAddAsset} className="w-full btn-primary text-lg">
                Add Asset to Portfolio
              </button>
            </div>
          </div>

          <div className="card p-10">
            <h2 className="text-3xl font-bold text-slate-900 mb-8 flex items-center">
              <div className="bg-gradient-to-br from-emerald-600 to-cyan-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-900/25 w-12 h-12 mr-4">
                <svg
                  className="w-6 h-6 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  role="img"
                  aria-label="Portfolio metrics"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              Portfolio Metrics
            </h2>

            {metrics ? (
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-6">
                  <div className="metric-card">
                    <div className="text-sm font-semibold text-slate-500 mb-2">Expected Return</div>
                    <div className="text-3xl font-bold text-emerald-600">
                      {(metrics.expectedReturn * 100).toFixed(2)}%
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="text-sm font-semibold text-slate-500 mb-2">Volatility</div>
                    <div className="text-3xl font-bold text-amber-600">{(metrics.volatility * 100).toFixed(2)}%</div>
                  </div>
                  <div className="metric-card">
                    <div className="text-sm font-semibold text-slate-500 mb-2">Sharpe Ratio</div>
                    <div className="text-3xl font-bold text-blue-600">{metrics.sharpeRatio.toFixed(3)}</div>
                  </div>
                  <div className="metric-card">
                    <div className="text-sm font-semibold text-slate-500 mb-2">Kelly Fraction</div>
                    <div className="text-3xl font-bold text-indigo-600">
                      {(metrics.kellyFraction * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500 text-lg">Add assets to see portfolio metrics</div>
            )}
          </div>
        </div>
      </div>

      {assets.length > 0 && (
        <div className="mt-12 card p-10">
          <h2 className="text-3xl font-bold text-slate-900 mb-8">Current Assets</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-4 px-6 text-slate-700 font-semibold">Symbol</th>
                  <th className="text-left py-4 px-6 text-slate-700 font-semibold">Name</th>
                  <th className="text-right py-4 px-6 text-slate-700 font-semibold">Expected Return</th>
                  <th className="text-right py-4 px-6 text-slate-700 font-semibold">Volatility</th>
                  <th className="text-right py-4 px-6 text-slate-700 font-semibold">Allocation</th>
                  <th className="text-right py-4 px-6 text-slate-700 font-semibold">Action</th>
                </tr>
              </thead>
              <tbody>
                {assets.map((asset) => (
                  <tr key={asset.id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                    <td className="py-4 px-6 font-mono text-blue-600 font-semibold text-lg">{asset.symbol}</td>
                    <td className="py-4 px-6 text-slate-700 font-medium">{asset.name}</td>
                    <td className="py-4 px-6 text-right text-emerald-600 font-bold">
                      {(asset.expectedReturn * 100).toFixed(1)}%
                    </td>
                    <td className="py-4 px-6 text-right text-amber-600 font-bold">
                      {(asset.volatility * 100).toFixed(1)}%
                    </td>
                    <td className="py-4 px-6 text-right text-blue-600 font-bold">
                      {(asset.allocation * 100).toFixed(1)}%
                    </td>
                    <td className="py-4 px-6 text-right">
                      <button
                        type="button"
                        onClick={() => handleRemoveAsset(asset.id)}
                        className="text-red-500 hover:text-red-700 transition-all transform hover:scale-110"
                        aria-label={`Remove ${asset.symbol}`}
                      >
                        <svg
                          className="w-6 h-6"
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
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
