// @vitest-environment node
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { ledgerSummary } from "~/content/experiments";

/**
 * `ledgerSummary` is the one place the client states how much searching was done,
 * and a search count quoted without being checked is exactly the failure the
 * ledger exists to prevent. It had drifted three generations behind
 * `research/ledger.jsonl` — 93/33/15/12 against an actual 116/41/21/17 — because
 * nothing compared them. This does.
 *
 * The ledger is an append-only event log, so current state is a fold over it.
 */

type Entry = {
  run_id: string;
  experiment_family: string;
  spec_hash: string | null;
  status: string;
  result_status: string | null;
  results_viewed: boolean;
  consumes_final_holdout: boolean;
};

const entries: Entry[] = readFileSync(join(import.meta.dirname, "..", "..", "research", "ledger.jsonl"), "utf8")
  .split("\n")
  .filter((line) => line.trim() !== "")
  .map((line) => JSON.parse(line) as Entry);

const runs = new Map<string, Entry[]>();
for (const entry of entries) {
  const found = runs.get(entry.run_id);
  if (found) found.push(entry);
  else runs.set(entry.run_id, [entry]);
}

/** The last result status a run recorded, or null if it never reached one. */
function terminalStatus(events: Entry[]): string | null {
  const reached = events.map((e) => e.result_status).filter((s): s is string => s !== null);
  return reached.at(-1) ?? null;
}

describe("the shipped ledger summary matches the ledger", () => {
  it("counts entries, runs, specifications and families", () => {
    expect({
      entries: entries.length,
      runs: runs.size,
      distinctSpecifications: new Set(entries.map((e) => e.spec_hash).filter((h): h is string => Boolean(h))).size,
      experimentFamilies: new Set(entries.map((e) => e.experiment_family)).size,
    }).toEqual({
      entries: ledgerSummary.entries,
      runs: ledgerSummary.runs,
      distinctSpecifications: ledgerSummary.distinctSpecifications,
      experimentFamilies: ledgerSummary.experimentFamilies,
    });
  });

  it("counts the runs that recorded a look at their results", () => {
    const viewed = [...runs.values()].filter((events) => events.some((e) => e.results_viewed)).length;
    expect(viewed).toBe(ledgerSummary.runsRecordingResultsViewed);
  });

  it("still records that no run consumed the final holdout", () => {
    const consumed = [...runs.values()].filter((events) => events.some((e) => e.consumes_final_holdout)).length;
    expect(consumed).toBe(ledgerSummary.runsConsumingTheFinalHoldout);
    expect(consumed).toBe(0);
  });

  it("counts the runs behind every terminal outcome it publishes", () => {
    const actual = new Map<string, number>();
    let unfinished = 0;
    for (const events of runs.values()) {
      const status = terminalStatus(events);
      if (status === null) unfinished += 1;
      else actual.set(status, (actual.get(status) ?? 0) + 1);
    }
    for (const outcome of ledgerSummary.terminalOutcomes) {
      expect(actual.get(outcome.status), outcome.status).toBe(outcome.runs);
    }
    expect(unfinished).toBe(ledgerSummary.noTerminalStatus.runs);
  });

  it("publishes every terminal status the ledger holds, so none is omitted", () => {
    const inLedger = new Set([...runs.values()].map(terminalStatus).filter((s): s is string => s !== null));
    const published = new Set<string>(ledgerSummary.terminalOutcomes.map((o) => o.status));
    expect([...inLedger].filter((s) => !published.has(s))).toEqual([]);
  });
});
