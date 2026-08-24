/**
 * The arithmetic behind every chart: value → pixel, and where to put a gridline.
 *
 * Kept separate from the components so it can be tested without a DOM, and so two
 * charts on the same page cannot disagree about where a tick belongs.
 */

export interface Scale {
  readonly domain: readonly [number, number];
  readonly range: readonly [number, number];
  (value: number): number;
}

/** A linear scale. A zero-width domain maps everything to the middle of the range. */
export function linearScale(domain: readonly [number, number], range: readonly [number, number]): Scale {
  const [d0, d1] = domain;
  const [r0, r1] = range;
  const span = d1 - d0;
  const scale = ((value: number) => (span === 0 ? (r0 + r1) / 2 : r0 + ((value - d0) / span) * (r1 - r0))) as {
    (value: number): number;
    domain?: readonly [number, number];
    range?: readonly [number, number];
  };
  scale.domain = domain;
  scale.range = range;
  return scale as Scale;
}

const STEPS = [1, 2, 2.5, 5, 10];

/** The smallest "nice" step at or above `rough`: 1, 2, 2.5 or 5 times a power of ten. */
export function niceStep(rough: number): number {
  if (!Number.isFinite(rough) || rough <= 0) {
    return 1;
  }
  const magnitude = 10 ** Math.floor(Math.log10(rough));
  const normalised = rough / magnitude;
  const step = STEPS.find((candidate) => candidate >= normalised - 1e-12) ?? 10;
  return step * magnitude;
}

/**
 * Gridline values covering `[min, max]`, at most `count`-ish of them. Zero is always
 * included when the domain crosses it, because a chart with negative values that
 * hides the zero line misreads at a glance.
 */
export function niceTicks(min: number, max: number, count = 5): number[] {
  if (!Number.isFinite(min) || !Number.isFinite(max) || count < 2) {
    return [];
  }
  if (min === max) {
    return [min];
  }
  const step = niceStep((max - min) / (count - 1));
  const first = Math.ceil(min / step - 1e-12) * step;
  const ticks: number[] = [];
  for (let value = first; value <= max + step * 1e-9; value += step) {
    // Re-round each tick: repeated addition of 0.1 does not stay on 0.1 boundaries.
    ticks.push(Math.round(value / step) * step);
  }
  return ticks;
}

/** Pads a domain outwards to the nearest gridline so the extremes are not clipped. */
export function niceDomain(min: number, max: number, count = 5): [number, number] {
  // A NaN or inverted domain produces a NaN scale, which `linePath` then skips point by
  // point — a silently blank chart rather than a visible failure. Refuse it here instead.
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    return [0, 1];
  }
  if (min > max) {
    return niceDomain(max, min, count);
  }
  if (min === max) {
    return [min - 0.5, max + 0.5];
  }
  const step = niceStep((max - min) / (count - 1));
  return [Math.floor(min / step) * step, Math.ceil(max / step) * step];
}

/** An SVG path through the points, skipping any that are not finite. */
export function linePath(points: readonly (readonly [number, number])[]): string {
  let path = "";
  let open = false;
  for (const [x, y] of points) {
    if (!Number.isFinite(x) || !Number.isFinite(y)) {
      open = false;
      continue;
    }
    path += `${open ? "L" : "M"}${x.toFixed(2)} ${y.toFixed(2)}`;
    open = true;
  }
  return path;
}

/** The same path closed back to a baseline, for a filled area. */
export function areaPath(points: readonly (readonly [number, number])[], baseline: number): string {
  const usable = points.filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y));
  const first = usable[0];
  const last = usable[usable.length - 1];
  if (first === undefined || last === undefined) {
    return "";
  }
  return `${linePath(usable)}L${last[0].toFixed(2)} ${baseline.toFixed(2)}L${first[0].toFixed(2)} ${baseline.toFixed(2)}Z`;
}

/**
 * A base-10 log scale. Both ends of the domain must be strictly positive.
 *
 * Two of this site's arguments live on ratios rather than differences — a stack of 1 to
 * 100 sleeves, and a wait of a month to a millennium — and a linear axis spends almost
 * its whole width on the top decade of each. A zero or negative bound is refused rather
 * than clamped, because silently moving the axis floor changes what the picture claims.
 */
export function logScale(domain: readonly [number, number], range: readonly [number, number]): Scale {
  const [d0, d1] = domain;
  if (!(d0 > 0) || !(d1 > 0)) {
    throw new RangeError(`a log scale needs a strictly positive domain, got [${d0}, ${d1}]`);
  }
  const inner = linearScale([Math.log10(d0), Math.log10(d1)], range);
  const scale = ((value: number) => inner(Math.log10(value))) as {
    (value: number): number;
    domain?: readonly [number, number];
    range?: readonly [number, number];
  };
  scale.domain = domain;
  scale.range = range;
  return scale as Scale;
}

/** Every power of ten inside `[min, max]`, inclusive of a bound that is one exactly. */
export function decadeTicks(min: number, max: number): number[] {
  if (!(min > 0) || !(max > 0) || min > max) {
    return [];
  }
  const ticks: number[] = [];
  for (let exponent = Math.ceil(Math.log10(min) - 1e-9); exponent <= Math.log10(max) + 1e-9; exponent += 1) {
    ticks.push(10 ** exponent);
  }
  return ticks;
}
