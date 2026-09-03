/**
 * Site-wide constants and the primary navigation, in reading order.
 *
 * Four items, and the order is the argument: what to hold, the ideas people add to it
 * and whether each earns its place, what the funds cost, and who is saying all this. The
 * calculator and the pages about the site live in the footer, which is where an errand
 * belongs.
 *
 * The site's own origin is not here. It is `site` in `astro.config.mjs`, which the
 * sitemap also reads, and a page reaches it through `Astro.site`.
 */

export const SITE_NAME = "Kelly Portfolios";

export const SITE_DESCRIPTION =
  "Three portfolios built from cheap funds, from plain to ambitious, with what each one costs, how far it has fallen, and how sure the evidence is. Plus a verdict on every idea people bolt onto a portfolio.";

export const REPO_URL = "https://github.com/FlanaganSe/kelly-portfolios";

/** The date the numbers on the site were last checked against the research. */
export const CORPUS_AS_OF = "2026-09-02";

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
  { href: "/about/", label: "About" },
] as const satisfies readonly NavItem[];

/**
 * The footer's own links: the calculator, then the pages about the site itself. None of
 * these belongs in the masthead; a reader reaches them on a different errand.
 */
export const FOOTER_ITEMS = [
  { href: "/tools/which-account/", label: "Which account" },
  { href: "/corrections/", label: "Corrections" },
  { href: "/disclosures/", label: "Disclosures" },
  { href: "/disclaimer/", label: "Disclaimer" },
  { href: "/search/", label: "Search" },
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
