import { describe, expect, it } from "vitest";
import { monthOfYear, toMonthIndex, toYearMonth, yearOf } from "~/lib/backtest/calendar";

describe("month arithmetic", () => {
  it("counts from January 1970", () => {
    expect(toMonthIndex("1970-01")).toBe(0);
    expect(toMonthIndex("1971-01")).toBe(12);
    expect(toMonthIndex("2000-03")).toBe(362);
  });

  it("round-trips", () => {
    for (const month of ["1926-07", "1970-01", "2000-12", "2026-08"]) {
      expect(toYearMonth(toMonthIndex(month))).toBe(month);
    }
  });

  it("handles months before the epoch", () => {
    expect(toMonthIndex("1969-12")).toBe(-1);
    expect(toYearMonth(-1)).toBe("1969-12");
    expect(yearOf(-1)).toBe(1969);
    expect(monthOfYear(-1)).toBe(11);
  });

  it("refuses anything that is not YYYY-MM", () => {
    expect(() => toMonthIndex("2000-1")).toThrow(/YYYY-MM/);
    expect(() => toMonthIndex("2000-13")).toThrow(/out of range/);
  });
});
