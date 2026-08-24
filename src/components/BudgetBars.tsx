import { For, type JSX, Show } from "solid-js";

/**
 * Horizontal bars for an edge budget, grouped by benchmark.
 *
 * The grouping is the point, not the decoration. Lines measured against different
 * benchmarks may never be added together, so a group here owns its own heading, its
 * own subtotal and its own block of the page, and no prop lets a caller sum across
 * two of them. Decision 0007 constraint 3.
 *
 * Two encoders carry every distinction, and colour is the second of them:
 *
 * - **Solid fill means the bar is inside its group's total. An outline means it is
 *   in no total at all** — switched off, a hurdle, a risk control, or a line booked
 *   against a benchmark this page does not sum. That survives greyscale and a
 *   printout.
 * - Every row also carries a word for what it is, next to the label.
 *
 * Every colour is a CSS custom property from `src/styles.css`, so the chart follows
 * the theme rather than freezing the light palette.
 *
 * Geometry note: each row's bar is its own inline SVG stretched with
 * `preserveAspectRatio="none"`, which is what makes it responsive down to 360px
 * without shrinking any text — all text is real HTML beside it. Strokes carry
 * `vector-effect="non-scaling-stroke"` so the stretch cannot thicken them, and bar
 * ends are square because a corner radius is the one thing the stretch would distort.
 */

/** What a bar is, which decides whether it may be added to anything. */
export type BarKind =
  /** In this group's total. */
  | "counted"
  /** The group's total itself. */
  | "subtotal"
  /** Available in principle, switched off for this reader. */
  | "off"
  /** A cost avoided, not a return earned. Never added. */
  | "hurdle"
  /** Bought for exposure control. Never added. */
  | "risk-control"
  /** Measured against something else entirely. */
  | "other-benchmark";

const fillFor: Readonly<Record<BarKind, string>> = {
  counted: "var(--accent)",
  subtotal: "var(--ink)",
  off: "var(--rule-strong)",
  hurdle: "var(--tone-caution)",
  "risk-control": "var(--tone-neutral)",
  "other-benchmark": "var(--tone-neutral)",
};

const isSolid: Readonly<Record<BarKind, boolean>> = {
  counted: true,
  subtotal: true,
  off: false,
  hurdle: false,
  "risk-control": false,
  "other-benchmark": false,
};

export interface BudgetBar {
  readonly id: string;
  readonly label: string;
  /** Basis points a year. Negative draws left of the zero rule. */
  readonly basisPoints: number;
  readonly kind: BarKind;
  /** The encoding in words, e.g. "counted" or "hurdle, not a saving". */
  readonly tag: string;
}

export interface BudgetBarGroup {
  readonly id: string;
  /** What every bar in this group is measured against. */
  readonly benchmark: string;
  /** One line on why this group cannot be added to the others. */
  readonly note: string;
  readonly bars: readonly BudgetBar[];
}

export interface BudgetBarsProps {
  /** States the finding, not the chart type. Read out in place of the whole graphic. */
  readonly ariaLabel: string;
  readonly caption: string;
  readonly groups: readonly BudgetBarGroup[];
  readonly footnote?: JSX.Element;
  readonly class?: string;
}

/** Print an exact content figure without rounding it, using the site's typographic minus. */
function bp(value: number): string {
  return String(value).replace("-", "−");
}

function stepFor(span: number): number {
  const raw = span / 5;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  for (const multiple of [1, 2, 2.5, 5]) {
    if (raw <= multiple * magnitude) return multiple * magnitude;
  }
  return 10 * magnitude;
}

interface Scale {
  readonly min: number;
  readonly max: number;
  readonly ticks: readonly number[];
  /** Position as a percentage of the plot width. */
  readonly pct: (value: number) => number;
}

/** One scale across every group: the lengths are comparable even though the totals never add. */
function scaleFor(groups: readonly BudgetBarGroup[]): Scale {
  const values = groups.flatMap((group) => group.bars.map((bar) => bar.basisPoints));
  const low = Math.min(0, ...values);
  const high = Math.max(0, ...values);
  const step = stepFor(Math.max(high - low, 1));
  const min = Math.floor(low / step) * step;
  const max = Math.ceil(high / step) * step;
  const ticks: number[] = [];
  for (let tick = min; tick <= max + step / 1000; tick += step) {
    ticks.push(Math.round(tick * 1000) / 1000);
  }
  return { min, max, ticks, pct: (value) => ((value - min) / (max - min)) * 100 };
}

const PLOT_WIDTH = 1000;
const PLOT_HEIGHT = 14;
/** So a zero-length bar still reads as a mark at the baseline rather than as nothing. */
const MINIMUM_BAR = 2;

function Bar(props: { readonly bar: BudgetBar; readonly scale: Scale }) {
  const x = (value: number) => (props.scale.pct(value) / 100) * PLOT_WIDTH;
  const start = () => Math.min(x(0), x(props.bar.basisPoints));
  const width = () => Math.max(Math.abs(x(props.bar.basisPoints) - x(0)), MINIMUM_BAR);
  const colour = () =>
    props.bar.kind === "counted" && props.bar.basisPoints < 0 ? "var(--tone-negative)" : fillFor[props.bar.kind];
  const solid = () => isSolid[props.bar.kind];

  return (
    <svg
      class="mt-1.5 block w-full"
      height={PLOT_HEIGHT}
      viewBox={`0 0 ${PLOT_WIDTH} ${PLOT_HEIGHT}`}
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <title>{`${props.bar.label}: ${bp(props.bar.basisPoints)} bp a year, ${props.bar.tag}`}</title>
      <For each={props.scale.ticks}>
        {(tick) => (
          <line
            x1={x(tick)}
            x2={x(tick)}
            y1="0"
            y2={PLOT_HEIGHT}
            stroke={tick === 0 ? "var(--rule-strong)" : "var(--rule)"}
            stroke-width="1"
            vector-effect="non-scaling-stroke"
          />
        )}
      </For>
      <rect
        x={start()}
        y="1"
        width={width()}
        height={PLOT_HEIGHT - 2}
        fill={solid() ? colour() : "none"}
        stroke={solid() ? "none" : colour()}
        stroke-width="1.5"
        vector-effect="non-scaling-stroke"
      />
    </svg>
  );
}

/**
 * The whole chart: one block per benchmark, then a shared axis, then the same data
 * again as a table for anyone not reading the picture.
 */
export function BudgetBars(props: BudgetBarsProps): JSX.Element {
  const scale = () => scaleFor(props.groups);

  return (
    <figure class={props.class}>
      <figcaption class="max-w-measure text-sm text-ink-muted">{props.caption}</figcaption>

      {/* The graphic is announced by its label; the table below carries the values. */}
      <div role="img" aria-label={props.ariaLabel} class="mt-5">
        <For each={props.groups}>
          {(group, index) => (
            <section class={index() === 0 ? "" : "mt-10 border-t-2 border-rule-strong pt-6"}>
              <h3 class="eyebrow">Measured against {group.benchmark}</h3>
              <p class="mt-1 max-w-measure text-sm text-ink-muted">{group.note}</p>

              <ul class="mt-4">
                <For each={group.bars}>
                  {(bar) => (
                    <li
                      class={
                        bar.kind === "subtotal"
                          ? "mt-2 border-t border-rule-strong pt-3 pb-1"
                          : "border-t border-rule py-2 first:border-t-0"
                      }
                    >
                      <div class="flex flex-wrap items-baseline gap-x-3 gap-y-0.5">
                        <span
                          class={`min-w-0 flex-1 text-sm ${
                            bar.kind === "off"
                              ? "text-ink-faint"
                              : bar.kind === "subtotal"
                                ? "font-medium text-ink"
                                : "text-ink"
                          }`}
                        >
                          {bar.label}
                        </span>
                        <span
                          data-numeric
                          class={`w-20 shrink-0 text-right text-sm ${
                            bar.kind === "off" ? "text-ink-faint" : "font-medium text-ink"
                          }`}
                        >
                          {bp(bar.basisPoints)} bp
                        </span>
                      </div>
                      {/* The word for what the bar is. The second encoder, and the one that survives greyscale. */}
                      <p class="eyebrow mt-0.5">{bar.tag}</p>
                      <Bar bar={bar} scale={scale()} />
                    </li>
                  )}
                </For>
              </ul>
            </section>
          )}
        </For>
      </div>

      {/* Shared axis. End labels are anchored inward so neither hangs off the page. */}
      <div class="relative mt-4 h-4" aria-hidden="true">
        <For each={scale().ticks}>
          {(tick, index) => (
            <span
              data-numeric
              class="absolute top-0 text-2xs text-ink-faint"
              style={{
                left: `${scale().pct(tick)}%`,
                transform:
                  index() === 0
                    ? "none"
                    : index() === scale().ticks.length - 1
                      ? "translateX(-100%)"
                      : "translateX(-50%)",
              }}
            >
              {bp(tick)}
            </span>
          )}
        </For>
      </div>
      <p class="mt-2 max-w-measure text-xs text-ink-faint">
        Basis points a year. One scale across all three blocks, so the lengths are comparable. The blocks are not: they
        are measured against different benchmarks, and their totals do not add. A solid bar is inside its own block's
        total; an outlined bar is in no total at all.
      </p>

      {/*
        The wrapper carries `sr-only`, not the table. `sr-only` works by pinning a box to
        1px and clipping the overflow, and a `display: table` element sizes to its content
        and ignores that width — so classing the table directly left a 1538px box hanging
        off the page, 305px of horizontal scroll at 1280 and 1197px at 360. A block-level
        wrapper clips properly.
      */}
      <div class="sr-only">
        <table>
          <caption>{props.caption}</caption>
          <thead>
            <tr>
              <th scope="col">Benchmark</th>
              <th scope="col">Line</th>
              <th scope="col">Basis points a year</th>
              <th scope="col">In its benchmark's total</th>
            </tr>
          </thead>
          <tbody>
            <For each={props.groups}>
              {(group) => (
                <For each={group.bars}>
                  {(bar) => (
                    <tr>
                      <td>{group.benchmark}</td>
                      <th scope="row">{bar.label}</th>
                      <td>{bp(bar.basisPoints)}</td>
                      <td>
                        {bar.kind === "counted" || bar.kind === "subtotal" ? `Yes — ${bar.tag}` : `No — ${bar.tag}`}
                      </td>
                    </tr>
                  )}
                </For>
              )}
            </For>
          </tbody>
        </table>
      </div>

      <Show when={props.footnote}>
        <p class="mt-3 max-w-measure text-xs text-ink-muted">{props.footnote}</p>
      </Show>
    </figure>
  );
}
