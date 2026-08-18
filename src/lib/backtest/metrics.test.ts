import { describe, expect, it } from "vitest";
import { toMonthIndex } from "~/lib/backtest/calendar";
import {
  annualisedVolatility,
  beta,
  cagr,
  calendarYears,
  correlation,
  drawdownPath,
  fractionAhead,
  growthPath,
  informationRatio,
  maxDrawdown,
  rollingExcess,
  sharpeRatio,
  sortinoRatio,
  standardDeviation,
  totalReturn,
  trackingError,
} from "~/lib/backtest/metrics";

const onePercentForAYear = Array.from({ length: 12 }, () => 0.01);

describe("compounding", () => {
  it("compounds a total return rather than adding it", () => {
    expect(totalReturn([0.1, 0.1])).toBeCloseTo(0.21, 12);
  });

  it("annualises twelve months of 1% to 1.01^12 − 1", () => {
    expect(cagr(onePercentForAYear)).toBeCloseTo(1.01 ** 12 - 1, 12);
  });

  it("annualises a six-month window rather than reporting it raw", () => {
    expect(cagr([0.1, 0, 0, 0, 0, 0])).toBeCloseTo(1.1 ** 2 - 1, 12);
  });

  it("reports −100% for a portfolio that reached zero instead of a root of a negative", () => {
    expect(cagr([-1, 0.5])).toBe(-1);
  });

  it("has no growth rate for an empty window", () => {
    expect(Number.isNaN(cagr([]))).toBe(true);
  });
});

describe("dispersion", () => {
  it("uses the sample standard deviation", () => {
    // Deviations ±0.01 about a zero mean, divided by n − 1 = 1.
    expect(standardDeviation([0.01, -0.01])).toBeCloseTo(Math.sqrt(0.0002), 12);
  });

  it("annualises monthly volatility by √12", () => {
    expect(annualisedVolatility([0.01, -0.01])).toBeCloseTo(Math.sqrt(0.0002) * Math.sqrt(12), 12);
  });

  it("has no dispersion below two observations", () => {
    expect(Number.isNaN(standardDeviation([0.01]))).toBe(true);
  });
});

describe("drawdown", () => {
  it("measures the fall from the running peak", () => {
    // 1 → 1.5 → 0.75 → 0.9. The peak is 1.5 and the trough is half of it.
    const worst = maxDrawdown([0.5, -0.5, 0.2]);
    expect(worst.depth).toBeCloseTo(-0.5, 12);
    expect(worst.peakIndex).toBe(1);
    expect(worst.troughIndex).toBe(2);
    expect(worst.recoveryIndex).toBeNull();
  });

  it("records the month the previous peak was regained", () => {
    const worst = maxDrawdown([-0.5, 1]);
    expect(worst.depth).toBeCloseTo(-0.5, 12);
    expect(worst.recoveryIndex).toBe(2);
  });

  it("is zero for a series that never falls", () => {
    expect(maxDrawdown(onePercentForAYear).depth).toBe(0);
  });

  it("tracks the whole underwater path", () => {
    expect(drawdownPath([0.5, -0.5])).toEqual([0, 0, -0.5]);
  });

  it("grows one unit month by month", () => {
    expect(growthPath([1, -0.5])).toEqual([1, 2, 1]);
  });
});

describe("risk-adjusted return", () => {
  it("annualises the arithmetic mean of excess returns over annualised volatility", () => {
    // Excess: +1%, −1%, +3%, +1%. Mean 1%, sample sd 0.0163299.
    const ratio = sharpeRatio([0.02, 0, 0.04, 0.02], 0.01);
    expect(ratio).toBeCloseTo((0.01 * 12) / (Math.sqrt(0.0008 / 3) * Math.sqrt(12)), 10);
  });

  it("accepts a monthly risk-free series as well as a constant", () => {
    const constant = sharpeRatio([0.02, 0, 0.04, 0.02], 0.01);
    const series = sharpeRatio([0.02, 0, 0.04, 0.02], [0.01, 0.01, 0.01, 0.01]);
    expect(series).toBeCloseTo(constant ?? 0, 12);
  });

  it("returns null rather than dividing by a zero volatility", () => {
    expect(sharpeRatio([0.01, 0.01], 0.01)).toBeNull();
  });

  it("divides downside deviation by every observation, not only the losing ones", () => {
    // One −1% shortfall in two months: √(0.0001 / 2) × √12.
    expect(sortinoRatio([0.03, -0.01])).toBeCloseTo((0.01 * 12) / (Math.sqrt(0.0001 / 2) * Math.sqrt(12)), 10);
  });

  it("has no Sortino for a series that never falls below the minimum", () => {
    expect(sortinoRatio([0.01, 0.02])).toBeNull();
  });
});

describe("against a benchmark", () => {
  const benchmark = [0.02, -0.01, 0.03, 0];

  it("is perfectly correlated with an affine transformation of itself", () => {
    expect(
      correlation(
        benchmark,
        benchmark.map((one) => 2 * one + 1)
      )
    ).toBeCloseTo(1, 12);
    expect(
      correlation(
        benchmark,
        benchmark.map((one) => -one)
      )
    ).toBeCloseTo(-1, 12);
  });

  it("reads a doubled series as a beta of two", () => {
    expect(
      beta(
        benchmark.map((one) => 2 * one),
        benchmark
      )
    ).toBeCloseTo(2, 12);
  });

  it("has no tracking error against itself", () => {
    expect(trackingError(benchmark, benchmark)).toBeCloseTo(0, 12);
    expect(informationRatio(benchmark, benchmark)).toBeNull();
  });

  it("annualises the dispersion of the difference", () => {
    const portfolio = benchmark.map((one, index) => one + (index % 2 === 0 ? 0.01 : -0.01));
    expect(trackingError(portfolio, benchmark)).toBeCloseTo(0.01 * Math.sqrt(12) * Math.sqrt(4 / 3), 10);
  });

  it("refuses a mismatched benchmark rather than truncating it", () => {
    expect(trackingError([0.01, 0.02], [0.01])).toBeNull();
    expect(beta([0.01, 0.02], [0.01])).toBeNull();
    expect(correlation([0.01, 0.02], [0.01])).toBeNull();
  });
});

describe("calendar years", () => {
  it("labels a part-year as incomplete", () => {
    const years = calendarYears([0.01, 0.01, 0.01], toMonthIndex("2000-11"));
    expect(years.map((one) => [one.year, one.complete])).toEqual([
      [2000, false],
      [2001, false],
    ]);
    expect(years[0]?.portfolio).toBeCloseTo(1.01 ** 2 - 1, 12);
  });

  it("marks a full January-to-December year complete", () => {
    const years = calendarYears(onePercentForAYear, toMonthIndex("2000-01"));
    expect(years).toHaveLength(1);
    expect(years[0]?.complete).toBe(true);
    expect(years[0]?.benchmark).toBeNull();
  });

  it("carries the benchmark's year alongside the portfolio's", () => {
    const years = calendarYears(
      onePercentForAYear,
      toMonthIndex("2000-01"),
      onePercentForAYear.map(() => 0)
    );
    expect(years[0]?.benchmark).toBeCloseTo(0, 12);
  });
});

describe("rolling windows", () => {
  const portfolio = Array.from({ length: 24 }, () => 0.01);
  const benchmark = Array.from({ length: 24 }, () => 0.005);

  it("produces one window per start month that fits", () => {
    const windows = rollingExcess(portfolio, benchmark, toMonthIndex("2000-01"), 12);
    expect(windows).toHaveLength(13);
    expect(windows[0]?.endMonth).toBe(toMonthIndex("2000-12"));
    expect(windows[0]?.excess).toBeCloseTo(1.01 ** 12 - 1.005 ** 12, 12);
  });

  it("returns nothing when the window is longer than the history", () => {
    expect(rollingExcess([0.01], [0.01], 0, 12)).toEqual([]);
  });

  it("counts the share of windows finishing ahead", () => {
    const windows = rollingExcess(portfolio, benchmark, toMonthIndex("2000-01"), 12);
    expect(fractionAhead(windows)).toBe(1);
    expect(fractionAhead([])).toBeNull();
  });
});

describe("a series that never falls", () => {
  it("has no recovery month, rather than reporting month zero", () => {
    expect(maxDrawdown([0.01, 0.01]).recoveryIndex).toBeNull();
    expect(maxDrawdown([]).recoveryIndex).toBeNull();
  });
});
