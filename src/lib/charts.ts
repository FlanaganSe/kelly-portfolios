/**
 * The arithmetic behind the build-time charts: scales, ticks, paths, drawdowns and the
 * dollar and percent formats the chart labels print.
 *
 * The components under `src/components/` stay thin and call these. Everything here is a
 * pure function of numbers, so it is tested in `charts.test.ts` with fixtures computed by
 * hand rather than by rendering an SVG and reading it back.
 *
 * A series is the shape the research emitter writes to `src/content/series/*.json`: a
 * monthly index level starting from $10,000, and a date for every level.
 */

import { formatDollars as formatWholeDollars } from "~/lib/format";

export interface Series {
  readonly id: string;
  readonly label: string;
  /** Monthly level in dollars from the start amount. */
  readonly values: readonly number[];
  /** `YYYY-MM`, one per value. */
  readonly dates: readonly string[];
}

/** Two coordinates. */
export type Point = readonly [x: number, y: number];

// ---------------------------------------------------------------------------
// Formats.
// ---------------------------------------------------------------------------

const MINUS = "\u2212";

/** Round to `digits` significant figures. `roundSignificant(350671, 3)` is 351000. */
export function roundSignificant(value: number, digits: number): number {
  if (value === 0 || !Number.isFinite(value)) return value;
  const magnitude = Math.floor(Math.log10(Math.abs(value)));
  const factor = 10 ** (magnitude - digits + 1);
  return Math.round(value / factor) * factor;
}

/**
 * A dollar amount for a label. `"label"` rounds to three significant figures above
 * $1,000, so $350,671 prints as $351,000 and $4,731 as $4,730: a reader takes in the
 * size of a number on a chart, and a fourth digit is noise there. `"exact"` prints every
 * dollar, for a table, and is `formatDollars` from `format.ts` unchanged.
 */
export function formatDollars(value: number, mode: "label" | "exact" = "label"): string {
  const rounded = mode === "label" && Math.abs(value) >= 1000 ? roundSignificant(value, 3) : value;
  return formatWholeDollars(rounded);
}

/**
 * A percent with a real minus sign. `formatPct(-52.71)` is "−52.7%". Pass `signed` to
 * print a plus on a positive number.
 */
export function formatPct(value: number, decimals = 1, signed = false): string {
  if (!Number.isFinite(value)) return "—";
  const fixed = Math.abs(value).toFixed(decimals);
  const isZero = Number(fixed) === 0;
  const sign = value < 0 && !isZero ? MINUS : signed && !isZero ? "+" : "";
  return `${sign}${fixed}%`;
}

/** "63 months", "1 month", or "not yet" when the fall has not recovered. */
export function formatMonths(months: number | null): string {
  if (months === null) return "not yet";
  return `${months} ${months === 1 ? "month" : "months"}`;
}

// ---------------------------------------------------------------------------
// Dates.
// ---------------------------------------------------------------------------

/** Whole months from one `YYYY-MM` to another. `monthsBetween("2007-10", "2013-01")` is 63. */
export function monthsBetween(from: string, to: string): number {
  const [fy, fm] = splitDate(from);
  const [ty, tm] = splitDate(to);
  return (ty - fy) * 12 + (tm - fm);
}

function splitDate(date: string): [number, number] {
  const match = /^(\d{4})-(\d{2})$/.exec(date);
  if (!match) throw new RangeError(`expected YYYY-MM, got "${date}"`);
  return [Number(match[1]), Number(match[2])];
}

/** The year of a `YYYY-MM` date. */
export function yearOf(date: string): number {
  return splitDate(date)[0];
}

/**
 * The index of the first month of every year divisible by `every`, for the x axis.
 * A series starting in 1990-10 with `every` 5 ticks at 1995-01, 2000-01 and so on; the
 * partial first year is skipped rather than labelled off its true position.
 */
export function yearTicks(dates: readonly string[], every = 5): { index: number; year: number }[] {
  const ticks: { index: number; year: number }[] = [];
  let lastYear = Number.NaN;
  dates.forEach((date, index) => {
    const [year, month] = splitDate(date);
    if (month === 1 && year % every === 0 && year !== lastYear) {
      ticks.push({ index, year });
      lastYear = year;
    }
  });
  return ticks;
}

// ---------------------------------------------------------------------------
// Scales and ticks.
// ---------------------------------------------------------------------------

/** A linear map from `domain` onto `range`. Not clamped. */
export function scaleLinear(domain: readonly [number, number], range: readonly [number, number]) {
  const [d0, d1] = domain;
  const [r0, r1] = range;
  const span = d1 - d0;
  return (value: number): number => (span === 0 ? r0 : r0 + ((value - d0) / span) * (r1 - r0));
}

/** A log map from a positive `domain` onto `range`. Not clamped. */
export function scaleLog(domain: readonly [number, number], range: readonly [number, number]) {
  const [d0, d1] = domain;
  if (d0 <= 0 || d1 <= 0) throw new RangeError("a log scale needs a positive domain");
  const l0 = Math.log(d0);
  const span = Math.log(d1) - l0;
  const [r0, r1] = range;
  return (value: number): number => (span === 0 ? r0 : r0 + ((Math.log(value) - l0) / span) * (r1 - r0));
}

/**
 * Gridline values for a log axis of dollars: 1, 2, 5 times a power of ten, inside
 * `[min, max]`. Growth from $10,000 to $351,000 gives 10k, 20k, 50k, 100k, 200k.
 */
export function growthTicks(min: number, max: number): number[] {
  if (min <= 0 || max < min) return [];
  const ticks: number[] = [];
  let decade = 10 ** Math.floor(Math.log10(min));
  while (decade <= max) {
    for (const step of [1, 2, 5]) {
      const tick = decade * step;
      if (tick >= min && tick <= max) ticks.push(tick);
    }
    decade *= 10;
  }
  return ticks;
}

/**
 * Gridline values for a drawdown axis: 0 down to the floor in steps that keep the count
 * between three and six. A worst fall of −52.7% gives 0, −20, −40, −60.
 */
export function drawdownTicks(worstPct: number): number[] {
  const worst = Math.min(0, worstPct);
  const step = worst <= -45 ? 20 : worst <= -22 ? 10 : 5;
  const floor = Math.floor(worst / step) * step;
  const ticks: number[] = [];
  for (let tick = 0; tick >= floor; tick -= step) ticks.push(tick);
  return ticks;
}

// ---------------------------------------------------------------------------
// Paths.
// ---------------------------------------------------------------------------

function fixed(value: number): string {
  return String(Math.round(value * 100) / 100);
}

/** An SVG path through the points, in order. Empty input gives an empty string. */
export function linePath(points: readonly Point[]): string {
  return points.map(([x, y], i) => `${i === 0 ? "M" : "L"}${fixed(x)} ${fixed(y)}`).join("");
}

/** The line closed down to `baseline`, for an area fill. */
export function areaPath(points: readonly Point[], baseline: number): string {
  if (points.length === 0) return "";
  const first = points[0] as Point;
  const last = points[points.length - 1] as Point;
  return `${linePath(points)}L${fixed(last[0])} ${fixed(baseline)}L${fixed(first[0])} ${fixed(baseline)}Z`;
}

/**
 * Push overlapping labels apart along one axis, keeping their order and staying inside
 * `[lo, hi]`. Positions are centres; two labels closer than `minGap` are spread until
 * they are `minGap` apart. Used for the end labels of a growth chart, where two lines
 * that finish near each other would otherwise print on top of one another.
 */
export function spreadLabels(positions: readonly number[], minGap: number, lo: number, hi: number): number[] {
  const order = positions.map((p, i) => ({ p, i })).sort((a, b) => a.p - b.p);
  const out = order.map((o) => o.p);
  // Relax: every overlapping neighbour pair moves apart by half the overlap, so a pair
  // stays centred on where its lines end, then everything is clamped back inside the
  // plot. A few dozen rounds settle any chain that fits; if it cannot fit, the labels
  // end up evenly packed from `lo`.
  for (let round = 0; round < 64; round++) {
    const moved = relaxNeighbours(out, minGap);
    clampInside(out, minGap, lo, hi);
    if (!moved) break;
  }
  const result = new Array<number>(positions.length);
  order.forEach((o, k) => {
    result[o.i] = Math.round((out[k] as number) * 100) / 100;
  });
  return result;
}

/** One pass of pushing sorted neighbours apart to `minGap`. Returns whether anything moved. */
function relaxNeighbours(sorted: number[], minGap: number): boolean {
  let moved = false;
  for (let k = 1; k < sorted.length; k++) {
    const prev = sorted[k - 1] as number;
    const gap = (sorted[k] as number) - prev;
    if (gap < minGap - 1e-9) {
      const shift = (minGap - gap) / 2;
      sorted[k - 1] = prev - shift;
      sorted[k] = (sorted[k] as number) + shift;
      moved = true;
    }
  }
  return moved;
}

/** Push a sorted list back inside `[lo, hi]`, keeping neighbours `minGap` apart. */
function clampInside(sorted: number[], minGap: number, lo: number, hi: number): void {
  for (let k = 0; k < sorted.length; k++) {
    const floor = k === 0 ? lo : (sorted[k - 1] as number) + minGap;
    if ((sorted[k] as number) < floor) sorted[k] = Math.min(floor, hi);
  }
  for (let k = sorted.length - 1; k >= 0; k--) {
    const cap = k === sorted.length - 1 ? hi : (sorted[k + 1] as number) - minGap;
    if ((sorted[k] as number) > cap) sorted[k] = Math.max(cap, lo);
  }
}

// ---------------------------------------------------------------------------
// Drawdowns.
// ---------------------------------------------------------------------------

/** Percent below the running peak at every month. Zero at a new high, never positive. */
export function drawdowns(values: readonly number[]): number[] {
  let peak = Number.NEGATIVE_INFINITY;
  return values.map((v) => {
    if (v > peak) peak = v;
    return peak > 0 ? ((v - peak) / peak) * 100 : 0;
  });
}

export interface Episode {
  /** The fall, as a negative percent of the peak. */
  readonly pct: number;
  readonly peakIndex: number;
  readonly troughIndex: number;
  /** The first month back at or above the peak, or null if it never got there. */
  readonly recoveredIndex: number | null;
  readonly peak: string;
  readonly trough: string;
  readonly recovered: string | null;
  /** Months from the peak to the recovery, the way the site quotes it. */
  readonly monthsToRecover: number | null;
  /** What `start` dollars at the peak had become at the trough. */
  readonly dollarsAtTrough: number;
}

/**
 * The deepest fall in the series, with the dates that bound it. `start` is the amount
 * the dollar figure is quoted on, $10,000 by default. Null for a series that never
 * falls.
 */
export function worstFall(series: Pick<Series, "values" | "dates">, start = 10000): Episode | null {
  const { values, dates } = series;
  if (values.length !== dates.length) throw new RangeError("values and dates differ in length");
  let peakIndex = 0;
  let worst: { pct: number; peakIndex: number; troughIndex: number } | null = null;
  values.forEach((v, i) => {
    const peak = values[peakIndex] as number;
    if (v > peak) {
      peakIndex = i;
      return;
    }
    const pct = peak > 0 ? ((v - peak) / peak) * 100 : 0;
    if (pct < 0 && (worst === null || pct < worst.pct)) worst = { pct, peakIndex, troughIndex: i };
  });
  if (worst === null) return null;
  const found: { pct: number; peakIndex: number; troughIndex: number } = worst;
  const peakValue = values[found.peakIndex] as number;
  let recoveredIndex: number | null = null;
  for (let i = found.troughIndex + 1; i < values.length; i++) {
    if ((values[i] as number) >= peakValue) {
      recoveredIndex = i;
      break;
    }
  }
  const peak = dates[found.peakIndex] as string;
  const recovered = recoveredIndex === null ? null : (dates[recoveredIndex] as string);
  return {
    pct: found.pct,
    peakIndex: found.peakIndex,
    troughIndex: found.troughIndex,
    recoveredIndex,
    peak,
    trough: dates[found.troughIndex] as string,
    recovered,
    monthsToRecover: recovered === null ? null : monthsBetween(peak, recovered),
    dollarsAtTrough: Math.round(start * (1 + found.pct / 100)),
  };
}

// ---------------------------------------------------------------------------
// Donut arcs.
// ---------------------------------------------------------------------------

export interface Arc {
  readonly index: number;
  readonly fraction: number;
  /** Degrees clockwise from twelve o'clock. */
  readonly start: number;
  readonly end: number;
}

/** Each weight as a share of the total and its angular span, in input order from the top. */
export function donutArcs(weights: readonly number[]): Arc[] {
  const total = weights.reduce((sum, w) => sum + Math.max(0, w), 0);
  if (total <= 0) return [];
  let angle = 0;
  return weights.map((w, index) => {
    const fraction = Math.max(0, w) / total;
    const start = angle;
    angle += fraction * 360;
    return { index, fraction, start, end: angle };
  });
}

function polar(cx: number, cy: number, r: number, degrees: number): Point {
  const rad = ((degrees - 90) * Math.PI) / 180;
  return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
}

/**
 * An SVG path for one ring segment from `start` to `end` degrees. A full circle is drawn
 * as two half arcs, because an arc command whose ends coincide draws nothing.
 */
export function arcPath(cx: number, cy: number, outer: number, inner: number, start: number, end: number): string {
  const sweep = Math.min(360, Math.max(0, end - start));
  if (sweep <= 0) return "";
  if (sweep >= 360) {
    return [
      arcPath(cx, cy, outer, inner, start, start + 180),
      arcPath(cx, cy, outer, inner, start + 180, start + 360),
    ].join("");
  }
  const large = sweep > 180 ? 1 : 0;
  const [ox0, oy0] = polar(cx, cy, outer, start);
  const [ox1, oy1] = polar(cx, cy, outer, end);
  const [ix0, iy0] = polar(cx, cy, inner, start);
  const [ix1, iy1] = polar(cx, cy, inner, end);
  return (
    `M${fixed(ox0)} ${fixed(oy0)}` +
    `A${outer} ${outer} 0 ${large} 1 ${fixed(ox1)} ${fixed(oy1)}` +
    `L${fixed(ix1)} ${fixed(iy1)}` +
    `A${inner} ${inner} 0 ${large} 0 ${fixed(ix0)} ${fixed(iy0)}Z`
  );
}
