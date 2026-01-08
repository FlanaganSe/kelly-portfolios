import type { JSX } from "solid-js";
import { createSignal, For, Show } from "solid-js";
import type { Asset } from "~/types";

interface ReturnOverridesProps {
  assets: Asset[];
  overrides: Record<string, number>;
  onOverride: (ticker: string, value: number | null) => void;
}

export function ReturnOverrides(props: ReturnOverridesProps): JSX.Element {
  const [isExpanded, setIsExpanded] = createSignal(false);

  return (
    <div class="glass-panel p-4">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded())}
        class="w-full flex items-center justify-between text-left"
      >
        <div>
          <h3 class="text-sm font-semibold text-white">Expected Return Overrides</h3>
          <p class="text-xs text-slate-400">Customize CAPM estimates for each asset</p>
        </div>
        <svg
          class={`w-5 h-5 text-slate-400 transition-transform ${isExpanded() ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          role="img"
          aria-hidden="true"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      <Show when={isExpanded()}>
        <div class="mt-4 space-y-3">
          <div class="grid grid-cols-12 gap-2 text-xs text-slate-400 px-1">
            <div class="col-span-3">Asset</div>
            <div class="col-span-3 text-right">CAPM Est.</div>
            <div class="col-span-4 text-center">Override</div>
            <div class="col-span-2" />
          </div>

          <For each={props.assets}>
            {(asset) => (
              <ReturnOverrideRow
                asset={asset}
                override={props.overrides[asset.id]}
                onOverride={(value) => props.onOverride(asset.id, value)}
              />
            )}
          </For>

          <Show when={Object.keys(props.overrides).length > 0}>
            <button
              type="button"
              onClick={() => {
                for (const ticker of Object.keys(props.overrides)) {
                  props.onOverride(ticker, null);
                }
              }}
              class="text-xs text-slate-400 hover:text-white transition-colors"
            >
              Clear all overrides
            </button>
          </Show>
        </div>
      </Show>
    </div>
  );
}

interface ReturnOverrideRowProps {
  asset: Asset;
  override?: number;
  onOverride: (value: number | null) => void;
}

function ReturnOverrideRow(props: ReturnOverrideRowProps): JSX.Element {
  const [localValue, setLocalValue] = createSignal(
    props.override !== undefined ? (props.override * 100).toFixed(1) : ""
  );

  const hasOverride = () => props.override !== undefined;

  function handleSubmit(): void {
    const value = Number.parseFloat(localValue());
    if (!Number.isNaN(value)) {
      props.onOverride(value / 100);
    }
  }

  function handleClear(): void {
    props.onOverride(null);
    setLocalValue("");
  }

  return (
    <div class="grid grid-cols-12 gap-2 items-center p-2 rounded bg-white/5">
      <div class="col-span-3">
        <span class="font-medium text-white text-sm">{props.asset.id}</span>
      </div>

      <div class="col-span-3 text-right">
        <span class={`text-sm ${hasOverride() ? "text-slate-500 line-through" : "text-slate-300"}`}>
          {(props.asset.metrics.expectedReturn * 100).toFixed(1)}%
        </span>
      </div>

      <div class="col-span-4">
        <div class="flex items-center gap-1">
          <input
            type="number"
            value={localValue()}
            onInput={(e) => setLocalValue(e.currentTarget.value)}
            onBlur={handleSubmit}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            placeholder="--"
            step="0.5"
            class="w-full px-2 py-1 text-sm text-center font-mono bg-white/5 border border-white/10 rounded
                   text-white focus:outline-none focus:border-blue-500/50"
          />
          <span class="text-xs text-slate-500">%</span>
        </div>
      </div>

      <div class="col-span-2 flex justify-end">
        <Show when={hasOverride()}>
          <button
            type="button"
            onClick={handleClear}
            class="p-1 rounded hover:bg-white/10 text-slate-400 hover:text-red-400"
            title="Clear override"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" role="img" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </Show>
      </div>
    </div>
  );
}
