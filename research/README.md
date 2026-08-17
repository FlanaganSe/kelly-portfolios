# Portfolio-edge research workspace

A contained Python workspace for reproducible portfolio experiments. It is
independent of the SolidJS client; nothing here is deployed and nothing here is
imported by the app.

Its purpose is stated negatively on purpose: **make false confidence expensive**.
The research question is whether a small number of economically distinct return
sources can improve net geometric return, or a predeclared investor utility,
against a cheap investable benchmark — not whether a backtest can be made to look
good. [`docs/research/portfolio-edge-research-framework.md`](../docs/research/portfolio-edge-research-framework.md)
governs whether a return source is real;
[`docs/research/portfolio-engine-specification.md`](../docs/research/portfolio-engine-specification.md)
governs how it is computed.

**Before freezing a new specification, read
[`docs/research/evidence-base.md`](../docs/research/evidence-base.md).** It carries every
source held, what each is pinned to, and — in its resolution table — the smallest effect
each instrument could detect at 80% power against the effect size that would matter.
**Where the floor exceeds the bar, a null result carries almost no information**, and that
has already happened here more than once.
[`docs/research/search-coverage.md`](../docs/research/search-coverage.md) is the standing
audit of which existing conclusions that qualifies.

## Run it

Requires [uv](https://docs.astral.sh/uv/). Python 3.12 is pinned in
`.python-version`; uv fetches it.

```sh
cd research
uv sync --extra dev
uv run pytest                 # offline tests only, by default
uv run pytest -m network      # tests that hit a primary data source
uv run mypy
uv run ruff check
```

## Layout

| Path | Holds |
| --- | --- |
| `src/portfolio_edge/core/` | Deterministic primitives: returns, wealth, drawdown, costs, portfolio, rebalancing, Kelly growth algebra. Closed-form fixtures, no market data. |
| `src/portfolio_edge/data/` | Download, raw-byte cache, manifests, parsers, validation. Provenance is enforced here or nowhere. |
| `src/portfolio_edge/inference/` | Block bootstrap, HAC, deflated Sharpe, multiple testing, covariance conditioning, purged walk-forward. |
| `src/portfolio_edge/experiments/` | Frozen specifications, the runner, the append-only ledger. |
| `src/portfolio_edge/reporting/` | Result artifacts and tables. |
| `experiments/` | One YAML specification per experiment, committed **before** its result is examined. |
| `data-manifests/` | Small committed manifests describing exactly which bytes were used. |
| `tests/fixtures/` | Small frozen inputs and independently calculated expected values. |
| `ledger.jsonl` | Append-only record of every attempted run, including failures. |
| `cache/`, `artifacts/` | Not in Git. Raw bytes and generated results. |

## Rules that are not negotiable

- **Raw bytes are preserved and hashed before anything parses them.** A parser may
  never be the only record of what was downloaded. A hash proves which file was
  used; it does not prove the file represents what was historically available.
- **Every run is ledgered, including failures and abandoned runs.** The effective
  number of independent trials cannot be reconstructed after the fact, so the
  ledger has to precede the first backtest rather than follow it.
- **A confirmatory run is refused** unless its specification freezes a benchmark,
  a primary metric, a cost model, a sample policy, and a rejection rule.
- **No observation may be used before its availability timestamp.**
- **Costs alter the trading rule**, never appear as a constant haircut afterwards.
- **Results carry a status**, never "works": `exploratory`, `source-reproduced`,
  `independently-reproduced`, `walk-forward-tested`, `shadow-live`,
  `production-eligible`, `rejected`, `unresolved`.
- **A fixture that disagrees with our own computation is a finding**, not a
  tolerance to loosen.

## Data sources and what they are not

| Source | Use | Do not |
| --- | --- | --- |
| Ken French data library | Factor returns, research portfolios | Treat as investable, or assume the current file matches the vintage a paper used |
| FRED | Cash rates, macro series | Treat as point-in-time; it is revised. `TB3MS`, `DGS3MO`, `DFF` are not interchangeable. Reach for its ICE BofA total-return indices: since April 2026 they serve a trailing **three years** and nothing more |
| AQR public datasets | Author-maintained replication targets, and the only broad-commodity and credit series held here | Call an evaluation of a vendor series an independent replication. Treat `Commodities for the Long Run` as a total return — it is excess of cash — or add `CORP_XS` to a cash rate, because it is excess of duration-matched governments, not of cash |
| Goyal–Welch | Return-predictability tests | Describe an annually updated full-sample file as point-in-time |
| Shiller | Long-horizon sensitivity | Use for modern execution backtests |
| Stooq / free price feeds | Exploratory only | Use in a confirmatory experiment; there is no documented total-return or corporate-action contract |
| SEC Form N-PORT | Fund-reported monthly total returns, net assets and the fund census, from the filings themselves | Treat as long, audited, or complete. Public filings begin 2019, figures are unaudited, and General Instruction G lets each filer use its own methodology |
