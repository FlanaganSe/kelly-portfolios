"""The fixed-income shelf: an investable bond leg, and whether TIPS are a second engine.

Why this module exists
----------------------
Until 2026-08-17 every bond figure in this repository came from one of two places, and
neither was a measured investable total return:

* a **modelled** ten-year par bond reconstructed from FRED ``GS10`` -- Experiment 004's
  robustness arm, Experiment 010's ``long_duration_treasury_proxy``, and the whole
  equity/bond ladder in ``docs/research/setting-the-equity-share.md``; and
* nothing at all for TIPS, standalone credit, or any maturity bucket.

``docs/research/search-coverage.md`` carried that as the last open row of "any asset
outside equity and cash". This module closes the measurement half of it from two
sources that were both already reachable:

**Long and measured, 1926-01 onward.** Goyal-Welch ``ltr`` and ``corpr`` are monthly
total returns on long-term US government and long-term investment-grade corporate
bonds. They were in this repository's cache and manifests the whole time and no
experiment had read them for a bond leg. That is the **sixth** source recorded here as
absent that turned out to be published, after Goyal-Welch itself, Shiller, gold, French
``RlEst`` and FRED's bitcoin price -- and the first that was already downloaded.

**Short and investable, 2019 onward.** Form N-PORT Item B.5 gives eighteen bond and
TIPS ETFs' own filed monthly total returns, net of their own fees, on the same footing
as the REIT and dividend work in ``docs/research/alternative-sleeves-audit.md``.

Neither is a substitute for the other and the module never splices them. ``ltr`` is a
roughly twenty-year duration index, gross of any fee, and not investable; the funds are
investable and six years long.

What decides, and the two ways to get it wrong
----------------------------------------------
Scoring is :mod:`portfolio_edge.studies.retail_shelf`'s, unchanged, because the question
is the same one: does the sleeve raise growth beside a cheap equity core. The instrument
is chosen by :func:`portfolio_edge.studies.retail_shelf.choose_instrument` from the
measured correlation and never by hand, and on this shelf **the choice is not uniform
across the funds** -- nominal Treasury funds sit below the 0.5 first-order limit and TIPS
funds sit above it. Assuming one instrument for "bonds" would have mis-scored half the
shelf, which is the failure :mod:`portfolio_edge.studies.overlay_growth` documents.

The arithmetic here that is not already in ``retail_shelf``
-----------------------------------------------------------
1. :func:`par_bond_risk` -- the same closed form as
   :func:`portfolio_edge.experiments.exp_010_marginal_sleeve_value.par_bond_risk`
   **with its positive-yield guard replaced by a limit at zero**. That guard is right
   for a nominal Treasury and wrong for a TIPS: the ten-year real constant-maturity
   yield was negative in **45 of the 283 months** FRED publishes, so the guard would
   refuse the only long TIPS series available rather than price it. A test holds this
   function against the exp_010 copy at positive yields and against numerical
   differentiation of the exact par-bond price at negative ones.
2. :func:`tips_nominal_total_return` -- a modelled TIPS total return in **nominal**
   terms, so that it can be correlated with a nominal equity return. The real leg is a
   real par bond priced off ``FII10``; the inflation leg is the non-seasonally-adjusted
   CPI-U with the statutory three-month lag. 31 CFR 356.2 defines the index this way
   ("the monthly non-seasonally adjusted U.S. City Average All Items Consumer Price
   Index for All Urban Consumers") and appendix B section I paragraph B sets the lag
   ("Ref CPI April 1 is the CPI January"), both read from eCFR on 2026-08-17.
3. :func:`correlation_stability` -- non-overlapping fixed-length block correlations and
   their dispersion. The question "is this sleeve's correlation to equity stable" needs
   a statistic that is fixed before the data are seen, because a split chosen after
   looking at the series is a split chosen on the answer. The block length is an
   argument and every table states it.

None of this reads the cache; :mod:`portfolio_edge.studies._fixed_income_tables` is the
one file that does.
"""

from __future__ import annotations

import itertools
import math
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np

from portfolio_edge.core._types import FloatArray

__all__ = [
    "FIXED_INCOME_SHELF",
    "REF_CPI_LAG_MONTHS",
    "CorrelationStability",
    "ShelfEntry",
    "annualised",
    "correlation_stability",
    "correlation_standard_error",
    "months_between",
    "par_bond_risk",
    "par_bond_total_returns",
    "tips_nominal_total_return",
]

#: Per-period yield below which the convexity closed form is replaced by its limit.
_NEAR_ZERO_YIELD: Final = 1e-6

#: 31 CFR 356 appendix B section I paragraph B: the Ref CPI for the first day of a
#: month is the published CPI-U for the calendar month three months earlier.
REF_CPI_LAG_MONTHS: Final = 3


@dataclass(frozen=True, slots=True, kw_only=True)
class ShelfEntry:
    """One fund on the fixed-income shelf, keyed to the SEC identifiers it files under.

    ``family`` groups the exposure, not the sponsor. ``exposure`` states in words what
    the fund is a claim on, because "a 0.03% bond fund" is a statement about the
    wrapper and the decision turns on the duration, the credit quality and whether the
    coupon is real or nominal.
    """

    ticker: str
    family: str
    series_id: str
    class_id: str
    registrant_cik: int
    exposure: str
    role: str = "sleeve"


#: The shelf as audited. Series and class identifiers are EDGAR's own, resolved from
#: ``https://www.sec.gov/files/company_tickers_mf.json`` retrieved 2026-08-17, so a
#: share class cannot be silently re-pointed at a different product.
FIXED_INCOME_SHELF: Final[tuple[ShelfEntry, ...]] = (
    ShelfEntry(
        ticker="SCHP", family="tips", series_id="S000029407", class_id="C000090317",
        registrant_cik=1454889, exposure="broad-maturity US TIPS, real coupon",
    ),
    ShelfEntry(
        ticker="TIP", family="tips", series_id="S000004363", class_id="C000012093",
        registrant_cik=1100663, exposure="broad-maturity US TIPS, real coupon",
    ),
    ShelfEntry(
        ticker="SPIP", family="tips", series_id="S000017330", class_id="C000047967",
        registrant_cik=1064642, exposure="broad-maturity US TIPS, real coupon",
    ),
    ShelfEntry(
        ticker="VTIP", family="tips", series_id="S000038501", class_id="C000118815",
        registrant_cik=836906, exposure="0-5 year US TIPS, real coupon",
    ),
    ShelfEntry(
        ticker="STIP", family="tips", series_id="S000030481", class_id="C000093655",
        registrant_cik=1100663, exposure="0-5 year US TIPS, real coupon",
    ),
    ShelfEntry(
        ticker="LTPZ", family="tips", series_id="S000026343", class_id="C000079104",
        registrant_cik=1450011, exposure="15+ year US TIPS, real coupon",
    ),
    ShelfEntry(
        ticker="SCHO", family="treasury", series_id="S000029408", class_id="C000090318",
        registrant_cik=1454889, exposure="1-3 year nominal US Treasury",
    ),
    ShelfEntry(
        ticker="VGSH", family="treasury", series_id="S000026859", class_id="C000080843",
        registrant_cik=1021882, exposure="1-3 year nominal US Treasury",
    ),
    ShelfEntry(
        ticker="SCHR", family="treasury", series_id="S000029409", class_id="C000090319",
        registrant_cik=1454889, exposure="3-10 year nominal US Treasury",
    ),
    ShelfEntry(
        ticker="VGIT", family="treasury", series_id="S000026860", class_id="C000080846",
        registrant_cik=1021882, exposure="3-10 year nominal US Treasury",
    ),
    ShelfEntry(
        ticker="VGLT", family="treasury", series_id="S000026861", class_id="C000080849",
        registrant_cik=1021882, exposure="10-25 year nominal US Treasury",
    ),
    ShelfEntry(
        ticker="TLT", family="treasury", series_id="S000004360", class_id="C000012090",
        registrant_cik=1100663, exposure="20+ year nominal US Treasury",
    ),
    ShelfEntry(
        ticker="GOVT", family="treasury", series_id="S000035919", class_id="C000110086",
        registrant_cik=1100663,
        exposure="1-30 year nominal US Treasury, all maturities",
    ),
    ShelfEntry(
        ticker="BND", family="aggregate", series_id="S000002564", class_id="C000046844",
        registrant_cik=794105,
        exposure="US investment-grade aggregate: Treasury, agency MBS, IG credit",
    ),
    ShelfEntry(
        ticker="AGG", family="aggregate", series_id="S000004362", class_id="C000012092",
        registrant_cik=1100663,
        exposure="US investment-grade aggregate: Treasury, agency MBS, IG credit",
    ),
    ShelfEntry(
        ticker="LQD", family="credit", series_id="S000004361", class_id="C000012091",
        registrant_cik=1100663, exposure="US investment-grade corporate, all maturities",
    ),
    ShelfEntry(
        ticker="VCIT", family="credit", series_id="S000026863", class_id="C000080855",
        registrant_cik=1021882, exposure="5-10 year US investment-grade corporate",
    ),
    ShelfEntry(
        ticker="HYG", family="credit", series_id="S000016772", class_id="C000046846",
        registrant_cik=1100663, exposure="US high-yield corporate",
    ),
    ShelfEntry(
        ticker="VTI", family="control", series_id="S000002848", class_id="C000007808",
        registrant_cik=36405, exposure="US total stock market", role="base",
    ),
)


# --------------------------------------------------------------------------------
# 1. Par-bond arithmetic that does not refuse a negative real yield
# --------------------------------------------------------------------------------


def par_bond_risk(annual_yield: float, *, periods: float) -> tuple[float, float]:
    """Modified duration and convexity, in years and years squared, of a par bond.

    Identical closed form to
    :func:`portfolio_edge.experiments.exp_010_marginal_sleeve_value.par_bond_risk`,
    and a test holds the two together at positive yields so they cannot drift. **The
    difference is the domain.** That function raises on a non-positive yield, which is
    correct for a nominal Treasury and wrong for an inflation-indexed one: FRED
    ``FII10``, the only long real-yield series available here, is negative in 45 of its
    283 monthly observations and touches zero exactly.

    At ``annual_yield = 0`` the closed form is a removable singularity and the limits
    are ``periods / 2`` and ``periods (periods + 1) / 4`` -- a par bond with a zero
    coupon, whose modified duration is its maturity. Both limits are checked in the
    tests against numerical differentiation of the exact price function rather than
    against this function's own output.

    The limit branch is taken below :data:`_NEAR_ZERO_YIELD` rather than at exactly
    zero because the convexity expression is a difference of two terms of order
    ``1/half``, so it loses relative precision to cancellation as the yield approaches
    zero: at a per-period yield of ``5e-8`` the closed form returns 104.67 where the
    limit is 105. The threshold sits four orders of magnitude below the smallest yield
    the source data can express -- Treasury quotes the real curve to 0.01% -- so no
    observation used here is ever inside it.
    """
    if periods <= 0.0:
        raise ValueError(f"periods must be positive, got {periods}")
    half = annual_yield / 2.0
    if half <= -1.0:
        raise ValueError(
            f"a per-period yield of {half} makes the discount factor undefined; a par "
            f"bond cannot be priced at an annual yield of {annual_yield}"
        )
    if abs(half) < _NEAR_ZERO_YIELD:
        return periods / 2.0, periods * (periods + 1.0) / 4.0
    discount = (1.0 + half) ** -periods
    modified = (1.0 - discount) / (2.0 * half)
    convexity = ((1.0 - discount) / half**2 - periods * discount / (half * (1.0 + half))) / 2.0
    return modified, convexity


def months_between(earlier: str, later: str) -> int:
    """Whole months from one ``YYYY-MM`` to another. Negative if ``later`` is earlier."""
    return (int(later[:4]) * 12 + int(later[5:7])) - (
        int(earlier[:4]) * 12 + int(earlier[5:7])
    )


def par_bond_total_returns(
    yields: Mapping[str, float], *, maturity_years: float
) -> dict[str, float]:
    """One-month total returns of a rolled par bond, from a monthly yield level.

    ``yields`` maps ``YYYY-MM`` to an annual yield as a decimal. The return for month
    ``t`` accrues one month of the coupon struck at ``t-1``'s yield and reprices at
    ``t``'s, to second order. **A month whose predecessor is missing is skipped**, never
    bridged, so a gap in the source cannot become a fabricated return.

    THIS IS A MODELLED SERIES. It has no on-the-run premium, no bid/ask, no tax, no
    index roll rule and no coupon reinvestment convention. It exists so that a real and
    a nominal yield curve can be compared on identical construction; where a measured
    total return is available -- Goyal-Welch ``ltr`` and ``corpr``, or a fund's own
    Item B.5 -- that is the series to use.
    """
    months = sorted(yields)
    out: dict[str, float] = {}
    for earlier, later in itertools.pairwise(months):
        if months_between(earlier, later) != 1:
            continue
        start = yields[earlier]
        change = yields[later] - start
        modified, convexity = par_bond_risk(start, periods=2.0 * maturity_years)
        out[later] = start / 12.0 - modified * change + 0.5 * convexity * change**2
    return out


def tips_nominal_total_return(
    real_returns: Mapping[str, float],
    consumer_prices: Mapping[str, float],
    *,
    lag_months: int = REF_CPI_LAG_MONTHS,
) -> dict[str, float]:
    """Gross a real bond return up by the reference-CPI inflation it accrues.

    ``real_returns`` is a real par bond's monthly total return in constant dollars;
    ``consumer_prices`` is the **non-seasonally-adjusted** CPI-U index level by month.
    The month ``t`` return is ``(1 + real_t)(1 + pi_t) - 1`` where ``pi_t`` is the CPI
    change over the month ``lag_months`` earlier, which is the security's own index
    ratio to the accuracy a monthly series can carry.

    ``lag_months`` is an argument rather than a constant so that a caller can measure
    how much the answer depends on it. Measured here: moving it from three to zero
    changes the correlation to equity by 0.009, so nothing in this study turns on it.

    Two things this is not. It is not a TIPS *index* return -- a real index rolls,
    weights by outstanding amount and holds seasoned issues off the constant-maturity
    point. And it is not a fund return: it carries no fee and no bid/ask.
    """
    if lag_months < 0:
        raise ValueError(f"lag_months must be non-negative, got {lag_months}")
    months = sorted(consumer_prices)
    inflation: dict[str, float] = {}
    for earlier, later in itertools.pairwise(months):
        if months_between(earlier, later) != 1:
            continue
        target = int(later[:4]) * 12 + int(later[5:7]) + lag_months
        key = f"{(target - 1) // 12:04d}-{((target - 1) % 12) + 1:02d}"
        inflation[key] = consumer_prices[later] / consumer_prices[earlier] - 1.0
    return {
        month: (1.0 + real) * (1.0 + inflation[month]) - 1.0
        for month, real in real_returns.items()
        if month in inflation
    }


# --------------------------------------------------------------------------------
# 2. Is a correlation stable, on a statistic fixed before the data are seen
# --------------------------------------------------------------------------------


@dataclass(frozen=True)
class CorrelationStability:
    """One series' correlation to a base, full sample and in non-overlapping blocks.

    ``dispersion`` is the sample standard deviation of the block correlations and
    ``span`` their range. Neither is a test statistic with a distribution attached --
    they are descriptive, and a comparison between two series is only meaningful on
    **identical months and identical block boundaries**, which
    :func:`correlation_stability` enforces by taking the months from the caller.

    ``flips_sign`` is the field the portfolio argument actually turns on: a sleeve held
    for diversification whose correlation to equity changes sign across eras is not
    diversifying in the era that matters, and this repository has already measured
    exactly that for nominal Treasuries.
    """

    label: str
    months: int
    block_months: int
    full_sample: float
    blocks: tuple[tuple[str, str, float], ...]

    @property
    def dispersion(self) -> float:
        values = [value for _, _, value in self.blocks]
        return statistics.stdev(values) if len(values) > 1 else float("nan")

    @property
    def span(self) -> float:
        values = [value for _, _, value in self.blocks]
        return max(values) - min(values) if len(values) > 1 else float("nan")

    @property
    def flips_sign(self) -> bool:
        values = [value for _, _, value in self.blocks]
        return any(value > 0.0 for value in values) and any(value < 0.0 for value in values)


def correlation_stability(
    series: Mapping[str, float],
    base: Mapping[str, float],
    months: Sequence[str],
    *,
    label: str,
    block_months: int = 60,
) -> CorrelationStability:
    """Correlation to ``base`` over ``months``, and over consecutive blocks of it.

    ``months`` is passed in rather than derived so that two series are compared on the
    same window and the same block edges. A trailing partial block is **dropped**, not
    reported short: a correlation from eleven months and one from sixty are not two
    readings of the same quantity.
    """
    if block_months < 2:
        raise ValueError(f"block_months must be at least 2, got {block_months}")
    missing = [month for month in months if month not in series or month not in base]
    if missing:
        raise ValueError(
            f"{label}: {len(missing)} of {len(months)} months are missing from one of "
            f"the two series, first {missing[0]}. Align the window in the caller and "
            "state what it dropped rather than silently comparing different periods."
        )
    left = np.array([series[month] for month in months], dtype=np.float64)
    right = np.array([base[month] for month in months], dtype=np.float64)
    blocks: list[tuple[str, str, float]] = []
    for start in range(0, len(months) - block_months + 1, block_months):
        stop = start + block_months
        blocks.append(
            (
                months[start],
                months[stop - 1],
                float(np.corrcoef(left[start:stop], right[start:stop])[0, 1]),
            )
        )
    return CorrelationStability(
        label=label,
        months=len(months),
        block_months=block_months,
        full_sample=float(np.corrcoef(left, right)[0, 1]),
        blocks=tuple(blocks),
    )


def correlation_standard_error(correlation: float, months: int) -> float:
    """Large-sample standard error of a Pearson correlation, ``(1 - r**2)/sqrt(n-3)``.

    Quoted beside every correlation in this study for the same reason every mean here
    carries a minimum detectable effect: a correlation of 0.13 from 275 months and one
    from 79 are not equally informative, and the resolution table in
    ``docs/research/evidence-base.md`` requires the difference to be visible.
    """
    if months < 4:
        raise ValueError(f"a correlation standard error needs at least 4 months, got {months}")
    return (1.0 - correlation**2) / math.sqrt(months - 3)


def annualised(
    monthly: Sequence[float] | FloatArray, *, periods_per_year: int = 12
) -> tuple[float, float]:
    """Arithmetic mean and standard deviation of a monthly series, scaled to a year."""
    values = np.asarray(monthly, dtype=np.float64)
    if values.size < 2:
        raise ValueError("at least two observations are needed")
    return (
        float(np.mean(values)) * periods_per_year,
        float(np.std(values, ddof=1)) * math.sqrt(periods_per_year),
    )
