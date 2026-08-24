import { describe, expect, it } from "vitest";
import { citationHref, REPO_BLOB_BASE } from "~/lib/citation";

describe("citationHref", () => {
  it("prefers an external primary source when the citation gives one", () => {
    expect(citationHref({ docPath: "docs/README.md", href: "https://example.org/paper.pdf" })).toBe(
      "https://example.org/paper.pdf"
    );
  });

  it("sends a research page to its own route on this site", () => {
    expect(citationHref({ docPath: "docs/research/long-only-capture.md" })).toBe("/research/long-only-capture/");
  });

  it("sends a decision record to its own route too", () => {
    expect(citationHref({ docPath: "docs/decisions/0004-no-sleeve-promoted.md" })).toBe(
      "/research/decisions/0004-no-sleeve-promoted/"
    );
  });

  it("still points at GitHub for evidence that is not rendered here", () => {
    // Study modules, frozen specifications and run artifacts stay where they are
    // maintained. Only the prose corpus has a page on this site.
    expect(citationHref({ docPath: "research/experiments/exp_016_construction.yaml" })).toBe(
      `${REPO_BLOB_BASE}/research/experiments/exp_016_construction.yaml`
    );
    // The decisions index is a listing rather than a record, so it has no route.
    expect(citationHref({ docPath: "docs/decisions/README.md" })).toBe(`${REPO_BLOB_BASE}/docs/decisions/README.md`);
  });

  it("appends the anchor, with or without a leading hash, on either kind of target", () => {
    expect(citationHref({ docPath: "docs/research/long-only-capture.md", anchor: "capture" })).toBe(
      "/research/long-only-capture/#capture"
    );
    expect(citationHref({ docPath: "docs/research/long-only-capture.md", anchor: "#capture" })).toBe(
      "/research/long-only-capture/#capture"
    );
    expect(citationHref({ docPath: "docs/README.md", anchor: "capture" })).toBe(
      `${REPO_BLOB_BASE}/docs/README.md#capture`
    );
  });

  it("strips a leading slash from the docPath", () => {
    expect(citationHref({ docPath: "/docs/research/long-only-capture.md" })).toBe("/research/long-only-capture/");
    expect(citationHref({ docPath: "/docs/README.md" })).toBe(`${REPO_BLOB_BASE}/docs/README.md`);
  });
});
