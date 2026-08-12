import { describe, expect, it } from "vitest";
import { citationHref, REPO_BLOB_BASE } from "~/lib/citation";

describe("citationHref", () => {
  it("points a docPath at the file on GitHub", () => {
    expect(citationHref({ docPath: "docs/research/long-only-capture.md" })).toBe(
      `${REPO_BLOB_BASE}/docs/research/long-only-capture.md`
    );
  });

  it("appends the anchor, with or without a leading hash", () => {
    expect(citationHref({ docPath: "docs/README.md", anchor: "capture" })).toBe(
      `${REPO_BLOB_BASE}/docs/README.md#capture`
    );
    expect(citationHref({ docPath: "docs/README.md", anchor: "#capture" })).toBe(
      `${REPO_BLOB_BASE}/docs/README.md#capture`
    );
  });

  it("strips a leading slash from the docPath", () => {
    expect(citationHref({ docPath: "/docs/README.md" })).toBe(`${REPO_BLOB_BASE}/docs/README.md`);
  });

  it("prefers an external primary source when the citation gives one", () => {
    expect(citationHref({ docPath: "docs/README.md", href: "https://example.org/paper.pdf" })).toBe(
      "https://example.org/paper.pdf"
    );
  });
});
