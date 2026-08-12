import { describe, expect, it } from "vitest";
import fixtures from "~/lib/fixtures/research-ground-truth.json";
import {
  derivedRates,
  type ForeignSleeve,
  forfeitedBp,
  form1116ThresholdAssets,
  locationBreakevenRate,
  type ShelterCandidate,
  shelteredCostBp,
  shelterPriorityBp,
  type TaxRegime,
  taxableCostBp,
} from "~/lib/placement";

const RELATIVE_TOLERANCE = 1e-9;

function expectClose(actual: number, expected: number): void {
  const tolerance = Math.max(Math.abs(expected) * RELATIVE_TOLERANCE, 1e-12);
  expect(Math.abs(actual - expected)).toBeLessThanOrEqual(tolerance);
}

/** Fixture lookup that fails loudly, since non-null assertions are banned. */
function byLabel<T extends { label: string }>(items: readonly T[], label: string): T {
  const found = items.find((item) => item.label === label);
  if (found === undefined) throw new Error(`fixture has no entry labelled ${label}`);
  return found;
}

function regime(label: string): TaxRegime {
  const source = byLabel(fixtures.regimes, label);
  return {
    label: source.label,
    asOf: source.asOf,
    ordinaryIncome: source.ordinaryIncome,
    longTermCapitalGain: source.longTermCapitalGain,
    netInvestmentIncome: source.netInvestmentIncome,
  };
}

function candidate(label: string): ShelterCandidate {
  const source = byLabel(fixtures.shelterCandidates, label);
  return {
    label: source.label,
    dividendYield: source.dividendYield,
    qualifiedFraction: source.qualifiedFraction,
    foreignWithholdingRate: source.foreignWithholdingRate,
  };
}

function sleeve(label: string): ForeignSleeve {
  const source = byLabel(fixtures.foreignSleeves, label);
  return {
    label: source.label,
    dividendYield: source.dividendYield,
    withholdingRate: source.withholdingRate,
  };
}

const allCandidates = fixtures.shelterCandidates.map((entry) => candidate(entry.label));

const TOP_BRACKET = "US top marginal bracket";
const UPPER_MIDDLE = "US upper-middle bracket";
const ZERO_RATE = "US zero long-term-rate bracket";
const DEVELOPED = "Developed ex-US equity";
const EMERGING = "Emerging-market equity";

describe("derivedRates", () => {
  for (const expected of fixtures.regimes) {
    it(`derives the all-in rates for the ${expected.label}`, () => {
      const rates = derivedRates(regime(expected.label));
      expectClose(rates.ordinary, expected.ordinary);
      expectClose(rates.capitalGain, expected.capitalGain);
      expectClose(rates.qualifiedDividend, expected.qualifiedDividend);
      expectClose(rates.section1256Blended, expected.section1256Blended);
    });
  }

  it("taxes a qualified dividend at the long-term rate", () => {
    const rates = derivedRates(regime(TOP_BRACKET));
    expect(rates.qualifiedDividend).toBe(rates.capitalGain);
    expect(rates.qualifiedDividend).toBeLessThan(rates.ordinary);
  });
});

describe("taxableCostBp and shelteredCostBp", () => {
  it(`match all ${fixtures.candidateCosts.length} research-workspace cases`, () => {
    for (const testCase of fixtures.candidateCosts) {
      const asset = candidate(testCase.candidate);
      expectClose(
        taxableCostBp(asset, regime(testCase.regime), {
          foreignCreditUtilisation: testCase.foreignCreditUtilisation,
        }),
        testCase.taxableCostBp
      );
      expectClose(shelteredCostBp(asset), testCase.shelteredCostBp);
    }
  });

  it("defaults the credit utilisation to full", () => {
    const asset = candidate(DEVELOPED);
    const top = regime(TOP_BRACKET);
    expect(taxableCostBp(asset, top)).toBe(taxableCostBp(asset, top, { foreignCreditUtilisation: 1 }));
  });

  it("caps the credit at the US tax, because an unused credit is not refundable", () => {
    // In the 0% bracket the US tax on a qualified dividend is nil, so no part of the
    // foreign withholding is recoverable and the taxable cost is the withholding itself.
    const asset = candidate(EMERGING);
    const cost = taxableCostBp(asset, regime(ZERO_RATE));
    expectClose(cost, shelteredCostBp(asset));
    expectClose(cost, forfeitedBp(sleeve(EMERGING)));
  });

  it("makes the taxable cost rise as the credit becomes less usable", () => {
    const asset = candidate(DEVELOPED);
    const top = regime(TOP_BRACKET);
    const full = taxableCostBp(asset, top, { foreignCreditUtilisation: 1 });
    const half = taxableCostBp(asset, top, { foreignCreditUtilisation: 0.5 });
    const none = taxableCostBp(asset, top, { foreignCreditUtilisation: 0 });
    expect(half).toBeGreaterThan(full);
    expect(none).toBeGreaterThan(half);
  });

  it("rejects a credit utilisation outside [0, 1]", () => {
    for (const foreignCreditUtilisation of [-0.1, 1.5]) {
      expect(() => taxableCostBp(candidate(DEVELOPED), regime(TOP_BRACKET), { foreignCreditUtilisation })).toThrow(
        /foreignCreditUtilisation must lie in \[0, 1\]/
      );
    }
  });

  it("charges nothing to shelter an asset with no foreign withholding", () => {
    expect(shelteredCostBp(candidate("US equity"))).toBe(0);
    expect(shelteredCostBp(candidate("Taxable investment-grade bonds"))).toBe(0);
  });
});

describe("shelterPriorityBp", () => {
  for (const expected of fixtures.shelterPriority) {
    it(`reproduces the ranking and the figures for the ${expected.regime}`, () => {
      const ranking = shelterPriorityBp(allCandidates, {
        regime: regime(expected.regime),
        foreignCreditUtilisation: expected.foreignCreditUtilisation,
      });
      expect(ranking.map((row) => row.label)).toEqual(expected.ranking.map((row) => row.label));
      for (const [index, row] of ranking.entries()) {
        const target = expected.ranking[index];
        expect(target).toBeDefined();
        if (target !== undefined) expectClose(row.priorityBp, target.priorityBp);
      }
    });
  }

  /**
   * The finding the application exists to deliver. The familiar rule ranks by taxable
   * cost alone, which puts emerging-market equity above US equity at every bracket.
   * Netting off the foreign withholding that leaks inside the shelter anyway inverts
   * that pair between the top bracket and the upper-middle one — so a page stating one
   * ranking is wrong for a large share of its readers.
   */
  it("inverts emerging-market and US equity between the top and upper-middle brackets", () => {
    const order = (label: string) =>
      shelterPriorityBp(allCandidates, { regime: regime(label) }).map((row) => row.label);

    const top = order(TOP_BRACKET);
    expect(top.indexOf(EMERGING)).toBeLessThan(top.indexOf("US equity"));

    const upperMiddle = order(UPPER_MIDDLE);
    expect(upperMiddle.indexOf(EMERGING)).toBeGreaterThan(upperMiddle.indexOf("US equity"));

    // Developed markets and bonds hold their places, so the inversion is that one pair.
    expect(top.indexOf(DEVELOPED)).toBe(upperMiddle.indexOf(DEVELOPED));
    expect(top[0]).toBe("Taxable investment-grade bonds");
    expect(upperMiddle[0]).toBe("Taxable investment-grade bonds");
  });

  it("breaks ties by label so the ordering is deterministic", () => {
    // In the 0% bracket every equity sleeve saves exactly nothing.
    const ranking = shelterPriorityBp(allCandidates, { regime: regime(ZERO_RATE) });
    expect(ranking.map((row) => row.label)).toEqual([
      "Taxable investment-grade bonds",
      DEVELOPED,
      EMERGING,
      "US equity",
    ]);
    const reversed = shelterPriorityBp([...allCandidates].reverse(), { regime: regime(ZERO_RATE) });
    expect(reversed.map((row) => row.label)).toEqual(ranking.map((row) => row.label));
  });

  it("does not mutate the candidates it was given", () => {
    const input = [...allCandidates];
    shelterPriorityBp(input, { regime: regime(TOP_BRACKET) });
    expect(input.map((entry) => entry.label)).toEqual(allCandidates.map((entry) => entry.label));
  });
});

describe("locationBreakevenRate and the foreign sleeves", () => {
  for (const expected of fixtures.foreignSleeves) {
    it(`matches the research workspace for ${expected.label}`, () => {
      const target = sleeve(expected.label);
      expectClose(forfeitedBp(target), expected.forfeitedBp);
      expectClose(
        locationBreakevenRate({ international: target, domesticDividendYield: 0.011 }),
        expected.breakevenQualifiedRate
      );
      expectClose(form1116ThresholdAssets({ foreignTaxLimit: 300, sleeve: target }), expected.form1116SingleAssets);
      expectClose(form1116ThresholdAssets({ foreignTaxLimit: 600, sleeve: target }), expected.form1116JointAssets);
    });
  }

  it("puts the break-even between the two live US qualified-dividend rates", () => {
    const developed = locationBreakevenRate({ international: sleeve(DEVELOPED), domesticDividendYield: 0.011 });
    const emerging = locationBreakevenRate({ international: sleeve(EMERGING), domesticDividendYield: 0.011 });
    expect(developed * 100).toBeCloseTo(10.5179, 4);
    expect(emerging * 100).toBeCloseTo(21.5071, 4);
    // 15% sits above the developed break-even and below the emerging one, which is the
    // arithmetic behind the ranking inversion.
    expect(developed).toBeLessThan(0.15);
    expect(emerging).toBeGreaterThan(0.15);
  });

  it("scales linearly with the share of the credit the investor can use", () => {
    const target = sleeve(DEVELOPED);
    const full = locationBreakevenRate({ international: target, domesticDividendYield: 0.011 });
    const half = locationBreakevenRate({
      international: target,
      domesticDividendYield: 0.011,
      foreignCreditUtilisation: 0.5,
    });
    expectClose(half, full / 2);
  });

  it("refuses a comparison in which the international yield does not exceed the domestic one", () => {
    const target = sleeve(DEVELOPED);
    for (const domesticDividendYield of [target.dividendYield, 0.05]) {
      expect(() => locationBreakevenRate({ international: target, domesticDividendYield })).toThrow(
        /international yield must exceed the domestic yield/
      );
    }
  });

  it("rejects out-of-range inputs", () => {
    const target = sleeve(DEVELOPED);
    expect(() =>
      locationBreakevenRate({ international: target, domesticDividendYield: 0.011, foreignCreditUtilisation: 2 })
    ).toThrow(/foreignCreditUtilisation must lie in \[0, 1\]/);
    expect(() => locationBreakevenRate({ international: target, domesticDividendYield: 1.5 })).toThrow(
      /domesticDividendYield must lie in \[0, 1\)/
    );
  });
});

describe("form1116ThresholdAssets", () => {
  it("rejects a non-positive limit and a sleeve with no withheld tax", () => {
    expect(() => form1116ThresholdAssets({ foreignTaxLimit: 0, sleeve: sleeve(DEVELOPED) })).toThrow(
      /foreignTaxLimit must be positive/
    );
    expect(() =>
      form1116ThresholdAssets({
        foreignTaxLimit: 300,
        sleeve: { label: "US equity", dividendYield: 0.011, withholdingRate: 0 },
      })
    ).toThrow(/no withheld tax has no threshold/);
  });

  it("scales the threshold with the limit", () => {
    const target = sleeve(EMERGING);
    expectClose(
      form1116ThresholdAssets({ foreignTaxLimit: 600, sleeve: target }),
      2 * form1116ThresholdAssets({ foreignTaxLimit: 300, sleeve: target })
    );
  });
});
