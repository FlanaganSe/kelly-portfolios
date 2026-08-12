import { type Component, createEffect, createSignal, createUniqueId, Show } from "solid-js";
import { clamp, decimalsOf, formatNumber, parseNumber } from "~/lib/format";

export interface NumberInputProps {
  readonly label: string;
  readonly value: number;
  /** Called with the parsed value. Clamped on blur, not while typing. */
  readonly onInput: (value: number) => void;
  readonly min?: number;
  readonly max?: number;
  readonly step?: number;
  /** Suffix shown after the field, e.g. `"%"`, `"bp"`, `"yr"`. */
  readonly unit?: string;
  /** Decimals to show. Defaults to whatever `step` implies. */
  readonly precision?: number;
  /** One line under the field. Wired to the input with `aria-describedby`. */
  readonly hint?: string;
  /** Hide the label visually. It stays in the accessibility tree. */
  readonly labelHidden?: boolean;
  readonly disabled?: boolean;
  readonly class?: string;
}

/**
 * A labelled number field.
 *
 * Typing is never interrupted: the value is emitted on every parseable
 * keystroke and clamped to `min`/`max` only on blur, so a reader can clear the
 * field and retype without the control fighting back.
 */
export const NumberInput: Component<NumberInputProps> = (props) => {
  const id = createUniqueId();
  const hintId = `${id}-hint`;

  const min = () => props.min ?? Number.NEGATIVE_INFINITY;
  const max = () => props.max ?? Number.POSITIVE_INFINITY;
  const decimals = () => props.precision ?? decimalsOf(props.step ?? 1);

  const [draft, setDraft] = createSignal(formatNumber(props.value, decimals()));
  const [focused, setFocused] = createSignal(false);

  // Track the value from outside, but never overwrite what is being typed.
  createEffect(() => {
    const next = formatNumber(props.value, decimals());
    if (!focused()) setDraft(next);
  });

  const commit = () => {
    const parsed = parseNumber(draft());
    const next = parsed === null ? props.value : clamp(parsed, min(), max());
    setDraft(formatNumber(next, decimals()));
    if (next !== props.value) props.onInput(next);
  };

  return (
    <div class={`flex flex-col gap-1 ${props.class ?? ""}`}>
      {/* The unit rides in the label so it reaches the accessible name too. */}
      <label for={id} class={props.labelHidden ? "sr-only" : "text-sm font-medium text-ink"}>
        {props.label}
        <Show when={props.unit}>
          <span class="sr-only"> in {props.unit}</span>
        </Show>
      </label>

      <div class="flex items-baseline gap-2">
        <input
          id={id}
          type="number"
          inputmode="decimal"
          class="control w-full max-w-[10rem] text-right"
          value={draft()}
          min={props.min}
          max={props.max}
          step={props.step ?? "any"}
          disabled={props.disabled}
          aria-describedby={props.hint ? hintId : undefined}
          onFocus={() => setFocused(true)}
          onInput={(event) => {
            const raw = event.currentTarget.value;
            setDraft(raw);
            const parsed = parseNumber(raw);
            if (parsed !== null) props.onInput(parsed);
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

      <Show when={props.hint}>
        <p id={hintId} class="max-w-[42ch] text-xs text-ink-faint">
          {props.hint}
        </p>
      </Show>
    </div>
  );
};
