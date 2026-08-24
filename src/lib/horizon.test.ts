import { describe, expect, it } from "vitest";
import fixtures from "~/lib/fixtures/research-ground-truth.json";
import {
  aggregate,
  detectableEdgeBp,
  type EdgeComponent,
  horizonForConfidence,
  probabilityOfOutperformance,
  terminalWealthRatio,
} from "~/lib/horizon";

/** Relative agreement required against a value the research workspace computed. */
const RELATIVE_TOLERANCE = 1e-9;

function expectClose(actual: number, expected: number): void {
  const tolerance = Math.max(Math.abs(expected) * RELATIVE_TOLERANCE, 1e-12);
  expect(Math.abs(actual - expected)).toBeLessThanOrEqual(tolerance);
}

function component(overrides: Partial<EdgeComponent> = {}): EdgeComponent {
  return {
    name: "Test line",
    benchmark: "stated-index",
    certainty: "probabilistic",
    lowBp: 0,
    centralBp: 10,
    highBp: 20,
    trackingErrorBp: 30,
    ...overrides,
  };
}

describe("probabilityOfOutperformance", () => {
  it(`matches all ${fixtures.probabilityOfOutperformance.length} research-workspace cases`, () => {
    for (const testCase of fixtures.probabilityOfOutperformance) {
      expectClose(
        probabilityOfOutperformance({
          edgeBp: testCase.edgeBp,
          trackingErrorBp: testCase.trackingErrorBp,
          horizonYears: testCase.horizonYears,
        }),
        testCase.expected
      );
    }
  });

  it("treats a zero tracking error as the contractual case, not a degenerate one", () => {
    const certain = { trackingErrorBp: 0, horizonYears: 1 };
    expect(probabilityOfOutperformance({ ...certain, edgeBp: 49 })).toBe(1);
    expect(probabilityOfOutperformance({ ...certain, edgeBp: -49 })).toBe(0);
    expect(probabilityOfOutperformance({ ...certain, edgeBp: 0 })).toBe(0.5);
    // And it does not decay with the horizon, which is the point of the branch.
    expect(probabilityOfOutperformance({ trackingErrorBp: 0, horizonYears: 50, edgeBp: 49 })).toBe(1);
  });

  it("rises with the horizon for a positive edge and falls for a negative one", () => {
    const at = (horizonYears: number, edgeBp: number) =>
      probabilityOfOutperformance({ edgeBp, trackingErrorBp: 140, horizonYears });
    expect(at(30, 15.2)).toBeGreaterThan(at(5, 15.2));
    expect(at(30, -7.8)).toBeLessThan(at(5, -7.8));
  });

  it("rejects a non-positive horizon and a negative tracking error", () => {
    expect(() => probabilityOfOutperformance({ edgeBp: 10, trackingErrorBp: 5, horizonYears: 0 })).toThrow(
      /horizonYears must be positive/
    );
    expect(() => probabilityOfOutperformance({ edgeBp: 10, trackingErrorBp: -1, horizonYears: 1 })).toThrow(
      /trackingErrorBp cannot be negative/
    );
  });
});

describe("horizonForConfidence", () => {
  it(`matches all ${fixtures.horizonForConfidence.length} research-workspace cases`, () => {
    for (const testCase of fixtures.horizonForConfidence) {
      expectClose(
        horizonForConfidence({
          edgeBp: testCase.edgeBp,
          trackingErrorBp: testCase.trackingErrorBp,
          confidence: testCase.confidence,
        }),
        testCase.expected
      );
    }
  });

  it("quadruples the horizon when the edge is halved", () => {
    const full = horizonForConfidence({ edgeBp: 24.4, trackingErrorBp: 401, confidence: 0.95 });
    const half = horizonForConfidence({ edgeBp: 12.2, trackingErrorBp: 401, confidence: 0.95 });
    expectClose(half, full * 4);
  });

  it("rejects a non-positive edge, a negative tracking error and a confidence outside [0.5, 1)", () => {
    expect(() => horizonForConfidence({ edgeBp: 0, trackingErrorBp: 10, confidence: 0.9 })).toThrow(
      /edgeBp must be positive/
    );
    expect(() => horizonForConfidence({ edgeBp: 10, trackingErrorBp: -1, confidence: 0.9 })).toThrow(
      /trackingErrorBp cannot be negative/
    );
    for (const confidence of [0.49, 1, 1.5, -0.1]) {
      expect(() => horizonForConfidence({ edgeBp: 10, trackingErrorBp: 10, confidence })).toThrow(
        /confidence must lie in \[0.5, 1\)/
      );
    }
  });
});

describe("detectableEdgeBp", () => {
  it(`matches all ${fixtures.detectableEdgeBp.length} research-workspace cases`, () => {
    for (const testCase of fixtures.detectableEdgeBp) {
      expectClose(
        detectableEdgeBp({
          trackingErrorBp: testCase.trackingErrorBp,
          horizonYears: testCase.horizonYears,
          confidence: testCase.confidence,
        }),
        testCase.expected
      );
    }
  });

  it("inverts horizonForConfidence", () => {
    const trackingErrorBp = 251;
    const confidence = 0.95;
    const edgeBp = detectableEdgeBp({ trackingErrorBp, horizonYears: 30, confidence });
    expectClose(horizonForConfidence({ edgeBp, trackingErrorBp, confidence }), 30);
  });

  it("rejects a non-positive horizon and a confidence outside [0.5, 1)", () => {
    expect(() => detectableEdgeBp({ trackingErrorBp: 10, horizonYears: -1, confidence: 0.9 })).toThrow(
      /horizonYears must be positive/
    );
    expect(() => detectableEdgeBp({ trackingErrorBp: 10, horizonYears: 10, confidence: 1 })).toThrow(
      /confidence must lie in \[0.5, 1\)/
    );
  });
});

describe("aggregate", () => {
  it("refuses a list whose components do not share a benchmark", () => {
    const mixed = [
      component({ name: "Fund cost reduction", benchmark: "counterfactual-holding" }),
      component({ name: "Factor tilt", benchmark: "stated-index" }),
    ];
    expect(() => aggregate(mixed)).toThrow(RangeError);
    expect(() => aggregate(mixed)).toThrow(/must share one benchmark/);
    // The message names the benchmarks that collided, so the caller can see the error.
    expect(() => aggregate(mixed)).toThrow(/counterfactual-holding/);
    expect(() => aggregate(mixed)).toThrow(/stated-index/);
  });

  it("refuses all three benchmarks at once", () => {
    const all = [
      component({ benchmark: "stated-index" }),
      component({ benchmark: "average-investor" }),
      component({ benchmark: "counterfactual-holding" }),
    ];
    expect(() => aggregate(all)).toThrow(/must share one benchmark/);
  });

  it("sums within one benchmark and combines tracking errors in quadrature", () => {
    const result = aggregate([
      component({ name: "Rebalancing", lowBp: 0, centralBp: 2.4, highBp: 18, trackingErrorBp: 27 }),
      component({ name: "Factor tilt", lowBp: -30, centralBp: 21, highBp: 80, trackingErrorBp: 400 }),
      component({
        name: "Securities lending",
        certainty: "deterministic",
        lowBp: 0.1,
        centralBp: 1,
        highBp: 3,
        trackingErrorBp: 2,
      }),
    ]);
    expect(result.benchmark).toBe("stated-index");
    expect(result.components).toBe(3);
    expectClose(result.lowBp, -29.9);
    expectClose(result.centralBp, 24.4);
    expectClose(result.highBp, 101);
    expectClose(result.trackingErrorBp, Math.sqrt(27 ** 2 + 400 ** 2 + 2 ** 2));
    // Quadrature is strictly below the arithmetic sum, which is the optimistic half of
    // the independence assumption the module documents.
    expect(result.trackingErrorBp).toBeLessThan(27 + 400 + 2);
  });

  it("refuses an empty budget", () => {
    expect(() => aggregate([])).toThrow(/empty budget/);
  });

  it("refuses a deterministic component whose low estimate is negative", () => {
    expect(() => aggregate([component({ certainty: "deterministic", lowBp: -1, centralBp: 10 })])).toThrow(
      /if the sign is in doubt it is probabilistic/
    );
    // The same figures are acceptable once the line admits it is a bet.
    expect(() => aggregate([component({ certainty: "probabilistic", lowBp: -1, centralBp: 10 })])).not.toThrow();
  });

  it("refuses an out-of-order interval and a negative tracking error", () => {
    expect(() => aggregate([component({ lowBp: 5, centralBp: 1, highBp: 20 })])).toThrow(
      /require low <= central <= high/
    );
    expect(() => aggregate([component({ trackingErrorBp: -1 })])).toThrow(/tracking error cannot be negative/);
  });
});

describe("terminalWealthRatio", () => {
  const cases = fixtures.terminalWealthRatio as readonly {
    edgeBp: number;
    horizonYears: number;
    expected: number;
  }[];

  it("matches every fixture the research workspace emitted", () => {
    expect(cases.length).toBeGreaterThan(0);
    for (const c of cases) {
      const got = terminalWealthRatio({ edgeBp: c.edgeBp, horizonYears: c.horizonYears });
      expect(got).toBeCloseTo(c.expected, 12);
    }
  });

  it("needs no market return, because the market term cancels", () => {
    // The property the front page states. If the ratio moved with the market it would be
    // a forecast rather than an identity.
    const edge = 0.0109;
    for (const marketLogGrowth of [-0.02, 0, 0.07, 0.15]) {
      const ratio = Math.exp((marketLogGrowth + edge) * 30) / Math.exp(marketLogGrowth * 30);
      expect(ratio).toBeCloseTo(terminalWealthRatio({ edgeBp: 109, horizonYears: 30 }), 12);
    }
  });

  it("is 1 at a zero edge, below 1 for a negative one, and rejects a negative horizon", () => {
    expect(terminalWealthRatio({ edgeBp: 0, horizonYears: 30 })).toBe(1);
    expect(terminalWealthRatio({ edgeBp: -7.8, horizonYears: 30 })).toBeLessThan(1);
    expect(() => terminalWealthRatio({ edgeBp: 109, horizonYears: -1 })).toThrow(RangeError);
  });
});
