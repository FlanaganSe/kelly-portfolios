import { describe, expect, it } from "vitest";
import { simulateRelativePaths } from "~/lib/lab/paths";

/**
 * Not a benchmark suite — a guard. The lab recomputes this while a slider moves, and a
 * simulation that takes longer than a frame budget makes the whole page feel broken.
 */
describe("simulation cost", () => {
  it("stays well inside an interaction budget at the size the lab uses", () => {
    const started = performance.now();
    simulateRelativePaths({ edgeBp: 46, trackingErrorBp: 313, horizonYears: 50, paths: 2000, seed: 1 });
    // The lab debounces this behind a 150 ms settle, so the budget is a settle, not a frame.
    expect(performance.now() - started).toBeLessThan(400);
  });
});
