/**
 * The social card for each page: what it says, and where its image lives.
 *
 * Two halves. The hand-written pages get a record each, because a card title is a
 * judgement about what the page is for and no rule derives one. The rendered corpus —
 * the syntheses under `/research/` and the decision records under
 * `/research/decisions/` — is handled by rule instead, from each document's own `# `
 * line, because there are fifty of them and a hand-written list would fall behind
 * `docs/` the first week nobody looked.
 *
 * **Nothing falls back.** {@link ogCard} throws on a route it does not recognise, and
 * every page renders through `Base.astro`, so a page added without a card fails the
 * build rather than shipping somebody else's card. The version of this file that
 * returned the home page's card for anything unlisted shipped the account-placement
 * calculator under the headline "Do the certain things first" for months, which is the
 * kind of wrong that no test catches and every reader does.
 *
 * **The 1MB rule.** Bluesky's lexicon caps an embedded thumbnail at exactly 1,000,000
 * bytes and drops the card silently above it — a limit that binds long before Facebook's
 * 8MB. These cards are flat colour, a rule and two blocks of text, which keeps a
 * 1200×630 PNG in the low tens of kilobytes, and `scripts/check-og-size.mjs` fails the
 * build if one ever grows past the cap.
 */

import { canonicalPath, SITE_NAME } from "~/lib/site";

export const OG_WIDTH = 1200;
export const OG_HEIGHT = 630;

/** The hard ceiling, in bytes. Bluesky's, not Facebook's. */
export const OG_MAX_BYTES = 1_000_000;

export interface OgPage {
  /** The line drawn on the card, and the only text in the image. */
  readonly title: string;
  /** The alt text served with the card. Say what the card says. */
  readonly alt: string;
}

/**
 * Keys are canonical page paths with a trailing slash, matching `canonicalPath`. The
 * generated image for `/stacking/` is `/og/stacking.png`; `/` is `/og/index.png`.
 *
 * Every route this site emits that is not a corpus document belongs here, including
 * the two that nobody shares on purpose. `/search/` and `/404/` still get scraped when
 * a link to one leaks into a chat window.
 */
export const OG_PAGES = {
  "/": {
    title: "What to hold",
    alt: `${SITE_NAME}: four portfolios you could actually hold, what each piece is for, and how much of the clever stuff holds up against a cheap index fund.`,
  },
  "/portfolios/": {
    title: "The four portfolios",
    alt: `${SITE_NAME}: all four side by side, with what each costs, what it was compared against, and the worst thing that has happened to it.`,
  },
  "/portfolios/whole-market/": {
    title: "The whole market",
    alt: `${SITE_NAME}: one fund that owns every listed company in the world, and why 90% of professionals could not beat it.`,
  },
  "/portfolios/held-well/": {
    title: "The same funds, held well",
    alt: `${SITE_NAME}: the same holdings as portfolio one, with four changes that are arithmetic rather than forecast.`,
  },
  "/portfolios/value-lean/": {
    title: "A lean toward cheaper, smaller, more profitable companies",
    alt: `${SITE_NAME}: six funds that shift the stock holdings toward cheap and profitable companies, what that was worth, and the decade it can cost you.`,
  },
  "/portfolios/with-trend/": {
    title: "The same, plus a holding that does not move with stocks",
    alt: `${SITE_NAME}: seven funds, one of which borrows inside itself to hold managed futures on top of stocks — the largest bet on this site and the least settled.`,
  },
  "/funds/": {
    title: "What every fund really costs",
    alt: `${SITE_NAME}: every fund we priced, and what each one costs once the income it earns lending its shares out is taken off the fee.`,
  },
  "/evidence/": {
    title: "What we found",
    alt: `${SITE_NAME}: every idea tested here, the verdict, and how sure we are.`,
  },
  "/evidence/fees-and-accounts/": {
    title: "The part that isn’t a guess",
    alt: `${SITE_NAME}: what a fund really costs after lending income, and which account each one belongs in.`,
  },
  "/evidence/how-many-bets/": {
    title: "Why stacking good ideas stops working",
    alt: `${SITE_NAME}: how many unrelated bets a near-certainty would take, and how few of them exist.`,
  },
  "/evidence/trend-following/": {
    title: "Does a managed-futures fund earn its place?",
    alt: `${SITE_NAME}: the crisis behaviour is real, the return cannot be measured, and the fund you pick decides the outcome.`,
  },
  "/evidence/market-timing/": {
    title: "Should you sell when the market falls below its 200-day average?",
    alt: `${SITE_NAME}: the moving-average rule has cost money since it became famous, and tax ends it for a taxable account.`,
  },
  "/evidence/value-and-factors/": {
    title: "Do cheaper, smaller, more profitable companies pay more?",
    alt: `${SITE_NAME}: cheap companies have paid more, small ones have not, and all of it is worth less to a fund holder than to a paper portfolio.`,
  },
  "/evidence/gold/": {
    title: "Is gold worth holding?",
    alt: `${SITE_NAME}: optional, small, and in place of cash rather than in place of shares.`,
  },
  "/evidence/bitcoin/": {
    title: "Does bitcoin protect a portfolio?",
    alt: `${SITE_NAME}: the only thing tested that made a portfolio's worst fall deeper at every weight.`,
  },
  "/evidence/crash-insurance/": {
    title: "Can you buy insurance against a crash?",
    alt: `${SITE_NAME}: it has cost far more than it ever paid out, and holding fewer shares does the same job for no fee.`,
  },
  "/evidence/rebalancing/": {
    title: "Does rebalancing make you money?",
    alt: `${SITE_NAME}: no, and it does not reliably cost you either; it keeps your mix from drifting and nothing more.`,
  },
  "/evidence/direct-indexing/": {
    title: "Is direct indexing worth it?",
    alt: `${SITE_NAME}: it costs a long-term investor money at any fee, including a fee of zero.`,
  },
  "/evidence/what-actually-diversifies/": {
    title: "What actually protects you when stocks fall",
    alt: `${SITE_NAME}: government bonds and trend following, each against one kind of crisis rather than all of them.`,
  },
  "/tools/placement/": {
    title: "Where to hold each fund",
    alt: `${SITE_NAME}: the account-placement calculator, ranking the shelf by what a sheltered dollar of it saves.`,
  },
  "/about/": {
    title: "About this site and the person who writes it",
    alt: `${SITE_NAME}: who writes this, and what stands in place of a credential nobody here holds.`,
  },
  "/corrections/": {
    title: "What we published that turned out to be wrong",
    alt: `${SITE_NAME}: the corrections log — eight dated entries, each one that moved a recommendation.`,
  },
  "/disclosures/": {
    title: "Nobody pays for this site",
    alt: `${SITE_NAME}: no advertising, no affiliate links and no sponsors, and the interests that do exist.`,
  },
  "/disclaimer/": {
    title: "General information, and never advice",
    alt: `${SITE_NAME}: the full disclaimer — general, impersonal, and not an answer about your own portfolio.`,
  },
  "/search/": {
    title: "Search the whole site",
    alt: `${SITE_NAME}: search, including the pages about what did not work.`,
  },
  "/404/": {
    title: "That page is not here",
    alt: `${SITE_NAME}: the page you asked for does not exist on this site.`,
  },
} as const satisfies Readonly<Record<string, OgPage>>;

/** Indexable by an arbitrary path, without losing the literal keys above. */
const PAGES: Readonly<Record<string, OgPage | undefined>> = OG_PAGES;

/**
 * Cuts a title to length on a word boundary, with an ellipsis when it was cut.
 *
 * Lived in `src/lib/research.ts` until the corpus was unpublished and that module had
 * one consumer left. A card is a way in, not a summary.
 */
function clamp(text: string, limit: number): string {
  if (text.length <= limit) return text;
  const cut = text.slice(0, limit);
  const boundary = cut.lastIndexOf(" ");
  return `${cut.slice(0, boundary > 0 ? boundary : cut.length).replace(/[,;:.\u2014-]$/, "")}…`;
}

/** The point past which a title is cut on a word boundary for a card. */
const TITLE_LIMIT = 96;

/** The route parameter `src/pages/og/[...route].ts` emits a card at. */
export function ogRouteParam(path: string): string {
  return path === "/" ? "index.png" : `${path.replace(/^\/|\/$/g, "")}.png`;
}

/** The path of the generated card for a canonical page path. */
export function ogImagePath(path: string): string {
  return `/og/${ogRouteParam(path)}`;
}

export interface OgCard {
  /** Site-absolute, e.g. `/og/tools/placement.png`. */
  readonly src: string;
  readonly alt: string;
}

/**
 * The card for a page, or a thrown error naming the page that has none.
 *
 * Every route is listed in {@link OG_PAGES} and says whatever its record says. There
 * used to be a second branch deriving a card from a corpus document's own heading;
 * it went with the corpus (decision 0011), and with it the reason this function took
 * the page's title as an argument.
 */
export function ogCard(pathname: string): OgCard {
  const path = canonicalPath(pathname);

  const page = PAGES[path];
  if (page) return { src: ogImagePath(path), alt: page.alt };

  throw new Error(
    `${path} has no social card. Add a record for it to OG_PAGES in src/lib/og.ts, ` +
      "which is what puts a card in dist/og/ and a matching og:image on the page. " +
      "Falling back to another page's card is what this throw exists to prevent."
  );
}
