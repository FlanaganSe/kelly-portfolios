TAKE THIS WITH A GRAIN OF SALT

    You are the lead research engineer for an AI-first portfolio-research project. Work
  directly in /Users/seanflanagan/dev/kelly-portfolios. Your objective is to build the
  smallest rigorous system that can materially improve an investor’s odds of
  outperforming an explicitly defined passive benchmark without manufacturing confidence
  from biased data, fragile backtests, or optimization noise.

  This is not a request to build a polished consumer application, produce personalized
  financial advice, or claim that any portfolio will beat the market. It is a request to
  build an evidence-backed research home containing reproducible experiments, portfolio
  examples, failure analysis, and provisional designs. The system should help us
  determine which strategies deserve further testing, which are investable, how they
  interact, and where confidence must remain low.

  Read AGENTS.md, README.md, docs/AGENTS.md, and docs/research/portfolio-edge-research-
  framework.md completely before acting. Preserve existing work and follow the
  documentation protocol. The research framework is the canonical synthesis; improve it
  rather than creating overlapping research pages. Do not modify shipped marketing copy
  without raising the issue. Do not extend or rename src/utils/
  calculateOptimizedPortfolio.ts; it is an unwired mean-variance optimizer despite its
  Kelly-oriented name. Never deploy SST infrastructure.

  Use subagents for bounded, independent research or verification tasks when useful, but
  do not delegate interpretation of repository instructions. Use primary sources
  wherever possible. Keep verified facts, assumptions, inferences, and unresolved
  questions visibly separate. Do not claim “alpha,” “optimal,” “validated,” or “beat the
  market” unless the evidence and experiment definition support the exact claim.

  ## Governing principle

  Build the institution that can reject attractive false discoveries before building the
  machine that searches for attractive discoveries.

  The first deliverable is not an allocation. It is a reproducible research loop:

  evidence
  → falsifiable hypothesis
  → frozen experiment specification
  → immutable input snapshot
  → deterministic calculation
  → adversarial validation
  → recorded decision
  → research synthesis

  AI may accelerate evidence collection, specification drafting, implementation, review,
  and explanation. AI must not be the source of portfolio returns, mathematical truth,
  historical facts, or promotion decisions. All numerical outputs must come from
  deterministic code operating on identified data. Every AI-generated claim must retain
  sources and be independently checked before becoming trusted research.

  ## Critical treatment of the proposed shortcut

  Use reproduction of a published table as an early integration test, but do not treat
  it as proof that the complete stack is correct.

  Reproducing a Fama–French table is valuable because it exercises downloading, parsing,
  date alignment, percentage conversion, sample boundaries, basic statistics, and
  reporting together. It is not a substitute for focused tests because the published
  factor file may already contain the authors’ calculated returns. Matching its table
  does not verify portfolio accounting, rebalancing, transaction costs, tax lots,
  insolvency behavior, corporate actions, missing data, look-ahead protection, or
  optimization constraints. It can also match despite compensating errors, revised
  source data, ambiguous annualization, or accidentally selected columns.

  Implement both:

  1. A narrow unit and property-test foundation covering calculations that can be
  established independently.
  2. A published-result reproduction covering end-to-end integration.

  Do not write twenty speculative tests before understanding the first data path. Start
  with approximately eight high-value deterministic tests, then add tests whenever an
  experiment exposes a new failure mode.

  The minimum initial test set is:

  - Simple returns compound to the expected terminal wealth.
  - Log returns aggregate consistently with wealth when wealth remains positive.
  - Costs never increase wealth.
  - Zero-value trades do not change wealth.
  - Portfolio weights sum to one after a rebalance within a declared tolerance.
  - Drawdown calculations reproduce a hand-computed path.
  - A scenario producing nonpositive wealth is rejected by log optimization.
  - No observation may be used before its availability timestamp.

  Then reproduce a precisely identified published result. Record the source paper,
  table, column, sample, units, statistic definition, expected tolerance, and source-
  data vintage. Do not merely say “reproduce FF5.” Determine exactly which values from
  Fama and French 2015 can be reproduced using the currently distributed file and
  whether later revisions prevent an exact match. If the current file differs from the
  original vintage, report that limitation instead of loosening tolerances until the
  test passes.

  ## Initial technical shape

  Do not build a broad app yet. Add a contained Python research workspace without
  disrupting the SolidJS client. Prefer a structure equivalent to:

  research/
    pyproject.toml
    README.md
    src/portfolio_edge/
      data/
        cache.py
        french.py
        fred.py
        prices.py
        manifest.py
        validation.py
      core/
        returns.py
        wealth.py
        statistics.py
        drawdown.py
        costs.py
        portfolio.py
        rebalance.py
      inference/
        bootstrap.py
        multiple_testing.py
        deflated_sharpe.py
      experiments/
        specification.py
        runner.py
        registry.py
      reporting/
        artifacts.py
        tables.py
    experiments/
      exp_001_factor_decay.yaml
      exp_002_fund_exposure.yaml
      exp_003_rebalancing.yaml
      exp_004_trend_marginal_value.yaml
    tests/
      fixtures/
      unit/
      integration/
    ledger.jsonl
    data-manifests/
    artifacts/

  Use uv, a supported Python version, pytest, strict typing, and either pandas or
  Polars. Do not add both dataframe libraries without a concrete need. Prefer the
  library that most directly supports the chosen data readers and statistical code. Pin
  dependencies and record the environment. Ask before adding dependencies, as required
  by the repository agreement.

  Do not commit large or frequently changing raw data. Cache downloaded bytes outside
  Git. Commit small manifests, experiment specifications, independently calculated
  fixtures, and compact result summaries when they support durable decisions. Generated
  Parquet files should normally remain ignored unless a small frozen fixture is
  necessary to reproduce a test.

  ## Data provenance

  A manifest containing URL, SHA-256, retrieval time, row count, and first and last
  observations is necessary but not sufficient. Implement at least:

  {
    "dataset_id": "french_us_ff5_monthly",
    "source_url": "...",
    "retrieved_utc": "...",
    "sha256_raw": "...",
    "content_type": "...",
    "source_last_modified": "...",
    "parser_version": "...",
    "frequency": "monthly",
    "units": "percent",
    "first_observation": "1963-07",
    "last_observation": "...",
    "rows": 0,
    "availability_policy": "...",
    "revision_policy": "...",
    "license_or_terms_url": "...",
    "warnings": []
  }

  Preserve the original downloaded bytes. Parse them into a derived table without
  altering the raw copy. Hash both raw and normalized representations. Validate
  duplicate dates, monotonic dates, missing values, unit conversions, column names, and
  discontinuities. A hash proves which file was used; it does not prove that the file
  represents what was historically available.

  The following direct French files were reachable as of 2026-08-11:

  -
  https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip
  -
  https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_CSV.zip
  -
  https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Developed_5_Factors_CSV.zip
  -
  https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Emerging_5_Factors_CSV.zip
  -
  https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/25_Portfolios_5x5_CSV.zip

  Download directly and archive the bytes even if pandas_datareader is used for
  convenience. A third-party parser can hide source changes and may not expose the raw
  header or file hash. Test the repository parser against a frozen sample.

  FRED’s CSV endpoint is suitable for macroeconomic and cash-rate series, but record
  each series’ definition, frequency, transformations, release timing, and revision
  behavior. TB3MS, DGS3MO, and DFF are not interchangeable: they have different
  maturities, frequencies, constructions, and economic meanings. Never select whichever
  cash series improves a result.

  AQR’s public dataset index currently exposes time-series momentum, betting-against-
  beta, quality-minus-junk, and related files. Treat these as author-maintained
  replication targets, not independent evidence or investable products. Archive the
  exact downloaded workbook and sheet because URLs, workbooks, and revisions can change.

  The Goyal–Welch data are useful for testing return-predictability claims. Preserve
  original and updated datasets separately. Do not describe an annually updated full-
  sample dataset as point-in-time unless historical vintages and publication lags are
  available.

  Shiller’s historical spreadsheet is useful for long-horizon sensitivity analysis, not
  precise modern execution backtests. Document its construction changes, interpolation,
  monthly frequency, and pre-index limitations.

  Do not use yfinance as the authoritative research source. It may be useful for
  disposable exploration or as a secondary cross-check, but it does not provide a strong
  point-in-time contract, stable revision history, delisting coverage, executable
  quotes, or guaranteed adjusted-price semantics. Any ETF result intended to inform a
  decision requires a source with documented total-return and corporate-action
  treatment. If no better free source is available, label the experiment exploratory and
  preserve the downloaded snapshot.

  ## Experiment ledger

  Make the runner write an append-only ledger entry for every attempted execution,
  including failed and abandoned runs. Use atomic append or a small transactional store
  so concurrent agents cannot corrupt the file.

  Each entry must include:

  - Unique run identifier.
  - Experiment-family identifier.
  - Timestamp.
  - Git commit and dirty-worktree hash or diff hash.
  - Specification hash.
  - Dataset-manifest hashes.
  - Code and environment versions.
  - Parameters.
  - Random seed.
  - Execution status.
  - Failure reason.
  - Artifact paths and hashes.
  - Whether the run was exploratory or confirmatory.
  - Parent run, if derived from another result.
  - AI or human origin.
  - Whether its results were viewed.
  - Whether it consumes the final holdout.

  Do not count repeated executions of an identical specification as independent
  hypotheses, but do record them. Separately track the number and dependence of distinct
  specifications searched. A Deflated Sharpe Ratio cannot use the raw number of process
  invocations as the number of independent trials. Implementing the ledger makes later
  estimation possible; it does not solve the dependence problem automatically.

  The runner must refuse a confirmatory experiment that lacks a frozen benchmark,
  primary metric, cost model, sample policy, and rejection rule.

  ## Phase 1: published-result integration test

  Build the French downloader, manifest writer, parser, monthly-statistics functions,
  and published-result test.

  Produce a compact report containing:

  - Exact source vintage and hash.
  - Paper and table being targeted.
  - Sample dates.
  - Monthly arithmetic means.
  - Annualized arithmetic premia.
  - Monthly and annualized volatility.
  - Sharpe ratios with stated risk-free treatment.
  - Conventional and heteroskedasticity/autocorrelation-robust standard errors where
  appropriate.
  - Differences from the published table.
  - Explanations for rounding, revised data, or definition differences.

  Gate: do not begin strategy conclusions until the ingestion and statistics path either
  matches the declared target within justified tolerances or documents why exact
  reproduction is impossible.

  ## Experiment 001: factor persistence and decay

  The proposed publication split is useful but insufficient and must be reformulated.

  Do not treat HML 1993, UMD 1997, and RMW/CMA 2015 as perfectly clean discovery dates.
  Factor definitions, predecessor evidence, sample construction, and data availability
  differ. The current French files may retroactively apply modern methodology to earlier
  history. A before/after comparison is descriptive and can confound publication,
  changing composition, valuation regimes, crowding, and chance.

  Freeze several eras:

  - Original paper sample.
  - First genuinely post-publication period.
  - Recent period.
  - Full available post-publication period.
  - A common period across factors.

  Report means, geometric contribution where meaningful, volatility, Sharpe uncertainty,
  drawdowns, worst rolling periods, and correlations. Include one-sided and two-sided
  inference but do not make “95% positive mean” the sole survival criterion; long-lived
  modest premia may lack that power even when economically useful. Use block-bootstrap
  confidence intervals and explicitly report low power.

  The decision question is:

  > Does a factor retain a positive, economically meaningful premium after publication,
  and is the result sufficiently stable to justify testing an investable implementation?

  Do not conclude that a factor “works” from the French long-short series alone.

  ## Experiment 002: investable factor products

  Treat this as an exposure and implementation audit, not a rapid fund-selection
  strategy.

  Select funds using a predeclared rule rather than “and peers.” Record every screened
  fund. Include inception, fee, assets, index methodology, closure status,
  distributions, securities-lending treatment, and data availability. Avoid comparing
  funds over incompatible eras without showing common-period results.

  For each product:

  - Construct total returns net of the published expense ratio as actually experienced.
  - Subtract a consistently defined cash rate when calculating excess returns.
  - Regress on FF5 plus momentum with HAC errors.
  - Test rolling and subperiod loadings.
  - Report factor exposure, residual volatility, tracking difference, drawdown, turnover
  if available, and realized tax distributions.
  - Compare the product with a cheap broad-market fund and with a simple combination of
  broad funds that approximates its exposures.
  - Correct for all screened products and model specifications.
  - Distinguish statistical alpha from implementation value.

  A fund can be useful with zero alpha if it provides a desired factor exposure cheaply
  and reliably. A positive alpha estimate over a short inception history is not
  sufficient evidence of future manager skill. A t-statistic below two should not
  automatically “kill the retail factor shelf”; it may instead show that the available
  sample cannot identify a small residual return.

  Gate: promote only products whose intended exposure is present, stable, economically
  material, and delivered at acceptable cost. Do not select products by residual alpha
  alone.

  ## Experiment 003: rebalancing before financing

  Move financing after the first unlevered portfolio experiments. Futures basis is not
  “the one certain edge.” Implied financing combines interest, expected dividends,
  contract conventions, taxes, supply and demand, balance-sheet constraints, and
  measurement error. A broker margin quote and futures financing are not directly
  comparable without accounting for collateral yield, variation margin, commissions,
  rolls, capital usage, and liquidation rules. A 40-basis-point estimate is not an
  uncompeted edge; it is a possible implementation-cost difference.

  First implement rebalancing using an investable, unlevered portfolio:

  - Buy-and-hold.
  - Annual calendar rebalance.
  - Monthly calendar rebalance.
  - A single frozen relative threshold.
  - Cash-flow-directed rebalancing.

  Do not combine French developed/emerging factor series with bonds as though they were
  investable sleeves. Use actual total-return indexes or investable fund histories,
  accepting the shorter sample. Separate pretax and after-tax experiments. A legitimate
  tax test requires tax lots, holding periods, realized gains, distributions, loss
  harvesting rules, rates, and account type. If these are absent, call the result pretax
  and do not apply a constant tax haircut.

  Compare identical starting weights and cash flows. Report turnover, costs, tax
  realization, drift, exposure deviation, drawdown, and certainty-equivalent return.
  Test decades as diagnostics, not six statistically independent observations.

  ## Experiment 004: trend as marginal crisis diversification

  Use the AQR series first as a published-series evaluation, not an independent
  replication. A true reimplementation requires contract-level futures histories, rolls,
  collateral returns, execution assumptions, and point-in-time market availability. Do
  not claim independent replication without those inputs.

  Compare:

  - Passive equity/bond benchmark.
  - Volatility-scaled passive benchmark.
  - Trend sleeve alone.
  - Passive portfolio plus trend.
  - Passive portfolio plus cash at a matched risk budget.

  Apply the same lagged volatility estimator and exposure caps wherever logically
  possible. Report full-period and crisis-conditional marginal utility, not merely
  standalone significance.

  Hostile tests must include:

  - Remove the best trend month.
  - Remove the best crisis.
  - Delay execution.
  - Double costs.
  - Cap leverage.
  - Stress gaps and reversals.
  - Change volatility lookback without retuning.
  - Compare pre- and post-publication performance.
  - Attribute returns to static asset and volatility exposures.

  Reject trend as a portfolio sleeve if its marginal net benefit is economically
  negligible, concentrated in one selected crisis, or explained by a simpler static
  exposure. Retain “unresolved” rather than “rejected” when the available public series
  cannot answer investability.

  ## Deferred financing experiment

  After an unlevered portfolio survives, construct a dedicated futures-financing study.

  Use synchronized futures prices, spot or fair-value references, dividend forecasts
  available at the time, contract multipliers, expiry conventions, collateral yield,
  rolls, commissions, bid–ask spreads, and broker-specific margin terms. Separate ex-
  ante implied financing from realized financing. Compare futures, margin loans,
  leveraged funds, options, and no leverage on a like-for-like exposure basis.

  The question is not whether futures sometimes imply cheaper financing. It is:

  > Does a particular leverage implementation improve the chosen portfolio objective
  after every financing, operational, tax, liquidity, and forced-liquidation cost?

  Do not call financing savings alpha. They are implementation efficiency.

  ## Reporting and decision discipline

  Do not produce an “actual allocation” after ten days. Produce a provisional portfolio-
  design map:

  - Baseline portfolio.
  - Candidate sleeve.
  - Evidence supporting it.
  - Counterevidence.
  - Investable proxy.
  - Expected mechanism.
  - Shared exposures.
  - Failure regimes.
  - Data quality.
  - Experiment status.
  - Conditions required for promotion.

  An allocation becomes appropriate only after defining the investor policy: benchmark,
  horizon, tax status, liabilities, cash flows, drawdown tolerance, liquidity reserve,
  permitted instruments, and objective.

  Update the canonical research synthesis with durable conclusions, not a daily journal.
  Create a decision record only when a real choice is made, such as adopting linear-
  shrinkage minimum variance as the baseline or rejecting a data source for confirmatory
  research.

  Every result must be classified:

  exploratory
  source-reproduced
  independently-reproduced
  walk-forward-tested
  shadow-live
  production-eligible
  rejected
  unresolved

  Never collapse these into “works” or “does not work.”

  ## Immediate execution order

  Proceed now in this order:

  1. Inspect the repository and report any conflicting uncommitted work.
  2. Propose the minimum dependency additions and request approval before installing
  them.
  3. Add the contained research workspace and test runner.
  4. Implement the eight deterministic foundation tests.
  5. Implement raw download caching, manifests, and the French parser.
  6. Freeze a small French input fixture for parser tests.
  7. Create the append-only experiment runner and ledger.
  8. Define the exact Fama–French published-result reproduction.
  9. Run it and resolve every discrepancy.
  10. Freeze and execute Experiment 001.
  11. Build the product-universe manifest for Experiment 002 before downloading returns.
  12. Execute the exposure audit with all screened funds recorded.
  13. Execute the unlevered rebalancing experiment.
  14. Execute the AQR trend marginal-value evaluation, clearly distinguishing vendor-
  series evaluation from independent replication.
  15. Fold durable findings into the existing research framework.
  16. Report which hypotheses advanced, failed, or remain unresolved.
  17. Propose the next single experiment with the highest expected information value.

  At each gate, prefer discovering that the evidence is insufficient over filling gaps
  with assumptions. The system succeeds when it makes false confidence difficult,
  preserves negative results, and identifies exactly what evidence would change the
  decision.

  The desired outcome is not a portfolio that looks impressive in history. It is a
  disciplined and increasingly investable body of evidence that improves the probability
  of making a good portfolio decision while making the remaining uncertainty impossible
  to ignore.

  TAKE THIS WITH A GRAIN OF SALT