/**
 * The social card for each page: what it says, and where its image lives.
 *
 * One record per route. A page not listed here falls back to the site card, which is
 * better than a broken image and much better than a card that describes the wrong page.
 *
 * **The 1MB rule.** Bluesky's lexicon caps an embedded thumbnail at exactly 1,000,000
 * bytes and drops the card silently above it — a limit that binds long before Facebook's
 * 8MB. These cards are flat colour, a rule and two blocks of text, which keeps a
 * 1200×630 PNG in the low tens of kilobytes, and `scripts/check-og-size.mjs` fails the
 * build if one ever grows past the cap.
 */

import { SITE_DESCRIPTION, SITE_NAME } from "~/lib/site";

export const OG_WIDTH = 1200;
export const OG_HEIGHT = 630;

/** The hard ceiling, in bytes. Bluesky's, not Facebook's. */
export const OG_MAX_BYTES = 1_000_000;

export interface OgPage {
  readonly title: string;
  readonly description: string;
  /** The alt text served with the card. Say what the card says. */
  readonly alt: string;
}

/**
 * Keys are canonical page paths with a trailing slash, matching `canonicalPath`. The
 * generated image for `/stacking/` is `/og/stacking.png`; `/` is `/og/index.png`.
 */
export const OG_PAGES = {
  "/": {
    title: "Do the certain things first",
    description: SITE_DESCRIPTION,
    alt: `${SITE_NAME}: do the certain things first — fees, taxes and account placement, then decide about the rest.`,
  },
  "/start/": {
    title: "Start here",
    description:
      "Six steps, ordered by how fast you would find out whether each one worked. Fees settle in about four months. Clever construction takes about thirty-one years.",
    alt: `${SITE_NAME}: the ordered checklist, fees first and clever construction last.`,
  },
  "/stacking/": {
    title: "Why more good bets stop helping",
    description:
      "Stacking has a ceiling, the ceiling arrives early, and how you pay for each new strategy decides whether your edges add up or average out.",
    alt: `${SITE_NAME}: the stacking ceiling, and why the funding rule decides everything.`,
  },
  "/portfolio/": {
    title: "The portfolio",
    description:
      "Seven funds, the account each one goes in, the single choice you have to make yourself, and an honest account of how bad it will feel when it is losing.",
    alt: `${SITE_NAME}: seven holdings and the account each one belongs in.`,
  },
  "/doesnt-work/": {
    title: "Things we tested that did not earn a place",
    description:
      "Market timing, crypto, crash insurance, direct indexing and six more, each with the data, the window and the yardstick its rejection is scoped to.",
    alt: `${SITE_NAME}: the rejections, each scoped to the design that produced it.`,
  },
  "/how-sure/": {
    title: "How sure we are, and how we have been wrong",
    description:
      "The four words attached to every claim here, how long you would have to hold something before your own account could tell you, and eight errors this project found in its own numbers.",
    alt: `${SITE_NAME}: the four confidence rungs, and the corrections log.`,
  },
  "/funds/": {
    title: "The shelf",
    description:
      "Every fund this project has priced or regressed, with its fee, its cost after securities lending, and the verdict attached to it.",
    alt: `${SITE_NAME}: the audited fund shelf, on cost rather than on fee.`,
  },
  "/research/": {
    title: "The research",
    description:
      "Every synthesis behind this site, one page per question. Several of them conclude that we could not tell.",
    alt: `${SITE_NAME}: the research corpus, one synthesis per question.`,
  },
} as const satisfies Readonly<Record<string, OgPage>>;

const DEFAULT_PATH = "/";

/** The path of the generated card for a page, or the site card if it has none. */
export function ogImagePath(pathname: string): string {
  const key = ogKey(pathname);
  return key === "/" ? "/og/index.png" : `/og${key.replace(/\/$/, "")}.png`;
}

export function ogAlt(pathname: string): string {
  return OG_PAGES[ogKey(pathname) as keyof typeof OG_PAGES].alt;
}

function ogKey(pathname: string): string {
  const here = pathname.replace(/\/+$/, "") || "/";
  const withSlash = here === "/" ? "/" : `${here}/`;
  return withSlash in OG_PAGES ? withSlash : DEFAULT_PATH;
}
