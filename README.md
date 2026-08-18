# Kelly Portfolios

Two halves. A Python research workspace that measures where portfolio outperformance can
actually come from, and a static SolidJS client that reads what it found.

The research is in [`research/`](research/README.md): the deterministic numerical core, the
data-provenance layer, the statistical inference used to make overfitting visible, and an
append-only ledger recording failed and abandoned runs alongside successful ones. Its
purpose is stated negatively on purpose — **make false confidence expensive**. Results carry
a status from a closed vocabulary and never "works".

The client is a reading of that, not a product built on top of it. It computes nothing the
research workspace has not already computed and tested.

The repository is not production-ready in the deployment sense: the infrastructure and
Lambda modules referenced by `sst.config.ts` are not in version control, and
`scripts/seed-database.ts` emits an unseeded random walk that is synthetic and must never be
described as market data.

## Where the research has got to

`as of 2026-08-12`. Twelve experiment families across 33 ledgered executions of **15
distinct specifications**. Fifteen is the number a later trial count starts from, not 33 —
and it is an upper bound, because two of those specifications are one search.

**No sleeve was promoted.** Hypotheses are `rejected` against falsifiers frozen before any
result was seen: rebalancing as a source of return, and the CMA and RMW factor premia. Two
factors reached `exploratory` on pooled cross-region evidence — value at +4.7 pp/yr and
momentum at +7.3 — and both are gross, long-short and not investable.

**The one result worth stating plainly:** up to **roughly 110 basis points a year** is
available against the portfolio you would otherwise have owned — fund cost, fund structure,
tax-lot method and account placement — because that edge is contractual rather than
statistical. **It is conditional**: only the ~49 bp fee line requires nothing but currently
holding an expensive fund, and for a reader already in cheap index funds in one tax-deferred
account the honest figure is close to zero. Against a cheap index the whole honest budget is
about **46 bp against 313 bp of tracking error — a 79.2% chance of being ahead after thirty
years**, and about 74 years to be 90% sure. Tracking error, not edge size, is what decides
that. (The 46 bp figure rose from 24.4 on 2026-08-17, when the factor line stopped
multiplying a fund's loading by a capture fraction that is itself a loading.)

**And the null result is partly a property of where the search has looked.** Several of the
instruments used here have measured detection floors above the effect size that would
matter, one closure turns on a reference weight rather than on evidence, and the only
experiment that would treat a portfolio as a joint object has never been run.
[Search coverage](docs/research/search-coverage.md) is the audit and the ranked agenda for a
second round; [the evidence base](docs/research/evidence-base.md) is what the data can and
cannot resolve.

Start at [`docs/README.md`](docs/README.md). The argument and design map are in the
[research framework](docs/research/portfolio-edge-research-framework.md); the construction
that follows is [the portfolio recommendation](docs/research/portfolio-recommendation.md);
the non-promotion and its conditions are
[decision 0004](docs/decisions/0004-no-sleeve-promoted.md).

## The client

A static reading of that research: what was tested, what survived, and what each line is
worth in confidence terms rather than in expected return. It calls no API, holds no keys and
ships no price data. What the reader types stays in their browser.

**There is no backtest on this site, and its absence is deliberate.** No research-grade
total-return source exists here ([decision 0002](docs/decisions/0002-no-research-grade-free-price-source.md)),
no per-fund loading vector is committed, and the redistribution terms on the public factor
libraries were not established. A growth chart built on any of those would be the most
persuasive object on the site and the least defensible one. The lab prices a forward edge
against a tracking error instead, which is arithmetic this repository has already tested.

[Decision 0007](docs/decisions/0007-application-may-render-research.md) permits it to show a
research number at all, under four conditions: every fact lives in one typed content layer
under `src/content/`; status, `as of` date, interval and source travel with every figure;
the certainty class governs the wording and the benchmark governs what may be added to what;
and the arithmetic in `src/lib/` is a port of a study module tested against fixtures that
module generates. **That last one is a real coupling** — a study whose numbers change will
break a client test, which is the intended behaviour.

**No optimiser ships.** Anything that searches a weight space belongs in `research/`, with a
frozen specification and a ledger entry.

| Route | Answers |
| --- | --- |
| `/` | Which benchmark you mean, and why the two do not add |
| `/portfolios`, `/portfolios/:id` | Four candidate constructions, ordered by how much of each case is a fact: exact weights, notional exposure where it differs from capital, and what would break each one |
| `/research`, `/research/:slug` | Ten strategy families, each asked the same ten questions — mechanism, evidence for, evidence against, failure modes, cost, overlap, role |
| `/funds`, `/funds/:ticker` | The audited shelf: delivered exposure with the panel it was measured on, cost net of securities lending, wrapper arithmetic, and issuer-filed structure |
| `/lab` | What an edge and a tracking error imply: the wait, the distribution, and how long you could sit behind |
| `/portfolio` | What to hold, and the longest section is what is deliberately absent |
| `/edge-budget` | Your budget against your own counterfactual, grouped so the groups cannot be summed |
| `/placement` | Which account each holding belongs in, computed from your bracket rather than asserted |
| `/confidence` | How long an edge takes to become visible, and why tracking error decides that |
| `/evidence` | Every experiment and where it landed, rejections given equal weight |
| `/concepts` | The vocabulary the rest of it assumes |
| `/method` | The status vocabulary, the frozen specification, the ledger, and where the machinery is currently broken |

The three computing pages read one shared investor policy held in
`src/state/investorPolicy.ts`. It is `localStorage` and nothing else: no account, no
network, no analytics. An empty policy is a valid complete state that falls back to the
repository's stated reference investor and says so.

## Start locally

Node.js 22 and pnpm 10. No environment variables are required.

```sh
pnpm install --frozen-lockfile
pnpm dev
```

## Checks

Two independent toolchains; run the checks for the half you touched.

```sh
pnpm biome check      # client
pnpm typecheck
pnpm test
pnpm build

cd research && uv run pytest && uv run mypy && uv run ruff check
```

`pnpm install` also installs the pre-push hook, which runs the first two client checks. CI
runs the client's on Node 22 and does not yet run the research workspace at all.

To regenerate the client's test fixtures after changing a study module:

```sh
cd research && uv run python -m portfolio_edge.reporting.client_fixtures \
  > ../src/lib/fixtures/research-ground-truth.json
```

## Repository map

- `src/content/` is the only place a research fact may live. Typed, sourced, dated. **A
  number hardcoded in a route is a defect.**
- `src/lib/` holds the ported arithmetic, its tests, and the generated fixtures it is checked
  against.
- `src/routes/` and `src/components/` are the pages and shared primitives.
- `sst.config.ts` describes the intended SST/AWS entry point. It imports `./infra/*` and
  deploys from `functions/`, neither of which is in version control; **do not "repair" it by
  deleting those imports.**
- `scripts/seed-database.ts` creates synthetic ETF metadata and price histories. Its output
  is an unseeded random walk and **is not market data.**
- [`research/`](research/README.md) is the Python research workspace, with its own toolchain
  and its own README.
- [`docs/README.md`](docs/README.md) indexes durable project knowledge.
- [`AGENTS.md`](AGENTS.md) is the canonical working agreement for coding agents, extended by
  [`docs/AGENTS.md`](docs/AGENTS.md) for documentation and research.

The deployed site is <https://kellyportfolios.com/>.
</content>
