import { describe, expect, it } from "vitest";
import fixtures from "~/lib/fixtures/research-ground-truth.json";
import {
  CaptureDoubleCountError,
  certaintyEquivalentContribution,
  deliveredLoading,
  incrementalCost,
  marginalGrowthContribution,
  portfolioTrackingError,
  sleeveEdge,
  sleeveTrackingError,
  substitutionVarianceChange,
  type TiltInputs,
  terminalWealthMultiple,
  tiltVerdict,
  turnoverCostPercent,
  varianceDrag,
} from "~/lib/tilt";

/**
 * Relative agreement required against a value the research workspace computed. The
 * repository's rule is that a disagreeing port is wrong; never loosen this.
 */
const RELATIVE_TOLERANCE = 1e-10;

function expectClose(actual: number, expected: number): void {
  const tolerance = Math.max(Math.abs(expected) * RELATIVE_TOLERANCE, 1e-12);
  expect(Math.abs(actual - expected)).toBeLessThanOrEqual(tolerance);
}

const { cases, turnoverCost, terminalWealthMultiple: wealthCases } = fixtures.valueTilt;

/** The published tilts, so a failure names the row of §5 that broke. */
function caseLabelled(prefix: string): (typeof cases)[number] {
  const row = cases.find((candidate) => candidate.label.startsWith(prefix));
  if (row === undefined) {
    throw new Error(`no fixture case labelled ${prefix}; regenerate the fixture file`);
  }
  return row;
}

const AVLV = caseLabelled("AVLV 20%");
const DFIV = caseLabelled("DFIV 8%");

function inputsOf(row: { readonly inputs: TiltInputs }): TiltInputs {
  return row.inputs;
}

describe("the fixture file", () => {
  it("carries the value-tilt block the client is tested against", () => {
    expect(fixtures._provenance.sourceModules).toContain("portfolio_edge.studies.value_tilt");
    expect(cases.length).toBeGreaterThan(0);
  });
});

describe("tilt arithmetic against the research workspace", () => {
  it(`matches all ${cases.length} cases on every derived quantity`, () => {
    for (const testCase of cases) {
      const inputs = inputsOf(testCase);
      expectClose(deliveredLoading(inputs), testCase.deliveredLoading);
      expectClose(incrementalCost(inputs), testCase.incrementalCost);
      expectClose(sleeveTrackingError(inputs), testCase.sleeveTrackingError);
      expectClose(sleeveEdge(inputs), testCase.sleeveEdge);
      expectClose(portfolioTrackingError(inputs), testCase.portfolioTrackingError);
      expectClose(substitutionVarianceChange(inputs), testCase.substitutionVarianceChange);
      expectClose(marginalGrowthContribution(inputs), testCase.marginalGrowthContribution);
    }
  });

  it("matches the variance drag and certainty equivalent at every gamma", () => {
    for (const testCase of cases) {
      const inputs = inputsOf(testCase);
      for (const row of testCase.varianceDrag) {
        expectClose(varianceDrag(inputs, { gamma: row.gamma }), row.expected);
      }
      for (const row of testCase.certaintyEquivalentContribution) {
        expectClose(certaintyEquivalentContribution(inputs, { gamma: row.gamma }), row.expected);
      }
    }
  });

  it("matches every field of every verdict", () => {
    for (const testCase of cases) {
      const expected = testCase.verdict;
      const actual = tiltVerdict(inputsOf(testCase), {
        gamma: expected.gamma,
        years: expected.years,
      });
      expectClose(actual.weight, expected.weight);
      expectClose(actual.deliveredLoading, expected.deliveredLoading);
      expectClose(actual.hmlPremium, expected.hmlPremium);
      expectClose(actual.incrementalCost, expected.incrementalCost);
      expectClose(actual.sleeveEdgePercent, expected.sleeveEdgePercent);
      expectClose(actual.portfolioEdgeBasisPoints, expected.portfolioEdgeBasisPoints);
      expectClose(actual.portfolioTrackingErrorBasisPoints, expected.portfolioTrackingErrorBasisPoints);
      expectClose(actual.growthContributionPercent, expected.growthContributionPercent);
      expectClose(actual.certaintyEquivalentPercent, expected.certaintyEquivalentPercent);
      expectClose(actual.terminalWealthMultiple30y, expected.terminalWealthMultiple30y);
    }
  });

  it(`matches all ${turnoverCost.length} turnover-cost cases`, () => {
    for (const row of turnoverCost) {
      expectClose(
        turnoverCostPercent({
          oneSidedTurnoverPercent: row.oneSidedTurnoverPercent,
          coefficient: row.coefficient,
        }),
        row.expected
      );
    }
  });

  it(`matches all ${wealthCases.length} terminal-wealth cases`, () => {
    for (const row of wealthCases) {
      expectClose(
        terminalWealthMultiple({
          growthContribution: row.growthContribution,
          years: row.years,
        }),
        row.expected
      );
    }
  });

  it("uses the gamma and years the verdict defaults to", () => {
    const inputs = inputsOf(AVLV);
    expect(tiltVerdict(inputs)).toEqual(tiltVerdict(inputs, { gamma: 3, years: 30 }));
  });
});

describe("the tilts §5 publishes", () => {
  it("reproduces the AVLV row: +24.4 bp, 135 bp, +24.9 bp growth, 1.078 over 30 years", () => {
    const verdict = tiltVerdict(inputsOf(AVLV));
    expect(verdict.portfolioEdgeBasisPoints).toBeCloseTo(24.4, 1);
    expect(verdict.portfolioTrackingErrorBasisPoints).toBeCloseTo(135.4, 1);
    expect(verdict.growthContributionPercent / 0.01).toBeCloseTo(24.9, 1);
    expect(verdict.certaintyEquivalentPercent / 0.01).toBeCloseTo(26.0, 1);
    expect(verdict.terminalWealthMultiple30y).toBeCloseTo(1.078, 3);
  });

  it("reproduces the DFIV row: +27.1 bp, 47.6 bp, +29.5 bp growth, +34.2 bp CE", () => {
    const verdict = tiltVerdict(inputsOf(DFIV));
    expect(verdict.incrementalCost).toBeCloseTo(0.274, 3);
    expect(verdict.portfolioEdgeBasisPoints).toBeCloseTo(27.1, 1);
    expect(verdict.portfolioTrackingErrorBasisPoints).toBeCloseTo(47.6, 1);
    expect(verdict.growthContributionPercent / 0.01).toBeCloseTo(29.5, 1);
    expect(verdict.certaintyEquivalentPercent / 0.01).toBeCloseTo(34.2, 1);
  });

  it("charges DFIV a negative drag, because the fund is quieter than the VEA it replaces", () => {
    // The certainty equivalent exceeding the growth contribution is only possible when
    // the substitution *reduces* portfolio variance, and the sign is worth pinning: a
    // gamma that made a tilt look better would otherwise pass unnoticed.
    const inputs = inputsOf(DFIV);
    expect(substitutionVarianceChange(inputs)).toBeLessThan(0);
    expect(certaintyEquivalentContribution(inputs, { gamma: 3 })).toBeGreaterThan(marginalGrowthContribution(inputs));
  });
});

describe("a capture fraction is refused", () => {
  it("throws CaptureDoubleCountError rather than applying the long-only discount twice", () => {
    const inputs = inputsOf(AVLV);
    expect(() => sleeveEdge(inputs, { capture: 0.52 })).toThrow(CaptureDoubleCountError);
    expect(() => sleeveEdge(inputs, { capture: 0.52 })).toThrow(/0\.52/);
    // Zero is a capture fraction too, and the falsy check that lets it through is the
    // easy way to reintroduce the bug in JavaScript.
    expect(() => sleeveEdge(inputs, { capture: 0 })).toThrow(CaptureDoubleCountError);
  });

  it("computes normally when nothing is passed, including an explicit empty options bag", () => {
    const inputs = inputsOf(AVLV);
    expect(sleeveEdge(inputs, {})).toBe(sleeveEdge(inputs));
    expect(sleeveEdge(inputs, { capture: undefined })).toBe(sleeveEdge(inputs));
  });
});

describe("validation", () => {
  const base = inputsOf(AVLV);

  it("rejects a weight outside [0, 1]", () => {
    expect(() => sleeveEdge({ ...base, weight: -0.01 })).toThrow(RangeError);
    expect(() => sleeveEdge({ ...base, weight: 1.01 })).toThrow(RangeError);
    expect(() => sleeveEdge({ ...base, weight: Number.NaN })).toThrow(/weight must lie/);
    expect(() => sleeveEdge({ ...base, weight: 0 })).not.toThrow();
    expect(() => sleeveEdge({ ...base, weight: 1 })).not.toThrow();
  });

  it("rejects a non-positive volatility on either leg", () => {
    expect(() => sleeveTrackingError({ ...base, fundVolatility: 0 })).toThrow(/volatilities must be positive/);
    expect(() => sleeveTrackingError({ ...base, benchmarkVolatility: -1 })).toThrow(/volatilities must be positive/);
  });

  it("rejects a correlation outside [-1, 1]", () => {
    expect(() => sleeveTrackingError({ ...base, correlation: 1.0001 })).toThrow(/correlation must lie/);
    expect(() => sleeveTrackingError({ ...base, correlation: -1.0001 })).toThrow(/correlation must lie/);
    expect(() => sleeveTrackingError({ ...base, correlation: 1 })).not.toThrow();
    expect(() => sleeveTrackingError({ ...base, correlation: -1 })).not.toThrow();
  });

  it("rejects a negative turnover or a negative coefficient", () => {
    expect(() => turnoverCostPercent({ oneSidedTurnoverPercent: -1, coefficient: 1.7 })).toThrow(
      /turnover cannot be negative/
    );
    expect(() => turnoverCostPercent({ oneSidedTurnoverPercent: 6, coefficient: -1 })).toThrow(
      /coefficient cannot be negative/
    );
  });

  it("rejects a non-positive gamma", () => {
    expect(() => varianceDrag(base, { gamma: 0 })).toThrow(/gamma must be positive/);
    expect(() => certaintyEquivalentContribution(base, { gamma: -3 })).toThrow(/gamma must be positive/);
  });

  it("rejects a negative horizon", () => {
    expect(() => terminalWealthMultiple({ growthContribution: 0.21, years: -1 })).toThrow(/years cannot be negative/);
  });
});

describe("identities the chain has to satisfy", () => {
  const base = inputsOf(AVLV);

  it("gives an edge of exactly minus the incremental cost when nothing is delivered", () => {
    // This is the whole argument for the loading form: buy no exposure and you pay the
    // fee anyway, at every premium, however large.
    for (const hmlPremium of [-4.74, 0, 1.57, 4.740625, 100]) {
      const inputs: TiltInputs = { ...base, fundHmlLoading: 0.35, benchmarkHmlLoading: 0.35, hmlPremium };
      expectClose(sleeveEdge(inputs), -incrementalCost(inputs));
      expectClose(deliveredLoading(inputs), 0);
    }
  });

  it("leaves the portfolio untouched at a zero weight", () => {
    const inputs: TiltInputs = { ...base, weight: 0 };
    expect(substitutionVarianceChange(inputs)).toBe(0);
    expect(portfolioTrackingError(inputs)).toBe(0);
    expect(marginalGrowthContribution(inputs)).toBe(0);
    expect(terminalWealthMultiple({ growthContribution: 0, years: 30 })).toBe(1);
  });

  it("collapses the sleeve tracking error to the volatility gap at a correlation of one", () => {
    const inputs: TiltInputs = { ...base, correlation: 1 };
    expectClose(sleeveTrackingError(inputs), Math.abs(inputs.fundVolatility - inputs.benchmarkVolatility));
    expect(sleeveTrackingError({ ...inputs, fundVolatility: inputs.benchmarkVolatility })).toBe(0);
  });

  it("scales the edge and the tracking error together, so the horizon is weight-free", () => {
    // §5's "P(30 yr) and the horizon do not vary with weight": both are linear in it.
    const at = (weight: number) => tiltVerdict({ ...base, weight });
    const ratio = (weight: number) =>
      at(weight).portfolioEdgeBasisPoints / at(weight).portfolioTrackingErrorBasisPoints;
    expectClose(ratio(0.1), ratio(0.3));
    expectClose(ratio(0.3), ratio(1));
  });

  it("makes the growth contribution the certainty equivalent at gamma one", () => {
    for (const testCase of cases) {
      const inputs = inputsOf(testCase);
      expectClose(certaintyEquivalentContribution(inputs, { gamma: 1 }), marginalGrowthContribution(inputs));
    }
  });
});
