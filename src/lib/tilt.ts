/**
 * What a long-only value tilt is worth, and the double count that made it look smaller.
 *
 * A port of `research/src/portfolio_edge/studies/value_tilt.py`, checked against
 * `~/lib/fixtures/research-ground-truth.json`, which that workspace generates.
 *
 * **Every figure here is in percent per year**, never a decimal fraction: a 4.74 pp/yr
 * premium is `4.74`, a 0.25% fee is `0.25`, a 15.6 pp/yr volatility is `15.6`, and a
 * weight — the one exception, and the only quantity that is a fraction — is `0.2`. A
 * variance is therefore in percent-squared, which is a hundred times too large for
 * `g = A - V/2`; that conversion is why {@link varianceDrag} divides by 200 and not by 2.
 * Dropping it turns a 21 bp growth contribution into -21 pp/yr, which is how the Python
 * caught it.
 *
 * The chain is
 *
 *     edge = weight * (h_fund - h_benchmark) * premium - weight * cost
 *
 * and it has **three** terms, not four. A capture fraction may not appear in it. A
 * capture fraction *is* an HML loading plus a small residue — the size-neutral 0.520
 * Experiment 007 measures decomposes exactly into a loading of 0.4891 and a 0.0313
 * residue — so multiplying a fund's regression coefficient by one applies the long-only
 * discount twice. A long-only fund cannot load 1.0 on a long-short factor and its
 * coefficient already says so. {@link sleeveEdge} refuses a capture argument outright
 * rather than accepting one and warning, exactly as `sleeve_edge` does and for the same
 * reason `aggregate` in `~/lib/horizon` refuses to sum across benchmarks.
 *
 * The one benchmark choice left is which fund is sold to buy the sleeve, and it enters
 * as `benchmarkHmlLoading` — a small measured number, not a haircut.
 */

/** One basis point in the percent-per-year units every figure here is stated in. */
const PERCENT_PER_BASIS_POINT = 0.01;

/** The conversion every variance term needs, and the one easy to forget. */
const PERCENT_PER_UNIT = 100;

/**
 * Thrown when a caller multiplies a regression loading by a capture fraction.
 *
 * The two measure the same quantity, so their product is not a delivered exposure. This
 * is the error `docs/research/portfolio-recommendation.md` §5 made, and it cost a factor
 * of about two in five places.
 */
export class CaptureDoubleCountError extends RangeError {
  constructor(message: string) {
    super(message);
    this.name = "CaptureDoubleCountError";
  }
}

/**
 * One long-only factor tilt against one incumbent fund, all figures percent per year.
 *
 * `weight` is the fraction of the whole portfolio moved out of the incumbent and into
 * the tilt product, so this is a **substitution** and never an overlay: nothing is
 * financed and total exposure does not change.
 *
 * Every cost is charged **incrementally over the incumbent**, because the incumbent's
 * own fee and turnover are paid either way. Charging the tilt's gross fee against a zero
 * baseline is the same double count in a different place.
 */
export type TiltInputs = {
  readonly weight: number;
  readonly fundHmlLoading: number;
  readonly benchmarkHmlLoading: number;
  readonly hmlPremium: number;
  readonly fundFee: number;
  readonly benchmarkFee: number;
  readonly fundTurnoverPercent: number;
  readonly benchmarkTurnoverPercent: number;
  readonly turnoverCoefficient: number;
  readonly fundVolatility: number;
  readonly benchmarkVolatility: number;
  readonly correlation: number;
};

/** The growth answer and the demonstrability answer, side by side and labelled. */
export type TiltVerdict = {
  readonly weight: number;
  readonly deliveredLoading: number;
  readonly hmlPremium: number;
  readonly incrementalCost: number;
  readonly sleeveEdgePercent: number;
  readonly portfolioEdgeBasisPoints: number;
  readonly portfolioTrackingErrorBasisPoints: number;
  readonly growthContributionPercent: number;
  readonly certaintyEquivalentPercent: number;
  readonly terminalWealthMultiple30y: number;
};

/**
 * The Python dataclass validates in `__post_init__`; a plain object cannot, so every
 * exported function that takes a {@link TiltInputs} calls this first.
 */
export function validateTiltInputs(inputs: TiltInputs): void {
  if (!(inputs.weight >= 0 && inputs.weight <= 1)) {
    throw new RangeError(`weight must lie in [0, 1], got ${inputs.weight}`);
  }
  if (inputs.fundVolatility <= 0 || inputs.benchmarkVolatility <= 0) {
    throw new RangeError("both volatilities must be positive");
  }
  if (!(inputs.correlation >= -1 && inputs.correlation <= 1)) {
    throw new RangeError(`correlation must lie in [-1, 1], got ${inputs.correlation}`);
  }
}

/**
 * `k * turnover` basis points, returned in percent per year.
 *
 * The calibration is `portfolio_edge.core.costs`: `k` runs from 1.0 (patient limit orders
 * in liquid names) to 1.7 (market orders, full universe). The turnover a fund files under
 * Item 3 of Form N-1A is `min(purchases, sales) / average net assets`, which is the
 * one-sided measure this rule wants, and it **excludes an ETF's in-kind creations and
 * redemptions** — the part of an ETF's rotation that costs the fund nothing.
 */
export function turnoverCostPercent({
  oneSidedTurnoverPercent,
  coefficient,
}: {
  readonly oneSidedTurnoverPercent: number;
  readonly coefficient: number;
}): number {
  if (oneSidedTurnoverPercent < 0) {
    throw new RangeError(`turnover cannot be negative, got ${oneSidedTurnoverPercent}`);
  }
  if (coefficient < 0) {
    throw new RangeError(`the turnover coefficient cannot be negative, got ${coefficient}`);
  }
  return coefficient * oneSidedTurnoverPercent * PERCENT_PER_BASIS_POINT;
}

/**
 * `h_fund - h_benchmark`: the exposure the swap actually buys.
 *
 * The incumbent is not exposure-free. VTI's own FF5+UMD HML loading over 2020-01..2025-12
 * is +0.0247, small but measured, and subtracting it is the only benchmark choice this
 * chain contains.
 */
export function deliveredLoading(inputs: TiltInputs): number {
  validateTiltInputs(inputs);
  return inputs.fundHmlLoading - inputs.benchmarkHmlLoading;
}

/** Fee plus trading cost, both net of what the incumbent already charges. */
export function incrementalCost(inputs: TiltInputs): number {
  validateTiltInputs(inputs);
  const fee = inputs.fundFee - inputs.benchmarkFee;
  const trading =
    turnoverCostPercent({
      oneSidedTurnoverPercent: inputs.fundTurnoverPercent,
      coefficient: inputs.turnoverCoefficient,
    }) -
    turnoverCostPercent({
      oneSidedTurnoverPercent: inputs.benchmarkTurnoverPercent,
      coefficient: inputs.turnoverCoefficient,
    });
  return fee + trading;
}

/** `sd(fund - benchmark)`, from the two volatilities and their correlation. */
export function sleeveTrackingError(inputs: TiltInputs): number {
  validateTiltInputs(inputs);
  const variance =
    inputs.fundVolatility ** 2 +
    inputs.benchmarkVolatility ** 2 -
    2 * inputs.correlation * inputs.fundVolatility * inputs.benchmarkVolatility;
  // Equal volatilities at a correlation of exactly one leave no tracking error at all,
  // and rounding can push that difference of near-equal squares fractionally negative.
  return Math.sqrt(Math.max(variance, 0));
}

/**
 * `(h_fund - h_benchmark) * premium - incremental cost`, per dollar of sleeve.
 *
 * `capture` exists only to be refused; pass nothing. See the module comment for why the
 * product of a loading and a capture fraction is not a delivered exposure.
 */
export function sleeveEdge(inputs: TiltInputs, options?: { readonly capture?: number }): number {
  if (options?.capture !== undefined) {
    throw new CaptureDoubleCountError(
      "a capture fraction may not multiply a regression loading: they measure the same " +
        "exposure, so the product discounts it twice. " +
        `Drop the capture of ${options.capture} and use the loading alone.`
    );
  }
  return deliveredLoading(inputs) * inputs.hmlPremium - incrementalCost(inputs);
}

/**
 * `weight * sd(fund - benchmark)`: what the swap does to the whole portfolio.
 *
 * **Not** the tracking error of the fund against a fitted cheap replication, which is
 * what Experiment 002 reports and what §5 previously borrowed. A replication basis is not
 * what the investor sells.
 */
export function portfolioTrackingError(inputs: TiltInputs): number {
  return inputs.weight * sleeveTrackingError(inputs);
}

/**
 * `V(w) - V(0)` for holding `1 - w` of the incumbent and `w` of the fund, in
 * **percent-squared per year**.
 *
 * Exact, and independent of either expected return, which is why the growth contribution
 * below needs no forecast of the equity premium. It is positive for any tilt into a more
 * volatile fund at a correlation below one, and it is the term the old chain omitted
 * entirely: a substitution that raises portfolio variance pays for its arithmetic edge
 * out of its own geometric return.
 */
export function substitutionVarianceChange(inputs: TiltInputs): number {
  validateTiltInputs(inputs);
  const weight = inputs.weight;
  const covariance = inputs.correlation * inputs.fundVolatility * inputs.benchmarkVolatility;
  const tilted =
    (1 - weight) ** 2 * inputs.benchmarkVolatility ** 2 +
    2 * weight * (1 - weight) * covariance +
    weight ** 2 * inputs.fundVolatility ** 2;
  return tilted - inputs.benchmarkVolatility ** 2;
}

/**
 * `gamma (V(w) - V(0)) / 2`, converted from percent-squared into percent per year.
 *
 * At `gamma = 1` this is the geometric drag in `g = A - V/2`; at `gamma > 1` it is the
 * CRRA risk charge. One function serves both deliberately, because the only difference
 * between the growth answer and the certainty-equivalent answer is this coefficient, and
 * decision 0008 exists because that difference was being read as a result about a sleeve.
 */
export function varianceDrag(inputs: TiltInputs, { gamma }: { readonly gamma: number }): number {
  if (!(gamma > 0)) {
    throw new RangeError(`gamma must be positive, got ${gamma}`);
  }
  return (0.5 * gamma * substitutionVarianceChange(inputs)) / PERCENT_PER_UNIT;
}

/**
 * `w * edge - (V(w) - V(0)) / 200`: what the swap adds to geometric growth.
 *
 * `g = r + A - V/2`, the lognormal approximation `studies/overlay_growth` uses and
 * decision 0008 makes deciding. Under a substitution the arithmetic-return change is
 * exactly `w * edge`, so the incumbent's own expected return cancels and does not have to
 * be forecast.
 *
 * This is the **matched-volatility** reading of that module's equation (5) rather than
 * the admission rule of its equation (4): a value tilt sits inside equity at a
 * correlation around 0.85, far above the `|rho| = 0.5` at which (4) stops being a
 * decision rule.
 */
export function marginalGrowthContribution(inputs: TiltInputs): number {
  return inputs.weight * sleeveEdge(inputs) - varianceDrag(inputs, { gamma: 1 });
}

/**
 * `w * edge - gamma (V(w) - V(0)) / 200`: the CRRA certainty equivalent beside it.
 *
 * Decision 0008 requires this to be **reported** and not to decide, because on a
 * certainty-equivalent metric a candidate is paid for reducing risk and the payment can
 * exceed the materiality threshold on its own. At `gamma = 1` it is the growth rate.
 */
export function certaintyEquivalentContribution(inputs: TiltInputs, { gamma }: { readonly gamma: number }): number {
  return inputs.weight * sleeveEdge(inputs) - varianceDrag(inputs, { gamma });
}

/**
 * `exp(g * T)`: terminal wealth relative to holding the incumbent throughout.
 *
 * `growthContribution` is in percent per year, as everything else here is.
 */
export function terminalWealthMultiple({
  growthContribution,
  years,
}: {
  readonly growthContribution: number;
  readonly years: number;
}): number {
  if (years < 0) {
    throw new RangeError(`years cannot be negative, got ${years}`);
  }
  return Math.exp((growthContribution / 100) * years);
}

/**
 * Every figure one set of tilt inputs produces, so a caller cannot quote half.
 *
 * The edge and the tracking error answer *"can an investor ever show this worked"*. The
 * growth contribution and the terminal wealth multiple answer *"did it help"*. They are
 * different questions and a positive answer to the second is compatible with a negative
 * answer to the first, which is the whole reason both are returned together.
 */
export function tiltVerdict(
  inputs: TiltInputs,
  { gamma = 3, years = 30 }: { readonly gamma?: number; readonly years?: number } = {}
): TiltVerdict {
  const edge = sleeveEdge(inputs);
  const growth = marginalGrowthContribution(inputs);
  return {
    weight: inputs.weight,
    deliveredLoading: deliveredLoading(inputs),
    hmlPremium: inputs.hmlPremium,
    incrementalCost: incrementalCost(inputs),
    sleeveEdgePercent: edge,
    portfolioEdgeBasisPoints: (inputs.weight * edge) / PERCENT_PER_BASIS_POINT,
    portfolioTrackingErrorBasisPoints: portfolioTrackingError(inputs) / PERCENT_PER_BASIS_POINT,
    growthContributionPercent: growth,
    certaintyEquivalentPercent: certaintyEquivalentContribution(inputs, { gamma }),
    terminalWealthMultiple30y: terminalWealthMultiple({ growthContribution: growth, years }),
  };
}
