# Portfolio-edge research workspace

This Python workspace holds reproducible portfolio research. It is independent of the
SolidJS client: nothing here is deployed or imported by the browser.

The workspace supports three kinds of work: inexpensive exploration, frozen evaluation,
and evidence strong enough to inform a published or promoted claim. See the tiered protocol
in [`docs/AGENTS.md`](../docs/AGENTS.md), the current research method in the
[`framework`](../docs/research/portfolio-edge-research-framework.md), and source fitness and
resolution in the [`evidence base`](../docs/research/evidence-base.md).

## Run it

Python 3.12 is pinned in `.python-version`; [`uv`](https://docs.astral.sh/uv/) manages the
environment.

```sh
uv sync --extra dev
uv run pytest
uv run pytest -m network
uv run mypy
uv run ruff check
uv run python -m portfolio_edge.reporting.programme_status
```

## Layout

| Path | Purpose |
| --- | --- |
| `src/portfolio_edge/core/` | Deterministic return, wealth, risk, cost, portfolio, and Kelly primitives |
| `src/portfolio_edge/data/` | Acquisition, content-addressed cache, manifests, parsing, and validation |
| `src/portfolio_edge/inference/` | Bootstrap, HAC, multiple testing, conditioning, and walk-forward tools |
| `src/portfolio_edge/experiments/` | Specifications, runner, registry, results, and ledger |
| `src/portfolio_edge/reporting/` | Client fixtures and generated reports |
| `experiments/` | Frozen experiment specifications |
| `data-manifests/` | Small provenance records for source bytes |
| `tests/fixtures/` | Frozen inputs and independently computed expectations |
| `ledger.jsonl` | Audit trail for hypothesis-bearing analytical runs |
| `artifacts/*/summary.md` | Committed run summaries; bulk intermediate output remains ignored |

## Integrity requirements

These protect correctness rather than a preferred conclusion:

- Identify acquired source bytes before parsing them. Preserve bytes where lawful and
  practical; otherwise preserve a content hash and durable retrieval/provenance recipe. A
  hash identifies input, not validity.
- Respect availability timestamps whenever a claim depends on what was knowable at the
  time. State when a revised full-sample source is being used instead.
- Ledger data-dependent analytical attempts that can affect inference, including abandoned
  and failed runs. Environment setup and smoke tests are not research trials.
- A confirmatory evaluation freezes its benchmark, primary outcome, cost model, sample
  policy, inference, and decision rule before results are inspected. Exploration records
  what it did and its limits, without pretending to meet that standard.
- Put costs inside the trading rule for implementation claims. A constant haircut is
  acceptable only for a clearly labelled sensitivity that cannot change behavior.
- Relate a null or decision threshold to the design's own resolution. If the material effect
  is below the MDE, report the question as unresolved by that instrument.
- Carry a precise result status in the ledger. Interpret it at claim level: a rejected
  product loading is not a rejection of a strategy, and a vendor-index result is not an
  independent replication.
- When a fixture and implementation disagree, validate both independently. Correct the
  defective implementation, fixture, units, conditioning, or tolerance with evidence; do
  not tune merely to pass.

## Source fitness

Source quality is use-case specific. A feed inadequate for fund total-return inference may
still support source reproduction, a non-distributing asset, a cross-check, or exploratory
measurement. Before declaring a source absent, search `data-manifests/` and the upstream
publisher. Before using one, check its total-return definition, corporate actions,
point-in-time behavior, revision policy, redistribution terms, and fit to the estimand.

The canonical, dated inventory—including French, AQR, FRED, Goyal–Welch, Shiller,
Macrohistory, World Bank, LBMA, SEC N-PORT/N-CEN, and known free-feed limitations—lives in
[`docs/research/evidence-base.md`](../docs/research/evidence-base.md). Update that page and
the relevant manifest rather than duplicating source facts here.

## Artifacts and client fixtures

Run summaries are the detailed source for an experiment's results. A research synthesis
should quote only the few numbers needed for interpretation and link the artifact for the
full table.

After changing research arithmetic used by the client, regenerate its fixture:

```sh
uv run python -m portfolio_edge.reporting.client_fixtures \
  > ../src/lib/fixtures/research-ground-truth.json
```

If the port and generated fixture disagree, investigate; do not loosen the test tolerance
to conceal the difference.
