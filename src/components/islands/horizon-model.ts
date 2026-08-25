/**
 * The wording and the guard rails around `horizonForConfidence`, and nothing else.
 *
 * The arithmetic is already ported and fixture-tested in `~/lib/horizon`; this module
 * only decides what to say when the formula has no answer, and converts between the
 * percent a reader types and the basis points the library takes.
 *
 * `T = (z·s/e)²` has three cases a control can reach and a reader deserves a sentence
 * for. An edge of zero or less never becomes an advantage at any horizon, so there is no
 * year to name. A tracking error of zero is the contractual case rather than a
 * degenerate one: a lower fee on the same index fund cannot drift, so it lands the day
 * it starts. Everything in between is the square law, and the square law is the finding.
 */

import { horizonForConfidence, probabilityOfOutperformance } from "~/lib/horizon";

/** A basis point as a fraction, matching `~/lib/horizon`. */
const BASIS_POINTS_PER_PERCENT = 100;

/** Where a wait stops being a wait. The same threshold the time-to-know chart shades. */
export const WORKING_LIFE_YEARS = 40;

/** 0.89 becomes 89. Rounded to three decimals, because 0.89 * 100 is not 89 in binary. */
export function bpFromPercent(percent: number): number {
  return Math.round(percent * BASIS_POINTS_PER_PERCENT * 1000) / 1000;
}

/** 89 becomes 0.89. */
export function percentFromBp(bp: number): number {
  return Math.round((bp / BASIS_POINTS_PER_PERCENT) * 10000) / 10000;
}

export type HorizonOutcome =
  /** `T` exists and is finite. */
  | { readonly kind: "years"; readonly years: number }
  /** No drift, so a positive edge lands at once. */
  | { readonly kind: "immediate" }
  /** The edge is zero or negative, so no horizon reaches the confidence asked for. */
  | { readonly kind: "never" };

/**
 * Years until the chance of being ahead reaches `confidence`.
 *
 * Wraps the library rather than reimplementing it, and turns the two arguments the
 * library refuses into named outcomes instead of a thrown error, because both of them
 * are values a reader can legitimately put in a field.
 */
export function timeToKnow({
  edgeBp,
  trackingErrorBp,
  confidence,
}: {
  readonly edgeBp: number;
  readonly trackingErrorBp: number;
  readonly confidence: number;
}): HorizonOutcome {
  if (!(edgeBp > 0)) return { kind: "never" };
  if (trackingErrorBp === 0) return { kind: "immediate" };
  return { kind: "years", years: horizonForConfidence({ edgeBp, trackingErrorBp, confidence }) };
}

/** The chance of being ahead after a stated number of years, as a fraction of one. */
export function chanceAhead({
  edgeBp,
  trackingErrorBp,
  horizonYears,
}: {
  readonly edgeBp: number;
  readonly trackingErrorBp: number;
  readonly horizonYears: number;
}): number {
  return probabilityOfOutperformance({ edgeBp, trackingErrorBp, horizonYears });
}

/**
 * "72%" — a whole percentage point, which is as fine as any of this resolves.
 *
 * Nothing here ever prints 100%. The normal distribution saturates in floating point
 * somewhere past six standard deviations, and rounding that to certainty would be the
 * arithmetic's limit being reported as a promise.
 */
export function formatChance(probability: number): string {
  const percent = probability * 100;
  if (percent > 99.5) return "over 99%";
  if (percent < 0.5 && percent > 0) return "under 1%";
  return `${Math.round(percent)}%`;
}

/**
 * How the wait compares with a working life, which is the comparison that matters.
 *
 * A number of years means nothing on its own. Four months and thirty-one years are the
 * same arithmetic and different advice, and the difference is whether you would still be
 * alive to collect the answer.
 */
export function againstAWorkingLife(outcome: HorizonOutcome): string {
  if (outcome.kind === "never") {
    return "No horizon reaches it, because the edge is not positive.";
  }
  if (outcome.kind === "immediate") {
    return "There is no drift, so the saving lands the day you make the switch.";
  }
  const { years } = outcome;
  if (years < 1) return `Inside a year, and well inside the ${WORKING_LIFE_YEARS} years of a working life.`;
  if (years < 5) return `A few years, against the ${WORKING_LIFE_YEARS} years of a working life.`;
  if (years < WORKING_LIFE_YEARS) {
    return `Most of a working life. ${WORKING_LIFE_YEARS} years is the whole of one.`;
  }
  const lives = years / WORKING_LIFE_YEARS;
  if (lives < 2) return `Longer than the ${WORKING_LIFE_YEARS} years of a working life.`;
  const rounded = lives < 10 ? Math.round(lives * 10) / 10 : Math.round(lives);
  return `About ${rounded} working lives, at ${WORKING_LIFE_YEARS} years each.`;
}
