import { Title } from "@solidjs/meta";
import { A } from "@solidjs/router";
import { For } from "solid-js";
import { Callout } from "~/components/Callout";
import { DataTable } from "~/components/DataTable";
import { PageHeader } from "~/components/PageHeader";
import { Prose } from "~/components/Prose";
import { SourceLink } from "~/components/SourceLink";
import {
  contractualRows,
  decidingComparison,
  formulas,
  managedFuturesCases,
  smallValueCorners,
  smallValueReading,
  upperBoundWarning,
} from "~/content/confidence";
import { edgeBudgetTotal } from "~/content/edgeBudget";
import { experiments } from "~/content/experiments";
import { factorPremia, sleeves } from "~/content/sleeves";
import type { Citation, KeyNumber } from "~/content/types";
import { CORPUS_AS_OF, NAV_ITEMS } from "~/lib/nav";

/**
 * The front page.
 *
 * Every figure below is read from `src/content/`. Nothing is formatted on the way
 * out except a probability, which is a plain number in the content layer rather
 * than a printed string, and is rendered at the full precision it is held at.
 */

function requireById<T extends { readonly id: string }>(rows: readonly T[], id: string): T {
  const row = rows.find((candidate) => candidate.id === id);
  if (row === undefined) {
    throw new Error(`content record "${id}" is missing; a page may not substitute a number for it`);
  }
  return row;
}

function requireKeyNumber(experimentId: string, label: string): KeyNumber {
  const found = requireById(experiments, experimentId).keyNumbers.find((number) => number.label === label);
  if (found === undefined) {
    throw new Error(`experiment "${experimentId}" no longer records "${label}"`);
  }
  return found;
}

/**
 * `decidingComparison` carries no probability, so each of its rows is joined to the
 * record that does. The join matches on edge *and* tracking error rather than on an
 * id, and throws when no record matches, so it fails loudly rather than quietly
 * pairing the wrong line if either module moves.
 */
function probabilityAtThirtyYears(row: (typeof decidingComparison)[number]): number {
  const candidates = [
    ...contractualRows.map((r) => ({ edgeBp: r.edgeBp, te: r.trackingErrorBp, p: r.probability30yr })),
    ...smallValueCorners.map((r) => ({ edgeBp: r.netEdgeBp, te: r.trackingErrorBp, p: r.probability30yr })),
    ...managedFuturesCases.map((r) => ({ edgeBp: r.netEdgeBp, te: r.trackingErrorBp, p: r.probability30yr })),
  ];
  const match = candidates.find((c) => c.edgeBp === row.edgeBp && c.te === row.trackingErrorBp && c.p !== undefined);
  if (match?.p === undefined) {
    throw new Error(`no 30-year probability is recorded for a ${row.edgeBp} bp / ${row.trackingErrorBp} bp line`);
  }
  return match.p;
}

const cheapIndex = requireById(contractualRows, "vs-cheap-index");
const momentum = requireById(factorPremia, "umd");
const momentumCost = requireKeyNumber("exp-006-regional-momentum", "Assumed cost of the academic construction");
const capture = requireKeyNumber("exp-007-longonly-capture", "Size-neutral value capture");
const captureSpread = requireKeyNumber("exp-007-longonly-capture", "Spread across five defensible benchmarks");
const taxDrag = requireKeyNumber("exp-008-managed-futures-products", "Distribution tax drag");
const smallValue = requireById(sleeves, "vbr-small-value");
const trend = requireById(sleeves, "dbmf-managed-futures");
const exploratoryProducts = sleeves.filter((sleeve) => sleeve.status === "exploratory").length;

/** The module that refuses the sum, not a page describing it. */
const refusesToSum: Citation = {
  label: "studies/outperformance_horizon.py",
  docPath: formulas.implementation,
};

const onwardLinks: Readonly<Record<string, string>> = {
  "/portfolio": "The construction itself, fund by fund, and the one decision the evidence refuses to make for you.",
  "/edge-budget":
    "Every line of the contractual budget, what each needs to be true, and the lines subtracted rather than added.",
  "/placement":
    "Which account each holding belongs in, computed from your own bracket rather than asserted from a rule.",
  "/confidence":
    "How long each edge takes to become visible, and why tracking error rather than edge size decides that.",
  "/evidence": "Every experiment, the status it was given, and the counter-evidence that travels with it.",
  "/concepts": "The vocabulary, defined once: capture fraction, tracking error, certainty class, detection threshold.",
  "/method": "How a result earns a status here, what the ledger records, and where the machinery is currently broken.",
};

export default function StartHere() {
  return (
    <>
      <Title>Start here — Portfolio Edge</Title>

      <PageHeader
        title="You probably can’t beat the index. You can almost certainly beat yourself."
        standfirst="Nine experiment families with a synthesis behind them, two more run and not yet written up, a specification frozen before each one of them ran, and a ledger that records the failures too. This is what came out, including the parts that argue against the interesting answer."
        lastChecked={CORPUS_AS_OF}
      />

      <section aria-labelledby="two-benchmarks">
        <Prose>
          <h2 id="two-benchmarks">Two benchmarks, and why the difference is the whole game</h2>
          <p>
            There are two different things hiding inside “beat the market”. Most investing advice never says which one
            it means.
          </p>
          <p>
            <strong>The index.</strong> A cheap, broad, fully invested fund. Beating it is hard, and everything measured
            here agrees. Add up every honest edge in this repository and you get about{" "}
            <span data-numeric>{cheapIndex.edgeBp}</span> bp a year against{" "}
            <span data-numeric>{cheapIndex.trackingErrorBp}</span> bp of tracking error — a{" "}
            <span data-numeric>{cheapIndex.probability30yr}</span> probability of being ahead after thirty years. That
            is a coin flip with a slight lean, and it is the honest answer.
          </p>
          <p>
            <strong>The portfolio you’d otherwise have owned.</strong> The active funds, the wrong account, the default
            FIFO lots, the turnover. Beating that is worth about <span data-numeric>{edgeBudgetTotal.basisPoints}</span>{" "}
            bp a year, and it is near-certain, because it is bought with arithmetic and tax law instead of forecasts. It
            reaches 99% confidence in {edgeBudgetTotal.ninetyNinePercentConfidence}.
          </p>
          <p>
            Those two numbers get added together all the time. They can’t be. They are measured against different
            things, and the code that computes them refuses to sum across benchmarks for exactly that reason —{" "}
            <SourceLink citation={refusesToSum} />.
          </p>
        </Prose>

        <Callout variant="caveat" label="What is wrong with the smaller number">
          <p>{cheapIndex.note}</p>
        </Callout>
      </section>

      <section aria-labelledby="comparison">
        <Prose>
          <h2 id="comparison">The comparison that decides what to work on</h2>
        </Prose>

        <DataTable
          class="mt-8"
          caption="Three candidate lines: what each is worth, and how long it takes to prove"
          columns={[
            { key: "label", header: "Line", rowHeader: true, cell: (row) => row.label },
            { key: "edge", header: "Edge, bp/yr", numeric: true, cell: (row) => row.edgeBp },
            { key: "te", header: "Tracking error, bp/yr", numeric: true, cell: (row) => row.trackingErrorBp },
            {
              key: "probability",
              header: "P(ahead at 30 yr)",
              numeric: true,
              cell: (row) => probabilityAtThirtyYears(row).toFixed(3),
            },
            { key: "confident", header: "99% confident in", cell: (row) => row.ninetyNinePercentAt },
          ]}
          rows={decidingComparison}
          footnote={
            <>
              The tilt is {smallValue.ticker} and the trend sleeve is {trend.ticker}. {upperBoundWarning} The first
              row’s probability is ~1.00 rather than exactly 1.{" "}
              <SourceLink citation={smallValueReading.source} prefix />
            </>
          }
        />

        <Prose class="mt-8">
          <p>
            The point is not that tilts are worthless. It is that{" "}
            <strong>tracking error, not edge size, decides whether a lifetime is long enough to tell.</strong> The
            horizon scales with the square of tracking error over edge, so halving the edge quadruples the wait.
          </p>
          <p>
            Every probability in that table is an <strong>upper bound</strong>. The arithmetic treats the edge as a
            known quantity, which removes the largest source of uncertainty there is.
          </p>
        </Prose>
      </section>

      <section aria-labelledby="what-was-found">
        <Prose>
          <h2 id="what-was-found">What the research actually found</h2>
          <p>Four things worth knowing before anything else.</p>
          <p>
            <strong>The reliable money is in decisions, not predictions.</strong> Fund choice, account placement, lot
            method and not trading. All four are contractual — their sign is known in advance — and together they are
            larger than any tilt measured here.
          </p>
          <p>
            <strong>Some tilts are real and still not worth much to you.</strong> Momentum has the largest gross premium
            in the whole repository, <span data-numeric>{momentum.pooledPremium}</span> pooled across three regions,{" "}
            <span data-numeric>{momentum.pooledInterval}</span>. It is still excluded, because its academic construction
            rebalances monthly at an assumed cost of{" "}
            <span data-numeric>
              {momentumCost.value} {momentumCost.unit}
            </span>
            , its three regions crash together, and the entire retail shelf is one fund that loses to a cheap three-fund
            combination.
          </p>
          <p>
            <strong>
              A long-only tilt delivers about half of the premium it advertises, and that half is counted once.
            </strong>{" "}
            The measured capture fraction is <span data-numeric>{capture.value}</span>,{" "}
            <span data-numeric>{capture.interval}</span>, and five defensible ways to define it disagree by{" "}
            <span data-numeric>{captureSpread.value}</span>. But regress the same spread on the factors and 94% of that{" "}
            <span data-numeric>{capture.value}</span> is simply its HML coefficient, so the fraction may not multiply a
            fund's own loading. The chain is <code>weight × (loading − incumbent loading) × premium − cost</code>, and
            it carries no capture term.
          </p>
          <p>
            <strong>Where you hold something can decide its sign.</strong> The managed-futures shelf distributes{" "}
            <span data-numeric>
              {taxDrag.value} {taxDrag.unit}
            </span>{" "}
            of tax in a taxable account — {taxDrag.note}. The account is a larger controllable term than the product.
          </p>
        </Prose>
      </section>

      <section aria-labelledby="what-this-is-not">
        <Prose>
          <h2 id="what-this-is-not">What this is not</h2>
        </Prose>

        <dl class="mt-6 max-w-measure border-t border-rule">
          <div class="border-b border-rule py-4">
            <dt class="font-medium">Not advice</dt>
            <dd class="mt-1 text-ink-muted">
              It is a construction derived from measurements, for one stated reference investor: US federal, thirty-year
              horizon, contributions continuing, state tax excluded.
            </dd>
          </div>
          <div class="border-b border-rule py-4">
            <dt class="font-medium">Not a forecast</dt>
            <dd class="mt-1 text-ink-muted">No expected return for any market appears anywhere on this site.</dd>
          </div>
          <div class="border-b border-rule py-4">
            <dt class="font-medium">Not a promotion</dt>
            <dd class="mt-1 text-ink-muted">
              Nothing tested here reached <code>production-eligible</code>, or <code>walk-forward-tested</code>, or even{" "}
              <code>independently-reproduced</code>. <span data-numeric>{exploratoryProducts}</span> products are{" "}
              <code>exploratory</code>, which permits them as proxies in a later experiment and permits nothing else.
            </dd>
          </div>
          <div class="border-b border-rule py-4">
            <dt class="font-medium">Not settled</dt>
            <dd class="mt-1 text-ink-muted">
              The largest decision in your portfolio — the split between equities and bonds — is the one thing here the
              evidence cannot set for you.
            </dd>
          </div>
        </dl>
      </section>

      <section aria-labelledby="onward">
        <Prose>
          <h2 id="onward">Where to go next</h2>
        </Prose>

        <dl class="mt-6 max-w-measure">
          <For each={NAV_ITEMS.filter((item) => item.href !== "/")}>
            {(item) => (
              <div class="mt-4 first:mt-0 sm:flex sm:gap-4">
                <dt class="sm:w-40 sm:shrink-0">
                  <A href={item.href} class="link">
                    {item.label}
                  </A>
                </dt>
                <dd class="text-ink-muted">{onwardLinks[item.href] ?? ""}</dd>
              </div>
            )}
          </For>
        </dl>
      </section>
    </>
  );
}
