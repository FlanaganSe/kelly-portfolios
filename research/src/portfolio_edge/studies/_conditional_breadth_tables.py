"""Regenerates the crisis-conditional breadth tables for
:mod:`portfolio_edge.studies.conditional_breadth`.

Kept separate from the study so the study stays pure and testable and only this file
touches the cache, exactly as :mod:`portfolio_edge.studies._stacking_tables` is. Run it
with

    uv run python -m portfolio_edge.studies._conditional_breadth_tables

**This is a scoping script, not a frozen experiment.** No specification was frozen before
its numbers were seen; the conditions are the ones the stacking page's open question 2
names, and one of them (the crisis-window union) reuses windows Experiment 004 froze for
a different question. Nothing it prints may promote a sleeve or settle a decision. It
answers one question the stacking page left open — *how far does 3.71 effective bets fall
when equity is falling* — and reports intervals wide enough to say how little a tail of
forty months can resolve.

The panel is the stacking page's panel, built by the same code
------------------------------------------------------------------
Every leg is constructed by :mod:`portfolio_edge.studies._stacking_tables`: the four
tilts as their delivered loading vector applied to their own region's French factors,
with no residual, no market-beta difference and no alpha; trend as AQR's TSMOM standing
in for RSST's trend leg, about a third hot. The common window and last month read are
that module's, so the all-months row below reproduces the page's ``3.71`` to the digit,
and the script stops if it does not.

The conditioning series are **not** legs. They are total-return equity series from the
same French files — ``Mkt-RF + RF`` for the US, and the candidate's 65/25/10 US,
developed ex-US, emerging blend the stacking twin already uses — so the mask is set by
what the investor's core holdings did, never by what the legs did.

Four conditions, and what each one is
--------------------------------------
* ``worst decile, US equity`` — the ``floor(0.10 n)`` lowest US months.
* ``worst decile, 65/25/10 blend`` — the same on the global blend.
* ``exp_004 crisis windows`` — the union of the four windows Experiment 004 froze
  before its result was seen: dot-com, GFC, covid, the 2022 rate shock. Read from the
  frozen YAML through Experiment 004's own parser so this file holds no copy.
* ``trailing 12-month US return negative`` — months whose twelve-month compounded US
  total return, including the month itself, is below zero. A regime label, not a
  signal.

Units: the legs are in **percent per month**, so every mean below is percentage points
a month and is never annualised, because a tail is not a calendar.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Final

import numpy as np

from portfolio_edge.core._types import FloatArray
from portfolio_edge.data.cache import RawCache, default_cache_root
from portfolio_edge.experiments.exp_004_trend_marginal_value import _crisis_windows
from portfolio_edge.experiments.exp_016_construction_tournament import workspace_root
from portfolio_edge.experiments.specification import load_specification
from portfolio_edge.studies._stacking_tables import (
    _ALL,
    _TILTS,
    CANDIDATE_SLEEVES,
    LAST_MONTH,
    PERCENT,
    _align,
    load_factors,
    load_trend,
    synthetic_excess,
)
from portfolio_edge.studies.conditional_breadth import (
    ConditionalBreadth,
    conditional_breadth,
    trailing_negative_mask,
    window_mask,
    worst_quantile_mask,
)
from portfolio_edge.studies.stacking import effective_bets
from portfolio_edge.studies.stress_dependence import episode_returns

#: The candidate's regional equity split, as ``_stacking_tables`` §7b states it: 65% US,
#: 25% developed ex-US, 10% emerging. "65/35" on the stacking page is this blend.
BLEND: Final[Mapping[str, float]] = {"us": 0.65, "exus": 0.25, "em": 0.10}

#: Fraction of months in the lower tail.
TAIL_QUANTILE: Final = 0.10

#: Trailing window for the regime condition, months.
TRAILING_MONTHS: Final = 12

#: Bootstrap draws behind every interval, and the seed. Both are stated because a
#: percentile interval on forty rows moves visibly between seeds.
N_RESAMPLES: Final = 4000
SEED: Final = 20260901

#: The name the trend leg carries in ``_stacking_tables``.
TREND: Final = "RSST-trend"


def _total_return(
    factors: Mapping[str, Mapping[str, Mapping[str, float]]],
    window: Sequence[str],
    blend: Mapping[str, float],
) -> FloatArray:
    """``sum_r share_r (Mkt-RF_r + RF_r)`` on ``window``, as a decimal monthly return."""
    return np.asarray(
        [
            sum(
                share * (factors[region]["Mkt-RF"][period] + factors[region]["RF"][period])
                for region, share in blend.items()
            )
            / PERCENT
            for period in window
        ],
        dtype=np.float64,
    )


def crisis_windows() -> dict[str, tuple[str, str]]:
    """Experiment 004's frozen crisis windows, read through its own parser."""
    specification = load_specification(
        workspace_root() / "experiments" / "exp_004_trend_marginal_value.yaml"
    )
    return {name: (start, end) for name, start, end in _crisis_windows(specification)}


def _print_matrix(labels: Sequence[str], matrix: Sequence[Sequence[float]]) -> None:
    print("               " + "".join(f"{label[:10]:>12s}" for label in labels))
    for label, row in zip(labels, matrix, strict=True):
        print(f"{label[:14]:>14s} " + "".join(f"{value:12.3f}" for value in row))


def _print_condition(result: ConditionalBreadth, unconditional: ConditionalBreadth) -> None:
    print(f"\n   {result.name}: n={result.months} months "
          f"({result.share_of_panel:.1%} of the panel)")
    _print_matrix(result.labels, result.correlation)
    print(
        f"   1'R^-1 1 = {result.effective_bets:.2f} of {len(result.labels)}  "
        f"[{result.effective_bets_lower:.2f}, {result.effective_bets_upper:.2f}] "
        f"iid bootstrap, {result.resamples_kept}/{result.n_resamples} replicates invertible; "
        f"all-months {unconditional.effective_bets:.2f}"
    )
    print(f"\n   {'leg':<12}{'mean pp/mo':>11}{'95% NW':>20}{'n':>5}{'n_eff':>7}"
          f"{'hit':>6}{'worst':>8}{'all-months':>12}")
    baseline = {leg.label: leg.mean for leg in unconditional.legs}
    for leg in result.legs:
        print(
            f"   {leg.label:<12}{leg.mean:>+11.3f}"
            f"{f'[{leg.lower:+.3f}, {leg.upper:+.3f}]':>20}"
            f"{leg.months:>5}{leg.effective_months:>7.1f}"
            f"{leg.hit_rate:>6.2f}{leg.worst:>+8.2f}{baseline[leg.label]:>+12.3f}"
        )
    print(f"\n   {'tilt vs trend':<16}{'rho':>8}{'95% bootstrap':>20}{'all-months':>12}")
    base_pairs = {pair.label: pair.correlation for pair in unconditional.trend_pairs}
    for pair in result.trend_pairs:
        print(
            f"   {pair.label:<16}{pair.correlation:>+8.3f}"
            f"{f'[{pair.lower:+.3f}, {pair.upper:+.3f}]':>20}"
            f"{base_pairs[pair.label]:>+12.3f}"
        )


def main() -> None:
    cache = RawCache(default_cache_root())
    factors = load_factors(cache)
    trend = load_trend(cache)

    series: dict[str, tuple[tuple[str, ...], FloatArray]] = {
        spec.ticker: synthetic_excess(factors[spec.region], spec.loadings)
        for spec in CANDIDATE_SLEEVES
    }
    series[TREND] = (
        tuple(sorted(trend)),
        np.asarray([trend[period] for period in sorted(trend)], dtype=np.float64),
    )
    window, aligned = _align(series, _ALL)
    panel = np.column_stack(aligned)

    print("=" * 100)
    print("CRISIS-CONDITIONAL BREADTH — a study, exploratory throughout, no ledger entry")
    print("=" * 100)
    print(f"\nLast month read {LAST_MONTH}. Legs built by _stacking_tables: delivered loading")
    print("vector x regional factor returns, no residual, no beta difference, no alpha;")
    print("trend is AQR TSMOM. Units: percent per month. Means are never annualised.")
    print(f"\nCommon window: {len(window)} months, {window[0]}..{window[-1]}.")

    rng = np.random.default_rng(SEED)
    unconditional = conditional_breadth(
        _ALL,
        panel,
        np.ones(len(window), dtype=bool),
        name="all months",
        trend_label=TREND,
        rng=rng,
        n_resamples=N_RESAMPLES,
    )
    page = effective_bets(unconditional.correlation)
    if abs(unconditional.effective_bets - page) > 1e-9:
        raise RuntimeError(
            f"the all-months count {unconditional.effective_bets:.6f} does not reproduce "
            f"stacking.effective_bets {page:.6f} on the same matrix"
        )

    us = _total_return(factors, window, {"us": 1.0})
    blend = _total_return(factors, window, BLEND)
    windows = crisis_windows()

    conditions: list[tuple[str, np.typing.NDArray[np.bool_]]] = [
        ("worst decile, US equity", worst_quantile_mask(us, quantile=TAIL_QUANTILE)),
        ("worst decile, 65/25/10 blend", worst_quantile_mask(blend, quantile=TAIL_QUANTILE)),
        ("exp_004 crisis windows (union)", window_mask(window, windows)),
        (
            f"trailing {TRAILING_MONTHS}-month US return negative",
            trailing_negative_mask(us, months=TRAILING_MONTHS),
        ),
    ]

    print("\n1. All months — must reproduce the stacking page")
    _print_condition(unconditional, unconditional)

    print("\n2. Conditioning series, decimal monthly total return")
    us_cut = float(np.sort(us)[int(TAIL_QUANTILE * len(us)) - 1])
    blend_cut = float(np.sort(blend)[int(TAIL_QUANTILE * len(blend)) - 1])
    print(f"   US equity: worst decile is months at or below {us_cut:+.4f}")
    print(f"   65/25/10 blend: worst decile is months at or below {blend_cut:+.4f}")
    print("   exp_004 crisis windows, from the frozen YAML:")
    for name, (start, end) in windows.items():
        covered = int(np.sum(window_mask(window, {name: (start, end)})))
        print(f"      {name:<16}{start}..{end}  {covered} panel months")

    results: list[ConditionalBreadth] = []
    print("\n3. Conditional breadth")
    for name, mask in conditions:
        result = conditional_breadth(
            _ALL,
            panel,
            mask,
            name=name,
            trend_label=TREND,
            rng=rng,
            n_resamples=N_RESAMPLES,
        )
        results.append(result)
        _print_condition(result, unconditional)

    print("\n4. Effective bets by condition")
    print(f"   {'condition':<44}{'n':>5}{'1 R^-1 1':>10}{'95% iid':>18}")
    for result in (unconditional, *results):
        interval = f"[{result.effective_bets_lower:.2f}, {result.effective_bets_upper:.2f}]"
        print(
            f"   {result.name:<44}{result.months:>5}{result.effective_bets:>10.2f}"
            f"{interval:>18}"
        )

    print("\n5. What each leg did inside each frozen window, compounded, decimal")
    print(f"   {'window':<16}{'months':>7}" + "".join(f"{label[:10]:>12}" for label in _ALL))
    rows = {
        label: episode_returns(window, panel[:, j] / PERCENT, windows=windows)
        for j, label in enumerate(_ALL)
    }
    for index, (name, _) in enumerate(windows.items()):
        first = rows[_ALL[0]][index]
        flag = "" if not first.partial else " (partial)"
        print(
            f"   {name + flag:<16}{first.months:>7}"
            + "".join(f"{rows[label][index].cumulative_return:>+12.3f}" for label in _ALL)
        )

    print("\n6. Sign pattern: legs with a negative conditional mean, by condition")
    for result in results:
        losers = [leg.label for leg in result.legs if leg.mean < 0.0]
        confident = [leg.label for leg in result.legs if leg.upper < 0.0]
        print(f"   {result.name:<44} negative: {', '.join(losers) or 'none'}"
              f"; interval below zero: {', '.join(confident) or 'none'}")
    print(
        "\n   Every interval above is on a sample the condition chose, after history was\n"
        "   seen. The bootstrap resamples months independently and understates the width\n"
        "   a clustered tail deserves; the n_eff column is the better guide. Nothing here\n"
        "   is significance, and nothing here promotes or removes a sleeve."
    )
    print(f"   Tilts: {', '.join(_TILTS)}; trend: {TREND}.")


if __name__ == "__main__":
    main()
