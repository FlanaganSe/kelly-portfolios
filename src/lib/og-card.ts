/**
 * Draws one 1200×630 social card, at build time, with no network call in it.
 *
 * **Why this is not `astro-og-canvas`.** That package stacks logo, title and
 * description down from the top padding edge and clamps the block to within one
 * padding of it, so the lower half of every card was empty whatever the title said.
 * It also defaults `fonts` to `https://api.fontsource.org/…/noto-sans/…ttf`, which
 * made a cold-cache build depend on somebody else's host being up. Both are
 * structural: the layout is not configurable and the default is a fetch. So the card
 * is composed here instead, over the CanvasKit that package was already pulling in.
 *
 * **The font trap.** Neither CanvasKit nor Satori can read a WOFF2. The two faces in
 * `src/assets/fonts/` are TTFs, read off disk, and their licences sit beside them.
 *
 * **The composition.** A wordmark and a rule at the top, the title set as large as it
 * can be and optically centred in the band between the rules, the site's own domain
 * on a rule at the bottom. The type sizes are the site's own relations — a serif
 * heading over a letter-spaced sans eyebrow — and the palette is the light theme,
 * hard-coded, because a social card is composited on whatever background the reader's
 * client uses and cannot follow a theme.
 *
 * The description is deliberately not drawn. Every client that renders one of these
 * also renders `og:description` as text beside it, so a second copy inside the image
 * buys nothing and was most of what made the old card look like a form.
 */
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import type { Canvas, CanvasKit, FontMgr, Paragraph } from "canvaskit-wasm";
import { OG_HEIGHT, OG_WIDTH } from "~/lib/og";
import { SITE_NAME } from "~/lib/site";

/** `--paper`, `--ink`, `--ink-muted`, `--rule-strong` and `--accent`, as RGB triples. */
const PAPER = [250, 249, 246] as const;
const INK = [26, 25, 23] as const;
const INK_MUTED = [87, 84, 77] as const;
const RULE_STRONG = [201, 197, 185] as const;
const ACCENT = [18, 80, 127] as const;

/** The accent stripe down the leading edge, as wide as the old card's border. */
const STRIPE = 16;
const PAD = 72;

/** The reading column: inside the stripe on the left, inside the padding on the right. */
const LEFT = STRIPE + PAD;
const RIGHT = OG_WIDTH - PAD;
const COLUMN = RIGHT - LEFT;

/** The two rules, and the band between them the title is centred in. */
const TOP_RULE_Y = 126;
const BOTTOM_RULE_Y = OG_HEIGHT - 118;

/**
 * Text sits a little high to read as centred. Two percent of the band is the usual
 * correction and it is what this uses; it is a judgement, checked in a rendered card
 * rather than derived.
 */
const OPTICAL_LIFT = Math.round((BOTTOM_RULE_Y - TOP_RULE_Y) * 0.02);

/**
 * How far Source Serif 4's ascenders reach above the baseline, as a fraction of the
 * em. Measured off a rendered card rather than read out of the font: 76px of ink above
 * the baseline at a 104px size.
 *
 * Centring a paragraph on its *line boxes* puts a title visibly high in the band,
 * because the leading above the ascenders and the descender space below are both
 * empty. Centring the ink instead — ascender height down to the last baseline, whether
 * or not this particular title happens to have a descender — puts every card in the
 * same place. A title that does descend then sits a few pixels high, which is the
 * direction the eye forgives.
 */
const ASCENDER = 0.73;

/**
 * The title is set as large as it can be without running past three lines or out of
 * the band. Both ends of the range matter: without the ceiling a two-word title fills
 * the frame like a poster, and without the floor a long one overflows the rules.
 */
const TITLE_MAX = 104;
const TITLE_MIN = 46;
const TITLE_STEP = 2;
const TITLE_MAX_LINES = 4;
const TITLE_LINE_HEIGHT = 1.14;

/** Clear air the title keeps above and below itself, so it never crowds a rule. */
const TITLE_INSET = 44;

const FONT_DIR = "src/assets/fonts";
const FONT_FILES = ["SourceSerif4-Semibold-latin.ttf", "Inter-Semibold-latin.ttf"] as const;

/** The family names CanvasKit parses out of those two files. */
const SERIF = "Source Serif 4";
const SANS = "Inter";

const require_ = createRequire(import.meta.url);

let kitPromise: Promise<CanvasKit> | undefined;
let fontsPromise: Promise<FontMgr> | undefined;

async function getCanvasKit(): Promise<CanvasKit> {
  if (!kitPromise) {
    kitPromise = import("canvaskit-wasm/full").then(({ default: init }) =>
      init({ locateFile: (file: string) => require_.resolve(`canvaskit-wasm/bin/full/${file}`) })
    );
  }
  return kitPromise;
}

/**
 * The faces, off disk. Paths are resolved against the working directory, which is the
 * project root for both `astro dev` and `astro build`; a bundled module's own URL is
 * not, which is why this does not use `import.meta.url`.
 */
async function getFonts(kit: CanvasKit): Promise<FontMgr> {
  if (!fontsPromise) {
    fontsPromise = (async () => {
      const buffers = await Promise.all(
        FONT_FILES.map(async (name) => {
          const file = path.resolve(process.cwd(), FONT_DIR, name);
          try {
            const buffer = await readFile(file);
            // `readFile` hands back a view on a pooled allocation, and CanvasKit wants
            // an `ArrayBuffer` of its own. Copying is the honest way to give it one.
            const bytes = new ArrayBuffer(buffer.byteLength);
            new Uint8Array(bytes).set(buffer);
            return bytes;
          } catch (cause) {
            throw new Error(
              `${file} is missing. The social cards are drawn from committed TTFs — ` +
                "neither CanvasKit nor Satori can read a WOFF2 — and nothing is fetched at build time. " +
                "See src/assets/fonts/OFL.txt for what these files are.",
              { cause }
            );
          }
        })
      );
      const manager = kit.FontMgr.FromData(...buffers);
      if (!manager) throw new Error("CanvasKit could not parse the committed TTFs in src/assets/fonts/.");
      const families = new Set<string>();
      for (let i = 0; i < manager.countFamilies(); i += 1) families.add(manager.getFamilyName(i));
      for (const wanted of [SERIF, SANS]) {
        if (!families.has(wanted)) {
          throw new Error(
            `CanvasKit read the font files but found no family called "${wanted}" — ` +
              `it found ${[...families].join(", ")}. Rendering would silently fall back and the card would ` +
              "stop looking like the site."
          );
        }
      }
      return manager;
    })();
  }
  return fontsPromise;
}

interface EyebrowOptions {
  readonly text: string;
  readonly y: number;
  readonly color: readonly [number, number, number];
}

/**
 * A line of small letter-spaced capitals, the site's `eyebrow`. Drawn as a paragraph
 * rather than with `drawText` so it gets the same shaping as everything else.
 */
function drawEyebrow(kit: CanvasKit, canvas: Canvas, fonts: FontMgr, { text, y, color }: EyebrowOptions): void {
  const style = new kit.ParagraphStyle({
    textAlign: kit.TextAlign.Left,
    textStyle: {
      color: kit.Color(...color),
      fontFamilies: [SANS],
      fontSize: 23,
      letterSpacing: 2.4,
      heightMultiplier: 1,
    },
  });
  const builder = kit.ParagraphBuilder.Make(style, fonts);
  builder.addText(text.toUpperCase());
  const paragraph = builder.build();
  paragraph.layout(COLUMN);
  canvas.drawParagraph(paragraph, LEFT, y);
  paragraph.delete();
  builder.delete();
}

function buildTitle(kit: CanvasKit, fonts: FontMgr, title: string, size: number): Paragraph {
  const style = new kit.ParagraphStyle({
    textAlign: kit.TextAlign.Left,
    textStyle: {
      color: kit.Color(...INK),
      fontFamilies: [SERIF],
      fontSize: size,
      letterSpacing: size * -0.015,
      heightMultiplier: TITLE_LINE_HEIGHT,
    },
  });
  const builder = kit.ParagraphBuilder.Make(style, fonts);
  builder.addText(title);
  const paragraph = builder.build();
  paragraph.layout(COLUMN);
  builder.delete();
  return paragraph;
}

interface FittedTitle {
  readonly paragraph: Paragraph;
  readonly size: number;
}

/**
 * The largest size at which the title still fits the band in at most three lines.
 * Returns the built paragraph so the caller does not lay it out a second time.
 */
function fitTitle(kit: CanvasKit, fonts: FontMgr, title: string): FittedTitle {
  const band = BOTTOM_RULE_Y - TOP_RULE_Y - TITLE_INSET * 2;
  let fallback: FittedTitle | undefined;
  for (let size = TITLE_MAX; size >= TITLE_MIN; size -= TITLE_STEP) {
    const paragraph = buildTitle(kit, fonts, title, size);
    const lines = paragraph.getLineMetrics().length;
    if (lines <= TITLE_MAX_LINES && paragraph.getHeight() <= band) {
      fallback?.paragraph.delete();
      return { paragraph, size };
    }
    fallback?.paragraph.delete();
    fallback = { paragraph, size };
  }
  // Nothing fit. The smallest is still the least bad, and it is drawn rather than
  // thrown over: a card that overflows its rules is easier to notice than no card.
  return fallback ?? { paragraph: buildTitle(kit, fonts, title, TITLE_MIN), size: TITLE_MIN };
}

/** Where to draw the title so its ink, not its line boxes, sits in the band. */
function titleTop({ paragraph, size }: FittedTitle): number {
  const lines = paragraph.getLineMetrics();
  const first = lines[0];
  const last = lines[lines.length - 1];
  if (!first || !last) return TOP_RULE_Y;

  const inkTop = first.baseline - ASCENDER * size;
  const inkBottom = last.baseline;
  const band = BOTTOM_RULE_Y - TOP_RULE_Y;
  return TOP_RULE_Y + band / 2 - OPTICAL_LIFT - (inkTop + inkBottom) / 2;
}

export interface Card {
  readonly title: string;
  /**
   * The site's own host, printed along the bottom. It is passed in rather than kept
   * here because `site` in `astro.config.mjs` is where this project's origin lives,
   * and a second copy of it would be a second thing to get wrong.
   */
  readonly domain: string;
}

/** One card, as PNG bytes. */
export async function renderCard({ title, domain }: Card): Promise<Uint8Array<ArrayBuffer>> {
  const kit = await getCanvasKit();
  const fonts = await getFonts(kit);

  const surface = kit.MakeSurface(OG_WIDTH, OG_HEIGHT);
  if (!surface) throw new Error(`CanvasKit could not make a ${OG_WIDTH}×${OG_HEIGHT} surface.`);
  const canvas = surface.getCanvas();

  const fill = new kit.Paint();
  fill.setStyle(kit.PaintStyle.Fill);
  fill.setAntiAlias(true);

  fill.setColor(kit.Color(...PAPER));
  canvas.drawRect(kit.XYWHRect(0, 0, OG_WIDTH, OG_HEIGHT), fill);

  fill.setColor(kit.Color(...ACCENT));
  canvas.drawRect(kit.XYWHRect(0, 0, STRIPE, OG_HEIGHT), fill);

  fill.setColor(kit.Color(...RULE_STRONG));
  canvas.drawRect(kit.XYWHRect(LEFT, TOP_RULE_Y, COLUMN, 1.5), fill);
  canvas.drawRect(kit.XYWHRect(LEFT, BOTTOM_RULE_Y, COLUMN, 1.5), fill);

  drawEyebrow(kit, canvas, fonts, { text: SITE_NAME, y: TOP_RULE_Y - 46, color: INK });
  drawEyebrow(kit, canvas, fonts, { text: domain, y: BOTTOM_RULE_Y + 26, color: INK_MUTED });

  const heading = fitTitle(kit, fonts, title);
  canvas.drawParagraph(heading.paragraph, LEFT, titleTop(heading));
  heading.paragraph.delete();

  const image = surface.makeImageSnapshot();
  const bytes = image.encodeToBytes(kit.ImageFormat.PNG, 100);
  if (!bytes) throw new Error(`CanvasKit encoded no bytes for the card titled "${title}".`);

  // CanvasKit's array is a view on the WASM heap, so it has to be copied out before
  // anything below hands that memory back.
  const png = new Uint8Array(bytes.byteLength);
  png.set(bytes);

  image.delete();
  surface.dispose();
  fill.delete();
  return png;
}
