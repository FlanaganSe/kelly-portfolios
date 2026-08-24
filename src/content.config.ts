import { defineCollection } from "astro:content";
import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import type { Loader, LoaderContext } from "astro/loaders";
import { glob } from "astro/loaders";
import { z } from "astro/zod";
import { CERTAINTY_CLASSES, EVIDENCE_STATUSES } from "~/content/types";
import { headingSlugs } from "~/lib/anchors";
import { REPO_BLOB_BASE } from "~/lib/citation";
import { DECISIONS_DIR, groupedResearchIds, RESEARCH_DIR, rewriteCorpusHtml } from "~/lib/research";

const REPO_ROOT = process.cwd();

/* -------------------------------------------------------------------------- */
/* The corpus loader                                                           */
/* -------------------------------------------------------------------------- */

interface CorpusFile {
  /** The filename stem, which is also the last segment of the route. */
  readonly id: string;
  /** Repository-relative, e.g. `docs/research/long-only-capture.md`. */
  readonly repoPath: string;
  readonly absolute: string;
  readonly raw: string;
}

function corpusFiles(dir: string): CorpusFile[] {
  const absoluteDir = path.join(REPO_ROOT, dir);
  return readdirSync(absoluteDir)
    .filter((name) => name.endsWith(".md") && name !== "README.md")
    .sort()
    .map((name) => {
      const absolute = path.join(absoluteDir, name);
      return {
        id: name.replace(/\.md$/, ""),
        repoPath: `${dir}/${name}`,
        absolute,
        raw: readFileSync(absolute, "utf8"),
      };
    });
}

/**
 * Heading ids for every document either half of the corpus can link to.
 *
 * Built for both directories at once, because the syntheses and the decision records
 * cite each other and a link can only be checked against the target's own headings.
 */
function corpusAnchors(): Map<string, Set<string>> {
  const anchors = new Map<string, Set<string>>();
  for (const dir of [RESEARCH_DIR, DECISIONS_DIR]) {
    for (const file of corpusFiles(dir)) anchors.set(file.repoPath, headingSlugs(file.raw));
  }
  return anchors;
}

/**
 * The date each document last changed, read from Git rather than guessed.
 *
 * None of these files carries frontmatter, so there is no written date to read and
 * inventing one would be worse than none. `%cs` is the committer date as `YYYY-MM-DD`.
 * A file Git cannot speak for — an uncommitted draft, a build with no repository —
 * falls back to its own mtime.
 */
function lastChangedDates(): Map<string, string> {
  const dates = new Map<string, string>();
  try {
    const log = execFileSync("git", ["log", "--name-only", "--pretty=format:%cs", "--", RESEARCH_DIR, DECISIONS_DIR], {
      cwd: REPO_ROOT,
      encoding: "utf8",
      maxBuffer: 32 * 1024 * 1024,
    });
    let date = "";
    for (const line of log.split("\n")) {
      if (/^\d{4}-\d{2}-\d{2}$/.test(line)) {
        date = line;
      } else if (line.endsWith(".md") && !dates.has(line)) {
        dates.set(line, date);
      }
    }
  } catch {
    // No Git, or a build from an export. The mtime fallback below covers it.
  }
  return dates;
}

function lastChangedDate(file: CorpusFile, fromGit: Map<string, string>): string {
  const committed = fromGit.get(file.repoPath);
  if (committed) return committed;
  return statSync(file.absolute).mtime.toISOString().slice(0, 10);
}

/**
 * Asserts that the ids the Markdown pipeline emitted are exactly the ids
 * {@link headingSlugs} computes.
 *
 * Figure citations name a `docPath` and an `anchor`, and the figures schema checks that
 * anchor against `headingSlugs`. If the renderer spelled its heading ids differently,
 * every one of those citations would point at a fragment that is not on the page and
 * nothing would say so. The two spellings agreeing is a build-time assertion, not an
 * assumption: `github-slugger` gives each space its own hyphen, so an em dash between
 * two words leaves a double hyphen behind, and a slugger that collapsed the run would
 * disagree here rather than in production.
 */
function assertHeadingIdsAgree(file: CorpusFile, rendered: readonly string[]): string[] {
  const computed = headingSlugs(file.raw);
  const problems: string[] = [];
  for (const slug of rendered) {
    if (!computed.has(slug)) problems.push(`${file.repoPath}: the renderer emitted #${slug}, headingSlugs did not`);
  }
  for (const slug of computed) {
    if (!rendered.includes(slug))
      problems.push(`${file.repoPath}: headingSlugs produced #${slug}, the renderer did not`);
  }
  return problems;
}

/**
 * Loads one half of the corpus: renders it, rewrites its links, and refuses to finish
 * if any link or anchor in it resolves to nothing.
 *
 * The files themselves are untouched evidence. Everything this does happens to the
 * rendered HTML on the way into the data store, so `docs/` stays a directory of
 * research notes rather than a directory of web pages.
 */
function corpusLoader(dir: string): Loader {
  return {
    name: `corpus:${dir}`,
    load: async ({ store, parseData, renderMarkdown, generateDigest, config, logger }: LoaderContext) => {
      store.clear();

      const anchors = corpusAnchors();
      const gitDates = lastChangedDates();
      const exists = (repoPath: string) => existsSync(path.join(REPO_ROOT, repoPath));
      const failures: string[] = [];
      const totals = { onSite: 0, offSite: 0 };

      for (const file of corpusFiles(dir)) {
        const rendered = await renderMarkdown(file.raw, {
          fileURL: new URL(`file://${file.absolute}`),
        });
        const headings = rendered.metadata?.headings ?? [];
        failures.push(
          ...assertHeadingIdsAgree(
            file,
            headings.map((heading) => heading.slug)
          )
        );

        const report = rewriteCorpusHtml(rendered.html, {
          from: file.repoPath,
          anchors,
          exists,
          repoBlobBase: REPO_BLOB_BASE,
        });
        failures.push(...report.failures);
        totals.onSite += report.onSite;
        totals.offSite += report.offSite;

        const data = await parseData({
          id: file.id,
          data: { updated: lastChangedDate(file, gitDates) },
          filePath: file.repoPath,
        });

        store.set({
          id: file.id,
          data,
          body: file.raw,
          filePath: file.repoPath,
          digest: generateDigest(`${config.base}:${file.raw}`),
          rendered: { ...rendered, html: report.html },
        });
      }

      if (failures.length > 0) {
        throw new Error(
          `${failures.length} unresolved link${failures.length === 1 ? "" : "s"} in ${dir}:\n  ${failures.join("\n  ")}`
        );
      }

      logger.info(`${totals.onSite} links rewritten to on-site routes, ${totals.offSite} left on GitHub, 0 unresolved`);
    },
  };
}

/** Every field is optional: no file in the corpus carries frontmatter. */
const corpusSchema = z.object({
  title: z.string().optional(),
  summary: z.string().optional(),
  updated: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/)
    .optional(),
  status: z.enum(EVIDENCE_STATUSES).optional(),
  draft: z.boolean().optional(),
});

/**
 * The research corpus, rendered on-site at `/research/:id/`.
 *
 * None of the files under `docs/research/` carries frontmatter, and rewriting them to
 * add some would edit evidence for the sake of a template. The reading title comes from
 * the document's own `# ` line at query time (see `researchTitle`) and the date comes
 * from Git.
 *
 * The id is the bare filename stem rather than Astro's slugified default. That is the
 * same string for every current file, but not guaranteed for a future one, and the
 * route has to keep matching the paths the figure citations already print.
 */
const research = defineCollection({
  loader: corpusLoader(RESEARCH_DIR),
  schema: corpusSchema,
});

/**
 * The decision records, rendered on-site at `/research/decisions/:id/`.
 *
 * They are cited about fifty times from the syntheses — decision 0004 alone twenty-one
 * times — so sending a reader to GitHub for them would rebuild the problem that
 * rendering the corpus exists to solve. `docs/decisions/README.md` is a listing rather
 * than a record and is not rendered.
 */
const decisions = defineCollection({
  loader: corpusLoader(DECISIONS_DIR),
  schema: corpusSchema,
});

/**
 * Every synthesis has a place in the reading order, and every place names a real file.
 *
 * The grouping in `src/lib/research.ts` is written by hand, because grouping by the
 * question a page answers is a judgement no filename carries. This is what stops it
 * from falling behind `docs/research/` in either direction.
 */
function assertCorpusIsGrouped(): void {
  const onDisk = new Set(corpusFiles(RESEARCH_DIR).map((file) => file.id));
  const grouped = groupedResearchIds();
  const ungrouped = [...onDisk].filter((id) => !grouped.has(id));
  const missing = [...grouped].filter((id) => !onDisk.has(id));
  if (ungrouped.length > 0 || missing.length > 0) {
    throw new Error(
      [
        "the research index and docs/research/ disagree.",
        ungrouped.length > 0 ? `Not in any group: ${ungrouped.join(", ")}.` : "",
        missing.length > 0 ? `Grouped but not on disk: ${missing.join(", ")}.` : "",
        "Both are fixed in RESEARCH_GROUPS in src/lib/research.ts.",
      ]
        .filter(Boolean)
        .join(" ")
    );
  }
}

assertCorpusIsGrouped();

/** The `YYYY-MM-DD` shape `AsOf` brands. Checked here so a bad date fails the build. */
const isoDate = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, "asOf must be an ISO date, YYYY-MM-DD")
  .refine((value) => !Number.isNaN(Date.parse(value)), "asOf is not a real date");

const citation = z.object({
  label: z.string().min(1),
  /** Repository-relative, e.g. `docs/research/stacking-and-effective-breadth.md`. */
  docPath: z.string().min(1),
  /** A heading anchor within that file, with or without the leading `#`. */
  anchor: z.string().min(1).optional(),
});

/**
 * Every figure the site prints, one YAML record each.
 *
 * `value` is a string and is never coerced. The sign, the precision and the interval
 * are part of the fact; a number that goes through a formatter has been requoted, and
 * `0.435` is not the same claim as `0.44`.
 */
const figures = defineCollection({
  loader: glob({ pattern: "*.yaml", base: "./src/content/figures" }),
  schema: z
    .object({
      label: z.string().min(1),
      value: z.string().min(1),
      unit: z.string().min(1).optional(),
      /** The interval as the source prints it, e.g. `[+1.46, +8.10]`. */
      interval: z.string().min(1).optional(),
      status: z.enum(EVIDENCE_STATUSES),
      certainty: z.enum(CERTAINTY_CLASSES).optional(),
      asOf: isoDate,
      /** The window the figure was measured over, e.g. `1963-07 to 2025-12`. */
      period: z.string().min(1).optional(),
      source: citation,
      note: z.string().min(1).optional(),
    })
    .superRefine((figure, ctx) => {
      const docPath = figure.source.docPath.replace(/^\/+/, "");
      const absolute = path.join(REPO_ROOT, docPath);

      if (!existsSync(absolute)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["source", "docPath"],
          message: `no such file in the repository: ${docPath}`,
        });
        return;
      }

      if (!figure.source.anchor) return;

      const wanted = figure.source.anchor.replace(/^#/, "");
      const slugs = headingSlugs(readFileSync(absolute, "utf8"));
      if (!slugs.has(wanted)) {
        const near = [...slugs].filter((s) => s.includes(wanted.slice(0, 8))).slice(0, 3);
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["source", "anchor"],
          message:
            `#${wanted} is not a heading in ${docPath}. ` +
            (near.length
              ? `Did you mean ${near.map((s) => `#${s}`).join(", ")}?`
              : `That file has ${slugs.size} headings.`),
        });
      }
    }),
});

export const collections = { research, decisions, figures };
