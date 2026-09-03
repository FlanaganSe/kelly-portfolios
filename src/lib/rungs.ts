/**
 * How sure the site is, in one of four words.
 *
 * The site says how sure it is with a word and never with prose hedging. The word is the
 * whole reading: no glyph, no mark a reader has to learn from another page. `Verdict`
 * draws it as a small badge with one restrained hue per word, and `.confidence` in
 * `styles.css` still draws the older left-rule form for pages that use it.
 *
 * Two vocabularies meet here. The research records carry their own statuses
 * (`EvidenceStatus` in `src/content/types.ts`), which describe how a number was
 * produced. A reader needs the other thing: whether to believe it. {@link toConfidence}
 * maps one onto the other and is the only place that mapping lives.
 */

import type { EvidenceStatus } from "~/content/types";

export const RUNG_LEVELS = ["settled", "probably", "might", "cant-tell"] as const;

export type RungLevel = (typeof RUNG_LEVELS)[number];

export interface RungMeta {
  readonly label: string;
  /** One line, in the reader's words, about what the level licenses. */
  readonly gloss: string;
}

export const rungMeta = {
  settled: {
    label: "Settled",
    gloss: "Arithmetic, a contract or a statute. The sign is known before you start.",
  },
  probably: {
    label: "Probably",
    gloss: "Measured, and it held up when I tried to break it. The size is a range, not a point.",
  },
  might: {
    label: "Too close to call",
    gloss: "The idea is real and the measurement is thin. Size it as if you could be wrong.",
  },
  "cant-tell": {
    label: "Too close to call",
    gloss: "The test could not have seen an effect this small. Neither a yes nor a no.",
  },
} as const satisfies Readonly<Record<RungLevel, RungMeta>>;

export function isRungLevel(value: unknown): value is RungLevel {
  return typeof value === "string" && (RUNG_LEVELS as readonly string[]).includes(value);
}

/**
 * The four words a reader sees. `Settled` is arithmetic or a contract; `Probably` was
 * measured and survived an attempt to break it; `Too close to call` means the test could
 * not separate the effect from zero; `No` means a test written down in advance failed.
 */
export const CONFIDENCE_WORDS = ["Settled", "Probably", "Too close to call", "No"] as const;

export type Confidence = (typeof CONFIDENCE_WORDS)[number];

/** A one-line reading of each word, for a tooltip or a legend. */
export const confidenceGloss = {
  Settled: "Arithmetic, a contract or a statute. Known before you start.",
  Probably: "Measured, and it held up under pressure. The size is a range.",
  "Too close to call": "The test could not tell this effect from zero.",
  No: "A test written down in advance, and it failed.",
} as const satisfies Readonly<Record<Confidence, string>>;

/** A short slug for `data-confidence`, which the badge styles key off. */
export function confidenceSlug(word: Confidence): "settled" | "probably" | "close" | "no" {
  switch (word) {
    case "Settled":
      return "settled";
    case "Probably":
      return "probably";
    case "Too close to call":
      return "close";
    case "No":
      return "no";
  }
}

/**
 * The words the research uses for how a number was produced, plus the four reader levels
 * that older pages pass straight through.
 */
export type ConfidenceInput = EvidenceStatus | RungLevel | "settled" | "probably" | "might" | "can't tell";

/** Maps a research status, or an older level word, onto the word a reader sees. */
export function toConfidence(status: ConfidenceInput): Confidence {
  switch (status) {
    case "settled":
    case "source-reproduced":
    case "independently-reproduced":
    case "walk-forward-tested":
    case "shadow-live":
    case "production-eligible":
      return "Settled";
    case "probably":
      return "Probably";
    case "rejected":
      return "No";
    case "might":
    case "cant-tell":
    case "can't tell":
    case "unresolved":
    case "exploratory":
      return "Too close to call";
  }
}

export function isConfidence(value: unknown): value is Confidence {
  return typeof value === "string" && (CONFIDENCE_WORDS as readonly string[]).includes(value);
}
