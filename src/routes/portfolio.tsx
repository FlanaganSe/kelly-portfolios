import { Title } from "@solidjs/meta";
import { For, Show } from "solid-js";
import { Callout } from "~/components/Callout";
import { DataTable } from "~/components/DataTable";
import { Figure } from "~/components/Figure";
import { PageHeader } from "~/components/PageHeader";
import { Prose } from "~/components/Prose";
import { SourceLink } from "~/components/SourceLink";
import { CertaintyChip, StatusChip } from "~/components/StatusChip";
import { openQuestions } from "~/content/openQuestions";
import {
  constructionSummary,
  drawdownAnchor,
  equityBondSplit,
  equitySleeveWeights,
  type Fund,
  feePolicy,
  funds,
  optionalSleeves,
  riskVariants,
  vxusTradeoff,
  whatThisIsNot,
} from "~/content/portfolio";
import { type Sleeve, sleeves } from "~/content/sleeves";

/**
 * The construction: what to hold, what each line buys, at what confidence, and —
 * at length, because it is the most useful part — what is deliberately absent.
 */

// Shared spacing for the tables on this page. The chip-overflow workaround that used to
// live here is gone; StatusChip fixes it at source now.
const TABLE = "mt-8";

const H2 = "font-sans text-xl font-semibold tracking-[-0.015em] text-ink";
const H3 = "font-sans text-base font-semibold text-ink";

const coreFunds = funds.filter((fund) => fund.role === "core");
const vxus = funds.find((fund) => fund.id === "vxus");
const heldFunds = funds.filter((fund) => fund.role === "core" || fund.role === "core-alternative");
const excluded = sleeves.filter((sleeve) => sleeve.verdict === "excluded");
const untested = sleeves.filter((sleeve) => sleeve.verdict === "untested");
const constructionQuestions = openQuestions.filter((question) => question.group === "changes-the-construction");

const shareOfEquity = (sleeveName: string): string => {
  const weight = equitySleeveWeights.weights.find((entry) => entry.sleeve === sleeveName);
  return weight ? `${weight.percentOfEquity}%` : "—";
};

const feeCell = (bp: number | null): string => (bp === null ? "Not read here" : `${bp} bp`);

/**
 * A few figures are held as numbers rather than as the string their page printed.
 * Print them with the typographic minus the rest of the site uses. Nothing is
 * rounded and no precision is dropped.
 */
const num = (value: number): string => String(value).replace("-", "−");

/** `null` means the row's share is set by something other than the horizon; variant D. */
const range = (bounds: readonly [number, number] | null): string =>
  bounds === null ? "set by the withdrawal rate" : `${bounds[0]}–${bounds[1]}%`;

function FundNotes(props: { readonly fund: Fund }) {
  return (
    <div class="max-w-measure border-t border-rule pt-4">
      <p class={H3}>
        {props.fund.ticker} — {props.fund.name}
      </p>
      <p class="mt-2 text-ink-muted">{props.fund.whatItBuys}</p>
      <div class="mt-3 flex flex-wrap items-baseline gap-x-4 gap-y-2">
        <CertaintyChip certainty={props.fund.certaintyClass} />
        <Show when={props.fund.status}>{(status) => <StatusChip status={status()} />}</Show>
      </div>
      <Show when={props.fund.expenseRatioNote}>
        {(note) => <p class="mt-3 text-sm text-ink-muted">Expense ratio: {note()}</p>}
      </Show>
      <Show when={props.fund.alternates.length > 0}>
        <ul class="mt-3 flex flex-col gap-1 text-sm text-ink-muted">
          <For each={props.fund.alternates}>
            {(alternate) => (
              <li>
                <span class="font-medium text-ink">
                  {alternate.ticker} {alternate.name}
                </span>
                <Show when={alternate.expenseRatioBp !== null}>
                  <span data-numeric> — {feeCell(alternate.expenseRatioBp)}</span>
                </Show>
                <Show when={alternate.note}>{(note) => <span> {note()}</span>}</Show>
              </li>
            )}
          </For>
        </ul>
      </Show>
      <p class="mt-3">
        <SourceLink citation={props.fund.source} prefix />
      </p>
    </div>
  );
}

function ExcludedSleeve(props: { readonly sleeve: Sleeve }) {
  return (
    <article class="max-w-measure border-t border-rule pt-5">
      <h3 class={H3}>
        {props.sleeve.label}
        <Show when={props.sleeve.ticker}>{(ticker) => <span class="text-ink-faint"> · {ticker()}</span>}</Show>
      </h3>

      <div class="mt-2 flex flex-wrap items-baseline gap-x-4 gap-y-2">
        <Show when={props.sleeve.status}>{(status) => <StatusChip status={status()} />}</Show>
        <Show when={props.sleeve.feeBp !== null}>
          <span data-numeric class="text-sm text-ink-muted">
            {feeCell(props.sleeve.feeBp)}
            <Show when={props.sleeve.feeAsOf}>{(date) => <span class="text-ink-faint"> as of {date()}</span>}</Show>
          </span>
        </Show>
      </div>

      <Show when={props.sleeve.statusNote}>{(note) => <p class="mt-3 text-sm text-ink-muted">{note()}</p>}</Show>

      <p class="mt-3 text-ink">{props.sleeve.reason}</p>

      <Show when={props.sleeve.loading}>
        {(loading) => (
          <Figure
            class="mt-4"
            size="sm"
            label={`${loading().factor} loading`}
            value={num(loading().value)}
            interval={loading().interval}
            note={loading().note}
          />
        )}
      </Show>

      <Show when={props.sleeve.caveat}>
        {(caveat) => (
          <Callout variant="caveat" label="Read it this way">
            <p>{caveat()}</p>
          </Callout>
        )}
      </Show>

      <p class="mt-3">
        <SourceLink citation={props.sleeve.source} prefix />
      </p>
    </article>
  );
}

export default function Portfolio() {
  return (
    <>
      <Title>The portfolio — Portfolio Edge</Title>
      <PageHeader
        title="The portfolio"
        standfirst="What to hold, what each line buys, and how confident anyone is entitled to be about it."
        lastChecked={constructionSummary.asOf}
      />

      <Prose as="section">
        <p>{constructionSummary.headline}</p>
        <p>{constructionSummary.detail}</p>
        <p>{constructionSummary.disciplinesAreWorthMore}</p>
      </Prose>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="split" class="mt-14">
        <h2 id="split" class={H2}>
          The split the evidence cannot set
        </h2>

        <p class="mt-3 max-w-measure font-serif text-xl text-ink">{equityBondSplit.headline}</p>
        <p class="mt-4 max-w-measure text-ink-muted">{equityBondSplit.detail}</p>

        <div class="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <Figure
            label="Maximum drawdown"
            value={num(drawdownAnchor.maxDrawdownPercent)}
            unit="%"
            size="lg"
            tone="negative"
            note={`${drawdownAnchor.asset}, ${drawdownAnchor.window}.`}
          />
          <Figure
            label="Months under water"
            value={num(drawdownAnchor.monthsUnderWater)}
            size="lg"
            note="Below the previous peak, before it was made back."
          />
          <Figure
            label="Geometric return"
            value={num(drawdownAnchor.geometricReturnPercent)}
            unit="%/yr"
            size="lg"
            note="What the same asset compounded over the same window."
          />
          <Figure
            label="Volatility"
            value={num(drawdownAnchor.volatilityPercent)}
            unit="%/yr"
            size="lg"
            note="Annualised."
            source={drawdownAnchor.source}
            asOf={drawdownAnchor.asOf}
          />
        </div>

        <p class="mt-8 max-w-measure font-serif text-xl text-ink">{equityBondSplit.anchor}</p>

        <Callout variant="mechanism" label="Why a shorter horizon holds less equity">
          <p>{equityBondSplit.sequenceRisk}</p>
        </Callout>

        <DataTable
          class={`mt-8 ${TABLE}`}
          caption="Three risk variants. Only the equity share differs; the equity composition is identical in all three."
          columns={[
            {
              key: "variant",
              header: "Variant",
              rowHeader: true,
              cell: (row) => `${row.id} — ${row.label}`,
            },
            { key: "equity", header: "Equity", numeric: true, cell: (row) => range(row.equityPercent) },
            { key: "bonds", header: "Bonds", numeric: true, cell: (row) => range(row.bondPercent) },
            {
              key: "when",
              header: "Applies when",
              cell: (row) => (
                <>
                  {row.appliesWhen}
                  <Show when={row.note}>
                    {(note) => <span class="mt-1 block text-ink-muted text-sm">{note()}</span>}
                  </Show>
                </>
              ),
            },
          ]}
          rows={riskVariants}
          footnote={<SourceLink citation={equityBondSplit.source} prefix />}
        />
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="weights" class="mt-14">
        <h2 id="weights" class={H2}>
          How the equity is split
        </h2>
        <p class="mt-2 max-w-measure text-ink-muted">
          These are declared research weights, frozen before anyone looked at a result. They are not a measured optimum
          and they are not a market weight — no global market-capitalisation series exists in this repository, so no
          page here can tell you what the market weight is.
        </p>

        <DataTable
          class={`mt-6 ${TABLE}`}
          caption="Equity sleeve weights, as a share of the equity portion"
          columns={[
            { key: "sleeve", header: "Sleeve", rowHeader: true, cell: (row) => row.sleeve },
            { key: "share", header: "Share of equity", numeric: true, cell: (row) => `${row.percentOfEquity}%` },
          ]}
          rows={equitySleeveWeights.weights}
          footnote={
            <>
              {equitySleeveWeights.provenance} <SourceLink citation={equitySleeveWeights.source} prefix />
            </>
          }
        />

        <Callout variant="caveat" label="A nearby split is indistinguishable">
          <p>{equitySleeveWeights.caveat}</p>
        </Callout>
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="holdings" class="mt-14">
        <h2 id="holdings" class={H2}>
          The holdings
        </h2>
        <p class="mt-2 max-w-measure text-ink-muted">
          Four lines. The bond share is set by the variant above, not by the equity weights, so it carries no share of
          equity.
        </p>

        <DataTable
          class={`mt-6 ${TABLE}`}
          caption="Core holdings, their alternates, cost and share of equity"
          columns={[
            { key: "sleeve", header: "Sleeve", rowHeader: true, cell: (row) => row.sleeve },
            {
              key: "fund",
              header: "Fund",
              cell: (row) => (
                <>
                  <span class="font-medium">{row.ticker}</span>
                  <span class="block text-ink-muted">{row.name}</span>
                </>
              ),
            },
            {
              key: "alternates",
              header: "Alternates",
              cell: (row) =>
                row.alternates.length === 0 ? "—" : row.alternates.map((alternate) => alternate.ticker).join(", "),
            },
            {
              key: "fee",
              header: "Expense ratio",
              numeric: true,
              cell: (row) => (
                <span class="whitespace-nowrap">
                  {feeCell(row.expenseRatioBp)}
                  <Show when={row.expenseRatioAsOf}>
                    {(date) => <span class="block text-xs text-ink-faint">as of {date()}</span>}
                  </Show>
                </span>
              ),
            },
            {
              key: "share",
              header: "Share of equity",
              numeric: true,
              cell: (row) => shareOfEquity(row.sleeve),
            },
            {
              key: "class",
              header: "What it buys",
              cell: (row) => <CertaintyChip certainty={row.certaintyClass} />,
            },
          ]}
          rows={coreFunds}
          footnote='"Not read here" means no experiment in this repository priced that fund. It is not a rounding to zero, and it is not an omission of convenience.'
        />

        <h3 class="mt-10 mb-4 font-sans text-base font-semibold text-ink">What each line buys</h3>
        <div class="flex flex-col gap-6">
          <For each={heldFunds}>{(fund) => <FundNotes fund={fund} />}</For>
        </div>

        <Callout variant="caveat" label="On the fees this repository does not have">
          <p>{feePolicy.headline}</p>
          <p>{feePolicy.detail}</p>
          <p>
            {feePolicy.instruction} <SourceLink citation={feePolicy.source} prefix />
          </p>
        </Callout>
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="vxus" class="mt-14">
        <h2 id="vxus" class={H2}>
          One fund for international, or two
        </h2>
        <p class="mt-3 max-w-measure font-serif text-xl text-ink">{vxusTradeoff.headline}</p>
        <p class="mt-4 max-w-measure text-ink-muted">{vxusTradeoff.why}</p>
        <Show when={vxus}>
          {(fund) => (
            <p class="mt-4 max-w-measure text-ink-muted">
              {fund().ticker} is {fund().name}. {vxusTradeoff.vxusFacts}
            </p>
          )}
        </Show>
        <p class="mt-4 flex flex-wrap items-baseline gap-x-4 gap-y-2">
          <span data-numeric class="text-xs text-ink-faint">
            as of {vxusTradeoff.asOf}
          </span>
          <SourceLink citation={vxusTradeoff.source} prefix />
        </p>
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="optional" class="mt-14">
        <h2 id="optional" class={H2}>
          Two optional sleeves
        </h2>
        <p class="mt-2 max-w-measure text-ink-muted">
          Both are optional in the strict sense: the portfolio above is complete without either, and neither has a
          status that would let it be recommended. Zero is a defensible weight for both.
        </p>

        <DataTable
          class={`mt-6 ${TABLE}`}
          caption="The two optional sleeves, their size, the account they need and their status"
          columns={[
            {
              key: "sleeve",
              header: "Sleeve",
              rowHeader: true,
              cell: (row) => (
                <>
                  <span>{row.label}</span>
                  <span class="block text-ink-muted">{row.ticker}</span>
                </>
              ),
            },
            { key: "size", header: "Size", cell: (row) => row.size },
            { key: "account", header: "Account", cell: (row) => row.requiredAccount },
            {
              key: "fee",
              header: "Expense ratio",
              numeric: true,
              cell: (row) => (
                <span class="whitespace-nowrap">
                  {row.expenseRatioBp} bp
                  <span class="block text-xs text-ink-faint">as of {row.expenseRatioAsOf}</span>
                </span>
              ),
            },
            {
              key: "product",
              header: "Product status",
              cell: (row) => <StatusChip status={row.productStatus} />,
            },
            {
              key: "underlying",
              header: "Underlying status",
              cell: (row) => <StatusChip status={row.underlyingStatus} />,
            },
          ]}
          rows={optionalSleeves}
          footnote="Two statuses because a product and the thing it is supposed to deliver are graded separately. Neither column is a recommendation."
        />

        <div class="mt-8 flex flex-col gap-8">
          <For each={optionalSleeves}>
            {(sleeve) => (
              <div class="max-w-measure border-t border-rule pt-5">
                <h3 class={H3}>
                  {sleeve.label} · {sleeve.ticker}
                </h3>
                <p class="mt-2 text-ink">{sleeve.verdict}</p>
                <p class="mt-3 text-ink-muted">{sleeve.sizingNote}</p>
                <p class="mt-3 text-ink-muted">
                  Account: {sleeve.requiredAccount}. Size: {sleeve.size}.
                </p>
                <div class="mt-3">
                  <StatusChip status={sleeve.productStatus} showGloss />
                </div>
                <p class="mt-3">
                  <SourceLink citation={sleeve.source} prefix />
                </p>
              </div>
            )}
          </For>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="absent" class="mt-16">
        <h2 id="absent" class={H2}>
          What is deliberately absent
        </h2>
        <p class="mt-3 max-w-measure font-serif text-xl text-ink">
          This is the part of the page worth reading twice. Everything below was tested and lost, or priced and refused,
          or never run at all — and the reasons are not interchangeable.
        </p>

        <DataTable
          class={`mt-8 ${TABLE}`}
          caption="Candidates that were tested and are not held"
          columns={[
            { key: "label", header: "Candidate", rowHeader: true, cell: (row) => row.label },
            { key: "ticker", header: "Ticker", cell: (row) => row.ticker ?? "—" },
            {
              key: "status",
              header: "Status",
              cell: (row) => (
                <Show when={row.status} fallback={<span class="text-ink-faint">Not graded</span>}>
                  {(status) => <StatusChip status={status()} />}
                </Show>
              ),
            },
            {
              key: "loading",
              header: "Loading",
              numeric: true,
              cell: (row) => (row.loading ? `${row.loading.value} ${row.loading.interval}` : "—"),
            },
            { key: "fee", header: "Expense ratio", numeric: true, cell: (row) => feeCell(row.feeBp) },
          ]}
          rows={excluded}
          footnote="A loading measures manufacturing, not return: a fund can deliver its exposure perfectly and still be a poor thing to own."
        />

        <div class="mt-10 flex flex-col gap-8">
          <For each={excluded}>{(sleeve) => <ExcludedSleeve sleeve={sleeve} />}</For>
        </div>

        <h3 class="mt-12 mb-3 font-sans text-base font-semibold text-ink">Never tested here</h3>
        <p class="max-w-measure text-ink-muted">
          No experiment in this repository has run on any of these. That is a gap in the record, not a verdict on the
          asset.
        </p>
        <div class="mt-6 flex flex-col gap-5">
          <For each={untested}>
            {(sleeve) => (
              <div class="max-w-measure border-t border-rule pt-4">
                <p class={H3}>{sleeve.label}</p>
                <p class="mt-2 text-ink-muted">{sleeve.reason}</p>
                <p class="mt-2">
                  <SourceLink citation={sleeve.source} prefix />
                </p>
              </div>
            )}
          </For>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="not" class="mt-16">
        <h2 id="not" class={H2}>
          What this is not
        </h2>
        <dl class="mt-6 flex max-w-measure flex-col gap-5">
          <For each={whatThisIsNot}>
            {(item) => (
              <div class="border-t border-rule pt-4">
                <dt class={H3}>{item.claim}</dt>
                <dd class="mt-2 text-ink-muted">{item.detail}</dd>
              </div>
            )}
          </For>
        </dl>
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="changes" class="mt-16">
        <h2 id="changes" class={H2}>
          What would change this
        </h2>
        <p class="mt-2 max-w-measure text-ink-muted">
          Each of these has a stated trigger. None is a hope that more data turns up.
        </p>
        <div class="mt-6 max-w-measure">
          <For each={constructionQuestions}>
            {(question) => (
              <details class="border-b border-rule py-1">
                <summary class="cursor-pointer list-none py-3 font-medium text-ink marker:content-none">
                  {question.question}
                </summary>
                <div class="pb-4">
                  <p class="text-ink-muted">{question.whyItIsOpen}</p>
                  <p class="eyebrow mt-4">What would settle it</p>
                  <p class="mt-1 text-ink">{question.whatWouldSettleIt}</p>
                  <p class="mt-3">
                    <SourceLink citation={question.source} prefix />
                  </p>
                </div>
              </details>
            )}
          </For>
        </div>
      </section>
    </>
  );
}
