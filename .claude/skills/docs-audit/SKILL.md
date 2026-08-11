---
name: docs-audit
description: Sweep the repository's Markdown for redundancy, drift, and dead pages, then consolidate or delete them. Use when documentation feels heavy, before or after a large change lands, or when two pages appear to answer the same question.
---

# Documentation audit

Goal: fewer, truer pages. A successful audit usually ends with less Markdown than
it started with. `docs/AGENTS.md` defines where things belong; this skill finds
where the repository has drifted from it.

## 1. Inventory

List every tracked Markdown file with its size and last commit date:

```sh
git ls-files '*.md' | while read -r f; do
  printf '%s\t%s\t%s\n' "$(wc -l <"$f" | tr -d ' ')" "$(git log -1 --format=%ad --date=short -- "$f")" "$f"
done | sort -rn
```

Read every file. Do not audit from filenames.

## 2. Judge each page against four tests

- **Duplication.** Does another page, the code, or a type state this same fact? If
  so, one of them is canonical and the rest become links or disappear.
- **Drift.** Does every command, path, link, name, date, and claim still match the
  source? Verify against the repository, not against memory. Contradicted text is
  worse than missing text.
- **Purpose.** Does a real reader need this to make a decision? Plans, status
  journals, roadmaps, transcripts, generated prompts, and superseded drafts fail.
- **Derivability.** Could an agent get this by reading the repository in a few
  seconds? Directory listings, dependency inventories, and restated code behaviour
  cost context on every request and earn nothing.

## 3. Act

- Merge overlapping pages into the one with the better claim to be canonical, then
  delete the others.
- Fix drift in place. Do not annotate a page as outdated and leave it.
- Delete rather than archive. Git history is the archive; an `archive/` tree is not.
- Trim always-on instruction files hardest of all. `AGENTS.md` and `docs/AGENTS.md`
  are loaded on every request, so a rule that is obvious from the code, enforced by
  Biome or TypeScript, or already stated elsewhere should be removed.
- Update `docs/README.md` to match the result.

Delete freely, but list what you are removing and why before you remove it, and ask
first about anything a reader might still be relying on.

## 4. Report

Give the user: pages removed, pages merged, drift corrected, net line change, and
anything you deliberately left alone with the reason. Then run `pnpm biome check`
if any non-Markdown file was touched.
