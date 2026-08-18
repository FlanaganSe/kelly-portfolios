import { Meta, Title } from "@solidjs/meta";
import { A } from "@solidjs/router";
import { createMemo, createSignal, For, type JSX, Show } from "solid-js";
import { DataTable } from "~/components/DataTable";
import { PageHeader } from "~/components/PageHeader";
import { Prose } from "~/components/Prose";
import { StatusChip } from "~/components/StatusChip";
import { findFund, type ShelfCategory, type ShelfFund, shelf, shelfAsOf } from "~/content/shelf";

/**
 * The shelf: every product this repository has priced or regressed, in one table.
 *
 * The columns are chosen to make one comparison easy and one comparison hard. Easy: fee
 * against net cost, because they rank differently and the difference is the finding.
 * Hard: alpha on its own — it is printed only beside its detection floor, since the
 * median alpha this instrument can see is roughly four times the true dispersion between
 * funds, and a number without that context reads as skill when it is noise.
 */

const CATEGORY_LABEL: Readonly<Record<ShelfCategory, string>> = {
  "us-core": "US core",
  "us-value": "US value",
  "us-small": "US small cap",
  "us-momentum": "US momentum",
  "us-quality": "US quality",
  "intl-core": "Developed ex-US core",
  "intl-value": "Developed ex-US value",
  "intl-small-value": "Developed ex-US small value",
  "intl-momentum": "Developed ex-US momentum",
  "emerging-core": "Emerging core",
  "emerging-value": "Emerging value",
  bonds: "Bonds",
  "managed-futures": "Managed futures",
  "capital-efficient": "Capital-efficient wrappers",
  alternative: "Alternatives",
};

const ORDER: readonly ShelfCategory[] = [
  "us-core",
  "us-value",
  "us-small",
  "us-momentum",
  "us-quality",
  "intl-core",
  "intl-value",
  "intl-small-value",
  "intl-momentum",
  "emerging-core",
  "emerging-value",
  "bonds",
  "managed-futures",
  "capital-efficient",
  "alternative",
];

function bp(value: number | null): JSX.Element {
  return value === null ? <span class="text-ink-faint">—</span> : value;
}

/** The deepest loading a fund carries, which is what it is bought for. */
function headlineLoading(fund: ShelfFund) {
  return [...fund.loadings].sort((a, b) => Math.abs(b.value) - Math.abs(a.value))[0];
}

const PANEL_LABEL = {
  us: "US",
  "developed-ex-us": "dev ex-US",
  emerging: "EM",
  "aqr-tsmom": "TSMOM",
} as const;

function columns() {
  return [
    {
      key: "ticker",
      header: "Fund",
      rowHeader: true,
      width: "16rem",
      cell: (row: ShelfFund) => (
        <span id={row.ticker}>
          <A href={`/funds/${row.ticker}`} data-numeric class="link font-mono text-sm">
            {row.ticker}
          </A>
          <span class="block text-xs text-ink-faint">{row.name}</span>
        </span>
      ),
    },
    { key: "fee", header: "Fee bp", numeric: true, width: "5rem", cell: (row: ShelfFund) => bp(row.expenseRatioBp) },
    {
      key: "net",
      header: "Net cost bp",
      numeric: true,
      width: "6.5rem",
      cell: (row: ShelfFund) => bp(row.netCostBp),
    },
    {
      key: "turnover",
      header: "Turnover",
      numeric: true,
      width: "6rem",
      cell: (row: ShelfFund) =>
        row.turnoverPercent === null ? <span class="text-ink-faint">—</span> : `${row.turnoverPercent}%`,
    },
    {
      key: "loading",
      header: "Exposure bought",
      width: "11rem",
      cell: (row: ShelfFund) => {
        const top = headlineLoading(row);
        if (top === undefined) {
          return <span class="text-ink-faint">Not regressed here</span>;
        }
        return (
          <span data-numeric>
            {top.factor} {top.value > 0 ? "+" : ""}
            {top.value.toFixed(3)}
            <span class="ml-1 text-xs text-ink-faint">{PANEL_LABEL[top.panel]}</span>
          </span>
        );
      },
    },
    {
      key: "alpha",
      header: "Alpha vs floor",
      numeric: true,
      width: "9rem",
      cell: (row: ShelfFund) =>
        row.alphaPpYr === null || row.alphaDetectionFloorPpYr === null ? (
          <span class="text-ink-faint">—</span>
        ) : (
          <span data-numeric>
            {row.alphaPpYr > 0 ? "+" : ""}
            {row.alphaPpYr.toFixed(2)} <span class="text-ink-faint">/ {row.alphaDetectionFloorPpYr.toFixed(2)}</span>
          </span>
        ),
    },
    {
      key: "status",
      header: "Status",
      width: "9rem",
      cell: (row: ShelfFund) => (
        <Show when={row.status} fallback={<span class="text-ink-faint">Control</span>}>
          {(status) => <StatusChip status={status()} />}
        </Show>
      ),
    },
  ];
}

export default function Funds(): JSX.Element {
  const [query, setQuery] = createSignal("");

  const groups = createMemo(() => {
    const needle = query().trim().toUpperCase();
    const matching = shelf.filter(
      (fund) => needle === "" || fund.ticker.includes(needle) || fund.name.toUpperCase().includes(needle)
    );
    return ORDER.map((category) => ({
      category,
      funds: matching.filter((fund) => fund.category === category),
    })).filter((group) => group.funds.length > 0);
  });

  return (
    <>
      <Title>Funds — Portfolio Edge</Title>
      <Meta
        name="description"
        content="Every fund audited here, with the factor exposure it actually delivers, its cost net of securities lending, and the status of the evidence behind it."
      />

      <PageHeader
        eyebrow="Funds"
        title="The shelf, priced and regressed"
        standfirst="Every product this repository has audited, with the exposure it actually delivers, what it costs to own after securities lending, and the status of the evidence behind it."
        lastChecked={shelfAsOf}
      />

      <Prose class="mb-8">
        <p>
          Two columns do most of the work. <strong>Net cost</strong> is the fee less securities-lending income, and it
          ranks funds differently from the fee alone. IEMG charges{" "}
          <span data-numeric>{findFund("IEMG")?.expenseRatioBp}</span> bp against VWO's{" "}
          <span data-numeric>{findFund("VWO")?.expenseRatioBp}</span>, and costs less to own:{" "}
          <span data-numeric>{findFund("IEMG")?.netCostBp}</span> bp against{" "}
          <span data-numeric>{findFund("VWO")?.netCostBp}</span>. BND is the dearest aggregate bond fund audited here
          because it is the only one that does not lend at all.
        </p>
        <p>
          <strong>Alpha vs floor</strong> prints a fund's raw alpha only beside the smallest alpha its own window could
          have detected. Where the second number is the larger one, which is nearly always, the first says nothing.
        </p>
        <p>
          A loading names its panel, because the panel changes the number. Read either emerging-market value fund on the
          US panel instead of its own and the sign flips, so a loading quoted without its panel is a different
          measurement wearing the same label.
        </p>
      </Prose>

      <div class="mb-8 flex flex-wrap items-end gap-4">
        <label class="flex flex-col gap-1.5 text-sm">
          <span class="eyebrow">Filter by ticker or name</span>
          <input
            type="search"
            class="control w-64"
            value={query()}
            onInput={(event) => setQuery(event.currentTarget.value)}
            placeholder="AVLV"
          />
        </label>
        <p data-numeric class="text-sm text-ink-muted">
          {groups().reduce((sum, group) => sum + group.funds.length, 0)} of {shelf.length} funds
        </p>
      </div>

      <Show
        when={groups().length > 0}
        fallback={
          <p class="border-l-2 border-rule-strong pl-4 text-base text-ink-muted">
            No audited fund matches that. The shelf holds what this repository has priced, which is not the whole
            market.
          </p>
        }
      >
        <For each={groups()}>
          {(group) => (
            <section class="mb-12">
              <h2 class="mb-3 font-serif text-xl">{CATEGORY_LABEL[group.category]}</h2>
              <DataTable
                caption={`${CATEGORY_LABEL[group.category]}: fee, net cost, delivered exposure and evidence status.`}
                captionHidden
                columns={columns()}
                rows={group.funds}
              />
            </section>
          )}
        </For>
      </Show>
    </>
  );
}
