import type { JSX } from "solid-js";
import { createSignal, For, Show } from "solid-js";
import { calculateScenarioImpact, STRESS_SCENARIOS } from "~/data/mock/scenarios";
import type { StressScenario } from "~/types";

interface StressTestPanelProps {
  weights: Record<string, number>;
}

export function StressTestPanel(props: StressTestPanelProps): JSX.Element {
  const [selectedScenario, setSelectedScenario] = createSignal<StressScenario | null>(null);

  const hasWeights = () => Object.keys(props.weights).length > 0;

  const calculateImpact = (scenario: StressScenario) => {
    if (!hasWeights()) return null;
    return calculateScenarioImpact(props.weights, scenario);
  };

  return (
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-white">Stress Test Scenarios</h3>
        <span class="text-xs text-slate-400">Simulate historical crisis events</span>
      </div>

      <Show
        when={hasWeights()}
        fallback={
          <div class="p-4 rounded-lg bg-white/5 border border-white/10 text-center">
            <p class="text-sm text-slate-400">Run optimization first to test scenarios</p>
          </div>
        }
      >
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          <For each={STRESS_SCENARIOS}>
            {(scenario) => {
              const impact = () => calculateImpact(scenario);
              const impactValue = () => impact();

              return (
                <button
                  type="button"
                  onClick={() => setSelectedScenario(scenario)}
                  class={`p-4 rounded-lg text-left transition-all group
                    ${
                      selectedScenario()?.name === scenario.name
                        ? "bg-white/10 border-blue-500/50 ring-1 ring-blue-500/25"
                        : "bg-white/5 border-white/10 hover:bg-white/10"
                    } border`}
                >
                  <div class="flex items-start justify-between gap-2">
                    <div>
                      <h4 class="font-medium text-white text-sm">{scenario.name}</h4>
                      <p class="text-xs text-slate-400 mt-1 line-clamp-2">{scenario.description}</p>
                    </div>
                    <Show when={impactValue() !== null}>
                      <div
                        class={`text-right flex-shrink-0 ${
                          (impactValue() ?? 0) < 0 ? "text-red-400" : "text-emerald-400"
                        }`}
                      >
                        <div class="text-lg font-bold">
                          {(impactValue() ?? 0) >= 0 ? "+" : ""}
                          {((impactValue() ?? 0) * 100).toFixed(1)}%
                        </div>
                      </div>
                    </Show>
                  </div>
                </button>
              );
            }}
          </For>
        </div>
      </Show>

      {/* Selected Scenario Detail */}
      <Show when={selectedScenario()}>
        {(scenario) => {
          const impact = () => calculateImpact(scenario());
          const impactValue = () => impact() ?? 0;

          return (
            <div class="p-4 rounded-lg bg-slate-800/50 border border-white/10">
              <div class="flex items-start justify-between mb-4">
                <div>
                  <h4 class="text-lg font-semibold text-white">{scenario().name}</h4>
                  <p class="text-sm text-slate-400 mt-1">{scenario().description}</p>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedScenario(null)}
                  class="p-1 rounded hover:bg-white/10 text-slate-400"
                  aria-label="Close details"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div class="p-3 rounded-lg bg-white/5">
                  <div class="text-xs text-slate-400 mb-1">Portfolio Impact</div>
                  <div class={`text-2xl font-bold ${impactValue() < 0 ? "text-red-400" : "text-emerald-400"}`}>
                    {impactValue() >= 0 ? "+" : ""}
                    {(impactValue() * 100).toFixed(1)}%
                  </div>
                </div>

                <div class="p-3 rounded-lg bg-white/5">
                  <div class="text-xs text-slate-400 mb-1">
                    vs SPY ({((scenario().impacts.SPY ?? 0) * 100).toFixed(0)}%)
                  </div>
                  <div
                    class={`text-2xl font-bold ${
                      impactValue() > (scenario().impacts.SPY ?? 0) ? "text-emerald-400" : "text-amber-400"
                    }`}
                  >
                    {impactValue() > (scenario().impacts.SPY ?? 0) ? "+" : ""}
                    {((impactValue() - (scenario().impacts.SPY ?? 0)) * 100).toFixed(1)}%
                  </div>
                  <div class="text-xs text-slate-500">relative performance</div>
                </div>
              </div>

              {/* Asset breakdown */}
              <div class="mt-4">
                <div class="text-xs text-slate-400 mb-2">Asset Performance in Scenario</div>
                <div class="grid grid-cols-2 gap-2">
                  <For each={Object.entries(props.weights).filter(([, w]) => w > 0.01)}>
                    {([ticker, weight]) => {
                      const assetImpact = scenario().impacts[ticker] ?? 0;
                      const contribution = assetImpact * weight;

                      return (
                        <div class="flex items-center justify-between p-2 rounded bg-white/5 text-sm">
                          <div class="flex items-center gap-2">
                            <span class="text-white font-medium">{ticker}</span>
                            <span class="text-xs text-slate-500">({(weight * 100).toFixed(0)}%)</span>
                          </div>
                          <div class="text-right">
                            <div class={assetImpact < 0 ? "text-red-400" : "text-emerald-400"}>
                              {(assetImpact * 100).toFixed(0)}%
                            </div>
                            <div class={`text-xs ${contribution < 0 ? "text-red-400/70" : "text-emerald-400/70"}`}>
                              {contribution >= 0 ? "+" : ""}
                              {(contribution * 100).toFixed(1)}% contrib
                            </div>
                          </div>
                        </div>
                      );
                    }}
                  </For>
                </div>
              </div>
            </div>
          );
        }}
      </Show>
    </div>
  );
}
