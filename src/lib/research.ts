/**
 * The research corpus, rendered on this site rather than deep-linked to GitHub.
 *
 * Three jobs live here, all of them pure string work so they can be tested without a
 * build. First, reading a document that has no frontmatter: none of the files under
 * `docs/research/` carries any, and each opens with its own `# ` line, so the title is
 * read from the document rather than duplicated into a header block that would then
 * drift from it. Second, rewriting the corpus's relative Markdown links to on-site
 * routes, reporting every one that cannot be resolved instead of emitting a dead link.
 * Third, the reading order: which question each page answers, and which reader-facing
 * page covers the same ground in plain English.
 */

import type { EvidenceStatus } from "~/content/types";

/** Where the two rendered halves of the corpus live in the repository. */
export const RESEARCH_DIR = "docs/research";
export const DECISIONS_DIR = "docs/decisions";

/** The decisions index is a listing, not a record, and is not rendered as one. */
const DECISIONS_INDEX = `${DECISIONS_DIR}/README.md`;

/** The document's own `# ` heading, or the id as a last resort. */
export function researchTitle(entry: { id: string; body?: string | undefined; data: { title?: string } }): string {
  if (entry.data.title) return entry.data.title;

  const heading = entry.body?.match(/^\s{0,3}#\s+(.+?)\s*#*\s*$/m);
  if (heading?.[1]) return heading[1].replace(/`/g, "");

  return entry.id.replace(/-/g, " ");
}

/** A block that is a heading, a table, a fence, a list or a quotation, not a lead. */
const NOT_A_PARAGRAPH = /^(#|\||```|>|[-*+]\s|\d+\.\s)/;

/**
 * A bold label opening a paragraph: `**Question.**`, `**Decision it informs.**`.
 *
 * Almost every page in the corpus opens with one, and repeating the same six words
 * down a listing of thirty-four rows carries nothing. The sentence after it does.
 */
const OPENING_LABEL = /^\*\*[^*\n]{1,40}\*\*\s*/;

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
    if (!text || NOT_A_PARAGRAPH.test(text)) continue;

    const lead = text
      .replace(OPENING_LABEL, "")
      .replace(/\s+/g, " ")
      .replace(/`/g, "")
      .replace(/\*\*|__|\*|_/g, "")
      .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
      .trim();
    // A paragraph that was nothing but its own label, as `**Two questions.**` is.
    if (lead) return lead;
  }
  return undefined;
}

/**
 * Cuts a blurb to length on a word boundary, with an ellipsis when it was cut.
 *
 * A listing row is a way in, not a summary: the page itself is one click away, and a
 * paragraph of eight clauses in a list of thirty-four is a wall rather than an index.
 */
export function clamp(text: string, limit: number): string {
  if (text.length <= limit) return text;
  const cut = text.slice(0, limit);
  const boundary = cut.lastIndexOf(" ");
  return `${cut.slice(0, boundary > 0 ? boundary : cut.length).replace(/[,;:.\u2014-]$/, "")}…`;
}

/* -------------------------------------------------------------------------- */
/* Routes                                                                      */
/* -------------------------------------------------------------------------- */

/** `/research/:id/`. Every href carries its slash, because the build emits one form. */
export function researchHref(id: string): string {
  return `/research/${id}/`;
}

/** `/research/decisions/:id/`. */
export function decisionHref(id: string): string {
  return `/research/decisions/${id}/`;
}

/**
 * The on-site route for a repository-relative document path, or `undefined` when the
 * document is not one this site renders.
 */
export function onSiteRoute(repoPath: string): string | undefined {
  if (repoPath === DECISIONS_INDEX) return undefined;
  const research = repoPath.match(/^docs\/research\/([^/]+)\.md$/);
  if (research?.[1]) return researchHref(research[1]);
  const decision = repoPath.match(/^docs\/decisions\/([^/]+)\.md$/);
  if (decision?.[1]) return decisionHref(decision[1]);
  return undefined;
}

/** Normalises a relative POSIX path against the directory it was written in. */
export function resolveRepoPath(fromDir: string, target: string): string {
  const parts = target.startsWith("/") ? [] : fromDir.split("/").filter(Boolean);
  for (const segment of target.split("/")) {
    if (segment === "" || segment === ".") continue;
    if (segment === "..") {
      parts.pop();
      continue;
    }
    parts.push(segment);
  }
  return parts.join("/");
}

/* -------------------------------------------------------------------------- */
/* Link rewriting                                                              */
/* -------------------------------------------------------------------------- */

export interface CorpusContext {
  /** Repository-relative path of the document being rendered. */
  readonly from: string;
  /** Heading ids keyed by repository-relative document path, for the whole corpus. */
  readonly anchors: ReadonlyMap<string, ReadonlySet<string>>;
  /** True when a repository-relative path names a file that exists. */
  readonly exists: (repoPath: string) => boolean;
  /** `https://github.com/<owner>/<repo>/blob/main`. */
  readonly repoBlobBase: string;
}

export interface RewriteReport {
  readonly html: string;
  /** Links now pointing at a page on this site. */
  readonly onSite: number;
  /** Links deliberately left pointing at the repository on GitHub. */
  readonly offSite: number;
  /** One line per link that resolves to nothing. A build must not survive these. */
  readonly failures: readonly string[];
}

const EXTERNAL = /^(?:[a-z][a-z0-9+.-]*:|\/\/)/i;

/** `&#x26;` and friends, as the Markdown pipeline writes them into an href. */
function decodeHref(value: string): string {
  return value
    .replace(/&#x26;|&#38;|&amp;/gi, "&")
    .replace(/&#x27;|&#39;/gi, "'")
    .replace(/&quot;|&#34;/gi, '"');
}

function encodeHref(value: string): string {
  return value.replace(/&/g, "&#38;").replace(/"/g, "&#34;");
}

/** What should happen to one link in a rendered corpus document. */
type LinkOutcome =
  | { readonly kind: "keep" }
  | { readonly kind: "onSite"; readonly href: string }
  | { readonly kind: "offSite"; readonly href: string }
  | { readonly kind: "failure"; readonly message: string };

/** A bare `#fragment`: it stays as written, but its heading still has to exist. */
function resolveFragment(anchor: string, context: CorpusContext): LinkOutcome {
  const own = context.anchors.get(context.from);
  if (anchor && own && !own.has(anchor)) {
    return { kind: "failure", message: `${context.from} links to #${anchor}, which is not a heading on that page` };
  }
  return { kind: "keep" };
}

/** A link to a document this site renders: it becomes an on-site route. */
function resolveRendered(
  route: string,
  repoPath: string,
  anchor: string,
  href: string,
  context: CorpusContext
): LinkOutcome {
  const known = context.anchors.get(repoPath);
  if (!known) {
    return { kind: "failure", message: `${context.from} links to ${href}, which is not a page in the corpus` };
  }
  if (anchor && !known.has(anchor)) {
    return {
      kind: "failure",
      message: `${context.from} links to ${href}, but #${anchor} is not a heading in ${repoPath}`,
    };
  }
  return { kind: "onSite", href: anchor ? `${route}#${anchor}` : route };
}

/**
 * Where one link in the corpus should point once the corpus is on this site.
 *
 * A link to another rendered page becomes an on-site route. A link to anything else
 * the repository holds — a study module, a frozen experiment specification, a run
 * artifact, the charter — becomes a GitHub blob URL, because those files are evidence
 * and belong where they are maintained rather than re-hosted here. A link that names
 * no file at all, and an anchor that names no heading, are reported rather than
 * emitted: a silent failure among several hundred of them would be invisible.
 */
export function resolveCorpusLink(href: string, context: CorpusContext): LinkOutcome {
  if (href === "" || EXTERNAL.test(href)) return { kind: "keep" };

  const [target = "", ...rest] = href.split("#");
  const anchor = rest.join("#");
  if (target === "") return resolveFragment(anchor, context);

  const fromDir = context.from.replace(/\/[^/]*$/, "");
  const repoPath = resolveRepoPath(fromDir, target);

  const route = onSiteRoute(repoPath);
  if (route) return resolveRendered(route, repoPath, anchor, href, context);

  if (!context.exists(repoPath)) {
    return {
      kind: "failure",
      message: `${context.from} links to ${href}, and ${repoPath} is not a file in the repository`,
    };
  }
  return { kind: "offSite", href: `${context.repoBlobBase}/${repoPath}${anchor ? `#${anchor}` : ""}` };
}

/**
 * Rewrites every link in one rendered corpus document and wraps its tables.
 *
 * The build must not survive a failure here. There are several hundred relative links
 * across these pages, so a dead one would be both invisible and widespread.
 */
export function rewriteCorpusHtml(html: string, context: CorpusContext): RewriteReport {
  const failures: string[] = [];
  let onSite = 0;
  let offSite = 0;

  const rewritten = html.replace(/href="([^"]*)"/g, (whole, raw: string) => {
    const outcome = resolveCorpusLink(decodeHref(raw), context);
    if (outcome.kind === "keep") return whole;
    if (outcome.kind === "failure") {
      failures.push(outcome.message);
      return whole;
    }
    if (outcome.kind === "onSite") {
      onSite += 1;
      return `href="${encodeHref(outcome.href)}"`;
    }
    offSite += 1;
    return `href="${encodeHref(outcome.href)}" rel="noopener noreferrer"`;
  });

  return { html: wrapTables(plainCodeBlocks(stripLeadingHeading(rewritten))), onSite, offSite, failures };
}

/**
 * Takes the syntax highlighter's colours off the corpus's code blocks.
 *
 * The default Shiki theme paints every fenced block `#24292e` through an inline style,
 * which no stylesheet can reach without `!important` and which does not follow the
 * theme toggle: a dark slab in the middle of a light page, unchanged when the reader
 * switches. Nothing else on this site is coloured code, and every fence in the corpus
 * is plain text or shell, so the colours carry nothing. Stripping the inline style
 * hands the block back to `.research-body pre`, which paints it in the palette.
 */
export function plainCodeBlocks(html: string): string {
  return html.replace(/<pre\b[^>]*\bclass="[^"]*astro-code[^"]*"[^>]*>/g, (open) => {
    const language = open.match(/data-language="([^"]*)"/)?.[1];
    // `tabindex` stays: the block scrolls, and a scrollable box has to be reachable
    // from the keyboard.
    return `<pre tabindex="0"${language ? ` data-language="${language}"` : ""}>`;
  });
}

/**
 * Removes the document's own opening `<h1>`.
 *
 * Every file in the corpus starts with one and the page prints it as the page title,
 * so leaving it in the body gives the page two `h1` elements and prints the title
 * twice. `_Document.astro` moves the heading's id onto the title it keeps, so a link
 * to the top of a page still lands.
 */
export function stripLeadingHeading(html: string): string {
  return html.replace(/^\s*<h1\b[^>]*>[\s\S]*?<\/h1>\s*/, "");
}

/**
 * Puts every table in its own horizontal scroller.
 *
 * The corpus is table-dense and several of its tables carry eight columns of numbers.
 * At 390px a table that cannot shrink drags the whole page sideways with it, so the
 * overflow has to belong to a box around the table rather than to the document.
 */
export function wrapTables(html: string): string {
  return html.replace(/<table(\s[^>]*)?>([\s\S]*?)<\/table>/g, (_whole, attrs: string | undefined, body: string) => {
    // `tabindex` and the label are not decoration. A box that scrolls has to be
    // reachable and operable from the keyboard, and a focusable box needs a name.
    const wrapper =
      '<div class="scroller research-table" tabindex="0" role="group" aria-label="Table, scrolls sideways">';
    return `${wrapper}<table${attrs ?? ""}>${body}</table></div>`;
  });
}

/* -------------------------------------------------------------------------- */
/* Reading order                                                               */
/* -------------------------------------------------------------------------- */

/** The reader-facing page that covers the same ground without the vocabulary. */
export interface PlainPage {
  readonly href: string;
  readonly label: string;
}

const PLAIN = {
  start: { href: "/start/", label: "Start here" },
  stacking: { href: "/stacking/", label: "Why more good bets stop helping" },
  portfolio: { href: "/portfolio/", label: "The portfolio" },
  rejected: { href: "/doesnt-work/", label: "What doesn't work" },
  howSure: { href: "/how-sure/", label: "How sure we are" },
  funds: { href: "/funds/", label: "The shelf" },
} as const satisfies Readonly<Record<string, PlainPage>>;

export interface ResearchEntryMeta {
  /** The filename stem under `docs/research/`, and the last segment of the route. */
  readonly id: string;
  /**
   * The status of the page's own headline conclusion, in the site's shared vocabulary.
   * A page that runs several experiments carries several statuses and says so in its
   * own text; this is the one attached to the conclusion at the top, and it is an
   * index label rather than a verdict on every result the page holds.
   */
  readonly status: EvidenceStatus;
  /** The four pages the rest of the corpus is read around. */
  readonly loadBearing?: true;
  readonly plain: PlainPage;
}

export interface ResearchGroup {
  readonly id: string;
  /** Two or three words for the left rail. The question is the heading, not this. */
  readonly rail: string;
  /** What a reader would have to want to know to open anything in this group. */
  readonly question: string;
  readonly blurb: string;
  readonly entries: readonly ResearchEntryMeta[];
}

/**
 * The corpus grouped by the question it answers rather than by filename.
 *
 * Every file under `docs/research/` appears exactly once, and the loader fails the
 * build when a file is added without a place here, so the grouping cannot silently
 * fall behind the directory.
 */
export const RESEARCH_GROUPS: readonly ResearchGroup[] = [
  {
    id: "what-to-hold",
    rail: "What to hold",
    question: "What should be held, and why that construction",
    blurb: "The working position, the investor it was derived for, and the tests that scored it against a cheap index.",
    entries: [
      { id: "portfolio-recommendation", status: "exploratory", loadBearing: true, plain: PLAIN.portfolio },
      { id: "construction-tournament", status: "unresolved", loadBearing: true, plain: PLAIN.portfolio },
      { id: "final-construction-test", status: "unresolved", plain: PLAIN.portfolio },
      { id: "portfolio-for-one-investor", status: "exploratory", plain: PLAIN.portfolio },
      { id: "setting-the-equity-share", status: "exploratory", plain: PLAIN.portfolio },
      { id: "valuation-and-the-allocation", status: "exploratory", plain: PLAIN.portfolio },
      { id: "untested-tilt-candidates", status: "exploratory", plain: PLAIN.portfolio },
      { id: "rebalancing-policy", status: "rejected", plain: PLAIN.portfolio },
    ],
  },
  {
    id: "does-stacking-help",
    rail: "Stacking",
    question: "Does piling up more good bets help",
    blurb:
      "Breadth, borrowing, and how each new strategy is paid for. This is where most of the money in the proposal was riding.",
    entries: [
      { id: "stacking-and-effective-breadth", status: "exploratory", loadBearing: true, plain: PLAIN.stacking },
      { id: "capital-efficiency-and-breadth", status: "unresolved", plain: PLAIN.stacking },
      { id: "leverage-and-the-notional-budget", status: "unresolved", plain: PLAIN.stacking },
      { id: "marginal-sleeve-value", status: "unresolved", plain: PLAIN.stacking },
      { id: "trend-marginal-value", status: "rejected", plain: PLAIN.stacking },
      { id: "trend-weight-under-uncertainty", status: "exploratory", plain: PLAIN.stacking },
      { id: "live-stacked-fund-records", status: "source-reproduced", plain: PLAIN.stacking },
      { id: "live-managed-futures", status: "unresolved", plain: PLAIN.stacking },
      { id: "loading-comparability-and-wrapper-exposure", status: "exploratory", plain: PLAIN.stacking },
    ],
  },
  {
    id: "are-the-premiums-real",
    rail: "Factors",
    question: "Are the factor returns real, and can a fund deliver one",
    blurb: "The academic series, what survives publication, and what a fund an investor can buy actually hands over.",
    entries: [
      { id: "factor-persistence", status: "exploratory", plain: PLAIN.howSure },
      { id: "factor-products", status: "unresolved", plain: PLAIN.funds },
      { id: "long-only-capture", status: "rejected", plain: PLAIN.howSure },
      { id: "expected-edge-decomposition", status: "exploratory", plain: PLAIN.howSure },
      { id: "fama-french-reproduction", status: "source-reproduced", plain: PLAIN.howSure },
    ],
  },
  {
    id: "what-is-contractual",
    rail: "Fees and tax",
    question: "What is contractual: fees, taxes and accounts",
    blurb:
      "The part of the answer that follows from a filing or a tax rule rather than from a backtest, and is the largest reliable line on the site.",
    entries: [
      { id: "structural-and-tax-edges", status: "source-reproduced", plain: PLAIN.start },
      { id: "harvesting-and-direct-indexing", status: "exploratory", plain: PLAIN.start },
      { id: "currency-and-the-international-sleeve", status: "exploratory", plain: PLAIN.portfolio },
    ],
  },
  {
    id: "did-not-earn-a-place",
    rail: "Rejections",
    question: "What was tested and did not earn a place",
    blurb: "Each rejection scoped to the data, the window and the yardstick that produced it.",
    entries: [
      { id: "timing-rules-on-the-equity-sleeve", status: "rejected", plain: PLAIN.rejected },
      { id: "alternative-sleeves-audit", status: "exploratory", plain: PLAIN.rejected },
      { id: "current-regime-and-pricing", status: "unresolved", plain: PLAIN.rejected },
    ],
  },
  {
    id: "how-the-evidence-was-made",
    rail: "Method",
    question: "How the evidence was made, and how sure it is",
    blurb: "The instruments, their resolution, the review that went looking for errors in all of it, and what is next.",
    entries: [
      { id: "adversarial-review", status: "exploratory", loadBearing: true, plain: PLAIN.howSure },
      { id: "evidence-base", status: "exploratory", plain: PLAIN.howSure },
      { id: "portfolio-edge-research-framework", status: "exploratory", plain: PLAIN.howSure },
      { id: "portfolio-engine-specification", status: "exploratory", plain: PLAIN.howSure },
      { id: "market-scan-2026", status: "source-reproduced", plain: PLAIN.funds },
      { id: "search-coverage", status: "exploratory", plain: PLAIN.howSure },
    ],
  },
];

const BY_ID = new Map(RESEARCH_GROUPS.flatMap((group) => group.entries.map((entry) => [entry.id, entry] as const)));

/** Every id the grouping knows about. The loader checks the directory against this. */
export function groupedResearchIds(): ReadonlySet<string> {
  return new Set(BY_ID.keys());
}

/** The grouping record for one page, or `undefined` when the page is ungrouped. */
export function researchMeta(id: string): ResearchEntryMeta | undefined {
  return BY_ID.get(id);
}

/** The group a page belongs to. */
export function researchGroupOf(id: string): ResearchGroup | undefined {
  return RESEARCH_GROUPS.find((group) => group.entries.some((entry) => entry.id === id));
}

/**
 * A decision record's reading title: `0004-no-sleeve-promoted` becomes `Decision 0004`.
 * The record's own `# ` line supplies the rest.
 */
export function decisionNumber(id: string): string {
  return id.split("-")[0] ?? id;
}
