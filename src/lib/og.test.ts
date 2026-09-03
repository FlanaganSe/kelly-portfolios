// @vitest-environment node
import { describe, expect, it } from "vitest";
import { OG_PAGES, ogCard, ogImagePath, ogRouteParam } from "~/lib/og";
import { NAV_ITEMS } from "~/lib/site";

describe("every route the site emits has a card of its own", () => {
  it("covers the whole masthead", () => {
    for (const item of NAV_ITEMS) expect(OG_PAGES).toHaveProperty([item.href]);
  });

  it("throws rather than handing back somebody else's card", () => {
    // The bug this replaced: an unlisted route silently served `/og/index.png`, so the
    // placement calculator was shared under the home page's headline.
    expect(() => ogCard("/tools/whatever-is-next/")).toThrow(/no social card/);
  });

  it("names the page that is missing one", () => {
    expect(() => ogCard("/ledger/")).toThrow(/^\/ledger\/ /);
  });

  it("reads a path with or without its trailing slash", () => {
    expect(ogCard("/tools/which-account").src).toBe("/og/tools/which-account.png");
    expect(ogCard("/tools/which-account/").src).toBe("/og/tools/which-account.png");
  });
});

describe("the card a page points at is the card the build draws", () => {
  /**
   * `src/pages/og/[...route].ts` builds its file names from `ogRouteParam` and
   * `Base.astro` builds its `og:image` from `ogImagePath`. Both are here, so the only
   * way they can disagree is if one of them stops being used.
   */
  it("pairs every hand-written page with its own file", () => {
    const files = Object.keys(OG_PAGES).map((path) => ogRouteParam(path));
    expect(new Set(files).size).toBe(files.length);
    for (const path of Object.keys(OG_PAGES)) expect(ogImagePath(path)).toBe(`/og/${ogRouteParam(path)}`);
  });

  it("puts the home page at index.png", () => {
    expect(ogImagePath("/")).toBe("/og/index.png");
  });
});
