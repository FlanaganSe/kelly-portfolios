/**
 * The pairs of edge and drift the tool opens on, and every one of them is a claim this
 * site makes somewhere else.
 *
 * Three come straight out of `~/content/confidence`. The fourth — the whole portfolio
 * against a same-split cheap core — has its canonical home in the figure collection,
 * `src/content/figures/thirty-year-edge.yaml` and `src/content/figures/tracking-error.yaml`,
 * which an island cannot read because that collection is resolved at build time. So the
 * two numbers are written once here and `horizon-presets.test.ts` reads those two files
 * and fails if either ever moves.
 */

import { contractualRows } from "~/content/confidence";

export interface HorizonPreset {
  readonly id: string;
  readonly label: string;
  /** What the edge is measured against. Never dropped: three benchmarks, never added. */
  readonly against: string;
  readonly edgeBp: number;
  readonly trackingErrorBp: number;
}

function contractual(id: string): { readonly edgeBp: number; readonly trackingErrorBp: number } {
  const row = contractualRows.find((entry) => entry.id === id);
  if (row === undefined) {
    throw new Error(`no confidence row "${id}"; ids are ${contractualRows.map((entry) => entry.id).join(", ")}`);
  }
  return { edgeBp: row.edgeBp, trackingErrorBp: row.trackingErrorBp };
}

/** Canonical record: `src/content/figures/thirty-year-edge.yaml`. */
export const PORTFOLIO_EDGE_BP = 92;
/** Canonical record: `src/content/figures/tracking-error.yaml`. */
export const PORTFOLIO_TRACKING_ERROR_BP = 400;

export const horizonPresets: readonly HorizonPreset[] = [
  {
    id: "structural",
    label: "Fees, taxes and which account each fund sits in",
    against: "against the portfolio you already own",
    ...contractual("contractual-109"),
  },
  {
    id: "structural-2025",
    label: "The same package, before the 2026 revision",
    against: "against the portfolio you already own",
    ...contractual("contractual-89"),
  },
  {
    id: "whole-portfolio",
    label: "The whole recommended portfolio",
    against: "against a cheap index fund at the same stock and bond split",
    edgeBp: PORTFOLIO_EDGE_BP,
    trackingErrorBp: PORTFOLIO_TRACKING_ERROR_BP,
  },
  {
    id: "vs-cheap-index",
    label: "The edge budget's own reading of that same question",
    against: "against a cheap total-market index fund",
    ...contractual("vs-cheap-index"),
  },
];

export const defaultPreset: HorizonPreset = horizonPresets[0] as HorizonPreset;
