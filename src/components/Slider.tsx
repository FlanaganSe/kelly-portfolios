import { type Component, createUniqueId, For, Show } from "solid-js";
import { clamp, decimalsOf, formatNumber } from "~/lib/format";

export interface SliderProps {
  readonly label: string;
  readonly value: number;
  readonly onInput: (value: number) => void;
  readonly min: number;
  readonly max: number;
  readonly step?: number;
  /** Suffix shown after the value, e.g. `"%"`, `"bp"`, `"yr"`. */
  readonly unit?: string;
  /** Decimals to show. Defaults to whatever `step` implies. */
  readonly precision?: number;
  /** Overrides the readout, for values that are not plain decimals. */
  readonly format?: (value: number) => string;
  /** One line under the track. Wired to the input with `aria-describedby`. */
  readonly hint?: string;
  /** Native tick marks on the track. */
  readonly ticks?: readonly number[];
  /** Print the min and max under the ends of the track. */
  readonly showBounds?: boolean;
  readonly disabled?: boolean;
  readonly class?: string;
}

/**
 * A labelled range control.
 *
 * Built on a native `input[type=range]`, so arrow keys, Home, End, Page Up and
 * Page Down all behave as a screen reader user expects, and the thumb picks up
 * the accent colour from `accent-color`.
 */
export const Slider: Component<SliderProps> = (props) => {
  const id = createUniqueId();
  const hintId = `${id}-hint`;

  const decimals = () => props.precision ?? decimalsOf(props.step ?? 1);
  const display = (value: number) => props.format?.(value) ?? formatNumber(value, decimals());
  const readout = () => `${display(props.value)}${props.unit ? ` ${props.unit}` : ""}`;

  return (
    <div class={`flex flex-col gap-1.5 ${props.class ?? ""}`}>
      <div class="flex items-baseline justify-between gap-4">
        <label for={id} class="text-sm font-medium text-ink">
          {props.label}
        </label>
        <output for={id} data-numeric class="text-sm font-semibold text-ink">
          {readout()}
        </output>
      </div>

      <input
        id={id}
        type="range"
        class="w-full cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
        list={props.ticks?.length ? `${id}-ticks` : undefined}
        min={props.min}
        max={props.max}
        step={props.step ?? 1}
        value={props.value}
        disabled={props.disabled}
        aria-describedby={props.hint ? hintId : undefined}
        aria-valuetext={readout()}
        onInput={(event) => {
          const parsed = Number(event.currentTarget.value);
          if (Number.isFinite(parsed)) props.onInput(clamp(parsed, props.min, props.max));
        }}
      />

      <Show when={props.ticks?.length}>
        <datalist id={`${id}-ticks`}>
          <For each={props.ticks}>{(tick) => <option value={tick} />}</For>
        </datalist>
      </Show>

      <Show when={props.showBounds}>
        <div data-numeric class="flex justify-between text-xs text-ink-faint" aria-hidden="true">
          <span>{display(props.min)}</span>
          <span>{display(props.max)}</span>
        </div>
      </Show>

      <Show when={props.hint}>
        <p id={hintId} class="max-w-[42ch] text-xs text-ink-faint">
          {props.hint}
        </p>
      </Show>
    </div>
  );
};
