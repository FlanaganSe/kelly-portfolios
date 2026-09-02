"""Regenerates the ITAN section of ``docs/research/untested-tilt-candidates.md``.

Kept separate from :mod:`portfolio_edge.studies.itan_substitution` so the arithmetic stays
pure and testable and only this file touches the cache, exactly as
:mod:`portfolio_edge.studies._untested_tilts_tables` is kept beside ``untested_tilts``.
Run it with::

    uv run python -m portfolio_edge.studies.itan_substitution

**Everything here is `exploratory`.** No specification was frozen before these numbers
were seen. Because the window, the incumbent, the premium scenarios and the choice of
VTI's filed return as the market leg are hypothesis-bearing analytical choices, every run
appends ``started`` and ``succeeded`` (or ``failed``) entries to the ledger under the
family :data:`FAMILY`, through :class:`portfolio_edge.experiments.ledger.Ledger` and never
by hand.

The question it answers
-----------------------
``docs/research/discovery-sweep-2026-09.md`` proposes VTV 15 becoming VTV 10 + ITAN 5 and
names the measurement: ITAN's correlation with the held value and momentum legs, and a
regression of ITAN on the French five factors plus momentum to see whether its value
exposure is positive at all or whether the label covers growth. This module runs exactly
that, then scores the substitution the way the page scores its other candidates.

Two design choices carry the conditioning step.

**A partial replacement is scored against the portfolio that would exist after it.** The
page's rule for a replacement is that the displaced position is dropped from the held set
first, because a candidate's active leg is mechanically correlated with a position it
removes and a position scored against itself reads as pure overlap. Five points of VTV are
therefore taken out of the held set before the five points of ITAN are scored against what
remains. The expected-return change of the substitution itself needs no conditioning: it
is ``0.05 * sleeve_edge(ITAN - VTV)``, fitted on the difference series directly.

**The market leg is VTI's own filed return.** Every active leg is a fund less a fund, so
that ITAN is compared with what the investor would otherwise hold rather than with a
factor no fund delivers. The French market factor enters the regressions as a control.

Sources, every one already used by a registered experiment or a sibling study:

* Form N-PORT Item B.5 for ITAN, VTV, VTI, AVUV, AVDV, IDMO, VXUS, AVES and RSST via
  :mod:`portfolio_edge.data.nport`, read through the same loader
  ``_untested_tilts_tables`` uses.
* Ken French's US and developed-ex-US FF5 and momentum files, for the panels and the
  one-month bill.
* Fee and turnover from ITAN's Form 497K, securities lending from the trust's Form N-CEN,
  and the issuer's own fund page, each dated in :data:`ITAN_COST` and :data:`ITAN_NCEN`.
"""

from __future__ import annotations

import math
import traceback
from collections.abc import Mapping, Sequence
from typing import Final

import numpy as np

from portfolio_edge.data import french, nport
from portfolio_edge.data.cache import RawCache
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
from portfolio_edge.studies._loading_windows_tables import Fund, fund_returns, load_french_panel
from portfolio_edge.studies._untested_tilts_tables import (
    AVES_EDGE,
    COSTS,
    FUNDS,
    PREMIA,
    PREMIUM_MDE80,
    PRICED,
    TREND_EDGE,
    Regression,
    difference,
    longest_contiguous_run,
    periods_between,
    regress,
)
from portfolio_edge.studies.conditional_breadth import worst_quantile_mask
from portfolio_edge.studies.itan_substitution import (
    PUBLISHED_VECTOR,
    SUBSTITUTION_WEIGHT,
    NcenLendingYear,
    lending_median_bp,
    substitution_return_change,
    tracking_error_after_substitution,
    vector_after_substitution,
)
from portfolio_edge.studies.untested_tilts import (
    FundCost,
    edge_standard_error,
    incremental_cost_bracket,
    marginal_tilt,
    sleeve_edge,
    tracking_error_from_monthly,
)

FAMILY: Final = "study_itan_substitution"

#: Series and class identifiers from ``https://www.sec.gov/files/company_tickers_mf.json``
#: (read 2026-09-02). ITAN commenced 2021-06-28, so its first filed month is a stub whose
#: Item B.5 return is 0.00% and is dropped by the same launch-cut rule the Avantis funds get.
ITAN: Final = Fund(
    ticker="ITAN", series_id="S000072323", class_id="C000228450", inception="2021-06-28"
)

#: Form N-CEN Item C.6.g (net income from securities lending) over Item C.2 (monthly
#: average net assets), dollars, one row per fiscal year the series has filed. Read from
#: EDGAR on 2026-09-02; the trust (CIK 1592900) files one N-CEN for every series with a
#: May fiscal year end.
ITAN_NCEN: Final[tuple[NcenLendingYear, ...]] = (
    NcenLendingYear(
        fiscal_year_end="2022-05-31", net_income=6.00, average_net_assets=2_598_304.24
    ),
    NcenLendingYear(
        fiscal_year_end="2023-05-31", net_income=1_332.78, average_net_assets=9_831_388.54
    ),
    NcenLendingYear(
        fiscal_year_end="2024-05-31", net_income=266.00, average_net_assets=30_463_140.63
    ),
    NcenLendingYear(
        fiscal_year_end="2025-05-31", net_income=175.67, average_net_assets=36_955_931.83
    ),
    NcenLendingYear(
        fiscal_year_end="2026-05-31", net_income=5.03, average_net_assets=61_182_308.765
    ),
)

#: Fee and turnover from ITAN's Form 497K dated 2025-09-30 (fiscal year to 2025-05-31);
#: lending is :func:`lending_median_bp` over :data:`ITAN_NCEN`.
ITAN_COST: Final = FundCost(
    ticker="ITAN",
    fee_bp=50.0,
    securities_lending_bp=lending_median_bp(ITAN_NCEN),
    turnover_percent=31.0,
)

#: Which cheap fund each active position is measured against.
INCUMBENT: Final[Mapping[str, str]] = {
    "RSST": "VTI",
    "VTV": "VTI",
    "AVDV": "VXUS",
    "IDMO": "VXUS",
    "AVES": "VXUS",
    "AVUV": "VTI",
    "ITAN": "VTI",
}

#: The active positions in the published vector, by weight of capital.
HELD: Final[Mapping[str, float]] = {
    ticker: weight for ticker, weight in PUBLISHED_VECTOR.items() if ticker in INCUMBENT
}

#: The vector after the substitution, and the active positions that remain once the five
#: displaced points of VTV are removed and before the five points of ITAN arrive.
PROPOSED_VECTOR: Final[Mapping[str, float]] = vector_after_substitution(
    PUBLISHED_VECTOR, sell="VTV", buy="ITAN", weight=SUBSTITUTION_WEIGHT
)
HELD_AFTER: Final[Mapping[str, float]] = {
    ticker: weight
    for ticker, weight in PROPOSED_VECTOR.items()
    if ticker in INCUMBENT and ticker != "ITAN"
}

#: The widest span asked for; the run-finder narrows it to the longest gapless run.
FIRST: Final = "2021-07"
LAST: Final = "2026-06"

#: The worst-decile condition, on VTI's own filed return.
WORST_QUANTILE: Final = 0.10

_Z95: Final = 1.959963984540054


def load_returns(cache: RawCache) -> dict[str, dict[str, float]]:
    """Filed Item B.5 monthly returns for ITAN and every fund the vector holds."""
    wanted = {"VTI", "VTV", "VXUS", "AVUV", "AVDV", "IDMO", "AVES", "RSST"}
    returns = {fund.ticker: fund_returns(cache, fund) for fund in FUNDS if fund.ticker in wanted}
    returns["ITAN"] = fund_returns(cache, ITAN)
    return returns


def active_leg(
    returns: Mapping[str, Mapping[str, float]], ticker: str, months: Sequence[str]
) -> np.ndarray:
    incumbent = INCUMBENT[ticker]
    return np.array(
        [returns[ticker][m] - returns[incumbent][m] for m in months], dtype=np.float64
    )


def shared_months(
    returns: Mapping[str, Mapping[str, float]], tickers: Sequence[str]
) -> tuple[str, ...]:
    needed = set(tickers) | {INCUMBENT[t] for t in tickers if t in INCUMBENT}
    return longest_contiguous_run(
        [m for m in periods_between(FIRST, LAST) if all(m in returns[t] for t in needed)]
    )


def correlation_interval(rho: float, n: int) -> tuple[float, float]:
    """Fisher-z 95% interval, for a reader who wants to know what five months can say."""
    if n <= 3:
        return -1.0, 1.0
    z = math.atanh(max(min(rho, 0.999999), -0.999999))
    half = _Z95 / math.sqrt(n - 3)
    return math.tanh(z - half), math.tanh(z + half)


def digests(cache: RawCache) -> dict[str, str]:
    """Hashes of the inputs: the French files and each fund's EDGAR filing index."""
    out: dict[str, str] = {}
    for name in (
        "french_us_ff5",
        "french_us_momentum",
        "french_developed_ex_us_ff5",
        "french_developed_ex_us_momentum",
    ):
        out[name] = cache.require(french.get_dataset(name).url).sha256
    for fund in (ITAN, *FUNDS):
        entry = cache.entry_for(nport.browse_edgar_url(fund.series_id))
        if entry is not None:
            out[f"nport_index_{fund.ticker.lower()}"] = entry.sha256
    return out


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


def _parameters(windows: Mapping[str, str]) -> JsonValue:
    return {
        "study": "VTV 15 becomes VTV 10 + ITAN 5 inside the published vector",
        "frozen_specification": None,
        "candidate": {
            "ticker": ITAN.ticker,
            "series_id": ITAN.series_id,
            "class_id": ITAN.class_id,
        },
        "incumbent": "VTV",
        "market_leg": "VTI filed Item B.5 return",
        "panel": "french_us_ff5 + french_us_momentum",
        "weight_moved": SUBSTITUTION_WEIGHT,
        "published_vector": dict(PUBLISHED_VECTOR),
        "cost": {
            "fee_bp": ITAN_COST.fee_bp,
            "lending_bp_median": ITAN_COST.securities_lending_bp,
            "turnover_percent": ITAN_COST.turnover_percent,
            "ncen_fiscal_years": [y.fiscal_year_end for y in ITAN_NCEN],
        },
        "premium_scenarios": list(PREMIA),
        "worst_quantile": WORST_QUANTILE,
        "windows": dict(windows),
    }


# --------------------------------------------------------------------------- report


def _rule(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def _print_regression(report: Regression) -> None:
    low, high = report.alpha_interval
    print(
        f"  {report.label:<12} n={report.months:>3} {report.window.label} extra return "
        f"{report.alpha:+6.2f} [{low:+6.2f}, {high:+6.2f}] pp/yr, smallest detectable "
        f"{report.alpha_minimum_detectable:.2f}"
    )
    for factor in ("Mkt-RF", *PRICED):
        print(f"      {factor:<7}{report.loadings[factor].format()}")


def _own_panel_edge(fit: Regression, *, fund: str, incumbent: str) -> float:
    """Own-panel sleeve edge at the worse end of the cost bracket, pp/yr per dollar."""
    cost = ITAN_COST if fund == "ITAN" else COSTS[fund]
    _, high = incremental_cost_bracket(fund=cost, incumbent=COSTS[incumbent])
    return sleeve_edge(
        delivered=fit.delivered(), premia=PREMIA["own-panel"][fit.panel], incremental_cost=high
    )


def _run(cache: RawCache) -> dict[str, str]:
    panels = {
        "us": load_french_panel(cache, "us"),
        "exus": load_french_panel(cache, "developed_ex_us"),
    }
    returns = load_returns(cache)
    windows: dict[str, str] = {}

    _rule("0. What was filed")
    filed = sorted(returns["ITAN"])
    run = longest_contiguous_run(filed)
    missing = [m for m in periods_between(filed[0], filed[-1]) if m not in returns["ITAN"]]
    print(
        f"  ITAN filed {len(filed)} whole months {filed[0]}..{filed[-1]} after the launch "
        f"stub; {len(missing)} inside that span have no filed return: {', '.join(missing)}."
    )
    print(f"  Longest gapless run: {len(run)} months {run[0]}..{run[-1]}. Every fit is on it.")

    _rule("1. Loadings: ITAN alone, ITAN over VTV, ITAN over VTI, and VTV over VTI beside them")
    fits: dict[str, Regression] = {}
    for label, weights, subtract_cash in (
        ("ITAN", {"ITAN": 1.0}, True),
        ("ITAN-VTV", {"ITAN": 1.0, "VTV": -1.0}, False),
        ("ITAN-VTI", {"ITAN": 1.0, "VTI": -1.0}, False),
    ):
        fits[label] = regress(
            label=label,
            panel=panels["us"],
            panel_name="us",
            series=difference(returns, weights),
            first=FIRST,
            last=LAST,
            subtract_cash=subtract_cash,
        )
        windows[label] = fits[label].window.label
        _print_regression(fits[label])
    fits["VTV-VTI"] = regress(
        label="VTV-VTI",
        panel=panels["us"],
        panel_name="us",
        series=difference(returns, {"VTV": 1.0, "VTI": -1.0}),
        first=fits["ITAN-VTV"].window.first,
        last=fits["ITAN-VTV"].window.last,
        subtract_cash=False,
    )
    _print_regression(fits["VTV-VTI"])
    print(
        "  Each row is a fund less a fund on VTI's or VTV's filed return; the market factor "
        "is a control, not the market leg. VTV-VTI is fitted on ITAN's months."
    )

    _rule("2. Overlap: ITAN's active leg against the value and momentum legs held")
    months = shared_months(returns, ("ITAN", "VTV", "AVUV", "AVDV", "IDMO"))
    windows["overlap"] = f"{months[0]}..{months[-1]}"
    itan = active_leg(returns, "ITAN", months)
    market = np.array([returns["VTI"][m] for m in months])
    worst = worst_quantile_mask(market, quantile=WORST_QUANTILE)
    stressed = [months[i] for i in np.flatnonzero(worst)]
    count = int(worst.sum())
    print(
        f"  n={len(months)} {months[0]}..{months[-1]}; worst-decile VTI months "
        f"({count}): {', '.join(stressed)}"
    )
    print(f"  {'':<8}{'full sample':>22}{'worst decile':>26}")
    for other in ("VTV", "AVUV", "AVDV", "IDMO"):
        leg = active_leg(returns, other, months)
        full = float(np.corrcoef(itan, leg)[0, 1])
        bad = float(np.corrcoef(itan[worst], leg[worst])[0, 1])
        flo, fhi = correlation_interval(full, len(months))
        blo, bhi = correlation_interval(bad, count)
        print(
            f"  {other:<8}{full:>+7.3f} [{flo:+.2f}, {fhi:+.2f}]"
            f"{bad:>+11.3f} [{blo:+.2f}, {bhi:+.2f}]"
        )
    print(
        "  Active legs are fund minus its cheap incumbent (VTI for the US funds, VXUS for "
        f"AVDV and IDMO). A worst-decile figure rests on {count} months; its interval says so."
    )

    _rule("3. Cost, from ITAN's own filings")
    low_cost, high_cost = incremental_cost_bracket(fund=ITAN_COST, incumbent=COSTS["VTV"])
    years = ", ".join(f"{y.fiscal_year_end[:4]} {y.basis_points:.3f}" for y in ITAN_NCEN)
    print(
        f"  Fee {ITAN_COST.fee_bp:.0f} bp (497K 2025-09-30); lending median "
        f"{ITAN_COST.securities_lending_bp:.3f} bp over {len(ITAN_NCEN)} N-CEN fiscal years "
        f"({years}); net cost {ITAN_COST.net_cost_bp:.2f} bp against VTV's "
        f"{COSTS['VTV'].net_cost_bp:.2f}."
    )
    print(
        f"  Turnover {ITAN_COST.turnover_percent:.0f}%/yr (fiscal year to 2025-05-31) against "
        f"VTV's {COSTS['VTV'].turnover_percent:.0f}% -> incremental cost {low_cost:.3f} to "
        f"{high_cost:.3f} pp/yr per dollar moved."
    )

    _rule("4. The substitution, VTV 15 -> VTV 10 + ITAN 5, across four premium scenarios")
    delivered = fits["ITAN-VTV"].delivered()
    error = edge_standard_error(delivered=delivered, minimum_detectable_premia=PREMIUM_MDE80["us"])
    print("  delivered over VTV: " + ", ".join(f"{k} {v:+.3f}" for k, v in delivered.items()))
    print(f"  premium standard error on the edge: {error:.2f} pp/yr per dollar")
    print(f"  {'scenario':<11}{'per dollar moved, pp/yr':>26}{'portfolio, % a year':>24}")
    edges: dict[str, tuple[float, float]] = {}
    for scenario, table in PREMIA.items():
        worst_edge = sleeve_edge(
            delivered=delivered, premia=table["us"], incremental_cost=high_cost
        )
        best_edge = sleeve_edge(
            delivered=delivered, premia=table["us"], incremental_cost=low_cost
        )
        edges[scenario] = (worst_edge, best_edge)
        worst_pf = substitution_return_change(
            weight=SUBSTITUTION_WEIGHT,
            delivered=delivered,
            premia=table["us"],
            incremental_cost=high_cost,
        )
        best_pf = substitution_return_change(
            weight=SUBSTITUTION_WEIGHT,
            delivered=delivered,
            premia=table["us"],
            incremental_cost=low_cost,
        )
        print(
            f"  {scenario:<11}{worst_edge:>+11.3f} to {best_edge:+.3f}"
            f"{worst_pf:>+15.3f} to {best_pf:+.3f}"
        )
    gross = {f: delivered[f] * PREMIA["own-panel"]["us"][f] for f in PRICED}
    print(
        "  own-panel gross by factor, pp/yr per dollar: "
        + ", ".join(f"{k} {v:+.3f}" for k, v in gross.items())
        + f"; sum {sum(gross.values()):+.3f}"
    )

    _rule("5. Given what the vector would hold after the substitution")
    exus_fits = {
        ticker: regress(
            label=f"{ticker}-VXUS",
            panel=panels["exus"],
            panel_name="exus",
            series=difference(returns, {ticker: 1.0, "VXUS": -1.0}),
            first="2019-10",
            last=LAST,
            subtract_cash=False,
        )
        for ticker in ("AVDV", "IDMO")
    }
    held_edges = {
        "RSST": TREND_EDGE,
        "VTV": _own_panel_edge(fits["VTV-VTI"], fund="VTV", incumbent="VTI"),
        "AVDV": _own_panel_edge(exus_fits["AVDV"], fund="AVDV", incumbent="VXUS"),
        "IDMO": _own_panel_edge(exus_fits["IDMO"], fund="IDMO", incumbent="VXUS"),
        "AVES": AVES_EDGE,
    }
    print(
        "  held active edges, own-panel, worse end of each cost bracket, pp/yr per dollar: "
        + ", ".join(f"{k} {v:+.3f}" for k, v in held_edges.items())
        + "\n  (AVES and the trend leg carried, not fitted). Held set for scoring: "
        + ", ".join(f"{k} {v:.0%}" for k, v in HELD_AFTER.items())
        + " (the five displaced points of VTV removed first)."
    )
    arriving = _own_panel_edge(fits["ITAN-VTI"], fund="ITAN", incumbent="VTI")
    leaving = held_edges["VTV"]
    print(
        f"  standalone edges over VTI, pp/yr per dollar: ITAN {arriving:+.3f}, VTV {leaving:+.3f}; "
        f"difference {arriving - leaving:+.3f} against {edges['own-panel'][0]:+.3f} fitted "
        "directly on ITAN-VTV"
    )
    for label, members in (
        ("with the trend wrapper", tuple(HELD_AFTER)),
        ("without it, on more months", tuple(t for t in HELD_AFTER if t != "RSST")),
    ):
        shared = shared_months(returns, ("ITAN", "VTV", *members))
        windows[f"held {label}"] = f"{shared[0]}..{shared[-1]}"
        held = sum(
            (HELD_AFTER[t] * active_leg(returns, t, shared) for t in members),
            start=np.zeros(len(shared)),
        )
        held_te = tracking_error_from_monthly(float(np.std(held, ddof=1)))
        held_edge = sum(HELD_AFTER[t] * held_edges[t] for t in members)
        leg = active_leg(returns, "ITAN", shared)
        leg_te = tracking_error_from_monthly(float(np.std(leg, ddof=1)))
        rho = float(np.corrcoef(leg, held)[0, 1])
        verdict = marginal_tilt(
            ticker="ITAN over VTI",
            weight=SUBSTITUTION_WEIGHT,
            candidate_edge=arriving,
            candidate_tracking_error=leg_te,
            held_edge=held_edge,
            held_tracking_error=held_te,
            correlation_to_held=rho,
        )
        before_after = []
        for ticker in ("VTV", "ITAN"):
            moved = active_leg(returns, ticker, shared)
            before_after.append(
                tracking_error_after_substitution(
                    held_tracking_error=held_te,
                    weight=SUBSTITUTION_WEIGHT,
                    candidate_tracking_error=tracking_error_from_monthly(
                        float(np.std(moved, ddof=1))
                    ),
                    correlation=float(np.corrcoef(moved, held)[0, 1]),
                )
            )
        before, after = before_after
        print(
            f"\n  -- {label}: n={len(shared)} {shared[0]}..{shared[-1]}; held tracking error "
            f"{held_te:.2f} pp/yr, held edge {held_edge:+.3f}\n"
            f"     ITAN over VTI at 5%: own tracking error {leg_te:.2f}, rho to held "
            f"{rho:+.3f}, standalone {arriving:+.3f}, marginal {verdict.alpha:+.3f} pp/yr per "
            f"dollar\n"
            f"     active tracking error, published vector {before:.2f} -> proposed {after:.2f}, "
            f"{after - before:+.2f} pp/yr"
        )
    print(
        "  The five points of VTV that leave are not scored against a held set that still\n"
        "  holds VTV: a position measured against itself reads as pure overlap, which is the\n"
        "  artefact the page's replacement rule exists to avoid."
    )

    _rule("6. The headline, and the vector it implies")
    print(
        "  Centre is the own-panel premia at the worse end of the cost bracket, fitted on\n"
        "  ITAN-VTV directly. The range carries the premia's own standard error at 95%; the\n"
        "  null column is what the move costs if every premium turns out to be zero."
    )
    for weight in (SUBSTITUTION_WEIGHT, 0.10, 0.15):
        centre = weight * edges["own-panel"][0]
        low = weight * (edges["own-panel"][0] - _Z95 * error)
        high = weight * (edges["own-panel"][0] + _Z95 * error)
        null = weight * edges["null"][0]
        print(
            f"  move {weight:.0%} of capital VTV -> ITAN: {centre:+.3f}% a year "
            f"[{low:+.3f}%, {high:+.3f}%], {null:+.3f}% if every premium is zero"
        )
    print("  proposed vector: " + ", ".join(f"{k} {v:.0%}" for k, v in PROPOSED_VECTOR.items()))
    print(
        "  Every interval above carries premium uncertainty only; the loadings' own sampling\n"
        "  error and the 54-month window are reported beside them, not folded in."
    )
    return windows


def main() -> None:
    print("=" * 78)
    print("ITAN IN PLACE OF FIVE POINTS OF VTV: a study, exploratory throughout")
    print("=" * 78)
    cache = RawCache()
    hashes = digests(cache)
    ledger = Ledger()
    run_id = new_run_id()
    ledger.append(
        _entry(
            run_id=run_id,
            event=LedgerEvent.STARTED,
            status=RunStatus.STARTED,
            hashes=hashes,
            parameters=_parameters({}),
            notes="study; no frozen specification; window and incumbent chosen after the sweep",
        )
    )
    try:
        windows = _run(cache)
    except Exception as exc:
        ledger.append(
            _entry(
                run_id=run_id,
                event=LedgerEvent.FAILED,
                status=RunStatus.FAILED,
                hashes=hashes,
                parameters=_parameters({}),
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
            hashes=digests(cache),
            parameters=_parameters(windows),
            result_status=ResultStatus.EXPLORATORY,
            notes="printed to stdout; interpreted in docs/research/untested-tilt-candidates.md §7",
        )
    )
    print(f"\n  ledger: run {run_id} recorded under family {FAMILY}.")


if __name__ == "__main__":
    main()
