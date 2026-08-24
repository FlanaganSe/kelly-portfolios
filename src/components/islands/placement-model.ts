/**
 * The shelf, ranked for one reader, and where each line lands once the shelter runs out.
 *
 * All of the arithmetic is `~/lib/placement`, run over `~/content/placement`. Nothing
 * here computes a tax; it maps a filed fund into the shape the library takes, fills a
 * shelter of the reader's size from the top of the ranking, and reads back what that
 * costs in foreign tax credit.
 *
 * The mapping is worth stating, because a fund files three numbers where the library
 * takes three different ones:
 *
 *     dividend yield        = the whole annual taxable distribution
 *     qualified fraction    = the share of it taxed at the long-term rate
 *     withholding rate      = creditable foreign tax / the whole distribution
 *
 * Run at the top bracket it reproduces every figure in `investorHoldings[].priorityBp`
 * to the cent, which is what `placement-model.test.ts` checks.
 */

import { type InvestorHolding, investorHoldings } from "~/content/placement";
import {
  type ShelterCandidate,
  shelteredCostBp,
  shelterPriorityBp,
  type TaxRegime,
  taxableCostBp,
} from "~/lib/placement";

/** One basis point, matching `~/lib/placement`. */
const BASIS_POINT = 1e-4;

/**
 * Which reading of a fund that files two.
 *
 * The stacked fund recognises income inside itself that it has not paid out. Counting it
 * puts that fund at the top of the queue; counting only what shareholders were taxed on
 * puts it seventh. The repository's own position is that the placement is the same under
 * either reading, so the tool shows the audited one and offers the other.
 */
export type Basis = "paid-out" | "recorded";

export interface ShelfRow {
  readonly ticker: string;
  readonly name: string;
  /** Fraction of the whole portfolio. */
  readonly weight: number;
  /** What a dollar of shelter capacity saves a year, in basis points. */
  readonly priorityBp: number;
  /** Recurring tax a year if this line sits in the taxable account, in basis points. */
  readonly taxableBp: number;
  /** Foreign tax forfeited a year if this line sits in a shelter, in basis points. */
  readonly shelteredBp: number;
  /** True where a foreign government withholds tax on the dividend before it arrives. */
  readonly international: boolean;
  readonly holding: InvestorHolding;
}

export interface PlacedRow extends ShelfRow {
  /** Fraction of the whole portfolio this line puts inside the shelter. */
  readonly shelteredWeight: number;
  readonly where: "shelter" | "split" | "taxable";
}

/** A fund's filed distribution, in the shape `~/lib/placement` takes. */
export function toCandidate(holding: InvestorHolding): ShelterCandidate {
  const gross = holding.boxOneAYield;
  return {
    label: holding.ticker,
    dividendYield: gross,
    qualifiedFraction: holding.capitalGainRateFraction,
    foreignWithholdingRate: gross > 0 ? holding.creditableForeignTaxYield / gross : 0,
  };
}

/**
 * One row per ticker.
 *
 * Where a ticker files two readings the audited one is the smaller distribution, so the
 * choice is made on the data rather than on a name written into this file.
 */
export function shelf(
  basis: Basis,
  holdings: readonly InvestorHolding[] = investorHoldings
): readonly InvestorHolding[] {
  const byTicker = new Map<string, InvestorHolding>();
  for (const holding of holdings) {
    const held = byTicker.get(holding.ticker);
    if (held === undefined) {
      byTicker.set(holding.ticker, holding);
      continue;
    }
    const takeNew =
      basis === "recorded" ? holding.boxOneAYield > held.boxOneAYield : holding.boxOneAYield < held.boxOneAYield;
    if (takeNew) byTicker.set(holding.ticker, holding);
  }
  return [...byTicker.values()];
}

/**
 * One fund's place in the queue: what a sheltered dollar of it saves a year, in basis
 * points, at the stated rates.
 *
 * The whole of the asset-location finding is in the subtraction. For a US fund the
 * second term is zero and this collapses to the familiar rule; for a fund that pays
 * foreign tax it does not, and the correction is exactly the credit a shelter forfeits.
 */
export function rank(holding: InvestorHolding, regime: TaxRegime): ShelfRow {
  const candidate = toCandidate(holding);
  const taxableBp = taxableCostBp(candidate, regime);
  const shelteredBp = shelteredCostBp(candidate);
  return {
    ticker: holding.ticker,
    name: holding.name,
    weight: holding.weight,
    priorityBp: taxableBp - shelteredBp,
    taxableBp,
    shelteredBp,
    international: holding.creditableForeignTaxYield > 0,
    holding,
  };
}

/**
 * The shelf ranked by what a sheltered dollar of it saves, best first.
 *
 * The order comes from `shelterPriorityBp`, so the ordering and its tie-break stay the
 * library's rather than this file's. That needs one row per ticker, which is what
 * {@link shelf} produces.
 */
export function queue(holdings: readonly InvestorHolding[], regime: TaxRegime): readonly ShelfRow[] {
  const byTicker = new Map(holdings.map((holding) => [holding.ticker, rank(holding, regime)]));
  if (byTicker.size !== holdings.length) {
    throw new RangeError("a queue takes one row per ticker; pass the result of shelf()");
  }
  const rows: ShelfRow[] = [];
  for (const entry of shelterPriorityBp(holdings.map(toCandidate), { regime })) {
    const row = byTicker.get(entry.label);
    if (row !== undefined) rows.push(row);
  }
  return rows;
}

/**
 * Fill a shelter of size `capacity` from the top of the queue.
 *
 * `capacity` and every weight are fractions of the same base, so a line that only partly
 * fits is split rather than dropped: splitting a fund across two accounts costs nothing,
 * and refusing to split it would overstate what the ordering can achieve.
 */
export function fill(rows: readonly ShelfRow[], capacity: number): readonly PlacedRow[] {
  if (!(capacity >= 0)) {
    throw new RangeError(`capacity must be non-negative, got ${capacity}`);
  }
  // Weights are decimals that do not sum to exactly one in binary, so a shelter the
  // size of the whole portfolio would otherwise leave the last line a hair short and
  // report it as split. The tolerance is a hundredth of a basis point of weight.
  const DUST = 1e-9;
  let remaining = capacity;
  return rows.map((row) => {
    const placed = Math.min(row.weight, Math.max(remaining, 0));
    remaining -= placed;
    const where = placed <= DUST ? "taxable" : placed >= row.weight - DUST ? "shelter" : "split";
    return { ...row, shelteredWeight: placed, where };
  });
}

/**
 * Foreign tax credit destroyed by this plan, in basis points a year of the whole
 * portfolio.
 *
 * A credit offsets a US tax and a sheltered account owes none, so every sheltered dollar
 * of a fund that pays foreign tax loses that tax outright, in a traditional account and
 * a Roth alike. The ranking has already subtracted it; this is the same quantity printed
 * on its own so a reader can see what the plan is spending.
 */
export function forfeitedCreditBp(placed: readonly PlacedRow[]): number {
  let total = 0;
  for (const row of placed) {
    total += row.shelteredWeight * row.holding.creditableForeignTaxYield;
  }
  return total / BASIS_POINT;
}

export interface Verdict {
  /** True when the worst international line still beats the best domestic one. */
  readonly everyInternationalAhead: boolean;
  readonly lowestInternational: ShelfRow | null;
  readonly highestDomestic: ShelfRow | null;
  readonly last: ShelfRow | null;
}

/** What the ranking actually says, read off the ranking rather than asserted. */
export function verdict(rows: readonly ShelfRow[]): Verdict {
  const international = rows.filter((row) => row.international);
  const domestic = rows.filter((row) => row.international === false);
  const lowestInternational = international.length > 0 ? (international[international.length - 1] as ShelfRow) : null;
  const highestDomestic = domestic.length > 0 ? (domestic[0] as ShelfRow) : null;
  return {
    everyInternationalAhead:
      lowestInternational !== null &&
      highestDomestic !== null &&
      lowestInternational.priorityBp > highestDomestic.priorityBp,
    lowestInternational,
    highestDomestic,
    last: rows.length > 0 ? (rows[rows.length - 1] as ShelfRow) : null,
  };
}

/** Basis points a year, to one decimal. Everything on the page is quoted this way. */
export function bp(value: number): string {
  return value.toFixed(1);
}

/** A rate as a percentage with its trailing zeros trimmed: 0.238 becomes "23.8". */
export function ratePercent(rate: number, maxDecimals = 3): string {
  const text = (rate * 100).toFixed(maxDecimals);
  return text.includes(".") ? text.replace(/\.?0+$/, "") : text;
}
