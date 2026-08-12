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

`as of 2026-08-12`. Nine experiment families have run, across 23 ledgered
executions of **12 distinct specifications** and 64 ledger entries, with 1,383
tests passing. Twelve is the number a later trial count starts from, not 23.

**No sleeve was promoted.** Hypotheses are `rejected` against falsifiers frozen
before any result was seen — rebalancing as a source of return, and the CMA and
RMW factor premia. The last two are `rejected` in a specific and permanent sense:
pooling every independent region the Ken French library distributes was tried, the
effective sample size it bought was **measured**, and it still cannot resolve a
premium at this repository's 2.0 pp/yr materiality threshold
([decision 0005](docs/decisions/0005-factor-premia-closed-on-public-data.md)).

Two factors reached `exploratory` on pooled cross-region evidence: value at
+4.74 pp/yr and momentum at **+7.33 pp/yr**, the larger of the two. Both are still
gross, long-short and not investable, and momentum's three regions crash together
— 1.33 effective regions of three, sharing 2009 as their worst year. The trend
sleeve is `unresolved` rather than rejected once its contested falsifier clause is
read as a share rather than a level, and only one product on the shelf delivers
the exposure at all.

The result that decides what a tilt is worth: **the long-only capture fraction is
about 0.520**, and five defensible definitions of it span 0.846. Chaining
`premium × loading × capture − cost` leaves a US-only long-only value tilt
negative after cost.

The one result worth stating plainly: **roughly 109 basis points a year is
available, near-certainly, against the portfolio you would otherwise have owned**
— fund cost, fund structure, tax-lot method, account placement, and not trading —
because that edge is contractual rather than statistical, and reaches 99%
confidence in about twelve months. Against a cheap index the honest budget is
about 24 bp against 401 bp of tracking error, a 63% chance of being ahead after
thirty years. The construction that follows is in the
[portfolio recommendation](docs/research/portfolio-recommendation.md); the
argument and design map are in the
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
