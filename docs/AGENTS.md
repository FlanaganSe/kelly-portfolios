# Documentation and research protocol

Scope: Markdown throughout the repository. Root [`AGENTS.md`](../AGENTS.md) holds the
repository-wide working agreement.

## Purpose

Documentation should help a reader make or revisit a decision. It is not a second result
store. Detailed run output belongs in committed `research/artifacts/*/summary.md` files;
syntheses explain what the results mean, where they apply, and what remains unknown.

Research is open by default. An earlier null, rejection, or decision does not prohibit a
new source, estimand, model, comparison, or exploratory measurement. Constraints on a
published claim should name their evidence, scope, owner, and a review or reopening trigger.

## Before writing

1. Search for the question and update its canonical page when one exists.
2. State the decision informed and what is out of scope.
3. Put exact contracts in types/tests, local rationale in comments, run results in generated
   artifacts, and only durable interpretation in prose.
4. Link generated facts instead of transcribing them. In particular, experiment counts come
   from `uv run python -m portfolio_edge.reporting.programme_status` and result tables from
   the run artifact.

## Research pages

A useful synthesis is as short as its evidence permits and normally contains:

- a direct current conclusion;
- verified findings, interpretation or assumptions, and open questions kept distinct;
- scope: instrument, sample/window, benchmark, units, costs, and material limitations;
- source links and `as of YYYY-MM-DD` for volatile facts;
- the consequence for the decision and the next informative test, if any;
- links to specifications, manifests, code, and run artifacts needed to reproduce details.

A null is only informative relative to the instrument's resolution. State the minimum
detectable effect when power is material. A conclusion should not outrun its design:
`unresolved` is a useful result, and “not detected here” is not “does not exist.”

Use three evidence levels rather than one universal ritual:

- **Explore:** establish the mechanism, provenance, rough magnitude, relevant costs, and
  explicit limits. Record hypothesis-bearing analytical choices in the ledger. Exploration
  can guide the next test but cannot support a shipped or promoted claim.
- **Evaluate:** freeze the decision-relevant specification, benchmark, primary outcome,
  costs, inference, and the hostile tests appropriate to the design before inspecting the
  result.
- **Promote:** add independent or forward evidence, implementation validation, and a
  decision-specific review of risks, taxes, liquidity, and holdability. The required
  evidence depends on the claim; explain applicability instead of mechanically deferring a
  fixed checklist.

## Information architecture

| Location | Purpose |
| --- | --- |
| `README.md` | Short project orientation, setup, and current-state pointers |
| `docs/README.md` | Reading paths and canonical page map; no duplicated findings |
| `docs/charter.md` | Research objective, reference scenario, and decision principles |
| `docs/research/` | One current synthesis per question |
| `docs/decisions/` | Rationale for durable choices; status and supersession explicit |
| `research/artifacts/*/summary.md` | Generated, detailed run results |

Delete stale and duplicated prose rather than archive it. Git holds history. Do not add
plans, transcripts, status journals, copied articles, or search dumps. When moving or
deleting a page, update `docs/README.md` and all inbound links in the same change.

## Before handoff

Check relative links and anchors, volatile dates, names, commands, and claims against their
sources. Remove nearby repetition while touching a page. Run the narrow documentation and
content tests, plus the checks for any code or research workspace changed.
