import { describe, expect, it } from "vitest";
import {
  defaultLabConfig,
  type LabConfig,
  normalise,
  parseHoldings,
  parseLabConfig,
  toBenchmark,
  toLabHref,
  toSearchParams,
  totalPercent,
} from "~/lib/lab/config";

describe("holdings in a link", () => {
  it("reads ticker and percent pairs", () => {
    expect(parseHoldings("VTI:20,AVLV:15")).toEqual([
      { ticker: "VTI", percent: 20 },
      { ticker: "AVLV", percent: 15 },
    ]);
  });

  it("upper-cases and trims what the reader pasted", () => {
    expect(parseHoldings(" vti :20 ")).toEqual([{ ticker: "VTI", percent: 20 }]);
  });

  it("sums a ticker that appears twice", () => {
    expect(parseHoldings("VTI:20,VTI:5")).toEqual([{ ticker: "VTI", percent: 25 }]);
  });

  it("drops an unreadable line rather than turning it into a zero position", () => {
    expect(parseHoldings("VTI:20,:30,ABC:,%%%:10,VEA:-5")).toEqual([{ ticker: "VTI", percent: 20 }]);
  });
});

describe("the whole configuration", () => {
  const config: LabConfig = {
    holdings: [
      { ticker: "VTI", percent: 60 },
      { ticker: "VEA", percent: 40 },
    ],
    benchmark: "own-counterfactual",
    edgeBp: 109,
    trackingErrorBp: 46,
    horizonYears: 10,
    seed: 42,
  };

  it("round-trips without loss", () => {
    expect(parseLabConfig(toSearchParams(config))).toEqual(config);
  });

  it("writes nothing but the holdings when everything else is default", () => {
    const plain = { ...defaultLabConfig, holdings: [{ ticker: "VTI", percent: 100 }] };
    expect(toSearchParams(plain).toString()).toBe("p=VTI%3A100");
    expect(toLabHref(defaultLabConfig)).toBe("/lab");
  });

  it("falls back per field rather than rejecting a damaged link", () => {
    const parsed = parseLabConfig("p=VTI:60&e=not-a-number&te=-5&h=900&s=&b=nonsense");
    expect(parsed.holdings).toEqual([{ ticker: "VTI", percent: 60 }]);
    expect(parsed.edgeBp).toBe(defaultLabConfig.edgeBp);
    expect(parsed.trackingErrorBp).toBe(defaultLabConfig.trackingErrorBp);
    expect(parsed.horizonYears).toBe(defaultLabConfig.horizonYears);
    expect(parsed.seed).toBe(defaultLabConfig.seed);
    expect(parsed.benchmark).toBe("cheap-index");
  });

  it("round-trips the third benchmark, which is a claim of its own", () => {
    expect(parseLabConfig("b=peer").benchmark).toBe("average-investor");
    expect(toSearchParams({ ...defaultLabConfig, benchmark: "average-investor" }).get("b")).toBe("peer");
  });

  it("keeps a negative edge, which is a real thing to want to see", () => {
    expect(parseLabConfig("e=-40").edgeBp).toBe(-40);
  });
});

describe("weights", () => {
  it("adds the percentages as typed", () => {
    expect(
      totalPercent([
        { ticker: "A", percent: 33.33 },
        { ticker: "B", percent: 66.67 },
      ])
    ).toBe(100);
  });

  it("normalises to exactly 100 and puts the rounding drift on the last line", () => {
    const scaled = normalise([
      { ticker: "A", percent: 1 },
      { ticker: "B", percent: 1 },
      { ticker: "C", percent: 1 },
    ]);
    expect(totalPercent(scaled)).toBe(100);
    expect(scaled[0]?.percent).toBeCloseTo(33.33, 10);
    expect(scaled[2]?.percent).toBeCloseTo(33.34, 10);
  });

  it("leaves an empty or zero portfolio alone rather than dividing by zero", () => {
    expect(normalise([])).toEqual([]);
    expect(normalise([{ ticker: "A", percent: 0 }])).toEqual([{ ticker: "A", percent: 0 }]);
  });
});

describe("weights too small to matter", () => {
  it("drops a weight that would round to zero rather than making it a real 0% line", () => {
    expect(parseHoldings("C:1e-30")).toEqual([]);
    expect(parseHoldings("C:0")).toEqual([{ ticker: "C", percent: 0 }]);
  });

  it("normalises a tiny portfolio instead of silently doing nothing", () => {
    expect(
      normalise([
        { ticker: "A", percent: 0.004 },
        { ticker: "B", percent: 0.004 },
      ])
    ).toEqual([
      { ticker: "A", percent: 50 },
      { ticker: "B", percent: 50 },
    ]);
  });
});

describe("narrowing a control's value", () => {
  it("accepts every benchmark the type holds and refuses anything else", () => {
    expect(toBenchmark("average-investor")).toBe("average-investor");
    expect(toBenchmark("own-counterfactual")).toBe("own-counterfactual");
    expect(toBenchmark("cheap-index")).toBe("cheap-index");
    expect(toBenchmark("something-else")).toBe(defaultLabConfig.benchmark);
  });
});
