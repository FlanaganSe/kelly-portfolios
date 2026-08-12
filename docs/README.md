# Documentation

An index, not a source of facts. Start at the root [`README.md`](../README.md) for
setup and current status.

## Protocol

- [Documentation and research protocol](AGENTS.md) — where a document belongs, the
  required shape of a research synthesis, and how pages are retired. Read it before
  adding, moving, or deleting anything here.

## Research

- [Repository assessment](research/2026-08-11-repository-assessment.md) — what this
  project is, what exists, and the gaps between its claims and its code.
- [Agent configuration](research/2026-08-11-agent-configuration.md) — the evidence
  behind the instruction files, permissions, hook, and skills in this repository.
- [Portfolio edge research framework](research/portfolio-edge-research-framework.md)
  — evidence, falsifiable hypotheses, numerical fixtures, and the validation
  protocol for leverage, rebalancing, crisis protection, factors, and manager alpha.
  Answers whether a return source is real.
- [Fama-French factor reproduction](research/fama-french-reproduction.md) — the
  Phase 1 ingestion gate: which published table was reproduced from which data
  vintage, the two cells that do not reproduce, and what a downstream experiment
  may and may not assume about the data path as a result.
- [Where outperformance can come from](research/expected-edge-decomposition.md) —
  the size and certainty class of every return source the repository will model,
  and the benchmark each is measured against. Proves when constant-weight
  rebalancing beats buy-and-hold, gives the closed-form probability of doing so,
  and separates what is beatable (your own counterfactual) from what is not (a
  cheap index).
- [Factor persistence and decay](research/factor-persistence.md) — Experiment 001:
  what HML, UMD, RMW and CMA did before and after publication across frozen eras,
  how little those windows can detect, and why none of the four is promoted.
- [Numerical engine specification](research/portfolio-engine-specification.md) —
  the algorithms, closed-form test fixtures, and conditioning requirements
  underneath any allocation feature, and where the optimiser should run. Answers
  how to compute it, and defers to the edge framework on whether to.

## Decisions

- [0001 — Contained Python research workspace](decisions/0001-contained-python-research-workspace.md)
  — why portfolio research runs in `research/` under `uv` rather than in the
  client, and what that costs.
- [0002 — No research-grade free price source](decisions/0002-no-research-grade-free-price-source.md)
  — every free price feed was tested and none carries a total-return contract, so
  fund-level work is exploratory until a source is licensed.
