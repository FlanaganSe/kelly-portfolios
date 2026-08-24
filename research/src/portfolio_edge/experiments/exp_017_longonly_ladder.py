"""Experiment 017: how many correlated strategies a long-only optimiser actually holds.

Runs the weight-space search behind the sentence the public `/stacking` page quotes most
often — *the best long-only portfolio holds three strategies and never improves past
three* — under a frozen specification, through the runner, and into the ledger. Before
this experiment that sentence came from a worked example with no specification, no ledger
entry and no committed code, which the root working agreement does not permit for a
weight-space search however cheap the search is.

**This experiment reads no market data.** Every candidate edge is an assumption declared
in ``experiments/exp_017_longonly_ladder.yaml``; the one measured number carried in is the
0.435 correlation among the candidate portfolio's own active sleeves, and it arrives as a
parameter rather than as a re-measurement. Nothing here can supply evidence about markets.
What it supplies is reproducibility: the argument now has a hash, a grid declared before
the answer was seen, and a committed artifact.

The arithmetic lives in :mod:`portfolio_edge.studies.longonly_ladder`, which is unit
tested against a hand-derived two-candidate closed form, against an independent
enumeration written inside the test, and against a dense Dirichlet search that can only
falsify the optimum and never set it. This module contributes the frozen grid, the four
hostile tests the specification names, and the report.
"""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from portfolio_edge.experiments.ledger import Ledger, Origin
from portfolio_edge.experiments.registry import ExperimentRegistry, RunContext
from portfolio_edge.experiments.result import (
    CostBasis,
    Estimate,
    ExperimentResult,
    ResultStatus,
)
from portfolio_edge.experiments.runner import RunOutcome, run_experiment
from portfolio_edge.experiments.specification import (
    JsonValue,
    Specification,
    load_specification,
)
from portfolio_edge.studies.longonly_ladder import (
    correlation_sweep,
    equicorrelated_matrix,
    ladder,
    long_only_maximum,
    unconstrained_weights,
)
from portfolio_edge.studies.stacking import correlation_to_covariance

__all__ = [
    "ENTRY_POINT",
    "build_registry",
    "default_specification_path",
    "main",
    "run",
    "workspace_root",
]

ENTRY_POINT: Final = "exp_017_longonly_ladder"

#: The specification's own tolerance for the hostile check on the optimiser. A Dirichlet
#: search that beats the exact enumeration by more than this voids the run rather than
#: being absorbed into it.
_SIMPLEX_TOLERANCE: Final = 1e-9


class LadderRunError(RuntimeError):
    """A hostile test declared in the specification failed, so the run is void."""


def workspace_root() -> Path:
    """``research/``, resolved from this module's location."""
    return Path(__file__).resolve().parents[3]


def default_specification_path() -> Path:
    return workspace_root() / "experiments" / "exp_017_longonly_ladder.yaml"


def build_registry() -> ExperimentRegistry:
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    return registry


def _mapping(value: JsonValue, *, where: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise LadderRunError(f"{where} must be a mapping, got {type(value).__name__}")
    return value


def _floats(value: JsonValue, *, where: str) -> tuple[float, ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise LadderRunError(f"{where} must be a list of numbers")
    out: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, int | float):
            raise LadderRunError(f"{where} must contain numbers, found {item!r}")
        out.append(float(item))
    return tuple(out)


def _ints(value: JsonValue, *, where: str) -> tuple[int, ...]:
    return tuple(int(one) for one in _floats(value, where=where))


def _float(value: JsonValue, *, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise LadderRunError(f"{where} must be a number, got {value!r}")
    return float(value)


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Score the frozen ladder, run the declared hostile tests, and report every cell."""
    parameters = _mapping(specification.parameters, where="parameters")
    edges = _floats(parameters["gross_edges"], where="parameters.gross_edges")
    cost = _float(
        parameters["cost_percentage_points_per_year"],
        where="parameters.cost_percentage_points_per_year",
    )
    costs = _floats(parameters["cost_sensitivity"], where="parameters.cost_sensitivity")
    tracking_error = _float(
        parameters["tracking_error_percentage_points_per_year"],
        where="parameters.tracking_error_percentage_points_per_year",
    )
    headline_correlation = _float(
        parameters["headline_correlation"], where="parameters.headline_correlation"
    )
    correlation_grid = _floats(
        parameters["correlation_grid"], where="parameters.correlation_grid"
    )
    reported_sizes = _ints(
        parameters["reported_shelf_sizes"], where="parameters.reported_shelf_sizes"
    )
    dispersion = _mapping(
        parameters["dispersion_settings"], where="parameters.dispersion_settings"
    )
    horizon = _float(
        parameters["probability_horizon_years"],
        where="parameters.probability_horizon_years",
    )

    rungs = ladder(
        edges,
        cost=cost,
        tracking_error=tracking_error,
        correlation=headline_correlation,
    )
    by_count = {rung.count: rung for rung in rungs}

    # ---- the equal-weighted optimum, at each declared cost -------------------------
    cost_optima: dict[str, int] = {}
    cost_frame_rows: list[dict[str, float]] = []
    for charge in costs:
        column = ladder(
            edges,
            cost=charge,
            tracking_error=tracking_error,
            correlation=headline_correlation,
        )
        best = max(column, key=lambda rung: rung.equal_weight_information_ratio)
        cost_optima[f"{charge:.2f}"] = best.count
        for rung in column:
            cost_frame_rows.append(
                {
                    "cost_pp_per_year": charge,
                    "count": float(rung.count),
                    "equal_weight_ir": rung.equal_weight_information_ratio,
                }
            )

    # ---- hostile test (a): identical edges -----------------------------------------
    identical = _floats(dispersion["identical"], where="parameters.dispersion_settings.identical")
    identical_rung = ladder(
        identical,
        cost=cost,
        tracking_error=tracking_error,
        correlation=headline_correlation,
        counts=(len(identical),),
    )[0]
    if identical_rung.sleeves_held != len(identical):
        raise LadderRunError(
            "the identical-edge case must hold every candidate; it held "
            f"{identical_rung.sleeves_held} of {len(identical)}. The implementation is "
            "wrong and the run is void."
        )
    if abs(identical_rung.long_only_transfer_coefficient - 1.0) > 1e-9:
        raise LadderRunError(
            "the identical-edge transfer coefficient must be 1.000, got "
            f"{identical_rung.long_only_transfer_coefficient:.6f}. The run is void."
        )

    dispersion_rows: list[dict[str, float | str]] = []
    for name in ("identical", "mild", "realistic"):
        shelf = _floats(
            dispersion[name], where=f"parameters.dispersion_settings.{name}"
        )
        rung = ladder(
            shelf,
            cost=cost,
            tracking_error=tracking_error,
            correlation=headline_correlation,
            counts=(len(shelf),),
        )[0]
        dispersion_rows.append(
            {
                "dispersion": name,
                "candidates": float(len(shelf)),
                "sleeves_held": float(rung.sleeves_held),
                "transfer_coefficient": rung.long_only_transfer_coefficient,
                "long_only_ir": rung.long_only_information_ratio,
                "unconstrained_ir": rung.unconstrained_information_ratio,
            }
        )

    # ---- hostile test (b): the correlation sweep ------------------------------------
    sweep = correlation_sweep(
        edges, cost=cost, tracking_error=tracking_error, correlations=correlation_grid
    )
    held_by_correlation = [rung.sleeves_held for _, rung in sweep]
    unconstrained_by_correlation = [
        rung.unconstrained_information_ratio for _, rung in sweep
    ]
    constrained_by_correlation = [rung.long_only_information_ratio for _, rung in sweep]
    if held_by_correlation != sorted(held_by_correlation, reverse=True):
        raise LadderRunError(
            "the held count is not monotone non-increasing in correlation: "
            f"{held_by_correlation}. The specification's clause (b) rejects the claim."
        )

    # ---- hostile test (d): the dense simplex search ---------------------------------
    net = np.asarray(edges, dtype=np.float64) - cost
    correlation_matrix = equicorrelated_matrix(len(edges), headline_correlation)
    covariance = np.asarray(
        correlation_to_covariance(
            [tuple(float(x) for x in row) for row in correlation_matrix],
            [tracking_error] * len(edges),
        )
    )
    exact = long_only_maximum(tuple(float(one) for one in net), covariance)
    draws = context.rng.dirichlet(np.ones(len(edges)), size=40_000)
    numerator = draws @ net
    denominator = np.sqrt(np.einsum("ij,jk,ik->i", draws, covariance, draws))
    best_random = float(np.max(numerator / denominator))
    if best_random > exact.information_ratio + _SIMPLEX_TOLERANCE:
        raise LadderRunError(
            f"a Dirichlet search reached {best_random:.12f}, above the enumerated optimum "
            f"{exact.information_ratio:.12f}. The enumeration is wrong and the run is void."
        )
    if exact.supports_examined != 2 ** len(edges) - 1:
        raise LadderRunError(
            f"the search examined {exact.supports_examined} supports, not the "
            f"{2 ** len(edges) - 1} an exhaustive enumeration requires."
        )

    # ---- the short leg ---------------------------------------------------------------
    weights = unconstrained_weights(tuple(float(one) for one in net), covariance)
    shorts = int(np.sum(weights < 0.0))
    net_to_gross = float(weights.sum())

    # ---- units check ------------------------------------------------------------------
    in_basis_points = ladder(
        tuple(one * 100.0 for one in edges),
        cost=cost * 100.0,
        tracking_error=tracking_error * 100.0,
        correlation=headline_correlation,
        counts=(len(edges),),
    )[0]
    if in_basis_points.sleeves_held != by_count[len(edges)].sleeves_held or not math.isclose(
        in_basis_points.long_only_information_ratio,
        by_count[len(edges)].long_only_information_ratio,
        rel_tol=1e-12,
    ):
        raise LadderRunError(
            "restating the shelf in basis points changed a ratio or a count, so at least "
            "one result is a unit artefact. The run is void."
        )

    equal_optimum = max(rungs, key=lambda rung: rung.equal_weight_information_ratio)
    full = by_count[len(edges)]

    estimates = (
        Estimate(
            name="sleeves held at the long-only optimum, twelve candidates",
            value=float(full.sleeves_held),
            units="count",
            uncertainty_unavailable_reason=(
                "Deterministic given the stated ladder. Nothing is sampled, so there is "
                "no sampling distribution and an interval would be a fabrication. The "
                "declared correlation and dispersion sweeps stand in its place: the count "
                f"spans {min(held_by_correlation)} to {max(held_by_correlation)} across "
                "the correlation grid and reaches every candidate under identical edges."
            ),
            cost_basis=CostBasis.NET_OPTIMISTIC,
            notes=(
                "It is already three at three candidates and does not rise at five, "
                "eight or twelve."
            ),
        ),
        Estimate(
            name="candidates held by the best equal-weighted portfolio",
            value=float(equal_optimum.count),
            units="count",
            uncertainty_unavailable_reason="Deterministic given the stated ladder.",
            cost_basis=CostBasis.NET_OPTIMISTIC,
            notes=(
                "Unchanged at zero cost, so dilution alone produces the shape and cost "
                "only sharpens it."
            ),
        ),
        Estimate(
            name="candidates held by the best equal-weighted portfolio",
            value=float(cost_optima[f"{0.0:.2f}"]),
            units="count",
            uncertainty_unavailable_reason="Deterministic given the stated ladder.",
            cost_basis=CostBasis.GROSS,
        ),
        Estimate(
            name="candidates held by the best equal-weighted portfolio",
            value=float(cost_optima[f"{max(costs):.2f}"]),
            units="count",
            uncertainty_unavailable_reason="Deterministic given the stated ladder.",
            cost_basis=CostBasis.NET_PESSIMISTIC,
        ),
        Estimate(
            name="long-only transfer coefficient, twelve candidates",
            value=full.long_only_transfer_coefficient,
            units="ratio",
            uncertainty_unavailable_reason=(
                "Deterministic. Across the declared correlation grid it spans "
                f"{min(rung.long_only_transfer_coefficient for _, rung in sweep):.3f} to "
                f"{max(rung.long_only_transfer_coefficient for _, rung in sweep):.3f}."
            ),
            cost_basis=CostBasis.NET_OPTIMISTIC,
            notes="IR long-only over IR unconstrained, the Clarke-de Silva-Thorley ratio.",
        ),
        Estimate(
            name="long-only information ratio, twelve candidates",
            value=full.long_only_information_ratio,
            units="ratio",
            uncertainty_unavailable_reason="Deterministic given the stated ladder.",
            cost_basis=CostBasis.NET_OPTIMISTIC,
        ),
        Estimate(
            name="unconstrained information ratio, twelve candidates",
            value=full.unconstrained_information_ratio,
            units="ratio",
            uncertainty_unavailable_reason="Deterministic given the stated ladder.",
            cost_basis=CostBasis.NET_OPTIMISTIC,
        ),
        Estimate(
            name="equal-weight information ratio, twelve candidates",
            value=full.equal_weight_information_ratio,
            units="ratio",
            uncertainty_unavailable_reason="Deterministic given the stated ladder.",
            cost_basis=CostBasis.NET_OPTIMISTIC,
            notes=(
                "Against "
                f"{by_count[1].equal_weight_information_ratio:.3f} for the single best "
                "candidate held alone."
            ),
        ),
        Estimate(
            name="short positions at the unconstrained optimum, twelve candidates",
            value=float(shorts),
            units="count",
            uncertainty_unavailable_reason="Deterministic given the stated ladder.",
            notes=(
                f"Net long exposure is {net_to_gross:.3f} of gross. This is where the "
                "incremental benefit of breadth lives, and a long-only investor cannot "
                "reach it."
            ),
        ),
    )

    ladder_frame = pd.DataFrame(
        [
            {
                "count": rung.count,
                "mean_net_edge_pp": rung.mean_net_edge,
                "available_bets": rung.available_bets,
                "sharpe_multiple": rung.sharpe_multiple,
                "equal_weight_ir": rung.equal_weight_information_ratio,
                "long_only_ir": rung.long_only_information_ratio,
                "unconstrained_ir": rung.unconstrained_information_ratio,
                "equal_weight_tc": rung.equal_weight_transfer_coefficient,
                "long_only_tc": rung.long_only_transfer_coefficient,
                "sleeves_held": rung.sleeves_held,
                "probability_at_horizon": rung.probability(horizon),
            }
            for rung in rungs
        ]
    )
    sweep_frame = pd.DataFrame(
        [
            {
                "correlation": correlation,
                "unconstrained_ir": rung.unconstrained_information_ratio,
                "long_only_ir": rung.long_only_information_ratio,
                "transfer_coefficient": rung.long_only_transfer_coefficient,
                "sleeves_held": rung.sleeves_held,
            }
            for correlation, rung in sweep
        ]
    )

    diagnostics: dict[str, JsonValue] = {
        "reads_market_data": False,
        "every_edge_is_an_assumption": True,
        "headline_correlation_is_a_measurement_of_one_portfolio": (
            "0.435 is the average pairwise correlation among the candidate portfolio's "
            "own four active tilts plus the trend overlay, 422 months 1990-11 to 2025-12. "
            "It is carried in as a parameter. It is not a market constant, and a wider "
            "stack would sit lower and have a higher ceiling."
        ),
        "supports_examined": exact.supports_examined,
        "dirichlet_best": best_random,
        "dirichlet_shortfall": exact.information_ratio - best_random,
        "equal_weight_optimum_by_cost": {
            key: value for key, value in cost_optima.items()
        },
        "held_by_correlation": list(held_by_correlation),
        "unconstrained_by_correlation": list(unconstrained_by_correlation),
        "long_only_by_correlation": list(constrained_by_correlation),
        "dispersion": [dict(row) for row in dispersion_rows],
        "unconstrained_weights_gross_normalised": [float(one) for one in weights],
        "short_positions": shorts,
        "net_to_gross": net_to_gross,
        "reported_shelf_sizes": list(reported_sizes),
        "units_restated_in_basis_points_unchanged": True,
    }

    summary = (
        f"On the frozen twelve-candidate ladder at rho = {headline_correlation}, the best "
        f"equal-weighted portfolio holds {equal_optimum.count} candidates and the exact "
        f"long-only optimum holds {full.sleeves_held}, unchanged from three candidates "
        f"upward, while the unconstrained optimum keeps improving to "
        f"{full.unconstrained_information_ratio:.3f} — a transfer coefficient of "
        f"{full.long_only_transfer_coefficient:.3f}, with {shorts} of twelve unconstrained "
        f"weights short and net long exposure at {net_to_gross:.3f} of gross. EVERY EDGE "
        "IS AN ASSUMPTION: this experiment reads no market data, so the result is a "
        "property of the stated ladder rather than of markets, and the 0.435 correlation "
        "is one portfolio's measurement rather than a market constant."
    )

    caveats = (
        "No market data is read and no premium is estimated. Every candidate edge is an "
        "input declared in the specification.",
        "The 0.435 correlation is measured on the candidate portfolio's own four value "
        "and momentum tilts plus a trend overlay. A genuinely wider stack would sit "
        "lower and hold more candidates.",
        "The count depends on edge DISPERSION as much as on correlation. Give every "
        f"candidate the same edge and the optimiser holds all {len(identical)} at a "
        "transfer coefficient of 1.000.",
        "The ladder omits skew, fat tails, time-varying correlation and estimation error "
        "in the edges. Each omission favours the thesis, so this is the generous case.",
        "The result has no interval and none may be invented; the declared sweeps are the "
        "sensitivity.",
        "Nothing here is promotable. An experiment with no data cannot supply evidence "
        "about markets; it can only make an argument reproducible.",
    )

    return ExperimentResult(
        status=ResultStatus.EXPLORATORY,
        summary=summary,
        estimates=estimates,
        diagnostics=diagnostics,
        caveats=caveats,
        frames={"ladder": ladder_frame, "correlation_sweep": sweep_frame},
    )


def _render_console_report(outcome: RunOutcome) -> str:
    result = outcome.result
    if result is None:  # pragma: no cover - the runner raises before this
        return "no result"
    frame = result.frames["ladder"]
    lines = ["== the ladder, at the headline correlation =="]
    lines.append(
        "  k   mean net   avail bets   mult    equal IR   long-only IR   unconstr IR"
        "   TC     held"
    )
    for row in frame.itertuples(index=False):
        lines.append(
            f"{row.count:3d}   {row.mean_net_edge_pp:8.2f}   {row.available_bets:10.2f}"
            f"   {row.sharpe_multiple:5.3f}   {row.equal_weight_ir:8.3f}"
            f"   {row.long_only_ir:12.3f}   {row.unconstrained_ir:11.3f}"
            f"   {row.long_only_tc:5.3f}   {row.sleeves_held:4d}"
        )
    lines.append("")
    lines.append("== the correlation sweep, whole shelf ==")
    lines.append("  rho    unconstrained   long-only      TC    held")
    for row in result.frames["correlation_sweep"].itertuples(index=False):
        lines.append(
            f"  {row.correlation:.3f}   {row.unconstrained_ir:13.3f}"
            f"   {row.long_only_ir:9.3f}   {row.transfer_coefficient:5.3f}"
            f"   {row.sleeves_held:5d}"
        )
    lines.append("")
    lines.append(result.summary)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run Experiment 017 through the runner and the ledger."""
    parser = argparse.ArgumentParser(
        prog="python -m portfolio_edge.experiments.exp_017_longonly_ladder",
        description=(
            "Score the frozen twelve-candidate ladder under equal, unconstrained and "
            "long-only weights, writing a ledger entry for the attempt."
        ),
    )
    parser.add_argument("--specification", type=Path, default=default_specification_path())
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--artifact-root", type=Path, default=None)
    parser.add_argument(
        "--origin", choices=[item.value for item in Origin], default=Origin.AI.value
    )
    parser.add_argument(
        "--view-results",
        action="store_true",
        help=(
            "print the computed numbers AND append a results_viewed entry to the "
            "ledger. Looking is an event with consequences, so it is recorded."
        ),
    )
    arguments = parser.parse_args(argv)
    specification = load_specification(arguments.specification)

    ledger = Ledger(arguments.ledger)
    outcome = run_experiment(
        specification,
        registry=build_registry(),
        ledger=ledger,
        artifact_root=arguments.artifact_root,
        origin=Origin(arguments.origin),
        dataset_manifest_hashes=(),
    )

    print(f"run_id       {outcome.run_id}")
    print(f"spec_hash    {outcome.spec_hash}")
    print(f"status       {outcome.status.value}")
    print(f"result       {outcome.result.status.value if outcome.result else 'none'}")
    print(f"git_commit   {outcome.git_state.commit} (dirty={outcome.git_state.dirty})")
    for record in outcome.artifacts:
        print(f"artifact     {record.path}  {record.sha256}  {record.size_bytes}B")

    if arguments.view_results:
        print()
        print(_render_console_report(outcome))
        ledger.record_results_viewed(
            outcome.run_id,
            origin=Origin(arguments.origin),
            notes=(
                "numbers printed to the console by the --view-results flag of "
                "exp_017_longonly_ladder"
            ),
        )
        print()
        print("results_viewed appended to the ledger")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
