# STATE

`as of 2026-08-23` · branch `further-research`

## Objective

A portfolio-research website a casual investor can use: what to do, how sure anyone can
be about each part, and every test that failed. Confident, skeptical, evidence-driven;
never a guarantee, and never a claim that any portfolio beats an index.

## What the site is now

Astro 7.2.4, static HTML per route, **17.5 kB of JavaScript for the whole site**. Two Solid islands
are hydrated: the account-placement tool and the how-long-until-you-know tool.

The editorial spine every page follows: say what to do, then why, then how sure we are,
then what would change our mind, then the evidence. The old site did the last three well
and skipped the first.

| Route | What it is |
|---|---|
| `/` | The three yardsticks and the headline contrast |
| `/start` | Six steps in the order the size and certainty of the payoff dictate |
| `/stacking` | Why many good bets stop helping, and the funding rule |
| `/portfolio` | The construction, and which account each holding goes in |
| `/doesnt-work` | Ten rejections, each with the scope that would reopen it |
| `/how-sure` | The four rungs, the two horizon questions, and the corrections log |
| `/funds` | 59 audited products by category, fee, net cost, verdict |
| `/research` | The 33-entry corpus, linked out |
| `/search`, `/404` | Pagefind over ten pages |

## The four rungs

**Settled · Probably · Might · Can't tell.** The hedge lives in the verb and the range is
printed inline in the same sentence, because a bracketed number beside a word doubles how
often a reader recovers the intended meaning against a word alone. Drawn in ink at four
intensities, never in colour: red and green fail one man in twelve.

## Content model

126 figure records under `src/content/figures/`, one file per id. No number is typed into
a paragraph; prose calls `<Figure id>` and the component throws at build time if the id is
unknown. Every record carries a value **as a string** so sign and precision survive, a
status from the closed `EvidenceStatus` union, an `asOf`, and a `docPath` the schema
resolves against the filesystem.

## Checks

`pnpm typecheck`, `pnpm test` (541), `pnpm biome check .`, `pnpm lint:figures` (126
records), `pnpm lint:prose` and `pnpm build` all pass. Research: `uv run pytest`,
`uv run mypy` (231 files) and `uv run ruff check` are clean.

Two tools were added because six agents writing in parallel needed them:

- `tools/prose-lint.mjs` enforces the house voice from `tools/prose-rules.txt`, plus
  density checks including one that fails any performance figure stated without its
  comparison.
- `tools/check-figures.mjs` catches a status outside the union, a numeric value, an
  unresolvable `docPath`, and the same figure id carrying two different facts.

## What changed on 2026-08-23

- **The site was rewritten.** Astro replaced the SPA, whose served HTML was one empty
  `div` — invisible to every AI crawler and to a reader without JavaScript.
- **A mixed estimand was found in the site's signature device.** "You would know in N
  years" was computed two ways and the headline contrasted them. Time until you are 90%
  likely to be ahead, and the horizon at which a two-sided test at 80% power could
  separate an effect from zero, are different questions. The headline is now four months
  against 31 years, both the first rule; the 59-year figure stays on `/how-sure`, labelled
  as the second.
- **The long-only strategy ladder became real research.** It was quoted as a finding while
  being arithmetic with no specification. It is now Experiment 017 with 26 tests, an exact
  solution by enumerating all supports, a frozen spec and a committed artifact. Its answer
  is inseparable from the correlation: three sleeves at ρ = 0.435, two at 0.50, five at
  0.10.
- **[Live stacked-fund records](docs/research/live-stacked-fund-records.md) is new.** Every
  figure re-verified against a primary source; five dropped as unverifiable rather than
  softened. Asness's number is a forward-looking illustration on assumed capital-market
  expectations, not a backtest, and the page says so.
- **`tracking-error` held two different facts under one id** — 6.0% against a
  leverage-matched control and 400 bp against a same-split cheap core. Split.
- **Astro 7's `compressHTML: 'jsx'` default deletes the space** after a closing inline tag
  followed by a newline. Pinned to `true`.
- Eleven unused AWS packages and the dead seeding script are gone.

## Unresolved

- **Nothing deploys until this branch lands on `main`.** The workflow triggers on `main`
  and this branch is 200-odd commits ahead. All 34 files under `docs/research/` exist only
  here, so every figure's source link is correct in form and 404s in fact until then.
- The DNS cutover needs the domain owner's console. [`docs/deploying.md`](docs/deploying.md)
  has the five steps, the exact records, and the rollback.
- `/tools` is out of the masthead. The calculators — placement, horizon, tilt pricer,
  backtester — are still Solid routes under `src/routes/` and porting them to islands is
  its own job. `src/lib/` is already ported and fixture-tested, so the arithmetic is free.
- `/research` links out to GitHub rather than rendering the corpus. `/research/:slug`
  needs decisions about anchors and figure ids first.
- The benchmark table scrolls sideways on a phone. A four-column table with a rung mark is
  not a mobile form; a stacked list would be.
- The OG card is top-aligned with a dead lower half, and its font is fetched from
  `api.fontsource.org` **during the build**, which is a network dependency in CI.
  Committing a TTF subset fixes both.
- The two chart components have no tests. The arithmetic under them does; the geometry is
  verified by screenshot, which is not the same thing. Chart 1's labels are hand-placed and
  a copy change can silently collide them.
- `src/content/portfolio.ts` and `src/content/shelf.ts` still overlap on eight tickers.
