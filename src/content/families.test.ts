import { describe, expect, it } from "vitest";
import { families, familyBySlug } from "~/content/families";
import { portfolioById } from "~/content/portfolios";
import { findFund } from "~/content/shelf";
import { certaintyMeta, statusMeta } from "~/content/types";

describe("the research library", () => {
  it("has a unique slug per family", () => {
    expect(new Set(families.map((one) => one.slug)).size).toBe(families.length);
  });

  it("uses only the repository's closed vocabularies", () => {
    for (const family of families) {
      expect(certaintyMeta[family.certainty], family.slug).toBeDefined();
      if (family.status !== null) {
        expect(statusMeta[family.status], family.slug).toBeDefined();
      }
    }
  });

  /**
   * The experiment ladder grades experiments. A contractual result is not one, and
   * giving it a rung would put a status on the page above the highest any experiment
   * here has actually reached.
   */
  it("gives a contractual family no experiment status at all", () => {
    for (const family of families.filter((one) => one.certainty === "contractual")) {
      expect(family.status, family.slug).toBeNull();
    }
  });

  it("explains every status rather than using the label decoratively", () => {
    for (const family of families) {
      expect(family.statusReason.length, family.slug).toBeGreaterThan(60);
    }
  });

  it("carries contrary evidence and named failure modes on every page", () => {
    for (const family of families) {
      expect(family.evidenceAgainst.length, family.slug).toBeGreaterThan(0);
      expect(family.failureModes.length, family.slug).toBeGreaterThan(0);
    }
  });

  it("links only to portfolios that exist", () => {
    for (const family of families) {
      for (const id of family.portfolios) {
        expect(portfolioById(id), `${family.slug} -> ${id}`).toBeDefined();
      }
    }
  });

  it("gives every page a practical summary near the top", () => {
    for (const family of families) {
      expect(family.inPractice.length, family.slug).toBeGreaterThan(80);
    }
  });

  it("cites at least one owning research page", () => {
    for (const family of families) {
      expect(family.sources.length, family.slug).toBeGreaterThan(0);
      for (const source of family.sources) {
        expect(source.docPath, family.slug).toMatch(/^docs\//);
      }
    }
  });

  it("finds a family by slug and returns undefined for an unknown one", () => {
    expect(familyBySlug("value")?.name).toBe("Value");
    expect(familyBySlug("nope")).toBeUndefined();
  });
});

describe("the funds a family names", () => {
  it("names only tickers the shelf actually carries", () => {
    for (const family of families) {
      for (const ticker of family.tickers) {
        expect(findFund(ticker), `${family.slug} -> ${ticker}`).toBeDefined();
      }
    }
  });
});
