"""Regenerates §5.7 of ``docs/research/valuation-and-the-allocation.md``.

Kept separate from :mod:`portfolio_edge.studies.global_split_regret` so the arithmetic
stays pure and testable and only this file touches the cache, as every other study pair
in this package is arranged. Run it with::

    uv run python -m portfolio_edge.studies.global_split_regret

**Everything here is `exploratory`.** No specification was frozen before these numbers
were seen. Because the scenario anchors, the French window and the yield readings are
hypothesis-bearing analytical choices, every run appends ``started`` and ``succeeded`` (or
``failed``) entries to the ledger under the family :data:`FAMILY`, through
:class:`portfolio_edge.experiments.ledger.Ledger` and never by hand.

Inputs, each dated where it is declared:

* Ken French's US and developed-ex-US five-factor files for ``Mkt-RF + RF``, the two
  markets' dollar total returns, on their common monthly window. They supply the second
  moments and nothing else: no mean from this window enters any scenario.
* The Jordà-Schularick-Taylor R6 panel, through
  :func:`portfolio_edge.studies._valuation_conditioning_tables.spread_history`, for the
  median and standard deviation of the US-minus-panel log dividend-yield spread over
  1871-2020, the anchor the reversion scenarios are measured against.
* Shiller's workbook for the S&P dividend yield, ``D / P`` on the last row carrying both.
* Readings that no loader here can reach, pinned as constants with their source and date:
  Siblis Research's US and developed-ex-US CAPE (the relative multiple) and global US
  weight, and Vanguard's VXUS cash yield as the ex-US dividend yield.
"""

from __future__ import annotations

import math
import traceback
from collections.abc import Mapping, Sequence
from itertools import pairwise
from typing import Final

import numpy as np

from portfolio_edge.data import french, shiller
from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.macrohistory import get_dataset as jst_dataset
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
from portfolio_edge.experiments.specification import JsonValue, RunKind
from portfolio_edge.studies._currency_hedging_tables import _french_total_return
from portfolio_edge.studies._valuation_conditioning_tables import spread_history
from portfolio_edge.studies.global_split_regret import (
    EQUAL_PRIOR,
    HORIZONS,
    RERATING_STATES,
    REVERSION_PRIOR,
    SPLITS,
    Reading,
    Readings,
    RegretTable,
    RelativeMoments,
    ReratingPrior,
    Scenario,
    bayes_split_sweep,
    expected_differential,
    growth_optimal_split,
    implied_differential,
    regret_table,
    years_to_reach,
)

FAMILY: Final = "study_global_split_regret"

US_FILE: Final = "french_us_ff5"
EX_US_FILE: Final = "french_developed_ex_us_ff5"

#: Siblis Research, ``https://siblisresearch.com/data/cape-ratios-by-country/`` and its
#: world CAPE page, read 2026-08-22, both figures inside one methodology.
SIBLIS_US_CAPE: Final = Reading(value=35.82, as_of="2026-06-30", source="Siblis Research")
SIBLIS_EX_US_CAPE: Final = Reading(value=21.02, as_of="2026-06-30", source="Siblis Research")
RELATIVE_CAPE: Final = Reading(
    value=SIBLIS_US_CAPE.value / SIBLIS_EX_US_CAPE.value,
    as_of="2026-06-30",
    source="Siblis Research US CAPE over developed ex-US CAPE",
)
#: The US share of Siblis's global index of the 3,000 largest companies.
CAP_WEIGHT_US: Final = Reading(value=0.64, as_of="2026-06-30", source="Siblis Research")

#: VXUS's cash yield from Vanguard's fund-yield endpoint, the reading
#: ``docs/research/portfolio-for-one-investor.md`` §3.1 grosses up to Box 1a. It carries EM
#: at about a quarter of the fund; AVDV's 2.62% and J.P. Morgan's Europe ex-UK 2.80%
#: (chart-read, 2026-06-30) bracket the developed-only figure from above.
EX_US_DIVIDEND_YIELD: Final = Reading(
    value=0.0250, as_of="2026-07-31", source="Vanguard fund-yield endpoint, VXUS cash yield"
)

#: The US share of the published vector's equity notional: RSST 30 + VTI 19 + VTV 15 over
#: 100 points of equity, the rest VXUS 16 + AVDV 10 + IDMO 5 + AVES 5.
CURRENT_US_SHARE: Final = 0.64

CONTRIBUTION_RATES: Final = (0.05, 0.10, 0.15)
SWEEP: Final = tuple(round(0.05 * i, 2) for i in range(21))


# --------------------------------------------------------------------------- inputs


def load_moments(cache: RawCache) -> tuple[RelativeMoments, dict[str, str]]:
    """Second moments of the two markets' dollar total returns on the common window."""
    us, us_hash = _french_total_return(cache, US_FILE)
    ex_us, ex_us_hash = _french_total_return(cache, EX_US_FILE)
    months = sorted(set(us) & set(ex_us))
    if len(months) < 24:
        raise RuntimeError("fewer than two years of overlap between the French files")
    u = np.array([us[m] for m in months], dtype=np.float64)
    x = np.array([ex_us[m] for m in months], dtype=np.float64)
    moments = RelativeMoments(
        us_volatility=float(np.std(u, ddof=1) * math.sqrt(12)),
        ex_us_volatility=float(np.std(x, ddof=1) * math.sqrt(12)),
        correlation=float(np.corrcoef(u, x)[0, 1]),
        first_month=months[0],
        last_month=months[-1],
        months=len(months),
    )
    return moments, {US_FILE: us_hash, EX_US_FILE: ex_us_hash}


def load_readings(cache: RawCache) -> tuple[Readings, dict[str, str]]:
    """The dated inputs: two from the cache, the rest pinned above."""
    spread = spread_history(cache)
    jst = cache.require(jst_dataset("jst_macrohistory_r6").url)
    first, last = int(spread.index[0]), int(spread.index[-1])
    dataset = shiller.get_dataset("shiller_ie_data")
    entry = cache.require(dataset.url)
    frame = shiller.parse(cache, entry, dataset=dataset).table.to_frame()
    dated = frame[["P", "D"]].dropna()
    row = dated.iloc[-1]
    readings = Readings(
        us_dividend_yield=Reading(
            value=float(row["D"]) / float(row["P"]),
            as_of=str(dated.index[-1]),
            source="Shiller ie_data, D / P",
        ),
        ex_us_dividend_yield=EX_US_DIVIDEND_YIELD,
        relative_cape=RELATIVE_CAPE,
        long_run_log_median=Reading(
            value=float(spread.median()),
            as_of=f"{first}-{last}",
            source="JST R6, median US-minus-panel-median log dividend-yield spread",
        ),
        log_spread_sd=Reading(
            value=float(spread.std(ddof=1)),
            as_of=f"{first}-{last}",
            source="JST R6, standard deviation of the same spread",
        ),
        cap_weight_us=CAP_WEIGHT_US,
    )
    return readings, {"jst_macrohistory_r6": jst.sha256, "shiller_ie_data": entry.sha256}


# --------------------------------------------------------------------------- ledger


def _entry(
    *,
    run_id: str,
    event: LedgerEvent,
    status: RunStatus,
    hashes: Mapping[str, str],
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
        dataset_manifest_hashes=tuple(sorted(hashes.values())),
        code_version=code_version(),
        environment=environment_snapshot(),
        parameters=parameters,
        seed=None,
        failure_reason=failure_reason,
        run_kind=RunKind.EXPLORATORY,
        result_status=result_status,
        notes=notes,
    )


def _reading(reading: Reading) -> JsonValue:
    return {"value": reading.value, "as_of": reading.as_of, "source": reading.source}


def _parameters(
    readings: Readings | None, moments: RelativeMoments | None
) -> JsonValue:
    return {
        "study": "US/international split as minimax and expected regret over a scenario grid",
        "frozen_specification": None,
        "splits_us_share": list(SPLITS),
        "horizons_years": list(HORIZONS),
        "rerating_states": list(RERATING_STATES),
        "growth_differentials": [0.0, 0.01, -0.01],
        "currency_legs": [0.0, 0.01, -0.01],
        "priors": {
            prior.label: {str(state): weight for state, weight in prior.weights.items()}
            for prior in (EQUAL_PRIOR, REVERSION_PRIOR)
        },
        "readings": None
        if readings is None
        else {
            "us_dividend_yield": _reading(readings.us_dividend_yield),
            "ex_us_dividend_yield": _reading(readings.ex_us_dividend_yield),
            "relative_cape": _reading(readings.relative_cape),
            "long_run_log_median": _reading(readings.long_run_log_median),
            "log_spread_sd": _reading(readings.log_spread_sd),
            "cap_weight_us": _reading(readings.cap_weight_us),
        },
        "moments": None
        if moments is None
        else {
            "window": [moments.first_month, moments.last_month],
            "months": moments.months,
            "us_volatility": moments.us_volatility,
            "ex_us_volatility": moments.ex_us_volatility,
            "correlation": moments.correlation,
        },
        "current_us_share": CURRENT_US_SHARE,
        "contribution_rates": list(CONTRIBUTION_RATES),
    }


# --------------------------------------------------------------------------- report


def _rule(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def _pp(value: float) -> str:
    return f"{100 * value:+.2f}"


def _central(table: RegretTable, state: str) -> Scenario:
    return next(
        s
        for s in table.scenarios
        if s.rerating == state and s.growth_differential == 0.0 and s.currency_leg == 0.0
    )


def _print_inputs(readings: Readings, moments: RelativeMoments) -> None:
    _rule("INPUTS, each with its as-of date")
    for name, reading in (
        ("US dividend yield", readings.us_dividend_yield),
        ("ex-US dividend yield", readings.ex_us_dividend_yield),
        ("relative CAPE, US / developed ex-US", readings.relative_cape),
        ("long-run median of the log spread", readings.long_run_log_median),
        ("standard deviation of the log spread", readings.log_spread_sd),
        ("cap-weight US share", readings.cap_weight_us),
    ):
        print(f"  {name:<40} {reading.value:>9.4f}  as of {reading.as_of}  ({reading.source})")
    print(
        f"  current log premium {readings.current_log_premium:+.3f}; gap to the median "
        f"{readings.long_run_log_median.value - readings.current_log_premium:+.3f}; "
        f"yield differential {_pp(readings.yield_differential)} pp/yr"
    )
    print(
        f"  French {US_FILE} and {EX_US_FILE}, Mkt-RF + RF, {moments.first_month}..."
        f"{moments.last_month}, {moments.months} months: US vol {moments.us_volatility:.2%}, "
        f"ex-US vol {moments.ex_us_volatility:.2%}, correlation {moments.correlation:.3f}, "
        f"relative vol {moments.relative_volatility:.2%}, minimum-variance split "
        f"{moments.minimum_variance_split:.3f}"
    )


def _print_scenarios(readings: Readings) -> None:
    _rule("SCENARIOS: implied US minus ex-US differential, pp/yr")
    print("  re-rating   log change   10y: /yr   30y: /yr   | central cell d at 10y, 30y")
    for state in RERATING_STATES:
        delta = readings.rerating_log_change(state)
        central = Scenario(rerating=state, growth_differential=0.0, currency_leg=0.0)
        print(
            f"  {state:<10} {delta:+9.3f}  {_pp(delta / 10):>9}  {_pp(delta / 30):>9}   | "
            f"{_pp(implied_differential(readings, central, horizon_years=10)):>7}  "
            f"{_pp(implied_differential(readings, central, horizon_years=30)):>7}"
        )
    print("  growth differential adds its value; the currency leg subtracts its value.")


def _print_table(table: RegretTable, priors: Sequence[ReratingPrior]) -> None:
    years = int(table.horizon_years)
    _rule(f"REGRET IN TERMINAL LOG WEALTH OVER {years} YEARS, log points x 100")
    header = "  split  TE bp/yr | " + " ".join(f"{s:>8}" for s in RERATING_STATES)
    header += " |  max   worst scenario"
    for prior in priors:
        header += f" | E[{prior.label}]"
    print(header)
    print("  (state columns are the central cell: growth 0, currency 0)")
    expectations = [table.expected_regret(prior) for prior in priors]
    for i, split in enumerate(table.splits):
        cells = " ".join(
            f"{100 * table.regret_at(split, _central(table, s)):8.1f}" for s in RERATING_STATES
        )
        worst = table.worst_scenario(split)
        line = (
            f"  {split:.2f}  {1e4 * table.tracking_error[i]:8.0f} | {cells} | "
            f"{100 * table.max_regret[i]:5.1f}  {worst.label:<40}"
        )
        for expected in expectations:
            line += f" | {100 * expected[i]:6.1f}"
        print(line)
    print(
        f"  minimax split {table.minimax_split:.2f} at max regret "
        f"{100 * table.minimax_regret:.1f} ({100 * (1 - math.exp(-table.minimax_regret)):.1f}% "
        f"of terminal wealth, {1e4 * table.minimax_regret / years:.0f} bp/yr)"
    )
    for prior in priors:
        print(
            f"  expected-regret split under the {prior.label} prior: "
            f"{table.bayes_split(prior):.2f}"
        )
    best = sorted(set(table.best_split))
    print(f"  best split by scenario takes the values {best}")


def _print_sweep(
    table: RegretTable, readings: Readings, moments: RelativeMoments
) -> dict[str, float]:
    years = int(table.horizon_years)
    _rule(f"SENSITIVITY TO THE PRIOR WEIGHT ON REVERSION, {years} years")
    points = bayes_split_sweep(table, readings, moments, reversion_weights=SWEEP)
    print("  weight on reversion   E[d] pp/yr   unconstrained s*   grid split")
    for point in points:
        print(
            f"  {point.reversion_weight:>19.2f}   {_pp(point.expected_differential):>10}   "
            f"{point.unconstrained_split:>16.2f}   {point.bayes_split:>10.2f}"
        )
    slope = (
        100.0
        * (points[-1].unconstrained_split - points[0].unconstrained_split)
        / (points[-1].reversion_weight - points[0].reversion_weight)
    )
    switches = [
        (a.reversion_weight, b.reversion_weight)
        for a, b in pairwise(points)
        if a.bayes_split != b.bayes_split
    ]
    print(
        f"  unconstrained split moves {slope:+.0f} points per unit of prior weight on "
        f"reversion ({slope / 10:+.1f} points per 0.1)"
    )
    if switches:
        print(f"  the grid answer steps between {switches}")
    else:
        print("  the grid answer does not move anywhere on the sweep")
    growth_one = Scenario(rerating="hold", growth_differential=0.01, currency_leg=0.0)
    print(
        "  under 'hold' with the century-average +1 pp growth edge, d = "
        f"{_pp(implied_differential(readings, growth_one, horizon_years=years))} pp/yr"
    )
    return {"slope_points_per_unit": slope}


def _print_contributions() -> None:
    _rule("YEARS OF CONTRIBUTIONS TO REACH EACH SPLIT FROM 64/36, growth ignored")
    print("  all new equity money to the under-weight side; in brackets, 70% of it")
    print("  split | " + " | ".join(f"{100 * c:.0f}%/yr" for c in CONTRIBUTION_RATES))
    for split in SPLITS:
        cells = []
        for rate in CONTRIBUTION_RATES:
            full = years_to_reach(
                current_us_share=CURRENT_US_SHARE, target_us_share=split, contribution_rate=rate
            )
            part = years_to_reach(
                current_us_share=CURRENT_US_SHARE,
                target_us_share=split,
                contribution_rate=rate,
                share_of_contributions=0.7,
            )
            cells.append(f"{full:4.1f} ({part:4.1f})")
        print(f"  {split:.2f}  | " + " | ".join(cells))


def _run(readings: Readings, moments: RelativeMoments) -> dict[str, JsonValue]:
    _print_inputs(readings, moments)
    _print_scenarios(readings)
    summary: dict[str, JsonValue] = {}
    priors = (EQUAL_PRIOR, REVERSION_PRIOR)
    for years in HORIZONS:
        table = regret_table(readings, moments, horizon_years=years)
        _print_table(table, priors)
        sweep = _print_sweep(table, readings, moments)
        summary[f"{years}y"] = {
            "minimax_split": table.minimax_split,
            "minimax_regret": table.minimax_regret,
            "bayes_split_equal": table.bayes_split(EQUAL_PRIOR),
            "bayes_split_reversion": table.bayes_split(REVERSION_PRIOR),
            "expected_differential_equal": expected_differential(
                readings, EQUAL_PRIOR, horizon_years=years
            ),
            "unconstrained_split_equal": growth_optimal_split(
                expected_differential(readings, EQUAL_PRIOR, horizon_years=years), moments
            ),
            **sweep,
        }
    _print_contributions()
    return summary


def main() -> None:
    print("=" * 78)
    print("THE US/INTERNATIONAL SPLIT AS A REGRET DECISION: a study, exploratory throughout")
    print("=" * 78)
    cache = RawCache()
    ledger = Ledger()
    run_id = new_run_id()
    hashes: dict[str, str] = {}
    for name in (US_FILE, EX_US_FILE):
        hashes[name] = cache.require(french.get_dataset(name).url).sha256
    hashes["jst_macrohistory_r6"] = cache.require(jst_dataset("jst_macrohistory_r6").url).sha256
    hashes["shiller_ie_data"] = cache.require(shiller.get_dataset("shiller_ie_data").url).sha256
    ledger.append(
        _entry(
            run_id=run_id,
            event=LedgerEvent.STARTED,
            status=RunStatus.STARTED,
            hashes=hashes,
            parameters=_parameters(None, None),
            notes="study; no frozen specification; scenario anchors chosen after §5 was read",
        )
    )
    try:
        readings, _ = load_readings(cache)
        moments, _ = load_moments(cache)
        summary = _run(readings, moments)
    except Exception as exc:
        ledger.append(
            _entry(
                run_id=run_id,
                event=LedgerEvent.FAILED,
                status=RunStatus.FAILED,
                hashes=hashes,
                parameters=_parameters(None, None),
                failure_reason=f"{type(exc).__name__}: {exc}",
            )
        )
        traceback.print_exc()
        raise
    parameters = _parameters(readings, moments)
    assert isinstance(parameters, dict)
    parameters["summary"] = summary
    ledger.append(
        _entry(
            run_id=run_id,
            event=LedgerEvent.SUCCEEDED,
            status=RunStatus.SUCCEEDED,
            hashes=hashes,
            parameters=parameters,
            result_status=ResultStatus.EXPLORATORY,
            notes=(
                "printed to stdout; interpreted in "
                "docs/research/valuation-and-the-allocation.md §5.7"
            ),
        )
    )
    print(f"\n  ledger: run {run_id} recorded under family {FAMILY}.")
