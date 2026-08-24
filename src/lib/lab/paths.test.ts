import { describe, expect, it } from "vitest";
import { probabilityOfOutperformance } from "~/lib/horizon";
import { percentileOfSorted, simulateRelativePaths } from "~/lib/lab/paths";

const base = { edgeBp: 100, trackingErrorBp: 400, horizonYears: 10, paths: 2000, seed: 7 };

describe("percentiles", () => {
  it("interpolates between the neighbouring observations", () => {
    expect(percentileOfSorted([0, 10], 0.5)).toBe(5);
    expect(percentileOfSorted([0, 10, 20], 0.25)).toBe(5);
  });

  it("has no percentile for an empty sample", () => {
    expect(Number.isNaN(percentileOfSorted([], 0.5))).toBe(true);
  });
});

describe("relative paths", () => {
  it("is reproducible from the seed", () => {
    expect(simulateRelativePaths(base)).toEqual(simulateRelativePaths(base));
  });

  it("changes when the seed changes", () => {
    expect(simulateRelativePaths({ ...base, seed: 8 }).fractionAhead).not.toBe(
      simulateRelativePaths(base).fractionAhead
    );
  });

  it("agrees with the closed form on the chance of being ahead", () => {
    const simulated = simulateRelativePaths({ ...base, paths: 20_000 }).fractionAhead;
    const closedForm = probabilityOfOutperformance({
      edgeBp: base.edgeBp,
      trackingErrorBp: base.trackingErrorBp,
      horizonYears: base.horizonYears,
    });
    expect(simulated).toBeCloseTo(closedForm, 2);
  });

  it("collapses to a single certain path when there is no tracking error", () => {
    const result = simulateRelativePaths({ ...base, trackingErrorBp: 0, paths: 50 });
    expect(result.fractionAhead).toBe(1);
    expect(result.medianLongestDroughtMonths).toBe(0);
    expect(result.bands.p05.at(-1)).toBeCloseTo(result.bands.p95.at(-1) ?? 0, 12);
  });

  it("starts every band at one and runs a month at a time", () => {
    const result = simulateRelativePaths({ ...base, horizonYears: 2, paths: 100 });
    expect(result.months).toBe(24);
    expect(result.bands.p50).toHaveLength(25);
    expect(result.bands.p50[0]).toBe(1);
  });

  it("orders the bands", () => {
    const result = simulateRelativePaths(base);
    const last = result.months;
    expect(result.bands.p05[last]).toBeLessThan(result.bands.p50[last] ?? 0);
    expect(result.bands.p50[last]).toBeLessThan(result.bands.p95[last] ?? 0);
  });

  it("finds long droughts at a tracking error that dwarfs the edge", () => {
    // 40 bp of edge against 500 bp of dispersion: being behind for years is the norm.
    const result = simulateRelativePaths({ edgeBp: 40, trackingErrorBp: 500, horizonYears: 20, paths: 2000, seed: 3 });
    expect(result.fractionWithLongDrought).toBeGreaterThan(0.5);
    expect(result.medianWorstShortfall).toBeLessThan(-0.05);
  });

  it("shortens the drought when the edge is large against the noise", () => {
    const noisy = simulateRelativePaths({ edgeBp: 40, trackingErrorBp: 500, horizonYears: 20, paths: 500, seed: 3 });
    const clean = simulateRelativePaths({ edgeBp: 400, trackingErrorBp: 50, horizonYears: 20, paths: 500, seed: 3 });
    expect(clean.medianLongestDroughtMonths).toBeLessThan(noisy.medianLongestDroughtMonths);
  });
});
