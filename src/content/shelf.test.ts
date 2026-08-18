import { describe, expect, it } from "vitest";
import { funds } from "~/content/portfolio";
import { fundByTicker, type ShelfFund, shelf } from "~/content/shelf";

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

  it("covers the six wrappers the candidate portfolio reaches for", () => {
    expect(wrappers.map((fund) => fund.ticker).sort()).toEqual(["GDE", "JPFP", "MATE", "NTSX", "RSSB", "RSST"]);
  });

  it("measures no factor loading and no alpha for any of them", () => {
    for (const fund of wrappers) {
      expect(fund.loadings).toHaveLength(0);
      expect(fund.alphaPpYr).toBeNull();
    }
  });

  it("keeps `delta` and funding capture consistent, since capture is `1 − delta` and cannot exceed the whole gap", () => {
    for (const fund of shelf) {
      const wrapper = fund.wrapper;
      if (wrapper === undefined || wrapper.delta === null || wrapper.fundingCapturePercent === null) continue;
      const capture = Math.min(100, (1 - wrapper.delta) * 100);
      expect(Math.abs(wrapper.fundingCapturePercent - capture), `${fund.ticker} capture`).toBeLessThan(1);
    }
  });

  it("records nothing for MATE beyond its base leg", () => {
    const mate = fundByTicker("MATE");
    expect(mate.expenseRatioBp).toBeNull();
    expect(mate.wrapper?.delta).toBeNull();
    expect(mate.wrapper?.grossNotionalPerDollar).toBeNull();
    expect(mate.notionalExposure).toEqual([{ kind: "equity", perDollarOfCapital: 0.498 }]);
  });
});
