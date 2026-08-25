// biome-ignore-all lint/a11y/noRedundantRoles: the roles on the table below are not redundant. `.stack-table` in src/styles.css sets `display: block` under 40rem to lay each row out as a card, and any `display` other than a `table-*` value drops the implicit table roles from the accessibility tree in every engine. Above the breakpoint the attributes restate what the elements already mean; below it they are the only thing relating a cell to its row. The lint rule reads the markup and cannot see the stylesheet.
// biome-ignore-all lint/a11y/useSemanticElements: the semantic elements are already in use — `table`, `thead`, `tr`, `th`, `td`. This rule fires on the same attributes as the one above, for the same reason, and has the same answer.
import { type Component, createMemo, createSignal, For, onMount, Show } from "solid-js";
import { NumberField, RangeField, SelectField } from "~/components/islands/controls";
import {
  defaultPlacementConfig,
  OWN_RATES,
  type PlacementConfig,
  parsePlacementConfig,
  toPlacementSearchParams,
} from "~/components/islands/placement-config";
import {
  type Basis,
  fill,
  forfeitedCreditBp,
  type PlacedRow,
  percentOfBp,
  queue,
  ratePercent,
  shelf,
  verdict,
} from "~/components/islands/placement-model";
import { placementAsOf, taxRegimes } from "~/content/placement";
import { derivedRates, type TaxRegime } from "~/lib/placement";

/**
 * Where each fund on the shelf belongs, computed at the reader's own rates.
 *
 * Nothing here is read out of the pre-ranked tables in `~/content/placement`. The whole
 * point of the finding is that the ranking moves with the bracket, so the page that
 * shows it has to run the arithmetic rather than print one bracket's answer.
 */

const BASIS_OPTIONS = [
  { value: "paid-out", label: "Only what the stacked fund has paid out" },
  { value: "recorded", label: "Everything the stacked fund has recorded" },
] as const;

const WHERE_TEXT: Readonly<Record<PlacedRow["where"], string>> = {
  shelter: "Sheltered",
  split: "Partly sheltered",
  taxable: "Taxable account",
};

/**
 * Written once, read twice: into `<thead>`, and into the label each cell shows when
 * the table becomes a list of cards below 40rem. Seven columns is the widest table
 * the site renders, and a phone cannot usefully scroll it.
 */
const COLUMNS = [
  "#",
  "Fund",
  "Weight",
  "Tax if taxable",
  "Credit lost if sheltered",
  "Saved per sheltered dollar",
  "Goes in",
] as const;

export const PlacementTool: Component = () => {
  const [config, setConfig] = createSignal<PlacementConfig>(defaultPlacementConfig);
  const update = (patch: Partial<PlacementConfig>) => setConfig((current) => ({ ...current, ...patch }));

  // A shared link wins over the opening state, and only on the client: the server has no
  // query string, so every reader's first paint is the same worked example.
  onMount(() => setConfig(parsePlacementConfig(window.location.search)));

  const named = () => taxRegimes.find((entry) => entry.id === config().bracketId);

  const regime = createMemo<TaxRegime>(() => {
    const chosen = named();
    if (chosen !== undefined) return chosen;
    return {
      label: "Your own rates",
      asOf: placementAsOf,
      ordinaryIncome: config().ownOrdinaryPercent / 100,
      longTermCapitalGain: config().ownQualifiedPercent / 100,
      netInvestmentIncome: 0,
    };
  });

  const rates = () => derivedRates(regime());
  const bracketNote = () =>
    `${ratePercent(rates().qualifiedDividend)}% on qualified dividends and ${ratePercent(rates().ordinary)}% on ordinary income`;

  const shelterPercent = () => config().rothPercent + config().deferredPercent;
  const taxablePercent = () => Math.max(0, 100 - shelterPercent());

  const setRoth = (value: number) =>
    update({ rothPercent: value, deferredPercent: Math.min(config().deferredPercent, 100 - value) });
  const setDeferred = (value: number) => update({ deferredPercent: Math.min(value, 100 - config().rothPercent) });

  const rows = createMemo(() => queue(shelf(config().basis), regime()));
  const placed = createMemo(() => fill(rows(), shelterPercent() / 100));
  const call = createMemo(() => verdict(rows()));
  const forfeited = createMemo(() => forfeitedCreditBp(placed()));
  const creditIsWorthless = () => rates().qualifiedDividend <= 0;

  const headline = createMemo(() => {
    const found = call();
    if (creditIsWorthless()) {
      return "At a 0% rate on dividends there is no credit to lose and almost no tax to save, so the ranking has nothing to say about the foreign funds. Section 904 caps the credit at the US tax on foreign income, and there is none.";
    }
    const low = found.lowestInternational;
    const high = found.highestDomestic;
    const last = found.last;
    if (found.everyInternationalAhead && low !== null && high !== null && last !== null) {
      return `Every fund with foreign tax withheld outranks every fund without it. The weakest of them, ${low.ticker}, saves ${percentOfBp(low.priorityBp)} a year per sheltered dollar against the strongest US line, ${high.ticker}, at ${percentOfBp(high.priorityBp)}. ${last.ticker} comes last at ${percentOfBp(last.priorityBp)}.`;
    }
    if (low !== null && high !== null && last !== null) {
      return `${high.ticker} breaks the pattern: it saves ${percentOfBp(high.priorityBp)} a year per sheltered dollar against ${percentOfBp(low.priorityBp)} for ${low.ticker}, the weakest foreign line. ${last.ticker} still comes last at ${percentOfBp(last.priorityBp)}.`;
    }
    return "There is nothing on the fund list to rank.";
  });

  const [shareHref, setShareHref] = createSignal("");
  const syncAddressBar = () => {
    const query = toPlacementSearchParams(config()).toString();
    const href = `${window.location.pathname}${query === "" ? "" : `?${query}`}`;
    window.history.replaceState(null, "", href);
    setShareHref(`${window.location.origin}${href}`);
  };

  const bracketOptions = [
    ...taxRegimes.map((entry) => ({
      value: entry.id,
      label: `${ratePercent(derivedRates(entry).qualifiedDividend)}% on dividends, ${ratePercent(derivedRates(entry).ordinary)}% on ordinary income`,
    })),
    { value: OWN_RATES, label: "My own rates" },
  ];

  return (
    <div class="not-prose">
      <div class="grid gap-6 rounded-[3px] border border-rule bg-raised p-5 sm:grid-cols-2">
        <SelectField
          class="sm:col-span-2"
          label="Your marginal tax rates"
          value={config().bracketId}
          options={bracketOptions}
          onChange={(value) => update({ bracketId: value })}
          hint="US federal, with the 3.8% surtax on investment income already inside both figures where it applies. State tax is left out and adds to every line."
        />

        <Show when={named() === undefined}>
          <NumberField
            label="Your rate on ordinary income, all in"
            value={config().ownOrdinaryPercent}
            onInput={(value) => update({ ownOrdinaryPercent: value })}
            min={0}
            max={99.9}
            step={0.1}
            unit="%"
          />
          <NumberField
            label="Your rate on qualified dividends, all in"
            value={config().ownQualifiedPercent}
            onInput={(value) => update({ ownQualifiedPercent: value })}
            min={0}
            max={99.9}
            step={0.1}
            unit="%"
            hint="Add the 3.8% surtax to both figures if you pay it."
          />
        </Show>

        <RangeField
          label="Share of your money in a Roth"
          value={config().rothPercent}
          onInput={setRoth}
          min={0}
          max={100}
          step={1}
          unit="%"
          showBounds
        />

        <RangeField
          label="Share in a traditional 401(k) or IRA"
          value={config().deferredPercent}
          onInput={setDeferred}
          min={0}
          max={100}
          step={1}
          unit="%"
          showBounds
          hint="The two shelters behave identically here. Foreign tax is lost inside both."
        />

        <SelectField
          class="sm:col-span-2"
          label="How to read the stacked fund"
          value={config().basis}
          options={[...BASIS_OPTIONS]}
          onChange={(value) => update({ basis: value as Basis })}
          hint="It books income inside itself that it has not distributed. Counting that puts it first in the queue; counting only what shareholders were taxed on puts it seventh. Its account does not change either way."
        />
      </div>

      <p data-numeric class="mt-4 text-sm text-ink-muted">
        That leaves {taxablePercent()}% of your money in a taxable brokerage account, and {shelterPercent()}% of it
        sheltered.
      </p>

      {/* The ranking, the placement and the verdict all move together, so a screen
          reader hears them as one update. */}
      <div aria-live="polite">
        <p class="mt-8 max-w-measure text-lg text-ink">{headline()}</p>

        <div
          class="scroller mt-6"
          tabindex="0"
          role="region"
          aria-label="The shelf, ranked by what a sheltered dollar saves"
        >
          <table role="table" class="stack-table w-full border-collapse text-base sm:min-w-[42rem]">
            <caption class="sr-only">
              What a sheltered dollar of each fund saves a year, at {bracketNote()}, and where the fund lands once your
              shelter runs out
            </caption>
            <thead role="rowgroup">
              <tr role="row" class="border-b border-rule-strong text-left">
                <For each={COLUMNS}>
                  {(heading, i) => (
                    <th
                      role="columnheader"
                      scope="col"
                      classList={{
                        eyebrow: true,
                        "py-2": true,
                        "pr-3": i() === 0,
                        "pr-4": i() > 0,
                        "text-right": i() === 0 || (i() >= 2 && i() <= 5),
                      }}
                    >
                      {heading}
                    </th>
                  )}
                </For>
              </tr>
            </thead>
            <tbody role="rowgroup" class="text-ink-muted">
              <For each={placed()}>
                {(row, index) => (
                  <tr role="row" class="border-b border-rule last:border-0">
                    <td role="cell" data-label={COLUMNS[0]} data-numeric class="py-2 pr-3 text-right text-ink-faint">
                      {index() + 1}
                    </td>
                    <th role="rowheader" scope="row" class="py-2 pr-4 text-left font-normal text-ink">
                      {row.ticker}
                      <span class="block text-xs font-normal text-ink-faint">{row.name}</span>
                    </th>
                    <td role="cell" data-label={COLUMNS[2]} data-numeric class="py-2 pr-4 text-right">
                      {ratePercent(row.weight, 1)}%
                    </td>
                    <td role="cell" data-label={COLUMNS[3]} data-numeric class="py-2 pr-4 text-right">
                      {percentOfBp(row.taxableBp)}
                    </td>
                    <td role="cell" data-label={COLUMNS[4]} data-numeric class="py-2 pr-4 text-right">
                      {percentOfBp(row.shelteredBp)}
                    </td>
                    <td
                      role="cell"
                      data-label={COLUMNS[5]}
                      data-numeric
                      class="py-2 pr-4 text-right font-semibold text-ink"
                    >
                      {percentOfBp(row.priorityBp)}
                    </td>
                    <td role="cell" data-label={COLUMNS[6]} class="py-2 pr-4">
                      {WHERE_TEXT[row.where]}
                      <Show when={row.where === "split"}>
                        <span data-numeric class="block text-xs text-ink-faint">
                          {ratePercent(row.shelteredWeight, 1)}% of the portfolio fits
                        </span>
                      </Show>
                    </td>
                  </tr>
                )}
              </For>
            </tbody>
          </table>
        </div>

        <p data-numeric class="mt-4 max-w-measure text-sm text-ink-muted">
          Computed at {bracketNote()}, on yields and withheld rates as of {placementAsOf}. Sheltering the foreign funds
          destroys {percentOfBp(forfeited())} a year of foreign tax credit, permanently and in a Roth and a traditional
          account alike. The last column has already subtracted it.
        </p>
      </div>

      <div class="mt-8 flex flex-wrap items-baseline gap-3">
        <button
          type="button"
          class="inline-flex h-9 items-center rounded-[3px] border border-rule px-3 text-sm text-ink-muted transition-colors hover:border-rule-strong hover:text-ink"
          onClick={syncAddressBar}
        >
          Put this setup in the address bar
        </button>
        <Show when={shareHref() !== ""}>
          <span data-numeric class="max-w-full truncate text-xs text-ink-faint">
            {shareHref()}
          </span>
        </Show>
      </div>
    </div>
  );
};

export default PlacementTool;
