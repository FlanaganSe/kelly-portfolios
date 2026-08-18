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
- **Check whether a source exists before recording it as absent, and check
  `data-manifests/` first.** Goyal-Welch, Shiller, gold, French's `RlEst` industry return
  and FRED's bitcoin price were each written down as unavailable and each was published the
  whole time. The sixth was worse: the bond total-return leg the programme called missing is
  Goyal-Welch `ltr`/`corpr`, **already downloaded, parsed and manifested here**.
  Check the *reasoning* of any decision that appears to forbid a source, too: decision 0002
  bans free price feeds because they drop distributions and mishandle corporate actions,
  and neither failure mode exists for an asset that pays nothing.
- **Results carry a status**, never "works": `exploratory`, `source-reproduced`,
  `independently-reproduced`, `walk-forward-tested`, `shadow-live`,
  `production-eligible`, `rejected`, `unresolved`.
- **A fixture that disagrees with our own computation is a finding**, not a
  tolerance to loosen.

## Data sources and what they are not

| Source | Use | Do not |
| --- | --- | --- |
| Ken French data library | Factor returns, research portfolios | Treat as investable, or assume the current file matches the vintage a paper used |
| FRED | Cash rates, macro series, and the **real** yield curve (`FII10`) with its breakeven (`T10YIE`) and reference index (`CPIAUCNS`) | Treat as point-in-time; it is revised. `TB3MS`, `DGS3MO`, `DFF` are not interchangeable, and neither are `GS10` and `FII10` — one is nominal and one is real. Reach for its ICE BofA total-return indices: since April 2026 they serve a trailing **three years** and nothing more. Read `T10YIE` as a forecast: it is a market price containing an inflation risk premium and a TIPS liquidity premium |
| AQR public datasets | Author-maintained replication targets, and the only broad-commodity and credit series held here | Call an evaluation of a vendor series an independent replication. Treat `Commodities for the Long Run` as a total return — it is excess of cash — or add `CORP_XS` to a cash rate, because it is excess of duration-matched governments, not of cash |
| Goyal–Welch | Return-predictability tests, **and the only long bond total-return history held**: `ltr` and `corpr`, 1,200 months from 1926-01 | Describe an annually updated full-sample file as point-in-time, or predict with `cay`, `pce`, `ogap`, `sntm`, `fbm`, `tchi` or `shtint` — the source marks all seven as full-sample estimates written back over history. Treat `ltr` as the `GS10` proxy's equal: it is a roughly twenty-year index against a ten-year point, they correlate +0.663, and `ltr` is not investable |
| Shiller | Long-horizon sensitivity | Use for modern execution backtests, or treat `P` as a month-end price; it is a monthly average of daily closes |
| Jordà–Schularick–Taylor Macrohistory (R6) | The only multi-country long-horizon returns held: 16 countries, 1870–2020, annual | Read it as 18 countries (Canada and Ireland carry no returns), compare its annual drawdowns with a monthly one, forget it is nominal and local-currency, or quote Portugal 1975–77, Spain 1937–40 or Germany 1922–23 without saying what they are |
| Stooq / free price feeds | Exploratory only | Use in a confirmatory experiment; there is no documented total-return or corporate-action contract |
| World Bank Pink Sheet | The **primary gold series**, monthly USD/troy oz from 1960, CC BY 4.0 and redistributable | Read it as a month-end level — it is a monthly **average** of daily rates, which biases a Sharpe ratio upward. Or trust the URL: it is release-specific and a superseded path answers 200 with an older vintage |
| LBMA Gold Price | A month-end **cross-check** on that average, daily from 1968 | Redistribute it, or let a published figure rest on it alone. IBA requires a written licence to obtain, use or redistribute; bytes stay uncommitted and only hashes are manifested. Splice the AM and PM auctions, or read anything before 1971-09 as a market price |
| FRED `CBBTCUSD` (Coinbase) | The **only bitcoin price series held**, daily from 2014-12 | Read it as the index a US spot bitcoin ETP strikes its NAV against — IBIT uses the CME CF Bitcoin Reference Rate and FBTC its sponsor affiliate's own rate, and neither is this. Or redistribute it: Coinbase prohibits reproduction, so bytes stay uncommitted and only hashes are manifested. Its sole documentation of when an observation is taken is "All data is as of 5 PM PST" |
| SEC Form N-PORT | Fund-reported monthly total returns, net assets and the fund census, from the filings themselves | Treat as long, audited, or complete. Public filings begin 2019, figures are unaudited, and General Instruction G lets each filer use its own methodology |
| SEC Form N-CEN | The only **structured** fund-cost source: a fund's tracking difference against its own index (Item C.3.b), its securities-lending income (C.6) and whether a waiver is **recoupable** (C.8), per series per fiscal year | Rank two funds on a tracking difference against two different indices, or read the after-expense figure as a share class's — the item never says which class a multi-class fund answered for. Filer error is visible and common: one sponsor files the before- and after-expense figures identically, another's C.8 recoupment flag contradicts its own prospectus |
