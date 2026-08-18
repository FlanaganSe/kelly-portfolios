import { Title } from "@solidjs/meta";
import { A, useParams } from "@solidjs/router";
import { For, type JSX, Show } from "solid-js";
import { Callout } from "~/components/Callout";
import { DataTable } from "~/components/DataTable";
import { Figure } from "~/components/Figure";
import { OutperformanceChart, type OutperformanceSeries } from "~/components/OutperformanceChart";
import { PageHeader } from "~/components/PageHeader";
import { Prose } from "~/components/Prose";
import { ExposureBar } from "~/components/portfolio/ExposureBar";
import { SourceLink } from "~/components/SourceLink";
import { CertaintyChip, StatusChip } from "~/components/StatusChip";
import { families } from "~/content/families";
import {
  engineMeta,
  type PortfolioCandidate,
  type PortfolioHolding,
  portfolioById,
  portfolios,
  weightByEngine,
} from "~/content/portfolios";
import NotFound from "~/routes/not-found";

/**
 * One portfolio, told as an argument rather than as a dashboard.
 *
 * The order is fixed across all four: what it claims, what it holds, what it is exposed
 * to, what it might earn and at what dispersion, what would break it, what it costs, and
 * what to read next. A reader comparing two portfolios is comparing the same sections in
 * the same order.
 */

function Section(props: { readonly id: string; readonly title: string; readonly children: JSX.Element }): JSX.Element {
  return (
    <section aria-labelledby={props.id} class="mt-14 border-t border-rule pt-8 first:mt-0 first:border-t-0 first:pt-0">
      <h2 id={props.id} class="font-serif text-2xl tracking-[-0.01em]">
        {props.title}
      </h2>
      <div class="mt-4">{props.children}</div>
    </section>
  );
}

function holdingColumns() {
  return [
    {
      key: "ticker",
      header: "Fund",
      rowHeader: true,
      cell: (row: PortfolioHolding) => (
        <span data-numeric class="font-mono text-sm">
          {row.ticker}
        </span>
      ),
    },
    {
      key: "weight",
      header: "Weight",
      numeric: true,
      width: "5.5rem",
      cell: (row: PortfolioHolding) => `${row.percent}%`,
    },
    {
      key: "engine",
      header: "Buys",
      width: "10rem",
      cell: (row: PortfolioHolding) => engineMeta[row.engine].label,
    },
    {
      key: "status",
      header: "Evidence",
      width: "9rem",
      cell: (row: PortfolioHolding) => (
        <Show when={row.status} fallback={<span class="text-ink-faint">Control</span>}>
          {(status) => <StatusChip status={status()} />}
        </Show>
      ),
    },
    {
      key: "why",
      header: "Why it is here",
      cell: (row: PortfolioHolding) => <span class="text-ink-muted">{row.why}</span>,
    },
  ];
}

/**
 * The page's sections, in render order. Kept beside the render rather than derived from
 * the DOM so that a section that is conditionally absent — a portfolio with nothing
 * priced, or with no suggested changes — never leaves a dead anchor in the contents.
 */
function sectionsOf(portfolio: PortfolioCandidate): { id: string; title: string }[] {
  return [
    { id: "allocation", title: "What it holds" },
    { id: "why", title: "Why it may outperform" },
    { id: "why-not", title: "Why it may not" },
    ...(portfolio.priced.length > 0 ? [{ id: "priced", title: "What each line is worth" }] : []),
    { id: "failure", title: "What would break it" },
    { id: "holding-it", title: "Cost, tax and placement" },
    ...(portfolio.suggestedChanges === undefined ? [] : [{ id: "changes", title: "What the evidence would change" }]),
    { id: "evidence", title: "How much is evidence" },
    { id: "next", title: "Where to go next" },
  ];
}

/** Only a line with dispersion belongs on a probability curve. */
function chartSeries(portfolio: PortfolioCandidate): OutperformanceSeries[] {
  return portfolio.priced
    .filter((line) => line.edgeBp !== null && (line.trackingErrorBp ?? 0) > 0)
    .map((line, index) => ({
      id: `${portfolio.id}-${index}`,
      label: line.label.length > 26 ? `${line.label.slice(0, 25)}…` : line.label,
      abbr: `${line.edgeBp}/${line.trackingErrorBp} bp`,
      fullLabel: line.label,
      edgeBp: line.edgeBp ?? 0,
      trackingErrorBp: line.trackingErrorBp ?? 0,
      kind: line.certainty === "contractual" ? ("contractual" as const) : ("probabilistic" as const),
    }));
}

export default function PortfolioDetail(): JSX.Element {
  const params = useParams<{ id: string }>();
  const portfolio = () => portfolioById(params.id);

  return (
    <Show when={portfolio()} fallback={<NotFound />}>
      {(found) => {
        const engines = () =>
          weightByEngine(found()).map((one) => ({
            id: one.engine,
            label: engineMeta[one.engine].label,
            percent: one.percent,
          }));
        const notional = () =>
          found().notional.map((one) => ({ id: one.label, label: one.label, percent: one.percent, note: one.note }));
        const related = () => families.filter((family) => family.portfolios.includes(found().id));
        const series = () => chartSeries(found());

        return (
          <>
            <Title>{found().name} — Portfolio Edge</Title>

            <nav aria-label="Breadcrumb" class="mb-6 text-sm">
              <A href="/portfolios" class="link">
                Portfolios
              </A>
              <span class="px-2 text-ink-faint">/</span>
              <span class="text-ink-muted">{found().name}</span>
            </nav>

            <PageHeader
              eyebrow="Portfolio"
              title={found().name}
              standfirst={found().thesis}
              lastChecked={found().asOf}
            />

            <Prose class="mb-2">
              <p>
                <strong>Who it is for.</strong> {found().forWhom}
              </p>
            </Prose>

            <nav aria-labelledby="on-this-page" class="mt-8 border-y border-rule py-4">
              <h2 id="on-this-page" class="eyebrow mb-3">
                On this page
              </h2>
              <ul class="flex flex-wrap gap-x-6 gap-y-2 text-sm">
                <For each={sectionsOf(found())}>
                  {(section) => (
                    <li>
                      <a href={`#${section.id}`} class="link">
                        {section.title}
                      </a>
                    </li>
                  )}
                </For>
              </ul>
            </nav>

            <Section id="allocation" title="What it holds">
              <DataTable
                caption={`${found().name}: exact allocation, summing to 100% of capital.`}
                columns={holdingColumns()}
                rows={found().holdings}
                footnote={
                  <>
                    Weights are percentages of capital and sum to exactly 100%.{" "}
                    <Show when={found().grossExposurePercent > 100}>
                      They do <em>not</em> describe this portfolio's exposure — see the next block.
                    </Show>
                  </>
                }
              />

              <div class="mt-8 grid gap-8 lg:grid-cols-2">
                <ExposureBar
                  segments={engines()}
                  ariaLabel={`Capital weight by return engine: ${engines()
                    .map((one) => `${one.label} ${one.percent}%`)
                    .join(", ")}.`}
                  caption="Capital weight by return engine."
                />

                <Show when={notional().length > 0}>
                  <ExposureBar
                    segments={notional()}
                    scaleTo={100}
                    ariaLabel={`Notional exposure per 100 units of capital: ${notional()
                      .map((one) => `${one.label} ${one.percent}%`)
                      .join(", ")}. Total ${found().grossExposurePercent}%.`}
                    caption={
                      <>
                        Notional exposure per 100 of capital. The bar overflows because the portfolio is exposed to{" "}
                        <span data-numeric>{found().grossExposurePercent}%</span> of its own capital.
                      </>
                    }
                  />
                </Show>
              </div>

              <Show when={notional().some((one) => one.note !== undefined)}>
                <ul class="mt-4 max-w-measure space-y-1 text-sm text-ink-muted">
                  <For each={notional().filter((one) => one.note !== undefined)}>
                    {(line) => (
                      <li>
                        <span class="font-medium text-ink">{line.label}.</span> {line.note}
                      </li>
                    )}
                  </For>
                </ul>
              </Show>
            </Section>

            <Section id="why" title="Why it may outperform">
              <ul class="max-w-measure space-y-4">
                <For each={found().mayOutperform}>
                  {(reason) => <li class="border-l-2 border-rule-strong pl-4 text-base text-ink">{reason}</li>}
                </For>
              </ul>
            </Section>

            <Section id="why-not" title="Why it may not">
              <ul class="max-w-measure space-y-4">
                <For each={found().mayUnderperform}>
                  {(reason) => <li class="border-l-2 border-rule-strong pl-4 text-base text-ink">{reason}</li>}
                </For>
              </ul>
            </Section>

            <Show when={found().priced.length > 0}>
              <Section id="priced" title="What each line is worth, and at what dispersion">
                <Prose class="mb-6">
                  <p>
                    A tilt quoted as an expected return without its tracking error is not reportable here. Each line
                    below carries both, along with the status of the evidence behind it and the page that owns the
                    figure.
                  </p>
                </Prose>

                <div class="grid gap-x-10 gap-y-8 sm:grid-cols-2">
                  <For each={found().priced}>
                    {(line) => (
                      <div class="border-t border-rule pt-4">
                        <p class="text-sm font-medium text-ink">{line.label}</p>
                        <div class="mt-3 flex flex-wrap items-baseline gap-x-8 gap-y-3">
                          <Show when={line.edgeBp !== null}>
                            <Figure
                              label="Expected edge"
                              value={`${(line.edgeBp ?? 0) > 0 ? "+" : ""}${line.edgeBp}`}
                              unit="bp/yr"
                              size="md"
                            />
                          </Show>
                          <Show when={(line.trackingErrorBp ?? 0) > 0}>
                            <Figure label="Tracking error" value={`${line.trackingErrorBp}`} unit="bp/yr" size="md" />
                          </Show>
                          <Show when={line.growthBp !== null}>
                            <Figure
                              label="Growth contribution"
                              value={`${(line.growthBp ?? 0) > 0 ? "+" : ""}${line.growthBp}`}
                              unit="bp/yr"
                              size="md"
                            />
                          </Show>
                        </div>
                        <p class="mt-3 max-w-measure text-sm text-ink-muted">{line.horizonNote}</p>
                        <p class="mt-3 flex flex-wrap items-baseline gap-x-4 gap-y-2">
                          <CertaintyChip certainty={line.certainty} />
                          <Show when={line.status}>{(status) => <StatusChip status={status()} />}</Show>
                          <SourceLink citation={line.source} prefix />
                        </p>
                      </div>
                    )}
                  </For>
                </div>

                <Show when={series().length > 0}>
                  <div class="mt-12">
                    <OutperformanceChart
                      series={series()}
                      horizonYears={30}
                      ariaLabel={`Probability that each priced line of ${found().name} is ahead of its benchmark, against holding period.`}
                      caption={
                        <>
                          Each curve is <code>P = Φ(e√T / s)</code> for that line's edge and tracking error. The
                          horizontal axis is square-rooted because the probability runs on √T. This is arithmetic on a
                          stated edge, not a forecast: if the edge is wrong, so is the curve.
                        </>
                      }
                      tableCaption={`Probability ahead of benchmark by horizon, ${found().name}.`}
                    />
                  </div>
                </Show>
              </Section>
            </Show>

            <Section id="failure" title="What would break it">
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

              <Callout variant="caveat" label="Tracking error" class="mt-8">
                <p>{found().trackingErrorCharacter}</p>
              </Callout>
            </Section>

            <Section id="holding-it" title="Cost, tax, rebalancing and where it is held">
              <dl class="max-w-measure space-y-6">
                <div>
                  <dt class="eyebrow">Tax</dt>
                  <dd class="mt-1.5 text-base">{found().tax}</dd>
                </div>
                <div>
                  <dt class="eyebrow">Rebalancing</dt>
                  <dd class="mt-1.5 text-base">{found().rebalancing}</dd>
                </div>
                <div>
                  <dt class="eyebrow">Account placement</dt>
                  <dd class="mt-1.5 text-base">{found().placement}</dd>
                </div>
                <div>
                  <dt class="eyebrow">Benchmark</dt>
                  <dd class="mt-1.5 text-base">{found().benchmark.why}</dd>
                </div>
              </dl>
            </Section>

            <Show when={found().suggestedChanges}>
              {(changes) => (
                <Section id="changes" title="What this evidence would change">
                  <p class="mb-6 max-w-measure text-base text-ink-muted">
                    Specific swaps, not a general warning. Each is editorial — this repository promotes no sleeve — but
                    each rests on a measurement named beside it.
                  </p>
                  <ol class="max-w-measure space-y-6">
                    <For each={changes()}>
                      {(one, index) => (
                        <li class="flex gap-4 border-t border-rule pt-4">
                          <span data-numeric class="shrink-0 text-lg font-semibold text-ink-faint tabular-nums">
                            {String(index() + 1).padStart(2, "0")}
                          </span>
                          <div>
                            <p class="text-base font-semibold text-ink">{one.change}</p>
                            <p class="mt-1.5 text-sm text-ink-muted">{one.because}</p>
                          </div>
                        </li>
                      )}
                    </For>
                  </ol>
                </Section>
              )}
            </Show>

            <Section id="evidence" title="How much of this is evidence">
              <Prose>
                <p>{found().evidenceSummary}</p>
              </Prose>
              <Callout variant="open-question" label="Where this is editorial" class="mt-6">
                <p>{found().editorialNote}</p>
              </Callout>
              <p class="mt-6 flex flex-wrap gap-x-6 gap-y-2">
                <For each={found().sources}>{(source) => <SourceLink citation={source} prefix />}</For>
              </p>
            </Section>

            <Section id="next" title="Where to go next">
              <ul class="max-w-measure space-y-3">
                <li>
                  <A href={`/lab?from=${found().id}`} class="link font-medium">
                    Open this portfolio in the lab
                  </A>
                  <span class="text-ink-muted"> — change the weights and see what the edge and the wait become.</span>
                </li>
                <For each={related()}>
                  {(family) => (
                    <li>
                      <A href={`/research/${family.slug}`} class="link">
                        {family.name}
                      </A>
                      <span class="text-ink-muted"> — {family.claim}</span>
                    </li>
                  )}
                </For>
                <For each={portfolios.filter((one) => one.id !== found().id)}>
                  {(other) => (
                    <li>
                      <A href={`/portfolios/${other.id}`} class="link">
                        {other.name}
                      </A>
                      <span class="text-ink-muted"> — {other.thesis}</span>
                    </li>
                  )}
                </For>
              </ul>
            </Section>
          </>
        );
      }}
    </Show>
  );
}
