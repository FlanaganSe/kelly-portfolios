# Repository working agreement

Canonical instructions for coding agents. `CLAUDE.md` imports this file. Read `README.md`,
[`docs/charter.md`](docs/charter.md), the files being changed, and `docs/AGENTS.md` before
changing documentation.

## Repository boundaries

This is an early-stage position-sizing and asset-allocation research application. The
Python workspace under `research/` produces evidence; the SolidJS client is the only
deployed code and imports no Python. Treat code, configuration, data manifests, frozen
specifications, and run artifacts as evidence of current behavior. Treat prose as an
interpretation that may be revised.

Research is open by default. An empirical conclusion is scoped to its data, instrument,
window, estimand, and benchmark; it is not a prohibition on a new measurement. Promotion
or publication gates must state their scope and what evidence would change the decision.

## Non-obvious traps

- Two applications share this tree. Astro owns `src/pages/`, `src/layouts/`, `src/content.config.ts`
  and `src/content/figures/`, and is what deploys. The client-routed application under
  `src/routes/` and `src/App.tsx` is the reference being ported from; `pnpm build:legacy`
  builds it into `dist-legacy/` and nothing publishes it.
- Content-collection schemas run only during `astro build`. `astro check` does not evaluate
  them, so `pnpm build` is the gate that catches a figure citing a heading that has moved.
- `sst.config.ts` imports `./infra/*` and deploys handlers from `functions/`; neither is in
  Git. Do not make the build green by deleting those imports.
- `scripts/mean-variance.py` is an unwired reference implementation, not shipped behavior.
- `scripts/seed-database.ts` emits an unseeded synthetic random walk, not market data.
- A client research figure belongs in `src/content/` and carries status, date or period,
  interval where applicable, and source ([decision 0007](docs/decisions/0007-application-may-render-research.md)).
- A factor loading and a long-only capture fraction measure the same exposure. Do not
  multiply them. The factor line is `weight × (fund loading − incumbent loading) × premium
  − cost`; code raises on a capture argument.
- A cheap index, the investor's counterfactual, and the average investor are different
  benchmarks. Compare them, but do not add results measured against different benchmarks;
  `aggregate()` raises on that error.
- No research-grade fund return series or per-fund loading vector is committed. The client
  backtest runs data supplied by the reader. This is the current data/licensing state, not
  a principle against backtesting; reassess it when source contracts change.

## Commands

Client: Node 22 and pnpm 10.

```sh
pnpm biome check
pnpm typecheck
pnpm test
pnpm lint:prose   # the house voice, on reader-facing pages
pnpm build
```

Research: Python 3.12 and `uv`.

```sh
cd research
uv sync --extra dev
uv run pytest
uv run pytest -m network   # primary-source network tests
uv run mypy
uv run ruff check
uv run python -m portfolio_edge.reporting.programme_status
```

Run narrow checks while iterating and all checks for the half changed before handoff. CI
currently covers only the client. Report any check that could not run or any pre-existing
failure precisely.

## Research integrity

- Optimisation and weight-space searches run in `research/`, with a specification and an
  experiment-ledger entry. The client may port closed-form arithmetic tested against
  generated fixtures.
- Preserve source provenance and availability timing. A hash identifies the bytes used; it
  does not establish that the source is valid or point-in-time.
- Ledger hypothesis-bearing, data-dependent analytical attempts, including abandoned and
  failed ones. Setup and smoke-test failures need not inflate the research trial count.
- Put costs inside an executable trading rule when making implementation claims.
- Before interpreting a null, compare the effect of interest with the design's resolution.
- If a fixture and implementation disagree, investigate the fixture, implementation,
  units, tolerance, and conditioning independently; correct the defective piece and record
  the evidence. Do not loosen a tolerance merely to obtain a pass.
- Keep assumptions separate from evidence and conclusions no broader than the claim tested.

Use the tiered exploration, evaluation, and promotion protocol in `docs/AGENTS.md`. The
full confirmatory battery is not a prerequisite for exploratory measurement.

## Engineering and documentation

- Keep domain logic in small typed functions under `src/lib/` or `src/utils/`, following
  the established module boundary; keep it out of components.
- Biome and `tsconfig.json` define client style and strictness.
- Optimisation-math changes need tests for constraints, numerical edges, units,
  annualisation, and at least one independently computed fixture.
- Update documentation with behavior, keep each fact in one canonical place, and delete
  superseded narrative. `docs/AGENTS.md` defines the documentation protocol.

Do not ask for approval for ordinary in-scope work. Dependencies, files, tooling, and
commands are pre-approved. The exceptions are destructive or unrecoverable actions,
personal or financial accounts, and denials in `.claude/settings.json`. The client has no
environment variables; if that changes, document public names in `.env.example`, keep real
values in `.env.local`, and never commit secrets.

Keep this file limited to non-inferable, repository-wide constraints. Prefer code or tests
for enforceable rules and scoped findings for empirical lessons.
