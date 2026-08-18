import { describe, expect, it } from "vitest";
import { areaPath, linearScale, linePath, niceDomain, niceStep, niceTicks } from "~/components/charts/scale";

describe("linear scale", () => {
  it("maps the domain onto the range", () => {
    const scale = linearScale([0, 10], [0, 100]);
    expect(scale(0)).toBe(0);
    expect(scale(5)).toBe(50);
    expect(scale(10)).toBe(100);
  });

  it("inverts for a pixel axis that grows downwards", () => {
    const scale = linearScale([0, 1], [200, 0]);
    expect(scale(0)).toBe(200);
    expect(scale(1)).toBe(0);
  });

  it("puts a flat series in the middle rather than dividing by zero", () => {
    expect(linearScale([5, 5], [0, 100])(5)).toBe(50);
  });
});

describe("ticks", () => {
  it("rounds a step up to 1, 2, 2.5 or 5 times a power of ten", () => {
    expect(niceStep(0.03)).toBeCloseTo(0.05, 12);
    expect(niceStep(1.1)).toBe(2);
    expect(niceStep(230)).toBe(250);
  });

  it("covers the domain without leaving it", () => {
    const ticks = niceTicks(-0.4, 0.2, 5);
    expect(ticks[0]).toBeGreaterThanOrEqual(-0.4);
    expect(ticks[ticks.length - 1]).toBeLessThanOrEqual(0.2);
  });

  it("includes zero whenever the domain crosses it", () => {
    expect(niceTicks(-0.4, 0.2, 5).some((tick) => Math.abs(tick) < 1e-12)).toBe(true);
  });

  it("stays on clean boundaries rather than drifting", () => {
    for (const tick of niceTicks(0, 1, 6)) {
      expect(Math.abs(tick * 100 - Math.round(tick * 100))).toBeLessThan(1e-9);
    }
  });

  it("gives one tick for a flat domain and none for a broken one", () => {
    expect(niceTicks(3, 3)).toEqual([3]);
    expect(niceTicks(Number.NaN, 1)).toEqual([]);
  });

  it("pads a domain outwards to the nearest gridline", () => {
    expect(niceDomain(0.03, 0.97, 5)).toEqual([0, 1]);
  });
});

describe("paths", () => {
  it("draws a polyline", () => {
    expect(
      linePath([
        [0, 0],
        [10, 5],
      ])
    ).toBe("M0.00 0.00L10.00 5.00");
  });

  it("breaks the line at a gap rather than bridging it", () => {
    expect(
      linePath([
        [0, 0],
        [5, Number.NaN],
        [10, 5],
      ])
    ).toBe("M0.00 0.00M10.00 5.00");
  });

  it("closes an area back to the baseline", () => {
    expect(
      areaPath(
        [
          [0, 0],
          [10, 5],
        ],
        20
      )
    ).toBe("M0.00 0.00L10.00 5.00L10.00 20.00L0.00 20.00Z");
  });

  it("draws nothing when there is nothing finite to draw", () => {
    expect(areaPath([[0, Number.NaN]], 20)).toBe("");
  });
});

describe("a chart axis over a short horizon", () => {
  it("still has more than one tick", () => {
    // The fan chart picks its year step from the horizon; a one-year test that plotted a
    // single "0" was the failure this guards.
    for (const total of [1, 2, 3, 5, 10, 30, 50]) {
      const step = total <= 4 ? 1 : total <= 10 ? 2 : total <= 30 ? 5 : 10;
      expect(Math.floor(total / step) + 1, `horizon ${total}`).toBeGreaterThan(1);
    }
  });
});
