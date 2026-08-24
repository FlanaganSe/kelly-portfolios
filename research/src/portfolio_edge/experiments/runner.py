"""Orchestration: validate, ledger, execute, hash, ledger again.

The order is fixed and the ledger writes bracket everything that can fail:

1. Validate the specification. A refusal is itself an attempted execution, so it
   is appended as ``failed`` before the error propagates.
2. Capture git commit and worktree state by shelling out to ``git``. An
   unreadable repository is recorded as *dirty*, never as clean.
3. Append ``started``.
4. Resolve the entry point against the registry handed to this call.
5. Execute with a generator seeded from the specification's seed.
6. Check the claimed :class:`~portfolio_edge.experiments.result.ResultStatus`
   against the run kind, write and hash artifacts, append ``succeeded``.

Any exception at any step appends a terminal entry with the reason *before* it
propagates. A ``KeyboardInterrupt`` or ``SystemExit`` is recorded as
``abandoned`` rather than ``failed``, because giving up on a run is a fact about
the search and abandoned runs still count against it.

This module imports nothing from ``core``, ``data`` or ``inference``. Everything
the experiment needs arrives through the frozen specification; everything the
runner needs arrives through the registry.
"""

from __future__ import annotations

import hashlib
import secrets
import subprocess
import traceback
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np

from portfolio_edge.experiments.ledger import (
    Ledger,
    LedgerEntry,
    LedgerEvent,
    Origin,
    RunStatus,
    code_version,
    environment_snapshot,
    new_run_id,
    utc_now,
)
from portfolio_edge.experiments.registry import ExperimentRegistry, RunContext
from portfolio_edge.experiments.result import (
    ArtifactRecord,
    ExperimentResult,
    ResultStatus,
    check_status_allowed,
)
from portfolio_edge.experiments.specification import (
    Specification,
    validate_specification,
)
from portfolio_edge.reporting.artifacts import write_result_artifacts

_GIT_TIMEOUT_SECONDS: Final = 30
_TRACEBACK_LINES: Final = 12


class RunnerError(Exception):
    """The runner could not complete a run. Always ledgered before it is raised."""


@dataclass(frozen=True, slots=True, kw_only=True)
class GitState:
    """Commit and worktree cleanliness at the moment a run started.

    ``dirty`` defaults to true on any failure to read the repository. Unknown
    provenance is treated as unreproducible provenance.
    """

    commit: str | None
    dirty: bool
    diff_sha256: str | None
    error: str | None = None


def capture_git_state(repo_dir: Path | str | None = None) -> GitState:
    """Shell out to ``git`` for the commit, dirty flag and a hash of the diff."""
    cwd = Path(repo_dir) if repo_dir is not None else Path(__file__).resolve().parents[3]

    def run(*args: str) -> tuple[int, str]:
        completed = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
        return completed.returncode, completed.stdout

    try:
        commit_code, commit_out = run("rev-parse", "HEAD")
        if commit_code != 0:
            return GitState(
                commit=None,
                dirty=True,
                diff_sha256=None,
                error=f"git rev-parse HEAD failed with code {commit_code}",
            )
        status_code, status_out = run("status", "--porcelain", "--untracked-files=all")
        if status_code != 0:
            return GitState(
                commit=commit_out.strip(),
                dirty=True,
                diff_sha256=None,
                error=f"git status failed with code {status_code}",
            )
        dirty = bool(status_out.strip())
        diff_hash: str | None = None
        if dirty:
            _, diff_out = run("diff", "HEAD")
            payload = f"{diff_out}\n--- untracked and staged ---\n{status_out}"
            diff_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return GitState(commit=commit_out.strip(), dirty=dirty, diff_sha256=diff_hash)
    except (OSError, subprocess.SubprocessError) as exc:
        return GitState(commit=None, dirty=True, diff_sha256=None, error=f"git unavailable: {exc}")


@dataclass(frozen=True, slots=True, kw_only=True)
class RunOutcome:
    """What a completed call to :func:`run_experiment` produced."""

    run_id: str
    status: RunStatus
    spec_hash: str
    seed: int
    result: ExperimentResult | None
    artifacts: tuple[ArtifactRecord, ...]
    failure_reason: str | None
    git_state: GitState


def _short_traceback(exc: BaseException) -> str:
    lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
    return "".join(lines[-_TRACEBACK_LINES:]).strip()


def run_experiment(
    specification: Specification,
    *,
    registry: ExperimentRegistry,
    ledger: Ledger,
    artifact_root: Path | str | None = None,
    origin: Origin = Origin.AI,
    parent_run_id: str | None = None,
    dataset_manifest_hashes: Sequence[str] = (),
    repo_dir: Path | str | None = None,
    run_id: str | None = None,
    seed_source: Callable[[], int] = lambda: secrets.randbits(63),
) -> RunOutcome:
    """Execute one specification, recording every attempt in the ledger.

    Raises whatever the experiment raised, after appending a terminal ledger
    entry. Returns a :class:`RunOutcome` only on success.
    """
    identifier = run_id or new_run_id()
    git_state = capture_git_state(repo_dir)
    spec_hash = specification.spec_hash
    declared_seed = specification.seed
    seed = declared_seed if declared_seed is not None else seed_source()
    seed_note = (
        ""
        if declared_seed is not None
        else "seed drawn at run time; the specification declared none"
    )

    def entry(
        event: LedgerEvent,
        status: RunStatus | None,
        *,
        failure_reason: str | None = None,
        artifacts: tuple[ArtifactRecord, ...] = (),
        result_status: ResultStatus | None = None,
        notes: str = "",
    ) -> LedgerEntry:
        combined = "; ".join(part for part in (seed_note, git_state.error or "", notes) if part)
        return LedgerEntry(
            run_id=identifier,
            experiment_family=specification.experiment_family,
            timestamp_utc=utc_now().isoformat(),
            event=event,
            status=status,
            git_commit=git_state.commit,
            worktree_dirty=git_state.dirty,
            diff_sha256=git_state.diff_sha256,
            spec_hash=spec_hash,
            dataset_manifest_hashes=tuple(dataset_manifest_hashes),
            code_version=code_version(),
            environment=environment_snapshot(),
            parameters=specification.parameters,
            seed=seed,
            failure_reason=failure_reason,
            artifacts=artifacts,
            run_kind=specification.run_kind,
            parent_run_id=parent_run_id,
            origin=origin,
            results_viewed=event is LedgerEvent.RESULTS_VIEWED,
            consumes_final_holdout=specification.consumes_final_holdout,
            result_status=result_status,
            notes=combined,
        )

    def fail(reason: str) -> None:
        ledger.append(entry(LedgerEvent.FAILED, RunStatus.FAILED, failure_reason=reason))

    # 1. Validate before anything is started. A refusal is still an attempt.
    try:
        validate_specification(specification)
    except Exception as exc:
        fail(f"specification refused: {type(exc).__name__}: {exc}")
        raise

    # 2. Started.
    ledger.append(entry(LedgerEvent.STARTED, RunStatus.STARTED))

    # 3. Resolve.
    try:
        function = registry.resolve(specification.entry_point)
    except Exception as exc:
        fail(f"entry point unresolved: {type(exc).__name__}: {exc}")
        raise

    root = Path(artifact_root) if artifact_root is not None else None
    context = RunContext(
        run_id=identifier,
        seed=seed,
        rng=np.random.default_rng(seed),
        artifact_dir=(root or Path("artifacts")) / identifier,
    )

    # 4. Execute.
    try:
        result = function(specification, context)
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}\n{_short_traceback(exc)}")
        raise
    except BaseException as exc:  # KeyboardInterrupt, SystemExit
        ledger.append(
            entry(
                LedgerEvent.ABANDONED,
                RunStatus.ABANDONED,
                failure_reason=f"{type(exc).__name__}: {exc}",
            )
        )
        raise

    # 5. Check the claim, then write and hash the evidence.
    try:
        if not isinstance(result, ExperimentResult):
            raise RunnerError(
                f"{specification.entry_point!r} returned {type(result).__name__}, "
                "not an ExperimentResult"
            )
        check_status_allowed(result.status, specification.run_kind)
        artifacts = write_result_artifacts(
            result,
            run_id=identifier,
            artifact_root=root,
            specification=specification,
        )
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")
        raise

    ledger.append(
        entry(
            LedgerEvent.SUCCEEDED,
            RunStatus.SUCCEEDED,
            artifacts=artifacts,
            result_status=result.status,
        )
    )
    return RunOutcome(
        run_id=identifier,
        status=RunStatus.SUCCEEDED,
        spec_hash=spec_hash,
        seed=seed,
        result=result,
        artifacts=artifacts,
        failure_reason=None,
        git_state=git_state,
    )
