/**
 * The social card for each page: what it says, and where its image lives.
 *
 * Every page gets a record, because a card title is a judgement about what the page is
 * for and no rule derives one.
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
    title: "Four portfolios, from plain to ambitious",
    alt: `${SITE_NAME}: four portfolios built from cheap funds, what each one costs, how far it has fallen, and how sure the evidence is.`,
  },
  "/portfolios/": {
    title: "The four portfolios, side by side",
    alt: `${SITE_NAME}: all four side by side, with what each costs, what it adds, the worst thing that has happened to it, and which one is yours.`,
  },
  "/portfolios/one-fund/": {
    title: "The whole world in one fund",
    alt: `${SITE_NAME}: one fund that owns every listed company in the world, and why 90% of professionals could not beat it.`,
  },
  "/portfolios/held-well/": {
    title: "The same fund, held well",
    alt: `${SITE_NAME}: the same holding as portfolio one, with four habits that are arithmetic rather than forecast.`,
  },
  "/portfolios/value-lean/": {
    title: "A lean toward cheaper companies",
    alt: `${SITE_NAME}: six funds that shift the stock holdings toward cheap and profitable companies, what that was worth, and the decade it can cost you.`,
  },
  "/portfolios/with-trend/": {
    title: "The same, plus a fund that can rise when stocks fall",
    alt: `${SITE_NAME}: seven funds, one of which holds trend following on top of stocks; the largest bet on this site and the least settled.`,
  },
  "/strategies/": {
    title: "Does it earn its place in a portfolio?",
    alt: `${SITE_NAME}: every idea people add to a portfolio, with a one-line verdict on whether it earns its place.`,
  },
  "/strategies/trend-following/": {
    title: "Does trend following earn its place?",
    alt: `${SITE_NAME}: what a managed-futures fund does, why it helps as an add-on and not a replacement, and which fund you pick decides the outcome.`,
  },
  "/strategies/market-timing/": {
    title: "Should you sell below the 200-day average?",
    alt: `${SITE_NAME}: the 200-day rule and leveraged funds, what they buy, what they cost, and the verdict.`,
  },
  "/strategies/gold-and-bitcoin/": {
    title: "Gold and bitcoin",
    alt: `${SITE_NAME}: gold is optional and small; bitcoin deepened every fall it was added to.`,
  },
  "/strategies/crash-insurance/": {
    title: "Can you buy insurance against a crash?",
    alt: `${SITE_NAME}: tail funds, buffer funds, bonds and cash, and which of them actually helped in bad months.`,
  },
  "/strategies/value-and-momentum/": {
    title: "Do cheaper companies pay more?",
    alt: `${SITE_NAME}: value and momentum on paper and in real funds, and why the lean is a probably rather than a yes.`,
  },
  "/strategies/international/": {
    title: "How much to hold outside the US",
    alt: `${SITE_NAME}: why hold foreign stocks, the 60/40 rule, and why you never sell to move.`,
  },
  "/strategies/fees-and-taxes/": {
    title: "The part that isn’t a guess",
    alt: `${SITE_NAME}: fees, fund structure, which account, direct indexing and rebalancing: the parts that are arithmetic.`,
  },
  "/funds/": {
    title: "What every fund really costs",
    alt: `${SITE_NAME}: every fund priced, and what each one costs once the income it earns lending its shares out is taken off the fee.`,
  },
  "/tools/which-account/": {
    title: "Which account should each fund go in?",
    alt: `${SITE_NAME}: the account calculator, ranking the seven funds by what putting each in a sheltered account saves.`,
  },
  "/about/": {
    title: "About this site and the person who writes it",
    alt: `${SITE_NAME}: who writes this, how the measuring works, and what stands in place of a credential.`,
  },
  "/corrections/": {
    title: "What I published that turned out to be wrong",
    alt: `${SITE_NAME}: the corrections log, dated, one line each.`,
  },
  "/disclosures/": {
    title: "Nobody pays for this site",
    alt: `${SITE_NAME}: no advertising, no affiliate links and no sponsors, and the interests that do exist.`,
  },
  "/disclaimer/": {
    title: "General information, and never advice",
    alt: `${SITE_NAME}: the full disclaimer: general, impersonal, and not an answer about your own portfolio.`,
  },
  "/search/": {
    title: "Search the whole site",
    alt: `${SITE_NAME}: search every page, including the ones about what did not work.`,
  },
  "/404/": {
    title: "That page is not here",
    alt: `${SITE_NAME}: the page you asked for does not exist on this site.`,
  },

} as const satisfies Readonly<Record<string, OgPage>>;

/** Indexable by an arbitrary path, without losing the literal keys above. */
const PAGES: Readonly<Record<string, OgPage | undefined>> = OG_PAGES;

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
