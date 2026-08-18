import { describe, expect, it } from "vitest";
import { toMonthIndex, toYearMonth } from "~/lib/backtest/calendar";
import { type ImportProblem, importReturns } from "~/lib/lab/importReturns";

function kinds(problems: readonly ImportProblem[]): string[] {
  return problems.map((one) => one.kind);
}

function byTicker(result: ReturnType<typeof importReturns>, ticker: string) {
  return result.series.find((one) => one.id === ticker);
}

describe("importReturns", () => {
  describe("nothing to read", () => {
    it("reports an empty paste rather than an empty success", () => {
      const result = importReturns("");
      expect(result.series).toEqual([]);
      expect(kinds(result.problems)).toEqual(["empty-paste"]);
    });

    it("treats whitespace as an empty paste", () => {
      expect(kinds(importReturns("  \n\n \t \n").problems)).toEqual(["empty-paste"]);
    });

    it("reports a header with no months under it", () => {
      const result = importReturns("Month,VTI\n");
      expect(result.series).toEqual([]);
      expect(kinds(result.problems)).toEqual(["no-rows"]);
    });

    it("refuses a paste whose first row is already data", () => {
      const result = importReturns("2020-01,0.01\n2020-02,0.02");
      expect(result.series).toEqual([]);
      expect(kinds(result.problems)).toEqual(["missing-header"]);
      expect(result.problems[0]?.message).toContain("2020-01");
    });

    it("reports a header with a month column and nothing else", () => {
      expect(kinds(importReturns("Month\n2020-01").problems)).toEqual(["no-tickers"]);
    });
  });

  describe("one ticker", () => {
    it("reads decimals as they are written", () => {
      const result = importReturns("Month,VTI\n2020-01,0.01\n2020-02,-0.02\n2020-03,0");
      expect(result.problems).toEqual([]);
      expect(result.series).toHaveLength(1);
      expect(result.series[0]).toEqual({ id: "VTI", start: toMonthIndex("2020-01"), returns: [0.01, -0.02, 0] });
    });

    it("accepts YYYY-MM-DD and keeps only the month", () => {
      const result = importReturns("Date,VTI\n2020-01-31,0.01\n2020-02-29,0.02");
      expect(result.problems).toEqual([]);
      expect(result.series[0]?.start).toBe(toMonthIndex("2020-01"));
      expect(result.series[0]?.returns).toEqual([0.01, 0.02]);
    });

    it("sorts rows pasted out of order", () => {
      const result = importReturns("Month,VTI\n2020-03,0.03\n2020-01,0.01\n2020-02,0.02");
      expect(result.problems).toEqual([]);
      expect(result.series[0]?.start).toBe(toMonthIndex("2020-01"));
      expect(result.series[0]?.returns).toEqual([0.01, 0.02, 0.03]);
    });
  });

  describe("percent and decimal", () => {
    it("converts a column marked with a percent sign, and leaves its neighbour alone", () => {
      const result = importReturns("Month,PCT,DEC\n2020-01,1.23%,0.0123\n2020-02,-2%,-0.02");
      expect(result.problems).toEqual([]);
      const percent = byTicker(result, "PCT");
      const decimal = byTicker(result, "DEC");
      expect(percent?.returns[0]).toBeCloseTo(0.0123, 12);
      expect(percent?.returns[1]).toBeCloseTo(-0.02, 12);
      expect(decimal?.returns).toEqual([0.0123, -0.02]);
    });

    it("marks the whole column from a single sign, wherever in the column it appears", () => {
      const result = importReturns("Month,PCT\n2020-01,1.5\n2020-02,2.5%");
      expect(result.problems).toEqual([]);
      expect(result.series[0]?.returns[0]).toBeCloseTo(0.015, 12);
      expect(result.series[0]?.returns[1]).toBeCloseTo(0.025, 12);
    });

    it("never guesses percent from magnitude", () => {
      // 1.5 without a sign is +150% for the month. Absurd, and not this parser's call.
      const result = importReturns("Month,BIG\n2020-01,1.5\n2020-02,2.5");
      expect(result.series[0]?.returns).toEqual([1.5, 2.5]);
    });
  });

  describe("blanks", () => {
    it("trims leading and trailing blanks into a shorter series", () => {
      const result = importReturns("Month,A,B\n2020-01,,0.01\n2020-02,0.02,0.02\n2020-03,0.03,\n2020-04,0.04,");
      expect(result.problems).toEqual([]);
      expect(byTicker(result, "A")).toEqual({ id: "A", start: toMonthIndex("2020-02"), returns: [0.02, 0.03, 0.04] });
      expect(byTicker(result, "B")).toEqual({ id: "B", start: toMonthIndex("2020-01"), returns: [0.01, 0.02] });
    });

    it("does not read a blank as a zero", () => {
      const result = importReturns("Month,A\n2020-01,0.01\n2020-02,\n2020-03,0.03");
      expect(result.series).toEqual([]);
      expect(result.problems[0]?.kind).toBe("gap");
    });

    it("reports a column with a heading and no values at all", () => {
      const result = importReturns("Month,A,B\n2020-01,0.01,\n2020-02,0.02,");
      expect(byTicker(result, "A")?.returns).toEqual([0.01, 0.02]);
      expect(kinds(result.problems)).toEqual(["empty-column"]);
      expect(result.problems[0]?.ticker).toBe("B");
    });
  });

  describe("gaps", () => {
    it("refuses a gap, names the ticker and the month, and imports everything else", () => {
      const text = "Month,GAPPY,FINE\n2020-01,0.01,0.05\n2020-02,,0.06\n2020-03,0.03,0.07";
      const result = importReturns(text);
      expect(result.series.map((one) => one.id)).toEqual(["FINE"]);
      expect(byTicker(result, "FINE")?.returns).toEqual([0.05, 0.06, 0.07]);

      const gap = result.problems[0];
      expect(gap?.kind).toBe("gap");
      expect(gap?.ticker).toBe("GAPPY");
      expect(gap?.month).toBe("2020-02");
      expect(gap?.message).toContain("GAPPY");
      expect(gap?.message).toContain("2020-02");
    });

    it("names the first missing month and counts the rest", () => {
      const result = importReturns("Month,A\n2020-01,0.01\n2020-05,0.05\n2020-06,0.06");
      expect(result.problems[0]?.month).toBe("2020-02");
      expect(result.problems[0]?.message).toContain("3 months are missing");
    });

    it("counts a gap across a year boundary", () => {
      const result = importReturns("Month,A\n2019-12,0.01\n2020-02,0.02");
      expect(result.problems[0]?.month).toBe(toYearMonth(toMonthIndex("2020-01")));
    });
  });

  describe("duplicates", () => {
    it("refuses two values for one ticker in one month and keeps the other tickers", () => {
      const result = importReturns("Month,DUP,FINE\n2020-01,0.01,0.05\n2020-01,0.02,\n2020-02,0.02,0.06");
      expect(result.series.map((one) => one.id)).toEqual(["FINE"]);
      const problem = result.problems[0];
      expect(problem?.kind).toBe("duplicate-month");
      expect(problem?.ticker).toBe("DUP");
      expect(problem?.month).toBe("2020-01");
    });

    it("does not call a repeated month a duplicate when the second cell is blank", () => {
      const result = importReturns("Month,A\n2020-01,0.01\n2020-01,\n2020-02,0.02");
      expect(result.problems).toEqual([]);
      expect(result.series[0]?.returns).toEqual([0.01, 0.02]);
    });

    it("reads only the first column of a repeated heading", () => {
      const result = importReturns("Month,A,A\n2020-01,0.01,0.09\n2020-02,0.02,0.09");
      expect(result.series).toHaveLength(1);
      expect(result.series[0]?.returns).toEqual([0.01, 0.02]);
      expect(kinds(result.problems)).toEqual(["duplicate-column"]);
    });

    it("skips a column with no heading", () => {
      const result = importReturns("Month,,B\n2020-01,0.01,0.02\n2020-02,0.01,0.02");
      expect(result.series.map((one) => one.id)).toEqual(["B"]);
      expect(kinds(result.problems)).toEqual(["unnamed-column"]);
    });
  });

  describe("bad cells and bad rows", () => {
    it("refuses a non-numeric value, naming the ticker and the month", () => {
      const result = importReturns("Month,A,B\n2020-01,n/a,0.02\n2020-02,0.01,0.02");
      expect(result.series.map((one) => one.id)).toEqual(["B"]);
      const problem = result.problems[0];
      expect(problem?.kind).toBe("bad-value");
      expect(problem?.ticker).toBe("A");
      expect(problem?.month).toBe("2020-01");
    });

    it("refuses a thousands separator rather than guessing what the comma means", () => {
      const result = importReturns('Month,A\n2020-01,"1,23"\n2020-02,0.02');
      expect(result.series).toEqual([]);
      expect(result.problems[0]?.kind).toBe("bad-value");
    });

    it("skips a line whose first cell is not a month", () => {
      const result = importReturns("Month,A\n2020-01,0.01\ntotal,0.99\n2020-02,0.02");
      expect(result.series[0]?.returns).toEqual([0.01, 0.02]);
      const problem = result.problems.find((one) => one.kind === "bad-date");
      expect(problem?.line).toBe(3);
    });

    it("rejects an impossible month number", () => {
      const result = importReturns("Month,A\n2020-13,0.01\n2020-01,0.02");
      expect(kinds(result.problems)).toContain("bad-date");
      expect(result.series[0]?.returns).toEqual([0.02]);
    });

    it("ignores cells past the end of the header row and says so", () => {
      const result = importReturns("Month,A\n2020-01,0.01,0.99\n2020-02,0.02");
      expect(result.series[0]?.returns).toEqual([0.01, 0.02]);
      expect(kinds(result.problems)).toEqual(["extra-cells"]);
    });

    it("treats a short row as blanks, not as zeros", () => {
      const result = importReturns("Month,A,B\n2020-01,0.01,0.02\n2020-02,0.01");
      expect(byTicker(result, "A")?.returns).toEqual([0.01, 0.01]);
      expect(byTicker(result, "B")?.returns).toEqual([0.02]);
    });

    it("never throws, whatever is pasted", () => {
      for (const nonsense of ['"""""', " ", "----", ",,,,\n,,,,", "Month,A\n2020-01,0.01\n "]) {
        expect(() => importReturns(nonsense)).not.toThrow();
      }
    });
  });

  describe("dirty text", () => {
    it("handles a UTF-8 BOM, CRLF line endings, quoted fields and stray whitespace", () => {
      const text = '﻿"Month" , "VTI" ,"AVUV"\r\n 2020-01 , 0.01 , "0.05"\r\n2020-02,0.02,0.06\r\n';
      const result = importReturns(text);
      expect(result.problems).toEqual([]);
      expect(result.series.map((one) => one.id)).toEqual(["VTI", "AVUV"]);
      expect(byTicker(result, "AVUV")?.returns).toEqual([0.05, 0.06]);
    });

    it("reads tab-separated text", () => {
      const result = importReturns("Month\tVTI\tAVUV\n2020-01\t0.01\t0.05\n2020-02\t0.02\t0.06");
      expect(result.problems).toEqual([]);
      expect(result.series.map((one) => one.id)).toEqual(["VTI", "AVUV"]);
    });

    it("keeps a comma inside a quoted heading out of the column count", () => {
      const result = importReturns('Month,"VTI, total market"\n2020-01,0.01\n2020-02,0.02');
      expect(result.series.map((one) => one.id)).toEqual(["VTI, total market"]);
    });

    it("skips blank lines between rows", () => {
      const result = importReturns("Month,A\n\n2020-01,0.01\n\n\n2020-02,0.02\n");
      expect(result.problems).toEqual([]);
      expect(result.series[0]?.returns).toEqual([0.01, 0.02]);
    });
  });

  describe("many tickers", () => {
    it("imports ten columns in header order", () => {
      const tickers = ["VTI", "AVUV", "AVDV", "VXUS", "BND", "VNQ", "IAU", "DBMF", "VTV", "VBR"];
      const months = ["2020-01", "2020-02", "2020-03"];
      const header = `Month,${tickers.join(",")}`;
      const rows = months.map(
        (month, row) => `${month},${tickers.map((_, column) => ((row + 1) / 100 + column / 1000).toFixed(4)).join(",")}`
      );
      const result = importReturns([header, ...rows].join("\n"));

      expect(result.problems).toEqual([]);
      expect(result.series.map((one) => one.id)).toEqual(tickers);
      expect(result.series.every((one) => one.returns.length === 3)).toBe(true);
      expect(byTicker(result, "VBR")?.returns).toEqual([0.019, 0.029, 0.039]);
    });
  });
});
