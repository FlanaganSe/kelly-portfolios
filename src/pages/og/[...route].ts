/**
 * Emits one 1200×630 social card per entry in {@link OG_PAGES}, at build time.
 *
 * The drawing is `~/lib/og-card`, which explains the composition and why this is not
 * `astro-og-canvas` any more. This file is only the routing: it turns a page path into
 * the file name `ogImagePath` promises, so `/stacking/` lands at `/og/stacking.png`
 * and `/` at `/og/index.png`.
 *
 * `scripts/check-og-size.mjs` runs after the build and fails it if any card passes
 * Bluesky's 1,000,000-byte cap, which binds long before anybody else's.
 */
import type { APIRoute, GetStaticPaths } from "astro";
import { OG_PAGES } from "~/lib/og";
import { renderCard } from "~/lib/og-card";

export const getStaticPaths = (() =>
  Object.entries(OG_PAGES).map(([path, page]) => ({
    params: { route: path === "/" ? "index.png" : `${path.replace(/^\/|\/$/g, "")}.png` },
    props: { title: page.title },
  }))) satisfies GetStaticPaths;

export const GET: APIRoute<{ title: string }> = async ({ props, site }) => {
  // `site` is `https://kellyportfolios.com` from `astro.config.mjs`, the one place this
  // project's origin is written down. Without it configured there is no card to draw a
  // domain on, and a card that silently says nothing is worse than a failed build.
  if (!site) {
    throw new Error("`site` is unset in astro.config.mjs, so the social card has no domain to print.");
  }

  return new Response(await renderCard({ title: props.title, domain: site.host }), {
    headers: {
      "Content-Type": "image/png",
      "Cache-Control": "public, max-age=31536000, immutable",
    },
  });
};
