import { Title } from "@solidjs/meta";
import { type Component, For } from "solid-js";
import { Callout } from "~/components/Callout";
import { DataTable } from "~/components/DataTable";
import { Figure } from "~/components/Figure";
import { PageHeader } from "~/components/PageHeader";
import { Prose } from "~/components/Prose";
import { SourceLink } from "~/components/SourceLink";
import { StatusChip } from "~/components/StatusChip";
import { experiments, ledgerSummary } from "~/content/experiments";
import { whatThisIsNot } from "~/content/portfolio";
import { factorPremia, sleeves } from "~/content/sleeves";
import { type Citation, type EvidenceStatus, type KeyNumber, statusMeta } from "~/content/types";
import { CORPUS_AS_OF } from "~/lib/nav";

/**
 * How a result earns a status here.
 *
 * Every count and every figure is read from `src/content/`. The "reached here"
 * column is computed from the statuses the content layer actually carries rather
 * than asserted, so it cannot drift away from the evidence pages.
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

function requireLimit(claim: string): string {
  const found = whatThisIsNot.find((item) => item.claim === claim);
  if (found === undefined) {
    throw new Error(`the content layer no longer records the limit "${claim}"`);
  }
  return found.detail;
}

/**
 * Content strings mark a status token with backticks, the way the research pages do.
 * This renders those as real code spans rather than printing the backticks.
 */
const Ticked: Component<{ readonly text: string }> = (props) => (
  <For each={props.text.split("`")}>{(part, index) => (index() % 2 === 1 ? <code>{part}</code> : part)}</For>
);

const statusLadder = Object.keys(statusMeta) as readonly EvidenceStatus[];

/** Statuses the rendered evidence actually carries. Counted, never asserted. */
const statusesInUse = new Set<EvidenceStatus>([
  ...experiments.flatMap((item) => (item.status === null ? [] : [item.status])),
  ...sleeves.flatMap((item) => (item.status === null ? [] : [item.status])),
  ...factorPremia.flatMap((item) => (item.status === null ? [] : [item.status])),
]);

const phaseOne = requireById(experiments, "phase1-ff-reproduction");
const gatingCells = requireKeyNumber("phase1-ff-reproduction", "Gating cells that reproduce");
const hmlDeviation = requireKeyNumber("phase1-ff-reproduction", "HML standard deviation");
const rmwDeviation = requireKeyNumber("phase1-ff-reproduction", "RMW standard deviation");
const systematicBand = requireKeyNumber("phase1-ff-reproduction", "Systematic band carried downstream");
const pedestal = requireKeyNumber("exp-002-fund-exposure", "Model-misfit pedestal");
const productAudit = requireById(experiments, "exp-002-fund-exposure");
const control = requireById(sleeves, "cheap-broad-market");

const workspaceRules: Citation = {
  label: "The research workspace’s non-negotiable rules",
  docPath: "research/README.md",
};

const renderDecision: Citation = {
  label: "0007 — The application may render research findings, under four constraints",
  docPath: "docs/decisions/0007-application-may-render-research.md",
};

export default function Method() {
  return (
    <>
      <Title>Method — Portfolio Edge</Title>

      <PageHeader
        eyebrow="Method"
        title="How this decides what is real"
        standfirst="A closed vocabulary of statuses, a specification frozen before anyone sees a result, and a ledger that counts the runs that failed. Here is the machinery, and here is where it is currently broken."
        lastChecked={CORPUS_AS_OF}
      />

      <Prose>
        <p>
          If you are here to find the weak point, skip ahead. The two places this project is most exposed are{" "}
          <a href="#pedestal">the model that cannot price its own control</a> and{" "}
          <a href="#broken">the ingestion gate that never closed</a>. Both are stated in full below, with numbers.
        </p>
      </Prose>

      <section aria-labelledby="vocabulary">
        <Prose>
          <h2 id="vocabulary">Eight words, and none of them is “works”</h2>
          <p>
            Every result carries one status from a closed list. The list has no rung meaning “this is true”, and no
            result is ever summarised as working. Two of the eight are terminal verdicts rather than rungs:{" "}
            <code>rejected</code> means a test written down in advance fired, and <code>unresolved</code> means the
            window could not have seen an effect of the size it was hunting.
          </p>
        </Prose>

        <DataTable
          class="mt-8"
          caption="The status vocabulary, in ladder order, and what this site’s evidence actually carries"
          columns={[
            {
              key: "status",
              header: "Status",
              rowHeader: true,
              cell: (status) => <StatusChip status={status} />,
            },
            { key: "gloss", header: "What it means", cell: (status) => statusMeta[status].gloss },
            {
              key: "reached",
              header: "Reached here",
              cell: (status) => (statusesInUse.has(status) ? "Yes" : "No"),
            },
          ]}
          rows={statusLadder}
          footnote={
            <>
              “Reached here” is counted across the experiments, sleeves and factor premia this site renders, not
              asserted. <Ticked text={requireLimit("Not a promotion")} />
            </>
          }
        />
      </section>

      <section aria-labelledby="frozen">
        <Prose>
          <h2 id="frozen">The specification is frozen before the result is examined</h2>
          <p>
            One YAML file per experiment, committed to the repository first. It names the universe, the signal, the
            holding period, the regime expected to hurt it, the capacity, the benchmark — and the result that would
            reject it. Only then does anything run.
          </p>
          <p>
            The runner refuses a confirmatory run outright unless its specification declares five things: a benchmark, a
            primary metric, a cost model, a sample policy and a rejection rule. That refusal is code, not a checklist,
            and it has fired: one of the runs in the ledger below is a verification guard turning down its own
            experiment.
          </p>
          <p>
            Freezing the benchmark first is not ceremony. The benchmark decides the answer. Experiment 004 measured a
            trend sleeve at a large margin against a fully invested passive portfolio and at a much smaller one against
            a risk-matched comparator, and it reports the smaller number because that is the comparator its
            specification named before the data was seen.
          </p>
          <p>
            <SourceLink citation={workspaceRules} prefix />
          </p>
        </Prose>
      </section>

      <section aria-labelledby="ledger">
        <Prose>
          <h2 id="ledger">The ledger records the failures</h2>
          <p>
            Every attempted run is appended to <code>research/ledger.jsonl</code> — the ones that produced a result, the
            two that failed outright, and the four that were abandoned mid-flight. The reason is not tidiness. The
            effective number of trials behind a finding cannot be reconstructed after the fact, so the record has to
            exist before the first backtest rather than be assembled after the interesting one.
          </p>
          <p>
            As of {ledgerSummary.asOf}: <span data-numeric>{ledgerSummary.entries}</span> entries,{" "}
            <span data-numeric>{ledgerSummary.runs}</span> runs,{" "}
            <span data-numeric>{ledgerSummary.distinctSpecifications}</span> distinct specifications, across{" "}
            <span data-numeric>{ledgerSummary.experimentFamilies}</span> experiment families.{" "}
            <span data-numeric>{ledgerSummary.runsRecordingResultsViewed}</span> runs recorded that a result was viewed,
            and <span data-numeric>{ledgerSummary.runsConsumingTheFinalHoldout}</span> consumed the final holdout.
          </p>
          <p>
            The two counts are not interchangeable, and the smaller one is the honest one.{" "}
            <strong>
              A trial count starts from the <span data-numeric>{ledgerSummary.distinctSpecifications}</span>{" "}
              specifications, not the <span data-numeric>{ledgerSummary.runs}</span> executions
            </strong>{" "}
            — running one specification four times is one hypothesis tested four times, not four hypotheses. Four of the{" "}
            <code>rejected</code> rows below are a single specification hash.
          </p>
        </Prose>

        <DataTable
          class="mt-8"
          caption="Ledgered runs by terminal outcome"
          columns={[
            {
              key: "status",
              header: "Outcome",
              rowHeader: true,
              cell: (row) => <StatusChip status={row.status} />,
            },
            { key: "runs", header: "Runs", numeric: true, cell: (row) => row.runs },
            { key: "which", header: "Which", cell: (row) => row.which },
          ]}
          rows={ledgerSummary.terminalOutcomes}
          footnote={
            <>
              A further <span data-numeric>{ledgerSummary.noTerminalStatus.runs}</span> runs reached no terminal status:{" "}
              {ledgerSummary.noTerminalStatus.which}. <SourceLink citation={ledgerSummary.source} prefix />
            </>
          }
        />

        <Callout variant="caveat" label="What these counts do and do not cover">
          <p>{ledgerSummary.note}</p>
        </Callout>
      </section>

      <section aria-labelledby="comparators">
        <Prose>
          <h2 id="comparators">Four comparators, on every result</h2>
          <p>
            The control is a cheap, broad, long-only, fully invested market portfolio, and every candidate is measured
            against it. A result that does not report all four of the following is not reportable.
          </p>
        </Prose>

        <dl class="mt-6 max-w-measure border-t border-rule">
          <div class="border-b border-rule py-4">
            <dt class="font-medium">The benchmark, named, and its certainty class</dt>
            <dd class="mt-1 text-ink-muted">
              A stated index, the investor’s own counterfactual, or the average investor — and whether the line is an
              accounting identity or a bet. A number missing either is not reportable at all.
            </dd>
          </div>
          <div class="border-b border-rule py-4">
            <dt class="font-medium">A cheap combination, not the market alone</dt>
            <dd class="mt-1 text-ink-muted">
              Whenever the candidate is a product or a tilt, it faces a long-only mix of cheap broad funds fitted to its
              own exposures. That mix is fitted in sample, so it is a look-ahead best case for the combination and a
              deliberately hard test — which is why such a rejection reads as “four cheap funds beat this over these
              months”, never as “this product is badly run”.
            </dd>
          </div>
          <div class="border-b border-rule py-4">
            <dt class="font-medium">A risk match, not the fully invested portfolio</dt>
            <dd class="mt-1 text-ink-muted">
              Whenever the candidate changes portfolio risk. Otherwise de-risking is scored as skill: protected excess
              return looks like protection until an equity-and-cash mix earns the same thing.
            </dd>
          </div>
          <div class="py-4">
            <dt class="font-medium">The model-misfit pedestal</dt>
            <dd class="mt-1 text-ink-muted">
              Whenever an alpha is quoted, the same model’s alpha on a total-market fund over the identical window. The
              next section is what that pedestal turned out to be.
            </dd>
          </div>
        </dl>

        <Prose class="mt-6">
          <p>
            <SourceLink citation={control.source} prefix />
          </p>
        </Prose>
      </section>

      <section aria-labelledby="costs">
        <Prose>
          <h2 id="costs">Costs change the trade, not the total</h2>
          <p>
            A cost model is not a haircut applied to the answer at the end. It alters the trading rule itself, inside
            the simulation, so a strategy that only works when it trades cheaply stops trading and reports the
            consequence. Subtracting costs afterwards lets a rule keep making trades it could never have afforded.
          </p>
          <p>
            The same applies in time. No observation may be used before its availability timestamp, so a rule cannot act
            on an accounting figure that had not been filed yet, or a factor value computed from data published later.
            Raw bytes are hashed before anything parses them, and a parser is never the only record of what was
            downloaded.
          </p>
          <p>
            None of that makes a number point-in-time by itself. A hash proves which file was used. It does not prove
            the file represents what was available at the time.
          </p>
        </Prose>
      </section>

      <section aria-labelledby="pedestal">
        <Prose>
          <h2 id="pedestal">The model does not span the control</h2>
          <p>
            This is the most uncomfortable single fact on the site, and it undercuts every alpha measured here,
            including the ones that flatter the argument.
          </p>
        </Prose>

        <div class="mt-8 max-w-measure border-y border-rule py-6">
          <Figure {...pedestal} size="lg" tone="negative" source={productAudit.source} />
        </div>

        <Prose class="mt-8">
          <p>{requireLimit("Not free of model risk")}</p>
          <p>
            So an alpha of zero in this repository is not a fund matching the market. It is a fund beating the pedestal
            by more than half a percentage point a year. Reading any alpha here as a distance from zero overstates it by
            exactly that amount, and the sign of a small alpha can flip on it.
          </p>
        </Prose>
      </section>

      <section aria-labelledby="broken">
        <Prose>
          <h2 id="broken">What is still broken</h2>
          <p>
            The gate everything else is built on has not closed. Phase 1 asked whether the download, parse and summary
            path reproduces a precisely identified published table. Its answer is <code>unresolved</code>, and it has
            stayed that way.
          </p>
          <p>{phaseOne.verdict}</p>
        </Prose>

        <div class="mt-8 grid max-w-measure gap-8 border-y border-rule py-6 sm:grid-cols-2">
          <Figure {...gatingCells} source={phaseOne.source} />
          <Figure {...systematicBand} source={phaseOne.source} />
          <Figure {...hmlDeviation} source={phaseOne.source} />
          <Figure {...rmwDeviation} source={phaseOne.source} />
        </div>

        <Prose class="mt-8">
          <p>
            Anything that divides by one of those two volatilities inherits the band: a Sharpe ratio, a
            volatility-scaled sleeve, a risk-parity weight, a covariance matrix, a Kelly fraction. It is systematic, not
            sampling error, and more data will not shrink it.
          </p>
          <p>
            <Ticked text={requireLimit("Not vintage-stable")} />
          </p>
          <p>
            A series with no measured band is not a series with a small one. It is a series nobody has checked, which is
            the weaker position of the two. All three momentum files sit in that group, and momentum carries the largest
            gross premium anywhere in this repository — so the least-verified series sits underneath the most attractive
            number.
          </p>
        </Prose>

        <Callout variant="open-question" label="What would settle it">
          <ul class="list-disc pl-5">
            <For each={phaseOne.whatWouldChangeIt}>{(item) => <li>{item}</li>}</For>
          </ul>
        </Callout>
      </section>

      <section aria-labelledby="what-the-site-does">
        <Prose>
          <h2 id="what-the-site-does">What this site is allowed to do with all that</h2>
          <p>
            A number lifted out of the research loses its status, its interval, its <code>as of</code> date and its
            counter-evidence, and what survives the trip is a confident-sounding figure with none of the machinery that
            made it honest. So four constraints hold everywhere on this site: every displayable fact lives in one typed
            content layer and a figure hardcoded in a page is a defect; status, date, interval and source travel with
            every number; the certainty class governs the wording and the benchmark governs what may be added to what;
            and any arithmetic the site runs is a port of a research module, tested against fixtures that module
            generates. <SourceLink citation={renderDecision} />
          </p>
        </Prose>
      </section>

      <section aria-labelledby="what-the-site-computes">
        <Prose>
          <h2 id="what-the-site-computes">What the site computes, and what it refuses to</h2>
          <p>
            Three calculations run in the browser. Each is a port of a research module and each is tested against
            fixtures that module generates, so a study whose numbers move breaks a client test.
          </p>
          <ul>
            <li>
              <strong>The probability of being ahead.</strong> <code>P = Φ(e√T / s)</code> for an edge <code>e</code>, a
              tracking error <code>s</code> and a horizon <code>T</code> in years, inverted to give the horizon at which
              any confidence is reached: <code>T = (z·s/e)²</code>.
            </li>
            <li>
              <strong>The value-tilt chain.</strong>{" "}
              <code>weight × (fund loading − incumbent loading) × premium − incremental cost</code>. Three terms. The
              module raises rather than accepting a capture fraction, because a capture fraction is itself a loading and
              the product would discount the same exposure twice. Alongside the edge it returns the substitution's
              effect on portfolio variance, so the figure that decides is geometric growth rather than an arithmetic
              average.
            </li>
            <li>
              <strong>The relative path.</strong> The same model as the first, simulated instead of solved: relative
              wealth as a random walk with drift, log-normal in the ratio, from a fixed seed. The share of paths ahead
              at the horizon reproduces the closed form rather than competing with it.
            </li>
          </ul>
          <p>
            <strong>What it refuses.</strong> There is no backtest anywhere on this site. No total-return source here is
            research-grade, no per-fund exposure vector is committed, and the redistribution terms on the public factor
            libraries were never established. A growth chart built on any of those would be the most persuasive object
            on the site and the least defensible one. The lab will happily run history the reader supplies, and it ships
            none.
          </p>
        </Prose>
      </section>
    </>
  );
}
