import { describe, expect, it } from "vitest";
import { families, familyBySlug } from "~/content/families";
import { portfolioById } from "~/content/portfolios";
import { statusMeta } from "~/content/types";

describe("the research library", () => {
  it("has a unique slug per family", () => {
    expect(new Set(families.map((one) => one.slug)).size).toBe(families.length);
  });

  it("uses only the repository's closed status vocabulary", () => {
    for (const family of families) {
      expect(statusMeta[family.status], family.slug).toBeDefined();
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
