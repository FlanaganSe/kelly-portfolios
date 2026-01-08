import type { JSX } from "solid-js";
import { createEffect, onMount, Show } from "solid-js";
import { unwrap } from "solid-js/store";
import { AllocationPie } from "~/components/charts/AllocationPie";
import { EfficientFrontierChart } from "~/components/charts/EfficientFrontierChart";
import { DashboardLayout } from "~/components/layout/DashboardLayout";
import { Sidebar } from "~/components/layout/Sidebar";
import { PortfolioStats } from "~/components/PortfolioStats";
import { ReturnOverrides } from "~/components/ReturnOverrides";
import { StressTestPanel } from "~/components/StressTestPanel";
import {
  currentWeights,
  efficientFrontier,
  initializeAssets,
  loadPriceHistory,
  portfolioState,
  portfolioStats,
  setError,
  setIsOptimizing,
  setOptimizationProgress,
  setOptimizationResult,
  setReturnOverride,
} from "~/store/portfolioStore";
import { useOptimizer } from "~/workers/useOptimizer";

export default function App(): JSX.Element {
  const optimizer = useOptimizer();

  // Initialize available assets on mount
  onMount(() => {
    initializeAssets();
  });

  // Watch for optimization progress
  createEffect(() => {
    setOptimizationProgress(optimizer.progress());
  });

  // Run optimization
  async function handleOptimize(): Promise<void> {
    if (portfolioState.selectedAssets.length < 2) {
      setError("Select at least 2 assets to optimize");
      return;
    }

    setIsOptimizing(true);
    setError(null);

    try {
      // Load fresh price history
      await loadPriceHistory();

      if (portfolioState.priceHistory.length === 0) {
        throw new Error("Failed to load price history");
      }

      // Unwrap reactive store data into plain objects for worker
      const priceHistory = unwrap(portfolioState.priceHistory);
      const config = unwrap(portfolioState.config);

      // Run optimization in worker
      const result = await optimizer.optimize(priceHistory, config);

      setOptimizationResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Optimization failed");
      setOptimizationResult(null);
    } finally {
      setIsOptimizing(false);
    }
  }

  return (
    <DashboardLayout sidebar={<Sidebar onOptimize={handleOptimize} />}>
      <div class="space-y-6">
        {/* Header */}
        <div>
          <h1 class="text-2xl font-bold text-white">Portfolio Dashboard</h1>
          <p class="text-slate-400 mt-1">Mean-Variance Optimization with Quadratic Programming</p>
        </div>

        {/* Portfolio Stats */}
        <PortfolioStats stats={portfolioStats()} />

        {/* Main Charts */}
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Allocation Pie */}
          <div class="glass-panel p-6">
            <h2 class="text-lg font-semibold text-white mb-4">Optimal Allocation</h2>
            <Show
              when={Object.keys(currentWeights()).length > 0}
              fallback={
                <div class="h-64 flex items-center justify-center text-slate-400">
                  <div class="text-center">
                    <svg
                      class="w-12 h-12 mx-auto mb-3 opacity-50"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      role="img"
                      aria-hidden="true"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="1.5"
                        d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"
                      />
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="1.5"
                        d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"
                      />
                    </svg>
                    <p>Select assets and run optimization</p>
                    <p class="text-sm text-slate-500 mt-1">Allocation will appear here</p>
                  </div>
                </div>
              }
            >
              <AllocationPie weights={currentWeights()} />
            </Show>
          </div>

          {/* Efficient Frontier */}
          <div class="glass-panel p-6">
            <h2 class="text-lg font-semibold text-white mb-4">Efficient Frontier</h2>
            <Show
              when={efficientFrontier().length > 0}
              fallback={
                <div class="h-72 flex items-center justify-center text-slate-400">
                  <div class="text-center">
                    <svg
                      class="w-12 h-12 mx-auto mb-3 opacity-50"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      role="img"
                      aria-hidden="true"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="1.5"
                        d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
                      />
                    </svg>
                    <p>Run optimization to see the frontier</p>
                    <p class="text-sm text-slate-500 mt-1">Risk-return tradeoff curve</p>
                  </div>
                </div>
              }
            >
              <EfficientFrontierChart frontier={efficientFrontier()} currentPortfolio={portfolioStats()} />
            </Show>
          </div>
        </div>

        {/* Return Overrides */}
        <Show when={portfolioState.selectedAssets.length > 0}>
          <ReturnOverrides
            assets={portfolioState.selectedAssets}
            overrides={portfolioState.config.userReturnOverrides}
            onOverride={setReturnOverride}
          />
        </Show>

        {/* Stress Test Section */}
        <div class="glass-panel p-6">
          <StressTestPanel weights={currentWeights()} />
        </div>

        {/* Footer Info */}
        <div class="text-center text-xs text-slate-500 py-4">
          <p>Portfolio Optimizer V2 - Mean-Variance Optimization Engine</p>
          <p class="mt-1">Using CAPM for expected returns and Quadratic Programming for optimization</p>
        </div>
      </div>
    </DashboardLayout>
  );
}
