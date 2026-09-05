// biome-ignore-all lint/a11y/noRedundantRoles: the roles on the table below are not redundant. `.stack-table` in src/styles.css sets `display: block` under 40rem to lay each row out as a card, and any `display` other than a `table-*` value drops the implicit table roles from the accessibility tree in every engine. Above the breakpoint the attributes restate what the elements already mean; below it they are the only thing relating a cell to its row. The lint rule reads the markup and cannot see the stylesheet.
// biome-ignore-all lint/a11y/useSemanticElements: the semantic elements are already in use. `table`, `thead`, `tr`, `th`, `td`. This rule fires on the same attributes as the one above, for the same reason, and has the same answer.
import { type Component, createMemo, createSignal, For, Show } from "solid-js";
import { RangeField, SelectField } from "~/components/islands/controls";
import { dollarsOn10k, fill, type PlacedRow, queue, ratePercent, shelf } from "~/components/islands/placement-model";
import { defaultTaxRegime, placementAsOf, taxRegimes } from "~/content/placement";
import { derivedRates } from "~/lib/placement";

/**
 * Which account each of the eight funds belongs in, at the reader's own bracket and
 * with the reader's own share of money in retirement accounts.
 *
 * Two inputs, because only two things move the answer: the bracket sets how much each
 * fund's yearly tax is worth avoiding, and the share of money in retirement accounts
 * sets where the queue is cut. RSST's income is counted on the fuller of its two filed
 * readings, which puts it first; it belongs in a retirement account on either reading,
 * and the page says so beside the tool.
 *
 * Rendered on the server with its opening state, so the table is on the page before any
 * script runs and stays there without one.
 */

const WHERE_TEXT: Readonly<Record<PlacedRow["where"], string>> = {
  retirement: "Retirement account",
  split: "Split between the two",
  taxable: "Taxable account",
};

/**
 * Written once, read twice: into `<thead>`, and into the label each cell shows when
 * the table becomes a list of cards below 40rem.
 */
const COLUMNS = ["#", "Fund", "Share", "Saved a year on $10,000 of it", "Goes in"] as const;

const OPENING_RETIREMENT_SHARE = 50;

export const PlacementTool: Component = () => {
  const [bracketId, setBracketId] = createSignal<string>(defaultTaxRegime.id);
  const [retirementPercent, setRetirementPercent] = createSignal(OPENING_RETIREMENT_SHARE);

  const regime = createMemo(() => taxRegimes.find((entry) => entry.id === bracketId()) ?? defaultTaxRegime);
  const rates = () => derivedRates(regime());
  const bracketNote = () =>
    `${ratePercent(rates().qualifiedDividend)}% on dividends taxed at the lower rate and ${ratePercent(rates().ordinary)}% on income taxed like wages`;

  const rows = createMemo(() => queue(shelf("recorded"), regime()));
  const placed = createMemo(() => fill(rows(), retirementPercent() / 100));

  const headline = createMemo(() => {
    const order = rows();
    const first = order[0];
    const last = order[order.length - 1];
    if (first === undefined || last === undefined) return "There is nothing on the fund list to rank.";
    if (rates().qualifiedDividend <= 0) {
      return `At a 0% rate on dividends there is little tax to save on the stock funds. Put ${first.ticker} and the bond fund in the retirement account first, because their income is taxed like wages even at your rate; where the rest sit barely matters.`;
    }
    const names = order.map((row) => row.ticker).join(", ");
    return `Fill the retirement account in this order: ${names}. ${first.ticker} saves the most, ${dollarsOn10k(first.priorityBp)} a year on every $10,000 of it; ${last.ticker} saves the least, ${dollarsOn10k(last.priorityBp)}, so it is the one to leave in the taxable account.`;
  });

  const bracketOptions = taxRegimes.map((entry) => ({
    value: entry.id,
    label: `${ratePercent(derivedRates(entry).qualifiedDividend)}% on dividends, ${ratePercent(derivedRates(entry).ordinary)}% on income taxed like wages`,
  }));

  const whereText = (row: PlacedRow) => {
    if (row.where === "split") {
      return `${WHERE_TEXT.split}: ${ratePercent(row.shelteredWeight, 1)}% of your money fits, and the retirement account is full here.`;
    }
    return `${WHERE_TEXT[row.where]}: ${row.holding.reason}.`;
  };

  return (
    <div class="not-prose">
      <div class="panel grid gap-6 p-5 sm:grid-cols-2">
        <SelectField
          class="sm:col-span-2"
          label="Your federal tax bracket"
          value={bracketId()}
          options={bracketOptions}
          onChange={setBracketId}
          hint="US federal rates, with the 3.8% surtax on investment income included where it applies. State tax is left out and adds to every line."
        />
        <RangeField
          class="sm:col-span-2"
          label="Share of your money in retirement accounts"
          value={retirementPercent()}
          onInput={setRetirementPercent}
          min={0}
          max={100}
          step={1}
          unit="%"
          showBounds
          hint="A Roth and a pre-tax account count the same here: neither pays yearly tax, and both lose the foreign tax you could otherwise claim back."
        />
      </div>

      {/* The sentence and the table move together, so a screen reader hears one update. */}
      <div aria-live="polite">
        <p class="mt-6 max-w-measure text-lg text-ink">{headline()}</p>

        <div
          class="scroller mt-6"
          tabindex="0"
          role="region"
          aria-label="The eight funds, ranked by what a year in a retirement account saves"
        >
          <table role="table" class="stack-table w-full border-collapse text-base sm:min-w-[40rem]">
            <caption class="sr-only">
              What each fund saves a year when $10,000 of it sits in a retirement account rather than a taxable one, at{" "}
              {bracketNote()}, and which account it lands in with {retirementPercent()}% of the money in retirement
              accounts
            </caption>
            <thead role="rowgroup">
              <tr role="row" class="border-b border-rule-strong text-left">
                <For each={COLUMNS}>
                  {(heading, i) => (
                    <th
                      role="columnheader"
                      scope="col"
                      classList={{
                        label: true,
                        "font-semibold": true,
                        "py-2": true,
                        "pr-3": true,
                        "text-right": i() === 0 || i() === 2 || i() === 3,
                      }}
                    >
                      {heading}
                    </th>
                  )}
                </For>
              </tr>
            </thead>
            <tbody role="rowgroup" class="text-ink-2">
              <For each={placed()}>
                {(row, index) => (
                  <tr role="row" class="border-b border-rule align-top last:border-0">
                    <td role="cell" data-label={COLUMNS[0]} data-numeric class="py-2 pr-3 text-right text-ink-3">
                      {index() + 1}
                    </td>
                    <th role="rowheader" scope="row" class="py-2 pr-3 text-left font-medium text-ink">
                      {row.ticker}
                      <span class="block text-sm font-normal text-ink-3">{row.name}</span>
                    </th>
                    <td role="cell" data-label={COLUMNS[2]} data-numeric class="py-2 pr-3 text-right whitespace-nowrap">
                      {ratePercent(row.weight, 1)}%
                    </td>
                    <td
                      role="cell"
                      data-label={COLUMNS[3]}
                      data-numeric
                      class="py-2 pr-3 text-right font-semibold whitespace-nowrap text-ink"
                    >
                      {dollarsOn10k(row.priorityBp)}
                    </td>
                    <td role="cell" data-label={COLUMNS[4]} class="py-2 pr-3">
                      <span class="text-ink">{WHERE_TEXT[row.where]}</span>
                      <Show when={row.where === "split"}>
                        <span data-numeric class="block text-sm text-ink-3">
                          {ratePercent(row.shelteredWeight, 1)}% of your money fits
                        </span>
                      </Show>
                    </td>
                  </tr>
                )}
              </For>
            </tbody>
          </table>
        </div>

        <ul class="mt-6 grid gap-2 text-sm text-ink-2">
          <For each={placed()}>
            {(row) => (
              <li>
                <span class="font-medium text-ink">{row.ticker}.</span> {whereText(row)}
              </li>
            )}
          </For>
        </ul>

        <p data-numeric class="mt-6 max-w-measure text-sm text-ink-3">
          Computed at {bracketNote()}, on yields and withholding rates as of {placementAsOf}. The saved-a-year column
          has already taken off the foreign tax the retirement account loses. The dollar figure is on $10,000 of the
          fund itself, not of the whole portfolio.
        </p>
      </div>
    </div>
  );
};

export default PlacementTool;
