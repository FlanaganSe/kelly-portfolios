import { Meta, Title } from "@solidjs/meta";
import { A } from "@solidjs/router";
import { For, type JSX, Show } from "solid-js";
import { PageHeader } from "~/components/PageHeader";
import { Prose } from "~/components/Prose";
import { CertaintyChip, StatusChip } from "~/components/StatusChip";
import { families, familiesAsOf, type StrategyFamily } from "~/content/families";
import { DEEP_PAGES } from "~/lib/nav";

/**
 * The research index, grouped by what a strategy claims rather than by file name.
 *
 * The grouping is the argument: contractual results are a different kind of thing from
 * risk premia, and putting them in one undifferentiated list is how a fee reduction ends
 * up quoted beside a factor premium as though the two were equally certain.
 */

interface Group {
  readonly title: string;
  readonly blurb: string;
  readonly slugs: readonly string[];
}

const GROUPS: readonly Group[] = [
  {
    title: "Things whose sign is known in advance",
    blurb:
      "Accounting and statutory facts. They require a view on no market, and they are the largest reliably available result here.",
    slugs: ["structural-and-tax", "placement"],
  },
  {
    title: "Return engines you can buy",
    blurb: "Risk premia. Real pay for real risk, at dispersions that can outlast a working lifetime.",
    slugs: ["value", "momentum", "trend", "quality", "alternatives"],
  },
  {
    title: "Decisions about the portfolio itself",
    blurb: "Not engines. How the money is funded, how often it is moved, and how much of it is in equities at all.",
    slugs: ["capital-efficiency", "rebalancing", "equity-share"],
  },
];

function Entry(props: { readonly family: StrategyFamily }): JSX.Element {
  return (
    <li class="border-t border-rule py-5">
      <div class="flex flex-col gap-1.5 sm:flex-row sm:items-baseline sm:justify-between sm:gap-6">
        <h3 class="font-serif text-xl">
          <A href={`/research/${props.family.slug}`} class="text-ink transition-colors hover:text-accent">
            {props.family.name}
          </A>
        </h3>
        <span class="flex shrink-0 flex-wrap items-baseline gap-x-4 gap-y-1 text-sm">
          <CertaintyChip certainty={props.family.certainty} />
          <Show when={props.family.status}>{(status) => <StatusChip status={status()} />}</Show>
        </span>
      </div>
      <p class="mt-2 max-w-measure text-base text-ink-muted">{props.family.claim}</p>
      <p class="mt-2 flex flex-wrap items-baseline gap-x-2 text-sm">
        <span class="eyebrow">Headline</span>
        <span data-numeric class="font-medium text-ink">
          {props.family.headline.value}
        </span>
        <span class="text-ink-muted">{props.family.headline.label}</span>
      </p>
    </li>
  );
}

export default function Research(): JSX.Element {
  return (
    <>
      <Title>Research — Portfolio Edge</Title>
      <Meta
        name="description"
        content="Ten research families, each put through the same seven questions: mechanism, evidence for, evidence against, failure modes, cost, overlap and role."
      />

      <PageHeader
        eyebrow="Research"
        title={`${families.length} families, each put through the same interrogation`}
        standfirst="The useful comparison between two return engines is not which one sounds better. It is which one survives the same seven questions: mechanism, evidence for, evidence against, failure modes, cost, overlap and role."
        lastChecked={familiesAsOf}
      />

      <Prose class="mb-12">
        <p>
          The status on each entry is this repository's own word, from a closed vocabulary. <em>Rejected</em> means a
          test written down in advance fired — not that the effect is zero. <em>Unresolved</em> means the window could
          not have seen an effect of the size it was looking for. <em>Exploratory</em> is the highest status anything
          here has reached, and it permits a product to stand in for a real one in a later experiment and nothing else.
        </p>
      </Prose>

      <For each={GROUPS}>
        {(group) => (
          <section aria-labelledby={`group-${group.title.replace(/\W+/g, "-").toLowerCase()}`} class="mb-14">
            <h2
              id={`group-${group.title.replace(/\W+/g, "-").toLowerCase()}`}
              class="font-serif text-2xl tracking-[-0.01em]"
            >
              {group.title}
            </h2>
            <p class="mt-2 max-w-measure text-base text-ink-muted">{group.blurb}</p>
            <ul class="mt-6">
              <For each={group.slugs}>
                {(slug) => {
                  const family = families.find((one) => one.slug === slug);
                  return family === undefined ? null : <Entry family={family} />;
                }}
              </For>
            </ul>
          </section>
        )}
      </For>

      <section aria-labelledby="long-form" class="mt-16 border-t border-rule-strong pt-8">
        <h2 id="long-form" class="font-serif text-2xl tracking-[-0.01em]">
          The long-form pages
        </h2>
        <p class="mt-2 max-w-measure text-base text-ink-muted">
          The original working pages, each canonical for what it covers and each going further than the family summary
          above it.
        </p>
        <ul class="mt-6 space-y-3">
          <For each={DEEP_PAGES}>
            {(page) => (
              <li>
                <A href={page.href} class="link">
                  {page.label}
                </A>
              </li>
            )}
          </For>
        </ul>
      </section>
    </>
  );
}
