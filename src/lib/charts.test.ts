import { describe, expect, it } from "vitest";
import series1990 from "~/content/series/portfolios-1990.json";
import {
  arcPath,
  areaPath,
  donutArcs,
  drawdowns,
  drawdownTicks,
  formatDollars,
  formatMonths,
  formatPct,
  growthTicks,
  linePath,
  monthsBetween,
  roundSignificant,
  scaleLinear,
  scaleLog,
  spreadLabels,
  worstFall,
  yearTicks,
} from "./charts";

describe("formats", () => {
  it("rounds a label to three significant figures and prints every dollar in a table", () => {
    expect(roundSignificant(350671, 3)).toBe(351000);
    expect(roundSignificant(4731, 3)).toBe(4730);
    expect(roundSignificant(999, 3)).toBe(999);
    expect(formatDollars(350671)).toBe("$351,000");
    expect(formatDollars(4731)).toBe("$4,730");
    expect(formatDollars(850)).toBe("$850");
    expect(formatDollars(350671, "exact")).toBe("$350,671");
    expect(formatDollars(12345678)).toBe("$12,300,000");
    expect(formatDollars(-1200)).toBe("−$1,200");
  });

  it("prints a percent with a real minus sign", () => {
    expect(formatPct(-52.71)).toBe("−52.7%");
    expect(formatPct(10.512, 2)).toBe("10.51%");
    expect(formatPct(0.4, 1, true)).toBe("+0.4%");
    expect(formatPct(-0.04)).toBe("0.0%");
  });

  it("counts months", () => {
    expect(formatMonths(63)).toBe("63 months");
    expect(formatMonths(1)).toBe("1 month");
    expect(formatMonths(null)).toBe("not yet");
  });
});

describe("dates", () => {
  it("measures whole months between two dates", () => {
    expect(monthsBetween("2007-10", "2013-01")).toBe(63);
    expect(monthsBetween("1990-11", "2026-05")).toBe(426);
    expect(monthsBetween("2020-02", "2020-02")).toBe(0);
    expect(() => monthsBetween("2020", "2021-01")).toThrow(RangeError);
  });

  it("ticks the first month of every fifth year and skips a partial first year", () => {
    const dates = ["1990-10", "1990-11", "1990-12"];
    for (let y = 1991; y <= 2001; y++) for (let m = 1; m <= 12; m++) dates.push(`${y}-${String(m).padStart(2, "0")}`);
    const ticks = yearTicks(dates, 5);
    expect(ticks.map((t) => t.year)).toEqual([1995, 2000]);
    expect(dates[ticks[0]?.index ?? -1]).toBe("1995-01");
  });
});

describe("scales and ticks", () => {
  it("maps linearly and logarithmically", () => {
    const lin = scaleLinear([0, 10], [0, 100]);
    expect(lin(5)).toBe(50);
    const log = scaleLog([10000, 1000000], [300, 0]);
    expect(log(10000)).toBe(300);
    expect(log(100000)).toBeCloseTo(150);
    expect(log(1000000)).toBeCloseTo(0);
    expect(() => scaleLog([0, 1], [0, 1])).toThrow(RangeError);
  });

  it("puts a growth gridline at 1, 2 and 5 times each power of ten", () => {
    expect(growthTicks(10000, 351000)).toEqual([10000, 20000, 50000, 100000, 200000]);
    expect(growthTicks(4000, 12000)).toEqual([5000, 10000]);
    expect(growthTicks(10000, 1000000)).toEqual([10000, 20000, 50000, 100000, 200000, 500000, 1000000]);
    expect(growthTicks(0, 10)).toEqual([]);
  });

  it("steps a drawdown axis to keep three to six lines", () => {
    expect(drawdownTicks(-52.7)).toEqual([0, -20, -40, -60]);
    expect(drawdownTicks(-18.1)).toEqual([0, -5, -10, -15, -20]);
    expect(drawdownTicks(-28.4)).toEqual([0, -10, -20, -30]);
    expect(drawdownTicks(-83.7)).toEqual([0, -20, -40, -60, -80, -100]);
  });
});

describe("paths", () => {
  it("writes a polyline and closes an area to the baseline", () => {
    expect(linePath([])).toBe("");
    expect(
      linePath([
        [0, 1.006],
        [2, 3],
      ])
    ).toBe("M0 1.01L2 3");
    expect(
      areaPath(
        [
          [0, 5],
          [10, 2],
        ],
        20
      )
    ).toBe("M0 5L10 2L10 20L0 20Z");
  });

  it("spreads colliding labels apart without reordering them", () => {
    expect(spreadLabels([10, 12, 50], 8, 0, 100)).toEqual([7, 15, 50]);
    const spread = spreadLabels([98, 99, 30], 10, 0, 100);
    expect(spread[2]).toBe(30);
    expect(spread[1]).toBe(100);
    expect(spread[0]).toBe(90);
    expect(spreadLabels([], 5, 0, 1)).toEqual([]);
    expect(spreadLabels([40], 5, 0, 100)).toEqual([40]);
  });
});

describe("drawdowns", () => {
  // $100 up to $120, down to $60, back to $120: a 50% fall over four months, peak to recovery.
  const values = [100, 120, 90, 60, 100, 120, 130];
  const dates = ["2007-06", "2007-07", "2007-08", "2007-09", "2007-10", "2007-11", "2007-12"];

  it("measures the fall below the running peak", () => {
    const dd = drawdowns(values);
    expect(dd.slice(0, 4)).toEqual([0, 0, -25, -50]);
    expect(dd[4]).toBeCloseTo(-16.667, 3);
    expect(dd.slice(5)).toEqual([0, 0]);
    expect(drawdowns([5, 4, 3])).toEqual([0, -20, -40]);
    expect(drawdowns([])).toEqual([]);
  });

  it("finds the worst episode with its dates, dollars and months to recover", () => {
    const fall = worstFall({ values, dates }, 10000);
    expect(fall).not.toBeNull();
    expect(fall?.pct).toBe(-50);
    expect(fall?.peak).toBe("2007-07");
    expect(fall?.trough).toBe("2007-09");
    expect(fall?.recovered).toBe("2007-11");
    expect(fall?.monthsToRecover).toBe(4);
    expect(fall?.dollarsAtTrough).toBe(5000);
  });

  it("reports a fall that has not recovered", () => {
    const fall = worstFall({ values: [100, 80, 90], dates: ["2020-01", "2020-02", "2020-03"] });
    expect(fall?.recovered).toBeNull();
    expect(fall?.monthsToRecover).toBeNull();
    expect(fall?.dollarsAtTrough).toBe(8000);
  });

  it("returns null for a series that only rises", () => {
    expect(worstFall({ values: [1, 2, 3], dates: ["2020-01", "2020-02", "2020-03"] })).toBeNull();
  });

  it("agrees with the emitter's summary on a real-shaped fall", () => {
    // A peak of $28,000 in 2007-10 falling 52.7% and recovering 63 months later.
    const dates: string[] = [];
    const values: number[] = [];
    let level = 28000;
    for (let i = 0; i <= 70; i++) {
      const y = 2007 + Math.floor((9 + i) / 12);
      const m = ((9 + i) % 12) + 1;
      dates.push(`${y}-${String(m).padStart(2, "0")}`);
      if (i <= 16) level = 28000 * (1 - 0.527 * (i / 16));
      else if (i < 63) level = 28000 * 0.473 + (28000 * 0.527 * (i - 16)) / 47.5;
      else level = 28000 + i;
      values.push(level);
    }
    const fall = worstFall({ values, dates });
    expect(fall?.peak).toBe("2007-10");
    expect(fall?.trough).toBe("2009-02");
    expect(fall?.pct).toBeCloseTo(-52.7, 5);
    expect(fall?.recovered).toBe("2013-01");
    expect(fall?.monthsToRecover).toBe(63);
    expect(fall?.dollarsAtTrough).toBe(4730);
  });
});

describe("donut", () => {
  it("shares the ring by weight, clockwise from the top", () => {
    const arcs = donutArcs([50, 25, 25]);
    expect(arcs.map((a) => a.fraction)).toEqual([0.5, 0.25, 0.25]);
    expect(arcs[0]).toMatchObject({ start: 0, end: 180 });
    expect(arcs[2]).toMatchObject({ start: 270, end: 360 });
    expect(donutArcs([0, 0])).toEqual([]);
  });

  it("draws an arc and a full ring", () => {
    const quarter = arcPath(100, 100, 90, 60, 0, 90);
    expect(quarter.startsWith("M100 10")).toBe(true);
    expect(quarter).toContain("A90 90 0 0 1 190 100");
    expect(quarter).toContain("L160 100");
    expect(arcPath(100, 100, 90, 60, 0, 0)).toBe("");
    const full = arcPath(100, 100, 90, 60, 0, 360);
    expect(full.match(/M/g)?.length).toBe(2);
  });
});

describe("against the emitter", () => {
  // The Python emitter and this module compute the worst fall independently. They must
  // agree on every committed series, or a chart annotation would contradict the page.
  it("finds the same worst fall as the summary in every 1990 series", () => {
    for (const s of series1990.series) {
      const fall = worstFall(s, series1990.start);
      const expected = s.summary.worstFall;
      expect(fall, s.id).not.toBeNull();
      expect(fall?.pct, s.id).toBeCloseTo(expected.pct, 1);
      expect(fall?.peak, s.id).toBe(expected.peak);
      expect(fall?.trough, s.id).toBe(expected.trough);
      expect(fall?.recovered, s.id).toBe(expected.recovered);
      expect(fall?.monthsToRecover, s.id).toBe(expected.monthsToRecover);
      expect(Math.abs((fall?.dollarsAtTrough ?? 0) - expected.dollarsAtTrough), s.id).toBeLessThanOrEqual(1);
    }
  });
});
