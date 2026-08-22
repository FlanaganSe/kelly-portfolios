# STATE

`as of 2026-08-22` · branch `further-research`

## Objective

A portfolio-research website that presents concrete portfolio candidates designed to
outperform a cap-weighted benchmark, the evidence behind each return engine, and a
frontend-only lab for sizing a tilt. Confident, skeptical, evidence-driven; never a
guarantee, and never a claim that any portfolio beats an index.

## Direction

- The design system in `src/styles.css` was kept and extended, not replaced. Tokens, dark
  mode, tabular numerals, one accent, and categorical identity carried by pattern and
  direct labelling rather than by colour.
- The typed content layer was widened rather than bypassed. No research number is written
  into a component; every figure carries status, certainty class, `as of` and source.
- **The site ships no return series, and says so on every page that would want one.** No
  fund history here is research-grade ([decision 0002](docs/decisions/0002-no-research-grade-free-price-source.md)),
  no per-fund exposure vector is committed, and the redistribution terms on the public
  factor libraries could not be established offline. The lab prices a forward edge against
  a tracking error — arithmetic this repository has already tested — and will run history
  the reader supplies.

## Information architecture

| Route | What it is |
|---|---|
| `/` | The two benchmarks, the five engines, the proposal beside the evidence-led alternative |
| `/portfolios`, `/portfolios/:id` | Four candidates: control, control-held-properly, evidence-led tilt, stacked candidate |
| `/research`, `/research/:slug` | Ten strategy families, each put through the same seven questions |
| `/funds`, `/funds/:ticker` | The 56-fund audited shelf: delivered exposure with its panel, cost net of lending, wrapper arithmetic, issuer-filed structure |
| `/lab` | Compose a portfolio, price a value tilt, see the wait an edge implies, simulate the drought, and run your own monthly returns: starting investment, period, benchmark, rebalancing frequency, fees on or off, growth, drawdown, rolling excess, calendar years and a metrics table |
| `/concepts` | The short course, then the vocabulary |
| `/method` | How a result earns a status, and the three calculations the client runs |
| `/reference`, `/edge-budget`, `/placement`, `/confidence`, `/evidence` | The original long-form pages, reached from the research index. `/portfolio` redirects to `/reference` |

## Content model

- `src/content/portfolios.ts` — four candidates, weights validated to exactly 100%,
  notional exposure where it differs from capital, priced lines carrying edge *and*
  tracking error, named failure modes, and the specific changes the evidence argues for.
- `src/content/families.ts` — ten strategy families, each with certainty class, status,
  contrary evidence and failure modes.
- `src/content/shelf.ts` — 56 funds: loadings with their panel and window, alpha only
  beside its detection floor and its pedestal, cost net of securities lending, wrapper
  arithmetic (`delta`), and issuer-filed structure with its own read date.
- `src/content/tilts.ts` — the two tilts priced end to end, at full precision, so the
  client's own arithmetic reproduces the published figures.
- `src/content/lessons.ts` — the short course.
- The pre-existing modules (`confidence`, `edgeBudget`, `placement`, `sleeves`,
  `experiments`, `openQuestions`, `glossary`, `portfolio`) are unchanged and still
  canonical for what they cover.

## Computation

Every calculation in the client is a port of a research module, checked against fixtures
that module generates.

- `src/lib/horizon.ts` — probability of outperformance, and the horizon any confidence
  needs. Pre-existing.
- `src/lib/tilt.ts` — the value-tilt chain, `weight × (fund loading − incumbent loading) ×
  premium − incremental cost`. Raises rather than accepting a capture fraction. Matches
  `research/.../value_tilt.py` to 1e-10 across 18 generated cases.
- `src/lib/lab/paths.ts` — seeded relative-path simulation, reproducing the closed form.
- `src/lib/lab/config.ts` — the lab's whole state in the query string, lossless, with
  per-field fallback.
- `src/lib/lab/importReturns.ts` — parses the reader's own monthly returns; refuses a gap
  rather than filling it, and never guesses percent from magnitude.
- `src/lib/backtest/` — alignment, calendar-anchored rebalancing, geometric fee charging
  and the metrics. Wired to `src/components/lab/HistoryPanel.tsx`, which is the only place
  history enters the site.
- `src/components/charts/scale.ts` — chart arithmetic, tested without a DOM.

## Checks

`pnpm typecheck`, `pnpm test` (413 tests, 31 files), `pnpm biome check .` and `pnpm build`
are clean, and `pnpm test` now exits zero: a lazy route import in `src/App.test.tsx` was
resolving after Vitest tore the environment down, so the suite passed every assertion and
still failed the command. `research/`: `uv run mypy`, `uv run ruff check` and
`uv run pytest` are clean.

## Unresolved

- Ken French and AQR redistribution terms were not verifiable offline, so no factor series
  is committed and the lab stays forward-looking. That is the single decision to revisit
  if a licensed source appears.
- `src/content/portfolio.ts` (`funds`) and `src/content/shelf.ts` overlap on eight
  tickers. A test pins their cost fields together; they should eventually be one record.
- VB's fund name follows the 2026-07-29 Morningstar rename pattern, which the source
  records for VTI and VBR but not for VB. It matches the pre-existing content layer and is
  pinned by a test, but it is an inference.
- No browser automation is available in this environment, so there are no true
  end-to-end tests. The route and flow tests drive real controls in jsdom, which catches
  state and content regressions but not layout or paint. `src/routes/layout.test.tsx`
  substitutes what can be checked without a browser: every control on every new route has
  an accessible name, no route skips a heading level or carries a second `h1`, and no
  source file commits a layout to a width a 360px screen does not have. The last of those
  was verified by planting a violation and watching it fail.

  What a browser would still have to check, and nothing here does: direct refresh of a
  deep route against the static build, sticky elements, overflow and truncation, chart
  readability, tooltip and focus behaviour, back/forward navigation, and console errors —
  across desktop, laptop, tablet and small mobile. The five flows worth automating first
  are open a portfolio → inspect its evidence → launch it in the lab; edit weights to an
  invalid total and recover; change benchmark and period; reopen a shared lab
  configuration and get the same portfolio back; and strategy → related portfolio →
  back.
- The stacked candidate departs from decision 0004 by being levered, and holds one fund
  the product audit excludes and one that is `unresolved`. All three departures are stated
  on its own page and none is resolved.
- No experiment has ever tested any of these constructions as a joint object. The
  construction tournament has never run.
