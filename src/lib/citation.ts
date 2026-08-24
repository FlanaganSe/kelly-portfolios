import type { Citation } from "~/content/types";
import { REPO_URL } from "~/lib/site";

/**
 * Where the Markdown that owns each fact actually lives.
 *
 * Derived from `REPO_URL` rather than written out again. The two were separate
 * literals and had drifted: this one still named a repository that no longer
 * exists, so every figure's source link 404'd.
 */
export const REPO_BLOB_BASE = `${REPO_URL}/blob/main`;

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
