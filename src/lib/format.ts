/**
 * Number handling for the interactive controls and the computed series.
 *
 * Figures that come out of `src/content/figures/` are already strings, deliberately, and
 * must not pass through a formatter — rounding one is a misquote. These helpers are for
 * numbers the reader types or drags, which have no source to misquote, and for the series
 * under `src/content/series/`, which the research emitter writes as numbers it has already
 * rounded, so `formatDollars` and `formatSignedPercent` add separators and a sign and
 * nothing else.
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

const DAYS_PER_YEAR = 365.25;
const MONTHS_PER_YEAR = 12;

/**
 * A holding period in the largest unit that keeps it legible, with its real digits.
 *
 * "Nearly two decades" is banned on this site and so is "0.29 years". A wait that runs
 * from three weeks to five thousand years has to change unit somewhere, and the
 * thresholds here are where a reader stops being able to picture the number: under two
 * months it is days, under two years it is months, under a century it is years to one
 * decimal, under a millennium it is whole years, and above that the trailing digits are
 * fake so it rounds to the nearest hundred.
 */
export function formatYears(years: number): string {
  if (!Number.isFinite(years) || years < 0) {
    throw new RangeError(`formatYears expects a non-negative number of years, got ${years}`);
  }
  if (years < 2 / MONTHS_PER_YEAR) {
    const days = Math.round(years * DAYS_PER_YEAR);
    return `${days} ${days === 1 ? "day" : "days"}`;
  }
  if (years < 2) {
    const months = roundTo(years * MONTHS_PER_YEAR, 1);
    return `${formatNumber(months, Number.isInteger(months) ? 0 : 1)} months`;
  }
  if (years < 100) {
    const rounded = roundTo(years, 1);
    return `${formatNumber(rounded, Number.isInteger(rounded) ? 0 : 1)} years`;
  }
  if (years < 1000) {
    return `${Math.round(years)} years`;
  }
  // Grouped, because five thousand five hundred without a separator is unreadable at a
  // glance. `formatNumber` deliberately does not group — it formats fields a reader is
  // typing into — so the separator is added here rather than by changing its contract.
  return `${grouped(Math.round(years / 100) * 100)} years`;
}

/** Thousands separators, en-US, without pulling in `Intl` for one call site. */
function grouped(value: number): string {
  return String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

const MINUS = "\u2212";

/** Whole dollars with separators: `350671` is `$350,671`; a negative carries a typographic minus. */
export function formatDollars(value: number): string {
  if (!Number.isFinite(value)) return "—";
  const rounded = Math.round(Math.abs(value));
  const sign = value < 0 && rounded !== 0 ? MINUS : "";
  return `${sign}$${grouped(rounded)}`;
}

/** A percent with its sign: `19.4` is `+19.4%`, `-17.8` is `−17.8%`, `0` is `0.0%`. */
export function formatSignedPercent(value: number, decimals = 1): string {
  if (!Number.isFinite(value)) return "—";
  const rounded = roundTo(value, decimals);
  const digits = Math.abs(rounded).toFixed(Math.max(0, Math.trunc(decimals)));
  if (rounded > 0) return `+${digits}%`;
  if (rounded < 0) return `${MINUS}${digits}%`;
  return `${digits}%`;
}
