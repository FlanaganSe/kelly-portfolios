# 0001 — Portfolio research runs in a contained Python workspace

Date: 2026-08-12. Status: accepted.

## Context

The root `AGENTS.md` requires a test runner before any change to optimisation
math, and there was none. The
[numerical engine specification](../research/portfolio-engine-specification.md)
separately established that no maintained browser-ready convex QP solver exists in
the JavaScript or WebAssembly ecosystem, so the optimisation core cannot live in
the client regardless of how the research is organised.

The research itself needs block bootstrap, HAC inference, eigenvalue work, and
reproducible seeded resampling. Those exist, mature and audited, in SciPy,
statsmodels and NumPy, and do not exist in JavaScript.

## Decision

Add `research/` as a contained Python 3.12 workspace managed by `uv`, isolated
from the SolidJS client, not deployed, and not imported by the app. pandas is the
single dataframe library; Polars is not added alongside it. Testing is pytest,
typing is `mypy --strict`, linting is ruff.

The client keeps display arithmetic. Nothing in `research/` is wired to the UI,
and wiring it is a separate decision that has not been made.

## Alternatives considered

**Do the research in TypeScript alongside the client.** Rejected: the numerical
libraries are not there, and for a research instrument the reproducibility of the
numerics *is* the product.

**Pyodide in the browser.** Deferred, not rejected. It remains the middle path if
client-side computation later becomes a product requirement, at the cost of a
large download. That depends on a product decision about offline use that has not
been taken.

**A single repository-wide toolchain.** Rejected as a false economy. The two
halves have genuinely different dependencies and lifecycles, and the boundary is
the point — the client cannot accidentally depend on research code, and research
cannot accidentally depend on shipped UI copy.

## Consequences

Contributors need `uv` in addition to Node and pnpm. CI would need a second job;
none is configured yet.

Two toolchains mean two sets of checks. The root `AGENTS.md` command list covers
the client only, and `research/README.md` covers the workspace.

Raw data caches and generated artifacts stay outside Git. Manifests, frozen
specifications, small fixtures and the experiment ledger are committed, because
they are what makes a result reconstructible.
