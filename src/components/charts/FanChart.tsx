import { createMemo, createSignal, For, type JSX, onCleanup, onMount, Show } from "solid-js";
import { linearScale, linePath, niceDomain, niceTicks } from "~/components/charts/scale";
import { DataTable } from "~/components/DataTable";

/**
 * Relative wealth against the benchmark, as a fan of percentile bands.
 *
 * The one thing this figure exists to show is the horizontal line at 1.0. Everything
 * above it is being ahead and everything below it is being behind, and the interesting
 * fact about a small edge against a large tracking error is how much of the fan sits
 * under that line for how long.
 *
 * **No colour carries meaning.** The bands are distinguished by fill density alone, so
 * the figure survives greyscale and colour blindness — and because density alone cannot
 * name a percentile, the table underneath is not an alternative view but the primary
 * one: it prints the same five numbers at four horizons, always visible.
 */

export interface FanBands {
  readonly p05: readonly number[];
  readonly p25: readonly number[];
  readonly p50: readonly number[];
  readonly p75: readonly number[];
  readonly p95: readonly number[];
}

export interface FanChartProps {
  readonly bands: FanBands;
  readonly horizonYears: number;
  /** Says what the picture shows. A screen reader gets this instead of the picture. */
  readonly ariaLabel: string;
  readonly caption?: JSX.Element;
  readonly tableCaption: string;
}

interface FanRow {
  readonly year: number;
  readonly p05: number;
  readonly p25: number;
  readonly p50: number;
  readonly p75: number;
  readonly p95: number;
}

const DEFAULT_WIDTH = 720;
const MONTHS_PER_YEAR = 12;

function formatMultiple(value: number): string {
  return `${value.toFixed(2)}×`;
}

export function FanChart(props: FanChartProps): JSX.Element {
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

  const geometry = createMemo(() => {
    const w = Math.max(300, Math.round(width()));
    const compact = w < 560;
    const h = Math.round(Math.min(420, Math.max(260, w * 0.52)));
    const left = compact ? 44 : 56;
    const right = compact ? 16 : 56;
    const top = 16;
    const bottom = compact ? 44 : 48;
    return { w, h, compact, left, right, top, bottom, plotWidth: w - left - right, plotHeight: h - top - bottom };
  });

  const domain = createMemo<[number, number]>(() => {
    const low = Math.min(1, ...props.bands.p05);
    const high = Math.max(1, ...props.bands.p95);
    return niceDomain(low, high, 5);
  });

  const months = () => Math.max(1, props.bands.p50.length - 1);

  const x = (index: number) => {
    const g = geometry();
    return g.left + (index / months()) * g.plotWidth;
  };
  const y = createMemo(() => {
    const g = geometry();
    return linearScale(domain(), [g.top + g.plotHeight, g.top]);
  });

  const points = (series: readonly number[]) => series.map((value, index) => [x(index), y()(value)] as const);

  const outer = () => {
    const upper = points(props.bands.p95);
    const lower = [...points(props.bands.p05)].reverse();
    return `${linePath(upper)}${linePath(lower).replace("M", "L")}Z`;
  };
  const inner = () => {
    const upper = points(props.bands.p75);
    const lower = [...points(props.bands.p25)].reverse();
    return `${linePath(upper)}${linePath(lower).replace("M", "L")}Z`;
  };

  const ticks = createMemo(() => niceTicks(domain()[0], domain()[1], 5));

  const yearTicks = createMemo(() => {
    const total = props.horizonYears;
    const step = total <= 10 ? 2 : total <= 30 ? 5 : 10;
    const out: number[] = [];
    for (let year = 0; year <= total + 1e-9; year += step) {
      out.push(year);
    }
    return out;
  });

  const tableRows = createMemo<FanRow[]>(() => {
    const total = props.horizonYears;
    const marks = [1, 5, 10, total].filter((year, index, all) => year <= total && all.indexOf(year) === index);
    return marks.map((year) => {
      const index = Math.min(months(), Math.round(year * MONTHS_PER_YEAR));
      return {
        year,
        p05: props.bands.p05[index] ?? Number.NaN,
        p25: props.bands.p25[index] ?? Number.NaN,
        p50: props.bands.p50[index] ?? Number.NaN,
        p75: props.bands.p75[index] ?? Number.NaN,
        p95: props.bands.p95[index] ?? Number.NaN,
      };
    });
  });

  return (
    <figure ref={wrapper}>
      <svg
        viewBox={`0 0 ${geometry().w} ${geometry().h}`}
        width="100%"
        height={geometry().h}
        role="img"
        aria-label={props.ariaLabel}
        class="block"
      >
        <title>{props.ariaLabel}</title>

        {/* Gridlines and the value axis. */}
        <For each={ticks()}>
          {(tick) => (
            <g>
              <line
                x1={geometry().left}
                x2={geometry().w - geometry().right}
                y1={y()(tick)}
                y2={y()(tick)}
                stroke="var(--rule)"
                stroke-width="1"
              />
              <text
                x={geometry().left - 8}
                y={y()(tick)}
                text-anchor="end"
                dominant-baseline="middle"
                class="fill-[var(--ink-faint)] text-[11px] tabular-nums"
              >
                {formatMultiple(tick)}
              </text>
            </g>
          )}
        </For>

        <path d={outer()} fill="var(--ink)" opacity="0.10" />
        <path d={inner()} fill="var(--ink)" opacity="0.20" />
        <path d={linePath(points(props.bands.p50))} fill="none" stroke="var(--accent)" stroke-width="2.2" />

        {/* Level pegging with the benchmark: the line the whole figure is about. */}
        <line
          x1={geometry().left}
          x2={geometry().w - geometry().right}
          y1={y()(1)}
          y2={y()(1)}
          stroke="var(--ink)"
          stroke-width="1.4"
          stroke-dasharray="5 4"
        />
        <text x={geometry().left + 4} y={y()(1) - 6} class="fill-[var(--ink-muted)] text-[11px]">
          level with the benchmark
        </text>

        {/* Year axis. */}
        <line
          x1={geometry().left}
          x2={geometry().w - geometry().right}
          y1={geometry().top + geometry().plotHeight}
          y2={geometry().top + geometry().plotHeight}
          stroke="var(--rule-strong)"
          stroke-width="1"
        />
        <For each={yearTicks()}>
          {(year) => (
            <text
              x={x(Math.min(months(), year * MONTHS_PER_YEAR))}
              y={geometry().top + geometry().plotHeight + 18}
              text-anchor="middle"
              class="fill-[var(--ink-faint)] text-[11px] tabular-nums"
            >
              {year}
            </text>
          )}
        </For>
        <text
          x={geometry().left + geometry().plotWidth / 2}
          y={geometry().h - 6}
          text-anchor="middle"
          class="fill-[var(--ink-muted)] text-[11px]"
        >
          Years held
        </text>
      </svg>

      <DataTable
        class="mt-6"
        caption={props.tableCaption}
        columns={[
          { key: "year", header: "Years", rowHeader: true, cell: (row: FanRow) => String(row.year) },
          { key: "p05", header: "5th", numeric: true, cell: (row: FanRow) => formatMultiple(row.p05) },
          { key: "p25", header: "25th", numeric: true, cell: (row: FanRow) => formatMultiple(row.p25) },
          { key: "p50", header: "Median", numeric: true, cell: (row: FanRow) => formatMultiple(row.p50) },
          { key: "p75", header: "75th", numeric: true, cell: (row: FanRow) => formatMultiple(row.p75) },
          { key: "p95", header: "95th", numeric: true, cell: (row: FanRow) => formatMultiple(row.p95) },
        ]}
        rows={tableRows()}
        footnote={
          <>
            Wealth relative to the benchmark. 1.00× is level; 0.90× is 10% behind. These are percentiles across
            simulated paths, not a forecast, and they are only as good as the edge and tracking error you set.
          </>
        }
      />

      <Show when={props.caption}>
        <figcaption class="mt-3 max-w-measure text-sm text-ink-muted">{props.caption}</figcaption>
      </Show>
    </figure>
  );
}
