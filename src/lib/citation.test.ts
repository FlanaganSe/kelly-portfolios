import { describe, expect, it } from "vitest";
import { citationHref } from "~/lib/citation";

describe("citationHref", () => {
  it("prefers a primary source on the open web", () => {
    expect(
      citationHref({
        href: "https://investor.vanguard.com/investment-products/etfs/profile/vti",
        page: "/evidence/fees-and-accounts/",
      })
    ).toBe("https://investor.vanguard.com/investment-products/etfs/profile/vti");
  });

  it("falls back to the page on this site that explains the number", () => {
    expect(citationHref({ page: "/evidence/how-many-bets/#the-ceiling" })).toBe("/evidence/how-many-bets/#the-ceiling");
  });

  /**
   * The one that matters. `docPath` is provenance the build checks and a reader never
   * sees; a figure carrying only a repository path renders its label as plain text
   * rather than a link into a directory of working notes.
   */
  it("gives no destination when a record names only its internal provenance", () => {
    expect(citationHref({})).toBeUndefined();
  });
});
