/**
 * Site-wide constants and the primary navigation, in reading order.
 *
 * The order is the argument: what to do, then the mechanism that makes it work, then
 * the construction, then what failed, then how sure any of it is.
 */

export const SITE_NAME = "Kelly Portfolios";

export const SITE_URL = "https://kellyportfolios.com";

export const SITE_DESCRIPTION =
  "What to do with a portfolio, how sure we are about each part, and every test that failed. Fees, taxes and account placement first; the rest is honest about what it cannot show.";

export const REPO_URL = "https://github.com/FlanaganSe/kelly-portfolios";

/** The date the research corpus was last read for this site. */
export const CORPUS_AS_OF = "2026-08-17";

export interface NavItem {
  readonly href: string;
  readonly label: string;
}

export const NAV_ITEMS = [
  { href: "/start", label: "Start" },
  { href: "/stacking", label: "Stacking" },
  { href: "/portfolio", label: "Portfolio" },
  { href: "/doesnt-work", label: "What doesn't work" },
  { href: "/how-sure", label: "How sure" },
  { href: "/funds", label: "Funds" },
  { href: "/tools", label: "Tools" },
  { href: "/research", label: "Research" },
] as const satisfies readonly NavItem[];

/** True when `href` is the current page or an ancestor of it. */
export function isCurrent(href: string, pathname: string): boolean {
  const here = pathname.replace(/\/+$/, "") || "/";
  if (href === "/") return here === "/";
  return here === href || here.startsWith(`${href}/`);
}
