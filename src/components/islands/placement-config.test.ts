import { describe, expect, it } from "vitest";
import {
  defaultPlacementConfig,
  OWN_RATES,
  type PlacementConfig,
  parsePlacementConfig,
  toPlacementSearchParams,
} from "~/components/islands/placement-config";

const roundTrip = (config: PlacementConfig) => parsePlacementConfig(toPlacementSearchParams(config));

describe("parsePlacementConfig", () => {
  it("returns the defaults for an empty query", () => {
    expect(parsePlacementConfig("")).toEqual(defaultPlacementConfig);
  });

  it("reads every field", () => {
    expect(parsePlacementConfig("q=own&o=32.5&g=18.8&r=10&d=20&x=recorded")).toEqual({
      bracketId: "own",
      ownOrdinaryPercent: 32.5,
      ownQualifiedPercent: 18.8,
      rothPercent: 10,
      deferredPercent: 20,
      basis: "recorded",
    });
  });

  it("falls back per field and still loads the rest", () => {
    const parsed = parsePlacementConfig("q=Not%20An%20Id&r=oops&d=25");
    expect(parsed.bracketId).toBe(defaultPlacementConfig.bracketId);
    expect(parsed.rothPercent).toBe(defaultPlacementConfig.rothPercent);
    expect(parsed.deferredPercent).toBe(25);
  });

  it("refuses a rate outside the range a rate can take", () => {
    expect(parsePlacementConfig("q=own&o=140").ownOrdinaryPercent).toBe(defaultPlacementConfig.ownOrdinaryPercent);
    expect(parsePlacementConfig("q=own&g=-3").ownQualifiedPercent).toBe(defaultPlacementConfig.ownQualifiedPercent);
  });

  it("caps the two shelters at the whole portfolio", () => {
    const parsed = parsePlacementConfig("r=80&d=60");
    expect(parsed.rothPercent).toBe(80);
    expect(parsed.deferredPercent).toBe(20);
  });

  it("treats an unknown reading of the stacked fund as the audited one", () => {
    expect(parsePlacementConfig("x=whatever").basis).toBe("recorded");
  });
});

describe("toPlacementSearchParams", () => {
  it("writes nothing for the defaults", () => {
    expect(toPlacementSearchParams(defaultPlacementConfig).toString()).toBe("");
  });

  it("keeps the reader's own rates whenever they are the ones in use", () => {
    const query = toPlacementSearchParams({ ...defaultPlacementConfig, bracketId: OWN_RATES }).toString();
    expect(query).toContain("q=own");
    expect(query).toContain("o=40.8");
    expect(query).toContain("g=23.8");
  });

  it("round-trips losslessly", () => {
    const cases: PlacementConfig[] = [
      defaultPlacementConfig,
      { ...defaultPlacementConfig, bracketId: "us-zero-ltcg", rothPercent: 0, deferredPercent: 12.5 },
      {
        bracketId: OWN_RATES,
        ownOrdinaryPercent: 22,
        ownQualifiedPercent: 0,
        rothPercent: 50,
        deferredPercent: 50,
        basis: "paid-out",
      },
    ];
    for (const config of cases) expect(roundTrip(config)).toEqual(config);
  });
});
