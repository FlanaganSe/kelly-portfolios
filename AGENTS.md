# Repository working agreement

Canonical instructions for coding agents. `CLAUDE.md` imports this file; do not
duplicate rules there or in tool-specific configuration. `docs/AGENTS.md` adds the
documentation and research protocol for everything under `docs/`.

Every line here is loaded on every request, so this file carries only what an agent
cannot infer from the code. Read `README.md` and the files you are changing.

## What this repository is

An early-stage research application for position sizing and asset allocation.
Only the SolidJS client is in version control. Treat code, configuration, and CI as
evidence of current behavior; treat product copy and prose as intent until a test
or an implementation supports it.

## Traps

- `sst.config.ts` imports `./infra/*` and deploys handlers from `functions/`.
  Neither directory is in Git. Do not "repair" the build by deleting those imports.
- `scripts/mean-variance.py` is an unwired reference implementation, not a shipped
  code path. Its client-side twin, `src/utils/calculateOptimizedPortfolio.ts`, was
  named for Kelly, maximised a mean-variance utility, was imported by no route, and
  has been deleted along with the intended-backend contract in `src/services/api.ts`.
- `scripts/seed-database.ts` emits an unseeded random walk. Its output is synthetic
  and not reproducible; never describe it as market data.
- The client may now show a research finding, but only with its status, `as of`
  date, interval and source attached, and only from `src/content/`
  ([decision 0007](docs/decisions/0007-application-may-render-research.md)). A
  number hardcoded in a route or a component is a defect. The old copy claiming
  real-time data, optimality and professional validation has been deleted; do not
  reintroduce that register.
- **Never add lines measured against different benchmarks.** A cheap index, the
  average investor, and the reader's own counterfactual are three different
  claims. `aggregate()` in `studies/outperformance_horizon.py` raises rather than
  summing them, and the interface has to enforce the same rule. This is the error
  the repository has actually made: *not trading* was described as part of the
  ~109 bp budget in four places and was never in its ledger
  ([edge decomposition §2.4](docs/research/expected-edge-decomposition.md)).
- `research/` is a separate Python workspace with its own toolchain and its own
  `README.md`. It is not deployed and the client does not import it. No result it
  has produced yet supports a shipped claim: every candidate return source tested
  so far is `unresolved`, `rejected`, or capped at `exploratory` by its data
  contract, and no sleeve is promoted
  (`docs/decisions/0004-no-sleeve-promoted.md`).
- Free price sources are not research-grade and the code raises rather than warns
  when a confirmatory experiment reaches for one. See
  `docs/decisions/0002-no-research-grade-free-price-source.md` before "fixing" it.

## Commands

Two independent toolchains. Run the checks for the half you touched.

**Client.** Node 22 and pnpm 10. `pnpm install` installs the pre-push hook through
`prepare`; `pnpm setup` is a built-in pnpm command and will not run repository
scripts.

```sh
pnpm dev            # Vite dev server
pnpm biome check    # lint and format
pnpm typecheck      # tsc --noEmit
pnpm build          # production bundle
```

**Research workspace.** `uv`, with Python 3.12 pinned in `research/.python-version`.

```sh
cd research
uv sync --extra dev
uv run pytest       # offline by default
uv run pytest -m network   # hits a primary data source
uv run mypy         # strict
uv run ruff check
```

Run the narrowest relevant check while iterating and all of the relevant half's
checks before handoff. CI runs the client's three on Node 22 and does not yet run
the research workspace at all. If a check cannot run, or a failure predates your
change, say so precisely instead of reporting a clean run.

Optimization math belongs in `research/`, which has a test runner, closed-form
fixtures, and an experiment ledger. **No optimiser ships**: anything that searches
a weight space goes there, with a frozen specification and a ledger entry.

The client may carry closed-form arithmetic `research/` has already run, as a port
in `src/lib/` tested against fixtures that workspace generates. Regenerate them
with `uv run python -m portfolio_edge.reporting.client_fixtures`. If a port
disagrees with a fixture, the port is wrong — never loosen the tolerance.

## Boundaries

- Never run `sst deploy` or `sst remove`. They spend money and mutate live
  infrastructure. `.claude/settings.json` denies them for Claude Code.
- Do not ask for permission or approval. Adding dependencies, creating files and
  directories, installing tooling, running commands, and expanding scope to finish
  the task are all pre-approved. Choose sensibly, act, and report what you did.
  The only exceptions are the denials in `.claude/settings.json` and anything that
  would destroy unrecoverable data or touch personal or financial accounts.
- The client has no environment variables and needs none. It calls no API and
  stores no keys. If that ever changes, secrets go in `.env.local`, a
  `.env.example` comes back to record the public contract, and real values are
  never committed.

## Engineering

- Import from `src/` through the `~/*` alias.
- Keep domain logic in small typed functions under `src/utils/`, not in components.
- Biome and `tsconfig.json` enforce style and strictness, including the ban on
  non-null assertions. Document any deliberate exception beside it.
- Changes to optimization math require tests covering constraints, numerical edge
  cases, units and annualization, and at least one fixture computed independently
  of the implementation under test.
- For financial methodology, record assumptions and keep evidence separate from
  inference.

## Documentation

Update documentation in the same change as the behavior it describes. Keep each
fact in one canonical place and link to it from anywhere else. Prefer deleting
superseded text over archiving it. `docs/AGENTS.md` has the full protocol, which
you must read before adding, moving, or deleting anything under `docs/`.

## Keeping this file useful

Add a rule only when it is non-obvious from the repository, applies broadly, and
cannot be enforced by tooling instead. Delete rules the repository has made
obsolete. A longer file is a worse file.
