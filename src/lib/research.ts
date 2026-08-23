/**
 * Reading a research entry that has no frontmatter.
 *
 * None of the 31 files under `docs/research/` carries any. They were written as
 * research notes and each opens with its own `# ` line, so the title is read from the
 * document rather than duplicated into a header block that would then drift from it.
 */

/** The document's own `# ` heading, or the id as a last resort. */
export function researchTitle(entry: { id: string; body?: string | undefined; data: { title?: string } }): string {
  if (entry.data.title) return entry.data.title;

  const heading = entry.body?.match(/^\s{0,3}#\s+(.+?)\s*#*\s*$/m);
  if (heading?.[1]) return heading[1].replace(/`/g, "");

  return entry.id.replace(/-/g, " ");
}

/**
 * The first paragraph after the title, trimmed to one line. Useful as a listing
 * blurb until a page supplies a written one.
 */
export function researchLead(entry: { body?: string | undefined; data: { summary?: string } }): string | undefined {
  if (entry.data.summary) return entry.data.summary;
  if (!entry.body) return undefined;

  const afterTitle = entry.body.replace(/^\s{0,3}#\s+.*$/m, "");
  for (const block of afterTitle.split(/\n\s*\n/)) {
    const text = block.trim();
    if (!text || text.startsWith("#") || text.startsWith("|") || text.startsWith("```")) continue;
    return text.replace(/\s+/g, " ").replace(/\*\*|__|\*|_/g, "");
  }
  return undefined;
}
