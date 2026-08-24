// @vitest-environment node
import { describe, expect, it } from "vitest";
import {
  clamp,
  decisionHref,
  demoteInnerHeadings,
  groupedResearchIds,
  onSiteRoute,
  plainCodeBlocks,
  RESEARCH_GROUPS,
  researchHref,
  researchLead,
  researchMeta,
  researchTitle,
  resolveCorpusLink,
  resolveRepoPath,
  rewriteCorpusHtml,
  stripLeadingHeading,
  wrapTables,
} from "~/lib/research";

describe("reading a document with no frontmatter", () => {
  it("takes the title from the document's own heading", () => {
    const entry = { id: "x", body: "# The long-only capture fraction\n\nBody.", data: {} };
    expect(researchTitle(entry)).toBe("The long-only capture fraction");
  });

  it("prefers frontmatter when a file ever grows some", () => {
    expect(researchTitle({ id: "x", body: "# Written", data: { title: "Declared" } })).toBe("Declared");
  });

  it("reads the lead from the first paragraph, past a table", () => {
    const entry = { body: "# Title\n\n| a | b |\n\n**Question.** What is *it*?\n", data: {} };
    expect(researchLead(entry)).toBe("What is it?");
  });
});

describe("resolving a repository-relative path", () => {
  it("walks up out of the directory the link was written in", () => {
    expect(resolveRepoPath("docs/research", "../decisions/0004-no-sleeve-promoted.md")).toBe(
      "docs/decisions/0004-no-sleeve-promoted.md"
    );
    expect(resolveRepoPath("docs/research", "../../research/studies/stacking.py")).toBe("research/studies/stacking.py");
    expect(resolveRepoPath("docs/research", "long-only-capture.md")).toBe("docs/research/long-only-capture.md");
  });
});

describe("which documents this site renders", () => {
  it("routes a synthesis and a decision record, and nothing else", () => {
    expect(onSiteRoute("docs/research/long-only-capture.md")).toBe("/research/long-only-capture/");
    expect(onSiteRoute("docs/decisions/0004-no-sleeve-promoted.md")).toBe(
      "/research/decisions/0004-no-sleeve-promoted/"
    );
    expect(onSiteRoute("docs/decisions/README.md")).toBeUndefined();
    expect(onSiteRoute("docs/charter.md")).toBeUndefined();
    expect(onSiteRoute("research/studies/stacking.py")).toBeUndefined();
  });

  it("carries a trailing slash on every route it builds", () => {
    expect(researchHref("x").endsWith("/")).toBe(true);
    expect(decisionHref("0001-x").endsWith("/")).toBe(true);
  });
});

const anchors = new Map<string, Set<string>>([
  ["docs/research/a.md", new Set(["here", "there"])],
  ["docs/research/b.md", new Set(["over-there"])],
  ["docs/decisions/0004-x.md", new Set(["scope"])],
]);

const context = {
  from: "docs/research/a.md",
  anchors,
  exists: (repoPath: string) => repoPath === "docs/charter.md",
  repoBlobBase: "https://example.test/blob/main",
};

describe("rewriting one link", () => {
  it("leaves an external link alone", () => {
    expect(resolveCorpusLink("https://fred.stlouisfed.org/series/SP500", context)).toEqual({ kind: "keep" });
  });

  it("keeps a bare fragment that names a real heading", () => {
    expect(resolveCorpusLink("#here", context)).toEqual({ kind: "keep" });
  });

  it("reports a bare fragment that names no heading", () => {
    expect(resolveCorpusLink("#nowhere", context)).toMatchObject({ kind: "failure" });
  });

  it("rewrites a sibling synthesis, anchor and all", () => {
    expect(resolveCorpusLink("b.md#over-there", context)).toEqual({
      kind: "onSite",
      href: "/research/b/#over-there",
    });
  });

  it("rewrites a decision record", () => {
    expect(resolveCorpusLink("../decisions/0004-x.md#scope", context)).toEqual({
      kind: "onSite",
      href: "/research/decisions/0004-x/#scope",
    });
  });

  it("reports an anchor that is not a heading in the page it names", () => {
    expect(resolveCorpusLink("b.md#missing", context)).toMatchObject({ kind: "failure" });
  });

  it("sends a file this site does not render to the repository", () => {
    expect(resolveCorpusLink("../charter.md", context)).toEqual({
      kind: "offSite",
      href: "https://example.test/blob/main/docs/charter.md",
    });
  });

  it("reports a link to a file that does not exist rather than emitting it", () => {
    expect(resolveCorpusLink("../../gone.md", context)).toMatchObject({ kind: "failure" });
  });
});

describe("rewriting a rendered document", () => {
  it("counts what it changed and leaves an external link untouched", () => {
    const html = '<p><a href="b.md">b</a> <a href="../charter.md">c</a> <a href="https://x.test/">x</a></p>';
    const report = rewriteCorpusHtml(html, context);
    expect(report.failures).toEqual([]);
    expect(report.onSite).toBe(1);
    expect(report.offSite).toBe(1);
    expect(report.html).toContain('href="/research/b/"');
    expect(report.html).toContain('href="https://x.test/"');
    expect(report.html).toContain('rel="noopener noreferrer"');
  });

  it("does not throw the document away when a link fails", () => {
    const report = rewriteCorpusHtml('<p><a href="gone.md">g</a>text</p>', context);
    expect(report.failures).toHaveLength(1);
    expect(report.html).toContain("text");
  });

  it("puts every table in its own scroller", () => {
    const wrapped = wrapTables("<p>a</p><table><tr><td>1</td></tr></table><table></table>");
    expect(wrapped.match(/class="scroller research-table"/g)).toHaveLength(2);
    expect(wrapped).toContain('tabindex="0"');
    expect(wrapped).toContain("<table><tr><td>1</td></tr></table></div>");
  });
});

describe("the reading order covers the corpus", () => {
  it("groups every synthesis exactly once", () => {
    const listed = RESEARCH_GROUPS.flatMap((group) => group.entries.map((entry) => entry.id));
    expect(new Set(listed).size).toBe(listed.length);
    expect(listed).toHaveLength(35);
  });

  it("names four load-bearing pages", () => {
    const leading = RESEARCH_GROUPS.flatMap((group) =>
      group.entries.filter((entry) => entry.loadBearing === true).map((entry) => entry.id)
    );
    expect(leading.sort()).toEqual([
      "adversarial-review",
      "construction-tournament",
      "portfolio-recommendation",
      "stacking-and-effective-breadth",
    ]);
  });

  it("points every entry at a reader-facing page whose href ends in a slash", () => {
    for (const group of RESEARCH_GROUPS) {
      for (const entry of group.entries) {
        expect(entry.plain.href.endsWith("/")).toBe(true);
      }
    }
  });

  it("gives every grouped id a record", () => {
    for (const id of groupedResearchIds()) expect(researchMeta(id)?.id).toBe(id);
  });
});

describe("a listing blurb", () => {
  it("drops the paragraph's own bold label", () => {
    const entry = { body: "# T\n\n**Question.** What does a candidate add?", data: {} };
    expect(researchLead(entry)).toBe("What does a candidate add?");
  });

  it("skips a paragraph that was nothing but its label", () => {
    const entry = { body: "# T\n\n**Two questions, two experiments.**\n\nThe real lead.", data: {} };
    expect(researchLead(entry)).toBe("The real lead.");
  });

  it("skips a list and a quotation as well as a table", () => {
    const entry = { body: "# T\n\n1. first\n\n> quoted\n\n- bullet\n\nThe lead.", data: {} };
    expect(researchLead(entry)).toBe("The lead.");
  });

  it("unwraps a link and drops code ticks", () => {
    const entry = { body: "# T\n\nSee [the tournament](construction-tournament.md), `as of 2026-08-23`.", data: {} };
    expect(researchLead(entry)).toBe("See the tournament, as of 2026-08-23.");
  });

  it("cuts on a word boundary and marks the cut", () => {
    expect(clamp("one two three four five", 12)).toBe("one two…");
    expect(clamp("short", 12)).toBe("short");
  });
});

describe("the document's own title", () => {
  it("is removed from the body, because the page prints it as the page title", () => {
    const html = '<h1 id="a-title">A title</h1>\n<p>Body.</p>';
    expect(stripLeadingHeading(html)).toBe("<p>Body.</p>");
  });

  it("leaves a later heading alone", () => {
    const html = "<p>Body.</p><h1>Late</h1>";
    expect(stripLeadingHeading(html)).toBe(html);
  });
});

describe("fenced code", () => {
  it("drops the highlighter's inline colours and keeps the language", () => {
    const html =
      '<pre class="astro-code github-dark" style="background-color:#24292e;color:#e1e4e8" tabindex="0" data-language="sh"><code>ls</code></pre>';
    expect(plainCodeBlocks(html)).toBe('<pre tabindex="0" data-language="sh"><code>ls</code></pre>');
  });

  it("leaves a plain pre alone", () => {
    expect(plainCodeBlocks("<pre><code>ls</code></pre>")).toBe("<pre><code>ls</code></pre>");
  });
});

describe("a document that splits itself into parts", () => {
  it("demotes a level-one heading left in the body, keeping its id", () => {
    expect(demoteInnerHeadings('<h1 id="part-a">Part A</h1>')).toBe('<h2 id="part-a">Part A</h2>');
  });

  it("leaves every other heading alone", () => {
    expect(demoteInnerHeadings("<h2>Two</h2><h3>Three</h3>")).toBe("<h2>Two</h2><h3>Three</h3>");
  });
});
