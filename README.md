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

## Where the research has got to

`as of 2026-08-12`. Six frozen experiments have run, across sixteen ledgered
executions of seven distinct specifications, with 1,082 tests passing.

**No sleeve was promoted.** Hypotheses are `rejected` against falsifiers frozen
before any result was seen — rebalancing as a source of return, the AQR trend series
as a marginal sleeve, and the CMA and RMW factor premia. The last two are `rejected`
in a specific and permanent sense: pooling every independent region the Ken French
library distributes was tried, the effective sample size it bought was **measured**,
and it still cannot resolve a premium at this repository's 2.0 pp/yr materiality
threshold ([decision 0005](docs/decisions/0005-factor-premia-closed-on-public-data.md)).
One factor, value, reached `exploratory` on a pooled +4.74 pp/yr — the first thing
here to advance on the strength of a premium, and still gross, long-short and not
investable. Momentum stays `unresolved` and could not be tested outside the US. The
retail factor-product audit is `exploratory` by decision, capped there because no
free price source carries a total-return contract.

The one result worth stating plainly: **roughly 89 basis points a year is available,
near-certainly, against the portfolio you would otherwise have owned** — fund cost,
tax location, and not trading — because that edge is contractual rather than
statistical. Against a cheap index the honest budget is about 24 bp against 401 bp
of tracking error, a 63% chance of being ahead after thirty years. The full argument,
the design map, and what would have to change are in the
[research framework](docs/research/portfolio-edge-research-framework.md); the
non-promotion and its conditions are
[decision 0004](docs/decisions/0004-no-sleeve-promoted.md).

**No number from `research/` backs anything the client shows, and none may be
presented as a finding in the application.**

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

Two independent toolchains; run the checks for the half you touched.

```sh
pnpm biome check      # client
pnpm typecheck
pnpm build

cd research && uv run pytest && uv run mypy && uv run ruff check
```

`pnpm install` also installs the pre-push hook, which runs the first two client
checks. CI runs the client's three on Node 22 and does not yet run the research
workspace at all.

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
