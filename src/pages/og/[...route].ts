/**
 * Emits one 1200×630 social card per page the site renders, at build time.
 *
 * The drawing is `~/lib/og-card`, which explains the composition and why this is not
 * `astro-og-canvas` any more. This file is only the routing: it turns a page path into
 * the file name `ogImagePath` promises, so `/stacking/` lands at `/og/stacking.png`,
 * `/tools/placement/` at `/og/tools/placement.png` and `/` at `/og/index.png`.
 *
 * Two sources, matching the two halves of `~/lib/og`. The hand-written pages come from
 * `OG_PAGES`; the corpus comes from the content collections, so a synthesis added to
 * `docs/research/` gets a card with its own name on it without anybody editing a list.
 * Both halves derive their route the same way `ogCard` does, which is what stops a page
 * from advertising a card that was never drawn.
 *
 * `scripts/check-og-size.mjs` runs after the build and fails it if any card passes
 * Bluesky's 1,000,000-byte cap, which binds long before anybody else's.
 */

import { getCollection } from "astro:content";
import type { APIRoute, GetStaticPaths } from "astro";
import { OG_PAGES, ogCorpusTitle, ogRouteParam } from "~/lib/og";
import { renderCard } from "~/lib/og-card";
import { decisionHref, researchHref, researchTitle } from "~/lib/research";

export const getStaticPaths = (async () => {
  // The same filter the two corpus routes apply. A draft has no page, so it gets no
  // card; drawing one would put an image in `dist/` that nothing on the site points at.
  const published = (entry: { data: { draft?: boolean } }) => entry.data.draft !== true;

  const corpus = [
    ...(await getCollection("research", published)).map((entry) => [researchHref(entry.id), entry] as const),
    ...(await getCollection("decisions", published)).map((entry) => [decisionHref(entry.id), entry] as const),
  ];

  return [
    ...Object.entries(OG_PAGES).map(([path, page]) => ({
      params: { route: ogRouteParam(path) },
      props: { title: page.title },
    })),
    ...corpus.map(([href, entry]) => ({
      params: { route: ogRouteParam(href) },
      props: { title: ogCorpusTitle(researchTitle(entry)) },
    })),
  ];
}) satisfies GetStaticPaths;

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
