/** The primary navigation, in reading order. */
export const NAV_ITEMS = [
  { href: "/", label: "Start here" },
  { href: "/portfolios", label: "Portfolios" },
  { href: "/research", label: "Research" },
  { href: "/funds", label: "Funds" },
  { href: "/lab", label: "Lab" },
  { href: "/concepts", label: "Concepts" },
  { href: "/method", label: "Method" },
] as const satisfies readonly { href: string; label: string }[];

/**
 * The original long-form pages, still canonical for what they cover and reached from
 * the research index rather than from the masthead. They pre-date the portfolio layer
 * and none of their content is duplicated into it.
 */
export const DEEP_PAGES = [
  { href: "/reference", label: "The reference construction" },
  { href: "/edge-budget", label: "The edge budget, line by line" },
  { href: "/placement", label: "Where each holding is held" },
  { href: "/confidence", label: "How long until you would know" },
  { href: "/evidence", label: "Every experiment and its status" },
] as const satisfies readonly { href: string; label: string }[];

export type NavItem = (typeof NAV_ITEMS)[number];

/** The date the research corpus was last read for this site. */
export const CORPUS_AS_OF = "2026-08-17";

export const REPO_URL = "https://github.com/FlanaganSe/investing-portfolio";
