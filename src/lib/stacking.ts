/**
 * What a pile of correlated bets is actually worth.
 *
 * A port of the closed form in
 * [stacking and effective breadth](../../docs/research/stacking-and-effective-breadth.md#1-the-arithmetic-of-stacking),
 * which is itself the `effective_breadth` in
 * `research/src/portfolio_edge/studies/overlay_growth.py`. Nothing here searches a
 * weight space or fits anything; it is arithmetic, so it is allowed on the client
 * under the research-integrity rule that keeps optimisation in `research/`.
 *
 * For `k` sleeves of identical edge, identical tracking error and mutual correlation
 * `rho` between their **excess** returns, the information ratio scales as
 *
 *     IR_k = IR_1 sqrt(k / (1 + (k - 1) rho))
 *
 * and the chance of finishing ahead is `Phi(z_1 sqrt(...))` where `z_1 = Phi^-1(P_1)`.
 * The horizon cancels out of that expression entirely, which is why one curve holds at
 * every holding period at once.
 *
 * The limit as `k` grows without bound is the part that matters:
 *
 *     breadth -> 1 / rho        P -> Phi(z_1 / sqrt(rho))
 *
 * so at any positive correlation the whole gain is bounded before the second sleeve is
 * bought. At `rho = 0` there is no ceiling and breadth is linear in `k`.
 *
 * Every probability here treats the edge as **known**. An estimated edge carries a
 * second, non-diversifying error term, `Phi(e / tau)`, which caps the answer again and
 * lower. Read anything this module returns as a best case.
 */

import { normalCdf, normalPpf } from "~/lib/normal";

/**
 * `k / (1 + (k - 1) rho)`: how many independent bets `k` correlated ones are worth.
 *
 * Equal weights and equal tracking errors are assumed, so this is the symmetric case,
 * not the general `1' R^-1 1`. A real portfolio's breadth is computed from its whole
 * correlation matrix and comes out different — 3.71 of 5 for the candidate here.
 */
export function effectiveBreadth(count: number, correlation: number): number {
  assertCount(count);
  assertCorrelation(correlation);
  const denominator = 1 + (count - 1) * correlation;
  if (denominator <= 0) {
    throw new RangeError(
      `a correlation of ${correlation} across ${count} sleeves is not a valid covariance; ` +
        "the implied matrix is not positive definite"
    );
  }
  return count / denominator;
}

/**
 * `Phi(z_1 sqrt(k / (1 + (k - 1) rho)))`: the chance `k` such sleeves finish ahead.
 *
 * `single` is the chance one sleeve on its own finishes ahead of the same benchmark
 * over the same period. It enters only through `z_1`, so the answer is scale-free in
 * the horizon.
 */
export function stackingProbability({
  count,
  correlation,
  single,
}: {
  readonly count: number;
  readonly correlation: number;
  readonly single: number;
}): number {
  assertSingle(single);
  const z = normalPpf(single);
  return normalCdf(z * Math.sqrt(effectiveBreadth(count, correlation)));
}

/**
 * `Phi(z_1 / sqrt(rho))`: where the stack stops, however many sleeves you buy.
 *
 * Returns 1 at `rho = 0`, which is the honest limit and not a certainty: reaching it
 * needs infinitely many genuinely independent bets. A hundred of them get to 0.896.
 */
export function stackingCeiling({
  correlation,
  single,
}: {
  readonly correlation: number;
  readonly single: number;
}): number {
  assertCorrelation(correlation);
  assertSingle(single);
  if (correlation === 0) return 1;
  return normalCdf(normalPpf(single) / Math.sqrt(correlation));
}

/**
 * The share of the ceiling's whole gain that `k` sleeves have already captured.
 *
 * Measured from the single-sleeve probability, because that is the reader's starting
 * point: `(P_k - P_1) / (P_inf - P_1)`. Undefined at `rho = 0`, where the ceiling is
 * certainty and no finite stack captures a fixed share of it.
 */
export function captureOfCeiling({
  count,
  correlation,
  single,
}: {
  readonly count: number;
  readonly correlation: number;
  readonly single: number;
}): number {
  if (correlation <= 0) {
    throw new RangeError(`capture is only defined at a positive correlation, got ${correlation}`);
  }
  const ceiling = stackingCeiling({ correlation, single });
  const gain = ceiling - single;
  if (gain <= 0) return 0;
  return (stackingProbability({ count, correlation, single }) - single) / gain;
}

function assertCount(count: number): void {
  if (!Number.isFinite(count) || count < 1) {
    throw new RangeError(`count must be at least one sleeve, got ${count}`);
  }
}

function assertCorrelation(correlation: number): void {
  if (!Number.isFinite(correlation) || correlation < 0 || correlation >= 1) {
    throw new RangeError(`correlation must lie in [0, 1), got ${correlation}`);
  }
}

function assertSingle(single: number): void {
  if (!Number.isFinite(single) || single <= 0 || single >= 1) {
    throw new RangeError(`the single-sleeve probability must lie strictly inside (0, 1), got ${single}`);
  }
}
