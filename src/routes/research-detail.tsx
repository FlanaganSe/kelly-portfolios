import { Meta, Title } from "@solidjs/meta";
import { A, useParams } from "@solidjs/router";
import { For, type JSX, Show } from "solid-js";
import { Callout } from "~/components/Callout";
import { DataTable } from "~/components/DataTable";
import { Figure } from "~/components/Figure";
import { PageHeader } from "~/components/PageHeader";
import { Prose } from "~/components/Prose";
import { SourceLink } from "~/components/SourceLink";
import { CertaintyChip, StatusChip } from "~/components/StatusChip";
import { families } from "~/content/families";
import { portfolioById } from "~/content/portfolios";
import { findFund, type ShelfFund } from "~/content/shelf";
import NotFound from "~/routes/not-found";

/**
 * One strategy family.
 *
 * Every page is the same ten sections in the same order, so two families can be compared
 * by scrolling to the same place rather than by trusting whichever page argued harder.
 */

function Section(props: { readonly id: string; readonly title: string; readonly children: JSX.Element }): JSX.Element {
  return (
    <section aria-labelledby={props.id} class="mt-12 border-t border-rule pt-7">
      <h2 id={props.id} class="font-serif text-2xl tracking-[-0.01em]">
        {props.title}
      </h2>
      <div class="mt-4">{props.children}</div>
    </section>
  );
}

const PANEL_SHORT = {
  us: "US",
  "developed-ex-us": "dev ex-US",
  emerging: "EM",
  "aqr-tsmom": "TSMOM",
} as const;

/** Only the tickers the shelf actually carries. A missing one is a content bug, not a row. */
function auditedFunds(tickers: readonly string[]): ShelfFund[] {
  return tickers.map((ticker) => findFund(ticker)).filter((fund): fund is ShelfFund => fund !== undefined);
}

function Points(props: { readonly items: readonly string[] }): JSX.Element {
  return (
    <ul class="max-w-measure space-y-4">
      <For each={props.items}>
        {(item) => <li class="border-l-2 border-rule-strong pl-4 text-base text-ink">{item}</li>}
      </For>
    </ul>
  );
}

export default function ResearchDetail(): JSX.Element {
  const params = useParams<{ slug: string }>();
  const family = () => families.find((one) => one.slug === params.slug);

  return (
    <Show when={family()} fallback={<NotFound />}>
      {(found) => (
        <>
          <Title>{found().name} — Portfolio Edge</Title>
          <Meta name="description" content={found().claim} />

          <nav aria-label="Breadcrumb" class="mb-6 text-sm">
            <A href="/research" class="link">
              Research
            </A>
            <span class="px-2 text-ink-faint">/</span>
            <span class="text-ink-muted">{found().name}</span>
          </nav>

          <PageHeader eyebrow="Research" title={found().name} standfirst={found().claim} lastChecked={found().asOf} />

          <div class="mb-10 flex flex-col gap-6 border-y border-rule py-6 sm:flex-row sm:items-start sm:justify-between sm:gap-10">
            <div class="max-w-measure">
              <p class="eyebrow mb-2">What this means in practice</p>
              <p class="font-serif text-lg text-ink">{found().inPractice}</p>
            </div>
            <Figure
              label={found().headline.label}
              value={found().headline.value}
              size="lg"
              align="end"
              class="shrink-0"
              {...(found().headline.interval === undefined ? {} : { interval: found().headline.interval })}
            />
          </div>

          <div class="flex flex-wrap items-baseline gap-x-8 gap-y-3">
            <CertaintyChip certainty={found().certainty} showGloss />
            <Show when={found().status}>{(status) => <StatusChip status={status()} showGloss />}</Show>
          </div>
          <p class="mt-3 max-w-measure text-sm text-ink-muted">{found().statusReason}</p>
          <Show when={found().headline.note}>
            {(note) => <p class="mt-3 max-w-measure text-sm text-ink-muted">{note()}</p>}
          </Show>

          <Section id="mechanism" title="Why it should exist at all">
            <Prose>
              <p>{found().mechanism}</p>
            </Prose>
          </Section>

          <Section id="for" title="The strongest evidence for it">
            <Points items={found().evidenceFor} />
          </Section>

          <Section id="against" title="The evidence against it">
            <Points items={found().evidenceAgainst} />
          </Section>

          <Section id="failure" title="How it fails">
            <div class="grid gap-6 sm:grid-cols-2">
              <For each={found().failureModes}>
                {(mode) => (
                  <div class="border-t border-rule pt-4">
                    <h3 class="text-base font-semibold text-ink">{mode.title}</h3>
                    <p class="mt-2 text-sm text-ink-muted">{mode.detail}</p>
                  </div>
                )}
              </For>
            </div>
          </Section>

          <Section id="implementation" title="How to hold it, and what it costs">
            <dl class="max-w-measure space-y-6">
              <div>
                <dt class="eyebrow">Implementation</dt>
                <dd class="mt-1.5 text-base">{found().implementation}</dd>
              </div>
              <div>
                <dt class="eyebrow">Cost</dt>
                <dd class="mt-1.5 text-base">{found().cost}</dd>
              </div>
              <div>
                <dt class="eyebrow">What it overlaps with</dt>
                <dd class="mt-1.5 text-base">{found().overlap}</dd>
              </div>
              <div>
                <dt class="eyebrow">Role in a portfolio</dt>
                <dd class="mt-1.5 text-base">{found().roleInPortfolio}</dd>
              </div>
            </dl>

            <Show when={auditedFunds(found().tickers).length > 0}>
              <div class="mt-8">
                <DataTable
                  caption={`Funds audited under ${found().name}, with what each delivers and what it costs.`}
                  columns={[
                    {
                      key: "ticker",
                      header: "Fund",
                      rowHeader: true,
                      cell: (row: ShelfFund) => (
                        <A href={`/funds/${row.ticker}`} data-numeric class="link font-mono text-sm">
                          {row.ticker}
                        </A>
                      ),
                    },
                    { key: "name", header: "Name", cell: (row: ShelfFund) => row.name },
                    {
                      key: "fee",
                      header: "Fee bp",
                      numeric: true,
                      cell: (row: ShelfFund) => row.expenseRatioBp ?? "—",
                    },
                    {
                      key: "turnover",
                      header: "Turnover",
                      numeric: true,
                      cell: (row: ShelfFund) => (row.turnoverPercent === null ? "—" : `${row.turnoverPercent}%`),
                    },
                    {
                      key: "loading",
                      header: "Delivers",
                      cell: (row: ShelfFund) => {
                        const top = [...row.loadings].sort((a, b) => Math.abs(b.value) - Math.abs(a.value))[0];
                        return top === undefined ? (
                          <span class="text-ink-faint">Not regressed here</span>
                        ) : (
                          <span data-numeric>
                            {top.factor} {top.value > 0 ? "+" : ""}
                            {top.value.toFixed(3)}
                            <span class="ml-1 text-xs text-ink-faint">{PANEL_SHORT[top.panel]}</span>
                          </span>
                        );
                      },
                    },
                    {
                      key: "status",
                      header: "Status",
                      cell: (row: ShelfFund) => (
                        <Show when={row.status} fallback={<span class="text-ink-faint">Control</span>}>
                          {(status) => <StatusChip status={status()} />}
                        </Show>
                      ),
                    },
                  ]}
                  rows={auditedFunds(found().tickers)}
                  footnote={
                    <>
                      Every loading names the panel it was measured on. The same fund can read a different sign on a
                      different panel.
                    </>
                  }
                />
              </div>
            </Show>
          </Section>

          <Section id="sources" title="Where this comes from">
            <p class="flex flex-wrap gap-x-6 gap-y-2">
              <For each={found().sources}>{(source) => <SourceLink citation={source} prefix />}</For>
            </p>

            <Show when={found().portfolios.length > 0}>
              <Callout variant="mechanism" label="Portfolios using it" class="mt-8">
                <ul class="space-y-2">
                  <For each={found().portfolios}>
                    {(id) => {
                      const portfolio = portfolioById(id);
                      return portfolio === undefined ? null : (
                        <li>
                          <A href={`/portfolios/${portfolio.id}`} class="link">
                            {portfolio.name}
                          </A>
                          <span class="text-ink-muted"> — {portfolio.thesis}</span>
                        </li>
                      );
                    }}
                  </For>
                </ul>
              </Callout>
            </Show>
          </Section>
        </>
      )}
    </Show>
  );
}
