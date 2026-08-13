import { Title } from "@solidjs/meta";
import { A } from "@solidjs/router";
import { createMemo, For, type ParentComponent, Show } from "solid-js";
import { createStore } from "solid-js/store";
import { type BudgetBar, type BudgetBarGroup, BudgetBars } from "~/components/BudgetBars";
import { Callout } from "~/components/Callout";
import { DataTable } from "~/components/DataTable";
import { Figure } from "~/components/Figure";
import { PageHeader } from "~/components/PageHeader";
import { Prose } from "~/components/Prose";
import { SourceLink } from "~/components/SourceLink";
import { CertaintyChip } from "~/components/StatusChip";
import { contractualRows } from "~/content/confidence";
import {
  budgetAssumptions,
  deferralHurdle,
  type EdgeBudgetLine,
  edgeBudgetLines,
  edgeBudgetTotal,
  notBooked,
  referenceInvestor,
} from "~/content/edgeBudget";
import { formatNumber, roundTo } from "~/lib/format";
import { horizonForConfidence, probabilityOfOutperformance, terminalWealthRatio } from "~/lib/horizon";
import { useInvestorPolicy } from "~/state/investorPolicy";

/**
 * The contractual budget: about 109 bp a year against the portfolio the reader would
 * otherwise have owned, line by line, with a switch on each line.
 *
 * The rule the page exists to enforce is that lines measured against different
 * benchmarks never add. `sumOneBenchmark` below is the only function here that
 * produces a total, and it refuses both a mixed benchmark and any line whose role is
 * not booked — the same refusal `aggregate()` makes in `~/lib/horizon` and
 * `studies/outperformance_horizon.py`. Decision 0007 constraint 3.
 */

const H2 = "font-sans text-xl font-semibold tracking-[-0.015em] text-ink";
const H3 = "font-sans text-base font-semibold text-ink";

const OWN_COUNTERFACTUAL = "the portfolio you would otherwise have owned";
const STATED_INDEX = "a cheap index";
const AVERAGE_INVESTOR = "the average investor";

/** Print an exact content figure without rounding it, with the site's typographic minus. */
const bp = (value: number): string => String(value).replace("-", "−");

const bookedLines = edgeBudgetLines.filter(
  (line) => line.role === "base" || line.role === "additive" || line.role === "correction"
);
const hurdleLines = edgeBudgetLines.filter((line) => line.role === "hurdle");
const riskControlLines = edgeBudgetLines.filter((line) => line.role === "risk-control");
const otherBenchmarkLines = edgeBudgetLines.filter((line) => line.role === "reported-not-booked");

/**
 * Every record this page needs, or a loud failure.
 *
 * A fallback number written here would be a number the content layer does not own,
 * which is the defect constraint 1 of decision 0007 names. If a record is renamed or
 * dropped the page breaks, which is the intended coupling.
 */
function mustFind<T>(item: T | undefined, what: string): T {
  if (item === undefined) throw new RangeError(`${what} is missing from src/content/`);
  return item;
}

const fundStructure = mustFind(
  edgeBudgetLines.find((line) => line.id === "fund-structure"),
  "the fund-structure line"
);
const deferralLine = mustFind(
  edgeBudgetLines.find((line) => line.id === "deferral-hurdle"),
  "the deferral-hurdle line"
);
const rebalancingLine = mustFind(
  edgeBudgetLines.find((line) => line.id === "rebalancing"),
  "the rebalancing line"
);
const versusIndex = mustFind(
  contractualRows.find((row) => row.id === "vs-cheap-index"),
  "the cheap-index confidence row"
);
const versusAverageInvestor = mustFind(
  contractualRows.find((row) => row.id === "vs-average-investor"),
  "the average-investor confidence row"
);

/** The thirty-year split, which is the one the concavity table is priced at. */
const thirtyYearDeferralBp = mustFind(
  deferralHurdle.byHorizon.find((row) => row.years === 30),
  "the thirty-year deferral row"
).deferralBp;
const tenthOfGainCost = mustFind(
  deferralHurdle.concavityAtThirtyYears.find((row) => row.shareOfStandingGainRealisedAnnually === 0.1),
  "the tenth-of-standing-gain concavity row"
).costBp;

/** What a line is measured against. Only one line in the record uses a different yardstick. */
function benchmarkOf(line: EdgeBudgetLine): string {
  return line.certaintyClass === "different-benchmark" ? STATED_INDEX : OWN_COUNTERFACTUAL;
}

/**
 * The only total on this page.
 *
 * It throws on a mixed benchmark, and on any line the ledger did not book — a hurdle
 * is avoided rather than earned, and a risk control buys exposure rather than return.
 * Both refusals mirror `aggregate()` rather than restating it in prose.
 */
function sumOneBenchmark(lines: readonly EdgeBudgetLine[]): number {
  const benchmarks = [...new Set(lines.map(benchmarkOf))];
  if (benchmarks.length > 1) {
    throw new RangeError(`lines must share one benchmark; got ${[...benchmarks].sort().join(", ")}`);
  }
  for (const line of lines) {
    if (line.role === "hurdle" || line.role === "risk-control" || line.role === "reported-not-booked") {
      throw new RangeError(`${line.id} has role ${line.role} and may not enter a total`);
    }
  }
  return lines.reduce((total, line) => total + line.basisPoints, 0);
}

/**
 * Per-line tracking error, which the record does not state.
 *
 * `docs/research/` gives one combined figure — 46 bp for the whole booked budget — and
 * per-line numbers for the three original lines only. So the page apportions the
 * recorded 46 bp across the booked lines by the width of each line's stated range, in
 * quadrature, with one rule from the ledger itself: a line whose low bound stays above
 * zero cannot fail to arrive, so it carries no tracking error at all. That is why fund
 * cost, the largest line, contributes none.
 *
 * The apportionment is a convention, and it is stated on the page as one. It
 * reproduces the recorded 46 bp exactly with every line on, and with it the recorded
 * 3.5-month and twelve-month confidence horizons.
 */
function spreadOf(line: EdgeBudgetLine): number {
  if (line.range === undefined || line.range[0] > 0) return 0;
  return line.range[1] - line.range[0];
}

const spreadQuadrature = Math.sqrt(bookedLines.reduce((total, line) => total + spreadOf(line) ** 2, 0));
const trackingErrorPerSpread = edgeBudgetTotal.combinedTrackingErrorBp / spreadQuadrature;
const trackingErrorOf = (line: EdgeBudgetLine): number => spreadOf(line) * trackingErrorPerSpread;

/** A correction cannot be claimed once the line it corrects has gone. */
const dependsOn: Readonly<Record<string, string>> = {
  "direct-indexing-fee": "tax-loss-harvesting",
  "foreign-tax-credit-forfeited": "asset-location",
};

const ACCOUNT_KEYS = ["taxable", "traditional", "roth", "hsa"] as const;

function formatHorizon(years: number): string {
  if (years <= 0) return "immediately";
  if (years < 1 / 12) return `${formatNumber(years * 365, 0)} days`;
  if (years < 2) return `${formatNumber(years * 12, 1)} months`;
  if (years < 10) return `${formatNumber(years, 1)} years`;
  return `${formatNumber(years, 0)} years`;
}

const LineDetail: ParentComponent<{ readonly line: EdgeBudgetLine; readonly class?: string }> = (props) => {
  return (
    <article class={`max-w-measure border-t border-rule pt-5 ${props.class ?? ""}`}>
      <h3 class={H3}>{props.line.label}</h3>

      <div class="mt-2 flex flex-wrap items-baseline gap-x-4 gap-y-2">
        <span data-numeric class="text-sm font-medium text-ink">
          {bp(props.line.basisPoints)} bp/yr
          <Show when={props.line.range}>
            {(range) => (
              <span class="text-ink-faint">
                {" "}
                ({bp(range()[0])} to {bp(range()[1])})
              </span>
            )}
          </Show>
        </span>
        <CertaintyChip certainty={props.line.certaintyClass} />
        <span class="text-sm text-ink-muted">{props.line.decaying ? "Decaying" : "Not decaying"}</span>
      </div>

      <p class="mt-3 text-sm text-ink-muted">
        <span class="eyebrow">Needs to be true — </span>
        {props.line.appliesWhen}.
      </p>

      <p class="mt-3 text-ink">{props.line.explanation}</p>

      <Show when={props.line.caveat}>
        {(caveat) => (
          <Callout variant="caveat">
            <p>{caveat()}</p>
          </Callout>
        )}
      </Show>

      {props.children}

      <p class="mt-3 flex flex-wrap items-baseline gap-x-4 gap-y-1">
        <Show when={props.line.asOf}>
          {(date) => (
            <span data-numeric class="text-xs text-ink-faint">
              as of {date()}
            </span>
          )}
        </Show>
        <SourceLink citation={props.line.source} prefix />
      </p>
    </article>
  );
};

export default function EdgeBudget() {
  const policy = useInvestorPolicy();
  const resolved = () => policy.resolved();

  const [switchedOn, setSwitchedOn] = createStore<Record<string, boolean>>(
    Object.fromEntries(bookedLines.map((line) => [line.id, true]))
  );

  /**
   * What the reader's own accounts settle. An unentered account is not a zero
   * balance, so nothing is withdrawn until balances have actually been entered.
   */
  const accountFacts = createMemo(() => {
    const current = resolved();
    const entered = !current.defaulted.accounts;
    const balances = current.accounts;
    const shelter = (balances.traditional ?? 0) + (balances.roth ?? 0) + (balances.hsa ?? 0);
    const typesHeld = ACCOUNT_KEYS.filter((key) => (balances[key] ?? 0) > 0).length;
    return {
      entered,
      hasTaxable: !entered || (balances.taxable ?? 0) > 0,
      hasShelter: !entered || shelter > 0,
      hasTwoTypes: !entered || typesHeld >= 2,
    };
  });

  const unavailableReason = (id: string): string | undefined => {
    const facts = accountFacts();
    switch (id) {
      case "tax-loss-harvesting":
        if (!facts.hasTaxable)
          return "No taxable balance. A sheltered account has no gain to offset and no loss to harvest.";
        if (!resolved().contributionsContinue)
          return "Contributions have stopped. Without new money the honest thirty-year figure is 5.6 bp, and negative at any fee.";
        return undefined;
      case "asset-location":
        if (!facts.hasTwoTypes) return "One account type. There is no second account to move anything into.";
        return undefined;
      case "foreign-tax-credit-forfeited":
        if (!facts.hasShelter) return "No sheltered balance, so no credit is trapped anywhere.";
        return undefined;
      case "fund-structure":
      case "specific-identification":
        if (!facts.hasTaxable) return "Taxable account only. A distribution inside a shelter is not a taxable event.";
        return undefined;
      default:
        return undefined;
    }
  };

  const blockedByParent = (id: string): string | undefined => {
    const parent = dependsOn[id];
    if (parent === undefined || counted(parent)) return undefined;
    const line = bookedLines.find((candidate) => candidate.id === parent);
    return `Follows "${line?.label ?? parent}", which is off. A correction cannot outlive the line it corrects.`;
  };

  const counted = (id: string): boolean => {
    if (!switchedOn[id]) return false;
    if (unavailableReason(id) !== undefined) return false;
    const parent = dependsOn[id];
    return parent === undefined || counted(parent);
  };

  const countedLines = createMemo(() => bookedLines.filter((line) => counted(line.id)));
  const totalBp = createMemo(() => roundTo(sumOneBenchmark(countedLines()), 4));
  const trackingErrorBp = createMemo(() =>
    Math.sqrt(countedLines().reduce((total, line) => total + trackingErrorOf(line) ** 2, 0))
  );

  const horizonAt = (confidence: number): string => {
    if (totalBp() <= 0) return "never";
    return formatHorizon(horizonForConfidence({ edgeBp: totalBp(), trackingErrorBp: trackingErrorBp(), confidence }));
  };

  const growthMultiple = createMemo(() =>
    terminalWealthRatio({ edgeBp: totalBp(), horizonYears: resolved().horizonYears })
  );

  const probabilityAtHorizon = createMemo(() =>
    totalBp() <= 0
      ? null
      : probabilityOfOutperformance({
          edgeBp: totalBp(),
          trackingErrorBp: trackingErrorBp(),
          horizonYears: resolved().horizonYears,
        })
  );

  /** The whole-budget figure with the fund-structure line gone, computed rather than quoted. */
  const budgetWithoutFundStructure = roundTo(edgeBudgetTotal.basisPoints - fundStructure.basisPoints, 1);

  const chartGroups = createMemo<readonly BudgetBarGroup[]>(() => {
    const bookedBars: BudgetBar[] = bookedLines.map((line) => ({
      id: line.id,
      label: line.label,
      basisPoints: line.basisPoints,
      kind: counted(line.id) ? "counted" : "off",
      tag: counted(line.id) ? (line.role === "correction" ? "correction, counted" : "counted") : "not counted for you",
    }));

    bookedBars.push({
      id: "subtotal",
      label: "Your budget, against your own counterfactual",
      basisPoints: roundTo(totalBp(), 1),
      kind: "subtotal",
      tag: "the only total here",
    });

    const groups: BudgetBarGroup[] = [
      {
        id: "counterfactual",
        benchmark: OWN_COUNTERFACTUAL,
        note: "Bought with arithmetic and tax law rather than with a forecast. These are the lines that add.",
        bars: bookedBars,
      },
      {
        id: "not-booked",
        benchmark: `${OWN_COUNTERFACTUAL} — and still not in that total`,
        note: "Same yardstick, deliberately outside the sum. One is a cost avoided, the other buys exposure control rather than return.",
        bars: [
          ...hurdleLines.map<BudgetBar>((line) => ({
            id: line.id,
            label: line.label,
            basisPoints: line.basisPoints,
            kind: "hurdle",
            tag: "hurdle — a cost avoided",
          })),
          ...riskControlLines.map<BudgetBar>((line) => ({
            id: line.id,
            label: line.label,
            basisPoints: line.basisPoints,
            kind: "risk-control",
            tag: "risk control — not a return",
          })),
        ],
      },
    ];

    groups.push({
      id: "stated-index",
      benchmark: STATED_INDEX,
      note: "A harder benchmark and a much larger tracking error. Nothing in this block may be added to the block above.",
      bars: [
        {
          id: versusIndex.id,
          label: versusIndex.label,
          basisPoints: versusIndex.edgeBp,
          kind: "other-benchmark",
          tag: `${versusIndex.trackingErrorBp} bp of tracking error`,
        },
        ...otherBenchmarkLines.map<BudgetBar>((line) => ({
          id: line.id,
          label: line.label,
          basisPoints: line.basisPoints,
          kind: "other-benchmark",
          tag: "a revision inside that figure, not an addition to it",
        })),
      ],
    });

    groups.push({
      id: "average-investor",
      benchmark: AVERAGE_INVESTOR,
      note: "The behaviour gap. Someone already holding broad index funds and not trading has a gap of exactly zero, so there is nothing here left to collect.",
      bars: [
        {
          id: versusAverageInvestor.id,
          label: versusAverageInvestor.label,
          basisPoints: versusAverageInvestor.edgeBp,
          kind: "other-benchmark",
          tag: "different benchmark — never added",
        },
      ],
    });

    return groups;
  });

  const chartLabel = () =>
    `Edge budget by benchmark. Against ${OWN_COUNTERFACTUAL}, the lines switched on total ${bp(roundTo(totalBp(), 1))} basis points a year. ` +
    `Below it, ${bp(thirtyYearDeferralBp)} basis points of deferral hurdle and a rebalancing line at zero are drawn as outlines because they are in no total. ` +
    `The remaining blocks are measured against ${STATED_INDEX} at ${versusIndex.edgeBp} basis points and against ${AVERAGE_INVESTOR} at ${versusAverageInvestor.edgeBp}, and neither adds to the first.`;

  const defaultedFields = createMemo(() => {
    const current = resolved();
    const fields: string[] = [];
    if (current.defaulted.accounts) fields.push("your account mix");
    if (current.defaulted.horizonYears) fields.push(`your horizon (${current.horizonYears} years)`);
    if (current.defaulted.contributionsContinue)
      fields.push(`whether contributions continue (${current.contributionsContinue ? "yes" : "no"})`);
    if (current.defaulted.regimeId) fields.push(`your bracket (${current.regime.label})`);
    return fields;
  });

  return (
    <>
      <Title>Edge budget — Portfolio Edge</Title>
      <PageHeader
        title="Edge budget"
        standfirst="What is available against the portfolio you would otherwise have owned, line by line."
        lastChecked={edgeBudgetTotal.asOf}
      />

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="headline" class="mt-4">
        <h2 id="headline" class="sr-only">
          The headline
        </h2>

        <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <Figure
            label="Against your own counterfactual"
            value={String(edgeBudgetTotal.basisPoints)}
            unit="bp/yr"
            size="lg"
            interval={`${bp(edgeBudgetTotal.outerBound[0])} to ${bp(edgeBudgetTotal.outerBound[1])}`}
            intervalLabel="outer bound"
            note="An outer bound, not a distribution: it assumes every condition fails together, then succeeds together."
          />
          <Figure
            label="Combined tracking error"
            value={String(edgeBudgetTotal.combinedTrackingErrorBp)}
            unit="bp/yr"
            size="lg"
            note="The number that makes the budget near-certain. It is never quoted without it."
          />
          <Figure
            label="Against a cheap index"
            value={String(versusIndex.edgeBp)}
            unit="bp/yr"
            size="lg"
            note={`Against ${versusIndex.trackingErrorBp} bp of tracking error — a ${versusIndex.probability30yr} probability of being ahead after thirty years. Both figures belong in the same place.`}
            source={edgeBudgetTotal.source}
            asOf={edgeBudgetTotal.asOf}
          />
        </div>

        <Prose as="section" class="mt-10">
          <p>
            The 109 bp is not a return against the market. It is what you gain against{" "}
            <em>the portfolio you would otherwise have owned</em> — a different benchmark, an easier one, and a
            completely legitimate one. It is worth more than any tilt in this repository, and unlike a tilt it is
            near-certain, because it is bought with arithmetic and tax law rather than with forecasts.
          </p>
          <p>
            Over thirty years, 109 bp/yr of log growth compounds to{" "}
            <strong data-numeric>
              {formatNumber(terminalWealthRatio({ edgeBp: edgeBudgetTotal.basisPoints, horizonYears: 30 }), 2)}× the
              terminal wealth
            </strong>{" "}
            of the same portfolio without it — <code>exp(0.0109 × 30)</code>. That's a ratio, not a forecast. It holds
            whatever the market does, and it needs no view on any market to collect. That is the whole of what separates
            it from every other large number in investing.
          </p>
          <p>
            Against a cheap index the same budget is about {versusIndex.edgeBp} bp against {versusIndex.trackingErrorBp}{" "}
            bp of tracking error, which is a {versusIndex.probability30yr} probability of being ahead after thirty
            years. Nothing here beats an index. The last section of this page states that case in full rather than
            leaving it as a footnote.
          </p>
        </Prose>

        <div class="mt-6 flex flex-wrap items-baseline gap-x-5 gap-y-2">
          <CertaintyChip certainty={edgeBudgetTotal.certaintyClass} showGloss />
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="your-budget" class="mt-16">
        <h2 id="your-budget" class={H2}>
          Your budget
        </h2>
        <p class="mt-2 max-w-measure text-ink-muted">
          Every line starts on. Switch off what doesn't apply and the total, the tracking error and the confidence
          horizons all move together. A line the record makes unavailable to you is switched off and locked, with the
          reason beside it.
        </p>

        <Show when={defaultedFields().length > 0}>
          <Callout variant="caveat" label="These are the reference investor's figures, not yours">
            <p>
              Nothing has been entered for {defaultedFields().join(", ")}, so this page is using{" "}
              {referenceInvestor.bracket}, a {referenceInvestor.horizon.toLowerCase()} horizon and{" "}
              {referenceInvestor.accounts}. Every line is sized for that investor:{" "}
              {referenceInvestor.jurisdiction.toLowerCase()}, {referenceInvestor.allocation}. Entering your own figures
              on{" "}
              <A href="/placement" class="link">
                Where it's held
              </A>{" "}
              narrows this page. Nothing on it is gated behind them.
            </p>
          </Callout>
        </Show>

        <div class="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_20rem]">
          <fieldset class="min-w-0 border-0 p-0">
            <legend class="eyebrow mb-2">Lines available to you</legend>
            <ul class="flex flex-col">
              <For each={bookedLines}>
                {(line) => {
                  const reason = () => unavailableReason(line.id) ?? blockedByParent(line.id);
                  const locked = () => reason() !== undefined;
                  return (
                    <li class="border-t border-rule py-3 first:border-t-0">
                      <label class="flex cursor-pointer items-start gap-3">
                        <input
                          type="checkbox"
                          class="mt-1 size-4 shrink-0 accent-accent"
                          checked={switchedOn[line.id] && !locked()}
                          disabled={locked()}
                          onChange={(event) => setSwitchedOn(line.id, event.currentTarget.checked)}
                        />
                        <span class="min-w-0 flex-1">
                          <span class="flex flex-wrap items-baseline justify-between gap-x-3">
                            <span class={locked() ? "text-ink-faint" : "text-ink"}>{line.label}</span>
                            <span
                              data-numeric
                              class={`text-sm ${locked() ? "text-ink-faint" : "font-medium text-ink"}`}
                            >
                              {bp(line.basisPoints)} bp
                            </span>
                          </span>
                          <span class="mt-1 block text-sm text-ink-muted">{line.appliesWhen}.</span>
                          <Show when={reason()}>
                            {(why) => <span class="mt-1 block text-sm text-caution">{why()}</span>}
                          </Show>
                        </span>
                      </label>
                    </li>
                  );
                }}
              </For>
            </ul>
          </fieldset>

          <div class="min-w-0 self-start rounded-[3px] border border-rule bg-sunken p-5">
            <div aria-live="polite" class="flex flex-col gap-5">
              <Figure
                label={`Your total, against ${OWN_COUNTERFACTUAL}`}
                value={bp(roundTo(totalBp(), 1))}
                unit="bp/yr"
                size="lg"
              />
              <Figure
                label="Combined tracking error, in quadrature"
                value={formatNumber(trackingErrorBp(), 1)}
                unit="bp/yr"
                size="sm"
              />
              <Figure label="90% confident after" value={horizonAt(0.9)} size="sm" />
              <Figure label="99% confident after" value={horizonAt(0.99)} size="sm" />
              <Figure
                label={`Terminal wealth after ${resolved().horizonYears} years`}
                value={`${formatNumber(growthMultiple(), 2)}×`}
                size="sm"
                note="The same portfolio without the budget is 1.00×. No market return is assumed anywhere in that ratio."
              />
              <Show when={probabilityAtHorizon()}>
                {(probability) => (
                  <Figure
                    label={`Probability of being ahead at ${resolved().horizonYears} years`}
                    value={formatNumber(probability(), 3)}
                    size="sm"
                    note="An upper bound. The arithmetic treats the edge as known, which removes the dominant source of uncertainty."
                  />
                )}
              </Show>
            </div>
            <p class="mt-5 border-t border-rule pt-4 text-xs text-ink-muted">
              The behaviour gap is not in this total and cannot be switched into it. It is measured against{" "}
              {AVERAGE_INVESTOR}; this total is measured against your own counterfactual.
            </p>
          </div>
        </div>

        <Callout variant="caveat" label="One number here is a convention, not a measurement">
          <p>
            The record states a single combined tracking error — {edgeBudgetTotal.combinedTrackingErrorBp} bp for the
            whole booked budget — and per-line figures for the three original lines only. So this page apportions the
            recorded {edgeBudgetTotal.combinedTrackingErrorBp} bp across the booked lines by the width of each line's
            stated range, in quadrature, with one rule taken from the ledger: a line whose low bound stays above zero
            cannot fail to arrive and carries no tracking error at all. That is why fund cost, the largest line,
            contributes none. With every line on, the apportionment returns exactly{" "}
            {edgeBudgetTotal.combinedTrackingErrorBp} bp and reproduces the recorded{" "}
            {edgeBudgetTotal.ninetyPercentConfidence} and {edgeBudgetTotal.ninetyNinePercentConfidence} horizons. Switch
            a line off and the figure is a convention doing the work of a measurement nobody made.
          </p>
        </Callout>
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="chart" class="mt-16">
        <h2 id="chart" class={H2}>
          The same thing as a picture
        </h2>

        <BudgetBars
          class="mt-6"
          caption="Every line in the record, grouped by what it is measured against. Blocks are separated because their totals do not add."
          ariaLabel={chartLabel()}
          groups={chartGroups()}
          footnote={
            <>
              A solid bar sits inside its own block's total. An outlined bar is in no total: switched off, a hurdle, a
              risk control, or booked against another benchmark. <SourceLink citation={edgeBudgetTotal.source} prefix />
            </>
          }
        />
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="lines" class="mt-16">
        <h2 id="lines" class={H2}>
          The lines, in full
        </h2>
        <p class="mt-2 max-w-measure text-ink-muted">
          Seven lines make the total. Each says what it needs to be true, what class of thing it is, whether it is
          shrinking, and what would break it.
        </p>

        <div class="mt-8 flex flex-col gap-8">
          <For each={bookedLines}>
            {(line) => (
              <LineDetail line={line}>
                <Show when={line.id === "fund-structure"}>
                  <Callout variant="open-question" label="Decaying while it is being measured">
                    <p>
                      Ninety-four SEC orders have been granted as of {line.asOf}, covering roughly ninety fund families,
                      and only two applications are still noticed and unordered. When mutual funds add ETF share classes
                      broadly, the counterfactual this line is measured against stops distributing and the line goes
                      toward zero. The budget then falls from {edgeBudgetTotal.basisPoints} bp to about{" "}
                      {budgetWithoutFundStructure} bp. This is the largest new line in the ledger and the one with a
                      standing instruction attached: re-check the order count before leaning on it.
                    </p>
                  </Callout>
                </Show>
              </LineDetail>
            )}
          </For>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="not-booked" class="mt-16">
        <h2 id="not-booked" class={H2}>
          Measured against the same yardstick, and still not in the total
        </h2>
        <p class="mt-2 max-w-measure text-ink-muted">
          Both of these are real and both are large enough to matter. Neither is a return you collect, so neither is
          added.
        </p>

        <div class="mt-8">
          <LineDetail line={deferralLine} />

          <div class="mt-8 max-w-measure">
            <h3 class={H3}>Why "low turnover" is not a defence</h3>
            <p class="mt-2 text-ink-muted">
              The function is sharply concave. Realising a tenth of the standing gain each year already costs{" "}
              {tenthOfGainCost} bp of the {thirtyYearDeferralBp} — about half the penalty, for a tenth of the turnover.
              Trading less buys far less than the proportions suggest.
            </p>
          </div>

          <DataTable
            class="mt-6"
            caption="Cost of realising a share of the standing gain each year, at thirty years"
            columns={[
              {
                key: "share",
                header: "Share realised each year",
                rowHeader: true,
                cell: (row) => `${row.shareOfStandingGainRealisedAnnually * 100}%`,
              },
              { key: "cost", header: "Cost, bp/yr", numeric: true, cell: (row) => bp(row.costBp) },
              {
                key: "share-of-max",
                header: "Share of the full penalty",
                numeric: true,
                cell: (row) => `${formatNumber((row.costBp / thirtyYearDeferralBp) * 100, 0)}%`,
              },
            ]}
            rows={deferralHurdle.concavityAtThirtyYears}
          />

          <DataTable
            class="mt-10"
            caption="Deferral and the step-up, by horizon. The total is horizon-free; the horizon only decides how it splits."
            columns={[
              { key: "years", header: "Horizon", rowHeader: true, cell: (row) => `${row.years} years` },
              { key: "deferral", header: "Deferral, bp/yr", numeric: true, cell: (row) => bp(row.deferralBp) },
              { key: "stepup", header: "Step-up, bp/yr", numeric: true, cell: (row) => bp(row.stepUpBp) },
              { key: "total", header: "Total, bp/yr", numeric: true, cell: (row) => bp(row.totalBp) },
            ]}
            rows={deferralHurdle.byHorizon}
            footnote={
              <>
                Horizon-free total {deferralHurdle.horizonFreeTotalBp} bp. {deferralHurdle.note}{" "}
                {deferralHurdle.vanishesWhen} Your horizon is currently {resolved().horizonYears} years
                {resolved().defaulted.horizonYears ? ", which is the reference investor's rather than yours" : ""}.{" "}
                <SourceLink citation={deferralHurdle.source} prefix />
              </>
            }
          />
        </div>

        <LineDetail line={rebalancingLine} class="mt-12" />
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="other-benchmarks" class="mt-16 border-t-2 border-rule-strong pt-10">
        <h2 id="other-benchmarks" class={H2}>
          Reported against a different benchmark, and never added
        </h2>

        <Prose as="div" class="mt-3">
          <p>
            Adding these to the {edgeBudgetTotal.basisPoints} bp would be arithmetic on two different yardsticks, so
            they are printed and kept out. <code>aggregate()</code> in the research workspace raises rather than summing
            across benchmarks, and this page has no code path that could.
          </p>
        </Prose>

        <div class="mt-8 max-w-measure border-t border-rule pt-5">
          <h3 class={H3}>
            The behaviour gap — {versusAverageInvestor.edgeBp} bp against {AVERAGE_INVESTOR}
          </h3>
          <p class="mt-3 text-ink">
            The gap is measured against the dollar-weighted experience of the average investor in the same fund. The
            budget above is measured against your own counterfactual. Those are two different benchmarks, so the two
            figures do not combine in either direction.
          </p>
          <p class="mt-3 text-ink">
            There is also nothing left in it for the reader this site describes. For a lump sum held throughout, the
            internal rate of return <em>is</em> the geometric return, so the gap is exactly zero — not small, not noisy,
            identically zero. Somebody already holding broad index funds and not trading has already collected all of
            it, and "not trading" cannot be a line in a budget whose own arithmetic sets it to zero. Four pages in this
            repository once described not trading as part of the {edgeBudgetTotal.basisPoints} bp. They were wrong, and
            this is the correction.
          </p>
          <p class="mt-3 text-ink-muted">{versusAverageInvestor.note}</p>
          <p class="mt-3 flex flex-wrap items-baseline gap-x-4 gap-y-1">
            <span data-numeric class="text-sm text-ink-muted">
              {versusAverageInvestor.edgeBp} bp against {versusAverageInvestor.trackingErrorBp} bp of tracking error ·
              P(ahead at 30 years) = {versusAverageInvestor.probability30yr}
            </span>
            <SourceLink citation={versusAverageInvestor.source} prefix />
          </p>
        </div>

        <div class="mt-10 flex flex-col gap-8">
          <For each={otherBenchmarkLines}>{(line) => <LineDetail line={line} />}</For>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="honest" class="mt-16 border-t-2 border-rule-strong pt-10">
        <h2 id="honest" class={H2}>
          The honest comparison
        </h2>

        <div class="mt-6 grid gap-6 sm:grid-cols-3">
          <Figure label="Whole budget vs a cheap index" value={String(versusIndex.edgeBp)} unit="bp/yr" size="lg" />
          <Figure label="Tracking error" value={String(versusIndex.trackingErrorBp)} unit="bp/yr" size="lg" />
          <Figure
            label="P(ahead after 30 years)"
            value={String(versusIndex.probability30yr)}
            size="lg"
            source={versusIndex.source}
          />
        </div>

        <Prose as="div" class="mt-8">
          <p>
            That is the whole budget — cost, tax, placement, lot discipline, a factor tilt and a rebalancing policy —
            measured against a cheap index instead of against the portfolio you would otherwise have owned.{" "}
            {versusIndex.edgeBp} bp against {versusIndex.trackingErrorBp} bp of tracking error is a{" "}
            {versusIndex.probability30yr} probability of being ahead after thirty years, which is close enough to a coin
            flip that thirty years of experience would not settle it.
          </p>
          <p>{versusIndex.note}</p>
          <p>
            Both numbers are true at once, and they are true of the same portfolio. The {edgeBudgetTotal.basisPoints} bp
            is large and near-certain because of what it is measured against. Change the benchmark and it collapses.
            Nothing on this page beats an index, and no page here claims to.
          </p>
        </Prose>
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="assumptions" class="mt-16">
        <h2 id="assumptions" class={H2}>
          What the whole budget assumes
        </h2>
        <p class="mt-2 max-w-measure text-ink-muted">
          Each of these fails in a direction that mostly reduces the measured advantage. The constant-rate assumption is
          the one that cuts both ways.
        </p>
        <ul class="mt-5 flex max-w-measure list-disc flex-col gap-2 pl-5 text-ink-muted marker:text-ink-faint">
          <For each={budgetAssumptions}>{(assumption) => <li>{assumption}</li>}</For>
        </ul>

        <h3 class={`${H3} mt-12`}>Priced, and left out on purpose</h3>
        <p class="mt-2 max-w-measure text-ink-muted">
          Five levers were sized and then refused. A lever whose sign depends on a forecast cannot enter a contractual
          budget however good the mechanism looks.
        </p>
        <dl class="mt-6 flex max-w-measure flex-col gap-5">
          <For each={notBooked}>
            {(lever) => (
              <div class="border-t border-rule pt-4">
                <dt class={H3}>{lever.label}</dt>
                <dd class="mt-2 text-ink-muted">
                  {lever.reason} <SourceLink citation={lever.source} prefix />
                </dd>
              </div>
            )}
          </For>
        </dl>
      </section>
    </>
  );
}
