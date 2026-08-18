import { Title } from "@solidjs/meta";
import { A, useParams } from "@solidjs/router";
import { For, type JSX, Show } from "solid-js";
import { Callout } from "~/components/Callout";
import { DataTable } from "~/components/DataTable";
import { Figure } from "~/components/Figure";
import { PageHeader } from "~/components/PageHeader";
import { Prose } from "~/components/Prose";
import { SourceLink } from "~/components/SourceLink";
import { StatusChip } from "~/components/StatusChip";
import { families } from "~/content/families";
import { portfolios } from "~/content/portfolios";
import { type FactorLoading, findFund } from "~/content/shelf";
import NotFound from "~/routes/not-found";

/**
 * One fund.
 *
 * The page is built around what is measured and what is not, in that order, because for
 * most of this shelf the second list is the longer one and hiding it is how a product
 * page becomes marketing.
 */

const PANEL_LABEL = {
  us: "US",
  "developed-ex-us": "developed ex-US",
  emerging: "emerging",
  "aqr-tsmom": "AQR time-series momentum",
} as const;

const EXPOSURE_LABEL = {
  "us-equity": "US equity",
  "global-equity": "Global equity",
  equity: "Equity",
  "treasury-futures": "Treasury futures",
  "gold-futures": "Gold futures",
  trend: "Managed futures",
} as const;

function loadingColumns() {
  return [
    { key: "factor", header: "Factor", rowHeader: true, cell: (row: FactorLoading) => row.factor },
    {
      key: "value",
      header: "Loading",
      numeric: true,
      cell: (row: FactorLoading) => `${row.value > 0 ? "+" : ""}${row.value.toFixed(3)}`,
    },
    {
      key: "interval",
      header: "95% interval",
      numeric: true,
      cell: (row: FactorLoading) => row.interval ?? "—",
    },
    { key: "panel", header: "Panel", cell: (row: FactorLoading) => PANEL_LABEL[row.panel] },
    {
      key: "months",
      header: "Months",
      numeric: true,
      cell: (row: FactorLoading) => (row.months === null ? "—" : String(row.months)),
    },
  ];
}

export default function FundDetail(): JSX.Element {
  const params = useParams<{ ticker: string }>();
  const fund = () => findFund(params.ticker.toUpperCase());

  return (
    <Show when={fund()} fallback={<NotFound />}>
      {(found) => {
        const heldBy = () => portfolios.filter((one) => one.holdings.some((h) => h.ticker === found().ticker));
        const studiedIn = () => families.filter((one) => one.tickers.includes(found().ticker));

        return (
          <>
            <Title>{found().ticker} — Portfolio Edge</Title>

            <nav aria-label="Breadcrumb" class="mb-6 text-sm">
              <A href="/funds" class="link">
                Funds
              </A>
              <span class="px-2 text-ink-faint">/</span>
              <span data-numeric class="font-mono text-ink-muted">
                {found().ticker}
              </span>
            </nav>

            <PageHeader
              eyebrow={found().ticker}
              title={found().name}
              standfirst={found().mandate}
              lastChecked={found().asOf}
            />

            <div class="flex flex-wrap items-start gap-x-12 gap-y-8 border-y border-rule py-6">
              <Figure
                label="Expense ratio"
                value={found().expenseRatioBp === null ? "—" : String(found().expenseRatioBp)}
                unit="bp/yr"
              />
              <Figure
                label="Net cost after lending"
                value={found().netCostBp === null ? "—" : String(found().netCostBp)}
                unit="bp/yr"
              />
              <Figure
                label="Turnover"
                value={found().turnoverPercent === null ? "—" : String(found().turnoverPercent)}
                unit="%/yr"
              />
              <Show when={found().status}>
                {(status) => (
                  <div>
                    <p class="eyebrow mb-1.5">Evidence</p>
                    <StatusChip status={status()} showGloss />
                  </div>
                )}
              </Show>
            </div>

            <section class="mt-10" aria-labelledby="verdict">
              <h2 id="verdict" class="font-serif text-2xl tracking-[-0.01em]">
                What is established
              </h2>
              <Prose class="mt-3">
                <p>{found().verdict}</p>
              </Prose>
            </section>

            <Show when={found().caution}>
              {(caution) => (
                <Callout variant="caveat" label="What is not" class="mt-8">
                  <p>{caution()}</p>
                </Callout>
              )}
            </Show>

            <Show when={found().loadings.length > 0}>
              <section class="mt-12 border-t border-rule pt-8" aria-labelledby="loadings">
                <h2 id="loadings" class="mb-4 font-serif text-2xl tracking-[-0.01em]">
                  The exposure it delivers
                </h2>
                <DataTable
                  caption={`${found().ticker}: factor loadings, each with the panel it was measured on.`}
                  captionHidden
                  columns={loadingColumns()}
                  rows={found().loadings}
                  footnote={
                    <>
                      Every loading names its panel. The same fund can read a different sign on a different panel, and
                      the US panel would put sixteen of twenty-five ex-US funds below the bar rather than five.
                    </>
                  }
                />

                <Show when={found().alphaPpYr !== null}>
                  <div class="mt-8 flex flex-wrap gap-x-12 gap-y-6">
                    <Figure
                      label="Raw alpha"
                      value={`${(found().alphaPpYr ?? 0) > 0 ? "+" : ""}${found().alphaPpYr}`}
                      unit="pp/yr"
                    />
                    <Figure
                      label="Smallest alpha detectable"
                      value={found().alphaDetectionFloorPpYr === null ? "—" : String(found().alphaDetectionFloorPpYr)}
                      unit="pp/yr"
                    />
                    <Figure
                      label="Panel pedestal"
                      value={found().pedestalPpYr === null ? "—" : String(found().pedestalPpYr)}
                      unit="pp/yr"
                      note="The model's own misfit before any fund is examined."
                    />
                  </div>
                </Show>
              </section>
            </Show>

            <Show when={found().wrapper}>
              {(wrapper) => (
                <section class="mt-12 border-t border-rule pt-8" aria-labelledby="wrapper">
                  <h2 id="wrapper" class="mb-2 font-serif text-2xl tracking-[-0.01em]">
                    The wrapper arithmetic
                  </h2>
                  <p class="mb-6 max-w-measure text-base text-ink-muted">
                    A wrapper may not be scored from its gross notional. The deciding quantity is{" "}
                    <code class="font-mono text-sm">delta = (1 − b) / d</code>, the base sold per unit of diversifier
                    notional obtained. One minus that is the share of the +2.44 pp/yr funding-rule gap the wrapper
                    keeps.
                  </p>
                  <div class="flex flex-wrap gap-x-12 gap-y-6">
                    <Figure label="delta" value={wrapper().delta === null ? "—" : String(wrapper().delta)} />
                    <Figure
                      label="Funding-rule gap retained"
                      value={wrapper().fundingCapturePercent === null ? "—" : `${wrapper().fundingCapturePercent}%`}
                    />
                    <Figure
                      label="All-in cost"
                      value={wrapper().allInCostBp === null ? "—" : String(wrapper().allInCostBp)}
                      unit="bp/yr"
                    />
                    <Figure
                      label="Distribution tax drag"
                      value={
                        wrapper().distributionTaxDragPpYr === null ? "—" : String(wrapper().distributionTaxDragPpYr)
                      }
                      unit="pp/yr"
                    />
                    <Figure
                      label="Incremental drag"
                      value={wrapper().incrementalTaxDragBp === null ? "—" : String(wrapper().incrementalTaxDragBp)}
                      unit="bp/yr"
                      note="Against the fund it displaces. A drag quoted alone is not quotable."
                    />
                  </div>

                  <Show when={found().notionalExposure}>
                    {(exposures) => (
                      <ul class="mt-8 max-w-measure space-y-2 border-l-2 border-rule-strong pl-4 text-base">
                        <For each={exposures()}>
                          {(exposure) => (
                            <li>
                              <span class="font-medium">{EXPOSURE_LABEL[exposure.kind]}</span>{" "}
                              <span data-numeric class="text-ink-muted">
                                {(exposure.perDollarOfCapital * 100).toFixed(1)}% of capital, as notional
                              </span>
                            </li>
                          )}
                        </For>
                      </ul>
                    )}
                  </Show>
                </section>
              )}
            </Show>

            <section class="mt-12 border-t border-rule pt-8" aria-labelledby="where">
              <h2 id="where" class="mb-4 font-serif text-2xl tracking-[-0.01em]">
                Where it appears
              </h2>
              <ul class="max-w-measure space-y-3">
                <For each={heldBy()}>
                  {(portfolio) => (
                    <li>
                      <A href={`/portfolios/${portfolio.id}`} class="link">
                        {portfolio.name}
                      </A>
                      <span class="text-ink-muted">
                        {" "}
                        — {portfolio.holdings.find((one) => one.ticker === found().ticker)?.percent}% of capital
                      </span>
                    </li>
                  )}
                </For>
                <For each={studiedIn()}>
                  {(family) => (
                    <li>
                      <A href={`/research/${family.slug}`} class="link">
                        {family.name}
                      </A>
                      <span class="text-ink-muted"> — the research this fund is audited under</span>
                    </li>
                  )}
                </For>
              </ul>

              <p class="mt-6">
                <SourceLink citation={found().source} prefix />
              </p>
            </section>
          </>
        );
      }}
    </Show>
  );
}
