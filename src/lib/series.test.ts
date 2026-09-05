import { describe, expect, it } from "vitest";
import { PORTFOLIOS } from "~/content/portfolios";
import raw1929 from "~/content/series/portfolios-1929.json";
import raw1990 from "~/content/series/portfolios-1990.json";
import { fundByTicker } from "~/content/shelf";
import { feeOn10kText, feePercentText, weightedExpenseRatioBp } from "~/lib/fees";
import { formatSignedPercent } from "~/lib/format";
import { loadSeries, parseSeriesFile, portfolioSummary, SERIES_IDS, seriesFor } from "~/lib/series";

const WINDOWS = ["1990", "1929"] as const;

describe("the emitted files parse", () => {
  it("accepts both files and reads their windows", () => {
    expect(parseSeriesFile(raw1990).window).toEqual({
      start: "1990-11",
      end: "2026-05",
      months: 427,
      label: "1990 to 2026",
    });
    expect(parseSeriesFile(raw1929).window).toEqual({
      start: "1929-01",
      end: "2025-05",
      months: 1157,
      label: "1929 to 2025",
    });
  });

  it("gives every series one value and one date per month plus the base month", () => {
    for (const window of WINDOWS) {
      const file = loadSeries(window);
      for (const s of file.series) {
        expect(s.values).toHaveLength(file.window.months + 1);
        expect(s.dates).toHaveLength(file.window.months + 1);
        expect(s.values[0]).toBe(10000);
        expect(s.dates[1]).toBe(file.window.start);
        expect(s.dates.at(-1)).toBe(file.window.end);
      }
    }
  });

  it("rejects a file whose summary disagrees with its values", () => {
    const broken = structuredClone(raw1990) as { series: { summary: { final: number } }[] };
    const first = broken.series[0];
    if (first === undefined) throw new Error("no series");
    first.summary.final += 1;
    expect(() => parseSeriesFile(broken)).toThrow(/summary.final/);
  });

  it("says in plain words what is simulated", () => {
    for (const window of WINDOWS) {
      const basis = loadSeries(window).basis;
      expect(basis).toMatch(/simulated/);
      expect(basis).toMatch(/not the records of real funds/);
      expect(basis).toMatch(/before trading costs/);
      expect(basis).toMatch(/RSST.*September 2023/);
      expect(basis).toMatch(/ten-year US government bond/);
    }
  });
});

describe("the printed weights are the scored weights", () => {
  it("sums each portfolio's holdings to 100", () => {
    for (const p of PORTFOLIOS) {
      const total = p.holdings.reduce((sum, h) => sum + h.weight, 0);
      expect(total).toBeCloseTo(100, 9);
    }
  });

  it("matches portfolios.ts to the 1990 series, ticker by ticker", () => {
    for (const p of PORTFOLIOS) {
      const printed = Object.fromEntries(p.holdings.map((h) => [h.ticker, h.weight]));
      expect(seriesFor(p.slug).weights).toEqual(printed);
    }
  });

  it("holds the vectors the plan fixed", () => {
    expect(seriesFor("with-trend").weights).toEqual({
      RSST: 25,
      VTI: 19,
      VXUS: 16,
      VTV: 15,
      AVDV: 10,
      IDMO: 5,
      AVES: 5,
      SCHP: 5,
    });
    expect(seriesFor("cautious").weights.VTI).toBe(9.5);
    expect(seriesFor("one-fund").weights).toEqual({ VT: 100 });
  });

  it("carries every series id on the 1990 window and no value lean on the 1929 window", () => {
    expect(
      loadSeries("1990")
        .series.map((s) => s.id)
        .sort()
    ).toEqual([...SERIES_IDS].sort());
    expect(() => seriesFor("value-lean", "1929")).toThrow(/1929/);
    expect(seriesFor("one-fund", "1929").values).toEqual(seriesFor("market", "1929").values);
  });
});

describe("summaries", () => {
  it("ends where the values end", () => {
    for (const window of WINDOWS) {
      for (const s of loadSeries(window).series) {
        expect(s.summary.final).toBe(s.values.at(-1));
        expect(s.summary.worstFall.pct).toBeLessThan(0);
        expect(s.summary.worstFall.dollarsAtTrough).toBeLessThan(10000);
      }
    }
  });

  it("reproduces the controls the research artifacts scored", () => {
    // research/artifacts/00c0b8b0…/tables.md, tournament panel: control_cheap −52.69,
    // control_cheap60_40 −27.18; primary panel: control_cheap −83.67.
    const market = portfolioSummary("market");
    expect(market.worstFall.pct).toBe(-52.7);
    expect(market.worstFall).toMatchObject({ peak: "2007-10", trough: "2009-02", recovered: "2013-01" });
    expect(market.worstFall.monthsToRecover).toBe(63);
    expect(portfolioSummary("sixty-forty").worstFall.pct).toBe(-27.2);
    expect(portfolioSummary("market", "1929").worstFall.pct).toBe(-83.7);
    expect(portfolioSummary("one-fund")).toEqual(market);
  });

  it("labels the one episode that is not a calendar year", () => {
    expect(loadSeries().episodeDefinitions["dotcom-2000-02"]).toMatch(/March 2000.*September 2002/);
    expect(loadSeries().episodeDefinitions["gfc-2008"]).toBe("Calendar year 2008.");
  });
});

describe("portfolios.ts prints what the shelf and the series say", () => {
  it("computes each fee from the shelf and rounds it correctly", () => {
    for (const p of PORTFOLIOS) {
      const bp = weightedExpenseRatioBp(p.holdings, (t) => fundByTicker(t).expenseRatioBp ?? Number.NaN);
      expect(p.fee).toBe(feePercentText(bp));
      expect(p.feeOn10k).toBe(feeOn10kText(bp));
    }
    const cautious = PORTFOLIOS.find((p) => p.slug === "cautious");
    expect(cautious?.fee).toBe("0.21%");
    expect(cautious?.feeOn10k).toBe("$21");
    const trend = PORTFOLIOS.find((p) => p.slug === "with-trend");
    expect(trend?.fee).toBe("0.33%");
  });

  it("prints the worst fall the emitter computed for the printed weights", () => {
    for (const p of PORTFOLIOS) {
      expect(p.worstFall).toBe(formatSignedPercent(portfolioSummary(p.slug).worstFall.pct));
      expect(p.worstFallNote).toBe("1990 to 2026, simulated");
    }
  });
});
