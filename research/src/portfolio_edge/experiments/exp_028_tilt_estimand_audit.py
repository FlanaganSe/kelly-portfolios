"""Register the correction separating priced tilt return from residual appraisal."""

from __future__ import annotations

import hashlib
import io
from collections.abc import Mapping
from contextlib import redirect_stdout
from pathlib import Path

from portfolio_edge.experiments.ledger import Ledger
from portfolio_edge.experiments.registry import ExperimentRegistry, RunContext
from portfolio_edge.experiments.result import ExperimentResult, ResultStatus
from portfolio_edge.experiments.runner import run_experiment
from portfolio_edge.experiments.specification import Specification, load_specification
from portfolio_edge.studies import _untested_tilts_tables

ENTRY_POINT = "exp_028_tilt_estimand_audit"


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Capture the unchanged study design with its corrected reporting estimand."""
    expected = specification.parameters
    if not isinstance(expected, Mapping):
        raise ValueError("audit parameters must be a mapping")
    source = Path(_untested_tilts_tables.__file__)
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected["emitter_sha256"]:
        raise ValueError("the registered emitter changed; freeze a new specification")
    captured = io.StringIO()
    with redirect_stdout(captured):
        _untested_tilts_tables.main()
    output = captured.getvalue()
    return ExperimentResult(
        status=ResultStatus.EXPLORATORY,
        summary=(
            "Correction audit: funded factor-tilt contribution uses the candidate's priced "
            "edge over its funding asset. Residual appraisal is a separate diagnostic. "
            "Neither measures full funded return or log growth.\n\n```text\n"
            + output
            + "\n```"
        ),
        diagnostics={"raw_table_output": output, "emitter_sha256": expected["emitter_sha256"]},
        caveats=(
            "Same historical data and study parameters already inspected; no new holdout.",
            "Market-beta contribution, intercept and taxes are omitted from the priced edge.",
            "Premium-error ranges omit loading, cost and residual-appraisal uncertainty.",
            "Held active-position proxy is incomplete; no allocation ranking is established.",
        ),
    )


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    specification = load_specification(root / "experiments" / f"{ENTRY_POINT}.yaml")
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    ledger = Ledger()
    outcome = run_experiment(specification, registry=registry, ledger=ledger)
    ledger.record_results_viewed(outcome.run_id, notes="correction audit output inspected")
    print(f"run {outcome.run_id}: artifacts/{outcome.run_id}/summary.md")


if __name__ == "__main__":
    main()
