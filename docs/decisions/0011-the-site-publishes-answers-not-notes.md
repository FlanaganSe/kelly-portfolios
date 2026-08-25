# 0011 — The site publishes answers, and keeps the notes internal

Date: 2026-08-24. Status: accepted. Narrows the publication surface established by
[decision 0007](0007-application-may-render-research.md); changes neither what the
research may conclude nor what the client may claim.

## Context

[Decision 0007](0007-application-may-render-research.md) let the client render research
findings, provided the machinery travelled with the number. It worked: figure records
carry status, interval, window and date, and the build fails on a citation that has
moved.

What it did not settle was how much of the corpus the site should *be*. The answer that
emerged by drift was: all of it. `src/content.config.ts` rendered 35 files from
`docs/research/` and 10 from `docs/decisions/` as public pages. That is 45 of 67 routes
and about 88% of the site's word count — roughly 203,000 words of working notes, each
page carrying a link to its own source file, under URLs built from internal filenames.

Three things are wrong with that, and none of them is a criticism of the notes.

- **The notes are addressed to someone else.** They are written for whoever is running
  the next experiment. One of the page templates said so to the reader's face: "a
  working note from the repository, printed as it was written… nothing in it has been
  softened for a general reader." Publishing something while warning that it was not
  written for the person reading it is not transparency. It is an unedited draft with a
  disclaimer.
- **The vocabulary leaked upward.** Reader-facing routes carried internal words in the
  URL itself. Pages that were written for a reader then spent paragraphs translating
  terms the corpus had introduced, and one page maintains a hand-written map from the
  research module's labels to plain ones, with an assertion that throws when a key goes
  stale. That map is a symptom.
- **It buried the thing a reader came for.** Someone arriving to find out what to hold
  met a research programme instead. The three routes that answer the actual question
  were four clicks and 200,000 words away from the front door.

## Decision

The corpus is not published. `docs/research/` and `docs/decisions/` stay in the
repository as the record of where every number came from, and the routes that rendered
them are removed.

In their place the site carries a small set of pages written for a reader, each
answering one question a person would actually ask, in their words. Where an outside
source establishes something, the page cites that source in words the reader could
search for, not a path.

The figure contract changes shape to match. A citation now carries `href`, a primary
source on the open web, or `page`, a route on this site. `docPath` stays required and
stays checked at build time — the note and the heading it names must exist — but it is
never rendered and never linked. Provenance is enforced without being published.

## What this does not change

- **Nothing about what the research may conclude.** Decision 0010's clause 1 stands:
  research is open by default, and an empirical finding is scoped to its data,
  instrument, window and benchmark rather than being a closure.
- **Nothing about what the client may claim.** Decision 0006's non-promotion and
  decision 0007's four constraints are untouched. A figure still travels with its
  status, its interval and its date.
- **Nothing about provenance.** Every published number still names an internal note
  that must exist, and the build still fails if it does not. The path is checked and
  not shown, which is the ordinary arrangement in publishing: an edited piece cites its
  sources without printing the editor's working file.

## What would reopen this

- A reader-facing reason to publish a specific note. The right move then is to write
  that note's finding as a page, not to restore the directory.
- Evidence that removing the corpus cost the site something a reader valued. The
  measurable version is search: if people arrive looking for material that now has no
  page, that is a request for a page.
- A corpus written for readers in the first place. This decision is about the audience
  a document was written for, not about research being unfit to publish.
