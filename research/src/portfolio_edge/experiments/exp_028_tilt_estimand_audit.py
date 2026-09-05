"""Register the correction separating priced tilt return from residual appraisal."""

from __future__ import annotations

import argparse
import hashlib
import io
from collections.abc import Mapping
from contextlib import redirect_stdout
from pathlib import Path

from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.experiments.ledger import Ledger
from portfolio_edge.experiments.registry import ExperimentRegistry, RunContext
from portfolio_edge.experiments.result import ExperimentResult, ResultStatus
from portfolio_edge.experiments.runner import run_experiment
from portfolio_edge.experiments.specification import JsonValue, Specification, load_specification
from portfolio_edge.studies import _untested_tilts_tables

ENTRY_POINT = "exp_028_tilt_estimand_audit"


class RecordingCache(RawCache):
    """Record the identity of every source artifact actually read by the study."""

    def __init__(self) -> None:
        super().__init__()
        self.sources: dict[tuple[str, str], JsonValue] = {}

    def read(self, entry: CacheEntry) -> bytes:
        raw = super().read(entry)
        self.sources[(entry.url, entry.sha256)] = {
            "url": entry.url, "sha256": entry.sha256,
            "size_bytes": entry.size_bytes, "retrieved_utc": entry.retrieved_utc,
        }
        return raw


def run(specification: Specification, context: RunContext) -> ExperimentResult:
    """Capture the unchanged study design with its corrected reporting estimand."""
    expected = specification.parameters
    if not isinstance(expected, Mapping):
        raise ValueError("audit parameters must be a mapping")
    source = Path(_untested_tilts_tables.__file__)
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected["emitter_sha256"]:
        raise ValueError("the registered emitter changed; freeze a new specification")
    cache = RecordingCache()
    captured = io.StringIO()
    with redirect_stdout(captured):
        _untested_tilts_tables.main(cache=cache)
    output = captured.getvalue()
    return ExperimentResult(
        status=ResultStatus.EXPLORATORY,
        summary=(
            "Correction audit: funded factor-tilt contribution uses the candidate's priced "
            "edge over its funding asset. Residual appraisal is a separate diagnostic. "
            "Neither measures full funded return or log growth."
        ),
        diagnostics={
            "raw_table_output": output, "emitter_sha256": expected["emitter_sha256"],
            "source_artifacts": list(cache.sources.values()),
        },
        caveats=(
            "Same historical data and study parameters already inspected; no new holdout.",
            "Market-beta contribution, intercept and taxes are omitted from the priced edge.",
            "Premium-error ranges omit loading, cost and residual-appraisal uncertainty.",
            "Held active-position proxy is incomplete; no allocation ranking is established.",
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-run-id", default=None)
    parser.add_argument("--specification", type=Path, default=None)
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    specification = load_specification(
        arguments.specification
        or root / "experiments" / "exp_028b_tilt_estimand_source_audit.yaml"
    )
    registry = ExperimentRegistry()
    registry.add(ENTRY_POINT, run)
    ledger = Ledger()
    outcome = run_experiment(
        specification, registry=registry, ledger=ledger,
        parent_run_id=arguments.parent_run_id,
    )
    assert outcome.result is not None
    table = Path("artifacts") / outcome.run_id / "tables.md"
    table.write_text("```text\n" + str(outcome.result.diagnostics["raw_table_output"]) + "\n```\n")
    ledger.record_results_viewed(outcome.run_id, notes="correction audit output inspected")
    print(f"run {outcome.run_id}: artifacts/{outcome.run_id}/summary.md")


if __name__ == "__main__":
    main()
