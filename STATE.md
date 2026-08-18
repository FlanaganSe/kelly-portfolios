# STATE

`as of 2026-08-17` · branch `further-research`

## Objective

A portfolio-research website that presents concrete portfolio candidates designed to
outperform a cap-weighted benchmark, the evidence behind each return engine, and a
frontend-only lab for sizing a tilt yourself. Confident, skeptical, evidence-driven;
never a guarantee.

## Direction

- The existing design system in `src/styles.css` is kept and extended. It is already a
  serious editorial system: tokens, dark mode, tabular numerals, one accent, patterns
  rather than colour for categorical identity.
- The typed content layer discipline is kept and widened. No number in a component; every
  figure carries status, `as of` and source.
- **The site cannot ship a fund backtest and does not pretend to.** No research-grade
  price source exists here (decision 0002), there are no committed per-fund loading
  vectors, and the redistribution terms on the factor libraries were not verifiable
  offline. The lab therefore prices a forward edge against a tracking error — this
  repository's own tested arithmetic — and simulates what holding it feels like.

## Information architecture

| Route | What it is |
|---|---|
| `/` | The two benchmarks, the five engines, the portfolio list |
| `/portfolios`, `/portfolios/:id` | Four candidates: control, control-held-properly, evidence-led tilt, stacked candidate |
| `/research`, `/research/:slug` | Ten strategy families, each asked the same ten questions |
| `/funds`, `/funds/:ticker` | The 52-fund audited shelf, with loadings, net cost and issuer-filed structure |
| `/lab` | Edge, tracking error, the wait each implies |
| `/concepts`, `/method` | Vocabulary and how a result earns a status |
| `/portfolio`, `/edge-budget`, `/placement`, `/confidence`, `/evidence` | The original long-form pages, reached from the research index |

## Content model

- `src/content/portfolios.ts` — four candidates, weights validated to 100%, notional
  exposure where it differs from capital, priced lines carrying edge *and* tracking error.
- `src/content/families.ts` — ten strategy families.
- `src/content/shelf.ts` — 52 funds: loadings with their panel, alpha with its detection
  floor and pedestal, cost net of securities lending, wrapper arithmetic, issuer facts.
- `src/content/{confidence,edgeBudget,placement,sleeves,experiments,openQuestions,glossary}.ts`
  — the pre-existing layer, unchanged and still canonical for what it covers.

## Computation

- `src/lib/horizon.ts` — probability of outperformance, ported and fixture-tested.
- `src/lib/backtest/` — deterministic engine: alignment, calendar-anchored rebalancing,
  geometric fee charging, and the metrics. 52 tests. Not yet wired to a data source,
  because no honest one exists; it is used by the scenario work in the lab.
- `src/lib/lab/config.ts` — shareable URL state with per-field fallback.
- `src/lib/lab/paths.ts` — seeded relative-path simulation reproducing the closed form.
- `src/components/charts/scale.ts` — chart arithmetic, tested without a DOM.

## Work completed

Backtest engine · lab URL state and path simulation · chart scales · portfolio, family
and fund content layers with tests · portfolio library and detail · research library and
family pages · fund shelf and fund pages · home page · route smoke tests · a useful 404.

## In progress

The value-tilt port and its research-workspace fixtures, then the lab route itself.

## Unresolved

- Ken French and AQR redistribution terms were not verifiable offline, so no factor
  series is committed. Until that is settled the lab stays forward-looking.
- `src/content/portfolio.ts` (`funds`) and `src/content/shelf.ts` overlap on eight
  tickers. A test pins them together; they should eventually be one record.
- The stacked candidate departs from decision 0004 by being levered. That is stated on
  its own page and is not resolved.

## Next three actions

1. Land the value-tilt port and build `/lab` on it.
2. Red-team pass: claims, weights, prose tone, accessibility, mobile.
3. Update `README.md`, which still prints the superseded 24 bp / 401 bp figures.
