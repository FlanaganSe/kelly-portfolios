import { Meta, Title } from "@solidjs/meta";
import { A, useNavigate, useSearchParams } from "@solidjs/router";
import { createMemo, createSignal, For, type JSX, lazy, onCleanup, Show, Suspense } from "solid-js";
import { Callout } from "~/components/Callout";
import { FanChart } from "~/components/charts/FanChart";
import { DataTable } from "~/components/DataTable";
import { Figure } from "~/components/Figure";

import { NumberInput } from "~/components/NumberInput";
import { OutperformanceChart, type OutperformanceSeries } from "~/components/OutperformanceChart";
import { PageHeader } from "~/components/PageHeader";
import { Prose } from "~/components/Prose";
import { ExposureBar } from "~/components/portfolio/ExposureBar";
import { Slider } from "~/components/Slider";
import { contractualRows } from "~/content/confidence";
import { engineMeta, portfolioById, portfolios } from "~/content/portfolios";
import { findFund, shelf } from "~/content/shelf";
import { pricedTilts, tiltById } from "~/content/tilts";
import { horizonForConfidence, probabilityOfOutperformance } from "~/lib/horizon";
import {
  defaultLabConfig,
  type LabBenchmark,
  type LabConfig,
  type LabHolding,
  normalise,
  parseLabConfig,
  toLabHref,
  totalPercent,
} from "~/lib/lab/config";
import { simulateRelativePaths } from "~/lib/lab/paths";
import { tiltVerdict } from "~/lib/tilt";

/**
 * The lab.
 *
 * **What it deliberately is not.** It is not a backtest. This repository has no
 * research-grade total-return source (decision 0002), no committed per-fund loading
 * vector, and no established right to redistribute a public factor library. A growth
 * chart built on any of those would be the most persuasive object on the site and the
 * least defensible one.
 *
 * What it does instead is the arithmetic that actually decides whether a tilt is worth
 * holding: an edge, a dispersion around it, and the horizon the pair implies. The
 * probability curve is a tested port of a study module; the fan is a seeded simulation of
 * the same model, and reproduces the curve rather than competing with it.
 */

/**
 * The history panel is the heaviest thing on the page and most readers never paste
 * anything into it, so it is fetched after the rest of the lab is interactive.
 */
const HistoryPanel = lazy(() => import("~/components/lab/HistoryPanel"));

/** Tenths of a year are false precision on a horizon driven by a basis-point slider. */
function formatYears(years: number | null): string {
  if (years === null) {
    return "never";
  }
  if (years > 500) {
    return ">500";
  }
  return years >= 10 ? String(Math.round(years)) : years.toFixed(1);
}

const PATHS = 2000;

/**
 * The simulation costs a couple of hundred milliseconds, which is fine once and awful on
 * every frame of a slider drag. The closed-form figures update immediately; the fan and
 * the URL wait until the reader stops moving.
 */
const SETTLE_MS = 150;

/** One editable line: what the reader typed, and what the shelf knows about it. */
interface Row {
  readonly holding: LabHolding;
  readonly fund: ReturnType<typeof findFund>;
}

/** Presets, so the sliders start from something measured rather than from a round number. */
const BENCHMARK_OF_ROW: Readonly<Record<string, LabBenchmark>> = {
  "own counterfactual": "own-counterfactual",
  "stated index": "cheap-index",
  "average investor": "average-investor",
};

const PRESETS = contractualRows.map((row) => ({
  id: row.id,
  label: row.label,
  edgeBp: row.edgeBp,
  trackingErrorBp: row.trackingErrorBp,
  benchmark: BENCHMARK_OF_ROW[row.benchmark] ?? ("cheap-index" as LabBenchmark),
}));

function holdingsOf(portfolioId: string): LabHolding[] {
  const portfolio = portfolioById(portfolioId);
  return portfolio === undefined ? [] : portfolio.holdings.map((one) => ({ ticker: one.ticker, percent: one.percent }));
}

/** The widest priced line a portfolio publishes, which is the one worth starting from. */
function pricedStart(portfolioId: string): Pick<LabConfig, "edgeBp" | "trackingErrorBp"> | null {
  const priced =
    portfolioById(portfolioId)?.priced.filter((one) => one.edgeBp !== null && (one.trackingErrorBp ?? 0) > 0) ?? [];
  const widest = [...priced].sort((a, b) => (b.trackingErrorBp ?? 0) - (a.trackingErrorBp ?? 0))[0];
  return widest === undefined ? null : { edgeBp: widest.edgeBp ?? 0, trackingErrorBp: widest.trackingErrorBp ?? 0 };
}

const BENCHMARK_LABEL: Readonly<Record<LabBenchmark, string>> = {
  "cheap-index": "a cheap index fund",
  "own-counterfactual": "the portfolio you would otherwise have owned",
  "average-investor": "the average investor",
};

export default function Lab(): JSX.Element {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const initial = (): LabConfig => {
    const query = new URLSearchParams(
      Object.entries(searchParams).flatMap(([key, value]) =>
        value === undefined ? [] : [[key, Array.isArray(value) ? (value[0] ?? "") : value] as [string, string]]
      )
    );
    const parsed = parseLabConfig(query);
    const from = query.get("from");
    if (from === null || parsed.holdings.length > 0) {
      return parsed;
    }
    // `?from=<portfolio>` is the link every portfolio page uses. It preloads the
    // holdings and the widest line that portfolio actually publishes, so the lab opens
    // on a real experiment rather than on a blank form.
    return { ...parsed, holdings: holdingsOf(from), ...(pricedStart(from) ?? {}) };
  };

  const [config, setConfig] = createSignal<LabConfig>(initial());
  const [copied, setCopied] = createSignal(false);
  const [tiltId, setTiltId] = createSignal(pricedTilts[0]?.id ?? "");
  const [premiumId, setPremiumId] = createSignal(pricedTilts[0]?.defaultPremiumId ?? "");
  const [tiltWeight, setTiltWeight] = createSignal((pricedTilts[0]?.publishedWeight ?? 0.2) * 100);

  const [settled, setSettled] = createSignal<LabConfig>(config());
  let settleTimer: ReturnType<typeof setTimeout> | undefined;
  onCleanup(() => clearTimeout(settleTimer));

  const update = (patch: Partial<LabConfig>) => {
    const next = { ...config(), ...patch };
    setConfig(next);
    setCopied(false);
    clearTimeout(settleTimer);
    settleTimer = setTimeout(() => {
      setSettled(next);
      navigate(toLabHref(next), { replace: true, scroll: false });
    }, SETTLE_MS);
  };

  const total = () => totalPercent(config().holdings);
  const balanced = () => Math.abs(total() - 100) < 0.005;

  const resolved = createMemo(() => config().holdings.map((holding) => ({ holding, fund: findFund(holding.ticker) })));

  const unknown = () => resolved().filter((one) => one.fund === undefined);
  const unpriced = () => resolved().filter((one) => one.fund !== undefined && one.fund.expenseRatioBp === null);

  const effectiveFeeBp = createMemo(() =>
    resolved().reduce((sum, one) => sum + ((one.fund?.expenseRatioBp ?? 0) * one.holding.percent) / 100, 0)
  );

  /**
   * Notional per dollar. A wrapper states its own; anything else is taken as 1.00, which
   * is an inference from the fund holding no leverage rather than a figure any issuer
   * prints, and the panel says so.
   */
  const notionalOf = (ticker: string): number => {
    const fund = findFund(ticker);
    const stated = fund?.notionalExposure;
    if (stated === undefined || stated.length === 0) {
      return 1;
    }
    return stated.reduce((sum, one) => sum + one.perDollarOfCapital, 0);
  };

  const grossExposure = createMemo(() =>
    config().holdings.reduce((sum, one) => sum + one.percent * notionalOf(one.ticker), 0)
  );

  const engineSegments = createMemo(() => {
    const totals = new Map<string, number>();
    for (const { holding, fund } of resolved()) {
      const key = fund === undefined ? "Unknown fund" : engineLabelFor(fund.category);
      totals.set(key, (totals.get(key) ?? 0) + holding.percent);
    }
    return [...totals.entries()].map(([label, percent]) => ({
      id: label,
      label,
      percent: Math.round(percent * 100) / 100,
    }));
  });

  const probability = (years: number) =>
    probabilityOfOutperformance({
      edgeBp: config().edgeBp,
      trackingErrorBp: config().trackingErrorBp,
      horizonYears: years,
    });

  const ninetyPercent = createMemo(() => {
    if (config().edgeBp <= 0) {
      return null;
    }
    try {
      return horizonForConfidence({
        edgeBp: config().edgeBp,
        trackingErrorBp: config().trackingErrorBp,
        confidence: 0.9,
      });
    } catch {
      return null;
    }
  });

  /**
   * The simulation reads four numbers, and `settled` is a whole fresh object on every
   * change — so tracking `settled()` directly re-ran a 150–250 ms simulation whenever a
   * weight was typed. This memo is the narrow gate: it changes only when one of the four
   * inputs does.
   */
  const simulationInputs = createMemo(
    () => ({
      edgeBp: settled().edgeBp,
      trackingErrorBp: settled().trackingErrorBp,
      horizonYears: settled().horizonYears,
      seed: settled().seed,
    }),
    undefined,
    {
      equals: (a, b) =>
        a.edgeBp === b.edgeBp &&
        a.trackingErrorBp === b.trackingErrorBp &&
        a.horizonYears === b.horizonYears &&
        a.seed === b.seed,
    }
  );

  const paths = createMemo(() => simulateRelativePaths({ ...simulationInputs(), paths: PATHS }));

  const liveSeries = (): OutperformanceSeries => ({
    id: "live",
    label: "What you set",
    abbr: "Yours",
    fullLabel: `Your inputs: ${config().edgeBp} bp against ${config().trackingErrorBp} bp`,
    edgeBp: config().edgeBp,
    trackingErrorBp: config().trackingErrorBp,
    kind: "live",
  });

  const referenceSeries = (): OutperformanceSeries[] =>
    PRESETS.filter((preset) => preset.trackingErrorBp > 0).map((preset) => ({
      id: preset.id,
      label: preset.label.length > 26 ? `${preset.label.slice(0, 25)}…` : preset.label,
      abbr: `${preset.edgeBp}/${preset.trackingErrorBp}`,
      fullLabel: preset.label,
      edgeBp: preset.edgeBp,
      trackingErrorBp: preset.trackingErrorBp,
      kind: preset.benchmark === "own-counterfactual" ? ("contractual" as const) : ("probabilistic" as const),
    }));

  const tilt = () => tiltById(tiltId());
  const premium = () => tilt()?.premia.find((one) => one.id === premiumId()) ?? tilt()?.premia[0];

  const verdict = createMemo(() => {
    const chosen = tilt();
    const chosenPremium = premium();
    if (chosen === undefined || chosenPremium === undefined) {
      return null;
    }
    return tiltVerdict({ ...chosen.measured, weight: tiltWeight() / 100, hmlPremium: chosenPremium.value });
  });

  const selectTilt = (id: string) => {
    const chosen = tiltById(id);
    if (chosen === undefined) {
      return;
    }
    setTiltId(id);
    setPremiumId(chosen.defaultPremiumId);
    setTiltWeight(chosen.publishedWeight * 100);
  };

  const share = async () => {
    const url = `${window.location.origin}${toLabHref(config())}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  return (
    <>
      <Title>Lab — Portfolio Edge</Title>
      <Meta
        name="description"
        content="Set an edge and a tracking error and see the horizon they imply, the distribution of outcomes, and how long a holder could sit behind."
      />

      <PageHeader
        eyebrow="Lab"
        title="What an edge and a tracking error actually cost you in patience"
        standfirst="Set a portfolio, then set what you believe it earns over its benchmark and how much the difference moves around. The site will tell you how long you would have to hold it to know, and how far behind you could reasonably be on the way there."
      />

      <Callout variant="caveat" label="There is no backtest here" class="mb-10">
        <p>
          Deliberately. This repository has no research-grade total-return source, no committed per-fund exposure
          vectors, and no established right to redistribute a public factor library. A growth chart built on any of
          those would be the most persuasive thing on the site and the least defensible. What follows is arithmetic on
          numbers <em>you</em> supply, with this repository's measured lines offered as starting points.
        </p>
      </Callout>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="build" class="border-t border-rule pt-8">
        <h2 id="build" class="font-serif text-2xl tracking-[-0.01em]">
          1. The portfolio
        </h2>

        <div class="mt-5 flex flex-wrap items-end gap-4">
          <label class="flex flex-col gap-1.5 text-sm">
            <span class="eyebrow">Start from</span>
            <select
              class="control w-64"
              onChange={(event) => {
                const id = event.currentTarget.value;
                if (id === "") {
                  update({ holdings: [] });
                  return;
                }
                update({ holdings: holdingsOf(id), ...(pricedStart(id) ?? {}) });
              }}
            >
              <option value="">Empty</option>
              <For each={portfolios}>{(portfolio) => <option value={portfolio.id}>{portfolio.name}</option>}</For>
            </select>
          </label>

          <label class="flex flex-col gap-1.5 text-sm">
            <span class="eyebrow">Add a fund</span>
            <select
              class="control w-64"
              value=""
              onChange={(event) => {
                const ticker = event.currentTarget.value;
                if (ticker === "" || config().holdings.some((one) => one.ticker === ticker)) {
                  return;
                }
                update({ holdings: [...config().holdings, { ticker, percent: 0 }] });
                event.currentTarget.value = "";
              }}
            >
              <option value="">Choose…</option>
              <For each={shelf}>
                {(fund) => (
                  <option value={fund.ticker}>
                    {fund.ticker} — {fund.name}
                  </option>
                )}
              </For>
            </select>
          </label>

          <button
            type="button"
            class="control cursor-pointer"
            onClick={() => update({ holdings: normalise(config().holdings) })}
          >
            Normalise to 100%
          </button>
          <button type="button" class="control cursor-pointer" onClick={() => update({ holdings: [] })}>
            Clear
          </button>
        </div>

        <Show
          when={config().holdings.length > 0}
          fallback={
            <p class="mt-8 border-l-2 border-rule-strong pl-4 text-base text-ink-muted">
              Nothing held yet. Start from a published portfolio, or add funds one at a time.
            </p>
          }
        >
          <div class="mt-8">
            <DataTable
              caption="Your allocation."
              captionHidden
              columns={[
                {
                  key: "ticker",
                  header: "Fund",
                  rowHeader: true,
                  cell: (row: Row) => (
                    <A href={`/funds/${row.holding.ticker}`} data-numeric class="link font-mono text-sm">
                      {row.holding.ticker}
                    </A>
                  ),
                },
                {
                  key: "name",
                  header: "Name",
                  cell: (row: Row) => <span class="text-ink-muted">{row.fund?.name ?? "Not on this shelf"}</span>,
                },
                {
                  key: "fee",
                  header: "Fee bp",
                  numeric: true,
                  cell: (row: Row) => row.fund?.expenseRatioBp ?? <span class="text-ink-faint">—</span>,
                },
                {
                  key: "weight",
                  header: "Weight %",
                  numeric: true,
                  width: "9rem",
                  cell: (row: Row) => (
                    <NumberInput
                      label={`${row.holding.ticker} weight`}
                      labelHidden
                      value={row.holding.percent}
                      min={0}
                      max={200}
                      step={0.5}
                      unit="%"
                      onInput={(value) =>
                        update({
                          holdings: config().holdings.map((one) =>
                            one.ticker === row.holding.ticker ? { ...one, percent: value } : one
                          ),
                        })
                      }
                    />
                  ),
                },
                {
                  key: "remove",
                  header: "Remove",
                  width: "5rem",
                  cell: (row: Row) => (
                    <button
                      type="button"
                      aria-label={`Remove ${row.holding.ticker}`}
                      class="-mx-2 inline-flex min-h-11 items-center px-2 text-sm text-ink-muted underline underline-offset-2 hover:text-ink"
                      onClick={() =>
                        update({ holdings: config().holdings.filter((one) => one.ticker !== row.holding.ticker) })
                      }
                    >
                      Remove
                    </button>
                  ),
                },
              ]}
              rows={resolved()}
            />

            <div aria-live="polite" class="mt-6 flex flex-wrap items-baseline gap-x-10 gap-y-4">
              <Figure
                label="Total weight"
                value={`${total()}%`}
                tone={balanced() ? "positive" : "caution"}
                note={balanced() ? undefined : "Not 100%. The remainder is cash, or borrowing if you are over."}
              />
              <Figure label="Weighted expense ratio" value={effectiveFeeBp().toFixed(2)} unit="bp/yr" />
              <Figure
                label="Gross exposure"
                value={`${(grossExposure() / 100).toFixed(2)}×`}
                note="Capital weights times each fund's stated notional. A plain fund is taken as 1.00×, which is an inference, not a printed figure."
              />
            </div>

            <div class="mt-8">
              <ExposureBar
                segments={engineSegments()}
                ariaLabel={`Capital weight by category: ${engineSegments()
                  .map((one) => `${one.label} ${one.percent}%`)
                  .join(", ")}.`}
                caption="Capital weight by shelf category."
              />
            </div>

            <Show when={unknown().length > 0 || unpriced().length > 0}>
              <Callout variant="caveat" label="Coverage" class="mt-8">
                <Show when={unknown().length > 0}>
                  <p>
                    Not on this shelf, so nothing is known about them here:{" "}
                    <span data-numeric>
                      {unknown()
                        .map((one) => one.holding.ticker)
                        .join(", ")}
                    </span>
                    . They are counted in the weight and in nothing else.
                  </p>
                </Show>
                <Show when={unpriced().length > 0}>
                  <p>
                    No expense ratio has been read for{" "}
                    <span data-numeric>
                      {unpriced()
                        .map((one) => one.holding.ticker)
                        .join(", ")}
                    </span>
                    , so the weighted fee above is an understatement.
                  </p>
                </Show>
              </Callout>
            </Show>
          </div>
        </Show>
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="tilt" class="mt-14 border-t border-rule pt-8">
        <h2 id="tilt" class="font-serif text-2xl tracking-[-0.01em]">
          2. Price a value tilt
        </h2>
        <p class="mt-2 max-w-measure text-base text-ink-muted">
          Two tilts here have been priced end to end. Everything but the weight and the premium was measured over a
          stated window and is fixed: both loadings, both fees, both turnovers, both volatilities and the correlation.
          At the published weight this arithmetic reproduces the published figure exactly, which is the only reason to
          trust it at any other weight.
        </p>

        <Show when={tilt()}>
          {(chosen) => (
            <>
              <div class="mt-6 grid gap-6 lg:grid-cols-3">
                <label class="flex flex-col gap-1.5 text-sm">
                  <span class="font-medium text-ink">Tilt</span>
                  <select class="control" value={tiltId()} onChange={(event) => selectTilt(event.currentTarget.value)}>
                    <For each={pricedTilts}>{(one) => <option value={one.id}>{one.label}</option>}</For>
                  </select>
                </label>

                <label class="flex flex-col gap-1.5 text-sm">
                  <span class="font-medium text-ink">Which premium you believe</span>
                  <select
                    class="control"
                    value={premiumId()}
                    onChange={(event) => setPremiumId(event.currentTarget.value)}
                  >
                    <For each={chosen().premia}>
                      {(one) => (
                        <option value={one.id}>
                          {one.label} — {one.value.toFixed(2)} pp/yr
                        </option>
                      )}
                    </For>
                  </select>
                  <Show when={premium()}>
                    {(one) => (
                      <span class="text-ink-muted">
                        <span data-numeric>{one().interval}</span> against a detection floor of{" "}
                        <span data-numeric>{one().detectionFloor}</span> pp/yr. {one().note}
                      </span>
                    )}
                  </Show>
                </label>

                <Slider
                  label={`Weight in ${chosen().fundTicker}, funded out of ${chosen().incumbentTicker}`}
                  value={tiltWeight()}
                  onInput={setTiltWeight}
                  min={0}
                  max={60}
                  step={1}
                  unit="% of portfolio"
                  hint={`The research published its figures at ${chosen().publishedWeight * 100}%.`}
                />
              </div>

              <Show when={verdict()}>
                {(result) => (
                  <>
                    <div aria-live="polite" class="mt-10 flex flex-wrap gap-x-12 gap-y-8">
                      <Figure
                        label="Exposure actually bought"
                        value={result().deliveredLoading.toFixed(3)}
                        note={`${chosen().fundTicker} loading less ${chosen().incumbentTicker}'s, measured over ${chosen().window}. The incumbent is not exposure-free.`}
                      />
                      <Figure label="Incremental cost" value={result().incrementalCost.toFixed(3)} unit="pp/yr" />
                      <Figure
                        label="Portfolio edge"
                        value={`${result().portfolioEdgeBasisPoints > 0 ? "+" : ""}${result().portfolioEdgeBasisPoints.toFixed(1)}`}
                        unit="bp/yr"
                        size="lg"
                        tone={result().portfolioEdgeBasisPoints > 0 ? "positive" : "negative"}
                      />
                      <Figure
                        label="Portfolio tracking error"
                        value={result().portfolioTrackingErrorBasisPoints.toFixed(1)}
                        unit="bp/yr"
                        size="lg"
                      />
                      <Figure
                        label="Growth contribution"
                        value={`${result().growthContributionPercent > 0 ? "+" : ""}${(result().growthContributionPercent * 100).toFixed(1)}`}
                        unit="bp/yr"
                        tone={result().growthContributionPercent > 0 ? "positive" : "negative"}
                        note="Geometric. This is what decides; the certainty equivalent reports beside it."
                      />
                      <Figure
                        label="Certainty equivalent, γ=3"
                        value={`${(result().certaintyEquivalentPercent * 100).toFixed(1)}`}
                        unit="bp/yr"
                      />
                      <Figure
                        label="Wealth after 30 years"
                        value={`${result().terminalWealthMultiple30y.toFixed(3)}×`}
                        note="Relative to not tilting at all."
                      />
                    </div>

                    <div class="mt-8 flex flex-wrap items-center gap-4">
                      <button
                        type="button"
                        class="control cursor-pointer"
                        onClick={() =>
                          update({
                            edgeBp: Math.round(result().portfolioEdgeBasisPoints),
                            trackingErrorBp: Math.round(result().portfolioTrackingErrorBasisPoints),
                            benchmark: "cheap-index",
                          })
                        }
                      >
                        Carry this edge and tracking error into the next section
                      </button>
                      <span class="text-sm text-ink-muted">
                        Published at {chosen().publishedWeight * 100}%:{" "}
                        <span data-numeric>
                          {chosen().published.edgeBp} bp against {chosen().published.trackingErrorBp} bp
                        </span>
                        .
                      </span>
                    </div>

                    <Callout variant="caveat" class="mt-8">
                      <p>{chosen().caveat}</p>
                    </Callout>
                  </>
                )}
              </Show>
            </>
          )}
        </Show>
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="edge" class="mt-14 border-t border-rule pt-8">
        <h2 id="edge" class="font-serif text-2xl tracking-[-0.01em]">
          3. What you think it earns, and how much that moves
        </h2>
        <p class="mt-2 max-w-measure text-base text-ink-muted">
          Nothing on this site can tell you the first number. What it can tell you is what the pair implies — and the
          second number, not the first, is what decides whether a lifetime is long enough.
        </p>

        <div class="mt-6 flex flex-wrap gap-2">
          <For each={PRESETS}>
            {(preset) => (
              <button
                type="button"
                aria-pressed={config().edgeBp === preset.edgeBp && config().trackingErrorBp === preset.trackingErrorBp}
                class="control cursor-pointer text-sm aria-pressed:border-accent aria-pressed:text-ink"
                onClick={() =>
                  update({
                    edgeBp: preset.edgeBp,
                    trackingErrorBp: preset.trackingErrorBp,
                    benchmark: preset.benchmark,
                  })
                }
              >
                {preset.label}{" "}
                <span data-numeric class="text-ink-faint">
                  ({preset.edgeBp}/{preset.trackingErrorBp})
                </span>
              </button>
            )}
          </For>
        </div>

        <div class="mt-8 grid gap-8 lg:grid-cols-2">
          <Slider
            label="Expected edge"
            value={config().edgeBp}
            onInput={(value) => update({ edgeBp: value })}
            min={-100}
            max={400}
            step={1}
            unit="bp/yr"
            hint="Annual return over the benchmark, before any dispersion. A negative value is a real thing to test."
          />
          <Slider
            label="Tracking error"
            value={config().trackingErrorBp}
            onInput={(value) => update({ trackingErrorBp: value })}
            min={0}
            max={800}
            step={1}
            unit="bp/yr"
            hint="Annual standard deviation of the difference from the benchmark."
          />
          <Slider
            label="Horizon"
            value={config().horizonYears}
            onInput={(value) => update({ horizonYears: value })}
            min={1}
            max={50}
            step={1}
            unit="yr"
            hint="How long you intend to hold it without changing your mind."
          />
          <label class="flex flex-col gap-1.5 text-sm">
            <span class="font-medium text-ink">Measured against</span>
            <select
              class="control"
              value={config().benchmark}
              onChange={(event) =>
                update({
                  benchmark: event.currentTarget.value === "own-counterfactual" ? "own-counterfactual" : "cheap-index",
                })
              }
            >
              <option value="cheap-index">A cheap index fund</option>
              <option value="own-counterfactual">The portfolio you would otherwise have owned</option>
            </select>
            <span class="text-ink-muted">These are different claims and may never be added together.</span>
          </label>
        </div>

        <div aria-live="polite" class="mt-10 flex flex-wrap gap-x-12 gap-y-8">
          <Figure
            label={`Chance of being ahead at ${config().horizonYears} years`}
            value={`${(probability(config().horizonYears) * 100).toFixed(1)}%`}
            size="lg"
          />
          <Figure label="At ten years" value={`${(probability(10) * 100).toFixed(1)}%`} />
          <Figure
            label="Years to be 90% sure"
            value={
              ninetyPercent() === null
                ? "never"
                : (ninetyPercent() ?? 0) > 500
                  ? ">500"
                  : (ninetyPercent() ?? 0).toFixed(1)
            }
            unit={ninetyPercent() === null ? undefined : "yr"}
            note={ninetyPercent() === null ? "A zero or negative edge never becomes visible." : undefined}
          />
        </div>

        <div class="mt-10">
          <OutperformanceChart
            series={referenceSeries()}
            live={liveSeries()}
            horizonYears={config().horizonYears}
            ariaLabel={`Probability of being ahead of ${BENCHMARK_LABEL[config().benchmark]} against holding period, for your inputs and for the lines this repository has measured.`}
            caption={
              <>
                Your inputs in the accent colour, against the lines this repository has measured. The horizontal axis is
                square-rooted because the probability runs on <code>√T</code>.
              </>
            }
            tableCaption="Probability of being ahead, by horizon."
          />
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="feel" class="mt-14 border-t border-rule pt-8">
        <h2 id="feel" class="font-serif text-2xl tracking-[-0.01em]">
          4. What holding it would feel like
        </h2>
        <p class="mt-2 max-w-measure text-base text-ink-muted">
          The same model, simulated rather than solved. A probability of being ahead at the end says nothing about the
          route, and the route is what people actually abandon a strategy over.
        </p>

        <div aria-live="polite" class="mt-8 flex flex-wrap gap-x-12 gap-y-8">
          <Figure
            label="Median longest spell behind"
            value={(paths().medianLongestDroughtMonths / 12).toFixed(1)}
            unit="yr"
            note="Consecutive months below the previous best relative to the benchmark."
          />
          <Figure
            label="Median worst shortfall"
            value={`${(paths().medianWorstShortfall * 100).toFixed(1)}%`}
            tone="caution"
            note="How far below its own relative peak a typical path fell."
          />
          <Figure
            label="Paths spending 3 years or more below their own best"
            value={`${(paths().fractionWithLongDrought * 100).toFixed(0)}%`}
          />
          <Figure label="Paths ahead at the end" value={`${(paths().fractionAhead * 100).toFixed(1)}%`} />
        </div>

        <div class="mt-10">
          <FanChart
            bands={paths().bands}
            horizonYears={settled().horizonYears}
            ariaLabel={`Simulated wealth relative to ${BENCHMARK_LABEL[settled().benchmark]} over ${settled().horizonYears} years, shown as percentile bands from ${PATHS} seeded paths.`}
            tableCaption="Wealth relative to the benchmark, by percentile and horizon."
            caption={
              <>
                {PATHS.toLocaleString()} seeded paths, so this picture is the same on every machine and every reload.
                The share ending above 1.00× reproduces the closed-form probability above rather than competing with it.
              </>
            }
          />
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="history" class="mt-14 border-t border-rule pt-8">
        <h2 id="history" class="font-serif text-2xl tracking-[-0.01em]">
          5. Bring your own history
        </h2>
        <p class="mt-2 max-w-measure text-base text-ink-muted">
          The one honest way to get a backtest out of this site: supply the returns yourself, from a source you are
          entitled to use, and the engine will run them. Nothing is uploaded and nothing is stored — the paste stays in
          this tab and disappears when you close it.
        </p>

        <div class="mt-8">
          <Suspense fallback={<p class="text-sm text-ink-muted">Loading the history panel…</p>}>
            <HistoryPanel holdings={config().holdings} />
          </Suspense>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}

      <section aria-labelledby="assumptions" class="mt-14 border-t border-rule pt-8">
        <h2 id="assumptions" class="font-serif text-2xl tracking-[-0.01em]">
          Assumptions, and what this cannot tell you
        </h2>
        <Prose class="mt-4">
          <ul>
            <li>
              Relative performance is modelled as a random walk with drift, log-normal in the ratio. That is the same
              model behind the probability curve, and it assumes the edge is constant and the dispersion is stationary.
              Neither is true of a real strategy.
            </li>
            <li>
              The edge and the tracking error are <strong>yours</strong>. The presets are figures this repository has
              measured; none of them is a forecast.
            </li>
            <li>
              Fees are counted only through the weighted expense ratio, which omits spread, brokerage, realised
              distributions and turnover — all of which are absent from the underlying product audits too.
            </li>
            <li>
              Notional exposure comes from the funds that publish one. Everything else is taken as one dollar per
              dollar, which is an inference from the fund holding no leverage rather than a figure any issuer prints.
            </li>
            <li>
              Nothing is stored. The whole state is in the address bar, so the link below reproduces exactly what you
              are looking at.
            </li>
          </ul>
        </Prose>

        <div class="mt-6 flex flex-wrap items-center gap-4">
          <button type="button" class="control cursor-pointer" onClick={share}>
            Copy a link to this experiment
          </button>
          <span role="status" class="text-sm text-ink-muted">
            <Show when={copied()}>Copied to the clipboard.</Show>
          </span>
          <button type="button" class="control cursor-pointer" onClick={() => update({ ...defaultLabConfig })}>
            Reset
          </button>
        </div>
      </section>
    </>
  );
}

/** The shelf's categories, collapsed to something a reader recognises on a bar. */
function engineLabelFor(category: string): string {
  if (category.endsWith("-value")) {
    return engineMeta.value.label;
  }
  if (category.endsWith("-momentum")) {
    return engineMeta.momentum.label;
  }
  if (category === "managed-futures") {
    return engineMeta.trend.label;
  }
  if (category === "capital-efficient") {
    return "Stacked wrapper";
  }
  if (category === "bonds") {
    return engineMeta["term-and-credit"].label;
  }
  if (category === "alternative") {
    return "Alternative";
  }
  return engineMeta["equity-beta"].label;
}
