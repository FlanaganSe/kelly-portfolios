import { describe, expect, it } from "vitest";
import { captureOfCeiling, effectiveBreadth, stackingCeiling, stackingProbability } from "~/lib/stacking";

const SINGLE = 0.55;

describe("effective breadth", () => {
  it("is the sleeve count when the sleeves are independent", () => {
    expect(effectiveBreadth(10, 0)).toBe(10);
  });

  it("converges to 1 / rho", () => {
    expect(effectiveBreadth(1_000_000, 0.4)).toBeCloseTo(2.5, 4);
  });

  it("refuses a correlation outside [0, 1)", () => {
    expect(() => effectiveBreadth(5, 1)).toThrow(RangeError);
    expect(() => effectiveBreadth(5, -0.1)).toThrow(RangeError);
  });

  it("refuses fewer than one sleeve", () => {
    expect(() => effectiveBreadth(0, 0.2)).toThrow(RangeError);
  });
});

/**
 * The published table in `docs/research/stacking-and-effective-breadth.md` §1, read off
 * the page and typed in here by hand. It is the independent fixture: the doc's numbers
 * came out of the Python study, and nothing in this file has seen that code.
 */
describe("the published stacking table", () => {
  const rows: ReadonlyArray<readonly [number, Readonly<Record<number, number>>]> = [
    [0.0, { 1: 0.55, 2: 0.571, 3: 0.586, 5: 0.611, 10: 0.654, 25: 0.735, 100: 0.896 }],
    [0.1, { 1: 0.55, 2: 0.567, 3: 0.579, 5: 0.594, 10: 0.613, 25: 0.633, 100: 0.648 }],
    [0.2, { 1: 0.55, 2: 0.564, 3: 0.573, 5: 0.583, 10: 0.594, 25: 0.603, 100: 0.609 }],
    [0.4, { 1: 0.55, 2: 0.56, 3: 0.564, 5: 0.569, 10: 0.573, 25: 0.577, 100: 0.578 }],
    [0.7, { 1: 0.55, 2: 0.554, 3: 0.556, 5: 0.557, 10: 0.558, 25: 0.559, 100: 0.56 }],
  ];

  for (const [correlation, expected] of rows) {
    it(`reproduces the rho = ${correlation} row`, () => {
      for (const [count, probability] of Object.entries(expected)) {
        expect(stackingProbability({ count: Number(count), correlation, single: SINGLE })).toBeCloseTo(probability, 3);
      }
    });
  }

  it("reproduces the published limits", () => {
    expect(stackingCeiling({ correlation: 0.1, single: SINGLE })).toBeCloseTo(0.654, 3);
    expect(stackingCeiling({ correlation: 0.2, single: SINGLE })).toBeCloseTo(0.611, 3);
    expect(stackingCeiling({ correlation: 0.4, single: SINGLE })).toBeCloseTo(0.579, 3);
    expect(stackingCeiling({ correlation: 0.7, single: SINGLE })).toBeCloseTo(0.56, 3);
  });

  it("reproduces the measured 0.435 correlation reaching 0.576", () => {
    expect(stackingCeiling({ correlation: 0.435, single: SINGLE })).toBeCloseTo(0.576, 3);
  });
});

describe("the ceiling", () => {
  it("is certainty at zero correlation, which no finite stack reaches", () => {
    expect(stackingCeiling({ correlation: 0, single: SINGLE })).toBe(1);
    expect(stackingProbability({ count: 100, correlation: 0, single: SINGLE })).toBeLessThan(0.9);
  });

  it("bounds every finite stack above it", () => {
    for (const correlation of [0.1, 0.2, 0.435, 0.7]) {
      const ceiling = stackingCeiling({ correlation, single: SINGLE });
      expect(stackingProbability({ count: 10_000, correlation, single: SINGLE })).toBeLessThan(ceiling);
    }
  });

  it("drives a losing bet further down rather than diversifying it away", () => {
    // Breadth multiplies whatever sign the edge has. Stacking a sleeve with a 40% chance
    // of finishing ahead converges on 35%, not on a coin flip.
    expect(stackingCeiling({ correlation: 0.435, single: 0.4 })).toBeCloseTo(0.35, 2);
    expect(stackingProbability({ count: 10, correlation: 0.435, single: 0.4 })).toBeLessThan(0.4);
  });
});

describe("capture of the ceiling", () => {
  it("is nothing at one sleeve and nearly everything at ten thousand", () => {
    expect(captureOfCeiling({ count: 1, correlation: 0.435, single: SINGLE })).toBeCloseTo(0, 12);
    expect(captureOfCeiling({ count: 10_000, correlation: 0.435, single: SINGLE })).toBeGreaterThan(0.99);
  });

  it("says five sleeves already buy two thirds of what infinity could", () => {
    expect(captureOfCeiling({ count: 5, correlation: 0.435, single: SINGLE })).toBeCloseTo(0.681, 2);
  });

  it("has no meaning without a positive correlation", () => {
    expect(() => captureOfCeiling({ count: 5, correlation: 0, single: SINGLE })).toThrow(RangeError);
  });
});
