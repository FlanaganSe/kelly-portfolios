import path from "node:path";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import solid from "@astrojs/solid-js";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "astro/config";

// The site is a static bundle. Every page is HTML on disk, readable and indexable
// with JavaScript switched off; interactivity arrives as Solid islands only where a
// reader can actually type something.
//
// The markdown pipeline is left on Astro 7's default (`satteri()`, the Rust processor).
// Nothing here needs a remark or rehype plugin, and the default already carries GFM,
// smart punctuation and heading IDs. If a plugin ever becomes necessary, import
// `unified` from `@astrojs/markdown-remark`, set it as `markdown.processor`, and MDX
// inherits it — `@astrojs/mdx` reads `config.markdown.processor` on its own.
export default defineConfig({
  site: "https://kellyportfolios.com",
  output: "static",
  outDir: "./dist",
  // Directory format plus `ignore` is the host-portable pair: every page lands as
  // `dist/<route>/index.html`, which GitHub Pages, S3 and every CDN serve without a
  // rewrite rule. `never` plus file format depends on the host stripping `.html`.
  trailingSlash: "ignore",
  integrations: [mdx(), solid(), sitemap()],
  vite: {
    plugins: [tailwindcss()],
    resolve: {
      alias: {
        "~": path.resolve(import.meta.dirname, "./src"),
      },
    },
  },
});
