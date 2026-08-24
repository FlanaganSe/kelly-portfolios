"""Every attempt reaches the ledger, including the ones that fail."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from portfolio_edge.experiments.ledger import Ledger, LedgerEvent, Origin, RunStatus
from portfolio_edge.experiments.registry import (
    ExperimentRegistry,
    RunContext,
    UnknownExperimentError,
)
from portfolio_edge.experiments.result import (
    ExperimentResult,
    ResultError,
    ResultStatus,
    check_status_allowed,
    statuses_available_to,
)
from portfolio_edge.experiments.runner import (
    RunnerError,
    capture_git_state,
    run_experiment,
)
from portfolio_edge.experiments.specification import (
    ConfirmatoryGateError,
    RunKind,
    Specification,
)
from tests.unit.test_experiments_support import build_spec, sample_result, valid_spec_mapping


def _registry_returning(result: ExperimentResult) -> ExperimentRegistry:
    registry = ExperimentRegistry()

    @registry.register("test_experiment")
    def experiment(spec: Specification, context: RunContext) -> ExperimentResult:
        assert context.seed is not None
        return result

    return registry


def _run(
    tmp_path: Path,
    registry: ExperimentRegistry,
    **spec_overrides: Any,
) -> tuple[Ledger, Any]:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    spec = build_spec(**spec_overrides)
    outcome = run_experiment(
        spec,
        registry=registry,
        ledger=ledger,
        artifact_root=tmp_path / "artifacts",
    )
    return ledger, outcome


def test_successful_run_appends_started_then_succeeded_with_hashed_artifacts(
    tmp_path: Path,
) -> None:
    ledger, outcome = _run(tmp_path, _registry_returning(sample_result()))
    entries = ledger.read()
    assert [entry.event for entry in entries] == [
        LedgerEvent.STARTED,
        LedgerEvent.SUCCEEDED,
    ]
    started, succeeded = entries
    assert started.run_id == succeeded.run_id == outcome.run_id
    assert succeeded.spec_hash == outcome.spec_hash
    assert succeeded.result_status is ResultStatus.EXPLORATORY
    assert succeeded.code_version
    assert succeeded.environment["python_version"]
    assert succeeded.seed == 7
    assert succeeded.origin is Origin.AI
    assert succeeded.run_kind is RunKind.EXPLORATORY
    assert {record.path for record in succeeded.artifacts} == {
        f"{outcome.run_id}/result.json",
        f"{outcome.run_id}/summary.md",
        f"{outcome.run_id}/manifest.json",
    }
    for record in succeeded.artifacts:
        assert len(record.sha256) == 64
        assert (tmp_path / "artifacts" / record.path).exists()

    state = ledger.runs()[outcome.run_id]
    assert state.status is RunStatus.SUCCEEDED
    assert state.results_viewed is False


def test_raised_exception_is_ledgered_as_failed_before_it_propagates(tmp_path: Path) -> None:
    registry = ExperimentRegistry()

    @registry.register("test_experiment")
    def explode(spec: Specification, context: RunContext) -> ExperimentResult:
        raise ZeroDivisionError("the data was not there")

    ledger = Ledger(tmp_path / "ledger.jsonl")
    with pytest.raises(ZeroDivisionError, match="the data was not there"):
        run_experiment(
            build_spec(),
            registry=registry,
            ledger=ledger,
            artifact_root=tmp_path / "artifacts",
        )

    entries = ledger.read()
    assert [entry.event for entry in entries] == [LedgerEvent.STARTED, LedgerEvent.FAILED]
    failure = entries[-1]
    assert failure.failure_reason is not None
    assert "ZeroDivisionError" in failure.failure_reason
    assert "the data was not there" in failure.failure_reason
    assert ledger.runs()[failure.run_id].status is RunStatus.FAILED


def test_keyboard_interrupt_is_recorded_as_abandoned(tmp_path: Path) -> None:
    registry = ExperimentRegistry()

    @registry.register("test_experiment")
    def interrupted(spec: Specification, context: RunContext) -> ExperimentResult:
        raise KeyboardInterrupt

    ledger = Ledger(tmp_path / "ledger.jsonl")
    with pytest.raises(KeyboardInterrupt):
        run_experiment(
            build_spec(),
            registry=registry,
            ledger=ledger,
            artifact_root=tmp_path / "artifacts",
        )
    assert ledger.read()[-1].event is LedgerEvent.ABANDONED
    assert ledger.runs()[ledger.read()[-1].run_id].status is RunStatus.ABANDONED


def test_unresolved_entry_point_is_ledgered(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    with pytest.raises(UnknownExperimentError):
        run_experiment(
            build_spec(),
            registry=ExperimentRegistry(),
            ledger=ledger,
            artifact_root=tmp_path / "artifacts",
        )
    entries = ledger.read()
    assert [entry.event for entry in entries] == [LedgerEvent.STARTED, LedgerEvent.FAILED]
    assert "entry point unresolved" in (entries[-1].failure_reason or "")


def test_refused_confirmatory_specification_is_ledgered_as_failed(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    mapping = valid_spec_mapping()
    mapping["run_kind"] = "confirmatory"
    spec = Specification(
        experiment_family="exp_test_family",
        title="Hand-built, ungated",
        hypothesis="h",
        mechanism="m",
        falsifier="f",
        universe={"description": "d"},
        sample_policy=build_spec().sample_policy,
        benchmark="",
        primary_metric="mean",
        secondary_metrics=(),
        cost_model={"applied": False},
        rebalance_rule="none",
        inference=build_spec().inference,
        rejection_rule="r",
        run_kind=RunKind.CONFIRMATORY,
        consumes_final_holdout=False,
        parameters={},
        seed=1,
        entry_point="test_experiment",
        evidence_class=build_spec().evidence_class,
    )
    with pytest.raises(ConfirmatoryGateError, match="benchmark"):
        run_experiment(
            spec,
            registry=_registry_returning(sample_result()),
            ledger=ledger,
            artifact_root=tmp_path / "artifacts",
        )
    entries = ledger.read()
    assert [entry.event for entry in entries] == [LedgerEvent.FAILED]
    assert "specification refused" in (entries[0].failure_reason or "")


def test_exploratory_run_may_not_claim_a_confirmatory_status(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    with pytest.raises(ResultError, match="requires run_kind"):
        run_experiment(
            build_spec(),
            registry=_registry_returning(sample_result(ResultStatus.PRODUCTION_ELIGIBLE)),
            ledger=ledger,
            artifact_root=tmp_path / "artifacts",
        )
    assert ledger.read()[-1].event is LedgerEvent.FAILED


def test_status_taxonomy_is_closed() -> None:
    assert {status.value for status in ResultStatus} == {
        "exploratory",
        "source-reproduced",
        "independently-reproduced",
        "walk-forward-tested",
        "shadow-live",
        "production-eligible",
        "rejected",
        "unresolved",
    }
    with pytest.raises(ValueError, match="works"):
        ResultStatus("works")
    assert ResultStatus.PRODUCTION_ELIGIBLE not in statuses_available_to(RunKind.EXPLORATORY)
    check_status_allowed(ResultStatus.PRODUCTION_ELIGIBLE, RunKind.CONFIRMATORY)


def test_non_result_return_value_is_refused_and_ledgered(tmp_path: Path) -> None:
    registry = ExperimentRegistry()

    def liar(spec: Specification, context: RunContext) -> ExperimentResult:
        return "looks good"  # type: ignore[return-value]

    registry.add("test_experiment", liar)
    ledger = Ledger(tmp_path / "ledger.jsonl")
    with pytest.raises(RunnerError, match="not an ExperimentResult"):
        run_experiment(
            build_spec(),
            registry=registry,
            ledger=ledger,
            artifact_root=tmp_path / "artifacts",
        )
    assert ledger.read()[-1].event is LedgerEvent.FAILED


def test_absent_seed_is_drawn_and_recorded(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    outcome = run_experiment(
        build_spec(seed=None),
        registry=_registry_returning(sample_result()),
        ledger=ledger,
        artifact_root=tmp_path / "artifacts",
        seed_source=lambda: 4242,
    )
    assert outcome.seed == 4242
    entry = ledger.read()[-1]
    assert entry.seed == 4242
    assert "seed drawn at run time" in entry.notes


def test_parent_run_and_origin_are_recorded(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    run_experiment(
        build_spec(),
        registry=_registry_returning(sample_result()),
        ledger=ledger,
        artifact_root=tmp_path / "artifacts",
        origin=Origin.HUMAN,
        parent_run_id="earlier-run",
        dataset_manifest_hashes=["a" * 64],
    )
    entry = ledger.read()[-1]
    assert entry.origin is Origin.HUMAN
    assert entry.parent_run_id == "earlier-run"
    assert entry.dataset_manifest_hashes == ("a" * 64,)


def test_git_state_is_captured_from_the_repository() -> None:
    state = capture_git_state(Path(__file__).resolve().parents[2])
    assert state.error is None
    assert state.commit is not None
    assert len(state.commit) == 40
    if state.dirty:
        assert state.diff_sha256 is not None and len(state.diff_sha256) == 64
    else:
        assert state.diff_sha256 is None


def test_unreadable_repository_is_recorded_as_dirty(tmp_path: Path) -> None:
    state = capture_git_state(tmp_path)
    assert state.dirty is True
    assert state.commit is None
    assert state.error is not None


def test_run_records_git_state_on_every_entry(tmp_path: Path) -> None:
    ledger, _ = _run(tmp_path, _registry_returning(sample_result()))
    for entry in ledger.read():
        assert isinstance(entry.worktree_dirty, bool)
        if entry.worktree_dirty:
            assert entry.diff_sha256 is not None or entry.git_commit is None
