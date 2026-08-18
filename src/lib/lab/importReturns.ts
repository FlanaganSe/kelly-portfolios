/**
 * The reader's own return history, pasted in.
 *
 * This repository ships no price data: there is no research-grade free source
 * (decision 0002) and no established right to redistribute a public factor library.
 * The honest way to run the engine in `src/lib/backtest/` is therefore to let a reader
 * paste a series they already have. Nothing here uploads, stores or transmits anything;
 * this module is a pure function from text to `ReturnSeries[]`.
 *
 * Three rules make the difference between a parser and a fabricator:
 *
 * 1. **A gap is never filled.** A ticker missing an interior month is reported by name
 *    and month and left out entirely. The engine's whole contract is that a
 *    `ReturnSeries` is contiguous, and a zero for a month nobody observed is an invented
 *    observation with the most flattering possible value.
 * 2. **Percent is never inferred from magnitude.** `1.23` is +123% and `1.23%` is
 *    +1.23%, and no amount of "these look like percentages" reasoning is allowed to
 *    decide which. A `%` sign anywhere in a column marks the whole column.
 * 3. **User input never throws.** Every refusal comes back as an `ImportProblem` so the
 *    interface can name it. Exceptions here would be programmer error.
 */

import { toMonthIndex, toYearMonth } from "~/lib/backtest/calendar";
import type { MonthIndex, ReturnSeries } from "~/lib/backtest/types";

export type ImportProblemKind =
  | "empty-paste"
  | "missing-header"
  | "no-tickers"
  | "no-rows"
  | "unnamed-column"
  | "duplicate-column"
  | "extra-cells"
  | "bad-date"
  | "bad-value"
  | "duplicate-month"
  | "gap"
  | "empty-column";

export interface ImportProblem {
  readonly kind: ImportProblemKind;
  /** Ready to print. Names the ticker and the month whenever the problem has them. */
  readonly message: string;
  /** The column this belongs to, when it belongs to one. */
  readonly ticker?: string;
  /** `"YYYY-MM"`. The month the problem is about. */
  readonly month?: string;
  /** 1-based line in the pasted text, counting blank lines. */
  readonly line?: number;
}

export interface ImportResult {
  /** In the order the columns appeared. Excludes every column that had a problem. */
  readonly series: readonly ReturnSeries[];
  readonly problems: readonly ImportProblem[];
}

/** `YYYY-MM` or `YYYY-MM-DD`. A day is read and discarded: the engine is monthly. */
const DATE = /^(\d{4})-(\d{2})(?:-(\d{2}))?$/;

const BOM = "﻿";

/**
 * One line into cells, RFC 4180 quoting.
 *
 * A quote only opens a field when nothing but whitespace precedes it, so an apostrophe
 * or an inches mark inside an unquoted cell is left alone rather than swallowing the
 * rest of the row.
 */
function splitLine(line: string, delimiter: string): string[] {
  const cells: string[] = [];
  let current = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line.charAt(index);
    if (quoted) {
      if (char !== '"') {
        current += char;
      } else if (line.charAt(index + 1) === '"') {
        current += '"';
        index += 1;
      } else {
        quoted = false;
      }
      continue;
    }
    if (char === '"' && current.trim() === "") {
      quoted = true;
      current = "";
    } else if (char === delimiter) {
      cells.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  cells.push(current);
  return cells;
}

/** Tab wins when the header has any, because a tab is never decorative. */
function detectDelimiter(header: string): string {
  return header.includes("\t") ? "\t" : ",";
}

function parseMonth(raw: string): MonthIndex | null {
  const match = DATE.exec(raw.trim());
  if (match === null) {
    return null;
  }
  const month = Number(match[2]);
  if (month < 1 || month > 12) {
    return null;
  }
  return toMonthIndex(`${match[1]}-${match[2]}`);
}

/**
 * A cell to a number, before any percent conversion.
 *
 * Thousands separators are deliberately not stripped: `1,23` is a decimal comma in half
 * of Europe and a thousands separator in the other half, and a monthly return has no
 * business needing either. An ambiguous cell is refused, not guessed.
 */
function parseValue(raw: string): number | null {
  const cleaned = raw.replace(/%/g, "").replace(/^\+/, "").trim();
  if (cleaned === "") {
    return null;
  }
  const parsed = Number(cleaned);
  return Number.isFinite(parsed) ? parsed : null;
}

/** What one column has accumulated while the rows are read. */
interface Column {
  readonly ticker: string;
  readonly values: Map<MonthIndex, number>;
  /** Set by a `%` anywhere in the column, and applied to every cell in it. */
  percent: boolean;
  /** Once a column is rejected its remaining cells are still read, but never used. */
  rejected: boolean;
}

const PERCENT_DIVISOR = 100;

function readHeader(cells: readonly string[], problems: ImportProblem[]): Map<number, Column> {
  const columns = new Map<number, Column>();
  const seen = new Set<string>();
  for (let index = 1; index < cells.length; index += 1) {
    const ticker = (cells[index] ?? "").trim();
    if (ticker === "") {
      problems.push({
        kind: "unnamed-column",
        message: `Column ${index + 1} has no heading, so there is nothing to call the series. It was skipped.`,
        line: 1,
      });
      continue;
    }
    if (seen.has(ticker)) {
      problems.push({
        kind: "duplicate-column",
        ticker,
        message: `${ticker} appears as a heading more than once. Only the first column with that name was read.`,
        line: 1,
      });
      continue;
    }
    seen.add(ticker);
    columns.set(index, { ticker, values: new Map(), percent: false, rejected: false });
  }
  return columns;
}

function reject(column: Column, problems: ImportProblem[], problem: ImportProblem): void {
  column.rejected = true;
  problems.push(problem);
}

function readRow(
  cells: readonly string[],
  month: MonthIndex,
  columns: ReadonlyMap<number, Column>,
  problems: ImportProblem[]
): void {
  for (const [index, column] of columns) {
    const raw = cells[index] ?? "";
    if (raw.includes("%")) {
      column.percent = true;
    }
    const trimmed = raw.trim();
    // A blank is an absence, never a zero. Whether it is a trim or a gap is decided
    // later, once the whole column is known.
    if (trimmed === "") {
      continue;
    }
    const value = parseValue(trimmed);
    if (value === null) {
      if (!column.rejected) {
        reject(column, problems, {
          kind: "bad-value",
          ticker: column.ticker,
          month: toYearMonth(month),
          message: `${column.ticker} has "${trimmed}" for ${toYearMonth(month)}, which is not a number. The series was not imported.`,
        });
      }
      continue;
    }
    if (column.values.has(month)) {
      if (!column.rejected) {
        reject(column, problems, {
          kind: "duplicate-month",
          ticker: column.ticker,
          month: toYearMonth(month),
          message: `${column.ticker} has two values for ${toYearMonth(month)}. The series was not imported: only you know which is right.`,
        });
      }
      continue;
    }
    column.values.set(month, value);
  }
}

/** The first month between the first and last observation that has no value. */
function firstGap(months: readonly MonthIndex[]): MonthIndex | null {
  for (let index = 1; index < months.length; index += 1) {
    const previous = months[index - 1];
    const current = months[index];
    if (previous === undefined || current === undefined) {
      continue;
    }
    if (current !== previous + 1) {
      return previous + 1;
    }
  }
  return null;
}

function countMissing(months: readonly MonthIndex[]): number {
  const first = months[0];
  const last = months[months.length - 1];
  if (first === undefined || last === undefined) {
    return 0;
  }
  return last - first + 1 - months.length;
}

function buildSeries(column: Column, problems: ImportProblem[]): ReturnSeries | null {
  if (column.rejected) {
    return null;
  }
  if (column.values.size === 0) {
    problems.push({
      kind: "empty-column",
      ticker: column.ticker,
      message: `${column.ticker} has a heading but no values.`,
    });
    return null;
  }

  const months = [...column.values.keys()].sort((a, b) => a - b);
  const missing = firstGap(months);
  if (missing !== null) {
    const total = countMissing(months);
    const extra = total > 1 ? ` (${total} months are missing in all)` : "";
    problems.push({
      kind: "gap",
      ticker: column.ticker,
      month: toYearMonth(missing),
      message: `${column.ticker} has no value for ${toYearMonth(missing)}${extra}. A gap is never filled in, so the series was not imported. Every other column still was.`,
    });
    return null;
  }

  const start = months[0];
  if (start === undefined) {
    return null;
  }
  const divisor = column.percent ? PERCENT_DIVISOR : 1;
  return {
    id: column.ticker,
    start,
    returns: months.map((month) => (column.values.get(month) ?? 0) / divisor),
  };
}

/**
 * Wide CSV or TSV to return series. Never throws on user input.
 *
 * The first column is the month, as `YYYY-MM` or `YYYY-MM-DD`; every other column is one
 * ticker, named by the header row the format requires. Rows may arrive in any order.
 */
export function importReturns(text: string): ImportResult {
  const problems: ImportProblem[] = [];
  const lines = text.replace(BOM, "").split(/\r\n|\r|\n/);

  const numbered = lines.map((line, index) => ({ line, number: index + 1 })).filter((one) => one.line.trim() !== "");
  const header = numbered[0];
  if (header === undefined) {
    problems.push({
      kind: "empty-paste",
      message: "There is nothing to import yet. Paste your monthly returns above.",
    });
    return { series: [], problems };
  }

  const delimiter = detectDelimiter(header.line);
  const headerCells = splitLine(header.line, delimiter);
  const firstCell = (headerCells[0] ?? "").trim();
  if (parseMonth(firstCell) !== null) {
    problems.push({
      kind: "missing-header",
      line: header.number,
      message: `The first row is data (${firstCell}), not headings. Add a row naming the month column and one ticker per column.`,
    });
    return { series: [], problems };
  }

  const columns = readHeader(headerCells, problems);
  if (columns.size === 0) {
    problems.push({
      kind: "no-tickers",
      line: header.number,
      message: "No ticker columns were found. The first column is the month; each column after it is one holding.",
    });
    return { series: [], problems };
  }

  const rows = numbered.slice(1);
  if (rows.length === 0) {
    problems.push({ kind: "no-rows", message: "The paste has headings but no months under them." });
    return { series: [], problems };
  }

  for (const row of rows) {
    const cells = splitLine(row.line, delimiter);
    if (cells.length > headerCells.length) {
      problems.push({
        kind: "extra-cells",
        line: row.number,
        message: `Line ${row.number} has ${cells.length} values for ${headerCells.length} columns. The extra ones were ignored.`,
      });
    }
    const month = parseMonth(cells[0] ?? "");
    if (month === null) {
      problems.push({
        kind: "bad-date",
        line: row.number,
        message: `Line ${row.number} starts with "${(cells[0] ?? "").trim()}", which is not a month. Use YYYY-MM or YYYY-MM-DD. The line was skipped.`,
      });
      continue;
    }
    readRow(cells, month, columns, problems);
  }

  const series: ReturnSeries[] = [];
  for (const column of columns.values()) {
    const built = buildSeries(column, problems);
    if (built !== null) {
      series.push(built);
    }
  }
  return { series, problems };
}
