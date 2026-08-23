"""Regenerates every table in ``docs/research/harvesting-and-direct-indexing.md``.

Kept separate from :mod:`portfolio_edge.studies.tax_loss_harvesting` so the study stays
pure and testable and only this file touches the raw cache. Run it with::

    cd research && uv run python -m portfolio_edge.studies.tax_loss_harvesting

**Everything here is `exploratory`.** No specification was frozen before these numbers
were seen, and no experiment is registered: this is a sizing exercise for an
implementation decision, not a hypothesis test about a market.

Three things are measured and two are modelled
----------------------------------------------
*Measured, from the committed Ken French 49-industry file.*

1. **Single-stock idiosyncratic volatility**, backed out of a cross-sectional
   regression of each industry portfolio's residual variance on the reciprocal of its
   firm count. An equal-weighted portfolio of ``n`` stocks carries ``sigma_idio^2 / n``
   of idiosyncratic variance, so the slope identifies ``sigma_idio^2`` and the intercept
   collects whatever common industry variance the market factor did not absorb. The
   identifying assumption is that idiosyncratic variance is uncorrelated with firm count
   across industries; it is not, which is why the estimate is also run separately on the
   larger and smaller halves of the industries by average firm size and reported as a
   range.
2. **The frequency and depth of harvestable losses**, at the position level and at the
   fund level, over every start month. This needs no model at all: it is the share of
   positions trading more than 5% below a lot bought ``h`` months earlier.
3. **The tracking error harvesting creates**, by running the harvest rule on the real
   monthly panel and differencing against the identical account that never sold.

*Modelled, in the study module.* The decay curve and the after-tax benefit, over
simulated market paths, under three brackets and three disposal paths.

The industry proxy and what it costs
------------------------------------
A 49-industry portfolio is a **diversified basket**, not a stock. Using it as a proxy
for a position understates dispersion badly, so measurements 2 and 3 are **floors on
frequency and depth** and measurement 3's tracking error is, for the opposite reason, a
**ceiling**: 49 positions with proceeds redistributed across the other 48 is a far
cruder replacement than a 500-name direct index buying one close substitute. Both
directions are stated wherever a figure is quoted.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from portfolio_edge.data import french
from portfolio_edge.data.cache import RawCache
from portfolio_edge.studies.tax_loss_harvesting import (
    MIDDLE_BRACKET,
    Disposal,
    HarvestRule,
    HarvestYieldPaths,
    LossUsage,
    MarketAssumptions,
    active_risk_from_substitution,
    lock_in_exit_cost_bp,
    ordinary_offset_ceiling_bp,
    simulate_harvest_yield,
    value_harvesting,
)
from portfolio_edge.studies.tax_structure import TOP_BRACKET, UPPER_MIDDLE_BRACKET, TaxRegime

FloatArray = NDArray[np.float64]

HARVEST_THRESHOLD = 0.05
"""A lot is harvested when it trades more than 5% below its basis. An operating choice,
not a tax rule: §1091 says nothing about how far down a loss must be."""

VTI_NET_COST = 0.000116
"""VTI's cost to own: a 3 bp fee less 1.84 bp of median securities-lending income, from
``structural-and-tax-edges.md`` §6.1, which reads it from 110 Form N-CEN filings. A
direct index replaces the fund, so it forfeits the lending offset as well as paying its
own fee, and the right hurdle is this number rather than the 3 bp headline."""

FUND_SWAP_COST = 0.0001
"""Round-trip cost of swapping one broad ETF for another: 1 bp, and conservative.
``structural-and-tax-edges.md`` §6.6 measures VTI's 30-day median bid-ask spread at
0.55 bp and ITOT's at 1 bp, so selling one and buying the other costs about 0.8 bp of
half-spreads. A single-stock direct index pays several times it, which is why the two
routes are priced with different trading costs."""

FREC_FEE = 0.0009
"""0.09% a year, $20,000 minimum, verified at frec.com/direct-indexing on 2026-08-23.
The provider lists **Morningstar US Total Market** among its indices, which since
2026-07-29 is VTI's own target index, so the sleeve substitution is exact rather than
approximate. No other provider's schedule was re-verified on that date; the wider list
in ``tax_structure.DIRECT_INDEXING_FEES_BP`` is dated mid-2026 and is carried forward
unchanged."""


@dataclass(frozen=True)
class IndustryPanel:
    """The committed 49-industry file, aligned with the market series."""

    periods: tuple[str, ...]
    returns: FloatArray
    firm_counts: FloatArray
    average_firm_size: FloatArray
    market_total_return: FloatArray
    risk_free: FloatArray
    sha256_industries: str
    sha256_factors: str


def load_industry_panel(cache: RawCache | None = None) -> IndustryPanel:
    """Read the two committed French files from the raw cache. Never touches the network.

    Equal-weighted industry returns are used deliberately. The ``sigma_idio^2 / n``
    identity holds for an equal-weighted basket of ``n`` names and not for a
    value-weighted one, whose effective breadth is far below its firm count.
    """
    cache = cache or RawCache()
    industries = french.get_dataset("french_us_49_industry_portfolios")
    factors = french.get_dataset("french_us_ff3")
    industry_entry = cache.require(industries.url)
    factor_entry = cache.require(factors.url)
    parsed = french.parse(cache, industry_entry, dataset=industries)
    factor_file = french.parse(cache, factor_entry, dataset=factors)

    returns_table = parsed.table("average_equal_weighted_returns_monthly")
    counts_table = parsed.table("number_of_firms_in_portfolios_monthly")
    size_table = parsed.table("average_firm_size_monthly")
    factor_table = factor_file.table("monthly")

    def dense(rows: tuple[tuple[float | None, ...], ...]) -> FloatArray:
        return np.array(
            [[np.nan if value is None else value for value in row] for row in rows],
            dtype=np.float64,
        )

    index = {period: row for row, period in enumerate(factor_table.periods)}
    market_column = factor_table.columns.index("Mkt-RF")
    rf_column = factor_table.columns.index("RF")
    excess = np.array(
        [factor_table.values[index[period]][market_column] for period in returns_table.periods],
        dtype=np.float64,
    )
    risk_free = np.array(
        [factor_table.values[index[period]][rf_column] for period in returns_table.periods],
        dtype=np.float64,
    )
    return IndustryPanel(
        periods=returns_table.periods,
        returns=dense(returns_table.values),
        firm_counts=dense(counts_table.values),
        average_firm_size=dense(size_table.values),
        market_total_return=excess + risk_free,
        risk_free=risk_free,
        sha256_industries=industry_entry.sha256,
        sha256_factors=factor_entry.sha256,
    )


@dataclass(frozen=True)
class IdiosyncraticEstimate:
    """One cross-sectional regression, with the resolution it actually has."""

    label: str
    first_period: str
    last_period: str
    industries: int
    common_volatility: float
    idiosyncratic_volatility: float
    slope_t_statistic: float
    r_squared: float


def estimate_idiosyncratic_volatility(
    panel: IndustryPanel,
    *,
    label: str,
    first_year: str,
    last_year: str,
    columns: tuple[int, ...] | None = None,
    minimum_months: int = 60,
    minimum_firms: float = 3.0,
) -> IdiosyncraticEstimate:
    """Regress industry residual variance on the reciprocal of the firm count.

    ``residual variance_j = common variance + sigma_idio^2 x mean(1 / n_j)``

    The residual is taken after a market regression on each industry's own excess
    return, so the intercept is the average *industry-factor* variance and the slope is
    the average *stock-level* idiosyncratic variance. Both are reported as annualised
    standard deviations, because that is the unit the harvesting model consumes.
    """
    rows = np.array(
        [
            row
            for row, period in enumerate(panel.periods)
            if first_year <= period[:4] <= last_year
        ],
        dtype=np.intp,
    )
    if rows.size == 0:
        raise ValueError(f"{label}: no observations in {first_year}..{last_year}")
    wanted = tuple(range(panel.returns.shape[1])) if columns is None else columns

    excess_market = panel.market_total_return[rows] - panel.risk_free[rows]
    residual_variance: list[float] = []
    inverse_count: list[float] = []
    for column in wanted:
        excess = panel.returns[rows, column] - panel.risk_free[rows]
        usable = (
            np.isfinite(excess)
            & np.isfinite(excess_market)
            & (panel.firm_counts[rows, column] >= minimum_firms)
        )
        if int(usable.sum()) < minimum_months:
            continue
        design = np.column_stack([np.ones(int(usable.sum())), excess_market[usable]])
        beta, *_ = np.linalg.lstsq(design, excess[usable], rcond=None)
        residual = excess[usable] - design @ beta
        residual_variance.append(float(np.var(residual, ddof=2)))
        inverse_count.append(float(np.mean(1.0 / panel.firm_counts[rows, column][usable])))

    y = np.array(residual_variance, dtype=np.float64)
    design = np.column_stack([np.ones(y.size), np.array(inverse_count, dtype=np.float64)])
    coefficients, *_ = np.linalg.lstsq(design, y, rcond=None)
    fitted = design @ coefficients
    degrees = y.size - 2
    sigma_squared = float(np.sum((y - fitted) ** 2) / degrees)
    covariance = np.linalg.inv(design.T @ design)
    standard_error = math.sqrt(sigma_squared * float(covariance[1, 1]))
    r_squared = 1.0 - float(np.sum((y - fitted) ** 2) / np.sum((y - float(np.mean(y))) ** 2))
    return IdiosyncraticEstimate(
        label=label,
        first_period=panel.periods[int(rows[0])],
        last_period=panel.periods[int(rows[-1])],
        industries=int(y.size),
        common_volatility=math.sqrt(max(float(coefficients[0]), 0.0) * 12.0),
        idiosyncratic_volatility=math.sqrt(max(float(coefficients[1]), 0.0) * 12.0),
        slope_t_statistic=float(coefficients[1]) / standard_error,
        r_squared=r_squared,
    )


def size_split(panel: IndustryPanel, *, first_year: str, last_year: str) -> tuple[
    tuple[int, ...], tuple[int, ...]
]:
    """Industries below and above the median average firm size over a window."""
    rows = np.array(
        [
            row
            for row, period in enumerate(panel.periods)
            if first_year <= period[:4] <= last_year
        ],
        dtype=np.intp,
    )
    mean_size = np.nanmean(panel.average_firm_size[rows], axis=0)
    order = np.argsort(mean_size)
    half = order.size // 2
    return tuple(int(c) for c in order[:half]), tuple(int(c) for c in order[half + 1 :])


@dataclass(frozen=True)
class BelowCostFrequency:
    """How often a lot is harvestable, measured over every start month."""

    horizon_months: int
    position_share: float
    market_share: float
    position_mean_depth: float


def below_cost_frequency(
    panel: IndustryPanel,
    *,
    first_year: str,
    last_year: str,
    horizons: tuple[int, ...] = (3, 6, 12, 24, 60, 120),
    threshold: float = HARVEST_THRESHOLD,
) -> tuple[BelowCostFrequency, ...]:
    """Share of positions, and of market start dates, more than 5% below cost.

    A pure measurement. Every start month in the window is used, so the horizons overlap
    heavily and the figures are not independent observations; they are a description of
    the sample rather than an estimate with a standard error, and no test is run on them.
    """
    rows = np.array(
        [
            row
            for row, period in enumerate(panel.periods)
            if first_year <= period[:4] <= last_year
        ],
        dtype=np.intp,
    )
    returns = panel.returns[rows]
    market = np.log1p(panel.market_total_return[rows])
    logs = np.log1p(returns)
    limit = math.log(1.0 - threshold)

    out: list[BelowCostFrequency] = []
    for horizon in horizons:
        shares: list[float] = []
        depths: list[float] = []
        market_hits: list[float] = []
        for start in range(logs.shape[0] - horizon):
            window = logs[start : start + horizon]
            usable = np.isfinite(returns[start]) & np.isfinite(returns[start + horizon - 1])
            cumulative = np.nansum(window, axis=0)[usable]
            below = cumulative < limit
            shares.append(float(np.mean(below)))
            if bool(below.any()):
                depths.append(float(-np.mean(np.expm1(cumulative[below]))))
            market_hits.append(float(market[start : start + horizon].sum() < limit))
        out.append(
            BelowCostFrequency(
                horizon_months=horizon,
                position_share=float(np.mean(shares)),
                market_share=float(np.mean(market_hits)),
                position_mean_depth=float(np.mean(depths)),
            )
        )
    return tuple(out)


@dataclass(frozen=True)
class RealisedHarvestRun:
    """The harvest rule run on the real monthly panel, one path, no model."""

    first_period: str
    last_period: str
    harvested_by_year: tuple[float, ...]
    tracking_error: float
    log_return_gap: float


def run_rule_on_panel(
    panel: IndustryPanel,
    *,
    first_year: str,
    last_year: str,
    contribution_rate: float = 0.10,
    threshold: float = HARVEST_THRESHOLD,
) -> RealisedHarvestRun:
    """Harvest the 49 industries as if they were positions, and price the drift.

    Proceeds are redistributed equally across the other 48 industries, which is the
    crudest possible replacement and therefore the **largest** tracking error the rule
    can produce on this panel. A 500-name direct index buying one close substitute per
    sale deviates far less. The number is quoted as a ceiling for that reason.
    """
    rows = [
        row for row, period in enumerate(panel.periods) if first_year <= period[:4] <= last_year
    ]
    returns = panel.returns[np.array(rows, dtype=np.intp)]
    months, industries = returns.shape

    basis = np.zeros((months, industries), dtype=np.float64)
    value = np.zeros((months, industries), dtype=np.float64)
    live = np.zeros((months, industries), dtype=bool)
    held = np.zeros((months, industries), dtype=np.float64)
    harvested = np.zeros(months // 12 + 1, dtype=np.float64)
    harvested_returns: list[float] = []
    held_returns: list[float] = []
    previous_account: float | None = None
    previous_held = 0.0

    for month in range(months):
        growth = 1.0 + np.nan_to_num(returns[month], nan=0.0)
        value[: month + 1] *= growth[None, :]
        held[: month + 1] *= growth[None, :]
        account = float(value[: month + 1][live[: month + 1]].sum())
        held_total = float(held[: month + 1].sum())
        if previous_account is not None:
            harvested_returns.append(account / previous_account - 1.0)
            held_returns.append(held_total / previous_held - 1.0)

        new_money = 1.0 if month == 0 else contribution_rate / 12.0 * account
        held_money = 1.0 if month == 0 else contribution_rate / 12.0 * held_total
        basis[month] += new_money / industries
        value[month] += new_money / industries
        live[month] = True
        held[month] += held_money / industries

        hit = live[: month + 1] & (value[: month + 1] < basis[: month + 1] * (1.0 - threshold))
        realised = np.where(hit, basis[: month + 1] - value[: month + 1], 0.0)
        harvested[month // 12] += float(realised.sum())
        proceeds = np.where(hit, value[: month + 1], 0.0)
        per_industry = proceeds.sum(axis=0)
        total = float(per_industry.sum())
        if total > 0.0:
            spread = (total - per_industry) / (industries - 1)
            window_basis = basis[: month + 1]
            window_value = value[: month + 1]
            window_basis[hit] = 0.0
            window_value[hit] = 0.0
            basis[month] += spread
            value[month] += spread
        previous_account = float(value[: month + 1][live[: month + 1]].sum())
        previous_held = float(held[: month + 1].sum())

    harvested_series = np.array(harvested_returns, dtype=np.float64)
    held_series = np.array(held_returns, dtype=np.float64)
    difference = harvested_series - held_series
    return RealisedHarvestRun(
        first_period=panel.periods[rows[0]],
        last_period=panel.periods[rows[-1]],
        harvested_by_year=tuple(float(x) for x in harvested),
        tracking_error=float(np.std(difference, ddof=1) * math.sqrt(12.0)),
        log_return_gap=float(
            12.0 * (np.mean(np.log1p(harvested_series)) - np.mean(np.log1p(held_series)))
        ),
    )


# --------------------------------------------------------------------------------------
# The modelled tables
# --------------------------------------------------------------------------------------

BRACKETS: tuple[tuple[TaxRegime, float, str], ...] = (
    (TOP_BRACKET, 0.37, "23.8% / 37%"),
    (MIDDLE_BRACKET, 0.32, "18.8% / 32%"),
    (UPPER_MIDDLE_BRACKET, 0.24, "15% / 24%"),
)
"""``(regime, marginal ordinary rate on wages, label)``.

The wage rate is not ``regime.ordinary``. The §1411 surtax reaches net investment
income, not salary, so a $3,000 deduction against wages is worth the bracket rate alone.
Where the loss also reduces net investment income it is worth up to 3.8 points more,
which is reported as a sensitivity and never booked."""


def baseline_market(idiosyncratic_volatility: float = 0.35) -> MarketAssumptions:
    """The central market assumption.

    Drift 7% pre-tax log growth, which ``tax_structure`` uses throughout so the two
    pages compare. Market volatility 15.8%, the measured monthly standard deviation of
    the French US market total return over 1996-2026 annualised. Dividend yield 1.5%,
    the order of VTI's. Idiosyncratic volatility is the swept parameter.
    """
    return MarketAssumptions(
        annual_total_log_drift=0.07,
        annual_market_volatility=0.158,
        annual_idiosyncratic_volatility=idiosyncratic_volatility,
        dividend_yield=0.015,
    )


def baseline_rule(
    *, contribution_rate: float = 0.10, years: int = 30, paths: int = 400
) -> HarvestRule:
    """Thirty years, 10%/yr of contributions — the midpoint of the stated 5-15% — and a
    5% harvest threshold."""
    return HarvestRule(
        years=years,
        harvest_threshold=HARVEST_THRESHOLD,
        contribution_rate=contribution_rate,
        lots_per_month=8,
        paths=paths,
        seed=20260823,
    )


def benefit_grid(
    paths: HarvestYieldPaths,
    *,
    account_value: float,
    gain_fractions: tuple[float, ...],
    fee: float = FREC_FEE,
) -> dict[tuple[str, str, float], tuple[float, float, float]]:
    """``(bracket, disposal, offsetting gain) -> (p10, median, p90)`` in bp/yr."""
    grid: dict[tuple[str, str, float], tuple[float, float, float]] = {}
    for regime, wage_rate, label in BRACKETS:
        for disposal in Disposal:
            for gain in gain_fractions:
                usage = LossUsage(
                    account_value=account_value,
                    annual_long_term_gain_fraction=gain,
                    marginal_ordinary_rate_on_wages=wage_rate,
                )
                value = value_harvesting(
                    paths,
                    regime=regime,
                    usage=usage,
                    disposal=disposal,
                    direct_index_fee=fee,
                    replaced_fund_cost=VTI_NET_COST,
                )
                grid[(label, disposal.value, gain)] = (
                    value.quantile(10.0),
                    value.median_bp,
                    value.quantile(90.0),
                )
    return grid


def break_even_gain_fraction(
    paths: HarvestYieldPaths,
    *,
    regime: TaxRegime,
    wage_rate: float,
    disposal: Disposal,
    account_value: float,
    fee: float = FREC_FEE,
    upper: float = 0.40,
    tolerance: float = 1e-4,
) -> float | None:
    """Offsetting long-term gain, as a fraction of the account, at which the median
    benefit crosses zero. ``None`` if it never does below ``upper``.

    This is the decision number. Direct indexing does not pay for itself out of the
    losses it harvests; it pays for itself out of the gains the investor already
    realises somewhere else, and this says how many of those are needed.
    """

    def median(gain: float) -> float:
        usage = LossUsage(
            account_value=account_value,
            annual_long_term_gain_fraction=gain,
            marginal_ordinary_rate_on_wages=wage_rate,
        )
        return value_harvesting(
            paths,
            regime=regime,
            usage=usage,
            disposal=disposal,
            direct_index_fee=fee,
            replaced_fund_cost=VTI_NET_COST,
        ).median_bp

    low, high = 0.0, upper
    if median(low) > 0.0:
        return 0.0
    if median(high) < 0.0:
        return None
    while high - low > tolerance:
        middle = 0.5 * (low + high)
        if median(middle) < 0.0:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)


def _median(
    paths: HarvestYieldPaths,
    regime: TaxRegime,
    wage_rate: float,
    gain: float,
    disposal: Disposal,
    fee: float,
    replaced: float,
    round_trip: float,
) -> float:
    usage = LossUsage(
        account_value=1_000_000.0,
        annual_long_term_gain_fraction=gain,
        marginal_ordinary_rate_on_wages=wage_rate,
    )
    return value_harvesting(
        paths,
        regime=regime,
        usage=usage,
        disposal=disposal,
        direct_index_fee=fee,
        replaced_fund_cost=replaced,
        round_trip_cost=round_trip,
    ).median_bp


def _crossover(
    direct_paths: HarvestYieldPaths,
    fund_paths: HarvestYieldPaths,
    regime: TaxRegime,
    wage_rate: float,
    disposal: Disposal,
    upper: float = 0.40,
) -> str:
    """Offsetting gain at which direct indexing's fee stops costing more than its extra
    dispersion earns. Below it, the free route wins."""

    def gap(gain: float) -> float:
        return _median(
            direct_paths, regime, wage_rate, gain, disposal, FREC_FEE, VTI_NET_COST, 0.0004
        ) - _median(fund_paths, regime, wage_rate, gain, disposal, 0.0, 0.0, FUND_SWAP_COST)

    if gap(0.0) > 0.0:
        return "0% - direct indexing wins everywhere"
    if gap(upper) < 0.0:
        return f"never below {upper:.0%} - fund-level wins throughout"
    low, high = 0.0, upper
    while high - low > 1e-4:
        middle = 0.5 * (low + high)
        if gap(middle) < 0.0:
            low = middle
        else:
            high = middle
    return f"{0.5 * (low + high):.2%}"


def main() -> None:  # pragma: no cover - a reporting entry point
    panel = load_industry_panel()
    print(f"49-industry file sha256 {panel.sha256_industries}")
    print(f"FF3 file sha256         {panel.sha256_factors}")

    print("\n== 1. Single-stock idiosyncratic volatility, from firm counts ==")
    print(f"{'window':22s} {'k':>3s} {'common sd':>10s} {'idio sd':>9s} {'t':>6s} {'R2':>6s}")
    windows = (
        ("1946", "1965"),
        ("1966", "1985"),
        ("1986", "2005"),
        ("2006", "2026"),
        ("1996", "2026"),
    )
    for first, last in windows:
        estimate = estimate_idiosyncratic_volatility(
            panel, label=f"{first}-{last}", first_year=first, last_year=last
        )
        print(
            f"{estimate.label:22s} {estimate.industries:3d} "
            f"{estimate.common_volatility:9.1%} {estimate.idiosyncratic_volatility:8.1%} "
            f"{estimate.slope_t_statistic:6.2f} {estimate.r_squared:6.2f}"
        )
    small, large = size_split(panel, first_year="1996", last_year="2026")
    for label, columns in (("1996-2026 small half", small), ("1996-2026 large half", large)):
        estimate = estimate_idiosyncratic_volatility(
            panel, label=label, first_year="1996", last_year="2026", columns=columns
        )
        print(
            f"{estimate.label:22s} {estimate.industries:3d} "
            f"{estimate.common_volatility:9.1%} {estimate.idiosyncratic_volatility:8.1%} "
            f"{estimate.slope_t_statistic:6.2f} {estimate.r_squared:6.2f}"
        )

    print("\n== 2. How often a lot is more than 5% below cost, 1996-2026 ==")
    print(f"{'horizon':>8s} {'position':>10s} {'market':>8s} {'depth':>8s}")
    for frequency in below_cost_frequency(panel, first_year="1996", last_year="2026"):
        print(
            f"{frequency.horizon_months:6d}m {frequency.position_share:10.1%} "
            f"{frequency.market_share:8.1%} {frequency.position_mean_depth:8.1%}"
        )

    print("\n== 3. The rule on the real panel ==")
    run = run_rule_on_panel(panel, first_year="1996", last_year="2026")
    print(f"window {run.first_period}..{run.last_period}")
    print(f"tracking error vs never selling: {run.tracking_error:.2%}/yr (a ceiling)")
    print(f"log return gap: {run.log_return_gap:+.3%}/yr (one path, not a result)")

    print("\n== 4. The modelled decay curve, % of account harvested ==")
    for contribution, label in ((0.0, "no contributions"), (0.10, "10%/yr contributions")):
        modelled = simulate_harvest_yield(
            baseline_market(), baseline_rule(contribution_rate=contribution)
        )
        curve = modelled.decay_curve()
        picks = [0, 1, 2, 4, 9, 19, 29]
        body = "  ".join(f"y{p + 1}={curve[p]:.1%}" for p in picks)
        print(f"{label:22s} {body}")
    fund_level = simulate_harvest_yield(
        MarketAssumptions(0.07, 0.158, 0.0, 0.015), baseline_rule(contribution_rate=0.10)
    )
    curve = fund_level.decay_curve()
    body = "  ".join(f"y{p + 1}={curve[p]:.1%}" for p in [0, 1, 2, 4, 9, 19, 29])
    print(f"{'fund level (one fund)':22s} {body}")

    print("\n== 5. Benefit in bp/yr, $1m taxable account, 9 bp fee ==")
    modelled = simulate_harvest_yield(baseline_market(), baseline_rule())
    grid = benefit_grid(modelled, account_value=1_000_000.0, gain_fractions=(0.0, 0.01, 0.03, 0.05))
    print(f"{'bracket':14s} {'disposal':10s} {'gains':>6s} {'p10':>8s} {'median':>8s} {'p90':>8s}")
    for (label, exit_name, gain), (low, mid, high) in grid.items():
        if exit_name == Disposal.GIFT.value:
            continue
        print(f"{label:14s} {exit_name:10s} {gain:6.0%} {low:8.1f} {mid:8.1f} {high:8.1f}")

    print("\n== 6. Break-even offsetting long-term gain, % of account per year ==")
    for regime, wage_rate, label in BRACKETS:
        crossings: list[str] = []
        for exit_path in (Disposal.LIQUIDATE, Disposal.STEP_UP):
            found = break_even_gain_fraction(
                modelled,
                regime=regime,
                wage_rate=wage_rate,
                disposal=exit_path,
                account_value=1_000_000.0,
            )
            crossings.append("none below 40%" if found is None else f"{found:.2%}")
        print(f"{label:14s} liquidate {crossings[0]:>16s}   step-up {crossings[1]:>16s}")

    print("\n== 7. The $3,000 ceiling, first year, by account size ==")
    for size in (100_000.0, 250_000.0, 1_000_000.0, 3_000_000.0):
        cells = [
            f"{label}: "
            f"{ordinary_offset_ceiling_bp(account_value=size, marginal_ordinary_rate=w):5.1f} bp"
            for _, w, label in BRACKETS
        ]
        print(f"${size:>11,.0f}  " + "  ".join(cells))

    print("\n== 8. Fee sensitivity, top bracket, step-up, $1m ==")
    for fee in (0.0, 0.0009, 0.0012, 0.0020, 0.0040):
        cells = []
        for gain in (0.0, 0.03):
            usage = LossUsage(
                account_value=1_000_000.0,
                annual_long_term_gain_fraction=gain,
                marginal_ordinary_rate_on_wages=0.37,
            )
            value = value_harvesting(
                modelled,
                regime=TOP_BRACKET,
                usage=usage,
                disposal=Disposal.STEP_UP,
                direct_index_fee=fee,
                replaced_fund_cost=VTI_NET_COST,
            )
            cells.append(f"{gain:.0%} gains {value.median_bp:7.1f} bp")
        print(f"fee {fee * 1e4:5.0f} bp  " + "   ".join(cells))

    print("\n== 9. Fund-level harvesting, no fee, same valuation ==")
    fund_paths = simulate_harvest_yield(
        MarketAssumptions(0.07, 0.158, 0.0, 0.015), baseline_rule()
    )
    for regime, wage_rate, label in BRACKETS:
        cells = []
        for exit_path in (Disposal.LIQUIDATE, Disposal.STEP_UP):
            for gain in (0.0, 0.03):
                usage = LossUsage(
                    account_value=1_000_000.0,
                    annual_long_term_gain_fraction=gain,
                    marginal_ordinary_rate_on_wages=wage_rate,
                )
                value = value_harvesting(
                    fund_paths,
                    regime=regime,
                    usage=usage,
                    disposal=exit_path,
                    direct_index_fee=0.0,
                    replaced_fund_cost=0.0,
                )
                cells.append(f"{exit_path.value[:4]} {gain:.0%} {value.median_bp:6.2f}")
        print(f"{label:14s} " + "  ".join(cells))

    print("\n== 10. Where in the distribution the benefit falls ==")
    for gain in (0.0, 0.03):
        usage = LossUsage(
            account_value=1_000_000.0,
            annual_long_term_gain_fraction=gain,
            marginal_ordinary_rate_on_wages=0.37,
        )
        value = value_harvesting(
            modelled,
            regime=TOP_BRACKET,
            usage=usage,
            disposal=Disposal.STEP_UP,
            direct_index_fee=FREC_FEE,
            replaced_fund_cost=VTI_NET_COST,
        )
        correlation = float(
            np.corrcoef(value.benefit_bp, np.log(modelled.terminal_value))[0, 1]
        )
        print(
            f"{gain:.0%} offsetting gains: median {value.median_bp:6.1f} bp, "
            f"P(negative) {value.probability_negative:.0%}, "
            f"corr(benefit, log terminal wealth) {correlation:+.2f}, "
            f"usable share of harvested loss {value.usable_share:.1%}"
        )
    held_embedded = 1.0 - modelled.terminal_basis_held / modelled.terminal_value
    print(
        f"\nmedian embedded gain at 30 years: "
        f"{float(np.median(modelled.embedded_gain_fraction)):.1%} of the account, against "
        f"{float(np.median(held_embedded)):.1%} for the same account never selling"
    )

    print("\n== 11. Direct indexing against fund-level harvesting ==")
    print("median bp/yr, $1m account, top bracket")
    for gain in (0.0, 0.01, 0.03, 0.05):
        cells = []
        for exit_path in (Disposal.STEP_UP, Disposal.LIQUIDATE):
            direct = _median(
                modelled, TOP_BRACKET, 0.37, gain, exit_path, FREC_FEE, VTI_NET_COST, 0.0004
            )
            at_fund = _median(
                fund_paths, TOP_BRACKET, 0.37, gain, exit_path, 0.0, 0.0, FUND_SWAP_COST
            )
            cells.append(f"{exit_path.value[:4]}: fund {at_fund:6.2f} direct {direct:6.2f}")
        print(f"gains {gain:4.0%}  " + "   ".join(cells))
    print("\noffsetting gain at which direct indexing overtakes fund-level harvesting")
    for regime, wage_rate, label in BRACKETS:
        for exit_path in (Disposal.STEP_UP, Disposal.LIQUIDATE):
            crossing = _crossover(modelled, fund_paths, regime, wage_rate, exit_path)
            print(f"{label:14s} {exit_path.value:10s} {crossing}")

    print("\n== 12. What it costs to leave, and what active risk it adds ==")
    embedded = float(np.median(modelled.embedded_gain_fraction))
    for regime, _, label in BRACKETS:
        cost = lock_in_exit_cost_bp(
            embedded_gain_fraction=embedded, regime=regime, remaining_years=10
        )
        print(
            f"{label:14s} abandoning a {embedded:.1%}-embedded account "
            f"with 10 years left: {cost:5.0f} bp/yr"
        )
    for share, names, rho in ((0.10, 50.0, 0.70), (0.30, 150.0, 0.50)):
        risk = active_risk_from_substitution(
            annual_idiosyncratic_volatility=0.35,
            substituted_fraction=share,
            substitute_positions=names,
            substitute_correlation=rho,
        )
        print(
            f"{share:.0%} in substitutes across {names:.0f} names "
            f"at rho={rho}: {risk:.2%}/yr"
        )


if __name__ == "__main__":  # pragma: no cover
    main()
