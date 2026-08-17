/**
 * Asset location: what a dollar of tax-advantaged shelter capacity is worth.
 *
 * A port of the asset-location arithmetic in
 * `research/src/portfolio_edge/studies/tax_structure.py`. Every rate is an **argument**,
 * never a constant here: the research framework's requirement is verbatim that tax law
 * "must be a dated jurisdiction-specific input, never a hardcoded financial truth", so
 * the regimes, candidates and sleeves themselves belong in the content layer and this
 * module only does arithmetic on them.
 *
 * The one non-obvious result is that the familiar rule — shelter whatever carries the
 * heaviest recurring tax — is wrong for foreign equity, because a foreign withholding
 * tax is levied inside a shelter too and generates no US tax to credit it against. The
 * ranking therefore inverts between US dividend brackets, which is why
 * {@link shelterPriorityBp} has to be computed per reader rather than asserted once.
 *
 * `after_tax_path` is deliberately **not** ported: it is a stateful year-by-year
 * compounding loop with tax-lot bookkeeping, and a subtly wrong version would be worse
 * than none. The `deferralPaths` and `disposalPaths` fixtures are therefore unused.
 */

/** One basis point, and the unit every drag below is reported in. */
const BASIS_POINT = 1e-4;

/** A dated set of marginal rates, expressed as decimals. */
export type TaxRegime = {
  readonly label: string;
  /** The date every rate in this regime is stated as of. A rate without one is a trap. */
  readonly asOf: string;
  readonly ordinaryIncome: number;
  readonly longTermCapitalGain: number;
  /**
   * The US §1411 surtax, which applies on top of both the ordinary and the long-term
   * rate above a modified-AGI threshold that is not inflation indexed, so the fraction
   * of investors paying it rises every year by construction.
   */
  readonly netInvestmentIncome: number;
};

/** The all-in marginal rates implied by a regime, once the §1411 surtax is added. */
export type DerivedRates = {
  /** All-in marginal rate on ordinary income. */
  readonly ordinary: number;
  /** All-in marginal rate on long-term capital gain. */
  readonly capitalGain: number;
  /**
   * Qualified dividends are taxed at the long-term rate (26 U.S.C. §1(h)(11)),
   * conditional on the §1(h)(11)(B)(iii) holding period and on the payer qualifying. A
   * fund failing the test on part of its book reports the shortfall as ordinary income,
   * which is {@link DerivedRates.ordinary} and not this rate.
   */
  readonly qualifiedDividend: number;
  /**
   * `0.6 x long-term + 0.4 x ordinary`: 26 U.S.C. §1256(a)(3). The statute assigns the
   * split without regard to holding period, so it is a rate reduction against ordinary
   * treatment and a rate *increase* against deferred long-term treatment.
   */
  readonly section1256Blended: number;
};

/** Derive the all-in rates from a regime's statutory ones. */
export function derivedRates(regime: TaxRegime): DerivedRates {
  const ordinary = regime.ordinaryIncome + regime.netInvestmentIncome;
  const capitalGain = regime.longTermCapitalGain + regime.netInvestmentIncome;
  return {
    ordinary,
    capitalGain,
    qualifiedDividend: capitalGain,
    section1256Blended: 0.6 * capitalGain + 0.4 * ordinary,
  };
}

/** An asset competing for a dollar of tax-advantaged shelter capacity. */
export type ShelterCandidate = {
  readonly label: string;
  /** Gross of any foreign withholding. */
  readonly dividendYield: number;
  /** The share of the distribution taxed at the qualified rate; the rest is ordinary. */
  readonly qualifiedFraction: number;
  readonly foreignWithholdingRate: number;
};

/** A stated international equity sleeve. Its yield is gross of withholding. */
export type ForeignSleeve = {
  readonly label: string;
  readonly dividendYield: number;
  readonly withholdingRate: number;
};

/** One row of a shelter ranking. */
export type ShelterPriority = {
  readonly label: string;
  readonly priorityBp: number;
};

/**
 * Annual recurring tax if this asset sits in the taxable account, in bp/yr.
 *
 * The foreign tax is paid at source in every case; the US tax on the same dividend is
 * then reduced by whatever credit the investor can actually use. Capping the credit at
 * the US tax is not decoration — an unused §901 credit is **not refundable**. It carries
 * back one year and forward ten (§904(c)), and in a 0% bracket it usually expires.
 */
export function taxableCostBp(
  candidate: ShelterCandidate,
  regime: TaxRegime,
  { foreignCreditUtilisation = 1 }: { readonly foreignCreditUtilisation?: number } = {}
): number {
  assertUtilisation(foreignCreditUtilisation);
  const rates = derivedRates(regime);
  const gross = candidate.dividendYield;
  const foreignTax = candidate.foreignWithholdingRate * gross;
  const usTax =
    rates.qualifiedDividend * candidate.qualifiedFraction * gross +
    rates.ordinary * (1 - candidate.qualifiedFraction) * gross;
  const credit = Math.min(foreignCreditUtilisation * foreignTax, usTax);
  return (foreignTax + usTax - credit) / BASIS_POINT;
}

/**
 * Annual recurring tax if this asset sits inside a shelter, in bp/yr.
 *
 * Zero for everything except an asset subject to foreign withholding, which leaks `w y`
 * a year in **every** account type, traditional and Roth alike, because §901 credits a
 * foreign tax against a *US* tax and a sheltered account generates none. That asymmetry
 * is the whole mechanism, and it is why a ranking computed on taxable cost alone —
 * which is what the standard rule is — is not the right ranking.
 */
export function shelteredCostBp(candidate: ShelterCandidate): number {
  return (candidate.foreignWithholdingRate * candidate.dividendYield) / BASIS_POINT;
}

/**
 * Rank assets by what a dollar of shelter capacity saves, highest first:
 *
 *     priority = (taxable recurring tax) - (irrecoverable foreign withholding).
 *
 * For every asset except a foreign one the second term is zero and the rule collapses to
 * the familiar "shelter the heaviest recurring tax burden". For a foreign equity sleeve
 * it does not, and the correction is exactly the forfeited credit.
 *
 * Ties are broken by label, ascending, so the ordering is deterministic. The comparison
 * is by code point rather than by locale, to keep the order independent of the reader's.
 */
export function shelterPriorityBp(
  candidates: readonly ShelterCandidate[],
  { regime, foreignCreditUtilisation = 1 }: { readonly regime: TaxRegime; readonly foreignCreditUtilisation?: number }
): readonly ShelterPriority[] {
  const scored = candidates.map((candidate) => ({
    label: candidate.label,
    priorityBp: taxableCostBp(candidate, regime, { foreignCreditUtilisation }) - shelteredCostBp(candidate),
  }));
  return scored.sort((a, b) => {
    if (a.priorityBp !== b.priorityBp) return b.priorityBp - a.priorityBp;
    if (a.label === b.label) return 0;
    return a.label < b.label ? -1 : 1;
  });
}

/** A sleeve competing for shelter capacity, already priced. */
export type WeightedSleeve = {
  readonly label: string;
  /** Fraction of the base the capacity is also expressed against. */
  readonly weight: number;
  readonly priorityBp: number;
};

/**
 * Fill a shelter of size `capacity` highest-priority-first, and return the saving.
 *
 * Weights and `capacity` are fractions of the same base, so the result is bp/yr **of
 * that base**. Ties break by label, matching {@link shelterPriorityBp}.
 *
 * A ranking is not an answer on its own. Below the first sleeve's weight only the top
 * line matters; once capacity covers everything, placement is worth nothing at all,
 * because every dollar is sheltered whatever the order. The interesting range is in
 * between, and it is the reader's own balances that decide where they sit in it.
 */
export function fillShelterBp(sleeves: readonly WeightedSleeve[], { capacity }: { readonly capacity: number }): number {
  if (!(capacity >= 0)) {
    throw new RangeError(`capacity must be non-negative, got ${capacity}`);
  }
  for (const sleeve of sleeves) {
    if (!(sleeve.weight >= 0)) {
      throw new RangeError(`${sleeve.label}: weight must be non-negative, got ${sleeve.weight}`);
    }
  }
  const ordered = [...sleeves].sort((a, b) => {
    if (a.priorityBp !== b.priorityBp) return b.priorityBp - a.priorityBp;
    if (a.label === b.label) return 0;
    return a.label < b.label ? -1 : 1;
  });
  let remaining = capacity;
  let saving = 0;
  for (const sleeve of ordered) {
    const placed = Math.min(sleeve.weight, remaining);
    saving += placed * sleeve.priorityBp;
    remaining -= placed;
    if (remaining <= 0) break;
  }
  return saving;
}

/**
 * The marginal qualified-dividend rate at which the two placements of an international
 * and a domestic sleeve tie.
 *
 * Equating "international taxable, domestic sheltered" with its mirror,
 *
 *     q y_i + (1 - u) w y_i  =  w y_i + q y_d
 *     q (y_i - y_d)          =  u w y_i
 *     q*                     =  u w y_i / (y_i - y_d),
 *
 * which reads as the sentence it is: **the international sleeve belongs in the taxable
 * account whenever the investor's dividend rate is below the withholding rate scaled by
 * the ratio of the international yield to the yield gap.** The rule flips on the
 * investor's bracket, not on any property of the funds.
 *
 * Throws when the international yield does not exceed the domestic one, because the
 * shelter should then hold the domestic asset for reasons unrelated to the credit.
 */
export function locationBreakevenRate({
  international,
  domesticDividendYield,
  foreignCreditUtilisation = 1,
}: {
  readonly international: ForeignSleeve;
  readonly domesticDividendYield: number;
  readonly foreignCreditUtilisation?: number;
}): number {
  assertUtilisation(foreignCreditUtilisation);
  if (!(domesticDividendYield >= 0 && domesticDividendYield < 1)) {
    throw new RangeError(`domesticDividendYield must lie in [0, 1), got ${domesticDividendYield}`);
  }
  const gap = international.dividendYield - domesticDividendYield;
  if (gap <= 0) {
    throw new RangeError(
      "the international yield must exceed the domestic yield for this comparison to be about the credit at all"
    );
  }
  return foreignCreditUtilisation * international.withholdingRate * (international.dividendYield / gap);
}

/**
 * Sleeve value at which foreign tax paid reaches the Form 1116 filing threshold.
 *
 * Creditable foreign tax at or below $300 (single) or $600 (joint), all of it qualified
 * passive income, may be claimed directly — without Form 1116 and **without the §904
 * limitation calculation**. Above the threshold the limitation binds, which is precisely
 * where `foreignCreditUtilisation` stops being 1.
 *
 * `foreign tax = assets x yield x withholding rate`, so the threshold in assets is
 * `limit / (yield x withholding rate)`.
 */
export function form1116ThresholdAssets({
  foreignTaxLimit,
  sleeve,
}: {
  readonly foreignTaxLimit: number;
  readonly sleeve: ForeignSleeve;
}): number {
  if (!(foreignTaxLimit > 0)) {
    throw new RangeError(`foreignTaxLimit must be positive, got ${foreignTaxLimit}`);
  }
  const perDollar = sleeve.dividendYield * sleeve.withholdingRate;
  if (!(perDollar > 0)) {
    throw new RangeError(`${sleeve.label}: a sleeve with no withheld tax has no threshold`);
  }
  return foreignTaxLimit / perDollar;
}

/**
 * `yield x withholding rate` in bp/yr: the cost of sheltering this sleeve.
 *
 * This is the whole of the foreign tax credit forfeiture. It is exact, it is annual, it
 * is permanent, and it applies identically to a traditional and a Roth account.
 */
export function forfeitedBp(sleeve: ForeignSleeve): number {
  return (sleeve.dividendYield * sleeve.withholdingRate) / BASIS_POINT;
}

function assertUtilisation(foreignCreditUtilisation: number): void {
  if (!(foreignCreditUtilisation >= 0 && foreignCreditUtilisation <= 1)) {
    throw new RangeError(`foreignCreditUtilisation must lie in [0, 1], got ${foreignCreditUtilisation}`);
  }
}
