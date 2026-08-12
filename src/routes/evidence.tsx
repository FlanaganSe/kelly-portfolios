import { Title } from "@solidjs/meta";
import { useSearchParams } from "@solidjs/router";
import { For, Show } from "solid-js";
import { Callout } from "~/components/Callout";
import { DataTable } from "~/components/DataTable";
import { Figure } from "~/components/Figure";
import { PageHeader } from "~/components/PageHeader";
import { Prose } from "~/components/Prose";
import { SourceLink } from "~/components/SourceLink";
import { StatusChip } from "~/components/StatusChip";
import {
  type Experiment,
  experiments,
  highestStatusReached,
  ledgerSummary,
  type RunState,
} from "~/content/experiments";
import { factorPremia, sharedExposures, sleeves } from "~/content/sleeves";
import { type EvidenceStatus, statusMeta } from "~/content/types";

/**
 * The receipts page. Every experiment family, what it asked, what it found, and
 * where it landed in the closed status vocabulary — filterable by that status.
 */

const H2 = "font-sans text-xl font-semibold tracking-[-0.015em] text-ink";

const RUN_STATE_LABEL: Readonly<Record<RunState, string>> = {
  synthesised: "Synthesised",
  "run-not-synthesised": "Run, not synthesised",
  "specified-not-run": "Specified, not run",
};

const KIND_LABEL = { confirmatory: "Confirmatory", exploratory: "Exploratory" } as const;

/** A status, or the absence of one. Derived from the data, so it cannot drift. */
type FilterKey = EvidenceStatus | "none";

const FILTER_KEYS: readonly FilterKey[] = [...new Set(experiments.map((entry) => entry.status ?? "none"))];

const keyOf = (entry: Experiment): FilterKey => entry.status ?? "none";
const labelOf = (key: FilterKey): string => (key === "none" ? "No status yet" : statusMeta[key].label);
const countOf = (key: FilterKey): number => experiments.filter((entry) => keyOf(entry) === key).length;

const rebalancing = experiments.find((entry) => entry.id === "exp-003-rebalancing");
const rejectedPremia = factorPremia.filter((premium) => premium.status === "rejected");
const rebalancingSleeve = sleeves.find((sleeve) => sleeve.id === "rebalancing-as-return");

function Tickbox(props: { readonly on: boolean }) {
  return (
    <svg viewBox="0 0 12 12" width="11" height="11" aria-hidden="true" class="shrink-0">
      <rect x="1" y="1" width="10" height="10" rx="2" fill="none" stroke="currentColor" stroke-width="1.2" />
      <Show when={props.on}>
        <path
          d="M3.1 6.2 5.1 8.2 8.9 4.1"
          fill="none"
          stroke="currentColor"
          stroke-width="1.7"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </Show>
    </svg>
  );
}

function ExperimentEntry(props: { readonly entry: Experiment }) {
  return (
    <details class="border-b border-rule py-1 [&[open]>summary]:border-b [&[open]>summary]:border-rule">
      <summary class="cursor-pointer list-none py-3 marker:content-none">
        <span class="flex flex-wrap items-baseline gap-x-3 gap-y-2">
          <span data-numeric class="eyebrow">
            {props.entry.number}
          </span>
          <span class="font-sans font-medium text-ink">{props.entry.title}</span>
          <Show when={props.entry.status} fallback={<span class="text-sm text-ink-faint">No status yet</span>}>
            {(status) => <StatusChip status={status()} />}
          </Show>
          <span class="text-sm text-ink-faint">
            {KIND_LABEL[props.entry.kind]} · {RUN_STATE_LABEL[props.entry.runState]}
          </span>
        </span>
      </summary>

      <div class="py-5">
        <p class="max-w-measure font-serif text-lg text-ink">{props.entry.question}</p>
        <p class="mt-4 max-w-measure text-ink-muted">{props.entry.verdict}</p>

        <Show when={props.entry.statusNote}>
          {(note) => (
            <Callout variant="caveat" label="How to read the status">
              <p>{note()}</p>
            </Callout>
          )}
        </Show>

        <DataTable
          class="my-6"
          caption={`Key numbers, ${props.entry.title}`}
          columns={[
            { key: "label", header: "Figure", rowHeader: true, cell: (row) => row.label },
            {
              key: "value",
              header: "Value",
              numeric: true,
              cell: (row) => (
                <span class="whitespace-nowrap">
                  {row.value}
                  <Show when={row.unit}>{(unit) => <span class="ml-1 text-ink-muted">{unit()}</span>}</Show>
                </span>
              ),
            },
            { key: "interval", header: "Interval", numeric: true, cell: (row) => row.interval ?? "—" },
            { key: "note", header: "What qualifies it", cell: (row) => row.note ?? "" },
          ]}
          rows={props.entry.keyNumbers}
          footnote={<SourceLink citation={props.entry.source} prefix />}
        />

        <p class="eyebrow">Why it matters</p>
        <p class="mt-1 max-w-measure text-ink">{props.entry.whyItMatters}</p>

        <p class="eyebrow mt-5">What would change it</p>
        <ul class="mt-1 flex max-w-measure list-disc flex-col gap-1 pl-5 text-ink-muted marker:text-ink-faint">
          <For each={props.entry.whatWouldChangeIt}>{(item) => <li>{item}</li>}</For>
        </ul>
      </div>
    </details>
  );
}

export default function Evidence() {
  const [params, setParams] = useSearchParams<{ status?: string }>();

  const selected = () => new Set((params.status ?? "").split(",").filter(Boolean));
  const isOn = (key: FilterKey) => selected().has(key);
  const visible = () => {
    const chosen = selected();
    return chosen.size === 0 ? experiments : experiments.filter((entry) => chosen.has(keyOf(entry)));
  };

  const toggle = (key: FilterKey) => {
    const next = new Set(selected());
    if (next.has(key)) next.delete(key);
    else next.add(key);
    setParams({ status: next.size > 0 ? [...next].join(",") : undefined }, { replace: true });
  };

  const clear = () => setParams({ status: undefined }, { replace: true });

  return (
    <>
      <Title>Evidence — Portfolio Edge</Title>
      <PageHeader
        title="Evidence"
        standfirst="Every experiment family, what it asked, what it found, and the status it earned. Most of them found nothing, which is the point."
        lastChecked={ledgerSummary.asOf}
      />

      <Prose as="section">
        <p>
          {ledgerSummary.experimentFamilies} experiment families, {ledgerSummary.distinctSpecifications} distinct frozen
          specifications, {ledgerSummary.runs} runs and {ledgerSummary.entries} ledger entries. No sleeve was promoted.
          The highest rung anything here reached is <em>{statusMeta[highestStatusReached].label.toLowerCase()}</em>,
          which permits a product to stand in for a real one in a later experiment and permits nothing else.
        </p>
        <p>
          The specification count is the one that matters for a search-adjusted result: repeated executions of the same
          frozen specification are not independent hypotheses, so the trial count starts at{" "}
          {ledgerSummary.distinctSpecifications}, not {ledgerSummary.runs}.
        </p>
      </Prose>

      <div class="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <Figure label="Experiment families" value={String(ledgerSummary.experimentFamilies)} />
        <Figure
          label="Distinct specifications"
          value={String(ledgerSummary.distinctSpecifications)}
          note={`Across ${ledgerSummary.runs} runs.`}
        />
        <Figure
          label="Runs consuming the final holdout"
          value={String(ledgerSummary.runsConsumingTheFinalHoldout)}
          note="The 2026-01-onward window is unread in every file."
        />
        <Figure
          label="Sleeves promoted"
          value="0"
          note="Nothing reached walk-forward tested, or independently reproduced."
          source={ledgerSummary.source}
          asOf={ledgerSummary.asOf}
        />
      </div>

      <section aria-labelledby="ledger" class="mt-14">
        <h2 id="ledger" class={H2}>
          Where the runs ended up
        </h2>
        <p class="mt-2 max-w-measure text-ink-muted">
          The ledger is append-only and counts failures and abandoned runs as well as finished ones. A run that produced
          no terminal status still costs a look at the data.
        </p>

        <DataTable
          class="mt-6"
          caption="Terminal outcomes across the committed ledger"
          columns={[
            {
              key: "status",
              header: "Outcome",
              rowHeader: true,
              cell: (row) => <StatusChip status={row.status} />,
            },
            { key: "runs", header: "Runs", numeric: true, cell: (row) => row.runs },
            { key: "which", header: "Which", cell: (row) => row.which },
          ]}
          rows={ledgerSummary.terminalOutcomes}
          footnote={<SourceLink citation={ledgerSummary.source} prefix />}
        />

        <p class="mt-4 max-w-measure text-ink-muted">
          A further <span data-numeric>{ledgerSummary.noTerminalStatus.runs}</span> runs reached no terminal status at
          all: {ledgerSummary.noTerminalStatus.which}. They are counted because a run that saw the data has spent some
          of it.
        </p>
        <p class="mt-3 max-w-measure text-sm text-ink-muted">{ledgerSummary.note}</p>
      </section>

      <section aria-labelledby="rejections" class="mt-14">
        <h2 id="rejections" class={H2}>
          The main product is rejections
        </h2>
        <p class="mt-2 max-w-measure text-ink-muted">
          Several of the things this project set out to find are now closed rather than open. That is the output, and it
          is worth more than another unresolved maybe.
        </p>

        <Show when={rebalancing}>
          {(entry) => (
            <div class="mt-8">
              <h3 class="font-sans text-base font-semibold text-ink">
                Rebalancing is not a source of return, and it was measured
              </h3>
              <div class="mt-4 grid gap-6 sm:grid-cols-2">
                <For each={entry().keyNumbers.slice(0, 2)}>
                  {(number) => <Figure {...number} tone="negative" size="lg" source={entry().source} />}
                </For>
              </div>
              <p class="mt-5 max-w-measure text-ink-muted">{entry().verdict}</p>
              <Show when={rebalancingSleeve?.caveat}>
                {(caveat) => (
                  <Callout variant="caveat" label="What it did buy">
                    <p>{caveat()}</p>
                  </Callout>
                )}
              </Show>
            </div>
          )}
        </Show>

        <div class="mt-10">
          <h3 class="font-sans text-base font-semibold text-ink">
            Profitability and investment are closed on public data
          </h3>
          <p class="mt-2 max-w-measure text-ink-muted">
            Closed is stronger than open and weaker than zero. The premium may be there; the publicly available data
            cannot sign it, and more of the same data provably will not.
          </p>
          <div class="mt-6 grid gap-8 sm:grid-cols-2">
            <For each={rejectedPremia}>
              {(premium) => (
                <div>
                  <Show when={premium.pooledPremium}>
                    {(value) => (
                      <Figure
                        label={`${premium.label}, pooled post-publication`}
                        value={value()}
                        interval={premium.pooledInterval ?? undefined}
                        note={
                          premium.detectionThreshold
                            ? `Smallest premium the window could have detected: ${premium.detectionThreshold}.`
                            : undefined
                        }
                        source={premium.source}
                      />
                    )}
                  </Show>
                  <p class="mt-3 max-w-measure text-sm text-ink-muted">{premium.statusNote}</p>
                </div>
              )}
            </For>
          </div>
        </div>
      </section>

      <section aria-labelledby="families" class="mt-14">
        <h2 id="families" class={H2}>
          The experiment families
        </h2>
        <p class="mt-2 max-w-measure text-ink-muted">
          Each entry opens to its question, its verdict, its numbers with their intervals, and what would change it.
        </p>

        <div class="mt-6 border-y border-rule py-4">
          <fieldset class="border-0 p-0">
            <legend class="eyebrow mb-3">Filter by status</legend>
            <div class="flex flex-wrap items-center gap-2">
              <For each={FILTER_KEYS}>
                {(key) => (
                  <button
                    type="button"
                    aria-pressed={isOn(key)}
                    onClick={() => toggle(key)}
                    class={`inline-flex items-center gap-2 rounded-[3px] border px-2.5 py-1.5 text-sm transition-colors ${
                      isOn(key)
                        ? "border-accent bg-accent-soft font-medium text-ink"
                        : "border-rule text-ink-muted hover:border-rule-strong hover:text-ink"
                    }`}
                  >
                    <Tickbox on={isOn(key)} />
                    {labelOf(key)}
                    <span data-numeric class="text-ink-faint">
                      {countOf(key)}
                    </span>
                  </button>
                )}
              </For>
              <button
                type="button"
                onClick={clear}
                disabled={selected().size === 0}
                class="rounded-[3px] px-2.5 py-1.5 text-sm text-ink-muted underline decoration-rule-strong underline-offset-4 transition-colors hover:text-ink disabled:text-ink-faint disabled:no-underline"
              >
                Show all
              </button>
            </div>
          </fieldset>
          <p aria-live="polite" class="mt-3 text-sm text-ink-muted">
            Showing <span data-numeric>{visible().length}</span> of <span data-numeric>{experiments.length}</span>{" "}
            families.
          </p>
        </div>

        <div class="mt-2">
          <For each={visible()}>{(entry) => <ExperimentEntry entry={entry} />}</For>
        </div>
      </section>

      <section aria-labelledby="premia" class="mt-14">
        <h2 id="premia" class={H2}>
          The premia underneath the products
        </h2>
        <p class="mt-2 max-w-measure text-ink-muted">
          Gross, long-short and not investable. A long-only holder receives a fraction of any of these, and the fraction
          depends on a benchmark nobody here has settled.
        </p>

        <DataTable
          class="mt-6"
          caption="Factor premia, pooled across the US, developed ex-US and emerging markets, over the frozen post-publication era"
          columns={[
            { key: "factor", header: "Factor", rowHeader: true, cell: (row) => row.label },
            {
              key: "status",
              header: "Status",
              cell: (row) => (
                <Show when={row.status} fallback={<span class="text-ink-faint">No status</span>}>
                  {(status) => <StatusChip status={status()} />}
                </Show>
              ),
            },
            { key: "pooled", header: "Pooled premium", numeric: true, cell: (row) => row.pooledPremium ?? "—" },
            { key: "interval", header: "Interval", numeric: true, cell: (row) => row.pooledInterval ?? "—" },
            {
              key: "threshold",
              header: "Detection threshold",
              numeric: true,
              cell: (row) => row.detectionThreshold ?? "—",
            },
            { key: "regions", header: "Effective regions", cell: (row) => row.effectiveRegions ?? "—" },
          ]}
          rows={factorPremia}
          footnote="A premium smaller than its own detection threshold is a premium the window could not have found, whatever the interval says."
        />

        <div class="mt-8 flex flex-col gap-4">
          <For each={factorPremia}>
            {(premium) => (
              <div class="max-w-measure border-t border-rule pt-4">
                <p class="font-sans text-sm font-semibold text-ink">{premium.label}</p>
                <p class="mt-1 text-ink-muted">{premium.statusNote}</p>
                <Show when={premium.longOnlyCapture}>
                  {(capture) => (
                    <p class="mt-2 text-sm text-ink-muted">
                      <span class="eyebrow">Long-only capture </span>
                      {capture()}
                    </p>
                  )}
                </Show>
                <p class="mt-2">
                  <SourceLink citation={premium.source} prefix />
                </p>
              </div>
            )}
          </For>
        </div>
      </section>

      <section aria-labelledby="shared" class="mt-14">
        <h2 id="shared" class={H2}>
          What these bets share
        </h2>
        <p class="mt-2 max-w-measure text-ink-muted">
          Counting sleeves is not counting bets. These are the exposures that do not diversify each other away.
        </p>
        <ul class="mt-5 flex max-w-measure list-disc flex-col gap-2 pl-5 text-ink-muted marker:text-ink-faint">
          <For each={sharedExposures}>{(item) => <li>{item}</li>}</For>
        </ul>
      </section>
    </>
  );
}
