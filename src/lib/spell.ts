/**
 * A count, spelled the way the rest of the site writes.
 *
 * Counts on this site are derived from the records they describe rather than typed, so
 * they cannot go stale — but a derived count renders as a digit, and "10 families" beside
 * a page of prose reads like a spreadsheet. This spells the small ones and leaves the
 * rest alone.
 */

const WORDS = [
  "zero",
  "one",
  "two",
  "three",
  "four",
  "five",
  "six",
  "seven",
  "eight",
  "nine",
  "ten",
  "eleven",
  "twelve",
  "thirteen",
  "fourteen",
  "fifteen",
  "sixteen",
  "seventeen",
  "eighteen",
  "nineteen",
  "twenty",
] as const;

export function spell(count: number): string {
  if (!Number.isInteger(count) || count < 0 || count >= WORDS.length) {
    return String(count);
  }
  return WORDS[count] ?? String(count);
}

/** The same, capitalised, for the start of a sentence or a heading. */
export function Spell(count: number): string {
  const word = spell(count);
  return `${word.charAt(0).toUpperCase()}${word.slice(1)}`;
}
