// @vitest-environment node
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * The client deep-links into the Markdown that owns each fact — every research
 * page and several of their section anchors. Nothing else checks that those
 * targets exist, so shrinking or restructuring a page silently breaks live links
 * on the deployed site.
 *
 * The sources are scanned as text rather than imported, so this also sees
 * citations the content barrel does not re-export, and costs no module graph.
 */

const repoRoot = join(import.meta.dirname, "..", "..");
const srcRoot = join(repoRoot, "src");

function sourceFiles(dir: string, found: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) sourceFiles(path, found);
    else if (/\.tsx?$/.test(name)) found.push(path);
  }
  return found;
}

/** GitHub's heading-to-fragment rule, which is what `citationHref` targets. */
function slugify(heading: string): string {
  return heading
    .trim()
    .toLowerCase()
    .replace(/`/g, "")
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/\*\*|__|\*|_/g, "")
    .replace(/[^\w\- ]/g, "")
    .replace(/ /g, "-");
}

function headingSlugs(markdown: string): Set<string> {
  const slugs = new Set<string>();
  for (const line of markdown.split("\n")) {
    const match = /^#{1,6}\s+(.*)$/.exec(line);
    if (match?.[1] !== undefined) slugs.add(slugify(match[1]));
  }
  return slugs;
}

type Cite = { docPath: string; anchor?: string; where: string };

/**
 * A citation object literal, whose `anchor` may sit on either side of `docPath`.
 * `citation.test.ts` fixtures are excluded: they assert URL shape, not targets.
 */
function citations(): Cite[] {
  const found: Cite[] = [];
  for (const file of sourceFiles(srcRoot)) {
    if (file.endsWith("citation.test.ts") || file.endsWith("citations.test.ts")) continue;
    const text = readFileSync(file, "utf8");
    const where = file.slice(repoRoot.length + 1);
    for (const match of text.matchAll(/docPath:\s*"([^"]+)"/g)) {
      const tail = text.slice(match.index, match.index + 400);
      const anchor = /^[^}]*?anchor:\s*"([^"]+)"/.exec(tail);
      found.push({ docPath: match[1] ?? "", anchor: anchor?.[1], where });
    }
  }
  return found;
}

const all = citations();

describe("every citation points at something that exists", () => {
  it("finds the citations to check", () => {
    expect(all.length).toBeGreaterThan(20);
  });

  it("resolves every docPath to a file in the repository", () => {
    const missing = [...new Set(all.map((c) => c.docPath))].filter((docPath) => {
      try {
        return !statSync(join(repoRoot, docPath.replace(/^\/+/, ""))).isFile();
      } catch {
        return true;
      }
    });
    expect(missing).toEqual([]);
  });

  it("resolves every anchor to a heading in the page it names", () => {
    const slugsFor = new Map<string, Set<string>>();
    const broken: string[] = [];
    for (const cite of all) {
      if (!cite.anchor) continue;
      const path = cite.docPath.replace(/^\/+/, "");
      let slugs = slugsFor.get(path);
      if (!slugs) {
        slugs = headingSlugs(readFileSync(join(repoRoot, path), "utf8"));
        slugsFor.set(path, slugs);
      }
      const anchor = cite.anchor.replace(/^#/, "");
      if (!slugs.has(anchor)) broken.push(`${path}#${anchor} (cited by ${cite.where})`);
    }
    expect(broken).toEqual([]);
  });
});

describe("the docs index stays a complete map", () => {
  it("links every page under docs/research", () => {
    const index = readFileSync(join(repoRoot, "docs", "README.md"), "utf8");
    const pages = readdirSync(join(repoRoot, "docs", "research")).filter((f) => f.endsWith(".md"));
    expect(pages.filter((page) => !index.includes(`research/${page}`))).toEqual([]);
  });

  it("links every decision record", () => {
    const index = readFileSync(join(repoRoot, "docs", "README.md"), "utf8");
    const records = readdirSync(join(repoRoot, "docs", "decisions")).filter((f) => f.endsWith(".md"));
    expect(records.filter((record) => !index.includes(`decisions/${record}`))).toEqual([]);
  });
});

/** Every tracked Markdown file, excluding vendored and generated trees. */
function markdownFiles(): string[] {
  const found = new Set<string>();
  for (const root of [join(repoRoot, "docs"), repoRoot]) {
    for (const name of readdirSync(root, { recursive: true, encoding: "utf8" })) {
      if (!name.endsWith(".md")) continue;
      if (/node_modules|\.venv|research\/artifacts|^dist\//.test(name)) continue;
      found.add(join(root, name));
    }
  }
  return [...found];
}

type Link = { from: string; target: string; anchor: string; line: number };

/** Every relative Markdown link in one file, with the line that wrote it. */
function linksIn(file: string): Link[] {
  const text = readFileSync(file, "utf8");
  const from = file.slice(repoRoot.length + 1);
  const found: Link[] = [];
  for (const match of text.matchAll(/\[[^\]]*\]\(([^)\s]+)\)/g)) {
    const link = match[1] ?? "";
    if (/^(https?:|mailto:)/.test(link)) continue;
    const [target = "", anchor = ""] = link.split("#");
    found.push({ from, target, anchor, line: text.slice(0, match.index).split("\n").length });
  }
  return found;
}

describe("the documentation links to itself correctly", () => {
  const links = markdownFiles().flatMap(linksIn);

  it("finds the links to check", () => {
    expect(links.length).toBeGreaterThan(200);
  });

  it("resolves every relative link to a file that exists", () => {
    const broken = links
      .filter((l) => l.target !== "")
      .filter((l) => {
        const from = join(repoRoot, l.from, "..");
        try {
          statSync(join(from, l.target));
          return false;
        } catch {
          return true;
        }
      })
      .map((l) => `${l.from}:${l.line} → ${l.target}`);
    expect(broken).toEqual([]);
  });

  it("resolves every anchor to a heading in the page it names", () => {
    const slugsFor = new Map<string, Set<string>>();
    const broken: string[] = [];
    for (const link of links) {
      if (link.anchor === "") continue;
      const from = join(repoRoot, link.from, "..");
      const path = link.target === "" ? join(repoRoot, link.from) : join(from, link.target);
      if (!path.endsWith(".md")) continue;
      let slugs = slugsFor.get(path);
      if (!slugs) {
        slugs = headingSlugs(readFileSync(path, "utf8"));
        slugsFor.set(path, slugs);
      }
      if (!slugs.has(link.anchor)) broken.push(`${link.from}:${link.line} → ${link.target}#${link.anchor}`);
    }
    expect(broken).toEqual([]);
  });
});

describe("no synthesis narrates its own history", () => {
  const syntheses = readdirSync(join(repoRoot, "docs", "research"))
    .filter((f) => f.endsWith(".md"))
    .map((f) => join(repoRoot, "docs", "research", f));

  /**
   * A reader cannot tell a live claim from a dead one when a page carries both, so
   * every figure has to be re-derived before it can be quoted. Corrections are written
   * as facts about the world; Git holds what the page used to say.
   */
  const banned = [
    /this (page|section) (previously|had wrong)/i,
    /previously (said|claimed|read|concluded|recorded|overstated)/i,
    /an earlier (draft|version) of this/i,
  ];

  it.each(
    syntheses.map((f) => [f.slice(repoRoot.length + 1), f] as const)
  )("%s states its current position rather than its edit history", (name, file) => {
    const offending = readFileSync(file, "utf8")
      .split("\n")
      .map((line, index) => [index + 1, line] as const)
      .filter(([, line]) => banned.some((pattern) => pattern.test(line)))
      .map(([number, line]) => `${name}:${number} ${line.trim().slice(0, 80)}`);
    expect(offending).toEqual([]);
  });

  it.each(
    syntheses.map((f) => [f.slice(repoRoot.length + 1), f] as const)
  )("%s carries no strikethrough", (name, file) => {
    const struck = readFileSync(file, "utf8")
      .split("\n")
      .map((line, index) => [index + 1, line] as const)
      .filter(([, line]) => line.includes("~~"))
      .map(([number]) => `${name}:${number}`);
    expect(struck).toEqual([]);
  });
});
