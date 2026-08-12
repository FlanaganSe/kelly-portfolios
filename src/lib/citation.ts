import type { Citation } from "~/content/types";

/** Where the Markdown that owns each fact actually lives. */
export const REPO_BLOB_BASE = "https://github.com/FlanaganSe/investing-portfolio/blob/main";

/**
 * The URL a citation points at. An external primary source wins when the owning
 * page gives one; otherwise the reader gets the repository file itself.
 */
export function citationHref(citation: Pick<Citation, "docPath" | "anchor" | "href">): string {
  if (citation.href) return citation.href;
  const path = citation.docPath.replace(/^\/+/, "");
  const anchor = citation.anchor ? `#${citation.anchor.replace(/^#/, "")}` : "";
  return `${REPO_BLOB_BASE}/${path}${anchor}`;
}
