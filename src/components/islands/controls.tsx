/**
 * The three controls the tools are built from.
 *
 * Written fresh for the islands rather than imported from the client-routed
 * application being ported from, so a tool page ships only what it uses. The
 * interaction contract is the one that tree established and readers already met:
 *
 * - A number field emits on every parseable keystroke and clamps to its bounds only on
 *   blur, so typing 0.05 into a field whose floor is 0.1 is never interrupted.
 * - A range control is a native `input[type=range]`, so arrow keys, Home, End and the
 *   Page keys behave the way a screen-reader user expects and the thumb picks up
 *   `accent-color` from the theme.
 * - Every control carries a real `<label for>`. None of them is labelled by placement.
 */
import { type Component, createEffect, createSignal, createUniqueId, For, type JSX, Show } from "solid-js";
import { clamp, decimalsOf, formatNumber, parseNumber } from "~/lib/format";

interface FieldShellProps {
  readonly id: string;
  readonly label: string;
  /** Read out after the label and shown to nobody. The unit belongs in here. */
  readonly srSuffix?: string;
  readonly hint?: string;
  readonly hintId: string;
  readonly readout?: string;
  readonly class?: string;
  readonly children: JSX.Element;
}

const FieldShell: Component<FieldShellProps> = (props) => (
  <div class={`flex flex-col gap-1.5 ${props.class ?? ""}`}>
    <div class="flex items-baseline justify-between gap-3">
      <label for={props.id} class="text-sm font-medium text-ink">
        {props.label}
        <Show when={props.srSuffix}>
          <span class="sr-only"> {props.srSuffix}</span>
        </Show>
      </label>
      <Show when={props.readout}>
        <output for={props.id} data-numeric class="whitespace-nowrap text-sm font-semibold text-ink">
          {props.readout}
        </output>
      </Show>
    </div>
    {props.children}
    <Show when={props.hint}>
      <p id={props.hintId} class="max-w-[46ch] text-xs text-ink-faint">
        {props.hint}
      </p>
    </Show>
  </div>
);

export interface NumberFieldProps {
  readonly label: string;
  readonly value: number;
  readonly onInput: (value: number) => void;
  readonly min?: number;
  readonly max?: number;
  readonly step?: number;
  /** Rides in the label too, so the accessible name carries it. */
  readonly unit?: string;
  readonly precision?: number;
  readonly hint?: string;
  readonly class?: string;
}

export const NumberField: Component<NumberFieldProps> = (props) => {
  const id = createUniqueId();
  const hintId = `${id}-hint`;
  const decimals = () => props.precision ?? decimalsOf(props.step ?? 1);
  const min = () => props.min ?? Number.NEGATIVE_INFINITY;
  const max = () => props.max ?? Number.POSITIVE_INFINITY;

  const [draft, setDraft] = createSignal(formatNumber(props.value, decimals()));
  const [focused, setFocused] = createSignal(false);

  // The last value this field itself sent up. Anything else arriving in `props.value` is
  // somebody else's change — a preset button, a shared link — and has to land in the box
  // even while the reader has the cursor in it, or the field shows one number and the
  // answer beside it shows another.
  let emitted = props.value;
  const emit = (value: number) => {
    emitted = value;
    props.onInput(value);
  };

  createEffect(() => {
    const next = props.value;
    if (focused() && next === emitted) return;
    emitted = next;
    setDraft(formatNumber(next, decimals()));
  });

  const commit = () => {
    const parsed = parseNumber(draft());
    const next = parsed === null ? props.value : clamp(parsed, min(), max());
    setDraft(formatNumber(next, decimals()));
    if (next !== props.value) emit(next);
  };

  return (
    <FieldShell
      id={id}
      label={props.label}
      srSuffix={props.unit ? `in ${props.unit}` : undefined}
      hint={props.hint}
      hintId={hintId}
      class={props.class}
    >
      <div class="flex items-baseline gap-2">
        <input
          id={id}
          type="number"
          inputmode="decimal"
          class="control w-full max-w-[9rem] text-right"
          value={draft()}
          min={props.min}
          max={props.max}
          step={props.step ?? "any"}
          aria-describedby={props.hint ? hintId : undefined}
          onFocus={() => setFocused(true)}
          onInput={(event) => {
            const raw = event.currentTarget.value;
            setDraft(raw);
            const parsed = parseNumber(raw);
            if (parsed !== null) emit(parsed);
          }}
          onBlur={() => {
            setFocused(false);
            commit();
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              commit();
            }
          }}
        />
        <Show when={props.unit}>
          <span aria-hidden="true" class="text-sm text-ink-muted">
            {props.unit}
          </span>
        </Show>
      </div>
    </FieldShell>
  );
};

export interface RangeFieldProps {
  readonly label: string;
  readonly value: number;
  readonly onInput: (value: number) => void;
  readonly min: number;
  readonly max: number;
  readonly step?: number;
  readonly unit?: string;
  readonly precision?: number;
  readonly format?: (value: number) => string;
  readonly hint?: string;
  readonly showBounds?: boolean;
  readonly class?: string;
}

export const RangeField: Component<RangeFieldProps> = (props) => {
  const id = createUniqueId();
  const hintId = `${id}-hint`;
  const decimals = () => props.precision ?? decimalsOf(props.step ?? 1);
  const display = (value: number) => props.format?.(value) ?? formatNumber(value, decimals());
  const readout = () => `${display(props.value)}${props.unit ? ` ${props.unit}` : ""}`;

  return (
    <FieldShell id={id} label={props.label} hint={props.hint} hintId={hintId} readout={readout()} class={props.class}>
      <input
        id={id}
        type="range"
        class="w-full cursor-pointer"
        min={props.min}
        max={props.max}
        step={props.step ?? 1}
        value={props.value}
        aria-describedby={props.hint ? hintId : undefined}
        aria-valuetext={readout()}
        onInput={(event) => {
          const parsed = Number(event.currentTarget.value);
          if (Number.isFinite(parsed)) props.onInput(clamp(parsed, props.min, props.max));
        }}
      />
      <Show when={props.showBounds}>
        <div data-numeric class="flex justify-between text-xs text-ink-faint" aria-hidden="true">
          <span>{display(props.min)}</span>
          <span>{display(props.max)}</span>
        </div>
      </Show>
    </FieldShell>
  );
};

export interface SelectOption {
  readonly value: string;
  readonly label: string;
}

export interface SelectFieldProps {
  readonly label: string;
  readonly value: string;
  readonly options: readonly SelectOption[];
  readonly onChange: (value: string) => void;
  readonly hint?: string;
  readonly class?: string;
}

export const SelectField: Component<SelectFieldProps> = (props) => {
  const id = createUniqueId();
  const hintId = `${id}-hint`;
  return (
    <FieldShell id={id} label={props.label} hint={props.hint} hintId={hintId} class={props.class}>
      <select
        id={id}
        class="control w-full"
        value={props.value}
        aria-describedby={props.hint ? hintId : undefined}
        onChange={(event) => props.onChange(event.currentTarget.value)}
      >
        <For each={props.options}>{(option) => <option value={option.value}>{option.label}</option>}</For>
      </select>
    </FieldShell>
  );
};
