import type { JSX } from "solid-js";
import { createMemo } from "solid-js";

interface RiskSliderProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
}

export function RiskSlider(props: RiskSliderProps): JSX.Element {
  const min = () => props.min ?? 0.5;
  const max = () => props.max ?? 15;
  const step = () => props.step ?? 0.5;

  // Risk level label
  const riskLabel = createMemo(() => {
    if (props.value <= 2) return "Aggressive";
    if (props.value <= 4) return "Moderate-Aggressive";
    if (props.value <= 6) return "Moderate";
    if (props.value <= 9) return "Moderate-Conservative";
    return "Conservative";
  });

  // Risk level color
  const riskColor = createMemo(() => {
    if (props.value <= 2) return "text-red-400";
    if (props.value <= 4) return "text-orange-400";
    if (props.value <= 6) return "text-yellow-400";
    if (props.value <= 9) return "text-emerald-400";
    return "text-blue-400";
  });

  return (
    <div class="space-y-2">
      <div class="flex justify-between items-center">
        <label class="text-xs text-slate-400">Risk Aversion (γ)</label>
        <div class="flex items-center gap-2">
          <span class={`text-xs font-medium ${riskColor()}`}>{riskLabel()}</span>
          <span class="text-sm font-mono text-white bg-white/10 px-1.5 py-0.5 rounded">{props.value.toFixed(1)}</span>
        </div>
      </div>

      <input
        type="range"
        min={min()}
        max={max()}
        step={step()}
        value={props.value}
        onInput={(e) => props.onChange(Number.parseFloat(e.currentTarget.value))}
        class="w-full h-2 rounded-full cursor-pointer"
        style={{
          background: `linear-gradient(to right,
            rgb(239, 68, 68) 0%,
            rgb(234, 179, 8) 50%,
            rgb(59, 130, 246) 100%)`,
        }}
      />

      <div class="flex justify-between text-xs text-slate-500">
        <span>Aggressive</span>
        <span>Conservative</span>
      </div>
    </div>
  );
}
