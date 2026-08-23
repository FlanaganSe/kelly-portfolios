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

`pnpm typecheck`, `pnpm test` (473 tests, 31 files), `pnpm biome check .` and `pnpm build`
are clean. `research/`: `uv run mypy` (216 files), `uv run ruff check` and `uv run pytest`
(3,056 tests) are clean.

## What changed on 2026-08-22

- **The index-relative edge budget was carrying a falsified line** and now reads 5.4 bp
  against 313 bp of tracking error rather than 46 bp. Against a cheap index this
  repository can demonstrate nothing; against the reader's own counterfactual it can
  demonstrate ~109 bp with near-certainty, and that distance is the deliverable.
- **Experiment results are committed.** `research/artifacts/*/summary.md` and
  `manifest.json` are tracked, so a synthesis can link to a result instead of retyping it.
- **`docs/the-plan.md` is gone.** It was an untracked orchestration prompt that fourteen
  committed files cited. Its content is now `docs/charter.md`, the strategy universe in
  `search-coverage.md` §2, and the named stress episodes in `evidence-base.md`.
- **[Decision 0009](docs/decisions/0009-blocks-lifted-and-closures-rescoped.md)** unblocks
  the construction tournament and funding-rule measurement, and requires that a verdict
  not outrun the instrument that produced it.
- **[Decision 0010](docs/decisions/0010-bars-carry-a-reopening-condition.md) carries that
  out on the corpus rather than only on future work.** A bar with no reopening condition is
  read as a finding; measurement is never gated, only promotion and publication; the
  eleven-step protocol is the promotion bar and a screening pass states what it deferred;
  the 2.0 and 0.30 pp/yr constants become reporting reference points until derived; and
  **six of Experiment 010b's ten sleeve verdicts are restated `unresolved`** — every
  estimate in that family lies inside the design's own ±0.58 pp/yr floor. The four that
  fired a sign or boundary clause stand, scoped to pro-rata funding at a 10% weight. The
  ledger, the frozen falsifiers and the specification hashes are untouched, and no candidate
  is promoted by any of it. 0005 is rescoped in place: its prohibition list is replaced by
  what its measurement actually reaches.

## Unresolved

- Ken French and AQR redistribution terms were not verifiable offline, so no factor series
  is committed and the lab stays forward-looking. That is the single decision to revisit
  if a licensed source appears.
- `src/content/portfolio.ts` (`funds`) and `src/content/shelf.ts` overlap on eight
  tickers. A test pins their cost fields together; they should eventually be one record.
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
- Six candidates re-enter the search as unresolved questions rather than closed ones —
  emerging and developed-ex-US small value, US and emerging long-only and overlay momentum,
  and the AQR trend leg. None is supported. The re-specified marginal-sleeve experiment,
  with a ceiling-derived bar, is what would settle them and has not run.
- The stacked candidate departs from decision 0004 by being levered, and holds one fund
  the product audit excludes and one that is `unresolved`. All three departures are stated
  on its own page and none is resolved.
## The construction tournament ran, and a units error had been deciding its headline

**Experiment 016 (plus 016b, 016c, 016d) compared twenty-five constructions over 427
months.** Three clear their own detection floor; every stacked arm is `unresolved`, and the
proposal needs **64 years** to be distinguished from levering a cheap index at 1.32×. The
wrapper choice is not a real question: RSST, MATE and JPFP span 0.15 pp/yr against floors of
3.18–3.33, and the ordering reverses inside the undisclosed financing band.

**The tournament's original finding 11 — that the overlay subtracts at the forward premium —
is withdrawn.** It cut the trend leg 84% while leaving equity at its realised mean, which is
a fitted comparator deciding a verdict. Experiment 016d sweeps both premia: **the sign is set
by the equity premium, not the trend premium**, because a leverage-matched benchmark holds
132% equity notional against the candidate's 67%. The restated finding is stronger than the
one it replaced.

**The 1.80 pp/yr forward trend premium was never measured.** It is the 2012–2025 subsample's
own geometric mean less a fee — `1.80 + 1.50 + ½×13.23²/100 = 4.17%`, recovering that era's
measured 4.17% exactly — carried on a gross arithmetic axis and double-counted. Decision
0004 records it in one sentence with no window, estimator, series or interval.

**Trend can be tested outside the 1990 window, and nobody had.** An independent 4-asset book
over 1929–2025 reads Sharpe 0.58 (*t* = 5.48); a 36-leg JST book over 1880–2020 reads 0.43
(*t* = 6.59). Both are above break-even. The post-2008 decay is real, independently
confirmed, and not resolvable.

## Sixteen new or rewritten syntheses

`construction-tournament`, `stacking-and-effective-breadth`, `leverage-and-the-notional-budget`,
`valuation-and-the-allocation`, `timing-rules-on-the-equity-sleeve`,
`currency-and-the-international-sleeve`, `trend-weight-under-uncertainty` and
`adversarial-review` are new; `alternative-sleeves-audit`, `capital-efficiency-and-breadth`,
`structural-and-tax-edges`, `rebalancing-policy`, `evidence-base`, `portfolio-recommendation`,
`trend-marginal-value` and `docs/README.md` are rewritten or extended.

Findings that changed a decision rather than adding to one:

- **MATE's `delta` is −0.159 and CTAP's is −0.027.** The shelf's warning that MATE's base leg
  sat "in the danger zone" was a reading error: the completing index future is on the same
  filing as the base ETF. The same available mistake was caught twice, two quarters apart.
- **CTAP's 0.10% net fee is a mirage** — a waiver expiring 2026-12-04 that omits the 0.75%
  charged inside a total-return swap on an affiliated fund. All-in ≈0.81% now, ≈0.99% after.
  SDMF is not a wrapper at all (`b = 0`, `delta = 1.000`).
- **Duration-hedged credit is a distinct engine.** The +0.83 correlation that closed the
  question belongs to the *unhedged* leg; the hedged excess reads **+0.016 over 1,068 months**.
- **`P(stack ahead) → Φ(z₁/√ρ)`.** At the ρ = 0.435 measured among this portfolio's own value
  tilts, an unlimited stack of 55% sleeves reaches 0.576. Effective breadth is 3.71, not 8.
- **The published MDEs used i.i.d. inference beside HAC intervals.** On matched inference the
  tilt floor is 0.72 not 0.47, and the horizon 30 years not 13.
- **Currency's mean is unresolvable on 150 years of annual data**; its variance effect is ~20%
  of sleeve volatility and precise.
- **The emerging-market placement inversion was an artifact** of assuming fully qualified
  dividends; the filed fractions reverse it.
