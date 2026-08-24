/**
 * The placement tool's whole state, encoded into the query string.
 *
 * `~/lib/lab/config` does this job for the pair of numbers the horizon tool takes, and
 * the horizon tool uses it. It has no field for a tax bracket or an account split, so
 * rather than bend `LabConfig` into carrying something it does not describe, this is the
 * same two rules applied to the fields this tool actually has:
 *
 * 1. Round-tripping is lossless for anything the parser accepts.
 * 2. A malformed field falls back to its default and the rest of the link still loads.
 *
 * Rates and shares are percentages here, because that is what a reader types.
 */

import type { Basis } from "~/components/islands/placement-model";

/** `own` means the reader typed their own rates rather than picking a named bracket. */
export const OWN_RATES = "own";

export interface PlacementConfig {
  /** A `TaxRegimeId` from `~/content/placement`, or {@link OWN_RATES}. */
  readonly bracketId: string;
  /** All-in marginal rate on ordinary income, percent. Read only when bracketId is own. */
  readonly ownOrdinaryPercent: number;
  /** All-in marginal rate on qualified dividends, percent. Read only when bracketId is own. */
  readonly ownQualifiedPercent: number;
  /** Share of the portfolio in a Roth, percent. */
  readonly rothPercent: number;
  /** Share of the portfolio in a traditional 401(k) or IRA, percent. */
  readonly deferredPercent: number;
  readonly basis: Basis;
}

/** Equal nominal thirds, which is the shape the research states its figures for. */
export const defaultPlacementConfig: PlacementConfig = {
  bracketId: "us-top",
  ownOrdinaryPercent: 40.8,
  ownQualifiedPercent: 23.8,
  rothPercent: 33,
  deferredPercent: 33,
  basis: "paid-out",
};

const BRACKET = /^[a-z][a-z0-9-]{0,23}$/;

function percentOr(raw: string | null, fallback: number, max: number): number {
  if (raw === null || raw.trim() === "") return fallback;
  const parsed = Number(raw);
  if (!Number.isFinite(parsed) || parsed < 0 || parsed > max) return fallback;
  return Math.round(parsed * 100) / 100;
}

export function parsePlacementConfig(search: string | URLSearchParams): PlacementConfig {
  const params = typeof search === "string" ? new URLSearchParams(search) : search;
  const bracket = params.get("q");
  const roth = percentOr(params.get("r"), defaultPlacementConfig.rothPercent, 100);
  return {
    bracketId: bracket !== null && BRACKET.test(bracket) ? bracket : defaultPlacementConfig.bracketId,
    ownOrdinaryPercent: percentOr(params.get("o"), defaultPlacementConfig.ownOrdinaryPercent, 99.9),
    ownQualifiedPercent: percentOr(params.get("g"), defaultPlacementConfig.ownQualifiedPercent, 99.9),
    rothPercent: roth,
    // The two shelters cannot together exceed the portfolio, so the second is capped by
    // what the first left rather than dropped. A link that over-fills is still readable.
    deferredPercent: Math.min(percentOr(params.get("d"), defaultPlacementConfig.deferredPercent, 100), 100 - roth),
    basis: params.get("x") === "recorded" ? "recorded" : "paid-out",
  };
}

/** Only what differs from the defaults is written, so a plain link stays short. */
export function toPlacementSearchParams(config: PlacementConfig): URLSearchParams {
  const params = new URLSearchParams();
  if (config.bracketId !== defaultPlacementConfig.bracketId) params.set("q", config.bracketId);
  if (config.bracketId === OWN_RATES) {
    params.set("o", String(config.ownOrdinaryPercent));
    params.set("g", String(config.ownQualifiedPercent));
  }
  if (config.rothPercent !== defaultPlacementConfig.rothPercent) params.set("r", String(config.rothPercent));
  if (config.deferredPercent !== defaultPlacementConfig.deferredPercent) {
    params.set("d", String(config.deferredPercent));
  }
  if (config.basis !== defaultPlacementConfig.basis) params.set("x", config.basis);
  return params;
}
