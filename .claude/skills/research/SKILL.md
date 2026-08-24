---
name: research
description: Investigate an open question for this repository and land the answer as a single synthesis under docs/research/. Use when asked to research, investigate, evaluate options, validate a financial or methodological claim, or check what current best practice is.
---

# Research

Follow `docs/AGENTS.md` for the required shape of a synthesis. This skill is the
procedure; that file is the contract.

## 1. Frame

State the question in one sentence and the decision it informs. Name what is out of
scope. If the request is really two questions, say so and pick one — two shallow
answers are worth less than one that settles something.

## 2. Check what already exists

Search `docs/` and the codebase for the question and its vocabulary before opening
a browser. If a page already covers it, you are updating that page. Report the
match instead of silently creating a second one.

## 3. Gather evidence

- Prefer primary sources: the vendor's own documentation, the paper, the standard,
  the code. A blog summarising a paper is a pointer to the paper, not a source.
- For anything time-sensitive, confirm it still holds and record `as of` with the
  retrieval date. Vendor behaviour and model capabilities change fast.
- For anything numeric or financial, record units, periods, annualisation, data
  source, and retrieval date. Recompute at least one figure yourself rather than
  quoting it.
- Note where sources disagree. Disagreement is a finding.

## 4. Write

One file under `docs/research/`, descriptive filename, ISO date prefix only if the
page is a snapshot. Conclusion near the top. Separate verified facts, assumptions,
and open questions — never blur them. Put links next to the claims they support.
End with the concrete consequence for this repository.

Length is not evidence of effort. Cut anything the reader can get from the code.

## 5. Land it

- Add or update the entry in `docs/README.md` in the same change.
- Fold anything now settled back into code, types, or tests, and shrink or delete
  the pages it supersedes.
- Report to the user: the answer, the confidence, what you deleted or merged, and
  which questions remain open.
