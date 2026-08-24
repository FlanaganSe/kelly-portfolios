// @vitest-environment node
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { headingSlugs, slugifyHeading } from "~/lib/anchors";

const repoRoot = join(import.meta.dirname, "..", "..");

describe("heading slugs spell anchors the way GitHub does", () => {
  it("gives each space its own hyphen rather than collapsing the run", () => {
    // The em dash is dropped and the spaces around it are not, which is the whole
    // reason the corpus is full of double-hyphen anchors.
    expect(slugifyHeading("Size on the three panels — a study, not an experiment")).toBe(
      "size-on-the-three-panels--a-study-not-an-experiment"
    );
  });

  it("keeps an underscore inside a code span", () => {
    expect(headingSlugs("### Does `gamma_star` match the closed form? Yes")).toContain(
      "does-gamma_star-match-the-closed-form-yes"
    );
  });

  it("strips emphasis outside code spans", () => {
    expect(headingSlugs("## **Question.**")).toEqual(new Set(["question"]));
  });

  it("disambiguates repeats the way GitHub does", () => {
    expect(headingSlugs("## Scope\n## Scope\n## Scope")).toEqual(new Set(["scope", "scope-1", "scope-2"]));
  });

  it("ignores a heading-shaped line inside a fence", () => {
    expect(headingSlugs("```sh\n# not a heading\n```\n## Real")).toEqual(new Set(["real"]));
  });
});

describe("the anchors the figures schema checks are the anchors the corpus writes", () => {
  /**
   * `src/content/citations.test.ts` already proves that every relative link in `docs/`
   * resolves, using its own copy of GitHub's slug rule. This proves the copy in
   * `src/lib/anchors.ts` — the one the figures schema and the corpus loader use —
   * agrees with it on the file that made them disagree.
   */
  it("keeps the double hyphen an em dash leaves behind", () => {
    const markdown = readFileSync(join(repoRoot, "docs/research/factor-persistence.md"), "utf8");
    expect(headingSlugs(markdown)).toContain("size-on-the-three-panels--a-study-not-an-experiment");
  });
});
