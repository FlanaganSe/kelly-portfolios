import type { Citation } from "~/content/types";
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
 * 1. An external primary source: a filing, a statute, a paper, a fund's own page.
 * 2. A page on this site that explains the number in words a reader has.
 * 3. Nothing. `docPath` is provenance, not a destination — it names the internal note
 *    a number came from, the build checks that the note and its heading exist, and a
 *    reader is never shown the path or sent to it. Sending someone who asked what to
 *    hold to a two-hundred-thousand-word directory of working notes was the largest
 *    single reason this site was hard to read.
 */
export function citationHref(citation: Pick<Citation, "href" | "page">): string | undefined {
  return citation.href ?? citation.page;
}
