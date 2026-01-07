import type { JSX } from "solid-js";

interface RateInputProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
}

export function RateInput(props: RateInputProps): JSX.Element {
  const min = () => props.min ?? 0;
  const max = () => props.max ?? 0.2;
  const step = () => props.step ?? 0.005;

  function handleInput(e: InputEvent & { currentTarget: HTMLInputElement }): void {
    const rawValue = e.currentTarget.value;
    // Handle percentage input (e.g., "4.5" means 4.5%)
    const numValue = Number.parseFloat(rawValue);
    if (!Number.isNaN(numValue)) {
      props.onChange(numValue / 100);
    }
  }

  function handleSlider(e: InputEvent & { currentTarget: HTMLInputElement }): void {
    props.onChange(Number.parseFloat(e.currentTarget.value));
  }

  return (
    <div class="space-y-1">
      <div class="flex justify-between items-center">
        <label class="text-xs text-slate-400">{props.label}</label>
        <div class="flex items-center gap-1">
          <input
            type="number"
            value={(props.value * 100).toFixed(2)}
            onInput={handleInput}
            min={min() * 100}
            max={max() * 100}
            step={(step() * 100).toString()}
            class="w-16 px-2 py-1 text-right text-sm font-mono bg-white/5 border border-white/10 rounded
                   text-white focus:outline-none focus:border-blue-500/50"
          />
          <span class="text-xs text-slate-500">%</span>
        </div>
      </div>

      <input
        type="range"
        min={min()}
        max={max()}
        step={step()}
        value={props.value}
        onInput={handleSlider}
        class="w-full h-1 rounded-full appearance-none cursor-pointer bg-white/10"
      />
    </div>
  );
}
