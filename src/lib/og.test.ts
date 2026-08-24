// @vitest-environment node
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { OG_PAGES, ogCard, ogCorpusTitle, ogImagePath, ogRouteParam } from "~/lib/og";
import { DECISIONS_DIR, decisionHref, RESEARCH_DIR, researchHref, researchTitle } from "~/lib/research";
import { NAV_ITEMS } from "~/lib/site";

const repoRoot = join(import.meta.dirname, "..", "..");

function corpusIds(dir: string): string[] {
  return readdirSync(join(repoRoot, dir))
    .filter((name) => name.endsWith(".md") && name !== "README.md")
    .map((name) => name.replace(/\.md$/, ""));
}

describe("every route the site emits has a card of its own", () => {
  it("covers the whole masthead", () => {
    for (const item of NAV_ITEMS) expect(OG_PAGES).toHaveProperty([item.href]);
  });

  it("throws rather than handing back somebody else's card", () => {
    // The bug this replaced: an unlisted route silently served `/og/index.png`, so the
    // placement calculator was shared under the home page's headline.
    expect(() => ogCard("/tools/whatever-is-next/", "A new tool")).toThrow(/no social card/);
  });

  it("names the page that is missing one", () => {
    expect(() => ogCard("/ledger/", "The ledger")).toThrow(/^\/ledger\/ /);
  });

  it("reads a path with or without its trailing slash", () => {
    expect(ogCard("/tools/placement", "").src).toBe("/og/tools/placement.png");
    expect(ogCard("/tools/placement/", "").src).toBe("/og/tools/placement.png");
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

  it("gives every corpus document a card under /og/research/", () => {
    for (const id of corpusIds(RESEARCH_DIR)) {
      expect(ogCard(researchHref(id), "A synthesis").src).toBe(`/og/research/${id}.png`);
    }
    for (const id of corpusIds(DECISIONS_DIR)) {
      expect(ogCard(decisionHref(id), "A record").src).toBe(`/og/research/decisions/${id}.png`);
    }
  });

  it("says which half of the corpus a card came from", () => {
    expect(ogCard(researchHref("long-only-capture"), "The long-only capture fraction").alt).toContain("working note");
    expect(ogCard(decisionHref("0004-no-sleeve-promoted"), "0004 — No sleeve is promoted").alt).toContain(
      "decision record"
    );
  });

  it("leaves the research index to its own hand-written card", () => {
    expect(ogCard("/research/", "The research").alt).toBe(OG_PAGES["/research/"].alt);
  });
});

describe("a corpus heading is cut to something the card can set large", () => {
  it("keeps a title that is already short", () => {
    expect(ogCorpusTitle("The construction tournament")).toBe("The construction tournament");
  });

  it("drops the subtitle of a long one", () => {
    expect(
      ogCorpusTitle(
        "Timing rules on the equity sleeve: the drawdown is real, the return is not, and it is a bet already held"
      )
    ).toBe("Timing rules on the equity sleeve");
  });

  it("keeps the subtitle when the head alone is a bare topic", () => {
    const trend = "Trend: the index, the products, and a clause that was ambiguously specified";
    expect(ogCorpusTitle(trend)).toBe(trend);
  });

  it("clamps a long title that has no subtitle to cut at", () => {
    const long = `${"word ".repeat(30)}end`;
    expect(ogCorpusTitle(long).length).toBeLessThanOrEqual(97);
    expect(ogCorpusTitle(long).endsWith("…")).toBe(true);
  });

  it("never sends the renderer a title long enough to set at the floor", () => {
    // The real headings, not a fixture: the longest one in the corpus is 104 characters
    // and the renderer's floor is where a title that long would end up.
    for (const dir of [RESEARCH_DIR, DECISIONS_DIR]) {
      for (const id of corpusIds(dir)) {
        const body = readFileSync(join(repoRoot, dir, `${id}.md`), "utf8");
        const drawn = ogCorpusTitle(researchTitle({ id, body, data: {} }));
        expect(drawn.length, `${dir}/${id}.md`).toBeLessThanOrEqual(97);
        expect(drawn, `${dir}/${id}.md`).not.toMatch(/[,;:]$/);
      }
    }
  });
});
