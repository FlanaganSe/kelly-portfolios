import type { AsOf, Citation } from "~/content/types";
import { asOf } from "~/content/types";
import type { TiltInputs } from "~/lib/tilt";

/**
 * The two value tilts this repository has actually priced, with every input it measured.
 *
 * Only two things on this record are the reader's to change: the weight, and which of
 * the measured HML premia to believe. Everything else — both loadings, both fees, both
 * turnovers, both volatilities and the correlation — was estimated over a stated window
 * and is carried here at full precision, so that at the published weight the arithmetic
 * reproduces the published figure exactly rather than approximately.
 *
 * The chain is `weight × (fund loading − incumbent loading) × premium − incremental
 * cost`. Three terms. There is no capture fraction, and `sleeveEdge` throws if one is
 * passed: a capture fraction *is* a loading, so the product would discount the same
 * exposure twice.
 */

const recommendation: Citation = {
  label: "The recommended portfolio, §5",
  docPath: "docs/research/portfolio-recommendation.md",
};

/** One selectable premium. Each is a measured, gross, long-short spread. */
export interface PremiumChoice {
  readonly id: string;
  readonly label: string;
  /** Percentage points a year. */
  readonly value: number;
  readonly interval: string;
  /** The smallest premium the window could have detected at 80% power, pp/yr. */
  readonly detectionFloor: number;
  readonly note: string;
}

export interface PricedTilt {
  readonly id: string;
  readonly label: string;
  readonly fundTicker: string;
  readonly incumbentTicker: string;
  /** The weight the repository published a figure at. */
  readonly publishedWeight: number;
  /** What the published figures are, so a reader can see the port reproduce them. */
  readonly published: {
    readonly edgeBp: number;
    readonly trackingErrorBp: number;
    readonly growthBp: number;
  };
  /**
   * The window every measured input below was estimated over.
   *
   * It has to be printed. DFIV reads +0.662 on its own 51-month window and +0.698 on the
   * 45 months common to the shelf, and VEA's own HML changes sign between them. Both are
   * correct; a page showing one number without its window makes the other look like an
   * error.
   */
  readonly window: string;
  /** Every measured input except the weight and the premium. */
  readonly measured: Omit<TiltInputs, "weight" | "hmlPremium">;
  readonly premia: readonly PremiumChoice[];
  readonly defaultPremiumId: string;
  readonly caveat: string;
  readonly source: Citation;
  readonly asOf: AsOf;
}

const POOLED: PremiumChoice = {
  id: "pooled",
  label: "Pooled, three regions",
  value: 4.740625,
  interval: "[+1.46, +8.10]",
  detectionFloor: 3.35,
  note: "The only factor premium in this repository to advance on its own strength. Carried by the two non-US regions.",
};

const US_ONLY: PremiumChoice = {
  id: "us",
  label: "US only, post-publication",
  value: 1.57,
  interval: "[−2.28, +5.54]",
  detectionFloor: 5.03,
  note: "Not signable: the interval contains zero and the estimate sits well below the floor its own window could detect.",
};

const DEV_EX_US: PremiumChoice = {
  id: "dev-ex-us",
  label: "Developed ex-US, post-publication",
  value: 5.07125,
  interval: "[+1.45, +9.05]",
  detectionFloor: 3.67,
  note: "Signable on its own panel, which is what makes the ex-US tilt the strongest one priced here.",
};

const EMERGING: PremiumChoice = {
  id: "emerging",
  label: "Emerging, post-publication",
  value: 7.58,
  interval: "[+4.34, +11.01]",
  detectionFloor: 3.0,
  note: "The largest measured anywhere here — and no emerging-market value product on this shelf reaches exploratory, so there is nothing audited to buy it with.",
};

export const pricedTilts: readonly PricedTilt[] = [
  {
    id: "avlv",
    label: "US large value: AVLV, funded out of VTI",
    fundTicker: "AVLV",
    incumbentTicker: "VTI",
    publishedWeight: 0.2,
    published: { edgeBp: 24.4, trackingErrorBp: 135, growthBp: 24.9 },
    window: "51 months, US panel",
    measured: {
      fundHmlLoading: 0.322028508346998,
      benchmarkHmlLoading: 0.0246971965235378,
      fundFee: 0.15,
      benchmarkFee: 0.03,
      fundTurnoverPercent: 7,
      benchmarkTurnoverPercent: 3,
      turnoverCoefficient: 1.7,
      fundVolatility: 17.181423095590738,
      benchmarkVolatility: 16.23770348459306,
      correlation: 0.9194103780959881,
    },
    premia: [POOLED, US_ONLY, EMERGING],
    defaultPremiumId: "pooled",
    caveat:
      "Switch the premium to US-only and the growth contribution is negative at every weight. That single choice, and not the fund, decides the sign of this line.",
    source: recommendation,
    asOf: asOf("2026-08-17"),
  },
  {
    id: "dfiv",
    label: "Developed ex-US large value: DFIV, funded out of VEA",
    fundTicker: "DFIV",
    incumbentTicker: "VEA",
    publishedWeight: 0.08,
    published: { edgeBp: 27.1, trackingErrorBp: 47.6, growthBp: 29.5 },
    window: "45 months common to the shelf, developed ex-US panel",
    measured: {
      fundHmlLoading: 0.6976037808578383,
      benchmarkHmlLoading: -0.025186177492858675,
      fundFee: 0.27,
      benchmarkFee: 0.03,
      fundTurnoverPercent: 6,
      benchmarkTurnoverPercent: 4,
      turnoverCoefficient: 1.7,
      fundVolatility: 15.781965234617221,
      benchmarkVolatility: 16.598108003208974,
      correlation: 0.9337858710123662,
    },
    premia: [DEV_EX_US, POOLED, US_ONLY],
    defaultPremiumId: "dev-ex-us",
    caveat:
      "None of this charges DFIV's own alpha, which is −4.11 pp/yr against a 3.52 pp/yr detection floor. Charging it takes the published 8% line from +27.1 bp to −8.2 bp, and on that reading the repository's answer is IVLU.",
    source: recommendation,
    asOf: asOf("2026-08-17"),
  },
];

export function tiltById(id: string): PricedTilt | undefined {
  return pricedTilts.find((one) => one.id === id);
}
