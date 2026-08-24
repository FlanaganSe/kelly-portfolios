"""Append-only experiment ledger.

Every attempted execution is recorded, including refusals, failures and
abandoned runs. The ledger exists because the effective number of independent
trials cannot be reconstructed after the fact: it has to precede the first
backtest rather than follow it.

**The ledger is append-only and there is no update-in-place API.** Recording that
a result was viewed, or that a run was abandoned, appends a *new* entry carrying
the same ``run_id``. Current state is a fold over the event log, never a mutation
of a row. This is not fussiness: a record that can be edited after the outcome is
known records the outcome, not the search.

Concurrency
-----------
Several agents run experiments at once. Appends are made with a single
``os.write`` of one complete, newline-terminated line to a file descriptor opened
``O_APPEND``, under an exclusive ``fcntl.flock``. ``O_APPEND`` makes the offset
seek and the write one operation; the lock serialises writers that would
otherwise interleave partial buffers; the single-write discipline means a partial
line is impossible even if a writer is killed between calls. JSON encoding
guarantees no embedded newline, which is asserted before writing.

Counting trials
---------------
:func:`search_counts` reports distinct specification hashes *and* total
invocations, because they are different numbers and a Deflated Sharpe Ratio needs
the former. Read :data:`TRIALS_CAVEAT` before using either.
"""

from __future__ import annotations

import fcntl
import importlib.metadata
import json
import os
import platform
import uuid
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Final

from portfolio_edge.experiments.result import ArtifactRecord, ResultStatus
from portfolio_edge.experiments.specification import JsonValue, RunKind, plain_json

LEDGER_SCHEMA_VERSION: Final = 1

TRIALS_CAVEAT: Final = (
    "The count of distinct specification hashes is an UPPER BOUND on the number of "
    "independent trials, not the number itself. Specifications overlap: they share "
    "data, universes, eras and construction choices, so their test statistics are "
    "dependent, and dependence is not solved by counting. Specification dependence "
    "is an unresolved statistical problem in this repository. The ledger makes later "
    "estimation possible; it does not perform it. Never pass the total invocation "
    "count to a Deflated Sharpe Ratio as the number of trials, and never pass the "
    "distinct-specification count without stating that it is an upper bound."
)

_NUMERIC_DEPENDENCIES: Final = ("numpy", "pandas", "scipy", "statsmodels", "pyarrow", "PyYAML")


class LedgerError(Exception):
    """Base class for ledger failures."""


class LedgerFormatError(LedgerError, ValueError):
    """A ledger line is malformed. Never repaired silently."""


class RunStatus(StrEnum):
    """Lifecycle status of a run. ``results_viewed`` is an event, not a status."""

    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ABANDONED = "abandoned"


class LedgerEvent(StrEnum):
    """What an appended line records."""

    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ABANDONED = "abandoned"
    RESULTS_VIEWED = "results_viewed"


_EVENT_STATUS: Final[Mapping[LedgerEvent, RunStatus | None]] = {
    LedgerEvent.STARTED: RunStatus.STARTED,
    LedgerEvent.SUCCEEDED: RunStatus.SUCCEEDED,
    LedgerEvent.FAILED: RunStatus.FAILED,
    LedgerEvent.ABANDONED: RunStatus.ABANDONED,
    LedgerEvent.RESULTS_VIEWED: None,
}

_TERMINAL_STATUSES: Final = frozenset(
    {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.ABANDONED}
)


class Origin(StrEnum):
    AI = "ai"
    HUMAN = "human"


def new_run_id() -> str:
    return uuid.uuid4().hex


def utc_now() -> datetime:
    return datetime.now(UTC)


def _package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def code_version() -> str:
    """Version of the installed ``portfolio-edge`` distribution."""
    return _package_version("portfolio-edge")


def environment_snapshot() -> dict[str, JsonValue]:
    """Python and resolved numeric-dependency versions.

    Recorded per entry rather than per session: a long-lived worktree can change
    its environment between runs, and a ledger that assumes otherwise is wrong
    exactly when it matters.
    """
    packages: dict[str, JsonValue] = {
        name: _package_version(name) for name in _NUMERIC_DEPENDENCIES
    }
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "packages": packages,
    }


@dataclass(frozen=True, slots=True, kw_only=True)
class LedgerEntry:
    """One appended line.

    ``entry_id`` is unique per line. ``run_id`` is shared by every line about the
    same run, which is how a ``results_viewed`` or ``abandoned`` event references
    an earlier ``started`` without editing it.
    """

    entry_id: str = field(default_factory=new_run_id)
    run_id: str
    experiment_family: str
    timestamp_utc: str
    event: LedgerEvent
    status: RunStatus | None
    git_commit: str | None = None
    worktree_dirty: bool = True
    diff_sha256: str | None = None
    spec_hash: str | None = None
    dataset_manifest_hashes: tuple[str, ...] = ()
    code_version: str = ""
    environment: Mapping[str, JsonValue] = field(default_factory=dict)
    parameters: JsonValue = None
    seed: int | None = None
    failure_reason: str | None = None
    artifacts: tuple[ArtifactRecord, ...] = ()
    run_kind: RunKind = RunKind.EXPLORATORY
    parent_run_id: str | None = None
    origin: Origin = Origin.AI
    results_viewed: bool = False
    consumes_final_holdout: bool = False
    result_status: ResultStatus | None = None
    notes: str = ""
    schema_version: int = LEDGER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        expected = _EVENT_STATUS[self.event]
        if self.status != expected:
            raise LedgerFormatError(
                f"event {self.event.value!r} must carry status {expected!r}, "
                f"got {self.status!r}"
            )
        if (self.event is LedgerEvent.RESULTS_VIEWED) != self.results_viewed:
            raise LedgerFormatError(
                "results_viewed must be true on a results_viewed entry and false "
                f"elsewhere; event={self.event.value!r} results_viewed={self.results_viewed!r}"
            )
        if self.event is LedgerEvent.FAILED and not (self.failure_reason or "").strip():
            raise LedgerFormatError("a failed entry must state a failure_reason")

    def to_json(self) -> dict[str, JsonValue]:
        return {
            "schema_version": self.schema_version,
            "entry_id": self.entry_id,
            "run_id": self.run_id,
            "experiment_family": self.experiment_family,
            "timestamp_utc": self.timestamp_utc,
            "event": self.event.value,
            "status": self.status.value if self.status is not None else None,
            "git_commit": self.git_commit,
            "worktree_dirty": self.worktree_dirty,
            "diff_sha256": self.diff_sha256,
            "spec_hash": self.spec_hash,
            "dataset_manifest_hashes": list(self.dataset_manifest_hashes),
            "code_version": self.code_version,
            "environment": plain_json(dict(self.environment)),
            "parameters": plain_json(self.parameters),
            "seed": self.seed,
            "failure_reason": self.failure_reason,
            "artifacts": [record.to_json() for record in self.artifacts],
            "run_kind": self.run_kind.value,
            "parent_run_id": self.parent_run_id,
            "origin": self.origin.value,
            "results_viewed": self.results_viewed,
            "consumes_final_holdout": self.consumes_final_holdout,
            "result_status": self.result_status.value if self.result_status else None,
            "notes": self.notes,
        }

    def to_line(self) -> str:
        """One complete JSON line. Contains exactly one newline, at the end."""
        text = json.dumps(
            self.to_json(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        if "\n" in text or "\r" in text:  # pragma: no cover - json escapes both
            raise LedgerFormatError("encoded ledger entry contains a line break")
        return text + "\n"

    @classmethod
    def from_json(cls, data: Mapping[str, JsonValue]) -> LedgerEntry:
        def text(key: str, *, required: bool = True) -> str:
            value = data.get(key)
            if value is None and not required:
                return ""
            if not isinstance(value, str):
                raise LedgerFormatError(f"ledger field {key!r} must be a string, got {value!r}")
            return value

        def optional_text(key: str) -> str | None:
            value = data.get(key)
            if value is None:
                return None
            if not isinstance(value, str):
                raise LedgerFormatError(f"ledger field {key!r} must be a string, got {value!r}")
            return value

        def flag(key: str) -> bool:
            value = data.get(key)
            if not isinstance(value, bool):
                raise LedgerFormatError(f"ledger field {key!r} must be a boolean, got {value!r}")
            return value

        try:
            event = LedgerEvent(text("event"))
        except ValueError as exc:
            raise LedgerFormatError(f"unknown ledger event {data.get('event')!r}") from exc

        raw_status = optional_text("status")
        status = RunStatus(raw_status) if raw_status is not None else None

        raw_result_status = optional_text("result_status")
        result_status = ResultStatus(raw_result_status) if raw_result_status else None

        manifests = data.get("dataset_manifest_hashes", [])
        if not isinstance(manifests, Sequence) or isinstance(manifests, str):
            raise LedgerFormatError("dataset_manifest_hashes must be a list of strings")

        raw_artifacts = data.get("artifacts", [])
        if not isinstance(raw_artifacts, Sequence) or isinstance(raw_artifacts, str):
            raise LedgerFormatError("artifacts must be a list of records")
        artifacts: list[ArtifactRecord] = []
        for item in raw_artifacts:
            if not isinstance(item, Mapping):
                raise LedgerFormatError(f"artifact record must be a mapping, got {item!r}")
            artifacts.append(ArtifactRecord.from_json(item))

        environment = data.get("environment", {})
        if not isinstance(environment, Mapping):
            raise LedgerFormatError("environment must be a mapping")

        seed = data.get("seed")
        if seed is not None and (not isinstance(seed, int) or isinstance(seed, bool)):
            raise LedgerFormatError(f"seed must be an integer or null, got {seed!r}")

        schema_version = data.get("schema_version", LEDGER_SCHEMA_VERSION)
        if not isinstance(schema_version, int) or isinstance(schema_version, bool):
            raise LedgerFormatError(f"schema_version must be an integer, got {schema_version!r}")

        return cls(
            entry_id=text("entry_id"),
            run_id=text("run_id"),
            experiment_family=text("experiment_family"),
            timestamp_utc=text("timestamp_utc"),
            event=event,
            status=status,
            git_commit=optional_text("git_commit"),
            worktree_dirty=flag("worktree_dirty"),
            diff_sha256=optional_text("diff_sha256"),
            spec_hash=optional_text("spec_hash"),
            dataset_manifest_hashes=tuple(str(item) for item in manifests),
            code_version=text("code_version", required=False),
            environment={str(key): value for key, value in environment.items()},
            parameters=data.get("parameters"),
            seed=seed,
            failure_reason=optional_text("failure_reason"),
            artifacts=tuple(artifacts),
            run_kind=RunKind(text("run_kind")),
            parent_run_id=optional_text("parent_run_id"),
            origin=Origin(text("origin")),
            results_viewed=flag("results_viewed"),
            consumes_final_holdout=flag("consumes_final_holdout"),
            result_status=result_status,
            notes=text("notes", required=False),
            schema_version=schema_version,
        )


def default_ledger_path() -> Path:
    """``research/ledger.jsonl``, resolved from this module's location."""
    return Path(__file__).resolve().parents[3] / "ledger.jsonl"


class Ledger:
    """An append-only JSONL file. No update, no delete, no rewrite."""

    __slots__ = ("path",)

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else default_ledger_path()

    # -- writing ---------------------------------------------------------- #

    def append(self, entry: LedgerEntry) -> LedgerEntry:
        """Append one entry atomically.

        A single ``os.write`` of one complete line to an ``O_APPEND`` descriptor
        held under ``fcntl.flock``. Returns the entry that was written so callers
        can record its ``entry_id``.
        """
        payload = entry.to_line().encode("utf-8")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            try:
                written = 0
                while written < len(payload):
                    written += os.write(descriptor, payload[written:])
                os.fsync(descriptor)
            finally:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)
        return entry

    # -- reading ---------------------------------------------------------- #

    def read(self) -> tuple[LedgerEntry, ...]:
        """Parse every line. A malformed line raises with its line number."""
        if not self.path.exists():
            return ()
        entries: list[LedgerEntry] = []
        with open(self.path, encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
            try:
                lines = handle.readlines()
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        for number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise LedgerFormatError(
                    f"{self.path}:{number}: not valid JSON: {exc}. The ledger is never "
                    "repaired in place; investigate the writer."
                ) from exc
            if not isinstance(payload, dict):
                raise LedgerFormatError(f"{self.path}:{number}: line is not a JSON object")
            try:
                entries.append(LedgerEntry.from_json(payload))
            except (LedgerFormatError, ValueError) as exc:
                raise LedgerFormatError(f"{self.path}:{number}: {exc}") from exc
        return tuple(entries)

    def runs(self) -> dict[str, RunState]:
        return fold_runs(self.read())

    def run_state(self, run_id: str) -> RunState:
        states = self.runs()
        try:
            return states[run_id]
        except KeyError as exc:
            raise LedgerError(f"no run {run_id!r} in {self.path}") from exc

    # -- follow-up events -------------------------------------------------- #
    #
    # These append; they never edit. A viewed or abandoned event is a new line
    # that references the earlier run_id.

    def record_results_viewed(
        self,
        run_id: str,
        *,
        origin: Origin = Origin.AI,
        notes: str = "",
    ) -> LedgerEntry:
        """Record that a human or agent looked at this run's results.

        Looking is an event with consequences -- it converts a holdout into
        training data -- so it is recorded as its own entry rather than by
        flipping a flag on the run that produced the numbers.
        """
        state = self.run_state(run_id)
        return self.append(
            LedgerEntry(
                run_id=run_id,
                experiment_family=state.experiment_family,
                timestamp_utc=utc_now().isoformat(),
                event=LedgerEvent.RESULTS_VIEWED,
                status=None,
                spec_hash=state.spec_hash,
                run_kind=state.run_kind,
                parent_run_id=state.parent_run_id,
                origin=origin,
                results_viewed=True,
                consumes_final_holdout=state.consumes_final_holdout,
                code_version=code_version(),
                environment=environment_snapshot(),
                seed=state.seed,
                notes=notes,
            )
        )

    def record_abandoned(
        self,
        run_id: str,
        *,
        reason: str,
        origin: Origin = Origin.AI,
    ) -> LedgerEntry:
        """Record that a started run was given up on. Abandoned runs still count."""
        if not reason.strip():
            raise LedgerError("an abandoned run must state why it was abandoned")
        state = self.run_state(run_id)
        return self.append(
            LedgerEntry(
                run_id=run_id,
                experiment_family=state.experiment_family,
                timestamp_utc=utc_now().isoformat(),
                event=LedgerEvent.ABANDONED,
                status=RunStatus.ABANDONED,
                spec_hash=state.spec_hash,
                run_kind=state.run_kind,
                parent_run_id=state.parent_run_id,
                origin=origin,
                consumes_final_holdout=state.consumes_final_holdout,
                code_version=code_version(),
                environment=environment_snapshot(),
                seed=state.seed,
                failure_reason=reason,
            )
        )

    def search_counts(self, *, experiment_family: str | None = None) -> SearchCounts:
        return search_counts(self.read(), experiment_family=experiment_family)


@dataclass(frozen=True, slots=True, kw_only=True)
class RunState:
    """Current state of one run, reconstructed by folding its events."""

    run_id: str
    experiment_family: str
    run_kind: RunKind
    status: RunStatus
    spec_hash: str | None
    seed: int | None
    origin: Origin
    parent_run_id: str | None
    consumes_final_holdout: bool
    results_viewed: bool
    result_status: ResultStatus | None
    failure_reason: str | None
    artifacts: tuple[ArtifactRecord, ...]
    first_seen_utc: str
    last_seen_utc: str
    entry_count: int
    git_commit: str | None
    worktree_dirty: bool

    @property
    def is_terminal(self) -> bool:
        return self.status in _TERMINAL_STATUSES


def fold_runs(entries: Iterable[LedgerEntry]) -> dict[str, RunState]:
    """Reconstruct run state from the event log, in file order.

    Later lifecycle events supersede earlier ones; ``results_viewed`` is sticky
    once true and never clears. Nothing here mutates the file.
    """
    states: dict[str, RunState] = {}
    for entry in entries:
        previous = states.get(entry.run_id)
        if previous is None:
            states[entry.run_id] = RunState(
                run_id=entry.run_id,
                experiment_family=entry.experiment_family,
                run_kind=entry.run_kind,
                status=entry.status or RunStatus.STARTED,
                spec_hash=entry.spec_hash,
                seed=entry.seed,
                origin=entry.origin,
                parent_run_id=entry.parent_run_id,
                consumes_final_holdout=entry.consumes_final_holdout,
                results_viewed=entry.results_viewed,
                result_status=entry.result_status,
                failure_reason=entry.failure_reason,
                artifacts=entry.artifacts,
                first_seen_utc=entry.timestamp_utc,
                last_seen_utc=entry.timestamp_utc,
                entry_count=1,
                git_commit=entry.git_commit,
                worktree_dirty=entry.worktree_dirty,
            )
            continue
        states[entry.run_id] = RunState(
            run_id=previous.run_id,
            experiment_family=previous.experiment_family,
            run_kind=previous.run_kind,
            status=entry.status if entry.status is not None else previous.status,
            spec_hash=entry.spec_hash or previous.spec_hash,
            seed=previous.seed if previous.seed is not None else entry.seed,
            origin=previous.origin,
            parent_run_id=previous.parent_run_id or entry.parent_run_id,
            consumes_final_holdout=previous.consumes_final_holdout
            or entry.consumes_final_holdout,
            results_viewed=previous.results_viewed or entry.results_viewed,
            result_status=entry.result_status or previous.result_status,
            failure_reason=entry.failure_reason or previous.failure_reason,
            artifacts=entry.artifacts or previous.artifacts,
            first_seen_utc=previous.first_seen_utc,
            last_seen_utc=entry.timestamp_utc,
            entry_count=previous.entry_count + 1,
            git_commit=previous.git_commit or entry.git_commit,
            worktree_dirty=previous.worktree_dirty or entry.worktree_dirty,
        )
    return states


@dataclass(frozen=True, slots=True, kw_only=True)
class SearchCounts:
    """Distinct specifications searched versus total invocations.

    These are different numbers and the difference matters. Repeated execution of
    an identical specification is one hypothesis tested many times, not many
    hypotheses. Read :attr:`caveat` before using either number in an inference.
    """

    experiment_family: str | None
    distinct_spec_hashes: int
    total_invocations: int
    distinct_spec_hashes_by_family: Mapping[str, int]
    spec_hashes: tuple[str, ...]
    runs_without_spec_hash: int
    caveat: str = TRIALS_CAVEAT

    @property
    def upper_bound_on_independent_trials(self) -> int:
        """Alias that refuses to be misread: this is a bound, not a count."""
        return self.distinct_spec_hashes


def search_counts(
    entries: Iterable[LedgerEntry], *, experiment_family: str | None = None
) -> SearchCounts:
    """Count distinct specification hashes and total invocations.

    An invocation is a run that was actually attempted, i.e. one ``started``,
    ``succeeded``, ``failed`` or ``abandoned`` run identifier -- not one line, and
    not one ``results_viewed`` event.
    """
    runs = fold_runs(entries)
    selected = [
        state
        for state in runs.values()
        if experiment_family is None or state.experiment_family == experiment_family
    ]
    hashes = sorted({state.spec_hash for state in selected if state.spec_hash})
    by_family: dict[str, set[str]] = {}
    for state in selected:
        if state.spec_hash:
            by_family.setdefault(state.experiment_family, set()).add(state.spec_hash)
    return SearchCounts(
        experiment_family=experiment_family,
        distinct_spec_hashes=len(hashes),
        total_invocations=len(selected),
        distinct_spec_hashes_by_family={
            family: len(values) for family, values in sorted(by_family.items())
        },
        spec_hashes=tuple(hashes),
        runs_without_spec_hash=sum(1 for state in selected if not state.spec_hash),
    )
