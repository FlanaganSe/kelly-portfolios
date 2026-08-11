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
- `src/services/api.ts` describes an intended backend contract. Nothing in this
  repository implements it, so it cannot be exercised locally.
- `src/utils/calculateOptimizedPortfolio.ts` is named for Kelly but maximizes a
  mean-variance utility, and no route imports it. `scripts/mean-variance.py` is a
  second unwired reference implementation. Neither is a shipped code path.
- `scripts/seed-database.ts` emits an unseeded random walk. Its output is synthetic
  and not reproducible; never describe it as market data.
- Shipped UI copy claims real-time data, optimality, and professional validation
  that nothing here supports. Do not extend those claims. Correcting them is a
  product decision: raise it rather than rewriting copy unasked.

## Commands

Node 22 and pnpm 10. `pnpm install` installs the pre-push hook through `prepare`;
`pnpm setup` is a built-in pnpm command and will not run repository scripts.

```sh
pnpm dev            # Vite dev server
pnpm biome check    # lint and format
pnpm typecheck      # tsc --noEmit
pnpm build          # production bundle
```

Run the narrowest relevant check while iterating and all three before handoff. CI
runs the same three on Node 22. If a check cannot run, or a failure predates your
change, say so precisely instead of reporting a clean run.

There is no test runner. Installing one is the first step of any change to
optimization math, not an optional extra.

## Boundaries

- Never run `sst deploy` or `sst remove`. They spend money and mutate live
  infrastructure. `.claude/settings.json` denies them for Claude Code.
- Ask first for destructive operations, external writes, new dependencies, or
  material scope expansion.
- Secrets belong in `.env.local`. Update `.env.example` when the public variable
  contract changes, and never commit real values.

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
