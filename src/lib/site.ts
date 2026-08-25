/**
 * Site-wide constants and the primary navigation, in reading order.
 *
 * Five items, and the order is the argument: what to hold, what it can be built from,
 * what the evidence behind it says, the calculators that run it at a reader's own
 * numbers, and who is saying all this. It ran to eight, which meant a reader had to
 * choose between eight destinations before reading a sentence; the pages that lost
 * their slot are reachable from the body of the page that needs them and from the
 * footer, which is where an errand belongs.
 *
 * `/portfolios/` leads rather than `/portfolio/`. The singular page prescribes one
 * construction and the plural one lays the options out, so the plural is the honest
 * front door and the singular is one click inside it.
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
 * Tools points at `/tools/placement/` rather than at the index above it. Placement is
 * the calculator a reader is actually looking for, and an index page whose whole
 * content is two links is a stop on the way rather than a destination.
 */
export const NAV_ITEMS = [
  { href: "/portfolios/", label: "Portfolios" },
  { href: "/funds/", label: "Funds" },
  { href: "/evidence/", label: "Evidence" },
  { href: "/tools/placement/", label: "Tools" },
  { href: "/about/", label: "About" },
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
