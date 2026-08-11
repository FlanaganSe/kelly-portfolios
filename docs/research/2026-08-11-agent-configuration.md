# Agent configuration

**Question.** How should this repository be configured so Claude Code and Codex work
effectively, and so documentation stays clean as the project accumulates research?

**Conclusion.** Keep always-on instructions small and restricted to facts an agent
cannot infer from the repository, and move everything else to a mechanism that
loads on demand or is enforced by tooling. Current evidence says context files earn
their keep only for non-standard practices; overviews and restated code cost tokens
and buy nothing. This repository's always-on instruction set is now 91 lines and
4.2 KB (`AGENTS.md` plus `CLAUDE.md`, measured 2026-08-11), against 133 KB of
removed PRD and prompt material.

## Verified findings

### Context files do not help by default

Gloaguen, Mündler, Müller, Raychev and Vechev evaluated coding agents with and
without repository context files across SWE-bench tasks with generated files and a
new set of issues from repositories with developer-committed files
([arXiv:2602.11988](https://arxiv.org/abs/2602.11988), ETH Zurich SRI Lab,
February 2026; ICLR 2026 Workshop on Memory for LLM-Based Agentic Systems). Their
result, quoted from the abstract: "providing context files does not generally
improve task success rates, while increasing inference cost by over 20% on average.
This observation holds across different LLMs, coding agents, and for both
LLM-generated and developer-committed context files."

Two qualifications matter more than the headline. First, "instructions in the
context files are well followed by coding agents" — the mechanism works, so what
you put in a context file will be obeyed. Second, "repository overviews, although
popular and recommended by model providers, are not helpful." The authors conclude
that context files are useful "for specifying non-standard coding practices" and
that performance claims should be evaluated before deployment.

This is the single most consequential finding for this repository, and it argues
against most of what a generated `AGENTS.md` contains.

### Vendor guidance has converged on the same shape

- [Claude Code memory](https://code.claude.com/docs/en/memory) (retrieved
  2026-08-11) targets under 200 lines per `CLAUDE.md`, states that files are
  delivered as context rather than enforced configuration, and directs anything
  that "must run at a specific point" to a hook instead. It recommends that
  multi-step procedures move to a skill and that path-specific instructions move to
  `.claude/rules/` with `paths:` frontmatter, which load only when Claude reads a
  matching file. `@path` imports organise content but do not reduce context,
  because imported files load at launch. The documented cross-agent pattern is a
  `CLAUDE.md` containing `@AGENTS.md`; Claude Code does not read `AGENTS.md`
  directly.
- [Claude Code skills](https://code.claude.com/docs/en/skills) (retrieved
  2026-08-11): a skill's body loads only when invoked, so reference material costs
  nothing until needed; the `description` drives automatic invocation and is
  truncated with `when_to_use` at 1,536 characters in the skill listing.
- [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
  and the Codex [configuration reference](https://developers.openai.com/codex/config-reference)
  (retrieved 2026-08-11): Codex walks from the project root down to the working
  directory, includes at most one file per directory, and concatenates root-first
  so that files nearer the working directory override earlier guidance. The
  combined instruction set is capped at 32 KiB via `project_doc_max_bytes`, and
  overflow is truncated — historically without warning
  ([openai/codex#7138](https://github.com/openai/codex/issues/7138),
  [#13386](https://github.com/openai/codex/issues/13386)). The page tells authors
  to keep rules concise and to leave lint and formatting checks to CI rather than
  to instructions.
- The [AGENTS.md format](https://agents.md/) specifies nested files for
  subprojects, with the closest file to the edited file taking precedence and user
  prompts overriding everything. It gives no size guidance.

### Rules that tooling can enforce should not be prose

Claude Code documents the split explicitly: permissions and hooks are enforced by
the client regardless of what the model decides, while instruction files only shape
behaviour. Biome and `tsconfig.json` already enforce this repository's style and
strictness, including the ban on non-null assertions, so restating them in
`AGENTS.md` spends context on a rule that cannot be violated undetected.

## Assumptions

- The ETH Zurich results were measured on issue-resolution benchmarks. This
  repository's expected workload is closer to research synthesis and greenfield
  implementation, where non-inferable context plausibly matters more. The
  conservative reading — keep instructions, keep them short and non-obvious — is
  what is applied here.
- Codex's 32 KiB cap applies to the concatenated instruction set. Nested
  `docs/AGENTS.md` only loads when Codex works under `docs/`, so the root file is
  what must stay small; both are far below the cap today.

## What this repository now does

| Concern | Mechanism | Why |
| --- | --- | --- |
| Non-inferable facts and traps | `AGENTS.md`, imported by `CLAUDE.md` | One canonical file both tools read; the documented cross-agent pattern. |
| Documentation and research protocol | `docs/AGENTS.md` | Codex loads it only under `docs/`; it stays out of every unrelated request. |
| The same protocol for Claude | `.claude/rules/documentation.md` with `paths:` | Fires when Claude reads Markdown, and points at the canonical file rather than restating it. |
| Multi-step procedures | `.claude/skills/research/` and `.claude/skills/docs-audit/` | Bodies load only on use, so the procedure can be thorough without a standing cost. |
| Actions with real consequences | `.claude/settings.json` permissions | `sst deploy` and `sst remove` spend money and mutate live infrastructure; `.env*` files hold credentials. Denied for every invocation form, not requested in prose. |
| Formatting discipline | `PostToolUse` hook running Biome on edited files | Deterministic, so `pnpm biome check` does not fail at handoff over whitespace. |

Deliberately not added: per-directory rules for `src/`, a repository-overview
section, and an architecture description. All three are derivable by reading the
code, and the evidence above says they would cost tokens without improving
outcomes.

## Open questions

- Whether the always-on set helps here at all. The honest answer is unmeasured; the
  authors' own recommendation is to evaluate rather than assume. Revisit if agent
  performance becomes measurable in this repository.
- Whether `docs/AGENTS.md` should also carry an `.claude/rules/` copy of its full
  text rather than a pointer. The pointer costs one extra file read; a copy costs a
  divergence risk. Pointer chosen; revisit if agents are observed skipping it.

## Consequence

Re-verify this page before materially changing agent configuration. Vendor
behaviour, cap sizes, and available mechanisms are time-sensitive, and every claim
above is `as of 2026-08-11`.
