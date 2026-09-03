import { readdirSync } from "node:fs";
import path from "node:path";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import solid from "@astrojs/solid-js";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "astro/config";
import pagefind from "astro-pagefind";

// The site is a static bundle. Every page is HTML on disk, readable and indexable
// with JavaScript switched off; interactivity arrives as Solid islands only where a
// reader can actually type something.
//
// The markdown pipeline is left on Astro 7's default (`satteri()`, the Rust processor).
// Nothing here needs a remark or rehype plugin, and the default already carries GFM,
// smart punctuation and heading IDs. If a plugin ever becomes necessary, import
// `unified` from `@astrojs/markdown-remark`, set it as `markdown.processor`, and MDX
// inherits it — `@astrojs/mdx` reads `config.markdown.processor` on its own.
/**
 * Every route the rendered research corpus used to occupy, pointing at `/strategies/`.
 *
 * Read from the directories rather than written out, because the list was 45 long and a
 * hand-typed copy would rot the first time a file was renamed. The files themselves stay
 * in the repository as the provenance a figure's `docPath` names; they are simply not
 * published any more.
 */
function retiredCorpusRoutes() {
  const ids = (dir) =>
    readdirSync(path.resolve(import.meta.dirname, dir))
      .filter((name) => name.endsWith(".md") && name !== "README.md")
      .map((name) => name.replace(/\.md$/, ""));

  return Object.fromEntries([
    ...ids("docs/research").map((id) => [`/research/${id}/`, "/strategies/"]),
    ...ids("docs/decisions").map((id) => [`/research/decisions/${id}/`, "/strategies/"]),
  ]);
}

export default defineConfig({
  // Canonical, Open Graph and sitemap URLs are all built from this. Without it they
  // emit relative, and `Astro.url` cannot stand in: its origin is localhost in dev.
  site: "https://kellyportfolios.com",
  output: "static",
  outDir: "./dist",

  // On a static build `trailingSlash` governs the dev server and on-demand routes; it
  // redirects nothing on a CDN. So the job here is to pick one form and emit only that
  // one, which `always` plus directory format does: every page lands as
  // `dist/<route>/index.html` and every internal link carries the slash. The host is
  // what turns the other form into a redirect rather than a second indexed URL, and
  // `docs/deploying.md` records how to check that it does.
  trailingSlash: "always",
  build: {
    format: "directory",
  },

  // Astro 7 changed the default to `'jsx'`, which strips whitespace between inline
  // elements. On a page of prose that eats the space before a link or an emphasis, so
  // this is pinned to the old behaviour. Verified in a rendered screenshot, not in the
  // build log: the difference is invisible in the HTML unless you go looking for it.
  compressHTML: true,

  // Every route the rewrite retired, pointed at whatever now answers the same question.
  //
  // On a static build Astro emits a small meta-refresh page per entry rather than a 301,
  // which is what this host can serve: the CloudFront function in front of the bucket
  // resolves directory indexes and does not read a redirect table. A meta refresh keeps
  // an old bookmark, an old search result and an old inbound link working, and search
  // engines follow it. The alternative was several hundred 404s on the day of the switch.
  redirects: {
    "/start/": "/portfolios/held-well/",
    "/portfolio/": "/portfolios/with-trend/",
    "/stacking/": "/strategies/value-and-momentum/",
    "/how-many-bets/": "/strategies/value-and-momentum/",
    "/doesnt-work/": "/strategies/",
    "/how-sure/": "/about/",
    "/methodology/": "/about/",
    "/lessons/": "/strategies/",
    "/glossary/": "/strategies/",
    "/tools/": "/tools/which-account/",
    "/tools/how-long/": "/strategies/",
    // A redirect that names a route a page still occupies replaces that page with a
    // stub, silently. These come on in wave 2, one per page deleted. Uncomment each line
    // with the page it retires.
    // "/tools/placement/": "/tools/which-account/",
    "/research/": "/strategies/",
    // The evidence pages became the strategies pages.
    // "/evidence/": "/strategies/",
    // "/evidence/how-many-bets/": "/strategies/value-and-momentum/",
    // "/evidence/value-and-factors/": "/strategies/value-and-momentum/",
    // "/evidence/what-actually-diversifies/": "/strategies/crash-insurance/",
    // "/evidence/crash-insurance/": "/strategies/crash-insurance/",
    // "/evidence/bitcoin/": "/strategies/gold-and-bitcoin/",
    // "/evidence/gold/": "/strategies/gold-and-bitcoin/",
    // "/evidence/market-timing/": "/strategies/market-timing/",
    // "/evidence/trend-following/": "/strategies/trend-following/",
    // "/evidence/rebalancing/": "/strategies/fees-and-taxes/",
    // "/evidence/direct-indexing/": "/strategies/fees-and-taxes/",
    // "/evidence/fees-and-accounts/": "/strategies/fees-and-taxes/",
    // "/portfolios/whole-market/": "/portfolios/one-fund/",
    // The 45 corpus routes, enumerated from the files they were built from. A dynamic
    // redirect may not drop its parameter, and these all collapse to one destination,
    // so they are listed rather than matched.
    ...retiredCorpusRoutes(),
  },

  // `hover` warms a page the reader has aimed at, and falls back to `tap` under
  // Save-Data or on a slow connection. Hand-written speculation rules cannot make that
  // judgement, which is the argument for using the built-in over rolling one.
  prefetch: {
    defaultStrategy: "hover",
    prefetchAll: true,
  },

  integrations: [
    mdx(),
    solid(),
    sitemap({
      // Google documents that it ignores `changefreq` and `priority`, so emitting them
      // is noise a crawler has to skip. `lastmod` is left off rather than guessed: an
      // inaccurate one is worse than none, because the trust is conditional on the
      // dates being right every time.
      serialize: ({ url }) => ({ url }),
      namespaces: { news: false, video: false, image: false, xhtml: false },
    }),
    // Indexes `dist/` after the build and serves `/pagefind/` in dev, so a search page
    // works the same in both. The UI is Pagefind's own component set, from
    // `@pagefind/component-ui`; see `astro-pagefind/components/PagefindConfig.astro`.
    pagefind(),
  ],

  vite: {
    plugins: [tailwindcss()],
    resolve: {
      alias: {
        "~": path.resolve(import.meta.dirname, "./src"),
      },
    },
  },
});
