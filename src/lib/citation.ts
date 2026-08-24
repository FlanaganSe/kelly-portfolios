import type { Citation } from "~/content/types";
import { onSiteRoute } from "~/lib/research";
import { REPO_URL } from "~/lib/site";

/**
 * Where the Markdown that owns each fact lives on GitHub.
 *
 * Derived from `REPO_URL` rather than written out again. The two were separate
 * literals and had drifted: this one still named a repository that no longer
 * exists, so every figure's source link 404'd.
 */
export const REPO_BLOB_BASE = `${REPO_URL}/blob/main`;

/**
 * The URL a citation points at, in falling order of preference.
 *
 * 1. An external primary source, when the owning page gives one.
 * 2. The page on this site, now that the whole corpus renders here. Sending a reader to
 *    GitHub to read our own argument was a habit from when it was the only copy.
 * 3. The file on GitHub, for the evidence that stays where it is maintained: study
 *    modules, frozen specifications and run artifacts.
 */
export function citationHref(citation: Pick<Citation, "docPath" | "anchor" | "href">): string {
  if (citation.href) return citation.href;
  const path = citation.docPath.replace(/^\/+/, "");
  const anchor = citation.anchor ? `#${citation.anchor.replace(/^#/, "")}` : "";

  const route = onSiteRoute(path);
  return route ? `${route}${anchor}` : `${REPO_BLOB_BASE}/${path}${anchor}`;
}
