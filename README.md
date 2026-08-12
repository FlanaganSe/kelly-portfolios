# Kelly Portfolios

An early-stage portfolio research application for exploring position sizing and
asset allocation with the Kelly criterion and mean-variance optimization.

The SolidJS client can assemble an ETF portfolio and call an intended AWS API for
asset search, volatility, correlation, and allocation results. The repository is
not production-ready: the client is present, but the infrastructure and Lambda
modules referenced by `sst.config.ts` are not currently in version control. Seed
data is simulated, and the financial methodology still needs validation before
results should inform real decisions.

Validating that methodology happens in [`research/`](research/README.md), a
contained Python workspace that is independent of the client and is not deployed.
It holds the deterministic numerical core, the data-provenance layer, the
statistical inference used to make overfitting visible, and an append-only
experiment ledger. Nothing the client renders is yet backed by it.

## Start locally

Requirements: Node.js 22 and pnpm 10.

```sh
pnpm install --frozen-lockfile
pnpm dev
```

The calculator's data-backed features require `VITE_API_URL`; copy `.env.example`
to `.env.local` and supply a working API URL. Without one, the informational pages
still run, but asset search and server-side optimization do not.

## Checks

```sh
pnpm biome check
pnpm typecheck
pnpm build
```

`pnpm install` also installs the pre-push hook, which runs the first two checks.

## Repository map

- `src/routes/` contains the SolidJS pages.
- `src/components/` contains reusable UI and chart components.
- `src/services/api.ts` defines the intended backend contract.
- `src/utils/` contains client-side validation and an experimental optimizer that
  no route currently imports.
- `scripts/seed-database.ts` creates synthetic ETF metadata and price histories.
- `sst.config.ts` describes the intended SST/AWS entry point.
- [`research/`](research/README.md) is the Python research workspace: primitives,
  data provenance, inference, frozen experiment specifications, and the ledger.
  It has its own toolchain (`uv`, `pytest`, `mypy`, `ruff`) and its own README.
- [`docs/README.md`](docs/README.md) indexes durable project knowledge.
- [`AGENTS.md`](AGENTS.md) is the canonical working agreement for coding agents,
  extended by [`docs/AGENTS.md`](docs/AGENTS.md) for documentation and research.

The deployed site is <https://kellyportfolios.com/>.
