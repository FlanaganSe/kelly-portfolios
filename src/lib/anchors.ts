/**
 * Heading anchors, the way GitHub and the Markdown pipeline both spell them.
 *
 * A citation that names a section is only useful if that section exists. The figures
 * collection checks every `source.anchor` against this, so a heading renamed in
 * `docs/research/` fails the build rather than shipping a link into nowhere.
 */

/** GitHub's heading slug: lowercase, punctuation dropped, spaces to hyphens. */
export function slugifyHeading(text: string): string {
  return text
    .trim()
    .toLowerCase()
    .replace(/[‘’“”]/g, "")
    .replace(/[^\p{L}\p{N}\s-]/gu, "")
    .replace(/\s+/g, "-");
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
    const text = heading[2]
      .replace(/`([^`]*)`/g, "$1")
      .replace(/\*\*|__|\*|_/g, "")
      .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1");

    const base = slugifyHeading(text);
    if (!base) continue;

    const count = seen.get(base) ?? 0;
    seen.set(base, count + 1);
    slugs.add(count === 0 ? base : `${base}-${count}`);
  }

  return slugs;
}
