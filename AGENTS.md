# Repository working agreement

Canonical instructions for coding agents. `CLAUDE.md` imports this file; do not
duplicate rules there or in tool-specific configuration. `docs/AGENTS.md` adds the
documentation and research protocol for everything under `docs/`.

Every line here is loaded on every request, so this file carries only what an agent
cannot infer from the code and cannot be told by a test. Read `README.md`,
[`docs/charter.md`](docs/charter.md) for what the programme is trying to do, and the
files you are changing.

## What this repository is

An early-stage research application for position sizing and asset allocation.
Only the SolidJS client is in version control. Treat code, configuration, and CI as
evidence of current behavior; treat product copy and prose as intent until a test
or an implementation supports it.

## How to read a rule here

**A finding is not a prohibition.** Most of what follows was learned by making a mistake
once, and the honest form of each is a scoped claim with an instrument and a window
attached. Where a rule really is absolute, it is arithmetic and the code raises. Where it
is empirical, it names what would change it.

This distinction is not decoration. Rules written here as absolutes have already
suppressed work that should have run: six data sources were recorded as unavailable while
published, and every marginal-sleeve verdict in the repository was taken against a hurdle
inflated by a rule adopted for prudence
([decision 0009](docs/decisions/0009-blocks-lifted-and-closures-rescoped.md)).

**So: check the reasoning of any rule that appears to forbid a source, a method or a
comparison, before treating it as a bar.** A rule written against one failure mode does
not reach a case that cannot exhibit it — decision 0002 bans free price feeds because
they drop distributions and mishandle corporate actions, and neither failure mode exists
for an asset that pays nothing. And before recording a source as absent, check that it is
not published, then check `research/data-manifests/`, where the last one was already
sitting.

## Traps

- `sst.config.ts` imports `./infra/*` and deploys handlers from `functions/`.
  Neither directory is in Git. Do not "repair" the build by deleting those imports.
- `scripts/mean-variance.py` is an unwired reference implementation, not a shipped
  code path. Its client-side twin was named for Kelly, maximised a mean-variance
  utility, was imported by no route, and has been deleted.
- `scripts/seed-database.ts` emits an unseeded random walk. Its output is synthetic
  and not reproducible; never describe it as market data.
- A research number in the client must carry status, `as of` date, interval and source,
  and must come from `src/content/`
  ([decision 0007](docs/decisions/0007-application-may-render-research.md)). A number
  hardcoded in a route or a component is a defect.
- **A factor loading and a long-only capture fraction are the same quantity measured two
  ways, so their product discounts one exposure twice.** A factor line is
  `weight × (fund loading − incumbent loading) × premium − cost`. This one is arithmetic:
  `studies/value_tilt.sleeve_edge` and `src/lib/tilt.ts` both raise rather than accept a
  capture argument ([long-only capture](docs/research/long-only-capture.md)).
- **A cheap index, the reader's own counterfactual and the average investor are three
  different benchmarks, and lines measured against different ones do not sum.**
  `aggregate()` in `studies/outperformance_horizon.py` raises rather than summing them.
  Comparing across benchmarks is fine and often necessary; adding is the error
  ([edge decomposition](docs/research/expected-edge-decomposition.md)).
- `research/` is a separate Python workspace with its own toolchain and `README.md`. It
  is not deployed and the client does not import it. Its current state is generated, not
  transcribed: `cd research && uv run python -m portfolio_edge.reporting.programme_status`.
- **The client ships no return series, and that is a data-licensing position rather than
  a principle.** No fund history here is research-grade
  ([decision 0002](docs/decisions/0002-no-research-grade-free-price-source.md)), no
  per-fund loading vector is committed, and the redistribution terms on the public factor
  libraries **were not verifiable offline** — nobody has checked them with a network
  connection, and at least one series held here (the World Bank gold price) is CC BY 4.0
  and redistributable. The lab is forward-looking because of that gap, not because a
  backtest would be wrong in principle. `src/lib/backtest/` runs data the *reader*
  supplies. If the licence question is settled, this changes.

## Commands

Two independent toolchains. Run the checks for the half you touched.

**Client.** Node 22 and pnpm 10. `pnpm install` installs the pre-push hook through
`prepare`; `pnpm setup` is a built-in pnpm command and will not run repository
scripts.

```sh
pnpm dev            # Vite dev server
pnpm biome check    # lint and format
pnpm typecheck      # tsc --noEmit
pnpm test
pnpm build          # production bundle
```

**Research workspace.** `uv`, with Python 3.12 pinned in `research/.python-version`.

```sh
cd research
uv sync --extra dev
uv run pytest              # offline by default
uv run pytest -m network   # hits a primary data source
uv run mypy                # strict
uv run ruff check
```

Run the narrowest relevant check while iterating and all of the relevant half's
checks before handoff. CI runs the client's checks on Node 22 and does not yet run
the research workspace. If a check cannot run, or a failure predates your change, say so
precisely instead of reporting a clean run.

## Where computation lives

Optimization math belongs in `research/`, which has a test runner, closed-form
fixtures, and an experiment ledger. **No optimiser ships**: anything that searches a
weight space goes there, with a frozen specification and a ledger entry. That is a
process rule and stands on its own; the browser-solver survey that originally justified
it is dated and no longer load-bearing.

The client may carry closed-form arithmetic `research/` has already run, as a port
in `src/lib/` tested against fixtures that workspace generates. Regenerate them
with `uv run python -m portfolio_edge.reporting.client_fixtures`. If a port
disagrees with a fixture, the port is wrong — never loosen the tolerance.

## Boundaries

- Do not ask for permission or approval. Adding dependencies, creating files and
  directories, installing tooling, running commands, and expanding scope to finish
  the task are all pre-approved. Choose sensibly, act, and report what you did.
  The exceptions are the denials in `.claude/settings.json` and anything that
  would destroy unrecoverable data or touch personal or financial accounts.
- The client has no environment variables and needs none. It calls no API and
  stores no keys. If that changes, secrets go in `.env.local`, a `.env.example`
  records the public contract, and real values are never committed.

## Engineering

- Keep domain logic in small typed functions under `src/utils/`, not in components.
- Biome and `tsconfig.json` enforce style, strictness and import paths. Document any
  deliberate exception beside it.
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
cannot be enforced by tooling instead. State it as what was learned and what would
change it, not as a ban. Delete rules the repository has made obsolete. A longer file
is a worse file.
