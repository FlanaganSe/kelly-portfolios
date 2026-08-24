/**
 * Generates one 1200×630 social card per entry in {@link OG_PAGES}, at build time.
 *
 * `astro-og-canvas` draws with CanvasKit rather than a headless browser, so there is no
 * Chromium in the build and the results are cached in `node_modules/.astro-og-canvas`
 * across builds. Nothing here reads a WOFF2: neither CanvasKit nor Satori can, so a
 * specific face would have to arrive as a TTF or an OTF subset. The card uses CanvasKit's
 * own default family instead, which is the honest trade for not committing a font binary
 * to render four cards.
 *
 * The palette is the site's light theme, hard-coded: a social card is composited on
 * whatever background the reader's client uses, so it cannot follow a theme.
 */
import { OGImageRoute } from "astro-og-canvas";
import { OG_PAGES, type OgPage } from "~/lib/og";
import { SITE_NAME } from "~/lib/site";

/** `--paper`, `--ink`, `--ink-muted` and `--accent`, as RGB triples. */
const PAPER: [number, number, number] = [250, 249, 246];
const INK: [number, number, number] = [26, 25, 23];
const INK_MUTED: [number, number, number] = [87, 84, 77];
const ACCENT: [number, number, number] = [18, 80, 127];

// No `param` option: 0.13 reads the parameter name out of the route pattern itself, so
// this file's name is what binds it to `[...route]`.
export const { getStaticPaths, GET } = await OGImageRoute({
  pages: OG_PAGES as Record<string, OgPage>,
  getSlug: (path) => (path === "/" ? "index.png" : `${path.replace(/^\/|\/$/g, "")}.png`),
  getImageOptions: (_path, page) => ({
    title: page.title,
    description: `${page.description}\n\n${SITE_NAME}`,
    padding: 72,
    bgGradient: [PAPER],
    border: { color: ACCENT, width: 16, side: "inline-start" },
    font: {
      title: { color: INK, size: 66, weight: "Bold", lineHeight: 1.15 },
      description: { color: INK_MUTED, size: 30, lineHeight: 1.4 },
    },
    format: "PNG",
  }),
});
