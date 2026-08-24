"""Regenerates the operating tables in ``docs/research/rebalancing-policy.md``.

Reads only from the local raw cache — every call goes through ``RawCache.require``, which
raises rather than reaching the network — and builds *index proxies* for the eight funds
of the stacked candidate. The proxies are declared in :data:`PROXIES` and are not funds:
they carry no fund fee except RSST's, no bid-offer, no tracking error and no survivorship
correction. That is acceptable here and would not be acceptable for a return claim, which
is why this module makes none: what it measures is exposure control, trade counts,
realised gain and tax, all of which are properties of the *rule* rather than of the
proxy's mean.

Run with ``uv run python -m portfolio_edge.studies._rebalancing_operations_tables``.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Final

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.data import aqr, french
from portfolio_edge.data.cache import RawCache, default_cache_root
from portfolio_edge.data.table import ParsedTable
from portfolio_edge.studies.rebalancing_operations import (
    CANDIDATE_CAPITAL,
    MONTHS_PER_YEAR,
    QUALIFIED_RATES,
    Account,
    OperationsResult,
    Placement,
    RebalanceRule,
    TaxRegime,
    account_totals,
    after_tax_account_shares,
    capital_for_notional,
    check_placement,
    double_counted_capital,
    forced_realisation_cost,
    gain_fraction_after,
    gross_notional,
    headroom,
    implied_notional,
    max_achievable_headroom,
    min_drag_placement,
    minimum_detectable_effect,
    normalised_notional_capital,
    ordinary_rate_for,
    placement_costs_at,
    placement_drag_bp,
    placement_totals,
    portfolio_returns,
    relative_drift_to_infeasibility,
    simulate_operations,
    tracking_error,
    worst_relative_stretch,
)

BP: Final = 1e4

RSST_FEE: Final = 0.0099
"""RSST's stated all-in expense ratio, ``src/content/shelf.ts``."""

IDMO_MOMENTUM_LOADING: Final = 0.35
"""Assumed WML loading of a long-only developed momentum fund. Not measured here.

A long-only index cannot short losers, so its loading on a long-short factor is well
below one. 0.35 is a stated assumption; the line is 5% of the portfolio and every
conclusion below was checked at 0.20 and 0.50 without changing a sign.
"""

SPREAD_BP: Final = 2.0
"""One-way ETF spread, the optimistic column of ``exp_003_rebalancing.yaml``."""

SPREAD_BP_PESSIMISTIC: Final = 8.0
"""The pessimistic column of the same specification."""

LONG_TERM_RATE: Final = 0.238
"""Top federal long-term capital gains rate plus net investment income tax."""

CONTRIBUTION_PER_YEAR: Final = 0.05
"""5% of initial wealth a year, flat nominal — the convention frozen in Experiment 003."""


# --------------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------------


def _cache() -> RawCache:
    return RawCache(default_cache_root())


def _french(dataset_id: str, table_id: str) -> ParsedTable:
    cache = _cache()
    dataset = french.get_dataset(dataset_id)
    return french.parse(cache, cache.require(dataset.url), dataset=dataset).table(table_id)


def _aqr(dataset_id: str) -> ParsedTable:
    cache = _cache()
    dataset = aqr.get_dataset(dataset_id)
    return aqr.parse(cache, cache.require(dataset.url), dataset=dataset).table


def _column(table: ParsedTable, name: str) -> dict[str, float]:
    return {
        period[:7]: float(value)
        for period, value in zip(table.periods, table.column(name), strict=True)
        if value is not None
    }


PROXIES: Final[Mapping[str, str]] = {
    "RSST": "US market total return at 1.072x plus AQR TSMOM at 1.0x, less 99 bp of fee",
    "VTI": "French US market total return (Mkt-RF + RF)",
    "AVLV": "French US large value, 6 portfolios 2x3 value-weighted, BIG HiBM",
    "DFIV": "French developed ex-US large value, BIG HiBM",
    "VEA": "French developed ex-US market total return",
    "IDMO": f"French developed ex-US market plus {IDMO_MOMENTUM_LOADING:.2f} x WML",
    "IEMG": "French emerging market total return",
    "AVES": "French emerging large value, BIG HiBM",
}

VALUE_TABLE: Final = "average_value_weighted_returns_monthly"


TREND_BASES: Final[Mapping[str, float | None]] = {
    "vendor gross": None,
    "live-fund mean +2.84%/yr": 0.0284,
    "zero excess over cash": 0.0,
}
"""How the trend leg's *level* is set. Its shape is AQR's series in every case.

The AQR workbook states no fee, transaction-cost, slippage or financing basis anywhere,
so ``TSMOM`` is gross of all of them by omission and its level is not investable. The
second row shifts the series' mean to the +2.84%/yr an equal-weight index of 46 live
managed-futures funds earned net of their own fees over the 78 months on which they can be
compared (``docs/research/live-managed-futures.md``), preserving every higher moment.
The third sets the trend leg's excess over cash to zero, which isolates
what the *volatility and correlation* of the sleeve do to drift from what its assumed
premium does. The mean shift uses the whole sample's mean and is therefore look-ahead in
level; it is used to bound drift, never to support a return claim.
"""


def load_proxies(*, trend_mean_per_year: float | None = None) -> tuple[
    dict[str, list[float]], list[str]
]:
    """Monthly total returns for the eight lines, plus the aligned period labels.

    ``trend_mean_per_year`` replaces the trend leg's sample mean, leaving every other
    moment alone. ``None`` keeps AQR's own gross level. See :data:`TREND_BASES`.
    """
    us = _french("french_us_ff5", "monthly")
    us_value = _french("french_us_6_portfolios_2x3", VALUE_TABLE)
    developed = _french("french_developed_ex_us_ff5", "monthly")
    developed_value = _french("french_developed_ex_us_6_portfolios_2x3", VALUE_TABLE)
    developed_momentum = _french("french_developed_ex_us_momentum", "monthly")
    emerging = _french("french_emerging_ff5", "monthly")
    emerging_value = _french("french_emerging_6_portfolios_2x3", VALUE_TABLE)
    trend = _aqr("aqr_tsmom_factors")

    us_excess = _column(us, "Mkt-RF")
    cash = _column(us, "RF")
    developed_excess = _column(developed, "Mkt-RF")
    emerging_excess = _column(emerging, "Mkt-RF")
    wml = _column(developed_momentum, "WML")
    tsmom = _column(trend, "TSMOM")

    sources = [
        us_excess, cash, developed_excess, emerging_excess, wml, tsmom,
        _column(us_value, "BIG HiBM"),
        _column(developed_value, "BIG HiBM"),
        _column(emerging_value, "BIG HiBM"),
    ]
    periods = sorted(set.intersection(*(set(source) for source in sources)))
    fee = RSST_FEE / MONTHS_PER_YEAR
    shift = 0.0
    if trend_mean_per_year is not None:
        realised = float(np.mean([tsmom[period] for period in periods]))
        shift = realised - trend_mean_per_year / MONTHS_PER_YEAR

    us_value_big = _column(us_value, "BIG HiBM")
    developed_value_big = _column(developed_value, "BIG HiBM")
    emerging_value_big = _column(emerging_value, "BIG HiBM")

    returns: dict[str, list[float]] = {name: [] for name in CANDIDATE_CAPITAL}
    for period in periods:
        rf = cash[period]
        trend_leg = tsmom[period] - shift
        returns["RSST"].append(rf + 1.072 * us_excess[period] + trend_leg - fee)
        returns["VTI"].append(rf + us_excess[period])
        returns["AVLV"].append(us_value_big[period])
        returns["DFIV"].append(developed_value_big[period])
        returns["VEA"].append(rf + developed_excess[period])
        returns["IDMO"].append(
            rf + developed_excess[period] + IDMO_MOMENTUM_LOADING * wml[period]
        )
        returns["IEMG"].append(rf + emerging_excess[period])
        returns["AVES"].append(emerging_value_big[period])
    return returns, periods


# --------------------------------------------------------------------------------
# Placements
# --------------------------------------------------------------------------------

TAXABLE_SHARE: Final = 1.0 / 3.0
SHELTERED_SPLIT: Final[Mapping[Account, float]] = {
    Account.TRADITIONAL: 0.5,
    Account.ROTH: 0.5,
}


def placement_plan() -> Placement:
    """The plan `src/content/placement.ts` publishes, as of 2026-08-22.

    Traditional takes the wrapper entire plus 3.33 pp of IDMO; Roth takes the rest of the
    international sleeve plus 1.67 pp of AVLV; taxable takes VTI entire plus the remaining
    13.33 pp of AVLV. It is the pure tax-priority optimum, and therefore exactly the
    ``min_headroom = 0`` corner of :func:`min_drag_placement` — the two analyses are the
    same knapsack at two constraint levels, which is why they can be compared directly.
    """
    return {
        "RSST": {Account.TRADITIONAL: 0.30, Account.ROTH: 0.0, Account.TAXABLE: 0.0},
        "IDMO": {Account.TRADITIONAL: 1.0 / 30.0, Account.ROTH: 0.05 - 1.0 / 30.0,
                 Account.TAXABLE: 0.0},
        "AVES": {Account.ROTH: 0.05, Account.TRADITIONAL: 0.0, Account.TAXABLE: 0.0},
        "IEMG": {Account.ROTH: 0.05, Account.TRADITIONAL: 0.0, Account.TAXABLE: 0.0},
        "DFIV": {Account.ROTH: 0.10, Account.TRADITIONAL: 0.0, Account.TAXABLE: 0.0},
        "VEA": {Account.ROTH: 0.10, Account.TRADITIONAL: 0.0, Account.TAXABLE: 0.0},
        "AVLV": {Account.ROTH: 1.0 / 60.0, Account.TAXABLE: 0.15 - 1.0 / 60.0,
                 Account.TRADITIONAL: 0.0},
        "VTI": {Account.TAXABLE: 0.20, Account.TRADITIONAL: 0.0, Account.ROTH: 0.0},
    }


def headroom_placement(min_headroom: float) -> Placement:
    """The cheapest placement carrying ``min_headroom`` on every line, wrapper barred.

    The bar on the wrapper is carried at every level because both this study and the
    placement page reached it independently, and because it is the line whose taxable
    treatment is least settled.
    """
    return min_drag_placement(
        dict(CANDIDATE_CAPITAL), taxable_share=TAXABLE_SHARE,
        min_headroom=min_headroom, sheltered_split=SHELTERED_SPLIT,
        taxable_capacity={"RSST": 0.0},
    )


def one_point_of_vti(taxable_vti: float = 0.19) -> Placement:
    """The published plan with one point of VTI moved out of the taxable account.

    The taxable account still holds only the two lowest-priority lines, so the plan's tax
    logic is untouched; AVLV absorbs the freed capacity. The single purpose is to lift
    VTI's headroom off zero, and the taxable vector that maximises the *minimum* headroom
    across the two lines is VTI 19.17 / AVLV 14.17 at 0.83 pp. 19.00 / 14.33 is the round
    version and is used here because an instruction an investor will actually follow beats
    a third decimal place.
    """
    taxable = {"VTI": taxable_vti, "AVLV": TAXABLE_SHARE - taxable_vti}
    return {
        name: {
            Account.TAXABLE: taxable.get(name, 0.0),
            **{
                account: (want - taxable.get(name, 0.0)) * share
                for account, share in SHELTERED_SPLIT.items()
            },
        }
        for name, want in CANDIDATE_CAPITAL.items()
    }


def taxable_vector(placement: Placement) -> dict[str, float]:
    return {name: by.get(Account.TAXABLE, 0.0) for name, by in placement.items()}


def rules() -> tuple[RebalanceRule, ...]:
    return (
        RebalanceRule("Buy and hold", review_months=1, absolute_band=math.inf,
                      direct_contributions=False),
        RebalanceRule("Contribution-directed only", review_months=1,
                      absolute_band=math.inf),
        RebalanceRule("Annual calendar, sheltered only", review_months=12),
        RebalanceRule("Quarterly calendar, sheltered only", review_months=3),
        RebalanceRule("Relative band 25%, sheltered only", review_months=1,
                      relative_band=0.25),
        RebalanceRule("Absolute band 5pp, sheltered only", review_months=1,
                      absolute_band=0.05),
        RebalanceRule("Annual review, act on a 25% relative band", review_months=12,
                      relative_band=0.25),
        RebalanceRule("Annual review, act on a 5pp absolute band", review_months=12,
                      absolute_band=0.05),
        RebalanceRule("Annual calendar, taxable sales allowed", review_months=12,
                      allow_taxable_sales=True),
    )


# --------------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------------


def _pp(value: float) -> str:
    return f"{100.0 * value:.2f}"


PRIMARY_TREND_BASIS: Final = "live-fund mean +2.84%/yr"
"""The trend level used for every headline table. See :data:`TREND_BASES`."""


def report() -> str:
    lines: list[str] = []
    write = lines.append
    target = dict(CANDIDATE_CAPITAL)

    # 1. Units.
    write("## 1. Units")
    exposure = implied_notional(CANDIDATE_CAPITAL)
    write(f"capital deployed {sum(CANDIDATE_CAPITAL.values()):.4f}")
    for kind, value in sorted(exposure.items()):
        write(f"  {kind:26s} {_pp(value):>7s} pp of capital")
    write(f"  gross notional             {_pp(gross_notional(CANDIDATE_CAPITAL)):>7s} pp")
    equity = sum(value for kind, value in exposure.items() if kind != "trend")
    write(f"  equity notional            {_pp(equity):>7s} pp")
    honest = capital_for_notional(
        CANDIDATE_CAPITAL, kind="us-equity", target=0.65, adjust=["VTI", "AVLV"]
    )
    write(
        "  capital weights that deliver exactly 65 pp of US equity notional: "
        + ", ".join(f"{name} {_pp(weight)}" for name, weight in honest.items())
        + f"; capital deployed {sum(honest.values()):.4f}"
    )
    write("")
    for mistake in (normalised_notional_capital(), double_counted_capital()):
        write(f"{mistake.label}: capital deployed {mistake.capital_deployed:.4f}")
        for kind, error in sorted(mistake.error_by_kind.items()):
            write(f"  {kind:26s} error {_pp(error):>7s} pp")
        worst_kind, worst = mistake.worst_error
        write(
            f"  worst: {worst_kind} {_pp(worst)} pp; gross "
            f"{_pp(mistake.gross_notional)} pp; typed weights "
            + ", ".join(f"{name} {_pp(weight)}" for name, weight in mistake.capital.items())
        )
        write("")

    # 2. Placement frontier.
    write("## 2. Placement: headroom against drag")
    ceiling = max_achievable_headroom(
        target, taxable_share=TAXABLE_SHARE, barred=["RSST"]
    )
    write(
        f"ceiling on min headroom at a {TAXABLE_SHARE:.4f} taxable share and "
        f"{len(target)} lines: {_pp(ceiling)} pp"
    )
    for count, weights in (
        (8, target),
        (5, {"RSST": 0.30, "VTI": 0.20, "AVLV": 0.15, "VEA": 0.25, "IEMG": 0.10}),
        (4, {"RSST": 0.30, "VTI": 0.20, "AVLV": 0.15, "VXUS": 0.35}),
        (3, {"RSST": 0.30, "VTI": 0.35, "VXUS": 0.35}),
    ):
        write(
            f"  {count} lines: ceiling "
            f"{_pp(max_achievable_headroom(weights, taxable_share=TAXABLE_SHARE))} pp "
            f"unrestricted, "
            f"{_pp(max_achievable_headroom(weights, taxable_share=TAXABLE_SHARE, barred=['RSST']))}"
            f" pp with the wrapper barred"
        )
    write("")
    write("shelter priority per dollar of capacity, bp/yr, by bracket "
          "(lowest goes to taxable first):")
    for rate in QUALIFIED_RATES:
        costs = placement_costs_at(rate)
        order = sorted(costs, key=lambda name: costs[name].priority_bp)
        write(
            f"  {100 * rate:4.1f}% qualified / {100 * ordinary_rate_for(rate):4.1f}% "
            "ordinary: "
            + ", ".join(f"{name} {costs[name].priority_bp:.1f}" for name in order)
        )
    write("")
    plan = placement_plan()
    check_placement(plan)
    room = headroom(placement_totals(plan), taxable_vector(plan))
    write(
        f"The published placement plan: drag {placement_drag_bp(plan):.2f} bp/yr, "
        f"min headroom {_pp(room.minimum)} pp on {room.binding_fund}"
    )
    write("  per-fund headroom: " + ", ".join(
        f"{name} {_pp(value)}" for name, value in sorted(room.per_fund.items())
    ))
    write("")
    write("| min headroom pp | drag bp/yr | premium over the cheapest | taxable holds |")
    frontier: list[tuple[float, float]] = []
    for step in range(0, 12):
        want_room = step / 100.0
        if want_room > ceiling:
            break
        placement = headroom_placement(want_room)
        drag = placement_drag_bp(placement)
        frontier.append((want_room, drag))
        held = ", ".join(
            f"{name} {_pp(by[Account.TAXABLE])}"
            for name, by in sorted(placement.items())
            if by[Account.TAXABLE] > 1e-9
        )
        write(f"| {_pp(want_room):>5s} | {drag:.2f} | {drag - frontier[0][1]:+.2f} | {held} |")
    ceiling_placement = headroom_placement(ceiling)
    write(
        f"| {_pp(ceiling):>5s} | {placement_drag_bp(ceiling_placement):.2f} | "
        f"{placement_drag_bp(ceiling_placement) - frontier[0][1]:+.2f} | ceiling |"
    )
    write("")
    write("after-tax account shares, which are what constrain rebalancing:")
    shares = after_tax_account_shares(
        balances={account: 1.0 / 3.0 for account in Account},
        ordinary_rate=0.24,
        capital_gains_rate=LONG_TERM_RATE,
        taxable_gain_fraction=gain_fraction_after(years=10, growth_rate=0.07),
    )
    write("  " + ", ".join(f"{a.value} {_pp(v)}%" for a, v in shares.items()))
    write("")
    write("| qualified rate | cheapest taxable holding at 5 pp of headroom | drag bp/yr | "
          "foreign-to-taxable drag bp/yr |")
    for rate in QUALIFIED_RATES:
        costs = placement_costs_at(rate)
        cheap = min_drag_placement(
            target, taxable_share=TAXABLE_SHARE, min_headroom=0.05, costs=costs,
            sheltered_split=SHELTERED_SPLIT, taxable_capacity={"RSST": 0.0},
        )
        held = ", ".join(
            f"{name} {_pp(by[Account.TAXABLE])}"
            for name, by in sorted(cheap.items())
            if by[Account.TAXABLE] > 1e-9
        )
        write(
            f"| {100 * rate:.1f}% | {held} | {placement_drag_bp(cheap, costs):.2f} | "
            f"{placement_drag_bp(plan, costs):.2f} |"
        )
    write("")
    write("| wrapper reading | plan drag bp/yr | 5 pp headroom drag bp/yr |")
    for reading in ("recognised", "distributed"):
        costs = placement_costs_at(0.238, wrapper_reading=reading)
        write(
            f"| {reading} | {placement_drag_bp(plan, costs):.2f} | "
            f"{placement_drag_bp(headroom_placement(0.05), costs):.2f} |"
        )
    write("")

    # 3. Drift budget and the forced trade.
    write("## 3. Drift budget and what a forced trade costs")
    for limit in (0.35, 0.375, 0.40, 0.4375):
        ratio = relative_drift_to_infeasibility(
            taxable_share=TAXABLE_SHARE, sheltered_share=1.0 - TAXABLE_SHARE, limit=limit
        )
        write(
            f"  international entirely taxable, limit {_pp(limit)}%: infeasible after "
            f"{100.0 * (ratio - 1.0):.1f}% cumulative relative outperformance"
        )
    write("")
    for years in (5.0, 10.0, 20.0, 30.0):
        fraction = gain_fraction_after(years=years, growth_rate=0.07)
        trade = forced_realisation_cost(
            traded=1.0, gain_fraction=fraction, tax_rate=LONG_TERM_RATE,
            spread_bp=SPREAD_BP,
        )
        write(
            f"  held {years:4.0f} yr at 7%: gain {_pp(fraction)}% of value, tax "
            f"{BP * trade.tax:7.1f} bp of the trade, spread {BP * trade.friction:.1f} bp, "
            f"ratio {trade.tax_to_friction:.0f}x"
        )
    write("")

    # 4. The recommended placements, line by line.
    write("## 4. The recommended placement, line by line")
    for label, weights in (
        ("eight lines", target),
        ("five lines", {"RSST": 0.30, "VTI": 0.20, "AVLV": 0.15, "VEA": 0.25,
                        "IEMG": 0.10}),
    ):
        plan = min_drag_placement(
            weights, taxable_share=TAXABLE_SHARE, min_headroom=0.05,
            sheltered_split=SHELTERED_SPLIT, taxable_capacity={"RSST": 0.0},
        )
        write(f"### {label}, drag {placement_drag_bp(plan):.2f} bp/yr, ceiling "
              f"{_pp(max_achievable_headroom(weights, taxable_share=TAXABLE_SHARE))} pp")
        # At target, headroom equals the sheltered holding, so one column serves both.
        write("| fund | target pp | taxable pp | sheltered pp = headroom pp |")
        for fund, want in weights.items():
            taxed = plan[fund][Account.TAXABLE]
            write(f"| {fund} | {_pp(want)} | {_pp(taxed)} | {_pp(want - taxed)} |")
    write("")

    # 5. Simulation.
    returns, periods = load_proxies(trend_mean_per_year=TREND_BASES[PRIMARY_TREND_BASIS])
    write(f"## 5. Policies, {periods[0]}..{periods[-1]}, {len(periods)} months")
    write(f"trend leg on the {PRIMARY_TREND_BASIS} basis")
    write("proxies: " + "; ".join(f"{k} = {v}" for k, v in PROXIES.items()))
    regime = TaxRegime(long_term_rate=LONG_TERM_RATE, spread_bp=SPREAD_BP)
    header = (
        "| policy | mean abs dev pp | max dev pp | trend notional err pp (mean/max) | "
        "reviews/yr | trades/yr | turnover %/yr | cost bp/yr | tax bp/yr | "
        "infeasible mo | worst headroom pp |"
    )
    placements = (
        ("P: the published plan, 0 pp of headroom", placement_plan()),
        ("H3: 3 pp of headroom", headroom_placement(0.03)),
        ("H5: 5 pp of headroom", headroom_placement(0.05)),
    )
    for label, placement in placements:
        write("")
        write(f"### Placement {label}, drag {placement_drag_bp(placement):.2f} bp/yr")
        write(header)
        for rule in rules():
            result = _run(returns, placement, rule, regime)
            write(_row(result))

    # 5b. The joint objective: drag plus the realisation cost it forces.
    write("")
    write("## 5b. The joint objective: recurring drag + forced realisation, bp/yr")
    write("Both arms hold the same portfolio-level target. The disciplined arm refuses to")
    write("sell in taxable and pays in exposure error instead; the restoring arm sells and")
    write("pays tax. Annual review, 25% relative band, wrapper barred from taxable.")
    write(
        "| headroom pp | drag bp/yr | forced tax bp/yr | **total bp/yr** | "
        "disciplined mean dev pp | disciplined max dev pp | infeasible mo |"
    )
    band = RebalanceRule("Annual review, act on a 25% relative band", review_months=12,
                         relative_band=0.25)
    restoring = RebalanceRule("Annual review, band, taxable sales allowed",
                              review_months=12, relative_band=0.25,
                              allow_taxable_sales=True)
    best: tuple[float, float] | None = None
    for step in (0, 1, 2, 3, 4, 5):
        want_room = step / 100.0
        if want_room > ceiling:
            break
        plan_here = placement_plan() if step == 0 else headroom_placement(want_room)
        drag = placement_drag_bp(plan_here)
        firm = _run(returns, plan_here, band, regime)
        sells = _run(returns, plan_here, restoring, regime)
        total = drag + BP * sells.tax_paid_per_year
        if best is None or total < best[1]:
            best = (want_room, total)
        write(
            f"| {_pp(want_room)} | {drag:.2f} | {BP * sells.tax_paid_per_year:.2f} | "
            f"**{total:.2f}** | {_pp(firm.mean_absolute_deviation)} | "
            f"{_pp(firm.max_absolute_deviation)} | {firm.months_infeasible} |"
        )
    recommended = one_point_of_vti()
    check_placement(recommended)
    room_here = headroom(placement_totals(recommended), taxable_vector(recommended))
    firm = _run(returns, recommended, band, regime)
    sells = _run(returns, recommended, restoring, regime)
    drag = placement_drag_bp(recommended)
    write(
        f"| **{_pp(room_here.minimum)} (one point of VTI moved)** | {drag:.2f} | "
        f"{BP * sells.tax_paid_per_year:.2f} | "
        f"**{drag + BP * sells.tax_paid_per_year:.2f}** | "
        f"{_pp(firm.mean_absolute_deviation)} | {_pp(firm.max_absolute_deviation)} | "
        f"{firm.months_infeasible} |"
    )
    if best is not None:
        write(f"minimum total on the frontier at {_pp(best[0])} pp of headroom, "
              f"{best[1]:.2f} bp/yr")
    write("")
    write("hostile: an embedded gain on day one, and a tighter band")
    write("| test | headroom pp | drag | forced tax | total | infeasible mo |")
    for label, gain, give, rule in (
        ("embedded gain 40%", 0.40, CONTRIBUTION_PER_YEAR, restoring),
        ("embedded gain 70%", 0.70, CONTRIBUTION_PER_YEAR, restoring),
        ("10% relative band", 0.0, CONTRIBUTION_PER_YEAR, RebalanceRule(
            "band 10", review_months=12, relative_band=0.10, allow_taxable_sales=True)),
        ("quarterly review", 0.0, CONTRIBUTION_PER_YEAR, RebalanceRule(
            "quarterly", review_months=3, relative_band=0.25, allow_taxable_sales=True)),
        ("no contributions", 0.0, 0.0, restoring),
    ):
        for step in (0, 1, 3):
            want_room = step / 100.0
            plan_here = placement_plan() if step == 0 else headroom_placement(want_room)
            drag = placement_drag_bp(plan_here)
            sells = _run(
                returns, plan_here, rule, regime, contribution=give, initial_gain=gain
            )
            firm_rule = RebalanceRule(
                rule.label, review_months=rule.review_months,
                relative_band=rule.relative_band,
            )
            firm_here = _run(
                returns, plan_here, firm_rule, regime, contribution=give,
                initial_gain=gain,
            )
            name = _pp(want_room)
            write(
                f"| {label} | {name} | {drag:.2f} | "
                f"{BP * sells.tax_paid_per_year:.2f} | "
                f"{drag + BP * sells.tax_paid_per_year:.2f} | "
                f"{firm_here.months_infeasible} |"
            )
    write("")
    write("| wrapper reading | headroom pp | drag | forced tax | total |")
    for reading in ("recognised", "distributed"):
        costs = placement_costs_at(0.238, wrapper_reading=reading)
        for step in (0, 3, 5):
            want_room = step / 100.0
            plan_here = placement_plan() if step == 0 else headroom_placement(want_room)
            drag = placement_drag_bp(plan_here, costs)
            sells = _run(returns, plan_here, restoring, regime)
            write(
                f"| {reading} | {_pp(want_room)} | {drag:.2f} | "
                f"{BP * sells.tax_paid_per_year:.2f} | "
                f"{drag + BP * sells.tax_paid_per_year:.2f} |"
            )

    # 6. Growth, with the resolution beside it.
    write("")
    write("## 6. Growth, and whether the design can resolve it")
    placement = placements[2][1]
    baseline = _run(returns, placement, rules()[0], regime)
    for rule in rules():
        result = _run(returns, placement, rule, regime)
        write(
            f"| {result.label} | {100 * result.growth_per_year:.3f} %/yr | "
            f"{100 * (result.growth_per_year - baseline.growth_per_year):+.3f} pp/yr | "
            f"MDE80 {100 * minimum_detectable_effect(_gap(result, baseline)):.3f} pp/yr |"
        )
    write(
        f"effective sample: {len(periods)} months, "
        f"{len(periods) / MONTHS_PER_YEAR:.1f} non-overlapping years"
    )

    # 7. The contribution rule.
    write("")
    write("## 7. Where taxable contributions should go")
    for by_headroom in (True, False):
        result = _run(
            returns, placement,
            RebalanceRule("Annual calendar, sheltered only", review_months=12),
            regime, by_headroom=by_headroom,
        )
        write(
            f"| taxable contributions by {'headroom' if by_headroom else 'deficit'} | "
            f"mean abs dev {_pp(result.mean_absolute_deviation)} pp | "
            f"max {_pp(result.max_absolute_deviation)} pp | "
            f"infeasible {result.months_infeasible} mo | "
            f"worst headroom {_pp(result.worst_headroom)} pp |"
        )

    # 8. Consolidation.
    designed = portfolio_returns(returns, dict(CANDIDATE_CAPITAL))
    write("")
    write("## 8. What a consolidation costs")
    write("| portfolio | tracking error vs the eight-line target | trend notional |")
    for label, consolidated in _consolidations().items():
        candidate = portfolio_returns(returns, consolidated)
        write(
            f"| {label} | {100 * tracking_error(candidate, designed):.2f} %/yr | "
            f"{_pp(implied_notional(consolidated).get('trend', 0.0))} pp |"
        )

    # 9. Holdability.
    write("")
    write("## 9. The stretches that are hardest to hold")
    us_market = np.asarray(returns["VTI"], dtype=np.float64)
    write("These rows contain no trend leg, so no assumption about it can move them.")
    write("| comparison | depth | length | window |")
    for label, candidate, benchmark in (
        ("US value tilt vs US market",
         np.asarray(returns["AVLV"], dtype=np.float64), us_market),
        ("International vs US",
         portfolio_returns(returns, {"DFIV": 2 / 7, "VEA": 2 / 7, "IDMO": 1 / 7,
                                     "IEMG": 1 / 7, "AVES": 1 / 7}), us_market),
        ("Ex-US value vs ex-US market",
         np.asarray(returns["DFIV"], dtype=np.float64),
         np.asarray(returns["VEA"], dtype=np.float64)),
    ):
        stretch = worst_relative_stretch(candidate, benchmark, periods)
        write(
            f"| {label} | {100 * stretch.depth:.1f}% behind | {stretch.years:.1f} yr | "
            f"{stretch.start} -> {stretch.trough} -> "
            f"{stretch.recovered or 'not recovered'} |"
        )
    write("")
    write("These rows do, so each is reported on all three trend bases.")
    write("| trend basis | comparison | depth | length | window | mean gap pp/yr | MDE80 |")
    for name, mean in TREND_BASES.items():
        source, _ = load_proxies(trend_mean_per_year=mean)
        base_market = np.asarray(source["VTI"], dtype=np.float64)
        whole = portfolio_returns(source, dict(CANDIDATE_CAPITAL))
        for comparison, candidate, benchmark in (
            ("whole portfolio vs US market", whole, base_market),
            ("stacked wrapper vs the equity it displaces",
             np.asarray(source["RSST"], dtype=np.float64), base_market),
        ):
            stretch = worst_relative_stretch(candidate, benchmark, periods)
            gap = np.asarray(candidate) - np.asarray(benchmark)
            write(
                f"| {name} | {comparison} | {100 * stretch.depth:.1f}% behind | "
                f"{stretch.years:.1f} yr | {stretch.start} -> {stretch.trough} -> "
                f"{stretch.recovered or 'not recovered'} | "
                f"{100 * MONTHS_PER_YEAR * float(np.mean(gap)):+.2f} | "
                f"{100 * minimum_detectable_effect(gap):.2f} |"
            )

    # 10. Sensitivities.
    write("")
    write("## 10. Sensitivities")
    write("| trend basis | placement | buy-and-hold mean dev pp | max dev pp | "
          "buy-and-hold trend notional err max pp | annual mean dev pp | "
          "annual infeasible mo | annual worst headroom pp |")
    for name, mean in TREND_BASES.items():
        source, _ = load_proxies(trend_mean_per_year=mean)
        for plan_label, plan in placements[1:]:
            buy_hold = _run(source, plan, rules()[0], regime)
            annual = _run(
                source, plan,
                RebalanceRule("Annual calendar, sheltered only", review_months=12), regime,
            )
            write(
                f"| {name} | {plan_label} | {_pp(buy_hold.mean_absolute_deviation)} | "
                f"{_pp(buy_hold.max_absolute_deviation)} | "
                f"{_pp(buy_hold.max_trend_notional_error)} | "
                f"{_pp(annual.mean_absolute_deviation)} | {annual.months_infeasible} | "
                f"{_pp(annual.worst_headroom)} |"
            )
    write("")
    for spread in (SPREAD_BP, SPREAD_BP_PESSIMISTIC):
        result = _run(
            returns, placement,
            RebalanceRule("Quarterly calendar, sheltered only", review_months=3),
            TaxRegime(long_term_rate=LONG_TERM_RATE, spread_bp=spread),
        )
        write(f"| quarterly at {spread:.0f} bp one-way | cost "
              f"{BP * result.friction_cost_per_year:.2f} bp/yr |")
    for contribution in (0.0, CONTRIBUTION_PER_YEAR, 0.10):
        result = _run(
            returns, placement,
            RebalanceRule("Contribution-directed only", review_months=1,
                          absolute_band=math.inf),
            regime, contribution=contribution,
        )
        write(f"| contribution-directed at {100 * contribution:.0f}%/yr | mean abs dev "
              f"{_pp(result.mean_absolute_deviation)} pp | max "
              f"{_pp(result.max_absolute_deviation)} pp |")
    for share in (0.0, TAXABLE_SHARE):
        result = _run(
            returns, placement,
            RebalanceRule("Annual calendar, sheltered only", review_months=12),
            regime, to_taxable=share,
        )
        write(f"| {100 * share:.0f}% of new money to taxable | mean abs dev "
              f"{_pp(result.mean_absolute_deviation)} pp | infeasible "
              f"{result.months_infeasible} mo |")

    write("")
    write(f"accounts: {[f'{a.value} {v:.4f}' for a, v in account_totals(placement).items()]}")
    return "\n".join(lines)


def _gap(result: OperationsResult, baseline: OperationsResult) -> NDArray[np.float64]:
    """Monthly paired difference of two policies run on the same returns."""
    return np.asarray(
        np.asarray(result.monthly_returns) - np.asarray(baseline.monthly_returns),
        dtype=np.float64,
    )


def _run(
    returns: Mapping[str, Sequence[float]],
    placement: Placement,
    rule: RebalanceRule,
    regime: TaxRegime,
    *,
    by_headroom: bool = True,
    contribution: float = CONTRIBUTION_PER_YEAR,
    to_taxable: float = TAXABLE_SHARE,
    initial_gain: float = 0.0,
) -> OperationsResult:
    return simulate_operations(
        returns=returns, placement=placement, rule=rule, regime=regime,
        contribution_per_year=contribution, contribution_to_taxable=to_taxable,
        taxable_eligible=[
            name for name, by in placement.items()
            if by.get(Account.TAXABLE, 0.0) > 1e-9
        ],
        taxable_contributions_by_headroom=by_headroom,
        initial_gain_fraction=initial_gain,
    )


def _row(result: OperationsResult) -> str:
    return (
        f"| {result.label} | {_pp(result.mean_absolute_deviation)} | "
        f"{_pp(result.max_absolute_deviation)} | "
        f"{_pp(result.mean_trend_notional_error)}/"
        f"{_pp(result.max_trend_notional_error)} | "
        f"{result.decisions_per_year:.1f} | {result.trades_per_year:.1f} | "
        f"{100 * result.turnover_per_year:.2f} | "
        f"{BP * result.friction_cost_per_year:.2f} | "
        f"{BP * result.tax_paid_per_year:.2f} | {result.months_infeasible} | "
        f"{_pp(result.worst_headroom)} |"
    )


def _consolidations() -> Mapping[str, Mapping[str, float]]:
    """Candidate simplifications, each keeping the same 65/35 and the same 30% of trend.

    Split into single-line cuts, which are the only ones that can be attributed to a line,
    and the cumulative ladder, which cannot: tracking errors do not add, so the ladder's
    increments are not the cost of the lines they drop.
    """
    return {
        "8: as designed": dict(CANDIDATE_CAPITAL),
        "7: IDMO alone, into VEA (simplification)": {
            "RSST": 0.30, "VTI": 0.20, "AVLV": 0.15,
            "DFIV": 0.10, "VEA": 0.15, "IEMG": 0.05, "AVES": 0.05,
        },
        "7: AVES alone, into IEMG (simplification)": {
            "RSST": 0.30, "VTI": 0.20, "AVLV": 0.15,
            "DFIV": 0.10, "VEA": 0.10, "IDMO": 0.05, "IEMG": 0.10,
        },
        "7: DFIV alone, into VEA (a change of intent, not a simplification)": {
            "RSST": 0.30, "VTI": 0.20, "AVLV": 0.15,
            "VEA": 0.20, "IDMO": 0.05, "IEMG": 0.05, "AVES": 0.05,
        },
        # The merge is the identity on holdings: a total-international fund at 15 pp
        # holding VEA and IEMG two to one *is* VEA 10 plus IEMG 5. It is free only if the
        # investor wants the fund's own regional split rather than a fixed one; the row
        # exists to pin that the exposure cost is exactly zero.
        "8: VEA and IEMG bought as one total-international fund": dict(CANDIDATE_CAPITAL),
        "6: DFIV dropped, VEA and IEMG merged": {
            "RSST": 0.30, "VTI": 0.20, "AVLV": 0.15, "VEA": 0.25, "IDMO": 0.05,
            "AVES": 0.05,
        },
        "5: also AVES into the international line": {
            "RSST": 0.30, "VTI": 0.20, "AVLV": 0.15, "VEA": 0.30, "IDMO": 0.05,
        },
        "7: drop IDMO": {
            "RSST": 0.30, "VTI": 0.20, "AVLV": 0.15,
            "DFIV": 0.10, "VEA": 0.15, "IEMG": 0.05, "AVES": 0.05,
        },
        "6: also drop AVES": {
            "RSST": 0.30, "VTI": 0.20, "AVLV": 0.15,
            "DFIV": 0.10, "VEA": 0.15, "IEMG": 0.10,
        },
        "5: also drop DFIV": {
            "RSST": 0.30, "VTI": 0.20, "AVLV": 0.15, "VEA": 0.25, "IEMG": 0.10,
        },
        "3: also drop AVLV, the US value tilt, into VTI": {
            "RSST": 0.30, "VTI": 0.35, "VEA": 0.25, "IEMG": 0.10,
        },
    }


if __name__ == "__main__":  # pragma: no cover - a reporting entry point
    print(report())
