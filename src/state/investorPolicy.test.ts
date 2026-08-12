import { beforeAll, beforeEach, describe, expect, it } from "vitest";
import { foreignSleeves, shelterCandidates, taxRegimes } from "~/content/placement";
import fixtures from "~/lib/fixtures/research-ground-truth.json";
import { forfeitedBp, form1116ThresholdAssets, locationBreakevenRate, shelterPriorityBp } from "~/lib/placement";
import {
  createInvestorPolicyStore,
  POLICY_STORAGE_KEY,
  POLICY_VERSION,
  parseStoredPolicy,
  REFERENCE_INVESTOR,
  resolvePolicy,
  serialisePolicy,
} from "~/state/investorPolicy";

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
 * fail, the constants in `~/content/placement` are wrong — never the fixture.
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
        if (target === undefined) throw new Error(`fixture ranking is shorter than the computed one`);
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

describe("resolvePolicy", () => {
  it("renders the reference investor from an empty policy", () => {
    const resolved = resolvePolicy({});

    expect(resolved.isEmpty).toBe(true);
    expect(resolved.regimeId).toBe(REFERENCE_INVESTOR.regimeId);
    expect(resolved.regime.label).toBe("US top marginal bracket");
    expect(resolved.horizonYears).toBe(30);
    expect(resolved.contributionsContinue).toBe(true);
    expect(resolved.withdrawalsBegun).toBe(false);
    expect(resolved.hasHighDeductiblePlan).toBe(false);
    expect(resolved.foreignCreditUtilisation).toBe(1);
    expect(resolved.accounts).toEqual({});
    expect(Object.values(resolved.defaulted).every(Boolean)).toBe(true);
  });

  it("marks only the entered fields as supplied", () => {
    const resolved = resolvePolicy({ horizonYears: 12 });

    expect(resolved.horizonYears).toBe(12);
    expect(resolved.isEmpty).toBe(false);
    expect(resolved.defaulted.horizonYears).toBe(false);
    expect(resolved.defaulted.regimeId).toBe(true);
  });

  it("builds an undated regime from custom rates", () => {
    const resolved = resolvePolicy({
      regimeId: "custom",
      customRegime: { ordinaryIncome: 0.32, longTermCapitalGain: 0.15, netInvestmentIncome: 0.038 },
    });

    expect(resolved.regimeId).toBe("custom");
    expect(resolved.regime.ordinaryIncome).toBe(0.32);
    expect(resolved.regime.asOf).toBe("");
  });

  it("falls back to the reference bracket when custom is selected with no rates", () => {
    const resolved = resolvePolicy({ regimeId: "custom" });

    expect(resolved.regimeId).toBe(REFERENCE_INVESTOR.regimeId);
    expect(resolved.regime.label).toBe("US top marginal bracket");
  });
});

describe("parseStoredPolicy", () => {
  it("discards malformed JSON rather than throwing", () => {
    expect(parseStoredPolicy("{not json")).toEqual({});
    expect(parseStoredPolicy("null")).toEqual({});
    expect(parseStoredPolicy("[1,2,3]")).toEqual({});
    expect(parseStoredPolicy(null)).toEqual({});
  });

  it("discards an unknown version outright", () => {
    const payload = JSON.stringify({ version: POLICY_VERSION + 1, horizonYears: 12, regimeId: "us-upper-middle" });
    expect(parseStoredPolicy(payload)).toEqual({});
    expect(parseStoredPolicy(JSON.stringify({ horizonYears: 12 }))).toEqual({});
  });

  it("drops fields of the wrong type or out of range, keeping the rest", () => {
    const payload = JSON.stringify({
      version: POLICY_VERSION,
      regimeId: "sepia",
      horizonYears: "thirty",
      contributionsContinue: "yes",
      foreignCreditUtilisation: 4,
      accounts: { taxable: 1000, roth: -5, hsa: "lots" },
      hasHighDeductiblePlan: true,
    });

    expect(parseStoredPolicy(payload)).toEqual({ accounts: { taxable: 1000 }, hasHighDeductiblePlan: true });
  });

  it("keeps a whole valid payload", () => {
    const policy = {
      regimeId: "us-upper-middle" as const,
      horizonYears: 18,
      contributionsContinue: false,
      withdrawalsBegun: true,
      accounts: { taxable: 250_000, traditional: 100_000 },
      hasHighDeductiblePlan: true,
      foreignCreditUtilisation: 0.5,
    };

    expect(parseStoredPolicy(serialisePolicy(policy))).toEqual(policy);
  });
});

describe("the store", () => {
  // Node 22 defines a global `localStorage` that is undefined unless the process was
  // started with --localstorage-file, and under jsdom the window *is* the global, so it
  // shadows jsdom's own. sessionStorage survives and is the same `Storage` class, so
  // the store still runs against a real implementation rather than a hand-rolled stub.
  beforeAll(() => {
    if (globalThis.localStorage === undefined) {
      Object.defineProperty(globalThis, "localStorage", { configurable: true, value: window.sessionStorage });
    }
  });

  beforeEach(() => {
    localStorage.clear();
  });

  it("starts empty when storage is empty", () => {
    const store = createInvestorPolicyStore();

    expect(store.policy).toEqual({});
    expect(store.resolved().isEmpty).toBe(true);
    expect(store.resolved().regime.label).toBe("US top marginal bracket");
  });

  it("round-trips through localStorage", () => {
    const store = createInvestorPolicyStore();
    store.update({ regimeId: "us-upper-middle", horizonYears: 20 });

    expect(localStorage.getItem(POLICY_STORAGE_KEY)).toContain(`"version":${POLICY_VERSION}`);

    const reloaded = createInvestorPolicyStore();
    expect(reloaded.policy.regimeId).toBe("us-upper-middle");
    expect(reloaded.resolved().horizonYears).toBe(20);
    expect(reloaded.resolved().regime.ordinaryIncome).toBe(0.24);
  });

  it("starts empty on a malformed payload", () => {
    localStorage.setItem(POLICY_STORAGE_KEY, "{ half a payl");
    const store = createInvestorPolicyStore();

    expect(store.policy).toEqual({});
    expect(store.resolved().isEmpty).toBe(true);
  });

  it("starts empty on an unknown version", () => {
    localStorage.setItem(POLICY_STORAGE_KEY, JSON.stringify({ version: 99, regimeId: "us-upper-middle" }));
    const store = createInvestorPolicyStore();

    expect(store.policy).toEqual({});
    expect(store.resolved().regimeId).toBe(REFERENCE_INVESTOR.regimeId);
  });

  it("merges a patch and removes a field set back to undefined", () => {
    const store = createInvestorPolicyStore();
    store.update({ regimeId: "us-zero-ltcg", hasHighDeductiblePlan: true });
    store.update({ hasHighDeductiblePlan: undefined });

    expect(store.policy.regimeId).toBe("us-zero-ltcg");
    expect(store.policy.hasHighDeductiblePlan).toBeUndefined();
    expect(store.resolved().hasHighDeductiblePlan).toBe(false);
  });

  it("refuses a utilisation outside [0, 1], which would throw downstream", () => {
    const store = createInvestorPolicyStore();
    store.update({ foreignCreditUtilisation: 1.5 });

    expect(store.policy.foreignCreditUtilisation).toBeUndefined();
    expect(store.resolved().foreignCreditUtilisation).toBe(1);
  });

  it("clears back to empty and drops the stored key", () => {
    const store = createInvestorPolicyStore();
    store.update({ regimeId: "us-upper-middle", accounts: { hsa: 8750 } });
    store.clear();

    expect(store.policy).toEqual({});
    expect(store.resolved().isEmpty).toBe(true);
    expect(localStorage.getItem(POLICY_STORAGE_KEY)).toBeNull();
    expect(createInvestorPolicyStore().policy).toEqual({});
  });
});
