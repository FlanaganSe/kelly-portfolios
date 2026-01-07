import type { JSX } from "solid-js";
import { For, Show } from "solid-js";
import { AssetSearch } from "~/components/controls/AssetSearch";
import { LeverageInput } from "~/components/controls/LeverageInput";
import { RateInput } from "~/components/controls/RateInput";
import { RiskSlider } from "~/components/controls/RiskSlider";
import { CATEGORY_COLORS } from "~/data/mock/mockAssets";
import {
  addAsset,
  addPresetPortfolio,
  canOptimize,
  portfolioState,
  removeAsset,
  setBorrowRate,
  setMaxLeverage,
  setRiskAversion,
  setRiskFreeRate,
} from "~/store/portfolioStore";
import type { Asset } from "~/types";

interface SidebarProps {
  onOptimize: () => void;
}

export function Sidebar(props: SidebarProps): JSX.Element {
  return (
    <div class="space-y-6">
      {/* Header */}
      <div class="glass-panel p-4">
        <h1 class="text-xl font-bold text-white">Portfolio Optimizer</h1>
        <p class="text-sm text-slate-400 mt-1">Mean-Variance Optimization Engine</p>
      </div>

      {/* Quick Presets */}
      <div class="glass-panel p-4">
        <h2 class="text-sm font-semibold text-slate-300 mb-3">Quick Presets</h2>
        <div class="flex gap-2 flex-wrap">
          <button type="button" onClick={() => addPresetPortfolio("balanced")} class="preset-btn">
            Balanced
          </button>
          <button type="button" onClick={() => addPresetPortfolio("aggressive")} class="preset-btn">
            Aggressive
          </button>
          <button type="button" onClick={() => addPresetPortfolio("conservative")} class="preset-btn">
            Conservative
          </button>
        </div>
      </div>

      {/* Asset Selection */}
      <div class="glass-panel p-4">
        <h2 class="text-sm font-semibold text-slate-300 mb-3">
          Select Assets ({portfolioState.selectedAssets.length}/10)
        </h2>
        <AssetSearch
          assets={portfolioState.availableAssets}
          selectedIds={portfolioState.selectedAssets.map((a) => a.id)}
          onSelect={addAsset}
        />

        {/* Selected Assets List */}
        <div class="mt-4 space-y-2">
          <For each={portfolioState.selectedAssets}>
            {(asset) => <SelectedAssetChip asset={asset} onRemove={removeAsset} />}
          </For>
        </div>

        <Show when={portfolioState.selectedAssets.length < 2}>
          <p class="text-xs text-amber-400 mt-3">Select at least 2 assets to optimize</p>
        </Show>
      </div>

      {/* Risk Parameters */}
      <div class="glass-panel p-4">
        <h2 class="text-sm font-semibold text-slate-300 mb-3">Risk Parameters</h2>

        <div class="space-y-4">
          <RiskSlider value={portfolioState.config.riskAversion} onChange={setRiskAversion} />

          <LeverageInput value={portfolioState.config.maxLeverage} onChange={setMaxLeverage} />
        </div>
      </div>

      {/* Rate Inputs */}
      <div class="glass-panel p-4">
        <h2 class="text-sm font-semibold text-slate-300 mb-3">Market Rates</h2>

        <div class="space-y-3">
          <RateInput label="Risk-Free Rate" value={portfolioState.config.riskFreeRate} onChange={setRiskFreeRate} />
          <RateInput label="Borrow Rate" value={portfolioState.config.borrowRate} onChange={setBorrowRate} />
        </div>
      </div>

      {/* Optimize Button */}
      <button
        type="button"
        onClick={props.onOptimize}
        disabled={!canOptimize()}
        class="w-full py-3 px-4 rounded-lg font-semibold text-white transition-all duration-200
               bg-gradient-to-r from-blue-600 to-purple-600
               hover:from-blue-500 hover:to-purple-500
               disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed
               shadow-lg shadow-blue-500/25"
      >
        <Show
          when={!portfolioState.isOptimizing}
          fallback={
            <div class="flex items-center justify-center gap-2">
              <div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Optimizing... {portfolioState.optimizationProgress}%</span>
            </div>
          }
        >
          Optimize Portfolio
        </Show>
      </button>

      {/* Error Display */}
      <Show when={portfolioState.error}>
        <div class="glass-panel p-3 border border-red-500/50 bg-red-500/10">
          <p class="text-sm text-red-400">{portfolioState.error}</p>
        </div>
      </Show>
    </div>
  );
}

// Selected asset chip component
interface SelectedAssetChipProps {
  asset: Asset;
  onRemove: (id: string) => void;
}

function SelectedAssetChip(props: SelectedAssetChipProps): JSX.Element {
  const categoryColor = () => CATEGORY_COLORS[props.asset.category] ?? "#6B7280";

  return (
    <div class="flex items-center justify-between p-2 rounded-lg bg-white/5 border border-white/10 group hover:bg-white/10 transition-colors">
      <div class="flex items-center gap-2">
        <div class="w-2 h-2 rounded-full" style={{ "background-color": categoryColor() }} />
        <span class="text-sm font-medium text-white">{props.asset.id}</span>
        <span class="text-xs text-slate-400 truncate max-w-[100px]">{props.asset.name}</span>
      </div>
      <button
        type="button"
        onClick={() => props.onRemove(props.asset.id)}
        class="p-1 rounded hover:bg-white/10 text-slate-400 hover:text-red-400 transition-colors"
        aria-label={`Remove ${props.asset.id}`}
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}
