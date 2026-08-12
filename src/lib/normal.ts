/**
 * The standard normal CDF and its inverse.
 *
 * The research workspace reaches for `scipy.stats.norm`; a browser has no scipy, and
 * every number in `~/lib/horizon` is a `Phi` or a `Phi^-1` of something. Both functions
 * here are pinned against the `normalCdf` and `normalPpf` fixtures that workspace
 * emitted, to 1e-12 absolute, so a cheap tail approximation is not good enough: the
 * fixture deliberately includes x = -4 and x = 6.
 */

const TWO_OVER_SQRT_PI = 2 / Math.sqrt(Math.PI);
const ONE_OVER_SQRT_PI = 1 / Math.sqrt(Math.PI);
const SQRT_TWO_PI = Math.sqrt(2 * Math.PI);

/**
 * Where `erfc` switches from `1 - erf` to the continued fraction. Below it the
 * subtraction is harmless; above it the continued fraction converges quickly enough
 * that there is no reason to pay for the cancellation.
 */
const SERIES_LIMIT = 2;

/** Guard for a zero denominator in the Lentz recurrence, per Numerical Recipes. */
const LENTZ_TINY = 1e-300;

/**
 * `erf` by its all-positive series, `erf(x) = (2/sqrt(pi)) e^-x^2 sum 2^n x^(2n+1) / (2n+1)!!`.
 *
 * The alternating Maclaurin series is the textbook one and is useless past x ~ 2
 * because the terms cancel. This form has no negative terms at all, so it keeps full
 * relative accuracy over the whole range it is used on.
 */
function erfSeries(x: number): number {
  const xx = x * x;
  let term = x;
  let sum = x;
  for (let n = 1; n < 300; n += 1) {
    term *= (2 * xx) / (2 * n + 1);
    sum += term;
    if (Math.abs(term) <= Math.abs(sum) * 1e-18) break;
  }
  return TWO_OVER_SQRT_PI * Math.exp(-xx) * sum;
}

/**
 * `erfc` for x >= SERIES_LIMIT by its continued fraction,
 * `erfc(x) = (e^-x^2 / sqrt(pi)) / (x + (1/2)/(x + 1/(x + (3/2)/(x + ...))))`,
 * evaluated with the modified Lentz algorithm.
 */
function erfcContinuedFraction(x: number): number {
  let f = LENTZ_TINY;
  let c = f;
  let d = 0;
  for (let i = 1; i < 1000; i += 1) {
    const a = i === 1 ? 1 : (i - 1) / 2;
    d = x + a * d;
    if (d === 0) d = LENTZ_TINY;
    c = x + a / c;
    if (c === 0) c = LENTZ_TINY;
    d = 1 / d;
    const delta = c * d;
    f *= delta;
    if (Math.abs(delta - 1) < 1e-17) break;
  }
  return ONE_OVER_SQRT_PI * Math.exp(-x * x) * f;
}

/** The complementary error function, `1 - erf(x)`, accurate into both tails. */
function erfc(x: number): number {
  if (x < 0) return 2 - erfc(-x);
  if (x < SERIES_LIMIT) return 1 - erfSeries(x);
  return erfcContinuedFraction(x);
}

/**
 * `Phi(x)`: the probability a standard normal draw falls at or below `x`.
 *
 * Written as `erfc(-x/sqrt(2)) / 2` rather than `(1 + erf(x/sqrt(2))) / 2` so the lower
 * tail keeps its relative accuracy instead of being subtracted away.
 */
export function normalCdf(x: number): number {
  if (!Number.isFinite(x)) {
    throw new RangeError(`normalCdf expects a finite number, got ${x}`);
  }
  return 0.5 * erfc(-x * Math.SQRT1_2);
}

/** Acklam's rational approximation to `Phi^-1`, good to about 1.15e-9 relative. */
const ACKLAM_A = [
  -3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2, 1.38357751867269e2, -3.066479806614716e1,
  2.506628277459239,
] as const;
const ACKLAM_B = [
  -5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2, 6.680131188771972e1, -1.328068155288572e1,
] as const;
const ACKLAM_C = [
  -7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838, -2.549732539343734, 4.374664141464968,
  2.938163982698783,
] as const;
const ACKLAM_D = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996, 3.754408661907416] as const;

const ACKLAM_LOW = 0.02425;

function acklam(p: number): number {
  const [a0, a1, a2, a3, a4, a5] = ACKLAM_A;
  const [b0, b1, b2, b3, b4] = ACKLAM_B;
  const [c0, c1, c2, c3, c4, c5] = ACKLAM_C;
  const [d0, d1, d2, d3] = ACKLAM_D;

  if (p < ACKLAM_LOW) {
    const q = Math.sqrt(-2 * Math.log(p));
    return (((((c0 * q + c1) * q + c2) * q + c3) * q + c4) * q + c5) / ((((d0 * q + d1) * q + d2) * q + d3) * q + 1);
  }
  if (p > 1 - ACKLAM_LOW) {
    const q = Math.sqrt(-2 * Math.log(1 - p));
    return -(((((c0 * q + c1) * q + c2) * q + c3) * q + c4) * q + c5) / ((((d0 * q + d1) * q + d2) * q + d3) * q + 1);
  }
  const q = p - 0.5;
  const r = q * q;
  return (
    ((((((a0 * r + a1) * r + a2) * r + a3) * r + a4) * r + a5) * q) /
    (((((b0 * r + b1) * r + b2) * r + b3) * r + b4) * r + 1)
  );
}

/**
 * `Phi^-1(p)`: the standard normal quantile, to machine precision.
 *
 * Acklam's approximation alone lands around 1e-9; two Halley steps against
 * {@link normalCdf} take it to the last bit or two. Above the median the residual is
 * taken as `(1 - p) - Phi(-x)` rather than `Phi(x) - p`, because both terms of the
 * former stay small in the upper tail while both terms of the latter approach 1 and
 * cancel. `1 - p` is exact for p in [0.5, 1), so nothing is lost in forming it.
 */
export function normalPpf(p: number): number {
  if (!Number.isFinite(p) || p <= 0 || p >= 1) {
    throw new RangeError(`normalPpf expects a probability strictly inside (0, 1), got ${p}`);
  }
  let x = acklam(p);
  for (let i = 0; i < 2; i += 1) {
    const residual = p <= 0.5 ? normalCdf(x) - p : 1 - p - normalCdf(-x);
    if (residual === 0) break;
    const u = residual * SQRT_TWO_PI * Math.exp((x * x) / 2);
    x -= u / (1 + (x * u) / 2);
  }
  return x;
}
