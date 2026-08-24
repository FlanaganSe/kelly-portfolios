import { createMemo, createSignal, createUniqueId, For, type JSX, Show } from "solid-js";
import { Callout } from "~/components/Callout";
import { TimeSeriesChart } from "~/components/charts/TimeSeriesChart";
import { DataTable } from "~/components/DataTable";
import { Figure } from "~/components/Figure";
import { NumberInput } from "~/components/NumberInput";
import { Prose } from "~/components/Prose";
import { Slider } from "~/components/Slider";
import { toMonthIndex, toYearMonth } from "~/lib/backtest/calendar";
import {
  annualisedVolatility,
  beta,
  type CalendarYear,
  cagr,
  calendarYears,
  correlation,
  drawdownPath,
  fractionAhead,
  growthPath,
  informationRatio,
  maxDrawdown,
  rollingExcess,
  sharpeRatio,
  trackingError,
} from "~/lib/backtest/metrics";
import { commonRange, rangeLength, seriesEnd, slice } from "~/lib/backtest/series";
import { simulate } from "~/lib/backtest/simulate";
import type { MonthRange, RebalanceFrequency, ReturnSeries, SimulationResult } from "~/lib/backtest/types";
import { type ImportProblem, importReturns } from "~/lib/lab/importReturns";

/**
 * Your own history, run through the engine.
 *
 * This site ships no price data, on purpose: there is no research-grade free source
 * (decision 0002) and no established right to redistribute a public factor library. What
 * it can honestly do is run a tested engine over a series the reader already has. The
 * paste box is the whole mechanism — nothing is uploaded, stored or transmitted, and
 * there is no request to make because there is no server to make it to.
 *
 * Two conventions the panel refuses to hide, because they are where backtest tools
 * quietly disagree with each other:
 *
 * - **The common history is the test.** Two funds with different inception dates share
 *   only the window both cover; the engine will not extend the shorter one, so the panel
 *   names the holding that set each end of the window.
 * - **The risk-free rate is an input, not a constant.** Sharpe is meaningless without it,
 *   so it is a control with its value printed beside the ratio rather than a number
 *   buried in a formula.
 */

export interface HistoryPanelProps {
  readonly holdings: readonly { readonly ticker: string; readonly percent: number }[];
  /** Pre-selects the benchmark, when a column of that name is imported. */
  readonly benchmarkDefault?: string;
}

const ROLLING_MONTHS = 36;
const MONTHS_PER_YEAR = 12;

/**
 * A starting investment, and the values derived from it, with no currency symbol.
 *
 * The reader's own data may be in any currency and this panel has no way to know which,
 * so it prints a number and stays quiet about the unit rather than guessing at a dollar.
 */
function money(value: number): string {
  return value >= 1000 ? Math.round(value).toLocaleString("en-US") : value.toFixed(2);
}
const EXAMPLE_MONTHS = 60;
const EXAMPLE_START = "2019-01";

/** Weights are floats: 33 + 33 + 34 leaves a residue that is rounding, not a cash holding. */
const CASH_EPSILON = 1e-9;

const REBALANCE_OPTIONS: readonly { readonly value: RebalanceFrequency; readonly label: string }[] = [
  { value: "monthly", label: "Monthly" },
  { value: "quarterly", label: "Quarterly (Jan, Apr, Jul, Oct)" },
  { value: "annually", label: "Annually (each January)" },
  { value: "never", label: "Never — let the weights drift" },
];

function formatPercent(value: number | null | undefined, decimals = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }
  return `${(value * 100).toFixed(decimals)}%`;
}

function formatRatio(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }
  return value.toFixed(2);
}

/** `growth[0]` is the month **before** the window opens, so index 0 has no month of its own. */
function pointLabel(range: MonthRange, index: number): string {
  return index === 0 ? "the start" : toYearMonth(range.start + index - 1);
}

interface AnalysisInput {
  readonly holdings: readonly { readonly ticker: string; readonly percent: number }[];
  readonly seriesById: ReadonlyMap<string, ReturnSeries>;
  readonly benchmarkId: string | null;
  readonly rebalance: RebalanceFrequency;
  readonly applyExpenses: boolean;
  readonly expensePercent: (ticker: string) => number;
  /** Clips the test to a window inside the common history. `null` means all of it. */
  readonly restrict: { readonly from: string | null; readonly to: string | null };
}

interface Analysis {
  readonly range: MonthRange;
  readonly result: SimulationResult;
  readonly benchmark: ReturnSeries;
  readonly benchmarkReturns: readonly number[];
  /** Every series in the test, holdings and benchmark alike. */
  readonly involved: readonly ReturnSeries[];
}

type AnalysisState =
  | { readonly kind: "ok"; readonly analysis: Analysis }
  | { readonly kind: "no-holdings" }
  | { readonly kind: "no-benchmark" }
  | { readonly kind: "missing"; readonly tickers: readonly string[] }
  | { readonly kind: "no-overlap" }
  | { readonly kind: "failed"; readonly message: string };

/**
 * The whole computation, as one pure function of the controls.
 *
 * It returns a reason rather than throwing, because every failure here is a state the
 * interface has to describe: the reader has not pasted a column for a holding, or the
 * columns never coexisted.
 */
function analyse(input: AnalysisInput): AnalysisState {
  const held = input.holdings.filter((one) => one.percent !== 0);
  if (held.length === 0) {
    return { kind: "no-holdings" };
  }
  const benchmark = input.benchmarkId === null ? undefined : input.seriesById.get(input.benchmarkId);
  if (benchmark === undefined) {
    return { kind: "no-benchmark" };
  }

  const missing = held.filter((one) => !input.seriesById.has(one.ticker)).map((one) => one.ticker);
  if (missing.length > 0) {
    return { kind: "missing", tickers: missing };
  }

  const holdingSeries = held.flatMap((one) => {
    const series = input.seriesById.get(one.ticker);
    return series === undefined ? [] : [series];
  });
  const involved = [...holdingSeries, benchmark];
  const available = commonRange(involved);
  if (available === null) {
    return { kind: "no-overlap" };
  }

  // A requested window is clipped to what the data has rather than refused, and an
  // inverted or too-short request falls back to the whole of it: a period control that
  // can empty the page is worse than one that quietly declines.
  const asked = {
    start:
      input.restrict.from === null ? available.start : Math.max(available.start, toMonthIndex(input.restrict.from)),
    end: input.restrict.to === null ? available.end : Math.min(available.end, toMonthIndex(input.restrict.to)),
  };
  const range = asked.end - asked.start + 1 >= MONTHS_PER_YEAR ? asked : available;

  try {
    const result = simulate({
      allocations: held.map((one) => ({
        symbol: one.ticker,
        weight: one.percent / 100,
        expenseRatio: input.expensePercent(one.ticker) / 100,
      })),
      series: input.seriesById,
      rebalance: input.rebalance,
      applyExpenses: input.applyExpenses,
      range,
    });
    return {
      kind: "ok",
      analysis: { range, result, benchmark, benchmarkReturns: slice(benchmark, range), involved },
    };
  } catch (error) {
    return { kind: "failed", message: error instanceof Error ? error.message : String(error) };
  }
}

/** Why the engine has nothing to run. `null` when it does. */
function blockedMessage(state: AnalysisState): string | null {
  switch (state.kind) {
    case "ok":
      return null;
    case "no-holdings":
      return "There are no holdings with a weight, so there is no portfolio to test.";
    case "no-benchmark":
      return "Pick a benchmark column. Every relative figure here is measured against one, and this panel will not invent it.";
    case "missing":
      return `No column was imported for ${state.tickers.join(", ")}. Add it to the paste, or set that holding's weight to zero.`;
    case "no-overlap":
      return "The imported columns never all existed in the same month, so there is no window to test. A shorter series is never extended to fill one.";
    case "failed":
      return state.message;
  }
}

/**
 * A stable, obviously fake series for the "Load example" button.
 *
 * A linear congruential generator, so the same button always produces the same numbers
 * and nobody can mistake a reload for new information. These are invented figures. They
 * are not market data, no fund produced them, and nothing on this site is fitted to them.
 */
function inventedReturns(seed: number, months: number): number[] {
  let state = (seed * 2654435761) % 2147483647;
  const out: number[] = [];
  for (let index = 0; index < months; index += 1) {
    state = (state * 1103515245 + 12345) % 2147483647;
    out.push(Math.round(((state / 2147483647) * 0.11 - 0.042) * 10000) / 10000);
  }
  return out;
}

function seedOf(ticker: string): number {
  let seed = 7;
  for (const character of ticker) {
    seed = (seed * 31 + character.charCodeAt(0)) % 100003;
  }
  return seed + 1;
}

function monthAfter(yearMonth: string, offset: number): string {
  const [year = 1970, month = 1] = yearMonth.split("-").map(Number);
  const index = (year - 1970) * MONTHS_PER_YEAR + (month - 1) + offset;
  return toYearMonth(index);
}

/** A worked example in the accepted format, built from the tickers actually held. */
function exampleText(tickers: readonly string[], benchmark: string): string {
  const columns = [...new Set([...tickers, benchmark])].filter((one) => one !== "");
  const named = columns.length > 0 ? columns : ["FUND-A", "BENCH"];
  const values = named.map((ticker) => inventedReturns(seedOf(ticker), EXAMPLE_MONTHS));
  const rows = Array.from(
    { length: EXAMPLE_MONTHS },
    (_, index) => `${monthAfter(EXAMPLE_START, index)},${values.map((one) => (one[index] ?? 0).toFixed(4)).join(",")}`
  );
  return [`Month,${named.join(",")}`, ...rows].join("\n");
}

interface MetricRow {
  readonly key: string;
  readonly metric: string;
  readonly portfolio: JSX.Element;
  readonly benchmark: JSX.Element;
}

interface DefinitionRow {
  readonly term: string;
  readonly definition: string;
}

const DEFINITIONS: readonly DefinitionRow[] = [
  {
    term: "CAGR",
    definition:
      "The single annual growth rate that would have turned the starting value into the ending one. It is not the average of the yearly returns, which is always higher.",
  },
  {
    term: "Annualised volatility",
    definition:
      "The sample standard deviation of the monthly returns, multiplied by the square root of twelve. It measures how much the monthly figures scatter, not how much you might lose.",
  },
  {
    term: "Max drawdown",
    definition:
      "The deepest fall from a previous month-end high to a later month-end low. Measured on month ends, so the worst price actually seen during a month is invisible to it and this figure understates it.",
  },
  {
    term: "Best and worst calendar year",
    definition:
      "The highest and lowest returns over a full January-to-December year. Part years at the start or end of the window are excluded rather than annualised.",
  },
  {
    term: "Sharpe ratio",
    definition:
      "Average monthly return above the risk-free rate, annualised, divided by annualised volatility. Higher means more return per unit of scatter. It uses the arithmetic mean, not CAGR.",
  },
  {
    term: "Correlation",
    definition:
      "How closely the monthly returns move with the benchmark's, from +1 (in lockstep) through 0 (unrelated) to −1 (opposite). It says nothing about which one earned more.",
  },
  {
    term: "Beta",
    definition:
      "How much the portfolio moved for each 1% move in the benchmark, fitted by least squares. A beta of 1.1 means it tended to move 10% further in both directions.",
  },
  {
    term: "Tracking error",
    definition:
      "The annualised standard deviation of the monthly difference from the benchmark. It is the size of the bumps along the way, and it is what makes a real edge take years to show.",
  },
  {
    term: "Information ratio",
    definition:
      "Average annual excess return divided by tracking error. It is the edge measured in units of the noise you have to sit through to collect it.",
  },
  {
    term: "Rolling 3-year windows ahead",
    definition:
      "Of every overlapping 36-month stretch in the window, the share in which the portfolio's annualised return beat the benchmark's. Overlapping windows are not independent, so this is a description, not a test.",
  },
];

export function HistoryPanel(props: HistoryPanelProps): JSX.Element {
  const pasteId = createUniqueId();
  const benchmarkId = createUniqueId();
  const rebalanceId = createUniqueId();
  const expensesId = createUniqueId();
  const logId = createUniqueId();

  const [draft, setDraft] = createSignal("");
  // Whether what is currently shown came from the invented example. The results region
  // has to say so: real tickers over made-up returns produce a CAGR and a drawdown that
  // look exactly like a finding.
  const [fromExample, setFromExample] = createSignal(false);
  const [submitted, setSubmitted] = createSignal("");
  const [chosenBenchmark, setChosenBenchmark] = createSignal<string | null>(null);
  const [rebalance, setRebalance] = createSignal<RebalanceFrequency>("annually");
  const [applyExpenses, setApplyExpenses] = createSignal(false);
  const [expenses, setExpenses] = createSignal<Readonly<Record<string, number>>>({});
  const [riskFreePercent, setRiskFreePercent] = createSignal(0);
  const [logGrowth, setLogGrowth] = createSignal(false);
  const [initial, setInitial] = createSignal(10_000);
  const [fromMonth, setFromMonth] = createSignal<string | null>(null);
  const [toMonth, setToMonth] = createSignal<string | null>(null);

  const parsed = createMemo(() => (submitted() === "" ? null : importReturns(submitted())));
  const problems = (): readonly ImportProblem[] => parsed()?.problems ?? [];
  const imported = (): readonly ReturnSeries[] => parsed()?.series ?? [];
  const seriesById = createMemo(() => new Map(imported().map((one) => [one.id, one])));

  const heldTickers = createMemo(() => props.holdings.filter((one) => one.percent !== 0).map((one) => one.ticker));

  /** The reader's choice wins; then the caller's default; then a column nothing holds. */
  const benchmarkChoice = createMemo<string | null>(() => {
    const chosen = chosenBenchmark();
    if (chosen !== null && seriesById().has(chosen)) {
      return chosen;
    }
    const fallback = props.benchmarkDefault;
    if (fallback !== undefined && seriesById().has(fallback)) {
      return fallback;
    }
    const held = new Set(heldTickers());
    return imported().find((one) => !held.has(one.id))?.id ?? imported()[0]?.id ?? null;
  });

  const expensePercent = (ticker: string): number => expenses()[ticker] ?? 0;

  /** Geometric, so a year of monthly charges costs exactly the annual rate. */
  const monthlyRiskFree = createMemo(() => (1 + riskFreePercent() / 100) ** (1 / MONTHS_PER_YEAR) - 1);

  const state = createMemo<AnalysisState | null>(() =>
    parsed() === null
      ? null
      : analyse({
          holdings: props.holdings,
          seriesById: seriesById(),
          benchmarkId: benchmarkChoice(),
          rebalance: rebalance(),
          applyExpenses: applyExpenses(),
          expensePercent,
          restrict: { from: fromMonth(), to: toMonth() },
        })
  );

  /**
   * What the period control may offer. Deliberately computed from the unrestricted
   * common history, so narrowing the window never narrows the control that widens it.
   */
  const availableWindow = createMemo<{ first: string; last: string } | null>(() => {
    const all = parsed();
    if (all === null) {
      return null;
    }
    const held = props.holdings.filter((one) => one.percent !== 0).map((one) => seriesById().get(one.ticker));
    const benchmark = benchmarkChoice() === null ? undefined : seriesById().get(benchmarkChoice() ?? "");
    const involved = [...held, benchmark].filter((one): one is ReturnSeries => one !== undefined);
    const range = involved.length === 0 ? null : commonRange(involved);
    return range === null ? null : { first: toYearMonth(range.start), last: toYearMonth(range.end) };
  });

  const ok = createMemo<Analysis | null>(() => {
    const current = state();
    return current !== null && current.kind === "ok" ? current.analysis : null;
  });

  const blocked = createMemo<string | null>(() => {
    const current = state();
    return current === null ? null : blockedMessage(current);
  });

  /** Which series pinned each end of the common window. Ties are all named. */
  const boundary = createMemo(() => {
    const analysis = ok();
    if (analysis === null) {
      return null;
    }
    const { range, involved } = analysis;
    return {
      startedBy: involved.filter((one) => one.start === range.start).map((one) => one.id),
      endedBy: involved.filter((one) => seriesEnd(one) === range.end).map((one) => one.id),
    };
  });

  const windows = createMemo(() => {
    const analysis = ok();
    if (analysis === null) {
      return [];
    }
    return rollingExcess(analysis.result.returns, analysis.benchmarkReturns, analysis.range.start, ROLLING_MONTHS);
  });

  const years = createMemo(() => {
    const analysis = ok();
    if (analysis === null) {
      return [];
    }
    return calendarYears(analysis.result.returns, analysis.range.start, analysis.benchmarkReturns).filter(
      (one) => one.complete
    );
  });

  const bestYear = createMemo<CalendarYear | null>(() =>
    years().reduce<CalendarYear | null>(
      (best, one) => (best === null || one.portfolio > best.portfolio ? one : best),
      null
    )
  );
  const worstYear = createMemo<CalendarYear | null>(() =>
    years().reduce<CalendarYear | null>(
      (worst, one) => (worst === null || one.portfolio < worst.portfolio ? one : worst),
      null
    )
  );

  const drawdown = createMemo(() => {
    const analysis = ok();
    return analysis === null ? null : maxDrawdown(analysis.result.returns);
  });

  const metricRows = createMemo<readonly MetricRow[]>(() => {
    const analysis = ok();
    if (analysis === null) {
      return [];
    }
    const portfolio = analysis.result.returns;
    const bench = analysis.benchmarkReturns;
    const worst = drawdown();
    const best = bestYear();
    const poorest = worstYear();
    const benchWorst = maxDrawdown(bench);

    return [
      {
        key: "cagr",
        metric: "CAGR",
        portfolio: formatPercent(cagr(portfolio)),
        benchmark: formatPercent(cagr(bench)),
      },
      {
        key: "volatility",
        metric: "Annualised volatility",
        portfolio: formatPercent(annualisedVolatility(portfolio)),
        benchmark: formatPercent(annualisedVolatility(bench)),
      },
      {
        key: "drawdown",
        metric: "Max drawdown",
        portfolio: (
          <>
            {formatPercent(worst?.depth)}
            <Show when={worst !== null && worst.depth < 0 ? worst : null}>
              {(deepest) => (
                <span class="block text-xs font-normal text-ink-faint">
                  {pointLabel(analysis.range, deepest().peakIndex)} to{" "}
                  {pointLabel(analysis.range, deepest().troughIndex)},{" "}
                  {deepest().recoveryIndex === null
                    ? "never recovered inside this window"
                    : `back to that peak by ${pointLabel(analysis.range, deepest().recoveryIndex ?? 0)}`}
                </span>
              )}
            </Show>
          </>
        ),
        benchmark: formatPercent(benchWorst.depth),
      },
      {
        key: "best-year",
        metric: "Best complete calendar year",
        portfolio: best === null ? "—" : `${formatPercent(best.portfolio)} (${best.year})`,
        benchmark: best === null ? "—" : formatPercent(best.benchmark),
      },
      {
        key: "worst-year",
        metric: "Worst complete calendar year",
        portfolio: poorest === null ? "—" : `${formatPercent(poorest.portfolio)} (${poorest.year})`,
        benchmark: poorest === null ? "—" : formatPercent(poorest.benchmark),
      },
      {
        key: "sharpe",
        metric: "Sharpe ratio",
        portfolio: formatRatio(sharpeRatio(portfolio, monthlyRiskFree())),
        benchmark: formatRatio(sharpeRatio(bench, monthlyRiskFree())),
      },
      {
        key: "correlation",
        metric: "Correlation to benchmark",
        portfolio: formatRatio(correlation(portfolio, bench)),
        benchmark: "1.00",
      },
      { key: "beta", metric: "Beta to benchmark", portfolio: formatRatio(beta(portfolio, bench)), benchmark: "1.00" },
      {
        key: "tracking-error",
        metric: "Tracking error",
        portfolio: formatPercent(trackingError(portfolio, bench)),
        benchmark: "0.00%",
      },
      {
        key: "information-ratio",
        metric: "Information ratio",
        portfolio: formatRatio(informationRatio(portfolio, bench)),
        benchmark: "—",
      },
      {
        key: "ahead",
        metric: "Rolling 3-year windows ahead",
        portfolio:
          windows().length === 0 ? "—" : `${formatPercent(fractionAhead(windows()), 0)} of ${windows().length}`,
        benchmark: "—",
      },
    ];
  });

  const growthSeries = createMemo(() => {
    const analysis = ok();
    if (analysis === null) {
      return [];
    }
    const start = initial();
    return [
      {
        id: "portfolio",
        label: "Your portfolio",
        abbr: "Yours",
        values: analysis.result.growth.map((one) => one * start),
        emphasis: true,
      },
      {
        id: "benchmark",
        label: analysis.benchmark.id,
        abbr: analysis.benchmark.id,
        values: growthPath(analysis.benchmarkReturns).map((one) => one * start),
      },
    ];
  });

  const drawdownSeries = createMemo(() => {
    const analysis = ok();
    if (analysis === null) {
      return [];
    }
    return [
      {
        id: "portfolio",
        label: "Your portfolio",
        abbr: "Yours",
        values: drawdownPath(analysis.result.returns),
        emphasis: true,
      },
      {
        id: "benchmark",
        label: analysis.benchmark.id,
        abbr: analysis.benchmark.id,
        values: drawdownPath(analysis.benchmarkReturns),
      },
    ];
  });

  const loadExample = () => {
    const text = exampleText(heldTickers(), props.benchmarkDefault ?? "BENCH");
    setDraft(text);
    setSubmitted(text);
    setFromExample(true);
  };

  return (
    <section class="mt-10" aria-labelledby={`${pasteId}-heading`}>
      <h3 id={`${pasteId}-heading`} class="text-lg font-semibold text-ink">
        Run it on your own history
      </h3>

      <Prose class="mt-3">
        <p>
          This site ships no price data, because it has no research-grade source it is free to redistribute. The engine
          is here all the same: paste monthly total returns you already have and it will run them.
        </p>
      </Prose>

      <Callout variant="mechanism" label="Where your data goes">
        <p>
          Nowhere. The parser and the engine both run in this browser tab, there is no account and no server to send
          anything to, and nothing you paste is uploaded, stored or logged. Closing the tab is the delete button.
        </p>
      </Callout>

      <div class="mt-6">
        <label for={pasteId} class="text-sm font-medium text-ink">
          Monthly total returns
        </label>
        <p id={`${pasteId}-hint`} class="mt-1 max-w-measure text-xs text-ink-faint">
          One header row, then one row per month. The first column is the month as <code>YYYY-MM</code> or{" "}
          <code>YYYY-MM-DD</code>; every column after it is one ticker. Values may be decimals (<code>0.0123</code>) or
          percentages (<code>1.23%</code>) — a <code>%</code> anywhere in a column marks the whole column, and nothing
          is ever inferred from how big a number looks. Commas or tabs both work. Leave a cell blank for a month a fund
          did not exist; a blank is never read as zero.
        </p>
        <p class="mt-2 text-xs text-ink-faint">The shape, with invented numbers and invented column names:</p>
        <pre class="mt-1 overflow-x-auto border border-rule bg-sunken p-3 text-xs">
          {"Month,FUND_A,FUND_B\n2019-01,0.0854,0.1131\n2019-02,0.0342,0.0447\n2019-03,0.0144,-0.0281"}
        </pre>
        <textarea
          id={pasteId}
          class="control mt-3 h-44 w-full font-mono text-xs"
          aria-describedby={`${pasteId}-hint`}
          placeholder="Month,FUND_A,FUND_B&#10;2019-01,0.0854,0.1131"
          value={draft()}
          onInput={(event) => {
            setDraft(event.currentTarget.value);
            setFromExample(false);
          }}
        />
        <div class="mt-3 flex flex-wrap items-center gap-3">
          <button type="button" class="control cursor-pointer font-medium" onClick={() => setSubmitted(draft())}>
            Import
          </button>
          <button type="button" class="control cursor-pointer" onClick={loadExample}>
            Load example
          </button>
          <button
            type="button"
            class="control cursor-pointer"
            onClick={() => {
              setDraft("");
              setSubmitted("");
              setFromExample(false);
            }}
          >
            Clear
          </button>
        </div>
        <p class="mt-2 max-w-measure text-xs text-ink-faint">
          <strong>The example is invented.</strong> Its numbers come from a fixed pseudo-random generator, not from any
          fund and not from any market. They exist only to show the format and to let you try the controls. Nothing on
          this site is derived from them, and no conclusion drawn from them means anything.
        </p>
      </div>

      <Show when={problems().length > 0}>
        <Callout variant="caveat" label="What could not be imported">
          <ul class="list-disc pl-5">
            <For each={problems()}>
              {(problem) => (
                <li>
                  <Show when={problem.ticker}>
                    {(ticker) => <strong class="font-semibold text-ink">{ticker()}</strong>}
                  </Show>
                  <Show when={problem.ticker && problem.month}>
                    <span data-numeric class="text-ink">
                      {" "}
                      · {problem.month}
                    </span>
                  </Show>
                  <Show when={problem.ticker}>{" — "}</Show>
                  {problem.message}
                </li>
              )}
            </For>
          </ul>
        </Callout>
      </Show>

      <Show when={parsed() === null}>
        <p class="mt-6 max-w-measure text-sm text-ink-muted">
          Nothing imported yet. Paste a table above, or load the invented example, and the charts and the metrics table
          will appear here.
        </p>
      </Show>

      <Show when={imported().length > 0}>
        <div class="mt-8 grid gap-6 sm:grid-cols-2">
          <div class="flex flex-col gap-1">
            <label for={benchmarkId} class="text-sm font-medium text-ink">
              Benchmark
            </label>
            <select
              id={benchmarkId}
              class="control"
              value={benchmarkChoice() ?? ""}
              onChange={(event) => setChosenBenchmark(event.currentTarget.value)}
            >
              <For each={imported()}>{(series) => <option value={series.id}>{series.id}</option>}</For>
            </select>
            <p class="max-w-[42ch] text-xs text-ink-faint">
              Correlation, beta, tracking error, information ratio and the rolling windows are all measured against this
              column, and against nothing else.
            </p>
          </div>

          <div class="flex flex-col gap-1">
            <label for={rebalanceId} class="text-sm font-medium text-ink">
              Rebalancing
            </label>
            <select
              id={rebalanceId}
              class="control"
              value={rebalance()}
              onChange={(event) => setRebalance(event.currentTarget.value as RebalanceFrequency)}
            >
              <For each={REBALANCE_OPTIONS}>{(option) => <option value={option.value}>{option.label}</option>}</For>
            </select>
            <p class="max-w-[42ch] text-xs text-ink-faint">
              Rebalancing dates are anchored to the calendar, not to the start of your data, so two windows rebalance on
              the same dates. Trading costs and tax are not modelled.
            </p>
          </div>

          <div class="flex flex-col gap-1">
            <NumberInput
              label="Starting investment"
              value={initial()}
              onInput={setInitial}
              min={1}
              max={100_000_000}
              step={1000}
              hint="Scales the growth chart and nothing else. No return, ratio or drawdown depends on it."
            />
          </div>

          <fieldset class="flex flex-col gap-2">
            <legend class="text-sm font-medium text-ink">Period</legend>
            <div class="flex flex-wrap items-end gap-3">
              <label class="flex flex-col gap-1 text-sm text-ink">
                From
                <input
                  type="month"
                  class="control"
                  value={fromMonth() ?? availableWindow()?.first ?? ""}
                  min={availableWindow()?.first}
                  max={availableWindow()?.last}
                  onChange={(event) =>
                    setFromMonth(event.currentTarget.value === "" ? null : event.currentTarget.value)
                  }
                />
              </label>
              <label class="flex flex-col gap-1 text-sm text-ink">
                To
                <input
                  type="month"
                  class="control"
                  value={toMonth() ?? availableWindow()?.last ?? ""}
                  min={availableWindow()?.first}
                  max={availableWindow()?.last}
                  onChange={(event) => setToMonth(event.currentTarget.value === "" ? null : event.currentTarget.value)}
                />
              </label>
              <button
                type="button"
                class="control cursor-pointer"
                onClick={() => {
                  setFromMonth(null);
                  setToMonth(null);
                }}
              >
                Whole history
              </button>
            </div>
            <p class="max-w-[42ch] text-xs text-ink-faint">
              Clipped to the window every column covers. A request the data cannot honour, or one shorter than a year,
              falls back to the whole of it rather than emptying the page.
            </p>
          </fieldset>

          <Slider
            label="Risk-free rate, annual"
            value={riskFreePercent()}
            onInput={setRiskFreePercent}
            min={0}
            max={8}
            step={0.1}
            unit="%"
            showBounds
            hint="Used only for Sharpe. Held constant across the whole window and converted geometrically to a monthly rate."
          />

          <fieldset class="flex flex-col gap-2">
            <legend class="text-sm font-medium text-ink">Expenses</legend>
            <label for={expensesId} class="flex items-center gap-2 text-sm text-ink">
              <input
                id={expensesId}
                type="checkbox"
                checked={applyExpenses()}
                onChange={(event) => setApplyExpenses(event.currentTarget.checked)}
              />
              Charge each holding its expense ratio
            </label>
            <p class="max-w-[42ch] text-xs text-ink-faint">
              Off means the figures are gross of fees. If your pasted series is already net of them — most published
              fund returns are — leave this off, or you will charge the fee twice.
            </p>
            <Show when={applyExpenses()}>
              <div class="mt-1 flex flex-wrap gap-4">
                <For each={heldTickers()}>
                  {(ticker) => (
                    <NumberInput
                      label={`${ticker} expense ratio`}
                      value={expensePercent(ticker)}
                      onInput={(value) => setExpenses((current) => ({ ...current, [ticker]: value }))}
                      min={0}
                      max={5}
                      step={0.01}
                      unit="%"
                    />
                  )}
                </For>
              </div>
            </Show>
          </fieldset>
        </div>
      </Show>

      <Show when={blocked()}>
        {(reason) => (
          <Callout variant="caveat" label="Nothing to run yet">
            <p>{reason()}</p>
          </Callout>
        )}
      </Show>

      <Show when={ok()}>
        {(analysis) => (
          <div class="mt-8">
            <Show when={fromExample()}>
              <Callout variant="caveat" label="These results are of invented data">
                <p>
                  Every figure and every chart below was computed from the example series, which came out of a fixed
                  pseudo-random generator. The column names are your own tickers so that the controls work; the returns
                  under them belong to no fund and no market. Nothing here is a finding about anything.
                </p>
              </Callout>
            </Show>

            <div aria-live="polite" class="flex flex-wrap items-start gap-x-10 gap-y-4 border-y border-rule py-4">
              <Figure
                label="Common history"
                value={`${toYearMonth(analysis().range.start)} → ${toYearMonth(analysis().range.end)}`}
                size="sm"
              />
              <Figure
                label="Months tested"
                value={String(rangeLength(analysis().range))}
                note={`${(rangeLength(analysis().range) / MONTHS_PER_YEAR).toFixed(1)} years`}
                size="sm"
              />
              <Figure label="Benchmark" value={analysis().benchmark.id} size="sm" />
              <Show when={Math.abs(analysis().result.cashWeight) > CASH_EPSILON}>
                <Figure
                  label="Held in cash"
                  value={formatPercent(analysis().result.cashWeight, 1)}
                  note="Your weights do not sum to 100%. The remainder earns nothing; it is not scaled away."
                  size="sm"
                />
              </Show>
              <Show when={analysis().result.effectiveExpenseRatio !== 0}>
                <Figure
                  label="Weighted expense ratio"
                  value={formatPercent(analysis().result.effectiveExpenseRatio, 2)}
                  note="Charged monthly, geometrically."
                  size="sm"
                />
              </Show>
            </div>

            <Show when={boundary()}>
              {(edges) => (
                <p class="mt-3 max-w-measure text-sm text-ink-muted">
                  The test runs over the window every column covers. It starts in{" "}
                  <strong class="font-semibold text-ink">{toYearMonth(analysis().range.start)}</strong> because{" "}
                  {edges().startedBy.join(", ")} {edges().startedBy.length > 1 ? "start" : "starts"} there, and ends in{" "}
                  <strong class="font-semibold text-ink">{toYearMonth(analysis().range.end)}</strong> because{" "}
                  {edges().endedBy.join(", ")} {edges().endedBy.length > 1 ? "end" : "ends"} there. Nothing before or
                  after that window is used, and nothing is filled in.
                </p>
              )}
            </Show>

            <div class="mt-8">
              <div class="flex flex-wrap items-baseline justify-between gap-3">
                <h4 class="text-base font-semibold text-ink">Growth of {money(initial())}</h4>
                <label for={logId} class="flex items-center gap-2 text-sm text-ink">
                  <input
                    id={logId}
                    type="checkbox"
                    checked={logGrowth()}
                    onChange={(event) => setLogGrowth(event.currentTarget.checked)}
                  />
                  Ratio (log) value axis
                </label>
              </div>
              <TimeSeriesChart
                class="mt-3"
                series={growthSeries()}
                start={analysis().range.start - 1}
                logScale={logGrowth()}
                baseline={initial()}
                baselineLabel="starting value"
                valueAxisLabel={`Growth of ${money(initial())}`}
                ariaLabel={`Growth of ${money(initial())} invested, your portfolio against ${analysis().benchmark.id}, from ${toYearMonth(analysis().range.start)} to ${toYearMonth(analysis().range.end)}. The table below the chart carries the same figures.`}
                tableCaption={`Growth of ${money(initial())}, at each year end`}
                formatValue={money}
              />
            </div>

            <div class="mt-10">
              <h4 class="text-base font-semibold text-ink">Drawdown</h4>
              <TimeSeriesChart
                class="mt-3"
                series={drawdownSeries()}
                start={analysis().range.start - 1}
                baseline={0}
                baselineLabel="at a new high"
                valueAxisLabel="Below the previous peak"
                ariaLabel={`Fall below the previous month-end peak, your portfolio against ${analysis().benchmark.id}. The table below the chart carries the same figures.`}
                tableCaption="Drawdown at each year end"
                formatValue={(value) => `${(value * 100).toFixed(0)}%`}
              />
            </div>

            <div class="mt-10">
              <h4 class="text-base font-semibold text-ink">Rolling 3-year excess return</h4>
              <Show
                when={windows().length > 0}
                fallback={
                  <p class="mt-2 max-w-measure text-sm text-ink-muted">
                    The common history is shorter than three years, so there is no rolling window to show.
                  </p>
                }
              >
                <TimeSeriesChart
                  class="mt-3"
                  series={[
                    {
                      id: "excess",
                      label: "Excess, annualised",
                      abbr: "Excess",
                      values: windows().map((one) => one.excess),
                      emphasis: true,
                    },
                  ]}
                  start={analysis().range.start + ROLLING_MONTHS - 1}
                  baseline={0}
                  baselineLabel="level with the benchmark"
                  valueAxisLabel="Annualised excess"
                  ariaLabel={`Annualised return over each rolling 36-month window minus the benchmark's, ending in the month plotted. ${formatPercent(fractionAhead(windows()), 0)} of ${windows().length} windows finished ahead.`}
                  tableCaption="Rolling 3-year excess return, at each year end"
                  formatValue={(value) => `${(value * 100).toFixed(1)}%`}
                />
                <p class="mt-2 max-w-measure text-sm text-ink-muted">
                  Each point is a 36-month window ending that month, so consecutive points share 35 of their months.
                  Overlapping windows are not independent observations and the share ahead is not a significance test.
                </p>
              </Show>
            </div>

            <div class="mt-10">
              <h4 class="text-base font-semibold text-ink">Return by calendar year</h4>
              <Show
                when={years().length > 0}
                fallback={
                  <p class="mt-2 max-w-measure text-sm text-ink-muted">
                    The window contains no complete calendar year. Part-years are excluded rather than annualised,
                    because a nine-month year printed beside a twelve-month one is not a comparison.
                  </p>
                }
              >
                <DataTable
                  class="mt-3"
                  caption={`Calendar-year total return, your portfolio against ${analysis().benchmark.id}`}
                  captionHidden
                  columns={[
                    { key: "year", header: "Year", rowHeader: true, cell: (row: CalendarYear) => String(row.year) },
                    {
                      key: "portfolio",
                      header: "Portfolio",
                      numeric: true,
                      cell: (row: CalendarYear) => formatPercent(row.portfolio, 1),
                    },
                    {
                      key: "benchmark",
                      header: analysis().benchmark.id,
                      numeric: true,
                      cell: (row: CalendarYear) => (row.benchmark === null ? "—" : formatPercent(row.benchmark, 1)),
                    },
                    {
                      key: "excess",
                      header: "Difference",
                      numeric: true,
                      cell: (row: CalendarYear) =>
                        row.benchmark === null ? "—" : formatPercent(row.portfolio - row.benchmark, 1),
                    },
                  ]}
                  rows={years()}
                  footnote={
                    <>
                      Complete calendar years only. The difference is a difference of annual total returns, not a
                      compounded excess.
                    </>
                  }
                />
              </Show>
            </div>

            <div class="mt-10">
              <h4 class="text-base font-semibold text-ink">Metrics</h4>
              <DataTable
                class="mt-3"
                caption={`Your portfolio against ${analysis().benchmark.id}, ${toYearMonth(analysis().range.start)} to ${toYearMonth(analysis().range.end)}`}
                columns={[
                  { key: "metric", header: "Metric", rowHeader: true, cell: (row: MetricRow) => row.metric },
                  { key: "portfolio", header: "Portfolio", numeric: true, cell: (row: MetricRow) => row.portfolio },
                  {
                    key: "benchmark",
                    header: analysis().benchmark.id,
                    numeric: true,
                    cell: (row: MetricRow) => row.benchmark,
                  },
                ]}
                rows={metricRows()}
                footnote={
                  <>
                    Time-weighted monthly total returns,{" "}
                    {applyExpenses() ? "net of the expense ratios set above" : "gross of fees"}, rebalanced{" "}
                    {rebalance()}. Sharpe assumes a constant risk-free rate of {riskFreePercent().toFixed(1)}% a year.
                    Drawdowns are measured on month ends, so they understate the worst price actually seen. Trading
                    costs, bid-ask spreads and tax are not modelled.
                  </>
                }
              />
            </div>

            <details class="mt-6">
              <summary class="cursor-pointer py-2 text-sm text-ink-muted hover:text-ink">
                What each of these means, in plain English
              </summary>
              <dl class="mt-3 max-w-measure text-sm">
                <For each={DEFINITIONS}>
                  {(entry) => (
                    <div class="mt-3 first:mt-0">
                      <dt class="font-medium text-ink">{entry.term}</dt>
                      <dd class="mt-0.5 text-ink-muted">{entry.definition}</dd>
                    </div>
                  )}
                </For>
              </dl>
            </details>
          </div>
        )}
      </Show>
    </section>
  );
}

/** Default export so the lab can code-split it. */
export default HistoryPanel;
