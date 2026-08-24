/**
 * Heading anchors, the way GitHub and the Markdown pipeline both spell them.
 *
 * A citation that names a section is only useful if that section exists. The figures
 * collection checks every `source.anchor` against this, and the corpus loader in
 * `src/content.config.ts` asserts that the ids this produces are exactly the ids the
 * Markdown pipeline emitted, so a heading renamed in `docs/research/` fails the build
 * rather than shipping a link into nowhere.
 */

/**
 * GitHub's heading slug: lowercase, punctuation dropped, spaces to hyphens.
 *
 * Each space becomes its own hyphen and runs are never collapsed, which is what
 * `github-slugger` does and therefore what both GitHub and Astro's pipeline emit.
 * Collapsing them looks tidier and is wrong: `panels — a study` drops the em dash and
 * leaves two spaces, so the real anchor is `panels--a-study` with the double hyphen.
 */
export function slugifyHeading(text: string): string {
  return text
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N} _-]/gu, "")
    .replace(/ /g, "-");
}

/**
 * Every heading slug in a Markdown document, with `-1`, `-2` suffixes for repeats
 * exactly as GitHub disambiguates them. Fenced code blocks are skipped so a shell
 * comment is not mistaken for an `#` heading.
 */
export function headingSlugs(markdown: string): Set<string> {
  const slugs = new Set<string>();
  const seen = new Map<string, number>();
  let inFence = false;

  for (const line of markdown.split("\n")) {
    if (/^\s{0,3}(```|~~~)/.test(line)) {
      inFence = !inFence;
      continue;
    }
    if (inFence) continue;

    const heading = line.match(/^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$/);
    if (!heading?.[2]) continue;

    // Strip inline markup so `**Question.**` slugs the same way GitHub renders it.
    // Emphasis markers are stripped outside code spans only: `gamma_star` keeps its
    // underscore in the rendered id, and treating that one as an emphasis marker put
    // `#does-gammastar-match…` in the anchor set and `#does-gamma_star-match…` on the
    // page.
    const text = heading[2]
      .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
      .split(/(`[^`]*`)/)
      .map((part) => (part.startsWith("`") ? part.slice(1, -1) : part.replace(/\*\*|__|\*|_/g, "")))
      .join("");

    const base = slugifyHeading(text);
    if (!base) continue;

    const count = seen.get(base) ?? 0;
    seen.set(base, count + 1);
    slugs.add(count === 0 ? base : `${base}-${count}`);
  }

  return slugs;
}
