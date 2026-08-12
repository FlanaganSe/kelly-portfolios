/**
 * The vocabulary every other module in `src/content/` is written in.
 *
 * Two rules govern this whole directory:
 *
 * 1. No number appears here that `docs/research/` does not already state. Where a
 *    figure was never read, the field is `null` and carries a note saying so.
 * 2. No status is upgraded on the way in. `unresolved` is not a promotion,
 *    `exploratory` permits use as an implementation proxy in a later experiment and
 *    permits nothing else, and nothing in this repository reached
 *    `production-eligible`.
 *
 * UI code imports from here. UI code does not hardcode a number.
 */

/** The repository's closed status vocabulary. It is never collapsed into "works". */
export type EvidenceStatus =
  | "exploratory"
  | "source-reproduced"
  | "independently-reproduced"
  | "walk-forward-tested"
  | "shadow-live"
  | "production-eligible"
  | "rejected"
  | "unresolved";

/** How a status or class should read, not how good it is. */
export type Tone = "positive" | "caution" | "negative" | "neutral";

export interface StatusMeta {
  readonly label: string;
  readonly gloss: string;
  readonly tone: Tone;
}

export const statusMeta = {
  exploratory: {
    label: "Exploratory",
    gloss: "The lowest rung. It may stand in for a real product in a later experiment, and nothing else.",
    tone: "caution",
  },
  "source-reproduced": {
    label: "Source-reproduced",
    gloss: "Our arithmetic matches the table the original source printed.",
    tone: "neutral",
  },
  "independently-reproduced": {
    label: "Independently reproduced",
    gloss: "Rebuilt by different code from different data, and it still held.",
    tone: "positive",
  },
  "walk-forward-tested": {
    label: "Walk-forward tested",
    gloss: "It survived data the specification had never seen, under a purged rolling test.",
    tone: "positive",
  },
  "shadow-live": {
    label: "Shadow-live",
    gloss: "Running forward on live data with no money behind it.",
    tone: "positive",
  },
  "production-eligible": {
    label: "Production-eligible",
    gloss: "Cleared every stage and may hold real money. Nothing in this repository has reached it.",
    tone: "positive",
  },
  rejected: {
    label: "Rejected",
    gloss: "A test written down before the result fired. That is not the same as the effect being zero.",
    tone: "negative",
  },
  unresolved: {
    label: "Unresolved",
    gloss:
      "The window could not have seen an effect of the size it was looking for. Neither a promotion nor a refutation.",
    tone: "neutral",
  },
} as const satisfies Readonly<Record<EvidenceStatus, StatusMeta>>;

/**
 * What kind of thing a line of return is, which decides how it may be described.
 * A risk premium may never be called an edge.
 */
export type CertaintyClass = "contractual" | "risk-premium" | "nothing-better-exists" | "different-benchmark";

export interface CertaintyMeta {
  readonly label: string;
  readonly gloss: string;
  readonly tone: Tone;
}

export const certaintyMeta = {
  contractual: {
    label: "Contractual",
    gloss: "An accounting identity or a statutory fact whose sign is known in advance.",
    tone: "positive",
  },
  "risk-premium": {
    label: "Risk premium",
    gloss: "A bet whose sign is not known at any horizon a human has.",
    tone: "caution",
  },
  "nothing-better-exists": {
    label: "Nothing better exists",
    gloss: "It is here because the alternatives were tested and lost, not because it was shown to be good.",
    tone: "neutral",
  },
  "different-benchmark": {
    label: "A different benchmark",
    gloss:
      "Real pay for a real risk, measured against a different yardstick. Booking it as an edge over an equity index swaps the benchmark rather than adding return.",
    tone: "neutral",
  },
} as const satisfies Readonly<Record<CertaintyClass, CertaintyMeta>>;

/** A link back to the page that owns the fact. `docPath` is repo-relative. */
export interface Citation {
  readonly label: string;
  readonly docPath: string;
  readonly anchor?: string;
  /** An external primary source, where the owning page gives one. */
  readonly href?: string;
}

declare const isoDate: unique symbol;

/**
 * An ISO date, `YYYY-MM-DD`. Branded so a date cannot be dropped by accident:
 * a fee without its `as of` is a misquote.
 */
export type AsOf = string & { readonly [isoDate]: "AsOf" };

/** Tag an ISO date string as an `AsOf`. */
export function asOf(iso: string): AsOf {
  return iso as AsOf;
}

/** Anything that carries its provenance. */
export type Sourced<T> = T & {
  readonly source: Citation;
  readonly asOf?: AsOf;
  readonly note?: string;
};

/**
 * A figure, held as the string its source page prints. Strings rather than numbers,
 * because the sign, the precision and the interval are all part of the fact, and a
 * formatter that rounds one of them has misquoted it.
 */
export interface KeyNumber {
  readonly label: string;
  readonly value: string;
  readonly unit?: string;
  /** The confidence interval as printed, e.g. `[+1.46, +8.10]`. */
  readonly interval?: string;
  readonly note?: string;
}
