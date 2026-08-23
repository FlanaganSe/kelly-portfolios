import { describe, expect, it } from "vitest";
import type { FactorLoading } from "~/content/shelf";
import { shelf } from "~/content/shelf";
import {
  commonWindow,
  distinctWindows,
  IncomparableWindowsError,
  loadingsFor,
  rankLoadings,
  sameWindow,
  windowLabel,
  windowMonths,
  windowSummary,
} from "~/lib/loadings";

function loading(
  value: number,
  from: string | null,
  to = "2025-12",
  factor: FactorLoading["factor"] = "HML"
): FactorLoading {
  return {
    factor,
    value,
    interval: null,
    panel: "us",
    window: from === null ? null : { from, to },
  };
}

describe("a window carries its own length", () => {
  it("counts both endpoints", () => {
    expect(windowMonths({ from: "2023-01", to: "2025-12" })).toBe(36);
    expect(windowMonths({ from: "2023-01", to: "2023-01" })).toBe(1);
    expect(windowMonths({ from: "2020-01", to: "2025-12" })).toBe(72);
  });

  it("reports nothing rather than zero when no window was recorded", () => {
    expect(windowMonths(null)).toBeNull();
    expect(windowLabel(null)).toBe("—");
    expect(windowSummary(null)).toBe("—");
  });

  it("never prints a length without the months it came from", () => {
    expect(windowSummary({ from: "2023-10", to: "2026-04" })).toBe("2023-10..2026-04 (31m)");
  });
});

describe("ranking refuses loadings from different windows", () => {
  it("throws on the published US value shelf, which is exactly such a set", () => {
    const published = loadingsFor(shelf, "HML", "us").filter((row) =>
      ["VTV", "AVLV", "DFLV", "DFUV", "AVUV", "DFSV", "DFAT", "RPV", "VBR"].includes(row.ticker)
    );
    expect(published).toHaveLength(9);
    expect(() => rankLoadings(published.map((row) => row.loading))).toThrow(IncomparableWindowsError);
  });

  it("names the windows it found, so the caller can see why", () => {
    try {
      rankLoadings([loading(0.337, "2020-01"), loading(0.637, "2023-01")]);
      throw new Error("expected a refusal");
    } catch (error) {
      expect(error).toBeInstanceOf(IncomparableWindowsError);
      expect((error as IncomparableWindowsError).windows).toEqual(["2020-01..2025-12", "2023-01..2025-12"]);
    }
  });

  it("sorts a matched set largest first", () => {
    const ranked = rankLoadings([loading(0.413, "2023-01"), loading(0.836, "2023-01"), loading(0.52, "2023-01")]);
    expect(ranked.map((item) => item.value)).toEqual([0.836, 0.52, 0.413]);
  });

  it("refuses a set where any window is missing, rather than treating it as a match", () => {
    expect(() => rankLoadings([loading(0.414, null), loading(0.444, null)])).toThrow(IncomparableWindowsError);
  });

  it("refuses to rank two different factors even on the same months", () => {
    expect(() => rankLoadings([loading(0.467, "2023-01"), loading(0.88, "2023-01", "2025-12", "SMB")])).toThrow(
      /different quantities/
    );
  });

  it("ranks nothing rather than throwing on an empty set", () => {
    expect(rankLoadings([])).toEqual([]);
  });
});

describe("the common window is what a refit would use", () => {
  it("intersects the nine published US value windows to 36 months", () => {
    const published = loadingsFor(shelf, "HML", "us")
      .filter((row) => ["VTV", "AVLV", "DFLV", "DFUV", "AVUV", "DFSV", "DFAT", "RPV", "VBR"].includes(row.ticker))
      .map((row) => row.loading);
    expect(commonWindow(published)).toEqual({ from: "2023-01", to: "2025-12" });
  });

  it("is null where the windows never overlap", () => {
    expect(commonWindow([loading(0.1, "2019-01", "2019-12"), loading(0.2, "2021-01", "2021-12")])).toBeNull();
  });

  it("is null where any window is missing", () => {
    expect(commonWindow([loading(0.1, "2020-01"), loading(0.2, null)])).toBeNull();
  });
});

describe("window equality", () => {
  it("holds only when both ends match", () => {
    expect(sameWindow(loading(0.1, "2023-01"), loading(0.2, "2023-01"))).toBe(true);
    expect(sameWindow(loading(0.1, "2023-01"), loading(0.2, "2023-02"))).toBe(false);
  });

  it("is false whenever either window is missing, since absence is not agreement", () => {
    expect(sameWindow(loading(0.1, null), loading(0.2, null))).toBe(false);
  });

  it("lists distinct windows in the order first seen", () => {
    expect(distinctWindows([loading(0.1, "2020-01"), loading(0.2, "2023-01"), loading(0.3, "2020-01")])).toEqual([
      "2020-01..2025-12",
      "2023-01..2025-12",
    ]);
  });
});
