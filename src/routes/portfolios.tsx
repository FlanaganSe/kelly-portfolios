import { Title } from "@solidjs/meta";
import { A } from "@solidjs/router";
import { For, type JSX, Show } from "solid-js";
import { PageHeader } from "~/components/PageHeader";
import { Prose } from "~/components/Prose";
import { ExposureBar } from "~/components/portfolio/ExposureBar";
import { engineMeta, type PortfolioCandidate, portfolios, portfoliosAsOf, weightByEngine } from "~/content/portfolios";

/**
 * The portfolio library.
 *
 * Ordered by how much of each construction's case is contractual and how much is a bet,
 * which is the only ordering that says something. It is deliberately not ordered by
 * expected return: three of the four have no expected return this repository will state.
 */

const complexityLabel = { low: "Low", moderate: "Moderate", high: "High" } as const;

function Card(props: { readonly portfolio: PortfolioCandidate }): JSX.Element {
  const engines = () =>
    weightByEngine(props.portfolio).map((one) => ({
      id: one.engine,
      label: engineMeta[one.engine].label,
      percent: one.percent,
    }));

  return (
    <article class="border-t border-rule-strong py-8 first:border-t-0 first:pt-0">
      <div class="flex flex-col gap-6 lg:flex-row lg:gap-10">
        <div class="lg:w-3/5">
          <h2 class="font-serif text-2xl tracking-[-0.01em]">
            <A href={`/portfolios/${props.portfolio.id}`} class="text-ink transition-colors hover:text-accent">
              {props.portfolio.name}
            </A>
          </h2>
          <p class="mt-2 max-w-measure font-serif text-lg text-ink-muted">{props.portfolio.thesis}</p>

          <dl class="mt-5 flex flex-wrap gap-x-8 gap-y-3 text-sm">
            <div>
              <dt class="eyebrow">Holdings</dt>
              <dd data-numeric class="mt-0.5 font-medium">
                {props.portfolio.holdings.length}
              </dd>
            </div>
            <div>
              <dt class="eyebrow">Gross exposure</dt>
              <dd data-numeric class="mt-0.5 font-medium">
                {props.portfolio.grossExposurePercent}%
              </dd>
            </div>
            <div>
              <dt class="eyebrow">Complexity</dt>
              <dd class="mt-0.5 font-medium">{complexityLabel[props.portfolio.complexity]}</dd>
            </div>
            <div>
              <dt class="eyebrow">Benchmark</dt>
              <dd class="mt-0.5 font-medium">{props.portfolio.benchmark.label}</dd>
            </div>
          </dl>

          <p class="mt-5 max-w-measure text-sm text-ink-muted">{props.portfolio.evidenceSummary}</p>

          <p class="mt-5 flex flex-wrap items-baseline gap-x-5 gap-y-2 text-sm">
            <A href={`/portfolios/${props.portfolio.id}`} class="link font-medium">
              The full case
            </A>
            <A href={`/lab?from=${props.portfolio.id}`} class="link">
              Open in the lab
            </A>
          </p>
        </div>

        <div class="lg:w-2/5">
          <ExposureBar
            segments={engines()}
            ariaLabel={`${props.portfolio.name}: capital weight by return engine. ${engines()
              .map((one) => `${one.label} ${one.percent}%`)
              .join(", ")}.`}
            caption={<>Capital weight by return engine. Holding-level weights are on the portfolio's own page.</>}
          />
          <Show when={props.portfolio.grossExposurePercent > 100}>
            <p class="mt-4 border-l-2 border-rule-strong pl-3 text-sm text-ink-muted">
              Capital weights do not describe this portfolio's risk. Its notional exposure is{" "}
              <span data-numeric>{props.portfolio.grossExposurePercent}%</span> of capital.
            </p>
          </Show>
        </div>
      </div>
    </article>
  );
}

export default function Portfolios(): JSX.Element {
  return (
    <>
      <Title>Portfolios — Portfolio Edge</Title>

      <PageHeader
        eyebrow="Portfolios"
        title="Four constructions, ordered by how much of each is a fact"
        standfirst={
          <>
            Not four risk levels. The first is the thing the others have to beat. The second changes no holding and is
            the only one whose edge is an accounting identity. The third takes the two tilts this evidence supports. The
            fourth is a reader's proposal, priced against the same shelf.
          </>
        }
        lastChecked={portfoliosAsOf}
      />

      <Prose class="mb-10">
        <p>
          Every weight below is exact and sums to 100%. Where a portfolio holds a capital-efficient fund, its notional
          exposure is shown separately, because a capital weight does not describe what that portfolio is exposed to.
        </p>
        <p>
          None of these is promoted. Nothing in the underlying research reached a status above <em>exploratory</em>, and
          no portfolio here is claimed to beat an index.
        </p>
      </Prose>

      <div>
        <For each={portfolios}>{(portfolio) => <Card portfolio={portfolio} />}</For>
      </div>
    </>
  );
}
