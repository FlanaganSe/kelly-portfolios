/**
 * Site-wide constants and the primary navigation, in reading order.
 *
 * The order is the argument: what to do, then the mechanism that makes it work, then
 * the construction, then what failed, then how sure any of it is.
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
 * Every item resolves to a page that exists. `/tools/` is not here: the calculators are
 * still Solid routes in the client being ported from, and a masthead link into a 404 is
 * worse than a missing one. Add it back with the page.
 */
export const NAV_ITEMS = [
  { href: "/start/", label: "Start" },
  { href: "/stacking/", label: "Stacking" },
  { href: "/portfolio/", label: "Portfolio" },
  { href: "/doesnt-work/", label: "What doesn't work" },
  { href: "/how-sure/", label: "How sure" },
  { href: "/funds/", label: "Funds" },
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
