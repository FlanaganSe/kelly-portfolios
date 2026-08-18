import { createUniqueId, For, type JSX, Show } from "solid-js";

/**
 * A single stacked bar: where the portfolio's weight actually sits.
 *
 * **Why the segments are hatched rather than coloured.** This site's palette is warm
 * paper, near-black ink and one blue accent. It has no categorical colour ramp and is
 * not getting one, so identity here is carried by fill pattern and by a legend that
 * prints the number — both of which survive greyscale, a printout and full colour
 * blindness. Colour is not used at all.
 *
 * The bar is never the only presentation of the figure. Every page that draws one also
 * prints the same weights in a table.
 */

export interface ExposureSegment {
  readonly id: string;
  readonly label: string;
  /** Percent of the bar. Segments need not sum to 100 — see `scaleTo`. */
  readonly percent: number;
  readonly note?: string;
}

export interface ExposureBarProps {
  readonly segments: readonly ExposureSegment[];
  /**
   * The value the bar's full width represents. Defaults to the segment total, which is
   * what an allocation wants; a notional bar passes 100 so that exposure above capital
   * visibly overflows the width a capital bar would have had.
   */
  readonly scaleTo?: number;
  readonly caption?: JSX.Element;
  /** Announced instead of the picture. Say the whole thing. */
  readonly ariaLabel: string;
  readonly class?: string;
}

/** Four fills that stay distinct in greyscale. Solid ink first, then increasing air. */
const FILLS = ["solid", "diagonal", "dots", "cross", "sparse"] as const;

function fillFor(index: number): (typeof FILLS)[number] {
  return FILLS[index % FILLS.length] ?? "solid";
}

const OPACITY = [1, 0.82, 0.66, 0.5, 0.36];

function Swatch(props: { readonly index: number; readonly patternId: string }): JSX.Element {
  return (
    <svg viewBox="0 0 12 12" width="12" height="12" aria-hidden="true" class="shrink-0 self-center">
      <rect
        x="0.5"
        y="0.5"
        width="11"
        height="11"
        fill={`url(#${props.patternId}-${fillFor(props.index)})`}
        stroke="var(--rule-strong)"
        stroke-width="1"
        opacity={OPACITY[props.index % OPACITY.length]}
      />
    </svg>
  );
}

function Patterns(props: { readonly id: string }): JSX.Element {
  return (
    <defs>
      <pattern id={`${props.id}-solid`} width="4" height="4" patternUnits="userSpaceOnUse">
        <rect width="4" height="4" fill="var(--ink)" />
      </pattern>
      <pattern id={`${props.id}-diagonal`} width="5" height="5" patternUnits="userSpaceOnUse">
        <rect width="5" height="5" fill="var(--paper-sunken)" />
        <path d="M0 5 L5 0" stroke="var(--ink)" stroke-width="1.6" />
      </pattern>
      <pattern id={`${props.id}-dots`} width="5" height="5" patternUnits="userSpaceOnUse">
        <rect width="5" height="5" fill="var(--paper-sunken)" />
        <circle cx="2.5" cy="2.5" r="1.3" fill="var(--ink)" />
      </pattern>
      <pattern id={`${props.id}-cross`} width="6" height="6" patternUnits="userSpaceOnUse">
        <rect width="6" height="6" fill="var(--paper-sunken)" />
        <path d="M0 6 L6 0 M0 0 L6 6" stroke="var(--ink)" stroke-width="1.1" />
      </pattern>
      <pattern id={`${props.id}-sparse`} width="7" height="7" patternUnits="userSpaceOnUse">
        <rect width="7" height="7" fill="var(--paper-sunken)" />
        <path d="M0 7 L7 0" stroke="var(--ink)" stroke-width="1" />
      </pattern>
    </defs>
  );
}

export function ExposureBar(props: ExposureBarProps): JSX.Element {
  const patternId = createUniqueId();
  const total = () => props.segments.reduce((sum, one) => sum + one.percent, 0);
  const scale = () => props.scaleTo ?? total();
  const widthOf = (percent: number) => (scale() === 0 ? 0 : (percent / scale()) * 100);

  return (
    <figure class={props.class}>
      <div
        class="flex h-9 w-full overflow-hidden rounded-[2px] border border-rule-strong"
        role="img"
        aria-label={props.ariaLabel}
      >
        <For each={props.segments}>
          {(segment, index) => (
            <div
              class="relative h-full border-r border-paper last:border-r-0"
              style={{ width: `${widthOf(segment.percent)}%` }}
              title={`${segment.label}: ${segment.percent}%`}
            >
              <svg width="100%" height="100%" preserveAspectRatio="none" aria-hidden="true" class="block h-full w-full">
                <Patterns id={`${patternId}-${index()}`} />
                <rect
                  width="100%"
                  height="100%"
                  fill={`url(#${patternId}-${index()}-${fillFor(index())})`}
                  opacity={OPACITY[index() % OPACITY.length]}
                />
              </svg>
            </div>
          )}
        </For>
      </div>

      <ul class="mt-3 flex flex-wrap gap-x-5 gap-y-1.5 text-sm">
        <For each={props.segments}>
          {(segment, index) => (
            <li class="flex items-baseline gap-1.5">
              <svg width="0" height="0" aria-hidden="true" class="absolute">
                <Patterns id={`legend-${patternId}-${index()}`} />
              </svg>
              <Swatch index={index()} patternId={`legend-${patternId}-${index()}`} />
              <span class="text-ink-muted">{segment.label}</span>
              <span data-numeric class="font-medium text-ink">
                {segment.percent}%
              </span>
            </li>
          )}
        </For>
      </ul>

      <Show when={props.caption}>
        <figcaption class="mt-2 max-w-measure text-xs text-ink-muted">{props.caption}</figcaption>
      </Show>
    </figure>
  );
}
