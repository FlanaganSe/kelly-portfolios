/**
 * How long an edge takes to become visible, and the budget it is applied to.
 *
 * A port of `research/src/portfolio_edge/studies/outperformance_horizon.py`. The two
 * ideas stay in one module for the same reason they do there: separating them is how the
 * dishonest version of the argument gets made.
 *
 * If a portfolio's log return exceeds a benchmark's by `e` per year with tracking error
 * `s` per year, and annual relative returns are independent, the cumulative log relative
 * return after `T` years is `N(e T, s^2 T)`, so
 *
 *     P(outperform) = Phi(e sqrt(T) / s),   T(confidence) = (z s / e)^2.
 *
 * The horizon scales with the **square** of `s / e`: halving the edge quadruples the
 * time. That is the whole result, and it is elementary.
 *
 * `s` is not a property of the edge, it is a property of the edge *relative to its
 * benchmark*. A contractual saving — a lower fee on the same index fund — has an `s` of
 * a few basis points and converts to near-certainty immediately. A risk premium
 * harvested by a factor tilt has an `s` of several hundred basis points against a broad
 * index and does not converge inside a human lifetime. Adding the two into one number is
 * the mistake this module exists to refuse.
 */

import { normalCdf, normalPpf } from "~/lib/normal";

/** One basis point, as the Python module defines it. Divide by it; never multiply by 1e4. */
const BASIS_POINT = 1e-4;

/** Whether a line item is an accounting identity or a bet. */
export type Certainty =
  /**
   * An accounting identity or a contractual saving. Realised with near-certainty
   * against its own benchmark; the only uncertainty is in the size of the input, not in
   * the sign of the outcome.
   */
  | "deterministic"
  /**
   * A risk premium, a forecast, or a policy whose payoff depends on the path. The sign
   * of the realised outcome is not known in advance at any human horizon.
   */
  | "probabilistic";

/**
 * What a line item is measured against. These never aggregate across classes, and
 * conflating them is the most common way an edge budget is inflated: beating *the
 * average investor* is a different and much easier claim than beating *the index*.
 */
export type Benchmark =
  /** A cheap investable index of the same asset class, gross of the investor's costs. */
  | "stated-index"
  /** The dollar-weighted experience of the average investor in the same asset class. */
  | "average-investor"
  /** The same investor's plausible alternative product or account choice. */
  | "counterfactual-holding";

/** One line of the budget, with what is needed to audit or reject it. */
export type EdgeComponent = {
  readonly name: string;
  readonly benchmark: Benchmark;
  readonly certainty: Certainty;
  readonly lowBp: number;
  readonly centralBp: number;
  readonly highBp: number;
  readonly trackingErrorBp: number;
};

/** A budget total for one benchmark, with its combined tracking error. */
export type AggregateEdge = {
  readonly benchmark: Benchmark;
  readonly components: number;
  readonly lowBp: number;
  readonly centralBp: number;
  readonly highBp: number;
  readonly trackingErrorBp: number;
};

/**
 * `Phi(e sqrt(T) / s)`: the probability the cumulative relative log return is positive.
 *
 * Assumes annual relative log returns are independent with constant mean and variance.
 * Both assumptions flatter the answer — real relative returns are autocorrelated, and
 * treating a point estimate of `e` as known removes the dominant source of uncertainty.
 * Read the output as an upper bound on attainable confidence.
 */
export function probabilityOfOutperformance({
  edgeBp,
  trackingErrorBp,
  horizonYears,
}: {
  readonly edgeBp: number;
  readonly trackingErrorBp: number;
  readonly horizonYears: number;
}): number {
  if (!(horizonYears > 0)) {
    throw new RangeError(`horizonYears must be positive, got ${horizonYears}`);
  }
  if (trackingErrorBp < 0) {
    throw new RangeError(`trackingErrorBp cannot be negative, got ${trackingErrorBp}`);
  }
  if (trackingErrorBp === 0) {
    // The contractual case, not a degenerate one. A fee saving on the same index fund
    // has no tracking error, so a positive edge is realised with certainty at every
    // horizon. This branch is the reason cost reduction dominates the budget.
    if (edgeBp > 0) return 1;
    return edgeBp < 0 ? 0 : 0.5;
  }
  return normalCdf((edgeBp * Math.sqrt(horizonYears)) / trackingErrorBp);
}

/** Years until `P(outperform)` reaches `confidence`: `T = (z s / e)^2`. */
export function horizonForConfidence({
  edgeBp,
  trackingErrorBp,
  confidence,
}: {
  readonly edgeBp: number;
  readonly trackingErrorBp: number;
  readonly confidence: number;
}): number {
  if (!(edgeBp > 0)) {
    throw new RangeError(`edgeBp must be positive, got ${edgeBp}`);
  }
  if (trackingErrorBp < 0) {
    throw new RangeError(`trackingErrorBp cannot be negative, got ${trackingErrorBp}`);
  }
  assertConfidence(confidence);
  const z = normalPpf(confidence);
  return ((z * trackingErrorBp) / edgeBp) ** 2;
}

/**
 * The smallest edge reaching `confidence` within `horizonYears`: `e = z s / sqrt(T)`.
 *
 * Read the other way round it says what an investor with a given tracking-error budget
 * and lifetime could ever hope to demonstrate — usually far more than any plausible
 * edge, which is why "wait and see" is not a validation strategy.
 */
export function detectableEdgeBp({
  trackingErrorBp,
  horizonYears,
  confidence,
}: {
  readonly trackingErrorBp: number;
  readonly horizonYears: number;
  readonly confidence: number;
}): number {
  if (!(horizonYears > 0)) {
    throw new RangeError(`horizonYears must be positive, got ${horizonYears}`);
  }
  assertConfidence(confidence);
  return (normalPpf(confidence) * trackingErrorBp) / Math.sqrt(horizonYears);
}

/**
 * Sum components sharing one benchmark, combining tracking errors in quadrature.
 *
 * Throws if the components do not share a benchmark. That is the entire point: summing
 * across benchmarks is the double-counting error this module is built to prevent, and
 * decision 0007 requires the interface to enforce it rather than to document it.
 *
 * The quadrature rule assumes the components' relative returns are mutually
 * independent. That is an **assumption**, and an optimistic one: a factor tilt and a
 * rebalancing policy applied to the same portfolio share the same equity beta and the
 * same crisis, so the true combined tracking error is larger than this.
 */
export function aggregate(components: readonly EdgeComponent[]): AggregateEdge {
  if (components.length === 0) {
    throw new RangeError("cannot aggregate an empty budget");
  }
  for (const item of components) {
    validateComponent(item);
  }
  const benchmarks = [...new Set(components.map((item) => item.benchmark))];
  const [benchmark] = benchmarks;
  if (benchmarks.length !== 1 || benchmark === undefined) {
    throw new RangeError(`components must share one benchmark; got ${[...benchmarks].sort().join(", ")}`);
  }
  let lowBp = 0;
  let centralBp = 0;
  let highBp = 0;
  let varianceBp = 0;
  for (const item of components) {
    lowBp += item.lowBp;
    centralBp += item.centralBp;
    highBp += item.highBp;
    varianceBp += item.trackingErrorBp ** 2;
  }
  return {
    benchmark,
    components: components.length,
    lowBp,
    centralBp,
    highBp,
    trackingErrorBp: Math.sqrt(varianceBp),
  };
}

/** The Python dataclass validates on construction; a plain object cannot, so this does. */
function validateComponent(item: EdgeComponent): void {
  if (!(item.lowBp <= item.centralBp && item.centralBp <= item.highBp)) {
    throw new RangeError(
      `${item.name}: require low <= central <= high, got ${item.lowBp}, ${item.centralBp}, ${item.highBp}`
    );
  }
  if (item.trackingErrorBp < 0) {
    throw new RangeError(`${item.name}: tracking error cannot be negative`);
  }
  if (item.certainty === "deterministic" && item.lowBp < 0) {
    throw new RangeError(
      `${item.name}: a deterministic component cannot have a negative low estimate; ` +
        "if the sign is in doubt it is probabilistic"
    );
  }
}

function assertConfidence(confidence: number): void {
  if (!(confidence >= 0.5 && confidence < 1)) {
    throw new RangeError(`confidence must lie in [0.5, 1), got ${confidence}`);
  }
}

/**
 * `exp(e T)`: terminal wealth with the edge, over terminal wealth without it.
 *
 * The one figure here that needs **no forecast of any market**. Both paths are the same
 * portfolio exposed to the same returns, and the edge is an addition to the log growth
 * rate, so the market term cancels out of the ratio exactly. What survives depends only
 * on the edge and the horizon.
 *
 * That is what makes a contractual edge worth quoting to a reader and a risk premium not.
 * Applied to a probabilistic line this would quote a median as though it were a promise,
 * so pair it with {@link probabilityOfOutperformance} and never show it alone for a line
 * whose certainty is `"probabilistic"`.
 *
 * `edgeBp` is a **log** growth rate in basis points a year, matching `EdgeComponent` and
 * the tax figures. Compounding `(1 + e)**T` instead would understate it slightly and mix
 * simple with log conventions inside one budget.
 *
 * Ported from `studies/outperformance_horizon.terminal_wealth_ratio`.
 */
export function terminalWealthRatio({
  edgeBp,
  horizonYears,
}: {
  readonly edgeBp: number;
  readonly horizonYears: number;
}): number {
  if (horizonYears < 0) {
    throw new RangeError(`horizonYears cannot be negative, got ${horizonYears}`);
  }
  return Math.exp(edgeBp * BASIS_POINT * horizonYears);
}
