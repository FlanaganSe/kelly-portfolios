/**
 * Number handling for the interactive controls.
 *
 * Figures that come out of `src/content/` are already strings, deliberately, and
 * must not pass through a formatter — rounding one is a misquote. These helpers
 * are for numbers the reader types or drags, which have no source to misquote.
 */

/** Constrain to a range. Returns `min` when the bounds are crossed. */
export function clamp(value: number, min: number, max: number): number {
  if (Number.isNaN(value)) return min;
  if (max < min) return min;
  return Math.min(Math.max(value, min), max);
}

/** Round to a fixed number of decimals, without float dust like 0.30000000000000004. */
export function roundTo(value: number, decimals: number): number {
  if (!Number.isFinite(value)) return value;
  const factor = 10 ** Math.max(0, Math.trunc(decimals));
  return Math.round(value * factor) / factor;
}

/** Snap to the nearest step from an origin, the way a range input does. */
export function snapToStep(value: number, step: number, origin = 0): number {
  if (!Number.isFinite(step) || step <= 0) return value;
  return roundTo(origin + Math.round((value - origin) / step) * step, decimalsOf(step));
}

/** How many decimals a step implies, so 0.25 renders as 0.25 and not 0.3. */
export function decimalsOf(step: number): number {
  if (!Number.isFinite(step)) return 0;
  const text = String(step);
  const dot = text.indexOf(".");
  if (dot === -1) return 0;
  return text.length - dot - 1;
}

/**
 * Parse user input. Tolerates thousands separators, a leading plus and a
 * trailing percent sign; returns `null` for anything else, including "".
 */
export function parseNumber(raw: string): number | null {
  const cleaned = raw.trim().replace(/,/g, "").replace(/%$/, "").replace(/^\+/, "");
  if (cleaned === "" || cleaned === "-" || cleaned === ".") return null;
  const parsed = Number(cleaned);
  return Number.isFinite(parsed) ? parsed : null;
}

/** Fixed-decimal display for a number the reader controls. */
export function formatNumber(value: number, decimals = 0): string {
  if (!Number.isFinite(value)) return "—";
  return value.toFixed(Math.max(0, Math.trunc(decimals)));
}
