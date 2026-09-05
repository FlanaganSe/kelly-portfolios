import { describe, expect, it } from "vitest";
import { feeOn10kText, feePercentText, weightedExpenseRatioBp } from "~/lib/fees";

const bp = (ticker: string): number => ({ CHEAP: 3, DEAR: 99 })[ticker] ?? Number.NaN;

describe("weightedExpenseRatioBp", () => {
  it("weights each fund's fee by its share of the money", () => {
    expect(
      weightedExpenseRatioBp(
        [
          { ticker: "CHEAP", weight: 50 },
          { ticker: "DEAR", weight: 50 },
        ],
        bp
      )
    ).toBe(51);
  });

  it("refuses holdings that do not sum to 100", () => {
    expect(() => weightedExpenseRatioBp([{ ticker: "CHEAP", weight: 99.9 }], bp)).toThrow(/not 100%/);
  });
});

describe("fee text", () => {
  it("rounds the percent to two places and the dollars on $10,000 to whole dollars", () => {
    expect(feePercentText(20.585)).toBe("0.21%");
    expect(feeOn10kText(20.585)).toBe("$21");
    expect(feePercentText(6)).toBe("0.06%");
    expect(feeOn10kText(6)).toBe("$6");
    expect(feePercentText(33.37)).toBe("0.33%");
    expect(feeOn10kText(9.37)).toBe("$9");
  });
});
