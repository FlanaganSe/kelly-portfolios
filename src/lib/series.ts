/**
 * The site's portfolio series: what $10,000 did, month by month, for each printed
 * portfolio on two histories.
 *
 * The two JSON files under `src/content/series/` are written by
 * `cd research && uv run python -m portfolio_edge.reporting.site_series`, which rebuilds
 * every printed weight vector with the experiments' own machinery and refuses to emit
 * unless the research arms it re-simulates reproduce the committed artifact tables.
 * Nothing here computes a return; this module types, validates and hands out what the
 * emitter wrote. Every dollar figure is a simulation from index data, and
 * `SeriesFile.basis` says so in plain English; print it beside any number taken from here.
 */
import raw1929 from "~/content/series/portfolios-1929.json";
import raw1990 from "~/content/series/portfolios-1990.json";

export type SeriesWindow = "1990" | "1929";

export const SERIES_IDS = [
  "one-fund",
  "value-lean",
  "with-trend",
  "cautious",
  "cautious-30",
  "market",
  "sixty-forty",
] as const;
export type SeriesId = (typeof SERIES_IDS)[number];

export const EPISODE_IDS = ["dotcom-2000-02", "gfc-2008", "covid-2020", "rates-2022"] as const;
export type EpisodeId = (typeof EPISODE_IDS)[number];

/** The deepest peak-to-trough fall and the months from the peak to the first month back above it. */
export interface WorstFall {
  /** Signed, one decimal: −52.7 means the value fell 52.7%. */
  readonly pct: number;
  /** `YYYY-MM` of the peak month. */
  readonly peak: string;
  readonly trough: string;
  /** `null` while the fall is still open at the end of the window. */
  readonly recovered: string | null;
  readonly monthsToRecover: number | null;
  /** What $10,000 held at the peak was worth at the trough. */
  readonly dollarsAtTrough: number;
}

export interface YearReturn {
  readonly year: number;
  readonly pct: number;
}

export interface SinceWindow {
  readonly start: string;
  readonly final: number;
  readonly cagrPct: number;
  readonly worstFallPct: number;
}

export interface SeriesSummary {
  /** Dollars at the end of the window from $10,000 at the start. Equals the last value. */
  readonly final: number;
  /** Compound growth a year, two decimals. */
  readonly cagrPct: number;
  readonly worstFall: WorstFall;
  readonly bestYear: YearReturn | null;
  readonly worstYear: YearReturn | null;
  /** Every calendar year the window holds in full, `"1991": 20.1`. */
  readonly calendarYears: Readonly<Record<string, number>>;
  /** `null` where the window does not cover the episode. */
  readonly episodes: Readonly<Record<EpisodeId, number | null>>;
  readonly since2009: SinceWindow | null;
}

export interface PortfolioSeries {
  readonly id: SeriesId;
  readonly label: string;
  /** Percent of capital by ticker; sums to 100. The vector the emitter scored. */
  readonly weights: Readonly<Record<string, number>>;
  /** Whole dollars from 10,000, one per month, the base month first. */
  readonly values: readonly number[];
  /** `YYYY-MM`, one per value; the first is the month before the window opens. */
  readonly dates: readonly string[];
  readonly summary: SeriesSummary;
}

export interface SeriesFile {
  readonly generatedAt: string;
  readonly window: {
    readonly start: string;
    readonly end: string;
    readonly months: number;
    readonly label: string;
  };
  /** Plain English on what is simulated and what is not. Print it beside the numbers. */
  readonly basis: string;
  readonly episodeDefinitions: Readonly<Record<EpisodeId, string>>;
  readonly provenance: {
    readonly experiments: readonly string[];
    readonly artifacts: readonly string[];
    readonly manifests: readonly string[];
  };
  readonly start: number;
  readonly series: readonly PortfolioSeries[];
}

export class SeriesFormatError extends Error {
  constructor(where: string, message: string) {
    super(`${where}: ${message}`);
    this.name = "SeriesFormatError";
  }
}

const MONTH = /^\d{4}-\d{2}$/;
const WEIGHT_TOLERANCE = 1e-6;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function record(value: unknown, where: string): Record<string, unknown> {
  if (!isRecord(value)) throw new SeriesFormatError(where, "expected an object");
  return value;
}

function number(value: unknown, where: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new SeriesFormatError(where, `expected a finite number, got ${String(value)}`);
  }
  return value;
}

function text(value: unknown, where: string): string {
  if (typeof value !== "string" || value === "") throw new SeriesFormatError(where, "expected text");
  return value;
}

function month(value: unknown, where: string): string {
  const s = text(value, where);
  if (!MONTH.test(s)) throw new SeriesFormatError(where, `expected YYYY-MM, got ${s}`);
  return s;
}

function nullable<T>(value: unknown, parse: (v: unknown) => T): T | null {
  return value === null ? null : parse(value);
}

function list(value: unknown, where: string): readonly unknown[] {
  if (!Array.isArray(value)) throw new SeriesFormatError(where, "expected a list");
  return value;
}

function isSeriesId(value: string): value is SeriesId {
  return (SERIES_IDS as readonly string[]).includes(value);
}

function parseWorstFall(raw: unknown, where: string): WorstFall {
  const r = record(raw, where);
  return {
    pct: number(r.pct, `${where}.pct`),
    peak: month(r.peak, `${where}.peak`),
    trough: month(r.trough, `${where}.trough`),
    recovered: nullable(r.recovered, (v) => month(v, `${where}.recovered`)),
    monthsToRecover: nullable(r.monthsToRecover, (v) => number(v, `${where}.monthsToRecover`)),
    dollarsAtTrough: number(r.dollarsAtTrough, `${where}.dollarsAtTrough`),
  };
}

function parseYear(raw: unknown, where: string): YearReturn {
  const r = record(raw, where);
  return { year: number(r.year, `${where}.year`), pct: number(r.pct, `${where}.pct`) };
}

function parseNumberMap(raw: unknown, where: string): Record<string, number> {
  const r = record(raw, where);
  const out: Record<string, number> = {};
  for (const [key, value] of Object.entries(r)) out[key] = number(value, `${where}.${key}`);
  return out;
}

function parseEpisodes(raw: unknown, where: string): Record<EpisodeId, number | null> {
  const r = record(raw, where);
  const out = {} as Record<EpisodeId, number | null>;
  for (const id of EPISODE_IDS) {
    if (!(id in r)) throw new SeriesFormatError(where, `missing episode ${id}`);
    out[id] = nullable(r[id], (v) => number(v, `${where}.${id}`));
  }
  return out;
}

function parseSummary(raw: unknown, where: string): SeriesSummary {
  const r = record(raw, where);
  return {
    final: number(r.final, `${where}.final`),
    cagrPct: number(r.cagrPct, `${where}.cagrPct`),
    worstFall: parseWorstFall(r.worstFall, `${where}.worstFall`),
    bestYear: nullable(r.bestYear, (v) => parseYear(v, `${where}.bestYear`)),
    worstYear: nullable(r.worstYear, (v) => parseYear(v, `${where}.worstYear`)),
    calendarYears: parseNumberMap(r.calendarYears, `${where}.calendarYears`),
    episodes: parseEpisodes(r.episodes, `${where}.episodes`),
    since2009: nullable(r.since2009, (v) => {
      const s = record(v, `${where}.since2009`);
      return {
        start: month(s.start, `${where}.since2009.start`),
        final: number(s.final, `${where}.since2009.final`),
        cagrPct: number(s.cagrPct, `${where}.since2009.cagrPct`),
        worstFallPct: number(s.worstFallPct, `${where}.since2009.worstFallPct`),
      };
    }),
  };
}

function parseSeries(raw: unknown, where: string, months: number, start: number): PortfolioSeries {
  const r = record(raw, where);
  const id = text(r.id, `${where}.id`);
  if (!isSeriesId(id)) throw new SeriesFormatError(where, `unknown series id ${id}`);
  const values = list(r.values, `${where}.values`).map((v, i) => number(v, `${where}.values[${i}]`));
  const dates = list(r.dates, `${where}.dates`).map((v, i) => month(v, `${where}.dates[${i}]`));
  if (values.length !== months + 1 || dates.length !== months + 1) {
    throw new SeriesFormatError(where, `expected ${months + 1} values and dates, got ${values.length}/${dates.length}`);
  }
  if (values[0] !== start) throw new SeriesFormatError(where, `first value must be ${start}`);
  const weights = parseNumberMap(r.weights, `${where}.weights`);
  const total = Object.values(weights).reduce((sum, w) => sum + w, 0);
  if (Math.abs(total - 100) > WEIGHT_TOLERANCE) {
    throw new SeriesFormatError(where, `weights sum to ${total}, not 100`);
  }
  const summary = parseSummary(r.summary, `${where}.summary`);
  const last = values[values.length - 1];
  if (summary.final !== last) {
    throw new SeriesFormatError(where, `summary.final ${summary.final} is not the last value ${String(last)}`);
  }
  return { id, label: text(r.label, `${where}.label`), weights, values, dates, summary };
}

/** Validate one emitted file. Throws `SeriesFormatError` naming the field that failed. */
export function parseSeriesFile(raw: unknown): SeriesFile {
  const r = record(raw, "series file");
  const w = record(r.window, "window");
  const months = number(w.months, "window.months");
  const start = number(r.start, "start");
  const provenance = record(r.provenance, "provenance");
  const definitions = record(r.episodeDefinitions, "episodeDefinitions");
  const episodeDefinitions = {} as Record<EpisodeId, string>;
  for (const id of EPISODE_IDS) episodeDefinitions[id] = text(definitions[id], `episodeDefinitions.${id}`);
  const series = list(r.series, "series").map((item, i) => parseSeries(item, `series[${i}]`, months, start));
  const ids = new Set(series.map((s) => s.id));
  if (ids.size !== series.length) throw new SeriesFormatError("series", "an id appears twice");
  return {
    generatedAt: text(r.generatedAt, "generatedAt"),
    window: {
      start: month(w.start, "window.start"),
      end: month(w.end, "window.end"),
      months,
      label: text(w.label, "window.label"),
    },
    basis: text(r.basis, "basis"),
    episodeDefinitions,
    provenance: {
      experiments: list(provenance.experiments, "provenance.experiments").map((v, i) =>
        text(v, `provenance.experiments[${i}]`)
      ),
      artifacts: list(provenance.artifacts, "provenance.artifacts").map((v, i) =>
        text(v, `provenance.artifacts[${i}]`)
      ),
      manifests: list(provenance.manifests, "provenance.manifests").map((v, i) =>
        text(v, `provenance.manifests[${i}]`)
      ),
    },
    start,
    series,
  };
}

const RAW: Readonly<Record<SeriesWindow, unknown>> = { "1990": raw1990, "1929": raw1929 };
const cache = new Map<SeriesWindow, SeriesFile>();

/** The validated file for one window; parsed once. */
export function loadSeries(window: SeriesWindow = "1990"): SeriesFile {
  const cached = cache.get(window);
  if (cached !== undefined) return cached;
  const parsed = parseSeriesFile(RAW[window]);
  cache.set(window, parsed);
  return parsed;
}

/** One series by id. Throws when the window does not carry it (the 1929 file has no value lean). */
export function seriesFor(id: SeriesId, window: SeriesWindow = "1990"): PortfolioSeries {
  const found = loadSeries(window).series.find((s) => s.id === id);
  if (found === undefined) throw new Error(`No series ${id} on the ${window} window`);
  return found;
}

/** The headline numbers for one series: final dollars, growth, worst fall, years, episodes. */
export function portfolioSummary(id: SeriesId, window: SeriesWindow = "1990"): SeriesSummary {
  return seriesFor(id, window).summary;
}
