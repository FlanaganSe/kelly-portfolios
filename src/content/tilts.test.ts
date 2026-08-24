import { describe, expect, it } from "vitest";
import { findFund } from "~/content/shelf";
import { pricedTilts } from "~/content/tilts";
import { tiltVerdict } from "~/lib/tilt";

/**
 * The point of this file: at the weight and premium the research published a figure at,
 * the client's own arithmetic has to land on that figure. If it does not, the content
 * record is wrong — never the tolerance.
 */
describe("the priced tilts", () => {
  it.each(pricedTilts.map((one) => [one.id, one] as const))("reproduces the published %s figures", (_id, tilt) => {
    const premium = tilt.premia.find((one) => one.id === tilt.defaultPremiumId);
    expect(premium).toBeDefined();
    const verdict = tiltVerdict({
      ...tilt.measured,
      weight: tilt.publishedWeight,
      hmlPremium: premium?.value ?? 0,
    });
    expect(verdict.portfolioEdgeBasisPoints).toBeCloseTo(tilt.published.edgeBp, 1);
    expect(verdict.portfolioTrackingErrorBasisPoints).toBeCloseTo(tilt.published.trackingErrorBp, 0);
    expect(verdict.growthContributionPercent * 100).toBeCloseTo(tilt.published.growthBp, 1);
  });

  it("names funds that are on the shelf", () => {
    for (const tilt of pricedTilts) {
      expect(findFund(tilt.fundTicker), tilt.fundTicker).toBeDefined();
      expect(findFund(tilt.incumbentTicker), tilt.incumbentTicker).toBeDefined();
    }
  });

  it("offers a default premium that exists in its own list", () => {
    for (const tilt of pricedTilts) {
      expect(
        tilt.premia.some((one) => one.id === tilt.defaultPremiumId),
        tilt.id
      ).toBe(true);
    }
  });

  it("keeps every premium's detection floor beside it, so a floor can never be dropped", () => {
    for (const tilt of pricedTilts) {
      for (const premium of tilt.premia) {
        expect(premium.detectionFloor, `${tilt.id}/${premium.id}`).toBeGreaterThan(0);
        expect(premium.interval).toMatch(/\[/);
      }
    }
  });
});
