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
    <div className="container mx-auto px-6 py-16">
      <div className="text-center mb-12">
        <h1 className="text-4xl md:text-6xl font-bold bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent mb-4">
          Portfolio Calculator
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto font-light">
          Build your portfolio and calculate optimal Kelly Criterion allocations
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        <div className="card rounded-2xl p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center mr-3 shadow-md">
              <svg
                className="w-4 h-4 text-white"
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

          <div className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="symbol" className="block text-sm font-medium text-gray-700 mb-2">
                  Symbol
                </label>
                <input
                  id="symbol"
                  type="text"
                  value={formData.symbol}
                  onChange={(e) => handleInputChange("symbol", e.currentTarget.value)}
                  placeholder="AAPL"
                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                />
              </div>
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                  Name
                </label>
                <input
                  id="name"
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleInputChange("name", e.currentTarget.value)}
                  placeholder="Apple Inc."
                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                />
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label htmlFor="expectedReturn" className="block text-sm font-medium text-gray-700 mb-2">
                  Expected Return (%)
                </label>
                <input
                  id="expectedReturn"
                  type="number"
                  value={formData.expectedReturn}
                  onChange={(e) => handleInputChange("expectedReturn", e.currentTarget.value)}
                  placeholder="12.5"
                  step="0.1"
                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                />
              </div>
              <div>
                <label htmlFor="volatility" className="block text-sm font-medium text-gray-700 mb-2">
                  Volatility (%)
                </label>
                <input
                  id="volatility"
                  type="number"
                  value={formData.volatility}
                  onChange={(e) => handleInputChange("volatility", e.currentTarget.value)}
                  placeholder="20.0"
                  step="0.1"
                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                />
              </div>
              <div>
                <label htmlFor="allocation" className="block text-sm font-medium text-gray-700 mb-2">
                  Allocation (%)
                </label>
                <input
                  id="allocation"
                  type="number"
                  value={formData.allocation}
                  onChange={(e) => handleInputChange("allocation", e.currentTarget.value)}
                  placeholder="25.0"
                  step="0.1"
                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                />
              </div>
            </div>

            <button
              type="button"
              onClick={handleAddAsset}
              className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg"
            >
              Add Asset to Portfolio
            </button>
          </div>
        </div>

        <div className="card rounded-2xl p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <div className="w-8 h-8 bg-gradient-to-r from-emerald-500 to-green-500 rounded-lg flex items-center justify-center mr-3 shadow-md">
              <svg
                className="w-4 h-4 text-white"
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
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="text-sm text-gray-500 mb-1">Expected Return</div>
                  <div className="text-2xl font-bold text-emerald-600">
                    {(metrics.expectedReturn * 100).toFixed(2)}%
                  </div>
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="text-sm text-gray-500 mb-1">Volatility</div>
                  <div className="text-2xl font-bold text-amber-600">{(metrics.volatility * 100).toFixed(2)}%</div>
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="text-sm text-gray-500 mb-1">Sharpe Ratio</div>
                  <div className="text-2xl font-bold text-blue-600">{metrics.sharpeRatio.toFixed(3)}</div>
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="text-sm text-gray-500 mb-1">Kelly Fraction</div>
                  <div className="text-2xl font-bold text-indigo-600">{(metrics.kellyFraction * 100).toFixed(1)}%</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">Add assets to see portfolio metrics</div>
          )}
        </div>
      </div>

      {assets.length > 0 && (
        <div className="mt-8 card rounded-2xl p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Current Assets</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-gray-700">Symbol</th>
                  <th className="text-left py-3 px-4 text-gray-700">Name</th>
                  <th className="text-right py-3 px-4 text-gray-700">Expected Return</th>
                  <th className="text-right py-3 px-4 text-gray-700">Volatility</th>
                  <th className="text-right py-3 px-4 text-gray-700">Allocation</th>
                  <th className="text-right py-3 px-4 text-gray-700">Action</th>
                </tr>
              </thead>
              <tbody>
                {assets.map((asset) => (
                  <tr key={asset.id} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="py-3 px-4 font-mono text-blue-600">{asset.symbol}</td>
                    <td className="py-3 px-4 text-gray-700">{asset.name}</td>
                    <td className="py-3 px-4 text-right text-emerald-600">
                      {(asset.expectedReturn * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-right text-amber-600">{(asset.volatility * 100).toFixed(1)}%</td>
                    <td className="py-3 px-4 text-right text-blue-600">{(asset.allocation * 100).toFixed(1)}%</td>
                    <td className="py-3 px-4 text-right">
                      <button
                        type="button"
                        onClick={() => handleRemoveAsset(asset.id)}
                        className="text-red-500 hover:text-red-700 transition-colors"
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
