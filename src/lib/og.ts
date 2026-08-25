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

import { clamp } from "~/lib/research";
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
  "/start/": {
    title: "Start here",
    alt: `${SITE_NAME}: the ordered checklist, fees first and clever construction last.`,
  },
  "/stacking/": {
    title: "Why more good bets stop helping",
    alt: `${SITE_NAME}: the stacking ceiling, and why the funding rule decides everything.`,
  },
  "/how-many-bets/": {
    title: "How many different bets you can buy",
    alt: `${SITE_NAME}: four or five genuinely different sources of return exist, not twenty, and the whole exercise is worth 1.5 to 2 points a year.`,
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
  "/portfolio/": {
    title: "The portfolio",
    alt: `${SITE_NAME}: seven holdings and the account each one belongs in.`,
  },
  "/doesnt-work/": {
    title: "Things we tested that did not earn a place",
    alt: `${SITE_NAME}: the rejections, each scoped to the design that produced it.`,
  },
  "/how-sure/": {
    title: "How sure we are",
    alt: `${SITE_NAME}: the four levels of confidence, and how long before you would know.`,
  },
  "/funds/": {
    title: "The shelf",
    alt: `${SITE_NAME}: the audited fund shelf, on cost rather than on fee.`,
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
  "/research/": {
    title: "The research",
    alt: `${SITE_NAME}: the research corpus, one synthesis per question.`,
  },
  "/tools/": {
    title: "Two calculators, and what each one answers",
    alt: `${SITE_NAME}: the two calculators — which account each fund belongs in, and how long a choice takes to show.`,
  },
  "/tools/placement/": {
    title: "Where to hold each fund",
    alt: `${SITE_NAME}: the account-placement calculator, ranking the shelf by what a sheltered dollar of it saves.`,
  },
  "/tools/how-long/": {
    title: "How long before you would know",
    alt: `${SITE_NAME}: the waiting calculator — an expected edge and a drift, in; the years before your own account could tell, out.`,
  },
  "/lessons/": {
    title: "What we’ve learned",
    alt: `${SITE_NAME}: seventeen claims worth having straight before the rest of the site is any use.`,
  },
  "/glossary/": {
    title: "Every word this site leans on",
    alt: `${SITE_NAME}: the glossary — one line, then the paragraph behind it, then why it would change what you do.`,
  },
  "/about/": {
    title: "About this site and the person who writes it",
    alt: `${SITE_NAME}: who writes this, and what stands in place of a credential nobody here holds.`,
  },
  "/methodology/": {
    title: "How a result earns its status here",
    alt: `${SITE_NAME}: frozen specifications, a ledger that records the failures, and costs inside the trading rule.`,
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

/** `/research/:id/` and `/research/decisions/:id/`, the two rendered corpus routes. */
const CORPUS_ROUTE = /^\/research\/(?<decision>decisions\/)?[^/]+\/$/;

/**
 * Where a corpus title stops being a title and starts being a sentence.
 *
 * The renderer never clips: `fitTitle` shrinks the type until the words fit four
 * lines, so a long title is set small rather than cut. Small is still the wrong
 * answer on a card that will be seen at the size of a playing card, and half the
 * corpus writes its heading as a head and a subtitle — "Live managed futures: what
 * the funds actually paid, and what the vendor index overstated" — where the head
 * alone is the better card and loses nothing a reader needed.
 */
const TITLE_SPLIT = 72;

/** The point past which even an unsubtitled title is cut on a word boundary. */
const TITLE_LIMIT = 96;

/** A head short enough to be a bare topic — "Trend" — is not a title. Keep the whole. */
const MIN_HEAD = 16;

/**
 * A corpus document's own heading, cut to something the card can set large.
 *
 * Applied by both halves of the pairing: `src/pages/og/[...route].ts` draws this and
 * {@link ogCard} describes it, so the alt text cannot describe a card that says
 * something else.
 */
export function ogCorpusTitle(title: string): string {
  if (title.length <= TITLE_SPLIT) return title;
  const head = title.split(": ")[0];
  if (head && head.length >= MIN_HEAD && head.length < title.length) return head;
  return clamp(title, TITLE_LIMIT);
}

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
 * `title` is the page's own title, which is all a corpus route needs: its card is
 * drawn from the same string. It is ignored for a page listed in {@link OG_PAGES},
 * whose card says whatever that record says.
 */
export function ogCard(pathname: string, title: string): OgCard {
  const path = canonicalPath(pathname);

  const page = PAGES[path];
  if (page) return { src: ogImagePath(path), alt: page.alt };

  const corpus = CORPUS_ROUTE.exec(path);
  if (corpus) {
    const kind = corpus.groups?.decision ? "decision record" : "working note";
    return {
      src: ogImagePath(path),
      // A full stop rather than a dash. Several corpus headings carry an em dash of
      // their own, and two in one sentence read as one clause too many.
      alt: `${SITE_NAME}: ${ogCorpusTitle(title)}. A ${kind} from the research corpus behind this site.`,
    };
  }

  throw new Error(
    `${path} has no social card. Add a record for it to OG_PAGES in src/lib/og.ts, ` +
      "which is what puts a card in dist/og/ and a matching og:image on the page. " +
      "Falling back to another page's card is what this throw exists to prevent."
  );
}
