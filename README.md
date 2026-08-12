# Kelly Portfolios

Two halves. A Python research workspace that measures where portfolio
outperformance can actually come from, and a static SolidJS client that reads what
it found.

The research is in [`research/`](research/README.md): the deterministic numerical
core, the data-provenance layer, the statistical inference used to make
overfitting visible, and an append-only ledger that records failed and abandoned
runs alongside successful ones. Its purpose is stated negatively on purpose —
**make false confidence expensive**. Results carry a status from a closed
vocabulary and never "works".

The client is a reading of that, not a product built on top of it. It computes
nothing the research workspace has not already computed and tested.

The repository is not production-ready in the deployment sense: the infrastructure
and Lambda modules referenced by `sst.config.ts` are not in version control, and
`scripts/seed-database.ts` emits an unseeded random walk that is synthetic and
must never be described as market data.

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

The client now reads from that research rather than around it, under the four
constraints in [decision 0007](docs/decisions/0007-application-may-render-research.md).
It states the 24 bp figure in the same place as the 109 bp one, never apart from
it, and it displays `exploratory` as `exploratory`.

## The client

A static reading of that research: what was tested, what survived, and what each
line is worth in confidence terms rather than in expected return. It calls no API,
holds no keys and ships no price data. What the reader types stays in their
browser.

[Decision 0007](docs/decisions/0007-application-may-render-research.md) is what
permits it to show a research number at all, and it attaches four conditions:
every fact lives in one typed content layer under `src/content/`; status, `as of`
date, interval and source travel with every figure; the certainty class governs
the wording and the benchmark governs what may be added to what; and the
arithmetic in `src/lib/` is a port of a study module tested against fixtures that
module generates.

That last one is a real coupling. `research/src/portfolio_edge/reporting/client_fixtures.py`
emits `src/lib/fixtures/research-ground-truth.json`, and a study whose numbers
change will break a client test. That is the intended behaviour.

No optimiser ships. Anything that searches a weight space belongs in `research/`,
with a frozen specification and a ledger entry.

## Start locally

Requirements: Node.js 22 and pnpm 10.

```sh
pnpm install --frozen-lockfile
pnpm dev
```

No environment variables are required. There is nothing to configure.

## Checks

Two independent toolchains; run the checks for the half you touched.

```sh
pnpm biome check      # client
pnpm typecheck
pnpm test
pnpm build

cd research && uv run pytest && uv run mypy && uv run ruff check
```

`pnpm install` also installs the pre-push hook, which runs the first two client
checks. CI runs the client's on Node 22 and does not yet run the research
workspace at all.

To regenerate the client's test fixtures after changing a study module:

```sh
cd research && uv run python -m portfolio_edge.reporting.client_fixtures \
  > ../src/lib/fixtures/research-ground-truth.json
```

## Repository map

- `src/content/` is the only place a research fact may live. Typed, sourced,
  dated. A number hardcoded in a route is a defect.
- `src/lib/` holds the ported arithmetic and its tests, plus the generated
  fixtures it is checked against.
- `src/routes/` and `src/components/` are the pages and the shared primitives.
- `sst.config.ts` describes the intended SST/AWS entry point. It imports
  `./infra/*` and deploys from `functions/`, neither of which is in version
  control; do not "repair" it by deleting those imports.
- `scripts/seed-database.ts` creates synthetic ETF metadata and price histories.
  Its output is an unseeded random walk and is not market data.
- [`research/`](research/README.md) is the Python research workspace: primitives,
  data provenance, inference, frozen experiment specifications, and the ledger.
  It has its own toolchain (`uv`, `pytest`, `mypy`, `ruff`) and its own README.
- [`docs/README.md`](docs/README.md) indexes durable project knowledge.
- [`AGENTS.md`](AGENTS.md) is the canonical working agreement for coding agents,
  extended by [`docs/AGENTS.md`](docs/AGENTS.md) for documentation and research.

The deployed site is <https://kellyportfolios.com/>.
