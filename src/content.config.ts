import { defineCollection } from "astro:content";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { glob } from "astro/loaders";
import { z } from "astro/zod";
import { CERTAINTY_CLASSES, EVIDENCE_STATUSES } from "~/content/types";
import { headingSlugs } from "~/lib/anchors";

const REPO_ROOT = process.cwd();

/*
 * The research corpus is no longer a content collection.
 *
 * Two loaders used to render `docs/research/` and `docs/decisions/` as 45 public
 * routes — 88% of the site's word count, in notes addressed to whoever runs the next
 * experiment. Decision 0011 records why that stopped. `docs/` stays in the repository
 * as the record a figure's `docPath` points at, and the schema below still checks that
 * the file and the heading it names exist. Provenance is enforced; it is not published.
 */

/** The `YYYY-MM-DD` shape `AsOf` brands. Checked here so a bad date fails the build. */
const isoDate = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, "asOf must be an ISO date, YYYY-MM-DD")
  .refine((value) => !Number.isNaN(Date.parse(value)), "asOf is not a real date");

const citation = z.object({
  /** What a reader sees. Never a filename. */
  label: z.string().min(1),
  /**
   * Repository-relative, e.g. `docs/research/stacking-and-effective-breadth.md`.
   *
   * Provenance, checked at build time and never rendered. The research notes stay in
   * the repository as the record of where a number came from; publishing them as
   * pages put two hundred thousand words of internal writing in front of readers who
   * came here to find out what to hold. What a reader is shown is `href` or `page`.
   */
  docPath: z.string().min(1),
  /** A heading anchor within that file, with or without the leading `#`. */
  anchor: z.string().min(1).optional(),
  /** A primary source on the open web: a filing, a statute, a paper, a fund page. */
  href: z.string().url().optional(),
  /** A page on this site that explains the number, e.g. `/evidence/trend/`. */
  page: z
    .string()
    .regex(/^\/[a-z0-9\-/]*\/(#[a-z0-9-]+)?$/, "page must be a rooted, slash-terminated site path")
    .optional(),
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

export const collections = { figures };
