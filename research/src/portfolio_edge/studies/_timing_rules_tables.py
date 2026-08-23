"""Regenerates every table in ``docs/research/timing-rules-on-the-equity-sleeve.md``.

Kept separate from :mod:`portfolio_edge.studies.timing_rules` so the study stays pure and
testable and only this file touches the cache. Run it with::

    uv run python -m portfolio_edge.studies.timing_rules

**Everything here is `exploratory`.** No specification was frozen before these numbers
were seen and no experiment is registered, so nothing below may support a promoted claim.
What it can do — and the reason it exists — is show whether the rule clears its own
detection floor and survives the deflation that the published versions of this backtest
omit.

The panels, and what each is for
--------------------------------
* **US, Ken French** ``Mkt-RF + RF``, 1926-07 onward. True month-end value-weighted total
  returns with a matching bill leg from the same file. The headline panel.
* **US, Shiller**, 1871-01 onward. Longer, and **not comparable**: Shiller's ``P`` is the
  monthly *average* of daily closes. Averaging induces positive autocorrelation, which
  flatters a moving-average rule mechanically. The overlap with French measures how much.
* **Developed ex-US and Emerging, Ken French**, 1990-07 and 1989-07 onward. Out of sample
  in both region and era.
* **Sixteen countries, Jorda-Schularick-Taylor**, annual, 1870-2020. Annual resolution
  cannot carry a ten-month average, so the rule there is one-year absolute momentum
  against the country's own bill rate. It is the broadest out-of-sample evidence held.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from portfolio_edge.core._types import FloatArray
from portfolio_edge.data import aqr, french, macrohistory, shiller
from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.table import ParsedTable
from portfolio_edge.inference.bootstrap import optimal_block_length, stationary_bootstrap_indices
from portfolio_edge.inference.deflated_sharpe import (
    deflated_sharpe_ratio,
    effective_number_of_trials,
    mean_off_diagonal_correlation,
    trial_dispersion_from_sharpes,
)
from portfolio_edge.inference.hac import hac_mean, hac_ols
from portfolio_edge.inference.multiple_testing import reality_check, spa_test
from portfolio_edge.studies.timing_rules import (
    MONTHS_PER_YEAR,
    Disposal,
    RuleKind,
    TaxableAssumptions,
    TimingRuleSpec,
    episode_ledger,
    in_market,
    levels_from_returns,
    matched_exposure_active_returns,
    out_of_market_episodes,
    relative_drawdown,
    rule_excess_returns,
    rule_grid,
    sheltered_path,
    summarise,
    switch_count,
    taxable_path,
    time_in_market,
)

SEED = 20260822
"""One seed for every bootstrap here, declared so the tables reproduce."""

ONE_WAY_COST = 0.0010
"""10 bp one way — 20 bp a round trip — on a broad US equity ETF.

Declared, not measured. It is generous against a modern ETF (a penny spread on a $600
share is under 1 bp, and commissions are zero) and hopelessly optimistic before May 1975,
when US commissions were fixed by the exchange and no index fund existed to trade. The
sensitivity grid runs 0, 10 and 50 bp so a reader can see how little of the answer the
cost assumption carries.
"""

COST_GRID = (0.0, 0.0005, 0.0010, 0.0050)

HEADLINE = TimingRuleSpec(kind=RuleKind.SMA, lookback=10)
MOMENTUM = TimingRuleSpec(kind=RuleKind.ABSOLUTE_MOMENTUM, lookback=12)


@dataclass(frozen=True)
class Panel:
    """One aligned equity/bill panel."""

    label: str
    periods: tuple[str, ...]
    excess: FloatArray
    cash: FloatArray

    @property
    def total(self) -> FloatArray:
        return self.excess + self.cash

    def window(self, first: str | None = None, last: str | None = None) -> Panel:
        keep = [
            index
            for index, period in enumerate(self.periods)
            if (first is None or period >= first) and (last is None or period <= last)
        ]
        if not keep:
            raise ValueError(f"{self.label}: no months in [{first}, {last}]")
        return Panel(
            label=f"{self.label} {first or self.periods[0]}..{last or self.periods[-1]}",
            periods=tuple(self.periods[index] for index in keep),
            excess=self.excess[keep],
            cash=self.cash[keep],
        )


def _cache() -> RawCache:
    return RawCache()


def _french_table(dataset_id: str, table_id: str = "monthly") -> ParsedTable:
    cache = _cache()
    dataset = french.get_dataset(dataset_id)
    entry = cache.require(dataset.url)
    return french.parse(cache, entry, dataset=dataset).table(table_id)


def _french_panel(dataset_id: str, label: str) -> Panel:
    table = _french_table(dataset_id)
    market = table.column("Mkt-RF")
    bill = table.column("RF")
    periods, excess, cash = [], [], []
    for period, mkt, rf in zip(table.periods, market, bill, strict=True):
        if mkt is None or rf is None:
            continue
        periods.append(period)
        excess.append(float(mkt))
        cash.append(float(rf))
    return Panel(
        label=label,
        periods=tuple(periods),
        excess=np.asarray(excess, dtype=np.float64),
        cash=np.asarray(cash, dtype=np.float64),
    )


def _shiller_panel() -> Panel:
    """US monthly nominal total return from Shiller, with the JST US bill rate as cash.

    The nominal total-return index is ``Real_Total_Return_Price * CPI``: Shiller publishes
    the real wealth index and the price index it was deflated by, so multiplying recovers
    the nominal one exactly. The bill leg is the Jorda-Schularick-Taylor US annual bill
    rate spread evenly across the year, which is a **splice** and is why this panel is
    used for one comparison only.
    """
    cache = _cache()
    dataset = shiller.get_dataset("shiller_ie_data")
    table = shiller.parse(cache, cache.require(dataset.url), dataset=dataset).table
    real_tr = table.column("Real_Total_Return_Price")
    cpi = table.column("CPI")
    levels: dict[str, float] = {}
    for period, value, price_index in zip(table.periods, real_tr, cpi, strict=True):
        if value is None or price_index is None:
            continue
        levels[period] = float(value) * float(price_index)

    jst = macrohistory.get_dataset("jst_macrohistory_r6")
    jst_file = macrohistory.parse(cache, cache.require(jst.url), dataset=jst)
    bills = jst_file.table("bill_rate")
    annual = {
        period: float(value)
        for period, value in zip(bills.periods, bills.column("USA"), strict=True)
        if value is not None
    }

    periods = sorted(levels)
    out_periods, excess, cash = [], [], []
    for previous, current in itertools.pairwise(periods):
        year = current[:4]
        if year not in annual:
            continue
        monthly_bill = (1.0 + annual[year]) ** (1.0 / MONTHS_PER_YEAR) - 1.0
        total = levels[current] / levels[previous] - 1.0
        out_periods.append(current)
        excess.append(total - monthly_bill)
        cash.append(monthly_bill)
    return Panel(
        label="US Shiller (averaged prices)",
        periods=tuple(out_periods),
        excess=np.asarray(excess, dtype=np.float64),
        cash=np.asarray(cash, dtype=np.float64),
    )


def _aqr_tsmom() -> Mapping[str, Mapping[str, float]]:
    cache = _cache()
    dataset = aqr.get_dataset("aqr_tsmom_factors")
    table = aqr.parse(cache, cache.require(dataset.url), dataset=dataset).table
    out: dict[str, dict[str, float]] = {}
    for column in ("TSMOM", "TSMOM^EQ"):
        values = table.column(column)
        out[column] = {
            period: float(value)
            for period, value in zip(table.periods, values, strict=True)
            if value is not None
        }
    return out


def positions(panel: Panel, spec: TimingRuleSpec, *, absolute_vs_cash: bool = True) -> FloatArray:
    """The rule's monthly position on ``panel``."""
    levels = levels_from_returns(panel.total)
    if spec.kind is RuleKind.ABSOLUTE_MOMENTUM and absolute_vs_cash:
        return in_market(
            levels, spec=spec, benchmark_levels=levels_from_returns(panel.cash)
        )
    return in_market(levels, spec=spec)


def _annualise(monthly_mean: float) -> float:
    return monthly_mean * MONTHS_PER_YEAR


def _mde80(standard_error_monthly: float) -> float:
    """Smallest annualised mean detectable at 80% power and 5% two-sided, in pp/yr."""
    return (1.959963985 + 0.8416212336) * standard_error_monthly * MONTHS_PER_YEAR * 100.0


def _fmt(value: float, places: int = 2) -> str:
    return "nan" if not math.isfinite(value) else f"{value:.{places}f}"


def _row(cells: Sequence[str]) -> str:
    return "| " + " | ".join(cells) + " |"


# --------------------------------------------------------------------------------------
# 1. What the rule does
# --------------------------------------------------------------------------------------


def _headline(panel: Panel, specs: Sequence[TimingRuleSpec], cost: float = ONE_WAY_COST) -> None:
    print(f"\n### Headline — {panel.label}, {panel.periods[0]}..{panel.periods[-1]}, "
          f"{panel.excess.size} months, one-way cost {cost * 1e4:.0f} bp")
    print(_row(["rule", "months", "in mkt", "switch/decade", "geo total", "vol",
                "Sharpe", "max DD", "under water", "worst 12m"]))
    print(_row(["---"] * 10))

    buy_hold = summarise(panel.excess, cash=panel.cash, label="buy and hold 100%")
    for spec in specs:
        position = positions(panel, spec)
        rule = rule_excess_returns(panel.excess, position=position, one_way_cost=cost)
        live = np.isfinite(rule)
        summary = summarise(rule[live], cash=panel.cash[live], label=spec.label)
        exposure = time_in_market(position)
        switches = switch_count(position)
        decades = int(np.count_nonzero(live)) / (MONTHS_PER_YEAR * 10.0)
        print(_row([
            spec.label, str(summary.months), _fmt(exposure, 3), _fmt(switches / decades, 1),
            _fmt(summary.geometric_total * 100.0), _fmt(summary.volatility * 100.0),
            _fmt(summary.sharpe, 3), _fmt(summary.max_drawdown * 100.0),
            str(summary.max_time_under_water), _fmt(summary.worst_twelve_months * 100.0),
        ]))
        matched_position = np.full_like(position, np.nan)
        matched_position[live] = exposure
        matched = rule_excess_returns(panel.excess, position=matched_position, one_way_cost=0.0)
        matched_summary = summarise(
            matched[live], cash=panel.cash[live], label=f"matched {exposure:.3f}"
        )
        print(_row([
            f"— control at {exposure:.3f} beta", str(matched_summary.months), _fmt(exposure, 3),
            "0.0", _fmt(matched_summary.geometric_total * 100.0),
            _fmt(matched_summary.volatility * 100.0), _fmt(matched_summary.sharpe, 3),
            _fmt(matched_summary.max_drawdown * 100.0), str(matched_summary.max_time_under_water),
            _fmt(matched_summary.worst_twelve_months * 100.0),
        ]))
    print(_row([
        "buy and hold 100%", str(buy_hold.months), "1.000", "0.0",
        _fmt(buy_hold.geometric_total * 100.0), _fmt(buy_hold.volatility * 100.0),
        _fmt(buy_hold.sharpe, 3), _fmt(buy_hold.max_drawdown * 100.0),
        str(buy_hold.max_time_under_water), _fmt(buy_hold.worst_twelve_months * 100.0),
    ]))


def _active(panel: Panel, spec: TimingRuleSpec, cost: float = ONE_WAY_COST) -> FloatArray:
    position = positions(panel, spec)
    return matched_exposure_active_returns(panel.excess, position=position, one_way_cost=cost)


def _gap_table(panel: Panel, specs: Sequence[TimingRuleSpec], cost: float = ONE_WAY_COST) -> None:
    print(f"\n### Beta-matched gap — {panel.label}, one-way cost {cost * 1e4:.0f} bp")
    print(_row(["rule", "months", "gap pp/yr", "HAC t", "95% HAC", "MDE80 pp/yr",
                "block b", "block 95%"]))
    print(_row(["---"] * 8))
    rng = np.random.default_rng(SEED)
    for spec in specs:
        active = _active(panel, spec, cost)
        series = active[np.isfinite(active)]
        result = hac_mean(series)
        gap = _annualise(result.mean) * 100.0
        half = 1.959963985 * result.standard_error * MONTHS_PER_YEAR * 100.0
        block = optimal_block_length(series).stationary
        indices = stationary_bootstrap_indices(series.size, block, 5000, rng)
        draws = np.sort(series[indices].mean(axis=1)) * MONTHS_PER_YEAR * 100.0
        low, high = float(draws[124]), float(draws[4874])
        print(_row([
            spec.label, str(series.size), _fmt(gap), _fmt(result.t_statistic),
            f"[{_fmt(gap - half)}, {_fmt(gap + half)}]",
            _fmt(_mde80(result.standard_error)), _fmt(block, 1), f"[{_fmt(low)}, {_fmt(high)}]",
        ]))


def _subperiods(panel: Panel, spec: TimingRuleSpec, splits: Sequence[tuple[str, str, str]]) -> None:
    print(f"\n### Subperiods — {spec.label} on {panel.label}, one-way cost "
          f"{ONE_WAY_COST * 1e4:.0f} bp")
    print(_row(["window", "months", "in mkt", "gap pp/yr", "HAC t", "MDE80", "rule geo",
                "control geo", "rule maxDD", "control maxDD"]))
    print(_row(["---"] * 10))
    position = positions(panel, spec)
    rule = rule_excess_returns(panel.excess, position=position, one_way_cost=ONE_WAY_COST)
    for label, first, last in splits:
        mask = np.array(
            [first <= period <= last for period in panel.periods], dtype=bool
        ) & np.isfinite(rule)
        if int(mask.sum()) < 24:
            continue
        exposure = float(np.mean(position[mask]))
        active = rule[mask] - exposure * panel.excess[mask]
        result = hac_mean(active)
        rule_summary = summarise(rule[mask], cash=panel.cash[mask], label=label)
        control_summary = summarise(
            exposure * panel.excess[mask], cash=panel.cash[mask], label=label
        )
        print(_row([
            label, str(int(mask.sum())), _fmt(exposure, 3),
            _fmt(_annualise(result.mean) * 100.0), _fmt(result.t_statistic),
            _fmt(_mde80(result.standard_error)),
            _fmt(rule_summary.geometric_total * 100.0),
            _fmt(control_summary.geometric_total * 100.0),
            _fmt(rule_summary.max_drawdown * 100.0),
            _fmt(control_summary.max_drawdown * 100.0),
        ]))


def _behaviour(panel: Panel, spec: TimingRuleSpec) -> None:
    print(f"\n### Whipsaw and holdability — {spec.label} on {panel.label}")
    position = positions(panel, spec)
    episodes = out_of_market_episodes(
        panel.excess, position=position, one_way_cost=ONE_WAY_COST
    )
    ledger = episode_ledger(episodes)
    first, last = ledger.worst_losing_run_span
    print(f"exits: {ledger.episodes}; helped {ledger.helped}; hurt {ledger.hurt} "
          f"({ledger.hurt / ledger.episodes:.1%})")
    print(f"median exit length: {ledger.median_episode_months:.1f} months")
    print(f"sum of exit gains against staying fully invested: {ledger.total_avoided:+.4f} "
          f"= {ledger.best_three_total:+.4f} from the best three exits "
          f"{ledger.remainder_total:+.4f} from the other {ledger.episodes - 3}")
    print(f"worst run of consecutive losing exits: {ledger.worst_losing_run} exits, "
          f"costing {ledger.worst_losing_run_cost:.4f}, "
          f"{panel.periods[first]}..{panel.periods[last]}")
    best = sorted(episodes, key=lambda item: item.avoided, reverse=True)[:5]
    print("five best exits:")
    for episode in best:
        print(f"  {panel.periods[episode.start]}..{panel.periods[episode.end]} "
              f"({episode.months} mo): {episode.avoided:+.4f}")
    worst = sorted(episodes, key=lambda item: item.avoided)[:5]
    print("five worst exits:")
    for episode in worst:
        print(f"  {panel.periods[episode.start]}..{panel.periods[episode.end]} "
              f"({episode.months} mo): {episode.avoided:+.4f}")

    rule = rule_excess_returns(panel.excess, position=position, one_way_cost=ONE_WAY_COST)
    live = np.isfinite(rule)
    exposure = time_in_market(position)
    matched = np.full_like(rule, np.nan)
    matched[live] = exposure * panel.excess[live]
    full = np.full_like(rule, np.nan)
    full[live] = panel.excess[live]
    months = [period for period, flag in zip(panel.periods, live, strict=True) if flag]
    for name, control in (
        ("the beta-matched control", matched),
        ("buy-and-hold 100%", full),
    ):
        result = relative_drawdown(rule, control_excess=control, cash=panel.cash)
        print(f"relative drawdown vs {name}: {result.max_shortfall:.1%}, "
              f"{result.max_months_behind} months behind, from a high at "
              f"{months[result.peak_index]} to a low at {months[result.trough_index]}; "
              f"still {result.final_months_behind} months below its best at the end")


# --------------------------------------------------------------------------------------
# 2. Deflation
# --------------------------------------------------------------------------------------


def _grid_matrix(panel: Panel, cost: float, specs: Sequence[TimingRuleSpec]) -> tuple[
    FloatArray, FloatArray, list[str]
]:
    """Rule excess returns and beta-matched active returns over the common months."""
    burn = max(spec.burn_in for spec in specs)
    rules, actives, labels = [], [], []
    for spec in specs:
        position = positions(panel, spec)
        rule = rule_excess_returns(panel.excess, position=position, one_way_cost=cost)
        exposure = float(np.mean(position[burn:]))
        rules.append(rule[burn:])
        actives.append(rule[burn:] - exposure * panel.excess[burn:])
        labels.append(spec.label)
    return (
        np.column_stack(rules),
        np.column_stack(actives),
        labels,
    )


def _deflate(panel: Panel, cost: float = ONE_WAY_COST) -> None:
    specs = rule_grid()
    rule_matrix, active_matrix, labels = _grid_matrix(panel, cost, specs)
    months = rule_matrix.shape[0]
    print(f"\n### Deflation — {panel.label}, {len(specs)} declared rules, "
          f"{months} common months, one-way cost {cost * 1e4:.0f} bp")

    monthly_sharpes = rule_matrix.mean(axis=0) / rule_matrix.std(axis=0, ddof=1)
    dispersion = trial_dispersion_from_sharpes(monthly_sharpes)
    import warnings

    from portfolio_edge.inference.deflated_sharpe import LinearDependenceWarning

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", LinearDependenceWarning)
        rho_bar = mean_off_diagonal_correlation(rule_matrix)
        rho_active = mean_off_diagonal_correlation(active_matrix)
    effective = effective_number_of_trials(len(specs), rho_bar)
    print(f"trial Sharpe dispersion (monthly): {dispersion:.5f}")
    print(f"mean off-diagonal correlation of the rules: {rho_bar:.4f} "
          f"-> effective independent trials {effective:.2f} of {len(specs)}")
    print(f"mean off-diagonal correlation of the ACTIVE returns: {rho_active:.4f}")

    order = np.argsort(monthly_sharpes)[::-1]
    print("\nbest five rules by in-sample Sharpe (annualised):")
    for index in order[:5]:
        print(f"  {labels[index]}: {monthly_sharpes[index] * math.sqrt(12):.3f}")
    print("worst five:")
    for index in order[-5:]:
        print(f"  {labels[index]}: {monthly_sharpes[index] * math.sqrt(12):.3f}")

    headline_index = labels.index(HEADLINE.label)
    momentum_index = labels.index(MOMENTUM.label)
    best_index = int(order[0])
    print()
    print(_row(["candidate", "SR ann.", "N trials", "E[max Z]", "SR* ann.", "DSR"]))
    print(_row(["---"] * 6))
    for name, index in (
        (f"{HEADLINE.label} (the rule asked about)", headline_index),
        (f"{MOMENTUM.label}", momentum_index),
        (f"best in grid: {labels[best_index]}", best_index),
    ):
        series = rule_matrix[:, index]
        centred = series - series.mean()
        variance = float(np.mean(centred**2))
        skew = float(np.mean(centred**3) / variance**1.5)
        kurt = float(np.mean(centred**4) / variance**2)
        for trials in (effective, 100.0, 1000.0, 10000.0):
            result = deflated_sharpe_ratio(
                float(monthly_sharpes[index]),
                trial_dispersion=dispersion,
                n_trials=trials,
                n_observations=months,
                skewness=skew,
                kurtosis=kurt,
            )
            print(_row([
                name if trials == effective else "",
                _fmt(monthly_sharpes[index] * math.sqrt(12), 3),
                _fmt(trials, 1), _fmt(result.expected_max_z, 3),
                _fmt(result.sharpe_threshold * math.sqrt(12), 3),
                _fmt(result.deflated_significance, 4),
            ]))

    active_sharpes = active_matrix.mean(axis=0) / active_matrix.std(axis=0, ddof=1)
    active_dispersion = trial_dispersion_from_sharpes(active_sharpes)
    active_effective = effective_number_of_trials(len(specs), rho_active)
    best_active = int(np.argmax(active_sharpes))
    print("\n**The deflation that answers the question** — same arithmetic on the "
          "beta-matched ACTIVE return, which is the only series with the equity premium "
          "taken out of it.")
    print(_row(["candidate", "active SR ann.", "N trials", "SR* ann.", "DSR"]))
    print(_row(["---"] * 5))
    for name, index in (
        (f"{HEADLINE.label}", headline_index),
        (f"{MOMENTUM.label}", momentum_index),
        (f"best in grid: {labels[best_active]}", best_active),
    ):
        series = active_matrix[:, index]
        centred = series - series.mean()
        variance = float(np.mean(centred**2))
        skew = float(np.mean(centred**3) / variance**1.5)
        kurt = float(np.mean(centred**4) / variance**2)
        for trials in (active_effective, 100.0, 1000.0, 10000.0):
            result = deflated_sharpe_ratio(
                float(active_sharpes[index]),
                trial_dispersion=active_dispersion,
                n_trials=trials,
                n_observations=months,
                skewness=skew,
                kurtosis=kurt,
            )
            print(_row([
                name if trials == active_effective else "",
                _fmt(active_sharpes[index] * math.sqrt(12), 3),
                _fmt(trials, 1),
                _fmt(result.sharpe_threshold * math.sqrt(12), 3),
                _fmt(result.deflated_significance, 4),
            ]))
    print(f"active trial Sharpe dispersion (monthly): {active_dispersion:.5f}; "
          f"effective independent trials {active_effective:.2f} of {len(specs)}")

    rng = np.random.default_rng(SEED)
    for name, matrix in (("rule less bills", rule_matrix), ("rule less beta-matched control",
                                                            active_matrix)):
        white = reality_check(matrix, rng=np.random.default_rng(SEED), n_resamples=2000)
        hansen = spa_test(matrix, rng=rng, n_resamples=2000)
        print(f"\n{name}: White reality-check p = {white.p_value:.4f} "
              f"(best {labels[white.best_index]}); Hansen SPA_c p = {hansen.p_value:.4f} "
              f"(best {labels[hansen.best_index]})")


# --------------------------------------------------------------------------------------
# 3. Taxes
# --------------------------------------------------------------------------------------


def _tax(panel: Panel, spec: TimingRuleSpec, *, dividend_yield: float, years_label: str) -> None:
    from portfolio_edge.studies.tax_structure import TOP_BRACKET, UPPER_MIDDLE_BRACKET

    position = positions(panel, spec)
    live = np.isfinite(position)
    exposure = time_in_market(position)
    total = panel.total
    buy_hold = np.where(live, 1.0, np.nan)
    matched = np.where(live, exposure, np.nan)

    print(f"\n### After tax — {spec.label} on {panel.label} ({years_label}), "
          f"dividend yield {dividend_yield:.2%}, one-way cost {ONE_WAY_COST * 1e4:.0f} bp")
    print(_row(["account", "portfolio", "terminal $1", "tax paid", "growth %/yr",
                "vs buy-hold pp/yr", "ST gain", "LT gain", "unused loss"]))
    print(_row(["---"] * 9))

    sheltered_hold = sheltered_path(
        label="buy and hold", position=buy_hold, risky_total=total, cash=panel.cash,
        one_way_cost=ONE_WAY_COST,
    )
    arms: tuple[tuple[str, FloatArray, float], ...] = (
        ("timing rule", position, 0.0),
        ("static blend, monthly rebalanced", matched, 0.0),
        ("static blend, never rebalanced", matched, 1.0),
        ("buy and hold 100%", buy_hold, 0.0),
    )
    for name, weights, band in arms:
        outcome = sheltered_path(
            label=name, position=weights, risky_total=total, cash=panel.cash,
            one_way_cost=ONE_WAY_COST, rebalance_band=band,
        )
        print(_row([
            "Roth / traditional", name, _fmt(outcome.terminal_after_disposal, 2), "0.00",
            _fmt(outcome.annualised_after_tax_growth * 100.0),
            _fmt((outcome.annualised_after_tax_growth - sheltered_hold.annualised_after_tax_growth)
                 * 100.0),
            "—", "—", "—",
        ]))

    for regime in (TOP_BRACKET, UPPER_MIDDLE_BRACKET):
        assumptions = TaxableAssumptions(
            ordinary_rate=regime.ordinary,
            long_term_rate=regime.capital_gain,
            dividend_yield=dividend_yield,
        )
        for disposal in (Disposal.STEP_UP, Disposal.LIQUIDATE):
            reference = taxable_path(
                label="buy and hold", position=buy_hold, risky_total=total, cash=panel.cash,
                assumptions=assumptions, one_way_cost=ONE_WAY_COST, disposal=disposal,
            )
            for name, weights, band in arms:
                outcome = taxable_path(
                    label=name, position=weights, risky_total=total, cash=panel.cash,
                    assumptions=assumptions, one_way_cost=ONE_WAY_COST, disposal=disposal,
                    rebalance_band=band,
                )
                print(_row([
                    f"taxable {regime.label.split()[1]} {disposal.value}", name,
                    _fmt(outcome.terminal_after_disposal, 2), _fmt(outcome.cumulative_tax, 2),
                    _fmt(outcome.annualised_after_tax_growth * 100.0),
                    _fmt((outcome.annualised_after_tax_growth
                          - reference.annualised_after_tax_growth) * 100.0),
                    _fmt(outcome.realised_short_term_gain, 2),
                    _fmt(outcome.realised_long_term_gain, 2),
                    _fmt(outcome.unused_loss_carryforward, 3),
                ]))


# --------------------------------------------------------------------------------------
# 4. Overlap with the managed-futures overlay already held
# --------------------------------------------------------------------------------------


def _overlap(panel: Panel, spec: TimingRuleSpec) -> None:
    series = _aqr_tsmom()
    position = positions(panel, spec)
    active = matched_exposure_active_returns(
        panel.excess, position=position, one_way_cost=ONE_WAY_COST
    )
    print(f"\n### Overlap — {spec.label}'s active return against AQR TSMOM")
    print(_row(["trend series", "months", "corr", "beta", "HAC t on beta", "R2",
                "alpha pp/yr", "HAC t on alpha"]))
    print(_row(["---"] * 8))
    for name, values in series.items():
        rows = [
            (index, values[period])
            for index, period in enumerate(panel.periods)
            if period in values and np.isfinite(active[index])
        ]
        if len(rows) < 60:
            continue
        indices = [index for index, _ in rows]
        trend = np.asarray([value for _, value in rows], dtype=np.float64)
        left = active[indices]
        correlation = float(np.corrcoef(left, trend)[0, 1])
        fit = hac_ols(left, trend[:, None])
        total_sum = float(np.sum((left - left.mean()) ** 2))
        r_squared = 1.0 - float(np.sum(fit.residuals**2)) / total_sum
        print(_row([
            name, str(trend.size), _fmt(correlation, 3), _fmt(fit.coefficients[1], 3),
            _fmt(fit.t_statistics[1]), _fmt(r_squared, 3),
            _fmt(fit.coefficients[0] * MONTHS_PER_YEAR * 100.0),
            _fmt(fit.t_statistics[0]),
        ]))
    # And the reverse framing a reader will want: how much of the rule's active return is
    # left once the trend overlay is held.
    rows = [
        (index, series["TSMOM"][period])
        for index, period in enumerate(panel.periods)
        if period in series["TSMOM"] and np.isfinite(active[index])
    ]
    indices = [index for index, _ in rows]
    trend = np.asarray([value for _, value in rows], dtype=np.float64)
    left = active[indices]
    print(f"active return of the rule over these months: "
          f"{_annualise(float(left.mean())) * 100.0:.2f} pp/yr; "
          f"TSMOM over the same months: {_annualise(float(trend.mean())) * 100.0:.2f} pp/yr")


# --------------------------------------------------------------------------------------
# 5. The cheaper ways to buy the same thing
# --------------------------------------------------------------------------------------


def _alternatives(panel: Panel, spec: TimingRuleSpec) -> None:
    series = _aqr_tsmom()["TSMOM"]
    position = positions(panel, spec)
    live = np.isfinite(position)
    exposure = time_in_market(position)
    common = np.array(
        [live[index] and period in series for index, period in enumerate(panel.periods)],
        dtype=bool,
    )
    trend = np.asarray(
        [series[period] for index, period in enumerate(panel.periods) if common[index]],
        dtype=np.float64,
    )
    excess = panel.excess[common]
    cash = panel.cash[common]
    rule = rule_excess_returns(panel.excess, position=position, one_way_cost=ONE_WAY_COST)[common]

    print(f"\n### The same drawdown, bought four ways — {panel.periods[int(np.argmax(common))]}"
          f".. , {int(common.sum())} months")
    print(_row(["construction", "geo total", "vol", "Sharpe", "max DD", "under water",
                "worst 12m"]))
    print(_row(["---"] * 7))
    # The AQR series states no fee, transaction-cost, slippage or financing basis
    # anywhere, so an un-haircut trend row is not an investable comparator. The haircuts
    # are the ones this repository already carries: 7.7 pp/yr is the CTA survivorship and
    # backfill bound, and the third row scales the leg to the +2.84%/yr the 46 live
    # managed-futures funds actually paid over 2019-2025
    # (docs/research/live-managed-futures.md).
    live_mean = 0.0284 / MONTHS_PER_YEAR
    haircut_to_live = trend - float(trend.mean()) + live_mean
    candidates: list[tuple[str, FloatArray]] = [
        ("equity 100%", excess),
        (f"{spec.label} timing rule", rule),
        (f"static equity {exposure:.2f} + bills", exposure * excess),
        ("equity 100% + 30% TSMOM, vendor gross", excess + 0.30 * trend),
        (f"equity {exposure:.2f} + 30% TSMOM, vendor gross", exposure * excess + 0.30 * trend),
        (f"equity {exposure:.2f} + 30% TSMOM less 7.7 pp/yr",
         exposure * excess + 0.30 * (trend - 0.077 / MONTHS_PER_YEAR)),
        (f"equity {exposure:.2f} + 30% TSMOM at the live-fund mean",
         exposure * excess + 0.30 * haircut_to_live),
    ]
    for name, values in candidates:
        summary = summarise(values, cash=cash, label=name)
        print(_row([
            name, _fmt(summary.geometric_total * 100.0), _fmt(summary.volatility * 100.0),
            _fmt(summary.sharpe, 3), _fmt(summary.max_drawdown * 100.0),
            str(summary.max_time_under_water), _fmt(summary.worst_twelve_months * 100.0),
        ]))


# --------------------------------------------------------------------------------------
# 6. Out of sample
# --------------------------------------------------------------------------------------


def _jst_countries() -> None:
    cache = _cache()
    dataset = macrohistory.get_dataset("jst_macrohistory_r6")
    parsed = macrohistory.parse(cache, cache.require(dataset.url), dataset=dataset)
    equity = parsed.table("equity_total_return")
    bills = parsed.table("bill_rate")
    spec = TimingRuleSpec(kind=RuleKind.ABSOLUTE_MOMENTUM, lookback=1)

    print("\n### Out of sample — 1-year absolute momentum, 16 countries, JST annual "
          "1870-2020")
    print(_row(["country", "years", "in mkt", "gap pp/yr", "t", "rule geo", "control geo",
                "rule maxDD", "control maxDD"]))
    print(_row(["---"] * 9))
    gaps: list[float] = []
    deeper = 0
    year_map: list[dict[str, float]] = []
    for country in equity.columns:
        pairs = [
            (period, e, b)
            for period, e, b in zip(
                equity.periods, equity.column(country), bills.column(country), strict=True
            )
            if e is not None and b is not None
        ]
        if len(pairs) < 60:
            continue
        # Drop the German hyperinflation rows, whose ratio of two astronomical numbers is
        # not a return an investor could have realised. The source's own documentation
        # says so; see portfolio_edge.data.macrohistory.
        pairs = [row for row in pairs if not (country == "DEU" and "1922" <= row[0] <= "1923")]
        periods = tuple(row[0] for row in pairs)
        excess = np.asarray([row[1] - row[2] for row in pairs], dtype=np.float64)
        cash = np.asarray([row[2] for row in pairs], dtype=np.float64)
        panel = Panel(label=country, periods=periods, excess=excess, cash=cash)
        position = positions(panel, spec)
        rule = rule_excess_returns(excess, position=position, one_way_cost=0.0)
        live = np.isfinite(rule)
        exposure = float(np.mean(position[live]))
        active = rule[live] - exposure * excess[live]
        result = hac_mean(active)
        rule_summary = summarise(rule[live], cash=cash[live], label=country, periods_per_year=1)
        control_summary = summarise(
            exposure * excess[live], cash=cash[live], label=country, periods_per_year=1
        )
        gaps.append(float(result.mean))
        if rule_summary.max_drawdown < control_summary.max_drawdown:
            deeper += 1
        live_periods = [period for period, flag in zip(periods, live, strict=True) if flag]
        year_map.append(dict(zip(live_periods, active.tolist(), strict=True)))
        print(_row([
            country, str(int(live.sum())), _fmt(exposure, 3), _fmt(result.mean * 100.0),
            _fmt(result.t_statistic), _fmt(rule_summary.geometric_total * 100.0),
            _fmt(control_summary.geometric_total * 100.0),
            _fmt(rule_summary.max_drawdown * 100.0),
            _fmt(control_summary.max_drawdown * 100.0),
        ]))
    array = np.asarray(gaps, dtype=np.float64)
    print(f"countries: {array.size}; mean gap {array.mean() * 100.0:+.2f} pp/yr; "
          f"median {np.median(array) * 100.0:+.2f}; positive in "
          f"{int(np.count_nonzero(array > 0))} of {array.size}; "
          f"cross-country SD {array.std(ddof=1) * 100.0:.2f} pp/yr; "
          f"deeper max drawdown than its control in "
          f"{deeper} of {array.size} countries")
    # Countries are not independent draws — 1929 and 2008 are in every column — so the
    # cross-country standard error understates. Pool by year instead: the equal-weighted
    # active return across whichever countries are live that year, tested with HAC.
    years = sorted({period for periods in year_map for period in periods})
    pooled = []
    for year in years:
        values = [
            series[year] for series in year_map if year in series
        ]
        if len(values) >= 5:
            pooled.append(float(np.mean(values)))
    pooled_array = np.asarray(pooled, dtype=np.float64)
    result = hac_mean(pooled_array)
    print(f"pooled equal-weight active return across countries: {result.mean * 100.0:+.2f} "
          f"pp/yr over {pooled_array.size} years, HAC t {result.t_statistic:.2f}, "
          f"MDE80 {(1.959963985 + 0.8416212336) * result.standard_error * 100.0:.2f} pp/yr")


def _averaging_bias(french_panel: Panel, shiller_panel: Panel) -> None:
    first = max(french_panel.periods[0], shiller_panel.periods[0])
    last = min(french_panel.periods[-1], shiller_panel.periods[-1])
    print(f"\n### The averaged-price artefact — same rule, same months {first}..{last}")
    print(_row(["panel", "months", "AR(1) of monthly return", "in mkt", "gap pp/yr", "HAC t"]))
    print(_row(["---"] * 6))
    for panel in (french_panel.window(first, last), shiller_panel.window(first, last)):
        position = positions(panel, HEADLINE)
        rule = rule_excess_returns(
            panel.excess, position=position, one_way_cost=ONE_WAY_COST
        )
        live = np.isfinite(rule)
        exposure = float(np.mean(position[live]))
        active = rule[live] - exposure * panel.excess[live]
        result = hac_mean(active)
        ar1 = float(np.corrcoef(panel.excess[:-1], panel.excess[1:])[0, 1])
        print(_row([
            panel.label, str(int(live.sum())), _fmt(ar1, 3), _fmt(exposure, 3),
            _fmt(_annualise(result.mean) * 100.0), _fmt(result.t_statistic),
        ]))


def _cost_sensitivity(panel: Panel, spec: TimingRuleSpec) -> None:
    print(f"\n### Cost sensitivity — {spec.label} on {panel.label}")
    print(_row(["one-way cost", "gap pp/yr", "HAC t"]))
    print(_row(["---"] * 3))
    for cost in COST_GRID:
        active = _active(panel, spec, cost)
        series = active[np.isfinite(active)]
        result = hac_mean(series)
        print(_row([
            f"{cost * 1e4:.0f} bp", _fmt(_annualise(result.mean) * 100.0),
            _fmt(result.t_statistic),
        ]))


def _dual_momentum(us: Panel, exus: Panel) -> None:
    """Antonacci's Global Equities Momentum, on the two French regional files.

    Absolute momentum decides risk-on; relative momentum picks the leg. Both use the same
    twelve-month lookback, both are formed from month-end data before the month traded.
    """
    common = sorted(set(us.periods) & set(exus.periods))
    us_index = {period: index for index, period in enumerate(us.periods)}
    exus_index = {period: index for index, period in enumerate(exus.periods)}
    excess_us = np.asarray([us.excess[us_index[p]] for p in common], dtype=np.float64)
    excess_exus = np.asarray([exus.excess[exus_index[p]] for p in common], dtype=np.float64)
    cash = np.asarray([us.cash[us_index[p]] for p in common], dtype=np.float64)
    level_us = levels_from_returns(excess_us + cash)
    level_exus = levels_from_returns(excess_exus + cash)
    level_cash = levels_from_returns(cash)

    lookback = 12
    weights_us = np.full(len(common), np.nan)
    weights_exus = np.full(len(common), np.nan)
    for index in range(lookback + 1, len(common)):
        decision = index - 1
        us_growth = level_us[decision] / level_us[decision - lookback]
        exus_growth = level_exus[decision] / level_exus[decision - lookback]
        cash_growth = level_cash[decision] / level_cash[decision - lookback]
        if us_growth <= cash_growth:
            weights_us[index] = 0.0
            weights_exus[index] = 0.0
        elif us_growth >= exus_growth:
            weights_us[index] = 1.0
            weights_exus[index] = 0.0
        else:
            weights_us[index] = 0.0
            weights_exus[index] = 1.0

    live = np.isfinite(weights_us)
    turnover = np.abs(np.diff(weights_us[live])) + np.abs(np.diff(weights_exus[live]))
    rule = weights_us[live] * excess_us[live] + weights_exus[live] * excess_exus[live]
    rule[1:] -= ONE_WAY_COST * turnover
    exposure = float(np.mean(weights_us[live] + weights_exus[live]))
    print(f"\n### Dual momentum (GEM), US + developed ex-US, {common[0]}..{common[-1]}")
    equal = 0.5 * (excess_us[live] + excess_exus[live])
    for name, values in (
        ("GEM", rule),
        (f"static 50/50 at {exposure:.2f} beta", exposure * equal),
        ("static 50/50 fully invested", equal),
        ("US only, fully invested", excess_us[live]),
    ):
        summary = summarise(values, cash=cash[live], label=name)
        print(f"  {name}: geo {summary.geometric_total:.2%}, vol {summary.volatility:.2%}, "
              f"Sharpe {summary.sharpe:.3f}, maxDD {summary.max_drawdown:.1%}, "
              f"under water {summary.max_time_under_water} mo")
    active = rule - exposure * equal
    result = hac_mean(active)
    print(f"  GEM less the beta-matched 50/50 control: "
          f"{_annualise(result.mean) * 100.0:+.2f} pp/yr, HAC t {result.t_statistic:.2f}, "
          f"MDE80 {_mde80(result.standard_error):.2f} pp/yr, in market {exposure:.3f}")


def _current_state(panel: Panel, specs: Sequence[TimingRuleSpec]) -> None:
    """What each rule reads at the last month in the file. Volatile by construction."""
    print(f"\n### Where the rules stand at {panel.periods[-1]} — {panel.label}")
    for spec in specs:
        position = positions(panel, spec)
        last = float(position[-1])
        history = position[np.isfinite(position)]
        run = 1
        while run < history.size and history[-1 - run] == last:
            run += 1
        print(f"  {spec.label}: {'in the market' if last == 1.0 else 'out of the market'}, "
              f"and has been for {run} month(s)")


def main() -> None:  # pragma: no cover - a reporting entry point
    us = _french_panel("french_us_ff3", "US Ken French")
    exus = _french_panel("french_developed_ex_us_ff5", "Developed ex-US Ken French")
    emerging = _french_panel("french_emerging_ff5", "Emerging Ken French")
    shiller_panel = _shiller_panel()

    specs = (
        HEADLINE,
        MOMENTUM,
        TimingRuleSpec(kind=RuleKind.SMA, lookback=10, execution_lag=1),
        TimingRuleSpec(kind=RuleKind.ABSOLUTE_MOMENTUM, lookback=12, execution_lag=1),
    )
    _headline(us, specs)
    _current_state(us, specs)
    _gap_table(us, specs)
    _cost_sensitivity(us, HEADLINE)
    _subperiods(us, HEADLINE, (
        ("1927-1945", "1927-01", "1945-12"),
        ("1946-1969", "1946-01", "1969-12"),
        ("1970-1989", "1970-01", "1989-12"),
        ("1990-2007", "1990-01", "2007-12"),
        ("2008-2026 (post-publication)", "2008-01", "2026-12"),
        ("pre-1990", "1926-07", "1989-12"),
        ("post-1990", "1990-01", "2026-12"),
        ("post-2007 (Faber)", "2007-05", "2026-12"),
    ))
    _subperiods(us, MOMENTUM, (
        ("pre-1990", "1926-07", "1989-12"),
        ("post-1990", "1990-01", "2026-12"),
        ("post-2007 (Faber)", "2007-05", "2026-12"),
    ))
    _behaviour(us, HEADLINE)
    _behaviour(us.window("1990-01"), HEADLINE)
    _deflate(us)
    _deflate(us.window("1990-01"))
    _tax(us.window("1990-01"), HEADLINE, dividend_yield=0.0175, years_label="1990-2026")
    _tax(us.window("1990-01"), HEADLINE, dividend_yield=0.0125, years_label="1990-2026")
    _overlap(us, HEADLINE)
    _overlap(us, MOMENTUM)
    _alternatives(us, HEADLINE)
    _headline(exus, (HEADLINE, MOMENTUM))
    _gap_table(exus, (HEADLINE, MOMENTUM))
    _headline(emerging, (HEADLINE, MOMENTUM))
    _gap_table(emerging, (HEADLINE, MOMENTUM))
    _dual_momentum(us, exus)
    _jst_countries()
    _averaging_bias(us, shiller_panel)
    _headline(shiller_panel.window(None, "1926-06"), (HEADLINE,))


if __name__ == "__main__":  # pragma: no cover - a reporting entry point
    main()
