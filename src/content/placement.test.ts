import { describe, expect, it } from "vitest";
import { foreignSleeves, shelterCandidates, taxRegimes } from "~/content/placement";
import fixtures from "~/lib/fixtures/research-ground-truth.json";
import { forfeitedBp, form1116ThresholdAssets, locationBreakevenRate, shelterPriorityBp } from "~/lib/placement";

const RELATIVE_TOLERANCE = 1e-9;

function expectClose(actual: number, expected: number): void {
  const tolerance = Math.max(Math.abs(expected) * RELATIVE_TOLERANCE, 1e-12);
  expect(Math.abs(actual - expected)).toBeLessThanOrEqual(tolerance);
}

/** Fixture lookup that fails loudly, since non-null assertions are banned. */
function byLabel<T extends { label: string }>(items: readonly T[], label: string): T {
  const found = items.find((item) => item.label === label);
  if (found === undefined) throw new Error(`no entry labelled ${label}`);
  return found;
}

/**
 * The content constants are the inputs the pages compute from, so they are checked
 * against the research workspace's own output rather than against each other. If these
 * fail, the constants in `~/content/placement` are wrong, never the fixture.
 */
describe("content constants against the research fixture", () => {
  it("carries the same regimes, candidates and sleeves the workspace generated", () => {
    expect(taxRegimes.map((regime) => regime.label)).toEqual(fixtures.regimes.map((regime) => regime.label));

    for (const regime of taxRegimes) {
      const expected = byLabel(fixtures.regimes, regime.label);
      expect(regime.asOf).toBe(expected.asOf);
      expectClose(regime.ordinaryIncome, expected.ordinaryIncome);
      expectClose(regime.longTermCapitalGain, expected.longTermCapitalGain);
      expectClose(regime.netInvestmentIncome, expected.netInvestmentIncome);
    }

    for (const candidate of shelterCandidates) {
      const expected = byLabel(fixtures.shelterCandidates, candidate.label);
      expectClose(candidate.dividendYield, expected.dividendYield);
      expectClose(candidate.qualifiedFraction, expected.qualifiedFraction);
      expectClose(candidate.foreignWithholdingRate, expected.foreignWithholdingRate);
    }

    for (const sleeve of foreignSleeves) {
      const expected = byLabel(fixtures.foreignSleeves, sleeve.label);
      expectClose(sleeve.dividendYield, expected.dividendYield);
      expectClose(sleeve.withholdingRate, expected.withholdingRate);
    }
  });

  it("reproduces the shelterPriority ranking in all three regimes", () => {
    expect(fixtures.shelterPriority).toHaveLength(3);

    for (const expected of fixtures.shelterPriority) {
      const regime = byLabel(taxRegimes, expected.regime);
      const ranking = shelterPriorityBp(shelterCandidates, {
        regime,
        foreignCreditUtilisation: expected.foreignCreditUtilisation,
      });

      expect(ranking.map((row) => row.label)).toEqual(expected.ranking.map((row) => row.label));
      for (const [index, row] of ranking.entries()) {
        const target = expected.ranking[index];
        if (target === undefined) throw new Error("fixture ranking is shorter than the computed one");
        expectClose(row.priorityBp, target.priorityBp);
      }
    }
  });

  it("reproduces the forfeiture, break-even and Form 1116 thresholds for both sleeves", () => {
    const domesticDividendYield = byLabel(shelterCandidates, "US equity").dividendYield;

    for (const sleeve of foreignSleeves) {
      const expected = byLabel(fixtures.foreignSleeves, sleeve.label);
      expectClose(forfeitedBp(sleeve), expected.forfeitedBp);
      expectClose(
        locationBreakevenRate({ international: sleeve, domesticDividendYield }),
        expected.breakevenQualifiedRate
      );
      expectClose(form1116ThresholdAssets({ foreignTaxLimit: 300, sleeve }), expected.form1116SingleAssets);
      expectClose(form1116ThresholdAssets({ foreignTaxLimit: 600, sleeve }), expected.form1116JointAssets);
    }
  });
});
