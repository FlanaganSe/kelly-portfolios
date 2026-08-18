import { describe, expect, it } from "vitest";
import { toMonthIndex } from "~/lib/backtest/calendar";
import {
  defaultLabConfig,
  type LabConfig,
  normalise,
  parseHoldings,
  parseLabConfig,
  requestedRange,
  toAllocations,
  toLabHref,
  toSearchParams,
  totalPercent,
} from "~/lib/lab/config";

describe("holdings in a link", () => {
  it("reads symbol and percent pairs", () => {
    expect(parseHoldings("VTI:20,AVLV:15")).toEqual([
      { symbol: "VTI", percent: 20 },
      { symbol: "AVLV", percent: 15 },
    ]);
  });

  it("upper-cases and trims what the reader pasted", () => {
    expect(parseHoldings(" vti :20 ")).toEqual([{ symbol: "VTI", percent: 20 }]);
  });

  it("sums a symbol that appears twice", () => {
    expect(parseHoldings("VTI:20,VTI:5")).toEqual([{ symbol: "VTI", percent: 25 }]);
  });

  it("drops an unreadable line rather than turning it into a zero position", () => {
    expect(parseHoldings("VTI:20,:30,ABC:,%%%:10,VEA:-5")).toEqual([{ symbol: "VTI", percent: 20 }]);
  });
});

describe("the whole configuration", () => {
  const config: LabConfig = {
    holdings: [
      { symbol: "VTI", percent: 60 },
      { symbol: "VEA", percent: 40 },
    ],
    benchmark: "VTI",
    rebalance: "quarterly",
    applyExpenses: false,
    from: "2015-01",
    to: "2024-12",
    initial: 25_000,
  };

  it("round-trips without loss", () => {
    expect(parseLabConfig(toSearchParams(config))).toEqual(config);
  });

  it("writes nothing but the holdings when everything else is default", () => {
    const plain = { ...defaultLabConfig, holdings: [{ symbol: "VTI", percent: 100 }] };
    expect(toSearchParams(plain).toString()).toBe("p=VTI%3A100");
    expect(toLabHref(defaultLabConfig)).toBe("/lab");
  });

  it("falls back per field rather than rejecting a damaged link", () => {
    const parsed = parseLabConfig("p=VTI:60&r=fortnightly&b=&from=2015-13&v=-4");
    expect(parsed.holdings).toEqual([{ symbol: "VTI", percent: 60 }]);
    expect(parsed.rebalance).toBe(defaultLabConfig.rebalance);
    expect(parsed.benchmark).toBe(defaultLabConfig.benchmark);
    expect(parsed.from).toBeNull();
    expect(parsed.initial).toBe(defaultLabConfig.initial);
  });

  it("charges fees unless the link explicitly turns them off", () => {
    expect(parseLabConfig("").applyExpenses).toBe(true);
    expect(parseLabConfig("f=0").applyExpenses).toBe(false);
  });
});

describe("weights", () => {
  it("adds the percentages as typed", () => {
    expect(
      totalPercent([
        { symbol: "A", percent: 33.33 },
        { symbol: "B", percent: 66.67 },
      ])
    ).toBe(100);
  });

  it("normalises to exactly 100 and puts the rounding drift on the last line", () => {
    const scaled = normalise([
      { symbol: "A", percent: 1 },
      { symbol: "B", percent: 1 },
      { symbol: "C", percent: 1 },
    ]);
    expect(totalPercent(scaled)).toBe(100);
    expect(scaled[0]?.percent).toBeCloseTo(33.33, 10);
    expect(scaled[2]?.percent).toBeCloseTo(33.34, 10);
  });

  it("leaves an empty or zero portfolio alone rather than dividing by zero", () => {
    expect(normalise([])).toEqual([]);
    expect(normalise([{ symbol: "A", percent: 0 }])).toEqual([{ symbol: "A", percent: 0 }]);
  });

  it("converts percentages to the fractions the engine takes", () => {
    const allocations = toAllocations([{ symbol: "VTI", percent: 60 }], (symbol) =>
      symbol === "VTI" ? 0.0003 : undefined
    );
    expect(allocations).toEqual([{ symbol: "VTI", weight: 0.6, expenseRatio: 0.0003 }]);
  });
});

describe("the requested window", () => {
  const available = { start: toMonthIndex("2010-01"), end: toMonthIndex("2026-06") };

  it("clips to what the data supplies", () => {
    const config = { ...defaultLabConfig, from: "1990-01", to: "2030-01" };
    expect(requestedRange(config, available)).toEqual(available);
  });

  it("honours a window inside the data", () => {
    const config = { ...defaultLabConfig, from: "2015-01", to: "2020-12" };
    expect(requestedRange(config, available)).toEqual({
      start: toMonthIndex("2015-01"),
      end: toMonthIndex("2020-12"),
    });
  });

  it("falls back to the whole window when the dates cross", () => {
    const config = { ...defaultLabConfig, from: "2020-01", to: "2015-01" };
    expect(requestedRange(config, available)).toEqual(available);
  });
});
