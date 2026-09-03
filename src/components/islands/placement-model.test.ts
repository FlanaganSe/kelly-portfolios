import { describe, expect, it } from "vitest";
import {
  fill,
  forfeitedCreditBp,
  queue,
  rank,
  shelf,
  toCandidate,
  verdict,
} from "~/components/islands/placement-model";
import { creditForfeitedByPlanBp, investorHoldings, investorRates, taxRegimes } from "~/content/placement";
import { derivedRates } from "~/lib/placement";

/**
 * The tool is only worth shipping if it reproduces the committed research figures, so
 * every assertion here is against `src/content/placement.ts` rather than against a
 * number written out again.
 */

const topBracket = taxRegimes.find((regime) => regime.id === "us-top");
const upperMiddle = taxRegimes.find((regime) => regime.id === "us-upper-middle");
if (topBracket === undefined || upperMiddle === undefined) throw new Error("missing a named tax regime");

/** `investorRates` is [23.8, 18.8, 15]; the two named regimes are the first and last. */
const [topRate, , upperMiddleRate] = investorRates;

describe("toCandidate", () => {
  it("recovers each fund's withholding rate from its two yields", () => {
    const avdv = investorHoldings.find((holding) => holding.ticker === "AVDV");
    if (avdv === undefined) throw new Error("AVDV is not on the shelf");
    // 6.068% of Box 1a is the rate `placementInputs` states for developed ex-US.
    expect(toCandidate(avdv).foreignWithholdingRate).toBeCloseTo(0.06068, 4);
  });

  it("gives a fund with no foreign tax a withholding rate of zero", () => {
    const vti = investorHoldings.find((holding) => holding.ticker === "VTI");
    if (vti === undefined) throw new Error("VTI is not on the shelf");
    expect(toCandidate(vti).foreignWithholdingRate).toBe(0);
  });
});

describe("shelf", () => {
  it("keeps one row per ticker", () => {
    const tickers = shelf("paid-out").map((holding) => holding.ticker);
    expect(new Set(tickers).size).toBe(tickers.length);
  });

  it("keeps the smaller distribution on the audited reading and the larger on the other", () => {
    const paidOut = shelf("paid-out").find((holding) => holding.ticker === "RSST");
    const recorded = shelf("recorded").find((holding) => holding.ticker === "RSST");
    if (paidOut === undefined || recorded === undefined) throw new Error("RSST is not on the shelf");
    expect(paidOut.boxOneAYield).toBeLessThan(recorded.boxOneAYield);
    expect(paidOut.account).toBe("split");
    expect(recorded.account).toBe("shelter");
  });

  it("weights sum to the whole portfolio once the duplicate is dropped", () => {
    const total = shelf("paid-out").reduce((sum, holding) => sum + holding.weight, 0);
    expect(total).toBeCloseTo(1, 10);
  });
});

describe("rank", () => {
  it(`reproduces every committed priority at ${topRate}% qualified`, () => {
    expect(derivedRates(topBracket).qualifiedDividend * 100).toBeCloseTo(topRate as number, 10);
    for (const holding of investorHoldings) {
      const got = rank(holding, topBracket).priorityBp;
      expect(got, `${holding.ticker} ${holding.name}`).toBeCloseTo(holding.priorityBp[0], 1);
    }
  });

  it(`reproduces every committed priority at ${upperMiddleRate}% qualified`, () => {
    expect(derivedRates(upperMiddle).qualifiedDividend * 100).toBeCloseTo(upperMiddleRate as number, 10);
    for (const holding of investorHoldings) {
      const got = rank(holding, upperMiddle).priorityBp;
      expect(got, `${holding.ticker} ${holding.name}`).toBeCloseTo(holding.priorityBp[2], 1);
    }
  });

  it("splits each priority into the tax paid and the credit forfeited", () => {
    for (const holding of investorHoldings) {
      const row = rank(holding, topBracket);
      expect(row.priorityBp).toBeCloseTo(row.taxableBp - row.shelteredBp, 10);
    }
  });
});

describe("queue", () => {
  it("orders the seven published funds the way the research does at the top bracket", () => {
    const rows = queue(shelf("recorded"), topBracket);
    expect(rows.map((row) => row.ticker)).toEqual(["RSST", "IDMO", "AVES", "AVDV", "VXUS", "VTV", "VTI"]);
  });

  it("holds the published weights", () => {
    const weights = Object.fromEntries(shelf("recorded").map((holding) => [holding.ticker, holding.weight]));
    expect(weights).toEqual({ RSST: 0.3, VTI: 0.19, VTV: 0.15, VXUS: 0.16, AVDV: 0.1, IDMO: 0.05, AVES: 0.05 });
  });

  it("ranks best first", () => {
    const rows = queue(shelf("paid-out"), topBracket);
    const sorted = [...rows].sort((a, b) => b.priorityBp - a.priorityBp);
    expect(rows.map((row) => row.ticker)).toEqual(sorted.map((row) => row.ticker));
  });

  it("refuses a shelf that files the same ticker twice", () => {
    expect(() => queue(investorHoldings, topBracket)).toThrow(RangeError);
  });
});

describe("verdict, on the audited reading", () => {
  for (const [name, regime] of [
    ["the top bracket", topBracket],
    ["the upper-middle bracket", upperMiddle],
  ] as const) {
    it(`puts every international fund above every US fund at ${name}`, () => {
      const rows = queue(shelf("paid-out"), regime);
      const call = verdict(rows);
      expect(call.everyInternationalAhead).toBe(true);
      expect(call.lowestInternational?.priorityBp).toBeGreaterThan(call.highestDomestic?.priorityBp ?? 0);
    });

    it(`puts the total-market US fund last at ${name}`, () => {
      const rows = queue(shelf("paid-out"), regime);
      expect(verdict(rows).last?.ticker).toBe("VTI");
    });
  }

  it("stops holding once the fund's own recorded income is counted", () => {
    const rows = queue(shelf("recorded"), topBracket);
    // The stacked fund is a US equity line and it goes straight to the top, which is
    // what the portfolio page prints. The claim is about the funds behind it.
    expect(rows[0]?.ticker).toBe("RSST");
    expect(verdict(rows).everyInternationalAhead).toBe(false);
  });
});

describe("fill", () => {
  const rows = queue(shelf("paid-out"), topBracket);

  it("shelters nothing when there is no shelter", () => {
    const placed = fill(rows, 0);
    expect(placed.every((row) => row.where === "taxable")).toBe(true);
    expect(forfeitedCreditBp(placed)).toBe(0);
  });

  it("shelters everything when the shelter covers the portfolio", () => {
    const placed = fill(rows, 1);
    expect(placed.every((row) => row.where === "shelter")).toBe(true);
  });

  it("never places more than the capacity", () => {
    for (const capacity of [0.1, 0.25, 0.5, 0.6667, 0.9]) {
      const placed = fill(rows, capacity);
      const used = placed.reduce((sum, row) => sum + row.shelteredWeight, 0);
      expect(used).toBeLessThanOrEqual(capacity + 1e-12);
      expect(used).toBeCloseTo(Math.min(capacity, 1), 10);
    }
  });

  it("splits the one line the shelter runs out inside", () => {
    const placed = fill(rows, 0.5);
    expect(placed.filter((row) => row.where === "split").length).toBeLessThanOrEqual(1);
  });

  it("fills from the top of the queue", () => {
    const placed = fill(rows, 0.2);
    const sheltered = placed.filter((row) => row.shelteredWeight > 0).map((row) => row.ticker);
    expect(sheltered).toEqual(rows.slice(0, sheltered.length).map((row) => row.ticker));
  });

  it("refuses a negative shelter", () => {
    expect(() => fill(rows, -0.1)).toThrow(RangeError);
  });
});

describe("forfeitedCreditBp", () => {
  it("matches the committed figure when the whole portfolio is sheltered", () => {
    const placed = fill(queue(shelf("paid-out"), topBracket), 1);
    expect(forfeitedCreditBp(placed)).toBeCloseTo(creditForfeitedByPlanBp, 2);
  });

  it("is the same in every bracket, because a shelter owes no US tax to credit against", () => {
    const top = forfeitedCreditBp(fill(queue(shelf("paid-out"), topBracket), 1));
    const middle = forfeitedCreditBp(fill(queue(shelf("paid-out"), upperMiddle), 1));
    expect(top).toBeCloseTo(middle, 10);
  });
});
