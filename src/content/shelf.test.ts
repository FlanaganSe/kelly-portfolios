import { describe, expect, it } from "vitest";
import { funds } from "~/content/portfolio";
import { fundByTicker, type ShelfFund, shelf } from "~/content/shelf";
import {
  commonWindow,
  distinctWindows,
  IncomparableWindowsError,
  loadingsFor,
  rankLoadings,
  windowMonths,
} from "~/lib/loadings";

/** Basis points, so 0.01 bp is a hundredth of a hundredth of a percent. */
const COST_TOLERANCE_BP = 0.01;

/**
 * The two panels an ex-US or emerging fund may be read on, plus the one case the audit
 * makes explicitly: DFEV and AVES were regressed on the **US** panel as well as their own,
 * and the point of publishing both is that the panel flips the sign. Any other ex-US fund
 * carrying a `us` loading would be the mistake this list exists to catch.
 */
const US_PANEL_ALLOWED = new Set(["AVES", "DFEV"]);

function isNonUsFund(fund: ShelfFund): boolean {
  return fund.category.startsWith("intl-") || fund.category.startsWith("emerging-");
}

describe("shelf identity", () => {
  it("gives every fund a unique upper-case ticker", () => {
    const tickers = shelf.map((fund) => fund.ticker);
    expect(new Set(tickers).size).toBe(tickers.length);
    for (const ticker of tickers) {
      expect(ticker).toBe(ticker.toUpperCase());
      expect(ticker).toMatch(/^[A-Z]{2,5}$/);
    }
  });

  it("throws for a ticker it does not carry rather than returning undefined", () => {
    expect(() => fundByTicker("NOPE")).toThrow(/no shelf record/);
    expect(() => fundByTicker("vti")).toThrow(/no shelf record/);
    expect(fundByTicker("VTI").ticker).toBe("VTI");
  });
});

describe("cost is fee less securities lending", () => {
  it("computes net cost from the two terms wherever both were read", () => {
    for (const fund of shelf) {
      if (fund.expenseRatioBp === null || fund.securitiesLendingBp === null) continue;
      expect(fund.netCostBp).not.toBeNull();
      const expected = fund.expenseRatioBp - fund.securitiesLendingBp;
      expect(Math.abs((fund.netCostBp ?? Number.NaN) - expected)).toBeLessThanOrEqual(COST_TOLERANCE_BP);
    }
  });
});

describe("a loading names its panel", () => {
  it("attaches a panel to every loading", () => {
    for (const fund of shelf) {
      for (const loading of fund.loadings) {
        expect(loading.panel).toBeTruthy();
      }
    }
  });

  it("keeps ex-US and emerging funds off the US panel except where both readings were published", () => {
    for (const fund of shelf.filter(isNonUsFund)) {
      const onUsPanel = fund.loadings.some((loading) => loading.panel === "us");
      if (onUsPanel) expect(US_PANEL_ALLOWED.has(fund.ticker)).toBe(true);
    }
  });

  it("publishes both panel readings for the two emerging value funds, and they differ in sign", () => {
    for (const ticker of US_PANEL_ALLOWED) {
      const fund = fundByTicker(ticker);
      const own = fund.loadings.find((loading) => loading.panel === "emerging");
      const us = fund.loadings.find((loading) => loading.panel === "us");
      expect(own).toBeDefined();
      expect(us).toBeDefined();
      expect(Math.sign(own?.value ?? 0)).toBe(1);
      expect(Math.sign(us?.value ?? 0)).toBe(-1);
    }
  });
});

/**
 * The nine US large- and small-value products the recommendation compares. Every one was
 * fitted on the months it had filed, so the published numbers are not on a common scale.
 */
const US_VALUE_SHELF = ["VTV", "AVLV", "DFLV", "DFUV", "AVUV", "DFSV", "DFAT", "RPV", "VBR"];

describe("a loading names its window, and the windows differ", () => {
  it("gives every loading a window, or an explicit null, and never a bare month count", () => {
    for (const fund of shelf) {
      for (const loading of fund.loadings) {
        expect(loading).toHaveProperty("window");
        expect("months" in loading).toBe(false);
        if (loading.window === null) continue;
        expect(loading.window.from).toMatch(/^\d{4}-\d{2}$/);
        expect(loading.window.to).toMatch(/^\d{4}-\d{2}$/);
        expect(windowMonths(loading.window) ?? 0).toBeGreaterThan(0);
      }
    }
  });

  /**
   * The invariant this file exists to pin. Nine US value products, nine different
   * windows-worth of history, and no two of the extremes share a month count. Sorting the
   * published values would order launch dates as much as funds, so `rankLoadings` refuses
   * — and this test fails the day someone quietly equalises the windows in prose without
   * refitting, or adds a tenth fund with no window at all.
   */
  it("cannot rank the published US value shelf, because its nine windows are not one window", () => {
    const rows = loadingsFor(shelf, "HML", "us").filter((row) => US_VALUE_SHELF.includes(row.ticker));
    expect(rows.map((row) => row.ticker).sort()).toEqual([...US_VALUE_SHELF].sort());
    const windows = distinctWindows(rows.map((row) => row.loading));
    expect(windows.length).toBeGreaterThan(1);
    expect(() => rankLoadings(rows.map((row) => row.loading))).toThrow(IncomparableWindowsError);
  });

  /**
   * The window a refit has to use, and the reason the matched ranking is a snapshot: the
   * nine funds share only 36 months. `docs/research/loading-comparability-and-wrapper-exposure.md`
   * publishes the refit on exactly these months.
   */
  it("leaves the nine funds only 36 months in common", () => {
    const rows = loadingsFor(shelf, "HML", "us").filter((row) => US_VALUE_SHELF.includes(row.ticker));
    const shared = commonWindow(rows.map((row) => row.loading));
    expect(shared).toEqual({ from: "2023-01", to: "2025-12" });
    expect(windowMonths(shared)).toBe(36);
  });

  it("keeps every managed-futures loading on its own window too", () => {
    const rows = loadingsFor(shelf, "TSMOM", "aqr-tsmom");
    expect(distinctWindows(rows.map((row) => row.loading)).length).toBeGreaterThan(1);
    expect(() => rankLoadings(rows.map((row) => row.loading))).toThrow(IncomparableWindowsError);
  });
});

/**
 * Two funds on this shelf are rejected by their trading rather than by their exposure, and
 * both deliver the factor they advertise. A turnover figure that quietly went missing would
 * turn either verdict back into an endorsement, so the numbers are pinned here.
 * `docs/research/untested-tilt-candidates.md` §3 prices them.
 */
describe("turnover decides two verdicts, so it may not go missing", () => {
  it.each([
    ["MTUM", 116, "UMD", 0.444],
    ["QVAL", 332, "HML", 0.503],
  ])("keeps %s's filed turnover beside the exposure it delivers", (ticker, turnover, factor, value) => {
    const fund = fundByTicker(ticker as string);
    expect(fund.turnoverPercent).toBe(turnover);
    const loading = fund.loadings.find((one) => one.factor === factor);
    expect(loading?.value).toBeCloseTo(value as number, 3);
    expect(fund.issuer, `${ticker} states a turnover with no filing behind it`).toBeDefined();
  });

  /**
   * EDGAR lists no Form N-PORT for QVAL's quarter ending 2021-09-30, so its history has a
   * three-month hole and only the gapless run after it is usable. The window is therefore
   * shorter than the fund is old, and it must not be widened to match its inception.
   */
  it("fits QVAL on its gapless run rather than on its whole filed history", () => {
    const qval = fundByTicker("QVAL");
    for (const loading of qval.loadings) {
      expect(loading.window).toEqual({ from: "2021-10", to: "2026-03" });
      expect(windowMonths(loading.window)).toBe(54);
    }
  });
});

describe("an alpha never prints without its pedestal", () => {
  it("carries a pedestal wherever an alpha was read", () => {
    for (const fund of shelf) {
      if (fund.alphaPpYr === null) continue;
      expect(fund.pedestalPpYr, `${fund.ticker} prints an alpha with no pedestal`).not.toBeNull();
    }
  });

  it("uses the three regional pedestals the evidence base publishes", () => {
    const published = new Set([-0.55, -0.31, 1.5]);
    for (const fund of shelf) {
      if (fund.pedestalPpYr === null) continue;
      expect(published.has(fund.pedestalPpYr), `${fund.ticker} invents a pedestal`).toBe(true);
    }
  });
});

describe("the two fund records may not drift apart", () => {
  /** `portfolio.ts` stores lending as prose where the filing is not a bare number. */
  function bareNumber(value: string | null): number | null {
    if (value === null || !/^\d+(\.\d+)?$/.test(value)) return null;
    return Number(value);
  }

  const shared = funds.filter((fund) => shelf.some((one) => one.ticker === fund.ticker));

  it("covers the eight funds the reference portfolio prices", () => {
    expect(shared.map((fund) => fund.ticker).sort()).toEqual(["BND", "DBMF", "VB", "VBR", "VEA", "VTI", "VWO", "VXUS"]);
  });

  it.each(shared.map((fund) => fund.ticker))("agrees with the reference portfolio on %s", (ticker) => {
    const inPortfolio = funds.find((fund) => fund.ticker === ticker);
    const onShelf = fundByTicker(ticker);
    if (inPortfolio === undefined) throw new Error(`portfolio.ts lost ${ticker}`);

    expect(onShelf.expenseRatioBp).toBe(inPortfolio.expenseRatioBp);
    expect(onShelf.netCostBp).toBe(inPortfolio.netCostBp);

    const lending = bareNumber(inPortfolio.securitiesLendingBp);
    if (lending !== null) expect(onShelf.securitiesLendingBp).toBe(lending);
  });
});

describe("wrappers report structure and cost, never a sleeve", () => {
  const wrappers = shelf.filter((fund) => fund.category === "capital-efficient");

  it("covers the seven wrappers the candidate portfolio reaches for", () => {
    expect(wrappers.map((fund) => fund.ticker).sort()).toEqual(["CTAP", "GDE", "JPFP", "MATE", "NTSX", "RSSB", "RSST"]);
  });

  /**
   * SDMF was reported to this repository as a stacked equity-plus-trend wrapper at 35 bp.
   * Its filing holds no equity at all, so it belongs with the standalone trend funds and
   * keeps none of the funding-rule gap. A cheap fee on the wrong category is not a cheap
   * wrapper, and this test is what stops it drifting back into the wrapper list.
   */
  it("keeps SDMF out of the wrapper category, because it holds no base leg", () => {
    const sdmf = fundByTicker("SDMF");
    expect(sdmf.category).toBe("managed-futures");
    expect(sdmf.wrapper?.delta).toBe(1);
    expect(sdmf.wrapper?.fundingCapturePercent).toBe(0);
    expect(sdmf.notionalExposure).toBeUndefined();
  });

  /**
   * A wrapper's *return* is not measured on this shelf and its alpha stays null: over
   * 29 to 31 months an alpha would be a statement about the window. Its delivered
   * *exposure* is a different question, and Form N-PORT Item B.5 answers it for any
   * wrapper old enough to have filed. RSST and RSSB have; the other five have three to
   * eight months of filings, which is why their lists are empty.
   */
  it("measures no alpha for any wrapper, and a loading only where the filings support one", () => {
    for (const fund of wrappers) {
      expect(fund.alphaPpYr, `${fund.ticker} alpha`).toBeNull();
      if (["RSST", "RSSB"].includes(fund.ticker)) continue;
      expect(fund.loadings, `${fund.ticker} loadings`).toHaveLength(0);
    }
  });

  it("gives RSST and RSSB a trend loading with the months behind it", () => {
    const rsst = fundByTicker("RSST").loadings[0];
    const rssb = fundByTicker("RSSB").loadings[0];
    expect(rsst?.factor).toBe("TSMOM");
    expect(rsst?.panel).toBe("aqr-tsmom");
    expect(windowMonths(rsst?.window ?? null)).toBe(31);
    expect(rssb?.factor).toBe("TSMOM");
    expect(windowMonths(rssb?.window ?? null)).toBe(29);
  });

  /**
   * RSSB is the negative control: same sponsor, same wrapper structure, bonds instead of
   * a trend book. If its trend loading were not near zero, RSST's +0.681 would be a
   * property of the regression rather than of the fund.
   */
  it("keeps the negative control near zero, which is what makes RSST's loading readable", () => {
    const rssb = fundByTicker("RSSB").loadings[0];
    expect(Math.abs(rssb?.value ?? 1)).toBeLessThan(0.2);
    const rsst = fundByTicker("RSST").loadings[0];
    expect(rsst?.value ?? 0).toBeGreaterThan(0.4);
  });

  it("keeps `delta` and funding capture consistent, since capture is `1 − delta` and cannot exceed the whole gap", () => {
    for (const fund of shelf) {
      const wrapper = fund.wrapper;
      if (wrapper === undefined || wrapper.delta === null || wrapper.fundingCapturePercent === null) continue;
      const capture = Math.min(100, (1 - wrapper.delta) * 100);
      expect(Math.abs(wrapper.fundingCapturePercent - capture), `${fund.ticker} capture`).toBeLessThan(1);
    }
  });

  /**
   * MATE's base leg is the filed ETF holding **plus** the S&P future that completes it.
   * Reading the 50.30% ETF line alone is what previously put this fund in the range where
   * a wrapper is worse than selling equity outright; the future is on the same filing.
   */
  it("reads MATE's base leg as the ETF plus the index future that completes it", () => {
    const mate = fundByTicker("MATE");
    const equity = mate.notionalExposure?.find((leg) => leg.kind === "us-equity");
    expect(equity?.perDollarOfCapital).toBeGreaterThan(1);
    expect(mate.wrapper?.delta).toBeLessThan(0);
    expect(mate.wrapper?.fundingCapturePercent).toBe(100);
  });

  /** No wrapper on this shelf has a distribution tax drag it did not file an after-tax table for. */
  it("leaves MATE's and JPFP's tax drag null, since neither has completed a calendar year", () => {
    for (const ticker of ["MATE", "JPFP"]) {
      const fund = fundByTicker(ticker);
      expect(fund.wrapper?.distributionTaxDragPpYr).toBeNull();
      expect(fund.wrapper?.incrementalTaxDragBp).toBeNull();
    }
  });

  /** JPFP has filed no N-PORT, so it has no structure date and no delta. Both must stay null. */
  it("gives JPFP no structure it has not filed", () => {
    const jpfp = fundByTicker("JPFP");
    expect(jpfp.wrapper?.structureAsOf).toBeNull();
    expect(jpfp.wrapper?.delta).toBeNull();
    expect(jpfp.wrapper?.grossNotionalPerDollar).toBeNull();
    expect(jpfp.notionalExposure).toBeUndefined();
  });
});
