import type { JSX } from "solid-js";
import { createMemo, createSignal, For, Show } from "solid-js";
import { CATEGORY_COLORS } from "~/data/mock/mockAssets";
import type { Asset } from "~/types";

interface AssetSearchProps {
  assets: Asset[];
  selectedIds: string[];
  onSelect: (asset: Asset) => void;
}

export function AssetSearch(props: AssetSearchProps): JSX.Element {
  const [query, setQuery] = createSignal("");
  const [isFocused, setIsFocused] = createSignal(false);

  const filteredAssets = createMemo(() => {
    const q = query().toLowerCase().trim();
    if (!q) return [];

    return props.assets
      .filter(
        (a) => !props.selectedIds.includes(a.id) && (a.id.toLowerCase().includes(q) || a.name.toLowerCase().includes(q))
      )
      .slice(0, 5);
  });

  const showDropdown = createMemo(() => isFocused() && query().length > 0 && filteredAssets().length > 0);

  function handleSelect(asset: Asset): void {
    props.onSelect(asset);
    setQuery("");
  }

  return (
    <div class="relative">
      <div class="relative">
        <input
          type="text"
          value={query()}
          onInput={(e) => setQuery(e.currentTarget.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setTimeout(() => setIsFocused(false), 200)}
          placeholder="Search tickers (SPY, BTC...)"
          class="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white placeholder-slate-500
                 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/25 transition-all"
        />
        <svg
          class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>

      <Show when={showDropdown()}>
        <div class="absolute z-50 w-full mt-1 rounded-lg bg-slate-800/95 backdrop-blur border border-white/10 shadow-xl overflow-hidden">
          <For each={filteredAssets()}>
            {(asset) => (
              <button
                type="button"
                onClick={() => handleSelect(asset)}
                class="w-full px-3 py-2 flex items-center gap-3 hover:bg-white/10 transition-colors text-left"
              >
                <div
                  class="w-2 h-2 rounded-full flex-shrink-0"
                  style={{
                    "background-color": CATEGORY_COLORS[asset.category] ?? "#6B7280",
                  }}
                />
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-white">{asset.id}</span>
                    <span class="text-xs px-1.5 py-0.5 rounded bg-white/10 text-slate-400">{asset.category}</span>
                  </div>
                  <p class="text-xs text-slate-400 truncate">{asset.name}</p>
                </div>
                <div class="text-right text-xs text-slate-500">
                  <div>Vol: {(asset.metrics.volatility * 100).toFixed(0)}%</div>
                  <div>Beta: {asset.metrics.beta.toFixed(2)}</div>
                </div>
              </button>
            )}
          </For>
        </div>
      </Show>
    </div>
  );
}
