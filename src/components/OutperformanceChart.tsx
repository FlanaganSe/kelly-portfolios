import { createMemo, createSignal, For, type JSX, onCleanup, onMount, Show } from "solid-js";
import { DataTable } from "~/components/DataTable";
import { probabilityOfOutperformance } from "~/lib/horizon";

/**
 * `P(ahead of the benchmark)` against horizon, one curve per edge / tracking-error pair.
 *
 * Hand-rolled inline SVG. There is no charting dependency and there is not going to be
 * one: the whole figure is five lines, an axis and a set of labels.
 *
 * **Why colour carries almost nothing here.** The site's palette is warm paper, near
 * black ink, one blue accent and four tone colours. Fed to the colour-blindness check
 * that governs categorical palettes, every pair of it fails: green against grey is
 * ΔE 3.4 under deuteranopia and 10.0 under normal vision in light mode, 3.0 and 10.2 in
 * dark, against thresholds of 8 and 15. That is not a defect to route around — the
 * palette is deliberately quiet — so identity is carried by things that survive
 * greyscale, a printout and full colour blindness:
 *
 * - a **direct label at the right-hand end of every curve**, with a leader line, so no
 *   reader ever matches a colour to a legend swatch;
 * - a **distinct dash pattern** per probabilistic curve;
 * - **vertical position**, which in this figure is the argument: the contractual curve
 *   is pinned to the top of the plot and the tilts crawl along the bottom.
 *
 * Colour then only reinforces the certainty class — green for the contractual line,
 * muted ink for the bets, the accent for the reader's own inputs — and removing it
 * entirely would cost the figure nothing it needs.
 *
 * **The x-axis is square-rooted**, because `P = Phi(e sqrt(T) / s)` runs on `sqrt(T)`:
 * a linear axis spends four fifths of its width on the part where nothing changes and
 * buries the first year, which is exactly where the contractual line does its work. The
 * axis says so in its own title, and the tick spacing shows it.
 */

/** One curve. Everything but `abbr` and `kind` comes straight from `src/content/`. */
export interface OutperformanceSeries {
  readonly id: string;
  /** The gutter label. Keep it under about 26 characters. */
  readonly label: string;
  /** The gutter label on a narrow screen. Keep it under about 14 characters. */
  readonly abbr: string;
  /** The row header in the table view. Say the whole thing here. */
  readonly fullLabel: string;
  readonly edgeBp: number;
  readonly trackingErrorBp: number;
  readonly kind: SeriesKind;
}

type SeriesKind = "contractual" | "probabilistic" | "live";

export interface OutperformanceChartProps {
  /** Drawn in order, under the live curve. */
  readonly series: readonly OutperformanceSeries[];
  /** The reader's own inputs. Drawn last, over everything. */
  readonly live?: OutperformanceSeries;
  /** Marked with a vertical rule and a dot on the live curve. */
  readonly horizonYears: number;
  readonly maxYears?: number;
  /** States the comparison in words. A screen reader gets this instead of the picture. */
  readonly ariaLabel: string;
  readonly caption: JSX.Element;
  readonly tableCaption: string;
  /** The standing upper-bound warning. Printed under the table view. */
  readonly footnote?: JSX.Element;
}

const DEFAULT_MAX_YEARS = 50;
const DEFAULT_WIDTH = 760;
const SAMPLES = 180;
const TABLE_YEARS = [1, 5, 10, 30, 50] as const;

/** Solid for the contractual line; the bets take one each, in order. */
const DASH_PATTERNS = ["7 5", "2 4", "13 6", "1 3 7 3"] as const;

const KIND_COLOR: Readonly<Record<SeriesKind, string>> = {
  contractual: "var(--tone-positive)",
  probabilistic: "var(--ink-muted)",
  live: "var(--accent)",
};

interface ResolvedSeries extends OutperformanceSeries {
  readonly color: string;
  readonly dash: string | undefined;
  readonly strokeWidth: number;
}

/**
 * `P` at a horizon, including the limit at zero the library declines to take.
 *
 * `probabilityOfOutperformance` throws below one year of zero, correctly — the formula
 * is not defined there. The curve still has to start somewhere, and the left edge of
 * the plot is the moment before anything has happened: a coin flip, unless there is no
 * tracking error at all, in which case a positive edge is already banked.
 */
function probabilityAt(series: Pick<OutperformanceSeries, "edgeBp" | "trackingErrorBp">, years: number): number {
  if (years > 0) {
    return probabilityOfOutperformance({
      edgeBp: series.edgeBp,
      trackingErrorBp: series.trackingErrorBp,
      horizonYears: years,
    });
  }
  if (series.trackingErrorBp !== 0) return 0.5;
  if (series.edgeBp > 0) return 1;
  return series.edgeBp < 0 ? 0 : 0.5;
}

/**
 * A probability as a percentage, without claiming precision the arithmetic does not have.
 *
 * Only a tracking error of exactly zero produces exactly 1. Everything else that rounds
 * to 100% is reported as greater than 99.9%, because the difference between "certain"
 * and "certain enough to print" is the subject of this page.
 */
export function formatProbability(probability: number, trackingErrorBp: number): string {
  if (trackingErrorBp === 0 && probability === 1) return "100%";
  if (probability >= 0.9995) return ">99.9%";
  if (probability <= 0.0005) return "<0.1%";
  return `${(probability * 100).toFixed(1)}%`;
}

/** `109` and `15.2` and `-7.8`, never `109.0`. */
export function formatBp(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function pairLabel(series: OutperformanceSeries): string {
  return `${formatBp(series.edgeBp)} vs ${formatBp(series.trackingErrorBp)} bp`;
}

function shortYears(years: number): string {
  if (years < 1) return `${Math.round(years * 12)} mo`;
  if (years < 10) return `${years.toFixed(1)} yr`;
  return `${Math.round(years)} yr`;
}

export function OutperformanceChart(props: OutperformanceChartProps): JSX.Element {
  const [width, setWidth] = createSignal(DEFAULT_WIDTH);
  const [hoverYears, setHoverYears] = createSignal<number | null>(null);
  let wrapper: HTMLDivElement | undefined;

  onMount(() => {
    const element = wrapper;
    if (!element || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver((entries) => {
      const measured = entries[0]?.contentRect.width;
      if (measured && measured > 0) setWidth(measured);
    });
    observer.observe(element);
    onCleanup(() => observer.disconnect());
  });

  const maxYears = () => props.maxYears ?? DEFAULT_MAX_YEARS;

  const resolved = createMemo<readonly ResolvedSeries[]>(() => {
    const live = props.live;
    const ordered = live ? [...props.series, live] : [...props.series];
    let betIndex = 0;
    return ordered.map((series) => {
      const dash = series.kind === "probabilistic" ? DASH_PATTERNS[betIndex++ % DASH_PATTERNS.length] : undefined;
      return {
        ...series,
        color: KIND_COLOR[series.kind],
        dash,
        strokeWidth: series.kind === "live" ? 2.6 : 2,
      };
    });
  });

  /** A negative edge runs the curve under the coin flip, so the axis has to admit it. */
  const yFloor = createMemo(() => (resolved().some((series) => series.edgeBp < 0) ? 0 : 0.5));

  const geometry = createMemo(() => {
    const w = Math.max(300, Math.round(width()));
    const compact = w < 560;
    const h = Math.round(Math.min(470, Math.max(296, w * 0.58)));
    const left = compact ? 40 : 54;
    const right = compact ? 102 : 182;
    const top = 20;
    const bottom = compact ? 50 : 58;
    return {
      w,
      h,
      compact,
      left,
      right,
      plotLeft: left,
      plotRight: w - right,
      plotTop: top,
      plotBottom: h - bottom,
      plotWidth: w - right - left,
      plotHeight: h - bottom - top,
    };
  });

  const xOf = (years: number): number => {
    const g = geometry();
    const fraction = Math.sqrt(Math.max(0, Math.min(years, maxYears()))) / Math.sqrt(maxYears());
    return g.plotLeft + fraction * g.plotWidth;
  };

  const yOf = (probability: number): number => {
    const g = geometry();
    const floor = yFloor();
    const clamped = Math.max(floor, Math.min(1, probability));
    return g.plotBottom - ((clamped - floor) / (1 - floor)) * g.plotHeight;
  };

  const pathFor = (series: ResolvedSeries): string => {
    const top = maxYears();
    let d = "";
    for (let i = 0; i <= SAMPLES; i += 1) {
      const fraction = i / SAMPLES;
      const years = fraction * fraction * top;
      d += `${i === 0 ? "M" : "L"}${xOf(years).toFixed(2)} ${yOf(probabilityAt(series, years)).toFixed(2)}`;
    }
    return d;
  };

  const xTicks = createMemo(() => {
    const ticks = geometry().compact ? [0, 1, 5, 10, 25, 50] : [0, 1, 2, 5, 10, 20, 30, 40, 50];
    return ticks.filter((tick) => tick <= maxYears());
  });

  const yTicks = createMemo(() => (yFloor() === 0 ? [0, 0.25, 0.5, 0.75, 1] : [0.5, 0.6, 0.7, 0.8, 0.9, 1]));

  /**
   * End labels, pushed apart where curves converge.
   *
   * Stacking a label away from its own line detaches it, so every label keeps a leader
   * back to the point it names. At fifty years the contractual line and a good trend
   * sleeve are four pixels apart, and without this they overprint.
   */
  const endLabels = createMemo(() => {
    const g = geometry();
    const gap = g.compact ? 21 : 25;
    const placed = resolved()
      .map((series) => ({ series, endY: yOf(probabilityAt(series, maxYears())), labelY: 0 }))
      .sort((a, b) => a.endY - b.endY);
    let previous = g.plotTop + 6 - gap;
    for (const item of placed) {
      item.labelY = Math.max(item.endY, previous + gap);
      previous = item.labelY;
    }
    const overflow = (placed.at(-1)?.labelY ?? 0) - g.plotBottom;
    if (overflow > 0) {
      for (const item of placed) item.labelY -= overflow;
    }
    return placed;
  });

  const hoverRows = createMemo(() => {
    const years = hoverYears();
    if (years === null) return null;
    return {
      years,
      x: xOf(years),
      rows: resolved().map((series) => ({
        series,
        probability: probabilityAt(series, years),
        y: yOf(probabilityAt(series, years)),
      })),
    };
  });

  const trackPointer = (event: PointerEvent & { currentTarget: SVGSVGElement }): void => {
    const g = geometry();
    const rect = event.currentTarget.getBoundingClientRect();
    if (rect.width === 0) return;
    const x = ((event.clientX - rect.left) * g.w) / rect.width;
    if (x < g.plotLeft - 4 || x > g.plotRight + 4) {
      setHoverYears(null);
      return;
    }
    const fraction = Math.max(0, Math.min(1, (x - g.plotLeft) / g.plotWidth));
    setHoverYears(fraction * fraction * maxYears());
  };

  const nearRightEdge = () => xOf(props.horizonYears) > geometry().plotRight - 34;

  const tableRows = createMemo(() => resolved());
  const tableYears = createMemo(() => TABLE_YEARS.filter((years) => years <= maxYears()));

  return (
    <figure class="m-0">
      <div ref={wrapper} class="relative w-full">
        <svg
          role="img"
          aria-label={props.ariaLabel}
          viewBox={`0 0 ${geometry().w} ${geometry().h}`}
          preserveAspectRatio="xMidYMid meet"
          style={{ width: "100%", height: "auto", display: "block", "touch-action": "pan-y" }}
          onPointerMove={trackPointer}
          onPointerLeave={() => setHoverYears(null)}
        >
          {/* Grid. Solid hairlines, one step off the surface, and nothing else. */}
          <g stroke="var(--rule)" stroke-width="1">
            <For each={yTicks()}>
              {(tick) => <line x1={geometry().plotLeft} x2={geometry().plotRight} y1={yOf(tick)} y2={yOf(tick)} />}
            </For>
            <For each={xTicks()}>
              {(tick) => <line x1={xOf(tick)} x2={xOf(tick)} y1={geometry().plotTop} y2={geometry().plotBottom} />}
            </For>
          </g>

          {/* The coin flip. Heavier than the grid, because it is the thing to beat. */}
          <line
            x1={geometry().plotLeft}
            x2={geometry().plotRight}
            y1={yOf(0.5)}
            y2={yOf(0.5)}
            stroke="var(--ink-faint)"
            stroke-width="1"
          />
          <text
            x={geometry().plotRight - 6}
            y={yOf(0.5) - 6}
            text-anchor="end"
            fill="var(--ink-faint)"
            stroke="var(--paper)"
            stroke-width="3"
            stroke-linejoin="round"
            paint-order="stroke fill"
            style={{ "font-size": "10px" }}
          >
            50% — a coin flip
          </text>

          {/* Axis ticks. */}
          <g fill="var(--ink-faint)" style={{ "font-size": geometry().compact ? "10px" : "11px" }}>
            <For each={yTicks()}>
              {(tick) => (
                <text x={geometry().plotLeft - 8} y={yOf(tick) + 3.5} text-anchor="end">
                  {`${Math.round(tick * 100)}%`}
                </text>
              )}
            </For>
            <For each={xTicks()}>
              {(tick) => (
                <text x={xOf(tick)} y={geometry().plotBottom + 18} text-anchor="middle">
                  {tick}
                </text>
              )}
            </For>
          </g>

          <line
            x1={geometry().plotLeft}
            x2={geometry().plotRight}
            y1={geometry().plotBottom}
            y2={geometry().plotBottom}
            stroke="var(--rule-strong)"
            stroke-width="1"
          />

          {/* Axis titles. The square root is announced, because an unannounced scale is a lie. */}
          <text
            x={geometry().plotLeft + geometry().plotWidth / 2}
            y={geometry().h - 14}
            text-anchor="middle"
            fill="var(--ink-muted)"
            style={{ "font-size": geometry().compact ? "10px" : "11px" }}
          >
            {geometry().compact ? "Years (square-root scale)" : "Horizon in years — square-root scale"}
          </text>
          <Show when={!geometry().compact}>
            <text
              transform={`translate(15 ${geometry().plotTop + geometry().plotHeight / 2}) rotate(-90)`}
              text-anchor="middle"
              fill="var(--ink-muted)"
              style={{ "font-size": "11px" }}
            >
              Chance you are ahead
            </text>
          </Show>

          {/* The horizon under the sliders, marked on the plot. */}
          <Show when={props.horizonYears > 0 && props.horizonYears <= maxYears()}>
            <line
              x1={xOf(props.horizonYears)}
              x2={xOf(props.horizonYears)}
              y1={geometry().plotTop}
              y2={geometry().plotBottom}
              stroke="var(--rule-strong)"
              stroke-width="1"
            />
            {/* Above the plot, where no curve can run through it. */}
            <text
              x={xOf(props.horizonYears) + (nearRightEdge() ? -5 : 5)}
              y={geometry().plotTop - 6}
              text-anchor={nearRightEdge() ? "end" : "start"}
              fill="var(--ink-faint)"
              stroke="var(--paper)"
              stroke-width="3"
              stroke-linejoin="round"
              paint-order="stroke fill"
              style={{ "font-size": "10px" }}
            >
              {shortYears(props.horizonYears)}
            </text>
          </Show>

          {/* The curves. */}
          <For each={resolved()}>
            {(series) => (
              <path
                d={pathFor(series)}
                fill="none"
                stroke={series.color}
                stroke-width={series.strokeWidth}
                stroke-dasharray={series.dash}
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            )}
          </For>

          {/* The reader's position: a dot with a surface ring, so it reads over any curve. */}
          <Show when={props.live}>
            {(live) => (
              <circle
                cx={xOf(props.horizonYears)}
                cy={yOf(probabilityAt(live(), props.horizonYears))}
                r="4.5"
                fill="var(--accent)"
                stroke="var(--paper)"
                stroke-width="2"
              />
            )}
          </Show>

          {/* Direct labels. Identity lives here, not in a colour swatch. */}
          <For each={endLabels()}>
            {(item) => (
              <g>
                <path
                  d={`M${geometry().plotRight} ${item.endY} C ${geometry().plotRight + 7} ${item.endY}, ${
                    geometry().plotRight + 4
                  } ${item.labelY - 4}, ${geometry().plotRight + 12} ${item.labelY - 4}`}
                  fill="none"
                  stroke={item.series.color}
                  stroke-width="1"
                  opacity="0.55"
                />
                <text
                  x={geometry().plotRight + 15}
                  y={item.labelY}
                  fill="var(--ink)"
                  style={{ "font-size": geometry().compact ? "10px" : "11.5px", "font-weight": "600" }}
                >
                  {geometry().compact ? item.series.abbr : item.series.label}
                </text>
                <text
                  x={geometry().plotRight + 15}
                  y={item.labelY + (geometry().compact ? 10 : 12)}
                  fill="var(--ink-faint)"
                  style={{ "font-size": geometry().compact ? "9px" : "10px" }}
                >
                  {pairLabel(item.series)}
                </text>
              </g>
            )}
          </For>

          {/* Hover crosshair. */}
          <Show when={hoverRows()}>
            {(hover) => (
              <g>
                <line
                  x1={hover().x}
                  x2={hover().x}
                  y1={geometry().plotTop}
                  y2={geometry().plotBottom}
                  stroke="var(--ink-faint)"
                  stroke-width="1"
                />
                <For each={hover().rows}>
                  {(row) => (
                    <circle
                      cx={hover().x}
                      cy={row.y}
                      r="3.5"
                      fill={row.series.color}
                      stroke="var(--paper)"
                      stroke-width="2"
                    />
                  )}
                </For>
              </g>
            )}
          </Show>
        </svg>

        {/* The readout rides in HTML so it wraps and inherits type, and it duplicates
            nothing: every figure in it is in the table view below. */}
        <Show when={hoverRows()}>
          {(hover) => (
            <div
              aria-hidden="true"
              class="pointer-events-none absolute w-[11.5rem] rounded-[3px] border border-rule-strong bg-raised px-2.5 py-2 text-xs shadow-sm"
              style={{
                left: `${Math.min(hover().x + 12, Math.max(0, geometry().w - 190))}px`,
                top: `${geometry().plotTop + 6}px`,
              }}
            >
              <p data-numeric class="eyebrow mb-1.5">
                At {shortYears(hover().years)}
              </p>
              <For each={hover().rows}>
                {(row) => (
                  <p class="flex items-baseline justify-between gap-2 leading-5">
                    <span class="flex min-w-0 items-center gap-1.5">
                      <svg viewBox="0 0 14 2" width="14" height="2" aria-hidden="true" class="shrink-0">
                        <line
                          x1="0"
                          x2="14"
                          y1="1"
                          y2="1"
                          stroke={row.series.color}
                          stroke-width="2"
                          stroke-dasharray={row.series.dash}
                        />
                      </svg>
                      <span class="truncate text-ink-muted">{row.series.abbr}</span>
                    </span>
                    <span data-numeric class="font-semibold text-ink">
                      {formatProbability(row.probability, row.series.trackingErrorBp)}
                    </span>
                  </p>
                )}
              </For>
            </div>
          )}
        </Show>
      </div>

      <figcaption class="mt-3 max-w-measure text-sm text-ink-muted">{props.caption}</figcaption>

      <Show when={yFloor() === 0}>
        <p class="mt-2 max-w-measure text-sm text-ink-muted">
          Your edge is negative, so the y-axis now runs from zero: the curve falls away from the coin flip instead of
          climbing away from it.
        </p>
      </Show>

      <details class="mt-4">
        <summary class="cursor-pointer text-sm text-ink-muted hover:text-ink">Read the chart as a table</summary>
        <div class="mt-3">
          <DataTable
            caption={props.tableCaption}
            columns={[
              {
                key: "series",
                header: "Line",
                rowHeader: true,
                cell: (row: ResolvedSeries) => row.fullLabel,
              },
              {
                key: "pair",
                header: "Edge vs tracking error",
                numeric: true,
                cell: (row: ResolvedSeries) => pairLabel(row),
              },
              ...tableYears().map((years) => ({
                key: `y${years}`,
                header: `${years} yr`,
                numeric: true,
                cell: (row: ResolvedSeries) => formatProbability(probabilityAt(row, years), row.trackingErrorBp),
              })),
            ]}
            rows={tableRows()}
            footnote={props.footnote}
          />
        </div>
      </details>
    </figure>
  );
}
