/**
 * The four rungs.
 *
 * The site says how sure it is with one of four words and never with prose hedging.
 *
 * The word is the whole reading. It used to be a word beside a hand-drawn monochrome
 * mark — solid, solid with a whisker, a hatched half, an empty outline — and a mark a
 * reader has to learn from another page is not a reading. What survives is the word,
 * and a left rule whose ink weight steps down with the evidence, which `.confidence` in
 * `styles.css` draws from `data-level`. The rule is drawn in ink alone: hue would
 * smuggle in a good/bad judgement the evidence does not make.
 */

export const RUNG_LEVELS = ["settled", "probably", "might", "cant-tell"] as const;

export type RungLevel = (typeof RUNG_LEVELS)[number];

export interface RungMeta {
  readonly label: string;
  /** One line, in the reader's words, about what the rung licenses. */
  readonly gloss: string;
}

export const rungMeta = {
  settled: {
    label: "Settled",
    gloss: "Arithmetic, a contract or a statute. The sign is known before you start.",
  },
  probably: {
    label: "Probably",
    gloss: "Measured, and it held up when we tried to break it. The size is a range, not a point.",
  },
  might: {
    label: "Might work",
    gloss: "The mechanism is real and the measurement is thin. Size it as if you could be wrong.",
  },
  "cant-tell": {
    label: "We can’t tell",
    gloss: "The test could not have seen an effect this small. Neither a yes nor a no.",
  },
} as const satisfies Readonly<Record<RungLevel, RungMeta>>;

export function isRungLevel(value: unknown): value is RungLevel {
  return typeof value === "string" && (RUNG_LEVELS as readonly string[]).includes(value);
}
