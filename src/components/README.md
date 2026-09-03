# Shared components

The set every page is built from. Use these rather than hand-rolling markup, so a
number looks the same on every page and a confidence word is never glossed two ways.
None of them ships JavaScript; the Solid islands under `islands/` are the only client
code and are documented in their own files.

## `Hero`

`{ title, lede?, eyebrow?, class? }`. The top of a page: an optional short line above,
the `h1`, one sentence under it, and a slot for a `KeyNumbers` strip.

```astro
<Hero eyebrow="Portfolio 1 of 4" title="One fund" lede="The whole world in one holding.">
  <KeyNumbers items={NUMBERS} />
</Hero>
```

## `KeyNumbers`

`{ items: { value, label, note? }[], class? }`. Two to four tiles. The value is text,
so a page prints it exactly as the source did; the note is where the comparison goes
when the label cannot carry it.

```astro
<KeyNumbers
  items={[
    { value: "0.06%", label: "Fee a year", note: "$6 on $10,000" },
    { value: "−83.7%", label: "Worst fall", note: "US stocks, from 1929" },
    { value: "Settled", label: "How sure" },
  ]}
/>
```

## `AllocationBar`

`{ holdings: { ticker, weight, label? }[], legend?, name?, class? }`. A portfolio as one
stacked bar with a legend. Colour per ticker comes from `src/lib/palette.ts` and is the
same on every page; the legend repeats ticker and weight so nothing depends on colour.

```astro
<AllocationBar holdings={[{ ticker: "VTI", weight: 49 }, { ticker: "VXUS", weight: 16 }]} />
```

## `PortfolioCard`

`{ name, href, tagline, holdings, fee, worstFall, worstFallNote?, confidence, number?, class? }`.
A card with the bar, three facts and a `Verdict`. The whole card is the link. Put four
in a `<div class="card-grid">` for the two-by-two grid.

```astro
<div class="card-grid">
  <PortfolioCard
    number={1}
    name="One fund"
    href="/portfolios/one-fund/"
    tagline="The whole world in one holding."
    holdings={[{ ticker: "VT", weight: 100 }]}
    fee="0.06%"
    worstFall="−83.7%"
    worstFallNote="US stocks, from 1929"
    confidence="Settled"
  />
</div>
```

## `Verdict`

`{ word?, status?, gloss?, class? }`. The confidence word as a badge. Pass one of the
four words (`Settled`, `Probably`, `Too close to call`, `No`) or a research status,
which `toConfidence` in `src/lib/rungs.ts` maps onto a word. `gloss` prints the one-line
reading beside it.

```astro
<Verdict word="Probably" />
<Verdict status="unresolved" gloss />
```

## `Ladder`

`{ rows: { worstFall, rsst, extra?, published? }[], extraHeading?, class? }`. The
drawdown ladder. The row with `published` is highlighted and tagged.

```astro
<Ladder
  rows={[
    { worstFall: "−30%", rsst: "11%" },
    { worstFall: "−50%", rsst: "19%", extra: "Plus 10 points of inflation-linked Treasuries" },
    { worstFall: "about −70%", rsst: "30%", published: true },
  ]}
/>
```

## `Compare`

`{ getLabel?, giveLabel?, class? }`. Two columns, "What you get" and "What you give up",
filled through the `get` and `give` slots.

```astro
<Compare>
  <ul slot="get"><li>A smaller worst fall.</li></ul>
  <ul slot="give"><li>About 0.7 points a year against holding.</li></ul>
</Compare>
```

## `Callout`

`{ kind, label?, class? }` where kind is `do-this` or `caveat`. A left rule and a label,
with the body in a slot. Two kinds and no more.

## `Breakout`

`{ scroll?, heading?, level?, label?, maxWidth?, class? }`. A block allowed past the
reading measure: a wide table, a chart. Must be a direct child of the page canvas.
`heading` prints a real `h2` (or `h3` with `level={3}`). A scrolling block needs a
`heading` or a `label`, so a keyboard user has a name for the region.

## `Figure`

`{ id, size?, inline?, showUnit?, class? }`. Prints a figure record from
`src/content/figures/<id>.yaml` and throws at build time if none exists. Inline, it
prints the value in running text; as a block, the label, value, interval, note and
source line.

## `ThemeToggle`

No props. Cycles system, light and dark and remembers the choice in the browser.

## Layout props on `Base`

`{ title, description?, bareTitle?, indexable?, noindex?, asOf?, wide? }`. `asOf`
prints "Numbers as of" at the foot of the canvas and defaults to the site-wide date;
pass `null` for a page with no numbers. `wide` widens the measure from 42rem to 48rem
for pages that are mostly cards and tables.

## Older confidence markup

A few pages still draw the word with a left rule instead of a badge:

```astro
<p class="confidence" data-level="settled">
  <span class="confidence-word">Settled</span>
</p>
```

`data-level` is one of `settled`, `probably`, `might`, `cant-tell`. Prefer `Verdict`.
