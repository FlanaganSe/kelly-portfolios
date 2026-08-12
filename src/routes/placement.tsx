import { Title } from "@solidjs/meta";
import { createMemo, createUniqueId, For, Show } from "solid-js";
import { Callout } from "~/components/Callout";
import { DataTable } from "~/components/DataTable";
import { Figure } from "~/components/Figure";
import { NumberInput } from "~/components/NumberInput";
import { PageHeader } from "~/components/PageHeader";
import { Prose } from "~/components/Prose";
import { Slider } from "~/components/Slider";
import { SourceLink } from "~/components/SourceLink";
import { referenceInvestor } from "~/content/edgeBudget";
import {
  accountOrder,
  bondCandidate,
  bondRowCaveat,
  breakEvens,
  deferredBalanceIsNotYourMoney,
  developedSleeve,
  emergingCandidate,
  emergingSleeve,
  form1116Threshold,
  hsaLimits,
  type NamedShelterCandidate,
  omissionsNote,
  placementAsOf,
  placementSource,
  priorityRule,
  shelterCandidates,
  statedOmissions,
  taxRegimes,
  usEquityCandidate,
  washSaleTrap,
} from "~/content/placement";
import { clamp } from "~/lib/format";
import {
  type DerivedRates,
  derivedRates,
  forfeitedBp,
  form1116ThresholdAssets,
  locationBreakevenRate,
  shelteredCostBp,
  shelterPriorityBp,
  taxableCostBp,
} from "~/lib/placement";
import { type CustomRegimeRates, useInvestorPolicy } from "~/state/investorPolicy";

/**
 * The page that computes rather than asserts.
 *
 * Every figure here is arithmetic from `~/lib/placement` over data from
 * `~/content/placement`, run at the reader's own bracket. Nothing is read out of the
 * pre-ranked `priorityTable`, because the ranking the recommendation page prints is
 * right for one bracket in four and the whole point of the finding is that it moves.
 */

/**
 * The margin below which the emerging/US gap is not a ranking.
 *
 * The recommendation page calls 2.1 bp at the top bracket "well inside the uncertainty
 * in either dividend yield" and says to treat it as a tie. This is that judgement made
 * into a threshold; it decides wording only, never an ordering.
 */
const TIE_MARGIN_BP = 5;

const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

/** A rate as a percentage, trailing zeros trimmed: 0.06068 to "6.068", 0.238 to "23.8". */
function percent(rate: number, maxDecimals = 3): string {
  const text = (rate * 100).toFixed(maxDecimals);
  return text.includes(".") ? text.replace(/\.?0+$/, "") : text;
}

/** Basis points a year, to one decimal. */
function bp(value: number): string {
  return value.toFixed(1);
}

/** How this asset's taxable cost is built, in words, at the reader's rates. */
function taxableBuild(candidate: NamedShelterCandidate, rates: DerivedRates): string {
  const yieldText = `${percent(candidate.dividendYield)}% yield`;
  if (candidate.foreignWithholdingRate > 0) {
    return `${yieldText} × ${percent(rates.qualifiedDividend)}% qualified, plus ${percent(
      candidate.foreignWithholdingRate
    )}% withheld at source less the credit §904 allows`;
  }
  return candidate.qualifiedFraction === 1
    ? `${yieldText} × ${percent(rates.qualifiedDividend)}% qualified`
    : `${yieldText} × ${percent(rates.ordinary)}% ordinary`;
}

export default function Placement() {
  const policy = useInvestorPolicy();
  const resolved = createMemo(() => policy.resolved());

  const regime = () => resolved().regime;
  const rates = createMemo(() => derivedRates(regime()));
  const utilisation = () => resolved().foreignCreditUtilisation;

  const bracketNote = () =>
    `${percent(rates().qualifiedDividend)}% qualified, ${percent(rates().ordinary)}% ordinary — ${regime().label}`;

  const ranking = createMemo(() =>
    shelterPriorityBp(shelterCandidates, { regime: regime(), foreignCreditUtilisation: utilisation() })
  );

  const rows = createMemo(() => {
    const byLabel = new Map(shelterCandidates.map((candidate) => [candidate.label, candidate]));
    return ranking().flatMap((entry, index) => {
      const candidate = byLabel.get(entry.label);
      if (candidate === undefined) return [];
      return [
        {
          rank: index + 1,
          label: entry.label,
          priorityBp: entry.priorityBp,
          taxableBp: taxableCostBp(candidate, regime(), { foreignCreditUtilisation: utilisation() }),
          shelteredBp: shelteredCostBp(candidate),
          build: taxableBuild(candidate, rates()),
        },
      ];
    });
  });

  const priorityOf = (label: string) => ranking().find((entry) => entry.label === label)?.priorityBp ?? 0;
  const rankOf = (label: string) => ranking().findIndex((entry) => entry.label === label) + 1;
  const margin = () => priorityOf(emergingCandidate.label) - priorityOf(usEquityCandidate.label);
  const inverted = () => rankOf(emergingCandidate.label) > rankOf(usEquityCandidate.label);
  const creditIsWorthless = () => rates().qualifiedDividend <= 0;

  const verdict = () => {
    if (creditIsWorthless()) {
      return `At a 0% qualified rate the credit is worth nothing in either location, so the ranking has nothing to say about the two international sleeves. ${breakEvens.zeroBracketTrap}`;
    }
    if (inverted()) {
      return `Inverted. Emerging-market equity now ranks below US equity by ${bp(
        -margin()
      )} bp, so emerging goes to the taxable account and US equity takes the shelter space. That is the opposite of the familiar rule, and it is the bracket that moved it, not the funds.`;
    }
    if (Math.abs(margin()) < TIE_MARGIN_BP) {
      return `Not inverted, but not a ranking either. Emerging-market equity leads US equity by ${bp(
        margin()
      )} bp for the same shelter dollar, which is inside the uncertainty in either dividend yield. It reads as a tie.`;
    }
    return `The conventional order holds. Emerging-market equity leads US equity by ${bp(
      margin()
    )} bp for the same shelter dollar.`;
  };

  const breakEvenOf = (sleeve: typeof developedSleeve) =>
    locationBreakevenRate({
      international: sleeve,
      domesticDividendYield: usEquityCandidate.dividendYield,
      foreignCreditUtilisation: utilisation(),
    });

  const developedBreakEvenNote = () =>
    creditIsWorthless()
      ? "At a 0% qualified rate this is not a decision. §904 leaves nothing to credit in either location."
      : `Below every positive rate in the US schedule, so developed ex-US takes shelter space ahead of US equity at every one of them. Yours is ${percent(rates().qualifiedDividend)}%, and it ranks ${rankOf(developedSleeve.label)} of ${rows().length}.`;

  const emergingBreakEvenNote = () =>
    creditIsWorthless()
      ? "At a 0% qualified rate this is not a decision either, and the sleeve forfeits the withholding in both locations."
      : `Between two live US rates. Yours is ${percent(rates().qualifiedDividend)}%, ${
          rates().qualifiedDividend >= breakEvenOf(emergingSleeve)
            ? "at or above it, so the shelter wins"
            : "below it, so the taxable account wins"
        }.`;

  const bondTaxableBp = () => taxableCostBp(bondCandidate, regime(), { foreignCreditUtilisation: utilisation() });
  const bondDominance = () => {
    const runnerUp = rows()[1];
    if (runnerUp === undefined || runnerUp.priorityBp <= 0) return null;
    return bondTaxableBp() / runnerUp.priorityBp;
  };

  const regimeSelectId = createUniqueId();
  const hsa = () => accountOrder.find((entry) => entry.id === "hsa");

  const selectRegime = (value: string) => {
    if (value === "custom") {
      const current = regime();
      policy.update({
        regimeId: "custom",
        customRegime: {
          ordinaryIncome: current.ordinaryIncome,
          longTermCapitalGain: current.longTermCapitalGain,
          netInvestmentIncome: current.netInvestmentIncome,
        },
      });
      return;
    }
    const named = taxRegimes.find((entry) => entry.id === value);
    if (named !== undefined) policy.update({ regimeId: named.id, customRegime: undefined });
  };

  /** Percentages in, decimals out, clamped so a half-typed rate cannot fail validation. */
  const setCustomRate = (field: keyof CustomRegimeRates, value: number) => {
    const current = regime();
    policy.update({
      regimeId: "custom",
      customRegime: {
        ordinaryIncome: current.ordinaryIncome,
        longTermCapitalGain: current.longTermCapitalGain,
        netInvestmentIncome: current.netInvestmentIncome,
        [field]: clamp(value, 0, 99.9) / 100,
      },
    });
  };

  return (
    <>
      <Title>Where it's held — Portfolio Edge</Title>

      <PageHeader
        title="Where it's held"
        standfirst="The asset-location ranking has to be computed rather than asserted. The familiar rule is right for bonds by a factor of four and wrong for emerging-market equity at two of the four US dividend rates."
        lastChecked={placementAsOf}
      />

      {/* --- The rule ------------------------------------------------------- */}
      <section aria-labelledby="rule">
        <Prose>
          <h2 id="rule">The rule</h2>
          <p>{priorityRule.plain}</p>
          <p>
            <code>{priorityRule.formula}</code>
          </p>
          <p>{priorityRule.whyForeignIsDifferent}</p>
          <p>{priorityRule.treatyRoute}</p>
        </Prose>
        <p class="mt-4 max-w-measure text-sm">
          <SourceLink citation={priorityRule.source} prefix />
        </p>
      </section>

      {/* --- Your rates ----------------------------------------------------- */}
      <section aria-labelledby="your-rates" class="mt-14">
        <Prose>
          <h2 id="your-rates">Your rates</h2>
          <p>
            Everything below is arithmetic on these. Nothing is sent anywhere — the entries live in this browser and the
            button clears them.
          </p>
        </Prose>

        <div class="mt-6 grid max-w-page gap-6 sm:grid-cols-2">
          <div class="flex flex-col gap-1">
            <label for={regimeSelectId} class="text-sm font-medium text-ink">
              Marginal rates
            </label>
            <select
              id={regimeSelectId}
              class="control w-full max-w-[26rem]"
              value={resolved().regimeId}
              onChange={(event) => selectRegime(event.currentTarget.value)}
            >
              <For each={taxRegimes}>
                {(entry) => (
                  <option value={entry.id}>
                    {entry.label} — {percent(derivedRates(entry).qualifiedDividend)}% qualified,{" "}
                    {percent(derivedRates(entry).ordinary)}% ordinary
                  </option>
                )}
              </For>
              <option value="custom">Your own rates</option>
            </select>
            <p class="max-w-[42ch] text-xs text-ink-faint">
              US federal. The §1411 surtax is included in both figures. State tax is excluded and additive.
            </p>
          </div>

          <Slider
            label="Foreign credit you can actually use"
            value={Math.round(utilisation() * 100)}
            onInput={(value) => policy.update({ foreignCreditUtilisation: value / 100 })}
            min={0}
            max={100}
            step={5}
            unit="%"
            showBounds
            hint="The §904 limitation caps the credit at the US tax on foreign-source income. Below the $300/$600 threshold it is the whole thing."
          />
        </div>

        <Show when={resolved().regimeId === "custom"}>
          <fieldset class="mt-6 max-w-page border-0 p-0">
            <legend class="eyebrow mb-3">Your own rates</legend>
            <div class="grid gap-6 sm:grid-cols-3">
              <NumberInput
                label="Ordinary income rate"
                value={regime().ordinaryIncome * 100}
                onInput={(value) => setCustomRate("ordinaryIncome", value)}
                min={0}
                max={60}
                step={0.1}
                unit="%"
              />
              <NumberInput
                label="Long-term capital gain rate"
                value={regime().longTermCapitalGain * 100}
                onInput={(value) => setCustomRate("longTermCapitalGain", value)}
                min={0}
                max={40}
                step={0.1}
                unit="%"
              />
              <NumberInput
                label="§1411 net investment income surtax"
                value={regime().netInvestmentIncome * 100}
                onInput={(value) => setCustomRate("netInvestmentIncome", value)}
                min={0}
                max={10}
                step={0.1}
                unit="%"
                hint="3.8% above the modified-AGI threshold, which is not indexed. Otherwise 0."
              />
            </div>
          </fieldset>
        </Show>

        <div class="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3">
          <label class="flex items-center gap-2 text-sm text-ink">
            <input
              type="checkbox"
              class="size-4"
              checked={resolved().hasHighDeductiblePlan}
              onChange={(event) => policy.update({ hasHighDeductiblePlan: event.currentTarget.checked })}
            />
            A high-deductible health plan covers me
          </label>

          <Show when={!resolved().isEmpty}>
            <button
              type="button"
              class="inline-flex h-8 items-center rounded-[3px] border border-rule px-3 text-sm text-ink-muted transition-colors hover:border-rule-strong hover:text-ink"
              onClick={() => policy.clear()}
            >
              Clear what I entered
            </button>
          </Show>
        </div>

        {/* The fallback is stated wherever it is being used, not only on a blank page. */}
        <Show when={resolved().defaulted.regimeId}>
          <p class="mt-4 max-w-measure text-sm text-ink-muted">
            No bracket entered, so every figure below is the stated reference investor's: {referenceInvestor.bracket};{" "}
            {referenceInvestor.horizon}; {referenceInvestor.jurisdiction}. Change the bracket and the page recomputes.
          </p>
        </Show>
      </section>

      {/* --- The ranking ---------------------------------------------------- */}
      <section aria-labelledby="ranking" class="mt-14">
        <Prose>
          <h2 id="ranking">What a dollar of shelter capacity saves</h2>
          <p>
            The expression again, with your numbers in it. Each line is that asset's recurring tax in a taxable account,
            less the withholding it would forfeit inside a shelter, at {bracketNote()}.
          </p>
        </Prose>

        {/* The ranking, the fill order and the verdict all change together, so a
            screen reader hears them as one update. */}
        <div aria-live="polite">
          <div class="mt-6 max-w-measure border-l-2 border-rule-strong pl-4 font-mono text-sm">
            <p class="text-ink-muted">priority = taxable cost − sheltered cost</p>
            <ul class="mt-2 space-y-1">
              <For each={rows()}>
                {(row) => (
                  <li data-numeric>
                    {row.label}: {bp(row.taxableBp)} − {bp(row.shelteredBp)} = {bp(row.priorityBp)} bp/yr
                  </li>
                )}
              </For>
            </ul>
          </div>

          <Prose class="mt-6">
            <h3>Fill order</h3>
            <p>The shelter fills from the top of that list. At {bracketNote()}, that is:</p>
            <ol>
              <For each={rows()}>
                {(row) => (
                  <li>
                    {row.label} — {bp(row.priorityBp)} bp/yr
                  </li>
                )}
              </For>
            </ol>
            <p>
              <strong>{inverted() ? "Inverted." : creditIsWorthless() ? "No ranking." : "Conventional order."}</strong>{" "}
              {verdict()}
            </p>
          </Prose>
        </div>

        <DataTable
          class="mt-8"
          caption={`Priority per dollar of shelter capacity, bp/yr, at ${bracketNote()}`}
          columns={[
            { key: "rank", header: "#", numeric: true, width: "3rem", cell: (row) => row.rank },
            { key: "asset", header: "Asset", rowHeader: true, cell: (row) => row.label },
            { key: "build", header: "How the taxable cost is built", cell: (row) => row.build },
            { key: "taxable", header: "Taxable", numeric: true, cell: (row) => bp(row.taxableBp) },
            { key: "sheltered", header: "Sheltered", numeric: true, cell: (row) => bp(row.shelteredBp) },
            { key: "priority", header: "Priority", numeric: true, cell: (row) => bp(row.priorityBp) },
          ]}
          rows={rows()}
          footnote={
            <>
              Computed at {bracketNote()}, with {percent(utilisation())}% of the foreign credit usable, on yields and
              withholding rates as of {placementAsOf}. The sheltered column is the same in a traditional account and a
              Roth: an IRA has no US tax to credit the foreign withholding against.{" "}
              <SourceLink citation={placementSource.recommendation} prefix />
            </>
          }
        />

        <Callout variant="caveat" label="The bond row, restated at your rate">
          <p>
            {bp(bondTaxableBp())} bp/yr, at your {percent(rates().ordinary)}% ordinary rate. {bondRowCaveat.headline}{" "}
            The 189.7 bp the recommendation page prints is the 40.8% top ordinary rate, and it belongs with the 23.8%
            qualified column and no other.
          </p>
          <Show when={bondDominance()}>
            {(ratio) => (
              <p>
                It still leads the next line by {ratio().toFixed(1)} to one, which is why restating it does not move the
                ranking. The uncontested half of the conventional rule stays uncontested.
              </p>
            )}
          </Show>
          <p>
            <SourceLink citation={bondRowCaveat.source} prefix />
          </p>
        </Callout>

        <Callout variant="open-question" label="Two omissions, both cutting against the inversion">
          <ul class="list-disc space-y-2 pl-5">
            <For each={statedOmissions}>{(omission) => <li>{omission.text}</li>}</For>
          </ul>
          <p>{omissionsNote}</p>
        </Callout>
      </section>

      {/* --- Break-evens ---------------------------------------------------- */}
      <section aria-labelledby="break-evens" class="mt-14">
        <Prose>
          <h2 id="break-evens">Where each sleeve turns over</h2>
          <p>
            The break-even is closed form: <code>{breakEvens.formula}</code>. Below that qualified rate the sleeve
            belongs in the taxable account; above it, in the shelter. Both are stated against the{" "}
            {percent(usEquityCandidate.dividendYield)}% US equity yield, which is a stated input rather than a retrieved
            measurement.
          </p>
        </Prose>

        <div class="mt-6 flex flex-wrap gap-x-12 gap-y-6">
          <Figure
            label="Developed ex-US break-even"
            value={percent(breakEvenOf(developedSleeve), 2)}
            unit="% qualified"
            note={developedBreakEvenNote()}
            asOf={placementAsOf}
            source={developedSleeve.source}
          />
          <Figure
            label="Emerging break-even"
            value={percent(breakEvenOf(emergingSleeve), 2)}
            unit="% qualified"
            note={emergingBreakEvenNote()}
            asOf={placementAsOf}
            source={emergingSleeve.source}
          />
          <Figure
            label="Forfeited inside any shelter, developed"
            value={bp(forfeitedBp(developedSleeve))}
            unit="bp/yr"
            note="Yield × withholding rate. Bracket-independent, and identical in a traditional account and a Roth."
            asOf={developedSleeve.asOf}
            source={developedSleeve.source}
          />
          <Figure
            label="Forfeited inside any shelter, emerging"
            value={bp(forfeitedBp(emergingSleeve))}
            unit="bp/yr"
            note="Forfeits more while yielding less, because the withholding rate is 62% higher."
            asOf={emergingSleeve.asOf}
            source={emergingSleeve.source}
          />
        </div>

        <Prose class="mt-6">
          <p>{breakEvens.whyEmergingInverts}</p>
          <p>{breakEvens.zeroBracketTrap}</p>
        </Prose>
      </section>

      {/* --- Account by account --------------------------------------------- */}
      <section aria-labelledby="accounts" class="mt-14">
        <Prose>
          <h2 id="accounts">Account by account</h2>
          <p>
            The ranking says what competes for shelter space. This says which shelter, and the order does not depend on
            the bracket.
          </p>
        </Prose>

        <DataTable
          class="mt-6"
          caption="Account order, and what each one holds"
          columns={[
            { key: "account", header: "Account", rowHeader: true, cell: (row) => row.account },
            { key: "holds", header: "Holds", cell: (row) => row.holds },
            { key: "why", header: "Why", cell: (row) => row.why },
          ]}
          rows={accountOrder}
          footnote={<SourceLink citation={placementSource.structural} prefix />}
        />

        <div class="mt-8 flex flex-wrap gap-x-12 gap-y-6">
          <Figure
            label={`HSA limit ${hsaLimits.taxYear}, self-only`}
            value={usd.format(hsaLimits.selfOnlyUsd)}
            asOf={hsaLimits.asOf}
            source={hsaLimits.source}
          />
          <Figure
            label={`HSA limit ${hsaLimits.taxYear}, family`}
            value={usd.format(hsaLimits.familyUsd)}
            asOf={hsaLimits.asOf}
            source={hsaLimits.source}
          />
          <Figure
            label="Age-55 catch-up"
            value={usd.format(hsaLimits.age55CatchUpUsd)}
            note={hsaLimits.catchUpNote}
            asOf={hsaLimits.asOf}
            source={hsaLimits.source}
          />
        </div>

        <Show when={hsa()}>
          {(entry) => (
            <Callout variant="caveat" label="What breaks the HSA">
              <ul class="list-disc space-y-2 pl-5">
                <For each={entry().conditions}>{(condition) => <li>{condition}</li>}</For>
              </ul>
              <Show when={!resolved().hasHighDeductiblePlan}>
                <p>
                  The high-deductible box is unticked, so the HSA line does not apply to what you have entered. The rest
                  of the order is unaffected.
                </p>
              </Show>
            </Callout>
          )}
        </Show>

        <Callout variant="mechanism" label={deferredBalanceIsNotYourMoney.headline}>
          <p>{deferredBalanceIsNotYourMoney.detail}</p>
        </Callout>
      </section>

      {/* --- Form 1116 ------------------------------------------------------ */}
      <section aria-labelledby="form-1116" class="mt-14">
        <Prose>
          <h2 id="form-1116">Where the credit stops being free</h2>
          <p>{form1116Threshold.detail}</p>
        </Prose>

        <div class="mt-6 flex flex-wrap gap-x-12 gap-y-6">
          <Figure
            label="Developed holdings that reach the single threshold"
            value={usd.format(
              form1116ThresholdAssets({ foreignTaxLimit: form1116Threshold.singleUsd, sleeve: developedSleeve })
            )}
            note={`${usd.format(form1116Threshold.singleUsd)} of creditable foreign tax at ${percent(
              developedSleeve.withholdingRate
            )}% on a ${percent(developedSleeve.dividendYield)}% yield. Statutory, so it does not move with your bracket.`}
            asOf={form1116Threshold.asOf}
            source={form1116Threshold.source}
          />
          <Figure
            label="Filing jointly"
            value={usd.format(
              form1116ThresholdAssets({ foreignTaxLimit: form1116Threshold.jointUsd, sleeve: developedSleeve })
            )}
            note={`${usd.format(form1116Threshold.jointUsd)} of creditable foreign tax, same sleeve, same rate.`}
            asOf={form1116Threshold.asOf}
            source={form1116Threshold.source}
          />
        </div>

        <Prose class="mt-6">
          <ul>
            <For each={form1116Threshold.caveats}>{(caveat) => <li>{caveat}</li>}</For>
          </ul>
        </Prose>
      </section>

      {/* --- The wash-sale trap --------------------------------------------- */}
      <section aria-labelledby="wash-sale" class="mt-14">
        <Prose>
          <h2 id="wash-sale">The one that is permanent</h2>
          <p>
            Most tax-loss mistakes cost timing. This one costs the deduction, and a same-account check does not catch
            it.
          </p>
        </Prose>

        <Callout variant="caveat" label={washSaleTrap.headline}>
          <p>{washSaleTrap.detail}</p>
          <p>{washSaleTrap.whyItMatters}</p>
          <p>
            <span data-numeric>{washSaleTrap.costBp} bp</span> — {washSaleTrap.costBasis}, so it is a top-bracket figure
            and shrinks with the ordinary rate. The mechanic does not: the deduction is destroyed at every bracket.
          </p>
          <p>
            <SourceLink citation={washSaleTrap.source} prefix />
          </p>
        </Callout>
      </section>
    </>
  );
}
