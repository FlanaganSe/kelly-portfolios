# Shared primitives

The component set every content page is built from. Use these rather than
hand-rolling markup, so a number looks the same on every page and a status never
gets glossed differently in two places.

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

### `Callout`

`{ variant: "caveat" | "mechanism" | "open-question", label?, class? }` — a rule and
a label. `caveat` is what would break the claim, `mechanism` is why the effect
should exist, `open-question` is what the work has not settled.

```tsx
<Callout variant="caveat"><p>Gross, long-short, and not investable.</p></Callout>
```

## Numbers and evidence

### `Figure`

`{ label, value, unit?, interval?, note?, source?, asOf?, intervalLabel?, size?, align?, tone?, class? }`
— a number with everything that qualifies it. Extends `KeyNumber`, so a content
record spreads straight in.

```tsx
<Figure {...edge.headline} source={edge.source} asOf={edge.asOf} size="lg" />
```

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
utilities carry them: `bg-paper`, `bg-raised`, `bg-sunken`, `text-ink`,
`text-ink-muted`, `text-ink-faint`, `border-rule`, `border-rule-strong`,
`text-accent`, `max-w-measure`, `max-w-page`.

Four component classes exist and no more: `prose`, `link`, `eyebrow`, `control`.
Prefer utilities in markup; extract a class only when it repeats.

Light and dark are one palette swapped on `:root`, so components do not need
`dark:` variants. Put `data-numeric` on any element holding a number outside a
table, which turns on tabular numerals. No gradients, no entrance animations;
transitions belong on hover, focus and disclosure only.
