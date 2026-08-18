import { describe, expect, it } from "vitest";
import { toMonthIndex } from "~/lib/backtest/calendar";
import { commonRange, seriesEnd, slice } from "~/lib/backtest/series";
import { InsufficientHistoryError, resolvableRange, simulate } from "~/lib/backtest/simulate";
import type { ReturnSeries } from "~/lib/backtest/types";

const JAN_2000 = toMonthIndex("2000-01");

function makeSeries(id: string, start: string, returns: readonly number[]): ReturnSeries {
  return { id, start: toMonthIndex(start), returns };
}

/** Every fixture below is short enough to check by hand. */
const flat = makeSeries("FLAT", "2000-01", [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
const doubleThenHalve = makeSeries("BOOM", "2000-01", [1, -0.5]);
const zero = makeSeries("ZERO", "2000-01", [0, 0]);
const late = makeSeries("LATE", "2000-03", [0.01, 0.01, 0.01]);

function seriesMap(...all: readonly ReturnSeries[]): Map<string, ReturnSeries> {
  return new Map(all.map((one) => [one.id, one]));
}

describe("series alignment", () => {
  it("reports the last month of a series", () => {
    expect(seriesEnd(late)).toBe(toMonthIndex("2000-05"));
  });

  it("takes the overlap of different inception dates", () => {
    expect(commonRange([flat, late])).toEqual({ start: toMonthIndex("2000-03"), end: toMonthIndex("2000-05") });
  });

  it("returns null when two series never coexisted", () => {
    const early = makeSeries("EARLY", "1990-01", [0, 0]);
    expect(commonRange([early, late])).toBeNull();
  });

  it("refuses to supply months it does not have rather than padding", () => {
    expect(() => slice(late, { start: JAN_2000, end: toMonthIndex("2000-05") })).toThrow(/cannot supply/);
  });
});

describe("simulate", () => {
  it("a single holding at 100% earns exactly the asset's return", () => {
    const result = simulate({
      allocations: [{ symbol: "BOOM", weight: 1 }],
      series: seriesMap(doubleThenHalve),
      rebalance: "monthly",
      applyExpenses: false,
    });
    expect(result.returns).toEqual([1, -0.5]);
    expect(result.growth[2]).toBeCloseTo(1, 12);
    expect(result.cashWeight).toBe(0);
  });

  it("two identical holdings behave as one", () => {
    const twin = { ...doubleThenHalve, id: "BOOM2" };
    const split = simulate({
      allocations: [
        { symbol: "BOOM", weight: 0.5 },
        { symbol: "BOOM2", weight: 0.5 },
      ],
      series: seriesMap(doubleThenHalve, twin),
      rebalance: "never",
      applyExpenses: false,
    });
    expect(split.returns[0]).toBeCloseTo(1, 12);
    expect(split.returns[1]).toBeCloseTo(-0.5, 12);
  });

  it("sums a duplicated symbol rather than rejecting it", () => {
    const result = simulate({
      allocations: [
        { symbol: "BOOM", weight: 0.3 },
        { symbol: "BOOM", weight: 0.2 },
        { symbol: "ZERO", weight: 0.5 },
      ],
      series: seriesMap(doubleThenHalve, zero),
      rebalance: "never",
      applyExpenses: false,
    });
    expect(result.weights.get("BOOM")).toBeCloseTo(0.5, 12);
    expect(result.cashWeight).toBeCloseTo(0, 12);
  });

  it("leaves the remainder in cash when the weights do not reach 100%", () => {
    // 50% in an asset that doubles, 50% left in cash earning nothing: +50%.
    const result = simulate({
      allocations: [{ symbol: "BOOM", weight: 0.5 }],
      series: seriesMap(doubleThenHalve),
      rebalance: "never",
      applyExpenses: false,
    });
    expect(result.cashWeight).toBeCloseTo(0.5, 12);
    expect(result.returns[0]).toBeCloseTo(0.5, 12);
  });

  it("treats weights above 100% as borrowing at the cash rate", () => {
    // 150% of an asset that doubles, funded by −50% cash at 0%: +150%.
    const result = simulate({
      allocations: [{ symbol: "BOOM", weight: 1.5 }],
      series: seriesMap(doubleThenHalve),
      rebalance: "never",
      applyExpenses: false,
    });
    expect(result.cashWeight).toBeCloseTo(-0.5, 12);
    expect(result.returns[0]).toBeCloseTo(1.5, 12);
  });

  it("rebalancing changes the answer, and monthly beats letting the winner ride here", () => {
    const allocations = [
      { symbol: "BOOM", weight: 0.5 },
      { symbol: "ZERO", weight: 0.5 },
    ];
    const series = seriesMap(doubleThenHalve, zero);
    const drifted = simulate({ allocations, series, rebalance: "never", applyExpenses: false });
    const reset = simulate({ allocations, series, rebalance: "monthly", applyExpenses: false });

    // Both earn +50% in January. Drifted then holds 0.75/0.25 and loses a third;
    // rebalanced holds 0.5/0.5 of 1.5 and loses a quarter.
    expect(drifted.returns[0]).toBeCloseTo(0.5, 12);
    expect(drifted.returns[1]).toBeCloseTo(-1 / 3, 12);
    expect(reset.returns[1]).toBeCloseTo(-0.25, 12);
  });

  it("anchors annual rebalancing to January rather than to the start of the test", () => {
    const twelve = Array.from({ length: 14 }, () => 0.01);
    const a = makeSeries("A", "2000-06", twelve);
    const b = makeSeries(
      "B",
      "2000-06",
      twelve.map(() => 0)
    );
    const result = simulate({
      allocations: [
        { symbol: "A", weight: 0.5 },
        { symbol: "B", weight: 0.5 },
      ],
      series: seriesMap(a, b),
      rebalance: "annually",
      applyExpenses: false,
    });
    // Seven months of drift to December, a reset in January, then drift again.
    // The reset shows up as the one month where the portfolio return steps back down.
    const january = 7;
    expect(result.returns[january]).toBeLessThan(result.returns[january - 1] ?? 0);
  });

  it("charges an expense ratio geometrically, so a year costs exactly the stated fee", () => {
    const result = simulate({
      allocations: [{ symbol: "FLAT", weight: 1, expenseRatio: 0.12 }],
      series: seriesMap(flat),
      rebalance: "never",
      applyExpenses: true,
    });
    expect(result.growth[12]).toBeCloseTo(0.88, 12);
    expect(result.effectiveExpenseRatio).toBeCloseTo(0.12, 12);
  });

  it("ignores the expense ratio when the test is run gross of fees", () => {
    const result = simulate({
      allocations: [{ symbol: "FLAT", weight: 1, expenseRatio: 0.12 }],
      series: seriesMap(flat),
      rebalance: "never",
      applyExpenses: false,
    });
    expect(result.growth[12]).toBeCloseTo(1, 12);
    expect(result.effectiveExpenseRatio).toBe(0);
  });

  it("uses the common history when inception dates differ", () => {
    const result = simulate({
      allocations: [
        { symbol: "FLAT", weight: 0.5 },
        { symbol: "LATE", weight: 0.5 },
      ],
      series: seriesMap(flat, late),
      rebalance: "monthly",
      applyExpenses: false,
    });
    expect(result.range).toEqual({ start: toMonthIndex("2000-03"), end: toMonthIndex("2000-05") });
    expect(result.returns).toHaveLength(3);
  });

  it("names the symbol that is short when a window is asked for that it cannot cover", () => {
    expect(() =>
      simulate({
        allocations: [{ symbol: "LATE", weight: 1 }],
        series: seriesMap(late),
        rebalance: "monthly",
        applyExpenses: false,
        range: { start: JAN_2000, end: toMonthIndex("2000-05") },
      })
    ).toThrow(InsufficientHistoryError);
  });

  it("names a symbol it has no series for at all", () => {
    try {
      simulate({
        allocations: [{ symbol: "NOPE", weight: 1 }],
        series: seriesMap(flat),
        rebalance: "monthly",
        applyExpenses: false,
      });
      throw new Error("expected the simulation to refuse");
    } catch (error) {
      expect(error).toBeInstanceOf(InsufficientHistoryError);
      expect((error as InsufficientHistoryError).missing[0]).toEqual({ symbol: "NOPE", absent: true });
    }
  });

  it("refuses an empty portfolio rather than reporting a flat line", () => {
    expect(() =>
      simulate({ allocations: [], series: seriesMap(flat), rebalance: "monthly", applyExpenses: false })
    ).toThrow(InsufficientHistoryError);
  });

  it("ignores a zero-weight line when working out what can be tested", () => {
    const range = resolvableRange({
      allocations: [
        { symbol: "FLAT", weight: 1 },
        { symbol: "LATE", weight: 0 },
      ],
      series: seriesMap(flat, late),
    });
    expect(range).toEqual({ start: JAN_2000, end: toMonthIndex("2000-12") });
  });

  it("pays the cash rate on the unallocated remainder when one is supplied", () => {
    const cash = makeSeries("CASH", "2000-01", [0.01, 0.01]);
    const result = simulate({
      allocations: [{ symbol: "ZERO", weight: 0.5 }],
      series: seriesMap(zero),
      rebalance: "never",
      applyExpenses: false,
      cashSeries: cash,
    });
    expect(result.returns[0]).toBeCloseTo(0.005, 12);
  });
});
