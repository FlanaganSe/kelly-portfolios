"""Can this portfolio be *run*? Units, accounts, and the price of maintaining it.

Every other question about the stacked candidate asks what it should hold. This module
asks whether an investor with three accounts can keep holding it, and prices the answer.
It is the executable record behind the operating half of
``docs/research/rebalancing-policy.md``.

Three results organise it, and each is arithmetic rather than a forecast.

**1. Capital is the only unit you can type.** A stacked wrapper delivers more notional
than the capital placed in it, so a capital weight and a notional weight are different
numbers for the same position. The conversion is linear and one-directional: capital is
observable on a brokerage screen and is what a trade moves; notional is a *derived*
quantity read off a dated holdings filing and is not stable between filings. So the
rebalancing target must be a capital-weight vector, and the notional it implies is an
audit figure recomputed at each review. :func:`implied_notional` and
:func:`capital_for_notional` are the two directions, and
:func:`normalised_notional_capital` reproduces the specific mistake an investor makes
when they try to type a notional table into a brokerage that adds to 100%.

**2. Rebalancing across accounts has an exact feasibility condition.** Let ``v`` be what
the taxable account holds, as a share of total wealth, and ``w*`` the portfolio target.
Sheltered accounts can be reallocated freely, so the reachable set is
``{v + s : s >= 0, sum(s) = 1 - sum(v)}``. Therefore

    ``w*`` is reachable without a taxable sale **iff** ``v_i <= w*_i`` for every fund.

The distance to infeasibility is ``min_i (w*_i - v_i)``, which :func:`headroom` returns
and an investor can watch as a single number. **At target it equals the sheltered holding
of that fund**, because ``w*_i = v_i + s_i``, so the rule needs no arithmetic at all: the
headroom on a line is however much of it sits somewhere you are allowed to sell.

A placement that fills the taxable account to exactly a fund's target weight therefore has
*zero* headroom, and the first month that fund outperforms, the portfolio target stops
being reachable. :func:`nearest_reachable` projects onto the reachable set so that the miss
can be measured rather than asserted.

**3. What a forced taxable trade costs is not the spread.** It is the realised gain times
the rate, and :func:`forced_realisation_cost` charges both. At retail ETF spreads the tax
term is two to three orders of magnitude larger than the friction term, which is why the
right question is never "how expensive is this trade" but "can this trade be avoided".

Scope. US federal, individual investor. Placement, contribution and rate assumptions are
arguments, never constants. Nothing here is a return claim: the simulation reports
exposure control, trade counts, realised gains and tax, and the growth columns exist to
show that the return difference is inside the design's resolution rather than to argue a
direction. ``docs/research/rebalancing-policy.md`` already rejects rebalancing as a
source of return on a 35-year window and that rejection is not revisited here.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Final

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.core.costs import ProportionalCostModel
from portfolio_edge.studies.notional_budget import (
    EQUITY_KINDS,
    Holding,
    NotionalLeg,
    portfolio_exposure,
)

FloatArray = NDArray[np.float64]
Series = Sequence[float] | FloatArray
"""Anything the study will read as a return or difference series."""

MONTHS_PER_YEAR: Final = 12

AS_OF: Final = "2026-08-22"
"""Every rate, weight and structural figure in this module is stated as of this date."""

# --------------------------------------------------------------------------------
# 1. The candidate, in the units the investor can actually type.
# --------------------------------------------------------------------------------

#: The stacked candidate's capital weights, from ``src/content/portfolios.ts``. Eight
#: lines, not nine: the portfolio is sometimes described as nine-line because the trend
#: leg is counted separately from the equity leg of the same fund, which is exactly the
#: units error this module exists to prevent.
CANDIDATE_CAPITAL: Final[Mapping[str, float]] = {
    "RSST": 0.30,
    "VTI": 0.20,
    "AVLV": 0.15,
    "DFIV": 0.10,
    "VEA": 0.10,
    "IDMO": 0.05,
    "IEMG": 0.05,
    "AVES": 0.05,
}

#: Notional legs per dollar of capital. RSST's are read from its 2026-04-30 Form N-PORT
#: (74.09% of net assets in a physical S&P 500 fund plus 33.1% in E-mini futures is 107.2%
#: equity; the trend book runs ~294% gross notional to deliver ~100% of risk exposure) and
#: mirror ``src/content/shelf.ts``. Every other line is an unlevered long-only fund and
#: carries exactly one leg at 1.0.
CANDIDATE_LEGS: Final[Mapping[str, tuple[NotionalLeg, ...]]] = {
    "RSST": (NotionalLeg("us-equity", 1.072), NotionalLeg("trend", 1.0)),
    "VTI": (NotionalLeg("us-equity", 1.0),),
    "AVLV": (NotionalLeg("us-equity", 1.0),),
    "DFIV": (NotionalLeg("developed-ex-us-equity", 1.0),),
    "VEA": (NotionalLeg("developed-ex-us-equity", 1.0),),
    "IDMO": (NotionalLeg("developed-ex-us-equity", 1.0),),
    "IEMG": (NotionalLeg("emerging-equity", 1.0),),
    "AVES": (NotionalLeg("emerging-equity", 1.0),),
}

#: Kinds that count as equity beta for this portfolio. Extends the shared set with the two
#: regional labels this candidate uses, in one place, for the reason the shared set exists.
CANDIDATE_EQUITY_KINDS: Final[frozenset[str]] = EQUITY_KINDS | {
    "developed-ex-us-equity",
    "emerging-equity",
}


def _as_holdings(
    capital: Mapping[str, float],
    legs: Mapping[str, tuple[NotionalLeg, ...]] = CANDIDATE_LEGS,
) -> tuple[Holding, ...]:
    missing = sorted(set(capital) - set(legs))
    if missing:
        raise KeyError(f"no notional legs declared for {missing}")
    return tuple(Holding(name, weight, legs[name]) for name, weight in capital.items())


def implied_notional(
    capital: Mapping[str, float],
    *,
    legs: Mapping[str, tuple[NotionalLeg, ...]] = CANDIDATE_LEGS,
    equity_kinds: frozenset[str] = CANDIDATE_EQUITY_KINDS,
) -> Mapping[str, float]:
    """Notional exposure by kind, per dollar of capital, from capital weights.

    This is the only direction that is safe to compute automatically. The reverse map is
    :func:`capital_for_notional` and needs a stated rule for which lines absorb the
    adjustment, because several capital weights produce the same notional.
    """
    summary = portfolio_exposure(_as_holdings(capital, legs), equity_kinds=equity_kinds)
    return dict(summary.by_kind)


def gross_notional(
    capital: Mapping[str, float],
    *,
    legs: Mapping[str, tuple[NotionalLeg, ...]] = CANDIDATE_LEGS,
    equity_kinds: frozenset[str] = CANDIDATE_EQUITY_KINDS,
) -> float:
    """Total notional per dollar of capital. 1.0 for an unlevered portfolio."""
    summary = portfolio_exposure(_as_holdings(capital, legs), equity_kinds=equity_kinds)
    return summary.gross_notional


def capital_for_notional(
    capital: Mapping[str, float],
    *,
    kind: str,
    target: float,
    adjust: Sequence[str],
    legs: Mapping[str, tuple[NotionalLeg, ...]] = CANDIDATE_LEGS,
) -> Mapping[str, float]:
    """Rescale ``adjust`` so that ``kind``'s notional hits ``target``, holding the rest.

    The adjustable lines keep their ratios to one another, which is the only rule that
    does not require a second decision. The freed or consumed capital lands in cash, so
    the returned weights need not sum to one — that shortfall or overflow is the honest
    report that a notional target and a capital budget are separate constraints.
    """
    if not adjust:
        raise ValueError("at least one line must be adjustable")
        # A notional target with nothing to adjust is a constraint, not a solution.
    unknown = sorted(set(adjust) - set(capital))
    if unknown:
        raise KeyError(f"adjustable lines not in the portfolio: {unknown}")

    def leg_total(name: str) -> float:
        return sum(leg.per_dollar_of_capital for leg in legs[name] if leg.kind == kind)

    movable = sum(capital[name] * leg_total(name) for name in adjust)
    fixed = sum(
        capital[name] * leg_total(name) for name in capital if name not in set(adjust)
    )
    if movable <= 0.0:
        raise ValueError(
            f"none of {list(adjust)} carries any {kind!r} notional, so no rescaling of "
            "them can reach the target"
        )
    scale = (target - fixed) / movable
    if scale < 0.0:
        raise ValueError(
            f"reaching {target} of {kind!r} would need a negative weight; the fixed "
            f"lines already carry {fixed}"
        )
    return {
        name: (weight * scale if name in set(adjust) else weight)
        for name, weight in capital.items()
    }


@dataclass(frozen=True, slots=True)
class UnitMistake:
    """What a stated capital plan actually delivers, against what it was meant to.

    ``capital_deployed`` below 1.0 is idle cash; above 1.0 is a plan that cannot be
    funded. ``error_by_kind`` is delivered minus intended, in the same units as
    :func:`implied_notional`.
    """

    label: str
    capital: Mapping[str, float]
    capital_deployed: float
    delivered: Mapping[str, float]
    intended: Mapping[str, float]
    error_by_kind: Mapping[str, float]
    gross_notional: float

    @property
    def worst_error(self) -> tuple[str, float]:
        """The kind furthest from intent, and by how much."""
        kind = max(self.error_by_kind, key=lambda k: abs(self.error_by_kind[k]))
        return kind, self.error_by_kind[kind]


def _unit_mistake(
    label: str,
    capital: Mapping[str, float],
    intended: Mapping[str, float],
    *,
    legs: Mapping[str, tuple[NotionalLeg, ...]] = CANDIDATE_LEGS,
) -> UnitMistake:
    delivered = implied_notional(capital, legs=legs)
    kinds = sorted(set(delivered) | set(intended))
    return UnitMistake(
        label=label,
        capital=dict(capital),
        capital_deployed=sum(capital.values()),
        delivered=delivered,
        intended=dict(intended),
        error_by_kind={
            kind: delivered.get(kind, 0.0) - intended.get(kind, 0.0) for kind in kinds
        },
        gross_notional=gross_notional(capital, legs=legs),
    )


def normalised_notional_capital(
    capital: Mapping[str, float] = CANDIDATE_CAPITAL,
    *,
    legs: Mapping[str, tuple[NotionalLeg, ...]] = CANDIDATE_LEGS,
) -> UnitMistake:
    """Mistake 1: type the published exposure table into a brokerage as capital weights.

    The exposure table adds to more than 100% because the portfolio is levered, so a
    screen that must add to 100% forces a pro-rata scale-down. The result double-counts
    the stack: its equity leg is already inside the table's US-equity line, and funding
    the wrapper again to obtain the trend line pays for that equity twice. The trend
    sleeve is the line that shrinks, because it is the one with no unlevered substitute.
    """
    intended = implied_notional(capital, legs=legs)
    total = sum(intended.values())
    scaled = {kind: value / total for kind, value in intended.items()}
    # The investor sizes each fund so its *capital* weight equals the scaled exposure,
    # keeping the ratios inside each kind. The trend line pins RSST.
    trend_share = scaled.get("trend", 0.0)
    typed: dict[str, float] = {}
    for name, weight in capital.items():
        kinds = {leg.kind for leg in legs[name]}
        if "trend" in kinds:
            typed[name] = trend_share
            continue
        kind = next(iter(kinds))
        within = weight / sum(
            other for other_name, other in capital.items()
            if {leg.kind for leg in legs[other_name]} == kinds
        )
        typed[name] = scaled.get(kind, 0.0) * within
    return _unit_mistake("notional table normalised to 100%", typed, intended, legs=legs)


def double_counted_capital(
    capital: Mapping[str, float] = CANDIDATE_CAPITAL,
    *,
    legs: Mapping[str, tuple[NotionalLeg, ...]] = CANDIDATE_LEGS,
) -> UnitMistake:
    """Mistake 2: treat the stack's trend leg as an allocation *beside* a full equity book.

    The investor keeps the full 65/35 equity split in unlevered funds and adds the stacked
    fund on top, because its trend leg is what they wanted from it. The plan needs 130% of
    capital, so the brokerage forces a pro-rata scale-down, and the result under-delivers
    trend while over-delivering equity — the opposite of the intent.
    """
    intended = implied_notional(capital, legs=legs)
    stacked = {
        name for name in capital if any(leg.kind == "trend" for leg in legs[name])
    }
    requested = {
        name: (weight if name in stacked else weight / (1.0 - sum(
            capital[other] for other in stacked
        )))
        for name, weight in capital.items()
    }
    total = sum(requested.values())
    typed = {name: weight / total for name, weight in requested.items()}
    return _unit_mistake("trend counted beside a full equity book", typed, intended, legs=legs)


# --------------------------------------------------------------------------------
# 2. Three accounts. The feasibility condition, exactly.
# --------------------------------------------------------------------------------


class Account(Enum):
    """Where a dollar sits. Sheltered accounts trade free; the taxable one does not."""

    TAXABLE = "taxable"
    TRADITIONAL = "traditional"
    ROTH = "roth"

    @property
    def sheltered(self) -> bool:
        return self is not Account.TAXABLE


#: A placement: fund -> account -> share of *total portfolio capital*. Shares over the
#: whole mapping sum to one.
Placement = Mapping[str, Mapping[Account, float]]


def placement_totals(placement: Placement) -> Mapping[str, float]:
    """Portfolio weight of each fund implied by a placement."""
    return {name: sum(by_account.values()) for name, by_account in placement.items()}


def account_totals(placement: Placement) -> Mapping[Account, float]:
    """Share of total capital in each account."""
    totals = {account: 0.0 for account in Account}
    for by_account in placement.values():
        for account, value in by_account.items():
            totals[account] += value
    return totals


def check_placement(placement: Placement, *, tolerance: float = 1e-9) -> None:
    """Raise unless a placement is a non-negative allocation of exactly one dollar."""
    total = 0.0
    for name, by_account in placement.items():
        for account, value in by_account.items():
            if value < 0.0:
                raise ValueError(f"{name} in {account.value} is negative: {value}")
            total += value
    if abs(total - 1.0) > tolerance:
        raise ValueError(f"placement allocates {total}, not 1.0")


@dataclass(frozen=True, slots=True)
class Headroom:
    """How far a portfolio is from needing a taxable sale to rebalance.

    ``per_fund[i] = target_i - taxable_i``, in shares of total wealth. Negative means the
    taxable account already holds more of that fund than the whole portfolio is supposed
    to, so no reallocation of the sheltered accounts can restore the target.
    """

    per_fund: Mapping[str, float]
    binding_fund: str
    minimum: float

    @property
    def feasible(self) -> bool:
        return self.minimum >= 0.0


def headroom(
    target: Mapping[str, float], taxable: Mapping[str, float]
) -> Headroom:
    """``min_i (target_i - taxable_i)``: the single number to watch.

    Non-negative means the portfolio target is reachable by sheltered trades alone. This
    is exact, not a heuristic: the reachable set is ``{taxable + s : s >= 0}`` with ``s``
    summing to the sheltered total, so the target is in it precisely when every taxable
    holding is at or below its portfolio target.
    """
    names = sorted(set(target) | set(taxable))
    per_fund = {name: target.get(name, 0.0) - taxable.get(name, 0.0) for name in names}
    binding = min(per_fund, key=lambda name: per_fund[name])
    return Headroom(per_fund=per_fund, binding_fund=binding, minimum=per_fund[binding])


def nearest_reachable(
    target: Mapping[str, float], taxable: Mapping[str, float]
) -> Mapping[str, float]:
    """The closest portfolio to ``target`` reachable without selling anything taxable.

    Euclidean projection of ``target`` onto ``{taxable + s : s >= 0, sum(s) = S}`` where
    ``S`` is the sheltered share. Equals ``target`` exactly when :func:`headroom` is
    non-negative, and otherwise reports what the investor can actually hold.
    """
    names = sorted(set(target) | set(taxable))
    fixed = np.array([taxable.get(name, 0.0) for name in names], dtype=np.float64)
    want = np.array([target.get(name, 0.0) for name in names], dtype=np.float64)
    sheltered = float(np.sum(want) - np.sum(fixed))
    if sheltered < -1e-12:
        raise ValueError(
            "the taxable account holds more than the whole portfolio; there is nothing "
            "to reallocate"
        )
    surplus = _project_to_simplex(want - fixed, total=max(sheltered, 0.0))
    return {name: float(fixed[i] + surplus[i]) for i, name in enumerate(names)}


def _project_to_simplex(desired: FloatArray, *, total: float) -> FloatArray:
    """``argmin ||s - desired||`` over ``s >= 0`` with ``sum(s) = total``.

    The standard sorted-threshold algorithm. ``s_i = max(desired_i + lam, 0)`` with ``lam``
    chosen to make the sum right; sorting locates ``lam`` in one pass.
    """
    if total <= 0.0:
        return np.zeros_like(desired)
    ordered = np.asarray(np.sort(desired)[::-1], dtype=np.float64)
    cumulative = np.cumsum(ordered)
    counts = np.arange(1, desired.size + 1, dtype=np.float64)
    thresholds = (cumulative - total) / counts
    admissible = ordered > thresholds
    last = int(np.max(np.nonzero(admissible)[0]))
    return np.asarray(np.maximum(desired - thresholds[last], 0.0), dtype=np.float64)


def relative_drift_to_infeasibility(
    *, taxable_share: float, sheltered_share: float, limit: float
) -> float:
    """Cumulative relative outperformance that exhausts a group's headroom.

    A group of funds (say, everything international) sits entirely in taxable at
    ``taxable_share`` of wealth; the sheltered accounts hold the rest at
    ``sheltered_share``. Returns the ratio ``(1+R_group)/(1+R_rest)`` at which the group's
    share of wealth reaches ``limit`` — the point past which no sheltered trade can bring
    the group back to target.

    Closed form: the share is ``a m / (a m + b)`` with ``a`` the taxable share, ``b`` the
    sheltered share and ``m`` the relative growth ratio, so ``m = limit b / (a (1 - limit))``.
    """
    if not 0.0 < limit < 1.0:
        raise ValueError(f"limit must lie strictly inside (0, 1), got {limit}")
    if taxable_share <= 0.0 or sheltered_share <= 0.0:
        raise ValueError("both shares must be positive")
    return limit * sheltered_share / (taxable_share * (1.0 - limit))


@dataclass(frozen=True, slots=True)
class FundTaxProfile:
    """What one fund's annual distribution is, and how much of it is taxed at which rate.

    Every field is filed, not assumed: ``box_1a_yield`` is the whole taxable distribution
    as a fraction of net assets (Box 1a grossed up for creditable foreign tax, plus Box
    2a); ``capital_gain_rate_fraction`` is the share taxed at the long-term rate; and
    ``creditable_foreign_tax_yield`` is the §853 pass-through a sheltered account forfeits,
    because §901 gives no credit against a tax the account does not pay.

    The single field that decides most of this study is ``capital_gain_rate_fraction``.
    Assuming it is 1.00 for an international fund — which this repository did until
    2026-08-22 — understates the tax by up to 17 percentage points of rate and reverses the
    fill order. Source: ``src/content/placement.ts``, ``investorHoldings``.
    """

    box_1a_yield: float
    capital_gain_rate_fraction: float
    creditable_foreign_tax_yield: float

    def __post_init__(self) -> None:
        if self.box_1a_yield < 0.0 or self.creditable_foreign_tax_yield < 0.0:
            raise ValueError("yields cannot be negative")
        if not 0.0 <= self.capital_gain_rate_fraction <= 1.0:
            raise ValueError(
                f"capital_gain_rate_fraction is a share, got {self.capital_gain_rate_fraction}"
            )

    def taxable_bp(self, *, capital_gains_rate: float, ordinary_rate: float) -> float:
        """Recurring tax on distributions, bp/yr per dollar held in a taxable account."""
        blended = (
            self.capital_gain_rate_fraction * capital_gains_rate
            + (1.0 - self.capital_gain_rate_fraction) * ordinary_rate
        )
        return 1e4 * self.box_1a_yield * blended

    @property
    def sheltered_bp(self) -> float:
        """Foreign tax credit forfeited by sheltering, bp/yr per dollar held."""
        return 1e4 * self.creditable_foreign_tax_yield


@dataclass(frozen=True, slots=True)
class PlacementCost:
    """Recurring drag per dollar of a fund, in each location, in basis points a year.

    Neither figure is the cost of a *realisation*, which :func:`forced_realisation_cost`
    prices separately and which this study's whole argument turns on keeping at zero.
    """

    taxable_bp: float
    sheltered_bp: float

    @property
    def priority_bp(self) -> float:
        """Shelter priority per dollar of capacity: what the shelter saves, net."""
        return self.taxable_bp - self.sheltered_bp


#: Filed tax profiles for the eight lines, from ``src/content/placement.ts``
#: (``investorHoldings``, ``as of 2026-08-22``), which carries the filing and date behind
#: every number. Two readings of the stacked wrapper are carried because the filing
#: supports both and they differ by an order of magnitude; see :data:`WRAPPER_READINGS`.
FUND_TAX_PROFILE: Final[Mapping[str, FundTaxProfile]] = {
    "RSST": FundTaxProfile(0.09273, 0.10504, 0.0),
    "IDMO": FundTaxProfile(0.044031, 0.2557, 0.001229),
    "AVES": FundTaxProfile(0.0391, 0.4448, 0.004598),
    "IEMG": FundTaxProfile(0.02545, 0.3482, 0.00245),
    "DFIV": FundTaxProfile(0.04033, 1.0, 0.003226),
    "VEA": FundTaxProfile(0.02387, 0.662741, 0.001448432),
    "AVLV": FundTaxProfile(0.0177, 1.0, 0.0),
    "VTI": FundTaxProfile(0.01067, 1.0, 0.0),
}

#: The wrapper's two readings of the same Tidal Trust II N-CSR. **Recognised** counts the
#: controlled-foreign-corporation income the fund included in investment company taxable
#: income whether or not it was paid out; **distributed** counts only what shareholders
#: were taxed on. The filing supports both, the difference is 328 bp/yr per dollar held in
#: taxable, and the review trigger is the wrapper's next December distribution.
WRAPPER_READINGS: Final[Mapping[str, FundTaxProfile]] = {
    "recognised": FundTaxProfile(0.09273, 0.10504, 0.0),
    "distributed": FundTaxProfile(0.01285, 0.8565, 0.0),
}

#: The three brackets the plan is reported across, as ``(qualified, ordinary)`` pairs.
#: A qualified rate implies an ordinary rate for the same taxpayer, and pairing a low
#: qualified rate with a top ordinary rate would be internally inconsistent — the error
#: ``src/content/placement.ts`` records under ``bondRowCaveat``. 40.8% is 37% plus the
#: §1411 surtax and 35.8% is 32% plus it; the 15% column sits below the surtax threshold,
#: so 24% carries no surtax. These pairs reproduce that page's published ``priorityBp``
#: for all eight funds at all three brackets, which the tests assert.
BRACKETS: Final[tuple[tuple[float, float], ...]] = (
    (0.238, 0.408),
    (0.188, 0.358),
    (0.150, 0.240),
)

ORDINARY_RATE: Final = 0.408
"""The ordinary rate paired with the default 23.8% qualified rate."""

QUALIFIED_RATES: Final[tuple[float, ...]] = tuple(pair[0] for pair in BRACKETS)


def ordinary_rate_for(qualified_rate: float) -> float:
    """The ordinary rate this study pairs with a qualified rate. Raises on an unknown one."""
    for qualified, ordinary in BRACKETS:
        if abs(qualified - qualified_rate) < 1e-12:
            return ordinary
    raise KeyError(
        f"no ordinary rate is paired with a qualified rate of {qualified_rate}; the "
        f"brackets carried here are {[pair[0] for pair in BRACKETS]}"
    )


def placement_costs_at(
    rate: float,
    *,
    ordinary_rate: float | None = None,
    wrapper_reading: str = "recognised",
    profiles: Mapping[str, FundTaxProfile] = FUND_TAX_PROFILE,
) -> Mapping[str, PlacementCost]:
    """The per-fund cost table at a stated qualified-dividend rate.

    The taxable column scales with the rate; the sheltered column does not, because
    forfeited foreign withholding is levied at source and does not depend on the US
    bracket. The two therefore cross at different rates for different funds, which is why
    the fill order is reported at three brackets rather than asserted once.
    """
    paired = ordinary_rate_for(rate) if ordinary_rate is None else ordinary_rate
    if not 0.0 <= rate < 1.0 or not 0.0 <= paired < 1.0:
        raise ValueError("rates must lie in [0, 1)")
    if wrapper_reading not in WRAPPER_READINGS:
        raise KeyError(f"wrapper reading must be one of {sorted(WRAPPER_READINGS)}")
    table = dict(profiles)
    table["RSST"] = WRAPPER_READINGS[wrapper_reading]
    return {
        name: PlacementCost(
            taxable_bp=profile.taxable_bp(
                capital_gains_rate=rate, ordinary_rate=paired
            ),
            sheltered_bp=profile.sheltered_bp,
        )
        for name, profile in table.items()
    }


PLACEMENT_COST_AT_23_8: Final[Mapping[str, PlacementCost]] = placement_costs_at(0.238)
"""The default cost table: 23.8% qualified, 40.8% ordinary, wrapper on the recognised basis."""


def placement_drag_bp(
    placement: Placement,
    costs: Mapping[str, PlacementCost] = PLACEMENT_COST_AT_23_8,
) -> float:
    """Recurring tax drag of a placement, basis points a year of total portfolio."""
    total = 0.0
    for name, by_account in placement.items():
        cost = costs[name]
        for account, value in by_account.items():
            total += value * (cost.sheltered_bp if account.sheltered else cost.taxable_bp)
    return total


def max_achievable_headroom(
    target: Mapping[str, float],
    *,
    taxable_share: float,
    barred: Sequence[str] = (),
    tolerance: float = 1e-12,
) -> float:
    """The largest ``min_i (target_i - taxable_i)`` any placement can achieve.

    The taxable account must hold ``taxable_share`` of wealth in *something*, and every
    dollar it holds of a fund eats that fund's headroom. The bound solves
    ``sum_i max(target_i - h, 0) = taxable_share`` over the lines not ``barred`` from the
    taxable account. It falls as the portfolio is cut into more and smaller lines — a line
    whose target is below ``h`` can hold nothing taxable at all — and it falls again for
    every line barred outright, which is the price of barring one.
    """
    if not 0.0 < taxable_share < 1.0:
        raise ValueError(f"taxable_share must lie in (0, 1), got {taxable_share}")
    allowed = {name: want for name, want in target.items() if name not in set(barred)}
    if sum(allowed.values()) < taxable_share - 1e-12:
        raise ValueError(
            "the lines allowed in a taxable account cannot fill it; either the bar or the "
            "account share has to give"
        )
    low, high = 0.0, max(allowed.values())
    while high - low > tolerance:
        middle = 0.5 * (low + high)
        capacity = sum(max(want - middle, 0.0) for want in allowed.values())
        if capacity >= taxable_share:
            low = middle
        else:
            high = middle
    return low


def min_drag_placement(
    target: Mapping[str, float],
    *,
    taxable_share: float,
    min_headroom: float,
    costs: Mapping[str, PlacementCost] = PLACEMENT_COST_AT_23_8,
    sheltered_split: Mapping[Account, float] | None = None,
    taxable_capacity: Mapping[str, float] | None = None,
) -> Placement:
    """The cheapest placement that keeps at least ``min_headroom`` on every line.

    Total drag is ``sum_i target_i * sheltered_i + sum_i taxable_i * priority_i``, and the
    first term does not depend on the placement, so **the shelter priority ranking alone
    decides the optimum**: fill the taxable account from the lowest priority upward,
    subject to a box constraint of ``target_i - min_headroom`` per line. That is a
    continuous knapsack, so the greedy fill is exact rather than a heuristic — and at
    ``min_headroom = 0`` it reproduces the pure tax-priority plan exactly, which is why
    that plan and this frontier are the same optimisation at two constraint levels.

    ``sheltered_split`` divides the sheltered remainder between the traditional and Roth
    accounts; it defaults to an even split, which affects after-tax value but not
    rebalancing feasibility, since both trade free. ``taxable_capacity`` caps individual
    lines below the headroom constraint; a cap of zero bars a line outright.
    """
    caps = dict(taxable_capacity or {})
    barred = [name for name, cap in caps.items() if cap <= 0.0]
    ceiling = max_achievable_headroom(target, taxable_share=taxable_share, barred=barred)
    if min_headroom > ceiling + 1e-9:
        raise ValueError(
            f"no placement reaches {min_headroom} of headroom with a taxable share of "
            f"{taxable_share}; the ceiling is {ceiling}"
        )
    split = sheltered_split or {Account.TRADITIONAL: 0.5, Account.ROTH: 0.5}
    remaining = taxable_share
    taxable: dict[str, float] = {}
    for name in sorted(target, key=lambda k: (costs[k].priority_bp, k)):
        capacity = min(max(target[name] - min_headroom, 0.0), caps.get(name, math.inf))
        take = min(capacity, remaining)
        taxable[name] = take
        remaining -= take
    if remaining > 1e-9:
        raise ValueError("the taxable account cannot be filled under this constraint")
    placement: dict[str, dict[Account, float]] = {}
    for name, want in target.items():
        rest = want - taxable[name]
        entry = {Account.TAXABLE: taxable[name]}
        for account, share in split.items():
            entry[account] = rest * share
        placement[name] = entry
    return placement


@dataclass(frozen=True, slots=True)
class ForcedTrade:
    """The cost of a rebalancing trade that a sheltered account could not absorb."""

    traded: float
    gain_realised: float
    tax: float
    friction: float

    @property
    def total(self) -> float:
        return self.tax + self.friction

    @property
    def tax_to_friction(self) -> float:
        """How many times larger the tax bill is than the spread. Usually three digits."""
        return math.inf if self.friction == 0.0 else self.tax / self.friction


def forced_realisation_cost(
    *, traded: float, gain_fraction: float, tax_rate: float, spread_bp: float
) -> ForcedTrade:
    """Price a taxable sale made for rebalancing: realised gain plus the spread.

    ``gain_fraction`` is the unrealised gain as a share of the position's *value*, which
    is the number a brokerage lot screen reports, not gain over basis. Both terms are
    charged inside the rule that decides to trade, never as a haircut afterwards.
    """
    if not 0.0 <= gain_fraction <= 1.0:
        raise ValueError(f"gain_fraction is a share of value, got {gain_fraction}")
    if not 0.0 <= tax_rate < 1.0:
        raise ValueError(f"tax_rate must lie in [0, 1), got {tax_rate}")
    if traded < 0.0 or spread_bp < 0.0:
        raise ValueError("traded notional and spread cannot be negative")
    gain = traded * gain_fraction
    return ForcedTrade(
        traded=traded,
        gain_realised=gain,
        tax=gain * tax_rate,
        friction=ProportionalCostModel(cost_bp=spread_bp).cost([traded], traded),
    )


def gain_fraction_after(*, years: float, growth_rate: float) -> float:
    """Unrealised gain as a share of value after ``years`` compounding at ``growth_rate``.

    ``1 - (1 + g)**-y``. A lot held ten years at 7% is 49% gain by value, which is why the
    tax term in :func:`forced_realisation_cost` dominates so quickly.
    """
    if years < 0.0:
        raise ValueError("years cannot be negative")
    if growth_rate <= -1.0:
        raise ValueError("growth_rate must exceed -100%")
    return float(1.0 - (1.0 + growth_rate) ** (-years))


def after_tax_account_shares(
    *,
    balances: Mapping[Account, float],
    ordinary_rate: float,
    capital_gains_rate: float,
    taxable_gain_fraction: float,
) -> Mapping[Account, float]:
    """Account shares restated in after-tax dollars, which is what the investor owns.

    A traditional balance carries an embedded income-tax liability and a taxable balance
    an embedded capital-gains one; a Roth balance carries neither. Restating matters here
    because the *taxable* share is the one that constrains rebalancing, and it is larger
    after tax than before.
    """
    if not 0.0 <= ordinary_rate < 1.0 or not 0.0 <= capital_gains_rate < 1.0:
        raise ValueError("rates must lie in [0, 1)")
    if not 0.0 <= taxable_gain_fraction <= 1.0:
        raise ValueError("taxable_gain_fraction is a share of value")
    net = {
        Account.ROTH: balances.get(Account.ROTH, 0.0),
        Account.TRADITIONAL: balances.get(Account.TRADITIONAL, 0.0) * (1.0 - ordinary_rate),
        Account.TAXABLE: balances.get(Account.TAXABLE, 0.0)
        * (1.0 - capital_gains_rate * taxable_gain_fraction),
    }
    total = sum(net.values())
    if total <= 0.0:
        raise ValueError("after-tax wealth is not positive")
    return {account: value / total for account, value in net.items()}


# --------------------------------------------------------------------------------
# 3. The executable rule. Costs and tax are inside it.
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RebalanceRule:
    """A complete, executable operating policy.

    ``review_months`` is how often the investor looks. ``relative_band`` and
    ``absolute_band`` are triggers checked at a review; ``None`` on both means rebalance
    at every review (a calendar policy) and a band of ``math.inf`` means never
    (buy-and-hold, or contribution-directed when ``direct_contributions`` is set).

    ``allow_taxable_sales`` is the switch this module exists to interrogate. With it off,
    the rule may only reallocate sheltered accounts and steer new money, so it can never
    realise a gain for rebalancing; with it on, it closes the remaining gap by selling in
    taxable and pays the bill inside the simulation.
    """

    label: str
    review_months: int
    relative_band: float | None = None
    absolute_band: float | None = None
    allow_taxable_sales: bool = False
    direct_contributions: bool = True
    #: Smallest trade worth placing, as a share of portfolio value. A real investor does
    #: not send a three-dollar order, and without a floor a calendar rule charges a spread
    #: on floating-point residue every time it reviews an already-correct portfolio.
    minimum_trade: float = 1e-4

    def __post_init__(self) -> None:
        if self.review_months < 1:
            raise ValueError(f"review_months must be at least 1, got {self.review_months}")
        for band in (self.relative_band, self.absolute_band):
            if band is not None and band <= 0.0:
                raise ValueError("bands must be positive")
        if self.minimum_trade < 0.0:
            raise ValueError("minimum_trade cannot be negative")

    def triggered(
        self, weights: Mapping[str, float], target: Mapping[str, float]
    ) -> bool:
        if self.relative_band is None and self.absolute_band is None:
            return True
        for name, want in target.items():
            drift = weights.get(name, 0.0) - want
            if self.absolute_band is not None and abs(drift) > self.absolute_band:
                return True
            if (
                self.relative_band is not None
                and want > 0.0
                and abs(drift / want) > self.relative_band
            ):
                return True
        return False


@dataclass(frozen=True, slots=True)
class OperationsResult:
    """What running one policy for the whole sample actually cost and achieved."""

    label: str
    months: int
    mean_absolute_deviation: float
    max_absolute_deviation: float
    mean_trend_notional_error: float
    max_trend_notional_error: float
    rebalance_events: int
    trades: int
    turnover_per_year: float
    friction_cost_per_year: float
    tax_paid_per_year: float
    gain_realised_per_year: float
    months_infeasible: int
    worst_headroom: float
    growth_per_year: float
    terminal_wealth: float
    monthly_returns: tuple[float, ...]

    @property
    def trades_per_year(self) -> float:
        return self.trades * MONTHS_PER_YEAR / self.months

    @property
    def decisions_per_year(self) -> float:
        """Reviews per year, whether or not they end in a trade. The real burden."""
        return self.rebalance_events * MONTHS_PER_YEAR / self.months


@dataclass(frozen=True, slots=True)
class TaxRegime:
    """Stated rates and lot behaviour. Arguments, because tax law is dated and local."""

    long_term_rate: float
    spread_bp: float
    #: Distributions are assumed reinvested inside each fund and are not modelled as a
    #: separate realisation; the recurring drag they cause is priced in
    #: ``docs/research/structural-and-tax-edges.md`` and is common to every policy here,
    #: so it cancels in every paired comparison this module makes.
    as_of: str = AS_OF


def simulate_operations(
    *,
    returns: Mapping[str, Series],
    placement: Placement,
    rule: RebalanceRule,
    regime: TaxRegime,
    contribution_per_year: float = 0.0,
    contribution_to_taxable: float = 0.0,
    taxable_eligible: Sequence[str] | None = None,
    taxable_contributions_by_headroom: bool = True,
    initial_gain_fraction: float = 0.0,
) -> OperationsResult:
    """Run one operating policy over aligned monthly total returns, three accounts, net.

    Order of operations inside a month, declared rather than inferred:

    1. the monthly contribution arrives and is split between sheltered and taxable;
    2. at a review month, the rule decides whether to act;
    3. if it acts, new money is directed at the most underweight lines first, then the
       sheltered accounts are reallocated to the point nearest the target, then — only if
       ``allow_taxable_sales`` — taxable lots are sold to close what remains;
    4. spreads are charged on traded notional and capital-gains tax on realised gain,
       both paid out of the portfolio;
    5. the month's returns are applied.

    ``contribution_per_year`` is a fraction of *initial* wealth a year, flat in nominal
    terms, matching the convention frozen in ``exp_003_rebalancing.yaml`` so the two are
    comparable. Basis in the taxable account is tracked as an average cost per fund, which
    understates what specific-identification would achieve and is stated as a limitation
    rather than corrected.

    ``initial_gain_fraction`` is the unrealised gain already embedded in the taxable
    account on day one, as a share of its value. Zero is an investor starting fresh and is
    the *optimistic* case: every figure that involves a realisation gets worse as it rises,
    and an investor who already holds these funds does not start at zero.

    ``taxable_contributions_by_headroom`` is the procedural rule this module argues for.
    Sending taxable money to whichever eligible line is most *underweight* is the obvious
    thing to do and it is wrong: it fills the one account that cannot later be sold, so it
    spends headroom to buy exposure that a sheltered trade could have bought for nothing.
    Sending it to whichever line has the most *headroom* buys the same exposure and cannot
    create an infeasibility. Setting this to ``False`` reproduces the obvious rule so the
    difference can be measured.
    """
    check_placement(placement)
    names = sorted(placement)
    unknown = sorted(set(names) - set(returns))
    if unknown:
        raise KeyError(f"no return series for {unknown}")
    months = min(len(returns[name]) for name in names)
    if months < MONTHS_PER_YEAR:
        raise ValueError(f"need at least a year of returns, got {months}")
    if not 0.0 <= contribution_to_taxable <= 1.0:
        raise ValueError("contribution_to_taxable is a share")

    target = dict(placement_totals(placement))
    eligible = set(taxable_eligible) if taxable_eligible is not None else set(names)
    matrix = np.array([returns[name][:months] for name in names], dtype=np.float64).T

    taxable = np.array([placement[name].get(Account.TAXABLE, 0.0) for name in names])
    sheltered = np.array(
        [
            placement[name].get(Account.TRADITIONAL, 0.0)
            + placement[name].get(Account.ROTH, 0.0)
            for name in names
        ]
    )
    if not 0.0 <= initial_gain_fraction < 1.0:
        raise ValueError(
            f"initial_gain_fraction is a share of value, got {initial_gain_fraction}"
        )
    basis = taxable * (1.0 - initial_gain_fraction)
    want = np.array([target[name] for name in names], dtype=np.float64)
    monthly_contribution = contribution_per_year / MONTHS_PER_YEAR

    deviations: list[float] = []
    trend_errors: list[float] = []
    headrooms: list[float] = []
    monthly_returns: list[float] = []
    eligible_mask = np.array([name in eligible for name in names])
    events = 0
    trades = 0
    turnover = 0.0
    friction = 0.0
    tax = 0.0
    realised = 0.0
    infeasible = 0
    target_trend = _trend_notional(dict(zip(names, want, strict=True)))

    for step in range(months):
        if monthly_contribution > 0.0:
            to_taxable = monthly_contribution * contribution_to_taxable
            to_sheltered = monthly_contribution - to_taxable
            wealth = float(np.sum(taxable) + np.sum(sheltered))
            desired = want * (wealth + monthly_contribution)
            if rule.direct_contributions:
                sheltered += to_sheltered * _weighted_split(
                    np.maximum(desired - (taxable + sheltered), 0.0), mask=None
                )
                room = (
                    np.maximum(desired - taxable, 0.0)
                    if taxable_contributions_by_headroom
                    else np.maximum(desired - (taxable + sheltered), 0.0)
                )
                bought = to_taxable * _weighted_split(room, mask=eligible_mask)
            else:
                share = (taxable + sheltered) / wealth if wealth > 0.0 else want
                sheltered += to_sheltered * share
                bought = to_taxable * share
            taxable += bought
            basis += bought

        wealth = float(np.sum(taxable) + np.sum(sheltered))
        weights = (taxable + sheltered) / wealth
        room_now = float(np.min(want - taxable / wealth))
        headrooms.append(room_now)
        if room_now < 0.0:
            infeasible += 1

        opening = wealth
        review = step % rule.review_months == 0
        if review and step > 0 and rule.triggered(
            dict(zip(names, weights, strict=True)), target
        ):
            events += 1
            reachable = _project_to_simplex(
                want * wealth - taxable, total=float(np.sum(sheltered))
            )
            moved = np.abs(reachable - sheltered)
            traded_notional = float(np.sum(moved))
            if traded_notional > rule.minimum_trade * wealth:
                trades += int(np.sum(moved > rule.minimum_trade * wealth))
                # Turnover is the one-sided convention; the spread is paid on both legs
                # of a switch, which is the basis ``exp_003_rebalancing.yaml`` charges.
                turnover += 0.5 * traded_notional / wealth
                cost = ProportionalCostModel(cost_bp=regime.spread_bp).cost(
                    [traded_notional], wealth
                )
                friction += cost / wealth
                sheltered = reachable * (1.0 - cost / max(float(np.sum(reachable)), 1e-18))

            if rule.allow_taxable_sales:
                held = taxable + sheltered
                excess = np.maximum(held - want * float(np.sum(held)), 0.0)
                sell = np.minimum(excess, taxable)
                sold = float(np.sum(sell))
                if sold > rule.minimum_trade * wealth:
                    trades += int(np.sum(sell > rule.minimum_trade * wealth))
                    gain_share = np.clip(
                        np.where(taxable > 0.0, 1.0 - basis / np.maximum(taxable, 1e-18), 0.0),
                        0.0,
                        1.0,
                    )
                    gain = float(np.sum(sell * gain_share))
                    bill = gain * regime.long_term_rate
                    cost = ProportionalCostModel(cost_bp=regime.spread_bp).cost(
                        [sold], wealth
                    )
                    basis -= sell * (1.0 - gain_share)
                    taxable -= sell
                    proceeds = sold - bill - cost
                    turnover += sold / wealth
                    friction += cost / wealth
                    tax += bill / wealth
                    realised += gain / wealth
                    total = float(np.sum(taxable) + np.sum(sheltered)) + proceeds
                    deficit = np.maximum(want * total - (taxable + sheltered), 0.0)
                    total_deficit = float(np.sum(deficit))
                    sheltered += proceeds * (
                        deficit / total_deficit if total_deficit > 0.0 else want
                    )

        wealth = float(np.sum(taxable) + np.sum(sheltered))
        weights = (taxable + sheltered) / wealth
        deviations.append(float(np.mean(np.abs(weights - want))))
        trend_errors.append(
            abs(_trend_notional(dict(zip(names, weights, strict=True))) - target_trend)
        )

        growth = 1.0 + matrix[step]
        taxable = taxable * growth
        sheltered = sheltered * growth
        closing = float(np.sum(taxable) + np.sum(sheltered))
        monthly_returns.append(closing / opening - 1.0)

    years = months / MONTHS_PER_YEAR
    path = np.asarray(monthly_returns, dtype=np.float64)
    return OperationsResult(
        label=rule.label,
        months=months,
        mean_absolute_deviation=float(np.mean(deviations)),
        max_absolute_deviation=float(np.max(deviations)),
        mean_trend_notional_error=float(np.mean(trend_errors)),
        max_trend_notional_error=float(np.max(trend_errors)),
        rebalance_events=events,
        trades=trades,
        turnover_per_year=turnover / years,
        friction_cost_per_year=friction / years,
        tax_paid_per_year=tax / years,
        gain_realised_per_year=realised / years,
        months_infeasible=infeasible,
        worst_headroom=float(np.min(headrooms)),
        growth_per_year=float(np.sum(np.log1p(path))) / years,
        terminal_wealth=float(np.sum(taxable) + np.sum(sheltered)),
        monthly_returns=tuple(monthly_returns),
    )


def _trend_notional(weights: Mapping[str, float]) -> float:
    """Trend notional per dollar of capital implied by a set of capital weights."""
    return sum(
        weight * sum(
            leg.per_dollar_of_capital
            for leg in CANDIDATE_LEGS.get(name, ())
            if leg.kind == "trend"
        )
        for name, weight in weights.items()
    )


def _weighted_split(
    appetite: FloatArray, *, mask: NDArray[np.bool_] | None
) -> FloatArray:
    """Fractions of a contribution, split across eligible lines in proportion to appetite.

    ``appetite`` is either the deficit against target (for sheltered money, which can be
    undone later) or the remaining headroom (for taxable money, which cannot).
    """
    room = np.maximum(appetite, 0.0)
    if mask is not None:
        room = np.where(mask, room, 0.0)
    total = float(np.sum(room))
    if total > 0.0:
        return np.asarray(room / total, dtype=np.float64)
    fallback = np.where(mask, 1.0, 0.0) if mask is not None else np.ones_like(room)
    return np.asarray(fallback / max(float(np.sum(fallback)), 1e-18), dtype=np.float64)


# --------------------------------------------------------------------------------
# 4. Complexity: what a consolidation costs, measured rather than asserted.
# --------------------------------------------------------------------------------


def tracking_error(
    a: Series, b: Series, *, periods_per_year: int = MONTHS_PER_YEAR
) -> float:
    """Annualised standard deviation of the difference between two return series."""
    left = np.asarray(a, dtype=np.float64)
    right = np.asarray(b, dtype=np.float64)
    if left.shape != right.shape:
        raise ValueError("series must be the same length")
    if left.size < 2:
        raise ValueError("need at least two observations")
    return float(np.std(left - right, ddof=1)) * math.sqrt(periods_per_year)


def portfolio_returns(
    returns: Mapping[str, Series], weights: Mapping[str, float]
) -> FloatArray:
    """Monthly returns of a constant-weight portfolio. Weights are capital shares."""
    names = sorted(weights)
    months = min(len(returns[name]) for name in names)
    matrix = np.array([returns[name][:months] for name in names], dtype=np.float64)
    vector = np.array([weights[name] for name in names], dtype=np.float64)
    return np.asarray(vector @ matrix, dtype=np.float64)


# --------------------------------------------------------------------------------
# 5. Holdability: the worst stretch, and how long it lasted.
# --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RelativeStretch:
    """The worst run of underperformance against a benchmark, and its length."""

    depth: float
    months: int
    start: str
    trough: str
    recovered: str | None

    @property
    def years(self) -> float:
        return self.months / MONTHS_PER_YEAR


def worst_relative_stretch(
    candidate: Series, benchmark: Series, periods: Sequence[str]
) -> RelativeStretch:
    """Deepest drawdown of the candidate's wealth *ratio* to the benchmark.

    This is the quantity an investor actually experiences when deciding whether to
    abandon a construction: not the portfolio's own drawdown, but how far behind a
    familiar comparator it has fallen and for how long it stayed there.
    """
    left = np.asarray(candidate, dtype=np.float64)
    right = np.asarray(benchmark, dtype=np.float64)
    if left.shape != right.shape or left.size != len(periods):
        raise ValueError("candidate, benchmark and periods must be the same length")
    ratio = np.cumprod((1.0 + left) / (1.0 + right))
    peak = np.maximum.accumulate(ratio)
    drawdown = ratio / peak - 1.0
    trough = int(np.argmin(drawdown))
    # The *last* month at which the peak was standing, so the reported window is the
    # decline rather than the run-up that preceded it.
    start = int(np.max(np.nonzero(ratio[: trough + 1] >= peak[trough])[0]))
    after = np.nonzero(ratio[trough:] >= ratio[start])[0]
    recovered = int(trough + after[0]) if after.size > 0 else None
    end = recovered if recovered is not None else left.size - 1
    return RelativeStretch(
        depth=float(drawdown[trough]),
        months=end - start,
        start=periods[start],
        trough=periods[trough],
        recovered=periods[recovered] if recovered is not None else None,
    )


def minimum_detectable_effect(
    differences: Series, *, periods_per_year: int = MONTHS_PER_YEAR
) -> float:
    """Annualised effect an 80%-power two-sided 5% test could just resolve here.

    ``2.80 * se`` on the mean of ``differences``, annualised. Reported beside every
    return column in this module because the operating question is decided by exposure
    control and tax, and the return column is almost always inside this bound.
    """
    values = np.asarray(differences, dtype=np.float64)
    if values.size < 2:
        raise ValueError("need at least two observations")
    error = float(np.std(values, ddof=1) / math.sqrt(values.size))
    return 2.802 * error * periods_per_year
