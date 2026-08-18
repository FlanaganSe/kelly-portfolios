import { createMemo, createSignal, For, type JSX, onCleanup, onMount, Show } from "solid-js";
import { linearScale, linePath, niceDomain, niceTicks } from "~/components/charts/scale";
import { DataTable } from "~/components/DataTable";
import { monthOfYear, toYearMonth, yearOf } from "~/lib/backtest/calendar";
import type { MonthIndex } from "~/lib/backtest/types";

/**
 * Several monthly series on one time axis. Growth, drawdown, rolling excess — the shape
 * is the same and only the value axis changes.
 *
 * Hand-rolled inline SVG, like every other figure here. There is no charting dependency.
 *
 * **Identity is not carried by colour.** The site's palette is warm paper, near-black
 * ink and one accent; it has no categorical ramp, and the pairs it does have fail the
 * colour-blindness check that governs one (see the note at the top of
 * `OutperformanceChart.tsx`). So every line is named at its own right-hand end, with a
 * leader back to the point it names, and takes a distinct dash pattern. The figure reads
 * the same in greyscale, on a printout and under full colour blindness.
 *
 * **The log axis is opt-in and refuses itself when it cannot be honest.** A ratio scale
 * is the right one for growth, where a doubling should look the same wherever it
 * happens, and is undefined for the drawdown and excess-return charts, which cross zero.
 * Asking for it on a series that touches zero gets a linear axis and a printed note
 * rather than a chart with holes in it.
 */

export interface TimeSeriesSeries {
  readonly id: string;
  /** The end-of-line label. Keep it under about 22 characters. */
  readonly label: string;
  /** The end-of-line label on a narrow screen. Keep it under about 10 characters. */
  readonly abbr?: string;
  /** One value per month, starting at the chart's `start`. May be shorter than a peer. */
  readonly values: readonly number[];
  /** Drawn solid and heavier. At most one series should set it. */
  readonly emphasis?: boolean;
}

export interface TimeSeriesChartProps {
  readonly series: readonly TimeSeriesSeries[];
  /** The month of index 0 in every series. */
  readonly start: MonthIndex;
  /** Says what the picture shows. A screen reader gets this instead of the picture. */
  readonly ariaLabel: string;
  /** Ratio value axis. Declined, with a note, when any value is at or below zero. */
  readonly logScale?: boolean;
  /** A horizontal reference line: 1 for growth of a unit, 0 for a difference. */
  readonly baseline?: number;
  readonly baselineLabel?: string;
  readonly formatValue?: (value: number) => string;
  readonly valueAxisLabel?: string;
  /** Renders the table alternative, one row per year end. Omit to leave it out. */
  readonly tableCaption?: string;
  readonly caption?: JSX.Element;
  readonly class?: string;
}

const DEFAULT_WIDTH = 720;
const MONTHS_PER_YEAR = 12;

/** The emphasised line is solid; the rest take one each, in order. */
const DASH_PATTERNS = ["6 4", "2 3", "12 5", "1 3 7 3", "9 3 2 3"] as const;

/** Multipliers a ratio axis can land on, so a log tick is still a readable number. */
const LOG_MANTISSAS = [1, 1.5, 2, 3, 5, 7] as const;

function defaultFormat(value: number): string {
  return value.toFixed(2);
}

/** Ticks for a ratio axis: nice multiples of a power of ten inside the domain. */
export function logTicks(low: number, high: number): number[] {
  if (!(low > 0) || !(high > low)) {
    return [];
  }
  const ticks: number[] = [];
  for (let power = Math.floor(Math.log10(low)); power <= Math.ceil(Math.log10(high)); power += 1) {
    for (const mantissa of LOG_MANTISSAS) {
      const value = mantissa * 10 ** power;
      if (value >= low && value <= high) {
        ticks.push(value);
      }
    }
  }
  // Two ticks is not an axis. Fall back to the ends rather than draw a bare frame.
  return ticks.length >= 2 ? ticks : [low, high];
}

export function TimeSeriesChart(props: TimeSeriesChartProps): JSX.Element {
  const [width, setWidth] = createSignal(DEFAULT_WIDTH);
  let wrapper: HTMLDivElement | undefined;

  onMount(() => {
    const element = wrapper;
    if (element === undefined || typeof ResizeObserver === "undefined") {
      return;
    }
    const observer = new ResizeObserver((entries) => {
      const measured = entries[0]?.contentRect.width;
      if (measured !== undefined && measured > 0) {
        setWidth(measured);
      }
    });
    observer.observe(element);
    onCleanup(() => observer.disconnect());
  });

  const format = (value: number) => (props.formatValue ?? defaultFormat)(value);

  const drawn = createMemo(() => props.series.filter((one) => one.values.length > 0));

  /** The longest series sets the time axis; a shorter one simply stops early. */
  const months = createMemo(() => Math.max(1, ...drawn().map((one) => one.values.length)));

  const finite = createMemo(() => drawn().flatMap((one) => one.values.filter((value) => Number.isFinite(value))));

  const positiveOnly = createMemo(() => finite().length > 0 && finite().every((value) => value > 0));
  const useLog = createMemo(() => props.logScale === true && positiveOnly());
  const declinedLog = createMemo(() => props.logScale === true && !positiveOnly());

  const geometry = createMemo(() => {
    const w = Math.max(300, Math.round(width()));
    const compact = w < 560;
    const h = Math.round(Math.min(400, Math.max(240, w * 0.5)));
    const left = compact ? 46 : 58;
    const right = compact ? 62 : 118;
    const top = 16;
    const bottom = compact ? 40 : 46;
    return {
      w,
      h,
      compact,
      plotLeft: left,
      plotRight: w - right,
      plotTop: top,
      plotBottom: h - bottom,
      plotWidth: w - left - right,
      plotHeight: h - top - bottom,
    };
  });

  /** In value space for a linear axis, in log10 space for a ratio one. */
  const domain = createMemo<[number, number]>(() => {
    const values = finite();
    if (values.length === 0) {
      return [0, 1];
    }
    if (useLog()) {
      const low = Math.log10(Math.min(...values));
      const high = Math.log10(Math.max(...values));
      return low === high ? [low - 0.1, high + 0.1] : [low, high];
    }
    const baseline = props.baseline;
    const low = Math.min(...values, ...(baseline === undefined ? [] : [baseline]));
    const high = Math.max(...values, ...(baseline === undefined ? [] : [baseline]));
    return niceDomain(low, high, 5);
  });

  const y = createMemo(() => {
    const g = geometry();
    return linearScale(domain(), [g.plotBottom, g.plotTop]);
  });

  const yOf = (value: number): number => {
    if (!Number.isFinite(value)) {
      return Number.NaN;
    }
    return useLog() ? (value > 0 ? y()(Math.log10(value)) : Number.NaN) : y()(value);
  };

  const xOf = (index: number): number => {
    const g = geometry();
    const span = Math.max(1, months() - 1);
    return g.plotLeft + (index / span) * g.plotWidth;
  };

  const valueTicks = createMemo(() => {
    const [low, high] = domain();
    return useLog() ? logTicks(10 ** low, 10 ** high) : niceTicks(low, high, 5);
  });

  /** January of each year in the window, thinned so the labels never collide. */
  const yearTicks = createMemo(() => {
    const firstYear = yearOf(props.start);
    const lastYear = yearOf(props.start + months() - 1);
    const span = Math.max(1, lastYear - firstYear);
    const room = Math.max(2, Math.floor(geometry().plotWidth / (geometry().compact ? 52 : 64)));
    const step = Math.max(1, Math.ceil(span / room));
    const ticks: { readonly index: number; readonly year: number }[] = [];
    for (let year = firstYear + (monthOfYear(props.start) === 0 ? 0 : 1); year <= lastYear; year += step) {
      const index = (year - firstYear) * MONTHS_PER_YEAR - monthOfYear(props.start);
      if (index >= 0 && index < months()) {
        ticks.push({ index, year });
      }
    }
    return ticks;
  });

  interface Resolved extends TimeSeriesSeries {
    readonly dash: string | undefined;
    readonly strokeWidth: number;
    readonly color: string;
  }

  const resolved = createMemo<readonly Resolved[]>(() => {
    let plain = 0;
    return drawn().map((series) => ({
      ...series,
      dash: series.emphasis === true ? undefined : DASH_PATTERNS[plain++ % DASH_PATTERNS.length],
      strokeWidth: series.emphasis === true ? 2.4 : 1.7,
      color: series.emphasis === true ? "var(--accent)" : "var(--ink-muted)",
    }));
  });

  const pathOf = (series: Resolved): string =>
    linePath(series.values.map((value, index) => [xOf(index), yOf(value)] as const));

  /**
   * End labels, pushed apart where lines converge, each keeping a leader back to the
   * point it names. Without this a benchmark that finishes level with the portfolio
   * prints two labels on top of each other.
   */
  const endLabels = createMemo(() => {
    const g = geometry();
    const gap = g.compact ? 13 : 15;
    const placed = resolved()
      .map((series) => {
        const lastIndex = series.values.length - 1;
        return {
          series,
          endX: xOf(lastIndex),
          endY: yOf(series.values[lastIndex] ?? Number.NaN),
          labelY: 0,
        };
      })
      .filter((item) => Number.isFinite(item.endY))
      .sort((a, b) => a.endY - b.endY);

    let previous = g.plotTop + 4 - gap;
    for (const item of placed) {
      item.labelY = Math.max(item.endY, previous + gap);
      previous = item.labelY;
    }
    const overflow = (placed.at(-1)?.labelY ?? 0) - g.plotBottom;
    if (overflow > 0) {
      for (const item of placed) {
        item.labelY -= overflow;
      }
    }
    return placed;
  });

  /** One row per year end, plus the last month, which is rarely a December. */
  const tableRows = createMemo(() => {
    const indices: number[] = [];
    for (let index = 0; index < months(); index += 1) {
      if (monthOfYear(props.start + index) === 11) {
        indices.push(index);
      }
    }
    const last = months() - 1;
    if (indices.at(-1) !== last) {
      indices.push(last);
    }
    return indices.map((index) => ({ index, month: toYearMonth(props.start + index) }));
  });

  return (
    <figure class={`m-0 ${props.class ?? ""}`}>
      <div ref={wrapper} class="w-full">
        <svg
          role="img"
          aria-label={props.ariaLabel}
          viewBox={`0 0 ${geometry().w} ${geometry().h}`}
          preserveAspectRatio="xMidYMid meet"
          style={{ width: "100%", height: "auto", display: "block" }}
        >
          <title>{props.ariaLabel}</title>

          <g stroke="var(--rule)" stroke-width="1">
            <For each={valueTicks()}>
              {(tick) => <line x1={geometry().plotLeft} x2={geometry().plotRight} y1={yOf(tick)} y2={yOf(tick)} />}
            </For>
          </g>

          <g class="fill-[var(--ink-faint)] text-[11px] tabular-nums">
            <For each={valueTicks()}>
              {(tick) => (
                <text x={geometry().plotLeft - 8} y={yOf(tick)} text-anchor="end" dominant-baseline="middle">
                  {format(tick)}
                </text>
              )}
            </For>
          </g>

          {/* The reference line: level with the benchmark, or no drawdown, or no excess. */}
          <Show when={props.baseline !== undefined && Number.isFinite(yOf(props.baseline ?? 0))}>
            <line
              x1={geometry().plotLeft}
              x2={geometry().plotRight}
              y1={yOf(props.baseline ?? 0)}
              y2={yOf(props.baseline ?? 0)}
              stroke="var(--ink)"
              stroke-width="1.3"
              stroke-dasharray="5 4"
            />
            <Show when={props.baselineLabel}>
              {(label) => (
                <text
                  x={geometry().plotLeft + 4}
                  y={yOf(props.baseline ?? 0) - 5}
                  class="fill-[var(--ink-muted)] text-[10px]"
                >
                  {label()}
                </text>
              )}
            </Show>
          </Show>

          <line
            x1={geometry().plotLeft}
            x2={geometry().plotRight}
            y1={geometry().plotBottom}
            y2={geometry().plotBottom}
            stroke="var(--rule-strong)"
            stroke-width="1"
          />
          <For each={yearTicks()}>
            {(tick) => (
              <text
                x={xOf(tick.index)}
                y={geometry().plotBottom + 17}
                text-anchor="middle"
                class="fill-[var(--ink-faint)] text-[11px] tabular-nums"
              >
                {tick.year}
              </text>
            )}
          </For>

          <Show when={props.valueAxisLabel && !geometry().compact}>
            {(label) => (
              <text
                transform={`translate(14 ${geometry().plotTop + geometry().plotHeight / 2}) rotate(-90)`}
                text-anchor="middle"
                class="fill-[var(--ink-muted)] text-[11px]"
              >
                {label()}
              </text>
            )}
          </Show>

          <For each={resolved()}>
            {(series) => (
              <path
                d={pathOf(series)}
                fill="none"
                stroke={series.color}
                stroke-width={series.strokeWidth}
                stroke-dasharray={series.dash}
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            )}
          </For>

          {/* Direct labels. Identity lives here, not in a colour swatch. */}
          <For each={endLabels()}>
            {(item) => (
              <g>
                <path
                  d={`M${item.endX} ${item.endY} L${geometry().plotRight + 6} ${item.labelY - 3}`}
                  fill="none"
                  stroke={item.series.color}
                  stroke-width="1"
                  opacity="0.5"
                />
                <text
                  x={geometry().plotRight + 9}
                  y={item.labelY}
                  class="fill-[var(--ink)] text-[11px] font-semibold"
                  style={{ "font-size": geometry().compact ? "10px" : "11px" }}
                >
                  {geometry().compact ? (item.series.abbr ?? item.series.label) : item.series.label}
                </text>
              </g>
            )}
          </For>
        </svg>
      </div>

      <Show when={props.caption}>
        <figcaption class="mt-3 max-w-measure text-sm text-ink-muted">{props.caption}</figcaption>
      </Show>

      <Show when={declinedLog()}>
        <p class="mt-2 max-w-measure text-sm text-ink-muted">
          A ratio axis was asked for and declined: this series reaches zero or below, where the logarithm is not
          defined. The axis shown is linear.
        </p>
      </Show>

      <Show when={props.tableCaption}>
        {(caption) => (
          <details class="mt-3">
            <summary class="cursor-pointer text-sm text-ink-muted hover:text-ink">Read the chart as a table</summary>
            <div class="mt-3">
              <DataTable
                caption={caption()}
                columns={[
                  {
                    key: "month",
                    header: "Month",
                    rowHeader: true,
                    cell: (row: { readonly index: number; readonly month: string }) => row.month,
                  },
                  ...resolved().map((series) => ({
                    key: series.id,
                    header: series.label,
                    numeric: true,
                    cell: (row: { readonly index: number; readonly month: string }) => {
                      const value = series.values[row.index];
                      return value === undefined || !Number.isFinite(value) ? "—" : format(value);
                    },
                  })),
                ]}
                rows={tableRows()}
                footnote="Year ends, plus the last month of the window."
              />
            </div>
          </details>
        )}
      </Show>
    </figure>
  );
}
