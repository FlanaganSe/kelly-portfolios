/** The primary navigation, in reading order. */
export const NAV_ITEMS = [
  { href: "/", label: "Start here" },
  { href: "/portfolio", label: "The portfolio" },
  { href: "/edge-budget", label: "Edge budget" },
  { href: "/placement", label: "Where it's held" },
  { href: "/confidence", label: "Confidence" },
  { href: "/evidence", label: "Evidence" },
  { href: "/concepts", label: "Concepts" },
  { href: "/method", label: "Method" },
] as const satisfies readonly { href: string; label: string }[];

export type NavItem = (typeof NAV_ITEMS)[number];

/** The date the research corpus was last read for this site. */
export const CORPUS_AS_OF = "2026-08-12";

export const REPO_URL = "https://github.com/FlanaganSe/investing-portfolio";
