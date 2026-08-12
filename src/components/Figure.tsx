import { type Component, Show } from "solid-js";
import { SourceLink } from "~/components/SourceLink";
import type { AsOf, Citation, KeyNumber, Tone } from "~/content/types";

const valueSize = {
  sm: "text-xl",
  md: "text-2xl",
  lg: "text-3xl",
} as const;

const toneColor: Record<Tone, string> = {
  positive: "var(--tone-positive)",
  caution: "var(--tone-caution)",
  negative: "var(--tone-negative)",
  neutral: "var(--ink)",
};

export interface FigureProps extends KeyNumber {
  /** The page that owns the fact. */
  readonly source?: Citation;
  readonly asOf?: AsOf | string;
  /** Names the interval, when the source page names it. Free text, e.g. "95% CI". */
  readonly intervalLabel?: string;
  readonly size?: "sm" | "md" | "lg";
  readonly align?: "start" | "end";
  /** Colours the number. Leave unset unless the sign genuinely carries meaning. */
  readonly tone?: Tone;
  readonly class?: string;
}

/**
 * A number with its label, unit, interval, `as of` date and source.
 *
 * `value` and `interval` are strings because that is how `src/content/` holds
 * them: the sign, the precision and the interval are part of the fact, and a
 * formatter that rounds one has misquoted it. A `KeyNumber` spreads straight in:
 *
 *     <Figure {...edge.headline} source={edge.source} asOf={edge.asOf} />
 */
export const Figure: Component<FigureProps> = (props) => {
  const alignEnd = () => props.align === "end";
  return (
    <figure class={`flex flex-col gap-1 ${alignEnd() ? "items-end text-right" : "items-start"} ${props.class ?? ""}`}>
      <figcaption class="eyebrow">{props.label}</figcaption>

      <div class={`flex items-baseline gap-1.5 ${alignEnd() ? "flex-row-reverse" : ""}`}>
        <span
          data-numeric
          class={`font-sans font-semibold tracking-[-0.02em] ${valueSize[props.size ?? "md"]}`}
          style={{ color: toneColor[props.tone ?? "neutral"] }}
        >
          {props.value}
        </span>
        <Show when={props.unit}>
          <span class="text-sm text-ink-muted">{props.unit}</span>
        </Show>
      </div>

      <Show when={props.interval}>
        <div data-numeric class="text-sm text-ink-muted">
          <Show when={props.intervalLabel} fallback={<span class="sr-only">Interval </span>}>
            <span class="text-ink-faint">{props.intervalLabel} </span>
          </Show>
          {props.interval}
        </div>
      </Show>

      <Show when={props.note}>
        <p class="max-w-[42ch] text-sm text-ink-muted">{props.note}</p>
      </Show>

      <Show when={props.asOf || props.source}>
        <div class={`flex flex-wrap items-baseline gap-x-3 gap-y-1 ${alignEnd() ? "justify-end" : ""}`}>
          <Show when={props.asOf}>
            {(date) => (
              <span data-numeric class="text-xs text-ink-faint">
                as of {date()}
              </span>
            )}
          </Show>
          <Show when={props.source}>{(citation) => <SourceLink citation={citation()} />}</Show>
        </div>
      </Show>
    </figure>
  );
};
