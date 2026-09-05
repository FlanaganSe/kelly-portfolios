# Shared components

The set every page is built from. Use these rather than hand-rolling markup, so a
number looks the same on every page and a confidence word is never glossed two ways.
None of them ships JavaScript; the charts are inline SVG rendered at build time, and the
Solid islands under `islands/` are the only client code, documented in their own files.

The arithmetic behind the charts (log ticks, drawdowns, dollar and percent formats,
donut arcs) lives in `src/lib/charts.ts` and is tested in `charts.test.ts`. Series
colours live in `src/lib/palette.ts` beside the fund colours.

## Layout

`Base` takes `{ title, description?, bareTitle?, indexable?, noindex?, asOf?, wide?, xl? }`.
`wide` widens the measure from 42rem to 48rem. `xl` opens the 1100px track for a page
built from charts and cards: prose inside it keeps a centred 768px measure, and a block
with class `wide` runs the full track. `measure` is the matching utility for a block that
should stay at 768px.

```astro
<Base title="Kelly Portfolios" xl>
  <div class="wide"><GrowthChart … /></div>
  <div class="prose">…</div>
</Base>
```

Three utilities carry the look: `panel` is the one container (surface, a hairline, 8px
radius, no shadow); `label` is the default label style (13px, sentence case, second
ink); `eyebrow` (11px uppercase) is reserved for a page's section eyebrow.

## `Button`

`{ href?, variant?, size?, type?, class? }`. Filled accent by default, `outline` for the
second action, 44px tall; `size="sm"` is 36px for a button inside a card. With `href` it
is a link, otherwise a real `<button>`.

```astro
<Button href="/portfolios/">See the four portfolios</Button>
<Button href="#choose" variant="outline">How to choose</Button>
```

## `GrowthChart`

`{ series, highlight?, height?, start?, title?, tickEvery?, class? }`. Growth of $10,000
for one to five series on a log axis, each labelled at its right end with the dollars it
finished on; gridlines at 1, 2 and 5 times each power of ten; a year tick every five
years. The `highlight` series is drawn heavier. Series with id `market` or `sixty-forty`
draw dashed in neutral ink; the four portfolio ids take the four series hues. On a phone
the end labels hide and a legend under the plot takes over. A visually hidden table
carries the end values, and the default slot is the caption.

```astro
<GrowthChart series={[market, oneFund, valueLean, withTrend, cautious]} highlight="with-trend" title="What $10,000 became">
  Four portfolios and a plain world stock index, 1990 to 2026.
</GrowthChart>
```

A series is `{ id, label, values, dates }` as `src/content/series/*.json` carries it:
monthly dollar levels from `start`, one `YYYY-MM` date per value.

## `DrawdownChart`

`{ series, highlight?, worst?, height?, start?, title?, tickEvery?, annotate?, class? }`.
The underwater chart for one or two series: percent below the last high, filled. The
deepest fall of the highlighted (or first) series is marked at its low point with the
dollars $10,000 had become and the months back to even, computed from the values unless
`worst` passes the emitter's summary (`{ pct, trough, monthsToRecover, dollarsAtTrough }`).

```astro
<DrawdownChart series={[withTrend, market]} highlight="with-trend" worst={summary.worstFall}>
  Plus trend against a plain world stock index, 1990 to 2026.
</DrawdownChart>
```

## `Donut`

`{ holdings: { ticker, weight, label? }[], center?, legend?, size?, name?, class? }`. The
holdings as a ring in the fund hues, with a legend of ticker, plain name and percent.
The centre shows the number of funds unless `center={{ value, label? }}` says otherwise.
`size="sm"` is the 72px card version, usually with `legend={false}`.

```astro
<Donut holdings={HOLDINGS} center={{ value: "0.38%", label: "a year" }} name="Plus trend" />
```

## `StatGrid` and `StatTile`

`StatGrid { items?, columns?, class? }`, `StatTile { value, label, note?, unit?, class? }`.
Big numbers: the value first at 30 to 40px in the serif, a plain label under it, an
optional note. Two by two on a phone, three or four across from a tablet. Pass `items`
or put tiles in the slot with `columns`. `unit` is a small second reading of the same
number. A value with no digit, such as a confidence word, is set a step smaller.

```astro
<StatGrid
  items={[
    { value: "$351,000", label: "$10,000 became", note: "1990 to 2026" },
    { value: "−52.7%", unit: "$4,730", label: "Worst fall", note: "2007 to 2009, back to even in 63 months" },
    { value: "$6", label: "Costs a year on $10,000", note: "0.06% fee" },
    { value: "Settled", label: "How sure" },
  ]}
/>
```

## `PortfolioCard`

`{ name, href, tagline, holdings, became?, fell?, fellPct?, costs?, period?, confidence,
gloss?, number?, visual?, cta?, class? }`. Name, one sentence on whom it is for, a small
donut (or `visual="bar"`), three rows in dollars with plain labels, the confidence word
with its gloss, and a "See portfolio" button. The whole card is the link. Put four in a
`<div class="card-grid-4">` for one, two or four across. The older `fee`, `worstFall`
and `worstFallNote` props still render, mapped onto the new rows, until every page has
moved to the series-based numbers.

```astro
<div class="card-grid-4">
  <PortfolioCard
    number={1}
    name="One fund"
    href="/portfolios/one-fund/"
    tagline="For anyone who wants one thing to buy and never think about."
    holdings={[{ ticker: "VT", weight: 100 }]}
    became="$351,000"
    fell="$4,730"
    fellPct="−52.7%"
    costs="$6"
    confidence="Settled"
  />
</div>
```

## `VerdictCard` and `VerdictGroup`

`VerdictCard { title, verdict, sentence, number?, numberLabel?, href, more?, class? }`;
`VerdictGroup { heading, count, level?, gloss?, class? }`. One idea per card: the title,
the badge, a sentence of about twenty words, the one number that carries the verdict,
and a link. `verdict` is one of the four confidence words or `Not measured yet`. A group
is a heading with a count and a grid of cards, three across on a wide screen.

```astro
<VerdictGroup heading="Probably" count={2}>
  <VerdictCard
    title="A lean toward value"
    verdict="Probably"
    sentence="Cheaper companies have beaten the market over a century, but they trailed it for the last seventeen years."
    number="+1.2% a year"
    numberLabel="over 96 years, against all US stocks"
    href="/portfolios/value-lean/"
  />
</VerdictGroup>
```

## `Verdict`

`{ word?, status?, gloss?, class? }`. The confidence word as a badge. Pass one of the
words (`Settled`, `Probably`, `Too close to call`, `No`, or `Not measured yet` on a
strategy card) or a research status, which `toConfidence` in `src/lib/rungs.ts` maps
onto a word. `gloss` prints the one-line reading beside it, or your own sentence.

```astro
<Verdict word="Probably" />
<Verdict status="unresolved" gloss />
```

## `AllocationBar`

`{ holdings: { ticker, weight, label? }[], legend?, name?, class? }`. A portfolio as one
stacked bar with a legend, in the same fund hues as the donut.

```astro
<AllocationBar holdings={[{ ticker: "VTI", weight: 49 }, { ticker: "VXUS", weight: 16 }]} />
```

## `Hero`

`{ title, lede?, eyebrow?, class? }`. The top of a page: an optional short line above,
the `h1`, one sentence under it, and a slot.

## `HoldingsTable`

`{ rows: { ticker, what, weight, fee }[], caption?, class? }`. Ticker, plain words,
weight and fee. Narrow enough to stay a table on a phone.

## `Compare`

`{ getLabel?, giveLabel?, class? }`. Two columns, "What you get" and "What you give up",
filled through the `get` and `give` slots.

## `Callout`

`{ kind, label?, class? }` where kind is `do-this` or `caveat`. A left rule and a label,
with the body in a slot. Two kinds and no more.

## `Breakout`

`{ scroll?, heading?, level?, label?, maxWidth?, class? }`. A block allowed past the
reading measure on a `wide` page. Must be a direct child of the page canvas. A scrolling
block needs a `heading` or a `label`. On an `xl` page prefer `<div class="wide">`.

## `Figure`

`{ id, size?, inline?, showUnit?, class? }`. Prints a figure record from
`src/content/figures/<id>.yaml` and throws at build time if none exists.

## `Ladder`

`{ rows: { worstFall, rsst, extra?, published? }[], extraHeading?, class? }`. The
drawdown ladder table, kept for the pages that still show one.

## `ThemeToggle`

No props. Cycles system, light and dark and remembers the choice in the browser.

## Deprecated

`KeyNumbers` (`{ items: { value, label, note? }[] }`) is the older numbers strip with
11px uppercase labels. Use `StatGrid`. It stays until the last page has moved.

A few pages still draw the confidence word with a left rule instead of a badge
(`<p class="confidence" data-level="settled">`). Prefer `Verdict`.
