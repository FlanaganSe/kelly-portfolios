import { Title } from "@solidjs/meta";
import { For, Show } from "solid-js";
import { PageHeader } from "~/components/PageHeader";
import { Prose } from "~/components/Prose";
import { SourceLink } from "~/components/SourceLink";
import { CertaintyChip, StatusChip } from "~/components/StatusChip";
import { type GlossaryEntry, glossary } from "~/content/glossary";
import { type CertaintyClass, certaintyMeta, type EvidenceStatus, statusMeta } from "~/content/types";
import { CORPUS_AS_OF } from "~/lib/nav";

/**
 * The field guide. Every term the rest of the site assumes you know, grouped so the
 * page is navigable, and each one anchored so another page can deep-link to it:
 * `/concepts#tracking-error`.
 */

const H2 = "font-sans text-xl font-semibold tracking-[-0.015em] text-ink";

/** `Tracking error` → `tracking-error`. Stable, so the anchors are linkable. */
function termId(term: string): string {
  return term
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

type GroupId = "vocabulary" | "measurement" | "construction" | "tax" | "statistics";

const GROUPS: readonly { readonly id: GroupId; readonly title: string; readonly blurb: string }[] = [
  {
    id: "vocabulary",
    title: "Status and certainty",
    blurb: "Two closed vocabularies. One grades the evidence, the other says what kind of thing a return is.",
  },
  {
    id: "measurement",
    title: "Measuring a return",
    blurb: "What a number means once you ask what it was measured against.",
  },
  {
    id: "construction",
    title: "Building a portfolio",
    blurb: "Risk, sizing and the worst case you have to sit through.",
  },
  {
    id: "tax",
    title: "Tax, structure and cost",
    blurb: "The lines whose sign is known in advance, because a statute or an accounting identity sets them.",
  },
  {
    id: "statistics",
    title: "Statistics and evidence",
    blurb: "How this repository decides whether it has found anything.",
  },
];

/** Presentation only. An unmapped term falls into `measurement` rather than vanishing. */
const GROUP_BY_TERM: Readonly<Record<string, GroupId>> = {
  "Tracking error": "measurement",
  "Geometric vs arithmetic return": "measurement",
  "Capture fraction": "measurement",
  "Factor loading": "measurement",
  "Model-misfit pedestal": "measurement",
  "Certainty equivalent": "construction",
  "Sequence risk": "construction",
  "Drawdown, and time under water": "construction",
  "Kelly, or growth-optimal sizing": "construction",
  "Step-up in basis": "tax",
  "Specific identification": "tax",
  "Qualified dividend": "tax",
  "Foreign tax credit": "tax",
  "Securities lending": "tax",
  "Contango and the funding basis": "tax",
  "Deflated Sharpe ratio": "statistics",
  "Block bootstrap": "statistics",
  "HAC standard errors": "statistics",
  "Purged walk-forward": "statistics",
  "Multiple testing and the Holm correction": "statistics",
  "Minimum detectable effect": "statistics",
  "Effective sample size": "statistics",
};

/** The three glossary terms the site's argument rests on. They get more room. */
const FEATURED: readonly string[] = ["Tracking error", "Geometric vs arithmetic return", "Capture fraction"];

const VOCABULARY_LINKS: readonly { readonly id: string; readonly label: string }[] = [
  { id: "certainty-class", label: "Certainty class" },
  { id: "evidence-status", label: "Evidence status" },
];

const groupOf = (entry: GlossaryEntry): GroupId => GROUP_BY_TERM[entry.term] ?? "measurement";
const entriesIn = (group: GroupId): readonly GlossaryEntry[] => glossary.filter((entry) => groupOf(entry) === group);

const indexLinks = (group: GroupId): readonly { readonly id: string; readonly label: string }[] =>
  group === "vocabulary"
    ? VOCABULARY_LINKS
    : entriesIn(group).map((entry) => ({ id: termId(entry.term), label: entry.term }));

const vocabularyGroup = GROUPS.find((group) => group.id === "vocabulary");

const certaintyOrder = Object.keys(certaintyMeta) as readonly CertaintyClass[];
const statusOrder = Object.keys(statusMeta) as readonly EvidenceStatus[];

function Term(props: { readonly entry: GlossaryEntry }) {
  const featured = () => FEATURED.includes(props.entry.term);
  return (
    <article id={termId(props.entry.term)} class="scroll-mt-6 border-t border-rule pt-5">
      <Show when={featured()}>
        <p class="eyebrow mb-1">Read this one</p>
      </Show>
      <h3 class="font-sans text-base font-semibold text-ink">{props.entry.term}</h3>
      <p class={`mt-2 max-w-measure font-serif text-ink ${featured() ? "text-xl" : "text-lg"}`}>{props.entry.short}</p>
      <p class="mt-3 max-w-measure text-ink-muted">{props.entry.long}</p>
      <p class="eyebrow mt-4">Why you care</p>
      <p class="mt-1 max-w-measure text-ink">{props.entry.whyYouCare}</p>
      <Show when={props.entry.source}>
        {(citation) => (
          <p class="mt-3">
            <SourceLink citation={citation()} prefix />
          </p>
        )}
      </Show>
    </article>
  );
}

export default function Concepts() {
  return (
    <>
      <Title>Concepts — Portfolio Edge</Title>
      <PageHeader
        title="Concepts"
        standfirst="The vocabulary the rest of the site is written in, with the reason each term earns its place."
        lastChecked={CORPUS_AS_OF}
      />

      <Prose as="section">
        <p>
          Every page here leans on a small set of terms. This one says what they mean and why they change an answer,
          rather than only what they are.
        </p>
        <p>
          Four carry most of the argument. <a href="#tracking-error">Tracking error</a> decides whether an edge can ever
          be demonstrated. <a href="#geometric-vs-arithmetic-return">Geometric versus arithmetic return</a> decides
          which number you actually compounded. <a href="#capture-fraction">Capture fraction</a> decides how much of a
          long-short premium a long-only holder receives, and it has no single value.{" "}
          <a href="#certainty-class">Certainty class</a> decides what a line of return may be called at all. Read those
          and the rest of the site reads itself.
        </p>
      </Prose>

      <nav aria-labelledby="on-this-page" class="mt-10 border-y border-rule py-6">
        <h2 id="on-this-page" class="eyebrow mb-4">
          On this page
        </h2>
        <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <For each={GROUPS}>
            {(group) => (
              <div>
                <a href={`#${group.id}`} class="link font-medium text-sm">
                  {group.title}
                </a>
                <ul class="mt-2 flex flex-col gap-1">
                  <For each={indexLinks(group.id)}>
                    {(item) => (
                      <li class="text-sm text-ink-muted">
                        <a href={`#${item.id}`} class="link">
                          {item.label}
                        </a>
                      </li>
                    )}
                  </For>
                </ul>
              </div>
            )}
          </For>
        </div>
      </nav>

      {/* The two closed vocabularies, which are types rather than glossary entries. */}
      <section aria-labelledby="vocabulary-heading" class="mt-14 scroll-mt-6" id="vocabulary">
        <h2 id="vocabulary-heading" class={H2}>
          Status and certainty
        </h2>
        <p class="mt-2 max-w-measure text-ink-muted">{vocabularyGroup?.blurb}</p>

        <article id="certainty-class" class="mt-8 scroll-mt-6 border-t border-rule pt-5">
          <h3 class="font-sans text-base font-semibold text-ink">Certainty class</h3>
          <p class="mt-2 max-w-measure font-serif text-xl text-ink">
            What kind of thing a line of return is, which decides how it is allowed to be described.
          </p>
          <p class="mt-3 max-w-measure text-ink-muted">
            A fee you avoid and a premium you hope for are not the same kind of object, and calling both an edge hides
            the difference that matters. A risk premium is never described as an edge on this site. Lines measured
            against different yardsticks — a cheap index, the average investor, the portfolio you would otherwise have
            held — are never added together, because the sum would be against no benchmark at all.
          </p>
          <ul class="mt-4 flex max-w-measure flex-col gap-3">
            <For each={certaintyOrder}>
              {(certainty) => (
                <li>
                  <CertaintyChip certainty={certainty} showGloss />
                </li>
              )}
            </For>
          </ul>
          <p class="eyebrow mt-4">Why you care</p>
          <p class="mt-1 max-w-measure text-ink">
            It tells you which lines of a budget you can count on and which you are betting on. The contractual ones are
            the reason the portfolio looks the way it does.
          </p>
        </article>

        <article id="evidence-status" class="mt-8 scroll-mt-6 border-t border-rule pt-5">
          <h3 class="font-sans text-base font-semibold text-ink">Evidence status</h3>
          <p class="mt-2 max-w-measure font-serif text-lg text-ink">
            How far a result got through the protocol, on a ladder that is never collapsed into "it works".
          </p>
          <p class="mt-3 max-w-measure text-ink-muted">
            Each rung is earned by a test written down before the result was seen. Nothing in this repository has
            climbed past the first one.
          </p>
          <ul class="mt-4 flex max-w-measure flex-col gap-3">
            <For each={statusOrder}>
              {(status) => (
                <li>
                  <StatusChip status={status} showGloss />
                </li>
              )}
            </For>
          </ul>
          <p class="eyebrow mt-4">Why you care</p>
          <p class="mt-1 max-w-measure text-ink">
            Two words do most of the work and are easy to misread. <em>Rejected</em> means a pre-registered test fired,
            not that the effect is zero. <em>Unresolved</em> means the window was too small to see the effect it was
            hunting, which is neither a promotion nor a refutation.
          </p>
        </article>
      </section>

      <For each={GROUPS.filter((group) => group.id !== "vocabulary")}>
        {(group) => (
          <section aria-labelledby={`${group.id}-heading`} class="mt-14 scroll-mt-6" id={group.id}>
            <h2 id={`${group.id}-heading`} class={H2}>
              {group.title}
            </h2>
            <p class="mt-2 max-w-measure text-ink-muted">{group.blurb}</p>
            <div class="mt-8 flex flex-col gap-8">
              <For each={entriesIn(group.id)}>{(entry) => <Term entry={entry} />}</For>
            </div>
          </section>
        )}
      </For>
    </>
  );
}
