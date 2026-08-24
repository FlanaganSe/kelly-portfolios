/**
 * Site-wide constants and the primary navigation, in reading order.
 *
 * The order is the argument, and it runs concrete before abstract: what to do, then
 * what to choose between, then why holding more good things stops helping, then what
 * failed, then how sure any of it is.
 *
 * Stacking used to sit second. It is the most abstract page here, and a reader working
 * left to right met it before they had seen a single holding.
 *
 * `/portfolios/` holds the second slot rather than `/portfolio/`, which used to. The
 * singular page prescribes one construction, and a reader arriving from `/start/` has
 * not yet been given a choice to make. The plural page lays the options out in order of
 * how much of each case is arithmetic and hands off to the singular one for the detail,
 * so `/portfolio/` is still reachable in one click and is no longer the only answer on
 * offer. The bar stays at eight items: a ninth would not survive the narrow breakpoint.
 *
 * The site's own origin is not here. It is `site` in `astro.config.mjs`, which the
 * sitemap also reads, and a page reaches it through `Astro.site`.
 */

export const SITE_NAME = "Kelly Portfolios";

export const SITE_DESCRIPTION =
  "What to do with a portfolio, how sure we are about each part, and every test that failed. Fees, taxes and account placement first; the rest is honest about what it cannot show.";

export const REPO_URL = "https://github.com/FlanaganSe/kelly-portfolios";

/** The date the research corpus was last read for this site. */
export const CORPUS_AS_OF = "2026-08-17";

export interface NavItem {
  readonly href: string;
  readonly label: string;
}

/**
 * Every href carries its trailing slash, because the build emits only that form
 * (`trailingSlash: "always"`). A link without one costs the reader a redirect.
 *
 * Every item resolves to a page that exists. `/tools/` sits next to the funds it ranks
 * and before the research it runs on, because a reader who has read the argument and
 * wants their own numbers is at that point in the page order.
 */
export const NAV_ITEMS = [
  { href: "/start/", label: "Start" },
  { href: "/portfolios/", label: "Portfolios" },
  { href: "/stacking/", label: "Stacking" },
  { href: "/doesnt-work/", label: "What doesn't work" },
  { href: "/how-sure/", label: "How sure" },
  { href: "/funds/", label: "Funds" },
  { href: "/tools/", label: "Tools" },
  { href: "/research/", label: "Research" },
] as const satisfies readonly NavItem[];

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
