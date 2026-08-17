# Documentation and research protocol

Scope: everything under `docs/`, plus `README.md` and any Markdown you add
elsewhere. The root `AGENTS.md` holds the repository-wide rules.

This project will accumulate a large amount of research. The failure mode is not
missing documents; it is many overlapping documents that disagree, so no reader —
human or agent — can tell which one is true. Every rule below exists to prevent
that.

## Before you write a document

1. Search `docs/` and the codebase for the question and its vocabulary. A near
   match means update that page, not add a sibling.
2. Name the decision the document informs, and what is out of scope.
3. Choose the cheapest durable home, in this order:
   - **Types or code** for an exact interface.
   - **A test** for an executable example or a numerical fixture.
   - **A comment** for a non-obvious reason at the point it applies.
   - **A document** only when the reader needs context that no code can carry.

Do not restate in prose what the code already states. Do not create a page to
record that work happened; that is what Git history is for.

## Where things go

| Location | Holds | Rule |
| --- | --- | --- |
| `README.md` | How to run the project and its current state | The only Markdown at the repository root besides agent files. Stays short. |
| `docs/README.md` | Index of durable pages | A map, never a source of facts. Update it in the same change that adds, moves, or removes a page. |
| `docs/research/` | One synthesis per question | Follows the shape below. |
| `docs/decisions/` | One choice worth defending later | `NNNN-slug.md` with context, decision, alternatives, consequences. Supersede with a newer record and link both ways. Create the directory with the first real record, not in advance. |

Do not commit plans, chat transcripts, generated execution prompts, status
journals, roadmaps, superseded drafts, or an `archive/` tree. If it would be stale
in a month and nothing links to it, it does not belong here.

## Shape of a research synthesis

Use a descriptive filename; prefix an ISO date only when the page is a snapshot of
something that will change. Keep it no longer than its evidence requires, and
include:

- the question and the decision it informs;
- the conclusion near the top, stated directly;
- findings separated into verified facts, assumptions, and open questions;
- links to primary sources next to the claims they support, preferring the
  vendor, the paper, or the code over a summary of it;
- `as of YYYY-MM-DD` on any fact likely to change;
- reproducibility details when relevant: data source and retrieval date, units,
  periods, parameters, software versions, random seed, and limitations;
- the concrete consequence for this repository.

Do not store copied articles, search-result dumps, reasoning transcripts, or
several near-identical summaries. Keep large raw data outside Git and commit a
small manifest describing its provenance and how to retrieve it.

### Say what a result is scoped to

Two failure modes have already happened here and both survive proofreading, because
the numbers are correct and only the framing is wrong.

- **A null result from an underpowered instrument is not evidence of absence.** Check
  [the resolution table](research/evidence-base.md) before proposing an experiment,
  and state the minimum detectable effect beside any result that did not find one.
- **A closure is scoped to the design that produced it.** "Closed", "permanently" and
  "cannot" need the instrument, the window and the parameters that decide them stated
  in the same sentence. [Search coverage](research/search-coverage.md) is the standing
  audit of where that has slipped.

## Why the always-on instruction files are short

`AGENTS.md`, `CLAUDE.md` and this file are loaded on every request, so they carry only
what an agent cannot infer from the repository. The evidence is
[Gloaguen et al., arXiv:2602.11988](https://arxiv.org/abs/2602.11988) (ETH Zurich SRI
Lab, February 2026), who evaluated coding agents with and without repository context
files: *"providing context files does not generally improve task success rates, while
increasing inference cost by over 20% on average"*, and *"repository overviews,
although popular and recommended by model providers, are not helpful."* Two
qualifications carry as much weight as the headline — *"instructions in the context
files are well followed"*, so what you put there will be obeyed; and the authors
conclude that context files earn their place *"for specifying non-standard coding
practices"*.

The consequence is a split rather than a shorter file: non-inferable facts and traps
go in `AGENTS.md`; this protocol lives here and under `.claude/rules/` with `paths:`
frontmatter, so it loads only when Markdown is touched; multi-step procedures are
skills, whose bodies load on use; actions with real consequences are permissions, not
prose; and formatting is a hook. **Rules that tooling can enforce should not be
prose.**

## Maintaining and retiring

- When implementation settles a question, move the durable outcome into code,
  types, or tests, and cut the page down to any rationale still worth keeping.
- Replace superseded claims in place and let Git hold the history. Split a page
  only once it answers genuinely independent questions.
- Delete research that no longer supports a decision, an implementation, or an
  open question. Deleting is the normal end state, not a failure.
- Recheck volatile claims when related code changes, before a decision leans on
  them, or when a stated review date passes. Never add `last updated` churn when
  the substance did not change.

## Every change to `docs/`

Leave the surrounding material better than you found it. When you touch a page,
remove or merge nearby text that is stale, contradicted, or redundant, and say in
your summary what you removed and why. Before handoff, check that links resolve
and that commands, dates, names, and claims match the source they describe.
Delete placeholders and empty scaffolding rather than committing them.

Run `/docs-audit` when documentation feels heavy, before a large piece of work
lands, or whenever you notice two pages answering the same question.
