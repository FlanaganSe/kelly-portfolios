/**
 * Site-wide constants and the primary navigation, in reading order.
 *
 * Five items, and the order is the argument: the four portfolios, the ideas people add
 * to one and whether each earns its place, what the funds cost, how to hold the
 * portfolio you pick, and who is saying all this. The pages about the site itself live
 * in the footer, which is where an errand belongs.
 *
 * The site's own origin is not here. It is `site` in `astro.config.mjs`, which the
 * sitemap also reads, and a page reaches it through `Astro.site`.
 */

export const SITE_NAME = "Kelly Portfolios";

export const SITE_DESCRIPTION =
  "Four portfolios you can actually buy, tested as whole portfolios: what $10,000 became, the worst fall in dollars, the cost a year, and how sure the evidence is.";

export const REPO_URL = "https://github.com/FlanaganSe/kelly-portfolios";

export interface NavItem {
  readonly href: string;
  readonly label: string;
}

/**
 * Every href carries its trailing slash, because the build emits only that form
 * (`trailingSlash: "always"`). A link without one costs the reader a redirect.
 */
export const NAV_ITEMS = [
  { href: "/portfolios/", label: "Portfolios" },
  { href: "/strategies/", label: "Strategies" },
  { href: "/funds/", label: "Funds" },
  { href: "/how-to-hold/", label: "How to hold" },
  { href: "/about/", label: "About" },
] as const satisfies readonly NavItem[];

/** The footer's own links. A reader reaches these on a different errand. */
export const FOOTER_ITEMS = [
  { href: "/disclaimer/", label: "Disclaimer" },
  { href: "/search/", label: "Search" },
] as const satisfies readonly NavItem[];

const MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
] as const;

/**
 * A `YYYY-MM-DD` date as a reader writes one: `"2026-09-05"` is "September 5, 2026".
 * Anything else is handed back untouched, so a page that passes its own text still prints.
 */
export function asOfLabel(iso: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (match === null) return iso;
  const month = MONTHS[Number(match[2]) - 1];
  if (month === undefined) return iso;
  return `${month} ${Number(match[3])}, ${match[1]}`;
}

/** A `YYYY-MM` month as a reader writes one: `"2007-10"` is "October 2007". */
export function monthLabel(yearMonth: string): string {
  const match = /^(\d{4})-(\d{2})$/.exec(yearMonth);
  if (match === null) return yearMonth;
  const month = MONTHS[Number(match[2]) - 1];
  if (month === undefined) return yearMonth;
  return `${month} ${match[1]}`;
}

/** Drops any trailing slash, so the two URL forms compare equal. */
function bare(pathname: string): string {
  return pathname.replace(/\/+$/, "") || "/";
}

/** True when `href` is the current page or an ancestor of it. */
export function isCurrent(href: string, pathname: string): boolean {
  const here = bare(pathname);
  const target = bare(href);
  if (target === "/") return here === "/";
  return here === target || here.startsWith(`${target}/`);
}

/** The canonical form of a path: exactly one trailing slash. */
export function canonicalPath(pathname: string): string {
  const here = bare(pathname);
  return here === "/" ? "/" : `${here}/`;
}
