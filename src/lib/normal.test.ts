import { describe, expect, it } from "vitest";
import fixtures from "~/lib/fixtures/research-ground-truth.json";
import { normalCdf, normalPpf } from "~/lib/normal";

/**
 * The fixtures come from scipy via the research workspace, so they are computed
 * independently of the code under test. A tolerance is never widened to make one pass.
 */
const ABSOLUTE_TOLERANCE = 1e-12;

describe("normalCdf", () => {
  for (const testCase of fixtures.normalCdf) {
    it(`matches the research workspace at x = ${testCase.x}`, () => {
      expect(Math.abs(normalCdf(testCase.x) - testCase.expected)).toBeLessThanOrEqual(ABSOLUTE_TOLERANCE);
    });
  }

  it("holds the tails, where a cheap polynomial would not", () => {
    // Both endpoints of the fixture range, restated as the property that matters.
    expect(normalCdf(-6)).toBeGreaterThan(0);
    expect(normalCdf(-6)).toBeLessThan(1e-8);
    expect(1 - normalCdf(6)).toBeGreaterThan(0);
  });

  it("is symmetric about zero", () => {
    // The upper-tail side loses its last bit or two to `1 - p`, so this is as tight as
    // the comparison can be made in double precision.
    for (const x of [0.25, 1, 2.5, 4, 6]) {
      expect(Math.abs(normalCdf(-x) - (1 - normalCdf(x)))).toBeLessThanOrEqual(1e-15);
    }
  });

  it("rejects a non-finite argument", () => {
    expect(() => normalCdf(Number.NaN)).toThrow(RangeError);
    expect(() => normalCdf(Number.NaN)).toThrow(/finite/);
    expect(() => normalCdf(Number.POSITIVE_INFINITY)).toThrow(RangeError);
  });
});

describe("normalPpf", () => {
  for (const testCase of fixtures.normalPpf) {
    it(`matches the research workspace at p = ${testCase.p}`, () => {
      expect(Math.abs(normalPpf(testCase.p) - testCase.expected)).toBeLessThanOrEqual(ABSOLUTE_TOLERANCE);
    });
  }

  it("rejects a probability outside (0, 1)", () => {
    for (const p of [0, 1, -0.5, 1.5, Number.NaN]) {
      expect(() => normalPpf(p)).toThrow(RangeError);
      expect(() => normalPpf(p)).toThrow(/probability/);
    }
  });
});

describe("normalCdf and normalPpf round-trip", () => {
  it("recovers p from Phi(Phi^-1(p)) to machine precision", () => {
    const probabilities = [1e-8, 1e-4, 0.001, 0.01, 0.02425, 0.05, 0.25, 0.5, 0.75, 0.9, 0.99, 0.999, 1 - 1e-8];
    for (const p of probabilities) {
      const recovered = normalCdf(normalPpf(p));
      expect(Math.abs(recovered - p)).toBeLessThanOrEqual(Math.abs(p) * 1e-14);
    }
  });

  it("recovers x from Phi^-1(Phi(x)) across the range", () => {
    for (let x = -5; x <= 5.0001; x += 0.25) {
      const recovered = normalPpf(normalCdf(x));
      expect(Math.abs(recovered - x)).toBeLessThanOrEqual(1e-9);
    }
  });
});
