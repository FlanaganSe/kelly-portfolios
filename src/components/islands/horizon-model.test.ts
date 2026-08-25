import { readFileSync } from "node:fs";
import * as yaml from "js-yaml";
import { describe, expect, it } from "vitest";
import {
  againstAWorkingLife,
  bpFromPercent,
  chanceAhead,
  formatChance,
  percentFromBp,
  timeToKnow,
} from "~/components/islands/horizon-model";
import { horizonPresets, PORTFOLIO_EDGE_BP, PORTFOLIO_TRACKING_ERROR_BP } from "~/components/islands/horizon-presets";
import { formatYears } from "~/lib/format";

const NINETY = 0.9;

/** The wait a preset produces, formatted the way the tool prints it. */
function waitFor(id: string): string {
  const preset = horizonPresets.find((entry) => entry.id === id);
  if (preset === undefined) throw new Error(`no preset "${id}"`);
  const outcome = timeToKnow({
    edgeBp: preset.edgeBp,
    trackingErrorBp: preset.trackingErrorBp,
    confidence: NINETY,
  });
  if (outcome.kind !== "years") throw new Error(`preset "${id}" has no finite horizon`);
  return formatYears(outcome.years);
}

describe("percent and basis points", () => {
  it("round-trips without float dust", () => {
    for (const bp of [5.4, 41, 46, 89, 92, 109, 313, 400]) {
      expect(bpFromPercent(percentFromBp(bp))).toBe(bp);
    }
  });

  it("reads 0.89 as 89 basis points", () => {
    expect(bpFromPercent(0.89)).toBe(89);
  });
});

describe("timeToKnow", () => {
  it("puts the fee and tax package at about four months", () => {
    expect(waitFor("structural")).toBe("3.5 months");
    expect(waitFor("structural-2025")).toBe("4.2 months");
  });

  it("puts the whole portfolio against a cheap index fund at 31 years", () => {
    expect(waitFor("whole-portfolio")).toBe("31 years");
  });

  it("lands at once when there is nothing to wander", () => {
    expect(timeToKnow({ edgeBp: 50, trackingErrorBp: 0, confidence: NINETY })).toEqual({ kind: "immediate" });
  });

  it("has no answer for an edge that is not positive", () => {
    expect(timeToKnow({ edgeBp: 0, trackingErrorBp: 100, confidence: NINETY })).toEqual({ kind: "never" });
    expect(timeToKnow({ edgeBp: -20, trackingErrorBp: 100, confidence: NINETY })).toEqual({ kind: "never" });
  });

  it("quadruples the wait when the edge halves, which is the whole finding", () => {
    const one = timeToKnow({ edgeBp: 100, trackingErrorBp: 400, confidence: NINETY });
    const half = timeToKnow({ edgeBp: 50, trackingErrorBp: 400, confidence: NINETY });
    if (one.kind !== "years" || half.kind !== "years") throw new Error("both should be finite");
    expect(half.years / one.years).toBeCloseTo(4, 10);
  });
});

describe("chanceAhead", () => {
  it("is a coin flip at a horizon of nothing much and rises with time", () => {
    const ten = chanceAhead({ edgeBp: 92, trackingErrorBp: 400, horizonYears: 10 });
    const thirty = chanceAhead({ edgeBp: 92, trackingErrorBp: 400, horizonYears: 30 });
    expect(ten).toBeGreaterThan(0.5);
    expect(thirty).toBeGreaterThan(ten);
    expect(thirty).toBeLessThan(NINETY);
  });

  it("is certainty when there is no drift", () => {
    expect(chanceAhead({ edgeBp: 109, trackingErrorBp: 0, horizonYears: 1 })).toBe(1);
  });
});

describe("formatChance", () => {
  it("never prints 100% for something short of it", () => {
    expect(formatChance(0.9999)).toBe("over 99%");
    expect(formatChance(1)).toBe("over 99%");
    expect(formatChance(0.716)).toBe("72%");
  });
});

describe("againstAWorkingLife", () => {
  it("says how the wait compares with forty years", () => {
    expect(againstAWorkingLife({ kind: "years", years: 0.29 })).toContain("Inside a year");
    expect(againstAWorkingLife({ kind: "years", years: 31 })).toContain("working life");
    expect(againstAWorkingLife({ kind: "years", years: 164 })).toContain("4.1 working lives");
    expect(againstAWorkingLife({ kind: "never" })).toContain("not positive");
    expect(againstAWorkingLife({ kind: "immediate" })).toContain("day you make the switch");
  });
});

/**
 * The two portfolio-level numbers have their canonical home in the figure collection,
 * which an island cannot import. This is the guard that keeps the copy honest.
 */
describe("the preset numbers against the figure records they came from", () => {
  const figure = (id: string) =>
    yaml.load(readFileSync(`src/content/figures/${id}.yaml`, "utf8")) as { label: string; value: string };

  it("matches thirty-year-edge.yaml", () => {
    expect(figure("thirty-year-edge").value).toBe(`${(PORTFOLIO_EDGE_BP / 100).toFixed(2)}%`);
  });

  it("matches tracking-error.yaml", () => {
    expect(figure("tracking-error").value).toBe(`${(PORTFOLIO_TRACKING_ERROR_BP / 100).toFixed(2)}%`);
  });

  it("matches the wait time-to-know-portfolio.yaml prints", () => {
    expect(figure("time-to-know-portfolio").value).toBe(waitFor("whole-portfolio"));
  });
});
