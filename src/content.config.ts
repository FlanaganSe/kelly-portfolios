import { defineCollection } from "astro:content";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { glob } from "astro/loaders";
import { z } from "astro/zod";
import { CERTAINTY_CLASSES, EVIDENCE_STATUSES } from "~/content/types";
import { headingSlugs } from "~/lib/anchors";

const REPO_ROOT = process.cwd();

/**
 * The research corpus, rendered on-site instead of deep-linked to GitHub.
 *
 * None of the 31 files under `docs/research/` carries frontmatter, and rewriting them
 * to add some would edit evidence for the sake of a template. So every field here is
 * optional and the reading title comes from the document's own `# ` line at query
 * time (see `researchTitle`). A file that later grows frontmatter is validated by it;
 * a file that does not is still a valid entry.
 */
const research = defineCollection({
  loader: glob({
    pattern: "*.md",
    base: path.join(REPO_ROOT, "docs/research"),
    // `/research/:slug` must keep matching the old client's URLs, which used the bare
    // filename stem. Astro's default would slugify, which is the same string here for
    // every current file, but not guaranteed for a future one.
    generateId: ({ entry }) => entry.replace(/\.md$/, ""),
  }),
  schema: z.object({
    title: z.string().optional(),
    summary: z.string().optional(),
    updated: z
      .string()
      .regex(/^\d{4}-\d{2}-\d{2}$/)
      .optional(),
    status: z.enum(EVIDENCE_STATUSES).optional(),
    draft: z.boolean().optional(),
  }),
});

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

export const collections = { research, figures };
