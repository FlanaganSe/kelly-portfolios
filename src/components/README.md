# Shared primitives

The component set every content page is built from. Use these rather than
hand-rolling markup, so a number looks the same on every page and a status never
gets glossed differently in two places.

## Astro components, which are what new pages use

These `.astro` components ship no JavaScript and are the ones a page should reach for.
The Solid components documented further down belong to the client-routed application
being ported from, and a new page should not import them.

### `Figure`

`{ id, size?: "sm" | "md" | "lg", inline?, showUnit?, class? }`. Looks the figure up by id in
the `figures` collection and throws at build time if no record exists, listing the ids
that do. Records live in `src/content/figures/<id>.yaml`; the id is the filename stem.

```astro
import Figure from "~/components/Figure.astro";
<Figure id="edge-vs-cheap-index" />
```

The block prints five things and no more: the label, the value with its unit, the
interval, the note and one source line. A record carries `label`, `value` (always a
string), `status`, `asOf` and a `source` with `label` and `docPath`, and may carry
`unit`, `interval`, `certainty`, `period`, `anchor` and `note`. The schema checks that `docPath` names a real file and that
`anchor` is a real heading inside it, so a renamed section fails `pnpm build`.

### Confidence

There is no component. A confidence reading is a word and a rule:

```astro
import { rungMeta } from "~/lib/rungs";

<p class="confidence" data-level="settled">
  <span class="confidence-word">{rungMeta.settled.label}</span>
  <span class="confidence-gloss">{rungMeta.settled.gloss}</span>
</p>
```

`data-level` is one of `settled`, `probably`, `might`, `cant-tell`, and it picks the ink
weight of the left rule. The gloss is optional. Labels and glosses live in
[`src/lib/rungs.ts`](../lib/rungs.ts); the four-state hand-drawn SVG mark that used to
sit beside the word is gone, because a mark a reader has to learn from another page is
not a reading.

### `Callout`

`{ kind, label?, class? }` where kind is `do-this` or `caveat`. A left rule and a label,
with the body in a slot. Two kinds and no more: a falsifier and an open question are
both caveats, and `label` is how one says which. Anything that explains why an effect
should exist is prose, not an aside.

### `Breakout`

`{ scroll?, heading?, level?, label?, maxWidth?, class? }` — a block allowed both tracks
of the canvas. Must be a direct child of the page canvas. `heading` prints a real `h2`
(or `h3` with `level={3}`) so the tables on a page are in its outline. `maxWidth` caps
any table inside through `--tw`: roughly 34rem for three columns, 44rem for a
comparison, 54rem for the shelf. `scroll` wraps the content in a keyboard-reachable
scroll region and then needs a `heading` or a `label` to name it.

### Two house rules these all follow

An internal `href` ends in a slash. The build emits one URL form, and a link missing the
slash is a redirect the reader pays for.

`node tools/prose-lint.mjs` reads `.astro` templates as prose and treats a bare `!` as
an exclamation mark. Write a positive prop and test it directly rather than negating
one in a template expression.

Types come from [`src/content/types.ts`](../content/types.ts). Nothing here
hardcodes a number, and nothing here reformats one: `value` and `interval` are
strings because the sign, the precision and the interval are part of the fact.

Import through the `~/*` alias:

```tsx
import { Figure } from "~/components/Figure";
```

## Layout and text

### `PageHeader`

`{ title, standfirst?, lastChecked?, eyebrow?, class? }` — h1, standfirst, and the
date the page was last checked against `docs/research/`.

```tsx
<PageHeader title="Edge budget" standfirst="What is available, line by line." lastChecked="2026-08-12" />
```

### `Prose`

`{ as?: "div" | "article" | "section", class? }` — the long-form wrapper. Caps the
measure at 70ch and styles headings, lists, links, `code` and `blockquote`. Write
plain HTML inside it. Anything that has to break the measure goes outside it.

```tsx
<Prose as="article"><p>The long-only capture fraction is about 0.520.</p></Prose>
```

## Numbers and evidence

### `DataTable`

`{ caption, columns, rows, captionHidden?, stickyHeader?, footnote?, class? }` —
a semantic table. Each column is
`{ key, header, cell, numeric?, width?, rowHeader? }`. Set `numeric` on every
number column: it right-aligns and applies tabular numerals. The table scrolls
sideways inside its own container, so the page body never does.

```tsx
<DataTable
  caption="Factor premia, pooled across regions"
  columns={[
    { key: "factor", header: "Factor", rowHeader: true, cell: (r) => r.name },
    { key: "premium", header: "pp/yr", numeric: true, cell: (r) => r.premium },
  ]}
  rows={factors}
/>
```

### `StatusChip` and `CertaintyChip`

`{ status: EvidenceStatus, showGloss?, class? }` and
`{ certainty: CertaintyClass, showGloss?, class? }` — label, tone mark and gloss,
read straight from `statusMeta` / `certaintyMeta`. Tone carries a distinct shape
as well as a colour, so it survives greyscale and a printout.

```tsx
<StatusChip status="rejected" showGloss />
```

### `SourceLink`

`{ citation: Citation, prefix?, class? }` — links a `docPath` to the file on
GitHub, or to `href` when the citation gives an external primary source. Opens in
a new tab.

```tsx
<SourceLink citation={{ label: "Long-only capture", docPath: "docs/research/long-only-capture.md" }} />
```

## Controls

Both are controlled. Hold the value in a signal and pass `onInput`.

### `NumberInput`

`{ label, value, onInput, min?, max?, step?, unit?, precision?, hint?, labelHidden?, disabled?, class? }`
— a labelled number field. Emits on every parseable keystroke and clamps to
`min`/`max` only on blur, so typing is never interrupted.

```tsx
<NumberInput label="Expense ratio" value={fee()} onInput={setFee} min={0} max={2} step={0.01} unit="%" />
```

### `Slider`

`{ label, value, onInput, min, max, step?, unit?, precision?, format?, hint?, ticks?, showBounds?, disabled?, class? }`
— a native range control, so arrow keys, Home, End and Page Up/Down all work.
`format` overrides the readout for values that are not plain decimals.

```tsx
<Slider label="Horizon" value={years()} onInput={setYears} min={1} max={40} unit="yr" showBounds />
```

## Shell

`App.tsx` owns the header, nav, footer and routes. `ThemeToggle` cycles system,
light and dark. `ErrorBoundary` wraps the whole app. Page titles are set per
route with `<Title>` from `@solidjs/meta`.

## Styling

Tokens live in [`src/styles.css`](../styles.css) under `@theme`, so Tailwind
utilities carry them: `bg-paper`, `bg-raised`, `bg-sunken`, `text-ink`, `text-ink-2`,
`text-ink-3`, `border-rule`, `border-rule-strong`, `border-rule-bold`, `text-accent`,
`max-w-measure`, `max-w-page`. Body text and every table cell are 17px; the display
serif is for the wordmark, `h1`, `h2` and a card title, and nothing else.

The component classes are `prose`, `link`, `eyebrow`, `control`, `lead`, `h1`, `h2`,
`h3`, `confidence`, `margin-note`, `breakout`, `scroller` and `plot`. Prefer utilities
in markup; extract a class only when it repeats.

Light and dark are one palette swapped on `:root`, so components do not need
`dark:` variants. Put `data-numeric` on any element holding a number outside a
table, which turns on tabular numerals. No gradients, no entrance animations;
transitions belong on hover, focus and disclosure only.
