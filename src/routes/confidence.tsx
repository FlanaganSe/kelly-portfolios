import { Title } from "@solidjs/meta";
import { createMemo, createSignal, For, Show } from "solid-js";
import { Callout } from "~/components/Callout";
import { DataTable } from "~/components/DataTable";
import { Figure } from "~/components/Figure";
import { NumberInput } from "~/components/NumberInput";
import {
  formatBp,
  formatProbability,
  OutperformanceChart,
  type OutperformanceSeries,
} from "~/components/OutperformanceChart";
import { PageHeader } from "~/components/PageHeader";
import { Prose } from "~/components/Prose";
import { Slider } from "~/components/Slider";
import { SourceLink } from "~/components/SourceLink";
import {
  confidenceAsOf,
  contractualRows,
  decidingComparison,
  decidingComparisonReading,
  demonstrability,
  formulas,
  managedFuturesCases,
  managedFuturesReading,
  smallValueCorners,
  smallValueReading,
  upperBoundWarning,
} from "~/content/confidence";
import { clamp } from "~/lib/format";
import { detectableEdgeBp, horizonForConfidence, probabilityOfOutperformance } from "~/lib/horizon";

/**
 * The one idea the rest of the site rests on: tracking error, not edge size, decides
 * whether a lifetime is long enough to tell.
 *
 * Every figure comes from `src/content/confidence.ts` and every calculation from
 * `src/lib/horizon.ts`. Nothing on this page is computed twice or typed twice.
 */

const H2 = "font-sans text-xl font-semibold tracking-[-0.015em] text-ink";

const EDGE_MIN = -50;
const EDGE_MAX = 250;
const TE_MIN = 0;
const TE_MAX = 500;
const HORIZON_MIN = 1;
const HORIZON_MAX = 50;

/** Gutter text for the chart. Display copy only — the numbers all come from content. */
const CHART_LABELS: Readonly<Record<string, { readonly label: string; readonly abbr: string }>> = {
  contractual: { label: "Contractual budget", abbr: "Contractual" },
  "small-value-best-case": { label: "Small-value tilt, best", abbr: "Small-value" },
  "trend-best-case": { label: "Trend sleeve, best", abbr: "Trend" },
  "vs-cheap-index": { label: "Whole budget vs index", abbr: "Vs index" },
};

const gutter = (id: string, fallback: string) => CHART_LABELS[id] ?? { label: fallback, abbr: fallback };

/**
 * The four curves. Three are the comparison that closes the page; the fourth is the
 * honest budget measured against a cheap index, which is the flattest line here.
 */
const chartSeries: readonly OutperformanceSeries[] = [
  ...decidingComparison.map((row): OutperformanceSeries => {
    const text = gutter(row.id, row.label);
    return {
      id: row.id,
      label: text.label,
      abbr: text.abbr,
      fullLabel: row.label,
      edgeBp: row.edgeBp,
      trackingErrorBp: row.trackingErrorBp,
      kind: row.id === "contractual" ? "contractual" : "probabilistic",
    };
  }),
  ...contractualRows
    .filter((row) => row.id === "vs-cheap-index")
    .map((row): OutperformanceSeries => {
      const text = gutter(row.id, row.label);
      return {
        id: row.id,
        label: text.label,
        abbr: text.abbr,
        fullLabel: row.label,
        edgeBp: row.edgeBp,
        trackingErrorBp: row.trackingErrorBp,
        kind: "probabilistic",
      };
    }),
];

/** The sliders open on a real research line, so the live curve starts somewhere honest. */
const OPENING_CASE = managedFuturesCases.find((row) => row.id === "post-pub-taxable") ?? managedFuturesCases[0];

/** A screen reader gets this instead of the picture, so it has to carry the finding. */
function buildAriaLabel(): string {
  const sentences = chartSeries.map((series) => {
    const ten = probabilityOfOutperformance({
      edgeBp: series.edgeBp,
      trackingErrorBp: series.trackingErrorBp,
      horizonYears: 10,
    });
    const fifty = probabilityOfOutperformance({
      edgeBp: series.edgeBp,
      trackingErrorBp: series.trackingErrorBp,
      horizonYears: 50,
    });
    return `${series.fullLabel}, ${formatBp(series.edgeBp)} bp against ${formatBp(
      series.trackingErrorBp
    )} bp of tracking error, is at ${formatProbability(ten, series.trackingErrorBp)} after ten years and ${formatProbability(
      fifty,
      series.trackingErrorBp
    )} after fifty.`;
  });
  return `The chance of being ahead of the benchmark, plotted against a horizon of zero to fifty years, one line per edge and tracking-error pair. ${sentences.join(
    " "
  )} The contractual line reaches the top of the plot inside a year. The three probabilistic lines are still close to a coin flip after fifty.`;
}

/** Years until a confidence level, or `null` where there is no such year. */
function yearsToConfidence(edgeBp: number, trackingErrorBp: number, confidence: number): number | null {
  try {
    return horizonForConfidence({ edgeBp, trackingErrorBp, confidence });
  } catch {
    // `edgeBp <= 0`. A persistent loss never becomes an outperformance.
    return null;
  }
}

function formatYears(years: number): string {
  if (years === 0) return "Immediately";
  if (years < 1 / 12) return `${Math.max(1, Math.round(years * 365))} days`;
  if (years < 1) return `${Math.round(years * 12)} months`;
  if (years < 10) return `${years.toFixed(1)} years`;
  if (years < 1000) return `${Math.round(years).toLocaleString("en-US")} years`;
  if (years < 1e9) return `${Number(years.toPrecision(2)).toLocaleString("en-US")} years`;
  return "Longer than the universe has existed";
}

function glossYears(years: number | null): string {
  if (years === null) return "A negative edge never turns into an outperformance. Waiting is not a plan.";
  if (years === 0) return "No tracking error, so there is nothing to wait for. The saving is banked as it is made.";
  if (years < 1) return "Inside a year.";
  if (years <= 40) return "Inside a working life, if the estimate holds.";
  if (years <= 120) return "Longer than a working life.";
  if (years <= 1200) return "Not in your lifetime.";
  return "Not in your lifetime, or your civilisation's.";
}

const percent = (value: number) => `${(value * 100).toFixed(1)}%`;

export default function Confidence() {
  const opening = OPENING_CASE;
  const [edgeBp, setEdgeBp] = createSignal(opening?.netEdgeBp ?? 0);
  const [trackingErrorBp, setTrackingErrorBp] = createSignal(opening?.trackingErrorBp ?? 100);
  const [horizonYears, setHorizonYears] = createSignal(30);

  const live = createMemo<OutperformanceSeries>(() => ({
    id: "live",
    label: "Your inputs",
    abbr: "You",
    fullLabel: "Your inputs",
    edgeBp: edgeBp(),
    trackingErrorBp: trackingErrorBp(),
    kind: "live",
  }));

  const probability = createMemo(() =>
    probabilityOfOutperformance({
      edgeBp: edgeBp(),
      trackingErrorBp: trackingErrorBp(),
      horizonYears: horizonYears(),
    })
  );

  const ninety = createMemo(() => yearsToConfidence(edgeBp(), trackingErrorBp(), 0.9));
  const ninetyNine = createMemo(() => yearsToConfidence(edgeBp(), trackingErrorBp(), 0.99));
  const detectable = createMemo(() =>
    detectableEdgeBp({ trackingErrorBp: trackingErrorBp(), horizonYears: horizonYears(), confidence: 0.9 })
  );

  const zeroTrackingError = () => trackingErrorBp() === 0;
  const negativeEdge = () => edgeBp() < 0;

  const load = (nextEdgeBp: number, nextTrackingErrorBp: number) => {
    setEdgeBp(clamp(nextEdgeBp, EDGE_MIN, EDGE_MAX));
    setTrackingErrorBp(clamp(nextTrackingErrorBp, TE_MIN, TE_MAX));
    document.getElementById("calculator")?.scrollIntoView({ block: "start" });
  };

  /** One click puts a research line into the sliders. */
  const Load = (props: { readonly edgeBp: number; readonly trackingErrorBp: number; readonly describe: string }) => {
    const loaded = () => edgeBp() === props.edgeBp && trackingErrorBp() === props.trackingErrorBp;
    return (
      <button
        type="button"
        aria-pressed={loaded()}
        aria-label={`Load ${props.describe} into the calculator`}
        onClick={() => load(props.edgeBp, props.trackingErrorBp)}
        class="rounded-[3px] border border-rule-strong px-2 py-1 text-xs whitespace-nowrap text-ink-muted transition-colors hover:border-ink-faint hover:text-ink aria-pressed:border-accent aria-pressed:font-medium aria-pressed:text-accent"
      >
        {loaded() ? "Loaded" : "Load"}
      </button>
    );
  };

  return (
    <>
      <Title>Confidence — Portfolio Edge</Title>
      <PageHeader
        title="Confidence"
        standfirst="How long it takes before a result could be told apart from luck, and why that answer is decided by tracking error rather than by the size of the edge."
        lastChecked={confidenceAsOf}
      />

      <Prose as="section">
        <p>
          Two portfolios drift apart at a rate you can name. One earns <code>e</code> more a year than the other, and
          the gap between them wanders with a standard deviation of <code>s</code> a year. That second number is the
          tracking error, and it is a property of the pair, not of either portfolio on its own.
        </p>
        <p>
          Ask how long before the better portfolio is visibly ahead, and the answer barely involves <code>e</code>.
        </p>
      </Prose>

      <div class="mt-6 max-w-measure border-l-2 border-rule-strong pl-4">
        <p data-numeric class="font-mono text-sm text-ink">
          {formulas.probability}
        </p>
        <p data-numeric class="mt-2 font-mono text-sm text-ink">
          {formulas.horizon}
        </p>
        <p class="mt-3 text-sm text-ink-muted">{formulas.variables}</p>
      </div>

      <Prose as="section" class="mt-6">
        <p>
          The first line says the chance you are ahead is the normal curve evaluated at{" "}
          <code class="whitespace-nowrap">e sqrt(T) / s</code>: your edge, scaled by the square root of time, measured
          in units of how much the two portfolios wander apart.
        </p>
        <p>
          The second line is the one to keep. <strong>The ratio is squared.</strong> Halve the edge and you quadruple
          the wait. Double the tracking error and you quadruple it again. Nothing about the arithmetic is subtle, and
          nothing about it can be argued with — it is the definition of a random walk with drift, not a finding.
        </p>
        <p>{formulas.theLesson}</p>
        <p>
          So a big gross premium tells you almost nothing on its own. A small one, harvested against a benchmark you
          barely deviate from, can be settled in months. That is the whole page, and the chart below is the same
          sentence drawn.
        </p>
      </Prose>

      <p class="mt-4">
        <SourceLink citation={formulas.source} prefix />
      </p>

      <section aria-labelledby="chart-heading" id="chart" class="mt-14 scroll-mt-6">
        <h2 id="chart-heading" class={H2}>
          Four lines, fifty years
        </h2>
        <p class="mt-2 max-w-measure text-ink-muted">
          Each curve is one pairing of edge and tracking error. The pairing is printed beside the name, because the
          pairing is what decides the shape.
        </p>

        <div class="mt-6">
          <OutperformanceChart
            series={chartSeries}
            live={live()}
            horizonYears={horizonYears()}
            ariaLabel={buildAriaLabel()}
            tableCaption="Chance of being ahead of the benchmark, by horizon"
            footnote={upperBoundWarning}
            caption={
              <>
                The contractual line is at the top of the plot before the first tick. The three bets are still hugging
                the coin flip at fifty years. Distance across the x-axis is the square root of time, because that is the
                variable the formula uses; the uneven tick spacing is what a squared law looks like when you flatten it.
              </>
            }
          />
        </div>

        <Callout variant="caveat" label="Upper bound">
          <p>{upperBoundWarning}</p>
        </Callout>
      </section>

      <section aria-labelledby="calculator-heading" id="calculator" class="mt-14 scroll-mt-6">
        <h2 id="calculator-heading" class={H2}>
          Your own numbers
        </h2>
        <p class="mt-2 max-w-measure text-ink-muted">
          Drag either control and the accent line above moves with it. The presets underneath load the research lines.
        </p>

        <div class="mt-6 grid gap-8 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)]">
          <div class="flex flex-col gap-6">
            <Slider
              label="Edge"
              value={edgeBp()}
              onInput={setEdgeBp}
              min={EDGE_MIN}
              max={EDGE_MAX}
              step={0.1}
              format={formatBp}
              unit="bp/yr"
              showBounds
              hint="How much more you earn a year than the thing you are being compared with. Negative is allowed, and one of the small-value corners is."
            />
            <Slider
              label="Tracking error"
              value={trackingErrorBp()}
              onInput={setTrackingErrorBp}
              min={TE_MIN}
              max={TE_MAX}
              step={0.1}
              format={formatBp}
              unit="bp/yr"
              showBounds
              hint="How far the two of you wander apart in a year. A cheaper share class of the same fund is near zero; a factor tilt against a broad index is several hundred."
            />
            <NumberInput
              label="Horizon"
              value={horizonYears()}
              onInput={(value) => setHorizonYears(clamp(value, HORIZON_MIN, HORIZON_MAX))}
              min={HORIZON_MIN}
              max={HORIZON_MAX}
              step={1}
              unit="years"
              hint="Marked on the chart with a vertical rule."
            />
          </div>

          <div>
            <div class="grid gap-6 border-y border-rule py-6 sm:grid-cols-2">
              <Figure
                label={`Chance you are ahead after ${horizonYears()} years`}
                value={formatProbability(probability(), trackingErrorBp())}
                size="lg"
                tone={probability() < 0.5 ? "negative" : "neutral"}
                note={
                  zeroTrackingError() && edgeBp() > 0
                    ? "Exactly one. With no tracking error there is no path to be unlucky on, so a positive edge is realised at every horizon. This is the contractual case, and it is why cost reduction dominates the budget."
                    : undefined
                }
              />
              <Figure
                label="Smallest edge you could demonstrate over that horizon"
                value={formatBp(Number(detectable().toFixed(1)))}
                unit="bp/yr"
                size="lg"
                note="At 90% confidence, at your tracking error. Read it as the bar any claim would have to clear before your own experience could settle it."
              />
              <Figure
                label="Years to 90% confidence"
                value={ninety() === null ? "Never" : formatYears(ninety() ?? 0)}
                size="lg"
                tone={ninety() === null ? "negative" : "neutral"}
                note={glossYears(ninety())}
              />
              <Figure
                label="Years to 99% confidence"
                value={ninetyNine() === null ? "Never" : formatYears(ninetyNine() ?? 0)}
                size="lg"
                tone={ninetyNine() === null ? "negative" : "neutral"}
                note={glossYears(ninetyNine())}
              />
            </div>

            <Show when={negativeEdge()}>
              <p class="mt-4 max-w-measure text-sm text-ink-muted">
                Your edge is negative, so there is no year at which you are 90% likely to be ahead, and no year at which
                you are 99% likely. The two readouts say "never" rather than a large number, because a persistent loss
                does not become an outperformance if you sit with it for long enough.
              </p>
            </Show>

            <Show when={zeroTrackingError()}>
              <p class="mt-4 max-w-measure text-sm text-ink-muted">
                Zero tracking error is not a trick. It is a cheaper share class of the same fund, or a lot sold in the
                right order, or an account that stops taxing the same income. Nothing wanders, so nothing has to be
                waited out.
              </p>
            </Show>

            <Callout variant="caveat" label="Upper bound">
              <p>{upperBoundWarning}</p>
            </Callout>
          </div>
        </div>
      </section>

      <section aria-labelledby="lines-heading" id="lines" class="mt-14 scroll-mt-6">
        <h2 id="lines-heading" class={H2}>
          The research lines
        </h2>
        <p class="mt-2 max-w-measure text-ink-muted">
          Every row below is a measured pairing from this repository, with the benchmark it was measured against. Load
          one and the chart redraws.
        </p>

        <h3 class="mt-8 font-sans text-base font-semibold text-ink">Contractual, and the benchmarks it is not</h3>
        <p class="mt-2 max-w-measure text-ink-muted">
          The first two rows are measured against the portfolio you would otherwise have held. The last two are measured
          against something else, and the three yardsticks never add together.
        </p>
        <DataTable
          class="mt-4"
          caption="Contractual lines and the benchmarks they are measured against"
          columns={[
            { key: "line", header: "Line", rowHeader: true, cell: (row) => row.label },
            { key: "benchmark", header: "Benchmark", cell: (row) => row.benchmark },
            { key: "edge", header: "Edge bp/yr", numeric: true, cell: (row) => formatBp(row.edgeBp) },
            { key: "te", header: "Tracking error bp/yr", numeric: true, cell: (row) => formatBp(row.trackingErrorBp) },
            {
              key: "ninety",
              header: "90% at",
              numeric: true,
              cell: (row) => row.ninetyPercentAt ?? "—",
            },
            {
              key: "load",
              header: "",
              numeric: true,
              cell: (row) => <Load edgeBp={row.edgeBp} trackingErrorBp={row.trackingErrorBp} describe={row.label} />,
            },
          ]}
          rows={contractualRows}
          footnote={upperBoundWarning}
        />
        <div class="mt-4 flex max-w-measure flex-col gap-3">
          <For each={contractualRows}>
            {(row) => (
              <Show when={row.note}>
                <p class="text-sm text-ink-muted">
                  <span class="font-medium text-ink">{row.label}.</span> {row.note}
                </p>
              </Show>
            )}
          </For>
          <p>
            <SourceLink citation={contractualRows[0]?.source ?? formulas.source} prefix />
          </p>
        </div>

        <h3 class="mt-10 font-sans text-base font-semibold text-ink">Four corners of a 20% small-value tilt</h3>
        <p class="mt-2 max-w-measure text-ink-muted">
          One sleeve, two inputs, and two defensible readings of each. The corners are not a range of opinion: they are
          the same arithmetic run on a premium pooled across regions or measured in the US alone, and on a sleeve cost
          at the low or high end of the audit.
        </p>
        <DataTable
          class="mt-4"
          caption="A 20% small-value tilt, four corners"
          columns={[
            {
              key: "corner",
              header: "Corner",
              rowHeader: true,
              cell: (row) => `${row.premiumUsed}, cost ${row.sleeveCostPpYr} pp/yr`,
            },
            { key: "edge", header: "Net edge bp/yr", numeric: true, cell: (row) => formatBp(row.netEdgeBp) },
            { key: "te", header: "Tracking error bp/yr", numeric: true, cell: (row) => formatBp(row.trackingErrorBp) },
            { key: "p30", header: "Ahead at 30 yr", numeric: true, cell: (row) => percent(row.probability30yr) },
            { key: "ninety", header: "90% at", numeric: true, cell: (row) => row.ninetyPercentAt },
            {
              key: "reading",
              header: "Reading",
              cell: (row) => (row.isDefensibleReading ? "Defensible" : "Optimistic"),
            },
            {
              key: "load",
              header: "",
              numeric: true,
              cell: (row) => (
                <Load
                  edgeBp={row.netEdgeBp}
                  trackingErrorBp={row.trackingErrorBp}
                  describe={`the ${row.premiumUsed} corner at a ${row.sleeveCostPpYr} pp/yr sleeve cost`}
                />
              ),
            },
          ]}
          rows={smallValueCorners}
          footnote={upperBoundWarning}
        />
        <Prose as="div" class="mt-5">
          <p>
            <strong>{smallValueReading.headline}</strong> {smallValueReading.detail}
          </p>
          <p>{smallValueReading.assumption}</p>
          <p>{smallValueReading.costAssumption}</p>
        </Prose>
        <p class="mt-3">
          <SourceLink citation={smallValueReading.source} prefix />
        </p>

        <h3 class="mt-10 font-sans text-base font-semibold text-ink">Three readings of a 15% trend sleeve</h3>
        <p class="mt-2 max-w-measure text-ink-muted">
          The largest gross premium measured anywhere in this repository sits in this sleeve, and its status is
          unresolved rather than rejected. These are the odds on it, not a verdict about it.
        </p>
        <DataTable
          class="mt-4"
          caption="A 15% managed-futures sleeve, three cases"
          columns={[
            { key: "case", header: "Case", rowHeader: true, cell: (row) => row.label },
            { key: "edge", header: "Net edge bp/yr", numeric: true, cell: (row) => formatBp(row.netEdgeBp) },
            { key: "te", header: "Tracking error bp/yr", numeric: true, cell: (row) => formatBp(row.trackingErrorBp) },
            { key: "p30", header: "Ahead at 30 yr", numeric: true, cell: (row) => percent(row.probability30yr) },
            { key: "ninety", header: "90% at", numeric: true, cell: (row) => row.ninetyPercentAt },
            {
              key: "load",
              header: "",
              numeric: true,
              cell: (row) => <Load edgeBp={row.netEdgeBp} trackingErrorBp={row.trackingErrorBp} describe={row.label} />,
            },
          ]}
          rows={managedFuturesCases}
          footnote={upperBoundWarning}
        />
        <Prose as="div" class="mt-5">
          <p>
            <strong>{managedFuturesReading.headline}</strong> {managedFuturesReading.detail}
          </p>
        </Prose>
        <Callout variant="caveat" label="What the trend numbers assume">
          <ul class="list-disc pl-5">
            <For each={managedFuturesReading.assumptions}>{(assumption) => <li>{assumption}</li>}</For>
          </ul>
        </Callout>
        <p class="mt-3">
          <SourceLink citation={managedFuturesReading.source} prefix />
        </p>
      </section>

      <section aria-labelledby="decides-heading" id="decides" class="mt-14 scroll-mt-6">
        <h2 id="decides-heading" class={H2}>
          What this decides
        </h2>
        <p class="mt-2 max-w-measure text-ink-muted">
          Three lines, side by side, at the confidence level nobody argues with.
        </p>
        <DataTable
          class="mt-4"
          caption="Years to 99% confidence, three ways"
          columns={[
            { key: "line", header: "Line", rowHeader: true, cell: (row) => row.label },
            { key: "edge", header: "Edge bp/yr", numeric: true, cell: (row) => formatBp(row.edgeBp) },
            { key: "te", header: "Tracking error bp/yr", numeric: true, cell: (row) => formatBp(row.trackingErrorBp) },
            { key: "ninetynine", header: "99% at", numeric: true, cell: (row) => row.ninetyNinePercentAt },
            {
              key: "load",
              header: "",
              numeric: true,
              cell: (row) => <Load edgeBp={row.edgeBp} trackingErrorBp={row.trackingErrorBp} describe={row.label} />,
            },
          ]}
          rows={decidingComparison}
          footnote={upperBoundWarning}
        />

        <Prose as="div" class="mt-6">
          <p>{decidingComparisonReading}</p>
          <p>
            None of that says a tilt is stupid. A bet with knowable odds is a legitimate thing to take, and the trend
            sleeve carries the largest gross premium measured anywhere here. It says the odds are the thing to look at,
            and that the certain line is available now while the bet is settled somewhere past the end of your life.
          </p>
        </Prose>

        <div class="mt-8 grid max-w-measure gap-6 border-y border-rule py-6 sm:grid-cols-2">
          <Figure
            label="Smallest edge 30 years can demonstrate"
            value={formatBp(demonstrability.thirtyYearsBp)}
            unit="bp/yr"
            size="lg"
            note={`At ${demonstrability.confidence} confidence, against the tracking error the whole budget carries against a cheap index.`}
          />
          <Figure
            label="Smallest edge 50 years can demonstrate"
            value={formatBp(demonstrability.fiftyYearsBp)}
            unit="bp/yr"
            size="lg"
            note={`At ${demonstrability.confidence} confidence, against the tracking error the whole budget carries against a cheap index.`}
          />
        </div>
        <p class="mt-4 max-w-measure text-ink">{demonstrability.reading}</p>
        <p class="mt-3">
          <SourceLink citation={demonstrability.source} prefix />
        </p>

        <Callout variant="caveat" label="Upper bound">
          <p>{upperBoundWarning}</p>
        </Callout>
      </section>
    </>
  );
}
