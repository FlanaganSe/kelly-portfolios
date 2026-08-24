/**
 * The four rungs.
 *
 * The site says how sure it is with one of four words and never with prose hedging.
 * The rung is about how much the evidence can carry, not about whether the news is
 * good, so the mark is drawn in ink alone. Nothing here is ever red or green.
 */

export const RUNG_LEVELS = ["settled", "probably", "might", "cant-tell"] as const;

export type RungLevel = (typeof RUNG_LEVELS)[number];

export interface RungMeta {
  readonly label: string;
  /** One line, in the reader's words, about what the rung licenses. */
  readonly gloss: string;
  /** How the mark is drawn. Intensity, never hue. */
  readonly mark: "solid" | "solid-range" | "hatched-half" | "outline";
}

export const rungMeta = {
  settled: {
    label: "Settled",
    gloss: "Arithmetic, a contract or a statute. The sign is known before you start.",
    mark: "solid",
  },
  probably: {
    label: "Probably",
    gloss: "Measured, and it held up when we tried to break it. The size is a range, not a point.",
    mark: "solid-range",
  },
  might: {
    label: "Might",
    gloss: "The mechanism is real and the measurement is thin. Size it as if you could be wrong.",
    mark: "hatched-half",
  },
  "cant-tell": {
    label: "Can't tell",
    gloss: "The test could not have seen an effect this small. Neither a yes nor a no.",
    mark: "outline",
  },
} as const satisfies Readonly<Record<RungLevel, RungMeta>>;

export function isRungLevel(value: unknown): value is RungLevel {
  return typeof value === "string" && (RUNG_LEVELS as readonly string[]).includes(value);
}

/**
 * Diagonal hatch segments for the `might` mark, clipped to the box by arithmetic
 * rather than by a `<clipPath>`. An SVG `id` would have to be unique per instance,
 * and a page can carry several rungs; plain line coordinates cannot collide.
 */
export function hatchSegments(
  width: number,
  height: number,
  gap = 3.5
): ReadonlyArray<readonly [number, number, number, number]> {
  const segments: Array<readonly [number, number, number, number]> = [];
  // Lines run at 45 degrees: y = -x + c, for c stepping across the whole box.
  for (let c = gap; c < width + height; c += gap) {
    const x1 = Math.max(0, c - height);
    const y1 = c - x1;
    const y2 = Math.max(0, c - width);
    const x2 = c - y2;
    if (x2 - x1 < 0.2) continue;
    segments.push([x1, y1, x2, y2]);
  }
  return segments;
}
