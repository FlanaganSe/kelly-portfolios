import { Meta, Title } from "@solidjs/meta";
import { A } from "@solidjs/router";
import { For, type JSX } from "solid-js";
import { Callout } from "~/components/Callout";
import { Figure } from "~/components/Figure";
import { PageHeader } from "~/components/PageHeader";
import { Prose } from "~/components/Prose";
import { StatusChip } from "~/components/StatusChip";
import { contractualRows } from "~/content/confidence";
import { edgeBudgetTotal } from "~/content/edgeBudget";
import { highestStatusReached } from "~/content/experiments";
import { families } from "~/content/families";
import { engineMeta, portfolios, type ReturnEngine } from "~/content/portfolios";
import { shelfAudit } from "~/content/shelf";
import { statusMeta } from "~/content/types";
import { CORPUS_AS_OF } from "~/lib/nav";

/**
 * The front page.
 *
 * Every figure is read from `src/content/`. The pairing rule from decision 0007 is
 * structural here rather than incidental: the 109 bp and the index-relative 46 bp appear
 * in the same paragraph, because quoting either alone is how this number gets misused.
 */

function requireRow(id: string) {
  const row = contractualRows.find((one) => one.id === id);
  if (row === undefined) {
    throw new Error(`the confidence record no longer holds "${id}"; a page may not substitute a number for it`);
  }
  return row;
}

const cheapIndex = requireRow("vs-cheap-index");

/** A probability as printed, without inventing precision the arithmetic does not have. */
function formatPercent(probability: number | undefined): string {
  return probability === undefined ? "—" : `${Math.round(probability * 100)}%`;
}

/** The contrast the site is built around: a proposal, and the defensible version of it. */
const FEATURED = ["candidate", "evidence-led"] as const;

const ENGINE_ORDER: readonly ReturnEngine[] = ["cost-and-tax", "equity-beta", "value", "momentum", "trend"];

const ENGINE_VERDICT: Readonly<Record<string, string>> = {
  "cost-and-tax": "The sign is known before the fact. Everything else here is a bet.",
  "equity-beta": "Not an edge. It is the thing an edge is measured against.",
  value: "Decades of dispersion for tens of basis points of expected edge. Size it accordingly.",
  momentum: "Real in the data and excluded on implementation: turnover takes 43% of the gross exposure.",
  trend: "A risk-reduction claim before it is a return claim. The correlation resolves; the mean does not.",
};

function Action(props: { readonly href: string; readonly title: string; readonly detail: string }): JSX.Element {
  return (
    <A href={props.href} class="group block border-t-2 border-rule-strong pt-4 transition-colors hover:border-accent">
      <span class="font-serif text-xl text-ink transition-colors group-hover:text-accent">{props.title}</span>
      <span class="mt-1.5 block max-w-[38ch] text-sm text-ink-muted">{props.detail}</span>
    </A>
  );
}

export default function StartHere(): JSX.Element {
  return (
    <>
      <Title>Portfolio Edge — what beating the market actually costs</Title>
      <Meta
        name="description"
        content="Two benchmarks hide inside “beat the market”. This site prices every route to outperformance the research could measure, says which are facts and which are bets, and lets you size them."
      />

      <PageHeader
        title="Most of what you can reliably win is decided before you pick a fund."
        standfirst="This site prices every route to outperformance that this repository has been able to measure, states which ones are facts and which are bets, and lets you size them yourself. It promises nothing, and it shows its working."
        lastChecked={CORPUS_AS_OF}
      />

      <section aria-labelledby="thesis">
        <Prose>
          <h2 id="thesis">Two benchmarks hide inside “beat the market”</h2>
          <p>
            Almost every claim about outperformance is ambiguous between two comparisons, and the difference between
            them is larger than the effect being argued about.
          </p>
          <p>
            <strong>Against the portfolio you would otherwise have owned</strong> — an expensive fund, in one account,
            on average-cost lots — fee, wrapper, lot method and account placement are worth about{" "}
            <span data-numeric>{edgeBudgetTotal.basisPoints}</span> bp a year, against{" "}
            <span data-numeric>{edgeBudgetTotal.combinedTrackingErrorBp}</span> bp of tracking error. That is{" "}
            {edgeBudgetTotal.ninetyNinePercentConfidence} to 99% confidence. None of it needs a view on any market,
            because every line is an accounting or statutory fact.
          </p>
          <p>
            <strong>Against a cheap index fund</strong>, the same work plus every tilt this repository can defend comes
            to about <span data-numeric>{cheapIndex.edgeBp}</span> bp a year against{" "}
            <span data-numeric>{cheapIndex.trackingErrorBp}</span> bp of tracking error — a{" "}
            <span data-numeric>{formatPercent(cheapIndex.probability30yr)}</span> chance of being ahead after thirty
            years, and {cheapIndex.ninetyPercentAt} to be 90% sure. It is an upper bound on an upper bound.
          </p>
          <p>
            <strong>The two may never be added.</strong> They are different claims about different reference portfolios,
            and this repository's own code raises an error rather than summing them. The interesting consequence is not
            that outperformance is impossible. It is that the reliable part is cheap and immediate, and the exciting
            part is slow and uncertain — which is the reverse of how it is usually sold.
          </p>
        </Prose>
      </section>

      <section aria-labelledby="actions" class="mt-14">
        <h2 id="actions" class="sr-only">
          Where to start
        </h2>
        <div class="grid gap-8 sm:grid-cols-3">
          <Action
            href="/portfolios"
            title={`${portfolios.length} portfolios`}
            detail="Ordered by how much of each construction's case is a fact and how much is a bet. Exact weights, notional exposure, and what would break each one."
          />
          <Action
            href="/lab"
            title="Size it yourself"
            detail="Set an edge and a tracking error and see the wait it implies — the distribution of outcomes, and how long you could sit behind on the way there."
          />
          <Action
            href="/research"
            title={`${families.length} research families`}
            detail="Each put through the same seven questions: mechanism, evidence for, evidence against, failure modes, cost, overlap and role."
          />
        </div>
      </section>

      <section aria-labelledby="candidates" class="mt-16 border-t border-rule pt-8">
        <h2 id="candidates" class="font-serif text-2xl tracking-[-0.01em]">
          The portfolios
        </h2>
        <ul class="mt-6 space-y-6">
          <For each={portfolios}>
            {(portfolio) => (
              <li class="flex flex-col gap-1.5 border-l-2 border-rule-strong pl-4 sm:flex-row sm:items-baseline sm:gap-4">
                <A href={`/portfolios/${portfolio.id}`} class="link shrink-0 font-medium sm:w-52">
                  {portfolio.name}
                </A>
                <span class="max-w-measure text-base text-ink-muted">{portfolio.thesis}</span>
              </li>
            )}
          </For>
        </ul>
      </section>

      <section aria-labelledby="two-portfolios" class="mt-16 border-t border-rule pt-8">
        <h2 id="two-portfolios" class="font-serif text-2xl tracking-[-0.01em]">
          A proposal, and what the evidence supports
        </h2>
        <p class="mt-2 max-w-measure text-base text-ink-muted">
          The same money, arranged two ways. On the left, a construction that diversifies the return engine and accepts
          leverage to do it. On the right, only the lines this repository has measured and can defend, unlevered. One
          runs at 1.32× of its own capital; the other at 1.00×.
        </p>

        <div class="mt-8 grid gap-10 lg:grid-cols-2">
          <For each={FEATURED}>
            {(id) => {
              const portfolio = portfolios.find((one) => one.id === id);
              return portfolio === undefined ? null : (
                <article>
                  <h3 class="font-serif text-xl">
                    <A href={`/portfolios/${portfolio.id}`} class="text-ink transition-colors hover:text-accent">
                      {portfolio.name}
                    </A>
                  </h3>
                  <p class="mt-1.5 max-w-measure text-sm text-ink-muted">{portfolio.thesis}</p>

                  <ul class="mt-5 divide-y divide-rule border-y border-rule">
                    <For each={portfolio.holdings}>
                      {(holding) => (
                        <li class="flex items-baseline justify-between gap-4 py-2">
                          <A href={`/funds/${holding.ticker}`} data-numeric class="link font-mono text-sm">
                            {holding.ticker}
                          </A>
                          <span class="flex-1 text-sm text-ink-faint">{engineMeta[holding.engine].label}</span>
                          <span data-numeric class="font-medium tabular-nums">
                            {holding.percent}%
                          </span>
                        </li>
                      )}
                    </For>
                  </ul>

                  <p class="mt-3 flex items-baseline justify-between gap-4 text-sm">
                    <span class="text-ink-muted">Exposure per unit of capital</span>
                    <span data-numeric class="font-medium">
                      {(portfolio.grossExposurePercent / 100).toFixed(2)}×
                    </span>
                  </p>
                  <p class="mt-4 text-sm">
                    <A href={`/portfolios/${portfolio.id}`} class="link">
                      Why it may outperform, and what would break it
                    </A>
                  </p>
                </article>
              );
            }}
          </For>
        </div>
      </section>

      <section aria-labelledby="engines" class="mt-16 border-t border-rule pt-8">
        <h2 id="engines" class="font-serif text-2xl tracking-[-0.01em]">
          Where a return can actually come from
        </h2>
        <p class="mt-2 max-w-measure text-base text-ink-muted">
          {ENGINE_ORDER.length} engines, in descending order of how certain their sign is. A portfolio is a decision
          about how much of each to hold, and almost every disagreement about investing is really a disagreement about
          this ordering.
        </p>

        <ol class="mt-8 space-y-6">
          <For each={ENGINE_ORDER}>
            {(engine, index) => (
              <li class="flex gap-4 border-t border-rule pt-4">
                <span data-numeric class="shrink-0 text-2xl font-semibold text-ink-faint tabular-nums">
                  {index() + 1}
                </span>
                <div>
                  <h3 class="text-base font-semibold text-ink">{engineMeta[engine].label}</h3>
                  <p class="mt-1 max-w-measure text-sm text-ink-muted">{engineMeta[engine].gloss}</p>
                  <p class="mt-1.5 max-w-measure text-sm text-ink">{ENGINE_VERDICT[engine]}</p>
                </div>
              </li>
            )}
          </For>
        </ol>
      </section>

      <section aria-labelledby="evidence" class="mt-16 border-t border-rule pt-8">
        <h2 id="evidence" class="font-serif text-2xl tracking-[-0.01em]">
          What the evidence is worth
        </h2>

        <div class="mt-6 flex flex-wrap gap-x-12 gap-y-8">
          <Figure label="Highest status reached, anywhere" value={statusMeta[highestStatusReached].label} size="md" />
          <Figure
            label="US factor loadings surviving correction"
            value={`${shelfAudit.loadingsSurvivingCorrection} of ${shelfAudit.usProductsAudited}`}
            size="md"
          />
          <Figure
            label="Alpha tests surviving correction"
            value={`${shelfAudit.alphaTestsSurviving} of ${shelfAudit.alphaTests}`}
            size="md"
            note={shelfAudit.alphaTestsSurvivingAllNegative ? "All five negative." : undefined}
          />
        </div>

        <Prose class="mt-8">
          <p>
            Exposure is measurable and skill is not. A fund's factor loadings can be estimated tightly enough to act on;
            its alpha cannot. The median alpha this instrument could detect is{" "}
            <span data-numeric>{shelfAudit.medianDetectableAlphaUsPpYr}</span> percentage points a year, against a true
            cross-sectional dispersion of about <span data-numeric>{shelfAudit.trueAlphaDispersionPpYr}</span>. So a
            portfolio built out of loadings rests on something that can be estimated, and one built out of alpha does
            not.
          </p>
          <p>
            Nothing here is promoted. The status vocabulary is closed and nothing has passed <em>exploratory</em>, which
            permits a product to stand in for a real one in a later experiment and permits nothing else.{" "}
            <em>Rejected</em> means a test written down in advance fired — not that the effect is zero.
          </p>
        </Prose>

        <div class="mt-6 flex flex-wrap gap-x-8 gap-y-3">
          <StatusChip status="exploratory" showGloss />
          <StatusChip status="unresolved" showGloss />
          <StatusChip status="rejected" showGloss />
        </div>
      </section>

      <section aria-labelledby="reading" class="mt-16 border-t border-rule pt-8">
        <h2 id="reading" class="font-serif text-2xl tracking-[-0.01em]">
          The highest-value research
        </h2>
        <ul class="mt-6 space-y-5">
          <For each={families.slice(0, 5)}>
            {(family) => (
              <li class="border-l-2 border-rule-strong pl-4">
                <A href={`/research/${family.slug}`} class="link font-medium">
                  {family.name}
                </A>
                <p class="mt-1 max-w-measure text-sm text-ink-muted">{family.claim}</p>
              </li>
            )}
          </For>
        </ul>
      </section>

      <Callout variant="caveat" label="What this is not" class="mt-16">
        <p>
          Nothing here is advice, and no sleeve in the underlying research is promoted. No page forecasts any market's
          return, and no number on this site is a claim that a portfolio will beat an index.
        </p>
      </Callout>
    </>
  );
}
