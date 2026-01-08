import type { JSX } from "solid-js";
import { For } from "solid-js";

interface LeverageInputProps {
  value: number;
  onChange: (value: number) => void;
}

const LEVERAGE_OPTIONS = [
  { value: 1.0, label: "1.0x", description: "No leverage" },
  { value: 1.25, label: "1.25x", description: "Low leverage" },
  { value: 1.5, label: "1.5x", description: "Moderate" },
  { value: 2.0, label: "2.0x", description: "High" },
  { value: 2.5, label: "2.5x", description: "Very High" },
  { value: 3.0, label: "3.0x", description: "Maximum" },
];

export function LeverageInput(props: LeverageInputProps): JSX.Element {
  return (
    <div class="space-y-2">
      <div class="flex justify-between items-center">
        <span class="text-xs text-slate-400">Maximum Leverage</span>
        <span class="text-sm font-semibold text-white">{props.value.toFixed(2)}x</span>
      </div>

      <div class="grid grid-cols-3 gap-1.5">
        <For each={LEVERAGE_OPTIONS}>
          {(option) => (
            <button
              type="button"
              onClick={() => props.onChange(option.value)}
              class={`px-2 py-1.5 rounded text-xs font-medium transition-all
                ${
                  props.value === option.value
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-500/25"
                    : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white"
                }`}
            >
              {option.label}
            </button>
          )}
        </For>
      </div>

      {props.value > 1 && (
        <div class="flex items-start gap-2 p-2 rounded bg-amber-500/10 border border-amber-500/30">
          <svg
            class="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            role="img"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <p class="text-xs text-amber-300">
            Leverage amplifies both gains and losses. Ensure you understand the margin costs (borrow rate) applied.
          </p>
        </div>
      )}
    </div>
  );
}
