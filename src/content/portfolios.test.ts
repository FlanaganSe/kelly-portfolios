import { describe, expect, it } from "vitest";
import { engineMeta, portfolioById, portfolios, totalWeight, weightByEngine } from "~/content/portfolios";

describe("every published portfolio", () => {
  it("has holdings summing to exactly 100% of capital", () => {
    for (const portfolio of portfolios) {
      expect(totalWeight(portfolio), portfolio.id).toBe(100);
    }
  });

  it("has a unique id and a unique name", () => {
    expect(new Set(portfolios.map((one) => one.id)).size).toBe(portfolios.length);
    expect(new Set(portfolios.map((one) => one.name)).size).toBe(portfolios.length);
  });

  it("names no holding twice", () => {
    for (const portfolio of portfolios) {
      const tickers = portfolio.holdings.map((one) => one.ticker);
      expect(new Set(tickers).size, portfolio.id).toBe(tickers.length);
    }
  });

  it("holds no zero or negative weight", () => {
    for (const portfolio of portfolios) {
      for (const holding of portfolio.holdings) {
        expect(holding.percent, `${portfolio.id}/${holding.ticker}`).toBeGreaterThan(0);
      }
    }
  });

  it("declares a return engine the vocabulary knows", () => {
    for (const portfolio of portfolios) {
      for (const holding of portfolio.holdings) {
        expect(engineMeta[holding.engine]).toBeDefined();
      }
    }
  });

  it("says how it may fail, not only how it may win", () => {
    for (const portfolio of portfolios) {
      expect(portfolio.mayUnderperform.length, portfolio.id).toBeGreaterThan(0);
      expect(portfolio.failureModes.length, portfolio.id).toBeGreaterThan(0);
    }
  });

  it("states where it is editorial rather than measured", () => {
    for (const portfolio of portfolios) {
      expect(portfolio.editorialNote.length, portfolio.id).toBeGreaterThan(40);
    }
  });

  /**
   * Decision 0006: a tilt quoted as an expected return without its dispersion is not
   * reportable. Only a contractual line may carry a zero tracking error.
   */
  it("prices every risk premium with a tracking error", () => {
    for (const portfolio of portfolios) {
      for (const line of portfolio.priced) {
        if (line.edgeBp !== null && line.certainty === "risk-premium") {
          expect(line.trackingErrorBp, `${portfolio.id}/${line.label}`).not.toBeNull();
          expect(line.trackingErrorBp ?? 0, `${portfolio.id}/${line.label}`).toBeGreaterThan(0);
        }
        // A line with no edge has to be saying something else instead.
        if (line.edgeBp === null) {
          expect(line.growthBp, `${portfolio.id}/${line.label}`).not.toBeNull();
        }
      }
    }
  });

  it("reports notional exposure whenever it exceeds capital", () => {
    for (const portfolio of portfolios) {
      if (portfolio.grossExposurePercent > 100) {
        expect(portfolio.notional.length, portfolio.id).toBeGreaterThan(0);
        const declared = portfolio.notional.reduce((sum, one) => sum + one.percent, 0);
        expect(Math.abs(declared - portfolio.grossExposurePercent), portfolio.id).toBeLessThan(1);
      } else {
        expect(portfolio.notional, portfolio.id).toHaveLength(0);
      }
    }
  });
});

describe("lookups", () => {
  it("finds a portfolio by id and returns undefined for an unknown one", () => {
    expect(portfolioById("control")?.name).toBe("The control");
    expect(portfolioById("nope")).toBeUndefined();
  });

  it("groups capital weight by engine without losing any of it", () => {
    for (const portfolio of portfolios) {
      const total = weightByEngine(portfolio).reduce((sum, one) => sum + one.percent, 0);
      expect(Math.round(total * 100) / 100, portfolio.id).toBe(100);
    }
  });
});
