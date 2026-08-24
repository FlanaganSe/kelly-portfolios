import { describe, expect, it } from "vitest";
import { clamp, decimalsOf, formatNumber, formatYears, parseNumber, roundTo, snapToStep } from "~/lib/format";

describe("clamp", () => {
  it("passes a value already inside the range through untouched", () => {
    expect(clamp(5, 0, 10)).toBe(5);
  });

  it("pins to each bound", () => {
    expect(clamp(-3, 0, 10)).toBe(0);
    expect(clamp(42, 0, 10)).toBe(10);
  });

  it("falls back to the lower bound for NaN and inverted ranges", () => {
    expect(clamp(Number.NaN, 2, 8)).toBe(2);
    expect(clamp(5, 10, 0)).toBe(10);
  });
});

describe("roundTo", () => {
  it("removes float dust", () => {
    expect(roundTo(0.1 + 0.2, 2)).toBe(0.3);
  });

  it("leaves non-finite values alone", () => {
    expect(roundTo(Number.POSITIVE_INFINITY, 2)).toBe(Number.POSITIVE_INFINITY);
  });
});

describe("decimalsOf", () => {
  it("reads the decimals a step implies", () => {
    expect(decimalsOf(1)).toBe(0);
    expect(decimalsOf(0.25)).toBe(2);
    expect(decimalsOf(0.001)).toBe(3);
  });
});

describe("snapToStep", () => {
  it("snaps to the nearest step and keeps the step's precision", () => {
    expect(snapToStep(0.37, 0.25)).toBe(0.25);
    expect(snapToStep(0.4, 0.25)).toBe(0.5);
  });

  it("returns the value unchanged for a non-positive step", () => {
    expect(snapToStep(1.234, 0)).toBe(1.234);
  });
});

describe("parseNumber", () => {
  it("accepts separators, a leading plus and a trailing percent", () => {
    expect(parseNumber(" 1,250 ")).toBe(1250);
    expect(parseNumber("+7.33")).toBe(7.33);
    expect(parseNumber("24%")).toBe(24);
  });

  it("rejects partial and non-numeric input", () => {
    expect(parseNumber("")).toBeNull();
    expect(parseNumber("-")).toBeNull();
    expect(parseNumber("abc")).toBeNull();
  });
});

describe("formatNumber", () => {
  it("fixes the decimals", () => {
    expect(formatNumber(1.005, 2)).toBe("1.00");
    expect(formatNumber(7, 0)).toBe("7");
  });

  it("shows an em dash for a non-finite value", () => {
    expect(formatNumber(Number.NaN)).toBe("—");
  });
});

describe("formatYears", () => {
  it("uses days under two months", () => {
    expect(formatYears(0.065687)).toBe("24 days");
    expect(formatYears(1 / 365.25)).toBe("1 day");
  });

  it("uses months under two years", () => {
    expect(formatYears(0.29249)).toBe("3.5 months");
    expect(formatYears(1)).toBe("12 months");
  });

  it("uses years with one decimal up to a century", () => {
    expect(formatYears(12.216)).toBe("12.2 years");
    expect(formatYears(105.1)).toBe("105 years");
  });

  it("stops pretending to precision past a century", () => {
    expect(formatYears(5517.9)).toBe("5,500 years");
  });

  it("refuses a negative or non-finite wait", () => {
    expect(() => formatYears(-1)).toThrow(RangeError);
    expect(() => formatYears(Number.NaN)).toThrow(RangeError);
  });
});
