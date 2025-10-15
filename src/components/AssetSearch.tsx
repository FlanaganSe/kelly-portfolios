import { createEffect, createSignal, For, onCleanup, Show } from "solid-js";
import { Icon } from "~/components/Icon";
import { type Asset, api } from "~/services/api";

interface AssetSearchProps {
  onSelect: (asset: Asset) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function AssetSearch(props: AssetSearchProps) {
  const [query, setQuery] = createSignal("");
  const [results, setResults] = createSignal<Asset[]>([]);
  const [isSearching, setIsSearching] = createSignal(false);
  const [showDropdown, setShowDropdown] = createSignal(false);
  const [selectedIndex, setSelectedIndex] = createSignal(-1);
  const [error, setError] = createSignal<string | undefined>();

  let searchTimeout: ReturnType<typeof setTimeout> | undefined;
  let inputRef: HTMLInputElement | undefined;
  let dropdownRef: HTMLDivElement | undefined;

  // Debounced search
  createEffect(() => {
    const searchQuery = query();

    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }

    if (!searchQuery.trim()) {
      setResults([]);
      setShowDropdown(false);
      setError(undefined);
      return;
    }

    if (searchQuery.length < 1) {
      return;
    }

    searchTimeout = setTimeout(async () => {
      setIsSearching(true);
      setError(undefined);
      try {
        const searchResults = await api.searchAssets(searchQuery, 10);
        setResults(searchResults);
        setShowDropdown(searchResults.length > 0);
        if (searchResults.length === 0) {
          setError("No assets found");
        }
      } catch (err) {
        console.error("Search error:", err);
        setError("Failed to search assets");
        setResults([]);
        setShowDropdown(false);
      } finally {
        setIsSearching(false);
      }
    }, 300);
  });

  // Cleanup timeout on unmount
  onCleanup(() => {
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }
  });

  // Close dropdown when clicking outside
  const handleClickOutside = (e: MouseEvent) => {
    if (inputRef && dropdownRef && !inputRef.contains(e.target as Node) && !dropdownRef.contains(e.target as Node)) {
      setShowDropdown(false);
    }
  };

  createEffect(() => {
    document.addEventListener("mousedown", handleClickOutside);
    onCleanup(() => document.removeEventListener("mousedown", handleClickOutside));
  });

  const handleSelect = (asset: Asset) => {
    props.onSelect(asset);
    setQuery("");
    setResults([]);
    setShowDropdown(false);
    setSelectedIndex(-1);
    setError(undefined);
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    const currentResults = results();
    if (!showDropdown() || currentResults.length === 0) return;

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, currentResults.length - 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, -1));
        break;
      case "Enter": {
        e.preventDefault();
        const idx = selectedIndex();
        if (idx >= 0 && idx < currentResults.length) {
          const selected = currentResults[idx];
          if (selected) handleSelect(selected);
        }
        break;
      }
      case "Escape":
        setShowDropdown(false);
        setSelectedIndex(-1);
        break;
    }
  };

  return (
    <div class="relative">
      <label for="asset-search" class="block text-sm font-semibold text-slate-700 mb-3">
        Search Asset
      </label>
      <div class="relative">
        <input
          id="asset-search"
          ref={inputRef}
          type="text"
          value={query()}
          onInput={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (results().length > 0) {
              setShowDropdown(true);
            }
          }}
          placeholder={props.placeholder || "Search by symbol or name..."}
          disabled={props.disabled}
          class="input-field text-lg pr-12 w-full"
          autocomplete="off"
        />
        <div class="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400">
          <Show when={isSearching()} fallback={<Icon name="search" size={5} aria-label="Search icon" />}>
            <Icon name="spinner" size={5} class="animate-spin" aria-label="Searching" />
          </Show>
        </div>
      </div>

      {/* Error message */}
      <Show when={error() && !isSearching()}>
        <p class="text-sm text-amber-600 mt-2">{error()}</p>
      </Show>

      {/* Dropdown with results */}
      <Show when={showDropdown() && results().length > 0}>
        <div
          ref={dropdownRef}
          class="absolute z-50 w-full mt-2 bg-white border border-slate-200 rounded-xl shadow-xl max-h-80 overflow-y-auto"
        >
          <For each={results()}>
            {(asset, index) => (
              <button
                type="button"
                onClick={() => handleSelect(asset)}
                onMouseEnter={() => setSelectedIndex(index())}
                class={`w-full text-left px-4 py-3 hover:bg-slate-50 transition-colors border-b border-slate-100 last:border-b-0 ${
                  selectedIndex() === index() ? "bg-slate-100" : ""
                }`}
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-3">
                    <div class="bg-gradient-to-br from-blue-500 to-indigo-600 text-white font-mono font-bold text-sm px-3 py-1 rounded-lg">
                      {asset.symbol}
                    </div>
                    <div>
                      <div class="font-semibold text-slate-900 text-sm">{asset.name}</div>
                      <div class="text-xs text-slate-500">
                        {asset.category} • {asset.assetClass}
                      </div>
                    </div>
                  </div>
                  <div class="text-right">
                    <div class="text-sm font-semibold text-emerald-600">{(asset.expectedReturn * 100).toFixed(1)}%</div>
                    <div class="text-xs text-slate-500">Expected Return</div>
                  </div>
                </div>
              </button>
            )}
          </For>
        </div>
      </Show>
    </div>
  );
}
