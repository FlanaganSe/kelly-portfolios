"""Regenerates the financed gold-and-bitcoin tables for
:mod:`portfolio_edge.studies.financed_gold_bitcoin`, and records the run in the ledger.

Kept separate from the study so the study stays pure and testable and only this file
touches the cache, exactly as :mod:`portfolio_edge.studies._conditional_breadth_tables`
is. Run it with either of

    uv run python -m portfolio_edge.studies.financed_gold_bitcoin
    uv run python -m portfolio_edge.studies._financed_gold_bitcoin_tables

**This is a scoping study, not a frozen experiment.** No specification was frozen before
its numbers were seen. The gold/bitcoin split is read from RSSX's holdings on one day, the
bitcoin financing basis is an assumption swept over a range, and the window is whatever
the bitcoin series allows. Nothing it prints may promote a sleeve or settle a decision. It
answers one question ``docs/research/market-scan-2026.md`` §2.1 left open: the crypto
verdict was measured on a pro-rata construction, and a financed one now exists. Because
the split, the basis and the arms are hypothesis-bearing analytical choices, every run
appends ``started`` and ``succeeded`` (or ``failed``) entries to the ledger under the
family :data:`FAMILY`, through :class:`portfolio_edge.experiments.ledger.Ledger` and never
by hand.

The panel, and what each leg is
--------------------------------
Every leg is a decimal monthly excess return over the Ken French one-month bill, which is
also the cash rate every arm earns on its capital. Equity is French ``Mkt-RF``; gold is the
LBMA PM month-end price return less cash, read through Experiment 018's pinned loader; the
trend leg is AQR ``TSMOM`` on the primary window and Experiment 018's own 4-asset book on
the check window, both read through that experiment's ``build_legs`` so the reference arm
is the one that experiment scored; bitcoin is FRED ``CBBTCUSD`` month-end less cash,
through the same helpers the audit's stress tables use. Bitcoin binds the window at
2015-02, so every number here is on eleven years of one asset, which is a floor and not a
verdict.

The arms
--------
The reference is Experiment 018's ``base_trend30``: 70% of capital in a 3 bp core and 30%
in an RSST-like wrapper. Each candidate replaces ten points of the core with a stacked
wrapper, or sells two to three and a half points of it for spot bitcoin, which is the
audit's construction. Wrapper structures are assumed exposure vectors, not fund returns.
"""

from __future__ import annotations

import itertools
import traceback
from collections.abc import Mapping, Sequence
from typing import Final

import numpy as np

from portfolio_edge.core._types import FloatArray
from portfolio_edge.data import fred
from portfolio_edge.data.cache import RawCache
from portfolio_edge.experiments.exp_018_defensive_engines import (
    build_legs,
    default_specification_path,
    load_series,
)
from portfolio_edge.experiments.ledger import (
    Ledger,
    LedgerEntry,
    LedgerEvent,
    RunStatus,
    code_version,
    environment_snapshot,
    new_run_id,
    utc_now,
)
from portfolio_edge.experiments.result import ResultStatus
from portfolio_edge.experiments.runner import capture_git_state
from portfolio_edge.experiments.specification import JsonValue, RunKind, load_specification
from portfolio_edge.inference.bootstrap import stationary_bootstrap_indices
from portfolio_edge.studies._stress_dependence_tables import (
    BITCOIN_FIRST_MONTH,
    STRESS_WINDOWS,
    _excess_from_levels,
    _month_end,
    _require,
)
from portfolio_edge.studies.financed_gold_bitcoin import (
    PERCENT,
    TAIL_QUANTILE,
    Comparison,
    Wrapper,
    break_even_bitcoin_excess,
    compare,
    growth_penalty_pp_yr,
    notional,
    portfolio_total,
    track,
    wrapper_excess,
)
from portfolio_edge.studies.stress_dependence import (
    EpisodeReturn,
    convexity,
    episode_returns,
    tail_dependence,
)

FAMILY: Final = "study_financed_gold_bitcoin"

#: Bootstrap draws and seed, stated because a percentile interval on 136 rows moves
#: visibly between seeds. Mean block length is Experiment 018's.
N_RESAMPLES: Final = 10_000
SEED: Final = 20260902
BLOCK_MONTHS: Final = 12.0

#: The gold/bitcoin split inside the stacked sleeve. RSSX's holdings on 2026-09-01
#: (issuer page, read 2026-09-02) were 64.43% of net assets in micro gold futures and
#: 26.73% in CME bitcoin futures plus 7.75% in IBIT, so 65/35 by notional. The prospectus
#: of 2025-05-22 says the sleeve "will generally allocate between 75% and 95% of its
#: assets to gold and between 5% and 25% to bitcoin" under a risk-parity rule, so the
#: read split sits outside the band the prospectus called typical; both are run.
SPLIT_GOLD: Final = 0.65
SPLIT_BITCOIN: Final = 0.35

#: Annual basis points over cash on financed notional. Equity and gold are Experiment
#: 018's. Bitcoin has no measured basis anywhere in this repository: the CME contract's
#: annualised contango has run from near zero to well above ten percent, so the base case
#: borrows the equity figure and the sweep covers the range.
BASIS_BP: Final[Mapping[str, float]] = {"equity": 62.0, "gold": 30.0, "bitcoin": 62.0}
BITCOIN_BASIS_SWEEP_BP: Final = (0.0, 62.0, 300.0, 600.0, 1000.0)

#: The gold premium scenarios the break-even is shown under: zero, the half-century
#: excess return the audit cites (+1.75%/yr at a Sharpe of 0.18), and the sample mean on
#: the window, which is printed beside them.
GOLD_PREMIUM_SCENARIOS_PP_YR: Final = (0.0, 1.75)

STACK_WEIGHT: Final = 0.10

WRAPPERS: Final[Mapping[str, Wrapper]] = {
    "CORE": Wrapper(ticker="CORE", exposures={"equity": 1.0}, fee_bp=3.0, financed={}),
    "RSST_LIKE": Wrapper(
        ticker="RSST_LIKE",
        exposures={"equity": 1.072, "trend": 1.0},
        fee_bp=99.0,
        financed={"equity": 0.331},
        note="Experiment 018's RSST-like wrapper, unchanged.",
    ),
    "RSSX_LIKE": Wrapper(
        ticker="RSSX_LIKE",
        exposures={"equity": 1.0, "gold": SPLIT_GOLD, "bitcoin": SPLIT_BITCOIN},
        fee_bp=67.0,
        financed={"gold": SPLIT_GOLD, "bitcoin": SPLIT_BITCOIN},
        note="One dollar of equity plus a 65/35 gold/bitcoin sleeve, all of it financed.",
    ),
    "RSSX_5050": Wrapper(
        ticker="RSSX_5050",
        exposures={"equity": 1.0, "gold": 0.5, "bitcoin": 0.5},
        fee_bp=67.0,
        financed={"gold": 0.5, "bitcoin": 0.5},
        note="The prospectus's equal-volatility example.",
    ),
    "RSSX_8020": Wrapper(
        ticker="RSSX_8020",
        exposures={"equity": 1.0, "gold": 0.8, "bitcoin": 0.2},
        fee_bp=67.0,
        financed={"gold": 0.8, "bitcoin": 0.2},
        note="Inside the prospectus's typical band.",
    ),
    "GOLD_STACK": Wrapper(
        ticker="GOLD_STACK",
        exposures={"equity": 1.0, "gold": 1.0},
        fee_bp=67.0,
        financed={"gold": 1.0},
        note="RSSX's structure with bitcoin set to zero, at RSSX's fee.",
    ),
    "GDE_LIKE": Wrapper(
        ticker="GDE_LIKE",
        exposures={"equity": 0.9, "gold": 0.9},
        fee_bp=20.0,
        financed={"gold": 0.9},
        note="Experiment 018's gold arm, for continuity.",
    ),
    "BTC_STACK": Wrapper(
        ticker="BTC_STACK",
        exposures={"equity": 1.0, "bitcoin": SPLIT_BITCOIN},
        fee_bp=67.0,
        financed={"bitcoin": SPLIT_BITCOIN},
        note="RSSX's bitcoin leg alone: 0.35 financed bitcoin per dollar, at RSSX's fee.",
    ),
    "BTC_SPOT": Wrapper(
        ticker="BTC_SPOT",
        exposures={"bitcoin": 1.0},
        fee_bp=25.0,
        financed={},
        note="A spot bitcoin ETP at IBIT's fee, bought with capital.",
    ),
}

REFERENCE: Final = "reference"

ARMS: Final[Mapping[str, Mapping[str, float]]] = {
    REFERENCE: {"CORE": 0.70, "RSST_LIKE": 0.30},
    "rssx_stack_10": {"CORE": 0.60, "RSST_LIKE": 0.30, "RSSX_LIKE": 0.10},
    "rssx_8020_stack_10": {"CORE": 0.60, "RSST_LIKE": 0.30, "RSSX_8020": 0.10},
    "rssx_5050_stack_10": {"CORE": 0.60, "RSST_LIKE": 0.30, "RSSX_5050": 0.10},
    "gold_stack_10": {"CORE": 0.60, "RSST_LIKE": 0.30, "GOLD_STACK": 0.10},
    "gde_stack_10": {"CORE": 0.60, "RSST_LIKE": 0.30, "GDE_LIKE": 0.10},
    "btc_stack_10": {"CORE": 0.60, "RSST_LIKE": 0.30, "BTC_STACK": 0.10},
    "btc_prorata_2": {"CORE": 0.68, "RSST_LIKE": 0.30, "BTC_SPOT": 0.02},
    "btc_prorata_3_5": {"CORE": 0.665, "RSST_LIKE": 0.30, "BTC_SPOT": 0.035},
}

ARM_NOTES: Final[Mapping[str, str]] = {
    "rssx_stack_10": "reference + 10 pts RSSX-like (6.5 gold, 3.5 bitcoin, financed)",
    "rssx_8020_stack_10": "same, 80/20 split (8 gold, 2 bitcoin)",
    "rssx_5050_stack_10": "same, 50/50 split (5 gold, 5 bitcoin)",
    "gold_stack_10": "reference + 10 pts financed gold at RSSX's fee",
    "gde_stack_10": "reference + 10 pts GDE-like (exp_018's gold arm)",
    "btc_stack_10": "reference + 3.5 pts financed bitcoin at RSSX's fee",
    "btc_prorata_2": "2 pts of core sold for spot bitcoin (the audit's construction)",
    "btc_prorata_3_5": "3.5 pts of core sold for spot bitcoin (notional-matched to btc_stack_10)",
}

#: Label, trend source, declared start. The first two start where bitcoin starts; the
#: third drops 2015-2019, a post-hoc cut made after the full-window numbers were seen,
#: printed so a reader can see how much of the full window is the asset's early years.
PANELS: Final = (
    ("vendor trend (AQR TSMOM)", "aqr_tsmom", None),
    ("own 4-asset book (exp_018 primary trend leg)", "own_4_asset_book", None),
    ("vendor trend, 2020-01 onward (post-hoc cut)", "aqr_tsmom", "2020-01"),
)

#: The two 2025-26 crypto drawdowns the recommendation cites, as month ranges, plus the
#: two modern equity shocks the audit's panel reaches on this window.
EPISODES: Final[Mapping[str, tuple[str, str]]] = {
    "2020 Q1 covid": STRESS_WINDOWS["2020 Q1 covid"],
    "2022 rate shock": STRESS_WINDOWS["2022 rate shock"],
    "2025 tariff episode": ("2025-02", "2025-04"),
    "2025-26 cycle drawdown": ("2025-10", "2026-06"),
}

#: RSSX month-end market price, adjusted for its one distribution ($0.393, ex-date
#: 2025-12-29), from Yahoo Finance's chart API read 2026-09-02, cross-checked against
#: Nasdaq's unadjusted closes for the same dates (they agree to the cent before the
#: distribution). Market price, not NAV: the fund's 30-day median spread was 0.28%.
RSSX_ADJUSTED_CLOSE: Final[Mapping[str, float]] = {
    "2025-05": 19.6043,
    "2025-06": 20.6272,
    "2025-07": 21.2777,
    "2025-08": 22.0957,
    "2025-09": 24.9932,
    "2025-10": 25.9294,
    "2025-11": 25.4692,
    "2025-12": 25.4500,
    "2026-01": 27.5800,
    "2026-02": 26.6800,
    "2026-03": 23.4300,
    "2026-04": 26.6200,
    "2026-05": 27.2410,
    "2026-06": 22.9800,
    "2026-07": 23.5810,
    "2026-08": 27.8600,
}

MonthSeries = dict[str, float]


# --------------------------------------------------------------------------- loading


def load() -> tuple[dict[str, MonthSeries], MonthSeries, dict[str, str], tuple[str, ...]]:
    """Every leg as a month-keyed excess return, the cash rate, digests, and findings."""
    specification = load_specification(default_specification_path())
    raw = load_series(specification)
    legs = build_legs(raw, specification)
    digests = {str(record["id"]): str(record["sha256_raw"]) for record in raw.provenance}

    cache = RawCache()
    btc_entry = _require(cache, fred.series_url("CBBTCUSD"), "the FRED bitcoin series")
    digests["fred_cbbtcusd"] = btc_entry.sha256
    btc_table = fred.parse(cache, btc_entry, "CBBTCUSD")
    bitcoin = _excess_from_levels(
        _month_end(btc_table.periods, btc_table.values),
        legs.cash,
        first=BITCOIN_FIRST_MONTH,
        carry=0.0,
    )
    series: dict[str, MonthSeries] = {
        "equity": dict(legs.equity),
        "gold": dict(legs.gold),
        "bitcoin": bitcoin,
        "aqr_tsmom": dict(legs.trend["aqr_tsmom"]),
        "own_4_asset_book": dict(legs.trend["own_4_asset_book"]),
    }
    return series, dict(legs.cash), digests, raw.findings


def _window(series: Sequence[MonthSeries]) -> tuple[str, ...]:
    common = set(series[0])
    for s in series[1:]:
        common &= set(s)
    months = tuple(sorted(common))
    for earlier, later in itertools.pairwise(months):
        gap = (int(later[:4]) * 12 + int(later[5:7])) - (int(earlier[:4]) * 12 + int(earlier[5:7]))
        if gap != 1:
            raise RuntimeError(f"the common window has a gap between {earlier} and {later}")
    return months


def _take(series: MonthSeries, months: Sequence[str]) -> FloatArray:
    return np.asarray([series[m] for m in months], dtype=np.float64)


# --------------------------------------------------------------------------- printing


def _interval(pair: tuple[float, float]) -> str:
    return f"[{pair[0]:+.2f}, {pair[1]:+.2f}]"


def _print_comparisons(rows: Sequence[Comparison]) -> None:
    print(
        f"   {'arm':<20}{'arith gap':>10}{'95% block':>17}{'MDE80':>7}{'log gap':>9}"
        f"{'95% block':>17}{'vol':>6}{'maxDD':>8}{'ref DD':>8}{'tail':>7}{'hit':>5}"
        f"{'up b':>7}{'dn b':>7}"
    )
    for r in rows:
        print(
            f"   {r.name:<20}{r.arithmetic_gap_pp_yr:>+10.2f}{_interval(r.arithmetic_interval):>17}"
            f"{r.mde_pp_yr:>7.2f}{r.log_growth_gap_pp_yr:>+9.2f}"
            f"{_interval(r.log_growth_interval):>17}{r.arm_volatility_pct:>6.1f}"
            f"{r.arm_max_drawdown * PERCENT:>8.1f}{r.reference_max_drawdown * PERCENT:>8.1f}"
            f"{r.worst_decile_offset_pp_month:>+7.2f}{r.worst_decile_hit_rate:>5.2f}"
            f"{r.up_beta:>+7.3f}{r.down_beta:>+7.3f}"
        )


def _ledger_parameters(months_by_panel: Mapping[str, tuple[str, str, int]]) -> JsonValue:
    return {
        "study": "financed gold and bitcoin on top of base_trend30",
        "frozen_specification": None,
        "gold_bitcoin_split": {"gold": SPLIT_GOLD, "bitcoin": SPLIT_BITCOIN},
        "split_source": "RSSX holdings 2026-09-01, issuer page read 2026-09-02",
        "basis_bp": dict(BASIS_BP),
        "bitcoin_basis_sweep_bp": list(BITCOIN_BASIS_SWEEP_BP),
        "stack_weight": STACK_WEIGHT,
        "wrappers": {
            t: {"exposures": dict(w.exposures), "fee_bp": w.fee_bp, "financed": dict(w.financed)}
            for t, w in WRAPPERS.items()
        },
        "arms": {name: dict(weights) for name, weights in ARMS.items()},
        "panels": {
            name: {"start": start, "end": end, "months": n}
            for name, (start, end, n) in months_by_panel.items()
        },
        "bootstrap": {
            "method": "stationary",
            "mean_block_months": BLOCK_MONTHS,
            "n_resamples": N_RESAMPLES,
            "seed": SEED,
        },
        "tail_quantile": TAIL_QUANTILE,
        "episodes": {k: list(v) for k, v in EPISODES.items()},
        "gold_premium_scenarios_pp_yr": list(GOLD_PREMIUM_SCENARIOS_PP_YR),
    }


def _entry(
    *,
    run_id: str,
    event: LedgerEvent,
    status: RunStatus,
    digests: Mapping[str, str],
    parameters: JsonValue,
    failure_reason: str | None = None,
    result_status: ResultStatus | None = None,
    notes: str = "",
) -> LedgerEntry:
    git = capture_git_state()
    return LedgerEntry(
        run_id=run_id,
        experiment_family=FAMILY,
        timestamp_utc=utc_now().isoformat(),
        event=event,
        status=status,
        git_commit=git.commit,
        worktree_dirty=git.dirty,
        diff_sha256=git.diff_sha256,
        spec_hash=None,
        dataset_manifest_hashes=tuple(sorted(digests.values())),
        code_version=code_version(),
        environment=environment_snapshot(),
        parameters=parameters,
        seed=SEED,
        failure_reason=failure_reason,
        run_kind=RunKind.EXPLORATORY,
        result_status=result_status,
        notes=notes,
    )


# --------------------------------------------------------------------------- main


def _run(series: Mapping[str, MonthSeries], cash: MonthSeries) -> dict[str, tuple[str, str, int]]:
    months_by_panel: dict[str, tuple[str, str, int]] = {}
    rng = np.random.default_rng(SEED)

    print("\n1. Wrappers: exposure per dollar of capital, fee, financed notional")
    for ticker, w in WRAPPERS.items():
        exposures = ", ".join(f"{k} {v:.3f}" for k, v in w.exposures.items())
        financed = ", ".join(f"{k} {v:.3f}" for k, v in w.financed.items()) or "none"
        print(f"   {ticker:<11}{exposures:<48}{w.fee_bp:>4.0f} bp  financed: {financed}")
    print(f"   basis over cash, bp: {dict(BASIS_BP)}")

    print("\n2. Arms: capital weights and notional per dollar")
    print(f"   {'arm':<20}{'equity':>8}{'trend':>7}{'gold':>7}{'btc':>7}{'gross':>7}  weights")
    for name, weights in ARMS.items():
        n = notional(weights, WRAPPERS)
        print(
            f"   {name:<20}{n.get('equity', 0):>8.3f}{n.get('trend', 0):>7.3f}"
            f"{n.get('gold', 0):>7.3f}{n.get('bitcoin', 0):>7.3f}{n['gross']:>7.3f}  "
            + ", ".join(f"{t} {w:.3f}" for t, w in weights.items())
        )

    first_panel: dict[str, FloatArray] | None = None
    first_months: tuple[str, ...] = ()
    first_totals: dict[str, FloatArray] = {}
    for label, trend_key, start in PANELS:
        months = _window(
            [series["equity"], series["gold"], series["bitcoin"], series[trend_key], cash]
        )
        if start is not None:
            months = tuple(m for m in months if m >= start)
        months_by_panel[label] = (months[0], months[-1], len(months))
        legs = {
            "equity": _take(series["equity"], months),
            "gold": _take(series["gold"], months),
            "bitcoin": _take(series["bitcoin"], months),
            "trend": _take(series[trend_key], months),
        }
        cash_arr = _take(cash, months)
        indices = stationary_bootstrap_indices(len(months), BLOCK_MONTHS, N_RESAMPLES, rng)
        excess = {t: wrapper_excess(legs, w, BASIS_BP) for t, w in WRAPPERS.items()}
        totals = {
            name: portfolio_total(cash_arr, weights, excess) for name, weights in ARMS.items()
        }
        rows = [
            compare(
                name,
                totals[name],
                totals[REFERENCE],
                equity_excess=legs["equity"],
                indices=indices,
            )
            for name in ARMS
            if name != REFERENCE
        ]
        print(f"\n3. Panel: {label}: {len(months)} months, {months[0]}..{months[-1]}")
        print(
            "   Gaps are arm minus reference, pp/yr, after fees and financing; MDE80 is the\n"
            "   smallest gap this window could resolve at 80% power and is the number to read\n"
            "   first. 'tail' is the arm-minus-reference mean in the worst decile of equity\n"
            "   months, pp/month, with its hit rate; betas are of that offset to equity."
        )
        _print_comparisons(rows)
        if first_panel is None:
            first_panel = legs
            first_months = months
            first_totals = totals
            first_cash = cash_arr

    assert first_panel is not None
    legs = first_panel
    months = first_months
    totals = first_totals
    equity = legs["equity"]

    print(f"\n4. Legs on the primary window, {months[0]}..{months[-1]}: decimal excess of cash")
    print(
        f"   {'leg':<10}{'mean/mo':>9}{'vol/yr':>8}{'arith/yr':>9}{'tail mean':>10}{'hit':>5}"
        f"{'worst':>7}{'rho':>7}{'up b':>7}{'dn b':>7}{'kappa t':>8}"
    )
    for name in ("equity", "gold", "bitcoin", "trend"):
        s = legs[name]
        t = tail_dependence(equity, s, quantile=TAIL_QUANTILE)
        c = convexity(equity, s)
        print(
            f"   {name:<10}{np.mean(s) * PERCENT:>+9.2f}"
            f"{np.std(s, ddof=1) * np.sqrt(12) * PERCENT:>8.1f}"
            f"{np.mean(s) * 1200:>+9.2f}{t.mean_low * PERCENT:>+10.2f}{t.hit_rate_low:>5.2f}"
            f"{t.worst_low * PERCENT:>+7.1f}{t.correlation_full:>+7.3f}{c.up_beta:>+7.3f}"
            f"{c.down_beta:>+7.3f}{c.kappa_t:>+8.2f}"
        )
    print(
        f"   worst decile: {t.months_low} months at or below "
        f"{np.sort(equity)[t.months_low - 1] * PERCENT:+.2f}%"
    )

    print("\n5. Episodes: cumulative return of each leg and each arm; '*' marks partial coverage")
    print(
        f"   {'episode':<24}"
        + "".join(f"{k[:10]:>12}" for k in ("equity", "gold", "bitcoin", "trend"))
    )
    leg_rows = {k: episode_returns(months, legs[k], windows=EPISODES) for k in legs}
    for i, name in enumerate(EPISODES):
        row = leg_rows["equity"][i]
        flag = "*" if row.partial else ""
        print(
            f"   {name + flag:<24}"
            + "".join(
                f"{leg_rows[k][i].cumulative_return * PERCENT:>+12.1f}"
                for k in ("equity", "gold", "bitcoin", "trend")
            )
        )
    arm_rows = {name: episode_returns(months, totals[name], windows=EPISODES) for name in ARMS}
    print(
        f"\n   {'episode':<24}{'reference':>11}"
        + "".join(f"{n[:12]:>14}" for n in ARMS if n != REFERENCE)
    )
    print(f"   {'(arm minus reference, pp)':<24}")
    for i, name in enumerate(EPISODES):
        ref_row = arm_rows[REFERENCE][i]
        flag = "*" if ref_row.partial else ""
        print(
            f"   {name + flag:<24}{ref_row.cumulative_return * PERCENT:>+11.1f}"
            + "".join(
                f"{(_offset(arm_rows[n][i], ref_row)) * PERCENT:>+14.1f}"
                for n in ARMS
                if n != REFERENCE
            )
        )

    print("\n6. Bitcoin financing basis sweep: arithmetic gap vs reference, pp/yr, primary window")
    print(
        f"   {'basis bp':<10}"
        + "".join(f"{n:>20}" for n in ("rssx_stack_10", "btc_stack_10", "rssx_5050_stack_10"))
    )
    for basis in BITCOIN_BASIS_SWEEP_BP:
        rates = {**BASIS_BP, "bitcoin": basis}
        excess = {t: wrapper_excess(legs, w, rates) for t, w in WRAPPERS.items()}
        ref = portfolio_total(first_cash, ARMS[REFERENCE], excess)
        cells = []
        for arm in ("rssx_stack_10", "btc_stack_10", "rssx_5050_stack_10"):
            arm_total = portfolio_total(first_cash, ARMS[arm], excess)
            cells.append(float(np.mean(arm_total - ref)) * 1200)
        print(f"   {basis:<10.0f}" + "".join(f"{c:>+20.2f}" for c in cells))

    print(
        "\n7. Break-even bitcoin excess return, pp/yr arithmetic, for ten points of RSSX-like stack"
    )
    gold_sample = float(np.mean(legs["gold"])) * 1200
    btc_sample = float(np.mean(legs["bitcoin"])) * 1200
    stack = WRAPPERS["RSSX_LIKE"]
    core_excess = wrapper_excess(legs, WRAPPERS["CORE"], BASIS_BP)
    penalty = growth_penalty_pp_yr(
        totals[REFERENCE], wrapper_excess(legs, stack, BASIS_BP) - core_excess, weight=STACK_WEIGHT
    )
    print(
        f"   sample means on this window: gold {gold_sample:+.2f}, "
        f"bitcoin {btc_sample:+.2f} pp/yr excess;\n"
        f"   log-growth penalty of the stack at {STACK_WEIGHT:.0%}: {penalty:+.2f} pp/yr "
        f"per dollar of stack\n"
        f"   (half the variance it adds, divided by its weight)."
    )
    print(
        f"   {'gold premium':<16}{'btc basis bp':>13}"
        f"{'arith break-even':>18}{'growth break-even':>19}"
    )
    for gold_premium in (*GOLD_PREMIUM_SCENARIOS_PP_YR, gold_sample):
        for basis in (62.0, 300.0, 600.0):
            rates = {**BASIS_BP, "bitcoin": basis}
            arith = break_even_bitcoin_excess(
                stack, core_fee_bp=3.0, basis_bp=rates, gold_excess_pp_yr=gold_premium
            )
            growth = break_even_bitcoin_excess(
                stack,
                core_fee_bp=3.0,
                basis_bp=rates,
                gold_excess_pp_yr=gold_premium,
                growth_penalty=penalty,
            )
            label = f"{gold_premium:+.2f}" + (" (sample)" if gold_premium == gold_sample else "")
            print(f"   {label:<16}{basis:>13.0f}{arith:>+18.2f}{growth:>+19.2f}")
    btc_stack = WRAPPERS["BTC_STACK"]
    btc_penalty = growth_penalty_pp_yr(
        totals[REFERENCE],
        wrapper_excess(legs, btc_stack, BASIS_BP) - core_excess,
        weight=STACK_WEIGHT,
    )
    print(
        f"\n   The bitcoin leg alone (BTC_STACK, 3.5 points financed at RSSX's fee), whose\n"
        f"   break-even does not depend on gold; its growth penalty is {btc_penalty:+.2f} pp/yr\n"
        f"   per dollar of stack:"
    )
    print(f"   {'btc basis bp':<16}{'arith break-even':>18}{'growth break-even':>19}")
    for basis in (62.0, 300.0, 600.0):
        rates = {**BASIS_BP, "bitcoin": basis}
        arith = break_even_bitcoin_excess(
            btc_stack, core_fee_bp=3.0, basis_bp=rates, gold_excess_pp_yr=0.0
        )
        growth = break_even_bitcoin_excess(
            btc_stack,
            core_fee_bp=3.0,
            basis_bp=rates,
            gold_excess_pp_yr=0.0,
            growth_penalty=btc_penalty,
        )
        print(f"   {basis:<16.0f}{arith:>+18.2f}{growth:>+19.2f}")
    print(
        "   Read: the bitcoin arithmetic excess return, pp/yr, at which the stack's expected\n"
        "   gap over the core it displaces is zero. Below the arithmetic figure the stack\n"
        "   loses money in expectation; below the growth figure it lowers expected log growth."
    )

    print("\n8. RSSX realised against the assumed exposure vector (market price, adjusted)")
    fund_months = [m for m in sorted(RSSX_ADJUSTED_CLOSE) if m > "2025-05"]
    common = [
        m
        for m in fund_months
        if all(m in series[k] for k in ("equity", "gold", "bitcoin")) and m in cash
    ]
    prices = RSSX_ADJUSTED_CLOSE
    fund = np.asarray([prices[m] / prices[_previous(m)] - 1.0 for m in common], dtype=np.float64)
    model_legs = {k: _take(series[k], common) for k in ("equity", "gold", "bitcoin")}
    model = _take(cash, common) + wrapper_excess(model_legs, stack, BASIS_BP)
    summary = track(fund, model)
    print(f"   {'month':<9}{'RSSX':>8}{'model':>8}{'equity':>8}{'gold':>8}{'bitcoin':>9}")
    for i, m in enumerate(common):
        print(
            f"   {m:<9}{fund[i] * PERCENT:>+8.2f}{model[i] * PERCENT:>+8.2f}"
            f"{model_legs['equity'][i] * PERCENT:>+8.2f}{model_legs['gold'][i] * PERCENT:>+8.2f}"
            f"{model_legs['bitcoin'][i] * PERCENT:>+9.2f}"
        )
    print(
        f"   {summary.months} months {common[0]}..{common[-1]}: "
        f"RSSX {summary.fund_cumulative:+.1%}, "
        f"model {summary.model_cumulative:+.1%}; correlation {summary.correlation:.3f}; "
        f"fund minus model {summary.mean_difference_pp_month:+.2f} pp/month "
        f"(se {summary.difference_standard_error_pp_month:.2f}); tracking error "
        f"{summary.tracking_error_pct:.1f}%/yr."
    )
    later = [m for m in fund_months if m not in common]
    if later:
        print(f"   RSSX months after the panel's last leg, not modelled: {', '.join(later)}.")

    print(
        "\n   Every interval above is on eleven years of one asset, chosen after its history\n"
        "   was seen. No specification was frozen. Nothing here promotes or removes a sleeve."
    )
    return months_by_panel


def _offset(arm: EpisodeReturn, reference: EpisodeReturn) -> float:
    return arm.cumulative_return - reference.cumulative_return


def _previous(month: str) -> str:
    year, m = int(month[:4]), int(month[5:7])
    return f"{year - 1}-12" if m == 1 else f"{year}-{m - 1:02d}"


def main() -> None:
    print("=" * 100)
    print("FINANCED GOLD AND BITCOIN ON THE CONSTRUCTION: a study, exploratory throughout")
    print("=" * 100)
    series, cash, digests, findings = load()
    for finding in findings:
        print(f"   note: {finding}")
    for name, digest in sorted(digests.items()):
        print(f"   {name:32s} {digest[:8]}")

    ledger = Ledger()
    run_id = new_run_id()
    parameters = _ledger_parameters({})
    ledger.append(
        _entry(
            run_id=run_id,
            event=LedgerEvent.STARTED,
            status=RunStatus.STARTED,
            digests=digests,
            parameters=parameters,
            notes="study; no frozen specification; split, basis and arms chosen after the audit",
        )
    )
    try:
        months_by_panel = _run(series, cash)
    except Exception as exc:
        ledger.append(
            _entry(
                run_id=run_id,
                event=LedgerEvent.FAILED,
                status=RunStatus.FAILED,
                digests=digests,
                parameters=parameters,
                failure_reason=f"{type(exc).__name__}: {exc}",
            )
        )
        traceback.print_exc()
        raise
    ledger.append(
        _entry(
            run_id=run_id,
            event=LedgerEvent.SUCCEEDED,
            status=RunStatus.SUCCEEDED,
            digests=digests,
            parameters=_ledger_parameters(months_by_panel),
            result_status=ResultStatus.EXPLORATORY,
            notes="printed to stdout; interpreted in docs/research/alternative-sleeves-audit.md §3",
        )
    )
    print(f"\n   ledger: run {run_id} recorded under family {FAMILY}.")


if __name__ == "__main__":
    main()
